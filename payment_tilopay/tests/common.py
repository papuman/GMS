# -*- coding: utf-8 -*-

"""
TiloPay Test Common Utilities

Provides shared test fixtures, factories, and mock data generators
for all TiloPay payment module tests.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from odoo.tests.common import TransactionCase


class TiloPayTestCommon(TransactionCase):
    """
    Base test class for TiloPay tests with common fixtures and helpers.

    Provides:
    - Test provider setup
    - Test transaction creation
    - Mock API responses
    - Helper methods for assertions
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test company
        cls.company = cls.env['res.company'].create({
            'name': 'Test Gym Company',
            'country_id': cls.env.ref('base.cr').id,
            'currency_id': cls.env.ref('base.CRC').id,
        })

        # Create test partner (customer)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
            'phone': '88887777',
            'company_id': cls.company.id,
        })

        # Create TiloPay payment provider
        cls.provider = cls.env['payment.provider'].create({
            'name': 'TiloPay Test',
            'code': 'tilopay',
            'state': 'test',
            'company_id': cls.company.id,
            'tilopay_api_key': 'test_api_key_12345',
            'tilopay_api_user': 'test_user',
            'tilopay_api_password': 'test_password',
            'tilopay_merchant_code': 'TEST_MERCHANT',
            'tilopay_secret_key': 'test_secret_key_abcdef',
            'tilopay_use_sandbox': True,
            'tilopay_enable_sinpe': True,
            'tilopay_enable_cards': True,
            'tilopay_enable_yappy': False,
        })

        # Create currency (CRC - Costa Rican Colón)
        cls.currency_crc = cls.env.ref('base.CRC')

        # Create invoice for testing
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'company_id': cls.company.id,
            'currency_id': cls.currency_crc.id,
            'invoice_date': datetime.now().date(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Gym Membership',
                'quantity': 1,
                'price_unit': 50000.00,
            })],
        })

    def _create_test_transaction(self, amount=50000.00, currency=None, state='draft'):
        """
        Create a test payment transaction.

        Args:
            amount (float): Transaction amount
            currency (res.currency): Currency (default CRC)
            state (str): Initial state

        Returns:
            payment.transaction: Created transaction
        """
        if currency is None:
            currency = self.currency_crc

        return self.env['payment.transaction'].create({
            'provider_id': self.provider.id,
            'reference': f'TEST-{datetime.now().timestamp()}',
            'amount': amount,
            'currency_id': currency.id,
            'partner_id': self.partner.id,
            'state': state,
            'invoice_ids': [(6, 0, [self.invoice.id])],
        })


