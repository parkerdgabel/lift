"""Workout CLI commands for logging and tracking workouts."""

import re
import sys
import time
from datetime import datetime
from decimal import Decimal

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from lift.core.database import DatabaseManager, get_db
from lift.core.models import SetCreate, SetType, WeightUnit, Workout, WorkoutCreate
from lift.services.config_service import ConfigService
from lift.services.program_service import ProgramService
from lift.services.set_service import SetService
from lift.services.workout_service import WorkoutService
from lift.utils.calculations import calculate_volume_load, suggest_next_weight
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
    """Start an interactive workout session.

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

    # Check for incomplete workouts and warn user
    incomplete = workout_service.get_incomplete_workouts(limit=1)
    if incomplete and not freestyle:
        console.print(
            f"\n[yellow]⚠ You have an incomplete workout from {incomplete[0].date.strftime('%Y-%m-%d %H:%M')}[/yellow]"
        )
        console.print(
            "[dim]Use 'lift workout incomplete' to view, 'lift workout resume <id>' to continue it,"
        )
        console.print(
            "'lift workout complete <id>' to finish it, or 'lift workout abandon <id>' to delete it[/dim]\n"
        )

        if not Confirm.ask("Start a new workout anyway?", default=True):
            raise typer.Exit(0)

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

    # Get rest timer default
    config_service = ConfigService(db)
    rest_timer_seconds = config_service.get_rest_timer_default()

    # Track workout state
    workout_state = {
        "total_volume": Decimal("0"),
        "total_sets": 0,
        "exercises": set(),
        "completed_indices": set(),  # Track completed exercise indices
        "skipped_indices": set(),  # Track skipped exercise indices
    }

    # Main workout loop
    if program_context:
        # Program-based workout: flexible exercise navigation
        exercises = program_context["exercises"]  # type: ignore[index]
        current_idx = 0

        while current_idx < len(exercises):  # type: ignore[arg-type]
            # Skip if already completed
            if current_idx in workout_state["completed_indices"]:  # type: ignore[operator]
                current_idx += 1
                continue

            exercise_data = exercises[current_idx]  # type: ignore[index]
            prog_exercise = exercise_data["program_exercise"]
            exercise_id = prog_exercise.exercise_id
            exercise_name = exercise_data["exercise_name"]

            console.print()
            console.print(
                f"\n[bold cyan]Exercise {current_idx + 1} of {len(exercises)}: {exercise_name}[/bold cyan]"  # type: ignore[arg-type]
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

                # Show weight suggestion based on last performance
                try:
                    suggested_weight = suggest_next_weight(last_workout_sets)
                    console.print(
                        f"[dim]💡 Suggested starting weight: [cyan]{suggested_weight} lbs[/cyan][/dim]"
                    )
                except (ValueError, KeyError):
                    # Not enough data for suggestion
                    pass

            # Log sets for this exercise
            console.print(f"\n[bold]Logging sets for {exercise_name}[/bold]")
            console.print(
                "[dim]Format: <weight> <reps> [rpe] or use shortcuts: s (same), +5/-5 (adjust weight)[/dim]"
            )
            console.print()

            workout_state["exercises"].add(exercise_id)  # type: ignore[attr-defined]
            set_number = 1
            last_set_data = None
            exercise_sets: list[dict] = []  # Track sets for this exercise

            while True:
                set_input = Prompt.ask(f"[cyan]Set {set_number}[/cyan]", default="done")

                if set_input.lower() == "done":
                    break

                parsed = _parse_set_input(set_input, last_set_data, rpe_enabled)

                if not parsed:
                    console.print("[red]Invalid input. Use format: weight reps [rpe][/red]")
                    continue

                weight, reps, rpe = parsed

                try:
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

                    # Track set for summary table
                    exercise_sets.append(
                        {
                            "set_number": set_number,
                            "weight": weight,
                            "reps": reps,
                            "rpe": rpe,
                            "volume": volume,
                        }
                    )

                    set_number += 1

                    # Start rest timer (user can skip with ENTER)
                    _start_rest_timer(rest_timer_seconds)

                except ValidationError as e:
                    # Extract validation error details for user-friendly message
                    error_details = []
                    for error in e.errors():
                        field = error["loc"][0] if error["loc"] else "unknown"
                        msg = error["msg"]
                        if field == "rpe" and "greater_than_equal" in error["type"]:
                            error_details.append(f"RPE must be between 6.0 and 10.0 (got {rpe})")
                        elif field == "weight" and "greater_than_equal" in error["type"]:
                            error_details.append(f"Weight must be greater than 0 (got {weight})")
                        elif field == "reps" and "greater_than_equal" in error["type"]:
                            error_details.append(f"Reps must be at least 1 (got {reps})")
                        else:
                            error_details.append(f"{field}: {msg}")

                    console.print(f"[red]Invalid input: {', '.join(error_details)}[/red]")
                    console.print("[dim]Please try again with valid values[/dim]")
                    continue
                except Exception as e:
                    console.print(f"[red]Error saving set: {e}[/red]")
                    continue

            # Show completion vs target
            console.print(
                f"\n[dim]Completed {set_number - 1}/{prog_exercise.target_sets} target sets[/dim]"
            )

            # Show set summary table
            _show_set_summary_table(exercise_name, exercise_sets)

            # Show progress dashboard
            _show_progress_dashboard(
                workout_state,
                start_time,
                current_idx + 1,
                len(exercises),  # type: ignore[arg-type]
            )

            # Mark as completed
            workout_state["completed_indices"].add(current_idx)  # type: ignore[attr-defined]

            # Show navigation menu
            if current_idx < len(exercises) - 1:  # type: ignore[arg-type]
                action = _show_exercise_menu(
                    current_idx,
                    exercises,  # type: ignore[arg-type]
                    workout_state["completed_indices"],  # type: ignore[arg-type]
                    workout_state["skipped_indices"],  # type: ignore[arg-type]
                )

                if action == "next":
                    current_idx += 1
                elif action == "skip":
                    # Prompt for exercise number
                    while True:
                        try:
                            skip_to = Prompt.ask(
                                f"Enter exercise number (1-{len(exercises)})",  # type: ignore[arg-type]
                                default=str(current_idx + 2),
                            )
                            skip_to_idx = int(skip_to) - 1

                            if 0 <= skip_to_idx < len(exercises):  # type: ignore[arg-type]
                                # Mark current as skipped (already logged some sets though)
                                current_idx = skip_to_idx
                                break

                            console.print(
                                f"[yellow]Invalid exercise number. Use 1-{len(exercises)}[/yellow]"
                            )  # type: ignore[arg-type]
                        except ValueError:
                            console.print("[yellow]Please enter a valid number[/yellow]")

                elif action == "view":
                    _show_remaining_exercises(
                        exercises,  # type: ignore[arg-type]
                        current_idx,
                        workout_state["completed_indices"],  # type: ignore[arg-type]
                        workout_state["skipped_indices"],  # type: ignore[arg-type]
                    )
                    # Don't increment, will show menu again for same exercise
                    continue

                elif action == "finish":
                    # Mark remaining as skipped
                    for idx in range(current_idx + 1, len(exercises)):  # type: ignore[arg-type]
                        if idx not in workout_state["completed_indices"]:  # type: ignore[operator]
                            workout_state["skipped_indices"].add(idx)  # type: ignore[attr-defined]
                    break
            else:
                # Last exercise, move on
                current_idx += 1

        # Prompt for skipped exercises
        _prompt_for_skipped_exercises(
            exercises,  # type: ignore[arg-type]
            workout_state["skipped_indices"],  # type: ignore[arg-type]
            workout,
            workout_service,
            set_service,
            workout_state,
            rpe_enabled,
        )
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

                # Show weight suggestion based on last performance
                try:
                    suggested_weight = suggest_next_weight(last_workout_sets)
                    console.print(
                        f"[dim]💡 Suggested starting weight: [cyan]{suggested_weight} lbs[/cyan][/dim]"
                    )
                except (ValueError, KeyError):
                    # Not enough data for suggestion
                    pass

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

                try:
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

                    # Start rest timer (user can skip with ENTER)
                    _start_rest_timer(rest_timer_seconds)

                except ValidationError as e:
                    # Extract validation error details for user-friendly message
                    error_details = []
                    for error in e.errors():
                        field = error["loc"][0] if error["loc"] else "unknown"
                        msg = error["msg"]
                        if field == "rpe" and "greater_than_equal" in error["type"]:
                            error_details.append(f"RPE must be between 6.0 and 10.0 (got {rpe})")
                        elif field == "weight" and "greater_than_equal" in error["type"]:
                            error_details.append(f"Weight must be greater than 0 (got {weight})")
                        elif field == "reps" and "greater_than_equal" in error["type"]:
                            error_details.append(f"Reps must be at least 1 (got {reps})")
                        else:
                            error_details.append(f"{field}: {msg}")

                    console.print(f"[red]Invalid input: {', '.join(error_details)}[/red]")
                    console.print("[dim]Please try again with valid values[/dim]")
                    continue
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
    """Quick manual workout logging (simpler than interactive session).

    This provides a simpler interface for logging workouts after the fact.
    """
    console.print("[yellow]Quick workout logging coming soon![/yellow]")
    console.print("For now, use 'lift workout start' for interactive logging.")


@workout_app.command("incomplete")
def show_incomplete_workouts(ctx: typer.Context) -> None:
    """Show incomplete workouts that can be resumed or abandoned."""
    db = get_db(ctx.obj.get("db_path"))
    workout_service = WorkoutService(db)
    set_service = SetService(db)

    incomplete = workout_service.get_incomplete_workouts(limit=10)

    if not incomplete:
        console.print("[green]No incomplete workouts found.[/green]")
        return

    console.print(f"\n[bold]Incomplete Workouts ({len(incomplete)})[/bold]\n")

    for workout in incomplete:
        # Get sets for this workout
        sets = set_service.get_sets_for_workout(workout.id)
        exercises = {s.exercise_id for s in sets}

        # Calculate duration
        if workout.duration_minutes:
            duration = f"{workout.duration_minutes}m"
        else:
            # Calculate elapsed time since workout start
            elapsed = datetime.now() - workout.date
            duration = f"{int(elapsed.total_seconds() / 60)}m ago"

        console.print(
            f"[cyan]ID {workout.id}[/cyan] - {workout.name or 'Workout'} "
            f"({workout.date.strftime('%Y-%m-%d %H:%M')})"
        )
        console.print(f"  [dim]{len(sets)} sets, {len(exercises)} exercises, {duration}[/dim]")
        console.print()

    console.print("[dim]Use 'lift workout resume <id>' to continue an incomplete workout[/dim]")
    console.print("[dim]Use 'lift workout complete <id>' to mark a workout as complete[/dim]")
    console.print("[dim]Use 'lift workout abandon <id>' to delete an incomplete workout[/dim]")


@workout_app.command("complete")
def complete_workout_cmd(
    ctx: typer.Context,
    workout_id: int = typer.Argument(..., help="Workout ID to mark as complete"),
) -> None:
    """Mark an incomplete workout as complete."""
    db = get_db(ctx.obj.get("db_path"))
    workout_service = WorkoutService(db)

    try:
        workout = workout_service.get_workout(workout_id)
        if not workout:
            console.print(f"[red]Workout {workout_id} not found[/red]")
            raise typer.Exit(1)

        if workout.completed:
            console.print(f"[yellow]Workout {workout_id} is already complete[/yellow]")
            return

        # Calculate duration if not set
        duration = workout.duration_minutes
        if not duration:
            elapsed = datetime.now() - workout.date
            duration = int(elapsed.total_seconds() / 60)

        workout = workout_service.finish_workout(workout_id, duration)
        console.print(f"[green]✓[/green] Workout {workout_id} marked as complete ({duration}m)")

    except Exception as e:
        console.print(f"[red]Error completing workout: {e}[/red]")
        raise typer.Exit(1)


@workout_app.command("abandon")
def abandon_workout(
    ctx: typer.Context,
    workout_id: int = typer.Argument(..., help="Workout ID to abandon"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an incomplete workout."""
    db = get_db(ctx.obj.get("db_path"))
    workout_service = WorkoutService(db)
    set_service = SetService(db)

    try:
        workout = workout_service.get_workout(workout_id)
        if not workout:
            console.print(f"[red]Workout {workout_id} not found[/red]")
            raise typer.Exit(1)

        if workout.completed and not force:
            console.print(
                f"[yellow]Workout {workout_id} is already complete. Use --force to delete anyway[/yellow]"
            )
            raise typer.Exit(1)

        # Show workout info
        sets = set_service.get_sets_for_workout(workout_id)
        exercises = {s.exercise_id for s in sets}

        console.print(
            f"\n[yellow]About to delete workout {workout_id}:[/yellow]\n"
            f"  Name: {workout.name or 'Workout'}\n"
            f"  Date: {workout.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"  Sets: {len(sets)}\n"
            f"  Exercises: {len(exercises)}\n"
        )

        if not force and not Confirm.ask("Delete this workout?", default=False):
            console.print("[dim]Cancelled[/dim]")
            return

        workout_service.delete_workout(workout_id)
        console.print(f"[green]✓[/green] Workout {workout_id} deleted")

    except Exception as e:
        console.print(f"[red]Error abandoning workout: {e}[/red]")
        raise typer.Exit(1)


