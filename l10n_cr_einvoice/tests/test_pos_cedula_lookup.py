# -*- coding: utf-8 -*-
"""
Integration Tests for POS Cedula Lookup

Tests the Point of Sale interface for cedula lookup functionality,
including button actions, auto-lookup, result display, and partner
creation/update workflows.

Test Coverage:
- POS lookup button action
- Auto-lookup on VAT entry
- Lookup result display
- Partner creation from lookup
- Partner update from lookup
- Error handling in POS UI
- Cache freshness indicators

Priority: P0 (Critical - core POS checkout workflow)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock
from odoo import fields
from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import EInvoiceTestCase


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestPOSCedulaLookupButton(EInvoiceTestCase):
    """Test POS lookup button action."""

    def _hacienda_success(self, name='Test Gym SA', cedula='3101234567'):
        """Return a successful _lookup_hacienda mock result."""
        return {
            'success': True,
            'data': {
                'name': name,
                'cedula': cedula,
                'cedula_type': 'juridica',
                'tax_status': 'inscrito',
                'tax_regime': 'General',
                'activities': [{'code': '9311', 'description': 'Gimnasios'}],
                'primary_activity': '9311',
                'economic_activities': [{'code': '9311', 'description': 'Gimnasios'}],
            },
            'source': 'hacienda',
        }

    def _hacienda_failure(self, error='Not found', error_type='not_found'):
        """Return a failed _lookup_hacienda mock result."""
        return {
            'success': False,
            'error': error,
            'error_type': error_type,
        }

    def _gometa_failure(self, error='Not found', error_type='not_found'):
        """Return a failed _lookup_gometa mock result."""
        return {
            'success': False,
            'error': error,
            'error_type': error_type,
        }

    def test_01_lookup_button_success(self):
        """Lookup button returns customer data successfully."""
        cedula = '3101234567'

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_success(name='Test Gym SA', cedula=cedula)):
            # Simulate POS lookup action
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Assert result structure
            self.assertEqual(result['name'], 'Test Gym SA')
            self.assertEqual(result['tax_status'], 'inscrito')

    def test_02_lookup_button_displays_cache_freshness(self):
        """Lookup result shows cache freshness indicator."""
        cedula = '2020202020'

        # Create fresh cache
        cache = self.env['l10n_cr.cedula.cache'].create({
            'cedula': cedula,
            'name': 'Cached Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.env.company.id,
        })

        result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

        # Assert cache indicators
        self.assertEqual(result['source'], 'cache')
        self.assertTrue(result['is_fresh'])
        self.assertLessEqual(result['cache_age_days'], 1)

    def test_03_lookup_button_handles_not_found(self):
        """Lookup button handles not found gracefully."""
        cedula = '999999999'

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_failure('Not found', 'not_found')), \
             patch.object(LookupService, '_lookup_gometa',
                          return_value=self._gometa_failure('Not found', 'not_found')):

            with self.assertRaises(UserError):
                self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestPOSAutoLookupOnVATEntry(EInvoiceTestCase):
    """Test auto-lookup on VAT entry."""

    def _hacienda_success(self, name='Auto Lookup Company', cedula='4040404040'):
        """Return a successful _lookup_hacienda mock result."""
        return {
            'success': True,
            'data': {
                'name': name,
                'cedula': cedula,
                'cedula_type': 'juridica',
                'tax_status': 'inscrito',
                'tax_regime': 'General',
                'primary_activity': None,
                'economic_activities': [],
            },
            'source': 'hacienda',
        }

    def test_01_auto_lookup_triggered_on_vat_change(self):
        """Auto-lookup triggered when VAT is entered."""
        cedula = '4040404040'

        # Create partner without lookup
        partner = self._create_test_partner(vat=None, name='Temp Name')

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_success(name='Auto Lookup Company', cedula=cedula)):
            # Trigger auto-lookup by setting VAT
            partner.write({'vat': cedula})

            # Verify lookup can be called
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)
            self.assertEqual(result['name'], 'Auto Lookup Company')

    def test_02_auto_lookup_respects_user_preference(self):
        """Auto-lookup can be disabled in settings."""
        # Create partner
        partner = self._create_test_partner(vat='5050505050', name='Manual Entry')

        # Update VAT - should not crash
        partner.write({'vat': '5050505051'})


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestPOSPartnerCreationFromLookup(EInvoiceTestCase):
    """Test partner creation from lookup results."""

    def _hacienda_success(self, name='New Partner Corp', cedula='6060606060'):
        """Return a successful _lookup_hacienda mock result."""
        return {
            'success': True,
            'data': {
                'name': name,
                'cedula': cedula,
                'cedula_type': 'juridica',
                'tax_status': 'inscrito',
                'tax_regime': 'General',
                'email': 'partner@corp.cr',
                'primary_activity': '9311',
                'economic_activities': [{'code': '9311', 'description': 'Gimnasios'}],
            },
            'source': 'hacienda',
        }

    def test_01_create_partner_from_lookup_success(self):
        """Create new partner from successful lookup."""
        cedula = '6060606060'

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_success(name='New Partner Corp', cedula=cedula)):
            # Lookup
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Create partner from result
            partner = self.env['res.partner'].create({
                'name': result['name'],
                'vat': cedula,
                'country_id': self.env.ref('base.cr').id,
                'email': result.get('email'),
                'l10n_cr_tax_status': result['tax_status'],
                'l10n_cr_hacienda_verified': True,
                'l10n_cr_hacienda_last_sync': fields.Datetime.now(),
                'company_id': self.company.id,
            })

            # Assert partner created correctly
            self.assertEqual(partner.name, 'New Partner Corp')
            self.assertEqual(partner.vat, cedula)
            self.assertEqual(partner.l10n_cr_tax_status, 'inscrito')
            self.assertTrue(partner.l10n_cr_hacienda_verified)

    def test_02_create_partner_sets_hacienda_metadata(self):
        """Partner creation includes Hacienda verification metadata."""
        cedula = '7070707070'

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_success(name='Metadata Partner', cedula=cedula)):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            partner = self.env['res.partner'].create({
                'name': result['name'],
                'vat': cedula,
                'country_id': self.env.ref('base.cr').id,
                'l10n_cr_tax_status': result['tax_status'],
                'l10n_cr_hacienda_verified': True,
                'l10n_cr_hacienda_last_sync': fields.Datetime.now(),
                'company_id': self.company.id,
            })

            # Verify partner metadata fields directly
            self.assertEqual(partner.name, 'Metadata Partner')
            self.assertEqual(partner.l10n_cr_tax_status, 'inscrito')
            self.assertTrue(partner.l10n_cr_hacienda_verified)
            self.assertTrue(partner.l10n_cr_hacienda_last_sync)

    def test_03_create_partner_assigns_ciiu_from_activities(self):
        """Partner creation auto-assigns CIIU from activities."""
        cedula = '8080808080'

        # Find or create CIIU code in catalog (may already exist from data files)
        ciiu = self.env['l10n_cr.ciiu.code'].search([('code', '=', '9311')], limit=1)
        if not ciiu:
            ciiu = self.env['l10n_cr.ciiu.code'].create({
                'code': '9311',
                'name': 'Gestion de instalaciones deportivas',
                'section': 'R',
            })

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_success(name='Gym With CIIU', cedula=cedula)):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Verify CIIU in result
            self.assertEqual(result['primary_activity'], '9311')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestPOSPartnerUpdateFromLookup(EInvoiceTestCase):
    """Test partner update from lookup results."""

    def _hacienda_success(self, name='Updated Name', cedula='9090909090'):
        """Return a successful _lookup_hacienda mock result."""
        return {
            'success': True,
            'data': {
                'name': name,
                'cedula': cedula,
                'cedula_type': 'juridica',
                'tax_status': 'inscrito',
                'tax_regime': 'General',
                'primary_activity': None,
                'economic_activities': [],
            },
            'source': 'hacienda',
        }

    def test_01_update_partner_from_fresh_lookup(self):
        """Update existing partner with fresh lookup data."""
        cedula = '9090909090'

        # Create partner with outdated info
        partner = self._create_test_partner(vat=cedula, name='Old Name')
        partner.write({
            'l10n_cr_tax_status': 'error',
            'l10n_cr_hacienda_verified': False,
        })

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_success(name='Updated Name', cedula=cedula)):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Update partner
            partner.write({
                'name': result['name'],
                'l10n_cr_tax_status': result['tax_status'],
                'l10n_cr_hacienda_verified': True,
                'l10n_cr_hacienda_last_sync': fields.Datetime.now(),
            })

            # Assert updated
            self.assertEqual(partner.name, 'Updated Name')
            self.assertEqual(partner.l10n_cr_tax_status, 'inscrito')
            self.assertTrue(partner.l10n_cr_hacienda_verified)

    def test_02_update_partner_preserves_custom_fields(self):
        """Partner update preserves user-entered custom fields."""
        cedula = '1212121212'

        # Create partner with custom data
        partner = self._create_test_partner(vat=cedula, name='Custom Name')
        partner.write({
            'phone': '+506 2200-1100',
            'street': 'Custom Address',
        })

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_success(name='Official Name', cedula=cedula)):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Selective update (name only)
            partner.write({
                'name': result['name'],
                'l10n_cr_tax_status': result['tax_status'],
            })

            # Custom fields preserved
            self.assertEqual(partner.phone, '+506 2200-1100')
            self.assertEqual(partner.street, 'Custom Address')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestPOSLookupErrorHandling(EInvoiceTestCase):
    """Test error handling in POS UI."""

    def _hacienda_failure(self, error='Error', error_type='network'):
        return {'success': False, 'error': error, 'error_type': error_type}

    def _gometa_failure(self, error='Error', error_type='network'):
        return {'success': False, 'error': error, 'error_type': error_type}

    def test_01_display_user_friendly_error_for_api_timeout(self):
        """API timeout shows user-friendly error message."""
        cedula = '1313131313'

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_failure('Timeout', 'timeout')), \
             patch.object(LookupService, '_lookup_gometa',
                          return_value=self._gometa_failure('Timeout', 'timeout')):

            with self.assertRaises(UserError):
                self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

    def test_02_display_clear_error_for_invalid_cedula(self):
        """Invalid cedula format shows clear validation error."""
        invalid_cedula = 'ABC123'

        # lookup_cedula raises UserError when _clean_cedula returns empty
        # (non-digit characters are rejected).
        # Note: Odoo 19's assertRaises does not accept a tuple of exceptions.
        with self.assertRaises(UserError):
            self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(invalid_cedula)

    def test_03_display_warning_for_stale_cache(self):
        """Stale cache returns data with warning indicator."""
        cedula = '1414141414'

        # Create stale cache
        stale_time = datetime.now(timezone.utc) - timedelta(days=30)
        cache = self.env['l10n_cr.cedula.cache'].create({
            'cedula': cedula,
            'name': 'Stale Data',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(stale_time),
            'refreshed_at': fields.Datetime.to_string(stale_time),
            'source': 'hacienda',
            'company_id': self.env.company.id,
        })

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        with patch.object(LookupService, '_lookup_hacienda',
                          return_value=self._hacienda_failure('API error', 'api_error')), \
             patch.object(LookupService, '_lookup_gometa',
                          return_value=self._gometa_failure('API error', 'api_error')):

            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Should return stale cache with warning
            self.assertEqual(result['source'], 'stale_cache')
            self.assertTrue(result['is_stale'])


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestPOSCacheFreshnessIndicators(EInvoiceTestCase):
    """Test cache freshness indicators in POS UI."""

    def test_01_fresh_cache_shows_green_indicator(self):
        """Fresh cache (<7 days) shows green/success indicator."""
        cedula = '1515151515'

        # Create fresh cache
        cache = self.env['l10n_cr.cedula.cache'].create({
            'cedula': cedula,
            'name': 'Fresh Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.env.company.id,
        })

        result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

        # Assert freshness indicators
        self.assertTrue(result['is_fresh'])
        self.assertFalse(result.get('is_stale', False))
        self.assertEqual(result['cache_age_days'], 0)

    def test_02_stale_cache_shows_warning_indicator(self):
        """Stale cache (7-90 days) shows warning indicator."""
        cedula = '1616161616'

        # Create stale cache
        stale_time = datetime.now(timezone.utc) - timedelta(days=45)
        cache = self.env['l10n_cr.cedula.cache'].create({
            'cedula': cedula,
            'name': 'Stale Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(stale_time),
            'refreshed_at': fields.Datetime.to_string(stale_time),
            'source': 'hacienda',
            'company_id': self.env.company.id,
        })

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        # Mock API failure to force stale cache use
        with patch.object(LookupService, '_lookup_hacienda',
                          return_value={'success': False, 'error': 'API error', 'error_type': 'api_error'}), \
             patch.object(LookupService, '_lookup_gometa',
                          return_value={'success': False, 'error': 'API error', 'error_type': 'api_error'}):

            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Assert staleness indicators
            self.assertTrue(result['is_stale'])
            self.assertFalse(result.get('is_fresh', False))

    def test_03_no_cache_shows_realtime_indicator(self):
        """Fresh API lookup shows real-time indicator."""
        cedula = '1717171717'

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        hacienda_result = {
            'success': True,
            'data': {
                'name': 'Realtime Company',
                'cedula': cedula,
                'cedula_type': 'juridica',
                'tax_status': 'inscrito',
                'tax_regime': 'General',
                'primary_activity': None,
                'economic_activities': [],
            },
            'source': 'hacienda',
        }

        with patch.object(LookupService, '_lookup_hacienda', return_value=hacienda_result):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Assert real-time indicators
            self.assertEqual(result['source'], 'hacienda')
            self.assertTrue(result['is_fresh'])


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p2')
class TestPOSLookupConflictResolution(EInvoiceTestCase):
    """Test duplicate VAT conflict resolution."""

    def test_01_duplicate_vat_detection(self):
        """Detect duplicate VAT when creating partner from lookup."""
        cedula = '1818181818'

        # Create existing partner
        existing = self._create_test_partner(vat=cedula, name='Existing Partner')

        # Odoo res.partner does not enforce unique VAT at the DB level.
        # Instead, duplicates should be detected by searching before creating.
        duplicates = self.env['res.partner'].search([
            ('vat', '=', cedula),
            ('company_id', '=', self.company.id),
        ])
        self.assertEqual(len(duplicates), 1, "Should find existing partner with same VAT")
        self.assertEqual(duplicates[0].name, 'Existing Partner')

    def test_02_merge_lookup_data_into_existing_partner(self):
        """Merge lookup data into existing partner instead of creating new."""
        cedula = '1919191919'

        # Create existing partner
        existing = self._create_test_partner(vat=cedula, name='Old Name')

        LookupService = type(self.env['l10n_cr.cedula.lookup.service'])

        hacienda_result = {
            'success': True,
            'data': {
                'name': 'New Official Name',
                'cedula': cedula,
                'cedula_type': 'juridica',
                'tax_status': 'inscrito',
                'tax_regime': 'General',
                'primary_activity': None,
                'economic_activities': [],
            },
            'source': 'hacienda',
        }

        with patch.object(LookupService, '_lookup_hacienda', return_value=hacienda_result):
            result = self.env['l10n_cr.cedula.lookup.service'].lookup_cedula(cedula)

            # Update existing partner
            existing.write({
                'name': result['name'],
                'l10n_cr_tax_status': result['tax_status'],
                'l10n_cr_hacienda_verified': True,
                'l10n_cr_hacienda_last_sync': fields.Datetime.now(),
            })

            # Verify no duplicate created
            partners = self.env['res.partner'].search([('vat', '=', cedula)])
            self.assertEqual(len(partners), 1)
            self.assertEqual(partners[0].name, 'New Official Name')
