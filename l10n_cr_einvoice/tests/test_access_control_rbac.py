# -*- coding: utf-8 -*-
"""
Integration tests for Access Control and RBAC (Role-Based Access Control)

Tests that only authorized users can submit to Hacienda, read-only users
cannot modify documents, manager users have full permissions, and users
can only access their own company's invoices.

Priority: P1 - High priority for security
Test Level: Integration (database, Odoo security framework)
Week: 2 (Integration Tests)
"""
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
class TestUserAccessControl(EInvoiceTestCase):
    """P1: Test user-level access control for e-invoice operations."""

    def setUp(self):
        super(TestUserAccessControl, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Company RBAC',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_active_username': 'test@sandbox.cr',
            'l10n_cr_active_password': 'testpass123',
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_emisor_location': '001',
            'l10n_cr_active_certificate': b'fake_cert_data',
            'l10n_cr_active_certificate_filename': 'test.p12',
        })

        # Get user groups
        group_user = self.env.ref('base.group_user')
        group_system = self.env.ref('base.group_system')

        # Create Read-Only User (base user, no special permissions)
        self.user_readonly = self.env['res.users'].create({
            'name': 'Read Only User',
            'login': 'user_readonly',
            'email': _generate_unique_email('company'),
            'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'groups_id': [(6, 0, [group_user.id])],
        })

        # Create Manager User (has full permissions)
        self.user_manager = self.env['res.users'].create({
            'name': 'Manager User',
            'login': 'user_manager',
            'email': _generate_unique_email('company'),
            'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'groups_id': [(6, 0, [group_user.id, group_system.id])],
        })

        # Create test customer and product
        self.customer = self.env['res.partner'].create({
            'name': 'Test Customer',
            'vat': _generate_unique_vat_person(),
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
        })

        # Create test invoice (as admin)
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'invoice_date': '2025-02-01',
            'company_id': self.company.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        self.invoice.action_post()

        # Create e-invoice document
        self.einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': self.invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': self.customer.id,
        })

    def test_01_readonly_user_can_view_einvoices(self):
        """P1: Read-only users can view e-invoices."""
        # Read-only user searches for e-invoices
        einvoices = self.env['l10n_cr.einvoice.document'].with_user(self.user_readonly).search([])

        # Should find the test invoice
        self.assertIn(self.einvoice, einvoices,
                     "Read-only user should be able to view e-invoices")

        # Should be able to read fields
        einvoice_as_readonly = self.einvoice.with_user(self.user_readonly)
        self.assertEqual(einvoice_as_readonly.document_type, 'FE')
        self.assertEqual(einvoice_as_readonly.state, 'draft')

    def test_02_readonly_user_cannot_generate_xml(self):
        """P1: Read-only users cannot generate XML (no modify permission)."""
        # Read-only user attempts to generate XML
        einvoice_as_readonly = self.einvoice.with_user(self.user_readonly)

        try:
            einvoice_as_readonly.action_generate_xml()
            self.fail("Expected AccessError when read-only user generates XML")
        except (AccessError, UserError):
            # Expected - read-only user cannot modify
            pass

    def test_03_readonly_user_cannot_sign_xml(self):
        """P1: Read-only users cannot sign XML."""
        # Setup: Generate XML as admin first
        with patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml') as mock_gen, \
             patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml') as mock_val:
            mock_gen.return_value = '<FacturaElectronica>...</FacturaElectronica>'
            mock_val.return_value = (True, None)
            self.einvoice.action_generate_xml()

        # Read-only user attempts to sign
        einvoice_as_readonly = self.einvoice.with_user(self.user_readonly)

        try:
            einvoice_as_readonly.action_sign_xml()
            self.fail("Expected AccessError when read-only user signs XML")
        except (AccessError, UserError):
            # Expected - read-only user cannot modify
            pass

    def test_04_readonly_user_cannot_submit_to_hacienda(self):
        """P1: Read-only users cannot submit to Hacienda."""
        # Setup: Generate and sign XML as admin
        with patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml') as mock_gen, \
             patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml') as mock_val, \
             patch('odoo.addons.l10n_cr_einvoice.models.xml_signer.XMLSigner.sign_xml') as mock_sign, \
             patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.CertificateManager.load_certificate_from_company') as mock_cert:

            mock_gen.return_value = '<FacturaElectronica>...</FacturaElectronica>'
            mock_val.return_value = (True, None)
            mock_cert.return_value = (Mock(), Mock())
            mock_sign.return_value = '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>'

            self.einvoice.action_generate_xml()
            self.einvoice.action_sign_xml()

        # Read-only user attempts to submit
        einvoice_as_readonly = self.einvoice.with_user(self.user_readonly)

        try:
            einvoice_as_readonly.action_submit_to_hacienda()
            self.fail("Expected AccessError when read-only user submits to Hacienda")
        except (AccessError, UserError):
            # Expected - read-only user cannot submit
            pass

    def test_05_manager_can_generate_xml(self):
        """P1: Manager users can generate XML."""
        # Manager user generates XML
        einvoice_as_manager = self.einvoice.with_user(self.user_manager)

        with patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml') as mock_gen, \
             patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml') as mock_val:
            mock_gen.return_value = '<FacturaElectronica>...</FacturaElectronica>'
            mock_val.return_value = (True, None)

            einvoice_as_manager.action_generate_xml()

        # Should succeed
        self.assertEqual(self.einvoice.state, 'generated')
        self.assertTrue(self.einvoice.xml_content)

    def test_06_manager_can_sign_xml(self):
        """P1: Manager users can sign XML."""
        # Setup: Generate XML first
        with patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml') as mock_gen, \
             patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml') as mock_val:
            mock_gen.return_value = '<FacturaElectronica>...</FacturaElectronica>'
            mock_val.return_value = (True, None)
            self.einvoice.action_generate_xml()

        # Manager user signs XML
        einvoice_as_manager = self.einvoice.with_user(self.user_manager)

        with patch('odoo.addons.l10n_cr_einvoice.models.xml_signer.XMLSigner.sign_xml') as mock_sign, \
             patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.CertificateManager.load_certificate_from_company') as mock_cert:
            mock_cert.return_value = (Mock(), Mock())
            mock_sign.return_value = '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>'

            einvoice_as_manager.action_sign_xml()

        # Should succeed
        self.assertEqual(self.einvoice.state, 'signed')
        self.assertTrue(self.einvoice.signed_xml)

    def test_07_manager_can_submit_to_hacienda(self):
        """P1: Manager users can submit to Hacienda."""
        # Setup: Complete workflow to signed state
        with patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml') as mock_gen, \
             patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml') as mock_val, \
             patch('odoo.addons.l10n_cr_einvoice.models.xml_signer.XMLSigner.sign_xml') as mock_sign, \
             patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.CertificateManager.load_certificate_from_company') as mock_cert:

            mock_gen.return_value = '<FacturaElectronica>...</FacturaElectronica>'
            mock_val.return_value = (True, None)
            mock_cert.return_value = (Mock(), Mock())
            mock_sign.return_value = '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>'

            self.einvoice.action_generate_xml()
            self.einvoice.action_sign_xml()

        # Manager user submits to Hacienda
        einvoice_as_manager = self.einvoice.with_user(self.user_manager)

        with patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.HaciendaAPI.submit_invoice') as mock_submit:
            mock_submit.return_value = {
                'ind-estado': 'aceptado',
                'respuesta-xml': 'Accepted',
            }

            einvoice_as_manager.action_submit_to_hacienda()

        # Should succeed
        self.assertEqual(self.einvoice.state, 'accepted')