@workout_app.command("resume")
def resume_workout(
    ctx: typer.Context,
    workout_id: int = typer.Argument(..., help="Workout ID to resume"),
) -> None:
    """Resume an incomplete workout.

    Continue adding sets to a previously started workout. Works with both
    program-based and freestyle workouts.
    """
    db = get_db(ctx.obj.get("db_path"))
    workout_service = WorkoutService(db)
    set_service = SetService(db)
    program_service = ProgramService(db)

    # Load workout
    workout = workout_service.get_workout(workout_id)
    if not workout:
        console.print(f"[red]Workout {workout_id} not found[/red]")
        raise typer.Exit(1)

    # Warn if already complete
    if workout.completed:
        console.print(f"[yellow]Warning: Workout {workout_id} is already marked complete[/yellow]")
        if not Confirm.ask("Resume anyway?", default=False):
            raise typer.Exit(0)

    # Load existing sets
    existing_sets = set_service.get_sets_for_workout(workout_id)

    # Reconstruct workout state
    workout_state = _reconstruct_workout_state(existing_sets)

    # Group sets by exercise for display
    sets_by_exercise = _group_sets_by_exercise(existing_sets)

    # Load exercise service for names
    from lift.services.exercise_service import ExerciseService

    exercise_service = ExerciseService(db)

    # Check if RPE is enabled
    rpe_enabled = _get_setting(db, "enable_rpe", "true") == "true"

    # Determine if this was a program workout
    program_context: dict | None = None
    if workout.program_workout_id:
        try:
            # Try to load program context
            exercises = program_service.get_workout_exercises(workout.program_workout_id)
            if exercises:
                # Find which exercises have been completed
                completed_exercise_ids = set(sets_by_exercise.keys())

                # Map program exercises to completion status
                for idx, exercise_data in enumerate(exercises):
                    exercise_id = exercise_data["program_exercise"].exercise_id
                    if exercise_id in completed_exercise_ids:
                        workout_state["completed_indices"].add(idx)  # type: ignore[attr-defined]

                program_context = {
                    "exercises": exercises,
                }
        except Exception:
            # Program may have been deleted, continue as freestyle
            pass

    # Display resume header
    console.print()
    console.print(f"[bold cyan]Resuming: {workout.name or 'Workout'}[/bold cyan]")
    console.print(f"[dim]Started: {workout.date.strftime('%Y-%m-%d %H:%M')}[/dim]")
    console.print("[cyan]" + "═" * 50 + "[/cyan]")

    # Show completed exercises
    if sets_by_exercise:
        console.print("\n[bold]Already completed:[/bold]")
        for exercise_id, sets in sets_by_exercise.items():
            exercise = exercise_service.get_by_id(exercise_id)
            exercise_name = exercise.name if exercise else f"Exercise {exercise_id}"

            total_volume = sum(s.weight * s.reps for s in sets)
            avg_rpe = (
                sum(s.rpe for s in sets if s.rpe) / len([s for s in sets if s.rpe])
                if any(s.rpe for s in sets)
                else None
            )

            rpe_str = f", avg RPE {avg_rpe:.1f}" if avg_rpe else ""
            console.print(
                f"  [green]✓[/green] {exercise_name} ({len(sets)} sets, {total_volume:,} lbs{rpe_str})"
            )

    # Show remaining exercises for program workouts
    if program_context:
        remaining_indices = [
            idx
            for idx in range(len(program_context["exercises"]))  # type: ignore[arg-type]
            if idx not in workout_state["completed_indices"]  # type: ignore[operator]
        ]

        if remaining_indices:
            console.print("\n[bold]Remaining exercises:[/bold]")
            for idx in remaining_indices:
                exercise_data = program_context["exercises"][idx]  # type: ignore[index]
                prog_exercise = exercise_data["program_exercise"]
                console.print(
                    f"  [ ] {exercise_data['exercise_name']} ({prog_exercise.target_sets} sets)"
                )

    # Show current stats
    console.print()
    elapsed = datetime.now() - workout.date
    elapsed_minutes = int(elapsed.total_seconds() / 60)
    hours = elapsed_minutes // 60
    mins = elapsed_minutes % 60
    elapsed_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

    console.print("[bold]Current Progress:[/bold]")
    console.print(
        f"  [dim]•[/dim] Duration: {elapsed_str} elapsed "
        f"[dim]•[/dim] Sets: {workout_state['total_sets']} "
        f"[dim]•[/dim] Volume: {workout_state['total_volume']:,} lbs"
    )
    console.print("[cyan]" + "═" * 50 + "[/cyan]")
    console.print()

    # Confirm resume
    if not Confirm.ask("Continue workout?", default=True):
        console.print("[dim]Resume cancelled[/dim]")
        raise typer.Exit(0)

    # Use original start time for duration calculation
    start_time = workout.date

    # Resume workout session
    # TODO: This needs refactoring to share code with start_workout()
    # For now, implement similar logic inline

    console.print()

    # Check if RPE is enabled
    rpe_enabled = _get_setting(db, "enable_rpe", "true") == "true"

    # Continue with remaining exercises or freestyle
    if program_context:
        # Program workout - continue with remaining exercises
        exercises = program_context["exercises"]  # type: ignore[index]
        current_idx = 0

        # Start from first uncompleted exercise
        while current_idx < len(exercises) and current_idx in workout_state["completed_indices"]:  # type: ignore[arg-type, operator]
            current_idx += 1

        # Resume exercise logging loop
        while current_idx < len(exercises):  # type: ignore[arg-type]
            # Skip if already completed
            if current_idx in workout_state["completed_indices"]:  # type: ignore[operator]
                current_idx += 1
                continue

            exercise_data = exercises[current_idx]  # type: ignore[index]
            prog_exercise = exercise_data["program_exercise"]
            exercise_id = prog_exercise.exercise_id
            exercise_name = exercise_data["exercise_name"]

            console.print()
            console.print(
                f"\n[bold cyan]Exercise {current_idx + 1} of {len(exercises)}: {exercise_name}[/bold cyan]"  # type: ignore[arg-type]
            )

            # Display program prescription
            console.print()
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

            # Track exercise
            workout_state["exercises"].add(exercise_id)  # type: ignore[attr-defined]

            # Log sets for this exercise (continue from last set number if resuming)
            starting_set = workout_state["exercise_last_set"].get(exercise_id, 0) + 1  # type: ignore[union-attr]
            sets_logged = _log_sets_for_exercise(
                workout.id,
                exercise_id,
                exercise_name,
                set_service,
                workout_state,
                rpe_enabled,
                starting_set_number=starting_set,
                last_performance=last_performance,
            )

            # Show completion vs target
            total_sets = workout_state["exercise_last_set"].get(exercise_id, 0) + sets_logged  # type: ignore[union-attr]
            console.print(
                f"\n[dim]Completed {total_sets}/{prog_exercise.target_sets} target sets[/dim]"
            )

            # Mark as completed
            workout_state["completed_indices"].add(current_idx)  # type: ignore[attr-defined]

            # Show navigation menu
            if current_idx < len(exercises) - 1:  # type: ignore[arg-type]
                action = _show_exercise_menu(
                    current_idx,
                    exercises,  # type: ignore[arg-type]
                    workout_state["completed_indices"],  # type: ignore[arg-type]
                    workout_state["skipped_indices"],  # type: ignore[arg-type]
                )

                if action == "next":
                    current_idx += 1
                elif action == "skip":
                    # Prompt for exercise number
                    while True:
                        try:
                            skip_to = Prompt.ask(
                                f"Enter exercise number (1-{len(exercises)})",  # type: ignore[arg-type]
                                default=str(current_idx + 2),
                            )
                            skip_to_idx = int(skip_to) - 1

                            if 0 <= skip_to_idx < len(exercises):  # type: ignore[arg-type]
                                current_idx = skip_to_idx
                                break

                            console.print(
                                f"[yellow]Invalid exercise number. Use 1-{len(exercises)}[/yellow]"
                            )  # type: ignore[arg-type]
                        except ValueError:
                            console.print("[yellow]Please enter a valid number[/yellow]")

                elif action == "view":
                    _show_remaining_exercises(
                        exercises,  # type: ignore[arg-type]
                        current_idx,
                        workout_state["completed_indices"],  # type: ignore[arg-type]
                        workout_state["skipped_indices"],  # type: ignore[arg-type]
                    )
                    # Don't increment, will show menu again for same exercise
                    continue

                elif action == "finish":
                    # Mark remaining as skipped
                    for idx in range(current_idx + 1, len(exercises)):  # type: ignore[arg-type]
                        if idx not in workout_state["completed_indices"]:  # type: ignore[operator]
                            workout_state["skipped_indices"].add(idx)  # type: ignore[attr-defined]
                    break
            else:
                # Last exercise, move on
                current_idx += 1

        # Prompt for skipped exercises
        _prompt_for_skipped_exercises(
            exercises,  # type: ignore[arg-type]
            workout_state["skipped_indices"],  # type: ignore[arg-type]
            workout,
            workout_service,
            set_service,
            workout_state,
            rpe_enabled,
        )

    else:
        # Freestyle workout - allow adding more exercises
        console.print("[bold]Continue adding exercises (or type 'done' to finish)[/bold]")
        console.print()

        # Resume freestyle workout
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

            # Log sets for this exercise (continue from last set number if resuming this exercise)
            starting_set = workout_state["exercise_last_set"].get(exercise_id, 0) + 1  # type: ignore[union-attr]
            _log_sets_for_exercise(
                workout.id,
                exercise_id,
                exercise_name,
                set_service,
                workout_state,
                rpe_enabled,
                starting_set_number=starting_set,
                last_performance=last_performance,
            )

    # Finish workout
    end_time = datetime.now()
    duration_minutes = int((end_time - start_time).total_seconds() / 60)

    try:
        workout = workout_service.finish_workout(workout.id, duration_minutes)
        console.print(
            f"\n[green]✓[/green] Workout resumed and completed ({duration_minutes}m total)"
        )
    except Exception as e:
        console.print(f"[yellow]Warning: Could not update workout duration: {e}[/yellow]")


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
    """Parse set input with shortcuts.

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
    """Look up exercise by name (fuzzy matching).

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


