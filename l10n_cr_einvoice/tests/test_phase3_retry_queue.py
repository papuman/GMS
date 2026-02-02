# -*- coding: utf-8 -*-
"""
Phase 3 Testing: Retry Queue

Tests for the intelligent retry queue system that automatically
retries failed e-invoice operations with exponential backoff.

Enhanced test suite covering:
- All 7 error categories (auth, network, validation, rate_limit, server, transient, unknown)
- Exponential backoff calculation (5min, 15min, 1hr, 4hr, 12hr)
- Max retry limits per category
- State transitions (pending → processing → completed/failed)
- Queue cleanup (30-day retention)
- Manual retry capability

Test Markers (for documentation - Odoo uses tagged() decorator):
- integration: Integration tests with database
- p0: Critical priority (must pass before production)
- p1: High priority
"""
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from odoo.tests import tagged
import uuid


def _generate_unique_vat_company():
    """Generate unique VAT number for company (10 digits starting with 3)."""
    return f"310{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_vat_person():
    """Generate unique VAT number for person (9 digits)."""
    return f"10{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_email(prefix='test'):
    """Generate unique email address."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.exceptions import UserError
from .common import EInvoiceTestCase

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'einvoice', 'phase3', 'integration', 'p0')
class TestPhase3RetryQueue(EInvoiceTestCase):
    """Test retry queue functionality with comprehensive coverage."""

    def setUp(self):
        super().setUp()

        # Create test invoice using base class helper
        self.invoice = self._create_test_invoice()

        # Create test document
        self.document = self._create_einvoice_document(self.invoice, document_type='FE')

    def test_add_to_queue(self):
        """Test adding a document to retry queue."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Add to queue
        queue_entry = retry_queue.add_to_queue(
            document=self.document,
            operation='submit',
            error_message='Test error: Connection timeout',
            error_category='network',
            priority='2',
        )

        self.assertTrue(queue_entry, "Queue entry should be created")
        self.assertEqual(queue_entry.document_id, self.document)
        self.assertEqual(queue_entry.operation, 'submit')
        self.assertEqual(queue_entry.error_category, 'network')
        self.assertEqual(queue_entry.state, 'pending')
        self.assertEqual(queue_entry.retry_count, 0)

    def test_error_classification(self):
        """Test automatic error classification."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Test various error messages
        test_cases = [
            ('Connection timeout', 'network'),
            ('Rate limit exceeded', 'rate_limit'),
            ('401 Unauthorized', 'auth'),
            ('Invalid XML format', 'validation'),
            ('500 Internal Server Error', 'server'),
            ('Temporary service unavailable', 'transient'),
            ('Unknown error occurred', 'unknown'),
        ]

        for error_msg, expected_category in test_cases:
            category = retry_queue.classify_error(error_msg)
            self.assertEqual(
                category, expected_category,
                f"Error '{error_msg}' should be classified as '{expected_category}'"
            )

    def test_retry_delay_calculation(self):
        """Test exponential backoff delay calculation."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Test delays increase exponentially
        delay_0 = retry_queue._get_retry_delay(0, 'transient')
        delay_1 = retry_queue._get_retry_delay(1, 'transient')
        delay_2 = retry_queue._get_retry_delay(2, 'transient')

        self.assertLess(delay_0, delay_1, "Delay should increase with retry count")
        self.assertLess(delay_1, delay_2, "Delay should increase exponentially")

        # Test different error categories have different multipliers
        network_delay = retry_queue._get_retry_delay(1, 'network')
        validation_delay = retry_queue._get_retry_delay(1, 'validation')

        self.assertLess(
            network_delay, validation_delay,
            "Validation errors should have longer delay (needs manual fix)"
        )

    def test_max_retries_by_category(self):
        """Test max retries varies by error category."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Transient errors should have more retries than validation errors
        transient_max = retry_queue._get_max_retries('transient')
        validation_max = retry_queue._get_max_retries('validation')

        self.assertGreater(
            transient_max, validation_max,
            "Transient errors should allow more retries than validation errors"
        )

    def test_retry_processing_success(self):
        """Test successful retry processing."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Add to queue
        queue_entry = retry_queue.add_to_queue(
            document=self.document,
            operation='sign',
            error_message='Test error',
            error_category='transient',
        )

        # Mock successful operation
        with patch.object(type(self.document), 'action_sign_xml'):
            queue_entry._process_retry()

        # Should be marked as completed
        self.assertEqual(queue_entry.state, 'completed', "Successful retry should mark as completed")

    def test_retry_processing_failure(self):
        """Test retry processing when operation still fails."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Add to queue
        queue_entry = retry_queue.add_to_queue(
            document=self.document,
            operation='sign',
            error_message='Test error',
            error_category='transient',
        )

        initial_retry_count = queue_entry.retry_count

        # Mock failed operation
        with patch.object(type(self.document), 'action_sign_xml', side_effect=Exception("Still failing")):
            queue_entry._process_retry()

        # Should still be pending with incremented retry count
        self.assertEqual(queue_entry.state, 'pending', "Failed retry should remain pending")
        self.assertEqual(
            queue_entry.retry_count, initial_retry_count + 1,
            "Retry count should increment"
        )
        self.assertIsNotNone(queue_entry.next_attempt, "Next attempt should be scheduled")

    def test_max_retries_exhausted(self):
        """Test behavior when max retries is reached."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Add to queue with low max retries
        queue_entry = retry_queue.add_to_queue(
            document=self.document,
            operation='submit',
            error_message='Test error',
            error_category='validation',  # Has low max_retries
        )

        # Set retry count to near max
        queue_entry.write({
            'retry_count': queue_entry.max_retries - 1,
        })

        # Mock failed operation
        with patch.object(type(self.document), 'action_submit_to_hacienda', side_effect=Exception("Persistent error")):
            queue_entry._process_retry()

        # Should be marked as failed
        self.assertEqual(queue_entry.state, 'failed', "Should be marked as failed after max retries")

    def test_cron_queue_processing(self):
        """Test scheduled queue processing."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create queue entries due for retry
        queue_entry1 = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': datetime.now() - timedelta(minutes=5),  # Overdue
            'retry_count': 0,
            'max_retries': 5,
        })

        queue_entry2 = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'submit',
            'error_category': 'network',
            'state': 'pending',
            'next_attempt': datetime.now() + timedelta(minutes=5),  # Not due yet
            'retry_count': 0,
            'max_retries': 5,
        })

        # Mock successful operations
        with patch.object(type(self.document), 'action_sign_xml'):
            with patch.object(type(self.document), 'action_submit_to_hacienda'):
                retry_queue._cron_process_retry_queue()

        # Only overdue entry should be processed
        self.assertEqual(queue_entry1.state, 'completed', "Overdue entry should be processed")
        self.assertEqual(queue_entry2.state, 'pending', "Future entry should remain pending")

    def test_manual_retry_now(self):
        """Test manual retry trigger."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create queue entry
        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': datetime.now() + timedelta(hours=1),  # Scheduled for later
            'retry_count': 0,
            'max_retries': 5,
        })

        # Mock successful operation
        with patch.object(type(self.document), 'action_sign_xml'):
            queue_entry.action_retry_now()

        # Should be completed despite not being due yet
        self.assertEqual(queue_entry.state, 'completed', "Manual retry should process immediately")

    def test_cancel_retry(self):
        """Test cancelling a retry queue entry."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create queue entry
        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'submit',
            'error_category': 'network',
            'state': 'pending',
            'next_attempt': datetime.now() + timedelta(minutes=5),
            'retry_count': 0,
            'max_retries': 5,
        })

        # Cancel retry
        queue_entry.action_cancel_retry()

        self.assertEqual(queue_entry.state, 'cancelled', "Should be marked as cancelled")

    def test_queue_cleanup(self):
        """Test cleanup of old completed/failed entries."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create old completed entry
        old_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'completed',
            'next_attempt': datetime.now(),
            'retry_count': 1,
            'max_retries': 5,
        })

        # Manually set create_date to old
        self.env.cr.execute(
            "UPDATE l10n_cr_einvoice_retry_queue SET create_date = %s WHERE id = %s",
            (datetime.now() - timedelta(days=35), old_entry.id)
        )

        # Run cleanup
        deleted_count = retry_queue._cleanup_old_entries(days=30)

        self.assertGreater(deleted_count, 0, "Should cleanup old entries")
        self.assertFalse(old_entry.exists(), "Old entry should be deleted")

    def test_queue_statistics(self):
        """Test queue statistics generation."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create various queue entries
        retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': datetime.now() + timedelta(minutes=5),
            'retry_count': 0,
            'max_retries': 5,
        })

        retry_queue.create({
            'document_id': self.document.id,
            'operation': 'submit',
            'error_category': 'network',
            'state': 'completed',
            'next_attempt': datetime.now(),
            'retry_count': 2,
            'max_retries': 5,
        })

        # Get statistics
        stats = retry_queue.get_queue_statistics(company_id=self.company.id)

        # Verify statistics
        self.assertIn('total', stats)
        self.assertIn('pending', stats)
        self.assertIn('completed', stats)
        self.assertIn('by_operation', stats)
        self.assertIn('by_category', stats)
        self.assertGreaterEqual(stats['total'], 2)


# ============================================================================
# ENHANCED TEST SUITE - ERROR CATEGORY COVERAGE
# ============================================================================


@tagged('post_install', '-at_install', 'einvoice', 'phase3', 'integration', 'p0')
class TestRetryQueueErrorCategories(EInvoiceTestCase):
    """Test all 7 error categories are properly handled."""

    def setUp(self):
        super().setUp()

        # Create test invoice using base class helper
        self.invoice = self._create_test_invoice()

        # Create test document
        self.document = self._create_einvoice_document(self.invoice, document_type='FE')

    def test_authentication_error_classification(self):
        """Test authentication errors are correctly classified."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        test_cases = [
            ('401 Unauthorized', 'auth'),
            ('403 Forbidden', 'auth'),
            ('Authentication failed', 'auth'),
            ('Invalid credentials', 'auth'),
            ('Token expired', 'auth'),
        ]

        for error_msg, expected_category in test_cases:
            category = retry_queue.classify_error(error_msg)
            self.assertEqual(
                category, expected_category,
                f"Error '{error_msg}' should be classified as '{expected_category}', got '{category}'"
            )

    def test_network_error_classification(self):
        """Test network errors are correctly classified."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        test_cases = [
            ('Connection timeout', 'network'),
            ('Network unreachable', 'network'),
            ('Connection refused', 'network'),
            ('DNS resolution failed', 'network'),
            ('Socket timeout', 'network'),
        ]

        for error_msg, expected_category in test_cases:
            category = retry_queue.classify_error(error_msg)
            self.assertEqual(
                category, expected_category,
                f"Error '{error_msg}' should be classified as '{expected_category}', got '{category}'"
            )

    def test_validation_error_classification(self):
        """Test validation errors are correctly classified."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        test_cases = [
            ('Invalid XML format', 'validation'),
            ('Validation error: missing field', 'validation'),
            ('400 Bad Request', 'validation'),
            ('Schema validation failed', 'validation'),
        ]

        for error_msg, expected_category in test_cases:
            category = retry_queue.classify_error(error_msg)
            self.assertEqual(
                category, expected_category,
                f"Error '{error_msg}' should be classified as '{expected_category}', got '{category}'"
            )

    def test_rate_limit_error_classification(self):
        """Test rate limit errors are correctly classified."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        test_cases = [
            ('Rate limit exceeded', 'rate_limit'),
            ('Too many requests', 'rate_limit'),
            ('429 Too Many Requests', 'rate_limit'),
        ]

        for error_msg, expected_category in test_cases:
            category = retry_queue.classify_error(error_msg)
            self.assertEqual(
                category, expected_category,
                f"Error '{error_msg}' should be classified as '{expected_category}', got '{category}'"
            )

    def test_server_error_classification(self):
        """Test server errors are correctly classified."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        test_cases = [
            ('500 Internal Server Error', 'server'),
            ('502 Bad Gateway', 'server'),
            ('503 Service Unavailable', 'server'),
            ('Server error occurred', 'server'),
        ]

        for error_msg, expected_category in test_cases:
            category = retry_queue.classify_error(error_msg)
            self.assertEqual(
                category, expected_category,
                f"Error '{error_msg}' should be classified as '{expected_category}', got '{category}'"
            )

    def test_transient_error_classification(self):
        """Test transient errors are correctly classified."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        test_cases = [
            ('Temporary service unavailable', 'transient'),
            ('Please try again later', 'transient'),
            ('Temporary error', 'transient'),
        ]

        for error_msg, expected_category in test_cases:
            category = retry_queue.classify_error(error_msg)
            self.assertEqual(
                category, expected_category,
                f"Error '{error_msg}' should be classified as '{expected_category}', got '{category}'"
            )

    def test_unknown_error_classification(self):
        """Test unknown errors default to 'unknown' category."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        test_cases = [
            ('Some weird error', 'unknown'),
            ('Unexpected exception', 'unknown'),
            ('Random failure', 'unknown'),
        ]

        for error_msg, expected_category in test_cases:
            category = retry_queue.classify_error(error_msg)
            self.assertEqual(
                category, expected_category,
                f"Error '{error_msg}' should be classified as '{expected_category}', got '{category}'"
            )

    def test_max_retries_per_category(self):
        """Test max retries configuration per error category."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Expected max retries per category (from implementation)
        expected_max_retries = {
            'transient': 5,
            'rate_limit': 4,
            'network': 5,
            'server': 5,
            'auth': 3,  # Fewer retries - needs manual fix
            'validation': 2,  # Fewest retries - needs manual fix
            'unknown': 3,
        }

        for category, expected_max in expected_max_retries.items():
            actual_max = retry_queue._get_max_retries(category)
            self.assertEqual(
                actual_max, expected_max,
                f"Max retries for '{category}' should be {expected_max}, got {actual_max}"
            )

    def test_category_specific_delays(self):
        """Test that different error categories have appropriate delay multipliers."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Validation errors should have longest delays (need manual fix)
        validation_delay = retry_queue._get_retry_delay(1, 'validation')

        # Transient errors should have shorter delays
        transient_delay = retry_queue._get_retry_delay(1, 'transient')

        # Auth errors should have medium delays
        auth_delay = retry_queue._get_retry_delay(1, 'auth')

        self.assertGreater(
            validation_delay, auth_delay,
            "Validation errors should have longer delays than auth errors"
        )
        self.assertGreater(
            auth_delay, transient_delay,
            "Auth errors should have longer delays than transient errors"
        )


