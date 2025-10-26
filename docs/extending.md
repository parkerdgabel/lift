# Extending Lift

This guide shows you how to add new features and customize Lift for your needs.

## Overview

Lift is designed to be extensible. Common extensions include:

- Adding new CLI commands
- Creating new services for business logic
- Adding new data models
- Extending the MCP server with tools
- Creating custom formatters
- Adding new calculations

## Prerequisites

Before extending Lift:

1. **Read the [Architecture Guide](./architecture.md)** to understand the design
2. **Review the [Data Model](./data-model.md)** to understand the schema
3. **Set up development environment**:

```bash
# Clone the repository
git clone https://github.com/parkerdgabel/lift.git
cd lift

# Install in development mode
pip install -e '.[dev]'

# Install pre-commit hooks
pre-commit install
```

## Adding a New CLI Command

### Step 1: Choose the Right Module

CLI commands are organized by domain:

- `cli/workout.py`: Workout tracking
- `cli/exercise.py`: Exercise management
- `cli/body.py`: Body measurements
- `cli/stats.py`: Statistics and analytics
- `cli/program.py`: Training programs
- `cli/config.py`: Configuration
- `cli/data.py`: Import/export

If your command doesn't fit existing modules, create a new one.

### Step 2: Define the Command

```python
# cli/workout.py

import typer
from rich.console import Console

workout_app = typer.Typer()
console = Console()

@workout_app.command("new-command")
def my_new_command(
    ctx: typer.Context,
    arg1: str = typer.Argument(..., help="Required argument"),
    opt1: int = typer.Option(10, "--option", "-o", help="Optional value"),
) -> None:
    """Brief description of what this command does.

    More detailed explanation here.

    Examples:
        lift workout new-command "value"
        lift workout new-command "value" --option 20

    """
    # Get service from context
    service = get_workout_service(ctx)

    try:
        # Call service method
        result = service.my_method(arg1, opt1)

        # Format output
        console.print(f"[green]Success: {result}[/green]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
```

### Step 3: Register the Command

If you created a new module, register it in `main.py`:

```python
# main.py

from lift.cli.mymodule import mymodule_app

app.add_typer(mymodule_app, name="mymodule")
```

### Step 4: Add Tests

```python
# tests/test_cli_mymodule.py

from typer.testing import CliRunner
from lift.main import app

runner = CliRunner()

def test_my_new_command(initialized_db: str) -> None:
    """Test the new command."""
    result = runner.invoke(
        app,
        ["--db-path", initialized_db, "workout", "new-command", "test-arg"],
    )

    assert result.exit_code == 0
    assert "Success" in result.stdout
```

## Adding a New Service

### Step 1: Create Service File

```python
# services/my_service.py

from lift.core.database import DatabaseManager
from lift.core.models import MyModel, MyModelCreate

class MyService:
    """Service for managing my feature.

    Attributes:
        db: Database manager instance

    """

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """Initialize service.

        Args:
            db: Database manager. If None, uses global instance.

        """
        from lift.core.database import get_db

        self.db = db or get_db()

    def create(self, data: MyModelCreate) -> MyModel:
        """Create a new record.

        Args:
            data: Creation data

        Returns:
            Created model instance

        Raises:
            ValueError: If validation fails

        Examples:
            >>> service = MyService()
            >>> model = service.create(MyModelCreate(name="Test"))
            >>> print(model.id)
            1

        """
        # Validation
        if not data.name:
            raise ValueError("Name is required")

        # Database operation
        with self.db.get_connection() as conn:
            result = conn.execute(
                """
                INSERT INTO my_table (name, value)
                VALUES (?, ?)
                RETURNING *
                """,
                (data.name, data.value),
            ).fetchone()

        # Return model
        return MyModel.model_validate(dict(result))

    def get_by_id(self, record_id: int) -> MyModel | None:
        """Get record by ID.

        Args:
            record_id: Record ID

        Returns:
            Model if found, None otherwise

        """
        with self.db.get_connection() as conn:
            result = conn.execute(
                "SELECT * FROM my_table WHERE id = ?",
                (record_id,),
            ).fetchone()

        return MyModel.model_validate(dict(result)) if result else None

    def get_all(self, filter_by: str | None = None) -> list[MyModel]:
        """Get all records with optional filter.

        Args:
            filter_by: Optional filter value

        Returns:
            List of models

        """
        query = "SELECT * FROM my_table"
        params: tuple = ()

        if filter_by:
            query += " WHERE category = ?"
            params = (filter_by,)

        with self.db.get_connection() as conn:
            results = conn.execute(query, params).fetchall()

        return [MyModel.model_validate(dict(row)) for row in results]

    def delete(self, record_id: int) -> bool:
        """Delete a record.

        Args:
            record_id: Record ID

        Returns:
            True if deleted, False if not found

        """
        with self.db.get_connection() as conn:
            result = conn.execute(
                "DELETE FROM my_table WHERE id = ? RETURNING id",
                (record_id,),
            ).fetchone()

        return result is not None
```

