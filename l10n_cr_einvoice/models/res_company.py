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

    l10n_cr_needs_private_key = fields.Boolean(
        string='Needs Separate Private Key',
        compute='_compute_needs_private_key',
        help='True when a PEM/CRT certificate is uploaded that requires a separate private key file',
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

    @api.depends('l10n_cr_certificate_filename')
    def _compute_needs_private_key(self):
        for company in self:
            filename = (company.l10n_cr_certificate_filename or '').lower()
            company.l10n_cr_needs_private_key = (
                bool(filename) and not filename.endswith(('.p12', '.pfx'))
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
        if not company.l10n_cr_hacienda_username:
            missing.append('Hacienda API Username')
        if not company.l10n_cr_hacienda_password:
            missing.append('Hacienda API Password')
        if not company.l10n_cr_certificate:
            missing.append('Digital Certificate')
        if not company.l10n_cr_key_password:
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
