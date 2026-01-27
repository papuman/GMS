# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class EInvoiceImportError(models.Model):
    _name = 'l10n_cr.einvoice.import.error'
    _description = 'E-Invoice Import Error'
    _order = 'create_date desc'

    batch_id = fields.Many2one(
        'l10n_cr.einvoice.import.batch',
        string='Import Batch',
        required=True,
        ondelete='cascade',
    )

    file_name = fields.Char(
        string='File Name',
        required=True,
    )

    error_type = fields.Selection([
        ('xml_parse', 'XML Parsing Error'),
        ('validation', 'Validation Error'),
        ('duplicate', 'Duplicate Invoice'),
        ('partner_not_found', 'Partner Not Found'),
        ('product_not_found', 'Product Not Found'),
        ('tax_config', 'Tax Configuration Error'),
        ('other', 'Other Error'),
    ], string='Error Type', required=True, default='other')

    error_message = fields.Text(
        string='Error Message',
        required=True,
    )

    clave = fields.Char(
        string='Clave',
        help='50-digit key from XML (if parsed)',
    )

    consecutive = fields.Char(
        string='Consecutive',
        help='Consecutive number from XML (if parsed)',
    )

    xml_content = fields.Binary(
        string='XML Content',
        attachment=True,
        help='Failed XML file for debugging',
    )

    is_resolved = fields.Boolean(
        string='Resolved',
        default=False,
    )

    resolution_notes = fields.Text(
        string='Resolution Notes',
    )

    @api.model
    def create_error(self, batch_id, file_name, error_type, error_message, clave=None, consecutive=None, xml_content=None):
        """Helper method to create error records."""
        vals = {
            'batch_id': batch_id.id if hasattr(batch_id, 'id') else batch_id,
            'file_name': file_name,
            'error_type': error_type,
            'error_message': error_message,
        }

        if clave:
            vals['clave'] = clave
        if consecutive:
            vals['consecutive'] = consecutive
        if xml_content:
            vals['xml_content'] = xml_content

        return self.create(vals)

    def action_mark_resolved(self):
        """Mark error as resolved."""
        self.write({'is_resolved': True})

    def action_retry_import(self):
        """Retry importing this failed file."""
        # This will be implemented as part of Day 9 (error handling)
        pass
