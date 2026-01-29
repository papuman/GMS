# 🚀 GMS Production Deployment Checklist

**Version:** 1.0.0
**Date:** 2025-12-28
**Status:** Ready for Use

---

## Pre-Deployment Checklist

### ✅ Documentation Review
- [ ] Read [Production Readiness Report](../../PRODUCTION-READINESS-REPORT.md)
- [ ] Review [100% Compliance Report](../../100-PERCENT-COMPLIANCE-ACHIEVED.md)
- [ ] Understand rollback procedures

### ✅ System Requirements
- [ ] Ubuntu 22.04 LTS (or compatible OS)
- [ ] PostgreSQL 14+ installed
- [ ] Python 3.10+ installed
- [ ] 4GB+ RAM available
- [ ] 20GB+ disk space
- [ ] SSL certificates ready (for production domain)

### ✅ Backup & Safety
- [ ] Current database backed up
- [ ] Backup restoration tested
- [ ] Rollback plan documented
- [ ] Emergency contacts list ready

### ✅ Configuration Files Ready
- [ ] `odoo.conf` configured
- [ ] Database connection settings
- [ ] Admin password changed from default
- [ ] Email server configured
- [ ] SSL/TLS certificates installed

---

## Deployment Steps

### Step 1: Backup Current System
```bash
# Create timestamped backup
pg_dump gms > gms_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup created
ls -lh gms_backup_*.sql
```

- [ ] Backup completed successfully
- [ ] Backup file size looks correct
- [ ] Backup timestamp noted: __________________

### Step 2: Stop Odoo Service
```bash
# Stop the service
sudo systemctl stop odoo

# Verify it's stopped
sudo systemctl status odoo
```

- [ ] Odoo service stopped
- [ ] No running processes confirmed

### Step 3: Update Module Files
```bash
# Navigate to module directory
cd /path/to/odoo/addons/

# Pull latest changes (if using git)
git pull origin main

# Or copy updated module files
rsync -av /path/to/l10n_cr_einvoice/ ./l10n_cr_einvoice/
```

- [ ] Module files updated
- [ ] File permissions correct
- [ ] Ownership correct (odoo:odoo)

### Step 4: Upgrade Module
```bash
# Run module upgrade
./odoo-bin -u l10n_cr_einvoice -d gms --stop-after-init

# Check for errors in output
```

- [ ] Upgrade completed without errors
- [ ] No warnings in output
- [ ] Database migrations successful

### Step 5: Start Odoo Service
```bash
# Start the service
sudo systemctl start odoo

# Verify it's running
sudo systemctl status odoo

# Check logs
sudo journalctl -u odoo -f
```

- [ ] Service started successfully
- [ ] No errors in logs
- [ ] Web interface accessible

### Step 6: Clear Browser Cache
```bash
# Instruct all users to:
# - Press Ctrl+Shift+Delete
# - Or Ctrl+F5 (hard refresh)
```

- [ ] Users notified to clear cache
- [ ] Admin browser cache cleared

---

## Post-Deployment Verification

### Module Verification
- [ ] Navigate to Apps
- [ ] Search for "l10n_cr_einvoice"
- [ ] Verify version shows: 19.0.1.0.0
- [ ] Status shows: Installed

### E-Invoice Module Tests
- [ ] Navigate to Accounting → Hacienda (CR)
- [ ] Kanban view displays correctly
- [ ] Badge colors correct (blue, green, yellow, red)
- [ ] Open "Batch Generate" wizard - no errors
- [ ] Open "Batch Submit" wizard - no errors
- [ ] Open "Batch Check Status" wizard - no errors
- [ ] Create test e-invoice document
- [ ] Verify sequence numbering works

### Membership Tests
- [ ] Navigate to Subscriptions
- [ ] View active subscriptions (should see test data)
- [ ] Create new subscription order
- [ ] Verify 13% IVA calculated correctly
- [ ] Check next invoice date calculated

### POS Tests
- [ ] Navigate to Point of Sale
- [ ] Open new POS session
- [ ] Add product to cart
- [ ] Verify 13% IVA shows correctly
- [ ] Process test transaction
- [ ] Close POS session

### Portal Tests
- [ ] Login as portal user
- [ ] View subscriptions
- [ ] Access invoices
- [ ] Download invoice PDF
- [ ] Verify data isolation (only own data visible)

