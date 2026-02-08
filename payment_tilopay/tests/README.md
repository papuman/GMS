# TiloPay Payment Module - Test Documentation

## Overview

This directory contains comprehensive test coverage for the TiloPay payment gateway integration module. All tests use **mocks** to simulate API interactions, requiring **NO real TiloPay credentials** to run.

## Test Architecture

### Test Files

```
tests/
├── __init__.py                              # Test suite initialization
├── common.py                                # Shared fixtures, factories, mocks
├── test_tilopay_api_client.py              # API client unit tests
├── test_tilopay_payment_provider.py        # Provider model unit tests
├── test_tilopay_payment_transaction.py     # Transaction model unit tests
├── test_tilopay_webhook.py                 # Webhook controller unit tests
├── test_tilopay_integration.py             # End-to-end integration tests
└── README.md                                # This file
```

### Test Organization

#### 1. **common.py** - Test Infrastructure
Provides shared testing utilities:

- **TiloPayTestCommon**: Base test class with fixtures
  - Pre-configured test company, partner, provider, invoice
  - Helper method `_create_test_transaction()`

- **TiloPayMockFactory**: Mock data generator
  - `create_payment_response()` - Mock payment creation
  - `create_status_response()` - Mock status queries
  - `create_webhook_payload()` - Mock webhook notifications
  - `create_error_response()` - Mock error responses
  - `create_sinpe_success()` - Complete SINPE scenario
  - `create_card_success()` - Complete card scenario
  - `create_payment_failure()` - Failure scenario

- **MockAPIClient**: Mock TiloPay API client
  - Simulates all API methods without HTTP calls
  - Tracks payments in memory
  - Helper methods to simulate success/failure

#### 2. **test_tilopay_api_client.py** - API Client Tests
Tests all API client functionality with mocked HTTP:

**Coverage:**
- Client initialization (sandbox/production modes)
- Authentication flow
- Payment creation
- Status queries (pending, approved, failed)
- Payment cancellation
- Payment refunds (full/partial)
- Webhook signature verification
- Error handling
- Complete payment scenarios (SINPE, card, failures)

**Key Tests:**
```python
test_api_client_initialization()
test_create_payment_success()
test_get_payment_status_approved()
test_refund_payment_full()
test_webhook_signature_verification_valid()
test_sinpe_payment_scenario()
test_card_payment_scenario()
test_payment_failure_scenario()
```

#### 3. **test_tilopay_payment_provider.py** - Provider Tests
Tests payment provider configuration and validation:

**Coverage:**
- Provider creation
- Credential validation
- Payment method configuration
- Webhook URL computation
- API client initialization
- Connection testing
- Security (credential groups)

**Key Tests:**
```python
test_provider_creation()
test_provider_credentials_required()
test_provider_payment_methods_validation()
test_provider_sinpe_only()
test_provider_cards_only()
test_webhook_url_computation()
test_get_api_client_success()
test_credentials_security()
```

#### 4. **test_tilopay_payment_transaction.py** - Transaction Tests
Tests payment transaction lifecycle:

**Coverage:**
- Transaction creation
- Payment initialization
- Webhook notification processing
- State transitions (pending → done/error/cancel)
- Duplicate webhook detection
- Payment ID validation
- Invoice integration
- Manual status refresh

**Key Tests:**
```python
test_transaction_creation()
test_create_payment_sets_pending_state()
test_webhook_notification_sinpe_success()
test_webhook_notification_card_success()
test_webhook_notification_failure()
test_webhook_duplicate_detection()
test_payment_id_mismatch_raises_error()
test_raw_response_storage()
```

#### 5. **test_tilopay_webhook.py** - Webhook Tests
Tests webhook controller endpoints:

**Coverage:**
- Endpoint accessibility
- Payload processing
- Security requirements
- Transaction lookup
- Error handling (always return 200)

**Key Tests:**
```python
test_webhook_endpoint_exists()
test_webhook_payload_processing()
test_webhook_signature_security()
test_return_url_with_reference()
test_webhook_finds_correct_transaction()
```

#### 6. **test_tilopay_integration.py** - Integration Tests
Tests complete end-to-end payment flows:

**Coverage:**
- SINPE payment complete journey
- Card payment complete journey
- Payment failure handling
- Payment cancellation
- Multiple concurrent payments
- Invoice-linked payments
- Webhook idempotency

**Key Tests:**
```python
test_sinpe_payment_complete_flow()
test_card_payment_complete_flow()
test_payment_failure_flow()
test_invoice_linked_payment_flow()
test_concurrent_payments_different_transactions()
test_webhook_idempotency()
```

