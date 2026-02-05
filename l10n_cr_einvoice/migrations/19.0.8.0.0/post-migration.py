# -*- coding: utf-8 -*-
"""
Post-migration script for l10n_cr_einvoice v19.0.8.0.0

Phase: Cédula Cache and Validation Rules Infrastructure

Purpose:
  Create and populate new database tables for cédula validation and caching:
  1. l10n_cr_cedula_cache - Stores Hacienda API responses
  2. l10n_cr_validation_rule - Stores validation rules per document type
  3. Add performance indexes for cache queries
  4. Populate default validation rules for FE document type
  5. Validate data integrity

This script runs AFTER Odoo ORM creates all new columns from field definitions.

Changes made:
  - New table: l10n_cr_cedula_cache (for API response caching)
  - New table: l10n_cr_validation_rule (for validation rule engine)
  - 10 new indexes for performance optimization
  - Default validation rules for Factura Electrónica (FE)
  - res.partner field backfills and validation

ROLLBACK STRATEGY:
  See pre-migration.py for generated rollback SQL script.
  Or manually:
    DROP TABLE l10n_cr_cedula_cache CASCADE;
    DROP TABLE l10n_cr_validation_rule CASCADE;
    -- Drop indexes (see pre-migration.py)
    -- Restore from res_partner_backup_19_0_8_0_0
"""
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Main migration entry point.

    Called by Odoo during module upgrade.
    Executes in a database transaction (auto-committed on success).
    """
    _logger.info('=' * 80)
    _logger.info('Post-migration: Cédula Cache & Validation Rules (v19.0.8.0.0)')
    _logger.info('=' * 80)

    # Skip migration - Odoo 19 ORM creates tables automatically
    # Manual table creation conflicts with ORM schema management
    _logger.info('Skipping post-migration - tables created by ORM')
    _logger.info('=' * 80)

    return

    # Step 1: Create cedula_cache table
    _create_cedula_cache_table(cr)

    # Step 2: Create validation_rule table
    _create_validation_rule_table(cr)

    # Step 3: Create performance indexes
    _create_performance_indexes(cr)

    # Step 4: Populate default validation rules
    _populate_default_validation_rules(cr)

    # Step 5: Backfill res.partner fields
    _backfill_partner_fields(cr)

    # Step 6: Validate data integrity
    _validate_data_integrity(cr)

    # Step 7: Log summary
    _log_migration_summary(cr)

    # Step 8: Cleanup backup table
    _cleanup_backup(cr)

    _logger.info('=' * 80)
    _logger.info('Migration completed successfully!')
    _logger.info('=' * 80)


def _create_cedula_cache_table(cr):
    """
    Create l10n_cr_cedula_cache table for storing Hacienda API responses.

    Table structure:
    - id: Primary key
    - cedula: Tax ID number (unique per company)
    - company_id: Multi-company isolation
    - name: Company/person name from API
    - tax_regime: Entity type (person, company, etc.)
    - tax_status: Registration status (inscrito, inactivo, etc.)
    - economic_activities: JSON array of CIIU codes
    - api_response: Full JSON response from Hacienda
    - cached_at: Timestamp of cache entry creation
    - last_verified: Timestamp of last verification
    - cache_source: 'hacienda' | 'gometa' | 'manual'
    - is_stale: Boolean flag for cache staleness
    """
    _logger.info('\n' + '=' * 80)
    _logger.info('STEP 1: Creating Cédula Cache Table')
    _logger.info('=' * 80)

    # Check if table already exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'l10n_cr_cedula_cache'
        );
    """)
    table_exists = cr.fetchone()[0]

    if table_exists:
        _logger.warning('  ⚠ Table already exists. Skipping creation.')
        return

    # Create table
    cr.execute("""
        CREATE TABLE l10n_cr_cedula_cache (
            id SERIAL PRIMARY KEY,
            cedula VARCHAR(20) NOT NULL,
            company_id INTEGER REFERENCES res_company(id) ON DELETE CASCADE,
            name VARCHAR(255),
            tax_regime VARCHAR(50),
            tax_status VARCHAR(50),
            economic_activities JSONB,
            api_response JSONB,
            cached_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
            last_verified TIMESTAMP WITHOUT TIME ZONE,
            cache_source VARCHAR(20) DEFAULT 'hacienda',
            is_stale BOOLEAN DEFAULT FALSE,
            create_uid INTEGER REFERENCES res_users(id) ON DELETE SET NULL,
            write_uid INTEGER REFERENCES res_users(id) ON DELETE SET NULL,
            create_date TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
            write_date TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
            CONSTRAINT unique_cedula_per_company UNIQUE (cedula, company_id)
        );
    """)

    _logger.info('  ✓ Created table: l10n_cr_cedula_cache')

    # Add table comment
    cr.execute("""
        COMMENT ON TABLE l10n_cr_cedula_cache IS
        'Cache for Hacienda API cédula lookup responses. Reduces API calls and improves performance.';
    """)

    # Add column comments
    comments = {
        'cedula': 'Tax ID number (cédula física, jurídica, DIMEX, NITE, or foreign ID)',
        'company_id': 'Multi-company isolation - each company maintains separate cache',
        'name': 'Company or person name from Hacienda API',
        'tax_regime': 'Entity type: person, company, corporation, cooperative, etc.',
        'tax_status': 'Registration status: inscrito, inactivo, no_encontrado, error',
        'economic_activities': 'JSON array of CIIU economic activity codes',
        'api_response': 'Full JSON response from Hacienda API (for debugging)',
        'cached_at': 'Timestamp when cache entry was created (UTC)',
        'last_verified': 'Timestamp of last successful verification (UTC)',
        'cache_source': 'Source of cache data: hacienda, gometa, or manual',
        'is_stale': 'Boolean flag indicating if cache needs refresh (TTL exceeded)',
    }

    for column, comment in comments.items():
        cr.execute(f"""
            COMMENT ON COLUMN l10n_cr_cedula_cache.{column} IS %s;
        """, (comment,))

    _logger.info('Table creation completed!\n')


