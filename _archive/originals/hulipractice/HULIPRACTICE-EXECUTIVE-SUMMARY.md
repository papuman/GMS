# HuliPractice Intelligence - Executive Summary

**Date:** December 31, 2025
**Analysis:** Comprehensive forensic capture of app.hulipractice.com
**Verdict:** 🎯 **You're 80-90% feature complete - but 3 CRITICAL gaps must be fixed**

---

## 30-Second Summary

HuliPractice (medical practice management for Costa Rica) uses a **separate microservice called "Lucida"** for billing/e-invoicing. After capturing 458 network requests, 35 API endpoints, and 184 screenshots, we've identified:

✅ **What you're doing better:**
- Offline POS mode (they don't have this)
- Transparent pricing
- Integrated platform (membership + billing + POS)

⚠️ **CRITICAL gaps to fix immediately:**
1. **Invoice void/cancellation workflow** (BLOCKING for v1.0)
2. **Preview before Hacienda submission** (prevents errors)
3. **Costa Rica tax reports** (D-104, D-101, D-151 for Hacienda filing)

---

## What is HuliPractice?

**Medical practice management system** for Costa Rica with:
- Main app: app.hulipractice.com (EHR/patient records)
- **Billing module: finanzas.hulipractice.com ("Lucida")** ← This is what we analyzed

### Key Stats from Captured Demo Account
- 33 invoices (Facturas, Tiquetes, Notas de Crédito)
- 4 customers
- 4 products/services
- 5 document types
- 9 payment methods (including SINPE Móvil)

---

## Architecture: Microservice vs Integrated

### HuliPractice (Lucida)
```
Main App (app.hulipractice.com)
    └── SSO Auth Token
        └── Billing Microservice (finanzas.hulipractice.com)
            - Separate domain
            - Own API (v1, v3)
            - Own database
            - Can be sold independently
```

### Your Module (l10n_cr_einvoice)
```
Odoo 19 Enterprise
    └── l10n_cr_einvoice Module
        - Integrated module
        - Extends account.move, pos.order
        - Single database
        - Odoo ecosystem
```

**Question:** Should you extract e-invoicing as a microservice?
- **Phase 1 (now):** NO - integrated is faster
- **Phase 2 (month 4-6):** MAYBE - if selling to non-gym customers
- **Phase 3:** YES - if offering "e-invoicing only" to gyms with other software

---

## Feature Comparison Matrix

| Feature | HuliPractice | Your Module | Status |
|---------|--------------|-------------|--------|
| **Factura (Invoice)** | ✅ | ✅ | ✅ PARITY |
| **Tiquete Electrónico (TE)** | ✅ | ✅ Phase 5 | ✅ PARITY |
| **Nota de Crédito** | ✅ | ✅ | ✅ PARITY |
| **Nota de Débito** | ✅ (UI only) | ⚠️ Missing | ⚠️ GAP (Low priority) |
| **Void/Cancel Invoice** | ✅ "Anular documento" | ❌ **MISSING** | 🔴 **CRITICAL GAP** |
| **Preview Before Submit** | ✅ "Previsualizar" | ❌ **MISSING** | 🔴 **CRITICAL GAP** |
| **Clone Invoice** | ✅ "Clonar" | ❌ Missing | 🟡 HIGH VALUE |
| **Payment Tracking** | ✅ | ✅ | ✅ PARITY |
| **SINPE Móvil** | ✅ | ✅ | ✅ PARITY |
| **Split Payments** | ⚠️ Unknown | ✅ POS | ✅ **YOUR ADVANTAGE** |
| **Offline Mode** | ❌ (Iframe-based) | ✅ Phase 5 | ✅ **YOUR ADVANTAGE** |
| **CR Tax Reports (D-104, D-101, D-151)** | ✅ | ❌ **MISSING** | 🔴 **CRITICAL GAP** |
| **Document Tags** | ✅ | ❌ Missing | 🟡 NICE-TO-HAVE |
| **Advanced Filters** | ✅ Sidebar | ⚠️ Odoo default | 🟡 UX IMPROVEMENT |
| **Proforma/Quotes** | ✅ Separate section | ⚠️ Missing | 🟡 SALES TOOL |

---

## 🔴 CRITICAL: Must Fix Before v1.0 Launch

### 1. Invoice Void/Cancellation Workflow

**What HuliPractice Does:**
- "Anular documento" action on every invoice
- Creates matching Nota de Crédito
- Marks original as void

**Why Critical:**
- Gyms WILL make mistakes (wrong amounts, wrong customer)
- Gyms WILL have member cancellations requiring refunds
- **Without this, you're not production-ready**

**Implementation:**
```python
# Add to l10n_cr.einvoice.document
def action_void_invoice(self):
    """
    Void accepted e-invoice:
    1. Create matching Nota de Crédito
    2. Submit to Hacienda
    3. Mark original as void
    """
    credit_note = self.create_credit_note()
    credit_note.submit_to_hacienda()
    self.state = 'void'
```

**Timeline:** Week 1 (HIGHEST PRIORITY)

---

### 2. Preview Before Hacienda Submission

**What HuliPractice Does:**
- "Previsualizar" button before final submission
- Shows PDF preview
- Reviews customer data, amounts, tax
- [Cancel] or [Submit to Hacienda]

**Why Critical:**
- **Prevents costly errors** (rejected invoices, wrong amounts)
- **Professional UX** (confidence before submission)
- **Reduces Hacienda rejections**

**Implementation:**
```xml
<!-- Add wizard before submission -->
<record id="view_einvoice_preview_wizard" model="ir.ui.view">
    <field name="name">Preview E-Invoice Before Submission</field>
    <field name="model">l10n_cr.einvoice.preview.wizard</field>
    <field name="arch" type="xml">
        <form>
            <group>
                <field name="pdf_preview" widget="pdf_viewer"/>
                <field name="customer_name" readonly="1"/>
                <field name="total_amount" readonly="1"/>
                <field name="tax_amount" readonly="1"/>
            </group>
            <footer>
                <button string="Cancel" special="cancel"/>
                <button string="Submit to Hacienda" type="object"
                        name="action_confirm_submit" class="btn-primary"/>
            </footer>
        </form>
    </field>
</record>
```

**Timeline:** Week 1 (HIGH PRIORITY)

---

### 3. Costa Rica Tax Reports (Hacienda Filing)

**What HuliPractice Has:**
Under "Reportes > Hacienda" menu:
1. **IVA D-104** - VAT report (quarterly/annual)
2. **Renta D-101** - Income tax report (annual)
3. **Hacienda D-151** - Tax authority report

**Why Critical:**
- Gyms must file these with Hacienda
- Accountants will demand these reports
- **Without them, GMS is incomplete for tax compliance**

**Next Steps:**
1. **Research** Hacienda D-104, D-101, D-151 formats (Week 1)
2. **Design** Odoo report templates (Week 2)
3. **Implement** using einvoice data (Week 3-4)
4. **Test** with sample data (Week 4)

**Timeline:** Week 1-4 (Research → Implementation)

---

## 🟡 HIGH VALUE: Implement in Month 1

### 4. Clone Invoice Function

**Use Case:** Recurring monthly membership fees

**Implementation:**
```python
def action_clone_invoice(self):
    """Clone invoice with new date"""
    new_invoice = self.copy({
        'date': fields.Date.today(),
        'hacienda_state': 'draft',
        'clave': False,
    })
    return new_invoice.open_form_view()
```

**Timeline:** Week 2

---

### 5. Document Tags System

**Use Case:** Organize invoices by campaign, member type, promotion

**HuliPractice:** Tag feature exists but unused in demo

**Implementation:**
```python
class EinvoiceTag(models.Model):
    _name = 'l10n_cr.einvoice.tag'
    name = fields.Char(required=True)
    color = fields.Integer('Color')

# Add to einvoice_document
tag_ids = fields.Many2many('l10n_cr.einvoice.tag')
```

**Timeline:** Week 2-3

---

### 6. Advanced Filter UI

**What HuliPractice Has:**
- Filter sidebar with checkboxes
- Multi-select document types
- Payment status toggles (Pending/Paid)
- Visual status badges (green ✓, red ✗)

**Implementation:**
```xml
<searchpanel>
    <field name="document_type" select="multi" icon="fa-file-text"/>
    <field name="payment_status" select="multi" icon="fa-money"/>
    <field name="hacienda_status" select="multi" icon="fa-check-circle"/>
</searchpanel>
```

**Timeline:** Week 3

---

## ✅ Your Competitive Advantages

### 1. Offline POS Mode (MAJOR)

**HuliPractice:** Appears to be online-only (iframe-based, no offline mode observed)

**Your Module:**
- ✅ Offline queue with retry
- ✅ 🟢 Online / 🔴 Offline indicator
- ✅ Auto-sync every 5 minutes
- ✅ Exponential backoff retry

**This is a HUGE advantage for gyms** (unreliable internet, rural areas)

---

### 2. Transparent Pricing

**HuliPractice:** No pricing page captured (likely quote-based)

**Your Model:**
- ✅ Public tier pricing
- ✅ ₡28,000 - ₡89,600/month
- ✅ 30-day free trial
- ✅ Self-service signup

**This removes sales friction** for independent gyms

---

### 3. Integrated Platform

**HuliPractice:** Medical EHR + Billing (2 separate concerns)

**Your Platform:**
- ✅ Membership management
- ✅ Billing & invoicing
- ✅ POS integration
- ✅ CRM for leads
- ✅ All in one Odoo instance

**Single source of truth** vs. fragmented systems

---

## API Intelligence Highlights

### HuliPractice API Patterns

**35 unique endpoints captured:**

```
GET  /api/lucida/v1/org/{org_id}/billing/docs-v2
GET  /api/lucida/v1/org/{org_id}/resource/batch
POST /api/lucida/v1/org/{org_id}/perms/validate
GET  /api/lucida/partner/huli/auth/{token}
```

**Key Learnings:**
1. **API versioning** (v1, v3) - allows breaking changes
2. **Organization-scoped URLs** - multi-tenant friendly
3. **Batch operations** - performance optimization
4. **SSO authentication** - token-based inter-service auth

**Recommendation:**
If you add custom APIs (beyond Odoo RPC), adopt these patterns:
```
/api/v1/company/{company_id}/einvoice/submit
/api/v1/company/{company_id}/einvoice/batch
```

---

## Implementation Roadmap

### Week 1 (CRITICAL)
- [ ] **Invoice void/cancel workflow** (blocking issue)
- [ ] **Preview before submission** (error prevention)
- [ ] **Research CR tax reports** (D-104, D-101, D-151 formats)

### Week 2 (HIGH VALUE)
- [ ] **Clone invoice action** (recurring memberships)
- [ ] **Document tags system** (organization)

### Week 3 (UX IMPROVEMENTS)
- [ ] **Advanced filter UI** (search panel)
- [ ] **Visual status badges** (colored icons)

### Week 4 (TAX COMPLIANCE)
- [ ] **Implement D-104 report** (VAT)
- [ ] **Implement D-101 report** (Income tax)
- [ ] **Implement D-151 report** (Hacienda)

### Month 2 (NICE-TO-HAVE)
- [ ] **Proforma/quote workflow** (sales tool)
- [ ] **Payment history UI enhancement**
- [ ] **Nota de Débito support** (late fees)

---

## Cost-Benefit Analysis

### Time Investment
- **Week 1 critical fixes:** ~20 hours
- **Week 2-4 enhancements:** ~30 hours
- **Total:** ~50 hours for feature parity

### Impact
- **Prevents launch blockers** (void/cancel)
- **Reduces support burden** (preview, better UX)
- **Enables accountant adoption** (tax reports)
- **Improves sales conversion** (clone for demos)

### ROI
- **50 hours** to reach 95% feature parity
- Prevents losing customers to competitors
- Enables v1.0 production launch

**Verdict:** **WORTH IT** - These are must-haves, not nice-to-haves

---

## Questions for Further Research

### About HuliPractice

1. **Pricing model?** (per practice, per doctor, per invoice?)
2. **Customer count?** (market penetration)
3. **Implementation time?** (onboarding process)
4. **Purchase module?** (how it works when populated)
5. **API authentication details?** (token lifetime, refresh)

### How to Get Answers

**Option 1:** Sign up for HuliPractice demo/trial
- Test platform end-to-end
- Document pricing
- Experience onboarding

**Option 2:** Interview their customers
- Find medical practices using it
- Ask about pros/cons
- Understand pain points

**Option 3:** Deeper forensic capture
- Create test invoice end-to-end
- Capture complete workflow
- Document API request/response bodies

---

## Final Verdict

### You're in Great Shape (80-90% Complete)

**✅ What's Working:**
- Core e-invoicing compliance (Factura, TE, Credit Notes)
- Hacienda integration (submit, poll, retry)
- Offline POS mode (better than HuliPractice)
- Payment tracking
- SINPE Móvil support
- PDF & email automation

**⚠️ Must Fix (Week 1):**
1. Invoice void/cancel
2. Preview before submit
3. CR tax reports research

**🟡 High Value (Month 1):**
4. Clone invoice
5. Document tags
6. Advanced filters
7. CR tax reports implementation

**🟢 Nice-to-Have (Month 2+):**
8. Proforma/quotes
9. Payment history UI
10. Nota de Débito

### Next Actions

**Today:**
1. ✅ Read this analysis
2. ✅ Prioritize Week 1 tasks
3. ✅ Create user stories for void/cancel workflow

**This Week:**
4. Implement invoice void/cancel
5. Add preview wizard
6. Research Hacienda D-104, D-101, D-151 formats

**This Month:**
7. Complete all HIGH VALUE items
8. Test with beta gym customers
9. Prepare v1.0 launch

---

## Summary in 3 Bullets

1. **You're 80-90% feature complete** vs. HuliPractice's billing module
2. **Fix 3 CRITICAL gaps in Week 1:** void/cancel, preview, tax reports research
3. **Your offline POS is superior** - lean into this competitive advantage

---

**Intelligence Gathered:** 458 network requests, 35 API endpoints, 184 screenshots
**Analysis Date:** December 31, 2025
**Confidence:** HIGH (comprehensive capture with manual navigation)

**Full Report:** HULIPRACTICE-COMPETITIVE-ANALYSIS.md

---

**YOU'RE ALMOST THERE. FIX THE 3 CRITICAL GAPS AND YOU'RE PRODUCTION-READY.** 🚀
