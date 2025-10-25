"""Tests for unit conversion utilities."""

from decimal import Decimal

import pytest

from lift.core.models import MeasurementUnit, WeightUnit
from lift.utils.conversions import (
    cm_to_inches,
    convert_measurement,
    convert_weight,
    inches_to_cm,
    kg_to_lbs,
    lbs_to_kg,
)


class TestWeightConversions:
    """Test weight conversion functions."""

    def test_lbs_to_kg(self) -> None:
        """Test pounds to kilograms conversion."""
        # Standard conversion (185.2 * 0.45359237 = 84.005... rounds to 84.01)
        result = lbs_to_kg(Decimal("185.2"))
        assert result == Decimal("84.01")

        # Edge cases
        assert lbs_to_kg(Decimal("0")) == Decimal("0.00")
        assert lbs_to_kg(Decimal("1")) == Decimal("0.45")
        assert lbs_to_kg(Decimal("220.5")) == Decimal("100.02")

    def test_kg_to_lbs(self) -> None:
        """Test kilograms to pounds conversion."""
        # Standard conversion
        result = kg_to_lbs(Decimal("84.00"))
        assert result == Decimal("185.19")

        # Edge cases
        assert kg_to_lbs(Decimal("0")) == Decimal("0.00")
        assert kg_to_lbs(Decimal("1")) == Decimal("2.20")
        assert kg_to_lbs(Decimal("100")) == Decimal("220.46")

    def test_weight_conversion_roundtrip(self) -> None:
        """Test that converting back and forth maintains precision."""
        original = Decimal("185.2")
        kg = lbs_to_kg(original)
        back_to_lbs = kg_to_lbs(kg)

        # Allow small rounding difference
        assert abs(back_to_lbs - original) < Decimal("0.1")

    def test_weight_conversion_precision(self) -> None:
        """Test that conversions are rounded to 2 decimal places."""
        result = lbs_to_kg(Decimal("123.456"))
        assert result.as_tuple().exponent == -2  # 2 decimal places

        result = kg_to_lbs(Decimal("56.789"))
        assert result.as_tuple().exponent == -2


class TestMeasurementConversions:
    """Test body measurement conversion functions."""

    def test_inches_to_cm(self) -> None:
        """Test inches to centimeters conversion."""
        # Standard conversion
        result = inches_to_cm(Decimal("15.5"))
        assert result == Decimal("39.37")

        # Edge cases
        assert inches_to_cm(Decimal("0")) == Decimal("0.00")
        assert inches_to_cm(Decimal("1")) == Decimal("2.54")
        assert inches_to_cm(Decimal("42.5")) == Decimal("107.95")

    def test_cm_to_inches(self) -> None:
        """Test centimeters to inches conversion."""
        # Standard conversion
        result = cm_to_inches(Decimal("39.37"))
        assert result == Decimal("15.50")

        # Edge cases
        assert cm_to_inches(Decimal("0")) == Decimal("0.00")
        assert cm_to_inches(Decimal("2.54")) == Decimal("1.00")
        assert cm_to_inches(Decimal("100")) == Decimal("39.37")

    def test_measurement_conversion_roundtrip(self) -> None:
        """Test that converting back and forth maintains precision."""
        original = Decimal("15.5")
        cm = inches_to_cm(original)
        back_to_inches = cm_to_inches(cm)

        # Should be very close to original
        assert abs(back_to_inches - original) < Decimal("0.1")

    def test_measurement_conversion_precision(self) -> None:
        """Test that conversions are rounded to 2 decimal places."""
        result = inches_to_cm(Decimal("12.345"))
        assert result.as_tuple().exponent == -2

        result = cm_to_inches(Decimal("45.678"))
        assert result.as_tuple().exponent == -2


