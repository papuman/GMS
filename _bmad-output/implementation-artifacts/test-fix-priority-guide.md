# Test Fix Priority Guide - l10n_cr_einvoice

**Quick reference for fixing the 135 failing tests**

---

## 🔴 P0 - CRITICAL (Blocks 47 tests - Fix First!)

### Issue: Missing Journal Setup

**Impact:** 34.8% of all failures
**Affected Tests:** 47
**Affected Classes:** TestAccountMovePayment, TestXMLGenerator*, TestTaxReportAPIIntegration, TestD1xx workflows

**Error:**
```
odoo.exceptions.UserError: No journal could be found in company Test Company CR for any of those types: sale
```

**Fix:** Create `l10n_cr_einvoice/tests/common.py`

```python
from odoo.tests import TransactionCase

class EInvoiceTestCase(TransactionCase):
    """Base class for e-invoice tests with proper accounting setup."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create Costa Rica company
        cls.company_cr = cls.env['res.company'].create({
            'name': 'Test Company CR',
            'country_id': cls.env.ref('base.cr').id,
            'vat': '312345678901',  # Valid CR ID format
            'currency_id': cls.env.ref('base.CRC').id,
        })

        # Create chart of accounts (use CR localization if available)
        cls.env['account.chart.template'].try_loading('cr', company=cls.company_cr)

        # Create sales journal
        cls.sales_journal = cls.env['account.journal'].create({
            'name': 'Test Sales Journal',
            'code': 'TSJ',
            'type': 'sale',
            'company_id': cls.company_cr.id,
        })

        # Create purchase journal
        cls.purchase_journal = cls.env['account.journal'].create({
            'name': 'Test Purchase Journal',
            'code': 'TPJ',
            'type': 'purchase',
            'company_id': cls.company_cr.id,
        })

        # Create default tax (13% IVA)
        cls.tax_iva = cls.env['account.tax'].create({
            'name': 'IVA 13%',
            'amount': 13.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': cls.company_cr.id,
        })

        # Create test partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'country_id': cls.env.ref('base.cr').id,
            'vat': '109876543210',
            'company_id': cls.company_cr.id,
        })

        # Create test product
        cls.product = cls.env['res.product'].create({
            'name': 'Test Product',
            'type': 'service',
            'list_price': 100.0,
            'taxes_id': [(6, 0, [cls.tax_iva.id])],
        })
```

**Then update all test files:**

```python
# OLD:
from odoo.tests import TransactionCase

class TestXMLGeneratorCore(TransactionCase):
    ...

# NEW:
from .common import EInvoiceTestCase

class TestXMLGeneratorCore(EInvoiceTestCase):
    ...
```

**Estimated Fix Time:** 2 hours
**Expected Impact:** +47 tests passing (total: 111/199 = 55.8%)

---

## 🟡 P1 - HIGH (Affects core functionality)

### Issue 1: XML Namespace Mismatch (3 tests)

**Impact:** Tax report validation tests
**Files:** `tests/test_tax_report_xml_generation.py`

**Error:**
```
AssertionError: '{https://hacienda.go.cr/schemas/d101}D101' != 'D101'
```

**Fix:**

```python
# OLD:
root = etree.fromstring(xml_string)
self.assertEqual(root.tag, 'D101')

# NEW:
from lxml import etree

root = etree.fromstring(xml_string)
# Option 1: Use full Clark notation
self.assertEqual(root.tag, '{https://hacienda.go.cr/schemas/d101}D101')

# Option 2: Use QName to get local name
self.assertEqual(etree.QName(root).localname, 'D101')
self.assertEqual(etree.QName(root).namespace, 'https://hacienda.go.cr/schemas/d101')
```

**Affected Tests:**
- `test_d101_xml_basic_structure`
- `test_d150_xml_basic_structure`
- `test_d151_xml_basic_structure`

**Estimated Fix Time:** 30 minutes
**Expected Impact:** +3 tests passing

---

### Issue 2: Assertion None Errors (9 tests)

**Impact:** Tax report XML generation
**Files:** `tests/test_tax_report_xml_generation.py`

**Error:**
```
AssertionError: unexpectedly None
```

