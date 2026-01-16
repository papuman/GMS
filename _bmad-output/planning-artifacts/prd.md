---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - docs/market-costa-rica-einvoicing-payment-research-2025-12-28.md
  - docs/GMS_FEATURE_LIST_COMPLETE.md
  - docs/USER_RESEARCH_GYM_OWNERS_2025.md
  - docs/USER_RESEARCH_EXECUTIVE_SUMMARY.md
  - docs/MODULE_CLONING_QUICK_REFERENCE.md
  - docs/architecture.md
  - docs/project-overview.md
  - docs/UX_AUDIT_EXECUTIVE_SUMMARY.md
  - _bmad-output/analysis/brainstorming-session-2025-12-29.md
  - COSTA-RICA-GYM-MARKET-RESEARCH-2025.md
workflowType: 'prd'
lastStep: 3
documentCounts:
  briefCount: 0
  researchCount: 4
  brainstormingCount: 1
  projectDocsCount: 5
---

# Product Requirements Document - GMS

**Author:** User
**Date:** 2025-12-29

---

## Executive Summary

### Vision

GMS transforms Odoo 19 Enterprise into Costa Rica's first gym management platform purpose-built for local compliance and payment realities. By addressing the urgent e-invoicing v4.4 deadline (September 2025) and seamlessly integrating payment gateways (Tilopay) for SINPE Móvil automation, GMS solves the compliance crisis while delivering modern, gym-specific workflows that hide Odoo's technical complexity.

The platform operates as a multi-tenant SaaS where gym customers receive tailored GMS modules while the infrastructure can serve vanilla Odoo customers, maximizing platform leverage.

### The Costa Rica Gym Market Reality

**Market Size:**
- **450-500 total gyms** in Costa Rica (2024-2025)
- **220 gyms in San José** (44% of market, primary target)
- **5-10% annual growth** (25-50 new gyms per year)
- **300-400 underserved gyms** (independent + boutique studios)

**Target Market Segmentation:**
1. **Independent Micro-Gyms (40-50% of market)**: 200-250 gyms, 50-200 members each
2. **Boutique Studios (20-25% of market)**: 100-150 gyms, CrossFit/Yoga/Pilates/HIIT
3. **Small Chains (12-15% of market)**: 30-50 operators with 2-5 locations
4. **Large Chains (10-15% of market)**: 8-15 operators with 6+ locations

### The Problem (Costa Rica-Specific)

**1. E-Invoicing Compliance Crisis** ⚠️ **URGENT**
- Mandatory deadline: **September 1, 2025** (6-9 month window)
- Hacienda v4.4 required (v4.3 deprecated)
- Penalties: **₡8.3M+ ($14,800+)** or 2% of gross revenue
- Most gyms unprepared, especially independents

**2. Payment Collection & Reconciliation Gap**
- **76% of Costa Ricans use SINPE Móvil** (primary payment method)
- Gyms manually record SINPE payments via WhatsApp screenshots
- No automatic reconciliation = cash flow blindness
- **Current gym software lacks payment gateway integration**

**3. No Transparent, Affordable Options**
- **LatinsoftCR**: Quote-based pricing, targets large chains only
- **CrossHero, ProGym**: No CR compliance, no local payment integration
- **International platforms**: No Hacienda integration, no CRC pricing
- **Result**: 250-300 independent gyms use Excel spreadsheets

**4. Manual Administrative Burden**
- Chasing late payments
- Hours spent on billing cycles
- Class booking chaos (WhatsApp overwhelm)

### The Solution

**GMS: Costa Rica's First Compliance-Native Gym Platform**

**Core Value Proposition:**
> "Get Hacienda-compliant in 24 hours. Automate payments through Tilopay. Focus on your members, not paperwork."

**Critical Features (Costa Rica-Specific):**

**1. Hacienda E-Invoice v4.4 Compliance** (Regulatory Moat)
- One-click compliant invoicing
- Automatic XML v4.4 generation + DGT submission
- Digital signature management
- 5-year archival compliance
- **Competitive Advantage**: 6-12 month head start