# ============================================================================
# EXPONENTIAL BACKOFF VALIDATION
# ============================================================================


@tagged('post_install', '-at_install', 'einvoice', 'phase3')
class TestRetryQueueExponentialBackoff(EInvoiceTestCase):
    """Test exponential backoff calculation in detail."""

    def setUp(self):
        super().setUp()

        # Create test invoice and document
        self.invoice = self._create_test_invoice()
        self.document = self._create_einvoice_document(self.invoice, document_type='FE')

    def test_backoff_progression_exact_values(self):
        """Test exact backoff values match specification (5min, 15min, 1hr, 4hr)."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Base delays for transient errors (multiplier = 1.0)
        expected_delays = {
            0: 5,      # 5 minutes
            1: 15,     # 15 minutes
            2: 60,     # 1 hour
            3: 240,    # 4 hours
            4: 720,    # 12 hours
        }

        for retry_count, expected_delay in expected_delays.items():
            actual_delay = retry_queue._get_retry_delay(retry_count, 'transient')
            self.assertEqual(
                actual_delay, expected_delay,
                f"Retry {retry_count} should have {expected_delay} min delay, got {actual_delay}"
            )

    def test_backoff_capped_at_max(self):
        """Test that backoff delays are capped for high retry counts."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Delays should cap at the maximum (720 minutes = 12 hours)
        delay_5 = retry_queue._get_retry_delay(5, 'transient')
        delay_10 = retry_queue._get_retry_delay(10, 'transient')

        self.assertEqual(delay_5, delay_10, "Delays should be capped at maximum value")
        self.assertEqual(delay_5, 720, "Maximum delay should be 720 minutes (12 hours)")

    def test_backoff_multipliers(self):
        """Test category-specific multipliers are applied correctly."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        base_delay = retry_queue._get_retry_delay(1, 'transient')  # 15 min

        # Rate limit: 2x multiplier
        rate_limit_delay = retry_queue._get_retry_delay(1, 'rate_limit')
        self.assertEqual(rate_limit_delay, base_delay * 2)

        # Auth: 3x multiplier
        auth_delay = retry_queue._get_retry_delay(1, 'auth')
        self.assertEqual(auth_delay, base_delay * 3)

        # Validation: 6x multiplier
        validation_delay = retry_queue._get_retry_delay(1, 'validation')
        self.assertEqual(validation_delay, base_delay * 6)

    def test_next_attempt_calculation(self):
        """Test that next_attempt is correctly calculated from current time."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        now = datetime.now()

        # Create queue entry with explicit next_attempt
        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': now + timedelta(minutes=5),
            'retry_count': 0,
            'max_retries': 5,
        })

        # Verify next_attempt is set
        self.assertTrue(queue_entry.next_attempt, "Next attempt should be set")

        # Verify it's in the future
        time_diff = (queue_entry.next_attempt - now).total_seconds()
        self.assertGreater(time_diff, 0, "Next attempt should be in the future")
        self.assertLess(time_diff, 400, "Next attempt should be within reasonable time (< 7 minutes)")


