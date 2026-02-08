# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from odoo import http
from odoo.http import request

from odoo.addons.payment_tilopay import const

_logger = logging.getLogger(__name__)


class TilopayController(http.Controller):

    @http.route(
        const.PAYMENT_RETURN_ROUTE, type='http', methods=['GET'], auth='public',
    )
    def tilopay_return(self, **data):
        """Handle the customer returning from the Tilopay hosted payment page.

        Query params include: tpt, OrderHash, order, code, auth, description,
        selected_method, wp_cancel, crd.

        :param dict data: The query parameters from Tilopay redirect.
        :return: Redirect to the payment status page.
        """
        _logger.info(
            "Handling return from Tilopay with data:\n%s", pprint.pformat(data),
        )
        self._verify_and_process(data)
        return request.redirect('/payment/status')

    @http.route(
        const.WEBHOOK_ROUTE, type='http', methods=['POST'], auth='public',
        csrf=False,
    )
    def tilopay_webhook(self, **_kwargs):
        """Handle async webhook notification from Tilopay.

        JSON body includes: orderNumber, code, orderHash, tpt, auth.

        :return: Empty 200 response to acknowledge receipt.
        """
        data = request.get_json_data()
        _logger.info(
            "Webhook received from Tilopay with data:\n%s", pprint.pformat(data),
        )
        self._verify_and_process(data)
        return ''

    @staticmethod
    def _verify_and_process(data):
        """Find the transaction, verify the hash, and process the payment data.

        :param dict data: The payment data from Tilopay (return or webhook).
        """
        tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference(
            'tilopay', data,
        )
        if not tx_sudo:
            _logger.warning("No transaction found for Tilopay data: %s", data)
            return

        # Verify HMAC hash
        try:
            tx_sudo._tilopay_verify_hash(data)
        except Exception:
            _logger.exception("Tilopay hash verification failed for tx %s", tx_sudo.reference)
            return

        # Process the payment
        tx_sudo._process('tilopay', data)
