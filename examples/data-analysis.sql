-- Lift Data Analysis Queries
-- Custom SQL queries for advanced analysis
-- Run these with: duckdb ~/.lift/lift.db < query.sql
-- Or interactively: duckdb ~/.lift/lift.db

-- =============================================================================
-- VOLUME ANALYSIS
-- =============================================================================

-- Total volume by exercise (all time)
SELECT
    e.name,
    e.category,
    e.primary_muscle,
    COUNT(DISTINCT s.workout_id) as workouts,
    COUNT(s.id) as total_sets,
    SUM(s.weight * s.reps) as total_volume,
    AVG(s.weight) as avg_weight,
    AVG(s.reps) as avg_reps
FROM sets s
JOIN exercises e ON s.exercise_id = e.id
WHERE s.set_type = 'working'
GROUP BY e.name, e.category, e.primary_muscle
ORDER BY total_volume DESC
LIMIT 20;

-- Volume by muscle group per month
SELECT
    date_trunc('month', w.date) as month,
    e.primary_muscle,
    COUNT(DISTINCT w.id) as workouts,
    COUNT(s.id) as sets,
    SUM(s.weight * s.reps) as volume
FROM workouts w
JOIN sets s ON w.id = s.workout_id
JOIN exercises e ON s.exercise_id = e.id
WHERE s.set_type = 'working'
  AND w.date >= current_timestamp - interval '12 months'
GROUP BY date_trunc('month', w.date), e.primary_muscle
ORDER BY month DESC, volume DESC;

-- Weekly volume trend
SELECT
    date_trunc('week', w.date) as week,
    COUNT(DISTINCT w.id) as workouts,
    COUNT(s.id) as total_sets,
    SUM(s.weight * s.reps) as total_volume,
    AVG(s.rpe) as avg_rpe,
    SUM(w.duration_minutes) as total_minutes
FROM workouts w
JOIN sets s ON w.id = s.workout_id
WHERE s.set_type = 'working'
  AND w.date >= current_timestamp - interval '26 weeks'
GROUP BY date_trunc('week', w.date)
ORDER BY week DESC;

-- =============================================================================
-- PROGRESSION ANALYSIS
-- =============================================================================

-- Best set ever for each exercise (by volume)
SELECT
    e.name,
    MAX(s.weight * s.reps) as best_volume,
    s.weight as weight_used,
    s.reps as reps_performed,
    w.date as achieved_date
FROM sets s
JOIN exercises e ON s.exercise_id = e.id
JOIN workouts w ON s.workout_id = w.id
WHERE s.set_type = 'working'
GROUP BY e.name, s.weight, s.reps, w.date
HAVING s.weight * s.reps = MAX(s.weight * s.reps)
ORDER BY best_volume DESC
LIMIT 20;

-- Progression on specific exercise (Bench Press example)
SELECT
    w.date,
    s.set_number,
    s.weight,
    s.reps,
    s.weight * s.reps as volume,
    CASE
        WHEN s.reps = 1 THEN s.weight
        ELSE s.weight * (1 + s.reps / 30.0)
    END as estimated_1rm
FROM sets s
JOIN workouts w ON s.workout_id = w.id
JOIN exercises e ON s.exercise_id = e.id
WHERE e.name = 'Barbell Bench Press'
  AND s.set_type = 'working'
ORDER BY w.date DESC, s.set_number
LIMIT 50;

-- Monthly PR count (how many PRs set each month)
SELECT
    date_trunc('month', date) as month,
    record_type,
    COUNT(*) as pr_count
FROM personal_records
WHERE date >= current_timestamp - interval '12 months'
GROUP BY date_trunc('month', date), record_type
ORDER BY month DESC, pr_count DESC;

-- =============================================================================
-- FREQUENCY ANALYSIS
-- =============================================================================

-- Training frequency by day of week
SELECT
    DAYNAME(date) as day_of_week,
    COUNT(*) as workout_count,
    AVG(duration_minutes) as avg_duration,
    SUM(duration_minutes) as total_minutes