**2. Integrated Payment Processing via Tilopay** (Automation)
- **SINPE Móvil**: Semi-automatic payment reconciliation via redirect-based TiloPay integration
- **Credit/Debit Cards**: Full payment gateway integration
- **Automatic E-Invoicing**: Payment received → Invoice generated → Hacienda submitted
- **Member Portal**: One-click payment links
- **Competitive Advantage**: Only gym software with integrated gateway + compliance + management

**Technical Architecture:**
```
Member Payment (SINPE/Card)
  → Tilopay Gateway
  → Redirect Return to GMS
  → Auto-Generate E-Invoice
  → Submit to Hacienda
  → Update Member Account
```

**3. Transparent CRC Pricing** (Trust Builder)
- Public tiered pricing: ₡28,000 - ₡89,600/month
- Self-service signup
- 30-day free trial (no credit card)
- **Competitive Advantage**: No quote-based sales friction

**4. Opt-In Communication Tools** (Legal Compliance)
- Email automation (payment reminders, renewals)
- SMS via local providers (with opt-in)
- WhatsApp click-to-chat (member-initiated)
- In-app push notifications (member app)
- **Note**: Automated WhatsApp requires explicit consent framework (Phase 2)

**5. Gym-Specific UX** (Usability)
- Hide Odoo complexity (8 states → 3 user states)
- Spanish-first interface
- Mobile-responsive design
- Video tutorials in Spanish

**Technical Foundation:**
- Odoo 19 Enterprise base (~60-70% of functionality)
- Module inheritance (extends POS, CRM, Sales, Accounting, Membership)
- Multi-tenant SaaS model

### What Makes This Special (Costa Rica Context)

**1. Integrated Solution** (vs. Fragmented Tools)

Current market: Gyms use separate systems:
- Payment gateway (Tilopay standalone)
- E-invoicing (separate tool or manual)
- Gym management (LatinsoftCR or spreadsheets)

**GMS**: All in ONE platform = time savings + seamless workflow

**2. Regulatory Compliance Ready**
- September 2025 deadline creates urgency
- Penalties ($14,800+) motivate immediate action
- 6-9 month window before competitors catch up

**3. Underserved Market Segment**
- 250-300 independent gyms have no viable option
- LatinsoftCR too expensive for small gyms
- International platforms lack CR compliance

**4. Speed to Market**
- Odoo foundation = 60-70% feature coverage
- Module inheritance = faster than from scratch
- Can launch MVP in 6-day sprint cycles

### Competitive Positioning

| Feature | GMS (Ours) | LatinsoftCR | CrossHero | International |
|---------|------------|-------------|-----------|---------------|
| **Payment Gateway Integration** | ✅ Tilopay (SINPE + Cards) | ❓ Research needed | ❓ Research needed | ⚠️ Stripe (no SINPE) |
| **E-Invoice v4.4 Compliance** | ✅ Built-in | ⚠️ v4.3 (needs update) | ❌ No CR support | ❌ No CR support |
| **Integrated Solution** | ✅ Payment + Invoice + Mgmt | ❌ Separate systems | ❌ Separate systems | ❌ Separate systems |
| **Transparent CRC Pricing** | ✅ Public tiers | ❌ Quote only | ❌ Quote only | ⚠️ USD only |
| **Self-Service Onboarding** | ✅ 24-hour setup | ❌ Sales required | ⚠️ Manual | ✅ Yes |
| **Free Trial** | ✅ 30 days | ❌ No | ⚠️ Limited | ✅ Varies |

**Competitive Moats:**
1. **Regulatory Compliance**: Deep Hacienda v4.4 integration
2. **Integrated Payment + Invoicing**: Single workflow vs. fragmented tools
3. **Compliance Switching Costs**: Once migrated, difficult to leave
4. **Transparent Pricing**: Trust builder in opaque market

**Note**: Tilopay integration is not unique (anyone can integrate), but **combining** Tilopay + E-Invoice + Gym Management in one platform IS unique.

