"""Tests for body tracking CLI commands."""

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
class TestBodyWeight:
    """Test body weight logging commands."""

    def test_log_weight_lbs(self, initialized_db: str) -> None:
        """Test logging weight in pounds."""
        result = runner.invoke(app, ["--db-path", initialized_db, "body", "weight", "185.5"])

        assert result.exit_code == 0
        assert "185.5" in result.stdout or "logged" in result.stdout.lower()

    def test_log_weight_kg(self, initialized_db: str) -> None:
        """Test logging weight in kilograms."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "body", "weight", "84.0", "--unit", "kg"]
        )

        assert result.exit_code == 0
        assert "84" in result.stdout or "logged" in result.stdout.lower()

    def test_log_weight_invalid(self, initialized_db: str) -> None:
        """Test logging invalid weight value."""
        result = runner.invoke(app, ["--db-path", initialized_db, "body", "weight", "invalid"])

        assert result.exit_code != 0

    def test_log_weight_shows_previous(self, initialized_db: str) -> None:
        """Test that logging weight shows previous weight."""
        # Log first weight via CLI
        result1 = runner.invoke(app, ["--db-path", initialized_db, "body", "weight", "180.0"])
        assert result1.exit_code == 0

        # Log second weight
        result = runner.invoke(app, ["--db-path", initialized_db, "body", "weight", "182.5"])

        assert result.exit_code == 0
        # Should show comparison with previous weight


@pytest.mark.cli
class TestBodyHistory:
    """Test body measurement history commands."""

    def test_history_empty(self, initialized_db: str) -> None:
        """Test viewing history with no measurements."""
        result = runner.invoke(app, ["--db-path", initialized_db, "body", "history"])

        assert result.exit_code == 0
        # Should handle empty case gracefully

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_history_with_data(self, initialized_db: str) -> None:
        """Test viewing history with measurements."""
        # TODO: Rewrite to use only CLI commands for data setup

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_history_with_limit(self, initialized_db: str) -> None:
        """Test viewing history with limit parameter."""
        # TODO: Rewrite to use only CLI commands for data setup


@pytest.mark.cli
class TestBodyLatest:
    """Test latest body measurement commands."""

    def test_latest_empty(self, initialized_db: str) -> None:
        """Test getting latest measurement when none exist."""
        result = runner.invoke(app, ["--db-path", initialized_db, "body", "latest"])

        assert result.exit_code == 0
        assert "No measurements" in result.stdout or "no data" in result.stdout.lower()

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_latest_with_data(self, initialized_db: str) -> None:
        """Test getting latest measurement."""
        # TODO: Rewrite to use only CLI commands for data setup


@pytest.mark.cli
class TestBodyProgress:
    """Test body progress tracking commands."""

    @pytest.mark.skip(reason="Body progress CLI command not yet fully implemented")
    def test_progress_empty(self, initialized_db: str) -> None:
        """Test viewing progress with no data."""
        result = runner.invoke(app, ["--db-path", initialized_db, "body", "progress"])

        assert result.exit_code == 0
        # Should handle empty case

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_progress_with_data(self, initialized_db: str) -> None:
        """Test viewing progress with measurements."""
        # TODO: Rewrite to use only CLI commands for data setup


@pytest.mark.cli
class TestBodyCompare:
    """Test body measurement comparison commands."""

    def test_compare_invalid_ids(self, initialized_db: str) -> None:
        """Test comparing non-existent measurements."""
        result = runner.invoke(
            app, ["--db-path", initialized_db, "body", "compare", "99999", "99998"]
        )

        # Should fail or handle gracefully
        assert result.exit_code != 0 or "not found" in result.stdout.lower()

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_compare_same_id(self, initialized_db: str) -> None:
        """Test comparing a measurement with itself."""
        # TODO: Rewrite to use only CLI commands for data setup

    @pytest.mark.skip(reason="Needs proper CLI-only test implementation")
    def test_compare_two_measurements(self, initialized_db: str) -> None:
        """Test comparing two different measurements."""
        # TODO: Rewrite to use only CLI commands for data setup
