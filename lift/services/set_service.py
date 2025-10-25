"""Set service for managing workout sets."""

from datetime import datetime
from decimal import Decimal

from lift.core.database import DatabaseManager, get_db
from lift.core.models import Set, SetCreate


class SetService:
    """Service for managing workout sets."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """
        Initialize set service.

        Args:
            db: Database manager instance. If None, uses global instance.
        """
        self.db = db or get_db()

    def add_set(self, set_data: SetCreate) -> Set:
        """
        Add a new set to a workout.

        Args:
            set_data: Set creation data

        Returns:
            Created set

        Example:
            >>> service = SetService()
            >>> set_obj = service.add_set(SetCreate(
            ...     workout_id=1,
            ...     exercise_id=5,
            ...     set_number=1,
            ...     weight=Decimal("185"),
            ...     reps=10
            ... ))
        """
        query = """
            INSERT INTO sets (
                workout_id, exercise_id, set_number, weight, weight_unit,
                reps, rpe, tempo, set_type, rest_seconds,
                is_superset, superset_group, notes, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
        """

        with self.db.get_connection() as conn:
            result = conn.execute(
                query,
                (
                    set_data.workout_id,
                    set_data.exercise_id,
                    set_data.set_number,
                    set_data.weight,
                    set_data.weight_unit.value if set_data.weight_unit else "lbs",
                    set_data.reps,
                    set_data.rpe,
                    set_data.tempo,
                    set_data.set_type.value if set_data.set_type else "working",
                    set_data.rest_seconds,
                    set_data.is_superset,
                    set_data.superset_group,
                    set_data.notes,
                    datetime.now(),
                ),
            ).fetchone()

            if not result:
                raise RuntimeError("Failed to create set")

            return self._row_to_set(result)

    def get_sets_for_workout(self, workout_id: int) -> list[Set]:
        """
        Get all sets for a workout.

        Args:
            workout_id: Workout ID

        Returns:
            List of sets ordered by completion time
        """
        query = """
            SELECT * FROM sets
            WHERE workout_id = ?
            ORDER BY completed_at ASC, set_number ASC
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query, (workout_id,)).fetchall()
            return [self._row_to_set(row) for row in results]

    def get_sets_for_exercise(self, exercise_id: int, limit: int = 50) -> list[Set]:
        """
        Get recent sets for an exercise across all workouts.

        Args:
            exercise_id: Exercise ID
            limit: Maximum number of sets to return

        Returns:
            List of sets ordered by completion time (most recent first)
        """
        query = """
            SELECT * FROM sets
            WHERE exercise_id = ?
            ORDER BY completed_at DESC
            LIMIT ?
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query, (exercise_id, limit)).fetchall()
            return [self._row_to_set(row) for row in results]

    def delete_set(self, id: int) -> bool:
        """
        Delete a set.

        Args:
            id: Set ID

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM sets WHERE id = ?"

        with self.db.get_connection() as conn:
            conn.execute(query, (id,))
            return True

    def calculate_volume(self, sets: list[Set]) -> Decimal:
        """
        Calculate total volume (weight × reps) for a list of sets.

        Args:
            sets: List of sets

        Returns:
            Total volume

        Example:
            >>> sets = service.get_sets_for_workout(1)
            >>> volume = service.calculate_volume(sets)
            >>> print(f"Total volume: {volume} lbs")
        """
        total_volume = Decimal("0")

        for set_obj in sets:
            # Only count working sets for volume
            if set_obj.set_type.value in (
                "working",
                "dropset",
                "failure",
                "amrap",
            ):
                total_volume += set_obj.weight * set_obj.reps

        return total_volume

    def calculate_estimated_1rm(self, weight: Decimal, reps: int) -> Decimal:
        """
        Calculate estimated 1 rep max using Epley formula.

        Formula: 1RM = weight × (1 + reps/30)

        Args:
            weight: Weight lifted
            reps: Number of reps

        Returns:
            Estimated 1RM

        Example:
            >>> estimated_1rm = service.calculate_estimated_1rm(Decimal("225"), 5)
            >>> print(f"Estimated 1RM: {estimated_1rm} lbs")
        """
        if reps == 1:
            return weight

        # Epley formula: 1RM = weight × (1 + reps/30)
        from decimal import ROUND_HALF_UP

        result = weight * (1 + Decimal(reps) / Decimal("30"))
        # Round to 1 decimal place for weights
        return result.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    def get_next_set_number(self, workout_id: int, exercise_id: int) -> int:
        """
        Get the next set number for an exercise in a workout.

        Args:
            workout_id: Workout ID
            exercise_id: Exercise ID

        Returns:
            Next set number (starting from 1)
        """
        query = """
            SELECT MAX(set_number) FROM sets
            WHERE workout_id = ? AND exercise_id = ?
        """

        with self.db.get_connection() as conn:
            result = conn.execute(query, (workout_id, exercise_id)).fetchone()
            max_set = result[0] if result and result[0] else 0
            return max_set + 1

    def get_last_set_for_exercise_in_workout(self, workout_id: int, exercise_id: int) -> Set | None:
        """
        Get the most recent set for an exercise in a workout.

        Args:
            workout_id: Workout ID
            exercise_id: Exercise ID

        Returns:
            Most recent set if exists, None otherwise
        """
        query = """
            SELECT * FROM sets
            WHERE workout_id = ? AND exercise_id = ?
            ORDER BY set_number DESC
            LIMIT 1
        """

        with self.db.get_connection() as conn:
            result = conn.execute(query, (workout_id, exercise_id)).fetchone()

            if not result:
                return None

            return self._row_to_set(result)

    def _row_to_set(self, row: tuple) -> Set:
        """
        Convert database row to Set model.

        Args:
            row: Database row tuple

        Returns:
            Set instance
        """
        from lift.core.models import SetType, WeightUnit

        return Set(
            id=row[0],
            workout_id=row[1],
            exercise_id=row[2],
            set_number=row[3],
            weight=Decimal(str(row[4])),
            weight_unit=WeightUnit(row[5]) if row[5] else WeightUnit.LBS,
            reps=row[6],
            rpe=Decimal(str(row[7])) if row[7] else None,
            tempo=row[8],
            set_type=SetType(row[9]) if row[9] else SetType.WORKING,
            rest_seconds=row[10],
            is_superset=bool(row[11]) if row[11] is not None else False,
            superset_group=row[12],
            notes=row[13],
            completed_at=row[14],
        )
