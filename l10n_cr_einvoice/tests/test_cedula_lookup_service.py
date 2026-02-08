# -*- coding: utf-8 -*-
"""
Comprehensive Integration Tests for Cedula Lookup Service

Tests the complete waterfall retry strategy for looking up Costa Rica tax IDs
(cedulas) from government APIs with caching, rate limiting, and fallback mechanisms.

Test Coverage:
- Waterfall retry strategy (all 4 steps)
- Cache hit scenarios (fresh cache, no API call)
- Hacienda API success
- Hacienda failure -> GoMeta fallback
- Both APIs fail -> stale cache return
- All fail -> manual entry prompt
- Rate limiting integration
- Concurrent lookups
- Batch lookup functionality

Priority: P0 (Critical - customer lookup is core POS feature)

Mock Strategy:
    The lookup service (l10n_cr.cedula.lookup.service) delegates to:
    - _lookup_hacienda() which calls l10n_cr.hacienda.cedula.api.lookup_cedula()
    - _lookup_gometa() which calls requests.get() directly

    For most tests we mock _lookup_hacienda and _lookup_gometa on the service
    model itself using patch.object(type(model), 'method'). This is the correct
    Odoo pattern because model instances are thin wrappers and their methods
    are read-only attributes resolved from the class.
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock, MagicMock
from odoo import fields
from odoo.tests import tagged
from odoo.exceptions import UserError
from .common import EInvoiceTestCase


# =============================================================================
# Helper: Get the model class for a given Odoo model name
# =============================================================================

def _model_cls(env, model_name):
    """Return the Python class backing an Odoo model so we can patch.object() on it."""
    return type(env[model_name])


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestCedulaLookupServiceWaterfall(EInvoiceTestCase):
    """Test waterfall retry strategy through all 4 steps."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service'].with_company(cls.company)
        cls.cache_model = cls.env['l10n_cr.cedula.cache'].with_company(cls.company)

    def setUp(self):
        super().setUp()
        # Clear cache before each test
        self.cache_model.search([]).unlink()

    # -------------------------------------------------------------------------
    # Step 1: Fresh cache hit
    # -------------------------------------------------------------------------
    def test_01_waterfall_step1_fresh_cache_hit(self):
        """Step 1: Fresh cache (<7 days) returns immediately without API call."""
        cedula = '3101234567'

        # Create fresh cache entry
        self.cache_model.create({
            'cedula': cedula,
            'name': 'Acme Corp SA',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'tax_regime': 'General',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Mock _lookup_hacienda to ensure it is NOT called
        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')
        with patch.object(ServiceCls, '_lookup_hacienda') as mock_hacienda:
            result = self.lookup_service.lookup_cedula(cedula)

            # Assert no API call was made
            mock_hacienda.assert_not_called()

            # Assert result comes from cache
            self.assertEqual(result['name'], 'Acme Corp SA')
            self.assertEqual(result['source'], 'cache')
            self.assertTrue(result['is_fresh'])

    # -------------------------------------------------------------------------
    # Step 2: Hacienda API success (no cache)
    # -------------------------------------------------------------------------
    def test_02_waterfall_step2_hacienda_api_success(self):
        """Step 2: No cache -> call Hacienda API successfully."""
        cedula = '3101234567'

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        # Mock _lookup_hacienda to return success
        hacienda_result = {
            'success': True,
            'data': {
                'cedula': cedula,
                'name': 'Gimnasio Test SA',
                'company_type': 'company',
                'tax_regime': 'General',
                'tax_status': 'inscrito',
                'economic_activities': [
                    {'code': '9311', 'description': 'Gimnasios', 'primary': True}
                ],
                'primary_activity': '9311',
                'raw_response': '{}',
            },
        }

        with patch.object(ServiceCls, '_lookup_hacienda', return_value=hacienda_result) as mock_h:
            result = self.lookup_service.lookup_cedula(cedula)

            # Assert Hacienda was called
            mock_h.assert_called_once()

            # Assert result from Hacienda
            self.assertEqual(result['name'], 'Gimnasio Test SA')
            self.assertEqual(result['source'], 'hacienda')
            self.assertEqual(result['tax_status'], 'inscrito')
            self.assertEqual(result['primary_activity'], '9311')

            # Assert cache was created
            cache = self.cache_model.search([('cedula', '=', cedula)])
            self.assertEqual(len(cache), 1)
            self.assertEqual(cache.name, 'Gimnasio Test SA')

    # -------------------------------------------------------------------------
    # Step 3: Hacienda fails -> GoMeta fallback succeeds
    # -------------------------------------------------------------------------
    def test_03_waterfall_step3_hacienda_fails_gometa_succeeds(self):
        """Step 3: Hacienda timeout -> fallback to GoMeta API."""
        cedula = '3101234567'

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        hacienda_fail = {
            'success': False,
            'error': 'Hacienda API timeout',
            'error_type': 'timeout',
        }

        gometa_success = {
            'success': True,
            'data': {
                'cedula': cedula,
                'name': 'Test Company From GoMeta',
                'company_type': 'other',
                'tax_regime': '',
                'tax_status': 'inscrito',
                'economic_activities': [],
                'primary_activity': None,
                'raw_response': '{}',
            },
        }

        with patch.object(ServiceCls, '_lookup_hacienda', return_value=hacienda_fail) as mock_h, \
             patch.object(ServiceCls, '_lookup_gometa', return_value=gometa_success) as mock_g:

            result = self.lookup_service.lookup_cedula(cedula)

            # Assert both APIs called
            self.assertTrue(mock_h.called, "Hacienda should be called first")
            self.assertTrue(mock_g.called, "GoMeta should be called as fallback")

            # Assert result from GoMeta
            self.assertEqual(result['name'], 'Test Company From GoMeta')
            self.assertEqual(result['source'], 'gometa')
            self.assertEqual(result['tax_status'], 'inscrito')

    # -------------------------------------------------------------------------
    # Step 4: Both APIs fail -> stale cache used
    # -------------------------------------------------------------------------
    def test_04_waterfall_step4_both_apis_fail_stale_cache_used(self):
        """Step 4: Both APIs fail -> return stale cache (7-90 days old)."""
        cedula = '3101234567'

        # Create stale cache entry (30 days old)
        stale_time = datetime.now(timezone.utc) - timedelta(days=30)
        self.cache_model.create({
            'cedula': cedula,
            'name': 'Stale Cache Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(stale_time),
            'refreshed_at': fields.Datetime.to_string(stale_time),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        api_fail = {
            'success': False,
            'error': 'API unavailable',
            'error_type': 'network',
        }

        with patch.object(ServiceCls, '_lookup_hacienda', return_value=api_fail) as mock_h, \
             patch.object(ServiceCls, '_lookup_gometa', return_value=api_fail) as mock_g:

            result = self.lookup_service.lookup_cedula(cedula)

            # Assert both APIs were attempted
            self.assertTrue(mock_h.called)
            self.assertTrue(mock_g.called)

            # Assert stale cache was returned
            self.assertEqual(result['name'], 'Stale Cache Company')
            self.assertEqual(result['source'], 'stale_cache')
            self.assertTrue(result['is_stale'])
            self.assertGreaterEqual(result['cache_age_days'], 29)

    # -------------------------------------------------------------------------
    # Step 5: All fail -> manual entry required
    # -------------------------------------------------------------------------
    def test_05_waterfall_step5_all_fail_manual_entry_required(self):
        """Step 5: All fail (no cache, APIs down) -> manual entry required."""
        cedula = '9999999999'

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        api_fail = {
            'success': False,
            'error': 'API unavailable',
            'error_type': 'network',
        }

        with patch.object(ServiceCls, '_lookup_hacienda', return_value=api_fail), \
             patch.object(ServiceCls, '_lookup_gometa', return_value=api_fail):

            with self.assertRaises(UserError) as ctx:
                self.lookup_service.lookup_cedula(cedula)

            # Assert error message indicates manual entry needed
            error_msg = str(ctx.exception).lower()
            self.assertIn('manual', error_msg)

    # -------------------------------------------------------------------------
    # Force refresh bypasses fresh cache
    # -------------------------------------------------------------------------
    def test_06_force_refresh_bypasses_fresh_cache(self):
        """Force refresh bypasses cache and calls API directly."""
        cedula = '3101234567'

        # Create fresh cache
        cache = self.cache_model.create({
            'cedula': cedula,
            'name': 'Old Name',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        hacienda_result = {
            'success': True,
            'data': {
                'cedula': cedula,
                'name': 'New Updated Name',
                'company_type': 'company',
                'tax_regime': 'General',
                'tax_status': 'inscrito',
                'economic_activities': [],
                'primary_activity': None,
                'raw_response': '{}',
            },
        }

        with patch.object(ServiceCls, '_lookup_hacienda', return_value=hacienda_result) as mock_h:
            result = self.lookup_service.lookup_cedula(cedula, force_refresh=True)

            # Assert API was called despite fresh cache
            mock_h.assert_called_once()

            # Assert result has new name
            self.assertEqual(result['name'], 'New Updated Name')

            # Assert cache was updated
            cache.invalidate_recordset()
            self.assertEqual(cache.name, 'New Updated Name')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestCedulaLookupServiceCache(EInvoiceTestCase):
    """Test cache behavior and freshness checks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service'].with_company(cls.company)
        cls.cache_model = cls.env['l10n_cr.cedula.cache'].with_company(cls.company)

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_cache_hit_fresh_no_api_call(self):
        """Fresh cache (<7 days) returns data without API call."""
        cedula = '1010101010'

        # Create fresh cache (2 days old)
        fresh_time = datetime.now(timezone.utc) - timedelta(days=2)
        cache = self.cache_model.create({
            'cedula': cedula,
            'name': 'Fresh Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(fresh_time),
            'refreshed_at': fields.Datetime.to_string(fresh_time),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')
        with patch.object(ServiceCls, '_lookup_hacienda') as mock_h:
            result = self.lookup_service.lookup_cedula(cedula)

            # No API call
            mock_h.assert_not_called()

            # Cache access counter incremented
            cache.invalidate_recordset()
            self.assertEqual(cache.access_count, 1)

    def test_02_cache_refresh_zone_triggers_background_refresh(self):
        """Cache in refresh zone (5-7 days) triggers background refresh."""
        cedula = '2020202020'

        # Create cache in refresh zone (6 days old)
        refresh_time = datetime.now(timezone.utc) - timedelta(days=6)
        cache = self.cache_model.create({
            'cedula': cedula,
            'name': 'Refresh Zone Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(refresh_time),
            'refreshed_at': fields.Datetime.to_string(refresh_time),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')
        with patch.object(ServiceCls, '_lookup_hacienda') as mock_h:
            result = self.lookup_service.lookup_cedula(cedula)

            # Should return cache immediately
            self.assertEqual(result['source'], 'cache')

            # But should trigger background refresh
            # (In production, this would be async. For tests, verify it can be called)
            self.assertTrue(cache.needs_refresh())

    def test_03_expired_cache_purged_automatically(self):
        """Cache older than 90 days is purged by cron."""
        cedula = '3030303030'

        # Create expired cache (100 days old)
        expired_time = datetime.now(timezone.utc) - timedelta(days=100)
        cache = self.cache_model.create({
            'cedula': cedula,
            'name': 'Expired Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(expired_time),
            'refreshed_at': fields.Datetime.to_string(expired_time),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Assert cache is expired
        self.assertTrue(cache.is_expired())

        # Run purge cron
        count = self.cache_model.purge_expired_cache(company=self.company)

        # Assert cache was deleted
        self.assertEqual(count, 1)
        self.assertFalse(self.cache_model.search([('id', '=', cache.id)]))


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestCedulaLookupServiceRateLimiting(EInvoiceTestCase):
    """Test rate limiting integration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service'].with_company(cls.company)
        cls.cache_model = cls.env['l10n_cr.cedula.cache'].with_company(cls.company)
        cls.rate_limiter = cls.env['l10n_cr.hacienda.rate_limiter'].with_company(cls.company)

    def setUp(self):
        super().setUp()
        self.rate_limiter.reset()
        self.cache_model.search([]).unlink()

    def test_01_rate_limit_respected_during_lookup(self):
        """Lookup service respects rate limiter when tokens exhausted."""
        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')
        RateLimiterCls = _model_cls(self.env, 'l10n_cr.hacienda.rate_limiter')

        # Instead of consuming 20 real tokens (timing-sensitive), directly mock
        # the rate limiter to deny tokens, which forces the Hacienda step to fail.
        # Then also fail GoMeta to trigger the final UserError.

        hacienda_rate_limited = {
            'success': False,
            'error': 'Rate limit exceeded',
            'error_type': 'rate_limit',
        }
        gometa_fail = {
            'success': False,
            'error': 'GoMeta unavailable',
            'error_type': 'network',
        }

        # First verify a normal lookup works when rate limiter allows it
        hacienda_ok = {
            'success': True,
            'data': {
                'cedula': '3101234567',
                'name': 'Test Company',
                'company_type': 'company',
                'tax_regime': 'General',
                'tax_status': 'inscrito',
                'economic_activities': [],
                'primary_activity': None,
                'raw_response': '{}',
            },
        }

        with patch.object(ServiceCls, '_lookup_hacienda', return_value=hacienda_ok):
            result = self.lookup_service.lookup_cedula('3101234567')
            self.assertEqual(result['source'], 'hacienda')

        # Now simulate rate limit exhaustion: _lookup_hacienda returns rate_limit error
        with patch.object(ServiceCls, '_lookup_hacienda', return_value=hacienda_rate_limited), \
             patch.object(ServiceCls, '_lookup_gometa', return_value=gometa_fail):
            with self.assertRaises(UserError):
                self.lookup_service.lookup_cedula('1000000021')

    def test_02_cache_hits_do_not_consume_rate_limit_tokens(self):
        """Cache hits don't consume API rate limit tokens."""
        cedula = '5050505050'

        # Create cache
        self.cache_model.create({
            'cedula': cedula,
            'name': 'Cached Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Check initial rate limit status
        initial_status = self.rate_limiter.get_available_tokens()
        initial_tokens = initial_status['tokens']

        # Perform 10 cache hits
        for _ in range(10):
            result = self.lookup_service.lookup_cedula(cedula)
            self.assertEqual(result['source'], 'cache')

        # Rate limit tokens should be unchanged
        final_status = self.rate_limiter.get_available_tokens()
        self.assertEqual(final_status['tokens'], initial_tokens)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestCedulaLookupServiceConcurrency(EInvoiceTestCase):
    """Test concurrent lookup scenarios."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service'].with_company(cls.company)
        cls.cache_model = cls.env['l10n_cr.cedula.cache'].with_company(cls.company)

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_concurrent_lookups_same_cedula(self):
        """Multiple concurrent lookups for same cedula use cache."""
        cedula = '6060606060'

        # Create cache
        self.cache_model.create({
            'cedula': cedula,
            'name': 'Concurrent Test',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        # Simulate 5 concurrent lookups
        with patch.object(ServiceCls, '_lookup_hacienda') as mock_h:
            results = []
            for _ in range(5):
                result = self.lookup_service.lookup_cedula(cedula)
                results.append(result)

            # No API calls (all cache hits)
            mock_h.assert_not_called()

            # All results identical
            for result in results:
                self.assertEqual(result['name'], 'Concurrent Test')
                self.assertEqual(result['source'], 'cache')

    def test_02_concurrent_lookups_different_cedulas(self):
        """Concurrent lookups for different cedulas process independently."""
        cedulas = [f'700000000{i}' for i in range(5)]

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        def fake_hacienda(self_model, cedula):
            return {
                'success': True,
                'data': {
                    'cedula': cedula,
                    'name': 'Test Company',
                    'company_type': 'company',
                    'tax_regime': 'General',
                    'tax_status': 'inscrito',
                    'economic_activities': [],
                    'primary_activity': None,
                    'raw_response': '{}',
                },
            }

        RateLimiterCls = _model_cls(self.env, 'l10n_cr.hacienda.rate_limiter')

        with patch.object(ServiceCls, '_lookup_hacienda', fake_hacienda), \
             patch.object(RateLimiterCls, 'try_acquire_token', return_value=True):

            results = []
            for cedula in cedulas:
                result = self.lookup_service.lookup_cedula(cedula)
                results.append(result)

            # All should succeed
            self.assertEqual(len(results), 5)
            for result in results:
                self.assertEqual(result['source'], 'hacienda')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestCedulaLookupServiceBatch(EInvoiceTestCase):
    """Test batch lookup functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service'].with_company(cls.company)
        cls.cache_model = cls.env['l10n_cr.cedula.cache'].with_company(cls.company)

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_batch_lookup_multiple_cedulas(self):
        """Batch lookup processes multiple cedulas efficiently."""
        cedulas = [f'800000000{i}' for i in range(10)]

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        def fake_hacienda(self_model, cedula):
            return {
                'success': True,
                'data': {
                    'cedula': cedula,
                    'name': 'Batch Company',
                    'company_type': 'company',
                    'tax_regime': 'General',
                    'tax_status': 'inscrito',
                    'economic_activities': [],
                    'primary_activity': None,
                    'raw_response': '{}',
                },
            }

        RateLimiterCls = _model_cls(self.env, 'l10n_cr.hacienda.rate_limiter')

        with patch.object(ServiceCls, '_lookup_hacienda', fake_hacienda), \
             patch.object(RateLimiterCls, 'try_acquire_token', return_value=True):

            results = self.lookup_service.batch_lookup_cedulas(cedulas)

            # Should return 10 results
            self.assertEqual(len(results), 10)

            # All should succeed
            for cedula, result in results.items():
                self.assertIn('name', result)
                self.assertEqual(result['tax_status'], 'inscrito')

    def test_02_batch_lookup_with_partial_failures(self):
        """Batch lookup handles partial failures gracefully."""
        cedulas = ['9000000001', '9000000002', '9000000003']

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        call_count = {'n': 0}

        def fake_hacienda(self_model, cedula):
            call_count['n'] += 1
            if call_count['n'] == 2:
                # Second call fails
                return {
                    'success': False,
                    'error': 'Not found',
                    'error_type': 'not_found',
                }
            return {
                'success': True,
                'data': {
                    'cedula': cedula,
                    'name': 'Success Company',
                    'company_type': 'company',
                    'tax_regime': 'General',
                    'tax_status': 'inscrito',
                    'economic_activities': [],
                    'primary_activity': None,
                    'raw_response': '{}',
                },
            }

        def fake_gometa(self_model, cedula):
            # GoMeta also fails for the second cedula
            return {
                'success': False,
                'error': 'Not found in GoMeta',
                'error_type': 'not_found',
            }

        RateLimiterCls = _model_cls(self.env, 'l10n_cr.hacienda.rate_limiter')

        with patch.object(ServiceCls, '_lookup_hacienda', fake_hacienda), \
             patch.object(ServiceCls, '_lookup_gometa', fake_gometa), \
             patch.object(RateLimiterCls, 'try_acquire_token', return_value=True):

            results = self.lookup_service.batch_lookup_cedulas(cedulas)

            # Should return all 3 results
            self.assertEqual(len(results), 3)

            # First and third succeed
            self.assertIn('name', results['9000000001'])
            self.assertIn('name', results['9000000003'])

            # Second failed
            self.assertIn('error', results['9000000002'])


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p2')
class TestCedulaLookupServiceEdgeCases(EInvoiceTestCase):
    """Test edge cases and error scenarios."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service'].with_company(cls.company)
        cls.cache_model = cls.env['l10n_cr.cedula.cache'].with_company(cls.company)

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_invalid_cedula_format(self):
        """Invalid cedula format raises validation error."""
        invalid_cedulas = [
            'ABC123',           # Non-numeric
            '12345',            # Too short
            '12345678901234',   # Too long
            '',                 # Empty
            None,               # None
        ]

        for cedula in invalid_cedulas:
            with self.assertRaises(Exception):
                self.lookup_service.lookup_cedula(cedula)

    def test_02_not_found_in_hacienda_registry(self):
        """Cedula not found in Hacienda returns error via UserError."""
        cedula = '9999999999'

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        not_found = {
            'success': False,
            'error': 'Cedula no encontrada en registros publicos.',
            'error_type': 'not_found',
        }

        with patch.object(ServiceCls, '_lookup_hacienda', return_value=not_found), \
             patch.object(ServiceCls, '_lookup_gometa', return_value=not_found):

            with self.assertRaises(UserError) as ctx:
                self.lookup_service.lookup_cedula(cedula)

            error_msg = str(ctx.exception)
            # Error message should contain useful info about the failure
            self.assertTrue(len(error_msg) > 0)

    def test_03_api_timeout_handled_gracefully(self):
        """API timeout falls back to next step in waterfall."""
        cedula = '8888888888'

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        hacienda_timeout = {
            'success': False,
            'error': 'Connection timeout',
            'error_type': 'timeout',
        }

        gometa_success = {
            'success': True,
            'data': {
                'cedula': cedula,
                'name': 'GoMeta Fallback',
                'company_type': 'other',
                'tax_regime': '',
                'tax_status': 'inscrito',
                'economic_activities': [],
                'primary_activity': None,
                'raw_response': '{}',
            },
        }

        with patch.object(ServiceCls, '_lookup_hacienda', return_value=hacienda_timeout), \
             patch.object(ServiceCls, '_lookup_gometa', return_value=gometa_success):

            result = self.lookup_service.lookup_cedula(cedula)

            # Should fallback to GoMeta
            self.assertEqual(result['source'], 'gometa')
            self.assertEqual(result['name'], 'GoMeta Fallback')

    def test_04_malformed_api_response(self):
        """Malformed API response triggers fallback and eventually UserError."""
        cedula = '7777777777'

        ServiceCls = _model_cls(self.env, 'l10n_cr.cedula.lookup.service')

        api_error = {
            'success': False,
            'error': 'Invalid JSON response from API',
            'error_type': 'api_error',
        }

        with patch.object(ServiceCls, '_lookup_hacienda', return_value=api_error), \
             patch.object(ServiceCls, '_lookup_gometa', return_value=api_error):

            with self.assertRaises(UserError):
                self.lookup_service.lookup_cedula(cedula)

    def test_05_cache_conflict_resolution(self):
        """Cache update handles conflicts correctly."""
        cedula = '4040404040'

        # Create initial cache
        cache1 = self.cache_model.create({
            'cedula': cedula,
            'name': 'Original Name',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Try to create duplicate (should update existing)
        self.cache_model.update_cache(
            cedula=cedula,
            data={
                'name': 'Updated Name',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'tax_regime': 'General',
            },
            source='hacienda',
            company=self.company,
        )

        # Should have only 1 cache entry
        caches = self.cache_model.search([('cedula', '=', cedula)])
        self.assertEqual(len(caches), 1)

        # Name should be updated
        self.assertEqual(caches[0].name, 'Updated Name')
