# -*- coding: utf-8 -*-
"""
Application-wide Token Bucket Rate Limiter for Hacienda API

Implements a distributed token bucket algorithm to enforce rate limits across
all POS terminals and API clients:
- Sustained rate: 10 requests/second
- Burst capacity: 20 requests/second
- Application-wide (shared state across all users/terminals)
- Thread-safe and distributed using PostgreSQL

Architecture:
- Uses PostgreSQL advisory locks for atomicity
- State stored in database table for multi-instance support
- Token bucket algorithm with precise time-based refill
- No external dependencies (Redis-free, pure Odoo)
"""

import logging
import time
import threading
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HaciendaRateLimiter(models.AbstractModel):
    """
    Token bucket rate limiter for Hacienda API requests.

    This is an application-wide singleton rate limiter that enforces:
    - Maximum burst: 20 requests
    - Sustained rate: 10 requests/second
    - Distributed state across multiple Odoo instances
    """

    _name = 'l10n_cr.hacienda.rate_limiter'
    _description = 'Hacienda API Rate Limiter'

    # Rate limit configuration
    BUCKET_CAPACITY = 20  # Maximum burst tokens (20 req/sec burst)
    REFILL_RATE = 10      # Tokens per second (10 req/sec sustained)
    BUCKET_KEY = 'hacienda_api_rate_limiter'  # Singleton key
    ADVISORY_LOCK_ID = 123456789  # PostgreSQL advisory lock ID

    # Local thread-safe cache to reduce DB queries
    _local_cache = threading.local()
    _cache_ttl = 0.1  # 100ms cache TTL

    @api.model
    def _get_state_table(self):
        """
        Get or create the rate limiter state table.

        Returns a dict with:
        - tokens: current token count (float)
        - last_refill: timestamp of last refill (datetime)
        - total_requests: total requests processed (int)
        - last_request: timestamp of last request (datetime)
        """
        self.env.cr.execute("""
            SELECT tokens, last_refill, total_requests, last_request
            FROM l10n_cr_hacienda_rate_limit_state
            WHERE key = %s
            FOR UPDATE
        """, (self.BUCKET_KEY,))

        row = self.env.cr.fetchone()

        if row:
            return {
                'tokens': row[0],
                'last_refill': row[1],
                'total_requests': row[2],
                'last_request': row[3],
            }
        else:
            # Initialize bucket with full capacity
            now = datetime.utcnow()
            self.env.cr.execute("""
                INSERT INTO l10n_cr_hacienda_rate_limit_state
                    (key, tokens, last_refill, total_requests, last_request, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                self.BUCKET_KEY,
                float(self.BUCKET_CAPACITY),
                now,
                0,
                now,
                now,
            ))
            # Flush to ensure INSERT is visible to subsequent queries
            # Do not commit - let caller control transaction boundary
            self.env.cr.flush()

            return {
                'tokens': float(self.BUCKET_CAPACITY),
                'last_refill': now,
                'total_requests': 0,
                'last_request': now,
            }

    @api.model
    def _update_state(self, tokens, total_requests):
        """
        Update the rate limiter state in database.

        Args:
            tokens: New token count
            total_requests: Updated total request count
        """
        now = datetime.utcnow()
        self.env.cr.execute("""
            UPDATE l10n_cr_hacienda_rate_limit_state
            SET tokens = %s,
                last_refill = %s,
                total_requests = %s,
                last_request = %s,
                updated_at = %s
            WHERE key = %s
        """, (
            tokens,
            now,
            total_requests,
            now,
            now,
            self.BUCKET_KEY,
        ))
        # Flush to ensure UPDATE is visible to subsequent queries
        # Do not commit - let caller control transaction boundary
        self.env.cr.flush()

    @api.model
    def _refill_tokens(self, state):
        """
        Calculate token refill based on elapsed time.

        Token bucket algorithm:
        1. Calculate time elapsed since last refill
        2. Add tokens: elapsed_time * REFILL_RATE
        3. Cap at BUCKET_CAPACITY

        Args:
            state: Current state dict from _get_state_table()

        Returns:
            float: New token count after refill
        """
        now = datetime.utcnow()
        last_refill = state['last_refill']

        # Handle timezone-naive datetime from database
        if last_refill.tzinfo is None:
            last_refill = last_refill.replace(tzinfo=None)
        if now.tzinfo is None:
            now = now.replace(tzinfo=None)

        elapsed = (now - last_refill).total_seconds()

        # Calculate new tokens
        tokens_to_add = elapsed * self.REFILL_RATE
        new_tokens = min(
            state['tokens'] + tokens_to_add,
            float(self.BUCKET_CAPACITY)
        )

        return new_tokens

    @api.model
    def _acquire_lock(self):
        """
        Acquire PostgreSQL advisory lock for atomic operations.

        Advisory locks are session-based and automatically released
        on transaction commit/rollback or session end.
        """
        self.env.cr.execute(
            "SELECT pg_advisory_lock(%s)",
            (self.ADVISORY_LOCK_ID,)
        )

    @api.model
    def _release_lock(self):
        """Release PostgreSQL advisory lock."""
        self.env.cr.execute(
            "SELECT pg_advisory_unlock(%s)",
            (self.ADVISORY_LOCK_ID,)
        )

    @api.model
    def try_acquire_token(self):
        """
        Try to acquire a token immediately without blocking.

        This is the non-blocking variant - returns immediately.
        Use this when you want to check if a request can proceed
        without waiting.

        Returns:
            bool: True if token acquired, False if rate limit exceeded
        """
        try:
            self._acquire_lock()

            # Get current state
            state = self._get_state_table()

            # Refill tokens based on elapsed time
            current_tokens = self._refill_tokens(state)

            # Check if we have tokens available
            if current_tokens >= 1.0:
                # Consume one token
                new_tokens = current_tokens - 1.0
                new_total = state['total_requests'] + 1

                self._update_state(new_tokens, new_total)

                _logger.debug(
                    f"Rate limiter: Token acquired. "
                    f"Remaining: {new_tokens:.2f}/{self.BUCKET_CAPACITY}, "
                    f"Total requests: {new_total}"
                )

                return True
            else:
                # No tokens available
                wait_time = (1.0 - current_tokens) / self.REFILL_RATE
                _logger.warning(
                    f"Rate limiter: No tokens available. "
                    f"Current: {current_tokens:.2f}/{self.BUCKET_CAPACITY}. "
                    f"Wait ~{wait_time:.2f}s"
                )

                return False

        finally:
            self._release_lock()

    @api.model
    def acquire_token(self, timeout=30):
        """
        Acquire a token, blocking until one is available.

        This method will wait (with exponential backoff) until a token
        becomes available or the timeout is reached.

        Args:
            timeout: Maximum seconds to wait (default: 30)

        Returns:
            bool: True if token acquired

        Raises:
            UserError: If timeout is reached without acquiring token
        """
        start_time = time.time()
        attempt = 0

        while True:
            # Try to acquire token
            if self.try_acquire_token():
                return True

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise UserError(_(
                    'Hacienda API rate limit exceeded. '
                    'Maximum wait time of %d seconds reached. '
                    'Please try again later.'
                ) % timeout)

            # Exponential backoff: 0.1s, 0.2s, 0.4s, 0.8s, max 2s
            wait_time = min(0.1 * (2 ** attempt), 2.0)

            # Don't wait longer than remaining timeout
            wait_time = min(wait_time, timeout - elapsed)

            _logger.debug(
                f"Rate limiter: Waiting {wait_time:.2f}s "
                f"(attempt {attempt + 1}, elapsed {elapsed:.2f}s)"
            )

            time.sleep(wait_time)
            attempt += 1

    @api.model
    def get_available_tokens(self):
        """
        Get the current number of available tokens (for monitoring).

        This is a read-only operation that doesn't consume tokens.
        Useful for dashboards, health checks, and debugging.

        Returns:
            dict: {
                'tokens': current token count,
                'capacity': maximum capacity,
                'refill_rate': tokens per second,
                'total_requests': lifetime request count,
                'last_request': timestamp of last request,
            }
        """
        try:
            self._acquire_lock()

            state = self._get_state_table()
            current_tokens = self._refill_tokens(state)

            return {
                'tokens': round(current_tokens, 2),
                'capacity': self.BUCKET_CAPACITY,
                'refill_rate': self.REFILL_RATE,
                'total_requests': state['total_requests'],
                'last_request': state['last_request'],
                'utilization': round(
                    (self.BUCKET_CAPACITY - current_tokens) / self.BUCKET_CAPACITY * 100,
                    2
                ),
            }

        finally:
            self._release_lock()

    @api.model
    def reset(self, commit=False):
        """
        Reset the rate limiter to full capacity.

        WARNING: This should only be used for testing or administrative
        purposes. It will reset the token bucket to full capacity and
        clear statistics.

        Args:
            commit (bool): Whether to commit the transaction. Default False.
                          Set to True in production cron jobs, False in tests.
        """
        try:
            self._acquire_lock()

            now = datetime.utcnow()
            self.env.cr.execute("""
                UPDATE l10n_cr_hacienda_rate_limit_state
                SET tokens = %s,
                    last_refill = %s,
                    total_requests = 0,
                    last_request = %s,
                    updated_at = %s
                WHERE key = %s
            """, (
                float(self.BUCKET_CAPACITY),
                now,
                now,
                now,
                self.BUCKET_KEY,
            ))

            if commit:
                self.env.cr.commit()
            else:
                # Flush to ensure UPDATE is visible without committing
                self.env.cr.flush()

            _logger.info("Rate limiter reset to full capacity")

        finally:
            self._release_lock()


# SQL migration to create the state table
# This should be added to a migration script or executed manually:
"""
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

CREATE INDEX IF NOT EXISTS idx_hacienda_rate_limit_key
    ON l10n_cr_hacienda_rate_limit_state(key);

COMMENT ON TABLE l10n_cr_hacienda_rate_limit_state IS
    'Distributed rate limiter state for Hacienda API (Token Bucket Algorithm)';
COMMENT ON COLUMN l10n_cr_hacienda_rate_limit_state.tokens IS
    'Current number of available tokens (max 20 for burst)';
COMMENT ON COLUMN l10n_cr_hacienda_rate_limit_state.last_refill IS
    'Timestamp of last token refill calculation';
COMMENT ON COLUMN l10n_cr_hacienda_rate_limit_state.total_requests IS
    'Lifetime counter of all requests processed';
"""
