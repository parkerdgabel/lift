"""Pydantic models for data validation and serialization."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS
# ============================================================================


class CategoryType(str, Enum):
    """Exercise category types."""

    PUSH = "Push"
    PULL = "Pull"
    LEGS = "Legs"
    CORE = "Core"


class MuscleGroup(str, Enum):
    """Muscle group classifications."""

    # Upper body
    CHEST = "Chest"
    BACK = "Back"
    SHOULDERS = "Shoulders"
    BICEPS = "Biceps"
    TRICEPS = "Triceps"
    FOREARMS = "Forearms"

    # Lower body
    QUADS = "Quads"
    HAMSTRINGS = "Hamstrings"
    GLUTES = "Glutes"
    CALVES = "Calves"

    # Core
    ABS = "Abs"
    OBLIQUES = "Obliques"
    LOWER_BACK = "Lower Back"


class EquipmentType(str, Enum):
    """Equipment types."""

    BARBELL = "Barbell"
    DUMBBELL = "Dumbbell"
    CABLE = "Cable"
    MACHINE = "Machine"
    BODYWEIGHT = "Bodyweight"
    RESISTANCE_BAND = "Resistance Band"
    KETTLEBELL = "Kettlebell"
    EZ_BAR = "EZ Bar"
    TRAP_BAR = "Trap Bar"
    SMITH_MACHINE = "Smith Machine"


class MovementType(str, Enum):
    """Movement classification."""

    COMPOUND = "Compound"
    ISOLATION = "Isolation"


class SetType(str, Enum):
    """Type of set performed."""

    WARMUP = "warmup"
    WORKING = "working"
    DROPSET = "dropset"
    FAILURE = "failure"
    AMRAP = "amrap"  # As Many Reps As Possible
    REST_PAUSE = "rest_pause"


class WeightUnit(str, Enum):
    """Weight measurement units."""

    LBS = "lbs"
    KG = "kg"


class MeasurementUnit(str, Enum):
    """Body measurement units."""

    INCHES = "in"
    CENTIMETERS = "cm"


class SplitType(str, Enum):
    """Training split types."""

    PPL = "PPL"  # Push Pull Legs
    UPPER_LOWER = "Upper/Lower"
    FULL_BODY = "Full Body"
    BRO_SPLIT = "Bro Split"
    ARNOLD_SPLIT = "Arnold Split"
    CUSTOM = "Custom"


class RecordType(str, Enum):
    """Personal record types."""

    ONE_RM = "1RM"
    THREE_RM = "3RM"
    FIVE_RM = "5RM"
    TEN_RM = "10RM"
    VOLUME = "volume"
    MAX_WEIGHT = "max_weight"


# ============================================================================
# EXERCISE MODELS
# ============================================================================


class ExerciseBase(BaseModel):
    """Base exercise model."""

    name: str = Field(..., min_length=1, max_length=200)
    category: CategoryType
    primary_muscle: MuscleGroup
    secondary_muscles: list[MuscleGroup] = Field(default_factory=list)
    equipment: EquipmentType
    movement_type: MovementType
    instructions: str | None = None
    video_url: str | None = None


class ExerciseCreate(ExerciseBase):
    """Model for creating an exercise."""

    is_custom: bool = True


class Exercise(ExerciseBase):
    """Full exercise model."""

    id: int
    is_custom: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# PROGRAM MODELS
# ============================================================================


class ProgramBase(BaseModel):
    """Base program model."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    split_type: SplitType
    days_per_week: int = Field(..., ge=1, le=7)
    duration_weeks: int | None = Field(None, ge=1)


class ProgramCreate(ProgramBase):
    """Model for creating a program."""


class Program(ProgramBase):
    """Full program model."""

    id: int
    is_active: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgramWorkoutBase(BaseModel):
    """Base program workout model."""

    name: str = Field(..., min_length=1, max_length=200)
    day_number: int | None = Field(None, ge=1, le=7)
    description: str | None = None
    estimated_duration_minutes: int | None = Field(None, ge=1)


class ProgramWorkoutCreate(ProgramWorkoutBase):
    """Model for creating a program workout."""

    program_id: int


class ProgramWorkout(ProgramWorkoutBase):
    """Full program workout model."""

    id: int
    program_id: int

    model_config = {"from_attributes": True}


class ProgramExerciseBase(BaseModel):
    """Base program exercise model."""

    exercise_id: int
    order_number: int = Field(..., ge=1)
    target_sets: int = Field(..., ge=1)
    target_reps_min: int = Field(..., ge=1)
    target_reps_max: int = Field(..., ge=1)
    target_rpe: Decimal | None = Field(None, ge=6, le=10)
    rest_seconds: int | None = Field(None, ge=0)
    tempo: str | None = None
    notes: str | None = None
    is_superset: bool = False
    superset_group: int | None = None

    @field_validator("target_reps_max")
    @classmethod
    def validate_rep_range(cls, v: int, info) -> int:
        """Ensure max reps >= min reps."""
        if "target_reps_min" in info.data and v < info.data["target_reps_min"]:
            raise ValueError("target_reps_max must be >= target_reps_min")
        return v