### Target Market & Revenue Model

**Phase 1 (Months 1-6): San José Independent Gyms**
- **Segment**: 150-200 independent gyms
- **Goal**: 30-50 customers
- **Pricing**: ₡28,000-50,400/month
- **Revenue Target**: ₡1.75M MRR (~$31k ARR)

**Pricing Tiers (CRC):**

| Tier | Monthly | Annual (20% off) | Members |
|------|---------|------------------|---------|
| **Starter** | ₡28,000 ($50) | ₡268,800 ($480) | Up to 100 |
| **Professional** | ₡50,400 ($90) | ₡483,840 ($864) | Up to 250 |
| **Business** | ₡89,600 ($160) | ₡860,160 ($1,536) | Up to 500 |
| **Enterprise** | Custom | Custom | Unlimited |

**Transaction Fees:**
- Tilopay charges estimated 2-3% per transaction
- **Decision Point**: Pass through to gyms or absorb into pricing?
- **Research Required**: Exact Tilopay pricing structure

### Critical Dependencies & Risks

**Technical Dependencies:**
- ✅ Odoo 19 Enterprise license
- ⚠️ Tilopay partnership & API access (CRITICAL)
- ⚠️ Hacienda API rate limits & SLA
- ⚠️ Alternative gateway options (BAC Credomatic backup)

**Legal/Compliance Dependencies:**
- ⚠️ Ley 8968 (Data Protection) compliance research
- ⚠️ Payment processing regulations (BCCR)
- ⚠️ Multi-tenant data isolation requirements
- ⚠️ Electronic communications laws

**Market Risks:**
- Tilopay already integrated by LatinsoftCR (need to verify)
- E-invoicing deadline extended (reduces urgency)
- Economic recession impacts gym software spending

### Expected Outcomes (Year 1)

**Quantitative:**
- 50-100 paying customers (10-20% of target market)
- ₡2M-4M MRR ($36k-72k USD ARR)
- <10% churn rate
- LTV:CAC ratio: 6-12x (needs validation)

**Qualitative:**
- Gyms avoid ₡8.3M+ compliance penalties
- 5-10 hours/week admin time savings
- Improved cash flow visibility
- Modern member experience

## Project Classification

**Technical Type:** SaaS B2B (Multi-tenant platform)
**Platform Base:** Odoo 19 Enterprise (unchanged core)
**Extension Layer:** GMS modules (gym-specific features)
**Primary Market:** Costa Rica (450-500 gyms)
**Domain:** Fitness & Wellness vertical
**Complexity:** Medium-High (multi-tenancy + module inheritance + regulatory compliance)
**Project Context:** Brownfield - extending existing Odoo framework

### Deployment Model

GMS is deployed as optional modules on a multi-tenant Odoo platform:

**Tenant Configuration:**
- **Gym tenants**: GMS modules installed → Gym-specific UI, workflows, compliance features
- **Non-gym tenants**: Standard Odoo (GMS modules not installed)
- **Activation mechanism**: Business type selection at tenant creation determines module installation

**Technical Benefits:**
- Shared infrastructure (hosting, multi-tenancy, DevOps)
- Focused product development (gym features only in GMS scope)
- Platform flexibility (serve multiple business types)
- Upgrade safety (no core Odoo modifications)

**Out of Scope** (infrastructure layer handles):
- Multi-tenant database architecture
- Tenant provisioning system
- Business type selection interface
- Module installation automation

---

## Success Criteria

### User Success (Gym Owner Success)

**The MVP "Aha!" Moments:**

1. **Compliance Relief** - Gym owner submits their first v4.4 e-invoice successfully and realizes "I'm not going to get fined ₡8.3M+"
2. **Simplicity** - "That was way easier than the old manual XML process"
3. **Speed** - "I just invoiced 20 members in 30 minutes instead of 4 hours"