class TestConvertWeight:
    """Test the convert_weight function."""

    def test_convert_lbs_to_kg(self) -> None:
        """Test converting lbs to kg."""
        result = convert_weight(Decimal("185.2"), WeightUnit.LBS, WeightUnit.KG)
        assert result == Decimal("84.01")

    def test_convert_kg_to_lbs(self) -> None:
        """Test converting kg to lbs."""
        result = convert_weight(Decimal("84.00"), WeightUnit.KG, WeightUnit.LBS)
        assert result == Decimal("185.19")

    def test_convert_same_unit(self) -> None:
        """Test that converting to the same unit returns the value unchanged."""
        result = convert_weight(Decimal("185.2"), WeightUnit.LBS, WeightUnit.LBS)
        assert result == Decimal("185.20")

        result = convert_weight(Decimal("84.5"), WeightUnit.KG, WeightUnit.KG)
        assert result == Decimal("84.50")

    def test_convert_weight_invalid_unit(self) -> None:
        """Test that invalid unit combinations raise ValueError."""
        # This shouldn't happen with proper enum usage, but test defensive code
        with pytest.raises(ValueError):
            # Force an invalid conversion by mocking
            convert_weight(Decimal("100"), "invalid", WeightUnit.LBS)  # type: ignore


class TestConvertMeasurement:
    """Test the convert_measurement function."""

    def test_convert_inches_to_cm(self) -> None:
        """Test converting inches to cm."""
        result = convert_measurement(
            Decimal("15.5"), MeasurementUnit.INCHES, MeasurementUnit.CENTIMETERS
        )
        assert result == Decimal("39.37")

    def test_convert_cm_to_inches(self) -> None:
        """Test converting cm to inches."""
        result = convert_measurement(
            Decimal("39.37"), MeasurementUnit.CENTIMETERS, MeasurementUnit.INCHES
        )
        assert result == Decimal("15.50")

    def test_convert_same_unit(self) -> None:
        """Test that converting to the same unit returns the value unchanged."""
        result = convert_measurement(
            Decimal("15.5"), MeasurementUnit.INCHES, MeasurementUnit.INCHES
        )
        assert result == Decimal("15.50")

        result = convert_measurement(
            Decimal("39.37"), MeasurementUnit.CENTIMETERS, MeasurementUnit.CENTIMETERS
        )
        assert result == Decimal("39.37")

    def test_convert_measurement_invalid_unit(self) -> None:
        """Test that invalid unit combinations raise ValueError."""
        with pytest.raises(ValueError):
            convert_measurement(Decimal("100"), "invalid", MeasurementUnit.INCHES)  # type: ignore


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_conversions(self) -> None:
        """Test that zero converts correctly."""
        assert lbs_to_kg(Decimal("0")) == Decimal("0.00")
        assert kg_to_lbs(Decimal("0")) == Decimal("0.00")
        assert inches_to_cm(Decimal("0")) == Decimal("0.00")
        assert cm_to_inches(Decimal("0")) == Decimal("0.00")

    def test_very_large_values(self) -> None:
        """Test conversions with very large values."""
        large_weight = Decimal("1000.0")
        result = lbs_to_kg(large_weight)
        assert result > Decimal("0")
        assert result.as_tuple().exponent == -2

        large_measurement = Decimal("1000.0")
        result = inches_to_cm(large_measurement)
        assert result > Decimal("0")
        assert result.as_tuple().exponent == -2

    def test_very_small_values(self) -> None:
        """Test conversions with very small values."""
        small_weight = Decimal("0.1")
        result = lbs_to_kg(small_weight)
        assert result > Decimal("0")
        assert result.as_tuple().exponent == -2

        small_measurement = Decimal("0.1")
        result = inches_to_cm(small_measurement)
        assert result > Decimal("0")
        assert result.as_tuple().exponent == -2

    def test_decimal_precision(self) -> None:
        """Test that decimal precision is maintained."""
        # Test with various decimal places
        values = [
            Decimal("185.2"),
            Decimal("185.25"),
            Decimal("185.255"),
            Decimal("185.2555"),
        ]

        for value in values:
            result = lbs_to_kg(value)
            # All should round to 2 decimal places
            assert result.as_tuple().exponent == -2