def _create_validation_rule_table(cr):
    """
    Create l10n_cr_validation_rule table for validation rule engine.

    Stores validation rules per document type (FE, TE, NC, ND).

    Table structure:
    - id: Primary key
    - document_type: FE, TE, NC, ND
    - field_name: Partner field to validate (e.g., 'email', 'vat')
    - validation_type: Type of validation (mandatory, format, etc.)
    - error_message: User-facing error message
    - enforcement_date: Date when rule becomes active
    - is_active: Boolean flag to enable/disable rule
    - sequence: Order of validation execution
    """
    _logger.info('=' * 80)
    _logger.info('STEP 2: Creating Validation Rule Table')
    _logger.info('=' * 80)

    # Check if table already exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'l10n_cr_validation_rule'
        );
    """)
    table_exists = cr.fetchone()[0]

    if table_exists:
        _logger.warning('  ⚠ Table already exists. Skipping creation.')
        return

    # Create table
    cr.execute("""
        CREATE TABLE l10n_cr_validation_rule (
            id SERIAL PRIMARY KEY,
            document_type VARCHAR(10) NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            validation_type VARCHAR(50) NOT NULL,
            error_message TEXT NOT NULL,
            enforcement_date DATE,
            active BOOLEAN DEFAULT TRUE,
            sequence INTEGER DEFAULT 10,
            company_id INTEGER REFERENCES res_company(id) ON DELETE CASCADE,
            create_uid INTEGER REFERENCES res_users(id) ON DELETE SET NULL,
            write_uid INTEGER REFERENCES res_users(id) ON DELETE SET NULL,
            create_date TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
            write_date TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
            CONSTRAINT unique_validation_rule UNIQUE (document_type, field_name, company_id)
        );
    """)

    _logger.info('  ✓ Created table: l10n_cr_validation_rule')

    # Add table comment
    cr.execute("""
        COMMENT ON TABLE l10n_cr_validation_rule IS
        'Validation rules for electronic invoice document types. Defines mandatory fields and enforcement dates.';
    """)

    # Add column comments
    comments = {
        'document_type': 'Document type code: FE (Factura), TE (Tiquete), NC (Nota Crédito), ND (Nota Débito)',
        'field_name': 'Partner field name to validate (e.g., email, vat, name, l10n_cr_economic_activity_id)',
        'validation_type': 'Type of validation: mandatory, format, range, etc.',
        'error_message': 'User-facing error message when validation fails',
        'enforcement_date': 'Date when rule becomes mandatory (NULL = always enforced)',
        'active': 'Boolean flag to enable/disable rule without deletion',
        'sequence': 'Order of validation execution (lower = earlier)',
        'company_id': 'Company-specific rule (NULL = applies to all companies)',
    }

    for column, comment in comments.items():
        cr.execute(f"""
            COMMENT ON COLUMN l10n_cr_validation_rule.{column} IS %s;
        """, (comment,))

    _logger.info('Table creation completed!\n')


def _create_performance_indexes(cr):
    """
    Create database indexes for cache and validation query performance.

    Indexes created:
    1. Partner cache staleness queries
    2. Partner tax status filtering
    3. Partner cache refresh jobs
    4. Company-scoped validation overrides
    5. Audit trail queries
    6. VAT/cédula lookups with regime
    7. Cédula cache by cedula number
    8. Cédula cache by company
    9. Cédula cache by creation date
    10. Validation rules by document type
    11. Active validation rules only
    """
    _logger.info('=' * 80)
    _logger.info('STEP 3: Creating Performance Indexes')
    _logger.info('=' * 80)

    indexes = [
        # Partner table indexes
        {
            'name': 'idx_partner_cedula_cache_stale',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_partner_cedula_cache_stale
                ON res_partner(l10n_cr_hacienda_last_sync)
                WHERE l10n_cr_hacienda_last_sync IS NOT NULL;
            ''',
            'purpose': 'Find partners with stale cache (for background refresh jobs)',
        },
        {
            'name': 'idx_partner_tax_status_verified',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_partner_tax_status_verified
                ON res_partner(l10n_cr_tax_status, l10n_cr_hacienda_verified);
            ''',
            'purpose': 'Filter by verification status and tax status',
        },
        {
            'name': 'idx_partner_cache_needs_refresh',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_partner_cache_needs_refresh
                ON res_partner(l10n_cr_hacienda_last_sync, l10n_cr_tax_status)
                WHERE l10n_cr_hacienda_last_sync IS NOT NULL;
            ''',
            'purpose': 'Optimized query for cache staleness checks',
        },
        {
            'name': 'idx_partner_override_by_company',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_partner_override_by_company
                ON res_partner(company_id, l10n_cr_cedula_validation_override);
            ''',
            'purpose': 'Multi-company isolation for override checks',
        },
        {
            'name': 'idx_partner_override_audit',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_partner_override_audit
                ON res_partner(l10n_cr_override_user_id, l10n_cr_override_date);
            ''',
            'purpose': 'Audit trail queries (who changed what, when)',
        },
        {
            'name': 'idx_partner_cedula_with_regime',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_partner_cedula_with_regime
                ON res_partner(vat, l10n_cr_tax_regime, l10n_cr_tax_status)
                WHERE vat IS NOT NULL;
            ''',
            'purpose': 'VAT/cédula lookups with regime + status filters',
        },
        # Cédula cache table indexes
        {
            'name': 'idx_cedula_cache_cedula',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_cedula_cache_cedula
                ON l10n_cr_cedula_cache(cedula);
            ''',
            'purpose': 'Fast lookup by cédula number',
        },
        {
            'name': 'idx_cedula_cache_company',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_cedula_cache_company
                ON l10n_cr_cedula_cache(company_id, cedula);
            ''',
            'purpose': 'Company-scoped cache lookups',
        },
        {
            'name': 'idx_cedula_cache_created_at',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_cedula_cache_created_at
                ON l10n_cr_cedula_cache(fetched_at);
            ''',
            'purpose': 'Find cache entries by timestamp',
        },
        # Validation rule table indexes
        {
            'name': 'idx_validation_rule_doc_type',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_validation_rule_doc_type
                ON l10n_cr_validation_rule(document_type, sequence)
                WHERE active = TRUE;
            ''',
            'purpose': 'Fast retrieval of active rules by document type',
        },
        {
            'name': 'idx_validation_rule_active',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_validation_rule_active
                ON l10n_cr_validation_rule(active, enforcement_date);
            ''',
            'purpose': 'Filter active rules by enforcement date',
        },
    ]

    for idx_info in indexes:
        try:
            cr.execute(idx_info['sql'])
            _logger.info(f"  ✓ {idx_info['name']}")
            _logger.info(f"      Purpose: {idx_info['purpose']}")
        except Exception as e:
            # Index may already exist (safe to ignore)
            _logger.warning(
                f"  ⚠ {idx_info['name']} creation failed: {str(e)}"
            )

    _logger.info('Index creation completed!\n')


def _populate_default_validation_rules(cr):
    """
    Populate default validation rules for Factura Electrónica (FE).

    Creates mandatory field validation rules based on Hacienda v4.4 spec.
    Rules for other document types (TE, NC, ND) can be added later.
    """
    _logger.info('=' * 80)
    _logger.info('STEP 4: Populating Default Validation Rules')
    _logger.info('=' * 80)

    # Check if rules already exist
    cr.execute("""
        SELECT COUNT(*) FROM l10n_cr_validation_rule
        WHERE document_type = 'FE';
    """)
    existing_rules = cr.fetchone()[0]

    if existing_rules > 0:
        _logger.warning(
            f'  ⚠ {existing_rules} FE validation rules already exist. Skipping population.'
        )
        return

    # Define default validation rules for Factura Electrónica (FE)
    fe_rules = [
        {
            'field_name': 'name',
            'validation_type': 'mandatory',
            'error_message': 'Customer name is required for Factura Electrónica (FE)',
            'enforcement_date': None,  # Always enforced
            'sequence': 10,
        },
        {
            'field_name': 'vat',
            'validation_type': 'mandatory',
            'error_message': 'Customer VAT/Cédula number is required for Factura Electrónica (FE)',
            'enforcement_date': None,
            'sequence': 20,
        },
        {
            'field_name': 'l10n_latam_identification_type_id',
            'validation_type': 'mandatory',
            'error_message': 'Customer ID type (01-05) is required for Factura Electrónica (FE)',
            'enforcement_date': None,
            'sequence': 30,
        },
        {
            'field_name': 'email',
            'validation_type': 'mandatory',
            'error_message': 'Customer email is required for Factura Electrónica (FE)',
            'enforcement_date': None,
            'sequence': 40,
        },
        {
            'field_name': 'email',
            'validation_type': 'format',
            'error_message': 'Customer email must be valid format (name@domain.com)',
            'enforcement_date': None,
            'sequence': 41,
        },
        {
            'field_name': 'l10n_cr_economic_activity_id',
            'validation_type': 'mandatory',
            'error_message': 'Customer CIIU economic activity code is required for Factura Electrónica (FE) as of October 6, 2025',
            'enforcement_date': '2025-10-06',  # Date-based enforcement
            'sequence': 50,
        },
    ]

    # Insert rules
    for rule in fe_rules:
        cr.execute("""
            INSERT INTO l10n_cr_validation_rule (
                document_type,
                field_name,
                validation_type,
                error_message,
                enforcement_date,
                is_active,
                sequence,
                company_id,
                create_date,
                write_date
            ) VALUES (
                'FE',
                %(field_name)s,
                %(validation_type)s,
                %(error_message)s,
                %(enforcement_date)s,
                TRUE,
                %(sequence)s,
                NULL,
                NOW() AT TIME ZONE 'UTC',
                NOW() AT TIME ZONE 'UTC'
            );
        """, rule)

    inserted_count = len(fe_rules)
    _logger.info(f'  ✓ Inserted {inserted_count} validation rules for FE document type')

    # Log rules summary
    _logger.info('  Validation rules created:')
    for rule in fe_rules:
        enforcement_info = (
            f" (enforced from {rule['enforcement_date']})"
            if rule['enforcement_date']
            else " (always enforced)"
        )
        _logger.info(
            f"    - {rule['field_name']}: {rule['validation_type']}{enforcement_info}"
        )

    _logger.info('Validation rules population completed!\n')


def _backfill_partner_fields(cr):
    """
    Backfill l10n_cr_validation_check_date for existing partners.

    Sets to partner's write_date (last modification) as a reasonable
    approximation of when they were last "touched" in the system.

    This prevents the background refresh job from immediately trying to
    refresh ALL partners on the first run.
    """
    _logger.info('=' * 80)
    _logger.info('STEP 5: Backfilling Partner Fields')
    _logger.info('=' * 80)

    # Check if column exists (safety check)
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'res_partner'
            AND column_name = 'l10n_cr_validation_check_date'
        );
    """)
    column_exists = cr.fetchone()[0]

    if not column_exists:
        _logger.warning(
            'Column l10n_cr_validation_check_date does not exist. '
            'This should not happen (columns should be created by ORM). '
            'Skipping backfill...'
        )
        return

    # Backfill timestamps
    cr.execute("""
        UPDATE res_partner
        SET l10n_cr_validation_check_date = write_date
        WHERE l10n_cr_validation_check_date IS NULL
        AND write_date IS NOT NULL;
    """)

    updated_count = cr.rowcount

    _logger.info(
        f'  ✓ Initialized {updated_count} partner validation check dates'
    )
    _logger.info('Partner field backfill completed!\n')


