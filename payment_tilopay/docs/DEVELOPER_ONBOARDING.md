# TiloPay Payment Gateway - Developer Onboarding Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-28
**Estimated Time:** 2-4 hours

---

## Welcome!

This guide will help you get started with developing and maintaining the TiloPay Payment Gateway module for Odoo 19. By the end, you'll understand the architecture, be able to make code changes, and run tests.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Environment Setup](#development-environment-setup)
3. [Understanding the Codebase](#understanding-the-codebase)
4. [Making Your First Change](#making-your-first-change)
5. [Running Tests](#running-tests)
6. [Common Development Tasks](#common-development-tasks)
7. [Code Standards](#code-standards)
8. [Debugging Tips](#debugging-tips)
9. [Contributing](#contributing)

---

## Prerequisites

### Required Knowledge

Before starting, you should be familiar with:

- **Python 3.10+**: Core language used
- **Odoo Framework**: Models, views, controllers
- **PostgreSQL**: Database operations
- **Git**: Version control
- **REST APIs**: HTTP, JSON, authentication
- **Web Development**: HTML, JavaScript basics

### Recommended Reading

1. **Odoo Documentation**
   - https://www.odoo.com/documentation/19.0/

2. **Payment Module Guide**
   - https://www.odoo.com/documentation/19.0/developer/howtos/payment_provider.html

3. **TiloPay API Docs**
   - https://tilopay.com/documentacion

### Time Investment

- **Beginner**: 4-6 hours to understand basics
- **Intermediate**: 2-3 hours to start contributing
- **Advanced**: 1-2 hours to deep dive

---

## Development Environment Setup

### Step 1: Install Odoo 19

```bash
# Clone Odoo repository
git clone https://github.com/odoo/odoo.git --depth 1 --branch 19.0 ~/odoo19

# Install Python dependencies
cd ~/odoo19
pip3 install -r requirements.txt

# Install additional dependencies for TiloPay
pip3 install requests cryptography
```

### Step 2: Create Development Database

```bash
# Create PostgreSQL database
createdb gms_dev

# Initialize Odoo database
~/odoo19/odoo-bin -c odoo.conf -d gms_dev -i base --stop-after-init
```

### Step 3: Clone Payment TiloPay Module

```bash
# Navigate to addons directory
cd ~/odoo19/addons

# Clone or copy payment_tilopay module
git clone <repo-url> payment_tilopay

# OR copy from existing location
cp -r /path/to/payment_tilopay ./
```

### Step 4: Install Module

```bash
# Start Odoo in development mode
~/odoo19/odoo-bin -c odoo.conf -d gms_dev --dev=all

# Navigate to: Apps > Update Apps List
# Search: "TiloPay"
# Click: Install
```

### Step 5: Configure Test Credentials

```bash
# In Odoo UI:
# Accounting > Configuration > Payment Providers > TiloPay

# Use sandbox credentials:
API Key:      6609-5850-8330-8034-3464
API User:     lSrT45
API Password: Zlb8H9
Environment:  ☑ Use Sandbox
```

### Step 6: Verify Installation

```bash
# In Odoo shell
~/odoo19/odoo-bin shell -c odoo.conf -d gms_dev

>>> env = api.Environment(cr, uid, {})
>>> provider = env['payment.provider'].search([('code', '=', 'tilopay')])
>>> print(provider.name)
TiloPay
>>> print(provider.state)
enabled
```

---

## Understanding the Codebase

### Directory Structure

```
payment_tilopay/
│
├── __init__.py                 # Module entry point
├── __manifest__.py             # Module metadata and dependencies
│
├── models/                     # Business logic
│   ├── __init__.py
│   ├── tilopay_api_client.py           # [150 lines] API wrapper
│   ├── tilopay_payment_provider.py     # [263 lines] Provider config
│   ├── tilopay_payment_transaction.py  # [459 lines] Transaction mgmt
│   └── account_move.py                 # [206 lines] Invoice integration
│
├── controllers/                # HTTP endpoints
│   ├── __init__.py
│   └── tilopay_webhook.py              # [216 lines] Webhook handler
│
├── views/                      # UI definitions
│   ├── payment_provider_views.xml      # Provider configuration form
│   ├── payment_transaction_views.xml   # Transaction list/form
│   └── portal_invoice_views.xml        # Member portal views
│
├── data/                       # Default data
│   └── payment_provider_data.xml       # Default provider record
│
├── security/                   # Access control
│   └── ir.model.access.csv             # Model permissions
│
├── static/                     # Frontend assets
│   └── src/
│       └── js/
│           └── payment_form.js         # Client-side logic
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── common.py                       # Test utilities
│   ├── test_tilopay_api_client.py
│   ├── test_tilopay_payment_provider.py
│   ├── test_tilopay_payment_transaction.py
│   └── test_tilopay_webhook.py
│
└── docs/                       # Documentation
    ├── API_DOCUMENTATION.md
    ├── ARCHITECTURE.md
    ├── SECURITY.md
    ├── TROUBLESHOOTING.md
    ├── DEVELOPER_ONBOARDING.md (this file)
    └── CONFIGURATION.md
```

### Code Flow Overview

**Payment Creation Flow:**
```
1. User clicks "Pay Now" on invoice
   ↓
2. account_move.action_pay_online()
   ↓
3. Create payment.transaction record
   ↓
4. payment_transaction._tilopay_create_payment()
   ↓
5. payment_provider._tilopay_get_api_client()
   ↓
6. tilopay_api_client.create_payment()
   ↓
7. HTTP POST to TiloPay API
   ↓
8. Store payment_id and payment_url
   ↓
9. Redirect user to TiloPay payment page
```

**Webhook Processing Flow:**
```
1. TiloPay sends POST to /payment/tilopay/webhook
   ↓
2. tilopay_webhook_controller.tilopay_webhook()
   ↓
3. Verify signature (CRITICAL)
   ↓
4. Find payment.transaction by payment_id
   ↓
5. payment_transaction._tilopay_process_notification()
   ↓
6. Update transaction state
   ↓
7. payment_transaction._tilopay_update_invoice_payment()
   ↓
8. Mark invoice as paid
   ↓
9. Trigger e-invoice generation
```

### Key Files Deep Dive

#### 1. tilopay_api_client.py

**Purpose:** Low-level HTTP wrapper for TiloPay API

**Key Methods:**
- `__init__()`: Initialize and authenticate
- `create_payment()`: Create payment request
- `get_payment_status()`: Query payment status
- `verify_webhook_signature()`: Security validation

**When to Modify:**
- Adding new API endpoints
- Changing authentication logic
- Adding request/response logging

**Example:**
```python
# Adding a new API method
def get_payment_details(self, payment_id):
    """Get detailed payment information."""
    response = self.session.get(
        f"{self.base_url}/payments/{payment_id}/details"
    )
    response.raise_for_status()
    return response.json()
```

#### 2. tilopay_payment_provider.py

**Purpose:** Odoo model for provider configuration

**Key Methods:**
- `_tilopay_get_api_client()`: Factory for API client
- `_tilopay_get_enabled_payment_methods()`: Configuration helper
- `action_test_tilopay_connection()`: Admin test action

**When to Modify:**
- Adding new configuration fields
- Adding new payment methods
- Changing credential validation

**Example:**
```python
# Adding a new payment method
tilopay_enable_transfer = fields.Boolean(
    string='Enable Bank Transfer',
    default=False,
    help="Allow customers to pay via bank transfer"
)

def _tilopay_get_enabled_payment_methods(self):
    methods = super()._tilopay_get_enabled_payment_methods()
    if self.tilopay_enable_transfer:
        methods.append('transfer')
    return methods
```

#### 3. tilopay_payment_transaction.py

**Purpose:** Transaction lifecycle management

**Key Methods:**
- `_tilopay_create_payment()`: Initialize payment
- `_tilopay_process_notification()`: Handle webhooks
- `_tilopay_update_invoice_payment()`: Invoice integration

**When to Modify:**
- Changing payment flow
- Adding transaction fields
- Customizing webhook processing

**Example:**
```python
# Adding custom transaction metadata
tilopay_customer_ip = fields.Char(
    string='Customer IP Address',
    readonly=True,
    help="IP address of customer who initiated payment"
)

def _tilopay_create_payment(self):
    # Store customer IP
    if request:
        self.tilopay_customer_ip = request.httprequest.remote_addr

    return super()._tilopay_create_payment()
```

#### 4. tilopay_webhook.py

**Purpose:** HTTP controller for webhooks

**Key Methods:**
- `tilopay_webhook()`: Process webhook POST
- `tilopay_return()`: Handle customer return

**When to Modify:**
- Changing webhook validation
- Adding custom webhook events
- Customizing return page

**Example:**
```python
# Adding custom webhook event handling
if payload.get('event') == 'payment.pending':
    # Send notification to customer
    tx.partner_id.message_post(
        body=_("Your payment is being processed...")
    )
```

---

## Making Your First Change

Let's add a simple feature: logging the payment method used.

### Step 1: Add Log Statement

**File:** `models/tilopay_payment_transaction.py`

```python
def _tilopay_process_notification(self, notification_data):
    """Process webhook notification from TiloPay."""
    # ... existing code ...

    payment_method = data.get('payment_method')

    # ADD THIS:
    _logger.info(
        "Payment completed via %s for transaction %s",
        payment_method,
        self.reference
    )

    # ... rest of existing code ...
```

### Step 2: Test Your Change

```bash
# Restart Odoo to load changes
~/odoo19/odoo-bin -c odoo.conf -d gms_dev

# Trigger a test webhook
curl -X POST http://localhost:8069/payment/tilopay/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "payment.completed", "payment_id": "test_123", "data": {"payment_method": "sinpe"}}'

# Check logs
tail -f odoo.log | grep "Payment completed via"
```

### Step 3: Verify in UI

1. Create test invoice
2. Click "Pay Now"
3. Complete payment (or simulate webhook)
4. Check logs for your message

---

## Running Tests

### Test Structure

```
tests/
├── common.py                   # Shared test utilities
├── test_tilopay_api_client.py  # API client tests
├── test_tilopay_payment_provider.py
├── test_tilopay_payment_transaction.py
└── test_tilopay_webhook.py
```

### Run All Tests

```bash
# Run all TiloPay tests
~/odoo19/odoo-bin -c odoo.conf -d gms_dev \
  --test-tags=tilopay \
  --stop-after-init
```

### Run Specific Test

```bash
# Run only API client tests
~/odoo19/odoo-bin -c odoo.conf -d gms_dev \
  --test-tags=tilopay.test_tilopay_api_client \
  --stop-after-init
```

### Run Single Test Method

```bash
# Run specific test method
~/odoo19/odoo-bin -c odoo.conf -d gms_dev \
  --test-tags=tilopay.test_tilopay_api_client.TestTiloPayAPIClient.test_create_payment \
  --stop-after-init
```

### Writing Tests

```python
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install', 'tilopay')
class TestTiloPayCustom(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env['payment.provider'].create({
            'name': 'TiloPay Test',
            'code': 'tilopay',
            'state': 'test',
            'tilopay_api_key': 'test_key',
            'tilopay_api_user': 'test_user',
            'tilopay_api_password': 'test_pass',
        })

    def test_my_feature(self):
        """Test my awesome new feature."""
        # Arrange
        tx = self.env['payment.transaction'].create({
            'provider_id': self.provider.id,
            'amount': 100.00,
            'currency_id': self.env.ref('base.USD').id,
            'reference': 'TEST-001',
        })

        # Act
        result = tx.my_new_method()

        # Assert
        self.assertEqual(result, expected_value)
```

---

## Common Development Tasks

### Task 1: Add New Configuration Field

**Requirement:** Add "Enable installment payments" option

```python
# 1. Add field to model
# File: models/tilopay_payment_provider.py

tilopay_enable_installments = fields.Boolean(
    string='Enable Installment Payments',
    default=False,
    help="Allow customers to pay in installments (Tasa Cero)"
)

# 2. Add to view
# File: views/payment_provider_views.xml

<field name="tilopay_enable_installments"/>

# 3. Update module
# Click: Apps > Payment TiloPay > Upgrade
```

### Task 2: Add New Payment Method

**Requirement:** Support "Yappy" payment method

```python
# 1. Add field to provider
tilopay_enable_yappy = fields.Boolean(
    string='Enable Yappy',
    default=False,
)

# 2. Update payment methods helper
def _tilopay_get_enabled_payment_methods(self):
    methods = super()._tilopay_get_enabled_payment_methods()
    if self.tilopay_enable_yappy:
        methods.append('yappy')
    return methods

# 3. Add to transaction model
tilopay_payment_method = fields.Selection(
    selection_add=[('yappy', 'Yappy')],
)

# 4. Update views
# 5. Test thoroughly
```

### Task 3: Add Custom Logging

**Requirement:** Log all API requests for debugging

```python
# File: models/tilopay_api_client.py

def _make_request(self, method, endpoint, **kwargs):
    """Make authenticated API request."""
    url = f"{self.base_url}{endpoint}"

    # ADD LOGGING
    _logger.debug(
        "TiloPay API Request: %s %s\nHeaders: %s\nBody: %s",
        method, url,
        self.session.headers,
        kwargs.get('json', {})
    )

    response = self.session.request(method, url, **kwargs)

    # ADD LOGGING
    _logger.debug(
        "TiloPay API Response: %d\nBody: %s",
        response.status_code,
        response.text
    )

    return response
```

### Task 4: Add Email Notification

**Requirement:** Email customer when payment completes

```python
# File: models/tilopay_payment_transaction.py

def _tilopay_process_notification(self, notification_data):
    # ... existing code ...

    if event == 'payment.completed' and status == 'approved':
        self._set_done()
        self._tilopay_update_invoice_payment()

        # ADD EMAIL NOTIFICATION
        self._send_payment_confirmation_email()

def _send_payment_confirmation_email(self):
    """Send payment confirmation email to customer."""
    self.ensure_one()

    template = self.env.ref('payment_tilopay.payment_confirmation_email')
    template.send_mail(self.id, force_send=True)
```

---

## Code Standards

### Python Style Guide

Follow **PEP 8** and **Odoo Guidelines**:

```python
# Good
def _tilopay_create_payment(self):
    """Create payment with TiloPay gateway."""
    provider = self.provider_id
    client = provider._tilopay_get_api_client()

    response = client.create_payment(
        amount=self.amount,
        currency=self.currency_id.name,
        reference=self.reference
    )

    return response

# Bad
def CreatePayment(self):
    p=self.provider_id
    c=p._tilopay_get_api_client()
    r=c.create_payment(amount=self.amount,currency=self.currency_id.name,reference=self.reference)
    return r
```

### Naming Conventions

```python
# Models: CamelCase
class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

# Methods: snake_case with prefix
def _tilopay_create_payment(self):  # Private method
def action_tilopay_refresh_status(self):  # Action (button)

# Fields: snake_case
tilopay_payment_id = fields.Char()

# Constants: UPPER_CASE
TILOPAY_SANDBOX_URL = "https://sandbox.tilopay.com/api/v1"
```

### Documentation

**Every method needs a docstring:**

```python
def _tilopay_process_notification(self, notification_data):
    """
    Process webhook notification from TiloPay.

    Args:
        notification_data (dict): Webhook payload containing:
            - event: Event type (payment.completed, etc.)
            - payment_id: TiloPay payment ID
            - data: Payment details

    Returns:
        None

    Raises:
        ValidationError: If notification data is invalid

    Side Effects:
        - Updates transaction state
        - Triggers invoice confirmation
        - Sends customer email
    """
```

### Logging

```python
# Use appropriate log levels
_logger.critical("System failure!")     # System is unusable
_logger.error("Payment failed: %s", e)  # Error conditions
_logger.warning("Duplicate webhook")    # Warning conditions
_logger.info("Payment created")         # Informational
_logger.debug("API response: %s", data) # Debug (dev only)
```

### Security

```python
# NEVER log sensitive data
_logger.info("API Key: %s", api_key)  # ❌ BAD

# Sanitize logs
_logger.info("Using API key: %s***", api_key[:5])  # ✅ OK

# Always validate input
if not payment_id:
    raise ValidationError(_("Payment ID is required"))

# Use parameterized queries (Odoo ORM does this automatically)
tx = self.search([('reference', '=', reference)])  # ✅ Safe
```

---

## Debugging Tips

### Enable Developer Mode

```
Settings > Activate Developer Mode
```

or add `?debug=1` to URL

### Use Odoo Shell

```bash
~/odoo19/odoo-bin shell -c odoo.conf -d gms_dev

>>> env = api.Environment(cr, uid, {})
>>> tx = env['payment.transaction'].browse(123)
>>> print(tx.state)
>>> tx._tilopay_create_payment()
```

### Python Debugger (pdb)

```python
def _tilopay_create_payment(self):
    import pdb; pdb.set_trace()  # Breakpoint
    # Code execution will pause here
    provider = self.provider_id
```

### View Database

```bash
psql gms_dev

gms_dev=# SELECT * FROM payment_transaction WHERE provider_code = 'tilopay';
gms_dev=# SELECT tilopay_payment_id, state FROM payment_transaction;
```

### Check Logs

```bash
# Real-time log monitoring
tail -f odoo.log

# Filter for TiloPay
tail -f odoo.log | grep -i tilopay

# Search for errors
grep -i "error.*tilopay" odoo.log
```

### Browser DevTools

```javascript
// In browser console
// Inspect JavaScript errors
// Monitor network requests to webhook endpoint
```

---

## Contributing

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature/add-yappy-support

# 2. Make changes
# ... edit files ...

# 3. Run tests
~/odoo19/odoo-bin -c odoo.conf -d gms_dev --test-tags=tilopay --stop-after-init

# 4. Commit changes
git add models/tilopay_payment_provider.py
git commit -m "feat: Add Yappy payment method support"

# 5. Push to remote
git push origin feature/add-yappy-support

# 6. Create pull request
# ... via GitHub/GitLab ...
```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Add/update tests
- `chore`: Maintenance

**Example:**
```
feat: Add Yappy payment method support

- Add tilopay_enable_yappy field to provider
- Update payment methods helper
- Add Yappy to transaction selection
- Update views and documentation

Closes #42
```

### Code Review Checklist

Before submitting PR:

- [ ] Code follows style guide
- [ ] All methods have docstrings
- [ ] Tests pass (`--test-tags=tilopay`)
- [ ] No sensitive data in logs
- [ ] Security considerations addressed
- [ ] Documentation updated
- [ ] Manual testing completed

---

## Next Steps

### Week 1: Learning
- [ ] Read all documentation
- [ ] Set up development environment
- [ ] Run existing tests
- [ ] Make small change and test

### Week 2: Understanding
- [ ] Read through all model files
- [ ] Trace payment creation flow
- [ ] Trace webhook processing flow
- [ ] Review security mechanisms

### Week 3: Contributing
- [ ] Pick a simple bug/feature
- [ ] Implement and test
- [ ] Submit pull request
- [ ] Incorporate review feedback

### Ongoing
- [ ] Monitor #tilopay-dev Slack channel
- [ ] Participate in code reviews
- [ ] Help with documentation
- [ ] Mentor new developers

---

## Resources

### Documentation
- [API Documentation](API_DOCUMENTATION.md)
- [Architecture](ARCHITECTURE.md)
- [Security](SECURITY.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Configuration](CONFIGURATION.md)

### External Links
- [Odoo Developer Docs](https://www.odoo.com/documentation/19.0/developer.html)
- [TiloPay API Docs](https://tilopay.com/documentacion)
- [Python Requests Docs](https://requests.readthedocs.io/)

### Team Contacts
- **Tech Lead:** lead@mygym.com
- **Code Reviews:** #code-review on Slack
- **Questions:** #tilopay-dev on Slack

---

**Welcome to the team! Happy coding!**

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-28
**Maintained By:** GMS Development Team
