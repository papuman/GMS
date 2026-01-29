# Costa Rica E-Invoicing Migration and Onboarding Research Report

**Report Date:** December 29, 2025
**Purpose:** Production deployment preparation for Odoo 19 e-invoicing module
**Critical Focus:** Migration/onboarding process for users switching from paper or other e-invoicing systems

---

## Executive Summary

### Key Findings

1. **CRITICAL: Invoice Number Continuity is Mandatory** - When migrating from an existing e-invoicing system, businesses MUST continue their consecutive numbering sequence. Starting fresh at "1" is NOT permitted.

2. **No Hacienda Notification Required** - There is NO formal requirement to notify Hacienda (DGT) when changing e-invoicing providers or systems. The continuity of consecutive numbers is self-regulated.

3. **System Provider Identification Required (v4.4)** - Starting September 1, 2025, all e-invoices must include a "System Provider" field in the XML to identify which software generated the invoice.

4. **Historical Data Import Not Mandatory** - There is no legal requirement to import historical invoices into the new system, though providers like FACTURATica offer this as a value-added service.

5. **Version 4.4 is Mandatory** - As of September 1, 2025, only version 4.4 e-invoices are accepted (except v4.3 credit/debit notes for adjusting old invoices).

### Migration Scenarios

| Scenario | Consecutive Number Handling | Special Requirements |
|----------|----------------------------|---------------------|
| **First-time e-invoicing** (from paper) | Start at 00000000001 | Must register in ATV/OVI as emisor-receptor |
| **Switching providers** (e.g., GDI to Odoo) | Continue from last number used | Must know exact last consecutive per document type |
| **Adding new branch/terminal** | New branch starts at 00000000001 | Branch code (001, 002, etc.) distinguishes sequences |
| **Reached max (9999999999)** | Can restart at 00000000001 | Extremely rare, ~10 billion invoices |
| **Version 4.3 to 4.4 migration** | Continue same sequence | System provider field now mandatory |

---

## 1. Official Hacienda Requirements for Migration

### Legal Framework

**Primary Regulation:** Resolution DGT-R-033-2019 (replaced by MH-DGT-RES-0027-2024 as of Nov 19, 2024)
- Governs technical specifications for electronic vouchers
- Defines consecutive numbering requirements
- Establishes validation and acceptance procedures

**Current Version:** 4.4 (mandatory since September 1, 2025)
- Previous version 4.3 is obsolete except for credit/debit notes adjusting old invoices
- 146 technical changes from v4.3 to v4.4
- New system provider identification field

### Invoice Number Continuity Requirements

#### Consecutive Number Structure (20 digits)

```
AAA-BBBBB-CC-DDDDDDDDDD
│   │      │   │
│   │      │   └─ Digits 11-20: Sequential number (0000000001 to 9999999999)
│   │      └───── Digits 9-10: Document type (01=Invoice, 02=Debit Note, 03=Credit Note, etc.)
│   └──────────── Digits 4-8: Terminal/POS identifier (00001, 00002, etc.)
└──────────────── Digits 1-3: Establishment code (001=headquarters, 002+=branches)
```

#### Migration Rules

**From Resolution DGT-R-033-2019 (confirmed in multiple sources):**

1. **First-time users:** "Numbering begins at 1, assigned automatically by the system"
   - Applies to businesses transitioning from paper invoicing
   - Each document type starts its own sequence at 00000000001

2. **Platform changes:** "Organizations already using e-invoices must maintain the consecutive numbering when switching emission platforms"
   - CRITICAL: This means you CANNOT reset to 1 when changing providers
   - Must continue from the exact next number in sequence

3. **No notification required:** No evidence found of any requirement to notify Hacienda when changing systems
   - The XML itself contains the consecutive number
   - Hacienda's validation system checks for sequence integrity automatically

4. **Sequence reset:** "Once the maximum consecutive number is reached, it is possible to restart from No. 1"
   - Maximum is 9999999999 (10 billion invoices)
   - Extremely unlikely for most businesses

#### Validation and Rejection

- **Automatic validation:** Hacienda's RCE (Recepción de Comprobantes Electrónicos) validates each invoice within 3 hours
- **Rejection reasons:** Duplicate consecutive numbers will cause automatic rejection
- **No manual override:** Once rejected, the consecutive number is "burned" and cannot be reused

### Transition Period Guidelines

**September 1, 2025 - Current:**
- Version 4.4 is mandatory for all new invoices
- Version 4.3 accepted ONLY for credit/debit notes adjusting pre-September invoices
- No grace period or exceptions

**TRIBU-CR Platform Migration (October 6, 2025):**
- New online tax administration system (OVI - Oficina Virtual) launched
- Replaces legacy ATV, TRAVI, DeclaraWeb, and EDDI-7 platforms
- TicoFactura free tool available for small taxpayers
- Access: https://ovitribucr.hacienda.go.cr/home/

### System Change Notification Requirements

**FINDING: No formal notification required**

Despite extensive research, there is NO evidence of:
- A "resolución de autorización" needed to change systems
- A form to submit to Hacienda when switching providers
- A waiting period or approval process
- Any registration of the specific software being used (except the new v4.4 system provider field in XML)

**What IS required:**
1. **ATV/OVI Registration:** Must be registered as "Emisor-Receptor Electrónico" in the tax registry
2. **Digital Certificate:** Must have valid certificate from Banco Central de Costa Rica
3. **System Provider Field (v4.4):** XML must include identifier of software generating invoices
4. **Consecutive Continuity:** Must maintain numbering sequence if already using e-invoicing

---

## 2. Local Provider Practices

### FACTURATica (Market Leader)

**Company Background:**
- Number one e-invoicing solution in Costa Rica since 2018
- Imported over 100 million electronic invoices from migrated customers
- Robust migration support infrastructure

**Onboarding Process:**

1. **Default Configuration:**
   - "FACTURATica by default allows immediate invoicing without any collision by consecutivos"
   - System anticipates that adjusting consecutivos may not be necessary for new users
   - New businesses can start at 00000000001 automatically

2. **Migration from Existing System:**
   - Must request consecutive adjustment via email to facturatica@zarza.com
   - Requires completing a template with last consecutive number for EACH document type:
     - Invoices (01)
     - Tickets (04)
     - Credit Notes (03)
     - Debit Notes (02)
     - Purchase Acceptance (05)
     - Partial Purchase Acceptance (06)
     - Purchase Rejection (07)
     - Electronic Purchase Invoice (08)
     - Export Electronic Invoice (09)

3. **Historical Data Import:**
   - Offers import of historical invoices as value-added service
   - Successfully imported 100+ million invoices for customers
   - NOT legally required, but useful for business continuity

4. **Support:**
   - Email: facturatica@zarza.com
   - Provide template for consecutive configuration
   - Manual review and setup by support team

**Key Insight:** "To adjust the consecutivos, you must know all of them to avoid collisions and rejections, and it's important to consider the last document issued for each electronic voucher."

### TicoPay / Ticontable

**Company Profile:**
- Cloud-based electronic invoicing software
- Focus on SMEs and independent professionals
- 5-year cloud backup included

**Features:**
- Batch XML integration and automatic confirmation
- Approval rules to auto-accept or reject incoming invoices
- Summary dashboard of all XMLs and status with Hacienda
- Unique and recurring invoice generation

**Migration Information:**
- Limited public documentation on migration process
- Blog focuses on ATV registration and basic setup
- Comparison article vs. Hacienda's free system (pre-TRIBU-CR)

**Registration Guide:** Provides step-by-step for ATV registration and cryptographic key download

### Alanube

**Company Profile:**
- Operating in Costa Rica since 2021
- Focus on ERP/CRM/e-commerce integration
- 10-year online backup retention

**Key Features:**
- API integration with management systems
- Compliance guarantee with Hacienda regulations
- Multi-business support

**Migration Information:**
- No specific migration documentation found in public sources
- Emphasizes compliance and integration capabilities
- Likely handles migration through custom onboarding process

### GTI (GDI) Facturación

**Company Profile:**
- Referred to as both GTI and GDI in different sources
- Integrated platform for e-invoicing
- Features client/supplier management and inventory control

**Migration Support:**
- Resources available for migrating FROM GTI to other systems (like Alegra)
- Focus on centralizing accounting in new platforms
- Excel-based initial balance import supported

**Version 4.4 Compliance:**
- Must verify with GTI if they've implemented v4.4 support
- Businesses using GTI need to validate compliance status

### Government-Provided Solutions

**TicoFactura (Free Tool):**
- Launched October 6, 2025 as part of TRIBU-CR
- Available in OVI platform
- Replaces old ATV free invoicing tool
- Target: Small taxpayers with basic needs
- Limitation: Cannot manually modify consecutive numbers (user complaints documented)

**Migration to TicoFactura:**
- Businesses using old ATV free tool had until September 2025 to migrate
- Transition support provided through September-October 2025
- Many businesses opted for paid providers due to consecutive number flexibility

### Provider Comparison Matrix

