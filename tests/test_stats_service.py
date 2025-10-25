"""Tests for stats service."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from lift.core.database import DatabaseManager
from lift.services.stats_service import StatsService


@pytest.fixture()
def db() -> DatabaseManager:
    """Create a test database."""
    db = DatabaseManager(":memory:")
    db.initialize_database()
    return db


@pytest.fixture()
def stats_service(db: DatabaseManager) -> StatsService:
    """Create stats service with test database."""
    return StatsService(db)


@pytest.fixture()
def sample_data(db: DatabaseManager) -> dict:
    """Create sample workout data for testing."""
    with db.get_connection() as conn:
        # Create exercise
        conn.execute(
            """
            INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
            VALUES ('Bench Press', 'Push', 'Chest', 'Barbell', 'Compound')
        """
        )
        exercise_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Create workout
        workout_date = datetime.now() - timedelta(days=1)
        conn.execute(
            """
            INSERT INTO workouts (date, name, duration_minutes, completed)
            VALUES (?, 'Push Day', 60, TRUE)
        """,
            (workout_date,),
        )
        workout_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Create sets
        sets_data = [
            (workout_id, exercise_id, 1, 225, 8, 8.0, "working"),
            (workout_id, exercise_id, 2, 225, 8, 8.5, "working"),
            (workout_id, exercise_id, 3, 225, 7, 9.0, "working"),
        ]

        for set_data in sets_data:
            conn.execute(
                """
                INSERT INTO sets (
                    workout_id, exercise_id, set_number, weight, reps, rpe, set_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                set_data,
            )

    return {
        "exercise_id": exercise_id,
        "workout_id": workout_id,
        "workout_date": workout_date,
    }


