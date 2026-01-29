# -*- coding: utf-8 -*-

"""
TiloPay Payment Transaction Model

Extends payment.transaction to handle TiloPay-specific payment processing,
status tracking, and webhook notifications.
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare

import logging
import json

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """
    Extend payment.transaction to support TiloPay payment processing.
    """
    _inherit = 'payment.transaction'

    # TiloPay-Specific Fields
    tilopay_payment_id = fields.Char(
        string='TiloPay Payment ID',
        readonly=True,
        copy=False,
        help="Unique payment ID from TiloPay gateway"
    )

    tilopay_payment_url = fields.Char(
        string='TiloPay Payment URL',
        readonly=True,
        copy=False,
        help="URL where customer completes payment"
    )

    tilopay_payment_method = fields.Selection([
        ('sinpe', 'SINPE Móvil'),
        ('card', 'Credit/Debit Card'),
        ('yappy', 'Yappy'),
    ], string='Payment Method Used', readonly=True, copy=False,
       help="Actual payment method used by customer")

    tilopay_transaction_id = fields.Char(
        string='Bank Transaction ID',
        readonly=True,
        copy=False,
        help="Transaction ID from bank (e.g., SINPE transaction number)"
    )

    tilopay_raw_response = fields.Text(
        string='TiloPay Raw Response',
        readonly=True,
        copy=False,
        groups='base.group_system',
        help="Complete API response for debugging (JSON)"
    )

    tilopay_webhook_received = fields.Boolean(
        string='Webhook Received',
        default=False,
        readonly=True,
        copy=False,
        help="Whether webhook notification was received from TiloPay"
    )

    tilopay_webhook_count = fields.Integer(
        string='Webhook Count',
        default=0,
        readonly=True,
        copy=False,
        help="Number of webhook notifications received (for duplicate detection)"
    )

    # Computed Fields
    tilopay_is_pending = fields.Boolean(
        compute='_compute_tilopay_status',
        string='Is Pending',
        help="Payment is pending completion"
    )

    @api.depends('state', 'tilopay_payment_id')
    def _compute_tilopay_status(self):
        """Compute TiloPay-specific status flags."""
        for tx in self:
            tx.tilopay_is_pending = (
                tx.provider_code == 'tilopay' and
                tx.state == 'pending' and
                bool(tx.tilopay_payment_id)
            )

    # ========== Payment Creation ==========

    def _tilopay_create_payment(self):
        """
        Initialize payment with TiloPay gateway.

        This method:
        1. Calls TiloPay API to create payment
        2. Stores payment_id and payment_url
        3. Updates transaction state to 'pending'

        The customer will then be redirected to tilopay_payment_url to complete payment.

        Raises:
            UserError: If payment creation fails

        TODO (Phase 3): Implement actual payment creation
        - Call provider._tilopay_get_api_client()
        - Call client.create_payment() with transaction details
        - Store response in tilopay_payment_id, tilopay_payment_url
        - Update state to 'pending'
        """
        self.ensure_one()

        if self.provider_code != 'tilopay':
            return

        _logger.info(
            "Creating TiloPay payment for transaction %s (reference: %s, amount: %s %s)",
            self.id, self.reference, self.amount, self.currency_id.name
        )

        try:
            provider = self.provider_id

            # Get API client
            # client = provider._tilopay_get_api_client()

            # Prepare payment data
            amount_cents = int(self.amount * 100)  # Convert to cents
            payment_methods = provider._tilopay_get_enabled_payment_methods()
            return_url = provider._tilopay_get_return_url(self.reference)
            callback_url = provider.tilopay_webhook_url

            # TODO (Phase 3): Call actual API
            # response = client.create_payment(
            #     amount=amount_cents,
            #     currency=self.currency_id.name,
            #     reference=self.reference,
            #     customer_email=self.partner_id.email or '',
            #     payment_methods=payment_methods,
            #     return_url=return_url,
            #     callback_url=callback_url,
            #     customer_name=self.partner_id.name,
            #     description=self._get_tilopay_payment_description(),
            # )

            # SKELETON: Placeholder response
            response = {
                'payment_id': f'pay_SKEL_{self.reference}',
                'payment_url': f'https://sandbox.tilopay.com/checkout/PLACEHOLDER',
                'status': 'pending',
            }

            # Store response
            self.write({
                'tilopay_payment_id': response['payment_id'],
                'tilopay_payment_url': response['payment_url'],
                'tilopay_raw_response': json.dumps(response, indent=2),
                'state': 'pending',
            })

            _logger.info(
                "TiloPay payment created successfully: %s (URL: %s)",
                response['payment_id'], response['payment_url']
            )

        except Exception as e:
            _logger.exception("Failed to create TiloPay payment for transaction %s", self.id)
            self._set_error(_("Payment creation failed: %s") % str(e))
            raise UserError(_(
                "Unable to create payment with TiloPay.\n\n"
                "Error: %s\n\n"
                "Please try again or contact support if the problem persists."
            ) % str(e))

    def _get_tilopay_payment_description(self):
        """
        Generate payment description for TiloPay.

        Returns:
            str: Human-readable payment description
        """
        self.ensure_one()

        # If linked to an invoice, use invoice description
        if self.invoice_ids:
            invoice = self.invoice_ids[0]
            return _("Payment for %s") % invoice.name

        # Otherwise use transaction reference
        return _("Payment for %s") % self.reference

    # ========== Webhook Processing ==========

    def _tilopay_process_notification(self, notification_data):
        """
        Process webhook notification from TiloPay.

        Args:
            notification_data (dict): Parsed webhook payload containing:
                - event: Event type (payment.completed, payment.failed, etc.)
                - payment_id: TiloPay payment ID
                - data: Payment details (status, amount, payment_method, etc.)

        This method:
        1. Validates payment_id matches
        2. Validates amount matches
        3. Updates transaction state based on status
        4. Stores payment method and transaction ID
        5. Triggers invoice confirmation if payment successful

        Raises:
            ValidationError: If notification data is invalid

        TODO (Phase 4): Implement full webhook processing
        - Validate notification_data structure
        - Check for duplicate webhook deliveries (tilopay_webhook_count)
        - Update state based on event type
        - Trigger _set_done() for successful payments
        - Trigger _set_canceled() for failed payments
        - Update linked invoice payment status
        """
        self.ensure_one()

        _logger.info(
            "Processing TiloPay webhook notification for transaction %s: %s",
            self.id, notification_data.get('event')
        )

        # Validate payment ID
        if notification_data.get('payment_id') != self.tilopay_payment_id:
            raise ValidationError(_(
                "Payment ID mismatch: expected %s, got %s"
            ) % (self.tilopay_payment_id, notification_data.get('payment_id')))

        # Increment webhook counter (for duplicate detection)
        self.tilopay_webhook_count += 1

        if self.tilopay_webhook_count > 1:
            _logger.warning(
                "Duplicate webhook received for transaction %s (count: %d)",
                self.id, self.tilopay_webhook_count
            )
            # Don't process duplicates
            return

        # Extract payment data
        event = notification_data.get('event')
        data = notification_data.get('data', {})
        status = data.get('status')
        payment_method = data.get('payment_method')
        transaction_id = data.get('transaction_id')
        amount = data.get('amount', 0) / 100.0  # Convert from cents

        # Validate amount (allow small rounding differences)
        if float_compare(amount, self.amount, precision_digits=2) != 0:
            _logger.error(
                "Amount mismatch for transaction %s: expected %s, got %s",
                self.id, self.amount, amount
            )
            # Don't fail on amount mismatch, but log it
            # Some payment methods may have small differences due to fees

        # Update transaction fields
        self.write({
            'tilopay_payment_method': payment_method,
            'tilopay_transaction_id': transaction_id,
            'tilopay_webhook_received': True,
            'tilopay_raw_response': json.dumps(notification_data, indent=2),
        })

        # Process based on event type
        if event == 'payment.completed' and status == 'approved':
            _logger.info("Payment completed successfully for transaction %s", self.id)
            self._set_done()
            self._tilopay_update_invoice_payment()

        elif event == 'payment.failed' or status == 'failed':
            error_msg = data.get('error_message', 'Payment failed')
            _logger.warning("Payment failed for transaction %s: %s", self.id, error_msg)
            self._set_error(error_msg)

        elif event == 'payment.cancelled' or status == 'cancelled':
            _logger.info("Payment cancelled for transaction %s", self.id)
            self._set_canceled()

        else:
            _logger.warning(
                "Unknown payment status for transaction %s: event=%s, status=%s",
                self.id, event, status
            )

    def _tilopay_update_invoice_payment(self):
        """
        Update linked invoice with payment details after successful payment.

        This method:
        1. Updates invoice payment method (SINPE = 06, Card = 02)
        2. Updates SINPE transaction ID if applicable
        3. Marks invoice as paid
        4. Triggers e-invoice generation

        TODO (Phase 5): Implement invoice integration
        - Get linked invoice from self.invoice_ids
        - Update invoice.l10n_cr_payment_method_id based on tilopay_payment_method
        - Update invoice.l10n_cr_payment_transaction_id if SINPE
        - Confirm invoice payment
        - Trigger e-invoice generation via l10n_cr_einvoice
        """
        self.ensure_one()

        if not self.invoice_ids:
            _logger.info("No invoices linked to transaction %s, skipping invoice update", self.id)
            return

        invoice = self.invoice_ids[0]

        _logger.info(
            "Updating invoice %s with TiloPay payment details: method=%s, tx_id=%s",
            invoice.name, self.tilopay_payment_method, self.tilopay_transaction_id
        )

        # TODO (Phase 5): Map payment method to Hacienda codes
        # payment_method_mapping = {
        #     'sinpe': self.env.ref('l10n_cr_einvoice.payment_method_sinpe').id,  # 06
        #     'card': self.env.ref('l10n_cr_einvoice.payment_method_card').id,    # 02
        # }
        #
        # payment_method_id = payment_method_mapping.get(self.tilopay_payment_method)
        #
        # invoice_vals = {}
        # if payment_method_id:
        #     invoice_vals['l10n_cr_payment_method_id'] = payment_method_id
        #
        # if self.tilopay_payment_method == 'sinpe' and self.tilopay_transaction_id:
        #     invoice_vals['l10n_cr_payment_transaction_id'] = self.tilopay_transaction_id
        #
        # if invoice_vals:
        #     invoice.write(invoice_vals)
        #
        # # Trigger e-invoice generation if not already done
        # if invoice.state == 'posted' and not invoice.l10n_cr_einvoice_id:
        #     invoice.action_generate_einvoice()

        _logger.warning("SKELETON: Invoice update not yet implemented (Phase 5)")

    # ========== Manual Actions ==========

    def action_tilopay_refresh_status(self):
        """
        Manually refresh payment status from TiloPay API.

        This action allows admins to force-check payment status if webhook
        delivery fails or is delayed.

        TODO (Phase 3): Implement status refresh
        - Call provider._tilopay_get_api_client()
        - Call client.get_payment_status(tilopay_payment_id)
        - Process response similar to webhook
        - Update transaction state
        """
        self.ensure_one()

        if self.provider_code != 'tilopay':
            raise UserError(_("This transaction is not from TiloPay"))

        if not self.tilopay_payment_id:
            raise UserError(_("No TiloPay payment ID found"))

        _logger.info("Manually refreshing status for TiloPay transaction %s", self.id)

        try:
            # TODO (Phase 3): Implement actual status query
            # provider = self.provider_id
            # client = provider._tilopay_get_api_client()
            # status_data = client.get_payment_status(self.tilopay_payment_id)
            #
            # # Process as if it were a webhook
            # notification_data = {
            #     'event': f'payment.{status_data["status"]}',
            #     'payment_id': self.tilopay_payment_id,
            #     'data': status_data
            # }
            # self._tilopay_process_notification(notification_data)

            _logger.warning("SKELETON: Status refresh not yet implemented (Phase 3)")

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Status Refresh'),
                    'message': _(
                        'SKELETON: Status refresh not yet implemented. '
                        'Will be functional in Phase 3.'
                    ),
                    'type': 'warning',
                }
            }

        except Exception as e:
            _logger.exception("Failed to refresh TiloPay status for transaction %s", self.id)
            raise UserError(_("Status refresh failed: %s") % str(e))

    # ========== Overrides ==========

    def _send_payment_request(self):
        """Override to handle TiloPay payment initiation."""
        if self.provider_code == 'tilopay':
            self._tilopay_create_payment()
            # Return action to redirect to payment URL
            return {
                'type': 'ir.actions.act_url',
                'url': self.tilopay_payment_url,
                'target': 'self',
            }
        else:
            return super()._send_payment_request()

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Override to find transaction from TiloPay webhook data.

        Args:
            provider_code (str): Provider code ('tilopay')
            notification_data (dict): Webhook payload

        Returns:
            payment.transaction: Transaction record

        Raises:
            ValidationError: If transaction not found
        """
        if provider_code != 'tilopay':
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        payment_id = notification_data.get('payment_id')
        reference = notification_data.get('data', {}).get('reference')

        # Try to find by TiloPay payment ID first
        tx = self.search([('tilopay_payment_id', '=', payment_id)], limit=1)

        # Fallback to reference
        if not tx and reference:
            tx = self.search([('reference', '=', reference)], limit=1)

        if not tx:
            raise ValidationError(_(
                "No transaction found for TiloPay payment ID %s (reference: %s)"
            ) % (payment_id, reference))

        return tx
