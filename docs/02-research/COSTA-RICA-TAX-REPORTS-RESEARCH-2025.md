# Costa Rica Tax Reports Research - E-Invoicing Compliance 2025

## Executive Summary

This comprehensive research document covers the three critical tax reports required for Costa Rica e-invoicing compliance: D-104 (Monthly VAT), D-101 (Annual Income Tax), and D-151 (Annual Informative Declaration). As of 2025, significant changes are underway with the new TRIBU-CR platform replacing ATV, and Electronic Invoice version 4.4 becoming mandatory September 1, 2025.

**Key Findings:**
- D-104 is filed MONTHLY (not quarterly), deadline: 15th of following month
- D-101 is filed ANNUALLY, deadline: March 15 (extended to March 17, 2025 due to weekend)
- D-151 is filed ANNUALLY, deadline: February 28
- Starting August 2025, D-104 declarations will be pre-filled from electronic invoice data
- The new D-150 form in TRIBU-CR replaces the old activity-based D-104 with tariff-based reporting

---

## 1. D-104 - IVA (VAT) MONTHLY REPORT

### Overview
- **Official Name:** Declaración Jurada del Impuesto General sobre las Ventas
- **English:** Value Added Tax (VAT) Sworn Declaration
- **Frequency:** MONTHLY (not quarterly)
- **Filing Deadline:** Between day 1 and day 15 of the following month
- **Platform:** ATV portal (transitioning to TRIBU-CR in October 2025)

### Official Downloads
- **Form Location:** https://atv.hacienda.go.cr/ATV/frmExceles.aspx
- **Excel Template:** Available on ATV portal for offline preparation
- **New Platform:** TRIBU-CR launches October 6, 2025

### Filing Frequency & Deadlines

**Monthly Declaration:**
- Must be filed even if there is zero income
- Deadline: 15th of the following month (or next business day if weekend/holiday)
- Example: January 2025 activity → File by February 15, 2025

**2025 Major Changes:**
- August 2025: Pre-filled declarations begin based on electronic invoices
- September 2025: Electronic Invoice v4.4 becomes mandatory
- October 2025: TRIBU-CR system becomes official platform
- New Form: D-104 evolves into D-150 in TRIBU-CR

### Required Data Fields

#### Section 1: Period Information
- Tax period (month and year)
- Taxpayer identification (RUT)
- Economic activity codes

#### Section 2: Sales (Ventas)
**Taxable Sales by Rate (Ventas Gravadas):**
- 13% standard rate (general goods and services)
- 4% reduced rate (specific products)
- 2% reduced rate (specific services)
- 1% reduced rate (specific items)
- 5% rate (residential electricity over 250 KW)
- 10% rate (timber sales)

**Exempt Sales (Ventas Exentas):**
- With credit rights (con derecho a crédito fiscal):
  - Exports
  - Sales to free trade zones
  - Sales to CCSS (Social Security)
  - Sales to municipalities
- Without credit rights (sin derecho a crédito fiscal)

**Sales Totals:**
- Total net sales (before IVA)
- Total IVA débito (charged on sales)

#### Section 3: Purchases (Compras)
**Taxable Purchases by Rate:**
- 13% standard rate
- 4% reduced rate
- 2% reduced rate
- 1% reduced rate
- Separated by:
  - Goods (Bienes)
  - Services (Servicios)

**Creditable IVA:**
- National purchases with IVA
- Imported services
- Import duties (DUA)

**Total Purchase IVA:**
- Total IVA crédito fiscal (creditable IVA from purchases)

#### Section 4: Calculation & Settlement
- IVA Débito (from sales)
- IVA Crédito (from purchases)
- Proportionality adjustment (if mixed activities: taxable + exempt)
- Credit card processor withholdings
- Previous period credit balance
- **Net IVA Due or Credit**

### Calculation Methodology

**Basic Formula:**
```
IVA Payable = IVA Débito (Sales) - IVA Crédito (Purchases)
```

**Step-by-Step:**

1. **Calculate Sales IVA (IVA Débito):**
   - Net Sales × Tax Rate (usually 13%) = IVA Débito
   - Example: ₡10,000 net sales × 13% = ₡1,300 IVA Débito

2. **Calculate Purchase IVA (IVA Crédito):**
   - Only creditable if:
     - Valid electronic invoice received
     - Purchase is business-related
     - Invoice is "accepted" in Hacienda system
   - Net Purchases × Tax Rate (usually 13%) = IVA Crédito
   - Example: ₡1,000 net purchases × 13% = ₡130 IVA Crédito

3. **Apply Proportionality (if applicable):**
   - If company has both taxable and exempt sales
   - Formula: (Taxable Sales / Total Sales) × Total IVA Crédito
   - Only applicable credit = Proportional amount

4. **Calculate Net Amount:**
   - IVA Débito - IVA Crédito = Net IVA
   - If positive: Amount to pay
   - If negative: Credit balance for next period

5. **Subtract Withholdings:**
   - Credit card processor withholdings
   - Other authorized withholdings

**Example Calculation:**
```
Sales (net):           ₡100,000
IVA Débito (13%):       ₡13,000

Purchases (net):        ₡30,000
IVA Crédito (13%):       ₡3,900

Net IVA Due:           ₡9,100
Withholdings:          -₡500
FINAL AMOUNT TO PAY:   ₡8,600
```

### How to Generate from E-Invoice Data

**Data Source: account.move records in Odoo**

#### For IVA Débito (Sales):
```python
# Filter customer invoices for the period
invoices = self.env['account.move'].search([
    ('move_type', '=', 'out_invoice'),
    ('invoice_date', '>=', period_start),
    ('invoice_date', '<=', period_end),
    ('state', '=', 'posted'),
    ('country_code', '=', 'CR')
])

# Group by tax rate
sales_by_rate = {}
for invoice in invoices:
    for line in invoice.invoice_line_ids:
        for tax in line.tax_ids:
            rate = tax.amount
            if rate not in sales_by_rate:
                sales_by_rate[rate] = {
                    'base': 0.0,
                    'tax': 0.0
                }
            sales_by_rate[rate]['base'] += line.price_subtotal
            sales_by_rate[rate]['tax'] += line.price_total - line.price_subtotal
```

#### For IVA Crédito (Purchases):
```python
# Filter supplier bills for the period
# CRITICAL: Only include invoices with state = 'accepted' by Hacienda
bills = self.env['account.move'].search([
    ('move_type', '=', 'in_invoice'),
    ('invoice_date', '>=', period_start),
    ('invoice_date', '<=', period_end),
    ('state', '=', 'posted'),
    ('country_code', '=', 'CR'),
    ('l10n_cr_einvoice_status', '=', 'aceptado')  # Only accepted invoices
])

# Group by tax rate and type (goods vs services)
purchases_by_rate = {}
for bill in bills:
    for line in bill.invoice_line_ids:
        line_type = 'goods' if line.product_id.type == 'product' else 'services'
        for tax in line.tax_ids:
            rate = tax.amount
            key = f"{rate}_{line_type}"
            if key not in purchases_by_rate:
                purchases_by_rate[key] = {
                    'base': 0.0,
                    'tax': 0.0
                }
            purchases_by_rate[key]['base'] += line.price_subtotal
            purchases_by_rate[key]['tax'] += line.price_total - line.price_subtotal
```

