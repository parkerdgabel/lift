"""Tests for export service."""

import json
import tempfile
from pathlib import Path

import pytest

from lift.core.database import DatabaseManager, reset_db_instance
from lift.services.export_service import ExportService


@pytest.fixture
def db():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        reset_db_instance()
        db = DatabaseManager(str(db_path))
        db.initialize_database()

        # Add some test data
        with db.get_connection() as conn:
            # Insert test exercise
            conn.execute(
                """
                INSERT INTO exercises (name, category, primary_muscle, equipment, movement_type)
                VALUES ('Bench Press', 'Push', 'Chest', 'Barbell', 'Compound')
                """
            )

            # Insert test setting
            conn.execute(
                """
                INSERT INTO settings (key, value, description)
                VALUES ('test_key', 'test_value', 'Test setting')
                """
            )

        yield db
        reset_db_instance()


def test_export_to_csv(db):
    """Test exporting a single table to CSV."""
    export_service = ExportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "exercises.csv"
        export_service.export_to_csv("exercises", str(output_path))

        # Verify file exists
        assert output_path.exists()

        # Verify content
        with open(output_path, "r") as f:
            lines = f.readlines()
            assert len(lines) >= 2  # Header + at least 1 data row
            assert "name" in lines[0].lower()
            assert "Bench Press" in lines[1]


def test_export_all_to_csv(db):
    """Test exporting all tables to CSV."""
    export_service = ExportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        summary = export_service.export_all_to_csv(tmpdir)

        # Verify summary
        assert isinstance(summary, dict)
        assert "exercises" in summary
        assert "settings" in summary
        assert summary["exercises"] >= 1

        # Verify files exist
        exercises_file = Path(tmpdir) / "exercises.csv"
        assert exercises_file.exists()


def test_export_to_json(db):
    """Test exporting a single table to JSON."""
    export_service = ExportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "exercises.json"
        export_service.export_to_json("exercises", str(output_path))

        # Verify file exists
        assert output_path.exists()

        # Verify content
        with open(output_path, "r") as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) >= 1
            assert data[0]["name"] == "Bench Press"


def test_export_all_to_json(db):
    """Test exporting all tables to a single JSON file."""
    export_service = ExportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "database.json"
        summary = export_service.export_all_to_json(str(output_path))

        # Verify summary
        assert isinstance(summary, dict)
        assert "exercises" in summary
        assert "settings" in summary
        assert summary["exercises"] >= 1

        # Verify file exists and content
        assert output_path.exists()

        with open(output_path, "r") as f:
            data = json.load(f)
            assert "export_date" in data
            assert "tables" in data
            assert "exercises" in data["tables"]
            assert len(data["tables"]["exercises"]) >= 1


def test_export_nonexistent_table(db):
    """Test exporting a table that doesn't exist."""
    export_service = ExportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "nonexistent.csv"

        with pytest.raises(ValueError, match="does not exist"):
            export_service.export_to_csv("nonexistent_table", str(output_path))


def test_export_empty_table(db):
    """Test exporting an empty table."""
    export_service = ExportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "workouts.csv"
        export_service.export_to_csv("workouts", str(output_path))

        # Verify file exists with headers only
        assert output_path.exists()

        with open(output_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1  # Header only


def test_export_workout_history(db):
    """Test exporting workout history."""
    export_service = ExportService(db)

    # Add a test workout
    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO workouts (date, name, completed)
            VALUES (CURRENT_TIMESTAMP, 'Test Workout', true)
            """
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "workout_history.json"
        count = export_service.export_workout_history(output_path=str(output_path))

        # Verify count
        assert count >= 1

        # Verify file exists and content
        assert output_path.exists()

        with open(output_path, "r") as f:
            data = json.load(f)
            assert "workouts" in data
            assert "workout_count" in data
            assert data["workout_count"] >= 1


def test_export_creates_directories(db):
    """Test that export creates necessary directories."""
    export_service = ExportService(db)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use a nested path that doesn't exist
        output_path = Path(tmpdir) / "nested" / "path" / "exercises.csv"
        export_service.export_to_csv("exercises", str(output_path))

        # Verify directory and file were created
        assert output_path.exists()
        assert output_path.parent.exists()
