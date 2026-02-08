# Tilopay Payment Module for Odoo 19 - Complete Research

## Executive Summary

We need to **rewrite the existing skeleton `payment_tilopay` module** to follow Odoo 19's actual payment provider framework. The current skeleton has wrong API URLs, wrong endpoints, and doesn't use Odoo 19's standard patterns. This document contains everything needed to build a production-ready module.

---

## Part 1: Tilopay API (Reverse-Engineered from WooCommerce Plugin v3.1.2)

### Base URL

There is **ONE base URL** for both sandbox and production:
```
https://app.tilopay.com/api/v1/
```
The environment (test vs production) is determined by your credentials, NOT by different URLs.

**CRITICAL**: The existing skeleton's `SANDBOX_URL = "https://sandbox.tilopay.com/api/v1"` and `PRODUCTION_URL = "https://api.tilopay.com/api/v1"` are **WRONG**.

### Authentication (3 credentials required)

| Credential | Field | Test Value |
|---|---|---|
| API Key | `tpay_key` | `6609-5850-8330-8034-3464` |
| API User | `tpay_user` | `lSrT45` |
| API Password | `tpay_password` | `Zlb8H9` |

Our actual credentials are in `docs/TiloPayAccess/API.md`.

### API Endpoints

| Endpoint | Method | Purpose | Auth |
|---|---|---|---|
| `/api/v1/login` | POST | Get Bearer token (redirect flow) | Body: `{email, password}` |
| `/api/v1/loginSdk` | POST | Get SDK token (native form) | Body: `{apiuser, password, key}` |
| `/api/v1/processPayment` | POST | Create payment (redirect) | Bearer token |
| `/api/v1/processModification` | POST | Capture/refund/reverse | Bearer token |
| `/api/v1/processRecurrentPayment` | POST | Recurring payment with token | Bearer token |
| `/admin/processPaymentFAC` | POST | Native card payment (encrypted) | Key in body |

### Recommended Flow: REDIRECT (simplest, no PCI scope)

```
1. POST /api/v1/login
   Body: { "email": "<api_user>", "password": "<api_password>" }
   Response: { "access_token": "..." }

2. POST /api/v1/processPayment  (with Bearer token)
   Body: {
     "redirect": "https://our-odoo.com/payment/tilopay/return",
     "key": "<api_key>",
     "amount": 50000.00,
     "currency": "CRC",
     "billToFirstName": "John",
     "billToLastName": "Doe",
     "billToAddress": "San Jose",
     "billToEmail": "customer@email.com",
     "orderNumber": "TX-12345",
     "capture": 1,
     "subscription": 0,
     "platform": "odoo",
     "hashVersion": "V2",
     "returnData": "tilopay"
   }
   Response: { "type": 100, "url": "https://securepayment.tilopay.com/..." }

3. REDIRECT customer to response.url (Tilopay hosted payment page)

4. Customer returns to our redirect URL with query params:
   ?tpt=TPT-12345&OrderHash=abc...&order=TX-12345&code=1&auth=ABC123&description=Approved

5. VERIFY OrderHash using HMAC-SHA256

6. WEBHOOK also fires async POST to our webhook URL
```

### processPayment Response Types

| type | Meaning |
|---|---|
| `100` | Success -- `url` contains hosted payment page |
| `200` | Direct approval -- `url` contains redirect with results |
| `300` | License error |
| `400-404` | Various errors |

### Payment Return Query Parameters

| Parameter | Description |
|---|---|
| `tpt` | Tilopay Order ID |
| `OrderHash` | HMAC-SHA256 hash (64 chars) for verification |
| `order` | Merchant order number |
| `code` | `1` = approved, `Pending` = pending, other = failed |
| `auth` | Authorization code |
| `description` | Human-readable result |
| `crd` | Card token (for subscriptions) |
| `selected_method` | Payment method used (e.g., `SINPEMOVIL`) |
| `wp_cancel` | `yes` if user cancelled |

### HMAC-SHA256 Hash Verification (CRITICAL)

```python
import hmac
import hashlib
from urllib.parse import urlencode

# Construct hash key
hash_key = f"{tpay_order_id}|{api_key}|{api_password}"

# Construct params in exact order
params = {
    'api_Key': api_key,
    'api_user': api_user,
    'orderId': tpay_order_id,
    'external_orden_id': merchant_order_id,
    'amount': f"{amount:.2f}",
    'currency': currency,
    'responseCode': code,
    'auth': auth_code,
    'email': billing_email,
}

computed_hash = hmac.new(
    hash_key.encode('utf-8'),
    urlencode(params).encode('utf-8'),
    hashlib.sha256
).hexdigest()

is_valid = hmac.compare_digest(computed_hash, received_order_hash)
```

