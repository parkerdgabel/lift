"""Terminal-based chart generation using plotext."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

import plotext as plt


def generate_volume_chart(
    data: list[dict], title: str = "Volume Over Time", width: int = 80, height: int = 20
) -> str:
    """
    Generate a line chart showing volume over time.

    Args:
        data: List of dicts with 'week_start' or 'date' and 'total_volume'
        title: Chart title
        width: Chart width
        height: Chart height

    Returns:
        Chart as string
    """
    if not data:
        return "No data available for chart"

    # Extract dates and volumes
    dates = []
    volumes = []

    for entry in data:
        date = entry.get("week_start") or entry.get("date") or entry.get("month_start")
        if date:
            if isinstance(date, datetime):
                dates.append(date.strftime("%m/%d"))
            else:
                dates.append(str(date)[:10])
        volume = entry.get("total_volume", 0)
        volumes.append(float(volume) if isinstance(volume, Decimal) else volume)

    # Reverse to show chronologically
    dates.reverse()
    volumes.reverse()

    # Clear any previous plot
    plt.clf()

    # Create line chart
    plt.plot(dates, volumes, marker="braille")
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Volume (lbs)")
    plt.plotsize(width, height)

    # Build the chart
    return plt.build()


def generate_progression_chart(
    exercise_name: str,
    data: list[dict],
    metric: str = "estimated_1rm",
    width: int = 80,
    height: int = 20,
) -> str:
    """
    Generate progression chart for an exercise.

    Args:
        exercise_name: Name of the exercise
        data: List of progression data points
        metric: Metric to plot ('estimated_1rm', 'weight', 'volume')
        width: Chart width
        height: Chart height

    Returns:
        Chart as string
    """
    if not data:
        return "No data available for chart"

    dates = []
    values = []

    for entry in data:
        date = entry.get("date")
        if date:
            if isinstance(date, datetime):
                dates.append(date.strftime("%m/%d"))
            else:
                dates.append(str(date)[:10])

        value = entry.get(metric, 0)
        values.append(float(value) if isinstance(value, Decimal) else value)

    # Reverse to show chronologically
    dates.reverse()
    values.reverse()

    plt.clf()
    plt.plot(dates, values, marker="braille")
    plt.title(f"{exercise_name} - {metric.replace('_', ' ').title()}")
    plt.xlabel("Date")
    plt.ylabel(metric.replace("_", " ").title())
    plt.plotsize(width, height)

    return plt.build()


def generate_muscle_distribution_chart(
    data: dict[str, Decimal], title: str = "Volume by Muscle Group", width: int = 80, height: int = 20
) -> str:
    """
    Generate bar chart showing volume distribution by muscle group.

    Args:
        data: Dictionary mapping muscle group to volume
        title: Chart title
        width: Chart width
        height: Chart height

    Returns:
        Chart as string
    """
    if not data:
        return "No data available for chart"

    # Sort by volume descending
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

    muscles = [item[0] for item in sorted_data]
    volumes = [float(item[1]) if isinstance(item[1], Decimal) else item[1] for item in sorted_data]

    plt.clf()
    plt.bar(muscles, volumes)
    plt.title(title)
    plt.xlabel("Muscle Group")
    plt.ylabel("Volume (lbs)")
    plt.plotsize(width, height)

    return plt.build()


def generate_frequency_chart(
    data: list[dict], title: str = "Training Frequency", width: int = 80, height: int = 20
) -> str:
    """
    Generate bar chart showing training frequency over time.

    Args:
        data: List of dicts with 'week_start' and 'workout_count'
        title: Chart title
        width: Chart width
        height: Chart height

    Returns:
        Chart as string
    """
    if not data:
        return "No data available for chart"

    weeks = []
    counts = []

    for entry in data:
        week = entry.get("week_start")
        if week:
            if isinstance(week, datetime):
                weeks.append(week.strftime("%m/%d"))
            else:
                weeks.append(str(week)[:10])

        count = entry.get("workout_count", 0)
        counts.append(count)

    # Reverse to show chronologically
    weeks.reverse()
    counts.reverse()

    plt.clf()
    plt.bar(weeks, counts)
    plt.title(title)
    plt.xlabel("Week")
    plt.ylabel("Workouts")
    plt.plotsize(width, height)

    return plt.build()


def generate_set_distribution_chart(
    data: dict[str, int], title: str = "Sets by Muscle Group", width: int = 80, height: int = 20
) -> str:
    """
    Generate horizontal bar chart showing set distribution.

    Args:
        data: Dictionary mapping muscle group to set count
        title: Chart title
        width: Chart width
        height: Chart height

    Returns:
        Chart as string
    """
    if not data:
        return "No data available for chart"

    # Sort by set count descending
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

    muscles = [item[0] for item in sorted_data]
    sets = [item[1] for item in sorted_data]

    plt.clf()
    plt.bar(muscles, sets)
    plt.title(title)
    plt.xlabel("Muscle Group")
    plt.ylabel("Sets")
    plt.plotsize(width, height)

    return plt.build()


def generate_pr_timeline(
    data: list[dict], title: str = "Personal Records Timeline", width: int = 80, height: int = 20
) -> str:
    """
    Generate timeline chart of personal records.

    Args:
        data: List of PR data with dates and values
        title: Chart title
        width: Chart width
        height: Chart height

    Returns:
        Chart as string
    """
    if not data:
        return "No data available for chart"

    dates = []
    values = []

    for pr in data:
        date = pr.get("date")
        if date:
            if isinstance(date, datetime):
                dates.append(date.strftime("%m/%d"))
            else:
                dates.append(str(date)[:10])

        value = pr.get("value", 0)
        values.append(float(value) if isinstance(value, Decimal) else value)

    plt.clf()
    plt.scatter(dates, values, marker="braille")
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.plotsize(width, height)

    return plt.build()


def generate_comparison_chart(
    data: dict[str, list[float]],
    labels: list[str],
    title: str = "Comparison",
    width: int = 80,
    height: int = 20,
) -> str:
    """
    Generate multi-line comparison chart.

    Args:
        data: Dictionary mapping series name to list of values
        labels: X-axis labels
        title: Chart title
        width: Chart width
        height: Chart height

    Returns:
        Chart as string
    """
    if not data:
        return "No data available for chart"

    plt.clf()

    for series_name, values in data.items():
        plt.plot(labels, values, label=series_name, marker="braille")

    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.plotsize(width, height)

    return plt.build()


def generate_weekly_volume_comparison(
    data: list[dict], weeks_to_compare: int = 4, width: int = 80, height: int = 20
) -> str:
    """
    Generate chart comparing weekly volumes.

    Args:
        data: List of weekly data
        weeks_to_compare: Number of recent weeks to compare
        width: Chart width
        height: Chart height

    Returns:
        Chart as string
    """
    if not data:
        return "No data available for chart"

    # Take most recent weeks
    recent_data = data[:weeks_to_compare]
    recent_data.reverse()  # Chronological order

    weeks = []
    volumes = []

    for entry in recent_data:
        week = entry.get("week_start")
        if week:
            if isinstance(week, datetime):
                weeks.append(week.strftime("%m/%d"))
            else:
                weeks.append(str(week)[:10])

        volume = entry.get("total_volume", 0)
        volumes.append(float(volume) if isinstance(volume, Decimal) else volume)

    plt.clf()
    plt.bar(weeks, volumes)
    plt.title(f"Volume Comparison - Last {weeks_to_compare} Weeks")
    plt.xlabel("Week")
    plt.ylabel("Total Volume (lbs)")
    plt.plotsize(width, height)

    return plt.build()


def format_chart_for_display(chart: str, border: bool = True) -> str:
    """
    Format a chart for display with optional border.

    Args:
        chart: Chart string from plotext
        border: Whether to add border

    Returns:
        Formatted chart string
    """
    if not border:
        return chart

    lines = chart.split("\n")
    max_width = max(len(line) for line in lines) if lines else 0

    border_line = "─" * (max_width + 2)
    formatted = ["┌" + border_line + "┐"]

    for line in lines:
        padding = max_width - len(line)
        formatted.append("│ " + line + " " * padding + " │")

    formatted.append("└" + border_line + "┘")

    return "\n".join(formatted)


def generate_simple_sparkline(values: list[float], width: int = 50) -> str:
    """
    Generate a simple ASCII sparkline.

    Args:
        values: List of numeric values
        width: Width of sparkline

    Returns:
        ASCII sparkline string
    """
    if not values:
        return ""

    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val

    if range_val == 0:
        return "─" * width

    chars = " ▁▂▃▄▅▆▇█"

    sparkline = []
    for val in values:
        normalized = (val - min_val) / range_val
        idx = int(normalized * (len(chars) - 1))
        sparkline.append(chars[idx])

    return "".join(sparkline)
