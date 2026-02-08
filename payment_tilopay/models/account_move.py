# -*- coding: utf-8 -*-

"""
Account Move (Invoice) Extension for TiloPay

Adds "Pay Now" functionality to invoices for online payment via TiloPay.
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """
    Extend account.move to add TiloPay payment functionality.
    """
    _inherit = 'account.move'

    # TiloPay Payment Fields
    # NOTE: Odoo 19 defines transaction_ids on account.move via account_payment module.
    # payment_transaction_ids is kept as an alias for backward compatibility within this module.
    payment_transaction_ids = fields.Many2many(
        related='transaction_ids',
        string='Payment Transactions',
    )

    has_tilopay_payment = fields.Boolean(
        compute='_compute_has_tilopay_payment',
        string='Has TiloPay Payment',
        help="Invoice has at least one TiloPay payment transaction"
    )

    tilopay_payment_url = fields.Char(
        compute='_compute_tilopay_payment_url',
        string='TiloPay Payment URL',
        help="URL for customer to pay this invoice online"
    )

    can_pay_online = fields.Boolean(
        compute='_compute_can_pay_online',
        string='Can Pay Online',
        help="Invoice is eligible for online payment"
    )

    @api.depends('transaction_ids', 'transaction_ids.provider_code')
    def _compute_has_tilopay_payment(self):
        """Check if invoice has any TiloPay payment transactions."""
        for move in self:
            move.has_tilopay_payment = any(
                tx.provider_code == 'tilopay'
                for tx in move.payment_transaction_ids
            )

    @api.depends('transaction_ids', 'transaction_ids.state')
    def _compute_tilopay_payment_url(self):
        """Get active TiloPay payment URL if available."""
        for move in self:
            # Find most recent pending TiloPay transaction
            tilopay_tx = move.payment_transaction_ids.filtered(
                lambda tx: (
                    tx.provider_code == 'tilopay' and
                    tx.state == 'pending' and
                    tx.tilopay_payment_url
                )
            ).sorted('create_date', reverse=True)

            move.tilopay_payment_url = tilopay_tx[0].tilopay_payment_url if tilopay_tx else False

    @api.depends('move_type', 'state', 'payment_state', 'amount_residual')
    def _compute_can_pay_online(self):
        """Determine if invoice can be paid online with TiloPay."""
        for move in self:
            move.can_pay_online = (
                move.move_type == 'out_invoice' and          # Customer invoice
                move.state == 'posted' and                    # Invoice confirmed
                move.payment_state in ['not_paid', 'partial'] and  # Not fully paid
                move.amount_residual > 0 and                  # Has outstanding balance
                move.partner_id.email                         # Customer has email
            )

    def action_pay_online(self):
        """
        Create TiloPay payment transaction and redirect customer to payment page.

        This action:
        1. Validates invoice can be paid online
        2. Gets or creates TiloPay payment provider
        3. Creates payment.transaction
        4. Initializes payment with TiloPay
        5. Redirects to TiloPay payment URL

        Returns:
            dict: Action to redirect to payment URL

        Raises:
            UserError: If invoice cannot be paid online

        TODO (Phase 4): This will work once payment.transaction methods are implemented
        """
        self.ensure_one()

        # Validate invoice can be paid
        if not self.can_pay_online:
            raise UserError(_(
                "This invoice cannot be paid online.\n\n"
                "Requirements:\n"
                "- Must be a customer invoice\n"
                "- Must be confirmed (posted)\n"
                "- Must have outstanding balance\n"
                "- Customer must have email address"
            ))

        _logger.info("Creating online payment for invoice %s (amount: %s %s)",
                    self.name, self.amount_residual, self.currency_id.name)

        # Get TiloPay provider
        tilopay_provider = self.env['payment.provider'].search([
            ('code', '=', 'tilopay'),
            ('state', '=', 'enabled'),
        ], limit=1)

        if not tilopay_provider:
            raise UserError(_(
                "TiloPay payment provider is not configured or enabled.\n\n"
                "Please contact your system administrator to enable online payments."
            ))

        # Check if there's already a pending payment for this invoice
        existing_tx = self.payment_transaction_ids.filtered(
            lambda tx: (
                tx.provider_code == 'tilopay' and
                tx.state == 'pending' and
                tx.tilopay_payment_url
            )
        )

        if existing_tx:
            _logger.info("Reusing existing TiloPay transaction %s for invoice %s",
                        existing_tx[0].id, self.name)
            # Redirect to existing payment URL
            return {
                'type': 'ir.actions.act_url',
                'url': existing_tx[0].tilopay_payment_url,
                'target': 'self',
            }

        # Create new payment transaction
        transaction = self.env['payment.transaction'].create({
            'provider_id': tilopay_provider.id,
            'amount': self.amount_residual,
            'currency_id': self.currency_id.id,
            'reference': self._get_payment_reference(),
            'invoice_ids': [(6, 0, [self.id])],
            'partner_id': self.partner_id.id,
            'partner_email': self.partner_id.email,
            'partner_name': self.partner_id.name,
        })

        _logger.info("Created TiloPay transaction %s for invoice %s", transaction.id, self.name)

        # Initialize payment with TiloPay
        transaction._tilopay_create_payment()

        # Redirect to TiloPay payment page
        return {
            'type': 'ir.actions.act_url',
            'url': transaction.tilopay_payment_url,
            'target': 'self',
        }

    def _get_payment_reference(self):
        """
        Generate unique payment reference for transaction.

        Returns:
            str: Payment reference (e.g., 'INV/2025/0001')
        """
        self.ensure_one()
        return self.name

    # ========== Portal Methods ==========

    def _get_portal_invoice_payment_action(self):
        """
        Get portal action for paying invoice online.

        This is called from the portal invoice view to show "Pay Now" button.

        Returns:
            dict: Action configuration for portal

        TODO (Phase 4): Customize for member portal
        """
        if self.can_pay_online:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/my/invoices/{self.id}/pay',
                'target': 'self',
            }
        return {}
