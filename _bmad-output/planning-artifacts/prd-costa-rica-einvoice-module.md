# Product Requirements Document
## Costa Rica Electronic Invoicing Module (l10n_cr_einvoice)

**Product Name**: GMS Costa Rica E-Invoice System
**Version**: 2.0 (Rebuild/Enhancement)
**Date**: January 1, 2026
**Owner**: Product Management
**Target Platform**: Odoo 19.0
**Status**: Production Enhancement & Stabilization

---

## 1. Executive Summary

### 1.1 Product Vision
Create the most comprehensive, user-friendly Costa Rica electronic invoicing solution for Odoo that serves both **point-of-sale operations** and **administrative/accounting workflows** with 100% Hacienda compliance and exceptional user experience.

### 1.2 Business Objectives
- **Primary Goal**: Provide seamless Hacienda-compliant invoicing for Costa Rica gyms and businesses
- **Competitive Edge**: First Odoo module with self-service historical invoice import
- **Market Position**: Premium alternative to ₡80K-200K/month SaaS providers
- **User Experience**: Reduce invoicing time from 2-3 minutes to <30 seconds (POS), maintain administrative efficiency

### 1.3 Success Metrics
- **Technical**: 100% Hacienda v4.4 compliance (all 146 requirements)
- **Performance**: <2s invoice generation, <5s Hacienda submission
- **User Adoption**: 95%+ invoice acceptance rate from Hacienda
- **Business Impact**: 2-3 day migration vs 1 week competitor average
- **Support**: <5% error rate requiring manual intervention

### 1.4 Current Status
- **Completion**: ~45% (Phases 1, 2, 2.5 complete, Phase 4 partial)
- **Code Base**: 27 Python files, 27 XML files, 10,000+ lines
- **Investment**: $7,900 spent, ~$7K remaining
- **Risk**: Module currently unstable, requires rebuild/stabilization

---

## 2. User Personas

### 2.1 Primary Personas

#### **Persona A: María - Gym Receptionist (POS User)**
- **Role**: Front desk, daily sales
- **Tech Savvy**: Low-Medium
- **Daily Tasks**:
  - Process 20-50 member payments
  - Generate tiquetes for products/services
  - Handle SINPE Móvil payments
- **Pain Points**:
  - Slow checkout reduces member satisfaction
  - Complex systems cause errors
  - Network issues lose sales
- **Goals**:
  - Fast checkout (<30 seconds)
  - Simple interface
  - Reliable offline mode

#### **Persona B: Carlos - Gym Administrator (Power User)**
- **Role**: Operations manager, monthly billing
- **Tech Savvy**: Medium-High
- **Monthly Tasks**:
  - Process 200+ membership invoices
  - Import historical invoices during migration
  - Handle credit notes and adjustments
  - Manage customer data
- **Pain Points**:
  - Manual data entry takes hours
  - Previous provider migrations are painful
  - Error correction is time-consuming
- **Goals**:
  - Bulk operations support
  - Self-service import tools
  - Clear error messaging

#### **Persona C: Ana - Gym Owner (Decision Maker)**
- **Role**: Business owner, financial oversight
- **Tech Savvy**: Medium
- **Monthly Tasks**:
  - Review financial reports
  - Monitor compliance status
  - Prepare tax filings
- **Pain Points**:
  - Hacienda compliance stress
  - Lack of business insights
  - High software costs
- **Goals**:
  - Clear compliance dashboard
  - Financial analytics
  - Cost-effective solution

#### **Persona D: Luis - Accountant (Professional User)**
- **Role**: External accountant, tax filing
- **Tech Savvy**: High
- **Quarterly Tasks**:
  - Generate D101, D150, D151 tax reports
  - Audit invoice records
  - Verify Hacienda submissions
- **Pain Points**:
  - Missing documentation
  - Disorganized records
  - Manual report compilation
- **Goals**:
  - Instant document retrieval
  - Automated tax reports
  - Complete audit trails

---

## 3. Product Requirements

### 3.1 MUST HAVE - Core Requirements (Priority 1)

#### 3.1.1 POS Features

**REQ-POS-001: Tiquete Electrónico Generation**
- **User Story**: As María (receptionist), I need to generate tiquetes in <30 seconds so checkout is fast
- **Acceptance Criteria**:
  - Generate XML v4.4 compliant tiquete
  - Auto-assign sequence number
  - Support all 5 payment methods
  - Display QR code on receipt
  - Handle offline queue gracefully
- **Technical Notes**: Uses `account.move` with `document_type=04`
- **Dependencies**: Payment method catalog, sequence configuration
- **Priority**: CRITICAL

**REQ-POS-002: SINPE Móvil Payment Tracking**
- **User Story**: As María, I need to record SINPE Móvil payments with transaction IDs for Hacienda compliance
- **Acceptance Criteria**:
  - Payment method selector includes SINPE (code 06)
  - Transaction ID field appears when SINPE selected
  - Transaction ID included in XML generation
  - Validation prevents submission without transaction ID
- **Technical Notes**: Payment method code 06 mandatory since v4.4
- **Dependencies**: Payment methods catalog (Phase 1A)
- **Priority**: HIGH

**REQ-POS-003: Offline Queue Management**
- **User Story**: As María, I need the system to queue invoices during network outages so no sales are lost
- **Acceptance Criteria**:
  - Detect network connectivity loss
  - Store pending invoices in local queue
  - Auto-submit when connection restored
  - Show queue status in UI
  - Notify user of submission results
- **Technical Notes**: Model `einvoice.offline.queue`
- **Dependencies**: Network monitoring, background jobs
- **Priority**: HIGH

#### 3.1.2 Administrative Features

**REQ-ADMIN-001: Factura Electrónica Generation**
- **User Story**: As Carlos, I need to generate compliant facturas for membership billing
- **Acceptance Criteria**:
  - Support multiple line items
  - Handle 5 tax rates (13%, 4%, 2%, 1%, Exempt)
  - Apply discount codes (11 types)
  - Include CIIU code for receiver
  - Generate 50-digit clave
  - Pass XSD validation
- **Technical Notes**: Document type 01, uses `xml_generator.py`
- **Dependencies**: Tax catalog, discount codes, CIIU catalog
- **Priority**: CRITICAL

**REQ-ADMIN-002: Credit/Debit Notes**
- **User Story**: As Carlos, I need to issue credit notes for refunds and debit notes for additional charges
- **Acceptance Criteria**:
  - Reference original invoice by clave
  - Support partial or full credit
  - Include reason code
  - Maintain audit trail
  - Update customer balance