#### Exempt Sales Tracking:
```python
# Track exempt sales with credit rights
exempt_with_credit = self.env['account.move'].search([
    ('move_type', '=', 'out_invoice'),
    ('invoice_date', '>=', period_start),
    ('invoice_date', '<=', period_end),
    ('state', '=', 'posted'),
    ('l10n_cr_export_status', '=', 'export'),  # Exports
    # OR
    ('partner_id.l10n_cr_free_zone', '=', True),  # Free trade zone
])

# Track exempt sales without credit rights
exempt_without_credit = self.env['account.move'].search([
    ('move_type', '=', 'out_invoice'),
    ('invoice_date', '>=', period_start),
    ('invoice_date', '<=', period_end),
    ('state', '=', 'posted'),
    ('l10n_cr_exempt_type', '=', 'no_credit'),
])
```

### TRIBU-CR Automation (Starting August 2025)

**Pre-filled Features:**
- System automatically extracts data from all electronic invoices (v4.4)
- Sales classified by tariff rate
- Purchases classified by type and rate
- Automatic proportionality calculations
- Real-time validation and discrepancy alerts

**What You Still Need to Do:**
1. Verify all invoices are emitted in version 4.4
2. Accept/register all received provider invoices promptly
3. Reconcile monthly between internal records and TRIBU-CR data
4. Monitor deferred IVA receipts (REP) for 90-day payment commitments
5. Review and approve the pre-filled declaration

### Penalties for Late Filing

**Late Filing Penalty:**
- Fine: Half a base salary (₡231,100 for 2025)
- Voluntary payment discount: 80% reduction → ₡46,220

**Late Payment Penalty:**
- 1% per month on unpaid tax amount
- Maximum: 20% total
- Calculated from due date until payment

**Non-Filing Penalty:**
- Minimum: 3 base salaries (₡1,386,600)
- Plus 1% monthly interest

### Important Notes

1. **Currency:** All amounts in Costa Rican colones (₡)
2. **Rounding:** No decimals, round to nearest unit
3. **Exchange Rates:** Use Central Bank of Costa Rica rates for foreign currency conversion
4. **Zero Declarations:** Required even with no activity
5. **Credit Balance:** Can be carried forward to next period or requested as refund

---

## 2. D-101 - RENTA (INCOME TAX) ANNUAL REPORT

### Overview
- **Official Name:** Declaración Jurada del Impuesto sobre la Renta
- **English:** Income Tax Sworn Declaration
- **Frequency:** ANNUALLY
- **Filing Deadline:** March 15 (extended if falls on weekend)
- **Tax Period:** Calendar year (January 1 - December 31)
- **Platform:** ATV portal (transitioning to TRIBU-CR)

### Official Downloads
- **Form Location:** https://atv.hacienda.go.cr/ATV/frmExceles.aspx
- **Official PDF:** https://www.hacienda.go.cr/docs/D-101DeclaracionImpuestossobrelaRenta_casilla46bis-papel.pdf
- **Instructions:** https://www.hacienda.go.cr/docs/CHARLAISU-2024-27-02-2025.pdf

### Filing Frequency & Deadlines

**Annual Declaration:**
- Tax Period: January 1 - December 31 of previous year
- Filing Deadline: March 15
- 2025 Deadline: March 17, 2025 (March 15 falls on Saturday)

**Who Must File:**
- Legal entities (corporations) with taxable income
- Independent workers and professionals
- Individuals with investment income
- Any entity obligated to file income tax returns

### Form Structure - 6 Main Blocks

#### Block 1: Assets and Liabilities (Activos y Pasivos)
- Total assets at year end
- Total liabilities at year end
- Net worth

#### Block 2: Income (Ingresos)
**Gross Income Sources:**
- Sales of goods and services
- Professional fees
- Investment income
- Capital gains
- Other income

**Key Fields:**
- Total gross income from all sources
- Income from salary (if applicable)
- Income from independent activities

#### Block 3: Costs, Expenses and Deductions (Costos, Gastos y Deducciones)
**Allowable Deductions:**
- Cost of goods sold (COGS)
- Operating expenses
- Salaries and benefits
- Depreciation
- Bad debts
- Professional fees
- Interest paid
- Other documented business expenses

**Special Deduction Option:**
- **Casilla 44:** 25% simplified deduction option
- Can claim 25% of gross income without documentation
- Alternative to itemizing all expenses
- Applies to professionals, technicians, sales agents, commission agents

**Important Fields:**
- Casilla 44: "Other costs, expenses and deductions permitted by Law"
- Casilla 46 bis: "Amount not subject applied to salary tax (annual accumulated)"

#### Block 4: Taxable Base (Base Imponible)
- Gross Income
- Less: Total Deductions
- **= Net Taxable Income**

#### Block 5: Tax Calculation & Credits
**Tax Rates:**

**Legal Entities (Personas Jurídicas):**
- Gross income > ₡119,626,000 (2025): Flat 30% rate on net income
- Gross income ≤ ₡119,626,000: Progressive brackets

**Progressive Brackets (for small entities):**
- Different rates apply based on net income levels
- Consult latest Hacienda guidelines for current brackets

**Credits Available:**
- **Casillas 58-84:** Various tax credits
- Partial payments made during the year
- Credits from other taxes
- Tax reductions for SMEs
- Family credits (for individuals)
- Withholdings at source

#### Block 6: Settlement of Tax Debt (Liquidación)
- Total tax calculated
- Less: Credits and partial payments
- **= Final amount due or credit**
- **Casilla 84:** Final balance

### Required Data Fields (Key Casillas)

**Income Section:**
- Casilla 1-20: Various income types
- Total gross income

**Deductions Section:**
- Casilla 21-44: Various expense categories
- Casilla 44: 25% simplified deduction OR total itemized expenses

**Tax Calculation:**
- Casilla 45-57: Tax computation
- Casilla 46 bis: Salary tax already paid (for mixed income earners)

**Credits:**
- Casilla 58-84: Credits and partial payments
- Casilla 84: Final settlement amount

### Calculation Methodology

