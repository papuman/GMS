# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.payment_tilopay import const
from odoo.addons.payment_tilopay.tests.common import TilopayCommon


@tagged('post_install', '-at_install')
class TestPaymentProvider(TilopayCommon):

    # --- Credential constraint ---

    def test_enabling_without_api_key_raises_validation_error(self):
        """Enabling the TiloPay provider without an API key must raise a ValidationError."""
        with self.assertRaises(ValidationError):
            self.tilopay.write({
                'tilopay_api_key': False,
                'state': 'enabled',
            })

    def test_enabling_with_api_key_succeeds(self):
        """Enabling the TiloPay provider with credentials set must succeed."""
        self.tilopay.write({
            'tilopay_api_key': 'valid_key',
            'tilopay_api_user': 'user@test.com',
            'tilopay_api_password': 'secret',
            'state': 'test',
        })
        self.assertEqual(self.tilopay.state, 'test')

    def test_disabled_state_does_not_require_credentials(self):
        """A disabled provider should not require API credentials."""
        self.tilopay.write({
            'tilopay_api_key': False,
            'state': 'disabled',
        })
        self.assertEqual(self.tilopay.state, 'disabled')

    # --- Feature support ---

    def test_feature_support_partial_refund(self):
        """TiloPay must advertise partial refund support."""
        self.tilopay._compute_feature_support_fields()
        self.assertEqual(
            self.tilopay.support_refund, 'partial',
            msg="TiloPay should support partial refunds.",
        )

    # --- Default payment method codes ---

    def test_default_payment_method_codes(self):
        """TiloPay's default payment method codes must match the const."""
        codes = self.tilopay._get_default_payment_method_codes()
        self.assertEqual(codes, const.DEFAULT_PAYMENT_METHOD_CODES)

    def test_default_payment_method_codes_non_tilopay_falls_through(self):
        """A non-tilopay provider should not return TiloPay's codes."""
        # The dummy_provider from PaymentCommon has code='none', so it won't match.
        codes = self.dummy_provider._get_default_payment_method_codes()
        self.assertNotEqual(codes, const.DEFAULT_PAYMENT_METHOD_CODES)

    # --- Supported currencies ---

    def test_supported_currencies_returns_all_active(self):
        """TiloPay supports all active currencies."""
        supported = self.tilopay._get_supported_currencies()
        all_currencies = self.env['res.currency'].search([])
        self.assertEqual(
            supported, all_currencies,
            msg="TiloPay should return all active currencies.",
        )

    # --- Request URL building ---

    def test_build_request_url(self):
        """The request URL must prepend the TiloPay API_URL to the endpoint."""
        url = self.tilopay._build_request_url('/api/v1/login')
        self.assertEqual(url, f'{const.API_URL}/api/v1/login')

    def test_build_request_url_process_payment(self):
        url = self.tilopay._build_request_url('/api/v1/processPayment')
        self.assertEqual(url, f'{const.API_URL}/api/v1/processPayment')

    # --- Request headers building ---

    def test_build_request_headers_without_token(self):
        """Headers without access_token should not include Authorization."""
        headers = self.tilopay._build_request_headers('POST', '/api/v1/login', {})
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['Accept'], 'application/json')
        self.assertNotIn('Authorization', headers)

    def test_build_request_headers_with_token(self):
        """Headers with access_token kwarg should include Bearer authorization."""
        headers = self.tilopay._build_request_headers(
            'POST', '/api/v1/processPayment', {}, access_token='my_token'
        )
        self.assertEqual(headers['Authorization'], 'bearer my_token')

    # --- Reset values ---

    def test_get_reset_values(self):
        """Reset values should clear all TiloPay credential fields."""
        reset = self.tilopay._get_reset_values()
        self.assertFalse(reset['tilopay_api_key'])
        self.assertFalse(reset['tilopay_api_user'])
        self.assertFalse(reset['tilopay_api_password'])

    # --- Login method ---

    def test_tilopay_login_success(self):
        """A successful login returns the access token string."""
        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            return_value={'access_token': 'bearer_abc'},
        ):
            token = self.tilopay._tilopay_login()
        self.assertEqual(token, 'bearer_abc')

    def test_tilopay_login_no_token_raises(self):
        """If the login response has no access_token, a ValidationError is raised."""
        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            return_value={'error': 'invalid credentials'},
        ), self.assertRaises(ValidationError):
            self.tilopay._tilopay_login()

    def test_tilopay_login_sends_correct_payload(self):
        """The login call must POST the api_user and api_password."""
        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            return_value={'access_token': 'tok'},
        ) as mock_request:
            self.tilopay._tilopay_login()

        mock_request.assert_called_once_with(
            'POST',
            '/api/v1/login',
            json={
                'email': self.tilopay.tilopay_api_user,
                'password': self.tilopay.tilopay_api_password,
            },
        )
