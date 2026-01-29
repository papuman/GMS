# Phase 3 Implementation Checklist

**Version**: 1.3.0
**Date**: 2025-12-29
**Overall Progress**: 40% Complete

---

## Core Infrastructure (COMPLETE ✅)

- [x] Create `hacienda_response_message.py` model
- [x] Create `einvoice_retry_queue.py` model
- [x] Add polling configuration fields to `res_company.py`
- [x] Add retry configuration fields to `res_company.py`
- [x] Add batch configuration fields to `res_company.py`
- [x] Create `hacienda_cron_jobs.xml`
- [x] Update `security/ir.model.access.csv`
- [x] Update `models/__init__.py`
- [x] Update `__manifest__.py`
- [x] Create reference file `einvoice_document_phase3_additions.py`

---

## Documentation (COMPLETE ✅)

- [x] PHASE3-IMPLEMENTATION-PLAN.md
- [x] PHASE3-IMPLEMENTATION-STATUS.md
- [x] PHASE3-QUICK-START.md
- [x] PHASE3-SUMMARY.md
- [x] PHASE3-CHECKLIST.md

---

## Integration Tasks (IN PROGRESS 🔧)

### einvoice_document.py Enhancement

- [ ] **Backup existing file**
  ```bash
  cp models/einvoice_document.py models/einvoice_document.py.bak
  ```

- [ ] **Add imports**
  ```python
  from datetime import datetime, timedelta
  ```

- [ ] **Replace _process_hacienda_response method**
  - Replace with `_process_hacienda_response_enhanced()`
  - Test response storage integration

- [ ] **Add new method: _store_response_message()**
  - Copy from phase3_additions.py
  - Test with sample response

- [ ] **Add new method: _add_to_retry_queue()**
  - Copy from phase3_additions.py
  - Test error classification

- [ ] **Add new method: _cron_poll_pending_documents()**
  - Copy from phase3_additions.py (as @api.model)
  - Test batch processing

- [ ] **Replace action_submit_to_hacienda method**
  - Replace with `action_submit_to_hacienda_with_retry()`
  - Test retry queue integration

- [ ] **Replace action_sign_xml method**
  - Replace with `action_sign_xml_with_retry()`
  - Test retry on signing failure

- [ ] **Add new method: action_view_response_messages()**
  - Copy from phase3_additions.py
  - Test action return

- [ ] **Add new method: action_view_retry_queue()**
  - Copy from phase3_additions.py
  - Test action return

- [ ] **Add new method: get_dashboard_statistics()**
  - Copy from phase3_additions.py (as @api.model)
  - Test statistics computation

- [ ] **Test integration**
  - Submit test invoice
  - Verify response stored
  - Trigger failure and check retry queue
  - Check all methods work

---

## View Development (PENDING ❌)

### Response Message Views

- [ ] **Create views/hacienda_response_message_views.xml**

- [ ] **Tree View**
  ```xml
  - Fields: clave, message_type, status, response_date, has_error
  - Filters: By message type, by status, by date
  - Colors: Green (acceptance), Red (rejection), Orange (other)
  - Order: response_date desc
  ```

- [ ] **Form View**
  ```xml
  - Header: Status badge, message type
  - Body: Document reference, dates, XML viewer
  - Actions: Download XML, View XML
  ```

- [ ] **Search View**
  ```xml
  - Search by: clave, error_code
  - Filter by: message_type, status, has_error, date ranges
  - Group by: message_type, date
  ```

- [ ] **Graph View**
  ```xml
  - Chart: Messages over time
  - Group by: message_type, status
  ```

- [ ] **Pivot View**
  ```xml
  - Rows: message_type
  - Columns: status
  - Measures: count
  ```

- [ ] **Add menu entry**
  ```xml
  - Location: E-Invoicing > Response Messages
  - Action: Open tree view
  - Security: account.group_account_invoice
  ```

- [ ] **Update manifest**
  - Uncomment view file in data list

---

### Retry Queue Views

- [ ] **Create views/einvoice_retry_queue_views.xml**

- [ ] **Tree View**
  ```xml
  - Fields: document_id, operation, retry_count, state, priority, next_attempt
  - Filters: By state, by priority, by operation
  - Colors: Red (failed), Orange (pending), Blue (processing)
  - Order: priority desc, next_attempt asc
  ```

