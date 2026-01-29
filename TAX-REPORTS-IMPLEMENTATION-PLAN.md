# Costa Rica Tax Reports (D-150/D-104, D-101, D-151) - Implementation Plan

**Date:** 2025-12-31
**Module:** `l10n_cr_einvoice` (Odoo 19)
**Current Status:** Phases 1-8 Complete (E-Invoicing Production Ready)
**New Feature:** Phase 9 - Tax Report Generation & Submission

---

## Executive Summary

This implementation plan leverages:
- ✅ **Existing research** from `COSTA-RICA-TAX-REPORTS-RESEARCH-2025.md` (field specs, calculations)
- ✅ **New research** from `technical-costa-rica-tax-reports-research-2025-12-31.md` (architecture, patterns)
- ✅ **Working codebase** (`l10n_cr_einvoice` with XML generation, digital signatures, Hacienda API)

**Goal:** Add D-150 (monthly VAT), D-101 (annual income tax), and D-151 (informative) report generation and submission to your existing e-invoicing module.

---

## What You Already Have (Reusable)

### ✅ Infrastructure (Phase 1-8)
1. **XML Generation** (`models/xml_generator.py`) - Reuse for tax report XMLs
2. **Digital Signatures** (`models/xml_signer.py`) - Sign tax reports with XAdES
3. **Hacienda API Client** (`models/hacienda_api.py`) - Submit tax reports
4. **Certificate Management** (`models/certificate_manager.py`) - Same certs for reports
5. **Retry Queue** (`models/einvoice_retry_queue.py`) - Handle failed submissions
6. **Response Messages** (`models/hacienda_response_message.py`) - Track validation results
7. **Analytics Dashboard** (`models/einvoice_analytics_dashboard.py`) - Already has monthly summaries!

### ✅ Data You're Already Collecting
- **Monthly Filing Report** (`reports/hacienda_reports.py::get_monthly_filing_report()`)
  - Sales by tax rate (13%, 4%, 2%, 1%)
  - Tax calculations
  - Document counts
  - **This is 80% of D-104 data!**

---

## What's Missing (To Implement)

### ❌ New Models Needed
1. `l10n_cr.tax.report.period` - Track reporting periods and deadlines
2. `l10n_cr.d150.report` - D-150 monthly VAT declaration
3. `l10n_cr.d101.report` - D-101 annual income tax
4. `l10n_cr.d151.report` - D-151 annual informative
5. `l10n_cr.d151.line` - D-151 client/supplier/expense lines

### ❌ New XML Generators
1. D-150 XML format (for TRIBU-CR submission)
2. D-101 XML format
3. D-151 XML format

### ❌ New Views & Menus
1. Tax Reports menu (under Hacienda)
2. Report generation wizards
3. Report list views with export buttons

---

## Implementation Architecture

### Architectural Pattern: **Extend Existing Module**

Following your existing pattern and the architectural research:

```
l10n_cr_einvoice/
├── models/
│   ├── tax_report_period.py          # NEW - Period tracking
│   ├── d150_vat_report.py             # NEW - Monthly VAT
│   ├── d101_income_report.py          # NEW - Annual income tax
│   ├── d151_informative_report.py     # NEW - Annual informative
│   ├── tax_report_xml_generator.py    # NEW - Extend xml_generator.py
│   └── hacienda_api.py                # EXTEND - Add report submission methods
├── wizards/
│   └── tax_report_wizard.py           # NEW - Generate report wizard
├── views/
│   ├── tax_report_period_views.xml    # NEW
│   ├── d150_vat_report_views.xml      # NEW
│   ├── d101_income_report_views.xml   # NEW
│   ├── d151_informative_report_views.xml # NEW
│   └── tax_reports_menu.xml           # NEW
├── data/
│   └── tax_report_cron_jobs.xml       # NEW - Auto-generate monthly
└── reports/
    └── tax_report_templates.xml        # NEW - PDF reports
```

**Design Pattern:** Repository + Service Layer
- **Repository Pattern:** Models access data (`account.move`, `account.payment`)
- **Service Layer:** Calculation logic separated from models
- **Adapter Pattern:** Convert Odoo data → Tax report XML

---

## Phase 9A: D-150 Monthly VAT Report (Priority 1)

### Why D-150 First?
1. **Deadline: 15th of every month** - Most urgent
2. **80% data already collected** in `get_monthly_filing_report()`
3. **Reuses existing infrastructure** (XML, signature, API)

### Implementation Steps

#### Step 1: Create Tax Report Period Model
**File:** `models/tax_report_period.py`

