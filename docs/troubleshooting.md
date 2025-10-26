# Troubleshooting Guide

This guide covers common issues you might encounter while using Lift and how to resolve them.

## Installation Issues

### "Command not found: lift"

**Symptom:** After installing, running `lift` gives a "command not found" error.

**Causes and Solutions:**

1. **Python scripts directory not in PATH**

   ```bash
   # Find where pip installed the script
   pip show lift-tracker

   # Add Python scripts directory to PATH
   # On macOS/Linux, add to ~/.bashrc or ~/.zshrc:
   export PATH="$HOME/.local/bin:$PATH"

   # On Windows, add to system PATH:
   # %APPDATA%\Python\Scripts
   ```

2. **Installed in virtual environment**

   Make sure your virtual environment is activated:
   ```bash
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

3. **Installed with wrong Python version**

   Ensure you're using Python 3.11+:
   ```bash
   python --version  # Should be 3.11 or higher
   pip install --upgrade lift-tracker
   ```

### Import Errors

**Symptom:** `ModuleNotFoundError` or `ImportError` when running lift.

**Solution:**

```bash
# Reinstall with dependencies
pip uninstall lift-tracker
pip install lift-tracker --force-reinstall

# Or install with all dependencies explicitly
pip install 'lift-tracker[dev]'
```

### Permission Denied

**Symptom:** Permission errors during installation.

**Solution:**

```bash
# Install for current user only (recommended)
pip install --user lift-tracker

# Or use sudo (not recommended)
sudo pip install lift-tracker
```

## Database Issues

### "Database not initialized"

**Symptom:** Commands fail with "database not initialized" or "table not found" errors.

**Solution:**

```bash
lift init
```

If the error persists:

```bash
# Remove corrupted database
rm ~/.lift/lift.db

# Reinitialize
lift init
```

**Warning:** This deletes all your data. Back up first if possible.

### Database Locked

**Symptom:** "database is locked" error when running commands.

**Causes and Solutions:**

1. **Multiple lift processes running**

   ```bash
   # Check for running lift processes
   ps aux | grep lift

   # Kill any stuck processes
   kill <process_id>
   ```

2. **Orphaned lock file**

   ```bash
   # Remove lock files (if they exist)
   rm ~/.lift/.lock
   ```

3. **Database file permissions**

   ```bash
   # Fix permissions
   chmod 644 ~/.lift/lift.db
   ```

### Corrupted Database

**Symptom:** Unexpected errors, crashes, or inconsistent data.

**Solution:**

```bash
# Try DuckDB's recovery tools
duckdb ~/.lift/lift.db "PRAGMA integrity_check;"

# If corruption is confirmed, export what you can
# (This requires custom SQL - contact support)

# Last resort: reinitialize
rm ~/.lift/lift.db
lift init
```

## Workout Tracking Issues

### "Exercise not found"

**Symptom:** When trying to log a workout, the exercise can't be found.

**Solutions:**

1. **Check spelling**

   ```bash
   lift exercise search "partial name"
   ```

2. **Exercise doesn't exist**

   Create it as a custom exercise:
   ```bash
   lift exercise add
   ```

3. **Using exercise ID instead of name**

   ```bash
   # Find the correct ID
   lift exercise list | grep "Exercise Name"

   # Use with --exercise-id flag
   lift workout log --quick --exercise-id 42
   ```

### Incomplete Workouts Piling Up

**Symptom:** Many incomplete workouts listed, cluttering history.

**Solutions:**

1. **Complete them**

   ```bash
   lift workout complete --id <workout_id>
   ```

2. **Abandon them**

   ```bash
   lift workout abandon --id <workout_id>
   ```

3. **Delete them**

   ```bash
   lift workout delete <workout_id>
   ```

### Cannot Edit Sets

**Symptom:** Made a mistake logging a set, can't edit it.

**Current Limitation:** Lift doesn't support editing sets after they're logged.

**Workaround:**

```bash
# Delete the entire workout
lift workout delete <workout_id>

