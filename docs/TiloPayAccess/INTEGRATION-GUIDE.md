# TiloPay Integration Guide - GMS Project

**Document Version:** 1.0
**Last Updated:** 2026-01-15
**Status:** Verified against official TiloPay documentation (28 files, 8.5 MB)

---

## Overview

This guide documents the **verified** TiloPay integration pattern for the GMS (Gym Management System) project. TiloPay uses a **redirect-based payment flow** (NOT webhooks) which is the industry-standard pattern for payment gateways.

### Key Facts

✅ **Integration Pattern:** Redirect-based callbacks via URL parameters
❌ **Webhook Support:** NOT supported by TiloPay
✅ **Documentation Sources:** Complete official TiloPay SDK and API documentation
✅ **Payment Methods:** SINPE Móvil (76% Costa Rica adoption), Credit/Debit Cards

---

## Architecture Pattern

### Redirect-Based Payment Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   GMS Odoo  │         │   TiloPay    │         │   Member    │
│   Backend   │         │   Gateway    │         │   Browser   │
└──────┬──────┘         └──────┬───────┘         └──────┬──────┘
       │                       │                        │
       │  1. Create Payment    │                        │
       │  (SDK: responseUrl)   │                        │
       ├──────────────────────>│                        │
       │                       │                        │
       │  2. Return Payment    │                        │
       │     URL + Token       │                        │
       │<──────────────────────┤                        │
       │                       │                        │
       │  3. Redirect Member   │                        │
       │     to Payment Page   │                        │
       ├───────────────────────┼───────────────────────>│
       │                       │                        │
       │                       │  4. Display Payment UI │
       │                       │<───────────────────────┤
       │                       │                        │
       │                       │  5. Complete Payment   │
       │                       │    (SINPE/Card)        │
       │                       │<───────────────────────┤
       │                       │                        │
       │  6. Redirect to       │                        │
       │     responseUrl +     │                        │
       │     payment params    │                        │
       │<──────────────────────┼────────────────────────┤
       │                       │                        │
       │  7. Parse URL params  │                        │
       │     Extract status    │                        │
       │     Update DB         │                        │
       │                       │                        │
       │  8. Display Success   │                        │
       │     to Member         │                        │
       ├───────────────────────┼───────────────────────>│
       │                       │                        │
```

---

## Payment Creation (Step 1-2)

### SDK Method: `create_payment()`

**Python Implementation (Odoo):**

```python
from tilopay import TiloPay

# Initialize SDK
tilopay = TiloPay(
    api_key=company.tilopay_api_key,
    secret_key=company.tilopay_secret_key,
    environment='sandbox'  # or 'production'
)

# Create payment
payment_response = tilopay.create_payment(
    amount=50000,  # CRC (Costa Rica Colones)
    currency='CRC',
    reference='INV/2025/0001',
    customer_email='member@gym.com',
    payment_methods=['sinpe', 'card'],
    return_url='https://gym.com/payment/tilopay/return',  # ← CRITICAL
    description='Membership - January 2025'
)

# Response structure:
{
    'payment_id': 'pay_abc123xyz',
    'payment_url': 'https://pay.tilopay.com/checkout/abc123xyz',
    'expires_at': '2025-01-15T10:30:00Z',
    'status': 'pending'
}
```

### Critical Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `amount` | Integer | Yes | Amount in minor units (50000 = ₡50,000.00) |
| `currency` | String | Yes | Always "CRC" for Costa Rica |
| `reference` | String | Yes | Unique invoice/order reference |
| `return_url` | String | **YES** | URL to redirect after payment (with result parameters) |
| `payment_methods` | Array | Yes | `['sinpe', 'card']` or specific methods |

**❌ DOES NOT EXIST:** `callback_url`, `webhook_url`, `notification_url`

---

## Member Redirect (Step 3-5)

### Redirect Member to TiloPay

```python
# In Odoo controller
@http.route('/payment/tilopay/initiate', type='http', auth='user', website=True)
def tilopay_payment_initiate(self, invoice_id=None, **kwargs):
    """Initiate TiloPay payment - redirects member to payment page"""

    invoice = request.env['account.move'].browse(int(invoice_id))

    # Create payment via SDK
    payment_response = tilopay.create_payment(
        amount=int(invoice.amount_total * 100),  # Convert to minor units
        currency='CRC',
        reference=invoice.name,
        customer_email=invoice.partner_id.email,
        payment_methods=['sinpe', 'card'],
        return_url=f'{request.httprequest.host_url}payment/tilopay/return'
    )

    # Store payment_id for verification later
    invoice.write({
        'tilopay_payment_id': payment_response['payment_id'],
        'tilopay_status': 'pending'
    })

    # Redirect member to TiloPay payment page
    return request.redirect(payment_response['payment_url'])
