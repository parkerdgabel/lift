# Changelog

All notable changes to LIFT will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-26

### Added

#### Core Features
- **Exercise Library** - 137 pre-loaded exercises covering all major muscle groups
  - Organized by category (Push, Pull, Legs, Core)
  - Classified by movement type (Compound vs Isolation)
  - Multiple equipment types (Barbell, Dumbbell, Cable, Machine, Bodyweight)
  - Search and filter capabilities
  - Custom exercise creation

- **Workout Tracking** - Interactive workout sessions with real-time logging
  - Set-by-set logging with weight, reps, and RPE tracking
  - Shortcuts for quick entry (s=same, +5=add weight, -5=reduce weight)
  - View last performance for each exercise
  - Automatic volume calculations
  - Workout history and summaries
  - Finish workout with duration and rating

- **Training Programs** - Complete program management system
  - Pre-loaded sample programs (PPL 6-Day, Upper/Lower 4-Day, Full Body 3-Day)
  - Custom program creation with workout templates
  - Exercise prescriptions with target sets, reps, RPE, and rest periods
  - Program cloning and modification
  - Program activation and adherence tracking

- **Analytics & Statistics** - Comprehensive performance tracking
  - Automatic PR detection (1RM, 3RM, 5RM, 10RM, volume PRs)
  - Exercise progression tracking with 6 different 1RM formulas
  - Volume analysis by muscle group
  - Weekly/monthly training summaries
  - Training consistency streaks
  - Terminal-based charts and visualizations
  - Progressive overload recommendations
  - Fatigue monitoring

- **Body Tracking** - Complete body measurement system
  - Bodyweight logging with trend analysis
  - Comprehensive circumference measurements (chest, waist, arms, legs, etc.)
  - Body fat percentage tracking
  - Progress comparisons (week-over-week, month-over-month)
  - Measurement history and trends
  - Weight charts and analytics

- **Data Management** - Import/export and backup capabilities
  - Export to CSV or JSON formats
  - Import data from external sources
  - Database backup and restore
  - Configuration management (7 settings)
  - Data optimization tools

#### Technical Features
- **Database** - DuckDB for high-performance analytical queries
  - Efficient schema with sequences for auto-increment
  - Analytical views for complex queries
  - Automatic database initialization with seed data

- **CLI Framework** - Modern command-line interface
  - Built with Typer for excellent UX
  - Rich terminal formatting with colors and tables
  - Interactive prompts and confirmations
  - Helpful error messages
  - Auto-completion support

- **Testing** - Comprehensive test suite
  - 260+ tests covering all functionality
  - End-to-end workflow tests
  - Cross-service integration tests
  - CLI integration tests
  - Shared fixtures for realistic test data

- **DevOps & Quality**
  - Ruff linting and formatting with 25+ rule categories
  - Pre-commit hooks for code quality
  - GitHub Actions CI/CD workflows
  - Cross-platform testing (Ubuntu, macOS, Windows)
  - Multi-version Python support (3.11, 3.12)
  - Security scanning with bandit
  - Code coverage reporting

### Dependencies
- Python >= 3.11
- typer >= 0.12.0
- rich >= 13.7.0
- duckdb >= 1.0.0
- pydantic >= 2.8.0
- plotext >= 5.2.8
- python-dateutil >= 2.9.0

[0.1.0]: https://github.com/parkerdgabel/lift/releases/tag/v0.1.0
