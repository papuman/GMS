# E-Invoice Test Execution Plan
## Complete Test Suite for Phases 1, 2, and 3

**Generated:** 2025-12-28
**Purpose:** Execute comprehensive e-invoicing test suite across all three implementation phases

---

## Executive Summary

This document provides a complete test execution plan for the Costa Rica E-Invoice module (`l10n_cr_einvoice`). The test suite validates XML generation (Phase 1), digital signature (Phase 2), and Hacienda API integration (Phase 3).

**Status:** Odoo is currently NOT running. Docker containers need to be started before test execution.

---

## Prerequisites

### 1. Environment Requirements

- Docker Desktop installed and running
- PostgreSQL container (gms_postgres)
- Odoo 19.0 container (gms_odoo)
- Python 3.x with xmlrpc.client library
- Network access for Hacienda API testing (Phase 3)

### 2. Configuration Files

```
/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/
├── docker-compose.yml          ✓ Exists
├── odoo.conf                   ✓ Exists
├── test_einvoice_phase1.py     ✓ Exists (Recommended)
├── test_phase1_einvoice.py     ✓ Exists (Older version)
├── test_einvoice_phase2_signature.py ✓ Exists
└── test_phase3_api.py          ✓ Exists
```

### 3. Test Data Requirements

- **Database:** `gms_validation`
- **User:** `admin` / Password: `admin`
- **Module:** `l10n_cr_einvoice` (must be installed)
- **Certificate:** `/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs/Tribu-CR/certificado.p12`
- **Certificate PIN:** `5147`

---

## Test Suite Overview

### Phase 1: XML Generation & Validation
**Script:** `test_einvoice_phase1.py` (RECOMMENDED - most recent)
**Purpose:** Validate XML generation without signature
**Duration:** ~2-3 minutes

#### Tests Covered:
1. Module installation verification
2. E-invoice document creation
3. Clave (50-character key) generation
4. XML structure generation
5. XSD compliance (basic structure)
6. DetalleServicio line items validation

#### Expected Outputs:
- Console test results
- XML file: `test_einvoice_<timestamp>.xml`
- Pass rate: 100% for basic functionality

---

### Phase 2: Digital Signature
**Script:** `test_einvoice_phase2_signature.py`
**Purpose:** Validate digital certificate and XML signing
**Duration:** ~5-8 minutes

#### Tests Covered:
1. Certificate file existence verification
2. Certificate upload to company configuration
3. .p12 certificate loading
4. Certificate validity check (expiry dates)
5. Certificate date extraction
6. Wrong PIN error handling
7. Test invoice creation
8. Unsigned XML generation
9. XML digital signature generation
10. Signature structure verification (XMLDSig standard)
11. SignedInfo element validation
12. CanonicalizationMethod verification
13. SignatureMethod (RSA-SHA256) validation
14. Reference element validation
15. DigestMethod (SHA-256) validation
16. DigestValue Base64 encoding validation
17. SignatureValue Base64 encoding validation
18. KeyInfo element validation
19. X509Data validation
20. X509Certificate embedding verification
21. Complete workflow integration test

#### Expected Outputs:
- Console test results with detailed pass/fail
- Signed XML file: `signed_xml_<invoice_number>.xml`
- JSON results: `phase2_signature_test_results_<timestamp>.json`
- Pass rate: 90%+ for production readiness

---

### Phase 3: Hacienda API Integration
**Script:** `test_phase3_api.py`
**Purpose:** Validate API connection and submission
**Duration:** ~3-5 minutes (depends on network)

#### Tests Covered:
1. API connection test
2. Environment detection (sandbox vs production)
3. Authentication validation
4. Find signed e-invoice documents
5. Submit document to Hacienda
6. Parse Hacienda response
7. Status checking workflow
8. Retry logic validation
9. ID type detection helpers (Cédula, DIMEX, etc.)
10. Error handling (rate limiting, network errors)

#### Expected Outputs:
- Console test results
- API response validation
- Hacienda acceptance/rejection status
- Error handling validation

---

## Step-by-Step Execution Instructions

### Step 1: Start Odoo Environment

