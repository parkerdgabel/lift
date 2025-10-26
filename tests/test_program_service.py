"""Tests for program service."""

import json
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from lift.core.models import (
    Program,
    ProgramCreate,
    ProgramExerciseCreate,
    ProgramWorkoutCreate,
    SplitType,
)
from lift.services.program_service import ProgramService


@pytest.fixture
def service(db):
    """Create a program service with test database."""
    return ProgramService(db)


@pytest.fixture
def sample_exercises(db):
    """Create sample exercises for testing."""
    exercises = [
        {
            "name": "Barbell Bench Press",
            "category": "Push",
            "primary_muscle": "Chest",
            "equipment": "Barbell",
            "movement_type": "Compound",
        },
        {
            "name": "Barbell Squat",
            "category": "Legs",
            "primary_muscle": "Quads",
            "equipment": "Barbell",
            "movement_type": "Compound",
        },
        {
            "name": "Pull-Up",
            "category": "Pull",
            "primary_muscle": "Back",
            "equipment": "Bodyweight",
            "movement_type": "Compound",
        },
        {
            "name": "Overhead Press",
            "category": "Push",
            "primary_muscle": "Shoulders",
            "equipment": "Barbell",
            "movement_type": "Compound",
        },
    ]

    exercise_ids = []
    with db.get_connection() as conn:
        for ex in exercises:
            result = conn.execute(
                """
                INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id
            """,
                (
                    ex["name"],
                    ex["category"],
                    ex["primary_muscle"],
                    ex["equipment"],
                    ex["movement_type"],
                ),
            ).fetchone()
            exercise_ids.append(result[0])

    return exercise_ids


