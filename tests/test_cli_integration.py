"""
CLI integration tests.

Tests CLI commands end-to-end using Typer's testing utilities.
"""

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


class TestCLIInitialization:
    """Test CLI initialization commands."""

    def test_init_command(self, temp_db: str) -> None:
        """Test database initialization via CLI."""
        result = runner.invoke(app, ["--db-path", temp_db, "init"])

        assert result.exit_code == 0
        assert "Database initialized successfully" in result.stdout
        assert Path(temp_db).exists()

    def test_init_force_flag(self, temp_db: str) -> None:
        """Test force reinitialization."""
        # Initialize first time
        runner.invoke(app, ["--db-path", temp_db, "init"])

        # Try to reinit without force (should fail)
        result = runner.invoke(app, ["--db-path", temp_db, "init"])
        assert result.exit_code == 1
        assert "already exists" in result.stdout

        # Reinit with force (should succeed)
        result = runner.invoke(app, ["--db-path", temp_db, "init", "--force"])
        assert result.exit_code == 0

    def test_info_command(self, temp_db: str) -> None:
        """Test database info command."""
        # Initialize database
        runner.invoke(app, ["--db-path", temp_db, "init"])

        # Get info
        result = runner.invoke(app, ["--db-path", temp_db, "info"])

        assert result.exit_code == 0
        assert "Database Information" in result.stdout
        assert "exercises" in result.stdout
        assert "137 rows" in result.stdout  # Seed exercises

    def test_version_command(self) -> None:
        """Test version command."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "LIFT" in result.stdout
        assert "version" in result.stdout


class TestCLIExerciseCommands:
    """Test exercise-related CLI commands."""

    def test_exercises_list(self, temp_db: str) -> None:
        """Test listing exercises."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "exercises", "list"])

        assert result.exit_code == 0
        assert "Barbell Bench Press" in result.stdout

    def test_exercises_search(self, temp_db: str) -> None:
        """Test searching exercises."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "exercises", "search", "bench"])

        assert result.exit_code == 0
        assert "Bench Press" in result.stdout

    def test_exercises_filter_by_category(self, temp_db: str) -> None:
        """Test filtering exercises by category."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(
            app, ["--db-path", temp_db, "exercises", "list", "--category", "Push"]
        )

        assert result.exit_code == 0
        # Should show push exercises
        assert "Bench Press" in result.stdout or "Push" in result.stdout

    def test_exercises_info(self, temp_db: str) -> None:
        """Test getting exercise info."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(
            app, ["--db-path", temp_db, "exercises", "info", "Barbell Bench Press"]
        )

        assert result.exit_code == 0
        assert "Barbell Bench Press" in result.stdout
        assert "Chest" in result.stdout

    def test_exercises_stats(self, temp_db: str) -> None:
        """Test exercise library statistics."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "exercises", "stats"])

        assert result.exit_code == 0
        assert "Exercise Library Statistics" in result.stdout


class TestCLIProgramCommands:
    """Test program-related CLI commands."""

    def test_program_import_samples(self, temp_db: str) -> None:
        """Test importing sample programs."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "program", "import-samples"])

        assert result.exit_code == 0
        assert "Successfully loaded" in result.stdout

    def test_program_list(self, temp_db: str) -> None:
        """Test listing programs."""
        runner.invoke(app, ["--db-path", temp_db, "init"])
        runner.invoke(app, ["--db-path", temp_db, "program", "import-samples"])

        result = runner.invoke(app, ["--db-path", temp_db, "program", "list"])

        assert result.exit_code == 0
        assert "PPL" in result.stdout or "Programs" in result.stdout

    def test_program_show(self, temp_db: str) -> None:
        """Test showing program details."""
        runner.invoke(app, ["--db-path", temp_db, "init"])
        runner.invoke(app, ["--db-path", temp_db, "program", "import-samples"])

        result = runner.invoke(app, ["--db-path", temp_db, "program", "show", "PPL 6-Day"])

        assert result.exit_code == 0
        assert "PPL 6-DAY" in result.stdout


class TestCLIBodyCommands:
    """Test body tracking CLI commands."""

    def test_body_weight_log(self, temp_db: str) -> None:
        """Test logging bodyweight."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "body", "weight", "185"])

        assert result.exit_code == 0
        assert "185" in result.stdout
        assert "Weight logged" in result.stdout

    def test_body_latest(self, temp_db: str) -> None:
        """Test showing latest measurement."""
        runner.invoke(app, ["--db-path", temp_db, "init"])
        runner.invoke(app, ["--db-path", temp_db, "body", "weight", "180"])

        result = runner.invoke(app, ["--db-path", temp_db, "body", "latest"])

        assert result.exit_code == 0
        assert "180" in result.stdout


