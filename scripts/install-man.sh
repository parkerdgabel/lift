#!/bin/bash
# Install LIFT man page to system man directory
# Usage: sudo ./scripts/install-man.sh

set -e

MAN_FILE="man/lift.1"
MAN_DIR="/usr/local/share/man/man1"

if [ ! -f "$MAN_FILE" ]; then
    echo "Error: Man page file not found: $MAN_FILE"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Create man directory if it doesn't exist
mkdir -p "$MAN_DIR"

# Copy man page
echo "Installing man page to $MAN_DIR/lift.1"
cp "$MAN_FILE" "$MAN_DIR/lift.1"

# Set proper permissions
chmod 644 "$MAN_DIR/lift.1"

# Update man database (if mandb is available)
if command -v mandb &> /dev/null; then
    echo "Updating man database..."
    mandb -q
elif command -v makewhatis &> /dev/null; then
    echo "Updating man database..."
    makewhatis "$MAN_DIR"
fi

echo "Man page installed successfully!"
echo "Try: man lift"
