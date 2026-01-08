#!/bin/bash
# Database Backup Script for TS OPAC eLibrary
# Usage: bash backup_database.sh
# Crontab: 0 2 * * * /path/to/backup_database.sh >> /var/log/elibrary/backup.log 2>&1

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_CONTAINER="elibrary_db"
DB_NAME="${DB_NAME:-elibrary}"
DB_USER="${DB_USER:-elibrary}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/elibrary_backup_$TIMESTAMP.sql"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $*"
}

# ============================================================================
# Validation
# ============================================================================

if [ ! -d "$BACKUP_DIR" ]; then
    log_error "Backup directory does not exist: $BACKUP_DIR"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "docker-compose not found"
    exit 1
fi

# Check if database container is running
if ! docker-compose ps | grep -q "$DB_CONTAINER"; then
    log_error "Database container not running: $DB_CONTAINER"
    exit 1
fi

# ============================================================================
# Backup
# ============================================================================

log_info "Starting database backup..."
log_info "Database: $DB_NAME"
log_info "Output: $BACKUP_FILE"

# Create backup
if ! docker-compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"; then
    log_error "Database dump failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

log_info "Backup created successfully"

# ============================================================================
# Compression
# ============================================================================

log_info "Compressing backup..."

if ! gzip "$BACKUP_FILE"; then
    log_error "Compression failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

BACKUP_FILE="${BACKUP_FILE}.gz"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

log_success "Backup compressed: $BACKUP_SIZE"

# ============================================================================
# Retention Policy
# ============================================================================

log_info "Applying retention policy (keeping last $RETENTION_DAYS days)..."

DELETED_COUNT=0
while IFS= read -r file; do
    rm -f "$file"
    ((DELETED_COUNT++))
done < <(find "$BACKUP_DIR" -name "elibrary_backup_*.sql.gz" -mtime +$RETENTION_DAYS)

if [ $DELETED_COUNT -gt 0 ]; then
    log_info "Deleted $DELETED_COUNT old backup(s)"
fi

# ============================================================================
# Verification
# ============================================================================

log_info "Verifying backup integrity..."

if gzip -t "$BACKUP_FILE"; then
    log_success "Backup integrity verified"
else
    log_error "Backup integrity check failed"
    exit 1
fi

# ============================================================================
# Summary
# ============================================================================

BACKUP_COUNT=$(find "$BACKUP_DIR" -name "elibrary_backup_*.sql.gz" | wc -l)

log_success "Backup completed successfully!"
log_info "Backup file: $BACKUP_FILE"
log_info "Backup size: $BACKUP_SIZE"
log_info "Total backups stored: $BACKUP_COUNT"

# ============================================================================
# Notification (optional)
# ============================================================================

# If you want email notification, uncomment and configure:
# NOTIFICATION_EMAIL="admin@yourlibrary.com"
# {
#     echo "Backup Report"
#     echo "============="
#     echo "Time: $(date)"
#     echo "Database: $DB_NAME"
#     echo "Size: $BACKUP_SIZE"
#     echo "Status: SUCCESS"
# } | mail -s "Database Backup Report - $TIMESTAMP" "$NOTIFICATION_EMAIL"

exit 0
