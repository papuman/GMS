# Week 1 Implementation Plan - Critical Blockers Resolution

**Sprint Goal:** Ship all 3 critical competitive gaps to achieve production readiness
**Timeline:** Monday - Friday (40 hours total, 32 hours planned work + 8 hours buffer)
**Developer:** Solo full-time (8 hours/day)
**Success Metric:** All 3 blockers implemented, tested, documented, and ready for beta by Friday 5pm

---

## Executive Summary

### Critical Blockers (From Competitive Analysis)
1. **Invoice Void/Cancel Wizard** - Currently missing, customers can't void/cancel invoices
2. **Preview Before Hacienda Submission** - Customers submit blindly, causing errors
3. **CR Tax Reports (D-104, D-101, D-151)** - Required for monthly/annual tax filing

### Risk-Based Prioritization
**Day 1-2:** Preview wizard (HIGHEST RISK - blocks all invoicing workflows)
**Day 3-4:** Void/Cancel wizard (HIGH RISK - blocks error correction)
**Day 5:** Tax reports research (LOWER RISK - implementation in Week 2)

---

## Day 1 (Monday) - Preview Wizard Foundation
**Focus:** Build core preview functionality (4 hours work + 1 hour testing + 3 hours documentation/integration)

### Morning Session (4 hours)

#### 9:00 AM - 10:30 AM (1.5h): Wizard Model & UI Structure
**File:** `/l10n_cr_einvoice/wizards/einvoice_preview_wizard.py`
```python
# Tasks:
- [ ] Create TransientModel 'l10n_cr.einvoice.preview.wizard'
- [ ] Add fields: move_id, xml_preview, warnings, validation_status
- [ ] Implement _compute_xml_preview() method
- [ ] Implement _compute_validation_warnings() method
```

**File:** `/l10n_cr_einvoice/wizards/einvoice_preview_wizard_views.xml`
```xml
# Tasks:
- [ ] Create wizard form view with XML preview
- [ ] Add validation warnings section
- [ ] Add Confirm/Cancel buttons
- [ ] Style with Bootstrap classes
```

**Deliverable:** Basic wizard loads from invoice

---

#### 10:30 AM - 12:00 PM (1.5h): XML Generation Preview
**File:** `/l10n_cr_einvoice/models/einvoice_document.py` (extend existing)
```python
# Tasks:
- [ ] Add method action_preview_xml() to generate XML without signing
- [ ] Copy XML generation logic to preview context
- [ ] Handle errors gracefully (show in preview)
- [ ] Add validation checks (partner data, tax codes, amounts)
```

**Deliverable:** Preview shows actual XML that would be sent

---

#### 12:00 PM - 1:00 PM: LUNCH BREAK

---

### Afternoon Session (4 hours)

#### 1:00 PM - 2:30 PM (1.5h): Validation Warning System
**File:** `/l10n_cr_einvoice/wizards/einvoice_preview_wizard.py`
```python
# Tasks:
- [ ] Implement _validate_partner_data() - check cedula, email
- [ ] Implement _validate_tax_configuration() - verify tax codes
- [ ] Implement _validate_amounts() - check totals match
- [ ] Implement _validate_hacienda_requirements() - mandate fields
- [ ] Create warning message builder (severity: error, warning, info)
```

**Deliverable:** Preview shows all validation issues before submission

---

#### 2:30 PM - 4:00 PM (1.5h): Integration with Submit Flow
**File:** `/l10n_cr_einvoice/models/account_move.py` (extend existing)
```python
# Tasks:
- [ ] Add action_preview_einvoice() button to invoice form
- [ ] Wire wizard to return to submit action
- [ ] Update action_generate_and_send_einvoice() to check preview flag
- [ ] Add company setting: require_preview_before_submit (default: True)
```

**File:** `/l10n_cr_einvoice/views/account_move_views.xml`
```xml
# Tasks:
- [ ] Add "Preview E-Invoice" button to invoice
- [ ] Position before "Submit to Hacienda"
- [ ] Show only when l10n_cr_requires_einvoice = True
```

**Deliverable:** Users can click "Preview" from invoice

---

