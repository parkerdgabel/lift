# Tracking Bulk and Cut Cycles

This guide shows how to use Lift to track your progress through different training phases.

## Overview

Bodybuilding typically involves cycling between:

- **Bulking**: Caloric surplus to build muscle
- **Cutting**: Caloric deficit to lose fat while maintaining muscle
- **Maintenance**: Maintaining current composition

Lift helps you track each phase and analyze what worked best.

## Setting Up a Bulk Phase

### Week 1: Baseline Measurements

```bash
# Initialize with comprehensive measurements
lift body measure

# Prompts for:
# Weight: 175.0 lbs
# Body fat: 12.0%
# ... all circumference measurements

# Calculate lean body mass for reference
# LBM = 175 × (1 - 0.12) = 154 lbs

# Start your bulk program
lift program start "PPL 6-Day Bulk"
```

### Weekly Tracking During Bulk

**Every Monday Morning** (fasted, post-bathroom):

```bash
lift body weight 176.5

# Every 2 weeks, full measurements:
lift body measure
```

**Target Rate of Gain:**
- Beginners: 0.5-1.0% bodyweight/week (0.9-1.75 lbs/week)
- Intermediate: 0.25-0.5% bodyweight/week (0.4-0.9 lbs/week)
- Advanced: 0.1-0.25% bodyweight/week (0.2-0.4 lbs/week)

### Monitoring Progress

```bash
# Weekly weight trend
lift body history --measurement weight --weeks 8

# Check if strength is increasing
lift stats exercise 1   # Bench
lift stats exercise 15  # Squat
lift stats exercise 23  # Deadlift

# Verify volume is progressing
lift stats volume --weeks 8

# Check if measurements growing in right places
lift body progress --weeks 4
```

### Example 12-Week Bulk Data

```
Week | Weight | BF%  | LBM  | Chest | Waist | Arms
-----|--------|------|------|-------|-------|------
1    | 175.0  | 12.0 | 154  | 42.0  | 32.0  | 15.0
3    | 178.0  | 12.5 | 156  | 42.5  | 32.5  | 15.2
6    | 182.0  | 13.0 | 158  | 43.0  | 33.0  | 15.5
9    | 185.0  | 13.5 | 160  | 43.5  | 33.5  | 15.8
12   | 188.0  | 14.0 | 162  | 44.0  | 34.0  | 16.0

Gains: +13 lbs total, +8 lbs LBM, +5 lbs fat
```

**Analysis:**
- Lean mass gain: 8 lbs (0.67 lbs/week) ✓ Good for intermediate
- Fat gain: 5 lbs (ratio 1.6:1 muscle:fat) ✓ Acceptable
- Measurements increased proportionally ✓

## Transitioning to Maintenance

### 2-Week Maintenance Phase

After a bulk, spend 2 weeks at maintenance before cutting:

```bash
# Continue training at same volume
lift program progress  # Check you're still following the program

# Hold bodyweight steady
# Track daily and average weekly weight
lift body weight 188.5
```

**Purpose:**
- Psychological break from surplus
- Allows metabolism to adapt
- Easier transition to deficit
- Verify current maintenance calories

## Starting a Cut

### Week 1: Establish Baseline

```bash
# Full measurements at start of cut
lift body measure

# Weight: 188.0 lbs
# Body fat: 14.0%
# LBM: 162 lbs

# Switch to cutting program (less volume, maintain intensity)
lift program start "PPL 5-Day Cut"
```

### Weekly Tracking During Cut

```bash
# Daily or alternate-day weights
lift body weight 187.2
lift body weight 186.8
# etc.

# Biweekly full measurements
lift body measure
```

**Target Rate of Loss:**
- 0.5-1.0% bodyweight/week
- For 188 lbs: 0.9-1.9 lbs/week
- Aim for ~1.5 lbs/week

### Critical Metrics During Cut

```bash
# Strength check (should maintain on main lifts)
lift stats exercise 1
lift stats exercise 15
lift stats exercise 23

# If strength dropping >10%, deficit too aggressive

# Volume check (expect some reduction)
lift stats volume --weeks 4

# Muscle measurements (should maintain)
lift body history --measurement chest --weeks 8
lift body history --measurement bicep_left --weeks 8
```

### Example 8-Week Cut Data

```
Week | Weight | BF%  | LBM  | Chest | Waist | Arms
-----|--------|------|------|-------|-------|------
1    | 188.0  | 14.0 | 162  | 44.0  | 34.0  | 16.0
2    | 186.5  | 13.5 | 161  | 43.8  | 33.5  | 15.9
4    | 183.0  | 12.5 | 160  | 43.5  | 32.5  | 15.8
6    | 180.0  | 11.5 | 159  | 43.2  | 31.5  | 15.7
8    | 177.5  | 10.5 | 159  | 43.0  | 31.0  | 15.6

Loss: -10.5 lbs total, -3 lbs LBM, -7.5 lbs fat
```

