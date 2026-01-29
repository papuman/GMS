# Tech-Spec: SINPE Móvil Payment Method Integration

**Created:** 2025-12-28
**Status:** Ready for Development
**Priority:** CRITICAL - Legal Compliance (Penalties up to 150%)
**Phase:** 1A - Critical Compliance

---

## Overview

### Problem Statement

Costa Rica's Ministry of Finance (Hacienda) requires payment method tracking in electronic invoices per Resolution MH-DGT-RES-0027-2024. SINPE Móvil (code "06") is MANDATORY for mobile payment transactions. Current implementation lacks payment method tracking entirely, resulting in:

- **Legal Risk**: Non-compliance penalties up to 150% of tax amount
- **Criminal Risk**: Potential criminal measures for repeated violations
- **Business Impact**: Cannot legally accept SINPE Móvil payments (84% of population uses it)
- **Competitive Disadvantage**: Cannot compete with compliant systems

**Market Context**: SINPE Móvil is Costa Rica's dominant payment method:
- 3 million active users
- 84% of population adoption
- 80% of interbank transfers
- Zero transaction fees for consumers

### Solution

Implement comprehensive payment method tracking system with:
1. Payment method catalog (5 methods as per v4.4 spec)
2. Payment method selection on invoices
3. XML v4.4 generation with payment method codes
4. Transaction ID tracking for SINPE Móvil
5. UI updates for method display
6. Payment gateway integration (TiloPay, ONVO Pay)
7. Backward compatibility for existing invoices

### Scope

**IN SCOPE**:
- ✅ Payment method catalog (01-Efectivo, 02-Tarjeta, 03-Cheque, 04-Transferencia, 06-SINPE Móvil)
- ✅ Payment method field on account.move model
- ✅ Payment method selection in invoice form
- ✅ XML generation updates for MedioPago tag
- ✅ Transaction ID field for SINPE Móvil
- ✅ Kanban badge display for payment method
- ✅ API integration framework (TiloPay, ONVO Pay)
- ✅ Migration script for existing invoices (default to "01-Efectivo")
- ✅ Validation rules (SINPE Móvil requires transaction ID)

**OUT OF SCOPE** (Future Phases):
- ❌ Full payment gateway transaction processing (Phase 4)
- ❌ Automated payment reconciliation
- ❌ Multiple payment methods per invoice
- ❌ Payment splitting/partial payments
- ❌ REP (Electronic Payment Receipt) document type (Phase 2)

---

## Context for Development

### Codebase Patterns

**Model Extension Pattern** (from `account_move.py`):
```python
class AccountMove(models.Model):
    _inherit = 'account.move'

    # Field definition pattern
    field_name = fields.Selection([
        ('value', 'Label'),
    ], string='Display Name', required=True, default='value')

    # Related field pattern
    related_field = fields.Selection(
        related='l10n_cr_einvoice_id.field',
        string='Display Name',
        store=True,
    )
```

**XML Generator Pattern** (from `xml_generator.py`):
```python
def _add_medio_pago(self, root, move):
    """Add payment method section to XML."""
    etree.SubElement(root, 'MedioPago').text = '01'  # Currently hardcoded
```

**Data Pattern** (from `data/document_types.xml`):
```xml
<odoo>
    <data noupdate="1">
        <record id="payment_method_efectivo" model="l10n_cr.payment.method">
            <field name="code">01</field>
            <field name="name">Efectivo</field>
        </record>
    </data>
</odoo>
```

### Files to Reference

**Models** (Must Read):
- `l10n_cr_einvoice/models/account_move.py:51-66` - action_post() auto-generation pattern
- `l10n_cr_einvoice/models/xml_generator.py:88` - _add_medio_pago() current implementation
- `l10n_cr_einvoice/models/einvoice_document.py:52-58` - document_type selection pattern

**Views** (Must Modify):
- `l10n_cr_einvoice/views/account_move_views.xml` - Invoice form view
- `l10n_cr_einvoice/views/einvoice_document_views.xml` - Kanban view with badges

**Data Files** (Must Create):
- `l10n_cr_einvoice/data/payment_methods.xml` - NEW FILE for catalog

**Manifest** (Must Update):
- `l10n_cr_einvoice/__manifest__.py:55-74` - Add payment_methods.xml to data list

### Technical Decisions

**Decision 1**: Payment Method Catalog as Master Data
- **Why**: Hacienda codes are fixed, won't change frequently
- **Implementation**: `l10n_cr.payment.method` model with noupdate="1"
- **Alternative Rejected**: Selection field (harder to extend, no descriptions)

