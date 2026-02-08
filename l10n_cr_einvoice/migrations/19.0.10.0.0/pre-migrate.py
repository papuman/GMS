# -*- coding: utf-8 -*-
"""
Pre-migration script for version 19.0.10.0.0

Creates two core infrastructure tables:
1. l10n_cr_cedula_cache - Hacienda API data caching (multi-tier strategy)
2. l10n_cr_hacienda_rate_limit_state - Rate limiter state (token bucket algorithm)

Part of: GMS E-Invoice Validation & Cédula Lookup System
Reference: models/cedula_cache.py, utils/rate_limiter.py
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Create cédula cache table and rate limiter state table.

    Args:
        cr: Database cursor
        version: Current module version
    """
    _logger.info('Running pre-migration for l10n_cr_einvoice 19.0.10.0.0')

    # ========================================================================
    # PART 1: Create cédula cache table
    # ========================================================================
    _create_cedula_cache_table(cr)

    # ========================================================================
    # PART 2: Create rate limiter state table
    # ========================================================================
    _create_rate_limiter_table(cr)

    _logger.info('Pre-migration for l10n_cr_einvoice 19.0.10.0.0 completed successfully')


def _create_cedula_cache_table(cr):
    """
    Create cédula cache table with all fields, indexes, and constraints.

    Args:
        cr: Database cursor
    """
    _logger.info('Processing cédula cache table creation')

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
        _logger.info('Table l10n_cr_cedula_cache already exists - skipping migration')
        return

    _logger.info('Creating l10n_cr_cedula_cache table')

    # Create the table with all fields
    cr.execute("""
        CREATE TABLE l10n_cr_cedula_cache (
            id SERIAL PRIMARY KEY,

            -- Core identification fields
            cedula VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            company_type VARCHAR DEFAULT 'other',
            tax_regime VARCHAR,
            tax_status VARCHAR NOT NULL DEFAULT 'inscrito',

            -- Economic activities (CIIU codes)
            economic_activities TEXT,
            primary_activity VARCHAR,
            ciiu_code_id INTEGER,

            -- Cache management fields
            cache_tier VARCHAR,
            fetched_at TIMESTAMP NOT NULL,
            refreshed_at TIMESTAMP NOT NULL,
            access_count INTEGER DEFAULT 0,
            last_access_at TIMESTAMP,

            -- Cache age computed fields (stored)
            cache_age_hours NUMERIC,
            cache_age_days INTEGER,

            -- Metadata fields
            source VARCHAR DEFAULT 'hacienda',
            raw_response TEXT,
            error_message TEXT,
            company_id INTEGER NOT NULL,

            -- Odoo standard fields
            create_uid INTEGER,
            create_date TIMESTAMP,
            write_uid INTEGER,
            write_date TIMESTAMP
        );
    """)

    _logger.info('Table l10n_cr_cedula_cache created successfully')

    # Add foreign key constraints
    _logger.info('Adding foreign key constraints')

    # FK to res_company
    cr.execute("""
        ALTER TABLE l10n_cr_cedula_cache
        ADD CONSTRAINT l10n_cr_cedula_cache_company_id_fkey
        FOREIGN KEY (company_id)
        REFERENCES res_company(id)
        ON DELETE CASCADE;
    """)

    # FK to l10n_cr_ciiu_code (nullable)
    cr.execute("""
        ALTER TABLE l10n_cr_cedula_cache
        ADD CONSTRAINT l10n_cr_cedula_cache_ciiu_code_id_fkey
        FOREIGN KEY (ciiu_code_id)
        REFERENCES l10n_cr_ciiu_code(id)
        ON DELETE SET NULL;
    """)

    # FK to res_users for create/write tracking
    cr.execute("""
        ALTER TABLE l10n_cr_cedula_cache
        ADD CONSTRAINT l10n_cr_cedula_cache_create_uid_fkey
        FOREIGN KEY (create_uid)
        REFERENCES res_users(id)
        ON DELETE SET NULL;
    """)

    cr.execute("""
        ALTER TABLE l10n_cr_cedula_cache
        ADD CONSTRAINT l10n_cr_cedula_cache_write_uid_fkey
        FOREIGN KEY (write_uid)
        REFERENCES res_users(id)
        ON DELETE SET NULL;
    """)

    _logger.info('Foreign key constraints added successfully')

    # Add unique constraint: (cedula, company_id)
    _logger.info('Adding unique constraint')

    cr.execute("""
        ALTER TABLE l10n_cr_cedula_cache
        ADD CONSTRAINT cedula_company_unique
        UNIQUE (cedula, company_id);
    """)

    _logger.info('Unique constraint added successfully')

    # Add indexes for performance
    _logger.info('Creating indexes')

    # Index 1: cedula (for lookups)
    cr.execute("""
        CREATE INDEX l10n_cr_cedula_cache_cedula_idx
        ON l10n_cr_cedula_cache (cedula);
    """)

    # Index 2: name (for searches)
    cr.execute("""
        CREATE INDEX l10n_cr_cedula_cache_name_idx
        ON l10n_cr_cedula_cache (name);
    """)

    # Index 3: tax_status (for filtering active entries)
    cr.execute("""
        CREATE INDEX l10n_cr_cedula_cache_tax_status_idx
        ON l10n_cr_cedula_cache (tax_status);
    """)

    # Index 4: fetched_at (for cache age queries)
    cr.execute("""
        CREATE INDEX l10n_cr_cedula_cache_fetched_at_idx
        ON l10n_cr_cedula_cache (fetched_at);
    """)

    # Index 5: refreshed_at (for stale entry queries)
    cr.execute("""
        CREATE INDEX l10n_cr_cedula_cache_refreshed_at_idx
        ON l10n_cr_cedula_cache (refreshed_at);
    """)

    # Index 6: company_id (for multi-company filtering)
    cr.execute("""
        CREATE INDEX l10n_cr_cedula_cache_company_id_idx
        ON l10n_cr_cedula_cache (company_id);
    """)

    _logger.info('All 6 indexes created successfully')

    # Add comment to table for documentation
    cr.execute("""
        COMMENT ON TABLE l10n_cr_cedula_cache IS
        'Cédula Cache for Hacienda API data. Multi-tier caching strategy: Fresh (0-7 days), Refresh (5-7 days), Stale (7-90 days), Expired (>90 days)';
    """)

    _logger.info('Cédula cache table creation completed successfully')


