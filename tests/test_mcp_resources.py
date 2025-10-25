"""Tests for MCP resource handlers."""

from decimal import Decimal

import pytest

from lift.core.database import DatabaseManager
from lift.core.models import SetCreate, SetType, WeightUnit, WorkoutCreate
from lift.mcp.resources import (
    ExerciseResourceHandler,
    StatsResourceHandler,
    WorkoutResourceHandler,
    get_all_resource_handlers,
)
from lift.services.exercise_service import ExerciseService
from lift.services.set_service import SetService
from lift.services.workout_service import WorkoutService


@pytest.fixture()
def db():
    """Create in-memory test database."""
    db = DatabaseManager(":memory:")
    db.initialize_database()
    return db


@pytest.fixture()
def workout_service(db):
    """Create workout service instance."""
    return WorkoutService(db)


@pytest.fixture()
def set_service(db):
    """Create set service instance."""
    return SetService(db)


@pytest.fixture()
def exercise_service(db):
    """Create exercise service instance."""
    return ExerciseService(db)


@pytest.fixture()
def sample_workout_with_sets(workout_service, set_service, exercise_service):
    """Create a sample workout with sets for testing."""
    # Create workout
    workout_create = WorkoutCreate(
        name="Test Workout",
        bodyweight=Decimal("185"),
        bodyweight_unit=WeightUnit.LBS,
    )
    workout = workout_service.create_workout(workout_create)

    # Get bench press exercise
    bench_press = exercise_service.get_by_name("Bench Press (Barbell)")

    # Add sets
    for _ in range(3):
        set_create = SetCreate(
            workout_id=workout.id,
            exercise_id=bench_press.id,
            weight=Decimal("225"),
            reps=8,
            rpe=Decimal("7.5"),
            set_type=SetType.WORKING,
        )
        set_service.create_set(set_create)

    return workout


class TestWorkoutResourceHandler:
    """Test workout resource handler."""

    def test_can_handle_workout_uris(self, db):
        """Test that handler recognizes workout URIs."""
        handler = WorkoutResourceHandler(db)

        assert handler.can_handle("lift://workouts/recent")
        assert handler.can_handle("lift://workouts/123")
        assert not handler.can_handle("lift://exercises/library")
        assert not handler.can_handle("lift://stats/summary")

    def test_list_resources(self, db):
        """Test listing workout resources."""
        handler = WorkoutResourceHandler(db)
        resources = handler.list_resources()

        assert len(resources) > 0
        assert any(r.uri == "lift://workouts/recent" for r in resources)

    def test_get_recent_workouts(self, db, sample_workout_with_sets):
        """Test getting recent workouts."""
        handler = WorkoutResourceHandler(db)
        result = handler.get_resource("lift://workouts/recent")

        assert "workouts" in result
        assert len(result["workouts"]) > 0

        workout = result["workouts"][0]
        assert "id" in workout
        assert "name" in workout
        assert workout["name"] == "Test Workout"

    def test_get_specific_workout(self, db, sample_workout_with_sets):
        """Test getting specific workout details."""
        handler = WorkoutResourceHandler(db)
        workout_id = sample_workout_with_sets.id

        result = handler.get_resource(f"lift://workouts/{workout_id}")

        assert "workout" in result
        workout = result["workout"]
        assert workout["id"] == workout_id
        assert workout["name"] == "Test Workout"
        assert "sets" in workout
        assert len(workout["sets"]) == 3

    def test_get_specific_workout_not_found(self, db):
        """Test getting non-existent workout."""
        handler = WorkoutResourceHandler(db)
        result = handler.get_resource("lift://workouts/99999")

        assert "error" in result

    def test_get_specific_workout_invalid_id(self, db):
        """Test getting workout with invalid ID."""
        handler = WorkoutResourceHandler(db)
        result = handler.get_resource("lift://workouts/invalid")

        assert "error" in result

    def test_get_unknown_resource(self, db):
        """Test getting unknown workout resource."""
        handler = WorkoutResourceHandler(db)
        result = handler.get_resource("lift://workouts/unknown/path")

        assert "error" in result


