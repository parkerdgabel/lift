# Lift Architecture

This document describes the overall architecture and design patterns used in Lift.

## Overview

Lift is a command-line application built with a **layered architecture** to separate concerns and maintain clean, testable code.

```
┌─────────────────────────────────────────────────────┐
│                   CLI Layer                          │
│              (User Interface)                        │
│   workout.py, exercise.py, body.py, etc.             │
└──────────────────┬──────────────────────────────────┘
                   │ Commands & Arguments
                   ↓
┌─────────────────────────────────────────────────────┐
│                 Service Layer                        │
│              (Business Logic)                        │
│ WorkoutService, ExerciseService, StatsService, etc.  │
└──────────────────┬──────────────────────────────────┘
                   │ CRUD Operations
                   ↓
┌─────────────────────────────────────────────────────┐
│                  Core Layer                          │
│         (Data Models & Database)                     │
│      DatabaseManager, Models (Pydantic)              │
└──────────────────┬──────────────────────────────────┘
                   │ SQL Queries
                   ↓
┌─────────────────────────────────────────────────────┐
│                   DuckDB                             │
│           (Embedded Database)                        │
└─────────────────────────────────────────────────────┘
```

Additionally:
- **Utils Layer**: Cross-cutting formatters, calculators, converters
- **MCP Layer**: Model Context Protocol server integration
- **Data Layer**: Static JSON files for exercises and programs

## Directory Structure

```
lift/
├── cli/           # Command-line interface (Typer commands)
├── core/          # Data models and database management
├── services/      # Business logic and operations
├── utils/         # Formatters, calculations, utilities
├── mcp/           # Model Context Protocol server
├── data/          # Static data files (exercises, programs)
├── man/           # Man page documentation
└── main.py        # Application entry point
```

## Layer Responsibilities

### CLI Layer (`lift/cli/`)

**Purpose:** Handle user interaction through the command line.

**Technologies:**
- **Typer**: Type-safe CLI framework
- **Rich**: Terminal formatting and styling

**Files:**
- `workout.py`: Workout tracking commands
- `exercise.py`: Exercise management commands
- `body.py`: Body measurement commands
- `stats.py`: Statistics and analytics commands
- `program.py`: Training program commands
- `config.py`: Configuration management
- `data.py`: Data import/export commands
- `mcp.py`: MCP server commands

**Responsibilities:**
- Parse command-line arguments
- Validate user input
- Call appropriate service methods
- Format and display output
- Handle errors gracefully

**Design Pattern:** **Command Pattern**
- Each command is a function with Typer decorators
- Commands delegate business logic to services
- CLI functions are thin wrappers around service calls

**Example:**
```python
@workout_app.command("start")
def start_workout(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Workout name"),
) -> None:
    """Start a new workout session."""
    service = get_workout_service(ctx)
    workout = service.create_workout(name=name)
    console.print(f"[green]Started workout: {workout.name}[/green]")
```

### Service Layer (`lift/services/`)

**Purpose:** Encapsulate business logic and database operations.

**Files:**
- `workout_service.py`: Workout session logic
- `set_service.py`: Set tracking logic
- `exercise_service.py`: Exercise CRUD operations
- `body_service.py`: Body measurement tracking
- `stats_service.py`: Analytics and statistics
- `pr_service.py`: Personal record detection
- `program_service.py`: Training program management
- `config_service.py`: User settings management
- `import_service.py`: Data import operations
- `export_service.py`: Data export operations

**Responsibilities:**
- Implement business rules
- Coordinate database operations
- Perform calculations
- Validate data before persistence
- Detect and create personal records
- Generate analytical insights

**Design Pattern:** **Service Layer Pattern**
- Each service has a single responsibility
- Services can call other services
- All database access goes through services
- Services return Pydantic models

**Example:**
```python
class WorkoutService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_workout(
        self,
        name: str,
        program_workout_id: int | None = None,
    ) -> Workout:
        """Create a new workout session."""
        # Validation
        if not name:
            raise ValueError("Workout name required")

        # Database operation
        with self.db.get_connection() as conn:
            result = conn.execute(
                """
                INSERT INTO workouts (name, program_workout_id)
                VALUES (?, ?)
                RETURNING *
                """,
                (name, program_workout_id),
            ).fetchone()

        # Return Pydantic model
        return Workout.model_validate(dict(result))
```

### Core Layer (`lift/core/`)

**Purpose:** Define data structures and manage database access.

**Files:**
- `models.py`: Pydantic data models
- `database.py`: Database connection management
- `schema.sql`: Database schema definition