### Step 2: Add to __init__.py

```python
# services/__init__.py

from lift.services.my_service import MyService

__all__ = [
    # ... existing
    "MyService",
]
```

### Step 3: Write Tests

```python
# tests/test_my_service.py

import pytest
from lift.services.my_service import MyService
from lift.core.models import MyModelCreate

def test_create_record(initialized_db: str) -> None:
    """Test creating a record."""
    service = MyService()

    data = MyModelCreate(name="Test", value=42)
    record = service.create(data)

    assert record.id > 0
    assert record.name == "Test"
    assert record.value == 42

def test_get_by_id(initialized_db: str) -> None:
    """Test retrieving a record."""
    service = MyService()

    # Create
    data = MyModelCreate(name="Test", value=42)
    created = service.create(data)

    # Retrieve
    retrieved = service.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == created.name
```

## Adding a New Data Model

### Step 1: Define Model in core/models.py

```python
# core/models.py

from pydantic import BaseModel, Field
from datetime import datetime

class MyModelBase(BaseModel):
    """Base model with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    value: int = Field(..., ge=0)
    category: str | None = None

class MyModelCreate(MyModelBase):
    """Model for creation (no ID)."""
    pass

class MyModel(MyModelBase):
    """Full model with ID and metadata."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

### Step 2: Add to Database Schema

```sql
-- core/schema.sql

CREATE SEQUENCE IF NOT EXISTS my_table_id_seq START 1;

