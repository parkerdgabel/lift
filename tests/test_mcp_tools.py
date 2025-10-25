"""Tests for MCP tool handlers."""

import pytest

from lift.mcp.tools import (
    GetExerciseInfoTool,
    LogBodyweightTool,
    SearchExercisesTool,
    StartWorkoutTool,
    get_all_tool_handlers,
)
from lift.services.body_service import BodyService
from lift.services.exercise_service import ExerciseService
from lift.services.workout_service import WorkoutService


@pytest.fixture()
def exercise_service(db):
    """Create exercise service instance."""
    return ExerciseService(db)


@pytest.fixture()
def workout_service(db):
    """Create workout service instance."""
    return WorkoutService(db)


@pytest.fixture()
def body_service(db):
    """Create body service instance."""
    return BodyService(db)


class TestSearchExercisesTool:
    """Test search exercises tool."""

    def test_get_name(self, db):
        """Test tool name."""
        tool = SearchExercisesTool(db)
        assert tool.get_name() == "search_exercises"

    def test_get_description(self, db):
        """Test tool description."""
        tool = SearchExercisesTool(db)
        desc = tool.get_description()
        assert "search" in desc.lower()
        assert "exercise" in desc.lower()

    def test_get_input_schema(self, db):
        """Test input schema is valid JSON schema."""
        tool = SearchExercisesTool(db)
        schema = tool.get_input_schema()

        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "muscle" in schema["properties"]
        assert "category" in schema["properties"]
        assert "equipment" in schema["properties"]
        assert "limit" in schema["properties"]

    def test_search_by_query(self, db):
        """Test searching exercises by query."""
        tool = SearchExercisesTool(db)
        result = tool.execute({"query": "bench"})

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["count"] > 0
        assert len(result["data"]["exercises"]) > 0

        # Check exercise structure
        exercise = result["data"]["exercises"][0]
        assert "name" in exercise
        assert "bench" in exercise["name"].lower()

    def test_search_by_muscle(self, db):
        """Test searching exercises by muscle."""
        tool = SearchExercisesTool(db)
        result = tool.execute({"muscle": "Chest"})

        assert result["success"] is True
        assert result["data"]["count"] > 0

        # All exercises should be chest exercises
        for exercise in result["data"]["exercises"]:
            assert exercise["primary_muscle"] == "Chest"

    def test_search_by_category(self, db):
        """Test searching exercises by category."""
        tool = SearchExercisesTool(db)
        result = tool.execute({"category": "Push"})

        assert result["success"] is True
        assert result["data"]["count"] > 0

        for exercise in result["data"]["exercises"]:
            assert exercise["category"] == "Push"

    def test_search_by_equipment(self, db):
        """Test searching exercises by equipment."""
        tool = SearchExercisesTool(db)
        result = tool.execute({"equipment": "Barbell"})

        assert result["success"] is True
        assert result["data"]["count"] > 0

        for exercise in result["data"]["exercises"]:
            assert exercise["equipment"] == "Barbell"

    def test_search_with_limit(self, db):
        """Test search result limiting."""
        tool = SearchExercisesTool(db)
        result = tool.execute({"limit": 5})

        assert result["success"] is True
        assert len(result["data"]["exercises"]) <= 5

    def test_search_validation_error(self, db):
        """Test search with invalid input."""
        tool = SearchExercisesTool(db)
        result = tool.execute({"limit": -1})  # Invalid limit

        assert result["success"] is False
        assert "error" in result


class TestGetExerciseInfoTool:
    """Test get exercise info tool."""

    def test_get_name(self, db):
        """Test tool name."""
        tool = GetExerciseInfoTool(db)
        assert tool.get_name() == "get_exercise_info"

    def test_get_description(self, db):
        """Test tool description."""
        tool = GetExerciseInfoTool(db)
        desc = tool.get_description()
        assert "exercise" in desc.lower()
        assert "information" in desc.lower()

    def test_get_input_schema(self, db):
        """Test input schema."""
        tool = GetExerciseInfoTool(db)
        schema = tool.get_input_schema()

        assert "properties" in schema
        assert "exercise_name" in schema["properties"]

    def test_get_existing_exercise(self, db):
        """Test getting info for existing exercise."""
        tool = GetExerciseInfoTool(db)
        result = tool.execute({"exercise_name": "Bench Press (Barbell)"})

        assert result["success"] is True
        assert "data" in result

        exercise = result["data"]
        assert exercise["name"] == "Bench Press (Barbell)"
        assert exercise["category"] == "Push"
        assert exercise["primary_muscle"] == "Chest"
        assert "equipment" in exercise
        assert "movement_type" in exercise

    def test_get_nonexistent_exercise(self, db):
        """Test getting info for non-existent exercise."""
        tool = GetExerciseInfoTool(db)
        result = tool.execute({"exercise_name": "Nonexistent Exercise"})

        assert result["success"] is False
        assert "error" in result

    def test_validation_error_missing_name(self, db):
        """Test validation error when exercise name is missing."""
        tool = GetExerciseInfoTool(db)
        result = tool.execute({})  # Missing exercise_name

        assert result["success"] is False
        assert "error" in result