```python
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class TaxReportPeriod(models.Model):
    _name = 'l10n_cr.tax.report.period'
    _description = 'Costa Rica Tax Report Period'
    _order = 'date_from desc'

    name = fields.Char(compute='_compute_name', store=True)
    report_type = fields.Selection([
        ('d150', 'D-150 VAT Monthly'),
        ('d101', 'D-101 Income Tax Annual'),
        ('d151', 'D-151 Informative Annual'),
    ], required=True)
    year = fields.Integer(required=True)
    month = fields.Integer()  # Only for D-150
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    deadline = fields.Date(required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], default='draft')

    d150_report_id = fields.Many2one('l10n_cr.d150.report')
    d101_report_id = fields.Many2one('l10n_cr.d101.report')
    d151_report_id = fields.Many2one('l10n_cr.d151.report')

    @api.depends('report_type', 'year', 'month')
    def _compute_name(self):
        for record in self:
            if record.report_type == 'd150':
                record.name = f"D-150 {record.year}-{record.month:02d}"
            elif record.report_type == 'd101':
                record.name = f"D-101 {record.year}"
            elif record.report_type == 'd151':
                record.name = f"D-151 {record.year}"
```

#### Step 2: Create D-150 VAT Report Model
**File:** `models/d150_vat_report.py`