```bash
cd /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS

# Start Docker containers
docker-compose up -d

# Verify containers are running
docker ps

# Expected output:
# CONTAINER ID   IMAGE          STATUS         PORTS
# <id>          odoo:19.0      Up X seconds   0.0.0.0:8070->8069/tcp
# <id>          postgres:13    Up X seconds   0.0.0.0:5432->5432/tcp

# Check Odoo logs (wait for "odoo.service.server: HTTP service (werkzeug) running")
docker logs -f gms_odoo
```

**Wait approximately 30-60 seconds for Odoo to fully start.**

### Step 2: Verify Database and Module

```bash
# Access Odoo web interface
# Open browser: http://localhost:8070
# Login: admin / admin
# Database: gms_validation

# Verify module installation:
# Apps > Search "l10n_cr_einvoice" > Should show "Installed"
```

### Step 3: Execute Phase 1 Tests

```bash
# Make script executable
chmod +x test_einvoice_phase1.py

# Run Phase 1 tests
python3 test_einvoice_phase1.py > phase1_test_output.txt 2>&1

# Review results
cat phase1_test_output.txt

# Check for generated XML
ls -lh test_einvoice_*.xml
```

**Expected Success Criteria:**
- Module installed: Yes
- E-invoice created: Yes
- XML generated: Yes (5,000-15,000 bytes)
- Clave generated: Yes (50 characters)
- State: `generated`

### Step 4: Execute Phase 2 Tests

```bash
# Verify certificate exists
ls -lh /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs/Tribu-CR/certificado.p12

# Make script executable
chmod +x test_einvoice_phase2_signature.py

# Run Phase 2 tests
python3 test_einvoice_phase2_signature.py > phase2_test_output.txt 2>&1

# Review results
cat phase2_test_output.txt

# Check for signed XML and JSON results
ls -lh signed_xml_*.xml
ls -lh phase2_signature_test_results_*.json
```

**Expected Success Criteria:**
- Certificate loaded: Yes
- Certificate valid: Yes (check expiry warning)
- XML signed: Yes (larger than unsigned XML)
- Signature structure: All XMLDSig elements present
- Pass rate: 18+ tests passed out of 21 (85%+)

### Step 5: Execute Phase 3 Tests

```bash
# Note: This requires signed documents from Phase 2

# Make script executable
chmod +x test_phase3_api.py

# Run Phase 3 tests
python3 test_phase3_api.py > phase3_test_output.txt 2>&1

# Review results
cat phase3_test_output.txt
```

**Expected Success Criteria:**
- API connection: Success (sandbox environment)
- Authentication: Valid
- Document submission: Success (or known error code)
- Status check: Processing/Accepted/Rejected
- Response parsing: Success

---

## Configuration Notes

### Port Mapping
- **Docker Internal Port:** 8069
- **External Port:** 8070
- **Database Port:** 5432

### Test Scripts Configuration
All test scripts are configured for:
- `ODOO_URL = 'http://localhost:8070'`
- `DB = 'gms_validation'`
- `USERNAME = 'admin'`
- `PASSWORD = 'admin'`

### Known Discrepancies
There are two Phase 1 test scripts:
1. `test_phase1_einvoice.py` - Older version (Dec 28, 14:10)
2. `test_einvoice_phase1.py` - **RECOMMENDED** - Newer version (Dec 28, 14:53)

**Use `test_einvoice_phase1.py` for consistency.**

---

## Troubleshooting Guide

### Problem: Cannot connect to Odoo

**Symptoms:**
```
xmlrpc.client.ProtocolError: <ProtocolError for localhost:8070/xmlrpc/2/common: 111 Connection refused>
```

**Solutions:**
1. Verify Docker containers are running: `docker ps`
2. Check Odoo logs: `docker logs gms_odoo`
3. Wait 60 seconds after starting containers
4. Verify port 8070 is not in use: `lsof -i :8070`

### Problem: Authentication failed

**Symptoms:**
```
❌ Authentication failed!
```

**Solutions:**
1. Verify database name: Should be `gms_validation`
2. Check credentials: admin/admin
3. Reset admin password via Odoo CLI if needed
4. Verify database exists: `docker exec -it gms_postgres psql -U odoo -l`

### Problem: Module not installed

**Symptoms:**
```
⚠️  Module l10n_cr_einvoice not installed
```

**Solutions:**
1. Access Odoo UI: http://localhost:8070
2. Go to Apps > Update Apps List
3. Search for "l10n_cr_einvoice"
4. Click Install
5. Or via CLI:
```bash
docker exec -it gms_odoo odoo-bin -d gms_validation -u l10n_cr_einvoice --stop-after-init
```

