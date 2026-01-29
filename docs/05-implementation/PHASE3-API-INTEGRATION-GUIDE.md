# Phase 3 API Integration - Quick Reference

## Quick Start

### 1. Configure Hacienda Credentials

```python
# Settings > Companies > Costa Rica E-Invoice Settings
company.l10n_cr_hacienda_env = 'sandbox'  # or 'production'
company.l10n_cr_hacienda_username = 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr'
company.l10n_cr_hacienda_password = 'your-password'
```

### 2. Test Connection

```python
api = env['l10n_cr.hacienda.api']
result = api.test_connection()
print(result)  # {'success': True, 'message': '...'}
```

### 3. Submit Invoice (Full Workflow)

```python
# Assuming you have an invoice
invoice = env['account.move'].browse(invoice_id)

# Step 1: Create e-invoice document
doc = env['l10n_cr.einvoice.document'].create({
    'move_id': invoice.id,
    'document_type': 'FE',
})

# Step 2: Generate XML
doc.action_generate_xml()

# Step 3: Sign XML
doc.action_sign_xml()

# Step 4: Submit to Hacienda (NEW - Phase 3)
doc.action_submit_to_hacienda()

# Step 5: Check status if needed
if doc.state == 'submitted':
    doc.action_check_status()
```

## API Methods Cheat Sheet

### Submit Invoice
```python
api = env['l10n_cr.hacienda.api']
response = api.submit_invoice(
    clave='50-digit-key',
    xml_content=signed_xml_string,
    sender_id='3101234567',
    receiver_id='123456789'
)
```

### Check Status
```python
response = api.check_status(clave='50-digit-key')
```

### Get Acceptance Message
```python
msg = api.get_acceptance_message(clave='50-digit-key')
print(msg['mensaje'])  # Decoded message
```

### Status Helpers
```python
if api.is_accepted(response):
    print("Accepted!")
elif api.is_rejected(response):
    print("Rejected!")
elif api.is_processing(response):
    print("Still processing...")
```

## Response Structure

### Successful Response
```python
{
    'ind-estado': 'aceptado',  # or 'rechazado', 'procesando'
    'clave': '50618010600001010001431130000100001000000001',
    'fecha': '2024-01-15T10:30:00-06:00',
    'respuesta-xml': 'base64-encoded-response',
    'respuesta-xml-decoded': 'decoded-xml-response'
}
```

### Error Response
```python
{
    'ind-estado': 'error',
    'error_details': 'Error description',
    'respuesta-xml': 'error message'
}
```

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| Authentication failed | Invalid credentials | Check username/password in company settings |
| Validation error | Invalid XML/payload | Review XML generation and signature |
| Connection error | Network issues | Check internet, will auto-retry |
| Rate limit exceeded | Too many requests | Reduce frequency, will auto-retry |
| Document not found | Invalid clave | Verify clave is correct and document exists |

## Configuration Constants

```python
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 2  # seconds
RETRY_BACKOFF_FACTOR = 2

# Retry timeline:
# Attempt 1: Immediate
# Attempt 2: +2 seconds
# Attempt 3: +4 seconds
# Total max: ~6 seconds (if all retries needed)
```

## Identification Types

| Length | Prefix | Type | Code | Description |
|--------|--------|------|------|-------------|
| 9 | Any | Física | 01 | Cédula Física |
| 10 | 3xxx | Jurídica | 02 | Cédula Jurídica |
| 10 | Other | NITE | 04 | NITE |
| 11-12 | Any | DIMEX | 03 | DIMEX |
| Other | Any | Extranjero | 05 | Foreign ID |

## Document States Flow

```
draft → generated → signed → submitted → accepted
                                    ↓
                                rejected
```

## Testing

### Run Phase 3 Tests
```bash
python3 test_phase3_api.py
```

### Manual Testing in Odoo Shell
```python
# Start shell
./odoo-bin shell -d gms_validation

# Get API client
api = env['l10n_cr.hacienda.api']

# Test connection
api.test_connection()

# Find a signed document
doc = env['l10n_cr.einvoice.document'].search([('state', '=', 'signed')], limit=1)

# Submit it
doc.action_submit_to_hacienda()

# Check its state
print(doc.state)
print(doc.hacienda_message)
```

## Logging

Enable debug logging to see detailed API interactions:

