# Phase 3 User Guide: Enhanced E-Invoicing Features

## Table of Contents

1. [Introduction](#introduction)
2. [Automatic Status Polling](#automatic-status-polling)
3. [Response Message Repository](#response-message-repository)
4. [Retry Queue Management](#retry-queue-management)
5. [Bulk Operations](#bulk-operations)
6. [Dashboard and Analytics](#dashboard-and-analytics)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

Phase 3 enhances the Costa Rica e-invoicing module with powerful automation and monitoring features:

- **Automatic Polling:** Documents are automatically checked with Hacienda every 15 minutes
- **Smart Retry:** Failed operations automatically retry with intelligent backoff
- **Complete Audit Trail:** All Hacienda communications are stored for compliance
- **Bulk Operations:** Process multiple documents at once
- **Real-time Dashboard:** Monitor your e-invoicing performance

---

## Automatic Status Polling

### What is it?

When you submit an invoice to Hacienda, it may take time to process. Instead of manually checking the status, the system automatically polls Hacienda every 15 minutes and updates your documents.

### How it works

1. You submit an invoice → Status: **Submitted**
2. System waits 2 minutes (cooling period)
3. Cron job automatically checks status every 15 minutes
4. When Hacienda accepts → Status: **Accepted**
5. Email automatically sent to customer (if configured)

### Configuration

**Go to:** Settings → E-Invoicing → Costa Rica

**Options:**
- **Enable Auto-Polling:** Turn automatic polling on/off
- **Max Polling Hours:** How long to keep checking (default: 24 hours)
- **Batch Size:** How many documents to check per cycle (default: 50)

**Recommended Settings:**
- Enable Auto-Polling: ✓ Yes
- Max Polling Hours: 24
- Batch Size: 50

### Manual Status Check

If you need to check immediately:

1. Open the document
2. Click **Check Status** button
3. View updated status

---

## Response Message Repository

### What is it?

A complete log of all communications with Hacienda, stored for audit and compliance purposes.

### Features

- Stores every acceptance, rejection, and status response
- Preserves original XML content
- Extracts and displays error codes
- Searchable and filterable
- Automatic cleanup after 90 days

### Viewing Response Messages

**Method 1: From Document**
1. Open any e-invoice document
2. Click **Responses** smart button (shows count)
3. View list of all responses for this document

**Method 2: Global View**
1. Go to **E-Invoicing → Response Messages**
2. Use filters to find specific messages:
   - By message type (Acceptance, Rejection, etc.)
   - By date range
   - With errors only
   - Final responses only

### Response Message Details

Click on any message to see:

- **Message ID:** Unique identifier
- **Document Clave:** 50-digit Hacienda key
- **Status:** aceptado, rechazado, procesando
- **Response Date:** When received from Hacienda
- **Error Details:** If rejected (code and description)
- **XML Content:** Complete response XML

### Actions

- **View XML:** See formatted XML response
- **Download XML:** Save XML file for records
- **View Document:** Jump to related e-invoice

---

## Retry Queue Management

### What is it?

When an operation fails (network error, server timeout, etc.), it's automatically added to a retry queue. The system intelligently retries the operation with exponential backoff.

### Error Categories

The system classifies errors automatically:

| Category | Examples | Max Retries | Retry Delays |
|----------|----------|-------------|--------------|
| **Transient** | Temporary errors | 5 | 5min, 15min, 1hr, 4hr, 12hr |
| **Network** | Timeout, connection | 5 | 7.5min, 22.5min, 1.5hr, 6hr, 18hr |
| **Rate Limit** | Too many requests | 4 | 10min, 30min, 2hr, 8hr |
| **Server** | 500 errors | 5 | 7.5min, 22.5min, 1.5hr, 6hr, 18hr |
| **Auth** | Credentials issue | 3 | 15min, 45min, 3hr |
| **Validation** | Invalid XML | 2 | 30min, 3hr |

### Viewing Retry Queue

**Go to:** E-Invoicing → Retry Queue

**Views Available:**
- **Kanban:** Card view grouped by state
- **List:** Detailed table view
- **Form:** Individual entry details

### Retry Queue States

- **Pending:** Waiting for next retry attempt
- **Processing:** Currently being retried
- **Completed:** Successfully recovered
- **Failed:** Max retries exhausted (needs manual intervention)
- **Cancelled:** Manually cancelled by user

### Managing Retries

**Manual Retry:**
1. Open retry queue entry
2. Click **Retry Now** button
3. Operation executes immediately

**Cancel Retry:**
1. Open retry queue entry
2. Click **Cancel** button
3. Confirm cancellation

**Monitor Progress:**
- Progress bar shows retry attempts (e.g., 2/5)
- Next attempt date/time displayed
- Overdue items highlighted in yellow
- Failed items highlighted in red

### From Document View

1. Open any e-invoice document
2. Click **Retries** smart button (shows pending count)
3. View all retry queue entries for this document

---

## Bulk Operations

### What are they?

Process multiple e-invoice documents simultaneously instead of one at a time. Perfect for high-volume periods.

### Available Operations

1. **Bulk Sign:** Sign multiple XML documents
2. **Bulk Submit:** Submit multiple documents to Hacienda
3. **Bulk Status Check:** Check status of multiple submitted documents

### How to Use

**Step 1: Select Documents**
1. Go to **E-Invoicing → Electronic Invoices**
2. Use filters to find documents:
   - By state (Generated, Signed, Submitted)
   - By date range
   - By customer
3. Select multiple documents (checkboxes)

**Step 2: Choose Operation**
1. Click **Action** dropdown
2. Select bulk operation:
   - Bulk Sign Documents
   - Bulk Submit to Hacienda
   - Bulk Check Status

**Step 3: Configure Options**

**For Bulk Sign:**
- Continue on Error: ✓ Recommended

**For Bulk Submit:**
- Batch Size: 10 (default)
- Delay Between Batches: 5 seconds
- Continue on Error: ✓ Recommended

**For Bulk Status Check:**
- Batch Size: 20 (default)
- Delay Between Batches: 5 seconds
- Continue on Error: ✓ Recommended

**Step 4: Review and Execute**
1. Review document list
2. Click confirmation button
3. Wait for processing (do not close window)
4. View results summary

### Results

The wizard shows:
- Successfully processed count
- Failed count
- Total processed
- List of errors (if any)

### Best Practices

1. **Start Small:** Test with 5-10 documents first
2. **Monitor Rate Limits:** Use batch delays to avoid API throttling
3. **Continue on Error:** Enable to process all documents
4. **Off-Peak Hours:** Run bulk operations during low-traffic times
5. **Check Results:** Review error list after completion

---

## Dashboard and Analytics

### Accessing Dashboard

**Go to:** E-Invoicing → Dashboard

### Available Metrics

**Summary Cards:**
- Total Documents
- Accepted This Month
- Rejected This Month
- Currently Submitted (pending)
- Error Count

**Charts:**
1. **Status Distribution (Pie Chart)**
   - Visual breakdown by document state
   - Click to filter by status

2. **Document Types (Pie Chart)**
   - Distribution of FE, TE, NC, ND
   - Click to filter by type

3. **Monthly Trend (Line Chart)**
   - Documents over time
   - Grouped by status
   - Identify patterns

4. **Detailed Analysis (Pivot Table)**
   - Cross-tabulate by multiple dimensions
   - Export to Excel
   - Create custom views

### Key Performance Indicators

**Acceptance Rate:**
- Percentage of documents accepted by Hacienda
- Target: >95%

**Average Acceptance Time:**
- How long between submission and acceptance
- Measured in hours
- Lower is better

**Pending Actions:**
- Documents awaiting submission
- Documents awaiting status check

### Using Dashboard Data

**Identify Issues:**
- High rejection rate → Review document configuration
- Long acceptance time → Check Hacienda API status
- Many errors → Review error logs

**Track Performance:**
- Monitor acceptance rate trends
- Compare month-over-month
- Set team goals

**Plan Resources:**
- Peak volume periods
- Staff scheduling
- System capacity planning

---

## Configuration

### Company Settings

**Path:** Settings → General Settings → E-Invoicing

**Phase 3 Settings:**

1. **Automatic Polling**
   ```
   ☑ Enable Automatic Status Polling
   Max Polling Hours: 24
   Batch Size: 50
   ```

2. **Email Settings**
   ```
   ☑ Auto-send email on acceptance
   Email Template: Default (or custom)
   ```

3. **Certificate Settings**
   ```
   Upload your X.509 certificate
   Upload private key
   Set certificate password
   ```

### Cron Jobs

**Path:** Settings → Technical → Scheduled Actions

**Phase 3 Cron Jobs:**

1. **Poll Pending Documents**
   - Active: ✓
   - Interval: 15 minutes
   - Next Run: (auto-calculated)

2. **Process Retry Queue**
   - Active: ✓
   - Interval: 5 minutes
   - Next Run: (auto-calculated)

3. **Cleanup Old Response Messages**
   - Active: ✓
   - Interval: Daily at 2:00 AM
   - Retention: 90 days

**Modifying Intervals:**

1. Open scheduled action
2. Click **Edit**
3. Change **Interval Number** or **Interval Type**
4. Save

**Caution:** Too frequent polling may hit API rate limits!

---

## Troubleshooting

### Documents Not Being Polled

**Symptoms:** Submitted documents stay in "Submitted" state

**Solutions:**
1. Check if auto-polling is enabled (Settings → E-Invoicing)
2. Verify cron job is active (Scheduled Actions)
3. Check document submission date (must be >2 minutes old)
4. Review server logs for errors

**Manual Fix:**
1. Open document
2. Click **Check Status** button manually

### Retry Queue Not Processing

**Symptoms:** Failed operations stay in "Pending" state

**Solutions:**
1. Check "Process Retry Queue" cron job is active
2. Verify next attempt date hasn't passed
3. Check if max retries exhausted (state = Failed)
4. Review error logs

**Manual Fix:**
1. Open retry queue entry
2. Click **Retry Now** button

### Response Messages Not Storing

**Symptoms:** Smart button shows 0 responses

**Solutions:**
1. Check user permissions (must have read access)
2. Verify document has been submitted to Hacienda
3. Check if _store_response_message() is being called
4. Review model access rights

### Bulk Operations Failing

**Symptoms:** Wizard shows many errors

**Common Issues:**
1. **Wrong State:** Documents must be in correct state for operation
2. **Rate Limiting:** Reduce batch size or increase delays
3. **API Timeout:** Check network connection
4. **Certificate Issue:** Verify certificate is valid

**Solutions:**
1. Filter documents by correct state before bulk operation
2. Use smaller batch sizes (e.g., 5-10)
3. Increase delay between batches
4. Test with single document first

### High Rejection Rate

**Symptoms:** Dashboard shows >10% rejection rate

**Investigation:**
1. Go to Response Messages
2. Filter by "Rejections"
3. Review error codes and descriptions

**Common Causes:**
1. **Invalid VAT Numbers:** Update customer information
2. **Missing Fields:** Complete all required invoice fields
3. **Incorrect Codes:** Verify discount/activity codes
4. **XML Validation:** Check XML generator configuration

### Slow Dashboard Loading

**Symptoms:** Dashboard takes >5 seconds to load

**Solutions:**
1. Reduce date range (filter by month)
2. Archive old documents
3. Run database optimization
4. Add indexes if needed

### Cron Jobs Not Running

**Symptoms:** No automatic processing happening

**Check:**
1. Odoo server is running
2. Cron worker is enabled (--max-cron-threads > 0)
3. Scheduled actions are active
4. No errors in server logs

**Restart Cron:**
```bash
# Restart Odoo with cron enabled
odoo-bin -c odoo.conf --max-cron-threads=2
```

---

## Tips and Best Practices

### Daily Operations

1. **Morning Check:**
   - Review dashboard for overnight processing
   - Check retry queue for failed items
   - Address any errors

2. **Throughout Day:**
   - Monitor acceptance rates
   - Respond to customer inquiries with response messages
   - Use bulk operations during peak times

3. **End of Day:**
   - Review daily statistics
   - Plan for next day's volume
   - Address any pending issues

### Weekly Maintenance

1. Review retry queue for chronic failures
2. Analyze rejection patterns
3. Clean up old cancelled retries
4. Update customer VAT information if needed

### Monthly Review

1. Generate acceptance rate report
2. Review error trends
3. Optimize cron job intervals if needed
4. Plan capacity for upcoming month

### Support

For issues not covered in this guide:

1. Check server logs: `/var/log/odoo/odoo.log`
2. Review Odoo documentation
3. Contact GMS support team
4. Check Hacienda API status page

---

**Guide Version:** 1.0
**Last Updated:** December 29, 2024
**Module Version:** 19.0.1.4.0
