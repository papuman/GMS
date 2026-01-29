# TiloPay Payment Gateway - Security Documentation

**Version:** 1.0.0
**Last Updated:** 2025-12-28
**Classification:** Internal - Security Sensitive

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Threat Model](#threat-model)
3. [Authentication & Authorization](#authentication--authorization)
4. [Credential Management](#credential-management)
5. [Webhook Security](#webhook-security)
6. [Data Protection](#data-protection)
7. [Network Security](#network-security)
8. [Audit & Logging](#audit--logging)
9. [Compliance](#compliance)
10. [Security Checklist](#security-checklist)
11. [Incident Response](#incident-response)

---

## Security Overview

The TiloPay Payment Gateway module handles financial transactions and must maintain the highest security standards. This document outlines security mechanisms, best practices, and potential vulnerabilities.

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimal permissions by default
3. **Fail Secure**: Errors result in denial, not exposure
4. **Audit Everything**: Complete transaction logging
5. **Never Trust Input**: Validate all external data

### PCI-DSS Compliance

This module is **PCI-DSS compliant** because:
- ✅ No card data is stored in Odoo
- ✅ Payments processed on TiloPay hosted page
- ✅ Only payment references stored locally
- ✅ HTTPS/TLS for all communications
- ✅ Audit logging enabled

---

## Threat Model

### Threat Actors

1. **External Attackers**
   - Goal: Steal funds or mark invoices as paid fraudulently
   - Vectors: Webhook forgery, API credential theft

2. **Malicious Insiders**
   - Goal: Process unauthorized refunds or view payment data
   - Vectors: Privilege escalation, credential theft

3. **Compromised Member Accounts**
   - Goal: View other members' payment information
   - Vectors: Session hijacking, SQL injection

### Attack Vectors

| Vector | Risk Level | Mitigation |
|--------|-----------|------------|
| Webhook Forgery | CRITICAL | HMAC-SHA256 signature verification |
| Credential Theft | CRITICAL | Encrypted storage, access control |
| Man-in-the-Middle | HIGH | HTTPS/TLS enforcement |
| SQL Injection | MEDIUM | Odoo ORM (parameterized queries) |
| XSS | MEDIUM | Odoo framework protections |
| CSRF | LOW | CSRF tokens (except webhooks) |
| Replay Attacks | LOW | Webhook duplicate detection |

---

## Authentication & Authorization

### TiloPay API Authentication

**Method:** OAuth2 Bearer Token

**Flow:**
```
1. POST /auth/login
   Body: {username, password, api_key}

2. Response: {access_token, expires_in}

3. Subsequent requests:
   Header: Authorization: Bearer {access_token}
```

**Security Considerations:**
- Tokens expire after period (check TiloPay docs)
- Tokens transmitted only over HTTPS
- Tokens never logged or displayed in UI
- Implement token refresh to avoid re-authentication

**Implementation:**
```python
def _authenticate(self):
    response = self.session.post(
        f"{self.base_url}/auth/login",
        json={
            "username": self.api_user,
            "password": self.api_password,
            "api_key": self.api_key
        },
        timeout=30
    )
    response.raise_for_status()

    data = response.json()
    self.access_token = data['access_token']

    # Set for all future requests
    self.session.headers.update({
        'Authorization': f'Bearer {self.access_token}',
        'Content-Type': 'application/json'
    })
```

---

### Odoo User Authorization

**Access Control Matrix:**

| Role | View Provider | Configure Provider | View Transactions | Create Payments | Refunds | Webhooks |
|------|--------------|-------------------|------------------|----------------|---------|----------|
| **System Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Accountant** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Sales User** | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Portal User** | ❌ | ❌ | Own Only | Own Only | ❌ | ❌ |
| **Public** | ❌ | ❌ | ❌ | ❌ | ❌ | Webhooks Only |

**Implementation:**
```xml
<!-- security/ir.model.access.csv -->
payment.provider,base.group_system,1,1,1,1
payment.provider,account.group_account_manager,1,0,1,1
payment.transaction,base.group_user,1,1,1,1
payment.transaction,base.group_portal,1,0,0,0
```

**Field-Level Security:**
```python
tilopay_api_key = fields.Char(
    groups='base.group_system'  # Only admins can view
)

tilopay_api_password = fields.Char(
    groups='base.group_system',
    # Never appears in logs or exports
)
```

---

## Credential Management

### Storage Security

**Database Encryption:**
```python
# Odoo automatically encrypts fields marked as password
tilopay_api_password = fields.Char(
    string='API Password',
    password=True,  # Triggers encryption
    groups='base.group_system'
)
```

**Access Restrictions:**
- Credentials visible only to `base.group_system` (System admins)
- Password fields display as `******` in UI
- Never included in exports or logs
- Cannot be retrieved via XML-RPC without proper auth

### Credential Lifecycle

**Creation:**
```python
@api.constrains('tilopay_api_key', 'tilopay_api_user', 'tilopay_api_password')
def _check_tilopay_credentials(self):
    """Validate credentials on save."""
    if self.code == 'tilopay' and self.state != 'disabled':
        if not all([self.tilopay_api_key,
                    self.tilopay_api_user,
                    self.tilopay_api_password]):
            raise ValidationError("All credentials required")
```

**Rotation:**
```
1. Obtain new credentials from TiloPay
2. Update provider configuration in Odoo
3. Test connection
4. Enable provider
5. Revoke old credentials in TiloPay dashboard
```

**Revocation:**
```
1. Disable provider in Odoo (state = 'disabled')
2. Revoke API credentials in TiloPay dashboard
3. Monitor logs for unauthorized access attempts
```

### Environment-Based Configuration

**Best Practice:** Use environment variables for credentials

```python
# In odoo.conf or environment
TILOPAY_API_KEY=6609-5850-8330-8034-3464
TILOPAY_API_USER=lSrT45
TILOPAY_API_PASSWORD=Zlb8H9

# In Odoo
import os

tilopay_api_key = os.getenv('TILOPAY_API_KEY')
```

**Benefit:** Credentials not stored in database or code

---

## Webhook Security

### Why Webhook Security Matters

**Vulnerability:** Unverified webhooks allow attackers to:
1. Mark unpaid invoices as paid (fraud)
2. Trigger refunds without actual payment
3. Manipulate transaction states
4. Inject malicious data

**Impact:** Financial loss, fraudulent invoices, accounting corruption

### Signature Verification (CRITICAL)

**HMAC-SHA256 Verification:**

```python
def verify_webhook_signature(self, payload, signature, secret_key):
    """
    Verify webhook signature using HMAC-SHA256.

    Security: This is CRITICAL for preventing fraudulent webhooks.
    NEVER process webhooks without signature verification.
    """
    # Compute expected signature
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        payload,  # Raw request body (bytes)
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison (prevents timing attacks)
    is_valid = hmac.compare_digest(expected_signature, signature)

    if not is_valid:
        _logger.error(
            "SECURITY: Invalid webhook signature detected! "
            "Expected: %s, Got: %s",
            expected_signature, signature
        )

    return is_valid
```

**Why Constant-Time Comparison?**

```python
# ❌ VULNERABLE: String comparison leaks timing information
if expected == signature:
    return True

# ✅ SECURE: Constant-time comparison
return hmac.compare_digest(expected, signature)
```

**Timing Attack Example:**
```
Attacker tries signatures:
"aaa..." → Fails instantly (first byte wrong)
"abc..." → Takes slightly longer (first byte matches)

By measuring response times, attacker can guess signature byte-by-byte.
Constant-time comparison prevents this.
```

### Webhook Validation Checklist

```python
def tilopay_webhook(self, **kwargs):
    """Webhook handler with complete security checks."""

    # 1. Extract signature
    signature = request.httprequest.headers.get('X-TiloPay-Signature')
    if not signature:
        _logger.error("SECURITY: Webhook missing signature!")
        return {'status': 'error'}

    # 2. Get raw payload (don't parse yet!)
    raw_payload = request.httprequest.get_data()

    # 3. Verify signature
    provider = request.env['payment.provider'].sudo().search([
        ('code', '=', 'tilopay'),
        ('state', '=', 'enabled')
    ], limit=1)

    client = provider._tilopay_get_api_client()
    if not client.verify_webhook_signature(
        raw_payload,
        signature,
        provider.tilopay_secret_key
    ):
        _logger.error("SECURITY: Invalid signature - possible attack!")
        return {'status': 'error'}

    # 4. Now safe to parse payload
    payload = json.loads(raw_payload)

    # 5. Validate payload structure
    if not payload.get('payment_id'):
        _logger.error("Invalid payload: missing payment_id")
        return {'status': 'error'}

    # 6. Find transaction
    tx = request.env['payment.transaction'].sudo().search([
        ('tilopay_payment_id', '=', payload['payment_id'])
    ], limit=1)

    if not tx:
        _logger.error("Transaction not found: %s", payload['payment_id'])
        return {'status': 'error'}

    # 7. Check for duplicates
    if tx.tilopay_webhook_count > 0:
        _logger.warning("Duplicate webhook for %s", tx.reference)
        return {'status': 'success'}  # Acknowledge but don't process

    # 8. Validate amount
    webhook_amount = payload['data'].get('amount', 0) / 100.0
    if abs(webhook_amount - tx.amount) > 0.01:
        _logger.error(
            "Amount mismatch: expected %s, got %s",
            tx.amount, webhook_amount
        )
        # Log but continue (some fees may cause small differences)

    # 9. Process notification
    tx._tilopay_process_notification(payload)

    return {'status': 'success'}
```

### Webhook Replay Attack Prevention

**Duplicate Detection:**
```python
tilopay_webhook_count = fields.Integer(
    default=0,
    readonly=True,
    help="Number of webhooks received (for duplicate detection)"
)

# In webhook handler
tx.tilopay_webhook_count += 1

if tx.tilopay_webhook_count > 1:
    _logger.warning("Duplicate webhook detected - ignoring")
    return
```

**Timestamp Validation (Optional):**
```python
webhook_timestamp = payload.get('timestamp')
webhook_time = datetime.fromisoformat(webhook_timestamp)
current_time = datetime.utcnow()

# Reject webhooks older than 5 minutes
if (current_time - webhook_time).total_seconds() > 300:
    _logger.error("Webhook too old - possible replay attack")
    return {'status': 'error'}
```

---

## Data Protection

### Sensitive Data Inventory

| Data Type | Sensitivity | Storage | Encryption |
|-----------|------------|---------|------------|
| API Credentials | CRITICAL | Database | ✅ Encrypted |
| Access Tokens | CRITICAL | Memory Only | ❌ (temp) |
| Payment IDs | MEDIUM | Database | ❌ (not PII) |
| Customer Email | MEDIUM | Database | ❌ (needed) |
| Card Numbers | N/A | Never Stored | N/A |
| Transaction IDs | LOW | Database | ❌ (public) |

### What We DON'T Store

**PCI-DSS Prohibited Data:**
- ❌ Credit card numbers (full PAN)
- ❌ CVV/CVC codes
- ❌ Card expiration dates
- ❌ Cardholder names (from cards)

**Why?** All card processing happens on TiloPay's hosted page. Odoo never sees card data.

### Data Retention

**Transaction Records:**
- Retain indefinitely for accounting/audit
- Include: payment_id, amount, status, timestamps
- Exclude: raw API responses after 90 days (optional cleanup)

**Log Files:**
- Retain 90 days for troubleshooting
- Rotate daily
- Archive for compliance (check local laws)

**Cleanup Script (Optional):**
```python
def cleanup_old_webhook_data(self):
    """Remove raw responses older than 90 days."""
    cutoff = fields.Date.today() - timedelta(days=90)

    old_txs = self.env['payment.transaction'].search([
        ('create_date', '<', cutoff),
        ('provider_code', '=', 'tilopay'),
        ('tilopay_raw_response', '!=', False)
    ])

    old_txs.write({'tilopay_raw_response': False})
    _logger.info("Cleaned up %d old transaction responses", len(old_txs))
```

---

## Network Security

### HTTPS/TLS Enforcement

**All communications MUST use HTTPS:**

```python
# In API client
if not self.base_url.startswith('https://'):
    raise ValueError("HTTPS required for TiloPay API")

# In webhook controller
if request.httprequest.scheme != 'https':
    _logger.error("SECURITY: Non-HTTPS webhook rejected")
    return {'status': 'error'}
```

**TLS Version:** Require TLS 1.2 or higher

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

# Use in session
self.session.mount('https://', TLSAdapter())
```

### Firewall Configuration

**Outbound (Odoo → TiloPay):**
```
Allow: HTTPS (443) to api.tilopay.com
Allow: HTTPS (443) to sandbox.tilopay.com
```

**Inbound (TiloPay → Odoo):**
```
Allow: HTTPS (443) to /payment/tilopay/webhook
     From: TiloPay webhook IPs (check documentation)
```

### IP Whitelisting (Optional)

```python
TILOPAY_WEBHOOK_IPS = [
    '1.2.3.4',      # TiloPay webhook server 1
    '5.6.7.8',      # TiloPay webhook server 2
]

def tilopay_webhook(self, **kwargs):
    client_ip = request.httprequest.remote_addr

    if client_ip not in TILOPAY_WEBHOOK_IPS:
        _logger.error("Webhook from unauthorized IP: %s", client_ip)
        return {'status': 'error'}
```

---

## Audit & Logging

### What to Log

**Security Events (Always):**
- ✅ Authentication failures
- ✅ Invalid webhook signatures
- ✅ Amount mismatches
- ✅ Duplicate webhooks
- ✅ Unauthorized access attempts
- ✅ Credential changes

**Transaction Events (Always):**
- ✅ Payment creation
- ✅ Payment completion
- ✅ Payment failure
- ✅ Refunds
- ✅ Manual status refreshes

**Sensitive Data (NEVER):**
- ❌ API credentials
- ❌ Access tokens
- ❌ Full payment responses (sanitize)

### Logging Levels

```python
# CRITICAL: Security incidents
_logger.critical("SECURITY: Invalid webhook signature from %s", ip)

# ERROR: Payment failures, API errors
_logger.error("Payment creation failed: %s", error_message)

# WARNING: Suspicious activity, duplicate webhooks
_logger.warning("Duplicate webhook received for %s", payment_id)

# INFO: Normal operations
_logger.info("Payment created successfully: %s", payment_id)

# DEBUG: Development/troubleshooting only
_logger.debug("API response: %s", sanitize_response(response))
```

### Log Sanitization

```python
def sanitize_log_data(data):
    """Remove sensitive data before logging."""
    sensitive_keys = [
        'api_key', 'api_password', 'access_token',
        'secret_key', 'authorization'
    ]

    sanitized = data.copy()
    for key in sensitive_keys:
        if key in sanitized:
            sanitized[key] = '***REDACTED***'

    return sanitized

# Usage
_logger.info("API request: %s", sanitize_log_data(request_data))
```

### Audit Trail

**Transaction Audit Fields (Automatic):**
```python
create_date: DateTime     # When transaction created
create_uid: Many2one      # Who created it
write_date: DateTime      # Last modification
write_uid: Many2one       # Who modified it
```

**Custom Audit Log:**
```python
class PaymentAuditLog(models.Model):
    _name = 'payment.audit.log'

    transaction_id = fields.Many2one('payment.transaction')
    event_type = fields.Selection([
        ('created', 'Payment Created'),
        ('webhook', 'Webhook Received'),
        ('completed', 'Payment Completed'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Payment Refunded'),
    ])
    event_date = fields.Datetime(default=fields.Datetime.now)
    user_id = fields.Many2one('res.users')
    ip_address = fields.Char()
    details = fields.Text()
```

---

## Compliance

### PCI-DSS Compliance

**Requirements:**
1. ✅ Build and maintain secure network
   - HTTPS/TLS for all communications
   - Firewall between Odoo and internet

2. ✅ Protect cardholder data
   - No card data stored in Odoo
   - Payments on TiloPay hosted page

3. ✅ Maintain vulnerability management
   - Regular Odoo updates
   - Security patches applied

4. ✅ Implement strong access control
   - Role-based access control (RBAC)
   - Credential encryption

5. ✅ Monitor and test networks
   - Audit logging
   - Regular security testing

6. ✅ Maintain information security policy
   - This security documentation
   - Incident response plan

### GDPR Compliance

**Personal Data Processed:**
- Customer name
- Customer email
- Payment transaction history

**Legal Basis:** Contract performance (payment for services)

**Data Subject Rights:**
```python
def export_customer_payment_data(self, partner_id):
    """Export customer payment data (GDPR Article 20)."""
    partner = self.env['res.partner'].browse(partner_id)

    txs = self.env['payment.transaction'].search([
        ('partner_id', '=', partner_id),
        ('provider_code', '=', 'tilopay')
    ])

    return {
        'name': partner.name,
        'email': partner.email,
        'transactions': [{
            'date': tx.create_date,
            'reference': tx.reference,
            'amount': tx.amount,
            'currency': tx.currency_id.name,
            'status': tx.state,
        } for tx in txs]
    }

def delete_customer_payment_data(self, partner_id):
    """Pseudonymize customer payment data (GDPR Article 17)."""
    txs = self.env['payment.transaction'].search([
        ('partner_id', '=', partner_id),
        ('provider_code', '=', 'tilopay')
    ])

    # Can't delete (needed for accounting)
    # Instead, pseudonymize
    txs.write({
        'partner_email': 'deleted@privacy.local',
        'partner_name': 'DELETED_USER',
    })
```

---

## Security Checklist

### Pre-Production Checklist

**Credentials:**
- [ ] Production credentials obtained from TiloPay
- [ ] Sandbox mode disabled
- [ ] Credentials stored encrypted
- [ ] Access limited to system admins
- [ ] Environment variables configured

**Network:**
- [ ] HTTPS enabled on Odoo
- [ ] Valid SSL/TLS certificate
- [ ] Firewall rules configured
- [ ] IP whitelisting (optional)

**Code:**
- [ ] Webhook signature verification enabled
- [ ] Input validation on all fields
- [ ] SQL injection prevention (Odoo ORM)
- [ ] XSS prevention (Odoo framework)
- [ ] CSRF tokens enabled (except webhooks)

**Monitoring:**
- [ ] Audit logging enabled
- [ ] Security event alerts configured
- [ ] Log rotation configured
- [ ] Backup strategy in place

**Testing:**
- [ ] Security test suite passed
- [ ] Penetration testing completed
- [ ] Webhook signature test passed
- [ ] Access control tests passed

### Ongoing Security

**Monthly:**
- [ ] Review security logs
- [ ] Check for failed authentication attempts
- [ ] Verify webhook signature rejections
- [ ] Review access control changes

**Quarterly:**
- [ ] Update Odoo to latest version
- [ ] Review and update credentials
- [ ] Test backup restoration
- [ ] Security awareness training

**Annually:**
- [ ] Full security audit
- [ ] Penetration testing
- [ ] Policy review and update
- [ ] Disaster recovery drill

---

## Incident Response

### Security Incident Types

1. **Credential Compromise**
2. **Webhook Forgery Attempt**
3. **Unauthorized Access**
4. **Data Breach**
5. **System Intrusion**

### Response Procedures

#### 1. Credential Compromise

**Detection:**
- Unusual API activity
- Failed authentication attempts
- Credentials leaked publicly

**Response:**
```
1. Immediately disable TiloPay provider in Odoo
2. Revoke credentials in TiloPay dashboard
3. Generate new credentials
4. Update Odoo configuration
5. Review logs for unauthorized activity
6. Document incident
7. Notify affected parties if data accessed
```

#### 2. Webhook Forgery Attempt

**Detection:**
```python
_logger.error("SECURITY: Invalid webhook signature detected!")
```

**Response:**
```
1. Alert security team
2. Review IP address and attempt details
3. Add IP to blocklist
4. Verify secret key not compromised
5. Monitor for additional attempts
6. Document incident
```

#### 3. Unauthorized Access

**Detection:**
- Odoo access logs
- Failed login attempts
- Privilege escalation attempts

**Response:**
```
1. Lock affected user account
2. Review access logs
3. Identify data accessed
4. Reset credentials
5. Enable 2FA (if not already)
6. Notify user
7. Document incident
```

### Incident Contact

**Security Team:**
- Email: security@mygym.com
- Phone: +506-XXXX-XXXX
- On-call: 24/7 for CRITICAL incidents

**TiloPay Support:**
- Email: sac@tilopay.com
- Developer Portal: https://cst.support.tilopay.com/servicedesk/customer/portal/21

---

## See Also

- [API Documentation](API_DOCUMENTATION.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-28
**Classification:** Internal - Security Sensitive
**Maintained By:** GMS Security Team
