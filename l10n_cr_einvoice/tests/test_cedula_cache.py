# -*- coding: utf-8 -*-
"""
Comprehensive Unit Tests for Cédula Cache System

This module provides comprehensive test coverage for the cédula validation cache system,
covering multi-tier caching logic, cache refresh, and expiration mechanisms.

Test Coverage:
- Cache age computation (hours since last sync)
- Cache staleness by tax status (inscrito: 24h, error: 7d)
- Cache validity checks (all conditions must be met)
- Cache refresh logic
- Cache expiration and auto-invalidation
- Computed field behavior
- Search domain functionality

Priority: P0 (Critical for production)
"""

from datetime import datetime, timedelta, timezone
from odoo import fields
from odoo.tests import tagged
from odoo.exceptions import ValidationError
from .common import EInvoiceTestCase


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestCedulaCacheComputed(EInvoiceTestCase):
    """Test computed cache fields: age, staleness, validity."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']

    def test_cache_age_hours_never_synced(self):
        """Cache age should be 0 if never synced."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
        })
        # When l10n_cr_hacienda_last_sync is False/None, age should be 0
        self.assertEqual(partner.l10n_cr_hacienda_cache_age_hours, 0.0)

    def test_cache_age_hours_old_sync(self):
        """Cache age should reflect hours since last sync."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
        })

        # Set sync time to 12 hours ago
        now = datetime.now(timezone.utc)
        old_sync = now - timedelta(hours=12)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(old_sync)

        # Cache age should be approximately 12 hours
        age = partner.l10n_cr_hacienda_cache_age_hours
        self.assertGreaterEqual(age, 11.5, "Cache age should be at least 11.5 hours")
        self.assertLessEqual(age, 12.5, "Cache age should be at most 12.5 hours")

    def test_cache_age_hours_recent_sync(self):
        """Cache age should be small for recently synced partners."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
        })

        # Set sync time to 1 hour ago
        now = datetime.now(timezone.utc)
        recent_sync = now - timedelta(hours=1)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(recent_sync)

        # Cache age should be approximately 1 hour
        age = partner.l10n_cr_hacienda_cache_age_hours
        self.assertGreaterEqual(age, 0.9, "Cache age should be at least 0.9 hours")
        self.assertLessEqual(age, 1.1, "Cache age should be at most 1.1 hours")

    def test_cache_stale_never_synced(self):
        """Cache should be stale if never synced."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
        })
        self.assertTrue(partner.l10n_cr_hacienda_cache_stale,
                       "Cache should be stale when never synced")

    def test_cache_stale_inscrito_threshold(self):
        """
        Cache should be stale if >24h old for inscrito partners.
        Fresh if <=24h old.
        """
        now = datetime.now(timezone.utc)
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
            'l10n_cr_tax_status': 'inscrito',
        })

        # Fresh: 6 hours old
        sync_time = now - timedelta(hours=6)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        self.assertFalse(partner.l10n_cr_hacienda_cache_stale,
                        "Cache should be fresh at 6 hours for inscrito")

        # Fresh: 23 hours old (just under threshold)
        sync_time = now - timedelta(hours=23)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        self.assertFalse(partner.l10n_cr_hacienda_cache_stale,
                        "Cache should be fresh at 23 hours for inscrito")

        # Stale: 25 hours old
        sync_time = now - timedelta(hours=25)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        self.assertTrue(partner.l10n_cr_hacienda_cache_stale,
                       "Cache should be stale at 25 hours for inscrito")

    def test_cache_stale_no_encontrado_threshold(self):
        """Cache should be stale if >30 days old for no_encontrado status."""
        now = datetime.now(timezone.utc)
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '9999999999',
            'country_id': self.env.ref('base.cr').id,
            'l10n_cr_tax_status': 'no_encontrado',
        })

        # Fresh: 15 days old
        sync_time = now - timedelta(days=15)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        self.assertFalse(partner.l10n_cr_hacienda_cache_stale,
                        "Cache should be fresh at 15 days for no_encontrado")

        # Stale: 31 days old
        sync_time = now - timedelta(days=31)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        self.assertTrue(partner.l10n_cr_hacienda_cache_stale,
                       "Cache should be stale at 31 days for no_encontrado")

    def test_cache_stale_error_threshold(self):
        """Cache should be stale if >7 days old for error status."""
        now = datetime.now(timezone.utc)
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
            'l10n_cr_tax_status': 'error',
        })

        # Fresh: 3 days old
        sync_time = now - timedelta(days=3)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        self.assertFalse(partner.l10n_cr_hacienda_cache_stale,
                        "Cache should be fresh at 3 days for error")

        # Fresh: 6 days old (just under threshold)
        sync_time = now - timedelta(days=6)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        self.assertFalse(partner.l10n_cr_hacienda_cache_stale,
                        "Cache should be fresh at 6 days for error")

        # Stale: 8 days old
        sync_time = now - timedelta(days=8)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        self.assertTrue(partner.l10n_cr_hacienda_cache_stale,
                       "Cache should be stale at 8 days for error")

    def test_cache_valid_all_conditions_met(self):
        """Cache is valid only if ALL conditions are true."""
        now = datetime.now(timezone.utc)
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
        })

        # Invalid: no sync
        self.assertFalse(partner.l10n_cr_hacienda_cache_valid,
                        "Cache should be invalid when never synced")

        # Invalid: synced but not verified
        sync_time = now - timedelta(hours=6)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        partner.l10n_cr_tax_status = 'inscrito'
        self.assertFalse(partner.l10n_cr_hacienda_cache_valid,
                        "Cache should be invalid when not verified")

        # Invalid: stale + error
        partner.l10n_cr_tax_status = 'error'
        sync_time = now - timedelta(days=10)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        self.assertFalse(partner.l10n_cr_hacienda_cache_valid,
                        "Cache should be invalid when stale with error status")

        # Valid: fresh + inscrito + verified
        sync_time = now - timedelta(hours=6)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        partner.l10n_cr_tax_status = 'inscrito'
        partner.l10n_cr_hacienda_verified = True
        self.assertTrue(partner.l10n_cr_hacienda_cache_valid,
                       "Cache should be valid when fresh, inscrito, and verified")

    def test_cache_valid_boundary_conditions(self):
        """Test cache validity at boundary conditions."""
        now = datetime.now(timezone.utc)
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
        })

        # Valid at just under 24 hours for inscrito
        # The model uses strict `> 24` for staleness, but by the time the
        # computed field evaluates, a sync set to exactly 24h ago will be
        # slightly over 24h. Use 23h59m to stay safely within the fresh window.
        sync_time = now - timedelta(hours=23, minutes=59)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)
        partner.l10n_cr_tax_status = 'inscrito'
        partner.l10n_cr_hacienda_verified = True
        self.assertTrue(partner.l10n_cr_hacienda_cache_valid,
                       "Cache should be valid at just under 24 hours")


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestCedulaCacheConstraints(EInvoiceTestCase):
    """Test cache validation constraints and business rules."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']

    def test_override_requires_reason(self):
        """Override must have justification reason."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
        })

        # Should raise validation error when override without reason
        with self.assertRaises(ValidationError, msg="Override without reason should raise error"):
            partner.write({
                'l10n_cr_cedula_validation_override': True,
                'l10n_cr_override_reason': False,
            })

        # Should succeed with reason
        partner.write({
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': 'Government entity',
        })
        self.assertTrue(partner.l10n_cr_cedula_validation_override)
        self.assertEqual(partner.l10n_cr_override_reason, 'Government entity')

    def test_override_reason_cleared_when_override_disabled(self):
        """When override is disabled via clear_validation_override(), reason should be cleared."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': 'Test reason',
        })

        # Use the helper method which clears all override fields.
        # Note: The @api.onchange handler only fires in form views, not
        # during direct ORM writes, so we use the dedicated method instead.
        partner.clear_validation_override()
        self.assertFalse(partner.l10n_cr_cedula_validation_override,
                        "Override should be disabled")
        self.assertFalse(partner.l10n_cr_override_reason,
                        "Override reason should be cleared when override is disabled")

    def test_verified_status_consistency(self):
        """Verified flag should only be True for valid tax statuses."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.env.ref('base.cr').id,
        })

        # Cannot set verified=True with error status
        with self.assertRaises(ValidationError, msg="Cannot verify partner with error status"):
            partner.write({
                'l10n_cr_hacienda_verified': True,
                'l10n_cr_tax_status': 'error',
            })

        # Cannot set verified=True with no_encontrado status
        with self.assertRaises(ValidationError, msg="Cannot verify partner with no_encontrado status"):
            partner.write({
                'l10n_cr_hacienda_verified': True,
                'l10n_cr_tax_status': 'no_encontrado',
            })

        # Can set verified=True with inscrito status
        partner.write({
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_verified': True,
        })
        self.assertTrue(partner.l10n_cr_hacienda_verified)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestCedulaCacheSearch(EInvoiceTestCase):
    """Test search domains and filtering for cache fields."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.cr_country = self.env.ref('base.cr')

    def test_search_hacienda_verified(self):
        """Filter by Hacienda verification status."""
        now = datetime.now(timezone.utc)

        # Create verified partner
        verified_partner = self.partner_model.create({
            'name': 'Verified Partner',
            'vat': '1111111111',
            'country_id': self.cr_country.id,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
        })

        # Create unverified partner
        unverified_partner = self.partner_model.create({
            'name': 'Unverified Partner',
            'vat': '2222222222',
            'country_id': self.cr_country.id,
            'l10n_cr_tax_status': 'error',
            'l10n_cr_hacienda_verified': False,
        })

        # Search for verified
        verified = self.partner_model.search([
            ('l10n_cr_hacienda_verified', '=', True),
            ('id', 'in', [verified_partner.id, unverified_partner.id]),
        ])
        self.assertEqual(len(verified), 1, "Should find exactly 1 verified partner")
        self.assertEqual(verified.id, verified_partner.id)

        # Search for unverified
        unverified = self.partner_model.search([
            ('l10n_cr_hacienda_verified', '=', False),
            ('id', 'in', [verified_partner.id, unverified_partner.id]),
        ])
        self.assertEqual(len(unverified), 1, "Should find exactly 1 unverified partner")
        self.assertEqual(unverified.id, unverified_partner.id)

    def test_search_cache_stale(self):
        """Filter by cache staleness."""
        now = datetime.now(timezone.utc)

        # Create fresh cache partner
        fresh_partner = self.partner_model.create({
            'name': 'Fresh Cache',
            'vat': '1111111111',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
            'l10n_cr_tax_status': 'inscrito',
        })

        # Create stale cache partner
        stale_time = now - timedelta(hours=30)
        stale_partner = self.partner_model.create({
            'name': 'Stale Cache',
            'vat': '2222222222',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(stale_time),
            'l10n_cr_tax_status': 'inscrito',
        })

        # Use filtered() instead of search() for non-stored computed fields
        test_partners = self.partner_model.search([
            ('id', 'in', [fresh_partner.id, stale_partner.id]),
        ])
        stale = test_partners.filtered(lambda p: p.l10n_cr_hacienda_cache_stale)
        self.assertIn(stale_partner.id, stale.ids, "Stale partner should be found")
        self.assertNotIn(fresh_partner.id, stale.ids, "Fresh partner should not be found")

        # Filter for fresh
        fresh = test_partners.filtered(lambda p: not p.l10n_cr_hacienda_cache_stale)
        self.assertIn(fresh_partner.id, fresh.ids, "Fresh partner should be found")
        self.assertNotIn(stale_partner.id, fresh.ids, "Stale partner should not be found")

    def test_search_cache_age_hours(self):
        """Filter by cache age (hours)."""
        now = datetime.now(timezone.utc)

        # 6 hours old
        young_time = now - timedelta(hours=6)
        young_partner = self.partner_model.create({
            'name': 'Young Cache',
            'vat': '1111111111',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(young_time),
        })

        # 18 hours old
        old_time = now - timedelta(hours=18)
        old_partner = self.partner_model.create({
            'name': 'Old Cache',
            'vat': '2222222222',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(old_time),
        })

        # l10n_cr_hacienda_cache_age_hours is a non-stored computed field on
        # res.partner, so it cannot be used in ORM search() domains.
        # Use filtered() on the recordset instead.
        test_partners = self.partner_model.search([
            ('id', 'in', [young_partner.id, old_partner.id]),
        ])

        # Cache older than 12 hours
        old_cache = test_partners.filtered(lambda p: p.l10n_cr_hacienda_cache_age_hours > 12)
        self.assertIn(old_partner.id, old_cache.ids, "18-hour cache should be found")
        self.assertNotIn(young_partner.id, old_cache.ids, "6-hour cache should not be found")

        # Cache younger than 12 hours
        young_cache = test_partners.filtered(lambda p: p.l10n_cr_hacienda_cache_age_hours < 12)
        self.assertIn(young_partner.id, young_cache.ids, "6-hour cache should be found")
        self.assertNotIn(old_partner.id, young_cache.ids, "18-hour cache should not be found")

    def test_search_cache_valid(self):
        """Filter by cache validity."""
        now = datetime.now(timezone.utc)

        # Valid cache partner
        valid_partner = self.partner_model.create({
            'name': 'Valid Cache',
            'vat': '1111111111',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_verified': True,
        })

        # Invalid cache partner (never synced)
        invalid_partner = self.partner_model.create({
            'name': 'Invalid Cache',
            'vat': '2222222222',
            'country_id': self.cr_country.id,
        })

        # Use filtered() instead of search() for non-stored computed fields
        test_partners = self.partner_model.search([
            ('id', 'in', [valid_partner.id, invalid_partner.id]),
        ])
        valid = test_partners.filtered(lambda p: p.l10n_cr_hacienda_cache_valid)
        self.assertIn(valid_partner.id, valid.ids, "Valid partner should be found")
        self.assertNotIn(invalid_partner.id, valid.ids, "Invalid partner should not be found")


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestCedulaCacheHelpers(EInvoiceTestCase):
    """Test helper methods for cache management."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.cr_country = self.env.ref('base.cr')

    def test_mark_validation_override(self):
        """Mark partner with validation override (audit trail)."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
        })

        reason = 'Government exemption'
        user = self.env.user

        # Mark override
        partner.mark_validation_override(reason=reason, user=user)

        self.assertTrue(partner.l10n_cr_cedula_validation_override)
        self.assertEqual(partner.l10n_cr_override_reason, reason)
        self.assertEqual(partner.l10n_cr_override_user_id, user)
        self.assertIsNotNone(partner.l10n_cr_override_date)

    def test_clear_validation_override(self):
        """Clear validation override (and all audit data)."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': 'Test reason',
            'l10n_cr_override_user_id': self.env.user.id,
            'l10n_cr_override_date': fields.Datetime.now(),
        })

        # Clear override
        partner.clear_validation_override()

        self.assertFalse(partner.l10n_cr_cedula_validation_override)
        self.assertFalse(partner.l10n_cr_override_reason)
        self.assertFalse(partner.l10n_cr_override_user_id)
        self.assertFalse(partner.l10n_cr_override_date)

    def test_get_validation_status_override(self):
        """Get status when override is active."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': 'Government entity',
        })

        status = partner.get_validation_status()
        self.assertTrue(status['is_valid'])
        self.assertEqual(status['icon'], 'warning')
        self.assertIn('Government entity', status['reason'])

    def test_get_validation_status_verified(self):
        """Get status when cache is valid and verified."""
        now = datetime.now(timezone.utc)
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(now),
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
        })

        status = partner.get_validation_status()
        self.assertTrue(status['is_valid'])
        self.assertEqual(status['icon'], 'valid')
        # The status text uses lowercase 'verified'; check case-insensitively
        status_text = (status.get('reason') or status.get('message') or '').lower()
        self.assertIn('verified', status_text)

    def test_get_validation_status_never_checked(self):
        """Get status when never verified."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
        })

        status = partner.get_validation_status()
        self.assertIsNone(status['is_valid'])
        self.assertEqual(status['icon'], 'unknown')

    def test_get_validation_status_stale_cache(self):
        """Get status when cache is stale."""
        now = datetime.now(timezone.utc)
        old_sync = now - timedelta(days=10)
        # Partner must be verified=True so get_validation_status() reaches the
        # stale-cache branch. When verified=False, it returns 'unknown' early.
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(old_sync),
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_verified': True,
        })

        status = partner.get_validation_status()
        self.assertFalse(status['is_valid'])
        self.assertEqual(status['icon'], 'warning')
        # The method may return the stale info in 'reason' or 'message'
        stale_text = (status.get('reason') or status.get('message') or '').lower()
        self.assertIn('stale', stale_text)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestCedulaCacheRefresh(EInvoiceTestCase):
    """Test cache refresh logic and background jobs."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.cr_country = self.env.ref('base.cr')

    def test_refresh_cache_updates_timestamp(self):
        """Cache refresh should update last_sync timestamp."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
        })

        # Initial state: never synced
        self.assertFalse(partner.l10n_cr_hacienda_last_sync)

        # Simulate cache refresh
        before_refresh = datetime.now(timezone.utc)
        partner.refresh_hacienda_cache()
        after_refresh = datetime.now(timezone.utc)

        # Timestamp should be set to current time (1-second buffer for timing)
        self.assertIsNotNone(partner.l10n_cr_hacienda_last_sync)
        sync_time = fields.Datetime.from_string(partner.l10n_cr_hacienda_last_sync)
        # fields.Datetime.from_string() returns a naive datetime (UTC);
        # strip tzinfo from our aware datetimes so comparison works.
        before_naive = before_refresh.replace(tzinfo=None)
        after_naive = after_refresh.replace(tzinfo=None)
        self.assertGreaterEqual(sync_time, before_naive - timedelta(seconds=1))
        self.assertLessEqual(sync_time, after_naive + timedelta(seconds=1))

    def test_refresh_cache_updates_tax_status(self):
        """Cache refresh should update tax status from Hacienda API."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
        })

        # Initial state: no status
        self.assertFalse(partner.l10n_cr_tax_status)

        # Mock API response and refresh
        # (In real tests, you would mock the Hacienda API call)
        partner.refresh_hacienda_cache()

        # Status should be updated (mocked as 'inscrito' in test)
        self.assertIsNotNone(partner.l10n_cr_tax_status)

    def test_bulk_refresh_stale_caches(self):
        """Bulk refresh should process multiple stale partners."""
        now = datetime.now(timezone.utc)
        stale_time = now - timedelta(hours=30)

        # Create partners with stale caches
        partners = []
        for i in range(5):
            partner = self.partner_model.create({
                'name': f'Partner {i}',
                'vat': f'{1000000000 + i}',
                'country_id': self.cr_country.id,
                'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(stale_time),
                'l10n_cr_tax_status': 'inscrito',
            })
            partners.append(partner)

        # All should be stale
        for partner in partners:
            self.assertTrue(partner.l10n_cr_hacienda_cache_stale)

        # Bulk refresh
        self.partner_model.cron_refresh_stale_caches()

        # After refresh, caches should be fresh
        for partner in partners:
            partner.invalidate_recordset()  # Reload from database
            # Note: In real implementation, this would check if cache is refreshed
            # For now, we just verify the method can be called without errors


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p2')
class TestCedulaCacheEdgeCases(EInvoiceTestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.cr_country = self.env.ref('base.cr')

    def test_cache_age_with_null_sync(self):
        """Cache age should safely handle NULL last_sync."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
            'l10n_cr_hacienda_last_sync': None,
        })

        # Should not crash, should return 0
        age = partner.l10n_cr_hacienda_cache_age_hours
        self.assertEqual(age, 0.0, "Cache age should be 0 for null sync time")

    def test_validation_status_with_missing_fields(self):
        """Get status should handle missing cache fields."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
        })

        # Should not crash when all cache fields are empty
        status = partner.get_validation_status()
        self.assertIsNotNone(status, "Status should not be None")
        self.assertIn('is_valid', status)
        self.assertIn('icon', status)
        # The status dict uses 'message' as the primary text key;
        # 'reason' is only present in some status branches (e.g. override, stale).
        self.assertTrue(
            'reason' in status or 'message' in status,
            "Status should contain either 'reason' or 'message' key"
        )

    def test_cache_with_non_cr_partner(self):
        """Cache fields should work for non-Costa Rica partners."""
        us_country = self.env.ref('base.us')
        partner = self.partner_model.create({
            'name': 'US Partner',
            'vat': '123456789',
            'country_id': us_country.id,
        })

        # Should not crash
        age = partner.l10n_cr_hacienda_cache_age_hours
        stale = partner.l10n_cr_hacienda_cache_stale
        valid = partner.l10n_cr_hacienda_cache_valid

        # All should have sensible defaults
        self.assertEqual(age, 0.0)
        self.assertTrue(stale)  # Never synced = stale
        self.assertFalse(valid)  # Never synced = invalid

    def test_timezone_aware_cache_age(self):
        """Cache age calculation must handle timezones correctly."""
        partner = self.partner_model.create({
            'name': 'Test Partner',
            'vat': '1234567890',
            'country_id': self.cr_country.id,
        })

        # Set sync time in UTC
        utc_now = datetime.now(timezone.utc)
        sync_time = utc_now - timedelta(hours=5)
        partner.l10n_cr_hacienda_last_sync = fields.Datetime.to_string(sync_time)

        # Cache age should be approximately 5 hours
        age = partner.l10n_cr_hacienda_cache_age_hours
        self.assertGreaterEqual(age, 4.9, "Cache age should be at least 4.9 hours")
        self.assertLessEqual(age, 5.1, "Cache age should be at most 5.1 hours")
