# Phase 2: Digital Signature - Quick Reference Guide

## Overview
Phase 2 implements digital signature functionality for Costa Rica e-invoicing using XMLDSig standard.

**Status**: ✅ COMPLETE
**Date**: 2025-12-29

---

## Key Files

### Models
```
l10n_cr_einvoice/models/
├── certificate_manager.py    # Certificate loading & validation
├── xml_signer.py              # XMLDSig signing implementation
├── hacienda_api.py            # API client with retry logic
├── res_company.py             # Certificate storage fields
└── res_config_settings.py     # Configuration UI integration
```

### Views
```
l10n_cr_einvoice/views/
├── res_config_settings_views.xml  # Settings page
├── res_company_views.xml          # Company configuration
└── einvoice_document_views.xml    # Document workflow UI
```

### Tests
```
test_phase2_signature.py      # Comprehensive test suite
```

---

## Quick Configuration

### 1. Upload Certificate

**Navigation**: Settings → Accounting → Costa Rica Electronic Invoicing

**Option A - PKCS#12 (.p12 file)**:
```
Certificate: [Upload certificado.p12]
Key Password: 5147
```

**Option B - PEM Format**:
```
Certificate: [Upload certificate.pem]
Private Key: [Upload private_key.pem]
Key Password: [password if encrypted]
```

### 2. Configure API

```
Hacienda Environment: Sandbox
API Username: cpj-xxx-xxxxxx
API Password: [your password]
```

Click **Test Connection** to verify.

### 3. Set Location

```
Emisor Location: 01010100
(Format: Provincia-Canton-Distrito-Barrio)
```

---

## API Endpoints

### Sandbox
```
https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1
```

### Production
```
https://api.comprobanteselectronicos.go.cr/recepcion/v1
```

---

## Document Workflow

### States
```
draft → generated → signed → submitted → accepted/rejected
```

### Actions
```python
# 1. Generate XML
document.action_generate_xml()

# 2. Sign XML
document.action_sign_xml()

# 3. Submit to Hacienda
document.action_submit_to_hacienda()

# 4. Check status
document.action_check_status()
```

### UI Buttons
- **Generate XML**: Available in `draft` or `error` state
- **Sign XML**: Available in `generated` state
- **Submit to Hacienda**: Available in `signed` state
- **Check Status**: Available in `submitted` state

---

## Certificate Manager API

### Load Certificate
```python
cert_mgr = env['l10n_cr.certificate.manager']
certificate, private_key = cert_mgr.load_certificate_from_company(company)
```

### Get Certificate Info
```python
info = cert_mgr.get_certificate_info(company)
# Returns: {
#   'subject_cn': '...',
#   'issuer_cn': '...',
#   'not_before': '2025-01-01',
#   'not_after': '2026-01-01',
#   'days_until_expiry': 365,
#   'is_valid': True
# }
```

---

## XML Signer API

### Sign XML
```python
xml_signer = env['l10n_cr.xml.signer']
signed_xml = xml_signer.sign_xml(xml_content, certificate, private_key)
```

### Verify Signature
```python
is_valid = xml_signer.verify_signature(signed_xml)
```

---

## Hacienda API Client

### Submit Invoice
```python
api = env['l10n_cr.hacienda.api']
response = api.submit_invoice(
    clave='50601010100010120250001012345678901234567890123456789012345678901',
    xml_content=signed_xml,
    sender_id='3101234567',
    receiver_id='123456789'
)
```

### Check Status
```python
response = api.check_status(clave)
```

### Test Connection
```python
result = api.test_connection()
# Returns: {
#   'success': True/False,
#   'message': '...',
#   'environment': 'sandbox',
#   'url': '...'
# }
```

### Response States
```python
api.is_accepted(response)    # → True if accepted
api.is_rejected(response)    # → True if rejected
api.is_processing(response)  # → True if processing
```

---

## Signature Structure

### XMLDSig Format
```xml
<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
  <SignedInfo>
    <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
    <SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
    <Reference URI="">
      <Transforms>
        <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
      </Transforms>
      <DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
      <DigestValue>BASE64_DIGEST</DigestValue>
    </Reference>
  </SignedInfo>
  <SignatureValue>BASE64_SIGNATURE</SignatureValue>
  <KeyInfo>
    <X509Data>
      <X509Certificate>BASE64_CERTIFICATE</X509Certificate>
    </X509Data>
  </KeyInfo>
</Signature>
```

### Algorithms
- **Canonicalization**: C14N
- **Signature**: RSA-SHA256
- **Digest**: SHA-256
- **Transform**: Enveloped Signature

---

## Testing

### Run Test Suite
```bash
cd /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS
python3 test_phase2_signature.py
```