**Standard Calculation:**
```
Step 1: Gross Income
  Total from all sources = Gross Income

Step 2: Net Income
  Gross Income - Allowable Deductions = Net Income

Step 3: Tax Calculation
  For Legal Entities with Gross Income > ₡119,626,000:
    Tax = Net Income × 30%

  For smaller entities:
    Apply progressive brackets

Step 4: Apply Credits
  Tax - Credits - Partial Payments = Amount Due/Credit

Step 5: Settlement
  If positive: Amount to pay
  If negative: Credit for next year or refund request
```

**Example for Legal Entity:**
```
Gross Income:              ₡150,000,000
Operating Expenses:        -₡50,000,000
Salaries:                  -₡30,000,000
Other Deductions:          -₡10,000,000
-----------------------------------------
Net Taxable Income:         ₡60,000,000

Tax (30%):                  ₡18,000,000
Partial Payments:           -₡5,000,000
-----------------------------------------
AMOUNT DUE:                 ₡13,000,000
```

**Example with 25% Simplified Deduction:**
```
Gross Professional Fees:    ₡40,000,000
25% Simplified Deduction:  -₡10,000,000  (Casilla 44)
-----------------------------------------
Net Taxable Income:         ₡30,000,000

Tax (30%):                   ₡9,000,000
Withholdings:               -₡2,000,000
-----------------------------------------
AMOUNT DUE:                  ₡7,000,000
```

### How to Generate from E-Invoice Data

**Data Source: account.move records in Odoo**

#### Calculate Gross Income:
```python
# Get all customer invoices for the year
income_invoices = self.env['account.move'].search([
    ('move_type', '=', 'out_invoice'),
    ('invoice_date', '>=', f'{year}-01-01'),
    ('invoice_date', '<=', f'{year}-12-31'),
    ('state', '=', 'posted'),
    ('company_id', '=', company_id),
])

# Calculate total gross income
gross_income = sum(invoice.amount_untaxed for invoice in income_invoices)
```

#### Calculate Deductible Expenses:
```python
# Get all supplier bills for the year
expense_bills = self.env['account.move'].search([
    ('move_type', '=', 'in_invoice'),
    ('invoice_date', '>=', f'{year}-01-01'),
    ('invoice_date', '<=', f'{year}-12-31'),
    ('state', '=', 'posted'),
    ('company_id', '=', company_id),
])

# Categorize by expense type
expense_by_category = {}
for bill in expense_bills:
    for line in bill.invoice_line_ids:
        account = line.account_id
        category = account.code[:2]  # First 2 digits of account code
        if category not in expense_by_category:
            expense_by_category[category] = 0.0
        expense_by_category[category] += line.price_subtotal

# Specific categories for D-101:
# 6xxx = Cost of Sales
# 7xxx = Operating Expenses
# 51xx = Salaries and Benefits
```

#### Calculate Depreciation:
```python
# Get depreciation entries from account.move.line
depreciation_account = self.env['account.account'].search([
    ('code', '=like', '68%'),  # Depreciation expense accounts
    ('company_id', '=', company_id),
])

depreciation_lines = self.env['account.move.line'].search([
    ('account_id', 'in', depreciation_account.ids),
    ('date', '>=', f'{year}-01-01'),
    ('date', '<=', f'{year}-12-31'),
    ('move_id.state', '=', 'posted'),
])

total_depreciation = sum(line.debit - line.credit for line in depreciation_lines)
```

#### Track Partial Payments:
```python
# Get tax payment records
tax_payments = self.env['account.payment'].search([
    ('payment_type', '=', 'outbound'),
    ('payment_date', '>=', f'{year}-01-01'),
    ('payment_date', '<=', f'{year}-12-31'),
    ('l10n_cr_tax_type', '=', 'income_tax'),  # Custom field
    ('state', '=', 'posted'),
])

total_partial_payments = sum(payment.amount for payment in tax_payments)
```

#### Generate D-101 Data Structure:
```python
d101_data = {
    # Block 2: Income
    'gross_income': gross_income,
    'service_income': service_income,
    'other_income': other_income,
    'total_income': gross_income + service_income + other_income,

    # Block 3: Deductions
    'cost_of_sales': expense_by_category.get('60', 0.0),
    'operating_expenses': expense_by_category.get('70', 0.0),
    'salaries': expense_by_category.get('51', 0.0),
    'depreciation': total_depreciation,
    'other_deductions': other_deductions,
    'total_deductions': total_deductions,

    # Simplified deduction option (Casilla 44)
    'simplified_deduction_25pct': gross_income * 0.25,

    # Block 4: Taxable Base
    'net_income': gross_income - total_deductions,

    # Block 5: Tax Calculation
    'tax_rate': 0.30 if gross_income > 119626000 else 'progressive',
    'tax_amount': net_income * 0.30,

    # Block 5: Credits (Casillas 58-84)
    'partial_payments': total_partial_payments,
    'other_credits': other_credits,
    'total_credits': total_partial_payments + other_credits,

    # Block 6: Settlement (Casilla 84)
    'amount_due': tax_amount - total_credits,
}
```

### Penalties for Late Filing

**Late Filing Penalty:**
- Fine: 50% of base salary = ₡231,100 (2025)
- Voluntary payment discount: 80% reduction
- Discounted amount: ₡46,220

**Late Payment Penalty:**
- 1% per month on unpaid tax amount
- Maximum: 20% total
- Accrues from March 15 until payment date

### Important Notes

1. **Fiscal Year:** Calendar year only (Jan 1 - Dec 31)
2. **Separate Declaration:** For 15-month transitional period (special cases)
3. **Electronic Submission:** Required through ATV/TRIBU-CR
4. **Supporting Documentation:** Must be retained for 5 years
5. **Audit Trail:** Keep detailed records of all calculations and source data

---

## 3. D-151 - DECLARACIÓN INFORMATIVA (INFORMATIVE DECLARATION)

### Overview
- **Official Name:** Declaración Informativa Resumen de Clientes, Proveedores y Gastos Específicos
- **English:** Informative Annual Summary of Clients, Suppliers and Specific Expenses
- **Frequency:** ANNUALLY
- **Filing Deadline:** February 28
- **Platform:** Declar@7 system (separate from ATV)
- **Important:** Only for non-electronic invoice transactions

### Official Downloads
- **Instructions:** https://www.hacienda.go.cr/docs/PresentacionDeclaracionesInformativasAnualesD-151_D-152_D-158.pdf
- **System:** Declar@7 portal (not ATV)
- **New TRIBU-CR Code:** Listed as "Informativa Resumen Mensual" with monthly periodicity in new system

### Filing Frequency & Deadlines

**Annual Declaration:**
- Tax Period: Previous calendar year (January 1 - December 31)
- Filing Deadline: February 28
- No extension available

**Important Change with Electronic Invoicing:**
- After e-invoicing implementation, D-151 only applies to:
  - Transactions with simplified regime taxpayers
  - Transactions NOT covered by electronic invoices
  - Most electronic invoices are auto-reported to Hacienda

