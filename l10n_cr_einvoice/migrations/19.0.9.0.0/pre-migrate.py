# -*- coding: utf-8 -*-
"""
Pre-migration script for version 19.0.9.0.0

Adds validation override fields to l10n_cr_einvoice_document table.
These fields were added in Phase 2 validation system implementation.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Add validation override fields to einvoice_document table.

    Args:
        cr: Database cursor
        version: Current module version
    """
    _logger.info('Running pre-migration for l10n_cr_einvoice 19.0.9.0.0')

    # Check if table exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'l10n_cr_einvoice_document'
        );
    """)

    table_exists = cr.fetchone()[0]

    if not table_exists:
        _logger.info('Table l10n_cr_einvoice_document does not exist yet - skipping migration')
        return

    _logger.info('Adding validation override fields to l10n_cr_einvoice_document table')

    # Add validation override columns if they don't exist
    columns_to_add = [
        ('validation_override', 'BOOLEAN', 'DEFAULT FALSE'),
        ('validation_override_reason', 'TEXT', ''),
        ('validation_override_user_id', 'INTEGER', ''),
        ('validation_override_date', 'TIMESTAMP', ''),
        ('validation_errors', 'TEXT', ''),
    ]

    for column_name, column_type, default_value in columns_to_add:
        # Check if column exists
        cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'l10n_cr_einvoice_document'
                AND column_name = %s
            );
        """, (column_name,))

        column_exists = cr.fetchone()[0]

        if not column_exists:
            _logger.info(f'Adding column {column_name} ({column_type})')
            cr.execute(f"""
                ALTER TABLE l10n_cr_einvoice_document
                ADD COLUMN {column_name} {column_type} {default_value};
            """)
        else:
            _logger.info(f'Column {column_name} already exists - skipping')

    # Add foreign key constraint for validation_override_user_id if needed
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints
            WHERE constraint_schema = 'public'
            AND table_name = 'l10n_cr_einvoice_document'
            AND constraint_name = 'l10n_cr_einvoice_document_validation_override_user_id_fkey'
        );
    """)

    fkey_exists = cr.fetchone()[0]

    if not fkey_exists:
        # Check if validation_override_user_id column exists and res_users table exists
        cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'l10n_cr_einvoice_document'
                AND column_name = 'validation_override_user_id'
            );
        """)

        if cr.fetchone()[0]:
            _logger.info('Adding foreign key constraint for validation_override_user_id')
            cr.execute("""
                ALTER TABLE l10n_cr_einvoice_document
                ADD CONSTRAINT l10n_cr_einvoice_document_validation_override_user_id_fkey
                FOREIGN KEY (validation_override_user_id)
                REFERENCES res_users(id)
                ON DELETE SET NULL;
            """)
        else:
            _logger.warning('validation_override_user_id column not found - skipping foreign key')
    else:
        _logger.info('Foreign key constraint already exists - skipping')

    _logger.info('Pre-migration for l10n_cr_einvoice 19.0.9.0.0 completed successfully')