- [ ] **Form View**
  ```xml
  - Header: State badge, priority indicator
  - Body: Document ref, operation, error details, retry schedule
  - Actions: Retry Now, Cancel Retry
  - Footer: Progress bar (retry_count/max_retries)
  ```

- [ ] **Kanban View**
  ```xml
  - Group by: state
  - Card: Document name, operation, retry count, next attempt
  - Priority indicator
  - Quick action: Retry Now
  ```

- [ ] **Search View**
  ```xml
  - Search by: document name
  - Filter by: state, priority, operation, error_category
  - Group by: state, priority, operation
  ```

- [ ] **Add menu entry**
  ```xml
  - Location: E-Invoicing > Retry Queue
  - Action: Open kanban view
  - Security: account.group_account_manager
  ```

- [ ] **Update manifest**
  - Uncomment view file in data list

---

### Settings View Enhancement

- [ ] **Open views/res_config_settings_views.xml**

- [ ] **Add Phase 3 Configuration Section**
  ```xml
  <group string="Phase 3: Automatic Processing">
  ```

- [ ] **Add Polling Configuration Group**
  ```xml
  - l10n_cr_auto_polling_enabled (checkbox)
  - l10n_cr_polling_interval (integer with unit)
  - l10n_cr_polling_max_hours (integer with unit)
  - l10n_cr_polling_batch_size (integer)
  - Help text for each field
  ```

- [ ] **Add Retry Configuration Group**
  ```xml
  - l10n_cr_auto_retry_enabled (checkbox)
  - l10n_cr_max_retry_attempts (integer)
  ```

- [ ] **Add Response Storage Group**
  ```xml
  - l10n_cr_store_responses (checkbox)
  - l10n_cr_response_retention_days (integer)
  ```

- [ ] **Add Batch Processing Group**
  ```xml
  - l10n_cr_batch_size (integer)
  - l10n_cr_batch_delay (integer)
  - l10n_cr_max_concurrent_batches (integer)
  ```

- [ ] **Test settings save and reload**

---

## Bulk Operations Wizards (PENDING ❌)

### Bulk Sign Wizard

- [ ] **Create wizards/einvoice_bulk_sign_wizard.py**

- [ ] **Model Definition**
  ```python
  - TransientModel
  - Fields: document_ids, batch_size, state, counts
  - Methods: action_sign_batch()
  ```

- [ ] **Create views/einvoice_bulk_sign_wizard_views.xml**
  ```xml
  - Form view with progress
  - Documents list
  - Sign button
  - Result summary
  ```

- [ ] **Add menu action**
  ```xml
  - Location: E-Invoice list > More > Bulk Sign
  - Domain: state = 'generated'
  ```

- [ ] **Test with 10+ documents**

---

### Bulk Submit Wizard

- [ ] **Create wizards/einvoice_bulk_submit_wizard.py**

- [ ] **Model Definition**
  ```python
  - TransientModel
  - Fields: document_ids, batch_size, delay, state, counts
  - Methods: action_submit_batch() with rate limiting
  ```

- [ ] **Create views/einvoice_bulk_submit_wizard_views.xml**
  ```xml
  - Form view with configuration
  - Progress bar
  - Submit button
  - Error log
  ```

- [ ] **Add menu action**
  ```xml
  - Location: E-Invoice list > More > Bulk Submit
  - Domain: state = 'signed'
  ```

- [ ] **Test with rate limiting**

---

### Bulk Status Check Wizard

- [ ] **Create wizards/einvoice_bulk_status_wizard.py**

- [ ] **Model Definition**
  ```python
  - TransientModel
  - Fields: document_ids, state, results
  - Methods: action_check_batch(), action_export_results()
  ```

- [ ] **Create views/einvoice_bulk_status_wizard_views.xml**
  ```xml
  - Form view
  - Results tree
  - Export button
  ```

- [ ] **Add menu action**
  ```xml
  - Location: E-Invoice list > More > Bulk Check Status
  - Domain: state = 'submitted'
  ```

- [ ] **Test export functionality**

---

### Update Wizards __init__.py

- [ ] **Add imports**
  ```python
  from . import einvoice_bulk_sign_wizard
  from . import einvoice_bulk_submit_wizard
  from . import einvoice_bulk_status_wizard
  ```

