# 🏋️ LIFT - Bodybuilding Workout Tracker

A robust, feature-complete command-line interface for tracking weightlifting sessions with a focus on bodybuilding and progressive overload.

## Features

### 📝 Comprehensive Exercise Library
- **137 pre-loaded exercises** covering all major muscle groups
- Organized by category (Push, Pull, Legs, Core)
- Classified by movement type (Compound vs Isolation)
- Multiple equipment types (Barbell, Dumbbell, Cable, Machine, Bodyweight)
- Add custom exercises
- Search and filter by muscle group, category, or equipment

### 💪 Workout Tracking
- **Interactive workout sessions** with beautiful terminal UI
- Real-time set logging with shortcuts (s=same, +5=add weight)
- Track weight, reps, RPE (Rate of Perceived Exertion)
- Optional tempo tracking
- View last performance for each exercise
- Automatic volume calculations
- Workout history and summaries

### 📋 Training Programs
- Create custom training programs with splits
- Pre-loaded sample programs:
  - PPL 6-Day (Push/Pull/Legs)
  - Upper/Lower 4-Day
  - Full Body 3-Day
- Workout templates with exercise prescriptions
- Set target sets, reps ranges, RPE, and rest periods
- Clone and modify existing programs
- Track program adherence

### 📊 Analytics & Statistics
- **Automatic PR detection** (1RM, 3RM, 5RM, 10RM, volume PRs)
- Exercise progression tracking
- Volume analysis by muscle group
- Weekly/monthly training summaries
- Training consistency streaks
- Terminal-based charts and visualizations
- Progressive overload recommendations
- Fatigue monitoring

### 📏 Body Tracking
- Bodyweight logging with trend analysis
- Comprehensive body measurements (circumferences)
- Body fat percentage tracking
- Progress comparisons (week-over-week, month-over-month)
- Measurement history and trends
- Weight charts and analytics

### 💾 Data Management
- Export to CSV or JSON
- Import data from other sources
- Database backup and restore
- Configuration management
- Data optimization tools

### 🤖 AI Assistant Integration (MCP Server)
- **Claude Desktop integration** via Model Context Protocol
- Natural language workout tracking and analysis
- AI-powered exercise recommendations
- Intelligent progression analysis
- Conversational data queries
- See [MCP Server Documentation](docs/MCP_SERVER.md) for setup

## Installation

### Requirements
- Python 3.11 or higher

### Install from PyPI (Recommended)

```bash
# Standard installation
pip install lift-tracker

# With MCP server support for Claude Desktop
pip install lift-tracker[mcp]
```

### Install with Homebrew (macOS/Linux)

```bash
# Download the formula
curl -O https://github.com/parkerdgabel/lift/releases/latest/download/lift.rb

# Install
brew install ./lift.rb
```

### Install on Debian/Ubuntu

```bash
# Download the .deb package
wget https://github.com/parkerdgabel/lift/releases/latest/download/lift_0.1.0-1_all.deb

# Install
sudo dpkg -i lift_0.1.0-1_all.deb

# Install dependencies if needed
sudo apt-get install -f
```

### Install from source

```bash
# Clone the repository
git clone https://github.com/parkerdgabel/lift.git
cd lift

# Install with pip
pip install -e .
```

## Quick Start

### 1. Initialize the database

```bash
lift init
```

This creates the database, loads 137 exercises, and sets up default configuration.

### 2. Start your first workout

```bash
lift workout start
```

Follow the interactive prompts to log sets for your exercises.

### 3. View your exercises

```bash
# List all exercises
lift exercises list

# Search for exercises
lift exercises search "bench"

# Filter by muscle group
lift exercises list --muscle Chest

# Filter by category
lift exercises list --category Push
```

### 4. Import sample programs

```bash
lift program import-samples
lift program list
lift program show "PPL 6-Day"
```

## Documentation

### Man Page

LIFT includes a comprehensive man page with detailed documentation of all commands and options.

```bash
# Install the man page (required for PyPI installations)
lift install-manpage

# View the man page
man lift

# Or view directly from source
man man/lift.1
```

**Note:** When installing via PyPI (`pip install lift-tracker`), the man page is bundled but not automatically installed to your system. Run `lift install-manpage` after installation to make it available via the `man` command. Homebrew and Debian packages install the man page automatically.

The man page includes:
- Complete command reference
- Detailed option descriptions
- Practical examples for all features
- Configuration settings
- Database schema information
- Environment variables

### MCP Server (AI Assistant Integration)

LIFT can integrate with Claude Desktop and other AI assistants via the Model Context Protocol.

```bash
# Quick setup with interactive wizard
lift mcp setup

# Or manually configure
lift mcp config >> ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Start the MCP server (usually automatic via Claude Desktop)
lift mcp start
```

Once configured, you can interact with your workout data naturally through Claude:

```
You: "Show me my recent workouts"
You: "What exercises target chest?"
You: "How is my bench press progressing?"
You: "Start a new workout called Push Day"
You: "Log my weight at 185 lbs"
```

See [MCP Server Documentation](docs/MCP_SERVER.md) for complete setup and usage guide.

## Usage Guide

### Exercise Management

```bash
# List exercises with filters
lift exercises list --category Push --equipment Barbell

# Show exercise library statistics
lift exercises stats

# Get detailed exercise info
lift exercises info "Barbell Bench Press"

# Add a custom exercise
lift exercises add

# Delete custom exercise
lift exercises delete "My Custom Exercise"
```

### Workout Logging

