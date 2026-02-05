# -*- coding: utf-8 -*-
"""
Integration Example: Using Rate Limiter with Hacienda API

This file demonstrates how to integrate the token bucket rate limiter
with the Hacienda API client to enforce application-wide rate limits.

DO NOT import this file in production - it's for reference only.
"""

from odoo import models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HaciendaAPIWithRateLimiting(models.AbstractModel):
    """
    Example: Hacienda API client with integrated rate limiting.

    This shows how to wrap API calls with rate limiter to enforce:
    - 10 requests/second sustained
    - 20 requests/second burst
    - Application-wide limits (all POS terminals share quota)
    """

    _name = 'l10n_cr.hacienda.api.example'
    _description = 'Hacienda API with Rate Limiting (Example)'

    @api.model
    def submit_invoice_with_rate_limit(self, clave, xml_content, sender_id, receiver_id):
        """
        Submit invoice with automatic rate limiting.

        This method demonstrates blocking acquisition - it will wait
        until a token becomes available (up to 30 seconds).

        Args:
            clave: Document key
            xml_content: Signed XML
            sender_id: Sender identification
            receiver_id: Receiver identification

        Returns:
            dict: Hacienda API response

        Raises:
            UserError: If rate limit exceeded for too long
        """
        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']

        # Acquire token (will wait up to 30 seconds if needed)
        _logger.info(f"Acquiring rate limit token for invoice {clave}")
        rate_limiter.acquire_token(timeout=30)

        # Token acquired - proceed with API call
        try:
            hacienda_api = self.env['l10n_cr.hacienda.api']
            response = hacienda_api.submit_invoice(
                clave=clave,
                xml_content=xml_content,
                sender_id=sender_id,
                receiver_id=receiver_id
            )

            _logger.info(f"Invoice {clave} submitted successfully")
            return response

        except Exception as e:
            _logger.error(f"Failed to submit invoice {clave}: {str(e)}")
            raise

    @api.model
    def submit_invoice_non_blocking(self, clave, xml_content, sender_id, receiver_id):
        """
        Submit invoice with non-blocking rate limit check.

        This method demonstrates try_acquire_token - it fails immediately
        if no tokens are available, allowing you to handle the rate limit
        differently (e.g., queue for later, show user message, etc.)

        Args:
            clave: Document key
            xml_content: Signed XML
            sender_id: Sender identification
            receiver_id: Receiver identification

        Returns:
            dict: {
                'success': bool,
                'response': API response or None,
                'rate_limited': bool,
                'message': User-friendly message
            }
        """
        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']

        # Try to acquire token without blocking
        if not rate_limiter.try_acquire_token():
            # Rate limit exceeded - cannot proceed now
            status = rate_limiter.get_available_tokens()

            _logger.warning(
                f"Rate limit exceeded for invoice {clave}. "
                f"Available tokens: {status['tokens']:.2f}/{status['capacity']}"
            )

            return {
                'success': False,
                'response': None,
                'rate_limited': True,
                'message': _(
                    'Hacienda API rate limit reached. '
                    'Your invoice has been queued and will be submitted automatically. '
                    'Current API utilization: %(util)s%%'
                ) % {'util': status['utilization']}
            }

        # Token acquired - submit invoice
        try:
            hacienda_api = self.env['l10n_cr.hacienda.api']
            response = hacienda_api.submit_invoice(
                clave=clave,
                xml_content=xml_content,
                sender_id=sender_id,
                receiver_id=receiver_id
            )

            return {
                'success': True,
                'response': response,
                'rate_limited': False,
                'message': _('Invoice submitted successfully')
            }

        except Exception as e:
            return {
                'success': False,
                'response': None,
                'rate_limited': False,
                'message': _('API error: %s') % str(e)
            }

    @api.model
    def batch_submit_with_rate_limit(self, invoices):
        """
        Submit multiple invoices with rate limiting.

        This demonstrates how to handle batch operations while respecting
        rate limits. Failed submissions are collected for retry.

        Args:
            invoices: List of invoice records to submit

        Returns:
            dict: {
                'submitted': [list of successful claves],
                'rate_limited': [list of rate-limited claves],
                'failed': [list of failed claves with errors],
            }
        """
        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']
        hacienda_api = self.env['l10n_cr.hacienda.api']

        submitted = []
        rate_limited = []
        failed = []

        for invoice in invoices:
            # Check rate limit before processing
            if not rate_limiter.try_acquire_token():
                # No tokens available - add to rate-limited queue
                rate_limited.append(invoice.clave)
                _logger.info(f"Invoice {invoice.clave} rate-limited, will retry later")
                continue

            # Token acquired - try to submit
            try:
                response = hacienda_api.submit_invoice(
                    clave=invoice.clave,
                    xml_content=invoice.signed_xml,
                    sender_id=invoice.company_id.vat,
                    receiver_id=invoice.partner_id.vat
                )

                if response.get('ind-estado') in ['aceptado', 'procesando']:
                    submitted.append(invoice.clave)
                else:
                    failed.append({
                        'clave': invoice.clave,
                        'error': response.get('detalle-mensaje', 'Unknown error')
                    })

            except Exception as e:
                failed.append({
                    'clave': invoice.clave,
                    'error': str(e)
                })

        # Log summary
        _logger.info(
            f"Batch submission complete: "
            f"{len(submitted)} submitted, "
            f"{len(rate_limited)} rate-limited, "
            f"{len(failed)} failed"
        )

        return {
            'submitted': submitted,
            'rate_limited': rate_limited,
            'failed': failed,
        }

    @api.model
    def get_rate_limit_status(self):
        """
        Get current rate limiter status for monitoring/dashboards.

        Returns:
            dict: Rate limiter statistics
        """
        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']
        return rate_limiter.get_available_tokens()

    @api.model
    def check_can_submit(self):
        """
        Check if we can submit a request right now (without consuming token).

        This is useful for UI elements to show/hide submit buttons,
        or to display rate limit warnings to users.

        Returns:
            dict: {
                'can_submit': bool,
                'tokens_available': float,
                'estimated_wait': float (seconds),
                'message': str
            }
        """
        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']
        status = rate_limiter.get_available_tokens()

        can_submit = status['tokens'] >= 1.0

        if can_submit:
            return {
                'can_submit': True,
                'tokens_available': status['tokens'],
                'estimated_wait': 0.0,
                'message': _('Ready to submit')
            }
        else:
            # Estimate wait time for next token
            tokens_needed = 1.0 - status['tokens']
            wait_seconds = tokens_needed / status['refill_rate']

            return {
                'can_submit': False,
                'tokens_available': status['tokens'],
                'estimated_wait': wait_seconds,
                'message': _('Rate limit reached. Please wait %(wait)s seconds.') % {
                    'wait': round(wait_seconds, 1)
                }
            }


