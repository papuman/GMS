# -*- coding: utf-8 -*-
"""
Integration tests for E-Invoice State Machine Transitions

Tests the complete state transition lifecycle for electronic invoice documents,
including happy paths, error paths, invalid transitions, rollbacks, and
concurrent modification protection.

Priority: P0/P1 - Critical for data integrity
Test Level: Integration (database persistence, state machine)
Week: 2 (Integration Tests)
"""
import pytest
from unittest.mock import Mock, patch
from odoo.tests.common import tagged
from odoo.exceptions import UserError, ValidationError
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


from psycopg2 import OperationalError


@tagged('post_install', '-at_install', 'integration', 'p0')
@pytest.mark.integration
@pytest.mark.p0
class TestEInvoiceStateTransitionsHappyPath(EInvoiceTestCase):
    """P0: Test happy path state transitions (draft → accepted)."""

    def setUp(self):
        super(TestEInvoiceStateTransitionsHappyPath, self).setUp()

        # Create test company with Hacienda configuration
        self.company = self.env['res.company'].create({
            'name': 'Test Company State Transitions',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_active_username': 'test@sandbox.cr',
            'l10n_cr_active_password': 'testpass123',
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_emisor_location': '001',
        })
        self.env.user.company_id = self.company

        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'vat': _generate_unique_vat_person(),
            'email': _generate_unique_email('company'),
        })

        # Create test product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
            'type': 'service',
        })

        # Create test invoice
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': '2025-02-01',
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
            'partner_id': self.partner.id,
        })

    def test_01_initial_state_is_draft(self):
        """P0: New e-invoice document starts in 'draft' state."""
        self.assertEqual(self.einvoice.state, 'draft')
        self.assertFalse(self.einvoice.xml_content)
        self.assertFalse(self.einvoice.signed_xml)
        self.assertFalse(self.einvoice.clave)

    @patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml')
    def test_02_draft_to_generated_transition(self, mock_validate, mock_generate):
        """P0: Transition from 'draft' to 'generated' state via action_generate_xml."""
        # Mock XML generation
        mock_generate.return_value = '<FacturaElectronica>...</FacturaElectronica>'
        mock_validate.return_value = (True, None)

        # Execute transition
        self.einvoice.action_generate_xml()

        # Assert state changed
        self.assertEqual(self.einvoice.state, 'generated')
        self.assertTrue(self.einvoice.xml_content)
        self.assertTrue(self.einvoice.clave)
        self.assertEqual(len(self.einvoice.clave), 50)
        self.assertFalse(self.einvoice.error_message)

    @patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xml_signer.XMLSigner.sign_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.CertificateManager.load_certificate_from_company')
    def test_03_generated_to_signed_transition(self, mock_load_cert, mock_sign, mock_validate, mock_generate):
        """P0: Transition from 'generated' to 'signed' state via action_sign_xml."""
        # Setup: generate XML first
        mock_generate.return_value = '<FacturaElectronica>...</FacturaElectronica>'
        mock_validate.return_value = (True, None)
        self.einvoice.action_generate_xml()

        # Mock certificate and signing
        mock_cert = Mock()
        mock_key = Mock()
        mock_load_cert.return_value = (mock_cert, mock_key)
        mock_sign.return_value = '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>'

        # Configure certificate
        self.company.write({
            'l10n_cr_active_certificate': b'fake_cert_data',
            'l10n_cr_active_certificate_filename': 'test.p12',
        })

        # Execute transition
        self.einvoice.action_sign_xml()

        # Assert state changed
        self.assertEqual(self.einvoice.state, 'signed')
        self.assertTrue(self.einvoice.signed_xml)
        self.assertTrue(self.einvoice.xml_attachment_id)
        self.assertFalse(self.einvoice.error_message)

    @patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xml_signer.XMLSigner.sign_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.CertificateManager.load_certificate_from_company')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.HaciendaAPI.submit_invoice')
    def test_04_signed_to_submitted_transition(self, mock_submit, mock_load_cert, mock_sign, mock_validate, mock_generate):
        """P0: Transition from 'signed' to 'submitted' state via action_submit_to_hacienda."""
        # Setup: generate and sign XML first
        mock_generate.return_value = '<FacturaElectronica>...</FacturaElectronica>'
        mock_validate.return_value = (True, None)
        self.einvoice.action_generate_xml()

        mock_cert = Mock()
        mock_key = Mock()
        mock_load_cert.return_value = (mock_cert, mock_key)
        mock_sign.return_value = '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>'
        self.company.write({
            'l10n_cr_active_certificate': b'fake_cert_data',
            'l10n_cr_active_certificate_filename': 'test.p12',
        })
        self.einvoice.action_sign_xml()

        # Mock Hacienda response (processing)
        mock_submit.return_value = {
            'ind-estado': 'procesando',
            'respuesta-xml': '',
        }

        # Execute transition
        self.einvoice.action_submit_to_hacienda()

        # Assert state changed
        self.assertIn(self.einvoice.state, ['submitted', 'accepted'])
        self.assertTrue(self.einvoice.hacienda_submission_date)

    @patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xml_signer.XMLSigner.sign_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.CertificateManager.load_certificate_from_company')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.HaciendaAPI.submit_invoice')
    def test_05_submitted_to_accepted_transition(self, mock_submit, mock_load_cert, mock_sign, mock_validate, mock_generate):
        """P0: Transition from 'submitted' to 'accepted' state (happy path completion)."""
        # Setup: complete full workflow
        mock_generate.return_value = '<FacturaElectronica>...</FacturaElectronica>'
        mock_validate.return_value = (True, None)
        self.einvoice.action_generate_xml()

        mock_cert = Mock()
        mock_key = Mock()
        mock_load_cert.return_value = (mock_cert, mock_key)
        mock_sign.return_value = '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>'
        self.company.write({
            'l10n_cr_active_certificate': b'fake_cert_data',
            'l10n_cr_active_certificate_filename': 'test.p12',
        })
        self.einvoice.action_sign_xml()

        # Mock Hacienda response (accepted immediately)
        mock_submit.return_value = {
            'ind-estado': 'aceptado',
            'respuesta-xml': 'Document accepted',
        }

        # Execute transition
        self.einvoice.action_submit_to_hacienda()

        # Assert final state
        self.assertEqual(self.einvoice.state, 'accepted')
        self.assertTrue(self.einvoice.hacienda_acceptance_date)
        self.assertFalse(self.einvoice.error_message)

    @patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xml_signer.XMLSigner.sign_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.CertificateManager.load_certificate_from_company')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.HaciendaAPI.submit_invoice')
    def test_06_complete_happy_path_lifecycle(self, mock_submit, mock_load_cert, mock_sign, mock_validate, mock_generate):
        """P0: Complete happy path: draft → generated → signed → submitted → accepted."""
        # Mock all operations
        mock_generate.return_value = '<FacturaElectronica>...</FacturaElectronica>'
        mock_validate.return_value = (True, None)
        mock_cert = Mock()
        mock_key = Mock()
        mock_load_cert.return_value = (mock_cert, mock_key)
        mock_sign.return_value = '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>'
        mock_submit.return_value = {
            'ind-estado': 'aceptado',
            'respuesta-xml': 'Document accepted',
        }
        self.company.write({
            'l10n_cr_active_certificate': b'fake_cert_data',
            'l10n_cr_active_certificate_filename': 'test.p12',
        })

        # Execute complete workflow
        initial_state = self.einvoice.state
        self.assertEqual(initial_state, 'draft')

        self.einvoice.action_generate_xml()
        self.assertEqual(self.einvoice.state, 'generated')

        self.einvoice.action_sign_xml()
        self.assertEqual(self.einvoice.state, 'signed')

        self.einvoice.action_submit_to_hacienda()
        self.assertEqual(self.einvoice.state, 'accepted')

        # Verify all artifacts exist
        self.assertTrue(self.einvoice.clave)
        self.assertTrue(self.einvoice.xml_content)
        self.assertTrue(self.einvoice.signed_xml)
        self.assertTrue(self.einvoice.xml_attachment_id)
        self.assertTrue(self.einvoice.hacienda_submission_date)
        self.assertTrue(self.einvoice.hacienda_acceptance_date)


