# -*- coding: utf-8 -*-
"""
POS Membership Controller
==========================
HTTP controllers for POS membership quick actions.
"""

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PosMembershipController(http.Controller):
    """
    HTTP controller for POS membership operations.
    """

    @http.route('/l10n_cr/einvoice/check_connection', type='json', auth='user')
    def check_connection(self):
        """
        Check Hacienda API connection status and offline queue count.

        Returns:
            dict: {
                'online': bool,
                'queue_count': int,
                'message': str
            }
        """
        try:
            # Get current user's company
            company = request.env.company

            # Check if e-invoicing is enabled
            if not company.l10n_cr_enable_einvoice:
                return {
                    'online': False,
                    'queue_count': 0,
                    'message': 'E-invoicing not enabled',
                }

            # Test Hacienda API connection
            is_online = False
            try:
                hacienda_api = request.env['l10n_cr.hacienda.api']
                is_online = hacienda_api._test_connection(company)
            except Exception as e:
                _logger.warning('Connection check failed: %s', str(e))
                is_online = False

            # Count pending queue entries
            queue_count = request.env['l10n_cr.pos.offline.queue'].search_count([
                ('state', 'in', ['pending', 'syncing']),
                ('company_id', '=', company.id),
            ])

            return {
                'online': is_online,
                'queue_count': queue_count,
                'message': 'Connected' if is_online else 'Offline',
            }

        except Exception as e:
            _logger.error('Error checking connection: %s', str(e))
            return {
                'online': False,
                'queue_count': 0,
                'message': str(e),
            }


class ResPartnerExtension(http.Controller):
    """
    Extension methods for res.partner (customer validation).
    """

    @http.route('/l10n_cr/customer/validate_id', type='json', auth='user')
    def validate_customer_id(self, id_value):
        """
        Validate Costa Rica customer ID and check if customer exists.

        Args:
            id_value (str): Customer ID to validate

        Returns:
            dict: {
                'valid': bool,
                'message': str,
                'formatted': str,
                'partner_id': int or None,
                'partner_name': str or None,
                'partner_email': str or None,
                'partner_phone': str or None
            }
        """
        try:
            Partner = request.env['res.partner']

            # Clean the ID
            cleaned_id = id_value.replace('-', '').replace(' ', '').strip()

            if not cleaned_id:
                return {
                    'valid': False,
                    'message': 'ID cannot be empty',
                }

            # Detect ID type based on format
            id_type, formatted_id, validation_msg = self._detect_and_validate_id(cleaned_id)

            if not id_type:
                return {
                    'valid': False,
                    'message': validation_msg or 'Invalid ID format',
                }

            # Search for existing customer
            partner = Partner.search([
                ('vat', '=', cleaned_id),
                ('customer_rank', '>', 0),
            ], limit=1)

            result = {
                'valid': True,
                'message': validation_msg,
                'formatted': formatted_id,
                'id_type': id_type,
            }

            if partner:
                result.update({
                    'partner_id': partner.id,
                    'partner_name': partner.name,
                    'partner_email': partner.email,
                    'partner_phone': partner.phone or partner.mobile,
                })
            else:
                result.update({
                    'partner_id': None,
                    'partner_name': None,
                    'partner_email': None,
                    'partner_phone': None,
                })

            return result

        except Exception as e:
            _logger.error('Error validating customer ID: %s', str(e))
            return {
                'valid': False,
                'message': 'Validation error: %s' % str(e),
            }

    def _detect_and_validate_id(self, cleaned_id):
        """
        Detect and validate Costa Rica ID type.

        Args:
            cleaned_id (str): Cleaned ID (no dashes/spaces)

        Returns:
            tuple: (id_type, formatted_id, message)
        """
        # Cédula Física (9 digits)
        if len(cleaned_id) == 9 and cleaned_id.isdigit():
            formatted = f"{cleaned_id[0]}-{cleaned_id[1:5]}-{cleaned_id[5:9]}"
            return ('01', formatted, 'Valid Cédula Física')

        # Cédula Jurídica (10 digits)
        if len(cleaned_id) == 10 and cleaned_id.isdigit():
            formatted = f"{cleaned_id[0]}-{cleaned_id[1:4]}-{cleaned_id[4:10]}"
            return ('02', formatted, 'Valid Cédula Jurídica')

        # DIMEX (11-12 digits)
        if len(cleaned_id) in (11, 12) and cleaned_id.isdigit():
            return ('03', cleaned_id, 'Valid DIMEX')

        # NITE (10 digits, starts with specific pattern)
        # Note: NITE format is similar to Jurídica but starts with specific codes
        if len(cleaned_id) == 10 and cleaned_id.isdigit() and cleaned_id.startswith(('1', '2', '3')):
            # Could be either Jurídica or NITE - default to Jurídica
            formatted = f"{cleaned_id[0]}-{cleaned_id[1:4]}-{cleaned_id[4:10]}"
            return ('02', formatted, 'Valid ID (Jurídica/NITE)')

        # Extranjero (alphanumeric, 1-20 characters)
        if 1 <= len(cleaned_id) <= 20 and cleaned_id.replace('-', '').replace('_', '').isalnum():
            return ('05', cleaned_id.upper(), 'Valid foreign ID')

        # Invalid format
        return (None, None, 'Invalid ID format. Expected: 9 digits (Física), 10 digits (Jurídica), 11-12 digits (DIMEX), or alphanumeric (Extranjero)')
