# E2E Sandbox Testing Guide

## Overview
This guide explains how to test the Costa Rica e-invoicing module against the real Hacienda sandbox environment.

## Prerequisites

✅ **Sandbox Credentials** (from `docs/Tribu-CR/Credentials.md`):
- Username: `cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr`
- Password: `e8KLJRHzRA1P0W2ybJ5T`
- Certificate PIN: `5147`

✅ **Certificate File**: `docs/Tribu-CR/certificado.p12`

✅ **Network Access**: Hacienda sandbox endpoints must be reachable

## Test Scenarios

### 1. Complete FE (Factura Electrónica) Lifecycle

**Objective**: Test full invoice submission flow from creation to acceptance

**Steps**:
1. Access Odoo at http://localhost:8070
2. Login as admin
3. Configure company for sandbox:
   - Go to Settings → Companies → Your Company
   - Navigate to "E-Invoicing" tab
   - Set Environment: "Sandbox (Testing)"
   - Enter sandbox credentials
   - Upload certificate (certificado.p12) with PIN 5147
4. Create test customer:
   - Name: "Test Customer E2E"
   - VAT: 9-digit number (e.g., `102340567`)
   - ID Type: "01 - Física"
   - Country: Costa Rica
5. Create invoice:
   - Customer: Test Customer E2E
   - Product/Service: Any item
   - Amount: ₡10,000 + 13% IVA = ₡11,300
   - Confirm invoice
6. Verify e-invoice document created:
   - Go to Accounting → Costa Rica → E-Invoice Documents
   - Find document for your invoice
   - State should be "Draft"
7. Generate XML:
   - Click "Generate XML" button
   - State → "Generated"
   - Verify Clave (50 digits)
8. Sign XML:
   - Click "Sign XML" button
   - State → "Signed"
   - Verify signature present in XML
9. Submit to Hacienda:
   - Click "Submit to Hacienda" button
   - State → "Submitted"
   - Check response messages
10. Check status:
    - Click "Check Status" button
    - State should become "Accepted" (may take a few seconds)

**Expected Result**: ✅ Invoice accepted by Hacienda sandbox

**Performance Target**: <15 seconds total (sandbox), <10 seconds (production)

---

### 2. TE (Tiquete Electrónico) Submission

**Objective**: Test simplified receipt/ticket format

**Steps**:
1. Create invoice as above
2. Before confirming, set document type to "TE" (if not automatic)
3. Follow same workflow: Generate → Sign → Submit → Check Status

**Expected Result**: ✅ Tiquete accepted by Hacienda

---

### 3. NC (Nota de Crédito) - Credit Note

**Objective**: Test refund/correction workflow

**Steps**:
1. First create and submit a regular FE invoice (follow scenario 1)
2. Wait for acceptance
3. Create credit note:
   - Go to invoice
   - Click "Add Credit Note" button
   - Reason: "Test refund"
   - Create and view credit note
4. Verify NC document created (document type = "NC")
5. Generate → Sign → Submit → Check Status

**Expected Result**: ✅ Credit note accepted, references original invoice

---

### 4. ND (Nota de Débito) - Debit Note

**Objective**: Test additional charge workflow

**Steps**:
1. Create and submit original FE invoice
2. Create debit note:
   - Go to Accounting → Costa Rica → E-Invoice Documents
   - Create new document
   - Type: "ND - Nota de Débito"
   - Link to original invoice (debit_origin_id field)
   - Add line items for additional charges
3. Generate → Sign → Submit → Check Status

**Expected Result**: ✅ Debit note accepted, references original invoice

---

### 5. Bulk Submission Performance

**Objective**: Test system performance with multiple invoices

**Steps**:
1. Create 10 invoices for same customer
2. Confirm all 10 invoices
3. For each e-invoice document:
   - Generate XML
   - Sign XML
   - Submit to Hacienda
4. Measure total time