### Who Must File

**Required to File:**
- All public entities (subject or not to income tax)
- International organizations
- Legal entities obligated to file income tax returns
- Individuals required to file D-101

**Exemptions:**
- Transactions backed by electronic vouchers (already reported)
- Amounts with withholding applied and reported on Form D-150

### Minimum Reporting Thresholds

#### For General Purchases/Sales:
- **Threshold:** ₡2,500,000 per year with same person/entity
- **Note:** Excludes IVA and consumption taxes
- Reports cumulative transactions that exceed threshold

#### For Specific Expenses (Services):
- **Threshold:** ₡50,000 per transaction
- **Applies to:**
  - Rental services (Alquileres)
  - Commissions
  - Professional services
  - Interest payments

**Conflicting Information Note:**
Some sources indicate reporting starts from ₡1, but official documents suggest thresholds above. Consult latest Hacienda guidelines.

### Required Data Fields

#### Taxpayer Information:
- Taxpayer identification (RUT)
- Tax period (year)
- Legal entity name

#### For Each Client (Customer):
- **Identification:** Cédula (ID number) or immigration document for foreigners
- **Name:** Full legal name
- **Transaction Type Code:** "V" (Ventas/Sales)
- **Total Amount:** Annual cumulative sales to this client
- **Amount excludes:** IVA and consumption taxes

#### For Each Supplier (Proveedor):
- **Identification:** Cédula (ID number) or immigration document
- **Name:** Full legal name
- **Transaction Type Code:** "C" (Compras/Purchases)
- **Total Amount:** Annual cumulative purchases from this supplier
- **Amount excludes:** IVA and consumption taxes

#### For Specific Expenses:
**Professional Services:**
- Code: "SP"
- Recipient identification
- Total amount paid for professional services
- Minimum: ₡50,000

**Rentals (Alquileres):**
- Code: "A"
- Landlord identification
- Total rent paid
- Minimum: ₡50,000

**Commissions:**
- Code: "M"
- Commission recipient identification
- Total commissions paid
- Minimum: ₡50,000

**Interest:**
- Code: "I"
- Creditor identification
- Total interest paid
- Minimum: ₡50,000

### Data Structure Example

```xml
<D-151>
  <Declarante>
    <Identificacion>3-101-654321</Identificacion>
    <Nombre>GYM FITNESS CR SA</Nombre>
    <Periodo>2024</Periodo>
  </Declarante>

  <Clientes>
    <Cliente>
      <Identificacion>1-0234-0567</Identificacion>
      <Nombre>Juan Pérez Mora</Nombre>
      <Codigo>V</Codigo>
      <Monto>3500000</Monto>
    </Cliente>
    <!-- More clients... -->
  </Clientes>

  <Proveedores>
    <Proveedor>
      <Identificacion>3-101-123456</Identificacion>
      <Nombre>Equipos Deportivos SA</Nombre>
      <Codigo>C</Codigo>
      <Monto>8500000</Monto>
    </Proveedor>
    <!-- More suppliers... -->
  </Proveedores>

  <GastosEspecificos>
    <Gasto>
      <Identificacion>2-0345-0678</Identificacion>
      <Nombre>María López González</Nombre>
      <Codigo>SP</Codigo>
      <Monto>1200000</Monto>
    </Gasto>
    <!-- More specific expenses... -->
  </GastosEspecificos>
</D-151>
```

### How to Generate from E-Invoice Data

**Important:** D-151 is primarily for NON-electronic transactions, but you can generate it from Odoo data for simplified regime partners.

#### Identify Non-Electronic Transactions:
```python
# Get all invoices/bills from simplified regime partners
# or those without electronic invoice validation

# For Clients (Sales - Code V)
non_einvoice_customers = self.env['res.partner'].search([
    ('l10n_cr_regime_type', '=', 'simplified'),  # Simplified regime
    ('customer_rank', '>', 0),
])

client_summary = {}
for customer in non_einvoice_customers:
    invoices = self.env['account.move'].search([
        ('partner_id', '=', customer.id),
        ('move_type', '=', 'out_invoice'),
        ('invoice_date', '>=', f'{year}-01-01'),
        ('invoice_date', '<=', f'{year}-12-31'),
        ('state', '=', 'posted'),
        ('l10n_cr_einvoice_status', '!=', 'accepted'),  # Not e-invoice
    ])

    total = sum(inv.amount_untaxed for inv in invoices)

    # Only include if exceeds threshold
    if total >= 2500000:
        client_summary[customer.id] = {
            'identification': customer.vat,
            'name': customer.name,
            'code': 'V',
            'amount': total,
        }
```

#### For Suppliers (Purchases - Code C):
```python
# For Proveedores (Purchases - Code C)
non_einvoice_suppliers = self.env['res.partner'].search([
    ('l10n_cr_regime_type', '=', 'simplified'),
    ('supplier_rank', '>', 0),
])

supplier_summary = {}
for supplier in non_einvoice_suppliers:
    bills = self.env['account.move'].search([
        ('partner_id', '=', supplier.id),
        ('move_type', '=', 'in_invoice'),
        ('invoice_date', '>=', f'{year}-01-01'),
        ('invoice_date', '<=', f'{year}-12-31'),
        ('state', '=', 'posted'),
        ('l10n_cr_einvoice_status', '!=', 'accepted'),
    ])

    total = sum(bill.amount_untaxed for bill in bills)

    if total >= 2500000:
        supplier_summary[supplier.id] = {
            'identification': supplier.vat,
            'name': supplier.name,
            'code': 'C',
            'amount': total,
        }
```

#### For Specific Expenses:
```python
# Professional Services (Code SP)
professional_services = self.env['account.move.line'].search([
    ('account_id.code', '=like', '725%'),  # Professional fees account
    ('date', '>=', f'{year}-01-01'),
    ('date', '<=', f'{year}-12-31'),
    ('move_id.state', '=', 'posted'),
])

# Group by partner
service_summary = {}
for line in professional_services:
    partner = line.partner_id
    if partner.id not in service_summary:
        service_summary[partner.id] = {
            'identification': partner.vat,
            'name': partner.name,
            'code': 'SP',
            'amount': 0.0,
        }
    service_summary[partner.id]['amount'] += line.price_subtotal

# Filter by minimum threshold
service_summary = {k: v for k, v in service_summary.items() if v['amount'] >= 50000}

# Similar logic for:
# - Rentals (Code A) - account 7210
# - Commissions (Code M) - account 7220
# - Interest (Code I) - account 8110
```

