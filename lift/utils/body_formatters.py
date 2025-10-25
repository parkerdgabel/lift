"""Rich formatters for body measurement display."""

from decimal import Decimal

import plotext as plt
from rich.panel import Panel
from rich.table import Table

from lift.core.models import BodyMeasurement


def format_measurement_table(measurements: list[BodyMeasurement]) -> Table:
    """
    Format a list of measurements as a Rich table.

    Args:
        measurements: List of body measurements

    Returns:
        Rich Table with measurement data

    Example:
        >>> table = format_measurement_table(measurements)
        >>> console.print(table)
    """
    table = Table(title="Body Measurement History", show_header=True, header_style="bold cyan")

    table.add_column("Date", style="dim")
    table.add_column("Weight", justify="right")
    table.add_column("Body Fat %", justify="right")
    table.add_column("Chest", justify="right")
    table.add_column("Waist", justify="right")
    table.add_column("Bicep (L)", justify="right")
    table.add_column("Thigh (L)", justify="right")

    for m in measurements:
        date_str = m.date.strftime("%b %d, %Y")
        weight_str = f"{m.weight} {m.weight_unit.value}" if m.weight else "-"
        bf_str = f"{m.body_fat_pct}%" if m.body_fat_pct else "-"
        chest_str = f"{m.chest} {m.measurement_unit.value}" if m.chest else "-"
        waist_str = f"{m.waist} {m.measurement_unit.value}" if m.waist else "-"
        bicep_str = f"{m.bicep_left} {m.measurement_unit.value}" if m.bicep_left else "-"
        thigh_str = f"{m.thigh_left} {m.measurement_unit.value}" if m.thigh_left else "-"

        table.add_row(
            date_str,
            weight_str,
            bf_str,
            chest_str,
            waist_str,
            bicep_str,
            thigh_str,
        )

    return table


def format_measurement_detail(measurement: BodyMeasurement) -> Panel:
    """
    Format a single measurement as a detailed Rich panel.

    Args:
        measurement: Body measurement to display

    Returns:
        Rich Panel with detailed measurement data

    Example:
        >>> panel = format_measurement_detail(measurement)
        >>> console.print(panel)
    """
    lines = []

    # Date and basic info
    date_str = measurement.date.strftime("%B %d, %Y at %I:%M %p")
    lines.append(f"[bold]Date:[/bold] {date_str}\n")

    # Weight and body composition
    if measurement.weight:
        lines.append(
            f"[bold cyan]Weight:[/bold cyan] {measurement.weight} {measurement.weight_unit.value}"
        )
    if measurement.body_fat_pct:
        lines.append(f"[bold cyan]Body Fat:[/bold cyan] {measurement.body_fat_pct}%")

    if measurement.weight or measurement.body_fat_pct:
        lines.append("")

    # Upper body measurements
    upper_body = []
    if measurement.neck:
        upper_body.append(f"  Neck: {measurement.neck} {measurement.measurement_unit.value}")
    if measurement.shoulders:
        upper_body.append(
            f"  Shoulders: {measurement.shoulders} {measurement.measurement_unit.value}"
        )
    if measurement.chest:
        upper_body.append(f"  Chest: {measurement.chest} {measurement.measurement_unit.value}")
    if measurement.waist:
        upper_body.append(f"  Waist: {measurement.waist} {measurement.measurement_unit.value}")
    if measurement.hips:
        upper_body.append(f"  Hips: {measurement.hips} {measurement.measurement_unit.value}")

    if upper_body:
        lines.append("[bold]Torso Measurements:[/bold]")
        lines.extend(upper_body)
        lines.append("")

    # Arms
    arms = []
    if measurement.bicep_left:
        arms.append(f"  Bicep (L): {measurement.bicep_left} {measurement.measurement_unit.value}")
    if measurement.bicep_right:
        arms.append(f"  Bicep (R): {measurement.bicep_right} {measurement.measurement_unit.value}")
    if measurement.forearm_left:
        arms.append(
            f"  Forearm (L): {measurement.forearm_left} {measurement.measurement_unit.value}"
        )
    if measurement.forearm_right:
        arms.append(
            f"  Forearm (R): {measurement.forearm_right} {measurement.measurement_unit.value}"
        )

    if arms:
        lines.append("[bold]Arm Measurements:[/bold]")
        lines.extend(arms)
        lines.append("")

    # Legs
    legs = []
    if measurement.thigh_left:
        legs.append(f"  Thigh (L): {measurement.thigh_left} {measurement.measurement_unit.value}")
    if measurement.thigh_right:
        legs.append(f"  Thigh (R): {measurement.thigh_right} {measurement.measurement_unit.value}")
    if measurement.calf_left:
        legs.append(f"  Calf (L): {measurement.calf_left} {measurement.measurement_unit.value}")
    if measurement.calf_right:
        legs.append(f"  Calf (R): {measurement.calf_right} {measurement.measurement_unit.value}")

    if legs:
        lines.append("[bold]Leg Measurements:[/bold]")
        lines.extend(legs)
        lines.append("")

    # Notes
    if measurement.notes:
        lines.append(f"[bold]Notes:[/bold]\n{measurement.notes}")

    content = "\n".join(lines)
    return Panel(content, title="Body Measurement Details", border_style="cyan")


