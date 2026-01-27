#!/bin/bash
# Database Restore Script for Odoo with E-Invoicing Module
# Restores database from backup with validation and integrity checks
# Usage: ./scripts/restore_database.sh <backup_file> [--decrypt]

set -euo pipefail

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file> [--decrypt]"
    echo "Example: $0 /path/to/odoo_backup_20241229_120000.dump"
    exit 1
fi

BACKUP_FILE="$1"
DECRYPT=false

# Parse optional arguments
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --decrypt)
            DECRYPT=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEMP_DIR="${MODULE_DIR}/docker/backups/temp"

# Load environment variables
if [ -f "${MODULE_DIR}/docker/.env" ]; then
    source "${MODULE_DIR}/docker/.env"
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Validation
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

log "========================================="
log "Starting database restoration"
log "========================================="
log "Backup file: $BACKUP_FILE"

# Decrypt if needed
if [ "$DECRYPT" = true ]; then
    if [ -z "${BACKUP_ENCRYPTION_PASSWORD:-}" ]; then
        log_error "BACKUP_ENCRYPTION_PASSWORD not set in .env file"
        exit 1
    fi

    log "Decrypting backup..."
    mkdir -p "$TEMP_DIR"

    DECRYPTED_FILE="${TEMP_DIR}/decrypted_$(basename ${BACKUP_FILE%.enc})"

    openssl enc -aes-256-cbc -d -pbkdf2 \
        -in "$BACKUP_FILE" \
        -out "$DECRYPTED_FILE" \
        -pass pass:"${BACKUP_ENCRYPTION_PASSWORD}"

    BACKUP_FILE="$DECRYPTED_FILE"
    log "Backup decrypted successfully"
fi

# Confirm restoration
log_warning "This will DESTROY the current database and replace it with the backup."
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log "Restoration cancelled by user"
    exit 0
fi

# Additional confirmation
read -p "Type 'RESTORE' to confirm: " -r
if [[ ! $REPLY == "RESTORE" ]]; then
    log "Restoration cancelled - confirmation failed"
    exit 0
fi

cd "${MODULE_DIR}/docker"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running"
    exit 1
fi

# Stop Odoo service (keep database running)
log "Stopping Odoo service..."
docker-compose stop odoo
sleep 5

# Create a backup of current database (just in case)
log "Creating safety backup of current database..."
SAFETY_BACKUP="${MODULE_DIR}/docker/backups/pre_restore_$(date +%Y%m%d_%H%M%S).dump"
docker-compose exec -T db pg_dump \
    -U "${POSTGRES_USER:-odoo}" \
    -Fc \
    "${POSTGRES_DB:-odoo}" > "$SAFETY_BACKUP" || {
    log_warning "Could not create safety backup (database might not exist)"
}

# Terminate existing connections
log "Terminating existing database connections..."
docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d postgres <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '${POSTGRES_DB:-odoo}'
  AND pid <> pg_backend_pid();
EOF

# Drop and recreate database
log "Dropping and recreating database..."
docker-compose exec -T db dropdb -U "${POSTGRES_USER:-odoo}" --if-exists "${POSTGRES_DB:-odoo}"
docker-compose exec -T db createdb -U "${POSTGRES_USER:-odoo}" "${POSTGRES_DB:-odoo}"

# Restore database
log "Restoring database from backup..."
cat "$BACKUP_FILE" | docker-compose exec -T db pg_restore \
    -U "${POSTGRES_USER:-odoo}" \
    -d "${POSTGRES_DB:-odoo}" \
    --no-owner \
    --no-acl \
    -v 2>&1 | grep -v "WARNING: errors ignored on restore"

if [ ${PIPESTATUS[1]} -eq 0 ]; then
    log "Database restored successfully"
else
    log_error "Database restoration failed"

    # Restore safety backup
    log "Attempting to restore safety backup..."
    docker-compose exec -T db dropdb -U "${POSTGRES_USER:-odoo}" "${POSTGRES_DB:-odoo}"
    docker-compose exec -T db createdb -U "${POSTGRES_USER:-odoo}" "${POSTGRES_DB:-odoo}"
    cat "$SAFETY_BACKUP" | docker-compose exec -T db pg_restore \
        -U "${POSTGRES_USER:-odoo}" \
        -d "${POSTGRES_DB:-odoo}" \
        --no-owner \
        --no-acl

    exit 1
fi

# Restore filestore if it exists
FILESTORE_BACKUP="${BACKUP_FILE%.dump}_filestore.tar.gz"
if [ -f "$FILESTORE_BACKUP" ]; then
    log "Restoring filestore..."

    # Remove old filestore
    docker-compose exec -T odoo rm -rf /var/lib/odoo/filestore/* || true

    # Restore new filestore
    cat "$FILESTORE_BACKUP" | docker-compose exec -T odoo tar xzf - -C /

    log "Filestore restored successfully"
else
    log_warning "Filestore backup not found: $FILESTORE_BACKUP"
fi

# Restore certificates if they exist
CERT_BACKUP="${BACKUP_FILE%.dump}_certificates.tar.gz"
if [ -f "$CERT_BACKUP" ]; then
    log "Restoring Hacienda certificates..."
    tar xzf "$CERT_BACKUP" -C "${MODULE_DIR}/docker/"
    log "Certificates restored successfully"
else
    log_warning "Certificate backup not found: $CERT_BACKUP"
fi

# Run ANALYZE and VACUUM
log "Optimizing database..."
docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d "${POSTGRES_DB:-odoo}" <<EOF
ANALYZE;
VACUUM ANALYZE;
EOF

# Start Odoo service
log "Starting Odoo service..."
docker-compose start odoo

# Wait for Odoo to be ready
log "Waiting for Odoo to start (60 seconds)..."
sleep 60

# Verify restoration
log "Verifying restoration..."

# Check if database is accessible
if docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d "${POSTGRES_DB:-odoo}" -c "SELECT 1" >/dev/null 2>&1; then
    log "Database is accessible"
else
    log_error "Database is not accessible"
    exit 1
fi

# Check if Odoo responds
if curl -f http://localhost/web/health >/dev/null 2>&1; then
    log "Odoo is responding"
else
    log_warning "Odoo is not responding yet (may need more time)"
fi

# Clean up temp files
if [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi

log "========================================="
log "Database restoration completed!"
log "========================================="
log ""
log "Safety backup created at: $SAFETY_BACKUP"
log ""
log "Next steps:"
log "1. Verify data integrity"
log "2. Test critical functionality"
log "3. Check module installation: docker-compose exec odoo odoo shell"
log "4. Review logs: docker-compose logs -f odoo"
log ""
log "If you encounter issues, you can restore the safety backup:"
log "  $0 $SAFETY_BACKUP"

exit 0
