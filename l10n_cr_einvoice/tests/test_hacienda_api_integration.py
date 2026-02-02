# -*- coding: utf-8 -*-
"""
Integration tests for Hacienda API Client (E-Invoice Submission)

Tests OAuth2 authentication flow, invoice submission, status checking,
error handling, retry mechanism, and response parsing for the Costa Rica
Hacienda e-invoice API.

Priority: P0/P1 - Critical for production deployment
Test Level: Integration (mocked HTTP requests)
"""
import base64
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from odoo.tests.common import tagged
from odoo.exceptions import UserError
import uuid
from .common import EInvoiceTestCase


def _generate_unique_vat_company():
    """Generate unique VAT number for company (10 digits starting with 3)."""
    return f"310{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_vat_person():
    """Generate unique VAT number for person (9 digits)."""
    return f"10{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_email(prefix='test'):
    """Generate unique email address."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


import requests


@tagged('post_install', '-at_install', 'hacienda_api', 'integration')
class TestHaciendaAPIIntegration(EInvoiceTestCase):
    """Integration tests for Hacienda API client with OAuth2."""

    def setUp(self):
        super(TestHaciendaAPIIntegration, self).setUp()

        # Update company with Hacienda credentials (sandbox)
        # (Base class already created company, journals, partner, product)
        self.company.write({
            'l10n_cr_active_username': 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr',
            'l10n_cr_active_password': 'e8KLJRHzRA1P0W2ybJ5T',
            'l10n_cr_hacienda_env': 'sandbox',
        })

        self.env.user.company_id = self.company

        self.api = self.env['l10n_cr.hacienda.api']

        # Sample invoice data
        self.sample_clave = '50601012025020100111111111111111111111111111111111'
        self.sample_xml = self._generate_sample_xml()

    def _generate_sample_xml(self):
        """Generate sample invoice XML for testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012025020100111111111111111111111111111111111</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-02-01T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Test Company SA</Nombre>
        <Identificacion>
            <Tipo>02</Tipo>
            <Numero>3101234567</Numero>
        </Identificacion>
    </Emisor>
    <Receptor>
        <Nombre>Test Customer</Nombre>
        <Identificacion>
            <Tipo>01</Tipo>
            <Numero>101234567</Numero>
        </Identificacion>
    </Receptor>
    <ResumenFactura>
        <TotalVenta>10000.00</TotalVenta>
        <TotalVentaNeta>10000.00</TotalVentaNeta>
        <TotalImpuesto>1300.00</TotalImpuesto>
        <TotalComprobante>11300.00</TotalComprobante>
    </ResumenFactura>