## Running Tests

### Run All TiloPay Tests

```bash
# From Odoo root directory
odoo-bin -c odoo.conf --test-tags tilopay --stop-after-init
```

### Run Specific Test Categories

```bash
# API client tests only
odoo-bin -c odoo.conf --test-tags tilopay_api --stop-after-init

# Provider tests only
odoo-bin -c odoo.conf --test-tags tilopay_provider --stop-after-init

# Transaction tests only
odoo-bin -c odoo.conf --test-tags tilopay_transaction --stop-after-init

# Webhook tests only
odoo-bin -c odoo.conf --test-tags tilopay_webhook --stop-after-init

# Integration tests only
odoo-bin -c odoo.conf --test-tags tilopay_integration --stop-after-init
```

### Run from payment_tilopay directory

```bash
# Navigate to module directory
cd /path/to/payment_tilopay

# Run tests
python -m pytest tests/ -v  # If using pytest
# OR
odoo-bin --addons-path=/path/to/addons --test-tags tilopay --stop-after-init
```

## Test Tags Reference

| Tag | Description |
|-----|-------------|
| `tilopay` | All TiloPay module tests |
| `tilopay_api` | API client tests |
| `tilopay_provider` | Provider model tests |
| `tilopay_transaction` | Transaction model tests |
| `tilopay_webhook` | Webhook controller tests |
| `tilopay_integration` | Integration tests |
| `post_install` | Run after module installation |
| `-at_install` | Do not run during installation |

## Mock Data Examples

### Creating Mock Payment Response

```python
from odoo.addons.payment_tilopay.tests.common import TiloPayMockFactory

# Create payment response
payment = TiloPayMockFactory.create_payment_response(
    reference='INV-001',
    amount=50000,  # Amount in cents (₡50,000)
    currency='CRC'
)

# Result:
{
    'payment_id': 'pay_INV-001_...',
    'payment_url': 'https://sandbox.tilopay.com/checkout/...',
    'status': 'pending',
    'amount': 50000,
    'currency': 'CRC',
    'reference': 'INV-001',
    'created_at': '2025-12-28T20:00:00Z',
    'expires_at': '2025-12-29T20:00:00Z'
}
```

### Creating Mock Webhook Payload

```python
# SINPE success webhook
webhook = TiloPayMockFactory.create_webhook_payload(
    event='payment.completed',
    payment_id='pay_12345',
    reference='INV-001',
    status='approved',
    amount=50000,
    payment_method='sinpe',
    transaction_id='SINPE987654'
)

# Result:
{
    'event': 'payment.completed',
    'payment_id': 'pay_12345',
    'timestamp': '2025-12-28T20:00:00Z',
    'data': {
        'status': 'approved',
        'amount': 50000,
        'currency': 'CRC',
        'reference': 'INV-001',
        'payment_method': 'sinpe',
        'transaction_id': 'SINPE987654'
    }
}
```

### Creating Complete Payment Scenario

```python
# Complete SINPE success scenario (creation + status + webhook)
sinpe_scenario = TiloPayMockFactory.create_sinpe_success(
    reference='INV-001',
    amount=50000
)

# Access different parts:
creation_response = sinpe_scenario['creation']
status_response = sinpe_scenario['status']
webhook_payload = sinpe_scenario['webhook']
```

## Using MockAPIClient

```python
from unittest.mock import patch
from odoo.addons.payment_tilopay.tests.common import MockAPIClient

@patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
def test_my_payment(self, mock_client_class):
    # Setup mock client
    mock_client = MockAPIClient(
        api_key='test_key',
        api_user='test_user',
        api_password='test_pass',
        use_sandbox=True
    )
    mock_client_class.return_value = mock_client

    # Create payment through mock
    payment = mock_client.create_payment(
        amount=50000,
        currency='CRC',
        reference='TEST-001',
        customer_email='customer@example.com',
        payment_methods=['sinpe'],
        return_url='https://example.com/return',
        callback_url='https://example.com/webhook'
    )

    # Simulate payment success
    mock_client.simulate_payment_success(
        payment['payment_id'],
        payment_method='sinpe'
    )

    # Query status
    status = mock_client.get_payment_status(payment['payment_id'])
    assert status['status'] == 'approved'
```

## Test Coverage Summary

### Current Coverage

| Component | Tests | Coverage |
|-----------|-------|----------|
| API Client | 20+ | Authentication, payments, status, refunds, signatures |
| Provider Model | 20+ | Configuration, validation, helpers |
| Transaction Model | 20+ | Lifecycle, webhooks, state management |
| Webhook Controller | 8+ | Endpoints, security, processing |
| Integration | 12+ | Complete payment flows |
| **Total** | **80+** | **Comprehensive coverage** |

