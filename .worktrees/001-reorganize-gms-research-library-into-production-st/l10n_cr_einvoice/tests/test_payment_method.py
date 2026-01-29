# -*- coding: utf-8 -*-
"""
Unit tests for Payment Method model (Phase 1A)
Tests payment method catalog creation and validation
"""
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestPaymentMethod(TransactionCase):
    """Test l10n_cr.payment.method model."""

    def setUp(self):
        super(TestPaymentMethod, self).setUp()
        self.PaymentMethod = self.env['l10n_cr.payment.method']

    def test_payment_method_catalog_exists(self):
        """Test that all 5 payment methods are loaded."""
        methods = self.PaymentMethod.search([])
        self.assertGreaterEqual(len(methods), 5, "Should have at least 5 payment methods")

        # Check specific codes exist
        codes = methods.mapped('code')
        expected_codes = ['01', '02', '03', '04', '06']
        for code in expected_codes:
            self.assertIn(code, codes, f"Payment method code {code} should exist")

    def test_payment_method_efectivo_exists(self):
        """Test that Efectivo (01) payment method exists."""
        efectivo = self.env.ref('l10n_cr_einvoice.payment_method_efectivo', raise_if_not_found=False)
        self.assertTrue(efectivo, "Efectivo payment method should exist")
        self.assertEqual(efectivo.code, '01', "Efectivo should have code 01")
        self.assertFalse(efectivo.requires_transaction_id, "Efectivo should not require transaction ID")

    def test_payment_method_sinpe_exists(self):
        """Test that SINPE Móvil (06) payment method exists."""
        sinpe = self.env.ref('l10n_cr_einvoice.payment_method_sinpe', raise_if_not_found=False)
        self.assertTrue(sinpe, "SINPE Móvil payment method should exist")
        self.assertEqual(sinpe.code, '06', "SINPE Móvil should have code 06")
        self.assertTrue(sinpe.requires_transaction_id, "SINPE Móvil should require transaction ID")

    def test_payment_method_code_unique(self):
        """Test that payment method codes must be unique."""
        with self.assertRaises(Exception):
            # Try to create duplicate code
            self.PaymentMethod.create({
                'name': 'Duplicate',
                'code': '01',  # Already exists
            })

    def test_payment_method_code_validation(self):
        """Test that payment method code must be exactly 2 digits."""
        # Test invalid code length
        with self.assertRaises(ValidationError):
            self.PaymentMethod.create({
                'name': 'Invalid Code',
                'code': '1',  # Only 1 digit
            })

        with self.assertRaises(ValidationError):
            self.PaymentMethod.create({
                'name': 'Invalid Code',
                'code': '123',  # 3 digits
            })

        # Test non-numeric code
        with self.assertRaises(ValidationError):
            self.PaymentMethod.create({
                'name': 'Invalid Code',
                'code': 'AB',  # Not numeric
            })

    def test_payment_method_name_get(self):
        """Test that name_get returns code + name."""
        efectivo = self.env.ref('l10n_cr_einvoice.payment_method_efectivo')
        name = efectivo.name_get()[0][1]
        self.assertIn('01', name, "Name should contain code")
        self.assertIn('Efectivo', name, "Name should contain method name")

    def test_payment_method_active_filter(self):
        """Test that inactive payment methods can be filtered."""
        # Create a test payment method and deactivate it
        test_method = self.PaymentMethod.create({
            'name': 'Test Method',
            'code': '99',
            'active': True,
        })
        self.assertTrue(test_method.active)

        # Deactivate
        test_method.active = False
        self.assertFalse(test_method.active)

        # Search for active only
        active_methods = self.PaymentMethod.search([('active', '=', True)])
        self.assertNotIn(test_method, active_methods)

    def test_all_payment_methods_have_required_fields(self):
        """Test that all payment methods have name, code, and other required fields."""
        methods = self.PaymentMethod.search([])
        for method in methods:
            self.assertTrue(method.name, f"Method {method.code} should have a name")
            self.assertTrue(method.code, f"Method {method.id} should have a code")
            self.assertIsNotNone(method.requires_transaction_id,
                               f"Method {method.code} should have requires_transaction_id set")

    def test_sinpe_movil_badge_color(self):
        """Test that SINPE Móvil has purple badge color."""
        sinpe = self.env.ref('l10n_cr_einvoice.payment_method_sinpe')
        self.assertEqual(sinpe.badge_color, 'purple', "SINPE Móvil should have purple badge color")

    def test_efectivo_badge_color(self):
        """Test that Efectivo has success/green badge color."""
        efectivo = self.env.ref('l10n_cr_einvoice.payment_method_efectivo')
        self.assertEqual(efectivo.badge_color, 'success', "Efectivo should have success badge color")