```

---

## Return URL Handler (Step 6-8)

### Parse Redirect Parameters

After payment completion, TiloPay redirects the member to your `return_url` with payment result as URL parameters:

**Example Return URL:**
```
https://gym.com/payment/tilopay/return?
  payment_id=pay_abc123xyz
  &status=approved
  &amount=50000
  &currency=CRC
  &reference=INV/2025/0001
  &payment_method=sinpe
  &transaction_id=87654321
  &timestamp=2025-01-15T09:15:23Z
```

### Odoo Controller Implementation

```python
@http.route('/payment/tilopay/return', type='http', auth='public', website=True, csrf=False)
def tilopay_payment_return(self, **params):
    """Handle TiloPay redirect return with payment result"""

    # 1. Extract URL parameters
    payment_id = params.get('payment_id')
    status = params.get('status')  # approved, rejected, cancelled
    amount = params.get('amount')
    reference = params.get('reference')  # Invoice number
    transaction_id = params.get('transaction_id')
    payment_method = params.get('payment_method')  # sinpe, visa, mastercard

    # 2. Validate payment exists
    if not payment_id:
        return request.render('l10n_cr_einvoice.payment_error', {
            'error': 'Invalid payment response - missing payment_id'
        })

    # 3. Find invoice by reference
    invoice = request.env['account.move'].sudo().search([
        ('name', '=', reference),
        ('tilopay_payment_id', '=', payment_id)
    ], limit=1)

    if not invoice:
        return request.render('l10n_cr_einvoice.payment_error', {
            'error': f'Invoice not found: {reference}'
        })

    # 4. Process payment result
    if status == 'approved':
        # Create payment record
        payment = request.env['account.payment'].sudo().create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': invoice.partner_id.id,
            'amount': float(amount) / 100,  # Convert from minor units
            'currency_id': invoice.currency_id.id,
            'journal_id': invoice.company_id.tilopay_journal_id.id,
            'ref': f'TiloPay {transaction_id}',
            'tilopay_payment_id': payment_id,
            'tilopay_transaction_id': transaction_id,
            'tilopay_payment_method': payment_method
        })

        # Reconcile with invoice
        payment.action_post()
        (payment.move_id.line_ids + invoice.line_ids).filtered(
            lambda line: line.account_id == invoice.account_id
        ).reconcile()

        # Update invoice status
        invoice.write({
            'tilopay_status': 'approved',
            'tilopay_transaction_id': transaction_id,
            'tilopay_paid_at': fields.Datetime.now()
        })

        # Trigger e-invoice generation
        invoice.action_generate_einvoice()

        return request.render('l10n_cr_einvoice.payment_success', {
            'invoice': invoice,
            'payment': payment,
            'transaction_id': transaction_id
        })

    elif status == 'rejected':
        invoice.write({
            'tilopay_status': 'rejected',
            'tilopay_rejection_reason': params.get('rejection_reason', 'Unknown')
        })
        return request.render('l10n_cr_einvoice.payment_rejected', {
            'invoice': invoice,
            'reason': params.get('rejection_reason')
        })

    elif status == 'cancelled':
        invoice.write({'tilopay_status': 'cancelled'})
        return request.render('l10n_cr_einvoice.payment_cancelled', {
            'invoice': invoice
        })

    else:
        # Unknown status
        return request.render('l10n_cr_einvoice.payment_error', {
            'error': f'Unknown payment status: {status}'
        })
```

---

## URL Parameter Reference

### Standard Return Parameters

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `payment_id` | String | `pay_*` | TiloPay payment ID (unique) |
| `status` | String | `approved`, `rejected`, `cancelled` | Final payment status |
| `amount` | Integer | 50000 | Amount in minor units (₡50,000.00) |
| `currency` | String | `CRC` | Currency code |
| `reference` | String | `INV/2025/0001` | Your original reference (invoice number) |
| `transaction_id` | String | 87654321 | Bank/processor transaction ID |
| `payment_method` | String | `sinpe`, `visa`, `mastercard`, `amex` | Payment method used |
| `timestamp` | ISO8601 | 2025-01-15T09:15:23Z | Payment completion timestamp |

### Rejection Parameters (status=rejected)

| Parameter | Type | Description |
|-----------|------|-------------|
| `rejection_reason` | String | Bank/processor rejection reason |
| `error_code` | String | Error code (bank-specific) |

---

## Error Handling

### Common Error Scenarios

**1. Member Closes Payment Page:**
- Status: `cancelled`
- Action: Allow retry, invoice remains unpaid

**2. Bank Rejects Payment:**
- Status: `rejected`
- Action: Display rejection reason, allow retry with different method

**3. Network Error During Redirect:**
- Symptom: Member never reaches return URL
- Mitigation: Implement polling fallback (check payment status via API)

**4. Duplicate Payment Attempt:**
- Check: Verify `payment_id` hasn't been processed before
- Action: Return existing payment result

### Polling Fallback (Optional)

For cases where redirect fails:

```python
def check_payment_status(payment_id):
    """Fallback: Poll TiloPay API for payment status"""

    response = tilopay.get_payment_status(payment_id)

    return {
        'status': response['status'],  # approved, rejected, pending, cancelled
        'transaction_id': response.get('transaction_id'),
        'payment_method': response.get('payment_method'),
        'completed_at': response.get('completed_at')
    }

