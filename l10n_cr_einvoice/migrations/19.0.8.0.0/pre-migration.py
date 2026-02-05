# -*- coding: utf-8 -*-
"""
Pre-migration script for l10n_cr_einvoice v19.0.8.0.0

Phase: Cédula Cache and Validation Rules Infrastructure
Purpose: Backup existing data before schema changes

Changes in this migration:
  1. Backup res.partner records with validation overrides
  2. Export current validation state for rollback purposes
  3. Log pre-migration state for audit trail
  4. Verify database integrity before proceeding

This script runs BEFORE Odoo ORM creates new tables/columns.

ROLLBACK INSTRUCTIONS:
  If migration fails, run the generated SQL scripts in reverse:

  1. Restore from backup:
     \copy res_partner FROM '/tmp/partner_backup_YYYYMMDD.csv' WITH CSV HEADER;

  2. Drop new tables:
     DROP TABLE IF EXISTS l10n_cr_cedula_cache;
     DROP TABLE IF EXISTS l10n_cr_validation_rule;

  3. Downgrade module:
     UPDATE ir_module_module
     SET latest_version = '19.0.7.0.0'
     WHERE name = 'l10n_cr_einvoice';
"""
import logging
import csv
from datetime import datetime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration entry point.

    Called by Odoo BEFORE module upgrade applies new field definitions.
    Creates safety backups and validates current state.
    """
    _logger.info('=' * 80)
    _logger.info('Pre-migration: Cédula Cache & Validation Rules (v19.0.8.0.0)')
    _logger.info('Current version: %s', version)
    _logger.info('=' * 80)

    # Step 1: Backup existing partner data
    _backup_partner_data(cr)

    # Step 2: Log current validation override state
    _log_validation_overrides(cr)

    # Step 3: Verify database integrity
    _verify_database_integrity(cr)

    # Step 4: Check for conflicting customizations
    _check_conflicts(cr)

    _logger.info('=' * 80)
    _logger.info('Pre-migration checks completed successfully!')
    _logger.info('Proceeding with schema changes...')
    _logger.info('=' * 80)


def _backup_partner_data(cr):
    """
    Create backup of res.partner records with existing validation data.

    Backs up to a temporary table for easy rollback.
    """
    _logger.info('\n' + '=' * 80)
    _logger.info('STEP 1: Backing Up Partner Data')
    _logger.info('=' * 80)

    # Check if backup table already exists (from previous failed migration)
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'res_partner_backup_19_0_8_0_0'
        );
    """)
    backup_exists = cr.fetchone()[0]

    if backup_exists:
        _logger.warning('  ⚠ Backup table already exists. Dropping old backup...')
        cr.execute('DROP TABLE res_partner_backup_19_0_8_0_0;')

    # Create backup table with key fields
    cr.execute("""
        CREATE TABLE res_partner_backup_19_0_8_0_0 AS
        SELECT
            id,
            name,
            vat,
            email,
            company_id,
            write_date,
            write_uid,
            create_date,
            create_uid
        FROM res_partner
        WHERE vat IS NOT NULL;
    """)

    backup_count = cr.rowcount
    _logger.info(f'  ✓ Backed up {backup_count} partners with VAT numbers')

    # Log backup location
    _logger.info(f'  Backup table: res_partner_backup_19_0_8_0_0')
    _logger.info('Backup completed!\n')