FROM workouts
WHERE date >= current_timestamp - interval '12 weeks'
GROUP BY DAYNAME(date)
ORDER BY workout_count DESC;

-- Exercise frequency (how often you do each exercise)
SELECT
    e.name,
    COUNT(DISTINCT w.id) as times_performed,
    MIN(w.date) as first_time,
    MAX(w.date) as last_time,
    DATEDIFF('day', MIN(w.date), MAX(w.date)) as days_span,
    CAST(COUNT(DISTINCT w.id) AS FLOAT) / DATEDIFF('week', MIN(w.date), MAX(w.date)) as times_per_week
FROM sets s
JOIN workouts w ON s.workout_id = w.id
JOIN exercises e ON s.exercise_id = e.id
GROUP BY e.name
HAVING times_performed >= 5
ORDER BY times_performed DESC;

-- Workout consistency (streaks and gaps)
SELECT
    date,
    name,
    LAG(date) OVER (ORDER BY date) as previous_workout,
    DATEDIFF('day', LAG(date) OVER (ORDER BY date), date) as days_since_last
FROM workouts
ORDER BY date DESC
LIMIT 30;

-- =============================================================================
-- RPE ANALYSIS
-- =============================================================================

-- Average RPE by exercise
SELECT
    e.name,
    COUNT(s.id) as sets_tracked,
    AVG(s.rpe) as avg_rpe,
    MIN(s.rpe) as min_rpe,
    MAX(s.rpe) as max_rpe,
    STDDEV(s.rpe) as rpe_variance
FROM sets s
JOIN exercises e ON s.exercise_id = e.id
WHERE s.rpe IS NOT NULL
GROUP BY e.name
HAVING COUNT(s.id) >= 10
ORDER BY avg_rpe DESC;

-- RPE trend over time (check if getting better at same weights)
SELECT
    date_trunc('week', w.date) as week,
    AVG(s.rpe) as avg_rpe,
    AVG(s.weight) as avg_weight,
    AVG(s.weight) / AVG(s.rpe) as weight_per_rpe_point
FROM sets s
JOIN workouts w ON s.workout_id = w.id
WHERE s.rpe IS NOT NULL
  AND s.set_type = 'working'
  AND w.date >= current_timestamp - interval '26 weeks'
GROUP BY date_trunc('week', w.date)
ORDER BY week DESC;

-- =============================================================================
-- BODY COMPOSITION
-- =============================================================================

-- Bodyweight trend with calculated lean mass
SELECT
    date,
    weight,
    weight_unit,
    body_fat_pct,
    CASE
        WHEN body_fat_pct IS NOT NULL
        THEN weight * (1 - body_fat_pct / 100.0)
        ELSE NULL
    END as lean_mass,
    CASE
        WHEN body_fat_pct IS NOT NULL
        THEN weight * (body_fat_pct / 100.0)
        ELSE NULL
    END as fat_mass
FROM body_measurements
WHERE weight IS NOT NULL
ORDER BY date DESC
LIMIT 50;

-- Measurement correlations (does chest grow with bench strength?)
SELECT
    bm.date as measurement_date,
    bm.chest,
    bm.bicep_left,
    bm.waist,
    (
        SELECT MAX(s.weight)
        FROM sets s
        JOIN exercises e ON s.exercise_id = e.id
        JOIN workouts w ON s.workout_id = w.id
        WHERE e.name = 'Barbell Bench Press'
          AND w.date <= bm.date
          AND s.set_type = 'working'
    ) as bench_max_weight
FROM body_measurements bm
WHERE chest IS NOT NULL
ORDER BY measurement_date DESC;

-- Body measurement trends (month over month)
SELECT
    date_trunc('month', date) as month,
    AVG(weight) as avg_weight,
    AVG(body_fat_pct) as avg_bf,
    AVG(chest) as avg_chest,
    AVG(waist) as avg_waist,
    AVG((bicep_left + bicep_right) / 2.0) as avg_bicep,
    AVG((thigh_left + thigh_right) / 2.0) as avg_thigh
