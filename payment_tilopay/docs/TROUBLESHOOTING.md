# TiloPay Payment Gateway - Troubleshooting Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-28
**Target Audience:** System Administrators, Support Staff, Developers

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Payment Creation Failures](#payment-creation-failures)
4. [Webhook Issues](#webhook-issues)
5. [Invoice Integration Issues](#invoice-integration-issues)
6. [Configuration Problems](#configuration-problems)
7. [Performance Issues](#performance-issues)
8. [Log Analysis](#log-analysis)
9. [Testing Tools](#testing-tools)
10. [Getting Help](#getting-help)

---

## Quick Diagnostics

### Health Check Script

Run this to diagnose common issues:

```python
# Execute in Odoo shell: odoo-bin shell -c odoo.conf -d your_database

def check_tilopay_health():
    """Quick health check for TiloPay module."""
    env = api.Environment(cr, uid, {})

    print("=== TiloPay Health Check ===\n")

    # 1. Module installed?
    module = env['ir.module.module'].search([('name', '=', 'payment_tilopay')])
    print(f"✓ Module installed: {module.state == 'installed'}")

    # 2. Provider configured?
    provider = env['payment.provider'].search([('code', '=', 'tilopay')])
    if provider:
        print(f"✓ Provider found: {provider.name}")
        print(f"  State: {provider.state}")
        print(f"  Sandbox: {provider.tilopay_use_sandbox}")
        print(f"  SINPE enabled: {provider.tilopay_enable_sinpe}")
        print(f"  Cards enabled: {provider.tilopay_enable_cards}")
        print(f"  Webhook URL: {provider.tilopay_webhook_url}")
    else:
        print("✗ No TiloPay provider found")
        return

    # 3. Credentials configured?
    has_creds = all([
        provider.tilopay_api_key,
        provider.tilopay_api_user,
        provider.tilopay_api_password
    ])
    print(f"✓ Credentials configured: {has_creds}")

    # 4. Recent transactions?
    txs = env['payment.transaction'].search([
        ('provider_code', '=', 'tilopay')
    ], limit=5, order='create_date desc')
    print(f"\n✓ Recent transactions: {len(txs)}")
    for tx in txs:
        print(f"  - {tx.reference}: {tx.state} ({tx.create_date})")

    # 5. Pending payments?
    pending = env['payment.transaction'].search_count([
        ('provider_code', '=', 'tilopay'),
        ('state', '=', 'pending')
    ])
    print(f"\n✓ Pending payments: {pending}")

    # 6. Failed payments (last 7 days)?
    from datetime import datetime, timedelta
    week_ago = datetime.now() - timedelta(days=7)
    failed = env['payment.transaction'].search_count([
        ('provider_code', '=', 'tilopay'),
        ('state', '=', 'error'),
        ('create_date', '>=', week_ago)
    ])
    print(f"✓ Failed payments (7 days): {failed}")

    print("\n=== Health Check Complete ===")

check_tilopay_health()
```

---

## Common Issues

### Issue: "Payment Creation Failed"

**Symptom:**
- Error when clicking "Pay Now" on invoice
- Message: "Unable to create payment with TiloPay"

**Possible Causes:**

1. **Invalid API Credentials**

   **Diagnosis:**
   ```python
   provider = env['payment.provider'].search([('code', '=', 'tilopay')])
   print(f"API Key: {provider.tilopay_api_key[:10]}... (truncated)")
   print(f"API User: {provider.tilopay_api_user}")
   print(f"Sandbox: {provider.tilopay_use_sandbox}")
   ```

   **Solution:**
   - Verify credentials in TiloPay dashboard
   - Ensure using correct environment (sandbox vs production)
   - Test credentials using "Test Connection" button
   - Update credentials if expired

2. **Provider Not Enabled**

   **Diagnosis:**
   ```python
   provider = env['payment.provider'].search([('code', '=', 'tilopay')])
   print(f"State: {provider.state}")
   ```

   **Solution:**
   - Go to: Accounting > Configuration > Payment Providers
   - Find TiloPay provider
   - Set state to "Enabled"

3. **Network Connectivity**

   **Diagnosis:**
   ```bash
   # Test connection to TiloPay
   curl -I https://sandbox.tilopay.com/api/v1
   curl -I https://api.tilopay.com/api/v1
   ```

   **Solution:**
   - Check firewall allows HTTPS to tilopay.com
   - Verify DNS resolution
   - Check proxy settings if applicable

4. **Missing Customer Email**

   **Diagnosis:**
   ```python
   invoice = env['account.move'].browse(invoice_id)
   print(f"Customer email: {invoice.partner_id.email}")
   ```

   **Solution:**
   - Add email to customer record
   - Go to: Contacts > Find customer > Add email

---

### Issue: "Webhook Not Received"

**Symptom:**
- Payment completed on TiloPay but invoice still unpaid
- Transaction stuck in "pending" state

**Possible Causes:**

1. **Webhook URL Not Configured in TiloPay**

   **Diagnosis:**
   ```python
   provider = env['payment.provider'].search([('code', '=', 'tilopay')])
   print(f"Webhook URL: {provider.tilopay_webhook_url}")
   ```

   **Solution:**
   - Copy webhook URL from Odoo
   - Log in to TiloPay dashboard
   - Go to: Developer > Webhooks
   - Add webhook with URL from Odoo
   - Select events: payment.completed, payment.failed, payment.cancelled

2. **Webhook URL Not Accessible**

   **Diagnosis:**
   ```bash
   # Test webhook URL from external location
   curl -X POST https://your-domain.com/payment/tilopay/webhook \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

   **Solution:**
   - Ensure Odoo is publicly accessible
   - Check firewall allows inbound HTTPS
   - Verify SSL certificate is valid
   - Check load balancer / reverse proxy configuration

3. **Invalid Webhook Signature**

   **Diagnosis:**
   ```bash
   # Check Odoo logs
   grep "Invalid webhook signature" odoo.log
   ```

   **Solution:**
   - Verify secret key matches between Odoo and TiloPay
   - Check secret key not expired
   - Ensure webhook payload not modified in transit

4. **Webhook Processing Error**

   **Diagnosis:**
   ```bash
   # Check Odoo logs for errors
   grep "Error processing TiloPay webhook" odoo.log
   ```

   **Solution:**
   - Review error message in logs
   - Check transaction exists for payment_id
   - Verify database constraints not violated
   - Check for code errors in custom extensions

**Workaround:**
Manually refresh transaction status:
1. Go to: Accounting > Configuration > Payment Transactions
2. Find transaction by reference
3. Click "Refresh Status" button

---

### Issue: "Invoice Not Marked as Paid"

**Symptom:**
- Payment successful (transaction state = 'done')
- But invoice still shows unpaid

**Possible Causes:**

1. **Invoice Integration Not Triggered**

   **Diagnosis:**
   ```python
   tx = env['payment.transaction'].search([('reference', '=', 'TX-REF')])
   print(f"Transaction state: {tx.state}")
   print(f"Linked invoices: {tx.invoice_ids}")
   print(f"Invoice payment state: {tx.invoice_ids[0].payment_state if tx.invoice_ids else 'N/A'}")
   ```

   **Solution:**
   - Verify transaction is linked to invoice
   - Check _tilopay_update_invoice_payment() was called
   - Review logs for errors during invoice update

2. **Amount Mismatch**

   **Diagnosis:**
   ```python
   tx = env['payment.transaction'].search([('reference', '=', 'TX-REF')])
   invoice = tx.invoice_ids[0]
   print(f"Transaction amount: {tx.amount}")
   print(f"Invoice residual: {invoice.amount_residual}")
   ```

   **Solution:**
   - Amounts must match exactly
   - Check for currency differences
   - Verify no partial payments

3. **Payment Not Reconciled**

   **Diagnosis:**
   ```python
   tx = env['payment.transaction'].search([('reference', '=', 'TX-REF')])
   invoice = tx.invoice_ids[0]
   print(f"Invoice reconciled: {invoice.payment_state}")
   ```

   **Solution:**
   - Manually reconcile payment with invoice
   - Check accounting journal configuration

---

### Issue: "Test Connection Fails"

**Symptom:**
- Click "Test Connection" in provider settings
- Error message displayed

**Possible Causes:**

1. **Invalid Credentials**

   **Solution:**
   - Verify credentials in TiloPay dashboard
   - Check for typos in API key, user, password
   - Ensure credentials match environment (sandbox/prod)

2. **Network Issues**

   **Solution:**
   - Test connectivity: `curl https://sandbox.tilopay.com`
   - Check firewall/proxy settings
   - Verify DNS resolution

3. **TiloPay Service Down**

   **Solution:**
   - Check TiloPay status page
   - Wait and retry later
   - Contact TiloPay support

---

## Payment Creation Failures

### Error: "Amount must be greater than zero"

**Cause:** Invoice amount is zero or negative

**Solution:**
```python
invoice = env['account.move'].browse(invoice_id)
print(f"Amount residual: {invoice.amount_residual}")
```
- Ensure invoice has positive balance
- Check for rounding errors

---

### Error: "Customer email is required"

**Cause:** Partner record missing email

**Solution:**
1. Go to Contacts
2. Find customer
3. Add valid email address
4. Try payment again

---

### Error: "No payment methods enabled"

**Cause:** All payment methods disabled in provider

**Solution:**
1. Go to: Accounting > Configuration > Payment Providers > TiloPay
2. Enable at least one of:
   - SINPE Móvil
   - Credit/Debit Cards
   - Yappy

---

### Error: "TiloPay API authentication failed"

**Cause:** Invalid credentials or expired token

**Solution:**
1. Verify credentials in TiloPay dashboard
2. Update credentials in Odoo
3. Test connection
4. Enable provider

**Log Analysis:**
```bash
grep "TiloPay API authentication" odoo.log
grep "401 Unauthorized" odoo.log
```

---

## Webhook Issues

### Webhook Not Triggering

**Checklist:**
- [ ] Webhook URL configured in TiloPay dashboard
- [ ] URL is publicly accessible (test with curl)
- [ ] HTTPS enabled (webhooks require HTTPS)
- [ ] Firewall allows inbound HTTPS
- [ ] SSL certificate valid

**Test Webhook Manually:**
```bash
# Send test webhook
curl -X POST https://your-domain.com/payment/tilopay/webhook \
  -H "Content-Type: application/json" \
  -H "X-TiloPay-Signature: test_signature" \
  -d '{
    "event": "payment.completed",
    "payment_id": "pay_test_123",
    "data": {
      "status": "approved",
      "amount": 50000,
      "currency": "CRC",
      "reference": "TEST-001",
      "payment_method": "sinpe"
    }
  }'
```

---

### Webhook Signature Verification Failing

**Log Output:**
```
ERROR odoo.addons.payment_tilopay.controllers.tilopay_webhook:
SECURITY: Invalid webhook signature detected!
Expected: abc123..., Got: xyz789...
```

**Cause:** Secret key mismatch

**Solution:**
1. Get secret key from TiloPay dashboard
2. Update in Odoo: Payment Provider > TiloPay > Secret Key
3. Save
4. Test webhook again

**Verify Secret Key:**
```python
provider = env['payment.provider'].search([('code', '=', 'tilopay')])
print(f"Secret key set: {bool(provider.tilopay_secret_key)}")
# Don't print actual key for security
```

---

### Duplicate Webhooks

**Log Output:**
```
WARNING odoo.addons.payment_tilopay.models.tilopay_payment_transaction:
Duplicate webhook received for transaction 123 (count: 3)
```

**Cause:** TiloPay retrying webhook delivery

**Impact:** None (duplicates are ignored)

**Why This Happens:**
- TiloPay retries if webhook response not 200
- Network timeouts
- Slow response times

**Solution:**
- Optimize webhook processing speed
- Ensure always returning 200 status
- No action needed (duplicates safely ignored)

---

## Invoice Integration Issues

### E-Invoice Not Generated

**Symptom:**
- Payment successful
- Invoice marked paid
- But no e-invoice generated

**Diagnosis:**
```python
invoice = env['account.move'].browse(invoice_id)
print(f"Payment state: {invoice.payment_state}")
print(f"Has e-invoice: {bool(invoice.l10n_cr_einvoice_id)}")
print(f"Payment method: {invoice.l10n_cr_payment_method_id.code if invoice.l10n_cr_payment_method_id else 'None'}")
```

**Possible Causes:**

1. **l10n_cr_einvoice module not installed**
   - Solution: Install Costa Rica E-Invoice module

2. **Invoice state not 'posted'**
   - Solution: Confirm invoice before payment

3. **E-invoice generation error**
   - Check logs: `grep "e-invoice" odoo.log`

**Manual Trigger:**
```python
invoice = env['account.move'].browse(invoice_id)
invoice.action_generate_einvoice()
```

---

### Payment Method Not Updated

**Symptom:**
- Payment successful via SINPE
- But invoice shows different payment method

**Diagnosis:**
```python
tx = env['payment.transaction'].search([('reference', '=', 'TX-REF')])
invoice = tx.invoice_ids[0]

print(f"TiloPay method: {tx.tilopay_payment_method}")
print(f"Invoice method: {invoice.l10n_cr_payment_method_id.code if invoice.l10n_cr_payment_method_id else 'None'}")
```

**Solution:**
Verify payment method mapping in `_tilopay_update_invoice_payment()`:
```python
'sinpe' → '06' (SINPE Móvil)
'card'  → '02' (Credit/Debit Card)
```

---

## Configuration Problems

### Provider Not Visible in Portal

**Symptom:**
- Admin sees TiloPay in payment providers
- Portal users don't see "Pay Now" button

**Checklist:**
- [ ] Provider state = "Enabled"
- [ ] Invoice is posted
- [ ] Invoice has balance due
- [ ] Customer has email
- [ ] Portal user has access to invoice

**Diagnosis:**
```python
invoice = env['account.move'].browse(invoice_id)
print(f"Can pay online: {invoice.can_pay_online}")
print(f"Move type: {invoice.move_type}")
print(f"State: {invoice.state}")
print(f"Payment state: {invoice.payment_state}")
print(f"Residual: {invoice.amount_residual}")
print(f"Customer email: {invoice.partner_id.email}")
```

---

### Sandbox vs Production Confusion

**Symptom:**
- Payments work in test but not production (or vice versa)

**Diagnosis:**
```python
provider = env['payment.provider'].search([('code', '=', 'tilopay')])
print(f"Using sandbox: {provider.tilopay_use_sandbox}")
```

**Solution:**
- Ensure sandbox flag matches credential type
- Sandbox = True → Use sandbox credentials
- Sandbox = False → Use production credentials
- Test both environments separately

---

## Performance Issues

### Slow Payment Creation

**Symptom:**
- "Pay Now" button takes >10 seconds
- Users see loading spinner

**Possible Causes:**

1. **Slow TiloPay API Response**
   - Check API response time in logs
   - Contact TiloPay support if consistently slow

2. **Network Latency**
   - Test: `time curl https://api.tilopay.com`
   - Optimize network routing

3. **Database Slow**
   - Check transaction table size
   - Add indexes if needed
   - Optimize database queries

**Monitoring:**
```python
import time

start = time.time()
tx = invoice.action_pay_online()
elapsed = time.time() - start

print(f"Payment creation took: {elapsed:.2f} seconds")
```

---

### Webhook Processing Delays

**Symptom:**
- Payment completes on TiloPay
- Invoice marked paid 30+ seconds later

**Possible Causes:**

1. **TiloPay Webhook Delays**
   - Normal: 1-5 seconds
   - Check TiloPay webhook logs

2. **Odoo Processing Slow**
   - Check webhook handler performance
   - Review logs for bottlenecks

3. **Database Locks**
   - Transaction waiting for lock
   - Check: `SELECT * FROM pg_locks;`

**Optimization:**
- Minimize work in webhook handler
- Defer heavy processing to scheduled jobs
- Use database indexes

---

## Log Analysis

### Log Locations

**Odoo Server Log:**
```bash
tail -f /var/log/odoo/odoo.log
```

**Filter TiloPay Logs:**
```bash
grep -i "tilopay" /var/log/odoo/odoo.log | tail -50
```

**Filter by Severity:**
```bash
# Errors only
grep "ERROR.*tilopay" /var/log/odoo/odoo.log

# Warnings and above
grep -E "(WARNING|ERROR|CRITICAL).*tilopay" /var/log/odoo/odoo.log
```

---

### Common Log Messages

**Normal Operations:**

```
INFO ... TiloPay API Client initialized in SANDBOX mode
INFO ... Creating TiloPay payment for transaction 123
INFO ... TiloPay payment created successfully: pay_abc123
INFO ... Processing TiloPay webhook notification for transaction 456
INFO ... Payment completed successfully for transaction 456
```

**Errors to Investigate:**

```
ERROR ... Failed to create TiloPay payment for transaction 789
ERROR ... SECURITY: Invalid webhook signature detected!
ERROR ... Transaction not found for payment_id: pay_xyz
ERROR ... Amount mismatch for transaction 111: expected 50000, got 49900
```

---

### Log Analysis Script

```bash
#!/bin/bash
# analyze_tilopay_logs.sh

LOG_FILE="/var/log/odoo/odoo.log"

echo "=== TiloPay Log Analysis ==="
echo

echo "Total TiloPay log entries:"
grep -c "tilopay" "$LOG_FILE"

echo
echo "Errors (last 10):"
grep "ERROR.*tilopay" "$LOG_FILE" | tail -10

echo
echo "Security warnings (last 10):"
grep "SECURITY.*tilopay" "$LOG_FILE" | tail -10

echo
echo "Recent payments (last 10):"
grep "Payment created successfully" "$LOG_FILE" | tail -10

echo
echo "Failed payments (last 10):"
grep "Payment failed" "$LOG_FILE" | tail -10

echo
echo "Webhook issues (last 10):"
grep -E "(webhook.*error|Invalid webhook)" "$LOG_FILE" | tail -10
```

---

## Testing Tools

### Manual Payment Test

```python
# Execute in Odoo shell

def test_payment_creation():
    """Test payment creation end-to-end."""
    env = api.Environment(cr, uid, {})

    # 1. Get test invoice
    invoice = env['account.move'].search([
        ('move_type', '=', 'out_invoice'),
        ('state', '=', 'posted'),
        ('payment_state', '=', 'not_paid')
    ], limit=1)

    if not invoice:
        print("No test invoice found")
        return

    print(f"Testing with invoice: {invoice.name}")
    print(f"Amount: {invoice.amount_residual} {invoice.currency_id.name}")

    # 2. Create payment
    try:
        action = invoice.action_pay_online()
        print(f"✓ Payment created successfully")
        print(f"Payment URL: {action['url']}")
    except Exception as e:
        print(f"✗ Payment creation failed: {e}")

test_payment_creation()
```

---

### Webhook Simulation

```python
def simulate_webhook():
    """Simulate webhook notification."""
    env = api.Environment(cr, uid, {})

    # Find pending transaction
    tx = env['payment.transaction'].search([
        ('provider_code', '=', 'tilopay'),
        ('state', '=', 'pending')
    ], limit=1)

    if not tx:
        print("No pending transaction found")
        return

    print(f"Simulating webhook for: {tx.reference}")

    # Build notification data
    notification_data = {
        'event': 'payment.completed',
        'payment_id': tx.tilopay_payment_id,
        'data': {
            'status': 'approved',
            'amount': int(tx.amount * 100),
            'currency': tx.currency_id.name,
            'reference': tx.reference,
            'payment_method': 'sinpe',
            'transaction_id': 'TEST_TX_12345'
        }
    }

    try:
        tx._tilopay_process_notification(notification_data)
        print(f"✓ Webhook processed successfully")
        print(f"Transaction state: {tx.state}")
    except Exception as e:
        print(f"✗ Webhook processing failed: {e}")

simulate_webhook()
```

---

### Connection Test

```bash
#!/bin/bash
# test_tilopay_connection.sh

echo "=== TiloPay Connection Test ==="

# Test sandbox
echo "Testing Sandbox API..."
curl -I https://sandbox.tilopay.com/api/v1 2>&1 | grep "HTTP"

# Test production
echo "Testing Production API..."
curl -I https://api.tilopay.com/api/v1 2>&1 | grep "HTTP"

# Test webhook URL
echo "Testing Webhook URL..."
WEBHOOK_URL="https://your-domain.com/payment/tilopay/webhook"
curl -I "$WEBHOOK_URL" 2>&1 | grep "HTTP"

echo
echo "=== Test Complete ==="
```

---

## Getting Help

### Self-Help Resources

1. **Check Logs First**
   ```bash
   grep -i "tilopay" /var/log/odoo/odoo.log | tail -100
   ```

2. **Review Documentation**
   - [API Documentation](API_DOCUMENTATION.md)
   - [Architecture](ARCHITECTURE.md)
   - [Security](SECURITY.md)

3. **Run Health Check**
   ```python
   check_tilopay_health()  # See "Quick Diagnostics" above
   ```

---

### Odoo Support

**Community Forum:**
- https://www.odoo.com/forum

**Search for:**
- "payment provider"
- "payment transaction"
- "webhook"

---

### TiloPay Support

**Email:** sac@tilopay.com

**Developer Portal:**
https://cst.support.tilopay.com/servicedesk/customer/portal/21

**Documentation:**
https://tilopay.com/documentacion

**When Contacting TiloPay:**
- Include merchant ID
- Describe issue clearly
- Provide payment IDs if applicable
- Include timestamp of issue
- Mention if sandbox or production

---

### Internal Support

**Development Team:**
- Email: dev@mygym.com
- Slack: #tilopay-support

**System Administrator:**
- Email: sysadmin@mygym.com
- Phone: +506-XXXX-XXXX

**When Requesting Help:**
1. Describe what you were trying to do
2. What happened instead
3. Any error messages
4. Relevant log excerpts
5. Steps you've already tried

---

### Debug Mode

Enable Odoo debug mode for additional information:

**URL Method:**
Add `?debug=1` to URL:
```
https://your-domain.com/web?debug=1
```

**Developer Mode:**
Settings > Activate Developer Mode

**Benefits:**
- View technical field names
- Access debug information
- See detailed error messages
- Inspect object attributes

---

## Escalation Matrix

| Issue Severity | Response Time | Escalation Path |
|---------------|--------------|-----------------|
| **Critical** (Payment processing down) | 15 minutes | Sysadmin → Dev Team → TiloPay |
| **High** (Multiple payment failures) | 2 hours | Support → Dev Team |
| **Medium** (Single payment failure) | 4 hours | Support → Sysadmin |
| **Low** (Questions, enhancements) | 24 hours | Support |

---

## Appendix: Error Codes

### TiloPay API Error Codes

| Code | Message | Solution |
|------|---------|----------|
| 401 | Unauthorized | Check credentials |
| 403 | Forbidden | Check API permissions |
| 404 | Not Found | Verify payment ID |
| 422 | Validation Error | Check request parameters |
| 500 | Server Error | Contact TiloPay support |

### Odoo Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| ValidationError | Data validation failed | Check constraints |
| UserError | User-facing error | Read error message |
| AccessError | Permission denied | Check access rights |
| MissingError | Record not found | Verify record exists |

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-28
**Maintained By:** GMS Support Team