def _create_rate_limiter_table(cr):
    """
    Create rate limiter state table for Hacienda API.

    The table stores state for a distributed token bucket rate limiter:
    - Sustained rate: 10 requests/second
    - Burst capacity: 20 requests/second
    - Application-wide shared state
    - Thread-safe using PostgreSQL advisory locks

    Args:
        cr: Database cursor
    """
    _logger.info('Processing rate limiter state table creation')

    # Check if table already exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'l10n_cr_hacienda_rate_limit_state'
        );
    """)

    table_exists = cr.fetchone()[0]

    if table_exists:
        _logger.info('Table l10n_cr_hacienda_rate_limit_state already exists - skipping creation')
        return

    _logger.info('Creating l10n_cr_hacienda_rate_limit_state table')

    # Create the table
    cr.execute("""
        CREATE TABLE l10n_cr_hacienda_rate_limit_state (
            id SERIAL PRIMARY KEY,
            key VARCHAR(255) NOT NULL,
            tokens DOUBLE PRECISION NOT NULL DEFAULT 20.0,
            last_refill TIMESTAMP NOT NULL DEFAULT NOW(),
            total_requests BIGINT NOT NULL DEFAULT 0,
            last_request TIMESTAMP NOT NULL DEFAULT NOW(),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)

    _logger.info('Table l10n_cr_hacienda_rate_limit_state created successfully')

    # Add unique constraint on key column
    _logger.info('Adding unique constraint on key column')
    cr.execute("""
        ALTER TABLE l10n_cr_hacienda_rate_limit_state
        ADD CONSTRAINT l10n_cr_hacienda_rate_limit_state_key_unique
        UNIQUE (key);
    """)

    # Create index on key column for faster lookups
    _logger.info('Creating index on key column')
    cr.execute("""
        CREATE INDEX idx_hacienda_rate_limit_key
            ON l10n_cr_hacienda_rate_limit_state(key);
    """)

    # Add table and column comments for documentation
    _logger.info('Adding table and column comments')

    cr.execute("""
        COMMENT ON TABLE l10n_cr_hacienda_rate_limit_state IS
            'Distributed rate limiter state for Hacienda API (Token Bucket Algorithm)';
    """)

    cr.execute("""
        COMMENT ON COLUMN l10n_cr_hacienda_rate_limit_state.key IS
            'Singleton key for rate limiter (always "hacienda_api_rate_limiter")';
    """)

    cr.execute("""
        COMMENT ON COLUMN l10n_cr_hacienda_rate_limit_state.tokens IS
            'Current number of available tokens (max 20 for burst capacity)';
    """)

    cr.execute("""
        COMMENT ON COLUMN l10n_cr_hacienda_rate_limit_state.last_refill IS
            'Timestamp of last token refill calculation';
    """)

    cr.execute("""
        COMMENT ON COLUMN l10n_cr_hacienda_rate_limit_state.total_requests IS
            'Lifetime counter of all requests processed through rate limiter';
    """)

    cr.execute("""
        COMMENT ON COLUMN l10n_cr_hacienda_rate_limit_state.last_request IS
            'Timestamp of the most recent API request';
    """)

    # Insert initial singleton row
    _logger.info('Inserting initial rate limiter state row')
    cr.execute("""
        INSERT INTO l10n_cr_hacienda_rate_limit_state
            (key, tokens, last_refill, total_requests, last_request, created_at, updated_at)
        VALUES
            ('hacienda_api_rate_limiter', 20.0, NOW(), 0, NOW(), NOW(), NOW());
    """)

    _logger.info('Rate limiter state table creation completed successfully')
