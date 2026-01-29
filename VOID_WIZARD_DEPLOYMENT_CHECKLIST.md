# Invoice Void Wizard - Deployment Checklist

## Pre-Deployment

### 1. Backup & Safety
- [ ] Create full database backup
  ```bash
  pg_dump -U odoo production_db > backup_$(date +%Y%m%d_%H%M%S).sql
  ```
- [ ] Backup file system (addons directory)
  ```bash
  tar -czf odoo_addons_backup.tar.gz /path/to/odoo/addons
  ```
- [ ] Document current module version (19.0.1.8.0)
- [ ] Create rollback plan document

### 2. Environment Verification
- [ ] Staging environment available
- [ ] Test database prepared
- [ ] SMTP configured for email testing
- [ ] Hacienda sandbox credentials ready
- [ ] SSL certificates valid

### 3. Dependencies Check
- [ ] Odoo version: 19.0
- [ ] Python version: 3.10+
- [ ] Required modules installed:
  - [ ] account
  - [ ] l10n_cr
  - [ ] sale
  - [ ] sale_subscription
  - [ ] mail
  - [ ] l10n_cr_einvoice (v19.0.1.8.0)

### 4. Code Review
- [ ] Review `gym_invoice_void_wizard.py` (746 lines)
- [ ] Review `gym_invoice_void_wizard_views.xml` (239 lines)
- [ ] Review `void_confirmation_email.xml` (277 lines)
- [ ] Verify `__init__.py` updated correctly
- [ ] Verify `__manifest__.py` updated to v19.0.1.9.0
- [ ] Verify `ir.model.access.csv` has new entries

---

## Staging Deployment

### 1. Deploy to Staging
```bash
# Copy files to staging
scp -r l10n_cr_einvoice staging:/opt/odoo/addons/

# Connect to staging
ssh staging

# Update module
/opt/odoo/odoo-bin -u l10n_cr_einvoice -d staging_db --stop-after-init

# Restart Odoo
sudo systemctl restart odoo
```

### 2. Verify Installation
- [ ] Module upgraded successfully (check logs)
- [ ] No errors in odoo logs
- [ ] Menu "Anular Factura" appears under Hacienda
- [ ] Wizard accessible from invoice action menu
- [ ] Form loads without errors
- [ ] Email template renders correctly

### 3. Functional Testing in Staging

#### Test 1: Simple Void
- [ ] Create test invoice
- [ ] Post invoice
- [ ] Open void wizard
- [ ] Select reason: "Error en facturación"
- [ ] Select refund: "Efectivo"
- [ ] Submit wizard
- [ ] Verify credit note created
- [ ] Verify e-invoice generated
- [ ] Check Hacienda submission (sandbox)
- [ ] Verify email sent (check inbox)

#### Test 2: Membership Cancellation
- [ ] Create invoice with membership
- [ ] Post invoice
- [ ] Open void wizard
- [ ] Select reason: "Cancelación de membresía"
- [ ] Enable "Cancel Membership"
- [ ] Enter cancellation reason
- [ ] Select refund: "Transferencia bancaria"
- [ ] Enter bank account
- [ ] Submit wizard
- [ ] Verify membership canceled
- [ ] Verify cancellation logged
- [ ] Check email includes membership notice

#### Test 3: All Refund Methods
- [ ] Test cash refund (verify email instructions)
- [ ] Test transfer refund (verify bank account required)
- [ ] Test credit refund (verify credit instructions)
- [ ] Test card refund (verify reversal timeline)
- [ ] Test no refund (verify courtesy message)

#### Test 4: Error Handling
- [ ] Try void on draft invoice (should fail with message)
- [ ] Try void on already voided invoice (should fail)
- [ ] Try membership cancel without reason (should fail)
- [ ] Try transfer without bank account (should fail)
- [ ] Simulate Hacienda failure (check error state)

### 4. Performance Testing
- [ ] Time 10 void operations: Average < 20 seconds
- [ ] Check database query count: < 15 queries
- [ ] Monitor memory usage: No leaks
- [ ] Verify transaction rollback on errors

### 5. User Acceptance Testing
- [ ] Accounting team tests workflow
- [ ] Customer service tests workflow
- [ ] Manager approves interface
- [ ] Gather feedback and document

---

## Production Deployment

### 1. Pre-Production Checks
- [ ] All staging tests passed
- [ ] User acceptance complete
- [ ] Documentation reviewed and approved
- [ ] Training materials prepared
- [ ] Team trained on new feature
- [ ] Deployment window scheduled (low-traffic time)
- [ ] Stakeholders notified

### 2. Deploy to Production
```bash
# Backup production database
./scripts/backup_production.sh

# Copy files to production
scp -r l10n_cr_einvoice production:/opt/odoo/addons/

# Connect to production
ssh production

# Stop Odoo (maintenance mode)
sudo systemctl stop odoo

# Update module
/opt/odoo/odoo-bin -u l10n_cr_einvoice -d production_db --stop-after-init

# Check logs for errors
tail -f /var/log/odoo/odoo.log

# Start Odoo
sudo systemctl start odoo

# Verify Odoo started
sudo systemctl status odoo
```

**Expected Downtime:** 5 minutes

### 3. Post-Deployment Verification
- [ ] Odoo started successfully
- [ ] No errors in logs
- [ ] Module version shows 19.0.1.9.0
- [ ] Menu appears for all users with permissions
- [ ] Wizard accessible from invoices

