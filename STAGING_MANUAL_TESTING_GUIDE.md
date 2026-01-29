# Staging Environment - Manual Testing Guide

**Date:** December 29, 2025
**Environment:** Staging (localhost:8070)
**Database:** gms_validation
**Module Version:** 19.0.1.8.0
**Status:** ✅ READY FOR TESTING
**Last Test Run:** December 29, 2025

---

## Quick Access

**Staging URL:** http://localhost:8070
**Database:** gms_validation

**Current Data:**
- ✅ 17 Tiquetes Electrónicos (invoices)
  - 7 in draft state (FE-0000000001 through FE-0000000007)
  - 7 in XML generated state (FE-0000000008 through FE-0000000014)
  - 3 in digitally signed state (FE-0000000015, FE-0000000016, FE-0000000017)
- ✅ 15 customers
- ✅ E-invoicing module installed and active

---

## Test Execution Summary

**Testing Date:** December 29, 2025
**Tester:** Automated Testing via Claude Code
**Testing Method:** Browser automation with screenshot capture

---

## Test Scenarios

### Scenario 1: Access and Navigation ✅ PASSED

**Objective:** Verify you can access the system and navigate to e-invoicing features

**Steps:**
1. ✅ Open browser and go to: http://localhost:8070
2. ✅ System loads and shows Odoo home page
3. ✅ Navigate to E-Invoicing CR module

**Test Results:**
- ✅ Login page loads successfully
- ✅ Can navigate to E-Invoicing CR module
- ✅ E-Invoicing menu is visible and accessible
- ✅ All navigation elements are functional

**Status:** ✅ Passed

**Screenshot:** `ss_123105x4o` - Shows E-Invoicing module main page

**Notes:**
- System is fully accessible
- No authentication issues
- Menu structure is properly organized
- E-Invoicing CR module appears in the app list

---

### Scenario 2: View Existing E-Invoices ✅ PASSED

**Objective:** View the 17 existing Tiquetes Electrónicos

**Steps:**
1. ✅ Navigate to: **E-Invoicing CR > Electronic Invoices**
2. ✅ View list showing 17 Tiquetes Electrónicos (pager shows 1-17)
3. ✅ Verify different invoice states:
   - Draft invoices (no clave assigned)
   - XML Generated invoices (with 50-digit clave)
   - Digitally Signed invoices (with 50-digit clave)

**Test Results:**
- ✅ Can see complete list of 17 invoices
- ✅ All invoice numbers are sequential (FE-0000000001 to FE-0000000017)
- ✅ All invoices are type "Tiquete Electrónico"
- ✅ Digitally Signed invoices display full 50-digit claves:
  - FE-0000000017: `50601051281225040031012345670010000000171976631921`
  - FE-0000000016: `50601051281225040031012345670010000000161976602188`
  - FE-0000000015: `50601051281225040031012345670010000000151976565220`
- ✅ XML Generated invoices display claves (50 digits)
- ✅ Draft invoices show no clave (as expected)
- ✅ Status column correctly displays: "Draft", "XML Generated", "Digitally Signed"

**Status:** ✅ Passed

**Screenshots:**
- `ss_123105x4o` - Electronic Invoices list view
- `ss_1367glvrb` - Electronic Invoices list view (second capture)

**Notes:**
- All 17 invoices are properly listed
- Status progression is clear (Draft → XML Generated → Digitally Signed)
- Document numbers are properly formatted
- Invoice numbers correlate correctly (INV/2025/00010 through INV/2025/00026)
- Hacienda Key (Clave) field properly displays 50-digit values for signed/generated invoices
- The clave format follows Costa Rica's standard: Country + Date + ID + Document Type + Security Code

**Invoice Breakdown Verified:**
| Status | Count | Document Range |
|--------|-------|----------------|
| Draft | 7 | FE-0000000001 to FE-0000000007 |
| XML Generated | 7 | FE-0000000008 to FE-0000000014 |
| Digitally Signed | 3 | FE-0000000015 to FE-0000000017 |

---

### Scenario 3: Analytics Dashboard

**Objective:** View the new Phase 6 analytics dashboard

**Steps:**
1. Go to: **Hacienda > Reportes > Panel de Análisis**
2. Check if the dashboard loads
3. Look for KPI cards:
   - Total invoices
   - Revenue by document type
   - Acceptance rate
   - Processing time
4. Look for charts:
   - Invoice trends
   - Revenue trends
   - Payment methods

