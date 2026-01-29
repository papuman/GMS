# Phase 1A Deployment Checklist

**Module:** l10n_cr_einvoice v19.0.1.0.0
**Phase:** 1A - SINPE Móvil Payment Method Integration
**Date:** 2025-12-28

---

## Pre-Deployment Checks

### 1. Code Review
- [ ] All 11 new files created
- [ ] All 5 modified files updated correctly
- [ ] No syntax errors in Python files
- [ ] No syntax errors in XML files
- [ ] Migration script is idempotent
- [ ] Test files are comprehensive

### 2. File Verification

**New Files (11):**
- [ ] `models/payment_method.py`
- [ ] `data/payment_methods.xml`
- [ ] `migrations/19.0.1.0.0/post-migration.py`
- [ ] `tests/__init__.py`
- [ ] `tests/test_payment_method.py`
- [ ] `tests/test_account_move_payment.py`
- [ ] `tests/test_xml_generator_payment.py`
- [ ] `../test_phase1a_sinpe_integration.py`
- [ ] `../PHASE1A-SINPE-IMPLEMENTATION-COMPLETE.md`
- [ ] `../PHASE1A-QUICK-START-GUIDE.md`
- [ ] `../PHASE1A-DEPLOYMENT-CHECKLIST.md`

**Modified Files (6):**
- [ ] `models/__init__.py`
- [ ] `models/account_move.py`
- [ ] `models/xml_generator.py`
- [ ] `views/account_move_views.xml`
- [ ] `security/ir.model.access.csv`
- [ ] `__manifest__.py`

### 3. Database Backup

- [ ] Backup database before upgrade
  ```bash
  pg_dump gms_production > backup_pre_phase1a_$(date +%Y%m%d_%H%M%S).sql
  ```
- [ ] Verify backup file exists and is not empty
- [ ] Store backup in safe location

---

## Deployment Steps

### Step 1: Stop Odoo Service
```bash
sudo systemctl stop odoo
# OR
sudo service odoo stop
```
- [ ] Odoo service stopped
- [ ] Verify no users connected

### Step 2: Update Module Files
```bash
cd /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS
# Module files already in place
```
- [ ] All new files in correct locations
- [ ] All modified files updated
- [ ] File permissions correct (readable by Odoo user)

### Step 3: Upgrade Module
```bash
# Test mode first (optional but recommended)
odoo-bin -c odoo.conf -d gms_production -u l10n_cr_einvoice --test-enable --stop-after-init --log-level=test

# Production upgrade
odoo-bin -c odoo.conf -d gms_production -u l10n_cr_einvoice --stop-after-init
```
- [ ] No errors during upgrade
- [ ] Migration logs show invoice count updated
- [ ] Payment method catalog loaded (5 records)

### Step 4: Start Odoo Service
```bash
sudo systemctl start odoo
# OR
sudo service odoo start
```
- [ ] Service started successfully
- [ ] Check logs for errors
- [ ] Application accessible

---

## Post-Deployment Validation

### 1. Database Checks

**Payment Method Catalog:**
```sql
SELECT code, name, requires_transaction_id 
FROM l10n_cr_payment_method 
ORDER BY code;
```
Expected: 5 rows (01, 02, 03, 04, 06)

- [ ] 5 payment methods exist
- [ ] SINPE Móvil (06) has requires_transaction_id = true
- [ ] All other methods have requires_transaction_id = false

**Invoice Migration:**
```sql
SELECT 
    COUNT(*) as total_invoices,
    COUNT(l10n_cr_payment_method_id) as with_payment_method,
    COUNT(*) - COUNT(l10n_cr_payment_method_id) as without_payment_method
FROM account_move
WHERE move_type IN ('out_invoice', 'out_refund')
AND country_code = 'CR'
AND state = 'posted';
```

- [ ] All posted CR invoices have payment method
- [ ] without_payment_method = 0

### 2. UI Validation

**Invoice Form View:**
- [ ] Open existing invoice
- [ ] Payment method field visible (below payment terms)
- [ ] Payment method dropdown shows 5 options
- [ ] Transaction ID field hidden initially

**SINPE Móvil Test:**
- [ ] Select "06 - SINPE Móvil"
- [ ] Transaction ID field appears
- [ ] Clear payment method
- [ ] Transaction ID field disappears

**Tree View:**
- [ ] Payment method column available (optional)
- [ ] Can enable/disable column

**Search Filters:**
- [ ] "SINPE Móvil Payments" filter works
- [ ] "Card Payments" filter works
- [ ] "Cash Payments" filter works
- [ ] "Group By Payment Method" works

### 3. Functional Tests

**Test 1: Create Invoice with Efectivo**
- [ ] Create new customer invoice
- [ ] Select payment method: "01 - Efectivo"
- [ ] Don't enter transaction ID
- [ ] Confirm invoice
- [ ] ✅ Should succeed

**Test 2: Create Invoice with SINPE (Valid)**
- [ ] Create new customer invoice
- [ ] Select payment method: "06 - SINPE Móvil"
- [ ] Enter transaction ID: "123456789"
- [ ] Confirm invoice
- [ ] ✅ Should succeed

**Test 3: Create Invoice with SINPE (Invalid)**
- [ ] Create new customer invoice
- [ ] Select payment method: "06 - SINPE Móvil"
- [ ] Leave transaction ID empty
- [ ] Try to confirm invoice
- [ ] ❌ Should show error: "Transaction ID is required"