#### 4:00 PM - 5:00 PM (1h): Testing & Documentation
```bash
# Tasks:
- [ ] Manual test: Create invoice > Preview > Check XML
- [ ] Test: Invalid partner data shows warnings
- [ ] Test: Missing tax codes show errors
- [ ] Test: Cancel from preview returns to invoice
- [ ] Test: Confirm from preview submits to Hacienda
- [ ] Write user documentation in PHASE5_QUICK_REFERENCE.md
```

**Deliverable:** Preview wizard tested and documented

---

### Day 1 End-of-Day Deliverables
- ✅ Preview wizard model and views created
- ✅ XML preview generation working
- ✅ Validation warnings system implemented
- ✅ Integration with invoice form complete
- ✅ Basic testing passed
- ✅ User documentation updated

### Day 1 Risks & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| XML generation fails in preview mode | Medium | High | Copy exact logic from production, add error handling |
| Too many validation rules to implement | Medium | Medium | Start with critical 3: partner, tax, amounts. Add more later |
| Integration with existing submit flow breaks | Low | High | Test both preview and direct submit paths |

---

## Day 2 (Tuesday) - Preview Wizard Polish & Advanced Features
**Focus:** PDF preview, edge cases, production-ready polish (5 hours work + 2 hours testing + 1 hour buffer)

### Morning Session (4 hours)

#### 9:00 AM - 10:30 AM (1.5h): PDF Preview Generation
**File:** `/l10n_cr_einvoice/wizards/einvoice_preview_wizard.py`
```python
# Tasks:
- [ ] Add pdf_preview field (Binary)
- [ ] Implement _generate_pdf_preview() using existing PDF generator
- [ ] Add PDF viewer in wizard (iframe or download link)
- [ ] Cache PDF to avoid regeneration
```

**File:** `/l10n_cr_einvoice/wizards/einvoice_preview_wizard_views.xml`
```xml
# Tasks:
- [ ] Add notebook with tabs: XML Preview, PDF Preview, Validation
- [ ] Embed PDF viewer
- [ ] Add download button for both XML and PDF
```

**Deliverable:** Users can preview both XML and PDF before submission

---

#### 10:30 AM - 12:00 PM (1.5h): Edge Cases & Error Handling
```python
# Test scenarios:
- [ ] Handle invoice with no lines (should error)
- [ ] Handle invoice with zero amount (should warn)
- [ ] Handle missing payment method (should error)
- [ ] Handle invalid customer cedula format (should error)
- [ ] Handle missing company certificate (should error)
- [ ] Handle offline Hacienda API (should warn, allow preview)
```

**File:** `/l10n_cr_einvoice/wizards/einvoice_preview_wizard.py`
```python
# Tasks:
- [ ] Add comprehensive validation for all mandatory fields
- [ ] Add graceful error messages in Spanish
- [ ] Implement "Fix Issues" button that returns to invoice
- [ ] Add "Submit Anyway" option for warnings (not errors)
```

**Deliverable:** Preview handles all edge cases gracefully

---

#### 12:00 PM - 1:00 PM: LUNCH BREAK

---

### Afternoon Session (4 hours)

#### 1:00 PM - 3:00 PM (2h): Production Polish & UX
**File:** `/l10n_cr_einvoice/wizards/einvoice_preview_wizard_views.xml`
```xml
# UI/UX Tasks:
- [ ] Add loading spinner while generating preview
- [ ] Color-code validation messages (red=error, yellow=warning, blue=info)
- [ ] Add icon indicators (✗ error, ⚠ warning, ℹ info)
- [ ] Improve XML formatting with syntax highlighting
- [ ] Add helpful tooltips for validation messages
- [ ] Add "What's This?" help links to documentation
```

**File:** `/l10n_cr_einvoice/static/src/css/preview_wizard.css`
```css
# Tasks:
- [ ] Style validation section with Bootstrap alerts
- [ ] Add syntax highlighting for XML (use highlight.js or similar)
- [ ] Responsive design for PDF viewer
- [ ] Print-friendly CSS for PDF preview
```

**Deliverable:** Professional, user-friendly preview interface