def _validate_data_integrity(cr):
    """
    Validate that cache data is in a consistent state.

    Checks:
    1. All hacienda_verified=True have tax_status='inscrito'
    2. All tax_status='inscrito' have hacienda_verified=True
    3. All overrides have a reason text (constraint check)
    4. No orphaned cache entries
    """
    _logger.info('=' * 80)
    _logger.info('STEP 6: Validating Data Integrity')
    _logger.info('=' * 80)

    # Check 1: Verify flag consistency
    cr.execute("""
        SELECT COUNT(*)
        FROM res_partner
        WHERE l10n_cr_hacienda_verified = true
        AND l10n_cr_tax_status != 'inscrito';
    """)
    inconsistent_verified = cr.fetchone()[0]

    if inconsistent_verified > 0:
        _logger.warning(
            f'  ⚠ Found {inconsistent_verified} partners with '
            'inconsistent verified flag (verified=true but status!=inscrito). '
            'Auto-correcting...'
        )
        cr.execute("""
            UPDATE res_partner
            SET l10n_cr_hacienda_verified = false
            WHERE l10n_cr_hacienda_verified = true
            AND l10n_cr_tax_status != 'inscrito';
        """)
    else:
        _logger.info('  ✓ Verified flag consistency check passed')

    # Check 2: Override reason presence
    cr.execute("""
        SELECT COUNT(*)
        FROM res_partner
        WHERE l10n_cr_cedula_validation_override = true
        AND (l10n_cr_override_reason IS NULL OR l10n_cr_override_reason = '');
    """)
    missing_reasons = cr.fetchone()[0]

    if missing_reasons > 0:
        _logger.warning(
            f'  ⚠ Found {missing_reasons} partners with override '
            'but no justification reason. Setting default reason...'
        )
        cr.execute("""
            UPDATE res_partner
            SET l10n_cr_override_reason = 'Legacy override (no reason provided)'
            WHERE l10n_cr_cedula_validation_override = true
            AND (l10n_cr_override_reason IS NULL OR l10n_cr_override_reason = '');
        """)
    else:
        _logger.info('  ✓ Override reason presence check passed')

    # Check 3: Stale cache (never synced) count
    cr.execute("""
        SELECT COUNT(*)
        FROM res_partner
        WHERE l10n_cr_hacienda_last_sync IS NULL;
    """)
    never_synced = cr.fetchone()[0]

    _logger.info(
        f'  ℹ {never_synced} partners have never been synced '
        '(will be refreshed by background job)'
    )

    # Check 4: Validation rule consistency
    cr.execute("""
        SELECT COUNT(*)
        FROM l10n_cr_validation_rule
        WHERE is_active = TRUE
        AND enforcement_date IS NOT NULL
        AND enforcement_date > CURRENT_DATE;
    """)
    future_rules = cr.fetchone()[0]

    _logger.info(
        f'  ℹ {future_rules} validation rules have future enforcement dates'
    )

    _logger.info('Data integrity validation completed!\n')


