# -*- coding: utf-8 -*-
"""
Phase 4 additions to einvoice_document model.

This file extends the einvoice_document model with Phase 4 PDF and Email fields.
It's designed to be merged into einvoice_document.py or loaded as inheritance.
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoiceDocumentPhase4(models.Model):
    """
    Phase 4 extensions for E-Invoice Document model.

    Adds PDF generation and email delivery capabilities with advanced features:
    - PDF file storage
    - Email sending tracking
    - Retry logic for failed emails
    - Error tracking
    """
    _inherit = 'l10n_cr.einvoice.document'

    # Phase 4: Additional PDF fields
    pdf_file = fields.Binary(
        string='PDF File (Binary)',
        attachment=True,
        help='PDF file content stored directly (alternative to attachment)',
    )

    pdf_filename = fields.Char(
        string='PDF Filename',
        compute='_compute_pdf_filename',
        store=True,
        help='Generated PDF filename based on clave',
    )

    # Phase 4: Email retry and error fields
    email_error = fields.Text(
        string='Email Error Message',
        readonly=True,
        help='Error message from last failed email send attempt',
    )

    email_retry_count = fields.Integer(
        string='Email Retry Count',
        default=0,
        readonly=True,
        help='Number of email send retry attempts (max 3)',
    )

    @api.depends('clave', 'document_type')
    def _compute_pdf_filename(self):
        """
        Compute PDF filename based on document type and clave.

        Format: {DocumentType}_{Clave}.pdf
        """
        for record in self:
            if record.clave:
                doc_type_prefix = {
                    'FE': 'FacturaElectronica',
                    'TE': 'TiqueteElectronico',
                    'NC': 'NotaCreditoElectronica',
                    'ND': 'NotaDebitoElectronica',
                }.get(record.document_type, 'Documento')

                record.pdf_filename = f'{doc_type_prefix}_{record.clave}.pdf'
            else:
                record.pdf_filename = f'{record.document_type}_{record.name or "draft"}.pdf'

    def action_preview_email(self):
        """
        Preview email that would be sent to customer.

        Opens email composition wizard with populated template.

        Returns:
            dict: Action to open email composition wizard
        """
        self.ensure_one()

        # Get appropriate email template
        email_sender = self.env['l10n_cr.einvoice.email.sender']
        template = email_sender._get_email_template(self)

        if not template:
            raise UserError(_('No email template configured for this document type'))

        # Get email composition wizard
        composer = self.env['mail.compose.message'].with_context(
            default_composition_mode='comment',
            default_model=self._name,
            default_res_id=self.id,
            default_template_id=template.id,
            default_partner_ids=[(6, 0, [self.partner_id.id])],
        ).create({})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Preview Email'),
            'res_model': 'mail.compose.message',
            'res_id': composer.id,
            'view_mode': 'form',
            'target': 'new',
            'views': [(False, 'form')],
        }

    def action_send_email_manual(self):
        """
        Manually send email to customer (with confirmation).

        Similar to action_send_email but includes user confirmation.

        Returns:
            dict: Success notification or wizard
        """
        self.ensure_one()

        # Delegate to email sender service
        email_sender = self.env['l10n_cr.einvoice.email.sender']

        if email_sender.send_email_for_document(self, force_send=True):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Email sent successfully to %s') % self.partner_id.email,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to send email. Check error details.'),
                    'type': 'warning',
                    'sticky': True,
                }
            }

    def action_regenerate_pdf(self):
        """
        Regenerate PDF file (useful if template changed).

        Returns:
            dict: Success notification
        """
        self.ensure_one()

        # Generate new PDF
        pdf_generator = self.env['l10n_cr.einvoice.pdf.generator']
        pdf_generator.create_pdf_attachment(self)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('PDF regenerated successfully'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _auto_send_email_on_acceptance(self):
        """
        Override Phase 3 method to use new email sender service.

        Automatically send email when document is accepted by Hacienda.
        """
        self.ensure_one()

        # Check if auto-send is enabled
        if not self.company_id.l10n_cr_auto_send_email:
            _logger.debug(f'Auto-send email disabled for company {self.company_id.name}')
            return

        # Use Phase 4 email sender
        email_sender = self.env['l10n_cr.einvoice.email.sender']
        email_sender.auto_send_on_acceptance(self)
