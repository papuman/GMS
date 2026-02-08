# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import hmac
import logging
import pprint
from urllib.parse import urlencode

from odoo import _, api, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_tilopay import const

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # --- Business methods ---

    def _get_specific_rendering_values(self, processing_values):
        """Create a Tilopay checkout session and return the redirect URL.

        1. Login to get Bearer token
        2. POST /api/v1/processPayment
        3. Return {'api_url': hosted_payment_page_url}

        :param dict processing_values: The generic processing values.
        :return: The provider-specific rendering values.
        :rtype: dict
        """
        if self.provider_code != 'tilopay':
            return super()._get_specific_rendering_values(processing_values)

        self.ensure_one()
        provider = self.provider_id

        # Step 1: Authenticate
        access_token = provider._tilopay_login()

        # Step 2: Build payment payload
        base_url = provider.get_base_url()
        partner = self.partner_id
        name_parts = (partner.name or 'Customer').split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else first_name

        payload = {
            'redirect': f'{base_url}{const.PAYMENT_RETURN_ROUTE}',
            'key': provider.tilopay_api_key,
            'amount': float(f'{self.amount:.2f}'),
            'currency': self.currency_id.name,
            'billToFirstName': first_name,
            'billToLastName': last_name,
            'billToAddress': partner.street or 'N/A',
            'billToAddress2': partner.street2 or '',
            'billToCity': partner.city or 'N/A',
            'billToState': partner.state_id.name or '',
            'billToZipPostCode': partner.zip or '',
            'billToCountry': partner.country_id.code or 'CR',
            'billToPhoneNumber': partner.phone or '',
            'billToEmail': partner.email or '',
            'orderNumber': self.reference,
            'capture': 1,
            'subscription': 0,
            'platform': 'odoo',
            'hashVersion': 'V2',
            'returnData': 'tilopay',
        }

        _logger.info(
            "Sending processPayment request for tx %s:\n%s",
            self.reference, pprint.pformat(payload),
        )

        # Step 3: Call processPayment
        try:
            response = provider._send_api_request(
                'POST',
                '/api/v1/processPayment',
                json=payload,
                access_token=access_token,
            )
        except ValidationError as e:
            _logger.error("Tilopay processPayment failed for tx %s: %s", self.reference, e)
            self._set_error(str(e))
            return {}

        _logger.info(
            "Tilopay processPayment response for tx %s:\n%s",
            self.reference, pprint.pformat(response),
        )

        # Step 4: Extract redirect URL
        response_type = response.get('type')
        redirect_url = response.get('url')

        if response_type == const.PAYMENT_RESPONSE_REDIRECT and redirect_url:
            return {'api_url': redirect_url}
        elif response_type == const.PAYMENT_RESPONSE_DIRECT and redirect_url:
            return {'api_url': redirect_url}
        else:
            error_msg = response.get('message', response.get('error', 'Unknown error'))
            _logger.error(
                "Tilopay processPayment returned error type %s for tx %s: %s",
                response_type, self.reference, error_msg,
            )
            self._set_error(_(
                "Payment creation failed: %(error)s", error=error_msg,
            ))
            return {}

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Extract the transaction reference from Tilopay callback data.

        Return callback sends `order` query param.
        Webhook sends `orderNumber` in JSON body.

        :param str provider_code: The code of the provider.
        :param dict payment_data: The payment data from Tilopay.
        :return: The transaction reference.
        :rtype: str
        """
        if provider_code != 'tilopay':
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get('order') or payment_data.get('orderNumber')

    def _apply_updates(self, payment_data):
        """Update transaction state based on Tilopay payment data.

        :param dict payment_data: The payment data from Tilopay callback/webhook.
        """
        if self.provider_code != 'tilopay':
            return super()._apply_updates(payment_data)

        # Set provider reference (Tilopay order ID)
        tpt = payment_data.get('tpt')
        if tpt:
            self.provider_reference = tpt

        # Update payment method if reported
        selected_method = payment_data.get('selected_method', '')
        if selected_method:
            method_code = 'card'  # Default
            if 'SINPE' in selected_method.upper():
                method_code = 'bank_transfer'
            payment_method = self.env['payment.method']._get_from_code(method_code)
            if payment_method:
                self.payment_method_id = payment_method

        # Map Tilopay status code to Odoo transaction state
        code = str(payment_data.get('code', ''))
        description = payment_data.get('description', '')
        wp_cancel = payment_data.get('wp_cancel', '')

        if code == '1':
            self._set_done()
        elif code == 'Pending':
            self._set_pending(state_message=description or _("Payment is pending."))
        elif str(wp_cancel).lower() == 'yes':
            self._set_canceled(state_message=_("Payment was cancelled by the customer."))
        else:
            self._set_error(description or _("Payment failed with code: %(code)s", code=code))

    def _send_refund_request(self):
        """Override of ``payment`` to send a refund request to Tilopay.

        Note: ``self`` is the **refund** child transaction (amount is negative).
              ``self.source_transaction_id`` is the original paid transaction.

        Calls ``POST /api/v1/processModification`` with ``type='2'`` (Refund).

        :return: None
        """
        if self.provider_code != 'tilopay':
            return super()._send_refund_request()

        provider = self.provider_id
        source_tx = self.source_transaction_id

        # Authenticate with Tilopay
        access_token = provider._tilopay_login()

        # The refund amount is stored as negative on the child tx; send positive to Tilopay.
        refund_amount = abs(self.amount)

        _logger.info(
            "Sending Tilopay refund request for tx %s (source: %s, amount: %s)",
            self.reference, source_tx.reference, refund_amount,
        )

        response = provider._send_api_request(
            'POST',
            '/api/v1/processModification',
            json={
                'orderNumber': source_tx.provider_reference or source_tx.reference,
                'key': provider.tilopay_api_key,
                'amount': float(f'{refund_amount:.2f}'),
                'type': const.MODIFICATION_REFUND,
                'hashVersion': 'V2',
                'platform': 'odoo',
            },
            access_token=access_token,
        )

        _logger.info(
            "Tilopay refund response for tx %s:\n%s",
            self.reference, pprint.pformat(response),
        )

        # Process the refund response through the standard flow.
        reason_code = str(response.get('ReasonCode', ''))
        self._process('tilopay', {
            'code': '1' if reason_code == '1' else 'error',
            'description': response.get('ReasonCodeDescription', 'Refund processed'),
            'tpt': source_tx.provider_reference,
        })

    # --- Tilopay-specific methods ---

    def _tilopay_verify_hash(self, payment_data):
        """Verify the HMAC-SHA256 hash from a Tilopay callback.

        The hash key is: tpt|api_key|api_password
        The hash payload is URL-encoded params in specific order.

        CRITICAL: amount, currency, and email are NOT in the callback params.
        They must come from the stored transaction record.

        :param dict payment_data: The callback/webhook data.
        :return: True if hash is valid.
        :rtype: bool
        :raise ValidationError: If hash verification fails.
        """
        self.ensure_one()
        provider = self.provider_id
        received_hash = payment_data.get('OrderHash') or payment_data.get('orderHash')

        if not received_hash:
            _logger.warning("No OrderHash in Tilopay callback for tx %s", self.reference)
            raise ValidationError(_("Missing payment verification hash."))

        tpt = payment_data.get('tpt', '')
        code = payment_data.get('code', '')
        auth_code = payment_data.get('auth', '')

        # Construct hash key: tpt|api_key|api_password
        hash_key = f"{tpt}|{provider.tilopay_api_key}|{provider.tilopay_api_password}"

        # Construct params — amount/currency/email from stored transaction, rest from callback
        params = {
            'api_Key': provider.tilopay_api_key,
            'api_user': provider.tilopay_api_user,
            'orderId': tpt,
            'external_orden_id': self.reference,
            'amount': f'{self.amount:.2f}',
            'currency': self.currency_id.name,
            'responseCode': str(code),
            'auth': auth_code,
            'email': self.partner_email or self.partner_id.email or '',
        }

        computed_hash = hmac.new(
            hash_key.encode('utf-8'),
            urlencode(params).encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            _logger.error(
                "SECURITY: Invalid Tilopay hash for tx %s. "
                "Computed: %s, Received: %s",
                self.reference, computed_hash, received_hash,
            )
            raise ValidationError(_("Payment verification failed: invalid hash."))

        _logger.info("Tilopay hash verified successfully for tx %s", self.reference)
        return True
