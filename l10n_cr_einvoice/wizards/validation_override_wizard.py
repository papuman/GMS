# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ValidationOverrideWizard(models.TransientModel):
    """
    Wizard to override validation errors for exceptional cases.

    This wizard allows authorized users (account managers or POS managers)
    to override validation errors with proper justification and full audit trail.

    Security:
    - Only users with 'account.group_account_manager' or 'point_of_sale.group_pos_manager'
      can use this wizard
    - Requires minimum 20-character reason
    - Logs all overrides in document chatter
    - Records user, timestamp, and reason in document fields
    - Increments validation rule trigger count for audit purposes
    """
    _name = 'l10n_cr.validation.override.wizard'
    _description = 'Validation Override Wizard'

    document_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='E-Invoice Document',
        required=True,
        readonly=True,
        help='The document with validation errors',
    )

    validation_errors = fields.Text(
        string='Validation Errors',
        required=True,
        readonly=True,
        help='List of validation errors that will be overridden',
    )

    override_reason = fields.Text(
        string='Override Justification',
        required=True,
        help=(
            'Provide a detailed justification for overriding these validation errors.\n'
            'Minimum 20 characters required.\n\n'
            'Example reasons:\n'
            '- Customer operates abroad, local CIIU not applicable\n'
            '- Emergency invoice during system migration\n'
            '- Customer email temporarily unavailable, will be updated'
        ),
    )

    reason_char_count = fields.Integer(
        string='Character Count',
        compute='_compute_reason_char_count',
        help='Number of characters in override reason (minimum 20 required)',
    )

    user_has_permission = fields.Boolean(
        string='User Has Permission',
        compute='_compute_user_has_permission',
        help='True if current user can approve overrides',
    )

    @api.depends('override_reason')
    def _compute_reason_char_count(self):
        """Compute character count for override reason."""
        for wizard in self:
            wizard.reason_char_count = len(wizard.override_reason or '')

    @api.depends()
    def _compute_user_has_permission(self):
        """Check if current user has permission to override validations."""
        for wizard in self:
            # Check if user has account manager or POS manager role
            has_account_manager = self.env.user.has_group('account.group_account_manager')
            has_pos_manager = self.env.user.has_group('point_of_sale.group_pos_manager')
            wizard.user_has_permission = has_account_manager or has_pos_manager

    @api.constrains('override_reason')
    def _check_override_reason(self):
        """Validate override reason meets minimum length requirement."""
        for wizard in self:
            if wizard.override_reason and len(wizard.override_reason.strip()) < 20:
                raise ValidationError(_(
                    'Override reason must be at least 20 characters long.\n'
                    'Current length: %d characters.\n\n'
                    'Please provide a detailed justification for this override.'
                ) % len(wizard.override_reason.strip()))

    def action_approve_override(self):
        """
        Approve validation override and update document.

        This method:
        1. Validates user permissions
        2. Validates reason length
        3. Updates document with override fields
        4. Logs override in chatter
        5. Increments validation rule trigger counts

        Returns:
            dict: Action to close wizard and refresh document form
        """
        self.ensure_one()

        # Verify user has permission
        if not self.user_has_permission:
            raise UserError(_(
                'You do not have permission to override validations.\n\n'
                'Required role: Account Manager or POS Manager'
            ))

        # Validate reason length
        reason = self.override_reason.strip()
        if len(reason) < 20:
            raise UserError(_(
                'Override reason must be at least 20 characters long.\n'
                'Current length: %d characters.'
            ) % len(reason))

        # Update document with override information
        override_data = {
            'validation_override': True,
            'validation_override_reason': reason,
            'validation_override_user_id': self.env.user.id,
            'validation_override_date': fields.Datetime.now(),
            'validation_errors': self.validation_errors,
        }

        self.document_id.write(override_data)

        # Log override in document chatter
        message = _(
            '<p><strong>Validation Override Approved</strong></p>'
            '<p><strong>Approved by:</strong> {user}</p>'
            '<p><strong>Date:</strong> {date}</p>'
            '<p><strong>Reason:</strong></p>'
            '<p>{reason}</p>'
            '<p><strong>Errors Overridden:</strong></p>'
            '<pre>{errors}</pre>'
        ).format(
            user=self.env.user.name,
            date=fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            reason=reason,
            errors=self.validation_errors,
        )

        self.document_id.message_post(
            body=message,
            subject=_('Validation Override'),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

        # Increment trigger count for affected validation rules (for audit)
        # This helps track which rules are frequently overridden
        try:
            validation_rules = self.env['l10n_cr.validation.rule'].search([
                ('active', '=', True),
                '|',
                ('document_type', '=', 'all'),
                ('document_type', '=', self.document_id.document_type),
            ])

            for rule in validation_rules:
                # Check if this rule's error message appears in validation_errors
                if rule.rule_name in self.validation_errors or rule.code in self.validation_errors:
                    rule.sudo().write({
                        'last_triggered': fields.Datetime.now(),
                        'trigger_count': rule.trigger_count + 1,
                    })
                    _logger.info(
                        f'Incremented trigger count for validation rule {rule.code} '
                        f'due to override on document {self.document_id.name}'
                    )

        except Exception as e:
            # Don't fail the override if rule audit fails
            _logger.warning(f'Failed to update validation rule audit trail: {str(e)}')

        # Log override for audit purposes
        _logger.warning(
            f'VALIDATION OVERRIDE: Document {self.document_id.name} '
            f'by user {self.env.user.name} (ID: {self.env.user.id}). '
            f'Reason: {reason}'
        )

        # Display success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Validation Override Approved'),
                'message': _('Validation errors have been overridden. You can now proceed with the document.'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close',
                },
            },
        }

    def action_cancel(self):
        """Cancel the wizard without making changes."""
        return {'type': 'ir.actions.act_window_close'}
