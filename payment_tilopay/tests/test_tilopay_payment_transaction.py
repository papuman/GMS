# -*- coding: utf-8 -*-

"""
Comprehensive Unit Tests for TiloPay Payment Transaction Model

Tests transaction lifecycle, webhook processing, and state management.
"""

from unittest.mock import patch, Mock
from odoo.tests import tagged
from odoo.exceptions import ValidationError, UserError
from .common import TiloPayTestCommon, TiloPayMockFactory, MockAPIClient


@tagged('post_install', '-at_install', 'tilopay', 'tilopay_transaction')
class TestTiloPayPaymentTransaction(TiloPayTestCommon):
    """Test TiloPay Payment Transaction functionality."""

    def test_transaction_creation(self):
        """Test creating a payment transaction."""
        tx = self._create_test_transaction()
        
        self.assertEqual(tx.provider_id, self.provider)
        self.assertEqual(tx.partner_id, self.partner)
        self.assertEqual(tx.amount, 50000.00)
        self.assertEqual(tx.currency_id, self.currency_crc)
        self.assertEqual(tx.state, 'draft')

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_create_payment_sets_pending_state(self, mock_client_class):
        """Test payment creation sets transaction to pending."""
        mock_client_class.return_value = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )
        
        tx = self._create_test_transaction()
        tx._tilopay_create_payment()
        
        self.assertEqual(tx.state, 'pending')
        self.assertTrue(tx.tilopay_payment_id)
        self.assertTrue(tx.tilopay_payment_url)

    def test_webhook_notification_sinpe_success(self):
        """Test processing SINPE success webhook notification."""
        tx = self._create_test_transaction()
        tx.tilopay_payment_id = 'pay_sinpe_001'
        
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            event='payment.completed',
            payment_id='pay_sinpe_001',
            reference=tx.reference,
            status='approved',
            amount=50000,
            payment_method='sinpe',
            transaction_id='SINPE123456'
        )
        
        tx._tilopay_process_notification(webhook_data)
        
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.tilopay_payment_method, 'sinpe')
        self.assertEqual(tx.tilopay_transaction_id, 'SINPE123456')
        self.assertTrue(tx.tilopay_webhook_received)

    def test_webhook_notification_card_success(self):
        """Test processing card success webhook notification."""
        tx = self._create_test_transaction()
        tx.tilopay_payment_id = 'pay_card_001'
        
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            event='payment.completed',
            payment_id='pay_card_001',
            reference=tx.reference,
            status='approved',
            amount=50000,
            payment_method='card'
        )
        
        tx._tilopay_process_notification(webhook_data)
        
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.tilopay_payment_method, 'card')

    def test_webhook_notification_failure(self):
        """Test processing payment failure webhook notification."""
        tx = self._create_test_transaction()
        tx.tilopay_payment_id = 'pay_failed_001'
        
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            event='payment.failed',
            payment_id='pay_failed_001',
            reference=tx.reference,
            status='failed',
            amount=50000,
            payment_method='card'
        )
        
        tx._tilopay_process_notification(webhook_data)
        
        self.assertEqual(tx.state, 'error')

    def test_webhook_notification_cancellation(self):
        """Test processing payment cancellation webhook notification."""
        tx = self._create_test_transaction()
        tx.tilopay_payment_id = 'pay_cancelled_001'
        
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            event='payment.cancelled',
            payment_id='pay_cancelled_001',
            reference=tx.reference,
            status='cancelled',
            amount=50000,
            payment_method='sinpe'
        )
        webhook_data['data']['status'] = 'cancelled'
        
        tx._tilopay_process_notification(webhook_data)
        
        self.assertEqual(tx.state, 'cancel')

    def test_webhook_duplicate_detection(self):
        """Test duplicate webhook notifications are detected."""
        tx = self._create_test_transaction()
        tx.tilopay_payment_id = 'pay_dup_001'
        
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            event='payment.completed',
            payment_id='pay_dup_001',
            reference=tx.reference,
            status='approved',
            amount=50000,
            payment_method='sinpe'
        )
        
        # First webhook
        tx._tilopay_process_notification(webhook_data)
        self.assertEqual(tx.tilopay_webhook_count, 1)
        
        # Second webhook (duplicate)
        tx._tilopay_process_notification(webhook_data)
        self.assertEqual(tx.tilopay_webhook_count, 2)

    def test_payment_id_mismatch_raises_error(self):
        """Test webhook with mismatched payment_id raises error."""
        tx = self._create_test_transaction()
        tx.tilopay_payment_id = 'pay_correct'
        
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            payment_id='pay_wrong',  # Wrong ID
            reference=tx.reference
        )
        
        with self.assertRaises(ValidationError):
            tx._tilopay_process_notification(webhook_data)

    def test_tilopay_is_pending_computed_field(self):
        """Test tilopay_is_pending computed field."""
        tx = self._create_test_transaction()
        
        # Initially False
        self.assertFalse(tx.tilopay_is_pending)
        
        # Set to pending with payment_id
        tx.write({
            'state': 'pending',
            'tilopay_payment_id': 'pay_123'
        })
        
        self.assertTrue(tx.tilopay_is_pending)

    def test_get_tx_from_notification_data(self):
        """Test finding transaction from webhook notification data."""
        tx = self._create_test_transaction()
        tx.tilopay_payment_id = 'pay_find_001'
        
        notification_data = {
            'payment_id': 'pay_find_001',
            'data': {'reference': tx.reference}
        }
        
        found_tx = self.env['payment.transaction']._get_tx_from_notification_data(
            'tilopay',
            notification_data
        )
        
        self.assertEqual(found_tx, tx)

    def test_get_tx_from_notification_data_not_found(self):
        """Test error when transaction not found from webhook data."""
        notification_data = {
            'payment_id': 'pay_nonexistent',
            'data': {'reference': 'NONEXISTENT'}
        }
        
        with self.assertRaises(ValidationError):
            self.env['payment.transaction']._get_tx_from_notification_data(
                'tilopay',
                notification_data
            )

    def test_send_payment_request_override(self):
        """Test _send_payment_request returns redirect action."""
        tx = self._create_test_transaction()
        tx.write({
            'tilopay_payment_id': 'pay_123',
            'tilopay_payment_url': 'https://sandbox.tilopay.com/checkout/pay_123'
        })
        
        result = tx._send_payment_request()
        
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertEqual(result['url'], tx.tilopay_payment_url)
        self.assertEqual(result['target'], 'self')

    def test_payment_description_with_invoice(self):
        """Test payment description includes invoice name."""
        tx = self._create_test_transaction()
        
        description = tx._get_tilopay_payment_description()
        
        self.assertIn(self.invoice.name, description)

    def test_payment_description_without_invoice(self):
        """Test payment description uses reference when no invoice."""
        tx = self._create_test_transaction()
        tx.invoice_ids = [(5, 0, 0)]  # Clear invoices
        
        description = tx._get_tilopay_payment_description()
        
        self.assertIn(tx.reference, description)

    def test_raw_response_storage(self):
        """Test raw API responses are stored."""
        tx = self._create_test_transaction()
        tx.tilopay_payment_id = 'pay_123'
        
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            payment_id='pay_123',
            reference=tx.reference
        )
        
        tx._tilopay_process_notification(webhook_data)
        
        self.assertTrue(tx.tilopay_raw_response)
        # Response should be JSON
        import json
        parsed = json.loads(tx.tilopay_raw_response)
        self.assertEqual(parsed['payment_id'], 'pay_123')

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_action_refresh_status(self, mock_client_class):
        """Test manual status refresh action (skeleton mode)."""
        mock_client_class.return_value = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )
        
        tx = self._create_test_transaction()
        tx.tilopay_payment_id = 'pay_123'
        
        result = tx.action_tilopay_refresh_status()
        
        # Skeleton mode returns warning
        self.assertEqual(result['type'], 'ir.actions.client')

    def test_action_refresh_status_no_payment_id(self):
        """Test refresh status without payment_id raises error."""
        tx = self._create_test_transaction()
        
        with self.assertRaises(UserError):
            tx.action_tilopay_refresh_status()

    def test_action_refresh_status_wrong_provider(self):
        """Test refresh status on non-TiloPay transaction raises error."""
        other_provider = self.env['payment.provider'].create({
            'name': 'Other Provider',
            'code': 'none',
            'state': 'disabled',
            'company_id': self.company.id,
        })
        
        tx = self.env['payment.transaction'].create({
            'provider_id': other_provider.id,
            'reference': 'TEST-OTHER',
            'amount': 100.00,
            'currency_id': self.currency_crc.id,
            'partner_id': self.partner.id,
        })
        
        with self.assertRaises(UserError):
            tx.action_tilopay_refresh_status()
