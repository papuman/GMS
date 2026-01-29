# Phase 2 Digital Signature - Execution Checklist

## Pre-Execution Checklist

### Environment Preparation
- [ ] Odoo container is running (`docker-compose ps`)
- [ ] Database `gms_validation` exists and is accessible
- [ ] l10n_cr_einvoice module is installed and up to date
- [ ] No pending Odoo errors in logs

### Certificate Preparation
- [ ] Certificate file exists at path
- [ ] Certificate is in .p12 (PKCS#12) format
- [ ] Certificate PIN/password is known
- [ ] Certificate is not expired
- [ ] Certificate contains both public and private key

### Verification Commands
```bash
# Check Odoo is running
docker-compose ps

# Verify certificate file
ls -lh /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs/Tribu-CR/certificado.p12

# Check Odoo logs (optional)
docker-compose logs -f odoo
```

---

## Test Execution Checklist

### Step 1: Run Test Script
```bash
python3 test_einvoice_phase2_signature.py
```

- [ ] Script starts without Python syntax errors
- [ ] Connection to Odoo successful
- [ ] Authentication successful (UID displayed)

### Step 2: Monitor Test Progress

Watch for these test sections:
- [ ] Test 1: Certificate File Verification - PASS
- [ ] Test 2: Certificate Upload to Company - PASS
- [ ] Test 3: Certificate Loading (.p12) - PASS
- [ ] Test 4: Certificate Validation - PASS
- [ ] Test 5: Error Handling - Wrong PIN - PASS
- [ ] Test 6: Create Test Invoice for Signing - PASS
- [ ] Test 7: XML Generation (Pre-Signing) - PASS
- [ ] Test 8: XML Digital Signature - PASS
- [ ] Test 9: Signature Structure Verification - PASS
- [ ] Test 10: Complete Workflow Integration - PASS

### Step 3: Review Test Summary

Expected summary output:
- [ ] Total tests executed: 25+
- [ ] Pass rate: ≥90%
- [ ] No critical failures
- [ ] Certificate info displayed correctly
- [ ] Signed XML files generated

---

## Post-Execution Checklist

### Generated Files Verification
- [ ] `signed_xml_*.xml` files created
- [ ] `phase2_signature_test_results_*.json` created
- [ ] Files are readable and contain data

### Signed XML Inspection
```bash
# List generated files
ls -lh signed_xml_*.xml

# View signed XML
cat signed_xml_*.xml

# Check signature element
grep -A 5 "<ds:Signature" signed_xml_*.xml
```

- [ ] File contains `<ds:Signature>` element
- [ ] Signature has correct namespace
- [ ] SignedInfo, SignatureValue, and KeyInfo present
- [ ] Base64 data appears valid (no obvious errors)

### Certificate Information Review
Check console output shows:
- [ ] Subject CN (Common Name)
- [ ] Organization name
- [ ] Issuer information
- [ ] Valid from date
- [ ] Valid until date
- [ ] Days remaining (>0 if valid)
- [ ] Serial number

### Signature Structure Verification
Console should show all these as PASS:
- [ ] Signature element exists
- [ ] SignedInfo element exists
- [ ] CanonicalizationMethod present
- [ ] SignatureMethod (RSA-SHA256)
- [ ] Reference element
- [ ] DigestMethod (SHA-256)
- [ ] DigestValue (Base64)
- [ ] SignatureValue (Base64)
- [ ] KeyInfo element exists
- [ ] X509Data element
- [ ] X509Certificate (Base64)

---

## Results Analysis Checklist

### Pass Criteria (≥90% pass rate)
- [ ] Certificate loads successfully
- [ ] Certificate validates (not expired)
- [ ] XML signs without errors
- [ ] Signature structure is correct
- [ ] All Base64 encoding valid
- [ ] XMLDSig namespace correct
- [ ] Certificate embedded in signature

### Review JSON Results
```bash
# View results file
cat phase2_signature_test_results_*.json | python3 -m json.tool
```

- [ ] All test entries present
- [ ] Pass/fail status recorded
- [ ] Details provided for failures (if any)

---

## Troubleshooting Checklist

### If Certificate Tests Fail

#### Certificate Not Found
- [ ] Verify path is correct
- [ ] Check file exists: `ls -lh <cert_path>`
- [ ] Ensure read permissions
- [ ] Try absolute path in script

#### Wrong PIN Error
- [ ] Verify PIN in script matches certificate
- [ ] Check for typos in PIN
- [ ] Remove quotes around PIN if present
- [ ] Try PIN from certificate provider

#### Certificate Expired
- [ ] Check certificate validity dates
- [ ] Obtain new certificate if expired
- [ ] Update certificate in docs/Tribu-CR/

### If Signature Tests Fail

#### XML Generation Fails
- [ ] Check invoice was created successfully
- [ ] Verify e-invoice document exists
- [ ] Review Odoo logs for XML errors
- [ ] Check XML generator configuration

#### Signature Generation Fails
- [ ] Ensure certificate loaded successfully
- [ ] Verify private key extracted
- [ ] Check cryptography library installed
- [ ] Review xml_signer.py logs

#### Structure Validation Fails
- [ ] Open signed XML file manually
- [ ] Check namespace declarations
- [ ] Verify element hierarchy
- [ ] Compare against XMLDSig spec

### If Connection Fails

#### Odoo Not Running
```bash
docker-compose up -d
docker-compose ps
```

#### Database Not Accessible
- [ ] Verify database name in script
- [ ] Check credentials (username/password)
- [ ] Ensure module is installed
- [ ] Review Odoo logs

#### Authentication Error
- [ ] Verify admin username/password
- [ ] Check database name is correct
- [ ] Try accessing Odoo UI manually
- [ ] Review Odoo configuration

---

## Manual Verification Checklist

### Inspect Signed XML File

Open `signed_xml_*.xml` and verify:
- [ ] XML declaration present: `<?xml version="1.0" encoding="utf-8"?>`
- [ ] Root element (FacturaElectronica or similar)
- [ ] Signature element at end of document
- [ ] Namespace: `xmlns:ds="http://www.w3.org/2000/09/xmldsig#"`

### Check Signature Elements

Within `<ds:Signature>`:
- [ ] `<ds:SignedInfo>` section
  - [ ] `<ds:CanonicalizationMethod Algorithm="...">`
  - [ ] `<ds:SignatureMethod Algorithm="...rsa-sha256">`
  - [ ] `<ds:Reference URI="">` with transforms
  - [ ] `<ds:DigestMethod Algorithm="...sha256">`
  - [ ] `<ds:DigestValue>` with Base64 content
- [ ] `<ds:SignatureValue>` with Base64 signature
- [ ] `<ds:KeyInfo>` section
  - [ ] `<ds:X509Data>`
  - [ ] `<ds:X509Certificate>` with Base64 certificate

### Validate Base64 Content

Test Base64 encoding (optional):
```bash
# Extract and decode signature value
grep -A1 "SignatureValue" signed_xml_*.xml | tail -1 | base64 -D | wc -c
# Should output byte count (e.g., 256 for 2048-bit RSA)

# Extract and decode certificate
grep -A1 "X509Certificate" signed_xml_*.xml | tail -1 | base64 -D | wc -c
# Should output certificate size in bytes
```

- [ ] SignatureValue decodes without error
- [ ] X509Certificate decodes without error
- [ ] DigestValue decodes without error

---

## Success Confirmation Checklist

### All Tests Passed
- [ ] Console shows "EXCELLENT!" message
- [ ] Pass rate 90% or higher
- [ ] No critical errors in output
- [ ] All 10 test sections completed

### Artifacts Generated
- [ ] Signed XML files exist and are valid
- [ ] JSON results file created
- [ ] No error messages in files

### Hacienda Compliance
- [ ] RSA-SHA256 algorithm used
- [ ] SHA-256 digest method
- [ ] Enveloped signature pattern
- [ ] X.509 certificate embedded
- [ ] Correct namespaces
- [ ] Base64 encoding valid

### Ready for Phase 3
- [ ] Digital signature working correctly
- [ ] Certificate management validated
- [ ] XML signing pipeline functional
- [ ] Structure matches Hacienda spec

---

## Next Actions Checklist

### If All Tests Pass
- [ ] Save test results for documentation
- [ ] Archive signed XML samples
- [ ] Update project status (Phase 2 complete)
- [ ] Begin Phase 3 planning (Hacienda API)
- [ ] Prepare API credentials for submission testing

### If Tests Fail
- [ ] Review detailed failure messages
- [ ] Check troubleshooting section
- [ ] Review Odoo logs for errors
- [ ] Verify implementation against spec
- [ ] Fix issues and re-run tests
- [ ] Document any configuration changes needed

### Documentation Tasks
- [ ] Update project README with Phase 2 status
- [ ] Document any special configuration needed
- [ ] Note certificate requirements for deployment
- [ ] Prepare handoff documentation

---

## Sign-Off Checklist

Phase 2 Digital Signature Implementation:
- [ ] All test sections pass
- [ ] Certificate management functional
- [ ] XML signing working correctly
- [ ] Signature structure validated
- [ ] Hacienda requirements met
- [ ] Documentation complete
- [ ] Ready for Phase 3

**Tested By**: _________________
**Date**: _________________
**Pass Rate**: ________%
**Status**: [ ] Pass [ ] Fail
**Notes**: _________________________________________________

---

## Quick Command Reference

```bash
# Run tests
python3 test_einvoice_phase2_signature.py

# Check Odoo status
docker-compose ps

# View Odoo logs
docker-compose logs -f odoo

# List generated files
ls -lh signed_xml_*.xml phase2_signature_test_results_*.json

# View signed XML
cat signed_xml_*.xml

# Check signature structure
grep -A 50 "<ds:Signature" signed_xml_*.xml

# View test results
cat phase2_signature_test_results_*.json | python3 -m json.tool
```

---

**Remember**: This is a critical phase - digital signature must be 100% correct for Hacienda acceptance!