def test_get_workout_summary(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting workout summary."""
    summary = stats_service.get_workout_summary()

    assert summary["total_workouts"] == 1
    assert summary["total_sets"] == 3
    assert summary["total_volume"] > 0
    assert summary["avg_duration"] == 60
    assert summary["total_exercises"] == 1


def test_get_workout_summary_with_date_range(
    stats_service: StatsService, sample_data: dict
) -> None:
    """Test getting workout summary with date filter."""
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()

    summary = stats_service.get_workout_summary(start_date=start_date, end_date=end_date)

    assert summary["total_workouts"] == 1


def test_get_workout_summary_empty(stats_service: StatsService) -> None:
    """Test getting workout summary with no data."""
    summary = stats_service.get_workout_summary()

    assert summary["total_workouts"] == 0
    assert summary["total_volume"] == Decimal(0)


def test_get_weekly_summary(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting weekly summary."""
    weekly = stats_service.get_weekly_summary(weeks_back=4)

    assert len(weekly) > 0
    assert "week_start" in weekly[0]
    assert "workouts" in weekly[0]
    assert "total_volume" in weekly[0]


def test_get_monthly_summary(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting monthly summary."""
    monthly = stats_service.get_monthly_summary(months_back=3)

    assert len(monthly) > 0
    assert "month_start" in monthly[0]
    assert "workouts" in monthly[0]


def test_get_muscle_volume_breakdown(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting muscle volume breakdown."""
    breakdown = stats_service.get_muscle_volume_breakdown()

    assert "Chest" in breakdown
    assert breakdown["Chest"] > 0


def test_get_training_frequency(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting training frequency."""
    frequency = stats_service.get_training_frequency(weeks_back=12)

    assert len(frequency) > 0
    assert "week_start" in frequency[0]
    assert "workout_count" in frequency[0]


def test_get_exercise_progression(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting exercise progression."""
    progression = stats_service.get_exercise_progression(sample_data["exercise_id"], limit=10)

    assert len(progression) == 3  # 3 sets
    assert "weight" in progression[0]
    assert "reps" in progression[0]
    assert "estimated_1rm" in progression[0]


def test_calculate_consistency_streak_active(
    stats_service: StatsService, sample_data: dict
) -> None:
    """Test calculating consistency streak with recent workout."""
    streak = stats_service.calculate_consistency_streak()

    assert streak >= 1


def test_calculate_consistency_streak_empty(stats_service: StatsService) -> None:
    """Test calculating consistency streak with no data."""
    streak = stats_service.calculate_consistency_streak()

    assert streak == 0


def test_get_volume_trends(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting volume trends."""
    trends = stats_service.get_volume_trends(weeks_back=12)

    assert len(trends) > 0
    assert "week_start" in trends[0]
    assert "total_volume" in trends[0]
    assert "workout_count" in trends[0]


def test_get_set_distribution(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting set distribution."""
    distribution = stats_service.get_set_distribution(weeks_back=4)

    assert "Chest" in distribution
    assert distribution["Chest"] == 3


def test_get_personal_records_count(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting PR counts."""
    counts = stats_service.get_personal_records_count()

    # Should be empty initially
    assert isinstance(counts, dict)


def test_get_exercise_volume_leaders(stats_service: StatsService, sample_data: dict) -> None:
    """Test getting exercise volume leaders."""
    leaders = stats_service.get_exercise_volume_leaders(limit=5, weeks_back=4)

    assert len(leaders) > 0
    assert "exercise" in leaders[0]
    assert "total_volume" in leaders[0]
    assert leaders[0]["exercise"] == "Bench Press"


def test_multiple_workouts_summary(db: DatabaseManager, stats_service: StatsService) -> None:
    """Test summary with multiple workouts."""
    with db.get_connection() as conn:
        # Create exercise
        conn.execute(
            """
            INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
            VALUES ('Squat', 'Legs', 'Quads', 'Barbell', 'Compound')
        """
        )
        exercise_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Create multiple workouts
        for i in range(3):
            workout_date = datetime.now() - timedelta(days=i)
            conn.execute(
                """
                INSERT INTO workouts (date, name, duration_minutes, completed)
                VALUES (?, 'Leg Day', 70, TRUE)
            """,
                (workout_date,),
            )
            workout_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Add sets
            conn.execute(
                """
                INSERT INTO sets (
                    workout_id, exercise_id, set_number, weight, reps, rpe, set_type
                ) VALUES (?, ?, 1, 315, 5, 8.5, 'working')
            """,
                (workout_id, exercise_id),
            )

    summary = stats_service.get_workout_summary()

    assert summary["total_workouts"] == 3
    assert summary["avg_duration"] == 70


def test_volume_calculation_accuracy(db: DatabaseManager, stats_service: StatsService) -> None:
    """Test that volume calculations are accurate."""
    with db.get_connection() as conn:
        # Create exercise
        conn.execute(
            """
            INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
            VALUES ('Deadlift', 'Pull', 'Back', 'Barbell', 'Compound')
        """
        )
        exercise_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Create workout
        conn.execute(
            """
            INSERT INTO workouts (date, name, completed)
            VALUES (?, 'Pull Day', TRUE)
        """,
            (datetime.now(),),
        )
        workout_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Add set with known volume: 405 lbs × 3 reps = 1215 lbs
        conn.execute(
            """
            INSERT INTO sets (
                workout_id, exercise_id, set_number, weight, reps, set_type
            ) VALUES (?, ?, 1, 405, 3, 'working')
        """,
            (workout_id, exercise_id),
        )

    summary = stats_service.get_workout_summary()
    expected_volume = Decimal("1215")

    assert summary["total_volume"] == expected_volume


def test_rpe_averaging(db: DatabaseManager, stats_service: StatsService) -> None:
    """Test that RPE averaging is correct."""
    with db.get_connection() as conn:
        # Create exercise
        conn.execute(
            """
            INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
            VALUES ('OHP', 'Push', 'Shoulders', 'Barbell', 'Compound')
        """
        )
        exercise_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Create workout
        conn.execute(
            """
            INSERT INTO workouts (date, name, completed)
            VALUES (?, 'Push Day', TRUE)
        """,
            (datetime.now(),),
        )
        workout_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Add sets with specific RPE values: 7, 8, 9 (avg = 8.0)
        for i, rpe in enumerate([7.0, 8.0, 9.0], 1):
            conn.execute(
                """
                INSERT INTO sets (
                    workout_id, exercise_id, set_number, weight, reps, rpe, set_type
                ) VALUES (?, ?, ?, 135, 8, ?, 'working')
            """,
                (workout_id, exercise_id, i, rpe),
            )

    summary = stats_service.get_workout_summary()

    assert summary["avg_rpe"] == Decimal("8.0")
