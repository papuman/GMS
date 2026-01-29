# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    Configuration settings for Costa Rica Electronic Invoicing.
    This extends the Settings UI to show Hacienda-related configuration.
    All fields are related to company fields defined in res_company.py.
    """
    _inherit = 'res.config.settings'

    # Hacienda API Configuration
    l10n_cr_hacienda_env = fields.Selection(
        related='company_id.l10n_cr_hacienda_env',
        readonly=False,
        string='Hacienda Environment',
    )

    l10n_cr_hacienda_username = fields.Char(
        related='company_id.l10n_cr_hacienda_username',
        readonly=False,
        string='Hacienda API Username',
    )

    l10n_cr_hacienda_password = fields.Char(
        related='company_id.l10n_cr_hacienda_password',
        readonly=False,
        string='Hacienda API Password',
    )

    # Digital Certificate
    l10n_cr_certificate = fields.Binary(
        related='company_id.l10n_cr_certificate',
        readonly=False,
        string='Digital Certificate',
    )

    l10n_cr_certificate_filename = fields.Char(
        related='company_id.l10n_cr_certificate_filename',
        readonly=False,
        string='Certificate Filename',
    )

    l10n_cr_private_key = fields.Binary(
        related='company_id.l10n_cr_private_key',
        readonly=False,
        string='Private Key',
    )

    l10n_cr_private_key_filename = fields.Char(
        related='company_id.l10n_cr_private_key_filename',
        readonly=False,
        string='Private Key Filename',
    )

    l10n_cr_key_password = fields.Char(
        related='company_id.l10n_cr_key_password',
        readonly=False,
        string='Private Key Password',
    )

    # Emisor Location
    l10n_cr_emisor_location = fields.Char(
        related='company_id.l10n_cr_emisor_location',
        readonly=False,
        string='Emisor Location Code',
    )

    # Automatic Processing
    l10n_cr_auto_generate_einvoice = fields.Boolean(
        related='company_id.l10n_cr_auto_generate_einvoice',
        readonly=False,
        string='Auto-generate E-Invoice',
    )

    l10n_cr_auto_submit_einvoice = fields.Boolean(
        related='company_id.l10n_cr_auto_submit_einvoice',
        readonly=False,
        string='Auto-submit to Hacienda',
    )

    l10n_cr_auto_send_email = fields.Boolean(
        related='company_id.l10n_cr_auto_send_email',
        readonly=False,
        string='Auto-send Email',
    )

    # Email Configuration
    l10n_cr_einvoice_email_template_id = fields.Many2one(
        related='company_id.l10n_cr_einvoice_email_template_id',
        readonly=False,
        string='E-Invoice Email Template',
    )
