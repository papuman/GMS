# Costa Rica E-Invoice XML Import - User Guide

**Version:** 1.0
**Last Updated:** December 29, 2024
**Module:** `l10n_cr_einvoice`

---

## Table of Contents

1. [Overview](#overview)
2. [Exporting from Previous Providers](#exporting-from-previous-providers)
3. [Importing to GMS System](#importing-to-gms-system)
4. [Handling Errors](#handling-errors)
5. [FAQ](#faq)

---

## Overview

The XML Import feature allows you to migrate your historical invoices from other Costa Rican e-invoicing providers (GTI, FACTURATica, TicoPay, etc.) into the GMS system.

### Key Features

- **Self-Service:** Import thousands of invoices without contacting support
- **Fast Processing:** 50-60 invoices per minute
- **Auto-Detection:** Automatically detects duplicate invoices
- **Smart Matching:** Finds existing customers and products
- **Error Recovery:** Detailed error reports with retry options
- **Data Preservation:** Original XML stored for 5-year legal compliance

### Supported Document Types

- **FE** - Factura Electrónica (Invoice)
- **TE** - Tiquete Electrónico (Electronic Receipt)
- **NC** - Nota de Crédito Electrónica (Credit Note)
- **ND** - Nota de Débito Electrónica (Debit Note)

---

## Exporting from Previous Providers

### GTI Costa Rica

1. Log into your GTI web portal
2. Navigate to **Reportes → Exportar Facturas**
3. Select date range (max 1 year at a time recommended)
4. Choose export format: **XML v4.4**
5. Check **"Incluir archivos firmados"** (Include signed files)
6. Click **"Exportar"**
7. Download the ZIP file when ready (you'll receive email notification)

**Note:** GTI groups exports by 1,000 invoices. For large volumes, make multiple exports.

### FACTURATica

1. Access FACTURATica dashboard
2. Go to **Configuración → Exportar Datos**
3. Select **"Exportar XMLs Firmados"**
4. Choose date range (recommend 3-6 months per batch)
5. Click **"Generar Exportación"**
6. Download ZIP file from **"Mis Exportaciones"**

**Alternative:** Email soporte@facturatica.com requesting XML export. Response time: 24-48 hours.

### TicoPay

1. Log into TicoPay admin panel
2. Navigate to **Facturas → Exportar**
3. Filter by date range
4. Select format: **"XML Completo (ZIP)"**
5. Include: **Facturas + Notas de Crédito**
6. Click **"Descargar"**

**Note:** TicoPay includes both original and signed XMLs. Use the "firmados" (signed) folder for import.

### Alegra

1. Go to **Ventas → Facturas**
2. Click **"Más opciones → Exportar"**
3. Choose **"Formato XML Hacienda"**
4. Select date range
5. Download the generated file

**Note:** Alegra exports individual files. You'll need to create a ZIP archive yourself (see below).

### Other Providers (PROCOM, Alanube, etc.)

Most providers offer XML export through:
- **Web Portal:** Look for "Exportar", "Backup", or "Descarga Masiva"
- **API Access:** If you have technical knowledge, use provider API
- **Support Request:** Email provider support requesting XML export

---

## Creating ZIP Files (For Individual XMLs)

If your provider gives individual XML files instead of a ZIP:

**Windows:**
1. Select all XML files
2. Right-click → Send to → Compressed (zipped) folder
3. Name it (e.g., `invoices_2023.zip`)

**Mac:**
1. Select all XML files
2. Right-click → Compress X items
3. Rename the Archive.zip file

**Linux:**
```bash
zip -r invoices_2023.zip *.xml
```

---

## Importing to GMS System

### Step 1: Access Import Wizard

1. Open Odoo GMS
2. Navigate to **Hacienda → Import → Import Historical Invoices**
3. The import wizard opens

### Step 2: Upload ZIP File

1. Click **"Choose File"**
2. Select your ZIP file (max 100 MB)
3. Select your **Previous Provider** from dropdown
   - Options: GTI, FACTURATica, TicoPay, Alegra, etc.
   - Choose **"Other Provider"** if yours isn't listed

### Step 3: Configure Import Options

#### Skip Duplicates (Recommended: ON)
- Automatically skips invoices that already exist (by clave)
- **Use case:** Safe for re-importing partially completed batches

#### Auto-Create Customers (Recommended: ON)
- Creates customer records for unknown VAT numbers
- **Turn OFF if:** You want manual approval of new customers

#### Auto-Create Products (Recommended: ON)
- Creates product records for unknown Cabys codes
- **Turn OFF if:** You want manual product matching

#### Validate Digital Signatures (Recommended: OFF)
- Verifies XML signatures cryptographically
- **Turn ON if:** Maximum security required (30% slower)

### Step 4: Start Import

1. Click **"Start Import"** button
2. Wait while processing (do not close window)
3. Progress bar shows real-time status:
   - Total Files
   - Processed
   - Successful
   - Failed
   - Skipped

### Step 5: Review Results

After completion, you'll see a summary:

```
✓ Import Completed Successfully

Total Files: 1,250
Successfully Imported: 1,245
Skipped (Duplicates): 3
Failed: 2
```

**Action Buttons:**
- **View Invoices:** See all imported invoices
- **View Errors:** Review failed imports (if any)
- **View Batch Details:** Full import report
- **Close:** Exit wizard

---

## Handling Errors

### Understanding Error Types

| Error Type | Meaning | Action Required |
|------------|---------|-----------------|
| **XML Parse Error** | Invalid XML file | Contact original provider for re-export |
| **Validation Error** | Missing required fields | Check XML completeness |
| **Duplicate Invoice** | Clave already exists | Normal - invoice already imported |
| **Partner Not Found** | Customer VAT not in system | Enable "Auto-Create Customers" and retry |
| **Product Not Found** | Cabys code not in system | Enable "Auto-Create Products" and retry |
| **Tax Config Error** | Tax rate not configured | Configure tax in Settings |
| **Currency Error** | Currency not activated | Activate currency (USD, EUR, etc.) |

### Viewing Errors

1. After import, click **"View Errors"** button
2. You'll see a list of all failed imports
3. Each error shows:
   - File name
   - Error type and category
   - Severity (Critical, High, Medium, Low)
   - Suggested action
   - Can Retry? (Yes/No)

### Retrying Failed Imports

**Individual Retry:**
1. Open the error record (double-click)
2. Read the **"Suggested Action"** section
3. Fix the issue (enable options, configure tax, etc.)
4. Click **"Retry Import"** button
5. If successful, invoice is created and error marked resolved

**Bulk Retry:**
1. In error list, select multiple errors
2. Click **"Action → Retry Selected Errors"**
3. System retries all retryable errors
4. See notification with results (Success: X, Failed: Y)

### Downloading Error Report

1. Go to **Hacienda → Import → Import Batches**
2. Open the batch with errors
3. Click **"Export Error Report"** button
4. Downloads CSV file with all error details
5. Share with IT team or provider for troubleshooting

### Downloading Failed XML

For deep troubleshooting:
1. Open error record
2. Click **"Download XML"** button
3. Send to technical support or original provider

---

## FAQ

### Q1: How long does import take?

**A:** Processing speed is 50-60 invoices/minute:
- 100 invoices: ~2 minutes
- 500 invoices: ~10 minutes
- 1,000 invoices: ~20 minutes
- 5,000 invoices: ~1.5 hours

### Q2: Can I import while users are working?

**A:** Yes! Import runs in the background. Users can continue working normally.

### Q3: What happens to duplicate invoices?

**A:** With "Skip Duplicates" enabled:
- System checks clave (50-digit unique key)
- If exists, skips without error
- You'll see count in "Skipped" field

### Q4: Will this overwrite existing data?

**A:** No. Import only creates NEW records. Existing invoices, customers, and products are never modified.

### Q5: Where is the original XML stored?

**A:** Each imported invoice has:
- **Original XML** field (binary attachment)
- **Original Provider** field
- **Original Clave** field
- **Historical Import** flag

Access via invoice form → "Other Info" tab.

### Q6: Can I import from multiple providers?

**A:** Yes! Each import batch tracks its provider. You can import GTI invoices, then FACTURATica, etc.

### Q7: What if customer names don't match?

**A:** System matches by VAT number (Cédula), not name:
- VAT match → Uses existing customer
- No VAT match + Auto-Create ON → Creates new customer
- No VAT match + Auto-Create OFF → Import fails with error

### Q8: Can I delete imported invoices?

**A:** Yes, but:
1. Go to **Hacienda → Import → Import Batches**
2. Open batch
3. Click **"View Invoices"**
4. Select invoices → Action → Delete

**Warning:** This is permanent and affects accounting reports.

### Q9: Do imported invoices affect accounting?

**A:** Yes! Imported invoices:
- Create accounting entries
- Affect P&L and Balance Sheet
- Included in reports (filter by "Historical Import" if needed)

Best practice: Import to test company first.

### Q10: What about payment status?

**A:** XML doesn't include payment data. All imported invoices are:
- Status: **Draft** or **Posted** (configurable)
- Payment: **Unpaid**

Mark as paid manually if needed: Invoice → Register Payment.

---

## Best Practices

### 1. Import in Batches

**Don't:** Upload 10,000 invoices at once
**Do:** Split into batches of 1,000-2,000

**Why:** Easier error management, faster processing

### 2. Test First

**Don't:** Import directly to production
**Do:** Test with 10-20 sample invoices first

**Why:** Verify customer/product matching, check tax config

### 3. Enable Auto-Creation Initially

**Don't:** Manually create all customers/products first
**Do:** Enable auto-creation for first import

**Why:** Saves hours of manual data entry

### 4. Review Error Report

**Don't:** Ignore failed imports
**Do:** Download CSV error report and review

**Why:** Identify systematic issues (missing tax config, etc.)

### 5. Keep Original ZIPs

**Don't:** Delete provider exports after import
**Do:** Keep ZIP files for 5+ years

**Why:** Legal requirement, backup if re-import needed

---

## Support

### Getting Help

1. **Documentation:** This guide + Administrator Guide
2. **Error Messages:** Each error has "Suggested Action"
3. **Support Email:** soporte@gms.cr
4. **Phone:** +506 2222-3333 (Mon-Fri 8am-5pm)

### What to Include in Support Request

- Import batch name
- Number of files (total/failed)
- Error report CSV (if applicable)
- Sample failed XML (1-2 files)
- Screenshots of error messages

---

## Appendix: XML File Structure

Valid Costa Rica e-invoice XML should have:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50-digit unique key</Clave>
    <NumeroConsecutivo>XXX-XXXXX-XX-XXXXXXXXXX</NumeroConsecutivo>
    <FechaEmision>2024-01-15T10:30:00-06:00</FechaEmision>
    <Emisor>...</Emisor>
    <Receptor>...</Receptor> <!-- Optional for TE -->
    <DetalleServicio>...</DetalleServicio>
    <ResumenFactura>...</ResumenFactura>
</FacturaElectronica>
```

**Required elements:**
- Clave (50 digits)
- NumeroConsecutivo
- FechaEmision
- Emisor (company data)
- ResumenFactura (totals)

**Optional elements:**
- Receptor (customer data - required for FE, NC, ND)
- DetalleServicio (line items)
- InformacionReferencia (for NC/ND)

---

**End of User Guide**

For administrator troubleshooting, see: `XML_IMPORT_ADMIN_GUIDE.md`
