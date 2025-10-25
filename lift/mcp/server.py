"""MCP Server implementation for LIFT."""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool

from lift.mcp.config import load_config
from lift.mcp.resources import get_all_resource_handlers
from lift.mcp.tools import get_all_tool_handlers


logger = logging.getLogger(__name__)


class MCPServer:
    """LIFT MCP Server implementation."""

    def __init__(self) -> None:
        """Initialize the MCP server."""
        self.config = load_config()
        self.server = Server("lift-mcp-server")
        self.resource_handlers = get_all_resource_handlers()
        self.tool_handlers = get_all_tool_handlers()

        # Register handlers
        self._register_resource_handlers()
        self._register_tool_handlers()

        logger.info("MCP Server initialized")

    def _register_resource_handlers(self) -> None:
        """Register all resource handlers with the server."""

        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List all available resources."""
            resources = []

            for handler in self.resource_handlers:
                try:
                    handler_resources = handler.list_resources()
                    resources.extend(handler_resources)
                except Exception as e:
                    logger.error(f"Error listing resources from {handler.__class__.__name__}: {e}")

            return resources

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a specific resource by URI."""
            for handler in self.resource_handlers:
                if handler.can_handle(uri):
                    try:
                        resource_data = handler.get_resource(uri)
                        # Convert to string representation
                        import json

                        return json.dumps(resource_data, indent=2, default=str)
                    except Exception as e:
                        logger.error(f"Error reading resource {uri}: {e}")
                        raise

            raise ValueError(f"No handler found for resource URI: {uri}")

    def _register_tool_handlers(self) -> None:
        """Register all tool handlers with the server."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            tools = []

            for handler in self.tool_handlers:
                try:
                    tool = Tool(
                        name=handler.get_name(),
                        description=handler.get_description(),
                        inputSchema=handler.get_input_schema(),
                    )
                    tools.append(tool)
                except Exception as e:
                    logger.error(f"Error registering tool {handler.__class__.__name__}: {e}")

            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[Any]:
            """Execute a tool by name."""
            for handler in self.tool_handlers:
                if handler.get_name() == name:
                    try:
                        result = handler.execute(arguments)
                        import json

                        # Return as a list with a single text content item
                        return [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, default=str),
                            }
                        ]
                    except Exception as e:
                        logger.error(f"Error executing tool {name}: {e}")
                        return [{"type": "text", "text": f"Error executing tool: {e!s}"}]

            return [{"type": "text", "text": f"Tool not found: {name}"}]

    async def run_stdio(self) -> None:
        """Run the server using stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


async def start_server() -> None:
    """Start the MCP server."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    server = MCPServer()
    await server.run_stdio()


def main() -> None:
    """Main entry point for the MCP server."""
    asyncio.run(start_server())


if __name__ == "__main__":
    main()
