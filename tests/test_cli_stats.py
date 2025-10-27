"""Tests for stats CLI commands."""

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
class TestStatsSummary:
    """Test stats summary commands."""

    def test_summary_empty(self, initialized_db: str) -> None:
        """Test stats summary with no data."""
        result = runner.invoke(app, ["--db-path", initialized_db, "stats", "summary"])

        assert result.exit_code == 0
        # Should show 0 workouts or similar

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_summary_with_data(self, initialized_db: str) -> None:
        """Test stats summary with workout data."""
        # TODO: Rewrite to use only CLI commands for data setup

    @pytest.mark.skip(reason="Period parameter not yet implemented in CLI")
    def test_summary_with_period(self, initialized_db: str) -> None:
        """Test stats summary with period parameter."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "stats", "summary", "--period", "month"]
        )

        assert result.exit_code == 0

    def test_summary_invalid_period(self, initialized_db: str) -> None:
        """Test stats summary with invalid period."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "stats", "summary", "--period", "invalid"]
        )

        # Should fail or handle gracefully
        assert result.exit_code != 0 or "invalid" in result.stdout.lower()


@pytest.mark.cli
class TestStatsExercise:
    """Test exercise statistics commands."""

    def test_exercise_stats_no_exercise(self, initialized_db: str) -> None:
        """Test exercise stats when exercise doesn't exist."""
        result = runner.invoke(app, ["--db-path", initialized_db, "stats", "exercise", "99999"])

        assert result.exit_code != 0 or "not found" in result.stdout.lower()

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_exercise_stats_with_data(self, initialized_db: str) -> None:
        """Test exercise stats with actual data."""
        # TODO: Rewrite to use only CLI commands for data setup


@pytest.mark.cli
class TestStatsVolume:
    """Test volume statistics commands."""

    def test_volume_empty(self, initialized_db: str) -> None:
        """Test volume stats with no data."""
        result = runner.invoke(app, ["--db-path", initialized_db, "stats", "volume"])

        assert result.exit_code == 0
        # Should handle empty case

    def test_volume_with_weeks(self, initialized_db: str) -> None:
        """Test volume stats with weeks parameter."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "stats", "volume", "--weeks", "12"]
        )

        assert result.exit_code == 0


@pytest.mark.cli
class TestStatsPR:
    """Test PR (personal record) statistics."""

    def test_pr_list_empty(self, initialized_db: str) -> None:
        """Test listing PRs when none exist."""
        result = runner.invoke(app, ["--db-path", initialized_db, "stats", "pr"])

        assert result.exit_code == 0
        # Should show no PRs or empty list

    def test_pr_for_exercise_not_found(self, initialized_db: str) -> None:
        """Test PRs for non-existent exercise."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "stats", "pr", "--exercise", "99999"]
        )

        # Should handle gracefully
        assert result.exit_code != 0 or "not found" in result.stdout.lower()


@pytest.mark.cli
class TestStatsMuscle:
    """Test muscle volume statistics."""

    @pytest.mark.skip(reason="Muscle stats CLI command not yet fully implemented")
    def test_muscle_volume_empty(self, initialized_db: str) -> None:
        """Test muscle volume with no data."""
        result = runner.invoke(app, ["--db-path", initialized_db, "stats", "muscle"])

        assert result.exit_code == 0
        # Should handle empty case

    @pytest.mark.skip(reason="Muscle stats CLI command not yet fully implemented")
    def test_muscle_volume_with_weeks(self, initialized_db: str) -> None:
        """Test muscle volume with weeks parameter."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "stats", "muscle", "--weeks", "4"]
        )

        assert result.exit_code == 0


@pytest.mark.cli
class TestStatsStreak:
    """Test consistency streak statistics."""

    def test_streak_empty(self, initialized_db: str) -> None:
        """Test streak with no workouts."""
        result = runner.invoke(app, ["--db-path", initialized_db, "stats", "streak"])

        assert result.exit_code == 0
        assert "No active streak" in result.stdout or "0" in result.stdout

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_streak_with_data(self, initialized_db: str) -> None:
        """Test streak with workout data."""
        # TODO: Rewrite to use only CLI commands for data setup


@pytest.mark.cli
class TestStatsProgress:
    """Test progress statistics."""

    def test_progress_no_exercise(self, initialized_db: str) -> None:
        """Test progress for non-existent exercise."""
        result = runner.invoke(app, ["--db-path", initialized_db, "stats", "progress", "99999"])

        assert result.exit_code != 0 or "not found" in result.stdout.lower()

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_progress_with_limit(self, initialized_db: str) -> None:
        """Test progress with limit parameter."""
        # TODO: Rewrite to use only CLI commands for data setup
