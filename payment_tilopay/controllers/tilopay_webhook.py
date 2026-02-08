# -*- coding: utf-8 -*-

"""
TiloPay Webhook Controller

Handles incoming webhook notifications from TiloPay payment gateway.
"""

import json
import logging

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TiloPayWebhookController(http.Controller):
    """
    HTTP controller for TiloPay webhook endpoints.

    Endpoints:
    - /payment/tilopay/webhook - Receive payment notifications
    - /payment/tilopay/return - Handle customer return after payment
    """

    @http.route('/payment/tilopay/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def tilopay_webhook(self, **kwargs):
        """
        Receive and process TiloPay webhook notifications.

        This endpoint:
        1. Receives POST request from TiloPay with payment status
        2. Verifies webhook signature for security
        3. Finds corresponding payment transaction
        4. Processes notification and updates transaction state
        5. Returns 200 OK to acknowledge receipt

        Security:
        - CSRF disabled (webhooks come from external server)
        - Signature verification REQUIRED (prevents fraud)
        - Always return 200 even on errors (don't leak info to attackers)

        Request body (JSON):
        {
            "event": "payment.completed",
            "payment_id": "pay_12345",
            "timestamp": "2025-12-28T14:30:00Z",
            "data": {
                "status": "approved",
                "amount": 50000,
                "currency": "CRC",
                "reference": "INV/2025/0001",
                "payment_method": "sinpe",
                "transaction_id": "87654321"
            },
            "signature": "sha256_signature_here"
        }

        Returns:
            dict: {'status': 'success'} or {'status': 'error', 'message': '...'}

        TODO (Phase 4): Implement actual webhook processing
        - Extract signature from request headers
        - Get raw request body for signature verification
        - Verify signature using provider's secret key
        - Find transaction by payment_id
        - Call transaction._tilopay_process_notification()
        - Handle errors gracefully (always return 200)
        """
        _logger.info("TiloPay webhook received: %s", request.httprequest.url)

        try:
            # Get webhook payload
            payload = request.jsonrequest
            _logger.info("Webhook payload: %s", json.dumps(payload, indent=2))

            # TODO (Phase 4): Extract signature from headers
            # signature = request.httprequest.headers.get('X-TiloPay-Signature')
            # if not signature:
            #     _logger.error("SECURITY: Webhook missing signature header!")
            #     return {'status': 'error', 'message': 'Missing signature'}

            # TODO (Phase 4): Get raw request body for signature verification
            # raw_payload = request.httprequest.get_data()

            # Find payment provider to get secret key
            provider = request.env['payment.provider'].sudo().search([
                ('code', '=', 'tilopay'),
                ('state', '=', 'enabled'),
            ], limit=1)

            if not provider:
                _logger.error("TiloPay provider not found or not enabled")
                return {'status': 'error', 'message': 'Provider not configured'}

            # TODO (Phase 4): Verify webhook signature
            # client = provider._tilopay_get_api_client()
            # is_valid = client.verify_webhook_signature(
            #     payload=raw_payload,
            #     signature=signature,
            #     secret_key=provider.tilopay_secret_key
            # )
            #
            # if not is_valid:
            #     _logger.error("SECURITY: Invalid webhook signature detected!")
            #     return {'status': 'error', 'message': 'Invalid signature'}

            # Find transaction by payment_id
            payment_id = payload.get('payment_id')
            if not payment_id:
                _logger.error("Webhook missing payment_id")
                return {'status': 'error', 'message': 'Missing payment_id'}

            transaction = request.env['payment.transaction'].sudo().search([
                ('tilopay_payment_id', '=', payment_id)
            ], limit=1)

            if not transaction:
                _logger.error("Transaction not found for payment_id: %s", payment_id)
                return {'status': 'error', 'message': 'Transaction not found'}

            # Process notification
            _logger.info("Processing webhook for transaction %s", transaction.id)

            # TODO (Phase 4): Uncomment when transaction method is implemented
            # transaction._tilopay_process_notification(payload)

            _logger.warning("SKELETON: Webhook processing not yet implemented (Phase 4)")

            _logger.info("Webhook processed successfully for transaction %s", transaction.id)
            return {'status': 'success'}

        except Exception as e:
            _logger.exception("Error processing TiloPay webhook")
            # Always return 200 to prevent TiloPay from retrying
            # Log the error for manual investigation
            return {'status': 'error', 'message': 'Internal error'}

    @http.route('/payment/tilopay/return', type='http', auth='public', methods=['GET'], website=True)
    def tilopay_return(self, reference=None, **kwargs):
        """
        Handle customer return after completing payment on TiloPay page.

        This endpoint:
        1. Customer is redirected here after payment (success or failure)
        2. Displays payment status message
        3. Shows link back to invoice or member portal

        Query parameters:
        - reference: Transaction reference
        - status: Payment status (optional, from TiloPay redirect)

        Returns:
            Rendered HTML page showing payment status

        TODO (Phase 4): Implement return page rendering
        - Find transaction by reference
        - Check transaction state (done, pending, error)
        - Render appropriate template with status message
        - Show link to invoice or portal dashboard
        """
        _logger.info("TiloPay return URL accessed: reference=%s", reference)

        if not reference:
            return request.render('payment_tilopay.payment_error', {
                'error_message': _('Missing payment reference')
            })

        # Find transaction
        transaction = request.env['payment.transaction'].sudo().search([
            ('reference', '=', reference)
        ], limit=1)

        if not transaction:
            _logger.error("Transaction not found for reference: %s", reference)
            return request.render('payment_tilopay.payment_error', {
                'error_message': _('Payment transaction not found')
            })

        # Prepare template values
        template_values = {
            'transaction': transaction,
            'invoice': transaction.invoice_ids[0] if transaction.invoice_ids else None,
            'status': kwargs.get('status'),
        }

        # Render appropriate template based on state
        if transaction.state == 'done':
            template = 'payment_tilopay.payment_success'
        elif transaction.state in ['error', 'cancel']:
            template = 'payment_tilopay.payment_failed'
        else:
            # Still pending
            template = 'payment_tilopay.payment_pending'

        # TODO (Phase 4): Create actual templates
        # For now, return placeholder
        _logger.warning("SKELETON: Return page templates not yet created (Phase 4)")

        return f"""
        <html>
        <head><title>Payment Status</title></head>
        <body>
            <h1>Payment Status: {transaction.state.upper()}</h1>
            <p>Reference: {reference}</p>
            <p>Amount: {transaction.amount} {transaction.currency_id.name}</p>
            <hr>
            <p><strong>SKELETON:</strong> This is a placeholder page.</p>
            <p>Actual payment status page will be implemented in Phase 4.</p>
            <p><a href="/my/invoices">Back to Invoices</a></p>
        </body>
        </html>
        """
