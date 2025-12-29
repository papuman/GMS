# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Hacienda API Configuration
    l10n_cr_hacienda_env = fields.Selection(
        related='company_id.l10n_cr_hacienda_env',
        string='Hacienda Environment',
        readonly=False,
    )

    l10n_cr_hacienda_username = fields.Char(
        related='company_id.l10n_cr_hacienda_username',
        string='API Username',
        readonly=False,
    )

    l10n_cr_hacienda_password = fields.Char(
        related='company_id.l10n_cr_hacienda_password',
        string='API Password',
        readonly=False,
    )

    # Digital Certificate
    l10n_cr_certificate = fields.Binary(
        related='company_id.l10n_cr_certificate',
        string='Digital Certificate',
        readonly=False,
    )

    l10n_cr_certificate_filename = fields.Char(
        related='company_id.l10n_cr_certificate_filename',
        readonly=False,
    )

    l10n_cr_private_key = fields.Binary(
        related='company_id.l10n_cr_private_key',
        string='Private Key',
        readonly=False,
    )

    l10n_cr_private_key_filename = fields.Char(
        related='company_id.l10n_cr_private_key_filename',
        readonly=False,
    )

    l10n_cr_key_password = fields.Char(
        related='company_id.l10n_cr_key_password',
        string='Key Password',
        readonly=False,
    )

    # Location
    l10n_cr_emisor_location = fields.Char(
        related='company_id.l10n_cr_emisor_location',
        string='Emisor Location',
        readonly=False,
    )

    # Automation
    l10n_cr_auto_generate_einvoice = fields.Boolean(
        related='company_id.l10n_cr_auto_generate_einvoice',
        string='Auto-generate E-Invoice',
        readonly=False,
    )

    l10n_cr_auto_submit_einvoice = fields.Boolean(
        related='company_id.l10n_cr_auto_submit_einvoice',
        string='Auto-submit to Hacienda',
        readonly=False,
    )

    l10n_cr_auto_send_email = fields.Boolean(
        related='company_id.l10n_cr_auto_send_email',
        string='Auto-send Email',
        readonly=False,
    )

    l10n_cr_einvoice_email_template_id = fields.Many2one(
        related='company_id.l10n_cr_einvoice_email_template_id',
        string='Email Template',
        readonly=False,
    )

    def action_test_hacienda_connection(self):
        """Test the connection to Hacienda API."""
        self.ensure_one()

        api_client = self.env['l10n_cr.hacienda.api']
        result = api_client.test_connection()

        if result['success']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': result['message'],
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(_('Connection test failed: %s') % result['message'])
