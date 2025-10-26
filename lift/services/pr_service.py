"""Personal Records (PR) service for tracking and detecting records."""

from datetime import datetime
from decimal import Decimal

from lift.core.database import DatabaseManager, get_db
from lift.core.models import PersonalRecord, PersonalRecordCreate, RecordType
from lift.utils.calculations import calculate_1rm


class PRService:
    """Service for managing personal records."""

    def __init__(self, db: DatabaseManager | None = None):
        """
        Initialize PR service.

        Args:
            db: Database manager instance. If None, uses global instance.
        """
        self.db = db or get_db()

    def auto_detect_prs(self, workout_id: int) -> list[PersonalRecord]:
        """
        Automatically detect personal records from a workout.

        Checks for:
        - 1RM, 3RM, 5RM, 10RM (rep maxes)
        - Volume PR (highest weight × reps for single set)
        - Max weight PR (heaviest weight lifted)

        Args:
            workout_id: ID of workout to check

        Returns:
            List of newly created personal records
        """
        # Get all working sets from the workout
        query = """
            SELECT
                s.id,
                s.exercise_id,
                s.weight,
                s.reps,
                s.rpe,
                s.weight_unit,
                e.name
            FROM sets s
            JOIN exercises e ON s.exercise_id = e.id
            WHERE s.workout_id = ?
                AND s.set_type IN ('working', 'dropset', 'failure', 'amrap')
            ORDER BY s.exercise_id, s.weight DESC, s.reps DESC
        """

        with self.db.get_connection() as conn:
            sets = conn.execute(query, (workout_id,)).fetchall()

        new_prs = []

        # Group sets by exercise
        exercise_sets: dict[int, list] = {}
        for set_data in sets:
            exercise_id = set_data[1]
            if exercise_id not in exercise_sets:
                exercise_sets[exercise_id] = []
            exercise_sets[exercise_id].append(set_data)

        # Check each exercise for PRs
        for exercise_id, ex_sets in exercise_sets.items():
            # Check rep maxes (1RM, 3RM, 5RM, 10RM)
            rep_targets = [1, 3, 5, 10]

            for target_reps in rep_targets:
                # Find best set matching this rep count
                matching_sets = [s for s in ex_sets if s[3] == target_reps]
                if matching_sets:
                    best_set = max(matching_sets, key=lambda x: x[2])  # Highest weight
                    weight = Decimal(str(best_set[2]))
                    reps = best_set[3]
                    weight_unit = best_set[5]

                    # Calculate estimated 1RM value
                    estimated_1rm = calculate_1rm(weight, reps)

                    # Determine record type
                    if target_reps == 1:
                        record_type = RecordType.ONE_RM
                    elif target_reps == 3:
                        record_type = RecordType.THREE_RM
                    elif target_reps == 5:
                        record_type = RecordType.FIVE_RM
                    elif target_reps == 10:
                        record_type = RecordType.TEN_RM

                    # Check if it's a new PR
                    if self.is_new_pr(exercise_id, record_type, estimated_1rm):
                        pr = self._create_pr_record(
                            exercise_id=exercise_id,
                            record_type=record_type,
                            value=estimated_1rm,
                            reps=reps,
                            weight=weight,
                            weight_unit=weight_unit,
                            workout_id=workout_id,
                            set_id=best_set[0],
                        )
                        new_prs.append(pr)

            # Check volume PR (highest weight × reps for single set)
            volume_sets = [(s[2] * s[3], s) for s in ex_sets]
            if volume_sets:
                best_volume_set = max(volume_sets, key=lambda x: x[0])[1]
                volume = Decimal(str(best_volume_set[2])) * Decimal(best_volume_set[3])

                if self.is_new_pr(exercise_id, RecordType.VOLUME, volume):
                    pr = self._create_pr_record(
                        exercise_id=exercise_id,
                        record_type=RecordType.VOLUME,
                        value=volume,
                        reps=best_volume_set[3],
                        weight=Decimal(str(best_volume_set[2])),
                        weight_unit=best_volume_set[5],
                        workout_id=workout_id,
                        set_id=best_volume_set[0],
                    )
                    new_prs.append(pr)

            # Check max weight PR
            max_weight_set = max(ex_sets, key=lambda x: x[2])
            max_weight = Decimal(str(max_weight_set[2]))

            if self.is_new_pr(exercise_id, RecordType.MAX_WEIGHT, max_weight):
                pr = self._create_pr_record(
                    exercise_id=exercise_id,
                    record_type=RecordType.MAX_WEIGHT,
                    value=max_weight,
                    reps=max_weight_set[3],
                    weight=max_weight,
                    weight_unit=max_weight_set[5],
                    workout_id=workout_id,
                    set_id=max_weight_set[0],
                )
                new_prs.append(pr)

        return new_prs

    def _create_pr_record(
        self,
        exercise_id: int,
        record_type: RecordType,
        value: Decimal,
        reps: int,
        weight: Decimal,
        weight_unit: str,
        workout_id: int,
        set_id: int,
    ) -> PersonalRecord:
        """
        Internal method to create a PR record.

        Args:
            exercise_id: Exercise ID
            record_type: Type of record
            value: Record value
            reps: Number of reps
            weight: Weight used
            weight_unit: Weight unit
            workout_id: Workout ID
            set_id: Set ID

        Returns:
            Created PersonalRecord
        """
        from lift.core.models import WeightUnit

        pr_create = PersonalRecordCreate(
            exercise_id=exercise_id,
            record_type=record_type,
            value=value,
            reps=reps,
            weight=weight,
            weight_unit=WeightUnit(weight_unit),
            workout_id=workout_id,
            set_id=set_id,
            date=datetime.now(),
        )

        return self.create_pr(pr_create)

    def get_all_prs(self, exercise_id: int | None = None) -> list[PersonalRecord]:
        """
        Get all personal records.

        Args:
            exercise_id: Optional exercise ID to filter by

        Returns:
            List of personal records
        """
        query = """
            SELECT
                pr.id,
                pr.exercise_id,
                pr.record_type,
                pr.value,
                pr.reps,
                pr.weight,
                pr.weight_unit,
                pr.date,
                pr.workout_id,
                pr.set_id
            FROM personal_records pr
        """

        params = []
        if exercise_id is not None:
            query += " WHERE pr.exercise_id = ?"
            params.append(exercise_id)

        query += " ORDER BY pr.date DESC"

        with self.db.get_connection() as conn:
            results = conn.execute(query, params).fetchall()

        prs = []
        for row in results:
            pr = PersonalRecord(
                id=row[0],
                exercise_id=row[1],
                record_type=RecordType(row[2]),
                value=Decimal(str(row[3])),
                reps=row[4],
                weight=Decimal(str(row[5])) if row[5] else None,
                weight_unit=row[6],
                date=row[7],
                workout_id=row[8],
                set_id=row[9],
            )
            prs.append(pr)

        return prs

    def get_pr_by_type(self, exercise_id: int, record_type: RecordType) -> PersonalRecord | None:
        """
        Get the current PR for a specific exercise and record type.

        Args:
            exercise_id: Exercise ID
            record_type: Type of record

        Returns:
            PersonalRecord if exists, None otherwise
        """
        query = """
            SELECT
                pr.id,
                pr.exercise_id,
                pr.record_type,
                pr.value,
                pr.reps,
                pr.weight,
                pr.weight_unit,
                pr.date,
                pr.workout_id,
                pr.set_id
            FROM personal_records pr
            WHERE pr.exercise_id = ?
                AND pr.record_type = ?
            ORDER BY pr.value DESC, pr.date DESC
            LIMIT 1
        """

        with self.db.get_connection() as conn:
            result = conn.execute(query, (exercise_id, record_type.value)).fetchone()

        if not result:
            return None

        return PersonalRecord(
            id=result[0],
            exercise_id=result[1],
            record_type=RecordType(result[2]),
            value=Decimal(str(result[3])),
            reps=result[4],
            weight=Decimal(str(result[5])) if result[5] else None,
            weight_unit=result[6],
            date=result[7],
            workout_id=result[8],
            set_id=result[9],
        )

    def create_pr(self, pr: PersonalRecordCreate) -> PersonalRecord:
        """
        Create a new personal record.

        Args:
            pr: PersonalRecordCreate model

        Returns:
            Created PersonalRecord
        """
        query = """
            INSERT INTO personal_records (
                exercise_id,
                record_type,
                value,
                reps,
                weight,
                weight_unit,
                date,
                workout_id,
                set_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
        """

        with self.db.get_connection() as conn:
            result = conn.execute(
                query,
                (
                    pr.exercise_id,
                    pr.record_type.value,
                    float(pr.value),
                    pr.reps,
                    float(pr.weight) if pr.weight else None,
                    pr.weight_unit.value,
                    pr.date,
                    pr.workout_id,
                    pr.set_id,
                ),
            ).fetchone()

        if not result:
            raise RuntimeError("Failed to create personal record")

        return PersonalRecord(
            id=result[0],
            exercise_id=result[1],
            record_type=RecordType(result[2]),
            value=Decimal(str(result[3])),
            reps=result[4],
            weight=Decimal(str(result[5])) if result[5] else None,
            weight_unit=result[6],
            date=result[7],
            workout_id=result[8],
            set_id=result[9],
        )

    def is_new_pr(self, exercise_id: int, record_type: RecordType, value: Decimal) -> bool:
        """
        Check if a value represents a new personal record.

        Args:
            exercise_id: Exercise ID
            record_type: Type of record
            value: Value to check

        Returns:
            True if this is a new PR, False otherwise
        """
        current_pr = self.get_pr_by_type(exercise_id, record_type)

        if current_pr is None:
            return True

        return value > current_pr.value

    def get_pr_summary(self, exercise_id: int) -> dict:
        """
        Get summary of all PRs for an exercise.

        Args:
            exercise_id: Exercise ID

        Returns:
            Dictionary with PR summary data
        """
        query = """
            SELECT
                pr.record_type,
                pr.value,
                pr.weight,
                pr.reps,
                pr.date,
                pr.weight_unit
            FROM personal_records pr
            WHERE pr.exercise_id = ?
            ORDER BY pr.record_type, pr.value DESC
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query, (exercise_id,)).fetchall()

        # Get best of each type
        pr_summary = {}
        seen_types = set()

        for row in results:
            record_type = row[0]
            if record_type not in seen_types:
                pr_summary[record_type] = {
                    "value": Decimal(str(row[1])),
                    "weight": Decimal(str(row[2])) if row[2] else None,
                    "reps": row[3],
                    "date": row[4],
                    "weight_unit": row[5],
                }
                seen_types.add(record_type)

        return pr_summary

    def get_recent_prs(self, days: int = 30, limit: int = 10) -> list[dict]:
        """
        Get recently set personal records.

        Args:
            days: Number of days to look back
            limit: Maximum number of PRs to return

        Returns:
            List of recent PRs with exercise info
        """
        query = f"""
            SELECT
                e.name as exercise_name,
                pr.record_type,
                pr.value,
                pr.weight,
                pr.reps,
                pr.date,
                pr.weight_unit
            FROM personal_records pr
            JOIN exercises e ON pr.exercise_id = e.id
            WHERE pr.date >= CURRENT_TIMESTAMP - INTERVAL '{days} DAY'
            ORDER BY pr.date DESC
            LIMIT ?
        """  # nosec B608  # days is integer parameter

        with self.db.get_connection() as conn:
            results = conn.execute(query, (limit,)).fetchall()

        return [
            {
                "exercise_name": row[0],
                "record_type": row[1],
                "value": Decimal(str(row[2])),
                "weight": Decimal(str(row[3])) if row[3] else None,
                "reps": row[4],
                "date": row[5],
                "weight_unit": row[6],
            }
            for row in results
        ]

    def delete_pr(self, pr_id: int) -> bool:
        """
        Delete a personal record.

        Args:
            pr_id: PR ID to delete

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM personal_records WHERE id = ? RETURNING id"

        with self.db.get_connection() as conn:
            result = conn.execute(query, (pr_id,)).fetchone()
            return result is not None

    def get_pr_history(self, exercise_id: int, record_type: RecordType) -> list[PersonalRecord]:
        """
        Get historical progression of a specific PR type.

        Args:
            exercise_id: Exercise ID
            record_type: Type of record

        Returns:
            List of all PRs for this type, ordered by date
        """
        query = """
            SELECT
                pr.id,
                pr.exercise_id,
                pr.record_type,
                pr.value,
                pr.reps,
                pr.weight,
                pr.weight_unit,
                pr.date,
                pr.workout_id,
                pr.set_id
            FROM personal_records pr
            WHERE pr.exercise_id = ?
                AND pr.record_type = ?
            ORDER BY pr.date ASC
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query, (exercise_id, record_type.value)).fetchall()

        return [
            PersonalRecord(
                id=row[0],
                exercise_id=row[1],
                record_type=RecordType(row[2]),
                value=Decimal(str(row[3])),
                reps=row[4],
                weight=Decimal(str(row[5])) if row[5] else None,
                weight_unit=row[6],
                date=row[7],
                workout_id=row[8],
                set_id=row[9],
            )
            for row in results
        ]
