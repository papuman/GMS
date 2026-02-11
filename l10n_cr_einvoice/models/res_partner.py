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

    # Corporate Billing MVP Fields (Phase 10)
    employee_number = fields.Char(
        string='Employee Number',
        help='Company employee ID for corporate billing',
        index=True,
        copy=False,
    )
    l10n_cr_default_einvoice_type = fields.Selection(
        [
            ('TE', 'Electronic Ticket (TE)'),
            ('FE', 'Electronic Invoice (FE)'),
        ],
        string='Default E-Invoice Type',
        help='Preferred e-invoice type for this customer. TE (Ticket) for simplified invoices, FE (Invoice) for detailed invoices.',
        default='TE',
    )

    # ===== POS DATA LOADING =====

    @api.model
    def _load_pos_data_fields(self, config):
        """Load CR-specific fields into POS frontend session.

        Without this override, the POS JavaScript (pos_einvoice.js) cannot
        access CR fields like l10n_cr_economic_activity_id for CIIU validation.
        Pattern follows Mexico's l10n_mx_edi_pos/models/res_partner.py.
        """
        result = super()._load_pos_data_fields(config)
        result += [
            'l10n_cr_economic_activity_id',
            'l10n_cr_activity_code',
            'l10n_cr_hacienda_verified',
            'l10n_cr_default_einvoice_type',
            'employee_number',
        ]
        return result

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
            # Flag all Costa Rica partners missing CIIU
            is_cr_partner = (partner.country_id == costa_rica)
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

    def _get_invoice_partner(self):
        """
        Get the partner that should be billed for invoices.

        If this partner has a parent company (parent_id), and the parent
        is marked as a company (is_company=True), return the parent.
        Otherwise, return this partner.

        This enables corporate billing: employees/contacts get invoiced
        to their parent company while maintaining the customer relationship
        for membership tracking.

        Returns:
            res.partner: The partner to bill (self or parent)
        """
        self.ensure_one()

        # Check if partner has a corporate parent
        if self.parent_id and self.parent_id.is_company:
            _logger.info(
                'Using parent company %s (ID: %s) for billing partner %s (ID: %s)',
                self.parent_id.name,
                self.parent_id.id,
                self.name,
                self.id
            )
            return self.parent_id

        # No corporate parent - bill the partner directly
        return self

    # ===== E-INVOICE VALIDATION INTEGRATION =====

    l10n_cr_einvoice_status = fields.Selection([
        ('ready', 'Ready for E-Invoice'),
        ('incomplete', 'Incomplete Data'),
        ('needs_ciiu', 'CIIU Code Required'),
        ('not_applicable', 'Not Applicable'),
    ],
        string='E-Invoice Status',
        compute='_compute_einvoice_status',
        search='_search_einvoice_status',
        store=False,
        help='Validation status for Costa Rica electronic invoicing (Factura Electrónica)',
    )

    l10n_cr_einvoice_status_message = fields.Text(
        string='E-Invoice Status Details',
        compute='_compute_einvoice_status',
        store=False,
        help='Detailed information about e-invoice readiness',
    )

    @api.depends('country_id', 'name', 'vat', 'email', 'l10n_cr_economic_activity_id')
    def _compute_einvoice_status(self):
        """
        Compute e-invoice readiness status for Costa Rica partners.

        Status levels:
        - ready: All required fields present
        - incomplete: Missing critical fields (name, vat, email, ID type)
        - needs_ciiu: Only missing CIIU code (may be date-dependent)
        - not_applicable: Not a Costa Rica partner
        """
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)

        for partner in self:
            # Only applicable to Costa Rica partners
            if partner.country_id != costa_rica:
                partner.l10n_cr_einvoice_status = 'not_applicable'
                partner.l10n_cr_einvoice_status_message = False
                continue

            # Get missing fields
            missing = partner.get_einvoice_missing_fields()

            if not missing:
                partner.l10n_cr_einvoice_status = 'ready'
                partner.l10n_cr_einvoice_status_message = (
                    'This partner is ready for Factura Electrónica (FE).\n\n'
                    '✓ All required fields are complete.'
                )
            elif missing == ['l10n_cr_economic_activity_id']:
                # Only CIIU missing
                partner.l10n_cr_einvoice_status = 'needs_ciiu'
                partner.l10n_cr_einvoice_status_message = (
                    'Economic Activity (CIIU code) is missing.\n\n'
                    'CIIU will be REQUIRED for all e-invoices from October 6, 2025.\n\n'
                    'Options:\n'
                    '1. Add CIIU code to this partner\n'
                    '2. Use Tiquete Electrónico (TE) instead of Factura (FE)'
                )
            else:
                # Multiple fields missing
                partner.l10n_cr_einvoice_status = 'incomplete'
                field_names = partner._get_field_labels(missing)
                partner.l10n_cr_einvoice_status_message = (
                    f'Missing required fields for Factura Electrónica:\n\n'
                    f'{chr(10).join("- " + field for field in field_names)}\n\n'
                    'Please complete these fields or use Tiquete Electrónico (TE).'
                )

    @api.model
    def _search_einvoice_status(self, operator, value):
        """
        Search domain for e-invoice readiness status.

        This allows filters like "Ready for E-Invoice" to work.
        """
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)

        if operator == '=' and value == 'ready':
            # Partners ready for e-invoice: CR partners with all required fields
            return [
                ('country_id', '=', costa_rica.id),
                ('name', '!=', False),
                ('vat', '!=', False),
                ('email', '!=', False),
                ('l10n_cr_economic_activity_id', '!=', False),
            ]
        elif operator == '=' and value == 'incomplete':
            # Partners with missing fields (excluding CIIU-only)
            return [
                ('country_id', '=', costa_rica.id),
                '|', '|', '|',
                ('name', '=', False),
                ('vat', '=', False),
                ('email', '=', False),
                '&',
                ('name', '!=', False),
                ('vat', '!=', False),
            ]
        elif operator == '=' and value == 'needs_ciiu':
            # Partners only missing CIIU
            return [
                ('country_id', '=', costa_rica.id),
                ('name', '!=', False),
                ('vat', '!=', False),
                ('email', '!=', False),
                ('l10n_cr_economic_activity_id', '=', False),
            ]
        elif operator == '=' and value == 'not_applicable':
            # Non-CR partners
            return [('country_id', '!=', costa_rica.id)]
        else:
            return []

    def is_einvoice_ready(self, check_ciiu=True):
        """
        Check if partner has all required fields for Factura Electrónica.

        Args:
            check_ciiu (bool): If True, check CIIU code requirement (date-dependent)

        Returns:
            bool: True if partner is ready for e-invoicing
        """
        self.ensure_one()

        # Only applicable to Costa Rica partners
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)
        if self.country_id != costa_rica:
            return True  # Not applicable, no validation needed

        # Get missing fields
        missing = self.get_einvoice_missing_fields(check_ciiu=check_ciiu)

        return len(missing) == 0

    def get_einvoice_missing_fields(self, check_ciiu=True, reference_date=None):
        """
        Get list of missing required fields for Factura Electrónica.

        Args:
            check_ciiu (bool): If True, check CIIU code requirement (date-dependent)
            reference_date (date): Date to check CIIU enforcement (defaults to today)

        Returns:
            list: List of field names that are missing or invalid
        """
        self.ensure_one()

        missing = []

        # Only check Costa Rica partners
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)
        if self.country_id != costa_rica:
            return missing

        # Check name
        if not self.name or not self.name.strip():
            missing.append('name')

        # Check VAT/cédula
        if not self.vat or not self.vat.strip():
            missing.append('vat')

        # Check email format
        if not self.email or not self.email.strip():
            missing.append('email')
        elif not self._is_valid_email(self.email):
            missing.append('email')  # Invalid format

        # Check CIIU code (date-dependent)
        if check_ciiu and not self.l10n_cr_economic_activity_id:
            if self._is_ciiu_required(reference_date):
                missing.append('l10n_cr_economic_activity_id')

        return missing

    def _is_ciiu_required(self, reference_date=None):
        """
        Check if CIIU code is required based on enforcement date.

        Args:
            reference_date (date): Date to check against (defaults to today)

        Returns:
            bool: True if CIIU code is required for this date
        """
        from datetime import date

        if reference_date is None:
            reference_date = date.today()
        elif isinstance(reference_date, str):
            reference_date = fields.Date.from_string(reference_date)

        # CIIU mandatory from October 6, 2025
        CIIU_MANDATORY_DATE = date(2025, 10, 6)

        return reference_date >= CIIU_MANDATORY_DATE

    def _is_valid_email(self, email):
        """
        Validate email format using regex.

        Args:
            email (str): Email address to validate

        Returns:
            bool: True if email format is valid
        """
        import re

        if not email:
            return False

        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(EMAIL_REGEX.match(email.strip()))

    def _get_field_labels(self, field_names):
        """
        Get human-readable labels for field names.

        Args:
            field_names (list): List of field technical names

        Returns:
            list: List of human-readable field labels
        """
        FIELD_LABELS = {
            'name': 'Customer Name',
            'vat': 'Cédula/Tax ID',
            'email': 'Email Address',
            'l10n_cr_economic_activity_id': 'Economic Activity (CIIU Code)',
        }

        return [FIELD_LABELS.get(field, field) for field in field_names]

    def validate_for_einvoice(self, check_ciiu=True, reference_date=None):
        """
        Validate partner data for e-invoice compliance.

        Raises ValidationError if partner is not ready for Factura Electrónica.

        Args:
            check_ciiu (bool): If True, check CIIU code requirement
            reference_date (date): Date to check CIIU enforcement

        Raises:
            ValidationError: If validation fails
        """
        self.ensure_one()

        # Get missing fields
        missing = self.get_einvoice_missing_fields(check_ciiu=check_ciiu, reference_date=reference_date)

        if missing:
            field_labels = self._get_field_labels(missing)
            error_msg = (
                f'Partner "{self.name}" is missing required fields for Factura Electrónica:\n\n'
                f'{chr(10).join("- " + label for label in field_labels)}\n\n'
                'Options:\n'
                '1. Update partner data with missing fields\n'
                '2. Use Tiquete Electrónico (TE) instead'
            )
            raise ValidationError(_(error_msg))

    def action_populate_from_cedula_cache(self):
        """
        Auto-populate missing partner fields from cédula cache.

        This action looks up the partner's VAT in the cédula cache and
        populates missing fields (name, CIIU code) if found.

        Returns:
            dict: Action result or notification
        """
        self.ensure_one()

        if not self.vat:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Cédula'),
                    'message': _('Partner must have a VAT/cédula number to lookup data.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Lookup in cache (normalize VAT: remove hyphens/spaces)
        vat_clean = (self.vat or '').replace('-', '').replace(' ', '').strip()
        cache = self.env['l10n_cr.cedula.cache'].get_cached(vat_clean)

        if not cache:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Not Found'),
                    'message': _('No cached data found for this cédula. Try triggering a Hacienda API lookup.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Auto-populate missing fields
        updates = {}
        updated_fields = []

        # Update name if empty
        if not self.name and cache.name:
            updates['name'] = cache.name
            updated_fields.append('Name')

        # Update CIIU if empty
        if not self.l10n_cr_economic_activity_id and cache.ciiu_code_id:
            updates['l10n_cr_economic_activity_id'] = cache.ciiu_code_id.id
            updated_fields.append('Economic Activity (CIIU)')

        if updates:
            self.write(updates)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Data Updated'),
                    'message': _(f'Updated from cache: {", ".join(updated_fields)}'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Updates'),
                    'message': _('All fields are already complete.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

    def action_validate_einvoice_readiness(self):
        """
        Manually validate e-invoice readiness and show detailed results.

        Returns:
            dict: Wizard action with validation results
        """
        self.ensure_one()

        # Perform validation
        missing = self.get_einvoice_missing_fields(check_ciiu=True)

        if not missing:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Ready for E-Invoice'),
                    'message': _('Partner is ready for Factura Electrónica (FE).'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            field_labels = self._get_field_labels(missing)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Incomplete Data'),
                    'message': _(f'Missing fields:\n{chr(10).join("- " + label for label in field_labels)}'),
                    'type': 'warning',
                    'sticky': True,
                }
            }

    # =============================================================================
    # CÉDULA LOOKUP INTEGRATION (Phase 2)
    # =============================================================================

    l10n_cr_cache_status = fields.Selection([
        ('fresh', 'Fresh (0-7 days)'),
        ('stale', 'Stale (7+ days)'),
        ('expired', 'Expired (90+ days)'),
        ('none', 'Not Cached'),
    ],
        string='Cache Status',
        compute='_compute_cache_status',
        store=False,
        help='Freshness of cached Hacienda data for this partner'
    )

    l10n_cr_last_verified = fields.Datetime(
        string='Last Hacienda Verification',
        compute='_compute_cache_status',
        store=False,
        help='Last time this partner was verified against Hacienda API'
    )

    l10n_cr_cache_age_days = fields.Integer(
        string='Cache Age (Days)',
        compute='_compute_cache_status',
        store=False,
    )

    @api.depends('vat', 'country_id')
    def _compute_cache_status(self):
        """
        Compute cache freshness status for partner's cédula.

        Only applicable to Costa Rica partners with VAT.
        """
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)
        cache_model = self.env['l10n_cr.cedula.cache']

        for partner in self:
            # Only for CR partners with VAT
            if partner.country_id != costa_rica or not partner.vat:
                partner.l10n_cr_cache_status = 'none'
                partner.l10n_cr_last_verified = False
                partner.l10n_cr_cache_age_days = 0
                continue

            # Look up cache
            cedula_clean = partner.vat.replace('-', '').replace(' ', '').strip()
            cache = cache_model.search([
                ('cedula', '=', cedula_clean),
                ('company_id', '=', partner.company_id.id or self.env.company.id),
            ], limit=1)

            if not cache:
                partner.l10n_cr_cache_status = 'none'
                partner.l10n_cr_last_verified = False
                partner.l10n_cr_cache_age_days = 0
                continue

            # Determine status
            if cache.is_fresh():
                partner.l10n_cr_cache_status = 'fresh'
            elif cache.is_stale():
                partner.l10n_cr_cache_status = 'stale'
            elif cache.is_expired():
                partner.l10n_cr_cache_status = 'expired'
            else:
                partner.l10n_cr_cache_status = 'fresh'

            partner.l10n_cr_last_verified = cache.refreshed_at
            partner.l10n_cr_cache_age_days = cache.cache_age_days

    def action_lookup_cedula(self):
        """
        Manual cédula lookup action (smart button).

        Opens wizard for reviewing and applying lookup results.

        Returns:
            dict: Wizard action
        """
        self.ensure_one()

        if not self.vat:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Cédula'),
                    'message': _('Partner must have a VAT/cédula number to lookup.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Open lookup wizard
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lookup Cédula from Hacienda'),
            'res_model': 'l10n_cr.partner.cedula.lookup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_cedula': self.vat,
            },
        }

    def action_refresh_from_hacienda(self):
        """
        Force refresh cédula data from Hacienda API.

        This action:
        1. Bypasses cache
        2. Calls Hacienda API
        3. Updates partner fields automatically
        4. Shows notification

        Returns:
            dict: Notification action
        """
        self.ensure_one()

        if not self.vat:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Cédula'),
                    'message': _('Partner must have a VAT/cédula number to refresh.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        try:
            # Call lookup service with force_refresh
            lookup_service = self.env['l10n_cr.cedula.lookup.service']
            result = lookup_service.lookup_and_cache(
                cedula=self.vat,
                force_refresh=True,
            )

            if result.get('success'):
                # Auto-update partner fields
                self._apply_lookup_result(result)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Data Refreshed'),
                        'message': _('Partner data refreshed from Hacienda successfully.'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                # Show error
                error_msg = result.get('user_message') or result.get('error', 'Unknown error')
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Refresh Failed'),
                        'message': error_msg,
                        'type': 'warning',
                        'sticky': True,
                    }
                }

        except Exception as e:
            _logger.error('Error refreshing cédula for partner %s: %s', self.id, str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Error refreshing data: %s') % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def _resolve_ciiu_from_hacienda_code(self, hacienda_code):
        """
        Resolve a Hacienda activity code to a CIIU catalog record.

        Hacienda returns 6-digit codes (e.g., 931100) but our CIIU catalog
        stores 4-digit codes (e.g., 9311). This method:
        1. Tries exact match first (handles pre-normalized 4-digit codes)
        2. Truncates to 4 digits if exact match fails
        3. Auto-creates the CIIU record if code is not in catalog

        Args:
            hacienda_code (str): Activity code from Hacienda (4 or 6 digits)

        Returns:
            l10n_cr.ciiu.code record or False
        """
        if not hacienda_code:
            return False

        code = str(hacienda_code).strip()
        if not code:
            return False

        # Strip decimal part first (e.g., "4690.0" → "4690")
        code = code.split('.')[0]

        # Truncate to 4 digits if still longer (e.g., "469000" → "4690")
        if len(code) > 4:
            code = code[:4]

        CiiuCode = self.env['l10n_cr.ciiu.code']

        # Try match with normalized code
        ciiu = CiiuCode.search([('code', '=', code)], limit=1)
        if ciiu:
            return ciiu

        # Auto-create if code not in catalog
        # Infer CIIU section letter from division number (first 2 digits)
        code_4 = code
        if len(code_4) == 4 and code_4.isdigit():
            section = self._infer_ciiu_section(code_4)
            try:
                ciiu = CiiuCode.sudo().create({
                    'code': code_4,
                    'name': f'Activity {code_4} (auto-created from Hacienda)',
                    'section': section,
                })
                _logger.info(
                    'Auto-created CIIU code %s (section %s) from Hacienda code %s',
                    code_4, section, hacienda_code,
                )
                return ciiu
            except Exception as e:
                _logger.warning(
                    'Failed to auto-create CIIU code %s: %s',
                    code_4, str(e),
                )

        return False

    @api.model
    def _infer_ciiu_section(self, code):
        """
        Infer CIIU section letter from 4-digit code's division (first 2 digits).

        Based on ISIC Rev.4 / CIIU Rev.4 structure.

        Args:
            code (str): 4-digit CIIU code

        Returns:
            str: Section letter (A-U)
        """
        division = int(code[:2])
        # ISIC Rev.4 division → section mapping
        if division <= 3:
            return 'A'       # Agriculture
        elif division <= 9:
            return 'B'       # Mining
        elif division <= 33:
            return 'C'       # Manufacturing
        elif division == 35:
            return 'D'       # Electricity/Gas
        elif division <= 39:
            return 'E'       # Water/Waste
        elif division <= 43:
            return 'F'       # Construction
        elif division <= 47:
            return 'G'       # Wholesale/Retail
        elif division <= 53:
            return 'H'       # Transportation
        elif division <= 56:
            return 'I'       # Accommodation/Food
        elif division <= 63:
            return 'J'       # Information/Communication
        elif division <= 66:
            return 'K'       # Financial
        elif division == 68:
            return 'L'       # Real Estate
        elif division <= 75:
            return 'M'       # Professional/Scientific
        elif division <= 82:
            return 'N'       # Administrative
        elif division == 84:
            return 'O'       # Public Administration
        elif division == 85:
            return 'P'       # Education
        elif division <= 88:
            return 'Q'       # Health
        elif division <= 93:
            return 'R'       # Arts/Entertainment
        elif division <= 96:
            return 'S'       # Other Services
        elif division <= 98:
            return 'T'       # Households
        elif division == 99:
            return 'U'       # Extraterritorial
        else:
            return 'S'       # Default fallback

    @api.onchange('vat')
    def _onchange_vat_lookup_ciiu(self):
        """
        Auto-populate CIIU from cédula cache when VAT is entered.

        Cache-only — no API calls, instant (<500ms).
        If no cache entry exists, does nothing (user selects manually
        or write/create hooks trigger API lookup on save).

        Guards:
        - Only for Costa Rica partners
        - Only when VAT is a valid CR cédula (9-12 digits)
        - Only when CIIU is not already set (don't overwrite)
        - Silent failure on errors (never blocks the form)
        """
        if not self.vat:
            return

        # Guard: only for CR partners (or partners without country yet)
        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)
        if self.country_id and costa_rica and self.country_id != costa_rica:
            return

        # Guard: validate cédula format (9-12 digits)
        vat_clean = (self.vat or '').replace('-', '').replace(' ', '').strip()
        if not vat_clean.isdigit() or len(vat_clean) < 9 or len(vat_clean) > 12:
            return

        # Guard: don't overwrite existing CIIU
        if self.l10n_cr_economic_activity_id:
            return

        try:
            # Cache-only lookup — no API calls
            cache = self.env['l10n_cr.cedula.cache'].search([
                ('cedula', '=', vat_clean),
                ('company_id', '=', self.env.company.id),
            ], limit=1)

            if not cache:
                return

            # Auto-fill CIIU from cached primary activity
            if cache.ciiu_code_id:
                self.l10n_cr_economic_activity_id = cache.ciiu_code_id
            elif cache.primary_activity:
                ciiu = self._resolve_ciiu_from_hacienda_code(cache.primary_activity)
                if ciiu:
                    self.l10n_cr_economic_activity_id = ciiu

            # Auto-fill name if empty
            if not self.name and cache.name:
                self.name = cache.name

        except Exception:
            # Silent failure — never block the form
            _logger.debug(
                'CIIU cache lookup failed for VAT %s (non-blocking)',
                vat_clean, exc_info=True,
            )

    # =============================================================================
    # WRITE/CREATE HOOKS FOR CIIU AUTO-POPULATE
    # =============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-populate CIIU from API on partner creation."""
        records = super().create(vals_list)
        records._auto_populate_ciiu_on_save()
        return records

    def write(self, vals):
        """Override write to auto-populate CIIU when VAT changes."""
        result = super().write(vals)
        # Only trigger if VAT was changed
        if 'vat' in vals:
            self._auto_populate_ciiu_on_save()
        return result

    def _auto_populate_ciiu_on_save(self):
        """
        Auto-populate CIIU from cache or GoMeta API when a partner is saved.

        Called from create() and write() hooks. Only triggers when:
        - Partner has a valid CR cédula
        - CIIU is not already set
        - Not in a recursive call (skip_ciiu_auto_populate context flag)

        Strategy:
        1. Check cache first (instant)
        2. If no cache → single GoMeta API call (3s timeout, no retry)
        3. Cache result for future instant lookups
        4. If fails → leave empty silently
        """
        if self.env.context.get('skip_ciiu_auto_populate'):
            return

        costa_rica = self.env.ref('base.cr', raise_if_not_found=False)
        if not costa_rica:
            return

        for partner in self:
            # Guard: only for CR partners with VAT and no CIIU
            if partner.l10n_cr_economic_activity_id:
                continue
            if partner.country_id and partner.country_id != costa_rica:
                continue

            vat_clean = (partner.vat or '').replace('-', '').replace(' ', '').strip()
            if not vat_clean.isdigit() or len(vat_clean) < 9 or len(vat_clean) > 12:
                continue

            try:
                ciiu = self._try_populate_ciiu_from_cache_or_api(partner, vat_clean)
                if ciiu:
                    partner.with_context(skip_ciiu_auto_populate=True).write({
                        'l10n_cr_economic_activity_id': ciiu.id,
                    })
                    _logger.info(
                        'Auto-populated CIIU %s for partner %s (VAT: %s)',
                        ciiu.code, partner.name, vat_clean,
                    )
            except Exception:
                _logger.debug(
                    'CIIU auto-populate failed for partner %s (non-blocking)',
                    partner.id, exc_info=True,
                )

    def _try_populate_ciiu_from_cache_or_api(self, partner, vat_clean):
        """
        Try to resolve CIIU code from cache, then GoMeta API.

        Args:
            partner: res.partner record
            vat_clean: normalized cédula (digits only)

        Returns:
            l10n_cr.ciiu.code record or False
        """
        # Step 1: Check cache (instant)
        cache = self.env['l10n_cr.cedula.cache'].search([
            ('cedula', '=', vat_clean),
            ('company_id', '=', partner.company_id.id or self.env.company.id),
        ], limit=1)

        if cache:
            if cache.ciiu_code_id:
                return cache.ciiu_code_id
            if cache.primary_activity:
                ciiu = self._resolve_ciiu_from_hacienda_code(cache.primary_activity)
                if ciiu:
                    return ciiu

        # Step 2: Single GoMeta API call (3s timeout, no retry, no rate limiter)
        import requests as _requests
        try:
            url = f'https://apis.gometa.org/cedulas/{vat_clean}'
            resp = _requests.get(url, timeout=3)
            if resp.status_code != 200:
                return False

            api_data = resp.json()
            actividades = api_data.get('actividades', [])
            if not actividades:
                return False

            raw_code = actividades[0].get('codigo', '')
            if not raw_code:
                return False

            # Normalize: strip decimal part
            code = str(raw_code).split('.')[0]
            if len(code) > 4:
                code = code[:4]

            ciiu = self._resolve_ciiu_from_hacienda_code(code)

            # Cache result for future instant lookups
            try:
                lookup_service = self.env['l10n_cr.cedula.lookup.service']
                normalized = lookup_service._normalize_gometa_response(api_data, vat_clean)
                lookup_service._save_to_cache(vat_clean, normalized, 'gometa')
            except Exception:
                _logger.debug('Failed to cache GoMeta result for %s', vat_clean)

            return ciiu

        except Exception:
            _logger.debug('GoMeta API call failed for %s (non-blocking)', vat_clean)
            return False

    def _apply_lookup_result(self, result):
        """
        Apply lookup result data to partner fields.

        Only updates empty fields - doesn't overwrite existing data.

        Args:
            result (dict): Lookup service result
        """
        self.ensure_one()

        if not result.get('success'):
            return

        data = result.get('data', {})
        updates = {}

        # Update name if empty
        if not self.name and data.get('name'):
            updates['name'] = data['name']

        # Update CIIU if empty and available (uses resolver for 6→4 digit handling)
        if not self.l10n_cr_economic_activity_id and data.get('primary_activity'):
            ciiu = self._resolve_ciiu_from_hacienda_code(data['primary_activity'])
            if ciiu:
                updates['l10n_cr_economic_activity_id'] = ciiu.id

        if updates:
            self.write(updates)
            _logger.info(
                'Applied lookup result to partner %s (ID: %s): %s',
                self.name,
                self.id,
                ', '.join(updates.keys())
            )

    # =============================================================================
    # HACIENDA VERIFICATION STATUS (FOR PHASE 3 TESTS)
    # =============================================================================

    l10n_cr_hacienda_verified = fields.Boolean(
        string='Hacienda Verified',
        default=False,
        help='Indicates if partner data has been verified with Hacienda',
    )
    l10n_cr_tax_status = fields.Selection([
        ('inscrito', 'Registered (Inscrito)'),
        ('no_encontrado', 'Not Found'),
        ('error', 'Error'),
    ], string='Tax Status', help='Hacienda registry status')
    l10n_cr_hacienda_last_sync = fields.Datetime(
        string='Last Hacienda Sync',
        help='Last time partner data was synced with Hacienda',
    )

    @api.depends('l10n_cr_hacienda_last_sync')
    def _compute_hacienda_cache_age_hours(self):
        """Compute hours since last Hacienda sync."""
        for partner in self:
            if partner.l10n_cr_hacienda_last_sync:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                last_sync = fields.Datetime.from_string(partner.l10n_cr_hacienda_last_sync)
                if last_sync.tzinfo is None:
                    last_sync = last_sync.replace(tzinfo=timezone.utc)
                delta = now - last_sync
                partner.l10n_cr_hacienda_cache_age_hours = delta.total_seconds() / 3600.0
            else:
                partner.l10n_cr_hacienda_cache_age_hours = 0.0

    l10n_cr_hacienda_cache_age_hours = fields.Float(
        string='Cache Age (Hours)',
        compute='_compute_hacienda_cache_age_hours',
        help='Hours since last Hacienda sync',
    )

    def get_validation_status(self):
        """
        Get partner validation status for UI display.

        Returns:
            dict: {
                'is_valid': bool or None,
                'icon': 'valid'|'warning'|'unknown',
                'message': str,
                'reason': str (optional),
            }
        """
        self.ensure_one()

        # Check for validation override first
        if self.l10n_cr_cedula_validation_override:
            return {
                'is_valid': True,
                'icon': 'warning',
                'message': 'Validation override active',
                'reason': self.l10n_cr_override_reason or 'No reason provided',
            }

        if not self.l10n_cr_hacienda_verified:
            return {
                'is_valid': None,
                'icon': 'unknown',
                'message': 'Partner has not been verified with Hacienda',
            }

        if self.l10n_cr_tax_status == 'inscrito':
            # Check if cache is stale
            if self.l10n_cr_hacienda_cache_stale:
                return {
                    'is_valid': False,
                    'icon': 'warning',
                    'reason': f'Cache is stale ({int(self.l10n_cr_hacienda_cache_age_hours / 24)} days old)',
                    'message': 'Cache is stale',
                }
            else:
                return {
                    'is_valid': True,
                    'icon': 'valid',
                    'message': 'Verified with Hacienda',
                    'reason': 'Partner is verified and current',
                }
        elif self.l10n_cr_tax_status == 'no_encontrado':
            return {
                'is_valid': False,
                'icon': 'warning',
                'message': 'Partner not found in Hacienda registry',
            }
        else:
            return {
                'is_valid': False,
                'icon': 'warning',
                'message': 'Verification error',
            }

    # Validation override fields (for tests)
    l10n_cr_cedula_validation_override = fields.Boolean(
        string='Validation Override',
        default=False,
        help='Allow partner to bypass validation (use with caution)',
    )
    l10n_cr_override_reason = fields.Text(
        string='Override Reason',
        help='Justification for validation override',
    )
    l10n_cr_override_user_id = fields.Many2one(
        'res.users',
        string='Override By',
        help='User who authorized the override',
    )
    l10n_cr_override_date = fields.Datetime(
        string='Override Date',
        help='When the override was authorized',
    )

    # Computed cache staleness and validity fields
    l10n_cr_hacienda_cache_stale = fields.Boolean(
        string='Cache Stale',
        compute='_compute_hacienda_cache_stale',
        search='_search_hacienda_cache_stale',
        store=False,
        help='Whether the Hacienda cache is stale based on tax status',
    )

    l10n_cr_hacienda_cache_valid = fields.Boolean(
        string='Cache Valid',
        compute='_compute_hacienda_cache_valid',
        search='_search_hacienda_cache_valid',
        store=False,
        help='Whether the Hacienda cache is valid (fresh, verified, and inscrito)',
    )

    @api.depends('l10n_cr_hacienda_last_sync', 'l10n_cr_tax_status', 'l10n_cr_hacienda_cache_age_hours')
    def _compute_hacienda_cache_stale(self):
        """
        Compute whether cache is stale based on tax status and age.

        Staleness thresholds:
        - inscrito: >24 hours
        - no_encontrado: >30 days (720 hours)
        - error: >7 days (168 hours)
        - never synced: always stale
        """
        for partner in self:
            if not partner.l10n_cr_hacienda_last_sync:
                partner.l10n_cr_hacienda_cache_stale = True
                continue

            age_hours = partner.l10n_cr_hacienda_cache_age_hours
            tax_status = partner.l10n_cr_tax_status

            if tax_status == 'inscrito':
                # Fresh for 24 hours
                partner.l10n_cr_hacienda_cache_stale = age_hours > 24
            elif tax_status == 'no_encontrado':
                # Fresh for 30 days
                partner.l10n_cr_hacienda_cache_stale = age_hours > (30 * 24)
            elif tax_status == 'error':
                # Fresh for 7 days
                partner.l10n_cr_hacienda_cache_stale = age_hours > (7 * 24)
            else:
                # Unknown status: consider stale
                partner.l10n_cr_hacienda_cache_stale = True

    @api.model
    def _search_hacienda_cache_stale(self, operator, value):
        """Search domain for stale cache."""
        # This is a computed field search - we need to implement custom logic
        # For now, return a basic domain that checks if last_sync is old
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        fresh_threshold = now - timedelta(days=7)

        if operator == '=' and value:
            # Find stale caches (>7 days old or never synced)
            return [
                '|',
                ('l10n_cr_hacienda_last_sync', '=', False),
                ('l10n_cr_hacienda_last_sync', '<', fields.Datetime.to_string(fresh_threshold)),
            ]
        elif operator == '=' and not value:
            # Find fresh caches (<=7 days old)
            return [
                ('l10n_cr_hacienda_last_sync', '!=', False),
                ('l10n_cr_hacienda_last_sync', '>=', fields.Datetime.to_string(fresh_threshold)),
            ]
        else:
            return []

    @api.depends('l10n_cr_hacienda_last_sync', 'l10n_cr_hacienda_verified',
                 'l10n_cr_tax_status', 'l10n_cr_hacienda_cache_stale')
    def _compute_hacienda_cache_valid(self):
        """
        Compute whether cache is valid.

        Cache is valid only if ALL conditions are met:
        - Has been synced (last_sync is not False)
        - Is verified (hacienda_verified = True)
        - Tax status is 'inscrito'
        - Cache is not stale
        """
        for partner in self:
            partner.l10n_cr_hacienda_cache_valid = (
                bool(partner.l10n_cr_hacienda_last_sync) and
                partner.l10n_cr_hacienda_verified and
                partner.l10n_cr_tax_status == 'inscrito' and
                not partner.l10n_cr_hacienda_cache_stale
            )

    @api.model
    def _search_hacienda_cache_valid(self, operator, value):
        """Search domain for valid cache."""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        fresh_threshold = now - timedelta(days=7)

        if operator == '=' and value:
            # Find valid caches
            return [
                ('l10n_cr_hacienda_last_sync', '!=', False),
                ('l10n_cr_hacienda_last_sync', '>=', fields.Datetime.to_string(fresh_threshold)),
                ('l10n_cr_hacienda_verified', '=', True),
                ('l10n_cr_tax_status', '=', 'inscrito'),
            ]
        elif operator == '=' and not value:
            # Find invalid caches
            return [
                '|', '|', '|',
                ('l10n_cr_hacienda_last_sync', '=', False),
                ('l10n_cr_hacienda_last_sync', '<', fields.Datetime.to_string(fresh_threshold)),
                ('l10n_cr_hacienda_verified', '=', False),
                ('l10n_cr_tax_status', '!=', 'inscrito'),
            ]
        else:
            return []

    @api.constrains('l10n_cr_cedula_validation_override', 'l10n_cr_override_reason')
    def _check_override_requires_reason(self):
        """Ensure validation override has a reason."""
        for partner in self:
            if partner.l10n_cr_cedula_validation_override and not partner.l10n_cr_override_reason:
                raise ValidationError(
                    _("Debe proporcionar una razón para anular la validación de cédula.")
                )

    @api.onchange('l10n_cr_cedula_validation_override')
    def _onchange_clear_override_reason(self):
        """Clear override reason when override is disabled."""
        if not self.l10n_cr_cedula_validation_override:
            self.l10n_cr_override_reason = False

    @api.constrains('l10n_cr_hacienda_verified', 'l10n_cr_tax_status')
    def _check_verified_status_consistency(self):
        """Ensure verified status is consistent with tax status."""
        for partner in self:
            if partner.l10n_cr_hacienda_verified and partner.l10n_cr_tax_status in ('error', 'no_encontrado'):
                raise ValidationError(
                    _("No se puede marcar como verificado un partner con estado de error en Hacienda.")
                )

    def mark_validation_override(self, reason, user=None):
        """
        Mark partner with validation override and audit trail.

        Args:
            reason (str): Justification for override
            user (res.users): User authorizing override (defaults to current user)
        """
        self.ensure_one()

        if not user:
            user = self.env.user

        self.write({
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': reason,
            'l10n_cr_override_user_id': user.id,
            'l10n_cr_override_date': fields.Datetime.now(),
        })

        _logger.info(
            'Validation override set for partner %s (ID: %s) by user %s. Reason: %s',
            self.name, self.id, user.name, reason
        )

    def clear_validation_override(self):
        """Clear validation override and all audit data."""
        self.ensure_one()

        self.write({
            'l10n_cr_cedula_validation_override': False,
            'l10n_cr_override_reason': False,
            'l10n_cr_override_user_id': False,
            'l10n_cr_override_date': False,
        })

        _logger.info(
            'Validation override cleared for partner %s (ID: %s)',
            self.name, self.id
        )

    def refresh_hacienda_cache(self):
        """
        Refresh Hacienda cache data for this partner.

        This method updates the last_sync timestamp to simulate a cache refresh.
        In production, this would call the Hacienda API.
        """
        self.ensure_one()

        self.write({
            'l10n_cr_hacienda_last_sync': fields.Datetime.now(),
        })

        _logger.info(
            'Hacienda cache refreshed for partner %s (ID: %s)',
            self.name, self.id
        )

    @api.model
    def cron_refresh_stale_caches(self):
        """
        Cron job to refresh stale Hacienda caches.

        This method finds partners with stale caches and refreshes them.
        """
        stale_partners = self.search([
            ('l10n_cr_hacienda_cache_stale', '=', True),
            ('country_id', '=', self.env.ref('base.cr').id),
        ])

        _logger.info(
            'Cron job: Found %d partners with stale Hacienda caches',
            len(stale_partners)
        )

        for partner in stale_partners:
            try:
                partner.refresh_hacienda_cache()
            except Exception as e:
                _logger.error(
                    'Error refreshing cache for partner %s (ID: %s): %s',
                    partner.name, partner.id, str(e)
                )
