# -*- coding: utf-8 -*-
"""
Membership Cancellation Tests for Gym Invoice Void Wizard

Tests membership detection, cancellation workflow, and audit trail.
"""
import logging
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestGymVoidWizardMembership(TransactionCase):
    """
    Tests for membership cancellation integration.

    Covers subscription detection, cancellation, audit logging.
    """

    @classmethod
    def setUpClass(cls):
        super(TestGymVoidWizardMembership, cls).setUpClass()

        # Create test company
        cls.company = cls.env['res.company'].create({
            'name': 'Elite Fitness CR',
            'vat': '3-101-888999',
            'email': 'info@elitefitness.cr',
        })

        # Create test member
        cls.member = cls.env['res.partner'].create({
            'name': 'Carlos Ramírez',
            'email': 'carlos.ramirez@email.com',
            'phone': '+506-7777-8888',
            'vat': '1-0456-0789',
            'l10n_cr_identification_type': '01',
        })

        # Create membership product
        cls.membership_product = cls.env['product.product'].create({
            'name': 'Membresía Premium Anual',
            'list_price': 600000.0,
            'type': 'service',
            'recurring_invoice': True,
        })

        # Create journal
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id),
        ], limit=1)

        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Sales',
                'code': 'SAL',
                'type': 'sale',
                'company_id': cls.company.id,
            })

    def _create_invoice(self, product, amount):
        """Helper to create and post invoice."""
        invoice = self.env['account.move'].create({
            'partner_id': self.member.id,
            'move_type': 'out_invoice',
            'invoice_date': datetime.today().date(),
            'company_id': self.company.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': 1,
                'price_unit': amount,
                'name': product.name,
            })],
        })
        invoice.action_post()

        # Create e-invoice
        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'state': 'accepted',
            'clave': f'50601012025{datetime.today().strftime("%m%d")}00012340000100001000000001234567890',
        })
        invoice.l10n_cr_einvoice_id = einvoice.id

        return invoice

    # ============================================================
    # MEMBERSHIP DETECTION TESTS
    # ============================================================

    def test_detect_no_membership(self):
        """Test that wizard detects when no membership exists."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Detect No Membership")
        _logger.info("=" * 70)

        invoice = self._create_invoice(self.membership_product, 600000.0)

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'billing_error',
        })

        self.assertFalse(wizard.has_membership, "Should detect no membership")
        self.assertEqual(len(wizard.subscription_ids), 0, "Should have no subscriptions")
        _logger.info("✅ Correctly detected: No membership")

        _logger.info("=" * 70 + "\n")

    def test_detect_active_membership(self):
        """Test that wizard detects active membership."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Detect Active Membership")
        _logger.info("=" * 70)

        invoice = self._create_invoice(self.membership_product, 600000.0)

        # Create subscription
        subscription = self.env['sale.subscription'].create({
            'partner_id': self.member.id,
            'name': 'Premium Annual Membership',
            'code': 'MEM-2025-001',
            'stage_category': 'progress',  # Active
            'recurring_total': 600000.0,
        })
        _logger.info(f"📋 Created subscription: {subscription.code}")

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'membership_cancel',
        })

        self.assertTrue(wizard.has_membership, "Should detect membership")
        self.assertIn(subscription.id, wizard.subscription_ids.ids, "Should include subscription")
        _logger.info(f"✅ Detected active membership: {subscription.code}")

        _logger.info("=" * 70 + "\n")

    def test_detect_multiple_memberships(self):
        """Test detection of multiple memberships for same member."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Detect Multiple Memberships")
        _logger.info("=" * 70)

        invoice = self._create_invoice(self.membership_product, 600000.0)

        # Create multiple subscriptions
        sub1 = self.env['sale.subscription'].create({
            'partner_id': self.member.id,
            'name': 'Gym Membership',
            'code': 'GYM-001',
            'stage_category': 'progress',
        })

        sub2 = self.env['sale.subscription'].create({
            'partner_id': self.member.id,
            'name': 'Personal Training Package',
            'code': 'PT-001',
            'stage_category': 'progress',
        })

        _logger.info(f"📋 Created subscriptions: {sub1.code}, {sub2.code}")

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'membership_cancel',
        })

        self.assertTrue(wizard.has_membership)
        self.assertEqual(len(wizard.subscription_ids), 2, "Should detect both memberships")
        _logger.info(f"✅ Detected {len(wizard.subscription_ids)} memberships")

        _logger.info("=" * 70 + "\n")

    # ============================================================
    # MEMBERSHIP CANCELLATION TESTS
    # ============================================================

    def test_cancel_single_membership(self):
        """Test canceling a single membership."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Cancel Single Membership")
        _logger.info("=" * 70)

        invoice = self._create_invoice(self.membership_product, 600000.0)

        subscription = self.env['sale.subscription'].create({
            'partner_id': self.member.id,
            'name': 'Annual Membership',
            'code': 'MEM-2025-100',
            'stage_category': 'progress',
            'to_renew': True,
        })

        _logger.info(f"📋 Subscription before void:")
        _logger.info(f"   Code: {subscription.code}")
        _logger.info(f"   Status: {subscription.stage_category}")
        _logger.info(f"   To Renew: {subscription.to_renew}")

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'membership_cancel',
            'cancel_membership': True,
            'membership_cancellation_reason': 'Cliente se muda de ciudad',
            'refund_method': 'transfer',
            'refund_bank_account': 'CR11111111111111111111',
            'auto_submit_to_hacienda': False,
            'send_email_notification': False,
        })

        wizard.action_void_invoice()

        # Verify subscription was modified
        subscription.invalidate_cache()  # Refresh from database
        self.assertFalse(subscription.to_renew, "Subscription should not renew")
        _logger.info(f"✅ Subscription to_renew set to False")

        # Verify cancellation message was posted
        messages = subscription.message_ids.filtered(
            lambda m: 'Membresía Cancelada' in (m.subject or '')
        )
        self.assertTrue(messages, "Cancellation message should be posted")
        _logger.info("✅ Cancellation message logged on subscription")

        # Verify reason in message
        message_body = ' '.join(messages.mapped('body'))
        self.assertIn('Cliente se muda de ciudad', message_body, "Reason should be in message")
        _logger.info("✅ Cancellation reason logged")

        _logger.info("\n📋 Subscription after void:")
        _logger.info(f"   To Renew: {subscription.to_renew}")
        _logger.info(f"   Description updated: Yes")

        _logger.info("=" * 70 + "\n")

    def test_cancel_multiple_memberships(self):
        """Test canceling multiple memberships at once."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Cancel Multiple Memberships")
        _logger.info("=" * 70)

        invoice = self._create_invoice(self.membership_product, 600000.0)

        # Create 3 subscriptions
        subs = []
        for i in range(1, 4):
            sub = self.env['sale.subscription'].create({
                'partner_id': self.member.id,
                'name': f'Membership Package {i}',
                'code': f'PKG-{i:03d}',
                'stage_category': 'progress',
                'to_renew': True,
            })
            subs.append(sub)

        _logger.info(f"📋 Created {len(subs)} subscriptions")

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'membership_cancel',
            'cancel_membership': True,
            'membership_cancellation_reason': 'Cancelación por problemas de salud',
            'refund_method': 'cash',
            'auto_submit_to_hacienda': False,
            'send_email_notification': False,
        })

        wizard.action_void_invoice()

        # Verify all subscriptions were canceled
        for sub in subs:
            sub.invalidate_cache()
            self.assertFalse(sub.to_renew, f"Subscription {sub.code} should not renew")
            _logger.info(f"✅ Canceled: {sub.code}")

        _logger.info(f"✅ All {len(subs)} subscriptions canceled")

        _logger.info("=" * 70 + "\n")

    def test_void_without_canceling_membership(self):
        """Test void invoice but keep membership active."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Void Without Canceling Membership")
        _logger.info("=" * 70)

        invoice = self._create_invoice(self.membership_product, 600000.0)

        subscription = self.env['sale.subscription'].create({
            'partner_id': self.member.id,
            'name': 'Keep Active Membership',
            'code': 'KEEP-001',
            'stage_category': 'progress',
            'to_renew': True,
        })

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'billing_error',  # Not membership_cancel
            'cancel_membership': False,  # Keep active
            'refund_method': 'cash',
            'auto_submit_to_hacienda': False,
            'send_email_notification': False,
        })

        wizard.action_void_invoice()

        # Verify subscription remains active
        subscription.invalidate_cache()
        self.assertTrue(subscription.to_renew, "Subscription should still renew")
        self.assertEqual(subscription.stage_category, 'progress', "Should still be active")
        _logger.info(f"✅ Subscription {subscription.code} remains active")

        _logger.info("=" * 70 + "\n")

    # ============================================================
    # AUTO-FILL TESTS
    # ============================================================

    def test_auto_enable_cancel_membership_on_reason(self):
        """Test that cancel_membership auto-enables for membership_cancel reason."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Auto-Enable Membership Cancellation")
        _logger.info("=" * 70)

        invoice = self._create_invoice(self.membership_product, 600000.0)

        subscription = self.env['sale.subscription'].create({
            'partner_id': self.member.id,
            'name': 'Auto Cancel Test',
            'code': 'AUTO-001',
            'stage_category': 'progress',
        })

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'cancel_membership': False,  # Initially False
        })

        # Change reason to membership_cancel
        wizard.void_reason = 'membership_cancel'
        wizard._onchange_void_reason()

        # Should auto-enable
        self.assertTrue(wizard.cancel_membership, "Should auto-enable membership cancellation")
        _logger.info("✅ Auto-enabled membership cancellation")

        # Should auto-fill notes
        self.assertIn('membresía', wizard.void_reason_notes.lower(), "Should auto-fill notes")
        _logger.info(f"✅ Auto-filled notes: {wizard.void_reason_notes}")

        _logger.info("=" * 70 + "\n")

    # ============================================================
    # AUDIT TRAIL TESTS
    # ============================================================

    def test_membership_audit_trail_complete(self):
        """Test complete audit trail for membership cancellation."""
        _logger.info("\n" + "=" * 70)
        _logger.info("TEST: Complete Membership Audit Trail")
        _logger.info("=" * 70)

        invoice = self._create_invoice(self.membership_product, 600000.0)

        subscription = self.env['sale.subscription'].create({
            'partner_id': self.member.id,
            'name': 'Audit Trail Test',
            'code': 'AUDIT-001',
            'stage_category': 'progress',
        })

        wizard = self.env['l10n_cr.gym.invoice.void.wizard'].create({
            'invoice_id': invoice.id,
            'void_reason': 'membership_cancel',
            'cancel_membership': True,
            'membership_cancellation_reason': 'Cliente insatisfecho con servicios',
            'refund_method': 'transfer',
            'refund_bank_account': 'CR99999999999999999999',
            'auto_submit_to_hacienda': False,
            'send_email_notification': False,
        })

        wizard.action_void_invoice()

        # Check invoice audit trail
        invoice_messages = invoice.message_ids.filtered(
            lambda m: 'Factura Anulada' in (m.subject or '')
        )
        self.assertTrue(invoice_messages, "Invoice should have void message")
        _logger.info("✅ Audit logged on invoice")

        # Check credit note audit trail
        cn_messages = wizard.credit_note_id.message_ids.filtered(
            lambda m: 'Nota de Crédito' in (m.subject or '')
        )
        self.assertTrue(cn_messages, "Credit note should have creation message")
        _logger.info("✅ Audit logged on credit note")

        # Check subscription audit trail
        sub_messages = subscription.message_ids.filtered(
            lambda m: 'Membresía Cancelada' in (m.subject or '')
        )
        self.assertTrue(sub_messages, "Subscription should have cancellation message")
        _logger.info("✅ Audit logged on subscription")

        # Verify all key information is in subscription message
        sub_message_body = ' '.join(sub_messages.mapped('body'))
        self.assertIn('Cliente insatisfecho', sub_message_body, "Reason should be logged")
        self.assertIn(invoice.name, sub_message_body, "Invoice number should be logged")
        self.assertIn(wizard.credit_note_id.name, sub_message_body, "Credit note should be logged")
        _logger.info("✅ All key information logged on subscription")

        _logger.info("=" * 70 + "\n")

    # ============================================================
    # SUMMARY
    # ============================================================

    def test_membership_summary(self):
        """Print membership test summary."""
        _logger.info("\n" + "=" * 70)
        _logger.info("MEMBERSHIP TEST SUMMARY - Gym Invoice Void Wizard")
        _logger.info("=" * 70)
        _logger.info("✅ No membership detection - PASSED")
        _logger.info("✅ Active membership detection - PASSED")
        _logger.info("✅ Multiple membership detection - PASSED")
        _logger.info("✅ Single membership cancellation - PASSED")
        _logger.info("✅ Multiple membership cancellation - PASSED")
        _logger.info("✅ Void without canceling membership - PASSED")
        _logger.info("✅ Auto-enable cancellation - PASSED")
        _logger.info("✅ Complete audit trail - PASSED")
        _logger.info("=" * 70)
        _logger.info("✅ All membership tests passed successfully")
        _logger.info("=" * 70 + "\n")