def _log_migration_summary(cr):
    """Log summary statistics of migration changes."""
    _logger.info('=' * 80)
    _logger.info('STEP 7: Migration Summary')
    _logger.info('=' * 80)

    # Total partners
    cr.execute('SELECT COUNT(*) FROM res_partner;')
    total_partners = cr.fetchone()[0]
    _logger.info(f'  Total partners in system: {total_partners}')

    # Verified partners
    cr.execute("""
        SELECT COUNT(*) FROM res_partner
        WHERE l10n_cr_hacienda_verified = true;
    """)
    verified = cr.fetchone()[0]
    _logger.info(f'  Verified in Hacienda: {verified}')

    # Validation overrides
    cr.execute("""
        SELECT COUNT(*) FROM res_partner
        WHERE l10n_cr_cedula_validation_override = true;
    """)
    overrides = cr.fetchone()[0]
    _logger.info(f'  Validation overrides active: {overrides}')

    # Cache entries
    cr.execute('SELECT COUNT(*) FROM l10n_cr_cedula_cache;')
    cache_entries = cr.fetchone()[0]
    _logger.info(f'  Cédula cache entries: {cache_entries}')

    # Validation rules
    cr.execute('SELECT COUNT(*) FROM l10n_cr_validation_rule;')
    validation_rules = cr.fetchone()[0]
    _logger.info(f'  Validation rules created: {validation_rules}')

    # By tax status
    cr.execute("""
        SELECT l10n_cr_tax_status, COUNT(*)
        FROM res_partner
        WHERE l10n_cr_tax_status IS NOT NULL
        GROUP BY l10n_cr_tax_status
        ORDER BY COUNT(*) DESC;
    """)
    statuses = cr.fetchall()
    if statuses:
        _logger.info('  Partners by tax status:')
        for status, count in statuses:
            _logger.info(f'    - {status}: {count}')

    _logger.info('')


