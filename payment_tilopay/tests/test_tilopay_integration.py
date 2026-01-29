# -*- coding: utf-8 -*-

"""
Integration Tests for TiloPay Payment Module

Tests complete end-to-end payment scenarios with all components:
- Provider + Transaction + Webhook flow
- SINPE payment complete journey
- Card payment complete journey
- Payment failure handling
- Invoice integration
"""

from unittest.mock import patch, Mock
from odoo.tests import tagged
from .common import TiloPayTestCommon, TiloPayMockFactory, MockAPIClient


@tagged('post_install', '-at_install', 'tilopay', 'tilopay_integration')
class TestTiloPayIntegration(TiloPayTestCommon):
    """Integration tests for complete payment flows."""

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_sinpe_payment_complete_flow(self, mock_client_class):
        """Test complete SINPE payment flow from creation to completion."""
        # Setup mock client
        mock_client = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )
        mock_client_class.return_value = mock_client
        
        # Step 1: Create transaction
        tx = self._create_test_transaction(amount=50000.00)
        self.assertEqual(tx.state, 'draft')
        
        # Step 2: Initialize payment with TiloPay
        tx._tilopay_create_payment()
        self.assertEqual(tx.state, 'pending')
        self.assertTrue(tx.tilopay_payment_id)
        self.assertTrue(tx.tilopay_payment_url)
        
        # Step 3: Customer completes SINPE payment
        # Simulate payment success in mock client
        mock_client.simulate_payment_success(
            tx.tilopay_payment_id,
            payment_method='sinpe'
        )
        
        # Step 4: Receive webhook notification
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            event='payment.completed',
            payment_id=tx.tilopay_payment_id,
            reference=tx.reference,
            status='approved',
            amount=50000,
            payment_method='sinpe',
            transaction_id='SINPE987654'
        )
        
        tx._tilopay_process_notification(webhook_data)
        
        # Step 5: Verify final state
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.tilopay_payment_method, 'sinpe')
        self.assertEqual(tx.tilopay_transaction_id, 'SINPE987654')
        self.assertTrue(tx.tilopay_webhook_received)
        self.assertEqual(tx.tilopay_webhook_count, 1)

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_card_payment_complete_flow(self, mock_client_class):
        """Test complete card payment flow from creation to completion."""
        # Setup mock client
        mock_client = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )
        mock_client_class.return_value = mock_client
        
        # Create and initialize payment
        tx = self._create_test_transaction(amount=75000.00)
        tx._tilopay_create_payment()
        
        # Simulate card payment success
        mock_client.simulate_payment_success(
            tx.tilopay_payment_id,
            payment_method='card'
        )
        
        # Receive webhook
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            event='payment.completed',
            payment_id=tx.tilopay_payment_id,
            reference=tx.reference,
            status='approved',
            amount=75000,
            payment_method='card'
        )
        
        tx._tilopay_process_notification(webhook_data)
        
        # Verify completion
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.tilopay_payment_method, 'card')

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_payment_failure_flow(self, mock_client_class):
        """Test payment failure flow."""
        # Setup mock client
        mock_client = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )
        mock_client_class.return_value = mock_client
        
        # Create and initialize payment
        tx = self._create_test_transaction(amount=50000.00)
        tx._tilopay_create_payment()
        
        # Simulate payment failure
        mock_client.simulate_payment_failure(
            tx.tilopay_payment_id,
            error_code='INSUFFICIENT_FUNDS',
            error_message='Insufficient funds in account'
        )
        
        # Receive failure webhook
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            event='payment.failed',
            payment_id=tx.tilopay_payment_id,
            reference=tx.reference,
            status='failed',
            amount=50000,
            payment_method='card'
        )
        
        tx._tilopay_process_notification(webhook_data)
        
        # Verify failure state
        self.assertEqual(tx.state, 'error')

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_payment_cancellation_flow(self, mock_client_class):
        """Test payment cancellation flow."""
        # Setup mock client
        mock_client = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )
        mock_client_class.return_value = mock_client
        
        # Create and initialize payment
        tx = self._create_test_transaction(amount=50000.00)
        tx._tilopay_create_payment()
        
        # Customer cancels payment
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            event='payment.cancelled',
            payment_id=tx.tilopay_payment_id,
            reference=tx.reference,
            status='cancelled',
            amount=50000,
            payment_method='sinpe'
        )
        webhook_data['data']['status'] = 'cancelled'
        
        tx._tilopay_process_notification(webhook_data)
        
        # Verify cancelled state
        self.assertEqual(tx.state, 'cancel')

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_multiple_payment_methods_configuration(self, mock_client_class):
        """Test provider with multiple payment methods."""
        # Create provider with SINPE and Cards
        multi_provider = self.env['payment.provider'].create({
            'name': 'TiloPay Multi',
            'code': 'tilopay',
            'state': 'test',
            'company_id': self.company.id,
            'tilopay_api_key': 'test_key',
            'tilopay_api_user': 'test_user',
            'tilopay_api_password': 'test_pass',
            'tilopay_enable_sinpe': True,
            'tilopay_enable_cards': True,
            'tilopay_enable_yappy': False,
        })
        
        methods = multi_provider._tilopay_get_enabled_payment_methods()
        
        self.assertEqual(set(methods), {'sinpe', 'card'})

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_invoice_linked_payment_flow(self, mock_client_class):
        """Test payment flow with linked invoice."""
        # Setup mock client
        mock_client = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )
        mock_client_class.return_value = mock_client
        
        # Create transaction linked to invoice
        tx = self._create_test_transaction(amount=50000.00)
        
        # Verify invoice is linked
        self.assertTrue(tx.invoice_ids)
        self.assertEqual(tx.invoice_ids[0], self.invoice)
        
        # Process payment
        tx._tilopay_create_payment()
        
        # Verify payment description includes invoice
        description = tx._get_tilopay_payment_description()
        self.assertIn(self.invoice.name, description)
        
        # Complete payment
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            payment_id=tx.tilopay_payment_id,
            reference=tx.reference,
            status='approved',
            amount=50000,
            payment_method='sinpe'
        )
        
        tx._tilopay_process_notification(webhook_data)
        
        # Verify payment completed
        self.assertEqual(tx.state, 'done')

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_concurrent_payments_different_transactions(self, mock_client_class):
        """Test handling multiple concurrent payments."""
        # Setup mock client
        mock_client = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )
        mock_client_class.return_value = mock_client
        
        # Create two transactions
        tx1 = self._create_test_transaction(amount=50000.00)
        tx2 = self._create_test_transaction(amount=75000.00)
        
        # Initialize both payments
        tx1._tilopay_create_payment()
        tx2._tilopay_create_payment()
        
        # Verify different payment IDs
        self.assertNotEqual(tx1.tilopay_payment_id, tx2.tilopay_payment_id)
        
        # Complete tx1
        webhook1 = TiloPayMockFactory.create_webhook_payload(
            payment_id=tx1.tilopay_payment_id,
            reference=tx1.reference,
            status='approved',
            amount=50000
        )
        tx1._tilopay_process_notification(webhook1)
        
        # Complete tx2
        webhook2 = TiloPayMockFactory.create_webhook_payload(
            payment_id=tx2.tilopay_payment_id,
            reference=tx2.reference,
            status='approved',
            amount=75000
        )
        tx2._tilopay_process_notification(webhook2)
        
        # Both should be completed
        self.assertEqual(tx1.state, 'done')
        self.assertEqual(tx2.state, 'done')

    def test_provider_sandbox_vs_production_urls(self):
        """Test provider uses correct URLs for sandbox vs production."""
        # Sandbox provider
        self.assertEqual(
            self.provider.tilopay_use_sandbox,
            True
        )
        
        # Production provider
        prod_provider = self.env['payment.provider'].create({
            'name': 'TiloPay Production',
            'code': 'tilopay',
            'state': 'disabled',
            'company_id': self.company.id,
            'tilopay_api_key': 'prod_key',
            'tilopay_api_user': 'prod_user',
            'tilopay_api_password': 'prod_pass',
            'tilopay_use_sandbox': False,
        })
        
        self.assertFalse(prod_provider.tilopay_use_sandbox)

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_webhook_idempotency(self, mock_client_class):
        """Test webhook notifications are idempotent."""
        # Setup
        mock_client = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )
        mock_client_class.return_value = mock_client
        
        tx = self._create_test_transaction()
        tx._tilopay_create_payment()
        
        webhook_data = TiloPayMockFactory.create_webhook_payload(
            payment_id=tx.tilopay_payment_id,
            reference=tx.reference,
            status='approved',
            amount=50000
        )
        
        # Process webhook first time
        tx._tilopay_process_notification(webhook_data)
        first_state = tx.state
        
        # Process same webhook again (duplicate)
        tx._tilopay_process_notification(webhook_data)
        second_state = tx.state
        
        # State should not change
        self.assertEqual(first_state, second_state)
        self.assertEqual(tx.tilopay_webhook_count, 2)
