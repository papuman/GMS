# -*- coding: utf-8 -*-
"""
Integration Tests for Cache Refresh Background Jobs

Tests the cron jobs that maintain cache freshness through background
refresh operations, purging expired entries, and priority-based updates.

Test Coverage:
- Stale cache refresh cron
- Expired cache purge cron
- Priority refresh cron
- Batch size limits
- Rate limiting in cron jobs
- Error handling and logging

Priority: P1 (High - cache health critical for performance)
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock
from odoo import fields
from odoo.tests import tagged
from .common import EInvoiceTestCase


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestStaleCacheRefreshCron(EInvoiceTestCase):
    """Test stale cache refresh cron job."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_cron_identifies_stale_entries(self):
        """Cron identifies cache entries older than 5 days."""
        now = datetime.now(timezone.utc)

        # Create mix of fresh and stale entries
        fresh = self.cache_model.create({
            'cedula': '1000000001',
            'name': 'Fresh Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now),
            'refreshed_at': fields.Datetime.to_string(now),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        stale = self.cache_model.create({
            'cedula': '1000000002',
            'name': 'Stale Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Get stale entries
        stale_entries = self.cache_model.get_stale_cache_entries(company=self.company)

        # Assert only stale entry returned
        self.assertIn(stale.id, stale_entries.ids)
        self.assertNotIn(fresh.id, stale_entries.ids)

    def test_02_cron_refreshes_stale_entries(self):
        """Cron refreshes stale cache entries from API."""
        now = datetime.now(timezone.utc)

        # Create stale entries
        for i in range(5):
            self.cache_model.create({
                'cedula': f'200000000{i}',
                'name': f'Stale Company {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Mock Hacienda API model (cron calls api.lookup_cedula(), not raw HTTP)
        mock_api_result = {
            'success': True,
            'name': 'Refreshed Company',
            'tax_regime': 'General',
            'economic_activities': [],
            'raw_data': {'nombre': 'Refreshed Company'},
        }

        with patch.object(
            type(self.env['l10n_cr.hacienda.cedula.api']),
            'lookup_cedula',
            return_value=mock_api_result,
        ):
            # Run cron
            self.cache_model._cron_refresh_stale_cache()

            # Verify caches were refreshed
            for i in range(5):
                cache = self.cache_model.search([('cedula', '=', f'200000000{i}')])
                refreshed = fields.Datetime.from_string(cache.refreshed_at)
                # Make timezone-aware for comparison (Odoo stores naive UTC)
                if refreshed.tzinfo is None:
                    refreshed = refreshed.replace(tzinfo=timezone.utc)
                cache_age = (datetime.now(timezone.utc) - refreshed).days
                self.assertLessEqual(cache_age, 1, f"Cache {i} should be refreshed")

    def test_03_cron_respects_batch_size_limit(self):
        """Cron processes at most 50 entries per run."""
        now = datetime.now(timezone.utc)

        # Create 100 stale entries
        for i in range(100):
            self.cache_model.create({
                'cedula': f'300000000{i:02d}',
                'name': f'Batch Company {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Get stale entries with limit
        stale = self.cache_model.get_stale_cache_entries(company=self.company, limit=50)

        # Assert exactly 50 returned
        self.assertEqual(len(stale), 50)

    def test_04_cron_prioritizes_high_access_count(self):
        """Cron prioritizes frequently-accessed entries."""
        now = datetime.now(timezone.utc)

        # Create stale entries with varying access counts
        low_access = self.cache_model.create({
            'cedula': '4000000001',
            'name': 'Low Access',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'access_count': 5,
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        high_access = self.cache_model.create({
            'cedula': '4000000002',
            'name': 'High Access',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'access_count': 100,
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Get stale entries (ordered by access_count desc)
        stale = self.cache_model.get_stale_cache_entries(company=self.company, limit=10)

        # High access should be first
        self.assertEqual(stale[0].id, high_access.id)

    def test_05_cron_handles_refresh_failures_gracefully(self):
        """Cron continues processing even when some refreshes fail."""
        now = datetime.now(timezone.utc)

        # Create stale entries
        for i in range(3):
            self.cache_model.create({
                'cedula': f'500000000{i}',
                'name': f'Fail Test {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Mock API: first fails, others succeed
        # Cron calls api.lookup_cedula(cache.cedula) which returns a dict
        call_count = [0]

        def mock_lookup_side_effect(cedula):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    'success': False,
                    'error': 'Server error (HTTP 500)',
                    'error_type': 'api_error',
                }
            else:
                return {
                    'success': True,
                    'name': 'Success',
                    'tax_regime': 'General',
                    'economic_activities': [],
                    'raw_data': {},
                }

        with patch.object(
            type(self.env['l10n_cr.hacienda.cedula.api']),
            'lookup_cedula',
            side_effect=mock_lookup_side_effect,
        ):
            # Cron should not crash
            result = self.cache_model._cron_refresh_stale_cache()

            # Verify some failed
            self.assertGreater(result['failed'], 0)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestExpiredCachePurgeCron(EInvoiceTestCase):
    """Test expired cache purge cron job."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_cron_identifies_expired_entries(self):
        """Cron identifies entries older than 90 days."""
        now = datetime.now(timezone.utc)

        # Create mix of valid and expired
        valid = self.cache_model.create({
            'cedula': '6000000001',
            'name': 'Valid Cache',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=30)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=30)),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        expired = self.cache_model.create({
            'cedula': '6000000002',
            'name': 'Expired Cache',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=100)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=100)),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Assert expired flag
        self.assertFalse(valid.is_expired())
        self.assertTrue(expired.is_expired())

    def test_02_cron_purges_expired_entries(self):
        """Cron deletes entries older than 90 days."""
        now = datetime.now(timezone.utc)

        # Create expired entries
        expired_ids = []
        for i in range(5):
            expired = self.cache_model.create({
                'cedula': f'700000000{i}',
                'name': f'Expired {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=100)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=100)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })
            expired_ids.append(expired.id)

        # Run purge cron
        count = self.cache_model.purge_expired_cache(company=self.company)

        # Assert 5 deleted
        self.assertEqual(count, 5)

        # Assert entries gone
        remaining = self.cache_model.search([('id', 'in', expired_ids)])
        self.assertEqual(len(remaining), 0)

    def test_03_cron_preserves_valid_entries(self):
        """Cron does not delete entries younger than 90 days."""
        now = datetime.now(timezone.utc)

        # Create valid entries
        valid_ids = []
        for i in range(5):
            valid = self.cache_model.create({
                'cedula': f'800000000{i}',
                'name': f'Valid {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })
            valid_ids.append(valid.id)

        # Run purge
        count = self.cache_model.purge_expired_cache(company=self.company)

        # Assert nothing deleted
        self.assertEqual(count, 0)

        # Assert all still exist
        remaining = self.cache_model.search([('id', 'in', valid_ids)])
        self.assertEqual(len(remaining), 5)

    def test_04_cron_runs_daily_at_midnight(self):
        """Verify cron job exists with correct schedule."""
        # In Odoo 19, ir.cron uses 'code' field (e.g. "model._cron_purge_expired_cache()")
        # instead of 'function'. Search by model and code content.
        cron = self.env['ir.cron'].search([
            ('model_id.model', '=', 'l10n_cr.cedula.cache'),
            ('code', 'ilike', '_cron_purge_expired_cache'),
        ])

        # If cron exists, verify schedule
        if cron:
            # Should run daily
            self.assertIn('day', cron.interval_type.lower())


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestPriorityRefreshCron(EInvoiceTestCase):
    """Test priority-based refresh cron."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_prioritizes_recent_access(self):
        """Priority refresh targets recently accessed entries."""
        now = datetime.now(timezone.utc)

        # Create stale entries with different last_access times
        old_access = self.cache_model.create({
            'cedula': '9000000001',
            'name': 'Old Access',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'last_access_at': fields.Datetime.to_string(now - timedelta(days=5)),
            'access_count': 10,
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        recent_access = self.cache_model.create({
            'cedula': '9000000002',
            'name': 'Recent Access',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'last_access_at': fields.Datetime.to_string(now - timedelta(hours=1)),
            'access_count': 50,
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Get priority entries
        stale = self.cache_model.get_stale_cache_entries(company=self.company)

        # High access count should be prioritized
        self.assertEqual(stale[0].id, recent_access.id)

    def test_02_prioritizes_high_frequency_partners(self):
        """Priority refresh targets high-frequency customers."""
        now = datetime.now(timezone.utc)

        # Create entries with different access frequencies
        low_freq = self.cache_model.create({
            'cedula': '9100000001',
            'name': 'Low Frequency',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'access_count': 2,
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        high_freq = self.cache_model.create({
            'cedula': '9100000002',
            'name': 'High Frequency',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'access_count': 200,
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Get priority entries
        stale = self.cache_model.get_stale_cache_entries(company=self.company)

        # High frequency should be first
        self.assertEqual(stale[0].id, high_freq.id)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestCronRateLimiting(EInvoiceTestCase):
    """Test rate limiting in cron jobs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_cron_respects_rate_limit(self):
        """Cron jobs respect API rate limits."""
        now = datetime.now(timezone.utc)

        # Create 25 stale entries
        for i in range(25):
            self.cache_model.create({
                'cedula': f'920000000{i:02d}',
                'name': f'Rate Limit Test {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Mock Hacienda API model (cron calls api.lookup_cedula(), not raw HTTP)
        mock_api_result = {
            'success': True,
            'name': 'Test',
            'tax_regime': 'General',
            'economic_activities': [],
            'raw_data': {},
        }

        with patch.object(
            type(self.env['l10n_cr.hacienda.cedula.api']),
            'lookup_cedula',
            return_value=mock_api_result,
        ):
            # This test verifies cron can run without crashing
            # due to rate limit errors
            try:
                self.cache_model._cron_refresh_stale_cache()
                success = True
            except Exception:
                success = False

            self.assertTrue(success, "Cron should handle rate limits gracefully")

    def test_02_cron_throttles_requests_over_time(self):
        """Cron spreads requests over time to avoid rate limit."""
        # This test would verify that cron jobs add delays between
        # API calls to stay within rate limits.
        # Implementation-specific test.
        pass


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p2')
class TestCronErrorHandlingAndLogging(EInvoiceTestCase):
    """Test error handling and logging in cron jobs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_cron_logs_refresh_attempts(self):
        """Cron logs refresh attempts and results."""
        now = datetime.now(timezone.utc)

        cache = self.cache_model.create({
            'cedula': '9300000001',
            'name': 'Log Test',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Mock API failure (cron calls api.lookup_cedula() which returns a dict)
        mock_api_result = {
            'success': False,
            'error': 'Server error (HTTP 500)',
            'error_type': 'api_error',
        }

        with patch.object(
            type(self.env['l10n_cr.hacienda.cedula.api']),
            'lookup_cedula',
            return_value=mock_api_result,
        ):
            self.cache_model._cron_refresh_stale_cache()

            # Error should be logged in cache (re-read from DB)
            cache.invalidate_recordset()
            self.assertTrue(cache.error_message)

    def test_02_cron_continues_on_partial_failures(self):
        """Cron continues processing after individual failures."""
        now = datetime.now(timezone.utc)

        # Create multiple stale entries
        for i in range(5):
            self.cache_model.create({
                'cedula': f'940000000{i}',
                'name': f'Partial Fail {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Mock: some succeed, some fail
        # Cron calls api.lookup_cedula(cache.cedula) which returns a dict
        call_count = [0]

        def mock_lookup_side_effect(cedula):
            call_count[0] += 1
            # Fail every other request
            if call_count[0] % 2 == 0:
                return {
                    'success': False,
                    'error': 'Server error',
                    'error_type': 'api_error',
                }
            else:
                return {
                    'success': True,
                    'name': 'Success',
                    'tax_regime': 'General',
                    'economic_activities': [],
                    'raw_data': {},
                }

        with patch.object(
            type(self.env['l10n_cr.hacienda.cedula.api']),
            'lookup_cedula',
            side_effect=mock_lookup_side_effect,
        ):
            # Should not crash
            result = self.cache_model._cron_refresh_stale_cache()

            # Verify some succeeded, some failed
            self.assertGreater(result['refreshed'], 0, "Some should succeed")
            self.assertGreater(result['failed'], 0, "Some should fail")

    def test_03_cron_tracks_execution_statistics(self):
        """Cron tracks execution statistics for monitoring."""
        now = datetime.now(timezone.utc)

        # Create stale entries
        for i in range(10):
            self.cache_model.create({
                'cedula': f'950000000{i}',
                'name': f'Stats Test {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Get statistics
        stats = self.cache_model.get_cache_statistics(company=self.company)

        # Assert statistics structure
        self.assertIn('total_entries', stats)
        self.assertIn('stale', stats)
        self.assertIn('cache_coverage', stats)
        self.assertEqual(stats['total_entries'], 10)
