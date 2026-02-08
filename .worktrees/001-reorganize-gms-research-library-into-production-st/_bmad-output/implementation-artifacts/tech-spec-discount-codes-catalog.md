# Tech-Spec: Discount Codes Catalog Implementation

**Created:** 2025-12-28
**Status:** Ready for Development
**Priority:** HIGH - Compliance Risk (Invoice Rejection)
**Phase:** 1B - Critical Compliance

---

## Overview

### Problem Statement

Costa Rica's v4.4 electronic invoicing specification requires specific discount codes for all discounts applied to invoices. The current implementation uses free-form text fields for discount descriptions, which is **no longer compliant** with Hacienda v4.4 requirements.

**Compliance Issue**:
- v4.3 allowed: Free-form text descriptions for discounts
- v4.4 requires: Specific discount codes from predefined catalog (11 categories)
- Current implementation: Using free-form text → **REJECTED by Hacienda**

**Business Impact**:
- Invoices with free-form discounts will be rejected by Hacienda validation
- Cannot process promotional discounts legally
- Risk of audit findings and penalties
- Competitive disadvantage (cannot offer structured discounts)

### Solution

Implement structured discount codes catalog per Hacienda v4.4 specification:
1. Create discount codes master data (11 categories)
2. Replace free-form text with code selection
3. Add discount code to invoice line items
4. Update XML generation to include discount codes
5. Support multiple discount types per line
6. Migrate existing free-form discounts to "99-Otro"
7. Add validation rules for discount codes

### Scope

**IN SCOPE**:
- ✅ Discount codes catalog (11 categories per Hacienda spec)
- ✅ Discount code field on invoice line items (account.move.line)
- ✅ Discount code selection in invoice line form
- ✅ XML generation updates for discount codes
- ✅ Migration script for existing invoices
- ✅ Validation rules (code "99" requires description)
- ✅ UI updates for discount code display
- ✅ Support for line-level discounts only (not global discounts)

**OUT OF SCOPE** (Future Enhancements):
- ❌ Automatic discount code suggestion based on discount rules
- ❌ Discount code analytics/reporting
- ❌ Global/header-level discounts (only line-level supported)
- ❌ Discount code permissions by user role
- ❌ Promotional campaign management

---

## Context for Development

### Codebase Patterns

**Line Item Discount Pattern** (from Odoo standard):
```python
# account.move.line already has discount field (percentage)
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    discount = fields.Float(
        string='Discount (%)',
        digits='Discount',
        default=0.0,
    )
```

**XML Generator Line Items Pattern** (from `xml_generator.py`):
```python
def _add_detalle_servicio(self, root, move):
    """Add line items to XML."""
    detalle = etree.SubElement(root, 'DetalleServicio')

    for line in move.invoice_line_ids:
        linea = etree.SubElement(detalle, 'LineaDetalle')
        # ... quantity, description, price ...

        # Discount handling (currently missing discount CODE)
        if line.discount:
            desc_elem = etree.SubElement(linea, 'Descuento')
            monto = etree.SubElement(desc_elem, 'MontoDescuento')
            monto.text = str(line.price_unit * line.quantity * line.discount / 100)
            # MISSING: NaturalezaDescuento (discount code)
```

**Master Data Pattern** (from `data/document_types.xml`):
```xml
<odoo>
    <data noupdate="1">
        <record id="unique_id" model="model.name">
            <field name="code">01</field>
            <field name="name">Display Name</field>
            <field name="description">Full description</field>
        </record>
    </data>
</odoo>
```

### Files to Reference

**Models** (Must Read):
- Core: Odoo `account/models/account_move.py` - Standard discount field
- Extension: `l10n_cr_einvoice/models/account_move.py` - Invoice model extension pattern
- XML Gen: `l10n_cr_einvoice/models/xml_generator.py:200-250` - Line item generation

**Views** (Must Modify):
- `l10n_cr_einvoice/views/account_move_views.xml` - Invoice line tree view
- Standard Odoo invoice views (inherit and extend)

**Data Files** (Must Create):
- `l10n_cr_einvoice/data/discount_codes.xml` - NEW FILE for catalog

**Manifest** (Must Update):
- `l10n_cr_einvoice/__manifest__.py:55-74` - Add discount_codes.xml to data list

### Technical Decisions

**Decision 1**: Discount Code Catalog as Master Data (Not Selection Field)
- **Why**: Master data allows descriptions, future extensibility, easier to query
- **Implementation**: `l10n_cr.discount.code` model with noupdate="1"
- **Alternative Rejected**: Hard-coded Selection field (no descriptions, not extendable)

