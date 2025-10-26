"""Statistics and analytics service for workout data."""

from datetime import datetime
from decimal import Decimal

from lift.core.database import DatabaseManager, get_db
from lift.core.models import PeriodWorkoutSummary


class StatsService:
    """Service for calculating workout statistics and analytics."""

    def __init__(self, db: DatabaseManager | None = None):
        """
        Initialize stats service.

        Args:
            db: Database manager instance. If None, uses global instance.
        """
        self.db = db or get_db()

    def get_workout_summary(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> PeriodWorkoutSummary:
        """
        Get overall workout summary statistics.

        Args:
            start_date: Start date for summary (optional)
            end_date: End date for summary (optional)

        Returns:
            PeriodWorkoutSummary model with summary statistics:
            - total_workouts: Number of workouts
            - total_volume: Total volume load
            - total_sets: Total number of sets
            - avg_duration: Average workout duration
            - avg_rpe: Average RPE
            - total_exercises: Number of unique exercises
        """
        query = """
            SELECT
                COUNT(DISTINCT w.id) as total_workouts,
                COALESCE(SUM(s.weight * s.reps), 0) as total_volume,
                COUNT(s.id) as total_sets,
                COALESCE(AVG(w.duration_minutes), 0) as avg_duration,
                COALESCE(AVG(s.rpe), 0) as avg_rpe,
                COUNT(DISTINCT s.exercise_id) as total_exercises
            FROM workouts w
            LEFT JOIN sets s ON w.id = s.workout_id
            WHERE s.set_type IN ('working', 'dropset', 'failure', 'amrap')
        """

        params = []
        if start_date:
            query += " AND w.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND w.date <= ?"
            params.append(end_date)

        with self.db.get_connection() as conn:
            result = conn.execute(query, params).fetchone()

        if not result:
            return PeriodWorkoutSummary()

        return PeriodWorkoutSummary(
            total_workouts=result[0],
            total_volume=Decimal(str(result[1])) if result[1] else Decimal(0),
            total_sets=result[2],
            avg_duration=round(result[3], 1) if result[3] else 0,
            avg_rpe=Decimal(str(result[4])).quantize(Decimal("0.1")) if result[4] else Decimal(0),
            total_exercises=result[5],
        )

    def get_weekly_summary(self, weeks_back: int = 4) -> list[dict]:
        """
        Get per-week breakdown of training statistics.

        Args:
            weeks_back: Number of weeks to look back

        Returns:
            List of weekly summaries with:
            - week_start: Start date of week
            - workouts: Number of workouts
            - total_volume: Total volume for week
            - total_sets: Total sets for week
            - avg_rpe: Average RPE for week
            - avg_duration: Average duration
        """
        query = f"""
            SELECT
                date_trunc('week', w.date) as week_start,
                COUNT(DISTINCT w.id) as workouts,
                COALESCE(SUM(s.weight * s.reps), 0) as total_volume,
                COUNT(s.id) as total_sets,
                COALESCE(AVG(s.rpe), 0) as avg_rpe,
                COALESCE(AVG(w.duration_minutes), 0) as avg_duration
            FROM workouts w
            LEFT JOIN sets s ON w.id = s.workout_id
            WHERE w.date >= CURRENT_TIMESTAMP - INTERVAL '{weeks_back} WEEK'
                AND s.set_type IN ('working', 'dropset', 'failure', 'amrap')
            GROUP BY date_trunc('week', w.date)
            ORDER BY week_start DESC
        """  # nosec B608  # weeks_back is integer parameter

        with self.db.get_connection() as conn:
            results = conn.execute(query).fetchall()

        summaries = []
        for row in results:
            summaries.append(
                {
                    "week_start": row[0],
                    "workouts": row[1],
                    "total_volume": Decimal(str(row[2])) if row[2] else Decimal(0),
                    "total_sets": row[3],
                    "avg_rpe": Decimal(str(row[4])).quantize(Decimal("0.1"))
                    if row[4]
                    else Decimal(0),
                    "avg_duration": round(row[5], 1) if row[5] else 0,
                }
            )

        return summaries

    def get_monthly_summary(self, months_back: int = 3) -> list[dict]:
        """
        Get per-month breakdown of training statistics.

        Args:
            months_back: Number of months to look back

        Returns:
            List of monthly summaries
        """
        query = f"""
            SELECT
                date_trunc('month', w.date) as month_start,
                COUNT(DISTINCT w.id) as workouts,
                COALESCE(SUM(s.weight * s.reps), 0) as total_volume,
                COUNT(s.id) as total_sets,
                COALESCE(AVG(s.rpe), 0) as avg_rpe,
                COALESCE(AVG(w.duration_minutes), 0) as avg_duration
            FROM workouts w
            LEFT JOIN sets s ON w.id = s.workout_id
            WHERE w.date >= CURRENT_TIMESTAMP - INTERVAL '{months_back} MONTH'
                AND s.set_type IN ('working', 'dropset', 'failure', 'amrap')
            GROUP BY date_trunc('month', w.date)
            ORDER BY month_start DESC
        """  # nosec B608  # months_back is integer parameter

        with self.db.get_connection() as conn:
            results = conn.execute(query).fetchall()

        summaries = []
        for row in results:
            summaries.append(
                {
                    "month_start": row[0],
                    "workouts": row[1],
                    "total_volume": Decimal(str(row[2])) if row[2] else Decimal(0),
                    "total_sets": row[3],
                    "avg_rpe": Decimal(str(row[4])).quantize(Decimal("0.1"))
                    if row[4]
                    else Decimal(0),
                    "avg_duration": round(row[5], 1) if row[5] else 0,
                }
            )

        return summaries

    def get_muscle_volume_breakdown(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> dict[str, Decimal]:
        """
        Get volume breakdown by muscle group.

        Args:
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            Dictionary mapping muscle group to total volume
        """
        query = """
            SELECT
                e.primary_muscle,
                COALESCE(SUM(s.weight * s.reps), 0) as total_volume
            FROM sets s
            JOIN exercises e ON s.exercise_id = e.id
            JOIN workouts w ON s.workout_id = w.id
            WHERE s.set_type IN ('working', 'dropset', 'failure', 'amrap')
        """

        params = []
        if start_date:
            query += " AND w.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND w.date <= ?"
            params.append(end_date)

        query += " GROUP BY e.primary_muscle ORDER BY total_volume DESC"

        with self.db.get_connection() as conn:
            results = conn.execute(query, params).fetchall()

        return {row[0]: Decimal(str(row[1])) for row in results}

    def get_training_frequency(self, weeks_back: int = 12) -> list[dict]:
        """
        Get training frequency (workouts per week).

        Args:
            weeks_back: Number of weeks to analyze

        Returns:
            List of dictionaries with week_start and workout_count
        """
        query = f"""
            SELECT
                date_trunc('week', date) as week_start,
                COUNT(*) as workout_count,
                SUM(duration_minutes) as total_minutes,
                AVG(duration_minutes) as avg_duration
            FROM workouts
            WHERE date >= CURRENT_TIMESTAMP - INTERVAL '{weeks_back} WEEK'
            GROUP BY date_trunc('week', date)
            ORDER BY week_start DESC
        """  # nosec B608  # weeks_back is integer parameter

        with self.db.get_connection() as conn:
            results = conn.execute(query).fetchall()

        return [
            {
                "week_start": row[0],
                "workout_count": row[1],
                "total_minutes": row[2] or 0,
                "avg_duration": round(row[3], 1) if row[3] else 0,
            }
            for row in results
        ]

    def get_exercise_progression(self, exercise_id: int, limit: int = 10) -> list[dict]:
        """
        Get historical progression for a specific exercise.

        Args:
            exercise_id: Exercise ID
            limit: Number of recent workouts to include

        Returns:
            List of progression data points with:
            - date: Workout date
            - weight: Weight used
            - reps: Reps performed
            - rpe: RPE rating
            - volume: Set volume
            - estimated_1rm: Estimated 1RM
        """
        query = """
            SELECT
                w.date,
                s.weight,
                s.reps,
                s.rpe,
                s.weight * s.reps as volume,
                CASE
                    WHEN s.reps = 1 THEN s.weight
                    ELSE s.weight * (1 + s.reps / 30.0)
                END as estimated_1rm
            FROM sets s
            JOIN workouts w ON s.workout_id = w.id
            WHERE s.exercise_id = ?
                AND s.set_type IN ('working', 'dropset', 'failure', 'amrap')
            ORDER BY w.date DESC, s.weight DESC, s.reps DESC
            LIMIT ?
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query, (exercise_id, limit)).fetchall()

        return [
            {
                "date": row[0],
                "weight": Decimal(str(row[1])),
                "reps": row[2],
                "rpe": Decimal(str(row[3])).quantize(Decimal("0.1")) if row[3] else None,
                "volume": Decimal(str(row[4])),
                "estimated_1rm": Decimal(str(row[5])).quantize(Decimal("0.1")),
            }
            for row in results
        ]

    def calculate_consistency_streak(self) -> int:
        """
        Calculate current training consistency streak in days.

        A streak is broken if no workout for 3+ consecutive days.

        Returns:
            Number of consecutive days with consistent training
        """
        query = """
            SELECT date
            FROM workouts
            ORDER BY date DESC
            LIMIT 100
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query).fetchall()

        if not results:
            return 0

        dates = [row[0] for row in results]
        today = datetime.now().date()

        # Check if last workout was within 3 days
        if isinstance(dates[0], datetime):
            last_workout = dates[0].date()
        else:
            last_workout = dates[0]

        if (today - last_workout).days > 3:
            return 0

        # Count consecutive training days
        streak_days = 1
        for i in range(len(dates) - 1):
            current = dates[i].date() if isinstance(dates[i], datetime) else dates[i]
            next_date = dates[i + 1].date() if isinstance(dates[i + 1], datetime) else dates[i + 1]

            gap = (current - next_date).days

            if gap <= 3:  # Allow up to 3 days between workouts
                streak_days += gap
            else:
                break

        return streak_days

    def get_volume_trends(self, weeks_back: int = 12) -> list[dict]:
        """
        Get weekly volume trends over time.

        Args:
            weeks_back: Number of weeks to analyze

        Returns:
            List of weekly volume data with:
            - week_start: Start of week
            - total_volume: Total volume for week
            - avg_volume_per_workout: Average volume per workout
            - workout_count: Number of workouts
        """
        query = f"""
            SELECT
                date_trunc('week', w.date) as week_start,
                COALESCE(SUM(s.weight * s.reps), 0) as total_volume,
                COUNT(DISTINCT w.id) as workout_count
            FROM workouts w
            LEFT JOIN sets s ON w.id = s.workout_id
            WHERE w.date >= CURRENT_TIMESTAMP - INTERVAL '{weeks_back} WEEK'
                AND s.set_type IN ('working', 'dropset', 'failure', 'amrap')
            GROUP BY date_trunc('week', w.date)
            ORDER BY week_start DESC
        """  # nosec B608  # weeks_back is integer parameter

        with self.db.get_connection() as conn:
            results = conn.execute(query).fetchall()

        trends = []
        for row in results:
            total_volume = Decimal(str(row[1])) if row[1] else Decimal(0)
            workout_count = row[2] or 1
            avg_volume = total_volume / Decimal(workout_count) if workout_count > 0 else Decimal(0)

            trends.append(
                {
                    "week_start": row[0],
                    "total_volume": total_volume,
                    "avg_volume_per_workout": avg_volume.quantize(Decimal("0.1")),
                    "workout_count": workout_count,
                }
            )

        return trends

    def get_set_distribution(self, weeks_back: int = 4) -> dict[str, int]:
        """
        Get distribution of sets by muscle group.

        Args:
            weeks_back: Number of weeks to analyze

        Returns:
            Dictionary mapping muscle group to set count
        """
        query = f"""
            SELECT
                e.primary_muscle,
                COUNT(s.id) as set_count
            FROM sets s
            JOIN exercises e ON s.exercise_id = e.id
            JOIN workouts w ON s.workout_id = w.id
            WHERE w.date >= CURRENT_TIMESTAMP - INTERVAL '{weeks_back} WEEK'
                AND s.set_type IN ('working', 'dropset', 'failure', 'amrap')
            GROUP BY e.primary_muscle
            ORDER BY set_count DESC
        """  # nosec B608  # weeks_back is integer parameter

        with self.db.get_connection() as conn:
            results = conn.execute(query).fetchall()

        return {row[0]: row[1] for row in results}

    def get_personal_records_count(self) -> dict[str, int]:
        """
        Get count of personal records by type.

        Returns:
            Dictionary mapping record type to count
        """
        query = """
            SELECT record_type, COUNT(*) as count
            FROM personal_records
            GROUP BY record_type
            ORDER BY count DESC
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query).fetchall()

        return {row[0]: row[1] for row in results}

    def get_exercise_volume_leaders(self, limit: int = 5, weeks_back: int = 4) -> list[dict]:
        """
        Get exercises with highest volume in recent weeks.

        Args:
            limit: Number of exercises to return
            weeks_back: Number of weeks to analyze

        Returns:
            List of exercises with volume data
        """
        query = f"""
            SELECT
                e.name,
                COALESCE(SUM(s.weight * s.reps), 0) as total_volume,
                COUNT(s.id) as set_count,
                AVG(s.weight) as avg_weight
            FROM sets s
            JOIN exercises e ON s.exercise_id = e.id
            JOIN workouts w ON s.workout_id = w.id
            WHERE w.date >= CURRENT_TIMESTAMP - INTERVAL '{weeks_back} WEEK'
                AND s.set_type IN ('working', 'dropset', 'failure', 'amrap')
            GROUP BY e.name
            ORDER BY total_volume DESC
            LIMIT ?
        """  # nosec B608  # weeks_back is integer parameter

        with self.db.get_connection() as conn:
            results = conn.execute(query, (limit,)).fetchall()

        return [
            {
                "exercise": row[0],
                "total_volume": Decimal(str(row[1])),
                "set_count": row[2],
                "avg_weight": Decimal(str(row[3])).quantize(Decimal("0.1")),
            }
            for row in results
        ]
