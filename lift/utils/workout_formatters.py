"""Formatting utilities for workout display using Rich."""

from datetime import datetime
from decimal import Decimal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lift.core.models import Set, Workout


def format_workout_summary(
    workout: Workout, summary: dict, console: Console | None = None
) -> Panel:
    """
    Format workout summary as a Rich Panel.

    Args:
        workout: Workout object
        summary: Summary dictionary from WorkoutService.get_workout_summary()
        console: Optional Rich console for rendering

    Returns:
        Rich Panel with formatted summary
    """
    if console is None:
        console = Console()

    # Format the summary content
    content = Text()

    # Workout name and date
    workout_name = workout.name or "Workout"
    date_str = workout.date.strftime("%B %d, %Y at %I:%M %p")
    content.append(f"{workout_name}\n", style="bold cyan")
    content.append(f"{date_str}\n\n", style="dim")

    # Duration
    if workout.duration_minutes:
        content.append("Duration: ", style="bold")
        content.append(f"{workout.duration_minutes} minutes\n", style="green")

    # Bodyweight
    if workout.bodyweight:
        content.append("Bodyweight: ", style="bold")
        content.append(f"{workout.bodyweight} {workout.bodyweight_unit.value}\n", style="cyan")

    # Summary stats
    content.append("\nWorkout Statistics:\n", style="bold yellow")
    content.append(f"  Exercises: {summary['exercise_count']}\n")
    content.append(f"  Total Sets: {summary['total_sets']}\n")
    content.append(
        f"  Total Volume: {summary['total_volume']:,.0f} {workout.bodyweight_unit.value}\n"
    )

    if summary["avg_rpe"]:
        content.append(f"  Average RPE: {summary['avg_rpe']:.1f}\n")

    # Rating
    if workout.rating:
        stars = "★" * workout.rating + "☆" * (5 - workout.rating)
        content.append(f"\nRating: {stars}\n", style="yellow")

    # Notes
    if workout.notes:
        content.append("\nNotes:\n", style="bold")
        content.append(f"{workout.notes}\n", style="dim")

    return Panel(
        content,
        title="[bold]Workout Summary[/bold]",
        border_style="green",
        padding=(1, 2),
    )


def format_set_table(sets: list[Set], show_exercise_name: bool = True) -> Table:
    """
    Format sets as a Rich Table.

    Args:
        sets: List of Set objects
        show_exercise_name: Whether to show exercise name column

    Returns:
        Rich Table with formatted sets
    """
    table = Table(show_header=True, header_style="bold magenta")

    # Add columns
    if show_exercise_name:
        table.add_column("Exercise", style="cyan")

    table.add_column("Set", justify="center")
    table.add_column("Weight", justify="right")
    table.add_column("Reps", justify="center")
    table.add_column("Volume", justify="right")
    table.add_column("RPE", justify="center")
    table.add_column("Type", justify="center")

    # Group sets by exercise if needed
    current_exercise = None

    for set_obj in sets:
        row = []

        if show_exercise_name:
            # Only show exercise name on first set for that exercise
            if set_obj.exercise_id != current_exercise:
                # Note: We'd need to fetch exercise name separately
                # For now, show exercise_id
                row.append(f"Exercise {set_obj.exercise_id}")
                current_exercise = set_obj.exercise_id
            else:
                row.append("")

        row.append(str(set_obj.set_number))
        row.append(f"{set_obj.weight} {set_obj.weight_unit.value}")
        row.append(str(set_obj.reps))

        # Calculate volume
        volume = set_obj.weight * set_obj.reps
        row.append(f"{volume:,.0f}")

        # RPE
        if set_obj.rpe:
            row.append(f"{set_obj.rpe:.1f}")
        else:
            row.append("-")

        # Set type
        row.append(set_obj.set_type.value)

        table.add_row(*row)

    return table


def format_exercise_performance(
    exercise_name: str, sets: list[dict], last_workout_date: datetime | None = None
) -> Panel:
    """
    Format exercise performance history as a Rich Panel.

    Args:
        exercise_name: Name of the exercise
        sets: List of set dictionaries with weight, reps, rpe
        last_workout_date: Date of last workout for this exercise

    Returns:
        Rich Panel with formatted performance data
    """
    content = Text()

    # Header
    content.append(f"{exercise_name}\n", style="bold cyan")

    if last_workout_date:
        # Calculate days ago
        days_ago = (datetime.now() - last_workout_date).days
        if days_ago == 0:
            time_str = "earlier today"
        elif days_ago == 1:
            time_str = "yesterday"
        else:
            time_str = f"{days_ago} days ago"

        content.append(f"Last performed: {time_str}\n", style="dim")

    content.append("\n")

    if not sets:
        content.append("No previous performance data", style="yellow")
    else:
        # Show last performance
        for i, set_data in enumerate(sets[:5], 1):  # Show up to 5 sets
            weight = set_data.get("weight", Decimal("0"))
            reps = set_data.get("reps", 0)
            rpe = set_data.get("rpe")
            weight_unit = set_data.get("weight_unit", "lbs")

            content.append(f"Set {i}: ", style="bold")
            content.append(f"{weight} {weight_unit} × {reps} reps", style="green")

            if rpe:
                content.append(f" @ RPE {rpe:.1f}", style="yellow")

            content.append("\n")

    return Panel(
        content,
        title="[bold]Last Performance[/bold]",
        border_style="blue",
        padding=(1, 2),
    )


