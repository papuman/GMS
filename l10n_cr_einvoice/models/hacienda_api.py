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

# Token cache: {company_id: {'access_token': str, 'refresh_token': str, 'expires_at': float, 'refresh_expires_at': float}}
_TOKEN_CACHE = {}


class HaciendaAPI(models.AbstractModel):
    _name = 'l10n_cr.hacienda.api'
    _description = 'Costa Rica Hacienda API Client'

    # API Endpoints
    PRODUCTION_URL = 'https://api.comprobanteselectronicos.go.cr/recepcion/v1'
    SANDBOX_URL = 'https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1'

    # OAuth2 / IDP Endpoints (Keycloak)
    IDP_SANDBOX_URL = 'https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token'
    IDP_PRODUCTION_URL = 'https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token'

    IDP_CLIENT_ID_SANDBOX = 'api-stag'
    IDP_CLIENT_ID_PRODUCTION = 'api-prod'

    @api.model
    def _get_base_url(self):
        """Get the base URL for API calls based on environment."""
        company = self.env.company

        if company.l10n_cr_hacienda_env == 'production':
            return self.PRODUCTION_URL
        else:
            return self.SANDBOX_URL

    @api.model
    def _get_idp_url(self):
        """Get the IDP token endpoint based on environment."""
        company = self.env.company
        if company.l10n_cr_hacienda_env == 'production':
            return self.IDP_PRODUCTION_URL
        return self.IDP_SANDBOX_URL

    @api.model
    def _get_idp_client_id(self):
        """Get the IDP client ID based on environment."""
        company = self.env.company
        if company.l10n_cr_hacienda_env == 'production':
            return self.IDP_CLIENT_ID_PRODUCTION
        return self.IDP_CLIENT_ID_SANDBOX

    @api.model
    def _obtain_token(self, force_refresh=False):
        """
        Obtain an OAuth2 bearer token from the Hacienda IDP with caching and refresh support.

        Uses a module-level cache keyed by company ID to avoid requesting a new token
        on every API call. Supports refresh_token grant when the access token expires.

        Args:
            force_refresh (bool): If True, ignore cached token and obtain a fresh one.

        Returns:
            str: Access token

        Raises:
            UserError: On authentication failure
        """
        company = self.env.company
        company_id = company.id

        if not company.l10n_cr_active_username or not company.l10n_cr_active_password:
            raise UserError(_('Hacienda API credentials not configured. Please check company settings.'))

        now = time.time()

        # Check cached token (unless forced refresh)
        if not force_refresh and company_id in _TOKEN_CACHE:
            cached = _TOKEN_CACHE[company_id]
            # Return cached access token if still valid
            if cached.get('expires_at', 0) > now:
                return cached['access_token']

            # Try refresh token grant if refresh token is still valid
            if cached.get('refresh_token') and cached.get('refresh_expires_at', 0) > now:
                try:
                    return self._refresh_token(cached['refresh_token'])
                except Exception:
                    _logger.info('Refresh token grant failed, falling back to password grant')
                    # Fall through to full password grant

        # Full password grant
        return self._password_grant()

    @api.model
    def _password_grant(self):
        """Obtain token using password grant and cache the result."""
        company = self.env.company
        idp_url = self._get_idp_url()
        client_id = self._get_idp_client_id()

        data = {
            'grant_type': 'password',
            'client_id': client_id,
            'username': company.l10n_cr_active_username,
            'password': company.l10n_cr_active_password,
        }

        try:
            response = requests.post(idp_url, data=data, timeout=15)
        except requests.exceptions.Timeout:
            raise UserError(_('IDP token request timed out. Server not responding.'))
        except requests.exceptions.ConnectionError as e:
            raise UserError(_('Cannot reach Hacienda IDP: %s') % str(e))

        if response.status_code == 200:
            token_data = response.json()
            self._cache_token(company.id, token_data)
            return token_data['access_token']
        elif response.status_code == 401:
            raise UserError(_('Authentication failed - Invalid username or password.'))
        else:
            detail = ''
            try:
                detail = response.json().get('error_description', response.text[:200])
            except Exception:
                detail = response.text[:200]
            raise UserError(
                _('IDP authentication failed (HTTP %s): %s') % (response.status_code, detail)
            )

    @api.model
    def _refresh_token(self, refresh_token):
        """Obtain a new access token using refresh_token grant."""
        company = self.env.company
        idp_url = self._get_idp_url()
        client_id = self._get_idp_client_id()

        data = {
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'refresh_token': refresh_token,
        }

        response = requests.post(idp_url, data=data, timeout=15)

        if response.status_code == 200:
            token_data = response.json()
            self._cache_token(company.id, token_data)
            _logger.debug('Token refreshed successfully for company %s', company.id)
            return token_data['access_token']
        else:
            # Clear stale cache on refresh failure
            _TOKEN_CACHE.pop(company.id, None)
            raise Exception('Refresh token grant failed (HTTP %s)' % response.status_code)

    @api.model
    def _cache_token(self, company_id, token_data):
        """Cache token data with computed expiration timestamps."""
        now = time.time()
        expires_in = token_data.get('expires_in', 300)
        refresh_expires_in = token_data.get('refresh_expires_in', 1800)

        _TOKEN_CACHE[company_id] = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token', ''),
            'expires_at': now + expires_in - 30,  # 30 second safety margin
            'refresh_expires_at': now + refresh_expires_in - 30,
        }

    @api.model
    def _clear_token_cache(self, company_id=None):
        """Clear token cache for a specific company or all companies."""
        if company_id:
            _TOKEN_CACHE.pop(company_id, None)
        else:
            _TOKEN_CACHE.clear()

    @api.model
    def _get_auth_headers(self):
        """Get authentication headers for API requests using OAuth2 bearer token."""
        token = self._obtain_token()

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        return headers

    @api.model
    def submit_invoice(self, clave, xml_content, sender_id, receiver_id, fecha=None):
        """
        Submit an electronic invoice to Hacienda with retry logic.

        Args:
            clave (str): 50-digit electronic document key
            xml_content (str): Signed XML content
            sender_id (str): Sender's cedula/identification
            receiver_id (str): Receiver's cedula/identification
            fecha (datetime, optional): Document date. If not provided, uses current time.

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

        # Use provided date or current time for the submission timestamp
        if fecha:
            fecha_str = fecha.strftime('%Y-%m-%dT%H:%M:%S-06:00')
        else:
            fecha_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-06:00')

        # Prepare payload according to Hacienda API specification
        payload = {
            'clave': clave,
            'fecha': fecha_str,
            'emisor': {
                'tipoIdentificacion': self.get_id_type(sender_clean),
                'numeroIdentificacion': sender_clean,
            },
            'comprobanteXml': xml_base64,
        }

        # Only include receptor if there is a real receiver identification
        # TE (Tiquete Electrónico) documents may not have a receptor
        if receiver_clean:
            payload['receptor'] = {
                'tipoIdentificacion': self.get_id_type(receiver_clean),
                'numeroIdentificacion': receiver_clean,
            }

        # Submit with retry logic
        return self._make_request_with_retry(
            method='POST',
            endpoint='/recepcion',
            payload=payload,
            operation=f'submit invoice {clave}',
            use_tribu_url=False
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
            operation=f'check status for {clave}',
            use_tribu_url=False
        )


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
    def is_error(self, response):
        """
        Check if a response indicates an error state from Hacienda.

        Args:
            response (dict): API response

        Returns:
            bool: True if document is in error state
        """
        estado = response.get('ind-estado', '').lower()
        return estado == 'error'

    @api.model
    def test_connection(self):
        """
        Test the connection to Hacienda API with OAuth2 credential validation.

        Obtains a bearer token from the IDP, then makes a test request to the
        API to confirm end-to-end connectivity.

        Returns:
            dict: Connection test result with success status and message
        """
        company = self.env.company

        if not company.l10n_cr_active_username or not company.l10n_cr_active_password:
            return {
                'success': False,
                'message': _('API credentials not configured'),
                'environment': company.l10n_cr_hacienda_env,
            }

        # Step 1: Obtain OAuth2 token (validates credentials)
        try:
            token = self._obtain_token()
        except UserError as e:
            return {
                'success': False,
                'message': str(e),
                'environment': company.l10n_cr_hacienda_env,
            }

        # Step 2: Verify connectivity to the API endpoint with the token
        base_url = self._get_base_url()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.get(f"{base_url}/recepcion/test", headers=headers, timeout=10)

            # 400/404 = auth worked, endpoint just doesn't exist (expected)
            # 401 = token not accepted by API (unexpected)
            if response.status_code in (200, 400, 404):
                return {
                    'success': True,
                    'message': _('Connection successful - Credentials validated'),
                    'environment': company.l10n_cr_hacienda_env,
                    'url': base_url,
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': _('Authentication failed - Token not accepted by API'),
                    'environment': company.l10n_cr_hacienda_env,
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

    # =====================================================
    # TAX REPORT SUBMISSION (TRIBU-CR API)
    # =====================================================

    # TRIBU-CR Tax Report Endpoints
    TRIBU_PRODUCTION_URL = 'https://api.hacienda.go.cr/tribucr/v1'
    TRIBU_SANDBOX_URL = 'https://api-sandbox.hacienda.go.cr/tribucr/v1'

    @api.model
    def _get_tribu_base_url(self):
        """Get the base URL for TRIBU-CR tax report API calls."""
        company = self.env.company

        if company.l10n_cr_hacienda_env == 'production':
            return self.TRIBU_PRODUCTION_URL
        else:
            return self.TRIBU_SANDBOX_URL

    @api.model
    def generate_tax_report_key(self, report_type, period_year, period_month=None):
        """
        Generate submission key (clave) for tax reports.

        Format: [Report Type]-[Company VAT]-[Year]-[Month]-[Sequence]
        Example: D150-3101234567-2026-01-00001

        Args:
            report_type (str): Report type (D150, D101, D151)
            period_year (int): Tax period year
            period_month (int, optional): Tax period month (for monthly reports)

        Returns:
            str: Generated submission key
        """
        company = self.env.company

        if not company.vat:
            raise UserError(_('Company VAT is required to generate tax report key.'))

        # Clean VAT number
        vat_clean = company.vat.replace('-', '').replace(' ', '')

        # Generate sequence number
        sequence_code = f'l10n_cr.tax.report.{report_type.lower()}'
        sequence = self.env['ir.sequence'].next_by_code(sequence_code)
        if not sequence:
            # Create sequence if it doesn't exist
            sequence = '00001'

        # Build key components
        key_parts = [
            report_type.upper(),
            vat_clean,
            str(period_year),
        ]

        if period_month:
            key_parts.append(str(period_month).zfill(2))

        key_parts.append(sequence.zfill(5))

        return '-'.join(key_parts)

    @api.model
    def submit_d150_report(self, report_id, signed_xml):
        """
        Submit D-150 Monthly VAT report to TRIBU-CR API.

        Args:
            report_id (int): D-150 report ID
            signed_xml (str): Digitally signed XML content

        Returns:
            dict: Submission result with structure:
                - success (bool): Submission succeeded
                - key (str): Submission key
                - message (str): Response message
                - estado (str): Processing state
                - error (str, optional): Error message if failed
        """
        report = self.env['l10n_cr.d150.report'].browse(report_id)

        if not report.exists():
            raise UserError(_('D-150 report not found.'))

        # Generate submission key if not exists
        if not report.submission_key:
            submission_key = self.generate_tax_report_key(
                'D150',
                report.period_id.year,
                report.period_id.month
            )
        else:
            submission_key = report.submission_key

        return self._submit_tax_report_generic(
            report_type='D150',
            submission_key=submission_key,
            signed_xml=signed_xml,
            period_year=report.period_id.year,
            period_month=report.period_id.month
        )

    @api.model
    def submit_d101_report(self, report_id, signed_xml):
        """
        Submit D-101 Annual Income Tax report to TRIBU-CR API.

        Args:
            report_id (int): D-101 report ID
            signed_xml (str): Digitally signed XML content

        Returns:
            dict: Submission result (see submit_d150_report)
        """
        report = self.env['l10n_cr.d101.report'].browse(report_id)

        if not report.exists():
            raise UserError(_('D-101 report not found.'))

        # Generate submission key
        if not report.submission_key:
            submission_key = self.generate_tax_report_key(
                'D101',
                report.period_id.year
            )
        else:
            submission_key = report.submission_key

        return self._submit_tax_report_generic(
            report_type='D101',
            submission_key=submission_key,
            signed_xml=signed_xml,
            period_year=report.period_id.year
        )

    @api.model
    def submit_d151_report(self, report_id, signed_xml):
        """
        Submit D-151 Annual Informative report to TRIBU-CR API.

        Args:
            report_id (int): D-151 report ID
            signed_xml (str): Digitally signed XML content

        Returns:
            dict: Submission result (see submit_d150_report)
        """
        report = self.env['l10n_cr.d151.report'].browse(report_id)

        if not report.exists():
            raise UserError(_('D-151 report not found.'))

        # Generate submission key
        if not report.submission_key:
            submission_key = self.generate_tax_report_key(
                'D151',
                report.period_id.year
            )
        else:
            submission_key = report.submission_key

        return self._submit_tax_report_generic(
            report_type='D151',
            submission_key=submission_key,
            signed_xml=signed_xml,
            period_year=report.period_id.year
        )

    @api.model
    def _submit_tax_report_generic(self, report_type, submission_key, signed_xml,
                                   period_year, period_month=None):
        """
        Generic method to submit tax reports to TRIBU-CR API.

        Args:
            report_type (str): Report type (D150, D101, D151)
            submission_key (str): Unique submission key
            signed_xml (str): Digitally signed XML
            period_year (int): Tax period year
            period_month (int, optional): Tax period month

        Returns:
            dict: Submission result
        """
        company = self.env.company

        # Encode XML to base64
        xml_base64 = base64.b64encode(signed_xml.encode('utf-8')).decode('utf-8')

        # Prepare payload for TRIBU-CR
        payload = {
            'clave': submission_key,
            'tipoDeclaracion': report_type.upper(),
            'periodo': {
                'anio': period_year,
            },
            'contribuyente': {
                'tipoIdentificacion': self.get_id_type(company.vat or ''),
                'numeroIdentificacion': (company.vat or '').replace('-', '').replace(' ', ''),
                'nombre': company.name,
            },
            'declaracionXml': xml_base64,
            'fechaPresentacion': datetime.now().strftime('%Y-%m-%dT%H:%M:%S-06:00'),
        }

        # Add month for monthly reports
        if period_month:
            payload['periodo']['mes'] = str(period_month).zfill(2)

        # Submit with retry logic
        try:
            result = self._make_request_with_retry(
                method='POST',
                endpoint=f'/declaraciones/{report_type.lower()}',
                payload=payload,
                operation=f'submit {report_type} report {submission_key}',
                use_tribu_url=True
            )

            # Parse successful response
            return {
                'success': True,
                'key': submission_key,
                'estado': result.get('estado', 'recibido'),
                'message': result.get('mensaje', _('Report submitted successfully')),
                'fecha_recepcion': result.get('fechaRecepcion'),
            }

        except UserError as e:
            # Handle submission errors
            _logger.error(f'Tax report submission failed: {str(e)}')
            return {
                'success': False,
                'key': submission_key,
                'error': str(e),
                'message': _('Submission failed: %s') % str(e),
            }

    @api.model
    def check_tax_report_status(self, submission_key, report_type):
        """
        Check the processing status of a submitted tax report.

        Args:
            submission_key (str): Submission key
            report_type (str): Report type (D150, D101, D151)

        Returns:
            dict: Status result with structure:
                - estado (str): Processing state
                  * 'recibido': Received, not processed
                  * 'procesando': Being processed
                  * 'aceptado': Accepted by Hacienda
                  * 'rechazado': Rejected
                - message (str): Status message
                - detalle (str, optional): Detailed information
                - fecha_procesamiento (str, optional): Processing timestamp
        """
        if not submission_key:
            raise UserError(_('Submission key is required.'))

        try:
            result = self._make_request_with_retry(
                method='GET',
                endpoint=f'/declaraciones/{report_type.lower()}/{submission_key}',
                payload=None,
                operation=f'check {report_type} status {submission_key}',
                use_tribu_url=True
            )

            return {
                'estado': result.get('estado', 'desconocido'),
                'message': result.get('mensaje', ''),
                'detalle': result.get('detalle', ''),
                'fecha_procesamiento': result.get('fechaProcesamiento'),
                'errores': result.get('errores', []),
            }

        except UserError as e:
            _logger.error(f'Status check failed: {str(e)}')
            return {
                'estado': 'error',
                'message': str(e),
            }

    @api.model
    def _make_request_with_retry(self, method, endpoint, payload, operation, use_tribu_url=False):
        """
        Make HTTP request with exponential backoff retry logic.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint path
            payload (dict): Request payload (None for GET)
            operation (str): Description of operation for logging
            use_tribu_url (bool): Use TRIBU-CR URL instead of e-invoice URL

        Returns:
            dict: Parsed response from API

        Raises:
            UserError: On authentication errors, validation errors, or max retries exceeded
        """
        # Select base URL
        if use_tribu_url:
            base_url = self._get_tribu_base_url()
        else:
            base_url = self._get_base_url()

        url = f"{base_url}{endpoint}"

        last_error = None
        retry_delay = INITIAL_RETRY_DELAY
        token_refreshed_this_cycle = False

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                # Refresh auth headers on each retry attempt (FIX 6: stale token across retries)
                headers = self._get_auth_headers()

                _logger.info(f'Attempt {attempt}/{MAX_RETRY_ATTEMPTS}: {operation}')

                # Make HTTP request
                if method == 'POST':
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                elif method == 'GET':
                    response = requests.get(url, headers=headers, timeout=30)
                else:
                    raise UserError(_('Unsupported HTTP method: %s') % method)

                # Log request details (avoid logging full response body in production)
                _logger.debug('Request URL: %s', url)
                _logger.debug('Response status: %s', response.status_code)

                # Check rate limit headers on every response
                remaining = response.headers.get('X-Ratelimit-Remaining')
                if remaining is not None:
                    try:
                        if int(remaining) < 5:
                            _logger.warning('Hacienda API rate limit low: %s remaining', remaining)
                    except (ValueError, TypeError):
                        pass

                # Handle different status codes
                if response.status_code in [200, 201, 202]:
                    # Success (202 = Accepted/processing for Hacienda submissions)
                    if response.status_code == 202:
                        # 202 Accepted - document received, will process async
                        # Body may be empty; treat as "recibido"
                        _logger.info(f'Successfully completed: {operation} (HTTP 202 Accepted)')
                        if not response.text.strip():
                            return {'ind-estado': 'recibido'}
                    parsed_response = self._parse_response(response)
                    _logger.info(f'Successfully completed: {operation} (HTTP {response.status_code})')
                    return parsed_response

                elif response.status_code == 400:
                    # Bad Request - validation error, don't retry
                    error_msg = self._parse_error(response)
                    error_cause = response.headers.get('X-Error-Cause', '')
                    if error_cause:
                        error_msg = f'{error_msg} (Causa: {error_cause})'
                    _logger.error(f'Validation error for {operation}: {error_msg}')
                    raise UserError(_('Error de validación: %s') % error_msg)

                elif response.status_code == 401:
                    # Unauthorized - clear token cache and retry once with fresh token
                    if not token_refreshed_this_cycle:
                        _logger.warning(f'Got 401 for {operation}, clearing token cache and retrying')
                        self._clear_token_cache(self.env.company.id)
                        token_refreshed_this_cycle = True
                        last_error = 'Token expirado, reintentando con token nuevo'
                        continue  # Retry immediately without delay
                    # Already retried with fresh token - credentials are truly invalid
                    _logger.error(f'Authentication failed for {operation} after token refresh')
                    raise UserError(_('Error de autenticación. Verifique las credenciales del API.'))

                elif response.status_code == 403:
                    # Forbidden - authorization error, don't retry
                    error_msg = self._parse_error(response)
                    _logger.error(f'Authorization error for {operation}: {error_msg}')
                    raise UserError(_('Error de autorización: %s') % error_msg)

                elif response.status_code == 404:
                    # Not Found - resource doesn't exist, don't retry
                    _logger.error(f'Resource not found for {operation}')
                    raise UserError(_('Documento no encontrado en el sistema de Hacienda.'))

                elif response.status_code == 429:
                    # Rate limiting - use server-provided reset time if available
                    reset_seconds = response.headers.get('X-Ratelimit-Reset')
                    if reset_seconds:
                        try:
                            retry_delay = max(int(reset_seconds), 1)
                            _logger.warning(
                                'Rate limited on attempt %d for %s, server says wait %ds',
                                attempt, operation, retry_delay
                            )
                        except (ValueError, TypeError):
                            retry_delay = retry_delay * 2
                            _logger.warning(f'Rate limited on attempt {attempt} for {operation}')
                    else:
                        retry_delay = retry_delay * 2  # Double the delay for rate limits
                        _logger.warning(f'Rate limited on attempt {attempt} for {operation}')
                    last_error = 'Límite de tasa excedido'

                elif response.status_code >= 500:
                    # Server error - retry
                    error_msg = self._parse_error(response)
                    _logger.warning(f'Server error on attempt {attempt} for {operation}: {error_msg}')
                    last_error = f'Error del servidor: {error_msg}'

                else:
                    # Other errors - retry
                    error_msg = self._parse_error(response)
                    _logger.warning(f'Error {response.status_code} on attempt {attempt} for {operation}: {error_msg}')
                    last_error = error_msg

            except requests.exceptions.Timeout as e:
                # Timeout - retry
                _logger.warning(f'Timeout on attempt {attempt} for {operation}: {str(e)}')
                last_error = f'Tiempo de espera agotado: {str(e)}'

            except requests.exceptions.ConnectionError as e:
                # Connection error - retry
                _logger.warning(f'Connection error on attempt {attempt} for {operation}: {str(e)}')
                last_error = f'Error de conexión: {str(e)}'

            except requests.exceptions.RequestException as e:
                # Other request exceptions - retry
                _logger.warning(f'Request error on attempt {attempt} for {operation}: {str(e)}')
                last_error = f'Error de solicitud: {str(e)}'

            # Wait before retrying (except on last attempt)
            if attempt < MAX_RETRY_ATTEMPTS:
                _logger.info(f'Retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
                retry_delay = retry_delay * RETRY_BACKOFF_FACTOR  # Exponential backoff

        # All retries exhausted
        error_message = _('Falló después de %d intentos. Último error: %s') % (MAX_RETRY_ATTEMPTS, last_error)
        _logger.error(f'{operation} - {error_message}')
        raise UserError(error_message)
