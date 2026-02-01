# Epic 002: Payment Gateway Integration (TiloPay)

**Status:** 🔄 In Progress - Investigation & Architecture Phase
**Priority:** HIGH
**Business Value:** Automate payment processing for 300+ gym members
**Estimated Effort:** 90-120 hours
**Created:** 2025-12-28

---

## Executive Summary

Integrate TiloPay payment gateway to enable automated online payment processing for gym memberships, subscriptions, and services. This will eliminate manual payment reconciliation, improve cash flow, reduce administrative overhead, and enhance member experience with instant payment confirmations.

### Business Impact

**Current State:**
- 300 active paying members
- ₡15M monthly revenue (₡180M annually)
- 8-10 hours/month spent on manual payment reconciliation
- Manual SINPE Móvil transaction tracking
- Delayed payment confirmations

**Target State:**
- Automated payment processing (SINPE Móvil + Cards)
- Payment confirmations via redirect returns (industry-standard pattern)
- Automatic invoice generation and e-invoicing
- Zero manual reconciliation time
- Improved member portal experience

**ROI Analysis:**
- **Cost:** ₡247,500/month (negotiated rates: 1.0% SINPE + 3.5% cards)
- **Savings:** ₡50,000/month labor + improved retention
- **Break-even:** Immediate (automation benefits exceed costs)
- **Additional Benefits:** Improved cash flow, reduced errors, better member experience

---

## Research Summary

### Payment Gateway Options Analyzed

| Provider | SINPE Fee | Card Fee | Odoo Module | Version | Cost | Recommendation |
|----------|-----------|----------|-------------|---------|------|----------------|
| **TiloPay** | 1.5% (negotiate to 1.0%) | 3.9% (negotiate to 3.5%) | ✅ Available | v18.0 | $57 USD | ✅ **RECOMMENDED** |
| ONVO Pay | 2.0% + ₡175 | 4.25% | ✅ Available | v15.0 | $267 USD | ❌ More expensive, older |

**Decision: TiloPay** - Lower fees, modern Odoo v18 module available, better documentation, active support.

### TiloPay Technical Overview

**Official Resources:**
- Developer Portal: https://tilopay.com/developers
- Documentation: https://tilopay.com/documentacion
- SDK Documentation: https://app.tilopay.com/sdk/documentation.pdf
- Support: sac@tilopay.com
- Developer Support: https://cst.support.tilopay.com/servicedesk/customer/portal/21

**Authentication Credentials:**
- API Key (Production): Obtained from TiloPay Account > Checkout
- API User: Username for API access
- API Password: Password for API access
- Merchant Code: Merchant identification (used in some integrations)
- Secret Key: Signing key for security (used in some integrations)

**Sandbox Test Credentials:**
```
API Key:  [REDACTED - use environment variable TILOPAY_API_KEY]
API User: [REDACTED - use environment variable TILOPAY_API_USER]
API Password: [REDACTED - use environment variable TILOPAY_API_PASSWORD]
```

**Supported Payment Methods:**
- SINPE Móvil (Costa Rica instant payments)
- Credit/Debit Cards (Visa, Mastercard, American Express)
- Yappy (Panama - if needed for expansion)
- Tasa Cero BAC Credomatic (installment plans)

**Existing Odoo Module Reference:**
- **Module 1:** "Tilopay Payment Connector" (bi_tilopay_payment_acquire) - v18.0, $57.39 USD
  - 212 lines of code
  - Depends on: sale_management, website_sale, mail, account, website
  - OPL-1 license (proprietary)
  - Features: Real-time auth, automated reconciliation, multi-currency

- **Module 2:** "TILOPAY PAYMENT GATEWAY" (payment_tilopay) - v17.0
  - Similar features, earlier version

**Note:** These modules are paid/proprietary but serve as reference for understanding integration patterns. We will build our own custom module integrated with l10n_cr_einvoice.

---