---

#### 3:00 PM - 5:00 PM (2h): Comprehensive Testing & Documentation
```bash
# Integration Testing:
- [ ] Test with real Hacienda sandbox credentials
- [ ] Test full flow: Invoice > Preview > Submit > Accept
- [ ] Test error flow: Preview > Find Error > Fix > Preview > Submit
- [ ] Test with different document types (FE, TE, NC)
- [ ] Test with different tax scenarios (13%, 4%, exempt)
- [ ] Performance test: Preview 50 invoices sequentially
```

**Documentation:**
```markdown
# Tasks:
- [ ] Update PHASE5_QUICK_REFERENCE.md with preview workflow
- [ ] Add screenshots to l10n_cr_einvoice/docs/ADMIN_GUIDE.md
- [ ] Create troubleshooting section for common validation errors
- [ ] Document company settings for preview requirement
- [ ] Add developer notes for extending validation rules
```

**Deliverable:** Preview wizard 100% production-ready

---

### Day 2 End-of-Day Deliverables
- ✅ PDF preview fully functional
- ✅ All edge cases handled
- ✅ Production-quality UI/UX
- ✅ Comprehensive testing complete
- ✅ Full documentation with screenshots
- ✅ Ready for beta testing

### Day 2 Risks & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PDF generation too slow | Low | Medium | Use caching, generate async if needed |
| Too many validation rules causing complexity | Medium | Low | Prioritize critical validations, make extensible |
| UI doesn't work on mobile | Low | Low | Test on mobile, use responsive Bootstrap components |

---

## Day 3 (Wednesday) - Void/Cancel Wizard Foundation
**Focus:** Build void/cancel wizard with credit note generation (5 hours work + 2 hours testing + 1 hour buffer)

### Morning Session (4 hours)

#### 9:00 AM - 10:30 AM (1.5h): Wizard Model & UI
**File:** `/l10n_cr_einvoice/wizards/einvoice_void_wizard.py`
```python
# Tasks:
- [ ] Create TransientModel 'l10n_cr.einvoice.void.wizard'
- [ ] Add fields: move_id, reason, void_type (void/cancel/credit_note)
- [ ] Add fields: refund_amount, refund_method (same payment method)
- [ ] Add field: cancel_membership (boolean, if invoice linked to membership)
- [ ] Implement action_void_invoice() method
- [ ] Implement action_create_credit_note() method
```

**File:** `/l10n_cr_einvoice/wizards/einvoice_void_wizard_views.xml`
```xml
# Tasks:
- [ ] Create wizard form with reason dropdown
- [ ] Add void type radio buttons
- [ ] Add refund method selector (if partial refund)
- [ ] Add membership cancellation checkbox (if applicable)
- [ ] Add confirmation message with consequences
- [ ] Add Execute/Cancel buttons
```

**Deliverable:** Basic void wizard opens from invoice

---

#### 10:30 AM - 12:00 PM (1.5h): Credit Note Generation Logic
**File:** `/l10n_cr_einvoice/models/account_move.py` (extend existing)
```python
# Tasks:
- [ ] Add action_void_einvoice() to open wizard
- [ ] Implement _create_credit_note() method
- [ ] Copy invoice lines to credit note (negative amounts)
- [ ] Link credit note to original invoice (reference field)
- [ ] Set document_type = 'NC' for e-invoice
- [ ] Auto-generate and submit credit note e-invoice
```

**File:** `/l10n_cr_einvoice/models/einvoice_document.py`
```python
# Tasks:
- [ ] Add field: reference_document_id (for credit notes)
- [ ] Update XML generation to include reference document data
- [ ] Handle NC (Nota de Crédito) specific XML structure
- [ ] Add validation for credit note amounts
```

**Deliverable:** Credit notes generate correctly with proper e-invoice XML

---

#### 12:00 PM - 1:00 PM: LUNCH BREAK

---

### Afternoon Session (4 hours)