class TestExerciseResourceHandler:
    """Test exercise resource handler."""

    def test_can_handle_exercise_uris(self, db):
        """Test that handler recognizes exercise URIs."""
        handler = ExerciseResourceHandler(db)

        assert handler.can_handle("lift://exercises/library")
        assert not handler.can_handle("lift://workouts/recent")
        assert not handler.can_handle("lift://stats/summary")

    def test_list_resources(self, db):
        """Test listing exercise resources."""
        handler = ExerciseResourceHandler(db)
        resources = handler.list_resources()

        assert len(resources) > 0
        assert any(r.uri == "lift://exercises/library" for r in resources)

    def test_get_exercise_library(self, db):
        """Test getting complete exercise library."""
        handler = ExerciseResourceHandler(db)
        result = handler.get_resource("lift://exercises/library")

        assert "exercises" in result
        assert "count" in result
        assert result["count"] > 100  # Should have pre-loaded exercises

        # Check exercise structure
        exercise = result["exercises"][0]
        assert "id" in exercise
        assert "name" in exercise
        assert "category" in exercise
        assert "primary_muscle" in exercise
        assert "equipment" in exercise

    def test_get_unknown_resource(self, db):
        """Test getting unknown exercise resource."""
        handler = ExerciseResourceHandler(db)
        result = handler.get_resource("lift://exercises/unknown")

        assert "error" in result


class TestStatsResourceHandler:
    """Test stats resource handler."""

    def test_can_handle_stats_uris(self, db):
        """Test that handler recognizes stats URIs."""
        handler = StatsResourceHandler(db)

        assert handler.can_handle("lift://stats/summary")
        assert handler.can_handle("lift://stats/summary?period=week")
        assert handler.can_handle("lift://stats/summary?period=month")
        assert not handler.can_handle("lift://workouts/recent")
        assert not handler.can_handle("lift://exercises/library")

    def test_list_resources(self, db):
        """Test listing stats resources."""
        handler = StatsResourceHandler(db)
        resources = handler.list_resources()

        assert len(resources) > 0
        assert any("stats/summary" in r.uri for r in resources)

    def test_get_weekly_stats(self, db, sample_workout_with_sets):
        """Test getting weekly statistics."""
        handler = StatsResourceHandler(db)
        result = handler.get_resource("lift://stats/summary?period=week")

        assert "summary" in result
        summary = result["summary"]
        assert "period" in summary
        assert summary["period"] == "week"
        assert "total_workouts" in summary
        assert "total_volume" in summary
        assert "total_sets" in summary

    def test_get_monthly_stats(self, db, sample_workout_with_sets):
        """Test getting monthly statistics."""
        handler = StatsResourceHandler(db)
        result = handler.get_resource("lift://stats/summary?period=month")

        assert "summary" in result
        summary = result["summary"]
        assert summary["period"] == "month"

    def test_get_yearly_stats(self, db, sample_workout_with_sets):
        """Test getting yearly statistics."""
        handler = StatsResourceHandler(db)
        result = handler.get_resource("lift://stats/summary?period=year")

        assert "summary" in result
        summary = result["summary"]
        assert summary["period"] == "year"

    def test_get_stats_default_period(self, db, sample_workout_with_sets):
        """Test getting stats with default period (week)."""
        handler = StatsResourceHandler(db)
        result = handler.get_resource("lift://stats/summary")

        assert "summary" in result
        summary = result["summary"]
        # Default should be week
        assert summary["period"] == "week"

    def test_get_unknown_resource(self, db):
        """Test getting unknown stats resource."""
        handler = StatsResourceHandler(db)
        result = handler.get_resource("lift://stats/unknown")

        assert "error" in result


class TestGetAllResourceHandlers:
    """Test getting all resource handlers."""

    def test_get_all_handlers(self, tmp_path, monkeypatch):
        """Test getting all resource handlers."""
        # Mock database path
        db_path = tmp_path / "test.duckdb"
        monkeypatch.setattr("lift.mcp.resources.get_database_path", lambda: str(db_path))

        handlers = get_all_resource_handlers()

        assert len(handlers) == 3
        assert any(isinstance(h, WorkoutResourceHandler) for h in handlers)
        assert any(isinstance(h, ExerciseResourceHandler) for h in handlers)
        assert any(isinstance(h, StatsResourceHandler) for h in handlers)

    def test_handlers_share_database(self, tmp_path, monkeypatch):
        """Test that all handlers use the same database instance."""
        db_path = tmp_path / "test.duckdb"
        monkeypatch.setattr("lift.mcp.resources.get_database_path", lambda: str(db_path))

        handlers = get_all_resource_handlers()

        # All handlers should have a database
        for handler in handlers:
            assert handler.db is not None
