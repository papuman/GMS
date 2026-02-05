# -*- coding: utf-8 -*-
"""
Partner Cédula Lookup Wizard
Allows reviewing and editing Hacienda API lookup results before creating/updating partner
"""

import logging
import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PartnerCedulaLookupWizard(models.TransientModel):
    """
    Wizard for looking up cédula data from Hacienda API and
    creating/updating partners with review step.

    Workflow:
    1. User enters cédula or selects existing partner
    2. Wizard calls Hacienda API (via lookup service)
    3. Shows results for review/editing
    4. User confirms or edits before creating/updating
    5. Handles conflicts (existing partner with same VAT)
    """
    _name = 'l10n_cr.partner.cedula.lookup.wizard'
    _description = 'Partner Cédula Lookup Wizard'

    # =============================================================================
    # INPUT FIELDS
    # =============================================================================

    cedula = fields.Char(
        string='Cédula / Tax ID',
        required=True,
        help='Costa Rica tax identification number to lookup'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Existing Partner',
        help='If set, will update this partner instead of creating new one'
    )

    # =============================================================================
    # LOOKUP RESULTS
    # =============================================================================

    state = fields.Selection([
        ('input', 'Input Cédula'),
        ('lookup', 'Looking up...'),
        ('review', 'Review Results'),
        ('conflict', 'Resolve Conflict'),
        ('error', 'Lookup Error'),
    ],
        string='State',
        default='input',
        required=True,
    )

    lookup_success = fields.Boolean(
        string='Lookup Successful',
        default=False,
        readonly=True,
    )

    lookup_error = fields.Text(
        string='Lookup Error Message',
        readonly=True,
    )

    cache_status = fields.Selection([
        ('fresh', 'Fresh (0-7 days)'),
        ('stale', 'Stale (7+ days)'),
        ('new', 'Newly Fetched'),
        ('unavailable', 'API Unavailable - Using Cache'),
    ],
        string='Data Source',
        readonly=True,
    )

    cache_age_days = fields.Integer(
        string='Cache Age (Days)',
        readonly=True,
    )

    # =============================================================================
    # EDITABLE PARTNER DATA
    # =============================================================================

    name = fields.Char(
        string='Company Name',
        required=True,
    )

    tax_regime = fields.Char(
        string='Tax Regime',
        readonly=True,
    )

    tax_status = fields.Selection([
        ('inscrito', 'Active / Registered'),
        ('inactivo', 'Inactive / Cancelled'),
        ('no_encontrado', 'Not Found'),
        ('error', 'Lookup Error'),
    ],
        string='Tax Status',
        readonly=True,
    )

    economic_activities = fields.Text(
        string='Economic Activities',
        readonly=True,
        help='List of CIIU codes from Hacienda'
    )

    suggested_ciiu_id = fields.Many2one(
        'l10n_cr.ciiu.code',
        string='Suggested CIIU Code',
        help='Primary economic activity auto-detected from Hacienda'
    )

    ciiu_code_id = fields.Many2one(
        'l10n_cr.ciiu.code',
        string='CIIU Code to Assign',
        help='Economic activity code to assign to partner'
    )

    email = fields.Char(
        string='Email',
        help='Email address for e-invoice delivery'
    )

    phone = fields.Char(
        string='Phone',
    )

    mobile = fields.Char(
        string='Mobile',
    )

    # =============================================================================
    # CONFLICT RESOLUTION
    # =============================================================================

    conflict_partner_id = fields.Many2one(
        'res.partner',
        string='Conflicting Partner',
        readonly=True,
        help='Existing partner with same VAT number'
    )

    conflict_resolution = fields.Selection([
        ('update_existing', 'Update Existing Partner'),
        ('create_new', 'Create New Partner Anyway'),
        ('cancel', 'Cancel Operation'),
    ],
        string='Conflict Resolution',
        help='How to handle duplicate VAT number'
    )

    # =============================================================================
    # METADATA
    # =============================================================================

    raw_response = fields.Text(
        string='Raw API Response',
        readonly=True,
        help='Complete API response (for debugging)'
    )

    response_time = fields.Float(
        string='Response Time (seconds)',
        readonly=True,
    )

    # =============================================================================
    # ACTIONS
    # =============================================================================

    def action_lookup_cedula(self):
        """
        Trigger Hacienda API lookup and populate wizard fields.

        Returns:
            dict: Action to reload wizard in 'review' state
        """
        self.ensure_one()

        if not self.cedula:
            raise UserError(_('Please enter a cédula number'))

        # Set state to lookup (shows loading indicator)
        self.state = 'lookup'

        try:
            # Get lookup service
            lookup_service = self.env['l10n_cr.cedula.lookup.service']

            # Perform lookup (integrates cache + API + rate limiter)
            result = lookup_service.lookup_cedula(
                cedula=self.cedula,
                force_refresh=False,  # Use cache if fresh
            )

            if result.get('success'):
                # Populate wizard with results
                self._populate_from_lookup_result(result)

                # Check for conflicts
                if self._check_for_conflicts():
                    self.state = 'conflict'
                else:
                    self.state = 'review'

            else:
                # Lookup failed
                self.lookup_success = False
                self.lookup_error = result.get('error', 'Unknown error')
                self.state = 'error'

        except Exception as e:
            _logger.error('Cédula lookup failed: %s', str(e), exc_info=True)
            self.lookup_success = False
            self.lookup_error = str(e)
            self.state = 'error'

        # Return action to reload wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_force_refresh(self):
        """
        Force refresh from Hacienda API (ignore cache).

        Returns:
            dict: Action to reload wizard
        """
        self.ensure_one()

        try:
            lookup_service = self.env['l10n_cr.cedula.lookup.service']

            result = lookup_service.lookup_cedula(
                cedula=self.cedula,
                force_refresh=True,  # Bypass cache
            )

            if result.get('success'):
                self._populate_from_lookup_result(result)
                self.state = 'review'
            else:
                self.lookup_success = False
                self.lookup_error = result.get('error', 'Unknown error')
                self.state = 'error'

        except Exception as e:
            _logger.error('Force refresh failed: %s', str(e), exc_info=True)
            self.lookup_success = False
            self.lookup_error = str(e)
            self.state = 'error'

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_partner(self):
        """
        Create new partner with reviewed data.

        Returns:
            dict: Action to open new partner
        """
        self.ensure_one()

        if self.state == 'conflict' and self.conflict_resolution == 'update_existing':
            return self.action_update_partner()

        # Create partner
        partner_vals = self._prepare_partner_values()
        partner = self.env['res.partner'].create(partner_vals)

        _logger.info(
            'Created partner %s (ID: %s) from cédula lookup: %s',
            partner.name,
            partner.id,
            self.cedula
        )

        # Show success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Partner Created'),
                'message': _('Partner "%s" created successfully from Hacienda data') % partner.name,
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'res.partner',
                    'res_id': partner.id,
                    'view_mode': 'form',
                },
            },
        }

    def action_update_partner(self):
        """
        Update existing partner with reviewed data.

        Returns:
            dict: Action to open updated partner
        """
        self.ensure_one()

        # Determine which partner to update
        partner = self.partner_id or self.conflict_partner_id

        if not partner:
            raise UserError(_('No partner to update'))

        # Update partner
        partner_vals = self._prepare_partner_values()
        partner.write(partner_vals)

        _logger.info(
            'Updated partner %s (ID: %s) from cédula lookup: %s',
            partner.name,
            partner.id,
            self.cedula
        )

        # Show success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Partner Updated'),
                'message': _('Partner "%s" updated successfully from Hacienda data') % partner.name,
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'res.partner',
                    'res_id': partner.id,
                    'view_mode': 'form',
                },
            },
        }

    def action_cancel(self):
        """
        Cancel wizard without changes.

        Returns:
            dict: Close wizard action
        """
        return {'type': 'ir.actions.act_window_close'}

    # =============================================================================
    # INTERNAL METHODS
    # =============================================================================

    def _populate_from_lookup_result(self, result):
        """
        Populate wizard fields from lookup service result.

        Args:
            result (dict): Lookup service result dictionary
        """
        self.lookup_success = True
        self.lookup_error = False

        # Basic data
        self.name = result.get('name', '')
        self.tax_regime = result.get('tax_regime', '')
        self.tax_status = result.get('tax_status', 'inscrito')

        # Economic activities
        activities = result.get('economic_activities', [])
        if activities:
            self.economic_activities = '\n'.join([
                f"{act.get('code', '')}: {act.get('description', '')}"
                for act in activities
            ])

            # Auto-suggest primary CIIU
            primary_code = activities[0].get('code') if activities else None
            if primary_code:
                ciiu = self.env['l10n_cr.ciiu.code'].search([
                    ('code', '=', primary_code)
                ], limit=1)
                if ciiu:
                    self.suggested_ciiu_id = ciiu
                    self.ciiu_code_id = ciiu

        # Cache metadata
        cache_info = result.get('cache', {})
        if cache_info.get('hit'):
            cache_age = cache_info.get('age_days', 0)
            self.cache_age_days = cache_age

            if cache_age < 7:
                self.cache_status = 'fresh'
            else:
                self.cache_status = 'stale'
        else:
            self.cache_status = 'new'

        # API metadata
        self.response_time = result.get('response_time', 0.0)
        self.raw_response = json.dumps(result.get('raw_data', {}), indent=2)

    def _check_for_conflicts(self):
        """
        Check if partner with same VAT already exists.

        Returns:
            bool: True if conflict found
        """
        if not self.cedula:
            return False

        # Clean cedula for search
        cedula_clean = self.cedula.replace('-', '').replace(' ', '').strip()

        # Search for existing partner (exclude current partner if updating)
        domain = [('vat', '=', cedula_clean)]
        if self.partner_id:
            domain.append(('id', '!=', self.partner_id.id))

        conflict = self.env['res.partner'].search(domain, limit=1)

        if conflict:
            self.conflict_partner_id = conflict
            _logger.warning(
                'Conflict detected: Partner %s (ID: %s) already has VAT: %s',
                conflict.name,
                conflict.id,
                cedula_clean
            )
            return True

        return False

    def _prepare_partner_values(self):
        """
        Prepare values dict for partner create/update.

        Returns:
            dict: Partner values
        """
        # Clean cedula
        cedula_clean = self.cedula.replace('-', '').replace(' ', '').strip()

        vals = {
            'name': self.name,
            'vat': cedula_clean,
            'country_id': self.env.ref('base.cr').id,
        }

        # Add optional fields if provided
        if self.ciiu_code_id:
            vals['l10n_cr_economic_activity_id'] = self.ciiu_code_id.id

        if self.email:
            vals['email'] = self.email

        if self.phone:
            vals['phone'] = self.phone

        if self.mobile:
            vals['mobile'] = self.mobile

        # Try to auto-detect ID type from cedula format
        id_type = self._detect_id_type(cedula_clean)
        if id_type:
            vals['l10n_latam_identification_type_id'] = id_type.id

        return vals

    def _detect_id_type(self, cedula):
        """
        Auto-detect cédula ID type from number pattern.

        CR ID Types:
        - 01: Cédula Física (9 digits: 0-0000-0000)
        - 02: Cédula Jurídica (10 digits: 0-000-000000)
        - 03: DIMEX (11-12 digits)
        - 04: NITE (10 digits)

        Args:
            cedula (str): Clean cedula number

        Returns:
            l10n_latam.identification.type or False
        """
        if not cedula:
            return False

        length = len(cedula)

        # Map length to ID type code
        if length == 9:
            code = '01'  # Física
        elif length == 10:
            # Could be Jurídica (02) or NITE (04)
            # Check first digit: Jurídica starts with 3, NITE starts with 1
            if cedula[0] == '3':
                code = '02'
            else:
                code = '04'
        elif length >= 11:
            code = '03'  # DIMEX
        else:
            return False

        # Search for ID type
        return self.env['l10n_latam.identification.type'].search([
            ('name', 'ilike', code)
        ], limit=1)

    # =============================================================================
    # DEFAULT VALUES
    # =============================================================================

    @api.model
    def default_get(self, fields_list):
        """
        Populate wizard with context values.

        Context keys:
        - default_partner_id: Partner to update
        - default_cedula: Cédula to lookup
        """
        res = super().default_get(fields_list)

        # If partner provided in context, pre-fill cedula
        if res.get('partner_id'):
            partner = self.env['res.partner'].browse(res['partner_id'])
            if partner.vat:
                res['cedula'] = partner.vat

        return res
