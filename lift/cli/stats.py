"""Stats CLI commands for analytics and statistics."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lift.core.database import get_db
from lift.core.models import RecordType
from lift.services.pr_service import PRService
from lift.services.stats_service import StatsService
from lift.utils.charts import (
    generate_frequency_chart,
    generate_muscle_distribution_chart,
    generate_progression_chart,
    generate_set_distribution_chart,
    generate_volume_chart,
)

stats_app = typer.Typer(name="stats", help="Analytics and statistics")
console = Console()


def format_volume(volume: Decimal) -> str:
    """Format volume with thousands separator."""
    return f"{volume:,.0f}"


def format_date(date: datetime) -> str:
    """Format date for display."""
    if isinstance(date, str):
        date = datetime.fromisoformat(date)
    return date.strftime("%b %d, %Y")


def format_date_short(date: datetime) -> str:
    """Format date short for display."""
    if isinstance(date, str):
        date = datetime.fromisoformat(date)
    return date.strftime("%m/%d")


@stats_app.command(name="summary")
def summary(
    ctx: typer.Context,
    week: bool = typer.Option(False, "--week", "-w", help="Show this week's summary"),
    month: bool = typer.Option(False, "--month", "-m", help="Show this month's summary"),
    year: bool = typer.Option(False, "--year", "-y", help="Show this year's summary"),
    weeks_back: int = typer.Option(4, "--weeks", help="Weeks to analyze for weekly view"),
) -> None:
    """
    Show training summary and statistics.

    By default shows last 4 weeks. Use --week, --month, or --year for specific periods.
    """
    db = get_db(ctx.obj.get("db_path"))
    stats_service = StatsService(db)

    # Determine date range
    now = datetime.now()
    start_date = None
    period_name = f"Last {weeks_back} Weeks"

    if week:
        start_date = now - timedelta(days=7)
        period_name = "This Week"
    elif month:
        start_date = now - timedelta(days=30)
        period_name = "This Month"
    elif year:
        start_date = now - timedelta(days=365)
        period_name = "This Year"

    # Get summary data
    summary_data = stats_service.get_workout_summary(start_date=start_date)

    # Create summary panel
    summary_text = (
        f"[bold]Workouts:[/bold] {summary_data['total_workouts']}\n"
        f"[bold]Total Volume:[/bold] {format_volume(summary_data['total_volume'])} lbs\n"
        f"[bold]Total Sets:[/bold] {summary_data['total_sets']}\n"
        f"[bold]Avg Duration:[/bold] {summary_data['avg_duration']:.0f} min\n"
        f"[bold]Avg RPE:[/bold] {summary_data['avg_rpe']}\n"
        f"[bold]Exercises Used:[/bold] {summary_data['total_exercises']}"
    )

    console.print(
        Panel(
            summary_text,
            title=f"Training Summary - {period_name}",
            border_style="cyan",
            expand=False,
        )
    )

    # Get muscle volume breakdown
    muscle_volume = stats_service.get_muscle_volume_breakdown(start_date=start_date)

    if muscle_volume:
        console.print("\n[bold cyan]Volume by Muscle Group:[/bold cyan]")

        # Calculate total for percentages
        total_volume = sum(muscle_volume.values())

        # Create table
        table = Table(show_header=True)
        table.add_column("Muscle Group", style="cyan")
        table.add_column("Volume", justify="right")
        table.add_column("% of Total", justify="right")

        for muscle, volume in muscle_volume.items():
            percentage = (volume / total_volume * 100) if total_volume > 0 else 0
            table.add_row(muscle, format_volume(volume), f"{percentage:.1f}%")

        console.print(table)

    # Show weekly breakdown if looking at multiple weeks
    if not (week or month or year):
        console.print("\n[bold cyan]Weekly Breakdown:[/bold cyan]")
        weekly_data = stats_service.get_weekly_summary(weeks_back=weeks_back)

        if weekly_data:
            table = Table(show_header=True)
            table.add_column("Week", style="cyan")
            table.add_column("Workouts", justify="right")
            table.add_column("Volume", justify="right")
            table.add_column("Sets", justify="right")
            table.add_column("Avg RPE", justify="right")

            for week_data in weekly_data:
                table.add_row(
                    format_date_short(week_data["week_start"]),
                    str(week_data["workouts"]),
                    format_volume(week_data["total_volume"]),
                    str(week_data["total_sets"]),
                    str(week_data["avg_rpe"]),
                )

            console.print(table)

    # Show streak
    streak = stats_service.calculate_consistency_streak()
    if streak > 0:
        console.print(f"\n[bold green]Consistency Streak:[/bold green] {streak} days")


@stats_app.command(name="exercise")
def exercise_stats(
    ctx: typer.Context,
    exercise_name: str = typer.Argument(..., help="Exercise name"),
    chart: bool = typer.Option(False, "--chart", "-c", help="Show progression chart"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent workouts to show"),
) -> None:
    """
    Show statistics and progression for a specific exercise.
    """
    db = get_db(ctx.obj.get("db_path"))
    stats_service = StatsService(db)
    pr_service = PRService(db)

    # Find exercise by name
    with db.get_connection() as conn:
        result = conn.execute(
            "SELECT id, name FROM exercises WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{exercise_name}%",),
        ).fetchone()

    if not result:
        console.print(f"[red]Exercise not found:[/red] {exercise_name}")
        raise typer.Exit(1)

    exercise_id = result[0]
    exercise_full_name = result[1]

    # Get progression data
    progression = stats_service.get_exercise_progression(exercise_id, limit=limit)

    if not progression:
        console.print(f"[yellow]No workout data found for {exercise_full_name}[/yellow]")
        raise typer.Exit(0)

    # Get PR summary
    pr_summary = pr_service.get_pr_summary(exercise_id)

    # Display header
    console.print(
        Panel(
            f"[bold]{exercise_full_name}[/bold]",
            title="Exercise Statistics",
            border_style="cyan",
        )
    )

    # Display PRs
    if pr_summary:
        console.print("\n[bold cyan]Personal Records:[/bold cyan]")
        pr_table = Table(show_header=True)
        pr_table.add_column("Type", style="yellow")
        pr_table.add_column("Value", justify="right")
        pr_table.add_column("Weight x Reps", justify="right")
        pr_table.add_column("Date", justify="right")

        for record_type, data in pr_summary.items():
            if data["weight"]:
                weight_reps = f"{data['weight']} x {data['reps']}"
            else:
                weight_reps = "-"

            pr_table.add_row(
                record_type,
                f"{data['value']:.1f}",
                weight_reps,
                format_date_short(data["date"]),
            )

        console.print(pr_table)

    # Display recent progression
    console.print(f"\n[bold cyan]Last {len(progression)} Workouts:[/bold cyan]")
    prog_table = Table(show_header=True)
    prog_table.add_column("Date", style="cyan")
    prog_table.add_column("Weight", justify="right")
    prog_table.add_column("Reps", justify="right")
    prog_table.add_column("RPE", justify="right")
    prog_table.add_column("Volume", justify="right")
    prog_table.add_column("Est 1RM", justify="right")

    for entry in progression:
        prog_table.add_row(
            format_date_short(entry["date"]),
            str(entry["weight"]),
            str(entry["reps"]),
            str(entry["rpe"]) if entry["rpe"] else "-",
            format_volume(entry["volume"]),
            f"{entry['estimated_1rm']:.1f}",
        )

    console.print(prog_table)

    # Show chart if requested
    if chart and len(progression) >= 3:
        console.print("\n[bold cyan]Progression Chart (Estimated 1RM):[/bold cyan]")
        chart_output = generate_progression_chart(
            exercise_full_name, progression, metric="estimated_1rm", height=15
        )
        console.print(chart_output)


@stats_app.command(name="volume")
def volume_stats(
    ctx: typer.Context,
    muscle_group: Optional[str] = typer.Option(None, "--muscle", "-m", help="Filter by muscle group"),
    chart: bool = typer.Option(False, "--chart", "-c", help="Show volume chart"),
    weeks: int = typer.Option(12, "--weeks", "-w", help="Weeks to analyze"),
) -> None:
    """
    Show volume analysis and trends.
    """
    db = get_db(ctx.obj.get("db_path"))
    stats_service = StatsService(db)

    # Get volume trends
    trends = stats_service.get_volume_trends(weeks_back=weeks)

    if not trends:
        console.print("[yellow]No volume data found[/yellow]")
        raise typer.Exit(0)

    console.print(
        Panel(
            f"Volume Analysis - Last {weeks} Weeks",
            border_style="cyan",
        )
    )

    # Display volume table
    table = Table(show_header=True)
    table.add_column("Week", style="cyan")
    table.add_column("Total Volume", justify="right")
    table.add_column("Workouts", justify="right")
    table.add_column("Avg/Workout", justify="right")

    for trend in trends:
        table.add_row(
            format_date_short(trend["week_start"]),
            format_volume(trend["total_volume"]),
            str(trend["workout_count"]),
            format_volume(trend["avg_volume_per_workout"]),
        )

    console.print(table)

    # Show muscle breakdown
    if not muscle_group:
        console.print("\n[bold cyan]Volume by Muscle Group:[/bold cyan]")
        muscle_volume = stats_service.get_muscle_volume_breakdown()

        muscle_table = Table(show_header=True)
        muscle_table.add_column("Muscle", style="cyan")
        muscle_table.add_column("Volume", justify="right")

        for muscle, volume in muscle_volume.items():
            muscle_table.add_row(muscle, format_volume(volume))

        console.print(muscle_table)

    # Show chart
    if chart:
        console.print("\n[bold cyan]Volume Trend Chart:[/bold cyan]")
        chart_output = generate_volume_chart(trends, title="Weekly Volume", height=15)
        console.print(chart_output)


@stats_app.command(name="pr")
def pr_stats(
    ctx: typer.Context,
    exercise: Optional[str] = typer.Option(None, "--exercise", "-e", help="Filter by exercise"),
    recent: bool = typer.Option(False, "--recent", "-r", help="Show recent PRs"),
    days: int = typer.Option(30, "--days", "-d", help="Days for recent PRs"),
) -> None:
    """
    Show personal records.
    """
    db = get_db(ctx.obj.get("db_path"))
    pr_service = PRService(db)

    if recent:
        # Show recent PRs
        recent_prs = pr_service.get_recent_prs(days=days, limit=20)

        if not recent_prs:
            console.print(f"[yellow]No PRs set in last {days} days[/yellow]")
            raise typer.Exit(0)

        console.print(
            Panel(
                f"Recent Personal Records - Last {days} Days",
                border_style="green",
            )
        )

        table = Table(show_header=True)
        table.add_column("Exercise", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Value", justify="right")
        table.add_column("Weight x Reps", justify="right")
        table.add_column("Date", justify="right")

        for pr in recent_prs:
            weight_reps = (
                f"{pr['weight']} x {pr['reps']}" if pr["weight"] else "-"
            )
            table.add_row(
                pr["exercise_name"],
                pr["record_type"],
                f"{pr['value']:.1f}",
                weight_reps,
                format_date_short(pr["date"]),
            )

        console.print(table)

    elif exercise:
        # Show PRs for specific exercise
        with db.get_connection() as conn:
            result = conn.execute(
                "SELECT id, name FROM exercises WHERE LOWER(name) LIKE LOWER(?)",
                (f"%{exercise}%",),
            ).fetchone()

        if not result:
            console.print(f"[red]Exercise not found:[/red] {exercise}")
            raise typer.Exit(1)

        exercise_id = result[0]
        exercise_name = result[1]

        prs = pr_service.get_all_prs(exercise_id=exercise_id)

        if not prs:
            console.print(f"[yellow]No PRs found for {exercise_name}[/yellow]")
            raise typer.Exit(0)

        console.print(
            Panel(
                f"Personal Records - {exercise_name}",
                border_style="green",
            )
        )

        table = Table(show_header=True)
        table.add_column("Type", style="yellow")
        table.add_column("Value", justify="right")
        table.add_column("Weight x Reps", justify="right")
        table.add_column("Date", justify="right")

        for pr in prs:
            weight_reps = f"{pr.weight} x {pr.reps}" if pr.weight else "-"
            table.add_row(
                pr.record_type.value,
                f"{pr.value:.1f}",
                weight_reps,
                format_date_short(pr.date),
            )

        console.print(table)

    else:
        # Show all PRs summary
        console.print(
            Panel(
                "Personal Records Summary",
                border_style="green",
            )
        )

        # Get PR counts by type
        pr_counts = pr_service.db.execute(
            """
            SELECT record_type, COUNT(*) as count
            FROM personal_records
            GROUP BY record_type
            ORDER BY count DESC
            """
        )

        table = Table(show_header=True)
        table.add_column("Record Type", style="yellow")
        table.add_column("Count", justify="right")

        for row in pr_counts:
            table.add_row(row[0], str(row[1]))

        console.print(table)

        console.print(
            "\n[dim]Use --exercise to see PRs for a specific exercise[/dim]"
        )
        console.print("[dim]Use --recent to see recently set PRs[/dim]")


@stats_app.command(name="muscle")
def muscle_stats(
    ctx: typer.Context,
    group: str = typer.Argument(..., help="Muscle group name"),
    weeks: int = typer.Option(4, "--weeks", "-w", help="Weeks to analyze"),
    chart: bool = typer.Option(False, "--chart", "-c", help="Show chart"),
) -> None:
    """
    Show detailed analysis for a specific muscle group.
    """
    db = get_db(ctx.obj.get("db_path"))
    stats_service = StatsService(db)

    # Get muscle volume data
    start_date = datetime.now() - timedelta(weeks=weeks)
    muscle_volume = stats_service.get_muscle_volume_breakdown(start_date=start_date)

    # Find matching muscle group
    matching_muscle = None
    for muscle in muscle_volume:
        if group.lower() in muscle.lower():
            matching_muscle = muscle
            break

    if not matching_muscle:
        console.print(f"[red]Muscle group not found:[/red] {group}")
        console.print("\n[dim]Available muscle groups:[/dim]")
        for muscle in muscle_volume:
            console.print(f"  - {muscle}")
        raise typer.Exit(1)

    # Get detailed stats for this muscle
    query = """
        SELECT
            e.name,
            COUNT(s.id) as set_count,
            SUM(s.weight * s.reps) as total_volume,
            AVG(s.weight) as avg_weight,
            AVG(s.reps) as avg_reps
        FROM sets s
        JOIN exercises e ON s.exercise_id = e.id
        JOIN workouts w ON s.workout_id = w.id
        WHERE e.primary_muscle = ?
            AND w.date >= ?
            AND s.set_type IN ('working', 'dropset', 'failure', 'amrap')
        GROUP BY e.name
        ORDER BY total_volume DESC
    """

    with db.get_connection() as conn:
        results = conn.execute(query, (matching_muscle, start_date)).fetchall()

    if not results:
        console.print(f"[yellow]No data found for {matching_muscle}[/yellow]")
        raise typer.Exit(0)

    console.print(
        Panel(
            f"{matching_muscle} Analysis - Last {weeks} Weeks",
            border_style="cyan",
        )
    )

    # Summary stats
    total_sets = sum(row[1] for row in results)
    total_volume = sum(row[2] for row in results)

    console.print(f"\n[bold]Total Sets:[/bold] {total_sets}")
    console.print(f"[bold]Total Volume:[/bold] {format_volume(Decimal(str(total_volume)))} lbs")

    # Exercise breakdown
    console.print(f"\n[bold cyan]Exercises:[/bold cyan]")
    table = Table(show_header=True)
    table.add_column("Exercise", style="cyan")
    table.add_column("Sets", justify="right")
    table.add_column("Volume", justify="right")
    table.add_column("Avg Weight", justify="right")
    table.add_column("Avg Reps", justify="right")

    for row in results:
        table.add_row(
            row[0],
            str(row[1]),
            format_volume(Decimal(str(row[2]))),
            f"{row[3]:.1f}",
            f"{row[4]:.1f}",
        )

    console.print(table)


@stats_app.command(name="streak")
def streak_stats(ctx: typer.Context) -> None:
    """
    Show training consistency streak.
    """
    db = get_db(ctx.obj.get("db_path"))
    stats_service = StatsService(db)

    streak = stats_service.calculate_consistency_streak()

    if streak == 0:
        console.print(
            Panel(
                "[yellow]No active streak[/yellow]\n\n"
                "Start a new streak by completing a workout!",
                title="Consistency Streak",
                border_style="yellow",
            )
        )
    else:
        # Calculate weeks
        weeks = streak // 7
        days = streak % 7

        streak_text = []
        if weeks > 0:
            streak_text.append(f"[bold green]{weeks}[/bold green] weeks")
        if days > 0:
            streak_text.append(f"[bold green]{days}[/bold green] days")

        console.print(
            Panel(
                f"Current Streak: {' '.join(streak_text)}\n\n"
                f"Total: [bold cyan]{streak}[/bold cyan] days\n\n"
                "Keep it up!",
                title="Consistency Streak",
                border_style="green",
            )
        )

    # Show frequency
    frequency = stats_service.get_training_frequency(weeks_back=12)
    if frequency:
        console.print("\n[bold cyan]Training Frequency (Last 12 Weeks):[/bold cyan]")
        table = Table(show_header=True)
        table.add_column("Week", style="cyan")
        table.add_column("Workouts", justify="right")

        for week_data in frequency[:8]:  # Show last 8 weeks
            table.add_row(
                format_date_short(week_data["week_start"]),
                str(week_data["workout_count"]),
            )

        console.print(table)


@stats_app.command(name="progress")
def progress_stats(
    ctx: typer.Context,
    exercise_name: str = typer.Argument(..., help="Exercise name"),
    weeks: int = typer.Option(12, "--weeks", "-w", help="Weeks to analyze"),
    chart: bool = typer.Option(True, "--chart/--no-chart", "-c", help="Show chart"),
) -> None:
    """
    Show detailed progression for an exercise over time.
    """
    db = get_db(ctx.obj.get("db_path"))
    stats_service = StatsService(db)

    # Find exercise
    with db.get_connection() as conn:
        result = conn.execute(
            "SELECT id, name FROM exercises WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{exercise_name}%",),
        ).fetchone()

    if not result:
        console.print(f"[red]Exercise not found:[/red] {exercise_name}")
        raise typer.Exit(1)

    exercise_id = result[0]
    exercise_full_name = result[1]

    # Get progression data
    progression = stats_service.get_exercise_progression(exercise_id, limit=50)

    if not progression:
        console.print(f"[yellow]No data found for {exercise_full_name}[/yellow]")
        raise typer.Exit(0)

    # Filter by weeks
    cutoff_date = datetime.now() - timedelta(weeks=weeks)
    filtered_progression = [
        p for p in progression
        if (p["date"] if isinstance(p["date"], datetime) else datetime.fromisoformat(str(p["date"]))) >= cutoff_date
    ]

    console.print(
        Panel(
            f"Progression Analysis - {exercise_full_name}",
            border_style="cyan",
        )
    )

    if not filtered_progression:
        console.print(f"[yellow]No data in last {weeks} weeks[/yellow]")
        raise typer.Exit(0)

    # Calculate stats
    weights = [float(p["weight"]) for p in filtered_progression]
    volumes = [float(p["volume"]) for p in filtered_progression]
    estimated_1rms = [float(p["estimated_1rm"]) for p in filtered_progression]

    console.print(f"\n[bold]Data Points:[/bold] {len(filtered_progression)}")
    console.print(f"[bold]Max Weight:[/bold] {max(weights):.1f} lbs")
    console.print(f"[bold]Max Volume:[/bold] {max(volumes):.0f} lbs")
    console.print(f"[bold]Best Est 1RM:[/bold] {max(estimated_1rms):.1f} lbs")

    # Show trend
    if len(estimated_1rms) >= 3:
        recent_avg = sum(estimated_1rms[:3]) / 3
        older_avg = sum(estimated_1rms[-3:]) / 3
        change = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0

        if change > 0:
            console.print(f"\n[green]Trending up: +{change:.1f}%[/green]")
        elif change < 0:
            console.print(f"\n[red]Trending down: {change:.1f}%[/red]")
        else:
            console.print(f"\n[yellow]Stable performance[/yellow]")

    # Show chart
    if chart and len(filtered_progression) >= 3:
        console.print("\n[bold cyan]Progression Chart:[/bold cyan]")
        chart_output = generate_progression_chart(
            exercise_full_name,
            filtered_progression,
            metric="estimated_1rm",
            height=15,
        )
        console.print(chart_output)
