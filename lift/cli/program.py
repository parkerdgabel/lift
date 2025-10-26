"""CLI commands for managing training programs."""

from decimal import Decimal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from lift.core.database import get_db
from lift.core.models import (
    ProgramCreate,
    ProgramExerciseCreate,
    ProgramWorkoutCreate,
    SplitType,
)
from lift.services.program_service import ProgramService
from lift.utils.program_formatters import (
    format_program_detail,
    format_program_list,
    format_program_summary,
)


program_app = typer.Typer(name="program", help="Manage training programs")
console = Console()


def get_program_service(ctx: typer.Context) -> ProgramService:
    """Get program service instance."""
    db_path = ctx.obj.get("db_path") if ctx.obj else None
    db = get_db(db_path)
    return ProgramService(db)


@program_app.command()
def create(ctx: typer.Context) -> None:
    """Create a new training program interactively.

    Guides you through creating a program with workouts and exercises.
    """
    service = get_program_service(ctx)

    console.print("\n[bold cyan]Create New Training Program[/bold cyan]\n")

    # Get program details
    name = Prompt.ask("[bold]Program name[/bold]")

    # Get split type
    console.print("\n[bold]Split types:[/bold]")
    split_types = list(SplitType)
    for i, split_type in enumerate(split_types, 1):
        console.print(f"  {i}. {split_type.value}")

    split_choice = IntPrompt.ask(
        "\nSelect split type",
        default=1,
        choices=[str(i) for i in range(1, len(split_types) + 1)],
    )
    split_type = split_types[split_choice - 1]

    days_per_week = IntPrompt.ask(
        "[bold]Days per week[/bold]",
        default=3,
        choices=["1", "2", "3", "4", "5", "6", "7"],
    )

    description_input = Prompt.ask("[bold]Description[/bold] (optional)", default="")
    description: str | None = description_input if description_input else None

    duration_weeks_input = Prompt.ask("[bold]Duration in weeks[/bold] (optional)", default="")
    duration_weeks: int | None = None
    if duration_weeks_input:
        duration_weeks = int(duration_weeks_input)

    # Create program
    try:
        program = service.create_program(
            ProgramCreate(
                name=name,
                description=description,
                split_type=split_type,
                days_per_week=days_per_week,
                duration_weeks=duration_weeks,
            )
        )

        console.print(f"\n[green]✓[/green] Program [bold]{program.name}[/bold] created!\n")

    except ValueError as e:
        console.print(f"\n[red]Error:[/red] {e}\n")
        raise typer.Exit(1)

    # Add workouts
    if not Confirm.ask("\nAdd workouts?", default=True):
        return

    workout_num = 1
    while True:
        console.print(f"\n[bold cyan]Workout {workout_num}[/bold cyan]")

        workout_name = Prompt.ask("[bold]Workout name[/bold]")

        day_number_input = Prompt.ask("[bold]Day number[/bold] (1-7, optional)", default="")
        day_number: int | None = None
        if day_number_input:
            day_number = int(day_number_input)

        workout_description_input = Prompt.ask("[bold]Description[/bold] (optional)", default="")
        workout_description: str | None = (
            workout_description_input if workout_description_input else None
        )

        estimated_duration_input = Prompt.ask(
            "[bold]Estimated duration (minutes)[/bold] (optional)", default=""
        )
        estimated_duration: int | None = None
        if estimated_duration_input:
            estimated_duration = int(estimated_duration_input)

        # Create workout
        try:
            workout = service.add_workout_to_program(
                program.id,
                ProgramWorkoutCreate(
                    program_id=program.id,
                    name=workout_name,
                    day_number=day_number,
                    description=workout_description,
                    estimated_duration_minutes=estimated_duration,
                ),
            )

            console.print(f"[green]✓[/green] Workout [bold]{workout.name}[/bold] added!\n")

        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}\n")
            continue

        # Add exercises
        if Confirm.ask("Add exercises?", default=True):
            _add_exercises_interactive(ctx, workout.id)

        workout_num += 1

        if not Confirm.ask("\nAdd another workout?", default=True):
            break

    # Show final program
    console.print("\n")
    _display_program(service, program.name)

    console.print(f"\n[green]✓[/green] Program [bold]{program.name}[/bold] created successfully!\n")