## Architecture Design

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     GMS ODOO SYSTEM (v19)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Member Portal (Website)                      │  │
│  │  • View Invoices                                          │  │
│  │  • "Pay Now" Button → Redirect to TiloPay               │  │
│  │  • Payment Status Display                                │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │         payment.provider (TiloPay Extension)             │  │
│  │  • tilopay_api_client.py - API wrapper                  │  │
│  │  • tilopay_payment_provider.py - Provider model         │  │
│  │  • tilopay_payment_transaction.py - Transaction model   │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │      l10n_cr_einvoice (E-Invoicing Integration)          │  │
│  │  • account_move.py - Invoice extension                  │  │
│  │  • _onchange_payment_status() - Auto-confirm            │  │
│  │  • _generate_einvoice_on_payment() - Auto e-invoice     │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
└───────────────────────┼─────────────────────────────────────────┘
                        │
         ┌──────────────▼──────────────┐
         │    HTTP/HTTPS (TLS 1.2+)    │
         └──────────────┬──────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                    TILOPAY GATEWAY API                          │
├─────────────────────────────────────────────────────────────────┤
│  • POST /payments/create - Initiate payment                    │
│  • GET /payments/{id}/status - Check payment status            │
│  • Processes SINPE Móvil transactions                          │
│  • Processes Card transactions                                 │
│  • Redirects user to return_url with payment result            │
└───────────────────────┬─────────────────────────────────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  Costa Rica Banking System  │
         │  • SINPE Móvil Network      │
         │  • Card Processing Network  │
         └─────────────────────────────┘
```

### Data Flow: Member Makes Payment

```
1. Member clicks "Pay Now" on invoice in portal
   ↓
2. Odoo creates payment.transaction record (status: draft)
   ↓
3. Odoo calls TiloPay API: POST /payments/create
   Request: {
     "amount": 50000,
     "currency": "CRC",
     "reference": "INV/2025/0001",
     "customer_email": "member@example.com",
     "payment_methods": ["sinpe", "card"],
     "return_url": "https://gym.com/payment/return"
   }
   ↓
4. TiloPay returns payment_url and payment_id
   ↓
5. Odoo redirects member to TiloPay payment page
   ↓
6. Member completes payment (SINPE or Card)
   ↓
7. TiloPay processes payment
   ↓
8. TiloPay redirects member to return_url with payment result
   ↓
9. Odoo return URL handler receives redirect
   ↓
10. Extracts payment status from URL parameters
   ↓
11. Updates payment.transaction status → "done"
   ↓
12. Marks account.move (invoice) as "paid"
   ↓
13. Triggers e-invoice generation (l10n_cr_einvoice)
   ↓
14. Updates payment method + transaction ID on invoice
   ↓
15. Generates Costa Rica Hacienda v4.4 XML
   ↓
16. Sends e-invoice to member email
   ↓
17. Displays "Payment successful!" message to member
   ↓
18. Payment complete! ✅
```

### Database Schema

**New Models:**

```python
# payment_tilopay/models/tilopay_payment_provider.py
class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('tilopay', 'TiloPay')],
        ondelete={'tilopay': 'set default'}
    )

    tilopay_api_key = fields.Char(
        string='TiloPay API Key',
        required_if_provider='tilopay',
        groups='base.group_system'
    )

    tilopay_api_user = fields.Char(
        string='TiloPay API User',
        required_if_provider='tilopay',
        groups='base.group_system'
    )

    tilopay_api_password = fields.Char(
        string='TiloPay API Password',
        required_if_provider='tilopay',
        groups='base.group_system'
    )

    tilopay_merchant_code = fields.Char(
        string='Merchant Code',
        groups='base.group_system'
    )

    tilopay_secret_key = fields.Char(
        string='Secret Key',
        groups='base.group_system'
    )

    tilopay_use_sandbox = fields.Boolean(
        string='Use Sandbox',
        default=True
    )

    tilopay_enable_sinpe = fields.Boolean(
        string='Enable SINPE Móvil',
        default=True
    )

    tilopay_enable_cards = fields.Boolean(
        string='Enable Credit/Debit Cards',
        default=True
    )