**Decision 2**: Default Payment Method = "01" (Efectivo)
- **Why**: Most conservative choice for historical data
- **Implementation**: Migration script sets all NULL to "01"
- **Alternative Rejected**: Force user selection (breaks existing workflows)

**Decision 3**: SINPE Transaction ID Optional Initially
- **Why**: Phase in validation, give users time to adapt
- **Implementation**: Warning if missing, error after grace period (March 2026)
- **Alternative Rejected**: Immediate hard validation (too disruptive)

**Decision 4**: Payment Gateway Integration = Abstraction Layer
- **Why**: Support multiple gateways (TiloPay, ONVO Pay, future providers)
- **Implementation**: `l10n_cr.payment.gateway` abstract model
- **Alternative Rejected**: Hardcode TiloPay (limits future flexibility)

---

## Implementation Plan

### Tasks

#### Phase 1A.1: Payment Method Catalog (8 hours)
- [ ] **Task 1.1**: Create `l10n_cr.payment.method` model
  - Fields: `code` (Char, 2), `name` (Char), `description` (Text), `active` (Boolean), `requires_transaction_id` (Boolean)
  - Add to `models/__init__.py`
  - Create `models/payment_method.py`

- [ ] **Task 1.2**: Create payment method data file
  - File: `data/payment_methods.xml`
  - Records: 5 payment methods with Hacienda codes
  - Add to `__manifest__.py` data list (load BEFORE views)

- [ ] **Task 1.3**: Create security rules
  - Add to `security/ir.model.access.csv`
  - Permissions: all_users (read), accountant (write)

#### Phase 1A.2: Account Move Model Extension (12 hours)
- [ ] **Task 2.1**: Add payment method field to `account.move`
  - File: `models/account_move.py`
  - Field: `l10n_cr_payment_method_id` (Many2one to l10n_cr.payment.method)
  - Field: `l10n_cr_payment_transaction_id` (Char, 50) - for SINPE Móvil
  - Default: Compute from payment or "01"

- [ ] **Task 2.2**: Add validation method
  - Method: `_validate_payment_method_transaction_id()`
  - Logic: If payment_method code == "06" and no transaction_id → UserError
  - Hook: On invoice confirmation (`action_post`)

- [ ] **Task 2.3**: Add payment method to e-invoice document
  - File: `models/einvoice_document.py`
  - Add related fields from move_id
  - Display in form view

#### Phase 1A.3: XML Generator Updates (16 hours)
- [ ] **Task 3.1**: Update `_add_medio_pago()` method
  - File: `models/xml_generator.py:88`
  - Current: Hardcoded "01"
  - New: Use `move.l10n_cr_payment_method_id.code or '01'`

- [ ] **Task 3.2**: Add conditional transaction ID to XML
  - If SINPE Móvil (code "06") → Add `<NumeroTransaccion>` tag
  - XML structure per v4.4 spec:
    ```xml
    <MedioPago>06</MedioPago>
    <NumeroTransaccion>123456789</NumeroTransaccion>
    ```

- [ ] **Task 3.3**: Update all document type generators
  - Files: `_generate_factura_electronica()`, `_generate_tiquete_electronico()`, `_generate_nota_credito()`, `_generate_nota_debito()`
  - Ensure all call `_add_medio_pago()` with transaction ID support

#### Phase 1A.4: UI Updates (12 hours)
- [ ] **Task 4.1**: Update invoice form view
  - File: `views/account_move_views.xml`
  - Add payment method selection field
  - Add transaction ID field (visible only if SINPE Móvil selected)
  - Position: Below payment terms, above invoice lines

- [ ] **Task 4.2**: Update Kanban view badges
  - File: `views/einvoice_document_views.xml`
  - Add payment method badge with icon
  - Badge colors: SINPE=purple, Card=blue, Cash=green, Check=yellow, Transfer=orange
  - Bootstrap 5 classes: `badge bg-purple`, etc.

- [ ] **Task 4.3**: Update list/tree views
  - Add payment method column (optional field)
  - Add transaction ID column (visible for SINPE only)

#### Phase 1A.5: Payment Gateway Framework (16 hours)
- [ ] **Task 5.1**: Create abstract payment gateway model
  - File: `models/payment_gateway.py` (NEW)
  - Model: `l10n_cr.payment.gateway` (Abstract)
  - Methods: `process_payment()`, `verify_transaction()`, `get_transaction_status()`

- [ ] **Task 5.2**: Create TiloPay gateway implementation
  - File: `models/payment_gateway_tilopay.py` (NEW)
  - Model: `l10n_cr.payment.gateway.tilopay`
  - API: TiloPay REST API v2
  - Fees: 2% + $0.35 per transaction
  - Endpoint: https://app.tilopay.com/api/v2/