class TiloPayMockFactory:
    """
    Factory for creating mock TiloPay API responses.

    Provides methods to generate realistic mock data for:
    - Payment creation responses
    - Payment status responses
    - Webhook payloads
    - Error responses
    """

    @staticmethod
    def create_payment_response(
        payment_id=None,
        reference='TEST-001',
        amount=50000,
        currency='CRC',
        status='pending'
    ):
        """
        Generate mock payment creation response.

        Args:
            payment_id (str): Payment ID (auto-generated if None)
            reference (str): Transaction reference
            amount (int): Amount in cents
            currency (str): Currency code
            status (str): Payment status

        Returns:
            dict: Mock API response
        """
        if payment_id is None:
            payment_id = f'pay_{reference}_{datetime.now().timestamp()}'

        return {
            'payment_id': payment_id,
            'payment_url': f'https://sandbox.tilopay.com/checkout/{payment_id}',
            'status': status,
            'amount': amount,
            'currency': currency,
            'reference': reference,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z',
        }

    @staticmethod
    def create_status_response(
        payment_id='pay_12345',
        status='approved',
        amount=50000,
        currency='CRC',
        payment_method='sinpe',
        transaction_id=None
    ):
        """
        Generate mock payment status response.

        Args:
            payment_id (str): Payment ID
            status (str): Payment status (approved, failed, pending, cancelled)
            amount (int): Amount in cents
            currency (str): Currency code
            payment_method (str): Payment method used
            transaction_id (str): Bank transaction ID

        Returns:
            dict: Mock API response
        """
        response = {
            'payment_id': payment_id,
            'status': status,
            'amount': amount,
            'currency': currency,
            'payment_method': payment_method,
        }

        if status == 'approved':
            response.update({
                'transaction_id': transaction_id or f'TXN{datetime.now().timestamp()}',
                'completed_at': datetime.utcnow().isoformat() + 'Z',
            })
        elif status == 'failed':
            response.update({
                'error_code': 'INSUFFICIENT_FUNDS',
                'error_message': 'Insufficient funds in account',
                'failed_at': datetime.utcnow().isoformat() + 'Z',
            })
        elif status == 'cancelled':
            response.update({
                'cancelled_at': datetime.utcnow().isoformat() + 'Z',
            })

        return response

    @staticmethod
    def create_webhook_payload(
        event='payment.completed',
        payment_id='pay_12345',
        reference='TEST-001',
        status='approved',
        amount=50000,
        currency='CRC',
        payment_method='sinpe',
        transaction_id=None
    ):
        """
        Generate mock webhook payload.

        Args:
            event (str): Webhook event type
            payment_id (str): Payment ID
            reference (str): Transaction reference
            status (str): Payment status
            amount (int): Amount in cents
            currency (str): Currency code
            payment_method (str): Payment method used
            transaction_id (str): Bank transaction ID

        Returns:
            dict: Mock webhook payload
        """
        payload = {
            'event': event,
            'payment_id': payment_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data': {
                'status': status,
                'amount': amount,
                'currency': currency,
                'reference': reference,
                'payment_method': payment_method,
            }
        }

        if status == 'approved' and transaction_id:
            payload['data']['transaction_id'] = transaction_id
        elif status == 'failed':
            payload['data'].update({
                'error_code': 'PAYMENT_DECLINED',
                'error_message': 'Payment declined by issuer',
            })

        return payload

    @staticmethod
    def create_error_response(
        error_code='INVALID_REQUEST',
        error_message='Invalid payment parameters',
        details=None
    ):
        """
        Generate mock error response.

        Args:
            error_code (str): Error code
            error_message (str): Error message
            details (dict): Additional error details

        Returns:
            dict: Mock error response
        """
        response = {
            'error': {
                'code': error_code,
                'message': error_message,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            }
        }

        if details:
            response['error']['details'] = details

        return response

    @classmethod
    def create_sinpe_success(cls, reference='TEST-001', amount=50000):
        """Create complete SINPE success scenario data."""
        payment_id = f'pay_sinpe_{reference}'
        transaction_id = f'SINPE{datetime.now().timestamp()}'

        return {
            'creation': cls.create_payment_response(
                payment_id=payment_id,
                reference=reference,
                amount=amount,
                status='pending'
            ),
            'status': cls.create_status_response(
                payment_id=payment_id,
                status='approved',
                amount=amount,
                payment_method='sinpe',
                transaction_id=transaction_id
            ),
            'webhook': cls.create_webhook_payload(
                event='payment.completed',
                payment_id=payment_id,
                reference=reference,
                status='approved',
                amount=amount,
                payment_method='sinpe',
                transaction_id=transaction_id
            )
        }

    @classmethod
    def create_card_success(cls, reference='TEST-001', amount=50000):
        """Create complete card payment success scenario data."""
        payment_id = f'pay_card_{reference}'

        return {
            'creation': cls.create_payment_response(
                payment_id=payment_id,
                reference=reference,
                amount=amount,
                status='pending'
            ),
            'status': cls.create_status_response(
                payment_id=payment_id,
                status='approved',
                amount=amount,
                payment_method='card',
                transaction_id=f'CARD{datetime.now().timestamp()}'
            ),
            'webhook': cls.create_webhook_payload(
                event='payment.completed',
                payment_id=payment_id,
                reference=reference,
                status='approved',
                amount=amount,
                payment_method='card'
            )
        }

    @classmethod
    def create_payment_failure(cls, reference='TEST-001', amount=50000):
        """Create complete payment failure scenario data."""
        payment_id = f'pay_failed_{reference}'

        return {
            'creation': cls.create_payment_response(
                payment_id=payment_id,
                reference=reference,
                amount=amount,
                status='pending'
            ),
            'status': cls.create_status_response(
                payment_id=payment_id,
                status='failed',
                amount=amount,
                payment_method='card'
            ),
            'webhook': cls.create_webhook_payload(
                event='payment.failed',
                payment_id=payment_id,
                reference=reference,
                status='failed',
                amount=amount,
                payment_method='card'
            )
        }

    @classmethod
    def create_payment_pending(cls, reference='TEST-001', amount=50000):
        """Create payment pending scenario data."""
        payment_id = f'pay_pending_{reference}'

        return {
            'creation': cls.create_payment_response(
                payment_id=payment_id,
                reference=reference,
                amount=amount,
                status='pending'
            ),
            'status': cls.create_status_response(
                payment_id=payment_id,
                status='pending',
                amount=amount,
                payment_method='sinpe'
            ),
        }


class MockAPIClient:
    """
    Mock TiloPay API Client for testing without real API calls.

    This mock client simulates all TiloPay API behavior including:
    - Authentication
    - Payment creation
    - Status queries
    - Cancellation
    - Refunds
    - Signature verification

    Use this in tests by patching the real API client.
    """

    def __init__(self, api_key, api_user, api_password, use_sandbox=True):
        self.api_key = api_key
        self.api_user = api_user
        self.api_password = api_password
        self.use_sandbox = use_sandbox
        self.access_token = 'MOCK_TOKEN_12345'
        self.payments = {}  # Store created payments

    def _authenticate(self):
        """Mock authentication - always succeeds."""
        self.access_token = 'MOCK_TOKEN_12345'

    def create_payment(self, amount, currency, reference, customer_email,
                      payment_methods, return_url, callback_url, **kwargs):
        """
        Mock payment creation.

        Returns mock payment data and stores it for later status queries.
        """
        payment = TiloPayMockFactory.create_payment_response(
            reference=reference,
            amount=amount,
            currency=currency,
            status='pending'
        )

        # Store payment for status queries
        self.payments[payment['payment_id']] = {
            **payment,
            'customer_email': customer_email,
            'payment_methods': payment_methods,
            'return_url': return_url,
            'callback_url': callback_url,
            **kwargs
        }

        return payment

    def get_payment_status(self, payment_id):
        """
        Mock status query.

        Returns stored payment data or default pending status.
        """
        if payment_id in self.payments:
            return TiloPayMockFactory.create_status_response(
                payment_id=payment_id,
                status=self.payments[payment_id].get('status', 'pending'),
                amount=self.payments[payment_id]['amount'],
                currency=self.payments[payment_id]['currency']
            )
        else:
            return TiloPayMockFactory.create_status_response(
                payment_id=payment_id,
                status='pending'
            )

    def cancel_payment(self, payment_id):
        """Mock payment cancellation."""
        if payment_id in self.payments:
            self.payments[payment_id]['status'] = 'cancelled'

        return {
            'status': 'cancelled',
            'cancelled_at': datetime.utcnow().isoformat() + 'Z'
        }

    def refund_payment(self, payment_id, amount=None, reason=None):
        """Mock payment refund."""
        if payment_id in self.payments:
            refund_amount = amount or self.payments[payment_id]['amount']
        else:
            refund_amount = amount or 50000

        return {
            'refund_id': f'refund_{payment_id}',
            'status': 'refunded',
            'amount': refund_amount,
            'refunded_at': datetime.utcnow().isoformat() + 'Z',
            'reason': reason,
        }

    def verify_webhook_signature(self, payload, signature, secret_key):
        """
        Mock signature verification.

        Returns True if signature matches expected pattern, False otherwise.
        For testing, we accept 'valid_signature' as valid and anything else as invalid.
        """
        # Simple mock logic: if signature is 'valid_signature', it's valid
        return signature == 'valid_signature'

    def simulate_payment_success(self, payment_id, payment_method='sinpe'):
        """
        Helper method to simulate successful payment completion.

        Updates internal state to mark payment as approved.
        """
        if payment_id in self.payments:
            self.payments[payment_id].update({
                'status': 'approved',
                'payment_method': payment_method,
                'transaction_id': f'TXN{datetime.now().timestamp()}',
                'completed_at': datetime.utcnow().isoformat() + 'Z',
            })

    def simulate_payment_failure(self, payment_id, error_code='DECLINED', error_message='Payment declined'):
        """
        Helper method to simulate payment failure.

        Updates internal state to mark payment as failed.
        """
        if payment_id in self.payments:
            self.payments[payment_id].update({
                'status': 'failed',
                'error_code': error_code,
                'error_message': error_message,
                'failed_at': datetime.utcnow().isoformat() + 'Z',
            })