def _show_set_summary_table(exercise_name: str, sets_data: list[dict]) -> None:
    """
    Display summary table of completed sets for an exercise.

    Args:
        exercise_name: Name of the exercise
        sets_data: List of set data dictionaries with weight, reps, rpe, etc.

    Returns:
        None
    """
    if not sets_data:
        return

    console.print()
    console.print(f"[bold]{exercise_name} - Set Summary[/bold]")

    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
    table.add_column("Set", style="dim", width=4)
    table.add_column("Weight", justify="right", width=8)
    table.add_column("Reps", justify="right", width=5)
    table.add_column("RPE", justify="right", width=5)
    table.add_column("Volume", justify="right", width=9)

    for set_data in sets_data:
        set_num = str(set_data["set_number"])
        weight = f"{set_data['weight']} lbs"
        reps = str(set_data["reps"])
        rpe = f"{set_data['rpe']}" if set_data.get("rpe") else "-"
        volume = f"{set_data['volume']:,} lbs"

        table.add_row(set_num, weight, reps, rpe, volume)

    # Add total row
    total_volume = sum(s["volume"] for s in sets_data)
    total_sets = len(sets_data)
    table.add_row(
        f"[bold]{total_sets}[/bold]",
        "",
        "",
        "",
        f"[bold]{total_volume:,} lbs[/bold]",
        style="bold",
    )

    console.print(table)
    console.print()


