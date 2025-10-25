"""Tests for PR service."""

from datetime import datetime
from decimal import Decimal

import pytest

from lift.core.database import DatabaseManager
from lift.core.models import PersonalRecordCreate, RecordType, WeightUnit
from lift.services.pr_service import PRService


@pytest.fixture
def db() -> DatabaseManager:
    """Create a test database."""
    db = DatabaseManager(":memory:")
    db.initialize_database()
    return db


@pytest.fixture
def pr_service(db: DatabaseManager) -> PRService:
    """Create PR service with test database."""
    return PRService(db)


@pytest.fixture
def sample_exercise(db: DatabaseManager) -> int:
    """Create a sample exercise and return its ID."""
    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
            VALUES ('Bench Press', 'Push', 'Chest', 'Barbell', 'Compound')
        """
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


@pytest.fixture
def sample_workout(db: DatabaseManager, sample_exercise: int) -> dict:
    """Create a sample workout with sets."""
    with db.get_connection() as conn:
        # Create workout
        conn.execute(
            """
            INSERT INTO workouts (date, name, duration_minutes, completed)
            VALUES (?, 'Push Day', 60, TRUE)
        """,
            (datetime.now(),),
        )
        workout_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Create sets with various rep ranges
        sets_data = [
            (workout_id, sample_exercise, 1, 315, 1, 10.0, "working"),  # 1RM attempt
            (workout_id, sample_exercise, 2, 275, 3, 9.0, "working"),  # 3RM
            (workout_id, sample_exercise, 3, 255, 5, 8.5, "working"),  # 5RM
            (workout_id, sample_exercise, 4, 225, 10, 8.0, "working"),  # 10RM
        ]

        set_ids = []
        for set_data in sets_data:
            conn.execute(
                """
                INSERT INTO sets (
                    workout_id, exercise_id, set_number, weight, reps, rpe, set_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                set_data,
            )
            set_ids.append(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    return {
        "workout_id": workout_id,
        "exercise_id": sample_exercise,
        "set_ids": set_ids,
    }


def test_create_pr(pr_service: PRService, sample_exercise: int) -> None:
    """Test creating a personal record."""
    pr_create = PersonalRecordCreate(
        exercise_id=sample_exercise,
        record_type=RecordType.ONE_RM,
        value=Decimal("315"),
        reps=1,
        weight=Decimal("315"),
        weight_unit=WeightUnit.LBS,
        date=datetime.now(),
    )

    pr = pr_service.create_pr(pr_create)

    assert pr.id is not None
    assert pr.exercise_id == sample_exercise
    assert pr.record_type == RecordType.ONE_RM
    assert pr.value == Decimal("315")


def test_get_all_prs(pr_service: PRService, sample_exercise: int) -> None:
    """Test getting all PRs."""
    # Create multiple PRs
    for record_type in [RecordType.ONE_RM, RecordType.FIVE_RM]:
        pr_create = PersonalRecordCreate(
            exercise_id=sample_exercise,
            record_type=record_type,
            value=Decimal("300"),
            reps=1 if record_type == RecordType.ONE_RM else 5,
            weight=Decimal("300"),
            weight_unit=WeightUnit.LBS,
            date=datetime.now(),
        )
        pr_service.create_pr(pr_create)

    prs = pr_service.get_all_prs()

    assert len(prs) == 2


def test_get_prs_by_exercise(pr_service: PRService, sample_exercise: int, db: DatabaseManager) -> None:
    """Test getting PRs filtered by exercise."""
    # Create another exercise
    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
            VALUES ('Squat', 'Legs', 'Quads', 'Barbell', 'Compound')
        """
        )
        squat_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Create PRs for both exercises
    for exercise_id in [sample_exercise, squat_id]:
        pr_create = PersonalRecordCreate(
            exercise_id=exercise_id,
            record_type=RecordType.ONE_RM,
            value=Decimal("400"),
            reps=1,
            weight=Decimal("400"),
            weight_unit=WeightUnit.LBS,
            date=datetime.now(),
        )
        pr_service.create_pr(pr_create)

    # Get PRs for bench press only
    bench_prs = pr_service.get_all_prs(exercise_id=sample_exercise)

    assert len(bench_prs) == 1
    assert bench_prs[0].exercise_id == sample_exercise


def test_get_pr_by_type(pr_service: PRService, sample_exercise: int) -> None:
    """Test getting PR by specific type."""
    # Create PR
    pr_create = PersonalRecordCreate(
        exercise_id=sample_exercise,
        record_type=RecordType.FIVE_RM,
        value=Decimal("275"),
        reps=5,
        weight=Decimal("275"),
        weight_unit=WeightUnit.LBS,
        date=datetime.now(),
    )
    pr_service.create_pr(pr_create)

    # Get the PR
    pr = pr_service.get_pr_by_type(sample_exercise, RecordType.FIVE_RM)

    assert pr is not None
    assert pr.record_type == RecordType.FIVE_RM
    assert pr.value == Decimal("275")


def test_get_pr_by_type_not_found(pr_service: PRService, sample_exercise: int) -> None:
    """Test getting PR that doesn't exist."""
    pr = pr_service.get_pr_by_type(sample_exercise, RecordType.TEN_RM)

    assert pr is None


def test_is_new_pr_true(pr_service: PRService, sample_exercise: int) -> None:
    """Test checking if a value is a new PR (should be true)."""
    # Create initial PR
    pr_create = PersonalRecordCreate(
        exercise_id=sample_exercise,
        record_type=RecordType.ONE_RM,
        value=Decimal("300"),
        reps=1,
        weight=Decimal("300"),
        weight_unit=WeightUnit.LBS,
        date=datetime.now(),
    )
    pr_service.create_pr(pr_create)

    # Check if 315 is a new PR (should be)
    is_pr = pr_service.is_new_pr(sample_exercise, RecordType.ONE_RM, Decimal("315"))

    assert is_pr is True


def test_is_new_pr_false(pr_service: PRService, sample_exercise: int) -> None:
    """Test checking if a value is a new PR (should be false)."""
    # Create initial PR
    pr_create = PersonalRecordCreate(
        exercise_id=sample_exercise,
        record_type=RecordType.ONE_RM,
        value=Decimal("315"),
        reps=1,
        weight=Decimal("315"),
        weight_unit=WeightUnit.LBS,
        date=datetime.now(),
    )
    pr_service.create_pr(pr_create)

    # Check if 300 is a new PR (should not be)
    is_pr = pr_service.is_new_pr(sample_exercise, RecordType.ONE_RM, Decimal("300"))

    assert is_pr is False


def test_is_new_pr_first_time(pr_service: PRService, sample_exercise: int) -> None:
    """Test checking if a value is a new PR (first time)."""
    # No existing PR, so any value should be a PR
    is_pr = pr_service.is_new_pr(sample_exercise, RecordType.ONE_RM, Decimal("225"))

    assert is_pr is True


def test_auto_detect_prs(pr_service: PRService, sample_workout: dict) -> None:
    """Test automatic PR detection."""
    prs = pr_service.auto_detect_prs(sample_workout["workout_id"])

    # Should detect PRs for various rep maxes
    assert len(prs) > 0

    # Check that different PR types were detected
    pr_types = {pr.record_type for pr in prs}
    assert RecordType.ONE_RM in pr_types


def test_auto_detect_prs_no_new_records(
    pr_service: PRService, sample_workout: dict, sample_exercise: int
) -> None:
    """Test auto-detection when no new PRs are set."""
    # First detection - should find PRs
    first_prs = pr_service.auto_detect_prs(sample_workout["workout_id"])
    assert len(first_prs) > 0

    # Create another workout with same or lower weights
    with pr_service.db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO workouts (date, name, completed)
            VALUES (?, 'Push Day 2', TRUE)
        """,
            (datetime.now(),),
        )
        workout_id_2 = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Add sets with lower weights
        conn.execute(
            """
            INSERT INTO sets (
                workout_id, exercise_id, set_number, weight, reps, set_type
            ) VALUES (?, ?, 1, 225, 5, 'working')
        """,
            (workout_id_2, sample_exercise),
        )

    # Second detection - should not find new PRs
    second_prs = pr_service.auto_detect_prs(workout_id_2)
    assert len(second_prs) == 0


def test_auto_detect_volume_pr(pr_service: PRService, sample_exercise: int, db: DatabaseManager) -> None:
    """Test detection of volume PR."""
    with db.get_connection() as conn:
        # Create workout with high-volume set
        conn.execute(
            """
            INSERT INTO workouts (date, name, completed)
            VALUES (?, 'Volume Day', TRUE)
        """,
            (datetime.now(),),
        )
        workout_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Add set with high volume: 225 × 15 = 3375 lbs
        conn.execute(
            """
            INSERT INTO sets (
                workout_id, exercise_id, set_number, weight, reps, set_type
            ) VALUES (?, ?, 1, 225, 15, 'working')
        """,
            (workout_id, sample_exercise),
        )

    prs = pr_service.auto_detect_prs(workout_id)

    # Should detect volume PR
    volume_prs = [pr for pr in prs if pr.record_type == RecordType.VOLUME]
    assert len(volume_prs) > 0
    assert volume_prs[0].value == Decimal("3375")


def test_auto_detect_max_weight_pr(
    pr_service: PRService, sample_exercise: int, db: DatabaseManager
) -> None:
    """Test detection of max weight PR."""
    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO workouts (date, name, completed)
            VALUES (?, 'Max Day', TRUE)
        """,
            (datetime.now(),),
        )
        workout_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Add set with very heavy weight
        conn.execute(
            """
            INSERT INTO sets (
                workout_id, exercise_id, set_number, weight, reps, set_type
            ) VALUES (?, ?, 1, 405, 1, 'working')
        """,
            (workout_id, sample_exercise),
        )

    prs = pr_service.auto_detect_prs(workout_id)

    # Should detect max weight PR
    max_weight_prs = [pr for pr in prs if pr.record_type == RecordType.MAX_WEIGHT]
    assert len(max_weight_prs) > 0
    assert max_weight_prs[0].value == Decimal("405")


