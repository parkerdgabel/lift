"""Tests for body measurement formatting utilities."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lift.core.models import BodyMeasurement, MeasurementUnit, WeightUnit
from lift.utils.body_formatters import (
    format_measurement_chart,
    format_measurement_detail,
    format_measurement_table,
    format_progress_comparison,
    format_progress_summary,
    format_weight_log_response,
)


@pytest.mark.formatter
class TestFormatMeasurementTable:
    """Test measurement table formatting."""

    def test_measurement_table_basic(self) -> None:
        """Test basic measurement table formatting."""
        measurements = [
            BodyMeasurement(
                id=1,
                date=datetime(2024, 1, 15),
                weight=Decimal("185.5"),
                weight_unit=WeightUnit.LBS,
                body_fat_pct=Decimal("15.2"),
                chest=Decimal("42.0"),
                waist=Decimal("32.0"),
                bicep_left=Decimal("15.5"),
                thigh_left=Decimal("24.0"),
                measurement_unit=MeasurementUnit.INCHES,
            ),
            BodyMeasurement(
                id=2,
                date=datetime(2024, 1, 22),
                weight=Decimal("187.0"),
                weight_unit=WeightUnit.LBS,
                body_fat_pct=Decimal("15.0"),
                chest=Decimal("42.5"),
                waist=Decimal("31.5"),
                bicep_left=Decimal("15.75"),
                thigh_left=Decimal("24.5"),
                measurement_unit=MeasurementUnit.INCHES,
            ),
        ]

        result = format_measurement_table(measurements)

        assert isinstance(result, Table)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "185.5" in output
        assert "187.0" in output
        assert "15.2%" in output
        assert "42.0" in output

    def test_measurement_table_empty(self) -> None:
        """Test empty measurement table."""
        result = format_measurement_table([])

        assert isinstance(result, Table)

    def test_measurement_table_partial_data(self) -> None:
        """Test measurement table with partial data."""
        measurements = [
            BodyMeasurement(
                id=1,
                date=datetime.now(),
                weight=Decimal("180.0"),
                weight_unit=WeightUnit.LBS,
                body_fat_pct=None,
                chest=None,
                waist=None,
                bicep_left=None,
                thigh_left=None,
                measurement_unit=MeasurementUnit.INCHES,
            ),
        ]

        result = format_measurement_table(measurements)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "180.0" in output
        assert "-" in output  # Should show dash for missing values

    def test_measurement_table_kilograms(self) -> None:
        """Test measurement table with kilograms."""
        measurements = [
            BodyMeasurement(
                id=1,
                date=datetime.now(),
                weight=Decimal("84.0"),
                weight_unit=WeightUnit.KG,
                measurement_unit=MeasurementUnit.CENTIMETERS,
            ),
        ]

        result = format_measurement_table(measurements)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "84" in output  # May show as 84.0 or 84
        # Weight unit shown in table


@pytest.mark.formatter
class TestFormatMeasurementDetail:
    """Test measurement detail formatting."""

    def test_measurement_detail_complete(self) -> None:
        """Test measurement detail with all fields."""
        measurement = BodyMeasurement(
            id=1,
            date=datetime(2024, 1, 15, 10, 30),
            weight=Decimal("185.5"),
            weight_unit=WeightUnit.LBS,
            body_fat_pct=Decimal("15.2"),
            neck=Decimal("16.0"),
            shoulders=Decimal("48.0"),
            chest=Decimal("42.0"),
            waist=Decimal("32.0"),
            hips=Decimal("38.0"),
            bicep_left=Decimal("15.5"),
            bicep_right=Decimal("15.75"),
            forearm_left=Decimal("12.5"),
            forearm_right=Decimal("12.5"),
            thigh_left=Decimal("24.0"),
            thigh_right=Decimal("24.5"),
            calf_left=Decimal("15.0"),
            calf_right=Decimal("15.0"),
            measurement_unit=MeasurementUnit.INCHES,
            notes="Feeling great!",
        )

        result = format_measurement_detail(measurement)

        assert isinstance(result, Panel)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "185.5" in output
        assert "15.2%" in output
        assert "16.0" in output  # neck
        assert "48.0" in output  # shoulders
        assert "42.0" in output  # chest
        assert "32.0" in output  # waist
        assert "15.5" in output  # bicep
        assert "24.0" in output  # thigh
        assert "Feeling great!" in output

    def test_measurement_detail_weight_only(self) -> None:
        """Test measurement detail with only weight."""
        measurement = BodyMeasurement(
            id=1,
            date=datetime.now(),
            weight=Decimal("180.0"),
            weight_unit=WeightUnit.LBS,
            measurement_unit=MeasurementUnit.INCHES,
        )

        result = format_measurement_detail(measurement)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "180.0" in output

    def test_measurement_detail_no_notes(self) -> None:
        """Test measurement detail without notes."""
        measurement = BodyMeasurement(
            id=1,
            date=datetime.now(),
            weight=Decimal("185.0"),
            weight_unit=WeightUnit.LBS,
            measurement_unit=MeasurementUnit.INCHES,
            notes=None,
        )

        result = format_measurement_detail(measurement)
        assert isinstance(result, Panel)


@pytest.mark.formatter
class TestFormatProgressComparison:
    """Test progress comparison formatting."""

    def test_progress_comparison_weight_gain(self) -> None:
        """Test progress comparison with weight gain."""
        current = {"weight": Decimal("187.0")}
        previous = {"weight": Decimal("185.0")}
        differences = {
            "weight": {
                "current": Decimal("187.0"),
                "previous": Decimal("185.0"),
                "change": Decimal("2.0"),
                "percent": Decimal("1.08"),
            }
        }

        result = format_progress_comparison(current, previous, differences)

        assert isinstance(result, Table)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "187.00" in output
        assert "185.00" in output
        assert "+2.00" in output

    def test_progress_comparison_weight_loss(self) -> None:
        """Test progress comparison with weight loss."""
        current = {"weight": Decimal("180.0")}
        previous = {"weight": Decimal("185.0")}
        differences = {
            "weight": {
                "current": Decimal("180.0"),
                "previous": Decimal("185.0"),
                "change": Decimal("-5.0"),
                "percent": Decimal("-2.7"),
            }
        }

        result = format_progress_comparison(current, previous, differences)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "180.00" in output
        assert "185.00" in output
        assert "-5.00" in output

    def test_progress_comparison_multiple_measurements(self) -> None:
        """Test progress comparison with multiple measurements."""
        current = {
            "weight": Decimal("187.0"),
            "body_fat_pct": Decimal("14.5"),
            "chest": Decimal("42.5"),
        }
        previous = {
            "weight": Decimal("185.0"),
            "body_fat_pct": Decimal("15.0"),
            "chest": Decimal("42.0"),
        }
        differences = {
            "weight": {
                "current": Decimal("187.0"),
                "previous": Decimal("185.0"),
                "change": Decimal("2.0"),
                "percent": Decimal("1.08"),
            },
            "body_fat_pct": {
                "current": Decimal("14.5"),
                "previous": Decimal("15.0"),
                "change": Decimal("-0.5"),
                "percent": Decimal("-3.33"),
            },
            "chest": {
                "current": Decimal("42.5"),
                "previous": Decimal("42.0"),
                "change": Decimal("0.5"),
                "percent": Decimal("1.19"),
            },
        }

        result = format_progress_comparison(current, previous, differences)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Weight" in output
        assert "Body Fat" in output
        assert "Chest" in output

    def test_progress_comparison_no_change(self) -> None:
        """Test progress comparison with no change."""
        current = {"weight": Decimal("185.0")}
        previous = {"weight": Decimal("185.0")}
        differences = {
            "weight": {
                "current": Decimal("185.0"),
                "previous": Decimal("185.0"),
                "change": Decimal("0.0"),
                "percent": Decimal("0.0"),
            }
        }

        result = format_progress_comparison(current, previous, differences)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "0.00" in output


@pytest.mark.formatter
class TestFormatMeasurementChart:
    """Test measurement chart formatting."""

    def test_measurement_chart_basic(self) -> None:
        """Test basic measurement chart."""
        data = [
            {"date": datetime(2024, 1, 1), "value": Decimal("180.0"), "unit": "lbs"},
            {"date": datetime(2024, 1, 8), "value": Decimal("182.0"), "unit": "lbs"},
            {"date": datetime(2024, 1, 15), "value": Decimal("185.0"), "unit": "lbs"},
        ]

        result = format_measurement_chart("Weight", data)

        assert isinstance(result, str)
        assert "Weight Trend" in result or "Weight" in result
        assert "lbs" in result

    def test_measurement_chart_empty(self) -> None:
        """Test measurement chart with no data."""
        result = format_measurement_chart("Weight", [])

        assert isinstance(result, str)
        assert "No data available" in result

    def test_measurement_chart_many_points(self) -> None:
        """Test measurement chart with many data points."""
        data = [
            {
                "date": datetime(2024, 1, 1) + timedelta(days=i),
                "value": Decimal(str(180.0 + i * 0.5)),
                "unit": "lbs",
            }
            for i in range(30)
        ]

        result = format_measurement_chart("Weight", data)

        assert isinstance(result, str)
        assert "lbs" in result

    def test_measurement_chart_downward_trend(self) -> None:
        """Test measurement chart with downward trend."""
        data = [
            {"date": datetime(2024, 1, 1), "value": Decimal("200.0"), "unit": "lbs"},
            {"date": datetime(2024, 1, 15), "value": Decimal("195.0"), "unit": "lbs"},
            {"date": datetime(2024, 1, 30), "value": Decimal("190.0"), "unit": "lbs"},
        ]

        result = format_measurement_chart("Weight", data)

        assert isinstance(result, str)
        # Should show negative trend
        assert "-" in result or "Trend" in result

    def test_measurement_chart_single_point(self) -> None:
        """Test measurement chart with single data point."""
        data = [{"date": datetime.now(), "value": Decimal("185.0"), "unit": "lbs"}]

        result = format_measurement_chart("Weight", data)

        assert isinstance(result, str)
        assert "185" in result


@pytest.mark.formatter
class TestFormatWeightLogResponse:
    """Test weight log response formatting."""

    def test_weight_log_basic(self) -> None:
        """Test basic weight log response."""
        result = format_weight_log_response(Decimal("185.5"), "lbs")

        assert isinstance(result, Panel)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "185.5" in output
        assert "lbs" in output

    def test_weight_log_with_previous_higher(self) -> None:
        """Test weight log with previous weight (weight gain)."""
        result = format_weight_log_response(
            Decimal("187.0"), "lbs", previous_weight=(Decimal("185.0"), "lbs")
        )

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "187.0" in output
        assert "185.0" in output
        assert "+2.0" in output

    def test_weight_log_with_previous_lower(self) -> None:
        """Test weight log with previous weight (weight loss)."""
        result = format_weight_log_response(
            Decimal("180.0"), "lbs", previous_weight=(Decimal("185.0"), "lbs")
        )

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "180.0" in output
        assert "185.0" in output
        assert "-5.0" in output

    def test_weight_log_with_previous_same(self) -> None:
        """Test weight log with same previous weight."""
        result = format_weight_log_response(
            Decimal("185.0"), "lbs", previous_weight=(Decimal("185.0"), "lbs")
        )

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "no change" in output

    def test_weight_log_with_seven_day_avg(self) -> None:
        """Test weight log with 7-day average."""
        result = format_weight_log_response(Decimal("185.5"), "lbs", seven_day_avg=Decimal("184.3"))

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "184.3" in output
        assert "7-day avg" in output

    def test_weight_log_all_data(self) -> None:
        """Test weight log with all optional data."""
        result = format_weight_log_response(
            Decimal("187.0"),
            "lbs",
            previous_weight=(Decimal("185.0"), "lbs"),
            seven_day_avg=Decimal("185.5"),
        )

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "187.0" in output
        assert "185.0" in output
        assert "185.5" in output
        assert "+2.0" in output


@pytest.mark.formatter
class TestFormatProgressSummary:
    """Test progress summary text generation."""

    def test_progress_summary_lean_mass_gain(self) -> None:
        """Test summary for lean mass gain (weight up, bf down)."""
        differences = {
            "weight": {"change": Decimal("3.0")},
            "body_fat_pct": {"change": Decimal("-0.5")},
        }

        result = format_progress_summary(4.0, differences)

        assert "Gaining lean mass" in result
        assert "Weight up" in result or "weight up" in result
        assert "body fat down" in result

    def test_progress_summary_muscle_loss(self) -> None:
        """Test summary for muscle loss (weight down, bf up)."""
        differences = {
            "weight": {"change": Decimal("-5.0")},
            "body_fat_pct": {"change": Decimal("1.0")},
        }

        result = format_progress_summary(4.0, differences)

        assert "Losing muscle mass" in result

    def test_progress_summary_dirty_bulk(self) -> None:
        """Test summary for weight gain with fat (weight up, bf up)."""
        differences = {
            "weight": {"change": Decimal("5.0")},
            "body_fat_pct": {"change": Decimal("1.5")},
        }

        result = format_progress_summary(4.0, differences)

        assert "Gaining weight with some fat" in result

    def test_progress_summary_successful_cut(self) -> None:
        """Test summary for successful cut (weight down, bf down)."""
        differences = {
            "weight": {"change": Decimal("-5.0")},
            "body_fat_pct": {"change": Decimal("-1.5")},
        }

        result = format_progress_summary(4.0, differences)

        assert "Cutting successfully" in result

    def test_progress_summary_weight_gain_only(self) -> None:
        """Test summary for weight gain without bf data."""
        differences = {"weight": {"change": Decimal("3.0")}}

        result = format_progress_summary(4.0, differences)

        assert "gaining" in result.lower()

    def test_progress_summary_weight_loss_only(self) -> None:
        """Test summary for weight loss without bf data."""
        differences = {"weight": {"change": Decimal("-3.0")}}

        result = format_progress_summary(4.0, differences)

        assert "loss" in result.lower()

    def test_progress_summary_bf_decrease_only(self) -> None:
        """Test summary for body fat decrease without weight data."""
        differences = {"body_fat_pct": {"change": Decimal("-1.0")}}

        result = format_progress_summary(4.0, differences)

        assert "recomposition" in result or "Losing fat" in result

    def test_progress_summary_bf_increase_only(self) -> None:
        """Test summary for body fat increase without weight data."""
        differences = {"body_fat_pct": {"change": Decimal("1.0")}}

        result = format_progress_summary(4.0, differences)

        assert "Body fat increasing" in result

    def test_progress_summary_no_weight_or_bf(self) -> None:
        """Test summary with no weight or body fat changes."""
        differences = {"chest": {"change": Decimal("0.5")}}

        result = format_progress_summary(4.0, differences)

        assert "4.0 weeks" in result

    def test_progress_summary_no_data(self) -> None:
        """Test summary with no data."""
        result = format_progress_summary(4.0, {})

        assert "4.0 weeks" in result