def format_workout_header(
    workout_name: str, start_time: datetime, bodyweight: Decimal | None = None
) -> Panel:
    """
    Format workout header for interactive session.

    Args:
        workout_name: Name of the workout
        start_time: When the workout started
        bodyweight: Optional bodyweight

    Returns:
        Rich Panel with workout header
    """
    content = Text()

    content.append(f"{workout_name}\n", style="bold cyan")
    content.append(f"Started: {start_time.strftime('%I:%M %p')}", style="dim")

    if bodyweight:
        content.append(f" | Bodyweight: {bodyweight} lbs", style="dim")

    return Panel(
        content,
        border_style="cyan",
        padding=(0, 2),
    )


def format_set_completion(
    weight: Decimal,
    reps: int,
    rpe: Decimal | None = None,
    volume: Decimal | None = None,
    is_pr: bool = False,
) -> Text:
    """
    Format set completion message.

    Args:
        weight: Weight used
        reps: Reps performed
        rpe: Optional RPE
        volume: Optional volume calculation
        is_pr: Whether this is a PR

    Returns:
        Rich Text with formatted message
    """
    text = Text()

    if is_pr:
        text.append("🏆 PR! ", style="bold yellow")
    else:
        text.append("✓ ", style="green")

    text.append(f"{weight} lbs × {reps} reps", style="bold")

    if rpe:
        text.append(f" @ RPE {rpe:.1f}", style="yellow")

    if volume:
        text.append(f"\n  Volume: {volume:,.0f} lbs", style="dim")

    return text


def format_workout_complete(
    duration_minutes: int,
    total_volume: Decimal,
    total_sets: int,
    exercise_count: int,
) -> Panel:
    """
    Format workout completion summary.

    Args:
        duration_minutes: Workout duration
        total_volume: Total volume in lbs
        total_sets: Number of sets completed
        exercise_count: Number of exercises

    Returns:
        Rich Panel with completion summary
    """
    content = Text()

    content.append("WORKOUT COMPLETE!\n\n", style="bold green")

    content.append(f"Duration: {duration_minutes} minutes\n", style="cyan")
    content.append(f"Total volume: {total_volume:,.0f} lbs\n", style="yellow")
    content.append(f"Sets completed: {total_sets}\n", style="magenta")
    content.append(f"Exercises: {exercise_count}\n", style="blue")

    return Panel(
        content,
        title="[bold green]✓ Success[/bold green]",
        border_style="green",
        padding=(1, 2),
    )


def format_workout_list(workouts: list[tuple[Workout, dict]]) -> Table:
    """
    Format list of workouts with summaries.

    Args:
        workouts: List of (Workout, summary_dict) tuples

    Returns:
        Rich Table with workout list
    """
    table = Table(show_header=True, header_style="bold magenta")

    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Date", style="yellow")
    table.add_column("Name")
    table.add_column("Duration", justify="right")
    table.add_column("Exercises", justify="center")
    table.add_column("Sets", justify="center")
    table.add_column("Volume", justify="right")

    for workout, summary in workouts:
        date_str = workout.date.strftime("%b %d, %Y")
        name = workout.name or "Workout"
        duration = f"{workout.duration_minutes} min" if workout.duration_minutes else "-"
        exercises = str(summary.get("exercise_count", 0))
        sets = str(summary.get("total_sets", 0))
        volume = f"{summary.get('total_volume', 0):,.0f}"

        table.add_row(
            str(workout.id),
            date_str,
            name,
            duration,
            exercises,
            sets,
            volume,
        )

    return table


def format_progress_indicator(current: int, total: int, label: str = "") -> Text:
    """
    Format progress indicator.

    Args:
        current: Current count
        total: Total count
        label: Optional label

    Returns:
        Rich Text with progress indicator
    """
    text = Text()

    if label:
        text.append(f"{label}: ", style="bold")

    percentage = (current / total * 100) if total > 0 else 0
    text.append(f"{current}/{total} ", style="cyan")
    text.append(f"({percentage:.0f}%)", style="dim")

    return text