# payment_tilopay/models/tilopay_payment_transaction.py
class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    tilopay_payment_id = fields.Char(
        string='TiloPay Payment ID',
        readonly=True
    )

    tilopay_payment_url = fields.Char(
        string='TiloPay Payment URL',
        readonly=True
    )

    tilopay_payment_method = fields.Selection([
        ('sinpe', 'SINPE Móvil'),
        ('card', 'Credit/Debit Card'),
        ('yappy', 'Yappy'),
    ], string='Payment Method Used', readonly=True)

    tilopay_transaction_id = fields.Char(
        string='Bank Transaction ID',
        readonly=True,
        help='Transaction ID from bank (e.g., SINPE transaction number)'
    )

    tilopay_raw_response = fields.Text(
        string='TiloPay Response',
        readonly=True,
        groups='base.group_system'
    )
```

**Extended Models:**

```python
# l10n_cr_einvoice/models/account_move.py
class AccountMove(models.Model):
    _inherit = 'account.move'

    # Existing fields...

    payment_transaction_ids = fields.One2many(
        'payment.transaction',
        'invoice_id',
        string='Payment Transactions'
    )

    has_online_payment = fields.Boolean(
        compute='_compute_has_online_payment',
        string='Has Online Payment'
    )

    def _compute_has_online_payment(self):
        for move in self:
            move.has_online_payment = bool(
                move.payment_transaction_ids.filtered(
                    lambda t: t.provider_code == 'tilopay'
                )
            )

    def action_pay_online(self):
        """Create TiloPay payment transaction and redirect to payment page."""
        self.ensure_one()

        # Create payment transaction
        transaction = self.env['payment.transaction'].create({
            'provider_id': self._get_tilopay_provider().id,
            'amount': self.amount_residual,
            'currency_id': self.currency_id.id,
            'reference': self.name,
            'invoice_id': self.id,
            'partner_id': self.partner_id.id,
        })

        # Initialize payment with TiloPay
        transaction._tilopay_create_payment()

        return {
            'type': 'ir.actions.act_url',
            'url': transaction.tilopay_payment_url,
            'target': 'self',
        }
```

---

## Implementation Phases

### Phase 1: Account Setup & Negotiation ⏸️ PENDING USER ACTION

**Objective:** Obtain TiloPay developer/merchant account with negotiated rates

**Tasks:**
1. Register for TiloPay developer account at https://tilopay.com/developers
2. Complete merchant onboarding process
3. Negotiate transaction fees:
   - Target: 1.0-1.25% for SINPE Móvil (standard: 1.5%)
   - Target: 3.5% for cards (standard: 3.9%)
4. Obtain production credentials:
   - API Key
   - API User
   - API Password
   - Merchant Code
5. Enable test mode initially

**Success Criteria:**
- ✅ TiloPay account active
- ✅ Production credentials obtained
- ✅ Transaction fees negotiated below standard rates
- ✅ Sandbox access confirmed working

**Dependencies:** None (user action required)
**Estimated Time:** 1-2 weeks (includes negotiation)

---

### Phase 2: Architecture & Module Structure ✅ IN PROGRESS

**Objective:** Design integration architecture and create module skeleton

**Tasks:**
1. ✅ Review TiloPay documentation and existing Odoo modules
2. ✅ Design system architecture and data flow
3. ✅ Create Epic 002 document (this document)
4. 🔄 Create module structure: `payment_tilopay/`
5. 🔄 Define Odoo models (payment.provider, payment.transaction extensions)
6. 🔄 Design API client interface
7. 🔄 Plan return URL handler structure
8. 🔄 Document integration points with l10n_cr_einvoice

**Success Criteria:**
- ✅ Architecture documented and approved
- 🔄 Module skeleton created with all files
- 🔄 Models defined (non-functional until Phase 3)
- 🔄 Integration points identified

**Dependencies:** None (no API credentials needed)
**Estimated Time:** 16-24 hours (documentation + skeleton code)

---

### Phase 3: API Client Implementation 🔒 BLOCKED (Needs Credentials)

**Objective:** Build TiloPay API client with authentication and payment methods

**Tasks:**
1. Create `tilopay_api_client.py` with:
   - Authentication (API Key, User, Password)
   - `create_payment()` method
   - `get_payment_status()` method
   - `cancel_payment()` method
   - `refund_payment()` method
2. Implement request/response handling
3. Add error handling and logging
4. Support sandbox vs production modes
5. Write unit tests for API client

**Success Criteria:**
- ✅ API client can authenticate with TiloPay
- ✅ Can create payment and get payment URL
- ✅ Can query payment status
- ✅ Error handling works correctly
- ✅ All methods have unit tests

**Dependencies:** Phase 1 (needs API credentials)
**Estimated Time:** 20-24 hours

---

### Phase 4: Payment Provider Model 🔒 BLOCKED (Needs Credentials)

**Objective:** Implement Odoo payment.provider and payment.transaction extensions

**Tasks:**
1. Extend `payment.provider` model:
   - Add TiloPay configuration fields
   - Implement `_tilopay_get_api_client()` method
   - Add validation for credentials
2. Extend `payment.transaction` model:
   - Add TiloPay-specific fields
   - Implement `_tilopay_create_payment()` method
   - Implement `_tilopay_process_notification()` method
   - Add state management (draft → pending → done/error)
3. Create views for configuration
4. Add security rules

**Success Criteria:**
- ✅ Can configure TiloPay provider in Odoo
- ✅ Can create payment transactions
- ✅ Transactions have correct status workflow
- ✅ UI shows payment configuration options

**Dependencies:** Phase 3
**Estimated Time:** 16-20 hours

---

### Phase 5: Return URL Handler 🔒 BLOCKED (Needs Credentials)

**Objective:** Build return URL endpoint to handle TiloPay redirect responses

**Tasks:**
1. Create HTTP controller: `/payment/tilopay/return`
2. Implement URL parameter validation and parsing
3. Extract payment result from redirect parameters
4. Update payment.transaction status based on result
5. Trigger invoice payment confirmation on success
6. Handle different payment states:
   - `approved` / `completed` - Payment successful
   - `failed` / `declined` - Payment failed
   - `cancelled` - User cancelled
   - `pending` - Processing (rare)
7. Add comprehensive logging
8. Display appropriate success/error message to user

**Success Criteria:**
- ✅ Return URL endpoint receives redirects
- ✅ URL parameter validation prevents tampering
- ✅ Payment status updates correctly
- ✅ Invoices auto-confirm on successful payment
- ✅ Failed/cancelled payments handled gracefully with clear messaging

**Dependencies:** Phase 4
**Estimated Time:** 12-16 hours

---

### Phase 6: Member Portal Integration 🔒 BLOCKED (Needs Credentials)

**Objective:** Add "Pay Now" functionality to member portal

**Tasks:**
1. Add "Pay Now" button to invoice portal view
2. Create payment confirmation page
3. Handle payment return URLs
4. Display payment status to members
5. Show payment method used (SINPE/Card)
6. Add payment history view
7. Test user experience flow

**Success Criteria:**
- ✅ Members can click "Pay Now" on invoices
- ✅ Redirects to TiloPay payment page
- ✅ Returns to portal with success/failure message
- ✅ Payment status displays correctly
- ✅ User experience is smooth and clear

**Dependencies:** Phase 5
**Estimated Time:** 12-16 hours

---

### Phase 7: E-Invoice Integration 🔒 BLOCKED (Needs Credentials)

**Objective:** Connect payment gateway with e-invoicing module

**Tasks:**
1. Extend `account_move` with payment transaction reference
2. Auto-update payment method on invoice from transaction:
   - SINPE Móvil → code "06"
   - Card → code "02"
3. Auto-populate transaction ID for SINPE payments
4. Trigger e-invoice generation on payment confirmation
5. Include payment details in XML v4.4 generation
6. Test full payment → e-invoice → email flow

**Success Criteria:**
- ✅ Invoices auto-update payment method from transaction
- ✅ SINPE transaction IDs captured correctly
- ✅ E-invoices generated immediately after payment
- ✅ XML includes correct payment method codes
- ✅ Members receive e-invoice via email

**Dependencies:** Phase 6 + l10n_cr_einvoice module
**Estimated Time:** 16-20 hours

---

### Phase 8: Testing & Quality Assurance 🔒 BLOCKED (Needs Credentials)

**Objective:** Comprehensive testing in sandbox environment

**Tasks:**
1. **Unit Tests:**
   - API client methods
   - Model validation
   - Return URL parsing
2. **Integration Tests:**
   - End-to-end payment flow
   - Return URL processing
   - E-invoice generation
3. **Manual Testing:**
   - SINPE Móvil payments (sandbox)
   - Card payments (sandbox)
   - Failed payment scenarios
   - Refund scenarios
   - Multiple concurrent payments
4. **Security Testing:**
   - Return URL parameter validation
   - Credential encryption
   - SQL injection prevention
   - XSS prevention
5. **Performance Testing:**
   - Concurrent payment handling
   - Return redirect response time
   - Database query optimization

**Success Criteria:**
- ✅ All unit tests pass (95%+ coverage)
- ✅ All integration tests pass
- ✅ Manual test scenarios completed
- ✅ No security vulnerabilities found
- ✅ Performance meets requirements (<2s response)

**Dependencies:** Phase 7
**Estimated Time:** 20-24 hours

---

### Phase 9: Production Deployment 🔒 BLOCKED (Needs Credentials)

**Objective:** Deploy to production with soft launch

**Tasks:**
1. **Pre-Deployment:**
   - Backup production database
   - Review all code changes
   - Update TiloPay return URLs (production)
   - Switch from sandbox to production credentials
2. **Deployment:**
   - Install `payment_tilopay` module
   - Configure TiloPay provider
   - Test with real ₡100 transaction
3. **Soft Launch:**
   - Enable for 5-10 test members only
   - Monitor for 1 week
   - Fix any issues discovered
4. **Full Rollout:**
   - Enable for all 300 members
   - Send announcement email
   - Update member portal with "Pay Online Now!" feature
   - Monitor closely for first month
5. **Post-Deployment:**
   - Track transaction success rate
   - Measure reconciliation time saved
   - Gather member feedback
   - Optimize based on usage patterns

**Success Criteria:**
- ✅ Module deployed without errors
- ✅ Test transactions successful
- ✅ Soft launch shows 100% success rate
- ✅ Full rollout completed
- ✅ All 300 members can pay online
- ✅ Zero manual reconciliation needed

**Dependencies:** Phase 8 + Production credentials
**Estimated Time:** 8-12 hours + 1 week monitoring

---

## Technical Specifications

### Module Structure

```
payment_tilopay/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── tilopay_api_client.py          # API wrapper
│   ├── tilopay_payment_provider.py    # payment.provider extension
│   ├── tilopay_payment_transaction.py # payment.transaction extension
│   └── account_move.py                 # Invoice integration
├── controllers/
│   ├── __init__.py
│   └── tilopay_return.py              # Return URL handler
├── views/
│   ├── payment_provider_views.xml      # Configuration UI
│   ├── payment_transaction_views.xml   # Transaction tracking UI
│   └── portal_invoice_views.xml        # Member portal "Pay Now"
├── data/
│   └── payment_provider_data.xml       # TiloPay provider record
├── security/
│   └── ir.model.access.csv             # Access control
├── static/
│   ├── description/
│   │   ├── icon.png
│   │   └── index.html
│   └── src/
│       ├── img/
│       │   └── tilopay_logo.png
│       └── js/
│           └── payment_form.js         # Client-side handling
└── tests/
    ├── __init__.py
    ├── test_tilopay_api_client.py
    ├── test_tilopay_payment_provider.py
    ├── test_tilopay_payment_transaction.py
    └── test_tilopay_return.py
