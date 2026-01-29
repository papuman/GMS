# Costa Rica E-Invoice Module - User Interface Guide

## Phase 4: Web UI Views - User Documentation

Version: 1.0.0
Date: 2025-12-28
Module: l10n_cr_einvoice

---

## Table of Contents

1. [Overview](#overview)
2. [Navigation](#navigation)
3. [Electronic Invoice Views](#electronic-invoice-views)
4. [Invoice Integration](#invoice-integration)
5. [Configuration](#configuration)
6. [Workflows](#workflows)
7. [Dashboard & Reports](#dashboard--reports)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Costa Rica E-Invoice module provides a comprehensive user interface for managing electronic invoices in compliance with Hacienda's requirements. This guide covers all UI components implemented in Phase 4.

### Key Features

- **Kanban Board**: Visual workflow management (Draft → Generated → Signed → Submitted → Accepted)
- **Smart Buttons**: Quick access to related invoices and attachments
- **Batch Operations**: Process multiple invoices simultaneously
- **Dashboard**: Real-time statistics and monitoring
- **Status Tracking**: Color-coded badges for instant status recognition
- **Error Handling**: Clear error messages and retry mechanisms

---

## Navigation

### Main Menu Structure

Access the E-Invoice module through: **Accounting > Hacienda (CR)**

```
Accounting
└── Hacienda (CR)
    ├── Electronic Invoices          (All e-invoices)
    ├── Pending E-Invoices           (Awaiting processing)
    ├── E-Invoice Errors             (Documents with errors)
    ├── ────────────────────
    ├── Dashboard                    (Statistics & graphs)
    ├── Reports                      (Future implementation)
    ├── ────────────────────
    └── Configuration                (Settings)
```

### Quick Access Points

1. **From Invoices**: Click the "E-Invoice" smart button on any Costa Rican invoice
2. **From Dashboard**: Access key metrics and jump to filtered lists
3. **From Notifications**: Activity tracking alerts for pending actions

---

## Electronic Invoice Views

### 1. Kanban View (Default)

**Path**: Hacienda (CR) > Electronic Invoices

**Description**: Visual board showing e-invoices grouped by status

#### Status Columns

| Status | Color | Description |
|--------|-------|-------------|
| Draft | Gray | Newly created, not yet processed |
| Generated | Blue | XML created, awaiting signature |
| Signed | Purple | Digitally signed, ready for submission |
| Submitted | Orange | Sent to Hacienda, awaiting confirmation |
| Accepted | Green | Approved by Hacienda |
| Rejected | Red | Rejected by Hacienda (requires action) |
| Error | Dark Red | Processing error (requires review) |

#### Kanban Card Contents

Each card displays:
- **Document Number** (e.g., EI/2024/0001)
- **Customer Name**
- **Invoice Reference**
- **Document Type Badge** (FE/TE/NC/ND)
- **Clave** (first 20 digits shown)
- **Total Amount**
- **Quick Action Buttons**

#### Quick Actions

Available directly from kanban cards:
- Generate XML (Draft/Error states)
- Sign XML (Generated state)
- Submit to Hacienda (Signed state)
- Check Status (Submitted state)

### 2. Tree View (List)

**Switch View**: Click list icon in top-right

**Features**:
- Sortable columns
- Color-coded rows by status
- Quick filters in search panel
- Export to Excel/CSV
- Batch selection for operations

#### Visible Columns

- Document # | Clave | Type | Invoice | Customer | Date | Amount | Status | Email Sent

#### Optional Columns

Right-click column headers to show/hide:
- Submission Date
- Acceptance Date
- Company (multi-company setups)

### 3. Form View (Detail)

**Access**: Click any e-invoice to open detailed view

#### Header Section

**Action Buttons** (context-aware):
- **Generate XML**: Creates v4.4 compliant XML
- **Sign XML**: Applies digital signature
- **Submit to Hacienda**: Sends to government API
- **Check Status**: Queries Hacienda for updates

**Status Bar**: Visual workflow progress indicator

#### Smart Buttons (Top-right)

1. **Invoice**: Jump to related invoice
2. **Download XML**: Download signed XML file
3. **Hacienda Response**: View API response details

#### Document Information

**Main Info Tab**:
```
Document Type: [FE|TE|NC|ND badge]
Invoice: [Link to account.move]
Customer: [Partner name]
Date: [Invoice date]
Amount: [Total with currency]
```

**Hacienda Info Tab**:
```
Clave: [50-digit key with copy button]
Submission Date: [Timestamp]
Acceptance Date: [Timestamp]
Response Message: [Latest status message]
Retry Count: [Number of retries]
```

#### Error Banner

When state = 'error' or 'rejected', a red alert banner appears showing:
```
┌─────────────────────────────────────────┐
│ ⚠ Error Details:                        │
│ [Detailed error message from system]    │
└─────────────────────────────────────────┘
```

#### Tabs

1. **XML Content** (Technical users only)
   - Raw generated XML
   - Syntax highlighting
   - Read-only

2. **Signed XML** (Technical users only)
   - XML with digital signature
   - Syntax highlighting
   - Read-only

3. **Hacienda Response**
   - Full API response
   - JSON formatted
   - Error details if rejected

4. **Attachments**
   - XML file
   - PDF with QR code (when available)
   - Download links

5. **Email**
   - Email sent status
   - Send date
   - Resend button

#### Chatter (Bottom)

- Activity tracking
- System notes
- Manual notes
- Email history

### 4. Activity View

**Access**: Switch to calendar/activity view

**Purpose**: Plan follow-ups for rejected or error documents

**Features**:
- Activity scheduling
- Deadline tracking
- Assignee management
- Priority flags

### 5. Search & Filters

#### Quick Filters

Pre-configured filters in search panel:

**By Status**:
- Draft
- Generated
- Signed
- Submitted
- Accepted
- Rejected
- Error

**By Document Type**:
- Facturas Electrónicas (FE)
- Tiquetes Electrónicos (TE)
- Notas de Crédito (NC)
- Notas de Débito (ND)

**By Email Status**:
- Email Sent
- Email Pending

**By Date Range**:
- Today
- This Week
- This Month

#### Group By Options

Organize data by:
- Status
- Document Type
- Customer
- Invoice Date
- Submission Date
- Company (multi-company)

#### Search Fields

Search by:
- Document Number
- Hacienda Key (Clave)
- Invoice Number
- Customer Name

---

## Invoice Integration

### Invoice Form Enhancements

When viewing a Costa Rican invoice (Accounting > Invoices):

#### Smart Button: E-Invoice Status

**Location**: Top-right button box

**States**:
1. **No E-Invoice**: "Create E-Invoice" button
2. **Has E-Invoice**: Status badge (Accepted/Rejected/etc.)

#### E-Invoice Information Group

**Location**: After invoice header section

**Shows**:
```
┌─── Electronic Invoice (Costa Rica) ────┐
│ E-Invoice: [Link to document]          │
│ Status: [Badge: Accepted/Rejected/etc] │
│ Clave: [50-digit key] [Copy button]    │
└────────────────────────────────────────┘
```

#### Header Action Button

**"Generate & Send E-Invoice"**
- Appears when invoice is posted and requires e-invoice
- Runs complete workflow:
  1. Create e-invoice document
  2. Generate XML
  3. Sign XML
  4. Submit to Hacienda
  5. Send email to customer (if accepted)
- Shows confirmation dialog before execution

### Invoice List View

Added column: **E-Invoice Status**
- Color-coded badge
- Optional column (can be hidden)
- Sortable and filterable

### Invoice Filters

New filters added:
- E-Invoice Accepted
- E-Invoice Rejected
- E-Invoice Pending
- E-Invoice Error
- Requires E-Invoice

---

## Configuration

### Settings (General)

**Path**: Settings > Accounting > Costa Rica Electronic Invoicing

#### 1. Hacienda Environment

```
( ) Sandbox (Testing)
(*) Production
```

**Use Sandbox for**:
- Initial setup
- Testing workflows
- Training users

**Switch to Production when**:
- All tests successful
- Real certificate installed
- Ready for live operations

#### 2. API Credentials

```
Username: cpj-xxx-xxxxxx
Password: ****************
[Test Connection] button
```

**Test Connection**: Verifies API access before processing invoices

**Expected Result**:
✅ Success: "Connection successful. API is responding correctly."
❌ Failure: "Connection test failed: [error message]"

#### 3. Digital Certificate

```
Certificate (.crt or .pem): [Choose File] certificate.pem
Private Key (.key or .pem): [Choose File] privatekey.pem
Key Password: ******** (if encrypted)
```

**Requirements**:
- Valid X.509 certificate in PEM format
- Issued by recognized Costa Rican CA
- Registered with Hacienda
- Private key matches certificate

**Info Alert**:
```
ℹ The certificate must be issued by a recognized Costa Rican CA
  and registered with Hacienda. For testing, you can use a
  self-signed certificate in Sandbox mode.
```

#### 4. Emisor Location Code

```
Emisor Location: [01010100]
```

**Format**: 8 digits: Provincia-Canton-Distrito-Barrio

**Example**: 01010100 = San José, Carmen, Merced, La California

**Reference**:
| Code | Location |
|------|----------|
| 01 | San José (Provincia) |
| 01 | San José (Cantón) |
| 01 | Carmen (Distrito) |
| 00 | No specific barrio |

#### 5. Email Template

```
E-Invoice Email Template: [Costa Rica E-Invoice Email]
```

Select template for customer emails. Template should include:
- XML attachment
- PDF with QR code
- Acceptance message
- Support contact

#### 6. Automation Settings

```
☑ Auto-generate E-Invoice
  Automatically create electronic invoice when posting invoices

☐ Auto-submit to Hacienda
  Automatically submit signed electronic invoices to Hacienda

⚠ Warning: This will automatically submit ALL invoices to
  Hacienda. Make sure your certificate and credentials are
  correctly configured.

☑ Auto-send Email
  Automatically send email to customer when e-invoice is accepted
```

**Recommended Settings**:

**For Testing**:
- ✅ Auto-generate: ON
- ❌ Auto-submit: OFF (manual review)
- ✅ Auto-send email: ON

**For Production**:
- ✅ Auto-generate: ON
- ✅ Auto-submit: ON (after thorough testing)
- ✅ Auto-send email: ON

#### Getting Started Checklist

```
ℹ Getting Started with Costa Rica E-Invoicing

1. Register your company with Hacienda and obtain API credentials
2. Obtain a valid X.509 digital certificate from a recognized CA
3. Configure the settings above (start with Sandbox for testing)
4. Test the connection to Hacienda API
5. Create a test invoice and verify the complete workflow
6. Once verified, switch to Production environment
```

### Company Settings

**Path**: Settings > Companies > [Your Company] > Hacienda (CR E-Invoicing) tab

**Same fields as general settings**, but company-specific for multi-company setups.

**Certificate Requirements**:
```
✅ Must be a valid X.509 certificate in PEM format
✅ Must be issued by a recognized Costa Rican CA
✅ Must be registered with Ministry of Finance
✅ Private key must match the certificate
```

---

## Workflows

### Workflow 1: Manual E-Invoice Creation

**Scenario**: Create and submit e-invoice step-by-step

1. **Create Invoice**
   - Navigate to: Accounting > Invoices > Create
   - Select Costa Rican customer
   - Add invoice lines
   - Validate invoice

2. **Create E-Invoice**
   - Click "Create E-Invoice" smart button
   - System creates draft e-invoice document

3. **Generate XML**
   - Open e-invoice form
   - Click "Generate XML" button
   - System creates clave and XML content
   - Status: Draft → Generated

4. **Sign XML**
   - Click "Sign XML" button
   - System applies digital signature
   - XML attachment created
   - Status: Generated → Signed

5. **Submit to Hacienda**
   - Click "Submit to Hacienda" button
   - System sends to API
   - Status: Signed → Submitted

6. **Check Status** (if needed)
   - Click "Check Status" button
   - System queries Hacienda
   - Status: Submitted → Accepted/Rejected

7. **Send Email** (if accepted)
   - Email sent automatically (if configured)
   - Or manually from Email tab

### Workflow 2: Automated E-Invoice

**Scenario**: One-click complete workflow

1. **Create & Post Invoice**
   - Create invoice for CR customer
   - Post invoice

2. **Generate & Send**
   - Click "Generate & Send E-Invoice" button
   - Confirm action
   - System processes all steps automatically

3. **Monitor Status**
   - Check e-invoice smart button for status
   - Review dashboard for overview

### Workflow 3: Batch Processing

**Scenario**: Process multiple pending invoices

1. **Select Pending Invoices**
   - Navigate to: Hacienda (CR) > Pending E-Invoices
   - Filter/search as needed
   - Select multiple invoices (checkboxes)

2. **Batch Generate**
   - Click "Action" dropdown
   - Select "Batch Generate E-Invoices"
   - Configure options:
     - ☑ Auto-submit
     - ☑ Auto-send email
   - Click "Process"

3. **Monitor Progress**
   - System processes each invoice
   - View results in dashboard
   - Review any errors

### Workflow 4: Handling Rejections

**Scenario**: E-invoice rejected by Hacienda

1. **Identify Rejection**
   - Dashboard shows rejected count
   - Or: Hacienda (CR) > E-Invoice Errors
   - Red badge on invoice

2. **Review Error**
   - Open e-invoice form
   - Read error banner message
   - Check Hacienda Response tab for details

3. **Fix Root Cause**
   - Common issues:
     - Invalid VAT number
     - Incorrect tax codes
     - Missing product codes (Cabys)
     - Certificate problems
   - Fix data on original invoice

4. **Retry Submission**
   - E-invoice remains in "rejected" state
   - Fix invoice data
   - Create new e-invoice (if needed)
   - Or retry from current state (if appropriate)

### Workflow 5: Monthly Closing

**Scenario**: End-of-month verification

1. **Review Dashboard**
   - Navigate to: Hacienda (CR) > Dashboard
   - Check acceptance rate
   - Identify outstanding items

2. **Process Pending**
   - Handle any submitted-but-not-accepted
   - Click "Check Status" on each
   - Follow up on errors

3. **Verify Email Delivery**
   - Filter: "Email Pending"
   - Resend as needed

4. **Generate Report**
   - Export accepted invoices list
   - Archive XML files
   - Document any rejections

---

## Dashboard & Reports

### Dashboard View

**Path**: Hacienda (CR) > Dashboard

#### KPI Cards (Top Section)

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Accepted    │  Submitted   │  Rejected    │  Errors      │
│     234      │      12      │       3      │      1       │
│  This Month  │  This Month  │  This Month  │  This Month  │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

Click any card to view filtered list.

#### Charts

**1. Status Distribution (Pie Chart)**
- Visual breakdown of e-invoices by status
- Click slice to filter

**2. Document Types (Pie Chart)**
- Distribution of FE/TE/NC/ND
- Shows invoice mix

**3. Monthly Trend (Line Chart)**
- E-invoices over time
- Multiple lines for each status
- Helps identify patterns

**4. Detailed Analysis (Pivot Table)**
- Rows: Status
- Columns: Document Type
- Values: Total Amount
- Drill-down capability

### Graph View

**Access**: From dashboard or switch view on e-invoice list

**Chart Types**:
- Bar Chart (default)
- Line Chart
- Pie Chart

**Measures**:
- Count of documents
- Total amount
- Average amount

**Grouping**:
- By status
- By document type
- By date (day/week/month)
- By customer

### Pivot View

**Access**: Switch view icon > Pivot

**Use Cases**:
- Complex analysis
- Cross-tabulation
- Financial summaries
- Trend analysis

**Features**:
- Drag-and-drop dimensions
- Multiple measures
- Export to Excel
- Expand/collapse groups

---

## Troubleshooting

### Common Issues

#### 1. Cannot Create E-Invoice

**Symptom**: "Create E-Invoice" button not visible

**Causes**:
- Invoice not posted
- Customer not from Costa Rica
- Company not Costa Rican
- E-invoice already exists

**Solution**:
1. Verify invoice is posted (state = "Posted")
2. Check customer country = Costa Rica
3. Check company country = Costa Rica
4. Look for existing e-invoice smart button

#### 2. XML Generation Fails

**Symptom**: State changes to "Error" after clicking "Generate XML"

**Common Errors**:

**"Missing VAT number"**
- Solution: Add VAT to company and customer

**"Invalid emisor location"**
- Solution: Configure location in Settings

**"Missing product code"**
- Solution: Add Cabys codes to products

**"Sequence not configured"**
- Solution: Install data files (sequences.xml)

#### 3. Signature Fails

**Symptom**: Error when clicking "Sign XML"

**Causes**:
- Certificate not uploaded
- Private key missing
- Password incorrect
- Certificate expired
- Key doesn't match certificate

**Solution**:
1. Settings > Costa Rica Electronic Invoicing
2. Upload certificate and private key
3. Verify password (if encrypted)
4. Test with openssl:
   ```bash
   openssl x509 -in cert.pem -text -noout
   openssl rsa -in key.pem -check
   ```

#### 4. Submission Fails

**Symptom**: Error when clicking "Submit to Hacienda"

**Causes**:
- API credentials incorrect
- Network/firewall issue
- Hacienda system down
- XML format invalid

**Solution**:
1. Test connection: Settings > Test Connection
2. Check credentials
3. Verify network connectivity
4. Check Hacienda status page
5. Review XML in technical view

#### 5. Stuck in "Submitted"

**Symptom**: E-invoice remains in "Submitted" state

**Explanation**: Hacienda is processing. Can take minutes to hours.

**Actions**:
1. Wait 5-10 minutes
2. Click "Check Status"
3. If still submitted after 1 hour, contact Hacienda support

#### 6. Email Not Sending

**Symptom**: "Email Sent" = False despite acceptance

**Causes**:
- Email template not configured
- Customer has no email
- Email server issue
- Auto-send disabled

**Solution**:
1. Check customer email address
2. Settings > Email Template
3. Settings > Auto-send Email (enable)
4. Manual resend: E-Invoice form > Email tab > Resend

### Error Codes from Hacienda

| Code | Meaning | Action |
|------|---------|--------|
| 100 | Validation error | Review XML structure |
| 200 | Invalid certificate | Check certificate registration |
| 300 | Duplicate clave | Already submitted |
| 400 | Invalid receiver | Check customer VAT |
| 500 | System error | Retry later |

### Getting Help

**Documentation**:
- This guide: `docs/USER_GUIDE_PHASE4_UI.md`
- Technical docs: `README.md`
- Hacienda official: https://www.hacienda.go.cr/

**Support**:
- Internal: Check with accounting manager
- Technical: Review logs in Debug mode
- Hacienda: Contact government support desk

**Debug Mode**:
1. Settings > Activate Developer Mode
2. E-Invoice form > Technical tabs visible
3. Review XML Content tab
4. Check server logs

---

## Best Practices

### Daily Operations

1. **Morning Check**
   - Review dashboard
   - Process pending e-invoices
   - Check for overnight errors

2. **Invoice Creation**
   - Use "Generate & Send" for speed
   - Or manual step-by-step for review

3. **Error Handling**
   - Address errors immediately
   - Document recurring issues
   - Update processes as needed

### Monthly Procedures

1. **Month-End**
   - Verify all invoices have e-invoices
   - Check acceptance rate (should be >98%)
   - Export summary report

2. **Archiving**
   - Download all XML files
   - Store securely (required by law)
   - Backup Hacienda responses

3. **Review**
   - Analyze rejection reasons
   - Update product codes
   - Improve data quality

### Performance Tips

1. **Batch Operations**
   - Use for >5 invoices
   - Schedule during off-hours
   - Monitor progress

2. **Automation**
   - Enable after testing period
   - Monitor first week closely
   - Adjust as needed

3. **Filters & Searches**
   - Save custom filters
   - Use grouping for analysis
   - Bookmark common views

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Alt+C | Create new record |
| Alt+E | Edit current record |
| Alt+S | Save |
| Alt+D | Discard changes |
| Ctrl+K | Open command palette |
| / | Focus search |
| Esc | Close dialog |

---

## View Mockup Descriptions

### E-Invoice Kanban Board

```
┌─────────────────────────────────────────────────────────────┐
│ Electronic Invoices                            [+ Create]   │
├─────────────────────────────────────────────────────────────┤
│ [Search...] [Filters▼] [Group By▼] [☰ List] [⊞ Kanban]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Draft (5)  │Generated (3)│ Signed (2) │Submitted │Accepted │
│            │             │            │   (1)    │  (45)   │
│ ┌────────┐ │ ┌────────┐ │ ┌────────┐│          │          │
│ │EI/001  │ │ │EI/004  │ │ │EI/007  ││          │          │
│ │Partner │ │ │Partner │ │ │Partner ││          │          │
│ │₡50,000 │ │ │₡75,000 │ │ │₡100,000││          │          │
│ │[Generate│ │[Sign]    │ │[Submit] ││          │          │
│ └────────┘ │ └────────┘ │ └────────┘│          │          │
│            │             │            │          │          │
└─────────────────────────────────────────────────────────────┘
```

### E-Invoice Form View

```
┌─────────────────────────────────────────────────────────────┐
│ [Generate XML] [Sign XML] [Submit] [Check Status]          │
│ ●━━━━━●━━━━━●━━━━━●━━━━━○━━━━━○  Status: Signed           │
├─────────────────────────────────────────────────────────────┤
│ [Invoice] [Download XML] [Hacienda Response]      🎗 Signed│
│                                                             │
│          Electronic Invoice EI/2024/0001                    │
│                                                             │
│ ┌─ Document Information ──┬─ Hacienda Information ───────┐ │
│ │ Type: [FE Badge]        │ Clave: 50606070501012024... │ │
│ │ Invoice: INV/2024/0123  │ Submission: 2024-01-15 14:30│ │
│ │ Customer: Gimnasio XYZ  │ Acceptance: 2024-01-15 14:35│ │
│ │ Date: 2024-01-15        │ Message: Aceptado           │ │
│ │ Amount: ₡250,000.00     │                              │ │
│ └─────────────────────────┴──────────────────────────────┘ │
│                                                             │
│ [XML Content] [Signed XML] [Hacienda Response] [Email]     │
│                                                             │
│ ╔═══════════════════════════════════════════════════════╗  │
│ ║ Follow-up Notes                                        ║  │
│ ║ • Created by System on 2024-01-15 14:25               ║  │
│ ║ • XML generated successfully                          ║  │
│ ║ • Signed with certificate                             ║  │
│ ║ • Submitted to Hacienda                               ║  │
│ ║ • Accepted by Hacienda                                ║  │
│ ╚═══════════════════════════════════════════════════════╝  │
└─────────────────────────────────────────────────────────────┘
```

### Settings Page

```
┌─────────────────────────────────────────────────────────────┐
│ Settings > Costa Rica Electronic Invoicing                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Hacienda Environment: ● Sandbox  ○ Production              │
│                                                             │
│ API Credentials                                             │
│   Username: cpj-000-000000                                  │
│   Password: ****************                                │
│   [Test Connection] ✓ Connection successful                │
│                                                             │
│ Digital Certificate                                         │
│   Certificate: [Choose File] certificate.pem               │
│   Private Key: [Choose File] privatekey.pem                │
│   Key Password: ********                                    │
│   ℹ Certificate must be registered with Hacienda           │
│                                                             │
│ Automation Settings                                         │
│   ☑ Auto-generate E-Invoice                                │
│   ☐ Auto-submit to Hacienda                                │
│   ☑ Auto-send Email                                        │
│                                                             │
│                                      [Save] [Discard]       │
└─────────────────────────────────────────────────────────────┘
```

---

## Conclusion

This UI implementation provides a complete, user-friendly interface for managing Costa Rica electronic invoices. The views support both novice and expert users with:

- **Visual workflows** via Kanban
- **Detailed management** via Forms
- **Batch operations** for efficiency
- **Real-time monitoring** via Dashboard
- **Comprehensive configuration** via Settings

For technical implementation details, see the developer documentation.

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-28
**Module Version**: 19.0.1.0.0