**Decision 2**: Line-Level Discount Codes Only
- **Why**: Hacienda v4.4 spec requires discount codes per line item, not global
- **Implementation**: Add field to `account.move.line`
- **Alternative Rejected**: Global discount codes (doesn't match Hacienda spec)

**Decision 3**: Migration Strategy = "99-Otro" for Existing
- **Why**: Safest approach - preserves existing discount amounts, allows gradual cleanup
- **Implementation**: All invoices with discounts → code "99", keep original text in description
- **Alternative Rejected**: Force users to reclassify (too disruptive, blocks migration)

**Decision 4**: Code "99-Otro" Requires Description
- **Why**: Hacienda requires explanation when using "Otro" category
- **Implementation**: Validation rule on save - if code == "99" and no description → warning
- **Alternative Rejected**: Hard error (too strict, blocks edge cases)

**Decision 5**: Multiple Discount Types Not Supported Initially
- **Why**: Complex implementation, rare use case in GMS gym scenario
- **Implementation**: One discount code per line item
- **Alternative Rejected**: Multi-code support (adds complexity, marginal value)

---

## Implementation Plan

### Tasks

#### Phase 1B.1: Discount Code Catalog (6 hours)
- [ ] **Task 1.1**: Create `l10n_cr.discount.code` model
  - File: `models/discount_code.py` (NEW)
  - Fields: `code` (Char, 2), `name` (Char), `description` (Text), `active` (Boolean), `requires_description` (Boolean)
  - Methods: `name_get()` to display "01 - Comercial descuento"
  - Add to `models/__init__.py`

- [ ] **Task 1.2**: Create discount codes data file
  - File: `data/discount_codes.xml` (NEW)
  - Records: 11 discount codes per Hacienda specification
  - Code "99" has `requires_description="True"`
  - Add to `__manifest__.py` data list

- [ ] **Task 1.3**: Create security rules
  - Add to `security/ir.model.access.csv`
  - Permissions: all_users (read), accountant (write)

#### Phase 1B.2: Invoice Line Model Extension (10 hours)
- [ ] **Task 2.1**: Extend `account.move.line` model
  - File: `models/account_move_line.py` (NEW - inherit account.move.line)
  - Field: `l10n_cr_discount_code_id` (Many2one to l10n_cr.discount.code)
  - Field: `l10n_cr_discount_description` (Text) - for code "99"
  - Compute: Show/hide description field based on discount code

- [ ] **Task 2.2**: Add validation method
  - Method: `_validate_discount_code_description()`
  - Logic: If discount > 0 and code == "99" and no description → UserError/Warning
  - Hook: On line save or invoice confirmation

- [ ] **Task 2.3**: Add discount code constraint
  - Constraint: If discount > 0, discount code is required
  - Error message: "Discount code is required when discount percentage is applied"

#### Phase 1B.3: XML Generator Updates (12 hours)
- [ ] **Task 3.1**: Update `_add_detalle_servicio()` method
  - File: `models/xml_generator.py:200-250`
  - Current: Only generates `MontoDescuento` (discount amount)
  - New: Add `NaturalezaDescuento` tag with discount code

- [ ] **Task 3.2**: Add discount code to XML structure
  - XML structure per v4.4 spec:
    ```xml
    <LineaDetalle>
      <Descuento>
        <MontoDescuento>5000.00</MontoDescuento>
        <NaturalezaDescuento>01</NaturalezaDescuento>
      </Descuento>
    </LineaDetalle>
    ```

- [ ] **Task 3.3**: Handle "99-Otro" with description
  - If code == "99", append description to `NaturalezaDescuento`
  - Format: "99 - {description}"
  - Validate max length per Hacienda spec (80 characters)

- [ ] **Task 3.4**: Update all document type generators
  - Files: `_generate_factura_electronica()`, `_generate_tiquete_electronico()`, `_generate_nota_credito()`, `_generate_nota_debito()`
  - Ensure all support discount codes in line items

#### Phase 1B.4: UI Updates (10 hours)
- [ ] **Task 4.1**: Update invoice line tree view
  - File: `views/account_move_views.xml`
  - Add discount code column (editable)
  - Add discount description column (visible only if code == "99")
  - Position: After discount percentage column

- [ ] **Task 4.2**: Update invoice line form view
  - Add discount code field with dropdown
  - Add discount description field (text area)
  - Add `attrs` to show/hide description based on code
  - Example:
    ```xml
    <field name="l10n_cr_discount_code_id"/>
    <field name="l10n_cr_discount_description"
           attrs="{'invisible': [('l10n_cr_discount_code_id.code', '!=', '99')],
                   'required': [('l10n_cr_discount_code_id.code', '=', '99')]}"/>
    ```

- [ ] **Task 4.3**: Add discount code to e-invoice document view
  - Show discount codes in generated XML preview
  - Display summary of discount codes used

#### Phase 1B.5: Data Migration (12 hours)
- [ ] **Task 5.1**: Create migration script
  - File: `migrations/19.0.1.0.0/post-migration.py`
  - Logic:
    1. Find all invoice lines with discount > 0
    2. Check if discount_code_id is NULL
    3. Set discount_code_id = code "99" (Otro)
    4. Copy any existing discount notes to discount_description
  - Log: Count of records updated per invoice

- [ ] **Task 5.2**: Create discount analysis report
  - Generate report of all existing discounts
  - Group by: discount percentage range
  - Output: CSV with suggestions for proper discount code
  - Help users reclassify discounts properly

- [ ] **Task 5.3**: Test migration on staging database
  - Backup test database
  - Run migration script
  - Verify all discounted lines have code "99"
  - Verify XML regeneration works
  - Test a sample reclassification

#### Phase 1B.6: Testing (14 hours)
- [ ] **Task 6.1**: Unit tests for discount code model
  - File: `tests/test_discount_code.py` (NEW)
  - Test catalog creation (11 codes)
  - Test code uniqueness
  - Test name_get() format

- [ ] **Task 6.2**: Unit tests for invoice line validation
  - File: `tests/test_account_move_line_discount.py` (NEW)
  - Test discount > 0 requires discount code
  - Test code "99" requires description
  - Test code "99" without description → Error

- [ ] **Task 6.3**: Integration tests for XML generation
  - File: `tests/test_xml_generator_discounts.py` (NEW)
  - Test XML contains `NaturalezaDescuento` tag
  - Test all 11 discount codes generate valid XML
  - Test code "99" includes description in XML

- [ ] **Task 6.4**: E2E test: Invoice with multiple discount types
  - Create invoice with 3 line items
  - Line 1: 10% discount, code "01" (Commercial)
  - Line 2: 15% discount, code "03" (Volume)
  - Line 3: 5% discount, code "99" (Other - "Special customer")
  - Generate XML
  - Validate against XSD schema
  - Submit to Hacienda sandbox

- [ ] **Task 6.5**: Migration tests
  - Create test invoices with discounts (no codes)
  - Run migration
  - Verify all get code "99"
  - Verify XML generation works post-migration

### Acceptance Criteria

#### AC1: Discount Code Catalog Exists
**Given** I am a system administrator
**When** I navigate to Settings → Technical → Database Structure → Models
**Then** I should see `l10n_cr.discount.code` model
**And** the model should contain 11 records with codes: 01-10, 99

#### AC2: Invoice Line Has Discount Code Field
**Given** I am creating a new invoice line with a discount
**When** I apply a discount percentage (e.g., 10%)
**Then** I should see a "Discount Code" dropdown field appear
**And** the dropdown should contain all 11 discount codes
**And** I must select a discount code before saving

#### AC3: Code "99-Otro" Requires Description
**Given** I have selected discount code "99 - Otro"
**When** I try to save the invoice line without a description
**Then** I should receive an error: "Description is required for discount code 'Otro'"
**And** the line should NOT be saved

#### AC4: Discount Description Field Visibility
**Given** I am on the invoice line form
**When** I select discount code = "01 - Comercial descuento"
**Then** the discount description field should be hidden
**When** I change discount code to "99 - Otro"
**Then** the discount description field should appear and be required

#### AC5: XML Contains Discount Code
**Given** I have confirmed an invoice with a line item having 10% discount with code "03"
**When** the e-invoice XML is generated
**Then** the XML should contain:
```xml
<Descuento>
  <MontoDescuento>1000.00</MontoDescuento>
  <NaturalezaDescuento>03</NaturalezaDescuento>
</Descuento>
```

#### AC6: XML for Code "99" Includes Description
**Given** I have an invoice line with discount code "99" and description "Special promotion"
**When** the e-invoice XML is generated
**Then** the XML should contain:
```xml
<NaturalezaDescuento>99 - Special promotion</NaturalezaDescuento>
```

#### AC7: Multiple Lines with Different Discount Codes
**Given** I have an invoice with 3 lines, each with different discount codes
**When** the e-invoice XML is generated
**Then** each `<LineaDetalle>` should have the correct `<NaturalezaDescuento>` for its line
**And** the codes should be: 01, 03, 99 (as set)

#### AC8: Migration Updates Existing Discounts
**Given** the module upgrade runs the migration script
**When** the migration completes
**Then** all invoice lines with discount > 0 and no discount code should have code "99"
**And** the migration log should show the count of updated lines

#### AC9: Discount Code Dropdown Displays Properly
**Given** I am viewing the invoice line tree view
**When** I look at the discount code column
**Then** I should see the format "01 - Comercial descuento" (code + name)
**And** the dropdown should be searchable

#### AC10: Hacienda Accepts Invoice with Discount Codes
**Given** I have generated and signed an e-invoice with discount codes
**When** I submit the invoice to Hacienda sandbox
**Then** Hacienda should accept the invoice
**And** the invoice state should change to "Accepted"
**And** no validation errors related to discount codes should occur

---

## Additional Context

### Dependencies

**Python Libraries** (already in external_dependencies):
- ✅ `lxml` - XML generation

**Odoo Modules**:
- ✅ `account` - Invoice and invoice line models
- ✅ `l10n_cr` - Costa Rica localization

**No External APIs Required**: This is pure data structure change

### Testing Strategy

**Unit Tests** (pytest + Odoo test framework):
```python
# tests/test_discount_code.py
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError

class TestDiscountCode(TransactionCase):
    def test_code_99_requires_description(self):
        # Create invoice line with code 99, no description
        line = self.env['account.move.line'].create({
            'name': 'Test Product',
            'discount': 10.0,
            'l10n_cr_discount_code_id': self.env.ref('l10n_cr_einvoice.discount_code_99').id,
            # Missing: l10n_cr_discount_description
        })

        # Should raise validation error
        with self.assertRaises(ValidationError):
            line._validate_discount_code_description()

    def test_discount_requires_code(self):
        # Create line with discount but no code
        line = self.env['account.move.line'].create({
            'name': 'Test Product',
            'discount': 10.0,
            # Missing: l10n_cr_discount_code_id
        })

        # Should raise validation error
        with self.assertRaises(ValidationError):
            line._validate_discount_code()
```

**XSD Schema Validation**:
- Validate `<NaturalezaDescuento>` tag format
- Ensure codes match Hacienda catalog
- Test against official v4.4 XSD schemas

**Sandbox Testing**:
- Test all 11 discount codes in real invoices
- Verify Hacienda accepts each code
- Test edge cases (long descriptions, special characters)

### Notes

**Costa Rica Discount Codes** (Official Hacienda v4.4):
```
01 = Comercial descuento (Commercial discount)
02 = Descuento por pronto pago (Early payment discount)
03 = Descuento por volumen (Volume discount)
04 = Descuento por fidelidad (Loyalty discount)
05 = Descuento estacional (Seasonal discount)
06 = Descuento por introducción (Introductory discount)
07 = Descuento por cierre (Closeout discount)
08 = Descuento por defecto (Defect discount)
09 = Descuento por mayoreo (Wholesale discount)
10 = Descuento corporativo (Corporate discount)
99 = Otro (Other - requires description)
```

**XML v4.4 Specification Reference**:
- Section 4.2.7: Descuento (Discount)
- Section 4.2.7.2: NaturalezaDescuento (Discount Nature/Code)
- Official XSD: Line 450-470 in v4.4 schema

**Discount Code Usage Guidelines** (for users):
```
01 - Use for: Standard promotional discounts
02 - Use for: "Pay within 15 days, get 2% off"
03 - Use for: "Buy 10+, save 15%"
04 - Use for: Loyalty program member discounts
05 - Use for: Black Friday, Christmas sales
06 - Use for: New product launch promotions
07 - Use for: End of season clearance
08 - Use for: Damaged goods, floor models
09 - Use for: Wholesale/bulk customer pricing
10 - Use for: Corporate contracts, government
99 - Use for: Any discount not fitting above
```

**Migration Considerations**:
- Current invoices may have discount notes in different fields
- Some may have no notes at all (just percentage)
- Migration script should be conservative (use code 99 for safety)
- Provide post-migration report for users to reclassify

**UI/UX Best Practices**:
- Discount code dropdown should be REQUIRED when discount > 0
- Description field should auto-focus when code 99 selected
- Provide inline help text with examples for each code
- Consider default suggestions based on discount percentage ranges

**Future Enhancements** (Out of Scope):
- Automatic code suggestion based on discount rules
- Discount code usage analytics dashboard
- Integration with promotional campaign module
- Multi-code support (e.g., seasonal + volume)

---

**Estimated Effort**: 64 hours (8 days)
**Developer Skill Level**: Intermediate Odoo developer
**Testing Time**: 14 hours included in estimate
**Documentation Time**: 6 hours (user guide on discount codes)

**Total Phase 1B Effort**: 64 hours

---

**Document Version**: 1.0
**Last Updated**: 2025-12-28
**Author**: BMAD Workflow System
**Reviewed By**: Pending
**Approved By**: Pending