```python
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class D150VATReport(models.Model):
    _name = 'l10n_cr.d150.report'
    _description = 'D-150 Monthly VAT Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(compute='_compute_name', store=True)
    period_id = fields.Many2one('l10n_cr.tax.report.period', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', related='period_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    state = fields.Selection(related='period_id.state', store=True)

    # Sales Section (Ventas)
    sales_13_base = fields.Monetary(string='Sales 13% - Base', tracking=True)
    sales_13_tax = fields.Monetary(string='Sales 13% - Tax', tracking=True)
    sales_4_base = fields.Monetary(string='Sales 4% - Base')
    sales_4_tax = fields.Monetary(string='Sales 4% - Tax')
    sales_2_base = fields.Monetary(string='Sales 2% - Base')
    sales_2_tax = fields.Monetary(string='Sales 2% - Tax')
    sales_1_base = fields.Monetary(string='Sales 1% - Base')
    sales_1_tax = fields.Monetary(string='Sales 1% - Tax')

    sales_exempt_with_credit = fields.Monetary(string='Exempt Sales (with credit)')
    sales_exempt_no_credit = fields.Monetary(string='Exempt Sales (no credit)')

    total_sales_base = fields.Monetary(compute='_compute_totals', store=True)
    total_sales_tax = fields.Monetary(string='Total IVA Débito', compute='_compute_totals', store=True)

    # Purchases Section (Compras)
    purchases_goods_13_base = fields.Monetary(string='Goods 13% - Base')
    purchases_goods_13_tax = fields.Monetary(string='Goods 13% - Tax')
    purchases_services_13_base = fields.Monetary(string='Services 13% - Base')
    purchases_services_13_tax = fields.Monetary(string='Services 13% - Tax')
    # Add other rates as needed (4%, 2%, 1%)

    total_purchases_base = fields.Monetary(compute='_compute_totals', store=True)
    total_purchases_tax = fields.Monetary(string='Total IVA Crédito', compute='_compute_totals', store=True)

    # Calculation & Settlement (Liquidación)
    proportionality_factor = fields.Float(string='Proportionality %', default=100.0,
                                         help='For mixed activities (taxable + exempt)')
    adjusted_credit = fields.Monetary(string='Adjusted IVA Credit', compute='_compute_settlement', store=True)
    withholdings = fields.Monetary(string='Withholdings')
    previous_credit = fields.Monetary(string='Previous Period Credit')
    net_amount_due = fields.Monetary(string='Net Amount Due/Credit', compute='_compute_settlement', store=True)

    # Submission tracking
    xml_content = fields.Text('XML Content')
    xml_signed = fields.Text('Signed XML')
    submission_date = fields.Datetime('Submission Date')
    hacienda_response = fields.Text('Hacienda Response')

    @api.depends('period_id.year', 'period_id.month')
    def _compute_name(self):
        for record in self:
            if record.period_id:
                record.name = f"D-150 {record.period_id.year}-{record.period_id.month:02d}"

    @api.depends('sales_13_base', 'sales_13_tax', 'sales_4_base', 'sales_4_tax',
                 'purchases_goods_13_base', 'purchases_goods_13_tax',
                 'purchases_services_13_base', 'purchases_services_13_tax')
    def _compute_totals(self):
        for record in self:
            # Sales totals
            record.total_sales_base = (
                record.sales_13_base + record.sales_4_base +
                record.sales_2_base + record.sales_1_base
            )
            record.total_sales_tax = (
                record.sales_13_tax + record.sales_4_tax +
                record.sales_2_tax + record.sales_1_tax
            )

            # Purchase totals
            record.total_purchases_base = (
                record.purchases_goods_13_base + record.purchases_services_13_base
            )
            record.total_purchases_tax = (
                record.purchases_goods_13_tax + record.purchases_services_13_tax
            )

    @api.depends('total_sales_tax', 'total_purchases_tax', 'proportionality_factor',
                 'withholdings', 'previous_credit')
    def _compute_settlement(self):
        for record in self:
            # Apply proportionality to credit
            record.adjusted_credit = record.total_purchases_tax * (record.proportionality_factor / 100.0)

            # Calculate net amount
            record.net_amount_due = (
                record.total_sales_tax -
                record.adjusted_credit -
                record.withholdings -
                record.previous_credit
            )

    def action_calculate(self):
        """Calculate D-150 from invoice data - REUSE existing method!"""
        self.ensure_one()

        # Get data from existing hacienda_reports.py
        HaciendaReports = self.env['report.l10n_cr_einvoice.hacienda_reports']
        data = HaciendaReports.get_monthly_filing_report(
            self.period_id.year,
            self.period_id.month
        )

        # Map to D-150 fields
        tax_by_rate = {item['rate']: item for item in data.get('tax_by_rate', [])}

        # Sales (from invoices + receipts)
        rate_13 = tax_by_rate.get(13.0, {'base': 0, 'tax': 0})
        self.sales_13_base = rate_13['base']
        self.sales_13_tax = rate_13['tax']

        rate_4 = tax_by_rate.get(4.0, {'base': 0, 'tax': 0})
        self.sales_4_base = rate_4['base']
        self.sales_4_tax = rate_4['tax']

        # Purchases (need to add similar logic to hacienda_reports.py)
        self._calculate_purchases()

        # Calculate proportionality if needed
        if self.sales_exempt_with_credit > 0:
            total_sales = self.total_sales_base + self.sales_exempt_with_credit + self.sales_exempt_no_credit
            if total_sales > 0:
                self.proportionality_factor = (self.total_sales_base / total_sales) * 100.0

        self.period_id.state = 'generated'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('D-150 report calculated successfully'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _calculate_purchases(self):
        """Calculate creditable purchases by rate and type"""
        # Filter supplier bills for the period
        # CRITICAL: Only include invoices accepted by Hacienda
        domain = [
            ('move_type', '=', 'in_invoice'),
            ('invoice_date', '>=', self.period_id.date_from),
            ('invoice_date', '<=', self.period_id.date_to),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id),
        ]

        bills = self.env['account.move'].search(domain)

        goods_13_base = goods_13_tax = 0.0
        services_13_base = services_13_tax = 0.0

        for bill in bills:
            # Check if einvoice document exists and is accepted
            einvoice_doc = self.env['l10n_cr.einvoice.document'].search([
                ('move_id', '=', bill.id)
            ], limit=1)

            # Only credit if accepted by Hacienda
            if einvoice_doc and einvoice_doc.state != 'accepted':
                continue

            for line in bill.invoice_line_ids:
                for tax in line.tax_ids:
                    if abs(tax.amount - 13.0) < 0.01:  # 13% tax
                        line_subtotal = line.price_subtotal
                        line_tax = line.price_total - line.price_subtotal

                        # Classify as goods or services
                        if line.product_id and line.product_id.type == 'product':
                            goods_13_base += line_subtotal
                            goods_13_tax += line_tax
                        else:
                            services_13_base += line_subtotal
                            services_13_tax += line_tax

        self.purchases_goods_13_base = goods_13_base
        self.purchases_goods_13_tax = goods_13_tax
        self.purchases_services_13_base = services_13_base
        self.purchases_services_13_tax = services_13_tax

    def action_generate_xml(self):
        """Generate D-150 XML for TRIBU-CR submission"""
        self.ensure_one()

        TaxReportXML = self.env['l10n_cr.tax.report.xml.generator']
        xml_content = TaxReportXML.generate_d150_xml(self)

        self.xml_content = xml_content
        return self.action_sign_xml()

    def action_sign_xml(self):
        """Sign D-150 XML with digital signature"""
        self.ensure_one()

        if not self.xml_content:
            raise UserError(_('Generate XML first before signing'))

        # Reuse existing xml_signer
        XMLSigner = self.env['l10n_cr.xml.signer']
        signed_xml = XMLSigner.sign_xml(self.xml_content, self.company_id)

        self.xml_signed = signed_xml
        return self.action_submit_to_hacienda()

    def action_submit_to_hacienda(self):
        """Submit D-150 to Hacienda TRIBU-CR"""
        self.ensure_one()

        if not self.xml_signed:
            raise UserError(_('Sign XML first before submission'))

        # Reuse existing hacienda_api
        HaciendaAPI = self.env['l10n_cr.hacienda.api']
        response = HaciendaAPI.submit_tax_report(self, 'D150')

        self.submission_date = fields.Datetime.now()
        self.hacienda_response = str(response)
        self.period_id.state = 'submitted'

        # Create response message record (reuse existing model)
        self.env['l10n_cr.hacienda.response.message'].create({
            'document_id': False,  # No invoice, this is a tax report
            'tax_report_id': self.id,
            'message_type': 'submission',
            'status_code': response.get('status_code'),
            'message': response.get('message'),
            'response_data': str(response),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('D-150 submitted to Hacienda successfully'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_export_excel(self):
        """Export to Excel matching ATV template"""
        self.ensure_one()
        # Reuse xlsxwriter pattern from hacienda_reports.py
        pass
```