</FacturaElectronica>'''

    # =========================================================================
    # OAUTH2 AUTHENTICATION TESTS
    # =========================================================================

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_oauth2_obtain_token_success(self, mock_post):
        """P0: Test successful OAuth2 token acquisition."""
        # Mock successful token response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "Bearer"}'
        mock_response.json.return_value = {
            'access_token': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_expires_in': 86400,
        }
        mock_post.return_value = mock_response

        # Obtain token
        token = self.api._obtain_token()

        # Verify token returned
        self.assertIsNotNone(token)
        self.assertIn('eyJ', token)  # JWT format

        # Verify correct IDP endpoint called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('rut-stag', call_args[0][0])  # Sandbox IDP URL

        # Verify correct payload
        payload = call_args[1]['data']
        self.assertEqual(payload['grant_type'], 'password')
        self.assertEqual(payload['client_id'], 'api-stag')
        self.assertEqual(payload['username'], self.company.l10n_cr_active_username)

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_oauth2_obtain_token_401_invalid_credentials(self, mock_post):
        """P0: Test OAuth2 authentication failure with invalid credentials."""
        # Mock 401 Unauthorized
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "invalid_grant", "error_description": "Invalid user credentials"}'
        mock_response.json.return_value = {
            'error': 'invalid_grant',
            'error_description': 'Invalid user credentials'
        }
        mock_post.return_value = mock_response

        # Should raise UserError
        with self.assertRaises(UserError) as cm:
            self.api._obtain_token()

        # Verify error message
        error_message = str(cm.exception)
        self.assertIn('Invalid username or password', error_message)

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_oauth2_obtain_token_timeout(self, mock_post):
        """P1: Test OAuth2 authentication timeout handling."""
        # Mock timeout exception
        mock_post.side_effect = requests.exceptions.Timeout('Connection timeout')

        # Should raise UserError with timeout message
        with self.assertRaises(UserError) as cm:
            self.api._obtain_token()

        error_message = str(cm.exception)
        self.assertIn('timed out', error_message.lower())

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_oauth2_obtain_token_connection_error(self, mock_post):
        """P1: Test OAuth2 authentication connection error handling."""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError('Network unreachable')

        # Should raise UserError
        with self.assertRaises(UserError) as cm:
            self.api._obtain_token()

        error_message = str(cm.exception)
        self.assertIn('Cannot reach Hacienda IDP', error_message)

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_oauth2_obtain_token_malformed_response(self, mock_post):
        """P1: Test OAuth2 response with malformed JSON."""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError('Invalid JSON', '', 0)
        mock_response.text = 'Not a JSON response'
        mock_post.return_value = mock_response

        # Should raise JSONDecodeError when trying to parse response
        with self.assertRaises(json.JSONDecodeError):
            self.api._obtain_token()

    # Priority: P1
    def test_oauth2_obtain_token_missing_credentials(self):
        """P1: Test OAuth2 authentication without configured credentials."""
        # Clear credentials
        self.company.write({
            'l10n_cr_active_username': False,
            'l10n_cr_active_password': False,
        })

        # Should raise UserError
        with self.assertRaises(UserError) as cm:
            self.api._obtain_token()

        error_message = str(cm.exception)
        self.assertIn('credentials not configured', error_message.lower())

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_oauth2_production_vs_sandbox_endpoint(self, mock_post):
        """P1: Test correct IDP endpoint selection (sandbox vs production)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"access_token": "test_token"}'
        mock_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_response

        # Test sandbox endpoint
        self.company.l10n_cr_hacienda_env = 'sandbox'
        self.company.l10n_cr_active_username = 'test@stag.example.com'
        self.company.l10n_cr_active_password = 'test123'
        self.api._obtain_token()
        sandbox_url = mock_post.call_args[0][0]
        self.assertIn('rut-stag', sandbox_url)

        # Test production endpoint
        self.company.l10n_cr_hacienda_env = 'production'
        self.company.l10n_cr_active_username = 'test@prod.example.com'
        self.company.l10n_cr_active_password = 'test456'
        self.api._obtain_token()
        prod_url = mock_post.call_args[0][0]
        self.assertIn('rut/', prod_url)
        self.assertNotIn('stag', prod_url)

    # =========================================================================
    # INVOICE SUBMISSION TESTS
    # =========================================================================

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_submit_invoice_success_200(self, mock_post):
        """P0: Test successful invoice submission with HTTP 200."""
        # Mock OAuth token response
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock invoice submission response
        mock_submit_response = Mock()
        mock_submit_response.status_code = 200
        mock_submit_response.text = '{"clave": "' + self.sample_clave + '", "ind-estado": "aceptado"}'
        mock_submit_response.json.return_value = {
            'clave': self.sample_clave,
            'fecha': '2025-02-01T10:00:00-06:00',
            'ind-estado': 'aceptado',
            'respuesta-xml': base64.b64encode(b'<Respuesta>Aceptado</Respuesta>').decode()
        }

        # Return different responses for token and submission
        mock_post.side_effect = [mock_token_response, mock_submit_response]

        # Submit invoice
        result = self.api.submit_invoice(
            clave=self.sample_clave,
            xml_content=self.sample_xml,
            sender_id='3101234567',
            receiver_id='101234567'
        )

        # Verify result
        self.assertEqual(result['ind-estado'], 'aceptado')
        self.assertIn('clave', result)
        self.assertIn('respuesta-xml-decoded', result)

        # Verify two calls: 1 for token, 1 for submission
        self.assertEqual(mock_post.call_count, 2)

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_submit_invoice_success_202_accepted(self, mock_post):
        """P0: Test invoice submission with HTTP 202 Accepted."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock 202 Accepted (async processing)
        mock_submit_response = Mock()
        mock_submit_response.status_code = 202
        mock_submit_response.text = ''  # Empty body for 202

        mock_post.side_effect = [mock_token_response, mock_submit_response]

        # Submit invoice
        result = self.api.submit_invoice(
            clave=self.sample_clave,
            xml_content=self.sample_xml,
            sender_id='3101234567',
            receiver_id='101234567'
        )

        # Verify 202 handled as "recibido"
        self.assertEqual(result['ind-estado'], 'recibido')

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_submit_invoice_400_validation_error(self, mock_post):
        """P0: Test invoice submission with validation error (HTTP 400)."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock validation error
        mock_submit_response = Mock()
        mock_submit_response.status_code = 400
        mock_submit_response.text = '{"error": "XML inválido", "mensaje": "El elemento ResumenFactura es obligatorio"}'
        mock_submit_response.json.return_value = {
            'error': 'XML inválido',
            'mensaje': 'El elemento ResumenFactura es obligatorio'
        }

        mock_post.side_effect = [mock_token_response, mock_submit_response]

        # Should raise UserError
        with self.assertRaises(UserError) as cm:
            self.api.submit_invoice(
                clave=self.sample_clave,
                xml_content=self.sample_xml,
                sender_id='3101234567',
                receiver_id='101234567'
            )

        error_message = str(cm.exception)
        self.assertIn('validación', error_message.lower())

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_submit_invoice_401_auth_error(self, mock_post):
        """P0: Test invoice submission with authentication error (HTTP 401)."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock auth error (token expired during submission)
        mock_submit_response = Mock()
        mock_submit_response.status_code = 401
        mock_submit_response.text = '{"error": "invalid_token", "error_description": "Token has expired"}'
        mock_submit_response.json.return_value = {
            'error': 'invalid_token',
            'error_description': 'Token has expired'
        }

        mock_post.side_effect = [mock_token_response, mock_submit_response]

        # Should raise UserError
        with self.assertRaises(UserError) as cm:
            self.api.submit_invoice(
                clave=self.sample_clave,
                xml_content=self.sample_xml,
                sender_id='3101234567',
                receiver_id='101234567'
            )

        error_message = str(cm.exception)
        self.assertIn('autenticación', error_message.lower())

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_submit_invoice_429_rate_limit(self, mock_post):
        """P0: Test invoice submission with rate limiting (HTTP 429)."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock rate limit error (all 3 retries)
        mock_rate_limit_response = Mock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.text = '{"error": "rate_limit_exceeded", "message": "Too many requests"}'
        mock_rate_limit_response.json.return_value = {
            'error': 'rate_limit_exceeded',
            'message': 'Too many requests'
        }

        # Return token once, then rate limit 3 times (should exhaust retries)
        mock_post.side_effect = [
            mock_token_response,
            mock_rate_limit_response,
            mock_rate_limit_response,
            mock_rate_limit_response
        ]

        # Should raise UserError after max retries
        with self.assertRaises(UserError) as cm:
            self.api.submit_invoice(
                clave=self.sample_clave,
                xml_content=self.sample_xml,
                sender_id='3101234567',
                receiver_id='101234567'
            )

        error_message = str(cm.exception)
        self.assertIn('intentos', error_message.lower())  # "Falló después de X intentos"

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.time.sleep')
    def test_submit_invoice_500_server_error_retry(self, mock_sleep, mock_post):
        """P0: Test invoice submission with server error and retry."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock server error then success
        mock_error_response = Mock()
        mock_error_response.status_code = 500
        mock_error_response.text = '{"error": "internal_server_error", "message": "Database connection error"}'
        mock_error_response.json.return_value = {
            'error': 'internal_server_error',
            'message': 'Database connection error'
        }

        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.text = '{"clave": "' + self.sample_clave + '", "ind-estado": "aceptado"}'
        mock_success_response.json.return_value = {
            'clave': self.sample_clave,
            'ind-estado': 'aceptado',
            'respuesta-xml': base64.b64encode(b'<Respuesta>OK</Respuesta>').decode()
        }

        # Token, error, success
        mock_post.side_effect = [
            mock_token_response,
            mock_error_response,
            mock_success_response
        ]

        # Submit (should retry and succeed)
        result = self.api.submit_invoice(
            clave=self.sample_clave,
            xml_content=self.sample_xml,
            sender_id='3101234567',
            receiver_id='101234567'
        )

        # Verify success after retry
        self.assertEqual(result['ind-estado'], 'aceptado')

        # Verify sleep was called (exponential backoff)
        mock_sleep.assert_called()

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_submit_invoice_timeout_handling(self, mock_post):
        """P1: Test invoice submission timeout handling (<30s)."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # First call returns token, then 3 timeouts for all retry attempts
        mock_post.side_effect = [
            mock_token_response,
            requests.exceptions.Timeout('Request timeout after 30s'),
            requests.exceptions.Timeout('Request timeout after 30s'),
            requests.exceptions.Timeout('Request timeout after 30s')
        ]

        # Should raise UserError after retries exhausted
        with self.assertRaises(UserError) as cm:
            self.api.submit_invoice(
                clave=self.sample_clave,
                xml_content=self.sample_xml,
                sender_id='3101234567',
                receiver_id='101234567'
            )

        error_message = str(cm.exception)
        self.assertIn('timeout', error_message.lower())

    # =========================================================================
    # STATUS CHECK TESTS
    # =========================================================================

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_check_status_aceptado(self, mock_get, mock_post):
        """P0: Test status check returns 'aceptado'."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_token_response

        # Mock status response
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.text = '{"clave": "' + self.sample_clave + '", "ind-estado": "aceptado"}'
        mock_status_response.json.return_value = {
            'clave': self.sample_clave,
            'ind-estado': 'aceptado',
            'respuesta-xml': base64.b64encode(b'<MensajeReceptor>Aceptado</MensajeReceptor>').decode()
        }
        mock_get.return_value = mock_status_response

        # Check status
        result = self.api.check_status(self.sample_clave)

        # Verify result
        self.assertEqual(result['ind-estado'], 'aceptado')
        self.assertIn('respuesta-xml-decoded', result)

        # Verify GET endpoint called
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        self.assertIn(self.sample_clave, call_url)

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_check_status_procesando(self, mock_get, mock_post):
        """P0: Test status check returns 'procesando'."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_token_response

        # Mock processing status
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.text = '{"clave": "' + self.sample_clave + '", "ind-estado": "procesando"}'
        mock_status_response.json.return_value = {
            'clave': self.sample_clave,
            'ind-estado': 'procesando',
            'respuesta-xml': ''
        }
        mock_get.return_value = mock_status_response

        # Check status
        result = self.api.check_status(self.sample_clave)

        # Verify result
        self.assertEqual(result['ind-estado'], 'procesando')
        self.assertTrue(self.api.is_processing(result))

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_check_status_rechazado(self, mock_get, mock_post):
        """P0: Test status check returns 'rechazado' with error details."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_token_response

        # Mock rejected status
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.text = '{"clave": "' + self.sample_clave + '", "ind-estado": "rechazado", "detalle-mensaje": "Clave duplicada"}'
        mock_status_response.json.return_value = {
            'clave': self.sample_clave,
            'ind-estado': 'rechazado',
            'detalle-mensaje': 'Clave duplicada',
            'respuesta-xml': base64.b64encode(b'<MensajeReceptor>Rechazado</MensajeReceptor>').decode()
        }
        mock_get.return_value = mock_status_response

        # Check status
        result = self.api.check_status(self.sample_clave)

        # Verify result
        self.assertEqual(result['ind-estado'], 'rechazado')
        self.assertTrue(self.api.is_rejected(result))
        self.assertIn('error_details', result)
        self.assertEqual(result['error_details'], 'Clave duplicada')

    # Priority: P1
    def test_check_status_invalid_clave_format(self):
        """P1: Test status check with invalid clave format."""
        # Test empty clave
        with self.assertRaises(UserError) as cm:
            self.api.check_status('')

        error_message = str(cm.exception)
        self.assertIn('Invalid clave', error_message)

        # Test wrong length
        with self.assertRaises(UserError) as cm:
            self.api.check_status('123456789')  # Too short

        error_message = str(cm.exception)
        self.assertIn('50 digits', error_message)

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_check_status_404_not_found(self, mock_get, mock_post):
        """P1: Test status check for non-existent document (404)."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_token_response

        # Mock 404 Not Found
        mock_status_response = Mock()
        mock_status_response.status_code = 404
        mock_status_response.text = '{"error": "Documento no encontrado"}'
        mock_status_response.json.return_value = {
            'error': 'Documento no encontrado'
        }
        mock_get.return_value = mock_status_response

        # Should raise UserError
        with self.assertRaises(UserError) as cm:
            self.api.check_status(self.sample_clave)

        error_message = str(cm.exception)
        self.assertIn('no encontrado', error_message.lower())

    # =========================================================================
    # RESPONSE PARSING TESTS
    # =========================================================================

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_parse_response_base64_decoding(self, mock_get, mock_post):
        """P1: Test response parsing with base64-encoded XML."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_token_response

        # Mock response with base64 XML
        response_xml = '<MensajeReceptor><Estado>aceptado</Estado></MensajeReceptor>'
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.text = '{"clave": "' + self.sample_clave + '", "ind-estado": "aceptado"}'
        mock_status_response.json.return_value = {
            'clave': self.sample_clave,
            'ind-estado': 'aceptado',
            'respuesta-xml': base64.b64encode(response_xml.encode()).decode()
        }
        mock_get.return_value = mock_status_response

        # Check status
        result = self.api.check_status(self.sample_clave)

        # Verify decoding
        self.assertIn('respuesta-xml-decoded', result)
        self.assertIn('MensajeReceptor', result['respuesta-xml-decoded'])
        self.assertIn('aceptado', result['respuesta-xml-decoded'])

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_parse_response_malformed_json(self, mock_get, mock_post):
        """P1: Test response parsing with malformed JSON."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_token_response

        # Mock malformed JSON response
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.json.side_effect = json.JSONDecodeError('Invalid JSON', '', 0)
        mock_status_response.text = 'Not valid JSON'
        mock_get.return_value = mock_status_response

        # Should handle gracefully
        result = self.api.check_status(self.sample_clave)

        # Verify error state
        self.assertEqual(result['ind-estado'], 'error')
        self.assertIn('Invalid JSON', result['error_details'])

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_parse_response_empty_body(self, mock_get, mock_post):
        """P1: Test response parsing with empty response body."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_token_response

        # Mock empty response
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.text = '{}'
        mock_status_response.json.return_value = {}
        mock_get.return_value = mock_status_response

        # Should handle gracefully
        result = self.api.check_status(self.sample_clave)

        # Should have some result
        self.assertIsInstance(result, dict)

    # =========================================================================
    # RETRY MECHANISM TESTS
    # =========================================================================

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.time.sleep')
    def test_retry_exponential_backoff(self, mock_sleep, mock_post):
        """P0: Test exponential backoff in retry mechanism."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock server errors
        mock_error_response = Mock()
        mock_error_response.status_code = 500
        mock_error_response.text = '{"error": "server error"}'
        mock_error_response.json.return_value = {'error': 'server error'}

        # All calls fail (token + 3 retries)
        mock_post.side_effect = [
            mock_token_response,
            mock_error_response,
            mock_error_response,
            mock_error_response
        ]

        # Should fail after max retries
        with self.assertRaises(UserError):
            self.api.submit_invoice(
                clave=self.sample_clave,
                xml_content=self.sample_xml,
                sender_id='3101234567',
                receiver_id='101234567'
            )

        # Verify exponential backoff (2s, 4s, but not after last attempt)
        self.assertEqual(mock_sleep.call_count, 2)

        # First delay: 2 seconds
        self.assertEqual(mock_sleep.call_args_list[0][0][0], 2)

        # Second delay: 4 seconds (exponential)
        self.assertEqual(mock_sleep.call_args_list[1][0][0], 4)

    # Priority: P0
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.time.sleep')
    def test_retry_max_attempts_reached(self, mock_sleep, mock_post):
        """P0: Test max retry attempts (3) is enforced."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock consistent failures
        mock_error_response = Mock()
        mock_error_response.status_code = 503
        mock_error_response.text = '{"error": "service unavailable"}'
        mock_error_response.json.return_value = {'error': 'service unavailable'}

        # Token + 3 failed attempts
        mock_post.side_effect = [
            mock_token_response,
            mock_error_response,
            mock_error_response,
            mock_error_response
        ]

        # Should raise after 3 retries
        with self.assertRaises(UserError) as cm:
            self.api.submit_invoice(
                clave=self.sample_clave,
                xml_content=self.sample_xml,
                sender_id='3101234567',
                receiver_id='101234567'
            )

        error_message = str(cm.exception)
        self.assertIn('3 intentos', error_message.lower())

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_retry_no_retry_on_400_validation_error(self, mock_post):
        """P1: Test no retry on validation errors (400)."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock validation error
        mock_error_response = Mock()
        mock_error_response.status_code = 400
        mock_error_response.text = '{"error": "XML inválido"}'
        mock_error_response.json.return_value = {'error': 'XML inválido'}

        # Token + validation error (should not retry)
        mock_post.side_effect = [mock_token_response, mock_error_response]

        # Should fail immediately without retry
        with self.assertRaises(UserError):
            self.api.submit_invoice(
                clave=self.sample_clave,
                xml_content=self.sample_xml,
                sender_id='3101234567',
                receiver_id='101234567'
            )

        # Should have only 2 calls (token + 1 failed attempt, no retries)
        self.assertEqual(mock_post.call_count, 2)

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_retry_no_retry_on_401_auth_error(self, mock_post):
        """P1: Test no retry on authentication errors (401)."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}

        # Mock auth error
        mock_error_response = Mock()
        mock_error_response.status_code = 401
        mock_error_response.text = '{"error": "invalid_token"}'
        mock_error_response.json.return_value = {'error': 'invalid_token'}

        # Token + auth error (should not retry)
        mock_post.side_effect = [mock_token_response, mock_error_response]

        # Should fail immediately
        with self.assertRaises(UserError):
            self.api.submit_invoice(
                clave=self.sample_clave,
                xml_content=self.sample_xml,
                sender_id='3101234567',
                receiver_id='101234567'
            )

        # Should have only 2 calls (no retries on 401)
        self.assertEqual(mock_post.call_count, 2)

    # =========================================================================
    # HELPER METHOD TESTS
    # =========================================================================

    # Priority: P1
    def test_get_id_type_cedula_fisica(self):
        """P1: Test identification type detection - Cédula Física (9 digits)."""
        result = self.api.get_id_type('101234567')
        self.assertEqual(result, '01')

        # With dashes
        result = self.api.get_id_type('1-0123-4567')
        self.assertEqual(result, '01')

    # Priority: P1
    def test_get_id_type_cedula_juridica(self):
        """P1: Test identification type detection - Cédula Jurídica (10 digits, starts with 3)."""
        result = self.api.get_id_type('3101234567')
        self.assertEqual(result, '02')

        # With dashes
        result = self.api.get_id_type('3-101-234567')
        self.assertEqual(result, '02')

    # Priority: P1
    def test_get_id_type_dimex(self):
        """P1: Test identification type detection - DIMEX (11-12 digits)."""
        result = self.api.get_id_type('12345678901')  # 11 digits
        self.assertEqual(result, '03')

        result = self.api.get_id_type('123456789012')  # 12 digits
        self.assertEqual(result, '03')

    # Priority: P1
    def test_get_id_type_nite(self):
        """P1: Test identification type detection - NITE (10 digits, not starting with 3)."""
        result = self.api.get_id_type('1234567890')
        self.assertEqual(result, '04')

    # Priority: P1
    def test_get_id_type_extranjero(self):
        """P1: Test identification type detection - Extranjero (variable)."""
        # 13 character alphanumeric - doesn't match 9, 10, 11, or 12
        result = self.api.get_id_type('ABC123XYZ4567')
        self.assertEqual(result, '05')  # Extranjero for non-standard length

        result = self.api.get_id_type('')
        self.assertEqual(result, '05')  # Extranjero for empty

    # Priority: P1
    def test_is_accepted(self):
        """P1: Test is_accepted() helper method."""
        self.assertTrue(self.api.is_accepted({'ind-estado': 'aceptado'}))
        self.assertTrue(self.api.is_accepted({'ind-estado': 'ACEPTADO'}))
        self.assertFalse(self.api.is_accepted({'ind-estado': 'procesando'}))
        self.assertFalse(self.api.is_accepted({'ind-estado': 'rechazado'}))

    # Priority: P1
    def test_is_rejected(self):
        """P1: Test is_rejected() helper method."""
        self.assertTrue(self.api.is_rejected({'ind-estado': 'rechazado'}))
        self.assertTrue(self.api.is_rejected({'ind-estado': 'RECHAZADO'}))
        self.assertFalse(self.api.is_rejected({'ind-estado': 'aceptado'}))
        self.assertFalse(self.api.is_rejected({'ind-estado': 'procesando'}))

    # Priority: P1
    def test_is_processing(self):
        """P1: Test is_processing() helper method."""
        self.assertTrue(self.api.is_processing({'ind-estado': 'procesando'}))
        self.assertTrue(self.api.is_processing({'ind-estado': 'recibido'}))
        self.assertFalse(self.api.is_processing({'ind-estado': 'aceptado'}))
        self.assertFalse(self.api.is_processing({'ind-estado': 'rechazado'}))

    # =========================================================================
    # TEST CONNECTION
    # =========================================================================

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_test_connection_success(self, mock_get, mock_post):
        """P1: Test connection test succeeds with valid credentials."""
        # Mock OAuth token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.text = '{"access_token": "test_token"}'
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_token_response

        # Mock API endpoint test (404 is acceptable - endpoint doesn't exist but auth worked)
        mock_api_response = Mock()
        mock_api_response.status_code = 404
        mock_api_response.text = '{"error": "Not Found"}'
        mock_get.return_value = mock_api_response

        # Test connection
        result = self.api.test_connection()

        # Verify success
        self.assertTrue(result['success'])
        self.assertIn('successful', result['message'].lower())
        self.assertEqual(result['environment'], 'sandbox')

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_test_connection_invalid_credentials(self, mock_post):
        """P1: Test connection test fails with invalid credentials."""
        # Mock 401 Unauthorized
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "invalid_grant", "error_description": "Invalid credentials"}'
        mock_response.json.return_value = {
            'error': 'invalid_grant',
            'error_description': 'Invalid credentials'
        }
        mock_post.return_value = mock_response

        # Test connection
        result = self.api.test_connection()

        # Verify failure
        self.assertFalse(result['success'])
        self.assertIn('Invalid username or password', result['message'])

    # Priority: P1
    def test_test_connection_no_credentials(self):
        """P1: Test connection test without configured credentials."""
        # Clear credentials
        self.company.write({
            'l10n_cr_active_username': False,
            'l10n_cr_active_password': False,
        })

        # Test connection
        result = self.api.test_connection()

        # Verify failure
        self.assertFalse(result['success'])
        self.assertIn('not configured', result['message'].lower())

    # Priority: P1
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_test_connection_timeout(self, mock_post):
        """P1: Test connection test with timeout."""
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout('Connection timeout')

        # Test connection
        result = self.api.test_connection()

        # Verify failure
        self.assertFalse(result['success'])
        self.assertIn('timed out', result['message'].lower())