- **Technical Notes**: Document types 02 (NC), 03 (ND)
- **Dependencies**: Original invoice lookup
- **Priority**: CRITICAL

**REQ-ADMIN-003: Digital Signature System**
- **User Story**: As Carlos, I need the system to digitally sign all invoices per Hacienda requirements
- **Acceptance Criteria**:
  - Upload PKCS#12 (.p12, .pfx) certificate
  - Support PEM format certificates
  - Password-protected private key extraction
  - XAdES-EPES signature standard
  - Certificate expiry warnings (30 days)
  - Signature validation before submission
- **Technical Notes**: Uses `certificate_manager.py`, `xml_signer.py`
- **Dependencies**: cryptography, pyOpenSSL libraries
- **Priority**: CRITICAL

**REQ-ADMIN-004: Historical Invoice Import (UNIQUE FEATURE)**
- **User Story**: As Carlos, I need to import 200+ invoices from our previous provider in under 30 minutes
- **Acceptance Criteria**:
  - Upload ZIP file with 100+ XML invoices
  - Auto-detect provider format (GTI, FACTURATica, TicoPay, Alegra)
  - Auto-create missing partners and products
  - Handle 18 error types gracefully
  - Generate CSV error report
  - Show batch statistics (success/fail counts)
  - Allow selective retry of failed invoices
  - Compare totals (imported vs system)
- **Technical Notes**: Models `einvoice.import.batch`, `einvoice.import.error`, `einvoice.xml.parser`
- **Dependencies**: XML parsing, partner/product creation logic
- **Priority**: HIGH (Competitive differentiator)
- **Market Impact**: FIRST self-service import in Costa Rica market

#### 3.1.3 Compliance Features

**REQ-COMP-001: v4.4 XML Generation**
- **User Story**: As Ana, I need 100% Hacienda compliance to avoid legal issues
- **Acceptance Criteria**:
  - Generate XML per Tribu-CR v4.4 standard (all 146 changes)
  - Include ProveedorSistemas node
  - Support 20-character identification (expanded from 12)
  - Include receiver economic activity (CIIU)
  - Support 11 discount code types
  - Include SINPE Móvil payment method (code 06)
  - Include CABYS code per line item (mandatory since July 1, 2020)
  - Pass XSD validation
- **Technical Notes**: Uses `xml_generator.py` with v4.4 templates
- **Dependencies**: XSD schemas from Hacienda CDN
- **Priority**: CRITICAL

**REQ-COMP-002: 50-Digit Clave Generation**
- **User Story**: As the system, I need to generate unique global identifiers for each invoice
- **Acceptance Criteria**:
  - Format: Country(3) + Day(2) + Month(2) + Year(2) + IssuerID(12) + Consecutive(20) + Situation(1) + Security(8) = 50 digits
  - Ensure global uniqueness
  - Calculate correct check digit
  - Validate against duplicates
- **Technical Notes**: Algorithm in `einvoice_document.py`
- **Dependencies**: Invoice sequence, issuer configuration
- **Priority**: CRITICAL

**REQ-COMP-003: Hacienda API Integration**
- **User Story**: As Carlos, I need invoices to submit to Hacienda automatically
- **Acceptance Criteria**:
  - Support sandbox and production environments
  - OAuth 2.0 authentication
  - Submit signed XML
  - Parse response (aceptado, rechazado, procesando)
  - Retry logic (3 attempts, exponential backoff)
  - Store response messages (5-year retention)
  - Handle all ID types (01-05)
- **Technical Notes**: Model `hacienda_api_client.py`
- **Dependencies**: OAuth credentials, certificate, network
- **Priority**: CRITICAL

**REQ-COMP-004: CIIU 4 Economic Activity Catalog**
- **User Story**: As Carlos, I need to assign CIIU codes to customers for v4.4 compliance
- **Acceptance Criteria**:
  - 100+ CIIU codes loaded from Hacienda catalog
  - Search by code or description
  - Smart suggestions based on partner category
  - Bulk assignment wizard
  - Grace period enforcement (Oct 6, 2025)
  - Validation prevents invoice without CIIU
- **Technical Notes**: Model `ciiu.code`, data file `ciiu_codes.xml`
- **Dependencies**: Partner model extension
- **Priority**: CRITICAL (v4.4 mandatory)

**REQ-COMP-005: Discount Codes Catalog**
- **User Story**: As Carlos, I need to apply official Hacienda discount codes to invoice lines
- **Acceptance Criteria**:
  - 11 official discount codes loaded
  - Code validation on invoice lines
  - Code "99" requires description
  - XML generation includes codes
- **Technical Notes**: Model `discount.code`, data file `discount_codes.xml`
- **Dependencies**: Invoice line model extension
- **Priority**: HIGH

#### 3.1.4 Reporting & Analytics

**REQ-REPORT-001: E-Invoice Dashboard**
- **User Story**: As Ana, I need a real-time dashboard showing compliance status
- **Acceptance Criteria**:
  - Total invoices submitted today/this month
  - Success rate percentage
  - Pending submissions count
  - Failed submissions with reasons
  - Recent activity log (last 20 invoices)
  - Quick action buttons (retry all, bulk submit)
- **Technical Notes**: Model `einvoice.analytics.dashboard`
- **Dependencies**: Invoice status tracking
- **Priority**: HIGH

**REQ-REPORT-002: Tax Reports (D101, D150, D151)**
- **User Story**: As Luis (accountant), I need to generate Hacienda tax reports quarterly
- **Acceptance Criteria**:
  - D101: Income Tax Report (PDF + XML)
  - D150: VAT Report (PDF + XML)
  - D151: Informative Report (PDF + XML)
  - Date range selection
  - Automatic calculations from invoice data
  - Digital signature for XML submission
  - Export to XML for ATV (Hacienda portal)
- **Technical Notes**: Models `d101_income_tax_report.py`, `d150_vat_report.py`, `d151_informative_report.py`
- **Dependencies**: Invoice data, tax configuration
- **Priority**: MEDIUM-HIGH

#### 3.1.5 REP (Electronic Payment Receipt)

**REQ-COMP-006: REP (Recibo Electrónico de Pago)**
- **User Story**: As Carlos, I need to issue electronic payment receipts for credit sales to comply with Hacienda requirements
- **Acceptance Criteria**:
  - Track credit sales payments
  - VAT deferral until payment received
  - Required for government sales
  - Generate XML v4.4 compliant REP