#### Step 3: Extend XML Generator for Tax Reports
**File:** `models/tax_report_xml_generator.py`

```python
# -*- coding: utf-8 -*-
from odoo import models, api
from lxml import etree

class TaxReportXMLGenerator(models.AbstractModel):
    _name = 'l10n_cr.tax.report.xml.generator'
    _description = 'Tax Report XML Generator'

    @api.model
    def generate_d150_xml(self, d150_report):
        """
        Generate D-150 XML for TRIBU-CR submission.

        Based on official TRIBU-CR schema (post-September 2025).
        """
        company = d150_report.company_id
        period = d150_report.period_id

        # Create root element
        root = etree.Element('D150')

        # Period information
        periodo = etree.SubElement(root, 'Periodo')
        etree.SubElement(periodo, 'Anio').text = str(period.year)
        etree.SubElement(periodo, 'Mes').text = str(period.month)

        # Declarant information
        declarante = etree.SubElement(root, 'Declarante')
        etree.SubElement(declarante, 'Identificacion').text = company.vat or ''
        etree.SubElement(declarante, 'Nombre').text = company.name or ''

        # Sales section
        ventas = etree.SubElement(root, 'Ventas')
        ventas_gravadas = etree.SubElement(ventas, 'VentasGravadas')

        # 13% rate
        if d150_report.sales_13_base > 0:
            tarifa_13 = etree.SubElement(ventas_gravadas, 'Tarifa13')
            etree.SubElement(tarifa_13, 'Base').text = f"{d150_report.sales_13_base:.0f}"
            etree.SubElement(tarifa_13, 'Impuesto').text = f"{d150_report.sales_13_tax:.0f}"

        # 4% rate
        if d150_report.sales_4_base > 0:
            tarifa_4 = etree.SubElement(ventas_gravadas, 'Tarifa4')
            etree.SubElement(tarifa_4, 'Base').text = f"{d150_report.sales_4_base:.0f}"
            etree.SubElement(tarifa_4, 'Impuesto').text = f"{d150_report.sales_4_tax:.0f}"

        # Exempt sales
        if d150_report.sales_exempt_with_credit > 0 or d150_report.sales_exempt_no_credit > 0:
            ventas_exentas = etree.SubElement(ventas, 'VentasExentas')
            if d150_report.sales_exempt_with_credit > 0:
                etree.SubElement(ventas_exentas, 'ConCredito').text = f"{d150_report.sales_exempt_with_credit:.0f}"
            if d150_report.sales_exempt_no_credit > 0:
                etree.SubElement(ventas_exentas, 'SinCredito').text = f"{d150_report.sales_exempt_no_credit:.0f}"

        # Purchases section
        compras = etree.SubElement(root, 'Compras')
        compras_gravadas = etree.SubElement(compras, 'ComprasGravadas')

        # Goods
        if d150_report.purchases_goods_13_base > 0:
            bienes = etree.SubElement(compras_gravadas, 'Bienes')
            tarifa_13_goods = etree.SubElement(bienes, 'Tarifa13')
            etree.SubElement(tarifa_13_goods, 'Base').text = f"{d150_report.purchases_goods_13_base:.0f}"
            etree.SubElement(tarifa_13_goods, 'Impuesto').text = f"{d150_report.purchases_goods_13_tax:.0f}"

        # Services
        if d150_report.purchases_services_13_base > 0:
            servicios = etree.SubElement(compras_gravadas, 'Servicios')
            tarifa_13_services = etree.SubElement(servicios, 'Tarifa13')
            etree.SubElement(tarifa_13_services, 'Base').text = f"{d150_report.purchases_services_13_base:.0f}"
            etree.SubElement(tarifa_13_services, 'Impuesto').text = f"{d150_report.purchases_services_13_tax:.0f}"

        # Settlement section
        liquidacion = etree.SubElement(root, 'Liquidacion')
        etree.SubElement(liquidacion, 'IVADebito').text = f"{d150_report.total_sales_tax:.0f}"
        etree.SubElement(liquidacion, 'IVACredito').text = f"{d150_report.adjusted_credit:.0f}"

        if d150_report.withholdings > 0:
            etree.SubElement(liquidacion, 'Retenciones').text = f"{d150_report.withholdings:.0f}"

        if d150_report.previous_credit > 0:
            etree.SubElement(liquidacion, 'SaldoFavor').text = f"{d150_report.previous_credit:.0f}"

        # Net amount due or credit balance
        if d150_report.net_amount_due >= 0:
            etree.SubElement(liquidacion, 'MontoPagar').text = f"{d150_report.net_amount_due:.0f}"
        else:
            etree.SubElement(liquidacion, 'SaldoProximoPeriodo').text = f"{abs(d150_report.net_amount_due):.0f}"

        # Convert to string with XML declaration
        xml_string = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')

        return xml_string
```

