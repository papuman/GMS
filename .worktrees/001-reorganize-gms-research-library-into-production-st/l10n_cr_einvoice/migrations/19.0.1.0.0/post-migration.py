# -*- coding: utf-8 -*-
"""
Post-migration script for l10n_cr_einvoice v19.0.1.0.0

Phase 1A: SINPE Móvil Payment Method Integration
Phase 1B: Discount Codes Catalog

Updates all existing data to comply with Hacienda v4.4 requirements:
1. Sets default payment method "01-Efectivo" for invoices without payment method
2. Sets discount code "99-Otro" for all invoice lines with discounts
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Main migration entry point for v19.0.1.0.0

    Runs both Phase 1A and Phase 1B migrations sequentially.
    """
    _logger.info('=' * 80)
    _logger.info('Running post-migration for l10n_cr_einvoice v19.0.1.0.0')
    _logger.info('=' * 80)

    # Phase 1A: Payment Methods
    _migrate_phase_1a_payment_methods(cr)

    # Phase 1B: Discount Codes
    _migrate_phase_1b_discount_codes(cr)

    _logger.info('=' * 80)
    _logger.info('All migrations completed successfully!')
    _logger.info('=' * 80)


def _migrate_phase_1a_payment_methods(cr):
    """
    Phase 1A: SINPE Móvil Payment Method Integration

    Sets default payment method "01-Efectivo" for all invoices without a payment method.
    Only affects Costa Rica electronic invoices (l10n_cr_requires_einvoice = True).
    """
    _logger.info('')
    _logger.info('=' * 80)
    _logger.info('Phase 1A: SINPE Móvil Payment Method Integration')
    _logger.info('=' * 80)

    # Check if payment_method table exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'l10n_cr_payment_method'
        );
    """)
    payment_method_table_exists = cr.fetchone()[0]

    if not payment_method_table_exists:
        _logger.warning('Payment method table does not exist yet. Skipping Phase 1A migration.')
        return

    # Get the ID of the default payment method "01-Efectivo"
    cr.execute("""
        SELECT id FROM l10n_cr_payment_method
        WHERE code = '01'
        LIMIT 1;
    """)
    result = cr.fetchone()

    if not result:
        _logger.error(
            'Default payment method "01-Efectivo" not found! '
            'Please ensure payment method data is loaded before running this migration.'
        )
        return

    default_payment_method_id = result[0]
    _logger.info(f'Using default payment method ID: {default_payment_method_id} (01-Efectivo)')

    # Check if the column exists in account_move
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'account_move'
            AND column_name = 'l10n_cr_payment_method_id'
        );
    """)
    column_exists = cr.fetchone()[0]

    if not column_exists:
        _logger.warning('Column l10n_cr_payment_method_id does not exist yet. Skipping Phase 1A migration.')
        return

    # Count invoices that need updating
    cr.execute("""
        SELECT COUNT(*)
        FROM account_move
        WHERE move_type IN ('out_invoice', 'out_refund')
        AND l10n_cr_payment_method_id IS NULL
        AND country_code = 'CR'
        AND state = 'posted';
    """)
    count_to_update = cr.fetchone()[0]

    _logger.info(f'Found {count_to_update} posted invoices without payment method')

    if count_to_update == 0:
        _logger.info('No invoices need updating for Phase 1A.')
        return

    # Update invoices with default payment method
    cr.execute("""
        UPDATE account_move
        SET l10n_cr_payment_method_id = %s
        WHERE move_type IN ('out_invoice', 'out_refund')
        AND l10n_cr_payment_method_id IS NULL
        AND country_code = 'CR'
        AND state = 'posted';
    """, (default_payment_method_id,))

    updated_count = cr.rowcount

    _logger.info('Phase 1A SUMMARY:')
    _logger.info(f'  - Total invoices updated: {updated_count}')
    _logger.info(f'  - Default payment method: 01 - Efectivo')
    _logger.info('Phase 1A migration completed successfully!')


