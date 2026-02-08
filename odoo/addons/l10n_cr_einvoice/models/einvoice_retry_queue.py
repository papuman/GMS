# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoiceRetryQueue(models.Model):
    """
    Retry queue for failed e-invoice operations.

    Manages automatic retry of failed submissions and status checks
    with intelligent exponential backoff and error classification.
    """
    _name = 'l10n_cr.einvoice.retry.queue'
    _description = 'E-Invoice Retry Queue'
    _order = 'next_attempt asc, priority desc, id asc'
    _rec_name = 'display_name'

    # Document Reference
    document_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='E-Invoice Document',
        required=True,
        ondelete='cascade',
        index=True,
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )

    # Operation Details
    operation = fields.Selection([
        ('sign', 'Sign XML'),
        ('submit', 'Submit to Hacienda'),
        ('check_status', 'Check Status'),
    ], string='Operation', required=True, index=True)

    # Retry Management
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        help='Number of retry attempts made',
    )

    max_retries = fields.Integer(
        string='Max Retries',
        default=5,
        help='Maximum number of retry attempts before giving up',
    )

    last_attempt = fields.Datetime(
        string='Last Attempt',
        help='Date/time of last retry attempt',
    )

    next_attempt = fields.Datetime(
        string='Next Attempt',
        required=True,
        index=True,
        help='Scheduled date/time for next retry',
    )

    # Error Classification
    error_category = fields.Selection([
        ('transient', 'Transient Error'),
        ('rate_limit', 'Rate Limit'),
        ('auth', 'Authentication Error'),
        ('validation', 'Validation Error'),
        ('server', 'Server Error'),
        ('network', 'Network Error'),
        ('unknown', 'Unknown Error'),
    ], string='Error Category', required=True, index=True)

    last_error = fields.Text(
        string='Last Error Message',
        help='Error message from last failed attempt',
    )

    # State Management
    state = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='pending', required=True, index=True)

    # Priority
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1', index=True)

    # Metadata
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='document_id.company_id',
        store=True,
        index=True,
    )

    create_date = fields.Datetime(
        string='Created',
        readonly=True,
    )

    # Computed Fields
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
    )

    retry_progress = fields.Float(
        string='Progress (%)',
        compute='_compute_retry_progress',
    )

    @api.depends('document_id', 'operation', 'retry_count')
    def _compute_display_name(self):
        """Compute display name for UI."""
        for record in self:
            op_label = dict(self._fields['operation'].selection).get(record.operation, 'Operation')
            doc_name = record.document_id.name if record.document_id else 'N/A'
            record.display_name = f"{doc_name} - {op_label} (Attempt {record.retry_count}/{record.max_retries})"

    @api.depends('next_attempt')
    def _compute_is_overdue(self):
        """Check if retry is overdue."""
        now = fields.Datetime.now()
        for record in self:
            record.is_overdue = record.next_attempt < now if record.next_attempt else False

    @api.depends('retry_count', 'max_retries')
    def _compute_retry_progress(self):
        """Calculate retry progress percentage."""
        for record in self:
            if record.max_retries > 0:
                record.retry_progress = (record.retry_count / record.max_retries) * 100
            else:
                record.retry_progress = 0.0

    @api.model
    def add_to_queue(self, document, operation, error_message='', error_category='unknown', priority='1'):
        """
        Add a document to the retry queue.

        Args:
            document (recordset): E-invoice document
            operation (str): Operation to retry ('sign', 'submit', 'check_status')
            error_message (str): Error message from failed attempt
            error_category (str): Classified error category
            priority (str): Queue priority

        Returns:
            recordset: Created retry queue record
        """
        # Check if already in queue
        existing = self.search([
            ('document_id', '=', document.id),
            ('operation', '=', operation),
            ('state', 'in', ['pending', 'processing']),
        ], limit=1)

        if existing:
            # Update existing entry
            existing.write({
                'last_error': error_message,
                'error_category': error_category,
                'priority': priority,
            })
            _logger.info(f'Updated retry queue entry for {document.name}: {operation}')
            return existing

        # Determine initial retry delay
        delay_minutes = self._get_retry_delay(0, error_category)
        next_attempt = datetime.now() + timedelta(minutes=delay_minutes)

        # Determine max retries based on error category
        max_retries = self._get_max_retries(error_category)

        # Create new queue entry
        values = {
            'document_id': document.id,
            'operation': operation,
            'retry_count': 0,
            'max_retries': max_retries,
            'next_attempt': next_attempt,
            'error_category': error_category,
            'last_error': error_message,
            'state': 'pending',
            'priority': priority,
        }

        queue_entry = self.create(values)

        _logger.info(
            f'Added {document.name} to retry queue: {operation} '
            f'(category: {error_category}, next attempt: {next_attempt})'
        )

        return queue_entry

    @api.model
    def _get_retry_delay(self, retry_count, error_category):
        """
        Calculate retry delay in minutes based on attempt number and error category.

        Args:
            retry_count (int): Current retry count
            error_category (str): Error category

        Returns:
            int: Delay in minutes
        """
        # Base delays (in minutes) for each retry attempt
        base_delays = [5, 15, 60, 240, 720]  # 5min, 15min, 1hr, 4hr, 12hr

        # Multipliers for different error categories
        category_multipliers = {
            'transient': 1.0,
            'rate_limit': 2.0,  # Longer delay for rate limits
            'network': 1.5,
            'server': 1.5,
            'auth': 3.0,  # Give more time for auth fixes
            'validation': 6.0,  # Validation needs manual fix
            'unknown': 2.0,
        }

        # Get base delay
        delay_index = min(retry_count, len(base_delays) - 1)
        base_delay = base_delays[delay_index]

        # Apply category multiplier
        multiplier = category_multipliers.get(error_category, 1.0)
        final_delay = int(base_delay * multiplier)

        return final_delay

    @api.model
    def _get_max_retries(self, error_category):
        """
        Determine max retries based on error category.

        Args:
            error_category (str): Error category

        Returns:
            int: Maximum retry attempts
        """
        max_retries_map = {
            'transient': 5,
            'rate_limit': 4,
            'network': 5,
            'server': 5,
            'auth': 3,  # Fewer retries, likely needs manual fix
            'validation': 2,  # Needs manual fix
            'unknown': 3,
        }

        return max_retries_map.get(error_category, 3)

    @api.model
    def classify_error(self, error_message):
        """
        Classify error based on error message content.

        Args:
            error_message (str): Error message text

        Returns:
            str: Error category
        """
        error_lower = error_message.lower()

        # Rate limiting
        if 'rate limit' in error_lower or 'too many requests' in error_lower or '429' in error_lower:
            return 'rate_limit'

        # Authentication
        if 'auth' in error_lower or 'unauthorized' in error_lower or '401' in error_lower or '403' in error_lower:
            return 'auth'

        # Validation
        if 'validation' in error_lower or 'invalid' in error_lower or '400' in error_lower:
            return 'validation'

        # Server errors
        if 'server error' in error_lower or '500' in error_lower or '502' in error_lower or '503' in error_lower:
            return 'server'

        # Network errors
        if 'timeout' in error_lower or 'connection' in error_lower or 'network' in error_lower:
            return 'network'

        # Transient errors
        if 'temporary' in error_lower or 'try again' in error_lower:
            return 'transient'

        return 'unknown'

    @api.model
    def _cron_process_retry_queue(self):
        """
        Scheduled action to process retry queue.

        Runs every 5 minutes to check for documents due for retry.
        """
        now = datetime.now()

        # Find items due for retry
        queue_items = self.search([
            ('state', '=', 'pending'),
            ('next_attempt', '<=', now),
            ('retry_count', '<', self._fields['max_retries'].default),
        ], limit=100, order='priority desc, next_attempt asc')

        _logger.info(f'Processing retry queue: {len(queue_items)} items due for retry')

        success_count = 0
        failure_count = 0
        requeued_count = 0

        for item in queue_items:
            try:
                item._process_retry()
                if item.state == 'completed':
                    success_count += 1
                elif item.state == 'pending':
                    requeued_count += 1
                elif item.state == 'failed':
                    failure_count += 1

                # Commit after each item to prevent rollback affecting others
                self.env.cr.commit()

            except Exception as e:
                _logger.error(f'Error processing retry queue item {item.id}: {e}')
                failure_count += 1
                continue

        _logger.info(
            f'Retry queue processed: {success_count} succeeded, '
            f'{requeued_count} requeued, {failure_count} failed'
        )

        # Cleanup old completed/failed entries (older than 30 days)
        self._cleanup_old_entries(days=30)

    def _process_retry(self):
        """
        Process a single retry attempt.

        Executes the failed operation and updates retry queue state.
        """
        self.ensure_one()

        # Mark as processing
        self.write({'state': 'processing', 'last_attempt': datetime.now()})

        try:
            # Execute operation based on type
            if self.operation == 'sign':
                self.document_id.action_sign_xml()
            elif self.operation == 'submit':
                self.document_id.action_submit_to_hacienda()
            elif self.operation == 'check_status':
                self.document_id.action_check_status()
            else:
                raise UserError(_('Unknown operation: %s') % self.operation)

            # Success - mark as completed
            self.write({
                'state': 'completed',
                'last_error': False,
            })

            _logger.info(f'Retry successful for {self.document_id.name}: {self.operation}')

        except Exception as e:
            error_message = str(e)

            # Increment retry count
            new_retry_count = self.retry_count + 1

            # Check if max retries reached
            if new_retry_count >= self.max_retries:
                # Max retries exhausted - mark as failed
                self.write({
                    'state': 'failed',
                    'retry_count': new_retry_count,
                    'last_error': error_message,
                })

                _logger.error(
                    f'Max retries exceeded for {self.document_id.name}: {self.operation}. '
                    f'Last error: {error_message}'
                )

                # Notify admin
                self._notify_retry_failure()

            else:
                # Schedule next retry
                delay_minutes = self._get_retry_delay(new_retry_count, self.error_category)
                next_attempt = datetime.now() + timedelta(minutes=delay_minutes)

                self.write({
                    'state': 'pending',
                    'retry_count': new_retry_count,
                    'last_attempt': datetime.now(),
                    'next_attempt': next_attempt,
                    'last_error': error_message,
                })

                _logger.warning(
                    f'Retry {new_retry_count}/{self.max_retries} failed for {self.document_id.name}. '
                    f'Next attempt at {next_attempt}. Error: {error_message[:200]}'
                )

    def _notify_retry_failure(self):
        """
        Notify administrators when retry attempts are exhausted.

        Sends email notification about failed document processing.
        """
        self.ensure_one()

        # Find users with invoice manager rights
        group = self.env.ref('account.group_account_manager', raise_if_not_found=False)
        if not group:
            return

        # Create activity for managers
        try:
            self.document_id.activity_schedule(
                'mail.mail_activity_data_warning',
                summary=_('E-Invoice Retry Failed'),
                note=_(
                    'Document %s failed after %d retry attempts.\n'
                    'Operation: %s\n'
                    'Last error: %s\n\n'
                    'Please review and take manual action.'
                ) % (
                    self.document_id.name,
                    self.retry_count,
                    dict(self._fields['operation'].selection)[self.operation],
                    self.last_error[:500],
                ),
                user_id=self.env.user.id,
            )
        except Exception as e:
            _logger.error(f'Failed to create activity for retry failure: {e}')

    def action_retry_now(self):
        """
        Manual action to retry immediately.

        Allows user to trigger retry without waiting for scheduled time.
        """
        self.ensure_one()

        if self.state not in ['pending', 'failed']:
            raise UserError(_('Can only retry pending or failed items.'))

        # Update next attempt to now
        self.write({
            'next_attempt': datetime.now(),
            'state': 'pending',
        })

        # Process immediately
        self._process_retry()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Retry Executed'),
                'message': _('Retry attempt completed. Check document status for results.'),
                'type': 'info',
                'sticky': False,
            },
        }

    def action_cancel_retry(self):
        """Cancel pending retry."""
        self.ensure_one()

        if self.state == 'completed':
            raise UserError(_('Cannot cancel completed retry.'))

        self.write({'state': 'cancelled'})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Retry Cancelled'),
                'message': _('Retry has been cancelled.'),
                'type': 'success',
                'sticky': False,
            },
        }

    @api.model
    def _cleanup_old_entries(self, days=30):
        """
        Remove old completed/failed entries from queue.

        Args:
            days (int): Remove entries older than this many days
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        old_entries = self.search([
            ('state', 'in', ['completed', 'failed', 'cancelled']),
            ('create_date', '<', cutoff_date),
        ])

        count = len(old_entries)
        if count > 0:
            old_entries.unlink()
            _logger.info(f'Cleaned up {count} old retry queue entries (older than {days} days)')

        return count

    @api.model
    def get_queue_statistics(self, company_id=None):
        """
        Get statistics for retry queue.

        Args:
            company_id (int, optional): Filter by company

        Returns:
            dict: Statistics dictionary
        """
        domain = []
        if company_id:
            domain.append(('company_id', '=', company_id))

        queue_items = self.search(domain)

        stats = {
            'total': len(queue_items),
            'pending': len(queue_items.filtered(lambda q: q.state == 'pending')),
            'processing': len(queue_items.filtered(lambda q: q.state == 'processing')),
            'completed': len(queue_items.filtered(lambda q: q.state == 'completed')),
            'failed': len(queue_items.filtered(lambda q: q.state == 'failed')),
            'cancelled': len(queue_items.filtered(lambda q: q.state == 'cancelled')),
            'overdue': len(queue_items.filtered(lambda q: q.is_overdue)),
        }

        # Count by operation
        stats['by_operation'] = {
            'sign': len(queue_items.filtered(lambda q: q.operation == 'sign')),
            'submit': len(queue_items.filtered(lambda q: q.operation == 'submit')),
            'check_status': len(queue_items.filtered(lambda q: q.operation == 'check_status')),
        }

        # Count by error category
        stats['by_category'] = {}
        for category in dict(self._fields['error_category'].selection).keys():
            stats['by_category'][category] = len(
                queue_items.filtered(lambda q: q.error_category == category)
            )

        return stats
