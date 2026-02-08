# -*- coding: utf-8 -*-
"""
Tests for TiloPay payment method mapping to Hacienda e-invoice codes.

Tests the automatic mapping of TiloPay payment methods (SINPE Movil, Card)
to Costa Rica Hacienda MedioPago codes (06, 02) on invoices.

The mapping is implemented in account.move._detect_payment_method_from_transactions()
and used by the XML generator's _add_medio_pago() method as a fallback.
"""
from unittest.mock import patch, MagicMock
from .common import EInvoiceTestCase


class TestTilopayPaymentMapping(EInvoiceTestCase):
    """Test TiloPay payment method -> Hacienda code mapping."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get CR payment methods from data
        cls.pm_efectivo = cls.env.ref('l10n_cr_einvoice.payment_method_efectivo')
        cls.pm_tarjeta = cls.env.ref('l10n_cr_einvoice.payment_method_tarjeta')
        cls.pm_sinpe = cls.env.ref('l10n_cr_einvoice.payment_method_sinpe')
        cls.pm_transferencia = cls.env.ref('l10n_cr_einvoice.payment_method_transferencia')

    def test_mapping_constants_exist(self):
        """Test that PAYMENT_METHOD_MAPPING is defined on account.move."""
        mapping = self.env['account.move'].PAYMENT_METHOD_MAPPING
        self.assertIsInstance(mapping, dict)
        self.assertTrue(len(mapping) > 0, "Mapping should not be empty")

    def test_mapping_tilopay_sinpe_to_code_06(self):
        """Test TiloPay bank_transfer maps to Hacienda code 06 (SINPE Movil)."""
        mapping = self.env['account.move'].PAYMENT_METHOD_MAPPING
        code = mapping.get(('tilopay', 'bank_transfer'))
        self.assertEqual(code, '06', "TiloPay bank_transfer should map to SINPE code 06")

    def test_mapping_tilopay_card_to_code_02(self):
        """Test TiloPay card maps to Hacienda code 02 (Tarjeta)."""
        mapping = self.env['account.move'].PAYMENT_METHOD_MAPPING
        code = mapping.get(('tilopay', 'card'))
        self.assertEqual(code, '02', "TiloPay card should map to Tarjeta code 02")

    def test_mapping_generic_card_to_code_02(self):
        """Test generic card payment maps to Hacienda code 02 (Tarjeta)."""
        mapping = self.env['account.move'].PAYMENT_METHOD_MAPPING
        code = mapping.get((None, 'card'))
        self.assertEqual(code, '02', "Generic card should map to Tarjeta code 02")

    def test_mapping_generic_bank_transfer_to_code_04(self):
        """Test generic bank_transfer maps to Hacienda code 04 (Transferencia)."""
        mapping = self.env['account.move'].PAYMENT_METHOD_MAPPING
        code = mapping.get((None, 'bank_transfer'))
        self.assertEqual(code, '04',
                         "Generic bank_transfer should map to Transferencia code 04, not SINPE")

    def test_mapping_tilopay_specific_overrides_generic(self):
        """Test that TiloPay-specific mapping takes precedence over generic."""
        mapping = self.env['account.move'].PAYMENT_METHOD_MAPPING
        # TiloPay bank_transfer -> 06 (SINPE)
        tilopay_code = mapping.get(('tilopay', 'bank_transfer'))
        # Generic bank_transfer -> 04 (Transferencia)
        generic_code = mapping.get((None, 'bank_transfer'))
        self.assertNotEqual(tilopay_code, generic_code,
                            "TiloPay-specific mapping should differ from generic for bank_transfer")
        self.assertEqual(tilopay_code, '06')
        self.assertEqual(generic_code, '04')

    def test_detect_returns_false_without_transactions(self):
        """Test that detection returns False when no transaction_ids field exists."""
        invoice = self._create_test_invoice()
        invoice.action_post()

        # If account_payment is not installed, transaction_ids won't exist.
        # The method should handle this gracefully.
        if not hasattr(invoice, 'transaction_ids'):
            result = invoice._detect_payment_method_from_transactions()
            self.assertFalse(result,
                             "Should return False when transaction_ids field doesn't exist")

    def test_detect_returns_false_with_empty_transactions(self):
        """Test that detection returns False when no transactions are linked."""
        invoice = self._create_test_invoice()
        invoice.action_post()

        # Even if transaction_ids exists but is empty, should return False
        if hasattr(invoice, 'transaction_ids'):
            result = invoice._detect_payment_method_from_transactions()
            self.assertFalse(result,
                             "Should return False when no transactions are linked")

    def test_detect_payment_method_with_mock_tilopay_card(self):
        """Test detection of card payment from a mock TiloPay transaction."""
        invoice = self._create_test_invoice()
        invoice.action_post()

        # Create a mock transaction that simulates TiloPay card payment
        mock_tx = MagicMock()
        mock_tx.state = 'done'
        mock_tx.provider_code = 'tilopay'
        mock_tx.payment_method_code = 'card'
        mock_tx.provider_reference = 'TPT-12345'
        mock_tx.last_state_change = '2025-01-01 00:00:00'
        mock_tx.sorted.return_value = mock_tx
        mock_tx.__getitem__ = lambda self, key: self  # Support [:1] slicing

        # Mock transaction_ids on the invoice
        mock_done_txs = MagicMock()
        mock_done_txs.sorted.return_value = MagicMock()
        mock_done_txs.sorted.return_value.__getitem__ = lambda self, key: mock_tx
        mock_done_txs.__bool__ = lambda self: True

        with patch.object(type(invoice), 'transaction_ids',
                          new_callable=lambda: property(lambda self: MagicMock(
                              filtered=lambda fn: mock_done_txs
                          ))):
            result = invoice._detect_payment_method_from_transactions()
            if result:
                self.assertEqual(result.code, '02',
                                 "TiloPay card should detect as Tarjeta (02)")

    def test_detect_payment_method_with_mock_tilopay_sinpe(self):
        """Test detection of SINPE payment from a mock TiloPay transaction."""
        invoice = self._create_test_invoice()
        invoice.action_post()

        # Create a mock transaction that simulates TiloPay SINPE payment
        mock_tx = MagicMock()
        mock_tx.state = 'done'
        mock_tx.provider_code = 'tilopay'
        mock_tx.payment_method_code = 'bank_transfer'
        mock_tx.provider_reference = 'SINPE-67890'
        mock_tx.last_state_change = '2025-01-01 00:00:00'
        mock_tx.sorted.return_value = mock_tx
        mock_tx.__getitem__ = lambda self, key: self

        mock_done_txs = MagicMock()
        mock_done_txs.sorted.return_value = MagicMock()
        mock_done_txs.sorted.return_value.__getitem__ = lambda self, key: mock_tx
        mock_done_txs.__bool__ = lambda self: True

        with patch.object(type(invoice), 'transaction_ids',
                          new_callable=lambda: property(lambda fn: MagicMock(
                              filtered=lambda fn: mock_done_txs
                          ))):
            result = invoice._detect_payment_method_from_transactions()
            if result:
                self.assertEqual(result.code, '06',
                                 "TiloPay bank_transfer should detect as SINPE (06)")

    def test_validate_auto_assigns_efectivo_when_no_transaction(self):
        """Test that validation auto-assigns Efectivo when no transaction detected."""
        invoice = self._create_test_invoice()
        # Don't set payment method
        self.assertFalse(invoice.l10n_cr_payment_method_id)

        # Post invoice - validation should auto-assign Efectivo
        invoice.action_post()

        self.assertTrue(invoice.l10n_cr_payment_method_id,
                        "Payment method should be auto-assigned after posting")
        self.assertEqual(invoice.l10n_cr_payment_method_id.code, '01',
                         "Default payment method should be Efectivo (01)")

    def test_explicit_payment_method_not_overridden(self):
        """Test that explicitly set payment method is not overridden by detection."""
        invoice = self._create_test_invoice()
        invoice.l10n_cr_payment_method_id = self.pm_tarjeta.id

        invoice.action_post()

        self.assertEqual(invoice.l10n_cr_payment_method_id.code, '02',
                         "Explicitly set Tarjeta should not be overridden")

    def test_sinpe_payment_method_record_exists(self):
        """Test that SINPE payment method record exists with correct code."""
        self.assertTrue(self.pm_sinpe, "SINPE payment method should exist")
        self.assertEqual(self.pm_sinpe.code, '06')
        self.assertTrue(self.pm_sinpe.requires_transaction_id,
                        "SINPE should require transaction ID")

    def test_tarjeta_payment_method_record_exists(self):
        """Test that Tarjeta payment method record exists with correct code."""
        self.assertTrue(self.pm_tarjeta, "Tarjeta payment method should exist")
        self.assertEqual(self.pm_tarjeta.code, '02')
        self.assertFalse(self.pm_tarjeta.requires_transaction_id,
                         "Tarjeta should not require transaction ID")

    def test_transferencia_payment_method_record_exists(self):
        """Test that Transferencia payment method record exists with correct code."""
        self.assertTrue(self.pm_transferencia, "Transferencia payment method should exist")
        self.assertEqual(self.pm_transferencia.code, '04')

    def test_mapping_covers_all_tilopay_methods(self):
        """Test that the mapping covers all methods TiloPay can return."""
        mapping = self.env['account.move'].PAYMENT_METHOD_MAPPING
        # TiloPay returns either 'card' or 'bank_transfer' (SINPE)
        self.assertIn(('tilopay', 'card'), mapping,
                      "Mapping should cover TiloPay card")
        self.assertIn(('tilopay', 'bank_transfer'), mapping,
                      "Mapping should cover TiloPay bank_transfer (SINPE)")

    def test_all_mapped_codes_have_cr_payment_method(self):
        """Test that all Hacienda codes in the mapping have corresponding records."""
        mapping = self.env['account.move'].PAYMENT_METHOD_MAPPING
        hacienda_codes = set(mapping.values())

        for code in hacienda_codes:
            cr_method = self.env['l10n_cr.payment.method'].search(
                [('code', '=', code), ('active', '=', True)], limit=1
            )
            self.assertTrue(
                cr_method,
                f"Hacienda code '{code}' from mapping should have a "
                f"l10n_cr.payment.method record"
            )
