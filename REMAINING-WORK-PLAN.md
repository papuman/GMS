# Remaining Work Plan - Costa Rica E-Invoicing

**Last Updated**: 2026-02-02
**Current Status**: Phase 6 & 7 completion needed

---

## 📊 Current State

### ✅ What's Complete (100%)
- Core e-invoicing (FE, TE, NC, ND) - XML generation
- XAdES-EPES digital signatures (48 tests passing)
- Hacienda API integration with OAuth2
- Tax reports (D101, D150, D151)
- XSD validation
- Retry queue with intelligent error handling
- Payment methods
- **301/301 tests passing (100% pass rate)**

### ⚠️ What Exists But Not Tested
- POS integration code (`pos_order.py`, `pos_config.py`)
- POS offline queue functionality
- POS UI components (JavaScript, XML, CSS)

### 🚧 What's Missing
- **Gym POS store type card** (NEW REQUIREMENT)
- POS integration testing
- Full UI workflow testing
- E2E sandbox validation

---

## 🎯 Remaining Work Breakdown

### Phase 6.5: Complete POS Integration (2-3 days)

#### Task 1: Add Gym POS Store Type Card
**Priority**: HIGH
**Effort**: 0.5 day

**Requirements**:
- Add "Gym" option to POS store selection screen
- **CRITICAL**: E-Invoice should be OPTIONAL, not automatic
  - By default: POS orders do NOT generate e-invoices
  - Only when cashier clicks "Generate E-Invoice" button
  - Requires customer info (name, ID, email)
- Follow exact same UI/design pattern as existing cards:
  - Restaurant (fork/plate icon)
  - Bar (cocktail icon)
  - Retail (cash register icon)
  - Clothes (t-shirt icon)
  - Furniture (desk/chair icon)
  - Bakery (bread icon)
- Create gym icon (dumbbell/fitness) matching outline style
- Description: "Memberships, day passes, personal training"

**Files to create/modify**:
```
l10n_cr_einvoice/
├── static/
│   ├── src/
│   │   ├── xml/pos_gym_store.xml       (NEW - Gym card template)
│   │   ├── js/pos_gym_config.js        (NEW - Gym config logic)
│   │   └── css/pos_gym_icon.css        (NEW - Gym icon styling)
│   └── description/
│       └── gym_icon.svg                (NEW - Gym icon asset)
├── data/
│   ├── pos_config_gym.xml              (NEW - Gym POS config)
│   └── gym_pos_products.xml            (NEW - Gym products)
└── tests/
    └── test_pos_gym.py                 (NEW - Gym POS tests)
```

**Deliverables**:
- [ ] Gym card appears in POS store selection
- [ ] Clicking gym card loads gym-specific configuration
- [ ] Gym products available in POS
- [ ] E-invoice integration works from gym POS
- [ ] **Retroactive e-invoice generation** - Customer can request after payment

---

#### Task 2: Implement Optional E-Invoice Button in POS
**Priority**: CRITICAL
**Effort**: 0.5 day

**IMPORTANT**: E-invoices should NOT be automatic for every sale!

**Requirements**:
- [ ] Add "Generate E-Invoice" toggle button in POS payment screen
- [ ] Button is OFF by default
- [ ] When enabled, show customer info form:
  - Customer name (required)
  - ID number (required - for Hacienda)
  - Email (optional - for sending PDF)
- [ ] Only generate TE when button is enabled
- [ ] Normal sales: Just POS receipt (no Hacienda submission)
- [ ] E-Invoice sales: TE + Hacienda submission + QR code

**Files to modify**:
```
l10n_cr_einvoice/static/src/xml/pos_payment_screen.xml  (add button)
l10n_cr_einvoice/static/src/js/pos_payment_screen.js    (toggle logic)
l10n_cr_einvoice/models/pos_order.py                    (Odoo 19 implementation)
```

