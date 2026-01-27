# -*- coding: utf-8 -*-
"""
Phase 3 Enhancements for EInvoice Document Model

Add these methods to the einvoice_document.py file after the existing methods.
These additions implement automatic polling, response storage, and retry queue integration.
"""
import logging
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# ADD THESE METHODS TO THE EInvoiceDocument CLASS IN einvoice_document.py:

def _process_hacienda_response_enhanced(self, response):
    """
    Enhanced version of _process_hacienda_response with response message storage.

    This replaces the existing _process_hacienda_response method.

    Args:
        response (dict): Response from Hacienda API
    """
    self.ensure_one()

    # Store response message in repository (Phase 3)
    self._store_response_message(response)

    # Original response processing logic
    status = response.get('ind-estado', '').lower()

    # Use decoded message if available, otherwise use base64
    message = response.get('respuesta-xml-decoded') or response.get('respuesta-xml', '')

    # Extract error details if present
    error_info = response.get('error_details', '')

    vals = {
        'hacienda_response': str(response),
        'hacienda_message': message[:500] if message else '',  # Limit message length
        'hacienda_submission_date': fields.Datetime.now(),
    }

    if status == 'aceptado':
        vals.update({
            'state': 'accepted',
            'hacienda_acceptance_date': fields.Datetime.now(),
            'error_message': False,  # Clear any previous errors
        })
        _logger.info(f'Document {self.name} accepted by Hacienda')

        # Update document first
        self.write(vals)

        # Auto-send email if configured
        self._auto_send_email_on_acceptance()

        # Return early to avoid duplicate write
        return

    elif status == 'rechazado':
        vals.update({
            'state': 'rejected',
            'error_message': error_info or message,
        })
        _logger.warning(f'Document {self.name} rejected by Hacienda: {error_info or message}')

    elif status in ['procesando', 'recibido']:
        vals.update({
            'state': 'submitted',
        })
        _logger.info(f'Document {self.name} submitted, status: {status}')

    else:
        # Unknown or error status
        vals.update({
            'state': 'error',
            'error_message': f'Unknown status: {status}. {error_info or message}',
        })
        _logger.error(f'Document {self.name} unknown status: {status}')

    self.write(vals)


def _store_response_message(self, response):
    """
    Store Hacienda response in the response message repository.

    Args:
        response (dict): Response from Hacienda API
    """
    self.ensure_one()

    try:
        response_msg_model = self.env['l10n_cr.hacienda.response.message']
        response_msg_model.create_from_hacienda_response(self, response)
        _logger.debug(f'Stored Hacienda response for document {self.name}')
    except Exception as e:
        # Don't fail the whole process if storage fails
        _logger.error(f'Failed to store response message for {self.name}: {e}')


def _add_to_retry_queue(self, operation, error_message):
    """
    Add document to retry queue after failure.

    Args:
        operation (str): Failed operation ('sign', 'submit', 'check_status')
        error_message (str): Error message from failure
    """
    self.ensure_one()

    try:
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Classify error
        error_category = retry_queue.classify_error(error_message)

        # Determine priority based on document type
        priority = '2' if self.document_type in ['FE', 'NC', 'ND'] else '1'

        # Add to queue
        retry_queue.add_to_queue(
            document=self,
            operation=operation,
            error_message=error_message,
            error_category=error_category,
            priority=priority,
        )

        _logger.info(f'Added {self.name} to retry queue: {operation} ({error_category})')

    except Exception as e:
        _logger.error(f'Failed to add {self.name} to retry queue: {e}')