- **Technical Notes**: Document type REP, mandatory since Sep 1, 2025
- **Dependencies**: Payment tracking, Hacienda API
- **Priority**: CRITICAL

> ⚠️ REP has been mandatory since September 1, 2025. Non-compliance may result in Hacienda penalties.

---

### 3.2 SHOULD HAVE - Enhanced Features (Priority 2)

**REQ-ENH-001: PDF Generation with QR Codes**
- Generate professional invoice PDFs
- Include QR code with 50-digit clave
- Hacienda validation link
- Custom branding (logo, colors)
- Email-ready format

**REQ-ENH-002: Email Automation**
- Auto-send PDF + XML to customers
- Delivery confirmation tracking
- Customizable email templates
- Batch email sending
- Retry failed emails

**REQ-ENH-003: Bulk Operations**
- Bulk signing wizard (sign 100+ invoices)
- Bulk submission to Hacienda
- Batch status checking
- Mass error correction
- Progress tracking

**REQ-ENH-004: Advanced Analytics**
- Revenue analysis by customer/product
- Tax collection reports
- Customer payment behavior
- Performance metrics (submission times)
- Hacienda acceptance trends

**REQ-ENH-005: POS Session Integration**
- Direct POS order → Tiquete automation
- Batch processing for multiple sales
- End-of-day reconciliation
- Cash drawer integration

---

### 3.3 COULD HAVE - Future Enhancements (Priority 3)

**REQ-FUT-002: FEC (Electronic Purchase Invoice)**
- Document purchases from non-registered suppliers
- Buyer-side invoice creation
- Support "No contribuyente" identification

**REQ-FUT-003: Export Invoice**
- 0% VAT for exports
- Incoterms support
- Customs documentation
- Foreign currency handling

**REQ-FUT-004: Multi-Company Support**
- Separate certificates per company
- Company-specific sequences
- Consolidated reporting

---

## 4. UI/UX Requirements

### 4.1 Design Principles (Learned from HuliPractice Analysis)

**PRINCIPLE 1: Progressive Disclosure**
- Show only essential fields initially
- Expand advanced options on demand
- Use accordions for optional sections
- Example: Import wizard shows basic upload first, then advanced mapping

**PRINCIPLE 2: Color-Coded Status**
- **Green**: Accepted by Hacienda (aceptado)
- **Red**: Rejected by Hacienda (rechazado)
- **Yellow**: Processing (procesando)
- **Blue**: Draft/Not submitted
- **Gray**: Cancelled/Voided
- Status badges with icons for quick recognition

**PRINCIPLE 3: Error Recovery Workflows**
- Clear error messages in plain language
- Actionable next steps (not just "Error occurred")
- One-click retry for transient failures
- Inline help text for common errors
- Example: "Certificate expired → Upload new certificate button"

**PRINCIPLE 4: Self-Service Empowerment**
- Users can fix most issues without support
- Bulk operations for power users
- Import/export for data portability
- Audit trails for transparency

**PRINCIPLE 5: Performance Feedback**
- Loading indicators for all async operations
- Progress bars for batch operations
- Success confirmations (not silent success)
- Estimated time for long operations

### 4.2 Key UI Components

#### 4.2.1 Invoice Form
**Layout**:
- **Header Section**: Document type selector, sequence number (auto), date
- **Partner Section**: Customer selector with CIIU code display, autocomplete search
- **Lines Section**: Product/service grid with columns: Item, CABYS Code, Qty, Price, Discount Code, Tax, Total
- **Totals Section**: Subtotal, Taxes (by rate), Discounts, Grand Total
- **Payment Section**: Payment method selector, SINPE transaction ID (conditional)
- **Actions Bar**: Draft/Validate/Submit/Cancel buttons, status badge

**Interactions**:
- Autosave drafts every 30 seconds
- Real-time total calculations
- CIIU code warning if not assigned
- Discount code dropdown with descriptions
- Inline tax rate display per line

#### 4.2.2 Import Wizard (Multi-Step)
**Step 1: Upload**
- Drag-and-drop ZIP file area
- File size limit: 50MB
- Supported formats: ZIP containing XML files
- Preview: File count, total size

**Step 2: Validation**
- Progress bar during XML parsing
- Error count display
- Expandable error list with details
- Continue button (only if some valid)

**Step 3: Mapping**
- Auto-detected provider format
- Partner matching rules (by name, tax ID)
- Product matching rules (by code, name)
- Option: "Create missing partners/products"

**Step 4: Import**
- Batch processing with progress bar
- Real-time success/failure count
- Estimated time remaining
- Pause/Resume controls

**Step 5: Results**
- Summary statistics (imported, failed, skipped)
- Download CSV error report
- Comparison totals (imported vs system)
- Retry failed invoices button

#### 4.2.3 Dashboard (Single Page)
**Layout**: 3-column responsive grid

**Column 1: KPIs**
- Total invoices (today/month/year)
- Acceptance rate (% with chart)
- Pending submissions (count with alert icon)
- Failed submissions (count with error icon)

**Column 2: Recent Activity**
- Last 20 invoices table
- Columns: Date, Number, Customer, Amount, Status
- Click row → Open invoice
- Refresh button for real-time updates

**Column 3: Quick Actions**
- "Submit Pending" button (batch)
- "Retry Failures" button (batch)
- "Generate Report" dropdown (D101/D150/D151)
- "Import Invoices" button → Launch wizard

**Filters**: Date range, document type, status

#### 4.2.4 Error Messages
**Bad Example** (avoid): "Error: Exception in XML generation"

**Good Example** (use):
```
❌ Invoice Cannot Be Submitted
Problem: Customer "Gimnasio Central" does not have a CIIU economic activity code assigned.

Solution:
1. Click "Assign CIIU Code" below
2. Select the appropriate activity (e.g., "9311 - Gym operations")
3. Return here and submit again

[Assign CIIU Code] [Learn More]
```

---

## 5. Technical Requirements

### 5.1 Architecture

**Technology Stack**:
- **Backend**: Python 3.10+, Odoo 19.0 framework
- **Database**: PostgreSQL 13+
- **XML Processing**: lxml, xmlschema
- **Cryptography**: cryptography, pyOpenSSL, signxml
- **HTTP**: requests, zeep (SOAP)
- **QR Codes**: qrcode, pillow
- **PDF**: reportlab, wkhtmltopdf