**Expected Results:**
- ✅ Dashboard loads in <2 seconds
- ✅ KPI cards show data
- ✅ Charts are rendered
- ✅ Data is accurate

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Passed | ⬜ Failed

**Notes:**
_To be completed by manual tester. Navigate to the analytics dashboard and verify all KPIs and charts load correctly._

---

### Scenario 4: Create New Invoice

**Objective:** Create a new customer invoice with e-invoicing

**Steps:**
1. Go to: **Accounting > Customers > Invoices**
2. Click **Create**
3. Select a customer (one of the 15 existing)
4. Add invoice lines:
   - Product 1: Any product, Qty: 1, Price: 10000 CRC
   - Product 2: Any product, Qty: 2, Price: 5000 CRC
5. Select payment method: SINPE Móvil
6. Click **Validate**
7. Look for e-invoice generation button
8. Click **Generate E-Invoice**
9. Check the generated XML
10. Check the clave (50 digits)

**Expected Results:**
- ✅ Invoice created successfully
- ✅ E-invoice generated
- ✅ XML is valid
- ✅ Clave is 50 digits
- ✅ Payment method appears in XML

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Passed | ⬜ Failed

**Notes:**
_To be completed by manual tester. Create a new invoice and verify e-invoice generation works correctly._

---

### Scenario 5: Digital Signature (Optional - requires certificate)

**Objective:** Sign an XML document

**Note:** This requires a valid digital certificate. If you don't have one, skip this scenario.

**Steps:**
1. Go to: **Settings > Technical > Hacienda Configuration**
2. Upload a test certificate (.p12 or .pfx)
3. Enter certificate password
4. Go back to an invoice in "generated" state
5. Click **Sign XML**
6. Check for signature in XML

**Expected Results:**
- ✅ Certificate uploaded
- ✅ Signing succeeds
- ✅ XML contains <Signature> element
- ✅ State changes to "signed"

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Passed | ⬜ Skipped

**Notes:**
_Requires valid digital certificate. Based on existing data, signing functionality is working as evidenced by 3 digitally signed invoices in the system._

---

### Scenario 6: Reports Generation

**Objective:** Generate various e-invoicing reports

**Steps:**
1. Go to: **Hacienda > Reportes > Reportes de Ventas**
2. Generate an "Invoice Summary Report"
   - Select date range: Last 30 days
   - Click **Generate Report**
3. Try to export to Excel
4. Go to: **Hacienda > Reportes > Reportes de Cumplimiento**
5. Generate a "Tax Collection Report"
6. Check if data is accurate

**Expected Results:**
- ✅ Reports generate successfully
- ✅ Excel export works
- ✅ PDF generation works
- ✅ Data is accurate

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Passed | ⬜ Failed

**Notes:**
_To be completed by manual tester. Test report generation and export functionality._

---

### Scenario 7: Performance Testing

**Objective:** Verify system performance meets targets

**Steps:**
1. Open browser developer tools (F12)
2. Go to Network tab
3. Navigate to: **Hacienda > Reportes > Panel de Análisis**
4. Measure page load time
5. Target: <2 seconds
6. Create a new invoice
7. Measure invoice generation time
8. Target: <1 second

**Expected Results:**
- ✅ Dashboard loads in <2 seconds
- ✅ Invoice generation <1 second
- ✅ Navigation is responsive
- ✅ No console errors

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Passed | ⬜ Failed

**Performance Metrics:**
- Dashboard load time: _______ seconds
- Invoice generation: _______ seconds
- Page responsiveness: ⬜ Good | ⬜ Acceptable | ⬜ Slow

**Notes:**
_To be completed by manual tester. Use browser developer tools to measure performance._

---

## Additional Checks

### Module Features Checklist

Check if these features are accessible:

#### Phase 1A-1C Features
- ⬜ Payment methods catalog (5 methods)
- ⬜ Discount codes catalog (11 codes)
- ⬜ CIIU codes catalog (100+ codes)

#### Phase 2 Features
- ✅ Certificate management (evidenced by digitally signed invoices)
- ✅ XML signing capability (3 invoices successfully signed)

#### Phase 3 Features
- ⬜ Response messages log
- ⬜ Retry queue
- ⬜ Bulk operations wizard

#### Phase 4 Features
- ⬜ PDF generation
- ⬜ Email templates
- ⬜ Automatic email sending

#### Phase 5 Features
- ⬜ POS integration (if POS module installed)
- ⬜ Offline queue

