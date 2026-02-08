# -*- coding: utf-8 -*-
"""
Account Move Line Extension for Costa Rica Electronic Invoicing

Adds discount code tracking to invoice lines for Hacienda v4.4 compliance.
"""
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    """
    Extends account.move.line to add discount code tracking.

    Required for Hacienda v4.4 compliance:
    - All discounts must have a discount code (01-10, 99)
    - Code "99" (Other) requires a text description
    """
    _inherit = 'account.move.line'

    l10n_cr_discount_code_id = fields.Many2one(
        'l10n_cr.discount.code',
        string='Discount Code (CR)',
        help='Costa Rica Hacienda discount code (required when discount > 0)',
        tracking=True,
    )

    l10n_cr_discount_description = fields.Text(
        string='Discount Description (CR)',
        help='Required when using discount code "99 - Otro". '
             'Explain the nature of the discount (max 80 characters)',
    )

    l10n_cr_discount_code_requires_description = fields.Boolean(
        string='Discount Code Requires Description',
        compute='_compute_discount_code_requires_description',
        store=False,
        help='Technical field: True if selected discount code requires description',
    )

    @api.depends('l10n_cr_discount_code_id', 'l10n_cr_discount_code_id.requires_description')
    def _compute_discount_code_requires_description(self):
        """Compute if the selected discount code requires a description."""
        for line in self:
            line.l10n_cr_discount_code_requires_description = (
                line.l10n_cr_discount_code_id and
                line.l10n_cr_discount_code_id.requires_description
            )

    @api.constrains('discount', 'l10n_cr_discount_code_id', 'move_id')
    def _check_discount_code_required(self):
        """
        Validate that discount code is provided when discount > 0.

        Only applies to Costa Rica customer invoices (out_invoice, out_refund).
        """
        for line in self:
            # Only validate for CR e-invoices
            if not line.move_id.l10n_cr_requires_einvoice:
                continue

            # Skip non-product lines (section, note, etc.)
            if line.display_type in ['line_section', 'line_note']:
                continue

            # If discount > 0, discount code is required
            if line.discount > 0 and not line.l10n_cr_discount_code_id:
                raise ValidationError(_(
                    'Discount code is required when discount percentage is applied.\n\n'
                    'Line: %(line_name)s\n'
                    'Discount: %(discount).2f%%\n\n'
                    'Please select a discount code (01-10, 99) from the dropdown.',
                    line_name=line.name or _('(no description)'),
                    discount=line.discount,
                ))

    @api.constrains('l10n_cr_discount_code_id', 'l10n_cr_discount_description', 'move_id')
    def _check_discount_code_99_description(self):
        """
        Validate that code "99" (Other) has a description.

        Hacienda requires an explanation when using "Otro" category.
        """
        for line in self:
            # Only validate for CR e-invoices
            if not line.move_id.l10n_cr_requires_einvoice:
                continue

            # Skip non-product lines
            if line.display_type in ['line_section', 'line_note']:
                continue

            # If code is "99" and has discount, description is required
            if (line.l10n_cr_discount_code_id and
                line.l10n_cr_discount_code_id.code == '99' and
                line.discount > 0):

                if not line.l10n_cr_discount_description or not line.l10n_cr_discount_description.strip():
                    raise ValidationError(_(
                        'Description is required for discount code "99 - Otro".\n\n'
                        'Line: %(line_name)s\n'
                        'Discount Code: %(code)s - %(code_name)s\n\n'
                        'Please explain the nature of this discount in the "Discount Description" field.',
                        line_name=line.name or _('(no description)'),
                        code=line.l10n_cr_discount_code_id.code,
                        code_name=line.l10n_cr_discount_code_id.name,
                    ))

    @api.constrains('l10n_cr_discount_description')
    def _check_discount_description_length(self):
        """
        Validate discount description length (max 80 characters).

        Hacienda XML spec limits NaturalezaDescuento to 80 characters.
        """
        for line in self:
            if line.l10n_cr_discount_description:
                # Format will be "99 - {description}" in XML, so max is 80 - 5 = 75
                max_length = 75
                description_length = len(line.l10n_cr_discount_description.strip())

                if description_length > max_length:
                    raise ValidationError(_(
                        'Discount description is too long (%(current)d characters).\n\n'
                        'Maximum allowed: %(max)d characters\n'
                        'Current: "%(description)s"\n\n'
                        'Please shorten the description.',
                        current=description_length,
                        max=max_length,
                        description=line.l10n_cr_discount_description[:100],
                    ))

    @api.onchange('discount', 'l10n_cr_discount_code_id')
    def _onchange_discount_code(self):
        """
        Auto-clear or set defaults when discount changes.

        - If discount = 0, clear discount code and description
        - If code != "99", clear description
        """
        for line in self:
            # Clear discount code and description if no discount
            if line.discount == 0:
                if line.l10n_cr_discount_code_id:
                    line.l10n_cr_discount_code_id = False
                if line.l10n_cr_discount_description:
                    line.l10n_cr_discount_description = False

            # Clear description if code is not "99"
            elif line.l10n_cr_discount_code_id and line.l10n_cr_discount_code_id.code != '99':
                if line.l10n_cr_discount_description:
                    line.l10n_cr_discount_description = False

    def _get_discount_nature_for_xml(self):
        """
        Get the discount nature text for XML generation.

        Returns the discount code or "code - description" format for code 99.
        Used by xml_generator.py for NaturalezaDescuento XML tag.

        Returns:
            str: Discount nature text (e.g., "01" or "99 - Special promotion")
        """
        self.ensure_one()

        if not self.l10n_cr_discount_code_id:
            # Fallback for legacy data without discount code
            return 'Descuento comercial'

        code = self.l10n_cr_discount_code_id.code

        # For code "99", include description
        if code == '99' and self.l10n_cr_discount_description:
            description = self.l10n_cr_discount_description.strip()
            # Ensure total length doesn't exceed 80 characters
            nature = f"{code} - {description}"
            if len(nature) > 80:
                nature = nature[:80]
            return nature

        # For other codes, just return the code
        return code