#### 1:00 PM - 2:30 PM (1.5h): Refund Processing
**File:** `/l10n_cr_einvoice/wizards/einvoice_void_wizard.py`
```python
# Tasks:
- [ ] Implement _process_refund() method
- [ ] Support multiple refund methods: cash, SINPE, card reversal
- [ ] Create accounting entries for refund
- [ ] Update payment reconciliation
- [ ] Send refund confirmation email to customer
```

**File:** `/l10n_cr_einvoice/models/account_payment.py` (new or extend)
```python
# Tasks:
- [ ] Add refund_type field (full/partial)
- [ ] Add original_payment_id reference
- [ ] Link refund to credit note
- [ ] Handle SINPE Móvil refund instructions
```

**Deliverable:** Refunds processed correctly with proper accounting

---

#### 2:30 PM - 4:00 PM (1.5h): Membership Cancellation Integration
**File:** `/l10n_cr_einvoice/wizards/einvoice_void_wizard.py`
```python
# Tasks:
- [ ] Check if invoice linked to membership
- [ ] If void + cancel membership: terminate subscription
- [ ] Calculate pro-rated refund if mid-cycle cancellation
- [ ] Send membership cancellation notification
- [ ] Update membership status to 'canceled'
```

**Integration Points:**
```python
# Tasks:
- [ ] Find membership module model (likely 'sale.subscription' or custom)
- [ ] Add _cancel_linked_membership() method
- [ ] Handle recurring payments cancellation
- [ ] Update access control (gym access, portal access)
```

**Deliverable:** Membership cancellations work end-to-end

---

#### 4:00 PM - 5:00 PM (1h): Email Notifications
**File:** `/l10n_cr_einvoice/data/email_templates.xml` (extend existing)
```xml
# Tasks:
- [ ] Create email template for invoice void notification
- [ ] Create email template for credit note notification
- [ ] Create email template for refund confirmation
- [ ] Create email template for membership cancellation
- [ ] Include refund amount, method, timeline in emails
- [ ] Add links to download credit note PDF and XML
```

**File:** `/l10n_cr_einvoice/wizards/einvoice_void_wizard.py`
```python
# Tasks:
- [ ] Implement _send_void_notification() method
- [ ] Attach credit note PDF and XML to email
- [ ] CC accounting team if configured
- [ ] Log email sent in chatter
```

**Deliverable:** Customers receive proper notifications

---

### Day 3 End-of-Day Deliverables
- ✅ Void wizard model and views created
- ✅ Credit note generation working
- ✅ Refund processing implemented
- ✅ Membership cancellation integrated
- ✅ Email notifications sent
- ✅ Basic testing passed

### Day 3 Risks & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Membership module integration breaks | High | High | Create abstraction layer, test without membership first |
| Credit note XML structure incorrect | Medium | High | Use official Hacienda XML samples, validate with XSD |
| Refund accounting entries incorrect | Medium | High | Consult with accountant, test in sandbox environment |

---

## Day 4 (Thursday) - Void/Cancel Wizard Polish & Edge Cases
**Focus:** Production-ready void wizard with all edge cases (5 hours work + 2 hours testing + 1 hour buffer)

### Morning Session (4 hours)

#### 9:00 AM - 10:30 AM (1.5h): Hacienda Integration for Credit Notes
**File:** `/l10n_cr_einvoice/models/einvoice_document.py`
```python
# Tasks:
- [ ] Test credit note submission to Hacienda sandbox
- [ ] Verify reference document data in XML (InformacionReferencia)
- [ ] Add proper CodigoReferencia (01 = Anula documento)
- [ ] Add Razon field (reason for credit note)
- [ ] Validate that amounts match or are less than original
```

**Testing:**
```bash
# Tasks:
- [ ] Submit test invoice to Hacienda sandbox
- [ ] Create credit note for test invoice
- [ ] Submit credit note to Hacienda sandbox
- [ ] Verify Hacienda accepts credit note
- [ ] Check that original invoice shows as voided in Hacienda portal
```

**Deliverable:** Credit notes accepted by Hacienda

---

#### 10:30 AM - 12:00 PM (1.5h): Edge Cases & Validation
```python
# Test scenarios:
- [ ] Void invoice that's already voided (should error)
- [ ] Void invoice that's not yet submitted to Hacienda (should warn)
- [ ] Void invoice that's rejected by Hacienda (should allow)
- [ ] Partial refund with amount > original (should error)
- [ ] Void invoice with payment already reconciled (should handle)
- [ ] Void invoice linked to closed membership (should prevent)
```

