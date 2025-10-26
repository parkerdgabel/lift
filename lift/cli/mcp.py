"""CLI commands for MCP server management."""

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lift.mcp.config import get_config_path, load_config
from lift.mcp.server import start_server


mcp_app = typer.Typer(name="mcp", help="MCP server management commands")
console = Console()


@mcp_app.command()
def start(
    transport: str = typer.Option(
        "stdio", "--transport", "-t", help="Transport type (stdio or sse)"
    ),
) -> None:
    """Start the MCP server.

    The MCP server allows AI assistants like Claude to interact with LIFT
    for workout tracking, exercise search, and performance analysis.

    Example:
        lift mcp start

    """
    console.print(
        Panel(
            "[bold cyan]Starting LIFT MCP Server[/bold cyan]\n\n"
            f"Transport: {transport}\n"
            "Server ready to accept connections...",
            border_style="cyan",
        )
    )

    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        console.print("\n[yellow]MCP server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting MCP server: {e}[/red]")
        raise typer.Exit(1)


@mcp_app.command()
def config() -> None:
    """Generate MCP server configuration for Claude Desktop.

    Outputs configuration JSON that can be added to Claude Desktop's
    config file to enable LIFT integration.

    Example:
        lift mcp config >> ~/Library/Application Support/Claude/claude_desktop_config.json

    """
    # Get the lift command path
    lift_cmd = str(Path(sys.executable).parent / "lift")

    config_json = {
        "mcpServers": {
            "lift": {
                "command": lift_cmd,
                "args": ["mcp", "start"],
                "description": "LIFT workout tracker - access workout data, log exercises, and analyze performance",
            }
        }
    }

    # Print just the JSON
    print(json.dumps(config_json, indent=2))


@mcp_app.command()
def info() -> None:
    """Show current MCP server configuration.

    Displays the configuration file location and current settings.
    """
    config_path = get_config_path()
    config = load_config()

    console.print(
        Panel(
            f"[bold]MCP Server Configuration[/bold]\n\n"
            f"Config file: {config_path}\n\n"
            f"Server Name: {config.server.name}\n"
            f"Version: {config.server.version}\n"
            f"Transport: {config.server.transport}\n\n"
            f"Database Path: {config.database.path}\n\n"
            f"Features:\n"
            f"  - Workout Logging: {'✓' if config.features.enable_workout_logging else '✗'}\n"
            f"  - Program Management: {'✓' if config.features.enable_program_management else '✗'}\n"
            f"  - Body Tracking: {'✓' if config.features.enable_body_tracking else '✗'}\n"
            f"  - Read-Only Mode: {'✓' if config.features.readonly_mode else '✗'}\n\n"
            f"Rate Limiting: {'✓' if config.rate_limiting.enabled else '✗'} "
            f"({config.rate_limiting.max_requests_per_minute} requests/min)",
            border_style="cyan",
            title="LIFT MCP Server",
        )
    )


@mcp_app.command()
def capabilities() -> None:
    """List all available MCP capabilities (resources, tools, prompts).

    Shows what resources, tools, and prompts are available to AI assistants
    when they connect to the LIFT MCP server.
    """
    # Resources
    resources_table = Table(title="Resources", show_header=True, header_style="bold cyan")
    resources_table.add_column("URI Pattern", style="green")
    resources_table.add_column("Description")

    resources_table.add_row("lift://workouts/recent", "Last 10 completed workouts")
    resources_table.add_row("lift://workouts/{id}", "Specific workout details")
    resources_table.add_row("lift://exercises/library", "Complete exercise library")
    resources_table.add_row("lift://stats/summary?period=week", "Weekly training summary")
    resources_table.add_row("lift://stats/summary?period=month", "Monthly training summary")

    console.print(resources_table)
    console.print()

    # Tools
    tools_table = Table(title="Tools", show_header=True, header_style="bold cyan")
    tools_table.add_column("Tool Name", style="green")
    tools_table.add_column("Description")

    tools_table.add_row("search_exercises", "Search exercises by name, muscle, or equipment")
    tools_table.add_row("get_exercise_info", "Get detailed exercise information")
    tools_table.add_row("start_workout", "Start a new workout session")
    tools_table.add_row("log_bodyweight", "Log bodyweight measurement")

    console.print(tools_table)
    console.print()

    console.print(
        Panel(
            "[dim]More capabilities coming soon:\n"
            "- Log workout sets\n"
            "- Analyze progression\n"
            "- Get personal records\n"
            "- Volume analysis\n"
            "- Program management[/dim]",
            title="Roadmap",
            border_style="yellow",
        )
    )


@mcp_app.command()
def setup() -> None:
    """Interactive setup wizard for MCP server integration with Claude Desktop.

    Guides you through the process of configuring Claude Desktop to use
    the LIFT MCP server.
    """

    console.print(
        Panel(
            "[bold cyan]LIFT MCP Server Setup[/bold cyan]\n\n"
            "This wizard will help you configure Claude Desktop to use LIFT.",
            border_style="cyan",
        )
    )

    # Step 1: Check if Claude Desktop config exists
    claude_config_path = Path(
        "~/Library/Application Support/Claude/claude_desktop_config.json"
    ).expanduser()

    console.print("\n[bold]Step 1:[/bold] Locating Claude Desktop configuration...")

    if claude_config_path.exists():
        console.print(f"[green]✓[/green] Found config: {claude_config_path}")
    else:
        console.print(
            f"[yellow]⚠[/yellow] Config not found at: {claude_config_path}\n"
            "[dim]You may need to create this file manually.[/dim]"
        )

    # Step 2: Generate config
    console.print("\n[bold]Step 2:[/bold] Generate configuration...")

    lift_cmd = str(Path(sys.executable).parent / "lift")

    config_snippet = {
        "mcpServers": {
            "lift": {
                "command": lift_cmd,
                "args": ["mcp", "start"],
            }
        }
    }

    console.print("\n[bold]Add this to your Claude Desktop configuration:[/bold]\n")
    console.print(Panel(json.dumps(config_snippet, indent=2), border_style="green"))

    # Step 3: Instructions
    console.print(
        "\n[bold]Step 3:[/bold] Complete setup\n\n"
        "1. Copy the configuration above\n"
        f"2. Open/create: {claude_config_path}\n"
        "3. Add the configuration to the file\n"
        "4. Restart Claude Desktop\n"
        "5. Look for the MCP server icon in Claude Desktop\n\n"
        "[dim]For more information, see: docs/MCP_SERVER.md[/dim]"
    )
