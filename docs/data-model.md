# Data Model Documentation

This document describes the Lift database schema, including all tables, relationships, and analytical views.

## Overview

Lift uses **DuckDB**, an embedded analytical database, to store all your fitness data. The database is located at `~/.lift/lift.db` by default.

### Key Design Principles

1. **Normalization**: Data is normalized to reduce redundancy
2. **Performance**: Indexes on frequently queried columns
3. **Flexibility**: Support for both structured programs and freestyle workouts
4. **Analytics**: Pre-built views for common analysis queries
5. **Extensibility**: Custom exercises and programs supported

## Database Schema Diagram

```
exercises ←──────┐
    ↑            │
    │            │
    ├── sets ────┼── workouts ←── programs
    │            │       ↑            ↑
    │            │       │            │
    │            └───────┼────────────┘
    │                    │
    └── program_exercises ── program_workouts
         personal_records

body_measurements (independent)
settings (independent)
```

## Core Tables

### exercises

The exercise library containing both built-in and custom exercises.

**Table:** `exercises`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `name` | VARCHAR | Unique exercise name |
| `category` | VARCHAR | Training category: Push, Pull, Legs, Core |
| `primary_muscle` | VARCHAR | Main muscle targeted |
| `secondary_muscles` | VARCHAR | JSON array of assisting muscles |
| `equipment` | VARCHAR | Equipment type required |
| `movement_type` | VARCHAR | Compound or Isolation |
| `is_custom` | BOOLEAN | True if user-created |
| `instructions` | TEXT | Form instructions (optional) |
| `video_url` | VARCHAR | Tutorial video link (optional) |
| `created_at` | TIMESTAMP | Creation timestamp |

**Indexes:**
- `idx_exercises_category` on `category`
- `idx_exercises_primary_muscle` on `primary_muscle`
- `idx_exercises_equipment` on `equipment`

**Example Data:**
```sql
{
  id: 1,
  name: "Barbell Bench Press",
  category: "Push",
  primary_muscle: "Chest",
  secondary_muscles: '["Triceps", "Shoulders"]',
  equipment: "Barbell",
  movement_type: "Compound",
  is_custom: false
}
```

**Category Values:**
- `Push`: Pressing movements (chest, shoulders, triceps)
- `Pull`: Pulling movements (back, biceps)
- `Legs`: Lower body (quads, hamstrings, glutes, calves)
- `Core`: Trunk stability (abs, obliques, lower back)

**Primary Muscle Values:**
- Upper: Chest, Back, Shoulders, Biceps, Triceps, Forearms
- Lower: Quads, Hamstrings, Glutes, Calves
- Core: Abs, Obliques, Lower Back

**Equipment Values:**
Barbell, Dumbbell, Cable, Machine, Bodyweight, Resistance Band, Kettlebell, EZ Bar, Trap Bar, Smith Machine

### workouts

Individual workout sessions, either freestyle or linked to a program.

**Table:** `workouts`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `date` | TIMESTAMP | When workout occurred |
| `program_workout_id` | INTEGER | FK to program_workouts (NULL if freestyle) |
| `name` | VARCHAR | Workout name (e.g., "Push Day A") |
| `duration_minutes` | INTEGER | Total workout duration |
| `bodyweight` | DECIMAL(5,2) | User's bodyweight during workout |
| `bodyweight_unit` | VARCHAR | lbs or kg |
| `notes` | TEXT | General workout notes |
| `rating` | INTEGER | 1-5 subjective rating |
| `completed` | BOOLEAN | Whether workout was completed |

**Indexes:**
- `idx_workouts_date` on `date DESC`
- `idx_workouts_program_workout` on `program_workout_id`

**Example Data:**
```sql
{
  id: 42,
  date: "2025-10-26 08:30:00",
  program_workout_id: null,
  name: "Morning Push",
  duration_minutes: 75,
  bodyweight: 185.5,
  bodyweight_unit: "lbs",
  notes: "Felt strong today",
  rating: 5,
  completed: true
}
```

### sets

Individual sets logged during workouts. This is the core tracking table.