**Affected Tests:**
- `test_d101_xml_expenses_section`
- `test_d101_xml_income_section`
- `test_d101_xml_tax_brackets`
- `test_d150_xml_line_items`
- `test_d150_xml_tax_totals`
- `test_d151_xml_line_items`
- `test_d151_xml_summary_section`

**Investigation Steps:**

1. Check if XML is being generated at all
2. Verify XPath queries include proper namespaces
3. Ensure test data creates required tax report lines
4. Check if computed fields are calculating

**Example Debug:**

```python
def test_d101_xml_income_section(self):
    report = self._create_d101_with_income()
    xml_string = report.generate_xml()

    # Add debugging
    print(f"Generated XML length: {len(xml_string)}")
    print(f"XML preview: {xml_string[:500]}")

    root = etree.fromstring(xml_string)

    # Use namespaced XPath
    namespaces = {'d101': 'https://hacienda.go.cr/schemas/d101'}
    income_section = root.xpath('//d101:Ingresos', namespaces=namespaces)

    # Check if section exists
    if not income_section:
        print(f"Income section not found. Available elements:")
        print([etree.QName(elem).localname for elem in root.iter()])

    self.assertIsNotNone(income_section, "Income section should exist")
```

**Estimated Fix Time:** 2-3 hours
**Expected Impact:** +9 tests passing

---

### Issue 3: Tax Report Workflow Failures (50+ tests)

**Impact:** D101, D150, D151 workflow tests
**Files:** `tests/test_d1*_workflow.py`, `tests/test_tax_report_api_integration.py`

**Sub-issues:**
1. Missing journal setup (covered in P0)
2. Tax calculations returning 0.0
3. API integration needs mocking

**Fix for Tax Calculations:**

```python
# In test setup, ensure tax report has actual data
def _create_d101_with_real_data(self):
    # Create actual invoices with tax amounts
    invoice = self.env['account.move'].create({
        'partner_id': self.partner.id,
        'move_type': 'out_invoice',
        'journal_id': self.sales_journal.id,
        'invoice_date': '2025-01-15',
        'invoice_line_ids': [(0, 0, {
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'tax_ids': [(6, 0, [self.tax_iva.id])],
        })],
    })
    invoice.action_post()  # Important: post the invoice!

    # Now create tax report for period
    report = self.env['l10n_cr.tax.report'].create({
        'report_type': 'd101',
        'period_year': 2025,
        'period_month': 1,
        'company_id': self.company_cr.id,
    })
    report.action_calculate()  # Should now have data

    return report
```

**Fix for API Integration (Mock Hacienda):**

```python
from unittest.mock import patch, MagicMock

class TestTaxReportAPIIntegration(EInvoiceTestCase):

    @patch('odoo.addons.l10n_cr_einvoice.models.tax_report.requests.post')
    def test_submit_d101_success(self, mock_post):
        # Mock successful Hacienda response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'clave': '50621012300310123456780000000011000000011234567891',
            'ind-estado': 'aceptado',
        }
        mock_post.return_value = mock_response

        # Test submission
        report = self._create_d101_with_real_data()
        report.action_submit_to_hacienda()

        self.assertEqual(report.state, 'submitted')
        self.assertTrue(report.clave)
```

**Estimated Fix Time:** 4-6 hours
**Expected Impact:** +30-40 tests passing

---

## 🟢 P2 - MEDIUM (Can fix later)

### Issue 1: Retry Queue Tests (18 tests)

**Impact:** Retry queue mechanism
**Files:** `tests/test_retry_queue.py`

**Classes:**
- `TestRetryQueueStateTransitions` (7 tests)
- `TestRetryQueueCleanup` (5 tests)
- `TestRetryQueueExponentialBackoff` (4 tests)
- `TestRetryQueueAutomaticTriggers` (2 tests)

**Likely Issues:**
1. Cron jobs not running in test mode
2. DateTime mocking issues
3. State machine implementation bugs

**Investigation needed:**
- Review retry queue model implementation
- Check if tests need `@freeze_time` decorator
- Verify cron triggers work in test environment

**Estimated Fix Time:** 3-4 hours
**Expected Impact:** +18 tests passing

