# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOfflineQueue(models.Model):
    _name = 'l10n_cr.pos.offline.queue'
    _description = 'POS Offline Invoice Queue'
    _order = 'create_date asc'

    name = fields.Char(
        string='Queue Entry',
        compute='_compute_name',
        store=True,
    )

    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        required=True,
        ondelete='cascade',
        index=True,
    )

    einvoice_document_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='E-Invoice Document',
        required=True,
        ondelete='cascade',
    )

    xml_data = fields.Binary(
        string='Cached XML',
        attachment=True,
        help='Cached signed XML for offline submission',
    )

    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        readonly=True,
        help='Number of sync attempts',
    )

    last_retry = fields.Datetime(
        string='Last Retry',
        readonly=True,
        help='Timestamp of last sync attempt',
    )

    last_error = fields.Text(
        string='Last Error',
        readonly=True,
        help='Error message from last failed attempt',
    )

    state = fields.Selection([
        ('pending', 'Pending Sync'),
        ('syncing', 'Syncing'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ], string='State', default='pending', required=True, index=True)

    next_retry = fields.Datetime(
        string='Next Retry',
        compute='_compute_next_retry',
        store=True,
        help='Calculated next retry time with exponential backoff',
    )

    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ], string='Priority', default='normal', help='Sync priority')

    session_id = fields.Many2one(
        'pos.session',
        string='POS Session',
        related='pos_order_id.session_id',
        store=True,
    )

    config_id = fields.Many2one(
        'pos.config',
        string='POS Terminal',
        related='session_id.config_id',
        store=True,
    )

    @api.depends('pos_order_id', 'einvoice_document_id')
    def _compute_name(self):
        """Generate name for queue entry."""
        for record in self:
            record.name = f"Queue: {record.pos_order_id.name or 'Unknown'}"

    @api.depends('retry_count', 'last_retry')
    def _compute_next_retry(self):
        """Calculate next retry time with exponential backoff."""
        for record in self:
            if record.state in ('synced', 'failed'):
                record.next_retry = False
                continue

            if not record.last_retry:
                record.next_retry = fields.Datetime.now()
                continue

            # Exponential backoff: 1, 2, 4, 8, 16 minutes
            backoff_minutes = 2 ** min(record.retry_count, 4)
            record.next_retry = record.last_retry + timedelta(minutes=backoff_minutes)

    def action_retry_sync(self):
        """Manually retry sync for this entry."""
        for record in self:
            if record.state == 'synced':
                raise UserError(_('This entry has already been synced'))

            if record.state == 'failed' and record.retry_count >= 5:
                raise UserError(_('This entry has exceeded maximum retries. Please check the error and reset.'))

            try:
                record.state = 'syncing'
                record.last_retry = fields.Datetime.now()

                # Check connectivity
                if not record.pos_order_id._l10n_cr_is_online():
                    raise UserError(_('Hacienda API is not accessible'))

                # Submit invoice
                record.einvoice_document_id.action_submit_to_hacienda()

                # Mark as synced
                record.state = 'synced'
                record.pos_order_id.l10n_cr_offline_queue = False
                record.pos_order_id.l10n_cr_hacienda_status = 'pending'

                _logger.info('Queue entry %s synced successfully', record.name)

            except Exception as e:
                record.retry_count += 1
                record.last_error = str(e)

                # Mark as failed after 5 retries
                if record.retry_count >= 5:
                    record.state = 'failed'
                else:
                    record.state = 'pending'

                _logger.error('Error syncing queue entry %s: %s', record.name, str(e))
                raise UserError(_('Sync failed: %s') % str(e))

    def action_reset(self):
        """Reset failed queue entry for retry."""
        for record in self:
            if record.state != 'failed':
                raise UserError(_('Only failed entries can be reset'))

            record.write({
                'state': 'pending',
                'retry_count': 0,
                'last_error': False,
                'last_retry': False,
            })

    def action_mark_synced(self):
        """Manually mark as synced (for conflict resolution)."""
        for record in self:
            record.state = 'synced'
            record.pos_order_id.l10n_cr_offline_queue = False

    def action_delete_queue_entry(self):
        """Delete queue entry."""
        for record in self:
            if record.state == 'syncing':
                raise UserError(_('Cannot delete entry that is currently syncing'))

            record.pos_order_id.l10n_cr_offline_queue = False
            record.unlink()

    @api.model
    def cron_sync_offline_queue(self):
        """Cron job to automatically sync pending entries."""
        # Find entries ready for retry
        now = fields.Datetime.now()
        entries = self.search([
            ('state', '=', 'pending'),
            '|',
            ('next_retry', '<=', now),
            ('next_retry', '=', False),
        ], limit=50, order='priority desc, create_date asc')

        if not entries:
            _logger.info('No pending queue entries to sync')
            return

        _logger.info('Syncing %d queued invoices', len(entries))

        success_count = 0
        error_count = 0

        for entry in entries:
            try:
                entry.action_retry_sync()
                success_count += 1

            except Exception as e:
                error_count += 1
                _logger.error('Error in cron sync for entry %s: %s', entry.name, str(e))

        _logger.info('Cron sync completed: %d success, %d errors', success_count, error_count)

        return {
            'success': success_count,
            'errors': error_count,
        }

    @api.model
    def get_queue_stats(self):
        """Get queue statistics for UI display."""
        stats = {
            'pending': self.search_count([('state', '=', 'pending')]),
            'syncing': self.search_count([('state', '=', 'syncing')]),
            'failed': self.search_count([('state', '=', 'failed')]),
            'total': self.search_count([('state', '!=', 'synced')]),
        }
        return stats

    @api.model
    def cleanup_old_entries(self):
        """Clean up old synced entries (older than 30 days)."""
        cutoff_date = fields.Datetime.now() - timedelta(days=30)
        old_entries = self.search([
            ('state', '=', 'synced'),
            ('create_date', '<', cutoff_date),
        ])

        count = len(old_entries)
        old_entries.unlink()

        _logger.info('Cleaned up %d old queue entries', count)
        return count
