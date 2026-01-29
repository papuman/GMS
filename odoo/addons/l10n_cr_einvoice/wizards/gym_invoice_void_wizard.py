# -*- coding: utf-8 -*-
"""
Gym Invoice Void Wizard for Costa Rica E-Invoicing

Production-ready wizard for voiding invoices and creating credit notes
in gym management context. Handles membership cancellations, refunds,
and automatic Hacienda submission.

Features:
- Void invoice and create matching Nota de Crédito
- Optional membership cancellation
- Multiple refund methods (cash, transfer, credit)
- Automatic Hacienda submission
- Email confirmation to member
- Comprehensive error handling
- Audit trail logging
"""
import logging
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class GymInvoiceVoidWizard(models.TransientModel):
    """
    Wizard for voiding gym invoices and creating credit notes.

    This wizard provides a complete workflow for:
    1. Voiding the original invoice
    2. Creating a matching Nota de Crédito
    3. Optionally canceling related memberships
    4. Processing refunds via multiple payment methods
    5. Submitting to Hacienda
    6. Sending confirmation email to member
    """
    _name = 'l10n_cr.gym.invoice.void.wizard'
    _description = 'Gym Invoice Void Wizard'

    # ============================================================
    # FIELDS
    # ============================================================

    # Basic Information
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice to Void',
        required=True,
        readonly=True,
        help='Original invoice to void',
    )

    invoice_number = fields.Char(
        string='Invoice Number',
        related='invoice_id.name',
        readonly=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Member',
        related='invoice_id.partner_id',
        readonly=True,
    )

    amount_total = fields.Monetary(
        string='Amount to Refund',
        related='invoice_id.amount_total',
        readonly=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='invoice_id.currency_id',
        readonly=True,
    )

    # E-Invoice Information
    einvoice_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='E-Invoice Document',
        related='invoice_id.l10n_cr_einvoice_id',
        readonly=True,
    )

    original_clave = fields.Char(
        string='Original Clave',
        related='einvoice_id.clave',
        readonly=True,
        help='Original 50-digit Hacienda key',
    )

    # Void Reason
    void_reason = fields.Selection([
        ('membership_cancel', 'Cancelación de membresía'),
        ('billing_error', 'Error en facturación'),
        ('customer_request', 'Devolución solicitada por cliente'),
        ('duplicate_invoice', 'Factura duplicada'),
        ('payment_failure', 'Fallo en procesamiento de pago'),
        ('service_not_provided', 'Servicio no prestado'),
        ('price_adjustment', 'Ajuste de precio'),
        ('other', 'Otro motivo'),
    ], string='Void Reason', required=True, default='customer_request',
       help='Reason for voiding the invoice')

    void_reason_notes = fields.Text(
        string='Additional Notes',
        help='Additional details about why the invoice is being voided',
    )

    # Membership Handling
    has_membership = fields.Boolean(
        string='Has Related Membership',
        compute='_compute_has_membership',
        help='Indicates if this invoice has related gym memberships',
    )

    # TODO: Re-enable when sale.subscription model is available in Odoo 19
    # Temporarily disabled to allow module installation without sale.subscription dependency
    # subscription_ids = fields.Many2many(
    #     'sale.subscription',
    #     string='Related Memberships',
    #     compute='_compute_has_membership',
    #     help='Gym memberships related to this invoice',
    # )

    cancel_membership = fields.Boolean(
        string='Cancel Membership',
        default=True,
        help='Cancel the related gym membership(s) when voiding this invoice',
    )

    membership_cancellation_reason = fields.Text(
        string='Membership Cancellation Reason',
        help='Reason for membership cancellation (required if canceling membership)',
    )

    # Refund Method
    refund_method = fields.Selection([
        ('cash', 'Efectivo'),
        ('transfer', 'Transferencia bancaria'),
        ('credit', 'Crédito para futuras compras'),
        ('card', 'Tarjeta de crédito/débito'),
        ('no_refund', 'Sin devolución (cortesía)'),
    ], string='Refund Method', required=True, default='cash',
       help='How the refund will be processed')

    refund_reference = fields.Char(
        string='Refund Reference',
        help='Reference number for the refund (e.g., transaction ID, check number)',
    )

    refund_bank_account = fields.Char(
        string='Bank Account',
        help='Customer bank account for transfer refunds',
    )

    refund_notes = fields.Text(
        string='Refund Notes',
        help='Additional notes about the refund process',
    )

    # Processing Options
    auto_submit_to_hacienda = fields.Boolean(
        string='Submit to Hacienda Automatically',
        default=True,
        help='Automatically submit credit note to Hacienda after creation',
    )

    send_email_notification = fields.Boolean(
        string='Send Email to Member',
        default=True,
        help='Send confirmation email to member with credit note details',
    )

    # Credit Note Information (populated after creation)
    credit_note_id = fields.Many2one(
        'account.move',
        string='Credit Note',
        readonly=True,
        help='Created credit note',
    )

    credit_note_einvoice_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='Credit Note E-Invoice',
        readonly=True,
        help='E-invoice document for the credit note',
    )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('done', 'Completed'),
        ('error', 'Error'),
    ], string='Status', default='draft', readonly=True)

    error_message = fields.Text(
        string='Error Details',
        readonly=True,
    )

    # ============================================================
    # COMPUTE METHODS
    # ============================================================

    @api.depends('invoice_id')
    def _compute_has_membership(self):
        """Check if invoice has related gym memberships."""
        # TODO: Re-enable when sale.subscription model is available in Odoo 19
        for wizard in self:
            # Temporarily disabled subscription detection
            wizard.has_membership = False
            # if wizard.invoice_id:
            #     # Find subscriptions related to this invoice
            #     subscriptions = self.env['sale.subscription'].search([
            #         '|',
            #         ('partner_id', '=', wizard.invoice_id.partner_id.id),
            #         ('invoice_ids', 'in', wizard.invoice_id.ids),
            #     ])
            #
            #     # Filter to active or recently active subscriptions
            #     active_subscriptions = subscriptions.filtered(
            #         lambda s: s.stage_category in ['progress', 'closed']
            #     )
            #
            #     wizard.has_membership = bool(active_subscriptions)
            #     wizard.subscription_ids = [(6, 0, active_subscriptions.ids)]
            # else:
            #     wizard.has_membership = False
            #     wizard.subscription_ids = [(5, 0, 0)]

    # ============================================================
    # VALIDATION
    # ============================================================

    @api.model
    def default_get(self, fields_list):
        """Pre-fill wizard with invoice from context."""
        res = super(GymInvoiceVoidWizard, self).default_get(fields_list)

        # Get invoice from context
        invoice_id = self.env.context.get('active_id')
        if invoice_id:
            res['invoice_id'] = invoice_id

        return res

    @api.constrains('cancel_membership', 'membership_cancellation_reason')
    def _check_membership_cancellation_reason(self):
        """Validate that cancellation reason is provided when canceling membership."""
        for wizard in self:
            if wizard.cancel_membership and wizard.has_membership:
                if not wizard.membership_cancellation_reason:
                    raise ValidationError(_(
                        'Please provide a reason for membership cancellation.'
                    ))

    @api.constrains('refund_method', 'refund_bank_account')
    def _check_refund_bank_account(self):
        """Validate that bank account is provided for transfer refunds."""
        for wizard in self:
            if wizard.refund_method == 'transfer' and not wizard.refund_bank_account:
                raise ValidationError(_(
                    'Bank account is required for transfer refunds.'
                ))

    def _validate_invoice(self):
        """Validate that invoice can be voided."""
        self.ensure_one()

        if not self.invoice_id:
            raise UserError(_('No invoice selected.'))

        if self.invoice_id.state != 'posted':
            raise UserError(_(
                'Only posted invoices can be voided.\n'
                'Current state: %s'
            ) % self.invoice_id.state)

        if self.invoice_id.move_type != 'out_invoice':
            raise UserError(_(
                'Only customer invoices can be voided with this wizard.\n'
                'Invoice type: %s'
            ) % self.invoice_id.move_type)

        # Check if invoice already has a credit note
        existing_reversals = self.env['account.move'].search([
            ('reversed_entry_id', '=', self.invoice_id.id),
            ('state', '=', 'posted'),
        ])

        if existing_reversals:
            raise UserError(_(
                'This invoice already has a credit note:\n%s\n\n'
                'If you need to create an additional credit note, '
                'please use the standard reversal process.'
            ) % ', '.join(existing_reversals.mapped('name')))

        # Check if e-invoice was accepted by Hacienda
        if self.invoice_id.l10n_cr_einvoice_id:
            einvoice = self.invoice_id.l10n_cr_einvoice_id
            if einvoice.state not in ['accepted', 'submitted']:
                _logger.warning(
                    f'Voiding invoice {self.invoice_id.name} with e-invoice '
                    f'in state: {einvoice.state}'
                )

        return True

    # ============================================================
    # ONCHANGE METHODS
    # ============================================================

    @api.onchange('void_reason')
    def _onchange_void_reason(self):
        """Auto-fill notes based on void reason."""
        if self.void_reason == 'membership_cancel' and self.has_membership:
            self.cancel_membership = True
            if not self.void_reason_notes:
                self.void_reason_notes = 'Cliente solicitó cancelación de membresía'
        elif self.void_reason == 'billing_error':
            if not self.void_reason_notes:
                self.void_reason_notes = 'Error en facturación, se procederá a emitir factura correcta'
        elif self.void_reason == 'duplicate_invoice':
            if not self.void_reason_notes:
                self.void_reason_notes = 'Factura duplicada por error del sistema'

    @api.onchange('refund_method')
    def _onchange_refund_method(self):
        """Clear fields not needed for selected refund method."""
        if self.refund_method != 'transfer':
            self.refund_bank_account = False

        if self.refund_method == 'no_refund':
            self.refund_notes = 'Cortesía - Sin devolución de dinero'

    # ============================================================
    # MAIN ACTIONS
    # ============================================================

    def action_void_invoice(self):
        """
        Main action: Void invoice and create credit note.

        Process:
        1. Validate invoice can be voided
        2. Create credit note (Nota de Crédito)
        3. Create e-invoice document for credit note
        4. Optionally cancel related memberships
        5. Process refund
        6. Submit to Hacienda (if enabled)
        7. Send email notification (if enabled)
        8. Log audit trail
        """
        self.ensure_one()

        # Validate
        self._validate_invoice()

        # Update state
        self.write({'state': 'processing'})

        try:
            # Step 1: Create credit note
            _logger.info(f'Creating credit note for invoice {self.invoice_id.name}')
            credit_note = self._create_credit_note()
            self.credit_note_id = credit_note.id

            # Step 2: Create e-invoice for credit note
            _logger.info(f'Creating e-invoice for credit note {credit_note.name}')
            credit_note_einvoice = self._create_credit_note_einvoice(credit_note)
            self.credit_note_einvoice_id = credit_note_einvoice.id

            # Step 3: Handle membership cancellation
            if self.cancel_membership and self.has_membership:
                _logger.info(f'Canceling memberships for invoice {self.invoice_id.name}')
                self._cancel_memberships()

            # Step 4: Process refund
            _logger.info(f'Processing refund via {self.refund_method}')
            self._process_refund(credit_note)

            # Step 5: Submit to Hacienda
            if self.auto_submit_to_hacienda:
                _logger.info(f'Submitting credit note to Hacienda')
                self._submit_to_hacienda(credit_note_einvoice)

            # Step 6: Send email notification
            if self.send_email_notification:
                _logger.info(f'Sending email notification to {self.partner_id.email}')
                self._send_email_notification()

            # Step 7: Log audit trail
            self._log_void_action()

            # Update state
            self.write({'state': 'done'})

            # Commit transaction
            self.env.cr.commit()

            # Return success message with credit note
            return self._show_success_message()

        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error voiding invoice {self.invoice_id.name}: {error_msg}', exc_info=True)

            self.write({
                'state': 'error',
                'error_message': error_msg,
            })

            # Rollback
            self.env.cr.rollback()

            raise UserError(_(
                'Error voiding invoice:\n\n%s\n\n'
                'Please review the error and try again, or contact support.'
            ) % error_msg)

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def _create_credit_note(self):
        """Create credit note (reversal) for the invoice."""
        self.ensure_one()

        # Prepare reversal values
        reversal_date = fields.Date.today()

        # Build reason text
        reason_text = dict(self._fields['void_reason'].selection).get(self.void_reason)
        if self.void_reason_notes:
            reason_text += f': {self.void_reason_notes}'

        # Create reversal using Odoo's built-in method
        reversal_wizard = self.env['account.move.reversal'].with_context(
            active_model='account.move',
            active_ids=self.invoice_id.ids,
        ).create({
            'date': reversal_date,
            'reason': reason_text,
            'journal_id': self.invoice_id.journal_id.id,
        })

        # Execute reversal
        reversal_action = reversal_wizard.reverse_moves()

        # Get created credit note
        credit_note = self.env['account.move'].browse(reversal_action['res_id'])

        # Copy payment method from original invoice
        if self.invoice_id.l10n_cr_payment_method_id:
            credit_note.write({
                'l10n_cr_payment_method_id': self.invoice_id.l10n_cr_payment_method_id.id,
            })

        _logger.info(f'Created credit note {credit_note.name} for invoice {self.invoice_id.name}')

        return credit_note

    def _create_credit_note_einvoice(self, credit_note):
        """Create e-invoice document for credit note."""
        self.ensure_one()

        # Check if credit note already has e-invoice
        if credit_note.l10n_cr_einvoice_id:
            return credit_note.l10n_cr_einvoice_id

        # Create e-invoice document
        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': credit_note.id,
            'document_type': 'NC',  # Nota de Crédito
            'company_id': credit_note.company_id.id,
        })

        credit_note.l10n_cr_einvoice_id = einvoice.id

        _logger.info(f'Created e-invoice document {einvoice.name} for credit note {credit_note.name}')

        return einvoice

    def _cancel_memberships(self):
        """Cancel related gym memberships."""
        # TODO: Re-enable when sale.subscription model is available in Odoo 19
        self.ensure_one()

        # Temporarily disabled - subscription cancellation not available
        _logger.info('Membership cancellation temporarily disabled (sale.subscription not available)')
        return

        # if not self.subscription_ids:
        #     return
        #
        # cancellation_reason = self.membership_cancellation_reason or self.void_reason_notes or \
        #                      'Cancelado por anulación de factura'
        #
        # for subscription in self.subscription_ids:
        #     try:
        #         # Set subscription to close
        #         subscription.write({
        #             'to_renew': False,
        #             'description': f'{subscription.description or ""}\n\n'
        #                          f'CANCELADO: {cancellation_reason}'
        #         })
        #
        #         # Close the subscription
        #         if hasattr(subscription, 'set_close'):
        #             subscription.set_close()
        #
        #         _logger.info(f'Canceled membership {subscription.code or subscription.id}')
        #
        #         # Log note on subscription
        #         subscription.message_post(
        #             body=_(
        #                 '<p><strong>Membresía Cancelada</strong></p>'
        #                 '<p>Razón: %s</p>'
        #                 '<p>Factura anulada: %s</p>'
        #                 '<p>Nota de crédito: %s</p>'
        #             ) % (cancellation_reason, self.invoice_id.name,
        #                  self.credit_note_id.name if self.credit_note_id else 'Pendiente'),
        #             subject='Membresía Cancelada',
        #         )
        #
        #     except Exception as e:
        #         _logger.error(f'Error canceling subscription {subscription.id}: {e}')
        #         # Don't fail the whole process if membership cancellation fails
        #         continue

    def _process_refund(self, credit_note):
        """Process the refund according to selected method."""
        self.ensure_one()

        refund_info = {
            'invoice_id': self.invoice_id.id,
            'credit_note_id': credit_note.id,
            'amount': self.amount_total,
            'method': self.refund_method,
            'reference': self.refund_reference,
            'bank_account': self.refund_bank_account,
            'notes': self.refund_notes,
            'processed_date': fields.Datetime.now(),
        }

        # Add note to credit note with refund details
        refund_method_name = dict(self._fields['refund_method'].selection).get(self.refund_method)

        message_body = _(
            '<p><strong>Información de Devolución</strong></p>'
            '<ul>'
            '<li><strong>Método:</strong> %s</li>'
            '<li><strong>Monto:</strong> %s %s</li>'
        ) % (refund_method_name, self.currency_id.symbol, self.amount_total)

        if self.refund_reference:
            message_body += f'<li><strong>Referencia:</strong> {self.refund_reference}</li>'

        if self.refund_bank_account:
            message_body += f'<li><strong>Cuenta Bancaria:</strong> {self.refund_bank_account}</li>'

        if self.refund_notes:
            message_body += f'<li><strong>Notas:</strong> {self.refund_notes}</li>'

        message_body += '</ul>'

        credit_note.message_post(
            body=message_body,
            subject='Información de Devolución',
        )

        _logger.info(f'Processed refund via {self.refund_method} for {self.amount_total}')

    def _submit_to_hacienda(self, einvoice):
        """Submit credit note to Hacienda."""
        self.ensure_one()

        try:
            # Generate XML
            if einvoice.state == 'draft':
                einvoice.action_generate_xml()

            # Sign XML
            if einvoice.state == 'generated':
                einvoice.action_sign_xml()

            # Submit to Hacienda
            if einvoice.state == 'signed':
                einvoice.action_submit_to_hacienda()

            _logger.info(f'Submitted credit note e-invoice {einvoice.name} to Hacienda')

        except Exception as e:
            _logger.error(f'Error submitting to Hacienda: {e}')
            # Don't fail the whole process if submission fails
            # User can manually retry submission later
            raise

    def _send_email_notification(self):
        """Send email notification to member."""
        self.ensure_one()

        if not self.partner_id.email:
            _logger.warning(f'Cannot send email: Member {self.partner_id.name} has no email')
            return

        try:
            # Get void confirmation email template
            template = self.env.ref('l10n_cr_einvoice.email_template_void_confirmation',
                                   raise_if_not_found=False)

            if not template:
                _logger.warning('Void confirmation email template not found')
                return

            # Send email
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.partner_id.email,
                }
            )

            _logger.info(f'Sent void confirmation email to {self.partner_id.email}')

        except Exception as e:
            _logger.error(f'Error sending email: {e}')
            # Don't fail the whole process if email fails

    def _log_void_action(self):
        """Log void action in audit trail."""
        self.ensure_one()

        # Log on original invoice
        self.invoice_id.message_post(
            body=_(
                '<p><strong>Factura Anulada</strong></p>'
                '<p><strong>Razón:</strong> %s</p>'
                '<p><strong>Nota de Crédito:</strong> %s</p>'
                '<p><strong>Método de Devolución:</strong> %s</p>'
                '<p><strong>Procesado por:</strong> %s</p>'
                '<p><strong>Fecha:</strong> %s</p>'
            ) % (
                dict(self._fields['void_reason'].selection).get(self.void_reason),
                self.credit_note_id.name if self.credit_note_id else 'N/A',
                dict(self._fields['refund_method'].selection).get(self.refund_method),
                self.env.user.name,
                fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ),
            subject='Factura Anulada',
        )

        # Log on credit note
        if self.credit_note_id:
            self.credit_note_id.message_post(
                body=_(
                    '<p><strong>Nota de Crédito Creada</strong></p>'
                    '<p><strong>Factura Original:</strong> %s</p>'
                    '<p><strong>Razón:</strong> %s</p>'
                ) % (
                    self.invoice_id.name,
                    dict(self._fields['void_reason'].selection).get(self.void_reason),
                ),
                subject='Nota de Crédito',
            )

    def _show_success_message(self):
        """Show success message and open credit note."""
        self.ensure_one()

        message = _(
            'Factura Anulada Exitosamente\n\n'
            'Factura Original: %s\n'
            'Nota de Crédito: %s\n'
            'Monto: %s %s\n'
            'Método de Devolución: %s\n'
        ) % (
            self.invoice_id.name,
            self.credit_note_id.name,
            self.currency_id.symbol,
            self.amount_total,
            dict(self._fields['refund_method'].selection).get(self.refund_method),
        )

        # TODO: Re-enable when sale.subscription model is available in Odoo 19
        # if self.cancel_membership:
        #     message += _('\nMembresías canceladas: %d') % len(self.subscription_ids)

        if self.auto_submit_to_hacienda:
            message += _('\nEstado Hacienda: %s') % (
                self.credit_note_einvoice_id.state if self.credit_note_einvoice_id else 'N/A'
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Factura Anulada'),
                'message': message,
                'type': 'success',
                'sticky': True,
                'next': {
                    'type': 'ir.actions.act_window',
                    'name': _('Nota de Crédito'),
                    'res_model': 'account.move',
                    'res_id': self.credit_note_id.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            }
        }

    # ============================================================
    # ADDITIONAL ACTIONS
    # ============================================================

    def action_cancel(self):
        """Cancel wizard without voiding invoice."""
        return {'type': 'ir.actions.act_window_close'}

    def action_view_credit_note(self):
        """Open credit note form."""
        self.ensure_one()

        if not self.credit_note_id:
            raise UserError(_('No credit note has been created yet.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Credit Note'),
            'res_model': 'account.move',
            'res_id': self.credit_note_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_einvoice(self):
        """Open credit note e-invoice."""
        self.ensure_one()

        if not self.credit_note_einvoice_id:
            raise UserError(_('No e-invoice document has been created yet.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Credit Note E-Invoice'),
            'res_model': 'l10n_cr.einvoice.document',
            'res_id': self.credit_note_einvoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