class TestProgramCRUD:
    """Test program CRUD operations."""

    def test_create_program(self, service):
        """Test creating a program."""
        program = service.create_program(
            ProgramCreate(
                name="Test PPL",
                description="Test program",
                split_type=SplitType.PPL,
                days_per_week=6,
                duration_weeks=12,
            )
        )

        assert program.id is not None
        assert program.name == "Test PPL"
        assert program.description == "Test program"
        assert program.split_type == SplitType.PPL
        assert program.days_per_week == 6
        assert program.duration_weeks == 12
        assert program.is_active is False

    def test_create_program_duplicate_name(self, service):
        """Test creating a program with duplicate name fails."""
        service.create_program(
            ProgramCreate(
                name="Test PPL",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        with pytest.raises(ValueError, match="already exists"):
            service.create_program(
                ProgramCreate(
                    name="Test PPL",
                    split_type=SplitType.PPL,
                    days_per_week=6,
                )
            )

    def test_get_all_programs(self, service):
        """Test getting all programs."""
        # Create multiple programs
        service.create_program(
            ProgramCreate(
                name="PPL",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )
        service.create_program(
            ProgramCreate(
                name="Upper Lower",
                split_type=SplitType.UPPER_LOWER,
                days_per_week=4,
            )
        )

        programs = service.get_all_programs()
        assert len(programs) == 2
        assert all(isinstance(p, Program) for p in programs)

    def test_get_program_by_id(self, service):
        """Test getting a program by ID."""
        created = service.create_program(
            ProgramCreate(
                name="Test Program",
                split_type=SplitType.FULL_BODY,
                days_per_week=3,
            )
        )

        program = service.get_program(created.id)
        assert program is not None
        assert program.id == created.id
        assert program.name == created.name

    def test_get_program_not_found(self, service):
        """Test getting a non-existent program returns None."""
        program = service.get_program(9999)
        assert program is None

    def test_get_program_by_name(self, service):
        """Test getting a program by name."""
        service.create_program(
            ProgramCreate(
                name="Test Program",
                split_type=SplitType.FULL_BODY,
                days_per_week=3,
            )
        )

        program = service.get_program_by_name("Test Program")
        assert program is not None
        assert program.name == "Test Program"

    def test_update_program(self, service):
        """Test updating a program."""
        program = service.create_program(
            ProgramCreate(
                name="Old Name",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        updated = service.update_program(
            program.id,
            {
                "name": "New Name",
                "days_per_week": 4,
                "description": "Updated description",
            },
        )

        assert updated.name == "New Name"
        assert updated.days_per_week == 4
        assert updated.description == "Updated description"

    def test_update_program_not_found(self, service):
        """Test updating a non-existent program fails."""
        with pytest.raises(ValueError, match="not found"):
            service.update_program(9999, {"name": "New Name"})

    def test_delete_program(self, service):
        """Test deleting a program."""
        program = service.create_program(
            ProgramCreate(
                name="To Delete",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        success = service.delete_program(program.id)
        assert success is True

        # Verify it's gone
        assert service.get_program(program.id) is None


class TestProgramActivation:
    """Test program activation."""

    def test_activate_program(self, service):
        """Test activating a program."""
        program1 = service.create_program(
            ProgramCreate(
                name="Program 1",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )
        program2 = service.create_program(
            ProgramCreate(
                name="Program 2",
                split_type=SplitType.UPPER_LOWER,
                days_per_week=4,
            )
        )

        # Activate program 1
        activated = service.activate_program(program1.id)
        assert activated.is_active is True

        # Check that program 2 is not active
        program2_check = service.get_program(program2.id)
        assert program2_check.is_active is False

        # Activate program 2
        activated2 = service.activate_program(program2.id)
        assert activated2.is_active is True

        # Check that program 1 is now inactive
        program1_check = service.get_program(program1.id)
        assert program1_check.is_active is False

    def test_get_active_program(self, service):
        """Test getting the active program."""
        # Initially no active program
        assert service.get_active_program() is None

        program = service.create_program(
            ProgramCreate(
                name="Test Program",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        service.activate_program(program.id)

        active = service.get_active_program()
        assert active is not None
        assert active.id == program.id


class TestWorkoutManagement:
    """Test workout management."""

    def test_add_workout_to_program(self, service):
        """Test adding a workout to a program."""
        program = service.create_program(
            ProgramCreate(
                name="Test Program",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        workout = service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Push Day",
                day_number=1,
                description="Heavy push day",
                estimated_duration_minutes=75,
            ),
        )

        assert workout.id is not None
        assert workout.program_id == program.id
        assert workout.name == "Push Day"
        assert workout.day_number == 1

    def test_add_workout_invalid_program(self, service):
        """Test adding workout to non-existent program fails."""
        with pytest.raises(ValueError, match="not found"):
            service.add_workout_to_program(
                9999,
                ProgramWorkoutCreate(
                    program_id=9999,
                    name="Push Day",
                ),
            )

    def test_get_program_workouts(self, service):
        """Test getting workouts for a program."""
        program = service.create_program(
            ProgramCreate(
                name="Test Program",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        # Add multiple workouts
        service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Push Day",
                day_number=1,
            ),
        )
        service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Pull Day",
                day_number=2,
            ),
        )

        workouts = service.get_program_workouts(program.id)
        assert len(workouts) == 2
        assert workouts[0].name == "Push Day"
        assert workouts[1].name == "Pull Day"


class TestExerciseManagement:
    """Test exercise management."""

    def test_add_exercise_to_workout(self, service, sample_exercises):
        """Test adding an exercise to a workout."""
        program = service.create_program(
            ProgramCreate(
                name="Test Program",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        workout = service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Push Day",
            ),
        )

        exercise = service.add_exercise_to_workout(
            workout.id,
            ProgramExerciseCreate(
                program_workout_id=workout.id,
                exercise_id=sample_exercises[0],
                order_number=1,
                target_sets=4,
                target_reps_min=8,
                target_reps_max=10,
                target_rpe=Decimal("8.5"),
                rest_seconds=120,
            ),
        )

        assert exercise.id is not None
        assert exercise.program_workout_id == workout.id
        assert exercise.exercise_id == sample_exercises[0]
        assert exercise.target_sets == 4
        assert exercise.target_reps_min == 8
        assert exercise.target_reps_max == 10

    def test_add_exercise_invalid_workout(self, service, sample_exercises):
        """Test adding exercise to non-existent workout fails."""
        with pytest.raises(ValueError, match="Workout.*not found"):
            service.add_exercise_to_workout(
                9999,
                ProgramExerciseCreate(
                    program_workout_id=9999,
                    exercise_id=sample_exercises[0],
                    order_number=1,
                    target_sets=3,
                    target_reps_min=8,
                    target_reps_max=10,
                ),
            )

    def test_add_exercise_invalid_exercise_id(self, service):
        """Test adding non-existent exercise fails."""
        program = service.create_program(
            ProgramCreate(
                name="Test Program",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        workout = service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Push Day",
            ),
        )

        with pytest.raises(ValueError, match="Exercise.*not found"):
            service.add_exercise_to_workout(
                workout.id,
                ProgramExerciseCreate(
                    program_workout_id=workout.id,
                    exercise_id=9999,
                    order_number=1,
                    target_sets=3,
                    target_reps_min=8,
                    target_reps_max=10,
                ),
            )

    def test_get_workout_exercises(self, service, sample_exercises):
        """Test getting exercises for a workout."""
        program = service.create_program(
            ProgramCreate(
                name="Test Program",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        workout = service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Push Day",
            ),
        )

        # Add multiple exercises
        for i, ex_id in enumerate(sample_exercises[:3], 1):
            service.add_exercise_to_workout(
                workout.id,
                ProgramExerciseCreate(
                    program_workout_id=workout.id,
                    exercise_id=ex_id,
                    order_number=i,
                    target_sets=3,
                    target_reps_min=8,
                    target_reps_max=10,
                ),
            )

        exercises = service.get_workout_exercises(workout.id)
        assert len(exercises) == 3

        # Verify structure
        for ex_data in exercises:
            assert "program_exercise" in ex_data
            assert "exercise_name" in ex_data
            assert "exercise_category" in ex_data
            assert ex_data["exercise_name"] in [
                "Barbell Bench Press",
                "Barbell Squat",
                "Pull-Up",
            ]


class TestProgramCloning:
    """Test program cloning."""

    def test_clone_program(self, service, sample_exercises):
        """Test cloning a complete program."""
        # Create original program with workouts and exercises
        program = service.create_program(
            ProgramCreate(
                name="Original Program",
                description="Original description",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        workout1 = service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Push Day",
                day_number=1,
            ),
        )

        workout2 = service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Pull Day",
                day_number=2,
            ),
        )

        # Add exercises to workouts
        service.add_exercise_to_workout(
            workout1.id,
            ProgramExerciseCreate(
                program_workout_id=workout1.id,
                exercise_id=sample_exercises[0],
                order_number=1,
                target_sets=4,
                target_reps_min=8,
                target_reps_max=10,
            ),
        )

        service.add_exercise_to_workout(
            workout2.id,
            ProgramExerciseCreate(
                program_workout_id=workout2.id,
                exercise_id=sample_exercises[2],
                order_number=1,
                target_sets=3,
                target_reps_min=8,
                target_reps_max=10,
            ),
        )

        # Clone the program
        cloned = service.clone_program(program.id, "Cloned Program")

        assert cloned.id != program.id
        assert cloned.name == "Cloned Program"
        assert cloned.description == program.description
        assert cloned.split_type == program.split_type

        # Verify workouts were cloned
        cloned_workouts = service.get_program_workouts(cloned.id)
        assert len(cloned_workouts) == 2

        # Verify exercises were cloned
        for workout in cloned_workouts:
            exercises = service.get_workout_exercises(workout.id)
            assert len(exercises) >= 1

    def test_clone_program_duplicate_name(self, service):
        """Test cloning with duplicate name fails."""
        program = service.create_program(
            ProgramCreate(
                name="Original",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        service.create_program(
            ProgramCreate(
                name="Existing",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        with pytest.raises(ValueError, match="already exists"):
            service.clone_program(program.id, "Existing")


class TestSeedPrograms:
    """Test loading seed programs."""

    def test_load_seed_programs(self, service, sample_exercises, db):
        """Test loading programs from JSON."""
        # Create a temporary JSON file
        programs_data = {
            "programs": [
                {
                    "name": "Test PPL",
                    "description": "Test program",
                    "split_type": "PPL",
                    "days_per_week": 6,
                    "workouts": [
                        {
                            "name": "Push Day",
                            "day_number": 1,
                            "exercises": [
                                {
                                    "exercise_name": "Barbell Bench Press",
                                    "order_number": 1,
                                    "target_sets": 4,
                                    "target_reps_min": 8,
                                    "target_reps_max": 10,
                                    "target_rpe": 8.5,
                                    "rest_seconds": 120,
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(programs_data, f)
            temp_file = f.name

        try:
            count = service.load_seed_programs(temp_file)
            assert count == 1

            # Verify program was created
            program = service.get_program_by_name("Test PPL")
            assert program is not None
            assert program.split_type == SplitType.PPL

            # Verify workouts were created
            workouts = service.get_program_workouts(program.id)
            assert len(workouts) == 1

            # Verify exercises were created
            exercises = service.get_workout_exercises(workouts[0].id)
            assert len(exercises) == 1

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_load_seed_programs_skip_existing(self, service, sample_exercises):
        """Test that existing programs are skipped."""
        # Create a program first
        service.create_program(
            ProgramCreate(
                name="Existing Program",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )

        programs_data = {
            "programs": [
                {
                    "name": "Existing Program",
                    "split_type": "PPL",
                    "days_per_week": 6,
                    "workouts": [],
                },
                {
                    "name": "New Program",
                    "split_type": "Upper/Lower",
                    "days_per_week": 4,
                    "workouts": [],
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(programs_data, f)
            temp_file = f.name

        try:
            count = service.load_seed_programs(temp_file)
            # Should only load the new program
            assert count == 1

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_load_seed_programs_file_not_found(self, service):
        """Test loading from non-existent file fails."""
        with pytest.raises(FileNotFoundError):
            service.load_seed_programs("/nonexistent/file.json")