def test_get_pr_summary(pr_service: PRService, sample_workout: dict) -> None:
    """Test getting PR summary for an exercise."""
    # Detect and create PRs
    pr_service.auto_detect_prs(sample_workout["workout_id"])

    # Get summary
    summary = pr_service.get_pr_summary(sample_workout["exercise_id"])

    assert len(summary) > 0
    assert RecordType.ONE_RM.value in summary


def test_get_recent_prs(pr_service: PRService, sample_workout: dict) -> None:
    """Test getting recent PRs."""
    # Create PRs
    pr_service.auto_detect_prs(sample_workout["workout_id"])

    # Get recent PRs
    recent = pr_service.get_recent_prs(days=30, limit=10)

    assert len(recent) > 0
    assert "exercise_name" in recent[0]
    assert "record_type" in recent[0]


def test_delete_pr(pr_service: PRService, sample_exercise: int) -> None:
    """Test deleting a PR."""
    # Create PR
    pr_create = PersonalRecordCreate(
        exercise_id=sample_exercise,
        record_type=RecordType.ONE_RM,
        value=Decimal("300"),
        reps=1,
        weight=Decimal("300"),
        weight_unit=WeightUnit.LBS,
        date=datetime.now(),
    )
    pr = pr_service.create_pr(pr_create)

    # Delete it
    success = pr_service.delete_pr(pr.id)

    assert success is True

    # Verify it's gone
    deleted_pr = pr_service.get_pr_by_type(sample_exercise, RecordType.ONE_RM)
    assert deleted_pr is None


