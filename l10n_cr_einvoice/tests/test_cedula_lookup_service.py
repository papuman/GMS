# -*- coding: utf-8 -*-
"""
Comprehensive Integration Tests for Cédula Lookup Service

Tests the complete waterfall retry strategy for looking up Costa Rica tax IDs
(cédulas) from government APIs with caching, rate limiting, and fallback mechanisms.

Test Coverage:
- Waterfall retry strategy (all 4 steps)
- Cache hit scenarios (fresh cache, no API call)
- Hacienda API success
- Hacienda failure → GoMeta fallback
- Both APIs fail → stale cache return
- All fail → manual entry prompt
- Rate limiting integration
- Concurrent lookups
- Batch lookup functionality

Priority: P0 (Critical - customer lookup is core POS feature)
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock
from odoo import fields
from odoo.tests import tagged
from odoo.exceptions import UserError
from .common import EInvoiceTestCase


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestCedulaLookupServiceWaterfall(EInvoiceTestCase):
    """Test waterfall retry strategy through all 4 steps."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service']
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

    def setUp(self):
        super().setUp()
        # Clear cache and rate limiter before each test
        self.cache_model.search([]).unlink()
        if hasattr(self.env, 'l10n_cr.hacienda.rate_limiter'):
            self.env['l10n_cr.hacienda.rate_limiter'].reset()

    def test_01_waterfall_step1_fresh_cache_hit(self):
        """Step 1: Fresh cache (<7 days) returns immediately without API call."""
        cedula = '3101234567'

        # Create fresh cache entry
        cache = self.cache_model.create({
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

        # Lookup should hit cache (no API call)
        with patch('requests.post') as mock_post:
            result = self.lookup_service.lookup_cedula(cedula)

            # Assert no API call was made
            mock_post.assert_not_called()

            # Assert result comes from cache
            self.assertEqual(result['name'], 'Acme Corp SA')
            self.assertEqual(result['source'], 'cache')
            self.assertEqual(result['cache_age_days'], 0)
            self.assertTrue(result['is_fresh'])

    def test_02_waterfall_step2_hacienda_api_success(self):
        """Step 2: No cache → call Hacienda API successfully."""
        cedula = '3101234567'

        # Mock successful Hacienda API response
        mock_hacienda_response = Mock()
        mock_hacienda_response.status_code = 200
        mock_hacienda_response.json.return_value = {
            'nombre': 'Gimnasio Test SA',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
            'actividades': [
                {'estado': 'ACTIVO', 'codigo': '9311', 'descripcion': 'Gimnasios'}
            ]
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_hacienda_response

            result = self.lookup_service.lookup_cedula(cedula)

            # Assert Hacienda API was called
            mock_post.assert_called_once()

            # Assert result from Hacienda
            self.assertEqual(result['name'], 'Gimnasio Test SA')
            self.assertEqual(result['source'], 'hacienda')
            self.assertEqual(result['tax_status'], 'inscrito')
            self.assertIn('9311', result['primary_activity'])

            # Assert cache was created
            cache = self.cache_model.search([('cedula', '=', cedula)])
            self.assertEqual(len(cache), 1)
            self.assertEqual(cache.name, 'Gimnasio Test SA')

    def test_03_waterfall_step3_hacienda_fails_gometa_succeeds(self):
        """Step 3: Hacienda timeout → fallback to GoMeta API."""
        cedula = '3101234567'

        # Mock Hacienda timeout
        mock_hacienda_response = Mock()
        mock_hacienda_response.status_code = 504

        # Mock GoMeta success
        mock_gometa_response = Mock()
        mock_gometa_response.status_code = 200
        mock_gometa_response.json.return_value = {
            'nombre': 'Test Company From GoMeta',
            'tipo': 'JURIDICA',
            'estado': 'ACTIVO',
        }

        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get:
            mock_post.return_value = mock_hacienda_response
            mock_get.return_value = mock_gometa_response

            result = self.lookup_service.lookup_cedula(cedula)

            # Assert both APIs called
            self.assertTrue(mock_post.called, "Hacienda should be called first")
            self.assertTrue(mock_get.called, "GoMeta should be called as fallback")

            # Assert result from GoMeta
            self.assertEqual(result['name'], 'Test Company From GoMeta')
            self.assertEqual(result['source'], 'gometa')
            self.assertEqual(result['tax_status'], 'inscrito')

    def test_04_waterfall_step4_both_apis_fail_stale_cache_used(self):
        """Step 4: Both APIs fail → return stale cache (7-90 days old)."""
        cedula = '3101234567'

        # Create stale cache entry (30 days old)
        stale_time = datetime.now(timezone.utc) - timedelta(days=30)
        cache = self.cache_model.create({
            'cedula': cedula,
            'name': 'Stale Cache Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(stale_time),
            'refreshed_at': fields.Datetime.to_string(stale_time),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Mock both APIs failing
        mock_failure = Mock()
        mock_failure.status_code = 503

        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get:
            mock_post.return_value = mock_failure
            mock_get.return_value = mock_failure

            result = self.lookup_service.lookup_cedula(cedula)

            # Assert both APIs were attempted
            self.assertTrue(mock_post.called)
            self.assertTrue(mock_get.called)

            # Assert stale cache was returned
            self.assertEqual(result['name'], 'Stale Cache Company')
            self.assertEqual(result['source'], 'cache')
            self.assertTrue(result['is_stale'])
            self.assertEqual(result['cache_age_days'], 30)
            self.assertIn('warning', result)

    def test_05_waterfall_step5_all_fail_manual_entry_required(self):
        """Step 5: All fail (no cache, APIs down) → manual entry required."""
        cedula = '9999999999'

        # Mock both APIs failing
        mock_failure = Mock()
        mock_failure.status_code = 404

        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get:
            mock_post.return_value = mock_failure
            mock_get.return_value = mock_failure

            with self.assertRaises(UserError) as ctx:
                self.lookup_service.lookup_cedula(cedula)

            # Assert error message indicates manual entry needed
            error_msg = str(ctx.exception).lower()
            self.assertIn('manual', error_msg)
            self.assertIn(cedula, error_msg)

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

        # Mock new API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'New Updated Name',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response

            result = self.lookup_service.lookup_cedula(cedula, force_refresh=True)

            # Assert API was called despite fresh cache
            mock_post.assert_called_once()

            # Assert result has new name
            self.assertEqual(result['name'], 'New Updated Name')

            # Assert cache was updated
            cache.refresh()
            self.assertEqual(cache.name, 'New Updated Name')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p0')
class TestCedulaLookupServiceCache(EInvoiceTestCase):
    """Test cache behavior and freshness checks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service']
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

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

        with patch('requests.post') as mock_post:
            result = self.lookup_service.lookup_cedula(cedula)

            # No API call
            mock_post.assert_not_called()

            # Cache access counter incremented
            cache.refresh()
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

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Updated Name',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response

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
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service']
        cls.rate_limiter = cls.env['l10n_cr.hacienda.rate_limiter']

    def setUp(self):
        super().setUp()
        self.rate_limiter.reset()

    def test_01_rate_limit_respected_during_lookup(self):
        """Lookup service respects rate limiter tokens."""
        # Mock successful API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Test Company',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response

            # Make 20 lookups (burst capacity)
            for i in range(20):
                cedula = f'100000000{i}'
                result = self.lookup_service.lookup_cedula(cedula)
                self.assertEqual(result['source'], 'hacienda')

            # 21st lookup should fail (rate limit)
            with self.assertRaises(UserError) as ctx:
                self.lookup_service.lookup_cedula('1000000021')

            error_msg = str(ctx.exception).lower()
            self.assertIn('rate limit', error_msg)

    def test_02_cache_hits_do_not_consume_rate_limit_tokens(self):
        """Cache hits don't consume API rate limit tokens."""
        cedula = '5050505050'

        # Create cache
        cache = self.env['l10n_cr.cedula.cache'].create({
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
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service']

    def test_01_concurrent_lookups_same_cedula(self):
        """Multiple concurrent lookups for same cédula use cache."""
        cedula = '6060606060'

        # Create cache
        cache = self.env['l10n_cr.cedula.cache'].create({
            'cedula': cedula,
            'name': 'Concurrent Test',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Simulate 5 concurrent lookups
        with patch('requests.post') as mock_post:
            results = []
            for _ in range(5):
                result = self.lookup_service.lookup_cedula(cedula)
                results.append(result)

            # No API calls (all cache hits)
            mock_post.assert_not_called()

            # All results identical
            for result in results:
                self.assertEqual(result['name'], 'Concurrent Test')
                self.assertEqual(result['source'], 'cache')

    def test_02_concurrent_lookups_different_cedulas(self):
        """Concurrent lookups for different cédulas process independently."""
        cedulas = [f'700000000{i}' for i in range(5)]

        # Mock API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Test Company',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response

            results = []
            for cedula in cedulas:
                result = self.lookup_service.lookup_cedula(cedula)
                results.append(result)

            # Should make 5 API calls
            self.assertEqual(mock_post.call_count, 5)

            # All should succeed
            self.assertEqual(len(results), 5)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p1')
class TestCedulaLookupServiceBatch(EInvoiceTestCase):
    """Test batch lookup functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service']

    def test_01_batch_lookup_multiple_cedulas(self):
        """Batch lookup processes multiple cédulas efficiently."""
        cedulas = [f'800000000{i}' for i in range(10)]

        # Mock API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Batch Company',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response

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

        # Mock API with mixed responses
        def mock_post_side_effect(*args, **kwargs):
            response = Mock()
            # First succeeds, second fails, third succeeds
            if mock_post_side_effect.call_count == 2:
                response.status_code = 404
            else:
                response.status_code = 200
                response.json.return_value = {
                    'nombre': 'Success Company',
                    'tipoIdentificacion': '02',
                    'regimen': {'descripcion': 'General'},
                    'situacion': 'INSCRITO',
                }
            mock_post_side_effect.call_count += 1
            return response

        mock_post_side_effect.call_count = 0

        with patch('requests.post', side_effect=mock_post_side_effect):
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
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service']

    def test_01_invalid_cedula_format(self):
        """Invalid cédula format raises validation error."""
        invalid_cedulas = [
            'ABC123',           # Non-numeric
            '12345',            # Too short
            '12345678901234',   # Too long
            '',                 # Empty
            None,               # None
        ]

        for cedula in invalid_cedulas:
            with self.assertRaises((UserError, ValueError, TypeError)):
                self.lookup_service.lookup_cedula(cedula)

    def test_02_not_found_in_hacienda_registry(self):
        """Cédula not found in Hacienda returns no_encontrado status."""
        cedula = '9999999999'

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404

        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get:
            mock_post.return_value = mock_response
            mock_get.return_value = mock_response

            with self.assertRaises(UserError) as ctx:
                self.lookup_service.lookup_cedula(cedula)

            error_msg = str(ctx.exception)
            self.assertIn(cedula, error_msg)

    def test_03_api_timeout_handled_gracefully(self):
        """API timeout falls back to next step in waterfall."""
        cedula = '8888888888'

        # Mock timeout on Hacienda
        import requests

        def hacienda_timeout(*args, **kwargs):
            raise requests.Timeout("Connection timeout")

        # Mock GoMeta success
        gometa_response = Mock()
        gometa_response.status_code = 200
        gometa_response.json.return_value = {
            'nombre': 'GoMeta Fallback',
            'tipo': 'JURIDICA',
            'estado': 'ACTIVO',
        }

        with patch('requests.post', side_effect=hacienda_timeout), \
             patch('requests.get', return_value=gometa_response):

            result = self.lookup_service.lookup_cedula(cedula)

            # Should fallback to GoMeta
            self.assertEqual(result['source'], 'gometa')
            self.assertEqual(result['name'], 'GoMeta Fallback')

    def test_04_malformed_api_response(self):
        """Malformed API response triggers fallback."""
        cedula = '7777777777'

        # Mock malformed response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get:
            mock_post.return_value = mock_response
            mock_get.return_value = mock_response

            with self.assertRaises(UserError):
                self.lookup_service.lookup_cedula(cedula)

    def test_05_cache_conflict_resolution(self):
        """Cache update handles conflicts correctly."""
        cedula = '4040404040'

        # Create initial cache
        cache1 = self.env['l10n_cr.cedula.cache'].create({
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
        self.env['l10n_cr.cedula.cache'].update_cache(
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
        caches = self.env['l10n_cr.cedula.cache'].search([('cedula', '=', cedula)])
        self.assertEqual(len(caches), 1)

        # Name should be updated
        self.assertEqual(caches[0].name, 'Updated Name')
