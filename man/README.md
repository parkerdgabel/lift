# LIFT Man Page

This directory contains the Unix man page for LIFT.

## Files

- `lift.1` - Manual page in troff format (section 1: User Commands)

## Viewing the Man Page

### From Source

```bash
# View using man
man man/lift.1

# View as plain text
groff -man -Tascii man/lift.1 | less

# View as HTML
groff -man -Thtml man/lift.1 > lift.html
```

### After Installation

Once LIFT is installed, the man page should be automatically available:

```bash
man lift
```

## Installing the Man Page

### Automatic Installation

The man page is automatically installed when you:
- Install via `pip install lift` (to Python's man directory)
- Install via Homebrew formula
- Install via Debian package

### Manual Installation

```bash
# Install to system man directory (requires sudo)
sudo ./scripts/install-man.sh

# Or copy manually
sudo cp man/lift.1 /usr/local/share/man/man1/
sudo mandb  # Update man database
```

## Generating Alternative Formats

Generate HTML, PDF, and text versions:

```bash
./scripts/gen-man-formats.sh
```

Generated files will be in `man/generated/`:
- `lift.1.txt` - Plain text
- `lift.1.html` - HTML
- `lift.1.pdf` - PDF (requires ps2pdf)

## Man Page Sections

The man page includes:

1. **NAME** - Brief description
2. **SYNOPSIS** - Command syntax
3. **DESCRIPTION** - Detailed overview
4. **GLOBAL OPTIONS** - Options that apply to all commands
5. **COMMANDS** - Complete command reference
   - Database Management
   - Exercise Management
   - Workout Tracking
   - Program Management
   - Statistics & Analytics
   - Body Tracking
   - Data Management
   - Configuration
6. **CONFIGURATION SETTINGS** - All available settings
7. **EXAMPLES** - Practical usage examples
8. **ENVIRONMENT** - Environment variables
9. **FILES** - Important file locations
10. **DATABASE SCHEMA** - Database structure
11. **EXERCISE CATEGORIES** - Exercise organization
12. **MUSCLE GROUPS** - Available muscle groups
13. **EQUIPMENT TYPES** - Supported equipment
14. **EXIT STATUS** - Return codes
15. **NOTES** - Additional information
16. **BUGS** - Bug reporting
17. **AUTHOR** - Author information
18. **COPYRIGHT** - License information
19. **SEE ALSO** - Related documentation

## Updating the Man Page

When updating the man page:

1. Edit `lift.1` in troff format
2. Test rendering: `man man/lift.1`
3. Update version and date in the header
4. Regenerate alternative formats if needed
5. Update this README if structure changes

## Man Page Format

The man page is written in troff/groff format. Key formatting codes:

- `.TH` - Title header
- `.SH` - Section header
- `.SS` - Subsection header
- `.TP` - Tagged paragraph (for options)
- `.PP` - Paragraph break
- `.B` - Bold text
- `.I` - Italic text
- `.BR` - Bold then roman
- `.RS/.RE` - Indent/outdent block
- `.nf/.fi` - No-fill/fill mode (for code blocks)

## Resources

- [groff man page format](https://man7.org/linux/man-pages/man7/groff_man.7.html)
- [Writing man pages](https://www.kernel.org/doc/man-pages/man-pages-style-guide.html)
- [Man page conventions](https://man7.org/linux/man-pages/man7/man-pages.7.html)