#### Step 4: Extend Hacienda API for Tax Report Submission
**File:** `models/hacienda_api.py` (EXTEND existing file)

```python
# Add to existing l10n_cr.hacienda.api model

def submit_tax_report(self, tax_report, report_type):
    """
    Submit tax report to Hacienda TRIBU-CR.

    Args:
        tax_report: D150/D101/D151 report record
        report_type: 'D150', 'D101', 'D151'

    Returns:
        dict: Response from Hacienda
    """
    company = tax_report.company_id

    # Get auth token (reuse existing method)
    token = self._get_auth_token(company)

    # Determine endpoint based on report type
    if company.l10n_cr_use_sandbox:
        base_url = 'https://api.hacienda.go.cr/tribu-sandbox/v1'
    else:
        base_url = 'https://api.hacienda.go.cr/tribu/v1'

    endpoint_map = {
        'D150': f'{base_url}/declaraciones/d150',
        'D101': f'{base_url}/declaraciones/d101',
        'D151': f'{base_url}/declaraciones/d151',
    }

    endpoint = endpoint_map.get(report_type)
    if not endpoint:
        raise ValueError(f"Unknown report type: {report_type}")

    # Prepare request
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/xml',
    }

    # Submit signed XML
    response = requests.post(
        endpoint,
        headers=headers,
        data=tax_report.xml_signed.encode('utf-8'),
        timeout=30
    )

    # Parse response
    if response.status_code == 200 or response.status_code == 201:
        result = {
            'success': True,
            'status_code': response.status_code,
            'message': 'Tax report submitted successfully',
            'response_data': response.text,
        }
    else:
        result = {
            'success': False,
            'status_code': response.status_code,
            'message': f'Submission failed: {response.text}',
            'response_data': response.text,
        }

    return result
```

#### Step 5: Add Automated Monthly Generation
**File:** `data/tax_report_cron_jobs.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <!-- Auto-generate D-150 on 1st of each month -->
    <record id="cron_generate_d150_monthly" model="ir.cron">
        <field name="name">Generate D-150 Monthly VAT Reports</field>
        <field name="model_id" ref="model_l10n_cr_tax_report_period"/>
        <field name="state">code</field>
        <field name="code">model._cron_generate_d150_monthly()</field>
        <field name="interval_number">1</field>
        <field name="interval_type">days</field>
        <field name="numbercall">-1</field>
        <field name="doall">False</field>
        <field name="active">True</field>
    </record>
</odoo>
```

**Add method to** `models/tax_report_period.py`:

```python
@api.model
def _cron_generate_d150_monthly(self):
    """Scheduled action to generate D-150 on 1st of month"""
    today = fields.Date.today()

    if today.day == 1:
        # Generate for previous month
        last_month = today - relativedelta(months=1)

        for company in self.env['res.company'].search([('country_id.code', '=', 'CR')]):
            # Check if already exists
            existing = self.search([
                ('report_type', '=', 'd150'),
                ('year', '=', last_month.year),
                ('month', '=', last_month.month),
                ('company_id', '=', company.id),
            ])

            if existing:
                continue

            # Create period
            period = self.create({
                'report_type': 'd150',
                'year': last_month.year,
                'month': last_month.month,
                'date_from': last_month.replace(day=1),
                'date_to': last_month + relativedelta(day=31),
                'deadline': today.replace(day=15),
                'company_id': company.id,
            })

            # Create report
            d150 = self.env['l10n_cr.d150.report'].create({
                'period_id': period.id,
            })

            # Auto-calculate
            d150.action_calculate()

            # Send notification to accountant
            period.message_post(
                body=f"D-150 for {last_month.strftime('%B %Y')} has been auto-generated. Please review and submit by {period.deadline.strftime('%B %d')}.",
                subject="D-150 Monthly VAT Report Ready for Review",
            )
```