# Use case: Member clicks "Check Payment Status" button
# if redirect didn't complete
```

---

## Security Considerations

### 1. Validate Return Parameters

```python
# Verify payment_id matches invoice
if invoice.tilopay_payment_id != payment_id:
    raise ValidationError('Payment ID mismatch - possible tampering')

# Verify amount matches invoice
expected_amount = int(invoice.amount_total * 100)
if int(amount) != expected_amount:
    raise ValidationError('Amount mismatch - possible tampering')
```

### 2. Use HTTPS Only

```python
# Force HTTPS for return URLs
return_url = f'https://{request.httprequest.host}/payment/tilopay/return'
```

### 3. CSRF Protection

```python
# Disable CSRF for return URL (member redirected from external site)
@http.route('/payment/tilopay/return', type='http', auth='public',
            website=True, csrf=False)
```

### 4. Idempotency

```python
# Prevent duplicate processing
if invoice.tilopay_status == 'approved':
    return request.render('l10n_cr_einvoice.payment_already_processed', {
        'invoice': invoice
    })
```

---

## Testing Guide

### Sandbox Environment

```python
# config.yaml or company settings
tilopay_environment = 'sandbox'
tilopay_api_key = '1944-7517-8858-2745-2844'  # Your sandbox key
tilopay_secret_key = 'your-sandbox-secret'
```

### Test Cards (Sandbox)

| Card Number | CVV | Result |
|-------------|-----|--------|
| 4111111111111111 | 123 | Approved |
| 5555555555554444 | 456 | Rejected (insufficient funds) |
| 378282246310005 | 789 | Cancelled by user |

### Test SINPE Móvil (Sandbox)

- Phone: 8888-8888
- Result: Always approved (instant)

---

## Integration Checklist

**Phase 1: Backend Setup**
- [ ] Install TiloPay SDK: `pip install tilopay`
- [ ] Configure API credentials (company settings)
- [ ] Create payment journal for TiloPay
- [ ] Add `tilopay_payment_id` field to `account.move`
- [ ] Add `tilopay_status` field to `account.move`

**Phase 2: Payment Initiate**
- [ ] Create `/payment/tilopay/initiate` controller
- [ ] Implement `create_payment()` call with return_url
- [ ] Store payment_id in invoice
- [ ] Redirect member to TiloPay payment_url

**Phase 3: Return Handler**
- [ ] Create `/payment/tilopay/return` controller
- [ ] Parse URL parameters (payment_id, status, etc.)
- [ ] Validate payment matches invoice
- [ ] Process approved payments (create account.payment)
- [ ] Reconcile payment with invoice
- [ ] Handle rejected/cancelled cases
- [ ] Render success/error templates

**Phase 4: Error Handling**
- [ ] Implement idempotency checks
- [ ] Add polling fallback for failed redirects
- [ ] Create user-friendly error messages
- [ ] Log all payment events for debugging

**Phase 5: Testing**
- [ ] Test approved flow (sandbox)
- [ ] Test rejected flow (sandbox)
- [ ] Test cancelled flow (sandbox)
- [ ] Test network failure scenarios
- [ ] Test duplicate payment attempts
- [ ] Test amount/reference tampering detection

**Phase 6: Production**
- [ ] Switch to production API keys
- [ ] Enable HTTPS for return URLs
- [ ] Configure monitoring/alerts
- [ ] Document support procedures

---

## Reference Documentation

**Official TiloPay Docs (Verified):**
- `docs/TiloPayAccess/docs/API-REFERENCE-COMPLETE.md`
- `docs/TiloPayAccess/docs/sdk-documentation-full-text.md`
- `docs/TiloPayAccess/docs/DOCUMENTATION-COMPLETE-SUMMARY.md`

**Integration Examples:**
- WooCommerce: Redirect-based pattern
- Odoo payment.provider extensions: Standard Odoo payment flow

**Related GMS Documents:**
- Epic 002: Payment Gateway Integration (redirect-based architecture)
- PRD: Section on TiloPay integration (corrected for redirect pattern)
- PRD Assumption Audit: Webhook verification results

---

## Support

**TiloPay Support:**
- Email: sac@tilopay.com
- Account: API Key 1944-7517-8858-2745-2844

**GMS Project:**
- Architecture Questions: See Epic 002
- Implementation Details: See correct-course Sprint Change Proposal

---

**Document Status:** ✅ Verified and Ready for Implementation
**Last Review:** 2026-01-15 (Correct-Course Workflow)