# Integration with existing einvoice_document model
# Add this to l10n_cr_einvoice/models/einvoice_document.py:

"""
class EinvoiceDocument(models.Model):
    _inherit = 'l10n_cr.einvoice.document'

    def submit_to_hacienda(self):
        '''Submit document to Hacienda with rate limiting.'''
        self.ensure_one()

        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']

        # Check if we can submit now
        if not rate_limiter.try_acquire_token():
            # Rate limited - add to retry queue
            _logger.warning(
                f'Rate limit exceeded for {self.clave}. '
                f'Adding to retry queue.'
            )

            self.write({
                'state': 'queued',
                'error_message': _(
                    'Hacienda API rate limit reached. '
                    'Document will be submitted automatically within 2 minutes.'
                ),
            })

            # Create retry queue entry
            self.env['l10n_cr.einvoice.retry.queue'].create({
                'document_id': self.id,
                'retry_after': fields.Datetime.now() + timedelta(seconds=120),
                'reason': 'rate_limit',
            })

            return

        # Token acquired - proceed with submission
        try:
            hacienda_api = self.env['l10n_cr.hacienda.api']
            response = hacienda_api.submit_invoice(
                clave=self.clave,
                xml_content=self.signed_xml,
                sender_id=self.company_id.vat,
                receiver_id=self.partner_id.vat
            )

            # Handle response...
            if response.get('ind-estado') == 'aceptado':
                self.write({
                    'state': 'accepted',
                    'hacienda_response': json.dumps(response),
                })
            # ... etc

        except Exception as e:
            _logger.error(f'Failed to submit {self.clave}: {str(e)}')
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
"""
