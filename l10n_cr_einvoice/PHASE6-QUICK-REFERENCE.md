# Phase 6: Analytics & Reporting - Quick Reference

## Quick Access

### Main Dashboard
**Menu:** Hacienda > Reportes > Panel de Análisis

### Reports Menu
**Location:** Hacienda > Reportes

---

## Common Tasks

### 1. View Real-Time Dashboard

1. Go to **Hacienda > Reportes > Panel de Análisis**
2. Dashboard shows:
   - Total invoices
   - Revenue
   - Acceptance rate
   - Processing time
   - Document breakdown

### 2. Generate Monthly Hacienda Report

1. **Hacienda > Reportes > Reportes de Cumplimiento > Declaración Mensual**
2. Select month and year
3. Click "Generate Report"
4. Export to Excel or PDF

### 3. View Top Customers

1. **Hacienda > Reportes > Panel de Análisis**
2. Click "Clientes" tab
3. See top 10 customers by revenue

### 4. Check System Health

1. **Hacienda > Reportes > Métricas de Rendimiento > Salud del Sistema**
2. View status: Healthy / Warning / Critical
3. Review error counts and backlogs

### 5. Export Report to Excel

1. Open any report
2. Click "Export to Excel" button
3. File downloads automatically

---

## Dashboard KPIs Explained

| KPI | Description |
|-----|-------------|
| **Total Facturas** | All invoices in date range |
| **Ingresos Totales** | Total revenue (FE + TE + ND - NC) |
| **Tasa de Aceptación** | % of submitted invoices accepted |
| **Tiempo Promedio** | Average time from submission to acceptance |
| **Entrega Email** | % of accepted invoices emailed |
| **Cola de Reintentos** | Pending retry queue items |
| **Cola Offline** | Pending POS offline items |

---

## Report Types

### Sales Reports

1. **Resumen de Facturación**
   - Total documents by type
   - Revenue breakdown
   - Tax summary

2. **Análisis de Ingresos**
   - Daily/weekly/monthly trends
   - Revenue by document type
   - Period comparisons

3. **Recaudación de Impuestos**
   - Total IVA collected
   - Breakdown by tax rate
   - Taxable base

4. **Métodos de Pago**
   - Distribution by payment type
   - Revenue per method
   - Transaction counts

5. **Historial de Cliente**
   - All invoices for one customer
   - Total revenue
   - Payment preferences

### Hacienda Compliance Reports

1. **Declaración Mensual**
   - Complete monthly summary
   - Document counts
   - Tax calculations
   - Top customers
   - **Export to Excel for filing**

2. **Facturas Rechazadas**
   - All rejected invoices
   - Error categorization
   - Common error patterns

3. **Facturas Pendientes**
   - Documents needing attention
   - Stuck documents (>24h)
   - By status breakdown

4. **Línea de Tiempo**
   - Processing time analysis
   - Fastest/slowest submissions
   - Time distribution

5. **Pista de Auditoría**
   - Complete audit trail
   - All API responses
   - Transaction log

### Performance Metrics

1. **Tiempos de Respuesta API**
   - Average response time
   - Min/max/percentiles
   - Time distribution

2. **Eficiencia de Reintentos**
   - Success rate
   - Average retries
   - Operation breakdown

3. **Métricas de Email**
   - Delivery rate
   - Average delivery time
   - Failures

4. **Volumen POS**
   - Total transactions
   - Acceptance rate
   - Average value

5. **Salud del Sistema**
   - Overall health status
   - Error counts
   - Queue backlogs

---

## Automated Reports

### Daily Summary (8:00 AM)
Sent to administrators with:
- Yesterday's invoice count
- Total revenue
- Acceptance rate
- Document breakdown

### Weekly Revenue Report (Every Monday 9:00 AM)
- Last 7 days summary
- Daily breakdown
- Total revenue

### Monthly Hacienda Report (1st of month 10:00 AM)
- Previous month complete summary
- Ready for tax filing

### System Health Check (Every Hour)
- Monitors system status
- Sends alerts if critical/warning