**Measurable MVP User Success:**
- ✅ **Setup Speed**: Complete Hacienda setup in <2 hours
- ✅ **Invoice Success**: >95% Hacienda acceptance rate on first submission
- ✅ **Processing Speed**: Create invoice → Hacienda approval in <5 minutes
- ✅ **Learning Curve**: Process first invoice within 30 minutes of setup
- ✅ **Self-Service**: <2 support tickets per gym in first month

**Post-MVP (with Tilopay - Phase 1):**
- ✅ **Payment Automation**: SINPE payment → invoice → Hacienda in <5 minutes (automated)
- ✅ **Billing Efficiency**: Monthly recurring billing runs automatically (zero manual work)
- ✅ **Time Freedom**: Monthly billing cycle completed in <1 hour (vs. 4-8 hours manual)
- ✅ **Payment Visibility**: Real-time payment reconciliation (SINPE payment confirmed within 5 minutes)

**User Satisfaction Targets:**
- Net Promoter Score (NPS): >40 by Month 6
- "Would recommend" rate: >70%
- "Saves me time" agreement: >80%
- "Easy to use" rating: >4/5 stars

### Business Success (GMS Platform)

**3-Month Milestones (MVP Launch Period):**
- 10-20 paying customers (Starter tier, compliance-focused)
- ₡280k-560k MRR ($500-1,000 USD)
- <20% churn (expect learning curve churn during MVP)
- 3+ documented success stories (compliance testimonials)
- First competitive win (gym switches from LatinsoftCR/spreadsheets)

**6-Month Milestones (Post-Tilopay Integration):**
- 30-50 paying customers
- ₡1M-1.5M MRR ($1,800-2,700 USD)
- <15% churn
- 20-30% upgrade to Professional tier (with payment automation)
- 5+ customer testimonials/case studies

**12-Month Targets:**
- 50-100 paying customers (10-20% of target market)
- ₡2M-4M MRR ($36k-72k USD ARR)
- <10% monthly churn rate
- 40-50% of revenue from Professional/Business tiers (not just Starter)
- LTV:CAC ratio: 6-12x (needs validation through actual customer data)

**Market Penetration Goals:**
- Primary market (San José independent gyms): 10-15% penetration (15-25 of ~150-200 gyms)
- Secondary market (boutique studios): 5-10% penetration (5-15 of ~100-150 studios)
- Competitive displacement: 5+ gyms switch from LatinsoftCR or spreadsheets

**Revenue Quality Metrics:**
- Annual contract rate: >30% of customers by Month 12 (vs. month-to-month)
- Average revenue per customer: >₡35,000/month by Month 12
- Customer acquisition cost (CAC): <₡200k per customer
- Months to payback CAC: <6 months

### Technical Success

**MVP Technical Requirements:**
- **Uptime**: >99% (basic infrastructure stability)
- **E-Invoice Success Rate**: >95% first-submission acceptance by Hacienda
- **Invoice Generation Speed**: <5 seconds (XML creation → signature → DGT submission)
- **Data Loss Prevention**: Zero data loss incidents (5-year archival requirement)
- **Certificate Management**: Automated digital signature renewal tracking

**Performance Targets:**
- Page load time: <2 seconds (Costa Rica internet speeds)
- Invoice generation: <5 seconds (complete workflow)
- Report generation: <10 seconds for standard reports
- Bulk operations: Process 100 invoices in <2 minutes

**Post-MVP Integration Success (Tilopay Phase):**
- **Tilopay Integration**: >98% redirect return success rate
- **Payment Reconciliation**: <5 minutes latency (SINPE payment → GMS update)

**Odoo Compatibility:**
- **Module Inheritance**: Zero breaking changes on Odoo minor version upgrades
- **Multi-Tenant Isolation**: Zero cross-tenant data leakage incidents

**Security & Compliance:**
- **Data Privacy (Ley 8968)**: 100% compliance with CR data protection law
- **Digital Signatures**: 100% valid signatures on all e-invoices
- **Audit Trail**: Complete transaction history for 5+ years (Hacienda requirement)
- **Payment Security (PCI DSS)**: Level 1 compliance when Tilopay integrated (rely on Tilopay for card handling)