FROM body_measurements
WHERE date >= current_timestamp - interval '12 months'
GROUP BY date_trunc('month', date)
ORDER BY month DESC;

-- =============================================================================
-- CUSTOM INSIGHTS
-- =============================================================================

-- Find your "money exercises" (best ROI on time invested)
SELECT
    e.name,
    COUNT(DISTINCT w.id) as workouts,
    SUM(w.duration_minutes) / COUNT(DISTINCT w.id) as avg_workout_duration,
    COUNT(s.id) as total_sets,
    SUM(s.weight * s.reps) as total_volume,
    (SUM(s.weight * s.reps) / SUM(w.duration_minutes)) as volume_per_minute
FROM sets s
JOIN exercises e ON s.exercise_id = e.id
JOIN workouts w ON s.workout_id = w.id
WHERE s.set_type = 'working'
GROUP BY e.name
HAVING COUNT(DISTINCT w.id) >= 10
ORDER BY volume_per_minute DESC
LIMIT 10;

-- Identify plateau exercises (no progress in 4+ weeks)
WITH recent_maxes AS (
    SELECT
        e.id as exercise_id,
        e.name,
        MAX(s.weight * s.reps) as recent_max_volume,
        MAX(w.date) as recent_max_date
    FROM sets s
    JOIN exercises e ON s.exercise_id = e.id
    JOIN workouts w ON s.workout_id = w.id
    WHERE w.date >= current_timestamp - interval '4 weeks'
      AND s.set_type = 'working'
    GROUP BY e.id, e.name
),
historical_maxes AS (
    SELECT
        e.id as exercise_id,
        MAX(s.weight * s.reps) as historical_max_volume,
        MAX(w.date) as historical_max_date
    FROM sets s
    JOIN exercises e ON s.exercise_id = e.id
    JOIN workouts w ON s.workout_id = w.id
    WHERE w.date < current_timestamp - interval '4 weeks'
      AND s.set_type = 'working'
    GROUP BY e.id
)
SELECT
    r.name,
    r.recent_max_volume,
    h.historical_max_volume,
    r.recent_max_volume - h.historical_max_volume as volume_change,
    ((r.recent_max_volume - h.historical_max_volume) / h.historical_max_volume) * 100 as pct_change
FROM recent_maxes r
JOIN historical_maxes h ON r.exercise_id = h.exercise_id
WHERE r.recent_max_volume <= h.historical_max_volume * 1.05  -- Less than 5% improvement
ORDER BY pct_change;

-- Compare your best and worst workout days
SELECT
    DAYNAME(date) as day_of_week,
    COUNT(*) as workout_count,
    AVG(rating) as avg_rating,
    AVG(duration_minutes) as avg_duration,
    SUM(volume.total_volume) / COUNT(*) as avg_volume
FROM workouts w
LEFT JOIN (
    SELECT
        workout_id,
        SUM(weight * reps) as total_volume
    FROM sets
    WHERE set_type = 'working'
    GROUP BY workout_id
) volume ON w.id = volume.workout_id
WHERE rating IS NOT NULL
GROUP BY DAYNAME(date)
ORDER BY avg_rating DESC;

-- =============================================================================
-- EXPORT QUERIES
-- =============================================================================

-- Export all workout data to CSV
-- Uncomment to run:
-- COPY (
--     SELECT
--         w.id as workout_id,
--         w.date,
--         w.name as workout_name,
--         e.name as exercise_name,
--         s.set_number,
--         s.weight,
--         s.reps,
--         s.rpe,
--         s.set_type
--     FROM workouts w
--     JOIN sets s ON w.id = s.workout_id
--     JOIN exercises e ON s.exercise_id = e.id
--     ORDER BY w.date DESC, s.set_number
-- ) TO 'workout_data_export.csv' (HEADER, DELIMITER ',');

-- Export body measurements to CSV
-- Uncomment to run:
-- COPY body_measurements TO 'body_measurements_export.csv' (HEADER, DELIMITER ',');