| Provider | Migration Support | Historical Import | Consecutive Config | Support Quality | Version 4.4 |
|----------|------------------|-------------------|-------------------|----------------|-------------|
| **FACTURATica** | Excellent - 100M+ invoices migrated | Yes, robust | Manual via email | High - documented process | Yes |
| **TicoPay** | Basic - limited documentation | Not advertised | Unknown | Medium - focus on SMEs | Assumed yes |
| **Alanube** | Unknown - custom approach | Likely via integration | API-based | Unknown | Assumed yes |
| **GTI/GDI** | Supports migration OUT | Yes (Excel) | Unknown | Medium | Verify with provider |
| **TicoFactura (Free)** | Government support | No | LOCKED (no manual edit) | Government channels | Yes |

---

## 3. Technical Implementation Patterns

### Sequence/Consecutive Management Best Practices

#### 1. Multi-Document Type Tracking

**Requirements:**
- Each document type maintains its own independent sequence
- Must track last used number for ALL 9 document types
- Cannot mix sequences between document types

**Implementation Pattern:**
```python
# Pseudo-code for consecutive management
consecutive_sequences = {
    '01': {'last_used': 152, 'next': 153},  # Invoices
    '02': {'last_used': 8, 'next': 9},      # Debit Notes
    '03': {'last_used': 45, 'next': 46},    # Credit Notes
    '04': {'last_used': 2340, 'next': 2341}, # Tickets
    '05': {'last_used': 120, 'next': 121},  # Purchase Acceptance
    '06': {'last_used': 5, 'next': 6},      # Partial Acceptance
    '07': {'last_used': 2, 'next': 3},      # Purchase Rejection
    '08': {'last_used': 30, 'next': 31},    # Purchase Invoice
    '09': {'last_used': 0, 'next': 1}       # Export Invoice
}
```

#### 2. Multi-Branch/Terminal Management

**Structure:**
- Each establishment (branch) has unique 3-digit code
- Each terminal within establishment has unique 5-digit code
- Sequences are independent per terminal per document type

**Example:**
```
Headquarters (001) - POS 1 (00001) - Invoices (01): at 00000000523
Headquarters (001) - POS 2 (00002) - Invoices (01): at 00000000089
Branch 1 (002) - POS 1 (00001) - Invoices (01): at 00000000012
```

**Implementation Consideration:**
- Odoo should support multiple journals/sequences per location
- Each journal represents a terminal/POS combination
- UI should clearly show which sequence applies to which location

#### 3. Collision Prevention

**Critical Rules:**
- Never reuse a consecutive number, even if invoice was rejected
- Rejected invoices "burn" that consecutive number forever
- Must implement gap-less sequence with no manual override

**Database Design:**
```sql
-- Recommended approach: Use database sequences with no gaps
CREATE SEQUENCE cr_invoice_seq_001_00001_01
    START WITH 154
    INCREMENT BY 1
    NO CYCLE
    NO CACHE;

-- Track burned/rejected numbers for audit trail
CREATE TABLE cr_consecutive_audit (
    consecutive_number INTEGER,
    establishment_code CHAR(3),
    terminal_code CHAR(5),
    document_type CHAR(2),
    status VARCHAR(20),  -- 'used', 'rejected', 'cancelled'
    invoice_id INTEGER,
    timestamp TIMESTAMP
);
```

### Invoice Number Migration Strategies

#### Strategy 1: Manual Configuration (FACTURATica Approach)

**Process:**
1. Customer provides last consecutive number for each document type
2. Admin configures system to start at next number
3. System locks configuration to prevent accidents

**Pros:**
- Simple and transparent
- Customer has full control
- Low technical complexity

**Cons:**
- Manual process requires support intervention
- Risk of human error in data entry
- No automated validation

**Best for:** Small to medium migrations with limited document types

#### Strategy 2: Automated Import from CSV/Excel

**Process:**
1. Customer exports report from old system showing:
   - Document type
   - Last invoice number
   - Date issued
   - Optional: establishment and terminal codes
2. System parses file and configures sequences automatically
3. Validation step shows proposed configuration for approval

**Pros:**
- Faster for complex setups
- Reduces human error
- Auditable import record

**Cons:**
- Requires customer to have export capability
- File format must be standardized
- More complex error handling

**Best for:** Enterprises with multiple branches/terminals

#### Strategy 3: API Integration from Previous System

**Process:**
1. Connect to previous system's API
2. Query last consecutive number for each sequence
3. Automatically configure Odoo sequences
4. Verify with customer before going live

**Pros:**
- Fully automated
- Real-time accuracy
- Minimal customer effort

**Cons:**
- Requires API access to old system
- Not all providers offer APIs
- Higher development complexity

**Best for:** Migrations from well-known platforms with APIs

#### Strategy 4: Hybrid Approach (Recommended for Odoo)

**Process:**
1. **Detection Phase:**
   - System asks: "Are you migrating from another system?"
   - If YES → proceed to configuration
   - If NO → use default (start at 1)

2. **Configuration Phase:**
   - Provide CSV template for download
   - Customer fills in: document_type, last_consecutive, establishment, terminal
   - Upload CSV for parsing

3. **Validation Phase:**
   - Show parsed sequences in UI
   - Allow manual correction if needed
   - Confirm before activation

4. **Safety Phase:**
   - Lock sequences after first invoice issued
   - Provide "emergency unlock" for admins only
   - Log all sequence changes for audit

**Implementation in Odoo:**
```python
# Configuration wizard model
class CrEinvoiceOnboardingWizard(models.TransientModel):
    _name = 'cr.einvoice.onboarding.wizard'

    is_migration = fields.Boolean('Migrating from another system?')
    import_file = fields.Binary('Import Consecutive Numbers (CSV)')

    # Manual entry option
    sequence_line_ids = fields.One2many(
        'cr.einvoice.sequence.line',
        'wizard_id',
        'Consecutive Sequences'
    )

    def action_configure_sequences(self):
        # Parse CSV or use manual entries
        # Validate no duplicates
        # Configure ir.sequence for each document type
        # Lock after confirmation
        pass
```

### Data Import Requirements

#### Historical Invoices: Not Legally Required

**Findings:**
- No legal requirement to import historical invoices into new system
- Hacienda only validates NEW invoices submitted to RCE
- Old invoices remain valid in their original system

**When Historical Import Makes Sense:**
1. **Business Continuity:** Customer wants unified reporting across all periods
2. **Analytics:** Need historical data for trends and forecasting
3. **Dispute Resolution:** Easier to reference old invoices in same system
4. **Audit Preparation:** Centralized access to all invoice records

**Implementation Considerations:**
- Import as "archived" records (not submitted to Hacienda again)
- Preserve original XML and PDF
- Mark clearly as "imported" vs. "issued in this system"
- Do NOT count toward consecutive sequence

**FACTURATica Example:**
- Imported 100+ million invoices for customers
- Positions it as value-added service, not compliance requirement
- Likely charges for large-volume imports

### Dual-System Operation During Transition

#### Is It Allowed?

**No explicit prohibition found**, but practical constraints exist:

**Challenges:**
1. **Consecutive Number Management:** Must ensure sequences don't overlap
   - Old system continues from X to Y
   - New system starts at Y+1
   - Requires coordination

2. **Reporting:** Tax reporting must include invoices from BOTH systems

3. **Customer Confusion:** Invoices look different, different URLs for validation

4. **Support Burden:** Two systems to maintain during overlap

**Recommended Approach: Hard Cut-Over**

**Rationale:**
- Simpler consecutive number management
- Clearer for customers and tax authorities
- Lower risk of errors
- Costa Rica's 3-hour validation time allows same-day verification

**Cut-Over Process:**
1. **Preparation (1-2 weeks before):**
   - Configure Odoo with correct consecutive numbers
   - Train staff on new system
   - Test in sandbox environment
   - Prepare customer communication

2. **Cut-Over Day:**
   - Issue last invoice in old system at EOD
   - Record final consecutive numbers
   - Configure Odoo to start at next number
   - Test first invoice in Odoo
   - Verify Hacienda acceptance

3. **Post-Cut-Over (1 week after):**
   - Monitor all invoices for rejections
   - Provide extra support for staff
   - Document any issues and resolutions

### Cut-Over Strategies

#### Option A: Weekend Cut-Over (Recommended)

**Timeline:**
- Friday EOD: Last invoice in old system
- Saturday: Configure Odoo, run tests
- Sunday: Final verification
- Monday: Go live with Odoo

**Pros:**
- Minimal business disruption
- Time for testing
- Staff can be trained over weekend

**Cons:**
- Requires weekend work
- May need emergency support on Sunday

#### Option B: Month-End Cut-Over

**Timeline:**
- Last day of month: Final invoice in old system
- First day of new month: Start with Odoo

**Pros:**
- Clean accounting period break
- Easier for monthly reporting
- Aligns with financial close process

**Cons:**
- Month-end is often busiest time
- Less flexibility if issues arise

#### Option C: Slow Business Period

**Timeline:**
- Identify lowest-volume day/week
- Cut over during that period

**Pros:**
- Lower risk of errors affecting many customers
- More time to handle issues
- Less pressure on staff

**Cons:**
- May not align with other business needs
- Harder to predict for some businesses

---

## 4. Specific Technical Questions - ANSWERED

### Q1: Can you start with any invoice number or must it continue previous sequence?

**ANSWER:** Depends on scenario:

