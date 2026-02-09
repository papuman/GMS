# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.addons.payment_tilopay import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('tilopay', "TiloPay")],
        ondelete={'tilopay': 'set default'},
    )
    tilopay_api_key = fields.Char(
        string="API Key",
        required_if_provider='tilopay',
        groups='base.group_system',
    )
    tilopay_api_user = fields.Char(
        string="API User",
        required_if_provider='tilopay',
        groups='base.group_system',
    )
    tilopay_api_password = fields.Char(
        string="API Password",
        required_if_provider='tilopay',
        groups='base.group_system',
    )

    # --- Constraint methods ---

    @api.constrains('state', 'tilopay_api_key', 'tilopay_api_user', 'tilopay_api_password')
    def _check_tilopay_credentials_before_enabling(self):
        for provider in self.filtered(
            lambda p: p.code == 'tilopay' and p.state != 'disabled'
        ):
            missing = []
            if not provider.tilopay_api_key:
                missing.append('API Key')
            if not provider.tilopay_api_user:
                missing.append('API User')
            if not provider.tilopay_api_password:
                missing.append('API Password')
            if missing:
                raise ValidationError(_(
                    "TiloPay credentials incomplete. Missing: %s. "
                    "Please configure all credentials before enabling the provider."
                ) % ', '.join(missing))

    # --- Business methods ---

    def _compute_feature_support_fields(self):
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'tilopay').update({
            'support_refund': 'partial',
        })

    def _get_default_payment_method_codes(self):
        self.ensure_one()
        if self.code != 'tilopay':
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.code != 'tilopay':
            return super()._get_supported_currencies()
        # Tilopay handles CRC, USD, etc. — return all active currencies.
        return self.env['res.currency'].search([])

    def _build_request_url(self, endpoint, **kwargs):
        self.ensure_one()
        if self.code != 'tilopay':
            return super()._build_request_url(endpoint, **kwargs)
        return f'{const.API_URL}{endpoint}'

    def _build_request_headers(self, method, endpoint, payload, **kwargs):
        self.ensure_one()
        if self.code != 'tilopay':
            return super()._build_request_headers(method, endpoint, payload, **kwargs)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        access_token = kwargs.get('access_token')
        if access_token:
            headers['Authorization'] = f'bearer {access_token}'
        return headers

    def _get_reset_values(self):
        self.ensure_one()
        if self.code != 'tilopay':
            return super()._get_reset_values()
        return {
            'tilopay_api_key': False,
            'tilopay_api_user': False,
            'tilopay_api_password': False,
        }

    # --- Tilopay-specific methods ---

    def _tilopay_login(self):
        """Authenticate with Tilopay and return the access token.

        POST /api/v1/login with {email: api_user, password: api_password}.
        Per-request — no caching, simplest approach.

        :return: The access token string.
        :rtype: str
        :raise ValidationError: If authentication fails.
        """
        self.ensure_one()
        _logger.info("Authenticating with Tilopay API for provider %s", self.id)
        response = self._send_api_request(
            'POST',
            '/api/v1/login',
            json={
                'email': self.tilopay_api_user,
                'password': self.tilopay_api_password,
            },
        )
        access_token = response.get('access_token')
        if not access_token:
            raise ValidationError(_(
                "Tilopay authentication failed: no access token in response."
            ))
        return access_token
