# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    # E-Invoice Status
    l10n_cr_is_einvoice = fields.Boolean(
        string='Is Electronic Invoice',
        default=False,
        copy=False
    )

    einvoice_type = fields.Selection(
        [('FE', 'Factura Electrónica'), ('TE', 'Tiquete Electrónico')],
        string='E-Invoice Type',
        default='TE',
        copy=False
    )

    l10n_cr_einvoice_document_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='Electronic Invoice Document',
        readonly=True,
        copy=False
    )

    # Fields required by views/pos_order_views.xml
    l10n_cr_hacienda_status = fields.Selection(
        related='l10n_cr_einvoice_document_id.state',
        string='Hacienda Status',
        store=True
    )
    
    l10n_cr_hacienda_error = fields.Text(
        related='l10n_cr_einvoice_document_id.error_message',
        string='Hacienda Error'
    )
    
    l10n_cr_clave = fields.Char(
        related='l10n_cr_einvoice_document_id.clave',
        string='Clave'
    )
    
    l10n_cr_consecutive = fields.Char(
        related='l10n_cr_einvoice_document_id.name',
        string='Consecutive'
    )

    l10n_cr_offline_queue = fields.Boolean(
        string='Offline Queue',
        default=False,
        help="Indicates if the invoice is queued for offline processing"
    )

    # Customer Data snapshot (for the invoice)
    # TODO: Fix related field - l10n_cr_ident_type_id doesn't exist in res.partner
    # l10n_cr_customer_id_type = fields.Selection(
    #     related='partner_id.l10n_cr_ident_type_id.code',
    #     string='Customer ID Type'
    # )
    l10n_cr_customer_id_number = fields.Char(
        related='partner_id.vat',
        string='Customer ID Number',
        store=True,
    )
    l10n_cr_customer_name = fields.Char(
        related='partner_id.name',
        string='Customer Name',
        store=True,
    )
    l10n_cr_customer_email = fields.Char(
        related='partner_id.email',
        string='Customer Email',
        store=True,
    )
    
    # QR Code for the view
    l10n_cr_qr_code = fields.Binary(
        string="QR Code",
        compute='_compute_l10n_cr_qr_code'
    )

    def _compute_l10n_cr_qr_code(self):
        for order in self:
            if order.l10n_cr_einvoice_document_id:
                order.l10n_cr_qr_code = order.l10n_cr_einvoice_document_id._get_qr_code_image()
            else:
                order.l10n_cr_qr_code = False

    # NOTE: In Odoo 19, _process_order() passes serialized data directly to create().
    # _order_fields() is NOT called by the base Odoo 19 flow. This override is kept
    # as a safety net in case any other module calls it, but the primary path for
    # getting l10n_cr_is_einvoice/einvoice_type to the server is serializeForORM() →
    # _process_order() → create().
    @api.model
    def _order_fields(self, ui_order):
        """Capture e-invoice flag from POS UI (safety net)."""
        fields = super()._order_fields(ui_order)

        # Capture the e-invoice flag from UI (default: False)
        fields['l10n_cr_is_einvoice'] = ui_order.get('l10n_cr_is_einvoice', False)
        fields['einvoice_type'] = ui_order.get('einvoice_type', 'TE')

        # NOTE: Do NOT set l10n_cr_customer_id_number/name/email here.
        # These are related+store=True fields that auto-populate from partner_id.
        # Writing to them in _order_fields would propagate back to the partner
        # record, corrupting partner data instead of snapshotting it.

        return fields

    @api.model_create_multi
    def create(self, vals_list):
        """Override to generate e-invoice after order creation if requested."""
        orders = super().create(vals_list)

        # Generate e-invoice for orders that have the flag set
        for order in orders:
            if order.state == 'paid':  # Only for paid orders
                order._generate_einvoice_if_requested()

        return orders

    def write(self, vals):
        result = super().write(vals)
        if vals.get('state') == 'paid':
            for order in self:
                if not order.l10n_cr_einvoice_document_id:
                    order._generate_einvoice_if_requested()
        return result

    def _generate_einvoice_if_requested(self):
        """
        Generate e-invoice only if explicitly requested.
        Called after order is created and paid.
        """
        self.ensure_one()

        # CRITICAL: Only generate if flag is True AND config enables it
        if self.l10n_cr_is_einvoice and self.config_id.l10n_cr_enable_einvoice:
            try:
                self._generate_cr_einvoice()
            except Exception as e:
                self.message_post(body=f"Electronic Invoice generation failed: {str(e)}")

    def _generate_cr_einvoice(self):
        """Generate and submit the electronic invoice."""
        self.ensure_one()

        if self.l10n_cr_einvoice_document_id:
            raise UserError(_("This order already has an electronic invoice."))

        # Ensure we have a partner
        partner = self.partner_id or self.config_id.l10n_cr_default_partner_id
        doc_type = self.einvoice_type or 'TE'
        if not partner and doc_type == 'FE':
            raise UserError(_("Cannot generate Factura Electrónica: No customer selected and no default configured."))
        if not partner and doc_type == 'TE':
            # TE can proceed without partner — use company as minimal data
            partner = self.company_id.partner_id

        # Get the billing partner (corporate parent if applicable)
        invoice_partner = partner._get_invoice_partner()

        # Determine document type (FE or TE)
        doc_type = self.einvoice_type or 'TE'
        # If FE was selected but partner has no VAT, downgrade to TE
        if doc_type == 'FE' and not invoice_partner.vat:
            doc_type = 'TE'

        # Create e-invoice document linked to POS order
        # Note: account_move is created later during invoicing/reconciliation
        # The einvoice document works from POS order data directly
        vals = {
            'pos_order_id': self.id,
            'document_type': doc_type,
            'company_id': self.company_id.id,
            'partner_id': invoice_partner.id,
        }

        einvoice = self.env['l10n_cr.einvoice.document'].create(vals)

        self.l10n_cr_einvoice_document_id = einvoice.id

        # Trigger generation flow
        try:
            einvoice.action_generate_xml()
            einvoice.action_sign_xml()

            # Check offline mode
            if not self.config_id.l10n_cr_offline_mode:
                einvoice.action_submit_to_hacienda()
            else:
                self.l10n_cr_offline_queue = True
                self.env['l10n_cr.pos.offline.queue'].create({
                    'pos_order_id': self.id,
                    'einvoice_document_id': einvoice.id,
                    'state': 'pending',
                })

        except Exception as e:
            # Log specific error to the document too
            einvoice.write({'error_message': str(e), 'state': 'error'})
            raise  # Re-raise to be caught by the caller to log to chatter

    def action_l10n_cr_resend_email(self):
        self.ensure_one()
        if self.l10n_cr_einvoice_document_id:
            return self.l10n_cr_einvoice_document_id.action_send_email()
            
    def action_l10n_cr_check_status(self):
        self.ensure_one()
        if self.l10n_cr_einvoice_document_id:
            return self.l10n_cr_einvoice_document_id.action_check_status()
            
    def action_l10n_cr_resubmit_hacienda(self):
        self.ensure_one()
        if self.l10n_cr_einvoice_document_id:
            return self.l10n_cr_einvoice_document_id.action_submit_to_hacienda()

    def get_einvoice_feedback(self):
        """Return e-invoice notification data for POS ReceiptScreen.

        Called via RPC from ReceiptScreen after order sync to show
        a toast notification about the Hacienda submission result.

        Returns:
            dict: {type: 'success'|'danger'|'warning'|'info', message: str}
                  or empty dict if no e-invoice on this order.
        """
        self.ensure_one()
        if not self.l10n_cr_is_einvoice or not self.l10n_cr_einvoice_document_id:
            return {}

        doc = self.l10n_cr_einvoice_document_id
        doc_label = 'Factura Electrónica' if doc.document_type == 'FE' else 'Tiquete Electrónico'

        if doc.state == 'accepted':
            return {'type': 'success', 'message': '%s aceptada por Hacienda' % doc_label}
        elif doc.state == 'rejected':
            reason = self._map_hacienda_error_for_pos(doc.error_message or '')
            return {'type': 'danger', 'message': '%s rechazada: %s' % (doc_label, reason)}
        elif doc.state == 'submitted':
            return {'type': 'info', 'message': '%s enviada a Hacienda' % doc_label}
        elif doc.state == 'signed':
            if self.l10n_cr_offline_queue:
                return {'type': 'warning', 'message': '%s en cola offline - se enviará cuando haya conexión' % doc_label}
            return {'type': 'info', 'message': '%s firmada, pendiente de envío' % doc_label}
        elif doc.state == 'error':
            reason = self._map_hacienda_error_for_pos(doc.error_message or '')
            return {'type': 'warning', 'message': 'Error enviando %s: %s' % (doc_label, reason)}
        return {}

    def _map_hacienda_error_for_pos(self, error_message):
        """Map Hacienda technical errors to plain-language Spanish for POS cashiers.

        Cashiers can't fix technical issues, so we translate errors into
        actionable messages or generic "contact admin" fallbacks.
        """
        msg = (error_message or '').lower()

        MAPPING = [
            ('identificacion', 'Falta cédula del cliente'),
            ('receptor', 'Datos del cliente incompletos'),
            ('duplicad', 'Factura duplicada'),
            ('certificado', 'Certificado vencido - contacte administrador'),
            ('firma', 'Error de firma - contacte administrador'),
            ('xml', 'Error interno - contacte administrador'),
            ('esquema', 'Error interno - contacte administrador'),
            ('no disponible', 'Hacienda no disponible - se reintentará'),
            ('timeout', 'Hacienda no disponible - se reintentará'),
            ('connection', 'Sin conexión a Hacienda - se reintentará'),
        ]

        for keyword, friendly_msg in MAPPING:
            if keyword in msg:
                return friendly_msg

        # Fallback: truncate for POS display
        if error_message and len(error_message) > 80:
            return error_message[:77] + '...'
        return error_message or 'Error desconocido'

    def action_generate_einvoice_retroactive(self, partner_id=None, partner_vat=None, partner_email=None):
        """
        Generate e-invoice after order completion.
        Common scenario: Customer completes purchase, then returns asking for invoice.

        Args:
            partner_id: Optional partner ID to set
            partner_vat: Optional VAT number if creating new partner
            partner_email: Optional email for delivery

        Returns:
            dict: Action to reprint receipt with QR code

        Raises:
            UserError: If order is not paid or already has e-invoice
        """
        self.ensure_one()

        # Validation: Order must be paid
        if self.state != 'paid':
            raise UserError(_("Can only generate e-invoice for paid orders"))

        # Validation: Cannot have existing e-invoice
        if self.l10n_cr_einvoice_document_id:
            raise UserError(_("This order already has an e-invoice"))

        # Set partner if provided
        if partner_id:
            self.partner_id = partner_id

        # Validate partner exists for FE
        if not self.partner_id:
            raise UserError(_("Partner is required to generate e-invoice"))

        # Enable e-invoice flag
        self.l10n_cr_is_einvoice = True

        # Generate e-invoice using existing order data
        try:
            self._generate_cr_einvoice()
        except Exception as e:
            # Reset flag on failure
            self.l10n_cr_is_einvoice = False
            raise UserError(_("Failed to generate e-invoice: %s") % str(e))

        # Return action to reprint receipt
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('E-Invoice Generated'),
                'message': _('Electronic invoice created successfully. Receipt can be reprinted with QR code.'),
                'type': 'success',
                'sticky': False,
            }
        }