- **First-time e-invoicing (from paper):** YES, start at 00000000001
- **Migrating from another e-invoicing system:** NO, must continue from last number used
- **Adding new branch/terminal:** YES, new sequences can start at 00000000001
- **Reached maximum (9999999999):** YES, can restart at 00000000001

**Legal Basis:** Resolution DGT-R-033-2019 (now MH-DGT-RES-0027-2024)

**Quote:** "For those taxpayers already using electronic vouchers who decide to change emission platforms, they must maintain the consecutive numbering."

### Q2: Is there a "declaration" to Hacienda about starting numbers?

**ANSWER:** NO

- No form to submit
- No approval process required
- No waiting period
- No "resolución de autorización" needed

**What Hacienda DOES check:**
- Each invoice's consecutive number is validated in real-time
- System rejects duplicates automatically
- Gaps in sequence may trigger audit questions, but not automatic rejection

**Implicit Declaration:**
- The first invoice you submit with a consecutive number effectively declares your sequence
- Hacienda's system tracks your sequences from that point forward

### Q3: Do you need to import old invoices into new system?

**ANSWER:** NO, not legally required

**Legal Requirement:**
- Must retain XML files for 5 years
- Files must be "accessible and readable at all times"
- Can be stored in old system or archived separately

**Business Reasons to Import:**
- Unified reporting and analytics
- Easier dispute resolution
- Customer convenience (single portal for all invoices)
- Audit preparation

**Implementation Notes:**
- If you DO import, mark as historical/archived
- Do NOT resubmit to Hacienda
- Do NOT count toward consecutive sequences
- Preserve original XML and PDF exactly

### Q4: Can you run both systems in parallel during transition?

**ANSWER:** Technically possible, but NOT recommended

**No Legal Prohibition:**
- No rule against using multiple systems simultaneously
- Each system just needs to use different consecutive ranges

**Practical Problems:**
1. **Sequence Coordination:** Must manually prevent overlap
   - Old system: use 001-00001-01-0000000150 to 0000000200
   - New system: starts at 001-00001-01-0000000201
   - HIGH RISK of human error

2. **Staff Confusion:** Which system to use when?

3. **Customer Confusion:** Invoices look different

4. **Audit Complexity:** Must explain dual-system setup to tax authority

5. **No Benefit:** 3-hour Hacienda validation is fast enough for hard cut-over

**Recommendation:** Hard cut-over on low-volume day (weekend or slow period)

### Q5: What happens to invoices issued during migration period?

**ANSWER:** Depends on cut-over strategy

**Hard Cut-Over (Recommended):**
- Last invoice in old system at time X
- First invoice in new system at time X + setup time
- Gap is typically hours, not days
- All invoices before X: old system
- All invoices after X: new system

**Parallel Operation (Not Recommended):**
- Define rules for which system to use
- Risk of sequence collision
- Must track carefully

**If Migration Fails Mid-Process:**
- Continue using old system
- New system hasn't issued any invoices yet (no Hacienda record)
- No cleanup needed in Hacienda
- Just delay cut-over to next date

**Failed Invoice After Cut-Over:**
- If first invoice in Odoo is rejected by Hacienda
- That consecutive number is "burned"
- Fix issue and issue with NEXT consecutive number
- Same as normal operations

---

## 5. Legal/Compliance Requirements

### Primary Resolutions and Regulations

#### Resolution MH-DGT-RES-0027-2024

**Status:** Current regulation (effective November 19, 2024)
**Replaces:** DGT-R-033-2019

**Key Provisions:**
- Establishes version 4.4 as mandatory standard
- Defines 146 technical changes from v4.3
- Introduces system provider identification field
- Sets September 1, 2025 as compliance deadline
- Six-month implementation period (Dec 2024 - June 2025, extended to Sept 2025)

**Relevance to Migration:**
- Any new system MUST support version 4.4
- No option to launch with v4.3 anymore
- System provider field must identify software vendor

#### Resolution DGT-R-033-2019 (Superseded)

**Historical Importance:**
- Established consecutive numbering rules still in effect
- Defined 20-digit structure
- Set validation requirements
- Created framework for automatic rejection

**Still Relevant:**
- Core consecutive number principles unchanged
- Migration continuity requirement persists
- Validation process remains same

### Resolución DGT sobre Consecutivos - Key Findings

**Consecutive Numbering Security:**
- "The electronic voucher issuance system must automatically assign consecutive numbering with security measures guaranteeing unalterability, legitimacy, and integrity of the consecutive."
- Manual modification must be prevented once sequence is active
- Gap-less sequence required (no skipping numbers)

**Migration Provision:**
- "For those taxpayers already using electronic vouchers who decide to change emission platforms, they must maintain the consecutive numbering."
- Clear and unambiguous
- No exceptions noted

**Maximum and Reset:**
- "Once the maximum consecutive number is reached, it is possible to restart from No. 1"
- 10 billion invoices before reset allowed
- No approval needed for reset

### Notification Requirements to Hacienda

**CRITICAL FINDING: No notification required for system changes**

**What IS Required:**
1. **Initial Registration:**
   - Register as "Emisor-Receptor Electrónico" in RUT (Registro Único Tributario)
   - Done through ATV (now migrated to OVI/TRIBU-CR)
   - One-time registration per taxpayer

2. **Digital Certificate:**
   - Obtain from Banco Central de Costa Rica
   - Must be valid and not expired
   - Used to digitally sign all invoices

3. **System Provider Field (v4.4):**
   - XML must include identifier of software generating invoice
   - This is IN the invoice, not a separate registration
   - Hacienda collects this data automatically from invoices

**What is NOT Required:**
- No form to submit when changing providers
- No approval process
- No waiting period
- No "resolución" to request
- No fee to pay

**Implication for Odoo Module:**
- No integration needed for system registration
- No API call to "register" software with Hacienda
- Just need to populate system provider field in XML correctly

### Record Keeping During Migration

**Legal Requirements:**

1. **5-Year Retention:**
   - All XML files must be kept for 5 years from issuance date
   - Must be in original format (XML, not just PDF)
   - Must be "accessible and readable at all times"

2. **Storage Location:**
   - Can be in issuing system
   - Can be in separate archive
   - Can be with third-party provider
   - Multiple locations allowed (redundancy recommended)

3. **During Migration:**
   - Old system's invoices remain valid in old system
   - No requirement to move them
   - If you DO move them, preserve originals

**Best Practices:**

1. **Before Migration:**
   - Export all XML files from old system
   - Backup to multiple locations
   - Verify file integrity (check XML can be opened/parsed)
   - Document export date and count

2. **After Migration:**
   - Keep old system accessible (read-only) for at least audit period
   - Or import historical data to Odoo
   - Maintain mapping of old invoice IDs to files

3. **Audit Trail:**
   - Document migration date
   - Record last consecutive numbers from old system
   - Log first invoice issued in new system
   - Keep evidence of Hacienda acceptance for first new invoice

### Audit Trail Requirements

**What Hacienda Expects:**

1. **Sequential Integrity:**
   - Consecutive numbers with no gaps (except rejected invoices)
   - Each document type maintains its own sequence
   - Temporal correlation (later invoices have higher numbers)

2. **System Logs:**
   - No specific format required
   - But must be able to explain sequence changes
   - Should document system changes, if asked

3. **During Audit:**
   - May be asked to explain gap in sequence (e.g., burned numbers from rejections)
   - May be asked to provide invoice from specific consecutive number
   - May be asked about system change date

**Migration-Specific:**
- Document WHY consecutive numbers jumped (system change)
- Keep evidence of last invoice from old system
- Keep evidence of first invoice from new system
- Have timeline of migration activities

**Odoo Implementation:**
```python
# Audit log for consecutive number changes
class CrEinvoiceSequenceAudit(models.Model):
    _name = 'cr.einvoice.sequence.audit'
    _description = 'Costa Rica E-Invoice Sequence Audit Log'
    _order = 'timestamp desc'

    timestamp = fields.Datetime('Timestamp', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', 'User')
    action = fields.Selection([
        ('configured', 'Initial Configuration'),
        ('migration', 'Migration from Another System'),
        ('reset', 'Sequence Reset (Max Reached)'),
        ('burned', 'Number Burned (Rejection)'),
        ('emergency_unlock', 'Emergency Admin Unlock')
    ], 'Action')
    establishment_code = fields.Char('Establishment', size=3)
    terminal_code = fields.Char('Terminal', size=5)
    document_type = fields.Selection([...], 'Document Type')
    old_value = fields.Integer('Previous Consecutive')
    new_value = fields.Integer('New Consecutive')
    reason = fields.Text('Reason / Notes')
    invoice_id = fields.Many2one('account.move', 'Related Invoice')
```

### Compliance Risks During Migration

#### High-Risk Issues

1. **Duplicate Consecutive Numbers**
   - **Risk:** Reusing a number from old system
   - **Cause:** Incorrect configuration, data entry error
   - **Result:** Automatic rejection by Hacienda, customer cannot receive invoice
   - **Mitigation:**
     - Double-check last consecutive from old system
     - Test first invoice in sandbox
     - Monitor first 10 invoices closely

