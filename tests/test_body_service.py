"""Tests for body measurement service."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from lift.core.database import DatabaseManager
from lift.core.models import BodyMeasurementCreate, MeasurementUnit, WeightUnit
from lift.services.body_service import BodyService


@pytest.fixture
def service(db: DatabaseManager) -> BodyService:
    """Create a BodyService instance with test database."""
    return BodyService(db)


class TestLogWeight:
    """Test weight logging functionality."""

    def test_log_weight_lbs(self, service: BodyService) -> None:
        """Test logging weight in pounds."""
        weight = Decimal("185.2")
        measurement = service.log_weight(weight, WeightUnit.LBS)

        assert measurement.weight == weight
        assert measurement.weight_unit == WeightUnit.LBS
        assert measurement.id > 0

    def test_log_weight_kg(self, service: BodyService) -> None:
        """Test logging weight in kilograms."""
        weight = Decimal("84.5")
        measurement = service.log_weight(weight, WeightUnit.KG)

        assert measurement.weight == weight
        assert measurement.weight_unit == WeightUnit.KG
        assert measurement.id > 0

    def test_log_multiple_weights(self, service: BodyService) -> None:
        """Test logging multiple weight entries."""
        weights = [
            Decimal("185.2"),
            Decimal("184.8"),
            Decimal("185.5"),
        ]

        for weight in weights:
            measurement = service.log_weight(weight, WeightUnit.LBS)
            assert measurement.weight == weight

        # Verify all were saved
        history = service.get_measurement_history(limit=10)
        assert len(history) == 3


class TestLogMeasurement:
    """Test comprehensive measurement logging."""

    def test_log_full_measurement(self, service: BodyService) -> None:
        """Test logging a complete body measurement."""
        measurement_data = BodyMeasurementCreate(
            date=datetime.now(),
            weight=Decimal("185.2"),
            weight_unit=WeightUnit.LBS,
            body_fat_pct=Decimal("12.5"),
            neck=Decimal("16.0"),
            shoulders=Decimal("48.0"),
            chest=Decimal("42.5"),
            waist=Decimal("32.0"),
            hips=Decimal("38.0"),
            bicep_left=Decimal("15.5"),
            bicep_right=Decimal("15.5"),
            forearm_left=Decimal("12.0"),
            forearm_right=Decimal("12.0"),
            thigh_left=Decimal("24.0"),
            thigh_right=Decimal("24.0"),
            calf_left=Decimal("15.0"),
            calf_right=Decimal("15.0"),
            measurement_unit=MeasurementUnit.INCHES,
            notes="Full body measurement",
        )

        measurement = service.log_measurement(measurement_data)

        assert measurement.id > 0
        assert measurement.weight == Decimal("185.2")
        assert measurement.body_fat_pct == Decimal("12.5")
        assert measurement.chest == Decimal("42.5")
        assert measurement.waist == Decimal("32.0")
        assert measurement.notes == "Full body measurement"

    def test_log_partial_measurement(self, service: BodyService) -> None:
        """Test logging measurement with only some fields."""
        measurement_data = BodyMeasurementCreate(
            date=datetime.now(),
            weight=Decimal("185.2"),
            weight_unit=WeightUnit.LBS,
            waist=Decimal("32.0"),
            measurement_unit=MeasurementUnit.INCHES,
        )

        measurement = service.log_measurement(measurement_data)

        assert measurement.id > 0
        assert measurement.weight == Decimal("185.2")
        assert measurement.waist == Decimal("32.0")
        assert measurement.body_fat_pct is None
        assert measurement.chest is None


class TestGetLatestMeasurement:
    """Test retrieving the latest measurement."""

    def test_get_latest_measurement_when_exists(self, service: BodyService) -> None:
        """Test getting latest measurement when measurements exist."""
        # Log several measurements
        for i in range(3):
            service.log_weight(Decimal(f"185.{i}"), WeightUnit.LBS)

        latest = service.get_latest_measurement()
        assert latest is not None
        assert latest.weight == Decimal("185.2")

    def test_get_latest_measurement_when_empty(self, service: BodyService) -> None:
        """Test getting latest measurement when no measurements exist."""
        latest = service.get_latest_measurement()
        assert latest is None

    def test_get_latest_weight(self, service: BodyService) -> None:
        """Test getting latest weight only."""
        service.log_weight(Decimal("185.2"), WeightUnit.LBS)

        weight, unit = service.get_latest_weight()
        assert weight == Decimal("185.2")
        assert unit == WeightUnit.LBS

    def test_get_latest_weight_when_empty(self, service: BodyService) -> None:
        """Test getting latest weight when no measurements exist."""
        result = service.get_latest_weight()
        assert result is None


class TestMeasurementHistory:
    """Test measurement history retrieval."""

    def test_get_measurement_history(self, service: BodyService) -> None:
        """Test retrieving measurement history."""
        # Create multiple measurements
        for i in range(5):
            service.log_weight(Decimal(f"185.{i}"), WeightUnit.LBS)

        history = service.get_measurement_history(limit=10)
        assert len(history) == 5
        # Should be in descending order (most recent first)
        assert history[0].weight == Decimal("185.4")

    def test_get_measurement_history_with_limit(self, service: BodyService) -> None:
        """Test that limit parameter works correctly."""
        # Create 10 measurements
        for i in range(10):
            service.log_weight(Decimal(f"180.{i}"), WeightUnit.LBS)

        history = service.get_measurement_history(limit=5)
        assert len(history) == 5

    def test_get_weight_history(self, service: BodyService) -> None:
        """Test getting weight history over time."""
        # Create measurements over several weeks
        base_date = datetime.now() - timedelta(weeks=8)

        for week in range(8):
            measurement_data = BodyMeasurementCreate(
                date=base_date + timedelta(weeks=week),
                weight=Decimal(f"180.{week}"),
                weight_unit=WeightUnit.LBS,
            )
            service.log_measurement(measurement_data)

        history = service.get_weight_history(weeks_back=12)
        assert len(history) == 8
        assert history[0]["weight"] == Decimal("180.0")
        assert history[-1]["weight"] == Decimal("180.7")


class TestMeasurementTrend:
    """Test measurement trend analysis."""

    def test_get_measurement_trend_valid_field(self, service: BodyService) -> None:
        """Test getting trend for a valid measurement field."""
        # Create measurements with chest values
        base_date = datetime.now() - timedelta(weeks=4)

        for week in range(4):
            measurement_data = BodyMeasurementCreate(
                date=base_date + timedelta(weeks=week),
                chest=Decimal(f"42.{week}"),
                measurement_unit=MeasurementUnit.INCHES,
            )
            service.log_measurement(measurement_data)

        trend = service.get_measurement_trend("chest", weeks_back=12)
        assert len(trend) == 4
        assert trend[0]["value"] == Decimal("42.0")

    def test_get_measurement_trend_invalid_field(self, service: BodyService) -> None:
        """Test that invalid field raises ValueError."""
        with pytest.raises(ValueError, match="Invalid measurement field"):
            service.get_measurement_trend("invalid_field", weeks_back=12)

    def test_get_measurement_trend_no_data(self, service: BodyService) -> None:
        """Test getting trend when no data exists."""
        trend = service.get_measurement_trend("waist", weeks_back=12)
        assert len(trend) == 0


class TestCompareMeasurements:
    """Test measurement comparison functionality."""

    def test_compare_two_measurements(self, service: BodyService) -> None:
        """Test comparing two measurements."""
        # Create two measurements
        measurement1_data = BodyMeasurementCreate(
            date=datetime.now() - timedelta(weeks=4),
            weight=Decimal("180.0"),
            weight_unit=WeightUnit.LBS,
            chest=Decimal("42.0"),
            waist=Decimal("32.5"),
            measurement_unit=MeasurementUnit.INCHES,
        )
        measurement2_data = BodyMeasurementCreate(
            date=datetime.now(),
            weight=Decimal("185.0"),
            weight_unit=WeightUnit.LBS,
            chest=Decimal("42.5"),
            waist=Decimal("32.0"),
            measurement_unit=MeasurementUnit.INCHES,
        )

        m1 = service.log_measurement(measurement1_data)
        m2 = service.log_measurement(measurement2_data)

        comparison = service.compare_measurements(m2.id, m1.id)

        assert "differences" in comparison
        assert "weight" in comparison["differences"]
        assert comparison["differences"]["weight"]["change"] == Decimal("5.0")
        assert comparison["differences"]["chest"]["change"] == Decimal("0.5")
        assert comparison["differences"]["waist"]["change"] == Decimal("-0.5")

    def test_compare_measurements_not_found(self, service: BodyService) -> None:
        """Test comparing measurements that don't exist."""
        with pytest.raises(ValueError, match="not found"):
            service.compare_measurements(999, 998)


