---
title: "Costa Rica E-Invoice Migration Best Practices - Consecutive Numbering & Data Import"
category: "research"
domain: "costa-rica"
layer: "technical-guide" # Migration implementation guide
audience: ["developer", "product-manager", "support"]
last_updated: "2026-01-01"
status: "production-ready"
version: "1.0.0"
maintainer: "Product Team"
extracted_from: "CR-EINVOICING-MIGRATION-ONBOARDING-RESEARCH.md (2,121 lines)"
research_date: "December 29, 2025"
related_docs:
  - "docs/02-research/costa-rica/00-COSTA-RICA-RESEARCH-INDEX.md"
  - "docs/02-research/costa-rica/einvoice-providers-landscape.md"
  - "docs/02-research/costa-rica/compliance-requirements.md"
  - "docs/../../PHASE3_API_INTEGRATION.md"
keywords: ["costa-rica", "migration", "consecutive-numbering", "20-digit", "hacienda", "sequence", "data-import", "onboarding"]
---

# 📍 Navigation Breadcrumb
[Home](../../index.md) > [Research](../../index.md) > [Costa Rica](./00-COSTA-RICA-RESEARCH-INDEX.md) > Migration Best Practices

---

# Costa Rica E-Invoice Migration Best Practices

**Research Date:** December 29, 2025
**Focus:** Consecutive number preservation, migration workflows, onboarding patterns
**Legal Basis:** Resolution DGT-R-033-2019, MH-DGT-RES-0027-2024

---

## 🚨 CRITICAL: The #1 Migration Requirement

### Invoice Number Continuity is MANDATORY

**When migrating from an existing e-invoicing system, businesses MUST continue their consecutive numbering sequence. Starting fresh at "1" is NOT permitted.**

**Legal Authority:** Resolution DGT-R-033-2019 (confirmed in MH-DGT-RES-0027-2024)

> "Organizations already using e-invoices must maintain the consecutive numbering when switching emission platforms"

**Consequences of Resetting to 1:**
- ❌ Hacienda automatic rejection
- ❌ Duplicate consecutive number errors
- ❌ Regulatory compliance violation
- ❌ Audit red flags

**THE most common migration failure:** Not preserving consecutive numbers.

---

## Consecutive Number Structure (20 Digits)

### Format Breakdown

```
AAA-BBBBB-CC-DDDDDDDDDD
│   │      │   │
│   │      │   └─ Digits 11-20: Sequential number (0000000001 to 9999999999)
│   │      └───── Digits 9-10: Document type (01, 02, 03, 04, etc.)
│   └──────────── Digits 4-8: Terminal/POS identifier (00001, 00002, etc.)
└──────────────── Digits 1-3: Establishment code (001, 002, 003, etc.)
```

### Document Type Codes

| Code | Document Type | Example Consecutive |
|------|---------------|---------------------|
| **01** | Factura Electrónica (Invoice) | 001-00001-01-0000000152 |
| **02** | Nota de Débito (Debit Note) | 001-00001-02-0000000008 |
| **03** | Nota de Crédito (Credit Note) | 001-00001-03-0000000023 |
| **04** | Tiquete Electrónico (Ticket) | 001-00001-04-0000000445 |
| **05** | Aceptación de Compra | 001-00001-05-0000000001 |
| **06** | Aceptación Parcial de Compra | 001-00001-06-0000000000 |
| **07** | Rechazo de Compra | 001-00001-07-0000000000 |
| **08** | Factura Electrónica de Compra | 001-00001-08-0000000000 |
| **09** | Factura Electrónica de Exportación | 001-00001-09-0000000000 |

### Key Rules

**1. Each document type has its own sequence**
- Invoice at 152, Credit Note at 23 ← Independent counters

**2. Each terminal has its own sequence**
- Terminal 1: 001-00001-01-0000000152
- Terminal 2: 001-00002-01-0000000089
- ← Different sequences per POS

**3. Each establishment has its own sequence**
- HQ (001): 001-00001-01-0000000152
- Branch 1 (002): 002-00001-01-0000000034
- ← Different sequences per location

**4. Maximum is 9,999,999,999**
- After that, can reset to 1
- Extremely unlikely (10 billion invoices!)

---

## Migration Scenarios

### Scenario 1: First-Time E-Invoicing (from Paper)

**Starting Point:** Business has been using paper invoices