CREATE TABLE IF NOT EXISTS my_table (
    id INTEGER PRIMARY KEY DEFAULT nextval('my_table_id_seq'),
    name VARCHAR NOT NULL,
    value INTEGER NOT NULL,
    category VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_my_table_category ON my_table(category);
```

### Step 3: Update Database Initialization

If you need seed data, update `database.py`:

```python
# core/database.py

def initialize_database(self) -> None:
    """Initialize database with schema and data."""
    # ... existing code

    # Load seed data for new table
    self._load_my_data()

def _load_my_data(self) -> None:
    """Load initial data for my_table."""
    with self.get_connection() as conn:
        # Check if data already exists
        count = conn.execute("SELECT COUNT(*) FROM my_table").fetchone()[0]
        if count > 0:
            return

        # Insert seed data
        conn.executemany(
            "INSERT INTO my_table (name, value) VALUES (?, ?)",
            [("Default 1", 10), ("Default 2", 20)],
        )
```

## Adding a Custom Formatter

Formatters transform data into terminal output using Rich.

### Step 1: Create Formatter Function

```python
# utils/my_formatters.py

from rich.table import Table
from rich.panel import Panel
from lift.core.models import MyModel

def create_my_table(items: list[MyModel], title: str = "My Data") -> Table:
    """Create a Rich table for my data.

    Args:
        items: List of models to display
        title: Table title

    Returns:
        Formatted Rich table

    """
    table = Table(title=title, show_header=True, header_style="bold cyan")

    # Define columns
    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Category")

    # Add rows
    for item in items:
        table.add_row(
            str(item.id),
            item.name,
            str(item.value),
            item.category or "-",
        )

    return table

def format_my_detail(item: MyModel) -> Panel:
    """Create detailed panel for single item.

    Args:
        item: Model to display

    Returns:
        Formatted Rich panel

    """
    content = f"""
[bold]ID:[/bold] {item.id}
[bold]Name:[/bold] {item.name}
[bold]Value:[/bold] {item.value}
[bold]Category:[/bold] {item.category or "None"}
[bold]Created:[/bold] {item.created_at.strftime("%Y-%m-%d %H:%M")}
    """.strip()

    return Panel(
        content,
        title=f"[bold]{item.name}[/bold]",
        border_style="cyan",
    )
```

### Step 2: Use in CLI

```python
# cli/mymodule.py

from lift.utils.my_formatters import create_my_table, format_my_detail

@mymodule_app.command("list")
def list_items(ctx: typer.Context) -> None:
    """List all items."""
    service = get_my_service(ctx)
    items = service.get_all()

    if not items:
        console.print("[yellow]No items found[/yellow]")
        return

    table = create_my_table(items)
    console.print(table)

@mymodule_app.command("show")
def show_item(ctx: typer.Context, item_id: int) -> None:
    """Show detailed item information."""
    service = get_my_service(ctx)
    item = service.get_by_id(item_id)

    if not item:
        console.print(f"[red]Item {item_id} not found[/red]")
        raise typer.Exit(1)

    panel = format_my_detail(item)
    console.print(panel)
```

## Adding MCP Tools

Extend the MCP server to expose new functionality to AI assistants.

### Step 1: Define Tool

```python
# mcp/tools.py

from mcp import Tool
from lift.services.my_service import MyService
from lift.core.database import get_db

@mcp_server.tool()
async def my_tool(
    name: str,
    value: int,
    category: str | None = None,
) -> str:
    """Create a new record via MCP.

    Args:
        name: Record name
        value: Record value
        category: Optional category

    Returns:
        Success message with created ID

    """
    service = MyService(get_db())

    try:
        from lift.core.models import MyModelCreate

        data = MyModelCreate(name=name, value=value, category=category)
        record = service.create(data)

        return f"Created record #{record.id}: {record.name}"

    except ValueError as e:
        return f"Error: {e}"
```

### Step 2: Add Schema

```python
# mcp/schemas.py

MY_TOOL_SCHEMA = {
    "name": "my_tool",
    "description": "Create a new record",
    "inputSchema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Record name",
            },
            "value": {
                "type": "integer",
                "description": "Record value",
            },
            "category": {
                "type": "string",
                "description": "Optional category",
            },
        },
        "required": ["name", "value"],
    },
}
```

## Adding Custom Calculations

Create reusable calculation functions in `utils/calculations.py`.

```python
# utils/calculations.py

from decimal import Decimal

def calculate_my_metric(value1: Decimal, value2: Decimal) -> Decimal:
    """Calculate custom metric.

    Args:
        value1: First value
        value2: Second value

    Returns:
        Calculated metric

    Examples:
        >>> calculate_my_metric(Decimal("100"), Decimal("10"))
        Decimal('10.0')

    """
    if value2 == 0:
        return Decimal(0)

    return value1 / value2
```

## Database Migrations

When you need to modify the schema:

### Step 1: Update schema.sql

```sql
-- core/schema.sql

-- Add new column
ALTER TABLE workouts ADD COLUMN new_field VARCHAR;

-- Or create new table
CREATE TABLE IF NOT EXISTS new_table (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL
);
```

### Step 2: Write Migration Function

```python
# core/database.py

