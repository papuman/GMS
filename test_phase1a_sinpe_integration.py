#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Phase 1A: SINPE Móvil Payment Method Integration

This script validates the complete implementation of Phase 1A including:
1. Payment method catalog (5 methods)
2. Account move extension with payment method fields
3. XML generator updates with MedioPago and NumeroTransaccion tags
4. UI updates with payment method selection
5. Migration script for existing invoices

Run with: python3 test_phase1a_sinpe_integration.py
"""
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'phase1a_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def print_header(title):
    """Print formatted header."""
    logger.info('=' * 80)
    logger.info(f' {title}')
    logger.info('=' * 80)


def print_section(title):
    """Print formatted section."""
    logger.info('-' * 80)
    logger.info(f' {title}')
    logger.info('-' * 80)


def test_phase1a_implementation():
    """Main test function for Phase 1A implementation."""

    print_header('PHASE 1A: SINPE MÓVIL PAYMENT METHOD INTEGRATION TEST')

    try:
        import odoo
        from odoo import api, SUPERUSER_ID

        # Connect to database
        logger.info('Connecting to Odoo database...')

        # Get database name from environment or use default
        db_name = 'gms_production'  # Update with your database name

        with api.Environment.manage():
            env = api.Environment(odoo.registry(db_name), SUPERUSER_ID, {})

            # Test 1: Payment Method Catalog
            print_section('Test 1: Payment Method Catalog')
            test_payment_method_catalog(env)

            # Test 2: Payment Method Model
            print_section('Test 2: Payment Method Model Fields')
            test_payment_method_model(env)

            # Test 3: Account Move Extension
            print_section('Test 3: Account Move Extension')
            test_account_move_extension(env)

            # Test 4: XML Generator Updates
            print_section('Test 4: XML Generator Updates')
            test_xml_generator(env)

            # Test 5: UI Views
            print_section('Test 5: UI Views')
            test_ui_views(env)

            # Test 6: Security Rules
            print_section('Test 6: Security Rules')
            test_security_rules(env)

            # Test 7: Migration Script
            print_section('Test 7: Migration Script Validation')
            test_migration_script()

            print_header('ALL TESTS COMPLETED SUCCESSFULLY!')
            return True

    except Exception as e:
        logger.error(f'Test failed with error: {str(e)}', exc_info=True)
        return False


def test_payment_method_catalog(env):
    """Test that payment method catalog is loaded correctly."""
    logger.info('Testing payment method catalog...')

    PaymentMethod = env['l10n_cr.payment.method']

    # Check all 5 methods exist
    expected_methods = {
        '01': 'Efectivo',
        '02': 'Tarjeta',
        '03': 'Cheque',
        '04': 'Transferencia - depósito bancario',
        '06': 'SINPE Móvil',
    }

    for code, name in expected_methods.items():
        method = PaymentMethod.search([('code', '=', code)], limit=1)
        assert method, f"Payment method {code} not found!"
        assert method.name == name, f"Payment method {code} has wrong name: {method.name}"
        logger.info(f'  ✓ {code} - {name} exists')

    # Check SINPE Móvil requires transaction ID
    sinpe = PaymentMethod.search([('code', '=', '06')], limit=1)
    assert sinpe.requires_transaction_id, "SINPE Móvil should require transaction ID"
    logger.info(f'  ✓ SINPE Móvil requires_transaction_id = {sinpe.requires_transaction_id}')

    # Check Efectivo does NOT require transaction ID
    efectivo = PaymentMethod.search([('code', '=', '01')], limit=1)
    assert not efectivo.requires_transaction_id, "Efectivo should NOT require transaction ID"
    logger.info(f'  ✓ Efectivo requires_transaction_id = {efectivo.requires_transaction_id}')

    logger.info('Payment method catalog test: PASSED')


def test_payment_method_model(env):
    """Test payment method model fields and constraints."""
    logger.info('Testing payment method model...')

    PaymentMethod = env['l10n_cr.payment.method']

    # Test fields exist
    required_fields = ['name', 'code', 'description', 'active', 'requires_transaction_id', 'icon', 'badge_color']
    method = PaymentMethod.search([], limit=1)

    for field in required_fields:
        assert hasattr(method, field), f"Field {field} not found in payment method model"
        logger.info(f'  ✓ Field {field} exists')

    # Test name_get returns code + name
    name_get_result = method.name_get()[0][1]
    assert method.code in name_get_result, "name_get should include code"
    assert method.name in name_get_result, "name_get should include name"
    logger.info(f'  ✓ name_get format: {name_get_result}')

    logger.info('Payment method model test: PASSED')


def test_account_move_extension(env):
    """Test account.move extension with payment method fields."""
    logger.info('Testing account.move extension...')

    AccountMove = env['account.move']

    # Test fields exist
    required_fields = ['l10n_cr_payment_method_id', 'l10n_cr_payment_transaction_id']

    for field in required_fields:
        assert field in AccountMove._fields, f"Field {field} not found in account.move"
        logger.info(f'  ✓ Field {field} exists in account.move')

    # Test field properties
    payment_method_field = AccountMove._fields['l10n_cr_payment_method_id']
    assert payment_method_field.comodel_name == 'l10n_cr.payment.method', "Wrong comodel"
    assert not payment_method_field.copy, "Payment method should not be copied"
    assert payment_method_field.tracking, "Payment method should have tracking"
    logger.info(f'  ✓ l10n_cr_payment_method_id field properties correct')

    transaction_field = AccountMove._fields['l10n_cr_payment_transaction_id']
    assert transaction_field.size == 50, "Transaction ID should have size 50"
    assert not transaction_field.copy, "Transaction ID should not be copied"
    logger.info(f'  ✓ l10n_cr_payment_transaction_id field properties correct')

    logger.info('Account move extension test: PASSED')


def test_xml_generator(env):
    """Test XML generator has been updated."""
    logger.info('Testing XML generator...')

    XMLGenerator = env['l10n_cr.xml.generator']

    # Check _add_medio_pago method exists
    assert hasattr(XMLGenerator, '_add_medio_pago'), "_add_medio_pago method not found"
    logger.info('  ✓ _add_medio_pago method exists')

    # Check method signature (should accept root and move parameters)
    import inspect
    sig = inspect.signature(XMLGenerator._add_medio_pago)
    params = list(sig.parameters.keys())
    assert 'root' in params, "_add_medio_pago should have 'root' parameter"
    assert 'move' in params, "_add_medio_pago should have 'move' parameter"
    logger.info(f'  ✓ _add_medio_pago signature: {params}')

    logger.info('XML generator test: PASSED')


def test_ui_views(env):
    """Test that UI views have been updated."""
    logger.info('Testing UI views...')

    View = env['ir.ui.view']

    # Check account_move form view includes payment method fields
    move_form_view = View.search([
        ('model', '=', 'account.move'),
        ('name', '=', 'account.move.form.einvoice')
    ], limit=1)

    assert move_form_view, "Account move form view not found"
    logger.info(f'  ✓ Account move form view exists: {move_form_view.name}')

    # Check view includes payment method field
    assert 'l10n_cr_payment_method_id' in move_form_view.arch, \
        "Payment method field not in view"
    logger.info('  ✓ Payment method field in form view')

    # Check view includes transaction ID field
    assert 'l10n_cr_payment_transaction_id' in move_form_view.arch, \
        "Transaction ID field not in view"
    logger.info('  ✓ Transaction ID field in form view')

    # Check tree view includes payment method
    move_tree_view = View.search([
        ('model', '=', 'account.move'),
        ('name', '=', 'account.move.tree.einvoice')
    ], limit=1)

    if move_tree_view:
        assert 'l10n_cr_payment_method_id' in move_tree_view.arch, \
            "Payment method not in tree view"
        logger.info('  ✓ Payment method field in tree view')

    logger.info('UI views test: PASSED')


def test_security_rules(env):
    """Test that security rules have been added."""
    logger.info('Testing security rules...')

    ModelAccess = env['ir.model.access']

    # Check payment method access rules exist
    payment_method_accesses = ModelAccess.search([
        ('model_id.model', '=', 'l10n_cr.payment.method')
    ])

    assert len(payment_method_accesses) >= 3, \
        f"Expected at least 3 access rules for payment method, found {len(payment_method_accesses)}"
    logger.info(f'  ✓ Found {len(payment_method_accesses)} access rules for payment method')

    for access in payment_method_accesses:
        logger.info(f'    - {access.name}: read={access.perm_read}, write={access.perm_write}')

    logger.info('Security rules test: PASSED')


def test_migration_script():
    """Test that migration script exists and is valid."""
    logger.info('Testing migration script...')

    import os

    migration_path = '/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/migrations/19.0.1.0.0/post-migration.py'

    assert os.path.exists(migration_path), f"Migration script not found at {migration_path}"
    logger.info(f'  ✓ Migration script exists: {migration_path}')

    # Check script contains required function
    with open(migration_path, 'r') as f:
        content = f.read()
        assert 'def migrate(cr, version):' in content, "migrate function not found"
        assert 'l10n_cr_payment_method' in content, "Script should reference payment method table"
        assert 'account_move' in content, "Script should update account_move table"
        logger.info('  ✓ Migration script has correct structure')

    logger.info('Migration script test: PASSED')


if __name__ == '__main__':
    print_header('STARTING PHASE 1A INTEGRATION TESTS')

    success = test_phase1a_implementation()

    if success:
        logger.info('')
        print_header('SUCCESS: All Phase 1A tests passed!')
        sys.exit(0)
    else:
        logger.error('')
        print_header('FAILURE: Some tests failed. Check logs for details.')
        sys.exit(1)
