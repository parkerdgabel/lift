"""CLI commands for exercise management."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from lift.core.database import get_db
from lift.core.models import (
    CategoryType,
    EquipmentType,
    ExerciseCreate,
    MovementType,
    MuscleGroup,
)
from lift.services.exercise_service import ExerciseService
from lift.utils.exercise_formatters import (
    create_exercise_table,
    format_equipment_summary,
    format_exercise_detail,
    format_muscle_group_summary,
)


# Create exercise app
exercise_app = typer.Typer(
    name="exercises",
    help="Manage exercises - view, search, add, and delete exercises",
)

console = Console()


@exercise_app.command("list")
def list_exercises(
    ctx: typer.Context,
    category: str | None = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category (Push, Pull, Legs, Core)",
    ),
    muscle: str | None = typer.Option(
        None,
        "--muscle",
        "-m",
        help="Filter by primary muscle",
    ),
    equipment: str | None = typer.Option(
        None,
        "--equipment",
        "-e",
        help="Filter by equipment type",
    ),
    summary: bool = typer.Option(
        False,
        "--summary",
        "-s",
        help="Show summary statistics",
    ),
) -> None:
    """
    List all exercises with optional filters.

    Examples:
        lift exercises list
        lift exercises list --category Push
        lift exercises list --muscle Chest --equipment Barbell
        lift exercises list --summary
    """
    db_path = ctx.obj.get("db_path")
    service = ExerciseService(get_db(db_path))

    try:
        # Get exercises with filters
        exercises = service.get_all(
            category=category,
            muscle=muscle,
            equipment=equipment,
        )

        if not exercises:
            console.print(
                Panel(
                    "[yellow]No exercises found matching your criteria.[/yellow]",
                    title="No Results",
                    border_style="yellow",
                )
            )
            return

        # Show summary statistics if requested
        if summary:
            console.print(format_muscle_group_summary(exercises))
            console.print()
            console.print(format_equipment_summary(exercises))
            return

        # Show exercises table
        table = create_exercise_table(exercises, title="Exercise Library")
        console.print(table)

        # Show count
        console.print(f"\n[dim]Total: {len(exercises)} exercises[/dim]")

    except Exception as e:
        console.print(
            Panel(
                f"[red]Error listing exercises: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@exercise_app.command("search")
def search_exercises(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query (partial name match)"),
) -> None:
    """
    Search exercises by name.

    Examples:
        lift exercises search "bench"
        lift exercises search "curl"
    """
    db_path = ctx.obj.get("db_path")
    service = ExerciseService(get_db(db_path))

    try:
        exercises = service.search(query)

        if not exercises:
            console.print(
                Panel(
                    f"[yellow]No exercises found matching '{query}'[/yellow]",
                    title="No Results",
                    border_style="yellow",
                )
            )
            return

        # Show results
        table = create_exercise_table(
            exercises,
            title=f"Search Results for '{query}'",
        )
        console.print(table)
        console.print(f"\n[dim]Found {len(exercises)} exercise(s)[/dim]")

    except Exception as e:
        console.print(
            Panel(
                f"[red]Error searching exercises: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@exercise_app.command("info")
def show_exercise_info(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Exercise name"),
) -> None:
    """
    Show detailed information about an exercise.

    Examples:
        lift exercises info "Barbell Bench Press"
        lift exercises info "Pull-Ups"
    """
    db_path = ctx.obj.get("db_path")
    service = ExerciseService(get_db(db_path))

    try:
        exercise = service.get_by_name(name)

        if not exercise:
            console.print(
                Panel(
                    f"[yellow]Exercise '{name}' not found.[/yellow]\n"
                    "[dim]Try searching with 'lift exercises search <query>'[/dim]",
                    title="Not Found",
                    border_style="yellow",
                )
            )
            raise typer.Exit(1)

        # Show detailed info
        format_exercise_detail(exercise, console)

    except Exception as e:
        console.print(
            Panel(
                f"[red]Error retrieving exercise info: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@exercise_app.command("add")
def add_exercise(ctx: typer.Context) -> None:
    """
    Add a custom exercise through interactive prompts.

    This will guide you through creating a new custom exercise.
    Built-in exercises cannot be modified through this command.

    Example:
        lift exercises add
    """
    db_path = ctx.obj.get("db_path")
    service = ExerciseService(get_db(db_path))

    console.print(
        Panel(
            "[cyan]Create a Custom Exercise[/cyan]\n"
            "[dim]You'll be prompted for exercise details.[/dim]",
            title="Add Exercise",
            border_style="cyan",
        )
    )

    try:
        # Prompt for exercise details
        name = Prompt.ask("[bold]Exercise name[/bold]")

        # Check if exercise already exists
        existing = service.get_by_name(name)
        if existing:
            console.print(
                Panel(
                    f"[red]Exercise '{name}' already exists![/red]",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

        # Category
        console.print("\n[bold]Category options:[/bold] Push, Pull, Legs, Core")
        category_str = Prompt.ask(
            "[bold]Category[/bold]",
            choices=["Push", "Pull", "Legs", "Core"],
        )
        category = CategoryType(category_str)

        # Primary Muscle
        muscle_options = [m.value for m in MuscleGroup]
        console.print(f"\n[bold]Muscle options:[/bold]\n{', '.join(muscle_options)}")
        primary_muscle_str = Prompt.ask(
            "[bold]Primary muscle[/bold]",
            choices=muscle_options,
        )
        primary_muscle = MuscleGroup(primary_muscle_str)

        # Secondary Muscles (optional)
        console.print("\n[dim]Secondary muscles (comma-separated, or press Enter to skip)[/dim]")
        secondary_muscles_str = Prompt.ask(
            "[bold]Secondary muscles[/bold]",
            default="",
        )

        secondary_muscles = []
        if secondary_muscles_str:
            for muscle_str in secondary_muscles_str.split(","):
                muscle_str = muscle_str.strip()
                try:
                    secondary_muscles.append(MuscleGroup(muscle_str))
                except ValueError:
                    console.print(
                        f"[yellow]Warning: '{muscle_str}' is not a valid muscle group, skipping.[/yellow]"
                    )

        # Equipment
        equipment_options = [e.value for e in EquipmentType]
        console.print(f"\n[bold]Equipment options:[/bold]\n{', '.join(equipment_options)}")
        equipment_str = Prompt.ask(
            "[bold]Equipment[/bold]",
            choices=equipment_options,
        )
        equipment = EquipmentType(equipment_str)

        # Movement Type
        console.print("\n[bold]Movement type options:[/bold] Compound, Isolation")
        movement_type_str = Prompt.ask(
            "[bold]Movement type[/bold]",
            choices=["Compound", "Isolation"],
        )
        movement_type = MovementType(movement_type_str)

        # Instructions (optional)
        console.print("\n[dim]Instructions (or press Enter to skip)[/dim]")
        instructions = Prompt.ask("[bold]Instructions[/bold]", default="")
        instructions = instructions if instructions else None

        # Video URL (optional)
        console.print("\n[dim]Video URL (or press Enter to skip)[/dim]")
        video_url = Prompt.ask("[bold]Video URL[/bold]", default="")
        video_url = video_url if video_url else None

        # Create the exercise
        exercise_data = ExerciseCreate(
            name=name,
            category=category,
            primary_muscle=primary_muscle,
            secondary_muscles=secondary_muscles,
            equipment=equipment,
            movement_type=movement_type,
            is_custom=True,
            instructions=instructions,
            video_url=video_url,
        )

        exercise = service.create(exercise_data)

        console.print(
            Panel(
                f"[green]Successfully created custom exercise![/green]\n\n"
                f"[bold]Name:[/bold] {exercise.name}\n"
                f"[bold]ID:[/bold] {exercise.id}",
                title="Success",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Exercise creation cancelled.[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(
            Panel(
                f"[red]Error creating exercise: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@exercise_app.command("delete")
def delete_exercise(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Exercise name to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """
    Delete a custom exercise.

    Only custom exercises can be deleted. Built-in exercises are protected.

    Examples:
        lift exercises delete "My Custom Exercise"
        lift exercises delete "My Custom Exercise" --force
    """
    db_path = ctx.obj.get("db_path")
    service = ExerciseService(get_db(db_path))

    try:
        # Find the exercise
        exercise = service.get_by_name(name)

        if not exercise:
            console.print(
                Panel(
                    f"[yellow]Exercise '{name}' not found.[/yellow]",
                    title="Not Found",
                    border_style="yellow",
                )
            )
            raise typer.Exit(1)

        # Check if it's a custom exercise
        if not exercise.is_custom:
            console.print(
                Panel(
                    f"[red]Cannot delete built-in exercise '{name}'.[/red]\n"
                    "[dim]Only custom exercises can be deleted.[/dim]",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

        # Confirm deletion
        if not force:
            confirm = Confirm.ask(f"[yellow]Are you sure you want to delete '{name}'?[/yellow]")
            if not confirm:
                console.print("[dim]Deletion cancelled.[/dim]")
                raise typer.Exit(0)

        # Delete the exercise
        service.delete(exercise.id)

        console.print(
            Panel(
                f"[green]Successfully deleted exercise '{name}'[/green]",
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
    except Exception as e:
        console.print(
            Panel(
                f"[red]Error deleting exercise: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@exercise_app.command("stats")
def show_statistics(ctx: typer.Context) -> None:
    """
    Show exercise library statistics.

    Displays breakdowns by muscle group and equipment type.

    Example:
        lift exercises stats
    """
    db_path = ctx.obj.get("db_path")
    service = ExerciseService(get_db(db_path))

    try:
        exercises = service.get_all()

        if not exercises:
            console.print(
                Panel(
                    "[yellow]No exercises in the library.[/yellow]\n"
                    "[dim]Run 'lift init' to load seed data.[/dim]",
                    title="No Data",
                    border_style="yellow",
                )
            )
            raise typer.Exit(1)

        console.print(
            Panel(
                f"[bold cyan]Total Exercises:[/bold cyan] {len(exercises)}",
                title="Exercise Library Statistics",
                border_style="cyan",
            )
        )

        console.print()
        console.print(format_muscle_group_summary(exercises))
        console.print()
        console.print(format_equipment_summary(exercises))

    except Exception as e:
        console.print(
            Panel(
                f"[red]Error retrieving statistics: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)
