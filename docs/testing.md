# Testing Documentation

This guide covers Lift's testing strategy, how to run tests, and how to write new tests.

## Overview

Lift uses **pytest** for all testing with comprehensive coverage across:

- **Unit tests**: Service layer logic, calculations, utilities
- **Integration tests**: CLI commands, service interactions
- **End-to-end tests**: Complete user workflows
- **MCP tests**: Model Context Protocol server functionality

**Current Coverage:** >51% (target: 70%+)

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_workout_service.py

# Run specific test
pytest tests/test_workout_service.py::test_create_workout

# Run tests matching a pattern
pytest -k "workout"

# Run only CLI tests
pytest -m cli

# Run only service tests
pytest -m service
```

### Coverage Reports

```bash
# Run with coverage
pytest --cov=lift --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=lift --cov-report=html
# Then open: htmlcov/index.html

# Generate JSON coverage for CI
pytest --cov=lift --cov-report=json
```

### Parallel Execution

```bash
# Run tests in parallel (faster)
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

### Failing Tests

```bash
# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Re-run only failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff
```

## Test Organization

### Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── test_workout_service.py        # Workout service tests
├── test_set_service.py            # Set service tests
├── test_exercise_service.py       # Exercise service tests
├── test_body_service.py           # Body service tests
├── test_program_service.py        # Program service tests
├── test_pr_service.py             # PR service tests
├── test_stats_service.py          # Stats service tests
├── test_cli_workout.py            # Workout CLI tests
├── test_cli_exercise.py           # Exercise CLI tests
├── test_cli_body.py               # Body CLI tests
├── test_cli_stats.py              # Stats CLI tests
├── test_conversions.py            # Utility tests
├── test_calculations.py           # Calculation tests
├── test_mcp_*.py                  # MCP server tests
└── test_e2e_*.py                  # End-to-end tests
```

### Test Markers

Tests are marked for organization:

```python
@pytest.mark.unit
def test_calculation():
    """Fast, isolated test."""
    pass

@pytest.mark.integration
def test_service_interaction():
    """Tests multiple components together."""
    pass

@pytest.mark.e2e
def test_complete_workflow():
    """Complete user workflow test."""
    pass

@pytest.mark.cli
def test_cli_command():
    """CLI command test."""
    pass

@pytest.mark.service
def test_service_method():
    """Service layer test."""
    pass

@pytest.mark.slow
def test_long_running():
    """Test that takes >0.5s."""
    pass
```

### Running by Marker

```bash
pytest -m unit          # Fast unit tests
pytest -m integration   # Integration tests
pytest -m e2e           # End-to-end tests
pytest -m cli           # CLI tests
pytest -m service       # Service tests
pytest -m "not slow"    # Skip slow tests
```

## Shared Fixtures

Fixtures are defined in `tests/conftest.py` and available to all tests.

### Database Fixtures

#### db (function scope)

Creates a fresh temporary database for each test.

```python
def test_create_workout(db: DatabaseManager) -> None:
    """Test with isolated database."""
    service = WorkoutService(db)
    workout = service.create_workout(name="Test")
    assert workout.id > 0
```

**When to use:**
- Tests that modify data
- Tests that need isolation
- Most service tests

#### session_db (session scope)

Single database shared across all tests in a session.

```python
def test_read_exercises(session_db: DatabaseManager) -> None:
    """Test with shared read-only database."""
    service = ExerciseService(session_db)
    exercises = service.get_all()
    assert len(exercises) > 0
```

**When to use:**
- Read-only tests
- Tests that don't modify data
- Performance-critical test suites

### Data Fixtures

#### exercise_data

Standard set of exercise data for testing.

```python
def test_with_exercise_data(db: DatabaseManager, exercise_data: list[dict]) -> None:
    """Test using standard exercise data."""
    service = ExerciseService(db)
    # exercise_data provides realistic test data
```

#### sample_workout

Creates a workout with multiple exercises and sets.

```python
def test_workout_volume(db: DatabaseManager, sample_workout: dict) -> None:
    """Test using a complete workout."""
    # sample_workout contains workout, exercises, sets
    workout_id = sample_workout["workout_id"]
    # ...
```

### Creating Custom Fixtures

```python
# In your test file or conftest.py

@pytest.fixture
def my_custom_fixture(db: DatabaseManager) -> MyObject:
    """Create a custom test object."""
    # Setup
    obj = create_test_object(db)

    yield obj

    # Cleanup (if needed)
    cleanup_test_object(obj)
```

## Writing Tests

### Unit Test Example

Testing isolated business logic:

```python
# tests/test_calculations.py

from decimal import Decimal
from lift.utils.calculations import calculate_estimated_1rm

@pytest.mark.unit
def test_calculate_1rm_single_rep() -> None:
    """Test 1RM calculation for single rep."""
    result = calculate_estimated_1rm(Decimal("225"), 1)
    assert result == Decimal("225")