class ProgramExerciseCreate(ProgramExerciseBase):
    """Model for creating a program exercise."""

    program_workout_id: int


class ProgramExercise(ProgramExerciseBase):
    """Full program exercise model."""

    id: int
    program_workout_id: int

    model_config = {"from_attributes": True}


# ============================================================================
# WORKOUT MODELS
# ============================================================================


class WorkoutBase(BaseModel):
    """Base workout model."""

    name: str | None = None
    bodyweight: Decimal | None = Field(None, gt=0)
    bodyweight_unit: WeightUnit = WeightUnit.LBS
    notes: str | None = None
    rating: int | None = Field(None, ge=1, le=5)


class WorkoutCreate(WorkoutBase):
    """Model for creating a workout."""

    program_workout_id: int | None = None
    date: datetime = Field(default_factory=datetime.now)


class WorkoutUpdate(BaseModel):
    """Model for updating a workout."""

    name: str | None = None
    duration_minutes: int | None = Field(None, ge=1)
    bodyweight: Decimal | None = Field(None, gt=0)
    bodyweight_unit: WeightUnit | None = None
    notes: str | None = None
    rating: int | None = Field(None, ge=1, le=5)
    completed: bool | None = None


class Workout(WorkoutBase):
    """Full workout model."""

    id: int
    date: datetime
    program_workout_id: int | None = None
    duration_minutes: int | None = None
    completed: bool = True

    model_config = {"from_attributes": True}


# ============================================================================
# SET MODELS
# ============================================================================


class SetBase(BaseModel):
    """Base set model."""

    exercise_id: int
    set_number: int = Field(..., ge=1)
    weight: Decimal = Field(..., ge=0)
    weight_unit: WeightUnit = WeightUnit.LBS
    reps: int = Field(..., ge=1)
    rpe: Decimal | None = Field(None, ge=6, le=10)
    tempo: str | None = None
    set_type: SetType = SetType.WORKING
    rest_seconds: int | None = Field(None, ge=0)
    is_superset: bool = False
    superset_group: int | None = None
    notes: str | None = None


class SetCreate(SetBase):
    """Model for creating a set."""

    workout_id: int


class Set(SetBase):
    """Full set model."""

    id: int
    workout_id: int
    completed_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# PERSONAL RECORD MODELS
# ============================================================================


class PersonalRecordBase(BaseModel):
    """Base personal record model."""

    exercise_id: int
    record_type: RecordType
    value: Decimal = Field(..., gt=0)
    reps: int | None = Field(None, ge=1)
    weight: Decimal | None = Field(None, ge=0)
    weight_unit: WeightUnit = WeightUnit.LBS


class PersonalRecordCreate(PersonalRecordBase):
    """Model for creating a personal record."""

    workout_id: int | None = None
    set_id: int | None = None
    date: datetime = Field(default_factory=datetime.now)


class PersonalRecord(PersonalRecordBase):
    """Full personal record model."""

    id: int
    date: datetime
    workout_id: int | None = None
    set_id: int | None = None

    model_config = {"from_attributes": True}


# ============================================================================
# BODY MEASUREMENT MODELS
# ============================================================================


class BodyMeasurementBase(BaseModel):
    """Base body measurement model."""

    weight: Decimal | None = Field(None, gt=0)
    weight_unit: WeightUnit = WeightUnit.LBS
    body_fat_pct: Decimal | None = Field(None, ge=0, le=100)

    # Circumference measurements
    neck: Decimal | None = Field(None, gt=0)
    shoulders: Decimal | None = Field(None, gt=0)
    chest: Decimal | None = Field(None, gt=0)
    waist: Decimal | None = Field(None, gt=0)
    hips: Decimal | None = Field(None, gt=0)

    bicep_left: Decimal | None = Field(None, gt=0)
    bicep_right: Decimal | None = Field(None, gt=0)
    forearm_left: Decimal | None = Field(None, gt=0)
    forearm_right: Decimal | None = Field(None, gt=0)

    thigh_left: Decimal | None = Field(None, gt=0)
    thigh_right: Decimal | None = Field(None, gt=0)
    calf_left: Decimal | None = Field(None, gt=0)
    calf_right: Decimal | None = Field(None, gt=0)

    measurement_unit: MeasurementUnit = MeasurementUnit.INCHES
    notes: str | None = None


class BodyMeasurementCreate(BodyMeasurementBase):
    """Model for creating a body measurement."""

    date: datetime = Field(default_factory=datetime.now)


class BodyMeasurement(BodyMeasurementBase):
    """Full body measurement model."""

    id: int
    date: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# SETTINGS MODELS
# ============================================================================


class SettingBase(BaseModel):
    """Base setting model."""

    key: str
    value: str
    description: str | None = None


class SettingCreate(SettingBase):
    """Model for creating a setting."""


class Setting(SettingBase):
    """Full setting model."""

    updated_at: datetime

    model_config = {"from_attributes": True}
