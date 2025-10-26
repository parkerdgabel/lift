# Creating Custom Exercises

Lift comes with a comprehensive built-in exercise library, but you may want to add your own variations or specialized movements. This guide shows you how to create, manage, and use custom exercises.

## Why Create Custom Exercises?

Custom exercises are useful for:

- **Equipment variations** (e.g., "Hammer Strength Chest Press" instead of generic machine press)
- **Specialized movements** specific to your training style or needs
- **Hybrid exercises** you've developed or learned from a coach
- **Sport-specific movements** not in the standard library
- **Personal exercise names** that match your gym's equipment

## Understanding Exercise Properties

Before creating a custom exercise, it's helpful to understand the properties you'll need to define:

### Category (Required)

The training category determines workout organization:

- **Push**: Exercises that push weight away (chest, shoulders, triceps)
- **Pull**: Exercises that pull weight toward you (back, biceps)
- **Legs**: Lower body exercises (quads, hamstrings, glutes, calves)
- **Core**: Trunk stability and abdominal work

### Primary Muscle (Required)

The main muscle group targeted. Options include:

**Upper Body:**
- Chest
- Back
- Shoulders
- Biceps
- Triceps
- Forearms

**Lower Body:**
- Quads
- Hamstrings
- Glutes
- Calves

**Core:**
- Abs
- Obliques
- Lower Back

### Secondary Muscles (Optional)

Supporting muscle groups that assist in the movement. You can specify multiple secondary muscles separated by commas.

**Example:** Barbell Bench Press
- Primary: Chest
- Secondary: Triceps, Shoulders

### Equipment (Required)

The equipment required for the exercise:

- Barbell
- Dumbbell
- Cable
- Machine
- Bodyweight
- Resistance Band
- Kettlebell
- EZ Bar
- Trap Bar
- Smith Machine

### Movement Type (Required)

Classification of the exercise complexity:

- **Compound**: Multi-joint movements that work multiple muscle groups (e.g., squats, deadlifts, bench press)
- **Isolation**: Single-joint movements targeting one specific muscle group (e.g., bicep curls, leg extensions)

### Instructions (Optional)

Step-by-step execution guidance. Useful for remembering proper form or technique cues.

### Video URL (Optional)

A link to a form tutorial or demonstration video.

## Creating a Custom Exercise

### Interactive Method

The easiest way to create a custom exercise is through the interactive command:

```bash
lift exercise add
```

This will guide you through each property with prompts:

#### Example: Creating "Hammer Strength Incline Press"

```bash
$ lift exercise add

Exercise name: Hammer Strength Incline Press

Category options: Push, Pull, Legs, Core
Category: Push

Muscle options:
Chest, Back, Shoulders, Biceps, Triceps, Forearms, Quads, Hamstrings, Glutes, Calves, Abs, Obliques, Lower Back
Primary muscle: Chest

Secondary muscles (comma-separated, or press Enter to skip): Triceps, Shoulders

Equipment options:
Barbell, Dumbbell, Cable, Machine, Bodyweight, Resistance Band, Kettlebell, EZ Bar, Trap Bar, Smith Machine
Equipment: Machine

Movement type options: Compound, Isolation
Movement type: Compound

Instructions (or press Enter to skip):
1. Adjust seat height so handles align with mid-chest
2. Press handles up and slightly forward
3. Control descent, stop when elbows reach 90 degrees
4. Maintain shoulder blade retraction throughout

Video URL (or press Enter to skip): https://www.youtube.com/watch?v=example

Successfully created custom exercise!
Name: Hammer Strength Incline Press
ID: 147
```

### Verification

After creating the exercise, verify it was added correctly:

```bash
lift exercise info "Hammer Strength Incline Press"
```

This displays all the exercise details including your custom properties.

## Using Custom Exercises in Workouts

Custom exercises work exactly like built-in exercises once created.

### Finding Your Exercise ID

```bash
lift exercise search "Hammer"
```

This shows your custom exercise with its ID number.

### Logging Sets

Use the exercise ID when logging workouts:

```bash
lift workout log --quick --exercise-id 147
```

Or select it during interactive workout logging:

```bash
lift workout log
# Then search for "Hammer" when prompted for exercise
```

## Managing Custom Exercises

### Listing Custom Exercises

To see only your custom exercises, you can search or filter:

```bash
lift exercise list
```

Custom exercises are marked in the output.

### Viewing Exercise Details

```bash
lift exercise info "Your Exercise Name"
```

Shows complete information including all properties and whether it's custom.

### Deleting Custom Exercises

Only custom exercises can be deleted (built-in exercises are protected):

```bash
lift exercise delete "Hammer Strength Incline Press"
```

You'll be prompted for confirmation. To skip the prompt:

```bash
lift exercise delete "Hammer Strength Incline Press" --force
```

**Warning:** Deleting an exercise does not delete historical workout data that used it. Past sets remain in the database for tracking purposes.

## Best Practices

