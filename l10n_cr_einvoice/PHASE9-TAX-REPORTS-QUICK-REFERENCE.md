# Phase 9: Tax Reports (D-150, D-101, D-151) - Quick Reference

## Overview

Phase 9 adds Costa Rica tax report functionality to the e-invoicing module:
- **D-150**: Monthly VAT (IVA) declaration - IMPLEMENTED
- **D-101**: Annual income tax - Infrastructure ready
- **D-151**: Annual informative declaration - Infrastructure ready

Filing deadlines:
- D-150: 15th of following month
- D-101: March 15 of following year
- D-151: April 15 of following year

---

## Quick Access

### Main Menu
**Location:** Hacienda > Declaraciones Fiscales

### Submenu Items
- Períodos Fiscales (Tax Periods)
- D-150 Declaración de IVA (VAT Reports)
- D-101 Renta Anual (Income Tax) - Coming soon
- D-151 Informativa Anual (Informative) - Coming soon

---

## D-150 Monthly VAT Declaration

### Auto-Generation (Recommended)

The system automatically generates D-150 reports on the **1st of each month** for the previous month.

**What happens automatically:**
1. Creates tax period for previous month
2. Creates D-150 report
3. Calculates sales and purchases from accepted invoices/bills
4. Sends notification to accountants

**Example:** On December 1, 2025, the system creates:
- Period: "D-150 November 2025"
- Deadline: December 15, 2025
- Status: Calculated (ready for review)

### Manual Creation

If you need to create a D-150 manually:

1. Go to **Hacienda > Declaraciones Fiscales > Períodos Fiscales**
2. Click **Create**
3. Fill in:
   - **Report Type**: D-150 VAT Monthly
   - **Year**: 2025
   - **Month**: 11
   - **Date From**: Auto-fills to 2025-11-01
   - **Date To**: Auto-fills to 2025-11-30
   - **Deadline**: Auto-fills to 2025-12-15
4. Click **Save**
5. Click **Create Report** button
6. D-150 form opens automatically

---

## D-150 Workflow

### Step 1: Calculate

**Action:** Click **Calculate** button

**What it does:**
- Collects all accepted invoices (FE, TE) for the month
- Collects all accepted credit notes (NC)
- Calculates sales totals by tax rate (13%, 4%, 2%, 1%, exempt)
- Collects all vendor bills for the month
- Calculates purchase totals by tax rate
- Gets previous month's balance (if exists)
- Calculates final VAT due or credit

**Result:** Report state changes to "Calculated"

### Step 2: Review

**Review the calculated amounts:**

**Sales Section (IVA Generado):**
- Sales 13% Base: ₡X,XXX,XXX
- Sales 13% Tax: ₡XXX,XXX (calculated at 13%)
- Sales 4%, 2%, 1% (if applicable)
- Exempt Sales: ₡X,XXX
- Total VAT Collected: ₡XXX,XXX

**Purchases Section (IVA Soportado):**
- Purchases Goods 13%: ₡X,XXX,XXX (tax credit)
- Purchases Services 13%: ₡X,XXX,XXX (tax credit)
- Other rates if applicable
- Total VAT Credit: ₡XXX,XXX

**Settlement (Liquidación):**
- VAT Collected: ₡XXX,XXX
- VAT Credit: (₡XX,XXX)
- Proportionality Factor: 100% (usually)
- Adjusted Credit: (₡XX,XXX)
- Previous Balance: ₡0 or (₡XXX)
- **Net Amount Due**: ₡XX,XXX
  - If positive: Amount to Pay
  - If negative: Credit to Next Period

**Make corrections if needed:**
- Adjust proportionality factor (if you have exempt activities)
- Verify previous balance
- Add manual adjustments (advanced)

### Step 3: Generate XML

**Action:** Click **Generate XML** button

**What it does:**
- Creates TRIBU-CR format XML
- Includes all VAT amounts
- Adds company identification
- Stores XML in report

**Result:** Report state changes to "Ready to Submit"

### Step 4: Sign XML

**Action:** Click **Sign XML** button

