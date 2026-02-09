# -*- coding: utf-8 -*-
"""
Costa Rica POS Offline Queue

Manages offline e-invoice queue for POS terminals.
When the POS cannot connect to Hacienda (offline mode), electronic invoices
are queued here for automatic synchronization when the connection is restored.

Features:
- Automatic retry with exponential backoff
- Priority-based processing
- Manual retry capability
- Cleanup of old synced entries
"""

import logging
from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOfflineQueue(models.Model):
    """
    POS Offline Queue for e-invoices.

    When the POS terminal is offline, e-invoices are stored in this queue
    and synchronized automatically when connectivity is restored.
    """
    _name = 'l10n_cr.pos.offline.queue'
    _description = 'POS Offline E-Invoice Queue'
    _order = 'priority desc, create_date asc'

    # Display name
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )

    # Relations
    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    session_id = fields.Many2one(
        'pos.session',
        string='POS Session',
        related='pos_order_id.session_id',
        store=True,
    )
    config_id = fields.Many2one(
        'pos.config',
        string='POS Terminal',
        related='pos_order_id.session_id.config_id',
        store=True,
    )
    einvoice_document_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='E-Invoice Document',
        ondelete='set null',
    )

    # State management
    state = fields.Selection([
        ('pending', 'Pending'),
        ('syncing', 'Syncing'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ], string='Status', default='pending', required=True, index=True)

    # Priority
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ], string='Priority', default='normal', required=True)

    # Retry management
    retry_count = fields.Integer('Retry Count', default=0)
    max_retries = fields.Integer('Max Retries', default=5)
    last_retry = fields.Datetime('Last Retry')
    next_retry = fields.Datetime(
        string='Next Retry',
        compute='_compute_next_retry',
        store=True,
    )
    last_error = fields.Text('Last Error')

    # Cached data
    xml_data = fields.Binary('Cached XML Data', attachment=True)

    @api.depends('pos_order_id', 'pos_order_id.name')
    def _compute_name(self):
        """Compute display name from POS order."""
        for record in self:
            if record.pos_order_id:
                record.name = f"Queue: {record.pos_order_id.name}"
            else:
                record.name = f"Queue: #{record.id or 'New'}"

    @api.depends('retry_count', 'last_retry')
    def _compute_next_retry(self):
        """
        Compute next retry time with exponential backoff.

        Backoff formula: 2^retry_count minutes
        - Retry 0: 1 minute (2^0)
        - Retry 1: 2 minutes (2^1)
        - Retry 2: 4 minutes (2^2)
        - Retry 3: 8 minutes (2^3)
        - Retry 4: 16 minutes (2^4)
        Max: 60 minutes
        """
        for record in self:
            if record.last_retry and record.state == 'pending':
                # Exponential backoff: 2^retry_count minutes, max 60
                delay_minutes = min(2 ** record.retry_count, 60)
                record.next_retry = record.last_retry + timedelta(minutes=delay_minutes)
            elif record.state == 'pending' and not record.last_retry:
                # First attempt - immediate
                record.next_retry = fields.Datetime.now()
            else:
                record.next_retry = False

    def action_retry_sync(self):
        """
        Manually trigger sync retry.

        Raises:
            UserError: If offline or max retries exceeded
        """
        self.ensure_one()

        # Check if failed with max retries
        if self.state == 'failed' and self.retry_count >= self.max_retries:
            raise UserError(
                f"Maximum retry attempts ({self.max_retries}) exceeded. "
                "Use 'Reset' to clear retry count first."
            )

        # Check if already synced
        if self.state == 'synced':
            raise UserError("This entry has already been synced.")

        # Check if currently syncing
        if self.state == 'syncing':
            raise UserError("This entry is currently being synced.")

        # Check online status via POS order
        if self.pos_order_id and hasattr(self.pos_order_id, '_l10n_cr_is_online'):
            if not self.pos_order_id._l10n_cr_is_online():
                raise UserError(
                    "Cannot sync while offline. "
                    "Please check your internet connection."
                )

        # Perform sync
        self._perform_sync()

    def _perform_sync(self):
        """
        Internal method to perform the actual sync operation.
        """
        self.ensure_one()
        self.write({'state': 'syncing'})

        try:
            # If there's an einvoice document, submit it
            if self.einvoice_document_id:
                if self.einvoice_document_id.state == 'draft':
                    self.einvoice_document_id.action_generate_xml()
                if self.einvoice_document_id.state == 'generated':
                    self.einvoice_document_id.action_sign_xml()
                if self.einvoice_document_id.state == 'signed':
                    self.einvoice_document_id.action_submit_to_hacienda()

            # Mark as synced
            self.write({
                'state': 'synced',
                'last_retry': fields.Datetime.now(),
                'last_error': False,
            })

            # Clear offline queue flag on POS order
            if self.pos_order_id:
                self.pos_order_id.write({'l10n_cr_offline_queue': False})

            _logger.info(f"POS offline queue entry {self.id} synced successfully")

        except Exception as e:
            error_msg = str(e)
            new_retry_count = self.retry_count + 1

            if new_retry_count >= self.max_retries:
                self.write({
                    'state': 'failed',
                    'retry_count': new_retry_count,
                    'last_retry': fields.Datetime.now(),
                    'last_error': error_msg,
                })
                _logger.error(
                    f"POS offline queue entry {self.id} failed permanently: {error_msg}"
                )
            else:
                self.write({
                    'state': 'pending',
                    'retry_count': new_retry_count,
                    'last_retry': fields.Datetime.now(),
                    'last_error': error_msg,
                })
                _logger.warning(
                    f"POS offline queue entry {self.id} failed (attempt {new_retry_count}): {error_msg}"
                )

    def action_reset(self):
        """
        Reset a failed entry to pending state.
        Clears retry count and error message.
        """
        self.ensure_one()
        if self.state not in ('failed', 'pending'):
            raise UserError("Can only reset failed or pending entries.")

        self.write({
            'state': 'pending',
            'retry_count': 0,
            'last_error': False,
            'last_retry': False,
        })
        _logger.info(f"POS offline queue entry {self.id} reset to pending")

    def action_mark_synced(self):
        """
        Manually mark an entry as synced.
        Use with caution - this skips actual submission to Hacienda.
        """
        self.ensure_one()
        if self.state == 'synced':
            raise UserError("Entry is already synced.")

        self.write({
            'state': 'synced',
            'last_error': False,
        })

        # Clear offline queue flag on POS order
        if self.pos_order_id:
            self.pos_order_id.write({'l10n_cr_offline_queue': False})

        _logger.info(f"POS offline queue entry {self.id} manually marked as synced")

    def action_delete_queue_entry(self):
        """
        Delete a queue entry.
        Cannot delete entries that are currently syncing.
        """
        self.ensure_one()
        if self.state == 'syncing':
            raise UserError("Cannot delete an entry that is currently syncing.")

        _logger.info(f"POS offline queue entry {self.id} deleted")
        self.unlink()

    @api.model
    def get_queue_stats(self, config_id=None):
        """
        Get statistics about the offline queue.

        Args:
            config_id: Optional POS config ID to filter by

        Returns:
            dict: Statistics with pending, failed, and total counts
        """
        domain = [('state', '!=', 'synced')]
        if config_id:
            domain.append(('config_id', '=', config_id))

        all_entries = self.search(domain)

        return {
            'pending': len(all_entries.filtered(lambda r: r.state == 'pending')),
            'syncing': len(all_entries.filtered(lambda r: r.state == 'syncing')),
            'failed': len(all_entries.filtered(lambda r: r.state == 'failed')),
            'total': len(all_entries),
        }

    @api.model
    def cron_sync_offline_queue(self, limit=50):
        """
        Cron job to sync pending offline queue entries.

        Args:
            limit: Maximum entries to process per run

        Returns:
            dict: Results with success, failed, and skipped counts
        """
        now = fields.Datetime.now()

        # Find entries ready for retry
        entries = self.search([
            ('state', '=', 'pending'),
            '|',
            ('next_retry', '<=', now),
            ('next_retry', '=', False),
        ], limit=limit, order='priority desc, create_date asc')

        results = {'success': 0, 'failed': 0, 'skipped': 0}

        for entry in entries:
            try:
                # Check online status
                if entry.pos_order_id and hasattr(entry.pos_order_id, '_l10n_cr_is_online'):
                    if not entry.pos_order_id._l10n_cr_is_online():
                        results['skipped'] += 1
                        continue

                entry._perform_sync()

                if entry.state == 'synced':
                    results['success'] += 1
                else:
                    results['failed'] += 1

            except Exception as e:
                _logger.error(f"Error processing queue entry {entry.id}: {e}")
                results['failed'] += 1

        _logger.info(
            f"POS offline queue sync: {results['success']} success, "
            f"{results['failed']} failed, {results['skipped']} skipped"
        )

        return results

    @api.model
    def cleanup_old_entries(self, days=30):
        """
        Clean up old synced queue entries.

        Args:
            days: Delete entries older than this many days

        Returns:
            int: Number of deleted entries
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        old_entries = self.search([
            ('state', '=', 'synced'),
            ('create_date', '<', cutoff_date),
        ])

        count = len(old_entries)
        if count > 0:
            old_entries.unlink()
            _logger.info(f"Cleaned up {count} old POS offline queue entries")

        return count