---

## Dashboard (PENDING ❌)

### Dashboard Model

- [ ] **Create models/einvoice_dashboard.py**

- [ ] **AbstractModel Definition**
  ```python
  - Computed statistics fields
  - Methods: _compute_stats()
  - Optimization for large datasets
  ```

- [ ] **Add to models/__init__.py**

---

### Dashboard Views

- [ ] **Create views/einvoice_dashboard_views.xml**

- [ ] **Kanban Dashboard**
  ```xml
  - KPI cards
  - Charts
  - Quick actions
  - Queue status
  ```

- [ ] **Add menu entry**
  ```xml
  - Location: E-Invoicing > Dashboard
  - Top menu item
  ```

- [ ] **Test auto-refresh**

---

## Testing (PENDING ❌)

### Unit Tests

- [ ] **Create tests/test_phase3_response_storage.py**
  - Test response message creation
  - Test error extraction
  - Test cleanup
  - Test statistics

- [ ] **Create tests/test_phase3_retry_queue.py**
  - Test queue addition
  - Test error classification
  - Test retry delay calculation
  - Test retry processing
  - Test notifications

- [ ] **Create tests/test_phase3_polling.py**
  - Test polling cron
  - Test batch processing
  - Test expired documents
  - Test rate limiting

- [ ] **Create tests/test_phase3_bulk_operations.py**
  - Test bulk sign
  - Test bulk submit
  - Test bulk status check

- [ ] **Create tests/__init__.py**
  - Import all test modules

---

### Integration Tests

- [ ] **Create tests/test_phase3_e2e.py**
  - Submit → Store Response → Poll → Accept workflow
  - Submit → Fail → Retry → Success workflow
  - Configuration changes affect behavior

---

### Manual Testing

- [ ] **Response Storage**
  - Submit invoice
  - Verify response in database
  - View via UI
  - Download XML

- [ ] **Retry Queue**
  - Trigger failure (wrong credentials)
  - Verify queue entry created
  - Check error classification
  - Wait for cron (or trigger manually)
  - Verify retry executed

- [ ] **Polling**
  - Submit invoice (gets 'procesando')
  - Wait for polling cron (15 min)
  - Verify status updated
  - Verify response stored

- [ ] **Configuration**
  - Change polling interval
  - Change max retries
  - Disable auto-polling
  - Verify behavior changes

- [ ] **Bulk Operations**
  - Select 50+ documents
  - Bulk sign
  - Verify progress
  - Check results

- [ ] **Performance**
  - 100+ documents polling
  - 1000+ documents bulk submit
  - Dashboard load time
  - No database locks

---

## Deployment (PENDING ❌)

### Pre-Deployment

- [ ] **Code Review**
  - All methods have docstrings
  - No security vulnerabilities
  - Performance optimized
  - Error handling comprehensive

- [ ] **Documentation Review**
  - Implementation plan complete
  - User guide complete
  - Admin guide complete
  - API documentation complete

- [ ] **Testing Complete**
  - All unit tests pass
  - Integration tests pass
  - Manual test checklist complete
  - Performance acceptable

---

### Deployment to Staging

- [ ] **Backup database**
  ```bash
  pg_dump -U odoo -d gms_staging > backup_pre_phase3.sql
  ```

- [ ] **Update module**
  ```bash
  python3 odoo-bin -c odoo.conf -d gms_staging -u l10n_cr_einvoice
  ```

- [ ] **Verify cron jobs activated**
  - Settings → Technical → Automation → Scheduled Actions
  - Verify 4 new cron jobs exist and active

- [ ] **Configure settings**
  - Settings → Companies → E-Invoicing
  - Review all Phase 3 settings
  - Enable auto-polling
  - Enable auto-retry

- [ ] **Test with real data**
  - Submit 10 invoices
  - Monitor for 24 hours
  - Check logs
  - Verify automatic processing

---

### User Acceptance Testing

- [ ] **Train users**
  - Demo new features
  - Explain automatic polling
  - Show retry queue
  - Show response messages

- [ ] **UAT Scenarios**
  - Normal invoice submission
  - Invoice with rejection
  - Network failure recovery
  - Bulk operations
  - Dashboard monitoring