**Module Structure**:
```
l10n_cr_einvoice/
├── models/              # 27 Python files (10,000+ lines)
│   ├── Core (6 files): einvoice_document, account_move, account_move_line, res_company, res_partner, res_config_settings
│   ├── XML (3 files): xml_generator, xml_signer, xsd_validator
│   ├── Hacienda (2 files): hacienda_api, certificate_manager
│   ├── Import (3 files): einvoice_import_batch, einvoice_import_error, einvoice_xml_parser
│   ├── POS (2 files): pos_config, pos_order
│   ├── Tax Reports (5 files): d101_income_tax_report, d150_vat_report, d151_informative_report, tax_report_period, tax_report_xml_generator
│   ├── Catalogs (3 files): ciiu_code, discount_code, payment_method
│   └── Analytics (2 files): einvoice_analytics_dashboard, qr_generator
├── views/               # 27 XML files
├── data/                # Master data (CIIU, discount codes, sequences)
├── security/            # Access rights, record rules
├── reports/             # PDF templates, QWeb reports
├── wizards/             # Import wizard, bulk operations
├── tests/               # Unit tests, integration tests (2,000+ lines)
└── static/              # JS, CSS, images
```

**Database Models** (Core):
- `einvoice.document` - Main invoice document
- `account.move` - Extended Odoo invoice
- `hacienda.api.client` - API integration
- `certificate.manager` - Certificate storage
- `einvoice.import.batch` - Import batch tracking
- `einvoice.import.error` - Import error details
- `ciiu.code` - Economic activities
- `discount.code` - Discount types
- `payment.method` - Payment methods

### 5.2 Integration Points

**INT-001: Odoo Accounting (account)**
- Extend `account.move` model
- Journal entry creation
- Tax calculation integration
- Payment reconciliation

**INT-002: Costa Rica Localization (l10n_cr)**
- Chart of accounts
- Tax configuration
- Partner identification types

**INT-003: Sales (sale)**
- Sales order → Invoice workflow
- Customer portal access
- Quotation integration

**INT-004: Subscriptions (sale_subscription)**
- Recurring invoice generation
- Membership billing
- Contract management

**INT-005: POS (point_of_sale)**
- POS session integration (planned)
- Order → Tiquete automation (planned)
- Receipt printing (planned)

**INT-006: External Systems**
- **Hacienda Tribu-CR API**: OAuth 2.0, REST/SOAP
- **Email Servers**: SMTP for invoice delivery
- **Payment Gateways**: TiloPay integration (separate module)

### 5.3 Performance Requirements

**PERF-001: Response Times**
- Invoice generation: <2 seconds
- Hacienda submission: <5 seconds
- Dashboard load: <1 second
- Import 100 invoices: <5 minutes
- Search/filter: <500ms

**PERF-002: Scalability**
- Support 10,000+ invoices per month
- Concurrent users: 10+
- Background job processing for heavy tasks
- Database indexing on key fields (clave, partner, date)

**PERF-003: Reliability**
- 99.9% uptime for module functionality
- Graceful degradation (offline queue if Hacienda down)
- Automatic retry with exponential backoff
- Error logging for debugging

### 5.4 Security Requirements

**SEC-001: Certificate Management**
- Encrypted storage of private keys
- Password protection in database (encrypted)
- Certificate expiry monitoring
- Secure certificate upload (HTTPS only)

**SEC-002: Access Control**
- Role-based permissions (Manager, User, Viewer)
- Restrict certificate access to managers
- Audit logs for sensitive operations (signature, submission)
- Multi-company data isolation

**SEC-003: Data Protection**
- 5-year invoice retention (Hacienda requirement)
- Backup and recovery procedures
- GDPR compliance for customer data
- Secure API credentials storage

### 5.5 Compliance Requirements

**COMP-001: Hacienda v4.4 Standard**
- 100% compliance with all 146 v4.4 changes
- XSD validation before submission
- Digital signature (XAdES-EPES)
- 50-digit clave uniqueness
- Provider system identification

**COMP-002: Legal Requirements**
- 5-year document retention
- Audit trail for all changes
- Tax rate accuracy (13%, 4%, 2%, 1%, 0%)
- CIIU code mandatory (since Oct 6, 2025)

**COMP-003: Standards**
- ISO 8601 dates
- UTF-8 encoding
- XML 1.0 specification
- RESTful API design

---

## 6. User Workflows

### 6.1 Workflow 1: Daily POS Sales (María - Receptionist)

**Scenario**: María needs to process a member's monthly payment at the front desk.

**Steps**:
1. Open POS session (or use Invoicing → Create Invoice)
2. Select customer "Juan Pérez" from dropdown (autocomplete search)
3. Add line item: "Membresía Mensual" - ₡25,000
4. Select payment method: "SINPE Móvil"
5. Enter SINPE transaction ID: "123456789"
6. Click "Validate" → System generates tiquete XML
7. System auto-submits to Hacienda (background job)
8. Print receipt with QR code
9. Hand receipt to Juan
10. System shows success notification "Tiquete TE-00123 accepted"

**Expected Time**: <30 seconds
**Error Scenarios**:
- Network down → Invoice queued, submitted when network restored
- Customer has no CIIU code → Warning shown, Carlos must assign later
- Certificate expired → Error shown, manager must upload new certificate

### 6.2 Workflow 2: Monthly Membership Billing (Carlos - Administrator)

**Scenario**: Carlos needs to bill 200 members for monthly memberships.

**Steps**:
1. Go to Subscriptions → Generate Invoices
2. Select date range: "January 1-31, 2026"
3. Click "Generate" → System creates 200 draft invoices
4. Go to Invoicing → Invoices → Filter "Draft"
5. Select all 200 invoices
6. Click "Bulk Operations" → "Validate & Submit"
7. System processes batch:
   - Generates XML for each
   - Signs with certificate
   - Submits to Hacienda (batches of 20)
   - Shows progress bar
8. Results: 198 accepted, 2 failed
9. Click "View Errors" → See 2 customers missing CIIU codes
10. Assign CIIU codes to 2 customers
11. Retry 2 failed invoices → Success

**Expected Time**: 10 minutes for 200 invoices
**Automation**: Scheduled job can run nightly

### 6.3 Workflow 3: Historical Invoice Import (Carlos - Migration)

**Scenario**: Carlos needs to migrate 250 invoices from FACTURATica.

**Steps**:
1. Export XML from FACTURATica (ZIP file)
2. Go to Invoicing → Import Invoices
3. **Step 1 - Upload**: Drag ZIP file → Upload
4. **Step 2 - Validation**: System parses 250 files → 245 valid, 5 errors
5. View errors: 5 files have invalid XML structure
6. **Step 3 - Mapping**:
   - Provider detected: FACTURATica
   - Partner matching: By tax ID (95% match)
   - Product matching: By code (80% match)
   - Enable "Auto-create missing partners/products"
