# Phase 3: Enhanced API Integration - Quick Start Guide

**Version**: 1.3.0
**Date**: 2025-12-29
**Status**: Core Complete, Integration Pending

---

## Overview

Phase 3 adds enterprise-grade automation to the e-invoicing system:
- **Automatic Status Polling**: Documents check themselves every 15 minutes
- **Response Repository**: Full audit trail of all Hacienda responses
- **Retry Queue**: Failed operations retry automatically with smart backoff
- **Configurable Settings**: Control all automation behavior

---

## What's New in Phase 3

### 1. Automatic Status Polling

Documents submitted to Hacienda are automatically checked for status updates:

- **Frequency**: Every 15 minutes (configurable)
- **Duration**: Up to 24 hours (configurable)
- **Batch Size**: 50 documents per batch (configurable)
- **States Monitored**: 'submitted'
- **Auto-Transition**: submitted → accepted/rejected

### 2. Response Message Repository

Every response from Hacienda is stored for compliance and troubleshooting:

- **What's Stored**: XML responses, error codes, status, timestamps
- **Access**: View all responses per document
- **Retention**: 90 days (configurable)
- **Features**: Download XML, view decoded content, search by error code

### 3. Intelligent Retry Queue

Failed operations automatically retry with exponential backoff:

- **Error Classification**: Transient, auth, validation, network, server
- **Smart Delays**: 5min → 15min → 1hr → 4hr → 12hr
- **Max Attempts**: 5 (configurable)
- **Priority Support**: High-priority documents retry first
- **Notifications**: Admins notified after max retries

### 4. Dashboard Statistics

Real-time monitoring of e-invoice processing:

- Total documents by state
- Acceptance rate
- Average acceptance time
- Queue status
- Today's activity

---

## New Models

### `l10n_cr.hacienda.response.message`

Stores all Hacienda API responses.

**Key Fields**:
- `document_id` - Related e-invoice
- `clave` - Document key
- `message_type` - acceptance/rejection/confirmation
- `status` - aceptado/rechazado/procesando
- `raw_xml` - Full XML response
- `decoded_xml` - Decoded content
- `error_code` - Error code (if rejected)
- `response_date` - When response received

**Usage**:
```python
# Automatically created when document receives response
# View all responses for a document
document.action_view_response_messages()

# Manual creation (rare)
response_msg_model.create_from_hacienda_response(document, response)
```

### `l10n_cr.einvoice.retry.queue`

Manages automatic retry of failed operations.

**Key Fields**:
- `document_id` - Document to retry
- `operation` - sign/submit/check_status
- `retry_count` - Current attempt number
- `max_retries` - Maximum attempts
- `next_attempt` - Scheduled retry time
- `error_category` - Classified error type
- `state` - pending/processing/completed/failed
- `priority` - Queue priority

**Usage**:
```python
# Automatically added on failure
# Manual retry
queue_entry.action_retry_now()

# View queue for document
document.action_view_retry_queue()

# Get statistics
retry_queue_model.get_queue_statistics()
```

---

## Configuration (res.company)

### Polling Settings

```python
l10n_cr_auto_polling_enabled = True  # Enable automatic polling
l10n_cr_polling_interval = 15  # Minutes between polls
l10n_cr_polling_max_hours = 24  # Max time to keep polling
l10n_cr_polling_batch_size = 50  # Documents per batch
```

**Access**: Settings → Companies → E-Invoicing → Polling Configuration

### Retry Settings

```python
l10n_cr_auto_retry_enabled = True  # Enable automatic retry
l10n_cr_max_retry_attempts = 5  # Max retry attempts
```

**Access**: Settings → Companies → E-Invoicing → Retry Configuration

### Response Storage Settings

```python
l10n_cr_store_responses = True  # Store all responses
l10n_cr_response_retention_days = 90  # Days to keep
```

**Access**: Settings → Companies → E-Invoicing → Response Storage

### Batch Processing Settings

```python
l10n_cr_batch_size = 50  # Batch size for bulk operations
l10n_cr_batch_delay = 5  # Seconds between batches
l10n_cr_max_concurrent_batches = 3  # Concurrent batches
```

**Access**: Settings → Companies → E-Invoicing → Batch Processing

---

## Cron Jobs (Scheduled Actions)

Phase 3 adds 4 automated scheduled actions:

### 1. Poll Pending Documents
- **Runs**: Every 15 minutes
- **Model**: `l10n_cr.einvoice.document`
- **Method**: `_cron_poll_pending_documents()`
- **Purpose**: Check status of submitted documents
- **Priority**: Normal (5)

### 2. Process Retry Queue
- **Runs**: Every 5 minutes
- **Model**: `l10n_cr.einvoice.retry.queue`
- **Method**: `_cron_process_retry_queue()`
- **Purpose**: Retry failed operations
- **Priority**: High (10)

### 3. Cleanup Old Response Messages
- **Runs**: Daily at 2:00 AM
- **Model**: `l10n_cr.hacienda.response.message`
- **Method**: `cleanup_old_messages()`
- **Purpose**: Remove old responses (90 days)
- **Priority**: Low (20)