**Consecutive Number Handling:**
- ✅ Start at `00000000001` for each document type
- ✅ No previous sequence to preserve
- ✅ Fresh start permitted

**Requirements:**
1. Register in ATV/OVI as "Emisor-Receptor Electrónico"
2. Obtain digital certificate from Banco Central
3. Configure establishment (001) and terminal (00001) codes
4. Initialize sequences at 1

**Implementation:**

```python
# First-time e-invoicing - start at 1
consecutive_sequences = {
    '01': {'last_used': 0, 'next': 1},  # Invoices
    '02': {'last_used': 0, 'next': 1},  # Debit Notes
    '03': {'last_used': 0, 'next': 1},  # Credit Notes
    '04': {'last_used': 0, 'next': 1},  # Tickets
    # ... other document types
}
```

---

### Scenario 2: Switching Providers (e.g., GTI → GMS)

**Starting Point:** Business already using e-invoicing (GTI, Facturele, etc.)

**Consecutive Number Handling:**
- 🔴 **CRITICAL:** Continue from last number used
- ❌ **CANNOT** reset to 1
- ✅ Must know exact last consecutive per document type

**Migration Workflow:**

#### Step 1: Gather Last Consecutive Numbers

**From Old Provider (GTI Example):**

```
Last invoices issued in GTI:
- Invoice (01): 001-00001-01-0000000152  ← Last was 152
- Credit Note (03): 001-00001-03-0000000023  ← Last was 23
- Ticket (04): 001-00001-04-0000000445  ← Last was 445
```

**Requirement:** Get this info BEFORE canceling old provider!

---

#### Step 2: Configure New System (GMS)

**In Odoo/GMS:**

```python
# Configure sequences to continue from last number
establishment_code = '001'
terminal_code = '00001'

# Set next consecutive numbers (last + 1)
consecutive_sequences = {
    '01': {'last_used': 152, 'next': 153},  # Invoices
    '02': {'last_used': 0, 'next': 1},      # Debit Notes (never used)
    '03': {'last_used': 23, 'next': 24},    # Credit Notes
    '04': {'last_used': 445, 'next': 446},  # Tickets
}
```

**Implementation in Odoo:**

```python
# l10n_cr_einvoice/models/hacienda_sequence.py

class HaciendaSequence(models.Model):
    _name = 'l10n_cr.hacienda.sequence'

    establishment_code = fields.Char(size=3, required=True, default='001')
    terminal_code = fields.Char(size=5, required=True, default='00001')
    document_type = fields.Selection([
        ('01', 'Factura Electrónica'),
        ('02', 'Nota de Débito'),
        ('03', 'Nota de Crédito'),
        ('04', 'Tiquete Electrónico'),
        # ... more types
    ], required=True)

    last_consecutive = fields.Integer(
        string='Último Consecutivo Usado',
        default=0,
        help='Last consecutive number used. Next will be last + 1.'
    )

    @api.model
    def get_next_consecutive(self, establishment, terminal, doc_type):
        """Get and increment next consecutive number"""
        sequence = self.search([
            ('establishment_code', '=', establishment),
            ('terminal_code', '=', terminal),
            ('document_type', '=', doc_type),
        ], limit=1)

        if not sequence:
            # First time for this combination - start at 1
            sequence = self.create({
                'establishment_code': establishment,
                'terminal_code': terminal,
                'document_type': doc_type,
                'last_consecutive': 0,
            })

        # Increment and return
        next_number = sequence.last_consecutive + 1
        sequence.last_consecutive = next_number

        return next_number

    def format_consecutive(self, number):
        """Format as 20-digit consecutive"""
        return (
            f"{self.establishment_code}-"
            f"{self.terminal_code}-"
            f"{self.document_type}-"
            f"{str(number).zfill(10)}"
        )
```

---

#### Step 3: Test Sequence Before Production

**CRITICAL:** Test with sandbox before going live!

```python
# Test sequence generation
test_sequence = env['l10n_cr.hacienda.sequence'].create({
    'establishment_code': '001',
    'terminal_code': '00001',
    'document_type': '01',
    'last_consecutive': 152,  # From GTI
})

# Should generate 153
next = test_sequence.get_next_consecutive('001', '00001', '01')
assert next == 153, f"Expected 153, got {next}"

# Should format correctly
formatted = test_sequence.format_consecutive(153)
assert formatted == '001-00001-01-0000000153'
```

---

#### Step 4: Validation Checklist

Before going live with new system:

- [ ] Last consecutive number from old system confirmed
- [ ] New system configured with last + 1
- [ ] Test invoice generated with correct number
- [ ] Test invoice submitted to Hacienda sandbox
- [ ] Hacienda accepted test invoice
- [ ] No duplicate consecutive errors
- [ ] Old system access still available (backup)

**If ANY check fails:** DO NOT go live. Fix first.

---

### Scenario 3: Adding New Branch/Terminal

**Starting Point:** Existing e-invoicing at HQ, adding new location

**Consecutive Number Handling:**
- ✅ New branch starts at 1 (new sequence)
- ✅ Branch code (002, 003, etc.) distinguishes sequences
- ✅ HQ sequence continues unaffected

**Example:**

```
HQ (001):
- 001-00001-01-0000000152  ← Continues normally

New Branch (002):
- 002-00001-01-0000000001  ← Starts at 1 (OK!)
```

**Implementation:**

```python
# Add new branch
new_branch_sequence = env['l10n_cr.hacienda.sequence'].create({
    'establishment_code': '002',  # New branch code
    'terminal_code': '00001',
    'document_type': '01',
    'last_consecutive': 0,  # Start at 1
})
```

---

### Scenario 4: Reached Maximum (9,999,999,999)

**Extremely Rare Scenario:** 10 billion invoices issued

**Consecutive Number Handling:**
- ✅ Can restart at 1
- ✅ No special notification to Hacienda
- ✅ Automatic validation continues

**Likelihood:** Almost zero for gyms
- 10 invoices/day = 2.74M years to reach max
- 100 invoices/day = 274,000 years to reach max

**If it happens:**

```python
if sequence.last_consecutive >= 9999999999:
    sequence.last_consecutive = 0  # Reset to 1
```

---

## Migration Workflow Patterns

### Pattern 1: Manual Consecutive Setup

**Provider Example:** FACTURATica

**Process:**
1. Customer emails facturatica@zarza.com
2. Customer completes template with last consecutive for EACH document type
3. Support manually adjusts sequences
4. Customer receives confirmation
5. Customer can begin invoicing

**Pros:**
- ✅ Human verification (prevents errors)
- ✅ Support handles edge cases
- ✅ Audit trail via email

**Cons:**
- ⏱️ Slow (manual process)
- 👤 Requires support intervention
- 📧 Dependency on email communication

**GMS Implementation:** NOT RECOMMENDED for scale

---

### Pattern 2: Self-Service Consecutive Configuration

**Provider Example:** Alegra, modern platforms

**Process:**
1. User clicks "Configure Consecutive Numbers"
2. System shows form with last consecutive for each doc type
3. User enters last number from old system
4. System validates format (10 digits max)
5. System sets next = last + 1
6. User confirms → sequences activated

**Pros:**
- ⚡ Fast (immediate activation)
- 🎯 User maintains control
- ✅ No support dependency

**Cons:**
- ⚠️ Risk of user error (typos)
- ⚠️ No validation of accuracy
- ⚠️ Could set wrong numbers

**GMS Recommendation:** ✅ **USE THIS** with validation

---

### Pattern 3: XML Import with Auto-Detection

**Provider Example:** FACTURATica (historical import)

**Process:**
1. User uploads XML files from old system
2. System parses consecutive numbers from XML
3. System identifies highest consecutive per document type
4. System auto-sets next = max + 1
5. User reviews detected numbers
6. User confirms → sequences activated

**Pros:**
- ✅ Accurate (source of truth: XML files)
- ✅ No manual data entry
- ✅ Can validate against old system

**Cons:**
- 🔧 Complex implementation
- 📦 Requires access to old XMLs
- ⏱️ Processing time for large datasets

**GMS Recommendation:** ✅ **IDEAL** for migrations with historical data

---

## Recommended GMS Migration Wizard

### UX Flow: Hybrid (Self-Service + Auto-Detection)

**Step 1: Migration Type Selection**

```
┌──────────────────────────────────────────────┐
│ Configure E-Invoicing Sequences              │
├──────────────────────────────────────────────┤
│                                              │
│ Are you migrating from another system?      │
│                                              │
│  ○ No - I'm using e-invoicing for the first │
│      time (Start at 1)                       │
│                                              │
│  ● Yes - I'm switching from another provider │
│      (Continue my sequences)                 │
│                                              │
│         [Next]                               │
└──────────────────────────────────────────────┘
```