### 4. Smoke Tests (Production)
- [ ] Login as accounting user
- [ ] Navigate to invoices
- [ ] Open test invoice (non-critical)
- [ ] Access void wizard
- [ ] Verify form loads correctly
- [ ] Cancel wizard (don't void)
- [ ] Check email template renders

### 5. Monitor First Operations
- [ ] Monitor first void operation closely
- [ ] Verify credit note created correctly
- [ ] Check Hacienda submission (PRODUCTION API)
- [ ] Verify email sent to actual customer
- [ ] Review customer feedback
- [ ] Monitor error logs for 24 hours

---

## Post-Deployment

### 1. Documentation & Communication
- [ ] Update internal wiki
- [ ] Send announcement to team
- [ ] Share quick start guide
- [ ] Schedule training sessions
- [ ] Create support knowledge base articles

### 2. Monitoring Setup
- [ ] Set up void operation alerts
- [ ] Configure Hacienda failure alerts
- [ ] Monitor email delivery rates
- [ ] Track processing times
- [ ] Set up weekly metrics report

### 3. First Week Monitoring
- [ ] Review all void operations daily
- [ ] Collect user feedback
- [ ] Document any edge cases
- [ ] Track Hacienda acceptance rates
- [ ] Monitor error rates

### 4. Optimization (if needed)
- [ ] Analyze processing times
- [ ] Review error patterns
- [ ] Optimize slow operations
- [ ] Update documentation based on usage
- [ ] Address user feedback

---

## Rollback Plan (If Needed)

### When to Rollback
- Critical errors affecting business operations
- Data corruption issues
- Hacienda submission failures > 50%
- Security vulnerabilities discovered

### Rollback Steps
```bash
# 1. Stop Odoo
sudo systemctl stop odoo

# 2. Restore database backup
psql -U odoo production_db < backup_YYYYMMDD_HHMMSS.sql

# 3. Restore previous module version
cd /opt/odoo/addons
rm -rf l10n_cr_einvoice
tar -xzf l10n_cr_einvoice_v1.8.0.tar.gz

# 4. Downgrade module in Odoo
/opt/odoo/odoo-bin -u l10n_cr_einvoice -d production_db --stop-after-init

# 5. Start Odoo
sudo systemctl start odoo

# 6. Verify rollback
# Check module version is 19.0.1.8.0
# Verify old functionality works
```

**Rollback Time:** 15 minutes

### Post-Rollback
- [ ] Notify stakeholders
- [ ] Document rollback reason
- [ ] Fix issues in development
- [ ] Re-test in staging
- [ ] Plan re-deployment

---

## Training Checklist

### Accounting Team Training
- [ ] Schedule 1-hour training session
- [ ] Cover all void scenarios
- [ ] Practice each refund method
- [ ] Demonstrate error handling
- [ ] Review audit trails
- [ ] Q&A session
- [ ] Provide quick reference card

### Customer Service Training
- [ ] Schedule 30-minute overview
- [ ] Explain when to use wizard
- [ ] Show how to check void status
- [ ] Review email communications
- [ ] Practice responding to customer questions
- [ ] Provide FAQ document

### Manager Training
- [ ] Schedule 30-minute demo
- [ ] Show reporting and analytics
- [ ] Explain refund tracking
- [ ] Review audit trail access
- [ ] Discuss approval workflows (future)

---

## Success Metrics

### Week 1 Targets
- [ ] Zero critical errors
- [ ] 95%+ Hacienda acceptance rate
- [ ] 90%+ email delivery rate
- [ ] Average processing time < 20 seconds
- [ ] User satisfaction score > 4/5

### Month 1 Targets
- [ ] 50+ successful void operations
- [ ] < 5% error rate
- [ ] User satisfaction score > 4.5/5
- [ ] Zero customer complaints about process
- [ ] Training completion: 100% of accounting team

---

## Contact Information

### Deployment Team
- **Technical Lead:** [Name]
- **Database Admin:** [Name]
- **QA Lead:** [Name]
- **Product Owner:** [Name]

### Support Contacts
- **Technical Issues:** support@gms-cr.com
- **Business Questions:** accounting@gms-cr.com
- **Emergency:** [Phone Number]

### Escalation Path
1. Support Team (first contact)
2. Technical Lead (if unresolved)
3. Database Admin (if database issues)
4. Product Owner (if business decision needed)

---

## Deployment Sign-Off

### Pre-Deployment
- [ ] **Technical Lead:** Staging tests passed ________________
- [ ] **QA Lead:** Quality assurance complete ________________
- [ ] **Product Owner:** Feature approved ________________
- [ ] **Database Admin:** Backup verified ________________

### Production Deployment
- [ ] **Technical Lead:** Deployment complete ________________
- [ ] **Database Admin:** Database healthy ________________
- [ ] **QA Lead:** Smoke tests passed ________________

### Post-Deployment
- [ ] **Support Team:** Monitoring active ________________
- [ ] **Training Lead:** Team trained ________________
- [ ] **Product Owner:** Feature live ________________

---

## Deployment Log

| Date | Time | Action | Result | By |
|------|------|--------|--------|-----|
| | | Pre-deployment backup | | |
| | | Deploy to staging | | |
| | | Staging tests | | |
| | | Deploy to production | | |
| | | Production verification | | |
| | | First operation monitored | | |

---

**Checklist Version:** 1.0
**Last Updated:** December 31, 2024
**Module Version:** 19.0.1.9.0
**Deployment Status:** READY

---

## Quick Commands Reference

### Check Module Version
```bash
grep "version" /opt/odoo/addons/l10n_cr_einvoice/__manifest__.py
```

### View Odoo Logs
```bash
tail -f /var/log/odoo/odoo.log
```

### Restart Odoo
```bash
sudo systemctl restart odoo
```

### Database Backup
```bash
pg_dump -U odoo production_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Check Odoo Status
```bash
sudo systemctl status odoo
```

---

**Ready for Deployment!**
