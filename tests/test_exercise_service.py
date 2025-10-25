"""Tests for ExerciseService."""

import json
import tempfile
from pathlib import Path

import pytest

from lift.core.database import DatabaseManager, reset_db_instance
from lift.core.models import (
    CategoryType,
    EquipmentType,
    ExerciseCreate,
    MovementType,
    MuscleGroup,
)
from lift.services.exercise_service import ExerciseService


@pytest.fixture()
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as f:
        db_path = f.name

    # Reset the global instance to ensure clean state
    reset_db_instance()

    db = DatabaseManager(db_path)
    db.initialize_database()

    yield db

    # Cleanup
    Path(db_path).unlink(missing_ok=True)
    reset_db_instance()


@pytest.fixture()
def service(temp_db):
    """Create an ExerciseService with a test database."""
    return ExerciseService(temp_db)


@pytest.fixture()
def sample_exercise_data():
    """Sample exercise data for testing."""
    return ExerciseCreate(
        name="Test Bench Press",
        category=CategoryType.PUSH,
        primary_muscle=MuscleGroup.CHEST,
        secondary_muscles=[MuscleGroup.TRICEPS, MuscleGroup.SHOULDERS],
        equipment=EquipmentType.BARBELL,
        movement_type=MovementType.COMPOUND,
        is_custom=True,
        instructions="Test instructions",
        video_url="https://example.com/video",
    )


class TestExerciseServiceCreate:
    """Tests for creating exercises."""

    def test_create_exercise(self, service, sample_exercise_data):
        """Test creating a new exercise."""
        exercise = service.create(sample_exercise_data)

        assert exercise.id is not None
        assert exercise.name == sample_exercise_data.name
        assert exercise.category == sample_exercise_data.category
        assert exercise.primary_muscle == sample_exercise_data.primary_muscle
        assert len(exercise.secondary_muscles) == 2
        assert exercise.equipment == sample_exercise_data.equipment
        assert exercise.movement_type == sample_exercise_data.movement_type
        assert exercise.is_custom is True
        assert exercise.instructions == sample_exercise_data.instructions
        assert exercise.video_url == sample_exercise_data.video_url
        assert exercise.created_at is not None

    def test_create_duplicate_exercise_fails(self, service, sample_exercise_data):
        """Test that creating a duplicate exercise raises an error."""
        service.create(sample_exercise_data)

        with pytest.raises(ValueError, match="already exists"):
            service.create(sample_exercise_data)

    def test_create_exercise_without_optional_fields(self, service):
        """Test creating an exercise without optional fields."""
        exercise_data = ExerciseCreate(
            name="Simple Exercise",
            category=CategoryType.PUSH,
            primary_muscle=MuscleGroup.CHEST,
            secondary_muscles=[],
            equipment=EquipmentType.BODYWEIGHT,
            movement_type=MovementType.ISOLATION,
            is_custom=True,
        )

        exercise = service.create(exercise_data)

        assert exercise.id is not None
        assert exercise.name == "Simple Exercise"
        assert exercise.instructions is None
        assert exercise.video_url is None
        assert len(exercise.secondary_muscles) == 0