2. **Sequence Gaps**
   - **Risk:** Large unexplained gaps in consecutive numbers
   - **Cause:** Misunderstanding migration process, attempting to "skip" numbers
   - **Result:** May trigger audit inquiry (not automatic rejection)
   - **Mitigation:**
     - Document system change in internal records
     - If asked, explain migration and provide evidence

3. **Wrong Document Type Sequence**
   - **Risk:** Configuring invoice sequence (01) when customer meant ticket sequence (04)
   - **Cause:** Confusion about document types, unclear customer data
   - **Result:** First invoice uses wrong number, burns a consecutive in wrong sequence
   - **Mitigation:**
     - Clear UI showing document type for each sequence
     - Validation step before activation
     - Ask customer to verify sample invoice before going live

#### Medium-Risk Issues

4. **Version Mismatch**
   - **Risk:** Generating v4.3 invoices when v4.4 is required
   - **Cause:** Old code, not updated to v4.4 specs
   - **Result:** Automatic rejection since September 1, 2025
   - **Mitigation:**
     - Ensure Odoo module is v4.4 compliant
     - Test with Hacienda sandbox
     - Verify acceptance of first production invoice

5. **System Provider Field Missing/Wrong**
   - **Risk:** Not including system provider identifier in v4.4 XML
   - **Cause:** Forgetting new v4.4 field requirement
   - **Result:** Invoice rejection
   - **Mitigation:**
     - Hard-code system provider identifier for Odoo module
     - Include in all v4.4 XML generation
     - Test in sandbox

6. **Digital Certificate Issues**
   - **Risk:** Expired certificate, wrong certificate, certificate not recognized
   - **Cause:** Customer didn't provide updated cert, admin error
   - **Result:** Invoice rejection
   - **Mitigation:**
     - Verify certificate validity before migration
     - Test certificate in sandbox
     - Provide clear instructions for certificate upload

#### Low-Risk Issues

7. **Historical Data Import Errors**
   - **Risk:** Imported invoices have data issues
   - **Cause:** File format problems, encoding issues
   - **Result:** Reporting inaccuracies, but no Hacienda compliance issue
   - **Mitigation:**
     - Validate import before showing to customer
     - Mark imported data clearly
     - Allow customer to verify before finalizing

8. **PDF Formatting Differences**
   - **Risk:** Invoice PDF looks different from old system
   - **Cause:** Different template, styling
   - **Result:** Customer complaints, confusion (not compliance issue)
   - **Mitigation:**
     - Show sample PDF before go-live
     - Allow customization of template
     - Communicate changes to end customers

---

## 6. Implementation Guide for Odoo Module

### Step-by-Step Migration Process

#### Phase 1: Pre-Migration Assessment (1-2 weeks before go-live)

**Objectives:**
- Understand customer's current state
- Gather necessary configuration data
- Identify potential issues

**Tasks:**

1. **Customer Interview:**
   - Are you currently using e-invoicing? (If NO → skip to Phase 2 - New User Setup)
   - Which provider are you using? (GDI, TicoPay, TicoFactura, other)
   - How many branches/establishments do you have?
   - How many POS terminals per establishment?
   - Which document types do you currently use?

2. **Data Collection:**
   - Request last consecutive number for EACH combination of:
     - Establishment code (001, 002, etc.)
     - Terminal code (00001, 00002, etc.)
     - Document type (01-09)
   - Provide template CSV for customer to complete:

   ```csv
   establishment_code,terminal_code,document_type,last_consecutive_used,last_invoice_date
   001,00001,01,0000000523,2025-12-28
   001,00001,03,0000000045,2025-12-15
   001,00001,04,0000002340,2025-12-28
   002,00001,01,0000000012,2025-12-20
   ```

3. **System Access Verification:**
   - Verify customer has active ATV/OVI account
   - Verify digital certificate is valid (not expired)
   - Verify certificate is uploaded to Odoo
   - Test certificate with Hacienda sandbox

4. **Communication Plan:**
   - Draft email to customer's clients about system change
   - Prepare internal staff training materials
   - Schedule go-live date (recommend weekend or low-volume day)

**Deliverables:**
- Completed migration configuration CSV
- Verified digital certificate
- Communication materials
- Go-live date scheduled

#### Phase 2A: New User Setup (First-Time E-Invoicing)

**For customers transitioning from paper invoicing**

**Tasks:**

1. **ATV/OVI Registration:**
   - Guide customer to https://ovitribucr.hacienda.go.cr/home/
   - Register as "Emisor-Receptor Electrónico"
   - Obtain cryptographic key from Banco Central

2. **Odoo Configuration:**
   - Set establishment code (001 for headquarters)
   - Set terminal code (00001 for first POS)
   - Configure sequences to start at 00000000001 for each document type
   - Set invoice journal to use CR e-invoice format

3. **Testing:**
   - Issue test invoice in Hacienda sandbox
   - Verify XML structure
   - Verify consecutive number format
   - Verify digital signature

4. **Go-Live:**
   - Issue first production invoice
   - Verify Hacienda acceptance within 3 hours
   - Monitor first 10 invoices closely

**Deliverables:**
- Registered emisor-receptor status
- Valid digital certificate
- Configured Odoo sequences
- Successful sandbox test
- First production invoice accepted

#### Phase 2B: Migration Configuration (Switching from Another System)

**For customers already using e-invoicing**

**Tasks:**

1. **Import Consecutive Numbers:**
   - Load customer's CSV into configuration wizard
   - Parse and validate data:
     - Check format (3-digit establishment, 5-digit terminal, 2-digit doc type)
     - Check no duplicates
     - Check all required document types included

2. **Configure Odoo Sequences:**
   ```python
   def configure_migration_sequences(self):
       for line in self.sequence_line_ids:
           sequence_name = f"CR E-Invoice {line.establishment_code}-{line.terminal_code}-{line.document_type}"

           # Create or update ir.sequence
           sequence = self.env['ir.sequence'].search([
               ('name', '=', sequence_name),
               ('company_id', '=', self.company_id.id)
           ])

           if not sequence:
               sequence = self.env['ir.sequence'].create({
                   'name': sequence_name,
                   'implementation': 'no_gap',
                   'padding': 10,
                   'number_increment': 1,
                   'company_id': self.company_id.id
               })

           # Set to start at NEXT number after customer's last
           next_number = int(line.last_consecutive_used) + 1
           sequence.number_next_actual = next_number

           # Lock sequence (prevent manual changes)
           sequence.write({'locked': True})

           # Create audit log
           self.env['cr.einvoice.sequence.audit'].create({
               'action': 'migration',
               'establishment_code': line.establishment_code,
               'terminal_code': line.terminal_code,
               'document_type': line.document_type,
               'old_value': int(line.last_consecutive_used),
               'new_value': next_number,
               'reason': f'Migration from {self.old_system_name}',
               'user_id': self.env.uid
           })
   ```

3. **Validation Interface:**
   - Show customer proposed configuration in Odoo UI:

   ```
   Review Your Consecutive Number Configuration

   Establishment 001 - Terminal 00001:
     Invoices (01): Will continue from 0000000524 (last used: 0000000523)
     Credit Notes (03): Will continue from 0000000046 (last used: 0000000045)
     Tickets (04): Will continue from 0000002341 (last used: 0000002340)

   Establishment 002 - Terminal 00001:
     Invoices (01): Will continue from 0000000013 (last used: 0000000012)

   [Edit] [Confirm Configuration]
   ```

