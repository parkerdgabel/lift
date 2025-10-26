# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LIFT is a bodybuilding workout tracker CLI built with Python 3.11+. It uses DuckDB for high-performance analytical queries, Typer for CLI framework, Rich for terminal UI, Pydantic for data validation, and Plotext for terminal charts.

## Development Commands

### Setup
```bash
# Install with dev dependencies
pip install -e ".[dev,mcp]"

# Install pre-commit hooks (required before committing)
pre-commit install
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_exercise_service.py

# Run specific test
pytest tests/test_exercise_service.py::test_create_exercise

# Run tests in parallel
pytest -n auto

# Run without coverage (faster)
pytest --no-cov
```

### Code Quality
```bash
# Type checking (must pass - 100% type coverage required)
mypy lift

# Linting
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .

# Security scanning
bandit -r lift -ll
```

### Running the CLI
```bash
# Use development install
lift --help

# Initialize database (creates ~/.lift/lift.duckdb)
lift init

# Use custom database location for development
export LIFT_DB_PATH=~/.lift/lift-dev.duckdb
lift init
```

## Architecture

### Layer Structure

```
lift/
├── cli/           # CLI commands (Typer apps, one per command group)
├── services/      # Business logic layer (database operations)
├── core/          # Database, models, schema
├── utils/         # Calculations, formatters, charts
├── mcp/           # Model Context Protocol server
└── data/          # Seed data (exercises.json, programs.json)
```

**Critical Pattern:** Services are the ONLY layer that talks to the database. CLI commands call services, never touch the database directly.

### Service Layer Pattern

All services follow this pattern:
- Accept a `DatabaseManager` instance in `__init__`
- Use `with self.db.get_connection() as conn:` for database operations
- Return Pydantic models, not raw database tuples
- Handle business logic validation (database constraints are secondary)

Example:
```python
class ExerciseService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def get_by_id(self, id: int) -> Exercise | None:
        with self.db.get_connection() as conn:
            result = conn.execute(query, (id,)).fetchone()
            return self._row_to_exercise(result) if result else None
```

### CLI Pattern

CLI commands follow this pattern:
- Use Typer for argument/option parsing
- Get `DatabaseManager` via `get_db(ctx.obj.get("db_path"))`
- Instantiate service(s)
- Call service methods
- Format output with Rich (console.print, Panel, Table, etc.)
- Use formatters from `lift/utils/` for complex displays

### Database Connection

Database path resolution (in order of precedence):
1. `--db-path` CLI flag
2. `LIFT_DB_PATH` environment variable
3. Default: `~/.lift/lift.duckdb`

The `get_db()` function uses a singleton pattern - only one DatabaseManager instance exists per process.

### Models and Validation

All data uses Pydantic models defined in `lift/core/models.py`:
- Base models: `Exercise`, `Workout`, `Set`, etc.
- Create models: `ExerciseCreate`, `WorkoutCreate`, etc. (for user input)
- Update models: `ExerciseUpdate`, `WorkoutUpdate`, etc. (all fields optional)

**Important:** Pydantic v2 requires explicit field values. When constructing models, always pass all fields explicitly, using `None` for optional fields you want to skip:
```python
# Correct
WorkoutUpdate(
    name="New Name",
    duration_minutes=60,
    completed=None,  # Explicit None
    bodyweight=None,
    notes=None,
)

# Wrong - will error
WorkoutUpdate(name="New Name", duration_minutes=60)
```

### Seed Data

Two critical JSON files:
- `lift/data/exercises.json` - 137 pre-loaded exercises
- `lift/data/programs.json` - Sample training programs

**Critical:** Exercise names in `programs.json` MUST exactly match names in `exercises.json`. The `program_service.load_seed_programs()` function looks up exercises by name. Mismatches cause exercises to be silently skipped during loading.

When adding/modifying programs, always verify exercise names exist in `exercises.json` first.

### Database Schema

Key tables:
- `exercises` - Exercise library (137 seed + custom)
- `workouts` - Workout sessions
- `sets` - Individual set logs
- `programs` - Training program definitions
- `program_workouts` - Workout templates within programs
- `program_exercises` - Exercise prescriptions (sets, reps, RPE targets)
- `personal_records` - PR tracking (auto-detected)
- `body_measurements` - Bodyweight and circumference tracking

Analytical views (for efficient queries):
- `workout_volume` - Volume calculations per workout
- `weekly_muscle_volume` - Volume by muscle group per week
- `exercise_progression` - Exercise history with 1RM estimates
- `bodyweight_trend` - Weekly bodyweight averages

Full schema: `lift/core/schema.sql`

### MCP Server

The MCP (Model Context Protocol) server enables Claude Desktop integration:
- Located in `lift/mcp/`
- Provides tools and resources for AI-powered workout tracking
- Setup via `lift mcp setup` command
- Server starts via `lift mcp start`

## Code Quality Standards

### Type Checking
- **100% type coverage required** - all functions must have type hints
- Strict mypy mode (`disallow_untyped_defs = true`)
- Use `tuple[Type, ...]` not `Tuple[Type, ...]` (Python 3.11+)
- Database result tuples often need None checks before indexing:
  ```python
  result = conn.execute(query).fetchone()
  if not result:
      raise ValueError("Not found")
  return result[0]  # Safe after None check
  ```

### Ruff Linting
- Version: 0.14.2 (pinned in CI and pre-commit)
- Line length: 100
- Many rules enabled (see pyproject.toml)
- Tests have relaxed rules (no ARG, PLR2004, PT001 checks)

### Testing
- Use pytest fixtures from `tests/conftest.py` (especially `db` fixture)
- Each test gets isolated in-memory DuckDB
- Tests must not depend on execution order
- Prefer parametrized tests for multiple scenarios
- Mock external dependencies (no real file I/O unless testing that specifically)

### Commit Messages
Follow conventional commit format:
```
<type>(<scope>): <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Git Workflow

This project uses Git Flow:
- `main` - Production releases only (tagged)
- `develop` - Integration branch
- `feature/*` - New features (branch from develop, PR to develop)
- `bugfix/*` - Bug fixes (branch from develop, PR to develop)
- `hotfix/*` - Emergency fixes (branch from main, merge to both main and develop)

**Never commit directly to main or develop.** Always use PRs.

CI runs on pushes/PRs to both main and develop. All checks must pass before merge.

## Common Gotchas

1. **Exercise name mismatches**: When loading programs, exercise names must exactly match between programs.json and exercises.json (case-sensitive, plural forms matter)

2. **Pydantic v2 explicit fields**: Always pass all fields to Pydantic models, using `None` for omitted optional fields

3. **Database singleton**: The `get_db()` function returns a singleton - don't create multiple DatabaseManager instances in the same process

4. **Context manager pattern**: Always use `with self.db.get_connection() as conn:` for database operations, never store connections as instance variables

5. **Type checking tuple results**: DuckDB `.fetchone()` returns `tuple | None` - always check for None before indexing

6. **Pre-commit hooks**: Version mismatch between local ruff and CI ruff will cause failures - keep .pre-commit-config.yaml in sync with CI workflow

7. **Test isolation**: Don't modify global state in tests - use fixtures that reset state between tests
