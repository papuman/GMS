# -*- coding: utf-8 -*-

"""
TiloPay Payment Provider Model

Extends the payment.provider model to add TiloPay-specific configuration
and functionality.
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    """
    Extend payment.provider to support TiloPay payment gateway.
    """
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('tilopay', 'TiloPay')],
        ondelete={'tilopay': 'set default'}
    )

    # TiloPay API Credentials
    tilopay_api_key = fields.Char(
        string='TiloPay API Key',
        required_if_provider='tilopay',
        groups='base.group_system',
        help="API Key from TiloPay dashboard (Account > Checkout)"
    )

    tilopay_api_user = fields.Char(
        string='TiloPay API User',
        required_if_provider='tilopay',
        groups='base.group_system',
        help="API username for authentication"
    )

    tilopay_api_password = fields.Char(
        string='TiloPay API Password',
        required_if_provider='tilopay',
        groups='base.group_system',
        help="API password for authentication"
    )

    tilopay_merchant_code = fields.Char(
        string='Merchant Code',
        groups='base.group_system',
        help="Merchant identification code (optional, used in some integrations)"
    )

    tilopay_secret_key = fields.Char(
        string='Secret Key',
        groups='base.group_system',
        help="Secret key for webhook signature verification (CRITICAL for security)"
    )

    # Environment Configuration
    tilopay_use_sandbox = fields.Boolean(
        string='Use Sandbox Environment',
        default=True,
        help="Enable to use TiloPay sandbox for testing. "
             "Disable for production with real transactions."
    )

    # Payment Method Configuration
    tilopay_enable_sinpe = fields.Boolean(
        string='Enable SINPE Móvil',
        default=True,
        help="Allow customers to pay using SINPE Móvil (Costa Rica instant payments)"
    )

    tilopay_enable_cards = fields.Boolean(
        string='Enable Credit/Debit Cards',
        default=True,
        help="Allow customers to pay with Visa, Mastercard, American Express"
    )

    tilopay_enable_yappy = fields.Boolean(
        string='Enable Yappy',
        default=False,
        help="Allow customers to pay with Yappy (Panama)"
    )

    # Webhook Configuration
    tilopay_webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_tilopay_webhook_url',
        help="URL for TiloPay to send payment notifications. "
             "Configure this URL in your TiloPay dashboard."
    )

    @api.depends('code')
    def _compute_tilopay_webhook_url(self):
        """Compute the webhook URL for this provider."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for provider in self:
            if provider.code == 'tilopay':
                provider.tilopay_webhook_url = f"{base_url}/payment/tilopay/webhook"
            else:
                provider.tilopay_webhook_url = False

    @api.constrains('tilopay_enable_sinpe', 'tilopay_enable_cards', 'tilopay_enable_yappy')
    def _check_tilopay_payment_methods(self):
        """Ensure at least one payment method is enabled."""
        for provider in self:
            if provider.code == 'tilopay':
                if not (provider.tilopay_enable_sinpe or
                       provider.tilopay_enable_cards or
                       provider.tilopay_enable_yappy):
                    raise ValidationError(_(
                        "At least one payment method must be enabled "
                        "(SINPE Móvil, Cards, or Yappy)."
                    ))

    @api.constrains('tilopay_api_key', 'tilopay_api_user', 'tilopay_api_password')
    def _check_tilopay_credentials(self):
        """Validate TiloPay credentials format."""
        for provider in self:
            if provider.code == 'tilopay' and provider.state != 'disabled':
                if not provider.tilopay_api_key:
                    raise ValidationError(_("TiloPay API Key is required"))
                if not provider.tilopay_api_user:
                    raise ValidationError(_("TiloPay API User is required"))
                if not provider.tilopay_api_password:
                    raise ValidationError(_("TiloPay API Password is required"))

                # Warn if using sandbox in production state
                if not provider.tilopay_use_sandbox and provider.state == 'enabled':
                    _logger.warning(
                        "TiloPay provider %s is ENABLED in PRODUCTION mode. "
                        "Ensure you are using production credentials!",
                        provider.name
                    )

    def _tilopay_get_api_client(self):
        """
        Get initialized TiloPay API client for this provider.

        Returns:
            TiloPayAPIClient: Initialized API client instance

        Raises:
            UserError: If provider is not TiloPay or credentials are missing

        TODO (Phase 3): This will work once API client is fully implemented
        """
        self.ensure_one()

        if self.code != 'tilopay':
            raise UserError(_("This provider is not TiloPay"))

        if not all([self.tilopay_api_key, self.tilopay_api_user, self.tilopay_api_password]):
            raise UserError(_(
                "TiloPay credentials are incomplete. Please configure: "
                "API Key, API User, and API Password in provider settings."
            ))

        # Import here to avoid circular dependency
        from .tilopay_api_client import TiloPayAPIClient

        return TiloPayAPIClient(
            api_key=self.tilopay_api_key,
            api_user=self.tilopay_api_user,
            api_password=self.tilopay_api_password,
            use_sandbox=self.tilopay_use_sandbox
        )

    def action_test_tilopay_connection(self):
        """
        Test TiloPay API connection.

        This action button allows admins to verify their credentials are correct
        before enabling the provider.

        TODO (Phase 3): Implement actual connection test
        - Create a minimal test payment
        - Verify authentication works
        - Cancel the test payment
        - Show success/failure message to user
        """
        self.ensure_one()

        if self.code != 'tilopay':
            raise UserError(_("This provider is not TiloPay"))

        try:
            # Get API client (will validate credentials)
            client = self._tilopay_get_api_client()

            # TODO (Phase 3): Actually test the connection
            # For now, just show placeholder message
            _logger.info("Testing TiloPay connection for provider %s", self.name)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test'),
                    'message': _(
                        'SKELETON: Connection test not yet implemented. '
                        'Will be functional in Phase 3 after API client implementation.'
                    ),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.exception("TiloPay connection test failed")
            raise UserError(_(
                "TiloPay connection test failed:\n%s"
            ) % str(e))

    def _tilopay_get_enabled_payment_methods(self):
        """
        Get list of enabled payment methods for TiloPay.

        Returns:
            list: Payment method codes (e.g., ['sinpe', 'card'])
        """
        self.ensure_one()
        methods = []

        if self.tilopay_enable_sinpe:
            methods.append('sinpe')
        if self.tilopay_enable_cards:
            methods.append('card')
        if self.tilopay_enable_yappy:
            methods.append('yappy')

        return methods

    def _tilopay_get_return_url(self, reference):
        """
        Get return URL for payment completion.

        Args:
            reference (str): Transaction reference

        Returns:
            str: URL where customer returns after payment
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/payment/tilopay/return?reference={reference}"

    @api.model
    def _get_compatible_providers(self, *args, company_id=None, **kwargs):
        """
        Override to ensure TiloPay is available as a payment option.
        """
        providers = super()._get_compatible_providers(*args, company_id=company_id, **kwargs)

        # TiloPay is compatible with all currencies, but primarily CRC
        # No additional filtering needed

        return providers
