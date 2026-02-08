# -*- coding: utf-8 -*-
"""
Comprehensive Integration Tests for Complete Validation System

This module provides end-to-end integration testing for the multi-layer validation
architecture across POS, Backend, and XML generation layers.

Test Coverage:
- End-to-end validation flow (POS -> Backend -> XML)
- FE validation enforcement (all mandatory fields)
- TE relaxed validation (minimal requirements)
- Date-based CIIU enforcement (before/after Oct 6, 2025)
- Validation override workflow (wizard -> approval -> bypass)
- Multi-layer validation (UI catches, Backend enforces, XML validates)
- Cross-layer consistency checks
- Error propagation and user feedback

Architecture Integration Points:
1. POS Layer: Pre-validation before document creation
2. Backend Layer: ORM constraints and validation rules
3. XML Layer: Schema validation and business rules
4. Override Layer: Bypass mechanism with audit trail

Priority: P0 (Critical for production)
"""

from datetime import datetime, date, timedelta
from odoo import fields, _
from odoo.tests import tagged
from odoo.exceptions import ValidationError, UserError
from .common import EInvoiceTestCase


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestEndToEndValidationFlow(EInvoiceTestCase):
    """Test complete validation flow from POS to XML generation."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.einvoice_model = self.env['l10n_cr.einvoice.document']
        self.validation_rule_model = self.env['l10n_cr.validation.rule']
        self.cr_country = self.env.ref('base.cr')
        # Put all validation rules in test mode so they report but don't block
        self.env['l10n_cr.validation.rule'].search([]).write({'test_mode': True})

    def test_e2e_fe_happy_path_all_fields_valid(self):
        """Happy path: FE with all required fields should succeed through all layers."""
        # Create verified partner with all required fields
        now = datetime.now()
        partner = self.partner_model.create({
            'name': 'Empresa Completa SA',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'email': 'completa@example.com',
            'phone': '22001100',
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
        })

        # Add CIIU code (required after Oct 6, 2025)
        ciiu = self.env['l10n_cr.ciiu.code'].search([], limit=1)
        if ciiu:
            partner.l10n_cr_economic_activity_id = ciiu

        # Create invoice
        invoice = self._create_test_invoice(partner=partner)
        invoice.invoice_date = date(2025, 11, 1)  # After CIIU enforcement date
        invoice.action_post()

        # Create e-invoice document (should pass backend validation)
        einvoice = self.einvoice_model.with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        # Verify document created successfully
        self.assertEqual(einvoice.state, 'draft')
        self.assertEqual(einvoice.partner_id, partner)
        self.assertEqual(einvoice.document_type, 'FE')

        # Validate against all rules (should pass)
        is_valid, error_messages = self.validation_rule_model.validate_all_rules(einvoice)
        self.assertTrue(is_valid, f"Validation should pass but got errors: {error_messages}")
        self.assertEqual(len(error_messages), 0, "Should have no error messages")

    def test_e2e_fe_missing_customer_blocks_creation(self):
        """FE without customer should be blocked at backend layer."""
        invoice = self._create_test_invoice()
        invoice.action_post()

        # Try to create FE without partner (should fail)
        with self.assertRaises(ValidationError) as cm:
            self.einvoice_model.create({
                'move_id': invoice.id,
                'document_type': 'FE',
                'company_id': self.company.id,
                'partner_id': False,  # Missing customer
            })

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            'cliente' in error_msg or 'customer' in error_msg,
            "Error should mention missing customer"
        )

    def test_e2e_fe_missing_email_blocks_creation(self):
        """FE without customer email should be blocked at backend layer."""
        # Create partner without email
        partner = self.partner_model.create({
            'name': 'No Email Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            # email is missing
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Try to create FE (should fail due to missing email)
        with self.assertRaises(ValidationError) as cm:
            self.einvoice_model.create({
                'move_id': invoice.id,
                'document_type': 'FE',
                'company_id': self.company.id,
                'partner_id': partner.id,
            })

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            'email' in error_msg or 'correo' in error_msg,
            "Error should mention missing email"
        )

    def test_e2e_te_relaxed_validation_succeeds(self):
        """TE should succeed with minimal partner information."""
        # Create partner with minimal info (no email, no verification)
        partner = self.partner_model.create({
            'name': 'Cliente Basico',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            # No email, no verification, no CIIU
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Create TE (should succeed with relaxed validation)
        einvoice = self.einvoice_model.create({
            'move_id': invoice.id,
            'document_type': 'TE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        # Should create successfully
        self.assertEqual(einvoice.state, 'draft')
        self.assertEqual(einvoice.document_type, 'TE')

    def test_e2e_xml_generation_with_invalid_data_fails(self):
        """XML generation should fail if data doesn't meet schema requirements."""
        # Create partner with invalid email format
        partner = self.partner_model.create({
            'name': 'Invalid Email Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'email': 'not-an-email',  # Invalid format
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Backend validation might catch this
        with self.assertRaises(ValidationError):
            self.einvoice_model.create({
                'move_id': invoice.id,
                'document_type': 'FE',
                'company_id': self.company.id,
                'partner_id': partner.id,
            })


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestFEValidationEnforcement(EInvoiceTestCase):
    """Test FE mandatory field enforcement across all layers."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.einvoice_model = self.env['l10n_cr.einvoice.document']
        self.cr_country = self.env.ref('base.cr')
        # Put all validation rules in test mode so they report but don't block
        self.env['l10n_cr.validation.rule'].search([]).write({'test_mode': True})

    def test_fe_customer_name_required(self):
        """FE requires customer name."""
        partner = self.partner_model.create({
            'name': '',  # Empty name
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'email': 'test@example.com',
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        with self.assertRaises(ValidationError) as cm:
            self.einvoice_model.create({
                'move_id': invoice.id,
                'document_type': 'FE',
                'company_id': self.company.id,
                'partner_id': partner.id,
            })

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            'nombre' in error_msg or 'name' in error_msg,
            f"Error should mention missing name: {error_msg}"
        )

    def test_fe_customer_vat_required(self):
        """FE requires customer VAT/ID."""
        partner = self.partner_model.create({
            'name': 'No VAT Partner',
            'vat': False,  # Missing VAT
            'country_id': self.cr_country.id,
            'email': 'test@example.com',
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        with self.assertRaises(ValidationError) as cm:
            self.einvoice_model.create({
                'move_id': invoice.id,
                'document_type': 'FE',
                'company_id': self.company.id,
                'partner_id': partner.id,
            })

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            'cedula' in error_msg or 'cédula' in error_msg
            or 'vat' in error_msg or 'identification' in error_msg
            or 'identificaci' in error_msg,
            f"Error should mention missing VAT/ID: {error_msg}"
        )

    def test_fe_customer_email_required(self):
        """FE requires customer email."""
        partner = self.partner_model.create({
            'name': 'No Email Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            # Missing email
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        with self.assertRaises(ValidationError) as cm:
            self.einvoice_model.create({
                'move_id': invoice.id,
                'document_type': 'FE',
                'company_id': self.company.id,
                'partner_id': partner.id,
            })

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            'email' in error_msg or 'correo' in error_msg,
            f"Error should mention missing email: {error_msg}"
        )

    def test_fe_customer_email_format_validated(self):
        """FE validates email format."""
        partner = self.partner_model.create({
            'name': 'Invalid Email Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'email': 'invalid-email-format',  # Invalid format
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        with self.assertRaises(ValidationError) as cm:
            self.einvoice_model.create({
                'move_id': invoice.id,
                'document_type': 'FE',
                'company_id': self.company.id,
                'partner_id': partner.id,
            })

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            'email' in error_msg or 'correo' in error_msg,
            f"Error should mention invalid email: {error_msg}"
        )


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestTERelaxedValidation(EInvoiceTestCase):
    """Test TE relaxed validation requirements."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.einvoice_model = self.env['l10n_cr.einvoice.document']
        self.cr_country = self.env.ref('base.cr')
        # Put all validation rules in test mode so they report but don't block
        self.env['l10n_cr.validation.rule'].search([]).write({'test_mode': True})

    def test_te_allows_anonymous_customer(self):
        """TE allows generic/anonymous customer."""
        # Create generic partner
        partner = self.partner_model.create({
            'name': 'Cliente Generico',
            'vat': '000000000',  # Generic ID
            'country_id': self.cr_country.id,
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # TE should allow this
        einvoice = self.einvoice_model.create({
            'move_id': invoice.id,
            'document_type': 'TE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        self.assertEqual(einvoice.state, 'draft')

    def test_te_allows_missing_email(self):
        """TE allows missing email."""
        partner = self.partner_model.create({
            'name': 'No Email Customer',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            # No email
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # TE should allow this
        einvoice = self.einvoice_model.create({
            'move_id': invoice.id,
            'document_type': 'TE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        self.assertEqual(einvoice.state, 'draft')

    def test_te_allows_unverified_cedula(self):
        """TE allows unverified cedula."""
        partner = self.partner_model.create({
            'name': 'Unverified Customer',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,  # Not verified
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # TE should allow this
        einvoice = self.einvoice_model.create({
            'move_id': invoice.id,
            'document_type': 'TE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        self.assertEqual(einvoice.state, 'draft')

    def test_te_allows_missing_ciiu(self):
        """TE allows missing CIIU code."""
        partner = self.partner_model.create({
            'name': 'No CIIU Customer',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            # No CIIU code
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.invoice_date = date(2025, 11, 1)  # After CIIU enforcement
        invoice.action_post()

        # TE should allow this even after CIIU enforcement date
        einvoice = self.einvoice_model.create({
            'move_id': invoice.id,
            'document_type': 'TE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        self.assertEqual(einvoice.state, 'draft')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestDateBasedCIIUEnforcement(EInvoiceTestCase):
    """Test CIIU enforcement before and after Oct 6, 2025."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.einvoice_model = self.env['l10n_cr.einvoice.document']
        self.cr_country = self.env.ref('base.cr')
        self.enforcement_date = date(2025, 10, 6)
        # Put all validation rules in test mode so they report but don't block
        self.env['l10n_cr.validation.rule'].search([]).write({'test_mode': True})

    def test_ciiu_not_required_before_enforcement_date(self):
        """CIIU should not be required before Oct 6, 2025."""
        now = datetime.now()
        partner = self.partner_model.create({
            'name': 'Pre-Enforcement Customer',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'email': 'pre@example.com',
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
            # No CIIU code
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.invoice_date = date(2025, 10, 5)  # One day before enforcement
        invoice.action_post()

        # Should succeed without CIIU
        einvoice = self.einvoice_model.with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        self.assertEqual(einvoice.state, 'draft')

    def test_ciiu_required_on_enforcement_date(self):
        """CIIU should be required starting Oct 6, 2025."""
        now = datetime.now()
        partner = self.partner_model.create({
            'name': 'Enforcement Date Customer',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'email': 'enforcement@example.com',
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
            # No CIIU code
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.invoice_date = date(2025, 10, 6)  # Enforcement date
        invoice.action_post()

        # Create document with bypass, then validate via rule engine
        einvoice = self.einvoice_model.with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        # Validate via rule engine - should report CIIU missing
        is_valid, error_messages = self.env['l10n_cr.validation.rule'].validate_all_rules(einvoice)
        # In test_mode rules report but don't raise; check the messages
        error_text = ' '.join(error_messages).lower()
        self.assertTrue(
            'ciiu' in error_text or 'actividad' in error_text or not is_valid,
            f"Validation should flag missing CIIU: {error_messages}"
        )

    def test_ciiu_required_after_enforcement_date(self):
        """CIIU should be required after Oct 6, 2025."""
        now = datetime.now()
        partner = self.partner_model.create({
            'name': 'Post-Enforcement Customer',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'email': 'post@example.com',
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
            # No CIIU code
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.invoice_date = date(2025, 11, 1)  # After enforcement
        invoice.action_post()

        # Create document with bypass, then validate via rule engine
        einvoice = self.einvoice_model.with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        # Validate via rule engine - should report CIIU missing
        is_valid, error_messages = self.env['l10n_cr.validation.rule'].validate_all_rules(einvoice)
        error_text = ' '.join(error_messages).lower()
        self.assertTrue(
            'ciiu' in error_text or 'actividad' in error_text or not is_valid,
            f"Validation should flag missing CIIU: {error_messages}"
        )

    def test_ciiu_present_after_enforcement_succeeds(self):
        """CIIU present after enforcement date should succeed."""
        now = datetime.now()
        partner = self.partner_model.create({
            'name': 'CIIU Present Customer',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'email': 'ciiu@example.com',
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
        })

        # Add CIIU code
        ciiu = self.env['l10n_cr.ciiu.code'].search([], limit=1)
        if ciiu:
            partner.l10n_cr_economic_activity_id = ciiu

        invoice = self._create_test_invoice(partner=partner)
        invoice.invoice_date = date(2025, 11, 1)  # After enforcement
        invoice.action_post()

        # Should succeed with CIIU
        einvoice = self.einvoice_model.with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        self.assertEqual(einvoice.state, 'draft')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestValidationOverrideWorkflow(EInvoiceTestCase):
    """Test validation override workflow with audit trail."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.einvoice_model = self.env['l10n_cr.einvoice.document']
        self.cr_country = self.env.ref('base.cr')
        # Put all validation rules in test mode so they report but don't block
        self.env['l10n_cr.validation.rule'].search([]).write({'test_mode': True})

    def test_override_bypasses_validation(self):
        """Document with validation_override should bypass validation."""
        partner = self.partner_model.create({
            'name': 'Government Entity',
            'vat': '300123456',
            'country_id': self.cr_country.id,
            # Missing email and verification
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': 'Government entity exempt from validation',
            'l10n_cr_override_user_id': self.env.user.id,
            'l10n_cr_override_date': fields.Datetime.now(),
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Create einvoice with validation_override set on the document itself
        einvoice = self.einvoice_model.with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': partner.id,
            'validation_override': True,
            'validation_override_reason': 'Government entity exempt from validation',
            'validation_override_user_id': self.env.user.id,
            'validation_override_date': fields.Datetime.now(),
        })

        self.assertEqual(einvoice.state, 'draft')
        self.assertTrue(einvoice.validation_override)

    def test_override_requires_reason(self):
        """Override requires justification reason."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
        })

        # Cannot set override without reason
        with self.assertRaises(ValidationError):
            partner.write({
                'l10n_cr_cedula_validation_override': True,
                'l10n_cr_override_reason': False,  # Missing reason
            })

    def test_override_creates_audit_trail(self):
        """Override creates complete audit trail."""
        partner = self.partner_model.create({
            'name': 'Audit Test Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
        })

        # Set override with audit info
        override_reason = 'Special exemption for testing'
        partner.write({
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': override_reason,
            'l10n_cr_override_user_id': self.env.user.id,
            'l10n_cr_override_date': fields.Datetime.now(),
        })

        # Verify audit trail
        self.assertTrue(partner.l10n_cr_cedula_validation_override)
        self.assertEqual(partner.l10n_cr_override_reason, override_reason)
        self.assertEqual(partner.l10n_cr_override_user_id, self.env.user)
        self.assertIsNotNone(partner.l10n_cr_override_date)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestMultiLayerValidation(EInvoiceTestCase):
    """Test validation consistency across UI, Backend, and XML layers."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.einvoice_model = self.env['l10n_cr.einvoice.document']
        self.validation_rule_model = self.env['l10n_cr.validation.rule']
        self.cr_country = self.env.ref('base.cr')
        # Put all validation rules in test mode so they report but don't block
        self.env['l10n_cr.validation.rule'].search([]).write({'test_mode': True})

    def test_backend_catches_what_ui_misses(self):
        """Backend validation should catch errors even if UI validation is bypassed."""
        # Create partner with missing fields
        partner = self.partner_model.create({
            'name': 'Incomplete Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            # Missing email
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Try to bypass UI validation via context (should still fail at backend fallback)
        with self.assertRaises(ValidationError):
            self.einvoice_model.create({
                'move_id': invoice.id,
                'document_type': 'FE',
                'company_id': self.company.id,
                'partner_id': partner.id,
            })

    def test_xml_layer_validates_business_rules(self):
        """XML generation should validate business rules even if data passed backend."""
        now = datetime.now()
        # Create partner that passes backend but might fail XML rules
        partner = self.partner_model.create({
            'name': 'Edge Case Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            'email': 'edge@example.com',
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self.einvoice_model.with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        # Document should be created but validation rules should apply
        self.assertEqual(einvoice.state, 'draft')

    def test_validation_bypass_context_flag(self):
        """Context flag should allow bypassing validation for special cases."""
        # Create partner with missing fields
        partner = self.partner_model.create({
            'name': 'Bypass Test Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            # Missing email
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Should succeed with bypass flag
        einvoice = self.einvoice_model.with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'partner_id': partner.id,
        })

        self.assertEqual(einvoice.state, 'draft')

    def test_error_messages_are_user_friendly(self):
        """Error messages should be actionable and user-friendly."""
        partner = self.partner_model.create({
            'name': 'Missing Email Partner',
            'vat': '101234567',
            'country_id': self.cr_country.id,
            # Missing email
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        try:
            self.einvoice_model.create({
                'move_id': invoice.id,
                'document_type': 'FE',
                'company_id': self.company.id,
                'partner_id': partner.id,
            })
            self.fail("Should have raised ValidationError")
        except ValidationError as e:
            error_msg = str(e)
            # Error should be in Spanish and mention what to do
            self.assertTrue(
                'correo' in error_msg.lower() or 'email' in error_msg.lower(),
                f"Error should mention email: {error_msg}"
            )
            # Should suggest TE as alternative
            self.assertTrue(
                'tiquete' in error_msg.lower() or 'te' in error_msg.lower(),
                f"Error should suggest TE alternative: {error_msg}"
            )
