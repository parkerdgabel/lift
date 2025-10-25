"""
LIFT MCP Server.

Model Context Protocol server implementation for LIFT workout tracker.
Exposes workout data, tools, and prompts to AI assistants.
"""

from lift.mcp.server import MCPServer, start_server


__all__ = ["MCPServer", "start_server"]
