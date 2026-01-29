# 🚀 Costa Rica E-Invoice XML Import - Complete Implementation Plan

**Project:** Full XML Import Feature for Odoo 19 E-Invoicing Module
**Timeline:** 10-12 Days (2 development sprints)
**Priority:** HIGH - Competitive Differentiator
**Status:** 📋 Ready for Implementation

---

## Executive Summary

**Goal:** Build the first self-service XML import feature in the Costa Rica e-invoicing market, enabling customers to migrate their complete invoice history in 30 minutes or less.

**Deliverable:** Upload wizard that accepts ZIP files containing Costa Rica v4.4 XML invoices, parses them, validates data, creates invoice records in Odoo, and stores original XMLs for 5-year legal compliance.

**Competitive Advantage:** Only provider with automated, self-service historical import (FACTURATica requires manual support intervention, others don't offer it at all).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema Changes](#database-schema-changes)
3. [File Structure](#file-structure)
4. [Implementation Phases](#implementation-phases)
5. [Day-by-Day Development Plan](#day-by-day-development-plan)
6. [Code Implementation Details](#code-implementation-details)
7. [UI/UX Specifications](#uiux-specifications)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Plan](#deployment-plan)
10. [Success Metrics](#success-metrics)

---

## Architecture Overview

### High-Level Flow

```
┌─────────────────┐
│ User uploads    │
│ invoices.zip    │
│ (1,200 XMLs)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 1. Extract ZIP                  │
│    - Validate file size         │
│    - Count XML files            │
│    - Create temp directory      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 2. Parse Each XML               │
│    - Validate against v4.4 XSD  │
│    - Extract clave (50 digits)  │
│    - Extract consecutive        │
│    - Extract customer data      │
│    - Extract line items         │
│    - Extract taxes, totals      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 3. Validate Business Rules      │
│    - Check for duplicates       │
│    - Verify consecutive order   │
│    - Match/create customers     │
│    - Validate amounts           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 4. Create Odoo Records          │
│    - Create account.move        │
│    - Create invoice lines       │
│    - Attach original XML        │
│    - Mark as "historical"       │
│    - Set state to 'posted'      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 5. Generate Report              │
│    - Success count              │
│    - Error count with details   │
│    - Import summary             │
│    - Allow error retry          │
└─────────────────────────────────┘
```

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Processing Speed | 50-60 XMLs/minute | 1,200 invoices in 20-25 minutes |
| Memory Usage | < 500 MB | Batch processing to limit memory |
| File Size Limit | 100 MB ZIP | ~2,000 average-sized XMLs |
| Concurrent Imports | 1 per user | Prevent resource conflicts |
| Error Rate | < 1% | 99%+ success on valid data |

---

## Database Schema Changes

### 1. Add Fields to `account.move`

```python
# l10n_cr_einvoice/models/account_move.py

class AccountMove(models.Model):
    _inherit = 'account.move'

    # Existing fields...

    # NEW: Historical import tracking
    l10n_cr_is_historical = fields.Boolean(
        string='Historical Invoice',
        default=False,
        readonly=True,
        help='Invoice imported from previous system (not submitted to Hacienda from this system)'
    )

    l10n_cr_import_batch_id = fields.Many2one(
        'l10n_cr.einvoice.import.batch',
        string='Import Batch',
        readonly=True,
        help='Links to the batch import that created this invoice'
    )

    l10n_cr_original_xml = fields.Binary(
        string='Original XML',
        attachment=True,
        help='Original XML file from previous provider (5-year legal retention)'
    )

    l10n_cr_original_xml_filename = fields.Char(
        string='XML Filename'
    )

    l10n_cr_original_provider = fields.Char(
        string='Original Provider',
        help='Previous e-invoicing provider (GTI, FACTURATica, etc.)'
    )

    l10n_cr_original_issue_date = fields.Datetime(
        string='Original Issue Date',
        help='Timestamp from original XML (may differ from invoice_date due to timezone)'
    )
```

### 2. Create Import Batch Model

```python
# l10n_cr_einvoice/models/einvoice_import_batch.py

class EInvoiceImportBatch(models.Model):
    _name = 'l10n_cr.einvoice.import.batch'
    _description = 'E-Invoice Import Batch'
    _order = 'create_date desc'

    name = fields.Char(
        string='Batch Name',
        required=True,
        default=lambda self: f"Import {fields.Datetime.now()}"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validating', 'Validating Files'),
        ('processing', 'Processing'),
        ('done', 'Completed'),
        ('error', 'Error Occurred'),
    ], default='draft', required=True)

    upload_file = fields.Binary(
        string='ZIP File',
        attachment=True
    )

    upload_filename = fields.Char(
        string='Filename'
    )

    # Statistics
    total_files = fields.Integer(
        string='Total XML Files',
        readonly=True
    )

    processed_count = fields.Integer(
        string='Processed',
        readonly=True
    )

    success_count = fields.Integer(
        string='Successful',
        readonly=True
    )

    error_count = fields.Integer(
        string='Errors',
        readonly=True
    )

    # Results
    invoice_ids = fields.One2many(
        'account.move',
        'l10n_cr_import_batch_id',
        string='Imported Invoices'
    )

    error_log = fields.Text(
        string='Error Log',
        readonly=True
    )

    processing_time = fields.Float(
        string='Processing Time (seconds)',
        readonly=True
    )

    # Settings
    skip_duplicates = fields.Boolean(
        string='Skip Duplicate Consecutives',
        default=True,
        help='If an invoice with the same consecutive exists, skip it instead of failing'
    )

    auto_create_partners = fields.Boolean(
        string='Auto-Create Missing Customers',
        default=True,
        help='Create customer records if not found by tax ID'
    )

    validate_signatures = fields.Boolean(
        string='Validate Digital Signatures',
        default=False,
        help='Verify XML digital signatures (slower but more secure)'
    )
```

### 3. Create Import Error Log Model

```python
# l10n_cr_einvoice/models/einvoice_import_error.py

class EInvoiceImportError(models.Model):
    _name = 'l10n_cr.einvoice.import.error'
    _description = 'E-Invoice Import Error Log'
    _order = 'create_date desc'

    batch_id = fields.Many2one(
        'l10n_cr.einvoice.import.batch',
        string='Import Batch',
        required=True,
        ondelete='cascade'
    )

    filename = fields.Char(
        string='XML Filename',
        required=True
    )

    error_type = fields.Selection([
        ('parse', 'XML Parse Error'),
        ('validation', 'Validation Error'),
        ('duplicate', 'Duplicate Consecutive'),
        ('customer', 'Customer Not Found'),
        ('amount', 'Amount Mismatch'),
        ('other', 'Other Error'),
    ], required=True)

    error_message = fields.Text(
        string='Error Details',
        required=True
    )

    xml_content = fields.Binary(
        string='Failed XML',
        attachment=True
    )

    can_retry = fields.Boolean(
        string='Can Retry',
        default=True,
        help='Whether this error can be fixed and retried'
    )
```

---

## File Structure

```
l10n_cr_einvoice/
├── models/
│   ├── __init__.py                      # Add new model imports
│   ├── account_move.py                  # MODIFY: Add historical fields
│   ├── einvoice_import_batch.py         # NEW
│   ├── einvoice_import_error.py         # NEW
│   └── einvoice_xml_parser.py           # NEW: XML parsing logic
│
├── wizards/
│   ├── __init__.py                      # Add wizard imports
│   └── einvoice_import_wizard.py        # NEW: Main import wizard
│
├── views/
│   ├── einvoice_import_views.xml        # NEW: Import UI
│   ├── einvoice_import_batch_views.xml  # NEW: Batch management
│   └── account_move_views.xml           # MODIFY: Add historical badge
│
├── static/
│   └── src/
│       └── js/
│           └── import_progress.js       # NEW: Real-time progress updates
│
├── data/
│   └── cr_v4.4_schema.xsd              # NEW: Costa Rica XML schema
│
├── tests/
│   ├── test_xml_import.py              # NEW: Import tests
│   └── sample_xmls/                     # NEW: Test XML files
│       ├── valid_fe.xml
│       ├── valid_te.xml
│       ├── invalid_clave.xml
│       └── duplicate_consecutive.xml
│
└── __manifest__.py                      # MODIFY: Add data files
```

---

## Implementation Phases

### Phase 1: Core XML Parser (Days 1-3)

**Objective:** Build robust XML parsing engine for Costa Rica v4.4 format

**Deliverables:**
1. XML parser class with v4.4 schema validation
2. Data extraction methods for all invoice elements
3. Unit tests for parsing various invoice types

### Phase 2: Import Wizard & UI (Days 4-6)

**Objective:** Create user-friendly upload and processing interface

**Deliverables:**
1. Upload wizard with drag & drop
2. Validation and progress display
3. Results report with error details

### Phase 3: Database Integration (Days 7-9)

**Objective:** Create Odoo invoice records from parsed data

**Deliverables:**
1. Invoice creation logic
2. Customer matching/creation
3. Line item processing
4. Tax calculations

### Phase 4: Testing & Polish (Days 10-12)

**Objective:** Comprehensive testing and user experience refinement

**Deliverables:**
1. End-to-end testing with real XML files
2. Performance optimization
3. Error handling improvements
4. Documentation

---

## Day-by-Day Development Plan

### **DAY 1: XML Parser Foundation**

**Tasks:**
- [ ] Create `einvoice_xml_parser.py` model
- [ ] Implement basic XML structure validation
- [ ] Extract clave (50-digit key) from XML
- [ ] Extract consecutive number
- [ ] Extract document type (FE, TE, NC, ND)
- [ ] Unit tests for basic parsing

**Deliverable:** Parser can extract key fields from valid XML

**Estimated Hours:** 8 hours

---

### **DAY 2: Customer & Header Data Extraction**

**Tasks:**
- [ ] Extract emisor (sender) data
- [ ] Extract receptor (receiver) data
  - Tax ID (cedula)
  - Name
  - Email
  - Address
- [ ] Extract invoice metadata
  - Date and time
  - Currency
  - Exchange rate (if applicable)
  - Payment method
  - Payment terms
- [ ] Unit tests for header extraction

**Deliverable:** Parser extracts complete header and customer data

**Estimated Hours:** 8 hours

---

### **DAY 3: Line Items & Tax Extraction**

**Tasks:**
- [ ] Extract line items (DetalleServicio)
  - Product/service description
  - Quantity
  - Unit price
  - Discount (if any)
  - Subtotal
  - Tax rate
  - Tax amount
  - Line total
- [ ] Extract summary totals (ResumenFactura)
  - Subtotal by tax rate
  - Total discounts
  - Total taxes
  - Grand total
- [ ] Validate calculations (line items sum to totals)
- [ ] Unit tests for line item extraction

**Deliverable:** Parser extracts complete invoice data with validation

**Estimated Hours:** 8 hours

---

### **DAY 4: Import Wizard UI (Backend)**

**Tasks:**
- [ ] Create `l10n_cr.einvoice.import.batch` model
- [ ] Create `l10n_cr.einvoice.import.error` model
- [ ] Create `einvoice_import_wizard.py` transient model
- [ ] Implement ZIP file extraction
- [ ] Implement file validation (size, format)
- [ ] Create batch processing queue

**Deliverable:** Backend models ready for import processing

**Estimated Hours:** 8 hours

---

### **DAY 5: Import Wizard UI (Frontend)**

**Tasks:**
- [ ] Create upload wizard view (einvoice_import_views.xml)
- [ ] Add drag & drop file upload
- [ ] Create progress bar display
- [ ] Create settings panel (skip duplicates, auto-create customers, etc.)
- [ ] Add "Start Import" button
- [ ] Link to Settings menu

**Deliverable:** User-friendly upload interface

**Estimated Hours:** 8 hours

---

### **DAY 6: Progress Tracking & Real-Time Updates**

**Tasks:**
- [ ] Implement background job processing
- [ ] Create progress tracking in database
- [ ] Implement JavaScript polling for progress updates
- [ ] Display current file being processed
- [ ] Show success/error counters in real-time
- [ ] Add "Cancel" button for long imports

**Deliverable:** Real-time import progress display

**Estimated Hours:** 8 hours

---

### **DAY 7: Invoice Creation Logic**

**Tasks:**
- [ ] Create account.move records from parsed data
- [ ] Set move_type (out_invoice, out_refund, out_receipt)
- [ ] Set invoice_date from XML
- [ ] Set l10n_cr_is_historical = True
- [ ] Store original XML as attachment
- [ ] Set clave and consecutive fields
- [ ] Handle currency and exchange rates

**Deliverable:** Basic invoice records created from XML

**Estimated Hours:** 8 hours

---

### **DAY 8: Customer Matching & Line Items**

**Tasks:**
- [ ] Implement customer matching by tax ID
- [ ] Implement auto-creation of missing customers
- [ ] Create invoice line items (account.move.line)
- [ ] Map products/services to Odoo accounts
- [ ] Handle taxes (map CR tax codes to Odoo taxes)
- [ ] Calculate and verify totals

**Deliverable:** Complete invoice records with lines and taxes

**Estimated Hours:** 8 hours

---

### **DAY 9: Error Handling & Validation**

**Tasks:**
- [ ] Implement duplicate detection (by consecutive number)
- [ ] Handle malformed XML gracefully
- [ ] Validate business rules
  - Amount calculations
  - Tax rate consistency
  - Customer data completeness
- [ ] Create error log entries
- [ ] Allow partial import (skip errors, continue processing)
- [ ] Implement retry mechanism for fixable errors

**Deliverable:** Robust error handling and recovery

**Estimated Hours:** 8 hours

---

### **DAY 10: Results Report & Error Display**

**Tasks:**
- [ ] Create import results view
- [ ] Display summary statistics
  - Total files processed
  - Successful imports
  - Errors encountered
  - Processing time
- [ ] Create error list view with details
- [ ] Add "Download Error Log" button
- [ ] Add "Retry Failed Imports" button
- [ ] Link to imported invoice list

**Deliverable:** Comprehensive results reporting

**Estimated Hours:** 8 hours

---

### **DAY 11: Testing & Performance Optimization**

**Tasks:**
- [ ] End-to-end testing with 1,200 XML files
- [ ] Performance profiling
- [ ] Optimize XML parsing (use lxml efficiently)
- [ ] Implement batch commit (every 50 invoices)
- [ ] Add database indexing for performance
- [ ] Memory usage optimization
- [ ] Test with large files (100+ MB ZIP)
- [ ] Load testing (concurrent imports)

**Deliverable:** Optimized, production-ready import

**Estimated Hours:** 8 hours

---

### **DAY 12: Documentation & Polish**

**Tasks:**
- [ ] Write user documentation
  - How to export XMLs from other providers
  - Step-by-step import guide
  - Troubleshooting common errors
- [ ] Create demo video (3-5 minutes)
- [ ] Add help tooltips to UI
- [ ] Create sample XML files for testing
- [ ] Write technical documentation for developers
- [ ] Update module README
- [ ] Create marketing one-pager

**Deliverable:** Complete documentation and training materials

**Estimated Hours:** 8 hours

---

## Code Implementation Details

### 1. XML Parser Core

```python
# l10n_cr_einvoice/models/einvoice_xml_parser.py

import base64
import zipfile
from lxml import etree
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EInvoiceXMLParser(models.AbstractModel):
    _name = 'l10n_cr.einvoice.xml.parser'
    _description = 'Costa Rica E-Invoice XML Parser'

    # XML Namespace for Costa Rica v4.4
    NS = {
        'ds': 'http://www.w3.org/2000/09/xmldsig#',
        'xades': 'http://uri.etsi.org/01903/v1.3.2#',
    }

    def parse_xml_file(self, xml_content):
        """
        Parse a single Costa Rica e-invoice XML file.

        Args:
            xml_content (bytes): Raw XML file content

        Returns:
            dict: Parsed invoice data

        Raises:
            ValidationError: If XML is invalid or doesn't match v4.4 schema
        """
        try:
            # Parse XML
            root = etree.fromstring(xml_content)

            # Extract all sections
            data = {
                'clave': self._extract_clave(root),
                'consecutive': self._extract_consecutive(root),
                'document_type': self._extract_document_type(root),
                'date': self._extract_date(root),
                'emisor': self._extract_emisor(root),
                'receptor': self._extract_receptor(root),
                'line_items': self._extract_line_items(root),
                'summary': self._extract_summary(root),
                'payment_info': self._extract_payment_info(root),
                'signature': self._extract_signature(root),
                'original_xml': base64.b64encode(xml_content).decode('utf-8'),
            }

            # Validate extracted data
            self._validate_invoice_data(data)

            return data

        except etree.XMLSyntaxError as e:
            raise ValidationError(_('Invalid XML format: %s') % str(e))
        except Exception as e:
            raise ValidationError(_('Error parsing XML: %s') % str(e))

    def _extract_clave(self, root):
        """Extract 50-digit Hacienda clave (unique invoice identifier)."""
        clave = root.find('.//Clave')
        if clave is None:
            raise ValidationError(_('Clave not found in XML'))

        clave_text = clave.text.strip()
        if len(clave_text) != 50:
            raise ValidationError(_('Invalid clave length: expected 50 digits, got %d') % len(clave_text))

        return clave_text

    def _extract_consecutive(self, root):
        """Extract consecutive number from NumeroConsecutivo field."""
        consecutivo = root.find('.//NumeroConsecutivo')
        if consecutivo is None:
            raise ValidationError(_('NumeroConsecutivo not found in XML'))

        return consecutivo.text.strip()

    def _extract_document_type(self, root):
        """Determine document type (FE, TE, NC, ND) from consecutive."""
        consecutivo = self._extract_consecutive(root)
        # Format: 001-00001-01-00000000001
        # Position 9-10 is document type: 01=FE, 02=ND, 03=NC, 04=TE
        parts = consecutivo.split('-')
        if len(parts) >= 3:
            doc_type_code = parts[2]
            doc_type_map = {
                '01': 'FE',  # Factura Electrónica
                '02': 'ND',  # Nota de Débito
                '03': 'NC',  # Nota de Crédito
                '04': 'TE',  # Tiquete Electrónico
            }
            return doc_type_map.get(doc_type_code, 'FE')
        return 'FE'

    def _extract_date(self, root):
        """Extract invoice date and time."""
        fecha = root.find('.//FechaEmision')
        if fecha is None:
            raise ValidationError(_('FechaEmision not found in XML'))

        # Format: 2024-12-28T10:30:00-06:00
        date_str = fecha.text.strip()

        # Parse ISO 8601 format
        from dateutil import parser
        try:
            dt = parser.isoparse(date_str)
            return dt
        except Exception as e:
            raise ValidationError(_('Invalid date format: %s') % str(e))

    def _extract_emisor(self, root):
        """Extract sender (business) information."""
        emisor = root.find('.//Emisor')
        if emisor is None:
            raise ValidationError(_('Emisor section not found in XML'))

        return {
            'identificacion': emisor.find('.//Numero').text if emisor.find('.//Numero') is not None else '',
            'nombre': emisor.find('.//Nombre').text if emisor.find('.//Nombre') is not None else '',
            'nombre_comercial': emisor.find('.//NombreComercial').text if emisor.find('.//NombreComercial') is not None else '',
            'correo_electronico': emisor.find('.//CorreoElectronico').text if emisor.find('.//CorreoElectronico') is not None else '',
            'telefono': emisor.find('.//Telefono/NumTelefono').text if emisor.find('.//Telefono/NumTelefono') is not None else '',
        }

    def _extract_receptor(self, root):
        """Extract receiver (customer) information."""
        receptor = root.find('.//Receptor')
        if receptor is None:
            # Tiquete Electrónico (TE) may not have receptor
            return None

        return {
            'identificacion': receptor.find('.//Numero').text if receptor.find('.//Numero') is not None else '',
            'nombre': receptor.find('.//Nombre').text if receptor.find('.//Nombre') is not None else '',
            'correo_electronico': receptor.find('.//CorreoElectronico').text if receptor.find('.//CorreoElectronico') is not None else '',
            'telefono': receptor.find('.//Telefono/NumTelefono').text if receptor.find('.//Telefono/NumTelefono') is not None else '',
        }

    def _extract_line_items(self, root):
        """Extract all invoice line items."""
        lines = []
        lineas = root.findall('.//LineaDetalle')

        for i, linea in enumerate(lineas):
            line_data = {
                'sequence': i + 1,
                'cantidad': float(linea.find('.//Cantidad').text) if linea.find('.//Cantidad') is not None else 1.0,
                'unidad_medida': linea.find('.//UnidadMedida').text if linea.find('.//UnidadMedida') is not None else 'Unid',
                'detalle': linea.find('.//Detalle').text if linea.find('.//Detalle') is not None else '',
                'precio_unitario': float(linea.find('.//PrecioUnitario').text) if linea.find('.//PrecioUnitario') is not None else 0.0,
                'monto_total': float(linea.find('.//MontoTotal').text) if linea.find('.//MontoTotal') is not None else 0.0,
                'subtotal': float(linea.find('.//SubTotal').text) if linea.find('.//SubTotal') is not None else 0.0,
                'monto_descuento': float(linea.find('.//MontoDescuento').text) if linea.find('.//MontoDescuento') is not None else 0.0,
                'impuesto': float(linea.find('.//Impuesto/Monto').text) if linea.find('.//Impuesto/Monto') is not None else 0.0,
                'tarifa_impuesto': float(linea.find('.//Impuesto/Tarifa').text) if linea.find('.//Impuesto/Tarifa') is not None else 0.0,
                'monto_total_linea': float(linea.find('.//MontoTotalLinea').text) if linea.find('.//MontoTotalLinea') is not None else 0.0,
            }
            lines.append(line_data)

        return lines

    def _extract_summary(self, root):
        """Extract invoice summary totals."""
        resumen = root.find('.//ResumenFactura')
        if resumen is None:
            raise ValidationError(_('ResumenFactura section not found in XML'))

        return {
            'total_venta_neta': float(resumen.find('.//TotalVentaNeta').text) if resumen.find('.//TotalVentaNeta') is not None else 0.0,
            'total_impuesto': float(resumen.find('.//TotalImpuesto').text) if resumen.find('.//TotalImpuesto') is not None else 0.0,
            'total_descuentos': float(resumen.find('.//TotalDescuentos').text) if resumen.find('.//TotalDescuentos') is not None else 0.0,
            'total_comprobante': float(resumen.find('.//TotalComprobante').text) if resumen.find('.//TotalComprobante') is not None else 0.0,
        }

    def _extract_payment_info(self, root):
        """Extract payment method and terms."""
        medio_pago = root.find('.//MedioPago')
        condicion_venta = root.find('.//CondicionVenta')

        return {
            'medio_pago': medio_pago.text if medio_pago is not None else '01',  # Default: Cash
            'condicion_venta': condicion_venta.text if condicion_venta is not None else '01',  # Default: Contado
        }

    def _extract_signature(self, root):
        """Extract digital signature information."""
        # Digital signature is in <ds:Signature> element
        signature = root.find('.//ds:Signature', self.NS)
        if signature is not None:
            return etree.tostring(signature, encoding='unicode')
        return None

    def _validate_invoice_data(self, data):
        """Validate parsed invoice data for consistency."""
        # Validate line items sum to summary totals
        lines_subtotal = sum(line['subtotal'] for line in data['line_items'])
        lines_tax = sum(line['impuesto'] for line in data['line_items'])
        lines_total = sum(line['monto_total_linea'] for line in data['line_items'])

        summary = data['summary']

        # Allow small rounding differences (0.50 colones)
        tolerance = 0.50

        if abs(lines_subtotal - summary['total_venta_neta']) > tolerance:
            raise ValidationError(_(
                'Line items subtotal (%.2f) does not match summary total (%.2f)'
            ) % (lines_subtotal, summary['total_venta_neta']))

        if abs(lines_tax - summary['total_impuesto']) > tolerance:
            raise ValidationError(_(
                'Line items tax (%.2f) does not match summary tax (%.2f)'
            ) % (lines_tax, summary['total_impuesto']))

        return True
```

### 2. Import Wizard

```python
# l10n_cr_einvoice/wizards/einvoice_import_wizard.py

import base64
import zipfile
import io
import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class EInvoiceImportWizard(models.TransientModel):
    _name = 'l10n_cr.einvoice.import.wizard'
    _description = 'E-Invoice XML Import Wizard'

    state = fields.Selection([
        ('upload', 'Upload File'),
        ('processing', 'Processing'),
        ('done', 'Completed'),
    ], default='upload', required=True)

    upload_file = fields.Binary(
        string='ZIP File with XMLs',
        required=True,
        help='Upload a ZIP file containing Costa Rica e-invoice XML files'
    )

    upload_filename = fields.Char(
        string='Filename'
    )

    # Settings
    skip_duplicates = fields.Boolean(
        string='Skip Duplicate Consecutives',
        default=True,
        help='If enabled, invoices with existing consecutive numbers will be skipped'
    )

    auto_create_partners = fields.Boolean(
        string='Auto-Create Missing Customers',
        default=True,
        help='Automatically create customer records for unknown tax IDs'
    )

    validate_signatures = fields.Boolean(
        string='Validate Digital Signatures',
        default=False,
        help='Verify XML digital signatures (slower but more secure)'
    )

    # Results (after processing)
    batch_id = fields.Many2one(
        'l10n_cr.einvoice.import.batch',
        string='Import Batch',
        readonly=True
    )

    total_files = fields.Integer(
        string='Total XML Files',
        readonly=True
    )

    success_count = fields.Integer(
        string='Successfully Imported',
        readonly=True
    )

    error_count = fields.Integer(
        string='Errors',
        readonly=True
    )

    processing_time = fields.Float(
        string='Processing Time (seconds)',
        readonly=True
    )

    error_log = fields.Text(
        string='Error Log',
        readonly=True
    )

    def action_start_import(self):
        """Start the import process."""
        self.ensure_one()

        if not self.upload_file:
            raise UserError(_('Please upload a ZIP file'))

        # Create import batch
        batch = self.env['l10n_cr.einvoice.import.batch'].create({
            'name': f'Import {self.upload_filename}',
            'company_id': self.env.company.id,
            'upload_file': self.upload_file,
            'upload_filename': self.upload_filename,
            'skip_duplicates': self.skip_duplicates,
            'auto_create_partners': self.auto_create_partners,
            'validate_signatures': self.validate_signatures,
        })

        self.batch_id = batch
        self.state = 'processing'

        # Process in background (async)
        self.env.ref('l10n_cr_einvoice.ir_cron_process_import_batch').sudo().method_direct_trigger()

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_process_batch(self):
        """Process the uploaded ZIP file (called by cron or manually)."""
        self.ensure_one()
        batch = self.batch_id

        start_time = time.time()

        try:
            batch.state = 'validating'

            # Extract ZIP file
            zip_data = base64.b64decode(self.upload_file)
            zip_buffer = io.BytesIO(zip_data)

            with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                # Get list of XML files
                xml_files = [f for f in zip_ref.namelist() if f.lower().endswith('.xml')]

                if not xml_files:
                    raise ValidationError(_('No XML files found in ZIP archive'))

                batch.total_files = len(xml_files)
                self.total_files = len(xml_files)

                batch.state = 'processing'

                # Process each XML file
                parser = self.env['l10n_cr.einvoice.xml.parser']
                errors = []
                success = 0

                for i, xml_filename in enumerate(xml_files):
                    try:
                        # Read XML content
                        xml_content = zip_ref.read(xml_filename)

                        # Parse XML
                        data = parser.parse_xml_file(xml_content)

                        # Create invoice in Odoo
                        invoice = self._create_invoice_from_data(data, xml_filename, batch)

                        if invoice:
                            success += 1

                        # Update progress every 50 invoices
                        if (i + 1) % 50 == 0:
                            batch.processed_count = i + 1
                            batch.success_count = success
                            self.env.cr.commit()  # Commit progress

                    except Exception as e:
                        # Log error but continue processing
                        error_msg = f'{xml_filename}: {str(e)}'
                        errors.append(error_msg)

                        # Create error log entry
                        self.env['l10n_cr.einvoice.import.error'].create({
                            'batch_id': batch.id,
                            'filename': xml_filename,
                            'error_type': 'other',
                            'error_message': str(e),
                            'xml_content': base64.b64encode(xml_content),
                        })

                # Final update
                batch.processed_count = len(xml_files)
                batch.success_count = success
                batch.error_count = len(errors)
                batch.error_log = '\n'.join(errors) if errors else ''
                batch.state = 'done'

                # Update wizard
                self.success_count = success
                self.error_count = len(errors)
                self.error_log = batch.error_log
                self.processing_time = time.time() - start_time
                batch.processing_time = self.processing_time
                self.state = 'done'

        except Exception as e:
            batch.state = 'error'
            batch.error_log = str(e)
            raise

    def _create_invoice_from_data(self, data, xml_filename, batch):
        """Create Odoo invoice record from parsed XML data."""
        # Check for duplicate consecutive
        if self.skip_duplicates:
            existing = self.env['account.move'].search([
                ('l10n_cr_consecutive', '=', data['consecutive']),
                ('company_id', '=', self.env.company.id),
            ], limit=1)

            if existing:
                # Skip duplicate
                return None

        # Find or create customer
        partner = self._find_or_create_partner(data['receptor'])

        # Determine move type
        move_type = self._get_move_type(data['document_type'])

        # Create invoice
        invoice_vals = {
            'move_type': move_type,
            'partner_id': partner.id if partner else False,
            'invoice_date': data['date'].date(),
            'invoice_date_due': data['date'].date(),
            'company_id': self.env.company.id,
            'currency_id': self.env.company.currency_id.id,

            # Costa Rica specific fields
            'l10n_cr_clave': data['clave'],
            'l10n_cr_consecutive': data['consecutive'],
            'l10n_cr_document_type': data['document_type'],

            # Historical import fields
            'l10n_cr_is_historical': True,
            'l10n_cr_import_batch_id': batch.id,
            'l10n_cr_original_xml': data['original_xml'],
            'l10n_cr_original_xml_filename': xml_filename,
            'l10n_cr_original_issue_date': data['date'],

            # Line items
            'invoice_line_ids': self._prepare_invoice_lines(data['line_items']),
        }

        invoice = self.env['account.move'].create(invoice_vals)

        # Post the invoice (historical invoices are already validated)
        invoice.action_post()

        return invoice

    def _find_or_create_partner(self, receptor_data):
        """Find existing customer or create new one."""
        if not receptor_data:
            return None

        vat = receptor_data['identificacion']

        # Search by VAT
        partner = self.env['res.partner'].search([
            ('vat', '=', vat),
            ('company_id', 'in', [False, self.env.company.id]),
        ], limit=1)

        if partner:
            return partner

        # Auto-create if enabled
        if self.auto_create_partners:
            partner = self.env['res.partner'].create({
                'name': receptor_data['nombre'],
                'vat': vat,
                'email': receptor_data.get('correo_electronico'),
                'phone': receptor_data.get('telefono'),
                'company_id': self.env.company.id,
                'country_id': self.env.ref('base.cr').id,
            })
            return partner

        raise ValidationError(_(
            'Customer with tax ID %s not found. Enable "Auto-Create Missing Customers" or create manually.'
        ) % vat)

    def _get_move_type(self, document_type):
        """Map Costa Rica document type to Odoo move type."""
        mapping = {
            'FE': 'out_invoice',      # Factura Electrónica
            'TE': 'out_invoice',      # Tiquete Electrónico
            'NC': 'out_refund',       # Nota de Crédito
            'ND': 'out_invoice',      # Nota de Débito (debit note, but Odoo uses invoice type)
        }
        return mapping.get(document_type, 'out_invoice')

    def _prepare_invoice_lines(self, line_items):
        """Prepare invoice line create values."""
        lines = []

        # Get default income account
        default_account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        # Get tax (13% IVA is standard in Costa Rica)
        tax_13 = self.env['account.tax'].search([
            ('amount', '=', 13),
            ('type_tax_use', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        for line_data in line_items:
            line_vals = {
                'sequence': line_data['sequence'],
                'name': line_data['detalle'],
                'quantity': line_data['cantidad'],
                'price_unit': line_data['precio_unitario'],
                'discount': 0.0,  # Calculate from line_data if needed
                'account_id': default_account.id,
            }

            # Add tax if applicable
            if line_data['tarifa_impuesto'] > 0:
                if tax_13 and abs(line_data['tarifa_impuesto'] - 13.0) < 0.1:
                    line_vals['tax_ids'] = [(6, 0, [tax_13.id])]

            lines.append((0, 0, line_vals))

        return lines

    def action_view_results(self):
        """View import results."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Results'),
            'res_model': 'l10n_cr.einvoice.import.batch',
            'res_id': self.batch_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_imported_invoices(self):
        """View list of imported invoices."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Imported Invoices'),
            'res_model': 'account.move',
            'domain': [('l10n_cr_import_batch_id', '=', self.batch_id.id)],
            'view_mode': 'tree,form',
            'target': 'current',
        }
```

### 3. UI Views

```xml
<!-- l10n_cr_einvoice/views/einvoice_import_views.xml -->

<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Import Wizard Form -->
    <record id="view_einvoice_import_wizard_form" model="ir.ui.view">
        <field name="name">l10n_cr.einvoice.import.wizard.form</field>
        <field name="model">l10n_cr.einvoice.import.wizard</field>
        <field name="arch" type="xml">
            <form string="Import Historical Invoices">
                <header>
                    <button name="action_start_import"
                            string="Start Import"
                            type="object"
                            class="btn-primary"
                            invisible="state != 'upload'"/>
                    <button name="action_view_results"
                            string="View Results"
                            type="object"
                            class="btn-primary"
                            invisible="state != 'done'"/>
                    <button name="action_view_imported_invoices"
                            string="View Imported Invoices"
                            type="object"
                            invisible="state != 'done'"/>
                    <field name="state" widget="statusbar"/>
                </header>

                <sheet>
                    <!-- Upload Step -->
                    <div invisible="state != 'upload'">
                        <div class="alert alert-info">
                            <strong>Historical Invoice Import</strong>
                            <p>Upload a ZIP file containing XML invoices from your previous e-invoicing provider.</p>
                            <ul>
                                <li>Supports Costa Rica v4.4 XML format</li>
                                <li>Maximum file size: 100 MB</li>
                                <li>Typical processing time: 20-30 minutes for 1,000 invoices</li>
                            </ul>
                        </div>

                        <group>
                            <group>
                                <field name="upload_file"
                                       filename="upload_filename"
                                       widget="binary"
                                       string="Select ZIP File"
                                       required="1"/>
                                <field name="upload_filename" invisible="1"/>
                            </group>
                            <group>
                                <field name="skip_duplicates"/>
                                <field name="auto_create_partners"/>
                                <field name="validate_signatures"/>
                            </group>
                        </group>

                        <div class="alert alert-warning">
                            <strong>Before importing:</strong>
                            <ol>
                                <li>Export all XML files from your old provider</li>
                                <li>Compress them into a single ZIP file</li>
                                <li>Record your last consecutive number for each document type</li>
                                <li>Configure your starting consecutives in Settings</li>
                            </ol>
                        </div>
                    </div>

                    <!-- Processing Step -->
                    <div invisible="state != 'processing'">
                        <div class="alert alert-info text-center">
                            <h3>
                                <i class="fa fa-spinner fa-spin"/> Processing Import...
                            </h3>
                            <p>This may take several minutes. Please do not close this window.</p>
                        </div>

                        <group>
                            <field name="total_files" readonly="1"/>
                            <field name="batch_id" readonly="1" invisible="1"/>
                        </group>

                        <!-- Real-time progress would be shown here via JavaScript -->
                        <div class="progress" style="height: 30px; margin: 20px 0;">
                            <div class="progress-bar progress-bar-striped active"
                                 role="progressbar"
                                 style="width: 50%">
                                Processing...
                            </div>
                        </div>
                    </div>

                    <!-- Results Step -->
                    <div invisible="state != 'done'">
                        <div class="alert alert-success text-center">
                            <h3>
                                <i class="fa fa-check-circle"/> Import Completed!
                            </h3>
                        </div>

                        <group>
                            <group string="Summary">
                                <field name="total_files" readonly="1"/>
                                <field name="success_count" readonly="1"/>
                                <field name="error_count" readonly="1"/>
                                <field name="processing_time" readonly="1" widget="float_time"/>
                            </group>
                        </group>

                        <group invisible="not error_log">
                            <field name="error_log"
                                   readonly="1"
                                   nolabel="1"
                                   widget="text"
                                   placeholder="No errors"/>
                        </group>

                        <div class="alert alert-info" invisible="error_count == 0">
                            <strong>Some files had errors.</strong>
                            <p>Review the error log above and fix any issues in the XML files, then re-import.</p>
                        </div>
                    </div>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Import Wizard Action -->
    <record id="action_einvoice_import_wizard" model="ir.actions.act_window">
        <field name="name">Import Historical Invoices</field>
        <field name="res_model">l10n_cr.einvoice.import.wizard</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
        <field name="binding_model_id" ref="account.model_account_move"/>
    </record>

    <!-- Menu Item -->
    <menuitem id="menu_einvoice_import"
              name="Import Historical Invoices"
              parent="account.menu_finance_configuration"
              action="action_einvoice_import_wizard"
              sequence="100"
              groups="account.group_account_manager"/>

    <!-- Import Batch List View -->
    <record id="view_einvoice_import_batch_tree" model="ir.ui.view">
        <field name="name">l10n_cr.einvoice.import.batch.tree</field>
        <field name="model">l10n_cr.einvoice.import.batch</field>
        <field name="arch" type="xml">
            <tree string="Import Batches" decoration-success="state == 'done'" decoration-danger="state == 'error'">
                <field name="create_date"/>
                <field name="name"/>
                <field name="total_files"/>
                <field name="success_count"/>
                <field name="error_count"/>
                <field name="processing_time" widget="float_time"/>
                <field name="state"/>
            </tree>
        </field>
    </record>

    <!-- Import Batch Form View -->
    <record id="view_einvoice_import_batch_form" model="ir.ui.view">
        <field name="name">l10n_cr.einvoice.import.batch.form</field>
        <field name="model">l10n_cr.einvoice.import.batch</field>
        <field name="arch" type="xml">
            <form string="Import Batch">
                <header>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1><field name="name"/></h1>
                    </div>

                    <group>
                        <group string="Import Details">
                            <field name="company_id"/>
                            <field name="create_date"/>
                            <field name="upload_filename"/>
                        </group>
                        <group string="Statistics">
                            <field name="total_files"/>
                            <field name="processed_count"/>
                            <field name="success_count"/>
                            <field name="error_count"/>
                            <field name="processing_time" widget="float_time"/>
                        </group>
                    </group>

                    <group string="Settings">
                        <field name="skip_duplicates"/>
                        <field name="auto_create_partners"/>
                        <field name="validate_signatures"/>
                    </group>

                    <notebook>
                        <page string="Imported Invoices" name="invoices">
                            <field name="invoice_ids" mode="tree">
                                <tree>
                                    <field name="l10n_cr_consecutive"/>
                                    <field name="invoice_date"/>
                                    <field name="partner_id"/>
                                    <field name="amount_total"/>
                                    <field name="state"/>
                                </tree>
                            </field>
                        </page>
                        <page string="Error Log" name="errors" invisible="not error_log">
                            <field name="error_log" widget="text" nolabel="1"/>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Import Batch Action -->
    <record id="action_einvoice_import_batch" model="ir.actions.act_window">
        <field name="name">Import History</field>
        <field name="res_model">l10n_cr.einvoice.import.batch</field>
        <field name="view_mode">tree,form</field>
    </record>

    <!-- Menu Item for Import History -->
    <menuitem id="menu_einvoice_import_history"
              name="Import History"
              parent="account.menu_finance_reports"
              action="action_einvoice_import_batch"
              sequence="200"
              groups="account.group_account_manager"/>

</odoo>
```

---

## Testing Strategy

### Unit Tests

```python
# l10n_cr_einvoice/tests/test_xml_import.py

from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
import base64

class TestXMLImport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.parser = self.env['l10n_cr.einvoice.xml.parser']
        self.wizard = self.env['l10n_cr.einvoice.import.wizard']

        # Load sample XML files
        self.sample_fe_xml = self._load_sample_xml('valid_fe.xml')
        self.sample_te_xml = self._load_sample_xml('valid_te.xml')
        self.sample_nc_xml = self._load_sample_xml('valid_nc.xml')

    def _load_sample_xml(self, filename):
        """Load sample XML file from test data."""
        path = f'l10n_cr_einvoice/tests/sample_xmls/{filename}'
        with open(path, 'rb') as f:
            return f.read()

    def test_parse_valid_factura_electronica(self):
        """Test parsing a valid Factura Electrónica (FE)."""
        data = self.parser.parse_xml_file(self.sample_fe_xml)

        # Verify key fields extracted
        self.assertEqual(len(data['clave']), 50, "Clave should be 50 digits")
        self.assertIn('001-00001-01', data['consecutive'], "FE consecutive format")
        self.assertEqual(data['document_type'], 'FE')
        self.assertIsNotNone(data['receptor'], "FE should have receptor")
        self.assertGreater(len(data['line_items']), 0, "FE should have line items")

    def test_parse_valid_tiquete_electronico(self):
        """Test parsing a valid Tiquete Electrónico (TE)."""
        data = self.parser.parse_xml_file(self.sample_te_xml)

        # Verify TE specifics
        self.assertIn('001-00001-04', data['consecutive'], "TE consecutive format")
        self.assertEqual(data['document_type'], 'TE')
        # TE may not have receptor (optional for tickets)

    def test_parse_invalid_xml(self):
        """Test parsing malformed XML raises ValidationError."""
        invalid_xml = b'<NotValidXML>incomplete'

        with self.assertRaises(ValidationError):
            self.parser.parse_xml_file(invalid_xml)

    def test_parse_missing_clave(self):
        """Test XML without clave raises ValidationError."""
        xml_no_clave = b'''<?xml version="1.0" encoding="utf-8"?>
        <FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
            <NumeroConsecutivo>001-00001-01-00000000123</NumeroConsecutivo>
        </FacturaElectronica>'''

        with self.assertRaises(ValidationError):
            self.parser.parse_xml_file(xml_no_clave)

    def test_import_wizard_creates_batch(self):
        """Test wizard creates import batch."""
        # Create sample ZIP file
        zip_content = self._create_sample_zip([self.sample_fe_xml])

        wizard = self.wizard.create({
            'upload_file': base64.b64encode(zip_content),
            'upload_filename': 'test_import.zip',
        })

        wizard.action_start_import()

        # Verify batch created
        self.assertTrue(wizard.batch_id, "Batch should be created")
        self.assertEqual(wizard.state, 'processing')

    def test_import_creates_invoices(self):
        """Test full import process creates Odoo invoices."""
        # Create ZIP with sample XMLs
        zip_content = self._create_sample_zip([
            self.sample_fe_xml,
            self.sample_te_xml,
        ])

        wizard = self.wizard.create({
            'upload_file': base64.b64encode(zip_content),
            'upload_filename': 'test_import.zip',
            'auto_create_partners': True,
        })

        wizard.action_start_import()
        wizard.action_process_batch()

        # Verify invoices created
        self.assertEqual(wizard.success_count, 2, "Should import 2 invoices")
        self.assertEqual(wizard.error_count, 0, "Should have no errors")

        # Verify invoice records
        invoices = self.env['account.move'].search([
            ('l10n_cr_import_batch_id', '=', wizard.batch_id.id)
        ])
        self.assertEqual(len(invoices), 2)

        # Verify marked as historical
        for invoice in invoices:
            self.assertTrue(invoice.l10n_cr_is_historical)
            self.assertIsNotNone(invoice.l10n_cr_original_xml)

    def test_duplicate_detection(self):
        """Test skip_duplicates setting works."""
        # Import same file twice
        zip_content = self._create_sample_zip([self.sample_fe_xml])

        # First import
        wizard1 = self.wizard.create({
            'upload_file': base64.b64encode(zip_content),
            'upload_filename': 'import1.zip',
        })
        wizard1.action_start_import()
        wizard1.action_process_batch()

        self.assertEqual(wizard1.success_count, 1)

        # Second import with skip_duplicates=True
        wizard2 = self.wizard.create({
            'upload_file': base64.b64encode(zip_content),
            'upload_filename': 'import2.zip',
            'skip_duplicates': True,
        })
        wizard2.action_start_import()
        wizard2.action_process_batch()

        self.assertEqual(wizard2.success_count, 0, "Should skip duplicate")

        # Verify only one invoice exists
        invoices = self.env['account.move'].search([
            ('l10n_cr_consecutive', '=', 'CONSECUTIVE_FROM_XML')
        ])
        self.assertEqual(len(invoices), 1)

    def _create_sample_zip(self, xml_contents):
        """Create a ZIP file from list of XML contents."""
        import zipfile
        import io

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, xml_content in enumerate(xml_contents):
                zip_file.writestr(f'invoice_{i+1}.xml', xml_content)

        return zip_buffer.getvalue()
```

### Integration Tests

```python
# l10n_cr_einvoice/tests/test_xml_import_integration.py

from odoo.tests import TransactionCase
import base64
import os

class TestXMLImportIntegration(TransactionCase):

    def test_large_batch_import(self):
        """Test importing 1,000+ invoices performs well."""
        # This test uses real XML samples from docs/sample_xmls/
        # Create ZIP with 1,200 XMLs

        # Performance targets:
        # - Complete in < 30 minutes
        # - Memory usage < 500 MB
        # - Success rate > 99%
        pass

    def test_concurrent_imports(self):
        """Test multiple users can't import simultaneously (safety check)."""
        pass

    def test_error_recovery(self):
        """Test import can resume after interruption."""
        pass
```

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All unit tests passing (100% coverage of parser)
- [ ] Integration tests passing
- [ ] Performance testing completed (1,200 invoices in < 30 minutes)
- [ ] User documentation written
- [ ] Demo video recorded
- [ ] Sample XML files available for testing
- [ ] Database migration script ready
- [ ] Rollback plan documented

### Deployment Steps

**1. Database Backup** (Before deployment)
```bash
pg_dump odoo_production > backup_$(date +%Y%m%d).sql
```

**2. Update Module** (Deploy code)
```bash
git pull origin main
sudo systemctl restart odoo
```

**3. Upgrade Module** (Apply database changes)
```bash
odoo-bin -u l10n_cr_einvoice -d production_db --stop-after-init
```

**4. Run Post-Upgrade Tests**
```bash
odoo-bin -d production_db --test-enable --stop-after-init
```

**5. Verify in UI**
- [ ] Import wizard accessible from menu
- [ ] Upload file works
- [ ] Sample import completes successfully
- [ ] Imported invoices display correctly

### Rollback Plan

**If issues occur:**
```bash
# 1. Restore database backup
pg_restore -d production_db backup_YYYYMMDD.sql

# 2. Revert code
git checkout previous_stable_tag
sudo systemctl restart odoo

# 3. Notify users
```

---

## Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Import Speed | 50-60 XMLs/min | Process 1,200 invoices in 20-25 minutes |
| Error Rate | < 1% | 99%+ invoices import successfully on valid data |
| Memory Usage | < 500 MB | Monitor during 1,200 invoice import |
| UI Response | < 2 seconds | Upload wizard loads and responds quickly |
| Database Impact | < 5% | Import doesn't slow down other operations |

### Business Metrics

| Metric | Target | Timeline |
|--------|--------|----------|
| Customer Adoption | 20+ customers use import | First 3 months |
| Migration Win Rate | 50%+ of migrations | vs. 30% without feature |
| Support Tickets | < 5 import issues | Per 100 imports |
| Customer Satisfaction | 4.5+ stars | Import feature rating |
| Time Savings | 2+ hours saved | Per customer migration |

### Competitive Metrics

| Metric | Target | Comparison |
|--------|--------|------------|
| Faster than FACTURATica | Yes | Self-service vs. manual support |
| More features than GTI | Yes | GTI has no import at all |
| Easiest in market | Yes | Simplest UI, clearest docs |

---

## Documentation Deliverables

### 1. User Guide

**File:** `l10n_cr_einvoice/static/description/IMPORT_GUIDE.md`

**Contents:**
- How to export XMLs from common providers (GTI, FACTURATica, TicoPay)
- Step-by-step import wizard walkthrough (with screenshots)
- Troubleshooting common errors
- FAQ section

### 2. Technical Documentation

**File:** `l10n_cr_einvoice/static/description/TECHNICAL_SPECS.md`

**Contents:**
- XML parser architecture
- Database schema changes
- API documentation for models
- Extension points for customization

### 3. Demo Video

**Duration:** 3-5 minutes
**Content:**
- Show export from old provider
- Upload ZIP to Odoo
- Watch progress
- Review results
- View imported invoices

**Script:**
```
[0:00-0:30] Introduction
"In this video, I'll show you how to migrate your complete invoice history
from GTI, FACTURATica, or any other Costa Rica e-invoicing provider to Odoo
in just 30 minutes."

[0:30-1:30] Export from Old System
"First, login to your old provider and export all your XML files..."

[1:30-3:00] Import to Odoo
"Now, in Odoo, go to Settings → Import Historical Invoices..."

[3:00-4:00] Review Results
"The import is complete! Let's review the results..."

[4:00-5:00] Verify Data
"All your invoices are now in Odoo with complete history..."
```

---

## Risk Assessment & Mitigation

### High-Risk Issues

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Performance issues with large imports** | High | Medium | Batch processing, progress commits, memory optimization |
| **XML schema variations between providers** | High | Medium | Extensive testing with real files, flexible parser |
| **Data loss during import** | Critical | Low | Transaction rollback on errors, extensive validation |
| **Customer matching failures** | High | Medium | Auto-create option, clear error messages, retry mechanism |

### Medium-Risk Issues

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Duplicate invoice detection false positives** | Medium | Medium | Skip duplicates option, clear UI warnings |
| **Tax calculation mismatches** | Medium | Low | Validate amounts, allow manual correction |
| **File size limits** | Medium | Low | Document limits, provide chunking instructions |

### Low-Risk Issues

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **UI/UX confusion** | Low | Medium | User testing, clear documentation, tooltips |
| **Browser compatibility** | Low | Low | Test on major browsers |
| **Translation issues** | Low | Low | Spanish language review |

---

## Next Steps After Completion

### Phase 4: Enhanced Features (Optional)

**IF customer demand justifies:**

1. **PDF Regeneration** (3-4 days)
   - Generate PDFs from imported XMLs
   - Apply current company branding
   - QR code generation for old invoices

2. **Advanced Analytics** (2-3 days)
   - Multi-year trend dashboards
   - Customer lifecycle analysis
   - Product performance history

3. **Batch Operations** (2-3 days)
   - Bulk re-send invoices by email
   - Bulk export to Excel
   - Bulk print to PDF

4. **API Integration** (5-7 days)
   - Direct API import from known providers
   - Skip XML file export step
   - One-click migration from GTI, FACTURATica

---

## Conclusion

This implementation plan provides a complete roadmap for building the **first self-service XML import feature in the Costa Rica e-invoicing market**.

**Key Advantages:**
- ✅ **Self-service**: No support tickets, instant processing
- ✅ **Fast**: 30 minutes for 1,200 invoices vs. days with FACTURATica
- ✅ **Free**: Included, not an extra charge
- ✅ **Complete**: Full data fidelity with original XMLs preserved
- ✅ **Professional**: Enterprise-grade validation and error handling

**Timeline:** 12 days = **3 weeks to market leadership**

**Investment:** ~$10,000 development cost
**Return:** $50,000-$100,000 extra revenue in Year 1 from improved win rate and retention

**Competitive Position:**
"The only e-invoicing solution in Costa Rica with true self-service migration"

---

**Status:** 📋 Ready for Development
**Owner:** Development Team
**Priority:** HIGH - Competitive Differentiator
**Start Date:** TBD
**Target Completion:** 12 working days from start

---

**Document Version:** 1.0
**Last Updated:** 2025-12-29
**Next Review:** After Day 6 (mid-sprint checkpoint)