#### Generate D-151 Report:
```python
def generate_d151_report(self, year):
    """Generate D-151 Informative Declaration"""

    company = self.env.company

    d151_data = {
        'declarant': {
            'identification': company.vat,
            'name': company.name,
            'period': year,
        },
        'clients': self._get_client_summary(year),
        'suppliers': self._get_supplier_summary(year),
        'specific_expenses': {
            'professional_services': self._get_professional_services(year),
            'rentals': self._get_rentals(year),
            'commissions': self._get_commissions(year),
            'interest': self._get_interest_paid(year),
        }
    }

    return d151_data
```

### Penalties for Non-Compliance

**Total or Partial Non-Compliance:**
- **Fine:** 2% of gross income from prior income tax period
- **Minimum:** 3 base salaries = ₡1,386,600 (2025)
- **Maximum:** 100 base salaries = ₡46,220,000 (2025)

**Incorrect Information:**
- **Fine:** 1% of base salary per incorrect record
- **Per Record:** ₡4,622 (2025)
- Can accumulate for multiple errors

**Late Filing:**
- Same penalties as non-compliance
- No discount available for late filing

### Important Notes

1. **Declining Relevance:** With e-invoicing v4.4, D-151 applies to fewer transactions
2. **Simplified Regime Focus:** Mainly for transactions with simplified regime taxpayers
3. **Separate System:** Filed through Declar@7, not ATV
4. **Future Changes:** May be eliminated or merged into TRIBU-CR
5. **Cross-Check:** Hacienda uses D-151 to cross-verify income tax declarations

---

## IMPLEMENTATION RECOMMENDATIONS FOR ODOO

### Database Schema Additions

#### New Models:

**1. Tax Report Period:**
```python
class TaxReportPeriod(models.Model):
    _name = 'l10n.cr.tax.report.period'
    _description = 'Costa Rica Tax Report Period'

    name = fields.Char(compute='_compute_name')
    report_type = fields.Selection([
        ('d104', 'D-104 VAT Monthly'),
        ('d101', 'D-101 Income Tax Annual'),
        ('d151', 'D-151 Informative Annual'),
    ])
    year = fields.Integer(required=True)
    month = fields.Integer()  # Only for D-104
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    deadline = fields.Date(required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('filed', 'Filed'),
        ('paid', 'Paid'),
    ], default='draft')
```

**2. D-104 VAT Report:**
```python
class D104VATReport(models.Model):
    _name = 'l10n.cr.d104.report'
    _description = 'D-104 Monthly VAT Report'

    period_id = fields.Many2one('l10n.cr.tax.report.period')
    company_id = fields.Many2one('res.company')

    # Sales Section
    sales_13_base = fields.Monetary()
    sales_13_tax = fields.Monetary()
    sales_4_base = fields.Monetary()
    sales_4_tax = fields.Monetary()
    sales_2_base = fields.Monetary()
    sales_2_tax = fields.Monetary()
    sales_1_base = fields.Monetary()
    sales_1_tax = fields.Monetary()
    sales_exempt_with_credit = fields.Monetary()
    sales_exempt_no_credit = fields.Monetary()
    total_sales_tax = fields.Monetary(compute='_compute_totals')

    # Purchases Section
    purchases_goods_13_base = fields.Monetary()
    purchases_goods_13_tax = fields.Monetary()
    purchases_services_13_base = fields.Monetary()
    purchases_services_13_tax = fields.Monetary()
    # ... other rates
    total_purchases_tax = fields.Monetary(compute='_compute_totals')

    # Calculation
    proportionality_factor = fields.Float()
    adjusted_credit = fields.Monetary(compute='_compute_credit')
    withholdings = fields.Monetary()
    previous_credit = fields.Monetary()
    net_amount_due = fields.Monetary(compute='_compute_net_due')

    # Methods
    def action_calculate(self):
        """Calculate D-104 from invoice data"""
        self._calculate_sales()
        self._calculate_purchases()
        self._calculate_proportionality()
        self.state = 'calculated'

    def action_export_xml(self):
        """Export to ATV/TRIBU-CR format"""
        pass
```

**3. D-101 Income Tax Report:**
```python
class D101IncomeReport(models.Model):
    _name = 'l10n.cr.d101.report'
    _description = 'D-101 Annual Income Tax Report'

    period_id = fields.Many2one('l10n.cr.tax.report.period')
    company_id = fields.Many2one('res.company')

    # Block 2: Income
    gross_income_sales = fields.Monetary()
    gross_income_services = fields.Monetary()
    other_income = fields.Monetary()
    total_gross_income = fields.Monetary(compute='_compute_totals')

    # Block 3: Deductions
    cost_of_sales = fields.Monetary()
    operating_expenses = fields.Monetary()
    salaries_benefits = fields.Monetary()
    depreciation = fields.Monetary()
    other_deductions = fields.Monetary()
    use_simplified_25pct = fields.Boolean()
    simplified_deduction = fields.Monetary(compute='_compute_simplified')
    total_deductions = fields.Monetary(compute='_compute_totals')

    # Block 4: Taxable Base
    net_taxable_income = fields.Monetary(compute='_compute_net_income')

    # Block 5: Tax Calculation
    tax_rate = fields.Float(compute='_compute_tax_rate')
    tax_amount = fields.Monetary(compute='_compute_tax')

    # Block 5: Credits (Casillas 58-84)
    partial_payments = fields.Monetary()
    other_credits = fields.Monetary()
    total_credits = fields.Monetary(compute='_compute_totals')

    # Block 6: Settlement
    amount_due = fields.Monetary(compute='_compute_settlement')

    # Methods
    def action_calculate(self):
        """Calculate D-101 from annual data"""
        self._calculate_income()
        self._calculate_deductions()
        self._calculate_tax()
        self.state = 'calculated'
```

**4. D-151 Informative Report:**
```python
class D151InformativeReport(models.Model):
    _name = 'l10n.cr.d151.report'
    _description = 'D-151 Annual Informative Report'

    period_id = fields.Many2one('l10n.cr.tax.report.period')
    company_id = fields.Many2one('res.company')

    client_line_ids = fields.One2many('l10n.cr.d151.client.line', 'report_id')
    supplier_line_ids = fields.One2many('l10n.cr.d151.supplier.line', 'report_id')
    expense_line_ids = fields.One2many('l10n.cr.d151.expense.line', 'report_id')

class D151ClientLine(models.Model):
    _name = 'l10n.cr.d151.client.line'

    report_id = fields.Many2one('l10n.cr.d151.report')
    partner_id = fields.Many2one('res.partner')
    identification = fields.Char(related='partner_id.vat')
    name = fields.Char(related='partner_id.name')
    code = fields.Char(default='V')
    amount = fields.Monetary()

class D151SupplierLine(models.Model):
    _name = 'l10n.cr.d151.supplier.line'

    report_id = fields.Many2one('l10n.cr.d151.report')
    partner_id = fields.Many2one('res.partner')
    identification = fields.Char(related='partner_id.vat')
    name = fields.Char(related='partner_id.name')
    code = fields.Char(default='C')
    amount = fields.Monetary()

class D151ExpenseLine(models.Model):
    _name = 'l10n.cr.d151.expense.line'

    report_id = fields.Many2one('l10n.cr.d151.report')
    partner_id = fields.Many2one('res.partner')
    identification = fields.Char(related='partner_id.vat')
    name = fields.Char(related='partner_id.name')
    code = fields.Selection([
        ('SP', 'Professional Services'),
        ('A', 'Rentals'),
        ('M', 'Commissions'),
        ('I', 'Interest'),
    ])
    amount = fields.Monetary()
```

