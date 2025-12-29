# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class L10nCRPaymentMethod(models.Model):
    _name = 'l10n_cr.payment.method'
    _description = 'Costa Rica Payment Method Catalog (Hacienda v4.4)'
    _order = 'code'

    name = fields.Char(
        string='Payment Method Name',
        required=True,
        translate=True,
        help='Payment method name as per Hacienda regulations'
    )

    code = fields.Char(
        string='Hacienda Code',
        size=2,
        required=True,
        help='Official Hacienda payment method code (01-06)'
    )

    description = fields.Text(
        string='Description',
        translate=True,
        help='Detailed description of the payment method'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Inactive payment methods are hidden but can be reactivated'
    )

    requires_transaction_id = fields.Boolean(
        string='Requires Transaction ID',
        default=False,
        help='If True, this payment method requires a transaction ID (e.g., SINPE Móvil)'
    )

    icon = fields.Char(
        string='Icon',
        help='Font Awesome icon name (without fa- prefix)'
    )

    badge_color = fields.Char(
        string='Badge Color',
        help='Bootstrap 5 badge color class (e.g., success, primary, warning, info, purple)'
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Payment method code must be unique!'),
    ]

    @api.constrains('code')
    def _check_code_format(self):
        """Validate that code is exactly 2 digits."""
        for record in self:
            if record.code and (len(record.code) != 2 or not record.code.isdigit()):
                raise ValidationError(_(
                    'Payment method code must be exactly 2 digits. '
                    'Got: %s'
                ) % record.code)

    def name_get(self):
        """Display code and name together."""
        result = []
        for record in self:
            name = f"{record.code} - {record.name}"
            result.append((record.id, name))
        return result