### Payment Scenarios Covered

- ✅ SINPE Móvil payment (success)
- ✅ Credit/Debit card payment (success)
- ✅ Payment failure (insufficient funds, declined)
- ✅ Payment cancellation by customer
- ✅ Payment pending (awaiting customer action)
- ✅ Webhook duplicate detection
- ✅ Webhook signature verification
- ✅ Invoice-linked payments
- ✅ Multiple concurrent payments
- ✅ Partial and full refunds

## CI/CD Integration

### GitHub Actions Example

```yaml
name: TiloPay Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install Odoo dependencies
        run: |
          pip install -r requirements.txt

      - name: Run TiloPay tests
        run: |
          odoo-bin -c odoo.conf \
            --test-tags tilopay \
            --stop-after-init \
            --log-level=test
```

### GitLab CI Example

```yaml
tilopay_tests:
  stage: test
  script:
    - odoo-bin -c odoo.conf --test-tags tilopay --stop-after-init
  only:
    - merge_requests
    - main
```

## Best Practices

### Writing New Tests

1. **Inherit from TiloPayTestCommon** for fixtures:
   ```python
   from odoo.addons.payment_tilopay.tests.common import TiloPayTestCommon

   class TestMyFeature(TiloPayTestCommon):
       def test_something(self):
           tx = self._create_test_transaction()
           # Test logic here
   ```

2. **Use TiloPayMockFactory** for mock data:
   ```python
   from odoo.addons.payment_tilopay.tests.common import TiloPayMockFactory

   webhook = TiloPayMockFactory.create_webhook_payload(...)
   ```

3. **Mock API client** for provider/transaction tests:
   ```python
   @patch('odoo.addons.payment_tilopay.models.tilopay_payment_provider.TiloPayAPIClient')
   def test_feature(self, mock_client_class):
       mock_client_class.return_value = MockAPIClient(...)
   ```

4. **Use descriptive test names**:
   ```python
   def test_webhook_notification_sinpe_success(self):
       """Test processing SINPE success webhook notification."""
   ```

5. **Tag tests appropriately**:
   ```python
   @tagged('post_install', '-at_install', 'tilopay', 'tilopay_feature')
   ```

### Test Isolation

- Each test starts with fresh database state (TransactionCase)
- Mocks prevent external API calls
- No dependencies on real credentials
- No dependencies on network connectivity

### Debugging Tests

```bash
# Run with verbose logging
odoo-bin -c odoo.conf --test-tags tilopay --log-level=test --stop-after-init

# Run single test method
odoo-bin -c odoo.conf --test-tags tilopay_api --stop-after-init \
  --test-file=addons/payment_tilopay/tests/test_tilopay_api_client.py::TestTiloPayAPIClient::test_create_payment_success
```

## Phase 3+ Preparation

These tests are designed to work in **skeleton mode** (current state) and will continue to work when the real API implementation is added in Phase 3+:

1. **Skeleton Mode** (Current):
   - API client returns placeholder data
   - Tests verify interface contracts
   - No real HTTP calls

2. **Phase 3** (Real API):
   - Tests can be run with mocks (default) or real API
   - Add `--test-enable-real-api` flag for live testing
   - Mocked tests remain for CI/CD

3. **Transition Strategy**:
   - Keep all existing mocked tests
   - Add optional real API integration tests
   - Mocks serve as API contract documentation

## Troubleshooting

### Common Issues

**Issue**: Tests fail with "Module not found"
```bash
# Solution: Ensure module is in addons path
odoo-bin --addons-path=/path/to/addons --test-tags tilopay --stop-after-init
```

**Issue**: Tests timeout
```bash
# Solution: Increase timeout (for slower systems)
odoo-bin -c odoo.conf --test-tags tilopay --test-timeout=300 --stop-after-init
```

**Issue**: Database errors
```bash
# Solution: Use test database
odoo-bin -c odoo.conf -d test_db --test-tags tilopay --stop-after-init
```

## Contributing

When adding new features to the TiloPay module:

1. ✅ Add corresponding tests
2. ✅ Use mocks for external dependencies
3. ✅ Update this README if adding new test files
4. ✅ Ensure all tests pass before committing
5. ✅ Tag tests appropriately

## Support

For questions about the test infrastructure:
- Review existing tests for examples
- Check common.py for available fixtures/mocks
- Consult Odoo testing documentation: https://www.odoo.com/documentation/17.0/developer/reference/backend/testing.html
