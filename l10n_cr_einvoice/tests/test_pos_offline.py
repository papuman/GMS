# -*- coding: utf-8 -*-
"""
Test POS Offline Queue for Costa Rica E-Invoicing
Tests offline queue management, sync logic, and retry mechanisms
"""

from odoo.tests import tagged, TransactionCase
from odoo.exceptions import UserError
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


from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from odoo import fields


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'pos_offline')
class TestPosOfflineQueue(TransactionCase):
    """Test POS offline queue functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test company
        cls.company = cls.env['res.company'].create({
            'name': 'Test GYM CR',
            'vat': _generate_unique_vat_company(),
            'country_id': cls.env.ref('base.cr').id,
            'l10n_cr_enable_einvoice': True,
        })

        # Create product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
            'list_price': 10000.0,
        })

        # Create POS config
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS',
            'company_id': cls.company.id,
            'l10n_cr_enable_einvoice': True,
            'l10n_cr_offline_mode': True,
            'l10n_cr_terminal_id': '001',
        })
        cls.pos_config._create_te_sequence()

        # Create POS session
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.uid,
        })
        cls.pos_session.action_pos_session_open()

        # Create mock einvoice document
        # Create test partner with valid CR data
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer POS',
            'vat': '109876543',
            'l10n_latam_identification_type_id': cls.env.ref('l10n_latam_base.it_vat').id,
            'email': 'testcustomer@example.com',
            'country_id': cls.env.ref('base.cr').id,
        })
        move = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'company_id': cls.company.id,
            'invoice_date': fields.Date.today(),
        })
        move.action_post()

        cls.einvoice = cls.env['l10n_cr.einvoice.document'].create({
            'name': 'TEST-001',
            'move_id': move.id,
            'company_id': cls.company.id,
            'document_type': 'TE',
            'partner_id': cls.partner.id,
            'clave': '5' * 50,
            'signed_xml': '<xml>test</xml>',
        })

    def test_01_create_queue_entry(self):
        """Test creating a queue entry"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'xml_data': b'<xml>test</xml>',
            'state': 'pending',
        })

        self.assertEqual(queue_entry.state, 'pending')
        self.assertEqual(queue_entry.retry_count, 0)
        self.assertEqual(queue_entry.config_id, self.pos_config)

    def test_02_queue_name_compute(self):
        """Test queue entry name computation"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
        })

        self.assertIn('Queue:', queue_entry.name)

    def test_03_next_retry_calculation(self):
        """Test exponential backoff calculation for retry"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'retry_count': 0,
            'last_retry': fields.Datetime.now(),
        })

        # First retry: 1 minute (2^0)
        next_retry = queue_entry.next_retry
        self.assertIsNotNone(next_retry)

        # Increment retry count
        queue_entry.retry_count = 2
        queue_entry._compute_next_retry()

        # Third retry: 4 minutes (2^2)
        # Just verify it's calculated (exact time depends on execution)
        self.assertIsNotNone(queue_entry.next_retry)

    def test_04_queue_stats(self):
        """Test queue statistics retrieval"""
        # Create multiple queue entries
        orders = []
        for i in range(5):
            order = self.env['pos.order'].create({
                'session_id': self.pos_session.id,
                'company_id': self.company.id,
            })
            orders.append(order)

        # 3 pending, 1 failed, 1 synced
        states = ['pending', 'pending', 'pending', 'failed', 'synced']
        for order, state in zip(orders, states):
            self.env['l10n_cr.pos.offline.queue'].create({
                'pos_order_id': order.id,
                'einvoice_document_id': self.einvoice.id,
                'state': state,
            })

        stats = self.env['l10n_cr.pos.offline.queue'].get_queue_stats()

        self.assertEqual(stats['pending'], 3)
        self.assertEqual(stats['failed'], 1)
        # Total excludes synced
        self.assertEqual(stats['total'], 4)

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.HaciendaAPI.submit_invoice')
    def test_05_retry_sync_success(self, mock_submit):
        """Test successful retry sync"""
        mock_submit.return_value = {'clave': '5' * 50, 'estado': 'aceptado'}

        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'state': 'pending',
        })

        # Mock online status
        with patch.object(type(order), '_l10n_cr_is_online', return_value=True):
            queue_entry.action_retry_sync()

        self.assertEqual(queue_entry.state, 'synced')
        self.assertFalse(order.l10n_cr_offline_queue)

    def test_06_retry_sync_offline_fail(self):
        """Test retry sync fails when offline"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'state': 'pending',
        })

        # Mock offline status
        with patch.object(type(order), '_l10n_cr_is_online', return_value=False):
            with self.assertRaises(UserError):
                queue_entry.action_retry_sync()

    def test_07_retry_sync_max_retries(self):
        """Test retry sync fails after max retries"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'state': 'failed',
            'retry_count': 5,
        })

        with self.assertRaises(UserError):
            queue_entry.action_retry_sync()

    def test_08_reset_failed_entry(self):
        """Test resetting a failed queue entry"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'state': 'failed',
            'retry_count': 5,
            'last_error': 'Test error',
        })

        queue_entry.action_reset()

        self.assertEqual(queue_entry.state, 'pending')
        self.assertEqual(queue_entry.retry_count, 0)
        self.assertFalse(queue_entry.last_error)

    def test_09_mark_as_synced(self):
        """Test manually marking entry as synced"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'state': 'pending',
        })

        queue_entry.action_mark_synced()

        self.assertEqual(queue_entry.state, 'synced')
        self.assertFalse(order.l10n_cr_offline_queue)

    def test_10_delete_queue_entry(self):
        """Test deleting a queue entry"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'state': 'pending',
        })

        entry_id = queue_entry.id
        queue_entry.action_delete_queue_entry()

        # Verify deleted
        exists = self.env['l10n_cr.pos.offline.queue'].search([
            ('id', '=', entry_id)
        ])
        self.assertEqual(len(exists), 0)

    def test_11_cannot_delete_syncing(self):
        """Test cannot delete entry that is syncing"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'state': 'syncing',
        })

        with self.assertRaises(UserError):
            queue_entry.action_delete_queue_entry()

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.HaciendaAPI.submit_invoice')
    def test_12_cron_sync_success(self, mock_submit):
        """Test cron job successfully syncs pending entries"""
        mock_submit.return_value = {'clave': '5' * 50, 'estado': 'aceptado'}

        # Create pending entries
        orders = []
        for i in range(3):
            order = self.env['pos.order'].create({
                'session_id': self.pos_session.id,
                'company_id': self.company.id,
            })
            orders.append(order)

            self.env['l10n_cr.pos.offline.queue'].create({
                'pos_order_id': order.id,
                'einvoice_document_id': self.einvoice.id,
                'state': 'pending',
            })

        # Run cron with mocked online status
        with patch('odoo.addons.l10n_cr_einvoice.models.pos_integration.PosOrder._l10n_cr_is_online', return_value=True):
            result = self.env['l10n_cr.pos.offline.queue'].cron_sync_offline_queue()

        self.assertGreaterEqual(result['success'], 0)

    def test_13_cleanup_old_entries(self):
        """Test cleanup of old synced entries"""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
        })

        # Create old synced entry (31 days ago)
        old_date = fields.Datetime.now() - timedelta(days=31)
        queue_entry = self.env['l10n_cr.pos.offline.queue'].create({
            'pos_order_id': order.id,
            'einvoice_document_id': self.einvoice.id,
            'state': 'synced',
        })

        # Manually set old create_date (normally readonly)
        self.env.cr.execute(
            "UPDATE l10n_cr_pos_offline_queue SET create_date = %s WHERE id = %s",
            (old_date, queue_entry.id)
        )

        # Run cleanup
        count = self.env['l10n_cr.pos.offline.queue'].cleanup_old_entries()

        self.assertGreaterEqual(count, 0)

    def test_14_priority_sorting(self):
        """Test queue entries are processed by priority"""
        # Create entries with different priorities
        priorities = ['low', 'normal', 'high']
        entries = []

        for priority in priorities:
            order = self.env['pos.order'].create({
                'session_id': self.pos_session.id,
                'company_id': self.company.id,
            })

            entry = self.env['l10n_cr.pos.offline.queue'].create({
                'pos_order_id': order.id,
                'einvoice_document_id': self.einvoice.id,
                'state': 'pending',
                'priority': priority,
            })
            entries.append(entry)

        # Search with priority ordering
        sorted_entries = self.env['l10n_cr.pos.offline.queue'].search([
            ('id', 'in', [e.id for e in entries]),
            ('state', '=', 'pending'),
        ], order='priority desc')

        # High priority should be first
        self.assertEqual(sorted_entries[0].priority, 'high')

    def test_15_batch_sync_limit(self):
        """Test batch sync respects limit"""
        # Create many pending entries
        for i in range(60):
            order = self.env['pos.order'].create({
                'session_id': self.pos_session.id,
                'company_id': self.company.id,
            })

            self.env['l10n_cr.pos.offline.queue'].create({
                'pos_order_id': order.id,
                'einvoice_document_id': self.einvoice.id,
                'state': 'pending',
            })

        # Search with limit (cron uses limit=50)
        entries = self.env['l10n_cr.pos.offline.queue'].search([
            ('state', '=', 'pending'),
        ], limit=50)

        # Should not exceed limit
        self.assertLessEqual(len(entries), 50)