- [ ] **Task 5.3**: Create ONVO Pay gateway implementation
  - File: `models/payment_gateway_onvo.py` (NEW)
  - Model: `l10n_cr.payment.gateway.onvo`
  - API: ONVO Pay API v1
  - Fees: 1.5% per transaction
  - Endpoint: https://api.onvopay.com/v1/

- [ ] **Task 5.4**: Add gateway configuration to company settings
  - File: `models/res_company.py`
  - Fields: `l10n_cr_payment_gateway` (Selection), API credentials
  - Update `views/res_company_views.xml`

#### Phase 1A.6: Data Migration (8 hours)
- [ ] **Task 6.1**: Create migration script
  - File: `migrations/19.0.1.0.0/post-migration.py` (NEW)
  - Logic: Update all account.move records where payment_method_id is NULL
  - Set to: payment_method with code "01" (Efectivo)
  - Log: Count of records updated

- [ ] **Task 6.2**: Test migration on staging database
  - Backup test database
  - Run migration script
  - Verify all invoices have payment method
  - Verify XML regeneration works

#### Phase 1A.7: Testing (24 hours)
- [ ] **Task 7.1**: Unit tests for payment method model
  - File: `tests/test_payment_method.py` (NEW)
  - Test catalog creation
  - Test code uniqueness
  - Test active/inactive filtering

- [ ] **Task 7.2**: Unit tests for account.move validation
  - File: `tests/test_account_move_payment.py` (NEW)
  - Test SINPE Móvil without transaction ID → Error
  - Test other methods without transaction ID → Success
  - Test default payment method assignment

- [ ] **Task 7.3**: Integration tests for XML generation
  - File: `tests/test_xml_generator_payment.py` (NEW)
  - Test XML contains correct MedioPago code
  - Test SINPE Móvil includes NumeroTransaccion
  - Test all 5 payment methods generate valid XML

- [ ] **Task 7.4**: E2E test: Create invoice with SINPE Móvil
  - Create invoice
  - Set payment method = SINPE Móvil
  - Set transaction ID
  - Generate XML
  - Validate against XSD schema
  - Submit to Hacienda sandbox

- [ ] **Task 7.5**: UI tests
  - Test payment method dropdown displays all 5 methods
  - Test transaction ID field shows/hides based on selection
  - Test Kanban badge displays correct color
  - Test validation message displays correctly

### Acceptance Criteria

#### AC1: Payment Method Catalog Exists
**Given** I am a system administrator
**When** I navigate to Settings → Technical → Database Structure → Models
**Then** I should see `l10n_cr.payment.method` model
**And** the model should contain 5 records with codes: 01, 02, 03, 04, 06

#### AC2: Invoice Form Has Payment Method Selection
**Given** I am creating a new customer invoice in Costa Rica
**When** I open the invoice form
**Then** I should see a "Payment Method" dropdown field
**And** the dropdown should contain: Efectivo, Tarjeta, Cheque, Transferencia, SINPE Móvil
**And** the default value should be "Efectivo"

#### AC3: SINPE Móvil Requires Transaction ID
**Given** I have selected SINPE Móvil as the payment method
**When** I try to confirm the invoice without a transaction ID
**Then** I should receive an error: "Transaction ID is required for SINPE Móvil payments"
**And** the invoice should NOT be posted

#### AC4: Transaction ID Field Visibility
**Given** I am on the invoice form
**When** I select payment method = "Efectivo"
**Then** the transaction ID field should be hidden
**When** I change payment method to "SINPE Móvil"
**Then** the transaction ID field should appear

#### AC5: XML Contains Correct Payment Method Code
**Given** I have confirmed an invoice with payment method = "SINPE Móvil"
**When** the e-invoice XML is generated
**Then** the XML should contain `<MedioPago>06</MedioPago>`
**And** the XML should contain `<NumeroTransaccion>{transaction_id}</NumeroTransaccion>`

#### AC6: XML for Other Methods Does NOT Include Transaction ID
**Given** I have confirmed an invoice with payment method = "Tarjeta"
**When** the e-invoice XML is generated
**Then** the XML should contain `<MedioPago>02</MedioPago>`
**And** the XML should NOT contain `<NumeroTransaccion>` tag

#### AC7: Kanban View Shows Payment Method Badge
**Given** I am viewing the e-invoice Kanban view
**When** I see invoices with different payment methods
**Then** each card should display a colored badge with the payment method
**And** SINPE Móvil should show a purple badge
**And** Efectivo should show a green badge

#### AC8: Migration Updates Existing Invoices
**Given** the module upgrade runs the migration script
**When** the migration completes
**Then** all existing invoices without a payment method should have payment_method_id = "01" (Efectivo)
**And** the migration log should show the count of updated records

