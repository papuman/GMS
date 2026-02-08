# -*- coding: utf-8 -*-
import base64
import logging
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HaciendaResponseMessage(models.Model):
    """
    Storage model for Hacienda API response messages.

    Stores all acceptance/rejection messages from Hacienda for audit trail,
    compliance, and troubleshooting purposes.
    """
    _name = 'l10n_cr.hacienda.response.message'
    _description = 'Hacienda Response Message Repository'
    _order = 'response_date desc, id desc'
    _rec_name = 'display_name'

    # Identification
    name = fields.Char(
        string='Message ID',
        required=True,
        index=True,
        help='Unique identifier for this response message',
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )

    # Related Document
    document_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='E-Invoice Document',
        required=True,
        ondelete='cascade',
        index=True,
    )

    clave = fields.Char(
        string='Document Clave',
        related='document_id.clave',
        store=True,
        index=True,
        help='50-digit electronic document key',
    )

    # Message Type
    message_type = fields.Selection([
        ('acceptance', 'Acceptance Message'),
        ('rejection', 'Rejection Message'),
        ('partial_acceptance', 'Partial Acceptance'),
        ('confirmation', 'Confirmation Message'),
        ('other', 'Other'),
    ], string='Message Type', required=True, index=True)

    # Response Data
    response_date = fields.Datetime(
        string='Response Date',
        required=True,
        index=True,
        help='Date and time of response from Hacienda',
    )

    status = fields.Char(
        string='Status Code',
        index=True,
        help='Status code from Hacienda (aceptado, rechazado, etc.)',
    )

    # XML Content
    raw_xml = fields.Text(
        string='Raw XML Response',
        help='Complete XML response as received from Hacienda',
    )

    decoded_xml = fields.Text(
        string='Decoded XML',
        help='Decoded XML content (if base64 encoded)',
    )

    base64_content = fields.Text(
        string='Base64 Encoded Content',
        help='Original base64 encoded content from respuesta-xml field',
    )

    # Error Information
    error_code = fields.Char(
        string='Error Code',
        index=True,
        help='Error code if message indicates rejection or error',
    )

    error_description = fields.Text(
        string='Error Description',
        help='Detailed error description from Hacienda',
    )

    # Metadata
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    create_date = fields.Datetime(
        string='Stored Date',
        readonly=True,
        help='Date when this response was stored in the system',
    )

    # Additional Fields
    is_final = fields.Boolean(
        string='Final Response',
        default=True,
        help='Indicates if this is the final response (not intermediate)',
    )

    response_number = fields.Integer(
        string='Response Number',
        help='Sequential number if multiple responses received',
    )

    # Computed Fields
    has_error = fields.Boolean(
        string='Has Error',
        compute='_compute_has_error',
        store=True,
    )

    @api.depends('name', 'message_type', 'clave')
    def _compute_display_name(self):
        """Compute display name for better UI presentation."""
        for record in self:
            type_label = dict(self._fields['message_type'].selection).get(record.message_type, 'Message')
            clave_short = record.clave[:20] + '...' if record.clave else 'N/A'
            record.display_name = f"{type_label} - {clave_short}"

    @api.depends('error_code', 'error_description', 'message_type')
    def _compute_has_error(self):
        """Determine if this response contains an error."""
        for record in self:
            record.has_error = bool(
                record.error_code or
                record.error_description or
                record.message_type == 'rejection'
            )

    @api.model
    def create_from_hacienda_response(self, document, response):
        """
        Create a response message record from Hacienda API response.

        Args:
            document (recordset): E-invoice document record
            response (dict): Response dictionary from Hacienda API

        Returns:
            recordset: Created response message record
        """
        # Extract data from response
        status = response.get('ind-estado', '').lower()
        raw_xml = response.get('respuesta-xml', '')
        decoded_xml = response.get('respuesta-xml-decoded', '')
        error_details = response.get('error_details', '')

        # Determine message type
        message_type = self._determine_message_type(status, response)

        # Extract error information
        error_code, error_description = self._extract_error_info(response, decoded_xml)

        # Generate unique name
        name = self._generate_message_name(document, status)

        # Get response number (sequential for same document)
        response_number = self.search_count([('document_id', '=', document.id)]) + 1

        # Create record
        values = {
            'name': name,
            'document_id': document.id,
            'message_type': message_type,
            'response_date': fields.Datetime.now(),
            'status': status,
            'raw_xml': raw_xml or False,
            'decoded_xml': decoded_xml or False,
            'base64_content': raw_xml if raw_xml and not decoded_xml else False,
            'error_code': error_code,
            'error_description': error_description,
            'company_id': document.company_id.id,
            'response_number': response_number,
            'is_final': status in ['aceptado', 'rechazado'],
        }

        message = self.create(values)

        _logger.info(
            f'Stored Hacienda response for document {document.name}: '
            f'{message_type} ({status})'
        )

        return message

    @api.model
    def _determine_message_type(self, status, response):
        """
        Determine the message type based on status and response content.

        Args:
            status (str): Status from Hacienda
            response (dict): Full response dictionary

        Returns:
            str: Message type selection value
        """
        status_map = {
            'aceptado': 'acceptance',
            'rechazado': 'rejection',
            'procesando': 'confirmation',
            'recibido': 'confirmation',
        }

        return status_map.get(status, 'other')

    @api.model
    def _extract_error_info(self, response, decoded_xml):
        """
        Extract error code and description from response.

        Args:
            response (dict): Response dictionary
            decoded_xml (str): Decoded XML content

        Returns:
            tuple: (error_code, error_description)
        """
        error_code = None
        error_description = None

        # Try to get from response dict
        error_description = response.get('error_details', '')

        # Try to parse from XML if available
        if decoded_xml:
            try:
                root = etree.fromstring(decoded_xml.encode('utf-8'))

                # Look for common error elements
                # Namespace-aware search
                namespaces = root.nsmap

                # Try common error paths
                error_paths = [
                    './/{*}CodigoMensaje',
                    './/{*}MensajeDetalle',
                    './/{*}DetalleMensaje',
                ]

                for path in error_paths:
                    elements = root.xpath(path)
                    if elements:
                        if 'Codigo' in path:
                            error_code = elements[0].text
                        else:
                            error_description = elements[0].text

            except Exception as e:
                _logger.warning(f'Failed to parse error from XML: {e}')

        return error_code, error_description

    @api.model
    def _generate_message_name(self, document, status):
        """
        Generate unique name for response message.

        Args:
            document (recordset): E-invoice document
            status (str): Response status

        Returns:
            str: Unique message name
        """
        sequence = self.env['ir.sequence'].next_by_code('l10n_cr.hacienda.response')
        if not sequence:
            # Fallback if sequence not exists
            sequence = f"RESP-{len(self.search([]))}"

        return f"{sequence}-{document.name}-{status}"

    def action_view_xml(self):
        """View the XML content in a dialog."""
        self.ensure_one()

        xml_content = self.decoded_xml or self.raw_xml

        if not xml_content:
            raise UserError(_('No XML content available for this response.'))

        # Format XML for display
        try:
            if self.decoded_xml:
                root = etree.fromstring(self.decoded_xml.encode('utf-8'))
                formatted_xml = etree.tostring(
                    root,
                    pretty_print=True,
                    encoding='unicode'
                )
            else:
                formatted_xml = xml_content
        except Exception:
            formatted_xml = xml_content

        # Return wizard to display XML
        return {
            'name': _('Response XML Content'),
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_cr.xml.viewer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_xml_content': formatted_xml,
                'default_title': f'Hacienda Response - {self.display_name}',
            },
        }

    def action_download_xml(self):
        """Download XML as file."""
        self.ensure_one()

        xml_content = self.decoded_xml or self.raw_xml

        if not xml_content:
            raise UserError(_('No XML content available for this response.'))

        # Create attachment
        filename = f'hacienda_response_{self.clave}_{self.response_number}.xml'

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(xml_content.encode('utf-8')),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/xml',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    @api.model
    def cleanup_old_messages(self, days=90):
        """
        Clean up old response messages to prevent database bloat.

        Args:
            days (int): Keep messages newer than this many days

        Returns:
            int: Number of messages deleted
        """
        cutoff_date = fields.Datetime.now() - timedelta(days=days)

        old_messages = self.search([
            ('create_date', '<', cutoff_date),
            ('is_final', '=', True),  # Only delete final responses
        ])

        count = len(old_messages)
        old_messages.unlink()

        _logger.info(f'Cleaned up {count} old Hacienda response messages (older than {days} days)')

        return count

    @api.model
    def get_statistics(self, company_id=None, date_from=None, date_to=None):
        """
        Get statistics for response messages.

        Args:
            company_id (int, optional): Filter by company
            date_from (datetime, optional): Start date
            date_to (datetime, optional): End date

        Returns:
            dict: Statistics dictionary
        """
        domain = []

        if company_id:
            domain.append(('company_id', '=', company_id))
        if date_from:
            domain.append(('response_date', '>=', date_from))
        if date_to:
            domain.append(('response_date', '<=', date_to))

        messages = self.search(domain)

        stats = {
            'total': len(messages),
            'acceptances': len(messages.filtered(lambda m: m.message_type == 'acceptance')),
            'rejections': len(messages.filtered(lambda m: m.message_type == 'rejection')),
            'confirmations': len(messages.filtered(lambda m: m.message_type == 'confirmation')),
            'with_errors': len(messages.filtered(lambda m: m.has_error)),
            'final_responses': len(messages.filtered(lambda m: m.is_final)),
        }

        # Calculate acceptance rate
        final_count = stats['final_responses']
        if final_count > 0:
            stats['acceptance_rate'] = (stats['acceptances'] / final_count) * 100
        else:
            stats['acceptance_rate'] = 0.0

        return stats