7. **Step 4 - Import**: Click "Start Import"
   - Progress bar: 245/245 processed
   - Time: ~5 minutes
8. **Step 5 - Results**:
   - Imported: 240 invoices
   - Failed: 5 invoices (duplicate claves)
   - Created: 10 new partners, 15 new products
   - Download CSV error report
9. Review 5 failed invoices → Fix duplicate issue
10. Click "Retry Failed" → 5 imported successfully

**Expected Time**: 30 minutes for 250 invoices
**Manual Comparison**: Carlos verifies total amounts match FACTURATica reports

### 6.4 Workflow 4: Quarterly Tax Report (Luis - Accountant)

**Scenario**: Luis needs to generate D150 VAT report for Q1 2026.

**Steps**:
1. Go to Accounting → Tax Reports → D150 VAT Report
2. Click "Create New Report"
3. Select period: "Q1 2026 (Jan 1 - Mar 31)"
4. Click "Calculate" → System aggregates all invoices
5. Review report:
   - Total sales: ₡12,500,000
   - VAT collected (13%): ₡1,625,000
   - Exempt sales: ₡500,000
6. Click "Generate XML" → System creates ATV-format XML
7. Click "Download XML"
8. Upload XML to Hacienda ATV portal
9. Click "Generate PDF" for records
10. Save PDF to accounting folder

**Expected Time**: 5 minutes
**Compliance**: XML ready for Hacienda submission

---

## 7. Competitive Analysis

### 7.1 Market Landscape (Costa Rica E-Invoice Providers)

| Provider | Monthly Cost | Setup Time | Self-Service Import | Odoo Integration | Target Market |
|----------|--------------|------------|---------------------|------------------|---------------|
| **GMS l10n_cr_einvoice** | FREE (module) | 2-3 days | ✅ YES | ✅ Native | SMBs, Gyms |
| FACTURATica | ₡80K-150K | 1 week | ❌ NO | ⚠️ Connector | Enterprise |
| GTI | ₡100K-200K | 1-2 weeks | ❌ NO | ⚠️ API only | Enterprise |
| Alegra | $29-$99 USD | 3-5 days | ❌ NO | ❌ None | SMBs |
| PROCOM | ₡120K+ | 2 weeks | ❌ NO | ⚠️ Limited | Enterprise |
| TicoPay | ₡60K-120K | 1 week | ❌ NO | ❌ None | SMBs |

### 7.2 Our Competitive Advantages

**ADV-001: Self-Service Historical Import**
- **Unique Feature**: FIRST and ONLY module with ZIP import wizard
- **Value**: Saves 10+ hours of manual data entry
- **ROI**: Phase 2.5 alone delivers 1,030%-1,450% Year 1 ROI

**ADV-002: Native Odoo Integration**
- **Advantage**: No API connectors, no middleware, no sync issues
- **Value**: Single source of truth for invoicing/accounting
- **Efficiency**: Real-time data, no duplicate entry

**ADV-003: Cost Savings**
- **Our Cost**: FREE module (hosting/support only)
- **Competitor Cost**: ₡80K-200K/month = ₡960K-2.4M/year
- **Savings**: ₡960K-2.4M annually for typical gym

**ADV-004: Migration Speed**
- **Our Time**: 2-3 days (with import wizard)
- **Competitor Time**: 1-2 weeks (manual entry)
- **Business Impact**: Less downtime, faster ROI

**ADV-005: Customization**
- **Open Source**: Full code access, customizable
- **Gym-Specific**: Built for gym workflows (memberships, POS)
- **Community**: Growing ecosystem, shared improvements

### 7.3 Competitive Gaps to Address

**GAP-001: Multi-Tenant SaaS**
- Competitors offer hosted solutions
- We require Odoo server (self-hosted or SaaS)
- **Mitigation**: Partner with Odoo hosting providers

**GAP-002: Support**
- Competitors include phone support
- We provide community/partner support
- **Mitigation**: Documentation, video tutorials, certified partners

**GAP-003: Mobile Apps**
- Some competitors have mobile apps
- We rely on Odoo web interface (mobile responsive)
- **Future**: Odoo mobile app integration

---

## 8. Implementation Roadmap

### 8.1 Current Status Summary

**Completed Phases**:
- ✅ **Phase 1**: XML Generation (34h, $1,700) - COMPLETE
- ✅ **Phase 1A**: SINPE Móvil (included in Phase 1) - COMPLETE
- ✅ **Phase 1B**: Discount Codes (included in Phase 1) - COMPLETE
- ✅ **Phase 1C**: CIIU Codes (included in Phase 1) - COMPLETE
- ✅ **Phase 2**: Digital Signature (40h, $2,000) - COMPLETE
- ✅ **Phase 2.5**: XML Import (84h, $4,200) - COMPLETE BONUS

**In Progress**:
- 🚧 **Phase 3**: Enhanced Hacienda API (30h est.) - PARTIAL
- 🚧 **Phase 4**: Retry Queue & Polling (25h est.) - PARTIAL

**Planned**:
- ⏳ **Phase 5**: PDF & Email (30h est.)
- ⏳ **Phase 6**: POS Integration (30h est.)
- ⏳ **Phase 7**: Deployment & Monitoring (20h est.)
- ⏳ **Phase 8**: Void Wizard (10h est.)
- ⏳ **Phase 9**: Tax Reports (30h est.)

**Overall Progress**: 45% complete (158h of 333h)

### 8.2 Recommended Rebuild/Stabilization Plan

Given the current module instability, recommend the following approach:

#### Option A: Stabilize & Continue (Recommended for MVP)
**Timeline**: 6-8 weeks
**Effort**: 120-150 hours
**Cost**: $6,000-7,500

**Tasks**:
1. **Diagnostic & Fix (20h)**
   - Identify root cause of installation failure
   - Fix dependency issues (model registration, data loading)
   - Restore module to installable state
   - Comprehensive testing

2. **Code Audit & Refactoring (30h)**
   - Review all 27 Python files for best practices
   - Consolidate redundant code
   - Improve error handling
   - Add logging and debugging

3. **Complete Critical Features (40h)**
   - Finish Phase 3: Enhanced Hacienda API
   - Finish Phase 4: Retry Queue & Polling
   - Test end-to-end workflows

