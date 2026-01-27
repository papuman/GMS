# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # E-Invoice Configuration
    l10n_cr_enable_einvoice = fields.Boolean(
        string='Enable Electronic Invoicing',
        default=True,
        help='Generate electronic receipts (Tiquetes Electrónicos) for Costa Rica',
    )

    l10n_cr_require_customer_id = fields.Boolean(
        string='Require Customer ID',
        default=True,
        help='Require customer identification for all transactions',
    )

    l10n_cr_auto_submit = fields.Boolean(
        string='Auto-Submit to Hacienda',
        default=True,
        help='Automatically submit invoices to Hacienda after validation',
    )

    l10n_cr_offline_mode = fields.Boolean(
        string='Enable Offline Mode',
        default=True,
        help='Queue invoices for later submission when offline',
    )

    l10n_cr_te_sequence_id = fields.Many2one(
        'ir.sequence',
        string='TE Sequence',
        help='Sequence for Tiquete Electrónico consecutive numbers',
        copy=False,
    )

    l10n_cr_default_email_customer = fields.Boolean(
        string='Auto-Email Receipts',
        default=True,
        help='Automatically email receipts to customers when email provided',
    )

    l10n_cr_terminal_id = fields.Char(
        string='Terminal ID',
        size=3,
        help='3-digit terminal identifier for consecutive numbers (e.g., 001)',
    )

    l10n_cr_allow_anonymous = fields.Boolean(
        string='Allow Anonymous Customers',
        default=True,
        help='Allow transactions without customer identification (uses default ID)',
    )

    l10n_cr_default_customer_id_type = fields.Selection([
        ('01', 'Cédula Física'),
        ('02', 'Cédula Jurídica'),
        ('03', 'DIMEX'),
        ('04', 'NITE'),
        ('05', 'Extranjero'),
    ], string='Default Customer ID Type', default='05',
       help='Default ID type for anonymous customers')

    l10n_cr_default_customer_id_number = fields.Char(
        string='Default Customer ID',
        default='999999999999',
        help='Default ID number for anonymous customers',
    )

    l10n_cr_queue_count = fields.Integer(
        string='Queued Invoices',
        compute='_compute_l10n_cr_queue_count',
        help='Number of invoices pending sync',
    )

    l10n_cr_last_sync = fields.Datetime(
        string='Last Sync',
        readonly=True,
        help='Timestamp of last successful sync',
    )

    l10n_cr_connection_status = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('unknown', 'Unknown'),
    ], string='Connection Status', compute='_compute_l10n_cr_connection_status',
       help='Current Hacienda API connection status')

    @api.depends('name')
    def _compute_l10n_cr_queue_count(self):
        """Count pending queue entries for this terminal."""
        for config in self:
            config.l10n_cr_queue_count = self.env['l10n_cr.pos.offline.queue'].search_count([
                ('config_id', '=', config.id),
                ('state', 'in', ['pending', 'syncing']),
            ])

    def _compute_l10n_cr_connection_status(self):
        """Check Hacienda API connectivity."""
        for config in self:
            try:
                api = self.env['l10n_cr.hacienda.api']
                if api._test_connection(config.company_id):
                    config.l10n_cr_connection_status = 'online'
                else:
                    config.l10n_cr_connection_status = 'offline'
            except Exception:
                config.l10n_cr_connection_status = 'unknown'

    @api.constrains('l10n_cr_terminal_id')
    def _check_l10n_cr_terminal_id(self):
        """Validate terminal ID format."""
        for config in self:
            if config.l10n_cr_terminal_id:
                if len(config.l10n_cr_terminal_id) != 3:
                    raise ValidationError(_('Terminal ID must be exactly 3 digits'))

                if not config.l10n_cr_terminal_id.isdigit():
                    raise ValidationError(_('Terminal ID must contain only digits'))

    @api.model
    def create(self, vals):
        """Auto-create TE sequence when creating POS config."""
        config = super().create(vals)

        # Create TE sequence if enabled for Costa Rica
        if config.company_id.country_id.code == 'CR' and config.l10n_cr_enable_einvoice:
            config._create_te_sequence()

        return config

    def _create_te_sequence(self):
        """Create Tiquete Electrónico sequence for this terminal."""
        self.ensure_one()

        if self.l10n_cr_te_sequence_id:
            _logger.warning('TE sequence already exists for %s', self.name)
            return

        # Get terminal ID (default to 001 if not set)
        terminal_id = self.l10n_cr_terminal_id or '001'

        # Sequence format: 00100001{terminal_id}0000000001 (20 digits)
        # Breakdown:
        # - 001 (3 digits): Sucursal (branch)
        # - 00001 (5 digits): POS terminal within branch
        # - {terminal_id} (3 digits): Terminal identifier
        # - 0000000001 (9 digits): Sequential number

        sequence_vals = {
            'name': f'TE Sequence - {self.name}',
            'code': f'l10n_cr.te.{self.id}',
            'implementation': 'standard',
            'prefix': f'001000{terminal_id}',
            'padding': 9,
            'number_increment': 1,
            'number_next_actual': 1,
            'company_id': self.company_id.id,
        }

        sequence = self.env['ir.sequence'].create(sequence_vals)
        self.l10n_cr_te_sequence_id = sequence

        _logger.info('Created TE sequence for POS %s: %s', self.name, sequence.code)

    def action_test_hacienda_connection(self):
        """Test connection to Hacienda API."""
        self.ensure_one()

        try:
            api = self.env['l10n_cr.hacienda.api']
            result = api._test_connection(self.company_id)

            if result:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Successful'),
                        'message': _('Successfully connected to Hacienda API'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Failed'),
                        'message': _('Cannot connect to Hacienda API'),
                        'type': 'danger',
                        'sticky': True,
                    }
                }

        except Exception as e:
            raise UserError(_('Connection test failed: %s') % str(e))

    def action_sync_offline_queue(self):
        """Manually trigger sync of offline queue."""
        self.ensure_one()

        queue_entries = self.env['l10n_cr.pos.offline.queue'].search([
            ('config_id', '=', self.id),
            ('state', '=', 'pending'),
        ])

        if not queue_entries:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Pending Invoices'),
                    'message': _('No invoices in queue for this terminal'),
                    'type': 'info',
                    'sticky': False,
                }
            }

        try:
            # Trigger sync
            result = self.env['pos.order']._l10n_cr_sync_offline_invoices()

            self.l10n_cr_last_sync = fields.Datetime.now()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Completed'),
                    'message': _('Synced %d invoices, %d errors') % (
                        result.get('success', 0),
                        result.get('errors', 0)
                    ),
                    'type': 'success' if result.get('errors', 0) == 0 else 'warning',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError(_('Sync failed: %s') % str(e))

    def action_view_queue(self):
        """Open queue view for this terminal."""
        self.ensure_one()

        return {
            'name': _('Offline Queue - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_cr.pos.offline.queue',
            'view_mode': 'tree,form',
            'domain': [('config_id', '=', self.id)],
            'context': {'default_config_id': self.id},
        }

    def action_regenerate_sequence(self):
        """Regenerate TE sequence (use with caution)."""
        self.ensure_one()

        if self.l10n_cr_te_sequence_id:
            # Archive old sequence instead of deleting
            self.l10n_cr_te_sequence_id.active = False

        self._create_te_sequence()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sequence Regenerated'),
                'message': _('New TE sequence created for %s') % self.name,
                'type': 'success',
                'sticky': False,
            }
        }