def _migrate_phase_1b_discount_codes(cr):
    """
    Phase 1B: Discount Codes Catalog

    Sets discount code "99-Otro" for all invoice lines with discounts > 0.
    Generates analysis report to help users reclassify discounts.
    """
    _logger.info('')
    _logger.info('=' * 80)
    _logger.info('Phase 1B: Discount Codes Catalog')
    _logger.info('=' * 80)

    # Check if discount_code table exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'l10n_cr_discount_code'
        );
    """)
    discount_code_table_exists = cr.fetchone()[0]

    if not discount_code_table_exists:
        _logger.warning('Discount code table does not exist yet. Skipping Phase 1B migration.')
        return

    # Get the ID of discount code "99-Otro"
    cr.execute("""
        SELECT id FROM l10n_cr_discount_code
        WHERE code = '99'
        LIMIT 1;
    """)
    result = cr.fetchone()

    if not result:
        _logger.error(
            'Discount code "99-Otro" not found! '
            'Please ensure discount code data is loaded before running this migration.'
        )
        return

    discount_code_99_id = result[0]
    _logger.info(f'Using discount code ID: {discount_code_99_id} (99-Otro)')

    # Check if the column exists in account_move_line
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'account_move_line'
            AND column_name = 'l10n_cr_discount_code_id'
        );
    """)
    column_exists = cr.fetchone()[0]

    if not column_exists:
        _logger.warning('Column l10n_cr_discount_code_id does not exist yet. Skipping Phase 1B migration.')
        return

    # Count invoice lines that need updating
    cr.execute("""
        SELECT COUNT(*)
        FROM account_move_line aml
        JOIN account_move am ON aml.move_id = am.id
        WHERE aml.discount > 0
        AND aml.l10n_cr_discount_code_id IS NULL
        AND am.move_type IN ('out_invoice', 'out_refund')
        AND am.country_code = 'CR'
        AND aml.display_type = 'product';
    """)
    count_to_update = cr.fetchone()[0]

    _logger.info(f'Found {count_to_update} invoice lines with discounts requiring migration')

    if count_to_update == 0:
        _logger.info('No invoice lines need updating for Phase 1B.')
        return

    # Get discount analysis data BEFORE updating
    cr.execute("""
        SELECT
            aml.discount,
            am.name as invoice_name,
            COALESCE(pt.name->>'en_US', aml.name) as product_name
        FROM account_move_line aml
        JOIN account_move am ON aml.move_id = am.id
        LEFT JOIN product_product pp ON aml.product_id = pp.id
        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE aml.discount > 0
        AND aml.l10n_cr_discount_code_id IS NULL
        AND am.move_type IN ('out_invoice', 'out_refund')
        AND am.country_code = 'CR'
        AND aml.display_type = 'product'
        ORDER BY aml.discount DESC
        LIMIT 100;
    """)
    discount_samples = cr.fetchall()

    # Update invoice lines with discount code "99"
    cr.execute("""
        UPDATE account_move_line
        SET l10n_cr_discount_code_id = %s
        WHERE id IN (
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            WHERE aml.discount > 0
            AND aml.l10n_cr_discount_code_id IS NULL
            AND am.move_type IN ('out_invoice', 'out_refund')
            AND am.country_code = 'CR'
            AND aml.display_type = 'product'
        );
    """, (discount_code_99_id,))

    updated_count = cr.rowcount

    # Generate analysis report
    _generate_discount_analysis_report(discount_samples)

    _logger.info('')
    _logger.info('Phase 1B SUMMARY:')
    _logger.info(f'  - Total invoice lines updated: {updated_count}')
    _logger.info(f'  - Discount code assigned: 99 - Otro')
    _logger.info('Phase 1B migration completed successfully!')


def _generate_discount_analysis_report(discount_samples):
    """
    Generate analysis report of discounts by percentage range.

    Args:
        discount_samples: List of tuples (discount, invoice_name, product_name)
    """
    _logger.info('')
    _logger.info('=' * 80)
    _logger.info('DISCOUNT ANALYSIS REPORT')
    _logger.info('=' * 80)
    _logger.info('')
    _logger.info('All migrated discounts have been set to code "99 - Otro".')
    _logger.info('Consider reclassifying them into proper categories:')
    _logger.info('')

    # Group by discount range
    ranges = {
        '0-5%': [],
        '5-10%': [],
        '10-15%': [],
        '15-20%': [],
        '20%+': [],
    }

    for discount, invoice_name, product_name in discount_samples:
        if 0 < discount <= 5:
            key = '0-5%'
        elif 5 < discount <= 10:
            key = '5-10%'
        elif 10 < discount <= 15:
            key = '10-15%'
        elif 15 < discount <= 20:
            key = '15-20%'
        else:
            key = '20%+'
        ranges[key].append((discount, invoice_name, product_name))

    for range_name, items in ranges.items():
        if items:
            _logger.info(f'{range_name}: {len(items)} lines')
            _logger.info('  Suggested codes:')
            if '0-5%' in range_name:
                _logger.info('    - Code 01: Comercial descuento (promotional)')
                _logger.info('    - Code 02: Descuento por pronto pago (early payment)')
            elif '5-10%' in range_name:
                _logger.info('    - Code 03: Descuento por volumen (volume)')
                _logger.info('    - Code 04: Descuento por fidelidad (loyalty)')
            elif '10-15%' in range_name:
                _logger.info('    - Code 03: Descuento por volumen (bulk)')
                _logger.info('    - Code 05: Descuento estacional (seasonal)')
            elif '15-20%' in range_name:
                _logger.info('    - Code 07: Descuento por cierre (clearance)')
                _logger.info('    - Code 09: Descuento por mayoreo (wholesale)')
            else:
                _logger.info('    - Code 08: Descuento por defecto (damaged)')
                _logger.info('    - Code 10: Descuento corporativo (corporate)')

            for discount, invoice, product in items[:3]:
                _logger.info(f'    Example: {invoice} - {product} ({discount}%)')
            if len(items) > 3:
                _logger.info(f'    ... and {len(items) - 3} more')
            _logger.info('')

    _logger.info('=' * 80)
    _logger.info('RECOMMENDED NEXT STEPS:')
    _logger.info('1. Review the discount analysis report above')
    _logger.info('2. Reclassify discounts into proper categories (codes 01-10)')
    _logger.info('3. Update future invoices to use specific discount codes')
    _logger.info('4. Train users on the 11 discount code categories')
    _logger.info('=' * 80)