def format_progress_comparison(current: dict, previous: dict, differences: dict) -> Table:
    """
    Format progress comparison as a Rich table.

    Args:
        current: Current measurement data
        previous: Previous measurement data
        differences: Dictionary of differences between measurements

    Returns:
        Rich Table showing progress comparison

    Example:
        >>> table = format_progress_comparison(current, previous, differences)
        >>> console.print(table)
    """
    table = Table(
        title="Progress Comparison",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Measurement", style="bold")
    table.add_column("Current", justify="right")
    table.add_column("Previous", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("% Change", justify="right")

    # Helper to format change with color
    def format_change(value: Decimal, is_weight: bool = False) -> str:
        """Format change value with appropriate color."""
        if value > 0:
            color = "green" if not is_weight else "yellow"
            return f"[{color}]+{value:.2f}[/{color}]"
        if value < 0:
            color = "red" if not is_weight else "green"
            return f"[{color}]{value:.2f}[/{color}]"
        return "[dim]0.00[/dim]"

    def format_percent(value: Decimal) -> str:
        """Format percent change with color."""
        if value > 0:
            return f"[yellow]+{value:.1f}%[/yellow]"
        if value < 0:
            return f"[green]{value:.1f}%[/green]"
        return "[dim]0.0%[/dim]"

    # Display order for measurements
    measurement_labels = {
        "weight": "Weight",
        "body_fat_pct": "Body Fat %",
        "chest": "Chest",
        "waist": "Waist",
        "bicep_left": "Bicep (L)",
        "bicep_right": "Bicep (R)",
        "thigh_left": "Thigh (L)",
        "thigh_right": "Thigh (R)",
        "neck": "Neck",
        "shoulders": "Shoulders",
        "hips": "Hips",
        "forearm_left": "Forearm (L)",
        "forearm_right": "Forearm (R)",
        "calf_left": "Calf (L)",
        "calf_right": "Calf (R)",
    }

    for field, label in measurement_labels.items():
        if field in differences:
            diff = differences[field]
            current_val = f"{diff['current']:.2f}"
            previous_val = f"{diff['previous']:.2f}"
            change_val = format_change(diff["change"], is_weight=(field == "weight"))
            percent_val = format_percent(diff["percent"])

            table.add_row(label, current_val, previous_val, change_val, percent_val)

    return table


def format_measurement_chart(measurement_name: str, data: list[dict]) -> str:
    """
    Create a terminal chart for measurement trend using plotext.

    Args:
        measurement_name: Name of the measurement being charted
        data: List of dicts with 'date', 'value', and 'unit' keys

    Returns:
        String representation of the chart

    Example:
        >>> chart = format_measurement_chart("Weight", weight_data)
        >>> print(chart)
    """
    if not data:
        return "No data available for chart"

    plt.clear_figure()
    plt.clf()

    # Extract dates and values
    dates = [d["date"] for d in data]
    values = [float(d["value"]) for d in data]
    unit = data[0]["unit"] if data else ""

    # Format dates for x-axis
    date_labels = [d.strftime("%m/%d") for d in dates]

    # Plot the data
    plt.plot(values, marker="braille")
    plt.title(f"{measurement_name} Trend")
    plt.xlabel("Date")
    plt.ylabel(f"{measurement_name} ({unit})")

    # Set x-axis labels at reasonable intervals
    if len(date_labels) > 10:
        step = len(date_labels) // 10
        xticks_positions = list(range(0, len(date_labels), step))
        xticks_labels = [date_labels[i] for i in xticks_positions]
        plt.xticks(xticks_positions, xticks_labels)
    else:
        plt.xticks(range(len(date_labels)), date_labels)

    # Calculate statistics
    current = values[-1] if values else 0
    avg = sum(values) / len(values) if values else 0
    trend = values[-1] - values[0] if len(values) > 1 else 0

    # Build the chart
    chart_output = plt.build()

    # Add statistics below the chart
    stats = f"\n[bold cyan]Current:[/bold cyan] {current:.1f} {unit}  "
    stats += f"[bold]Average:[/bold] {avg:.1f} {unit}  "
    if trend > 0:
        stats += f"[bold green]Trend:[/bold green] +{trend:.1f} {unit}"
    elif trend < 0:
        stats += f"[bold red]Trend:[/bold red] {trend:.1f} {unit}"
    else:
        stats += f"[bold]Trend:[/bold] {trend:.1f} {unit}"

    return chart_output + "\n" + stats


def format_weight_log_response(
    weight: Decimal,
    unit: str,
    previous_weight: tuple[Decimal, str] | None = None,
    seven_day_avg: Decimal | None = None,
) -> Panel:
    """
    Format response for quick weight logging.

    Args:
        weight: Current weight value
        unit: Weight unit
        previous_weight: Previous weight as (value, unit) tuple
        seven_day_avg: 7-day moving average

    Returns:
        Rich Panel with weight log confirmation

    Example:
        >>> panel = format_weight_log_response(Decimal("185.2"), "lbs")
        >>> console.print(panel)
    """
    lines = [f"[bold green]Weight logged:[/bold green] {weight} {unit}"]

    if previous_weight:
        prev_val, prev_unit = previous_weight
        change = weight - prev_val
        if change > 0:
            lines.append(
                f"  Previous: {prev_val} {prev_unit} ([yellow]+{change:.1f} {unit}[/yellow])"
            )
        elif change < 0:
            lines.append(f"  Previous: {prev_val} {prev_unit} ([green]{change:.1f} {unit}[/green])")
        else:
            lines.append(f"  Previous: {prev_val} {prev_unit} (no change)")

    if seven_day_avg:
        lines.append(f"  7-day avg: {seven_day_avg} {unit}")

    content = "\n".join(lines)
    return Panel(content, border_style="green")


def format_progress_summary(weeks_apart: float, differences: dict) -> str:
    """
    Generate a text summary of progress.

    Args:
        weeks_apart: Number of weeks between measurements
        differences: Dictionary of measurement differences

    Returns:
        Human-readable progress summary

    Example:
        >>> summary = format_progress_summary(4.0, differences)
        "Gaining lean mass! Weight up, body fat down."
    """
    summaries = []

    # Check weight trend
    if "weight" in differences:
        weight_change = differences["weight"]["change"]
        if weight_change > 0:
            summaries.append("weight up")
        elif weight_change < 0:
            summaries.append("weight down")

    # Check body fat trend
    if "body_fat_pct" in differences:
        bf_change = differences["body_fat_pct"]["change"]
        if bf_change < 0:
            summaries.append("body fat down")
        elif bf_change > 0:
            summaries.append("body fat up")

    # Interpret the combination
    if "weight up" in summaries and "body fat down" in summaries:
        return "Gaining lean mass! Weight up, body fat down."
    if "weight down" in summaries and "body fat up" in summaries:
        return "Losing muscle mass. Weight down, body fat up."
    if "weight up" in summaries and "body fat up" in summaries:
        return "Gaining weight with some fat. Consider adjusting diet."
    if "weight down" in summaries and "body fat down" in summaries:
        return "Cutting successfully! Losing fat while preserving muscle."
    if "weight up" in summaries:
        return "Weight gaining phase."
    if "weight down" in summaries:
        return "Weight loss phase."
    if "body fat down" in summaries:
        return "Body recomposition! Losing fat."
    if "body fat up" in summaries:
        return "Body fat increasing."

    return f"Progress over {weeks_apart:.1f} weeks."