@pytest.mark.unit
def test_calculate_1rm_multiple_reps() -> None:
    """Test 1RM calculation for multiple reps."""
    result = calculate_estimated_1rm(Decimal("225"), 5)
    # Epley formula: 225 * (1 + 5/30) = 225 * 1.167 ≈ 262
    assert result == Decimal("225") * (Decimal("1") + Decimal("5") / Decimal("30"))

@pytest.mark.unit
def test_calculate_1rm_zero_weight() -> None:
    """Test 1RM with zero weight."""
    result = calculate_estimated_1rm(Decimal("0"), 5)
    assert result == Decimal("0")
```

### Service Test Example

Testing business logic with database:

```python
# tests/test_workout_service.py

import pytest
from lift.services.workout_service import WorkoutService
from lift.core.models import WorkoutCreate

@pytest.mark.service
def test_create_workout(db: DatabaseManager) -> None:
    """Test creating a workout."""
    service = WorkoutService(db)

    workout = service.create_workout(name="Push Day")

    assert workout.id > 0
    assert workout.name == "Push Day"
    assert workout.completed is True

@pytest.mark.service
def test_create_workout_invalid_name(db: DatabaseManager) -> None:
    """Test creating workout with invalid name."""
    service = WorkoutService(db)

    with pytest.raises(ValueError, match="name"):
        service.create_workout(name="")

@pytest.mark.service
def test_get_workout_by_id(db: DatabaseManager) -> None:
    """Test retrieving workout by ID."""
    service = WorkoutService(db)

    # Create
    created = service.create_workout(name="Test")

    # Retrieve
    retrieved = service.get_workout_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == created.name

@pytest.mark.service
def test_get_nonexistent_workout(db: DatabaseManager) -> None:
    """Test retrieving non-existent workout."""
    service = WorkoutService(db)

    result = service.get_workout_by_id(99999)

    assert result is None
```

### CLI Test Example

Testing command-line interface:

```python
# tests/test_cli_workout.py

from pathlib import Path
import pytest
from typer.testing import CliRunner
from lift.main import app

runner = CliRunner()