def migrate_to_version_2(self) -> None:
    """Migrate database to version 2."""
    with self.get_connection() as conn:
        # Check current version
        version = conn.execute(
            "SELECT value FROM settings WHERE key = 'schema_version'"
        ).fetchone()

        if version and int(version[0]) >= 2:
            return  # Already migrated

        # Apply migration
        conn.execute("ALTER TABLE workouts ADD COLUMN new_field VARCHAR")

        # Update version
        conn.execute(
            "UPDATE settings SET value = '2' WHERE key = 'schema_version'"
        )
```

### Step 3: Call Migration

```python
# core/database.py

def initialize_database(self) -> None:
    """Initialize database with schema and migrations."""
    # ... existing initialization

    # Run migrations
    self.migrate_to_version_2()
```

## Best Practices

### 1. Follow Existing Patterns

- Study existing code before adding new features
- Match the style and structure
- Reuse existing utilities

### 2. Write Tests

- Unit tests for service logic
- Integration tests for CLI commands
- Use fixtures for database setup

### 3. Type Hints

- Use type hints everywhere
- Leverage Pydantic for validation
- Enable mypy checking

### 4. Documentation

- Docstrings for all public functions
- Examples in docstrings
- Update README if adding major features

### 5. Error Handling

- Validate input in services
- Raise specific exceptions
- Handle errors gracefully in CLI

### 6. Performance

- Use database indexes
- Batch operations when possible
- Profile before optimizing

## Testing Your Extension

```bash
# Run specific test
pytest tests/test_my_service.py -v

# Run all tests
pytest -v

# Run with coverage
pytest --cov=lift --cov-report=html

# Type checking
mypy lift/

# Linting
ruff check lift/

# Format code
ruff format lift/
```

## Submitting Your Extension

If you want to contribute your extension:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-extension`
3. **Write tests** for your code
4. **Update documentation**
5. **Run pre-commit**: `pre-commit run --all-files`
6. **Submit a pull request**

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full guidelines.

## Example: Complete Feature Addition

Let's walk through adding a "notes" feature for workouts.

### 1. Add Model

```python
# core/models.py

class WorkoutNote(BaseModel):
    workout_id: int
    note: str
    created_at: datetime
```

### 2. Update Schema

```sql
-- core/schema.sql
-- Note: Workouts table already has notes column
-- This example assumes we want a separate notes table

CREATE TABLE IF NOT EXISTS workout_notes (
    id INTEGER PRIMARY KEY,
    workout_id INTEGER NOT NULL,
    note TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workout_id) REFERENCES workouts(id)
);
```

### 3. Add Service Method

```python
# services/workout_service.py

def add_note(self, workout_id: int, note: str) -> WorkoutNote:
    """Add note to workout."""
    with self.db.get_connection() as conn:
        result = conn.execute(
            """
            INSERT INTO workout_notes (workout_id, note)
            VALUES (?, ?)
            RETURNING *
            """,
            (workout_id, note),
        ).fetchone()

    return WorkoutNote.model_validate(dict(result))
```

### 4. Add CLI Command

```python
# cli/workout.py

@workout_app.command("note")
def add_workout_note(
    ctx: typer.Context,
    workout_id: int = typer.Argument(...),
    note: str = typer.Argument(...),
) -> None:
    """Add a note to a workout.

    Examples:
        lift workout note 42 "Felt great today!"

    """
    service = get_workout_service(ctx)

    try:
        workout_note = service.add_note(workout_id, note)
        console.print(f"[green]✓ Note added to workout {workout_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
```

### 5. Add Tests

```python
# tests/test_workout_service.py

def test_add_note(initialized_db: str) -> None:
    """Test adding note to workout."""
    service = WorkoutService()

    # Create workout
    workout = service.create_workout(name="Test")

    # Add note
    note = service.add_note(workout.id, "Great workout!")

    assert note.workout_id == workout.id
    assert note.note == "Great workout!"
```

Done! You've added a complete feature following Lift's architecture.

## Getting Help

- Read the [Architecture Guide](./architecture.md)
- Check existing code for examples
- Ask questions in GitHub Discussions
- Open an issue if you find a bug

Happy extending! 🚀