@api.model
def _cron_poll_pending_documents(self):
    """
    Scheduled action to automatically check status of submitted documents.

    Runs periodically (every 15 minutes by default) to poll Hacienda for
    status updates on documents in 'submitted' state.
    """
    company = self.env.company

    # Check if auto-polling is enabled
    if not company.l10n_cr_auto_polling_enabled:
        _logger.debug('Auto-polling disabled for company %s', company.name)
        return

    # Get polling configuration
    max_age_hours = company.l10n_cr_polling_max_hours or 24
    min_age_minutes = 2  # Don't poll too soon after submission

    # Calculate cutoff dates
    cutoff_date = fields.Datetime.now() - timedelta(hours=max_age_hours)
    min_date = fields.Datetime.now() - timedelta(minutes=min_age_minutes)

    # Find documents to poll
    documents = self.search([
        ('state', '=', 'submitted'),
        ('hacienda_submission_date', '>=', cutoff_date),
        ('hacienda_submission_date', '<=', min_date),
        ('company_id', '=', company.id),
    ], limit=100, order='hacienda_submission_date asc')

    _logger.info(f'Polling {len(documents)} submitted documents for company {company.name}')

    # Process in batches
    batch_size = company.l10n_cr_polling_batch_size or 50
    success_count = 0
    error_count = 0

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]

        for doc in batch:
            try:
                doc.action_check_status()
                self.env.cr.commit()  # Commit after each document
                success_count += 1

                # Rate limiting delay
                import time
                time.sleep(0.5)

            except Exception as e:
                error_count += 1
                _logger.error(f'Polling error for {doc.name}: {e}')
                continue

        # Delay between batches
        if i + batch_size < len(documents):
            import time
            time.sleep(5)

    _logger.info(
        f'Polling completed: {success_count} successful, {error_count} errors'
    )

    # Mark expired documents as error
    expired_docs = self.search([
        ('state', '=', 'submitted'),
        ('hacienda_submission_date', '<', cutoff_date),
        ('company_id', '=', company.id),
    ])

    if expired_docs:
        expired_docs.write({
            'state': 'error',
            'error_message': _(
                'Polling timeout exceeded (%d hours). Please check status manually.'
            ) % max_age_hours,
        })
        _logger.warning(f'Marked {len(expired_docs)} documents as error (polling timeout)')


def action_submit_to_hacienda_with_retry(self):
    """
    Enhanced version of action_submit_to_hacienda with retry queue integration.

    This replaces the existing action_submit_to_hacienda method.
    """
    self.ensure_one()

    if self.state != 'signed':
        raise UserError(_('Can only submit signed documents.'))

    if not self.signed_xml:
        raise UserError(_('No signed XML to submit.'))

    try:
        # Get API client
        api_client = self.env['l10n_cr.hacienda.api']

        # Submit to Hacienda
        response = api_client.submit_invoice(
            clave=self.clave,
            xml_content=self.signed_xml,
            sender_id=self.company_id.vat,
            receiver_id=self.partner_id.vat or '',
        )

        # Update document based on response (uses enhanced version)
        self._process_hacienda_response(response)

        _logger.info(f'Submitted document {self.name} to Hacienda')

    except Exception as e:
        error_msg = str(e)
        _logger.error(f'Error submitting {self.name} to Hacienda: {error_msg}')

        # Add to retry queue (Phase 3)
        self._add_to_retry_queue('submit', error_msg)

        # Update document state
        self.write({
            'state': 'error',
            'error_message': error_msg,
            'retry_count': self.retry_count + 1,
        })

        raise UserError(_('Error submitting to Hacienda: %s') % error_msg)


def action_sign_xml_with_retry(self):
    """
    Enhanced version of action_sign_xml with retry queue integration.

    This replaces the existing action_sign_xml method.
    """
    self.ensure_one()

    if self.state != 'generated':
        raise UserError(_('Can only sign generated XML documents.'))

    if not self.xml_content:
        raise UserError(_('No XML content to sign.'))

    try:
        # Get company certificate
        certificate = self.company_id.l10n_cr_certificate
        private_key = self.company_id.l10n_cr_private_key

        if not certificate or not private_key:
            raise UserError(_('Company certificate and private key must be configured.'))

        # Sign the XML
        signed_xml = self._sign_xml_content(self.xml_content, certificate, private_key)

        # Create XML attachment
        attachment = self._create_xml_attachment(signed_xml)

        # Update document
        self.write({
            'signed_xml': signed_xml,
            'xml_attachment_id': attachment.id,
            'state': 'signed',
            'error_message': False,
        })

        _logger.info(f'Signed XML for document {self.name}')

    except Exception as e:
        error_msg = str(e)
        _logger.error(f'Error signing XML for {self.name}: {error_msg}')

        # Add to retry queue (Phase 3)
        self._add_to_retry_queue('sign', error_msg)

        self.write({
            'state': 'error',
            'error_message': error_msg,
        })

        raise UserError(_('Error signing XML: %s') % error_msg)


