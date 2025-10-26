"""CLI commands for data management (import/export/backup)."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lift.core.database import get_db
from lift.services.export_service import ExportService
from lift.services.import_service import ImportService


# Create data management app
data_app = typer.Typer(name="data", help="Data management commands")
console = Console()


@data_app.command()
def export(
    ctx: typer.Context,
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Export format (csv or json)",
    ),
    table: str | None = typer.Option(
        None,
        "--table",
        "-t",
        help="Specific table to export (omit for all tables)",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file or directory path",
    ),
) -> None:
    """Export data from the database.

    Export all data or specific tables in CSV or JSON format.
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

    export_service = ExportService(db)

    # Validate format
    if format.lower() not in ["csv", "json"]:
        console.print(
            Panel(
                "[red]Invalid format. Must be 'csv' or 'json'.[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    try:
        with console.status("[bold green]Exporting data..."):
            if format.lower() == "csv":
                if table:
                    # Export single table to CSV
                    if not output:
                        output = f"{table}.csv"
                    export_service.export_to_csv(table, output)
                    count = db.get_table_count(table)

                    console.print(
                        Panel(
                            f"[green]Successfully exported {count} rows from {table}[/green]\n"
                            f"[dim]Output: {output}[/dim]",
                            title="Export Complete",
                            border_style="green",
                        )
                    )
                else:
                    # Export all tables to CSV directory
                    if not output:
                        output = "./lift_export_csv"
                    summary = export_service.export_all_to_csv(output)

                    # Display summary
                    table_display = Table(title="Export Summary")
                    table_display.add_column("Table", style="cyan")
                    table_display.add_column("Rows", style="green", justify="right")

                    total_rows = 0
                    for table_name, count in sorted(summary.items()):
                        table_display.add_row(table_name, str(count))
                        total_rows += count

                    console.print(table_display)
                    console.print(
                        f"\n[green]Total: {total_rows} records exported to {output}[/green]"
                    )

            elif table:
                # Export single table to JSON
                if not output:
                    output = f"{table}.json"
                export_service.export_to_json(table, output)
                count = db.get_table_count(table)

                console.print(
                    Panel(
                        f"[green]Successfully exported {count} rows from {table}[/green]\n"
                        f"[dim]Output: {output}[/dim]",
                        title="Export Complete",
                        border_style="green",
                    )
                )
            else:
                # Export all tables to single JSON file
                if not output:
                    output = "lift_export.json"
                summary = export_service.export_all_to_json(output)

                # Display summary
                table_display = Table(title="Export Summary")
                table_display.add_column("Table", style="cyan")
                table_display.add_column("Rows", style="green", justify="right")

                total_rows = 0
                for table_name, count in sorted(summary.items()):
                    table_display.add_row(table_name, str(count))
                    total_rows += count

                console.print(table_display)
                console.print(f"\n[green]Total: {total_rows} records exported to {output}[/green]")

    except Exception as e:
        console.print(
            Panel(
                f"[red]Export failed: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@data_app.command()
def import_data(
    ctx: typer.Context,
    file: str = typer.Argument(..., help="File to import"),
    table: str | None = typer.Option(
        None,
        "--table",
        "-t",
        help="Target table name (required for CSV, auto-detected for JSON)",
    ),
) -> None:
    """Import data from a file.

    Supports CSV and JSON formats. Format is auto-detected from file extension.
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

    file_path = Path(file).expanduser()

    if not file_path.exists():
        console.print(
            Panel(
                f"[red]File not found: {file}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    import_service = ImportService(db)

    # Detect format from extension
    extension = file_path.suffix.lower()

    try:
        with console.status("[bold green]Importing data..."):
            if extension == ".csv":
                if not table:
                    console.print(
                        Panel(
                            "[red]Table name required for CSV import. Use --table option.[/red]",
                            title="Error",
                            border_style="red",
                        )
                    )
                    raise typer.Exit(1)

                count = import_service.import_from_csv(table, str(file_path))

                console.print(
                    Panel(
                        f"[green]Successfully imported {count} rows into {table}[/green]\n"
                        f"[dim]Source: {file}[/dim]",
                        title="Import Complete",
                        border_style="green",
                    )
                )

            elif extension == ".json":
                # Check if this is a single table or full database export
                # For exercises, use specialized handler
                if table == "exercises" or "exercise" in file_path.stem.lower():
                    count = import_service.import_exercises_from_json(str(file_path))
                    console.print(
                        Panel(
                            f"[green]Successfully imported {count} exercises[/green]\n"
                            f"[dim]Source: {file}[/dim]",
                            title="Import Complete",
                            border_style="green",
                        )
                    )
                else:
                    summary = import_service.import_from_json(str(file_path))

                    # Display summary
                    table_display = Table(title="Import Summary")
                    table_display.add_column("Table", style="cyan")
                    table_display.add_column("Rows", style="green", justify="right")

                    total_rows = 0
                    for table_name, count in sorted(summary.items()):
                        table_display.add_row(table_name, str(count))
                        total_rows += count

                    console.print(table_display)
                    console.print(f"\n[green]Total: {total_rows} records imported[/green]")

            else:
                console.print(
                    Panel(
                        f"[red]Unsupported file format: {extension}[/red]\n"
                        "[yellow]Supported formats: .csv, .json[/yellow]",
                        title="Error",
                        border_style="red",
                    )
                )
                raise typer.Exit(1)

    except Exception as e:
        console.print(
            Panel(
                f"[red]Import failed: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@data_app.command()
def backup(
    ctx: typer.Context,
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Backup directory path",
    ),
) -> None:
    """Create a database backup.

    Creates a backup of the database in Parquet format using DuckDB's EXPORT DATABASE.
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

    # Generate default backup path with timestamp
    if not output:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output = f"~/.lift/backups/lift_backup_{timestamp}"

    try:
        with console.status("[bold green]Creating backup..."):
            db.backup(output)

        backup_path = Path(output).expanduser()
        size_mb = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file()) / (
            1024 * 1024
        )

        console.print(
            Panel(
                f"[green]Backup created successfully![/green]\n"
                f"[dim]Location: {backup_path}[/dim]\n"
                f"[dim]Size: {size_mb:.2f} MB[/dim]",
                title="Backup Complete",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(
            Panel(
                f"[red]Backup failed: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@data_app.command()
def restore(
    ctx: typer.Context,
    file: str = typer.Argument(..., help="Backup directory to restore from"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Restore database from a backup.

    WARNING: This will overwrite the current database!
    """
    db_path = ctx.obj.get("db_path")
    db = get_db(db_path)

    backup_path = Path(file).expanduser()

    if not backup_path.exists():
        console.print(
            Panel(
                f"[red]Backup directory not found: {file}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Confirm before overwriting
    if not force:
        console.print(
            Panel(
                "[yellow]WARNING: This will overwrite your current database![/yellow]\n"
                "[yellow]All current data will be lost.[/yellow]",
                title="Confirm Restore",
                border_style="yellow",
            )
        )
        confirm = typer.confirm("Are you sure you want to continue?")
        if not confirm:
            console.print("[yellow]Restore cancelled.[/yellow]")
            raise typer.Exit(0)

    try:
        with console.status("[bold green]Restoring from backup..."):
            db.restore(str(backup_path))

        console.print(
            Panel(
                f"[green]Database restored successfully![/green]\n[dim]Source: {backup_path}[/dim]",
                title="Restore Complete",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(
            Panel(
                f"[red]Restore failed: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@data_app.command()
def optimize(ctx: typer.Context) -> None:
    """Optimize the database file size.

    Runs VACUUM to reclaim unused space and optimize the database.
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

    try:
        # Get size before
        size_before = db.db_path.stat().st_size / (1024 * 1024)

        with console.status("[bold green]Optimizing database..."):
            db.vacuum()

        # Get size after
        size_after = db.db_path.stat().st_size / (1024 * 1024)
        saved = size_before - size_after

        console.print(
            Panel(
                f"[green]Database optimized successfully![/green]\n"
                f"[dim]Size before: {size_before:.2f} MB[/dim]\n"
                f"[dim]Size after: {size_after:.2f} MB[/dim]\n"
                f"[dim]Space saved: {saved:.2f} MB[/dim]",
                title="Optimization Complete",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(
            Panel(
                f"[red]Optimization failed: {e}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)