class TestCLIConfigCommands:
    """Test configuration CLI commands."""

    def test_config_list(self, temp_db: str) -> None:
        """Test listing configuration."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "config", "list"])

        assert result.exit_code == 0
        assert "CONFIGURATION" in result.stdout
        assert "default_weight_unit" in result.stdout

    def test_config_get(self, temp_db: str) -> None:
        """Test getting a config value."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "config", "get", "default_weight_unit"])

        assert result.exit_code == 0
        assert "lbs" in result.stdout

    def test_config_set(self, temp_db: str) -> None:
        """Test setting a config value."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(
            app, ["--db-path", temp_db, "config", "set", "default_weight_unit", "kg"]
        )

        assert result.exit_code == 0
        assert "Configuration updated" in result.stdout

        # Verify the change
        result = runner.invoke(app, ["--db-path", temp_db, "config", "get", "default_weight_unit"])
        assert "kg" in result.stdout


class TestCLIDataCommands:
    """Test data management CLI commands."""

    def test_data_export_json(self, temp_db: str, tmp_path: Path) -> None:
        """Test exporting data to JSON."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        export_path = tmp_path / "export.json"

        result = runner.invoke(
            app,
            [
                "--db-path",
                temp_db,
                "data",
                "export",
                "--format",
                "json",
                "--output",
                str(export_path),
            ],
        )

        assert result.exit_code == 0
        assert export_path.exists()
        assert export_path.stat().st_size > 0

    def test_data_backup(self, temp_db: str, tmp_path: Path) -> None:
        """Test database backup."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        backup_path = tmp_path / "backup"

        result = runner.invoke(
            app,
            ["--db-path", temp_db, "data", "backup", "--output", str(backup_path)],
        )

        assert result.exit_code == 0
        assert backup_path.exists()

    def test_data_optimize(self, temp_db: str) -> None:
        """Test database optimization."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "data", "optimize"])

        assert result.exit_code == 0
        assert "optimized" in result.stdout.lower()


class TestCLIWorkoutCommands:
    """Test workout CLI commands."""

    def test_workout_history_empty(self, temp_db: str) -> None:
        """Test workout history when empty."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "workout", "history"])

        assert result.exit_code == 0
        # Should show empty or no workouts message

    def test_workout_last_empty(self, temp_db: str) -> None:
        """Test last workout when no workouts exist."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "workout", "last"])

        # Should handle gracefully (might be exit code 0 or 1 depending on implementation)
        assert "No workouts" in result.stdout or result.exit_code != 0


class TestCLIStatsCommands:
    """Test statistics CLI commands."""

    def test_stats_summary_empty(self, temp_db: str) -> None:
        """Test stats summary with no data."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "stats", "summary"])

        assert result.exit_code == 0
        # Should show 0 workouts or similar

    def test_stats_streak_empty(self, temp_db: str) -> None:
        """Test training streak with no data."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "stats", "streak"])

        assert result.exit_code == 0


class TestCLIGlobalOptions:
    """Test global CLI options."""

    def test_db_path_option(self, temp_db: str) -> None:
        """Test custom database path via --db-path option."""
        result = runner.invoke(app, ["--db-path", temp_db, "init"])

        assert result.exit_code == 0
        assert Path(temp_db).exists()

    def test_help_option(self) -> None:
        """Test --help option."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "LIFT" in result.stdout or "bodybuilding" in result.stdout

    def test_subcommand_help(self) -> None:
        """Test help for subcommands."""
        result = runner.invoke(app, ["exercises", "--help"])

        assert result.exit_code == 0
        assert "exercises" in result.stdout.lower()


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_command_without_init(self, temp_db: str) -> None:
        """Test commands fail gracefully without initialization."""
        result = runner.invoke(app, ["--db-path", temp_db, "exercises", "list"])

        # Should fail or show appropriate error
        assert "not initialized" in result.stdout.lower() or result.exit_code != 0

    def test_invalid_exercise_name(self, temp_db: str) -> None:
        """Test handling of invalid exercise name."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(
            app, ["--db-path", temp_db, "exercises", "info", "NonexistentExercise"]
        )

        # Should handle gracefully
        assert result.exit_code != 0 or "not found" in result.stdout.lower()

    def test_invalid_program_name(self, temp_db: str) -> None:
        """Test handling of invalid program name."""
        runner.invoke(app, ["--db-path", temp_db, "init"])

        result = runner.invoke(app, ["--db-path", temp_db, "program", "show", "NonexistentProgram"])

        # Should handle gracefully
        assert result.exit_code != 0 or "not found" in result.stdout.lower()
