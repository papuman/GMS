#!/bin/bash
# Data Migration Script for Costa Rica E-Invoicing Module
# Migrates data from test/staging to production environment
# Usage: ./scripts/migrate_data.sh --source <source_db> --target <target_db>

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DB=""
TARGET_DB=""
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --source)
            SOURCE_DB="$2"
            shift 2
            ;;
        --target)
            TARGET_DB="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 --source <source_db> --target <target_db> [--dry-run]"
            exit 1
            ;;
    esac
done

# Validate arguments
if [ -z "$SOURCE_DB" ] || [ -z "$TARGET_DB" ]; then
    echo "Error: --source and --target are required"
    echo "Usage: $0 --source <source_db> --target <target_db> [--dry-run]"
    exit 1
fi

# Load environment
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

log "========================================="
log "Data Migration"
log "========================================="
log "Source: $SOURCE_DB"
log "Target: $TARGET_DB"
log "Dry Run: $DRY_RUN"
log "========================================="

cd "${MODULE_DIR}/docker"

# Verify databases exist
log "Verifying databases..."
if ! docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -lqt | cut -d \| -f 1 | grep -qw "$SOURCE_DB"; then
    log_error "Source database '$SOURCE_DB' not found"
    exit 1
fi

if ! docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -lqt | cut -d \| -f 1 | grep -qw "$TARGET_DB"; then
    log_error "Target database '$TARGET_DB' not found"
    exit 1
fi

log "Databases verified"

# Create migration script
MIGRATION_SQL=$(cat <<'EOF'
-- Data Migration Script for Costa Rica E-Invoicing Module
-- This script migrates master data from source to target database

\echo 'Starting data migration...'

-- 1. Migrate CIIU codes (if not already present)
\echo '1. Migrating CIIU codes...'
INSERT INTO target_db.einvoice_ciiu_code (code, name, description, category, active, create_uid, create_date, write_uid, write_date)
SELECT code, name, description, category, active, create_uid, create_date, write_uid, write_date
FROM source_db.einvoice_ciiu_code
WHERE code NOT IN (SELECT code FROM target_db.einvoice_ciiu_code)
ON CONFLICT (code) DO NOTHING;

-- 2. Migrate payment methods
\echo '2. Migrating payment methods...'
INSERT INTO target_db.einvoice_payment_method (code, name, description, requires_transaction_id, active, create_uid, create_date, write_uid, write_date)
SELECT code, name, description, requires_transaction_id, active, create_uid, create_date, write_uid, write_date
FROM source_db.einvoice_payment_method
WHERE code NOT IN (SELECT code FROM target_db.einvoice_payment_method)
ON CONFLICT (code) DO NOTHING;

-- 3. Migrate discount codes
\echo '3. Migrating discount codes...'
INSERT INTO target_db.einvoice_discount_code (code, name, description, requires_description, active, create_uid, create_date, write_uid, write_date)
SELECT code, name, description, requires_description, active, create_uid, create_date, write_uid, write_date
FROM source_db.einvoice_discount_code
WHERE code NOT IN (SELECT code FROM target_db.einvoice_discount_code)
ON CONFLICT (code) DO NOTHING;

-- 4. Migrate partner CIIU code assignments
\echo '4. Migrating partner CIIU codes...'
UPDATE target_db.res_partner tp
SET einvoice_ciiu_code_id = sp.einvoice_ciiu_code_id
FROM source_db.res_partner sp
WHERE tp.vat = sp.vat
  AND sp.einvoice_ciiu_code_id IS NOT NULL
  AND tp.einvoice_ciiu_code_id IS NULL;

-- 5. Migrate product configurations (if applicable)
\echo '5. Migrating product e-invoice configurations...'
UPDATE target_db.product_template tt
SET einvoice_tax_code = st.einvoice_tax_code,
    einvoice_exempt_reason = st.einvoice_exempt_reason
FROM source_db.product_template st
WHERE tt.default_code = st.default_code
  AND st.einvoice_tax_code IS NOT NULL;

-- 6. Summary
\echo 'Migration completed!'
\echo 'Summary:'
SELECT 'CIIU codes migrated:' as item, COUNT(*) as count FROM target_db.einvoice_ciiu_code
UNION ALL
SELECT 'Payment methods migrated:', COUNT(*) FROM target_db.einvoice_payment_method
UNION ALL
SELECT 'Discount codes migrated:', COUNT(*) FROM target_db.einvoice_discount_code
UNION ALL
SELECT 'Partners with CIIU codes:', COUNT(*) FROM target_db.res_partner WHERE einvoice_ciiu_code_id IS NOT NULL;
EOF
)

# Replace database names in script
MIGRATION_SQL="${MIGRATION_SQL//source_db/$SOURCE_DB}"
MIGRATION_SQL="${MIGRATION_SQL//target_db/$TARGET_DB}"

if [ "$DRY_RUN" = true ]; then
    log "DRY RUN - Migration script:"
    echo "==========================================="
    echo "$MIGRATION_SQL"
    echo "==========================================="
    log "Dry run completed (no changes made)"
    exit 0
fi

# Confirm migration
log_warning "This will migrate data from '$SOURCE_DB' to '$TARGET_DB'"
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log "Migration cancelled by user"
    exit 0
fi

# Backup target database before migration
log "Creating backup of target database..."
BACKUP_FILE="${MODULE_DIR}/docker/backups/pre_migration_${TARGET_DB}_$(date +%Y%m%d_%H%M%S).dump"
docker-compose exec -T db pg_dump \
    -U "${POSTGRES_USER:-odoo}" \
    -Fc \
    "$TARGET_DB" > "$BACKUP_FILE"
log "Backup created: $BACKUP_FILE"

# Execute migration
log "Executing data migration..."
echo "$MIGRATION_SQL" | docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d "$TARGET_DB"

if [ $? -eq 0 ]; then
    log "Migration completed successfully"
else
    log_error "Migration failed"
    log "You can restore the backup using:"
    log "  ./scripts/restore_database.sh $BACKUP_FILE"
    exit 1
fi

# Verify migration
log "Verifying migration..."

# Count migrated records
ciiu_count=$(docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d "$TARGET_DB" -t -c "SELECT COUNT(*) FROM einvoice_ciiu_code;" | xargs)
payment_count=$(docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d "$TARGET_DB" -t -c "SELECT COUNT(*) FROM einvoice_payment_method;" | xargs)
discount_count=$(docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d "$TARGET_DB" -t -c "SELECT COUNT(*) FROM einvoice_discount_code;" | xargs)
partner_ciiu_count=$(docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d "$TARGET_DB" -t -c "SELECT COUNT(*) FROM res_partner WHERE einvoice_ciiu_code_id IS NOT NULL;" | xargs)

log "========================================="
log "Migration Summary"
log "========================================="
log "CIIU codes: $ciiu_count"
log "Payment methods: $payment_count"
log "Discount codes: $discount_count"
log "Partners with CIIU codes: $partner_ciiu_count"
log "========================================="
log "Backup saved to: $BACKUP_FILE"
log "========================================="

exit 0