---

## Date Range Shortcuts

| Button | Range |
|--------|-------|
| **Últimos 7 días** | Last 7 days |
| **Últimos 30 días** | Last 30 days |
| **Este mes** | Current month |
| **Mes pasado** | Previous month |

---

## Export Formats

### Excel (.xlsx)
- Full formatting
- Multiple sheets
- Currency formatting
- **Best for:** Hacienda filing, detailed analysis

### CSV
- Plain text
- Universal compatibility
- **Best for:** Data import, external tools

### PDF
- Print-ready
- Professional layout
- **Best for:** Archiving, sharing

---

## Health Status Colors

| Status | Color | Meaning |
|--------|-------|---------|
| **Healthy** | Green | All systems normal |
| **Warning** | Orange | Minor issues detected |
| **Critical** | Red | Immediate action required |

### Critical Triggers
- Error documents > 10
- Stuck documents > 20
- Retry queue > 50

### Warning Triggers
- Error documents > 5
- Stuck documents > 10
- Retry queue > 20

---

## Common Filters

### By Date Range
- Select start and end dates
- Use preset buttons for common ranges

### By Document Type
- FE: Facturas Electrónicas
- TE: Tiquetes Electrónicos
- NC: Notas de Crédito
- ND: Notas de Débito

### By Status
- Draft
- Pending (generated, signed, submitted)
- Accepted
- Rejected
- Error

### By Customer
- Select specific partner
- View all their invoices

---

## Tips & Best Practices

### Dashboard Performance
- Use specific date ranges for faster loading
- Archive old documents regularly
- Default to last 30 days

### Monthly Reports
- Generate on 1st of month for previous month
- Export to Excel before Hacienda filing
- Review rejected invoices first

### System Health
- Check daily
- Act on warnings immediately
- Review error patterns weekly

### Customer Analytics
- Review top customers monthly
- Identify high-value segments
- Track CLV trends

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Alt+D** | Open dashboard |
| **Alt+R** | Refresh data |
| **Ctrl+E** | Export to Excel |
| **Ctrl+P** | Print report |

---

## Troubleshooting Quick Fixes

### Dashboard not loading
1. Reduce date range
2. Clear browser cache
3. Check Odoo logs

### Export fails
```bash
pip install xlsxwriter
```

### Emails not sending
1. Settings > Technical > Email > Outgoing Mail Servers
2. Test connection
3. Check mail queue

### Wrong KPI values
1. Verify document states
2. Check date range
3. Refresh dashboard

---

## API Access (Developers)

### Get KPIs Programmatically

```python
dashboard = env['l10n_cr.einvoice.analytics.dashboard']
kpis = dashboard.get_kpis(
    date_from='2025-11-01',
    date_to='2025-11-30'
)
```

### Generate Report

```python
report = env['report.l10n_cr_einvoice.hacienda_reports']
data = report.get_monthly_filing_report(2025, 11)
```

### Export to Excel

```python
excel = report.export_monthly_filing_to_excel(2025, 11)
# Returns bytes of Excel file
```

---

## Security & Permissions

| Group | Access |
|-------|--------|
| **Accountant** | View all reports |
| **Manager** | View + Export + Configure |
| **Read-only** | View dashboards only |

---

## Support

**Documentation:** Check PHASE6-ANALYTICS-GUIDE.md for detailed instructions

**Logs:** Settings > Technical > Logging

**Issues:** Contact GMS Development Team

---

## Quick Command Reference

### Python Shell Commands

```python
# Get today's KPIs
env['l10n_cr.einvoice.analytics.dashboard'].get_kpis()

# Get top 20 customers
env['l10n_cr.einvoice.analytics.dashboard'].get_top_customers(limit=20)

# Monthly report
env['report.l10n_cr_einvoice.hacienda_reports'].get_monthly_filing_report(2025, 11)

# System health
env['report.l10n_cr_einvoice.performance_metrics'].get_system_health_metrics()
```

---

**Phase 6 Quick Reference - Version 19.0.1.7.0**