### Test Coverage
- ✅ Module installation
- ✅ Certificate fields
- ✅ Certificate loading
- ✅ XML signing
- ✅ API connectivity
- ✅ Workflow integration
- ✅ UI views
- ✅ Security access

---

## Common Operations

### Manual Testing Flow
```python
# 1. Create test invoice
invoice = env['account.move'].create({...})
invoice.action_post()

# 2. Create e-invoice document
doc = env['l10n_cr.einvoice.document'].create({
    'move_id': invoice.id,
    'document_type': 'FE',
})

# 3. Generate XML
doc.action_generate_xml()
# State: generated

# 4. Sign XML
doc.action_sign_xml()
# State: signed

# 5. Submit to Hacienda
doc.action_submit_to_hacienda()
# State: submitted

# 6. Check status
doc.action_check_status()
# State: accepted or rejected
```

### Batch Operations
```python
# Sign multiple documents
docs = env['l10n_cr.einvoice.document'].search([
    ('state', '=', 'generated')
])
for doc in docs:
    doc.action_sign_xml()

# Check status for all submitted
docs = env['l10n_cr.einvoice.document'].search([
    ('state', '=', 'submitted')
])
for doc in docs:
    doc.action_check_status()
```

---

## Troubleshooting

### Certificate Won't Load
```
Error: "Failed to load digital certificate"
```
**Solutions**:
1. Verify file format (.p12 or .pem)
2. Check password is correct
3. Ensure certificate matches private key (PEM)
4. Verify file is not corrupted

### Signature Fails
```
Error: "Failed to sign XML document"
```
**Solutions**:
1. Verify certificate loaded successfully
2. Check certificate not expired
3. Ensure XML is well-formed
4. Verify private key is valid

### API Connection Failed
```
Error: "Connection test failed"
```
**Solutions**:
1. Check internet connectivity
2. Verify credentials are correct
3. Ensure environment setting matches credentials
4. Check firewall/proxy settings

### Document Rejected
```
Estado: rechazado
```
**Solutions**:
1. Check `hacienda_response` field for details
2. Verify XML structure (v4.4 spec)
3. Ensure signature is valid
4. Check company VAT is correct
5. Verify customer ID is valid

---

## Security Notes

### Access Control
```
Invoice Users:  Read, Write, Create
Managers:       Full access (including Delete)
Readonly:       Read only
```

### Password Storage
- Certificate passwords stored in plain text in database
- API passwords stored in plain text in database
- **Production**: Use Odoo's encryption or external secret manager

### Certificate Security
- Certificates stored as binary in database
- Private keys stored separately (PEM format)
- No automatic certificate distribution

---

## Performance Notes

### Retry Logic
```
Max attempts: 3
Initial delay: 2 seconds
Backoff: Exponential (2x)
Timeout: 30 seconds per request
```

### Retries On
- 429 (Rate Limit)
- 5xx (Server Errors)
- Timeouts
- Connection Errors

### No Retry On
- 400 (Validation)
- 401 (Authentication)
- 403 (Forbidden)
- 404 (Not Found)

---

## API Response Examples

### Accepted
```json
{
  "clave": "506...",
  "ind-estado": "aceptado",
  "respuesta-xml": "PHJlc3B1ZXN0YT4uLi48L3Jlc3B1ZXN0YT4="
}
```

### Rejected
```json
{
  "clave": "506...",
  "ind-estado": "rechazado",
  "detalle-mensaje": "Firma digital inválida"
}
```

### Processing
```json
{
  "clave": "506...",
  "ind-estado": "procesando"
}
```

---

## Next Phase

**Phase 3**: Enhanced API Integration
- Automatic status polling
- Response message parsing
- Bulk operations
- Admin dashboard
- Cron jobs for monitoring

---

## Resources

### Documentation
- Phase 2 Complete: `/PHASE2-IMPLEMENTATION-COMPLETE.md`
- Epic 001: `/_bmad-output/implementation-artifacts/epics/epic-001-einvoicing.md`

### Test Files
- Test Suite: `/test_phase2_signature.py`

### Code Files
- Certificate Manager: `/l10n_cr_einvoice/models/certificate_manager.py`
- XML Signer: `/l10n_cr_einvoice/models/xml_signer.py`
- Hacienda API: `/l10n_cr_einvoice/models/hacienda_api.py`

### External Links
- [Hacienda Portal](https://www.hacienda.go.cr/contenido/14185-factura-electronica)
- [v4.4 Spec](https://www.hacienda.go.cr/docs/Comprobantes_Electronicos_V4_4.pdf)
- [XMLDSig Standard](https://www.w3.org/TR/xmldsig-core/)

---

**Last Updated**: 2025-12-29
**Status**: Production Ready (Sandbox Tested)
