# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import hmac
from urllib.parse import urlencode

from odoo.addons.payment.tests.common import PaymentCommon


class TilopayCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tilopay = cls._prepare_provider('tilopay', update_values={
            'tilopay_api_key': 'test_api_key_123',
            'tilopay_api_user': 'test@example.com',
            'tilopay_api_password': 'test_password_456',
        })

        # Override default values from PaymentCommon
        cls.provider = cls.tilopay

        # Tilopay-specific test fixtures
        cls.access_token = 'test_bearer_token_abc123'
        cls.tilopay_order_id = 'TPT-999888'

        # Simulate a successful processPayment response
        cls.process_payment_response = {
            'type': '100',
            'url': 'https://app.tilopay.com/hosted/pay/abc123',
        }

        # Simulate a successful callback/return from Tilopay
        cls.return_data = {
            'tpt': cls.tilopay_order_id,
            'order': cls.reference,
            'code': '1',
            'auth': 'AUTH123',
            'description': 'Transaction approved',
            'selected_method': 'VISA',
            'wp_cancel': '',
            'crd': '****1234',
        }

        # Build a valid OrderHash for the return_data
        cls.return_data['OrderHash'] = cls._compute_tilopay_hash(
            tpt=cls.tilopay_order_id,
            api_key='test_api_key_123',
            api_password='test_password_456',
            api_user='test@example.com',
            reference=cls.reference,
            amount=cls.amount,
            currency_name=cls.currency.name,
            code='1',
            auth_code='AUTH123',
            email=cls.default_partner.email,
        )

        # Webhook data uses slightly different key names
        cls.webhook_data = {
            'tpt': cls.tilopay_order_id,
            'orderNumber': cls.reference,
            'code': '1',
            'auth': 'AUTH123',
            'orderHash': cls.return_data['OrderHash'],
            'description': 'Transaction approved',
            'selected_method': 'VISA',
        }

        # Refund response from processModification
        cls.refund_response = {
            'ReasonCode': '1',
            'ReasonCodeDescription': 'Refund approved',
        }

    def setUp(self):
        super().setUp()
        # Clear the module-level token cache before each test to prevent
        # tokens cached by one test from contaminating the next.
        from odoo.addons.payment_tilopay.models.payment_provider import _TILOPAY_TOKEN_CACHE
        _TILOPAY_TOKEN_CACHE.clear()

    @staticmethod
    def _compute_tilopay_hash(
        tpt, api_key, api_password, api_user, reference, amount, currency_name,
        code, auth_code, email,
    ):
        """Compute the HMAC-SHA256 hash matching TiloPay's V2 hash scheme."""
        hash_key = f"{tpt}|{api_key}|{api_password}"
        params = {
            'api_Key': api_key,
            'api_user': api_user,
            'orderId': tpt,
            'external_orden_id': reference,
            'amount': f'{amount:.2f}',
            'currency': currency_name,
            'responseCode': str(code),
            'auth': auth_code,
            'email': email,
        }
        return hmac.new(
            hash_key.encode('utf-8'),
            urlencode(params).encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