class TestExerciseServiceRead:
    """Tests for reading exercises."""

    def test_get_by_id(self, service, sample_exercise_data):
        """Test retrieving an exercise by ID."""
        created = service.create(sample_exercise_data)
        retrieved = service.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_by_id_not_found(self, service):
        """Test retrieving a non-existent exercise by ID."""
        result = service.get_by_id(99999)
        assert result is None

    def test_get_by_name(self, service, sample_exercise_data):
        """Test retrieving an exercise by name."""
        service.create(sample_exercise_data)
        retrieved = service.get_by_name("Test Bench Press")

        assert retrieved is not None
        assert retrieved.name == "Test Bench Press"

    def test_get_by_name_case_insensitive(self, service, sample_exercise_data):
        """Test that name search is case-insensitive."""
        service.create(sample_exercise_data)

        # Test various cases
        assert service.get_by_name("test bench press") is not None
        assert service.get_by_name("TEST BENCH PRESS") is not None
        assert service.get_by_name("TeSt BeNcH pReSs") is not None

    def test_get_by_name_not_found(self, service):
        """Test retrieving a non-existent exercise by name."""
        result = service.get_by_name("Non-Existent Exercise")
        assert result is None

    def test_get_all(self, service):
        """Test retrieving all exercises."""
        # Create multiple exercises
        for i in range(3):
            exercise_data = ExerciseCreate(
                name=f"Exercise {i}",
                category=CategoryType.PUSH,
                primary_muscle=MuscleGroup.CHEST,
                secondary_muscles=[],
                equipment=EquipmentType.BARBELL,
                movement_type=MovementType.COMPOUND,
                is_custom=True,
            )
            service.create(exercise_data)

        exercises = service.get_all()
        assert len(exercises) == 3

    def test_get_all_with_category_filter(self, service):
        """Test filtering exercises by category."""
        # Create exercises with different categories
        push_exercise = ExerciseCreate(
            name="Push Exercise",
            category=CategoryType.PUSH,
            primary_muscle=MuscleGroup.CHEST,
            secondary_muscles=[],
            equipment=EquipmentType.BARBELL,
            movement_type=MovementType.COMPOUND,
            is_custom=True,
        )
        pull_exercise = ExerciseCreate(
            name="Pull Exercise",
            category=CategoryType.PULL,
            primary_muscle=MuscleGroup.BACK,
            secondary_muscles=[],
            equipment=EquipmentType.BARBELL,
            movement_type=MovementType.COMPOUND,
            is_custom=True,
        )

        service.create(push_exercise)
        service.create(pull_exercise)

        # Filter by Push
        push_exercises = service.get_all(category="Push")
        assert len(push_exercises) == 1
        assert push_exercises[0].name == "Push Exercise"

        # Filter by Pull
        pull_exercises = service.get_all(category="Pull")
        assert len(pull_exercises) == 1
        assert pull_exercises[0].name == "Pull Exercise"

    def test_get_all_with_muscle_filter(self, service):
        """Test filtering exercises by muscle group."""
        chest_exercise = ExerciseCreate(
            name="Chest Exercise",
            category=CategoryType.PUSH,
            primary_muscle=MuscleGroup.CHEST,
            secondary_muscles=[],
            equipment=EquipmentType.BARBELL,
            movement_type=MovementType.COMPOUND,
            is_custom=True,
        )
        back_exercise = ExerciseCreate(
            name="Back Exercise",
            category=CategoryType.PULL,
            primary_muscle=MuscleGroup.BACK,
            secondary_muscles=[],
            equipment=EquipmentType.BARBELL,
            movement_type=MovementType.COMPOUND,
            is_custom=True,
        )

        service.create(chest_exercise)
        service.create(back_exercise)

        # Filter by Chest
        chest_exercises = service.get_all(muscle="Chest")
        assert len(chest_exercises) == 1
        assert chest_exercises[0].name == "Chest Exercise"

    def test_get_all_with_equipment_filter(self, service):
        """Test filtering exercises by equipment."""
        barbell_exercise = ExerciseCreate(
            name="Barbell Exercise",
            category=CategoryType.PUSH,
            primary_muscle=MuscleGroup.CHEST,
            secondary_muscles=[],
            equipment=EquipmentType.BARBELL,
            movement_type=MovementType.COMPOUND,
            is_custom=True,
        )
        dumbbell_exercise = ExerciseCreate(
            name="Dumbbell Exercise",
            category=CategoryType.PUSH,
            primary_muscle=MuscleGroup.CHEST,
            secondary_muscles=[],
            equipment=EquipmentType.DUMBBELL,
            movement_type=MovementType.COMPOUND,
            is_custom=True,
        )

        service.create(barbell_exercise)
        service.create(dumbbell_exercise)

        # Filter by Barbell
        barbell_exercises = service.get_all(equipment="Barbell")
        assert len(barbell_exercises) == 1
        assert barbell_exercises[0].name == "Barbell Exercise"

    def test_get_all_with_multiple_filters(self, service):
        """Test filtering with multiple criteria."""
        # Create exercises
        exercises_data = [
            ExerciseCreate(
                name="Barbell Bench Press",
                category=CategoryType.PUSH,
                primary_muscle=MuscleGroup.CHEST,
                secondary_muscles=[],
                equipment=EquipmentType.BARBELL,
                movement_type=MovementType.COMPOUND,
                is_custom=True,
            ),
            ExerciseCreate(
                name="Dumbbell Bench Press",
                category=CategoryType.PUSH,
                primary_muscle=MuscleGroup.CHEST,
                secondary_muscles=[],
                equipment=EquipmentType.DUMBBELL,
                movement_type=MovementType.COMPOUND,
                is_custom=True,
            ),
            ExerciseCreate(
                name="Barbell Row",
                category=CategoryType.PULL,
                primary_muscle=MuscleGroup.BACK,
                secondary_muscles=[],
                equipment=EquipmentType.BARBELL,
                movement_type=MovementType.COMPOUND,
                is_custom=True,
            ),
        ]

        for exercise_data in exercises_data:
            service.create(exercise_data)

        # Filter: Push + Chest + Barbell
        filtered = service.get_all(category="Push", muscle="Chest", equipment="Barbell")
        assert len(filtered) == 1
        assert filtered[0].name == "Barbell Bench Press"

    def test_search(self, service):
        """Test searching exercises by name."""
        exercises_data = [
            ExerciseCreate(
                name="Barbell Bench Press",
                category=CategoryType.PUSH,
                primary_muscle=MuscleGroup.CHEST,
                secondary_muscles=[],
                equipment=EquipmentType.BARBELL,
                movement_type=MovementType.COMPOUND,
                is_custom=True,
            ),
            ExerciseCreate(
                name="Incline Bench Press",
                category=CategoryType.PUSH,
                primary_muscle=MuscleGroup.CHEST,
                secondary_muscles=[],
                equipment=EquipmentType.BARBELL,
                movement_type=MovementType.COMPOUND,
                is_custom=True,
            ),
            ExerciseCreate(
                name="Barbell Row",
                category=CategoryType.PULL,
                primary_muscle=MuscleGroup.BACK,
                secondary_muscles=[],
                equipment=EquipmentType.BARBELL,
                movement_type=MovementType.COMPOUND,
                is_custom=True,
            ),
        ]

        for exercise_data in exercises_data:
            service.create(exercise_data)

        # Search for "bench"
        results = service.search("bench")
        assert len(results) == 2
        assert all("bench" in ex.name.lower() for ex in results)

        # Search for "barbell"
        results = service.search("barbell")
        assert len(results) == 2

    def test_search_case_insensitive(self, service, sample_exercise_data):
        """Test that search is case-insensitive."""
        service.create(sample_exercise_data)

        assert len(service.search("bench")) > 0
        assert len(service.search("BENCH")) > 0
        assert len(service.search("BeNcH")) > 0


