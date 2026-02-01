# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Electronic Invoice Fields
    l10n_cr_einvoice_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='Electronic Invoice',
        readonly=True,
        copy=False,
    )

    l10n_cr_einvoice_state = fields.Selection(
        related='l10n_cr_einvoice_id.state',
        string='E-Invoice Status',
        store=True,
    )

    l10n_cr_clave = fields.Char(
        related='l10n_cr_einvoice_id.clave',
        string='Hacienda Key',
        store=True,
        copy=False,
    )

    l10n_cr_requires_einvoice = fields.Boolean(
        string='Requires Electronic Invoice',
        compute='_compute_requires_einvoice',
        store=True,
    )

    # XML Import Batch (Phase 3)
    l10n_cr_import_batch_id = fields.Many2one(
        'l10n_cr.einvoice.import.batch',
        string='Import Batch',
        readonly=True,
        copy=False,
        help='Batch from which this invoice was imported via XML',
    )

    # Payment Method Fields (Phase 1A)
    l10n_cr_payment_method_id = fields.Many2one(
        'l10n_cr.payment.method',
        string='Payment Method (CR)',
        help='Costa Rica payment method for electronic invoicing (required by Hacienda)',
        copy=False,
        tracking=True,
    )

    l10n_cr_payment_transaction_id = fields.Char(
        string='Transaction ID',
        size=50,
        help='Transaction ID for SINPE Móvil or card payments',
        copy=False,
        tracking=True,
    )

    @api.depends('move_type', 'country_code', 'company_id')
    def _compute_requires_einvoice(self):
        """Determine if this invoice requires electronic invoicing."""
        for move in self:
            # Require e-invoice for Costa Rica customer invoices
            move.l10n_cr_requires_einvoice = (
                move.move_type in ['out_invoice', 'out_refund']
                and move.country_code == 'CR'
                and move.company_id.country_id.code == 'CR'
            )

    @api.model
    def _get_default_payment_method(self):
        """Get default payment method (01 - Efectivo)."""
        return self.env.ref('l10n_cr_einvoice.payment_method_efectivo', raise_if_not_found=False)

    @api.onchange('l10n_cr_payment_method_id')
    def _onchange_payment_method(self):
        """Clear transaction ID if payment method doesn't require it."""
        if self.l10n_cr_payment_method_id and not self.l10n_cr_payment_method_id.requires_transaction_id:
            self.l10n_cr_payment_transaction_id = False

    def _validate_payment_method_transaction_id(self):
        """Validate that SINPE Móvil has transaction ID."""
        self.ensure_one()

        if not self.l10n_cr_requires_einvoice:
            return True

        # If no payment method selected, set default
        if not self.l10n_cr_payment_method_id:
            default_method = self._get_default_payment_method()
            if default_method:
                self.l10n_cr_payment_method_id = default_method
                _logger.info(f'Auto-assigned default payment method "01-Efectivo" to invoice {self.name}')
            else:
                raise UserError(_(
                    'Payment method is required for Costa Rica electronic invoicing.\n'
                    'Please select a payment method before posting this invoice.'
                ))

        # Validate SINPE Móvil requires transaction ID
        if self.l10n_cr_payment_method_id.requires_transaction_id:
            if not self.l10n_cr_payment_transaction_id:
                raise UserError(_(
                    'Transaction ID is required for payment method "%s".\n\n'
                    'Please enter the transaction ID provided by the payment system.'
                ) % self.l10n_cr_payment_method_id.name)

        return True

    def action_post(self):
        """Override post to validate payment method and auto-generate e-invoice for CR."""
        # Validate payment method for CR invoices BEFORE posting
        for move in self:
            if move.l10n_cr_requires_einvoice:
                move._validate_payment_method_transaction_id()

        res = super(AccountMove, self).action_post()

        for move in self:
            if move.l10n_cr_requires_einvoice and not move.l10n_cr_einvoice_id:
                # Auto-create e-invoice document
                if move.company_id.l10n_cr_auto_generate_einvoice:
                    try:
                        move._create_einvoice_document()
                    except Exception as e:
                        # Log error but don't block invoice posting
                        _logger.error(f'Failed to auto-create e-invoice for {move.name}: {str(e)}')

        return res

    def action_create_einvoice(self):
        """Manual action to create electronic invoice document."""
        self.ensure_one()

        if not self.l10n_cr_requires_einvoice:
            raise UserError(_('This invoice does not require electronic invoicing.'))

        if self.l10n_cr_einvoice_id:
            raise UserError(_('Electronic invoice already exists for this document.'))

        if self.state != 'posted':
            raise UserError(_('Invoice must be posted before creating electronic invoice.'))

        # Validate payment method
        self._validate_payment_method_transaction_id()

        self._create_einvoice_document()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Electronic Invoice'),
            'res_model': 'l10n_cr.einvoice.document',
            'res_id': self.l10n_cr_einvoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_einvoice_document(self):
        """Create the electronic invoice document."""
        self.ensure_one()

        # Determine document type
        doc_type = self._get_einvoice_document_type()

        # Create e-invoice document
        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': self.id,
            'document_type': doc_type,
            'company_id': self.company_id.id,
        })

        self.l10n_cr_einvoice_id = einvoice.id

        _logger.info(f'Created e-invoice document {einvoice.name} for invoice {self.name}')

        return einvoice

    def _get_einvoice_document_type(self):
        """Determine the electronic document type based on invoice type."""
        self.ensure_one()

        if self.move_type == 'out_invoice':
            # Check if it's a simplified invoice (tiquete)
            if self.amount_total <= 1000000:  # Below 1M CRC threshold
                return 'TE'
            return 'FE'
        elif self.move_type == 'out_refund':
            return 'NC'
        else:
            return 'FE'

    def action_generate_and_send_einvoice(self):
        """Complete workflow: generate XML, sign, submit, and email."""
        self.ensure_one()

        if not self.l10n_cr_einvoice_id:
            self._create_einvoice_document()

        einvoice = self.l10n_cr_einvoice_id

        # Generate XML
        if einvoice.state == 'draft':
            einvoice.action_generate_xml()

        # Sign XML
        if einvoice.state == 'generated':
            einvoice.action_sign_xml()

        # Submit to Hacienda
        if einvoice.state == 'signed':
            einvoice.action_submit_to_hacienda()

        # Send email if accepted
        if einvoice.state == 'accepted' and not einvoice.email_sent:
            self._send_einvoice_email()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Electronic Invoice'),
            'res_model': 'l10n_cr.einvoice.document',
            'res_id': einvoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _send_einvoice_email(self):
        """Send email with electronic invoice attachments."""
        self.ensure_one()

        if not self.l10n_cr_einvoice_id:
            return

        einvoice = self.l10n_cr_einvoice_id

        # Prepare email
        template = self.env.ref('l10n_cr_einvoice.email_template_einvoice', raise_if_not_found=False)

        if template:
            template.send_mail(self.id, force_send=True)

            einvoice.write({
                'email_sent': True,
                'email_sent_date': fields.Datetime.now(),
            })

            _logger.info(f'Sent e-invoice email for {self.name}')
