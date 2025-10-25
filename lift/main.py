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