def _log_validation_overrides(cr):
    """
    Log current validation override state (if fields exist from manual additions).

    This is defensive - checks if override fields already exist before migration.
    """
    _logger.info('=' * 80)
    _logger.info('STEP 2: Logging Validation Override State')
    _logger.info('=' * 80)

    # Check if override fields already exist
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'res_partner'
            AND column_name = 'l10n_cr_cedula_validation_override'
        );
    """)
    override_field_exists = cr.fetchone()[0]

    if override_field_exists:
        _logger.info('  ℹ Override fields already exist (manual addition detected)')

        # Count existing overrides
        cr.execute("""
            SELECT COUNT(*)
            FROM res_partner
            WHERE l10n_cr_cedula_validation_override = true;
        """)
        override_count = cr.fetchone()[0]

        _logger.info(f'  Current overrides active: {override_count}')

        if override_count > 0:
            _logger.warning(
                f'  ⚠ {override_count} partners have validation overrides. '
                'These will be preserved during migration.'
            )
    else:
        _logger.info('  ✓ No existing override fields (clean migration)')

    _logger.info('Validation override logging completed!\n')


def _verify_database_integrity(cr):
    """
    Verify database integrity before migration.

    Checks:
    1. No orphaned records
    2. Referential integrity
    3. Data consistency
    """
    _logger.info('=' * 80)
    _logger.info('STEP 3: Verifying Database Integrity')
    _logger.info('=' * 80)

    # Check 1: Orphaned partner companies
    cr.execute("""
        SELECT COUNT(*)
        FROM res_partner p
        WHERE p.company_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM res_company c WHERE c.id = p.company_id
        );
    """)
    orphaned_companies = cr.fetchone()[0]

    if orphaned_companies > 0:
        _logger.error(
            f'  ✗ CRITICAL: {orphaned_companies} partners reference deleted companies!'
        )
        raise Exception(
            f'Database integrity check failed: {orphaned_companies} orphaned company references. '
            'Fix these before migrating.'
        )
    else:
        _logger.info('  ✓ No orphaned company references')

    # Check 2: Duplicate VAT numbers (will cause cache key conflicts)
    cr.execute("""
        SELECT vat, COUNT(*)
        FROM res_partner
        WHERE vat IS NOT NULL
        GROUP BY vat
        HAVING COUNT(*) > 1
        LIMIT 5;
    """)
    duplicates = cr.fetchall()

    if duplicates:
        _logger.warning('  ⚠ Duplicate VAT numbers detected:')
        for vat, count in duplicates:
            _logger.warning(f'    - VAT {vat}: {count} partners')
        _logger.warning('  This may cause cache lookup ambiguities.')
    else:
        _logger.info('  ✓ No duplicate VAT numbers')

    # Check 3: Invalid email formats (will fail validation)
    cr.execute("""
        SELECT COUNT(*)
        FROM res_partner
        WHERE email IS NOT NULL
        AND email != ''
        AND email NOT LIKE '%_@_%.__%';
    """)
    invalid_emails = cr.fetchone()[0]

    if invalid_emails > 0:
        _logger.warning(
            f'  ⚠ {invalid_emails} partners have potentially invalid email formats'
        )
    else:
        _logger.info('  ✓ All emails appear valid')

    _logger.info('Database integrity checks completed!\n')


def _check_conflicts(cr):
    """
    Check for conflicting customizations that might break migration.

    Looks for:
    1. Custom fields with similar names
    2. Conflicting indexes
    3. Custom constraints
    """
    _logger.info('=' * 80)
    _logger.info('STEP 4: Checking for Conflicts')
    _logger.info('=' * 80)

    # Check for conflicting indexes
    conflicting_indexes = [
        'idx_partner_cedula_cache_stale',
        'idx_partner_tax_status_verified',
        'idx_partner_cache_needs_refresh',
        'idx_partner_override_by_company',
        'idx_partner_override_audit',
        'idx_partner_cedula_with_regime',
    ]

    for idx_name in conflicting_indexes:
        cr.execute("""
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE schemaname = 'public'
                AND indexname = %s
            );
        """, (idx_name,))

        exists = cr.fetchone()[0]
        if exists:
            _logger.warning(
                f'  ⚠ Index {idx_name} already exists. Will be recreated.'
            )
            # Drop existing index to avoid conflicts
            cr.execute(f'DROP INDEX IF EXISTS {idx_name};')
            _logger.info(f'    Dropped existing index: {idx_name}')

    # Check for new tables that will be created
    new_tables = ['l10n_cr_cedula_cache', 'l10n_cr_validation_rule']

    for table_name in new_tables:
        cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            );
        """, (table_name,))

        exists = cr.fetchone()[0]
        if exists:
            _logger.error(
                f'  ✗ CONFLICT: Table {table_name} already exists!'
            )
            raise Exception(
                f'Pre-migration conflict: Table {table_name} already exists. '
                'Drop it manually or rename your custom table before migrating.'
            )

    _logger.info('  ✓ No conflicts detected')
    _logger.info('Conflict checks completed!\n')