```

### API Client Interface

```python
# payment_tilopay/models/tilopay_api_client.py

import requests
import json
import logging
from datetime import datetime
from werkzeug.urls import url_join

_logger = logging.getLogger(__name__)

class TiloPayAPIClient:
    """TiloPay API Client for payment processing."""

    SANDBOX_URL = "https://sandbox.tilopay.com/api/v1"
    PRODUCTION_URL = "https://api.tilopay.com/api/v1"

    def __init__(self, api_key, api_user, api_password, use_sandbox=True):
        """
        Initialize TiloPay API client.

        :param api_key: TiloPay API Key
        :param api_user: TiloPay API User
        :param api_password: TiloPay API Password
        :param use_sandbox: Use sandbox environment (default True)
        """
        self.api_key = api_key
        self.api_user = api_user
        self.api_password = api_password
        self.base_url = self.SANDBOX_URL if use_sandbox else self.PRODUCTION_URL
        self.session = requests.Session()
        self._authenticate()

    def _authenticate(self):
        """Authenticate with TiloPay API and get access token."""
        # Implementation: POST /auth/login
        # Store token in self.session.headers
        pass

    def create_payment(self, amount, currency, reference, customer_email,
                      payment_methods, return_url, **kwargs):
        """
        Create a payment with TiloPay.

        :param amount: Payment amount (integer, e.g., 50000 for ₡50,000)
        :param currency: Currency code (CRC)
        :param reference: Unique reference (e.g., invoice number)
        :param customer_email: Customer email address
        :param payment_methods: List of allowed methods ['sinpe', 'card']
        :param return_url: URL to redirect after payment (with result parameters)
        :return: dict with payment_id, payment_url, status
        """
        # Implementation: POST /payments/create
        pass

    def get_payment_status(self, payment_id):
        """
        Get current status of a payment.

        :param payment_id: TiloPay payment ID
        :return: dict with status, amount, payment_method, transaction_id
        """
        # Implementation: GET /payments/{payment_id}/status
        pass

    def cancel_payment(self, payment_id):
        """Cancel a pending payment."""
        # Implementation: POST /payments/{payment_id}/cancel
        pass

    def refund_payment(self, payment_id, amount=None, reason=None):
        """
        Refund a completed payment.

        :param payment_id: TiloPay payment ID
        :param amount: Amount to refund (None = full refund)
        :param reason: Refund reason
        """
        # Implementation: POST /payments/{payment_id}/refund
        pass