### Security Verification
- [ ] Wizard security rules working (no access errors)
- [ ] Portal users cannot modify partner records (correct)
- [ ] Portal users cannot access payment records directly (correct)
- [ ] Admin users have full access

---

## Performance Checks

### System Performance
- [ ] Page load times < 3 seconds
- [ ] Database queries optimized
- [ ] No memory leaks
- [ ] CPU usage normal

### Logs Review
```bash
# Check for errors
sudo journalctl -u odoo -f | grep -i error

# Check for warnings
sudo journalctl -u odoo -f | grep -i warning
```

- [ ] No critical errors in logs
- [ ] No unexpected warnings
- [ ] All services responding

---

## User Acceptance Testing

### End User Testing
- [ ] Gym manager can create memberships
- [ ] Cashier can process POS sales
- [ ] Members can access portal
- [ ] Invoices generate correctly
- [ ] Emails send properly

### Integration Testing
- [ ] CRM lead-to-member workflow works
- [ ] Subscription billing triggers correctly
- [ ] E-invoice submission works
- [ ] Tax calculations accurate

---

## Go-Live Checklist

### Final Checks
- [ ] All tests passed
- [ ] Users trained
- [ ] Support team ready
- [ ] Monitoring configured
- [ ] Backup schedule active

### Communication
- [ ] Users notified of go-live
- [ ] Support contacts shared
- [ ] Known issues documented
- [ ] FAQ prepared

### Monitoring (First 24 Hours)
- [ ] Monitor error logs continuously
- [ ] Track user login success rate
- [ ] Verify automated processes running
- [ ] Check email delivery
- [ ] Validate tax calculations

---

## Rollback Procedure (If Needed)

### When to Rollback
- Critical functionality broken
- Data corruption detected
- Security vulnerability found
- Unrecoverable errors

### Rollback Steps
```bash
# 1. Stop Odoo
sudo systemctl stop odoo

# 2. Restore database
dropdb gms
createdb gms
psql gms < gms_backup_YYYYMMDD_HHMMSS.sql

# 3. Restore previous code (if needed)
cd /path/to/odoo/addons
git checkout HEAD~1 l10n_cr_einvoice/

# 4. Start Odoo
sudo systemctl start odoo
```

- [ ] Rollback completed
- [ ] System functional
- [ ] Users notified
- [ ] Incident documented

---

## Post-Deployment Tasks

### Day 1
- [ ] Monitor all logs
- [ ] Verify all scheduled actions running
- [ ] Check automated billing
- [ ] Validate e-invoice submissions
- [ ] Respond to user feedback

### Week 1
- [ ] Review error logs daily
- [ ] Track user adoption
- [ ] Document any issues
- [ ] Fine-tune configuration
- [ ] Collect user feedback

### Month 1
- [ ] Performance review
- [ ] User satisfaction survey
- [ ] System optimization
- [ ] Training refinement
- [ ] Documentation updates

---

## Success Criteria

Deployment is successful when:
- ✅ All modules load without errors
- ✅ All wizards open correctly
- ✅ Sequences generate properly
- ✅ Tax calculations accurate (13%)
- ✅ E-invoices submit to Hacienda
- ✅ No critical bugs reported
- ✅ Users can perform daily tasks
- ✅ Performance acceptable

---

## Support Contacts

### Technical Support
- **Name:** ________________
- **Email:** ________________
- **Phone:** ________________
- **Hours:** ________________

### Emergency Contact
- **Name:** ________________
- **Email:** ________________
- **Phone:** ________________
- **Available:** 24/7

---

## Sign-Off

### Deployment Team
- [ ] Technical Lead: ________________ Date: ________
- [ ] System Admin: _________________ Date: ________
- [ ] QA Lead: _____________________ Date: ________

### Stakeholder Approval
- [ ] Business Owner: _______________ Date: ________
- [ ] Gym Manager: _________________ Date: ________

---

**Deployment Date:** __________________
**Deployment Time:** __________________
**Completed By:** __________________
**Status:** ⬜ Success | ⬜ Partial | ⬜ Rolled Back

---

**Document Status:** READY FOR USE  
**Last Updated:** 2025-12-28  
**Version:** 1.0.0

