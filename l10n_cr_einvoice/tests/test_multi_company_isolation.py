# -*- coding: utf-8 -*-
"""
Integration tests for Multi-Company Isolation

Tests that e-invoice documents, certificates, credentials, and responses are
properly isolated between companies. Ensures Company A cannot access, modify,
or view Company B's data.

Priority: P1 - High priority for multi-tenant deployments
Test Level: Integration (database, ORM security)
Week: 2 (Integration Tests)
"""
import base64
import pytest
from unittest.mock import Mock, patch
from odoo.tests.common import tagged
from odoo.exceptions import AccessError, UserError
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




@tagged('post_install', '-at_install', 'integration', 'p1')
@pytest.mark.integration
@pytest.mark.p1
class TestMultiCompanyDataIsolation(EInvoiceTestCase):
    """P1: Test multi-company data isolation for e-invoices."""

    def setUp(self):
        super(TestMultiCompanyDataIsolation, self).setUp()

        # Create Company A
        self.company_a = self.env['res.company'].create({
            'name': 'Company A Costa Rica',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_active_username': 'company_a@sandbox.cr',
            'l10n_cr_active_password': 'password_a',
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_emisor_location': '001',
        })

        # Create Company B
        self.company_b = self.env['res.company'].create({
            'name': 'Company B Costa Rica',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_active_username': 'company_b@sandbox.cr',
            'l10n_cr_active_password': 'password_b',
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_emisor_location': '002',
        })

        # Create User A (belongs to Company A)
        self.user_a = self.env['res.users'].create({
            'name': 'User A',
            'login': 'user_a',
            'email': _generate_unique_email('user'),
            'company_id': self.company_a.id,
            'company_ids': [(6, 0, [self.company_a.id])],
        })

        # Create User B (belongs to Company B)
        self.user_b = self.env['res.users'].create({
            'name': 'User B',
            'login': 'user_b',
            'email': _generate_unique_email('user'),
            'company_id': self.company_b.id,
            'company_ids': [(6, 0, [self.company_b.id])],
        })

        # Create customers for each company
        self.customer_a = self.env['res.partner'].create({
            'name': 'Customer A',
            'vat': _generate_unique_vat_person(),
            'company_id': self.company_a.id,
        })
        self.customer_b = self.env['res.partner'].create({
            'name': 'Customer B',
            'vat': _generate_unique_vat_person(),
            'company_id': self.company_b.id,
        })

        # Create products
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
        })

        # Create invoices for each company
        self.invoice_a = self.env['account.move'].with_user(self.user_a).create({
            'move_type': 'out_invoice',
            'partner_id': self.customer_a.id,
            'invoice_date': '2025-02-01',
            'company_id': self.company_a.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        self.invoice_a.action_post()

        self.invoice_b = self.env['account.move'].with_user(self.user_b).create({
            'move_type': 'out_invoice',
            'partner_id': self.customer_b.id,
            'invoice_date': '2025-02-01',
            'company_id': self.company_b.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 2000.0,
            })],
        })
        self.invoice_b.action_post()

        # Create e-invoice documents for each company
        self.einvoice_a = self.env['l10n_cr.einvoice.document'].with_user(self.user_a).create({
            'move_id': self.invoice_a.id,
            'document_type': 'FE',
            'company_id': self.company_a.id,
            'partner_id': self.customer_a.id,
        })

        self.einvoice_b = self.env['l10n_cr.einvoice.document'].with_user(self.user_b).create({
            'move_id': self.invoice_b.id,
            'document_type': 'FE',
            'company_id': self.company_b.id,
            'partner_id': self.customer_b.id,
        })

    def test_01_company_a_cannot_see_company_b_invoices(self):
        """P1: Company A users cannot see Company B's e-invoices."""
        # User A searches for all e-invoices
        einvoices = self.env['l10n_cr.einvoice.document'].with_user(self.user_a).search([])

        # Should only see Company A invoices
        company_ids = einvoices.mapped('company_id')
        self.assertIn(self.company_a, company_ids)
        self.assertNotIn(self.company_b, company_ids)

        # Should not find Company B's specific invoice
        self.assertNotIn(self.einvoice_b, einvoices)

    def test_02_company_b_cannot_see_company_a_invoices(self):
        """P1: Company B users cannot see Company A's e-invoices."""
        # User B searches for all e-invoices
        einvoices = self.env['l10n_cr.einvoice.document'].with_user(self.user_b).search([])

        # Should only see Company B invoices
        company_ids = einvoices.mapped('company_id')
        self.assertIn(self.company_b, company_ids)
        self.assertNotIn(self.company_a, company_ids)

        # Should not find Company A's specific invoice
        self.assertNotIn(self.einvoice_a, einvoices)

    def test_03_company_a_cannot_modify_company_b_invoice(self):
        """P1: Company A users cannot modify Company B's e-invoices."""
        # User A attempts to modify Company B's invoice
        try:
            # Direct write should fail due to company_id check
            self.einvoice_b.with_user(self.user_a).write({
                'document_type': 'TE',
            })
            # If no error, test fails
            self.fail("Expected AccessError when modifying other company's invoice")
        except AccessError:
            # Expected behavior
            pass
        except Exception as e:
            # Other exceptions are acceptable (e.g., missing record)
            self.assertIn('record', str(e).lower(),
                         "Expected access-related error")

    def test_04_company_a_cannot_read_company_b_invoice_details(self):
        """P1: Company A users cannot read Company B's invoice details."""
        # User A attempts to browse Company B's invoice
        try:
            einvoice = self.env['l10n_cr.einvoice.document'].with_user(self.user_a).browse(self.einvoice_b.id)
            # Accessing fields should trigger access check
            _ = einvoice.clave
            # If we get here without error, check if it's empty (filtered out)
            self.assertFalse(einvoice.exists(),
                           "Company B invoice should not be accessible to Company A")
        except AccessError:
            # Expected behavior
            pass

    def test_05_invoices_respect_company_id_domain(self):
        """P1: Invoice searches automatically filter by company_id."""
        # User A searches without explicit company filter
        einvoices_a = self.env['l10n_cr.einvoice.document'].with_user(self.user_a).search([
            ('document_type', '=', 'FE')
        ])

        # Should only return Company A invoices
        for einvoice in einvoices_a:
            self.assertEqual(einvoice.company_id, self.company_a,
                           "Found invoice from wrong company")

        # User B searches without explicit company filter
        einvoices_b = self.env['l10n_cr.einvoice.document'].with_user(self.user_b).search([
            ('document_type', '=', 'FE')
        ])

        # Should only return Company B invoices
        for einvoice in einvoices_b:
            self.assertEqual(einvoice.company_id, self.company_b,
                           "Found invoice from wrong company")


