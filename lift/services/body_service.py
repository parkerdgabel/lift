"""Body measurement tracking service."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from lift.core.database import DatabaseManager
from lift.core.models import (
    BodyMeasurement,
    BodyMeasurementCreate,
    MeasurementUnit,
    WeightUnit,
)


class BodyService:
    """Service for managing body measurements and tracking progress."""

    def __init__(self, db: DatabaseManager) -> None:
        """
        Initialize the body service.

        Args:
            db: Database manager instance
        """
        self.db = db

    def log_weight(
        self, weight: Decimal, unit: WeightUnit = WeightUnit.LBS
    ) -> BodyMeasurement:
        """
        Quick log bodyweight only.

        Args:
            weight: Bodyweight value
            unit: Weight unit (lbs or kg)

        Returns:
            Created body measurement

        Example:
            >>> service.log_weight(Decimal("185.2"), WeightUnit.LBS)
        """
        measurement_create = BodyMeasurementCreate(
            weight=weight,
            weight_unit=unit,
            date=datetime.now(),
        )
        return self.log_measurement(measurement_create)

    def log_measurement(self, measurement: BodyMeasurementCreate) -> BodyMeasurement:
        """
        Log a comprehensive body measurement.

        Args:
            measurement: Body measurement data to log

        Returns:
            Created body measurement with ID

        Example:
            >>> measurement = BodyMeasurementCreate(
            ...     weight=Decimal("185.2"),
            ...     weight_unit=WeightUnit.LBS,
            ...     body_fat_pct=Decimal("12.5"),
            ...     chest=Decimal("42.5")
            ... )
            >>> service.log_measurement(measurement)
        """
        query = """
            INSERT INTO body_measurements (
                date, weight, weight_unit, body_fat_pct,
                neck, shoulders, chest, waist, hips,
                bicep_left, bicep_right, forearm_left, forearm_right,
                thigh_left, thigh_right, calf_left, calf_right,
                measurement_unit, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
        """

        params = (
            measurement.date,
            measurement.weight,
            measurement.weight_unit.value,
            measurement.body_fat_pct,
            measurement.neck,
            measurement.shoulders,
            measurement.chest,
            measurement.waist,
            measurement.hips,
            measurement.bicep_left,
            measurement.bicep_right,
            measurement.forearm_left,
            measurement.forearm_right,
            measurement.thigh_left,
            measurement.thigh_right,
            measurement.calf_left,
            measurement.calf_right,
            measurement.measurement_unit.value,
            measurement.notes,
        )

        result = self.db.execute(query, params)
        if result:
            return self._row_to_measurement(result[0])
        raise RuntimeError("Failed to create body measurement")

    def get_latest_measurement(self) -> Optional[BodyMeasurement]:
        """
        Get the most recent body measurement.

        Returns:
            Latest body measurement or None if no measurements exist

        Example:
            >>> service.get_latest_measurement()
        """
        query = """
            SELECT * FROM body_measurements
            ORDER BY date DESC
            LIMIT 1
        """
        result = self.db.execute(query)
        if result:
            return self._row_to_measurement(result[0])
        return None

    def get_latest_weight(self) -> Optional[tuple[Decimal, WeightUnit]]:
        """
        Get the most recent bodyweight entry.

        Returns:
            Tuple of (weight, unit) or None if no weight logged

        Example:
            >>> service.get_latest_weight()
            (Decimal('185.2'), WeightUnit.LBS)
        """
        query = """
            SELECT weight, weight_unit FROM body_measurements
            WHERE weight IS NOT NULL
            ORDER BY date DESC
            LIMIT 1
        """
        result = self.db.execute(query)
        if result and result[0][0] is not None:
            return (Decimal(str(result[0][0])), WeightUnit(result[0][1]))
        return None

    def get_measurement_history(self, limit: int = 50) -> list[BodyMeasurement]:
        """
        Get body measurement history.

        Args:
            limit: Maximum number of measurements to return

        Returns:
            List of body measurements, most recent first

        Example:
            >>> service.get_measurement_history(limit=10)
        """
        query = """
            SELECT * FROM body_measurements
            ORDER BY date DESC
            LIMIT ?
        """
        results = self.db.execute(query, (limit,))
        return [self._row_to_measurement(row) for row in results]

    def get_weight_history(self, weeks_back: int = 12) -> list[dict]:
        """
        Get weight history for the specified time period.

        Args:
            weeks_back: Number of weeks to look back

        Returns:
            List of dicts with date, weight, and unit

        Example:
            >>> service.get_weight_history(weeks_back=12)
            [{'date': datetime(...), 'weight': Decimal('185.2'), 'unit': 'lbs'}, ...]
        """
        query = """
            SELECT date, weight, weight_unit
            FROM body_measurements
            WHERE weight IS NOT NULL
                AND date >= ?
            ORDER BY date ASC
        """
        cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
        results = self.db.execute(query, (cutoff_date,))

        return [
            {
                "date": row[0],
                "weight": Decimal(str(row[1])),
                "unit": row[2],
            }
            for row in results
        ]

    def get_measurement_trend(self, field: str, weeks_back: int = 12) -> list[dict]:
        """
        Get trend for a specific measurement field.

        Args:
            field: Measurement field name (e.g., 'waist', 'bicep_left', 'chest')
            weeks_back: Number of weeks to look back

        Returns:
            List of dicts with date, value, and unit

        Example:
            >>> service.get_measurement_trend('chest', weeks_back=12)
            [{'date': datetime(...), 'value': Decimal('42.5'), 'unit': 'in'}, ...]
        """
        # Validate field name to prevent SQL injection
        valid_fields = [
            "neck",
            "shoulders",
            "chest",
            "waist",
            "hips",
            "bicep_left",
            "bicep_right",
            "forearm_left",
            "forearm_right",
            "thigh_left",
            "thigh_right",
            "calf_left",
            "calf_right",
            "body_fat_pct",
        ]
        if field not in valid_fields:
            raise ValueError(f"Invalid measurement field: {field}")

        query = f"""
            SELECT date, {field}, measurement_unit
            FROM body_measurements
            WHERE {field} IS NOT NULL
                AND date >= ?
            ORDER BY date ASC
        """
        cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
        results = self.db.execute(query, (cutoff_date,))

        return [
            {
                "date": row[0],
                "value": Decimal(str(row[1])),
                "unit": row[2] if field != "body_fat_pct" else "%",
            }
            for row in results
        ]

    def compare_measurements(self, measurement1_id: int, measurement2_id: int) -> dict:
        """
        Compare two measurements and show differences.

        Args:
            measurement1_id: ID of first measurement (typically newer)
            measurement2_id: ID of second measurement (typically older)

        Returns:
            Dictionary with comparison data including differences and percent changes

        Example:
            >>> service.compare_measurements(10, 5)
            {
                'measurement1': BodyMeasurement(...),
                'measurement2': BodyMeasurement(...),
                'differences': {
                    'weight': {'change': Decimal('4.7'), 'percent': Decimal('2.6')},
                    ...
                }
            }
        """
        query = "SELECT * FROM body_measurements WHERE id = ?"

        result1 = self.db.execute(query, (measurement1_id,))
        result2 = self.db.execute(query, (measurement2_id,))

        if not result1 or not result2:
            raise ValueError("One or both measurements not found")

        m1 = self._row_to_measurement(result1[0])
        m2 = self._row_to_measurement(result2[0])

        differences = {}

        # Compare all numeric fields
        fields_to_compare = [
            ("weight", "weight"),
            ("body_fat_pct", "body_fat_pct"),
            ("neck", "neck"),
            ("shoulders", "shoulders"),
            ("chest", "chest"),
            ("waist", "waist"),
            ("hips", "hips"),
            ("bicep_left", "bicep_left"),
            ("bicep_right", "bicep_right"),
            ("forearm_left", "forearm_left"),
            ("forearm_right", "forearm_right"),
            ("thigh_left", "thigh_left"),
            ("thigh_right", "thigh_right"),
            ("calf_left", "calf_left"),
            ("calf_right", "calf_right"),
        ]

        for field_name, attr_name in fields_to_compare:
            val1 = getattr(m1, attr_name)
            val2 = getattr(m2, attr_name)

            if val1 is not None and val2 is not None:
                change = val1 - val2
                percent_change = (change / val2 * 100) if val2 != 0 else Decimal("0")

                differences[field_name] = {
                    "current": val1,
                    "previous": val2,
                    "change": change,
                    "percent": percent_change,
                }

        return {
            "measurement1": m1,
            "measurement2": m2,
            "differences": differences,
        }

    def get_progress_report(self, weeks_back: int = 4) -> dict:
        """
        Generate progress report comparing current vs X weeks ago.

        Args:
            weeks_back: Number of weeks to compare against

        Returns:
            Dictionary with current measurement, comparison measurement, and changes

        Example:
            >>> service.get_progress_report(weeks_back=4)
            {
                'current': BodyMeasurement(...),
                'previous': BodyMeasurement(...),
                'weeks_apart': 4,
                'differences': {...}
            }
        """
        latest = self.get_latest_measurement()
        if not latest:
            raise ValueError("No measurements found")

        # Find measurement closest to X weeks ago
        target_date = datetime.now() - timedelta(weeks=weeks_back)

        query = """
            SELECT * FROM body_measurements
            WHERE date <= ?
            ORDER BY date DESC
            LIMIT 1
        """
        result = self.db.execute(query, (target_date,))

        if not result:
            raise ValueError(f"No measurements found from {weeks_back} weeks ago")

        previous = self._row_to_measurement(result[0])

        # Calculate actual weeks apart
        days_apart = (latest.date - previous.date).days
        actual_weeks = days_apart / 7

        comparison = self.compare_measurements(latest.id, previous.id)

        return {
            "current": latest,
            "previous": previous,
            "weeks_apart": round(actual_weeks, 1),
            "differences": comparison["differences"],
        }

    def get_seven_day_average(self, field: str = "weight") -> Optional[Decimal]:
        """
        Get 7-day moving average for a field.

        Args:
            field: Field to average (default: weight)

        Returns:
            Average value or None if insufficient data

        Example:
            >>> service.get_seven_day_average("weight")
            Decimal('185.8')
        """
        if field not in [
            "weight",
            "body_fat_pct",
            "neck",
            "shoulders",
            "chest",
            "waist",
            "hips",
            "bicep_left",
            "bicep_right",
            "forearm_left",
            "forearm_right",
            "thigh_left",
            "thigh_right",
            "calf_left",
            "calf_right",
        ]:
            raise ValueError(f"Invalid field: {field}")

        query = f"""
            SELECT AVG({field}) as avg_value
            FROM body_measurements
            WHERE {field} IS NOT NULL
                AND date >= ?
        """
        cutoff_date = datetime.now() - timedelta(days=7)
        result = self.db.execute(query, (cutoff_date,))

        if result and result[0][0] is not None:
            return Decimal(str(result[0][0])).quantize(Decimal("0.1"))
        return None

    def _row_to_measurement(self, row: tuple) -> BodyMeasurement:
        """Convert database row to BodyMeasurement model."""
        return BodyMeasurement(
            id=row[0],
            date=row[1],
            weight=Decimal(str(row[2])) if row[2] is not None else None,
            weight_unit=WeightUnit(row[3]),
            body_fat_pct=Decimal(str(row[4])) if row[4] is not None else None,
            neck=Decimal(str(row[5])) if row[5] is not None else None,
            shoulders=Decimal(str(row[6])) if row[6] is not None else None,
            chest=Decimal(str(row[7])) if row[7] is not None else None,
            waist=Decimal(str(row[8])) if row[8] is not None else None,
            hips=Decimal(str(row[9])) if row[9] is not None else None,
            bicep_left=Decimal(str(row[10])) if row[10] is not None else None,
            bicep_right=Decimal(str(row[11])) if row[11] is not None else None,
            forearm_left=Decimal(str(row[12])) if row[12] is not None else None,
            forearm_right=Decimal(str(row[13])) if row[13] is not None else None,
            thigh_left=Decimal(str(row[14])) if row[14] is not None else None,
            thigh_right=Decimal(str(row[15])) if row[15] is not None else None,
            calf_left=Decimal(str(row[16])) if row[16] is not None else None,
            calf_right=Decimal(str(row[17])) if row[17] is not None else None,
            measurement_unit=MeasurementUnit(row[18]),
            notes=row[19],
        )