**Test 4: Default Payment Method**
- [ ] Create new customer invoice
- [ ] Don't select any payment method
- [ ] Confirm invoice
- [ ] ✅ Should auto-assign "01 - Efectivo"

### 4. XML Generation Tests

**Test XML Generation:**
- [ ] Create test invoice with SINPE Móvil + transaction ID
- [ ] Generate e-invoice document
- [ ] Generate XML
- [ ] Verify XML contains: `<MedioPago>06</MedioPago>`
- [ ] Verify XML contains: `<NumeroTransaccion>123456789</NumeroTransaccion>`

**Test Other Payment Methods:**
- [ ] Create invoice with Tarjeta (02)
- [ ] Generate XML
- [ ] Verify XML contains: `<MedioPago>02</MedioPago>`
- [ ] Verify XML does NOT contain: `<NumeroTransaccion>`

### 5. Security Tests

**Test User Access:**
- [ ] Login as regular user
- [ ] Can view payment methods (read)
- [ ] Cannot create payment methods
- [ ] Cannot edit payment methods

**Test Accountant Access:**
- [ ] Login as accountant
- [ ] Can view payment methods
- [ ] Can select payment methods on invoices
- [ ] Cannot create new payment method codes

**Test Manager Access:**
- [ ] Login as accounting manager
- [ ] Can create payment methods
- [ ] Can edit payment methods
- [ ] Can delete payment methods

---

## Performance Checks

- [ ] Invoice creation time < 2 seconds
- [ ] Invoice list loads < 3 seconds
- [ ] XML generation time < 5 seconds
- [ ] No database locks
- [ ] No memory leaks

---

## Rollback Plan (If Needed)

### Immediate Rollback

If critical errors occur:

1. **Stop Odoo:**
   ```bash
   sudo systemctl stop odoo
   ```

2. **Restore Database:**
   ```bash
   psql -U odoo -d postgres -c "DROP DATABASE gms_production;"
   psql -U odoo -d postgres -c "CREATE DATABASE gms_production;"
   psql -U odoo -d gms_production < backup_pre_phase1a_YYYYMMDD_HHMMSS.sql
   ```

3. **Restore Module Files:**
   ```bash
   git checkout HEAD~1 l10n_cr_einvoice/
   ```

4. **Restart Odoo:**
   ```bash
   sudo systemctl start odoo
   ```

- [ ] Rollback procedure tested (optional)
- [ ] Team knows rollback steps

---

## Communication

### Before Deployment
- [ ] Notify all users of scheduled maintenance
- [ ] Send email 24 hours before
- [ ] Send reminder 1 hour before

### After Deployment
- [ ] Send success notification
- [ ] Share Quick Start Guide
- [ ] Schedule training session (optional)
- [ ] Update documentation wiki

---

## Training Plan

### User Training (1 hour)
- [ ] Introduction to payment methods (10 min)
- [ ] Demo: Creating invoice with each method (20 min)
- [ ] Demo: SINPE Móvil with transaction ID (15 min)
- [ ] Q&A session (15 min)

### Materials Prepared
- [ ] Quick Start Guide distributed
- [ ] Quick Reference Card printed
- [ ] Video tutorial recorded (optional)
- [ ] FAQ document available

---

## Monitoring (First 7 Days)

### Daily Checks
- [ ] Day 1: Check for errors in logs
- [ ] Day 2: Verify payment methods being used
- [ ] Day 3: Review user feedback
- [ ] Day 4: Check XML generation success rate
- [ ] Day 5: Validate Hacienda submissions
- [ ] Day 6: Performance monitoring
- [ ] Day 7: Comprehensive review

### Metrics to Track
- [ ] Invoices created per day
- [ ] Payment method distribution
- [ ] SINPE Móvil usage rate
- [ ] Errors/validation failures
- [ ] User support tickets

---

## Success Criteria

### Technical Success
- [ ] 0 critical errors
- [ ] < 5 minor bugs
- [ ] All tests passing
- [ ] Migration successful
- [ ] XML validation 100% pass rate

### Business Success
- [ ] Users adopting payment methods
- [ ] SINPE Móvil usage increasing
- [ ] Compliance with Hacienda requirements
- [ ] No invoice posting delays
- [ ] Positive user feedback

---

## Known Issues & Workarounds

### Issue 1: Transaction ID Copy/Paste
**Problem:** Users might copy transaction ID with spaces
**Workaround:** Trim spaces in code (already implemented)

### Issue 2: Old Invoices Show "Efectivo"
**Problem:** Historical invoices may not reflect actual payment method
**Workaround:** Expected behavior - migration default
**Action:** Update important invoices manually if needed

### Issue 3: Multiple Payment Methods
**Problem:** Customer paid with 2 methods (e.g., card + cash)
**Workaround:** Select primary method, note others in comments
**Future:** Multi-payment support in Phase 4

---

## Sign-Off

**Deployment Completed:**
- Date: ___________________
- Time: ___________________
- Deployed by: ___________________

**Validation Completed:**
- Date: ___________________
- Validated by: ___________________

**Approved for Production:**
- Date: ___________________
- Approved by: ___________________

---

## Next Steps

- [ ] Monitor for 7 days
- [ ] Collect user feedback
- [ ] Fix any minor issues
- [ ] Plan Phase 1B deployment (Discount Codes)
- [ ] Schedule Hacienda sandbox testing

---

**Version:** 1.0
**Last Updated:** 2025-12-28
**Status:** Ready for Deployment
