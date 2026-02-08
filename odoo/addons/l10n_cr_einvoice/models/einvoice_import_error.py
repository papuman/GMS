# -*- coding: utf-8 -*-
import logging
import base64
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

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
        index=True,
    )

    file_name = fields.Char(
        string='File Name',
        required=True,
        index=True,
    )

    error_type = fields.Selection([
        ('xml_parse', 'XML Parsing Error'),
        ('xml_structure', 'Invalid XML Structure'),
        ('validation', 'Validation Error'),
        ('duplicate', 'Duplicate Invoice'),
        ('partner_not_found', 'Partner Not Found'),
        ('partner_creation', 'Partner Creation Failed'),
        ('product_not_found', 'Product Not Found'),
        ('product_creation', 'Product Creation Failed'),
        ('tax_config', 'Tax Configuration Error'),
        ('tax_mapping', 'Tax Mapping Error'),
        ('amount_mismatch', 'Amount Validation Failed'),
        ('currency_error', 'Currency Error'),
        ('invoice_creation', 'Invoice Creation Failed'),
        ('missing_data', 'Required Data Missing'),
        ('encoding_error', 'File Encoding Error'),
        ('network_error', 'Network/Connection Error'),
        ('permission_error', 'Permission/Access Error'),
        ('other', 'Other Error'),
    ], string='Error Type', required=True, default='other', index=True)

    error_category = fields.Selection([
        ('transient', 'Transient (Can Retry)'),
        ('config', 'Configuration Issue'),
        ('data', 'Data Quality Issue'),
        ('permanent', 'Permanent Error'),
    ], string='Error Category', compute='_compute_error_category', store=True)

    error_message = fields.Text(
        string='Error Message',
        required=True,
    )

    error_context = fields.Text(
        string='Error Context',
        help='Additional context about where and why the error occurred',
    )

    stack_trace = fields.Text(
        string='Stack Trace',
        help='Full stack trace for debugging (development only)',
    )

    clave = fields.Char(
        string='Clave',
        help='50-digit key from XML (if parsed)',
        index=True,
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

    xml_file_name = fields.Char(
        string='XML File Name',
        compute='_compute_xml_file_name',
    )

    is_resolved = fields.Boolean(
        string='Resolved',
        default=False,
        index=True,
    )

    resolution_notes = fields.Text(
        string='Resolution Notes',
    )

    retry_count = fields.Integer(
        string='Retry Attempts',
        default=0,
        help='Number of times this error has been retried',
    )

    last_retry_date = fields.Datetime(
        string='Last Retry Date',
        readonly=True,
    )

    can_retry = fields.Boolean(
        string='Can Retry',
        compute='_compute_can_retry',
        help='Whether this error can be retried automatically',
    )

    suggested_action = fields.Text(
        string='Suggested Action',
        compute='_compute_suggested_action',
        help='Recommended action to resolve this error',
    )

    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Severity', compute='_compute_severity', store=True)

    @api.depends('error_type')
    def _compute_error_category(self):
        """Categorize errors for better handling."""
        transient_types = [
            'network_error',
            'permission_error',
        ]

        config_types = [
            'tax_config',
            'tax_mapping',
            'currency_error',
        ]

        data_types = [
            'missing_data',
            'amount_mismatch',
            'partner_not_found',
            'product_not_found',
        ]

        for error in self:
            if error.error_type in transient_types:
                error.error_category = 'transient'
            elif error.error_type in config_types:
                error.error_category = 'config'
            elif error.error_type in data_types:
                error.error_category = 'data'
            else:
                error.error_category = 'permanent'

    @api.depends('error_category', 'retry_count', 'is_resolved')
    def _compute_can_retry(self):
        """Determine if error can be retried."""
        MAX_RETRIES = 3

        for error in self:
            # Already resolved - no retry needed
            if error.is_resolved:
                error.can_retry = False
                continue

            # Transient errors can always be retried
            if error.error_category == 'transient':
                error.can_retry = error.retry_count < MAX_RETRIES

            # Config errors can be retried after fixes
            elif error.error_category == 'config':
                error.can_retry = error.retry_count < 2

            # Data errors - only if auto-create is enabled
            elif error.error_category == 'data':
                error.can_retry = error.retry_count < 2

            # Permanent errors cannot be retried automatically
            else:
                error.can_retry = False

    @api.depends('error_type', 'error_category')
    def _compute_suggested_action(self):
        """Provide suggested actions for each error type."""
        suggestions = {
            'xml_parse': 'Verify XML file is valid and not corrupted. Check for encoding issues.',
            'xml_structure': 'Ensure XML follows Costa Rica e-invoice v4.4 schema.',
            'validation': 'Review XML data for completeness and format compliance.',
            'duplicate': 'Invoice with this clave already exists. This is expected behavior if re-importing.',
            'partner_not_found': 'Enable "Auto-Create Customers" option or create customer manually with VAT: {vat}',
            'partner_creation': 'Check partner data in XML. May need manual creation with proper identification.',
            'product_not_found': 'Enable "Auto-Create Products" option or create products with Cabys codes.',
            'product_creation': 'Review product data in XML. May need manual product creation.',
            'tax_config': 'Configure tax rates in Accounting > Configuration > Taxes for Costa Rica.',
            'tax_mapping': 'Ensure tax rates in XML match configured taxes in system.',
            'amount_mismatch': 'Review tax calculations. May indicate rounding or configuration issues.',
            'currency_error': 'Activate required currencies in Accounting > Configuration > Currencies.',
            'invoice_creation': 'Check invoice data and system configuration. Review error details.',
            'missing_data': 'XML is missing required fields. Contact original provider for complete data.',
            'encoding_error': 'File has encoding issues. Try re-exporting from original system.',
            'network_error': 'Temporary connection issue. Retry the import.',
            'permission_error': 'Check user permissions for creating invoices, partners, and products.',
            'other': 'Review error message and context for specific details.',
        }

        for error in self:
            error.suggested_action = suggestions.get(error.error_type, 'Review error details and contact support if needed.')

    @api.depends('error_type', 'error_category')
    def _compute_severity(self):
        """Compute error severity for prioritization."""
        critical_types = ['permission_error', 'invoice_creation']
        high_types = ['xml_parse', 'xml_structure', 'validation', 'encoding_error']
        medium_types = ['partner_creation', 'product_creation', 'tax_config', 'currency_error']

        for error in self:
            if error.error_type in critical_types:
                error.severity = 'critical'
            elif error.error_type in high_types:
                error.severity = 'high'
            elif error.error_type in medium_types:
                error.severity = 'medium'
            else:
                error.severity = 'low'

    @api.depends('file_name')
    def _compute_xml_file_name(self):
        """Compute downloadable XML file name."""
        for error in self:
            if error.file_name:
                error.xml_file_name = error.file_name
            else:
                error.xml_file_name = f'error_{error.id}.xml'

    @api.model
    def create_error(self, batch_id, file_name, error_type, error_message, clave=None,
                     consecutive=None, xml_content=None, error_context=None, stack_trace=None):
        """
        Helper method to create error records with enhanced information.

        Args:
            batch_id: Import batch record or ID
            file_name: Name of the failed XML file
            error_type: Type of error from selection
            error_message: Human-readable error message
            clave: Optional clave if parsed
            consecutive: Optional consecutive if parsed
            xml_content: Optional XML content (will be base64 encoded)
            error_context: Optional additional context
            stack_trace: Optional stack trace for debugging

        Returns:
            Created error record
        """
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
            # Ensure XML content is base64 encoded
            if isinstance(xml_content, bytes):
                vals['xml_content'] = base64.b64encode(xml_content)
            else:
                vals['xml_content'] = xml_content
        if error_context:
            vals['error_context'] = error_context
        if stack_trace:
            vals['stack_trace'] = stack_trace

        return self.create(vals)

    @api.model
    def categorize_exception(self, exception, file_name=None):
        """
        Categorize an exception and determine error type.

        Args:
            exception: Python exception object
            file_name: Optional file name for context

        Returns:
            tuple: (error_type, error_message, error_context)
        """
        error_message = str(exception)
        error_type = 'other'
        error_context = None

        # XML parsing errors
        if 'XMLSyntaxError' in exception.__class__.__name__:
            error_type = 'xml_parse'
            error_context = f'File: {file_name}\nInvalid XML syntax detected.'

        # Validation errors from parser
        elif isinstance(exception, ValidationError):
            if 'Clave' in error_message or 'clave' in error_message.lower():
                error_type = 'validation'
                error_context = 'Clave validation failed - may be missing or invalid format'
            elif 'Emisor' in error_message:
                error_type = 'missing_data'
                error_context = 'Required emisor (sender) data missing from XML'
            elif 'Consecutive' in error_message:
                error_type = 'validation'
                error_context = 'Consecutive number validation failed'
            else:
                error_type = 'validation'

        # Partner/Product errors
        elif 'partner' in error_message.lower() or 'customer' in error_message.lower():
            if 'create' in error_message.lower():
                error_type = 'partner_creation'
            else:
                error_type = 'partner_not_found'
            error_context = 'Customer record issue - check VAT number and data'

        elif 'product' in error_message.lower():
            if 'create' in error_message.lower():
                error_type = 'product_creation'
            else:
                error_type = 'product_not_found'
            error_context = 'Product issue - check Cabys codes'

        # Tax errors
        elif 'tax' in error_message.lower():
            error_type = 'tax_config'
            error_context = 'Tax configuration or mapping issue'

        # Currency errors
        elif 'currency' in error_message.lower():
            error_type = 'currency_error'
            error_context = 'Currency not found or not activated'

        # Amount validation
        elif 'amount' in error_message.lower() or 'total' in error_message.lower():
            error_type = 'amount_mismatch'
            error_context = 'Invoice totals do not match XML summary'

        # Encoding errors
        elif isinstance(exception, UnicodeDecodeError):
            error_type = 'encoding_error'
            error_context = f'File encoding issue with {file_name}'

        # Permission errors
        elif isinstance(exception, UserError) and 'permission' in error_message.lower():
            error_type = 'permission_error'
            error_context = 'User lacks required permissions'

        return (error_type, error_message, error_context)

    def action_mark_resolved(self):
        """Mark error as resolved."""
        self.ensure_one()
        self.write({
            'is_resolved': True,
            'resolution_notes': self.resolution_notes or _('Manually marked as resolved on %s') % fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
        })

        _logger.info(f'Error {self.id} for file {self.file_name} marked as resolved')

    def action_retry_import(self):
        """
        Retry importing this failed file.
        Creates a new import batch with just this file and attempts re-import.
        """
        self.ensure_one()

        if not self.can_retry:
            raise UserError(_('This error cannot be retried automatically. Maximum retries reached or error type is not retryable.'))

        if not self.xml_content:
            raise UserError(_('Cannot retry - XML content not available.'))

        try:
            # Create new single-file batch
            batch = self.env['l10n_cr.einvoice.import.batch'].create({
                'name': _('Retry Import - %s') % self.file_name,
                'company_id': self.batch_id.company_id.id,
                'original_provider': self.batch_id.original_provider,
                'file_name': f'retry_{self.file_name}',
                'total_files': 1,
                'state': 'processing',
                'start_time': fields.Datetime.now(),
            })

            # Get wizard settings from original batch
            wizard = self.env['l10n_cr.einvoice.import.wizard'].create({
                'state': 'processing',
                'batch_id': batch.id,
                'total_files': 1,
                'auto_create_partners': True,  # Enable for retry
                'auto_create_products': True,  # Enable for retry
                'skip_duplicates': False,      # Don't skip on retry
            })

            # Decode XML content
            xml_content = base64.b64decode(self.xml_content)

            # Process the XML file
            xml_file = {
                'filename': self.file_name,
                'content': xml_content,
            }

            parser = self.env['l10n_cr.einvoice.xml.parser']

            # Parse and create invoice
            invoice_data = parser.parse_xml_file(xml_content)
            invoice = wizard._create_invoice_from_data(invoice_data, batch, xml_file)

            # Update batch
            batch.write({
                'processed_files': 1,
                'successful_imports': 1,
                'state': 'done',
                'end_time': fields.Datetime.now(),
            })

            # Update this error
            self.write({
                'retry_count': self.retry_count + 1,
                'last_retry_date': fields.Datetime.now(),
                'is_resolved': True,
                'resolution_notes': _('Successfully retried on %s. Invoice created: %s') % (
                    fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
                    invoice.name if invoice else 'N/A'
                ),
            })

            _logger.info(f'Successfully retried error {self.id} - created invoice {invoice.name}')

            # Return action to view created invoice
            return {
                'type': 'ir.actions.act_window',
                'name': _('Retry Successful'),
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }

        except Exception as e:
            _logger.error(f'Retry failed for error {self.id}: {str(e)}', exc_info=True)

            # Update retry count
            self.write({
                'retry_count': self.retry_count + 1,
                'last_retry_date': fields.Datetime.now(),
                'resolution_notes': (self.resolution_notes or '') + _('\n\nRetry attempt failed on %s: %s') % (
                    fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
                    str(e)
                ),
            })

            # Mark batch as error
            if 'batch' in locals():
                batch.action_mark_error(str(e))

            raise UserError(_('Retry failed: %s\n\nPlease review the error and try manual import.') % str(e))

    def action_download_xml(self):
        """Download the failed XML file for debugging."""
        self.ensure_one()

        if not self.xml_content:
            raise UserError(_('No XML content available for this error.'))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/xml_content/{self.xml_file_name}?download=true',
            'target': 'self',
        }

    def action_bulk_retry(self):
        """Retry multiple errors at once."""
        if not self:
            return

        retryable = self.filtered(lambda e: e.can_retry and not e.is_resolved)

        if not retryable:
            raise UserError(_('No retryable errors selected.'))

        success_count = 0
        fail_count = 0

        for error in retryable:
            try:
                error.action_retry_import()
                success_count += 1
            except Exception as e:
                _logger.warning(f'Bulk retry failed for error {error.id}: {str(e)}')
                fail_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Retry Complete'),
                'message': _('Success: %d | Failed: %d') % (success_count, fail_count),
                'type': 'success' if success_count > 0 else 'warning',
                'sticky': False,
            }
        }

    @api.model
    def get_error_statistics(self, batch_id=None):
        """
        Get error statistics for reporting.

        Args:
            batch_id: Optional batch ID to filter by

        Returns:
            dict: Error statistics
        """
        domain = []
        if batch_id:
            domain = [('batch_id', '=', batch_id)]

        errors = self.search(domain)

        return {
            'total': len(errors),
            'resolved': len(errors.filtered('is_resolved')),
            'unresolved': len(errors.filtered(lambda e: not e.is_resolved)),
            'retryable': len(errors.filtered('can_retry')),
            'by_type': {
                error_type: len(errors.filtered(lambda e: e.error_type == error_type))
                for error_type in dict(self._fields['error_type'].selection).keys()
            },
            'by_category': {
                cat: len(errors.filtered(lambda e: e.error_category == cat))
                for cat in ['transient', 'config', 'data', 'permanent']
            },
            'by_severity': {
                sev: len(errors.filtered(lambda e: e.severity == sev))
                for sev in ['low', 'medium', 'high', 'critical']
            },
        }