### Measurable Outcomes Summary

**By End of Month 3 (MVP):**
- 10-20 paying gym customers using the platform
- >95% e-invoice acceptance rate by Hacienda
- <20% monthly churn
- 3+ documented success stories (compliance-focused)

**By End of Month 6 (Post-Tilopay):**
- 30-50 paying customers
- ₡1M-1.5M MRR
- <15% monthly churn
- 20-30% on Professional tier (payment automation)

**By End of Month 12:**
- 50-100 paying customers (10-20% market penetration)
- ₡2M-4M MRR ($36k-72k USD ARR)
- <10% monthly churn
- >70% customer satisfaction ("would recommend")
- Zero compliance-related penalties for any customer

---

## Product Scope

### MVP - Minimum Viable Product (Launch by Q2 2025)

**Core Focus: Get gyms Hacienda-compliant BEFORE the September 2025 deadline**

**Must-Have for Launch:**

**1. Hacienda E-Invoice v4.4 Compliance** (PRIMARY VALUE)
- XML v4.4 generation (compliant format)
- Digital signature management (certificate upload, renewal tracking)
- DGT API submission (real-time)
- Real-time status tracking (Pending/Accepted/Rejected)
- Error handling with plain-language Spanish messages
- 5-year archival (compliance requirement)
- **Success Metric**: >95% first-submission acceptance rate

**2. Gym Owner Settings & Configuration**
- Company information setup
- Digital certificate upload/management
- Hacienda credentials configuration
- Tax ID (Cédula/NITE) validation
- Business type selection
- **Success Metric**: Complete setup in <2 hours

**3. Basic Member Management**
- Member registration & profiles
- Customer tax ID capture (required for invoicing)
- Member list/search
- Basic member status (active/inactive)
- **Success Metric**: Can invoice any member with required tax data

**4. Manual Invoicing Workflow**
- Create invoice for member
- Line items (membership, services, products)
- Tax calculation (IVA 13%)
- Generate + Sign + Submit to Hacienda (one-click)
- View invoice status (Preparing/Sent/Approved-Rejected)
- Download compliant PDF
- Resend/retry failed invoices
- **Success Metric**: Invoice → Hacienda approval in <5 minutes

**5. Essential UX (Odoo Simplified)**
- Spanish-first interface
- Simple 3-state workflow (Preparing → Sent → Approved/Rejected)
- Hide Odoo technical complexity (no "Draft/Generated/Signed" states)
- Mobile-responsive web (not native apps yet)
- Setup wizard (guided Hacienda configuration)
- Video tutorials in Spanish

**6. Self-Service Onboarding**
- 30-day free trial (no credit card required)
- Email support (24-hour response SLA)
- Knowledge base articles (Spanish)

**What's NOT in MVP:**
- ❌ Tilopay payment integration (manual payment recording for MVP)
- ❌ Automatic payment reconciliation
- ❌ Recurring billing automation
- ❌ SINPE Móvil integration
- ❌ Class scheduling & booking
- ❌ Mobile apps (iOS/Android)
- ❌ WhatsApp integration
- ❌ Advanced reporting/analytics
- ❌ Multi-location support

**MVP Value Proposition:**
> "Get Hacienda v4.4 compliant in 2 hours. Submit compliant e-invoices with one click. Avoid ₡8.3M+ penalties."

**MVP Success Criteria:**
- Gym owner can go from signup → first compliant invoice in <2 hours
- Works for 50-200 member gyms
- Handles 100+ manual invoices/month per gym
- Starter tier only (₡28,000/month)

### Growth Features - Phase 1: Payment Automation (Months 4-6)

**Focus: Automate payment collection and invoicing**

**1. Tilopay Payment Integration**
- SINPE Móvil reconciliation (automatic)
- Credit/debit card processing
- Automatic invoice generation on payment received
- Payment confirmation via redirect returns
- Payment status dashboard

**2. Recurring Billing Automation**
- Membership auto-billing (monthly/annual)
- Automatic payment reminders (email)
- Failed payment retry logic
- Subscription management
- Member payment portal (self-service)