class TestExerciseServiceDelete:
    """Tests for deleting exercises."""

    def test_delete_custom_exercise(self, service, sample_exercise_data):
        """Test deleting a custom exercise."""
        exercise = service.create(sample_exercise_data)
        result = service.delete(exercise.id)

        assert result is True
        assert service.get_by_id(exercise.id) is None

    def test_delete_non_custom_exercise_fails(self, service):
        """Test that deleting a non-custom exercise raises an error."""
        # Create a non-custom exercise
        exercise_data = ExerciseCreate(
            name="Built-in Exercise",
            category=CategoryType.PUSH,
            primary_muscle=MuscleGroup.CHEST,
            secondary_muscles=[],
            equipment=EquipmentType.BARBELL,
            movement_type=MovementType.COMPOUND,
            is_custom=False,
        )
        exercise = service.create(exercise_data)

        with pytest.raises(ValueError, match="Cannot delete built-in exercises"):
            service.delete(exercise.id)

    def test_delete_non_existent_exercise(self, service):
        """Test deleting a non-existent exercise."""
        result = service.delete(99999)
        assert result is False


class TestExerciseServiceSeedData:
    """Tests for loading seed data."""

    def test_load_seed_exercises_from_json(self, service, tmp_path):
        """Test loading exercises from JSON file."""
        # Create a temporary JSON file
        seed_data = [
            {
                "name": "Test Exercise 1",
                "category": "Push",
                "primary_muscle": "Chest",
                "secondary_muscles": ["Triceps"],
                "equipment": "Barbell",
                "movement_type": "Compound",
                "is_custom": False,
                "instructions": "Test instructions",
                "video_url": None,
            },
            {
                "name": "Test Exercise 2",
                "category": "Pull",
                "primary_muscle": "Back",
                "secondary_muscles": [],
                "equipment": "Dumbbell",
                "movement_type": "Isolation",
                "is_custom": False,
                "instructions": None,
                "video_url": None,
            },
        ]

        json_file = tmp_path / "test_exercises.json"
        with open(json_file, "w") as f:
            json.dump(seed_data, f)

        # Temporarily replace the exercises.json path
        original_path = Path(__file__).parent.parent / "lift" / "data" / "exercises.json"
        import shutil

        # Backup if exists
        backup_path = None
        if original_path.exists():
            backup_path = original_path.with_suffix(".json.backup")
            shutil.copy(original_path, backup_path)

        try:
            # Copy test file to expected location
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(json_file, original_path)

            # Load seed data
            loaded_count = service.load_seed_exercises()

            assert loaded_count == 2
            assert len(service.get_all()) == 2

        finally:
            # Restore backup
            if backup_path and backup_path.exists():
                shutil.move(backup_path, original_path)

    def test_load_seed_exercises_skips_if_exists(self, service, sample_exercise_data):
        """Test that seed loading is skipped if exercises already exist."""
        # Create an exercise first
        service.create(sample_exercise_data)

        # Try to load seed data
        loaded_count = service.load_seed_exercises(force=False)

        # Should return 0 because exercises already exist
        assert loaded_count == 0

    def test_load_seed_exercises_force_reload(self, service, tmp_path):
        """Test force reloading seed data."""
        # Create initial exercise
        exercise_data = ExerciseCreate(
            name="Initial Exercise",
            category=CategoryType.PUSH,
            primary_muscle=MuscleGroup.CHEST,
            secondary_muscles=[],
            equipment=EquipmentType.BARBELL,
            movement_type=MovementType.COMPOUND,
            is_custom=True,
        )
        service.create(exercise_data)

        # Create test JSON with new exercise
        seed_data = [
            {
                "name": "New Seed Exercise",
                "category": "Push",
                "primary_muscle": "Chest",
                "secondary_muscles": [],
                "equipment": "Barbell",
                "movement_type": "Compound",
                "is_custom": False,
                "instructions": None,
                "video_url": None,
            }
        ]

        json_file = tmp_path / "test_exercises.json"
        with open(json_file, "w") as f:
            json.dump(seed_data, f)

        original_path = Path(__file__).parent.parent / "lift" / "data" / "exercises.json"
        import shutil

        backup_path = None
        if original_path.exists():
            backup_path = original_path.with_suffix(".json.backup")
            shutil.copy(original_path, backup_path)

        try:
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(json_file, original_path)

            # Force reload should load the new exercise
            loaded_count = service.load_seed_exercises(force=True)

            assert loaded_count == 1
            assert len(service.get_all()) == 2  # Initial + new seed

        finally:
            if backup_path and backup_path.exists():
                shutil.move(backup_path, original_path)
