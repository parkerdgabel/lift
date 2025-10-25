"""Resource handlers for MCP server."""

import logging
from datetime import datetime, timedelta
from typing import Any

from mcp.types import Resource

from lift.core.database import DatabaseManager
from lift.mcp.config import get_database_path
from lift.mcp.handlers import ResourceHandler
from lift.services.exercise_service import ExerciseService
from lift.services.stats_service import StatsService
from lift.services.workout_service import WorkoutService


logger = logging.getLogger(__name__)


class WorkoutResourceHandler(ResourceHandler):
    """Handler for workout-related resources."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """Initialize workout resource handler."""
        super().__init__(db)
        self.workout_service = WorkoutService(self.db)

    def can_handle(self, uri: str) -> bool:
        """Check if this handler can process the given URI."""
        return uri.startswith("lift://workouts/")

    def get_resource(self, uri: str) -> dict[str, Any]:
        """Get workout resource data."""
        if uri == "lift://workouts/recent":
            return self._get_recent_workouts()
        if uri.startswith("lift://workouts/"):
            # Extract workout ID
            workout_id_str = uri.split("/")[-1]
            try:
                workout_id = int(workout_id_str)
                return self._get_workout_details(workout_id)
            except ValueError:
                return {"error": f"Invalid workout ID: {workout_id_str}"}

        return {"error": f"Unknown workout resource: {uri}"}

    def list_resources(self) -> list[Resource]:
        """List available workout resources."""
        return [
            Resource(
                uri="lift://workouts/recent",
                name="Recent Workouts",
                description="Last 10 completed workouts",
                mimeType="application/json",
            ),
        ]

    def _get_recent_workouts(self) -> dict[str, Any]:
        """Get recent workouts."""
        workouts = self.workout_service.get_recent_workouts(limit=10)
        return {
            "workouts": [
                {
                    "id": w.id,
                    "date": str(w.date),
                    "name": w.name,
                    "duration_minutes": w.duration_minutes,
                    "rating": w.rating,
                }
                for w in workouts
            ]
        }

    def _get_workout_details(self, workout_id: int) -> dict[str, Any]:
        """Get detailed workout information."""
        workout = self.workout_service.get_workout(workout_id)
        if not workout:
            return {"error": f"Workout not found: {workout_id}"}

        summary = self.workout_service.get_workout_summary(workout_id)

        return {
            "id": workout.id,
            "date": str(workout.date),
            "name": workout.name,
            "bodyweight": float(workout.bodyweight) if workout.bodyweight else None,
            "duration_minutes": workout.duration_minutes,
            "rating": workout.rating,
            "notes": workout.notes,
            "summary": summary,
        }


class ExerciseResourceHandler(ResourceHandler):
    """Handler for exercise-related resources."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """Initialize exercise resource handler."""
        super().__init__(db)
        self.exercise_service = ExerciseService(self.db)

    def can_handle(self, uri: str) -> bool:
        """Check if this handler can process the given URI."""
        return uri.startswith("lift://exercises/")

    def get_resource(self, uri: str) -> dict[str, Any]:
        """Get exercise resource data."""
        if uri == "lift://exercises/library":
            return self._get_exercise_library()

        return {"error": f"Unknown exercise resource: {uri}"}

    def list_resources(self) -> list[Resource]:
        """List available exercise resources."""
        return [
            Resource(
                uri="lift://exercises/library",
                name="Exercise Library",
                description="Complete library of 137+ exercises",
                mimeType="application/json",
            ),
        ]

    def _get_exercise_library(self) -> dict[str, Any]:
        """Get complete exercise library."""
        exercises = self.exercise_service.get_all()
        return {
            "total_exercises": len(exercises),
            "exercises": [
                {
                    "id": ex.id,
                    "name": ex.name,
                    "category": ex.category.value,
                    "primary_muscle": ex.primary_muscle.value,
                    "equipment": ex.equipment.value,
                    "movement_type": ex.movement_type.value,
                    "is_custom": ex.is_custom,
                }
                for ex in exercises
            ],
        }


class StatsResourceHandler(ResourceHandler):
    """Handler for statistics-related resources."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """Initialize stats resource handler."""
        super().__init__(db)
        self.stats_service = StatsService(self.db)

    def can_handle(self, uri: str) -> bool:
        """Check if this handler can process the given URI."""
        return uri.startswith("lift://stats/")

    def get_resource(self, uri: str) -> dict[str, Any]:
        """Get statistics resource data."""
        if uri.startswith("lift://stats/summary"):
            # Parse query parameters
            if "?" in uri:
                query_part = uri.split("?")[1]
                params = dict(param.split("=") for param in query_part.split("&"))
                period = params.get("period", "week")
            else:
                period = "week"

            return self._get_summary(period)

        return {"error": f"Unknown stats resource: {uri}"}

    def list_resources(self) -> list[Resource]:
        """List available stats resources."""
        return [
            Resource(
                uri="lift://stats/summary?period=week",
                name="Weekly Summary",
                description="Training summary for the past week",
                mimeType="application/json",
            ),
            Resource(
                uri="lift://stats/summary?period=month",
                name="Monthly Summary",
                description="Training summary for the past month",
                mimeType="application/json",
            ),
        ]

    def _get_summary(self, period: str) -> dict[str, Any]:
        """Get training summary for a period."""
        # Calculate date range
        end_date = datetime.now()
        if period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)

        summary = self.stats_service.get_workout_summary(start_date, end_date)
        return {
            "period": period,
            "start_date": str(start_date.date()),
            "end_date": str(end_date.date()),
            "summary": summary,
        }


def get_all_resource_handlers() -> list[ResourceHandler]:
    """
    Get all available resource handlers.

    Returns:
        List of resource handler instances
    """
    db_path = get_database_path()
    db = DatabaseManager(db_path)

    return [
        WorkoutResourceHandler(db),
        ExerciseResourceHandler(db),
        StatsResourceHandler(db),
    ]
