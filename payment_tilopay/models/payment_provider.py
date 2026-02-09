# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import threading
import time

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.addons.payment_tilopay import const

_logger = logging.getLogger(__name__)

# Module-level token cache: {provider_id: {'access_token': str, 'expires_at': float}}
# Tilopay tokens are cached with a conservative TTL to avoid authenticating on every API call.
_TILOPAY_TOKEN_CACHE = {}
_TILOPAY_TOKEN_CACHE_LOCK = threading.Lock()
# Default TTL: 10 minutes (Tilopay tokens typically last longer, but we stay conservative)
_TILOPAY_TOKEN_TTL = 600


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
        Tokens are cached per provider with a conservative TTL to avoid
        authenticating on every API call.

        :return: The access token string.
        :rtype: str
        :raise ValidationError: If authentication fails.
        """
        self.ensure_one()
        now = time.time()

        # Check cached token
        with _TILOPAY_TOKEN_CACHE_LOCK:
            cached = _TILOPAY_TOKEN_CACHE.get(self.id)
            if cached and cached.get('expires_at', 0) > now:
                _logger.debug(
                    "Using cached Tilopay token for provider %s (expires in %ds)",
                    self.id, int(cached['expires_at'] - now),
                )
                return cached['access_token']

        # Token missing or expired -- authenticate
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

        # Cache the token with TTL
        with _TILOPAY_TOKEN_CACHE_LOCK:
            _TILOPAY_TOKEN_CACHE[self.id] = {
                'access_token': access_token,
                'expires_at': now + _TILOPAY_TOKEN_TTL,
            }

        return access_token

    @api.model
    def _tilopay_clear_token_cache(self, provider_id=None):
        """Clear the Tilopay token cache.

        Call this when credentials change or on authentication failures.

        :param int provider_id: Specific provider to clear, or None to clear all.
        """
        with _TILOPAY_TOKEN_CACHE_LOCK:
            if provider_id:
                _TILOPAY_TOKEN_CACHE.pop(provider_id, None)
            else:
                _TILOPAY_TOKEN_CACHE.clear()
