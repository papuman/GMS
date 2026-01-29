# Phase 2 Digital Signature - Quick Start Guide

## Quick Test Execution

```bash
# 1. Ensure Odoo is running
docker-compose up -d

# 2. Run Phase 2 signature tests
python3 test_einvoice_phase2_signature.py
```

## What Gets Tested (10 Tests)

| # | Test Name | What It Validates |
|---|-----------|-------------------|
| 1 | Certificate File Verification | Certificate exists at path |
| 2 | Certificate Upload | Upload to company config |
| 3 | Certificate Loading | Load from .p12 format |
| 4 | Certificate Validation | Expiry and validity checks |
| 5 | Wrong PIN Handling | Error handling test |
| 6 | Test Invoice Creation | Setup test data |
| 7 | XML Generation | Generate unsigned XML |
| 8 | XML Signing | Apply digital signature |
| 9 | Signature Structure | Verify XMLDSig format |
| 10 | Complete Workflow | End-to-end integration |

## Expected Results

### Success Output
```
================================================================================
  Phase 2 Test Summary
================================================================================

Total Tests:  25
Passed:       25 ✅
Failed:       0 ❌
Pass Rate:    100.0%

🎉 EXCELLENT! Phase 2 digital signature is working correctly.
```

### Generated Files
- `signed_xml_*.xml` - Signed XML documents for inspection
- `phase2_signature_test_results_*.json` - Detailed test results

## Certificate Configuration

### Default Settings (in script)
```python
CERT_PATH = '/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs/Tribu-CR/certificado.p12'
CERT_PIN = '5147'
```

### Using Different Certificate
Edit these variables in the script:
```python
CERT_PATH = '/path/to/your/certificate.p12'
CERT_PIN = 'your_pin'
```

## Quick Troubleshooting

### Certificate Not Found
```bash
# Check certificate exists
ls -lh docs/Tribu-CR/certificado.p12

# If missing, place your .p12 certificate in:
docs/Tribu-CR/certificado.p12
```

### Connection Failed
```bash
# Check Odoo is running
docker-compose ps

# Start if needed
docker-compose up -d

# Check logs
docker-compose logs -f odoo
```

### Wrong PIN Error
```
Error: Invalid password
```
**Fix**: Update `CERT_PIN` in script with correct certificate password

## Signature Verification Checklist

After tests pass, verify signed XML contains:

- [ ] `<ds:Signature>` element present
- [ ] `<ds:SignedInfo>` with RSA-SHA256 algorithm
- [ ] `<ds:SignatureValue>` with Base64 signature
- [ ] `<ds:KeyInfo>` with X.509 certificate
- [ ] `<ds:DigestValue>` with SHA-256 hash
- [ ] Correct XMLDSig namespace

## Manual Inspection

```bash
# View signed XML
cat signed_xml_*.xml

# Check signature element
grep -A 50 "<ds:Signature" signed_xml_*.xml

# Verify certificate embedded
grep "<ds:X509Certificate>" signed_xml_*.xml
```

## Test Results Interpretation

### Certificate Info Display
```
Certificate loaded successfully:
  Subject CN:       [Certificate common name]
  Organization:     [Organization name]
  Issuer:           [Issuer name]
  Valid From:       2024-01-01
  Valid Until:      2025-12-31
  Days Remaining:   365
  Serial Number:    [Serial]
```

### Signature Structure Validation
```
✅ PASS: Signature element exists
✅ PASS: SignedInfo element exists
✅ PASS: CanonicalizationMethod
✅ PASS: SignatureMethod (RSA-SHA256)
✅ PASS: Reference element
✅ PASS: DigestMethod (SHA-256)
✅ PASS: DigestValue (Base64)
✅ PASS: SignatureValue (Base64)
✅ PASS: KeyInfo element exists
✅ PASS: X509Data element
✅ PASS: X509Certificate (Base64)
```

## Next Steps

1. **If All Tests Pass** ✅
   - Review generated signed XML files
   - Proceed to Phase 3: Hacienda API Integration
   - Begin implementation of submission workflow

2. **If Tests Fail** ❌
   - Review failed test details in JSON output
   - Check Odoo logs for error messages
   - Verify certificate validity and format
   - Consult PHASE2-SIGNATURE-TEST-GUIDE.md

## Phase 3 Preview

After Phase 2 completes successfully:
- Hacienda API authentication (OAuth 2.0)
- Document submission endpoint
- Response processing (acceptance/rejection)
- Status tracking and retry logic
- PDF generation with QR code
- Email delivery

## Command Reference

```bash
# Run tests
python3 test_einvoice_phase2_signature.py

# Check syntax
python3 -m py_compile test_einvoice_phase2_signature.py

# View Odoo logs
docker-compose logs -f odoo | grep -i "certificate\|signature"

# List generated files
ls -lh signed_xml_*.xml phase2_signature_test_results_*.json
```

## Support Files

- **test_einvoice_phase2_signature.py** - Main test script
- **PHASE2-SIGNATURE-TEST-GUIDE.md** - Comprehensive documentation
- **PHASE2-QUICK-START.md** - This quick reference
- **certificate_manager.py** - Certificate loading module
- **xml_signer.py** - XML signing module

## Certificate Requirements

Your certificate must:
- Be in .p12 (PKCS#12) or .pfx format
- Contain both certificate and private key
- Be valid (not expired)
- Use RSA algorithm
- Be issued by recognized Costa Rican CA

## Test Execution Flow

```
Start
  ↓
Verify Certificate File
  ↓
Upload to Company Config
  ↓
Load Certificate (.p12)
  ↓
Validate Certificate
  ↓
Test Error Handling
  ↓
Create Test Invoice
  ↓
Generate XML
  ↓
Sign XML
  ↓
Verify Signature Structure
  ↓
Complete Workflow Test
  ↓
Generate Results & Summary
  ↓
End
```

## Success Criteria

For Phase 2 to be considered complete:
- ✅ All 10 test sections pass (≥90% pass rate)
- ✅ Signed XML files generated successfully
- ✅ Signature structure matches XMLDSig standard
- ✅ Certificate properly embedded in KeyInfo
- ✅ RSA-SHA256 signature algorithm used
- ✅ Base64 encoding verified
- ✅ No errors in Odoo logs

---

**Ready to test?** Run: `python3 test_einvoice_phase2_signature.py`