**File:** `/l10n_cr_einvoice/wizards/einvoice_void_wizard.py`
```python
# Tasks:
- [ ] Add _validate_can_void() method with all checks
- [ ] Add user-friendly error messages for each scenario
- [ ] Add "Force Void" option for admin users (with audit log)
- [ ] Implement proper permissions (only accounting can void)
```

**Deliverable:** All edge cases handled properly

---

#### 12:00 PM - 1:00 PM: LUNCH BREAK

---

### Afternoon Session (4 hours)

#### 1:00 PM - 2:30 PM (1.5h): Audit Trail & Compliance
**File:** `/l10n_cr_einvoice/models/einvoice_document.py`
```python
# Tasks:
- [ ] Add fields: void_date, void_user_id, void_reason
- [ ] Add field: credit_note_ids (One2many)
- [ ] Add computed field: is_voided
- [ ] Add state transition: accepted -> voided
- [ ] Log all void actions in chatter with reason
```

**File:** `/l10n_cr_einvoice/models/account_move.py`
```python
# Tasks:
- [ ] Add field: l10n_cr_is_voided
- [ ] Add field: l10n_cr_void_date
- [ ] Prevent editing voided invoices
- [ ] Show "VOIDED" banner on invoice form
- [ ] Add void history to invoice (smart button)
```

**Deliverable:** Full audit trail for compliance

---

#### 2:30 PM - 4:00 PM (1.5h): UI/UX Polish
**File:** `/l10n_cr_einvoice/wizards/einvoice_void_wizard_views.xml`
```xml
# UI Improvements:
- [ ] Add confirmation dialog before void (prevent accidents)
- [ ] Show invoice details in wizard (customer, amount, date)
- [ ] Show membership info if linked (member name, plan)
- [ ] Add help text explaining each void option
- [ ] Add visual indicators for refund amounts
- [ ] Show estimated refund processing time
```

**File:** `/l10n_cr_einvoice/views/account_move_views.xml`
```xml
# Tasks:
- [ ] Add "Void Invoice" button (red, with warning icon)
- [ ] Position button appropriately (separate from other actions)
- [ ] Show only when invoice is posted and e-invoice accepted
- [ ] Add "Voided" status bar on voided invoices
```

**Deliverable:** Professional void wizard UI

---

#### 4:00 PM - 5:00 PM (1h): Comprehensive Testing
```bash
# Integration Testing:
- [ ] Full flow: Invoice > Pay > Void > Credit Note > Refund
- [ ] Test with membership: Invoice > Void > Cancel Membership
- [ ] Test partial refund scenario
- [ ] Test void after Hacienda acceptance
- [ ] Test permissions: accountant can void, salesperson cannot
- [ ] Test email notifications delivered correctly
- [ ] Performance: Void 20 invoices and verify all credit notes
```

**Deliverable:** Void wizard fully tested and production-ready

---

### Day 4 End-of-Day Deliverables
- ✅ Hacienda integration for credit notes complete
- ✅ All edge cases handled
- ✅ Audit trail implemented
- ✅ Professional UI/UX
- ✅ Comprehensive testing passed
- ✅ Ready for beta testing

### Day 4 Risks & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Hacienda rejects credit notes | Medium | High | Test extensively in sandbox, follow official examples |
| Permissions too restrictive | Low | Medium | Make configurable, default to accounting only |
| Refund processing takes too long | Low | Low | Make async if needed, show progress indicator |

---

## Day 5 (Friday) - Tax Reports Research & Documentation
**Focus:** Research CR tax forms, create implementation spec, finalize week's work (6 hours work + 2 hours wrap-up)

### Morning Session (4 hours)