class TestStartWorkoutTool:
    """Test start workout tool."""

    def test_get_name(self, db):
        """Test tool name."""
        tool = StartWorkoutTool(db)
        assert tool.get_name() == "start_workout"

    def test_get_description(self, db):
        """Test tool description."""
        tool = StartWorkoutTool(db)
        desc = tool.get_description()
        assert "start" in desc.lower()
        assert "workout" in desc.lower()

    def test_get_input_schema(self, db):
        """Test input schema."""
        tool = StartWorkoutTool(db)
        schema = tool.get_input_schema()

        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "bodyweight" in schema["properties"]
        assert "bodyweight_unit" in schema["properties"]

    def test_start_workout_minimal(self, db):
        """Test starting workout with minimal info."""
        tool = StartWorkoutTool(db)
        result = tool.execute({})

        assert result["success"] is True
        assert "data" in result

        workout = result["data"]
        assert "workout_id" in workout
        assert workout["workout_id"] > 0

    def test_start_workout_with_name(self, db):
        """Test starting workout with name."""
        tool = StartWorkoutTool(db)
        result = tool.execute({"name": "Chest Day"})

        assert result["success"] is True
        workout = result["data"]
        assert workout["name"] == "Chest Day"

    def test_start_workout_with_bodyweight(self, db):
        """Test starting workout with bodyweight."""
        tool = StartWorkoutTool(db)
        result = tool.execute({"bodyweight": 185.5, "bodyweight_unit": "lbs"})

        assert result["success"] is True
        assert "workout_id" in result["data"]

    def test_start_workout_validation_error(self, db):
        """Test validation error with invalid bodyweight unit."""
        tool = StartWorkoutTool(db)
        result = tool.execute({"bodyweight": 185.5, "bodyweight_unit": "invalid"})

        assert result["success"] is False
        assert "error" in result


class TestLogBodyweightTool:
    """Test log bodyweight tool."""

    def test_get_name(self, db):
        """Test tool name."""
        tool = LogBodyweightTool(db)
        assert tool.get_name() == "log_bodyweight"

    def test_get_description(self, db):
        """Test tool description."""
        tool = LogBodyweightTool(db)
        desc = tool.get_description()
        assert "bodyweight" in desc.lower() or "log" in desc.lower()

    def test_get_input_schema(self, db):
        """Test input schema."""
        tool = LogBodyweightTool(db)
        schema = tool.get_input_schema()

        assert "properties" in schema
        assert "weight" in schema["properties"]
        assert "unit" in schema["properties"]

    def test_log_bodyweight_lbs(self, db):
        """Test logging bodyweight in pounds."""
        tool = LogBodyweightTool(db)
        result = tool.execute({"weight": 185.5, "unit": "lbs"})

        assert result["success"] is True
        assert "data" in result

        measurement = result["data"]
        assert "weight" in measurement
        assert "unit" in measurement
        assert measurement["unit"] == "lbs"

    def test_log_bodyweight_kg(self, db):
        """Test logging bodyweight in kilograms."""
        tool = LogBodyweightTool(db)
        result = tool.execute({"weight": 84.5, "unit": "kg"})

        assert result["success"] is True
        measurement = result["data"]
        assert measurement["unit"] == "kg"

    def test_log_bodyweight_validation_error_negative(self, db):
        """Test validation error with negative weight."""
        tool = LogBodyweightTool(db)
        result = tool.execute({"weight": -10, "unit": "lbs"})

        assert result["success"] is False
        assert "error" in result

    def test_log_bodyweight_validation_error_invalid_unit(self, db):
        """Test validation error with invalid unit."""
        tool = LogBodyweightTool(db)
        result = tool.execute({"weight": 185, "unit": "invalid"})

        assert result["success"] is False
        assert "error" in result

    def test_log_bodyweight_missing_weight(self, db):
        """Test validation error when weight is missing."""
        tool = LogBodyweightTool(db)
        result = tool.execute({"unit": "lbs"})  # Missing weight

        assert result["success"] is False
        assert "error" in result


class TestGetAllToolHandlers:
    """Test getting all tool handlers."""

    def test_get_all_handlers(self, tmp_path, monkeypatch):
        """Test getting all tool handlers."""
        # Mock database path
        db_path = tmp_path / "test.duckdb"
        monkeypatch.setattr("lift.mcp.tools.get_database_path", lambda: str(db_path))

        handlers = get_all_tool_handlers()

        assert len(handlers) == 4
        assert any(isinstance(h, SearchExercisesTool) for h in handlers)
        assert any(isinstance(h, GetExerciseInfoTool) for h in handlers)
        assert any(isinstance(h, StartWorkoutTool) for h in handlers)
        assert any(isinstance(h, LogBodyweightTool) for h in handlers)

    def test_handlers_have_unique_names(self, tmp_path, monkeypatch):
        """Test that all tool handlers have unique names."""
        db_path = tmp_path / "test.duckdb"
        monkeypatch.setattr("lift.mcp.tools.get_database_path", lambda: str(db_path))

        handlers = get_all_tool_handlers()
        names = [h.get_name() for h in handlers]

        # All names should be unique
        assert len(names) == len(set(names))

    def test_handlers_share_database(self, tmp_path, monkeypatch):
        """Test that all handlers use the same database instance."""
        db_path = tmp_path / "test.duckdb"
        monkeypatch.setattr("lift.mcp.tools.get_database_path", lambda: str(db_path))

        handlers = get_all_tool_handlers()

        # All handlers should have a database
        for handler in handlers:
            assert handler.db is not None
