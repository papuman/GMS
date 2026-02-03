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
        string='Customer ID Number'
    )
    l10n_cr_customer_name = fields.Char(
        related='partner_id.name',
        string='Customer Name'
    )
    l10n_cr_customer_email = fields.Char(
        related='partner_id.email',
        string='Customer Email'
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

    # Odoo 19 POS order processing
    @api.model
    def _order_fields(self, ui_order):
        """
        Override to capture e-invoice flag from POS UI.
        Odoo 19 uses _order_fields instead of _process_order.
        """
        fields = super()._order_fields(ui_order)

        # Capture the e-invoice flag from UI (default: False)
        fields['l10n_cr_is_einvoice'] = ui_order.get('l10n_cr_is_einvoice', False)

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
        
        # Determine document type (FE or TE)
        # If client has ID -> FE, otherwise TE
        doc_type = 'TE'
        if self.partner_id and self.partner_id.vat:
             doc_type = 'FE'

        # Ensure we have a partner
        partner = self.partner_id or self.config_id.l10n_cr_default_partner_id
        if not partner:
             # Critical: cannot invoice without a partner
             raise UserError(_("Cannot generate e-invoice: No partner selected and no default configured."))

        # Create the document
        # TODO: Odoo 19 pos.order no longer has 'account_move' field.
        # This needs to be updated to use the correct Odoo 19 relationship
        # (e.g., account_move_id or the invoice created via pos order invoicing).
        vals = {
            'move_id': self.account_move.id if hasattr(self, 'account_move') and self.account_move else False,
            'pos_order_id': self.id,  # Link to POS order
            'document_type': doc_type,
            'company_id': self.company_id.id,
            'partner_id': partner.id,
        }
        
        # If no move exists yet (POS often creates moves async or in batch),
        # we might need to rely on the POS Order logic itself or create a stub.
        # For this implementation, we assume Immediate Invoicing is preferred 
        # or we accept that move_id might be empty until reconciliation.
        
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
                
        except Exception as e:
            # Log specific error to the document too
             einvoice.write({'error_message': str(e), 'state': 'error'})
             raise e # Re-raise to be caught by the caller to log to chatter

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
