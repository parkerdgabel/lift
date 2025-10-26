"""Tests for MCP configuration management."""

import json

import pytest

from lift.mcp.config import (
    DatabaseConfig,
    FeaturesConfig,
    MCPServerConfig,
    RateLimitConfig,
    ServerConfig,
    get_database_path,
    load_config,
    save_config,
)


@pytest.fixture
def temp_config_file(tmp_path, monkeypatch):
    """Create a temporary config file location."""
    config_dir = tmp_path / ".lift"
    config_dir.mkdir()
    config_path = config_dir / "mcp-server.json"

    # Patch the config path function
    monkeypatch.setattr("lift.mcp.config.get_config_path", lambda: config_path)

    return config_path


class TestServerConfig:
    """Test server configuration model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ServerConfig()
        assert config.name == "lift-mcp-server"
        assert config.version == "0.2.2"
        assert config.transport == "stdio"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ServerConfig(name="custom-server", version="1.0.0", transport="sse")
        assert config.name == "custom-server"
        assert config.version == "1.0.0"
        assert config.transport == "sse"


class TestDatabaseConfig:
    """Test database configuration model."""

    def test_default_path(self):
        """Test default database path."""
        config = DatabaseConfig()
        assert config.path == "~/.lift/lift.duckdb"

    def test_custom_path(self):
        """Test custom database path."""
        config = DatabaseConfig(path="/custom/path/db.duckdb")
        assert config.path == "/custom/path/db.duckdb"


class TestFeaturesConfig:
    """Test features configuration model."""

    def test_default_features(self):
        """Test default feature flags."""
        config = FeaturesConfig()
        assert config.enable_workout_logging is True
        assert config.enable_program_management is True
        assert config.enable_body_tracking is True
        assert config.readonly_mode is False

    def test_custom_features(self):
        """Test custom feature flags."""
        config = FeaturesConfig(
            enable_workout_logging=False,
            enable_program_management=False,
            enable_body_tracking=False,
            readonly_mode=True,
        )
        assert config.enable_workout_logging is False
        assert config.enable_program_management is False
        assert config.enable_body_tracking is False
        assert config.readonly_mode is True


class TestRateLimitConfig:
    """Test rate limiting configuration model."""

    def test_default_rate_limit(self):
        """Test default rate limit settings."""
        config = RateLimitConfig()
        assert config.enabled is True
        assert config.max_requests_per_minute == 60

    def test_custom_rate_limit(self):
        """Test custom rate limit settings."""
        config = RateLimitConfig(enabled=False, max_requests_per_minute=100)
        assert config.enabled is False
        assert config.max_requests_per_minute == 100


class TestMCPServerConfig:
    """Test complete MCP server configuration."""

    def test_default_config(self):
        """Test default MCP server configuration."""
        config = MCPServerConfig()
        assert config.server.name == "lift-mcp-server"
        assert config.database.path == "~/.lift/lift.duckdb"
        assert config.features.enable_workout_logging is True
        assert config.rate_limiting.enabled is True

    def test_custom_config(self):
        """Test custom MCP server configuration."""
        config = MCPServerConfig(
            server=ServerConfig(name="custom"),
            database=DatabaseConfig(path="/custom/db.duckdb"),
            features=FeaturesConfig(readonly_mode=True),
            rate_limiting=RateLimitConfig(enabled=False),
        )
        assert config.server.name == "custom"
        assert config.database.path == "/custom/db.duckdb"
        assert config.features.readonly_mode is True
        assert config.rate_limiting.enabled is False


class TestConfigPersistence:
    """Test configuration loading and saving."""

    def test_save_config(self, temp_config_file):
        """Test saving configuration to file."""
        config = MCPServerConfig(
            server=ServerConfig(name="test-server"),
            database=DatabaseConfig(path="/test/db.duckdb"),
        )

        save_config(config)

        assert temp_config_file.exists()

        # Verify JSON contents
        with open(temp_config_file) as f:
            data = json.load(f)

        assert data["server"]["name"] == "test-server"
        assert data["database"]["path"] == "/test/db.duckdb"

    def test_load_existing_config(self, temp_config_file):
        """Test loading existing configuration from file."""
        # Create config file
        config_data = {
            "server": {"name": "loaded-server", "version": "2.0.0", "transport": "sse"},
            "database": {"path": "/loaded/db.duckdb"},
            "features": {
                "enable_workout_logging": False,
                "enable_program_management": True,
                "enable_body_tracking": True,
                "readonly_mode": True,
            },
            "rate_limiting": {"enabled": False, "max_requests_per_minute": 120},
        }

        with open(temp_config_file, "w") as f:
            json.dump(config_data, f)

        # Load config
        config = load_config()

        assert config.server.name == "loaded-server"
        assert config.server.version == "2.0.0"
        assert config.server.transport == "sse"
        assert config.database.path == "/loaded/db.duckdb"
        assert config.features.enable_workout_logging is False
        assert config.features.readonly_mode is True
        assert config.rate_limiting.enabled is False
        assert config.rate_limiting.max_requests_per_minute == 120

    def test_load_creates_default_config(self, temp_config_file):
        """Test loading creates default config if file doesn't exist."""
        assert not temp_config_file.exists()

        config = load_config()

        # File should be created
        assert temp_config_file.exists()

        # Should have default values
        assert config.server.name == "lift-mcp-server"
        assert config.database.path == "~/.lift/lift.duckdb"


class TestGetDatabasePath:
    """Test database path resolution."""

    def test_get_database_path_from_config(self, temp_config_file):
        """Test getting database path from config file."""
        config = MCPServerConfig(database=DatabaseConfig(path="~/.lift/custom.duckdb"))
        save_config(config)

        db_path = get_database_path()
        assert "custom.duckdb" in db_path

    def test_get_database_path_from_env(self, temp_config_file, monkeypatch):
        """Test getting database path from environment variable."""
        monkeypatch.setenv("LIFT_DB_PATH", "~/env/db.duckdb")

        db_path = get_database_path()
        # Environment variable should take precedence
        # Use Path for cross-platform compatibility
        from pathlib import Path

        assert Path("env/db.duckdb").as_posix() in Path(db_path).as_posix()

    def test_expanduser_in_database_path(self, temp_config_file):
        """Test that tilde is expanded in database path."""
        config = MCPServerConfig(database=DatabaseConfig(path="~/test/db.duckdb"))
        save_config(config)

        db_path = get_database_path()
        # Should not contain tilde
        assert "~" not in db_path
        # Use Path for cross-platform compatibility
        from pathlib import Path

        assert Path("test/db.duckdb").as_posix() in Path(db_path).as_posix()
