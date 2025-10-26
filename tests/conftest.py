"""
Shared pytest fixtures for all tests.

This module provides reusable fixtures that can be used across all test files.
"""

from collections.abc import Generator
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from lift.core.database import DatabaseManager, reset_db_instance
from lift.core.models import (
    CategoryType,
    EquipmentType,
    ExerciseCreate,
    MovementType,
    MuscleGroup,
    ProgramCreate,
    ProgramExerciseCreate,
    ProgramWorkoutCreate,
    SetCreate,
    SetType,
    SplitType,
    WorkoutCreate,
)
from lift.services.exercise_service import ExerciseService
from lift.services.program_service import ProgramService
from lift.services.set_service import SetService
from lift.services.workout_service import WorkoutService


@pytest.fixture(autouse=True)
def reset_global_db() -> Generator[None, None, None]:
    """Reset the global database instance before each test."""
    reset_db_instance()
    yield
    reset_db_instance()


@pytest.fixture
def db() -> Generator[DatabaseManager, None, None]:
    """Create a temporary database for testing (function scope - gets reset each test)."""
    import tempfile
    from pathlib import Path

    # Create a temporary file path (delete the empty file so DuckDB can create it fresh)
    temp_file = tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    Path(temp_path).unlink()  # Delete empty file so DuckDB can create it

    try:
        db = DatabaseManager(temp_path)
        db.initialize_database()
        yield db
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)
        if Path(temp_path + ".wal").exists():
            Path(temp_path + ".wal").unlink()


@pytest.fixture(scope="session")
def session_db() -> Generator[DatabaseManager, None, None]:
    """
    Create a session-scoped database for read-only tests.

    Use this for tests that only read data and don't modify the database.
    Much faster than creating a new DB for each test.
    """
    import tempfile
    from pathlib import Path

    temp_file = tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    Path(temp_path).unlink()

    try:
        db = DatabaseManager(temp_path)
        db.initialize_database()
        yield db
    finally:
        Path(temp_path).unlink(missing_ok=True)
        if Path(temp_path + ".wal").exists():
            Path(temp_path + ".wal").unlink()


@pytest.fixture
def exercise_data() -> list[dict]:
    """Standard set of exercises for testing."""
    return [
        {
            "name": "Barbell Bench Press",
            "category": CategoryType.PUSH,
            "primary_muscle": MuscleGroup.CHEST,
            "secondary_muscles": [MuscleGroup.TRICEPS, MuscleGroup.SHOULDERS],
            "equipment": EquipmentType.BARBELL,
            "movement_type": MovementType.COMPOUND,
        },
        {
            "name": "Barbell Squat",
            "category": CategoryType.LEGS,
            "primary_muscle": MuscleGroup.QUADS,
            "secondary_muscles": [MuscleGroup.GLUTES, MuscleGroup.HAMSTRINGS],
            "equipment": EquipmentType.BARBELL,
            "movement_type": MovementType.COMPOUND,
        },
        {
            "name": "Deadlift",
            "category": CategoryType.PULL,
            "primary_muscle": MuscleGroup.BACK,
            "secondary_muscles": [MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES],
            "equipment": EquipmentType.BARBELL,
            "movement_type": MovementType.COMPOUND,
        },
        {
            "name": "Overhead Press",
            "category": CategoryType.PUSH,
            "primary_muscle": MuscleGroup.SHOULDERS,
            "secondary_muscles": [MuscleGroup.TRICEPS],
            "equipment": EquipmentType.BARBELL,
            "movement_type": MovementType.COMPOUND,
        },
        {
            "name": "Barbell Row",
            "category": CategoryType.PULL,
            "primary_muscle": MuscleGroup.BACK,
            "secondary_muscles": [MuscleGroup.BICEPS],
            "equipment": EquipmentType.BARBELL,
            "movement_type": MovementType.COMPOUND,
        },
        {
            "name": "Dumbbell Curl",
            "category": CategoryType.PULL,
            "primary_muscle": MuscleGroup.BICEPS,
            "secondary_muscles": [],
            "equipment": EquipmentType.DUMBBELL,
            "movement_type": MovementType.ISOLATION,
        },
        {
            "name": "Leg Press",
            "category": CategoryType.LEGS,
            "primary_muscle": MuscleGroup.QUADS,
            "secondary_muscles": [MuscleGroup.GLUTES],
            "equipment": EquipmentType.MACHINE,
            "movement_type": MovementType.COMPOUND,
        },
        {
            "name": "Lat Pulldown",
            "category": CategoryType.PULL,
            "primary_muscle": MuscleGroup.BACK,
            "secondary_muscles": [MuscleGroup.BICEPS],
            "equipment": EquipmentType.CABLE,
            "movement_type": MovementType.COMPOUND,
        },
    ]