```python
import logging
logging.getLogger('odoo.addons.l10n_cr_einvoice.models.hacienda_api').setLevel(logging.DEBUG)
```

Log levels:
- `INFO` - Normal operations
- `DEBUG` - Request/response details
- `WARNING` - Retries, rate limits
- `ERROR` - Permanent failures

## Environment URLs

### Sandbox (Testing)
```
URL: https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1
Credentials: cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr / e8KLJRHzRA1P0W2ybJ5T
```

### Production
```
URL: https://api.comprobanteselectronicos.go.cr/recepcion/v1
Credentials: Your production credentials
```

## Performance Tips

1. **Async Processing**: For bulk submissions, use scheduled actions
2. **Status Polling**: Don't check status immediately, wait 5-10 seconds
3. **Retry Awareness**: Account for retry delays in workflow timing
4. **Batch Operations**: Group submissions with delays to avoid rate limits

## Security Notes

- Credentials transmitted via HTTPS only
- XML base64 encoded before transmission
- No credentials logged
- Error messages truncated to prevent data leakage

## Code Examples

### Example 1: Programmatic Submission
```python
def submit_invoice_to_hacienda(invoice_id):
    """Submit an invoice to Hacienda."""
    invoice = env['account.move'].browse(invoice_id)

    # Get or create e-invoice document
    doc = env['l10n_cr.einvoice.document'].search([
        ('move_id', '=', invoice.id)
    ], limit=1)

    if not doc:
        doc = env['l10n_cr.einvoice.document'].create({
            'move_id': invoice.id,
            'document_type': 'FE',
        })

    # Generate and sign if needed
    if doc.state == 'draft':
        doc.action_generate_xml()
    if doc.state == 'generated':
        doc.action_sign_xml()

    # Submit
    if doc.state == 'signed':
        doc.action_submit_to_hacienda()

    return doc.state
```

### Example 2: Bulk Status Check
```python
def check_all_submitted_documents():
    """Check status of all submitted documents."""
    docs = env['l10n_cr.einvoice.document'].search([
        ('state', '=', 'submitted')
    ])

    for doc in docs:
        try:
            doc.action_check_status()
            print(f"Document {doc.name}: {doc.state}")
        except Exception as e:
            print(f"Error checking {doc.name}: {str(e)}")
```

### Example 3: Error Handling
```python
def safe_submit(doc_id):
    """Submit with error handling."""
    doc = env['l10n_cr.einvoice.document'].browse(doc_id)

    try:
        doc.action_submit_to_hacienda()
        return {'success': True, 'state': doc.state}
    except UserError as e:
        # Handle specific errors
        if 'Authentication failed' in str(e):
            return {'success': False, 'error': 'credentials'}
        elif 'Validation error' in str(e):
            return {'success': False, 'error': 'validation'}
        else:
            return {'success': False, 'error': str(e)}
```

## API Endpoints

### Submit Document
```
POST /recepcion/v1/recepcion
Body: {clave, fecha, emisor, receptor, comprobanteXml}
```

### Check Status
```
GET /recepcion/v1/recepcion/{clave}
```

## Next Steps After Phase 3

1. ✅ Phase 1: XML Generation
2. ✅ Phase 2: Digital Signatures
3. ✅ Phase 3: API Integration
4. 🚧 Phase 4: Email & PDF with QR
5. 🚧 Phase 5: Automatic workflows
6. 🚧 Phase 6: Reports & analytics

## Support Resources

- Documentation: `/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/PHASE3_API_INTEGRATION.md`
- Test Script: `/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/test_phase3_api.py`
- API Code: `/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/models/hacienda_api.py`

## Troubleshooting Commands

```python
# Check API configuration
company = env.company
print(f"Environment: {company.l10n_cr_hacienda_env}")
print(f"Username: {company.l10n_cr_hacienda_username}")
print(f"Password set: {bool(company.l10n_cr_hacienda_password)}")

# Test connection
api = env['l10n_cr.hacienda.api']
result = api.test_connection()
print(result)

# Check document state
doc = env['l10n_cr.einvoice.document'].browse(doc_id)
print(f"State: {doc.state}")
print(f"Clave: {doc.clave}")
print(f"Error: {doc.error_message}")
print(f"Response: {doc.hacienda_response}")

# Retry submission
if doc.state in ['error', 'signed']:
    doc.action_submit_to_hacienda()
```