4. **Final Verification:**
   - Customer confirms configuration is correct
   - Admin locks configuration (prevent accidental changes)
   - System generates confirmation report (PDF for customer's records)

**Deliverables:**
- Configured sequences matching old system
- Locked configuration (tamper-proof)
- Confirmation report for customer
- Audit log entries

#### Phase 3: Testing and Validation

**Tasks:**

1. **Sandbox Testing:**
   - Configure Odoo to use Hacienda sandbox API
   - Issue test invoice for EACH establishment/terminal/document type combination
   - Verify consecutive numbers are correct
   - Verify XML structure is valid
   - Verify digital signature is accepted
   - Verify Hacienda response is "accepted"

2. **Staff Training:**
   - Train customer's accounting staff on Odoo UI
   - Train on how to issue each document type
   - Train on how to handle rejections
   - Train on how to view Hacienda acceptance status
   - Provide quick reference guide

3. **Customer Communication:**
   - Send email to customer's clients (if invoicing B2C):

   ```
   Subject: Important: We're upgrading our invoicing system

   Dear [Customer],

   Starting [Date], we'll be using a new electronic invoicing system to serve you better.

   What this means for you:
   - Invoices will look slightly different
   - You'll still receive them by email as usual
   - The validation process with Hacienda remains the same
   - Your invoice history remains accessible

   If you have any questions, please contact us at [Contact].
   ```

4. **Contingency Planning:**
   - Keep old system accessible (read-only) for at least 1 week
   - Have old system admin on standby for emergency rollback
   - Document rollback procedure (hopefully never needed):
     - If Odoo fails to generate valid invoices
     - Return to old system temporarily
     - No Hacienda notification needed (no damage done)
     - Fix Odoo issues
     - Reschedule go-live

**Deliverables:**
- Successful sandbox tests for all sequences
- Trained staff (sign-off on training)
- Customer communication sent
- Contingency plan documented

#### Phase 4: Go-Live

**Recommended Timeline: Weekend or Low-Volume Day**

**Friday (Last day with old system):**
- 8:00 AM: Reminder to staff: today is last day with old system
- Throughout day: Business as usual
- 5:00 PM: Issue last invoice in old system
- 5:30 PM: Record final consecutive numbers from old system
- 6:00 PM: Verify recorded numbers match configuration from Phase 2B
- 6:30 PM: Mark old system as "read-only" (prevent accidental use)

**Saturday (Configuration day):**
- 9:00 AM: Admin logs into Odoo
- 9:30 AM: Final verification of consecutive number configuration
- 10:00 AM: Switch Odoo from sandbox to production Hacienda API
- 10:30 AM: Issue test invoice to friendly customer (or internal)
- 11:00 AM: Monitor Hacienda acceptance (3-hour window)
- 2:00 PM: Test invoice accepted → Ready for Monday
- 2:00 PM: Test invoice rejected → Debug and fix, retest

**Sunday (Verification day):**
- Relaxed monitoring
- Admin on standby for issues
- Review Saturday's test invoice
- Prepare for Monday launch

**Monday (First production day):**
- 8:00 AM: Staff briefing: "Today we go live with Odoo"
- 8:30 AM: First real customer invoice issued
- 9:00 AM: Monitor Hacienda acceptance closely
- 11:30 AM: First invoice accepted → Success!
- Throughout day: Monitor all invoices
- 5:00 PM: End-of-day review: how many invoices, any rejections, any issues?

**Deliverables:**
- Last invoice from old system documented
- First invoice from Odoo accepted by Hacienda
- Staff successfully issuing invoices
- No customer complaints
- Documentation of cut-over completed

#### Phase 5: Post-Migration Monitoring (1-2 weeks)

**Tasks:**

1. **Daily Monitoring:**
   - Check rejection rate (should be <1%)
   - Review any rejections and identify patterns
   - Verify consecutive numbers are incrementing correctly
   - Monitor customer feedback

2. **Issue Resolution:**
   - Common issues to watch for:
     - Certificate expiration
     - Network connectivity to Hacienda
     - User errors (wrong customer data)
     - CAByS code errors
   - Document each issue and resolution
   - Update training materials if needed

3. **Performance Tuning:**
   - Measure invoice generation time
   - Measure Hacienda API response time
   - Optimize if needed

4. **Customer Check-In:**
   - Schedule call or meeting with customer 1 week after go-live
   - Ask: "How is it going? Any issues?"
   - Collect feedback
   - Provide additional training if needed

5. **Final Report:**
   - Document migration success metrics:
     - Total invoices issued
     - Rejection rate
     - Issues encountered and resolved
     - Customer satisfaction
   - Archive migration configuration for future reference
   - Update Odoo documentation with lessons learned

**Deliverables:**
- Stable production system
- Low rejection rate
- Satisfied customer
- Migration post-mortem report
- Updated documentation

### Migration Checklist (Printable)

```
[ ] ASSESSMENT
    [ ] Customer interview completed
    [ ] Current system identified
    [ ] Consecutive numbers collected (CSV)
    [ ] Digital certificate obtained and verified
    [ ] Go-live date scheduled

[ ] CONFIGURATION
    [ ] Consecutive numbers imported to Odoo
    [ ] Sequences configured correctly
    [ ] Customer reviewed and approved configuration
    [ ] Configuration locked
    [ ] Audit logs created

[ ] TESTING
    [ ] Sandbox API configured
    [ ] Test invoices issued for all document types
    [ ] All tests accepted by Hacienda sandbox
    [ ] Staff trained on new system
    [ ] Customer communication sent

[ ] GO-LIVE
    [ ] Last invoice issued in old system
    [ ] Final consecutive numbers recorded
    [ ] Old system set to read-only
    [ ] Odoo switched to production API
    [ ] First test invoice issued and accepted
    [ ] Staff ready for Monday

[ ] MONITORING
    [ ] Daily rejection rate review
    [ ] Issues documented and resolved
    [ ] Customer feedback collected
    [ ] Final migration report completed

[ ] DOCUMENTATION
    [ ] Migration date recorded
    [ ] Old system consecutive numbers archived
    [ ] First Odoo invoice details saved
    [ ] Lessons learned documented
```

---

## 7. Compliance Checklist

### Pre-Migration

```
[ ] Legal Requirements
    [ ] Company registered as Emisor-Receptor in RUT (ATV/OVI)
    [ ] Digital certificate obtained from Banco Central de Costa Rica
    [ ] Certificate is valid (not expired)
    [ ] Certificate uploaded to Odoo
    [ ] Establishment codes assigned (001 for headquarters, 002+ for branches)
    [ ] Terminal codes assigned (00001, 00002, etc.)

[ ] System Requirements
    [ ] Odoo module is version 4.4 compliant
    [ ] System provider identifier configured in XML generation
    [ ] CAByS 2025 catalog integrated
    [ ] Payment methods include SINPE Móvil (v4.4 requirement)
    [ ] Electronic Payment Receipt (REP) document type supported (v4.4)

[ ] Data Requirements
    [ ] Consecutive numbers from old system documented (if migrating)
    [ ] Each document type's last number recorded
    [ ] Each establishment/terminal combination recorded
    [ ] Historical XML files backed up (5-year retention requirement)

[ ] Access Requirements
    [ ] Admin access to old system (for reference)
    [ ] Admin access to Odoo
    [ ] Access to Hacienda sandbox for testing
    [ ] Access to Hacienda production RCE API
```

### During Migration

```
[ ] Configuration Compliance
    [ ] Consecutive numbers continue from old system (no reset to 1)
    [ ] No gaps in consecutive sequences (except documented burned numbers)
    [ ] Each document type has independent sequence
    [ ] Sequences use 20-digit format: AAA-BBBBB-CC-DDDDDDDDDD
    [ ] Sequences locked after configuration (prevent tampering)

[ ] Testing Compliance
    [ ] All document types tested in sandbox
    [ ] Digital signature verified
    [ ] Hacienda sandbox accepted all test invoices
    [ ] XML structure validated against v4.4 schema
    [ ] System provider field populated correctly

[ ] Audit Trail Compliance
    [ ] Migration date documented
    [ ] Last consecutive from old system recorded
    [ ] First consecutive from Odoo recorded
    [ ] Reason for sequence change logged
    [ ] Admin approval logged
```

### Post-Migration

```
[ ] Operational Compliance
    [ ] All invoices digitally signed with valid certificate
    [ ] All invoices include system provider identifier (v4.4)
    [ ] All invoices submitted to Hacienda RCE within required timeframe
    [ ] Acceptance messages from Hacienda received and stored
    [ ] Rejected invoices logged with reason
    [ ] Consecutive numbers incrementing correctly (no duplicates)

[ ] Storage Compliance
    [ ] XML files stored in original format
    [ ] XML files accessible and readable
    [ ] PDF files generated and stored
    [ ] Acceptance messages from Hacienda stored
    [ ] Storage solution ensures 5-year retention

[ ] Monitoring Compliance
    [ ] Daily check for rejections
    [ ] Weekly audit of consecutive sequences (no gaps)
    [ ] Monthly review of certificate expiration date
    [ ] Quarterly backup verification (can restore XML files)

[ ] Documentation Compliance
    [ ] Migration documentation filed
    [ ] Sequence configuration documented
    [ ] Staff training records maintained
    [ ] Issue log maintained
    [ ] Ready for tax audit (can explain system change)
```

---

## 8. Risk Assessment

### Critical Risks (Must Be Avoided)

| Risk | Probability | Impact | Mitigation | Contingency |
|------|------------|--------|------------|-------------|
| **Duplicate Consecutive Numbers** | Medium | Critical | Double-check config, test in sandbox, lock sequences after config | If happens: number is burned, use next number, document in audit log |
| **Invalid Digital Certificate** | Low | Critical | Verify before go-live, test in sandbox, monitor expiration | Keep backup certificate ready, process to renew before expiration |
| **Version 4.3 Instead of 4.4** | Low | Critical | Code review, sandbox testing, verify system provider field | If happens: update code, reissue invoices with correct version |
| **Wrong Establishment/Terminal Code** | Low | High | Clear UI labels, customer verification step | Difficult to fix - would need to restart sequence with correct code |

### High Risks (Significant Disruption)

| Risk | Probability | Impact | Mitigation | Contingency |
|------|------------|--------|------------|-------------|
| **Hacienda API Downtime During Go-Live** | Low | High | Schedule go-live during off-peak hours, have old system ready | Delay go-live to next day, continue with old system temporarily |
| **Staff Training Insufficient** | Medium | High | Thorough training, practice sessions, quick reference guide | On-call support during first week, admin can issue invoices if needed |
| **Network Connectivity Issues** | Low | High | Test connectivity, have backup internet, monitor uptime | Use mobile hotspot, delay invoices until connectivity restored |
| **Missing CAByS Codes** | Medium | High | Validate product catalog before go-live, provide training on CAByS lookup | Have CAByS reference guide, assign default codes for common products |

### Medium Risks (Manageable Disruption)

| Risk | Probability | Impact | Mitigation | Contingency |
|------|------------|--------|------------|-------------|
| **Customer Confusion** | High | Medium | Clear communication, sample invoices, FAQ | Customer support ready to explain, provide validation link |
| **Rejected Invoices (User Error)** | Medium | Medium | Training, validation before submission, clear error messages | Support helps fix error, reissue with next consecutive |
| **Performance Issues** | Low | Medium | Load testing, optimize database queries, monitor response times | Scale server resources, optimize code |
| **Historical Data Import Errors** | Medium | Low | Validate import, allow preview, mark as historical | Fix import errors, re-import if needed (no Hacienda impact) |

### Low Risks (Minor Inconvenience)

| Risk | Probability | Impact | Mitigation | Contingency |
|------|------------|--------|------------|-------------|
| **PDF Formatting Issues** | High | Low | Provide template customization, show samples before go-live | Adjust template, regenerate PDF (XML unchanged) |
| **Timezone Issues** | Low | Low | Verify server timezone matches Costa Rica, test timestamp format | Adjust timezone config, verify future invoices correct |
| **Language/Translation Issues** | Low | Low | Provide Spanish UI, translate error messages | Update translations, provide glossary |

### Risk Mitigation Strategy Summary

**Before Migration:**
1. Comprehensive testing in sandbox
2. Thorough staff training
3. Customer communication
4. Documentation of contingency plans

**During Migration:**
5. Close monitoring of first invoices
6. Admin on standby for issues
7. Old system kept accessible (read-only)
8. Clear go/no-go criteria

**After Migration:**
9. Daily monitoring for first week
10. Weekly check-ins with customer
11. Issue log to track patterns
12. Continuous improvement based on feedback

---

## 9. Recommendations for Odoo Module Enhancement

### Priority 1: Migration Wizard (Must Have)

**Feature:** Guided onboarding wizard that detects migration vs. new user

**Implementation:**
```python
class CrEinvoiceOnboardingWizard(models.TransientModel):
    _name = 'cr.einvoice.onboarding.wizard'
    _description = 'Costa Rica E-Invoice Onboarding Wizard'

    # Step 1: Detect scenario
    scenario = fields.Selection([
        ('new', 'First-time e-invoicing (from paper invoices)'),
        ('migration', 'Migrating from another e-invoicing system'),
        ('additional', 'Adding a new branch or terminal')
    ], 'Scenario', required=True)

    # For migration scenario
    old_system_name = fields.Char('Previous E-Invoicing System')
    import_file = fields.Binary('Import Consecutive Numbers (CSV Template)')
    import_filename = fields.Char('Filename')

    # Manual entry option
    sequence_line_ids = fields.One2many(
        'cr.einvoice.sequence.config.line',
        'wizard_id',
        'Consecutive Sequences'
    )

    # Step 2: Configuration
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
    establishment_code = fields.Char('Establishment Code', size=3, default='001')
    terminal_code = fields.Char('Terminal Code', size=5, default='00001')

    # Step 3: Validation
    state = fields.Selection([
        ('scenario', 'Select Scenario'),
        ('config', 'Configure Sequences'),
        ('validate', 'Review and Validate'),
        ('done', 'Configuration Complete')
    ], 'State', default='scenario')

    def action_next_step(self):
        if self.state == 'scenario':
            if self.scenario == 'migration':
                self.state = 'config'
            else:
                # Auto-configure for new users
                self._configure_new_user_sequences()
                self.state = 'done'
        elif self.state == 'config':
            self._parse_import_file()
            self.state = 'validate'
        elif self.state == 'validate':
            self._apply_configuration()
            self.state = 'done'

    def _configure_new_user_sequences(self):
        # Create sequences starting at 1 for all document types
        for doc_type in ['01', '02', '03', '04', '05', '06', '07', '08', '09']:
            self._create_sequence(
                self.establishment_code,
                self.terminal_code,
                doc_type,
                1  # Start at 1
            )

    def _parse_import_file(self):
        # Parse CSV and populate sequence_line_ids
        # Validate format and values
        pass

    def _apply_configuration(self):
        for line in self.sequence_line_ids:
            next_number = int(line.last_consecutive_used) + 1
            self._create_sequence(
                line.establishment_code,
                line.terminal_code,
                line.document_type,
                next_number
            )
            # Create audit log entry
            self._log_sequence_config(line, next_number)

    def _create_sequence(self, establishment, terminal, doc_type, start_number):
        # Create ir.sequence with proper configuration
        pass

    def _log_sequence_config(self, line, next_number):
        # Create audit log entry
        pass
```

**UI/UX:**
- Step-by-step wizard with clear instructions
- CSV template download button
- Preview/validation screen before applying
- Success confirmation with summary report

**Benefits:**
- Reduces configuration errors
- Guides user through complex process
- Creates audit trail automatically
- Provides professional onboarding experience

### Priority 2: Consecutive Number Locking (Must Have)

**Feature:** Prevent accidental modification of consecutive sequences after first invoice

**Implementation:**
```python
# Extend ir.sequence model
class IrSequenceCR(models.Model):
    _inherit = 'ir.sequence'

    cr_einvoice_locked = fields.Boolean(
        'CR E-Invoice Locked',
        help='Locked sequences cannot be manually modified to ensure consecutive number integrity'
    )
    cr_last_invoice_id = fields.Many2one(
        'account.move',
        'Last Invoice Issued',
        help='Reference to last invoice using this sequence'
    )

    def write(self, vals):
        for seq in self:
            if seq.cr_einvoice_locked:
                # Only allow system to increment, not admin to change manually
                if not self.env.context.get('cr_einvoice_system_increment'):
                    if any(key in vals for key in ['number_next', 'number_next_actual', 'padding']):
                        raise UserError(
                            _('This sequence is locked for Costa Rica e-invoicing compliance. '
                              'Contact administrator if you need to unlock it.')
                        )
        return super().write(vals)

    def _emergency_unlock(self):
        # Admin-only method
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Only system administrators can unlock sequences'))

        # Create audit log
        self.env['cr.einvoice.sequence.audit'].create({
            'action': 'emergency_unlock',
            'sequence_id': self.id,
            'user_id': self.env.uid,
            'reason': 'Admin emergency unlock',
            'timestamp': fields.Datetime.now()
        })

        self.cr_einvoice_locked = False
```

**UI/UX:**
- Clear visual indicator when sequence is locked
- "Emergency Unlock" button only visible to system admins
- Warning message before unlocking
- Auto-lock after first invoice

**Benefits:**
- Prevents accidental sequence changes
- Ensures compliance with Hacienda requirements
- Reduces support burden (fewer user errors)

### Priority 3: Migration Audit Log (Must Have)

**Feature:** Complete audit trail of all consecutive number changes

**Implementation:**
```python
class CrEinvoiceSequenceAudit(models.Model):
    _name = 'cr.einvoice.sequence.audit'
    _description = 'Costa Rica E-Invoice Sequence Audit Log'
    _order = 'timestamp desc'

    timestamp = fields.Datetime('Timestamp', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.uid)
    sequence_id = fields.Many2one('ir.sequence', 'Sequence')
    action = fields.Selection([
        ('configured', 'Initial Configuration'),
        ('migration', 'Migration from Another System'),
        ('reset', 'Sequence Reset (Max Reached)'),
        ('burned', 'Number Burned (Rejection)'),
        ('emergency_unlock', 'Emergency Admin Unlock'),
        ('relock', 'Sequence Re-Locked')
    ], 'Action', required=True)

    establishment_code = fields.Char('Establishment', size=3)
    terminal_code = fields.Char('Terminal', size=5)
    document_type = fields.Selection([
        ('01', 'Invoice'),
        ('02', 'Debit Note'),
        ('03', 'Credit Note'),
        ('04', 'Ticket'),
        ('05', 'Purchase Acceptance'),
        ('06', 'Partial Purchase Acceptance'),
        ('07', 'Purchase Rejection'),
        ('08', 'Electronic Purchase Invoice'),
        ('09', 'Export Electronic Invoice')
    ], 'Document Type')

    old_value = fields.Integer('Previous Consecutive')
    new_value = fields.Integer('New Consecutive')
    reason = fields.Text('Reason / Notes', required=True)
    invoice_id = fields.Many2one('account.move', 'Related Invoice')

    # For migration tracking
    old_system_name = fields.Char('Previous System')
    migration_date = fields.Date('Migration Date')
```

**UI/UX:**
- Filterable, searchable log view
- Export to PDF for audit purposes
- Automatic entries (no manual creation)
- Timeline view showing sequence history

**Benefits:**
- Complete audit trail for tax authorities
- Easy to explain sequence changes during audit
- Troubleshooting tool (identify when issue occurred)
- Compliance documentation

### Priority 4: Historical Data Import Tool (Nice to Have)

**Feature:** Import historical invoices from previous system for reporting continuity

**Implementation:**
```python
class CrEinvoiceHistoricalImport(models.TransientModel):
    _name = 'cr.einvoice.historical.import'
    _description = 'Import Historical E-Invoices'

    import_file = fields.Binary('Import File (CSV or ZIP of XMLs)', required=True)
    import_filename = fields.Char('Filename')
    import_type = fields.Selection([
        ('csv', 'CSV Summary (invoice metadata only)'),
        ('xml', 'ZIP of XML Files (full invoice data)')
    ], 'Import Type', required=True)

    # Validation options
    validate_xml = fields.Boolean('Validate XML Structure', default=True)
    preserve_original = fields.Boolean('Store Original XML Files', default=True,
        help='Store original XML files for compliance (5-year retention requirement)')

    # Import summary
    state = fields.Selection([
        ('draft', 'Ready to Import'),
        ('validating', 'Validating Files'),
        ('importing', 'Importing'),
        ('done', 'Import Complete'),
        ('error', 'Error Occurred')
    ], 'State', default='draft')

    total_records = fields.Integer('Total Records', readonly=True)
    imported_records = fields.Integer('Imported Records', readonly=True)
    error_records = fields.Integer('Failed Records', readonly=True)
    error_log = fields.Text('Error Log', readonly=True)

    def action_import(self):
        self.state = 'validating'

        if self.import_type == 'csv':
            invoices = self._parse_csv()
        else:
            invoices = self._parse_xml_zip()

        self.total_records = len(invoices)

        self.state = 'importing'
        imported = 0
        errors = []

        for invoice_data in invoices:
            try:
                self._create_historical_invoice(invoice_data)
                imported += 1
            except Exception as e:
                errors.append(f"Invoice {invoice_data.get('consecutive')}: {str(e)}")

        self.imported_records = imported
        self.error_records = len(errors)
        self.error_log = '\n'.join(errors) if errors else ''
        self.state = 'done'

    def _create_historical_invoice(self, data):
        # Create invoice in Odoo, marked as historical
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self._find_or_create_partner(data),
            'invoice_date': data['date'],
            'cr_einvoice_consecutive': data['consecutive'],
            'cr_einvoice_is_historical': True,  # Mark as imported, not issued by this system
            'cr_einvoice_xml_original': data.get('xml_content'),  # Store original XML
            'state': 'posted',  # Historical invoices are already posted
            # ... other fields
        })
        return invoice
```

**UI/UX:**
- Upload interface with drag-and-drop
- Progress bar during import
- Summary report with error details
- Option to download error log

**Benefits:**
- Unified reporting across all periods
- Customer convenience (single source of truth)
- Competitive advantage vs. providers who don't offer this
- Not legally required, so low priority

### Priority 5: Migration Validation Dashboard (Nice to Have)

**Feature:** Real-time dashboard showing migration health and consecutive number status

**Implementation:**
```python
class CrEinvoiceMigrationDashboard(models.Model):
    _name = 'cr.einvoice.migration.dashboard'
    _description = 'Migration Dashboard'
    _auto = False  # SQL view, not a table

    sequence_id = fields.Many2one('ir.sequence', 'Sequence')
    establishment_code = fields.Char('Establishment')
    terminal_code = fields.Char('Terminal')
    document_type = fields.Char('Document Type')

    expected_next = fields.Integer('Expected Next Consecutive')
    actual_next = fields.Integer('Actual Next Consecutive')
    is_valid = fields.Boolean('Sequence Valid', compute='_compute_is_valid')

    invoices_issued = fields.Integer('Invoices Issued')
    last_invoice_date = fields.Datetime('Last Invoice Date')
    rejection_count = fields.Integer('Rejections (Last 7 Days)')
    rejection_rate = fields.Float('Rejection Rate %')

    def _compute_is_valid(self):
        for record in self:
            # Check for gaps, duplicates, etc.
            record.is_valid = record.expected_next == record.actual_next
```

**UI/UX:**
- Kanban or dashboard view
- Color-coded status indicators (green = healthy, red = issue)
- Quick filters (by establishment, by document type)
- Drill-down to details

**Benefits:**
- Proactive issue detection
- Confidence during migration period
- Easy to show customer "everything is working"
- Professional appearance

### Priority 6: Cut-Over Checklist Widget (Nice to Have)

**Feature:** Interactive checklist that guides through go-live process

**Implementation:**
```python
class CrEinvoiceCutoverChecklist(models.Model):
    _name = 'cr.einvoice.cutover.checklist'
    _description = 'Migration Cut-Over Checklist'
    _order = 'sequence, id'

    company_id = fields.Many2one('res.company', 'Company', required=True)
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Task', required=True)
    description = fields.Text('Description')
    phase = fields.Selection([
        ('pre', 'Pre-Migration'),
        ('cutover', 'Cut-Over Day'),
        ('post', 'Post-Migration')
    ], 'Phase', required=True)

    is_completed = fields.Boolean('Completed')
    completed_by = fields.Many2one('res.users', 'Completed By')
    completed_date = fields.Datetime('Completed Date')
    notes = fields.Text('Notes')

    # Template tasks created automatically
    is_template = fields.Boolean('Is Template Task', default=True)
```

**UI/UX:**
- Kanban board by phase
- Check boxes to mark complete
- Progress bar showing % complete
- Printable checklist for offline use

**Benefits:**
- Reduces missed steps
- Confidence during stressful cut-over
- Training tool for support team
- Can be customized per customer

---

## 10. Key Takeaways for Production Deployment

### What You MUST Do

1. **Consecutive Number Continuity**
   - If customer is migrating from existing e-invoicing system: MUST continue numbering
   - Build configuration interface to set starting numbers
   - Validate configuration before going live

2. **Version 4.4 Compliance**
   - Ensure ALL generated invoices use v4.4 format
   - Include system provider field in XML
   - Support all v4.4 changes (REP document type, SINPE Móvil payment method, etc.)

3. **Digital Signature**
   - Verify certificate validity before go-live
   - Test signature in sandbox
   - Monitor certificate expiration

4. **Testing Process**
   - Use Hacienda sandbox for ALL testing
   - Test each document type
   - Verify consecutive numbers in XML
   - Verify acceptance by Hacienda

5. **Audit Trail**
   - Log all sequence configuration changes
   - Document migration date and details
   - Keep evidence of first invoice acceptance

### What You DON'T Need to Do

1. **Hacienda Notification**
   - No form to submit when changing systems
   - No approval process required
   - No registration of specific software (except system provider field IN the invoice)

2. **Historical Invoice Import**
   - Not legally required
   - Can be offered as value-added service
   - Customers can keep old invoices in old system

3. **Gradual Migration**
   - No requirement for parallel operation
   - Hard cut-over is simpler and safer
   - 3-hour validation time is fast enough

### What You SHOULD Do (Best Practices)

1. **Onboarding Wizard**
   - Detect migration vs. new user
   - Guide through configuration
   - Validate before applying

2. **CSV Import for Consecutive Numbers**
   - Faster than manual entry
   - Reduces errors
   - Provides template for consistency

3. **Sequence Locking**
   - Prevent accidental changes
   - Admin-only unlock
   - Audit log for unlocks

4. **Clear Documentation**
   - Migration guide for customers
   - Quick reference for staff
   - Troubleshooting tips

5. **Post-Go-Live Support**
   - Monitor first week closely
   - Daily check-in with customer
   - Document issues and resolutions

### Common Misconceptions Debunked

1. **MYTH:** "You need Hacienda approval to change systems"
   - **FACT:** No approval needed, just maintain consecutive numbers

2. **MYTH:** "You must import all historical invoices"
   - **FACT:** Not required, but can be offered as service

3. **MYTH:** "You need to run both systems in parallel"
   - **FACT:** Not necessary, hard cut-over is simpler

4. **MYTH:** "There's a special 'migration' invoice format"
   - **FACT:** Same format, just continue consecutive numbers

5. **MYTH:** "You can restart consecutive numbers when changing systems"
   - **FACT:** MUST continue from last number (unless first-time user)

### Red Flags to Avoid

1. **Duplicate Consecutive Numbers**
   - Causes automatic rejection
   - Damages customer trust
   - Difficult to explain to Hacienda

2. **Version 4.3 in Production**
   - Rejected since September 1, 2025
   - Shows lack of compliance
   - Customer cannot use invoices

3. **Unlocked Sequences**
   - User can accidentally change
   - Creates compliance risk
   - No audit trail

4. **No Testing in Sandbox**
   - First invoice in production fails
   - Customer has no valid invoice
   - Emergency troubleshooting

5. **Insufficient Staff Training**
   - User errors cause rejections
   - Support burden increases
   - Customer dissatisfaction

### Success Metrics

**Technical Metrics:**
- Rejection rate <1% in first week
- 100% of invoices include system provider field
- Zero duplicate consecutive numbers
- 100% digital signature validation

**Process Metrics:**
- Migration wizard completion rate
- Average configuration time
- Time from go-live to first accepted invoice

**Customer Metrics:**
- Customer satisfaction score
- Support tickets per customer
- Onboarding completion time

### Next Steps for Development

1. **Immediate (Before Launch):**
   - [ ] Implement migration onboarding wizard
   - [ ] Add consecutive number configuration interface
   - [ ] Build sequence locking mechanism
   - [ ] Create audit log for all sequence changes
   - [ ] Test with multiple migration scenarios
   - [ ] Write migration guide documentation

2. **Short-Term (First Month After Launch):**
   - [ ] Monitor migration success rate
   - [ ] Collect customer feedback
   - [ ] Identify common issues
   - [ ] Update documentation based on real experiences
   - [ ] Build FAQ from support tickets

3. **Medium-Term (Months 2-6):**
   - [ ] Build historical invoice import tool (if customers request)
   - [ ] Create migration dashboard
   - [ ] Develop automated testing for migration scenarios
   - [ ] Consider API integrations with common providers (FACTURATica, TicoPay, etc.)

4. **Long-Term (Year 1+):**
   - [ ] Analyze migration data to improve process
   - [ ] Build AI-powered migration assistant
   - [ ] Create certification program for migration consultants
   - [ ] Develop migration-as-a-service offering

---

## Sources and References

### Official Hacienda Documentation
- [Comprobantes Electrónicos y Versión 4.4 - Dirección General de Tributación](https://www.hacienda.go.cr/docs/ComprobantesElectronicos-GeneralidadesyVersion4.4.marzo2025.pdf)
- [Administración Tributaria Virtual - ATV](https://atv.hacienda.go.cr/ATV/login.aspx)
- [TRIBU-CR Portal (new system)](https://ovitribucr.hacienda.go.cr/home/)

### Regulations
- [Resolución DGT-R-033-2019 (superseded)](https://pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=89094&nValor3=116989&strTipM=TC)
- [Resolution MH-DGT-RES-0027-2024 (current)](https://www.hacienda.go.cr/docs/DGT-R-000-2024DisposicionesTecnicasDeComprobantesElectronicosCP.pdf)
- [Análisis Resolución DGT-R-033-2019 - GRUPOEV](https://grupoevcr.com/comprobantes-electronicos-analisis-ndgt-r-033-2019/)

### Consecutive Numbering
- [Número Consecutivo y Clave - Roy Rojas](https://royrojas.com/numero-consecutivo-y-clave-en-la-factura-electronica-en-costa-rica/)
- [Numeración Consecutiva - HuliPractice](https://blog.hulipractice.com/como-funciona-la-numeracion-consecutiva-en-la-factura-electronica-de-costa-rica/)
- [Numeración Consecutiva - TicoFacturas](https://www.ticofacturas.com/blog/como-funciona-la-numeracion-consecutiva-en-la-factura-electronica-de-costa-rica.php)

### Version 4.4 Information
- [Facturación electrónica 4.4 - Softland](https://softland.com/cr/nuevos-cambios-de-la-facturacion-electronica-4-4/)
- [Resumen Detallado FE 4.4 - JGutierrez](https://www.consultoresjg.com/cr/resumen-detallado-sobre-facturacion-electronica-4-4-y-hacienda-digital-en-costa-rica-actualizado-y-ampliado-2025/)
- [Comprobante 4.4 - Deloitte](https://www.deloitte.com/latam/es/services/tax/perspectives/cr-comprobante-electronico-4-4-cinco-cambios-relevantes.html)
- [Obligatoriedad FE 4.4 - Siempre al Día](https://siemprealdia.co/costa-rica/impuestos/hacienda-confirma-obligatoriedad-de-la-factura-electronica-4-4/)
- [Factura Electrónica 4.4 - Facturele](https://www.facturele.com/2025/06/03/cambios-factura-version-4-4/)

### Provider Information
- **FACTURATica:**
  - [Cómo cambiar consecutivos - FACTURATica](https://facturatica.com/como-cambiar-los-consecutivos-de-mis-documentos-electronicos/)
  - [Onboarding Efectivo - FACTURATica](https://facturatica.com/onboarding-efectivo-integracion-desde-el-primer-dia/)
  - [FACTURATica Homepage](https://facturatica.com/)
  - [FACTURATica Migration Success - Ticos Land](https://ticosland.com/facturatica-imports-over-100-million-electronic-invoices-from-recently-migrated-customers/)

- **TicoPay:**
  - [TicoPay Homepage](http://ticopays.com/)
  - [TicoPay Blog](https://blog.ticopays.com/)
  - [Guía completa Facturación Electrónica](https://blog.ticopays.com/2021/11/04/guia-facturacion-electronica/)

- **Alanube:**
  - [Alanube Costa Rica](https://www.alanube.co/costarica/)

- **GTI:**
  - [GTI Facturación - Análisis](https://programascontabilidad.com/analisis-de-herramientas/gti-facturacion-costa-rica/)

### General E-Invoicing Information
- [Electronic Invoicing in Costa Rica - EDICOM](https://edicomgroup.com/blog/how-electronic-invoicing-works-in-costa-rica)
- [Practical Guide to E-invoicing - Fonoa](https://www.fonoa.com/blog/practical-guide-to-e-invoicing-in-costa-rica)
- [E-Invoicing Guide - Fonoa](https://www.fonoa.com/resources/country-tax-guides/costa-rica/e-invoicing-and-digital-reporting)
- [E-Invoicing in Costa Rica - Avalara](https://www.avalara.com/vatlive/en/country-guides/south-america/costa-rica-e-services/e-invoicing-in-costa-rica.html)
- [Costa Rica E-Invoicing - Basware](https://www.basware.com/en/compliance-map/costa-rica)

### TRIBU-CR Migration
- [TRIBU-CR Tips - Q Costa Rica](https://qcostarica.com/tips-for-a-successful-transition-to-tribu-cr/)
- [Changes in Hacienda - Asicon Consulting](https://www.asiconcr.com/builder.php?page=article-20250829001-en.php)
- [Costa Rica Ministry of Finance - New Platform - EY](https://www.ey.com/en_gl/technical/tax-alerts/costa-rica-ministry-of-finance-confirms-launch-date-of-new-tax-platform-and-provides-further-details-on-transition-process)

---

## Appendix: CSV Templates

### Template 1: Consecutive Number Migration Import

**Filename:** `consecutive_migration_import.csv`

```csv
establishment_code,terminal_code,document_type,document_type_name,last_consecutive_used,last_invoice_date,notes
001,00001,01,Invoice,0000000523,2025-12-28,Main office invoices
001,00001,02,Debit Note,0000000008,2025-11-15,Rare document type
001,00001,03,Credit Note,0000000045,2025-12-22,Returns and corrections
001,00001,04,Ticket,0000002340,2025-12-28,POS sales
001,00001,05,Purchase Acceptance,0000000120,2025-12-27,Vendor invoices accepted
001,00001,06,Partial Purchase Acceptance,0000000005,2025-10-05,Partial accepts rare
001,00001,07,Purchase Rejection,0000000002,2025-09-12,Rejected vendor invoices
001,00001,08,Electronic Purchase Invoice,0000000030,2025-12-20,Foreign purchases
001,00001,09,Export Electronic Invoice,0000000000,Never used,No exports yet
002,00001,01,Invoice,0000000012,2025-12-20,Branch 1 invoices
002,00001,04,Ticket,0000000089,2025-12-28,Branch 1 POS
```

**Instructions for customers:**
1. Download this template
2. Fill in your last consecutive number for EACH combination of establishment, terminal, and document type
3. Only include document types you actually use (delete rows for unused types)
4. Verify the numbers are correct (this is critical!)
5. Save and upload to Odoo migration wizard

### Template 2: Historical Invoice Import

**Filename:** `historical_invoices_import.csv`

```csv
consecutive,date,customer_identification,customer_name,customer_email,currency,subtotal,tax,total,notes
001-00001-01-0000000001,2024-01-05,104560789,Acme Corp,billing@acme.cr,CRC,100000,13000,113000,First invoice of 2024
001-00001-01-0000000002,2024-01-08,205670890,Beta Inc,info@beta.cr,CRC,250000,32500,282500,
001-00001-01-0000000003,2024-01-10,306781901,Gamma SA,ap@gamma.cr,CRC,175000,22750,197750,Recurring customer
```

**Instructions for customers:**
1. Download this template
2. Export your historical invoice data from your old system
3. Match the columns to this format
4. Upload to Odoo historical import tool
5. Review imported data before finalizing

---

## Conclusion

Based on extensive research of Costa Rica's e-invoicing regulations, provider practices, and technical requirements, the migration/onboarding process for the Odoo 19 e-invoicing module is **straightforward but requires careful attention to consecutive numbering**.

**The good news:**
- No Hacienda notification or approval required
- No mandatory historical data import
- No complex parallel operation needed
- Hard cut-over is simple and low-risk

**The critical requirement:**
- Businesses migrating from existing e-invoicing systems MUST continue their consecutive numbering (cannot restart at 1)
- Configuration interface must be built to set starting numbers
- Sequences must be locked after configuration to prevent tampering

**Recommended implementation:**
1. Build migration onboarding wizard (Priority 1)
2. Implement sequence locking (Priority 1)
3. Create audit log (Priority 1)
4. Document migration process (Priority 1)
5. Offer historical import as value-add (Priority 4)

With these features implemented, the Odoo module will be **production-ready for both new e-invoicing users and migrations from existing systems**, with a professional onboarding experience that rivals commercial providers like FACTURATica.

---

**Report Prepared By:** Market Trend Analyst AI
**Date:** December 29, 2025
**Version:** 1.0
**Status:** Final
**Next Review:** After first 5 production migrations (gather real-world feedback)
