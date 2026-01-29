# Phase 5 Quick Reference Guide

## PDF Generation and Email Delivery - Quick Start

---

## Installation

### 1. Install Python Dependency

```bash
pip install qrcode[pil]
```

### 2. Update Odoo Module

```bash
odoo-bin -u l10n_cr_einvoice -d your_database
```

### 3. Restart Odoo

```bash
# Restart your Odoo service
```

---

## Configuration

### Enable Auto-send Email

**UI Path:** Settings → Companies → [Your Company] → E-Invoicing

**Field:** Auto-send Email ☑

**Code:**
```python
company.l10n_cr_auto_send_email = True
```

---

## Usage

### Automatic Workflow (Recommended)

1. Create and post invoice
2. E-invoice automatically generated
3. Submitted to Hacienda
4. When accepted:
   - PDF auto-generated
   - Email auto-sent to customer
   - Done! ✅

### Manual Workflow

1. Create and post invoice
2. Generate XML → Sign → Submit
3. Wait for acceptance
4. Click **"Generate PDF"** button
5. Click **"Send Email"** button
6. Done! ✅

---

## Key Buttons

### Form View Header

| Button | When Visible | Action |
|--------|--------------|--------|
| Generate PDF | XML exists, no PDF | Creates PDF with QR code |
| Send Email | Accepted, not sent | Emails customer with PDF |

### Smart Buttons

| Button | Icon | Action |
|--------|------|--------|
| Download PDF | 📄 | Downloads PDF file |
| Download XML | 📥 | Downloads XML file |

---

## Code Examples

### Generate PDF

```python
doc = env['l10n_cr.einvoice.document'].browse(doc_id)
doc.action_generate_pdf()
```

### Send Email

```python
doc.action_send_email()
```

### Generate QR Code

```python
qr_gen = env['l10n_cr.qr.generator']
qr_code = qr_gen.generate_qr_code(clave)
```

### Check Status

```python
if doc.email_sent:
    print(f"Email sent on: {doc.email_sent_date}")
if doc.pdf_attachment_id:
    print(f"PDF: {doc.pdf_attachment_id.name}")
```

---

## Testing

### Run Test Suite

```bash
odoo-bin shell -c odoo.conf -d your_database
```

```python
>>> exec(open('test_phase5_pdf_email.py').read())
```

### Manual Test

1. Find accepted invoice:
   ```python
   doc = env['l10n_cr.einvoice.document'].search([
       ('state', '=', 'accepted')
   ], limit=1)
   ```

2. Test QR generation:
   ```python
   qr = doc._get_qr_code_image()
   print(f"QR Generated: {bool(qr)}")
   ```

3. Test PDF:
   ```python
   doc.action_generate_pdf()
   print(f"PDF: {doc.pdf_attachment_id.name}")
   ```

4. Test email (dry run):
   ```python
   print(f"Customer: {doc.partner_id.name}")
   print(f"Email: {doc.partner_id.email}")
   print(f"Can send: {doc.state == 'accepted' and doc.partner_id.email}")
   ```

---

## Troubleshooting

### QR Library Error

**Error:** "QR code library is not installed"

**Fix:**
```bash
pip install qrcode[pil]
```

### No Email Sent

**Check:**
1. Auto-send enabled? `company.l10n_cr_auto_send_email`
2. Document accepted? `doc.state == 'accepted'`
3. Customer has email? `doc.partner_id.email`
4. Not already sent? `doc.email_sent == False`

### PDF Missing QR

**Debug:**
```python
qr = doc._get_qr_code_image()
if not qr:
    print("QR generation failed")
    print(f"Clave: {doc.clave}")
```

---

## File Locations

### Code Files

```
l10n_cr_einvoice/
├── models/qr_generator.py           # QR generation
├── models/einvoice_document.py      # PDF/email methods
├── reports/einvoice_report_templates.xml  # PDF template
├── data/email_templates.xml         # Email templates
└── views/einvoice_document_views.xml      # UI buttons
```

### Documentation

```
l10n_cr_einvoice/docs/
└── PHASE5_PDF_EMAIL_IMPLEMENTATION.md  # Full documentation
```

### Tests

```
test_phase5_pdf_email.py             # Test script
```

---

## Key Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `action_generate_pdf()` | Generate PDF report | Notification |
| `action_download_pdf()` | Download PDF | URL action |
| `action_send_email()` | Send email | Notification |
| `_get_qr_code_image()` | Get QR for template | Base64 PNG |
| `_auto_send_email_on_acceptance()` | Auto-send logic | None |

---

## Templates

### Email Template IDs

- `email_template_einvoice` - For FE, NC, ND
- `email_template_eticket` - For TE

### Report Template ID

- `action_report_einvoice` - PDF report

### Access

```python
# Email template
template = env.ref('l10n_cr_einvoice.email_template_einvoice')

# PDF report
report = env.ref('l10n_cr_einvoice.action_report_einvoice')
```

---

## Customization

### Override Email Template

```xml
<record id="email_template_einvoice" model="mail.template">
    <field name="body_html">
        <!-- Your custom HTML -->
    </field>
</record>
```

### Customize PDF

```xml
<template id="custom_pdf" inherit_id="l10n_cr_einvoice.report_einvoice_document">
    <xpath expr="//div[@class='page']" position="inside">
        <!-- Your additions -->
    </xpath>
</template>
```

---

## Costa Rica Requirements

### QR Code
- ✅ Links to Hacienda validation
- ✅ Contains 50-digit clave
- ✅ 150x150px minimum

### PDF Content
- ✅ "DOCUMENTO ELECTRÓNICO"
- ✅ Clave displayed
- ✅ Tax breakdown
- ✅ Legal footer

### Email
- ✅ Professional format
- ✅ PDF attached
- ✅ Company info

---

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| QR Generation | ~50ms | Cached in PDF |
| PDF Generation | ~300ms | One-time |
| Email Sending | ~150ms | Async possible |
| Total Auto-send | ~500ms | After acceptance |

---

## Support

### Log Locations

```bash
# Check Odoo logs for:
# - QR generation: "Generated QR code for clave..."
# - PDF creation: "Generated PDF for document..."
# - Email sent: "Sent email for document..."
# - Auto-send: "Auto-sent email for document..."
```

### Debug Mode

```python
import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
```

---

## Checklist

### Pre-Production
- [ ] Install qrcode library
- [ ] Update module
- [ ] Configure SMTP
- [ ] Set auto-send preference
- [ ] Test with sample invoice

### Go-Live
- [ ] Monitor first auto-sends
- [ ] Check customer emails received
- [ ] Verify PDFs display correctly
- [ ] Confirm QR codes scan

---

**Quick Reference Version:** 1.0
**Last Updated:** 2025-12-28
