"""Pydantic schemas for MCP server requests and responses."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Tool Input Schemas
# ============================================================================


class StartWorkoutInput(BaseModel):
    """Input schema for start_workout tool."""

    name: str | None = Field(None, description="Name for the workout session")
    program_workout_id: int | None = Field(None, description="Program workout template ID")
    bodyweight: float | None = Field(None, description="Current bodyweight")
    bodyweight_unit: str = Field("lbs", description="Unit for bodyweight (lbs or kg)")


class LogWorkoutSetInput(BaseModel):
    """Input schema for log_workout_set tool."""

    workout_id: int = Field(..., description="ID of the active workout")
    exercise_name: str = Field(..., description="Name of the exercise")
    weight: float = Field(..., description="Weight used for the set")
    reps: int = Field(..., description="Number of reps completed")
    rpe: float | None = Field(None, description="Rate of Perceived Exertion (1-10)", ge=1, le=10)
    notes: str | None = Field(None, description="Optional notes about the set")
    set_type: str = Field("working", description="Type of set (working, warmup, dropset, etc.)")


class FinishWorkoutInput(BaseModel):
    """Input schema for finish_workout tool."""

    workout_id: int = Field(..., description="ID of the workout to finish")
    duration_minutes: int | None = Field(None, description="Total workout duration in minutes")
    rating: int | None = Field(None, description="Workout quality rating (1-10)", ge=1, le=10)
    notes: str | None = Field(None, description="Optional workout notes")


class SearchExercisesInput(BaseModel):
    """Input schema for search_exercises tool."""

    query: str | None = Field(None, description="Search query for exercise name")
    muscle: str | None = Field(None, description="Filter by primary muscle group")
    category: str | None = Field(None, description="Filter by category (Push, Pull, Legs, Core)")
    equipment: str | None = Field(None, description="Filter by equipment type")
    limit: int = Field(50, description="Maximum number of results", gt=0, le=200)


class GetExerciseInfoInput(BaseModel):
    """Input schema for get_exercise_info tool."""

    exercise_name: str = Field(..., description="Name of the exercise")


class GetWorkoutSummaryInput(BaseModel):
    """Input schema for get_workout_summary tool."""

    period: str = Field("week", description="Time period (week, month, year, or custom)")
    start_date: str | None = Field(None, description="Start date for custom period (YYYY-MM-DD)")
    end_date: str | None = Field(None, description="End date for custom period (YYYY-MM-DD)")


class GetExerciseProgressionInput(BaseModel):
    """Input schema for get_exercise_progression tool."""

    exercise_name: str = Field(..., description="Name of the exercise")
    limit: int = Field(10, description="Number of recent workouts to analyze", gt=0, le=50)


class GetPersonalRecordsInput(BaseModel):
    """Input schema for get_personal_records tool."""

    exercise_name: str | None = Field(None, description="Filter by specific exercise")


class AnalyzeVolumeInput(BaseModel):
    """Input schema for analyze_volume tool."""

    weeks: int = Field(4, description="Number of weeks to analyze", gt=0, le=52)
    muscle_group: str | None = Field(None, description="Filter by specific muscle group")


class LogBodyweightInput(BaseModel):
    """Input schema for log_bodyweight tool."""

    weight: float = Field(..., description="Bodyweight value", gt=0)
    unit: str = Field("lbs", description="Unit (lbs or kg)")
    date: str | None = Field(
        None, description="Date of measurement (YYYY-MM-DD), defaults to today"
    )


class LogMeasurementInput(BaseModel):
    """Input schema for log_measurement tool."""

    measurement_type: str = Field(
        ..., description="Type of measurement (chest, waist, bicep, etc.)"
    )
    value: float = Field(..., description="Measurement value", gt=0)
    unit: str = Field("in", description="Unit (in or cm)")
    notes: str | None = Field(None, description="Optional notes")


class GetProgressReportInput(BaseModel):
    """Input schema for get_progress_report tool."""

    weeks: int = Field(4, description="Number of weeks to compare", gt=0, le=52)


class ActivateProgramInput(BaseModel):
    """Input schema for activate_program tool."""

    program_name: str = Field(..., description="Name of the program to activate")


# ============================================================================
# Resource Response Schemas
# ============================================================================


class WorkoutResource(BaseModel):
    """Schema for workout resource data."""

    id: int
    date: datetime
    name: str | None = None
    bodyweight: Decimal | None = None
    bodyweight_unit: str = "lbs"
    duration_minutes: int | None = None
    rating: int | None = None
    notes: str | None = None
    total_sets: int = 0
    total_volume: Decimal = Decimal("0")
    exercises: list[str] = []


class ExerciseResource(BaseModel):
    """Schema for exercise resource data."""

    id: int
    name: str
    category: str
    primary_muscle: str
    secondary_muscles: list[str]
    equipment: str
    movement_type: str
    is_custom: bool


class ProgramResource(BaseModel):
    """Schema for program resource data."""

    id: int
    name: str
    description: str | None = None
    split_type: str
    days_per_week: int
    is_active: bool = False
    workouts: list[dict[str, Any]] = []


class StatsResource(BaseModel):
    """Schema for statistics resource data."""

    total_workouts: int
    total_volume: Decimal
    total_sets: int
    avg_duration: float
    avg_rpe: float
    total_exercises: int
    period_start: str | None = None
    period_end: str | None = None


class PersonalRecordResource(BaseModel):
    """Schema for personal record resource data."""

    exercise_name: str
    record_type: str
    value: Decimal
    weight: Decimal | None = None
    reps: int | None = None
    date: datetime


class BodyMeasurementResource(BaseModel):
    """Schema for body measurement resource data."""

    date: datetime
    weight: Decimal | None = None
    weight_unit: str = "lbs"
    chest: Decimal | None = None
    waist: Decimal | None = None
    hips: Decimal | None = None
    measurement_unit: str = "in"
