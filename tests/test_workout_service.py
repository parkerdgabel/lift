"""Tests for workout service."""

from datetime import datetime
from decimal import Decimal

import pytest

from lift.core.models import SetCreate, SetType, WeightUnit, WorkoutCreate, WorkoutUpdate
from lift.services.set_service import SetService
from lift.services.workout_service import WorkoutService


@pytest.fixture
def workout_service(db):
    """Create workout service instance."""
    return WorkoutService(db)


@pytest.fixture
def set_service(db):
    """Create set service instance."""
    return SetService(db)


@pytest.fixture
def sample_workout(workout_service):
    """Create a sample workout for testing."""
    workout_create = WorkoutCreate(
        name="Test Workout",
        date=datetime.now(),
        bodyweight=Decimal("185"),
        bodyweight_unit=WeightUnit.LBS,
    )
    return workout_service.create_workout(workout_create)


class TestWorkoutService:
    """Test workout service operations."""

    def test_create_workout(self, workout_service):
        """Test creating a workout."""
        workout_create = WorkoutCreate(
            name="Push Day",
            date=datetime.now(),
            bodyweight=Decimal("180.5"),
            bodyweight_unit=WeightUnit.LBS,
            notes="Felt strong today",
            rating=4,
        )

        workout = workout_service.create_workout(workout_create)

        assert workout.id is not None
        assert workout.name == "Push Day"
        assert workout.bodyweight == Decimal("180.5")
        assert workout.bodyweight_unit == WeightUnit.LBS
        assert workout.notes == "Felt strong today"
        assert workout.rating == 4
        assert workout.completed is False  # New workouts start incomplete

    def test_create_workout_minimal(self, workout_service):
        """Test creating a workout with minimal data."""
        workout_create = WorkoutCreate(date=datetime.now())

        workout = workout_service.create_workout(workout_create)

        assert workout.id is not None
        assert workout.name is None
        assert workout.bodyweight is None

    def test_get_workout(self, workout_service, sample_workout):
        """Test retrieving a workout by ID."""
        workout = workout_service.get_workout(sample_workout.id)

        assert workout is not None
        assert workout.id == sample_workout.id
        assert workout.name == sample_workout.name

    def test_get_workout_not_found(self, workout_service):
        """Test retrieving non-existent workout."""
        workout = workout_service.get_workout(9999)

        assert workout is None

    def test_get_recent_workouts(self, workout_service):
        """Test retrieving recent workouts."""
        # Create multiple workouts
        for i in range(5):
            workout_create = WorkoutCreate(
                name=f"Workout {i}",
                date=datetime.now(),
            )
            workout_service.create_workout(workout_create)

        workouts = workout_service.get_recent_workouts(limit=3)

        assert len(workouts) == 3
        # Should be ordered by date descending
        assert workouts[0].name == "Workout 4"

    def test_get_last_workout(self, workout_service):
        """Test retrieving the most recent workout."""
        # Create workouts
        for i in range(3):
            workout_create = WorkoutCreate(
                name=f"Workout {i}",
                date=datetime.now(),
            )
            workout_service.create_workout(workout_create)

        last_workout = workout_service.get_last_workout()

        assert last_workout is not None
        assert last_workout.name == "Workout 2"

    def test_update_workout(self, workout_service, sample_workout):
        """Test updating a workout."""
        update = WorkoutUpdate(
            name="Updated Workout",
            duration_minutes=60,
            rating=5,
            notes="Great session!",
        )

        updated_workout = workout_service.update_workout(sample_workout.id, update)

        assert updated_workout.name == "Updated Workout"
        assert updated_workout.duration_minutes == 60
        assert updated_workout.rating == 5
        assert updated_workout.notes == "Great session!"

    def test_update_workout_partial(self, workout_service, sample_workout):
        """Test partial workout update."""
        update = WorkoutUpdate(rating=3)

        updated_workout = workout_service.update_workout(sample_workout.id, update)

        assert updated_workout.rating == 3
        assert updated_workout.name == sample_workout.name  # Unchanged

    def test_delete_workout(self, workout_service, sample_workout):
        """Test deleting a workout."""
        result = workout_service.delete_workout(sample_workout.id)

        assert result is True

        # Verify deletion
        workout = workout_service.get_workout(sample_workout.id)
        assert workout is None

    def test_finish_workout(self, workout_service, sample_workout):
        """Test finishing a workout."""
        finished_workout = workout_service.finish_workout(sample_workout.id, 75)

        assert finished_workout.duration_minutes == 75
        assert finished_workout.completed is True

    def test_get_workout_summary(self, workout_service, set_service, sample_workout, db):
        """Test getting workout summary with sets."""
        # First, create an exercise
        with db.get_connection() as conn:
            result = conn.execute(
                """
                INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
                VALUES ('Bench Press', 'Push', 'Chest', 'Barbell', 'Compound')
                RETURNING id
                """
            ).fetchone()
            exercise_id = result[0]

        # Add sets to the workout
        for i in range(3):
            set_create = SetCreate(
                workout_id=sample_workout.id,
                exercise_id=exercise_id,
                set_number=i + 1,
                weight=Decimal("185"),
                weight_unit=WeightUnit.LBS,
                reps=10,
                rpe=Decimal("8.5"),
                set_type=SetType.WORKING,
            )
            set_service.add_set(set_create)

        summary = workout_service.get_workout_summary(sample_workout.id)

        assert summary.total_exercises == 1
        assert summary.total_sets == 3
        assert summary.total_volume == Decimal("5550")  # 185 * 10 * 3
        assert summary.avg_rpe == Decimal("8.5")

    def test_get_workout_summary_empty(self, workout_service, sample_workout):
        """Test getting summary for workout with no sets."""
        summary = workout_service.get_workout_summary(sample_workout.id)

        assert summary.total_exercises == 0
        assert summary.total_sets == 0
        assert summary.total_volume == Decimal("0")
        assert summary.avg_rpe is None

    def test_get_last_performance(self, workout_service, set_service, db):
        """Test getting last performance for an exercise."""
        # Create exercise
        with db.get_connection() as conn:
            result = conn.execute(
                """
                INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
                VALUES ('Squat', 'Legs', 'Quads', 'Barbell', 'Compound')
                RETURNING id
                """
            ).fetchone()
            exercise_id = result[0]

        # Create workout and sets
        workout_create = WorkoutCreate(
            name="Leg Day",
            date=datetime.now(),
        )
        workout = workout_service.create_workout(workout_create)

        for i in range(3):
            set_create = SetCreate(
                workout_id=workout.id,
                exercise_id=exercise_id,
                set_number=i + 1,
                weight=Decimal("225"),
                weight_unit=WeightUnit.LBS,
                reps=8,
                rpe=Decimal("8.0"),
                set_type=SetType.WORKING,
            )
            set_service.add_set(set_create)

        # Get last performance
        performance = workout_service.get_last_performance(exercise_id, limit=1)

        assert len(performance) >= 3
        assert performance[0]["weight"] == Decimal("225")
        assert performance[0]["reps"] == 8


