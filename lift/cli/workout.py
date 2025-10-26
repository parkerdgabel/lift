"""Workout CLI commands for logging and tracking workouts."""

import re
from datetime import datetime
from decimal import Decimal

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from lift.core.database import DatabaseManager, get_db
from lift.core.models import SetCreate, SetType, WeightUnit, WorkoutCreate
from lift.services.program_service import ProgramService
from lift.services.set_service import SetService
from lift.services.workout_service import WorkoutService
from lift.utils.calculations import calculate_volume_load
from lift.utils.workout_formatters import (
    format_exercise_performance,
    format_program_prescription,
    format_program_workout_header,
    format_set_completion,
    format_workout_complete,
    format_workout_header,
    format_workout_list,
    format_workout_summary,
)


# Create workout CLI app
workout_app = typer.Typer(help="Log and track workouts")
console = Console()


@workout_app.command("start")
def start_workout(
    ctx: typer.Context,
    name: str | None = typer.Option(None, "--name", "-n", help="Workout name"),
    freestyle: bool = typer.Option(
        False, "--freestyle", "-f", help="Freestyle workout (ignore active program)"
    ),
    bodyweight: float | None = typer.Option(
        None, "--bodyweight", "-bw", help="Current bodyweight in lbs"
    ),
) -> None:
    """
    Start an interactive workout session.

    This command launches an interactive session where you can:
    - Follow an active program automatically (if set)
    - Select exercises manually (freestyle mode)
    - Log sets with shortcuts (s=same, +5=add 5lbs, etc.)
    - View last performance for each exercise
    - Track RPE if enabled
    - See real-time volume calculations
    """
    db = get_db(ctx.obj.get("db_path"))
    workout_service = WorkoutService(db)
    set_service = SetService(db)
    program_service = ProgramService(db)

    # Check for active program (unless freestyle)
    program_context: dict | None = None
    if not freestyle:
        active_program = program_service.get_active_program()
        if active_program:
            # Get next workout in rotation
            next_workout = program_service.get_next_workout_in_program(active_program.id)
            if next_workout:
                # Load exercise prescriptions
                exercises = program_service.get_workout_exercises(next_workout.id)
                position, total = program_service.get_workout_position_in_program(
                    next_workout.id, active_program.id
                )

                program_context = {
                    "program": active_program,
                    "workout": next_workout,
                    "exercises": exercises,
                    "position": position,
                    "total": total,
                }

                # Use workout name from template if not specified
                if not name:
                    name = next_workout.name

    # Create workout
    workout_name = name or "Workout"
    workout_create = WorkoutCreate(
        name=workout_name,
        date=datetime.now(),
        bodyweight=Decimal(str(bodyweight)) if bodyweight else None,
        bodyweight_unit=WeightUnit.LBS,
        program_workout_id=program_context["workout"].id if program_context else None,  # type: ignore[index]
        rating=None,
    )

    try:
        workout = workout_service.create_workout(workout_create)
    except Exception as e:
        console.print(f"[red]Error creating workout: {e}[/red]")
        raise typer.Exit(1)

    start_time = datetime.now()

    # Display header
    console.print()
    if program_context:
        console.print(
            format_program_workout_header(
                program_context["program"].name,  # type: ignore[index]
                program_context["workout"].name,  # type: ignore[index]
                program_context["position"],  # type: ignore[index]
                program_context["total"],  # type: ignore[index]
                len(program_context["exercises"]),  # type: ignore[index, arg-type]
                program_context["workout"].estimated_duration_minutes,  # type: ignore[index]
            )
        )
    else:
        console.print(format_workout_header(workout_name, start_time, workout_create.bodyweight))
    console.print()

    # Check if RPE is enabled
    rpe_enabled = _get_setting(db, "enable_rpe", "true") == "true"

    # Track workout state
    workout_state = {
        "total_volume": Decimal("0"),
        "total_sets": 0,
        "exercises": set(),
    }

    # Main workout loop
    if program_context:
        # Program-based workout: iterate through prescribed exercises
        for idx, exercise_data in enumerate(program_context["exercises"], 1):  # type: ignore[index, arg-type, var-annotated]
            exercise_id = exercise_data["exercise_id"]
            exercise_name = exercise_data["exercise_name"]
            prog_exercise = exercise_data["program_exercise"]

            console.print()
            console.print(
                f"\n[bold cyan]Exercise {idx} of {len(program_context['exercises'])}: {exercise_name}[/bold cyan]"  # type: ignore[index, arg-type]
            )

            # Display program prescription
            console.print()
            # Convert ProgramExercise object to dict for formatter
            prog_exercise_dict = {
                "target_sets": prog_exercise.target_sets,
                "target_reps_min": prog_exercise.target_reps_min,
                "target_reps_max": prog_exercise.target_reps_max,
                "target_rpe": prog_exercise.target_rpe,
                "rest_seconds": prog_exercise.rest_seconds,
                "tempo": prog_exercise.tempo,
                "notes": prog_exercise.notes,
            }
            console.print(format_program_prescription(exercise_name, prog_exercise_dict))

            # Show last performance
            last_performance = workout_service.get_last_performance(exercise_id, limit=1)
            if last_performance:
                last_workout_sets = [
                    s
                    for s in last_performance
                    if s["workout_id"] == last_performance[0]["workout_id"]
                ]
                last_date = last_performance[0]["workout_date"]
                console.print()
                console.print(
                    format_exercise_performance(exercise_name, last_workout_sets, last_date)
                )

            # Log sets for this exercise
            console.print(f"\n[bold]Logging sets for {exercise_name}[/bold]")
            console.print(
                "[dim]Format: <weight> <reps> [rpe] or use shortcuts: s (same), +5/-5 (adjust weight)[/dim]"
            )
            console.print()

            workout_state["exercises"].add(exercise_id)  # type: ignore[attr-defined]
            set_number = 1
            last_set_data = None

            while True:
                set_input = Prompt.ask(f"[cyan]Set {set_number}[/cyan]", default="done")

                if set_input.lower() == "done":
                    break

                parsed = _parse_set_input(set_input, last_set_data, rpe_enabled)

                if not parsed:
                    console.print("[red]Invalid input. Use format: weight reps [rpe][/red]")
                    continue

                weight, reps, rpe = parsed

                set_create = SetCreate(
                    workout_id=workout.id,
                    exercise_id=exercise_id,
                    set_number=set_number,
                    weight=weight,
                    weight_unit=WeightUnit.LBS,
                    reps=reps,
                    rpe=rpe,
                    set_type=SetType.WORKING,
                    rest_seconds=None,
                )

                try:
                    created_set = set_service.add_set(set_create)
                    volume = calculate_volume_load(weight, reps)

                    is_pr = False
                    if last_performance:
                        best_weight = max(s["weight"] for s in last_performance)
                        if weight > best_weight:
                            is_pr = True

                    console.print(format_set_completion(weight, reps, rpe, volume, is_pr))

                    workout_state["total_volume"] = workout_state["total_volume"] + volume  # type: ignore[operator]
                    workout_state["total_sets"] = workout_state["total_sets"] + 1  # type: ignore[operator]
                    last_set_data = {"weight": weight, "reps": reps, "rpe": rpe}
                    set_number += 1

                except Exception as e:
                    console.print(f"[red]Error saving set: {e}[/red]")
                    continue

            # Show completion vs target
            console.print(
                f"\n[dim]Completed {set_number - 1}/{prog_exercise.target_sets} target sets[/dim]"
            )

            # Ask if user wants to continue
            if idx < len(program_context["exercises"]) and not Confirm.ask(  # type: ignore[index, arg-type]
                "\nContinue to next exercise?", default=True
            ):
                break
    else:
        # Freestyle workout: existing logic
        while True:
            console.print()
            exercise_name = Prompt.ask(
                "[bold cyan]Enter exercise name[/bold cyan] (or 'done' to finish)",
                default="done",
            )

            if exercise_name.lower() == "done":
                break

            exercise_id = _lookup_exercise(db, exercise_name)

            if not exercise_id:
                console.print(
                    f"[yellow]Exercise '{exercise_name}' not found. Creating as custom exercise.[/yellow]"
                )
                exercise_id = 1  # Placeholder

            workout_state["exercises"].add(exercise_id)  # type: ignore[attr-defined]

            # Show last performance
            last_performance = workout_service.get_last_performance(exercise_id, limit=1)
            if last_performance:
                last_workout_sets = [
                    s
                    for s in last_performance
                    if s["workout_id"] == last_performance[0]["workout_id"]
                ]
                last_date = last_performance[0]["workout_date"]
                console.print()
                console.print(
                    format_exercise_performance(exercise_name, last_workout_sets, last_date)
                )

            # Log sets for this exercise
            console.print(f"\n[bold]Logging sets for {exercise_name}[/bold]")
            console.print(
                "[dim]Format: <weight> <reps> [rpe] or use shortcuts: s (same), +5/-5 (adjust weight)[/dim]"
            )
            console.print()

            set_number = 1
            last_set_data = None

            while True:
                set_input = Prompt.ask(f"[cyan]Set {set_number}[/cyan]", default="done")

                if set_input.lower() == "done":
                    break

                parsed = _parse_set_input(set_input, last_set_data, rpe_enabled)

                if not parsed:
                    console.print("[red]Invalid input. Use format: weight reps [rpe][/red]")
                    continue

                weight, reps, rpe = parsed

                set_create = SetCreate(
                    workout_id=workout.id,
                    exercise_id=exercise_id,
                    set_number=set_number,
                    weight=weight,
                    weight_unit=WeightUnit.LBS,
                    reps=reps,
                    rpe=rpe,
                    set_type=SetType.WORKING,
                    rest_seconds=None,
                )

                try:
                    created_set = set_service.add_set(set_create)
                    volume = calculate_volume_load(weight, reps)

                    is_pr = False
                    if last_performance:
                        best_weight = max(s["weight"] for s in last_performance)
                        if weight > best_weight:
                            is_pr = True

                    console.print(format_set_completion(weight, reps, rpe, volume, is_pr))

                    workout_state["total_volume"] = workout_state["total_volume"] + volume  # type: ignore[operator]
                    workout_state["total_sets"] = workout_state["total_sets"] + 1  # type: ignore[operator]
                    last_set_data = {"weight": weight, "reps": reps, "rpe": rpe}
                    set_number += 1

                except Exception as e:
                    console.print(f"[red]Error saving set: {e}[/red]")
                    continue

    # Finish workout
    end_time = datetime.now()
    duration_minutes = int((end_time - start_time).total_seconds() / 60)

    try:
        workout = workout_service.finish_workout(workout.id, duration_minutes)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not update workout duration: {e}[/yellow]")

    # Display completion summary
    console.print()
    total_volume: Decimal = workout_state["total_volume"]  # type: ignore[assignment]
    total_sets: int = workout_state["total_sets"]  # type: ignore[assignment]
    exercises_set: set[int] = workout_state["exercises"]  # type: ignore[assignment]
    console.print(
        format_workout_complete(
            duration_minutes,
            total_volume,
            total_sets,
            len(exercises_set),
        )
    )