#### AC9: Payment Gateway API Configuration
**Given** I am a system administrator
**When** I navigate to Settings → General Settings → Costa Rica E-Invoicing
**Then** I should see a "Payment Gateway" selection field
**And** I should see fields for API credentials (API Key, Secret Key)
**And** I can select between: None, TiloPay, ONVO Pay

#### AC10: Hacienda Accepts Invoice with Payment Method
**Given** I have generated and signed an e-invoice with payment method = "06"
**When** I submit the invoice to Hacienda sandbox
**Then** Hacienda should accept the invoice
**And** the invoice state should change to "Accepted"
**And** no validation errors related to payment method should occur

---

## Additional Context

### Dependencies

**Python Libraries** (already in external_dependencies):
- ✅ `lxml` - XML generation
- ✅ `requests` - API calls to payment gateways
- 📦 `cryptography` - Already installed (for signatures)

**Odoo Modules**:
- ✅ `account` - Invoice model
- ✅ `l10n_cr` - Costa Rica localization

**External APIs** (Optional - Phase 4):
- 🔌 TiloPay API v2: https://docs.tilopay.com/
- 🔌 ONVO Pay API v1: https://docs.onvopay.com/

### Testing Strategy

**Unit Tests** (pytest + Odoo test framework):
```python
# tests/test_payment_method.py
from odoo.tests import TransactionCase
from odoo.exceptions import UserError

class TestPaymentMethod(TransactionCase):
    def test_sinpe_movil_requires_transaction_id(self):
        # Create invoice with SINPE Móvil
        invoice = self.env['account.move'].create({...})
        invoice.l10n_cr_payment_method_id = self.env.ref('l10n_cr_einvoice.payment_method_sinpe')

        # Should raise error without transaction ID
        with self.assertRaises(UserError):
            invoice.action_post()

        # Should succeed with transaction ID
        invoice.l10n_cr_payment_transaction_id = '123456789'
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')
```

**XSD Schema Validation**:
- Use existing `xsd_validator.py` to validate XML
- Test against official Hacienda v4.4 XSD schemas
- Ensure `<MedioPago>` tag validates correctly

**Sandbox Testing**:
- Use Hacienda sandbox environment: https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/
- Test all 5 payment methods
- Verify Hacienda accepts XML with payment method codes

### Notes

**Costa Rica Payment Method Codes** (Official Hacienda v4.4):
```
01 = Efectivo (Cash)
02 = Tarjeta (Card - credit/debit)
03 = Cheque (Check)
04 = Transferencia - depósito bancario (Bank transfer/deposit)
05 = RECAUDADO POR TERCEROS (Collected by third parties) - NOT IMPLEMENTED
06 = SINPE Móvil (Mobile payment system)
```

**Why code "05" is excluded**:
- Used for specific business scenarios (utility companies, municipalities)
- Not applicable to GMS gym management use case
- Can be added in future if needed

**Transaction ID Format** (SINPE Móvil):
- Length: Variable (typically 8-12 digits)
- Format: Numeric string
- Example: "123456789"
- Source: Provided by SINPE app after payment
- Validation: No checksum, just alphanumeric

**XML v4.4 Specification Reference**:
- Section 4.3.1: MedioPago (Payment Method)
- Section 4.3.2: NumeroTransaccion (Transaction Number)
- Official XSD: https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/

**Bootstrap 5 Badge Classes**:
```html
<span class="badge bg-success">Efectivo</span>    <!-- Green -->
<span class="badge bg-primary">Tarjeta</span>     <!-- Blue -->
<span class="badge bg-warning">Cheque</span>      <!-- Yellow -->
<span class="badge bg-info">Transferencia</span>  <!-- Orange -->
<span class="badge" style="background: #6f42c1;">SINPE Móvil</span> <!-- Purple -->
```

**Migration Safety**:
- Use `noupdate="1"` for payment method data
- Migration script should be idempotent (safe to run multiple times)
- Log all changes for audit trail
- Test on copy of production database first

**Future Enhancements** (Out of Scope):
- Automatic payment gateway selection based on payment method
- Real-time SINPE Móvil transaction verification
- Payment reconciliation automation
- Multi-payment support (split between methods)
- Payment link generation for online payments

---

**Estimated Effort**: 96 hours (12 days)
**Developer Skill Level**: Intermediate-Advanced Odoo developer
**Testing Time**: 24 hours included in estimate
**Documentation Time**: 8 hours (update user manual)

**Total Phase 1A Effort**: 96 hours

---

**Document Version**: 1.0
**Last Updated**: 2025-12-28
**Author**: BMAD Workflow System
**Reviewed By**: Pending
**Approved By**: Pending