### Problem: Certificate not found (Phase 2)

**Symptoms:**
```
❌ Certificate file not found
```

**Solutions:**
1. Verify certificate path:
```bash
ls -lh /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs/Tribu-CR/certificado.p12
```
2. Update `CERT_PATH` in `test_einvoice_phase2_signature.py` if location changed
3. Verify certificate PIN is correct: `5147`

### Problem: No signed documents for Phase 3

**Symptoms:**
```
❌ No signed documents found to test
```

**Solutions:**
1. Run Phase 2 tests first to create signed documents
2. Or manually create and sign an invoice via Odoo UI
3. Check document state:
```python
# Search for signed documents
doc_ids = models.execute_kw(DB, uid, PASSWORD,
    'l10n_cr.einvoice.document', 'search',
    [[('state', '=', 'signed')]])
```

### Problem: Hacienda API connection fails (Phase 3)

**Symptoms:**
```
❌ Connection test failed
```

**Solutions:**
1. Verify internet connection
2. Check if sandbox environment is accessible
3. Verify credentials in company configuration
4. Review Hacienda API status (may be down for maintenance)
5. Check firewall/proxy settings

---

## Test Result Interpretation

### Phase 1 Results

**100% Pass Rate:**
- Production ready for basic XML generation
- Can proceed to Phase 2

**75-99% Pass Rate:**
- Review failed tests
- Common issues: Missing fields, incorrect clave format
- Fix issues before Phase 2

**< 75% Pass Rate:**
- Critical issues detected
- Review module configuration
- Check data setup (company, taxes, products)

### Phase 2 Results

**90-100% Pass Rate:**
- Production ready for digital signatures
- Can proceed to Phase 3

**70-89% Pass Rate:**
- Partial functionality
- Review certificate configuration
- May proceed to Phase 3 with caution

**< 70% Pass Rate:**
- Critical signature issues
- Do NOT proceed to Phase 3
- Review certificate manager and XML signer implementation

### Phase 3 Results

**100% Success:**
- Production ready for Hacienda submission
- All API integrations working

**Partial Success:**
- Review specific API errors
- May be Hacienda sandbox limitations
- Check credentials and environment configuration

**Complete Failure:**
- Verify network connectivity
- Check Hacienda API credentials
- Review API implementation

---

## Test Data Files Generated

After running all tests, the following files will be created:

```
/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/
├── test_einvoice_<timestamp>.xml                     # Phase 1 unsigned XML
├── phase1_test_output.txt                             # Phase 1 console output
├── signed_xml_<invoice_number>.xml                    # Phase 2 signed XML
├── phase2_signature_test_results_<timestamp>.json     # Phase 2 JSON results
├── phase2_test_output.txt                             # Phase 2 console output
├── phase3_test_output.txt                             # Phase 3 console output
```

**Cleanup Commands:**
```bash
# Remove test XML files
rm -f test_einvoice_*.xml signed_xml_*.xml

# Remove test output files
rm -f phase*_test_output.txt

# Remove JSON results
rm -f phase2_signature_test_results_*.json
```

---

## Key Metrics and Benchmarks

### Phase 1 Metrics
- **XML Generation Time:** < 5 seconds
- **XML Size:** 5,000 - 15,000 bytes (varies by invoice complexity)
- **Clave Length:** Exactly 50 characters
- **State After Generation:** `generated`

### Phase 2 Metrics
- **Certificate Loading Time:** < 2 seconds
- **XML Signing Time:** < 10 seconds
- **Signed XML Size:** 20,000 - 40,000 bytes (larger due to signature)
- **Signature Length:** ~350-500 characters (Base64)
- **Certificate Embedding:** ~2,000-4,000 bytes
- **State After Signing:** `signed`

### Phase 3 Metrics
- **API Connection Time:** < 3 seconds
- **Submission Time:** 5-15 seconds (depends on network)
- **Status Check Time:** < 5 seconds
- **Expected Response Time:** 10-60 seconds for Hacienda processing
- **Retry Attempts:** Max 3 (exponential backoff)

---

## Production Readiness Assessment

### Phase 1 Criteria
- [x] Module installed successfully
- [x] XML generation works for all invoice types
- [x] Clave generation is correct (50 chars)
- [x] DetalleServicio contains line items
- [x] XSD validation passes
- [ ] Manual XML review against Hacienda v4.4 spec

### Phase 2 Criteria
- [x] Certificate manager loads .p12 files
- [x] Certificate validation works (expiry check)
- [x] XML signing produces valid XMLDSig structure
- [x] SignatureValue is valid Base64
- [x] X509Certificate is embedded correctly
- [ ] Signature verification with external tools

### Phase 3 Criteria
- [ ] API connection successful (sandbox)
- [ ] Authentication with Hacienda credentials works
- [ ] Document submission returns valid response
- [ ] Status checking workflow functional
- [ ] Error handling covers all scenarios
- [ ] Ready for production Hacienda environment

---

## Next Steps After Testing

### If All Tests Pass (90%+ across all phases):
1. Create production Hacienda credentials
2. Update company configuration with production environment
3. Test with real invoice in sandbox first
4. Monitor first 10 production submissions closely
5. Enable auto-generation if desired
6. Train users on e-invoice workflow

### If Tests Partially Pass (70-89%):
1. Document all failed tests
2. Prioritize fixes based on criticality
3. Re-run tests after fixes
4. Consider phased rollout (Phase 1 only, then add Phase 2)

### If Tests Fail (< 70%):
1. Review error logs in detail
2. Verify configuration matches requirements
3. Check Odoo version compatibility (should be 19.0)
4. Review module implementation for bugs
5. Consider consulting Odoo developer

---

## Security Considerations

### Certificate Management
- Certificate PIN stored in script for testing (CHANGE for production)
- .p12 file should have restricted permissions: `chmod 600`
- Store production certificates in secure vault
- Rotate certificates before expiry (30-day warning)

### API Credentials
- Test scripts use sandbox credentials
- Production credentials should be encrypted
- Use environment variables for sensitive data
- Implement credential rotation policy

### Test Data
- Test invoices should use fictional customer data
- Avoid using real VAT numbers in testing
- Clean up test data after validation

---

## Automated Execution Script

For convenience, here's a complete automated execution script:

```bash
#!/bin/bash
# File: run_all_einvoice_tests.sh

set -e  # Exit on error

echo "======================================================================"
echo "  E-Invoice Complete Test Suite"
echo "  Starting at: $(date)"
echo "======================================================================"

# Step 1: Start Odoo
echo ""
echo "[1/5] Starting Odoo containers..."
docker-compose up -d

echo "Waiting 60 seconds for Odoo to start..."
sleep 60

# Step 2: Verify Odoo is running
echo ""
echo "[2/5] Verifying Odoo is accessible..."
curl -s http://localhost:8070 > /dev/null && echo "✓ Odoo is running" || (echo "✗ Odoo not accessible" && exit 1)

# Step 3: Run Phase 1 tests
echo ""
echo "[3/5] Running Phase 1 tests (XML Generation)..."
python3 test_einvoice_phase1.py | tee phase1_test_output.txt

# Step 4: Run Phase 2 tests
echo ""
echo "[4/5] Running Phase 2 tests (Digital Signature)..."
python3 test_einvoice_phase2_signature.py | tee phase2_test_output.txt

# Step 5: Run Phase 3 tests
echo ""
echo "[5/5] Running Phase 3 tests (Hacienda API)..."
python3 test_phase3_api.py | tee phase3_test_output.txt

# Summary
echo ""
echo "======================================================================"
echo "  Test Suite Completed at: $(date)"
echo "======================================================================"
echo ""
echo "Generated files:"
ls -lh test_einvoice_*.xml signed_xml_*.xml phase*_test_output.txt phase2_signature_test_results_*.json 2>/dev/null || echo "No files generated"

echo ""
echo "Review test outputs:"
echo "  - phase1_test_output.txt"
echo "  - phase2_test_output.txt"
echo "  - phase3_test_output.txt"
echo ""
```

**To use:**
```bash
chmod +x run_all_einvoice_tests.sh
./run_all_einvoice_tests.sh
```

---

## Conclusion

This comprehensive test execution plan provides a systematic approach to validating the entire e-invoicing system across all three implementation phases. Follow the steps sequentially, review results carefully, and address any failures before proceeding to production.

For questions or issues, refer to the troubleshooting section or review the individual test script source code for detailed implementation logic.

**Document Version:** 1.0
**Last Updated:** 2025-12-28
**Maintained By:** E-Invoice Testing Team