@workout_app.command("log")
def log_workout(
    ctx: typer.Context,
    name: str | None = typer.Option(None, "--name", "-n", help="Workout name"),
) -> None:
    """
    Quick manual workout logging (simpler than interactive session).

    This provides a simpler interface for logging workouts after the fact.
    """
    console.print("[yellow]Quick workout logging coming soon![/yellow]")
    console.print("For now, use 'lift workout start' for interactive logging.")


@workout_app.command("last")
def show_last_workout(ctx: typer.Context) -> None:
    """Show details of the last workout."""
    db = get_db(ctx.obj.get("db_path"))
    workout_service = WorkoutService(db)
    set_service = SetService(db)

    last_workout = workout_service.get_last_workout()

    if not last_workout:
        console.print("[yellow]No workouts found.[/yellow]")
        raise typer.Exit(0)

    # Get workout summary
    summary = workout_service.get_workout_summary(last_workout.id)

    # Display summary
    console.print()
    console.print(format_workout_summary(last_workout, summary, console))

    # Get and display sets
    sets = set_service.get_sets_for_workout(last_workout.id)

    if sets:
        console.print()
        console.print("[bold]Sets:[/bold]")

        # Group sets by exercise
        from itertools import groupby

        sets_by_exercise = groupby(sets, key=lambda s: s.exercise_id)

        for exercise_id, exercise_sets in sets_by_exercise:
            exercise_sets_list = list(exercise_sets)

            console.print(f"\n[cyan]Exercise {exercise_id}:[/cyan]")

            table = Table(show_header=True, header_style="bold magenta", box=None)
            table.add_column("Set", justify="center")
            table.add_column("Weight", justify="right")
            table.add_column("Reps", justify="center")
            table.add_column("Volume", justify="right")
            table.add_column("RPE", justify="center")

            for set_obj in exercise_sets_list:
                volume = set_obj.weight * set_obj.reps
                rpe_str = f"{set_obj.rpe:.1f}" if set_obj.rpe else "-"

                table.add_row(
                    str(set_obj.set_number),
                    f"{set_obj.weight} {set_obj.weight_unit.value}",
                    str(set_obj.reps),
                    f"{volume:,.0f}",
                    rpe_str,
                )

            console.print(table)


