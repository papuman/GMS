# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoicePerformanceMetrics(models.AbstractModel):
    """Performance Metrics for E-Invoice System."""

    _name = 'report.l10n_cr_einvoice.performance_metrics'
    _description = 'E-Invoice Performance Metrics'

    @api.model
    def get_api_response_time_tracking(self, date_from=None, date_to=None):
        """
        Track API response times from Hacienda.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: API response time metrics
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=7)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
            ('hacienda_submission_date', '!=', False),
        ]

        # Get documents with submission times
        documents = self.env['l10n_cr.einvoice.document'].search(domain)

        # Calculate response times from response messages
        ResponseMessage = self.env['l10n_cr.hacienda.response.message']
        response_times = []

        for doc in documents:
            messages = ResponseMessage.search([
                ('document_id', '=', doc.id),
                ('message_type', '=', 'response'),
            ], order='create_date')

            if messages:
                # Calculate time between submission and first response
                first_response = messages[0]
                if doc.hacienda_submission_date:
                    response_time = (
                        first_response.create_date - doc.hacienda_submission_date
                    ).total_seconds()

                    response_times.append({
                        'document_id': doc.id,
                        'document_number': doc.name,
                        'submission_date': doc.hacienda_submission_date,
                        'response_date': first_response.create_date,
                        'response_time_seconds': response_time,
                        'response_time_minutes': response_time / 60,
                        'status_code': first_response.status_code,
                    })

        # Calculate statistics
        if response_times:
            times = [r['response_time_seconds'] for r in response_times]
            avg_response_time = sum(times) / len(times)
            min_response_time = min(times)
            max_response_time = max(times)

            # Calculate percentiles
            sorted_times = sorted(times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p50 = p95 = p99 = 0

        # Response time distribution
        time_distribution = {
            '0-10s': 0,
            '10-30s': 0,
            '30-60s': 0,
            '60-300s': 0,
            '300+s': 0,
        }

        for item in response_times:
            time = item['response_time_seconds']
            if time <= 10:
                time_distribution['0-10s'] += 1
            elif time <= 30:
                time_distribution['10-30s'] += 1
            elif time <= 60:
                time_distribution['30-60s'] += 1
            elif time <= 300:
                time_distribution['60-300s'] += 1
            else:
                time_distribution['300+s'] += 1

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_requests': len(response_times),
            'avg_response_time_seconds': round(avg_response_time, 2),
            'avg_response_time_minutes': round(avg_response_time / 60, 2),
            'min_response_time_seconds': round(min_response_time, 2),
            'max_response_time_seconds': round(max_response_time, 2),
            'p50_response_time_seconds': round(p50, 2),
            'p95_response_time_seconds': round(p95, 2),
            'p99_response_time_seconds': round(p99, 2),
            'time_distribution': time_distribution,
            'response_details': sorted(
                response_times,
                key=lambda x: x['response_time_seconds'],
                reverse=True
            )[:20],  # Top 20 slowest
        }

    @api.model
    def get_retry_queue_efficiency(self, date_from=None, date_to=None):
        """
        Analyze retry queue efficiency.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Retry queue metrics
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=7)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ]

        RetryQueue = self.env['l10n_cr.einvoice.retry.queue']
        retry_items = RetryQueue.search(domain)

        # Status breakdown
        pending_count = len(retry_items.filtered(lambda x: x.state == 'pending'))
        processing_count = len(retry_items.filtered(lambda x: x.state == 'processing'))
        completed_count = len(retry_items.filtered(lambda x: x.state == 'completed'))
        failed_count = len(retry_items.filtered(lambda x: x.state == 'failed'))
        cancelled_count = len(retry_items.filtered(lambda x: x.state == 'cancelled'))

        total_count = len(retry_items)
        success_rate = (completed_count / total_count * 100) if total_count > 0 else 0

        # Retry attempt analysis
        avg_retries = sum(retry_items.mapped('retry_count')) / len(retry_items) if retry_items else 0
        max_retries = max(retry_items.mapped('retry_count')) if retry_items else 0

        # Operation type breakdown
        operation_stats = {}
        for item in retry_items:
            op_type = item.operation_type
            if op_type not in operation_stats:
                operation_stats[op_type] = {
                    'operation_type': op_type,
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'pending': 0,
                }

            operation_stats[op_type]['total'] += 1
            if item.state == 'completed':
                operation_stats[op_type]['completed'] += 1
            elif item.state == 'failed':
                operation_stats[op_type]['failed'] += 1
            elif item.state in ['pending', 'processing']:
                operation_stats[op_type]['pending'] += 1

        # Calculate success rate per operation
        for stats in operation_stats.values():
            stats['success_rate'] = (
                stats['completed'] / stats['total'] * 100
            ) if stats['total'] > 0 else 0

        # Calculate average processing time for completed items
        completed_items = retry_items.filtered(lambda x: x.state == 'completed')
        processing_times = []

        for item in completed_items:
            if item.last_attempt_date:
                processing_time = (
                    item.last_attempt_date - item.create_date
                ).total_seconds() / 60
                processing_times.append(processing_time)

        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_retry_items': total_count,
            'pending_count': pending_count,
            'processing_count': processing_count,
            'completed_count': completed_count,
            'failed_count': failed_count,
            'cancelled_count': cancelled_count,
            'success_rate': round(success_rate, 2),
            'avg_retries': round(avg_retries, 2),
            'max_retries': max_retries,
            'avg_processing_time_minutes': round(avg_processing_time, 2),
            'operation_stats': list(operation_stats.values()),
        }

    @api.model
    def get_email_delivery_metrics(self, date_from=None, date_to=None):
        """
        Track email delivery success rates.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Email delivery metrics
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=7)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
            ('state', '=', 'accepted'),
        ]

        documents = self.env['l10n_cr.einvoice.document'].search(domain)

        total_eligible = len(documents)
        emails_sent = len(documents.filtered(lambda x: x.email_sent))
        emails_not_sent = total_eligible - emails_sent

        delivery_rate = (emails_sent / total_eligible * 100) if total_eligible > 0 else 0

        # Email delivery times
        delivery_times = []
        for doc in documents.filtered(lambda x: x.email_sent and x.email_sent_date):
            # Calculate time from acceptance to email sent
            if doc.hacienda_acceptance_date and doc.email_sent_date:
                delivery_time = (
                    doc.email_sent_date - doc.hacienda_acceptance_date
                ).total_seconds() / 60

                delivery_times.append({
                    'document_number': doc.name,
                    'acceptance_date': doc.hacienda_acceptance_date,
                    'email_sent_date': doc.email_sent_date,
                    'delivery_time_minutes': delivery_time,
                })

        avg_delivery_time = (
            sum(d['delivery_time_minutes'] for d in delivery_times) / len(delivery_times)
        ) if delivery_times else 0

        # Document type breakdown
        fe_sent = len(documents.filtered(lambda x: x.document_type == 'FE' and x.email_sent))
        te_sent = len(documents.filtered(lambda x: x.document_type == 'TE' and x.email_sent))
        nc_sent = len(documents.filtered(lambda x: x.document_type == 'NC' and x.email_sent))
        nd_sent = len(documents.filtered(lambda x: x.document_type == 'ND' and x.email_sent))

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_eligible_documents': total_eligible,
            'emails_sent': emails_sent,
            'emails_not_sent': emails_not_sent,
            'delivery_rate': round(delivery_rate, 2),
            'avg_delivery_time_minutes': round(avg_delivery_time, 2),
            'fe_emails_sent': fe_sent,
            'te_emails_sent': te_sent,
            'nc_emails_sent': nc_sent,
            'nd_emails_sent': nd_sent,
            'delivery_time_details': sorted(
                delivery_times,
                key=lambda x: x['delivery_time_minutes'],
                reverse=True
            )[:20],
        }

    @api.model
    def get_pdf_generation_performance(self, date_from=None, date_to=None):
        """
        Track PDF generation performance.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: PDF generation metrics
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=7)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
            ('state', '=', 'accepted'),
        ]

        documents = self.env['l10n_cr.einvoice.document'].search(domain)

        total_documents = len(documents)
        pdfs_generated = len(documents.filtered(lambda x: x.pdf_attachment_id))
        pdfs_not_generated = total_documents - pdfs_generated

        generation_rate = (pdfs_generated / total_documents * 100) if total_documents > 0 else 0

        # Document type breakdown
        fe_pdfs = len(documents.filtered(lambda x: x.document_type == 'FE' and x.pdf_attachment_id))
        te_pdfs = len(documents.filtered(lambda x: x.document_type == 'TE' and x.pdf_attachment_id))
        nc_pdfs = len(documents.filtered(lambda x: x.document_type == 'NC' and x.pdf_attachment_id))
        nd_pdfs = len(documents.filtered(lambda x: x.document_type == 'ND' and x.pdf_attachment_id))

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_documents': total_documents,
            'pdfs_generated': pdfs_generated,
            'pdfs_not_generated': pdfs_not_generated,
            'generation_rate': round(generation_rate, 2),
            'fe_pdfs_generated': fe_pdfs,
            'te_pdfs_generated': te_pdfs,
            'nc_pdfs_generated': nc_pdfs,
            'nd_pdfs_generated': nd_pdfs,
        }

    @api.model
    def get_pos_transaction_volume(self, date_from=None, date_to=None):
        """
        Track POS transaction volumes.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: POS transaction metrics
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=7)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        # POS transactions (TE documents)
        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
            ('document_type', '=', 'TE'),
        ]

        te_documents = self.env['l10n_cr.einvoice.document'].search(domain)

        total_transactions = len(te_documents)
        accepted_transactions = len(te_documents.filtered(lambda x: x.state == 'accepted'))
        rejected_transactions = len(te_documents.filtered(lambda x: x.state == 'rejected'))
        pending_transactions = len(te_documents.filtered(lambda x: x.state in ['draft', 'generated', 'signed', 'submitted']))

        acceptance_rate = (accepted_transactions / total_transactions * 100) if total_transactions > 0 else 0

        total_revenue = sum(te_documents.mapped('amount_total'))
        avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0

        # Offline queue status
        OfflineQueue = self.env['l10n_cr.pos.offline.queue']
        offline_domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ]

        offline_items = OfflineQueue.search(offline_domain)
        offline_pending = len(offline_items.filtered(lambda x: x.state == 'pending'))
        offline_completed = len(offline_items.filtered(lambda x: x.state == 'completed'))
        offline_failed = len(offline_items.filtered(lambda x: x.state == 'failed'))

        # Daily transaction volume
        daily_volume = {}
        for doc in te_documents:
            date_key = doc.create_date.date().strftime('%Y-%m-%d')
            if date_key not in daily_volume:
                daily_volume[date_key] = {
                    'date': date_key,
                    'transaction_count': 0,
                    'total_revenue': 0,
                }

            daily_volume[date_key]['transaction_count'] += 1
            daily_volume[date_key]['total_revenue'] += doc.amount_total

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_transactions': total_transactions,
            'accepted_transactions': accepted_transactions,
            'rejected_transactions': rejected_transactions,
            'pending_transactions': pending_transactions,
            'acceptance_rate': round(acceptance_rate, 2),
            'total_revenue': total_revenue,
            'avg_transaction_value': round(avg_transaction_value, 2),
            'offline_queue_pending': offline_pending,
            'offline_queue_completed': offline_completed,
            'offline_queue_failed': offline_failed,
            'daily_volume': sorted(daily_volume.values(), key=lambda x: x['date']),
        }

    @api.model
    def get_system_health_metrics(self):
        """
        Get overall system health metrics.

        Returns:
            dict: System health summary
        """
        # Documents in error state
        error_documents = self.env['l10n_cr.einvoice.document'].search_count([
            ('state', '=', 'error')
        ])

        # Stuck documents (pending > 24 hours)
        stuck_threshold = datetime.now() - timedelta(hours=24)
        stuck_documents = self.env['l10n_cr.einvoice.document'].search_count([
            ('state', 'in', ['draft', 'generated', 'signed', 'submitted']),
            ('create_date', '<', stuck_threshold)
        ])

        # Retry queue backlog
        retry_backlog = self.env['l10n_cr.einvoice.retry.queue'].search_count([
            ('state', 'in', ['pending', 'processing'])
        ])

        # Offline queue backlog
        offline_backlog = self.env['l10n_cr.pos.offline.queue'].search_count([
            ('state', 'in', ['pending', 'processing'])
        ])

        # Recent acceptance rate (last 24 hours)
        recent_domain = [
            ('create_date', '>=', fields.Datetime.to_string(datetime.now() - timedelta(hours=24)))
        ]
        recent_docs = self.env['l10n_cr.einvoice.document'].search(recent_domain)
        recent_accepted = len(recent_docs.filtered(lambda x: x.state == 'accepted'))
        recent_rate = (recent_accepted / len(recent_docs) * 100) if recent_docs else 0

        # Determine health status
        if error_documents > 10 or stuck_documents > 20 or retry_backlog > 50:
            health_status = 'critical'
        elif error_documents > 5 or stuck_documents > 10 or retry_backlog > 20:
            health_status = 'warning'
        else:
            health_status = 'healthy'

        return {
            'health_status': health_status,
            'error_documents': error_documents,
            'stuck_documents': stuck_documents,
            'retry_queue_backlog': retry_backlog,
            'offline_queue_backlog': offline_backlog,
            'recent_acceptance_rate': round(recent_rate, 2),
            'timestamp': fields.Datetime.now(),
        }
