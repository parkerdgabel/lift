"""Base handlers for MCP resources and tools."""

import logging
from typing import Any

from lift.core.database import DatabaseManager
from lift.mcp.config import get_database_path


logger = logging.getLogger(__name__)


class BaseHandler:
    """Base class for MCP handlers."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """
        Initialize handler with database connection.

        Args:
            db: Database manager instance. If None, creates new instance.
        """
        if db is None:
            db_path = get_database_path()
            self.db = DatabaseManager(db_path)
        else:
            self.db = db

    def handle_error(self, error: Exception, context: str = "") -> dict[str, Any]:
        """
        Handle errors and format error response.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred

        Returns:
            Error response dictionary
        """
        error_msg = str(error)
        if context:
            error_msg = f"{context}: {error_msg}"

        logger.error(f"Error in MCP handler: {error_msg}", exc_info=True)

        return {
            "error": {
                "message": error_msg,
                "type": type(error).__name__,
            }
        }


class ResourceHandler(BaseHandler):
    """Base class for resource handlers."""

    def can_handle(self, uri: str) -> bool:
        """
        Check if this handler can process the given URI.

        Args:
            uri: Resource URI

        Returns:
            True if handler can process this URI
        """
        raise NotImplementedError

    def get_resource(self, uri: str) -> dict[str, Any]:
        """
        Get resource data for the given URI.

        Args:
            uri: Resource URI

        Returns:
            Resource data dictionary
        """
        raise NotImplementedError

    def list_resources(self) -> list[dict[str, Any]]:
        """
        List all available resources of this type.

        Returns:
            List of resource metadata
        """
        raise NotImplementedError


class ToolHandler(BaseHandler):
    """Base class for tool handlers."""

    def get_name(self) -> str:
        """
        Get the tool name.

        Returns:
            Tool name string
        """
        raise NotImplementedError

    def get_description(self) -> str:
        """
        Get the tool description.

        Returns:
            Tool description string
        """
        raise NotImplementedError

    def get_input_schema(self) -> dict[str, Any]:
        """
        Get the tool input schema.

        Returns:
            JSON Schema for tool inputs
        """
        raise NotImplementedError

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the tool with given arguments.

        Args:
            arguments: Tool input arguments

        Returns:
            Tool execution result
        """
        raise NotImplementedError


def format_success_response(data: Any, message: str | None = None) -> dict[str, Any]:
    """
    Format a successful response.

    Args:
        data: Response data
        message: Optional success message

    Returns:
        Formatted response dictionary
    """
    response: dict[str, Any] = {"success": True, "data": data}

    if message:
        response["message"] = message

    return response


def format_error_response(error: str, error_type: str = "Error") -> dict[str, Any]:
    """
    Format an error response.

    Args:
        error: Error message
        error_type: Type of error

    Returns:
        Formatted error response
    """
    return {"success": False, "error": {"message": error, "type": error_type}}