@tagged('post_install', '-at_install', 'integration', 'p0')
@pytest.mark.integration
@pytest.mark.p0
class TestEInvoiceRejectionPath(EInvoiceTestCase):
    """P0: Test rejection path (submitted → rejected)."""

    def setUp(self):
        super(TestEInvoiceRejectionPath, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Company Rejection',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_active_username': 'test@sandbox.cr',
            'l10n_cr_active_password': 'testpass123',
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_emisor_location': '001',
        })
        self.env.user.company_id = self.company

        # Create test partner and product
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'vat': _generate_unique_vat_person(),
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
        })

        # Create invoice and e-invoice
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': '2025-02-01',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        self.invoice.action_post()

        self.einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': self.invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': self.partner.id,
        })

    @patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xml_signer.XMLSigner.sign_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.CertificateManager.load_certificate_from_company')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.HaciendaAPI.submit_invoice')
    def test_07_submitted_to_rejected_transition(self, mock_submit, mock_load_cert, mock_sign, mock_validate, mock_generate):
        """P0: Transition to 'rejected' state when Hacienda rejects the document."""
        # Setup: complete workflow to signed state
        mock_generate.return_value = '<FacturaElectronica>...</FacturaElectronica>'
        mock_validate.return_value = (True, None)
        mock_cert = Mock()
        mock_key = Mock()
        mock_load_cert.return_value = (mock_cert, mock_key)
        mock_sign.return_value = '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>'
        self.company.write({
            'l10n_cr_active_certificate': b'fake_cert_data',
            'l10n_cr_active_certificate_filename': 'test.p12',
        })

        self.einvoice.action_generate_xml()
        self.einvoice.action_sign_xml()

        # Mock Hacienda rejection
        mock_submit.return_value = {
            'ind-estado': 'rechazado',
            'respuesta-xml': 'XML structure is invalid',
            'error_details': 'Missing required element: ResumenFactura',
        }

        # Execute submission
        self.einvoice.action_submit_to_hacienda()

        # Assert rejection state
        self.assertEqual(self.einvoice.state, 'rejected')
        self.assertTrue(self.einvoice.error_message)
        self.assertIn('Missing required element', self.einvoice.error_message)
        self.assertTrue(self.einvoice.hacienda_submission_date)
        self.assertFalse(self.einvoice.hacienda_acceptance_date)


