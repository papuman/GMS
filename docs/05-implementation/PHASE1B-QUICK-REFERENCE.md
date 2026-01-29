# Phase 1B: Discount Codes - Quick Reference Guide

**Module**: l10n_cr_einvoice v19.0.1.0.0
**Date**: 2025-12-28
**Status**: Production Ready

---

## Implementation Overview

Phase 1B adds complete support for Costa Rica Hacienda v4.4 discount codes, implementing all 11 official codes with validation, XML generation, and migration.

---

## Key Files Added/Modified

### New Files (6)
```
l10n_cr_einvoice/
├── models/
│   ├── discount_code.py              # Discount code catalog model
│   └── account_move_line.py          # Invoice line extension
├── data/
│   └── discount_codes.xml            # 11 discount codes catalog
└── migrations/19.0.1.0.0/
    └── post-migration.py             # Phase 1A + 1B migration
```

### Modified Files (5)
```
l10n_cr_einvoice/
├── models/
│   ├── __init__.py                   # Added imports
│   └── xml_generator.py              # Updated NaturalezaDescuento
├── views/
│   └── account_move_views.xml        # Added discount code fields
├── security/
│   └── ir.model.access.csv           # Added 3 access rules
└── __manifest__.py                   # Added data file, updated description
```

---

## 11 Discount Codes

| Code | Name (ES) | Name (EN) | Use Case |
|------|-----------|-----------|----------|
| 01 | Comercial descuento | Commercial | Promotional discounts |
| 02 | Descuento por pronto pago | Early payment | Pay within X days |
| 03 | Descuento por volumen | Volume | Buy 10+, save 15% |
| 04 | Descuento por fidelidad | Loyalty | Loyalty programs |
| 05 | Descuento estacional | Seasonal | Black Friday sales |
| 06 | Descuento por introducción | Introductory | New product launch |
| 07 | Descuento por cierre | Closeout | End of season |
| 08 | Descuento por defecto | Defect | Damaged goods |
| 09 | Descuento por mayoreo | Wholesale | Bulk/reseller |
| 10 | Descuento corporativo | Corporate | B2B contracts |
| 99 | Otro | Other | **Requires description** |

---

## Usage Examples

### Creating Invoice with Discount Code

```python
# In Odoo Python
invoice_line = self.env['account.move.line'].create({
    'move_id': invoice.id,
    'product_id': product.id,
    'quantity': 10,
    'price_unit': 100.00,
    'discount': 10.0,  # 10% discount
    'l10n_cr_discount_code_id': self.env.ref('l10n_cr_einvoice.discount_code_03').id,  # Volume discount
})
```

### Using Code "99" with Description

```python
# Code 99 requires description
invoice_line = self.env['account.move.line'].create({
    'move_id': invoice.id,
    'product_id': product.id,
    'quantity': 5,
    'price_unit': 200.00,
    'discount': 15.0,
    'l10n_cr_discount_code_id': self.env.ref('l10n_cr_einvoice.discount_code_99').id,
    'l10n_cr_discount_description': 'Special promotion for new gym members',  # Required!
})
```

### Getting Discount Code for XML

```python
# In XML generator or custom code
discount_nature = line._get_discount_nature_for_xml()
# Returns: "03" for codes 01-10
# Returns: "99 - Special promotion..." for code 99
```

---

## XML Output Examples

### Code 01-10 (Simple)
```xml
<LineaDetalle>
  <NumeroLinea>1</NumeroLinea>
  <Cantidad>10</Cantidad>
  <Detalle>Monthly Membership</Detalle>
  <PrecioUnitario>100.00000</PrecioUnitario>
  <MontoTotal>1000.00000</MontoTotal>
  <Descuento>
    <MontoDescuento>100.00000</MontoDescuento>
    <NaturalezaDescuento>03</NaturalezaDescuento>
  </Descuento>
  <SubTotal>900.00000</SubTotal>
  ...
</LineaDetalle>
```

### Code 99 (With Description)
```xml
<Descuento>
  <MontoDescuento>150.00000</MontoDescuento>
  <NaturalezaDescuento>99 - Special promotion for new members</NaturalezaDescuento>
</Descuento>
```

---

## Validation Rules

### Rule 1: Discount Requires Code
```python
# If discount > 0, discount_code_id is REQUIRED
# Exception: ValidationError
# Message: "Discount code is required when discount percentage is applied"
```

### Rule 2: Code "99" Requires Description
```python
# If code == "99" and discount > 0, description is REQUIRED
# Exception: ValidationError
# Message: "Description is required for discount code '99 - Otro'"
```

### Rule 3: Description Max Length
```python
# Max length: 75 characters (total XML tag = 80 chars with "99 - ")
# Exception: ValidationError
# Message: "Discount description is too long (XX characters)"
```

### Rule 4: Only for Costa Rica Invoices
```python
# Validation only applies when:
# - move_type in ['out_invoice', 'out_refund']
# - country_code == 'CR'
# - display_type == 'product'
```

---

## Database Schema

### Table: l10n_cr_discount_code
```sql
CREATE TABLE l10n_cr_discount_code (
    id SERIAL PRIMARY KEY,
    code VARCHAR(2) NOT NULL UNIQUE,
    name VARCHAR NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    requires_description BOOLEAN DEFAULT FALSE
);
```