@tagged('post_install', '-at_install', 'integration', 'p1')
@pytest.mark.integration
@pytest.mark.p1
class TestMultiCompanyCertificateIsolation(EInvoiceTestCase):
    """P1: Test certificate and credential isolation between companies."""

    def setUp(self):
        super(TestMultiCompanyCertificateIsolation, self).setUp()

        # Create two companies with different certificates
        self.company_a = self.env['res.company'].create({
            'name': 'Company A Certificates',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_active_username': 'company_a@sandbox.cr',
            'l10n_cr_active_password': 'password_a',
            'l10n_cr_active_certificate': base64.b64encode(b'CERT_A_DATA'),
            'l10n_cr_active_certificate_filename': 'company_a.p12',
            'l10n_cr_active_key_password': 'pin_a_123',
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_emisor_location': '001',
        })

        self.company_b = self.env['res.company'].create({
            'name': 'Company B Certificates',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_active_username': 'company_b@sandbox.cr',
            'l10n_cr_active_password': 'password_b',
            'l10n_cr_active_certificate': base64.b64encode(b'CERT_B_DATA'),
            'l10n_cr_active_certificate_filename': 'company_b.p12',
            'l10n_cr_active_key_password': 'pin_b_456',
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_emisor_location': '002',
        })

    def test_06_each_company_uses_own_certificate(self):
        """P1: Each company uses its own certificate, not shared."""
        # Get certificate data for each company
        cert_a = self.company_a.l10n_cr_active_certificate
        cert_b = self.company_b.l10n_cr_active_certificate

        # Certificates should be different
        self.assertNotEqual(cert_a, cert_b,
                          "Companies should have different certificates")

        # Decode and verify content
        cert_a_decoded = base64.b64decode(cert_a)
        cert_b_decoded = base64.b64decode(cert_b)

        self.assertEqual(cert_a_decoded, b'CERT_A_DATA')
        self.assertEqual(cert_b_decoded, b'CERT_B_DATA')

    def test_07_each_company_uses_own_credentials(self):
        """P1: Hacienda credentials are isolated per company."""
        # Check Company A credentials
        self.assertEqual(self.company_a.l10n_cr_active_username, 'company_a@sandbox.cr')
        self.assertEqual(self.company_a.l10n_cr_active_password, 'password_a')

        # Check Company B credentials
        self.assertEqual(self.company_b.l10n_cr_active_username, 'company_b@sandbox.cr')
        self.assertEqual(self.company_b.l10n_cr_active_password, 'password_b')

        # Credentials should be different
        self.assertNotEqual(
            self.company_a.l10n_cr_active_username,
            self.company_b.l10n_cr_active_username
        )

    def test_08_certificate_pin_is_isolated(self):
        """P1: Certificate PIN/password is isolated per company."""
        # Check PINs are different
        pin_a = self.company_a.l10n_cr_active_key_password
        pin_b = self.company_b.l10n_cr_active_key_password

        self.assertEqual(pin_a, 'pin_a_123')
        self.assertEqual(pin_b, 'pin_b_456')
        self.assertNotEqual(pin_a, pin_b)

    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.CertificateManager.load_certificate_from_company')
    def test_09_signing_uses_correct_company_certificate(self, mock_load_cert):
        """P1: Document signing uses the correct company's certificate."""
        # Create invoice for Company A
        customer_a = self.env['res.partner'].create({
            'name': 'Customer A',
            'vat': _generate_unique_vat_person(),
        })
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
        })

        invoice_a = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': customer_a.id,
            'invoice_date': '2025-02-01',
            'company_id': self.company_a.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        invoice_a.action_post()

        einvoice_a = self.env['l10n_cr.einvoice.document'].create({
            'move_id': invoice_a.id,
            'document_type': 'FE',
            'company_id': self.company_a.id,
            'partner_id': customer_a.id,
        })

        # Generate and sign
        with patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml') as mock_gen, \
             patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml') as mock_val, \
             patch('odoo.addons.l10n_cr_einvoice.models.xml_signer.XMLSigner.sign_xml') as mock_sign:

            mock_gen.return_value = '<FacturaElectronica>...</FacturaElectronica>'
            mock_val.return_value = (True, None)
            mock_cert = Mock()
            mock_key = Mock()
            mock_load_cert.return_value = (mock_cert, mock_key)
            mock_sign.return_value = '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>'

            einvoice_a.action_generate_xml()
            einvoice_a.action_sign_xml()

            # Verify certificate manager was called with Company A
            mock_load_cert.assert_called_once()
            called_company = mock_load_cert.call_args[0][0]
            self.assertEqual(called_company.id, self.company_a.id,
                           "Certificate should be loaded from Company A")