# Or delete and re-enter (requires custom SQL)
# Contact support for assistance
```

**Future Enhancement:** Set editing is planned for a future release.

### Sets Not Appearing in Workout

**Symptom:** Logged sets but they don't show in workout summary.

**Solutions:**

1. **Verify the workout is active**

   ```bash
   lift workout incomplete
   ```

2. **Check if sets were actually saved**

   ```bash
   lift workout last
   ```

3. **Database sync issue**

   ```bash
   # Stop any running processes
   # Re-run the command
   lift workout last
   ```

## Body Tracking Issues

### Weight Unit Conversion

**Symptom:** Logged weight in wrong unit (kg instead of lbs or vice versa).

**Solution:**

Currently no automatic conversion. You'll need to:

```bash
# Delete the incorrect entry (requires custom SQL)
# Or keep track manually which entries use which unit
```

**Tip:** Always specify the unit explicitly:

```bash
lift body weight 185.5 --unit lbs
lift body weight 84.0 --unit kg
```

### Missing Body Measurements

**Symptom:** Some measurements don't appear in history.

**Cause:** Optional measurements left blank are not stored.

**Solution:** This is by design. Enter 0 or a placeholder if you want to track that you measured on a given day.

## Statistics Issues

### "No data found"

**Symptom:** Stats commands return "no data" despite having logged workouts.

**Causes and Solutions:**

1. **Wrong exercise ID**

   ```bash
   lift exercise search "exercise name"
   # Note the correct ID
   lift stats exercise <correct_id>
   ```

2. **Data outside time range**

   ```bash
   # Increase the time window
   lift stats volume --weeks 52  # Look back a full year
   ```

3. **Incomplete workouts**

   Incomplete workouts don't count toward stats. Complete them:
   ```bash
   lift workout complete
   ```

### Incorrect Volume Calculations

**Symptom:** Volume numbers seem wrong.

**Explanation:** Volume = weight × reps × sets

**Checks:**

1. Verify your sets were logged with correct weight and reps
2. Check if warmup sets are included (they shouldn't be by default)
3. Ensure you're looking at the correct exercise

## Program Issues

### "Program not found"

**Symptom:** Can't start or view a program.

**Solutions:**

1. **Check exact name**

   ```bash
   lift program list
   # Copy the exact name
   lift program start "Exact Program Name"
   ```

2. **Program was deleted**

   Built-in programs can't be deleted. If it's a custom program, it may have been removed.

### Program Progress Not Updating

**Symptom:** Completed workouts don't show in program progress.

**Cause:** Workout name doesn't match the program workout template.

**Solution:** When starting a workout, use the exact name from the program:

```bash
# View program workout names
lift program show "Your Program"

# Start workout with matching name
lift workout start "Push A (Chest Focus)"
```

## Command-Line Issues

### Flags Not Working

**Symptom:** Command-line flags are ignored or cause errors.

**Common Mistakes:**

1. **Flag after argument**

   ```bash
   # Wrong
   lift workout history 10 --limit

   # Correct
   lift workout history --limit 10
   ```

2. **Using = instead of space**

   ```bash
   # Wrong (in most cases)
   lift body weight --unit=kg

   # Correct
   lift body weight --unit kg
   ```

### "Too many arguments"

**Symptom:** Error about too many arguments provided.

**Cause:** Strings with spaces not quoted.

**Solution:**

```bash
# Wrong
lift exercise info Barbell Bench Press

# Correct
lift exercise info "Barbell Bench Press"
```

### Typer/Click Errors

**Symptom:** Errors mentioning Typer or Click.

**Solution:**

```bash
# Update Typer
pip install --upgrade 'typer[all]'

