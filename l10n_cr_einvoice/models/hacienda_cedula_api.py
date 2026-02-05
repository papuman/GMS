# -*- coding: utf-8 -*-
import json
import logging
import requests
import time
from datetime import datetime

from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 1  # seconds
RETRY_BACKOFF_FACTOR = 2  # exponential backoff multiplier
CONNECTION_TIMEOUT = 5  # seconds


class HaciendaCedulaAPI(models.AbstractModel):
    """
    Costa Rica Hacienda Cédula Lookup API Client.

    Free public API for looking up company information by cédula (tax ID).
    No authentication required.

    Rate Limits:
        - 10 requests/second sustained
        - 20 requests/second burst

    API Documentation:
        - Endpoint: https://api.hacienda.go.cr/fe/ae
        - Query parameter: identificacion={cedula}
        - Returns: company name, tax regime, economic activities (CIIU codes)
    """
    _name = 'l10n_cr.hacienda.cedula.api'
    _description = 'Costa Rica Hacienda Cédula Lookup API Client'

    # API Endpoint (production only - no sandbox available)
    CEDULA_API_URL = 'https://api.hacienda.go.cr/fe/ae'

    @api.model
    def lookup_cedula(self, cedula):
        """
        Look up company information by cédula from Hacienda API.

        This is a free public API that returns basic taxpayer information
        registered with the Costa Rica Tax Authority (Hacienda).

        Args:
            cedula (str): Tax identification number (cédula). Can be formatted
                         (e.g. '3-101-234567') or unformatted ('3101234567').

        Returns:
            dict: Company information with structure:
                {
                    'success': True,
                    'cedula': '3101234567',
                    'name': 'GIMNASIO FITNESS CR S.A.',
                    'tax_regime': 'Régimen General',
                    'economic_activities': [
                        {
                            'code': '931100',
                            'description': 'Actividades de gimnasios',
                            'primary': True
                        },
                        ...
                    ],
                    'response_time': 0.523,  # seconds
                }

                On error:
                {
                    'success': False,
                    'cedula': '3101234567',
                    'error': 'Error message',
                    'error_type': 'not_found' | 'rate_limit' | 'network' | 'timeout' | 'api_error'
                }

        Raises:
            UserError: On invalid cedula format only (API errors returned in dict)
        """
        # Validate and clean cedula
        cedula_clean = self._clean_cedula(cedula)

        if not cedula_clean:
            raise UserError(_('Invalid cédula format. Cédula must contain only digits.'))

        _logger.info(f'Looking up cédula: {cedula_clean}')

        # Make API request with retry logic
        start_time = time.time()
        result = self._make_request_with_retry(cedula_clean)
        response_time = time.time() - start_time

        # Add response time to result
        result['response_time'] = round(response_time, 3)
        result['cedula'] = cedula_clean

        return result

    @api.model
    def _clean_cedula(self, cedula):
        """
        Clean and validate cédula format.

        Removes dashes, spaces, and validates that result contains only digits.

        Args:
            cedula (str): Raw cédula input

        Returns:
            str: Cleaned cédula (digits only) or empty string if invalid
        """
        if not cedula:
            return ''

        # Remove common formatting characters
        cleaned = str(cedula).replace('-', '').replace(' ', '').strip()

        # Validate that result contains only digits
        if not cleaned.isdigit():
            return ''

        return cleaned

    @api.model
    def _make_request_with_retry(self, cedula):
        """
        Make HTTP request to Hacienda API with exponential backoff retry logic.

        Handles:
            - Network timeouts (5 second timeout)
            - Connection errors
            - Rate limiting (429 errors)
            - API errors (4xx, 5xx)
            - Exponential backoff between retries

        Args:
            cedula (str): Clean cédula (digits only)

        Returns:
            dict: Parsed API response or error information
        """
        url = f'{self.CEDULA_API_URL}?identificacion={cedula}'

        last_error = None
        last_error_type = 'api_error'
        retry_delay = INITIAL_RETRY_DELAY

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                _logger.debug(f'Attempt {attempt}/{MAX_RETRY_ATTEMPTS}: Querying {url}')

                # Make HTTP GET request with timeout
                response = requests.get(url, timeout=CONNECTION_TIMEOUT)

                # Log response details
                _logger.debug(f'Response status: {response.status_code}')
                _logger.debug(f'Response body: {response.text[:500]}...')

                # Handle different status codes
                if response.status_code == 200:
                    # Success - parse and return data
                    return self._parse_success_response(response, cedula)

                elif response.status_code == 404:
                    # Cédula not found in Hacienda registry
                    _logger.warning(f'Cédula not found: {cedula}')
                    return {
                        'success': False,
                        'error': _('Cédula not found in Hacienda registry. May be invalid or not registered.'),
                        'error_type': 'not_found',
                    }

                elif response.status_code == 429:
                    # Rate limiting - retry with exponential backoff
                    _logger.warning(f'Rate limited on attempt {attempt} for cédula {cedula}')
                    last_error = _('Rate limit exceeded. Too many requests to Hacienda API.')
                    last_error_type = 'rate_limit'
                    # Double the delay for rate limits
                    retry_delay = retry_delay * 2

                elif response.status_code == 400:
                    # Bad request - invalid cedula format
                    error_msg = self._parse_error_response(response)
                    _logger.error(f'Invalid request for cédula {cedula}: {error_msg}')
                    return {
                        'success': False,
                        'error': _('Invalid request: %s') % error_msg,
                        'error_type': 'api_error',
                    }

                elif response.status_code >= 500:
                    # Server error - retry
                    error_msg = self._parse_error_response(response)
                    _logger.warning(f'Server error on attempt {attempt}: {error_msg}')
                    last_error = _('Hacienda API server error: %s') % error_msg
                    last_error_type = 'api_error'

                else:
                    # Other errors - retry
                    error_msg = self._parse_error_response(response)
                    _logger.warning(f'Error {response.status_code} on attempt {attempt}: {error_msg}')
                    last_error = _('API error (HTTP %s): %s') % (response.status_code, error_msg)
                    last_error_type = 'api_error'

            except requests.exceptions.Timeout:
                # Timeout - retry
                _logger.warning(f'Timeout on attempt {attempt} for cédula {cedula}')
                last_error = _('Request timeout after %s seconds') % CONNECTION_TIMEOUT
                last_error_type = 'timeout'

            except requests.exceptions.ConnectionError as e:
                # Connection error - retry
                _logger.warning(f'Connection error on attempt {attempt}: {str(e)}')
                last_error = _('Connection error: Cannot reach Hacienda API')
                last_error_type = 'network'

            except requests.exceptions.RequestException as e:
                # Other request exceptions - retry
                _logger.warning(f'Request error on attempt {attempt}: {str(e)}')
                last_error = _('Request error: %s') % str(e)
                last_error_type = 'network'

            except Exception as e:
                # Unexpected errors - retry
                _logger.error(f'Unexpected error on attempt {attempt}: {str(e)}', exc_info=True)
                last_error = _('Unexpected error: %s') % str(e)
                last_error_type = 'api_error'

            # Wait before retrying (except on last attempt)
            if attempt < MAX_RETRY_ATTEMPTS:
                _logger.info(f'Retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
                retry_delay = retry_delay * RETRY_BACKOFF_FACTOR  # Exponential backoff

        # All retries exhausted
        error_message = _('Failed after %d attempts. Last error: %s') % (MAX_RETRY_ATTEMPTS, last_error)
        _logger.error(f'Cédula lookup failed for {cedula}: {error_message}')

        return {
            'success': False,
            'error': error_message,
            'error_type': last_error_type,
        }

    @api.model
    def _parse_success_response(self, response, cedula):
        """
        Parse successful API response.

        Expected JSON structure from Hacienda API:
        {
            "nombre": "GIMNASIO FITNESS CR S.A.",
            "tipoIdentificacion": "02",
            "regimen": {
                "codigo": "01",
                "descripcion": "Régimen General"
            },
            "actividades": [
                {
                    "codigo": "931100",
                    "descripcion": "Actividades de gimnasios",
                    "tipo": "principal"
                },
                ...
            ]
        }

        Args:
            response: requests.Response object
            cedula (str): Cédula being queried

        Returns:
            dict: Normalized response with company information
        """
        try:
            data = response.json()

            # Extract company name
            name = data.get('nombre', '').strip()

            # Extract tax regime
            regimen = data.get('regimen', {})
            tax_regime = regimen.get('descripcion', '') if isinstance(regimen, dict) else str(regimen)

            # Extract economic activities (CIIU codes)
            economic_activities = []
            actividades = data.get('actividades', [])

            if isinstance(actividades, list):
                for act in actividades:
                    if isinstance(act, dict):
                        economic_activities.append({
                            'code': act.get('codigo', ''),
                            'description': act.get('descripcion', ''),
                            'primary': act.get('tipo', '').lower() == 'principal',
                        })

            _logger.info(f'Successfully retrieved data for cédula {cedula}: {name}')

            return {
                'success': True,
                'name': name,
                'tax_regime': tax_regime,
                'economic_activities': economic_activities,
                'raw_data': data,  # Store raw response for debugging
            }

        except json.JSONDecodeError as e:
            _logger.error(f'Failed to parse JSON response: {str(e)}')
            return {
                'success': False,
                'error': _('Invalid JSON response from API'),
                'error_type': 'api_error',
                'raw_response': response.text[:500],
            }

        except Exception as e:
            _logger.error(f'Error parsing response: {str(e)}', exc_info=True)
            return {
                'success': False,
                'error': _('Error parsing API response: %s') % str(e),
                'error_type': 'api_error',
            }

    @api.model
    def _parse_error_response(self, response):
        """
        Parse error response from API.

        Attempts to extract meaningful error message from various response formats.

        Args:
            response: requests.Response object

        Returns:
            str: Human-readable error message
        """
        try:
            error_data = response.json()

            # Try common error field names
            error_fields = [
                'message',
                'error',
                'mensaje',
                'detalle',
                'descripcion',
                'errorMessage',
            ]

            for field in error_fields:
                if field in error_data and error_data[field]:
                    return str(error_data[field])

            # If error is a list, join messages
            if isinstance(error_data.get('errors'), list):
                return '; '.join([str(e) for e in error_data['errors']])

            # Return entire error object as string
            return str(error_data)

        except json.JSONDecodeError:
            # Not JSON, return raw text
            error_text = response.text or f'HTTP {response.status_code}'
            return error_text[:200]  # Limit length

        except Exception:
            return f'HTTP {response.status_code}'

    @api.model
    def test_connection(self):
        """
        Test connection to Hacienda Cédula API.

        Uses a well-known test cédula to verify API connectivity.

        Returns:
            dict: Connection test result with structure:
                {
                    'success': True/False,
                    'message': 'Connection status message',
                    'response_time': 0.523,  # seconds
                }
        """
        # Use a test cédula (you may want to configure this)
        test_cedula = '3101234567'

        _logger.info('Testing connection to Hacienda Cédula API...')

        try:
            result = self.lookup_cedula(test_cedula)

            if result.get('success'):
                return {
                    'success': True,
                    'message': _('Connection successful - API responding normally'),
                    'response_time': result.get('response_time', 0),
                    'test_cedula': test_cedula,
                }
            else:
                # API responded but lookup failed (expected for test cédula)
                error_type = result.get('error_type', 'unknown')

                if error_type == 'not_found':
                    # This is actually good - API is working, just test cédula doesn't exist
                    return {
                        'success': True,
                        'message': _('Connection successful - API responding (test cédula not found, which is normal)'),
                        'response_time': result.get('response_time', 0),
                    }
                else:
                    return {
                        'success': False,
                        'message': _('Connection failed: %s') % result.get('error', 'Unknown error'),
                        'error_type': error_type,
                    }

        except Exception as e:
            _logger.error(f'Connection test failed: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': _('Connection test failed: %s') % str(e),
            }

    @api.model
    def batch_lookup(self, cedulas):
        """
        Look up multiple cédulas with rate limiting.

        Respects API rate limits (10 req/sec sustained, 20 req/sec burst).
        Adds delays between requests to stay within limits.

        Args:
            cedulas (list): List of cédula strings

        Returns:
            dict: Results keyed by cédula:
                {
                    '3101234567': {success: True, name: '...', ...},
                    '3101234568': {success: False, error: '...'},
                    ...
                }
        """
        if not cedulas:
            return {}

        results = {}
        delay_between_requests = 0.1  # 10 requests/second = 0.1 second delay

        _logger.info(f'Batch lookup for {len(cedulas)} cédulas')

        for i, cedula in enumerate(cedulas):
            try:
                # Look up cédula
                result = self.lookup_cedula(cedula)
                results[cedula] = result

                # Add delay between requests (except for last one)
                if i < len(cedulas) - 1:
                    time.sleep(delay_between_requests)

            except Exception as e:
                _logger.error(f'Error in batch lookup for cédula {cedula}: {str(e)}')
                results[cedula] = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'api_error',
                }

        _logger.info(f'Batch lookup complete: {sum(1 for r in results.values() if r.get("success"))} successful, {sum(1 for r in results.values() if not r.get("success"))} failed')

        return results