```

### Redirect URL Parameter Examples

**Payment Successful:**
```
https://gym.com/payment/return?
  payment_id=pay_abc123xyz
  &status=approved
  &amount=50000
  &currency=CRC
  &reference=INV/2025/0001
  &payment_method=sinpe
  &transaction_id=87654321
  &timestamp=2025-12-28T14:30:00Z
```

**Payment Failed:**
```
https://gym.com/payment/return?
  payment_id=pay_abc123xyz
  &status=failed
  &amount=50000
  &currency=CRC
  &reference=INV/2025/0001
  &payment_method=card
  &error_code=insufficient_funds
  &error_message=Fondos%20insuficientes
  &timestamp=2025-12-28T14:30:00Z
```

**Payment Cancelled:**
```
https://gym.com/payment/return?
  payment_id=pay_abc123xyz
  &status=cancelled
  &reference=INV/2025/0001
  &timestamp=2025-12-28T14:30:00Z
```

---

## Security Considerations

### Credential Protection
- ✅ Store API credentials in `ir.config_parameter` (encrypted)
- ✅ Never log API credentials
- ✅ Use `groups='base.group_system'` on sensitive fields
- ✅ Implement credential rotation capability

### Return URL Security
- ✅ Validate payment amounts match invoice amounts
- ✅ Check for replay attacks (timestamp validation)
- ✅ Use HTTPS only for return URLs
- ✅ Implement rate limiting on return URL endpoint
- ✅ Validate payment_id matches expected transaction

### Data Protection
- ✅ Never store full credit card numbers
- ✅ Store only last 4 digits for reference
- ✅ Comply with PCI-DSS by using TiloPay's hosted payment page
- ✅ Encrypt sensitive data at rest
- ✅ Use SSL/TLS for all API communications

### Access Control
- ✅ Restrict payment provider configuration to system admins
- ✅ Allow invoice managers to view transactions
- ✅ Members can only view their own payments
- ✅ Implement audit logging for all payment actions

---

## Testing Strategy

### Unit Tests
- API client authentication
- Payment creation request formatting
- Return URL parameter parsing and validation
- Error handling and exceptions
- Model validations

### Integration Tests
- Full payment flow (Odoo → TiloPay → Redirect Return → E-Invoice)
- Multiple payment methods (SINPE, Cards)
- Concurrent payment processing
- Failed payment handling
- Refund processing

### Manual Test Cases

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| **TC-001: SINPE Payment** | Member clicks "Pay Now" → Selects SINPE → Completes payment | Invoice marked paid, e-invoice sent, payment method "06" |
| **TC-002: Card Payment** | Member clicks "Pay Now" → Selects Card → Completes payment | Invoice marked paid, e-invoice sent, payment method "02" |
| **TC-003: Failed Payment** | Member clicks "Pay Now" → Payment fails | Transaction marked failed, invoice remains unpaid, error shown |
| **TC-004: Concurrent Payments** | Two members pay simultaneously | Both payments process correctly, no conflicts |
| **TC-005: Redirect Delay** | User returns to site after extended time | Payment status still updates correctly, no timeout errors |
| **TC-006: Parameter Tampering** | Return URL with modified payment amount | Parameter validation detects mismatch, payment not confirmed |
| **TC-007: Refund** | Admin initiates refund | Money returned, invoice marked as refunded |

---

## Success Metrics

### Technical Metrics
- **Payment Success Rate:** > 98%
- **Redirect Return Handling Time:** < 3 seconds
- **API Response Time:** < 1 second
- **Uptime:** > 99.5%
- **Test Coverage:** > 90%

### Business Metrics
- **Reconciliation Time:** Reduced from 8-10 hrs/month → 0 hours
- **Payment Confirmation Speed:** From 24-48 hours → < 5 minutes
- **Member Satisfaction:** > 90% satisfied with payment experience
- **Transaction Costs:** < 1.25% average (after negotiation)
- **Adoption Rate:** > 80% of members using online payments within 3 months

### Member Experience Metrics
- **Payment Completion Time:** < 3 minutes from invoice to confirmation
- **Failed Payment Rate:** < 2%
- **Support Tickets:** < 5 payment-related tickets per month
- **Mobile Payment Usage:** > 60% use SINPE Móvil

---

## Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **TiloPay API Downtime** | Low | High | Implement retry logic, queue payments, show clear error messages |
| **User Doesn't Return After Payment** | Low | Medium | Poll payment status as backup, add "Check Payment Status" button in portal |
| **Transaction Fee Negotiation Fails** | Medium | Medium | Have fallback rates, consider ONVO as alternative |
| **Member Adoption Low** | Low | Medium | Prominent "Pay Now" buttons, member education campaign |
| **Security Breach** | Very Low | Very High | Signature verification, audit logging, credential encryption |
| **Integration Bugs** | Medium | High | Comprehensive testing, phased rollout, monitoring |
| **Regulatory Changes** | Low | Medium | Stay updated on Hacienda requirements, flexible architecture |

---

## Dependencies & Prerequisites

### External Dependencies
- ✅ TiloPay merchant account (pending registration)
- ✅ Production API credentials (pending account approval)
- ✅ SSL certificate for production domain (for HTTPS return URLs)

### Internal Dependencies
- ✅ `l10n_cr_einvoice` module (fully implemented)
- ✅ `sale_subscription` module (for recurring payments)
- ✅ Member portal enabled and accessible
- ✅ Odoo v19 running in production

### Python Dependencies
```python
# Add to l10n_cr_einvoice/__manifest__.py:
'external_dependencies': {
    'python': [
        'requests',      # HTTP client for API calls
    ],
}
```

---

## Next Steps (Immediate Actions)

### What We Can Do NOW (Without API Credentials)

1. ✅ **Complete Epic 002 Documentation** (this document)
2. 🔄 **Create Module Skeleton:**
   - Create `payment_tilopay/` directory structure
   - Write `__manifest__.py` with dependencies
   - Create all model files (placeholder implementations)
   - Create controller files (placeholder implementations)
   - Create view XML files
3. 🔄 **Design & Document Architecture:**
   - Data flow diagrams (completed above)
   - Database schema (completed above)
   - API client interface (completed above)
4. 🔄 **Write Skeleton Code:**
   - Model definitions with fields and methods (non-functional)
   - Controller endpoints with documentation
   - View templates
5. 🔄 **Create Test Suite Structure:**
   - Test file structure
   - Test case documentation
   - Mock API responses for unit tests

### What We CANNOT Do (Requires API Credentials)

- ❌ Actual API client implementation (needs authentication)
- ❌ Return URL parameter validation (needs actual TiloPay redirect examples)
- ❌ Integration testing (needs sandbox access)
- ❌ Payment flow testing (needs test credentials)
- ❌ Production deployment

### User Action Required: Phase 1

**You need to:** Register for TiloPay account and obtain credentials

**Steps:**
1. Visit https://tilopay.com/developers
2. Click "Register" or "Sign Up"
3. Complete merchant onboarding form
4. Provide gym business information (RUC, business license, etc.)
5. Submit application
6. Wait for approval (typically 2-5 business days)
7. Once approved, navigate to Account > Checkout
8. Copy credentials:
   - API Key
   - API User
   - API Password
   - Merchant Code
9. **Negotiate fees via email to sac@tilopay.com:**
   - Subject: "Solicitud de Tarifas Preferenciales - Gimnasio con 300 Miembros"
   - Mention: ₡15M monthly volume, 300 active members
   - Request: 1.0-1.25% SINPE, 3.5% cards
   - Reference competing offers if needed

**Timeline:** Allow 1-2 weeks for approval + negotiation

---

## Budget Summary

### One-Time Costs
- TiloPay Odoo Module (reference): $57.39 USD (optional - we're building custom)
- Development Time: 90-120 hours @ internal rate
- Testing & QA: 20-24 hours

### Recurring Costs (Monthly)
**Standard Rates:**
- SINPE Móvil: 1.5% × ₡10.5M = ₡157,500
- Cards: 3.9% × ₡4.5M = ₡175,500
- **Total:** ₡333,000/month (₡3,996,000/year)

**Target Negotiated Rates:**
- SINPE Móvil: 1.0% × ₡10.5M = ₡105,000
- Cards: 3.5% × ₡4.5M = ₡157,500
- **Total:** ₡262,500/month (₡3,150,000/year)

**Savings vs Standard:** ₡70,500/month (₡846,000/year)

### ROI Analysis
- **Costs:** ₡262,500/month (transaction fees)
- **Savings:** ₡50,000/month (labor) + retention improvements
- **Net Impact:** Break-even with significant intangible benefits:
  - Instant payment confirmations
  - Improved member satisfaction
  - Reduced errors
  - Better cash flow visibility
  - Scalability for growth

---

## References & Resources

### TiloPay Official
- Developer Portal: https://tilopay.com/developers
- Documentation: https://tilopay.com/documentacion
- SDK Docs: https://app.tilopay.com/sdk/documentation.pdf
- Support: sac@tilopay.com
- Developer Support Portal: https://cst.support.tilopay.com/servicedesk/customer/portal/21

### Odoo Modules (Reference)
- TiloPay Payment Connector (v18): https://apps.odoo.com/apps/modules/18.0/bi_tilopay_payment_acquire
- TiloPay Payment Gateway (v17): https://apps.odoo.com/apps/modules/17.0/payment_tilopay

### Costa Rica Market Research
- Previous research: `_bmad-output/planning-artifacts/research/market-costa-rica-einvoicing-payment-research-2025-12-28.md`

### Technical References
- Odoo Payment Provider Documentation: https://www.odoo.com/documentation/19.0/developer/reference/backend/payment.html
- Odoo HTTP Controller Best Practices: https://www.odoo.com/documentation/19.0/developer/reference/backend/http.html

---

## Approval & Sign-Off

**Epic Owner:** Papu (User)
**Technical Lead:** Claude Sonnet 4.5 (AI Agent)
**Status:** ✅ Architecture Complete, Ready for User Action (Phase 1)

**Date Created:** 2025-12-28
**Last Updated:** 2025-12-28
**Version:** 1.0

---

**Next Action:** User to complete Phase 1 (TiloPay account registration) while AI agent continues with Phase 2 (module skeleton creation).

Once credentials are obtained, we can immediately proceed with Phases 3-9 since all groundwork will be prepared.