**What it does:**
- Uses company's X.509 certificate
- Digitally signs the XML
- Validates signature

**Prerequisite:** Company must have valid certificate configured

**Result:** Signed XML stored in report

### Step 5: Submit to Hacienda

**Action:** Click **Submit to Hacienda** button

**What it does:**
- Sends signed XML to TRIBU-CR platform
- Receives submission key
- Records submission timestamp

**Result:**
- Report state: "Submitted"
- Submission key displayed
- Submission date recorded

### Step 6: Check Status

**Action:** Click **Check Status** button (or wait for auto-polling)

**Possible results:**
- **Accepted**: ✅ Report accepted by Hacienda
- **Rejected**: ❌ Report rejected (see error message)
- **Processing**: ⏳ Still being processed

**If accepted:**
- Report state: "Accepted"
- Period state: "Accepted"
- Credit/payment amount finalized

**If rejected:**
- Review error message
- Fix issues
- Reset to draft
- Recalculate and resubmit

---

## Understanding the Numbers

### Sales (Ventas - IVA Generado)

**What's included:**
- All accepted invoices (FE) for the month
- All accepted tickets (TE) for the month
- Grouped by tax rate

**What's excluded:**
- Draft invoices
- Rejected invoices
- Invoices still processing
- Credit notes (they reduce VAT)

### Purchases (Compras - IVA Soportado)

**What's included:**
- All posted vendor bills in the month
- Separated: Goods vs Services at 13%
- Grouped by other rates

**Goods vs Services:**
- Currently all treated as Goods
- TODO: Add product type detection

### Proportionality Factor

**Default:** 100% (all activities are taxed)

**When to adjust:**
- You have exempt activities AND taxed activities
- Calculate: (Taxed Sales / Total Sales) × 100
- Example: If 80% taxed, 20% exempt → Factor = 80%

**Effect:**
- Reduces your VAT credit proportionally
- Adjusted Credit = Total Credit × (Factor / 100)

### Previous Period Balance

**Automatically calculated** from previous month's D-150:
- If previous month had credit → Adds to current credit
- If previous month owed taxes → Reduces current credit

**Manual override** if needed (rare)

---

## Common Scenarios

### Scenario 1: Amount to Pay

**Example:**
- VAT Collected: ₡500,000
- VAT Credit: ₡200,000
- Net Amount Due: ₡300,000

**Action:** Pay ₡300,000 to Hacienda before deadline

### Scenario 2: Credit to Next Period

**Example:**
- VAT Collected: ₡200,000
- VAT Credit: ₡500,000
- Net Amount Due: (₡300,000) negative

**Result:** Credit of ₡300,000 carries forward to next month

### Scenario 3: Zero Activity

**Example:**
- No sales, no purchases
- VAT Collected: ₡0
- VAT Credit: ₡0
- Net Amount Due: ₡0

**Action:** Still file D-150 showing ₡0

---

## Automation Features

### Auto-Generation

**Cron Job:** Daily at midnight
**Trigger:** 1st of month
**Action:** Creates D-150 for previous month

**Notification:**
- Email to accountants
- Activity created in Odoo
- Message: "D-150 November 2025 ready for review"

### Overdue Reminders

**Cron Job:** Daily at midnight
**Trigger:** After deadline passes
**Action:** Sends urgent reminders

**Example:**
- Deadline: December 15
- Check on December 16: Sends "1 day overdue" alert
- Check on December 20: Sends "5 days overdue" urgent alert

---

## Troubleshooting

### Issue 1: Numbers Don't Match My Records

**Cause:** Report uses ACCEPTED invoices only

**Solution:**
1. Go to **Hacienda > Facturas Electrónicas**
2. Filter: Period = November, State = Accepted
3. Verify these match your expectations
4. Check if any invoices stuck in "Submitted" or "Error"
5. Fix those, then recalculate D-150

### Issue 2: Missing Purchases

**Cause:** Vendor bills not posted or outside date range

**Solution:**
1. Go to **Accounting > Vendors > Bills**
2. Check bills are **Posted** (not draft)
3. Check invoice_date is within period
4. Recalculate D-150