@pytest.fixture
def db_with_seed_exercises(db: DatabaseManager) -> DatabaseManager:
    """Database with all seed exercises loaded. Use sparingly as it's slow."""
    exercise_service = ExerciseService(db)
    exercise_service.load_seed_exercises()
    return db


@pytest.fixture(scope="session")
def session_db_with_seed_exercises(session_db: DatabaseManager) -> DatabaseManager:
    """
    Session-scoped database with all seed exercises pre-loaded.

    Use this for read-only tests that need the full exercise library.
    Much faster than loading seed exercises for each test.
    """
    exercise_service = ExerciseService(session_db)
    exercise_service.load_seed_exercises()
    return session_db


@pytest.fixture
def loaded_exercises(db: DatabaseManager, exercise_data: list[dict]) -> dict[str, int]:
    """Database with exercises pre-loaded. Returns dict of exercise_name -> exercise_id."""
    exercise_service = ExerciseService(db)
    exercise_ids = {}

    for ex_data in exercise_data:
        exercise = exercise_service.create(ExerciseCreate(**ex_data))
        exercise_ids[exercise.name] = exercise.id

    return exercise_ids


@pytest.fixture
def sample_workout(
    db: DatabaseManager, loaded_exercises: dict[str, int]
) -> tuple[int, dict[str, int]]:
    """Create a sample workout with sets. Returns (workout_id, exercise_ids)."""
    workout_service = WorkoutService(db)
    set_service = SetService(db)

    # Create workout
    workout = workout_service.create_workout(
        WorkoutCreate(
            name="Sample Workout",
            bodyweight=Decimal("180.0"),
        )
    )

    # Add sets for bench press
    bench_id = loaded_exercises["Barbell Bench Press"]
    for set_num in range(1, 4):
        set_service.add_set(
            SetCreate(
                workout_id=workout.id,
                exercise_id=bench_id,
                set_number=set_num,
                weight=Decimal("185"),
                reps=10,
                rpe=Decimal("8.0"),
                set_type=SetType.WORKING,
            )
        )

    # Add sets for squat
    squat_id = loaded_exercises["Barbell Squat"]
    for set_num in range(1, 4):
        set_service.add_set(
            SetCreate(
                workout_id=workout.id,
                exercise_id=squat_id,
                set_number=set_num,
                weight=Decimal("225"),
                reps=8,
                rpe=Decimal("8.5"),
                set_type=SetType.WORKING,
            )
        )

    workout_service.finish_workout(workout.id, duration_minutes=75)

    return workout.id, loaded_exercises


@pytest.fixture
def sample_program(
    db: DatabaseManager, loaded_exercises: dict[str, int]
) -> tuple[int, int, dict[str, int]]:
    """
    Create a sample program with a workout template.

    Returns (program_id, program_workout_id, exercise_ids).
    """
    program_service = ProgramService(db)

    # Create program
    program = program_service.create_program(
        ProgramCreate(
            name="Sample PPL",
            description="Push Pull Legs for testing",
            split_type=SplitType.PPL,
            days_per_week=6,
        )
    )

    # Add Push workout
    push_workout = program_service.add_workout_to_program(
        program.id,
        ProgramWorkoutCreate(
            program_id=program.id,
            name="Push A",
            day_number=1,
            description="Chest and shoulders",
        ),
    )

    # Add exercises to Push workout
    bench_id = loaded_exercises["Barbell Bench Press"]
    ohp_id = loaded_exercises["Overhead Press"]

    program_service.add_exercise_to_workout(
        push_workout.id,
        ProgramExerciseCreate(
            program_workout_id=push_workout.id,
            exercise_id=bench_id,
            order_number=1,
            target_sets=4,
            target_reps_min=8,
            target_reps_max=10,
            target_rpe=Decimal("8.5"),
            rest_seconds=180,
        ),
    )

    program_service.add_exercise_to_workout(
        push_workout.id,
        ProgramExerciseCreate(
            program_workout_id=push_workout.id,
            exercise_id=ohp_id,
            order_number=2,
            target_sets=3,
            target_reps_min=8,
            target_reps_max=12,
            target_rpe=Decimal("8.0"),
            rest_seconds=120,
        ),
    )

    return program.id, push_workout.id, loaded_exercises