---

**Step 2A: First-Time User (Simple)**

```
┌──────────────────────────────────────────────┐
│ Welcome to E-Invoicing!                      │
├──────────────────────────────────────────────┤
│                                              │
│ Your sequences will start at:                │
│                                              │
│ Facturas: 001-00001-01-0000000001           │
│ Tiquetes: 001-00001-04-0000000001           │
│                                              │
│ ✓ Ready to start invoicing!                 │
│                                              │
│         [Finish Setup]                       │
└──────────────────────────────────────────────┘
```

---

**Step 2B: Migration User (Complex)**

```
┌──────────────────────────────────────────────┐
│ Configure Consecutive Numbers                │
├──────────────────────────────────────────────┤
│                                              │
│ Choose how to set your sequences:           │
│                                              │
│  ○ Import XML files (Automatic detection)   │
│  ● Enter manually                            │
│                                              │
│         [Next]                               │
└──────────────────────────────────────────────┘
```

---

**Step 3A: XML Import (Automatic)**

```
┌──────────────────────────────────────────────┐
│ Import XML Files                             │
├──────────────────────────────────────────────┤
│                                              │
│ Upload your last 10-20 invoices from your   │
│ previous system (XML format):                │
│                                              │
│  [📎 Drop files here or click to browse]    │
│                                              │
│  Detected files: 15 XMLs                     │
│                                              │
│         [Analyze Files]                      │
└──────────────────────────────────────────────┘
```

**After Analysis:**

```
┌──────────────────────────────────────────────┐
│ Detected Consecutive Numbers                 │
├──────────────────────────────────────────────┤
│                                              │
│ Last numbers found in your XMLs:             │
│                                              │
│ Facturas (01):       152                     │
│ Tiquetes (04):       445                     │
│ Notas de Crédito:    23                      │
│                                              │
│ Your next invoices will be:                  │
│                                              │
│ Facturas: 001-00001-01-0000000153 ✓         │
│ Tiquetes: 001-00001-04-0000000446 ✓         │
│ NC:       001-00001-03-0000000024 ✓         │
│                                              │
│  [ ] I confirm these are correct             │
│                                              │
│         [Save & Activate]                    │
└──────────────────────────────────────────────┘
```

---

**Step 3B: Manual Entry**

```
┌──────────────────────────────────────────────┐
│ Enter Last Consecutive Numbers               │
├──────────────────────────────────────────────┤
│                                              │
│ Enter the LAST number you used in your      │
│ previous system for each document type:      │
│                                              │
│ Facturas (01):     [________152________]    │
│                    Your next: 153            │
│                                              │
│ Tiquetes (04):     [________445________]    │
│                    Your next: 446            │
│                                              │
│ Notas Crédito (03): [_______23________]     │
│                    Your next: 24             │
│                                              │
│  [ ] I confirm these are correct             │
│                                              │
│         [Save & Activate]                    │
└──────────────────────────────────────────────┘
```

---

### Implementation Code

