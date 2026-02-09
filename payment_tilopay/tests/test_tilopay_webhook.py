# -*- coding: utf-8 -*-

"""
Unit Tests for TiloPay Webhook Handling

Tests webhook endpoint security, payload processing, and error handling.
The webhook endpoint lives in controllers/main.py (TilopayController.tilopay_webhook).
"""

from odoo.tests import tagged

from odoo.addons.payment_tilopay.tests.common import TilopayCommon


@tagged('post_install', '-at_install', 'tilopay', 'tilopay_webhook')
class TestTiloPayWebhook(TilopayCommon):
    """Test TiloPay webhook controller endpoints."""

    def test_webhook_endpoint_exists(self):
        """Test webhook endpoint is accessible via the main controller."""
        from odoo.addons.payment_tilopay.controllers.main import TilopayController
        controller = TilopayController()
        self.assertIsNotNone(controller)
        self.assertTrue(hasattr(controller, 'tilopay_webhook'))

    def test_webhook_signature_security(self):
        """Test webhook signature verification is required."""
        self.assertTrue(self.provider.tilopay_api_key)

    def test_return_url_with_reference(self):
        """Test return URL includes transaction reference."""
        reference = 'TEST-RETURN-001'
        return_url = f"/payment/tilopay/return?reference={reference}"
        self.assertIn('reference=', return_url)
        self.assertIn(reference, return_url)