**Code changes needed**:
```python
# pos_order.py - Implement for Odoo 19
@api.model
def _order_fields(self, ui_order):
    """Override to capture l10n_cr_is_einvoice flag from POS"""
    fields = super()._order_fields(ui_order)
    fields['l10n_cr_is_einvoice'] = ui_order.get('l10n_cr_is_einvoice', False)
    return fields

def _generate_einvoice_if_requested(self):
    """Generate e-invoice only if explicitly requested"""
    if self.l10n_cr_is_einvoice and self.config_id.l10n_cr_enable_einvoice:
        self._create_einvoice_from_pos()

def action_generate_einvoice_retroactive(self, partner_id, partner_vat, partner_email):
    """
    Generate e-invoice after payment completed.
    Called when customer returns and requests invoice.
    """
    self.ensure_one()

    # Validation
    if self.state != 'paid':
        raise UserError(_("Can only generate e-invoice for paid orders"))

    if self.l10n_cr_einvoice_document_id:
        raise UserError(_("This order already has an e-invoice"))

    # Update customer info
    self.write({
        'partner_id': partner_id,
        'l10n_cr_is_einvoice': True
    })

    # Generate e-invoice with existing order data
    self._create_einvoice_from_pos()

    return {
        'type': 'ir.actions.client',
        'tag': 'pos.ui',
        'params': {
            'order_id': self.id,
            'reprint_receipt': True
        }
    }
```

---

#### Task 2B: Retroactive E-Invoice Generation (IMPORTANT)
**Priority**: HIGH
**Effort**: 0.5 day

**Real-world scenario**:
```
Customer pays → Gets receipt → Leaves
5 minutes later...
Customer returns: "I need an invoice for taxes!"
```

**Requirements**:
- [ ] Add "Recent Orders" search in POS
- [ ] Show last 50 orders from current session
- [ ] Add "Generate E-Invoice" button on completed orders
- [ ] Capture customer info when generating retroactively
- [ ] Generate TE with same order data
- [ ] Submit to Hacienda
- [ ] Reprint receipt with QR code
- [ ] Update order to mark it has e-invoice

**UI additions**:
```
File: l10n_cr_einvoice/static/src/xml/pos_orders_screen.xml
Add: Order history with e-invoice generation option
```

**Validations needed**:
- Order must be in 'paid' state
- Order cannot already have an e-invoice
- Customer ID must be valid (9 or 10 digits)
- Order cannot be older than X days (business rule)

**Code implementation**:
```python
# pos_order.py
def action_generate_einvoice_retroactive(self):
    """Generate e-invoice after order completion"""
    # Validation, generation, submission
    # Return receipt for reprinting
```

---

#### Task 3: Gym POS Configuration
**Priority**: HIGH
**Effort**: 1 day

**Configuration includes**:
- [ ] Gym product categories pre-configured
  - Monthly membership (₡25,000 + IVA)
  - Quarterly membership (₡70,000 + IVA)
  - Annual membership (₡250,000 + IVA)
  - Day pass (₡5,000 + IVA)
  - Personal training session (₡15,000 + IVA)
  - Equipment rental (₡3,000 + IVA)
- [ ] Hacienda e-invoice settings enabled
- [ ] Costa Rica payment methods configured
- [ ] TE (Tiquete Electrónico) auto-generation
- [ ] Offline mode with retry queue
- [ ] Receipt template with gym branding

---

#### Task 3: POS Integration Testing
**Priority**: HIGH
**Effort**: 1 day

**Tests to run/fix**:
- [ ] Run `test_pos_offline.py` tests
- [ ] Fix any failing POS tests
- [ ] Create `test_pos_gym.py` for gym-specific flows
- [ ] Test scenarios:
  - Member purchases membership → TE generated
  - Day pass sale → TE with e-invoice
  - Personal training booking → proper tax codes
  - Offline mode → queues for sync
  - Receipt printing → QR code present

**Commands**:
```bash
# Run POS tests
docker compose run --rm odoo -d GMS --test-enable \
  --test-tags=pos_offline --stop-after-init --no-http

# Run gym POS tests
docker compose run --rm odoo -d GMS --test-enable \
  --test-tags=pos_gym --stop-after-init --no-http
```