**Table:** `sets`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `workout_id` | INTEGER | FK to workouts |
| `exercise_id` | INTEGER | FK to exercises |
| `set_number` | INTEGER | Set number within the exercise |
| `weight` | DECIMAL(6,2) | Weight used |
| `weight_unit` | VARCHAR | lbs or kg |
| `reps` | INTEGER | Repetitions performed |
| `rpe` | DECIMAL(3,1) | Rate of Perceived Exertion (6.0-10.0) |
| `tempo` | VARCHAR | Lifting tempo (e.g., "3-0-1-0") |
| `set_type` | VARCHAR | warmup, working, dropset, failure, amrap, rest_pause |
| `rest_seconds` | INTEGER | Rest time after this set |
| `is_superset` | BOOLEAN | Part of a superset |
| `superset_group` | INTEGER | Groups sets in supersets |
| `notes` | TEXT | Set-specific notes |
| `completed_at` | TIMESTAMP | When set was completed |

**Indexes:**
- `idx_sets_workout` on `workout_id`
- `idx_sets_exercise` on `exercise_id`
- `idx_sets_completed_at` on `completed_at DESC`

**Example Data:**
```sql
{
  id: 1523,
  workout_id: 42,
  exercise_id: 1,
  set_number: 1,
  weight: 225.0,
  weight_unit: "lbs",
  reps: 8,
  rpe: 7.5,
  tempo: null,
  set_type: "working",
  rest_seconds: 180,
  is_superset: false,
  superset_group: null,
  notes: null,
  completed_at: "2025-10-26 08:35:00"
}
```

**Set Type Values:**
- `warmup`: Warmup sets (not counted in volume stats)
- `working`: Standard working sets
- `dropset`: Drop set (reduce weight mid-set)
- `failure`: Taken to muscular failure
- `amrap`: As Many Reps As Possible
- `rest_pause`: Rest-pause technique

### personal_records

Tracks personal records automatically or manually.

**Table:** `personal_records`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `exercise_id` | INTEGER | FK to exercises |
| `record_type` | VARCHAR | Type of PR (1RM, 3RM, volume, etc.) |
| `value` | DECIMAL(8,2) | PR value |
| `reps` | INTEGER | Reps for rep-max PRs |
| `weight` | DECIMAL(6,2) | Weight used |
| `weight_unit` | VARCHAR | lbs or kg |
| `date` | TIMESTAMP | When PR was achieved |
| `workout_id` | INTEGER | FK to workouts |
| `set_id` | INTEGER | FK to sets |

**Indexes:**
- `idx_pr_exercise` on `exercise_id`
- `idx_pr_date` on `date DESC`
- `idx_pr_type` on `record_type`

**Record Type Values:**
- `1RM`, `3RM`, `5RM`, `10RM`: Rep max records
- `volume`: Highest single-set volume (weight × reps)
- `max_weight`: Heaviest weight lifted (any rep range)

### body_measurements

Tracks body composition and circumference measurements.

**Table:** `body_measurements`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `date` | TIMESTAMP | Measurement date |
| `weight` | DECIMAL(5,2) | Body weight |
| `weight_unit` | VARCHAR | lbs or kg |
| `body_fat_pct` | DECIMAL(4,2) | Body fat percentage |
| `neck` | DECIMAL(4,2) | Neck circumference |
| `shoulders` | DECIMAL(5,2) | Shoulder circumference |
| `chest` | DECIMAL(5,2) | Chest circumference |
| `waist` | DECIMAL(5,2) | Waist circumference |
| `hips` | DECIMAL(5,2) | Hip circumference |
| `bicep_left` | DECIMAL(4,2) | Left bicep circumference |
| `bicep_right` | DECIMAL(4,2) | Right bicep circumference |
| `forearm_left` | DECIMAL(4,2) | Left forearm circumference |
| `forearm_right` | DECIMAL(4,2) | Right forearm circumference |
| `thigh_left` | DECIMAL(5,2) | Left thigh circumference |
| `thigh_right` | DECIMAL(5,2) | Right thigh circumference |
| `calf_left` | DECIMAL(4,2) | Left calf circumference |
| `calf_right` | DECIMAL(4,2) | Right calf circumference |
| `measurement_unit` | VARCHAR | in or cm |
| `notes` | TEXT | Measurement notes |

**Index:**
- `idx_body_measurements_date` on `date DESC`

## Program Tables

### programs

Training program definitions.