class TestSetService:
    """Test set service operations."""

    def test_add_set(self, set_service, sample_workout, db):
        """Test adding a set."""
        # Create exercise
        with db.get_connection() as conn:
            result = conn.execute(
                """
                INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
                VALUES ('Deadlift', 'Pull', 'Back', 'Barbell', 'Compound')
                RETURNING id
                """
            ).fetchone()
            exercise_id = result[0]

        set_create = SetCreate(
            workout_id=sample_workout.id,
            exercise_id=exercise_id,
            set_number=1,
            weight=Decimal("315"),
            weight_unit=WeightUnit.LBS,
            reps=5,
            rpe=Decimal("9.0"),
            set_type=SetType.WORKING,
        )

        set_obj = set_service.add_set(set_create)

        assert set_obj.id is not None
        assert set_obj.workout_id == sample_workout.id
        assert set_obj.exercise_id == exercise_id
        assert set_obj.weight == Decimal("315")
        assert set_obj.reps == 5
        assert set_obj.rpe == Decimal("9.0")

    def test_get_sets_for_workout(self, set_service, sample_workout, db):
        """Test retrieving all sets for a workout."""
        # Create exercise
        with db.get_connection() as conn:
            result = conn.execute(
                """
                INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
                VALUES ('Row', 'Pull', 'Back', 'Barbell', 'Compound')
                RETURNING id
                """
            ).fetchone()
            exercise_id = result[0]

        # Add multiple sets
        for i in range(4):
            set_create = SetCreate(
                workout_id=sample_workout.id,
                exercise_id=exercise_id,
                set_number=i + 1,
                weight=Decimal("135"),
                weight_unit=WeightUnit.LBS,
                reps=12,
                set_type=SetType.WORKING,
            )
            set_service.add_set(set_create)

        sets = set_service.get_sets_for_workout(sample_workout.id)

        assert len(sets) == 4
        assert sets[0].set_number == 1
        assert sets[-1].set_number == 4

    def test_calculate_volume(self, set_service, sample_workout, db):
        """Test volume calculation."""
        # Create exercise
        with db.get_connection() as conn:
            result = conn.execute(
                """
                INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
                VALUES ('Press', 'Push', 'Shoulders', 'Barbell', 'Compound')
                RETURNING id
                """
            ).fetchone()
            exercise_id = result[0]

        # Add sets with varying weights and reps
        sets_data = [
            (Decimal("135"), 10),
            (Decimal("155"), 8),
            (Decimal("175"), 6),
        ]

        created_sets = []
        for i, (weight, reps) in enumerate(sets_data):
            set_create = SetCreate(
                workout_id=sample_workout.id,
                exercise_id=exercise_id,
                set_number=i + 1,
                weight=weight,
                weight_unit=WeightUnit.LBS,
                reps=reps,
                set_type=SetType.WORKING,
            )
            created_sets.append(set_service.add_set(set_create))

        total_volume = set_service.calculate_volume(created_sets)

        # 135*10 + 155*8 + 175*6 = 1350 + 1240 + 1050 = 3640
        assert total_volume == Decimal("3640")

    def test_calculate_estimated_1rm(self, set_service):
        """Test 1RM estimation."""
        # Test with 5 reps at 225 lbs
        estimated_1rm = set_service.calculate_estimated_1rm(Decimal("225"), 5)

        # Epley formula: 225 * (1 + 5/30) = 225 * 1.1667 = 262.5
        assert estimated_1rm == Decimal("262.5")

    def test_calculate_estimated_1rm_single_rep(self, set_service):
        """Test 1RM estimation with single rep."""
        estimated_1rm = set_service.calculate_estimated_1rm(Decimal("315"), 1)

        assert estimated_1rm == Decimal("315")

    def test_delete_set(self, set_service, sample_workout, db):
        """Test deleting a set."""
        # Create exercise and set
        with db.get_connection() as conn:
            result = conn.execute(
                """
                INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
                VALUES ('Curl', 'Pull', 'Biceps', 'Dumbbell', 'Isolation')
                RETURNING id
                """
            ).fetchone()
            exercise_id = result[0]

        set_create = SetCreate(
            workout_id=sample_workout.id,
            exercise_id=exercise_id,
            set_number=1,
            weight=Decimal("30"),
            weight_unit=WeightUnit.LBS,
            reps=12,
            set_type=SetType.WORKING,
        )
        created_set = set_service.add_set(set_create)

        # Delete set
        result = set_service.delete_set(created_set.id)
        assert result is True

        # Verify deletion
        sets = set_service.get_sets_for_workout(sample_workout.id)
        assert len(sets) == 0