@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Create temporary database path."""
    db_path = tmp_path / "test.duckdb"
    return str(db_path)

@pytest.fixture
def initialized_db(temp_db: str) -> str:
    """Create and initialize temporary database."""
    result = runner.invoke(app, ["--db-path", temp_db, "init"])
    assert result.exit_code == 0
    return temp_db

@pytest.mark.cli
def test_workout_start(initialized_db: str) -> None:
    """Test starting a workout via CLI."""
    result = runner.invoke(
        app,
        ["--db-path", initialized_db, "workout", "start", "Push Day"],
    )

    assert result.exit_code == 0
    assert "Push Day" in result.stdout

@pytest.mark.cli
def test_workout_history_empty(initialized_db: str) -> None:
    """Test viewing history with no workouts."""
    result = runner.invoke(
        app,
        ["--db-path", initialized_db, "workout", "history"],
    )

    assert result.exit_code == 0
    # Should succeed even with no workouts

@pytest.mark.cli
def test_workout_invalid_command(initialized_db: str) -> None:
    """Test invalid workout command."""
    result = runner.invoke(
        app,
        ["--db-path", initialized_db, "workout", "nonexistent"],
    )

    assert result.exit_code != 0
```

### Integration Test Example

Testing multiple components together:

```python
# tests/test_complete_workout_flow.py

@pytest.mark.integration
def test_complete_workout_logging_flow(db: DatabaseManager) -> None:
    """Test complete workout logging workflow."""
    workout_service = WorkoutService(db)
    exercise_service = ExerciseService(db)
    set_service = SetService(db)

    # Get exercise
    exercises = exercise_service.get_all()
    bench_press = next(e for e in exercises if "Bench" in e.name)

    # Start workout
    workout = workout_service.create_workout(name="Push Day")

    # Log sets
    set1 = set_service.create_set(
        workout_id=workout.id,
        exercise_id=bench_press.id,
        set_number=1,
        weight=Decimal("225"),
        reps=8,
    )

    set2 = set_service.create_set(
        workout_id=workout.id,
        exercise_id=bench_press.id,
        set_number=2,
        weight=Decimal("225"),
        reps=7,
    )

    # Verify
    sets = set_service.get_sets_for_workout(workout.id)
    assert len(sets) == 2
    assert sets[0].weight == Decimal("225")
    assert sets[0].reps == 8
```

### End-to-End Test Example

Testing complete user workflows:

```python
# tests/test_e2e_complete_workflow.py

@pytest.mark.e2e
def test_complete_tracking_workflow(tmp_path: Path) -> None:
    """Test a complete workout tracking session via CLI."""
    db_path = tmp_path / "test.duckdb"

    # Initialize
    result = runner.invoke(app, ["--db-path", str(db_path), "init"])
    assert result.exit_code == 0

    # Start workout
    result = runner.invoke(
        app,
        ["--db-path", str(db_path), "workout", "start", "Push Day"],
    )
    assert result.exit_code == 0

    # List exercises
    result = runner.invoke(
        app,
        ["--db-path", str(db_path), "exercise", "list"],
    )
    assert result.exit_code == 0
    assert "Bench Press" in result.stdout

    # View history
    result = runner.invoke(
        app,
        ["--db-path", str(db_path), "workout", "history"],
    )
    assert result.exit_code == 0

    # Check stats
    result = runner.invoke(
        app,
        ["--db-path", str(db_path), "stats", "summary"],
    )
    assert result.exit_code == 0
```

## Testing Best Practices

### 1. Test Organization

- **One test file per module**: `test_workout_service.py` tests `workout_service.py`
- **Group related tests in classes**: Use `class TestWorkoutCreation`
- **Clear test names**: `test_create_workout_with_valid_data()`

### 2. Test Independence

```python
# Good: Each test is independent
def test_create_workout(db: DatabaseManager) -> None:
    service = WorkoutService(db)
    workout = service.create_workout(name="Test")
    assert workout.id > 0

def test_delete_workout(db: DatabaseManager) -> None:
    service = WorkoutService(db)
    workout = service.create_workout(name="Test")
    result = service.delete_workout(workout.id)
    assert result is True

# Bad: Tests depend on each other
# Don't do this!
```

### 3. Arrange-Act-Assert Pattern

```python
def test_calculate_volume() -> None:
    # Arrange - setup test data
    weight = Decimal("225")
    reps = 8

    # Act - perform the operation
    volume = calculate_volume(weight, reps)

    # Assert - verify the result
    assert volume == Decimal("1800")
```

### 4. Use Descriptive Assertions

```python
# Good: Clear what's being tested
assert workout.name == "Push Day", "Workout name should match input"
assert len(sets) == 3, "Should have created 3 sets"

# Better: Use pytest helpers
from pytest import approx
assert volume == approx(1800.0, rel=0.01)
```

### 5. Test Edge Cases

```python
def test_create_workout_empty_name(db: DatabaseManager) -> None:
    """Test creating workout with empty name."""
    service = WorkoutService(db)
    with pytest.raises(ValueError):
        service.create_workout(name="")

def test_calculate_1rm_zero_reps() -> None:
    """Test 1RM calculation with invalid reps."""
    # Should handle edge case gracefully
    pass
```

### 6. Use Fixtures for Setup

```python
@pytest.fixture
def workout_with_sets(db: DatabaseManager) -> dict:
    """Create a workout with sample sets."""
    workout_service = WorkoutService(db)
    set_service = SetService(db)

    workout = workout_service.create_workout(name="Test")

    sets = []
    for i in range(3):
        set_obj = set_service.create_set(
            workout_id=workout.id,
            exercise_id=1,
            set_number=i + 1,
            weight=Decimal("225"),
            reps=8,
        )
        sets.append(set_obj)

    return {"workout": workout, "sets": sets}

def test_workout_volume(workout_with_sets: dict) -> None:
    """Test using fixture."""
    workout = workout_with_sets["workout"]
    sets = workout_with_sets["sets"]
    # ... test logic
```

## Continuous Integration

### GitHub Actions

Tests run automatically on push and PR:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e '.[dev]'
      - run: pytest --cov=lift --cov-report=json
      - run: mypy lift/
      - run: ruff check lift/
```

### Pre-commit Hooks

Tests run locally before commit:

```bash
# Install pre-commit
pre-commit install

# Runs automatically on git commit
# Or run manually:
pre-commit run --all-files
```

## Coverage Goals

### Current Coverage

- Overall: >51%
- Services: ~70%
- CLI: ~40%
- Utils: ~60%

### Coverage Targets

- Overall: 70%+
- Critical services: 80%+
- New code: 80%+

### Checking Coverage

```bash
# Generate coverage report
pytest --cov=lift --cov-report=term-missing

# Find untested lines
pytest --cov=lift --cov-report=annotate
# Check lift/*.py,cover files

# Coverage by file
pytest --cov=lift --cov-report=term-missing | grep -A 100 "Name"
```

## Debugging Tests

### Print Debugging

```python
def test_my_feature(db: DatabaseManager, capfd) -> None:
    """Test with print output captured."""
    print("Debug info")

    # Test logic...

    # Access captured output
    captured = capfd.readouterr()
    print(f"stdout: {captured.out}")
```

### Interactive Debugging

```python
def test_my_feature(db: DatabaseManager) -> None:
    """Test with breakpoint."""
    workout = create_workout()

    import pdb; pdb.set_trace()  # Debugger stops here

    assert workout.id > 0
```

### Pytest Debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on error
pytest --pdbcls=IPython.terminal.debugger:Pdb
```

## Next Steps

- Write tests for new features (see [Extending Guide](./extending.md))
- Improve coverage in under-tested areas
- Add more end-to-end tests for complete workflows
- Contribute tests via pull requests

Happy testing! 🧪
