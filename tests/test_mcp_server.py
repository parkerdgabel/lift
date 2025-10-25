"""Tests for MCP server implementation."""

import pytest

from lift.mcp.config import MCPServerConfig
from lift.mcp.server import MCPServer


@pytest.fixture()
def temp_db_path(tmp_path, monkeypatch):
    """Create a temporary database path."""
    db_path = tmp_path / "test.duckdb"

    # Mock config to use temp database
    config = MCPServerConfig()
    config.database.path = str(db_path)

    monkeypatch.setattr("lift.mcp.server.load_config", lambda: config)
    monkeypatch.setattr("lift.mcp.resources.get_database_path", lambda: str(db_path))
    monkeypatch.setattr("lift.mcp.tools.get_database_path", lambda: str(db_path))

    return db_path


class TestMCPServer:
    """Test MCP server initialization and setup."""

    def test_server_initialization(self, temp_db_path):
        """Test that server initializes correctly."""
        server = MCPServer()

        assert server.server is not None
        assert server.config is not None
        assert server.resource_handlers is not None
        assert server.tool_handlers is not None

    def test_server_has_resource_handlers(self, temp_db_path):
        """Test that server has resource handlers."""
        server = MCPServer()

        assert len(server.resource_handlers) > 0
        # Should have workout, exercise, and stats handlers
        assert len(server.resource_handlers) == 3

    def test_server_has_tool_handlers(self, temp_db_path):
        """Test that server has tool handlers."""
        server = MCPServer()

        assert len(server.tool_handlers) > 0
        # Should have search, info, start workout, and log bodyweight tools
        assert len(server.tool_handlers) == 4

    def test_server_name(self, temp_db_path):
        """Test server has correct name."""
        server = MCPServer()

        # Server should be named
        assert hasattr(server.server, "name")

    def test_config_loading(self, temp_db_path):
        """Test that config is loaded on initialization."""
        server = MCPServer()

        assert server.config.server.name is not None
        assert server.config.database.path is not None

    def test_resource_handlers_initialized(self, temp_db_path):
        """Test that resource handlers are properly initialized."""
        server = MCPServer()

        for handler in server.resource_handlers:
            # Each handler should have required methods
            assert hasattr(handler, "can_handle")
            assert hasattr(handler, "get_resource")
            assert hasattr(handler, "list_resources")
            assert callable(handler.can_handle)
            assert callable(handler.get_resource)
            assert callable(handler.list_resources)

    def test_tool_handlers_initialized(self, temp_db_path):
        """Test that tool handlers are properly initialized."""
        server = MCPServer()

        for handler in server.tool_handlers:
            # Each handler should have required methods
            assert hasattr(handler, "get_name")
            assert hasattr(handler, "get_description")
            assert hasattr(handler, "get_input_schema")
            assert hasattr(handler, "execute")
            assert callable(handler.get_name)
            assert callable(handler.get_description)
            assert callable(handler.get_input_schema)
            assert callable(handler.execute)

    def test_tool_names_are_unique(self, temp_db_path):
        """Test that all tool handlers have unique names."""
        server = MCPServer()

        names = [handler.get_name() for handler in server.tool_handlers]
        assert len(names) == len(set(names)), "Tool names should be unique"

    def test_resource_handlers_have_database(self, temp_db_path):
        """Test that resource handlers have database access."""
        server = MCPServer()

        for handler in server.resource_handlers:
            assert hasattr(handler, "db")
            assert handler.db is not None

    def test_tool_handlers_have_database(self, temp_db_path):
        """Test that tool handlers have database access."""
        server = MCPServer()

        for handler in server.tool_handlers:
            assert hasattr(handler, "db")
            assert handler.db is not None
