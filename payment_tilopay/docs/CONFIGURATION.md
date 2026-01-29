# TiloPay Payment Gateway - Configuration Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-28
**Target Audience:** System Administrators, Implementation Consultants

---

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Payment Provider Settings](#payment-provider-settings)
3. [Credential Configuration](#credential-configuration)
4. [Payment Method Configuration](#payment-method-configuration)
5. [Webhook Configuration](#webhook-configuration)
6. [Environment Configuration](#environment-configuration)
7. [Advanced Configuration](#advanced-configuration)
8. [Multi-Company Setup](#multi-company-setup)
9. [Configuration Validation](#configuration-validation)

---

## Configuration Overview

The TiloPay Payment Gateway module requires configuration at multiple levels:

```
┌─────────────────────────────────────┐
│  1. TiloPay Account Setup           │  (External)
│     - Merchant registration         │
│     - API credentials               │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  2. Odoo Provider Configuration     │  (System Admin)
│     - API credentials               │
│     - Payment methods               │
│     - Webhook URL                   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  3. Invoice Configuration           │  (Accountant)
│     - Payment terms                 │
│     - Default payment provider      │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  4. Portal Configuration            │  (Portal Manager)
│     - Payment page customization    │
│     - Member portal access          │
└─────────────────────────────────────┘
```

---

## Payment Provider Settings

### Accessing Provider Settings

**Navigation:**
```
Accounting > Configuration > Payment Providers
  → Find "TiloPay"
  → Click to open
```

**Required Permissions:**
- `base.group_system` (System Administrator)

### Provider Fields Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| **Name** | Char | ✅ | "TiloPay" | Display name |
| **Code** | Selection | ✅ | "tilopay" | Technical identifier (fixed) |
| **State** | Selection | ✅ | "disabled" | Provider status |
| **Company** | Many2one | ✅ | Current | Related company |
| **Logo** | Binary | ❌ | TiloPay logo | Provider logo image |

### State Values

```python
STATE_DISABLED = 'disabled'  # Provider not available
STATE_ENABLED = 'enabled'    # Live transactions
STATE_TEST = 'test'          # Test mode (uses test credentials)
```

**Recommendation:** Start with `test`, move to `enabled` after validation

---

## Credential Configuration

### Required Credentials

#### 1. API Key

**Field:** `tilopay_api_key`
**Format:** `XXXX-XXXX-XXXX-XXXX-XXXX`
**Example:** `6609-5850-8330-8034-3464`

**How to Obtain:**
1. Log in to TiloPay dashboard
2. Navigate to: Account > Checkout > API
3. Copy "API Key"

**Security:**
- Visible only to system administrators
- Never logged in plain text
- Stored encrypted in database

**Validation:**
- Must not be empty if provider enabled
- Format: 5 groups of 4 digits separated by hyphens

---

#### 2. API User

**Field:** `tilopay_api_user`
**Format:** Alphanumeric string
**Example:** `lSrT45`

**How to Obtain:**
1. Provided during TiloPay merchant onboarding
2. Or in: Account > Checkout > API

**Security:**
- Visible only to system administrators
- Used for authentication

**Validation:**
- Must not be empty if provider enabled
- Case-sensitive

---

#### 3. API Password

**Field:** `tilopay_api_password`
**Format:** Alphanumeric string
**Example:** `Zlb8H9`

**How to Obtain:**
1. Provided during TiloPay merchant onboarding
2. Or generate new in: Account > Checkout > API

**Security:**
- Visible only to system administrators
- Displayed as `******` in UI
- Never logged or exported
- Stored encrypted

**Validation:**
- Must not be empty if provider enabled
- Case-sensitive

---

#### 4. Merchant Code (Optional)

**Field:** `tilopay_merchant_code`
**Format:** Alphanumeric string
**Required:** ❌ Optional

**When Needed:**
- Some integrations require merchant identifier
- Used for advanced features
- Check with TiloPay support if needed

---

#### 5. Secret Key (Webhook Security)

**Field:** `tilopay_secret_key`
**Format:** Long alphanumeric string
**Required:** ✅ CRITICAL for security

**How to Obtain:**
1. TiloPay dashboard: Developer > Webhooks
2. Create or view webhook
3. Copy "Secret Key"

**Security:**
- CRITICAL for webhook signature verification
- Without this, fraudulent webhooks possible
- Visible only to system administrators

**Validation:**
- Should be at least 32 characters
- Must match secret key in TiloPay dashboard

**Warning:**
```
⚠️  NEVER process webhooks without signature verification!
⚠️  Missing or incorrect secret key = security vulnerability
```

---

### Credential Security Best Practices

1. **Environment Variables**
   ```bash
   # In server environment
   export TILOPAY_API_KEY="6609-5850-8330-8034-3464"
   export TILOPAY_API_USER="lSrT45"
   export TILOPAY_API_PASSWORD="Zlb8H9"
   export TILOPAY_SECRET_KEY="your_secret_key_here"
   ```

   ```python
   # In Odoo configuration
   import os
   tilopay_api_key = os.getenv('TILOPAY_API_KEY')
   ```

2. **Credential Rotation**
   - Rotate credentials every 90 days
   - Generate new credentials in TiloPay
   - Update in Odoo
   - Test connection
   - Revoke old credentials

3. **Access Control**
   - Only system administrators can view
   - Audit log all credential changes
   - Use 2FA for admin accounts

---

## Payment Method Configuration

### Available Payment Methods

#### 1. SINPE Móvil

**Field:** `tilopay_enable_sinpe`
**Type:** Boolean
**Default:** `True`

**Description:**
- Costa Rica instant payment system
- Bank-to-bank transfers
- Real-time confirmation
- No transaction fees for payer

**When to Enable:**
- Target market: Costa Rica
- Customer preference: Local payment
- Transaction size: Any amount

**Configuration:**
```python
tilopay_enable_sinpe = True
```

**User Experience:**
1. Customer selects SINPE on payment page
2. Enters phone number registered with SINPE
3. Receives push notification on phone
4. Approves payment with PIN
5. Instant confirmation

---

#### 2. Credit/Debit Cards

**Field:** `tilopay_enable_cards`
**Type:** Boolean
**Default:** `True`

**Description:**
- Visa, Mastercard, American Express
- International and local cards
- 3D Secure authentication
- Chargeback protection

**When to Enable:**
- International customers
- Customers without SINPE
- Subscription payments

**Configuration:**
```python
tilopay_enable_cards = True
```

**Supported Cards:**
- 💳 Visa
- 💳 Mastercard
- 💳 American Express
- 💳 Local Costa Rican cards

---

#### 3. Yappy (Optional)

**Field:** `tilopay_enable_yappy`
**Type:** Boolean
**Default:** `False`

**Description:**
- Panama mobile payment system
- Similar to SINPE for Panama
- Instant transfers

**When to Enable:**
- Target market: Panama
- Panamanian customers

**Configuration:**
```python
tilopay_enable_yappy = False  # Enable if needed
```

---

### Payment Method Selection Rules

**Validation:**
- At least one payment method must be enabled
- Constraint enforced at database level

```python
@api.constrains('tilopay_enable_sinpe', 'tilopay_enable_cards', 'tilopay_enable_yappy')
def _check_tilopay_payment_methods(self):
    if not (self.tilopay_enable_sinpe or
            self.tilopay_enable_cards or
            self.tilopay_enable_yappy):
        raise ValidationError("At least one payment method must be enabled")
```

**Recommended Configurations:**

**Costa Rica Gym (Standard):**
```python
tilopay_enable_sinpe = True   # Primary
tilopay_enable_cards = True   # Backup
tilopay_enable_yappy = False
```

**International Gym:**
```python
tilopay_enable_sinpe = True   # Local members
tilopay_enable_cards = True   # International
tilopay_enable_yappy = False
```

**Panama Branch:**
```python
tilopay_enable_sinpe = False
tilopay_enable_cards = True
tilopay_enable_yappy = True   # Local preference
```

---

## Webhook Configuration

### Webhook URL

**Field:** `tilopay_webhook_url` (Computed)
**Format:** `https://your-domain.com/payment/tilopay/webhook`
**Editable:** No (automatically computed)

**How It's Generated:**
```python
@api.depends('code')
def _compute_tilopay_webhook_url(self):
    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    for provider in self:
        if provider.code == 'tilopay':
            provider.tilopay_webhook_url = f"{base_url}/payment/tilopay/webhook"
```

**Setting Base URL:**
```
Settings > General Settings > System Parameters
  → web.base.url = "https://your-domain.com"
```

---

### Configuring Webhook in TiloPay Dashboard

**Step-by-Step:**

1. **Copy Webhook URL from Odoo**
   - Go to: Payment Provider > TiloPay
   - Copy value of "Webhook URL" field

2. **Log in to TiloPay Dashboard**
   - Navigate to: Developer > Webhooks

3. **Create New Webhook**
   - Click "Add Webhook"
   - Paste URL from step 1
   - Select environment (Sandbox or Production)

4. **Configure Events**
   Select these events:
   - ✅ `payment.completed`
   - ✅ `payment.failed`
   - ✅ `payment.cancelled`
   - ❌ `payment.pending` (optional)
   - ❌ `payment.refunded` (optional)

5. **Save and Test**
   - Save webhook configuration
   - Use TiloPay's test webhook feature
   - Verify Odoo receives notification

**Required Events:**
```json
{
  "events": [
    "payment.completed",  // Payment successful
    "payment.failed",     // Payment failed
    "payment.cancelled"   // Payment cancelled
  ]
}
```

---

### Webhook Security

**Signature Verification:**
- Always enabled (cannot be disabled)
- Uses HMAC-SHA256 algorithm
- Secret key from provider configuration

**Network Security:**
- HTTPS required (not HTTP)
- Valid SSL certificate required
- Firewall must allow inbound HTTPS

**Testing Webhook:**
```bash
# Test webhook is accessible
curl -X POST https://your-domain.com/payment/tilopay/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Should return: {"status": "error"}  (missing signature, but endpoint accessible)
```

---

## Environment Configuration

### Sandbox vs Production

**Field:** `tilopay_use_sandbox`
**Type:** Boolean
**Default:** `True`

**Sandbox Environment:**
```
✅ Use for: Testing, development, training
✅ API URL: https://sandbox.tilopay.com/api/v1
✅ Credentials: Test credentials from TiloPay
✅ Payments: Simulated (no real money)
✅ E-invoices: Test mode
```

**Production Environment:**
```
✅ Use for: Live transactions
✅ API URL: https://api.tilopay.com/api/v1
✅ Credentials: Production credentials
✅ Payments: Real money processed
✅ E-invoices: Sent to Hacienda
```

**Configuration Examples:**

**Development/Testing Server:**
```python
tilopay_use_sandbox = True
state = 'test'
```

**Production Server:**
```python
tilopay_use_sandbox = False
state = 'enabled'
```

**Warning:**
```
⚠️  NEVER use production credentials with sandbox=True
⚠️  NEVER use sandbox credentials with sandbox=False
```

---

### Environment Migration Checklist

**Moving from Sandbox to Production:**

- [ ] Obtain production credentials from TiloPay
- [ ] Update API Key, User, Password
- [ ] Update Secret Key
- [ ] Set `tilopay_use_sandbox = False`
- [ ] Update webhook URL in TiloPay to production URL
- [ ] Test connection with "Test Connection" button
- [ ] Create test payment with small amount
- [ ] Verify webhook delivery
- [ ] Verify e-invoice generation
- [ ] Set provider state to 'enabled'
- [ ] Monitor first 10 transactions closely

---

## Advanced Configuration

### Currency Configuration

**Default Currency:**
- TiloPay primarily processes CRC (Costa Rican Colón)
- USD also supported for some merchants

**Setting Default Currency:**
```
Accounting > Configuration > Accounting
  → Currency = "CRC" (₡)
```

**Multi-Currency:**
```python
# Transaction uses invoice currency
tx.currency_id = invoice.currency_id

# Converted to CRC if needed
amount_crc = tx.currency_id._convert(
    tx.amount,
    crc_currency,
    tx.company_id,
    tx.create_date
)
```

---

### Payment Journal Configuration

**Creating Payment Journal:**

1. Go to: Accounting > Configuration > Journals
2. Click "Create"
3. Configure:
   ```
   Name: TiloPay Payments
   Type: Bank
   Short Code: TILO
   Currency: CRC
   ```

**Link to Provider (Optional):**
```python
provider.journal_id = journal
```

---

### Email Template Configuration

**Payment Confirmation Email:**

```xml
<!-- data/payment_confirmation_email.xml -->
<odoo>
  <record id="payment_confirmation_email" model="mail.template">
    <field name="name">TiloPay Payment Confirmation</field>
    <field name="model_id" ref="payment.model_payment_transaction"/>
    <field name="subject">Payment Confirmation - {{ object.reference }}</field>
    <field name="body_html"><![CDATA[
      <p>Dear {{ object.partner_id.name }},</p>
      <p>Your payment has been received successfully.</p>
      <ul>
        <li>Reference: {{ object.reference }}</li>
        <li>Amount: {{ object.amount }} {{ object.currency_id.name }}</li>
        <li>Payment Method: {{ dict(object._fields['tilopay_payment_method'].selection).get(object.tilopay_payment_method) }}</li>
        <li>Date: {{ object.create_date }}</li>
      </ul>
      <p>Thank you for your payment!</p>
    ]]></field>
  </record>
</odoo>
```

---

### Portal Configuration

**Enabling Payment Portal:**

1. Install `portal` module
2. Create portal users for members
3. Grant invoice access
4. Payment button appears automatically

**Portal Access Control:**
```xml
<!-- security/ir.model.access.csv -->
payment.transaction,portal_payment_transaction,payment.model_payment_transaction,base.group_portal,1,0,0,0
```

**Customizing Portal Templates:**
```xml
<!-- views/portal_invoice_views.xml -->
<template id="portal_invoice_payment_button" inherit_id="account.portal_invoice_page">
  <xpath expr="//div[@id='invoice_content']" position="inside">
    <t t-if="invoice.can_pay_online">
      <a t-att-href="'/my/invoices/%s/pay' % invoice.id" class="btn btn-primary">
        Pay Now with TiloPay
      </a>
    </t>
  </xpath>
</template>
```

---

## Multi-Company Setup

### Separate Providers per Company

**Scenario:** Gym chain with multiple branches

**Configuration:**

**Company A:**
```python
provider_a = env['payment.provider'].create({
    'name': 'TiloPay - Branch A',
    'code': 'tilopay',
    'company_id': company_a.id,
    'tilopay_api_key': 'company_a_key',
    'tilopay_api_user': 'company_a_user',
    'tilopay_api_password': 'company_a_pass',
})
```

**Company B:**
```python
provider_b = env['payment.provider'].create({
    'name': 'TiloPay - Branch B',
    'code': 'tilopay',
    'company_id': company_b.id,
    'tilopay_api_key': 'company_b_key',
    'tilopay_api_user': 'company_b_user',
    'tilopay_api_password': 'company_b_pass',
})
```

**Access Control:**
- Users see only their company's provider
- Transactions filtered by company
- Webhooks routed to correct company

---

### Shared Provider (Not Recommended)

**Configuration:**
```python
provider = env['payment.provider'].create({
    'name': 'TiloPay - Shared',
    'code': 'tilopay',
    'company_id': False,  # Shared across companies
})
```

**Implications:**
- All companies use same credentials
- Cannot track revenue by company
- Webhook routing complex
- Not recommended for production

---

## Configuration Validation

### Manual Validation

**Test Connection Button:**
1. Go to: Payment Provider > TiloPay
2. Fill in all credentials
3. Click "Test Connection"
4. Verify success message

**Expected Behavior:**
```
✅ Success: "Connection test successful"
❌ Failure: "Connection test failed: [error message]"
```

---

### Automated Validation

**Run Health Check:**
```python
# In Odoo shell
def validate_configuration():
    """Validate TiloPay configuration."""
    provider = env['payment.provider'].search([('code', '=', 'tilopay')])

    checks = {
        'Provider exists': bool(provider),
        'API Key set': bool(provider.tilopay_api_key),
        'API User set': bool(provider.tilopay_api_user),
        'API Password set': bool(provider.tilopay_api_password),
        'Secret Key set': bool(provider.tilopay_secret_key),
        'At least one payment method': (
            provider.tilopay_enable_sinpe or
            provider.tilopay_enable_cards or
            provider.tilopay_enable_yappy
        ),
        'Webhook URL set': bool(provider.tilopay_webhook_url),
        'Provider enabled': provider.state == 'enabled',
    }

    print("\n=== TiloPay Configuration Validation ===\n")
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")

    all_passed = all(checks.values())
    print(f"\n{'✅ All checks passed!' if all_passed else '❌ Some checks failed'}\n")

    return all_passed

validate_configuration()
```

---

### Pre-Production Checklist

Before going live:

**Credentials:**
- [ ] Production credentials obtained
- [ ] Credentials tested with "Test Connection"
- [ ] Secret key configured
- [ ] Sandbox mode disabled

**Configuration:**
- [ ] At least one payment method enabled
- [ ] Webhook URL configured in TiloPay
- [ ] Provider state set to "enabled"
- [ ] Base URL is production URL (not localhost)

**Testing:**
- [ ] Test payment created successfully
- [ ] Webhook received and processed
- [ ] Invoice marked as paid
- [ ] E-invoice generated
- [ ] Customer email sent

**Security:**
- [ ] HTTPS enabled
- [ ] Valid SSL certificate
- [ ] Firewall configured
- [ ] Access control validated

**Monitoring:**
- [ ] Logging enabled
- [ ] Alert notifications configured
- [ ] Backup strategy in place

---

## Configuration Templates

### Template 1: Basic Setup (Small Gym)

```python
{
    'name': 'TiloPay',
    'code': 'tilopay',
    'state': 'enabled',
    'tilopay_api_key': 'YOUR_KEY',
    'tilopay_api_user': 'YOUR_USER',
    'tilopay_api_password': 'YOUR_PASS',
    'tilopay_secret_key': 'YOUR_SECRET',
    'tilopay_use_sandbox': False,
    'tilopay_enable_sinpe': True,
    'tilopay_enable_cards': True,
    'tilopay_enable_yappy': False,
}
```

### Template 2: International Gym

```python
{
    'name': 'TiloPay International',
    'code': 'tilopay',
    'state': 'enabled',
    'tilopay_api_key': 'YOUR_KEY',
    'tilopay_api_user': 'YOUR_USER',
    'tilopay_api_password': 'YOUR_PASS',
    'tilopay_secret_key': 'YOUR_SECRET',
    'tilopay_use_sandbox': False,
    'tilopay_enable_sinpe': True,   # For local members
    'tilopay_enable_cards': True,   # Primary for international
    'tilopay_enable_yappy': False,
}
```

### Template 3: Development/Testing

```python
{
    'name': 'TiloPay Test',
    'code': 'tilopay',
    'state': 'test',
    'tilopay_api_key': '6609-5850-8330-8034-3464',
    'tilopay_api_user': 'lSrT45',
    'tilopay_api_password': 'Zlb8H9',
    'tilopay_secret_key': 'test_secret_key',
    'tilopay_use_sandbox': True,
    'tilopay_enable_sinpe': True,
    'tilopay_enable_cards': True,
    'tilopay_enable_yappy': False,
}
```

---

## See Also

- [API Documentation](API_DOCUMENTATION.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Security Documentation](SECURITY.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Developer Onboarding](DEVELOPER_ONBOARDING.md)

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-28
**Maintained By:** GMS Implementation Team