def _show_progress_dashboard(
    workout_state: dict, start_time: datetime, current_exercise_num: int, total_exercises: int
) -> None:
    """
    Display current workout progress dashboard.

    Args:
        workout_state: Dictionary with total_volume, total_sets, exercises
        start_time: Workout start time
        current_exercise_num: Current exercise number (1-indexed)
        total_exercises: Total number of exercises in workout

    Returns:
        None
    """
    elapsed = datetime.now() - start_time
    minutes = int(elapsed.total_seconds() / 60)

    # Format duration
    hours = minutes // 60
    mins = minutes % 60
    duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

    console.print()
    console.print("[bold cyan]═══ Workout Progress ═══[/bold cyan]")
    console.print(
        f"[dim]Exercise:[/dim] {current_exercise_num}/{total_exercises}  "
        f"[dim]│[/dim]  [dim]Duration:[/dim] {duration_str}  "
        f"[dim]│[/dim]  [dim]Sets:[/dim] {workout_state['total_sets']}  "
        f"[dim]│[/dim]  [dim]Volume:[/dim] {workout_state['total_volume']:,} lbs"
    )
    console.print("[cyan]═══════════════════════[/cyan]")
    console.print()


def _start_rest_timer(seconds: int, allow_skip: bool = True) -> None:
    """
    Start a countdown rest timer.

    Args:
        seconds: Rest duration in seconds
        allow_skip: Whether to allow skipping the timer

    Returns:
        None
    """
    if seconds <= 0:
        return

    console.print()
    console.print(f"[dim]⏱️  Rest: {seconds}s[/dim]", end="")

    if allow_skip:
        console.print(" [dim](Press ENTER to skip)[/dim]")
    else:
        console.print()

    remaining = seconds

    try:
        import select

        # Unix-like systems can use select
        while remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            time_str = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}s"

            # Clear line and show countdown
            console.print(f"\r⏱️  Rest: {time_str} remaining...", end="", style="dim")

            if allow_skip:
                # Check if input is available (non-blocking)
                ready, _, _ = select.select([sys.stdin], [], [], 1)
                if ready:
                    sys.stdin.readline()  # Consume the input
                    console.print("\r[dim]Rest timer skipped[/dim]" + " " * 30)
                    return
            else:
                time.sleep(1)

            remaining -= 1

    except (ImportError, AttributeError):
        # Windows or systems without select - use simple countdown
        while remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            time_str = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}s"

            console.print(f"\r⏱️  Rest: {time_str} remaining...", end="", style="dim")
            time.sleep(1)
            remaining -= 1

    console.print("\r✓ Rest complete!" + " " * 30)
    console.print()


