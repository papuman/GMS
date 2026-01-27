#!/bin/bash
# Database Backup Script for Odoo with E-Invoicing Module
# Creates compressed, encrypted backups with cloud upload support
# Usage: ./scripts/backup_database.sh [--encrypt] [--upload]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${MODULE_DIR}/docker/backups"
FILESTORE_DIR="/var/lib/odoo/filestore"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="odoo_backup_${TIMESTAMP}"
RETENTION_DAYS=30
ENCRYPT=false
UPLOAD=false

# Load environment variables
if [ -f "${MODULE_DIR}/docker/.env" ]; then
    source "${MODULE_DIR}/docker/.env"
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --encrypt)
            ENCRYPT=true
            shift
            ;;
        --upload)
            UPLOAD=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--encrypt] [--upload]"
            exit 1
            ;;
    esac
done

# Colors for output
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

# Create backup directory
mkdir -p "${BACKUP_DIR}"

log "Starting database backup: ${BACKUP_NAME}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running"
    exit 1
fi

# Check if containers are running
cd "${MODULE_DIR}/docker"
if ! docker-compose ps | grep -q "Up"; then
    log_error "Containers are not running"
    exit 1
fi

# 1. Backup PostgreSQL database
log "Backing up PostgreSQL database..."
docker-compose exec -T db pg_dump \
    -U "${POSTGRES_USER:-odoo}" \
    -Fc \
    -Z9 \
    "${POSTGRES_DB:-odoo}" > "${BACKUP_DIR}/${BACKUP_NAME}.dump"

if [ $? -eq 0 ]; then
    log "Database backup created: ${BACKUP_NAME}.dump"
else
    log_error "Database backup failed"
    exit 1
fi

# 2. Backup filestore (attachments, images, etc.)
log "Backing up filestore..."
docker-compose exec -T odoo tar czf - /var/lib/odoo/filestore 2>/dev/null > "${BACKUP_DIR}/${BACKUP_NAME}_filestore.tar.gz" || {
    log_warning "Filestore backup failed or empty"
}

# 3. Backup Hacienda certificates (if they exist)
if [ -d "${MODULE_DIR}/docker/certificates" ]; then
    log "Backing up Hacienda certificates..."
    tar czf "${BACKUP_DIR}/${BACKUP_NAME}_certificates.tar.gz" \
        -C "${MODULE_DIR}/docker" certificates
fi

# 4. Create manifest file
log "Creating backup manifest..."
cat > "${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt" <<EOF
Backup Information
==================
Timestamp: $(date)
Database: ${POSTGRES_DB:-odoo}
Module Version: 19.0.1.8.0
Hostname: $(hostname)

Files:
------
- ${BACKUP_NAME}.dump (PostgreSQL database)
- ${BACKUP_NAME}_filestore.tar.gz (Odoo filestore)
- ${BACKUP_NAME}_certificates.tar.gz (Hacienda certificates)

Backup Size:
-----------
$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}"* | awk '{print $1, $2}')

Checksum (SHA256):
-----------------
$(sha256sum "${BACKUP_DIR}/${BACKUP_NAME}.dump" | awk '{print $1}')
EOF

# 5. Encrypt backup if requested
if [ "$ENCRYPT" = true ]; then
    if [ -z "${BACKUP_ENCRYPTION_PASSWORD:-}" ]; then
        log_error "BACKUP_ENCRYPTION_PASSWORD not set in .env file"
        exit 1
    fi

    log "Encrypting backup..."

    # Encrypt database dump
    openssl enc -aes-256-cbc -salt -pbkdf2 \
        -in "${BACKUP_DIR}/${BACKUP_NAME}.dump" \
        -out "${BACKUP_DIR}/${BACKUP_NAME}.dump.enc" \
        -pass pass:"${BACKUP_ENCRYPTION_PASSWORD}"

    # Remove unencrypted version
    rm "${BACKUP_DIR}/${BACKUP_NAME}.dump"

    log "Backup encrypted successfully"
fi

# 6. Upload to cloud storage if requested
if [ "$UPLOAD" = true ]; then
    if [ "${BACKUP_S3_ENABLED:-false}" = "true" ]; then
        log "Uploading to S3..."

        # Check if AWS CLI is installed
        if ! command -v aws &> /dev/null; then
            log_error "AWS CLI not installed. Install with: pip install awscli"
            exit 1
        fi

        # Configure AWS credentials
        export AWS_ACCESS_KEY_ID="${BACKUP_S3_ACCESS_KEY}"
        export AWS_SECRET_ACCESS_KEY="${BACKUP_S3_SECRET_KEY}"
        export AWS_DEFAULT_REGION="${BACKUP_S3_REGION:-us-east-1}"

        # Upload all backup files
        aws s3 sync "${BACKUP_DIR}" "s3://${BACKUP_S3_BUCKET}/backups/" \
            --exclude "*" \
            --include "${BACKUP_NAME}*" \
            --storage-class STANDARD_IA

        if [ $? -eq 0 ]; then
            log "Backup uploaded to S3: s3://${BACKUP_S3_BUCKET}/backups/"
        else
            log_error "S3 upload failed"
        fi
    else
        log_warning "S3 backup not enabled in .env file"
    fi
fi

# 7. Clean up old backups
log "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "odoo_backup_*" -type f -mtime +${RETENTION_DAYS} -delete
log "Old backups cleaned up"

# 8. Display backup summary
log "========================================="
log "Backup completed successfully!"
log "========================================="
log "Backup location: ${BACKUP_DIR}"
log "Backup files:"
ls -lh "${BACKUP_DIR}/${BACKUP_NAME}"* 2>/dev/null | awk '{print "  -", $9, "(" $5 ")"}'
log ""
log "Total backup size: $(du -sh "${BACKUP_DIR}/${BACKUP_NAME}"* | awk '{sum+=$1} END {print sum}')"
log ""
log "To restore this backup, run:"
log "  ./scripts/restore_database.sh ${BACKUP_DIR}/${BACKUP_NAME}.dump"

# Return success
exit 0
