# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # CIIU Economic Activity Fields
    l10n_cr_economic_activity_id = fields.Many2one(
        'l10n_cr.ciiu.code',
        string='Economic Activity (CIIU)',
        help='CIIU 4 economic activity code for Costa Rica e-invoicing (mandatory from Oct 6, 2025)',
        index=True,
    )
    l10n_cr_activity_code = fields.Char(
        string='Activity Code',
        related='l10n_cr_economic_activity_id.code',
        store=True,
        readonly=True,
        help='CIIU 4-digit code for quick XML access',
    )
    l10n_cr_suggested_ciiu_id = fields.Many2one(
        'l10n_cr.ciiu.code',
        string='Suggested CIIU Code',
        compute='_compute_suggested_ciiu_code',
        help='Smart suggestion based on partner category or industry',
    )
    l10n_cr_missing_ciiu = fields.Boolean(
        string='Missing CIIU Code',
        compute='_compute_missing_ciiu',
        search='_search_missing_ciiu',
        help='Partner is missing economic activity code (Costa Rica only)',
    )

    @api.depends('category_id', 'industry_id', 'name')
    def _compute_suggested_ciiu_code(self):
        """
        Suggest CIIU code based on partner category, industry, or name patterns.

        This helps users quickly assign economic activity codes.
        """
        for partner in self:
            suggested = False

            # Skip if already has a code
            if partner.l10n_cr_economic_activity_id:
                partner.l10n_cr_suggested_ciiu_id = False
                continue

            # Try category mapping first
            if partner.category_id:
                suggested = self._get_ciiu_from_category(partner.category_id)

            # Try industry mapping if no category match
            if not suggested and partner.industry_id:
                suggested = self._get_ciiu_from_industry(partner.industry_id)

            # Try name pattern matching as last resort
            if not suggested and partner.name:
                suggested = self._get_ciiu_from_name_pattern(partner.name)

            partner.l10n_cr_suggested_ciiu_id = suggested

    @api.model
    def _get_ciiu_from_category(self, categories):
        """
        Map partner categories to CIIU codes.

        Returns the most appropriate CIIU code based on category tags.
        """
        # Category name to CIIU code mapping
        CATEGORY_MAPPING = {
            # Sports & Recreation
            'gym': '9311',
            'sport': '9311',
            'fitness': '9311',
            'deportivo': '9311',
            'gimnasio': '9311',

            # Food & Beverage
            'restaurant': '5610',
            'restaurante': '5610',
            'food': '5610',
            'comida': '5610',
            'cafe': '5630',
            'bar': '5630',
            'bebidas': '5630',

            # Retail
            'retail': '4711',
            'store': '4711',
            'tienda': '4711',
            'comercio': '4711',
            'supermarket': '4711',
            'supermercado': '4711',

            # Technology
            'software': '6201',
            'technology': '6201',
            'it': '6209',
            'tecnología': '6201',
            'desarrollo': '6201',

            # Professional Services
            'consulting': '7020',
            'consultoría': '7020',
            'consultancy': '7020',
            'legal': '6910',
            'accounting': '6920',
            'contabilidad': '6920',

            # Education
            'education': '8511',
            'educación': '8511',
            'school': '8511',
            'escuela': '8511',
            'university': '8522',
            'universidad': '8522',

            # Health
            'medical': '8621',
            'health': '8621',
            'clinic': '8621',
            'clínica': '8621',
            'hospital': '8610',
            'dental': '8622',
            'odontología': '8622',

            # Beauty & Personal Services
            'beauty': '9602',
            'salon': '9602',
            'peluquería': '9602',
            'belleza': '9602',

            # Automotive
            'auto': '4520',
            'automotive': '4520',
            'repair': '4520',
            'taller': '4520',

            # Real Estate
            'real estate': '6810',
            'inmobiliaria': '6810',
            'bienes raíces': '6810',

            # Security
            'security': '8010',
            'seguridad': '8010',

            # Transportation
            'transport': '4920',
            'transporte': '4920',
            'logistics': '4920',
            'logística': '4920',
        }

        for category in categories:
            cat_name = category.name.lower()
            for keyword, ciiu_code in CATEGORY_MAPPING.items():
                if keyword in cat_name:
                    ciiu = self.env['l10n_cr.ciiu.code'].search([
                        ('code', '=', ciiu_code)
                    ], limit=1)
                    if ciiu:
                        return ciiu

        return False

    @api.model
    def _get_ciiu_from_industry(self, industry):
        """
        Map partner industry to CIIU code.

        This uses Odoo's standard industry field (res.partner.industry).
        """
        if not industry:
            return False

        # Industry to CIIU mapping
        industry_name = industry.name.lower() if industry.name else ''

        INDUSTRY_MAPPING = {
            'agriculture': '0111',
            'manufacturing': '1010',
            'retail': '4711',
            'wholesale': '4690',
            'transportation': '4920',
            'hotel': '5510',
            'restaurant': '5610',
            'telecommunications': '6110',
            'software': '6201',
            'finance': '6419',
            'real estate': '6810',
            'legal': '6910',
            'consulting': '7020',
            'engineering': '7110',
            'advertising': '7310',
            'education': '8511',
            'healthcare': '8621',
            'entertainment': '9311',
        }

        for keyword, ciiu_code in INDUSTRY_MAPPING.items():
            if keyword in industry_name:
                ciiu = self.env['l10n_cr.ciiu.code'].search([
                    ('code', '=', ciiu_code)
                ], limit=1)
                if ciiu:
                    return ciiu

        return False

    @api.model
    def _get_ciiu_from_name_pattern(self, name):
        """
        Suggest CIIU code based on company name patterns.

        This is a fallback when no category or industry is available.
        """
        if not name:
            return False

        name_lower = name.lower()

        # Name pattern to CIIU mapping
        NAME_PATTERNS = {
            'gym': '9311',
            'gimnasio': '9311',
            'fitness': '9311',
            'restaurant': '5610',
            'cafe': '5630',
            'hotel': '5510',
            'software': '6201',
            'clinic': '8621',
            'hospital': '8610',
            'school': '8511',
            'university': '8522',
            'taller': '4520',
            'ferretería': '4752',
            'farmacia': '4772',
            'supermercado': '4711',
        }

        for pattern, ciiu_code in NAME_PATTERNS.items():
            if pattern in name_lower:
                ciiu = self.env['l10n_cr.ciiu.code'].search([
                    ('code', '=', ciiu_code)
                ], limit=1)
                if ciiu:
                    return ciiu

        return False

    @api.depends('l10n_cr_economic_activity_id', 'country_id')
    def _compute_missing_ciiu(self):
        """Check if Costa Rica partner is missing CIIU code."""
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)

        for partner in self:
            # Only flag Costa Rica B2B partners
            is_cr_partner = (
                partner.country_id == costa_rica and
                not partner.is_company is False  # Exclude individuals explicitly
            )
            partner.l10n_cr_missing_ciiu = (
                is_cr_partner and
                not partner.l10n_cr_economic_activity_id
            )

    @api.model
    def _search_missing_ciiu(self, operator, value):
        """
        Search domain for partners missing CIIU code.

        This enables filters like "Missing Economic Activity".
        """
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)

        if operator == '=' and value:
            # Find CR partners without CIIU
            return [
                ('country_id', '=', costa_rica.id),
                ('l10n_cr_economic_activity_id', '=', False),
                ('is_company', '!=', False),  # Exclude explicit individuals
            ]
        elif operator == '=' and not value:
            # Find CR partners WITH CIIU or non-CR partners
            return [
                '|',
                ('country_id', '!=', costa_rica.id),
                ('l10n_cr_economic_activity_id', '!=', False),
            ]
        else:
            return []

    def action_use_suggested_ciiu(self):
        """Apply the suggested CIIU code to the partner."""
        for partner in self:
            if partner.l10n_cr_suggested_ciiu_id:
                partner.l10n_cr_economic_activity_id = partner.l10n_cr_suggested_ciiu_id
                _logger.info(
                    'Applied suggested CIIU code %s to partner %s',
                    partner.l10n_cr_suggested_ciiu_id.code,
                    partner.name
                )

    @api.constrains('l10n_cr_economic_activity_id')
    def _validate_economic_activity_for_cr_invoices(self):
        """
        Validate economic activity for Costa Rica partners.

        Before Oct 6, 2025: Log warning only
        After Oct 6, 2025: This will be enforced at invoice generation time
        """
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)

        for partner in self:
            # Only validate for Costa Rica B2B partners
            if (partner.country_id == costa_rica and
                    partner.is_company and
                    not partner.l10n_cr_economic_activity_id):

                # Log warning (not blocking yet)
                _logger.warning(
                    'Partner %s (ID: %s) is missing CIIU economic activity code. '
                    'This will be REQUIRED for e-invoicing from October 6, 2025.',
                    partner.name,
                    partner.id
                )

    @api.model
    def get_partners_missing_ciiu_count(self):
        """
        Get count of Costa Rica partners missing CIIU code.

        Used for dashboard widget.
        """
        return self.search_count([('l10n_cr_missing_ciiu', '=', True)])

    def action_view_partners_missing_ciiu(self):
        """
        Open list of partners missing CIIU code.

        Action for dashboard widget.
        """
        return {
            'name': _('Partners Missing Economic Activity'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('l10n_cr_missing_ciiu', '=', True)],
            'context': {'create': False},
        }
