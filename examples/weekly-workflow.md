# Weekly Tracking Workflow

This example shows a complete week of tracking workouts, body measurements, and progress review.

## Weekly Schedule

This example uses a PPL (Push/Pull/Legs) 6-day split:

- **Monday**: Push A (Chest Focus)
- **Tuesday**: Pull A (Back Focus)
- **Wednesday**: Legs A (Quad Focus)
- **Thursday**: Push B (Shoulder Focus)
- **Friday**: Pull B (Bicep Focus)
- **Saturday**: Legs B (Hamstring Focus)
- **Sunday**: Rest

## Monday: Push Day

### Morning Routine

```bash
# Check body weight before workout
lift body weight 186.5

# View last push workout for reference
lift workout last

# Start today's workout
lift workout start "Push A (Chest Focus)"
```

### During Workout

```bash
# Log workout interactively
lift workout log

# Example interaction:
# Exercise: Barbell Bench Press
# Set 1: 135 lbs × 10 (warmup)
# Set 2: 185 lbs × 8 @ RPE 7.5
# Set 3: 205 lbs × 6 @ RPE 8.0
# Set 4: 225 lbs × 5 @ RPE 8.5
# Set 5: 205 lbs × 7 @ RPE 8.0
#
# Continue with: Incline Dumbbell Press, Cable Flyes,
# Overhead Press, Lateral Raises, Tricep Pushdowns
```

### Post-Workout

```bash
# Workout automatically completes when you finish logging
# View today's summary
lift workout last

# Check if you set any PRs
lift stats pr
```

## Tuesday: Pull Day

```bash
# Morning weight check
lift body weight 186.2

# Notice the drop? Track trend
lift body history --limit 7

# Start workout
lift workout start "Pull A (Back Focus)"

# Log sets
lift workout log
# Deadlift, Pull-Ups, Barbell Rows, Face Pulls,
# Hammer Curls, Cable Curls
```

## Wednesday: Leg Day

```bash
# Weight check
lift body weight 187.0

# Start workout
lift workout start "Legs A (Quad Focus)"

# Log heavy squats and accessories
lift workout log
```

## Thursday: Volume Push

```bash
# Weight check
lift body weight 186.8

# Start workout
lift workout start "Push B (Shoulder Focus)"

# Higher volume, moderate intensity
lift workout log
```

## Friday: Volume Pull

```bash
# Weight check
lift body weight 187.2

# Start workout
lift workout start "Pull B (Bicep Focus)"

# Log workout
lift workout log
```

## Saturday: Volume Legs

```bash
# Weight check
lift body weight 186.5

# Start workout
lift workout start "Legs B (Hamstring Focus)"

# Log workout
lift workout log
```

## Sunday: Rest & Review

### Morning Check-In

```bash
# Log rest day weight
lift body weight 186.0

# Full body measurements (weekly)
lift body measure
# This prompts for:
# - Body fat % (if tracking with calipers/scale)
# - Neck, chest, waist, hips
# - Arm, forearm, thigh, calf circumferences
```

### Weekly Review

```bash
# View this week's workouts
lift workout history --limit 7

# Check volume trend
lift stats volume --weeks 4

# Review per-exercise progress
lift stats exercise 1  # Bench Press
lift stats exercise 15 # Squat
lift stats exercise 23 # Deadlift

# Check if maintaining frequency
lift stats streak

# Review body progress
lift body progress --weeks 1
```

### Planning Next Week

```bash
# Check program status (if following a program)
lift program progress

# Identify weak points
lift stats muscle --weeks 4

# Note exercises where progress stalled
lift stats progress 1  # Review bench press trend
# If plateau, plan variation or deload
```

## Weekly Metrics to Track

| Day | Bodyweight | Workout | Volume | Duration | Rating |
|-----|------------|---------|--------|----------|--------|
| Mon | 186.5 | Push A | ~15,000 lbs | 75 min | 5/5 |
| Tue | 186.2 | Pull A | ~12,000 lbs | 70 min | 4/5 |
| Wed | 187.0 | Legs A | ~18,000 lbs | 80 min | 5/5 |
| Thu | 186.8 | Push B | ~14,000 lbs | 65 min | 4/5 |
| Fri | 187.2 | Pull B | ~11,000 lbs | 65 min | 5/5 |
| Sat | 186.5 | Legs B | ~16,000 lbs | 75 min | 4/5 |
| Sun | 186.0 | Rest | - | - | - |

**Weekly Totals:**
- Average Bodyweight: 186.6 lbs
- Total Volume: 86,000 lbs
- Total Training Time: 430 minutes (7.2 hours)
- Workouts Completed: 6/6

## Tips for Consistency

1. **Same time daily**: Track bodyweight at the same time (morning, after bathroom, before food)
2. **Log immediately**: Enter data right after each workout
3. **Weekly review**: Set aside 15-30 minutes every Sunday
4. **Adjust as needed**: If volume is too high/low, adjust next week
5. **Note how you feel**: Use the rating and notes fields

## Adjustments Based on Data

### If Bodyweight Is Dropping

- Increase calories
- Monitor strength - ensure not losing performance
- Consider reducing cardio

### If Bodyweight Is Climbing Too Fast

- Reduce surplus
- Ensure it's muscle not fat (use measurements)
- Check recovery quality

### If Volume Is Too High

- Fatigue accumulating
- Performance dropping
- Consider deload or reduce accessory work

### If Volume Is Too Low

- Not enough stimulus
- Could add sets to weak points
- Verify progressive overload is happening

## Sample Sunday Review Output

```bash
$ lift stats summary

📊 Training Summary (Last 4 Weeks)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Workouts: 24
Total Sets: 312
Total Volume: 344,000 lbs
Avg Duration: 72 minutes

Top Exercises by Volume:
1. Back Squat: 72,000 lbs
2. Deadlift: 54,000 lbs
3. Bench Press: 48,000 lbs

Weekly Frequency:
Week 1: 6 workouts
Week 2: 6 workouts
Week 3: 6 workouts
Week 4: 6 workouts

Current Streak: 4 weeks
```

This weekly workflow ensures you're consistently tracking, reviewing, and adjusting your training for optimal progress!
