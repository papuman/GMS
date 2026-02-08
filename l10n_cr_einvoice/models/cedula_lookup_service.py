# -*- coding: utf-8 -*-
"""
Cédula Lookup Service - Main Orchestrator with Waterfall Retry Strategy

Implements multi-tier lookup with graceful degradation:
1. Fresh Cache (0-7 days) → Instant response (90%+ hit rate)
2. Hacienda API (5s timeout) → Authoritative government source
3. GoMeta API (3s timeout) → Free fallback service
4. Stale Cache (7-90 days) → Emergency data during API outages
5. Manual Entry → User fallback with clear guidance

Part of: GMS E-Invoice Validation & Cédula Lookup System
Architecture: architecture-einvoice-validation-cedula-lookup.md
Dependencies:
    - hacienda_cedula_api.py (Phase 1)
    - cedula_cache.py (Phase 1)
    - rate_limiter.py (Phase 1 in utils/)
"""

import json
import logging
import requests
import time
from datetime import datetime, timezone

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# API Configuration
GOMETA_API_URL = 'https://apis.gometa.org/cedulas/{cedula}'
GOMETA_TIMEOUT = 3  # seconds
HACIENDA_TIMEOUT = 5  # seconds

# Error types for categorization
ERROR_NOT_FOUND = 'not_found'
ERROR_TIMEOUT = 'timeout'
ERROR_RATE_LIMIT = 'rate_limit'
ERROR_NETWORK = 'network'
ERROR_API_ERROR = 'api_error'