**Table:** `programs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `name` | VARCHAR | Unique program name |
| `description` | TEXT | Program overview |
| `split_type` | VARCHAR | PPL, Upper/Lower, Full Body, Bro Split, Arnold Split, Custom |
| `days_per_week` | INTEGER | Frequency (1-7) |
| `duration_weeks` | INTEGER | Recommended program length |
| `is_active` | BOOLEAN | Currently active program |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

### program_workouts

Individual workout templates within a program.

**Table:** `program_workouts`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `program_id` | INTEGER | FK to programs |
| `name` | VARCHAR | Workout name (e.g., "Push A") |
| `day_number` | INTEGER | Day in program cycle (1-7) |
| `description` | TEXT | Workout description |
| `estimated_duration_minutes` | INTEGER | Expected duration |

**Index:**
- `idx_program_workouts_program` on `program_id`

### program_exercises

Exercise prescriptions within program workouts.

**Table:** `program_exercises`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `program_workout_id` | INTEGER | FK to program_workouts |
| `exercise_id` | INTEGER | FK to exercises |
| `order_number` | INTEGER | Exercise order in workout |
| `target_sets` | INTEGER | Prescribed sets |
| `target_reps_min` | INTEGER | Minimum target reps |
| `target_reps_max` | INTEGER | Maximum target reps |
| `target_rpe` | DECIMAL(3,1) | Target RPE |
| `rest_seconds` | INTEGER | Prescribed rest period |
| `tempo` | VARCHAR | Prescribed tempo |
| `notes` | TEXT | Exercise-specific notes |
| `is_superset` | BOOLEAN | Part of superset |
| `superset_group` | INTEGER | Superset grouping |

**Indexes:**
- `idx_program_exercises_workout` on `program_workout_id`
- `idx_program_exercises_exercise` on `exercise_id`

## Configuration Table

### settings

Application settings and preferences.

**Table:** `settings`

| Column | Type | Description |
|--------|------|-------------|
| `key` | VARCHAR | Setting name (primary key) |
| `value` | VARCHAR | Setting value |
| `description` | TEXT | What this setting controls |
| `updated_at` | TIMESTAMP | Last update |

**Default Settings:**
- `default_weight_unit`: lbs or kg
- `default_measurement_unit`: in or cm
- `enable_rpe`: true/false
- `enable_tempo`: true/false
- `rest_timer_default`: seconds
- `auto_detect_pr`: true/false
- `database_path`: path to database file

## Analytical Views

Pre-built views for common analytics queries.

### workout_volume

Total volume and stats per workout.

```sql
SELECT
    workout_id,
    date,
    workout_name,
    exercise_count,      -- Distinct exercises
    total_sets,          -- Total working sets
    total_volume,        -- Sum of weight × reps
    avg_rpe,             -- Average RPE
    duration_minutes
FROM workout_volume
ORDER BY date DESC;
```

### weekly_muscle_volume

Volume breakdown by muscle group per week.

```sql
SELECT
    week_start,
    primary_muscle,
    workout_count,
    total_sets,
    total_volume,
    avg_rpe
FROM weekly_muscle_volume
WHERE week_start >= current_date - interval '12 weeks'
ORDER BY week_start DESC, total_volume DESC;
```

### exercise_progression

Track progression for specific exercises over time.

```sql
SELECT
    exercise_name,
    workout_date,
    set_number,
    weight,
    reps,
    rpe,
    volume,              -- weight × reps
    estimated_1rm        -- Epley formula: weight × (1 + reps/30)
FROM exercise_progression
WHERE exercise_id = 1
ORDER BY workout_date DESC
LIMIT 50;
```

### pr_summary

All personal records with recency.

```sql
SELECT
    exercise_name,
    record_type,
    value,
    reps,
    weight,
    weight_unit,
    date,
    days_since          -- Days since PR was set
FROM pr_summary
ORDER BY exercise_name, record_type;
```

### training_frequency

Workout frequency over last 12 weeks.

```sql
SELECT
    week_start,
    workout_count,      -- Workouts that week
    total_minutes,      -- Total training time
    avg_duration        -- Average workout length
FROM training_frequency
ORDER BY week_start DESC;
```

### bodyweight_trend

Weekly bodyweight averages.

```sql
SELECT
    week_start,
    avg_weight,
    min_weight,
    max_weight,
    weight_unit
