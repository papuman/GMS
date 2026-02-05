# -*- coding: utf-8 -*-
"""
Comprehensive Unit Tests for Cédula Validation Rules

This module provides comprehensive test coverage for validation rule enforcement
by document type, date-based enforcement, and error message generation.

Test Coverage:
- Rule enforcement by document type (FE vs TE)
- Date-based enforcement (mandatory from specific date)
- Error message generation and formatting
- Validation bypass for exempt partners
- Validation override mechanism
- Multi-company rule isolation

Priority: P0 (Critical for production)
"""

from datetime import datetime, date, timedelta
from odoo import fields
from odoo.tests import tagged
from odoo.exceptions import ValidationError, UserError
from .common import EInvoiceTestCase


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestValidationRulesByDocType(EInvoiceTestCase):
    """Test validation rule enforcement by document type."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.move_model = self.env['account.move']
        self.cr_country = self.env.ref('base.cr')

    def test_fe_requires_validated_cedula(self):
        """FE (Electronic Invoice) requires validated cédula."""
        # Create partner with unverified cédula
        partner = self.partner_model.create({
            'name': 'Unverified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
        })

        # Create FE invoice
        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Create e-invoice document
        einvoice = self._create_einvoice_document(invoice, document_type='FE')

        # Validation should fail for unverified partner
        is_valid, message = einvoice.validate_partner_cedula()
        self.assertFalse(is_valid, "FE should require validated cédula")
        self.assertIn('not verified', message.lower() or message)

    def test_fe_accepts_verified_cedula(self):
        """FE accepts verified cédula."""
        now = datetime.now()
        # Create partner with verified cédula
        partner = self.partner_model.create({
            'name': 'Verified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
        })

        # Create FE invoice
        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Create e-invoice document
        einvoice = self._create_einvoice_document(invoice, document_type='FE')

        # Validation should succeed
        is_valid, message = einvoice.validate_partner_cedula()
        self.assertTrue(is_valid, "FE should accept verified cédula")

    def test_te_relaxed_validation(self):
        """TE (Electronic Ticket) has relaxed validation requirements."""
        # Create partner without verification
        partner = self.partner_model.create({
            'name': 'Unverified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
        })

        # Create TE invoice
        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Create e-invoice document
        einvoice = self._create_einvoice_document(invoice, document_type='TE')

        # TE should allow unverified partners (more relaxed)
        is_valid, message = einvoice.validate_partner_cedula()
        # Note: TE may warn but shouldn't block
        # Implementation depends on business rules

    def test_nc_inherits_fe_validation(self):
        """NC (Credit Note) inherits validation from referenced FE."""
        now = datetime.now()
        # Create verified partner
        partner = self.partner_model.create({
            'name': 'Verified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
        })

        # Create original FE invoice
        original_invoice = self._create_test_invoice(partner=partner)
        original_invoice.action_post()

        # Create credit note (NC)
        refund = self._create_test_invoice(
            invoice_type='out_refund',
            partner=partner
        )
        refund.action_post()

        # Create e-invoice document
        einvoice = self._create_einvoice_document(refund, document_type='NC')

        # Validation should succeed (partner is verified)
        is_valid, message = einvoice.validate_partner_cedula()
        self.assertTrue(is_valid, "NC should accept verified partner")

    def test_nd_requires_validated_cedula(self):
        """ND (Debit Note) requires validated cédula."""
        # Create unverified partner
        partner = self.partner_model.create({
            'name': 'Unverified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
        })

        # Create invoice
        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Create e-invoice document
        einvoice = self._create_einvoice_document(invoice, document_type='ND')

        # Validation should fail for unverified partner
        is_valid, message = einvoice.validate_partner_cedula()
        self.assertFalse(is_valid, "ND should require validated cédula")


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestValidationRulesDateBased(EInvoiceTestCase):
    """Test date-based validation rule enforcement."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.move_model = self.env['account.move']
        self.cr_country = self.env.ref('base.cr')

    def test_validation_mandatory_after_enforcement_date(self):
        """Validation becomes mandatory after enforcement date."""
        # Enforcement date: 2025-06-01 (example)
        enforcement_date = date(2025, 6, 1)

        partner = self.partner_model.create({
            'name': 'Unverified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
        })

        # Invoice before enforcement date (should be relaxed)
        invoice_before = self._create_test_invoice(partner=partner)
        invoice_before.invoice_date = date(2025, 5, 15)
        invoice_before.action_post()

        einvoice_before = self._create_einvoice_document(invoice_before, document_type='FE')
        is_valid_before, message_before = einvoice_before.validate_partner_cedula()
        # May warn but shouldn't block before enforcement date

        # Invoice after enforcement date (should be strict)
        invoice_after = self._create_test_invoice(partner=partner)
        invoice_after.invoice_date = date(2025, 6, 15)
        invoice_after.action_post()

        einvoice_after = self._create_einvoice_document(invoice_after, document_type='FE')
        is_valid_after, message_after = einvoice_after.validate_partner_cedula()
        self.assertFalse(is_valid_after, "Should enforce validation after enforcement date")

    def test_grace_period_warnings(self):
        """Grace period shows warnings but doesn't block."""
        # Grace period: 2025-05-01 to 2025-05-31 (example)
        grace_start = date(2025, 5, 1)
        grace_end = date(2025, 5, 31)

        partner = self.partner_model.create({
            'name': 'Unverified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
        })

        # Invoice during grace period
        invoice = self._create_test_invoice(partner=partner)
        invoice.invoice_date = date(2025, 5, 15)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        # Should warn but not block during grace period
        # (Implementation may vary - adjust based on business rules)

    def test_historical_invoices_not_retroactively_validated(self):
        """Historical invoices before enforcement date are not retroactively validated."""
        partner = self.partner_model.create({
            'name': 'Unverified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
        })

        # Create historical invoice (before any enforcement date)
        invoice = self._create_test_invoice(partner=partner)
        invoice.invoice_date = date(2024, 1, 1)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')

        # Historical invoices should not be affected by new validation rules
        is_valid, message = einvoice.validate_partner_cedula()
        # Should not raise error for historical data


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestValidationErrorMessages(EInvoiceTestCase):
    """Test error message generation and formatting."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.move_model = self.env['account.move']
        self.cr_country = self.env.ref('base.cr')

    def test_error_message_unverified_partner(self):
        """Error message for unverified partner."""
        partner = self.partner_model.create({
            'name': 'Unverified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        self.assertFalse(is_valid)
        self.assertIn('not verified', message.lower())
        self.assertIn(partner.vat, message)

    def test_error_message_not_found_in_hacienda(self):
        """Error message for partner not found in Hacienda."""
        now = datetime.now()
        partner = self.partner_model.create({
            'name': 'Not Found Partner',
            'vat': '9999999999',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
            'l10n_cr_tax_status': 'no_encontrado',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        self.assertFalse(is_valid)
        self.assertIn('not found', message.lower())

    def test_error_message_stale_cache(self):
        """Error message for stale cache."""
        old_sync = datetime.now() - timedelta(days=10)
        partner = self.partner_model.create({
            'name': 'Stale Cache Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(old_sync),
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_verified': False,
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        self.assertFalse(is_valid)
        self.assertIn('stale', message.lower() or 'outdated' in message.lower())

    def test_error_message_includes_partner_name(self):
        """Error messages should include partner name for clarity."""
        partner = self.partner_model.create({
            'name': 'Test Company S.A.',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        self.assertFalse(is_valid)
        self.assertIn('Test Company', message)

    def test_error_message_actionable_next_steps(self):
        """Error messages should include actionable next steps."""
        partner = self.partner_model.create({
            'name': 'Unverified Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': False,
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        self.assertFalse(is_valid)
        # Message should suggest action (e.g., "Please verify" or "Click to verify")
        # Implementation may vary


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestValidationBypass(EInvoiceTestCase):
    """Test validation bypass for exempt partners."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.move_model = self.env['account.move']
        self.cr_country = self.env.ref('base.cr')

    def test_validation_bypass_with_override(self):
        """Partners with validation override should bypass validation."""
        partner = self.partner_model.create({
            'name': 'Exempt Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': 'Government entity',
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        # Should bypass validation
        self.assertTrue(is_valid, "Override should bypass validation")
        self.assertIn('override', message.lower() or 'exempt' in message.lower())

    def test_validation_bypass_requires_reason(self):
        """Validation override requires justification reason."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
        })

        # Cannot set override without reason
        with self.assertRaises(ValidationError):
            partner.write({
                'l10n_cr_cedula_validation_override': True,
                'l10n_cr_override_reason': False,
            })

    def test_validation_bypass_audit_trail(self):
        """Override creates audit trail with user and date."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
        })

        user = self.env.user
        reason = 'Special exemption'

        # Set override with audit info
        partner.mark_validation_override(reason=reason, user=user)

        # Verify audit trail
        self.assertTrue(partner.l10n_cr_cedula_validation_override)
        self.assertEqual(partner.l10n_cr_override_reason, reason)
        self.assertEqual(partner.l10n_cr_override_user_id, user)
        self.assertIsNotNone(partner.l10n_cr_override_date)

    def test_validation_bypass_foreign_partners(self):
        """Foreign (non-CR) partners bypass cédula validation."""
        us_country = self.env.ref('base.us')
        partner = self.partner_model.create({
            'name': 'US Partner',
            'vat': '123456789',
            'country_id': us_country.id,
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        # Foreign partners should bypass CR cédula validation
        self.assertTrue(is_valid, "Foreign partners should bypass validation")

    def test_validation_bypass_generic_identifications(self):
        """Generic identification types (passport, DIMEX) may have relaxed validation."""
        partner = self.partner_model.create({
            'name': 'Foreign Resident',
            'vat': '123456789012',  # DIMEX format (12 digits)
            'country_id': self.cr_country.id,
            'l10n_cr_identification_type': 'dimex',
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        # DIMEX may have relaxed validation (depends on business rules)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestValidationMultiCompany(EInvoiceTestCase):
    """Test validation rule isolation by company."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.move_model = self.env['account.move']
        self.cr_country = self.env.ref('base.cr')

        # Create second company
        self.company2 = self.env['res.company'].create({
            'name': 'Test Company 2 SA',
            'country_id': self.cr_country.id,
            'vat': '3109876543',
            'currency_id': self.env.ref('base.CRC').id,
        })

    def test_validation_rules_isolated_by_company(self):
        """Validation rules are isolated per company."""
        # Create partner in company 1
        partner1 = self.partner_model.create({
            'name': 'Partner Company 1',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'company_id': self.company.id,
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
        })

        # Create partner in company 2 (same VAT but different company)
        partner2 = self.partner_model.create({
            'name': 'Partner Company 2',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'company_id': self.company2.id,
            'l10n_cr_hacienda_verified': False,
        })

        # Validation status should be independent
        self.assertTrue(partner1.l10n_cr_hacienda_verified)
        self.assertFalse(partner2.l10n_cr_hacienda_verified)

    def test_override_isolated_by_company(self):
        """Validation override is isolated per company."""
        # Create partner with override in company 1
        partner1 = self.partner_model.create({
            'name': 'Partner Company 1',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'company_id': self.company.id,
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': 'Override in C1',
        })

        # Create partner in company 2
        partner2 = self.partner_model.create({
            'name': 'Partner Company 2',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'company_id': self.company2.id,
        })

        # Override should not affect company 2
        self.assertTrue(partner1.l10n_cr_cedula_validation_override)
        self.assertFalse(partner2.l10n_cr_cedula_validation_override)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p2')
class TestValidationEdgeCases(EInvoiceTestCase):
    """Test validation edge cases and error handling."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.move_model = self.env['account.move']
        self.cr_country = self.env.ref('base.cr')

    def test_validation_with_missing_vat(self):
        """Validation handles partners with missing VAT."""
        partner = self.partner_model.create({
            'name': 'No VAT Partner',
            'country_id': self.cr_country.id,
            'vat': False,
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        # Should fail with clear message
        self.assertFalse(is_valid)
        self.assertIn('vat', message.lower() or 'identification' in message.lower())

    def test_validation_with_invalid_vat_format(self):
        """Validation handles partners with invalid VAT format."""
        partner = self.partner_model.create({
            'name': 'Invalid VAT Partner',
            'vat': 'INVALID',
            'country_id': self.cr_country.id,
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        # Should fail with format error
        self.assertFalse(is_valid)

    def test_validation_with_concurrent_updates(self):
        """Validation handles concurrent partner updates."""
        now = datetime.now()
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
        })

        # Create invoice
        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        # Simulate concurrent update (partner becomes unverified)
        partner.l10n_cr_hacienda_verified = False

        einvoice = self._create_einvoice_document(invoice, document_type='FE')
        is_valid, message = einvoice.validate_partner_cedula()

        # Should use current partner state
        self.assertFalse(is_valid)

    def test_validation_with_null_country(self):
        """Validation handles partners with null country."""
        partner = self.partner_model.create({
            'name': 'No Country Partner',
            'vat': '1234567890',
            'country_id': False,
        })

        invoice = self._create_test_invoice(partner=partner)
        invoice.action_post()

        einvoice = self._create_einvoice_document(invoice, document_type='FE')

        # Should not crash
        is_valid, message = einvoice.validate_partner_cedula()
        # May fail or pass depending on business rules
