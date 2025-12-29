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

    @api.depends('move_type', 'company_id', 'company_id.country_id')
    def _compute_requires_einvoice(self):
        """Determine if this invoice requires electronic invoicing."""
        for move in self:
            # Require e-invoice for Costa Rica companies' customer invoices
            move.l10n_cr_requires_einvoice = (
                move.move_type in ['out_invoice', 'out_refund']
                and move.company_id.country_id.code == 'CR'
            )

    def action_post(self):
        """Override post to automatically generate e-invoice for CR."""
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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Costa Rica specific tax codes
    l10n_cr_tax_code = fields.Selection([
        ('01', 'IVA 13%'),
        ('02', 'IVA 4%'),
        ('03', 'IVA 2%'),
        ('04', 'IVA 1%'),
        ('05', 'Exento'),
        ('06', 'Gravado 0%'),
        ('07', 'No sujeto'),
        ('08', 'Exonerado'),
    ], string='CR Tax Code', help='Costa Rica tax code for electronic invoicing')

    l10n_cr_product_code = fields.Char(
        string='CR Product Code',
        help='Costa Rica product classification code (Cabys)',
    )

    @api.onchange('product_id')
    def _onchange_product_id_l10n_cr(self):
        """Set CR product code from product."""
        if self.product_id and self.product_id.l10n_cr_cabys_code:
            self.l10n_cr_product_code = self.product_id.l10n_cr_cabys_code
