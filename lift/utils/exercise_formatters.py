"""Formatting utilities for exercise display using Rich."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lift.core.models import Exercise


def create_exercise_table(
    exercises: list[Exercise],
    title: str = "Exercises",
    show_id: bool = False,
) -> Table:
    """
    Create a Rich table displaying exercises.

    Args:
        exercises: List of Exercise objects
        title: Table title
        show_id: Whether to show exercise ID column

    Returns:
        Rich Table object
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    if show_id:
        table.add_column("ID", style="dim", width=6)

    table.add_column("Name", style="cyan", no_wrap=False, width=30)
    table.add_column("Category", style="green", width=10)
    table.add_column("Primary Muscle", style="yellow", width=15)
    table.add_column("Equipment", style="blue", width=15)
    table.add_column("Type", style="magenta", width=10)

    for exercise in exercises:
        row = []

        if show_id:
            row.append(str(exercise.id))

        row.extend([
            exercise.name,
            exercise.category.value,
            exercise.primary_muscle.value,
            exercise.equipment.value,
            exercise.movement_type.value,
        ])

        table.add_row(*row)

    return table


def format_exercise_detail(exercise: Exercise, console: Console) -> None:
    """
    Display detailed information about an exercise.

    Args:
        exercise: Exercise object
        console: Rich Console object
    """
    # Build content string
    content_lines = [
        f"[bold cyan]Name:[/bold cyan] {exercise.name}",
        f"[bold green]Category:[/bold green] {exercise.category.value}",
        f"[bold yellow]Primary Muscle:[/bold yellow] {exercise.primary_muscle.value}",
    ]

    # Add secondary muscles if present
    if exercise.secondary_muscles:
        secondary_str = ", ".join([muscle.value for muscle in exercise.secondary_muscles])
        content_lines.append(f"[bold]Secondary Muscles:[/bold] {secondary_str}")

    content_lines.extend([
        f"[bold blue]Equipment:[/bold blue] {exercise.equipment.value}",
        f"[bold magenta]Movement Type:[/bold magenta] {exercise.movement_type.value}",
        f"[bold]Custom:[/bold] {'Yes' if exercise.is_custom else 'No'}",
    ])

    # Add instructions if present
    if exercise.instructions:
        content_lines.append("")
        content_lines.append("[bold]Instructions:[/bold]")
        content_lines.append(f"[dim]{exercise.instructions}[/dim]")

    # Add video URL if present
    if exercise.video_url:
        content_lines.append("")
        content_lines.append(f"[bold]Video:[/bold] {exercise.video_url}")

    content = "\n".join(content_lines)

    # Display in panel
    panel = Panel(
        content,
        title=f"Exercise Details (ID: {exercise.id})",
        border_style="blue",
        expand=False,
    )

    console.print(panel)


def format_exercise_summary(exercises: list[Exercise]) -> str:
    """
    Create a summary string for a list of exercises.

    Args:
        exercises: List of Exercise objects

    Returns:
        Summary string
    """
    if not exercises:
        return "No exercises found."

    # Count by category
    category_counts = {}
    for exercise in exercises:
        category = exercise.category.value
        category_counts[category] = category_counts.get(category, 0) + 1

    # Build summary
    summary_parts = [f"Total: {len(exercises)} exercises"]

    if category_counts:
        category_strs = [f"{cat}: {count}" for cat, count in sorted(category_counts.items())]
        summary_parts.append(" | ".join(category_strs))

    return " | ".join(summary_parts)


def format_muscle_group_summary(exercises: list[Exercise]) -> Table:
    """
    Create a table showing exercise counts by muscle group.

    Args:
        exercises: List of Exercise objects

    Returns:
        Rich Table object
    """
    # Count by primary muscle
    muscle_counts = {}
    for exercise in exercises:
        muscle = exercise.primary_muscle.value
        muscle_counts[muscle] = muscle_counts.get(muscle, 0) + 1

    table = Table(
        title="Exercises by Muscle Group",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Muscle Group", style="cyan", width=20)
    table.add_column("Exercise Count", style="yellow", justify="right", width=15)

    for muscle, count in sorted(muscle_counts.items(), key=lambda x: x[1], reverse=True):
        table.add_row(muscle, str(count))

    # Add total row
    table.add_row("[bold]TOTAL[/bold]", f"[bold]{len(exercises)}[/bold]")

    return table


def format_equipment_summary(exercises: list[Exercise]) -> Table:
    """
    Create a table showing exercise counts by equipment type.

    Args:
        exercises: List of Exercise objects

    Returns:
        Rich Table object
    """
    # Count by equipment
    equipment_counts = {}
    for exercise in exercises:
        equipment = exercise.equipment.value
        equipment_counts[equipment] = equipment_counts.get(equipment, 0) + 1

    table = Table(
        title="Exercises by Equipment",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Equipment", style="cyan", width=20)
    table.add_column("Exercise Count", style="yellow", justify="right", width=15)

    for equipment, count in sorted(equipment_counts.items(), key=lambda x: x[1], reverse=True):
        table.add_row(equipment, str(count))

    # Add total row
    table.add_row("[bold]TOTAL[/bold]", f"[bold]{len(exercises)}[/bold]")

    return table