### Payment Modification (Capture/Refund/Reverse)

```
POST /api/v1/processModification  (with Bearer token)
Body: {
    "orderNumber": "12345",
    "key": "<api_key>",
    "amount": 50000.00,
    "type": "2",          // 1=Capture, 2=Refund, 3=Reversal
    "hashVersion": "V2",
    "platform": "odoo"
}
Response: { "ReasonCode": "1", "ReasonCodeDescription": "Approved" }
```

### Webhook Payload

```json
POST /payment/tilopay/webhook
{
    "orderNumber": "12345",
    "code": 1,
    "orderHash": "abcdef1234567890...",
    "tpt": "TPT-12345",
    "auth": "ABC123"
}
```

Same HMAC-SHA256 verification as redirect callback.

---

## Part 2: Odoo 19 Payment Provider Framework

### Required Module Structure

```
payment_tilopay/
  __init__.py                 # setup_provider / reset_payment_provider hooks
  __manifest__.py
  const.py                    # URLs, status mappings, sensitive keys
  controllers/
    __init__.py
    main.py                   # Return route + Webhook route
  models/
    __init__.py
    payment_provider.py       # Extends payment.provider
    payment_transaction.py    # Extends payment.transaction
  data/
    payment_provider_data.xml # Provider record + payment method links
  views/
    redirect_form.xml         # QWeb template for auto-submit form
    payment_provider_views.xml # Backend credential form
  static/
    description/icon.png      # Provider logo
```

### Key Odoo 19 Patterns (from actual source code)

#### `__init__.py` - Module Hooks
```python
from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider

def post_init_hook(env):
    setup_provider(env, 'tilopay')

def uninstall_hook(env):
    reset_payment_provider(env, 'tilopay')
```

#### `payment.provider` - Required Overrides
```python
class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('tilopay', 'TiloPay')],
        ondelete={'tilopay': 'set default'}
    )

    # Credential fields
    tilopay_api_key = fields.Char(string='API Key', required_if_provider='tilopay')
    tilopay_api_user = fields.Char(string='API User', required_if_provider='tilopay')
    tilopay_api_password = fields.Char(string='API Password', required_if_provider='tilopay')

    def _get_default_payment_method_codes(self):
        if self.code != 'tilopay':
            return super()._get_default_payment_method_codes()
        return {'card'}  # Links to payment.payment_method_card

    def _get_supported_currencies(self):
        if self.code != 'tilopay':
            return super()._get_supported_currencies()
        return None  # None = all currencies supported

    def _build_request_url(self, endpoint, **kwargs):
        return f'https://app.tilopay.com{endpoint}'

    def _build_request_headers(self, method, endpoint, payload, **kwargs):
        return {
            'Authorization': f'bearer {kwargs.get("access_token", "")}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _get_reset_values(self):
        if self.code != 'tilopay':
            return super()._get_reset_values()
        return {
            'tilopay_api_key': None,
            'tilopay_api_user': None,
            'tilopay_api_password': None,
        }
```

#### `payment.transaction` - Required Overrides

```python
class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """Create Tilopay checkout session, return redirect URL."""
        if self.provider_code != 'tilopay':
            return super()._get_specific_rendering_values(processing_values)
        # 1. Login to Tilopay API
        # 2. Call processPayment
        # 3. Return {'api_url': response['url'], ...}

    def _extract_reference(self, provider_code, payment_data):
        """Extract Odoo reference from Tilopay callback data."""
        if provider_code != 'tilopay':
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get('order')  # 'order' query param = our orderNumber

    def _apply_updates(self, payment_data):
        """Map Tilopay status codes to Odoo transaction states."""
        if self.provider_code != 'tilopay':
            return super()._apply_updates(payment_data)
        code = payment_data.get('code')
        if str(code) == '1':
            self.provider_reference = payment_data.get('tpt')
            self._set_done()
        elif code == 'Pending':
            self._set_pending()
        elif payment_data.get('wp_cancel') == 'yes':
            self._set_canceled()
        else:
            self._set_error(payment_data.get('description', 'Payment failed'))
```

#### Transaction State Machine

```
draft -> pending    (_set_pending)
draft -> done       (_set_done)
draft -> error      (_set_error)
draft -> cancel     (_set_canceled)
pending -> done     (_set_done)
pending -> authorized (_set_authorized)
pending -> error    (_set_error)
pending -> cancel   (_set_canceled)
authorized -> done  (_set_done)
authorized -> cancel (_set_canceled)
```

#### Controller Routes