@pytest.fixture
def multi_week_workout_data(
    db: DatabaseManager, loaded_exercises: dict[str, int]
) -> tuple[list[int], dict[str, int]]:
    """
    Create 4 weeks of workout data with progression.

    Returns (list of workout_ids, exercise_ids).
    """
    workout_service = WorkoutService(db)
    set_service = SetService(db)

    bench_id = loaded_exercises["Barbell Bench Press"]
    squat_id = loaded_exercises["Barbell Squat"]

    base_date = datetime.now() - timedelta(days=28)
    workout_ids = []

    for week in range(4):
        workout_date = base_date + timedelta(days=week * 7)
        bench_weight = Decimal(str(185 + (week * 5)))
        squat_weight = Decimal(str(225 + (week * 10)))

        # Create workout
        workout = workout_service.create_workout(
            WorkoutCreate(
                name=f"Week {week + 1} - Full Body",
                date=workout_date,
                bodyweight=Decimal(str(180 + (week * 0.5))),
            )
        )

        # Bench press sets
        for set_num in range(1, 4):
            set_service.add_set(
                SetCreate(
                    workout_id=workout.id,
                    exercise_id=bench_id,
                    set_number=set_num,
                    weight=bench_weight,
                    reps=10,
                    rpe=Decimal("8.0") + Decimal(str(set_num * 0.5)),
                    set_type=SetType.WORKING,
                )
            )

        # Squat sets
        for set_num in range(1, 4):
            set_service.add_set(
                SetCreate(
                    workout_id=workout.id,
                    exercise_id=squat_id,
                    set_number=set_num,
                    weight=squat_weight,
                    reps=8,
                    rpe=Decimal("8.5") + Decimal(str(set_num * 0.5)),
                    set_type=SetType.WORKING,
                )
            )

        workout_service.finish_workout(workout.id, duration_minutes=75 + (week * 5))
        workout_ids.append(workout.id)

    return workout_ids, loaded_exercises


@pytest.fixture
def realistic_training_cycle(
    db: DatabaseManager, loaded_exercises: dict[str, int]
) -> tuple[list[int], dict[str, int]]:
    """
    Create a realistic 8-week training cycle with:
    - Progressive overload
    - Multiple exercises per workout
    - Varying rep ranges
    - Deload week

    Returns (list of workout_ids, exercise_ids).
    """
    workout_service = WorkoutService(db)
    set_service = SetService(db)

    bench_id = loaded_exercises["Barbell Bench Press"]
    squat_id = loaded_exercises["Barbell Squat"]
    deadlift_id = loaded_exercises["Deadlift"]
    row_id = loaded_exercises["Barbell Row"]

    base_date = datetime.now() - timedelta(days=56)  # 8 weeks ago
    workout_ids = []

    for week in range(8):
        # Weeks 1-3: Linear progression
        # Weeks 4-6: Continued progression
        # Week 7: Deload
        # Week 8: Test maxes

        is_deload = week == 6
        is_test = week == 7

        workout_date = base_date + timedelta(days=week * 7)

        # Adjust weights based on week
        if is_deload:
            bench_weight = Decimal("155")  # -30 lbs for deload
            squat_weight = Decimal("185")  # -40 lbs for deload
            reps = 10
        elif is_test:
            bench_weight = Decimal("215")
            squat_weight = Decimal("315")
            reps = 3
        else:
            bench_weight = Decimal(str(185 + (week * 5)))
            squat_weight = Decimal(str(225 + (week * 10)))
            reps = 8 if week < 4 else 5  # Switch to strength work

        # Create workout
        workout = workout_service.create_workout(
            WorkoutCreate(
                name=f"Week {week + 1} - {'Deload' if is_deload else 'Test' if is_test else 'Training'}",
                date=workout_date,
                bodyweight=Decimal(str(180 + (week * 0.3))),
            )
        )

        # Log sets
        sets_per_exercise = 3 if not is_deload else 2

        for set_num in range(1, sets_per_exercise + 1):
            # Bench
            set_service.add_set(
                SetCreate(
                    workout_id=workout.id,
                    exercise_id=bench_id,
                    set_number=set_num,
                    weight=bench_weight,
                    reps=reps,
                    rpe=Decimal("7.0") if is_deload else Decimal("8.5"),
                    set_type=SetType.WORKING,
                )
            )

            # Squat
            set_service.add_set(
                SetCreate(
                    workout_id=workout.id,
                    exercise_id=squat_id,
                    set_number=set_num,
                    weight=squat_weight,
                    reps=reps,
                    rpe=Decimal("7.0") if is_deload else Decimal("9.0"),
                    set_type=SetType.WORKING,
                )
            )

        workout_service.finish_workout(workout.id, duration_minutes=90)
        workout_ids.append(workout.id)

    return workout_ids, loaded_exercises
