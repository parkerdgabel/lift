"""Configuration management for MCP server."""

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server configuration settings."""

    name: str = "lift-mcp-server"
    version: str = "0.4.0"
    transport: str = "stdio"  # stdio or sse


class DatabaseConfig(BaseModel):
    """Database configuration settings."""

    path: str = "~/.lift/lift.duckdb"


class FeaturesConfig(BaseModel):
    """Feature flags configuration."""

    enable_workout_logging: bool = True
    enable_program_management: bool = True
    enable_body_tracking: bool = True
    readonly_mode: bool = False


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = True
    max_requests_per_minute: int = 60


class MCPServerConfig(BaseModel):
    """Complete MCP server configuration."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)


def get_config_path() -> Path:
    """Get the path to the MCP server configuration file."""
    config_dir = Path.home() / ".lift"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "mcp-server.json"


def load_config() -> MCPServerConfig:
    """
    Load MCP server configuration from file or create default.

    Returns:
        MCPServerConfig instance
    """
    config_path = get_config_path()

    if config_path.exists():
        with open(config_path) as f:
            config_data = json.load(f)
            return MCPServerConfig(**config_data)

    # Create default config
    config = MCPServerConfig()
    save_config(config)
    return config


def save_config(config: MCPServerConfig) -> None:
    """
    Save MCP server configuration to file.

    Args:
        config: Configuration to save
    """
    config_path = get_config_path()

    with open(config_path, "w") as f:
        json.dump(config.model_dump(), f, indent=2, default=str)


def get_database_path() -> str:
    """
    Get the database path from config or environment.

    Returns:
        Database path string
    """
    # Check environment variable first
    if db_path := os.getenv("LIFT_DB_PATH"):
        return str(Path(db_path).expanduser())

    # Load from config
    config = load_config()
    return str(Path(config.database.path).expanduser())