- [ ] **Collect feedback**
  - Issues/bugs
  - Usability concerns
  - Performance observations
  - Feature requests

---

### Production Deployment

- [ ] **Backup production database**
  ```bash
  pg_dump -U odoo -d gms_production > backup_pre_phase3_prod.sql
  ```

- [ ] **Schedule downtime (optional)**
  - Off-peak hours
  - Notify users

- [ ] **Deploy to production**
  ```bash
  python3 odoo-bin -c odoo.conf -d gms_production -u l10n_cr_einvoice
  ```

- [ ] **Post-deployment verification**
  - Check cron jobs active
  - Verify settings retained
  - Test with 1 invoice
  - Monitor for 1 hour

- [ ] **Monitor for 24 hours**
  - Check logs daily
  - Monitor error rate
  - Check retry queue
  - Verify automatic polling working

---

### Post-Deployment

- [ ] **Performance tuning**
  - Adjust polling interval if needed
  - Optimize batch sizes
  - Review retention periods

- [ ] **Documentation handoff**
  - Provide admin guide
  - Provide user guide
  - Provide troubleshooting guide

- [ ] **Training**
  - Admin training session
  - User training session
  - Q&A session

---

## Success Metrics

### Functional Metrics

- [ ] **Polling Success Rate**: > 95% of submitted docs auto-updated
- [ ] **Retry Success Rate**: > 80% of failures recovered automatically
- [ ] **Response Storage**: 100% of API responses stored
- [ ] **Configuration Flexibility**: All settings accessible and working

### Performance Metrics

- [ ] **Polling Time**: < 2 minutes for 100 documents
- [ ] **Bulk Submit**: < 30 minutes for 1000 documents
- [ ] **Dashboard Load**: < 3 seconds
- [ ] **Database Size**: < 100MB for 90 days of responses

### Quality Metrics

- [ ] **Code Coverage**: > 80% test coverage
- [ ] **Documentation**: 100% of public methods documented
- [ ] **Security**: No vulnerabilities found in audit
- [ ] **User Satisfaction**: > 90% positive feedback

---

## Risk Mitigation Checklist

- [ ] **Database backup before each deployment**
- [ ] **Cron jobs staggered to avoid conflicts**
- [ ] **Rate limiting implemented in all bulk operations**
- [ ] **Automatic cleanup scheduled for old data**
- [ ] **Error notifications configured for admins**
- [ ] **Rollback plan documented**
- [ ] **Staging environment mirrors production**

---

## Completion Criteria

Phase 3 is complete when ALL of the following are true:

- [ ] All core models implemented and tested
- [ ] All views created and functional
- [ ] All wizards working
- [ ] Dashboard operational
- [ ] All tests passing
- [ ] Documentation complete
- [ ] UAT passed
- [ ] Production deployment successful
- [ ] 7 days of stable operation in production

---

## Current Status Summary

**Completed**: 10 items (core infrastructure, documentation)
**In Progress**: 1 item (einvoice_document integration)
**Pending**: 50+ items (views, wizards, tests, deployment)

**Overall Progress**: 40%

**Estimated Time to Complete**: 10-15 days

**Next Action**: Integrate einvoice_document enhancements

---

## Quick Commands

### Development
```bash
# Start Odoo
python3 odoo-bin -c odoo.conf -d gms_dev

# Update module
python3 odoo-bin -c odoo.conf -d gms_dev -u l10n_cr_einvoice

# Run tests
python3 odoo-bin -c odoo.conf -d gms_test --test-enable --stop-after-init

# Odoo shell
python3 odoo-bin shell -c odoo.conf -d gms_dev
```

### Database
```bash
# Backup
pg_dump -U odoo -d gms_dev > backup.sql

# Restore
psql -U odoo -d gms_dev < backup.sql

# Monitor size
psql -U odoo -d gms_dev -c "SELECT pg_size_pretty(pg_database_size('gms_dev'));"
```

### Logs
```bash
# Tail logs
tail -f /var/log/odoo/odoo.log

# Filter for Phase 3
tail -f /var/log/odoo/odoo.log | grep -E "(retry|poll|response)"

# Check cron execution
grep "cron" /var/log/odoo/odoo.log | tail -20
```

---

**Last Updated**: 2025-12-29
**Next Review**: After einvoice_document integration
