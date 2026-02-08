# Phase 4 Quick Reference: PDF Generation & Email Delivery

**Module**: l10n_cr_einvoice v19.0.1.5.0
**Last Updated**: 2025-12-29

---

## Quick Commands

### Generate PDF for Single Invoice

```python
# From einvoice document record
document.action_generate_pdf()

# Programmatically
pdf_generator = env['l10n_cr.einvoice.pdf.generator']
pdf_content, filename = pdf_generator.generate_pdf_for_document(document)

# Create attachment
attachment = pdf_generator.create_pdf_attachment(document)
```

### Send Email for Single Invoice

```python
# From einvoice document record (UI button)
document.action_send_email()

# Programmatically
email_sender = env['l10n_cr.einvoice.email.sender']
result = email_sender.send_email_for_document(document)

# Force resend
email_sender.send_email_for_document(document, force_send=True)
```

### Batch Operations

```python
# Generate PDFs for multiple documents
pdf_generator = env['l10n_cr.einvoice.pdf.generator']
stats = pdf_generator.generate_batch_pdfs(documents)
# Returns: {'generated': 10, 'failed': 0}

# Send emails for multiple documents
email_sender = env['l10n_cr.einvoice.email.sender']
stats = email_sender.send_batch_emails(documents)
# Returns: {'sent': 8, 'failed': 1, 'skipped': 1}
```

---

## Configuration

### Enable Auto-Send Email

```python
# Via UI
Settings → Accounting → Costa Rica E-Invoicing
→ Check "Automatically send email when invoice accepted"

# Programmatically
company.l10n_cr_auto_send_email = True
```

### Configure Rate Limit

```python
# Set custom rate limit (default 50/hour)
company.l10n_cr_email_rate_limit = 100  # 100 emails/hour
```

### Add CC Recipients

```python
# Add email CC addresses
company.l10n_cr_einvoice_email_cc = 'admin@company.com,manager@company.com'
```

---

## Testing Commands

### Run All Phase 4 Tests

```bash
# All tests
odoo-bin -c odoo.conf -d test_db -i l10n_cr_einvoice --test-enable \
  --test-tags l10n_cr_einvoice --stop-after-init

# PDF tests only
odoo-bin -c odoo.conf -d test_db --test-enable \
  --test-tags /l10n_cr_einvoice/test_pdf_generation --stop-after-init

# Email tests only
odoo-bin -c odoo.conf -d test_db --test-enable \
  --test-tags /l10n_cr_einvoice/test_email_sending --stop-after-init
```

### Manual Testing

```python
# In Odoo shell (odoo-bin shell -c odoo.conf -d your_db)
env = api.Environment(cr, uid, {})

# Get test document
doc = env['l10n_cr.einvoice.document'].search([
    ('state', '=', 'accepted')
], limit=1)

# Generate PDF
doc.action_generate_pdf()

# Send email
doc.action_send_email()

# Check status
print(f"PDF: {doc.pdf_attachment_id.name}")
print(f"Email sent: {doc.email_sent}")
print(f"Email date: {doc.email_sent_date}")
```

---

## Troubleshooting

### PDF Not Generating

**Problem**: `action_generate_pdf()` fails

**Solutions**:
```python
# Check if document has clave
if not doc.clave:
    print("ERROR: No clave - generate XML first")

# Check if XML exists
if not doc.xml_content and not doc.signed_xml:
    print("ERROR: No XML - generate XML first")

# Check dependencies
try:
    import qrcode
    from PIL import Image
    print("Dependencies OK")
except ImportError as e:
    print(f"Missing dependency: {e}")
    # Install: pip install qrcode[pil]
```

### Email Not Sending

**Problem**: Email not being sent

**Solutions**:
```python
# Check customer email
if not doc.partner_id.email:
    print("ERROR: Customer has no email")
    doc.partner_id.email = 'customer@example.com'

# Check if already sent
if doc.email_sent:
    print("Already sent - use force_send=True to resend")

# Check email error
if doc.email_error:
    print(f"Previous error: {doc.email_error}")
    print(f"Retry count: {doc.email_retry_count}")

# Check rate limit
email_sender = env['l10n_cr.einvoice.email.sender']
if not email_sender._check_rate_limit(doc.company_id):
    print("ERROR: Rate limit exceeded")
```

### Rate Limit Issues

**Problem**: Emails being queued due to rate limit

**Solutions**:
```python
# Check current rate
from datetime import datetime, timedelta
one_hour_ago = datetime.now() - timedelta(hours=1)
recent_count = env['l10n_cr.einvoice.document'].search_count([
    ('company_id', '=', company.id),
    ('email_sent', '=', True),
    ('email_sent_date', '>=', one_hour_ago),
])
print(f"Emails sent in last hour: {recent_count}/50")

# Increase rate limit
company.l10n_cr_email_rate_limit = 100

# Process queued emails
email_sender._cron_process_email_queue()
```

