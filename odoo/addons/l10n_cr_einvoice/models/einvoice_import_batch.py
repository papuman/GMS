# -*- coding: utf-8 -*-
import logging
import base64
import io
import csv
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoiceImportBatch(models.Model):
    _name = 'l10n_cr.einvoice.import.batch'
    _description = 'E-Invoice Import Batch'
    _order = 'create_date desc'

    name = fields.Char(
        string='Batch Name',
        required=True,
        default=lambda self: _('Import %s') % fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], string='Status', default='draft', required=True)

    original_provider = fields.Char(
        string='Original Provider',
        help='Previous e-invoicing provider (GTI, FACTURATica, etc.)',
    )

    file_name = fields.Char(
        string='File Name',
        help='Original ZIP file name',
    )

    total_files = fields.Integer(
        string='Total Files',
        default=0,
    )

    processed_files = fields.Integer(
        string='Processed Files',
        default=0,
    )

    successful_imports = fields.Integer(
        string='Successful Imports',
        default=0,
    )

    failed_imports = fields.Integer(
        string='Failed Imports',
        default=0,
    )

    skipped_duplicates = fields.Integer(
        string='Skipped Duplicates',
        default=0,
    )

    progress_percentage = fields.Float(
        string='Progress %',
        compute='_compute_progress',
        store=True,
    )

    start_time = fields.Datetime(
        string='Start Time',
    )

    end_time = fields.Datetime(
        string='End Time',
    )

    duration = fields.Float(
        string='Duration (minutes)',
        compute='_compute_duration',
        store=True,
    )

    import_error_ids = fields.One2many(
        'l10n_cr.einvoice.import.error',
        'batch_id',
        string='Import Errors',
    )

    invoice_ids = fields.One2many(
        'account.move',
        'l10n_cr_import_batch_id',
        string='Imported Invoices',
    )

    notes = fields.Text(
        string='Notes',
    )

    @api.depends('total_files', 'processed_files')
    def _compute_progress(self):
        for batch in self:
            if batch.total_files > 0:
                batch.progress_percentage = (batch.processed_files / batch.total_files) * 100
            else:
                batch.progress_percentage = 0.0

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for batch in self:
            if batch.start_time and batch.end_time:
                delta = batch.end_time - batch.start_time
                batch.duration = delta.total_seconds() / 60  # Convert to minutes
            else:
                batch.duration = 0.0

    def action_start_processing(self):
        """Mark batch as processing and record start time."""
        self.write({
            'state': 'processing',
            'start_time': fields.Datetime.now(),
        })

    def action_mark_done(self):
        """Mark batch as done and record end time."""
        self.write({
            'state': 'done',
            'end_time': fields.Datetime.now(),
        })

    def action_mark_error(self, error_message=None):
        """Mark batch as error."""
        vals = {
            'state': 'error',
            'end_time': fields.Datetime.now(),
        }
        if error_message:
            vals['notes'] = error_message

        self.write(vals)

    def action_view_invoices(self):
        """Open view with imported invoices."""
        return {
            'name': _('Imported Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'create': False},
        }

    def action_view_errors(self):
        """Open view with import errors."""
        return {
            'name': _('Import Errors'),
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_cr.einvoice.import.error',
            'view_mode': 'tree,form',
            'domain': [('batch_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_export_error_report(self):
        """Export error report as CSV file."""
        self.ensure_one()

        if not self.import_error_ids:
            raise UserError(_('No errors to export for this batch.'))

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        # Write header
        writer.writerow([
            'File Name',
            'Error Type',
            'Error Category',
            'Severity',
            'Clave',
            'Consecutive',
            'Error Message',
            'Context',
            'Suggested Action',
            'Can Retry',
            'Retry Count',
            'Is Resolved',
            'Resolution Notes',
            'Date',
        ])

        # Write error rows
        for error in self.import_error_ids:
            writer.writerow([
                error.file_name or '',
                dict(error._fields['error_type'].selection).get(error.error_type, ''),
                dict(error._fields['error_category'].selection).get(error.error_category, ''),
                dict(error._fields['severity'].selection).get(error.severity, ''),
                error.clave or '',
                error.consecutive or '',
                error.error_message or '',
                error.error_context or '',
                error.suggested_action or '',
                'Yes' if error.can_retry else 'No',
                error.retry_count,
                'Yes' if error.is_resolved else 'No',
                error.resolution_notes or '',
                error.create_date.strftime('%Y-%m-%d %H:%M:%S') if error.create_date else '',
            ])

        # Get CSV content
        csv_content = output.getvalue()
        output.close()

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Error_Report_{self.name.replace(" ", "_")}.csv',
            'type': 'binary',
            'datas': base64.b64encode(csv_content.encode('utf-8')),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'text/csv',
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def get_batch_statistics(self):
        """
        Get comprehensive batch statistics.

        Returns:
            dict: Batch statistics including success rate, error breakdown, etc.
        """
        self.ensure_one()

        success_rate = 0.0
        if self.total_files > 0:
            success_rate = (self.successful_imports / self.total_files) * 100

        # Get error statistics
        error_stats = self.env['l10n_cr.einvoice.import.error'].get_error_statistics(
            batch_id=self.id
        )

        return {
            'batch_name': self.name,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_imports': self.successful_imports,
            'failed_imports': self.failed_imports,
            'skipped_duplicates': self.skipped_duplicates,
            'success_rate': success_rate,
            'duration_minutes': self.duration,
            'processing_speed': self.processed_files / self.duration if self.duration > 0 else 0,
            'error_statistics': error_stats,
        }

    @api.model
    def compare_batches(self, batch_ids):
        """
        Compare multiple import batches.

        Args:
            batch_ids: List of batch IDs to compare

        Returns:
            dict: Comparison data
        """
        batches = self.browse(batch_ids)

        if not batches:
            raise UserError(_('No batches selected for comparison.'))

        comparison = {
            'batches': [],
            'totals': {
                'total_files': 0,
                'successful_imports': 0,
                'failed_imports': 0,
                'skipped_duplicates': 0,
            },
            'averages': {
                'success_rate': 0.0,
                'duration_minutes': 0.0,
                'processing_speed': 0.0,
            },
        }

        for batch in batches:
            stats = batch.get_batch_statistics()
            comparison['batches'].append(stats)

            # Add to totals
            comparison['totals']['total_files'] += batch.total_files
            comparison['totals']['successful_imports'] += batch.successful_imports
            comparison['totals']['failed_imports'] += batch.failed_imports
            comparison['totals']['skipped_duplicates'] += batch.skipped_duplicates

        # Calculate averages
        num_batches = len(batches)
        if num_batches > 0:
            comparison['averages']['success_rate'] = sum(
                b.get('success_rate', 0) for b in comparison['batches']
            ) / num_batches

            comparison['averages']['duration_minutes'] = sum(
                b.get('duration_minutes', 0) for b in comparison['batches']
            ) / num_batches

            comparison['averages']['processing_speed'] = sum(
                b.get('processing_speed', 0) for b in comparison['batches']
            ) / num_batches

        return comparison
