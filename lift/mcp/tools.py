"""Tool handlers for MCP server."""

import logging
from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from lift.core.database import DatabaseManager
from lift.core.models import (
    WeightUnit,
    WorkoutCreate,
)
from lift.mcp.config import get_database_path
from lift.mcp.handlers import ToolHandler, format_error_response, format_success_response
from lift.mcp.schemas import (
    GetExerciseInfoInput,
    LogBodyweightInput,
    SearchExercisesInput,
    StartWorkoutInput,
)
from lift.services.body_service import BodyService
from lift.services.exercise_service import ExerciseService
from lift.services.workout_service import WorkoutService


logger = logging.getLogger(__name__)


class SearchExercisesTool(ToolHandler):
    """Tool for searching exercises."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """Initialize tool."""
        super().__init__(db)
        self.exercise_service = ExerciseService(self.db)

    def get_name(self) -> str:
        """Get tool name."""
        return "search_exercises"

    def get_description(self) -> str:
        """Get tool description."""
        return "Search for exercises by name, muscle group, category, or equipment type"

    def get_input_schema(self) -> dict[str, Any]:
        """Get input schema."""
        return SearchExercisesInput.model_json_schema()

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute tool."""
        try:
            input_data = SearchExercisesInput(**arguments)
        except ValidationError as e:
            return format_error_response(str(e), "ValidationError")

        try:
            # Use search if query provided, otherwise filter
            if input_data.query:
                exercises = self.exercise_service.search(input_data.query)
            else:
                exercises = self.exercise_service.get_all(
                    category=input_data.category,
                    muscle=input_data.muscle,
                    equipment=input_data.equipment,
                )

            # Limit results
            exercises = exercises[: input_data.limit]

            return format_success_response(
                {
                    "count": len(exercises),
                    "exercises": [
                        {
                            "id": ex.id,
                            "name": ex.name,
                            "category": ex.category.value,
                            "primary_muscle": ex.primary_muscle.value,
                            "equipment": ex.equipment.value,
                            "movement_type": ex.movement_type.value,
                        }
                        for ex in exercises
                    ],
                }
            )
        except Exception as e:
            logger.error(f"Error searching exercises: {e}")
            return format_error_response(str(e))


class GetExerciseInfoTool(ToolHandler):
    """Tool for getting exercise information."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """Initialize tool."""
        super().__init__(db)
        self.exercise_service = ExerciseService(self.db)

    def get_name(self) -> str:
        """Get tool name."""
        return "get_exercise_info"

    def get_description(self) -> str:
        """Get tool description."""
        return "Get detailed information about a specific exercise"

    def get_input_schema(self) -> dict[str, Any]:
        """Get input schema."""
        return GetExerciseInfoInput.model_json_schema()

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute tool."""
        try:
            input_data = GetExerciseInfoInput(**arguments)
        except ValidationError as e:
            return format_error_response(str(e), "ValidationError")

        try:
            exercise = self.exercise_service.get_by_name(input_data.exercise_name)
            if not exercise:
                return format_error_response(f"Exercise not found: {input_data.exercise_name}")

            return format_success_response(
                {
                    "id": exercise.id,
                    "name": exercise.name,
                    "category": exercise.category.value,
                    "primary_muscle": exercise.primary_muscle.value,
                    "secondary_muscles": [m.value for m in exercise.secondary_muscles],
                    "equipment": exercise.equipment.value,
                    "movement_type": exercise.movement_type.value,
                    "is_custom": exercise.is_custom,
                }
            )
        except Exception as e:
            logger.error(f"Error getting exercise info: {e}")
            return format_error_response(str(e))


class StartWorkoutTool(ToolHandler):
    """Tool for starting a workout session."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """Initialize tool."""
        super().__init__(db)
        self.workout_service = WorkoutService(self.db)

    def get_name(self) -> str:
        """Get tool name."""
        return "start_workout"

    def get_description(self) -> str:
        """Get tool description."""
        return "Start a new workout session"

    def get_input_schema(self) -> dict[str, Any]:
        """Get input schema."""
        return StartWorkoutInput.model_json_schema()

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute tool."""
        try:
            input_data = StartWorkoutInput(**arguments)
        except ValidationError as e:
            return format_error_response(str(e), "ValidationError")

        try:
            # Create workout
            workout_create = WorkoutCreate(
                name=input_data.name,
                program_workout_id=input_data.program_workout_id,
                bodyweight=Decimal(str(input_data.bodyweight)) if input_data.bodyweight else None,
                bodyweight_unit=WeightUnit(input_data.bodyweight_unit),
            )

            workout = self.workout_service.create_workout(workout_create)

            return format_success_response(
                {
                    "workout_id": workout.id,
                    "date": str(workout.date),
                    "name": workout.name,
                },
                message=f"Workout started: {workout.name or 'Unnamed Workout'}",
            )
        except Exception as e:
            logger.error(f"Error starting workout: {e}")
            return format_error_response(str(e))


class LogBodyweightTool(ToolHandler):
    """Tool for logging bodyweight."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """Initialize tool."""
        super().__init__(db)
        self.body_service = BodyService(self.db)

    def get_name(self) -> str:
        """Get tool name."""
        return "log_bodyweight"

    def get_description(self) -> str:
        """Get tool description."""
        return "Log a bodyweight measurement"

    def get_input_schema(self) -> dict[str, Any]:
        """Get input schema."""
        return LogBodyweightInput.model_json_schema()

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute tool."""
        try:
            input_data = LogBodyweightInput(**arguments)
        except ValidationError as e:
            return format_error_response(str(e), "ValidationError")

        try:
            weight_val = Decimal(str(input_data.weight))
            unit = WeightUnit(input_data.unit)

            measurement = self.body_service.log_weight(weight_val, unit)

            return format_success_response(
                {
                    "date": str(measurement.date),
                    "weight": float(measurement.weight) if measurement.weight else None,
                    "unit": measurement.weight_unit.value,
                },
                message=f"Bodyweight logged: {weight_val} {unit.value}",
            )
        except Exception as e:
            logger.error(f"Error logging bodyweight: {e}")
            return format_error_response(str(e))


def get_all_tool_handlers() -> list[ToolHandler]:
    """
    Get all available tool handlers.

    Returns:
        List of tool handler instances
    """
    db_path = get_database_path()
    db = DatabaseManager(db_path)

    return [
        SearchExercisesTool(db),
        GetExerciseInfoTool(db),
        StartWorkoutTool(db),
        LogBodyweightTool(db),
    ]
