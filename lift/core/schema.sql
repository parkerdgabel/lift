-- LIFT Database Schema
-- Complete schema for bodybuilding workout tracking

-- ============================================================================
-- SEQUENCES FOR AUTO-INCREMENT
-- ============================================================================

CREATE SEQUENCE IF NOT EXISTS exercises_id_seq START 1;
CREATE SEQUENCE IF NOT EXISTS programs_id_seq START 1;
CREATE SEQUENCE IF NOT EXISTS program_workouts_id_seq START 1;
CREATE SEQUENCE IF NOT EXISTS program_exercises_id_seq START 1;
CREATE SEQUENCE IF NOT EXISTS workouts_id_seq START 1;
CREATE SEQUENCE IF NOT EXISTS sets_id_seq START 1;
CREATE SEQUENCE IF NOT EXISTS personal_records_id_seq START 1;
CREATE SEQUENCE IF NOT EXISTS body_measurements_id_seq START 1;

-- ============================================================================
-- EXERCISE LIBRARY
-- ============================================================================

CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY DEFAULT nextval('exercises_id_seq'),
    name VARCHAR NOT NULL UNIQUE,
    category VARCHAR NOT NULL,              -- Push, Pull, Legs, Core
    primary_muscle VARCHAR NOT NULL,        -- Chest, Back, Quads, Hamstrings, etc.
    secondary_muscles VARCHAR,              -- JSON array of secondary muscles
    equipment VARCHAR NOT NULL,             -- Barbell, Dumbbell, Cable, Machine, Bodyweight
    movement_type VARCHAR,                  -- Compound, Isolation
    is_custom BOOLEAN DEFAULT FALSE,
    instructions TEXT,
    video_url VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_exercises_category ON exercises(category);
CREATE INDEX IF NOT EXISTS idx_exercises_primary_muscle ON exercises(primary_muscle);
CREATE INDEX IF NOT EXISTS idx_exercises_equipment ON exercises(equipment);

-- ============================================================================
-- TRAINING PROGRAMS
-- ============================================================================

