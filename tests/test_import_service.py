"""Tests for import service."""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from lift.core.database import DatabaseManager, reset_db_instance
from lift.services.import_service import ImportService


@pytest.fixture
def db():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        reset_db_instance()
        db = DatabaseManager(str(db_path))
        db.initialize_database()
        yield db
        reset_db_instance()


def test_import_from_csv(db):
    """Test importing data from CSV."""
    import_service = ImportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test CSV file
        csv_path = Path(tmpdir) / "exercises.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["name", "category", "primary_muscle", "equipment", "movement_type"]
            )
            writer.writerow(["Squat", "Legs", "Quads", "Barbell", "Compound"])
            writer.writerow(["Deadlift", "Pull", "Back", "Barbell", "Compound"])

        # Import the CSV
        count = import_service.import_from_csv("exercises", str(csv_path))

        # Verify import
        assert count == 2

        # Verify data in database
        with db.get_connection() as conn:
            result = conn.execute(
                "SELECT name FROM exercises ORDER BY name"
            ).fetchall()
            assert len(result) == 2
            assert result[0][0] == "Deadlift"
            assert result[1][0] == "Squat"


def test_import_from_json(db):
    """Test importing data from JSON."""
    import_service = ImportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test JSON file (full database export format)
        json_path = Path(tmpdir) / "database.json"
        data = {
            "export_date": "2025-01-20T12:00:00",
            "tables": {
                "exercises": [
                    {
                        "name": "Pull-up",
                        "category": "Pull",
                        "primary_muscle": "Back",
                        "equipment": "Bodyweight",
                        "movement_type": "Compound",
                        "is_custom": True,
                    }
                ]
            },
        }

        with open(json_path, "w") as f:
            json.dump(data, f)

        # Import the JSON
        summary = import_service.import_from_json(str(json_path))

        # Verify import
        assert "exercises" in summary
        assert summary["exercises"] == 1

        # Verify data in database
        with db.get_connection() as conn:
            result = conn.execute(
                "SELECT name FROM exercises WHERE name = 'Pull-up'"
            ).fetchone()
            assert result is not None
            assert result[0] == "Pull-up"


def test_import_exercises_from_json(db):
    """Test specialized exercise import."""
    import_service = ImportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create exercises JSON file
        json_path = Path(tmpdir) / "exercises.json"
        exercises = [
            {
                "name": "Bench Press",
                "category": "Push",
                "primary_muscle": "Chest",
                "secondary_muscles": ["Triceps", "Shoulders"],
                "equipment": "Barbell",
                "movement_type": "Compound",
                "is_custom": False,
            },
            {
                "name": "Incline Dumbbell Press",
                "category": "Push",
                "primary_muscle": "Chest",
                "secondary_muscles": ["Triceps", "Shoulders"],
                "equipment": "Dumbbell",
                "movement_type": "Compound",
                "is_custom": True,
            },
        ]

        with open(json_path, "w") as f:
            json.dump(exercises, f)

        # Import exercises
        count = import_service.import_exercises_from_json(str(json_path))

        # Verify import
        assert count == 2

        # Verify data in database
        with db.get_connection() as conn:
            result = conn.execute(
                "SELECT name, secondary_muscles FROM exercises ORDER BY name"
            ).fetchall()
            assert len(result) == 2
            # Secondary muscles should be stored as JSON string
            assert "Triceps" in result[0][1]


def test_validate_import_data(db):
    """Test data validation."""
    import_service = ImportService(db)

    # Valid data
    valid_data = [
        {
            "name": "Test Exercise",
            "category": "Push",
            "primary_muscle": "Chest",
            "equipment": "Barbell",
        }
    ]

    assert import_service.validate_import_data(valid_data, "exercises") is True

    # Invalid table name
    assert import_service.validate_import_data(valid_data, "nonexistent_table") is False

    # Empty data is valid
    assert import_service.validate_import_data([], "exercises") is True


def test_import_csv_file_not_found(db):
    """Test importing from non-existent CSV file."""
    import_service = ImportService(db)

    with pytest.raises(FileNotFoundError):
        import_service.import_from_csv("exercises", "/nonexistent/file.csv")


def test_import_json_file_not_found(db):
    """Test importing from non-existent JSON file."""
    import_service = ImportService(db)

    with pytest.raises(FileNotFoundError):
        import_service.import_from_json("/nonexistent/file.json")


def test_import_csv_invalid_table(db):
    """Test importing CSV into non-existent table."""
    import_service = ImportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test CSV file
        csv_path = Path(tmpdir) / "data.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["col1", "col2"])
            writer.writerow(["val1", "val2"])

        with pytest.raises(ValueError, match="does not exist"):
            import_service.import_from_csv("nonexistent_table", str(csv_path))


def test_import_csv_invalid_columns(db):
    """Test importing CSV with invalid column names."""
    import_service = ImportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test CSV file with invalid columns
        csv_path = Path(tmpdir) / "exercises.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["invalid_column", "another_invalid"])
            writer.writerow(["val1", "val2"])

        with pytest.raises(ValueError, match="does not match any column"):
            import_service.import_from_csv("exercises", str(csv_path))


def test_import_empty_csv(db):
    """Test importing empty CSV file."""
    import_service = ImportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create empty CSV file with headers only
        csv_path = Path(tmpdir) / "exercises.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["name", "category", "primary_muscle", "equipment", "movement_type"]
            )

        count = import_service.import_from_csv("exercises", str(csv_path))

        # Should import 0 rows
        assert count == 0


def test_import_csv_with_null_values(db):
    """Test importing CSV with empty/null values."""
    import_service = ImportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test CSV file with empty values
        csv_path = Path(tmpdir) / "exercises.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "name",
                    "category",
                    "primary_muscle",
                    "equipment",
                    "movement_type",
                    "instructions",
                ]
            )
            writer.writerow(["Test Exercise", "Push", "Chest", "Barbell", "Compound", ""])

        count = import_service.import_from_csv("exercises", str(csv_path))

        # Verify import
        assert count == 1

        # Verify null value handling
        with db.get_connection() as conn:
            result = conn.execute(
                "SELECT instructions FROM exercises WHERE name = 'Test Exercise'"
            ).fetchone()
            assert result[0] is None


def test_import_exercises_missing_required_field(db):
    """Test importing exercises with missing required fields."""
    import_service = ImportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create exercises JSON file missing required field
        json_path = Path(tmpdir) / "exercises.json"
        exercises = [
            {
                "name": "Bench Press",
                "category": "Push",
                "primary_muscle": "Chest",
                # Missing 'equipment' field
            }
        ]

        with open(json_path, "w") as f:
            json.dump(exercises, f)

        with pytest.raises(ValueError, match="missing required field"):
            import_service.import_exercises_from_json(str(json_path))


def test_import_json_invalid_format(db):
    """Test importing JSON with invalid format."""
    import_service = ImportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create invalid JSON file (list without tables wrapper)
        json_path = Path(tmpdir) / "invalid.json"
        data = [{"some": "data"}]

        with open(json_path, "w") as f:
            json.dump(data, f)

        with pytest.raises(ValueError, match="Invalid JSON format"):
            import_service.import_from_json(str(json_path))
