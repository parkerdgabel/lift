"""Tests for workout formatting utilities."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lift.core.models import Set, SetType, WeightUnit, Workout, WorkoutSummary
from lift.utils.workout_formatters import (
    format_exercise_performance,
    format_program_prescription,
    format_program_workout_header,
    format_progress_indicator,
    format_set_completion,
    format_set_table,
    format_workout_complete,
    format_workout_header,
    format_workout_list,
    format_workout_summary,
)


@pytest.mark.formatter
class TestFormatWorkoutSummary:
    """Test workout summary formatting."""

    def test_basic_workout_summary(self) -> None:
        """Test formatting a basic workout summary."""
        workout = Workout(
            id=1,
            name="Push Day",
            date=datetime(2024, 1, 15, 10, 30),
            duration_minutes=60,
            bodyweight=Decimal("180.5"),
            bodyweight_unit=WeightUnit.LBS,
        )

        summary = WorkoutSummary(
            total_exercises=5,
            total_sets=15,
            total_volume=Decimal("5000"),
            avg_rpe=Decimal("8.5"),
        )

        result = format_workout_summary(workout, summary)

        assert isinstance(result, Panel)
        # Render to string to check content
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Push Day" in output
        assert "January 15, 2024" in output
        assert "60 minutes" in output
        assert "180.5" in output
        assert "5" in output  # total exercises
        assert "15" in output  # total sets

    def test_workout_summary_with_rating(self) -> None:
        """Test workout summary with rating."""
        workout = Workout(
            id=1,
            name="Test Workout",
            date=datetime.now(),
            rating=4,
        )

        summary = WorkoutSummary(
            total_exercises=3,
            total_sets=10,
            total_volume=Decimal("1000"),
        )

        result = format_workout_summary(workout, summary)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should contain star rating
        assert "★" in output

    def test_workout_summary_with_notes(self) -> None:
        """Test workout summary with notes."""
        workout = Workout(
            id=1,
            name="Test",
            date=datetime.now(),
            notes="Felt strong today!",
        )

        summary = WorkoutSummary(
            total_exercises=1,
            total_sets=3,
            total_volume=Decimal("500"),
        )

        result = format_workout_summary(workout, summary)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Felt strong today!" in output

    def test_workout_summary_minimal(self) -> None:
        """Test workout summary with minimal data."""
        workout = Workout(
            id=1,
            name=None,  # No name
            date=datetime.now(),
        )

        summary = WorkoutSummary(
            total_exercises=0,
            total_sets=0,
            total_volume=Decimal("0"),
        )

        result = format_workout_summary(workout, summary)
        assert isinstance(result, Panel)


@pytest.mark.formatter
class TestFormatSetTable:
    """Test set table formatting."""

    def test_set_table_with_exercise_names(self) -> None:
        """Test set table with exercise names shown."""
        sets = [
            Set(
                id=1,
                workout_id=1,
                exercise_id=10,
                set_number=1,
                weight=Decimal("185"),
                weight_unit=WeightUnit.LBS,
                reps=10,
                rpe=Decimal("8.0"),
                set_type=SetType.WORKING,
                completed_at=datetime.now(),
            ),
            Set(
                id=2,
                workout_id=1,
                exercise_id=10,
                set_number=2,
                weight=Decimal("185"),
                weight_unit=WeightUnit.LBS,
                reps=10,
                rpe=Decimal("8.5"),
                set_type=SetType.WORKING,
                completed_at=datetime.now(),
            ),
        ]

        result = format_set_table(sets, show_exercise_name=True)

        assert isinstance(result, Table)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Exercise 10" in output
        assert "185" in output
        assert "10" in output

    def test_set_table_without_exercise_names(self) -> None:
        """Test set table without exercise names."""
        sets = [
            Set(
                id=1,
                workout_id=1,
                exercise_id=10,
                set_number=1,
                weight=Decimal("225"),
                weight_unit=WeightUnit.LBS,
                reps=5,
                set_type=SetType.WORKING,
                completed_at=datetime.now(),
            ),
        ]

        result = format_set_table(sets, show_exercise_name=False)

        assert isinstance(result, Table)

    def test_set_table_with_no_rpe(self) -> None:
        """Test set table when RPE is not provided."""
        sets = [
            Set(
                id=1,
                workout_id=1,
                exercise_id=10,
                set_number=1,
                weight=Decimal("100"),
                weight_unit=WeightUnit.LBS,
                reps=12,
                rpe=None,
                set_type=SetType.WARMUP,
                completed_at=datetime.now(),
            ),
        ]

        result = format_set_table(sets)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "-" in output  # Should show dash for missing RPE

    def test_set_table_multiple_exercises(self) -> None:
        """Test set table with multiple different exercises."""
        sets = [
            Set(
                id=1,
                workout_id=1,
                exercise_id=10,
                set_number=1,
                weight=Decimal("185"),
                weight_unit=WeightUnit.LBS,
                reps=10,
                set_type=SetType.WORKING,
                completed_at=datetime.now(),
            ),
            Set(
                id=2,
                workout_id=1,
                exercise_id=20,
                set_number=1,
                weight=Decimal("225"),
                weight_unit=WeightUnit.LBS,
                reps=5,
                set_type=SetType.WORKING,
                completed_at=datetime.now(),
            ),
        ]

        result = format_set_table(sets, show_exercise_name=True)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Exercise 10" in output
        assert "Exercise 20" in output

    def test_set_table_empty(self) -> None:
        """Test set table with no sets."""
        result = format_set_table([])
        assert isinstance(result, Table)


@pytest.mark.formatter
class TestFormatExercisePerformance:
    """Test exercise performance formatting."""

    def test_exercise_performance_with_data(self) -> None:
        """Test formatting exercise performance with sets."""
        sets = [
            {
                "weight": Decimal("185"),
                "reps": 10,
                "rpe": Decimal("8.0"),
                "weight_unit": "lbs",
            },
            {
                "weight": Decimal("185"),
                "reps": 9,
                "rpe": Decimal("8.5"),
                "weight_unit": "lbs",
            },
        ]

        result = format_exercise_performance(
            "Bench Press", sets, last_workout_date=datetime.now() - timedelta(days=3)
        )

        assert isinstance(result, Panel)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Bench Press" in output
        assert "3 days ago" in output
        assert "185" in output

    def test_exercise_performance_today(self) -> None:
        """Test exercise performance when last workout was today."""
        sets = [{"weight": Decimal("100"), "reps": 10, "weight_unit": "lbs"}]

        result = format_exercise_performance("Curls", sets, last_workout_date=datetime.now())

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "earlier today" in output

    def test_exercise_performance_yesterday(self) -> None:
        """Test exercise performance when last workout was yesterday."""
        sets = [{"weight": Decimal("100"), "reps": 10, "weight_unit": "lbs"}]

        result = format_exercise_performance(
            "Squats", sets, last_workout_date=datetime.now() - timedelta(days=1)
        )

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "yesterday" in output

    def test_exercise_performance_no_data(self) -> None:
        """Test exercise performance with no previous data."""
        result = format_exercise_performance("Deadlift", [], last_workout_date=None)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "No previous performance data" in output

    def test_exercise_performance_more_than_five_sets(self) -> None:
        """Test that only first 5 sets are shown."""
        sets = [{"weight": Decimal("100"), "reps": 10, "weight_unit": "lbs"} for _ in range(10)]

        result = format_exercise_performance("Test Exercise", sets)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should show Set 1-5 but not Set 6
        assert "Set 5" in output
        assert "Set 6" not in output


@pytest.mark.formatter
class TestFormatWorkoutHeader:
    """Test workout header formatting."""

    def test_workout_header_basic(self) -> None:
        """Test basic workout header."""
        result = format_workout_header("Push Day", datetime(2024, 1, 15, 14, 30), bodyweight=None)

        assert isinstance(result, Panel)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Push Day" in output
        assert "02:30 PM" in output

    def test_workout_header_with_bodyweight(self) -> None:
        """Test workout header with bodyweight."""
        result = format_workout_header("Pull Day", datetime.now(), bodyweight=Decimal("182.5"))

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Pull Day" in output
        assert "182.5" in output


@pytest.mark.formatter
class TestFormatSetCompletion:
    """Test set completion message formatting."""

    def test_set_completion_basic(self) -> None:
        """Test basic set completion."""
        result = format_set_completion(
            weight=Decimal("185"), reps=10, rpe=None, volume=None, is_pr=False
        )

        assert isinstance(result, Text)
        output = str(result)
        assert "185" in output
        assert "10" in output

    def test_set_completion_with_pr(self) -> None:
        """Test set completion with PR flag."""
        result = format_set_completion(weight=Decimal("225"), reps=5, is_pr=True)

        output = str(result)
        assert "PR" in output or "🏆" in output
        assert "225" in output

    def test_set_completion_with_rpe(self) -> None:
        """Test set completion with RPE."""
        result = format_set_completion(weight=Decimal("135"), reps=12, rpe=Decimal("7.5"))

        output = str(result)
        assert "7.5" in output

    def test_set_completion_with_volume(self) -> None:
        """Test set completion with volume."""
        result = format_set_completion(weight=Decimal("185"), reps=10, volume=Decimal("1850"))

        output = str(result)
        assert "1,850" in output or "1850" in output


@pytest.mark.formatter
class TestFormatWorkoutComplete:
    """Test workout completion summary formatting."""

    def test_workout_complete_basic(self) -> None:
        """Test basic workout completion summary."""
        result = format_workout_complete(
            duration_minutes=75,
            total_volume=Decimal("5000"),
            total_sets=20,
            exercise_count=6,
        )

        assert isinstance(result, Panel)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "75" in output
        assert "5,000" in output or "5000" in output
        assert "20" in output
        assert "6" in output
        assert "COMPLETE" in output

    def test_workout_complete_large_volume(self) -> None:
        """Test workout completion with large volume."""
        result = format_workout_complete(
            duration_minutes=90,
            total_volume=Decimal("15000"),
            total_sets=30,
            exercise_count=8,
        )

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "15,000" in output or "15000" in output


@pytest.mark.formatter
class TestFormatWorkoutList:
    """Test workout list formatting."""

    def test_workout_list_basic(self) -> None:
        """Test formatting a list of workouts."""
        workouts = [
            (
                Workout(
                    id=1,
                    name="Push Day",
                    date=datetime(2024, 1, 15),
                    duration_minutes=60,
                ),
                WorkoutSummary(
                    total_exercises=5,
                    total_sets=15,
                    total_volume=Decimal("5000"),
                ),
            ),
            (
                Workout(
                    id=2,
                    name="Pull Day",
                    date=datetime(2024, 1, 17),
                    duration_minutes=55,
                ),
                WorkoutSummary(
                    total_exercises=4,
                    total_sets=12,
                    total_volume=Decimal("4500"),
                ),
            ),
        ]

        result = format_workout_list(workouts)

        assert isinstance(result, Table)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Push Day" in output
        assert "Pull Day" in output
        assert "60 min" in output
        assert "55 min" in output

    def test_workout_list_no_duration(self) -> None:
        """Test workout list with no duration."""
        workouts = [
            (
                Workout(
                    id=1,
                    name="Test",
                    date=datetime.now(),
                    duration_minutes=None,
                ),
                WorkoutSummary(
                    total_exercises=1,
                    total_sets=3,
                    total_volume=Decimal("500"),
                ),
            ),
        ]

        result = format_workout_list(workouts)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "-" in output  # Should show dash for missing duration

    def test_workout_list_empty(self) -> None:
        """Test empty workout list."""
        result = format_workout_list([])
        assert isinstance(result, Table)


@pytest.mark.formatter
class TestFormatProgressIndicator:
    """Test progress indicator formatting."""

    def test_progress_indicator_basic(self) -> None:
        """Test basic progress indicator."""
        result = format_progress_indicator(5, 10, label="Sets")

        assert isinstance(result, Text)
        output = str(result)
        assert "5" in output
        assert "10" in output
        assert "50" in output  # 50%

    def test_progress_indicator_complete(self) -> None:
        """Test progress indicator at 100%."""
        result = format_progress_indicator(10, 10)

        output = str(result)
        assert "100" in output

    def test_progress_indicator_zero_total(self) -> None:
        """Test progress indicator with zero total."""
        result = format_progress_indicator(0, 0)

        output = str(result)
        assert "0" in output

    def test_progress_indicator_no_label(self) -> None:
        """Test progress indicator without label."""
        result = format_progress_indicator(3, 12)

        output = str(result)
        assert "3" in output
        assert "12" in output
        assert "25" in output  # 25%


@pytest.mark.formatter
class TestFormatProgramWorkoutHeader:
    """Test program workout header formatting."""

    def test_program_workout_header_basic(self) -> None:
        """Test basic program workout header."""
        result = format_program_workout_header(
            program_name="5/3/1",
            workout_name="Week 1 - Squat",
            workout_position=1,
            total_workouts=12,
            num_exercises=5,
            estimated_duration=None,
        )

        assert isinstance(result, Panel)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "5/3/1" in output
        assert "Week 1 - Squat" in output
        assert "Day 1 of 12" in output
        assert "5 exercises" in output

    def test_program_workout_header_with_duration(self) -> None:
        """Test program workout header with estimated duration."""
        result = format_program_workout_header(
            program_name="PPL",
            workout_name="Push A",
            workout_position=1,
            total_workouts=6,
            num_exercises=6,
            estimated_duration=75,
        )

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "75 min" in output


@pytest.mark.formatter
class TestFormatProgramPrescription:
    """Test program prescription formatting."""

    def test_program_prescription_basic(self) -> None:
        """Test basic program prescription."""
        program_exercise = {
            "target_sets": 4,
            "target_reps_min": 8,
            "target_reps_max": 10,
        }

        result = format_program_prescription("Bench Press", program_exercise)

        assert isinstance(result, Panel)
        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "4 sets" in output
        assert "8-10 reps" in output

    def test_program_prescription_same_rep_range(self) -> None:
        """Test program prescription with same min/max reps."""
        program_exercise = {
            "target_sets": 5,
            "target_reps_min": 5,
            "target_reps_max": 5,
        }

        result = format_program_prescription("Squat", program_exercise)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "5 sets" in output
        assert "5 reps" in output

    def test_program_prescription_with_rpe(self) -> None:
        """Test program prescription with RPE."""
        program_exercise = {
            "target_sets": 3,
            "target_reps_min": 10,
            "target_reps_max": 12,
            "target_rpe": Decimal("8.5"),
        }

        result = format_program_prescription("Lateral Raise", program_exercise)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "8.5" in output

    def test_program_prescription_with_rest(self) -> None:
        """Test program prescription with rest period."""
        program_exercise = {
            "target_sets": 4,
            "target_reps_min": 5,
            "target_reps_max": 8,
            "rest_seconds": 180,
        }

        result = format_program_prescription("Deadlift", program_exercise)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "3m" in output  # 180 seconds = 3 minutes

    def test_program_prescription_with_rest_minutes_and_seconds(self) -> None:
        """Test program prescription with rest in minutes and seconds."""
        program_exercise = {
            "target_sets": 3,
            "target_reps_min": 12,
            "target_reps_max": 15,
            "rest_seconds": 90,  # 1m 30s
        }

        result = format_program_prescription("Leg Press", program_exercise)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "1m 30s" in output or "90s" in output

    def test_program_prescription_with_tempo(self) -> None:
        """Test program prescription with tempo."""
        program_exercise = {
            "target_sets": 4,
            "target_reps_min": 8,
            "target_reps_max": 10,
            "tempo": "3-1-1-0",
        }

        result = format_program_prescription("RDL", program_exercise)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "3-1-1-0" in output

    def test_program_prescription_with_notes(self) -> None:
        """Test program prescription with notes."""
        program_exercise = {
            "target_sets": 3,
            "target_reps_min": 10,
            "target_reps_max": 12,
            "notes": "Focus on mind-muscle connection",
        }

        result = format_program_prescription("Cable Fly", program_exercise)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "Focus on mind-muscle connection" in output

    def test_program_prescription_all_fields(self) -> None:
        """Test program prescription with all fields."""
        program_exercise = {
            "target_sets": 4,
            "target_reps_min": 6,
            "target_reps_max": 8,
            "target_rpe": Decimal("9.0"),
            "rest_seconds": 240,
            "tempo": "2-0-2-0",
            "notes": "Increase weight if RPE < 8",
        }

        result = format_program_prescription("Barbell Row", program_exercise)

        console = Console()
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        assert "4 sets" in output
        assert "6-8 reps" in output
        assert "9.0" in output
        assert "4m" in output
        assert "2-0-2-0" in output
        assert "Increase weight if RPE < 8" in output
