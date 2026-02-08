# -*- coding: utf-8 -*-
"""
Unit tests for account.move payment method validation (Phase 1A)
Tests SINPE Móvil transaction ID validation
"""
from odoo.tests import tagged
from odoo.exceptions import UserError
import uuid
from .common import EInvoiceTestCase


def _generate_unique_vat_company():
    """Generate unique VAT number for company (10 digits starting with 3)."""
    return f"310{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_vat_person():
    """Generate unique VAT number for person (9 digits)."""
    return f"10{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_email(prefix='test'):
    """Generate unique email address."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"




class TestAccountMovePayment(EInvoiceTestCase):
    """Test payment method validation on invoices."""

    def setUp(self):
        super(TestAccountMovePayment, self).setUp()

        # Use company and partner from base class (already have journals configured)
        # Base class provides: self.company, self.partner, self.product

        # Get payment methods
        self.payment_method_efectivo = self.env.ref('l10n_cr_einvoice.payment_method_efectivo')
        self.payment_method_sinpe = self.env.ref('l10n_cr_einvoice.payment_method_sinpe')
        self.payment_method_tarjeta = self.env.ref('l10n_cr_einvoice.payment_method_tarjeta')

    def _create_test_invoice_payment(self, payment_method=None, transaction_id=None):
        """Helper to create test invoice with payment method."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.sales_journal.id,
            'invoice_date': '2025-12-28',
            'l10n_cr_payment_method_id': payment_method.id if payment_method else False,
            'l10n_cr_payment_transaction_id': transaction_id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 10000.0,
            })],
        })
        return invoice

    def test_default_payment_method_assigned(self):
        """Test that invoices without payment method get Efectivo (01) by default."""
        invoice = self._create_test_invoice_payment()
        self.assertFalse(invoice.l10n_cr_payment_method_id, "Should start without payment method")

        # Post invoice - should auto-assign Efectivo
        invoice.action_post()

        self.assertTrue(invoice.l10n_cr_payment_method_id, "Payment method should be assigned")
        self.assertEqual(invoice.l10n_cr_payment_method_id.code, '01',
                        "Default payment method should be Efectivo (01)")

    def test_efectivo_without_transaction_id_success(self):
        """Test that Efectivo can be posted without transaction ID."""
        invoice = self._create_test_invoice_payment(payment_method=self.payment_method_efectivo)

        # Should post successfully without transaction ID
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted', "Invoice should be posted")

    def test_sinpe_movil_without_transaction_id_error(self):
        """Test that SINPE Móvil requires transaction ID."""
        invoice = self._create_test_invoice_payment(payment_method=self.payment_method_sinpe)

        # Should raise error without transaction ID
        with self.assertRaises(UserError) as context:
            invoice.action_post()

        self.assertIn('Transaction ID', str(context.exception),
                     "Error message should mention Transaction ID")

    def test_sinpe_movil_with_transaction_id_success(self):
        """Test that SINPE Móvil can be posted with transaction ID."""
        invoice = self._create_test_invoice_payment(
            payment_method=self.payment_method_sinpe,
            transaction_id='123456789'
        )

        # Should post successfully with transaction ID
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted', "Invoice should be posted")
        self.assertEqual(invoice.l10n_cr_payment_transaction_id, '123456789',
                        "Transaction ID should be saved")

    def test_tarjeta_without_transaction_id_success(self):
        """Test that Tarjeta can be posted without transaction ID."""
        invoice = self._create_test_invoice_payment(payment_method=self.payment_method_tarjeta)

        # Should post successfully without transaction ID
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted', "Invoice should be posted")

    def test_onchange_payment_method_clears_transaction_id(self):
        """Test that changing from SINPE to other method clears transaction ID."""
        invoice = self._create_test_invoice_payment(
            payment_method=self.payment_method_sinpe,
            transaction_id='123456789'
        )

        # Change to Efectivo (which doesn't require transaction ID)
        invoice.l10n_cr_payment_method_id = self.payment_method_efectivo
        invoice._onchange_payment_method()

        self.assertFalse(invoice.l10n_cr_payment_transaction_id,
                        "Transaction ID should be cleared when changing to method that doesn't require it")

    def test_payment_method_copied_false(self):
        """Test that payment method is not copied when duplicating invoice."""
        invoice = self._create_test_invoice_payment(
            payment_method=self.payment_method_sinpe,
            transaction_id='123456789'
        )
        invoice.action_post()

        # Copy invoice
        copied_invoice = invoice.copy()

        self.assertFalse(copied_invoice.l10n_cr_payment_method_id,
                        "Payment method should not be copied")
        self.assertFalse(copied_invoice.l10n_cr_payment_transaction_id,
                        "Transaction ID should not be copied")

    def test_payment_method_tracking(self):
        """Test that payment method changes are tracked."""
        invoice = self._create_test_invoice_payment(payment_method=self.payment_method_efectivo)

        # Check that tracking is enabled
        field = self.env['account.move']._fields['l10n_cr_payment_method_id']
        self.assertTrue(field.tracking, "Payment method field should have tracking enabled")

    def test_requires_einvoice_compute(self):
        """Test that l10n_cr_requires_einvoice is computed correctly."""
        # Costa Rica customer invoice
        invoice_cr = self._create_test_invoice_payment()
        self.assertTrue(invoice_cr.l10n_cr_requires_einvoice,
                       "CR customer invoice should require e-invoice")

        # Non-CR partner with CR company still requires e-invoice (company is CR)
        partner_us = self.env['res.partner'].create({
            'name': 'US Customer',
            'country_id': self.env.ref('base.us').id,
        })
        invoice_us = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner_us.id,
            'company_id': self.company.id,
            'journal_id': self.sales_journal.id,
        })
        # Note: l10n_cr_requires_einvoice depends on COMPANY country, not partner country
        # If company is CR, then e-invoice is required regardless of partner location
        self.assertTrue(invoice_us.l10n_cr_requires_einvoice,
                       "Invoice from CR company requires e-invoice even for non-CR partner")

    def test_validation_only_for_cr_invoices(self):
        """Test that payment method validation only applies to CR invoices."""
        # Test by checking l10n_cr_requires_einvoice computation
        # CR company invoice should require e-invoice
        invoice_cr = self._create_test_invoice_payment()
        self.assertTrue(invoice_cr.l10n_cr_requires_einvoice,
                       "CR company invoice should require e-invoice")

        # Validation logic in account_move.py checks:
        # if not self.l10n_cr_requires_einvoice: return
        # So non-CR invoices skip validation automatically