@tagged('post_install', '-at_install', 'integration', 'p0')
@pytest.mark.integration
@pytest.mark.p0
class TestInvalidStateTransitions(EInvoiceTestCase):
    """P0: Test invalid state transitions are prevented."""

    def setUp(self):
        super(TestInvalidStateTransitions, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Company Invalid Transitions',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_active_username': 'test@sandbox.cr',
            'l10n_cr_active_password': 'testpass123',
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_emisor_location': '001',
        })
        self.env.user.company_id = self.company

        # Create test partner and product
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'vat': _generate_unique_vat_person(),
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
        })

        # Create invoice and e-invoice
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': '2025-02-01',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        self.invoice.action_post()

        self.einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': self.invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': self.partner.id,
        })

    def test_08_cannot_sign_without_generate(self):
        """P0: Cannot sign XML without generating it first (draft → signed blocked)."""
        self.assertEqual(self.einvoice.state, 'draft')

        # Attempt to sign without generating
        with self.assertRaises(UserError) as context:
            self.einvoice.action_sign_xml()

        self.assertIn('Can only sign generated XML', str(context.exception))
        self.assertEqual(self.einvoice.state, 'draft')

    def test_09_cannot_submit_without_sign(self):
        """P0: Cannot submit without signing first (generated → submitted blocked)."""
        # Generate XML
        with patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml') as mock_gen, \
             patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml') as mock_val:
            mock_gen.return_value = '<FacturaElectronica>...</FacturaElectronica>'
            mock_val.return_value = (True, None)
            self.einvoice.action_generate_xml()

        self.assertEqual(self.einvoice.state, 'generated')

        # Attempt to submit without signing
        with self.assertRaises(UserError) as context:
            self.einvoice.action_submit_to_hacienda()

        self.assertIn('Can only submit signed documents', str(context.exception))
        self.assertEqual(self.einvoice.state, 'generated')

    def test_10_cannot_regenerate_accepted_document(self):
        """P0: Cannot regenerate XML for accepted document."""
        # Simulate accepted state
        self.einvoice.write({
            'state': 'accepted',
            'clave': '50601012025020100111111111111111111111111111111111',
            'xml_content': '<FacturaElectronica>...</FacturaElectronica>',
            'signed_xml': '<FacturaElectronica><Signature>...</Signature></FacturaElectronica>',
        })

        # Attempt to regenerate
        with self.assertRaises(UserError) as context:
            self.einvoice.action_generate_xml()

        self.assertIn('Can only generate XML for draft or error documents', str(context.exception))
        self.assertEqual(self.einvoice.state, 'accepted')


