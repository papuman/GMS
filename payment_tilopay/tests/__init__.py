# -*- coding: utf-8 -*-

"""
TiloPay Payment Module - Test Suite

Comprehensive test coverage for TiloPay payment gateway integration.

Test Organization:
- common.py: Shared fixtures, factories, and mock utilities
- test_tilopay_api_client.py: Unit tests for API client
- test_tilopay_payment_provider.py: Unit tests for provider model
- test_tilopay_payment_transaction.py: Unit tests for transaction model
- test_tilopay_webhook.py: Unit tests for webhook controller
- test_tilopay_integration.py: Integration tests for complete payment flows

Running Tests:
    # Run all TiloPay tests
    odoo-bin -c odoo.conf --test-tags tilopay --stop-after-init

    # Run specific test class
    odoo-bin -c odoo.conf --test-tags tilopay_api --stop-after-init

    # Run integration tests only
    odoo-bin -c odoo.conf --test-tags tilopay_integration --stop-after-init

Test Tags:
- tilopay: All TiloPay tests
- tilopay_api: API client tests
- tilopay_provider: Provider model tests
- tilopay_transaction: Transaction model tests
- tilopay_webhook: Webhook controller tests
- tilopay_integration: Integration tests

Note: All tests use mocks to avoid requiring real TiloPay API credentials.
      Tests are designed to work in CI/CD environments without external dependencies.
"""

from . import common
from . import test_installation
from . import test_tilopay_api_client
from . import test_tilopay_payment_provider
from . import test_tilopay_payment_transaction
from . import test_tilopay_webhook
from . import test_tilopay_integration
