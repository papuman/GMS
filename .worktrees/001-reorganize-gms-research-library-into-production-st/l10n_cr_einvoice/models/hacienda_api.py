# -*- coding: utf-8 -*-
import base64
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
INITIAL_RETRY_DELAY = 2  # seconds
RETRY_BACKOFF_FACTOR = 2  # exponential backoff multiplier


class HaciendaAPI(models.AbstractModel):
    _name = 'l10n_cr.hacienda.api'
    _description = 'Costa Rica Hacienda API Client'

    # API Endpoints
    PRODUCTION_URL = 'https://api.comprobanteselectronicos.go.cr/recepcion/v1'
    SANDBOX_URL = 'https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1'

    @api.model
    def _get_base_url(self):
        """Get the base URL for API calls based on environment."""
        company = self.env.company

        if company.l10n_cr_hacienda_env == 'production':
            return self.PRODUCTION_URL
        else:
            return self.SANDBOX_URL

    @api.model
    def _get_auth_headers(self):
        """Get authentication headers for API requests."""
        company = self.env.company

        if not company.l10n_cr_hacienda_username or not company.l10n_cr_hacienda_password:
            raise UserError(_('Hacienda API credentials not configured. Please check company settings.'))

        # Basic authentication
        credentials = f"{company.l10n_cr_hacienda_username}:{company.l10n_cr_hacienda_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
        }

        return headers

    @api.model
    def submit_invoice(self, clave, xml_content, sender_id, receiver_id):
        """
        Submit an electronic invoice to Hacienda with retry logic.

        Args:
            clave (str): 50-digit electronic document key
            xml_content (str): Signed XML content
            sender_id (str): Sender's cedula/identification
            receiver_id (str): Receiver's cedula/identification

        Returns:
            dict: Response from Hacienda API with structure:
                - ind-estado: 'aceptado' | 'rechazado' | 'procesando'
                - respuesta-xml: Response message (may be base64 encoded)
                - error details if applicable

        Raises:
            UserError: On authentication, validation, or permanent API errors
        """
        # Encode XML to base64
        xml_base64 = base64.b64encode(xml_content.encode('utf-8')).decode('utf-8')

        # Clean and format identification numbers
        sender_clean = (sender_id or '').replace('-', '').replace(' ', '')
        receiver_clean = (receiver_id or '').replace('-', '').replace(' ', '') if receiver_id else ''

        # Prepare payload according to Hacienda API specification
        payload = {
            'clave': clave,
            'fecha': datetime.now().strftime('%Y-%m-%dT%H:%M:%S-06:00'),  # Costa Rica timezone
            'emisor': {
                'tipoIdentificacion': self.get_id_type(sender_clean),
                'numeroIdentificacion': sender_clean,
            },
            'receptor': {
                'tipoIdentificacion': self.get_id_type(receiver_clean) if receiver_clean else '05',
                'numeroIdentificacion': receiver_clean or '000000000000',
            },
            'comprobanteXml': xml_base64,
        }

        # Submit with retry logic
        return self._make_request_with_retry(
            method='POST',
            endpoint='/recepcion',
            payload=payload,
            operation=f'submit invoice {clave}'
        )

    @api.model
    def check_status(self, clave):
        """
        Check the status of a submitted document with retry logic.

        Args:
            clave (str): 50-digit electronic document key

        Returns:
            dict: Status response from Hacienda with structure:
                - ind-estado: Document status
                  * 'aceptado': Document accepted
                  * 'rechazado': Document rejected
                  * 'procesando': Still processing
                  * 'recibido': Received but not processed
                - respuesta-xml: Response XML (base64 encoded)
                - detalle-mensaje: Error details if rejected

        Raises:
            UserError: On connection or API errors
        """
        if not clave or len(clave) != 50:
            raise UserError(_('Invalid clave format. Must be 50 digits.'))

        # Query status with retry logic
        return self._make_request_with_retry(
            method='GET',
            endpoint=f'/recepcion/{clave}',
            payload=None,
            operation=f'check status for {clave}'
        )

    @api.model
    def _make_request_with_retry(self, method, endpoint, payload, operation):
        """
        Make HTTP request with exponential backoff retry logic.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint path
            payload (dict): Request payload (None for GET)
            operation (str): Description of operation for logging

        Returns:
            dict: Parsed response from API

        Raises:
            UserError: On authentication errors, validation errors, or max retries exceeded
        """
        base_url = self._get_base_url()
        url = f"{base_url}{endpoint}"
        headers = self._get_auth_headers()

        last_error = None
        retry_delay = INITIAL_RETRY_DELAY

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                _logger.info(f'Attempt {attempt}/{MAX_RETRY_ATTEMPTS}: {operation}')

                # Make HTTP request
                if method == 'POST':
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                elif method == 'GET':
                    response = requests.get(url, headers=headers, timeout=30)
                else:
                    raise UserError(_('Unsupported HTTP method: %s') % method)

                # Log request details
                _logger.debug(f'Request URL: {url}')
                _logger.debug(f'Response status: {response.status_code}')
                _logger.debug(f'Response body: {response.text[:500]}...')

                # Handle different status codes
                if response.status_code in [200, 201]:
                    # Success
                    parsed_response = self._parse_response(response)
                    _logger.info(f'Successfully completed: {operation}')
                    return parsed_response

                elif response.status_code == 400:
                    # Bad Request - validation error, don't retry
                    error_msg = self._parse_error(response)
                    _logger.error(f'Validation error for {operation}: {error_msg}')
                    raise UserError(_('Validation error: %s') % error_msg)

                elif response.status_code == 401:
                    # Unauthorized - authentication error, don't retry
                    _logger.error(f'Authentication failed for {operation}')
                    raise UserError(_('Authentication failed. Please check API credentials.'))

                elif response.status_code == 403:
                    # Forbidden - authorization error, don't retry
                    error_msg = self._parse_error(response)
                    _logger.error(f'Authorization error for {operation}: {error_msg}')
                    raise UserError(_('Authorization error: %s') % error_msg)

                elif response.status_code == 404:
                    # Not Found - resource doesn't exist, don't retry
                    _logger.error(f'Resource not found for {operation}')
                    raise UserError(_('Document not found in Hacienda system.'))

                elif response.status_code == 429:
                    # Rate limiting - retry with longer delay
                    _logger.warning(f'Rate limited on attempt {attempt} for {operation}')
                    last_error = 'Rate limit exceeded'
                    retry_delay = retry_delay * 2  # Double the delay for rate limits

                elif response.status_code >= 500:
                    # Server error - retry
                    error_msg = self._parse_error(response)
                    _logger.warning(f'Server error on attempt {attempt} for {operation}: {error_msg}')
                    last_error = f'Server error: {error_msg}'

                else:
                    # Other errors - retry
                    error_msg = self._parse_error(response)
                    _logger.warning(f'Error {response.status_code} on attempt {attempt} for {operation}: {error_msg}')
                    last_error = error_msg

            except requests.exceptions.Timeout as e:
                # Timeout - retry
                _logger.warning(f'Timeout on attempt {attempt} for {operation}: {str(e)}')
                last_error = f'Request timeout: {str(e)}'

            except requests.exceptions.ConnectionError as e:
                # Connection error - retry
                _logger.warning(f'Connection error on attempt {attempt} for {operation}: {str(e)}')
                last_error = f'Connection error: {str(e)}'

            except requests.exceptions.RequestException as e:
                # Other request exceptions - retry
                _logger.warning(f'Request error on attempt {attempt} for {operation}: {str(e)}')
                last_error = f'Request error: {str(e)}'

            # Wait before retrying (except on last attempt)
            if attempt < MAX_RETRY_ATTEMPTS:
                _logger.info(f'Retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
                retry_delay = retry_delay * RETRY_BACKOFF_FACTOR  # Exponential backoff

        # All retries exhausted
        error_message = _('Failed after %d attempts. Last error: %s') % (MAX_RETRY_ATTEMPTS, last_error)
        _logger.error(f'{operation} - {error_message}')
        raise UserError(error_message)

    @api.model
    def get_id_type(self, identification):
        """
        Determine the identification type based on the number format.

        Types:
        01 - Cédula Física (9 digits)
        02 - Cédula Jurídica (10 digits)
        03 - DIMEX (11-12 digits)
        04 - NITE (10 digits)
        05 - Extranjero (variable)
        """
        if not identification:
            return '05'

        # Remove dashes and spaces
        clean_id = identification.replace('-', '').replace(' ', '')
        length = len(clean_id)

        if length == 9:
            return '01'  # Cédula Física
        elif length == 10:
            # Could be Cédula Jurídica or NITE
            # Cédula Jurídica typically starts with 3
            if clean_id.startswith('3'):
                return '02'
            else:
                return '04'
        elif length in [11, 12]:
            return '03'  # DIMEX
        else:
            return '05'  # Extranjero

    @api.model
    def _parse_response(self, response):
        """
        Parse successful API response with enhanced error handling.

        Expected response structure from Hacienda:
        {
            "clave": "50-digit key",
            "fecha": "timestamp",
            "ind-estado": "aceptado|rechazado|procesando|recibido",
            "respuesta-xml": "base64 encoded XML or message"
        }

        Returns:
            dict: Normalized response dictionary
        """
        try:
            data = response.json()

            # Decode respuesta-xml if it's base64 encoded
            if 'respuesta-xml' in data and data['respuesta-xml']:
                try:
                    # Try to decode as base64
                    decoded = base64.b64decode(data['respuesta-xml']).decode('utf-8')
                    # Store both encoded and decoded versions
                    data['respuesta-xml-decoded'] = decoded
                except Exception:
                    # Not base64 or decoding failed, keep as-is
                    pass

            # Normalize status field
            estado = data.get('ind-estado', '').lower()
            if estado:
                data['ind-estado'] = estado

            # Extract error details if present
            if 'detalle-mensaje' in data:
                data['error_details'] = data['detalle-mensaje']

            _logger.debug(f"Parsed response - Estado: {data.get('ind-estado')}")

            return data

        except json.JSONDecodeError as e:
            _logger.warning(f'Failed to parse JSON response: {str(e)}')
            # Return raw text as error
            return {
                'ind-estado': 'error',
                'respuesta-xml': response.text,
                'error_details': f'Invalid JSON response: {str(e)}',
            }

    @api.model
    def _parse_error(self, response):
        """
        Parse error response from API with comprehensive error extraction.

        Handles various error response formats from Hacienda API.

        Returns:
            str: Human-readable error message
        """
        try:
            error_data = response.json()

            # Try multiple possible error field names
            error_fields = [
                'message',
                'error',
                'mensaje',
                'detalle-mensaje',
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
            return error_text[:500]  # Limit length

    @api.model
    def get_acceptance_message(self, clave):
        """
        Get the acceptance or rejection message (respuesta) for a document.

        This is used when a document has been accepted/rejected and you need
        to retrieve the official response message from Hacienda.

        Args:
            clave (str): 50-digit electronic document key

        Returns:
            dict: Response with decoded acceptance/rejection message
        """
        response = self.check_status(clave)

        # Decode the respuesta-xml if present
        if 'respuesta-xml-decoded' in response:
            return {
                'clave': clave,
                'estado': response.get('ind-estado'),
                'mensaje': response.get('respuesta-xml-decoded'),
                'mensaje-base64': response.get('respuesta-xml'),
            }
        else:
            return {
                'clave': clave,
                'estado': response.get('ind-estado'),
                'mensaje': response.get('respuesta-xml', 'No message available'),
            }

    @api.model
    def is_accepted(self, response):
        """
        Check if a response indicates document acceptance.

        Args:
            response (dict): API response

        Returns:
            bool: True if document is accepted
        """
        estado = response.get('ind-estado', '').lower()
        return estado == 'aceptado'

    @api.model
    def is_rejected(self, response):
        """
        Check if a response indicates document rejection.

        Args:
            response (dict): API response

        Returns:
            bool: True if document is rejected
        """
        estado = response.get('ind-estado', '').lower()
        return estado == 'rechazado'

    @api.model
    def is_processing(self, response):
        """
        Check if a response indicates document is still processing.

        Args:
            response (dict): API response

        Returns:
            bool: True if document is still being processed
        """
        estado = response.get('ind-estado', '').lower()
        return estado in ['procesando', 'recibido']

    @api.model
    def test_connection(self):
        """
        Test the connection to Hacienda API with credential validation.

        Returns:
            dict: Connection test result with success status and message
        """
        try:
            # Validate credentials are configured
            company = self.env.company
            if not company.l10n_cr_hacienda_username or not company.l10n_cr_hacienda_password:
                return {
                    'success': False,
                    'message': _('API credentials not configured'),
                    'environment': company.l10n_cr_hacienda_env,
                }

            base_url = self._get_base_url()
            headers = self._get_auth_headers()

            # Make a simple GET request to check connectivity
            # Use a non-existent endpoint to test auth without side effects
            response = requests.get(f"{base_url}/recepcion/test", headers=headers, timeout=10)

            # 404 means endpoint doesn't exist but auth worked
            # 401 means auth failed
            if response.status_code == 404:
                return {
                    'success': True,
                    'message': _('Connection successful - Credentials validated'),
                    'environment': company.l10n_cr_hacienda_env,
                    'url': base_url,
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': _('Authentication failed - Invalid credentials'),
                    'environment': company.l10n_cr_hacienda_env,
                }
            elif response.status_code == 200:
                return {
                    'success': True,
                    'message': _('Connection successful'),
                    'environment': company.l10n_cr_hacienda_env,
                    'url': base_url,
                }
            else:
                return {
                    'success': False,
                    'message': _('Connection failed: HTTP %s') % response.status_code,
                    'environment': company.l10n_cr_hacienda_env,
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': _('Connection timeout - Server not responding'),
            }
        except requests.exceptions.ConnectionError as e:
            return {
                'success': False,
                'message': _('Connection error: %s') % str(e),
            }
        except Exception as e:
            return {
                'success': False,
                'message': _('Error: %s') % str(e),
            }
