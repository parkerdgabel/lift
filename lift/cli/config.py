"""CLI commands for configuration management."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lift.core.database import get_db
from lift.services.config_service import ConfigService

# Create configuration app
config_app = typer.Typer(name="config", help="Configuration management")
console = Console()


@config_app.command()
def set(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
    """
    Set a configuration value.

    Set or update a configuration setting.
    """
    db_path = ctx.obj.get("db_path")
    db = get_db(db_path)

    if not db.database_exists():
        console.print(
            Panel(
                "[yellow]Database not initialized. Run 'lift init' first.[/yellow]",
                title="Warning",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    config_service = ConfigService(db)

    try:
        setting = config_service.set_setting(key, value)

        console.print(
            Panel(
                f"[green]Configuration updated[/green]\n"
                f"[cyan]{key}[/cyan] = [yellow]{value}[/yellow]",
                title="Success",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(
            Panel(
                f"[red]Failed to set configuration: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@config_app.command()
def get(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Configuration key"),
) -> None:
    """
    Get a configuration value.

    Retrieve the value of a specific configuration setting.
    """
    db_path = ctx.obj.get("db_path")
    db = get_db(db_path)

    if not db.database_exists():
        console.print(
            Panel(
                "[yellow]Database not initialized. Run 'lift init' first.[/yellow]",
                title="Warning",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    config_service = ConfigService(db)

    try:
        value = config_service.get_setting(key)

        if value is None:
            console.print(
                Panel(
                    f"[yellow]Configuration key '{key}' not found[/yellow]",
                    title="Not Found",
                    border_style="yellow",
                )
            )
            raise typer.Exit(1)

        console.print(f"[cyan]{key}[/cyan] = [yellow]{value}[/yellow]")

    except Exception as e:
        console.print(
            Panel(
                f"[red]Failed to get configuration: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@config_app.command()
def list(ctx: typer.Context) -> None:
    """
    List all configuration settings.

    Display all configuration settings in a formatted table.
    """
    db_path = ctx.obj.get("db_path")
    db = get_db(db_path)

    if not db.database_exists():
        console.print(
            Panel(
                "[yellow]Database not initialized. Run 'lift init' first.[/yellow]",
                title="Warning",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    config_service = ConfigService(db)

    try:
        settings = config_service.get_all_settings_detailed()

        # Create table
        table = Table(title="CONFIGURATION", show_header=True, header_style="bold cyan")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow")
        table.add_column("Description", style="dim")

        for setting in settings:
            # Truncate long values
            value = setting.value
            if len(value) > 50:
                value = value[:47] + "..."

            description = setting.description or ""
            if len(description) > 60:
                description = description[:57] + "..."

            table.add_row(setting.key, value, description)

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        console.print(
            Panel(
                f"[red]Failed to list configuration: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@config_app.command()
def reset(
    ctx: typer.Context,
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """
    Reset all configuration to default values.

    WARNING: This will delete all custom configuration settings!
    """
    db_path = ctx.obj.get("db_path")
    db = get_db(db_path)

    if not db.database_exists():
        console.print(
            Panel(
                "[yellow]Database not initialized. Run 'lift init' first.[/yellow]",
                title="Warning",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    # Confirm before resetting
    if not force:
        console.print(
            Panel(
                "[yellow]WARNING: This will reset all configuration to default values![/yellow]\n"
                "[yellow]All custom settings will be lost.[/yellow]",
                title="Confirm Reset",
                border_style="yellow",
            )
        )
        confirm = typer.confirm("Are you sure you want to continue?")
        if not confirm:
            console.print("[yellow]Reset cancelled.[/yellow]")
            raise typer.Exit(0)

    config_service = ConfigService(db)

    try:
        with console.status("[bold green]Resetting configuration..."):
            config_service.reset_to_defaults()

        console.print(
            Panel(
                "[green]Configuration reset to defaults successfully![/green]",
                title="Reset Complete",
                border_style="green",
            )
        )

        # Show current settings
        settings = config_service.get_all_settings()
        console.print("\n[bold]Default Settings:[/bold]")
        for key, value in sorted(settings.items()):
            console.print(f"  [cyan]{key}[/cyan] = [yellow]{value}[/yellow]")

    except Exception as e:
        console.print(
            Panel(
                f"[red]Reset failed: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@config_app.command()
def delete(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Configuration key to delete"),
) -> None:
    """
    Delete a configuration setting.

    Remove a custom configuration setting (will fall back to default if available).
    """
    db_path = ctx.obj.get("db_path")
    db = get_db(db_path)

    if not db.database_exists():
        console.print(
            Panel(
                "[yellow]Database not initialized. Run 'lift init' first.[/yellow]",
                title="Warning",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    config_service = ConfigService(db)

    try:
        deleted = config_service.delete_setting(key)

        if deleted:
            console.print(
                Panel(
                    f"[green]Configuration key '{key}' deleted successfully[/green]",
                    title="Success",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[yellow]Configuration key '{key}' not found[/yellow]",
                    title="Not Found",
                    border_style="yellow",
                )
            )

    except Exception as e:
        console.print(
            Panel(
                f"[red]Failed to delete configuration: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)
