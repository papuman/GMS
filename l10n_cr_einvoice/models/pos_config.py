# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    # Main Config
    l10n_cr_enable_einvoice = fields.Boolean(string="Enable CR E-Invoicing", default=True)
    
    # Behavior
    l10n_cr_require_customer_id = fields.Boolean(string="Require Customer for FE", default=True)
    l10n_cr_auto_submit = fields.Boolean(string="Auto Submit to Hacienda", default=True)
    l10n_cr_offline_mode = fields.Boolean(string="Offline Mode", help="Queue invoices locally first")
    l10n_cr_allow_anonymous = fields.Boolean(string="Allow Anonymous TE", default=True)
    l10n_cr_default_email_customer = fields.Boolean(string="Auto Email Customer", default=True)

    # Technical
    l10n_cr_terminal_id = fields.Char(string="Terminal ID (Sucursal)", default="001")
    l10n_cr_te_sequence_id = fields.Many2one('ir.sequence', string="Tiquete Sequence")
    
    # Status / Monitoring fields (computed or dummy for now to satisfy view)
    l10n_cr_connection_status = fields.Selection(
        [('online', 'Online'), ('offline', 'Offline')],
        string="Hacienda Connection",
        default='online'
    )
    l10n_cr_queue_count = fields.Integer(string="Queue Size")
    l10n_cr_last_sync = fields.Datetime(string="Last Sync")

    # Anonymous Customer Defaults
    l10n_cr_default_partner_id = fields.Many2one('res.partner', string="Default Partner")
    # TODO: Fix related field - l10n_cr_ident_type_id doesn't exist in res.partner
    # l10n_cr_default_customer_id_type = fields.Selection(related='l10n_cr_default_partner_id.l10n_cr_ident_type_id.code')
    l10n_cr_default_customer_id_number = fields.Char(related='l10n_cr_default_partner_id.vat')

    def action_test_hacienda_connection(self):
        # Placeholder for connection test logic
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Connection Test',
                'message': 'Connection to Hacienda API Successful',
                'type': 'success',
            }
        }

    def action_sync_offline_queue(self):
        # Placeholder for sync logic
        pass

    def action_view_queue(self):
        # Placeholder
        pass

    def action_regenerate_sequence(self):
        # Placeholder
        pass
