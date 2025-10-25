"""CLI commands for body measurement tracking."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from lift.core.database import get_db
from lift.core.models import BodyMeasurementCreate, MeasurementUnit, WeightUnit
from lift.services.body_service import BodyService
from lift.utils.body_formatters import (
    format_measurement_chart,
    format_measurement_detail,
    format_measurement_table,
    format_progress_comparison,
    format_progress_summary,
    format_weight_log_response,
)

# Create body tracking app
body_app = typer.Typer(
    name="body",
    help="Track body measurements and progress",
    no_args_is_help=True,
)

console = Console()


def _get_body_service(ctx: typer.Context) -> BodyService:
    """Get body service instance with database connection."""
    db_path = ctx.obj.get("db_path") if ctx.obj else None
    db = get_db(db_path)
    return BodyService(db)


@body_app.command()
def weight(
    ctx: typer.Context,
    value: float = typer.Argument(..., help="Body weight value"),
    unit: str = typer.Option("lbs", "--unit", "-u", help="Weight unit (lbs or kg)"),
) -> None:
    """
    Quick log bodyweight.

    Example:
        lift body weight 185.2
        lift body weight 84.0 --unit kg
    """
    try:
        weight_val = Decimal(str(value))
        weight_unit = WeightUnit.LBS if unit.lower() == "lbs" else WeightUnit.KG

        service = _get_body_service(ctx)

        # Get previous weight for comparison
        previous = service.get_latest_weight()

        # Get 7-day average
        seven_day_avg = service.get_seven_day_average("weight")

        # Log the weight
        measurement = service.log_weight(weight_val, weight_unit)

        # Display confirmation
        panel = format_weight_log_response(
            weight_val, weight_unit.value, previous, seven_day_avg
        )
        console.print(panel)

    except InvalidOperation:
        console.print("[red]Error: Invalid weight value[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error logging weight: {e}[/red]")
        raise typer.Exit(1)


@body_app.command()
def measure(
    ctx: typer.Context,
) -> None:
    """
    Interactive comprehensive body measurement entry.

    Prompts for weight, body fat percentage, and all circumference measurements.
    Press Enter to skip any optional measurement.

    Example:
        lift body measure
    """
    console.print(
        Panel(
            "[bold cyan]Body Measurement Entry[/bold cyan]\n"
            f"Date: {datetime.now().strftime('%b %d, %Y')}\n\n"
            "[dim]Press Enter to skip any measurement[/dim]",
            border_style="cyan",
        )
    )

    try:
        service = _get_body_service(ctx)

        # Weight (required)
        weight_str = Prompt.ask("\n[bold]Weight[/bold]", default="")
        weight_val = Decimal(weight_str) if weight_str else None

        weight_unit = WeightUnit.LBS
        if weight_val:
            unit_choice = Prompt.ask(
                "Unit",
                choices=["lbs", "kg"],
                default="lbs",
            )
            weight_unit = WeightUnit.LBS if unit_choice == "lbs" else WeightUnit.KG

        # Body fat percentage
        bf_str = Prompt.ask("[bold]Body fat %[/bold]", default="")
        body_fat = Decimal(bf_str) if bf_str else None

        # Ask about measurement unit
        console.print("\n[bold cyan]Circumference Measurements[/bold cyan]")
        meas_unit_choice = Prompt.ask(
            "Measurement unit",
            choices=["in", "cm"],
            default="in",
        )
        measurement_unit = (
            MeasurementUnit.INCHES if meas_unit_choice == "in" else MeasurementUnit.CENTIMETERS
        )

        # Torso measurements
        console.print("\n[dim]Torso (press Enter to skip):[/dim]")
        neck_str = Prompt.ask("  Neck", default="")
        shoulders_str = Prompt.ask("  Shoulders", default="")
        chest_str = Prompt.ask("  Chest", default="")
        waist_str = Prompt.ask("  Waist", default="")
        hips_str = Prompt.ask("  Hips", default="")

        # Arm measurements
        console.print("\n[dim]Arms (press Enter to skip):[/dim]")
        bicep_left_str = Prompt.ask("  Bicep (L)", default="")
        bicep_right_str = Prompt.ask("  Bicep (R)", default="")
        forearm_left_str = Prompt.ask("  Forearm (L)", default="")
        forearm_right_str = Prompt.ask("  Forearm (R)", default="")

        # Leg measurements
        console.print("\n[dim]Legs (press Enter to skip):[/dim]")
        thigh_left_str = Prompt.ask("  Thigh (L)", default="")
        thigh_right_str = Prompt.ask("  Thigh (R)", default="")
        calf_left_str = Prompt.ask("  Calf (L)", default="")
        calf_right_str = Prompt.ask("  Calf (R)", default="")

        # Notes
        console.print()
        notes = Prompt.ask("[bold]Notes[/bold] (optional)", default="")

        # Create measurement
        measurement_create = BodyMeasurementCreate(
            date=datetime.now(),
            weight=weight_val,
            weight_unit=weight_unit,
            body_fat_pct=body_fat,
            neck=Decimal(neck_str) if neck_str else None,
            shoulders=Decimal(shoulders_str) if shoulders_str else None,
            chest=Decimal(chest_str) if chest_str else None,
            waist=Decimal(waist_str) if waist_str else None,
            hips=Decimal(hips_str) if hips_str else None,
            bicep_left=Decimal(bicep_left_str) if bicep_left_str else None,
            bicep_right=Decimal(bicep_right_str) if bicep_right_str else None,
            forearm_left=Decimal(forearm_left_str) if forearm_left_str else None,
            forearm_right=Decimal(forearm_right_str) if forearm_right_str else None,
            thigh_left=Decimal(thigh_left_str) if thigh_left_str else None,
            thigh_right=Decimal(thigh_right_str) if thigh_right_str else None,
            calf_left=Decimal(calf_left_str) if calf_left_str else None,
            calf_right=Decimal(calf_right_str) if calf_right_str else None,
            measurement_unit=measurement_unit,
            notes=notes if notes else None,
        )

        # Save measurement
        measurement = service.log_measurement(measurement_create)

        console.print(
            "\n" + Panel(
                "[bold green]Measurement saved successfully![/bold green]",
                border_style="green",
            )
        )

        # Show what was saved
        panel = format_measurement_detail(measurement)
        console.print(panel)

    except InvalidOperation as e:
        console.print(f"[red]Error: Invalid number format - {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error saving measurement: {e}[/red]")
        raise typer.Exit(1)


@body_app.command()
def history(
    ctx: typer.Context,
    measurement: Optional[str] = typer.Option(
        None,
        "--measurement",
        "-m",
        help="Specific measurement to show (e.g., weight, chest, waist)",
    ),
    weeks: int = typer.Option(12, "--weeks", "-w", help="Number of weeks to show"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of entries"),
) -> None:
    """
    Show body measurement history.

    Without --measurement flag, shows overview of all measurements.
    With --measurement flag, shows detailed history of that specific measurement.

    Example:
        lift body history
        lift body history --measurement weight --weeks 8
        lift body history --limit 10
    """
    try:
        service = _get_body_service(ctx)

        if measurement:
            # Show specific measurement trend
            trend_data = service.get_measurement_trend(measurement, weeks_back=weeks)

            if not trend_data:
                console.print(
                    f"[yellow]No {measurement} measurements found in the last {weeks} weeks[/yellow]"
                )
                return

            # Display as chart
            chart = format_measurement_chart(measurement.title(), trend_data)
            console.print(
                Panel(
                    chart,
                    title=f"{measurement.title()} History ({weeks} weeks)",
                    border_style="cyan",
                )
            )

        else:
            # Show overview table
            measurements = service.get_measurement_history(limit=limit)

            if not measurements:
                console.print("[yellow]No measurements found[/yellow]")
                return

            table = format_measurement_table(measurements)
            console.print(table)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error retrieving history: {e}[/red]")
        raise typer.Exit(1)


@body_app.command()
def progress(
    ctx: typer.Context,
    weeks: int = typer.Option(4, "--weeks", "-w", help="Number of weeks to compare"),
) -> None:
    """
    Show progress report comparing current vs X weeks ago.

    Displays changes in weight, body fat, and all measurements with
    absolute and percentage changes.

    Example:
        lift body progress
        lift body progress --weeks 8
    """
    try:
        service = _get_body_service(ctx)

        # Get progress report
        report = service.get_progress_report(weeks_back=weeks)

        current = report["current"]
        previous = report["previous"]
        weeks_apart = report["weeks_apart"]
        differences = report["differences"]

        # Display header
        console.print(
            Panel(
                f"[bold cyan]{weeks_apart:.1f}-WEEK PROGRESS REPORT[/bold cyan]\n\n"
                f"Comparison: {current.date.strftime('%b %d')} vs {previous.date.strftime('%b %d')}",
                border_style="cyan",
            )
        )

        # Display comparison table
        table = format_progress_comparison(
            {"date": current.date},
            {"date": previous.date},
            differences,
        )
        console.print(table)

        # Display summary
        summary = format_progress_summary(weeks_apart, differences)
        console.print(f"\n[bold]{summary}[/bold]\n")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error generating progress report: {e}[/red]")
        raise typer.Exit(1)


@body_app.command()
def chart(
    ctx: typer.Context,
    measurement: str = typer.Argument(..., help="Measurement to chart (e.g., weight, chest, waist)"),
    weeks: int = typer.Option(12, "--weeks", "-w", help="Number of weeks to chart"),
) -> None:
    """
    Display a terminal chart for a specific measurement trend.

    Shows a line chart with current value, average, and trend direction.

    Example:
        lift body chart weight
        lift body chart chest --weeks 8
        lift body chart waist --weeks 16
    """
    try:
        service = _get_body_service(ctx)

        # Get trend data
        trend_data = service.get_measurement_trend(measurement, weeks_back=weeks)

        if not trend_data:
            console.print(
                f"[yellow]No {measurement} measurements found in the last {weeks} weeks[/yellow]"
            )
            return

        # Generate and display chart
        console.print(
            Panel(
                "",
                title=f"{measurement.upper()} TREND ({weeks} Weeks)",
                border_style="cyan",
            )
        )

        chart = format_measurement_chart(measurement.title(), trend_data)
        console.print(chart)
        console.print()

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error generating chart: {e}[/red]")
        raise typer.Exit(1)


@body_app.command()
def latest(
    ctx: typer.Context,
) -> None:
    """
    Show the most recent body measurement.

    Displays all recorded values from the latest measurement entry.

    Example:
        lift body latest
    """
    try:
        service = _get_body_service(ctx)

        measurement = service.get_latest_measurement()

        if not measurement:
            console.print("[yellow]No measurements found. Log one with 'lift body measure'[/yellow]")
            return

        panel = format_measurement_detail(measurement)
        console.print(panel)

    except Exception as e:
        console.print(f"[red]Error retrieving latest measurement: {e}[/red]")
        raise typer.Exit(1)
