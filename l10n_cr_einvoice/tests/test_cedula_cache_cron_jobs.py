# -*- coding: utf-8 -*-
"""
Test Suite: Cédula Cache Cron Jobs

Tests the automated cache maintenance system:
- Refresh stale cache entries (every 6 hours)
- Purge expired cache entries (daily at 2 AM)
- Priority refresh for high-access entries (daily at 3 AM)

Test coverage:
- Cron job execution
- Rate limiting and batch processing
- Statistics tracking and logging
- Error handling and notifications
- System parameter configuration
"""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestCedulaCacheCronJobs(TransactionCase):
    """Test automated cron jobs for cache maintenance."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test company
        cls.company = cls.env['res.company'].create({
            'name': 'Test Company CR',
            'country_id': cls.env.ref('base.cr').id,
        })

        # Create cache model
        cls.cache_model = cls.env['l10n_cr.cedula.cache']

        # System parameters
        cls.params = cls.env['ir.config_parameter'].sudo()

    def setUp(self):
        super().setUp()
        # Clean cache before each test
        self.cache_model.search([]).unlink()

    def _create_cache_entry(self, cedula, age_days=0, access_count=0, company=None):
        """Helper: Create cache entry with specific age and access count."""
        company = company or self.company
        refresh_date = datetime.now() - timedelta(days=age_days)

        return self.cache_model.create({
            'cedula': cedula,
            'name': f'Company {cedula}',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'company_id': company.id,
            'fetched_at': refresh_date,
            'refreshed_at': refresh_date,
            'access_count': access_count,
        })

    # ==========================================================================
    # TEST: Refresh Stale Cache Cron Job
    # ==========================================================================

    def test_cron_refresh_stale_cache_success(self):
        """Test successful refresh of stale cache entries."""
        # Create stale cache entries (5-7 days old)
        cache1 = self._create_cache_entry('3101234567', age_days=5, access_count=20)
        cache2 = self._create_cache_entry('3101234568', age_days=6, access_count=15)
        cache3 = self._create_cache_entry('3101234569', age_days=7, access_count=10)

        # Create fresh entry (should be ignored)
        cache_fresh = self._create_cache_entry('3101234570', age_days=2, access_count=5)

        # Mock Hacienda API responses
        mock_api_response = {
            'success': True,
            'name': 'Updated Company Name',
            'tax_regime': 'Régimen General',
            'economic_activities': [
                {'code': '931100', 'description': 'Gimnasios', 'primary': True}
            ],
            'raw_data': {'nombre': 'Updated Company Name'},
        }

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            return_value=mock_api_response
        ) as mock_lookup:
            # Run cron job
            result = self.cache_model._cron_refresh_stale_cache()

            # Verify statistics
            self.assertTrue(result['success'])
            self.assertEqual(result['processed'], 3, "Should process 3 stale entries")
            self.assertEqual(result['refreshed'], 3, "All 3 should succeed")
            self.assertEqual(result['failed'], 0, "No failures expected")

            # Verify API was called 3 times (not for fresh entry)
            self.assertEqual(mock_lookup.call_count, 3)

            # Verify cache entries were updated
            cache1.invalidate_recordset()
            cache2.invalidate_recordset()
            cache3.invalidate_recordset()

            self.assertEqual(cache1.name, 'Updated Company Name')
            self.assertEqual(cache2.name, 'Updated Company Name')
            self.assertEqual(cache3.name, 'Updated Company Name')

            # Verify fresh entry was NOT updated
            cache_fresh.invalidate_recordset()
            self.assertNotEqual(cache_fresh.name, 'Updated Company Name')

    def test_cron_refresh_stale_cache_prioritizes_high_access(self):
        """Test that cron prioritizes high-access-count entries."""
        # Create stale entries with varying access counts
        cache_high = self._create_cache_entry('3101234567', age_days=6, access_count=100)
        cache_mid = self._create_cache_entry('3101234568', age_days=6, access_count=50)
        cache_low = self._create_cache_entry('3101234569', age_days=6, access_count=10)

        # Set small batch size to test ordering
        self.params.set_param('l10n_cr_einvoice.cache_refresh_batch_size', '2')

        mock_api_response = {
            'success': True,
            'name': 'Test Company',
            'tax_regime': 'General',
            'economic_activities': [],
            'raw_data': {},
        }

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            return_value=mock_api_response
        ) as mock_lookup:
            # Run cron job
            result = self.cache_model._cron_refresh_stale_cache()

            # Verify only 2 entries processed (batch size limit)
            self.assertEqual(result['processed'], 2)

            # Verify high and mid access entries were processed (not low)
            call_cedulas = [call[1]['cedula'] for call in mock_lookup.call_args_list]
            self.assertIn('3101234567', call_cedulas, "High-access entry should be processed")
            self.assertIn('3101234568', call_cedulas, "Mid-access entry should be processed")
            self.assertNotIn('3101234569', call_cedulas, "Low-access entry should be skipped")

    def test_cron_refresh_stale_cache_handles_api_failures(self):
        """Test cron handles API failures gracefully."""
        # Create stale cache entries
        cache1 = self._create_cache_entry('3101234567', age_days=6, access_count=10)
        cache2 = self._create_cache_entry('3101234568', age_days=6, access_count=5)

        # Mock API with mixed success/failure
        def mock_lookup_side_effect(cedula):
            if cedula == '3101234567':
                return {'success': True, 'name': 'Success Company', 'economic_activities': [], 'raw_data': {}}
            else:
                return {'success': False, 'error': 'API rate limit exceeded', 'error_type': 'rate_limit'}

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            side_effect=mock_lookup_side_effect
        ):
            # Run cron job
            result = self.cache_model._cron_refresh_stale_cache()

            # Verify statistics
            self.assertTrue(result['success'])
            self.assertEqual(result['processed'], 2)
            self.assertEqual(result['refreshed'], 1)
            self.assertEqual(result['failed'], 1)

            # Verify error was stored
            cache2.invalidate_recordset()
            self.assertIn('rate limit', cache2.error_message.lower())

    def test_cron_refresh_stale_cache_no_entries(self):
        """Test cron handles empty cache gracefully."""
        # No cache entries created

        result = self.cache_model._cron_refresh_stale_cache()

        # Verify graceful exit
        self.assertTrue(result['success'])
        self.assertEqual(result['processed'], 0)
        self.assertEqual(result['refreshed'], 0)
        self.assertEqual(result['failed'], 0)

    def test_cron_refresh_respects_batch_size_parameter(self):
        """Test that batch size system parameter is respected."""
        # Create 10 stale entries
        for i in range(10):
            self._create_cache_entry(f'310123456{i}', age_days=6, access_count=i)

        # Set batch size to 5
        self.params.set_param('l10n_cr_einvoice.cache_refresh_batch_size', '5')

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            return_value={'success': True, 'name': 'Test', 'economic_activities': [], 'raw_data': {}}
        ) as mock_lookup:
            result = self.cache_model._cron_refresh_stale_cache()

            # Verify only 5 entries processed
            self.assertEqual(result['processed'], 5)
            self.assertEqual(mock_lookup.call_count, 5)

    # ==========================================================================
    # TEST: Purge Expired Cache Cron Job
    # ==========================================================================

    def test_cron_purge_expired_cache_success(self):
        """Test successful purge of expired cache entries."""
        # Create expired entries (>90 days old)
        cache1 = self._create_cache_entry('3101234567', age_days=91)
        cache2 = self._create_cache_entry('3101234568', age_days=100)
        cache3 = self._create_cache_entry('3101234569', age_days=365)

        # Create stale but not expired (should be kept)
        cache_stale = self._create_cache_entry('3101234570', age_days=45)

        # Run cron job
        result = self.cache_model._cron_purge_expired_cache()

        # Verify statistics
        self.assertTrue(result['success'])
        self.assertEqual(result['purged'], 3)

        # Verify expired entries deleted
        self.assertFalse(cache1.exists())
        self.assertFalse(cache2.exists())
        self.assertFalse(cache3.exists())

        # Verify stale entry preserved
        self.assertTrue(cache_stale.exists())

    def test_cron_purge_expired_respects_max_age_parameter(self):
        """Test that max age system parameter is respected."""
        # Create entries at 30 days old
        cache1 = self._create_cache_entry('3101234567', age_days=30)
        cache2 = self._create_cache_entry('3101234568', age_days=45)

        # Set max age to 35 days (so cache2 is expired, cache1 is not)
        self.params.set_param('l10n_cr_einvoice.cache_max_age_days', '35')

        result = self.cache_model._cron_purge_expired_cache()

        # Verify only cache2 purged
        self.assertEqual(result['purged'], 1)
        self.assertTrue(cache1.exists())
        self.assertFalse(cache2.exists())

    def test_cron_purge_expired_multi_company(self):
        """Test purge across multiple companies."""
        # Create second company
        company2 = self.env['res.company'].create({
            'name': 'Test Company 2',
            'country_id': self.env.ref('base.cr').id,
        })

        # Create expired entries for both companies
        cache1 = self._create_cache_entry('3101234567', age_days=100, company=self.company)
        cache2 = self._create_cache_entry('3101234568', age_days=100, company=company2)

        result = self.cache_model._cron_purge_expired_cache()

        # Verify both companies' expired entries purged
        self.assertEqual(result['purged'], 2)
        self.assertIn(self.company.name, result['by_company'])
        self.assertIn(company2.name, result['by_company'])

    def test_cron_purge_expired_no_entries(self):
        """Test purge handles empty cache gracefully."""
        # No expired entries

        result = self.cache_model._cron_purge_expired_cache()

        self.assertTrue(result['success'])
        self.assertEqual(result['purged'], 0)

    # ==========================================================================
    # TEST: Priority Refresh Cron Job
    # ==========================================================================

    def test_cron_priority_refresh_high_traffic_entries(self):
        """Test priority refresh of high-access-count entries."""
        # Create high-traffic entries (access_count > 10)
        cache_high1 = self._create_cache_entry('3101234567', age_days=2, access_count=50)
        cache_high2 = self._create_cache_entry('3101234568', age_days=1, access_count=20)

        # Create low-traffic entry (should be ignored)
        cache_low = self._create_cache_entry('3101234569', age_days=6, access_count=5)

        mock_api_response = {
            'success': True,
            'name': 'Priority Refreshed',
            'tax_regime': 'General',
            'economic_activities': [],
            'raw_data': {},
        }

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            return_value=mock_api_response
        ) as mock_lookup:
            result = self.cache_model._cron_priority_refresh()

            # Verify only high-traffic entries processed
            self.assertEqual(result['processed'], 2)
            self.assertEqual(result['refreshed'], 2)

            # Verify API called for high-traffic entries
            call_cedulas = [call[1]['cedula'] for call in mock_lookup.call_args_list]
            self.assertIn('3101234567', call_cedulas)
            self.assertIn('3101234568', call_cedulas)
            self.assertNotIn('3101234569', call_cedulas)

    def test_cron_priority_refresh_respects_threshold_parameter(self):
        """Test that priority threshold parameter is respected."""
        # Create entries with varying access counts
        cache1 = self._create_cache_entry('3101234567', age_days=1, access_count=25)
        cache2 = self._create_cache_entry('3101234568', age_days=1, access_count=15)
        cache3 = self._create_cache_entry('3101234569', age_days=1, access_count=5)

        # Set threshold to 20 (only cache1 qualifies)
        self.params.set_param('l10n_cr_einvoice.cache_priority_threshold', '20')

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            return_value={'success': True, 'name': 'Test', 'economic_activities': [], 'raw_data': {}}
        ) as mock_lookup:
            result = self.cache_model._cron_priority_refresh()

            # Verify only cache1 processed
            self.assertEqual(result['processed'], 1)
            call_cedulas = [call[1]['cedula'] for call in mock_lookup.call_args_list]
            self.assertIn('3101234567', call_cedulas)
            self.assertNotIn('3101234568', call_cedulas)
            self.assertNotIn('3101234569', call_cedulas)

    def test_cron_priority_refresh_even_when_fresh(self):
        """Test priority refresh runs even for fresh cache entries."""
        # Create FRESH high-traffic entry (age=1 day, access_count=100)
        cache_fresh = self._create_cache_entry('3101234567', age_days=1, access_count=100)

        self.assertTrue(cache_fresh.is_fresh(), "Entry should be fresh")

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            return_value={'success': True, 'name': 'Refreshed Fresh', 'economic_activities': [], 'raw_data': {}}
        ) as mock_lookup:
            result = self.cache_model._cron_priority_refresh()

            # Verify fresh entry was refreshed anyway
            self.assertEqual(result['processed'], 1)
            self.assertEqual(result['refreshed'], 1)
            self.assertEqual(mock_lookup.call_count, 1)

    def test_cron_priority_refresh_orders_by_access_count(self):
        """Test priority refresh processes highest access count first."""
        # Create high-traffic entries with varying counts
        cache_highest = self._create_cache_entry('3101234567', age_days=3, access_count=1000)
        cache_high = self._create_cache_entry('3101234568', age_days=3, access_count=500)
        cache_medium = self._create_cache_entry('3101234569', age_days=3, access_count=100)

        # Set batch size to 2
        self.params.set_param('l10n_cr_einvoice.cache_refresh_batch_size', '2')

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            return_value={'success': True, 'name': 'Test', 'economic_activities': [], 'raw_data': {}}
        ) as mock_lookup:
            result = self.cache_model._cron_priority_refresh()

            # Verify only 2 highest processed
            self.assertEqual(result['processed'], 2)

            call_cedulas = [call[1]['cedula'] for call in mock_lookup.call_args_list]
            self.assertIn('3101234567', call_cedulas, "Highest should be processed")
            self.assertIn('3101234568', call_cedulas, "High should be processed")
            self.assertNotIn('3101234569', call_cedulas, "Medium should be skipped")

    def test_cron_priority_refresh_no_entries(self):
        """Test priority refresh handles no qualifying entries."""
        # Create only low-traffic entries
        self._create_cache_entry('3101234567', age_days=3, access_count=5)

        result = self.cache_model._cron_priority_refresh()

        self.assertTrue(result['success'])
        self.assertEqual(result['processed'], 0)

    # ==========================================================================
    # TEST: Rate Limiting
    # ==========================================================================

    def test_cron_refresh_rate_limiting(self):
        """Test that rate limiting delays are applied between requests."""
        # Create 3 stale entries
        for i in range(3):
            self._create_cache_entry(f'310123456{i}', age_days=6, access_count=10)

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            return_value={'success': True, 'name': 'Test', 'economic_activities': [], 'raw_data': {}}
        ):
            import time
            with patch('time.sleep') as mock_sleep:
                result = self.cache_model._cron_refresh_stale_cache()

                # Verify sleep was called between requests (not after last)
                self.assertEqual(mock_sleep.call_count, 2, "Should sleep between 3 requests (2 times)")

                # Verify 0.1 second delay (10 req/sec)
                for call in mock_sleep.call_args_list:
                    self.assertAlmostEqual(call[0][0], 0.1, places=1)

    # ==========================================================================
    # TEST: Error Handling and Notifications
    # ==========================================================================

    def test_cron_sends_notification_on_high_failure_rate(self):
        """Test that notification is sent when failure rate > 50%."""
        # Create 4 stale entries
        for i in range(4):
            self._create_cache_entry(f'310123456{i}', age_days=6, access_count=10)

        # Mock API with 75% failure rate (3 fails, 1 success)
        call_count = [0]
        def mock_lookup_side_effect(cedula):
            call_count[0] += 1
            if call_count[0] == 1:
                return {'success': True, 'name': 'Success', 'economic_activities': [], 'raw_data': {}}
            else:
                return {'success': False, 'error': 'API Error', 'error_type': 'api_error'}

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            side_effect=mock_lookup_side_effect
        ):
            with patch.object(
                self.cache_model,
                '_send_cron_failure_notification'
            ) as mock_notify:
                result = self.cache_model._cron_refresh_stale_cache()

                # Verify notification was sent
                self.assertEqual(result['failed'], 3)
                self.assertEqual(result['refreshed'], 1)
                mock_notify.assert_called_once()

    def test_cron_no_notification_on_low_failure_rate(self):
        """Test that no notification sent when failure rate < 50%."""
        # Create 4 stale entries
        for i in range(4):
            self._create_cache_entry(f'310123456{i}', age_days=6, access_count=10)

        # Mock API with 25% failure rate (1 fail, 3 success)
        call_count = [0]
        def mock_lookup_side_effect(cedula):
            call_count[0] += 1
            if call_count[0] <= 3:
                return {'success': True, 'name': 'Success', 'economic_activities': [], 'raw_data': {}}
            else:
                return {'success': False, 'error': 'API Error', 'error_type': 'api_error'}

        with patch.object(
            self.env['l10n_cr.hacienda.cedula.api'],
            'lookup_cedula',
            side_effect=mock_lookup_side_effect
        ):
            with patch.object(
                self.cache_model,
                '_send_cron_failure_notification'
            ) as mock_notify:
                result = self.cache_model._cron_refresh_stale_cache()

                # Verify no notification sent
                self.assertEqual(result['failed'], 1)
                self.assertEqual(result['refreshed'], 3)
                mock_notify.assert_not_called()

    # ==========================================================================
    # TEST: System Parameter Configuration
    # ==========================================================================

    def test_system_parameters_default_values(self):
        """Test system parameters have correct default values."""
        # Get parameters (use defaults if not set)
        batch_size = int(self.params.get_param(
            'l10n_cr_einvoice.cache_refresh_batch_size', 100
        ))
        priority_threshold = int(self.params.get_param(
            'l10n_cr_einvoice.cache_priority_threshold', 10
        ))
        max_age_days = int(self.params.get_param(
            'l10n_cr_einvoice.cache_max_age_days', 90
        ))

        # Verify defaults
        self.assertEqual(batch_size, 100)
        self.assertEqual(priority_threshold, 10)
        self.assertEqual(max_age_days, 90)

    def test_system_parameters_can_be_modified(self):
        """Test that system parameters can be changed."""
        # Modify parameters
        self.params.set_param('l10n_cr_einvoice.cache_refresh_batch_size', '50')
        self.params.set_param('l10n_cr_einvoice.cache_priority_threshold', '20')
        self.params.set_param('l10n_cr_einvoice.cache_max_age_days', '60')

        # Verify parameters changed
        self.assertEqual(
            int(self.params.get_param('l10n_cr_einvoice.cache_refresh_batch_size')),
            50
        )
        self.assertEqual(
            int(self.params.get_param('l10n_cr_einvoice.cache_priority_threshold')),
            20
        )
        self.assertEqual(
            int(self.params.get_param('l10n_cr_einvoice.cache_max_age_days')),
            60
        )

    # ==========================================================================
    # TEST: Cron Job Data Records
    # ==========================================================================

    def test_cron_jobs_exist_in_database(self):
        """Test that cron job records are created by data file."""
        # Search for cron jobs
        cron_refresh = self.env.ref(
            'l10n_cr_einvoice.ir_cron_cedula_cache_refresh_stale',
            raise_if_not_found=False
        )
        cron_purge = self.env.ref(
            'l10n_cr_einvoice.ir_cron_cedula_cache_purge_expired',
            raise_if_not_found=False
        )
        cron_priority = self.env.ref(
            'l10n_cr_einvoice.ir_cron_cedula_cache_priority_refresh',
            raise_if_not_found=False
        )

        # Verify cron jobs exist
        self.assertTrue(cron_refresh, "Refresh stale cache cron should exist")
        self.assertTrue(cron_purge, "Purge expired cache cron should exist")
        self.assertTrue(cron_priority, "Priority refresh cron should exist")

        # Verify configurations
        if cron_refresh:
            self.assertEqual(cron_refresh.interval_number, 6)
            self.assertEqual(cron_refresh.interval_type, 'hours')
            self.assertTrue(cron_refresh.active)

        if cron_purge:
            self.assertEqual(cron_purge.interval_number, 1)
            self.assertEqual(cron_purge.interval_type, 'days')
            self.assertTrue(cron_purge.active)

        if cron_priority:
            self.assertEqual(cron_priority.interval_number, 1)
            self.assertEqual(cron_priority.interval_type, 'days')
            self.assertTrue(cron_priority.active)
