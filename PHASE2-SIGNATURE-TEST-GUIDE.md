# Phase 2 Digital Signature Test Guide

## Overview

The `test_einvoice_phase2_signature.py` script provides comprehensive testing of the digital signature functionality implemented in Phase 2 of the Costa Rica e-invoice module.

## What This Test Validates

### Core Components Tested
1. **Certificate Manager** (`certificate_manager.py`)
   - Loading X.509 certificates from .p12 (PKCS#12) format
   - Certificate validation (expiry dates, validity period)
   - Error handling for invalid certificates and wrong PINs

2. **XML Signer** (`xml_signer.py`)
   - XML digital signature generation using XMLDSig standard
   - RSA-SHA256 signature algorithm
   - Enveloped signature pattern (as required by Hacienda)

3. **Signature Structure Verification**
   - SignedInfo element with canonicalization method
   - SignatureValue with Base64 encoding
   - KeyInfo with embedded X.509 certificate
   - Reference and digest calculations

## Test Coverage

### Test Suite (10 Comprehensive Tests)

1. **Certificate File Verification**
   - Verifies certificate file exists at specified path
   - Checks file size and accessibility

2. **Certificate Upload to Company**
   - Uploads certificate to Odoo company configuration
   - Stores certificate data, filename, and PIN
   - Tests Base64 encoding of certificate file

3. **Certificate Loading (.p12)**
   - Loads certificate using certificate manager
   - Extracts certificate metadata (subject, issuer, validity dates)
   - Verifies private key extraction

4. **Certificate Validation**
   - Checks certificate validity period
   - Verifies not expired and not yet valid
   - Calculates days until expiry
   - Warns if expiring soon (<30 days)

5. **Error Handling - Wrong PIN**
   - Tests certificate loading with incorrect PIN
   - Verifies proper error handling and exception raising
   - Restores correct PIN after test

6. **Create Test Invoice for Signing**
   - Creates customer, product, and invoice
   - Posts invoice and generates e-invoice document
   - Prepares data for signing workflow

7. **XML Generation (Pre-Signing)**
   - Generates unsigned XML from invoice data
   - Validates XML structure and content
   - Saves XML for comparison

8. **XML Digital Signature**
   - Signs XML with loaded certificate
   - Uses RSA-SHA256 algorithm
   - Embeds signature in XML document
   - Saves signed XML for inspection

9. **Signature Structure Verification**
   - Validates XMLDSig namespace and structure
   - Checks SignedInfo (canonicalization, signature method, reference)
   - Validates SignatureValue Base64 encoding
   - Verifies KeyInfo and X509Certificate embedding
   - Confirms digest method (SHA-256)

10. **Complete Workflow Integration**
    - End-to-end test: Create → Generate → Sign → Verify
    - Validates entire signature pipeline
    - Confirms all components work together

## Usage

### Prerequisites

```bash
# Ensure Odoo is running
docker-compose up -d

# Verify certificate file exists
ls -lh /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs/Tribu-CR/certificado.p12
```

### Running the Tests

```bash
# Run the test script
python3 test_einvoice_phase2_signature.py
```

### Expected Output

The test will produce:
1. **Console output** with detailed test results
2. **Signed XML files** saved as `signed_xml_*.xml`
3. **JSON results file** with complete test data

## Configuration

Edit the script header if needed:

```python
# Odoo connection
ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

# Certificate configuration
CERT_PATH = '/path/to/certificado.p12'
CERT_PIN = '5147'
```

## Understanding Test Results

### Pass Rate Interpretation

- **≥90%**: Excellent! Digital signature implementation is working correctly
- **70-89%**: Good. Most functionality works, review failed tests
- **<70%**: Attention needed. Multiple components need fixes

### Common Issues

#### Certificate Not Found
```
❌ FAIL: Certificate file exists
    Certificate not found at: /path/to/certificado.p12
```
**Solution**: Verify certificate path is correct

#### Wrong PIN Error
```
❌ FAIL: Load certificate from .p12
    Error: Invalid password
```
**Solution**: Verify CERT_PIN matches certificate password

#### Missing Signature Elements
```
❌ FAIL: SignedInfo element exists
    Missing
```
**Solution**: Check xml_signer.py implementation

#### Invalid Base64 Encoding
```
❌ FAIL: SignatureValue (Base64)
    Invalid Base64 encoding
```
**Solution**: Review Base64 encoding in signature generation

## Output Files

### Signed XML Files
Location: `signed_xml_*.xml`

These files contain the complete signed XML that will be sent to Hacienda. Inspect to verify:
- XML structure matches Hacienda v4.4 spec
- Signature element is present and properly formatted
- All required elements are included

### Test Results JSON
Location: `phase2_signature_test_results_YYYYMMDD_HHMMSS.json`

Contains:
```json
{
  "total": 25,
  "passed": 23,
  "failed": 2,
  "tests": [
    {
      "name": "Test name",
      "passed": true,
      "details": "Test details"
    }
  ]
}
```

## Signature Structure Validation

The test verifies the XML signature follows this structure:

```xml
<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <ds:SignedInfo>
    <ds:CanonicalizationMethod Algorithm="..."/>
    <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
    <ds:Reference URI="">
      <ds:Transforms>
        <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
      </ds:Transforms>
      <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
      <ds:DigestValue>...</ds:DigestValue>
    </ds:Reference>
  </ds:SignedInfo>
  <ds:SignatureValue>...</ds:SignatureValue>
  <ds:KeyInfo>
    <ds:X509Data>
      <ds:X509Certificate>...</ds:X509Certificate>
    </ds:X509Data>
  </ds:KeyInfo>
</ds:Signature>
```

## Hacienda Requirements Checklist

The signature implementation must meet these Hacienda requirements:

- ✅ **Algorithm**: RSA-SHA256 for signature
- ✅ **Digest**: SHA-256 for hash calculation
- ✅ **Certificate**: X.509 embedded in KeyInfo
- ✅ **Pattern**: Enveloped signature (signature inside document)
- ✅ **Namespace**: XMLDSig namespace correctly used
- ✅ **Encoding**: Base64 for all binary data

## Troubleshooting

### Test Failures

#### Certificate Loading Fails
1. Check certificate file exists and is readable
2. Verify PIN is correct
3. Ensure certificate is valid (not expired)
4. Check certificate format (.p12 or .pfx)

#### Signature Generation Fails
1. Verify certificate was loaded successfully
2. Check private key was extracted from certificate
3. Review logs for specific error messages
4. Ensure lxml and cryptography libraries are installed

#### Structure Verification Fails
1. Inspect generated signed XML file
2. Compare against XMLDSig specification
3. Check namespace declarations
4. Verify element hierarchy

### Debug Mode

Enable detailed logging by checking Odoo logs:

```bash
# View Odoo logs
docker-compose logs -f odoo
```

Look for messages from:
- `l10n_cr.certificate.manager`
- `l10n_cr.xml.signer`

## Next Steps After Successful Tests

Once all tests pass:

1. **Review Signed XML**: Open generated `signed_xml_*.xml` files
2. **Validate Structure**: Ensure signature matches Hacienda requirements
3. **Manual Verification**: Use online XML signature validators
4. **Prepare for Phase 3**: Hacienda API integration and submission

## Phase 3 Preview

After Phase 2 signature tests pass, Phase 3 will implement:
- Hacienda API client (authentication, submission)
- Response processing (acceptance, rejection handling)
- Document status tracking
- Retry logic for failed submissions

## Support

If tests fail consistently:
1. Review certificate validity and format
2. Check Odoo module installation
3. Verify database configuration
4. Review implementation against Hacienda technical documentation v4.4

## References

- **Hacienda Technical Spec**: v4.4 Electronic Invoice Specification
- **XMLDSig Standard**: W3C XML Signature Syntax and Processing
- **X.509 Certificates**: RFC 5280
- **PKCS#12 Format**: RFC 7292
