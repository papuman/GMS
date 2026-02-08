# TiloPay Payment Gateway - API Documentation

**Version:** 1.0.0
**Last Updated:** 2025-12-28
**Target Audience:** Developers integrating with or extending the TiloPay module

---

## Table of Contents

1. [Overview](#overview)
2. [API Client](#api-client)
3. [Payment Provider API](#payment-provider-api)
4. [Payment Transaction API](#payment-transaction-api)
5. [Invoice Integration API](#invoice-integration-api)
6. [Webhook API](#webhook-api)
7. [Data Structures](#data-structures)
8. [Error Handling](#error-handling)
9. [Code Examples](#code-examples)

---

## Overview

The TiloPay Payment Gateway module provides a comprehensive API for processing online payments in Odoo. This document describes the public and internal APIs available for developers.

### Module Structure

```
payment_tilopay/
├── models/
│   ├── tilopay_api_client.py          # Low-level API wrapper
│   ├── tilopay_payment_provider.py    # Provider configuration
│   ├── tilopay_payment_transaction.py # Transaction processing
│   └── account_move.py                 # Invoice integration
└── controllers/
    └── tilopay_webhook.py             # HTTP webhooks
```

### API Layers

1. **TiloPayAPIClient** - Low-level HTTP client for TiloPay REST API
2. **payment.provider** - Odoo model for provider configuration
3. **payment.transaction** - Odoo model for transaction management
4. **account.move** - Invoice extensions for payment integration
5. **HTTP Controllers** - Webhook endpoints

---

## API Client

### TiloPayAPIClient

Low-level Python client for TiloPay REST API communication.

**Location:** `models/tilopay_api_client.py`

#### Constructor

```python
client = TiloPayAPIClient(
    api_key: str,
    api_user: str,
    api_password: str,
    use_sandbox: bool = True
)
```

**Parameters:**
- `api_key` (str): TiloPay API Key from dashboard
- `api_user` (str): API username
- `api_password` (str): API password
- `use_sandbox` (bool): Use sandbox environment (default: True)

**Returns:** Authenticated TiloPayAPIClient instance

**Raises:**
- `requests.exceptions.RequestException`: Authentication failure
- `ValueError`: Invalid credentials

**Example:**
```python
from odoo.addons.payment_tilopay.models.tilopay_api_client import TiloPayAPIClient

client = TiloPayAPIClient(
    api_key='6609-5850-8330-8034-3464',
    api_user='lSrT45',
    api_password='Zlb8H9',
    use_sandbox=True
)
```

---

#### create_payment()

Create a new payment with TiloPay.

```python
response = client.create_payment(
    amount: int,
    currency: str,
    reference: str,
    customer_email: str,
    payment_methods: list,
    return_url: str,
    callback_url: str,
    **kwargs
)
```

**Parameters:**
- `amount` (int): Payment amount in minor units (cents for CRC)
- `currency` (str): ISO currency code ('CRC', 'USD')
- `reference` (str): Unique payment reference
- `customer_email` (str): Customer email address
- `payment_methods` (list): Allowed methods ['sinpe', 'card', 'yappy']
- `return_url` (str): Customer return URL after payment
- `callback_url` (str): Webhook notification URL
- `**kwargs`: Optional parameters
  - `customer_name` (str): Customer full name
  - `description` (str): Payment description
  - `metadata` (dict): Custom metadata

**Returns:**
```python
{
    'payment_id': 'pay_abc123',          # TiloPay payment ID
    'payment_url': 'https://...',        # Customer payment URL
    'status': 'pending',                 # Initial status
    'created_at': '2025-12-28T14:30:00Z' # ISO timestamp
}
```

**Raises:**
- `requests.exceptions.RequestException`: API request failed
- `ValueError`: Invalid parameters

**Example:**
```python
result = client.create_payment(
    amount=50000,  # ₡50,000 (in cents)
    currency='CRC',
    reference='INV-2025-001',
    customer_email='member@gym.com',
    payment_methods=['sinpe', 'card'],
    return_url='https://mygym.com/payment/return',
    callback_url='https://mygym.com/payment/webhook',
    customer_name='Juan Pérez',
    description='Monthly membership payment'
)

# Redirect customer to:
print(result['payment_url'])
```

---

#### get_payment_status()

Query current payment status.

```python
status = client.get_payment_status(payment_id: str)
```

**Parameters:**
- `payment_id` (str): TiloPay payment ID

**Returns:**
```python
{
    'status': 'approved',               # approved|pending|failed|cancelled
    'amount': 50000,                    # Amount in cents
    'currency': 'CRC',
    'payment_method': 'sinpe',          # Actual method used
    'transaction_id': '87654321',       # Bank transaction ID
    'completed_at': '2025-12-28T14:35:00Z',
    'error_code': None,                 # Error code if failed
    'error_message': None               # Error message if failed
}
```

**Example:**
```python
status = client.get_payment_status('pay_abc123')

if status['status'] == 'approved':
    print(f"Payment approved! Transaction ID: {status['transaction_id']}")
elif status['status'] == 'failed':
    print(f"Payment failed: {status['error_message']}")
```

---

#### cancel_payment()

Cancel a pending payment.

```python
result = client.cancel_payment(payment_id: str)
```

**Parameters:**
- `payment_id` (str): TiloPay payment ID

**Returns:**
```python
{
    'status': 'cancelled',
    'cancelled_at': '2025-12-28T14:40:00Z'
}
```

**Raises:**
- `ValueError`: Payment cannot be cancelled (already completed)

---

#### refund_payment()

Refund a completed payment.

```python
result = client.refund_payment(
    payment_id: str,
    amount: int = None,
    reason: str = None
)
```

**Parameters:**
- `payment_id` (str): TiloPay payment ID
- `amount` (int, optional): Refund amount (None = full refund)
- `reason` (str, optional): Refund reason

**Returns:**
```python
{
    'refund_id': 'ref_xyz789',
    'status': 'refunded',
    'amount': 50000,
    'refunded_at': '2025-12-28T15:00:00Z'
}
```

**Example:**
```python
# Full refund
result = client.refund_payment(
    payment_id='pay_abc123',
    reason='Customer request'
)

# Partial refund (₡25,000)
result = client.refund_payment(
    payment_id='pay_abc123',
    amount=25000,
    reason='Partial refund for damaged item'
)
```

---

#### verify_webhook_signature()

Verify webhook signature for security.

```python
is_valid = client.verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret_key: str
)
```

**Parameters:**
- `payload` (bytes): Raw webhook request body
- `signature` (str): Signature from webhook header
- `secret_key` (str): TiloPay secret key

**Returns:** `bool` - True if signature is valid

**Security Critical:**
ALWAYS verify webhook signatures before processing payment updates to prevent fraud.

**Example:**
```python
# In webhook controller
raw_payload = request.httprequest.get_data()
signature = request.httprequest.headers.get('X-TiloPay-Signature')

is_valid = client.verify_webhook_signature(
    payload=raw_payload,
    signature=signature,
    secret_key=provider.tilopay_secret_key
)

if not is_valid:
    _logger.error("SECURITY: Invalid webhook signature!")
    return {'status': 'error'}
```

---

## Payment Provider API

### payment.provider (TiloPay Extension)

Odoo model for TiloPay provider configuration.

**Model Name:** `payment.provider`
**Inherits:** `payment.provider`

#### Fields

**Credentials:**
- `tilopay_api_key` (Char): API Key
- `tilopay_api_user` (Char): API User
- `tilopay_api_password` (Char): API Password
- `tilopay_merchant_code` (Char): Merchant Code
- `tilopay_secret_key` (Char): Webhook Secret Key

**Configuration:**
- `tilopay_use_sandbox` (Boolean): Sandbox mode
- `tilopay_enable_sinpe` (Boolean): Enable SINPE Móvil
- `tilopay_enable_cards` (Boolean): Enable credit/debit cards
- `tilopay_enable_yappy` (Boolean): Enable Yappy (Panama)

**Computed:**
- `tilopay_webhook_url` (Char): Webhook URL for TiloPay dashboard

#### Methods

##### _tilopay_get_api_client()

Get authenticated API client instance.

```python
client = provider._tilopay_get_api_client()
```

**Returns:** `TiloPayAPIClient` instance

**Raises:**
- `UserError`: Provider is not TiloPay or credentials missing

**Example:**
```python
provider = self.env['payment.provider'].search([
    ('code', '=', 'tilopay'),
    ('state', '=', 'enabled')
], limit=1)

client = provider._tilopay_get_api_client()
result = client.create_payment(...)
```

---

##### action_test_tilopay_connection()

Test API connection (admin action button).

```python
provider.action_test_tilopay_connection()
```

**Returns:** Notification action

**Phase:** Phase 3 (currently skeleton)

---

##### _tilopay_get_enabled_payment_methods()

Get list of enabled payment methods.

```python
methods = provider._tilopay_get_enabled_payment_methods()
```

**Returns:** `list` - ['sinpe', 'card', 'yappy']

**Example:**
```python
methods = provider._tilopay_get_enabled_payment_methods()
# Returns: ['sinpe', 'card'] if both enabled
```

---

##### _tilopay_get_return_url()

Generate customer return URL.

```python
url = provider._tilopay_get_return_url(reference: str)
```

**Parameters:**
- `reference` (str): Transaction reference

**Returns:** `str` - Full return URL

**Example:**
```python
return_url = provider._tilopay_get_return_url('TX-001')
# Returns: 'https://example.com/payment/tilopay/return?reference=TX-001'
```

---

## Payment Transaction API

### payment.transaction (TiloPay Extension)

Odoo model for payment transaction processing.

**Model Name:** `payment.transaction`
**Inherits:** `payment.transaction`

#### Fields

**TiloPay Data:**
- `tilopay_payment_id` (Char): TiloPay payment ID
- `tilopay_payment_url` (Char): Customer payment URL
- `tilopay_payment_method` (Selection): Method used ('sinpe', 'card', 'yappy')
- `tilopay_transaction_id` (Char): Bank transaction ID (for SINPE)
- `tilopay_raw_response` (Text): Full API response (JSON)

**Webhook Tracking:**
- `tilopay_webhook_received` (Boolean): Webhook received flag
- `tilopay_webhook_count` (Integer): Number of webhooks received

**Computed:**
- `tilopay_is_pending` (Boolean): Transaction is pending

#### Methods

##### _tilopay_create_payment()

Initialize payment with TiloPay.

```python
transaction._tilopay_create_payment()
```

**Side Effects:**
- Creates payment via TiloPay API
- Stores payment_id and payment_url
- Updates transaction state to 'pending'

**Raises:**
- `UserError`: Payment creation failed

**Example:**
```python
# Create transaction
tx = self.env['payment.transaction'].create({
    'provider_id': provider.id,
    'amount': 50000.00,
    'currency_id': currency_crc.id,
    'reference': 'INV-2025-001',
    'partner_id': partner.id,
})

# Initialize with TiloPay
tx._tilopay_create_payment()

# Redirect customer
print(tx.tilopay_payment_url)
```

---

##### _tilopay_process_notification()

Process webhook notification.

```python
transaction._tilopay_process_notification(notification_data: dict)
```

**Parameters:**
```python
notification_data = {
    'event': 'payment.completed',
    'payment_id': 'pay_abc123',
    'data': {
        'status': 'approved',
        'amount': 50000,
        'currency': 'CRC',
        'payment_method': 'sinpe',
        'transaction_id': '87654321'
    }
}
```

**Side Effects:**
- Validates payment_id and amount
- Updates transaction state
- Stores payment method and transaction ID
- Triggers invoice confirmation if successful
- Increments webhook counter

**Raises:**
- `ValidationError`: Invalid notification data

**Example:**
```python
# In webhook controller
notification_data = request.jsonrequest
tx = self.env['payment.transaction'].sudo().search([
    ('tilopay_payment_id', '=', notification_data['payment_id'])
])

tx._tilopay_process_notification(notification_data)
```

---

##### action_tilopay_refresh_status()

Manually refresh payment status.

```python
transaction.action_tilopay_refresh_status()
```

**Returns:** Notification action

**Use Case:** When webhook delivery fails or is delayed

**Example:**
```python
# Admin manually refreshes status
tx.action_tilopay_refresh_status()
```

---

## Invoice Integration API

### account.move (TiloPay Extension)

Invoice model extension for online payments.

**Model Name:** `account.move`
**Inherits:** `account.move`

#### Fields

**Payment Integration:**
- `payment_transaction_ids` (One2many): Related payment transactions
- `has_tilopay_payment` (Boolean, computed): Has TiloPay transactions
- `tilopay_payment_url` (Char, computed): Active payment URL
- `can_pay_online` (Boolean, computed): Eligible for online payment

#### Methods

##### action_pay_online()

Create payment transaction and redirect to TiloPay.

```python
action = invoice.action_pay_online()
```

**Returns:** `dict` - Action to redirect to payment URL

**Business Rules:**
- Invoice must be customer invoice (`out_invoice`)
- Invoice must be posted
- Must have outstanding balance
- Customer must have email

**Raises:**
- `UserError`: Invoice cannot be paid online

**Example:**
```python
invoice = self.env['account.move'].browse(invoice_id)

if invoice.can_pay_online:
    action = invoice.action_pay_online()
    # Returns: {'type': 'ir.actions.act_url', 'url': '...', ...}
```

---

## Webhook API

### HTTP Endpoints

#### POST /payment/tilopay/webhook

Receive payment notifications from TiloPay.

**URL:** `https://your-domain.com/payment/tilopay/webhook`

**Method:** POST
**Auth:** Public (signature verified)
**Content-Type:** application/json

**Request Headers:**
```
X-TiloPay-Signature: sha256_signature_here
Content-Type: application/json
```

**Request Body:**
```json
{
    "event": "payment.completed",
    "payment_id": "pay_abc123",
    "timestamp": "2025-12-28T14:30:00Z",
    "data": {
        "status": "approved",
        "amount": 50000,
        "currency": "CRC",
        "reference": "INV-2025-001",
        "payment_method": "sinpe",
        "transaction_id": "87654321"
    },
    "signature": "computed_by_tilopay"
}
```

**Response:**
```json
{
    "status": "success"
}
```

**Status Codes:**
- `200 OK`: Webhook processed (even on error, to prevent retries)

**Security:**
- CSRF disabled (external webhook)
- Signature verification REQUIRED
- Always returns 200 (don't leak errors)

---

#### GET /payment/tilopay/return

Customer return page after payment.

**URL:** `https://your-domain.com/payment/tilopay/return?reference=TX-001`

**Method:** GET
**Auth:** Public

**Query Parameters:**
- `reference` (str, required): Transaction reference
- `status` (str, optional): Payment status from TiloPay redirect

**Response:** HTML page showing payment status

---

## Data Structures

### Payment Status Values

```python
STATUS_PENDING = 'pending'     # Payment created, awaiting completion
STATUS_APPROVED = 'approved'   # Payment successful
STATUS_FAILED = 'failed'       # Payment failed
STATUS_CANCELLED = 'cancelled' # Payment cancelled
```

### Payment Methods

```python
METHOD_SINPE = 'sinpe'   # SINPE Móvil (Costa Rica instant payments)
METHOD_CARD = 'card'     # Credit/Debit cards (Visa, MC, Amex)
METHOD_YAPPY = 'yappy'   # Yappy (Panama mobile payments)
```

### Event Types (Webhooks)

```python
EVENT_COMPLETED = 'payment.completed'   # Payment successful
EVENT_FAILED = 'payment.failed'         # Payment failed
EVENT_CANCELLED = 'payment.cancelled'   # Payment cancelled
EVENT_REFUNDED = 'payment.refunded'     # Payment refunded
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── requests.exceptions.RequestException  # Network/API errors
│   ├── ConnectionError                   # Cannot reach TiloPay
│   ├── Timeout                           # Request timeout
│   └── HTTPError                         # HTTP error response
├── ValueError                            # Invalid parameters
├── ValidationError (Odoo)                # Data validation errors
└── UserError (Odoo)                      # User-facing errors
```

### Error Response Format

TiloPay API errors follow this structure:

```json
{
    "error": {
        "code": "invalid_amount",
        "message": "Amount must be greater than zero",
        "field": "amount"
    }
}
```

### Best Practices

1. **Always log errors with context:**
```python
try:
    result = client.create_payment(...)
except requests.exceptions.RequestException as e:
    _logger.exception("Failed to create payment for reference %s", reference)
    raise UserError(_("Payment creation failed: %s") % str(e))
```

2. **Validate inputs before API calls:**
```python
if amount <= 0:
    raise ValueError("Amount must be positive")
if not customer_email:
    raise ValueError("Customer email is required")
```

3. **Handle webhook errors gracefully:**
```python
try:
    tx._tilopay_process_notification(data)
    return {'status': 'success'}
except Exception as e:
    _logger.exception("Webhook processing failed")
    # Still return 200 to prevent TiloPay retries
    return {'status': 'error', 'message': 'Internal error'}
```

---

## Code Examples

### Complete Payment Flow

```python
def process_invoice_payment(invoice_id):
    """Complete example of payment processing."""
    env = api.Environment(...)

    # 1. Get invoice
    invoice = env['account.move'].browse(invoice_id)

    if not invoice.can_pay_online:
        raise UserError("Invoice cannot be paid online")

    # 2. Get TiloPay provider
    provider = env['payment.provider'].search([
        ('code', '=', 'tilopay'),
        ('state', '=', 'enabled'),
    ], limit=1)

    # 3. Create transaction
    tx = env['payment.transaction'].create({
        'provider_id': provider.id,
        'amount': invoice.amount_residual,
        'currency_id': invoice.currency_id.id,
        'reference': invoice.name,
        'invoice_ids': [(6, 0, [invoice.id])],
        'partner_id': invoice.partner_id.id,
    })

    # 4. Initialize payment
    tx._tilopay_create_payment()

    # 5. Return payment URL
    return tx.tilopay_payment_url
```

### Custom Webhook Handler

```python
@http.route('/my/custom/webhook', type='json', auth='public', csrf=False)
def custom_webhook_handler(self, **kwargs):
    """Custom webhook handler with additional logic."""
    payload = request.jsonrequest

    # 1. Verify signature
    provider = request.env['payment.provider'].sudo().search([
        ('code', '=', 'tilopay')
    ], limit=1)

    client = provider._tilopay_get_api_client()
    raw_payload = request.httprequest.get_data()
    signature = request.httprequest.headers.get('X-TiloPay-Signature')

    if not client.verify_webhook_signature(raw_payload, signature, provider.tilopay_secret_key):
        _logger.error("Invalid signature")
        return {'status': 'error'}

    # 2. Find transaction
    tx = request.env['payment.transaction'].sudo().search([
        ('tilopay_payment_id', '=', payload['payment_id'])
    ])

    # 3. Process notification
    tx._tilopay_process_notification(payload)

    # 4. Custom logic (send SMS, update CRM, etc.)
    if payload['data']['status'] == 'approved':
        send_sms_notification(tx.partner_id.phone, "Payment received!")

    return {'status': 'success'}
```

### Batch Status Check

```python
def check_pending_payments():
    """Check status of all pending TiloPay transactions."""
    env = api.Environment(...)

    # Find pending transactions
    pending_txs = env['payment.transaction'].search([
        ('provider_code', '=', 'tilopay'),
        ('state', '=', 'pending'),
        ('tilopay_payment_id', '!=', False),
    ])

    provider = env['payment.provider'].search([
        ('code', '=', 'tilopay')
    ], limit=1)

    client = provider._tilopay_get_api_client()

    for tx in pending_txs:
        try:
            # Query status
            status = client.get_payment_status(tx.tilopay_payment_id)

            # Process as webhook
            notification_data = {
                'event': f'payment.{status["status"]}',
                'payment_id': tx.tilopay_payment_id,
                'data': status
            }

            tx._tilopay_process_notification(notification_data)

        except Exception as e:
            _logger.error("Failed to check status for %s: %s", tx.reference, e)
```

---

## Testing

### Unit Test Example

```python
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install', 'tilopay')
class TestTiloPayIntegration(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create provider
        self.provider = self.env['payment.provider'].create({
            'name': 'TiloPay Test',
            'code': 'tilopay',
            'state': 'test',
            'tilopay_api_key': 'test_key',
            'tilopay_api_user': 'test_user',
            'tilopay_api_password': 'test_pass',
            'tilopay_use_sandbox': True,
        })

    def test_payment_creation(self):
        """Test payment transaction creation."""
        tx = self.env['payment.transaction'].create({
            'provider_id': self.provider.id,
            'amount': 50000.00,
            'currency_id': self.env.ref('base.CRC').id,
            'reference': 'TEST-001',
        })

        self.assertEqual(tx.provider_code, 'tilopay')
        self.assertEqual(tx.state, 'draft')
```

---

## Migration Guide

### From v1.0 to v2.0 (Future)

When migrating to future versions:

1. **Check deprecated methods:**
   - Review changelog for deprecated APIs
   - Update code to use new methods

2. **Database migration:**
   - Run pre-upgrade scripts
   - Update module dependencies

3. **Test thoroughly:**
   - Run all unit tests
   - Test payment flow in sandbox
   - Verify webhook processing

---

## See Also

- [Architecture Documentation](ARCHITECTURE.md)
- [Security Documentation](SECURITY.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Developer Onboarding](DEVELOPER_ONBOARDING.md)
- [TiloPay Official API Docs](https://tilopay.com/documentacion)

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-28
**Maintained By:** GMS Development Team