def test_delete_pr_not_found(pr_service: PRService) -> None:
    """Test deleting a PR that doesn't exist."""
    success = pr_service.delete_pr(99999)

    assert success is False


def test_get_pr_history(pr_service: PRService, sample_exercise: int) -> None:
    """Test getting PR history."""
    # Create multiple PRs over time
    values = [Decimal("275"), Decimal("300"), Decimal("315")]

    for value in values:
        pr_create = PersonalRecordCreate(
            exercise_id=sample_exercise,
            record_type=RecordType.ONE_RM,
            value=value,
            reps=1,
            weight=value,
            weight_unit=WeightUnit.LBS,
            date=datetime.now(),
        )
        pr_service.create_pr(pr_create)

    # Get history
    history = pr_service.get_pr_history(sample_exercise, RecordType.ONE_RM)

    assert len(history) == 3
    # Should be in chronological order
    assert history[0].value <= history[-1].value


def test_pr_with_workout_and_set_ids(
    pr_service: PRService, sample_workout: dict
) -> None:
    """Test that PRs are linked to workouts and sets."""
    prs = pr_service.auto_detect_prs(sample_workout["workout_id"])

    assert len(prs) > 0

    for pr in prs:
        assert pr.workout_id == sample_workout["workout_id"]
        assert pr.set_id in sample_workout["set_ids"]


def test_multiple_exercises_pr_detection(pr_service: PRService, db: DatabaseManager) -> None:
    """Test PR detection with multiple exercises in one workout."""
    with db.get_connection() as conn:
        # Create exercises
        conn.execute(
            """
            INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
            VALUES ('Bench Press', 'Push', 'Chest', 'Barbell', 'Compound'),
                   ('Squat', 'Legs', 'Quads', 'Barbell', 'Compound')
        """
        )

        # Get exercise IDs
        exercises = conn.execute(
            "SELECT id FROM exercises WHERE name IN ('Bench Press', 'Squat')"
        ).fetchall()
        bench_id, squat_id = exercises[0][0], exercises[1][0]

        # Create workout
        conn.execute(
            """
            INSERT INTO workouts (date, name, completed)
            VALUES (?, 'Full Body', TRUE)
        """,
            (datetime.now(),),
        )
        workout_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Add sets for both exercises
        conn.execute(
            """
            INSERT INTO sets (workout_id, exercise_id, set_number, weight, reps, set_type)
            VALUES (?, ?, 1, 315, 1, 'working'),
                   (?, ?, 1, 405, 1, 'working')
        """,
            (workout_id, bench_id, workout_id, squat_id),
        )

    prs = pr_service.auto_detect_prs(workout_id)

    # Should detect PRs for both exercises
    exercise_ids = {pr.exercise_id for pr in prs}
    assert bench_id in exercise_ids
    assert squat_id in exercise_ids