def _show_exercise_menu(current_idx: int, exercises: list, completed: set, skipped: set) -> str:
    """Show exercise navigation menu and get user choice.

    Args:
        current_idx: Current exercise index
        exercises: List of all exercises
        completed: Set of completed exercise indices
        skipped: Set of skipped exercise indices

    Returns:
        Action string: "next", "skip", "view", or "finish"

    """
    console.print()

    # Show next exercise name if available
    next_idx = current_idx + 1
    while next_idx < len(exercises) and next_idx in completed:
        next_idx += 1

    if next_idx < len(exercises):
        next_name = exercises[next_idx]["exercise_name"]
        console.print(f"[dim]Next: {next_name}[/dim]\n")

    console.print("[bold]Options:[/bold]")
    if next_idx < len(exercises):
        console.print(f"  [cyan][n][/cyan] Next exercise ({next_name})")
    console.print("  [cyan][s][/cyan] Skip to exercise #")
    console.print("  [cyan][v][/cyan] View all exercises")
    console.print("  [cyan][f][/cyan] Finish workout")

    while True:
        choice = Prompt.ask("Choice", default="n").lower().strip()

        if choice == "n":
            return "next"
        if choice == "s":
            return "skip"
        if choice == "v":
            return "view"
        if choice == "f":
            return "finish"

        console.print("[yellow]Invalid choice. Use n/s/v/f[/yellow]")