### 4. Cleanup Old Retry Queue Entries
- **Runs**: Daily at 3:00 AM
- **Model**: `l10n_cr.einvoice.retry.queue`
- **Method**: `_cleanup_old_entries()`
- **Purpose**: Remove old queue entries (30 days)
- **Priority**: Low (20)

**Access**: Settings → Technical → Automation → Scheduled Actions

---

## Enhanced EInvoice Document Methods

### New Actions

```python
# View all Hacienda responses for this document
document.action_view_response_messages()

# View retry queue entries
document.action_view_retry_queue()

# Get dashboard statistics (class method)
model.get_dashboard_statistics(company_id=1)
```

### Enhanced Methods

**Automatic Response Storage**:
```python
# Old: Just process response
self._process_hacienda_response(response)

# New: Process AND store in repository
self._process_hacienda_response(response)
# Automatically calls: self._store_response_message(response)
```

**Automatic Retry Queue**:
```python
# On any failure during sign or submit:
try:
    self.action_submit_to_hacienda()
except Exception as e:
    # Automatically adds to retry queue
    self._add_to_retry_queue('submit', str(e))
```

---

## Typical Workflows

### Workflow 1: Normal Submission with Auto-Polling

1. **User**: Create and post invoice
2. **System**: Auto-generate e-invoice (if enabled)
3. **User**: Click "Sign XML"
4. **System**: Sign and update state to 'signed'
5. **User**: Click "Submit to Hacienda"
6. **System**: Submit, receive "procesando", state → 'submitted'
7. **Cron** (15 min later): Poll status
8. **Hacienda**: Returns "aceptado"
9. **System**: State → 'accepted', store response, send email

**Total Time**: ~15 minutes (automatic)

### Workflow 2: Failed Submission with Retry

1. **User**: Click "Submit to Hacienda"
2. **System**: Submission fails (network error)
3. **System**: Add to retry queue (category: network)
4. **Cron** (5 min later): Retry submission
5. **System**: Success! State → 'submitted'
6. **Cron** (15 min later): Poll status
7. **System**: State → 'accepted'

**Total Time**: ~20 minutes (automatic recovery)

### Workflow 3: Manual Retry

1. **Document** failed after 5 auto-retries
2. **Admin**: Fix issue (e.g., update credentials)
3. **Admin**: Open document
4. **Admin**: Click "View Retry Queue"
5. **Admin**: Select failed entry
6. **Admin**: Click "Retry Now"
7. **System**: Retry immediately
8. **System**: Success! Queue entry → 'completed'

**Total Time**: Immediate

---

## Error Classification

The retry queue automatically classifies errors:

| Error Type | Detection | Retry Delay Multiplier | Max Retries |
|------------|-----------|------------------------|-------------|
| **Transient** | "temporary", "try again" | 1.0x | 5 |
| **Rate Limit** | "rate limit", "429" | 2.0x (longer) | 4 |
| **Network** | "timeout", "connection" | 1.5x | 5 |
| **Server** | "500", "502", "503" | 1.5x | 5 |
| **Auth** | "auth", "401", "403" | 3.0x (needs manual fix) | 3 |
| **Validation** | "validation", "invalid", "400" | 6.0x (needs manual fix) | 2 |
| **Unknown** | Everything else | 2.0x | 3 |

---

## Monitoring & Troubleshooting

### Check Polling Status

**Odoo Shell**:
```python
# Check if polling is enabled
env.company.l10n_cr_auto_polling_enabled

# See pending documents
pending = env['l10n_cr.einvoice.document'].search([
    ('state', '=', 'submitted')
])
print(f"Pending documents: {len(pending)}")

# Check last polling run (cron log)
cron = env.ref('l10n_cr_einvoice.ir_cron_poll_pending_documents')
print(f"Last run: {cron.lastcall}")
print(f"Next run: {cron.nextcall}")
```

### Check Retry Queue

**Odoo Shell**:
```python
# Get queue statistics
stats = env['l10n_cr.einvoice.retry.queue'].get_queue_statistics()
print(stats)

# See pending retries
pending = env['l10n_cr.einvoice.retry.queue'].search([
    ('state', '=', 'pending')
])
for entry in pending:
    print(f"{entry.document_id.name}: {entry.operation} - Next: {entry.next_attempt}")

# See failed retries (need attention)
failed = env['l10n_cr.einvoice.retry.queue'].search([
    ('state', '=', 'failed')
])
```

### Check Response Storage

**Odoo Shell**:
```python
# Get response statistics
stats = env['l10n_cr.hacienda.response.message'].get_statistics()
print(f"Total responses: {stats['total']}")
print(f"Acceptance rate: {stats['acceptance_rate']:.2f}%")

# Find all rejections
rejections = env['l10n_cr.hacienda.response.message'].search([
    ('message_type', '=', 'rejection')
])
for r in rejections:
    print(f"{r.clave}: {r.error_description}")
```

### Common Issues