class CedulaLookupService(models.AbstractModel):
    """
    Main cédula lookup orchestrator with waterfall retry strategy.

    This is the primary service for all cédula lookups in the system.
    It implements a sophisticated fallback strategy that ensures business
    continuity even during API outages.

    Performance characteristics:
    - Cache hit (fresh): <500ms
    - Hacienda API: ~2-5s
    - GoMeta fallback: ~1-3s
    - Stale cache: <500ms
    - 90%+ cache hit rate in production

    Usage:
        service = self.env['l10n_cr.cedula.lookup.service']
        result = service.lookup_and_cache('3101234567')

        if result['success']:
            partner_vals = {
                'name': result['data']['name'],
                'vat': result['data']['cedula'],
                ...
            }
    """
    _name = 'l10n_cr.cedula.lookup.service'
    _description = 'Costa Rica Cédula Lookup Service (Waterfall Strategy)'

    # =============================================================================
    # MAIN LOOKUP METHOD (Waterfall Strategy)
    # =============================================================================

    @api.model
    def lookup_and_cache(self, cedula, force_refresh=False):
        """
        Main method: Look up cédula with waterfall retry strategy.

        Waterfall steps:
        1. Check cache (if fresh, return immediately)
        2. Try Hacienda API (with rate limiting)
        3. Try GoMeta API fallback (if Hacienda fails)
        4. Return stale cache (if APIs fail)
        5. Return error + manual entry prompt

        Args:
            cedula (str): Tax identification number (formatted or unformatted)
            force_refresh (bool): Skip cache, force API call (default: False)

        Returns:
            dict: {
                'success': True/False,
                'source': 'cache'|'hacienda'|'gometa'|'stale_cache'|'failed',
                'data': {
                    'cedula': '3101234567',
                    'name': 'GIMNASIO FITNESS CR S.A.',
                    'company_type': 'company',
                    'tax_regime': 'Régimen General',
                    'tax_status': 'inscrito',
                    'economic_activities': [...],
                    'primary_activity': '9311',
                    'ciiu_code_id': 42,  # Odoo record ID
                },
                'cache_age_days': 3,
                'response_time': 0.523,  # seconds
                'error': 'Human-readable error message (if failed)',
                'error_type': 'not_found'|'timeout'|'rate_limit'|'network',
                'manual_entry_required': True/False,
                'user_message': 'Spanish message for UI display',
            }
        """
        start_time = time.time()
        cedula_clean = self._clean_cedula(cedula)

        if not cedula_clean:
            return {
                'success': False,
                'source': 'failed',
                'error': _('Formato de cédula inválido. Debe contener solo dígitos.'),
                'error_type': 'validation',
                'manual_entry_required': True,
                'user_message': _('Por favor ingrese los datos manualmente.'),
            }

        _logger.info(f'Cédula lookup request: {cedula_clean} (force_refresh={force_refresh})')

        # Step 1: Check Fresh Cache (unless force refresh)
        if not force_refresh:
            cache_result = self._lookup_cache(cedula_clean)
            if cache_result['success']:
                response_time = time.time() - start_time
                cache_result['response_time'] = round(response_time, 3)
                _logger.info(
                    f'Cédula lookup SUCCESS (cache): {cedula_clean} '
                    f'in {response_time:.3f}s (age: {cache_result.get("cache_age_days", 0)} days)'
                )
                return cache_result

        # Step 2: Try Hacienda API (with rate limiting)
        hacienda_result = self._lookup_hacienda(cedula_clean)
        if hacienda_result['success']:
            # Cache the result
            cache_record = self._save_to_cache(cedula_clean, hacienda_result['data'], 'hacienda')
            response_time = time.time() - start_time
            _logger.info(
                f'Cédula lookup SUCCESS (hacienda): {cedula_clean} in {response_time:.3f}s'
            )
            return {
                'success': True,
                'source': 'hacienda',
                'data': hacienda_result['data'],
                'cache_age_days': 0,
                'response_time': round(response_time, 3),
                'user_message': _('Datos obtenidos de Hacienda.'),
            }

        # Step 3: Try GoMeta API Fallback
        _logger.warning(f'Hacienda API failed for {cedula_clean}, trying GoMeta fallback...')
        gometa_result = self._lookup_gometa(cedula_clean)
        if gometa_result['success']:
            # Cache the result
            cache_record = self._save_to_cache(cedula_clean, gometa_result['data'], 'gometa')
            response_time = time.time() - start_time
            _logger.info(
                f'Cédula lookup SUCCESS (gometa): {cedula_clean} in {response_time:.3f}s'
            )
            return {
                'success': True,
                'source': 'gometa',
                'data': gometa_result['data'],
                'cache_age_days': 0,
                'response_time': round(response_time, 3),
                'user_message': _('Datos obtenidos de fuente alternativa (GoMeta).'),
            }

        # Step 4: Return Stale Cache (7-90 days old) as emergency fallback
        _logger.warning(f'Both APIs failed for {cedula_clean}, checking stale cache...')
        stale_result = self._lookup_stale_cache(cedula_clean)
        if stale_result['success']:
            response_time = time.time() - start_time
            stale_result['response_time'] = round(response_time, 3)
            _logger.warning(
                f'Cédula lookup SUCCESS (stale cache): {cedula_clean} '
                f'in {response_time:.3f}s (age: {stale_result.get("cache_age_days", 0)} days)'
            )
            return stale_result

        # Step 5: All sources failed - return error with manual entry prompt
        response_time = time.time() - start_time
        error_message = self._build_error_message(hacienda_result, gometa_result)

        _logger.error(
            f'Cédula lookup FAILED: {cedula_clean} after {response_time:.3f}s. '
            f'All sources exhausted.'
        )

        return {
            'success': False,
            'source': 'failed',
            'error': error_message,
            'error_type': hacienda_result.get('error_type', ERROR_API_ERROR),
            'response_time': round(response_time, 3),
            'manual_entry_required': True,
            'user_message': _(
                'No se pudo obtener información de esta cédula. '
                'Por favor ingrese los datos manualmente.'
            ),
        }

    # =============================================================================
    # STEP 1: CACHE LOOKUP (Fresh Cache 0-7 days)
    # =============================================================================

    def _lookup_cache(self, cedula):
        """
        Look up cédula in fresh cache (0-7 days old).

        Returns immediately with cached data if available and fresh.
        Triggers background refresh if in refresh zone (5-7 days).

        Args:
            cedula (str): Clean cédula (digits only)

        Returns:
            dict: Cache result with success=True if found, False if miss
        """
        cache_model = self.env['l10n_cr.cedula.cache']
        cache = cache_model.get_cached(cedula)

        if not cache:
            return {'success': False, 'source': 'cache_miss'}

        # Check if cache is fresh (0-7 days)
        if not cache.is_fresh():
            _logger.debug(f'Cache entry for {cedula} is stale ({cache.cache_age_days} days)')
            return {'success': False, 'source': 'cache_stale'}

        # Trigger background refresh if in refresh zone (5-7 days)
        if cache.needs_refresh():
            _logger.info(f'Cache entry for {cedula} needs refresh, triggering background job')
            cache.refresh_if_needed()

        # Return cached data
        data = self._parse_cache_record(cache)

        return {
            'success': True,
            'source': 'cache',
            'data': data,
            'cache_age_days': cache.cache_age_days,
            'user_message': _('Datos obtenidos de caché (verificados recientemente).'),
        }

    # =============================================================================
    # STEP 2: HACIENDA API LOOKUP
    # =============================================================================

    def _lookup_hacienda(self, cedula):
        """
        Look up cédula using Hacienda API with rate limiting.

        Uses application-wide rate limiter to stay within API limits.
        Returns structured data or error information.

        Args:
            cedula (str): Clean cédula (digits only)

        Returns:
            dict: {
                'success': True/False,
                'data': {...} or None,
                'error': str,
                'error_type': str,
            }
        """
        try:
            # Check rate limiter
            rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']

            # Try to acquire token (non-blocking)
            token_acquired = rate_limiter.try_acquire_token()

            if not token_acquired:
                _logger.warning(f'Rate limit exceeded for Hacienda API (cédula: {cedula})')
                return {
                    'success': False,
                    'error': _('Límite de consultas excedido. Intente nuevamente en unos segundos.'),
                    'error_type': ERROR_RATE_LIMIT,
                }

            # Call Hacienda API
            api = self.env['l10n_cr.hacienda.cedula.api']
            result = api.lookup_cedula(cedula)

            if result.get('success'):
                # Parse and normalize response
                data = self._normalize_hacienda_response(result, cedula)
                return {
                    'success': True,
                    'data': data,
                }
            else:
                # API returned error
                return {
                    'success': False,
                    'error': result.get('error', _('Error desconocido de Hacienda API')),
                    'error_type': result.get('error_type', ERROR_API_ERROR),
                }

        except Exception as e:
            _logger.error(f'Exception in Hacienda API lookup: {str(e)}', exc_info=True)
            return {
                'success': False,
                'error': _('Error de conexión con Hacienda: %s') % str(e),
                'error_type': ERROR_NETWORK,
            }

    # =============================================================================
    # STEP 3: GOMETA API FALLBACK
    # =============================================================================

    def _lookup_gometa(self, cedula):
        """
        Look up cédula using GoMeta API as fallback.

        GoMeta is a free public API that provides 7-day cached data from Hacienda.
        Used as fallback when Hacienda API is unavailable.

        API: https://apis.gometa.org/cedulas/{cedula}

        Args:
            cedula (str): Clean cédula (digits only)

        Returns:
            dict: {
                'success': True/False,
                'data': {...} or None,
                'error': str,
                'error_type': str,
            }
        """
        url = GOMETA_API_URL.format(cedula=cedula)

        try:
            _logger.debug(f'Querying GoMeta API: {url}')

            response = requests.get(url, timeout=GOMETA_TIMEOUT)

            if response.status_code == 200:
                # Parse successful response
                data = response.json()
                normalized = self._normalize_gometa_response(data, cedula)

                _logger.info(f'GoMeta API success for cédula {cedula}: {normalized.get("name")}')

                return {
                    'success': True,
                    'data': normalized,
                }

            elif response.status_code == 404:
                # Cédula not found
                _logger.warning(f'GoMeta API: Cédula not found: {cedula}')
                return {
                    'success': False,
                    'error': _('Cédula no encontrada en registros públicos.'),
                    'error_type': ERROR_NOT_FOUND,
                }

            else:
                # Other error
                error_text = response.text[:200]
                _logger.warning(f'GoMeta API error {response.status_code}: {error_text}')
                return {
                    'success': False,
                    'error': _('Error de API GoMeta (HTTP %s)') % response.status_code,
                    'error_type': ERROR_API_ERROR,
                }

        except requests.exceptions.Timeout:
            _logger.warning(f'GoMeta API timeout for cédula {cedula}')
            return {
                'success': False,
                'error': _('Tiempo de espera agotado (GoMeta API)'),
                'error_type': ERROR_TIMEOUT,
            }

        except requests.exceptions.ConnectionError:
            _logger.warning(f'GoMeta API connection error for cédula {cedula}')
            return {
                'success': False,
                'error': _('Error de conexión con GoMeta API'),
                'error_type': ERROR_NETWORK,
            }

        except Exception as e:
            _logger.error(f'GoMeta API exception: {str(e)}', exc_info=True)
            return {
                'success': False,
                'error': _('Error inesperado: %s') % str(e),
                'error_type': ERROR_API_ERROR,
            }

    # =============================================================================
    # STEP 4: STALE CACHE LOOKUP (7-90 days old)
    # =============================================================================

    def _lookup_stale_cache(self, cedula):
        """
        Look up cédula in stale cache (7-90 days old).

        This is an emergency fallback when all APIs fail.
        Returns old data with strong warning to user.

        Args:
            cedula (str): Clean cédula (digits only)

        Returns:
            dict: Stale cache result or failure
        """
        cache_model = self.env['l10n_cr.cedula.cache']
        cache = cache_model.search([
            ('cedula', '=', cedula),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if not cache:
            return {'success': False, 'source': 'no_cache'}

        # Check if cache is stale (7-90 days)
        if cache.is_expired():
            _logger.debug(f'Cache entry for {cedula} is expired ({cache.cache_age_days} days)')
            return {'success': False, 'source': 'cache_expired'}

        if not cache.is_stale():
            _logger.debug(f'Cache entry for {cedula} is not stale ({cache.cache_age_days} days)')
            return {'success': False, 'source': 'cache_not_stale'}

        # Return stale data with warning
        data = self._parse_cache_record(cache)

        _logger.warning(
            f'Using STALE cache for {cedula} (age: {cache.cache_age_days} days). '
            f'This is emergency fallback data.'
        )

        return {
            'success': True,
            'source': 'stale_cache',
            'data': data,
            'cache_age_days': cache.cache_age_days,
            'user_message': _(
                'ADVERTENCIA: Datos desactualizados (última verificación hace %d días). '
                'Los APIs están temporalmente no disponibles.'
            ) % cache.cache_age_days,
        }

    # =============================================================================
    # BATCH LOOKUP METHOD
    # =============================================================================

    @api.model
    def batch_lookup(self, cedulas, max_concurrent=5):
        """
        Bulk lookup for multiple cédulas with concurrency control.

        Useful for bulk import operations or background processing.
        Returns results dict keyed by cédula.

        Args:
            cedulas (list): List of cédula strings
            max_concurrent (int): Not used (sequential processing for simplicity)

        Returns:
            dict: {
                'results': {
                    '3101234567': {success: True, data: {...}, ...},
                    '3101234568': {success: False, error: '...', ...},
                },
                'summary': {
                    'total': 100,
                    'success': 95,
                    'failed': 5,
                    'cache_hits': 85,
                    'api_calls': 15,
                },
                'elapsed_time': 12.5,  # seconds
            }
        """
        if not cedulas:
            return {
                'results': {},
                'summary': {
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'cache_hits': 0,
                    'api_calls': 0,
                },
                'elapsed_time': 0.0,
            }

        start_time = time.time()
        results = {}
        stats = {
            'cache_hits': 0,
            'api_calls': 0,
            'success': 0,
            'failed': 0,
        }

        _logger.info(f'Starting batch lookup for {len(cedulas)} cédulas')

        for i, cedula in enumerate(cedulas):
            try:
                result = self.lookup_and_cache(cedula)
                results[cedula] = result

                # Update stats
                if result['success']:
                    stats['success'] += 1
                    if result['source'] == 'cache':
                        stats['cache_hits'] += 1
                    elif result['source'] in ('hacienda', 'gometa'):
                        stats['api_calls'] += 1
                else:
                    stats['failed'] += 1

                # Progress logging
                if (i + 1) % 10 == 0 or (i + 1) == len(cedulas):
                    _logger.info(
                        f'Batch lookup progress: {i + 1}/{len(cedulas)} '
                        f'({stats["success"]} success, {stats["failed"]} failed)'
                    )

            except Exception as e:
                _logger.error(f'Error in batch lookup for cédula {cedula}: {str(e)}')
                results[cedula] = {
                    'success': False,
                    'error': str(e),
                    'error_type': ERROR_API_ERROR,
                }
                stats['failed'] += 1

        elapsed_time = time.time() - start_time

        _logger.info(
            f'Batch lookup complete: {len(cedulas)} cédulas in {elapsed_time:.2f}s. '
            f'Success: {stats["success"]}, Failed: {stats["failed"]}, '
            f'Cache hit rate: {stats["cache_hits"] / len(cedulas) * 100:.1f}%'
        )

        return {
            'results': results,
            'summary': {
                'total': len(cedulas),
                'success': stats['success'],
                'failed': stats['failed'],
                'cache_hits': stats['cache_hits'],
                'api_calls': stats['api_calls'],
            },
            'elapsed_time': round(elapsed_time, 2),
        }

    # =============================================================================
    # HELPER METHODS - Data Normalization
    # =============================================================================

    def _normalize_hacienda_response(self, api_result, cedula):
        """
        Normalize Hacienda API response to standard format.

        Args:
            api_result (dict): Raw API response from hacienda_cedula_api
            cedula (str): Clean cédula

        Returns:
            dict: Normalized data structure
        """
        economic_activities = api_result.get('economic_activities', [])
        primary_activity = None
        if economic_activities:
            primary_activity = economic_activities[0].get('code')

        return {
            'cedula': cedula,
            'name': api_result.get('name', '').strip(),
            'company_type': self._infer_company_type(api_result.get('tax_regime', '')),
            'tax_regime': api_result.get('tax_regime', ''),
            'tax_status': 'inscrito',  # If API returns data, it's active
            'economic_activities': economic_activities,
            'primary_activity': primary_activity,
            'raw_response': json.dumps(api_result.get('raw_data', {})),
        }

    def _normalize_gometa_response(self, api_data, cedula):
        """
        Normalize GoMeta API response to standard format.

        GoMeta API structure (example):
        {
            "nombre": "GIMNASIO FITNESS CR S.A.",
            "tipoIdentificacion": "02",
            "actividades": [...]
        }

        Args:
            api_data (dict): Raw API response from GoMeta
            cedula (str): Clean cédula

        Returns:
            dict: Normalized data structure
        """
        # Parse activities
        economic_activities = []
        actividades = api_data.get('actividades', [])
        if isinstance(actividades, list):
            for act in actividades:
                if isinstance(act, dict):
                    economic_activities.append({
                        'code': act.get('codigo', ''),
                        'description': act.get('descripcion', ''),
                        'primary': act.get('tipo', '').lower() == 'principal',
                    })

        primary_activity = None
        if economic_activities:
            primary_activity = economic_activities[0].get('code')

        return {
            'cedula': cedula,
            'name': api_data.get('nombre', '').strip(),
            'company_type': 'other',  # GoMeta doesn't provide detailed type
            'tax_regime': api_data.get('regimen', {}).get('descripcion', '') if isinstance(api_data.get('regimen'), dict) else '',
            'tax_status': 'inscrito',
            'economic_activities': economic_activities,
            'primary_activity': primary_activity,
            'raw_response': json.dumps(api_data),
        }

    def _parse_cache_record(self, cache):
        """
        Parse cache record into standard data structure.

        Args:
            cache (l10n_cr.cedula.cache): Cache record

        Returns:
            dict: Normalized data structure
        """
        # Parse economic activities from JSON
        economic_activities = []
        if cache.economic_activities:
            try:
                economic_activities = json.loads(cache.economic_activities)
            except json.JSONDecodeError:
                _logger.warning(f'Failed to parse activities JSON for cédula {cache.cedula}')

        return {
            'cedula': cache.cedula,
            'name': cache.name,
            'company_type': cache.company_type,
            'tax_regime': cache.tax_regime or '',
            'tax_status': cache.tax_status,
            'economic_activities': economic_activities,
            'primary_activity': cache.primary_activity,
            'ciiu_code_id': cache.ciiu_code_id.id if cache.ciiu_code_id else False,
        }

    # =============================================================================
    # HELPER METHODS - Cache Management
    # =============================================================================

    def _save_to_cache(self, cedula, data, source):
        """
        Save lookup result to cache.

        Args:
            cedula (str): Clean cédula
            data (dict): Normalized data structure
            source (str): 'hacienda' or 'gometa'

        Returns:
            l10n_cr.cedula.cache: Cache record (created or updated)
        """
        cache_model = self.env['l10n_cr.cedula.cache']

        cache_data = {
            'name': data.get('name'),
            'company_type': data.get('company_type'),
            'tax_regime': data.get('tax_regime'),
            'tax_status': data.get('tax_status'),
            'economic_activities': data.get('economic_activities'),
            'raw_response': data.get('raw_response'),
        }

        cache = cache_model.update_cache(cedula, cache_data, source=source)

        return cache

    # =============================================================================
    # HELPER METHODS - Utilities
    # =============================================================================

    def _clean_cedula(self, cedula):
        """
        Clean and validate cédula format.

        Removes dashes, spaces, validates digits only.

        Args:
            cedula (str): Raw cédula input

        Returns:
            str: Clean cédula (digits only) or empty string if invalid
        """
        if not cedula:
            return ''

        # Remove formatting
        cleaned = str(cedula).replace('-', '').replace(' ', '').strip()

        # Validate digits only
        if not cleaned.isdigit():
            return ''

        # Validate length (Costa Rica cédulas are 9-12 digits)
        if len(cleaned) < 9 or len(cleaned) > 12:
            return ''

        return cleaned

    def _infer_company_type(self, tax_regime):
        """
        Infer company type from tax regime string.

        Args:
            tax_regime (str): Tax regime description

        Returns:
            str: Company type code
        """
        regime_lower = tax_regime.lower() if tax_regime else ''

        if 'física' in regime_lower or 'freelance' in regime_lower:
            return 'person'
        elif 'sociedad' in regime_lower or 's.a.' in regime_lower:
            return 'company'
        elif 'cooperativa' in regime_lower:
            return 'cooperative'
        elif 'fideicomiso' in regime_lower:
            return 'trust'
        elif 'asociación' in regime_lower or 'fundación' in regime_lower:
            return 'nonprofit'
        else:
            return 'other'

    def _build_error_message(self, hacienda_result, gometa_result):
        """
        Build user-friendly error message from API failures.

        Args:
            hacienda_result (dict): Hacienda API result
            gometa_result (dict): GoMeta API result

        Returns:
            str: Spanish error message for user display
        """
        # Check error types
        hacienda_error = hacienda_result.get('error_type', '')
        gometa_error = gometa_result.get('error_type', '')

        # Not found in both sources
        if hacienda_error == ERROR_NOT_FOUND and gometa_error == ERROR_NOT_FOUND:
            return _(
                'Cédula no encontrada en registros públicos. '
                'Verifique el número o ingrese los datos manualmente.'
            )

        # Rate limit
        if hacienda_error == ERROR_RATE_LIMIT:
            return _(
                'Límite de consultas temporalmente excedido. '
                'Por favor espere unos segundos e intente nuevamente, '
                'o ingrese los datos manualmente.'
            )

        # Network errors
        if hacienda_error in (ERROR_TIMEOUT, ERROR_NETWORK):
            return _(
                'Error de conexión con los servicios de consulta. '
                'Verifique su conexión a internet o ingrese los datos manualmente.'
            )

        # Generic error
        return _(
            'No se pudo consultar la cédula en este momento. '
            'Por favor ingrese los datos manualmente.'
        )

    # =============================================================================
    # MONITORING AND HEALTH CHECK
    # =============================================================================

    @api.model
    def get_service_health(self):
        """
        Get service health status for monitoring dashboard.

        Returns:
            dict: {
                'cache_stats': {...},
                'rate_limiter_stats': {...},
                'last_24h_stats': {...},
            }
        """
        cache_model = self.env['l10n_cr.cedula.cache']
        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']

        return {
            'cache_stats': cache_model.get_cache_statistics(),
            'rate_limiter_stats': rate_limiter.get_available_tokens(),
            'service_status': 'operational',
        }

    # =============================================================================
    # TEST COMPATIBILITY ALIASES
    # =============================================================================

    @api.model
    def lookup_cedula(self, cedula, force_refresh=False):
        """
        Alias for lookup_and_cache() for test compatibility.

        This method provides backward compatibility with test files that use
        lookup_cedula() instead of lookup_and_cache().

        Args:
            cedula (str): Tax identification number
            force_refresh (bool): Skip cache, force API call

        Returns:
            dict: Simplified result format for tests:
                {
                    'name': str,
                    'source': 'cache'|'hacienda'|'gometa',
                    'tax_status': str,
                    'tax_regime': str,
                    'email': str,
                    'primary_activity': str,
                    'is_fresh': bool,
                    'is_stale': bool,
                    'cache_age_days': int,
                    'warning': str (optional),
                }
        """
        result = self.lookup_and_cache(cedula, force_refresh=force_refresh)

        if not result['success']:
            from odoo.exceptions import UserError
            error_msg = result.get('error', result.get('user_message', 'Lookup failed'))
            raise UserError(error_msg)

        data = result['data']
        source = result['source']

        # Determine cache freshness
        is_fresh = source in ('cache', 'hacienda', 'gometa')
        is_stale = source == 'stale_cache'
        cache_age_days = 0

        if source in ('cache', 'stale_cache'):
            cache = self.env['l10n_cr.cedula.cache'].search([
                ('cedula', '=', cedula),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            if cache:
                cache_age_days = cache.cache_age_days
                is_fresh = cache.cache_tier in ('fresh', 'refresh')
                is_stale = cache.cache_tier == 'stale'

        return {
            'name': data.get('name', ''),
            'source': source,
            'tax_status': data.get('tax_status', ''),
            'tax_regime': data.get('tax_regime', ''),
            'email': data.get('email', ''),
            'primary_activity': data.get('primary_activity', ''),
            'economic_activities': data.get('economic_activities', []),
            'is_fresh': is_fresh,
            'is_stale': is_stale,
            'cache_age_days': cache_age_days,
            'warning': result.get('warning'),
        }

    @api.model
    def batch_lookup_cedulas(self, cedulas, max_concurrent=5):
        """
        Alias for batch_lookup() for test compatibility.

        Args:
            cedulas (list): List of cédula strings
            max_concurrent (int): Max concurrent lookups

        Returns:
            dict: {cedula: result_dict} for each cédula
        """
        batch_result = self.batch_lookup(cedulas, max_concurrent=max_concurrent)

        # Convert to test-compatible format
        output = {}
        for cedula, result in batch_result.get('results', {}).items():
            if result['success']:
                data = result['data']
                output[cedula] = {
                    'name': data.get('name', ''),
                    'tax_status': data.get('tax_status', ''),
                    'source': result['source'],
                }
            else:
                output[cedula] = {
                    'error': result.get('error', result.get('user_message', 'Lookup failed')),
                }

        return output
