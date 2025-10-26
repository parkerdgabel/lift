"""Tests for workout CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from lift.main import app


runner = CliRunner()


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Create a temporary database path."""
    db_path = tmp_path / "test.duckdb"
    return str(db_path)


@pytest.fixture
def initialized_db(temp_db: str) -> str:
    """Create and initialize a temporary database."""
    result = runner.invoke(app, ["--db-path", temp_db, "init"])
    assert result.exit_code == 0
    return temp_db


@pytest.mark.cli
class TestWorkoutListCommands:
    """Test workout list and history commands."""

    def test_workout_incomplete_empty(self, initialized_db: str) -> None:
        """Test listing incomplete workouts when none exist."""
        result = runner.invoke(app, ["--db-path", initialized_db, "workout", "incomplete"])

        assert result.exit_code == 0
        assert "No incomplete workouts" in result.stdout

    def test_workout_history_empty(self, initialized_db: str) -> None:
        """Test workout history when no workouts exist."""
        result = runner.invoke(app, ["--db-path", initialized_db, "workout", "history"])

        assert result.exit_code == 0
        # Should succeed even with no workouts

    def test_workout_last_empty(self, initialized_db: str) -> None:
        """Test getting last workout when none exists."""
        result = runner.invoke(app, ["--db-path", initialized_db, "workout", "last"])

        assert result.exit_code == 0
        assert "No workouts found" in result.stdout or "No recent workout" in result.stdout


@pytest.mark.cli
class TestWorkoutLog:
    """Test basic workout logging."""

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_workout_log_quick_success(self, initialized_db: str) -> None:
        """Test quick workout logging with exercise ID."""
        # TODO: Rewrite to use only CLI commands for data setup


@pytest.mark.cli
class TestWorkoutCompletion:
    """Test workout completion and abandonment."""

    def test_complete_nonexistent_workout(self, initialized_db: str) -> None:
        """Test completing a workout that doesn't exist."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "workout", "complete", "--id", "99999"]
        )

        # Should fail gracefully
        assert result.exit_code != 0 or "not found" in result.stdout.lower()

    def test_abandon_nonexistent_workout(self, initialized_db: str) -> None:
        """Test abandoning a workout that doesn't exist."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "workout", "abandon", "--id", "99999"]
        )

        # Should fail gracefully
        assert result.exit_code != 0 or "not found" in result.stdout.lower()


@pytest.mark.cli
class TestWorkoutDelete:
    """Test workout deletion."""

    def test_delete_nonexistent_workout(self, initialized_db: str) -> None:
        """Test deleting a workout that doesn't exist."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "workout", "delete", "99999"], input="y\n"
        )

        # Should handle gracefully
        assert result.exit_code != 0 or "not found" in result.stdout.lower()

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_delete_workout_cancel(self, initialized_db: str) -> None:
        """Test canceling workout deletion."""
        # TODO: Rewrite to use only CLI commands for data setup


@pytest.mark.cli
class TestWorkoutDisplay:
    """Test workout display commands."""

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_workout_last_with_data(self, initialized_db: str) -> None:
        """Test displaying last workout when data exists."""
        # TODO: Rewrite to use only CLI commands for data setup

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_workout_history_with_limit(self, initialized_db: str) -> None:
        """Test workout history with limit parameter."""
        # TODO: Rewrite to use only CLI commands for data setup

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_workout_incomplete_with_data(self, initialized_db: str) -> None:
        """Test listing incomplete workouts when they exist."""
        # TODO: Rewrite to use only CLI commands for data setup


@pytest.mark.cli
class TestWorkoutResume:
    """Test workout resume functionality."""

    @pytest.mark.skip(reason="Resume command implementation needs verification")
    def test_resume_no_incomplete(self, initialized_db: str) -> None:
        """Test resuming when no incomplete workouts exist."""
        result = runner.invoke(app, ["--db-path", initialized_db, "workout", "resume"])

        assert result.exit_code == 0
        assert "No incomplete workouts" in result.stdout

    def test_resume_with_id_not_found(self, initialized_db: str) -> None:
        """Test resuming with invalid workout ID."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "workout", "resume", "--id", "99999"]
        )

        # Should handle gracefully
        assert result.exit_code != 0 or "not found" in result.stdout.lower()
