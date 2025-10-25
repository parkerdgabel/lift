"""Unit conversion utilities for body measurements and weights."""

from decimal import Decimal, ROUND_HALF_UP

from lift.core.models import MeasurementUnit, WeightUnit


# Conversion constants
LBS_TO_KG_FACTOR = Decimal("0.45359237")
KG_TO_LBS_FACTOR = Decimal("2.20462262")
INCHES_TO_CM_FACTOR = Decimal("2.54")
CM_TO_INCHES_FACTOR = Decimal("0.393700787")


def lbs_to_kg(lbs: Decimal) -> Decimal:
    """
    Convert pounds to kilograms.

    Args:
        lbs: Weight in pounds

    Returns:
        Weight in kilograms, rounded to 2 decimal places

    Example:
        >>> lbs_to_kg(Decimal("185.2"))
        Decimal('84.00')
    """
    result = lbs * LBS_TO_KG_FACTOR
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def kg_to_lbs(kg: Decimal) -> Decimal:
    """
    Convert kilograms to pounds.

    Args:
        kg: Weight in kilograms

    Returns:
        Weight in pounds, rounded to 2 decimal places

    Example:
        >>> kg_to_lbs(Decimal("84.00"))
        Decimal('185.19')
    """
    result = kg * KG_TO_LBS_FACTOR
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def inches_to_cm(inches: Decimal) -> Decimal:
    """
    Convert inches to centimeters.

    Args:
        inches: Measurement in inches

    Returns:
        Measurement in centimeters, rounded to 2 decimal places

    Example:
        >>> inches_to_cm(Decimal("15.5"))
        Decimal('39.37')
    """
    result = inches * INCHES_TO_CM_FACTOR
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def cm_to_inches(cm: Decimal) -> Decimal:
    """
    Convert centimeters to inches.

    Args:
        cm: Measurement in centimeters

    Returns:
        Measurement in inches, rounded to 2 decimal places

    Example:
        >>> cm_to_inches(Decimal("39.37"))
        Decimal('15.50')
    """
    result = cm * CM_TO_INCHES_FACTOR
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def convert_weight(value: Decimal, from_unit: WeightUnit, to_unit: WeightUnit) -> Decimal:
    """
    Convert weight between different units.

    Args:
        value: Weight value to convert
        from_unit: Source unit (lbs or kg)
        to_unit: Target unit (lbs or kg)

    Returns:
        Converted weight value, rounded to 2 decimal places

    Example:
        >>> convert_weight(Decimal("185.2"), WeightUnit.LBS, WeightUnit.KG)
        Decimal('84.00')
    """
    if from_unit == to_unit:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if from_unit == WeightUnit.LBS and to_unit == WeightUnit.KG:
        return lbs_to_kg(value)
    elif from_unit == WeightUnit.KG and to_unit == WeightUnit.LBS:
        return kg_to_lbs(value)
    else:
        raise ValueError(f"Unknown weight unit conversion: {from_unit} to {to_unit}")


def convert_measurement(
    value: Decimal, from_unit: MeasurementUnit, to_unit: MeasurementUnit
) -> Decimal:
    """
    Convert body measurements between different units.

    Args:
        value: Measurement value to convert
        from_unit: Source unit (in or cm)
        to_unit: Target unit (in or cm)

    Returns:
        Converted measurement value, rounded to 2 decimal places

    Example:
        >>> convert_measurement(Decimal("15.5"), MeasurementUnit.INCHES, MeasurementUnit.CENTIMETERS)
        Decimal('39.37')
    """
    if from_unit == to_unit:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if from_unit == MeasurementUnit.INCHES and to_unit == MeasurementUnit.CENTIMETERS:
        return inches_to_cm(value)
    elif from_unit == MeasurementUnit.CENTIMETERS and to_unit == MeasurementUnit.INCHES:
        return cm_to_inches(value)
    else:
        raise ValueError(f"Unknown measurement unit conversion: {from_unit} to {to_unit}")