CREATE TABLE IF NOT EXISTS programs (
    id INTEGER PRIMARY KEY DEFAULT nextval('programs_id_seq'),
    name VARCHAR NOT NULL UNIQUE,
    description TEXT,
    split_type VARCHAR,                     -- PPL, Upper/Lower, Full Body, Bro Split
    days_per_week INTEGER,
    duration_weeks INTEGER,                 -- Program duration
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS program_workouts (
    id INTEGER PRIMARY KEY DEFAULT nextval('program_workouts_id_seq'),
    program_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,                  -- "Push A", "Pull B", "Leg Day", etc.
    day_number INTEGER,                     -- Day in the program (1-7)
    description TEXT,
    estimated_duration_minutes INTEGER,
    FOREIGN KEY (program_id) REFERENCES programs(id)
);

CREATE INDEX IF NOT EXISTS idx_program_workouts_program ON program_workouts(program_id);

CREATE TABLE IF NOT EXISTS program_exercises (
    id INTEGER PRIMARY KEY DEFAULT nextval('program_exercises_id_seq'),
    program_workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    order_number INTEGER NOT NULL,         -- Exercise order in workout
    target_sets INTEGER,
    target_reps_min INTEGER,
    target_reps_max INTEGER,
    target_rpe DECIMAL(3,1),               -- Target RPE (6.0-10.0)
    rest_seconds INTEGER,
    tempo VARCHAR,                          -- e.g., "3-0-1-0"
    notes TEXT,
    is_superset BOOLEAN DEFAULT FALSE,
    superset_group INTEGER,                 -- Groups exercises in supersets
    FOREIGN KEY (program_workout_id) REFERENCES program_workouts(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);

CREATE INDEX IF NOT EXISTS idx_program_exercises_workout ON program_exercises(program_workout_id);
CREATE INDEX IF NOT EXISTS idx_program_exercises_exercise ON program_exercises(exercise_id);

-- ============================================================================
-- WORKOUT SESSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY DEFAULT nextval('workouts_id_seq'),
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    program_workout_id INTEGER,             -- NULL if freestyle workout
    name VARCHAR,                           -- Workout name (e.g., "Push Day", "Leg Day")
    duration_minutes INTEGER,
    bodyweight DECIMAL(5,2),
    bodyweight_unit VARCHAR DEFAULT 'lbs',
    notes TEXT,
    rating INTEGER,                         -- 1-5 how good was the workout
    completed BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (program_workout_id) REFERENCES program_workouts(id)
);

CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(date DESC);
CREATE INDEX IF NOT EXISTS idx_workouts_program_workout ON workouts(program_workout_id);

-- ============================================================================
-- SETS (Individual Set Logging)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sets (
    id INTEGER PRIMARY KEY DEFAULT nextval('sets_id_seq'),
    workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    set_number INTEGER NOT NULL,
    weight DECIMAL(6,2) NOT NULL,
    weight_unit VARCHAR DEFAULT 'lbs',
    reps INTEGER NOT NULL,
    rpe DECIMAL(3,1),                       -- 6.0 to 10.0 (Borg RPE scale)
    tempo VARCHAR,                          -- "eccentric-pause-concentric-pause" (e.g., "3-0-1-0")
    set_type VARCHAR DEFAULT 'working',     -- warmup, working, dropset, failure, amrap, rest_pause
    rest_seconds INTEGER,
    is_superset BOOLEAN DEFAULT FALSE,
    superset_group INTEGER,                 -- Groups sets in supersets
    notes TEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workout_id) REFERENCES workouts(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);

CREATE INDEX IF NOT EXISTS idx_sets_workout ON sets(workout_id);
CREATE INDEX IF NOT EXISTS idx_sets_exercise ON sets(exercise_id);
CREATE INDEX IF NOT EXISTS idx_sets_completed_at ON sets(completed_at DESC);

-- ============================================================================
-- PERSONAL RECORDS
-- ============================================================================

CREATE TABLE IF NOT EXISTS personal_records (
    id INTEGER PRIMARY KEY DEFAULT nextval('personal_records_id_seq'),
    exercise_id INTEGER NOT NULL,
    record_type VARCHAR NOT NULL,           -- 1RM, 3RM, 5RM, 10RM, volume, max_weight
    value DECIMAL(8,2) NOT NULL,
    reps INTEGER,                           -- Number of reps (for rep maxes)
    weight DECIMAL(6,2),                    -- Weight used
    weight_unit VARCHAR DEFAULT 'lbs',
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    workout_id INTEGER,
    set_id INTEGER,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (workout_id) REFERENCES workouts(id),
    FOREIGN KEY (set_id) REFERENCES sets(id)
);

CREATE INDEX IF NOT EXISTS idx_pr_exercise ON personal_records(exercise_id);
CREATE INDEX IF NOT EXISTS idx_pr_date ON personal_records(date DESC);
CREATE INDEX IF NOT EXISTS idx_pr_type ON personal_records(record_type);

-- ============================================================================
-- BODY MEASUREMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS body_measurements (
    id INTEGER PRIMARY KEY DEFAULT nextval('body_measurements_id_seq'),
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    weight DECIMAL(5,2),
    weight_unit VARCHAR DEFAULT 'lbs',
    body_fat_pct DECIMAL(4,2),              -- Body fat percentage

    -- Circumference measurements (inches or cm)
    neck DECIMAL(4,2),
    shoulders DECIMAL(5,2),
    chest DECIMAL(5,2),
    waist DECIMAL(5,2),
    hips DECIMAL(5,2),

    bicep_left DECIMAL(4,2),
    bicep_right DECIMAL(4,2),
    forearm_left DECIMAL(4,2),
    forearm_right DECIMAL(4,2),

    thigh_left DECIMAL(5,2),
    thigh_right DECIMAL(5,2),
    calf_left DECIMAL(4,2),
    calf_right DECIMAL(4,2),

    measurement_unit VARCHAR DEFAULT 'in',  -- in or cm
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_body_measurements_date ON body_measurements(date DESC);

-- ============================================================================
-- SETTINGS & CONFIGURATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR PRIMARY KEY,
    value VARCHAR NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default settings
INSERT OR IGNORE INTO settings (key, value, description) VALUES
    ('default_weight_unit', 'lbs', 'Default weight unit (lbs or kg)'),
    ('default_measurement_unit', 'in', 'Default measurement unit for body (in or cm)'),
    ('enable_rpe', 'true', 'Enable RPE tracking'),
    ('enable_tempo', 'false', 'Enable tempo tracking'),
    ('rest_timer_default', '90', 'Default rest timer in seconds'),
    ('auto_detect_pr', 'true', 'Automatically detect and save personal records'),
    ('database_path', '~/.lift/lift.duckdb', 'Path to database file');

-- ============================================================================
-- ANALYTICAL VIEWS
-- ============================================================================

-- View: Total volume per workout
CREATE OR REPLACE VIEW workout_volume AS
SELECT
    w.id as workout_id,
    w.date,
    w.name as workout_name,
    COUNT(DISTINCT s.exercise_id) as exercise_count,
    COUNT(s.id) as total_sets,
    SUM(s.weight * s.reps) as total_volume,
    AVG(s.rpe) as avg_rpe,
    w.duration_minutes
FROM workouts w
JOIN sets s ON w.id = s.workout_id
WHERE s.set_type IN ('working', 'dropset', 'failure', 'amrap')
GROUP BY w.id, w.date, w.name, w.duration_minutes
ORDER BY w.date DESC;

-- View: Volume per muscle group per week
CREATE OR REPLACE VIEW weekly_muscle_volume AS
SELECT
    date_trunc('week', w.date) as week_start,
    e.primary_muscle,
    COUNT(DISTINCT w.id) as workout_count,
    COUNT(s.id) as total_sets,
    SUM(s.weight * s.reps) as total_volume,
    AVG(s.rpe) as avg_rpe
FROM workouts w
JOIN sets s ON w.id = s.workout_id
JOIN exercises e ON s.exercise_id = e.id
WHERE s.set_type IN ('working', 'dropset', 'failure', 'amrap')
GROUP BY date_trunc('week', w.date), e.primary_muscle
ORDER BY week_start DESC, total_volume DESC;

-- View: Exercise progression (last 10 workouts per exercise)
CREATE OR REPLACE VIEW exercise_progression AS
SELECT
    e.id as exercise_id,
    e.name as exercise_name,
    w.date as workout_date,
    s.set_number,
    s.weight,
    s.weight_unit,
    s.reps,
    s.rpe,
    s.weight * s.reps as volume,
    -- Calculate estimated 1RM using Epley formula
    CASE
        WHEN s.reps = 1 THEN s.weight
        ELSE s.weight * (1 + s.reps / 30.0)
    END as estimated_1rm
FROM sets s
JOIN exercises e ON s.exercise_id = e.id
JOIN workouts w ON s.workout_id = w.id
WHERE s.set_type IN ('working', 'dropset', 'failure', 'amrap')
ORDER BY e.id, w.date DESC, s.set_number;

-- View: Personal records summary
CREATE OR REPLACE VIEW pr_summary AS
SELECT
    e.name as exercise_name,
    pr.record_type,
    pr.value,
    pr.reps,
    pr.weight,
    pr.weight_unit,
    pr.date,
    DATEDIFF('day', pr.date, CURRENT_TIMESTAMP) as days_since
FROM personal_records pr
JOIN exercises e ON pr.exercise_id = e.id
ORDER BY e.name, pr.record_type, pr.date DESC;

-- View: Training frequency (sessions per week, last 12 weeks)
CREATE OR REPLACE VIEW training_frequency AS
SELECT
    date_trunc('week', date) as week_start,
    COUNT(*) as workout_count,
    SUM(duration_minutes) as total_minutes,
    AVG(duration_minutes) as avg_duration
FROM workouts
WHERE date >= CURRENT_TIMESTAMP - INTERVAL '12 weeks'
GROUP BY date_trunc('week', date)
ORDER BY week_start DESC;

-- View: Body weight trend (weekly average)
CREATE OR REPLACE VIEW bodyweight_trend AS
SELECT
    date_trunc('week', date) as week_start,
    AVG(weight) as avg_weight,
    MIN(weight) as min_weight,
    MAX(weight) as max_weight,
    weight_unit
FROM body_measurements
WHERE weight IS NOT NULL
GROUP BY date_trunc('week', date), weight_unit
ORDER BY week_start DESC;