class TestProgressReport:
    """Test progress report generation."""

    def test_get_progress_report(self, service: BodyService) -> None:
        """Test generating a progress report."""
        # Create measurements 4 weeks apart
        old_measurement = BodyMeasurementCreate(
            date=datetime.now() - timedelta(weeks=4),
            weight=Decimal("180.0"),
            weight_unit=WeightUnit.LBS,
            body_fat_pct=Decimal("15.0"),
            chest=Decimal("42.0"),
            measurement_unit=MeasurementUnit.INCHES,
        )
        new_measurement = BodyMeasurementCreate(
            date=datetime.now(),
            weight=Decimal("185.0"),
            weight_unit=WeightUnit.LBS,
            body_fat_pct=Decimal("13.0"),
            chest=Decimal("42.5"),
            measurement_unit=MeasurementUnit.INCHES,
        )

        service.log_measurement(old_measurement)
        service.log_measurement(new_measurement)

        report = service.get_progress_report(weeks_back=4)

        assert report["current"].weight == Decimal("185.0")
        assert report["previous"].weight == Decimal("180.0")
        assert report["weeks_apart"] > 3.9
        assert "weight" in report["differences"]
        assert "body_fat_pct" in report["differences"]

    def test_get_progress_report_no_measurements(self, service: BodyService) -> None:
        """Test progress report when no measurements exist."""
        with pytest.raises(ValueError, match="No measurements found"):
            service.get_progress_report(weeks_back=4)

    def test_get_progress_report_insufficient_history(self, service: BodyService) -> None:
        """Test progress report when not enough historical data."""
        # Only create current measurement
        service.log_weight(Decimal("185.0"), WeightUnit.LBS)

        with pytest.raises(ValueError, match="No measurements found from"):
            service.get_progress_report(weeks_back=4)