### Table: account_move_line (extended)
```sql
ALTER TABLE account_move_line
ADD COLUMN l10n_cr_discount_code_id INTEGER REFERENCES l10n_cr_discount_code(id),
ADD COLUMN l10n_cr_discount_description TEXT;
```

---

## Migration Script

### What It Does
1. Sets all existing discounts to code "99" (Otro)
2. Generates analysis report by discount percentage
3. Suggests proper codes for each range
4. Logs detailed summary

### Running Migration
```bash
# Automatic during module upgrade
odoo-bin -u l10n_cr_einvoice -d your_database
```

### Migration Output Example
```
================================================================================
DISCOUNT ANALYSIS REPORT
================================================================================

0-5%: 23 lines
  Suggested codes:
    - Code 01: Comercial descuento (promotional)
    - Code 02: Descuento por pronto pago (early payment)
    Example: INV/2024/0001 - Monthly Membership (3%)
    Example: INV/2024/0002 - Personal Training (5%)
    ... and 21 more

10-15%: 12 lines
  Suggested codes:
    - Code 03: Descuento por volumen (bulk)
    - Code 05: Descuento estacional (seasonal)
```

---

## Common Tasks

### Find Invoices with Code "99" Needing Reclassification
```python
lines = self.env['account.move.line'].search([
    ('l10n_cr_discount_code_id.code', '=', '99'),
    ('move_id.state', '=', 'posted'),
])
```

### Bulk Update Discount Codes
```python
# Update all 10% volume discounts
lines = self.env['account.move.line'].search([
    ('discount', '=', 10.0),
    ('l10n_cr_discount_code_id.code', '=', '99'),
])
volume_code = self.env.ref('l10n_cr_einvoice.discount_code_03')
lines.write({'l10n_cr_discount_code_id': volume_code.id})
```

### Generate Discount Usage Report
```python
# Group by discount code
self.env.cr.execute("""
    SELECT dc.code, dc.name, COUNT(aml.id) as usage_count
    FROM account_move_line aml
    JOIN l10n_cr_discount_code dc ON aml.l10n_cr_discount_code_id = dc.id
    WHERE aml.discount > 0
    GROUP BY dc.code, dc.name
    ORDER BY usage_count DESC
""")
```

---

## Testing Checklist

### Unit Tests
```python
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError

class TestDiscountCode(TransactionCase):
    def test_discount_requires_code(self):
        # Create line with discount, no code → ValidationError

    def test_code_99_requires_description(self):
        # Create line with code 99, no description → ValidationError

    def test_xml_generation_with_code(self):
        # Generate XML, verify NaturalezaDescuento tag
```

### Manual Testing
1. Create invoice with 10% discount
2. Select code "03 - Volumen"
3. Save → Success
4. Generate e-invoice XML
5. Verify: `<NaturalezaDescuento>03</NaturalezaDescuento>`

---

## Troubleshooting

### Error: "Discount code is required"
**Solution**: Select a discount code from the dropdown (01-10, 99)

### Error: "Description is required for discount code 'Otro'"
**Solution**: Enter description in "Discount Description" field (code 99 only)

### Error: "Discount description is too long"
**Solution**: Shorten description to max 75 characters

### Migration fails: "Discount code '99' not found"
**Solution**: Ensure `data/discount_codes.xml` is loaded before migration

### XML validation error: "Invalid NaturalezaDescuento"
**Solution**: Verify discount code is from official catalog (01-10, 99)

---

## API Reference

### Model: l10n_cr.discount.code

```python
# Fields
code                  # Char(2), required, unique
name                  # Char, required
description           # Text
active                # Boolean
requires_description  # Boolean

# Methods
name_get()            # Returns "01 - Comercial descuento"
_name_search()        # Searchable by code or name
```

### Model: account.move.line (extended)

```python
# Fields
l10n_cr_discount_code_id              # Many2one('l10n_cr.discount.code')
l10n_cr_discount_description          # Text
l10n_cr_discount_code_requires_description  # Boolean (computed)

# Methods
_check_discount_code_required()       # Constraint: discount > 0 needs code
_check_discount_code_99_description() # Constraint: code 99 needs description
_get_discount_nature_for_xml()        # Returns XML-ready discount nature
```

---

## Support & Documentation

### Files
- **Tech Spec**: `/_bmad-output/implementation-artifacts/tech-spec-discount-codes-catalog.md`
- **Implementation Summary**: `/PHASE1B-DISCOUNT-CODES-IMPLEMENTATION-COMPLETE.md`
- **This Guide**: `/PHASE1B-QUICK-REFERENCE.md`

### Training Resources (To Be Created)
- Discount Code Selection Guide (1-pager)
- Video: "How to Select the Right Discount Code"
- FAQ: Common Discount Code Scenarios

### Module Info
```python
{
    'name': 'l10n_cr_einvoice',
    'version': '19.0.1.0.0',
    'depends': ['account', 'l10n_cr', 'sale', 'sale_subscription'],
}
```

---

**Last Updated**: 2025-12-28
**Module Status**: Production Ready
**Next Steps**: Testing → Staging → Production
