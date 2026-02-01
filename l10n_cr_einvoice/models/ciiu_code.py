# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CIIUCode(models.Model):
    _name = 'l10n_cr.ciiu.code'
    _description = 'CIIU 4 Economic Activity Codes for Costa Rica'
    _order = 'code'
    _rec_name = 'complete_name'

    code = fields.Char(
        string='CIIU Code',
        size=4,
        required=True,
        index=True,
        help='4-digit CIIU 4 classification code',
    )
    name = fields.Char(
        string='Activity Name',
        required=True,
        translate=True,
        help='Description of the economic activity',
    )
    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        store=True,
        help='Code and name combined for display',
    )
    description = fields.Text(
        string='Detailed Description',
        translate=True,
        help='Extended description of the economic activity',
    )
    section = fields.Selection([
        ('A', 'A - Agriculture, forestry and fishing'),
        ('B', 'B - Mining and quarrying'),
        ('C', 'C - Manufacturing'),
        ('D', 'D - Electricity, gas, steam and air conditioning supply'),
        ('E', 'E - Water supply; sewerage, waste management'),
        ('F', 'F - Construction'),
        ('G', 'G - Wholesale and retail trade'),
        ('H', 'H - Transportation and storage'),
        ('I', 'I - Accommodation and food service'),
        ('J', 'J - Information and communication'),
        ('K', 'K - Financial and insurance activities'),
        ('L', 'L - Real estate activities'),
        ('M', 'M - Professional, scientific and technical'),
        ('N', 'N - Administrative and support service'),
        ('O', 'O - Public administration and defence'),
        ('P', 'P - Education'),
        ('Q', 'Q - Human health and social work'),
        ('R', 'R - Arts, entertainment and recreation'),
        ('S', 'S - Other service activities'),
        ('T', 'T - Households as employers'),
        ('U', 'U - Extraterritorial organizations'),
    ], string='CIIU Section', required=True, index=True,
        help='Main section of economic activity classification')
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to hide this code without deleting it',
    )
    partner_count = fields.Integer(
        string='Partners Using',
        compute='_compute_partner_count',
        help='Number of partners using this economic activity',
    )

    _code_unique = models.Constraint('unique(code)', 'CIIU code must be unique!')

    @api.depends('code', 'name')
    def _compute_complete_name(self):
        """Compute complete name as 'Code - Name' for display."""
        for record in self:
            if record.code and record.name:
                record.complete_name = f"{record.code} - {record.name}"
            elif record.code:
                record.complete_name = record.code
            else:
                record.complete_name = record.name or ''

    def _compute_partner_count(self):
        """Count partners using this economic activity."""
        for record in self:
            record.partner_count = self.env['res.partner'].search_count([
                ('l10n_cr_economic_activity_id', '=', record.id)
            ])

    @api.constrains('code')
    def _check_code_format(self):
        """Validate CIIU code format (4 digits)."""
        for record in self:
            if record.code:
                if not record.code.isdigit():
                    raise ValidationError(
                        _('CIIU code must contain only digits: %s') % record.code
                    )
                if len(record.code) != 4:
                    raise ValidationError(
                        _('CIIU code must be exactly 4 digits: %s') % record.code
                    )

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Search by code or name.

        This allows users to search by either code (e.g., "9311") or
        activity name (e.g., "deportivas").
        """
        args = args or []
        domain = []

        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)]

        return self._search(domain + args, limit=limit)

    def action_view_partners(self):
        """Open list of partners using this economic activity."""
        self.ensure_one()
        return {
            'name': _('Partners with %s') % self.complete_name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('l10n_cr_economic_activity_id', '=', self.id)],
            'context': {'default_l10n_cr_economic_activity_id': self.id},
        }
