# Program Design Guide

Training programs provide structure and progression to your workouts. This guide covers how to use built-in programs, create custom programs, and track your progress through them.

## What is a Training Program?

A training program is a structured plan that defines:

- **Training split**: How you divide muscle groups across the week
- **Workout templates**: Specific workouts with exercises, sets, and reps
- **Progression scheme**: How to progress over time
- **Duration**: How long to follow the program

Programs help you:
- Stay consistent with exercise selection
- Follow proven training principles
- Track progress against specific benchmarks
- Avoid decision fatigue during workouts

## Understanding Training Splits

### Available Split Types

Lift supports several popular training splits:

#### PPL (Push/Pull/Legs)
- **Days**: Typically 6 days/week (or 3 days with lower frequency)
- **Division**:
  - Push: Chest, shoulders, triceps
  - Pull: Back, biceps
  - Legs: Quads, hamstrings, glutes, calves
- **Best for**: High frequency, muscle building focus

#### Upper/Lower
- **Days**: Typically 4 days/week
- **Division**:
  - Upper: All upper body muscles
  - Lower: All lower body muscles
- **Best for**: Balanced development, moderate frequency

#### Full Body
- **Days**: 3 days/week
- **Division**: All muscle groups each workout
- **Best for**: Beginners, strength focus, time efficiency

#### Bro Split
- **Days**: 5 days/week
- **Division**: One muscle group per day (chest, back, shoulders, arms, legs)
- **Best for**: Advanced lifters, bodybuilding focus

#### Arnold Split
- **Days**: 6 days/week
- **Division**: Chest/Back, Shoulders/Arms, Legs (repeated twice)
- **Best for**: High volume, advanced bodybuilding

#### Custom
- **Days**: Variable
- **Division**: Your own design
- **Best for**: Specific goals, unique constraints

## Using Built-In Programs

Lift comes with several pre-made programs designed by fitness professionals.

### Viewing Available Programs

```bash
lift program list
```

This shows all available programs with:
- Name and description
- Split type
- Days per week
- Duration

### Viewing Program Details

To see the full program structure with all workouts and exercises:

```bash
lift program show "PPL 6-Day"
```

This displays:
- Complete workout list
- Exercises for each workout
- Target sets, reps, and RPE
- Rest periods
- Estimated duration

### Starting a Program

```bash
lift program start "PPL 6-Day"
```

This activates the program and you can now track your workouts against it.

### Tracking Program Progress

Check your progress through the program:

```bash
lift program progress
```

This shows:
- Which workouts you've completed
- Current week in the program
- Completion percentage
- Next scheduled workout

### Completing Program Workouts

When you log a workout, you can associate it with your active program:

```bash
lift workout start "Push A (Chest Focus)"
```

The workout will be automatically linked to your program if the name matches.

## Creating Custom Programs

If the built-in programs don't meet your needs, create your own!

### Interactive Program Creation

```bash
lift program create
```

This guides you through:
1. Program details (name, split type, days/week, duration)
2. Adding workouts
3. Adding exercises to each workout
4. Setting targets (sets, reps, RPE, rest)

### Step-by-Step Example

Let's create a simple 4-day upper/lower program.

#### Step 1: Start Creation

```bash
$ lift program create

Create New Training Program

Program name: My Upper/Lower Split

Split types:
  1. PPL
  2. Upper/Lower
  3. Full Body
  4. Bro Split
  5. Arnold Split
  6. Custom

Select split type: 2

Days per week: 4

Description (optional): Custom upper/lower split for strength and hypertrophy

Duration in weeks (optional): 8

✓ Program My Upper/Lower Split created!
```

#### Step 2: Add First Workout

```
Add workouts? Yes

Workout 1
Workout name: Upper Power

Day number (1-7, optional): 1

Description (optional): Heavy compound movements for upper body

Estimated duration (minutes) (optional): 60

✓ Workout Upper Power added!
```

#### Step 3: Add Exercises to Workout

```
Add exercises? Yes

Exercise 1
Exercise name: Barbell Bench Press
Sets: 4
Reps (e.g., 8-10 or just 10): 5-6
RPE (optional): 8.5
Rest seconds (optional): 180

✓ Exercise added!

Exercise 2
Exercise name: Barbell Rows
Sets: 4
Reps: 5-6
RPE: 8.5
Rest seconds: 180

✓ Exercise added!

Exercise 3
Exercise name: Overhead Press
Sets: 3
Reps: 6-8
RPE: 8
Rest seconds: 120

✓ Exercise added!

Exercise 4
Exercise name: Pull-Ups
Sets: 3
Reps: 8-10
RPE: 8
Rest seconds: 120

✓ Exercise added!

Exercise 5
Exercise name (or 'done' to finish): done
```

