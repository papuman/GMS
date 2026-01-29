# -*- coding: utf-8 -*-

"""
Comprehensive Unit Tests for TiloPay Payment Provider Model

Tests provider configuration, validation, and helper methods:
- Provider creation and configuration
- Credential validation
- Payment method configuration
- API client initialization
- Connection testing
- Helper methods
"""

from unittest.mock import patch, Mock
from odoo.tests import tagged
from odoo.exceptions import ValidationError, UserError
from .common import TiloPayTestCommon, MockAPIClient


@tagged('post_install', '-at_install', 'tilopay', 'tilopay_provider')
class TestTiloPayPaymentProvider(TiloPayTestCommon):
    """
    Test TiloPay Payment Provider model functionality.

    All tests use the base fixtures from TiloPayTestCommon.
    """

    def test_provider_creation(self):
        """Test creating a TiloPay payment provider."""
        self.assertEqual(self.provider.code, 'tilopay')
        self.assertEqual(self.provider.name, 'TiloPay Test')
        self.assertTrue(self.provider.tilopay_use_sandbox)
        self.assertTrue(self.provider.tilopay_enable_sinpe)
        self.assertTrue(self.provider.tilopay_enable_cards)
        self.assertFalse(self.provider.tilopay_enable_yappy)

    def test_provider_credentials_required(self):
        """Test that credentials are required for enabled provider."""
        with self.assertRaises(ValidationError):
            self.env['payment.provider'].create({
                'name': 'TiloPay Invalid',
                'code': 'tilopay',
                'state': 'enabled',
                'company_id': self.company.id,
                # Missing credentials
            })

    def test_provider_sandbox_configuration(self):
        """Test sandbox mode configuration."""
        self.assertTrue(self.provider.tilopay_use_sandbox)

        # Create production provider
        prod_provider = self.env['payment.provider'].create({
            'name': 'TiloPay Production',
            'code': 'tilopay',
            'state': 'test',
            'company_id': self.company.id,
            'tilopay_api_key': 'prod_key',
            'tilopay_api_user': 'prod_user',
            'tilopay_api_password': 'prod_pass',
            'tilopay_use_sandbox': False,
        })

        self.assertFalse(prod_provider.tilopay_use_sandbox)

    def test_provider_payment_methods_validation(self):
        """Test that at least one payment method must be enabled."""
        with self.assertRaises(ValidationError):
            self.env['payment.provider'].create({
                'name': 'TiloPay No Methods',
                'code': 'tilopay',
                'state': 'test',
                'company_id': self.company.id,
                'tilopay_api_key': 'test_key',
                'tilopay_api_user': 'test_user',
                'tilopay_api_password': 'test_pass',
                'tilopay_enable_sinpe': False,
                'tilopay_enable_cards': False,
                'tilopay_enable_yappy': False,
            })

    def test_provider_sinpe_only(self):
        """Test provider with only SINPE enabled."""
        sinpe_provider = self.env['payment.provider'].create({
            'name': 'TiloPay SINPE Only',
            'code': 'tilopay',
            'state': 'test',
            'company_id': self.company.id,
            'tilopay_api_key': 'test_key',
            'tilopay_api_user': 'test_user',
            'tilopay_api_password': 'test_pass',
            'tilopay_enable_sinpe': True,
            'tilopay_enable_cards': False,
            'tilopay_enable_yappy': False,
        })

        methods = sinpe_provider._tilopay_get_enabled_payment_methods()
        self.assertEqual(methods, ['sinpe'])

    def test_provider_cards_only(self):
        """Test provider with only cards enabled."""
        card_provider = self.env['payment.provider'].create({
            'name': 'TiloPay Cards Only',
            'code': 'tilopay',
            'state': 'test',
            'company_id': self.company.id,
            'tilopay_api_key': 'test_key',
            'tilopay_api_user': 'test_user',
            'tilopay_api_password': 'test_pass',
            'tilopay_enable_sinpe': False,
            'tilopay_enable_cards': True,
            'tilopay_enable_yappy': False,
        })

        methods = card_provider._tilopay_get_enabled_payment_methods()
        self.assertEqual(methods, ['card'])

    def test_provider_all_methods_enabled(self):
        """Test provider with all payment methods enabled."""
        all_methods_provider = self.env['payment.provider'].create({
            'name': 'TiloPay All Methods',
            'code': 'tilopay',
            'state': 'test',
            'company_id': self.company.id,
            'tilopay_api_key': 'test_key',
            'tilopay_api_user': 'test_user',
            'tilopay_api_password': 'test_pass',
            'tilopay_enable_sinpe': True,
            'tilopay_enable_cards': True,
            'tilopay_enable_yappy': True,
        })

        methods = all_methods_provider._tilopay_get_enabled_payment_methods()
        self.assertEqual(set(methods), {'sinpe', 'card', 'yappy'})

    def test_webhook_url_computation(self):
        """Test webhook URL is computed correctly."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        expected_url = f"{base_url}/payment/tilopay/webhook"

        self.assertEqual(self.provider.tilopay_webhook_url, expected_url)

    def test_webhook_url_only_for_tilopay(self):
        """Test webhook URL is only computed for TiloPay providers."""
        # Create non-TiloPay provider
        other_provider = self.env['payment.provider'].create({
            'name': 'Other Provider',
            'code': 'none',
            'state': 'disabled',
            'company_id': self.company.id,
        })

        self.assertFalse(other_provider.tilopay_webhook_url)

    def test_return_url_generation(self):
        """Test return URL generation with reference."""
        reference = 'TEST-RETURN-001'
        return_url = self.provider._tilopay_get_return_url(reference)

        self.assertIn('/payment/tilopay/return', return_url)
        self.assertIn(f'reference={reference}', return_url)

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_get_api_client_success(self, mock_client_class):
        """Test getting API client with valid credentials."""
        mock_client_class.return_value = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )

        client = self.provider._tilopay_get_api_client()

        self.assertIsNotNone(client)
        mock_client_class.assert_called_once_with(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=self.provider.tilopay_use_sandbox
        )

    def test_get_api_client_wrong_provider(self):
        """Test getting API client from non-TiloPay provider raises error."""
        other_provider = self.env['payment.provider'].create({
            'name': 'Other Provider',
            'code': 'none',
            'state': 'disabled',
            'company_id': self.company.id,
        })

        with self.assertRaises(UserError):
            other_provider._tilopay_get_api_client()

    def test_get_api_client_missing_credentials(self):
        """Test getting API client with incomplete credentials raises error."""
        incomplete_provider = self.env['payment.provider'].create({
            'name': 'TiloPay Incomplete',
            'code': 'tilopay',
            'state': 'disabled',
            'company_id': self.company.id,
            'tilopay_api_key': 'test_key',
            # Missing api_user and api_password
        })

        with self.assertRaises(UserError):
            incomplete_provider._tilopay_get_api_client()

    @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
    def test_action_test_connection_success(self, mock_client_class):
        """Test connection test action (skeleton mode)."""
        mock_client_class.return_value = MockAPIClient(
            api_key=self.provider.tilopay_api_key,
            api_user=self.provider.tilopay_api_user,
            api_password=self.provider.tilopay_api_password,
            use_sandbox=True
        )

        result = self.provider.action_test_tilopay_connection()

        # In skeleton mode, returns warning notification
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')

    def test_action_test_connection_wrong_provider(self):
        """Test connection test on non-TiloPay provider raises error."""
        other_provider = self.env['payment.provider'].create({
            'name': 'Other Provider',
            'code': 'none',
            'state': 'disabled',
            'company_id': self.company.id,
        })

        with self.assertRaises(UserError):
            other_provider.action_test_tilopay_connection()

    def test_credentials_security(self):
        """Test that credentials are restricted to system group."""
        # Verify fields have system group restriction
        api_key_field = self.env['payment.provider']._fields['tilopay_api_key']
        api_user_field = self.env['payment.provider']._fields['tilopay_api_user']
        api_password_field = self.env['payment.provider']._fields['tilopay_api_password']
        secret_key_field = self.env['payment.provider']._fields['tilopay_secret_key']

        self.assertEqual(api_key_field.groups, 'base.group_system')
        self.assertEqual(api_user_field.groups, 'base.group_system')
        self.assertEqual(api_password_field.groups, 'base.group_system')
        self.assertEqual(secret_key_field.groups, 'base.group_system')

    def test_provider_compatible_with_all_currencies(self):
        """Test that TiloPay provider is compatible with all currencies."""
        # Get compatible providers for USD
        usd_currency = self.env.ref('base.USD')
        compatible = self.env['payment.provider']._get_compatible_providers(
            company_id=self.company.id,
        )

        # TiloPay should be in the list (doesn't filter by currency)
        tilopay_providers = compatible.filtered(lambda p: p.code == 'tilopay')
        self.assertTrue(tilopay_providers)

    def test_provider_merchant_code_optional(self):
        """Test that merchant code is optional."""
        provider_without_merchant = self.env['payment.provider'].create({
            'name': 'TiloPay No Merchant',
            'code': 'tilopay',
            'state': 'test',
            'company_id': self.company.id,
            'tilopay_api_key': 'test_key',
            'tilopay_api_user': 'test_user',
            'tilopay_api_password': 'test_pass',
            # No merchant_code
        })

        self.assertFalse(provider_without_merchant.tilopay_merchant_code)

    def test_provider_secret_key_for_webhooks(self):
        """Test that secret key is stored for webhook verification."""
        self.assertEqual(self.provider.tilopay_secret_key, 'test_secret_key_abcdef')

    def test_multiple_providers_same_company(self):
        """Test creating multiple TiloPay providers for same company."""
        # Create second provider (e.g., for different configurations)
        second_provider = self.env['payment.provider'].create({
            'name': 'TiloPay Production',
            'code': 'tilopay',
            'state': 'disabled',
            'company_id': self.company.id,
            'tilopay_api_key': 'prod_key',
            'tilopay_api_user': 'prod_user',
            'tilopay_api_password': 'prod_pass',
            'tilopay_use_sandbox': False,
        })

        # Both should exist
        tilopay_providers = self.env['payment.provider'].search([
            ('code', '=', 'tilopay'),
            ('company_id', '=', self.company.id)
        ])

        self.assertEqual(len(tilopay_providers), 2)

    def test_provider_state_transitions(self):
        """Test provider can be enabled/disabled."""
        # Start in test state
        self.assertEqual(self.provider.state, 'test')

        # Enable provider
        self.provider.state = 'enabled'
        self.assertEqual(self.provider.state, 'enabled')

        # Disable provider
        self.provider.state = 'disabled'
        self.assertEqual(self.provider.state, 'disabled')

    def test_provider_yappy_support(self):
        """Test Yappy payment method configuration."""
        yappy_provider = self.env['payment.provider'].create({
            'name': 'TiloPay Yappy',
            'code': 'tilopay',
            'state': 'test',
            'company_id': self.company.id,
            'tilopay_api_key': 'test_key',
            'tilopay_api_user': 'test_user',
            'tilopay_api_password': 'test_pass',
            'tilopay_enable_sinpe': False,
            'tilopay_enable_cards': False,
            'tilopay_enable_yappy': True,
        })

        methods = yappy_provider._tilopay_get_enabled_payment_methods()
        self.assertEqual(methods, ['yappy'])