**Analysis:**
- Weight loss: 10.5 lbs (1.3 lbs/week) ✓ Good pace
- LBM loss: 3 lbs (minimal, expected) ✓
- Fat loss: 7.5 lbs (ratio 2.5:1 fat:muscle) ✓ Excellent
- Measurements maintained well ✓

## Diet Breaks

Every 6-8 weeks during a long cut, take a 1-2 week diet break:

```bash
# Increase calories to maintenance
# Continue training normally

# Track to ensure weight stabilizes
lift body weight 177.0
lift body weight 176.8
lift body weight 177.2

# After break, resume cut
```

**Benefits:**
- Restore metabolic hormones
- Psychological relief
- Improved adherence long-term

## Comparing Bulk vs Cut Performance

### Query Total Volume by Phase

```bash
# Volume during bulk (weeks 1-12)
lift stats volume --weeks 52  # View full chart

# Volume during cut (weeks 13-20)
# Compare to see how volume adjusted
```

### Example Analysis

**Bulk Phase (12 weeks):**
```
Average weekly volume: 95,000 lbs
Average weekly sets: 130
Best PRs: Bench +25 lbs, Squat +40 lbs, Deadlift +30 lbs
```

**Cut Phase (8 weeks):**
```
Average weekly volume: 75,000 lbs (-21%)
Average weekly sets: 105 (-19%)
Strength maintained: Bench -5 lbs, Squat -10 lbs, Deadlift -5 lbs
```

**Learnings:**
- Volume reduced ~20% during cut (appropriate)
- Strength loss minimal (<5% on main lifts)
- Quality of sets mattered more than quantity

## Using Notes for Context

```bash
# Add context to measurements
lift body measure
# In notes field: "End of bulk, starting maintenance phase"

# Add context to workouts
lift workout start "Push Day"
# After completing:
# Notes: "Week 6 of cut, energy lower but pushed through"
```

## Long-Term Tracking

After multiple bulk/cut cycles, query your data:

```bash
# Bodyweight trend over full year
lift body history --weeks 52

# Strength trends across phases
lift stats exercise 1 --weeks 52

# Total volume trends
lift stats volume --weeks 52
```

### Example 1-Year Progress

```
Starting Point (Jan 1):
- Weight: 170 lbs @ 15% BF
- LBM: 144.5 lbs
- Bench: 185 lbs × 5
- Squat: 225 lbs × 5

After 16-week Bulk (May 1):
- Weight: 185 lbs @ 14% BF
- LBM: 159 lbs (+14.5 lbs muscle!)
- Bench: 205 lbs × 5
- Squat: 275 lbs × 5

After 12-week Cut (Aug 1):
- Weight: 175 lbs @ 10% BF
- LBM: 157.5 lbs (retained almost all muscle)
- Bench: 200 lbs × 5
- Squat: 265 lbs × 5

After 16-week Bulk #2 (Dec 1):
- Weight: 190 lbs @ 13% BF
- LBM: 165 lbs (+20.5 lbs from start!)
- Bench: 225 lbs × 5
- Squat: 305 lbs × 5

Net yearly gain:
+20.5 lbs lean mass
Strength: +40 lbs bench, +80 lbs squat
```

## Tips for Success

1. **Consistent measurement timing**: Same day, same time, same conditions
2. **Take progress photos**: Measurements and photos together tell the full story
3. **Track how you feel**: Energy, recovery, hunger - note these
4. **Be patient**: Give each phase 8-12 weeks minimum
5. **Adjust based on data**: If fat gain too fast, reduce surplus
6. **Prioritize performance**: Strength should increase in bulk, maintain in cut
7. **Don't bulk forever**: Staying too lean is hard, but don't exceed 15-17% BF

## Red Flags

### During Bulk

- Waist growing faster than chest/arms
- Strength not increasing despite surplus
- Gaining >2 lbs/week consistently
- Body fat rising above 15-17%

**Action:** Reduce surplus, increase cardio, or switch to maintenance

### During Cut

- Losing >2 lbs/week consistently
- Strength dropping >10% on compounds
- Muscle measurements decreasing
- Energy levels bottoming out

**Action:** Reduce deficit, add diet break, or move to maintenance

## Conclusion

Lift gives you complete data to optimize your bulk/cut cycles over time. Track consistently, analyze objectively, and adjust based on what YOUR data shows!