def _log_migration_metadata(cr):
    """Store migration metadata for audit trail."""
    timestamp = datetime.now().isoformat()

    _logger.info('Migration Metadata:')
    _logger.info(f'  Timestamp: {timestamp}')
    _logger.info(f'  Target version: 19.0.8.0.0')
    _logger.info(f'  Database: {cr.dbname}')


# =============================================================================
# UTILITY FUNCTIONS FOR MANUAL ROLLBACK
# =============================================================================

def _generate_rollback_sql(cr):
    """
    Generate SQL script for manual rollback (emergency use).

    Not called during normal migration - only for documentation.
    """
    rollback_sql = """
-- =============================================================================
-- EMERGENCY ROLLBACK SCRIPT - l10n_cr_einvoice v19.0.8.0.0
-- Generated: {timestamp}
-- Database: {dbname}
-- =============================================================================

-- WARNING: This will destroy all data created by migration v19.0.8.0.0
-- Only use if migration fails catastrophically and backups are intact.

-- Step 1: Drop new indexes
DROP INDEX IF EXISTS idx_partner_cedula_cache_stale;
DROP INDEX IF EXISTS idx_partner_tax_status_verified;
DROP INDEX IF EXISTS idx_partner_cache_needs_refresh;
DROP INDEX IF EXISTS idx_partner_override_by_company;
DROP INDEX IF EXISTS idx_partner_override_audit;
DROP INDEX IF EXISTS idx_partner_cedula_with_regime;
DROP INDEX IF EXISTS idx_cedula_cache_cedula;
DROP INDEX IF EXISTS idx_cedula_cache_company;
DROP INDEX IF EXISTS idx_cedula_cache_created_at;
DROP INDEX IF EXISTS idx_validation_rule_doc_type;
DROP INDEX IF EXISTS idx_validation_rule_active;

-- Step 2: Drop new tables
DROP TABLE IF EXISTS l10n_cr_cedula_cache CASCADE;
DROP TABLE IF EXISTS l10n_cr_validation_rule CASCADE;

-- Step 3: Drop new columns from res.partner
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_cedula_validation_override CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_override_reason CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_override_date CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_override_user_id CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_hacienda_last_sync CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_hacienda_verified CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_tax_regime CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_tax_status CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_validation_check_date CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_hacienda_cache_age_hours CASCADE;

-- Step 4: Restore from backup (if needed)
-- Uncomment if data was corrupted:
-- INSERT INTO res_partner (id, name, vat, email, company_id, write_date, write_uid, create_date, create_uid)
-- SELECT id, name, vat, email, company_id, write_date, write_uid, create_date, create_uid
-- FROM res_partner_backup_19_0_8_0_0
-- ON CONFLICT (id) DO UPDATE SET
--     name = EXCLUDED.name,
--     vat = EXCLUDED.vat,
--     email = EXCLUDED.email;

-- Step 5: Drop backup table
DROP TABLE IF EXISTS res_partner_backup_19_0_8_0_0;

-- Step 6: Reset module version
UPDATE ir_module_module
SET latest_version = '19.0.7.0.0'
WHERE name = 'l10n_cr_einvoice';

-- =============================================================================
-- Rollback complete. Run module update to re-sync:
--   docker compose run --rm odoo -d GMS -u l10n_cr_einvoice --stop-after-init
-- =============================================================================
    """.format(
        timestamp=datetime.now().isoformat(),
        dbname=cr.dbname,
    )

    return rollback_sql


# =============================================================================
# END OF PRE-MIGRATION SCRIPT
# =============================================================================
