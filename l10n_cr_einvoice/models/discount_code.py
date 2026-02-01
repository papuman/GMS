# -*- coding: utf-8 -*-
"""
Costa Rica Discount Codes Catalog

Implements the 11 official discount codes required by Hacienda v4.4 specification
for electronic invoicing compliance.

Specification: Hacienda v4.4 Section 4.2.7.2 - NaturalezaDescuento
"""
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class L10nCrDiscountCode(models.Model):
    """
    Costa Rica Discount Codes Catalog

    Master data table for discount codes required by Hacienda.
    Contains 11 predefined codes (01-10, 99) per v4.4 specification.
    """
    _name = 'l10n_cr.discount.code'
    _description = 'Costa Rica Discount Code'
    _order = 'code'
    _rec_name = 'name'

    code = fields.Char(
        string='Code',
        size=2,
        required=True,
        readonly=True,
        help='Discount code as defined by Hacienda (01-10, 99)',
    )

    name = fields.Char(
        string='Name',
        required=True,
        readonly=True,
        translate=True,
        help='Short name for the discount type',
    )

    description = fields.Text(
        string='Description',
        readonly=True,
        translate=True,
        help='Detailed description of when to use this discount code',
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Inactive discount codes cannot be used in new invoices',
    )

    requires_description = fields.Boolean(
        string='Requires Description',
        default=False,
        readonly=True,
        help='If True, users must provide a description when using this code (e.g., code 99 - Otro)',
    )

    _code_unique = models.Constraint('UNIQUE(code)', 'Discount code must be unique!')

    @api.constrains('code')
    def _check_code_format(self):
        """Validate discount code format (2 digits)."""
        for record in self:
            if not record.code.isdigit() or len(record.code) != 2:
                raise ValidationError(
                    _('Discount code must be exactly 2 digits (e.g., 01, 02, 99)')
                )

    @api.depends('code', 'name')
    def _compute_display_name(self):
        """Display format: "01 - Comercial descuento"."""
        for record in self:
            record.display_name = f"{record.code} - {record.name}"

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Enable searching by code or name.

        Users can type "01" or "comercial" to find the code.
        """
        args = args or []
        domain = []

        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)]

        return self._search(domain + args, limit=limit)
