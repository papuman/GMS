# -*- coding: utf-8 -*-
"""
Cédula Lookup Controller for POS Real-Time Customer Data Population

Provides JSON-RPC endpoints for:
- Real-time cédula lookup from Hacienda API
- Cache status checks
- Partner auto-fill data

Part of: GMS E-Invoice Validation & Cédula Lookup System
Architecture: architecture-einvoice-validation-cedula-lookup.md
"""

import json
import logging
from datetime import datetime

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CedulaLookupController(http.Controller):
    """
    Controller for cédula lookup operations in POS.

    All methods return JSON responses compatible with POS JavaScript layer.
    """

    @http.route('/pos/cedula/lookup', type='json', auth='user', methods=['POST'])
    def pos_cedula_lookup(self, cedula, force_refresh=False):
        """
        Look up cédula and return company data for POS auto-fill.

        This is the main endpoint called by POS UI when user enters a cédula.

        Args:
            cedula (str): Cédula/Tax ID to look up (formatted or unformatted)
            force_refresh (bool): Skip cache and force fresh API call

        Returns:
            dict: Lookup result with structure:
                {
                    'success': True,
                    'source': 'cache'|'hacienda'|'gometa'|'stale_cache',
                    'data': {
                        'name': 'COMPANY NAME',
                        'vat': '3101234567',
                        'tax_regime': 'Régimen General',
                        'ciiu_codes': [
                            {'code': '9311', 'description': 'Gym activities', 'primary': True},
                            ...
                        ],
                        'suggested_ciiu_id': 123,  # Odoo CIIU record ID
                    },
                    'cache_info': {
                        'age_days': 3,
                        'status': 'fresh'|'stale'|'expired'|'new',
                        'last_verified': '2026-02-01 10:30:00',
                    },
                    'message': 'Human-readable status message'
                }

                On error:
                {
                    'success': False,
                    'error': 'Error message',
                    'error_type': 'not_found'|'rate_limit'|'network'|'timeout',
                    'fallback_available': True,  # If stale cache exists
                    'message': 'Human-readable error'
                }
        """
        try:
            # Validate cedula format
            if not cedula or not str(cedula).strip():
                return {
                    'success': False,
                    'error': 'Cédula is required',
                    'error_type': 'validation',
                    'message': 'Please enter a valid cédula number',
                }

            # Clean cedula (remove formatting)
            cedula_clean = self._clean_cedula(cedula)

            if not cedula_clean:
                return {
                    'success': False,
                    'error': 'Invalid cédula format',
                    'error_type': 'validation',
                    'message': 'Cédula must contain only digits',
                }

            _logger.info(f'POS cédula lookup: {cedula_clean} (force_refresh={force_refresh})')

            # Check cache first (unless force refresh)
            cache_result = None
            if not force_refresh:
                cache_result = self._check_cache(cedula_clean)

                if cache_result and cache_result.get('is_fresh'):
                    # Fresh cache hit - return immediately
                    _logger.info(f'Cache HIT (fresh): {cedula_clean}')
                    return self._format_cache_response(cache_result)

            # Cache miss or stale - call API
            api_result = self._call_hacienda_api(cedula_clean)

            if api_result.get('success'):
                # API success - save to cache and return
                _logger.info(f'API success: {cedula_clean}')
                return self._format_api_response(api_result, cache_result)

            # API failed - check for stale cache fallback
            if cache_result and not cache_result.get('is_fresh'):
                _logger.warning(f'API failed, using stale cache: {cedula_clean}')
                return self._format_stale_cache_response(cache_result, api_result)

            # No cache, API failed
            _logger.error(f'Lookup failed (no fallback): {cedula_clean}')
            return self._format_error_response(api_result)

        except Exception as e:
            _logger.error(f'Exception in POS cédula lookup: {str(e)}', exc_info=True)
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

        Args:
            cedula (str): Cédula to validate

        Returns:
            dict: {
                'valid': True/False,
                'formatted': '3-101-234567',  # Formatted version
                'clean': '3101234567',  # Clean version
                'error': 'Error message' (if invalid)
            }
        """
        try:
            cedula_clean = self._clean_cedula(cedula)

            if not cedula_clean:
                return {
                    'valid': False,
                    'error': 'Cédula must contain only digits',
                }

            # Basic length validation (9-12 digits for CR)
            if len(cedula_clean) < 9 or len(cedula_clean) > 12:
                return {
                    'valid': False,
                    'error': 'Cédula must be 9-12 digits long',
                }

            # Format based on type
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

        Args:
            cedula (str): Cédula to check

        Returns:
            dict: {
                'in_cache': True/False,
                'age_days': 3,
                'status': 'fresh'|'stale'|'expired',
                'last_verified': '2026-02-01 10:30:00',
            }
        """
        try:
            cedula_clean = self._clean_cedula(cedula)
            cache_result = self._check_cache(cedula_clean)

            if not cache_result:
                return {
                    'in_cache': False,
                    'status': 'new',
                }

            return {
                'in_cache': True,
                'age_days': cache_result.get('age_days', 0),
                'status': cache_result.get('cache_status', 'unknown'),
                'last_verified': cache_result.get('last_verified', ''),
            }

        except Exception as e:
            _logger.error(f'Error checking cache status: {str(e)}')
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
            # DIMEX or other - no standard format
            return cedula_clean

    def _check_cache(self, cedula):
        """
        Check if cédula exists in cache and return cached data.

        Returns None if not in cache.
        """
        CedulaCache = request.env['l10n_cr.cedula.cache'].sudo()

        cache_record = CedulaCache.search([
            ('cedula', '=', cedula)
        ], limit=1)

        if not cache_record:
            return None

        # Calculate cache age
        now = datetime.now()
        fetched_at = cache_record.fetched_at or cache_record.create_date

        if fetched_at:
            age_days = (now - fetched_at).days
        else:
            age_days = 999  # Very old

        # Determine cache status
        if age_days <= 7:
            cache_status = 'fresh'
            is_fresh = True
        elif age_days <= 90:
            cache_status = 'stale'
            is_fresh = False
        else:
            cache_status = 'expired'
            is_fresh = False

        return {
            'cache_id': cache_record.id,
            'name': cache_record.name,
            'tax_regime': cache_record.tax_regime,
            'economic_activities': cache_record.economic_activities,
            'age_days': age_days,
            'cache_status': cache_status,
            'is_fresh': is_fresh,
            'last_verified': fetched_at.strftime('%Y-%m-%d %H:%M:%S') if fetched_at else '',
        }

    def _call_hacienda_api(self, cedula):
        """Call Hacienda API to fetch company data."""
        try:
            HaciendaAPI = request.env['l10n_cr.hacienda.cedula.api'].sudo()
            result = HaciendaAPI.lookup_cedula(cedula)
            return result

        except Exception as e:
            _logger.error(f'Error calling Hacienda API: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'error_type': 'api_error',
            }

    def _format_cache_response(self, cache_result):
        """Format fresh cache response for POS."""
        # Parse economic activities JSON
        ciiu_codes = self._parse_economic_activities(
            cache_result.get('economic_activities', '')
        )

        # Get suggested CIIU record
        suggested_ciiu_id = self._suggest_ciiu_from_codes(ciiu_codes)

        return {
            'success': True,
            'source': 'cache',
            'data': {
                'name': cache_result.get('name', ''),
                'vat': cache_result.get('cache_id'),  # Use for lookup
                'tax_regime': cache_result.get('tax_regime', ''),
                'ciiu_codes': ciiu_codes,
                'suggested_ciiu_id': suggested_ciiu_id,
            },
            'cache_info': {
                'age_days': cache_result.get('age_days', 0),
                'status': cache_result.get('cache_status', 'fresh'),
                'last_verified': cache_result.get('last_verified', ''),
            },
            'message': f'Data from cache ({cache_result.get("age_days", 0)} days old)',
        }

    def _format_api_response(self, api_result, old_cache=None):
        """Format successful API response and update cache."""
        # Save to cache
        self._save_to_cache(api_result)

        # Parse CIIU codes
        ciiu_codes = api_result.get('economic_activities', [])
        suggested_ciiu_id = self._suggest_ciiu_from_codes(ciiu_codes)

        return {
            'success': True,
            'source': 'hacienda',
            'data': {
                'name': api_result.get('name', ''),
                'vat': api_result.get('cedula', ''),
                'tax_regime': api_result.get('tax_regime', ''),
                'ciiu_codes': ciiu_codes,
                'suggested_ciiu_id': suggested_ciiu_id,
            },
            'cache_info': {
                'age_days': 0,
                'status': 'fresh',
                'last_verified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            },
            'message': 'Fresh data from Hacienda API',
        }

    def _format_stale_cache_response(self, cache_result, api_error):
        """Format stale cache response (API failed)."""
        ciiu_codes = self._parse_economic_activities(
            cache_result.get('economic_activities', '')
        )

        suggested_ciiu_id = self._suggest_ciiu_from_codes(ciiu_codes)

        return {
            'success': True,
            'source': 'stale_cache',
            'data': {
                'name': cache_result.get('name', ''),
                'vat': cache_result.get('cache_id'),
                'tax_regime': cache_result.get('tax_regime', ''),
                'ciiu_codes': ciiu_codes,
                'suggested_ciiu_id': suggested_ciiu_id,
            },
            'cache_info': {
                'age_days': cache_result.get('age_days', 0),
                'status': 'stale',
                'last_verified': cache_result.get('last_verified', ''),
            },
            'warning': f'Using stale cache ({cache_result.get("age_days", 0)} days old). API unavailable.',
            'api_error': api_error.get('error', 'Unknown error'),
            'message': f'Using cached data (API unavailable)',
        }

    def _format_error_response(self, api_result):
        """Format error response (no cache, API failed)."""
        error_type = api_result.get('error_type', 'unknown')
        error_msg = api_result.get('error', 'Unknown error')

        # User-friendly messages based on error type
        messages = {
            'not_found': 'Cédula not found in Hacienda registry. Please enter data manually.',
            'rate_limit': 'Rate limit exceeded. Please wait a moment and try again.',
            'timeout': 'Request timeout. Please check your connection and try again.',
            'network': 'Network error. Please check your connection.',
            'api_error': 'Hacienda API error. Please try again or enter data manually.',
        }

        return {
            'success': False,
            'error': error_msg,
            'error_type': error_type,
            'fallback_available': False,
            'message': messages.get(error_type, 'Lookup failed. Please enter data manually.'),
        }

    def _save_to_cache(self, api_result):
        """Save API result to cache."""
        try:
            CedulaCache = request.env['l10n_cr.cedula.cache'].sudo()

            cedula = api_result.get('cedula', '')

            # Check if already exists
            existing = CedulaCache.search([('cedula', '=', cedula)], limit=1)

            values = {
                'cedula': cedula,
                'name': api_result.get('name', ''),
                'tax_regime': api_result.get('tax_regime', ''),
                'economic_activities': json.dumps(api_result.get('economic_activities', [])),
                'fetched_at': datetime.now(),
                'refreshed_at': datetime.now(),
                'api_source': 'hacienda',
                'tax_status': 'inscrito',
            }

            if existing:
                existing.write(values)
            else:
                CedulaCache.create(values)

        except Exception as e:
            _logger.error(f'Error saving to cache: {str(e)}')

    def _parse_economic_activities(self, activities_json):
        """Parse economic activities from JSON string."""
        try:
            if not activities_json:
                return []

            activities = json.loads(activities_json)

            if not isinstance(activities, list):
                return []

            return activities

        except json.JSONDecodeError:
            return []

    def _suggest_ciiu_from_codes(self, ciiu_codes):
        """
        Find primary CIIU code in Odoo catalog and return record ID.

        Returns None if no match found.
        """
        try:
            if not ciiu_codes:
                return None

            # Find primary activity
            primary = next(
                (act for act in ciiu_codes if act.get('primary')),
                ciiu_codes[0] if ciiu_codes else None
            )

            if not primary:
                return None

            # Look up in Odoo catalog
            CIIUCode = request.env['l10n_cr.ciiu.code'].sudo()
            ciiu_record = CIIUCode.search([
                ('code', '=', primary.get('code', ''))
            ], limit=1)

            return ciiu_record.id if ciiu_record else None

        except Exception as e:
            _logger.error(f'Error suggesting CIIU: {str(e)}')
            return None