@workout_app.command("history")
def show_history(
    ctx: typer.Context,
    limit: int = typer.Option(10, "--limit", "-l", help="Number of workouts to show"),
) -> None:
    """Show workout history."""
    db = get_db(ctx.obj.get("db_path"))
    workout_service = WorkoutService(db)

    workouts = workout_service.get_recent_workouts(limit=limit)

    if not workouts:
        console.print("[yellow]No workouts found.[/yellow]")
        raise typer.Exit(0)

    # Get summaries for each workout
    workout_data = []
    for workout in workouts:
        summary = workout_service.get_workout_summary(workout.id)
        workout_data.append((workout, summary))

    # Display table
    console.print()
    console.print(f"[bold]Last {len(workouts)} Workouts[/bold]")
    console.print()
    console.print(format_workout_list(workout_data))


@workout_app.command("delete")
def delete_workout(
    ctx: typer.Context,
    workout_id: int = typer.Argument(..., help="Workout ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a workout."""
    db = get_db(ctx.obj.get("db_path"))
    workout_service = WorkoutService(db)

    # Get workout to confirm
    workout = workout_service.get_workout(workout_id)

    if not workout:
        console.print(f"[red]Workout {workout_id} not found.[/red]")
        raise typer.Exit(1)

    # Confirm deletion
    if not force:
        workout_name = workout.name or "Workout"
        date_str = workout.date.strftime("%B %d, %Y")

        if not Confirm.ask(
            f"Delete workout '{workout_name}' from {date_str}?",
            default=False,
        ):
            console.print("[yellow]Deletion cancelled.[/yellow]")
            raise typer.Exit(0)

    # Delete workout
    try:
        workout_service.delete_workout(workout_id)
        console.print(f"[green]Workout {workout_id} deleted successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error deleting workout: {e}[/red]")
        raise typer.Exit(1)


# Helper functions


def _parse_set_input(
    input_str: str, last_set: dict | None, rpe_enabled: bool
) -> tuple[Decimal, int, Decimal | None] | None:
    """
    Parse set input with shortcuts.

    Formats:
    - "185 10" -> 185 lbs, 10 reps
    - "185 10 8.5" -> 185 lbs, 10 reps, RPE 8.5
    - "s" -> same as last set
    - "+5" -> last weight + 5 lbs, same reps
    - "-5" -> last weight - 5 lbs, same reps
    - "+5 8" -> last weight + 5 lbs, 8 reps

    Returns:
        Tuple of (weight, reps, rpe) or None if invalid
    """
    input_str = input_str.strip().lower()

    # Handle "same" shortcut
    if input_str == "s" and last_set:
        return (
            last_set["weight"],
            last_set["reps"],
            last_set.get("rpe"),
        )

    # Handle weight adjustment shortcuts
    adjustment_match = re.match(r"^([+-]\d+)(?:\s+(\d+)(?:\s+([\d.]+))?)?$", input_str)
    if adjustment_match and last_set:
        adjustment = Decimal(adjustment_match.group(1))
        weight = last_set["weight"] + adjustment

        if adjustment_match.group(2):
            reps = int(adjustment_match.group(2))
        else:
            reps = last_set["reps"]

        rpe = None
        if adjustment_match.group(3) and rpe_enabled:
            rpe = Decimal(adjustment_match.group(3))

        return (weight, reps, rpe)

    # Handle standard input: weight reps [rpe]
    standard_match = re.match(r"^([\d.]+)\s+(\d+)(?:\s+([\d.]+))?$", input_str)
    if standard_match:
        weight = Decimal(standard_match.group(1))
        reps = int(standard_match.group(2))

        rpe = None
        if standard_match.group(3) and rpe_enabled:
            rpe = Decimal(standard_match.group(3))

        return (weight, reps, rpe)

    return None


def _lookup_exercise(db: DatabaseManager, exercise_name: str) -> int | None:
    """
    Look up exercise by name (fuzzy matching).

    Returns:
        Exercise ID if found, None otherwise
    """
    try:
        with db.get_connection() as conn:
            # Try exact match first
            result = conn.execute(
                "SELECT id FROM exercises WHERE LOWER(name) = ?",
                (exercise_name.lower(),),
            ).fetchone()

            if result:
                return int(result[0])

            # Try fuzzy match (contains)
            result = conn.execute(
                "SELECT id, name FROM exercises WHERE LOWER(name) LIKE ?",
                (f"%{exercise_name.lower()}%",),
            ).fetchone()

            if result:
                console.print(f"[dim]Found exercise: {result[1]}[/dim]")
                return int(result[0])

    except Exception as e:
        console.print(f"[dim]Could not look up exercise: {e}[/dim]")

    return None


def _get_setting(db: DatabaseManager, key: str, default: str = "") -> str:
    """Get a setting value from the database."""
    try:
        with db.get_connection() as conn:
            result = conn.execute(
                "SELECT value FROM settings WHERE key = ?",
                (key,),
            ).fetchone()

            if result:
                return str(result[0])

    except Exception:
        pass

    return default
