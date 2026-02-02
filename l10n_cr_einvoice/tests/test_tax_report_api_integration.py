# -*- coding: utf-8 -*-
"""
Comprehensive tests for Tax Report API Integration (Phase 9C)
Tests TRIBU-CR API submission, status checking, and error handling
"""
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


from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


@tagged('post_install', '-at_install', 'tax_reports', 'api')
class TestTaxReportAPIIntegration(EInvoiceTestCase):
    """Test API integration for tax report submission."""

    def setUp(self):
        super(TestTaxReportAPIIntegration, self).setUp()

        # Create test company with Hacienda configuration
        self.company = self.env['res.company'].create({
            'name': 'Test Gym Costa Rica',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'email': _generate_unique_email('company'),
            'phone': '22001100',
        })

        self.env.user.company_id = self.company

        # Create test certificate (mock)
        self.company.write({
            'l10n_cr_tribu_api_username': 'test_user',
            'l10n_cr_tribu_api_environment': 'sandbox',
        })

        self.HaciendaAPI = self.env['l10n_cr.hacienda.api']

    def _create_d150_report_with_xml(self):
        """Helper to create D-150 report with generated XML."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 1000000.00,
            'sales_13_tax': 130000.00,
        })

        # Generate and sign XML
        XMLGenerator = self.env['l10n_cr.tax.report.xml.generator']
        xml_content = XMLGenerator.generate_d150_xml(d150)
        d150.xml_content = xml_content
        d150.xml_signed = xml_content  # Mock signed XML
        d150.state = 'ready'

        return d150

    # =====================================================
    # SUBMISSION TESTS
    # =====================================================

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d150_successful_submission(self, mock_post):
        """Test successful D-150 submission to Hacienda."""
        d150 = self._create_d150_report_with_xml()

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'clave': '50625112300003101234567000000010000001000000001',
            'mensaje': 'Recibido exitosamente',
        }
        mock_post.return_value = mock_response

        # Submit
        d150.action_submit_to_hacienda()

        # Verify state changed
        self.assertEqual(d150.state, 'submitted')
        self.assertIsNotNone(d150.submission_key)
        self.assertIsNotNone(d150.submission_date)
        self.assertIn('exitosamente', d150.hacienda_message)

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d150_submission_authentication_failure(self, mock_post):
        """Test D-150 submission with authentication error."""
        d150 = self._create_d150_report_with_xml()

        # Mock authentication failure
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'error': 'Credenciales inválidas',
        }
        mock_post.return_value = mock_response

        # Submit
        d150.action_submit_to_hacienda()

        # Should be in error state
        self.assertEqual(d150.state, 'error')
        self.assertIn('inválidas', d150.hacienda_message.lower())

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d150_submission_invalid_xml(self, mock_post):
        """Test D-150 submission with invalid XML rejection."""
        d150 = self._create_d150_report_with_xml()

        # Mock XML validation error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'XML inválido: elemento Ventas faltante',
        }
        mock_post.return_value = mock_response

        # Submit
        d150.action_submit_to_hacienda()

        # Should be in error state
        self.assertEqual(d150.state, 'error')
        self.assertIn('XML', d150.hacienda_message)

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d150_submission_network_timeout(self, mock_post):
        """Test D-150 submission with network timeout."""
        d150 = self._create_d150_report_with_xml()

        # Mock timeout
        import requests
        mock_post.side_effect = requests.Timeout('Connection timeout')

        # Submit
        d150.action_submit_to_hacienda()

        # Should be in error state
        self.assertEqual(d150.state, 'error')
        self.assertIn('timeout', d150.hacienda_message.lower())

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d150_submission_network_error(self, mock_post):
        """Test D-150 submission with network error."""
        d150 = self._create_d150_report_with_xml()

        # Mock connection error
        import requests
        mock_post.side_effect = requests.ConnectionError('Network unreachable')

        # Submit
        d150.action_submit_to_hacienda()

        # Should be in error state
        self.assertEqual(d150.state, 'error')

    # =====================================================
    # STATUS CHECK TESTS
    # =====================================================

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_d150_status_check_accepted(self, mock_get):
        """Test checking status returns accepted."""
        d150 = self._create_d150_report_with_xml()
        d150.submission_key = '50625112300003101234567000000010000001000000001'
        d150.state = 'submitted'

        # Mock accepted response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'estado': 'aceptado',
            'mensaje': 'Declaración aceptada',
        }
        mock_get.return_value = mock_response

        # Check status
        d150.action_check_status()

        # Should be accepted
        self.assertEqual(d150.state, 'accepted')
        self.assertIsNotNone(d150.acceptance_date)

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_d150_status_check_rejected(self, mock_get):
        """Test checking status returns rejected."""
        d150 = self._create_d150_report_with_xml()
        d150.submission_key = '50625112300003101234567000000010000001000000001'
        d150.state = 'submitted'

        # Mock rejected response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'estado': 'rechazado',
            'mensaje': 'Monto de IVA no coincide',
        }
        mock_get.return_value = mock_response

        # Check status
        d150.action_check_status()

        # Should be rejected
        self.assertEqual(d150.state, 'rejected')
        self.assertIn('IVA', d150.hacienda_message)

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_d150_status_check_processing(self, mock_get):
        """Test checking status returns processing."""
        d150 = self._create_d150_report_with_xml()
        d150.submission_key = '50625112300003101234567000000010000001000000001'
        d150.state = 'submitted'

        # Mock processing response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'estado': 'procesando',
            'mensaje': 'Declaración en proceso de validación',
        }
        mock_get.return_value = mock_response

        # Check status
        d150.action_check_status()

        # Should still be submitted
        self.assertEqual(d150.state, 'submitted')

    def test_d150_status_check_without_submission_key(self):
        """Test error when checking status without submission key."""
        d150 = self._create_d150_report_with_xml()
        d150.state = 'ready'

        with self.assertRaises(UserError) as cm:
            d150.action_check_status()

        self.assertIn('submission key', str(cm.exception).lower())

    # =====================================================
    # RETRY LOGIC TESTS
    # =====================================================

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d150_submission_retry_on_500(self, mock_post):
        """Test retry logic on server error (500)."""
        d150 = self._create_d150_report_with_xml()

        # Mock 500 error then success
        mock_response_error = Mock()
        mock_response_error.status_code = 500
        mock_response_error.json.return_value = {'error': 'Internal server error'}

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'clave': '50625112300003101234567000000010000001000000001',
            'mensaje': 'Recibido exitosamente',
        }

        mock_post.side_effect = [mock_response_error, mock_response_success]

        # Submit (should retry and succeed)
        d150.action_submit_to_hacienda()

        # Should succeed after retry
        self.assertEqual(d150.state, 'submitted')
        self.assertEqual(mock_post.call_count, 2)

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d150_submission_max_retries_exceeded(self, mock_post):
        """Test max retries exceeded."""
        d150 = self._create_d150_report_with_xml()

        # Mock consistent 500 errors
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'error': 'Internal server error'}
        mock_post.return_value = mock_response

        # Submit (should fail after max retries)
        d150.action_submit_to_hacienda()

        # Should be in error state
        self.assertEqual(d150.state, 'error')

    # =====================================================
    # D-101 SUBMISSION TESTS
    # =====================================================

    def _create_d101_report_with_xml(self):
        """Helper to create D-101 report with generated XML."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 50000000.00,
            'operating_expenses': 20000000.00,
        })

        # Generate and sign XML
        XMLGenerator = self.env['l10n_cr.tax.report.xml.generator']
        xml_content = XMLGenerator.generate_d101_xml(d101)
        d101.xml_content = xml_content
        d101.xml_signed = xml_content
        d101.state = 'ready'

        return d101

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d101_successful_submission(self, mock_post):
        """Test successful D-101 submission."""
        d101 = self._create_d101_report_with_xml()

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'clave': '50625010100003101234567000000010000001000000001',
            'mensaje': 'D-101 recibido exitosamente',
        }
        mock_post.return_value = mock_response

        # Submit
        d101.action_submit_to_hacienda()

        # Verify
        self.assertEqual(d101.state, 'submitted')
        self.assertIsNotNone(d101.submission_key)

    # =====================================================
    # D-151 SUBMISSION TESTS
    # =====================================================

    def _create_d151_report_with_xml(self):
        """Helper to create D-151 report with generated XML."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        # Add customer line
        self.env['l10n_cr.d151.customer.line'].create({
            'report_id': d151.id,
            'partner_vat': '109876543',
            'partner_name': 'Juan Pérez',
            'total_amount': 5000000.00,
            'transaction_count': 12,
        })

        # Generate and sign XML
        XMLGenerator = self.env['l10n_cr.tax.report.xml.generator']
        xml_content = XMLGenerator.generate_d151_xml(d151)
        d151.xml_content = xml_content
        d151.xml_signed = xml_content
        d151.state = 'ready'

        return d151

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d151_successful_submission(self, mock_post):
        """Test successful D-151 submission."""
        d151 = self._create_d151_report_with_xml()

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'clave': '50625015100003101234567000000010000001000000001',
            'mensaje': 'D-151 recibido exitosamente',
        }
        mock_post.return_value = mock_response

        # Submit
        d151.action_submit_to_hacienda()

        # Verify
        self.assertEqual(d151.state, 'submitted')
        self.assertIsNotNone(d151.submission_key)

    # =====================================================
    # ERROR RESPONSE HANDLING
    # =====================================================

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_submission_malformed_json_response(self, mock_post):
        """Test handling of malformed JSON response."""
        d150 = self._create_d150_report_with_xml()

        # Mock malformed response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError('Invalid JSON')
        mock_response.text = 'Invalid response body'
        mock_post.return_value = mock_response

        # Submit
        d150.action_submit_to_hacienda()

        # Should handle gracefully
        self.assertEqual(d150.state, 'error')

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_submission_empty_response(self, mock_post):
        """Test handling of empty response."""
        d150 = self._create_d150_report_with_xml()

        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        # Submit
        d150.action_submit_to_hacienda()

        # Should handle gracefully
        self.assertEqual(d150.state, 'error')

    # =====================================================
    # API CONFIGURATION TESTS
    # =====================================================

    def test_submission_without_api_credentials(self):
        """Test error when API credentials not configured."""
        d150 = self._create_d150_report_with_xml()

        # Remove API credentials
        self.company.l10n_cr_tribu_api_username = False

        with self.assertRaises(UserError) as cm:
            d150.action_submit_to_hacienda()

        self.assertIn('credentials', str(cm.exception).lower())

    def test_api_endpoint_selection_sandbox(self):
        """Test correct API endpoint selection for sandbox."""
        self.company.l10n_cr_tribu_api_environment = 'sandbox'

        endpoint = self.HaciendaAPI._get_api_endpoint('tax_reports')

        self.assertIn('sandbox', endpoint.lower())

    def test_api_endpoint_selection_production(self):
        """Test correct API endpoint selection for production."""
        self.company.l10n_cr_tribu_api_environment = 'production'

        endpoint = self.HaciendaAPI._get_api_endpoint('tax_reports')

        self.assertNotIn('sandbox', endpoint.lower())

    # =====================================================
    # CONCURRENT SUBMISSION TESTS
    # =====================================================

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_prevent_duplicate_submission(self, mock_post):
        """Test prevention of duplicate submission."""
        d150 = self._create_d150_report_with_xml()
        d150.submission_key = 'existing_key'
        d150.state = 'submitted'

        # Try to submit again
        with self.assertRaises(UserError) as cm:
            d150.action_submit_to_hacienda()

        self.assertIn('already', str(cm.exception).lower())

    # =====================================================
    # STATUS POLLING TESTS
    # =====================================================

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_status_polling_with_delay(self, mock_get):
        """Test status polling with appropriate delay."""
        d150 = self._create_d150_report_with_xml()
        d150.submission_key = '50625112300003101234567000000010000001000000001'
        d150.state = 'submitted'
        d150.submission_date = datetime.now()

        # Mock processing response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'estado': 'procesando',
        }
        mock_get.return_value = mock_response

        # Check status multiple times
        for _ in range(3):
            d150.action_check_status()

        # Should not make too many calls
        self.assertLessEqual(mock_get.call_count, 3)
