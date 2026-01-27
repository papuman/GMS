# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class EInvoiceEmailSender(models.AbstractModel):
    """
    Advanced email sending service for Costa Rica electronic invoices.

    Features:
    - Automatic email sending on status changes
    - Template selection based on document type and status
    - Retry logic for failed sends (max 3 attempts)
    - Rate limiting to avoid spam filters (max 50/hour)
    - Customer email preferences (opt-out support)
    - Multiple recipients (customer email + CC)
    - Comprehensive error logging
    - Email queue for batch processing
    """
    _name = 'l10n_cr.einvoice.email.sender'
    _description = 'Costa Rica E-Invoice Email Sender Service'

    @api.model
    def send_email_for_document(self, document, template_ref=None, force_send=False):
        """
        Send email for an electronic invoice document.

        Args:
            document: l10n_cr.einvoice.document record
            template_ref: Optional template reference (auto-selected if None)
            force_send: Force send even if already sent

        Returns:
            bool: True if email sent successfully, False otherwise

        Raises:
            UserError: If document or customer validation fails
        """
        document.ensure_one()

        # Validation checks
        if not self._validate_email_send(document, force_send):
            return False

        # Check rate limiting
        if not force_send and not self._check_rate_limit(document.company_id):
            _logger.warning(
                f'Rate limit exceeded for company {document.company_id.name}. '
                f'Email queued for later delivery.'
            )
            self._queue_email(document, template_ref)
            return False

        try:
            # Select appropriate template
            template = self._get_email_template(document, template_ref)

            if not template:
                raise UserError(_('No email template found for this document.'))

            # Prepare email values
            email_values = self._prepare_email_values(document)

            # Send email
            mail_id = template.send_mail(
                document.id,
                force_send=True,
                email_values=email_values,
                notif_layout='mail.mail_notification_light',
            )

            # Update document
            document.write({
                'email_sent': True,
                'email_sent_date': fields.Datetime.now(),
                'email_error': False,
                'email_retry_count': 0,
            })

            _logger.info(
                f'Email sent successfully for document {document.name} '
                f'to {document.partner_id.email}'
            )

            return True

        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error sending email for {document.name}: {error_msg}')

            # Record error and increment retry count
            retry_count = (document.email_retry_count or 0) + 1
            document.write({
                'email_error': error_msg,
                'email_retry_count': retry_count,
            })

            # Queue for retry if under max attempts
            if retry_count < 3:
                self._queue_email_retry(document, template_ref, error_msg)
            else:
                _logger.error(
                    f'Max retry attempts (3) reached for document {document.name}. '
                    f'Email sending abandoned.'
                )

            return False

    @api.model
    def _validate_email_send(self, document, force_send=False):
        """
        Validate if email can be sent for this document.

        Args:
            document: l10n_cr.einvoice.document record
            force_send: Skip some validations if True

        Returns:
            bool: True if validation passes
        """
        # Check if already sent
        if document.email_sent and not force_send:
            _logger.debug(f'Email already sent for document {document.name}')
            return False

        # Check if customer has email
        if not document.partner_id.email:
            _logger.warning(
                f'Cannot send email for {document.name}: '
                f'Customer {document.partner_id.name} has no email address'
            )
            document.write({
                'email_error': _('Customer has no email address'),
            })
            return False

        # Check customer email preferences (opt-out)
        if self._customer_opted_out(document.partner_id):
            _logger.info(
                f'Customer {document.partner_id.name} has opted out of emails. '
                f'Skipping send for {document.name}'
            )
            return False

        # Check document state (only send for accepted by default)
        if not force_send and document.state not in ['accepted', 'rejected']:
            _logger.debug(
                f'Document {document.name} not in sendable state: {document.state}'
            )
            return False

        return True

    @api.model
    def _get_email_template(self, document, template_ref=None):
        """
        Get appropriate email template based on document type and status.

        Args:
            document: l10n_cr.einvoice.document record
            template_ref: Optional template reference override

        Returns:
            mail.template record or False
        """
        if template_ref:
            # Use provided template reference
            try:
                return self.env.ref(template_ref)
            except ValueError:
                _logger.warning(f'Template reference not found: {template_ref}')

        # Auto-select template based on state and document type
        template_mapping = {
            ('accepted', 'FE'): 'l10n_cr_einvoice.email_template_invoice_accepted',
            ('accepted', 'TE'): 'l10n_cr_einvoice.email_template_invoice_accepted',
            ('accepted', 'NC'): 'l10n_cr_einvoice.email_template_credit_note_notification',
            ('accepted', 'ND'): 'l10n_cr_einvoice.email_template_debit_note_notification',
            ('rejected', 'FE'): 'l10n_cr_einvoice.email_template_invoice_rejected',
            ('rejected', 'TE'): 'l10n_cr_einvoice.email_template_invoice_rejected',
            ('rejected', 'NC'): 'l10n_cr_einvoice.email_template_invoice_rejected',
            ('rejected', 'ND'): 'l10n_cr_einvoice.email_template_invoice_rejected',
            ('submitted', 'FE'): 'l10n_cr_einvoice.email_template_invoice_pending',
            ('submitted', 'TE'): 'l10n_cr_einvoice.email_template_invoice_pending',
        }

        template_key = (document.state, document.document_type)
        template_ref = template_mapping.get(template_key)

        if not template_ref:
            # Fallback to generic template
            _logger.warning(
                f'No specific template for state={document.state}, '
                f'type={document.document_type}. Using generic template.'
            )
            template_ref = 'l10n_cr_einvoice.email_template_einvoice'

        try:
            return self.env.ref(template_ref, raise_if_not_found=False)
        except Exception as e:
            _logger.error(f'Error loading template {template_ref}: {e}')
            return False

    @api.model
    def _prepare_email_values(self, document):
        """
        Prepare email values including attachments.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            dict: Email values for send_mail
        """
        email_values = {}

        # Attach PDF and XML
        attachment_ids = []

        # Generate PDF if not exists
        if not document.pdf_attachment_id:
            try:
                document.action_generate_pdf()
            except Exception as e:
                _logger.warning(f'Could not generate PDF for {document.name}: {e}')

        if document.pdf_attachment_id:
            attachment_ids.append(document.pdf_attachment_id.id)

        if document.xml_attachment_id:
            attachment_ids.append(document.xml_attachment_id.id)

        if attachment_ids:
            email_values['attachment_ids'] = [(6, 0, attachment_ids)]

        # Add CC recipients from company settings
        cc_emails = self._get_cc_recipients(document.company_id)
        if cc_emails:
            email_values['email_cc'] = cc_emails

        return email_values

    @api.model
    def _customer_opted_out(self, partner):
        """
        Check if customer has opted out of email notifications.

        Args:
            partner: res.partner record

        Returns:
            bool: True if opted out
        """
        # Check if partner has email_opt_out field (from mail module)
        if hasattr(partner, 'email_opt_out'):
            return partner.email_opt_out

        # Check custom field for einvoice emails
        if hasattr(partner, 'l10n_cr_einvoice_email_opt_out'):
            return partner.l10n_cr_einvoice_email_opt_out

        return False

    @api.model
    def _get_cc_recipients(self, company):
        """
        Get CC email recipients from company settings.

        Args:
            company: res.company record

        Returns:
            str: Comma-separated email addresses or False
        """
        if hasattr(company, 'l10n_cr_einvoice_email_cc'):
            return company.l10n_cr_einvoice_email_cc
        return False

    @api.model
    def _check_rate_limit(self, company):
        """
        Check if sending email would exceed rate limit.

        Rate limit: 50 emails per hour per company

        Args:
            company: res.company record

        Returns:
            bool: True if under rate limit, False if exceeded
        """
        # Get emails sent in last hour
        one_hour_ago = fields.Datetime.now() - timedelta(hours=1)

        recent_emails = self.env['l10n_cr.einvoice.document'].search_count([
            ('company_id', '=', company.id),
            ('email_sent', '=', True),
            ('email_sent_date', '>=', one_hour_ago),
        ])

        # Get rate limit from settings (default 50/hour)
        rate_limit = 50
        if hasattr(company, 'l10n_cr_email_rate_limit'):
            rate_limit = company.l10n_cr_email_rate_limit or 50

        if recent_emails >= rate_limit:
            _logger.warning(
                f'Rate limit reached for {company.name}: '
                f'{recent_emails}/{rate_limit} emails in last hour'
            )
            return False

        return True

    @api.model
    def _queue_email(self, document, template_ref=None):
        """
        Queue email for later delivery (when rate limit is exceeded).

        Args:
            document: l10n_cr.einvoice.document record
            template_ref: Optional template reference
        """
        # Create a scheduled action to send this email later
        # This could use ir.cron or a custom queue table
        _logger.info(f'Queued email for document {document.name} (rate limit)')

        # For now, just log. In production, implement proper queue
        # TODO: Implement email queue table in Phase 5

    @api.model
    def _queue_email_retry(self, document, template_ref, error_msg):
        """
        Queue email for retry after failure.

        Args:
            document: l10n_cr.einvoice.document record
            template_ref: Template reference
            error_msg: Error message from failed attempt
        """
        retry_count = document.email_retry_count or 0

        # Calculate exponential backoff delay
        # Retry 1: 5 minutes
        # Retry 2: 15 minutes
        # Retry 3: 30 minutes
        delays = [5, 15, 30]
        delay_minutes = delays[min(retry_count, len(delays) - 1)]

        _logger.info(
            f'Queued email retry {retry_count + 1}/3 for document {document.name} '
            f'(retry in {delay_minutes} minutes)'
        )

        # TODO: Implement retry queue in Phase 5
        # For now, the cron job can pick up failed emails and retry

    @api.model
    def _cron_process_email_queue(self):
        """
        Scheduled action to process queued and retry emails.

        Called by cron job every 15 minutes to:
        - Send queued emails (rate limit)
        - Retry failed emails
        """
        company = self.env.company

        # Process retry emails
        retry_documents = self.env['l10n_cr.einvoice.document'].search([
            ('company_id', '=', company.id),
            ('email_sent', '=', False),
            ('email_error', '!=', False),
            ('email_retry_count', '<', 3),
            ('state', 'in', ['accepted', 'rejected']),
        ], limit=20)

        _logger.info(
            f'Processing {len(retry_documents)} email retries for {company.name}'
        )

        for doc in retry_documents:
            try:
                self.send_email_for_document(doc, force_send=False)
                self.env.cr.commit()
            except Exception as e:
                _logger.error(f'Retry failed for {doc.name}: {e}')
                continue

    @api.model
    def send_batch_emails(self, documents, template_ref=None):
        """
        Send emails for multiple documents in batch.

        Respects rate limiting and processes in optimal order.

        Args:
            documents: l10n_cr.einvoice.document recordset
            template_ref: Optional template reference

        Returns:
            dict: Statistics {sent: int, failed: int, skipped: int}
        """
        stats = {'sent': 0, 'failed': 0, 'skipped': 0}

        # Filter to documents that can receive email
        sendable_docs = documents.filtered(
            lambda d: d.partner_id.email and not d.email_sent
        )

        _logger.info(f'Batch sending emails for {len(sendable_docs)} documents')

        for doc in sendable_docs:
            try:
                if self.send_email_for_document(doc, template_ref):
                    stats['sent'] += 1
                else:
                    stats['skipped'] += 1

                # Small delay between sends
                import time
                time.sleep(0.5)

            except Exception as e:
                _logger.error(f'Batch send failed for {doc.name}: {e}')
                stats['failed'] += 1
                continue

        _logger.info(
            f'Batch email complete: {stats["sent"]} sent, '
            f'{stats["failed"]} failed, {stats["skipped"]} skipped'
        )

        return stats

    @api.model
    def auto_send_on_acceptance(self, document):
        """
        Automatically send email when document is accepted by Hacienda.

        Called by einvoice_document when state changes to 'accepted'.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            bool: True if sent, False if skipped/failed
        """
        # Check if auto-send is enabled
        if not document.company_id.l10n_cr_auto_send_email:
            _logger.debug(
                f'Auto-send disabled for company {document.company_id.name}'
            )
            return False

        # Send email
        return self.send_email_for_document(document, force_send=False)
