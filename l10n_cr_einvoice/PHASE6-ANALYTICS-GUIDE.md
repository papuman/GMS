# Phase 6: Analytics & Reporting - Complete User Guide

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Executive Dashboard](#executive-dashboard)
4. [Sales Reports](#sales-reports)
5. [Hacienda Compliance Reports](#hacienda-compliance-reports)
6. [Customer Analytics](#customer-analytics)
7. [Performance Metrics](#performance-metrics)
8. [Automated Reports](#automated-reports)
9. [Export & Integration](#export--integration)
10. [Best Practices](#best-practices)

---

## Overview

The Analytics & Reporting module provides comprehensive insights into your e-invoicing operations, helping you make data-driven decisions, ensure compliance, and optimize performance.

### Key Benefits

- **Real-time insights** into invoice operations
- **Automated compliance reporting** for Hacienda
- **Customer intelligence** for better service
- **Performance monitoring** for system health
- **Automated alerts** for critical issues

---

## Getting Started

### Accessing Analytics

**Navigation:** Hacienda > Reportes

You'll see four main sections:
1. Panel de Análisis (Analytics Dashboard)
2. Reportes de Ventas (Sales Reports)
3. Reportes de Cumplimiento (Compliance Reports)
4. Métricas de Rendimiento (Performance Metrics)

### Permissions Required

- **View Reports**: Accountant role
- **Export Data**: Manager role
- **Configure**: System Administrator

---

## Executive Dashboard

### Overview

The main dashboard provides at-a-glance visibility of your e-invoicing performance.

**Access:** Hacienda > Reportes > Panel de Análisis

### Key Sections

#### 1. Resumen Ejecutivo (Executive Summary)

**Métricas Clave (Key Metrics):**

- **Total Facturas**: Count of all invoices
- **Ingresos Totales**: Total revenue (₡)
- **Tasa de Aceptación**: Percentage accepted by Hacienda
- **Tiempo Promedio**: Average processing time

**What to Watch:**
- Acceptance rate should be >95%
- Processing time should be <5 minutes
- Revenue trends should match expectations

#### 2. Estado de Documentos (Document Status)

- **Aceptados**: Successfully processed
- **Rechazados**: Rejected by Hacienda (needs attention)
- **Pendientes**: Awaiting Hacienda response

**Action Items:**
- Review rejected invoices daily
- Follow up on pending >24 hours
- Investigate error patterns

#### 3. Por Tipo de Documento (By Document Type)

- **FE**: Standard invoices
- **TE**: POS receipts
- **NC**: Credit notes
- **ND**: Debit notes

Each shows count and total revenue.

#### 4. Tendencias (Trends Tab)

**Invoice Trend Chart:**
- Daily invoice volume over last 30 days
- Shows accepted vs rejected
- Identifies patterns and anomalies

**Revenue Trend Chart:**
- Daily revenue trends
- Breakdown by document type
- Seasonal patterns

**How to Use:**
- Compare to previous periods
- Identify growth trends
- Spot unusual patterns

#### 5. Clientes (Customers Tab)

**Top 10 Customers:**
- Ranked by revenue
- Shows invoice count
- Displays total spent

**Actions:**
- Identify VIP customers
- Plan retention strategies
- Target upsell opportunities

#### 6. Rendimiento (Performance Tab)

**Email y PDF:**
- Email delivery rate
- PDF generation success
- Engagement metrics

**Estado de Colas (Queue Status):**
- Retry queue items
- Offline queue items
- Completion rates

**Health Indicators:**
- Green: All good
- Yellow: Minor issues
- Red: Immediate action needed

### Date Range Filtering

Use preset buttons for quick filtering:
- **Últimos 7 días**: Last week
- **Últimos 30 días**: Last month (default)
- **Este mes**: Current month
- **Mes pasado**: Previous month

Or select custom date range.

### Refreshing Data

- Click "Refresh" button
- Data updates in real-time
- Dashboard caches for 5 minutes

---

## Sales Reports

### 1. Resumen de Facturación (Invoice Summary)

**Purpose:** Overview of invoice activity

**Access:** Reportes de Ventas > Resumen de Facturación

**Parameters:**
- Date range (required)
- Customer (optional)
- Document type (optional)

**Output:**
- Total documents
- Total revenue
- Breakdown by type
- Tax summary

**Use Cases:**
- Daily sales review
- Customer account review
- Period-end reconciliation

**Export:** Excel, PDF

### 2. Análisis de Ingresos (Revenue Analysis)

**Purpose:** Deep dive into revenue trends

**Access:** Reportes de Ventas > Análisis de Ingresos

**Parameters:**
- Date range
- Period: Daily, Weekly, or Monthly

**Output:**
- Revenue by period
- Document type breakdown
- Trend analysis
- Growth rates

**Use Cases:**
- Monthly business review
- Revenue forecasting
- Performance tracking

**Key Insights:**
- Identify peak periods
- Seasonal patterns
- Growth trends
- Revenue composition

### 3. Recaudación de Impuestos (Tax Collection)

**Purpose:** IVA collection summary

**Access:** Reportes de Ventas > Recaudación de Impuestos

**Parameters:**
- Date range

**Output:**
- Total IVA collected
- Taxable base
- Breakdown by tax rate
- Document count

**Use Cases:**
- Tax filing preparation
- Compliance verification
- Financial reporting

**Important:**
- Excludes credit notes
- Includes FE, TE, ND only
- Shows tax rate breakdown (13%, etc.)

### 4. Métodos de Pago (Payment Methods)

**Purpose:** Payment preference analysis

**Access:** Reportes de Ventas > Métodos de Pago

**Parameters:**
- Date range

**Output:**
- Distribution by method
- Revenue per method
- Transaction counts
- Percentage breakdown

**Use Cases:**
- Payment optimization
- Fee analysis
- Customer preferences

**Methods Tracked:**
- Efectivo (Cash)
- Tarjeta (Card)
- Transferencia (Transfer)
- SINPE Móvil
- Cheque

### 5. Historial de Cliente (Customer History)

**Purpose:** Complete customer transaction history

**Access:** Reportes de Ventas > Historial de Cliente

**Parameters:**
- Customer (required)
- Date range (optional)

**Output:**
- All invoices
- Total revenue
- Payment preferences
- Document breakdown

**Use Cases:**
- Customer service inquiries
- Account reconciliation
- Credit decisions
- Relationship review

---

## Hacienda Compliance Reports

### 1. Declaración Mensual (Monthly Filing)

**Purpose:** Complete monthly summary for tax filing

**Access:** Reportes de Cumplimiento > Declaración Mensual

**Parameters:**
- Year
- Month

**Output:**

**Document Summary:**
- FE count
- TE count
- NC count
- ND count

**Financial Summary:**
- Gross sales (FE + TE)
- Credit notes
- Debit notes
- Net sales

**Tax Summary:**
- Total IVA
- IVA in credits
- Net IVA to declare

**Tax by Rate:**
- 13% IVA breakdown
- Other rates
- Taxable base

**Top 20 Customers:**
- Customer identification
- Invoice count
- Total amount

**Use Cases:**
- Monthly Hacienda filing
- Tax calculation verification
- Compliance documentation

**Export to Excel:**
1. Click "Export to Excel"
2. Open in Excel/LibreOffice
3. Review all sheets
4. Use for tax filing

### 2. Facturas Rechazadas (Rejected Invoices)

**Purpose:** Analyze and resolve rejections

**Access:** Reportes de Cumplimiento > Facturas Rechazadas

**Parameters:**
- Date range

**Output:**

**Error Categories:**
- Certificate/signature issues
- XML format errors
- Emisor/receptor data
- Tax calculation errors
- Clave errors
- Other

**For Each Category:**
- Error count
- Example errors
- Document numbers

**Use Cases:**
- Error pattern identification
- Process improvement
- Staff training
- System troubleshooting

**Action Steps:**
1. Review error categories
2. Identify most common
3. Fix root cause
4. Train staff if needed
5. Update processes

### 3. Facturas Pendientes (Pending Invoices)

**Purpose:** Identify documents needing attention

**Access:** Reportes de Cumplimiento > Facturas Pendientes

**Output:**

**By State:**
- Draft count
- Generated count
- Signed count
- Submitted count

**Stuck Documents:**
- Documents >24 hours old
- Oldest document date
- Total stuck

**Retry Queue:**
- Pending retries
- Completed
- Failed

**Action Required:**
- Review stuck documents
- Process draft invoices
- Check retry queue failures

### 4. Línea de Tiempo (Status Timeline)

**Purpose:** Processing time analysis

**Access:** Reportes de Cumplimiento > Línea de Tiempo

**Parameters:**
- Date range

**Output:**

**Statistics:**
- Average processing time
- Fastest submission
- Slowest submission

**Time Distribution:**
- 0-5 minutes
- 5-15 minutes
- 15-30 minutes
- 30-60 minutes
- 60+ minutes

**Individual Documents:**
- Document number
- Submission time
- Acceptance time
- Processing duration

**Use Cases:**
- SLA monitoring
- Performance optimization
- Issue identification

### 5. Pista de Auditoría (Audit Trail)

**Purpose:** Complete transaction log

**Access:** Reportes de Cumplimiento > Pista de Auditoría

**Parameters:**
- Document ID (optional)
- Date range (optional)

**Output:**

**For Each Document:**
- All API responses
- Timestamps
- Status codes
- Messages
- Response data

**Use Cases:**
- Compliance audits
- Dispute resolution
- System debugging
- Historical analysis

---

## Customer Analytics

### 1. Top Customers by Revenue

**Purpose:** Identify high-value customers

**Parameters:**
- Date range (default: 90 days)
- Limit (default: 20)

**Metrics per Customer:**
- Total revenue
- Net revenue (after credits)
- Invoice count
- Average order value
- First purchase date
- Last purchase date
- Purchase frequency

**Use Cases:**
- VIP customer identification
- Retention focus
- Upsell targeting
- Relationship management

**Action Items:**
- Contact top 10 customers monthly
- Offer VIP benefits
- Request testimonials
- Plan retention strategy

### 2. Purchase Frequency Analysis

**Purpose:** Segment customers by activity

**Categories:**
- **High Frequency**: >10 invoices
- **Medium Frequency**: 5-10 invoices
- **Low Frequency**: 2-4 invoices
- **One-time**: 1 invoice

**Metrics:**
- Count in each category
- Percentage distribution
- Revenue by category

**Use Cases:**
- Customer segmentation
- Marketing campaigns
- Loyalty programs
- Churn prevention

**Strategies:**
- High: Maintain, reward loyalty
- Medium: Increase frequency
- Low: Re-engagement campaigns
- One-time: Win-back programs

### 3. Payment Preferences

**Purpose:** Understand payment behavior

**Per Customer:**
- Payment methods used
- Usage count per method
- Total amount per method
- Dominant method
- Dominant percentage

**Use Cases:**
- Payment option optimization
- Fee management
- Customer convenience
- Cash flow planning

### 4. CIIU Distribution

**Purpose:** Customer economic activity analysis

**Metrics:**
- Customer count per CIIU
- Invoice count per CIIU
- Total revenue per CIIU
- Average revenue per customer

**Use Cases:**
- Market segmentation
- Industry targeting
- Service customization
- Compliance reporting

### 5. Email Engagement

**Purpose:** Track communication effectiveness

**Metrics:**
- Total eligible invoices
- Emails sent
- Emails not sent
- Delivery rate
- Customers without email
- Per-customer engagement rate

**Use Cases:**
- Communication optimization
- Contact data cleanup
- Engagement improvement
- Email template effectiveness

**Action Items:**
- Collect missing emails
- Review bounced emails
- Test email templates
- Improve delivery rate

### 6. Customer Lifetime Value (CLV)

**Purpose:** Predict long-term customer value

**Metrics:**
- Customer since date
- Customer age (days)
- First purchase
- Last purchase
- Recency (days since last)
- Total invoices
- Total revenue
- Total credits
- Net revenue
- Average order value
- Lifetime value

**Use Cases:**
- Investment prioritization
- Marketing budget allocation
- Retention focus
- Growth forecasting

**Strategies:**
- High CLV: Maximize retention
- Medium CLV: Increase value
- Low CLV: Evaluate viability
- New customers: Track potential

---

## Performance Metrics

### 1. API Response Times

**Purpose:** Monitor Hacienda API performance

**Metrics:**
- Total requests
- Average response time
- Minimum response time
- Maximum response time
- 50th percentile (median)
- 95th percentile
- 99th percentile

**Time Distribution:**
- 0-10 seconds
- 10-30 seconds
- 30-60 seconds
- 60-300 seconds (1-5 minutes)
- 300+ seconds (>5 minutes)

**Alert Thresholds:**
- Average >60s: Warning
- Average >120s: Critical
- 95th percentile >180s: Review needed

### 2. Retry Queue Efficiency

**Purpose:** Evaluate retry effectiveness

**Metrics:**
- Total retry items
- Pending count
- Completed count
- Failed count
- Success rate
- Average retries
- Average processing time

**Per Operation Type:**
- Sign operations
- Submit operations
- Status check operations

**Success rate targets:**
- >90%: Healthy
- 70-90%: Review needed
- <70%: Critical issue

### 3. Email Delivery

**Purpose:** Track email effectiveness

**Metrics:**
- Total eligible documents
- Emails sent
- Emails not sent
- Delivery rate
- Average delivery time

**Per Document Type:**
- FE emails sent
- TE emails sent
- NC emails sent
- ND emails sent

**Targets:**
- Delivery rate >95%
- Avg delivery time <5 minutes

### 4. PDF Generation

**Purpose:** Monitor PDF performance

**Metrics:**
- Total documents
- PDFs generated
- PDFs not generated
- Generation rate

**Per Document Type:**
- FE PDFs
- TE PDFs
- NC PDFs
- ND PDFs

**Targets:**
- Generation rate >98%

### 5. POS Transaction Volume

**Purpose:** Monitor POS operations

**Metrics:**
- Total transactions
- Accepted transactions
- Rejected transactions
- Pending transactions
- Acceptance rate
- Total revenue
- Average transaction value

**Offline Queue:**
- Pending items
- Completed items
- Failed items

**Daily Volume Chart:**
- Transaction count per day
- Revenue per day

### 6. System Health

**Purpose:** Overall system status

**Metrics:**
- Health status (healthy/warning/critical)
- Error documents count
- Stuck documents (>24h)
- Retry queue backlog
- Offline queue backlog
- Recent acceptance rate (24h)

**Health Status Levels:**

**Healthy (Green):**
- Error docs <5
- Stuck docs <10
- Retry backlog <20
- Recent acceptance >95%

**Warning (Yellow):**
- Error docs 5-10
- Stuck docs 10-20
- Retry backlog 20-50
- Recent acceptance 90-95%

**Critical (Red):**
- Error docs >10
- Stuck docs >20
- Retry backlog >50
- Recent acceptance <90%

**Actions by Status:**

**Healthy:**
- Continue monitoring
- Routine maintenance

**Warning:**
- Review error logs
- Check stuck documents
- Monitor trends

**Critical:**
- Immediate action
- Review all errors
- Check API connectivity
- Contact support if needed

---

## Automated Reports

### Daily Summary Email

**When:** Every day at 8:00 AM

**Recipients:** System administrators

**Content:**
- Yesterday's metrics
- Total invoices
- Revenue
- Acceptance rate
- Document breakdown

**Purpose:** Daily operations review

### Weekly Revenue Report

**When:** Every Monday at 9:00 AM

**Recipients:** System administrators

**Content:**
- Last 7 days summary
- Daily breakdown table
- Total revenue
- Trend analysis

**Purpose:** Weekly business review

### Monthly Hacienda Report

**When:** 1st of month at 10:00 AM

**Recipients:** System administrators

**Content:**
- Complete previous month summary
- Document counts
- Financial summary
- Tax calculations

**Purpose:** Tax filing preparation

**Action Required:**
- Review report
- Verify accuracy
- Prepare for Hacienda submission

### Quarterly Performance Review

**When:** Every 3 months

**Recipients:** System administrators

**Content:**
- 90-day performance summary
- KPI trends
- System health
- API performance

**Purpose:** Strategic review

**Status:** Disabled by default (enable in Settings > Scheduled Actions)

### System Health Alerts

**When:** Every hour

**Recipients:** System administrators

**Triggers:**
- Health status: Warning or Critical
- Error threshold exceeded
- Stuck documents detected
- Queue backlog high

**Content:**
- Current health status
- Problem details
- Recommended actions

**Purpose:** Proactive issue detection

### Configuring Automated Reports

1. Go to **Settings > Technical > Automation > Scheduled Actions**
2. Find "E-Invoice" cron jobs
3. Modify:
   - **Interval**: Change frequency
   - **Next Execution**: Set next run time
   - **Active**: Enable/disable

---

## Export & Integration

### Excel Export

**Features:**
- Multiple sheets for complex reports
- Formatted tables
- Currency formatting
- Headers and titles
- Summary calculations

**How to Export:**
1. Open any report
2. Click "Export to Excel"
3. File downloads as `.xlsx`
4. Open in Excel, LibreOffice, etc.

**Requirements:**
- `xlsxwriter` Python library
- Install: `pip install xlsxwriter`

### CSV Export

**Features:**
- Plain text format
- Universal compatibility
- Easy import to databases
- Lightweight files

**Use Cases:**
- Data analysis in Python/R
- Import to external systems
- Database loading
- Custom processing

### PDF Export

**Features:**
- Professional layout
- Print-ready format
- Company branding
- Archival quality

**Use Cases:**
- Printing for records
- Email distribution
- Regulatory archival
- Client distribution

### JSON API Endpoints

For developers integrating with external systems:

```python
# Get KPIs via API
kpis = odoo.execute_kw(
    db, uid, password,
    'l10n_cr.einvoice.analytics.dashboard',
    'get_kpis',
    [],
    {'date_from': '2025-11-01', 'date_to': '2025-11-30'}
)

# Get monthly report
report = odoo.execute_kw(
    db, uid, password,
    'report.l10n_cr_einvoice.hacienda_reports',
    'get_monthly_filing_report',
    [2025, 11]
)
```

---

## Best Practices

### Daily Operations

**Morning Routine:**
1. Check system health
2. Review yesterday's summary email
3. Check for stuck documents
4. Review rejected invoices
5. Process any alerts

**Ongoing:**
- Monitor acceptance rate
- Respond to system alerts
- Review error patterns

### Weekly Review

**Every Monday:**
1. Review weekly revenue report
2. Compare to previous week
3. Identify trends
4. Check top customers
5. Review system performance

### Monthly Tasks

**First Week of Month:**
1. Generate monthly Hacienda report
2. Export to Excel
3. Verify all calculations
4. Review rejected invoices
5. Prepare tax filing
6. Archive previous month

**Mid-Month:**
- Review customer analytics
- Update customer segments
- Plan retention strategies

**End of Month:**
- Forecast next month
- Review KPI trends
- Plan improvements

### Quarterly Review

**Every 3 Months:**
1. Review quarterly performance report
2. Analyze long-term trends
3. Evaluate system health trends
4. Plan system improvements
5. Review customer CLV
6. Strategic planning

### Data Quality

**Regular Maintenance:**
- Archive old documents (>2 years)
- Clean up duplicate customers
- Update customer emails
- Verify customer identification
- Review CIIU codes

### Performance Optimization

**Keep System Fast:**
- Use specific date ranges
- Archive old data
- Run maintenance tasks during off-hours
- Monitor database size
- Optimize indexes

### Security

**Protect Sensitive Data:**
- Limit export permissions
- Audit export activity
- Secure Excel files with passwords
- Review access logs
- Follow data retention policies

### Compliance

**Ensure Hacienda Compliance:**
- Generate monthly reports on time
- Review all rejections
- Maintain audit trail
- Keep backup exports
- Document any discrepancies

---

## Troubleshooting

### Dashboard Issues

**Problem:** Dashboard loads slowly
**Solution:**
- Reduce date range to last 7 days
- Clear browser cache
- Check server resources
- Review database indexes

**Problem:** KPIs show wrong numbers
**Solution:**
- Verify document states are correct
- Check date range settings
- Refresh dashboard
- Review SQL query logs

### Report Issues

**Problem:** Export to Excel fails
**Solution:**
```bash
pip install xlsxwriter
```
- Verify disk space
- Check write permissions
- Review error logs

**Problem:** PDF generation fails
**Solution:**
- Check QR code library
- Verify font installation
- Review report template
- Check disk space

### Email Issues

**Problem:** Automated emails not sending
**Solution:**
1. Settings > Technical > Email > Outgoing Mail Servers
2. Click "Test Connection"
3. Review mail queue
4. Check SMTP credentials
5. Verify cron job is active

**Problem:** Wrong email recipients
**Solution:**
1. Verify user email addresses
2. Check user groups
3. Review cron job configuration

### Data Issues

**Problem:** Missing invoices in reports
**Solution:**
- Check document state
- Verify date range
- Review filters
- Check archived documents

**Problem:** Duplicate data in exports
**Solution:**
- Review database integrity
- Check for duplicate documents
- Run data cleanup

### Performance Issues

**Problem:** Reports time out
**Solution:**
- Reduce date range
- Optimize database
- Add indexes
- Increase timeout limits
- Run during off-hours

---

## Advanced Features

### Custom Metrics

For developers, add custom metrics:

```python
class CustomDashboard(models.Model):
    _inherit = 'l10n_cr.einvoice.analytics.dashboard'

    def get_custom_kpi(self):
        # Your custom calculation
        return custom_value
```

### Scheduled Report Customization

Modify email templates in:
**Settings > Technical > Email > Templates**

Search for "E-Invoice" templates

### Integration Examples

**Power BI:**
- Export to Excel
- Import into Power BI
- Create custom dashboards

**Google Sheets:**
- Export to CSV
- Import to Google Sheets
- Use Apps Script for automation

**Python/Pandas:**
```python
import pandas as pd

# Read CSV export
df = pd.read_csv('einvoice_report.csv')

# Analyze data
summary = df.groupby('document_type')['amount'].sum()
```

---

## Support Resources

### Documentation
- PHASE6-IMPLEMENTATION-COMPLETE.md - Technical details
- PHASE6-QUICK-REFERENCE.md - Quick lookup
- This guide - Complete user manual

### Logs
**Location:** Settings > Technical > Server Actions > Logging

**Useful for:**
- Debugging errors
- Performance issues
- API problems

### Community
- Odoo Community Forums
- GMS Development Team
- Internal support channels

---

**Phase 6 Analytics & Reporting - Complete User Guide**
**Version 19.0.1.7.0**