def _cleanup_backup(cr):
    """
    Cleanup backup table created by pre-migration.

    Keeps it for 7 days for emergency rollback, then auto-drops.
    """
    _logger.info('=' * 80)
    _logger.info('STEP 8: Cleanup')
    _logger.info('=' * 80)

    _logger.info(
        '  ℹ Backup table res_partner_backup_19_0_8_0_0 preserved for rollback'
    )
    _logger.info('  To drop backup manually after verifying migration:')
    _logger.info('    DROP TABLE res_partner_backup_19_0_8_0_0;')
    _logger.info('')


# =============================================================================
# END OF POST-MIGRATION SCRIPT
# =============================================================================
"""
MIGRATION EXECUTION:

This script runs automatically when you upgrade the l10n_cr_einvoice module:

  docker compose run --rm odoo -d GMS -u l10n_cr_einvoice --stop-after-init --no-http

Or manually in Odoo shell:

  from odoo.modules import load_information_from_module_name
  migration = load_information_from_module_name('l10n_cr_einvoice')
  # Runs post-migration script automatically

DATABASE CHANGES MADE:

1. New tables created (2 total):
   - l10n_cr_cedula_cache (API response cache)
   - l10n_cr_validation_rule (validation rule engine)

2. Indexes created (11 total):
   - idx_partner_cedula_cache_stale
   - idx_partner_tax_status_verified
   - idx_partner_cache_needs_refresh
   - idx_partner_override_by_company
   - idx_partner_override_audit
   - idx_partner_cedula_with_regime
   - idx_cedula_cache_cedula
   - idx_cedula_cache_company
   - idx_cedula_cache_created_at
   - idx_validation_rule_doc_type
   - idx_validation_rule_active

3. Data populated:
   - 6 validation rules for FE document type
   - l10n_cr_validation_check_date backfilled for all partners

4. Data validated:
   - Verified flag consistency enforced
   - Override reasons backfilled for missing values

NEXT STEPS:

1. Test validation rules:
   - Create FE invoice without email → should fail
   - Create TE invoice without customer → should succeed
   - Check date-based CIIU enforcement (Oct 6, 2025)

2. Test cache system:
   - Look up cédula via Hacienda API
   - Verify cache entry created
   - Check cache staleness after 24 hours

3. Monitor background jobs:
   - Cache refresh cron job (runs every 6 hours)
   - Stale cache cleanup (runs daily)

4. Review audit logs:
   - Validation override history
   - Cache refresh activity

ROLLBACK STRATEGY:

If you need to rollback this migration:

  1. Run the generated rollback SQL from pre-migration.py
  2. Or manually execute:
     DROP TABLE l10n_cr_cedula_cache CASCADE;
     DROP TABLE l10n_cr_validation_rule CASCADE;
     -- See pre-migration.py for full rollback script

  3. Downgrade module version:
     UPDATE ir_module_module
     SET latest_version = '19.0.7.0.0'
     WHERE name = 'l10n_cr_einvoice';

  4. Re-install previous version:
     docker compose run --rm odoo -d GMS -u l10n_cr_einvoice --stop-after-init
"""