**3. Professional Tier Features**
- Email automation (payment reminders, renewals)
- Basic reporting (revenue, member status)
- Export invoices to Excel/PDF

**Phase 1 Value Proposition:**
> "Automatic SINPE Móvil payments → invoices → Hacienda. Zero manual billing work."

**Pricing Tier Introduced:**
- Professional: ₡50,400/month (includes payment automation)

### Growth Features - Phase 2: Operations & Engagement (Months 7-12)

**Focus: Boutique studio features and member engagement**

**1. Class Scheduling & Booking**
- Class schedule management
- Class capacity limits
- Member booking portal
- Waitlist management
- Attendance tracking

**2. Member Mobile App** (iOS + Android)
- Class booking
- Payment history
- Membership status
- Push notifications

**3. Advanced Reporting & Analytics**
- Revenue analytics
- Member retention dashboards
- Hacienda compliance reports
- Class attendance reports
- Custom report builder

**4. Business Tier Features**
- Multi-location support (2-3 locations)
- Consolidated reporting across locations
- Staff roles & permissions
- API access (for custom integrations)

**Pricing Tiers Introduced:**
- Business: ₡89,600/month (multi-location)

### Vision - Future (Months 13-24+)

**1. Advanced Automation**
- AI-powered churn prediction
- Dynamic pricing recommendations
- Automated re-engagement campaigns

**2. Enterprise Features**
- White-label member apps (gym branding)
- 6+ location management
- Custom Hacienda integrations
- Payroll system integration

**3. Ecosystem Expansion**
- WhatsApp Business API (with full legal compliance framework)
- Accounting software integrations (ContaPlus, other CR tools)
- Access control hardware partnerships (biometric, QR codes)
- Nutrition/wellness tracking
- Retail POS (supplements, apparel)

**4. Geographic Expansion**
- Panama market (similar e-invoicing requirements)
- Nicaragua expansion
- Mexico (CFDI compliance)
- Full LATAM compliance roadmap

**5. Vertical Expansion**
- Dance studios
- Martial arts schools
- Yoga/wellness centers
- Sports clubs
- Personal training studios

**Pricing Tier:**
- Enterprise: Custom pricing (₡150k+/month)

---

---

## ⚠️ CRITICAL: Legal & Regulatory Compliance Research Required

**Status**: PENDING - Must complete before launch

The following Costa Rican laws and regulations require thorough research and compliance validation:

1. **Data Privacy**: Ley No. 8968 (Data Protection Law)
2. **E-Invoicing**: Resolution MH-DGT-RES-0027-2024 (v4.4) ✅ Partially covered
3. **Payment Processing**: BCCR regulations, Tilopay partnership terms, PCI DSS
4. **Electronic Communications**: WhatsApp, SMS, Email marketing laws
5. **SaaS/Software**: Consumer protection, terms of service requirements
6. **Multi-Tenant Data**: Data isolation, privacy obligations
7. **Fitness Industry**: Health data, liability, insurance requirements

**Action Required**: Legal research workflow or attorney consultation before production launch.

---

## ⚠️ CRITICAL: Technical Dependencies & Assumptions

**Payment Gateway Dependency:**
- **SINPE Móvil Integration**: Requires payment gateway partner (Tilopay or similar)
- **Direct Bank API**: NOT AVAILABLE for SINPE Móvil reconciliation
- **Vendor Dependency**: Tied to Tilopay's uptime, fees, API changes, terms of service
- **Transaction Fees**: Tilopay charges 2-3% per transaction (research exact pricing)

**Research Required Before MVP:**
- [ ] Tilopay API documentation review
- [ ] Tilopay pricing structure (transaction fees, monthly costs)
- [ ] Tilopay partnership terms and SLA
- [ ] Alternative gateways evaluation (BAC Credomatic, FirstAtlanticCommerce)
- [ ] Competitor payment gateway analysis (LatinsoftCR, CrossHero integration status)

---