@tagged('post_install', '-at_install', 'integration', 'p2')
@pytest.mark.integration
@pytest.mark.p2
class TestMultiCompanyResponseIsolation(EInvoiceTestCase):
    """P2: Test Hacienda response message isolation between companies."""

    def setUp(self):
        super(TestMultiCompanyResponseIsolation, self).setUp()

        # Create two companies
        self.company_a = self.env['res.company'].create({
            'name': 'Company A Responses',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_hacienda_env': 'sandbox',
        })

        self.company_b = self.env['res.company'].create({
            'name': 'Company B Responses',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_hacienda_env': 'sandbox',
        })

        # Create users
        self.user_a = self.env['res.users'].create({
            'name': 'User A Responses',
            'login': 'user_a_resp',
            'company_id': self.company_a.id,
            'company_ids': [(6, 0, [self.company_a.id])],
        })

        self.user_b = self.env['res.users'].create({
            'name': 'User B Responses',
            'login': 'user_b_resp',
            'company_id': self.company_b.id,
            'company_ids': [(6, 0, [self.company_b.id])],
        })

    def test_10_response_messages_isolated_by_company(self):
        """P2: Hacienda response messages are isolated per company."""
        # Check if response message model exists
        if 'l10n_cr.hacienda.response.message' not in self.env:
            self.skipTest("Response message model not implemented yet")

        # Create response messages for each company
        response_a = self.env['l10n_cr.hacienda.response.message'].create({
            'company_id': self.company_a.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'xml_response_decoded': 'Response for Company A',
        })

        response_b = self.env['l10n_cr.hacienda.response.message'].create({
            'company_id': self.company_b.id,
            'clave': '50601012025020100122222222222222222222222222222222',
            'xml_response_decoded': 'Response for Company B',
        })

        # User A should only see Company A responses
        responses_a = self.env['l10n_cr.hacienda.response.message'].with_user(self.user_a).search([])
        self.assertIn(response_a, responses_a)
        self.assertNotIn(response_b, responses_a)

        # User B should only see Company B responses
        responses_b = self.env['l10n_cr.hacienda.response.message'].with_user(self.user_b).search([])
        self.assertIn(response_b, responses_b)
        self.assertNotIn(response_a, responses_b)