### Issue 3: Certificate Error on Sign

**Cause:** Certificate not configured or expired

**Solution:**
1. Go to **Settings > Companies > Your Company**
2. Check **Hacienda** tab
3. Verify certificate uploaded and not expired
4. If expired, upload new certificate

### Issue 4: Submission Fails

**Cause:** TRIBU-CR API error or credentials issue

**Solution:**
1. Check Hacienda credentials in company settings
2. Test connection: Settings > Companies > Test Connection
3. Check logs for detailed error
4. Retry submission after fixing

### Issue 5: Wrong Proportionality Factor

**Cause:** Manual adjustment needed for mixed activities

**Solution:**
1. Calculate: Taxed Sales / Total Sales
2. Edit D-150 report
3. Update "Proportionality Factor" field
4. Click "Calculate" again
5. Verify adjusted credit

---

## Data Reuse from Existing System

Phase 9 **reuses 80%** of existing data:

**From Phase 1-6:**
- ✅ Accepted invoices (FE, TE)
- ✅ Accepted credit notes (NC)
- ✅ Tax calculations by rate
- ✅ Vendor bills
- ✅ Company configuration
- ✅ Certificate manager
- ✅ XML generator
- ✅ XML signer
- ✅ Hacienda API client
- ✅ Retry queue

**New additions:**
- Tax period management
- D-150 report model
- TRIBU-CR XML format
- TRIBU-CR API endpoints
- Proportionality calculations
- Auto-generation cron

**Result:** Minimal new code, maximum reuse!

---

## API/Python Shell Examples

### Create Period Manually

```python
# Create D-150 period for November 2025
period = env['l10n_cr.tax.report.period'].create_monthly_period(2025, 11)

# Create and calculate report
period.action_create_report()
period.d150_report_id.action_calculate()
```

### Check All Overdue

```python
# Find overdue D-150 periods
overdue = env['l10n_cr.tax.report.period'].search([
    ('report_type', '=', 'd150'),
    ('deadline', '<', fields.Date.today()),
    ('state', 'in', ['draft', 'calculated']),
])

for period in overdue:
    days = (fields.Date.today() - period.deadline).days
    print(f"{period.name}: {days} days overdue")
```

### Get D-150 Data

```python
# Get November 2025 D-150
period = env['l10n_cr.tax.report.period'].search([
    ('report_type', '=', 'd150'),
    ('year', '=', 2025),
    ('month', '=', 11),
], limit=1)

d150 = period.d150_report_id

print(f"Sales 13%: {d150.sales_13_base} @ 13% = {d150.sales_13_tax}")
print(f"Purchases: {d150.purchases_total_tax}")
print(f"Net Due: {d150.net_amount_due}")
```

---

## File Locations

**Models:**
- `l10n_cr_einvoice/models/tax_report_period.py`
- `l10n_cr_einvoice/models/d150_vat_report.py`
- `l10n_cr_einvoice/models/tax_report_xml_generator.py`
- `l10n_cr_einvoice/models/hacienda_api.py` (extended)

**Data:**
- `l10n_cr_einvoice/data/tax_report_sequences.xml`
- `l10n_cr_einvoice/data/tax_report_cron_jobs.xml`

**Security:**
- `l10n_cr_einvoice/security/ir.model.access.csv` (updated)

---

## Next Steps

**Now:** D-150 is fully implemented and ready

**Coming Soon:**
- D-101 Annual Income Tax
- D-151 Annual Informative Declaration
- D-152 Purchase Withholdings
- D-158 Foreign Payments (with auto-detection)
- D-195 Inactive Declaration (with auto-validation)

---

## Support

**Documentation:** See TAX-REPORTS-IMPLEMENTATION-PLAN.md for full technical details

**Logs:** Settings > Technical > Logging > Filter: "tax_report"

**Issues:** Contact GMS Development Team

---

**Phase 9 Tax Reports - Version 19.0.1.10.0**
*Seamlessly integrated with Phases 1-8*