#### Step 4: Continue Adding Workouts

Repeat for:
- Workout 2: Lower Power
- Workout 3: Upper Hypertrophy
- Workout 4: Lower Hypertrophy

#### Step 5: Review

Once complete, the program is saved and ready to use!

```bash
lift program show "My Upper/Lower Split"
```

## Program Design Principles

### Exercise Selection

**Compound Movements First**
- Start workouts with multi-joint exercises
- Examples: squats, deadlifts, bench press, rows
- These build the most strength and muscle

**Isolation Movements Last**
- End with single-joint exercises
- Examples: curls, extensions, raises
- These target specific muscles for detail

**Balance Push and Pull**
- Maintain roughly equal push/pull volume
- Prevents muscle imbalances and injuries
- Promotes shoulder health

### Volume and Intensity

**Sets Per Week (Per Muscle Group)**
- Beginners: 10-15 sets/week
- Intermediate: 15-20 sets/week
- Advanced: 20-25+ sets/week

**Rep Ranges**
- Strength: 1-5 reps @ RPE 8-10
- Hypertrophy: 6-12 reps @ RPE 7-9
- Endurance: 12-20 reps @ RPE 6-8

**RPE (Rate of Perceived Exertion)**
- Use RPE 6-8 for most work sets
- Save RPE 9-10 for peak weeks or testing
- Allows for autoregulation based on recovery

### Rest Periods

- **Heavy compounds (1-6 reps)**: 3-5 minutes
- **Moderate compounds (6-12 reps)**: 2-3 minutes
- **Isolation (12+ reps)**: 1-2 minutes
- **Supersets/circuits**: 0-1 minute between exercises

### Progressive Overload

Plan for progression:

1. **Add reps**: Increase reps within target range
2. **Add weight**: Once hitting top of rep range
3. **Add sets**: Increase volume over mesocycle
4. **Reduce rest**: Advanced technique for conditioning

## Example Program Templates

### Beginner Full Body (3 Days/Week)

**Program Details:**
- Split: Full Body
- Days: 3/week (M/W/F)
- Duration: 8-12 weeks

**Workout A:**
```
1. Squat: 3x8-10 @ RPE 7-8
2. Bench Press: 3x8-10 @ RPE 7-8
3. Barbell Rows: 3x8-10 @ RPE 7-8
4. Overhead Press: 2x10-12 @ RPE 7
5. Romanian Deadlift: 2x10-12 @ RPE 7
6. Lat Pulldown: 2x10-12 @ RPE 7
```

**Workout B:**
```
1. Deadlift: 3x6-8 @ RPE 8
2. Overhead Press: 3x8-10 @ RPE 7-8
3. Lat Pulldown: 3x8-10 @ RPE 7-8
4. Leg Press: 3x10-12 @ RPE 7-8
5. Incline Dumbbell Press: 2x10-12 @ RPE 7
6. Cable Rows: 2x10-12 @ RPE 7
```

Alternate A/B each workout (Week 1: A/B/A, Week 2: B/A/B)

### Intermediate Upper/Lower (4 Days/Week)

**Program Details:**
- Split: Upper/Lower
- Days: 4/week (M/T/Th/F or M/T/Th/Sa)
- Duration: 8-12 weeks

**Upper 1 (Power):**
```
1. Bench Press: 4x5-6 @ RPE 8-9
2. Barbell Rows: 4x5-6 @ RPE 8-9
3. Overhead Press: 3x6-8 @ RPE 8
4. Pull-Ups: 3x6-8 @ RPE 8
5. Incline Dumbbell Press: 3x8-10 @ RPE 7-8
6. Face Pulls: 3x15-20 @ RPE 7
```

**Lower 1 (Power):**
```
1. Squat: 4x5-6 @ RPE 8-9
2. Romanian Deadlift: 4x6-8 @ RPE 8
3. Leg Press: 3x8-10 @ RPE 8
4. Leg Curl: 3x10-12 @ RPE 7-8
5. Standing Calf Raise: 4x12-15 @ RPE 8
```