---

## Phase 9B: D-101 Annual Income Tax (Priority 2)

**Implementation:** Similar pattern to D-150, but:
- Triggered annually (January 1st for previous year)
- Different field structure (income, deductions, tax calculation)
- Supports 25% simplified deduction option

**Files to create:**
- `models/d101_income_report.py`
- `models/tax_report_xml_generator.py` (extend with `generate_d101_xml()`)
- `views/d101_income_report_views.xml`

---

## Phase 9C: D-151 Informative (Priority 3)

**Implementation:** Similar pattern but with line items:
- `l10n_cr.d151.report` (header)
- `l10n_cr.d151.line` (client/supplier/expense lines)
- Threshold filtering (₡2,500,000 for clients/suppliers, ₡50,000 for expenses)

---

## Additional D- Forms to Implement

### Priority 4: D-152 Informative Purchase Declarations
**When:** Annual (February 28 deadline)
**Who Needs It:** Companies making specific purchases subject to withholding

**Purpose:** Report purchases from suppliers where you applied withholding at source

**Key Fields:**
- Supplier identification
- Purchase type code
- Amount purchased
- Amount withheld
- Minimum threshold: ₡100,000

**Implementation:**
```python
class D152InformativeReport(models.Model):
    _name = 'l10n_cr.d152.report'
    _description = 'D-152 Informative Purchase Report'

    period_id = fields.Many2one('l10n_cr.tax.report.period')
    purchase_line_ids = fields.One2many('l10n_cr.d152.line', 'report_id')

class D152PurchaseLine(models.Model):
    _name = 'l10n_cr.d152.line'

    report_id = fields.Many2one('l10n_cr.d152.report')
    partner_id = fields.Many2one('res.partner')
    purchase_type = fields.Selection([
        ('01', 'Professional Services'),
        ('02', 'Commissions'),
        ('03', 'Rentals'),
        # ... more types
    ])
    amount = fields.Monetary()
    withheld_amount = fields.Monetary()
```

**When to Use:** If your gym pays professionals (trainers, therapists) as independent contractors

---

### Priority 5: D-158 Foreign Service Payments
**When:** Annual (February 28 deadline)
**Who Needs It:** Companies paying for foreign services (hosting, software, etc.)

**Purpose:** Report payments to foreign providers for services used in Costa Rica

**Key Fields:**
- Foreign provider identification
- Country of provider
- Service type
- Amount paid
- Withholding applied (if any)

**Gym Use Case:**
- International software subscriptions (ClassPass, MindBody)
- Online marketing services (Google Ads, Facebook Ads)
- Cloud hosting (AWS, DigitalOcean)
- Email services (Mailchimp, SendGrid)

**Implementation:**
```python
class D158ForeignPayments(models.Model):
    _name = 'l10n_cr.d158.report'
    _description = 'D-158 Foreign Service Payments'

    period_id = fields.Many2one('l10n_cr.tax.report.period')
    payment_line_ids = fields.One2many('l10n_cr.d158.line', 'report_id')

class D158PaymentLine(models.Model):
    _name = 'l10n_cr.d158.line'

    report_id = fields.Many2one('l10n_cr.d158.report')
    partner_id = fields.Many2one('res.partner')  # Foreign provider
    country_id = fields.Many2one('res.country')
    service_type = fields.Selection([
        ('01', 'Software/SaaS'),
        ('02', 'Marketing Services'),
        ('03', 'Cloud Hosting'),
        ('04', 'Professional Services'),
        ('99', 'Other Services'),
    ])
    amount_usd = fields.Monetary(currency_field='usd_currency_id')
    amount_crc = fields.Monetary()  # Converted to colones
    withholding = fields.Monetary()
```

**Auto-Detection:**
```python
def _auto_detect_foreign_payments(self, year):
    """Auto-detect foreign service payments from bills"""

    # Find supplier bills from foreign countries
    foreign_bills = self.env['account.move'].search([
        ('move_type', '=', 'in_invoice'),
        ('invoice_date', '>=', f'{year}-01-01'),
        ('invoice_date', '<=', f'{year}-12-31'),
        ('state', '=', 'posted'),
        ('partner_id.country_id.code', '!=', 'CR'),
        ('partner_id.country_id', '!=', False),
    ])

    # Create D-158 lines
    for bill in foreign_bills:
        # Categorize by service type
        service_type = self._classify_service_type(bill)

        self.env['l10n_cr.d158.line'].create({
            'report_id': self.id,
            'partner_id': bill.partner_id.id,
            'country_id': bill.partner_id.country_id.id,
            'service_type': service_type,
            'amount_usd': bill.amount_total_in_currency_signed,
            'amount_crc': bill.amount_total,
        })
```

