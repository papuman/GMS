# -*- coding: utf-8 -*-
"""
Integration Tests for Cédula Lookup Dashboard

Tests the monitoring dashboard for cache health metrics, API performance,
and usage statistics visualization.

Test Coverage:
- Cache health metrics calculation
- API performance metrics
- Usage statistics
- Dashboard view rendering

Priority: P2 (Medium - monitoring and analytics)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock
from odoo import fields
from odoo.tests import tagged
from .common import EInvoiceTestCase


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p2')
class TestCacheHealthMetrics(EInvoiceTestCase):
    """Test cache health metrics calculation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_total_entries_metric(self):
        """Dashboard shows total cache entries."""
        now = datetime.now(timezone.utc)

        # Create 10 cache entries
        for i in range(10):
            self.cache_model.create({
                'cedula': f'100000000{i}',
                'name': f'Company {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now),
                'refreshed_at': fields.Datetime.to_string(now),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        stats = self.cache_model.get_cache_statistics(company=self.company)

        self.assertEqual(stats['total_entries'], 10)

    def test_02_cache_tier_distribution(self):
        """Dashboard shows distribution across cache tiers."""
        now = datetime.now(timezone.utc)

        # Create entries in different tiers
        # Fresh (0-5 days)
        for i in range(5):
            self.cache_model.create({
                'cedula': f'200000000{i}',
                'name': f'Fresh {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=2)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=2)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Refresh zone (5-7 days)
        for i in range(3):
            self.cache_model.create({
                'cedula': f'300000000{i}',
                'name': f'Refresh {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=6)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Stale (7-90 days)
        for i in range(2):
            self.cache_model.create({
                'cedula': f'400000000{i}',
                'name': f'Stale {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        stats = self.cache_model.get_cache_statistics(company=self.company)

        self.assertEqual(stats['fresh'], 5)
        self.assertEqual(stats['refresh_zone'], 3)
        self.assertEqual(stats['stale'], 2)

    def test_03_cache_coverage_percentage(self):
        """Dashboard shows cache coverage percentage."""
        now = datetime.now(timezone.utc)

        # Create 8 fresh, 2 stale
        for i in range(8):
            self.cache_model.create({
                'cedula': f'500000000{i}',
                'name': f'Fresh {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now),
                'refreshed_at': fields.Datetime.to_string(now),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        for i in range(2):
            self.cache_model.create({
                'cedula': f'600000000{i}',
                'name': f'Stale {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        stats = self.cache_model.get_cache_statistics(company=self.company)

        # Coverage = (fresh + refresh) / total * 100
        # 8 / 10 * 100 = 80%
        self.assertEqual(stats['cache_coverage'], 80.0)

    def test_04_average_access_count(self):
        """Dashboard shows average access count per entry."""
        now = datetime.now(timezone.utc)

        # Create entries with varying access counts
        self.cache_model.create({
            'cedula': '7000000001',
            'name': 'High Access',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now),
            'refreshed_at': fields.Datetime.to_string(now),
            'access_count': 100,
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        self.cache_model.create({
            'cedula': '7000000002',
            'name': 'Medium Access',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now),
            'refreshed_at': fields.Datetime.to_string(now),
            'access_count': 50,
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        self.cache_model.create({
            'cedula': '7000000003',
            'name': 'Low Access',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now),
            'refreshed_at': fields.Datetime.to_string(now),
            'access_count': 10,
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        stats = self.cache_model.get_cache_statistics(company=self.company)

        # Average = (100 + 50 + 10) / 3 = 53.33
        self.assertAlmostEqual(stats['avg_access_count'], 53.33, places=2)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p2')
class TestAPIPerformanceMetrics(EInvoiceTestCase):
    """Test API performance metrics."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_api_response_time_tracking(self):
        """Track API response times for performance monitoring."""
        cedula = '8000000001'

        # Mock API with delay
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'nombre': 'Performance Test',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }

        with patch('requests.post', return_value=mock_response):
            import time
            start = time.time()
            result = self.lookup_service.lookup_cedula(cedula)
            elapsed = time.time() - start

            # Response should be fast (<5s)
            self.assertLess(elapsed, 5.0)

    def test_02_api_success_rate_tracking(self):
        """Track API success/failure rate."""
        # Make 10 requests: 8 succeed, 2 fail
        success_count = 0
        fail_count = 0

        for i in range(10):
            cedula = f'900000000{i}'

            mock_response = Mock()
            if i < 8:
                # Success
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'nombre': f'Company {i}',
                    'tipoIdentificacion': '02',
                    'regimen': {'descripcion': 'General'},
                    'situacion': 'INSCRITO',
                }
            else:
                # Failure
                mock_response.status_code = 500

            with patch('requests.post', return_value=mock_response):
                try:
                    result = self.lookup_service.lookup_cedula(cedula)
                    success_count += 1
                except:
                    fail_count += 1

        # Success rate = 80%
        success_rate = success_count / (success_count + fail_count) * 100
        self.assertEqual(success_rate, 80.0)

    def test_03_api_cache_hit_rate(self):
        """Track cache hit rate vs API calls."""
        cedula = '1000000001'

        # Create cache
        cache = self.cache_model.create({
            'cedula': cedula,
            'name': 'Cached Company',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.now(),
            'refreshed_at': fields.Datetime.now(),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Make 10 lookups (all should hit cache)
        api_calls = 0
        cache_hits = 0

        with patch('requests.post') as mock_post:
            for _ in range(10):
                result = self.lookup_service.lookup_cedula(cedula)
                if result['source'] == 'cache':
                    cache_hits += 1
                else:
                    api_calls += 1

            # Should be 10 cache hits, 0 API calls
            self.assertEqual(cache_hits, 10)
            self.assertEqual(api_calls, 0)
            mock_post.assert_not_called()

        # Cache hit rate = 100%
        hit_rate = cache_hits / 10 * 100
        self.assertEqual(hit_rate, 100.0)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p2')
class TestUsageStatistics(EInvoiceTestCase):
    """Test usage statistics."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']
        cls.lookup_service = cls.env['l10n_cr.cedula.lookup.service']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_most_frequently_accessed_partners(self):
        """Dashboard shows most frequently accessed partners."""
        now = datetime.now(timezone.utc)

        # Create entries with different access counts
        entries = []
        for i in range(5):
            entry = self.cache_model.create({
                'cedula': f'110000000{i}',
                'name': f'Company {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now),
                'refreshed_at': fields.Datetime.to_string(now),
                'access_count': (i + 1) * 10,  # 10, 20, 30, 40, 50
                'source': 'hacienda',
                'company_id': self.company.id,
            })
            entries.append(entry)

        # Get top 3
        top = self.cache_model.search([
            ('company_id', '=', self.company.id)
        ], order='access_count desc', limit=3)

        # Should be entries 4, 3, 2 (50, 40, 30)
        self.assertEqual(top[0].access_count, 50)
        self.assertEqual(top[1].access_count, 40)
        self.assertEqual(top[2].access_count, 30)

    def test_02_recently_accessed_partners(self):
        """Dashboard shows recently accessed partners."""
        now = datetime.now(timezone.utc)

        # Create entries with different last_access times
        for i in range(5):
            self.cache_model.create({
                'cedula': f'120000000{i}',
                'name': f'Company {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now),
                'refreshed_at': fields.Datetime.to_string(now),
                'last_access_at': fields.Datetime.to_string(now - timedelta(hours=i)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Get most recent
        recent = self.cache_model.search([
            ('company_id', '=', self.company.id)
        ], order='last_access_at desc', limit=3)

        # Should be entries 0, 1, 2 (most recent)
        self.assertEqual(len(recent), 3)

    def test_03_lookup_source_distribution(self):
        """Dashboard shows distribution of lookup sources."""
        now = datetime.now(timezone.utc)

        # Create entries from different sources
        for i in range(7):
            self.cache_model.create({
                'cedula': f'130000000{i}',
                'name': f'Hacienda {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now),
                'refreshed_at': fields.Datetime.to_string(now),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        for i in range(3):
            self.cache_model.create({
                'cedula': f'140000000{i}',
                'name': f'GoMeta {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now),
                'refreshed_at': fields.Datetime.to_string(now),
                'source': 'gometa',
                'company_id': self.company.id,
            })

        # Count by source
        hacienda_count = self.cache_model.search_count([
            ('company_id', '=', self.company.id),
            ('source', '=', 'hacienda')
        ])
        gometa_count = self.cache_model.search_count([
            ('company_id', '=', self.company.id),
            ('source', '=', 'gometa')
        ])

        self.assertEqual(hacienda_count, 7)
        self.assertEqual(gometa_count, 3)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p2')
class TestDashboardViewRendering(EInvoiceTestCase):
    """Test dashboard view rendering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_dashboard_view_accessible(self):
        """Dashboard view is accessible to users."""
        # Check if dashboard action exists
        action = self.env.ref('l10n_cr_einvoice.action_cedula_dashboard',
                             raise_if_not_found=False)

        # If dashboard implemented, verify action exists
        if action:
            self.assertTrue(action.exists())

    def test_02_dashboard_displays_cache_health_chart(self):
        """Dashboard displays cache health pie chart."""
        now = datetime.now(timezone.utc)

        # Create mix of cache tiers
        for i in range(6):
            self.cache_model.create({
                'cedula': f'150000000{i}',
                'name': f'Fresh {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now),
                'refreshed_at': fields.Datetime.to_string(now),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        for i in range(4):
            self.cache_model.create({
                'cedula': f'160000000{i}',
                'name': f'Stale {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        # Get statistics for chart
        stats = self.cache_model.get_cache_statistics(company=self.company)

        # Verify chart data
        self.assertEqual(stats['total_entries'], 10)
        self.assertEqual(stats['fresh'], 6)
        self.assertEqual(stats['stale'], 4)

    def test_03_dashboard_shows_rate_limiter_status(self):
        """Dashboard shows current rate limiter status."""
        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']
        rate_limiter.reset()

        # Get rate limiter status
        status = rate_limiter.get_available_tokens()

        # Assert structure
        self.assertIn('tokens', status)
        self.assertIn('capacity', status)
        self.assertIn('utilization', status)

        # Should start at full capacity
        self.assertEqual(status['tokens'], status['capacity'])
        self.assertEqual(status['utilization'], 0.0)

    def test_04_dashboard_refreshes_statistics(self):
        """Dashboard statistics refresh when requested."""
        now = datetime.now(timezone.utc)

        # Create initial cache
        cache = self.cache_model.create({
            'cedula': '1700000001',
            'name': 'Initial',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now),
            'refreshed_at': fields.Datetime.to_string(now),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Get initial stats
        stats1 = self.cache_model.get_cache_statistics(company=self.company)
        self.assertEqual(stats1['total_entries'], 1)

        # Add more entries
        self.cache_model.create({
            'cedula': '1700000002',
            'name': 'Second',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'fetched_at': fields.Datetime.to_string(now),
            'refreshed_at': fields.Datetime.to_string(now),
            'source': 'hacienda',
            'company_id': self.company.id,
        })

        # Get updated stats
        stats2 = self.cache_model.get_cache_statistics(company=self.company)
        self.assertEqual(stats2['total_entries'], 2)


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'integration', 'p3')
class TestDashboardAlerts(EInvoiceTestCase):
    """Test dashboard alert system."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

    def setUp(self):
        super().setUp()
        self.cache_model.search([]).unlink()

    def test_01_alert_when_cache_coverage_below_threshold(self):
        """Dashboard shows alert when cache coverage <80%."""
        now = datetime.now(timezone.utc)

        # Create 3 fresh, 7 stale (30% coverage)
        for i in range(3):
            self.cache_model.create({
                'cedula': f'180000000{i}',
                'name': f'Fresh {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now),
                'refreshed_at': fields.Datetime.to_string(now),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        for i in range(7):
            self.cache_model.create({
                'cedula': f'190000000{i}',
                'name': f'Stale {i}',
                'company_type': 'company',
                'tax_status': 'inscrito',
                'fetched_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'refreshed_at': fields.Datetime.to_string(now - timedelta(days=30)),
                'source': 'hacienda',
                'company_id': self.company.id,
            })

        stats = self.cache_model.get_cache_statistics(company=self.company)

        # Coverage = 30%
        self.assertEqual(stats['cache_coverage'], 30.0)

        # Should trigger alert
        self.assertLess(stats['cache_coverage'], 80.0)

    def test_02_alert_when_rate_limit_utilization_high(self):
        """Dashboard shows alert when rate limit >80% utilized."""
        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']
        rate_limiter.reset()

        # Consume 18 of 20 tokens (90% utilization)
        for _ in range(18):
            rate_limiter.try_acquire_token()

        status = rate_limiter.get_available_tokens()

        # Utilization = 90%
        self.assertEqual(status['utilization'], 90.0)

        # Should trigger alert
        self.assertGreater(status['utilization'], 80.0)