def _add_exercises_interactive(ctx: typer.Context, workout_id: int) -> None:
    """Add exercises to a workout interactively.

    Args:
        ctx: Typer context
        workout_id: Workout ID to add exercises to

    """
    service = get_program_service(ctx)
    db = get_db(ctx.obj.get("db_path") if ctx.obj else None)

    order_number = 1

    while True:
        console.print(f"\n[bold]Exercise {order_number}[/bold]")

        # Get exercise name
        exercise_name = Prompt.ask("Exercise name (or 'done' to finish)")

        if exercise_name.lower() == "done":
            break

        # Look up exercise
        with db.get_connection() as conn:
            result = conn.execute(
                "SELECT id, name FROM exercises WHERE LOWER(name) = LOWER(?)",
                (exercise_name,),
            ).fetchone()

            if not result:
                console.print(
                    f"[yellow]Warning:[/yellow] Exercise '{exercise_name}' not found in database."
                )
                if not Confirm.ask("Try again?", default=True):
                    continue
                continue

            exercise_id = result[0]
            actual_name = result[1]

        # Get exercise parameters
        target_sets = IntPrompt.ask("[bold]Sets[/bold]", default=3)

        reps_input = Prompt.ask("[bold]Reps[/bold] (e.g., 8-10 or just 10)", default="8-10")

        if "-" in reps_input:
            parts = reps_input.split("-")
            target_reps_min = int(parts[0].strip())
            target_reps_max = int(parts[1].strip())
        else:
            target_reps_min = target_reps_max = int(reps_input)

        target_rpe_input = Prompt.ask("[bold]Target RPE[/bold] (6-10, optional)", default="")
        target_rpe: Decimal | None = None
        if target_rpe_input:
            target_rpe = Decimal(target_rpe_input)

        rest_seconds_input = Prompt.ask("[bold]Rest (seconds)[/bold] (optional)", default="")
        rest_seconds: int | None = None
        if rest_seconds_input:
            rest_seconds = int(rest_seconds_input)

        tempo_input = Prompt.ask("[bold]Tempo[/bold] (e.g., 3-0-1-0, optional)", default="")
        tempo: str | None = tempo_input if tempo_input else None

        notes_input = Prompt.ask("[bold]Notes[/bold] (optional)", default="")
        notes: str | None = notes_input if notes_input else None

        # Add exercise
        try:
            service.add_exercise_to_workout(
                workout_id,
                ProgramExerciseCreate(
                    program_workout_id=workout_id,
                    exercise_id=exercise_id,
                    order_number=order_number,
                    target_sets=target_sets,
                    target_reps_min=target_reps_min,
                    target_reps_max=target_reps_max,
                    target_rpe=target_rpe,
                    rest_seconds=rest_seconds,
                    tempo=tempo,
                    notes=notes,
                ),
            )

            console.print(
                f"[green]✓[/green] [bold]{actual_name}[/bold] added ({target_sets} x {target_reps_min}-{target_reps_max})"
            )
            order_number += 1

        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            continue


@program_app.command("list")
def list_programs(ctx: typer.Context) -> None:
    """List all training programs."""
    service = get_program_service(ctx)

    programs = service.get_all_programs()

    if not programs:
        console.print(
            Panel(
                "[yellow]No programs found. Create one with 'lift program create'[/yellow]",
                title="No Programs",
                border_style="yellow",
            )
        )
        return

    table = format_program_list(programs)
    console.print(table)