---

### Priority 6: D-195 Inactive Company Declaration
**When:** Annual (if no business activity)
**Who Needs It:** Companies with zero sales/purchases in a year

**Purpose:** Declare that company had no taxable activity during the year

**Key Fields:**
- Company identification
- Tax period (year)
- Declaration of inactivity
- Reason for inactivity

**Gym Use Case:**
- Temporary closure (renovation, pandemic)
- Seasonal business pause
- Company dissolution process

**Implementation:**
```python
class D195InactiveReport(models.Model):
    _name = 'l10n_cr.d195.report'
    _description = 'D-195 Inactive Company Declaration'

    period_id = fields.Many2one('l10n_cr.tax.report.period')
    company_id = fields.Many2one('res.company')

    inactivity_reason = fields.Selection([
        ('temporary_closure', 'Temporary Closure'),
        ('renovation', 'Renovation/Remodeling'),
        ('seasonal', 'Seasonal Business'),
        ('dissolution', 'Company Dissolution in Progress'),
        ('other', 'Other'),
    ])
    reason_description = fields.Text()

    # Verification fields
    has_sales = fields.Boolean(compute='_compute_verification')
    has_purchases = fields.Boolean(compute='_compute_verification')
    has_payroll = fields.Boolean(compute='_compute_verification')

    @api.depends('period_id')
    def _compute_verification(self):
        """Verify company truly had no activity"""
        for record in self:
            year = record.period_id.year

            # Check for any sales
            sales = self.env['account.move'].search_count([
                ('move_type', '=', 'out_invoice'),
                ('invoice_date', '>=', f'{year}-01-01'),
                ('invoice_date', '<=', f'{year}-12-31'),
                ('state', '=', 'posted'),
                ('company_id', '=', record.company_id.id),
            ])
            record.has_sales = sales > 0

            # Check for any purchases
            purchases = self.env['account.move'].search_count([
                ('move_type', '=', 'in_invoice'),
                ('invoice_date', '>=', f'{year}-01-01'),
                ('invoice_date', '<=', f'{year}-12-31'),
                ('state', '=', 'posted'),
                ('company_id', '=', record.company_id.id),
            ])
            record.has_purchases = purchases > 0

            # Check for any payroll
            payroll = self.env['hr.payslip'].search_count([
                ('date_from', '>=', f'{year}-01-01'),
                ('date_to', '<=', f'{year}-12-31'),
                ('state', '=', 'done'),
                ('company_id', '=', record.company_id.id),
            ])
            record.has_payroll = payroll > 0

    def action_validate_inactivity(self):
        """Validate company truly had no activity"""
        self.ensure_one()

        if self.has_sales or self.has_purchases or self.has_payroll:
            raise UserError(_(
                'Cannot file D-195 - Company had activity during this period:\n'
                f'- Sales invoices: {self.has_sales}\n'
                f'- Purchase bills: {self.has_purchases}\n'
                f'- Payroll: {self.has_payroll}\n\n'
                'Please file regular tax declarations instead.'
            ))

        return True
```

---

### OPTIONAL: D-156 Digital Services VAT (Specialized)
**When:** Monthly (if applicable)
**Who Needs It:** Digital platforms intermediating services

**Purpose:** Report VAT on digital services (Uber, Airbnb, marketplace platforms)

**Gym Use Case:** ONLY if you run a digital marketplace (e.g., ClassPass-style aggregator)

**Skip Unless:** You're building a gym aggregator platform

---

### OPTIONAL: D-157 Used Goods VAT (Specialized)
**When:** Monthly (if applicable)
**Who Needs It:** Businesses selling used goods

**Purpose:** Special VAT regime for used goods resellers

**Gym Use Case:** ONLY if you buy/sell used gym equipment as main business

**Skip Unless:** You run a used fitness equipment store

---

## Updated Priority Matrix

| Form | Priority | Frequency | Your Gym Needs It? | Reason |
|------|----------|-----------|-------------------|---------|
| **D-150** (VAT) | **1 - CRITICAL** | Monthly | ✅ Yes | Mandatory for all VAT-registered businesses |
| **D-101** (Income Tax) | **2 - CRITICAL** | Annual | ✅ Yes | Mandatory for all corporations |
| **D-151** (Informative) | **3 - HIGH** | Annual | ✅ Yes | Required with conditions (simplified regime transactions) |
| **D-152** (Purchases) | **4 - MEDIUM** | Annual | ⚠️ Maybe | Only if you withhold on supplier payments |
| **D-158** (Foreign) | **5 - MEDIUM** | Annual | ✅ Likely | If you use foreign software/services |
| **D-195** (Inactive) | **6 - LOW** | Annual | ⚠️ Rare | Only during closure/no activity |
| **D-156** (Digital) | **7 - SKIP** | Monthly | ❌ No | Only for digital platforms |
| **D-157** (Used Goods) | **8 - SKIP** | Monthly | ❌ No | Only for used goods resellers |