```python
class TilopayController(http.Controller):

    @http.route('/payment/tilopay/return', type='http', methods=['GET'], auth='public')
    def tilopay_return(self, **data):
        """Customer returns from Tilopay hosted page."""
        # 1. Verify HMAC hash
        # 2. Find transaction by reference
        # 3. Call tx._process('tilopay', data)
        return request.redirect('/payment/status')

    @http.route('/payment/tilopay/webhook', type='http', auth='public',
                methods=['POST'], csrf=False)
    def tilopay_webhook(self, **data):
        """Async notification from Tilopay."""
        data = request.get_json_data()
        # 1. Verify HMAC hash
        # 2. Find transaction
        # 3. Call tx._process('tilopay', data)
        return ''  # 200 OK
```

#### Redirect Form Template

```xml
<template id="redirect_form">
    <form t-att-action="api_url" method="POST">
        <!-- Tilopay redirect - no hidden fields needed,
             the URL from processPayment IS the redirect target -->
    </form>
</template>
```

Actually, since `processPayment` returns a URL (not a form action), the redirect is simpler -- we just redirect the user directly to the URL via the controller or JS.

### Blueprint: payment_mercado_pago (closest Odoo 19 reference)

Files in the Mercado Pago module (Latin American gateway, similar to Tilopay):
```
__init__.py, __manifest__.py, const.py
controllers/__init__.py, controllers/onboarding.py, controllers/payment.py
models/__init__.py, models/payment_provider.py, models/payment_token.py, models/payment_transaction.py
data/payment_provider_data.xml
views/payment_form_templates.xml, payment_mercado_pago_templates.xml, payment_provider_views.xml
static/src/interactions/payment_form.js
tests/common.py, test_payment_provider.py, test_payment_transaction.py, test_processing_flows.py
```

---

## Part 3: Existing Competitors on Odoo Apps Store

| Module | Author | Price | LOC | License |
|---|---|---|---|---|
| `payment_tilopay` | ABL Solutions | $49 | 456 | Proprietary (ABL) |
| `bi_tilopay_payment_acquire` | BrowseInfo | $58 | 212 | OPL-1 |

Both are eCommerce-only (no POS), proprietary (can't modify), and use redirect flow.

---

## Part 4: What Our Skeleton Gets Wrong

| Issue | Skeleton Says | Reality |
|---|---|---|
| API URL (sandbox) | `https://sandbox.tilopay.com/api/v1` | `https://app.tilopay.com/api/v1/` |
| API URL (prod) | `https://api.tilopay.com/api/v1` | `https://app.tilopay.com/api/v1/` |
| Auth endpoint | `/auth/login` | `/api/v1/login` |
| Payment endpoint | `/payments/create` | `/api/v1/processPayment` |
| Status endpoint | `/payments/{id}/status` | Does not exist -- status via redirect/webhook |
| Webhook format | Custom JSON with `payment_id` | `{orderNumber, code, orderHash, tpt, auth}` |
| Hash verification | Vague HMAC-SHA256 | Specific: key=`tpt|api_key|api_password`, payload=url-encoded params |
| Module structure | Custom `TiloPayAPIClient` class | Should use Odoo's `_send_api_request` pattern |
| Init hooks | `post_init_hook` | Must call `setup_provider(env, 'tilopay')` |
| Dependencies | Includes `l10n_cr_einvoice` | Should only depend on `payment` + `account` |

---

## Part 5: SDK Details (for future native form integration)

SDK v2: `https://app.tilopay.com/sdk/v2/sdk_tpay.min.js`

| Method | Purpose |
|---|---|
| `Tilopay.Init(config)` | Initialize with token + payment details, returns available methods |
| `Tilopay.getCipherData()` | Encrypt card number + CVV for PCI-safe transmission |
| `Tilopay.getCardType()` | Detect visa/mastercard/amex from card number |
| `Tilopay.getSinpeMovil()` | Get SINPE Movil payment instructions (phone, code, amount) |
| `Tilopay.startPayment()` | Submit payment to Tilopay |
| `Tilopay.updateOptions({})` | Update payment parameters before submission |

ID Types for SINPE Movil (`typeDni`):
- 1 = Cedula Fisica (10 digits)
- 2 = Cedula Juridica (10 digits)
- 3 = Gobierno Central (10 digits)
- 4 = Institucion Autonoma (10 digits)
- 5 = Extranjero no Residente (20 chars)
- 6 = DIMEX (12 digits)
- 7 = DIDI (12 digits)

---

## Next Steps

1. **Rewrite `payment_tilopay` module** following Odoo 19's payment provider framework exactly
2. **Start with redirect flow** (simplest, no PCI scope)
3. **Copy patterns from `payment_mercado_pago`** -- it's the closest reference
4. **Remove `l10n_cr_einvoice` dependency** -- payment module should work independently
5. **Add native SDK form** as Phase 2 enhancement