# If that doesn't work, reinstall Lift
pip uninstall lift-tracker
pip install lift-tracker
```

## Performance Issues

### Slow Commands

**Symptom:** Commands take a long time to execute.

**Causes and Solutions:**

1. **Large database**

   ```bash
   # Check database size
   du -h ~/.lift/lift.db

   # If > 100MB, consider archiving old data
   ```

2. **Many exercises in library**

   ```bash
   # Use filters to narrow results
   lift exercise list --category Push
   ```

3. **System resource constraints**

   Close other applications, especially if on lower-end hardware.

### High Memory Usage

**Symptom:** Lift uses excessive memory.

**Solution:** This shouldn't happen with normal usage. If it does:

```bash
# Report the issue at
# https://github.com/parkerdgabel/lift/issues
```

## Display Issues

### Table Formatting Problems

**Symptom:** Tables appear garbled or misaligned.

**Causes and Solutions:**

1. **Terminal too narrow**

   Widen your terminal window, or use:
   ```bash
   # Some commands have compact modes
   lift exercise list --summary
   ```

2. **Emoji rendering issues**

   If your terminal doesn't support emojis, they may display incorrectly. This is a terminal limitation.

3. **Color issues**

   ```bash
   # Disable colors if needed
   export NO_COLOR=1
   lift workout history
   ```

### Text Truncation

**Symptom:** Long text (like exercise names or instructions) is cut off.

**Explanation:** This is intentional to fit tables in terminal width.

**Solution:** View full details:

```bash
lift exercise info "Exercise Name"
```

## Data Management Issues

### Lost Data After Update

**Symptom:** Data disappeared after updating Lift.

**Cause:** Unlikely but possible if database schema changed.

**Solution:**

```bash
# Check if database file still exists
ls -la ~/.lift/

# If file exists, ensure it's not corrupted
duckdb ~/.lift/lift.db "PRAGMA integrity_check;"

# If file is missing, check backups
ls -la ~/backup/  # or wherever you backup
```

**Prevention:** Always backup before major updates:

```bash
cp ~/.lift/lift.db ~/backup/lift-$(date +%Y%m%d).db
```

### Duplicate Entries

**Symptom:** Same workout or measurement appears twice.

**Cause:** Accidentally ran the same command twice.

**Solution:**

```bash
# Delete the duplicate
lift workout delete <workout_id>
# or
# Delete via custom SQL (contact support)
```

## Getting More Help

If your issue isn't covered here:

1. **Check the documentation**
   - [Getting Started Guide](./tutorials/getting-started.md)
   - [Custom Exercises Guide](./tutorials/custom-exercises.md)
   - [Program Design Guide](./tutorials/program-design.md)

2. **Use built-in help**
   ```bash
   lift --help
   lift workout --help
   lift exercise --help
   ```

3. **Search existing issues**
   Visit [GitHub Issues](https://github.com/parkerdgabel/lift/issues)

4. **Report a new issue**
   - Provide your Lift version: `lift --version`
   - Provide Python version: `python --version`
   - Provide OS and version
   - Describe steps to reproduce
   - Include error messages

5. **Check system logs**
   ```bash
   # macOS/Linux
   ~/.lift/logs/  # if logging is enabled

   # Or run with verbose output
   lift --verbose workout history
   ```

## Preventive Measures

To avoid issues:

1. **Regular backups**
   ```bash
   # Add to crontab or create an alias
   alias lift-backup='cp ~/.lift/lift.db ~/backup/lift-$(date +%Y%m%d).db'
   ```

2. **Keep Lift updated**
   ```bash
   pip install --upgrade lift-tracker
   ```

3. **Validate critical operations**
   - Double-check before deleting
   - Review data after bulk operations
   - Use `--help` when unsure about a command

4. **Use version control for custom programs**
   - Keep notes on custom programs in a text file
   - Makes it easier to recreate if needed

## Quick Diagnostic Checklist

If something goes wrong, run through this checklist:

- [ ] Is Lift installed? `which lift`
- [ ] Is database initialized? `ls ~/.lift/lift.db`
- [ ] Is Python version 3.11+? `python --version`
- [ ] Are dependencies up to date? `pip list | grep -E 'typer|rich|duckdb'`
- [ ] Can you run basic commands? `lift --version`
- [ ] Is there a database lock? `ps aux | grep lift`
- [ ] Is disk space available? `df -h`
- [ ] Are permissions correct? `ls -la ~/.lift/`

If all checks pass but you still have issues, file a bug report!
