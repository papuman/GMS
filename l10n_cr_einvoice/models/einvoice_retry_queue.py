# -*- coding: utf-8 -*-
"""
Costa Rica E-Invoice Retry Queue

Intelligent retry queue system for failed e-invoice operations with:
- Automatic error classification (auth, network, validation, rate_limit, server, transient, unknown)
- Exponential backoff (5min, 15min, 1hr, 4hr, 12hr)
- Category-specific max retries and delay multipliers
- Automatic retry via cron job
- Manual retry capability
- 30-day retention policy for completed/failed entries
"""

import logging
from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoiceRetryQueue(models.Model):
    """
    Retry queue for failed e-invoice operations.

    Automatically retries failed operations with exponential backoff based on
    error category classification.
    """
    _name = 'l10n_cr.einvoice.retry.queue'
    _description = 'E-Invoice Retry Queue'
    _order = 'priority desc, next_attempt asc, id asc'

    # Core fields
    document_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='E-Invoice Document',
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='document_id.company_id',
        store=True,
        index=True,
    )
    operation = fields.Selection([
        ('sign', 'Sign XML'),
        ('submit', 'Submit to Hacienda'),
        ('query', 'Query Status'),
    ], string='Operation', required=True)

    # Error tracking
    error_message = fields.Text('Error Message')
    error_category = fields.Selection([
        ('auth', 'Authentication'),
        ('network', 'Network'),
        ('validation', 'Validation'),
        ('rate_limit', 'Rate Limit'),
        ('server', 'Server Error'),
        ('transient', 'Transient'),
        ('unknown', 'Unknown'),
    ], string='Error Category', required=True)
    last_error = fields.Text('Last Error')

    # Retry logic
    state = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='pending', required=True)
    retry_count = fields.Integer('Retry Count', default=0)
    max_retries = fields.Integer('Max Retries', default=5)
    next_attempt = fields.Datetime('Next Attempt', index=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1')

    # Base delay configuration per category (in minutes)
    _base_delays = {
        0: 5,      # 5 minutes
        1: 15,     # 15 minutes
        2: 60,     # 1 hour
        3: 240,    # 4 hours
        4: 720,    # 12 hours
    }

    # Category-specific multipliers
    _category_multipliers = {
        'transient': 1.0,
        'network': 1.0,
        'server': 1.0,
        'rate_limit': 2.0,
        'auth': 3.0,
        'validation': 6.0,
        'unknown': 2.0,
    }

    # Max retries per category
    _category_max_retries = {
        'transient': 5,
        'network': 5,
        'server': 5,
        'rate_limit': 4,
        'auth': 3,
        'validation': 2,
        'unknown': 3,
    }

    @api.model
    def add_to_queue(self, document, operation, error_message, error_category=None, priority='2'):
        """
        Add a document to the retry queue.

        Args:
            document: l10n_cr.einvoice.document record
            operation: str - 'sign', 'submit', or 'query'
            error_message: str - Error description
            error_category: str - Error category (if None, will classify automatically)
            priority: str - '0' to '3'

        Returns:
            l10n_cr.einvoice.retry.queue record
        """
        if not error_category:
            error_category = self.classify_error(error_message)

        max_retries = self._get_max_retries(error_category)
        delay_minutes = self._get_retry_delay(0, error_category)
        next_attempt = datetime.now() + timedelta(minutes=delay_minutes)

        return self.create({
            'document_id': document.id,
            'operation': operation,
            'error_message': error_message,
            'error_category': error_category,
            'last_error': error_message,
            'priority': priority,
            'retry_count': 0,
            'max_retries': max_retries,
            'next_attempt': next_attempt,
            'state': 'pending',
        })

    @api.model
    def classify_error(self, error_message):
        """
        Classify error message into a category.

        Args:
            error_message: str - Error description

        Returns:
            str - Error category
        """
        error_lower = error_message.lower()

        # Transient errors (check first - more specific than server errors)
        if any(keyword in error_lower for keyword in ['temporary', 'try again', 'transient']):
            return 'transient'

        # Authentication errors
        if any(keyword in error_lower for keyword in ['401', '403', 'unauthorized', 'forbidden', 'authentication', 'credentials', 'token expired']):
            return 'auth'

        # Network errors
        if any(keyword in error_lower for keyword in ['timeout', 'connection', 'network', 'dns', 'socket']):
            return 'network'

        # Validation errors
        if any(keyword in error_lower for keyword in ['400', 'validation', 'invalid', 'schema', 'bad request']):
            return 'validation'

        # Rate limit errors
        if any(keyword in error_lower for keyword in ['429', 'rate limit', 'too many requests']):
            return 'rate_limit'

        # Server errors
        if any(keyword in error_lower for keyword in ['500', '502', '503', 'server error', 'bad gateway', 'service unavailable']):
            return 'server'

        # Unknown
        return 'unknown'

    @api.model
    def _get_retry_delay(self, retry_count, error_category):
        """
        Calculate retry delay in minutes with exponential backoff.

        Args:
            retry_count: int - Current retry attempt number
            error_category: str - Error category

        Returns:
            int - Delay in minutes
        """
        # Get base delay (capped at max retry count)
        base_delay = self._base_delays.get(min(retry_count, 4), 720)

        # Apply category multiplier
        multiplier = self._category_multipliers.get(error_category, 1.0)

        return int(base_delay * multiplier)

    @api.model
    def _get_max_retries(self, error_category):
        """
        Get maximum retry count for error category.

        Args:
            error_category: str - Error category

        Returns:
            int - Maximum retry count
        """
        return self._category_max_retries.get(error_category, 3)

    def _process_retry(self):
        """
        Process a single retry attempt.

        This method attempts to execute the queued operation and updates
        the queue entry state accordingly.
        """
        self.ensure_one()

        try:
            # Execute the operation based on type
            if self.operation == 'sign':
                self.document_id.action_sign_xml()
            elif self.operation == 'submit':
                self.document_id.action_submit_to_hacienda()
            elif self.operation == 'query':
                self.document_id.action_query_hacienda_status()

            # Success - mark as completed
            self.write({
                'state': 'completed',
                'last_error': False,
            })
            _logger.info(f"Retry queue entry {self.id} completed successfully")

        except Exception as e:
            error_msg = str(e)
            _logger.warning(f"Retry queue entry {self.id} failed: {error_msg}")

            # Increment retry count
            new_retry_count = self.retry_count + 1

            # Check if max retries reached
            if new_retry_count >= self.max_retries:
                self.write({
                    'state': 'failed',
                    'retry_count': new_retry_count,
                    'last_error': error_msg,
                })
                _logger.error(f"Retry queue entry {self.id} failed permanently after {new_retry_count} attempts")
            else:
                # Schedule next retry with exponential backoff
                delay_minutes = self._get_retry_delay(new_retry_count, self.error_category)
                next_attempt = datetime.now() + timedelta(minutes=delay_minutes)

                self.write({
                    'state': 'pending',
                    'retry_count': new_retry_count,
                    'next_attempt': next_attempt,
                    'last_error': error_msg,
                })
                _logger.info(f"Retry queue entry {self.id} scheduled for retry {new_retry_count} at {next_attempt}")

    @api.model
    def _cron_process_retry_queue(self):
        """
        Cron job to process pending retry queue entries.

        Processes all pending entries where next_attempt is in the past,
        ordered by priority and next_attempt time.
        """
        now = datetime.now()

        # Find all pending entries due for retry
        entries = self.search([
            ('state', '=', 'pending'),
            ('next_attempt', '<=', now),
        ], order='priority desc, next_attempt asc')

        _logger.info(f"Processing {len(entries)} retry queue entries")

        for entry in entries:
            try:
                entry._process_retry()
            except Exception as e:
                _logger.error(f"Error processing retry queue entry {entry.id}: {e}")

    def action_retry_now(self):
        """
        Manual retry action - process immediately regardless of schedule.
        """
        self.ensure_one()
        if self.state not in ('pending', 'failed'):
            raise UserError("Can only retry pending or failed entries")

        self._process_retry()

    def action_cancel_retry(self):
        """
        Cancel a pending retry.
        """
        self.ensure_one()
        if self.state in ('completed', 'cancelled'):
            raise UserError("Cannot cancel completed or already cancelled entries")

        self.write({'state': 'cancelled'})

    @api.model
    def _cleanup_old_entries(self, days=30):
        """
        Clean up old completed/failed entries.

        Args:
            days: int - Delete entries older than this many days

        Returns:
            int - Number of deleted entries
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        old_entries = self.search([
            ('create_date', '<', cutoff_date),
            ('state', 'in', ['completed', 'failed', 'cancelled']),
        ])

        count = len(old_entries)
        old_entries.unlink()

        _logger.info(f"Cleaned up {count} old retry queue entries")
        return count

    @api.model
    def get_queue_statistics(self, company_id=None):
        """
        Get statistics about retry queue.

        Args:
            company_id: int - Filter by company (optional)

        Returns:
            dict - Statistics
        """
        domain = []
        if company_id:
            domain.append(('company_id', '=', company_id))

        all_entries = self.search(domain)

        stats = {
            'total': len(all_entries),
            'pending': len(all_entries.filtered(lambda r: r.state == 'pending')),
            'processing': len(all_entries.filtered(lambda r: r.state == 'processing')),
            'completed': len(all_entries.filtered(lambda r: r.state == 'completed')),
            'failed': len(all_entries.filtered(lambda r: r.state == 'failed')),
            'cancelled': len(all_entries.filtered(lambda r: r.state == 'cancelled')),
            'by_operation': {},
            'by_category': {},
        }

        # Group by operation
        for op in ['sign', 'submit', 'query']:
            stats['by_operation'][op] = len(all_entries.filtered(lambda r: r.operation == op))

        # Group by category
        for cat in ['auth', 'network', 'validation', 'rate_limit', 'server', 'transient', 'unknown']:
            stats['by_category'][cat] = len(all_entries.filtered(lambda r: r.error_category == cat))

        return stats