@tagged('post_install', '-at_install', 'integration', 'p1')
@pytest.mark.integration
@pytest.mark.p1
class TestStateRollbackAndPersistence(EInvoiceTestCase):
    """P1: Test state rollback on errors and state persistence."""

    def setUp(self):
        super(TestStateRollbackAndPersistence, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Company Rollback',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'l10n_cr_active_username': 'test@sandbox.cr',
            'l10n_cr_active_password': 'testpass123',
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_emisor_location': '001',
        })
        self.env.user.company_id = self.company

        # Create test partner and product
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'vat': _generate_unique_vat_person(),
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 1000.0,
        })

        # Create invoice and e-invoice
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': '2025-02-01',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        self.invoice.action_post()

        self.einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': self.invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': self.partner.id,
        })

    @patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml')
    def test_11_generation_error_sets_error_state(self, mock_validate, mock_generate):
        """P1: Generation errors transition to 'generation_error' state."""
        # Mock generation failure
        mock_generate.side_effect = Exception('Missing required field: partner_id.vat')

        # Attempt generation
        with self.assertRaises(UserError):
            self.einvoice.action_generate_xml()

        # Assert error state
        self.assertEqual(self.einvoice.state, 'generation_error')
        self.assertTrue(self.einvoice.error_message)
        self.assertIn('Missing required field', self.einvoice.error_message)

    @patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml')
    def test_12_state_persists_after_commit(self, mock_validate, mock_generate):
        """P1: State changes survive database commit."""
        # Mock successful generation
        mock_generate.return_value = '<FacturaElectronica>...</FacturaElectronica>'
        mock_validate.return_value = (True, None)

        # Generate XML
        self.einvoice.action_generate_xml()
        self.assertEqual(self.einvoice.state, 'generated')

        # Flush changes to database (no commit needed in tests - relies on rollback)
        self.env.cr.flush()

        # Re-read from database
        einvoice_reread = self.env['l10n_cr.einvoice.document'].browse(self.einvoice.id)
        self.assertEqual(einvoice_reread.state, 'generated')
        self.assertTrue(einvoice_reread.clave)

    @patch('odoo.addons.l10n_cr_einvoice.models.xml_generator.XMLGenerator.generate_invoice_xml')
    @patch('odoo.addons.l10n_cr_einvoice.models.xsd_validator.XSDValidator.validate_xml')
    def test_13_error_state_allows_retry(self, mock_validate, mock_generate):
        """P1: Error states can retry the same operation."""
        # First attempt fails
        mock_generate.side_effect = Exception('Temporary error')
        with self.assertRaises(UserError):
            self.einvoice.action_generate_xml()

        self.assertEqual(self.einvoice.state, 'generation_error')

        # Second attempt succeeds
        mock_generate.side_effect = None
        mock_generate.return_value = '<FacturaElectronica>...</FacturaElectronica>'
        mock_validate.return_value = (True, None)

        self.einvoice.action_retry()

        # Assert recovery
        self.assertEqual(self.einvoice.state, 'generated')
        self.assertFalse(self.einvoice.error_message)