### Account Configuration

#### Chart of Accounts Mapping:

**Sales Accounts (Income):**
- 4110-4119: Product Sales (for D-104 and D-101)
- 4120-4129: Service Sales (for D-104 and D-101)
- 4130-4139: Membership Income (for D-104 and D-101)
- 4200-4299: Other Income (for D-101)

**Purchase/Expense Accounts:**
- 5110-5199: Cost of Goods Sold (for D-101)
- 6110-6199: Operating Expenses (for D-101)
- 6210-6219: Rent (for D-101 and D-151 - Code A)
- 6220-6229: Professional Services (for D-101 and D-151 - Code SP)
- 6230-6239: Commissions (for D-101 and D-151 - Code M)
- 7110-7199: Salary Expenses (for D-101)
- 7210: Depreciation (for D-101)
- 8110: Interest Expense (for D-101 and D-151 - Code I)

#### Tax Configuration:

**IVA Taxes (for D-104):**
```python
# 13% Standard Rate
{
    'name': 'IVA 13% (Ventas)',
    'amount': 13.0,
    'amount_type': 'percent',
    'type_tax_use': 'sale',
    'l10n_cr_tax_code': 'IVA_13',
}

{
    'name': 'IVA 13% (Compras)',
    'amount': 13.0,
    'amount_type': 'percent',
    'type_tax_use': 'purchase',
    'l10n_cr_tax_code': 'IVA_13',
}

# 4% Reduced Rate
{
    'name': 'IVA 4% (Ventas)',
    'amount': 4.0,
    'amount_type': 'percent',
    'type_tax_use': 'sale',
    'l10n_cr_tax_code': 'IVA_4',
}

# 2% Reduced Rate
{
    'name': 'IVA 2% (Ventas)',
    'amount': 2.0,
    'amount_type': 'percent',
    'type_tax_use': 'sale',
    'l10n_cr_tax_code': 'IVA_2',
}

# 1% Reduced Rate
{
    'name': 'IVA 1% (Ventas)',
    'amount': 1.0,
    'amount_type': 'percent',
    'type_tax_use': 'sale',
    'l10n_cr_tax_code': 'IVA_1',
}

# 0% Exempt with Credit
{
    'name': 'IVA 0% Exento con Crédito',
    'amount': 0.0,
    'amount_type': 'percent',
    'type_tax_use': 'sale',
    'l10n_cr_exempt_type': 'with_credit',
}

# 0% Exempt without Credit
{
    'name': 'IVA 0% Exento sin Crédito',
    'amount': 0.0,
    'amount_type': 'percent',
    'type_tax_use': 'sale',
    'l10n_cr_exempt_type': 'no_credit',
}
```

### Partner Configuration

**Add fields to res.partner:**
```python
class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_cr_regime_type = fields.Selection([
        ('traditional', 'Traditional Regime'),
        ('simplified', 'Simplified Regime'),
    ], default='traditional')

    l10n_cr_free_zone = fields.Boolean('Free Trade Zone Entity')

    l10n_cr_expense_category = fields.Selection([
        ('SP', 'Professional Services'),
        ('A', 'Rental'),
        ('M', 'Commission'),
        ('I', 'Interest'),
    ], help='For D-151 specific expenses')
```

### Report Generation Workflow

**Automated Monthly D-104:**
```python
@api.model
def _cron_generate_d104_monthly(self):
    """Scheduled action to generate D-104 on 1st of month"""
    today = fields.Date.today()
    if today.day == 1:
        # Generate for previous month
        last_month = today - relativedelta(months=1)

        for company in self.env['res.company'].search([('country_id.code', '=', 'CR')]):
            period = self.env['l10n.cr.tax.report.period'].create({
                'report_type': 'd104',
                'year': last_month.year,
                'month': last_month.month,
                'date_from': last_month.replace(day=1),
                'date_to': last_month + relativedelta(day=31),
                'deadline': today.replace(day=15),
            })

            report = self.env['l10n.cr.d104.report'].create({
                'period_id': period.id,
                'company_id': company.id,
            })

            report.action_calculate()
```

**Annual D-101:**
```python
@api.model
def _cron_generate_d101_annual(self):
    """Scheduled action to generate D-101 on Jan 1"""
    today = fields.Date.today()
    if today.month == 1 and today.day == 1:
        last_year = today.year - 1

        for company in self.env['res.company'].search([('country_id.code', '=', 'CR')]):
            period = self.env['l10n.cr.tax.report.period'].create({
                'report_type': 'd101',
                'year': last_year,
                'date_from': f'{last_year}-01-01',
                'date_to': f'{last_year}-12-31',
                'deadline': f'{today.year}-03-15',
            })

            report = self.env['l10n.cr.d101.report'].create({
                'period_id': period.id,
                'company_id': company.id,
            })

            report.action_calculate()
```

### User Interface - Menu Structure

```xml
<!-- Main Menu -->
<menuitem id="menu_l10n_cr_tax_reports"
    name="Costa Rica Tax Reports"
    parent="account.menu_finance_reports"
    sequence="100"/>

<!-- D-104 VAT Reports -->
<menuitem id="menu_l10n_cr_d104"
    name="D-104 VAT Monthly"
    parent="menu_l10n_cr_tax_reports"
    action="action_l10n_cr_d104_report"
    sequence="10"/>

<!-- D-101 Income Tax Reports -->
<menuitem id="menu_l10n_cr_d101"
    name="D-101 Income Tax Annual"
    parent="menu_l10n_cr_tax_reports"
    action="action_l10n_cr_d101_report"
    sequence="20"/>

<!-- D-151 Informative Reports -->
<menuitem id="menu_l10n_cr_d151"
    name="D-151 Informative Annual"
    parent="menu_l10n_cr_tax_reports"
    action="action_l10n_cr_d151_report"
    sequence="30"/>
```

### Export Formats