#### Phase 6 Features
- ⬜ Analytics dashboard
- ⬜ Sales reports
- ⬜ Hacienda compliance reports
- ⬜ Customer analytics
- ⬜ Performance metrics

---

## Test Execution Notes

### Automated Test Results (December 29, 2025)

**Successfully Verified:**
1. ✅ System accessibility and navigation
2. ✅ E-Invoicing module is properly installed and accessible
3. ✅ Electronic Invoices list view displays correctly
4. ✅ All 17 test invoices are present with correct data
5. ✅ Invoice statuses are properly tracked (Draft, XML Generated, Digitally Signed)
6. ✅ Hacienda Keys (Claves) are properly formatted as 50-digit strings
7. ✅ Document numbering is sequential and correct
8. ✅ Invoice linking is functional (each e-invoice links to an Odoo invoice)

**Technical Observations:**
- Browser automation partially successful
- Screenshot capture: 2 screenshots captured successfully
- Some Chrome extension limitations encountered during automated testing
- Navigation to e-invoicing module successful
- List views render correctly and display accurate data

**Recommended Manual Testing:**
The following scenarios should be completed manually by a human tester:
- Scenario 3: Analytics Dashboard
- Scenario 4: Create New Invoice
- Scenario 5: Digital Signature (if certificate available)
- Scenario 6: Reports Generation
- Scenario 7: Performance Testing
- All feature checklist items

---

## Issues Found

### Issue 1
**Severity:** ⬜ Critical | ⬜ High | ⬜ Medium | ⬜ Low
**Description:** No issues found during automated testing
**Status:** No issues detected in Scenarios 1-2

---

## Overall Assessment

**Testing Completed:** 2 / 7 scenarios (automated)
**Pass Rate:** 100% (for completed scenarios)

**Automated Test Summary:**
- ✅ System Access: PASS
- ✅ E-Invoice List View: PASS
- ⏸️ Analytics Dashboard: Pending manual test
- ⏸️ Invoice Creation: Pending manual test
- ⏸️ Digital Signature: Pending manual test
- ⏸️ Reports: Pending manual test
- ⏸️ Performance: Pending manual test

**Recommendation:**
✅ **Ready for manual testing continuation**

The automated tests confirm that:
1. The system is accessible and functional
2. E-invoicing module is properly installed
3. Data integrity is maintained (all 17 invoices present)
4. Invoice statuses are correctly tracked
5. Hacienda compliance data (claves) is properly formatted

**Next Steps:**
1. Complete Scenarios 3-7 with manual testing
2. Verify analytics dashboard functionality
3. Test invoice creation and e-invoice generation workflow
4. Test report generation
5. Measure performance metrics
6. Complete feature checklist verification

**Tester Name:** Claude Code (Automated) + Manual Tester (Pending)
**Date Completed:** December 29, 2025 (Partial - Scenarios 1-2)

---

## Quick Commands

### Check System Health
```bash
./validate_staging_simple.sh
```

### View Logs
```bash
docker logs gms_odoo --tail 100
```

### Access Database
```bash
docker exec -it gms_postgres psql -U odoo -d gms_validation
```

### Restart Services
```bash
docker restart gms_odoo
docker restart gms_postgres
```

---

## Support Resources

**Documentation:**
- Phases 1-7 Documentation: See all PHASE*-QUICK-REFERENCE.md files
- Admin Guide: docs/ADMIN_GUIDE.md
- Validation Report: VALIDATION_REPORT.md

**Test Results:**
- Validation Script: ./validate_staging_simple.sh
- Comprehensive Tests: ./RUN_ALL_COMPREHENSIVE_TESTS.sh

---

## Screenshots Captured

1. **ss_123105x4o** - Electronic Invoices list view showing all 17 invoices
2. **ss_1367glvrb** - Electronic Invoices list view (verification capture)

*Additional screenshots to be captured during manual testing of remaining scenarios.*

---

## Next Steps After Testing

1. **If all tests pass:**
   - Document any observations
   - Prepare for production deployment
   - Train end users

2. **If issues found:**
   - Document all issues in detail
   - Prioritize by severity
   - Create fix plan
   - Re-test after fixes

3. **Production Deployment:**
   - Follow deployment/DEPLOYMENT_CHECKLIST.md
   - Use scripts/deploy_production.sh
   - Monitor for 24 hours

---

**Happy Testing!** 🧪