def action_view_response_messages(self):
    """
    View all response messages for this document.

    Returns action to display response message list.
    """
    self.ensure_one()

    return {
        'name': _('Hacienda Response Messages'),
        'type': 'ir.actions.act_window',
        'res_model': 'l10n_cr.hacienda.response.message',
        'view_mode': 'tree,form',
        'domain': [('document_id', '=', self.id)],
        'context': {'default_document_id': self.id},
    }


def action_view_retry_queue(self):
    """
    View retry queue entries for this document.

    Returns action to display retry queue entries.
    """
    self.ensure_one()

    return {
        'name': _('Retry Queue'),
        'type': 'ir.actions.act_window',
        'res_model': 'l10n_cr.einvoice.retry.queue',
        'view_mode': 'tree,form',
        'domain': [('document_id', '=', self.id)],
        'context': {'default_document_id': self.id},
    }


@api.model
def get_dashboard_statistics(self, company_id=None):
    """
    Get statistics for dashboard display.

    Args:
        company_id (int, optional): Filter by company

    Returns:
        dict: Statistics dictionary
    """
    domain = []
    if company_id:
        domain.append(('company_id', '=', company_id))
    else:
        domain.append(('company_id', '=', self.env.company.id))

    # Today's date range
    today_start = fields.Datetime.now().replace(hour=0, minute=0, second=0)
    today_end = fields.Datetime.now().replace(hour=23, minute=59, second=59)

    # Get all documents
    all_docs = self.search(domain)

    # Count by state
    stats = {
        'total_documents': len(all_docs),
        'draft': len(all_docs.filtered(lambda d: d.state == 'draft')),
        'generated': len(all_docs.filtered(lambda d: d.state == 'generated')),
        'signed': len(all_docs.filtered(lambda d: d.state == 'signed')),
        'submitted': len(all_docs.filtered(lambda d: d.state == 'submitted')),
        'accepted': len(all_docs.filtered(lambda d: d.state == 'accepted')),
        'rejected': len(all_docs.filtered(lambda d: d.state == 'rejected')),
        'error': len(all_docs.filtered(lambda d: d.state == 'error')),
    }

    # Today's statistics
    today_domain = domain + [
        ('create_date', '>=', today_start),
        ('create_date', '<=', today_end),
    ]
    today_docs = self.search(today_domain)

    stats['today_created'] = len(today_docs)
    stats['today_accepted'] = len(today_docs.filtered(lambda d: d.state == 'accepted'))
    stats['today_rejected'] = len(today_docs.filtered(lambda d: d.state == 'rejected'))

    # Acceptance rate
    final_docs = all_docs.filtered(lambda d: d.state in ['accepted', 'rejected'])
    if final_docs:
        acceptance_count = len(final_docs.filtered(lambda d: d.state == 'accepted'))
        stats['acceptance_rate'] = (acceptance_count / len(final_docs)) * 100
    else:
        stats['acceptance_rate'] = 0.0

    # Average acceptance time (in hours)
    accepted_docs = all_docs.filtered(
        lambda d: d.state == 'accepted' and d.hacienda_submission_date and d.hacienda_acceptance_date
    )
    if accepted_docs:
        total_hours = 0
        for doc in accepted_docs:
            delta = doc.hacienda_acceptance_date - doc.hacienda_submission_date
            total_hours += delta.total_seconds() / 3600
        stats['avg_acceptance_time'] = total_hours / len(accepted_docs)
    else:
        stats['avg_acceptance_time'] = 0.0

    # Pending actions
    stats['pending_submission'] = len(all_docs.filtered(lambda d: d.state == 'signed'))
    stats['pending_status_check'] = len(all_docs.filtered(lambda d: d.state == 'submitted'))

    return stats


"""
INSTALLATION INSTRUCTIONS:

1. Backup the existing einvoice_document.py file

2. Replace the _process_hacienda_response method with _process_hacienda_response_enhanced

3. Replace the action_submit_to_hacienda method with action_submit_to_hacienda_with_retry

4. Replace the action_sign_xml method with action_sign_xml_with_retry

5. Add these new methods to the EInvoiceDocument class:
   - _store_response_message
   - _add_to_retry_queue
   - _cron_poll_pending_documents (classmethod with @api.model)
   - action_view_response_messages
   - action_view_retry_queue
   - get_dashboard_statistics (classmethod with @api.model)

6. Update the imports at the top of the file to include:
   from datetime import datetime, timedelta

7. The polling configuration fields will be added to res_company.py in the next step
"""