**Responsibilities:**
- Define data schemas with Pydantic
- Manage database connections
- Execute SQL queries
- Ensure data consistency
- Handle migrations (schema changes)

**Design Pattern:** **Repository Pattern** (implicit)
- DatabaseManager provides connection interface
- Services use raw SQL for flexibility
- Pydantic models ensure type safety

**Database Manager:**
```python
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path).expanduser()

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get database connection (context manager)."""
        return duckdb.connect(str(self.db_path))

    def initialize_database(self) -> None:
        """Create tables and load initial data."""
        # Execute schema.sql
        # Load exercises.json
        # Load programs.json
```

**Data Models:**
```python
class Exercise(BaseModel):
    id: int
    name: str
    category: CategoryType
    primary_muscle: MuscleGroup
    equipment: EquipmentType
    # ... other fields

    model_config = {"from_attributes": True}
```

### Utils Layer (`lift/utils/`)

**Purpose:** Provide cross-cutting utilities and formatters.

**Files:**
- `workout_formatters.py`: Workout display formatting
- `exercise_formatters.py`: Exercise display formatting
- `body_formatters.py`: Body measurement formatting
- `program_formatters.py`: Program display formatting
- `calculations.py`: Fitness calculations (1RM, volume, etc.)
- `conversions.py`: Unit conversions (lbs/kg, in/cm)
- `charts.py`: Terminal charts (using plotext)

**Responsibilities:**
- Format data for terminal display
- Create tables and panels (Rich library)
- Generate charts
- Perform calculations (1RM estimation, volume, etc.)
- Convert units

**Design Pattern:** **Utility/Helper Pattern**
- Pure functions when possible
- No state
- Reusable across CLI commands

**Example:**
```python
def calculate_estimated_1rm(weight: Decimal, reps: int) -> Decimal:
    """Calculate estimated 1RM using Epley formula."""
    if reps == 1:
        return weight
    return weight * (1 + Decimal(reps) / Decimal(30))

def format_workout_summary(workout: Workout, sets: list[Set]) -> Panel:
    """Create Rich Panel with workout summary."""
    # Build table
    # Calculate totals
    # Return formatted panel
```

### MCP Layer (`lift/mcp/`)

**Purpose:** Expose Lift as a Model Context Protocol server for AI integration.

**Files:**
- `server.py`: MCP server implementation
- `tools.py`: Tool definitions for AI
- `resources.py`: Resource providers
- `handlers.py`: Request handlers
- `schemas.py`: JSON schemas for tools
- `config.py`: MCP server configuration

**Responsibilities:**
- Implement MCP protocol
- Expose workout tracking as tools
- Provide resources for AI context
- Handle AI assistant requests

**Design Pattern:** **Adapter Pattern**
- Adapts Lift services to MCP interface
- Translates MCP requests to service calls

**Example:**
```python
@mcp_server.tool()
async def log_set(
    workout_id: int,
    exercise_name: str,
    weight: float,
    reps: int,
    rpe: float | None = None,
) -> str:
    """Log a set for an exercise."""
    # Find exercise
    # Call SetService
    # Return formatted result
```

## Data Flow

### Example: Logging a Workout Set

```
User Input:
lift workout log --quick --exercise-id 1

↓ CLI Layer (workout.py)
- Parse arguments
- Get WorkoutService and SetService
- Prompt for set details (weight, reps, RPE)

↓ Service Layer (set_service.py)
- Validate input (weight > 0, reps > 0, RPE 6-10)
- Create Set model
- Insert into database
- Detect PR (call PRService)
- Return Set model

↓ Core Layer (database.py)
- Execute INSERT query
- Return row data

↑ Service Layer
- Convert row to Set model
- Return to CLI

↑ CLI Layer
- Format output with Rich
- Display to user

Output:
✓ Set logged: 225 lbs × 8 @ RPE 8.0
🏆 New PR: Best volume for Bench Press!
```

## Key Design Decisions

### 1. DuckDB as Database

**Why DuckDB?**
- Embedded (no server setup)
- Blazing fast analytics
- SQL interface for complex queries
- Columnar storage for efficient aggregations
- Built-in analytical functions
- Zero-copy data access

**Alternative Considered:** SQLite
- DuckDB better for analytical workloads
- Better performance on aggregations
- Modern SQL features

### 2. Pydantic for Models

**Why Pydantic?**
- Automatic validation
- Type safety
- JSON serialization
- IDE autocomplete
- Easy migration to/from dict

