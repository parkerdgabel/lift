"""
Integration tests for cross-slice functionality.

Tests interactions between different feature slices.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from lift.core.database import DatabaseManager
from lift.core.models import (
    CategoryType,
    EquipmentType,
    ExerciseCreate,
    MovementType,
    MuscleGroup,
    SetCreate,
    SetType,
    WeightUnit,
    WorkoutCreate,
)
from lift.services.body_service import BodyService
from lift.services.config_service import ConfigService
from lift.services.exercise_service import ExerciseService
from lift.services.pr_service import PRService
from lift.services.program_service import ProgramService
from lift.services.set_service import SetService
from lift.services.stats_service import StatsService
from lift.services.workout_service import WorkoutService


@pytest.fixture()
def db() -> DatabaseManager:
    """Create a temporary in-memory database for testing."""
    db = DatabaseManager(":memory:")
    db.initialize_database()
    return db


@pytest.fixture()
def loaded_db(db: DatabaseManager) -> DatabaseManager:
    """Database with exercises and config pre-loaded."""
    exercise_service = ExerciseService(db)

    # Load 5 basic exercises
    exercises = [
        ("Bench Press", CategoryType.PUSH, MuscleGroup.CHEST, EquipmentType.BARBELL),
        ("Squat", CategoryType.LEGS, MuscleGroup.QUADS, EquipmentType.BARBELL),
        ("Deadlift", CategoryType.PULL, MuscleGroup.BACK, EquipmentType.BARBELL),
        ("Overhead Press", CategoryType.PUSH, MuscleGroup.SHOULDERS, EquipmentType.BARBELL),
        ("Barbell Row", CategoryType.PULL, MuscleGroup.BACK, EquipmentType.BARBELL),
    ]

    for name, category, muscle, equipment in exercises:
        exercise_service.create(
            ExerciseCreate(
                name=name,
                category=category,
                primary_muscle=muscle,
                equipment=equipment,
                movement_type=MovementType.COMPOUND,
            )
        )

    return db


class TestConfigServiceIntegration:
    """Test how configuration affects other services."""

    def test_weight_unit_config_affects_body_service(self, loaded_db: DatabaseManager) -> None:
        """Test that weight unit configuration is respected by body service."""
        config_service = ConfigService(loaded_db)
        body_service = BodyService(loaded_db)

        # Set to kg
        config_service.set_setting("default_weight_unit", "kg")
        assert config_service.get_default_weight_unit() == WeightUnit.KG

        # Log weight (should default to kg based on config)
        measurement = body_service.log_weight(Decimal("80.0"), WeightUnit.KG)
        assert measurement.weight_unit == "kg"
        assert measurement.weight == Decimal("80.0")

    def test_rpe_config_affects_workout_logging(self, loaded_db: DatabaseManager) -> None:
        """Test that RPE config is respected."""
        config_service = ConfigService(loaded_db)

        # RPE should be enabled by default
        assert config_service.is_rpe_enabled() is True

        # Disable RPE
        config_service.set_setting("enable_rpe", "false")
        assert config_service.is_rpe_enabled() is False


class TestExerciseWorkoutIntegration:
    """Test exercise and workout integration."""

    def test_exercise_deletion_prevents_workout_creation(self, loaded_db: DatabaseManager) -> None:
        """Test that deleting an exercise affects workout capability."""
        exercise_service = ExerciseService(loaded_db)

        # Create custom exercise
        custom_ex = exercise_service.create(
            ExerciseCreate(
                name="Custom Lift",
                category=CategoryType.PUSH,
                primary_muscle=MuscleGroup.CHEST,
                equipment=EquipmentType.BARBELL,
                movement_type=MovementType.COMPOUND,
                is_custom=True,
            )
        )

        # Delete it
        deleted = exercise_service.delete(custom_ex.id)
        assert deleted is True

        # Try to get it back
        retrieved = exercise_service.get_by_id(custom_ex.id)
        assert retrieved is None

    def test_workout_uses_exercise_data(self, loaded_db: DatabaseManager) -> None:
        """Test that workouts properly reference exercise data."""
        exercise_service = ExerciseService(db=loaded_db)
        workout_service = WorkoutService(loaded_db)
        set_service = SetService(loaded_db)

        # Get an exercise
        bench = exercise_service.get_by_name("Bench Press")
        assert bench is not None

        # Create workout with sets
        workout = workout_service.create_workout(WorkoutCreate(name="Push Day"))

        set_service.add_set(
            SetCreate(
                workout_id=workout.id,
                exercise_id=bench.id,
                set_number=1,
                weight=Decimal("185"),
                reps=10,
                set_type=SetType.WORKING,
            )
        )

        # Verify we can query sets by exercise
        sets = set_service.get_sets_for_exercise(bench.id)
        assert len(sets) == 1
        assert sets[0].exercise_id == bench.id


class TestWorkoutStatsIntegration:
    """Test workout and stats integration."""

    def test_workout_volume_appears_in_stats(self, loaded_db: DatabaseManager) -> None:
        """Test that logged workouts appear in statistics."""
        exercise_service = ExerciseService(loaded_db)
        workout_service = WorkoutService(loaded_db)
        set_service = SetService(loaded_db)
        stats_service = StatsService(loaded_db)

        bench = exercise_service.get_by_name("Bench Press")
        assert bench is not None

        # Initial stats should be empty
        initial_summary = stats_service.get_workout_summary()
        assert initial_summary["total_workouts"] == 0

        # Log a workout
        workout = workout_service.create_workout(WorkoutCreate(name="Test"))

        set_service.add_set(
            SetCreate(
                workout_id=workout.id,
                exercise_id=bench.id,
                set_number=1,
                weight=Decimal("200"),
                reps=10,
                set_type=SetType.WORKING,
            )
        )

        workout_service.finish_workout(workout.id, duration_minutes=60)

        # Stats should update
        summary = stats_service.get_workout_summary()
        assert summary["total_workouts"] == 1
        assert summary["total_sets"] == 1
        assert summary["total_volume"] == Decimal("2000")  # 200 * 10

    def test_muscle_volume_breakdown_from_workouts(self, loaded_db: DatabaseManager) -> None:
        """Test that muscle volume breakdown aggregates correctly."""
        exercise_service = ExerciseService(loaded_db)
        workout_service = WorkoutService(loaded_db)
        set_service = SetService(loaded_db)
        stats_service = StatsService(loaded_db)

        # Get exercises for different muscle groups
        bench = exercise_service.get_by_name("Bench Press")
        squat = exercise_service.get_by_name("Squat")

        # Create workout
        workout = workout_service.create_workout(WorkoutCreate(name="Full Body"))

        # Log chest work
        set_service.add_set(
            SetCreate(
                workout_id=workout.id,
                exercise_id=bench.id,
                set_number=1,
                weight=Decimal("185"),
                reps=10,
                set_type=SetType.WORKING,
            )
        )

        # Log leg work
        set_service.add_set(
            SetCreate(
                workout_id=workout.id,
                exercise_id=squat.id,
                set_number=1,
                weight=Decimal("225"),
                reps=10,
                set_type=SetType.WORKING,
            )
        )

        # Get breakdown
        breakdown = stats_service.get_muscle_volume_breakdown()

        assert MuscleGroup.CHEST.value in breakdown
        assert MuscleGroup.QUADS.value in breakdown
        assert breakdown[MuscleGroup.CHEST.value] == Decimal("1850")
        assert breakdown[MuscleGroup.QUADS.value] == Decimal("2250")


class TestWorkoutPRIntegration:
    """Test workout and PR detection integration."""

    def test_pr_auto_detection_after_workout(self, loaded_db: DatabaseManager) -> None:
        """Test that PRs are automatically detected after workouts."""
        exercise_service = ExerciseService(loaded_db)
        workout_service = WorkoutService(loaded_db)
        set_service = SetService(loaded_db)
        pr_service = PRService(loaded_db)

        bench = exercise_service.get_by_name("Bench Press")
        assert bench is not None

        # Create first workout
        workout1 = workout_service.create_workout(WorkoutCreate(name="Week 1"))

        set_service.add_set(
            SetCreate(
                workout_id=workout1.id,
                exercise_id=bench.id,
                set_number=1,
                weight=Decimal("185"),
                reps=10,
                set_type=SetType.WORKING,
            )
        )

        workout_service.finish_workout(workout1.id, duration_minutes=60)

        # Detect PRs
        prs1 = pr_service.auto_detect_prs(workout1.id)
        assert len(prs1) > 0  # First workout creates initial PRs

        # Create second workout with heavier weight
        workout2 = workout_service.create_workout(WorkoutCreate(name="Week 2"))

        set_service.add_set(
            SetCreate(
                workout_id=workout2.id,
                exercise_id=bench.id,
                set_number=1,
                weight=Decimal("195"),
                reps=10,
                set_type=SetType.WORKING,
            )
        )

        workout_service.finish_workout(workout2.id, duration_minutes=60)

        # Should detect new PRs
        prs2 = pr_service.auto_detect_prs(workout2.id)
        assert len(prs2) > 0

        # Get all PRs for the exercise
        all_prs = pr_service.get_all_prs(exercise_id=bench.id)
        assert len(all_prs) > 0

    def test_volume_pr_detection(self, loaded_db: DatabaseManager) -> None:
        """Test that volume PRs are detected correctly."""
        exercise_service = ExerciseService(loaded_db)
        workout_service = WorkoutService(loaded_db)
        set_service = SetService(loaded_db)
        pr_service = PRService(loaded_db)

        squat = exercise_service.get_by_name("Squat")
        assert squat is not None

        # First workout - moderate volume
        workout1 = workout_service.create_workout(WorkoutCreate(name="Leg Day 1"))

        for i in range(1, 4):
            set_service.add_set(
                SetCreate(
                    workout_id=workout1.id,
                    exercise_id=squat.id,
                    set_number=i,
                    weight=Decimal("225"),
                    reps=8,
                    set_type=SetType.WORKING,
                )
            )

        prs1 = pr_service.auto_detect_prs(workout1.id)

        # Second workout - higher volume (more reps)
        workout2 = workout_service.create_workout(WorkoutCreate(name="Leg Day 2"))

        for i in range(1, 4):
            set_service.add_set(
                SetCreate(
                    workout_id=workout2.id,
                    exercise_id=squat.id,
                    set_number=i,
                    weight=Decimal("225"),
                    reps=12,  # More reps = more volume
                    set_type=SetType.WORKING,
                )
            )

        prs2 = pr_service.auto_detect_prs(workout2.id)

        # Should detect volume PR
        from lift.core.models import RecordType

        volume_prs = [pr for pr in prs2 if pr.record_type == RecordType.VOLUME]
        assert len(volume_prs) > 0


class TestProgramWorkoutIntegration:
    """Test program and workout integration."""

    def test_workout_from_program_template(self, loaded_db: DatabaseManager) -> None:
        """Test creating workouts from program templates."""
        exercise_service = ExerciseService(loaded_db)
        program_service = ProgramService(loaded_db)
        workout_service = WorkoutService(loaded_db)

        bench = exercise_service.get_by_name("Bench Press")
        squat = exercise_service.get_by_name("Squat")

        # Create program
        from lift.core.models import (
            ProgramCreate,
            ProgramExerciseCreate,
            ProgramWorkoutCreate,
            SplitType,
        )

        program = program_service.create_program(
            ProgramCreate(
                name="Test Program",
                split_type=SplitType.UPPER_LOWER,
                days_per_week=4,
            )
        )

        # Create workout template
        upper_template = program_service.add_workout_to_program(
            program.id,
            ProgramWorkoutCreate(
                program_id=program.id,
                name="Upper A",
                day_number=1,
            ),
        )

        # Add exercises to template
        program_service.add_exercise_to_workout(
            upper_template.id,
            ProgramExerciseCreate(
                program_workout_id=upper_template.id,
                exercise_id=bench.id,
                order_number=1,
                target_sets=4,
                target_reps_min=8,
                target_reps_max=10,
            ),
        )

        # Create actual workout from template
        workout = workout_service.create_workout(
            WorkoutCreate(
                name="Upper A - Week 1",
                program_workout_id=upper_template.id,
            )
        )

        # Verify linkage
        assert workout.program_workout_id == upper_template.id

        # Get exercises from template
        template_exercises = program_service.get_workout_exercises(upper_template.id)
        assert len(template_exercises) == 1
        assert template_exercises[0]["exercise_name"] == "Bench Press"


class TestBodyTrackingIntegration:
    """Test body tracking integration with workouts."""

    def test_bodyweight_in_workout_and_body_service(self, loaded_db: DatabaseManager) -> None:
        """Test that bodyweight can be tracked via workouts and body service."""
        workout_service = WorkoutService(loaded_db)
        body_service = BodyService(loaded_db)

        # Log bodyweight via body service
        body_service.log_weight(Decimal("180.0"))

        # Log workout with bodyweight
        workout = workout_service.create_workout(
            WorkoutCreate(
                name="Test Workout",
                bodyweight=Decimal("181.5"),
            )
        )

        # Both should be tracked independently
        latest_weight = body_service.get_latest_weight()
        assert latest_weight is not None
        assert latest_weight[0] == Decimal("180.0")

        retrieved_workout = workout_service.get_workout(workout.id)
        assert retrieved_workout is not None
        assert retrieved_workout.bodyweight == Decimal("181.5")


class TestExportImportIntegration:
    """Test data export/import across services."""

    def test_export_and_verify_all_data(self, loaded_db: DatabaseManager) -> None:
        """Test that export captures data from all services."""
        import json
        import tempfile
        from pathlib import Path

        from lift.services.export_service import ExportService

        # Create some data across services
        exercise_service = ExerciseService(loaded_db)
        workout_service = WorkoutService(loaded_db)
        set_service = SetService(loaded_db)
        body_service = BodyService(loaded_db)

        # Exercise data (already loaded in fixture)
        exercises = exercise_service.get_all()
        assert len(exercises) > 0

        # Workout data
        bench = exercise_service.get_by_name("Bench Press")
        workout = workout_service.create_workout(WorkoutCreate(name="Test"))
        set_service.add_set(
            SetCreate(
                workout_id=workout.id,
                exercise_id=bench.id,
                set_number=1,
                weight=Decimal("185"),
                reps=10,
                set_type=SetType.WORKING,
            )
        )

        # Body data
        body_service.log_weight(Decimal("180.0"))

        # Export all data
        export_service = ExportService(loaded_db)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            export_path = f.name

        try:
            export_service.export_all_to_json(export_path)

            # Verify export has all data
            with open(export_path) as f:
                data = json.load(f)

            assert "exercises" in data
            assert "workouts" in data
            assert "sets" in data
            assert "body_measurements" in data

            assert len(data["exercises"]) == len(exercises)
            assert len(data["workouts"]) == 1
            assert len(data["sets"]) == 1
            assert len(data["body_measurements"]) == 1

        finally:
            Path(export_path).unlink(missing_ok=True)


class TestMultiWeekProgression:
    """Test progression tracking over multiple weeks."""

    def test_progression_over_weeks(self, loaded_db: DatabaseManager) -> None:
        """Test tracking and analyzing progression over several weeks."""
        exercise_service = ExerciseService(loaded_db)
        workout_service = WorkoutService(loaded_db)
        set_service = SetService(loaded_db)
        stats_service = StatsService(loaded_db)

        bench = exercise_service.get_by_name("Bench Press")

        # Simulate 4 weeks of training with progression
        base_date = datetime.now() - timedelta(days=28)

        for week in range(4):
            workout_date = base_date + timedelta(days=week * 7)
            weight = Decimal(str(185 + (week * 5)))  # +5 lbs per week

            workout = workout_service.create_workout(
                WorkoutCreate(
                    name=f"Bench Day - Week {week + 1}",
                    date=workout_date,
                )
            )

            # Log 3 sets
            for set_num in range(1, 4):
                set_service.add_set(
                    SetCreate(
                        workout_id=workout.id,
                        exercise_id=bench.id,
                        set_number=set_num,
                        weight=weight,
                        reps=10,
                        rpe=Decimal("8.0"),
                        set_type=SetType.WORKING,
                    )
                )

            workout_service.finish_workout(workout.id, duration_minutes=60)

        # Analyze progression
        progression = stats_service.get_exercise_progression(bench.id, limit=10)

        # Should have data from all 4 weeks
        unique_weights = {p["weight"] for p in progression}
        assert len(unique_weights) == 4

        # Weights should increase (progression is ordered DESC by date)
        weights = [p["weight"] for p in progression]
        assert weights[0] == Decimal("200")  # Most recent (week 4)
        assert weights[-1] == Decimal("185")  # Oldest (week 1)

        # Get weekly summary
        weekly = stats_service.get_weekly_summary(weeks_back=5)
        assert len(weekly) >= 4

        # Volume should increase week over week
        volumes = [w["total_volume"] for w in weekly if w["total_volume"] > 0]
        assert len(volumes) == 4