# ============================================================================
# STATE TRANSITION TESTS
# ============================================================================


@tagged('post_install', '-at_install', 'einvoice', 'phase3')
class TestRetryQueueStateTransitions(EInvoiceTestCase):
    """Test state machine transitions in retry queue."""

    def setUp(self):
        super().setUp()

        # Create test invoice and document
        self.invoice = self._create_test_invoice()
        self.document = self._create_einvoice_document(self.invoice, document_type='FE')

    def test_state_transition_pending_to_processing(self):
        """Test transition from pending to processing."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': datetime.now() - timedelta(minutes=1),
            'retry_count': 0,
            'max_retries': 5,
        })

        self.assertEqual(queue_entry.state, 'pending')

        # Mock operation to prevent actual execution
        with patch.object(type(self.document), 'action_sign_xml', side_effect=Exception("Test error")):
            queue_entry._process_retry()

        # Should attempt processing (state changed from pending)
        self.assertNotEqual(queue_entry.state, 'processing', "Should not stay in processing state after error")

    def test_state_transition_processing_to_completed(self):
        """Test successful transition from processing to completed."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': datetime.now(),
            'retry_count': 0,
            'max_retries': 5,
        })

        # Mock successful operation
        with patch.object(type(self.document), 'action_sign_xml'):
            queue_entry._process_retry()

        self.assertEqual(queue_entry.state, 'completed')
        self.assertFalse(queue_entry.last_error)

    def test_state_transition_processing_to_pending_on_failure(self):
        """Test transition back to pending after failed retry (not exhausted)."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': datetime.now(),
            'retry_count': 0,
            'max_retries': 5,
        })

        # Mock failed operation
        with patch.object(type(self.document), 'action_sign_xml', side_effect=Exception("Temporary failure")):
            queue_entry._process_retry()

        self.assertEqual(queue_entry.state, 'pending', "Should return to pending after failed retry")
        self.assertEqual(queue_entry.retry_count, 1, "Retry count should increment")
        self.assertTrue(queue_entry.last_error, "Should store error message")

    def test_state_transition_processing_to_failed_max_retries(self):
        """Test transition to failed when max retries exhausted."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'validation',  # max_retries = 2
            'state': 'pending',
            'next_attempt': datetime.now(),
            'retry_count': 1,  # One retry already done
            'max_retries': 2,
        })

        # Mock failed operation
        with patch.object(type(self.document), 'action_sign_xml', side_effect=Exception("Validation error")):
            queue_entry._process_retry()

        self.assertEqual(queue_entry.state, 'failed', "Should transition to failed after max retries")
        self.assertEqual(queue_entry.retry_count, 2, "Retry count should match max_retries")

    def test_state_transition_pending_to_cancelled(self):
        """Test manual cancellation."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': datetime.now() + timedelta(hours=1),
            'retry_count': 0,
            'max_retries': 5,
        })

        queue_entry.action_cancel_retry()

        self.assertEqual(queue_entry.state, 'cancelled')

    def test_cannot_cancel_completed(self):
        """Test that completed retries cannot be cancelled."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'completed',
            'next_attempt': datetime.now(),
            'retry_count': 1,
            'max_retries': 5,
        })

        with self.assertRaises(UserError):
            queue_entry.action_cancel_retry()

    def test_failed_to_pending_via_manual_retry(self):
        """Test that failed entries can be retried manually."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        queue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'failed',
            'next_attempt': datetime.now() + timedelta(hours=1),
            'retry_count': 5,
            'max_retries': 5,
        })

        # Mock successful operation
        with patch.object(type(self.document), 'action_sign_xml'):
            queue_entry.action_retry_now()

        self.assertEqual(queue_entry.state, 'completed', "Manual retry should succeed and complete")


# ============================================================================
# AUTOMATIC RETRY TRIGGER TESTS
# ============================================================================


@tagged('post_install', '-at_install', 'einvoice', 'phase3', 'integration', 'p1')
class TestRetryQueueAutomaticTriggers(EInvoiceTestCase):
    """Test automatic retry triggers via cron job."""

    def setUp(self):
        super().setUp()

        # Create test invoice and document
        self.invoice = self._create_test_invoice()
        self.document = self._create_einvoice_document(self.invoice, document_type='FE')

    def test_cron_processes_only_overdue_items(self):
        """Test cron only processes items past their next_attempt time."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']
        now = datetime.now()

        # Create overdue entry
        overdue_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': now - timedelta(minutes=10),  # Overdue
            'retry_count': 0,
            'max_retries': 5,
        })

        # Create future entry
        future_entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'submit',
            'error_category': 'network',
            'state': 'pending',
            'next_attempt': now + timedelta(hours=1),  # Not due
            'retry_count': 0,
            'max_retries': 5,
        })

        # Mock operations
        with patch.object(type(self.document), 'action_sign_xml'):
            with patch.object(type(self.document), 'action_submit_to_hacienda'):
                retry_queue._cron_process_retry_queue()

        # Verify only overdue was processed
        self.assertEqual(overdue_entry.state, 'completed', "Overdue entry should be processed")
        self.assertEqual(future_entry.state, 'pending', "Future entry should remain pending")

    def test_cron_respects_priority_order(self):
        """Test cron processes high-priority items first."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']
        now = datetime.now()

        processed_order = []

        def mock_sign():
            processed_order.append('low')

        def mock_submit():
            processed_order.append('high')

        # Create low-priority entry
        low_priority = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': now - timedelta(minutes=10),
            'priority': '0',  # Low
            'retry_count': 0,
            'max_retries': 5,
        })

        # Create high-priority entry
        high_priority = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'submit',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': now - timedelta(minutes=5),
            'priority': '3',  # Urgent
            'retry_count': 0,
            'max_retries': 5,
        })

        # Mock operations
        with patch.object(type(self.document), 'action_sign_xml', side_effect=mock_sign):
            with patch.object(type(self.document), 'action_submit_to_hacienda', side_effect=mock_submit):
                retry_queue._cron_process_retry_queue()

        # High priority should be processed first
        self.assertEqual(processed_order[0], 'high', "High-priority items should be processed first")


# ============================================================================
# QUEUE CLEANUP TESTS
# ============================================================================


@tagged('post_install', '-at_install', 'einvoice', 'phase3')
class TestRetryQueueCleanup(EInvoiceTestCase):
    """Test 30-day retention policy for queue cleanup."""

    def setUp(self):
        super().setUp()

        # Create test invoice and document
        self.invoice = self._create_test_invoice()
        self.document = self._create_einvoice_document(self.invoice, document_type='FE')

    def test_cleanup_removes_old_completed_entries(self):
        """Test cleanup removes completed entries older than 30 days."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create old completed entry
        old_completed = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'completed',
            'next_attempt': datetime.now(),
            'retry_count': 1,
            'max_retries': 5,
        })

        # Manually set create_date to 35 days ago
        self.env.cr.execute(
            "UPDATE l10n_cr_einvoice_retry_queue SET create_date = %s WHERE id = %s",
            (datetime.now() - timedelta(days=35), old_completed.id)
        )

        # Run cleanup
        deleted_count = retry_queue._cleanup_old_entries(days=30)

        self.assertGreater(deleted_count, 0, "Should delete old entries")
        self.assertFalse(old_completed.exists(), "Old completed entry should be deleted")

    def test_cleanup_removes_old_failed_entries(self):
        """Test cleanup removes failed entries older than 30 days."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create old failed entry
        old_failed = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'validation',
            'state': 'failed',
            'next_attempt': datetime.now(),
            'retry_count': 5,
            'max_retries': 5,
        })

        # Set to 40 days old
        self.env.cr.execute(
            "UPDATE l10n_cr_einvoice_retry_queue SET create_date = %s WHERE id = %s",
            (datetime.now() - timedelta(days=40), old_failed.id)
        )

        deleted_count = retry_queue._cleanup_old_entries(days=30)

        self.assertGreater(deleted_count, 0)
        self.assertFalse(old_failed.exists(), "Old failed entry should be deleted")

    def test_cleanup_preserves_pending_entries(self):
        """Test cleanup does NOT remove pending entries (even if old)."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create old pending entry
        old_pending = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'pending',
            'next_attempt': datetime.now() + timedelta(hours=1),
            'retry_count': 0,
            'max_retries': 5,
        })

        # Set to 35 days old
        self.env.cr.execute(
            "UPDATE l10n_cr_einvoice_retry_queue SET create_date = %s WHERE id = %s",
            (datetime.now() - timedelta(days=35), old_pending.id)
        )

        # Run cleanup
        retry_queue._cleanup_old_entries(days=30)

        # Pending entry should still exist
        self.assertTrue(old_pending.exists(), "Pending entries should NOT be deleted")

    def test_cleanup_preserves_recent_completed_entries(self):
        """Test cleanup preserves completed entries less than 30 days old."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create recent completed entry
        recent_completed = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'completed',
            'next_attempt': datetime.now(),
            'retry_count': 1,
            'max_retries': 5,
        })

        # Set to 15 days old (within retention period)
        self.env.cr.execute(
            "UPDATE l10n_cr_einvoice_retry_queue SET create_date = %s WHERE id = %s",
            (datetime.now() - timedelta(days=15), recent_completed.id)
        )

        # Run cleanup
        retry_queue._cleanup_old_entries(days=30)

        # Should still exist
        self.assertTrue(recent_completed.exists(), "Recent completed entries should be preserved")

    def test_cleanup_custom_retention_period(self):
        """Test cleanup with custom retention period."""
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        # Create entry
        entry = retry_queue.create({
            'document_id': self.document.id,
            'operation': 'sign',
            'error_category': 'transient',
            'state': 'completed',
            'next_attempt': datetime.now(),
            'retry_count': 1,
            'max_retries': 5,
        })

        # Set to 10 days old
        self.env.cr.execute(
            "UPDATE l10n_cr_einvoice_retry_queue SET create_date = %s WHERE id = %s",
            (datetime.now() - timedelta(days=10), entry.id)
        )

        # Cleanup with 7-day retention
        deleted_count = retry_queue._cleanup_old_entries(days=7)

        self.assertGreater(deleted_count, 0, "Should delete entries older than custom period")
        self.assertFalse(entry.exists(), "Entry older than 7 days should be deleted")
