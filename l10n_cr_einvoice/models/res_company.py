# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Hacienda API Configuration
    l10n_cr_hacienda_env = fields.Selection([
        ('sandbox', 'Sandbox (Testing)'),
        ('production', 'Production'),
    ], string='Hacienda Environment', default='sandbox',
        help='Select the Hacienda API environment to use')

    # ---- Sandbox credential storage (existing DB columns) ----
    l10n_cr_hacienda_username = fields.Char(
        string='Sandbox API Username',
    )
    l10n_cr_hacienda_password = fields.Char(
        string='Sandbox API Password',
        groups='base.group_system',
    )
    l10n_cr_certificate = fields.Binary(
        string='Sandbox Certificate',
    )
    l10n_cr_certificate_filename = fields.Char(
        string='Sandbox Certificate Filename',
    )
    l10n_cr_private_key = fields.Binary(
        string='Sandbox Private Key',
    )
    l10n_cr_private_key_filename = fields.Char(
        string='Sandbox Private Key Filename',
    )
    l10n_cr_key_password = fields.Char(
        string='Sandbox Key Password',
        groups='base.group_system',
    )

    # ---- Production credential storage (new fields) ----
    l10n_cr_prod_hacienda_username = fields.Char(
        string='Production API Username',
    )
    l10n_cr_prod_hacienda_password = fields.Char(
        string='Production API Password',
        groups='base.group_system',
    )
    l10n_cr_prod_certificate = fields.Binary(
        string='Production Certificate',
    )
    l10n_cr_prod_certificate_filename = fields.Char(
        string='Production Certificate Filename',
    )
    l10n_cr_prod_private_key = fields.Binary(
        string='Production Private Key',
    )
    l10n_cr_prod_private_key_filename = fields.Char(
        string='Production Private Key Filename',
    )
    l10n_cr_prod_key_password = fields.Char(
        string='Production Key Password',
        groups='base.group_system',
    )

    # ---- Computed "active" fields (UI binds to these) ----
    l10n_cr_active_username = fields.Char(
        compute='_compute_active_credentials',
        inverse='_inverse_active_username',
        string='Hacienda API Username',
    )
    l10n_cr_active_password = fields.Char(
        compute='_compute_active_credentials',
        inverse='_inverse_active_password',
        string='Hacienda API Password',
    )
    l10n_cr_active_certificate = fields.Binary(
        compute='_compute_active_credentials',
        inverse='_inverse_active_certificate',
        string='Digital Certificate',
    )
    l10n_cr_active_certificate_filename = fields.Char(
        compute='_compute_active_credentials',
        inverse='_inverse_active_certificate_filename',
        string='Certificate Filename',
    )
    l10n_cr_active_private_key = fields.Binary(
        compute='_compute_active_credentials',
        inverse='_inverse_active_private_key',
        string='Private Key',
    )
    l10n_cr_active_private_key_filename = fields.Char(
        compute='_compute_active_credentials',
        inverse='_inverse_active_private_key_filename',
        string='Private Key Filename',
    )
    l10n_cr_active_key_password = fields.Char(
        compute='_compute_active_credentials',
        inverse='_inverse_active_key_password',
        string='Certificate PIN / Password',
    )

    l10n_cr_needs_private_key = fields.Boolean(
        string='Needs Separate Private Key',
        compute='_compute_needs_private_key',
        help='True when a PEM/CRT certificate is uploaded that requires a separate private key file',
    )

    @api.depends(
        'l10n_cr_hacienda_env',
        'l10n_cr_hacienda_username', 'l10n_cr_hacienda_password',
        'l10n_cr_certificate', 'l10n_cr_certificate_filename',
        'l10n_cr_key_password', 'l10n_cr_private_key', 'l10n_cr_private_key_filename',
        'l10n_cr_prod_hacienda_username', 'l10n_cr_prod_hacienda_password',
        'l10n_cr_prod_certificate', 'l10n_cr_prod_certificate_filename',
        'l10n_cr_prod_key_password', 'l10n_cr_prod_private_key', 'l10n_cr_prod_private_key_filename',
    )
    def _compute_active_credentials(self):
        for company in self:
            if company.l10n_cr_hacienda_env == 'production':
                company.l10n_cr_active_username = company.l10n_cr_prod_hacienda_username
                company.l10n_cr_active_password = company.l10n_cr_prod_hacienda_password
                company.l10n_cr_active_certificate = company.l10n_cr_prod_certificate
                company.l10n_cr_active_certificate_filename = company.l10n_cr_prod_certificate_filename
                company.l10n_cr_active_private_key = company.l10n_cr_prod_private_key
                company.l10n_cr_active_private_key_filename = company.l10n_cr_prod_private_key_filename
                company.l10n_cr_active_key_password = company.l10n_cr_prod_key_password
            else:
                company.l10n_cr_active_username = company.l10n_cr_hacienda_username
                company.l10n_cr_active_password = company.l10n_cr_hacienda_password
                company.l10n_cr_active_certificate = company.l10n_cr_certificate
                company.l10n_cr_active_certificate_filename = company.l10n_cr_certificate_filename
                company.l10n_cr_active_private_key = company.l10n_cr_private_key
                company.l10n_cr_active_private_key_filename = company.l10n_cr_private_key_filename
                company.l10n_cr_active_key_password = company.l10n_cr_key_password

    def _inverse_active_username(self):
        for company in self:
            if company.l10n_cr_hacienda_env == 'production':
                company.l10n_cr_prod_hacienda_username = company.l10n_cr_active_username
            else:
                company.l10n_cr_hacienda_username = company.l10n_cr_active_username

    def _inverse_active_password(self):
        for company in self:
            if company.l10n_cr_hacienda_env == 'production':
                company.l10n_cr_prod_hacienda_password = company.l10n_cr_active_password
            else:
                company.l10n_cr_hacienda_password = company.l10n_cr_active_password

    def _inverse_active_certificate(self):
        for company in self:
            if company.l10n_cr_hacienda_env == 'production':
                company.l10n_cr_prod_certificate = company.l10n_cr_active_certificate
            else:
                company.l10n_cr_certificate = company.l10n_cr_active_certificate

    def _inverse_active_certificate_filename(self):
        for company in self:
            if company.l10n_cr_hacienda_env == 'production':
                company.l10n_cr_prod_certificate_filename = company.l10n_cr_active_certificate_filename
            else:
                company.l10n_cr_certificate_filename = company.l10n_cr_active_certificate_filename

    def _inverse_active_private_key(self):
        for company in self:
            if company.l10n_cr_hacienda_env == 'production':
                company.l10n_cr_prod_private_key = company.l10n_cr_active_private_key
            else:
                company.l10n_cr_private_key = company.l10n_cr_active_private_key

    def _inverse_active_private_key_filename(self):
        for company in self:
            if company.l10n_cr_hacienda_env == 'production':
                company.l10n_cr_prod_private_key_filename = company.l10n_cr_active_private_key_filename
            else:
                company.l10n_cr_private_key_filename = company.l10n_cr_active_private_key_filename

    def _inverse_active_key_password(self):
        for company in self:
            if company.l10n_cr_hacienda_env == 'production':
                company.l10n_cr_prod_key_password = company.l10n_cr_active_key_password
            else:
                company.l10n_cr_key_password = company.l10n_cr_active_key_password

    @api.depends('l10n_cr_active_certificate_filename')
    def _compute_needs_private_key(self):
        for company in self:
            filename = (company.l10n_cr_active_certificate_filename or '').lower()
            company.l10n_cr_needs_private_key = (
                bool(filename) and not filename.endswith(('.p12', '.pfx'))
            )

    # Credential fields that should invalidate the Hacienda token cache when changed
    _HACIENDA_CREDENTIAL_FIELDS = {
        'l10n_cr_hacienda_username', 'l10n_cr_hacienda_password',
        'l10n_cr_prod_hacienda_username', 'l10n_cr_prod_hacienda_password',
        'l10n_cr_hacienda_env',
    }

    def write(self, vals):
        res = super().write(vals)
        if self._HACIENDA_CREDENTIAL_FIELDS & set(vals):
            from .hacienda_api import HaciendaAPI
            for company in self:
                HaciendaAPI.invalidate_token_cache(company.id)
        return res

    # Software Provider ID (v4.4 mandatory ProveedorSistemas element)
    l10n_cr_proveedor_sistemas = fields.Char(
        string='Software Provider ID',
        size=20,
        help='Developer/provider cedula for Hacienda v4.4 ProveedorSistemas. '
             'If empty, company VAT is used as fallback (self-developed system).',
    )

    # Sucursal code (branch) for consecutive number in clave
    l10n_cr_sucursal = fields.Char(
        string='Sucursal (Branch Code)',
        size=3,
        default='001',
        help='3-digit branch code for the consecutive number (Hacienda v4.4 Art. 4). '
             'Default: 001 for single-location businesses.',
    )

    # Default terminal code (used when no POS config is available)
    l10n_cr_terminal = fields.Char(
        string='Default Terminal Code',
        size=5,
        default='00001',
        help='5-digit terminal code for the consecutive number (Hacienda v4.4 Art. 4). '
             'POS terminals use their own l10n_cr_terminal_id instead.',
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

    def action_test_hacienda_connection(self):
        """Run step-by-step validation of Hacienda configuration."""
        self.ensure_one()
        company = self
        env_label = 'Production' if company.l10n_cr_hacienda_env == 'production' else 'Sandbox'
        results = []

        # ----------------------------------------------------------
        # Step 1: Required fields
        # ----------------------------------------------------------
        missing = []
        if not company.l10n_cr_active_username:
            missing.append('Hacienda API Username')
        if not company.l10n_cr_active_password:
            missing.append('Hacienda API Password')
        if not company.l10n_cr_active_certificate:
            missing.append('Digital Certificate')
        if not company.l10n_cr_active_key_password:
            missing.append('Certificate PIN / Password')

        if missing:
            results.append(('1. Required fields', 'FAILED', 'Missing: ' + ', '.join(missing)))
            results.append(('2. Certificate', 'SKIPPED', ''))
            results.append(('3. Hacienda API connection', 'SKIPPED', ''))
            raise UserError(self._format_connection_results(env_label, results))

        results.append(('1. Required fields', 'OK', ''))

        # ----------------------------------------------------------
        # Step 2: Load certificate
        # ----------------------------------------------------------
        cert_mgr = self.env['l10n_cr.certificate.manager']
        try:
            certificate, _private_key = cert_mgr.load_certificate_from_company(company)
            # Certificate loaded successfully – gather info
            now = datetime.utcnow()
            not_after = certificate.not_valid_after
            days_remaining = (not_after - now).days
            filename = company.l10n_cr_certificate_filename or 'certificate'
            cert_detail = '%s (expires %s, %d days remaining)' % (
                filename, not_after.strftime('%Y-%m-%d'), days_remaining,
            )
            results.append(('2. Certificate', 'OK', cert_detail))
        except (UserError, ValidationError, Exception) as e:
            error_msg = str(e)
            # Try to provide a friendlier message for common errors
            lower_msg = error_msg.lower()
            if 'password' in lower_msg or 'pin' in lower_msg or 'mac' in lower_msg or 'decrypt' in lower_msg:
                error_msg = 'Incorrect PIN/password for .p12 file'
            elif 'expired' in lower_msg:
                error_msg = error_msg  # already descriptive
            elif 'not yet valid' in lower_msg:
                error_msg = error_msg
            results.append(('2. Certificate', 'FAILED', error_msg))
            results.append(('3. Hacienda API connection', 'SKIPPED', ''))
            raise UserError(self._format_connection_results(env_label, results))

        # ----------------------------------------------------------
        # Step 3: Hacienda API connection
        # ----------------------------------------------------------
        api_client = self.env['l10n_cr.hacienda.api']
        try:
            result = api_client.test_connection()
        except Exception as e:
            results.append(('3. Hacienda API connection', 'FAILED', str(e)))
            raise UserError(self._format_connection_results(env_label, results))

        if result.get('success'):
            results.append(('3. Hacienda API connection', 'OK', 'authenticated successfully'))
        else:
            results.append(('3. Hacienda API connection', 'FAILED', result.get('message', 'Unknown error')))
            raise UserError(self._format_connection_results(env_label, results))

        # ----------------------------------------------------------
        # All passed – return sticky success notification
        # ----------------------------------------------------------
        cert_detail = ''
        for _name, _status, detail in results:
            if detail and 'expires' in detail:
                cert_detail = detail
                break

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Connection Test Passed (%s)') % env_label,
                'message': _(
                    'All 3 checks passed: Fields OK, Certificate OK%s, API OK.'
                ) % (' - %s' % cert_detail if cert_detail else ''),
                'type': 'success',
                'sticky': True,
            },
        }

    def _format_connection_results(self, env_label, results):
        """Format step results into a readable string for UserError dialogs."""
        lines = ['Connection Test Results (%s):\n' % env_label]
        for step_name, status, detail in results:
            if detail:
                lines.append('  %s ... %s (%s)' % (step_name, status, detail))
            else:
                lines.append('  %s ... %s' % (step_name, status))
        return '\n'.join(lines)