def _show_remaining_exercises(
    exercises: list, current_idx: int, completed: set, skipped: set
) -> None:
    """Display table of all exercises with their status.

    Args:
        exercises: List of all exercises
        current_idx: Current exercise index
        completed: Set of completed exercise indices
        skipped: Set of skipped exercise indices

    """
    console.print("\n[bold]All Exercises:[/bold]\n")

    for idx, exercise_data in enumerate(exercises):
        exercise_name = exercise_data["exercise_name"]

        if idx in completed:
            status = "[green]✓[/green]"
            label = "[dim](completed)[/dim]"
        elif idx in skipped:
            status = "[yellow]⊗[/yellow]"
            label = "[yellow](skipped)[/yellow]"
        elif idx == current_idx:
            status = "[cyan]→[/cyan]"
            label = "[cyan](current)[/cyan]"
        else:
            status = "[ ]"
            label = ""

        console.print(f"  {status} {idx + 1}. {exercise_name} {label}")

    console.print()


def _prompt_for_skipped_exercises(
    exercises: list,
    skipped: set,
    workout: Workout,
    workout_service: WorkoutService,
    set_service: SetService,
    workout_state: dict,
    rpe_enabled: bool,
) -> None:
    """Prompt user to complete skipped exercises at the end of workout.

    Args:
        exercises: List of all exercises
        skipped: Set of skipped exercise indices
        workout: Workout object
        workout_service: WorkoutService instance
        set_service: SetService instance
        workout_state: Workout state dictionary
        rpe_enabled: Whether RPE tracking is enabled

    """
    if not skipped:
        return

    console.print("\n[yellow]You skipped the following exercises:[/yellow]")
    for idx in sorted(skipped):
        console.print(f"  - {exercises[idx]['exercise_name']}")

    console.print()

    if not Confirm.ask("Complete skipped exercises now?", default=True):
        return

    # Process each skipped exercise
    for idx in sorted(skipped):
        exercise_data = exercises[idx]
        prog_exercise = exercise_data["program_exercise"]
        exercise_id = prog_exercise.exercise_id
        exercise_name = exercise_data["exercise_name"]

        console.print()
        console.print(f"\n[bold cyan]Skipped Exercise: {exercise_name}[/bold cyan]")

        # Display program prescription
        console.print()
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
                s for s in last_performance if s["workout_id"] == last_performance[0]["workout_id"]
            ]
            last_date = last_performance[0]["workout_date"]
            console.print()
            console.print(format_exercise_performance(exercise_name, last_workout_sets, last_date))

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

            try:
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

            except ValidationError as e:
                # Extract validation error details for user-friendly message
                error_details = []
                for error in e.errors():
                    field = error["loc"][0] if error["loc"] else "unknown"
                    msg = error["msg"]
                    if field == "rpe" and "greater_than_equal" in error["type"]:
                        error_details.append(f"RPE must be between 6.0 and 10.0 (got {rpe})")
                    elif field == "weight" and "greater_than_equal" in error["type"]:
                        error_details.append(f"Weight must be greater than 0 (got {weight})")
                    elif field == "reps" and "greater_than_equal" in error["type"]:
                        error_details.append(f"Reps must be at least 1 (got {reps})")
                    else:
                        error_details.append(f"{field}: {msg}")

                console.print(f"[red]Invalid input: {', '.join(error_details)}[/red]")
                console.print("[dim]Please try again with valid values[/dim]")
                continue
            except Exception as e:
                console.print(f"[red]Error saving set: {e}[/red]")
                continue

        # Show completion vs target
        console.print(
            f"\n[dim]Completed {set_number - 1}/{prog_exercise.target_sets} target sets[/dim]"
        )


