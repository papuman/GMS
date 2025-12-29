# -*- coding: utf-8 -*-
import base64
import json
import logging
import requests
from datetime import datetime

from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
        Submit an electronic invoice to Hacienda.

        Args:
            clave (str): 50-digit electronic document key
            xml_content (str): Signed XML content
            sender_id (str): Sender's cedula/identification
            receiver_id (str): Receiver's cedula/identification

        Returns:
            dict: Response from Hacienda API
        """
        try:
            base_url = self._get_base_url()
            url = f"{base_url}/recepcion"

            # Encode XML to base64
            xml_base64 = base64.b64encode(xml_content.encode('utf-8')).decode('utf-8')

            # Prepare payload
            payload = {
                'clave': clave,
                'fecha': datetime.now().isoformat(),
                'emisor': {
                    'tipoIdentificacion': self.get_id_type(sender_id),
                    'numeroIdentificacion': sender_id,
                },
                'receptor': {
                    'tipoIdentificacion': self.get_id_type(receiver_id) if receiver_id else '05',
                    'numeroIdentificacion': receiver_id or '000000000000',
                },
                'comprobanteXml': xml_base64,
            }

            # Make request
            headers = self._get_auth_headers()
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            # Log request and response
            _logger.info(f'Submitted invoice {clave} to Hacienda')
            _logger.debug(f'Response status: {response.status_code}')
            _logger.debug(f'Response body: {response.text}')

            # Check response
            if response.status_code == 200 or response.status_code == 201:
                return self._parse_response(response)
            else:
                error_msg = self._parse_error(response)
                raise UserError(_('Hacienda API error: %s') % error_msg)

        except requests.exceptions.RequestException as e:
            _logger.error(f'Request error submitting to Hacienda: {str(e)}')
            raise UserError(_('Connection error: %s') % str(e))

    @api.model
    def check_status(self, clave):
        """
        Check the status of a submitted document.

        Args:
            clave (str): 50-digit electronic document key

        Returns:
            dict: Status response from Hacienda
        """
        try:
            base_url = self._get_base_url()
            url = f"{base_url}/recepcion/{clave}"

            headers = self._get_auth_headers()
            response = requests.get(url, headers=headers, timeout=30)

            _logger.info(f'Checked status for {clave}')

            if response.status_code == 200:
                return self._parse_response(response)
            else:
                error_msg = self._parse_error(response)
                raise UserError(_('Status check error: %s') % error_msg)

        except requests.exceptions.RequestException as e:
            _logger.error(f'Request error checking status: {str(e)}')
            raise UserError(_('Connection error: %s') % str(e))

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
        """Parse the API response."""
        try:
            data = response.json()
            return data
        except json.JSONDecodeError:
            return {
                'ind-estado': 'error',
                'respuesta-xml': response.text,
            }

    @api.model
    def _parse_error(self, response):
        """Parse error response from API."""
        try:
            error_data = response.json()
            if 'message' in error_data:
                return error_data['message']
            elif 'error' in error_data:
                return error_data['error']
            else:
                return str(error_data)
        except json.JSONDecodeError:
            return response.text or f'HTTP {response.status_code}'

    @api.model
    def test_connection(self):
        """Test the connection to Hacienda API."""
        try:
            base_url = self._get_base_url()
            headers = self._get_auth_headers()

            # Make a simple GET request to check connectivity
            response = requests.get(f"{base_url}/status", headers=headers, timeout=10)

            if response.status_code in [200, 404]:  # 404 is OK, means auth worked
                return {
                    'success': True,
                    'message': _('Connection successful'),
                    'environment': self.env.company.l10n_cr_hacienda_env,
                }
            else:
                return {
                    'success': False,
                    'message': _('Connection failed: HTTP %s') % response.status_code,
                }

        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }
