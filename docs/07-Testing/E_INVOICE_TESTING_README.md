# E-Invoice Test Suite - Quick Start Guide

## TL;DR - Execute All Tests Now

```bash
cd /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS
./run_all_einvoice_tests.sh
```

Wait 15-20 minutes, then review the consolidated report.

---

## Current Status

**Odoo:** NOT RUNNING - needs to be started
**Database:** gms_validation
**Module:** l10n_cr_einvoice
**Certificate:** ✓ Available at `docs/Tribu-CR/certificado.p12`

---

## Test Scripts

| Phase | Script | Tests | Purpose |
|-------|--------|-------|---------|
| 1 | `test_einvoice_phase1.py` | 6 | XML Generation |
| 2 | `test_einvoice_phase2_signature.py` | 21 | Digital Signature |
| 3 | `test_phase3_api.py` | 10 | Hacienda API |

**Total:** 37 comprehensive tests

---

## What Gets Tested

### Phase 1: XML Generation
- Module installation
- E-invoice creation
- Clave (50-char key) generation
- XML structure (Hacienda v4.4 spec)
- DetalleServicio line items

### Phase 2: Digital Signature
- Certificate loading (.p12)
- Certificate validation
- XML signing (XMLDSig)
- Signature structure validation
- Error handling

### Phase 3: Hacienda API
- API connection (sandbox)
- Authentication
- Document submission
- Status checking
- Response parsing

---

## Expected Results

### Success (Production Ready)
- Phase 1: 100% pass
- Phase 2: 90%+ pass (18+ of 21 tests)
- Phase 3: 80%+ pass (API connected)

### Partial Success (Needs Review)
- Phase 1: 100% pass
- Phase 2: 70-89% pass
- Phase 3: 50-79% pass

### Failure (Not Ready)
- Any phase < 70% pass
- Certificate expired
- Cannot connect to Odoo
- Module not installed

---

## Output Files

After running tests, you'll have:

```
phase1_test_output.txt                        # Phase 1 console output
phase2_test_output.txt                        # Phase 2 console output
phase3_test_output.txt                        # Phase 3 console output
test_einvoice_<timestamp>.xml                 # Unsigned XML
signed_xml_<invoice>.xml                      # Signed XML
phase2_signature_test_results_<time>.json     # Detailed results
E_INVOICE_TEST_CONSOLIDATED_REPORT_<time>.txt # Summary report
```

---

## Manual Execution (If Needed)

### 1. Start Odoo
```bash
docker-compose up -d
sleep 60  # Wait for startup
```

### 2. Run Tests Individually
```bash
# Phase 1
python3 test_einvoice_phase1.py

# Phase 2
python3 test_einvoice_phase2_signature.py

# Phase 3
python3 test_phase3_api.py
```

### 3. Stop Odoo
```bash
docker-compose stop
```

---

## Quick Troubleshooting

### Problem: Connection refused
```bash
# Check if Docker is running
docker ps

# Wait longer for Odoo startup
sleep 30

# Check logs
docker logs gms_odoo
```

### Problem: Module not installed
```bash
# Access Odoo UI
open http://localhost:8070

# Apps > Search "l10n_cr_einvoice" > Install
```

### Problem: Certificate error
```bash
# Verify certificate exists
ls -lh docs/Tribu-CR/certificado.p12

# Check file is readable
cat docs/Tribu-CR/certificado.p12 > /dev/null && echo "OK"
```

---

## Time Required

- **Automated Execution:** 15-20 minutes
- **Manual Execution:** 25-30 minutes
- **Review Results:** 10-15 minutes

**Total:** ~30-45 minutes for complete validation

---

## Decision Tree

```
Run ./run_all_einvoice_tests.sh
        |
        v
All tests pass (90%+)?
    |           |
   YES         NO
    |           |
    v           v
Production   Fix issues
  Ready      Re-test
```

---

## Additional Documentation

- **Complete Guide:** `E_INVOICE_TEST_EXECUTION_PLAN.md` (detailed)
- **Summary:** `E_INVOICE_TEST_SUMMARY.md` (overview)
- **This File:** `E_INVOICE_TESTING_README.md` (quick start)

---

## Support

If tests fail:
1. Check `phase*_test_output.txt` files
2. Review `E_INVOICE_TEST_EXECUTION_PLAN.md` troubleshooting section
3. Verify Docker logs: `docker logs gms_odoo`
4. Ensure certificate is not expired
5. Verify network connectivity for Phase 3

---

## Next Steps After Testing

**If All Pass:**
- Configure production Hacienda credentials
- Test 1-2 real invoices in sandbox
- Deploy to production
- Monitor first 10 submissions

**If Partial Pass:**
- Review failed tests
- Fix critical issues
- Re-run affected phases
- Consider phased deployment

**If Tests Fail:**
- Review error logs
- Check configuration
- Verify module installation
- Consult Odoo documentation

---

**Ready to start?** Run `./run_all_einvoice_tests.sh` now!
