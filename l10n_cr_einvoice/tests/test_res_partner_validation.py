# -*- coding: utf-8 -*-
"""
Test suite for res.partner e-invoice validation integration.

Tests cover:
- E-invoice readiness checks
- Missing field detection
- CIIU date-based enforcement
- Auto-population from cedula cache
- Validation status computed field
"""

import logging
from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'einvoice', 'partner_validation')
class TestResPartnerValidation(TransactionCase):
    """Test partner e-invoice validation integration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get Costa Rica country
        cls.costa_rica = cls.env.ref('base.cr')

        # Get or create ID type (Cédula Física)
        cls.id_type_fisica = cls.env['l10n_latam.identification.type'].search([
            ('name', '=', 'Cédula Física')
        ], limit=1)
        if not cls.id_type_fisica:
            cls.id_type_fisica = cls.env['l10n_latam.identification.type'].create({
                'name': 'Cédula Física',
                'l10n_ar_afip_code': '01',
            })

        # Get or create CIIU code
        cls.ciiu_9311 = cls.env['l10n_cr.ciiu.code'].search([
            ('code', '=', '9311')
        ], limit=1)
        if not cls.ciiu_9311:
            cls.ciiu_9311 = cls.env['l10n_cr.ciiu.code'].create({
                'code': '9311',
                'name': 'Operación de instalaciones deportivas',
                'section': 'R',
                'description': 'Gimnasios, clubes deportivos',
            })

    def test_complete_partner_is_ready(self):
        """Test that a complete partner is marked as ready."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'info@fitness.cr',
            'l10n_cr_economic_activity_id': self.ciiu_9311.id,
        })

        # Check readiness
        self.assertTrue(partner.is_einvoice_ready())
        self.assertEqual(partner.l10n_cr_einvoice_status, 'ready')
        self.assertEqual(partner.get_einvoice_missing_fields(), [])

    def test_missing_name_detected(self):
        """Test that missing name is detected."""
        partner = self.env['res.partner'].create({
            'name': '',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'info@fitness.cr',
            'l10n_cr_economic_activity_id': self.ciiu_9311.id,
        })

        missing = partner.get_einvoice_missing_fields()
        self.assertIn('name', missing)
        self.assertFalse(partner.is_einvoice_ready())
        self.assertEqual(partner.l10n_cr_einvoice_status, 'incomplete')

    def test_missing_vat_detected(self):
        """Test that missing VAT is detected."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'info@fitness.cr',
            'l10n_cr_economic_activity_id': self.ciiu_9311.id,
        })

        missing = partner.get_einvoice_missing_fields()
        self.assertIn('vat', missing)
        self.assertFalse(partner.is_einvoice_ready())

    def test_missing_id_type_detected(self):
        """Test that missing ID type is detected."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'email': 'info@fitness.cr',
            'l10n_cr_economic_activity_id': self.ciiu_9311.id,
        })

        missing = partner.get_einvoice_missing_fields()
        self.assertIn('l10n_latam_identification_type_id', missing)
        self.assertFalse(partner.is_einvoice_ready())

    def test_missing_email_detected(self):
        """Test that missing email is detected."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': '',
            'l10n_cr_economic_activity_id': self.ciiu_9311.id,
        })

        missing = partner.get_einvoice_missing_fields()
        self.assertIn('email', missing)
        self.assertFalse(partner.is_einvoice_ready())

    def test_invalid_email_detected(self):
        """Test that invalid email format is detected."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'not-an-email',
            'l10n_cr_economic_activity_id': self.ciiu_9311.id,
        })

        missing = partner.get_einvoice_missing_fields()
        self.assertIn('email', missing)
        self.assertFalse(partner.is_einvoice_ready())

    def test_ciiu_required_after_date(self):
        """Test that CIIU is required after enforcement date."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'info@fitness.cr',
        })

        # Before enforcement date (Oct 6, 2025)
        before_date = date(2025, 10, 5)
        missing_before = partner.get_einvoice_missing_fields(reference_date=before_date)
        self.assertNotIn('l10n_cr_economic_activity_id', missing_before)

        # After enforcement date
        after_date = date(2025, 10, 6)
        missing_after = partner.get_einvoice_missing_fields(reference_date=after_date)
        self.assertIn('l10n_cr_economic_activity_id', missing_after)

        # Check status
        self.assertEqual(partner.l10n_cr_einvoice_status, 'needs_ciiu')

    def test_ciiu_can_be_skipped(self):
        """Test that CIIU check can be disabled."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'info@fitness.cr',
        })

        # With CIIU check disabled
        missing = partner.get_einvoice_missing_fields(check_ciiu=False)
        self.assertNotIn('l10n_cr_economic_activity_id', missing)
        self.assertTrue(partner.is_einvoice_ready(check_ciiu=False))

    def test_validate_for_einvoice_raises_error(self):
        """Test that validate_for_einvoice raises ValidationError."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '',  # Missing VAT
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'info@fitness.cr',
            'l10n_cr_economic_activity_id': self.ciiu_9311.id,
        })

        with self.assertRaises(ValidationError) as cm:
            partner.validate_for_einvoice()

        error_message = str(cm.exception)
        self.assertIn('missing required fields', error_message.lower())
        self.assertIn('cédula', error_message.lower())

    def test_non_cr_partner_not_validated(self):
        """Test that non-Costa Rica partners are not validated."""
        usa = self.env.ref('base.us')
        partner = self.env['res.partner'].create({
            'name': 'USA Gym',
            'country_id': usa.id,
            'email': '',  # Missing email but shouldn't matter
        })

        # Should not require validation
        self.assertTrue(partner.is_einvoice_ready())
        self.assertEqual(partner.l10n_cr_einvoice_status, 'not_applicable')
        self.assertEqual(partner.get_einvoice_missing_fields(), [])

    def test_populate_from_cedula_cache(self):
        """Test auto-population from cedula cache."""
        # Create cache entry
        cache = self.env['l10n_cr.cedula.cache'].create({
            'cedula': '310123456',
            'name': 'Gimnasio Fitness CR SA',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'ciiu_code_id': self.ciiu_9311.id,
            'primary_activity': '9311',
        })

        # Create partner with minimal data
        partner = self.env['res.partner'].create({
            'name': 'Temp Name',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'info@fitness.cr',
        })

        # Populate from cache
        result = partner.action_populate_from_cedula_cache()

        # Verify updates
        self.assertEqual(partner.name, 'Gimnasio Fitness CR SA')
        self.assertEqual(partner.l10n_cr_economic_activity_id.id, self.ciiu_9311.id)
        self.assertEqual(result['type'], 'ir.actions.client')

    def test_populate_without_vat_shows_warning(self):
        """Test that populate without VAT shows warning."""
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'country_id': self.costa_rica.id,
            'email': 'test@example.com',
        })

        result = partner.action_populate_from_cedula_cache()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertIn('warning', result['params']['type'].lower())

    def test_populate_without_cache_shows_warning(self):
        """Test that populate without cache shows warning."""
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'vat': '999999999',  # Not in cache
            'country_id': self.costa_rica.id,
            'email': 'test@example.com',
        })

        result = partner.action_populate_from_cedula_cache()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertIn('warning', result['params']['type'].lower())

    def test_status_message_for_ready(self):
        """Test status message for ready partner."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'info@fitness.cr',
            'l10n_cr_economic_activity_id': self.ciiu_9311.id,
        })

        self.assertIn('ready', partner.l10n_cr_einvoice_status_message.lower())
        self.assertIn('complete', partner.l10n_cr_einvoice_status_message.lower())

    def test_status_message_for_incomplete(self):
        """Test status message for incomplete partner."""
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'vat': '',  # Missing
            'country_id': self.costa_rica.id,
            'email': '',  # Missing
        })

        self.assertIn('missing', partner.l10n_cr_einvoice_status_message.lower())

    def test_multiple_missing_fields_listed(self):
        """Test that multiple missing fields are all detected."""
        partner = self.env['res.partner'].create({
            'name': '',  # Missing
            'vat': '',  # Missing
            'country_id': self.costa_rica.id,
            'email': '',  # Missing
        })

        missing = partner.get_einvoice_missing_fields(check_ciiu=False)
        self.assertIn('name', missing)
        self.assertIn('vat', missing)
        self.assertIn('l10n_latam_identification_type_id', missing)
        self.assertIn('email', missing)
        self.assertEqual(len(missing), 4)

    def test_email_validation_regex(self):
        """Test email validation with various formats."""
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'country_id': self.costa_rica.id,
        })

        # Valid emails
        self.assertTrue(partner._is_valid_email('test@example.com'))
        self.assertTrue(partner._is_valid_email('user.name+tag@example.co.uk'))
        self.assertTrue(partner._is_valid_email('info@gym-fitness.cr'))

        # Invalid emails
        self.assertFalse(partner._is_valid_email(''))
        self.assertFalse(partner._is_valid_email('not-an-email'))
        self.assertFalse(partner._is_valid_email('@example.com'))
        self.assertFalse(partner._is_valid_email('test@'))
        self.assertFalse(partner._is_valid_email('test'))

    def test_field_labels_mapping(self):
        """Test that field labels are mapped correctly."""
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'country_id': self.costa_rica.id,
        })

        labels = partner._get_field_labels(['name', 'vat', 'email', 'l10n_cr_economic_activity_id'])
        self.assertIn('Customer Name', labels)
        self.assertIn('Cédula/Tax ID', labels)
        self.assertIn('Email Address', labels)
        self.assertIn('CIIU Code', labels)

    def test_validate_einvoice_readiness_action(self):
        """Test manual validation action."""
        partner = self.env['res.partner'].create({
            'name': 'Gimnasio Fitness CR',
            'vat': '310123456',
            'country_id': self.costa_rica.id,
            'l10n_latam_identification_type_id': self.id_type_fisica.id,
            'email': 'info@fitness.cr',
            'l10n_cr_economic_activity_id': self.ciiu_9311.id,
        })

        result = partner.action_validate_einvoice_readiness()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertIn('success', result['params']['type'].lower())