FROM bodyweight_trend
ORDER BY week_start DESC;
```

## Relationships

### One-to-Many

- `programs` → `program_workouts` (one program has many workouts)
- `program_workouts` → `program_exercises` (one workout has many exercises)
- `workouts` → `sets` (one workout has many sets)
- `exercises` → `sets` (one exercise used in many sets)
- `exercises` → `personal_records` (one exercise has many PRs)

### Many-to-One

- `sets` → `workouts` (many sets belong to one workout)
- `sets` → `exercises` (many sets use one exercise)
- `workouts` → `program_workouts` (many workouts can use one template)

### Optional Relationships

- `workouts.program_workout_id` is NULL for freestyle workouts
- `personal_records.workout_id` and `set_id` can be NULL for manually entered PRs

## Data Calculations

### Volume

**Set Volume:** `weight × reps`

**Workout Volume:** Sum of all working set volumes

**Weekly Volume:** Sum of all workout volumes in a week

**Muscle Volume:** Sum of volumes for exercises targeting that muscle

### Estimated 1RM

Using the **Epley Formula:**

```
1RM = weight × (1 + reps / 30)
```

For 1-rep sets, the weight itself is the 1RM.

### RPE Scale

**Rate of Perceived Exertion** (6.0 - 10.0):

- **6.0**: Very light effort, could do 15+ more reps
- **7.0**: Light effort, could do 10+ more reps
- **8.0**: Moderate effort, could do 4-6 more reps
- **8.5**: Hard effort, could do 2-3 more reps
- **9.0**: Very hard, could do 1 more rep
- **9.5**: Maximum effort, possibly 1 more rep
- **10.0**: Absolute max, no reps left

## Data Integrity

### Constraints

- **Unique constraints:** exercise names, program names
- **Foreign keys:** Enforce referential integrity
- **Default values:** Timestamps, units, booleans
- **NOT NULL:** Required fields enforced

### Indexes

Indexes are created on:
- Primary keys (automatic)
- Foreign keys (for joins)
- Date columns (for time-based queries)
- Filter columns (category, muscle, equipment)

### Sequences

Auto-increment handled via DuckDB sequences:
- `exercises_id_seq`
- `programs_id_seq`
- `program_workouts_id_seq`
- `program_exercises_id_seq`
- `workouts_id_seq`
- `sets_id_seq`
- `personal_records_id_seq`
- `body_measurements_id_seq`

## Querying Your Data

### Example Queries

**Get all workouts in last 30 days:**
```sql
SELECT * FROM workouts
WHERE date >= current_timestamp - interval '30 days'
ORDER BY date DESC;
```

**Find total volume for an exercise:**
```sql
SELECT
    e.name,
    COUNT(s.id) as total_sets,
    SUM(s.weight * s.reps) as total_volume
FROM sets s
JOIN exercises e ON s.exercise_id = e.id
WHERE e.name = 'Barbell Bench Press'
  AND s.set_type = 'working'
GROUP BY e.name;
```

**Check weekly workout frequency:**
```sql
SELECT
    date_trunc('week', date) as week,
    COUNT(*) as workouts
FROM workouts
WHERE date >= current_timestamp - interval '12 weeks'
GROUP BY date_trunc('week', date)
ORDER BY week DESC;
```

**Get PRs for all exercises:**
```sql
SELECT * FROM pr_summary
ORDER BY exercise_name, record_type, date DESC;
```

## Backup and Export

### Backup Database

```bash
# Full database backup
cp ~/.lift/lift.db ~/backup/lift-$(date +%Y%m%d).db

# Or use DuckDB export
duckdb ~/.lift/lift.db "EXPORT DATABASE 'backup' (FORMAT PARQUET)"
```

### Export Specific Tables

```bash
# Export sets to CSV
duckdb ~/.lift/lift.db "COPY sets TO 'sets.csv' (HEADER, DELIMITER ',')"

# Export workouts to JSON
duckdb ~/.lift/lift.db "COPY workouts TO 'workouts.json'"
```

## Next Steps

- [Architecture Guide](./architecture.md) - Understanding how Lift components work together
- [Extending Lift](./extending.md) - Adding new features or customizations
- [Troubleshooting](./troubleshooting.md) - Common database issues
