# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CIIUBulkAssign(models.TransientModel):
    _name = 'l10n_cr.ciiu.bulk.assign'
    _description = 'Bulk Assign CIIU Economic Activity Codes'

    ciiu_code_id = fields.Many2one(
        'l10n_cr.ciiu.code',
        string='Economic Activity Code',
        required=True,
        help='CIIU code to assign to selected partners',
    )
    partner_ids = fields.Many2many(
        'res.partner',
        string='Partners',
        help='Partners to assign the CIIU code to',
    )
    filter_mode = fields.Selection([
        ('selected', 'Selected Partners'),
        ('category', 'By Category'),
        ('missing', 'All Missing CIIU'),
    ], string='Filter Mode', default='selected', required=True)

    category_id = fields.Many2one(
        'res.partner.category',
        string='Partner Category',
        help='Filter partners by category',
    )
    country_filter = fields.Boolean(
        string='Costa Rica Only',
        default=True,
        help='Only show Costa Rica partners',
    )
    partner_count = fields.Integer(
        string='Partners to Update',
        compute='_compute_partner_count',
        help='Number of partners that will be updated',
    )
    preview_partner_ids = fields.Many2many(
        'res.partner',
        'ciiu_bulk_assign_preview_rel',
        string='Preview',
        compute='_compute_preview_partners',
        help='Preview of partners that will be updated',
    )

    @api.depends('filter_mode', 'category_id', 'country_filter', 'partner_ids')
    def _compute_partner_count(self):
        """Compute the number of partners that will be updated."""
        for wizard in self:
            partners = wizard._get_target_partners()
            wizard.partner_count = len(partners)

    @api.depends('filter_mode', 'category_id', 'country_filter', 'partner_ids')
    def _compute_preview_partners(self):
        """Compute preview of partners to be updated."""
        for wizard in self:
            partners = wizard._get_target_partners()
            wizard.preview_partner_ids = partners[:100]  # Limit preview to 100

    def _get_target_partners(self):
        """
        Get the list of partners to update based on filter settings.

        Returns:
            recordset: Partners to update
        """
        domain = []

        # Country filter
        if self.country_filter:
            costa_rica = self.env.ref('base.cr', raise_if_not_found=False)
            if costa_rica:
                domain.append(('country_id', '=', costa_rica.id))

        # Filter mode
        if self.filter_mode == 'selected':
            if self.partner_ids:
                domain.append(('id', 'in', self.partner_ids.ids))
            else:
                return self.env['res.partner']

        elif self.filter_mode == 'category':
            if self.category_id:
                domain.append(('category_id', 'in', [self.category_id.id]))
            else:
                return self.env['res.partner']

        elif self.filter_mode == 'missing':
            domain.append(('l10n_cr_economic_activity_id', '=', False))
            domain.append(('is_company', '!=', False))  # Exclude explicit individuals

        return self.env['res.partner'].search(domain)

    def action_assign(self):
        """Assign the selected CIIU code to target partners."""
        self.ensure_one()

        if not self.ciiu_code_id:
            raise ValidationError(_('Please select a CIIU code to assign.'))

        partners = self._get_target_partners()

        if not partners:
            raise ValidationError(_('No partners match the selected filters.'))

        # Assign CIIU code
        partners.write({
            'l10n_cr_economic_activity_id': self.ciiu_code_id.id,
        })

        _logger.info(
            'Bulk assigned CIIU code %s (%s) to %s partners',
            self.ciiu_code_id.code,
            self.ciiu_code_id.name,
            len(partners)
        )

        # Return action to show updated partners
        return {
            'name': _('Updated Partners'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', partners.ids)],
            'context': {'create': False},
        }

    def action_preview(self):
        """Preview partners that will be updated."""
        self.ensure_one()
        partners = self._get_target_partners()

        return {
            'name': _('Partners to Update (%s)') % len(partners),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', partners.ids)],
            'context': {'create': False},
        }

    @api.model
    def action_quick_assign_gym(self):
        """Quick action: Assign code 9311 (Sports facilities) to gym partners."""
        return self._quick_assign_template('gym', '9311')

    @api.model
    def action_quick_assign_restaurant(self):
        """Quick action: Assign code 5610 (Restaurants) to restaurant partners."""
        return self._quick_assign_template('restaurant', '5610')

    @api.model
    def action_quick_assign_retail(self):
        """Quick action: Assign code 4711 (Retail) to retail partners."""
        return self._quick_assign_template('retail', '4711')

    @api.model
    def action_quick_assign_software(self):
        """Quick action: Assign code 6201 (Software development) to software partners."""
        return self._quick_assign_template('software', '6201')

    def _quick_assign_template(self, category_keyword, ciiu_code):
        """
        Helper method for quick assign templates.

        Args:
            category_keyword: Keyword to search in partner categories
            ciiu_code: CIIU code to assign

        Returns:
            dict: Action definition
        """
        # Find CIIU code
        ciiu = self.env['l10n_cr.ciiu.code'].search([
            ('code', '=', ciiu_code)
        ], limit=1)

        if not ciiu:
            raise ValidationError(
                _('CIIU code %s not found. Please ensure CIIU codes are loaded.') % ciiu_code
            )

        # Find partners with matching category
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)
        domain = [
            ('country_id', '=', costa_rica.id),
            ('l10n_cr_economic_activity_id', '=', False),
            ('category_id.name', 'ilike', category_keyword),
        ]

        partners = self.env['res.partner'].search(domain)

        if not partners:
            raise ValidationError(
                _('No Costa Rica partners found with category containing "%s" and missing CIIU code.') %
                category_keyword
            )

        # Assign CIIU code
        partners.write({
            'l10n_cr_economic_activity_id': ciiu.id,
        })

        _logger.info(
            'Quick assigned CIIU code %s to %s partners (category: %s)',
            ciiu_code,
            len(partners),
            category_keyword
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Assigned CIIU code %s to %s partners') % (ciiu_code, len(partners)),
                'type': 'success',
                'sticky': False,
            }
        }
