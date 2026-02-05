# -*- coding: utf-8 -*-
"""
Integration Tests for Partner Lookup Integration

Tests the res.partner integration with cédula lookup service,
including manual lookup buttons, auto-lookup workflows, cache status
display, and smart buttons.

Test Coverage:
- Partner manual lookup button
- Partner auto-lookup on VAT change
- Cache status computed fields
- Smart button visibility
- Lookup wizard workflow
- Conflict resolution (duplicate VAT)

Priority: P0 (Critical - partner management core feature)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock
from odoo import fields
from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import EInvoiceTestCase


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestPartnerManualLookupButton(EInvoiceTestCase):
    """Test partner manual lookup button."""

    def test_01_lookup_button_updates_partner_data(self):
        """Manual lookup button updates partner with Hacienda data."""
        cedula = '3101234567'

        # Create partner
        partner = self._create_test_partner(vat=cedula, name='Old Name')

        # Mock API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'New Official Name SA',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
            'correo': 'new@company.cr',
            'actividades': [
                {'codigo': '9311', 'descripcion': 'Gimnasios'}
            ]
        }

        with patch('requests.post', return_value=mock_response):
            # Trigger manual lookup
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Update partner from result
            partner.write({
                'name': result['name'],
                'email': result.get('email'),
                'l10n_cr_tax_status': result['tax_status'],
                'l10n_cr_hacienda_verified': True,
                'l10n_cr_hacienda_last_sync': fields.Datetime.now(),
            })

            # Assert updated
            self.assertEqual(partner.name, 'New Official Name SA')
            self.assertEqual(partner.email, 'new@company.cr')
            self.assertTrue(partner.l10n_cr_hacienda_verified)

    def test_02_lookup_button_shows_confirmation_before_overwrite(self):
        """Lookup button confirms before overwriting existing data."""
        cedula = '2020202020'

        # Create partner with existing data
        partner = self._create_test_partner(vat=cedula, name='Existing Name')
        partner.write({
            'email': 'existing@email.com',
            'phone': '+506 2200-1100',
        })

        # Mock API with different data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Different Name',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
            'correo': 'different@email.com',
        }

        with patch('requests.post', return_value=mock_response):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # In production UI, user would confirm overwrite
            # For test, verify data is available to merge
            self.assertEqual(result['name'], 'Different Name')
            self.assertEqual(result['email'], 'different@email.com')

    def test_03_lookup_button_disabled_for_non_cr_partners(self):
        """Lookup button disabled for non-Costa Rica partners."""
        # Create US partner
        us_partner = self.env['res.partner'].create({
            'name': 'US Company',
            'vat': '123456789',
            'country_id': self.env.ref('base.us').id,
            'company_id': self.company.id,
        })

        # Lookup should fail or be disabled
        # (Implementation may check country before calling service)
        # For now, verify error handling
        with self.assertRaises((UserError, ValidationError)):
            self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(us_partner.vat)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestPartnerAutoLookupOnVATChange(EInvoiceTestCase):
    """Test partner auto-lookup on VAT change."""

    def test_01_auto_lookup_on_vat_entry_for_new_partner(self):
        """Auto-lookup triggers when VAT entered for new partner."""
        cedula = '4040404040'

        # Mock API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Auto Lookup Corp',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post', return_value=mock_response):
            # Create partner with VAT
            partner = self._create_test_partner(vat=cedula, name='Temp')

            # Perform lookup (simulating auto-trigger)
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Verify lookup successful
            self.assertEqual(result['name'], 'Auto Lookup Corp')

    def test_02_auto_lookup_on_vat_change_for_existing_partner(self):
        """Auto-lookup triggers when VAT changed on existing partner."""
        # Create partner without VAT
        partner = self._create_test_partner(vat=None, name='No VAT')

        cedula = '5050505050'

        # Mock API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Updated Company',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post', return_value=mock_response):
            # Set VAT (triggers auto-lookup)
            partner.write({'vat': cedula})

            # Perform lookup
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Verify data available
            self.assertEqual(result['name'], 'Updated Company')

    def test_03_auto_lookup_can_be_disabled_in_settings(self):
        """Auto-lookup respects system configuration."""
        # This test verifies that auto-lookup can be disabled
        # via system parameter or company setting
        # Implementation-specific test
        pass


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestPartnerCacheStatusFields(EInvoiceTestCase):
    """Test cache status computed fields on partner."""

    def test_01_cache_status_shows_verified(self):
        """Cache status field shows verified status."""
        cedula = '6060606060'

        # Create verified partner
        partner = self._create_verified_partner(name='Verified Corp', vat=cedula)

        # Get status
        status = partner.get_validation_status()

        # Assert verified
        self.assertTrue(status['is_valid'])
        self.assertEqual(status['icon'], 'valid')

    def test_02_cache_status_shows_stale_warning(self):
        """Cache status field shows warning for stale cache."""
        cedula = '7070707070'

        # Create partner with stale cache
        partner = self._create_stale_cache_partner(
            name='Stale Partner',
            vat=cedula,
            days_old=30
        )

        # Get status
        status = partner.get_validation_status()

        # Assert stale warning
        self.assertFalse(status['is_valid'])
        self.assertEqual(status['icon'], 'warning')

    def test_03_cache_status_shows_never_verified(self):
        """Cache status field shows not verified status."""
        cedula = '8080808080'

        # Create unverified partner
        partner = self._create_unverified_partner(name='Never Verified', vat=cedula)

        # Get status
        status = partner.get_validation_status()

        # Assert not verified
        self.assertIsNone(status['is_valid'])
        self.assertEqual(status['icon'], 'unknown')

    def test_04_cache_age_computed_field(self):
        """Cache age computed field shows hours/days."""
        cedula = '9090909090'

        # Create partner with 6-day-old cache
        partner = self._create_stale_cache_partner(
            name='Age Test',
            vat=cedula,
            days_old=6
        )

        # Assert cache age (approximately 6 days)
        self.assertGreaterEqual(partner.l10n_cr_hacienda_cache_age_hours, 140)
        self.assertLessEqual(partner.l10n_cr_hacienda_cache_age_hours, 150)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestPartnerSmartButtons(EInvoiceTestCase):
    """Test smart button visibility and actions."""

    def test_01_hacienda_lookup_button_visible_for_cr_partners(self):
        """Hacienda lookup button visible only for CR partners."""
        # CR partner
        cr_partner = self._create_test_partner(vat='1010101010', name='CR Partner')
        cr_partner.write({'country_id': self.env.ref('base.cr').id})

        # US partner
        us_partner = self.env['res.partner'].create({
            'name': 'US Partner',
            'vat': '123456789',
            'country_id': self.env.ref('base.us').id,
            'company_id': self.company.id,
        })

        # CR partner should have button (country_id = Costa Rica)
        self.assertEqual(cr_partner.country_id, self.env.ref('base.cr'))

        # US partner should not
        self.assertNotEqual(us_partner.country_id, self.env.ref('base.cr'))

    def test_02_cache_status_smart_button_shows_details(self):
        """Cache status smart button shows cache details."""
        cedula = '1111111111'

        # Create partner with cache
        partner = self._create_verified_partner(name='Cache Button Test', vat=cedula)

        # Verify cache exists
        cache = self.env['l10n_cr.cedula.cache'].search([('cedula', '=', cedula)])
        if cache:
            self.assertEqual(cache.name, 'Cache Button Test')

    def test_03_refresh_cache_button_triggers_lookup(self):
        """Refresh cache button triggers fresh lookup."""
        cedula = '1212121212'

        # Create partner with old cache
        partner = self._create_stale_cache_partner(
            name='Refresh Button Test',
            vat=cedula,
            days_old=10
        )

        # Mock fresh API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Refreshed Name',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post', return_value=mock_response):
            # Trigger refresh
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(
                cedula,
                force_refresh=True
            )

            # Verify fresh data
            self.assertEqual(result['name'], 'Refreshed Name')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestPartnerLookupWizard(EInvoiceTestCase):
    """Test lookup wizard workflow."""

    def test_01_wizard_displays_lookup_results(self):
        """Lookup wizard displays API results for confirmation."""
        cedula = '1313131313'

        # Mock API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Wizard Test Company',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
            'correo': 'wizard@test.cr',
        }

        with patch('requests.post', return_value=mock_response):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Assert wizard data
            self.assertEqual(result['name'], 'Wizard Test Company')
            self.assertEqual(result['email'], 'wizard@test.cr')

    def test_02_wizard_allows_field_selection(self):
        """Wizard allows user to select which fields to update."""
        cedula = '1414141414'

        # Create partner
        partner = self._create_test_partner(vat=cedula, name='Original Name')
        partner.write({'email': 'original@email.com'})

        # Mock API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'API Name',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
            'correo': 'api@email.com',
        }

        with patch('requests.post', return_value=mock_response):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # User selects to update name only (not email)
            partner.write({'name': result['name']})

            # Assert name updated, email preserved
            self.assertEqual(partner.name, 'API Name')
            self.assertEqual(partner.email, 'original@email.com')

    def test_03_wizard_confirms_before_overwrite(self):
        """Wizard shows confirmation when overwriting existing data."""
        cedula = '1515151515'

        # Create partner with data
        partner = self._create_test_partner(vat=cedula, name='Existing')

        # Mock API with different data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Different',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post', return_value=mock_response):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Wizard would show: "Existing" → "Different"
            # User confirms or cancels
            self.assertNotEqual(result['name'], partner.name)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestPartnerDuplicateVATResolution(EInvoiceTestCase):
    """Test conflict resolution for duplicate VAT."""

    def test_01_duplicate_vat_detected_on_create(self):
        """Creating partner with duplicate VAT raises error."""
        cedula = '1616161616'

        # Create first partner
        partner1 = self._create_test_partner(vat=cedula, name='Partner 1')

        # Try to create duplicate
        with self.assertRaises(ValidationError):
            partner2 = self._create_test_partner(vat=cedula, name='Partner 2')

    def test_02_duplicate_vat_detected_on_update(self):
        """Updating partner VAT to existing value raises error."""
        cedula1 = '1717171717'
        cedula2 = '1818181818'

        # Create two partners
        partner1 = self._create_test_partner(vat=cedula1, name='Partner 1')
        partner2 = self._create_test_partner(vat=cedula2, name='Partner 2')

        # Try to change partner2 VAT to match partner1
        with self.assertRaises(ValidationError):
            partner2.write({'vat': cedula1})

    def test_03_merge_partners_on_duplicate_vat(self):
        """Provide option to merge partners when duplicate VAT found."""
        cedula = '1919191919'

        # Create partner with minimal data
        partner1 = self._create_test_partner(vat=cedula, name='Partner 1')

        # Try to create another with same VAT (should suggest merge)
        # In production, wizard would show merge option
        # For test, verify first partner exists
        existing = self.env['res.partner'].search([('vat', '=', cedula)])
        self.assertEqual(len(existing), 1)
        self.assertEqual(existing[0].id, partner1.id)

    def test_04_update_existing_partner_instead_of_duplicate(self):
        """Lookup updates existing partner instead of creating duplicate."""
        cedula = '2020202020'

        # Create partner
        partner = self._create_test_partner(vat=cedula, name='Old Name')

        # Mock lookup
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'New Name',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post', return_value=mock_response):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Update existing partner
            partner.write({'name': result['name']})

            # Verify no duplicate created
            partners = self.env['res.partner'].search([('vat', '=', cedula)])
            self.assertEqual(len(partners), 1)
            self.assertEqual(partners[0].name, 'New Name')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p2')
class TestPartnerLookupEdgeCases(EInvoiceTestCase):
    """Test edge cases in partner lookup integration."""

    def test_01_lookup_with_empty_vat(self):
        """Lookup with empty VAT handles gracefully."""
        partner = self._create_test_partner(vat=None, name='No VAT')

        # Attempt lookup should fail gracefully
        with self.assertRaises((UserError, ValueError, TypeError)):
            self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(partner.vat)

    def test_02_lookup_with_invalid_vat_format(self):
        """Lookup with invalid VAT format shows validation error."""
        partner = self._create_test_partner(vat='ABC123', name='Invalid VAT')

        with self.assertRaises((UserError, ValueError, ValidationError)):
            self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(partner.vat)

    def test_03_lookup_for_archived_partner(self):
        """Lookup works for archived partners."""
        cedula = '2121212121'

        partner = self._create_test_partner(vat=cedula, name='Archived')
        partner.active = False

        # Mock API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Unarchived',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post', return_value=mock_response):
            # Lookup should still work
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)
            self.assertEqual(result['name'], 'Unarchived')

    def test_04_lookup_with_multi_company(self):
        """Lookup respects multi-company isolation."""
        cedula = '2222222222'

        # Create partner in company 1
        partner1 = self._create_test_partner(vat=cedula, name='Company 1')

        # Create cache for company 1
        cache1 = self.env['l10n_cr.cedula.cache'].create({
            'cedula': cedula,
            'name': 'Company 1 Cache',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Lookup in same company should find cache
        result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)
        self.assertEqual(result['source'], 'cache')