```bash
# Start interactive workout session
lift workout start

# Show last workout
lift workout last

# View workout history
lift workout history --limit 10

# Delete a workout
lift workout delete <workout-id>
```

#### Interactive Workout Session

During a workout session, you can log sets using these shortcuts:

- `185 10` → 185 lbs × 10 reps
- `185 10 8.5` → 185 lbs × 10 reps @ RPE 8.5
- `s` → Same as previous set
- `+5` → Add 5 lbs to previous weight
- `-5 8` → Subtract 5 lbs, 8 reps
- `done` → Finish current exercise

Example session:
```
Exercise: bench press
Set 1 > 185 10 8
✓ 185 lbs × 10 reps @ RPE 8.0

Set 2 > s
✓ 185 lbs × 10 reps @ RPE 8.0

Set 3 > +5 8 9
✓ 190 lbs × 8 reps @ RPE 9.0

Set 4 > done
```

### Program Management

```bash
# Create a new program (interactive)
lift program create

# List all programs
lift program list

# Show program details
lift program show "PPL 6-Day"

# Activate a program
lift program activate "PPL 6-Day"

# Clone a program
lift program clone "PPL 6-Day" "My PPL Variation"

# Delete a program
lift program delete "Old Program"
```

### Analytics & Statistics

```bash
# Weekly summary
lift stats summary --week

# Monthly summary
lift stats summary --month

# Exercise-specific statistics
lift stats exercise "Bench Press"

# Exercise progression with chart
lift stats exercise "Squat" --chart

# Volume analysis
lift stats volume --weeks 12

# Personal records
lift stats pr
lift stats pr --exercise "Deadlift"

# Muscle group analysis
lift stats muscle Chest

# Training streak
lift stats streak

# Detailed progression
lift stats progress "Overhead Press" --chart
```

### Body Tracking

```bash
# Log bodyweight
lift body weight 185.5

# Full body measurement entry
lift body measure

# View measurement history
lift body history

# Progress comparison
lift body progress --weeks 4

# View trends with charts
lift body chart weight --weeks 12
lift body chart waist --weeks 8

# Show latest measurement
lift body latest
```

### Data Management

```bash
# Export data to JSON
lift data export --format json --output my_data.json

# Export specific table to CSV
lift data export --format csv --table workouts --output workouts.csv

# Import data
lift data import exercises.csv --table exercises

# Create backup
lift data backup --output ~/backups/lift_backup

# Restore from backup
lift data restore ~/backups/lift_backup

# Optimize database
lift data optimize
```

### Configuration

```bash
# List all settings
lift config list

# Get a setting
lift config get default_weight_unit

# Set a setting
lift config set default_weight_unit kg

# Reset to defaults
lift config reset
```

Available settings:
- `default_weight_unit` - lbs or kg (default: lbs)
- `default_measurement_unit` - in or cm (default: in)
- `enable_rpe` - Enable RPE tracking (default: true)
- `enable_tempo` - Enable tempo tracking (default: false)
- `rest_timer_default` - Default rest timer in seconds (default: 90)
- `auto_detect_pr` - Automatically detect PRs (default: true)

## Database

LIFT uses DuckDB for high-performance analytical queries. The database is stored at `~/.lift/lift.duckdb` by default.

### Custom database location

```bash
# Set via environment variable
export LIFT_DB_PATH=/path/to/custom/lift.duckdb
lift init

# Or specify per-command
lift --db-path /path/to/custom/lift.duckdb info
```

### Database schema

The database includes:
- **exercises** - Exercise library with metadata
- **workouts** - Workout sessions
- **sets** - Individual set logs
- **programs** - Training programs
- **program_workouts** - Workout templates
- **program_exercises** - Exercise prescriptions
- **personal_records** - PR tracking
- **body_measurements** - Body tracking data
- **settings** - Configuration

Plus analytical views for efficient querying:
- `workout_volume` - Volume per workout
- `weekly_muscle_volume` - Volume by muscle group per week
- `exercise_progression` - Exercise history with 1RM estimates
- `bodyweight_trend` - Weekly bodyweight averages

## Architecture

LIFT follows a clean architecture with clear separation of concerns:

```
lift/
├── cli/           # CLI command groups (Typer)
├── services/      # Business logic layer
├── core/          # Database and models (DuckDB, Pydantic)
├── utils/         # Utilities (calculations, formatters, charts)
└── data/          # Seed data (exercises, programs)
```

### Technology Stack

- **Typer** - CLI framework with auto-completion
- **Rich** - Beautiful terminal output and formatting
- **DuckDB** - High-performance analytical database
- **Pydantic** - Data validation and serialization
- **Plotext** - Terminal-based charts and graphs
- **Python 3.11+** - Modern Python with type hints

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Development

### Setup development environment

```bash
# Clone repository
git clone https://github.com/yourusername/lift.git
cd lift

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=lift --cov-report=html

# Type checking
mypy lift

# Linting
ruff check lift
```

### Running tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_exercise_service.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=lift --cov-report=term-missing
```

## Roadmap

Future enhancements:
- [ ] Mobile companion app
- [ ] Web dashboard
- [ ] Training block periodization
- [ ] Exercise substitution recommendations
- [ ] Volume landmarks and achievements
- [ ] Social features (share programs, workouts)
- [ ] Integration with fitness trackers
- [ ] Plate calculator
- [ ] Rest timer with notifications
- [ ] Workout templates from programs
- [ ] Exercise demonstration GIFs

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built with love for the bodybuilding community. Train hard, track harder! 💪

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Made with Claude Code** 🤖