**Expected Result**:
- ✅ All 10 invoices accepted
- ✅ Average <15 seconds per invoice (sandbox)
- ✅ No duplicate submissions

---

### 6. Error Handling & Retry Queue

**Objective**: Verify retry mechanism handles transient failures

**Steps**:
1. Temporarily disable network (or use invalid credentials)
2. Try to submit invoice
3. Verify retry queue entry created:
   - Go to Accounting → Costa Rica → Retry Queue
   - Find entry for your invoice
   - Status should be "Pending"
4. Re-enable network (or fix credentials)
5. Run retry queue manually or wait for cron
6. Verify submission succeeds

**Expected Result**:
- ✅ Retry queue captures failed submission
- ✅ Automatic retry succeeds after issue resolved
- ✅ No duplicate submissions

---

### 7. Idempotency Test

**Objective**: Ensure clicking "Submit" twice doesn't create duplicates

**Steps**:
1. Create invoice, generate and sign XML
2. Click "Submit to Hacienda" button
3. Wait for submission to complete
4. Click "Submit to Hacienda" again (should be prevented or no-op)
5. Check response messages count

**Expected Result**:
- ✅ Only ONE submission response message created
- ✅ Second click either prevented or safely ignored

---

## Manual Testing Checklist

Use this checklist to track manual E2E testing progress:

- [ ] **FE Complete Lifecycle** - Invoice created → accepted
- [ ] **TE Submission** - Tiquete accepted
- [ ] **NC Submission** - Credit note accepted
- [ ] **ND Submission** - Debit note accepted
- [ ] **XML Signature Validation** - XAdES-EPES signature present
- [ ] **Clave Generation** - 50-digit clave valid format
- [ ] **Response Messages** - Audit trail captured
- [ ] **Bulk Submission** - 10 invoices in <150s total
- [ ] **Retry Queue** - Failed submission retried successfully
- [ ] **Idempotency** - No duplicate submissions
- [ ] **Error Handling** - Invalid XML rejected with clear error
- [ ] **Certificate Validation** - Expired cert rejected

---

## Troubleshooting

### Issue: "Authentication failed"
**Solution**: Verify sandbox credentials in company settings match docs/Tribu-CR/Credentials.md

### Issue: "Certificate error"
**Solution**:
- Verify certificate file is uploaded
- Verify PIN (5147) is correct
- Check certificate not expired

### Issue: "XML validation failed"
**Solution**:
- Check invoice data completeness
- Verify customer VAT format (9 or 10 digits)
- Ensure all required fields filled

### Issue: "Submission timeout"
**Solution**:
- Check network connectivity to Hacienda sandbox
- Verify firewall not blocking HTTPS to `*.comprobanteselectronicos.go.cr`
- Try again - sandbox may be slow

### Issue: "Invoice stuck in 'Processing'"
**Solution**:
- Wait 30 seconds, click "Check Status" again
- Sandbox can take 5-30 seconds to process
- If still stuck after 5 minutes, check Hacienda sandbox status

---

## Automated E2E Test Execution (Advanced)

The automated E2E tests in `l10n_cr_einvoice/tests/test_e2e_sandbox_lifecycle.py` are designed to run the above scenarios programmatically.

**Note**: These tests are currently not integrated with Odoo's standard test runner due to their external dependency nature and long execution time. They are intended for:
- Nightly CI/CD runs
- Pre-release validation
- Performance regression testing

To run programmatically, you would need to:
1. Install pytest in the Odoo container
2. Configure test fixtures for sandbox access
3. Run: `pytest l10n_cr_einvoice/tests/test_e2e_sandbox_lifecycle.py -v`

**For Phase 7 completion, manual testing using this guide is sufficient.**

---

## Success Criteria

✅ All test scenarios pass
✅ No errors in Odoo logs
✅ Response messages captured correctly
✅ Performance targets met
✅ Retry queue handles failures
✅ No duplicate submissions

**Status**: Ready for manual E2E testing