---

### Phase 7.5: Integration & UI Testing (1 day)

#### Task 4: Full Workflow Integration Testing
**Priority**: MEDIUM
**Effort**: 0.5 day

**Manual testing checklist**:
- [ ] Create invoice in Odoo Invoicing module
- [ ] Verify e-invoice document auto-created
- [ ] Generate XML
- [ ] Sign XML with certificate
- [ ] Submit to Hacienda (sandbox)
- [ ] Check acceptance status
- [ ] Verify PDF generation with QR code
- [ ] Test email delivery to customer

**Test from POS**:
- [ ] Open gym POS
- [ ] Sell membership
- [ ] Verify TE auto-generated
- [ ] Print receipt with QR code
- [ ] Check offline queue works

---

#### Task 5: Batch Operations Testing
**Priority**: LOW
**Effort**: 0.5 day

- [ ] Test bulk invoice generation
- [ ] Test batch XML generation
- [ ] Test batch submission to Hacienda
- [ ] Verify performance (target: <15s per invoice in sandbox)

---

### Phase 7.6: E2E Sandbox Validation (0.5 day)

#### Task 6: Manual E2E Testing
**Priority**: HIGH
**Effort**: 0.5 day

Follow guide: `E2E-SANDBOX-TESTING-GUIDE.md`

**Scenarios to validate**:
- [ ] FE (Factura Electrónica) complete lifecycle
- [ ] TE (Tiquete Electrónico) from POS
- [ ] NC (Nota de Crédito) - Credit note
- [ ] ND (Nota de Débito) - Debit note
- [ ] Bulk submission (10 invoices)
- [ ] Retry queue on failure
- [ ] Idempotency (no duplicates)

**Success criteria**:
- All 7 scenarios complete successfully
- Real Hacienda sandbox accepts invoices
- Certificate authentication works
- Response messages captured correctly

---

## 📅 Execution Timeline

### Week 1: Complete POS Integration
**Days 1-3: Phase 6.5**
- Day 1: Gym POS store card + configuration
- Day 2: POS testing and fixes
- Day 3: Gym-specific POS features

**Deliverable**: Gym POS fully functional with e-invoicing

### Week 2: Final Testing & Validation
**Days 4-5: Phase 7.5 + 7.6**
- Day 4: Full integration testing + batch operations
- Day 5: E2E sandbox validation

**Deliverable**: All integration points validated, sandbox approved

### Week 3: Phase 8 Preparation
- Production certificate acquisition
- Production environment setup
- User training
- Go-live planning

---

## 🎯 Success Criteria

**Phase 6.5 Complete When**:
- [ ] Gym card appears in POS store selection
- [ ] Gym POS loads with correct configuration
- [ ] Gym products available and properly taxed
- [ ] POS→TE e-invoice generation works
- [ ] All POS tests passing
- [ ] Offline queue tested and working

**Phase 7.5 Complete When**:
- [ ] Full invoice workflow tested end-to-end
- [ ] POS workflow tested end-to-end
- [ ] Batch operations validated
- [ ] Performance targets met

**Phase 7.6 Complete When**:
- [ ] All 7 E2E scenarios pass with real Hacienda sandbox
- [ ] Certificate authentication verified
- [ ] Ready for production deployment

---

## 🚀 Next Steps

**Immediate action**:
1. Review this plan
2. Confirm priorities and timeline
3. Begin Phase 6.5: Gym POS store card implementation

**Questions to confirm**:
- Does the 2-3 day timeline for Phase 6.5 work?
- Should we complete all POS work before E2E testing?
- Any changes to Gym POS requirements (products, features)?

---

## 📝 Notes

- Original estimate was Phase 6 complete, but POS needs testing + Gym card
- Core e-invoicing is solid (100% test coverage)
- Main risk is POS integration bugs discovered during testing
- E2E sandbox testing is final validation before production

**Status**: Ready to begin Phase 6.5 implementation
