# -*- coding: utf-8 -*-
"""
Phase 3: Bulk Operations Wizards

Wizards for performing bulk operations on multiple e-invoice documents:
- Bulk Sign: Sign multiple XML documents at once
- Bulk Submit: Submit multiple signed documents to Hacienda
- Bulk Status Check: Check status of multiple submitted documents
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BulkSignWizard(models.TransientModel):
    """
    Wizard for bulk signing multiple e-invoice documents.

    Allows users to select and sign multiple XML documents in one operation.
    """
    _name = 'l10n_cr.bulk.sign.wizard'
    _description = 'Bulk Sign E-Invoice Documents'

    document_ids = fields.Many2many(
        'l10n_cr.einvoice.document',
        string='Documents to Sign',
        required=True,
    )

    total_documents = fields.Integer(
        string='Total Documents',
        compute='_compute_total_documents',
    )

    continue_on_error = fields.Boolean(
        string='Continue on Error',
        default=True,
        help='If checked, continue signing other documents even if one fails',
    )

    @api.depends('document_ids')
    def _compute_total_documents(self):
        """Calculate total documents selected."""
        for record in self:
            record.total_documents = len(record.document_ids)

    @api.model
    def default_get(self, fields_list):
        """Pre-fill with selected documents from context."""
        res = super(BulkSignWizard, self).default_get(fields_list)

        # Get active IDs from context
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            # Filter only documents in 'generated' state
            documents = self.env['l10n_cr.einvoice.document'].browse(active_ids)
            signable_docs = documents.filtered(lambda d: d.state == 'generated')
            res['document_ids'] = [(6, 0, signable_docs.ids)]

        return res

    def action_sign_documents(self):
        """Execute bulk sign operation."""
        self.ensure_one()

        if not self.document_ids:
            raise UserError(_('No documents selected for signing.'))

        success_count = 0
        error_count = 0
        errors = []

        total = len(self.document_ids)

        for index, document in enumerate(self.document_ids, 1):
            try:
                # Log progress
                _logger.info(f'Signing document {index}/{total}: {document.name}')

                # Sign the document
                document.action_sign_xml()
                success_count += 1

                # Commit after each success if continue_on_error is enabled
                if self.continue_on_error:
                    self.env.cr.commit()

            except Exception as e:
                error_count += 1
                error_msg = f'{document.name}: {str(e)}'
                errors.append(error_msg)
                _logger.error(f'Error signing {document.name}: {e}')

                if not self.continue_on_error:
                    # Rollback and raise error
                    self.env.cr.rollback()
                    raise UserError(_(
                        'Bulk signing stopped due to error:\n%s\n\n'
                        'Signed: %d\nFailed: %d'
                    ) % (error_msg, success_count, error_count))

        # Show results
        message = _(
            'Bulk Signing Complete!\n\n'
            'Successfully signed: %d\n'
            'Failed: %d\n'
            'Total processed: %d'
        ) % (success_count, error_count, total)

        if errors:
            message += '\n\nErrors:\n' + '\n'.join(errors[:10])
            if len(errors) > 10:
                message += f'\n... and {len(errors) - 10} more errors'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Signing Complete'),
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }


class BulkSubmitWizard(models.TransientModel):
    """
    Wizard for bulk submitting multiple e-invoice documents to Hacienda.

    Submits multiple signed documents in one operation with rate limiting.
    """
    _name = 'l10n_cr.bulk.submit.wizard'
    _description = 'Bulk Submit E-Invoice Documents'

    document_ids = fields.Many2many(
        'l10n_cr.einvoice.document',
        string='Documents to Submit',
        required=True,
    )

    total_documents = fields.Integer(
        string='Total Documents',
        compute='_compute_total_documents',
    )

    continue_on_error = fields.Boolean(
        string='Continue on Error',
        default=True,
        help='If checked, continue submitting other documents even if one fails',
    )

    batch_size = fields.Integer(
        string='Batch Size',
        default=10,
        help='Number of documents to submit per batch (rate limiting)',
    )

    delay_between_batches = fields.Integer(
        string='Delay Between Batches (seconds)',
        default=5,
        help='Delay in seconds between batches to avoid rate limiting',
    )

    @api.depends('document_ids')
    def _compute_total_documents(self):
        """Calculate total documents selected."""
        for record in self:
            record.total_documents = len(record.document_ids)

    @api.model
    def default_get(self, fields_list):
        """Pre-fill with selected documents from context."""
        res = super(BulkSubmitWizard, self).default_get(fields_list)

        # Get active IDs from context
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            # Filter only documents in 'signed' state
            documents = self.env['l10n_cr.einvoice.document'].browse(active_ids)
            submittable_docs = documents.filtered(lambda d: d.state == 'signed')
            res['document_ids'] = [(6, 0, submittable_docs.ids)]

        return res

    def action_submit_documents(self):
        """Execute bulk submit operation with batching."""
        self.ensure_one()

        if not self.document_ids:
            raise UserError(_('No documents selected for submission.'))

        import time

        success_count = 0
        error_count = 0
        errors = []

        total = len(self.document_ids)
        batch_size = self.batch_size or 10

        # Process in batches
        for batch_num, i in enumerate(range(0, total, batch_size), 1):
            batch = self.document_ids[i:i + batch_size]

            _logger.info(f'Processing batch {batch_num}: documents {i+1} to {i+len(batch)}')

            for index, document in enumerate(batch, i + 1):
                try:
                    # Log progress
                    _logger.info(f'Submitting document {index}/{total}: {document.name}')

                    # Submit the document
                    document.action_submit_to_hacienda()
                    success_count += 1

                    # Commit after each success if continue_on_error is enabled
                    if self.continue_on_error:
                        self.env.cr.commit()

                    # Small delay between individual submissions
                    time.sleep(0.5)

                except Exception as e:
                    error_count += 1
                    error_msg = f'{document.name}: {str(e)}'
                    errors.append(error_msg)
                    _logger.error(f'Error submitting {document.name}: {e}')

                    if not self.continue_on_error:
                        # Rollback and raise error
                        self.env.cr.rollback()
                        raise UserError(_(
                            'Bulk submission stopped due to error:\n%s\n\n'
                            'Submitted: %d\nFailed: %d'
                        ) % (error_msg, success_count, error_count))

            # Delay between batches
            if i + batch_size < total and self.delay_between_batches > 0:
                _logger.info(f'Waiting {self.delay_between_batches} seconds before next batch...')
                time.sleep(self.delay_between_batches)

        # Show results
        message = _(
            'Bulk Submission Complete!\n\n'
            'Successfully submitted: %d\n'
            'Failed: %d\n'
            'Total processed: %d'
        ) % (success_count, error_count, total)

        if errors:
            message += '\n\nErrors:\n' + '\n'.join(errors[:10])
            if len(errors) > 10:
                message += f'\n... and {len(errors) - 10} more errors'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Submission Complete'),
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }


class BulkStatusCheckWizard(models.TransientModel):
    """
    Wizard for bulk checking status of multiple submitted e-invoice documents.

    Checks Hacienda status for multiple submitted documents in one operation.
    """
    _name = 'l10n_cr.bulk.status.check.wizard'
    _description = 'Bulk Check Status of E-Invoice Documents'

    document_ids = fields.Many2many(
        'l10n_cr.einvoice.document',
        string='Documents to Check',
        required=True,
    )

    total_documents = fields.Integer(
        string='Total Documents',
        compute='_compute_total_documents',
    )

    continue_on_error = fields.Boolean(
        string='Continue on Error',
        default=True,
        help='If checked, continue checking other documents even if one fails',
    )

    batch_size = fields.Integer(
        string='Batch Size',
        default=20,
        help='Number of documents to check per batch (rate limiting)',
    )

    delay_between_batches = fields.Integer(
        string='Delay Between Batches (seconds)',
        default=5,
        help='Delay in seconds between batches to avoid rate limiting',
    )

    @api.depends('document_ids')
    def _compute_total_documents(self):
        """Calculate total documents selected."""
        for record in self:
            record.total_documents = len(record.document_ids)

    @api.model
    def default_get(self, fields_list):
        """Pre-fill with selected documents from context."""
        res = super(BulkStatusCheckWizard, self).default_get(fields_list)

        # Get active IDs from context
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            # Filter only documents in 'submitted' state
            documents = self.env['l10n_cr.einvoice.document'].browse(active_ids)
            checkable_docs = documents.filtered(lambda d: d.state == 'submitted')
            res['document_ids'] = [(6, 0, checkable_docs.ids)]

        return res

    def action_check_status(self):
        """Execute bulk status check operation."""
        self.ensure_one()

        if not self.document_ids:
            raise UserError(_('No documents selected for status check.'))

        import time

        success_count = 0
        error_count = 0
        errors = []

        # Track status changes
        accepted_count = 0
        still_pending_count = 0

        total = len(self.document_ids)
        batch_size = self.batch_size or 20

        # Process in batches
        for batch_num, i in enumerate(range(0, total, batch_size), 1):
            batch = self.document_ids[i:i + batch_size]

            _logger.info(f'Processing batch {batch_num}: documents {i+1} to {i+len(batch)}')

            for index, document in enumerate(batch, i + 1):
                old_state = document.state

                try:
                    # Log progress
                    _logger.info(f'Checking status {index}/{total}: {document.name}')

                    # Check the status
                    document.action_check_status()
                    success_count += 1

                    # Track state changes
                    if document.state == 'accepted':
                        accepted_count += 1
                    elif document.state == 'submitted':
                        still_pending_count += 1

                    # Commit after each success if continue_on_error is enabled
                    if self.continue_on_error:
                        self.env.cr.commit()

                    # Small delay between individual checks
                    time.sleep(0.3)

                except Exception as e:
                    error_count += 1
                    error_msg = f'{document.name}: {str(e)}'
                    errors.append(error_msg)
                    _logger.error(f'Error checking status for {document.name}: {e}')

                    if not self.continue_on_error:
                        # Rollback and raise error
                        self.env.cr.rollback()
                        raise UserError(_(
                            'Bulk status check stopped due to error:\n%s\n\n'
                            'Checked: %d\nFailed: %d'
                        ) % (error_msg, success_count, error_count))

            # Delay between batches
            if i + batch_size < total and self.delay_between_batches > 0:
                _logger.info(f'Waiting {self.delay_between_batches} seconds before next batch...')
                time.sleep(self.delay_between_batches)

        # Show results
        message = _(
            'Bulk Status Check Complete!\n\n'
            'Successfully checked: %d\n'
            'Failed: %d\n'
            'Total processed: %d\n\n'
            'Status Updates:\n'
            'Accepted: %d\n'
            'Still Pending: %d'
        ) % (success_count, error_count, total, accepted_count, still_pending_count)

        if errors:
            message += '\n\nErrors:\n' + '\n'.join(errors[:10])
            if len(errors) > 10:
                message += f'\n... and {len(errors) - 10} more errors'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Status Check Complete'),
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }
