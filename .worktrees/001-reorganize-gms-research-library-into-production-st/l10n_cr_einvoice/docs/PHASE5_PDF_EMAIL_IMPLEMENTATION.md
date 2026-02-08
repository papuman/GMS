# Phase 5: PDF Report Generation and Email Delivery

## Implementation Summary

Phase 5 adds PDF report generation with QR codes and automated email delivery functionality to the Costa Rica e-invoicing module. This phase completes the end-to-end e-invoicing workflow by providing customer-facing documents and communication.

**Implementation Date:** 2025-12-28
**Odoo Version:** 19.0
**Status:** ✅ COMPLETE

---

## Table of Contents

1. [Overview](#overview)
2. [Components Implemented](#components-implemented)
3. [QR Code Generation](#qr-code-generation)
4. [PDF Report Template](#pdf-report-template)
5. [Email Templates](#email-templates)
6. [Model Methods](#model-methods)
7. [UI Updates](#ui-updates)
8. [Workflow Integration](#workflow-integration)
9. [Testing](#testing)
10. [Usage Guide](#usage-guide)
11. [Configuration](#configuration)
12. [Troubleshooting](#troubleshooting)

---

## Overview

Phase 5 implements the final components of the e-invoicing system:

- **QR Code Generation**: Generates QR codes linking to Hacienda validation pages
- **PDF Reports**: Professional PDF invoices with QR codes and all required information
- **Email Delivery**: Automated email sending to customers with PDF attachments
- **Auto-send Workflow**: Automatic email dispatch when invoices are accepted by Hacienda

### Key Features

✅ QR code generation per Hacienda specifications
✅ Professional PDF report template with Costa Rica compliance
✅ Email templates for invoices and tickets
✅ Manual and automatic email sending
✅ PDF download functionality
✅ Company configuration for auto-send behavior

---

## Components Implemented

### Files Created

```
l10n_cr_einvoice/
├── models/
│   └── qr_generator.py              # QR code generation logic
├── reports/
│   └── einvoice_report_templates.xml  # PDF report templates
├── data/
│   └── email_templates.xml          # Email templates
└── docs/
    └── PHASE5_PDF_EMAIL_IMPLEMENTATION.md  # This file
```

### Files Modified

```
l10n_cr_einvoice/
├── models/
│   ├── __init__.py                  # Added qr_generator import
│   └── einvoice_document.py         # Added PDF/email methods
├── views/
│   └── einvoice_document_views.xml  # Added PDF/email buttons
└── __manifest__.py                  # Added email_templates.xml
```

### Test Script

```
test_phase5_pdf_email.py             # Comprehensive test suite
```

---

## QR Code Generation

### Model: `l10n_cr.qr.generator`

**File:** `models/qr_generator.py`

An AbstractModel that provides QR code generation services for e-invoice documents.

### QR Code Specifications

Following Hacienda requirements:

- **URL Format:** `https://tribunet.hacienda.go.cr/docs/esquemas/2017/v4.3/facturaElectronica.html?clave={clave}`
- **Size:** Minimum 150x150 pixels
- **Error Correction:** HIGH level (30% damage tolerance)
- **Format:** Base64 encoded PNG
- **Purpose:** Customer validation of invoice authenticity

### Key Methods

#### `generate_qr_code(clave)`

Generates a QR code for a 50-digit clave.

```python
qr_generator = env['l10n_cr.qr.generator']
qr_code_base64 = qr_generator.generate_qr_code(clave)
```

**Parameters:**
- `clave` (str): 50-digit Hacienda key

**Returns:**
- `str`: Base64 encoded PNG image

**Raises:**
- `UserError`: If qrcode library not installed or invalid clave

#### `generate_qr_code_for_document(document)`

Convenience method for generating QR code from document record.

```python
qr_code = qr_generator.generate_qr_code_for_document(einvoice_doc)
```

### Dependencies

Requires the `qrcode` Python library:

```bash
pip install qrcode[pil]
```

Already declared in `__manifest__.py` external dependencies.

---

## PDF Report Template

### Report: `action_report_einvoice`

**File:** `reports/einvoice_report_templates.xml`

A QWeb PDF report that generates professional invoices compliant with Costa Rica requirements.

### Template Features

#### Header Section
- Document type (Factura/Tiquete/Nota de Crédito/Débito)
- "DOCUMENTO ELECTRÓNICO" designation
- QR code (150x150px) for validation

#### Document Information
- Document number
- Invoice date
- 50-digit clave (monospace font for readability)
- Acceptance status and date

#### Company Information (Emisor)
- Company name
- Cédula Jurídica (tax ID)
- Complete address
- Phone and email

#### Customer Information (Receptor)
- Customer name
- Cédula/ID number
- Complete address
- Contact information

#### Line Items Table
- Line number
- Product/service description
- Product code (if available)
- Quantity and unit of measure
- Unit price
- Discount percentage
- Tax percentage
- Line total

#### Totals Section
- Subtotal (before taxes)
- Tax breakdown by group
- Grand total

#### Additional Information
- Payment terms
- Notes/narration
- Legal footer text

#### Footer
- "DOCUMENTO ELECTRÓNICO" statement
- Authorization text
- Clave verification instructions
- Generation timestamp

### Costa Rica Compliance

The template includes all required elements:

✅ "DOCUMENTO ELECTRÓNICO" designation
✅ 50-digit clave prominently displayed
✅ QR code for Hacienda validation
✅ Cédula Jurídica for company and customer
✅ Complete tax breakdown
✅ Legal authorization footer

### Template Structure

```xml
<template id="report_einvoice_document">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="o">
            <t t-call="web.external_layout">
                <div class="page">
                    <!-- Header with QR Code -->
                    <!-- Document Information -->
                    <!-- Company and Customer Info -->
                    <!-- Line Items Table -->
                    <!-- Totals -->
                    <!-- Footer -->
                </div>
            </t>
        </t>
    </t>
</template>
```

### Customization

The template can be customized by:

1. **Inheriting the template:**
```xml
<template id="custom_report" inherit_id="l10n_cr_einvoice.report_einvoice_document">
    <!-- XPath modifications -->
</template>
```

2. **Overriding the report action:**
```xml
<record id="action_report_einvoice" model="ir.actions.report">
    <field name="report_name">custom_module.custom_template</field>
</record>
```

---

## Email Templates

### Templates Created

**File:** `data/email_templates.xml`

#### 1. Electronic Invoice Template (`email_template_einvoice`)

Professional email template for standard invoices (FE, NC, ND).

**Features:**
- Responsive HTML design
- Company branding colors
- Invoice details table
- Verification instructions
- PDF attachment

**Subject:** `Factura Electrónica {document.name} - {company.name}`

**Structure:**
```
┌─────────────────────────────────┐
│      Company Header (Blue)      │
├─────────────────────────────────┤
│   Greeting: "Estimado/a..."     │
│                                 │
│   ┌─────────────────────┐       │
│   │ Invoice Details     │       │
│   │ - Number            │       │
│   │ - Date              │       │
│   │ - Total Amount      │       │
│   │ - Clave             │       │
│   │ - Status            │       │
│   └─────────────────────┘       │
│                                 │
│   Verification Instructions     │
│   Payment Terms                 │
│   Signature                     │
├─────────────────────────────────┤
│   Footer (Company Info)         │
└─────────────────────────────────┘
```

#### 2. Electronic Ticket Template (`email_template_eticket`)

Simplified template for electronic tickets (TE).

**Features:**
- Lightweight design
- Essential information only
- Quick read format

**Subject:** `Tiquete Electrónico {document.name} - {company.name}`

### Email Configuration

Templates support:
- Multi-language (uses partner language)
- Monetary formatting
- Date formatting
- Conditional content display
- Automatic PDF attachment

### Template Variables

Available in templates:

- `object` - The einvoice document record
- `object.partner_id` - Customer
- `object.company_id` - Company
- `object.move_id` - Related invoice
- `format_date()` - Date formatting function
- `format_amount()` - Monetary formatting function

---

## Model Methods

### Added to `l10n_cr.einvoice.document`

**File:** `models/einvoice_document.py`

### Public Action Methods

#### `action_generate_pdf()`

Generates PDF report with QR code.

```python
einvoice_doc.action_generate_pdf()
```

**Workflow:**
1. Validates clave exists
2. Validates XML content exists
3. Calls report rendering engine
4. Creates PDF attachment
5. Links attachment to document
6. Returns success notification

**Returns:** Notification action dict

**Raises:** UserError if validation fails

#### `action_download_pdf()`

Downloads the PDF attachment.

```python
result = einvoice_doc.action_download_pdf()
```

**Returns:** `ir.actions.act_url` action dict

**Raises:** UserError if no PDF attachment

#### `action_send_email()`

Sends email to customer with PDF attachment.

```python
einvoice_doc.action_send_email()
```

**Workflow:**
1. Validates document is accepted
2. Validates customer has email
3. Generates PDF if not exists
4. Selects appropriate template (invoice/ticket)
5. Sends email with PDF attachment
6. Updates email_sent flag and date
7. Returns success notification

**Returns:** Notification action dict

**Raises:** UserError if validation fails or template not found

### Internal Methods

#### `_auto_send_email_on_acceptance()`

Automatically sends email when document is accepted.

Called internally by `_process_hacienda_response()` when state changes to 'accepted'.

**Logic:**
```python
if company.l10n_cr_auto_send_email:
    if not email_sent:
        if partner.email:
            action_send_email()
```

**Features:**
- Respects company configuration
- Checks if already sent
- Validates email address exists
- Logs but doesn't fail if email fails

#### `_get_qr_code_image()`

Gets QR code image for use in PDF templates.

```python
qr_code_base64 = einvoice_doc._get_qr_code_image()
```

**Returns:** Base64 encoded PNG or False

Called by PDF template: `<t t-set="qr_code" t-value="o._get_qr_code_image()"/>`

### Workflow Integration

Modified `_process_hacienda_response()` to trigger auto-send:

```python
if status == 'aceptado':
    vals.update({
        'state': 'accepted',
        'hacienda_acceptance_date': fields.Datetime.now(),
        'error_message': False,
    })

    # Update document first
    self.write(vals)

    # Auto-send email if configured
    self._auto_send_email_on_acceptance()

    return  # Early return to avoid duplicate write
```

---

## UI Updates

### Form View Buttons

**File:** `views/einvoice_document_views.xml`

#### Header Buttons

Added to the form header (after Check Status):

```xml
<!-- PDF and Email Buttons -->
<button name="action_generate_pdf" string="Generate PDF"
        type="object" class="oe_highlight"
        invisible="not xml_content or pdf_attachment_id"/>

<button name="action_send_email" string="Send Email"
        type="object"
        invisible="state != 'accepted' or email_sent"/>
```

**Visibility Logic:**

- **Generate PDF**: Shown when XML exists and PDF not yet generated
- **Send Email**: Shown when document accepted and email not sent

#### Smart Buttons

Added PDF download smart button:

```xml
<button name="action_download_pdf"
        type="object"
        class="oe_stat_button"
        icon="fa-file-pdf-o"
        invisible="not pdf_attachment_id">
    <span class="o_stat_text">Download PDF</span>
</button>
```

Located in button box alongside:
- Invoice button
- Download XML button
- Hacienda Response button

### Tree View

Already includes:
- `email_sent` field with boolean toggle widget
- State-based decorations

### Search View

Already includes filters for:
- Email Sent
- Email Pending (accepted but not sent)

---

## Workflow Integration

### Complete E-Invoice Lifecycle

```
Draft → Generate XML → Sign XML → Submit → Accepted
                                              ↓
                                        Generate PDF
                                              ↓
                                     Auto-send Email? ←─── Company Config
                                              ↓
                                            Email
                                            Sent
```

### Auto-send Trigger

When Hacienda accepts a document:

1. `action_submit_to_hacienda()` or `action_check_status()` called
2. `_process_hacienda_response(response)` processes response
3. If status is 'aceptado':
   - Update state to 'accepted'
   - Set acceptance date
   - **Call `_auto_send_email_on_acceptance()`**
4. Auto-send checks:
   - Is `company.l10n_cr_auto_send_email` enabled?
   - Is email not already sent?
   - Does customer have email address?
5. If all checks pass:
   - Generate PDF (if needed)
   - Select template (invoice/ticket)
   - Send email
   - Mark email_sent = True

### Manual Workflow

User can also manually:

1. **Generate PDF:** Click "Generate PDF" button
2. **Download PDF:** Click PDF smart button
3. **Send Email:** Click "Send Email" button
4. **Resend Email:** Use existing "Resend Email" functionality

---

## Testing

### Test Script

**File:** `test_phase5_pdf_email.py`

Comprehensive test suite covering:

#### Test Coverage

1. **QR Code Generator Model**
   - Valid clave generation
   - URL format validation
   - Base64 output validation

2. **Find Test Documents**
   - Search for accepted documents
   - Fallback to any document
   - Document information display

3. **PDF Report Generation**
   - QR code integration
   - PDF attachment creation
   - File size validation

4. **Email Template**
   - Template existence
   - Template rendering
   - Variable substitution

5. **Email Sending Logic**
   - Prerequisite checks
   - Dry run mode (no actual sending)
   - Attachment validation

6. **Auto-send Configuration**
   - Company field existence
   - Configuration value check

7. **PDF Download Action**
   - Action return validation
   - URL format check

8. **Report Template**
   - Template existence
   - Configuration validation

### Running Tests

#### In Odoo Shell

```bash
odoo-bin shell -c odoo.conf -d your_database
```

```python
>>> exec(open('test_phase5_pdf_email.py').read())
```

#### Expected Output

```
================================================================================
PHASE 5: PDF REPORT GENERATION AND EMAIL DELIVERY - TEST SUITE
================================================================================

1. Testing QR Code Generator Model
--------------------------------------------------------------------------------
  ✓ QR code generation successful
  ✓ Generated QR code (base64 length: 2847)
  ✓ QR URL format correct: https://tribunet.hacienda.go.cr/docs/esquemas/...

2. Finding Test E-Invoice Documents
--------------------------------------------------------------------------------
  ✓ Found document: FE-0000000001
    - State: accepted
    - Clave: 50601011234567890101234567890123456789012345678901
    - Customer: Test Customer
    - Email: customer@example.com

...

================================================================================
TEST SUMMARY
================================================================================

Total Tests: 15
Passed: 15 ✓
Failed: 0 ✗
Warnings: 0 ⚠

✓ PASSED:
  • QR code generation
  • QR URL format
  • Find test documents
  ...

Success Rate: 100.0%

================================================================================
✓ ALL TESTS PASSED - PHASE 5 IMPLEMENTATION COMPLETE!
================================================================================
```

---

## Usage Guide

### For Developers

#### Generating PDF Programmatically

```python
# Get document
doc = env['l10n_cr.einvoice.document'].browse(doc_id)

# Generate PDF
doc.action_generate_pdf()

# Access PDF
pdf_data = doc.pdf_attachment_id.datas
pdf_filename = doc.pdf_attachment_id.name
```

#### Sending Email Programmatically

```python
# Send email
doc.action_send_email()

# Check if sent
if doc.email_sent:
    sent_date = doc.email_sent_date
```

#### Generating QR Code

```python
# Generate QR for any clave
qr_gen = env['l10n_cr.qr.generator']
qr_code = qr_gen.generate_qr_code(clave)

# Use in template
<img t-att-src="'data:image/png;base64,' + qr_code"/>
```

### For End Users

#### Manual Process

1. **Create and submit e-invoice** (Phases 1-4)
2. Wait for Hacienda acceptance
3. Once accepted:
   - Click **"Generate PDF"** button (if auto-gen disabled)
   - Click **"Send Email"** button to email customer
   - Or click **PDF smart button** to download

#### Automatic Process

1. Configure company: Enable "Auto-send Email"
2. Create and submit e-invoice
3. System automatically:
   - Generates PDF when accepted
   - Sends email to customer
   - Marks as sent

#### Downloading PDF

Multiple ways:

1. **Smart Button:** Click "Download PDF" in form view
2. **Attachments Tab:** Access via attachments page
3. **Print Menu:** Use standard Odoo print functionality

---

## Configuration

### Company Settings

**Menu:** Settings → Companies → [Your Company] → E-Invoicing

#### Auto-send Email

```python
company.l10n_cr_auto_send_email = True  # Enable auto-send
```

**Field:** `l10n_cr_auto_send_email` (Boolean)
**Default:** `True`
**Description:** Automatically send email when e-invoice is accepted by Hacienda

### Email Template Customization

#### Override Default Template

In company settings (future enhancement):

```python
company.l10n_cr_einvoice_email_template_id = custom_template
```

#### Create Custom Template

```xml
<record id="my_custom_template" model="mail.template">
    <field name="name">My Custom Invoice Email</field>
    <field name="model_id" ref="model_l10n_cr_einvoice_document"/>
    <!-- ... template fields ... -->
</record>
```

### PDF Report Customization

#### Add Company Logo

1. Go to Settings → Companies
2. Upload logo in company form
3. Logo automatically appears in PDF (via `web.external_layout`)

#### Customize Colors/Styling

Inherit and modify template:

```xml
<template id="custom_pdf_style" inherit_id="l10n_cr_einvoice.report_einvoice_document">
    <xpath expr="//div[@class='page']" position="attributes">
        <attribute name="style">font-family: Arial; color: #333;</attribute>
    </xpath>
</template>
```

---

## Troubleshooting

### Common Issues

#### QR Code Library Not Installed

**Error:** "QR code library is not installed"

**Solution:**
```bash
pip install qrcode[pil]
```

Or in requirements.txt:
```
qrcode[pil]>=7.4.2
```

#### PDF Generation Fails

**Error:** "Cannot generate PDF: Document has no clave"

**Causes:**
- Document not processed through full workflow
- XML not generated

**Solution:**
1. Ensure document has gone through "Generate XML" step
2. Check that clave field is populated
3. Verify XML content exists

#### Email Not Sending

**Error:** "Customer has no email address"

**Solution:**
1. Add email to customer record
2. Go to Contacts → [Customer] → Email field

**Error:** "Email template not found"

**Solution:**
1. Check module installation
2. Verify `data/email_templates.xml` loaded
3. Check: Settings → Technical → Email Templates

#### Email Not Auto-sending

**Check:**
1. Company auto-send enabled: `company.l10n_cr_auto_send_email`
2. Document state is 'accepted'
3. Customer has email address
4. Email not already sent
5. Check logs for errors

**Enable Debug Logging:**
```python
import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
```

#### PDF Missing QR Code

**Causes:**
- QR generation failed silently
- Template issue

**Debug:**
```python
# Test QR generation
doc = env['l10n_cr.einvoice.document'].browse(doc_id)
qr = doc._get_qr_code_image()
print(f"QR Code: {'Generated' if qr else 'Failed'}")
```

### Log Locations

Check Odoo logs for:

```
INFO l10n_cr.qr.generator: Generated QR code for clave: 50601011234567...
INFO l10n_cr.einvoice.document: Generated PDF for document FE-0000000001
INFO l10n_cr.einvoice.document: Sent email for document FE-0000000001 to customer@example.com
INFO l10n_cr.einvoice.document: Auto-sent email for document FE-0000000001
```

### Performance Considerations

#### Large Volume Scenarios

If processing many invoices:

1. **Batch PDF Generation:**
```python
docs = env['l10n_cr.einvoice.document'].search([
    ('state', '=', 'accepted'),
    ('pdf_attachment_id', '=', False)
])
for doc in docs:
    try:
        doc.action_generate_pdf()
        env.cr.commit()  # Commit each to avoid rollback
    except Exception as e:
        _logger.error(f"PDF gen failed for {doc.name}: {e}")
        continue
```

2. **Async Email Sending:**
Consider using Odoo's queue_job module for high volumes

3. **PDF Caching:**
PDFs are created once and stored as attachments

---

## Technical Notes

### Dependencies

External Python libraries:

```python
'external_dependencies': {
    'python': [
        'qrcode',  # QR code generation
    ],
}
```

### Database Fields

Added to `l10n_cr.einvoice.document`:

```python
pdf_attachment_id = fields.Many2one('ir.attachment', string='PDF with QR')
email_sent = fields.Boolean(string='Email Sent', default=False)
email_sent_date = fields.Datetime(string='Email Sent Date')
```

### Report Rendering

Uses Odoo's QWeb report engine:

```python
report = env.ref('l10n_cr_einvoice.action_report_einvoice')
pdf_content, _ = report._render_qweb_pdf([doc_id])
```

### Email Sending

Uses Odoo's mail.template:

```python
template = env.ref('l10n_cr_einvoice.email_template_einvoice')
template.send_mail(
    doc_id,
    force_send=True,
    email_values={'attachment_ids': [(4, pdf_attachment_id)]}
)
```

---

## Future Enhancements

Potential improvements for future phases:

1. **Multi-PDF Support**
   - Different PDF layouts per document type
   - Customer-specific templates

2. **Email Scheduling**
   - Scheduled batch sending
   - Retry logic for failed sends

3. **Advanced QR Codes**
   - Multiple QR codes per page
   - Custom QR content

4. **PDF Signatures**
   - Visual signature on PDF
   - Digital PDF signatures

5. **Analytics**
   - Email open tracking
   - PDF download tracking
   - Customer engagement metrics

6. **Localization**
   - Multi-language PDF templates
   - Regional format variations

---

## Compliance Notes

### Costa Rica Requirements Met

✅ **QR Code:** Links to Hacienda validation page
✅ **Clave Display:** 50-digit key prominently shown
✅ **Legal Text:** "DOCUMENTO ELECTRÓNICO" designation
✅ **Tax Details:** Complete breakdown per Hacienda specs
✅ **Company ID:** Cédula Jurídica displayed
✅ **Authorization:** Legal footer text included

### Email Compliance

✅ **CAN-SPAM Compliant:** Company contact info in footer
✅ **GDPR Considerations:** Emails only sent to customers with invoices
✅ **Opt-out:** Manual control via auto-send toggle

---

## Conclusion

Phase 5 successfully completes the Costa Rica e-invoicing module by implementing:

- ✅ Professional PDF generation with QR codes
- ✅ Automated email delivery system
- ✅ Costa Rica compliance requirements
- ✅ User-friendly UI controls
- ✅ Comprehensive testing suite

The module now provides a complete end-to-end solution from invoice creation through customer delivery, fully compliant with Hacienda requirements.

---

**Document Version:** 1.0
**Last Updated:** 2025-12-28
**Author:** GMS Development Team
**Status:** Production Ready ✅