**Alternative Considered:** Dataclasses
- Pydantic provides validation
- Better for CLI input validation

### 3. Typer for CLI

**Why Typer?**
- Type hints for arguments
- Automatic help generation
- Subcommands built-in
- Rich integration
- Modern Python (3.11+)

**Alternative Considered:** Click
- Typer is built on Click
- Typer has better type hints

### 4. Rich for Display

**Why Rich?**
- Beautiful terminal output
- Tables, panels, trees
- Progress bars
- Markdown rendering
- Emoji support

**Alternative Considered:** Colorama/Termcolor
- Rich much more feature-complete
- Better user experience

### 5. Service Layer Pattern

**Why Services?**
- Separation of concerns
- Testable business logic
- Reusable across CLI and MCP
- Single source of truth

**Alternative Considered:** Active Record
- Service layer better for complex logic
- Easier to test

## Extension Points

### Adding a New Command

1. **Create CLI command** in appropriate module (e.g., `workout.py`)
2. **Add service method** if needed (e.g., `WorkoutService`)
3. **Use existing formatters** or create new ones
4. **Add tests** for service logic

### Adding a New Service

1. **Create service file** (e.g., `services/new_service.py`)
2. **Import DatabaseManager** in `__init__`
3. **Implement methods** using Pydantic models
4. **Add tests** with fixtures

### Adding a New Model

1. **Define in `core/models.py`** using Pydantic
2. **Add to schema.sql** if storing in database
3. **Update migration** if changing existing tables

### Adding MCP Tools

1. **Define tool** in `mcp/tools.py`
2. **Implement handler** using services
3. **Add schema** in `mcp/schemas.py`
4. **Test via MCP client**

## Testing Strategy

See [Testing Documentation](./testing.md) for full details.

**Unit Tests:**
- Service layer logic
- Calculations and conversions
- Model validation

**Integration Tests:**
- CLI commands end-to-end
- Database operations
- Service interactions

**Fixtures:**
- `temp_db`: Temporary database
- `initialized_db`: Database with schema
- Mock services for CLI tests

## Configuration Management

**Global Configuration:**
- Database path: `~/.lift/lift.db`
- Settings stored in database `settings` table
- Accessed via `ConfigService`

**User Preferences:**
- Default units (lbs/kg, in/cm)
- RPE tracking enabled/disabled
- Tempo tracking enabled/disabled
- Auto-PR detection

**Access Pattern:**
```python
from lift.core.database import get_db
from lift.services.config_service import ConfigService

config = ConfigService(get_db())
default_unit = config.get_setting("default_weight_unit")
```

## Error Handling

**CLI Layer:**
- Catch all exceptions
- Display user-friendly messages
- Use Typer.Exit() for clean exits

**Service Layer:**
- Raise specific exceptions (ValueError, etc.)
- Let CLI layer handle display

**Database Layer:**
- Catch database errors
- Re-raise with context

**Example:**
```python
# Service
def create_workout(self, name: str) -> Workout:
    if not name:
        raise ValueError("Workout name is required")
    # ... database operation

# CLI
try:
    workout = service.create_workout(name)
except ValueError as e:
    console.print(f"[red]Error: {e}[/red]")
    raise typer.Exit(1)
```

## Performance Considerations

1. **Database Indexes**: Key columns indexed for fast lookups
2. **Connection Pooling**: DuckDB handles internally
3. **Batch Operations**: Use transactions for multiple inserts
4. **Lazy Loading**: Only fetch needed data
5. **Caching**: Minimal (database is fast enough)

## Security Considerations

1. **No User Authentication**: Single-user local app
2. **SQL Injection**: Parameterized queries only
3. **File Permissions**: Database file has user-only access
4. **Input Validation**: All inputs validated by Pydantic
5. **MCP Server**: Optional, local network only

## Future Enhancements

Potential architectural improvements:

1. **Plugin System**: Allow third-party extensions
2. **Event System**: Publish/subscribe for PR detection, etc.
3. **Caching Layer**: Redis for frequently accessed data (if needed)
4. **API Server**: REST API for web/mobile apps
5. **Migration System**: Automated schema migrations (Alembic)

## Conclusion

Lift's architecture prioritizes:
- **Simplicity**: Easy to understand and extend
- **Testability**: Separated layers, dependency injection
- **Type Safety**: Pydantic and type hints throughout
- **User Experience**: Rich terminal output, helpful errors
- **Performance**: Fast database, efficient queries

The layered design allows each component to evolve independently while maintaining a clean contract between layers.