#### 9:00 AM - 10:30 AM (1.5h): Official Tax Form Research
**Research Tasks:**
```markdown
# D-104 (Monthly Sales Tax Return)
- [ ] Find official form from Ministerio de Hacienda website
- [ ] Download PDF template and XML schema (if exists)
- [ ] Document all required fields
- [ ] Identify data sources in Odoo (account.move, account.tax)
- [ ] Document calculation formulas
- [ ] Find filing deadlines and penalties

# D-101 (Annual Income Tax Return)
- [ ] Find official form from Ministerio de Hacienda
- [ ] Document required sections
- [ ] Identify data sources (P&L, balance sheet)
- [ ] Document depreciation calculations
- [ ] Find filing deadlines

# D-151 (Withholding Tax Return)
- [ ] Find official form
- [ ] Document withholding scenarios
- [ ] Identify data sources
- [ ] Find filing deadlines
```

**Deliverable:** Complete understanding of all 3 forms

---

#### 10:30 AM - 12:00 PM (1.5h): Data Mapping & Requirements
**File:** `/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/CR-TAX-REPORTS-IMPLEMENTATION-SPEC.md`
```markdown
# Document Structure:
- [ ] Executive Summary
- [ ] D-104 Data Mapping (which Odoo fields map to form fields)
- [ ] D-101 Data Mapping
- [ ] D-151 Data Mapping
- [ ] Required Odoo Modules (account_reports, l10n_cr_einvoice)
- [ ] Database Schema Changes (if any)
- [ ] Calculation Logic (tax totals, withholdings, etc.)
- [ ] Export Formats (PDF, XML, Excel)
- [ ] Filing Integration (API vs manual download)
- [ ] Estimated Implementation Time (Week 2 roadmap)
```

**Research Sources:**
- Ministerio de Hacienda Costa Rica website
- Odoo l10n_es_reports, l10n_mx_reports as reference
- Costa Rica tax accountant forums
- Competitor analysis (FacturaTica, TicoPay tax reports)

**Deliverable:** Complete implementation spec document

---

#### 12:00 PM - 1:00 PM: LUNCH BREAK

---

### Afternoon Session (4 hours)

#### 1:00 PM - 2:30 PM (1.5h): Week 2 Roadmap Planning
**File:** `/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/WEEK-2-TAX-REPORTS-ROADMAP.md`
```markdown
# Week 2 Plan (to be refined):

## Monday-Tuesday: D-104 Implementation
- Create report model and wizard
- Implement calculation logic
- Generate PDF export
- Test with sample data

## Wednesday: D-101 Implementation
- Create annual report structure
- Implement P&L integration
- Generate PDF export

## Thursday: D-151 Implementation
- Create withholding report
- Implement vendor payment tracking
- Generate PDF export

## Friday: Testing & Polish
- Integration testing all 3 reports
- User acceptance testing
- Documentation
- Deployment
```

**Deliverable:** Clear roadmap for Week 2

---

#### 2:30 PM - 4:00 PM (1.5h): Week 1 Final Testing & Bug Fixes
```bash
# Comprehensive Testing:
- [ ] Preview Wizard: Test all validation scenarios again
- [ ] Preview Wizard: Test with 10 different invoices
- [ ] Void Wizard: Test all void scenarios again
- [ ] Void Wizard: Test membership integration
- [ ] Integration: Preview > Submit > Void flow
- [ ] Performance: Generate 50 previews, void 20 invoices
- [ ] UI/UX: Test on mobile devices
- [ ] Accessibility: Test keyboard navigation, screen reader
```

**Bug Fixes:**
- [ ] Fix any bugs found during testing
- [ ] Polish UI issues
- [ ] Improve error messages
- [ ] Optimize slow queries

**Deliverable:** All Week 1 features bug-free

---

#### 4:00 PM - 5:00 PM (1h): Documentation & Handoff to Beta
**Documentation Tasks:**
```markdown
# Update Documentation:
- [ ] PHASE5_QUICK_REFERENCE.md - Add preview & void workflows
- [ ] l10n_cr_einvoice/docs/ADMIN_GUIDE.md - Add screenshots
- [ ] l10n_cr_einvoice/docs/USER_GUIDE.md - Step-by-step guides
- [ ] WEEK-1-IMPLEMENTATION-SUMMARY.md - What was delivered
- [ ] CR-TAX-REPORTS-IMPLEMENTATION-SPEC.md - Research findings
```