4. **Testing & Validation (30h)**
   - Unit tests for all models
   - Integration tests for workflows
   - Hacienda sandbox testing
   - User acceptance testing (UAT)

**Deliverables**:
- Stable, installable module
- 100% Hacienda compliance verified
- Documentation (admin guide, user guide)
- Test coverage >80%

#### Option B: Rebuild from Scratch (For Long-Term Quality)
**Timeline**: 12-16 weeks
**Effort**: 250-300 hours
**Cost**: $12,500-15,000

**Advantages**:
- Clean architecture
- Modern best practices
- Better maintainability
- Comprehensive testing from start

**Disadvantages**:
- Higher cost
- Longer timeline
- Risk of feature parity issues

**Recommendation**: Use Option A for MVP, then incremental refactoring

### 8.3 Phase Priorities (Post-Stabilization)

**Priority 1 - Critical (Must Have)**
1. **Phase 3**: Enhanced Hacienda API (bulk operations, better error handling)
2. **Phase 4**: Retry Queue & Polling (reliability improvements)
3. **Phase 5**: PDF & Email (customer-facing deliverables)

**Priority 2 - Important (Should Have)**
4. **Phase 6**: POS Integration (receptionist efficiency)
5. **Phase 9**: Tax Reports (accountant compliance)

**Priority 3 - Nice to Have (Could Have)**
6. **Phase 7**: Deployment & Monitoring (operational excellence)
7. **Phase 8**: Void Wizard (edge case handling)

---

## 9. Success Criteria & KPIs

### 9.1 Technical Success Metrics

**Metric 1: Hacienda Acceptance Rate**
- Target: >95% first-time acceptance
- Measurement: (Accepted invoices / Total submitted) * 100
- Current: Unknown (module unstable)

**Metric 2: Performance**
- Invoice generation: <2s (Target: <2s)
- Hacienda submission: <5s (Target: <5s)
- Dashboard load: <1s (Target: <1s)

**Metric 3: Reliability**
- Module uptime: 99.9%
- Failed submissions requiring manual intervention: <5%
- Test coverage: >80%

**Metric 4: Code Quality**
- Code review pass rate: 100%
- Static analysis warnings: 0 critical
- Security vulnerabilities: 0 high/critical

### 9.2 User Experience Metrics

**Metric 5: Task Completion Time**
- POS sale: <30s (vs 2-3 min industry average)
- Monthly billing (200 invoices): <10 min (vs 2-3 hours manual)
- Historical import (250 invoices): <30 min (vs 10+ hours manual)

**Metric 6: User Satisfaction**
- User survey score: >4.5/5
- Feature request rate: <5 per month
- Bug report rate: <2 per month

**Metric 7: Adoption**
- Active users: 100% of billing staff
- Daily usage: >20 invoices/day per gym
- Feature utilization: >80% for core features

### 9.3 Business Impact Metrics

**Metric 8: Cost Savings**
- Software savings vs competitors: ₡960K-2.4M/year
- Migration time savings: 3-5 days (vs 1-2 weeks)
- Data entry time savings: 10+ hours per migration

**Metric 9: Compliance**
- Hacienda audit pass rate: 100%
- Tax filing errors: 0
- Legal violations: 0

**Metric 10: Market Position**
- Unique features: Self-service import (FIRST in market)
- Customer testimonials: >10 gyms using module
- Community contributions: >5 external contributors

---

## 10. Risks & Mitigation

### 10.1 Technical Risks

**RISK-TECH-001: Module Stability Issues**
- **Probability**: HIGH (currently unstable)
- **Impact**: CRITICAL (blocks all usage)
- **Mitigation**:
  - Allocate 20h for diagnostic and fix
  - Comprehensive testing before deployment
  - Rollback plan to known-good version

**RISK-TECH-002: Hacienda API Changes**
- **Probability**: MEDIUM (v4.4 just released)
- **Impact**: HIGH (compliance breakage)
- **Mitigation**:
  - Monitor Hacienda announcements
  - Version detection in code
  - Graceful degradation for new fields

