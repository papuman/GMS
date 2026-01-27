# -*- coding: utf-8 -*-
"""
Phase 3 Testing: Retry Queue

Tests for the intelligent retry queue system that automatically
retries failed e-invoice operations with exponential backoff.
"""
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo import fields

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'einvoice', 'phase3')
class TestPhase3RetryQueue(TransactionCase):
    """Test retry queue functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test company
        cls.company = cls.env['res.company'].create({
            'name': 'Test Company CR',
            'vat': '1234567890',
            'country_id': cls.env.ref('base.cr').id,
        })

        # Create test partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'vat': '0987654321',
            'country_id': cls.env.ref('base.cr').id,
        })

        # Create test invoice
        cls.invoice = cls.env['account.move'].create({
            'partner_id': cls.partner.id,
            'move_type': 'out_invoice',
            'company_id': cls.company.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Product',
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })

        # Create test document
        cls.document = cls.env['l10n_cr.einvoice.document'].create({
            'move_id': cls.invoice.id,
            'company_id': cls.company.id,
            'document_type': 'FE',
            'state': 'draft',
        })

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