class TestSevenDayAverage:
    """Test 7-day moving average calculation."""

    def test_get_seven_day_average_weight(self, service: BodyService) -> None:
        """Test calculating 7-day weight average."""
        # Create daily measurements for 7 days
        weights = [185.0, 185.2, 184.8, 185.5, 185.1, 184.9, 185.3]

        for i, weight in enumerate(weights):
            measurement_data = BodyMeasurementCreate(
                date=datetime.now() - timedelta(days=6 - i),
                weight=Decimal(str(weight)),
                weight_unit=WeightUnit.LBS,
            )
            service.log_measurement(measurement_data)

        avg = service.get_seven_day_average("weight")
        assert avg is not None
        # Average should be around 185.1
        assert Decimal("184.5") < avg < Decimal("185.5")

    def test_get_seven_day_average_no_data(self, service: BodyService) -> None:
        """Test 7-day average when no data exists."""
        avg = service.get_seven_day_average("weight")
        assert avg is None

    def test_get_seven_day_average_invalid_field(self, service: BodyService) -> None:
        """Test that invalid field raises ValueError."""
        with pytest.raises(ValueError, match="Invalid field"):
            service.get_seven_day_average("invalid_field")


class TestRowToMeasurement:
    """Test database row conversion to model."""

    def test_row_to_measurement_full_data(self, service: BodyService) -> None:
        """Test converting a full database row to measurement model."""
        measurement_data = BodyMeasurementCreate(
            date=datetime.now(),
            weight=Decimal("185.2"),
            weight_unit=WeightUnit.LBS,
            body_fat_pct=Decimal("12.5"),
            chest=Decimal("42.5"),
            measurement_unit=MeasurementUnit.INCHES,
        )

        measurement = service.log_measurement(measurement_data)

        # Verify all data was properly converted
        assert isinstance(measurement.weight, Decimal)
        assert isinstance(measurement.body_fat_pct, Decimal)
        assert isinstance(measurement.chest, Decimal)
        assert measurement.weight_unit == WeightUnit.LBS

    def test_row_to_measurement_with_nulls(self, service: BodyService) -> None:
        """Test converting row with NULL values."""
        measurement_data = BodyMeasurementCreate(
            date=datetime.now(),
            weight=Decimal("185.2"),
            weight_unit=WeightUnit.LBS,
            measurement_unit=MeasurementUnit.INCHES,
        )

        measurement = service.log_measurement(measurement_data)

        assert measurement.weight == Decimal("185.2")
        assert measurement.body_fat_pct is None
        assert measurement.chest is None
        assert measurement.waist is None