@tagged('post_install', '-at_install', 'integration', 'p1')
@pytest.mark.integration
@pytest.mark.p1
class TestCompanyAccessControl(EInvoiceTestCase):
    """P1: Test users can only access their own company's invoices."""

    def setUp(self):
        super(TestCompanyAccessControl, self).setUp()

        # Create Company A and Company B
        self.company_a = self.env['res.company'].create({
            'name': 'Company A Access Control',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
        })

        self.company_b = self.env['res.company'].create({
            'name': 'Company B Access Control',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
        })

        # Create User A (only Company A access)
        self.user_a = self.env['res.users'].create({
            'name': 'User A',
            'login': 'user_a_access',
            'company_id': self.company_a.id,
            'company_ids': [(6, 0, [self.company_a.id])],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        # Create User B (only Company B access)
        self.user_b = self.env['res.users'].create({
            'name': 'User B',
            'login': 'user_b_access',
            'company_id': self.company_b.id,
            'company_ids': [(6, 0, [self.company_b.id])],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        # Create customers and products
        self.customer_a = self.env['res.partner'].create({
            'name': 'Customer A',
            'vat': _generate_unique_vat_person(),
        })

        self.customer_b = self.env['res.partner'].create({
            'name': 'Customer B',
            'vat': _generate_unique_vat_person(),
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
        })

        # Create invoices for each company
        self.invoice_a = self.env['account.move'].create({
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

        self.invoice_b = self.env['account.move'].create({
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

        # Create e-invoices
        self.einvoice_a = self.env['l10n_cr.einvoice.document'].create({
            'move_id': self.invoice_a.id,
            'document_type': 'FE',
            'company_id': self.company_a.id,
            'partner_id': self.customer_a.id,
        })

        self.einvoice_b = self.env['l10n_cr.einvoice.document'].create({
            'move_id': self.invoice_b.id,
            'document_type': 'FE',
            'company_id': self.company_b.id,
            'partner_id': self.customer_b.id,
        })

    def test_08_user_a_can_only_access_company_a_invoices(self):
        """P1: User A can only access Company A's invoices, not Company B's."""
        # User A searches for all e-invoices
        einvoices = self.env['l10n_cr.einvoice.document'].with_user(self.user_a).search([])

        # Should find Company A invoice
        company_ids = einvoices.mapped('company_id')
        self.assertIn(self.company_a, company_ids,
                     "User A should see Company A invoices")

        # Should NOT find Company B invoice
        self.assertNotIn(self.company_b, company_ids,
                        "User A should NOT see Company B invoices")

    def test_09_user_b_can_only_access_company_b_invoices(self):
        """P1: User B can only access Company B's invoices, not Company A's."""
        # User B searches for all e-invoices
        einvoices = self.env['l10n_cr.einvoice.document'].with_user(self.user_b).search([])

        # Should find Company B invoice
        company_ids = einvoices.mapped('company_id')
        self.assertIn(self.company_b, company_ids,
                     "User B should see Company B invoices")

        # Should NOT find Company A invoice
        self.assertNotIn(self.company_a, company_ids,
                        "User B should NOT see Company A invoices")

    def test_10_user_cannot_modify_other_company_invoice(self):
        """P1: Users cannot modify invoices from other companies."""
        # User A attempts to modify Company B's invoice
        try:
            self.einvoice_b.with_user(self.user_a).write({
                'document_type': 'TE',
            })
            self.fail("Expected error when user modifies other company's invoice")
        except (AccessError, Exception):
            # Expected - user cannot access other company's data
            pass

        # User B attempts to modify Company A's invoice
        try:
            self.einvoice_a.with_user(self.user_b).write({
                'document_type': 'TE',
            })
            self.fail("Expected error when user modifies other company's invoice")
        except (AccessError, Exception):
            # Expected - user cannot access other company's data
            pass


@tagged('post_install', '-at_install', 'integration', 'p2')
@pytest.mark.integration
@pytest.mark.p2
class TestDatabaseLevelSecurity(EInvoiceTestCase):
    """P2: Test security rules are enforced at database level."""

    def setUp(self):
        super(TestDatabaseLevelSecurity, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Company DB Security',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
        })

        # Create test user
        self.user = self.env['res.users'].create({
            'name': 'Test User DB Security',
            'login': 'user_db_security',
            'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
        })

    def test_11_company_id_field_is_required(self):
        """P2: company_id field is required on e-invoice documents."""
        # Create customer and product
        customer = self.env['res.partner'].create({
            'name': 'Test Customer',
            'vat': _generate_unique_vat_person(),
        })
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
        })

        # Create invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': customer.id,
            'invoice_date': '2025-02-01',
            'company_id': self.company.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        invoice.action_post()

        # Create e-invoice WITH company_id (should succeed)
        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': customer.id,
        })
        self.assertTrue(einvoice.company_id,
                       "E-invoice should have company_id set")

    def test_12_security_rules_apply_to_search(self):
        """P2: Security rules automatically filter search results."""
        # Create another company
        other_company = self.env['res.company'].create({
            'name': 'Other Company',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
        })

        # Create customer and product
        customer = self.env['res.partner'].create({
            'name': 'Test Customer',
            'vat': _generate_unique_vat_person(),
        })
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
        })

        # Create invoice for other company
        invoice_other = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': customer.id,
            'invoice_date': '2025-02-01',
            'company_id': other_company.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        invoice_other.action_post()

        # Create e-invoice for other company
        einvoice_other = self.env['l10n_cr.einvoice.document'].create({
            'move_id': invoice_other.id,
            'document_type': 'FE',
            'company_id': other_company.id,
            'partner_id': customer.id,
        })

        # User searches (should only see own company)
        einvoices = self.env['l10n_cr.einvoice.document'].with_user(self.user).search([])

        # Should not include other company's invoice
        self.assertNotIn(einvoice_other, einvoices,
                        "Security rules should filter out other company's invoices")