---

## Recommended Implementation Order

### Phase 9: Core Tax Reports (Must Have)
1. **D-150** - Monthly VAT (Week 1-3)
2. **D-101** - Annual Income Tax (Week 4-5)
3. **D-151** - Annual Informative (Week 6)

### Phase 10: Specialized Reports (Nice to Have)
4. **D-158** - Foreign Payments (Week 7)
   - Auto-detect foreign suppliers
   - Categorize by service type
5. **D-152** - Purchase Withholdings (Week 8)
   - Only if needed
6. **D-195** - Inactive Declaration (Week 9)
   - Simple form, low priority

### Phase 11: Platform Reports (Skip for Now)
7. **D-156** - Digital Services VAT ❌ Skip
8. **D-157** - Used Goods VAT ❌ Skip

---

## Auto-Detection Smart Features

### Smart D-158 Detection
```python
def suggest_d158_filing(self, year):
    """
    Auto-suggest D-158 filing if foreign payments detected.

    Returns notification: "You may need to file D-158 - we detected ₡X,XXX,XXX
    in payments to foreign providers for cloud services and software."
    """
    foreign_total = self._calculate_foreign_payments(year)

    if foreign_total > 500000:  # Threshold: ₡500,000
        return {
            'show_notification': True,
            'message': f'D-158 Filing Recommended: ₡{foreign_total:,.0f} in foreign payments detected',
            'foreign_providers': self._get_foreign_provider_summary(year),
        }
```

### Smart D-195 Detection
```python
@api.model
def suggest_d195_filing(self, year):
    """
    Auto-suggest D-195 if no activity detected.

    Runs in January for previous year.
    """
    # Check if company had any activity
    had_activity = self._check_annual_activity(year)

    if not had_activity:
        return {
            'show_notification': True,
            'message': f'No business activity detected for {year}. Consider filing D-195 (Inactive Company Declaration) instead of regular tax reports.',
            'can_auto_generate': True,
        }
```

---

## Technology Stack (From Research)

### Reusing Your Existing Stack ✅
- **lxml**: XML generation (already using)
- **xmlschema**: XSD validation (already using)
- **cryptography + pyOpenSSL**: Digital signatures (already using)
- **requests**: HTTP API calls (already using)
- **PostgreSQL**: Database (already using)

### No New Dependencies Needed! 🎉

---

## Security & Compliance (From Research)

### Following Existing Patterns ✅
1. **XAdES Signatures**: Reuse `xml_signer.py`
2. **OAuth 2.0**: Reuse `hacienda_api.py`
3. **5-Year Retention**: Store XML in database (like einvoice_document)
4. **Audit Trail**: Reuse `hacienda_response_message` model
5. **Retry Logic**: Reuse `einvoice_retry_queue` model

---

## Deployment Plan

### Week 1: D-150 Foundation
- Create models (period, D-150)
- Implement calculation logic
- Test with sample data

### Week 2: D-150 Submission
- XML generation
- Digital signature integration
- Hacienda API submission
- Response handling

### Week 3: D-150 Testing
- Unit tests
- Integration tests with sandbox
- User acceptance testing
- Deploy to production

### Week 4: D-101 & D-151
- Implement D-101 model and calculations
- Implement D-151 with line items
- Testing and validation

---

## Success Metrics

### Technical Metrics
- **Calculation Accuracy**: 100% match with manual calculations
- **Submission Success**: 99%+ acceptance from Hacienda
- **Processing Time**: < 5 seconds to generate report
- **Test Coverage**: 80%+ for new modules

### Business Metrics
- **On-Time Filing**: 100% before deadline
- **Zero Penalties**: No late filing fees
- **Automation**: 90%+ reports auto-generated

---

## Next Steps

**Want me to:**

1. **Start implementing D-150 model?** Create the full `d150_vat_report.py` file
2. **Create views and menus?** Build the UI for tax reports
3. **Write tests first?** TDD approach with unit tests
4. **Something else?**

---

**Research Sources:**
- Existing: `COSTA-RICA-TAX-REPORTS-RESEARCH-2025.md`
- New: `_bmad-output/planning-artifacts/research/technical-costa-rica-tax-reports-research-2025-12-31.md`
- Codebase: `l10n_cr_einvoice/` (Phases 1-8)
