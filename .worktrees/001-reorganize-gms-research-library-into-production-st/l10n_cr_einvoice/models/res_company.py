# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Hacienda API Configuration
    l10n_cr_hacienda_env = fields.Selection([
        ('sandbox', 'Sandbox (Testing)'),
        ('production', 'Production'),
    ], string='Hacienda Environment', default='sandbox',
        help='Select the Hacienda API environment to use')

    l10n_cr_hacienda_username = fields.Char(
        string='Hacienda API Username',
        help='Username for Hacienda API authentication',
    )

    l10n_cr_hacienda_password = fields.Char(
        string='Hacienda API Password',
        help='Password for Hacienda API authentication',
    )

    # Digital Certificate
    l10n_cr_certificate = fields.Binary(
        string='Digital Certificate',
        help='X.509 digital certificate in PEM format',
    )

    l10n_cr_certificate_filename = fields.Char(
        string='Certificate Filename',
    )

    l10n_cr_private_key = fields.Binary(
        string='Private Key',
        help='Private key for digital signature in PEM format',
    )

    l10n_cr_private_key_filename = fields.Char(
        string='Private Key Filename',
    )

    l10n_cr_key_password = fields.Char(
        string='Private Key Password',
        help='Password to decrypt the private key if encrypted',
    )

    # Emisor Location (for clave generation)
    l10n_cr_emisor_location = fields.Char(
        string='Emisor Location Code',
        size=8,
        default='01010100',
        help='8-digit code: Provincia-Canton-Distrito-Barrio (e.g., 01010100 for San José)',
    )

    # Automatic Processing
    l10n_cr_auto_generate_einvoice = fields.Boolean(
        string='Auto-generate E-Invoice',
        default=True,
        help='Automatically generate electronic invoice when invoice is posted',
    )

    l10n_cr_auto_submit_einvoice = fields.Boolean(
        string='Auto-submit to Hacienda',
        default=False,
        help='Automatically submit electronic invoice to Hacienda after generation',
    )

    l10n_cr_auto_send_email = fields.Boolean(
        string='Auto-send Email',
        default=True,
        help='Automatically send email to customer when e-invoice is accepted',
    )

    # Email Configuration
    l10n_cr_einvoice_email_template_id = fields.Many2one(
        'mail.template',
        string='E-Invoice Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email template for sending electronic invoices',
    )