**Upper 2 (Hypertrophy):**
```
1. Incline Barbell Press: 4x8-10 @ RPE 8
2. Cable Rows: 4x10-12 @ RPE 8
3. Dumbbell Shoulder Press: 3x10-12 @ RPE 7-8
4. Lat Pulldown: 3x10-12 @ RPE 7-8
5. Cable Flyes: 3x12-15 @ RPE 7-8
6. Dumbbell Curls: 3x12-15 @ RPE 7-8
7. Tricep Extensions: 3x12-15 @ RPE 7-8
```

**Lower 2 (Hypertrophy):**
```
1. Front Squat: 4x8-10 @ RPE 8
2. Deadlift: 3x6-8 @ RPE 8
3. Bulgarian Split Squat: 3x10-12/leg @ RPE 8
4. Leg Extension: 3x12-15 @ RPE 7-8
5. Leg Curl: 3x12-15 @ RPE 7-8
6. Seated Calf Raise: 4x15-20 @ RPE 8
```

## Managing Programs

### Switching Programs

To stop your current program and start a different one:

```bash
lift program stop
lift program start "New Program Name"
```

### Deleting Custom Programs

Remove a program you created:

```bash
lift program delete "My Custom Program"
```

**Note:** Built-in programs cannot be deleted.

### Modifying Programs

Currently, programs cannot be edited after creation. To modify:

1. Delete the old program: `lift program delete "Program Name"`
2. Recreate it with changes: `lift program create`

**Tip:** Keep notes on your program structure before deleting for easier recreation.

## Advanced Topics

### Periodization

Structure your program in phases:

**Accumulation (Weeks 1-4)**
- Higher volume, moderate intensity
- RPE 7-8
- Build work capacity

**Intensification (Weeks 5-8)**
- Moderate volume, higher intensity
- RPE 8-9
- Build strength

**Realization (Weeks 9-10)**
- Lower volume, peak intensity
- RPE 9-10
- Peak performance

**Deload (Week 11)**
- Low volume, low intensity
- RPE 6-7
- Recovery

### Deload Weeks

Every 4-6 weeks, program a deload:
- Reduce volume by 40-50%
- Reduce intensity by 10-20%
- Maintain movement patterns
- Promote recovery

### Exercise Substitutions

If you need to substitute an exercise:

1. Match the movement pattern
2. Match the load type (barbell → barbell, cable → cable)
3. Match the target muscle group
4. Maintain similar rep ranges

**Example Substitutions:**
- Barbell Bench → Dumbbell Bench
- Pull-Ups → Lat Pulldown
- Back Squat → Front Squat
- Deadlift → Trap Bar Deadlift

### Auto-Regulation

Use RPE for auto-regulation:

**Feeling Strong?**
- Hit top of rep range
- Consider adding weight
- Push RPE up slightly

**Feeling Fatigued?**
- Hit bottom of rep range
- Maintain weight
- Keep RPE in check
- Don't grind every rep

## Tips for Success

1. **Follow the program**: Don't change exercises every week
2. **Track consistently**: Log every workout to see patterns
3. **Progressive overload**: Always aim to beat previous performance
4. **Deload when needed**: Recovery is part of progress
5. **Adjust based on recovery**: Use RPE to manage fatigue
6. **Give it time**: Programs take 6-12 weeks to show results

## Common Mistakes

### Too Much Volume
- Starting with advanced programs
- Adding extra exercises "just in case"
- **Fix:** Start conservative, add volume gradually

### Too Much Intensity
- Going to failure every set
- Always using RPE 9-10
- **Fix:** Save max efforts for key lifts, use RPE 7-8 for most work

### Inconsistent Execution
- Skipping workouts
- Changing exercises frequently
- **Fix:** Commit to the program, trust the process

### No Progression Plan
- Using same weight every workout
- Not tracking performance
- **Fix:** Add reps or weight every week, review lift stats regularly

## Quick Reference

| Task | Command |
|------|---------|
| List available programs | `lift program list` |
| View program details | `lift program show "Name"` |
| Start a program | `lift program start "Name"` |
| View progress | `lift program progress` |
| Create custom program | `lift program create` |
| Stop active program | `lift program stop` |
| Delete custom program | `lift program delete "Name"` |

## Next Steps

- Start with a built-in program matching your experience level
- Track your workouts consistently
- Review progress every 4 weeks
- Adjust based on results and recovery
- Create custom programs once you understand principles

Happy programming! 💪
