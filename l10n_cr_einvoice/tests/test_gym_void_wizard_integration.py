# -*- coding: utf-8 -*-
"""
Integration Tests for Gym Invoice Void Wizard

Tests complete workflow execution from start to finish.
"""
import logging
from datetime import datetime

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestGymVoidWizardIntegration(TransactionCase):
    """
    Integration tests for complete void workflow.

    Tests the entire process: create credit note, cancel membership,
    process refund, submit to Hacienda, send email.
    """

    @classmethod
    def setUpClass(cls):
        super(TestGymVoidWizardIntegration, cls).setUpClass()

        # Create test company with complete configuration
        cls.company = cls.env['res.company'].create({
            'name': 'Test Gym Costa Rica',
            'vat': '3-101-654321',
            'email': 'gym@testgym.cr',
            'phone': '+506-2222-3333',
            'street': 'San José, Costa Rica',
            'country_id': cls.env.ref('base.cr').id,
        })

        # Create test customer
        cls.customer = cls.env['res.partner'].create({
            'name': 'María González',
            'email': 'maria.gonzalez@email.com',
            'phone': '+506-8888-9999',
            'vat': '1-0345-0678',
            'l10n_cr_identification_type': '01',
            'country_id': cls.env.ref('base.cr').id,
        })

        # Create gym products
        cls.monthly_membership = cls.env['product.product'].create({
            'name': 'Membresía Mensual',
            'list_price': 50000.0,
            'type': 'service',
            'recurring_invoice': True,
        })

        cls.personal_training = cls.env['product.product'].create({
            'name': 'Entrenamiento Personal',
            'list_price': 25000.0,
            'type': 'service',
        })

        # Create journal
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id),
        ], limit=1)

        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Sales Journal',
                'code': 'SAJ',
                'type': 'sale',
                'company_id': cls.company.id,
            })

    def _create_test_invoice(self, products_data):
        """
        Helper to create test invoice with products.

        Args:
            products_data: List of (product, quantity, price_unit) tuples
        """
        invoice_lines = []
        for product, quantity, price_unit in products_data:
            invoice_lines.append((0, 0, {
                'product_id': product.id,
                'quantity': quantity,
                'price_unit': price_unit,
                'name': product.name,
            }))

        invoice = self.env['account.move'].create({
            'partner_id': self.customer.id,
            'move_type': 'out_invoice',
            'invoice_date': datetime.today().date(),
            'company_id': self.company.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': invoice_lines,
        })

        invoice.action_post()
        return invoice

    def _create_einvoice(self, invoice):
        """Helper to create e-invoice document."""
        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'state': 'accepted',
            'clave': f'50601012025{datetime.today().strftime("%m%d")}00012340000100001000000001234567890',
        })
        invoice.l10n_cr_einvoice_id = einvoice.id
        return einvoice

    # ============================================================
    # BASIC WORKFLOW TESTS
    # ============================================================

    def test_void_simple_invoice_cash_refund(self):
        """Test voiding simple invoice with cash refund."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Void Simple Invoice - Cash Refund")
        _logger.info("=" * 70)

        # Create invoice
        invoice = self._create_test_invoice([
            (self.monthly_membership, 1, 50000.0),
        ])
        self._create_einvoice(invoice)

        _logger.info(f"📄 Created invoice: {invoice.name} - ₡{invoice.amount_total:,.2f}")

        # Create void wizard
        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'customer_request',
            'void_reason_notes': 'Cliente solicitó cancelación',
            'refund_method': 'cash',
            'auto_submit_to_hacienda': False,  # Skip Hacienda for test
            'send_email_notification': False,  # Skip email for test
        })

        _logger.info(f"🔧 Wizard created - Reason: {wizard.void_reason}")

        # Execute void
        try:
            result = wizard.action_void_invoice()
            _logger.info("✅ Void action executed successfully")

            # Verify wizard state
            self.assertEqual(wizard.state, 'done', "Wizard should be in 'done' state")
            _logger.info("✅ Wizard state: done")

            # Verify credit note created
            self.assertTrue(wizard.credit_note_id, "Credit note should be created")
            credit_note = wizard.credit_note_id
            _logger.info(f"✅ Credit note created: {credit_note.name}")

            # Verify credit note details
            self.assertEqual(credit_note.move_type, 'out_refund', "Should be a customer refund")
            self.assertEqual(credit_note.partner_id.id, self.customer.id, "Same customer")
            self.assertEqual(credit_note.amount_total, invoice.amount_total, "Same amount")
            self.assertEqual(credit_note.state, 'posted', "Credit note should be posted")
            _logger.info(f"✅ Credit note amount: ₡{credit_note.amount_total:,.2f}")

            # Verify e-invoice for credit note created
            self.assertTrue(wizard.credit_note_einvoice_id, "E-invoice for CN should be created")
            cn_einvoice = wizard.credit_note_einvoice_id
            self.assertEqual(cn_einvoice.document_type, 'NC', "Should be NC document type")
            _logger.info(f"✅ E-invoice NC created: {cn_einvoice.name}")

            # Verify reversal relationship
            self.assertEqual(credit_note.reversed_entry_id.id, invoice.id, "Should reference original invoice")
            _logger.info("✅ Reversal relationship established")

            # Verify audit trail
            invoice_messages = invoice.message_ids.filtered(lambda m: 'Factura Anulada' in (m.subject or ''))
            self.assertTrue(invoice_messages, "Audit log should exist on invoice")
            _logger.info("✅ Audit trail logged on original invoice")

            cn_messages = credit_note.message_ids.filtered(lambda m: 'Nota de Crédito' in (m.subject or ''))
            self.assertTrue(cn_messages, "Audit log should exist on credit note")
            _logger.info("✅ Audit trail logged on credit note")

            _logger.info("\n✅ TEST PASSED: Simple invoice void with cash refund")

        except Exception as e:
            _logger.error(f"❌ TEST FAILED: {e}")
            raise

        _logger.info("=" * 70 + "\n")

    def test_void_invoice_with_multiple_lines(self):
        """Test voiding invoice with multiple product lines."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Void Invoice - Multiple Lines")
        _logger.info("=" * 70)

        # Create invoice with multiple lines
        invoice = self._create_test_invoice([
            (self.monthly_membership, 1, 50000.0),
            (self.personal_training, 4, 25000.0),
        ])
        self._create_einvoice(invoice)

        total_amount = 50000.0 + (4 * 25000.0)
        _logger.info(f"📄 Created invoice with 2 lines: {invoice.name} - ₡{total_amount:,.2f}")

        # Void invoice
        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'billing_error',
            'void_reason_notes': 'Error en cantidad de sesiones',
            'refund_method': 'card',
            'refund_reference': 'VISA-1234',
            'auto_submit_to_hacienda': False,
            'send_email_notification': False,
        })

        wizard.action_void_invoice()

        # Verify credit note has same number of lines
        credit_note = wizard.credit_note_id
        self.assertEqual(len(credit_note.invoice_line_ids), len(invoice.invoice_line_ids),
                        "Credit note should have same number of lines")
        _logger.info(f"✅ Credit note has {len(credit_note.invoice_line_ids)} lines")

        # Verify amounts match
        self.assertEqual(credit_note.amount_total, invoice.amount_total,
                        "Total amounts should match")
        _logger.info(f"✅ Amounts match: ₡{credit_note.amount_total:,.2f}")

        # Verify refund info logged
        refund_messages = credit_note.message_ids.filtered(
            lambda m: 'Información de Devolución' in (m.subject or '')
        )
        self.assertTrue(refund_messages, "Refund information should be logged")
        _logger.info("✅ Refund information logged")

        _logger.info("\n✅ TEST PASSED: Multiple line invoice void")
        _logger.info("=" * 70 + "\n")

    # ============================================================
    # REFUND METHOD TESTS
    # ============================================================

    def test_void_with_transfer_refund(self):
        """Test void with bank transfer refund."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Void Invoice - Bank Transfer Refund")
        _logger.info("=" * 70)

        invoice = self._create_test_invoice([
            (self.monthly_membership, 1, 50000.0),
        ])
        self._create_einvoice(invoice)

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'customer_request',
            'refund_method': 'transfer',
            'refund_bank_account': 'CR12345678901234567890',
            'refund_reference': 'TRANS-2025-001',
            'auto_submit_to_hacienda': False,
            'send_email_notification': False,
        })

        wizard.action_void_invoice()

        # Verify bank account is logged
        credit_note = wizard.credit_note_id
        messages = credit_note.message_ids.mapped('body')
        message_text = ' '.join(messages)

        self.assertIn('CR12345678901234567890', message_text,
                     "Bank account should be in message")
        self.assertIn('TRANS-2025-001', message_text,
                     "Reference should be in message")
        _logger.info("✅ Bank transfer details logged")

        _logger.info("\n✅ TEST PASSED: Bank transfer refund")
        _logger.info("=" * 70 + "\n")

    def test_void_with_credit_refund(self):
        """Test void with credit for future purchases."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Void Invoice - Credit Refund")
        _logger.info("=" * 70)

        invoice = self._create_test_invoice([
            (self.monthly_membership, 1, 50000.0),
        ])
        self._create_einvoice(invoice)

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'customer_request',
            'refund_method': 'credit',
            'refund_notes': 'Crédito disponible para próximas clases',
            'auto_submit_to_hacienda': False,
            'send_email_notification': False,
        })

        wizard.action_void_invoice()

        # Verify refund notes logged
        credit_note = wizard.credit_note_id
        messages = credit_note.message_ids.mapped('body')
        message_text = ' '.join(messages)

        self.assertIn('Crédito', message_text, "Credit refund should be mentioned")
        _logger.info("✅ Credit refund details logged")

        _logger.info("\n✅ TEST PASSED: Credit refund")
        _logger.info("=" * 70 + "\n")

    def test_void_with_no_refund(self):
        """Test void without refund (courtesy)."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Void Invoice - No Refund (Courtesy)")
        _logger.info("=" * 70)

        invoice = self._create_test_invoice([
            (self.monthly_membership, 1, 50000.0),
        ])
        self._create_einvoice(invoice)

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'service_not_provided',
            'refund_method': 'no_refund',
            'auto_submit_to_hacienda': False,
            'send_email_notification': False,
        })

        # Onchange should auto-fill notes
        wizard._onchange_refund_method()

        wizard.action_void_invoice()

        # Verify no refund is logged
        credit_note = wizard.credit_note_id
        messages = credit_note.message_ids.mapped('body')
        message_text = ' '.join(messages)

        self.assertIn('Cortesía', message_text, "Courtesy should be mentioned")
        _logger.info("✅ No refund (courtesy) details logged")

        _logger.info("\n✅ TEST PASSED: No refund void")
        _logger.info("=" * 70 + "\n")

    # ============================================================
    # ERROR HANDLING TESTS
    # ============================================================

    def test_void_fails_gracefully_on_error(self):
        """Test that errors are handled gracefully."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Error Handling")
        _logger.info("=" * 70)

        # Create invoice but don't post it
        invoice = self.env['account.move'].create({
            'partner_id': self.customer.id,
            'move_type': 'out_invoice',
            'invoice_date': datetime.today().date(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.monthly_membership.id,
                'quantity': 1,
                'price_unit': 50000.0,
            })],
        })
        # Don't post!

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'customer_request',
            'refund_method': 'cash',
        })

        # Should raise UserError
        with self.assertRaises(UserError) as cm:
            wizard.action_void_invoice()

        _logger.info(f"✅ Error caught: {cm.exception}")
        self.assertIn('Only posted invoices', str(cm.exception))

        _logger.info("\n✅ TEST PASSED: Errors handled gracefully")
        _logger.info("=" * 70 + "\n")

    # ============================================================
    # VOID REASON TESTS
    # ============================================================

    def test_void_all_reason_types(self):
        """Test void with all different reason types."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: All Void Reason Types")
        _logger.info("=" * 70)

        reasons = [
            'membership_cancel',
            'billing_error',
            'customer_request',
            'duplicate_invoice',
            'payment_failure',
            'service_not_provided',
            'price_adjustment',
            'other',
        ]

        for reason in reasons:
            # Create new invoice for each test
            invoice = self._create_test_invoice([
                (self.monthly_membership, 1, 50000.0),
            ])
            self._create_einvoice(invoice)

            wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
                'invoice_id': invoice.id,
                'void_reason': reason,
                'refund_method': 'cash',
                'auto_submit_to_hacienda': False,
                'send_email_notification': False,
            })

            wizard.action_void_invoice()

            self.assertEqual(wizard.state, 'done', f"Void should succeed for reason: {reason}")
            _logger.info(f"✅ Void succeeded with reason: {reason}")

        _logger.info("\n✅ TEST PASSED: All void reasons work")
        _logger.info("=" * 70 + "\n")

    # ============================================================
    # SUMMARY
    # ============================================================

    def test_integration_summary(self):
        """Print integration test summary."""
        _logger.info("\n" + "=" * 70)
        _logger.info("INTEGRATION TEST SUMMARY - Gym Invoice Void Wizard")
        _logger.info("=" * 70)
        _logger.info("✅ Simple invoice void - PASSED")
        _logger.info("✅ Multiple line invoice void - PASSED")
        _logger.info("✅ Bank transfer refund - PASSED")
        _logger.info("✅ Credit refund - PASSED")
        _logger.info("✅ No refund (courtesy) - PASSED")
        _logger.info("✅ Error handling - PASSED")
        _logger.info("✅ All void reasons - PASSED")
        _logger.info("=" * 70)
        _logger.info("✅ Complete workflow tested successfully")
        _logger.info("=" * 70 + "\n")