---

### Issue 2: Payment Method Validation (1 test)

**File:** `tests/test_payment_method.py`

**Error:**
```
AssertionError: ValidationError not raised
```

**Test:** `test_payment_method_code_validation`

**Fix:** Check if `_check_payment_method_code` constraint is properly defined

```python
# In models/payment_method.py
@api.constrains('code')
def _check_payment_method_code(self):
    for record in self:
        if record.code and not re.match(r'^[0-9]{2}$', record.code):
            raise ValidationError(_("Payment method code must be exactly 2 digits"))
```

**Estimated Fix Time:** 15 minutes
**Expected Impact:** +1 test passing

---

### Issue 3: XSD Validator Existence (1 test)

**File:** `tests/test_xsd_validator.py`

**Error:**
```
AssertionError: l10n_cr.xsd.validator() is not true
```

**Test:** `test_validator_exists`

**Fix:** Change assertion to check recordset properly

```python
# OLD:
def test_validator_exists(self):
    self.assertTrue(self.validator, "XSD validator model should exist")

# NEW:
def test_validator_exists(self):
    self.assertTrue(len(self.validator) > 0, "XSD validator model should exist")
    # OR
    self.assertNotEqual(self.validator, self.env['l10n_cr.xsd.validator'])
```

**Estimated Fix Time:** 5 minutes
**Expected Impact:** +1 test passing

---

## Fix Sequence Recommendation

### Day 1: Critical Setup (4-6 hours)
1. ✅ Create `tests/common.py` with `EInvoiceTestCase`
2. ✅ Update all test classes to inherit from base
3. ✅ Run test suite again
4. ✅ Verify ~47 tests now pass (target: 111/199 = 55.8%)

### Day 2: XML & Namespace Fixes (2-3 hours)
5. ✅ Fix XML namespace assertions (3 tests)
6. ✅ Debug and fix assertion None errors (9 tests)
7. ✅ Run tax report XML tests
8. ✅ Target: 123/199 = 61.8%

### Day 3: Workflow & Calculations (4-6 hours)
9. ✅ Fix tax calculation issues
10. ✅ Add Hacienda API mocks
11. ✅ Fix D101/D150/D151 workflow tests
12. ✅ Target: 160/199 = 80.4%

### Day 4: Cleanup & Edge Cases (3-4 hours)
13. ✅ Fix payment method validation (1 test)
14. ✅ Fix XSD validator existence (1 test)
15. ✅ Investigate retry queue tests (18 tests)
16. ✅ Target: 180/199 = 90.5%

### Day 5: Final Polish (2-3 hours)
17. ✅ Fix remaining retry queue tests
18. ✅ Full test suite run
19. ✅ Documentation updates
20. ✅ Final target: >90% pass rate

---

## Quick Commands

**Run all tests:**
```bash
docker compose run --rm odoo -d GMS \
  --test-tags=l10n_cr_einvoice,unit \
  --stop-after-init --no-http
```

**Run specific test class:**
```bash
docker compose run --rm odoo -d GMS \
  --test-tags=/TestXMLGeneratorCore \
  --stop-after-init --no-http
```

**Run specific test method:**
```bash
docker compose run --rm odoo -d GMS \
  --test-tags=/TestXMLGeneratorCore/test_generate_xml_basic \
  --stop-after-init --no-http
```

**Run with verbose output:**
```bash
docker compose run --rm odoo -d GMS \
  --test-tags=l10n_cr_einvoice,unit \
  --stop-after-init --no-http \
  --log-level=test:DEBUG
```

---

## Success Metrics

| Phase | Target Pass Rate | Tests Passing | Priority |
|-------|------------------|---------------|----------|
| Current | 32.2% | 64/199 | - |
| After P0 | 55.8% | 111/199 | 🔴 Critical |
| After P1 XML | 61.8% | 123/199 | 🟡 High |
| After P1 Workflow | 80.4% | 160/199 | 🟡 High |
| After P2 | 90.5% | 180/199 | 🟢 Medium |
| Final Goal | >95% | >189/199 | ✅ Target |

---

**Last Updated:** 2026-02-01
**Next Review:** After P0 fixes are applied