**XML Export for ATV/TRIBU-CR:**
```python
def export_d104_xml(self):
    """Export D-104 to XML format for TRIBU-CR"""
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<D104>
    <Periodo>
        <Anio>{self.period_id.year}</Anio>
        <Mes>{self.period_id.month}</Mes>
    </Periodo>
    <Declarante>
        <Identificacion>{self.company_id.vat}</Identificacion>
        <Nombre>{self.company_id.name}</Nombre>
    </Declarante>
    <Ventas>
        <VentasGravadas>
            <Tarifa13>
                <Base>{self.sales_13_base}</Base>
                <Impuesto>{self.sales_13_tax}</Impuesto>
            </Tarifa13>
            <Tarifa4>
                <Base>{self.sales_4_base}</Base>
                <Impuesto>{self.sales_4_tax}</Impuesto>
            </Tarifa4>
        </VentasGravadas>
        <VentasExentas>
            <ConCredito>{self.sales_exempt_with_credit}</ConCredito>
            <SinCredito>{self.sales_exempt_no_credit}</SinCredito>
        </VentasExentas>
    </Ventas>
    <Compras>
        <ComprasGravadas>
            <Bienes>
                <Tarifa13>
                    <Base>{self.purchases_goods_13_base}</Base>
                    <Impuesto>{self.purchases_goods_13_tax}</Impuesto>
                </Tarifa13>
            </Bienes>
            <Servicios>
                <Tarifa13>
                    <Base>{self.purchases_services_13_base}</Base>
                    <Impuesto>{self.purchases_services_13_tax}</Impuesto>
                </Tarifa13>
            </Servicios>
        </ComprasGravadas>
    </Compras>
    <Liquidacion>
        <IVADebito>{self.total_sales_tax}</IVADebito>
        <IVACredito>{self.adjusted_credit}</IVACredito>
        <Retenciones>{self.withholdings}</Retenciones>
        <SaldoFavor>{self.previous_credit}</SaldoFavor>
        <MontoPagar>{max(self.net_amount_due, 0)}</MontoPagar>
        <SaldoProximoPeriodo>{abs(min(self.net_amount_due, 0))}</SaldoProximoPeriodo>
    </Liquidacion>
</D104>
"""
    return xml_content
```

**Excel Export:**
```python
def export_d104_excel(self):
    """Export to Excel format matching ATV template"""
    # Use xlsxwriter or openpyxl to create Excel file
    # matching official ATV D-104 template layout
    pass
```

### Validation & Compliance Checks

**Pre-submission Validation:**
```python
def validate_d104_report(self):
    """Validate D-104 before submission"""
    errors = []

    # Check all invoices are accepted
    unaccepted = self._check_unaccepted_invoices()
    if unaccepted:
        errors.append(f"{len(unaccepted)} invoices not yet accepted by Hacienda")

    # Check for missing tax configurations
    if not self.sales_13_base and not self.sales_exempt_with_credit:
        errors.append("No sales data found for period")

    # Check calculations
    if abs(self.net_amount_due - self._recalculate_net_due()) > 1:
        errors.append("Calculation mismatch detected")

    # Check deadline
    if fields.Date.today() > self.period_id.deadline:
        errors.append(f"Past deadline: {self.period_id.deadline}")

    return errors
```

---

## APPENDIX A: QUICK REFERENCE TABLES

### Tax Report Comparison Matrix

| Report | Frequency | Deadline | Purpose | Platform | Mandatory |
|--------|-----------|----------|---------|----------|-----------|
| D-104 | Monthly | 15th of next month | VAT Declaration | ATV → TRIBU-CR | Yes (if VAT registered) |
| D-101 | Annual | March 15 | Income Tax | ATV → TRIBU-CR | Yes (if taxable income) |
| D-151 | Annual | February 28 | Informative Summary | Declar@7 | Yes (with conditions) |

### IVA Tax Rates (for D-104)

| Rate | Application | Common Products/Services |
|------|-------------|--------------------------|
| 13% | Standard | Most goods and services, gym memberships, supplements |
| 4% | Reduced | Specific agricultural products |
| 2% | Reduced | Specific services |
| 1% | Reduced | Specific items |
| 5% | Special | Residential electricity >250 KW |
| 10% | Special | Timber sales |
| 0% | Exempt with credit | Exports, free trade zones, CCSS, municipalities |
| 0% | Exempt no credit | Specific exempt services |

### Income Tax Rates (for D-101)

| Entity Type | Gross Income | Rate | Notes |
|-------------|--------------|------|-------|
| Legal Entity | > ₡119,626,000 | 30% flat | On net income |
| Legal Entity | ≤ ₡119,626,000 | Progressive | Various brackets |
| Individual | Depends on brackets | Progressive | Different from entities |
| Simplified Deduction | Any | 25% of gross | Alternative to itemizing |

### D-151 Minimum Thresholds

| Transaction Type | Code | Minimum Amount | Notes |
|------------------|------|----------------|-------|
| General Sales | V | ₡2,500,000/year | Per client, excludes IVA |
| General Purchases | C | ₡2,500,000/year | Per supplier, excludes IVA |
| Professional Services | SP | ₡50,000 | Per transaction |
| Rentals | A | ₡50,000 | Per transaction |
| Commissions | M | ₡50,000 | Per transaction |
| Interest | I | ₡50,000 | Per transaction |

### Penalty Schedule (2025)

| Violation | Form | Penalty | Discount | Final Amount |
|-----------|------|---------|----------|--------------|
| Late filing D-104 | D-104 | 50% base salary | 80% if voluntary | ₡46,220 |
| Late filing D-101 | D-101 | 50% base salary | 80% if voluntary | ₡46,220 |
| Non-filing D-151 | D-151 | 2% of gross income | None | Min ₡1,386,600 / Max ₡46,220,000 |
| Incorrect D-151 data | D-151 | 1% base salary/record | None | ₡4,622 per error |
| Late payment | Any | 1% per month | N/A | Max 20% of tax due |

**Base Salary 2025:** ₡462,200

---

## APPENDIX B: USEFUL RESOURCES

### Official Government Links

**Ministry of Finance (Hacienda):**
- Main Portal: https://www.hacienda.go.cr
- ATV Portal: https://atv.hacienda.go.cr/ATV/login.aspx
- Excel Forms: https://atv.hacienda.go.cr/ATV/frmExceles.aspx
- TRIBU-CR Info: https://www.hacienda.go.cr/AvisosTRIBU-CR.html

**Official Documents:**
- D-104 Resolution: https://pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=89100&nValor3=116971&strTipM=TC
- IVA Law: https://pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?nValor1=1&nValor2=32526
- Income Tax Law: https://pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=10969&nValor3=11751&strTipM=TC

### Technical Implementation

**Odoo Community:**
- Costa Rica Localization: https://github.com/odoocr/l10n_cr
- Odoo Apps Store: https://apps.odoo.com/apps/modules/17.0/l10n_cr_invoice

**Service Providers:**
- Facturele: https://www.facturele.com
- Factun: https://factun.com/cr/

### Calculators & Tools

