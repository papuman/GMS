# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Electronic Invoice Fields
    l10n_cr_einvoice_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='Electronic Invoice',
        readonly=True,
        copy=False,
    )

    l10n_cr_einvoice_state = fields.Selection(
        related='l10n_cr_einvoice_id.state',
        string='E-Invoice Status',
        store=True,
    )

    l10n_cr_clave = fields.Char(
        related='l10n_cr_einvoice_id.clave',
        string='Hacienda Key',
        store=True,
        copy=False,
    )

    l10n_cr_requires_einvoice = fields.Boolean(
        string='Requires Electronic Invoice',
        compute='_compute_requires_einvoice',
        store=True,
    )

    # XML Import Batch (Phase 3)
    l10n_cr_import_batch_id = fields.Many2one(
        'l10n_cr.einvoice.import.batch',
        string='Import Batch',
        readonly=True,
        copy=False,
        help='Batch from which this invoice was imported via XML',
    )

    # Payment Method Fields (Phase 1A)
    l10n_cr_payment_method_id = fields.Many2one(
        'l10n_cr.payment.method',
        string='Payment Method (CR)',
        help='Costa Rica payment method for electronic invoicing (required by Hacienda)',
        copy=False,
        tracking=True,
    )

    l10n_cr_payment_transaction_id = fields.Char(
        string='Transaction ID',
        size=50,
        help='Transaction ID for SINPE Móvil or card payments',
        copy=False,
        tracking=True,
    )

    # Debit Note Origin (Phase 7)
    debit_origin_id = fields.Many2one(
        'account.move',
        string='Origin Invoice (for Debit Notes)',
        help='Original invoice being debited (for Nota de Débito)',
        copy=False,
        domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('company_id', '=', company_id)]",
    )

    @api.depends('move_type', 'country_code', 'company_id')
    def _compute_requires_einvoice(self):
        """Determine if this invoice requires electronic invoicing."""
        for move in self:
            # Require e-invoice for Costa Rica customer invoices
            move.l10n_cr_requires_einvoice = (
                move.move_type in ['out_invoice', 'out_refund']
                and move.country_code == 'CR'
                and move.company_id.country_id.code == 'CR'
            )

    # Mapping from Odoo payment.method codes to Hacienda l10n_cr.payment.method codes.
    # Keys: (provider_code or None, payment_method_code) -> Hacienda code
    # provider_code=None means any provider.
    PAYMENT_METHOD_MAPPING = {
        # TiloPay-specific: bank_transfer from TiloPay is always SINPE Movil
        ('tilopay', 'bank_transfer'): '06',  # SINPE Movil
        ('tilopay', 'card'): '02',           # Tarjeta
        # Generic mappings (any provider)
        (None, 'card'): '02',                # Tarjeta
        (None, 'bank_transfer'): '04',       # Transferencia bancaria
    }

    @api.model
    def _get_default_payment_method(self):
        """Get default payment method (01 - Efectivo)."""
        return self.env.ref('l10n_cr_einvoice.payment_method_efectivo', raise_if_not_found=False)

    @api.onchange('l10n_cr_payment_method_id')
    def _onchange_payment_method(self):
        """Clear transaction ID if payment method doesn't require it."""
        if self.l10n_cr_payment_method_id and not self.l10n_cr_payment_method_id.requires_transaction_id:
            self.l10n_cr_payment_transaction_id = False

    def _detect_payment_method_from_transactions(self):
        """Detect the Costa Rica payment method from linked payment transactions.

        Maps Odoo payment.method codes (e.g. 'card', 'bank_transfer') to
        Hacienda l10n_cr.payment.method codes (e.g. '02', '06').

        Special handling for TiloPay: 'bank_transfer' from TiloPay is SINPE Movil
        (code '06'), while from other providers it maps to Transferencia (code '04').

        Returns:
            l10n_cr.payment.method record or False if no mapping found
        """
        self.ensure_one()

        # Check if account_payment module is installed (provides transaction_ids)
        if not hasattr(self, 'transaction_ids'):
            return False

        # Get the most recent done transaction linked to this invoice
        done_txs = self.transaction_ids.filtered(lambda tx: tx.state == 'done')
        if not done_txs:
            return False

        # Use the last completed transaction
        tx = done_txs.sorted('last_state_change', reverse=True)[:1]
        if not tx:
            return False

        provider_code = tx.provider_code or ''
        method_code = tx.payment_method_code or ''

        if not method_code:
            return False

        # Look up the Hacienda payment method code using the mapping
        # Try provider-specific mapping first, then generic
        hacienda_code = self.PAYMENT_METHOD_MAPPING.get(
            (provider_code, method_code)
        ) or self.PAYMENT_METHOD_MAPPING.get(
            (None, method_code)
        )

        if not hacienda_code:
            _logger.info(
                'No Hacienda payment method mapping for provider=%s, method=%s on invoice %s',
                provider_code, method_code, self.name
            )
            return False

        # Find the l10n_cr.payment.method record by Hacienda code
        cr_payment_method = self.env['l10n_cr.payment.method'].search(
            [('code', '=', hacienda_code), ('active', '=', True)], limit=1
        )

        if cr_payment_method:
            _logger.info(
                'Detected payment method "%s" (code %s) from transaction %s '
                '(provider: %s, method: %s) for invoice %s',
                cr_payment_method.name, hacienda_code,
                tx.reference, provider_code, method_code, self.name
            )

            # Also store the provider reference as transaction ID if applicable
            if tx.provider_reference and not self.l10n_cr_payment_transaction_id:
                self.l10n_cr_payment_transaction_id = tx.provider_reference
                _logger.info(
                    'Auto-set transaction ID "%s" from payment provider on invoice %s',
                    tx.provider_reference, self.name
                )

        return cr_payment_method

    def _validate_payment_method_transaction_id(self):
        """Validate that SINPE Movil has transaction ID.

        If no payment method is set, first tries to detect it from linked
        payment transactions (e.g. TiloPay SINPE/Card), then falls back
        to the default (01 - Efectivo).
        """
        self.ensure_one()

        if not self.l10n_cr_requires_einvoice:
            return True

        # If no payment method selected, try to detect from payment transactions
        if not self.l10n_cr_payment_method_id:
            detected_method = self._detect_payment_method_from_transactions()
            if detected_method:
                self.l10n_cr_payment_method_id = detected_method
            else:
                # Fall back to default (Efectivo)
                default_method = self._get_default_payment_method()
                if default_method:
                    self.l10n_cr_payment_method_id = default_method
                    _logger.info(
                        'Auto-assigned default payment method "01-Efectivo" to invoice %s',
                        self.name
                    )
                else:
                    raise UserError(_(
                        'Payment method is required for Costa Rica electronic invoicing.\n'
                        'Please select a payment method before posting this invoice.'
                    ))

        # Validate SINPE Movil requires transaction ID
        if self.l10n_cr_payment_method_id.requires_transaction_id:
            if not self.l10n_cr_payment_transaction_id:
                raise UserError(_(
                    'Transaction ID is required for payment method "%s".\n\n'
                    'Please enter the transaction ID provided by the payment system.'
                ) % self.l10n_cr_payment_method_id.name)

        return True

    def action_post(self):
        """Override post to validate payment method and auto-generate e-invoice for CR."""
        # Validate payment method for CR invoices BEFORE posting
        for move in self:
            if move.l10n_cr_requires_einvoice:
                move._validate_payment_method_transaction_id()

        res = super(AccountMove, self).action_post()

        for move in self:
            if move.l10n_cr_requires_einvoice and not move.l10n_cr_einvoice_id:
                # Auto-create e-invoice document
                if move.company_id.l10n_cr_auto_generate_einvoice:
                    try:
                        move._create_einvoice_document()
                    except Exception as e:
                        # Log error but don't block invoice posting
                        _logger.error(f'Failed to auto-create e-invoice for {move.name}: {str(e)}')

        return res

    def action_create_einvoice(self):
        """Manual action to create electronic invoice document."""
        self.ensure_one()

        if not self.l10n_cr_requires_einvoice:
            raise UserError(_('This invoice does not require electronic invoicing.'))

        if self.l10n_cr_einvoice_id:
            raise UserError(_('Electronic invoice already exists for this document.'))

        if self.state != 'posted':
            raise UserError(_('Invoice must be posted before creating electronic invoice.'))

        # Validate payment method
        self._validate_payment_method_transaction_id()

        self._create_einvoice_document()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Electronic Invoice'),
            'res_model': 'l10n_cr.einvoice.document',
            'res_id': self.l10n_cr_einvoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_einvoice_document(self):
        """Create the electronic invoice document."""
        self.ensure_one()

        # Get the billing partner (corporate parent if applicable)
        invoice_partner = self.partner_id._get_invoice_partner()

        # Determine document type
        doc_type = self._get_einvoice_document_type()

        # Create e-invoice document
        # The partner_id in einvoice_document will be used for Receptor in XML
        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': self.id,
            'document_type': doc_type,
            'company_id': self.company_id.id,
            'partner_id': invoice_partner.id,  # Bill to corporate parent if applicable
        })

        self.l10n_cr_einvoice_id = einvoice.id

        _logger.info(
            f'Created e-invoice document {einvoice.name} for invoice {self.name}. '
            f'Billing partner: {invoice_partner.name} (ID: {invoice_partner.id})'
        )

        return einvoice

    def _get_einvoice_document_type(self):
        """Determine the electronic document type based on invoice type."""
        self.ensure_one()

        if self.move_type == 'out_invoice':
            # Check if it's a simplified invoice (tiquete)
            if self.amount_total <= 1000000:  # Below 1M CRC threshold
                return 'TE'
            return 'FE'
        elif self.move_type == 'out_refund':
            return 'NC'
        else:
            return 'FE'

    def action_generate_and_send_einvoice(self):
        """Complete workflow: generate XML, sign, submit, and email."""
        self.ensure_one()

        if not self.l10n_cr_einvoice_id:
            self._create_einvoice_document()

        einvoice = self.l10n_cr_einvoice_id

        # Generate XML
        if einvoice.state == 'draft':
            einvoice.action_generate_xml()

        # Sign XML
        if einvoice.state == 'generated':
            einvoice.action_sign_xml()

        # Submit to Hacienda
        if einvoice.state == 'signed':
            einvoice.action_submit_to_hacienda()

        # Send email if accepted
        if einvoice.state == 'accepted' and not einvoice.email_sent:
            self._send_einvoice_email()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Electronic Invoice'),
            'res_model': 'l10n_cr.einvoice.document',
            'res_id': einvoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _send_einvoice_email(self):
        """Send email with electronic invoice attachments."""
        self.ensure_one()

        if not self.l10n_cr_einvoice_id:
            return

        einvoice = self.l10n_cr_einvoice_id

        # Delegate to the einvoice document's own send method
        # which handles PDF + XML attachments correctly
        if einvoice.state == 'accepted':
            einvoice.action_send_email()
            _logger.info(f'Sent e-invoice email for {self.name}')
