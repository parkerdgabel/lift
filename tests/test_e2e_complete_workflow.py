"""
End-to-end tests for complete user workflows.

These tests verify that all slices work together properly in realistic scenarios.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Generator

import pytest

from lift.core.database import DatabaseManager
from lift.core.models import (
    CategoryType,
    EquipmentType,
    ExerciseCreate,
    MuscleGroup,
    MovementType,
    SetType,
    WeightUnit,
)
from lift.services.body_service import BodyService
from lift.services.config_service import ConfigService
from lift.services.exercise_service import ExerciseService
from lift.services.pr_service import PRService
from lift.services.program_service import ProgramService
from lift.services.set_service import SetService
from lift.services.stats_service import StatsService
from lift.services.workout_service import WorkoutService


@pytest.fixture
def db() -> Generator[DatabaseManager, None, None]:
    """Create a temporary in-memory database for testing."""
    db = DatabaseManager(":memory:")
    db.initialize_database()
    yield db


class TestCompleteUserJourney:
    """Test a complete user journey from setup to analysis."""

    def test_new_user_complete_workflow(self, db: DatabaseManager) -> None:
        """
        Test complete workflow for a new user:
        1. Initialize database
        2. Load exercise library
        3. Create a training program
        4. Log multiple workouts
        5. Track body measurements
        6. View statistics and PRs
        7. Export data
        """
        # Step 1: Load exercises
        exercise_service = ExerciseService(db)

        # Create some exercises manually (simulating seed data)
        exercises_data = [
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
                "name": "Barbell Row",
                "category": CategoryType.PULL,
                "primary_muscle": MuscleGroup.BACK,
                "secondary_muscles": [MuscleGroup.BICEPS],
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
        ]

        exercise_ids = {}
        for ex_data in exercises_data:
            exercise = exercise_service.create(ExerciseCreate(**ex_data))
            exercise_ids[exercise.name] = exercise.id

        # Verify exercises loaded
        all_exercises = exercise_service.get_all()
        assert len(all_exercises) == 4

        # Step 2: Configure settings
        config_service = ConfigService(db)
        config_service.set_setting("default_weight_unit", "lbs")
        config_service.set_setting("enable_rpe", "true")

        assert config_service.get_default_weight_unit() == WeightUnit.LBS
        assert config_service.is_rpe_enabled() is True

        # Step 3: Log initial body weight
        body_service = BodyService(db)
        initial_weight = body_service.log_weight(Decimal("180.0"))
        assert initial_weight.weight == Decimal("180.0")

        # Step 4: Create a simple program
        program_service = ProgramService(db)
        from lift.core.models import ProgramCreate, SplitType

        program = program_service.create_program(
            ProgramCreate(
                name="Test PPL",
                description="Push Pull Legs for testing",
                split_type=SplitType.PPL,
                days_per_week=6,
            )
        )
        assert program.id is not None

        # Add a Push workout to the program
        from lift.core.models import ProgramWorkoutCreate

        push_workout = program_service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Push A",
                day_number=1,
                description="Chest and shoulders focus",
            ),
        )

        # Add exercises to the workout
        from lift.core.models import ProgramExerciseCreate

        program_service.add_exercise_to_workout(
            push_workout.id,
            ProgramExerciseCreate(
                program_workout_id=push_workout.id,
                exercise_id=exercise_ids["Barbell Bench Press"],
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
                exercise_id=exercise_ids["Overhead Press"],
                order_number=2,
                target_sets=3,
                target_reps_min=8,
                target_reps_max=12,
                target_rpe=Decimal("8.0"),
                rest_seconds=120,
            ),
        )

        # Verify program structure
        workouts = program_service.get_program_workouts(program.id)
        assert len(workouts) == 1

        exercises = program_service.get_workout_exercises(push_workout.id)
        assert len(exercises) == 2

        # Step 5: Log first workout (Week 1)
        workout_service = WorkoutService(db)
        set_service = SetService(db)

        from lift.core.models import WorkoutCreate

        workout1 = workout_service.create_workout(
            WorkoutCreate(
                name="Push A - Week 1",
                program_workout_id=push_workout.id,
                date=datetime.now() - timedelta(days=14),  # 2 weeks ago
                bodyweight=Decimal("180.0"),
            )
        )

        # Log sets for bench press
        from lift.core.models import SetCreate

        bench_sets = [
            (Decimal("185"), 10, Decimal("8.0")),
            (Decimal("185"), 10, Decimal("8.5")),
            (Decimal("185"), 9, Decimal("9.0")),
            (Decimal("185"), 8, Decimal("9.5")),
        ]

        for i, (weight, reps, rpe) in enumerate(bench_sets, 1):
            set_service.add_set(
                SetCreate(
                    workout_id=workout1.id,
                    exercise_id=exercise_ids["Barbell Bench Press"],
                    set_number=i,
                    weight=weight,
                    reps=reps,
                    rpe=rpe,
                    set_type=SetType.WORKING,
                )
            )

        # Log sets for overhead press
        ohp_sets = [
            (Decimal("115"), 10, Decimal("8.0")),
            (Decimal("115"), 9, Decimal("8.5")),
            (Decimal("115"), 8, Decimal("9.0")),
        ]

        for i, (weight, reps, rpe) in enumerate(ohp_sets, 1):
            set_service.add_set(
                SetCreate(
                    workout_id=workout1.id,
                    exercise_id=exercise_ids["Overhead Press"],
                    set_number=i,
                    weight=weight,
                    reps=reps,
                    rpe=rpe,
                    set_type=SetType.WORKING,
                )
            )

        # Finish workout
        workout_service.finish_workout(workout1.id, duration_minutes=65)

        # Step 6: Check PRs after first workout
        pr_service = PRService(db)
        new_prs = pr_service.auto_detect_prs(workout1.id)

        # First workout should create PRs
        assert len(new_prs) > 0

        # Step 7: Log second workout (Week 2) with progression
        workout2 = workout_service.create_workout(
            WorkoutCreate(
                name="Push A - Week 2",
                program_workout_id=push_workout.id,
                date=datetime.now() - timedelta(days=7),  # 1 week ago
                bodyweight=Decimal("181.5"),
            )
        )

        # Progressive overload - increased weight
        bench_sets_week2 = [
            (Decimal("190"), 10, Decimal("8.0")),  # +5 lbs
            (Decimal("190"), 10, Decimal("8.5")),
            (Decimal("190"), 9, Decimal("9.0")),
            (Decimal("190"), 9, Decimal("9.5")),
        ]

        for i, (weight, reps, rpe) in enumerate(bench_sets_week2, 1):
            set_service.add_set(
                SetCreate(
                    workout_id=workout2.id,
                    exercise_id=exercise_ids["Barbell Bench Press"],
                    set_number=i,
                    weight=weight,
                    reps=reps,
                    rpe=rpe,
                    set_type=SetType.WORKING,
                )
            )

        workout_service.finish_workout(workout2.id, duration_minutes=68)

        # Check for new PRs
        new_prs_week2 = pr_service.auto_detect_prs(workout2.id)
        assert len(new_prs_week2) > 0  # Should have new PRs from increased weight

        # Step 8: Log third workout (Week 3)
        workout3 = workout_service.create_workout(
            WorkoutCreate(
                name="Push A - Week 3",
                program_workout_id=push_workout.id,
                date=datetime.now(),
                bodyweight=Decimal("182.5"),
            )
        )

        # Further progression
        bench_sets_week3 = [
            (Decimal("195"), 10, Decimal("8.5")),  # +5 lbs again
            (Decimal("195"), 10, Decimal("9.0")),
            (Decimal("195"), 9, Decimal("9.5")),
            (Decimal("195"), 8, Decimal("10.0")),  # Pushed to failure
        ]

        for i, (weight, reps, rpe) in enumerate(bench_sets_week3, 1):
            set_service.add_set(
                SetCreate(
                    workout_id=workout3.id,
                    exercise_id=exercise_ids["Barbell Bench Press"],
                    set_number=i,
                    weight=weight,
                    reps=reps,
                    rpe=rpe,
                    set_type=SetType.WORKING if i < 4 else SetType.FAILURE,
                )
            )

        workout_service.finish_workout(workout3.id, duration_minutes=70)

        # Step 9: Track body measurements over time
        body_service.log_weight(Decimal("182.5"))

        from lift.core.models import BodyMeasurementCreate

        body_service.log_measurement(
            BodyMeasurementCreate(
                weight=Decimal("182.5"),
                chest=Decimal("42.5"),
                waist=Decimal("32.0"),
                bicep_left=Decimal("15.5"),
                bicep_right=Decimal("15.5"),
            )
        )

        # Step 10: Analyze statistics
        stats_service = StatsService(db)

        # Get workout summary
        summary = stats_service.get_workout_summary()
        assert summary["total_workouts"] == 3
        assert summary["total_sets"] > 0
        assert summary["total_volume"] > Decimal("0")

        # Get exercise progression
        progression = stats_service.get_exercise_progression(
            exercise_ids["Barbell Bench Press"], limit=10
        )
        assert len(progression) > 0

        # Verify progression (weights should increase)
        weights = [p["weight"] for p in progression]
        assert weights[0] >= weights[-1]  # Most recent should be >= oldest

        # Get muscle volume breakdown
        volume_breakdown = stats_service.get_muscle_volume_breakdown()
        assert MuscleGroup.CHEST.value in volume_breakdown
        assert volume_breakdown[MuscleGroup.CHEST.value] > Decimal("0")

        # Get weekly summary
        weekly = stats_service.get_weekly_summary(weeks_back=4)
        assert len(weekly) > 0

        # Get all PRs
        all_prs = pr_service.get_all_prs()
        assert len(all_prs) > 0

        # Get PRs for bench press specifically
        bench_prs = pr_service.get_all_prs(exercise_id=exercise_ids["Barbell Bench Press"])
        assert len(bench_prs) > 0

        # Step 11: Check consistency streak
        streak = stats_service.calculate_consistency_streak()
        assert streak > 0  # Should have a streak

        # Step 12: Export data
        from lift.services.export_service import ExportService
        import tempfile

        export_service = ExportService(db)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            export_path = f.name

        try:
            export_service.export_all_to_json(export_path)

            # Verify export file exists and has content
            assert Path(export_path).exists()
            assert Path(export_path).stat().st_size > 0
        finally:
            Path(export_path).unlink(missing_ok=True)

        # Step 13: Verify progression recommendations
        from lift.utils.calculations import suggest_next_weight

        bench_progression = stats_service.get_exercise_progression(
            exercise_ids["Barbell Bench Press"], limit=3
        )

        # Should have workout history
        assert len(bench_progression) >= 3

        # Step 14: Verify body tracking integration
        weight_history = body_service.get_weight_history(weeks_back=4)
        assert len(weight_history) > 0

        # Weight should be trending up (bulking)
        assert weight_history[0]["weight"] >= Decimal("180.0")

    def test_program_based_workout_flow(self, db: DatabaseManager) -> None:
        """Test workflow using a program-based workout."""
        # Setup
        exercise_service = ExerciseService(db)
        program_service = ProgramService(db)
        workout_service = WorkoutService(db)
        set_service = SetService(db)

        # Create exercise
        exercise = exercise_service.create(
            ExerciseCreate(
                name="Deadlift",
                category=CategoryType.PULL,
                primary_muscle=MuscleGroup.BACK,
                secondary_muscles=[MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES],
                equipment=EquipmentType.BARBELL,
                movement_type=MovementType.COMPOUND,
            )
        )

        # Create program
        from lift.core.models import ProgramCreate, ProgramWorkoutCreate, ProgramExerciseCreate, SplitType

        program = program_service.create_program(
            ProgramCreate(
                name="Deadlift Program",
                split_type=SplitType.CUSTOM,
                days_per_week=3,
            )
        )

        # Add workout template
        workout_template = program_service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Deadlift Day",
                day_number=1,
            ),
        )

        # Add exercise to template
        program_service.add_exercise_to_workout(
            workout_template.id,
            ProgramExerciseCreate(
                program_workout_id=workout_template.id,
                exercise_id=exercise.id,
                order_number=1,
                target_sets=5,
                target_reps_min=3,
                target_reps_max=5,
                target_rpe=Decimal("9.0"),
                rest_seconds=240,
            ),
        )

        # Create workout from template
        from lift.core.models import WorkoutCreate

        workout = workout_service.create_workout(
            WorkoutCreate(
                name="Deadlift Day",
                program_workout_id=workout_template.id,
            )
        )

        # Log sets following the program prescription
        from lift.core.models import SetCreate

        for set_num in range(1, 6):  # 5 sets as prescribed
            set_service.add_set(
                SetCreate(
                    workout_id=workout.id,
                    exercise_id=exercise.id,
                    set_number=set_num,
                    weight=Decimal("315"),
                    reps=5 if set_num < 5 else 3,  # Drop reps on last set
                    rpe=Decimal("9.0") if set_num < 5 else Decimal("9.5"),
                    set_type=SetType.WORKING,
                )
            )

        # Finish workout
        workout_service.finish_workout(workout.id, duration_minutes=45)

        # Verify workout summary
        summary = workout_service.get_workout_summary(workout.id)
        assert summary["total_sets"] == 5
        assert summary["total_exercises"] == 1
        assert summary["total_volume"] > Decimal("0")

        # Verify it's linked to the program
        retrieved_workout = workout_service.get_workout(workout.id)
        assert retrieved_workout is not None
        assert retrieved_workout.program_workout_id == workout_template.id

    def test_cross_slice_data_consistency(self, db: DatabaseManager) -> None:
        """Test that data remains consistent across all slices."""
        # Create exercise
        exercise_service = ExerciseService(db)
        exercise = exercise_service.create(
            ExerciseCreate(
                name="Squat",
                category=CategoryType.LEGS,
                primary_muscle=MuscleGroup.QUADS,
                equipment=EquipmentType.BARBELL,
                movement_type=MovementType.COMPOUND,
            )
        )

        # Log workout with sets
        workout_service = WorkoutService(db)
        set_service = SetService(db)

        from lift.core.models import WorkoutCreate, SetCreate

        workout = workout_service.create_workout(
            WorkoutCreate(name="Leg Day", bodyweight=Decimal("175.0"))
        )

        # Log 3 sets
        for i in range(1, 4):
            set_service.add_set(
                SetCreate(
                    workout_id=workout.id,
                    exercise_id=exercise.id,
                    set_number=i,
                    weight=Decimal("225"),
                    reps=10,
                    rpe=Decimal("8.0"),
                    set_type=SetType.WORKING,
                )
            )

        workout_service.finish_workout(workout.id, duration_minutes=60)

        # Verify stats service sees the data
        stats_service = StatsService(db)
        summary = stats_service.get_workout_summary()
        assert summary["total_workouts"] == 1
        assert summary["total_sets"] == 3

        # Verify PR service can detect PRs
        pr_service = PRService(db)
        prs = pr_service.auto_detect_prs(workout.id)
        assert len(prs) > 0

        # Verify export includes the workout
        from lift.services.export_service import ExportService
        import tempfile

        export_service = ExportService(db)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            export_path = f.name

        try:
            export_service.export_to_json("workouts", export_path)

            import json
            with open(export_path) as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["name"] == "Leg Day"
        finally:
            Path(export_path).unlink(missing_ok=True)

        # Delete workout and verify cascade
        workout_service.delete_workout(workout.id)

        # Sets should be deleted (cascade)
        sets = set_service.get_sets_for_workout(workout.id)
        assert len(sets) == 0

        # Workout count should be 0
        summary = stats_service.get_workout_summary()
        assert summary["total_workouts"] == 0