**RISK-TECH-003: Certificate Management Complexity**
- **Probability**: MEDIUM (user error)
- **Impact**: HIGH (can't submit invoices)
- **Mitigation**:
  - Clear documentation with screenshots
  - Validation before upload
  - Expiry warnings (30 days)

**RISK-TECH-004: Performance Degradation**
- **Probability**: MEDIUM (as data grows)
- **Impact**: MEDIUM (slow UX)
- **Mitigation**:
  - Database indexing on key fields
  - Pagination for large lists
  - Background jobs for heavy tasks

### 10.2 Business Risks

**RISK-BUS-001: Competitive Pressure**
- **Probability**: MEDIUM (established players)
- **Impact**: MEDIUM (market share loss)
- **Mitigation**:
  - Focus on unique features (import wizard)
  - Build community ecosystem
  - Faster innovation cycle

**RISK-BUS-002: Support Burden**
- **Probability**: MEDIUM (complex domain)
- **Impact**: MEDIUM (resource drain)
- **Mitigation**:
  - Excellent documentation (admin + user guides)
  - Video tutorials for common tasks
  - Partner certification program

**RISK-BUS-003: Regulatory Changes**
- **Probability**: LOW-MEDIUM (Costa Rica government)
- **Impact**: HIGH (compliance breakage)
- **Mitigation**:
  - Modular code design (easy updates)
  - Version detection and warnings
  - Active monitoring of Hacienda announcements

### 10.3 User Adoption Risks

**RISK-USER-001: Migration Complexity**
- **Probability**: MEDIUM (user unfamiliarity)
- **Impact**: MEDIUM (delayed adoption)
- **Mitigation**:
  - Import wizard (self-service)
  - Migration checklist/guide
  - Partner support for complex cases

**RISK-USER-002: Training Needs**
- **Probability**: MEDIUM (new system)
- **Impact**: LOW (temporary inefficiency)
- **Mitigation**:
  - Video tutorials (5-10 min each)
  - Quick reference cards
  - In-app help text

---

## 11. Dependencies & Assumptions

### 11.1 External Dependencies

**DEP-001: Hacienda Tribu-CR API**
- **Dependency**: Hacienda maintains stable API
- **Assumption**: API downtime <1% per month
- **Risk**: API changes break integration
- **Mitigation**: Monitor Hacienda announcements, version detection

**DEP-002: Odoo Framework**
- **Dependency**: Odoo 19.0 compatibility
- **Assumption**: No breaking changes in Odoo 19.x
- **Risk**: Odoo upgrades break module
- **Mitigation**: Pin version, test before upgrades

**DEP-003: Certificate Authorities**
- **Dependency**: Users have valid Hacienda certificates
- **Assumption**: Certificates issued by authorized CAs
- **Risk**: Certificate expiry/revocation
- **Mitigation**: Expiry monitoring, renewal reminders

### 11.2 Internal Assumptions

**ASSUM-001: User Technical Skills**
- **Assumption**: Users are comfortable with basic Odoo navigation
- **Implication**: Need training materials for non-technical users
- **Validation**: User testing with actual gym staff

**ASSUM-002: Data Quality**
- **Assumption**: Customer data (tax IDs, names) is accurate
- **Implication**: Import wizard may fail with bad data
- **Validation**: Data validation rules, cleansing tools

**ASSUM-003: Network Reliability**
- **Assumption**: Internet connectivity is stable (>95% uptime)
- **Implication**: Offline queue needed for network failures
- **Validation**: Test offline mode in production-like conditions

**ASSUM-004: Business Requirements Stability**
- **Assumption**: Costa Rica e-invoice rules are mostly stable post-v4.4
- **Implication**: Major changes could require significant rework
- **Validation**: Monitor regulatory landscape, build modular code

---

## 12. Documentation Requirements

### 12.1 User Documentation

**DOC-USER-001: Quick Start Guide**
- Audience: Gym receptionists, administrators
- Format: PDF, 5-10 pages with screenshots
- Content:
  - Installation overview (for admins)
  - Creating first invoice
  - Submitting to Hacienda
  - Handling common errors

**DOC-USER-002: Administrator Guide**
- Audience: Gym administrators, IT staff
- Format: PDF, 30-50 pages
- Content:
  - Installation and configuration
  - Certificate setup
  - CIIU code management
  - Import wizard walkthrough
  - Bulk operations
  - Troubleshooting

**DOC-USER-003: Accountant Guide**
- Audience: External accountants
- Format: PDF, 15-20 pages
- Content:
  - Tax report generation (D101/D150/D151)
  - Audit trail navigation
  - Document retrieval
  - Compliance verification

**DOC-USER-004: Video Tutorials**
- Audience: All users
- Format: YouTube/Vimeo, 5-10 min each
- Topics:
  - Creating and submitting a factura (5 min)
  - Importing historical invoices (10 min)
  - Generating tax reports (7 min)
  - Fixing common errors (8 min)

### 12.2 Technical Documentation

**DOC-TECH-001: Developer Guide**
- Audience: Odoo developers, contributors
- Format: Markdown, hosted on GitHub
- Content:
  - Module architecture
  - Model relationships (ERD)
  - API reference (public methods)
  - Extension points (hooks)
  - Testing guide

**DOC-TECH-002: API Documentation**
- Audience: Integration developers
- Format: Swagger/OpenAPI spec
- Content:
  - Hacienda API endpoints used
  - Request/response formats
  - Error codes and handling
  - Rate limits and retries

**DOC-TECH-003: Database Schema**
- Audience: Database administrators
- Format: ERD diagram + Markdown
- Content:
  - All models and fields
  - Relationships and foreign keys
  - Indexes and constraints
  - Migration scripts

**DOC-TECH-004: Security Guide**
- Audience: Security auditors, IT admins
- Format: PDF, 10-15 pages
- Content:
  - Certificate storage security
  - Access control configuration
  - Audit logging
  - GDPR compliance

---

## 13. Testing Strategy

### 13.1 Unit Testing

**TEST-UNIT-001: Model Tests**
- Coverage target: >90%
- Frameworks: Odoo test framework, Python unittest
- Scope:
  - All compute fields
  - All constraint methods
  - All business logic methods
- Example: Test 50-digit clave generation algorithm

**TEST-UNIT-002: XML Generation Tests**
- Validate XML structure against XSD
- Test all document types (FE, TE, NC, ND, MR)
- Test all edge cases (zero tax, multiple taxes, discounts)
- Verify v4.4 compliance (146 requirements)

**TEST-UNIT-003: Certificate Tests**
- Test PKCS#12 and PEM import
- Test password-protected keys
- Test expiry detection
- Test signature generation

### 13.2 Integration Testing

**TEST-INT-001: Hacienda API Tests**
- Use Hacienda sandbox environment
- Test all submission scenarios (accept, reject, timeout)
- Test retry logic (3 attempts)
- Test OAuth authentication

**TEST-INT-002: Import Wizard Tests**
- Test 5 provider formats (GTI, FACTURATica, etc.)
- Test 100+ invoice ZIP files
- Test error handling (18 error types)
- Verify partner/product auto-creation

**TEST-INT-003: POS Integration Tests**
- Test POS order → Tiquete workflow
- Test offline queue (network down/up)
- Test batch processing

### 13.3 User Acceptance Testing (UAT)

**TEST-UAT-001: Real Gym Testing**
- Partner with 2-3 gyms for beta testing
- Test workflows with actual staff
- Duration: 2-4 weeks
- Collect feedback on usability, performance

**TEST-UAT-002: Accountant Review**
- Have external accountant validate tax reports
- Verify D101/D150/D151 accuracy
- Test audit trail completeness

**TEST-UAT-003: Migration Testing**
- Test import wizard with real data from competitors
- Verify data accuracy (compare totals)
- Measure time savings vs manual entry

### 13.4 Performance Testing

**TEST-PERF-001: Load Testing**
- Simulate 1,000+ invoice submissions
- Measure response times (p50, p95, p99)
- Identify bottlenecks (database, API calls)

**TEST-PERF-002: Stress Testing**
- Test concurrent users (10+ simultaneous)
- Test large batch operations (500+ invoices)
- Verify graceful degradation under load

### 13.5 Security Testing

**TEST-SEC-001: Penetration Testing**
- Test certificate upload security
- Test SQL injection vulnerabilities
- Test XSS in user inputs
- Test access control bypasses

**TEST-SEC-002: Data Privacy Audit**
- Verify customer data encryption
- Test data retention policies (5 years)
- Verify GDPR compliance (right to erasure)

---

## 14. Deployment Strategy

### 14.1 Deployment Environments

**ENV-001: Development**
- Purpose: Active development and testing
- Update frequency: Daily
- Data: Synthetic test data
- Hacienda: Sandbox environment

**ENV-002: Staging**
- Purpose: Pre-production testing, UAT
- Update frequency: Weekly
- Data: Anonymized production clone
- Hacienda: Sandbox environment

**ENV-003: Production**
- Purpose: Live gym operations
- Update frequency: Monthly (or as needed for critical fixes)
- Data: Real customer data
- Hacienda: Production environment

### 14.2 Deployment Process

**DEPLOY-001: Release Checklist**
1. ✅ All tests passing (unit, integration, UAT)
2. ✅ Code review approved
3. ✅ Documentation updated
4. ✅ Changelog written
5. ✅ Backup production database
6. ✅ Deploy to staging → Smoke test
7. ✅ Deploy to production (off-peak hours)
8. ✅ Smoke test production
9. ✅ Monitor for 24 hours
10. ✅ Notify users of new features

**DEPLOY-002: Rollback Plan**
- Keep previous version for 30 days
- Database backup before each deployment
- Rollback command: `odoo -d DB -u l10n_cr_einvoice --version=X.Y.Z`
- Test rollback in staging before production

### 14.3 Monitoring & Alerting

**MONITOR-001: Application Metrics**
- Invoice submission success rate (target: >95%)
- Average response times (API calls, page loads)
- Error rate by type (Hacienda errors, validation errors)
- Certificate expiry dates

**MONITOR-002: Infrastructure Metrics**
- Server CPU/memory usage
- Database performance (slow queries)
- Network latency to Hacienda API
- Disk space (document storage)

**MONITOR-003: Alerts**
- Critical: Certificate expires in <7 days
- Critical: Hacienda submission failure rate >10%
- Warning: Certificate expires in <30 days
- Warning: Average response time >5s
- Info: New module version available

---

## 15. Support & Maintenance

### 15.1 Support Channels

**SUPPORT-001: Community Support**
- Forum: Odoo Community Forum (l10n_cr_einvoice tag)
- Response time: Best effort (1-3 days)
- Cost: FREE
- Scope: General questions, feature requests

**SUPPORT-002: Partner Support**
- Provider: Certified Odoo partners
- Response time: 24-48 hours (business days)
- Cost: Varies by partner (typically $50-150/hour)
- Scope: Implementation, customization, training

**SUPPORT-003: Documentation**
- Quick Start Guide (PDF)
- Administrator Guide (PDF)
- Video Tutorials (YouTube)
- FAQ (Wiki)

### 15.2 Maintenance Plan

**MAINT-001: Bug Fixes**
- Critical bugs: Hotfix within 24-48 hours
- High-priority bugs: Fix in next weekly release
- Low-priority bugs: Fix in next monthly release
- Process: GitHub Issues → Triage → Fix → Test → Deploy

**MAINT-002: Feature Updates**
- Minor features: Monthly releases
- Major features: Quarterly releases
- Breaking changes: Major version (e.g., 2.0 → 3.0)
- Process: GitHub Discussions → PRD → Implementation → UAT → Deploy

**MAINT-003: Compliance Updates**
- Monitor Hacienda announcements (weekly)
- Test new requirements in sandbox
- Deploy compliance updates ASAP (target: <2 weeks)
- Notify users of mandatory updates

---

## 16. Appendices

### Appendix A: Glossary

**Terms**:
- **Clave**: 50-digit unique numeric key for each invoice
- **FE**: Factura Electrónica (Electronic Invoice)
- **TE**: Tiquete Electrónico (Electronic Receipt)
- **NC**: Nota de Crédito (Credit Note)
- **ND**: Nota de Débito (Debit Note)
- **MR**: Mensaje Receptor - acceptance/rejection message sent to Hacienda when receiving supplier invoices (types: 05-Acceptance, 06-Partial Acceptance, 07-Rejection)
- **CABYS**: Catálogo de Bienes y Servicios - mandatory 13-digit product/service classification code required on all invoice line items since July 1, 2020
- **CIIU**: International Standard Industrial Classification (economic activity codes)
- **Hacienda**: Costa Rica Ministry of Finance (Ministerio de Hacienda)
- **Tribu-CR**: Costa Rica e-invoice standard (v4.4 as of Sep 1, 2025)
- **XAdES-EPES**: XML Advanced Electronic Signature (digital signature standard)
- **ATV**: Hacienda online portal for tax filing
- **REP**: Recibo Electrónico de Pago (Electronic Payment Receipt)

### Appendix B: Costa Rica Tax Rates

**Current Rates** (as of 2026):
- **13%**: General VAT (Impuesto al Valor Agregado)
- **4%**: Reduced VAT (e.g., some food items)
- **2%**: Reduced VAT (e.g., medicines)
- **1%**: Reduced VAT (e.g., essential goods)
- **0%**: Exempt (e.g., exports, financial services)

### Appendix C: Hacienda Response Codes

**Status Codes**:
- **1**: Aceptado (Accepted) - Invoice approved
- **2**: Rechazado (Rejected) - Invoice rejected (errors)
- **3**: Procesando (Processing) - Still being validated
- **4**: Error (Error) - System error, retry needed

**Common Rejection Reasons**:
- Invalid tax ID (cédula)
- Duplicate clave
- Invalid XML structure
- Missing required fields (e.g., CIIU code)
- Certificate issues (expired, revoked)

### Appendix D: Research Document References

**Primary Sources**:
1. `HULIPRACTICE-COMPETITIVE-ANALYSIS.md` - UI/UX insights
2. `COSTA-RICA-EINVOICING-COMPLETE-RESEARCH-2025.md` - Compliance requirements
3. `HACIENDA-MANDATORY-REQUIREMENTS-V44-COMPLIANCE-AUDIT.md` - v4.4 changes
4. `PHASE-*.md` (Phases 1-9) - Implementation details
5. `invoice-module-research-synthesis.md` - Comprehensive synthesis
6. `l10n_cr_einvoice/` - Module source code

**Additional References**:
- Hacienda documentation: https://www.hacienda.go.cr/
- Tribu-CR specifications: https://tribunet.hacienda.go.cr/
- Odoo developer docs: https://www.odoo.com/documentation/19.0/

### Appendix E: Contact Information

**Product Owner**: [To be assigned]
**Technical Lead**: [To be assigned]
**QA Lead**: [To be assigned]
**Support Contact**: support@gms-einvoice.com (to be created)
**Community Forum**: https://github.com/GMS-CR/l10n_cr_einvoice/discussions

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-01 | Product Management | Initial PRD based on research synthesis |

---

**END OF PRODUCT REQUIREMENTS DOCUMENT**

*This PRD is a living document and will be updated as requirements evolve and new insights are gained. All stakeholders are encouraged to provide feedback through GitHub Discussions or direct communication with the Product Owner.*
