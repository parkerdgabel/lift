"""Workout service for managing workout sessions."""

from decimal import Decimal
from typing import Any

from lift.core.database import DatabaseManager, get_db
from lift.core.models import Workout, WorkoutCreate, WorkoutUpdate


class WorkoutService:
    """Service for managing workout sessions."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """
        Initialize workout service.

        Args:
            db: Database manager instance. If None, uses global instance.
        """
        self.db = db or get_db()

    def create_workout(self, workout: WorkoutCreate) -> Workout:
        """
        Create a new workout session.

        Args:
            workout: Workout creation data

        Returns:
            Created workout

        Example:
            >>> service = WorkoutService()
            >>> workout = service.create_workout(WorkoutCreate(name="Push Day"))
        """
        query = """
            INSERT INTO workouts (
                date, program_workout_id, name, bodyweight,
                bodyweight_unit, notes, rating, completed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
        """

        with self.db.get_connection() as conn:
            result = conn.execute(
                query,
                (
                    workout.date,
                    workout.program_workout_id,
                    workout.name,
                    workout.bodyweight,
                    workout.bodyweight_unit.value if workout.bodyweight_unit else "lbs",
                    workout.notes,
                    workout.rating,
                    True,  # completed defaults to True
                ),
            ).fetchone()

            if not result:
                raise RuntimeError("Failed to create workout")

            return self._row_to_workout(result)

    def get_workout(self, id: int) -> Workout | None:
        """
        Get a workout by ID.

        Args:
            id: Workout ID

        Returns:
            Workout if found, None otherwise
        """
        query = "SELECT * FROM workouts WHERE id = ?"

        with self.db.get_connection() as conn:
            result = conn.execute(query, (id,)).fetchone()

            if not result:
                return None

            return self._row_to_workout(result)

    def get_recent_workouts(self, limit: int = 10) -> list[Workout]:
        """
        Get recent workouts ordered by date.

        Args:
            limit: Maximum number of workouts to return

        Returns:
            List of recent workouts
        """
        query = """
            SELECT * FROM workouts
            ORDER BY date DESC
            LIMIT ?
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query, (limit,)).fetchall()
            return [self._row_to_workout(row) for row in results]

    def get_last_workout(self) -> Workout | None:
        """
        Get the most recent workout.

        Returns:
            Most recent workout if exists, None otherwise
        """
        workouts = self.get_recent_workouts(limit=1)
        return workouts[0] if workouts else None

    def update_workout(self, id: int, update: WorkoutUpdate) -> Workout:
        """
        Update a workout.

        Args:
            id: Workout ID
            update: Update data

        Returns:
            Updated workout

        Raises:
            ValueError: If workout not found
        """
        # Build dynamic update query based on provided fields
        update_fields: list[str] = []
        params: list[Any] = []

        if update.name is not None:
            update_fields.append("name = ?")
            params.append(update.name)

        if update.duration_minutes is not None:
            update_fields.append("duration_minutes = ?")
            params.append(update.duration_minutes)

        if update.bodyweight is not None:
            update_fields.append("bodyweight = ?")
            params.append(update.bodyweight)

        if update.bodyweight_unit is not None:
            update_fields.append("bodyweight_unit = ?")
            params.append(update.bodyweight_unit.value)

        if update.notes is not None:
            update_fields.append("notes = ?")
            params.append(update.notes)

        if update.rating is not None:
            update_fields.append("rating = ?")
            params.append(update.rating)

        if update.completed is not None:
            update_fields.append("completed = ?")
            params.append(update.completed)

        if not update_fields:
            # No fields to update, just return existing workout
            existing = self.get_workout(id)
            if not existing:
                raise ValueError(f"Workout {id} not found")
            return existing

        params.append(id)
        # Note: DuckDB has issues with RETURNING clause when foreign keys reference the row
        # Use separate UPDATE and SELECT instead
        query = f"""
            UPDATE workouts
            SET {", ".join(update_fields)}
            WHERE id = ?
        """  # nosec B608  # update_fields built from validated model fields

        with self.db.get_connection() as conn:
            conn.execute(query, tuple(params))

            # Fetch the updated workout
            result = conn.execute("SELECT * FROM workouts WHERE id = ?", (id,)).fetchone()

            if not result:
                raise ValueError(f"Workout {id} not found")

            return self._row_to_workout(result)

    def delete_workout(self, id: int) -> bool:
        """
        Delete a workout and all associated sets.

        Args:
            id: Workout ID

        Returns:
            True if deleted, False if not found
        """
        with self.db.get_connection() as conn:
            # Delete related records first (DuckDB doesn't support CASCADE)
            conn.execute("DELETE FROM personal_records WHERE workout_id = ?", (id,))
            conn.execute("DELETE FROM sets WHERE workout_id = ?", (id,))
            # Now delete the workout
            conn.execute("DELETE FROM workouts WHERE id = ?", (id,))
            return True

    def finish_workout(self, id: int, duration_minutes: int) -> Workout:
        """
        Mark a workout as finished and set duration.

        Args:
            id: Workout ID
            duration_minutes: Duration in minutes

        Returns:
            Updated workout

        Raises:
            ValueError: If workout not found
        """
        return self.update_workout(
            id,
            WorkoutUpdate(
                duration_minutes=duration_minutes,
                completed=True,
                name=None,
                bodyweight=None,
                bodyweight_unit=None,
                notes=None,
                rating=None,
            ),
        )

    def get_workout_summary(self, id: int) -> dict:
        """
        Get comprehensive summary of a workout including volume and set statistics.

        Args:
            id: Workout ID

        Returns:
            Dictionary with summary statistics

        Example:
            >>> summary = service.get_workout_summary(1)
            >>> print(f"Total volume: {summary['total_volume']} lbs")
        """
        query = """
            SELECT
                COUNT(DISTINCT s.exercise_id) as exercise_count,
                COUNT(s.id) as total_sets,
                SUM(s.weight * s.reps) as total_volume,
                AVG(s.rpe) as avg_rpe,
                MAX(s.weight * s.reps) as max_set_volume
            FROM sets s
            WHERE s.workout_id = ?
              AND s.set_type IN ('working', 'dropset', 'failure', 'amrap')
        """

        with self.db.get_connection() as conn:
            result = conn.execute(query, (id,)).fetchone()

            if not result:
                return {
                    "total_exercises": 0,
                    "total_sets": 0,
                    "total_volume": Decimal("0"),
                    "avg_rpe": None,
                    "max_set_volume": Decimal("0"),
                }

            return {
                "total_exercises": result[0] or 0,
                "total_sets": result[1] or 0,
                "total_volume": Decimal(str(result[2])) if result[2] else Decimal("0"),
                "avg_rpe": Decimal(str(result[3])) if result[3] else None,
                "max_set_volume": (Decimal(str(result[4])) if result[4] else Decimal("0")),
            }

    def get_last_performance(self, exercise_id: int, limit: int = 1) -> list[dict]:
        """
        Get the last performance for an exercise (most recent sets).

        Args:
            exercise_id: Exercise ID
            limit: Number of most recent workouts to include

        Returns:
            List of dictionaries containing set data from recent workouts

        Example:
            >>> performance = service.get_last_performance(5, limit=1)
            >>> for set_data in performance:
            ...     print(f"{set_data['weight']} lbs x {set_data['reps']} reps")
        """
        query = """
            SELECT
                s.weight,
                s.weight_unit,
                s.reps,
                s.rpe,
                s.set_number,
                s.set_type,
                w.date,
                w.id as workout_id
            FROM sets s
            JOIN workouts w ON s.workout_id = w.id
            WHERE s.exercise_id = ?
            ORDER BY w.date DESC, s.set_number ASC
            LIMIT ?
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query, (exercise_id, limit * 10)).fetchall()

            performance = []
            for row in results:
                performance.append(
                    {
                        "weight": Decimal(str(row[0])),
                        "weight_unit": row[1],
                        "reps": row[2],
                        "rpe": Decimal(str(row[3])) if row[3] else None,
                        "set_number": row[4],
                        "set_type": row[5],
                        "workout_date": row[6],
                        "workout_id": row[7],
                    }
                )

            return performance

    def _row_to_workout(self, row: tuple) -> Workout:
        """
        Convert database row to Workout model.

        Args:
            row: Database row tuple

        Returns:
            Workout instance
        """
        from lift.core.models import WeightUnit

        return Workout(
            id=row[0],
            date=row[1],
            program_workout_id=row[2],
            name=row[3],
            duration_minutes=row[4],
            bodyweight=Decimal(str(row[5])) if row[5] else None,
            bodyweight_unit=WeightUnit(row[6]) if row[6] else WeightUnit.LBS,
            notes=row[7],
            rating=row[8],
            completed=bool(row[9]),
        )
