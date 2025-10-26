"""LIFT - Main CLI entry point."""

import typer
from rich.console import Console
from rich.panel import Panel

from lift.core.database import get_db


# Create main app
app = typer.Typer(
    name="lift",
    help="🏋️ A robust bodybuilding workout tracker CLI",
    no_args_is_help=True,
    add_completion=True,
)

console = Console()


# Global options
@app.callback()
def main(
    ctx: typer.Context,
    db_path: str | None = typer.Option(
        None,
        "--db-path",
        "-d",
        help="Path to database file",
        envvar="LIFT_DB_PATH",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """Global options for all commands."""
    ctx.obj = {"db_path": db_path, "verbose": verbose}


@app.command()
def init(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", "-f", help="Force reinitialization"),
) -> None:
    """
    Initialize the LIFT database.

    Creates the database schema and loads seed data.
    """
    db_path = ctx.obj.get("db_path")
    db = get_db(db_path)

    if db.database_exists() and not force:
        console.print(
            Panel(
                "[yellow]Database already exists. Use --force to reinitialize.[/yellow]",
                title="⚠️  Warning",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    try:
        with console.status("[bold green]Initializing database..."):
            db.initialize_database()

        console.print(
            Panel(
                f"[green]Database initialized successfully![/green]\n"
                f"[dim]Location: {db.db_path}[/dim]",
                title="✅ Success",
                border_style="green",
            )
        )

        # Load seed exercises
        from lift.services.exercise_service import ExerciseService

        with console.status("[bold green]Loading exercise library..."):
            exercise_service = ExerciseService(db)
            loaded_count = exercise_service.load_seed_exercises(force=force)

        if loaded_count > 0:
            console.print(f"\n[green]✓[/green] Loaded {loaded_count} exercises into the library")

        # Show database info
        info = db.get_database_info()
        console.print("\n[bold]Database Tables:[/bold]")
        for table, count in info["tables"].items():
            console.print(f"  • {table}: {count} rows")

    except Exception as e:
        console.print(
            Panel(
                f"[red]Failed to initialize database: {e}[/red]",
                title="❌ Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@app.command()
def info(ctx: typer.Context) -> None:
    """Show database information and statistics."""
    db_path = ctx.obj.get("db_path")
    db = get_db(db_path)

    if not db.database_exists():
        console.print(
            Panel(
                "[yellow]Database not initialized. Run 'lift init' first.[/yellow]",
                title="⚠️  Warning",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    info = db.get_database_info()

    console.print(
        Panel(
            f"[bold]Database Path:[/bold] {info['database_path']}\n"
            f"[bold]Size:[/bold] {info['database_size_mb']:.2f} MB",
            title="📊 Database Information",
            border_style="blue",
        )
    )

    console.print("\n[bold]Tables:[/bold]")
    for table, count in sorted(info["tables"].items()):
        console.print(f"  • {table}: [cyan]{count}[/cyan] rows")


@app.command()
def version() -> None:
    """Show LIFT version."""
    from lift import __version__

    console.print(f"[bold]LIFT[/bold] version [cyan]{__version__}[/cyan]")


@app.command()
def install_manpage(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Install the LIFT man page to system location.

    This copies the bundled man page to the appropriate system directory.
    May require sudo/administrator privileges.
    """
    import os
    import platform
    import shutil
    from pathlib import Path

    # Find the bundled man page
    import lift

    lift_dir = Path(lift.__file__).parent
    source_manpage = lift_dir / "man" / "lift.1"

    if not source_manpage.exists():
        console.print(
            Panel(
                "[red]Man page not found in package installation.[/red]\n"
                "[dim]The man page may only be available when installed from source.[/dim]",
                title="❌ Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Determine system man page directory
    system = platform.system()
    if system == "Darwin":  # macOS
        man_dirs = [
            Path("/usr/local/share/man/man1"),
            Path.home() / ".local/share/man/man1",
        ]
    elif system == "Linux":
        man_dirs = [
            Path("/usr/local/share/man/man1"),
            Path("/usr/share/man/man1"),
            Path.home() / ".local/share/man/man1",
        ]
    else:  # Windows or other
        console.print(
            Panel(
                "[yellow]Man pages are not supported on this operating system.[/yellow]",
                title="⚠️  Warning",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    # Try to find a writable directory
    target_dir = None
    for man_dir in man_dirs:
        if (man_dir.exists() and os.access(man_dir, os.W_OK)) or (
            not man_dir.exists() and os.access(man_dir.parent, os.W_OK)
        ):
            target_dir = man_dir
            break

    if not target_dir:
        # Suggest using user's local man directory
        target_dir = Path.home() / ".local/share/man/man1"
        console.print(
            Panel(
                f"[yellow]No writable system man directory found.[/yellow]\n"
                f"Will install to user directory: [cyan]{target_dir}[/cyan]\n\n"
                f"[dim]To install system-wide, run with sudo:[/dim]\n"
                f"[dim]sudo lift install-manpage[/dim]",
                title="ℹ️  Info",
                border_style="blue",
            )
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    target_manpage = target_dir / "lift.1"

    # Check if already exists
    if target_manpage.exists() and not force:
        console.print(
            Panel(
                f"[yellow]Man page already installed at:[/yellow]\n"
                f"[cyan]{target_manpage}[/cyan]\n\n"
                f"Use --force to overwrite.",
                title="⚠️  Warning",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    # Copy the man page
    try:
        shutil.copy2(source_manpage, target_manpage)
        console.print(
            Panel(
                f"[green]Man page installed successfully![/green]\n"
                f"[dim]Location: {target_manpage}[/dim]\n\n"
                f"You can now use: [cyan]man lift[/cyan]",
                title="✅ Success",
                border_style="green",
            )
        )

        # Update man database if possible
        if shutil.which("mandb"):
            console.print("\n[dim]Updating man database...[/dim]")
            os.system("mandb -q 2>/dev/null || true")

    except Exception as e:
        console.print(
            Panel(
                f"[red]Failed to install man page: {e}[/red]\n\n"
                f"Try running with sudo:\n"
                f"[cyan]sudo lift install-manpage[/cyan]",
                title="❌ Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


# Command groups
# Import and register command groups
from lift.cli.body import body_app
from lift.cli.config import config_app
from lift.cli.data import data_app
from lift.cli.exercise import exercise_app
from lift.cli.mcp import mcp_app
from lift.cli.program import program_app
from lift.cli.stats import stats_app
from lift.cli.workout import workout_app


app.add_typer(body_app, name="body")
app.add_typer(data_app, name="data")
app.add_typer(config_app, name="config")
app.add_typer(exercise_app, name="exercises")
app.add_typer(mcp_app, name="mcp")
app.add_typer(program_app, name="program")
app.add_typer(stats_app, name="stats")
app.add_typer(workout_app, name="workout")


def main_entry() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main_entry()