@program_app.command()
def show(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Program name"),
) -> None:
    """Show detailed information about a program.

    Displays all workouts and exercises in the program.
    """
    service = get_program_service(ctx)
    _display_program(service, name)


def _display_program(service: ProgramService, name: str) -> None:
    """Display a program with all details.

    Args:
        service: Program service
        name: Program name

    """
    program = service.get_program_by_name(name)

    if not program:
        console.print(
            Panel(
                f"[red]Program '{name}' not found[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Get workouts with exercises
    workouts = service.get_program_workouts(program.id)
    workouts_with_exercises = []

    for workout in workouts:
        exercises = service.get_workout_exercises(workout.id)
        workouts_with_exercises.append((workout, exercises))

    # Display
    detail = format_program_detail(program, workouts_with_exercises)
    console.print(detail)


@program_app.command()
def activate(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Program name"),
) -> None:
    """Activate a program.

    Sets the specified program as active and deactivates all others.
    """
    service = get_program_service(ctx)

    program = service.get_program_by_name(name)

    if not program:
        console.print(
            Panel(
                f"[red]Program '{name}' not found[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    try:
        activated = service.activate_program(program.id)

        console.print(
            Panel(
                f"[green]Program '{activated.name}' is now active![/green]",
                title="Success",
                border_style="green",
            )
        )

    except ValueError as e:
        console.print(
            Panel(
                f"[red]{e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@program_app.command()
def delete(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Program name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a program.

    This will also delete all workouts and exercises in the program.
    """
    service = get_program_service(ctx)

    program = service.get_program_by_name(name)

    if not program:
        console.print(
            Panel(
                f"[red]Program '{name}' not found[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Confirm deletion
    if not force:
        console.print(
            f"\n[yellow]Warning:[/yellow] This will delete program [bold]{program.name}[/bold] "
            "and all its workouts and exercises.\n"
        )
        if not Confirm.ask("Are you sure?", default=False):
            console.print("Deletion cancelled.")
            return

    success = service.delete_program(program.id)

    if success:
        console.print(
            Panel(
                f"[green]Program '{program.name}' deleted successfully[/green]",
                title="Success",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[red]Failed to delete program '{program.name}'[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@program_app.command()
def clone(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Program name to clone"),
    new_name: str = typer.Argument(..., help="Name for the cloned program"),
) -> None:
    """Clone an existing program.

    Creates a copy of a program with all its workouts and exercises.
    """
    service = get_program_service(ctx)

    program = service.get_program_by_name(name)

    if not program:
        console.print(
            Panel(
                f"[red]Program '{name}' not found[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    try:
        with console.status(f"[bold green]Cloning program '{name}'..."):
            cloned = service.clone_program(program.id, new_name)

        console.print(
            Panel(
                f"[green]Program '{name}' cloned to '{cloned.name}' successfully![/green]",
                title="Success",
                border_style="green",
            )
        )

    except ValueError as e:
        console.print(
            Panel(
                f"[red]{e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@program_app.command()
def edit(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Program name"),
) -> None:
    """Edit a program.

    Allows adding/removing workouts or exercises from an existing program.
    """
    service = get_program_service(ctx)

    program = service.get_program_by_name(name)

    if not program:
        console.print(
            Panel(
                f"[red]Program '{name}' not found[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Editing Program: {program.name}[/bold cyan]\n")

    # Show current program
    panel = format_program_summary(program)
    console.print(panel)

    console.print("\n[bold]What would you like to do?[/bold]")
    console.print("  1. Add a workout")
    console.print("  2. Add exercises to existing workout")
    console.print("  3. Update program details")
    console.print("  4. Cancel")

    choice = IntPrompt.ask(
        "\nSelect option",
        default=1,
        choices=["1", "2", "3", "4"],
    )

    if choice == 1:
        # Add workout
        workout_name = Prompt.ask("\n[bold]Workout name[/bold]")

        day_number_input = Prompt.ask("[bold]Day number[/bold] (1-7, optional)", default="")
        day_number: int | None = None
        if day_number_input:
            day_number = int(day_number_input)

        workout_description_input = Prompt.ask("[bold]Description[/bold] (optional)", default="")
        workout_description: str | None = (
            workout_description_input if workout_description_input else None
        )

        estimated_duration_input = Prompt.ask(
            "[bold]Estimated duration (minutes)[/bold] (optional)", default=""
        )
        estimated_duration: int | None = None
        if estimated_duration_input:
            estimated_duration = int(estimated_duration_input)

        try:
            workout = service.add_workout_to_program(
                program.id,
                ProgramWorkoutCreate(
                    program_id=program.id,
                    name=workout_name,
                    day_number=day_number,
                    description=workout_description,
                    estimated_duration_minutes=estimated_duration,
                ),
            )

            console.print(f"\n[green]✓[/green] Workout [bold]{workout.name}[/bold] added!\n")

            if Confirm.ask("Add exercises to this workout?", default=True):
                _add_exercises_interactive(ctx, workout.id)

        except ValueError as e:
            console.print(f"\n[red]Error:[/red] {e}\n")
            raise typer.Exit(1)

    elif choice == 2:
        # Add exercises to existing workout
        workouts = service.get_program_workouts(program.id)

        if not workouts:
            console.print("\n[yellow]No workouts found. Add a workout first.[/yellow]\n")
            raise typer.Exit(1)

        console.print("\n[bold]Select workout:[/bold]")
        for i, workout in enumerate(workouts, 1):
            console.print(f"  {i}. {workout.name}")

        workout_choice = IntPrompt.ask(
            "\nSelect workout",
            default=1,
            choices=[str(i) for i in range(1, len(workouts) + 1)],
        )

        selected_workout = workouts[workout_choice - 1]
        _add_exercises_interactive(ctx, selected_workout.id)

    elif choice == 3:
        # Update program details
        console.print("\n[bold]Update program details[/bold]")
        console.print("(Leave blank to keep current value)\n")

        new_name = Prompt.ask(f"[bold]Name[/bold] (current: {program.name})", default="")
        new_description = Prompt.ask(
            f"[bold]Description[/bold] (current: {program.description or 'None'})",
            default="",
        )
        new_days = Prompt.ask(
            f"[bold]Days per week[/bold] (current: {program.days_per_week})", default=""
        )

        updates: dict[str, str | int] = {}
        if new_name:
            updates["name"] = new_name
        if new_description:
            updates["description"] = new_description
        if new_days:
            updates["days_per_week"] = int(new_days)

        if updates:
            try:
                updated = service.update_program(program.id, updates)
                console.print(f"\n[green]✓[/green] Program [bold]{updated.name}[/bold] updated!\n")
            except ValueError as e:
                console.print(f"\n[red]Error:[/red] {e}\n")
                raise typer.Exit(1)
        else:
            console.print("\n[yellow]No changes made.[/yellow]\n")

    else:
        console.print("\nCancelled.\n")
        return

    # Show updated program
    console.print("\n")
    _display_program(service, program.name if choice != 3 or not new_name else new_name)


@program_app.command("import-samples")
def import_samples(
    ctx: typer.Context,
    file: str | None = typer.Option(None, "--file", "-f", help="Path to programs JSON file"),
) -> None:
    """Import sample training programs from JSON file.

    Uses the default programs.json if no file is specified.
    """
    service = get_program_service(ctx)

    try:
        with console.status("[bold green]Loading sample programs..."):
            count = service.load_seed_programs(file)

        console.print(
            Panel(
                f"[green]Successfully loaded {count} sample program(s)![/green]",
                title="Success",
                border_style="green",
            )
        )

    except FileNotFoundError as e:
        console.print(
            Panel(
                f"[red]{e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)
    except ValueError as e:
        console.print(
            Panel(
                f"[red]Invalid JSON format: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)
