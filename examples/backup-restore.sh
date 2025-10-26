#!/bin/bash

# Lift Database Backup and Restore Script
# Usage:
#   ./backup-restore.sh backup    - Create a backup
#   ./backup-restore.sh restore   - Restore from latest backup
#   ./backup-restore.sh list      - List all backups

set -e  # Exit on error

# Configuration
DEFAULT_DB_PATH="$HOME/.lift/lift.db"
BACKUP_DIR="$HOME/.lift/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/lift_backup_$TIMESTAMP.db"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Function: Print usage
usage() {
    echo "Usage: $0 {backup|restore|list|auto-backup}"
    echo ""
    echo "Commands:"
    echo "  backup         Create a new backup"
    echo "  restore        Restore from latest backup"
    echo "  restore <file> Restore from specific backup file"
    echo "  list           List all available backups"
    echo "  auto-backup    Set up automatic daily backups (cron)"
    echo "  cleanup        Remove backups older than 30 days"
    exit 1
}

# Function: Create backup
backup() {
    echo -e "${GREEN}Creating backup...${NC}"

    if [ ! -f "$DEFAULT_DB_PATH" ]; then
        echo -e "${RED}Error: Database not found at $DEFAULT_DB_PATH${NC}"
        exit 1
    fi

    # Copy database file
    cp "$DEFAULT_DB_PATH" "$BACKUP_FILE"

    # Compress to save space
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"

    # Get file size
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

    echo -e "${GREEN}✓ Backup created successfully${NC}"
    echo "  Location: $BACKUP_FILE"
    echo "  Size: $SIZE"

    # Optional: Verify backup integrity
    echo -e "${YELLOW}Verifying backup integrity...${NC}"
    gunzip -c "$BACKUP_FILE" | duckdb -c "PRAGMA integrity_check" 2>&1 | grep -q "ok" && \
        echo -e "${GREEN}✓ Backup verified${NC}" || \
        echo -e "${RED}⚠ Warning: Backup verification failed${NC}"
}

# Function: List backups
list_backups() {
    echo -e "${GREEN}Available backups:${NC}"
    echo ""

    if [ -z "$(ls -A $BACKUP_DIR/*.gz 2>/dev/null)" ]; then
        echo "  No backups found"
        return
    fi

    printf "%-30s %10s %20s\n" "Backup File" "Size" "Created"
    printf "%-30s %10s %20s\n" "$(printf '%.0s-' {1..30})" "$(printf '%.0s-' {1..10})" "$(printf '%.0s-' {1..20})"

    for backup in "$BACKUP_DIR"/*.gz; do
        if [ -f "$backup" ]; then
            filename=$(basename "$backup")
            size=$(du -h "$backup" | cut -f1)
            created=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$backup" 2>/dev/null || stat -c "%y" "$backup" | cut -d' ' -f1-2)
            printf "%-30s %10s %20s\n" "$filename" "$size" "$created"
        fi
    done

    echo ""
    echo "Backup directory: $BACKUP_DIR"
}

# Function: Restore from backup
restore() {
    local restore_file="$1"

    # If no file specified, use latest backup
    if [ -z "$restore_file" ]; then
        restore_file=$(ls -t "$BACKUP_DIR"/*.gz 2>/dev/null | head -1)

        if [ -z "$restore_file" ]; then
            echo -e "${RED}Error: No backups found${NC}"
            exit 1
        fi

        echo -e "${YELLOW}No backup file specified. Using latest: $(basename $restore_file)${NC}"
    fi

    # Check if file exists
    if [ ! -f "$restore_file" ]; then
        # Try adding backup dir prefix
        restore_file="$BACKUP_DIR/$restore_file"

        if [ ! -f "$restore_file" ]; then
            echo -e "${RED}Error: Backup file not found: $restore_file${NC}"
            exit 1
        fi
    fi

    # Confirm restoration
    read -p "This will replace your current database. Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        exit 0
    fi

    echo -e "${GREEN}Restoring from backup...${NC}"

    # Create backup of current database before restoring
    if [ -f "$DEFAULT_DB_PATH" ]; then
        SAFETY_BACKUP="$BACKUP_DIR/pre_restore_backup_$TIMESTAMP.db"
        cp "$DEFAULT_DB_PATH" "$SAFETY_BACKUP"
        echo "  Created safety backup: $SAFETY_BACKUP"
    fi

    # Decompress and restore
    gunzip -c "$restore_file" > "$DEFAULT_DB_PATH"

    # Verify restored database
    echo -e "${YELLOW}Verifying restored database...${NC}"
    if duckdb "$DEFAULT_DB_PATH" "PRAGMA integrity_check" 2>&1 | grep -q "ok"; then
        echo -e "${GREEN}✓ Database restored successfully${NC}"
        echo "  Location: $DEFAULT_DB_PATH"
    else
        echo -e "${RED}⚠ Warning: Database verification failed${NC}"
        echo "  Restoring safety backup..."
        cp "$SAFETY_BACKUP" "$DEFAULT_DB_PATH"
        echo -e "${YELLOW}Rolled back to previous state${NC}"
        exit 1
    fi
}

# Function: Set up automatic backups
auto_backup() {
    echo -e "${GREEN}Setting up automatic daily backups...${NC}"

    SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
    CRON_COMMAND="0 2 * * * $SCRIPT_PATH backup > /dev/null 2>&1"

    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH backup"; then
        echo -e "${YELLOW}Automatic backup already configured${NC}"
        return
    fi

    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

    echo -e "${GREEN}✓ Automatic backups enabled${NC}"
    echo "  Schedule: Daily at 2:00 AM"
    echo "  Location: $BACKUP_DIR"
    echo ""
    echo "To disable automatic backups, run:"
    echo "  crontab -e"
    echo "  # Remove the line containing: $SCRIPT_PATH"
}

# Function: Clean up old backups
cleanup() {
    echo -e "${GREEN}Cleaning up backups older than 30 days...${NC}"

    DELETED=0
    for backup in "$BACKUP_DIR"/*.gz; do
        if [ -f "$backup" ]; then
            # Find files older than 30 days
            if [ "$(find "$backup" -mtime +30 2>/dev/null)" ]; then
                echo "  Deleting: $(basename $backup)"
                rm "$backup"
                DELETED=$((DELETED + 1))
            fi
        fi
    done

    if [ $DELETED -eq 0 ]; then
        echo "  No old backups to delete"
    else
        echo -e "${GREEN}✓ Deleted $DELETED old backup(s)${NC}"
    fi
}

# Main script logic
case "${1:-}" in
    backup)
        backup
        ;;
    restore)
        restore "$2"
        ;;
    list)
        list_backups
        ;;
    auto-backup)
        auto_backup
        ;;
    cleanup)
        cleanup
        ;;
    *)
        usage
        ;;
esac
