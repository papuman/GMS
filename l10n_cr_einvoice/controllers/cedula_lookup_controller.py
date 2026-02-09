# -*- coding: utf-8 -*-
"""
Cédula Lookup Controller for POS Real-Time Customer Data Population

Provides JSON-RPC endpoints for:
- Real-time cédula lookup from Hacienda API
- Cache status checks
- Partner auto-fill data

Delegates all lookup logic to l10n_cr.cedula.lookup.service to ensure
proper rate limiting, company isolation, and cache management.

Part of: GMS E-Invoice Validation & Cédula Lookup System
Architecture: architecture-einvoice-validation-cedula-lookup.md
"""

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CedulaLookupController(http.Controller):
    """
    Controller for cédula lookup operations in POS.

    All methods return JSON responses compatible with POS JavaScript layer.
    All lookup logic is delegated to the centralized lookup service.
    """

    @http.route('/pos/cedula/lookup', type='json', auth='user', methods=['POST'])
    def pos_cedula_lookup(self, cedula, force_refresh=False):
        """
        Look up cédula and return company data for POS auto-fill.

        Delegates to l10n_cr.cedula.lookup.service which handles:
        - Cache with company isolation
        - Hacienda API with rate limiting
        - GoMeta fallback
        - Stale cache fallback

        Args:
            cedula (str): Cédula/Tax ID to look up (formatted or unformatted)
            force_refresh (bool): Skip cache and force fresh API call

        Returns:
            dict: Lookup result for POS consumption
        """
        try:
            if not cedula or not str(cedula).strip():
                return {
                    'success': False,
                    'error': 'Cédula is required',
                    'error_type': 'validation',
                    'message': 'Please enter a valid cédula number',
                }

            cedula_clean = self._clean_cedula(cedula)

            if not cedula_clean:
                return {
                    'success': False,
                    'error': 'Invalid cédula format',
                    'error_type': 'validation',
                    'message': 'Cédula must contain only digits',
                }

            _logger.info('POS cédula lookup: %s (force_refresh=%s)', cedula_clean, force_refresh)

            # Delegate to centralized lookup service (handles cache, rate limiting, company isolation)
            lookup_service = request.env['l10n_cr.cedula.lookup.service']
            result = lookup_service.lookup_and_cache(cedula_clean, force_refresh=force_refresh)

            if result.get('success'):
                return self._format_success_response(cedula_clean, result)

            return self._format_error_response(result)

        except Exception as e:
            _logger.error('Exception in POS cédula lookup: %s', str(e), exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_type': 'system',
                'message': 'System error. Please try again or enter data manually.',
            }

    @http.route('/pos/cedula/validate', type='json', auth='user', methods=['POST'])
    def pos_validate_cedula_format(self, cedula):
        """
        Validate cédula format without calling API.

        Used for real-time validation as user types.
        """
        try:
            cedula_clean = self._clean_cedula(cedula)

            if not cedula_clean:
                return {
                    'valid': False,
                    'error': 'Cédula must contain only digits',
                }

            if len(cedula_clean) < 9 or len(cedula_clean) > 12:
                return {
                    'valid': False,
                    'error': 'Cédula must be 9-12 digits long',
                }

            formatted = self._format_cedula(cedula_clean)

            return {
                'valid': True,
                'formatted': formatted,
                'clean': cedula_clean,
            }

        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
            }

    @http.route('/pos/cedula/cache_status', type='json', auth='user', methods=['POST'])
    def pos_cedula_cache_status(self, cedula):
        """
        Get cache status for a cédula without fetching.

        Used to show cache age indicators in UI.
        """
        try:
            cedula_clean = self._clean_cedula(cedula)
            if not cedula_clean:
                return {'in_cache': False, 'status': 'new'}

            # Use proper company-scoped cache lookup
            cache_record = request.env['l10n_cr.cedula.cache'].search([
                ('cedula', '=', cedula_clean),
                ('company_id', '=', request.env.company.id),
            ], limit=1)

            if not cache_record:
                return {'in_cache': False, 'status': 'new'}

            return {
                'in_cache': True,
                'age_days': cache_record.cache_age_days,
                'status': cache_record.cache_tier or 'unknown',
                'last_verified': (
                    cache_record.refreshed_at.strftime('%Y-%m-%d %H:%M:%S')
                    if cache_record.refreshed_at else ''
                ),
            }

        except Exception as e:
            _logger.error('Error checking cache status: %s', str(e))
            return {
                'in_cache': False,
                'status': 'error',
                'error': str(e),
            }

    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================

    def _clean_cedula(self, cedula):
        """Remove formatting from cédula and validate digits only."""
        if not cedula:
            return ''

        cleaned = str(cedula).replace('-', '').replace(' ', '').strip()

        if not cleaned.isdigit():
            return ''

        return cleaned

    def _format_cedula(self, cedula_clean):
        """
        Format cédula based on type.

        Physical person (9 digits): 1-0234-0567
        Legal entity (10 digits): 3-101-234567
        DIMEX (11-12 digits): 123456789012
        """
        if len(cedula_clean) == 9:
            return f'{cedula_clean[0]}-{cedula_clean[1:5]}-{cedula_clean[5:]}'
        elif len(cedula_clean) == 10:
            return f'{cedula_clean[0]}-{cedula_clean[1:4]}-{cedula_clean[4:]}'
        else:
            return cedula_clean

    def _format_success_response(self, cedula, result):
        """Format successful lookup result for POS consumption."""
        data = result.get('data', {})
        source = result.get('source', 'unknown')

        # Get CIIU codes and suggested record ID
        economic_activities = data.get('economic_activities', [])
        suggested_ciiu_id = self._suggest_ciiu_from_codes(economic_activities)

        cache_age = result.get('cache_age_days', 0)
        is_stale = source == 'stale_cache'

        response = {
            'success': True,
            'source': source,
            'data': {
                'name': data.get('name', ''),
                'vat': cedula,
                'tax_regime': data.get('tax_regime', ''),
                'ciiu_codes': economic_activities,
                'suggested_ciiu_id': suggested_ciiu_id,
            },
            'cache_info': {
                'age_days': cache_age,
                'status': 'stale' if is_stale else 'fresh',
                'last_verified': result.get('response_time', ''),
            },
            'message': result.get('user_message', ''),
        }

        if is_stale:
            response['warning'] = result.get('warning', f'Using stale cache ({cache_age} days old)')

        return response

    def _format_error_response(self, result):
        """Format error response for POS consumption."""
        error_type = result.get('error_type', 'unknown')

        messages = {
            'not_found': 'Cédula not found in Hacienda registry. Please enter data manually.',
            'rate_limit': 'Rate limit exceeded. Please wait a moment and try again.',
            'timeout': 'Request timeout. Please check your connection and try again.',
            'network': 'Network error. Please check your connection.',
            'api_error': 'Hacienda API error. Please try again or enter data manually.',
            'validation': str(result.get('error', 'Invalid input')),
        }

        return {
            'success': False,
            'error': str(result.get('error', 'Unknown error')),
            'error_type': error_type,
            'fallback_available': False,
            'message': messages.get(error_type, 'Lookup failed. Please enter data manually.'),
        }

    def _suggest_ciiu_from_codes(self, ciiu_codes):
        """
        Find primary CIIU code in Odoo catalog and return record ID.

        Returns None if no match found.
        """
        try:
            if not ciiu_codes:
                return None

            primary = next(
                (act for act in ciiu_codes if act.get('primary')),
                ciiu_codes[0] if ciiu_codes else None
            )

            if not primary:
                return None

            ciiu_record = request.env['l10n_cr.ciiu.code'].search([
                ('code', '=', primary.get('code', ''))
            ], limit=1)

            return ciiu_record.id if ciiu_record else None

        except Exception as e:
            _logger.error('Error suggesting CIIU: %s', str(e))
            return None
