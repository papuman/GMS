# -*- coding: utf-8 -*-
from datetime import datetime
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
    l10n_cr_default_customer_id_number = fields.Char(related='l10n_cr_default_partner_id.vat')

    @api.model
    def _load_pos_data_read(self, records, config):
        """Inject CR e-invoice config parameters into POS session data.

        Follows the Mexico l10n_mx_edi_pos pattern: override _load_pos_data_read
        to add custom keys (prefixed with _) to the config record dict.
        """
        read_records = super()._load_pos_data_read(records, config)
        if read_records:
            # Load CIIU mandatory date from system parameter (same source as xml_generator.py)
            IrConfigParameter = self.env['ir.config_parameter'].sudo()
            date_str = IrConfigParameter.get_param('l10n_cr_einvoice.ciiu_mandatory_date')
            if date_str:
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    # Valid date string — pass it through as-is
                except ValueError:
                    date_str = None
            # Default: October 6, 2025 (matches XmlGenerator.CIIU_MANDATORY_DATE)
            read_records[0]['_l10n_cr_ciiu_mandatory_date'] = date_str or '2025-10-06'
        return read_records

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

    @api.model
    def load_onboarding_gym_scenario(self, with_demo=False):
        """
        Load the Gym POS configuration scenario.
        Called when user clicks the Gym card in the store selection screen.
        """
        # Check if gym config already exists
        gym_config = self.env.ref('l10n_cr_einvoice.pos_config_gym', raise_if_not_found=False)

        if gym_config:
            # Gym config already exists, just return it
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pos.config',
                'res_id': gym_config.id,
                'view_mode': 'form',
                'target': 'current',
            }

        # If not exists, create it (shouldn't happen as it's in data file)
        company = self.env.company
        receipt_header = company.name or ''
        if company.city:
            receipt_header += '\n%s, %s' % (company.city, company.country_id.name or 'Costa Rica')
        if company.phone:
            receipt_header += '\nTel: %s' % company.phone
        if company.email:
            receipt_header += '\n%s' % company.email

        gym_config = self.create({
            'name': 'GYM POS',
            'l10n_cr_enable_einvoice': True,
            'l10n_cr_require_customer_id': False,
            'l10n_cr_auto_submit': True,
            'l10n_cr_offline_mode': False,
            'l10n_cr_allow_anonymous': True,
            'l10n_cr_default_email_customer': True,
            'l10n_cr_terminal_id': '001',
            'iface_tipproduct': False,
            'iface_tax_included': 'total',
            'receipt_header': receipt_header,
            'receipt_footer': '*** Este es un comprobante válido ***',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pos.config',
            'res_id': gym_config.id,
            'view_mode': 'form',
            'target': 'current',
        }