```python
# l10n_cr_einvoice/wizards/migration_wizard.py

class MigrationWizard(models.TransientModel):
    _name = 'l10n_cr.migration.wizard'
    _description = 'E-Invoicing Migration Setup'

    migration_type = fields.Selection([
        ('first_time', 'First-time e-invoicing (start at 1)'),
        ('switching', 'Switching providers (continue sequences)'),
    ], string='Migration Type', required=True)

    import_method = fields.Selection([
        ('xml', 'Import XML files (automatic)'),
        ('manual', 'Enter manually'),
    ], string='How to configure sequences')

    # XML Import
    xml_files = fields.Many2many('ir.attachment', string='XML Files')

    # Manual Entry
    factura_last = fields.Integer('Last Invoice Number', default=0)
    tiquete_last = fields.Integer('Last Ticket Number', default=0)
    nc_last = fields.Integer('Last Credit Note Number', default=0)

    # Detected/Calculated
    factura_next = fields.Integer(compute='_compute_next_numbers')
    tiquete_next = fields.Integer(compute='_compute_next_numbers')
    nc_next = fields.Integer(compute='_compute_next_numbers')

    confirmed = fields.Boolean('I confirm these numbers are correct')

    @api.depends('factura_last', 'tiquete_last', 'nc_last')
    def _compute_next_numbers(self):
        for wizard in self:
            wizard.factura_next = wizard.factura_last + 1
            wizard.tiquete_next = wizard.tiquete_last + 1
            wizard.nc_next = wizard.nc_last + 1

    def action_analyze_xmls(self):
        """Parse XML files to detect last consecutives"""
        if not self.xml_files:
            raise UserError('Please upload at least one XML file')

        max_consecutives = {}

        for attachment in self.xml_files:
            xml_content = base64.b64decode(attachment.datas)
            root = etree.fromstring(xml_content)

            # Extract consecutive from <NumeroConsecutivo>
            consecutive_elem = root.find('.//NumeroConsecutivo')
            if consecutive_elem is not None:
                consecutive = consecutive_elem.text  # e.g., "001-00001-01-0000000152"
                parts = consecutive.split('-')
                doc_type = parts[2]  # "01"
                number = int(parts[3])  # 152

                if doc_type not in max_consecutives or number > max_consecutives[doc_type]:
                    max_consecutives[doc_type] = number

        # Update wizard with detected values
        self.factura_last = max_consecutives.get('01', 0)
        self.tiquete_last = max_consecutives.get('04', 0)
        self.nc_last = max_consecutives.get('03', 0)

        return {'type': 'ir.actions.do_nothing'}

    def action_save_and_activate(self):
        """Create/update sequence records"""
        if not self.confirmed:
            raise UserError('Please confirm the consecutive numbers are correct')

        # Create sequences
        sequences = [
            ('01', self.factura_last),
            ('04', self.tiquete_last),
            ('03', self.nc_last),
        ]

        for doc_type, last_consecutive in sequences:
            self.env['l10n_cr.hacienda.sequence'].create({
                'establishment_code': '001',
                'terminal_code': '00001',
                'document_type': doc_type,
                'last_consecutive': last_consecutive,
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Migration Complete!',
                'message': f'Your sequences are configured. Next invoice will be {self.factura_next}',
                'sticky': False,
                'type': 'success',
            }
        }
```

---

## Validation & Error Prevention

### Pre-Migration Checklist

Before migrating customer to GMS:

**From Old System:**
- [ ] Get last consecutive for EACH document type
- [ ] Export all XML files (5+ years recommended)
- [ ] Document establishment and terminal codes used
- [ ] Verify no pending submissions in old system
- [ ] Keep old system access for 30 days (backup)

**In GMS:**
- [ ] Test sequence configuration in sandbox
- [ ] Submit test invoice to Hacienda sandbox
- [ ] Verify no duplicate consecutive errors
- [ ] Confirm next number = last + 1
- [ ] Validate 20-digit format correct

**Go-Live:**
- [ ] Configure production sequences
- [ ] Issue first invoice
- [ ] Submit to Hacienda
- [ ] Wait for acceptance (within 3 hours)
- [ ] Monitor for any rejections

---

### Common Migration Errors

**Error 1: Starting at 1 when already using e-invoicing**

```
⚠️ DUPLICATE CONSECUTIVE DETECTED
Invoice 001-00001-01-0000000001 already exists.
Hacienda rejection reason: Duplicate number.
```

**Fix:** Configure last consecutive from old system + 1

---

**Error 2: Missing document type sequence**

```
⚠️ NO SEQUENCE CONFIGURED
Document type "03" (Credit Note) has no sequence.
Cannot generate consecutive number.
```

**Fix:** Initialize sequence for all document types (even if last = 0)

---

**Error 3: Wrong establishment/terminal code**

```
⚠️ SEQUENCE MISMATCH
Generated: 002-00001-01-0000000001
Expected:  001-00001-01-0000000153
```

**Fix:** Verify establishment (001) and terminal (00001) codes match old system

---

## Related Documentation

**🔬 For Provider Details:**
- [Provider Landscape](./einvoice-providers-landscape.md) - FACTURATica migration stats

**⚖️ For Compliance:**
- [Compliance Requirements](./compliance-requirements.md) - Legal consecutive numbering rules

**💻 For Implementation:**
- [Phase 3: API Integration](../../../PHASE3_API_INTEGRATION.md) - Hacienda submission

---

**Research Date:** December 29, 2025
**Legal Basis:** Resolution DGT-R-033-2019, MH-DGT-RES-0027-2024
**Confidence:** HIGH (regulatory requirements + provider practices)

**KEY TAKEAWAY:** Consecutive number preservation is THE #1 migration requirement. GMS MUST implement self-service configuration wizard with XML auto-detection to ensure accuracy and prevent costly errors.