### Naming Conventions

- **Be specific**: "Hammer Strength Incline Press" instead of just "Incline Press"
- **Include equipment**: "Cable Lateral Raise" vs "Lateral Raise"
- **Use standard terminology**: Makes exercises easier to find and remember
- **Avoid special characters**: Stick to letters, numbers, spaces, and basic punctuation

### Categorization Tips

1. **Choose the right category**:
   - Incline press → Push
   - Cable rows → Pull
   - Leg press → Legs
   - Pallof press → Core

2. **Primary vs Secondary muscles**:
   - Primary = the main target muscle
   - Secondary = significant contributors
   - Don't list every muscle that activates slightly

3. **Movement type**:
   - If it crosses multiple joints → Compound
   - If it crosses one joint → Isolation
   - When in doubt, look at similar built-in exercises

### Documentation

For exercises you create, consider adding:

- **Instructions**: Especially for unique or complex movements
- **Video URL**: Links to form videos help maintain consistency
- **Equipment notes**: Specific machine settings or setup requirements

## Real-World Examples

### Example 1: Specialty Bar Variation

```
Name: Swiss Bar Floor Press
Category: Push
Primary Muscle: Chest
Secondary Muscles: Triceps
Equipment: Barbell (or add "Specialty Bar" if needed)
Movement Type: Compound
Instructions:
- Lie on floor (not bench)
- Use neutral grip on swiss bar
- Lower until elbows touch floor
- Press up to lockout
```

### Example 2: Bodyweight Variation

```
Name: Deficit Push-Ups
Category: Push
Primary Muscle: Chest
Secondary Muscles: Triceps, Shoulders
Equipment: Bodyweight
Movement Type: Compound
Instructions:
- Hands on elevated platforms (4-6 inches)
- Increase range of motion below chest
- Maintain straight body line
```

### Example 3: Machine Specific

```
Name: Cybex Arc Trainer
Category: Legs
Primary Muscle: Quads
Secondary Muscles: Hamstrings, Glutes
Equipment: Machine
Movement Type: Compound
Instructions: Cardio warm-up or conditioning work
```

### Example 4: Cable Variation

```
Name: Single Arm Low-to-High Cable Fly
Category: Push
Primary Muscle: Chest
Secondary Muscles: Shoulders
Equipment: Cable
Movement Type: Isolation
Instructions:
- Start with cable at lowest setting
- Pull across body from low to high
- Focus on upper chest contraction
```

## Common Issues

### "Exercise already exists"

If you try to create an exercise with a name that's already taken:

1. Search for the existing exercise: `lift exercise search "name"`
2. Use `lift exercise info "exact name"` to see if it matches your needs
3. If it's different, choose a more specific name (e.g., add equipment brand or grip variation)

### Wrong Category or Muscle Group

If you make a mistake during creation:

1. Delete the custom exercise: `lift exercise delete "name"`
2. Re-create it with correct properties

Unfortunately, you cannot edit existing exercises (this is a protection against accidentally modifying built-in exercises).

### Finding Exercise IDs

To quickly find an exercise ID for quick logging:

```bash
lift exercise search "partial name" | grep "ID"
```

Or search and note the ID from the table output.

## Advanced Topics

### Tracking Variations Separately

If you perform an exercise with different equipment or grips, you might want separate tracking:

**Example:** You do both:
- Barbell Bench Press (built-in)
- Dumbbell Bench Press (built-in)
- Hammer Strength Chest Press (custom)

Create the custom variation so you can track progression independently for each.

### Exercise Substitutions

When following a program that calls for equipment you don't have:

1. Find the closest equivalent in the built-in library, or
2. Create a custom exercise matching your available equipment
3. Use it consistently to track progression

### Importing Exercises

Currently, Lift doesn't support bulk import of exercises from a file. Each custom exercise must be created individually through the CLI.

If you need many custom exercises, consider:

1. Creating them as you need them during workouts
2. Setting aside time to add several at once
3. Using a script to automate creation (advanced users can interact with the database directly)

## Next Steps

Now that you can create custom exercises, you might want to:

- [Design Custom Programs](./program-design.md) using your exercises
- Learn about [Advanced Stats and Tracking](../user-guide/stats.md) (coming soon)
- Explore the [Data Model](../data-model.md) to understand how exercises are stored

## Quick Reference

| Task | Command |
|------|---------|
| Create custom exercise | `lift exercise add` |
| List all exercises | `lift exercise list` |
| Search exercises | `lift exercise search "query"` |
| View exercise details | `lift exercise info "Name"` |
| Delete custom exercise | `lift exercise delete "Name"` |
| Force delete (no prompt) | `lift exercise delete "Name" --force` |
| Filter by category | `lift exercise list --category Push` |
| Filter by muscle | `lift exercise list --muscle Chest` |
| Filter by equipment | `lift exercise list --equipment Dumbbell` |
| Show summary stats | `lift exercise list --summary` |

Happy training! 💪
