"""Formatting utilities for displaying programs with Rich."""

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lift.core.models import Program, ProgramWorkout


def format_program_summary(program: Program) -> Panel:
    """
    Format a program as a summary panel.

    Args:
        program: Program to format

    Returns:
        Rich Panel with program summary
    """
    title = f"[bold]{program.name.upper()}[/bold]"
    if program.is_active:
        title += " [green]✓ ACTIVE[/green]"

    content_parts = [
        f"[bold]Split:[/bold] {program.split_type}",
        f"[bold]Days/Week:[/bold] {program.days_per_week}",
    ]

    if program.duration_weeks:
        content_parts.append(f"[bold]Duration:[/bold] {program.duration_weeks} weeks")

    if program.description:
        content_parts.append(f"\n{program.description}")

    content = "\n".join(content_parts)

    border_style = "green" if program.is_active else "blue"

    return Panel(
        content,
        title=title,
        border_style=border_style,
        padding=(1, 2),
    )


def format_program_detail(
    program: Program, workouts: list[tuple[ProgramWorkout, list[dict]]]
) -> Group:
    """
    Format a program with full workout and exercise details.

    Args:
        program: Program to format
        workouts: List of tuples (workout, exercises) where exercises is list of dicts
                  with 'program_exercise' and exercise details

    Returns:
        Rich Group with program details
    """
    components = []

    # Program header
    header_text = f"[bold cyan]{program.name.upper()}[/bold cyan]\n"
    header_text += f"Split: {program.split_type} | {program.days_per_week} days/week"

    if program.duration_weeks:
        header_text += f" | {program.duration_weeks} weeks"

    if program.is_active:
        header_text += " | [green]✓ Active[/green]"

    if program.description:
        header_text += f"\n\n{program.description}"

    components.append(
        Panel(
            header_text,
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # Add each workout
    for workout, exercises in workouts:
        workout_panel = format_workout_template(workout, exercises)
        components.append(Text(""))  # Spacer
        components.append(workout_panel)

    return Group(*components)


def format_workout_template(workout: ProgramWorkout, exercises: list[dict]) -> Panel:
    """
    Format a workout template with exercises.

    Args:
        workout: Workout to format
        exercises: List of dicts with 'program_exercise' and exercise details

    Returns:
        Rich Panel with workout details
    """
    title = f"[bold]{workout.name}[/bold]"
    if workout.day_number:
        title = f"Day {workout.day_number}: {title}"

    # Create exercises table
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        padding=(0, 1),
    )

    table.add_column("Exercise", style="white", no_wrap=False)
    table.add_column("Sets", justify="center", style="yellow")
    table.add_column("Reps", justify="center", style="green")
    table.add_column("RPE", justify="center", style="magenta")
    table.add_column("Rest", justify="center", style="blue")

    for exercise_data in exercises:
        pe = exercise_data["program_exercise"]
        exercise_name = exercise_data["exercise_name"]

        # Format exercise name with superset indicator
        if pe.is_superset and pe.superset_group:
            exercise_name = f"[dim]{pe.superset_group}.[/dim] {exercise_name}"

        # Format rep range
        if pe.target_reps_min == pe.target_reps_max:
            reps = str(pe.target_reps_min)
        else:
            reps = f"{pe.target_reps_min}-{pe.target_reps_max}"

        # Format RPE
        rpe = str(pe.target_rpe) if pe.target_rpe else "-"

        # Format rest
        if pe.rest_seconds:
            if pe.rest_seconds >= 60:
                minutes = pe.rest_seconds // 60
                seconds = pe.rest_seconds % 60
                if seconds:
                    rest = f"{minutes}m {seconds}s"
                else:
                    rest = f"{minutes}m"
            else:
                rest = f"{pe.rest_seconds}s"
        else:
            rest = "-"

        table.add_row(
            exercise_name,
            str(pe.target_sets),
            reps,
            rpe,
            rest,
        )

    # Build description
    description_parts = []
    if workout.description:
        description_parts.append(workout.description)
    if workout.estimated_duration_minutes:
        description_parts.append(f"Est. {workout.estimated_duration_minutes} min")

    description = " | ".join(description_parts) if description_parts else None

    # Combine description and table
    if description:
        content = Group(Text(description, style="dim"), Text(""), table)
    else:
        content = table

    return Panel(
        content,
        title=title,
        border_style="blue",
        padding=(1, 2),
    )


def format_program_list(programs: list[Program]) -> Table:
    """
    Format a list of programs as a table.

    Args:
        programs: List of programs to format

    Returns:
        Rich Table with program list
    """
    table = Table(
        title="[bold]Training Programs[/bold]",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
    )

    table.add_column("Name", style="white")
    table.add_column("Split", style="yellow")
    table.add_column("Days/Week", justify="center", style="green")
    table.add_column("Duration", justify="center", style="magenta")
    table.add_column("Status", justify="center")

    for program in programs:
        status = "[green]✓ Active[/green]" if program.is_active else ""
        duration = f"{program.duration_weeks}w" if program.duration_weeks else "-"

        table.add_row(
            program.name,
            program.split_type,
            str(program.days_per_week),
            duration,
            status,
        )

    return table


def format_workout_summary(workout: ProgramWorkout, exercise_count: int) -> str:
    """
    Format a workout as a one-line summary.

    Args:
        workout: Workout to format
        exercise_count: Number of exercises in workout

    Returns:
        Formatted string
    """
    parts = [workout.name]

    if workout.day_number:
        parts.insert(0, f"Day {workout.day_number}:")

    parts.append(f"({exercise_count} exercises)")

    if workout.estimated_duration_minutes:
        parts.append(f"~{workout.estimated_duration_minutes}min")

    return " ".join(parts)