def _log_sets_for_exercise(
    workout_id: int,
    exercise_id: int,
    exercise_name: str,
    set_service: SetService,
    workout_state: dict,
    rpe_enabled: bool,
    starting_set_number: int = 1,
    last_performance: list[dict] | None = None,
) -> int:
    """Log sets for a single exercise in an interactive loop.

    Args:
        workout_id: ID of current workout
        exercise_id: ID of exercise to log sets for
        exercise_name: Name of exercise for display
        set_service: SetService instance
        workout_state: Current workout state dict
        rpe_enabled: Whether RPE tracking is enabled
        starting_set_number: Set number to start from (default 1, higher for resume)
        last_performance: Optional last performance data for PR detection

    Returns:
        Number of sets logged

    """
    console.print(f"\n[bold]Logging sets for {exercise_name}[/bold]")
    console.print(
        "[dim]Format: <weight> <reps> [rpe] or use shortcuts: s (same), +5/-5 (adjust weight)[/dim]"
    )
    console.print()

    set_number = starting_set_number
    last_set_data = None
    sets_logged = 0

    while True:
        set_input = Prompt.ask(f"[cyan]Set {set_number}[/cyan]", default="done")

        if set_input.lower() == "done":
            break

        parsed = _parse_set_input(set_input, last_set_data, rpe_enabled)

        if not parsed:
            console.print("[red]Invalid input. Use format: weight reps [rpe][/red]")
            continue

        weight, reps, rpe = parsed

        try:
            set_create = SetCreate(
                workout_id=workout_id,
                exercise_id=exercise_id,
                set_number=set_number,
                weight=weight,
                weight_unit=WeightUnit.LBS,
                reps=reps,
                rpe=rpe,
                set_type=SetType.WORKING,
                rest_seconds=None,
            )

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
            sets_logged += 1

        except ValidationError as e:
            # Extract validation error details for user-friendly message
            error_details = []
            for error in e.errors():
                field = error["loc"][0] if error["loc"] else "unknown"
                msg = error["msg"]
                if field == "rpe" and "greater_than_equal" in error["type"]:
                    error_details.append(f"RPE must be between 6.0 and 10.0 (got {rpe})")
                elif field == "weight" and "greater_than_equal" in error["type"]:
                    error_details.append(f"Weight must be greater than 0 (got {weight})")
                elif field == "reps" and "greater_than_equal" in error["type"]:
                    error_details.append(f"Reps must be at least 1 (got {reps})")
                else:
                    error_details.append(f"{field}: {msg}")

            console.print(f"[red]Invalid input: {', '.join(error_details)}[/red]")
            console.print("[dim]Please try again with valid values[/dim]")
            continue
        except Exception as e:
            console.print(f"[red]Error saving set: {e}[/red]")
            continue

    return sets_logged