- IVA Calculator: https://ivacalculator.com/costa-rica/
- D-101 Calculator: https://calculadorarenta-d101.azurewebsites.net/

---

## APPENDIX C: TRIBU-CR TRANSITION TIMELINE

### Key Dates for 2025

| Date | Event | Impact |
|------|-------|--------|
| August 2025 | Pre-filled D-104 begins | First pre-filled declaration for July activity |
| September 1, 2025 | E-Invoice v4.4 mandatory | All new invoices must use v4.4 format |
| October 6, 2025 | TRIBU-CR launch | Official platform for all declarations |
| Ongoing 2025 | ATV phase-out | Gradual transition from ATV to TRIBU-CR |

### What Changes with TRIBU-CR

**Before (ATV):**
- Manual data entry for all fields
- Separate activity-based reporting
- Offline Excel template preparation
- Manual reconciliation with invoices

**After (TRIBU-CR):**
- Pre-filled from electronic invoices
- Tariff-based reporting (by tax rate)
- Integrated online platform
- Automatic reconciliation
- Real-time validation
- Integrated payment processing

---

## APPENDIX D: SAMPLE CALCULATION SCENARIOS

### Scenario 1: Simple Gym (D-104 Monthly)

**Gym Fitness CR - January 2025**

**Sales:**
- Memberships: ₡8,000,000 (net) × 13% = ₡1,040,000 IVA
- Personal training: ₡2,000,000 (net) × 13% = ₡260,000 IVA
- Supplements: ₡1,500,000 (net) × 13% = ₡195,000 IVA
- **Total Sales IVA Débito: ₡1,495,000**

**Purchases:**
- Equipment: ₡3,000,000 (net) × 13% = ₡390,000 IVA (Goods)
- Cleaning services: ₡500,000 (net) × 13% = ₡65,000 IVA (Services)
- Supplements inventory: ₡800,000 (net) × 13% = ₡104,000 IVA (Goods)
- **Total Purchase IVA Crédito: ₡559,000**

**Calculation:**
- IVA Débito: ₡1,495,000
- IVA Crédito: -₡559,000
- Credit card withholdings: -₡50,000
- **NET IVA DUE: ₡886,000**

**File by:** February 15, 2025

---

### Scenario 2: Gym with Mixed Activities (D-104)

**Gym Elite SA - January 2025**

**Sales:**
- Regular memberships (taxable 13%): ₡10,000,000 → IVA ₡1,300,000
- Corporate wellness (exempt with credit): ₡2,000,000 → IVA ₡0
- **Total Sales: ₡12,000,000**

**Purchases:**
- Equipment: ₡4,000,000 → IVA ₡520,000
- Services: ₡1,000,000 → IVA ₡130,000
- **Total Purchase IVA: ₡650,000**

**Proportionality:**
- Taxable sales / Total sales = ₡10,000,000 / ₡12,000,000 = 83.33%
- Creditable IVA = ₡650,000 × 83.33% = ₡541,645

**Calculation:**
- IVA Débito: ₡1,300,000
- Adjusted IVA Crédito: -₡541,645
- **NET IVA DUE: ₡758,355**

---

### Scenario 3: Annual Income Tax (D-101)

**Gym Fitness CR SA - Year 2024**

**Income:**
- Membership sales: ₡96,000,000
- PT sessions: ₡24,000,000
- Supplement sales: ₡18,000,000
- **Gross Income: ₡138,000,000**

**Deductions:**
- Cost of supplements sold: ₡9,000,000
- Salaries and benefits: ₡36,000,000
- Rent: ₡12,000,000
- Equipment depreciation: ₡3,000,000
- Utilities: ₡4,800,000
- Marketing: ₡2,400,000
- Other operating: ₡6,800,000
- **Total Deductions: ₡74,000,000**

**Tax Calculation:**
- Gross Income: ₡138,000,000 (exceeds ₡119,626,000)
- Net Income: ₡138,000,000 - ₡74,000,000 = ₡64,000,000
- Tax Rate: 30% (flat rate applies)
- **Tax Due: ₡64,000,000 × 30% = ₡19,200,000**

**Credits:**
- Partial payments made in 2024: ₡15,000,000

**Final Settlement:**
- Tax Due: ₡19,200,000
- Credits: -₡15,000,000
- **AMOUNT TO PAY: ₡4,200,000**

**File by:** March 17, 2025

---

### Scenario 4: D-151 Informative Report

**Gym Fitness CR SA - Year 2024**

**Clients (Code V) - Simplified Regime Only:**
- Corporate Client A: ₡3,200,000 (exceeds threshold) ✓ Include
- Corporate Client B: ₡1,800,000 (below threshold) ✗ Exclude
- Individual Client C: ₡2,600,000 (exceeds threshold) ✓ Include

**Suppliers (Code C) - Simplified Regime Only:**
- Equipment Supplier: ₡8,500,000 ✓ Include
- Small cleaning service: ₡1,200,000 ✗ Exclude

**Specific Expenses:**
- Accountant (SP): ₡2,400,000 ✓ Include
- Lawyer (SP): ₡800,000 ✓ Include
- Building rent (A): ₡12,000,000 ✓ Include
- Equipment lease (A): ₡600,000 ✓ Include

**D-151 Lines to Report:**
- 2 Client lines (V)
- 1 Supplier line (C)
- 2 Professional service lines (SP)
- 2 Rental lines (A)
- **Total: 7 lines**

**File by:** February 28, 2025

---

## CONCLUSION

This research provides comprehensive coverage of Costa Rica's three primary tax reports required for e-invoicing compliance. The transition to TRIBU-CR and Electronic Invoice v4.4 in 2025 represents a significant modernization of the tax system, with increased automation and pre-filled declarations reducing manual work.

**Key Implementation Priorities:**

1. **Immediate (Q1 2025):**
   - Implement D-104 monthly VAT report generation
   - Ensure all invoices transition to v4.4 format by September 1
   - Configure tax codes and account mappings

2. **Short-term (Q2-Q3 2025):**
   - Build D-101 annual income tax calculation engine
   - Implement D-151 for non-electronic transactions
   - Prepare for TRIBU-CR integration (October 6)

3. **Ongoing:**
   - Monitor Hacienda updates and regulatory changes
   - Test pre-filled declaration accuracy
   - Maintain compliance with filing deadlines

**Success Metrics:**
- 100% on-time filing (before 15th each month for D-104)
- Zero penalties for late or incorrect filings
- Automated reconciliation between Odoo and TRIBU-CR
- Seamless user experience for accountants

For any questions or clarifications, consult official Hacienda documentation or engage a certified Costa Rican tax advisor.

---

**Document Version:** 1.0
**Last Updated:** December 31, 2025
**Author:** Market Trend Analyst - GMS Project
**Status:** Research Complete - Ready for Implementation
