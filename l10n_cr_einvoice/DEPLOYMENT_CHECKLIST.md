# 🚀 Production Deployment Checklist

## Pre-Deployment (Development Environment)

### ✅ Code Review
- [x] All fixes from review applied
- [x] move_id made optional for POS compatibility
- [x] pos_order_id field added
- [x] Computed fields implemented (partner, amount, currency, date)
- [x] XML generator supports both invoice and POS orders
- [x] Security rules updated

### ✅ Testing
- [ ] **Backend Unit Tests** - Run all tests and verify pass
- [ ] **POS E-Invoice Generation** - Create order, verify document created
- [ ] **Invoice E-Invoice Generation** - Post invoice, verify document created
- [ ] **XML Generation** - Check XML is v4.4 compliant
- [ ] **Digital Signature** - Verify XML signing works
- [ ] **Hacienda Submission (Sandbox)** - Test full flow in sandbox
- [ ] **Email Delivery** - Verify customer receives email
- [ ] **PDF Generation** - Check PDF has QR code
- [ ] **Offline Mode** - Test POS offline queue
- [ ] **Error Recovery** - Test FE→TE switch in POS
- [ ] **Touch Device** - Test on iPad/tablet
- [ ] **Keyboard Shortcuts** - Test F2/F4 on desktop

### ✅ Configuration Validation
- [ ] Company has valid Hacienda credentials
- [ ] Certificate uploaded and not expired
- [ ] Activity code (CIIU) set for company
- [ ] Default partner configured for POS
- [ ] POS configs have e-invoicing enabled
- [ ] Payment methods loaded (5 official)
- [ ] Discount codes loaded (11 official)
- [ ] CIIU codes loaded (100+)

---

## Staging Deployment

### ✅ Environment Setup
- [ ] Staging database created
- [ ] Module installed
- [ ] Test data populated (products, customers, partners)
- [ ] Sandbox credentials configured
- [ ] Test certificate uploaded

### ✅ Smoke Tests
- [ ] Module loads without errors
- [ ] Views accessible
- [ ] POS loads correctly
- [ ] Create test invoice → E-invoice generated
- [ ] Submit to sandbox → Accepted
- [ ] Create POS order → E-invoice generated

### ✅ User Acceptance Testing (UAT)
- [ ] Cashiers can use POS e-invoicing
- [ ] Accountants can create invoices
- [ ] Managers can view reports
- [ ] Customers receive emails
- [ ] Error messages are clear
- [ ] Performance is acceptable

---

## Production Deployment

### 🔴 Pre-Flight Checks
- [ ] ✅ All staging tests passed
- [ ] ✅ UAT sign-off received
- [ ] ✅ Backup created
- [ ] ✅ Rollback plan documented
- [ ] ✅ Maintenance window scheduled
- [ ] ✅ Users notified of deployment

### ✅ Deployment Steps

#### 1. Database Backup
\`\`\`bash
# Create backup before deployment
pg_dump your_database > backup_$(date +%Y%m%d_%H%M%S).sql
\`\`\`

#### 2. Module Installation
\`\`\`bash
# Update module
odoo-bin -d production_db -u l10n_cr_einvoice --stop-after-init

# Or via UI: Apps → Update Apps List → Upgrade
\`\`\`

#### 3. Configuration
- [ ] Set Hacienda environment to **PRODUCTION**
- [ ] Upload **PRODUCTION** certificate (not sandbox)
- [ ] Verify credentials are production (not sandbox)
- [ ] Enable auto-generation if desired
- [ ] Configure email SMTP settings

#### 4. Verification
- [ ] Module installed successfully
- [ ] No errors in log
- [ ] Views load correctly
- [ ] POS loads without issues
- [ ] Test e-invoice creation (use test customer)
- [ ] Submit to Hacienda production
- [ ] Verify acceptance

---

## Post-Deployment

### ✅ Immediate Verification (First Hour)
- [ ] Create 1-2 real invoices, verify e-invoice generated
- [ ] Create 1 POS order, verify e-invoice generated
- [ ] Check Hacienda acceptance
- [ ] Verify customer receives email
- [ ] Monitor error logs
- [ ] Check system performance

### ✅ First Day Monitoring
- [ ] Monitor e-invoice generation rate
- [ ] Check acceptance rate (should be >95%)
- [ ] Review error logs hourly
- [ ] Verify offline queue working (if applicable)
- [ ] Check email delivery rate
- [ ] Gather user feedback

### ✅ First Week Monitoring
- [ ] Daily acceptance rate review
- [ ] Weekly error analysis
- [ ] Performance metrics review
- [ ] User feedback survey
- [ ] Identify common issues
- [ ] Document workarounds

---

## Rollback Plan

### If Critical Issues Occur
1. **Stop creating new e-invoices**
   - Disable auto-generation in settings
   - Notify users to avoid e-invoicing

2. **Assess impact**
   - How many invoices affected?
   - Can they be manually fixed?
   - Is rollback necessary?

3. **Rollback procedure**
   \`\`\`bash
   # Restore database backup
   psql production_db < backup_YYYYMMDD_HHMMSS.sql
   
   # Or downgrade module
   odoo-bin -d production_db -u l10n_cr_einvoice --stop-after-init
   \`\`\`

4. **Communication**
   - Notify users of rollback
   - Explain next steps
   - Provide timeline for fix

---

## Key Metrics to Monitor

### Performance
- **E-Invoice Generation Time**: < 5 seconds average
- **Hacienda API Response Time**: < 10 seconds average
- **POS Transaction Time**: No noticeable increase

### Quality
- **Acceptance Rate**: > 95%
- **Error Rate**: < 5%
- **Email Delivery Rate**: > 98%

### Business
- **Daily E-Invoice Volume**: Track trend
- **FE vs TE Ratio**: Monitor split
- **Customer Complaints**: Track and resolve

---

## Support Contacts

### Technical Support
- **Email**: support@gms-cr.com
- **Phone**: [Your Phone]
- **On-Call**: [On-call rotation]

### Hacienda Support
- **API Issues**: [Hacienda support contact]
- **Certificate Issues**: [Certificate authority]

---

## Common Issues & Solutions

### Issue: Certificate expired
**Solution**: Upload new certificate in Settings → E-Invoicing

### Issue: Hacienda returns "Invalid ID"
**Solution**: Check customer ID format (remove dashes/spaces)

### Issue: POS order doesn't generate e-invoice
**Solution**: Check POS config has "Enable E-Invoicing" checked

### Issue: Email not delivered
**Solution**: Check SMTP settings in Settings → Technical → Email

---

## Success Criteria

Deployment is considered successful when:
- ✅ Acceptance rate > 95% for 7 consecutive days
- ✅ Zero critical bugs reported
- ✅ User satisfaction > 80%
- ✅ No performance degradation
- ✅ All key metrics within target

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Sign-off**: _______________

---

🎉 **Good luck with your deployment!**