---

## Common Workflows

### Workflow 1: Manual Invoice Process

```python
# 1. Create invoice
invoice = env['account.move'].create({
    'move_type': 'out_invoice',
    'partner_id': partner.id,
    'invoice_line_ids': [(0, 0, {
        'name': 'Product',
        'quantity': 1,
        'price_unit': 100.0,
    })],
})

# 2. Create e-invoice document
doc = env['l10n_cr.einvoice.document'].create({
    'move_id': invoice.id,
    'company_id': company.id,
    'document_type': 'FE',
})

# 3. Generate XML
doc.action_generate_xml()

# 4. Sign XML
doc.action_sign_xml()

# 5. Submit to Hacienda
doc.action_submit_to_hacienda()

# 6. Wait for acceptance (or check manually)
doc.action_check_status()

# 7. Generate PDF (done automatically on acceptance if auto-send enabled)
doc.action_generate_pdf()

# 8. Send email (done automatically if auto-send enabled)
doc.action_send_email()
```

### Workflow 2: Batch Process Pending Invoices

```python
# Get all accepted documents without email
docs = env['l10n_cr.einvoice.document'].search([
    ('state', '=', 'accepted'),
    ('email_sent', '=', False),
    ('partner_id.email', '!=', False),
])

print(f"Found {len(docs)} documents to process")

# Generate PDFs
pdf_generator = env['l10n_cr.einvoice.pdf.generator']
pdf_stats = pdf_generator.generate_batch_pdfs(docs)
print(f"PDFs: {pdf_stats['generated']} generated, {pdf_stats['failed']} failed")

# Send emails
email_sender = env['l10n_cr.einvoice.email.sender']
email_stats = email_sender.send_batch_emails(docs)
print(f"Emails: {email_stats['sent']} sent, {email_stats['skipped']} skipped, {email_stats['failed']} failed")
```

### Workflow 3: Retry Failed Emails

```python
# Get failed emails
failed_docs = env['l10n_cr.einvoice.document'].search([
    ('state', '=', 'accepted'),
    ('email_sent', '=', False),
    ('email_error', '!=', False),
    ('email_retry_count', '<', 3),
])

print(f"Found {len(failed_docs)} failed emails to retry")

# Retry each
email_sender = env['l10n_cr.einvoice.email.sender']
for doc in failed_docs:
    print(f"Retrying {doc.name}...")
    result = email_sender.send_email_for_document(doc, force_send=False)
    if result:
        print(f"  SUCCESS")
    else:
        print(f"  FAILED: {doc.email_error}")
```

---

## API Reference

### PDF Generator Methods

```python
pdf_generator = env['l10n_cr.einvoice.pdf.generator']

# Generate PDF (returns bytes and filename)
pdf_content, filename = pdf_generator.generate_pdf_for_document(document)

# Create attachment (returns ir.attachment)
attachment = pdf_generator.create_pdf_attachment(document)

# Get QR code data (returns dict)
qr_data = pdf_generator.get_qr_code_data(document)
# → {'qr_image': 'base64...', 'verification_url': 'https://...'}

# Batch generation (returns stats dict)
stats = pdf_generator.generate_batch_pdfs(documents)
# → {'generated': 10, 'failed': 0}
```

### Email Sender Methods

```python
email_sender = env['l10n_cr.einvoice.email.sender']

# Send email (returns bool)
result = email_sender.send_email_for_document(document, template_ref=None, force_send=False)

# Batch send (returns stats dict)
stats = email_sender.send_batch_emails(documents, template_ref=None)
# → {'sent': 8, 'failed': 1, 'skipped': 1}

# Auto-send on acceptance (returns bool)
result = email_sender.auto_send_on_acceptance(document)

# Process retry queue (cron job)
email_sender._cron_process_email_queue()
```

### Document Action Methods

```python
# PDF actions
document.action_generate_pdf()      # Generate PDF
document.action_regenerate_pdf()    # Regenerate PDF
document.action_download_pdf()      # Download PDF (UI)

# Email actions
document.action_send_email()        # Send email
document.action_send_email_manual() # Send with confirmation
document.action_preview_email()     # Preview email
```

---

## Field Reference

### PDF Fields

```python
document.pdf_attachment_id    # Many2one to ir.attachment
document.pdf_file             # Binary (alternative storage)
document.pdf_filename         # Char (computed)
```

### Email Fields

```python
document.email_sent           # Boolean
document.email_sent_date      # Datetime
document.email_error          # Text (error message)
document.email_retry_count    # Integer (0-3)
```

---

## Email Template Reference

### Available Templates

