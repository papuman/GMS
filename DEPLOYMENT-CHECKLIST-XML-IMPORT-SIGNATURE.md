# Costa Rica E-Invoicing: XML Import & Digital Signature Deployment Checklist

**Version:** 1.0.0
**Date:** 2025-12-29
**Features:** XML Import (Days 1-12) & Digital Signature (Phase 2)
**Status:** Production Ready

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [XML Import Feature Deployment](#xml-import-feature-deployment)
3. [Digital Signature Feature Deployment](#digital-signature-feature-deployment)
4. [Post-Deployment Checklist](#post-deployment-checklist)
5. [Production Validation](#production-validation)
6. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Checklist

### Code Review Requirements
**Responsible:** Technical Lead | **Due:** Before deployment

- [ ] **XML Import Code Review**
  - [ ] Review `/l10n_cr_einvoice/models/einvoice_xml_parser.py` (619 lines)
  - [ ] Review `/l10n_cr_einvoice/models/einvoice_import_batch.py` (329 lines)
  - [ ] Review `/l10n_cr_einvoice/models/einvoice_import_error.py` (557 lines)
  - [ ] Review `/l10n_cr_einvoice/wizards/einvoice_import_wizard.py` (643 lines)
  - [ ] Verify error handling for all 18 error types
  - [ ] Check batch commit logic (every 50 records)
  - **Success Criteria:** No critical code smells, proper error handling, optimized queries

- [ ] **Digital Signature Code Review**
  - [ ] Review `/l10n_cr_einvoice/models/certificate_manager.py`
  - [ ] Review `/l10n_cr_einvoice/models/xml_signer.py`
  - [ ] Review `/l10n_cr_einvoice/models/hacienda_api.py`
  - [ ] Verify XMLDSig implementation matches XAdES-EPES spec
  - [ ] Check certificate validation logic
  - [ ] Verify API retry logic (exponential backoff)
  - **Success Criteria:** Standards-compliant, secure key handling, proper retry logic

### Testing Requirements
**Responsible:** QA Lead | **Due:** Before deployment

- [ ] **Unit Tests Passed**
  - [ ] XML Parser tests: 25+ tests passing
  - [ ] Integration tests: 15+ tests passing
  - [ ] Certificate manager tests passing
  - [ ] XML signer tests passing
  - [ ] Hacienda API tests passing
  - **Success Criteria:** 100% of unit tests passing

- [ ] **Integration Tests Passed**
  - [ ] End-to-end XML import (10 invoices)
  - [ ] Duplicate detection working
  - [ ] Partner/product auto-creation working
  - [ ] Amount validation accurate (±0.50 tolerance)
  - [ ] Error recovery and retry working
  - [ ] Certificate signing workflow complete
  - [ ] Hacienda sandbox submission successful
  - **Success Criteria:** All workflows execute without errors

- [ ] **Performance Tests Passed**
  - [ ] XML import: 50+ invoices/minute achieved
  - [ ] Memory usage: <500MB per batch
  - [ ] Large batch (100+ invoices) processed successfully
  - [ ] Signing performance: <2 seconds per invoice
  - **Success Criteria:** Meets or exceeds performance targets

### Documentation Verification
**Responsible:** Documentation Manager | **Due:** Before deployment

- [ ] **User Documentation Complete**
  - [ ] XML Import User Guide reviewed (`XML_IMPORT_USER_GUIDE.md`)
  - [ ] Provider export guides tested (GTI, FACTURATica, TicoPay, Alegra)
  - [ ] Certificate upload instructions clear
  - [ ] Error handling procedures documented
  - [ ] FAQ addresses common questions
  - **Success Criteria:** Non-technical user can complete import without support

- [ ] **Admin Documentation Complete**
  - [ ] XML Import Admin Guide reviewed (`XML_IMPORT_ADMIN_GUIDE.md`)
  - [ ] Troubleshooting guides tested
  - [ ] Performance optimization documented
  - [ ] Database schema documented
  - [ ] API reference complete
  - [ ] Certificate configuration documented
  - [ ] Hacienda API setup documented
  - **Success Criteria:** Admin can configure, troubleshoot, and maintain features

### Security Audit Items
**Responsible:** Security Lead | **Due:** Before deployment

- [ ] **Access Control Review**
  - [ ] Import wizard restricted to invoice users
  - [ ] Batch management restricted to managers
  - [ ] Error logs contain no sensitive data
  - [ ] Certificate private keys encrypted at rest
  - [ ] API credentials stored securely
  - [ ] Password fields properly masked
  - **Success Criteria:** Follows least-privilege principle, no data leakage

- [ ] **Data Protection Review**
  - [ ] Original XML stored securely (5-year retention)
  - [ ] Customer data encryption verified
  - [ ] Certificate data encryption verified
  - [ ] XML parsing prevents XXE attacks
  - [ ] No SQL injection vulnerabilities
  - [ ] CSRF protection enabled
  - **Success Criteria:** Passes security scan with no critical issues

- [ ] **Certificate Security Review**
  - [ ] Private keys never logged
  - [ ] Certificate passwords hashed
  - [ ] Certificate expiry warnings implemented
  - [ ] Certificate validation comprehensive
  - [ ] Signature verification secure
  - **Success Criteria:** Meets cryptographic best practices

### Performance Validation
**Responsible:** Performance Engineer | **Due:** Before deployment

- [ ] **XML Import Performance**
  - [ ] Baseline test: 100 invoices in <2 minutes
  - [ ] Stress test: 1,000 invoices in <20 minutes
  - [ ] Memory test: <500MB for 1,000 invoices
  - [ ] Database indexes created
  - [ ] Query optimization verified
  - **Success Criteria:** 50-60 invoices/minute sustained

- [ ] **Digital Signature Performance**
  - [ ] Single signature: <2 seconds
  - [ ] Batch signing (50 invoices): <2 minutes
  - [ ] Hacienda API response: <5 seconds average
  - [ ] Retry logic doesn't cause delays
  - **Success Criteria:** No user-noticeable delays

### Backup Procedures
**Responsible:** System Admin | **Due:** Before deployment

- [ ] **Full System Backup**
  - [ ] Database backup created: `gms_backup_YYYYMMDD_HHMMSS.sql`
  - [ ] Backup size verified: ___________ MB
  - [ ] Backup restoration tested successfully
  - [ ] Backup stored off-site
  - **Success Criteria:** Can restore to pre-deployment state in <30 minutes

- [ ] **Module Backup**
  - [ ] Current `l10n_cr_einvoice` module backed up
  - [ ] Git commit hash noted: ___________
  - [ ] Configuration files backed up
  - **Success Criteria:** Can revert code changes in <10 minutes

---

## XML Import Feature Deployment

### Database Migration Steps
**Responsible:** Database Admin | **Estimated Time:** 15 minutes

- [ ] **Pre-Migration Checks**
  - [ ] PostgreSQL version ≥ 14.0: ___________
  - [ ] Available disk space ≥ 5GB: ___________
  - [ ] Database connections < 80% of max
  - [ ] Backup completed (reference timestamp): ___________
  - **Success Criteria:** Environment ready for migration

- [ ] **Execute Migration**
  ```bash
  # Stop Odoo service
  sudo systemctl stop odoo

  # Run module upgrade
  ./odoo-bin -u l10n_cr_einvoice -d gms --stop-after-init

  # Check for migration errors
  tail -n 100 /var/log/odoo/odoo.log | grep -i error
  ```
  - [ ] Migration command executed
  - [ ] No errors in output
  - [ ] New tables created:
    - [ ] `l10n_cr_einvoice_import_batch`
    - [ ] `l10n_cr_einvoice_import_error`
  - [ ] `account_move` table extended with historical fields
  - **Success Criteria:** All database objects created without errors

- [ ] **Post-Migration Verification**
  ```sql
  -- Verify tables exist
  SELECT tablename FROM pg_tables
  WHERE tablename LIKE 'l10n_cr%import%';

  -- Verify indexes created
  SELECT indexname FROM pg_indexes
  WHERE tablename = 'account_move'
  AND indexname LIKE '%clave%';
  ```
  - [ ] All expected tables exist
  - [ ] All indexes created
  - [ ] Foreign keys established
  - **Success Criteria:** Database schema matches documentation

### Module Update Procedure
**Responsible:** System Admin | **Estimated Time:** 10 minutes

- [ ] **File Deployment**
  ```bash
  # Copy module files
  rsync -av /path/to/l10n_cr_einvoice/ /opt/odoo/addons/l10n_cr_einvoice/

  # Set permissions
  chown -R odoo:odoo /opt/odoo/addons/l10n_cr_einvoice
  chmod -R 755 /opt/odoo/addons/l10n_cr_einvoice
  ```
  - [ ] All files copied successfully
  - [ ] Ownership correct (odoo:odoo)
  - [ ] Permissions correct (755)
  - [ ] No missing files reported
  - **Success Criteria:** Module files match source repository

- [ ] **Restart Odoo**
  ```bash
  # Start Odoo service
  sudo systemctl start odoo

  # Verify service running
  sudo systemctl status odoo

  # Monitor logs for startup errors
  sudo journalctl -u odoo -f
  ```
  - [ ] Service started successfully
  - [ ] No errors in startup logs
  - [ ] Web interface accessible
  - [ ] Module shows as installed
  - **Success Criteria:** System operational with new module version

### Configuration Requirements
**Responsible:** Configuration Manager | **Estimated Time:** 20 minutes

- [ ] **Tax Configuration**
  - [ ] Navigate to: Accounting → Configuration → Taxes
  - [ ] Verify tax rates exist:
    - [ ] IVA 13% (amount: 13.0, type: sale)
    - [ ] IVA 4% (amount: 4.0, type: sale)
    - [ ] IVA 2% (amount: 2.0, type: sale)
    - [ ] IVA 1% (amount: 1.0, type: sale)
    - [ ] Exento 0% (amount: 0.0, type: sale)
  - **Success Criteria:** All Costa Rica tax rates configured

- [ ] **Currency Activation**
  - [ ] Navigate to: Accounting → Configuration → Currencies
  - [ ] Activate currencies:
    - [ ] CRC - Costa Rican Colón (default)
    - [ ] USD - US Dollar
    - [ ] EUR - Euro
  - [ ] Set exchange rate provider (if needed)
  - **Success Criteria:** All required currencies active

- [ ] **Payment Methods**
  - [ ] Navigate to: Accounting → Configuration
  - [ ] Verify Costa Rica payment methods exist:
    - [ ] 01 - Efectivo (Cash)
    - [ ] 02 - Tarjeta (Card)
    - [ ] 03 - Cheque
    - [ ] 04 - Transferencia (Transfer)
    - [ ] 05 - Otros (Other)
  - **Success Criteria:** All payment methods available

- [ ] **Access Rights Configuration**
  - [ ] Navigate to: Settings → Users & Companies → Groups
  - [ ] Grant import permissions:
    - [ ] Invoice users: Read/Write on import batches and errors
    - [ ] Account managers: Full access including delete
  - [ ] Test access with non-admin user
  - **Success Criteria:** Proper role-based access control

### Testing with Sample Data (10-20 invoices)
**Responsible:** QA Engineer | **Estimated Time:** 30 minutes

- [ ] **Small Batch Test**
  - [ ] Prepare test ZIP with 10-20 XMLs (mixed document types: FE, TE, NC, ND)
  - [ ] Navigate to: Hacienda → Import → Import Historical Invoices
  - [ ] Upload ZIP file
  - [ ] Select provider: "Test Provider"
  - [ ] Enable options:
    - [ ] Skip Duplicates: ON
    - [ ] Auto-Create Customers: ON
    - [ ] Auto-Create Products: ON
    - [ ] Validate Signatures: OFF
  - [ ] Click "Start Import"
  - [ ] Monitor progress bar completion
  - [ ] Review results summary
  - **Success Criteria:**
    - All 10-20 invoices imported successfully (0 errors)
    - Processing time <1 minute
    - Partners auto-created as needed
    - Products auto-created as needed

- [ ] **Duplicate Detection Test**
  - [ ] Re-upload same ZIP file
  - [ ] Verify "Skipped (Duplicates)" count = 10-20
  - [ ] Verify "Successful" count = 0
  - [ ] Check no duplicate invoices created in database
  - **Success Criteria:** Perfect duplicate detection (0 duplicates created)

- [ ] **Error Handling Test**
  - [ ] Create ZIP with 1 invalid XML
  - [ ] Import and verify error logged
  - [ ] Navigate to: Hacienda → Import → Import Errors
  - [ ] Open error record
  - [ ] Verify error categorization correct
  - [ ] Verify suggested action displayed
  - [ ] Test "Download XML" button
  - **Success Criteria:** Error properly logged and actionable

### Testing with Medium Batch (100-200 invoices)
**Responsible:** QA Engineer | **Estimated Time:** 1 hour

- [ ] **Medium Batch Test**
  - [ ] Prepare test ZIP with 100-200 XMLs
  - [ ] Import using same procedure as small batch
  - [ ] Monitor system resources during import:
    - [ ] CPU usage stays <80%: ___________
    - [ ] Memory usage stays <500MB: ___________
    - [ ] No database connection errors
  - [ ] Record processing time: ___________ minutes
  - [ ] Calculate speed: ___________ invoices/minute
  - **Success Criteria:**
    - >95% success rate
    - Speed ≥50 invoices/minute
    - No system errors

- [ ] **Partner/Product Auto-Creation Test**
  - [ ] Note count before: Partners: _____ Products: _____
  - [ ] Import batch with new partners/products
  - [ ] Note count after: Partners: _____ Products: _____
  - [ ] Verify new partners have:
    - [ ] Correct VAT number
    - [ ] Correct name
    - [ ] Correct identification type
    - [ ] Customer rank set
  - [ ] Verify new products have:
    - [ ] Correct Cabys code
    - [ ] Correct description
    - [ ] Default unit price
  - **Success Criteria:** All entities created with complete data

- [ ] **Amount Validation Test**
  - [ ] Import batch and check for amount mismatch warnings
  - [ ] Review 5 random invoices:
    - [ ] Invoice 1: Odoo total matches XML ±0.50
    - [ ] Invoice 2: Odoo total matches XML ±0.50
    - [ ] Invoice 3: Odoo total matches XML ±0.50
    - [ ] Invoice 4: Odoo total matches XML ±0.50
    - [ ] Invoice 5: Odoo total matches XML ±0.50
  - **Success Criteria:** All amounts within tolerance

### Testing with Large Batch (1000+ invoices)
**Responsible:** Performance Engineer | **Estimated Time:** 2 hours

- [ ] **Large Batch Test**
  - [ ] Prepare test ZIP with 1,000+ XMLs
  - [ ] Record start time: ___________
  - [ ] Import batch
  - [ ] Monitor system continuously:
    - [ ] CPU usage: ___________
    - [ ] Memory usage: ___________
    - [ ] Database connections: ___________
    - [ ] Disk I/O: ___________
  - [ ] Record end time: ___________
  - [ ] Calculate total duration: ___________ minutes
  - [ ] Calculate speed: ___________ invoices/minute
  - **Success Criteria:**
    - Duration <20 minutes for 1,000 invoices
    - Speed ≥50 invoices/minute
    - Memory <500MB
    - No crashes or errors

- [ ] **Batch Management Test**
  - [ ] Navigate to: Hacienda → Import → Import Batches
  - [ ] Open batch record
  - [ ] Verify statistics:
    - [ ] Total files count correct
    - [ ] Success count correct
    - [ ] Failed count correct
    - [ ] Progress percentage = 100%
  - [ ] Click "View Invoices" button
  - [ ] Verify all invoices linked to batch
  - [ ] Click "Export Error Report" (if errors exist)
  - [ ] Verify CSV download works
  - **Success Criteria:** Batch tracking accurate and complete

- [ ] **Database Performance Test**
  ```sql
  -- Check query performance
  EXPLAIN ANALYZE
  SELECT * FROM account_move
  WHERE l10n_cr_original_clave = '50601010100010120250001012345678901234567890123456789012345678901';

  -- Should use index, <10ms execution
  ```
  - [ ] Clave lookup uses index
  - [ ] Query execution <10ms
  - [ ] No table scans
  - **Success Criteria:** Optimal query performance maintained

### XML Import Rollback Plan
**Responsible:** System Admin | **Execution Time:** 30 minutes

- [ ] **Rollback Procedure Documented**
  ```bash
  # 1. Stop Odoo
  sudo systemctl stop odoo

  # 2. Restore database backup
  dropdb gms
  createdb gms
  psql gms < gms_backup_YYYYMMDD_HHMMSS.sql

  # 3. Restore previous module code
  cd /opt/odoo/addons
  git checkout HEAD~1 l10n_cr_einvoice/

  # 4. Start Odoo
  sudo systemctl start odoo
  ```
  - [ ] Procedure tested in staging
  - [ ] Estimated rollback time: ___________ minutes
  - [ ] Communication plan ready
  - **Success Criteria:** Can rollback in <30 minutes with zero data loss

---

## Digital Signature Feature Deployment

### Certificate Setup Requirements
**Responsible:** Security Admin | **Estimated Time:** 30 minutes

- [ ] **Certificate Acquisition**
  - [ ] Digital certificate obtained from authorized CA
  - [ ] Certificate format: PKCS#12 (.p12) or PEM (.crt + .key)
  - [ ] Certificate validity verified: Valid from _____ to _____
  - [ ] Certificate issued to: _____________________
  - [ ] Certificate includes private key
  - [ ] Certificate password available: ___________
  - **Success Criteria:** Valid certificate ready for deployment

- [ ] **Certificate Validation**
  ```bash
  # For PKCS#12
  openssl pkcs12 -info -in certificate.p12

  # For PEM
  openssl x509 -in certificate.crt -text -noout
  openssl rsa -in private_key.key -check
  ```
  - [ ] Certificate not expired
  - [ ] Certificate not yet invalid
  - [ ] Private key matches certificate
  - [ ] Certificate chain complete
  - **Success Criteria:** Certificate cryptographically valid

- [ ] **Certificate Upload**
  - [ ] Navigate to: Settings → Accounting → Costa Rica Electronic Invoicing
  - [ ] Upload certificate file
  - [ ] Enter certificate password
  - [ ] For PEM: Upload separate private key file
  - [ ] Click "Save"
  - [ ] Verify certificate info displays:
    - [ ] Subject: _____________________
    - [ ] Issuer: _____________________
    - [ ] Valid from: _____________________
    - [ ] Valid until: _____________________
  - [ ] Verify no expiry warning (unless <30 days)
  - **Success Criteria:** Certificate loaded and validated successfully

### Sandbox Environment Configuration
**Responsible:** Configuration Manager | **Estimated Time:** 20 minutes

- [ ] **Hacienda Sandbox Registration**
  - [ ] Register at: https://www.hacienda.go.cr/ate
  - [ ] Obtain sandbox credentials:
    - [ ] Username (cpj-xxx-xxxxxx): _____________________
    - [ ] Password: _____________________
  - [ ] Test credentials received
  - **Success Criteria:** Sandbox account active

- [ ] **Sandbox Configuration**
  - [ ] Navigate to: Settings → Accounting → Costa Rica Electronic Invoicing
  - [ ] Select Hacienda Environment: **Sandbox**
  - [ ] Enter API Credentials:
    - [ ] Username: _____________________
    - [ ] Password: _____________________
  - [ ] Click "Test Connection"
  - [ ] Verify success message: "Connection successful"
  - **Success Criteria:** Sandbox API connection verified

- [ ] **Emisor Location Configuration**
  - [ ] Enter location code (8 digits): _____________________
  - [ ] Format: Provincia-Canton-Distrito-Barrio
  - [ ] Example: 01010100 for San José
  - [ ] Verify code valid in Hacienda database
  - **Success Criteria:** Location properly configured

### API Credential Setup
**Responsible:** Configuration Manager | **Estimated Time:** 15 minutes

- [ ] **Production API Credentials** (if deploying to production)
  - [ ] Request production credentials from Hacienda
  - [ ] Receive production username: _____________________
  - [ ] Receive production password: _____________________
  - [ ] Store credentials securely
  - **Success Criteria:** Production credentials ready (not yet configured)

- [ ] **Connection Testing**
  ```bash
  # Test API connection
  curl -X GET \
    -u "username:password" \
    https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1/recepcion
  ```
  - [ ] API responds with 200 OK or expected error
  - [ ] Credentials accepted
  - [ ] Network connectivity confirmed
  - **Success Criteria:** API accessible and credentials valid

### Signing Workflow Testing
**Responsible:** QA Engineer | **Estimated Time:** 45 minutes

- [ ] **Generate Test Invoice**
  - [ ] Create test invoice in Odoo
  - [ ] Customer: Test customer with valid cedula
  - [ ] Products: 2-3 line items
  - [ ] Taxes: 13% IVA applied
  - [ ] Post invoice
  - **Success Criteria:** Valid invoice posted

- [ ] **Generate E-Invoice Document**
  - [ ] From invoice, click "E-Invoicing" → "Generate XML"
  - [ ] Verify XML content populated
  - [ ] Download XML and inspect structure:
    - [ ] Root element correct (FacturaElectronica)
    - [ ] Clave present (50 digits)
    - [ ] NumeroConsecutivo formatted correctly
    - [ ] Emisor data complete
    - [ ] Receptor data complete
    - [ ] Line items present
    - [ ] Totals calculated correctly
  - **Success Criteria:** Valid v4.4 XML generated

- [ ] **Sign XML**
  - [ ] Click "Sign XML" button
  - [ ] Wait for completion (<5 seconds)
  - [ ] Verify state changed to "Signed"
  - [ ] Download signed XML
  - [ ] Inspect signature element:
    - [ ] `<Signature>` element present
    - [ ] `<SignedInfo>` contains correct algorithm
    - [ ] `<SignatureValue>` populated
    - [ ] `<KeyInfo>` contains certificate
  - **Success Criteria:** Valid XMLDSig signature added

- [ ] **Verify Signature Structure**
  ```bash
  # Extract signature from XML
  xmllint --xpath "//*[local-name()='Signature']" signed.xml
  ```
  - [ ] Signature namespace correct: http://www.w3.org/2000/09/xmldsig#
  - [ ] Canonicalization method: C14N
  - [ ] Signature method: RSA-SHA256
  - [ ] Digest method: SHA-256
  - [ ] Transform: Enveloped signature
  - **Success Criteria:** Signature complies with XAdES-EPES standard

### Hacienda Submission Testing
**Responsible:** QA Engineer | **Estimated Time:** 30 minutes

- [ ] **Submit to Sandbox**
  - [ ] Click "Submit to Hacienda" button
  - [ ] Wait for submission (may take 5-10 seconds)
  - [ ] Verify state changed to "Submitted"
  - [ ] Check submission date populated
  - [ ] Review Hacienda response
  - **Success Criteria:** Submitted without errors

- [ ] **Check Status**
  - [ ] Click "Check Status" button
  - [ ] Wait for status check
  - [ ] Verify response received:
    - [ ] Status: procesando / aceptado / rechazado
    - [ ] Message displayed
  - [ ] If "procesando", wait 30 seconds and check again
  - [ ] Continue until status is final (aceptado / rechazado)
  - **Success Criteria:** Status retrieved successfully

- [ ] **Handle Acceptance**
  - [ ] If status = "aceptado":
    - [ ] Verify state changed to "Accepted"
    - [ ] Check acceptance date populated
    - [ ] Verify response XML stored
    - [ ] Check auto-email sent (if enabled)
  - **Success Criteria:** Acceptance properly processed

- [ ] **Handle Rejection** (if applicable)
  - [ ] If status = "rechazado":
    - [ ] Review rejection message
    - [ ] Check error details in Hacienda response
    - [ ] Document rejection reason: _____________________
    - [ ] Fix issue (XML structure, certificate, etc.)
    - [ ] Re-generate and re-submit
  - **Success Criteria:** Rejection properly logged and actionable

### Production Environment Switch Plan
**Responsible:** Configuration Manager | **Estimated Time:** 15 minutes

- [ ] **Pre-Production Checklist**
  - [ ] All sandbox tests passed
  - [ ] Production credentials obtained
  - [ ] Production certificate installed
  - [ ] Users trained
  - [ ] Support team ready
  - **Success Criteria:** Ready for production switch

- [ ] **Production Switch Procedure**
  ```bash
  # Plan (do not execute until approved):
  # 1. Schedule downtime window: _____________________
  # 2. Notify users
  # 3. Switch environment to Production
  # 4. Update API credentials
  # 5. Test with one production invoice
  # 6. Monitor for 1 hour
  # 7. Approve for general use
  ```
  - [ ] Procedure documented
  - [ ] Rollback plan ready
  - [ ] Downtime window scheduled: _____________________
  - **Success Criteria:** Production switch procedure approved

### Digital Signature Rollback Plan
**Responsible:** System Admin | **Execution Time:** 20 minutes

- [ ] **Rollback to Unsigned Workflow**
  ```python
  # Disable auto-submit
  company.l10n_cr_auto_submit_einvoice = False

  # Disable auto-generate
  company.l10n_cr_auto_generate_einvoice = False

  # Revert to manual XML generation only
  ```
  - [ ] Automation disabled
  - [ ] Users can still generate XML manually
  - [ ] No automatic submissions
  - **Success Criteria:** System operational without signing

- [ ] **Switch Back to Sandbox**
  - [ ] Navigate to: Settings → Accounting → Costa Rica Electronic Invoicing
  - [ ] Change Hacienda Environment to: **Sandbox**
  - [ ] Update credentials to sandbox
  - [ ] Test connection
  - **Success Criteria:** Sandbox environment restored

---

## Post-Deployment Checklist

### Monitoring Setup
**Responsible:** DevOps Engineer | **Due:** Within 24 hours

- [ ] **Application Monitoring**
  - [ ] Enable debug logging for l10n_cr_einvoice module
  - [ ] Configure log aggregation (e.g., ELK, Grafana Loki)
  - [ ] Set up log rotation (max 30 days retention)
  - [ ] Create dashboard for:
    - [ ] Import batches per day
    - [ ] Average import success rate
    - [ ] Average processing speed
    - [ ] Error rate percentage
    - [ ] Signature success rate
    - [ ] Hacienda submission success rate
  - **Success Criteria:** Real-time visibility into feature usage

- [ ] **Performance Monitoring**
  - [ ] Monitor CPU usage during imports
  - [ ] Monitor memory usage during imports
  - [ ] Monitor database connection pool
  - [ ] Monitor disk I/O
  - [ ] Set up alerts:
    - [ ] Import processing <30 inv/min
    - [ ] Error rate >10%
    - [ ] Import running >2 hours
    - [ ] Memory usage >1GB
    - [ ] Certificate expiring <30 days
  - **Success Criteria:** Proactive alerts configured

- [ ] **Business Metrics**
  - [ ] Track total invoices imported
  - [ ] Track average batch size
  - [ ] Track most common errors
  - [ ] Track certificate usage
  - [ ] Track Hacienda acceptance rate
  - **Success Criteria:** Business insights available

### User Training Plan
**Responsible:** Training Manager | **Due:** Before go-live

- [ ] **Training Materials Prepared**
  - [ ] User guide reviewed: `XML_IMPORT_USER_GUIDE.md`
  - [ ] Video tutorial created (XML import walkthrough)
  - [ ] Video tutorial created (Certificate setup)
  - [ ] Video tutorial created (Signing workflow)
  - [ ] Quick reference card printed
  - [ ] FAQ document distributed
  - **Success Criteria:** Complete training package ready

- [ ] **Training Sessions Scheduled**
  - [ ] Session 1: XML Import (Accounting team) - Date: _____
  - [ ] Session 2: Digital Signature (Managers) - Date: _____
  - [ ] Session 3: Error Handling (Support team) - Date: _____
  - [ ] Hands-on practice session - Date: _____
  - **Success Criteria:** All users scheduled for training

- [ ] **Training Completed**
  - [ ] Accounting team trained: ____ attendees
  - [ ] Managers trained: ____ attendees
  - [ ] Support team trained: ____ attendees
  - [ ] Training feedback collected
  - [ ] Knowledge test passed (80%+ score)
  - **Success Criteria:** Users competent and confident

### Support Documentation Ready
**Responsible:** Documentation Manager | **Due:** Before go-live

- [ ] **User Support Resources**
  - [ ] XML Import User Guide published
  - [ ] XML Import Admin Guide published
  - [ ] Certificate setup guide published
  - [ ] Hacienda API guide published
  - [ ] Video tutorials published
  - [ ] FAQ updated with deployment learnings
  - **Success Criteria:** Documentation easily accessible

- [ ] **Support Team Preparation**
  - [ ] Support team trained on features
  - [ ] Troubleshooting flowcharts created
  - [ ] Escalation procedures defined
  - [ ] Support ticket categories created:
    - [ ] XML Import - General
    - [ ] XML Import - Errors
    - [ ] Digital Signature - Certificate
    - [ ] Digital Signature - Hacienda
  - **Success Criteria:** Support ready for user questions

### Error Tracking
**Responsible:** Support Manager | **Ongoing**

- [ ] **Error Tracking System**
  - [ ] Create Jira/Trello board for feature issues
  - [ ] Categories:
    - [ ] Bug
    - [ ] Enhancement
    - [ ] Question
    - [ ] Documentation
  - [ ] Priorities: Critical, High, Medium, Low
  - [ ] SLA defined:
    - [ ] Critical: 4 hours response
    - [ ] High: 24 hours response
    - [ ] Medium: 3 days response
    - [ ] Low: 1 week response
  - **Success Criteria:** Issue tracking operational

- [ ] **Common Issues Documented**
  - [ ] Issue: ZIP upload fails
    - Solution: Check ZIP structure, flatten folders
  - [ ] Issue: High error rate
    - Solution: Check tax configuration
  - [ ] Issue: Certificate load fails
    - Solution: Verify password, check format
  - [ ] Issue: Hacienda submission fails
    - Solution: Check credentials, verify XML
  - **Success Criteria:** Knowledge base growing

### User Feedback Collection
**Responsible:** Product Manager | **Ongoing**

- [ ] **Feedback Mechanisms**
  - [ ] In-app feedback button enabled
  - [ ] User survey created (10 questions)
  - [ ] Feedback email: feedback@gms.cr
  - [ ] Monthly user interviews scheduled
  - **Success Criteria:** Multiple feedback channels active

- [ ] **Week 1 Feedback Review**
  - [ ] Collect feedback from first week
  - [ ] Analyze common themes
  - [ ] Identify quick wins
  - [ ] Create improvement backlog
  - [ ] Review date: _____________________
  - **Success Criteria:** Continuous improvement cycle started

---

## Production Validation

### XML Import: Test with Real Provider Data
**Responsible:** QA Lead | **Estimated Time:** 2 hours

- [ ] **Real GTI Data Test**
  - [ ] Obtain real GTI export from customer (sample: 50-100 invoices)
  - [ ] Import to staging environment
  - [ ] Verify success rate >95%
  - [ ] Review any errors, ensure resolvable
  - [ ] Validate sample invoices manually (5 invoices)
  - **Success Criteria:** Real GTI data imports successfully

- [ ] **Real FACTURATica Data Test**
  - [ ] Obtain real FACTURATica export (sample: 50-100 invoices)
  - [ ] Import to staging environment
  - [ ] Verify success rate >95%
  - [ ] Review any errors, ensure resolvable
  - [ ] Validate sample invoices manually (5 invoices)
  - **Success Criteria:** Real FACTURATica data imports successfully

- [ ] **Real TicoPay Data Test**
  - [ ] Obtain real TicoPay export (sample: 50-100 invoices)
  - [ ] Import to staging environment
  - [ ] Verify success rate >95%
  - [ ] Review any errors, ensure resolvable
  - [ ] Validate sample invoices manually (5 invoices)
  - **Success Criteria:** Real TicoPay data imports successfully

- [ ] **Mixed Provider Test**
  - [ ] Create ZIP with mixed provider XMLs (30 each from GTI, FACTURATica, TicoPay)
  - [ ] Import single batch
  - [ ] Verify all providers handled correctly
  - [ ] Check for provider-specific issues
  - **Success Criteria:** Mixed sources handled uniformly

### Digital Signature: Test with Real Certificates
**Responsible:** Security Lead | **Estimated Time:** 1 hour

- [ ] **Production Certificate Test (Sandbox)**
  - [ ] Install production certificate in sandbox environment
  - [ ] Generate and sign 10 test invoices
  - [ ] Submit all to Hacienda sandbox
  - [ ] Verify 100% acceptance rate
  - [ ] Check no certificate warnings
  - **Success Criteria:** Production certificate works in sandbox

- [ ] **Certificate Rotation Test**
  - [ ] Install secondary certificate
  - [ ] Switch between certificates
  - [ ] Sign invoices with both
  - [ ] Verify both work correctly
  - **Success Criteria:** Certificate switching seamless

### End-to-End Workflow Validation
**Responsible:** QA Lead | **Estimated Time:** 1 hour

- [ ] **Complete E-Invoice Workflow**
  1. [ ] Create customer invoice in Odoo
  2. [ ] Post invoice
  3. [ ] Generate e-invoice document (auto or manual)
  4. [ ] Generate XML
  5. [ ] Sign XML with certificate
  6. [ ] Submit to Hacienda sandbox
  7. [ ] Check status until accepted
  8. [ ] Verify email sent to customer (if enabled)
  9. [ ] Download PDF with QR code
  10. [ ] Download signed XML
  - **Success Criteria:** Complete workflow successful end-to-end

- [ ] **Historical Import + Current Workflow**
  1. [ ] Import 100 historical invoices
  2. [ ] Verify imported correctly
  3. [ ] Create new invoice (same customer)
  4. [ ] Generate and submit new e-invoice
  5. [ ] Verify historical and current invoices both visible
  6. [ ] Check reporting includes both
  - **Success Criteria:** Historical and current data integrated seamlessly

### User Acceptance Testing
**Responsible:** Business Owner | **Estimated Time:** 2 days

- [ ] **Accounting Team UAT**
  - [ ] Import historical invoices from previous provider
  - [ ] Generate e-invoices for current month
  - [ ] Submit to Hacienda
  - [ ] Handle rejections (if any)
  - [ ] Generate reports
  - [ ] Provide feedback: _____________________
  - **Success Criteria:** Accounting team approves for production

- [ ] **Management UAT**
  - [ ] Review import statistics
  - [ ] Review e-invoice dashboard
  - [ ] Test certificate management
  - [ ] Review Hacienda submission reports
  - [ ] Provide feedback: _____________________
  - **Success Criteria:** Management approves for production

- [ ] **IT Support UAT**
  - [ ] Test error handling procedures
  - [ ] Practice troubleshooting scenarios
  - [ ] Review monitoring dashboards
  - [ ] Test backup and restore
  - [ ] Provide feedback: _____________________
  - **Success Criteria:** IT confident supporting features

---

## Rollback Procedures

### Database Rollback Steps
**Responsible:** Database Admin | **Execution Time:** 30 minutes

- [ ] **Rollback Decision Criteria**
  - Critical functionality broken (>50% success rate)
  - Data corruption detected
  - Security vulnerability discovered
  - Performance degradation (>80% slower)
  - **Decision Made By:** Technical Lead + Business Owner

- [ ] **Rollback Execution**
  1. [ ] Announce rollback to users (downtime window)
  2. [ ] Stop Odoo service
     ```bash
     sudo systemctl stop odoo
     ```
  3. [ ] Backup current state (for analysis)
     ```bash
     pg_dump gms > gms_failed_state_$(date +%Y%m%d_%H%M%S).sql
     ```
  4. [ ] Drop current database
     ```bash
     dropdb gms
     ```
  5. [ ] Create fresh database
     ```bash
     createdb gms
     ```
  6. [ ] Restore from pre-deployment backup
     ```bash
     psql gms < gms_backup_YYYYMMDD_HHMMSS.sql
     ```
  7. [ ] Verify restoration
     ```sql
     SELECT COUNT(*) FROM account_move;
     -- Should match pre-deployment count
     ```
  8. [ ] Start Odoo service
     ```bash
     sudo systemctl start odoo
     ```
  9. [ ] Verify system operational
  10. [ ] Notify users of rollback completion
  - **Success Criteria:** System restored to pre-deployment state

### Module Downgrade Procedure
**Responsible:** System Admin | **Execution Time:** 20 minutes

- [ ] **Code Rollback**
  ```bash
  # Stop Odoo
  sudo systemctl stop odoo

  # Checkout previous version
  cd /opt/odoo/addons/l10n_cr_einvoice
  git checkout <previous-commit-hash>

  # Or restore from backup
  rm -rf /opt/odoo/addons/l10n_cr_einvoice
  tar -xzf l10n_cr_einvoice_backup.tar.gz -C /opt/odoo/addons/

  # Set permissions
  chown -R odoo:odoo /opt/odoo/addons/l10n_cr_einvoice

  # Start Odoo
  sudo systemctl start odoo
  ```
  - [ ] Previous code version restored
  - [ ] Service running
  - [ ] No errors in logs
  - **Success Criteria:** Previous module version operational

- [ ] **Downgrade Verification**
  - [ ] Login to Odoo
  - [ ] Check module version matches pre-deployment
  - [ ] Test basic e-invoice functionality
  - [ ] Verify existing invoices still accessible
  - [ ] Check no new errors introduced
  - **Success Criteria:** System stable on previous version

### Data Recovery Process
**Responsible:** Database Admin | **Execution Time:** 1 hour

- [ ] **Identify Data Loss**
  - [ ] Determine what data was lost/corrupted
  - [ ] Check import batches affected
  - [ ] Identify invoices affected
  - [ ] Assess impact on customers
  - [ ] Document scope: _____________________
  - **Success Criteria:** Clear understanding of data loss

- [ ] **Selective Data Recovery**
  ```sql
  -- Extract lost data from backup
  pg_restore -d gms -t account_move gms_backup_YYYYMMDD.sql

  -- Or restore specific records
  psql gms < custom_recovery_script.sql
  ```
  - [ ] Backup loaded to temporary database
  - [ ] Lost records identified
  - [ ] Records exported
  - [ ] Records imported to production
  - [ ] Verification queries run
  - **Success Criteria:** Lost data recovered

- [ ] **Data Integrity Verification**
  ```sql
  -- Check for duplicates
  SELECT l10n_cr_original_clave, COUNT(*)
  FROM account_move
  WHERE l10n_cr_original_clave IS NOT NULL
  GROUP BY l10n_cr_original_clave
  HAVING COUNT(*) > 1;

  -- Check totals
  SELECT COUNT(*), SUM(amount_total)
  FROM account_move
  WHERE l10n_cr_is_historical = true;
  ```
  - [ ] No duplicate claves
  - [ ] Record counts match expected
  - [ ] Totals match expected
  - **Success Criteria:** Data integrity confirmed

### Post-Rollback Actions
**Responsible:** Project Manager | **Due:** Within 48 hours

- [ ] **Incident Analysis**
  - [ ] Root cause identified: _____________________
  - [ ] Timeline documented
  - [ ] Affected users identified
  - [ ] Impact assessed
  - [ ] Lessons learned documented
  - **Success Criteria:** Clear understanding of what went wrong

- [ ] **Communication**
  - [ ] Users notified of rollback reason
  - [ ] Timeline for fix communicated
  - [ ] Interim workarounds provided
  - [ ] Confidence restored
  - **Success Criteria:** Stakeholders informed and satisfied

- [ ] **Fix and Re-Deployment Plan**
  - [ ] Issue fixed in development
  - [ ] Additional tests added
  - [ ] Re-deployment scheduled: _____________________
  - [ ] Enhanced rollback criteria defined
  - **Success Criteria:** Ready for second deployment attempt

---

## Sign-Off

### Pre-Deployment Approval
- [ ] **Technical Lead:** ___________________ Date: _____
  - Code reviewed and approved
  - Tests passed
  - Performance validated

- [ ] **Security Lead:** ___________________ Date: _____
  - Security audit passed
  - Certificates validated
  - Access controls verified

- [ ] **QA Lead:** ___________________ Date: _____
  - All test scenarios passed
  - UAT completed successfully
  - Known issues documented

### Deployment Execution Sign-Off
- [ ] **System Admin:** ___________________ Date: _____
  - Backup completed
  - Module deployed
  - Service restarted
  - Post-deployment verification passed

- [ ] **Database Admin:** ___________________ Date: _____
  - Database migration successful
  - Indexes created
  - Performance validated

### Post-Deployment Approval
- [ ] **Business Owner:** ___________________ Date: _____
  - Features working as expected
  - Users trained
  - Approved for production use

- [ ] **Support Manager:** ___________________ Date: _____
  - Support team ready
  - Documentation complete
  - Monitoring active

---

## Deployment Summary

**Deployment Date:** _____________________
**Deployment Start Time:** _____________________
**Deployment End Time:** _____________________
**Total Deployment Duration:** _____________________

### Features Deployed
- [x] XML Import Feature (Days 1-12)
- [x] Digital Signature Feature (Phase 2)

### Deployment Status
- [ ] ✅ Success - All features operational
- [ ] ⚠️ Partial Success - Some issues, but operational
- [ ] ❌ Failed - Rolled back

### Metrics
- **XML Import Tests:** _____ / _____ passed
- **Digital Signature Tests:** _____ / _____ passed
- **Performance:** _____ invoices/minute (target: 50+)
- **Success Rate:** _____% (target: >95%)
- **User Training:** _____ users trained
- **Issues Found:** _____ critical, _____ high, _____ medium, _____ low

### Outstanding Items
1. _____________________
2. _____________________
3. _____________________

### Next Steps
1. _____________________
2. _____________________
3. _____________________

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-29
**Status:** Production Ready
**Review Date:** 2026-01-29 (30 days post-deployment)

---

## Reference Documentation

### XML Import Documentation
- User Guide: `/l10n_cr_einvoice/docs/XML_IMPORT_USER_GUIDE.md`
- Admin Guide: `/l10n_cr_einvoice/docs/XML_IMPORT_ADMIN_GUIDE.md`
- Implementation Status: `XML-IMPORT-IMPLEMENTATION-STATUS.md`

### Digital Signature Documentation
- Phase 2 Complete: `PHASE2-IMPLEMENTATION-COMPLETE.md`
- Test Guide: `PHASE2-SIGNATURE-TEST-GUIDE.md`
- Certificate Manager: `/l10n_cr_einvoice/models/certificate_manager.py`
- XML Signer: `/l10n_cr_einvoice/models/xml_signer.py`
- Hacienda API: `/l10n_cr_einvoice/models/hacienda_api.py`

### General Documentation
- Production Readiness Report: `PRODUCTION-READINESS-REPORT.md`
- Compliance Report: `100-PERCENT-COMPLIANCE-ACHIEVED.md`
- Deployment Guide: `docs/04-Deployment/DEPLOYMENT-CHECKLIST.md`