**Beta Testing Checklist:**
```markdown
# Create WEEK-1-BETA-TESTING-GUIDE.md:
- [ ] Preview Wizard test scenarios (10 scenarios)
- [ ] Void Wizard test scenarios (8 scenarios)
- [ ] Expected results for each scenario
- [ ] Bug reporting template
- [ ] Feedback collection form
```

**Git Commit:**
```bash
git add .
git commit -m "Week 1 Critical Blockers: Preview & Void Wizards Complete

- Implemented e-invoice preview wizard with PDF/XML preview
- Implemented validation system with error/warning/info levels
- Implemented void/cancel wizard with credit note generation
- Integrated refund processing and membership cancellation
- Added comprehensive email notifications
- Created audit trail for compliance
- Researched Costa Rica tax reports (D-104, D-101, D-151)
- Created implementation spec for Week 2

Tested: All scenarios passing
Ready for: Beta testing"

git push origin main
```

**Deliverable:** Week 1 complete, documented, ready for beta

---

### Day 5 End-of-Day Deliverables
- ✅ CR tax reports researched (D-104, D-101, D-151)
- ✅ Implementation spec created for Week 2
- ✅ Week 2 roadmap planned
- ✅ All Week 1 features tested and bug-free
- ✅ Documentation complete
- ✅ Beta testing guide created
- ✅ Code committed and pushed

---

## Dependencies Matrix

### Day 1 → Day 2
**Dependency:** Preview wizard foundation must work before adding PDF preview
**Mitigation:** Day 1 must deliver working XML preview minimum

### Day 2 → Day 3
**No hard dependency** - Void wizard independent of preview wizard
**Soft dependency:** Both wizards share similar UI patterns (copy code)

### Day 3 → Day 4
**Dependency:** Credit note generation must work before Hacienda integration
**Mitigation:** Day 3 must deliver working credit note creation

### Day 4 → Day 5
**No dependency** - Tax research independent of void wizard
**Benefit:** Can start tax research in parallel if ahead of schedule

---

## Testing Schedule

### Daily Testing (Last hour each day)
- **Manual testing:** Core functionality works
- **Regression testing:** Previous features still work
- **Documentation testing:** Docs match implementation

### Integration Testing Checkpoints
- **Day 2 End:** Preview → Submit full flow
- **Day 4 End:** Submit → Void → Credit Note full flow
- **Day 5 End:** All features together (preview, submit, void)

### Performance Testing
- **Day 2:** Preview 50 invoices (should complete in < 5 seconds each)
- **Day 4:** Void 20 invoices (should complete in < 10 seconds each)

### User Acceptance Testing
- **Day 5 Afternoon:** Simulate real user workflows
- **Criteria:** Non-technical user can complete tasks without help

---

## Risk Mitigation Strategies

### If Preview Wizard Takes Too Long (Day 1-2)
**Plan B:** Ship minimum viable preview (XML only, no PDF)
**Adjustment:** Move PDF preview to Week 2, prioritize void wizard

### If Hacienda Integration Fails (Day 4)
**Plan B:** Credit notes work locally, Hacienda integration debugged Week 2
**Adjustment:** Deliver void wizard with manual Hacienda submission

### If Membership Integration Breaks (Day 3-4)
**Plan B:** Void wizard works without membership integration
**Adjustment:** Add membership cancellation as Week 2 enhancement

### If Tax Research Incomplete (Day 5)
**Plan B:** Partial research, continue Week 2 Monday morning
**Adjustment:** Week 2 starts Tuesday instead of Monday

---

## Buffer Time Allocation (8 hours total)

### Scheduled Buffer
- **Day 1:** 1 hour (testing overflow)
- **Day 2:** 1 hour (polish overflow)
- **Day 3:** 1 hour (testing overflow)
- **Day 4:** 1 hour (Hacienda integration debugging)
- **Day 5:** 2 hours (tax research overflow)

### Emergency Buffer (2 hours)
- **Unscheduled issues:** Critical bugs, blocking dependencies
- **If unused:** Use for Week 2 prep or early start on D-104

