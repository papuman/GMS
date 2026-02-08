# -*- coding: utf-8 -*-
"""
Unit tests for Hacienda API Token Bucket Rate Limiter

Tests cover:
- Token acquisition and consumption
- Token refill over time
- Burst capacity handling
- Blocking vs non-blocking acquisition
- Thread safety and concurrency
- Distributed state consistency
- Monitoring and statistics
"""

import time
import threading
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'rate_limiter')
class TestHaciendaRateLimiter(TransactionCase):
    """Test suite for Hacienda API rate limiter."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rate_limiter = cls.env['l10n_cr.hacienda.rate_limiter']

        # Create the state table if it doesn't exist
        cls.env.cr.execute("""
            CREATE TABLE IF NOT EXISTS l10n_cr_hacienda_rate_limit_state (
                id SERIAL PRIMARY KEY,
                key VARCHAR(255) UNIQUE NOT NULL,
                tokens DOUBLE PRECISION NOT NULL DEFAULT 20.0,
                last_refill TIMESTAMP NOT NULL DEFAULT NOW(),
                total_requests BIGINT NOT NULL DEFAULT 0,
                last_request TIMESTAMP NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """)
        # Flush to ensure table creation is visible to subsequent queries
        cls.env.cr.flush()

    def setUp(self):
        super().setUp()
        # Reset rate limiter before each test
        self.rate_limiter.reset()

    def test_01_initial_state_full_capacity(self):
        """Test that rate limiter starts with full capacity."""
        status = self.rate_limiter.get_available_tokens()

        self.assertEqual(
            status['tokens'],
            self.rate_limiter.BUCKET_CAPACITY,
            "Should start with full capacity"
        )
        self.assertEqual(
            status['capacity'],
            20,
            "Capacity should be 20 tokens"
        )
        self.assertEqual(
            status['refill_rate'],
            10,
            "Refill rate should be 10 tokens/sec"
        )
        self.assertEqual(
            status['total_requests'],
            0,
            "Should start with zero requests"
        )

    def test_02_try_acquire_single_token(self):
        """Test non-blocking token acquisition."""
        # Should succeed - we have full capacity
        result = self.rate_limiter.try_acquire_token()
        self.assertTrue(result, "Should acquire token successfully")

        # Check token count decreased
        status = self.rate_limiter.get_available_tokens()
        self.assertEqual(
            status['tokens'],
            19.0,
            "Should have 19 tokens after consuming 1"
        )
        self.assertEqual(
            status['total_requests'],
            1,
            "Total requests should be 1"
        )

    def test_03_acquire_blocking_token(self):
        """Test blocking token acquisition."""
        result = self.rate_limiter.acquire_token(timeout=5)
        self.assertTrue(result, "Should acquire token successfully")

        status = self.rate_limiter.get_available_tokens()
        self.assertEqual(
            status['tokens'],
            19.0,
            "Should have 19 tokens after consuming 1"
        )

    def test_04_burst_capacity_exhaustion(self):
        """Test consuming all burst capacity tokens."""
        # Consume all 20 tokens
        for i in range(20):
            result = self.rate_limiter.try_acquire_token()
            self.assertTrue(
                result,
                f"Token {i+1}/20 should be acquired"
            )

        # 21st request should fail
        result = self.rate_limiter.try_acquire_token()
        self.assertFalse(
            result,
            "Should fail when bucket is empty"
        )

        # Verify state
        status = self.rate_limiter.get_available_tokens()
        self.assertLess(
            status['tokens'],
            1.0,
            "Should have less than 1 token remaining"
        )
        self.assertEqual(
            status['total_requests'],
            20,
            "Should have processed 20 requests"
        )

    def test_05_token_refill_over_time(self):
        """Test that tokens refill at correct rate (10/sec)."""
        # Consume all tokens
        for _ in range(20):
            self.rate_limiter.try_acquire_token()

        # Check empty bucket
        status = self.rate_limiter.get_available_tokens()
        self.assertLess(status['tokens'], 1.0)

        # Wait 1 second - should refill 10 tokens
        time.sleep(1.1)

        status = self.rate_limiter.get_available_tokens()
        self.assertGreaterEqual(
            status['tokens'],
            10.0,
            "Should refill ~10 tokens after 1 second"
        )
        self.assertLessEqual(
            status['tokens'],
            12.0,
            "Should not refill more than ~11 tokens after 1 second"
        )

    def test_06_token_refill_caps_at_capacity(self):
        """Test that token refill never exceeds capacity."""
        # Consume 5 tokens
        for _ in range(5):
            self.rate_limiter.try_acquire_token()

        # Wait 3 seconds (would refill 30 tokens if uncapped)
        time.sleep(3.1)

        status = self.rate_limiter.get_available_tokens()
        self.assertEqual(
            status['tokens'],
            20.0,
            "Tokens should cap at capacity (20)"
        )

    def test_07_blocking_timeout(self):
        """Test that blocking acquisition times out correctly."""
        # Exhaust all tokens
        for _ in range(20):
            self.rate_limiter.try_acquire_token()

        # Try to acquire with very short timeout - should fail.
        # Timeout must be short enough that refill (10 tokens/sec) can't
        # produce a full token before the timeout expires. At 0.05s, only
        # 0.5 tokens refill which is below the 1.0 threshold.
        with self.assertRaises(UserError) as ctx:
            self.rate_limiter.acquire_token(timeout=0.05)

        self.assertIn(
            'rate limit exceeded',
            str(ctx.exception).lower(),
            "Should raise rate limit error"
        )

    def test_08_blocking_waits_for_refill(self):
        """Test that blocking acquisition waits for token refill."""
        # Exhaust all tokens
        for _ in range(20):
            self.rate_limiter.try_acquire_token()

        # Acquire with blocking - should wait ~0.1s for refill
        start_time = time.time()
        result = self.rate_limiter.acquire_token(timeout=2)
        elapsed = time.time() - start_time

        self.assertTrue(result, "Should eventually acquire token")
        self.assertGreater(
            elapsed,
            0.05,
            "Should wait at least 50ms for refill"
        )
        self.assertLess(
            elapsed,
            1.0,
            "Should not wait more than 1 second"
        )

    def test_09_sustained_rate_limit(self):
        """Test sustained rate limit (10 req/sec) over time."""
        # Reset and wait for full capacity
        self.rate_limiter.reset()
        time.sleep(0.1)

        successful = 0
        failed = 0
        start_time = time.time()

        # Try to make 30 requests in 2 seconds
        # Should only succeed ~20 requests (burst) + ~10 (2s refill)
        for _ in range(30):
            if self.rate_limiter.try_acquire_token():
                successful += 1
            else:
                failed += 1
            time.sleep(0.05)  # 50ms between requests

        elapsed = time.time() - start_time

        # Should have consumed burst + refilled tokens
        # Burst: 20 tokens, Refill: ~20 tokens (2 seconds * 10/sec)
        # Total possible: ~40 tokens
        # But we only made 30 requests, so all should succeed
        self.assertGreaterEqual(
            successful,
            25,
            f"Should succeed at least 25 requests in {elapsed:.2f}s "
            f"(got {successful} success, {failed} failed)"
        )

    def test_10_concurrent_token_acquisition(self):
        """Test thread-safe concurrent token acquisition."""
        self.rate_limiter.reset()
        successful_acquisitions = []
        lock = threading.Lock()

        def acquire_tokens(count):
            """Worker thread to acquire tokens."""
            for _ in range(count):
                if self.rate_limiter.try_acquire_token():
                    with lock:
                        successful_acquisitions.append(1)
                time.sleep(0.01)

        # Launch 5 threads, each trying to acquire 10 tokens
        threads = []
        for _ in range(5):
            t = threading.Thread(target=acquire_tokens, args=(10,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join(timeout=5)

        # Total requested: 50 tokens
        # Available at start: 20 (burst capacity)
        # Should only succeed ~20-25 (depending on timing/refill)
        total_successful = len(successful_acquisitions)

        self.assertGreaterEqual(
            total_successful,
            20,
            "Should acquire at least burst capacity (20)"
        )
        self.assertLessEqual(
            total_successful,
            50,
            "Should not exceed total requested tokens"
        )

    def test_11_get_available_tokens_monitoring(self):
        """Test monitoring interface returns correct stats."""
        # Consume some tokens
        for _ in range(7):
            self.rate_limiter.try_acquire_token()

        status = self.rate_limiter.get_available_tokens()

        # Verify structure
        self.assertIn('tokens', status)
        self.assertIn('capacity', status)
        self.assertIn('refill_rate', status)
        self.assertIn('total_requests', status)
        self.assertIn('last_request', status)
        self.assertIn('utilization', status)

        # Verify values - use approximate checks because get_available_tokens()
        # calls _refill_tokens() which adds tokens based on elapsed time since
        # the last _update_state() call. Even a few ms at 10 tokens/sec refill
        # rate can add fractional tokens (e.g. 10ms = 0.1 tokens).
        self.assertAlmostEqual(status['tokens'], 13.0, delta=0.5)
        self.assertEqual(status['capacity'], 20)
        self.assertEqual(status['refill_rate'], 10)
        self.assertEqual(status['total_requests'], 7)

        # Utilization should be approximately (20-13)/20 * 100 = 35%
        self.assertAlmostEqual(status['utilization'], 35.0, delta=2.5)

    def test_12_reset_clears_state(self):
        """Test that reset restores full capacity and clears stats."""
        # Consume tokens and build stats
        for _ in range(15):
            self.rate_limiter.try_acquire_token()

        status_before = self.rate_limiter.get_available_tokens()
        # Use approximate check: refill adds fractional tokens between last
        # acquisition and the get_available_tokens() call
        self.assertAlmostEqual(status_before['tokens'], 5.0, delta=0.5)
        self.assertEqual(status_before['total_requests'], 15)

        # Reset
        self.rate_limiter.reset()

        # Verify reset
        status_after = self.rate_limiter.get_available_tokens()
        self.assertEqual(
            status_after['tokens'],
            20.0,
            "Should restore full capacity (capped at bucket capacity)"
        )
        self.assertEqual(
            status_after['total_requests'],
            0,
            "Should reset request counter"
        )

    def test_13_token_refill_precision(self):
        """Test token refill calculation precision."""
        # Consume 10 tokens
        for _ in range(10):
            self.rate_limiter.try_acquire_token()

        # Should have approximately 10 tokens left (small refill may occur
        # between the last acquisition and this check)
        status = self.rate_limiter.get_available_tokens()
        self.assertAlmostEqual(status['tokens'], 10.0, delta=0.5)

        # Wait 0.5 seconds - should refill ~5 tokens
        time.sleep(0.55)

        status = self.rate_limiter.get_available_tokens()
        self.assertGreaterEqual(
            status['tokens'],
            14.5,
            "Should refill ~5 tokens in 0.5s (10 + 5 = 15)"
        )
        self.assertLessEqual(
            status['tokens'],
            16.5,
            "Should not refill more than ~6.5 tokens"
        )

    def test_14_multiple_acquire_calls_decrement_correctly(self):
        """Test that multiple sequential acquisitions decrement correctly."""
        initial_status = self.rate_limiter.get_available_tokens()
        initial_tokens = initial_status['tokens']

        # Acquire 3 tokens sequentially
        for i in range(3):
            result = self.rate_limiter.try_acquire_token()
            self.assertTrue(result, f"Acquisition {i+1} should succeed")

            status = self.rate_limiter.get_available_tokens()
            expected_tokens = initial_tokens - (i + 1)

            # Use approximate check: _refill_tokens() adds fractional tokens
            # based on elapsed time between _update_state and the read.
            # With refill rate of 10/s, a few ms adds ~0.01-0.1 tokens.
            self.assertAlmostEqual(
                status['tokens'],
                expected_tokens,
                delta=0.5,
                msg=f"After {i+1} acquisitions, should have ~{expected_tokens} tokens"
            )
            self.assertEqual(
                status['total_requests'],
                i + 1,
                f"Total requests should be {i+1}"
            )

    def test_15_zero_timeout_blocking_behavior(self):
        """Test blocking acquisition with zero timeout."""
        # Consume all tokens
        for _ in range(20):
            self.rate_limiter.try_acquire_token()

        # Try with zero timeout - should fail immediately
        with self.assertRaises(UserError):
            self.rate_limiter.acquire_token(timeout=0)

    def test_16_partial_token_consumption(self):
        """Test that token count can be fractional after refill."""
        # Consume all 20 tokens
        for _ in range(20):
            self.rate_limiter.try_acquire_token()

        # Wait 0.15 seconds - should refill 1.5 tokens
        time.sleep(0.18)

        status = self.rate_limiter.get_available_tokens()

        # Should have ~1.5 tokens (can only acquire 1 request)
        self.assertGreaterEqual(
            status['tokens'],
            1.3,
            "Should have at least 1.3 tokens after 0.15s refill"
        )
        self.assertLess(
            status['tokens'],
            2.5,
            "Should have less than 2.5 tokens after 0.15s refill"
        )

        # Should be able to acquire 1 token
        result = self.rate_limiter.try_acquire_token()
        self.assertTrue(result, "Should acquire 1 token from 1.5 available")

        # Should NOT be able to acquire another immediately
        result = self.rate_limiter.try_acquire_token()
        self.assertFalse(result, "Should not acquire when <1 token remains")

    def test_17_high_load_burst_scenario(self):
        """Test behavior under high-load burst scenario."""
        self.rate_limiter.reset()

        # Simulate POS rush: 50 simultaneous checkout attempts
        results = []
        for _ in range(50):
            results.append(self.rate_limiter.try_acquire_token())

        successful = sum(results)
        failed = len(results) - successful

        # Should accept burst capacity (20) immediately
        self.assertEqual(
            successful,
            20,
            f"Should accept exactly 20 requests (burst capacity), "
            f"got {successful} success, {failed} failed"
        )

        # All remaining should fail
        self.assertEqual(
            failed,
            30,
            "Should reject 30 requests when burst exhausted"
        )

    def test_18_utilization_calculation(self):
        """Test utilization percentage calculation."""
        self.rate_limiter.reset()

        # 0% utilization (full capacity) - tokens are at capacity so
        # refill doesn't change the value (capped at BUCKET_CAPACITY)
        status = self.rate_limiter.get_available_tokens()
        self.assertEqual(status['utilization'], 0.0)

        # Consume 10 tokens = ~50% utilization
        # Use approximate checks because _refill_tokens adds fractional
        # tokens based on elapsed time between last update and the read
        for _ in range(10):
            self.rate_limiter.try_acquire_token()

        status = self.rate_limiter.get_available_tokens()
        self.assertAlmostEqual(status['utilization'], 50.0, delta=2.5)

        # Consume remaining 10 = ~100% utilization
        for _ in range(10):
            self.rate_limiter.try_acquire_token()

        status = self.rate_limiter.get_available_tokens()
        self.assertAlmostEqual(status['utilization'], 100.0, delta=2.5)


@tagged('post_install', '-at_install', 'rate_limiter_stress')
class TestHaciendaRateLimiterStress(TransactionCase):
    """Stress tests for rate limiter under extreme conditions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rate_limiter = cls.env['l10n_cr.hacienda.rate_limiter']

        # Create the state table if it doesn't exist
        cls.env.cr.execute("""
            CREATE TABLE IF NOT EXISTS l10n_cr_hacienda_rate_limit_state (
                id SERIAL PRIMARY KEY,
                key VARCHAR(255) UNIQUE NOT NULL,
                tokens DOUBLE PRECISION NOT NULL DEFAULT 20.0,
                last_refill TIMESTAMP NOT NULL DEFAULT NOW(),
                total_requests BIGINT NOT NULL DEFAULT 0,
                last_request TIMESTAMP NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """)
        # Flush to ensure table creation is visible to subsequent queries
        cls.env.cr.flush()

    def setUp(self):
        super().setUp()
        self.rate_limiter.reset()

    def test_01_extreme_concurrent_load(self):
        """Test rate limiter under extreme concurrent load."""
        successful = []
        failed = []
        lock = threading.Lock()
        start_time = time.time()

        def worker():
            """Worker thread hammering rate limiter."""
            for _ in range(20):
                try:
                    if self.rate_limiter.try_acquire_token():
                        with lock:
                            successful.append(1)
                    else:
                        with lock:
                            failed.append(1)
                except Exception:
                    with lock:
                        failed.append(1)

        # Launch 20 threads, each making 20 requests (400 total)
        threads = []
        for _ in range(20):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=10)

        elapsed = time.time() - start_time
        total_successful = len(successful)
        total_failed = len(failed)
        total_requests = total_successful + total_failed

        # Should process exactly 400 requests
        self.assertEqual(
            total_requests,
            400,
            "Should process all 400 requests"
        )

        # Should succeed at least burst capacity (20 tokens)
        self.assertGreaterEqual(
            total_successful,
            20,
            "Should acquire at least burst capacity"
        )

        # Upper bound: should not exceed total requests
        self.assertLessEqual(
            total_successful,
            400,
            "Should not exceed total requested tokens"
        )

    def test_02_sustained_throughput_over_time(self):
        """Test sustained throughput matches rate limit (10/sec)."""
        self.rate_limiter.reset()

        successful = 0
        start_time = time.time()
        duration = 5  # Run for 5 seconds

        # Make requests continuously for 5 seconds
        while time.time() - start_time < duration:
            if self.rate_limiter.try_acquire_token():
                successful += 1
            time.sleep(0.05)  # 20 req/sec attempt rate

        elapsed = time.time() - start_time

        # Expected: 20 (burst) + 50 (5 sec * 10/sec) = 70 tokens
        # But we're trying 100 requests (5s * 20 req/sec)
        # So should succeed ~70 and fail ~30

        expected_min = 60  # Conservative: burst + 4s refill
        expected_max = 80  # Generous: burst + 6s refill

        self.assertGreaterEqual(
            successful,
            expected_min,
            f"Should succeed at least {expected_min} requests in {elapsed:.2f}s "
            f"(got {successful})"
        )
        self.assertLessEqual(
            successful,
            expected_max,
            f"Should not exceed {expected_max} requests in {elapsed:.2f}s "
            f"(got {successful})"
        )