**Issue**: Documents not polling
- **Check**: Is `l10n_cr_auto_polling_enabled = True`?
- **Check**: Is cron active? (Settings → Scheduled Actions)
- **Check**: Are documents in 'submitted' state?
- **Check**: Is submission date > 2 minutes ago?

**Issue**: Retry queue not processing
- **Check**: Is `l10n_cr_auto_retry_enabled = True`?
- **Check**: Is retry cron active?
- **Check**: Check `next_attempt` time - may not be due yet

**Issue**: Responses not being stored
- **Check**: Is `l10n_cr_store_responses = True`?
- **Check**: Check Odoo logs for storage errors
- **Fix**: May need to manually trigger storage

---

## Performance Tuning

### High-Volume Scenarios

If processing 1000+ documents per day:

**Polling**:
```python
l10n_cr_polling_interval = 10  # Poll more frequently
l10n_cr_polling_batch_size = 100  # Larger batches
```

**Batch Processing**:
```python
l10n_cr_batch_size = 100  # Process more at once
l10n_cr_batch_delay = 2  # Shorter delays (but watch rate limits)
```

**Response Storage**:
```python
l10n_cr_response_retention_days = 30  # Shorter retention
```

### Low-Volume Scenarios

If processing < 50 documents per day:

**Polling**:
```python
l10n_cr_polling_interval = 30  # Poll less frequently
l10n_cr_polling_batch_size = 20  # Smaller batches
```

**Response Storage**:
```python
l10n_cr_response_retention_days = 365  # Longer retention
```

---

## Security & Access Control

### Access Rights

**Hacienda Response Messages**:
- **Invoice Users**: Read-only access
- **Account Managers**: Full access (create, edit, delete)
- **Readonly Users**: Read-only access

**Retry Queue**:
- **Invoice Users**: Read-only access (can view, not modify)
- **Account Managers**: Full access (can retry, cancel, delete)

### Data Sensitivity

**Stored Data**:
- Response messages contain full XML (may include customer data)
- Retry queue contains error messages (may include credentials in auth errors)
- All data is company-scoped (multi-company safe)

**Recommendations**:
- Regular cleanup of old messages (automatic)
- Restrict access to managers only
- Monitor for sensitive data in error messages

---

## Migration from Previous Versions

### Upgrading from 1.2.x to 1.3.0

**Module Upgrade**:
```bash
# Backup database first!
python3 odoo-bin -c odoo.conf -d your_database -u l10n_cr_einvoice
```

**What Happens**:
1. New models created (response_message, retry_queue)
2. New fields added to res.company
3. Cron jobs activated
4. Security rules updated

**Post-Upgrade**:
1. Go to Settings → Companies → E-Invoicing
2. Review new configuration options
3. Enable auto-polling if desired
4. Enable auto-retry if desired
5. Test with a few documents

**Data Migration**:
- No data migration needed (new features)
- Existing documents continue working
- Old responses NOT migrated (start fresh)

---

## FAQs

**Q: Will this slow down my system?**
A: No. Polling and retry are background processes. They run asynchronously and don't block user actions.

**Q: What if I disable auto-polling?**
A: Documents will stay in 'submitted' state until you manually click "Check Status" or re-enable polling.

**Q: Can I customize retry delays?**
A: Yes, but requires code modification. The delays are defined in `einvoice_retry_queue.py`.

**Q: How many responses are stored?**
A: All responses are stored. Old ones are cleaned up automatically after 90 days (configurable).

**Q: What happens if retry queue fills up?**
A: Queue entries are automatically cleaned after 30 days. Failed retries are kept for manual review.

**Q: Can I export response messages?**
A: Yes, via the response message list view (Export button). Can export to CSV/Excel.

**Q: Does this work with multi-company?**
A: Yes! Each company has its own configuration and data is properly isolated.

---

## Next Steps

After Phase 3 integration is complete:

1. **Test in Development**: Submit test invoices, watch polling work
2. **Configure Settings**: Adjust polling and retry settings
3. **Monitor Dashboard**: Check statistics daily
4. **Review Queue**: Weekly review of failed retries
5. **Cleanup**: Monthly check of old responses

**Phase 4 Preview**: Advanced UI with bulk operations and enhanced dashboard

---

## Support & Resources

### Documentation Files
- `PHASE3-IMPLEMENTATION-PLAN.md` - Detailed implementation plan
- `PHASE3-IMPLEMENTATION-STATUS.md` - Current status and checklist
- `PHASE3-QUICK-START.md` - This file

### Code References
- `models/hacienda_response_message.py` - Response storage
- `models/einvoice_retry_queue.py` - Retry queue
- `data/hacienda_cron_jobs.xml` - Scheduled actions

### Getting Help
- Check Odoo logs: `/var/log/odoo/odoo.log`
- Enable debug mode: `?debug=1`
- Odoo shell: `python3 odoo-bin shell -c odoo.conf -d database`

---

**Phase 3 brings enterprise-grade automation to your e-invoicing workflow. Submit once, let the system handle the rest!**