---

## Success Criteria (Friday 5pm Checklist)

### Preview Wizard
- [ ] Users can preview XML before submission
- [ ] Users can preview PDF before submission
- [ ] Validation shows errors, warnings, info
- [ ] Preview integrates with submit workflow
- [ ] Works with all document types (FE, TE, NC)
- [ ] Tested with 20+ invoices
- [ ] Documented with screenshots

### Void Wizard
- [ ] Users can void invoices
- [ ] Credit notes generate automatically
- [ ] Credit notes submit to Hacienda successfully
- [ ] Refunds process correctly
- [ ] Membership cancellation works (if applicable)
- [ ] Email notifications sent
- [ ] Audit trail complete
- [ ] Tested with 15+ void scenarios
- [ ] Documented with screenshots

### Tax Reports Research
- [ ] D-104 form documented
- [ ] D-101 form documented
- [ ] D-151 form documented
- [ ] Data mapping complete
- [ ] Implementation spec created
- [ ] Week 2 roadmap defined

### Production Readiness
- [ ] All features work in Hacienda sandbox
- [ ] No critical bugs
- [ ] Performance acceptable (< 10 sec per operation)
- [ ] Documentation complete
- [ ] Beta testing guide ready
- [ ] Code committed and pushed

---

## Communication Plan

### Daily Standup (Self-Check)
**Time:** 9:00 AM each day
**Questions:**
1. What did I complete yesterday?
2. What am I working on today?
3. Any blockers or risks?

### End-of-Day Summary
**Time:** 5:00 PM each day
**Deliverable:** Update this document with actual progress
**Format:**
```markdown
## Day X Actual Results
- Completed: [list tasks]
- Delayed: [list tasks with reason]
- Blockers: [list issues]
- Tomorrow's priority: [adjusted plan]
```

### Friday Stakeholder Demo
**Time:** 4:30 PM Friday
**Audience:** Beta testers, stakeholders
**Agenda:**
1. Preview wizard demo (5 min)
2. Void wizard demo (5 min)
3. Tax reports research findings (5 min)
4. Week 2 roadmap preview (5 min)
5. Q&A and feedback (10 min)

---

## Appendix: File Manifest

### New Files Created (Week 1)
```
l10n_cr_einvoice/wizards/
  ├── einvoice_preview_wizard.py
  ├── einvoice_preview_wizard_views.xml
  ├── einvoice_void_wizard.py
  └── einvoice_void_wizard_views.xml

l10n_cr_einvoice/static/src/css/
  └── preview_wizard.css

l10n_cr_einvoice/static/src/js/
  └── preview_wizard.js (if needed for XML highlighting)

docs/
  ├── WEEK-1-IMPLEMENTATION-SUMMARY.md
  ├── CR-TAX-REPORTS-IMPLEMENTATION-SPEC.md
  ├── WEEK-2-TAX-REPORTS-ROADMAP.md
  └── WEEK-1-BETA-TESTING-GUIDE.md
```

### Files Modified (Week 1)
```
l10n_cr_einvoice/models/
  ├── account_move.py (add preview & void actions)
  ├── einvoice_document.py (add credit note support)
  └── __init__.py (register new models)

l10n_cr_einvoice/views/
  └── account_move_views.xml (add buttons)

l10n_cr_einvoice/data/
  └── email_templates.xml (add void notifications)

l10n_cr_einvoice/security/
  └── ir.model.access.csv (add wizard permissions)

l10n_cr_einvoice/
  ├── __manifest__.py (increment version, add dependencies)
  └── PHASE5_QUICK_REFERENCE.md (update user guide)
```

---

## Lessons Learned (To be updated Friday)

### What Went Well
- [To be filled Friday EOD]

### What Could Be Improved
- [To be filled Friday EOD]

### Adjustments for Week 2
- [To be filled Friday EOD]

---

**Plan Owner:** Solo Developer
**Plan Created:** 2025-12-31
**Plan Status:** ACTIVE
**Next Review:** Daily at 9:00 AM
**Completion Target:** Friday 2025-01-XX 5:00 PM