def _group_sets_by_exercise(sets: list) -> dict[int, list]:
    """Group sets by exercise ID.

    Args:
        sets: List of Set objects

    Returns:
        Dictionary mapping exercise_id -> list of sets

    """
    grouped: dict[int, list] = {}
    for set_obj in sets:
        if set_obj.exercise_id not in grouped:
            grouped[set_obj.exercise_id] = []
        grouped[set_obj.exercise_id].append(set_obj)
    return grouped


def _reconstruct_workout_state(sets: list, exercises_map: dict[int, str] | None = None) -> dict:
    """Reconstruct workout state from existing sets.

    Args:
        sets: List of Set objects from the workout
        exercises_map: Optional mapping of exercise_id -> exercise_name

    Returns:
        workout_state dict with total_volume, total_sets, exercises, etc.

    """
    from collections import defaultdict

    workout_state = {
        "total_volume": Decimal("0"),
        "total_sets": 0,
        "exercises": set(),
        "completed_indices": set(),
        "skipped_indices": set(),
        "exercise_last_set": defaultdict(int),  # exercise_id -> last set number
    }

    for set_obj in sets:
        # Add to totals
        volume = set_obj.weight * set_obj.reps
        workout_state["total_volume"] = workout_state["total_volume"] + volume  # type: ignore[operator]
        workout_state["total_sets"] += 1  # type: ignore[operator]

        # Track exercises
        workout_state["exercises"].add(set_obj.exercise_id)  # type: ignore[attr-defined]

        # Track last set number per exercise
        workout_state["exercise_last_set"][set_obj.exercise_id] = max(  # type: ignore[index]
            workout_state["exercise_last_set"][set_obj.exercise_id],  # type: ignore[index]
            set_obj.set_number,
        )

    return workout_state
