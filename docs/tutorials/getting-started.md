# Getting Started with Lift

This guide will walk you through installing Lift and completing your first workout tracking session.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install lift-tracker
```

### Option 2: Install from Source

```bash
git clone https://github.com/parkerdgabel/lift.git
cd lift
pip install -e .
```

### Verify Installation

```bash
lift --version
```

You should see output showing the installed version.

## Initial Setup

### 1. Initialize Your Database

Before you can start tracking workouts, you need to initialize the database:

```bash
lift init
```

This creates a DuckDB database at `~/.lift/lift.db` with all necessary tables and default exercises.

**Custom Database Location (Optional)**

If you want to use a different location for your database:

```bash
lift --db-path /path/to/custom/lift.db init
```

### 2. Verify Exercise Library

Lift comes with a comprehensive exercise library. Check what's available:

```bash
lift exercise list
```

You should see exercises organized by category (Push, Pull, Legs, Core).

## Your First Workout

Let's track a simple Push workout with three exercises.

### Step 1: Start a Workout

```bash
lift workout start
```

You'll be prompted to enter a workout name. Enter something like "Push Day A".

The CLI will show you the workout ID and confirm it's been created.

### Step 2: Log Your First Exercise

Let's log some bench press sets:

```bash
lift workout log
```

This starts an interactive workout session:

1. **Select Exercise**: Type "bench" to search, then select "Barbell Bench Press"
2. **Log Sets**: For each set, enter:
   - Weight (e.g., `185`)
   - Reps (e.g., `8`)
   - Optionally, RPE if you're tracking it

**Example Set Entry:**

```
Weight: 185
Reps: 8
RPE [optional]: 7.5
```

3. **Add More Sets**: After each set, you'll be prompted:
   - Press Enter to log another set
   - Type 'n' when done with this exercise

4. **Add More Exercises**: After finishing an exercise:
   - Press Enter to add another exercise
   - Type 'n' when done with the workout

### Step 3: Complete Your Workout

Once you've logged all exercises, the workout will be automatically completed and you'll see a summary showing:

- Total sets completed
- Total volume (weight × reps)
- Duration
- Exercises performed

## Quick Logging Workflow

For experienced users who know exercise IDs:

```bash
# Log sets directly for exercise ID 1 (Barbell Bench Press)
lift workout log --quick --exercise-id 1

# This will prompt for sets without the exercise selection step
```

## Viewing Your Progress

### Check Your Last Workout

```bash
lift workout last
```

This displays a detailed breakdown of your most recent session.

### View Workout History

```bash
lift workout history
```

See all your completed workouts with dates and summaries.

### Check Exercise Stats

```bash
lift stats exercise 1
```

View detailed statistics for a specific exercise, including:
- Total volume over time
- Personal records
- Set/rep patterns
- Frequency

## Body Tracking

Lift also supports body measurement tracking.

### Log Your Weight

```bash
lift body weight 185.5
```

Or in kilograms:

```bash
lift body weight 84.0 --unit kg
```

### Full Body Measurements

For comprehensive tracking:

```bash
lift body measure
```

This interactive command prompts for:
- Weight
- Body fat percentage
- Circumference measurements (chest, waist, arms, etc.)

### View Body History

```bash
lift body history
```

See your measurement trends over time.

### View Progress

```bash
lift body progress
```

See changes compared to 4 weeks ago (customizable with `--weeks`).

## Working with Programs

Lift supports structured workout programs for consistent progression.

### View Available Programs

```bash
lift program list
```

### Start a Program

```bash
lift program start "Upper/Lower Split"
```

### Check Program Progress

```bash
lift program progress
```

## Tips for Success

1. **Be Consistent**: Log workouts immediately after completing them
2. **Track RPE**: Rate of Perceived Exertion helps gauge recovery and adjust training
3. **Review Progress**: Check stats weekly to ensure progressive overload
4. **Use Quick Logging**: Once you know exercise IDs, use `--quick` flag for faster entry
5. **Backup Your Data**: Your database is at `~/.lift/lift.db` - back it up regularly!

## Common Workflows

### Full Body Workout Day

```bash
# Start workout
lift workout start

# Log exercises interactively
lift workout log

# Check today's summary
lift workout last

# Update body weight
lift body weight 186.0
```

### Check Weekly Progress

```bash
# View last 7 workouts
lift workout history --limit 7

# Check volume trends
lift stats volume --weeks 4

# Review body progress
lift body progress --weeks 1
```

### Pre-Workout Routine

```bash
# Check incomplete workouts
lift workout incomplete

# Resume if needed
lift workout resume

# Or start fresh
lift workout start
```

## Next Steps

Now that you're familiar with the basics, explore these topics:

- [Creating Custom Exercises](./custom-exercises.md)
- [Designing Your Own Programs](./program-design.md)
- [Advanced Stats and Analysis](../user-guide/stats.md) (coming soon)
- [Data Export and Backup](../user-guide/data-management.md) (coming soon)

## Getting Help

- Run any command with `--help` flag for detailed options
- Check the [Troubleshooting Guide](../troubleshooting.md) for common issues
- Report bugs at [GitHub Issues](https://github.com/parkerdgabel/lift/issues)
- Read the full [User Guide](../user-guide/overview.md) (coming soon)

## Quick Reference

| Task | Command |
|------|---------|
| Initialize database | `lift init` |
| Start workout | `lift workout start` |
| Log workout interactively | `lift workout log` |
| Quick log (by exercise ID) | `lift workout log --quick --exercise-id <id>` |
| View last workout | `lift workout last` |
| View workout history | `lift workout history` |
| Complete workout | `lift workout complete` |
| Log body weight | `lift body weight <value>` |
| Full body measurement | `lift body measure` |
| View exercise stats | `lift stats exercise <id>` |
| View volume stats | `lift stats volume` |
| View PRs | `lift stats pr` |
| List exercises | `lift exercise list` |
| Search exercises | `lift exercise search <term>` |
| Add custom exercise | `lift exercise add` |
| Start program | `lift program start <name>` |
| View program progress | `lift program progress` |

Happy lifting! 💪