```python
# Get template
template = env.ref('l10n_cr_einvoice.email_template_invoice_accepted')

# Template IDs
templates = {
    'accepted': 'l10n_cr_einvoice.email_template_invoice_accepted',
    'rejected': 'l10n_cr_einvoice.email_template_invoice_rejected',
    'pending': 'l10n_cr_einvoice.email_template_invoice_pending',
    'credit_note': 'l10n_cr_einvoice.email_template_credit_note_notification',
    'debit_note': 'l10n_cr_einvoice.email_template_debit_note_notification',
}

# Send with specific template
template = env.ref(templates['accepted'])
template.send_mail(document.id, force_send=True)
```

### Customize Templates

```python
# Find template
template = env.ref('l10n_cr_einvoice.email_template_invoice_accepted')

# Update subject
template.subject = 'New Subject ${object.name}'

# Update body
template.body_html = '''<p>Your custom HTML</p>'''

# Add attachment
template.report_template = env.ref('l10n_cr_einvoice.action_report_einvoice')
```

---

## Cron Jobs

### Email Retry Queue Processor

```python
# Cron configuration
Name: Process E-Invoice Email Retry Queue
Interval: 15 minutes
User: Administrator
Model: l10n_cr.einvoice.email.sender
Function: _cron_process_email_queue

# Run manually
env['l10n_cr.einvoice.email.sender']._cron_process_email_queue()
```

### Document Status Poller (Phase 3)

```python
# Also triggers auto-send email
env['l10n_cr.einvoice.document']._cron_poll_pending_documents()
```

---

## Monitoring & Logging

### Check Email Statistics

```python
from datetime import datetime, timedelta

# Today's stats
today_start = datetime.now().replace(hour=0, minute=0, second=0)
today_docs = env['l10n_cr.einvoice.document'].search([
    ('create_date', '>=', today_start),
])

sent_count = len(today_docs.filtered(lambda d: d.email_sent))
failed_count = len(today_docs.filtered(lambda d: d.email_error))

print(f"Today: {sent_count} sent, {failed_count} failed")

# Rate limit check
one_hour_ago = datetime.now() - timedelta(hours=1)
recent_emails = env['l10n_cr.einvoice.document'].search_count([
    ('company_id', '=', company.id),
    ('email_sent', '=', True),
    ('email_sent_date', '>=', one_hour_ago),
])
print(f"Last hour: {recent_emails}/50 emails")
```

### Check PDF Generation Stats

```python
# Documents with PDFs
with_pdf = env['l10n_cr.einvoice.document'].search_count([
    ('pdf_attachment_id', '!=', False),
])

without_pdf = env['l10n_cr.einvoice.document'].search_count([
    ('state', 'in', ['accepted', 'rejected']),
    ('pdf_attachment_id', '=', False),
])

print(f"With PDF: {with_pdf}")
print(f"Without PDF: {without_pdf}")
```

---

## Performance Tips

### Batch Operations

```python
# Good: Batch generation
pdf_generator.generate_batch_pdfs(documents)  # Efficient

# Bad: Loop generation
for doc in documents:
    doc.action_generate_pdf()  # Inefficient (multiple commits)
```

### Rate Limit Management

```python
# Schedule batch sends during off-peak hours
# Use cron to process queue automatically
# Increase rate limit if needed

# Check if near limit before large batch
email_sender = env['l10n_cr.einvoice.email.sender']
if email_sender._check_rate_limit(company):
    # OK to send
    email_sender.send_batch_emails(documents)
else:
    # Wait or increase limit
    print("Near rate limit - wait 1 hour")
```

---

## Security Checklist

- [ ] SMTP server configured securely (TLS/SSL)
- [ ] Email templates don't expose sensitive data
- [ ] Customer opt-out mechanism enabled
- [ ] PDF attachments have proper access control
- [ ] QR codes only contain verification data
- [ ] Rate limiting configured appropriately
- [ ] Unsubscribe link working (GDPR)

---

## Quick Debugging

```python
# Enable debug logging
import logging
logging.getLogger('odoo.addons.l10n_cr_einvoice').setLevel(logging.DEBUG)

# Check last error
doc = env['l10n_cr.einvoice.document'].browse(DOC_ID)
print(f"State: {doc.state}")
print(f"PDF: {doc.pdf_attachment_id.name if doc.pdf_attachment_id else 'None'}")
print(f"Email sent: {doc.email_sent}")
print(f"Email error: {doc.email_error}")
print(f"Retry count: {doc.email_retry_count}")
```

---

## File Locations

```
l10n_cr_einvoice/
├── models/
│   ├── einvoice_email_sender.py           # Email service
│   └── einvoice_document_phase4_additions.py  # Phase 4 fields
├── reports/
│   ├── einvoice_pdf_generator.py          # PDF generator
│   └── einvoice_report_templates.xml      # PDF templates
├── data/
│   └── email_templates.xml                # Email templates
└── tests/
    ├── test_pdf_generation.py             # PDF tests
    └── test_email_sending.py              # Email tests
```

---

**End of Quick Reference**
**Version**: 1.0.0
**Last Updated**: 2025-12-29
