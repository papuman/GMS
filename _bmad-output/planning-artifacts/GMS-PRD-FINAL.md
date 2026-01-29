# GMS Product Requirements Document

**Costa Rica Gym Management SaaS Platform**

**Version:** 1.0 (Final)
**Date:** January 16, 2026
**Author:** Papu
**Quality Score:** 96.8/100 (Grade: A+)
**Status:** ✅ Approved for Architecture Phase

---

## Document Metadata

**Classification:**
- **Domain:** Fitness & Wellness
- **Project Type:** Web Application (Multi-tenant SaaS B2B)
- **Deployment Model:** Multi-tenant SaaS B2B
- **Complexity:** Medium

**Quality Metrics:**
- **Validation Score:** 96.8/100
- **Grade:** A+

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Classification](#project-classification)
3. [Success Criteria](#success-criteria)
4. [Product Scope](#product-scope)
5. [User Journeys](#user-journeys)
6. [Functional Requirements](#functional-requirements)
7. [Non-Functional Requirements](#non-functional-requirements)
8. [Legal & Regulatory Compliance Requirements](#legal--regulatory-compliance-requirements)
9. [Technical Dependencies & Assumptions](#technical-dependencies--assumptions)

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

**4. Opt-In Communication Tools** (Legal Compliance - Laws 8968/7975/8642)
- **Email Marketing**: Express written consent required before first contact; exception for existing customers if informed during purchase; must include sender identification and unsubscribe method; penalties 0.025%-0.5% annual income for violations
- **SMS Marketing**: Explicit opt-in consent required; must honor STOP/CANCELAR/NO keywords (opt-out); must support HELP/AYUDA keywords (EN/ES) with business identification and contact details; SUTEL oversight
- **WhatsApp Business**: No specific regulations beyond general data protection (Law 8968); 80% of Costa Rica population uses WhatsApp; member-initiated click-to-chat compliant; automated messaging requires express consent
- **In-App Push Notifications**: Member app notifications governed by general consent framework (opt-in during app installation)

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
- Pass-through to gyms or absorb into pricing?
- **Research Required**: Exact Tilopay pricing structure

### Critical Dependencies & Risks

**Technical Dependencies:**
- ✅ Odoo 19 Enterprise license
- ⚠️ Tilopay partnership & API access (CRITICAL)
- ⚠️ Hacienda API rate limits & SLA
- ✅ **BAC Credomatic backup gateway** (validated): Requires banking approval, SSL/TLS 1.2 certificate, supports e-Socket and 3D Secure integration; API Center at developers.baccredomatic.com; WooCommerce/Magento integrations available

**Legal/Compliance Dependencies:**
- ✅ **Ley 8968 (Data Protection)**: Express consent required for data processing; data quality and security measures mandatory; penalties USD 4,000-24,000 for non-compliance; GDPR-aligned Bill 23097 expected Q1 2025 implementation in 2026
- ✅ **Payment Processing (BCCR)**: Regulation 9831 governs payment card commissions; SUGEF oversees all financial intermediaries; SINPE Móvil regulated by BCCR as national payment system
- ✅ **Multi-Tenant Data Isolation**: Ley 8968 requires secure personal data handling; databases must prevent cross-tenant data exposure
- ✅ **Electronic Communications**: Laws 8968/7975/8642 require express written consent for email/SMS/phone marketing; penalties 0.025%-0.5% of annual income; SMS must support STOP/CANCELAR/NO and HELP/AYUDA keywords (EN/ES); WhatsApp governed by general data protection laws (80% CR population uses WhatsApp)

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

---

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

**Infrastructure layer handles:**
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
- LTV:CAC ratio: 6-12x (needs validation through customer data)

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
- **Invoice Generation Speed**: <5 seconds (complete v4.4 compliance workflow)
- **Data Loss**: Zero incidents (5-year archival requirement)
- **Certificate Management**: Automated digital signature renewal tracking

**Performance Targets:**
- Interface responsiveness: <2 seconds for primary operations (Costa Rica internet speeds)
- Invoice generation: <5 seconds (complete workflow)
- Report availability: <10 seconds for standard reports
- Bulk operations: Process 100 invoices in <2 minutes

**Post-MVP Integration Success (Tilopay Phase):**
- **Tilopay Integration**: >98% redirect return success rate
- **Payment Reconciliation**: <5 minutes latency (SINPE payment → GMS update)

**Odoo Compatibility:**
- **Platform Compatibility**: Zero service disruptions during platform minor version upgrades
- **Data Security**: Zero customer data exposure incidents between accounts

**Security & Compliance:**
- **Data Privacy (Ley 8968)**: 100% compliance with CR data protection law
- **Digital Signatures**: 100% valid signatures on all e-invoices
- **Audit Trail**: Complete transaction history for 5+ years (Hacienda requirement)
- **Payment Card Data Security**: Industry-standard compliance when Tilopay integrated (rely on Tilopay for card handling)

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
- Zero penalties for any customer

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

**4. Data Privacy Compliance (Ley 8968)**
- Privacy notice display on signup and data collection forms
- Member consent tracking for data processing (explicit opt-in)
- Member data access request handling (self-service data export)
- Member data deletion request workflow (right to be forgotten)
- Data retention policy enforcement (automatic purge after account closure)
- Processing activity documentation (data mapping for gym owner + members)
- **Success Metric**: 100% Ley 8968 compliance, zero data privacy violations

**5. Manual Invoicing Workflow**
- Create invoice for member
- Line items (membership, services, products)
- Tax calculation (IVA 13%)
- Generate + Sign + Submit to Hacienda (one-click)
- View invoice status (Preparing/Sent/Approved-Rejected)
- Download compliant PDF
- Resend/retry failed invoices
- **Success Metric**: Invoice → Hacienda approval in <5 minutes

**6. Essential UX (Odoo Simplified)**
- Spanish-first interface
- Simple 3-state workflow (Preparing → Sent → Approved/Rejected)
- Hide Odoo technical complexity (no "Draft/Generated/Signed" states)
- Mobile-responsive web (not native apps yet)
- Setup wizard (guided Hacienda configuration)
- Video tutorials in Spanish

**7. Self-Service Onboarding**
- 30-day free trial (no credit card required)
- Email support (24-hour response SLA)
- Knowledge base articles (Spanish)

**8. User Feedback Collection**
- In-app NPS survey (30-day post-signup trigger)
- Recommendation likelihood measurement ("Would recommend" scale)
- Time-saving perception survey ("Saves me time" agreement scale)
- Response tracking and aggregation
- **Success Metric**: NPS >40, "Would recommend" >70%, "Saves me time" >80%

**MVP Exclusions:**
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
- Annual contract incentive system (discount pricing, upgrade prompts)
- Contract renewal automation (pre-expiration notifications)
- **Success Metric**: >30% annual contract adoption rate by Month 12

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
- **Success Metrics**: >70% class utilization rate, <5% no-show rate, member booking time <2 minutes

**2. Member Mobile App** (iOS + Android)
- Class booking
- Payment history
- Membership status
- Push notifications
- **Success Metrics**: >60% member adoption rate, >4.0 app store rating, >50% monthly active users

**3. Advanced Reporting & Analytics**
- Revenue analytics
- Member retention dashboards
- Hacienda compliance reports
- Class attendance reports
- Custom report builder
- Business metrics tracking (LTV, CAC, churn rate calculations)
- **Success Metric**: LTV:CAC ratio 6-12x, automated metric calculation accuracy >95%

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

## User Journeys

### Primary User Types

**1. Gym Owner** (Decision-maker, administrator, compliance-responsible)
**2. Gym Staff** (Front desk, trainers, operations)
**3. Gym Member** (End customer, service consumer)

### Journey 1: Gym Owner - Initial Setup & Compliance Configuration

**User Type:** Gym Owner
**Goal:** Get Hacienda-compliant and ready to invoice in under 2 hours
**Frequency:** One-time (onboarding)

**Current Pain Points:**
- No clear path to e-invoicing compliance
- September 2025 deadline causing urgency
- ₡8.3M+ penalties for non-compliance
- Complex Hacienda technical requirements overwhelming

**Journey Steps:**
1. **Sign up** → Create GMS account with 30-day free trial
2. **Company setup** → Enter business details (RUT, NITE, business type)
3. **Upload digital certificate** → Upload Hacienda-issued certificate file
4. **Configure Hacienda credentials** → Enter API credentials from Hacienda admin panel
5. **Test connection** → System validates connection to Hacienda DGT API
6. **Create first test invoice** → Submit test invoice to sandbox environment
7. **Receive approval confirmation** → Hacienda responds with "Approved" status

**Success State:**
- Hacienda connection active and validated
- Can submit compliant e-invoices
- Setup completed in <2 hours
- Ready to invoice members legally

**Key Metrics:**
- Setup time <2 hours (Success Criteria)
- First invoice approval <5 minutes (MVP requirement)

### Journey 2: Gym Owner - Monthly E-Invoicing Workflow

**User Type:** Gym Owner
**Goal:** Submit compliant e-invoices for all monthly memberships without manual work
**Frequency:** Monthly (recurring)

**Current Pain Points:**
- Manually creating invoices in separate system
- Chasing late payments via WhatsApp
- No automatic reconciliation with payments
- Hours spent on billing cycles

**Journey Steps:**
1. **Trigger billing cycle** → System identifies all members with active subscriptions
2. **Auto-generate invoices** → System creates XML v4.4 invoices for each member
3. **Digital signature** → System signs invoices with gym's digital certificate
4. **Submit to Hacienda** → Batch submit all invoices to DGT API
5. **Monitor status** → View dashboard showing "Sent/Approved/Rejected" status
6. **Handle rejections** → Review rejected invoices, fix issues, resubmit
7. **Archive compliant PDFs** → Download and store 5-year compliant records

**Success State:**
- 100+ invoices submitted in <30 minutes
- >95% first-submission acceptance rate
- Compliant archival for 5 years
- Zero manual XML creation

**Key Metrics:**
- Invoice → Hacienda approval <5 minutes (MVP requirement)
- >95% first-submission acceptance rate (MVP requirement)

### Journey 3: Gym Owner - Payment Reconciliation via Tilopay

**User Type:** Gym Owner
**Goal:** Automatically reconcile SINPE Móvil payments with member accounts
**Frequency:** Daily (recurring)

**Current Pain Points:**
- Members send SINPE payments via WhatsApp screenshots
- Manual matching of payments to member accounts
- Cash flow blindness - don't know who paid
- Hours per week on reconciliation

**Journey Steps:**
1. **Member initiates payment** → Member clicks "Pay Now" link in member portal
2. **Redirect to Tilopay** → Member redirected to Tilopay gateway (SINPE or card)
3. **Complete payment** → Member completes payment (SINPE Móvil or card)
4. **Redirect return** → Tilopay redirects back to GMS with payment confirmation
5. **Auto-generate invoice** → System creates and submits e-invoice to Hacienda
6. **Update member account** → Payment applied to member balance automatically
7. **Send confirmation** → Member receives email with invoice PDF and payment receipt

**Success State:**
- Zero manual payment matching
- Instant member account updates
- Automatic e-invoice generation on payment
- Payment → Invoice → Member update in <5 minutes

**Key Metrics:**
- Automatic payment reconciliation (Growth Phase 1)
- Payment → Invoice generation (Growth Phase 1)

### Journey 4: Gym Staff - Member Check-In & Payment Processing

**User Type:** Gym Staff (Front desk)
**Goal:** Quickly check in members and process walk-in payments
**Frequency:** Daily (recurring, multiple times)

**Current Pain Points:**
- Slow manual lookup of member status
- Confusion about whether member paid
- No quick payment processing at front desk

**Journey Steps:**
1. **Member arrives** → Member approaches front desk
2. **Search member** → Staff searches by name or member ID
3. **View status** → Staff sees active/inactive status and payment status
4. **Process payment** (if needed) → Staff records payment (manual MVP, automated Growth Phase)
5. **Check in member** → Staff marks member as checked in for session
6. **Confirm** → Member receives confirmation

**Success State:**
- Check-in completed in <30 seconds
- Clear visibility of member payment status
- Simple 3-click workflow (not 8-state Odoo complexity)

**Key Metrics:**
- Check-in time <30 seconds
- Staff can operate after <1 hour training (UX simplification goal)

### Journey 5: Gym Member - Self-Service Payment

**User Type:** Gym Member
**Goal:** Pay monthly membership fee quickly via SINPE Móvil or card
**Frequency:** Monthly (recurring)

**Current Pain Points:**
- Must send SINPE screenshot via WhatsApp
- Gym sometimes doesn't see payment
- No automatic confirmation
- Unclear if payment received

**Journey Steps:**
1. **Receive payment reminder** → Email reminder 3 days before due date
2. **Click payment link** → Click "Pay Now" in email
3. **Choose payment method** → Select SINPE Móvil or credit/debit card
4. **Complete payment** → Pay via Tilopay gateway
5. **Receive confirmation** → Instant email with invoice PDF and receipt
6. **Access member portal** → View payment history and invoices

**Success State:**
- Payment completed in <2 minutes
- Instant confirmation with compliant invoice
- No WhatsApp screenshots needed
- Can access payment history anytime

**Key Metrics:**
- Member payment portal (Growth Phase 1)
- Automatic payment reminders (Growth Phase 1)

### Journey 6: Gym Owner - Analytics & Revenue Reporting

**User Type:** Gym Owner
**Goal:** Understand revenue, member retention, and payment collection rates
**Frequency:** Weekly/Monthly (recurring)

**Current Pain Points:**
- No visibility into cash flow
- Excel spreadsheets for tracking revenue
- Can't identify late payers quickly
- No retention metrics

**Journey Steps:**
1. **Open dashboard** → View GMS analytics dashboard
2. **Review KPIs** → See MRR, active members, retention rate, late payments
3. **Filter by period** → Select date range (week/month/quarter)
4. **Export reports** → Download CSV for accounting
5. **Identify issues** → See which members have late payments
6. **Take action** → Send payment reminders to late payers

**Success State:**
- Real-time revenue visibility
- Retention metrics tracked automatically
- Late payer identification in <1 click
- Export-ready accounting reports

**Key Metrics:**
- Dashboard with KPIs (Growth Phase 2)
- Revenue analytics (Growth Phase 2)

### Journey Coverage Validation

**User Types Covered:** 3/3
- ✅ Gym Owner (6 journeys)
- ✅ Gym Staff (1 journey)
- ✅ Gym Member (1 journey)

**Success Criteria Coverage:**
- ✅ User Success: Gym owner setup <2 hours (Journey 1)
- ✅ User Success: Invoice approval <5 minutes (Journey 2)
- ✅ User Success: NPS >40 (implicit in friction reduction across journeys)
- ✅ Business Success: Customer acquisition (enabled by Journey 1 onboarding)
- ✅ Technical Success: >95% invoice acceptance (Journey 2)

**MVP Feature Coverage:**
- ✅ E-Invoice v4.4 compliance (Journey 1, 2)
- ✅ Gym owner settings (Journey 1)
- ✅ Member management (Journey 4)
- ✅ Data privacy compliance (implicit in all journeys)
- ✅ Manual invoicing (Journey 2)
- ✅ Essential UX (Journey 4 - 3-state workflow)

**Growth Phase Coverage:**
- ✅ Tilopay payment integration (Journey 3)
- ✅ Recurring billing automation (Journey 5)
- ✅ Analytics dashboard (Journey 6)

---

## Functional Requirements

**Format:** [Actor] can [capability]
**Traceability:** Each FR maps to User Journey and Success Criteria
**Acceptance Criteria:** Measurable, testable conditions

### MVP Requirements (M1-M3: Q2 2025)

**FR-001: Gym Owner can upload and configure digital certificate for Hacienda**
- **Journey:** Journey 1 (Initial Setup)
- **Acceptance Criteria:**
  - Upload .p12 or .pfx certificate file
  - Enter certificate password
  - System validates certificate is valid and not expired
  - Certificate stored securely (encrypted at rest)
  - Certificate expiration warning 30 days before expiry
- **Priority:** CRITICAL (MVP blocker)

**FR-002: Gym Owner can configure Hacienda DGT API credentials**
- **Journey:** Journey 1 (Initial Setup)
- **Acceptance Criteria:**
  - Enter API username and password
  - Select environment (sandbox/production)
  - Test connection returns success/failure status
  - Credentials stored securely (encrypted)
  - Connection status visible on dashboard
- **Priority:** CRITICAL (MVP blocker)

**FR-003: Gym Owner can create e-invoice compliant with Hacienda v4.4**
- **Journey:** Journey 2 (Monthly E-Invoicing)
- **Acceptance Criteria:**
  - Generate XML v4.4 format automatically
  - Include all required Hacienda fields (cédula, NITE, tax IDs, line items, IVA 13%)
  - Digitally sign XML with gym's certificate
  - Validate XML against Hacienda v4.4 schema before submission
  - Display validation errors in Spanish with actionable guidance
- **Priority:** CRITICAL (MVP blocker)

**FR-004: Gym Owner can submit e-invoice to Hacienda DGT and receive status**
- **Journey:** Journey 2 (Monthly E-Invoicing)
- **Acceptance Criteria:**
  - Submit signed XML to Hacienda DGT API
  - Receive response within 5 minutes for 95% of submissions
  - Display status: Preparing → Sent → Approved/Rejected
  - Parse Hacienda response and display reason for rejection (if rejected)
  - Provide "Retry" action for rejected invoices
- **Priority:** CRITICAL (MVP blocker)
- **Success Metric:** >95% first-submission acceptance rate

**FR-005: Gym Owner can download compliant e-invoice PDF**
- **Journey:** Journey 2 (Monthly E-Invoicing)
- **Acceptance Criteria:**
  - Generate PDF with all Hacienda-required elements (QR code, digital signature, tax breakdown)
  - Include gym branding (logo, colors)
  - PDF is 5-year archival compliant (PDF/A format)
  - Download immediately after Hacienda approval
  - Email PDF to member automatically
- **Priority:** HIGH (MVP requirement)

**FR-006: Gym Owner can view 5-year archive of all e-invoices**
- **Journey:** Journey 2 (Monthly E-Invoicing)
- **Acceptance Criteria:**
  - Search invoices by date range, member name, invoice number, status
  - Filter by status (Approved/Rejected/Pending)
  - Download individual or bulk PDFs
  - Export XML files for Hacienda audit requests
  - Archive retention: minimum 5 years
- **Priority:** HIGH (compliance requirement)

**FR-007: Gym Owner can register members with required tax information**
- **Journey:** Journey 4 (Member Check-In), implicit in all journeys
- **Acceptance Criteria:**
  - Capture member name, email, phone, cédula (tax ID)
  - Validate cédula format (9 digits for individuals, 10-12 for legal entities)
  - Mark required fields clearly (cédula required for invoicing)
  - Support both individual and legal entity customer types
  - Store member data securely with encryption
- **Priority:** CRITICAL (MVP blocker - needed for invoicing)

**FR-008: Gym Owner can search and view member profiles**
- **Journey:** Journey 4 (Member Check-In)
- **Acceptance Criteria:**
  - Search by name, email, phone, member ID, cédula
  - View member profile with contact info, membership status, payment history
  - Display active/inactive status prominently
  - Show last payment date and next billing date
  - Responsive search (results appear as typing)
- **Priority:** HIGH (MVP requirement)

**FR-009: Member can provide data processing consent (Ley 8968 compliance)**
- **Journey:** All journeys (implicit)
- **Acceptance Criteria:**
  - Display privacy notice on signup and data collection forms
  - Explicit opt-in checkbox for data processing (no pre-checked boxes)
  - Record consent timestamp and IP address
  - Allow member to withdraw consent anytime
  - Provide data export on request (CSV format)
- **Priority:** CRITICAL (legal compliance - Ley 8968)

**FR-010: Member can request data deletion (Ley 8968 right to be forgotten)**
- **Journey:** All journeys (implicit)
- **Acceptance Criteria:**
  - Member submits data deletion request via member portal or email
  - Gym owner reviews and approves request
  - System purges member data within 30 days of approval
  - Retain only legally required data (invoices for 5-year tax compliance)
  - Send deletion confirmation email to member
- **Priority:** HIGH (legal compliance - Ley 8968)

**FR-011: System can auto-purge member data after account closure**
- **Journey:** All journeys (implicit)
- **Acceptance Criteria:**
  - Identify inactive members (no activity for 3+ years post-closure)
  - Send deletion notice 30 days before purge
  - Automatically delete member data after notice period
  - Retain only invoices for 5-year compliance
  - Log all purge actions for audit trail
- **Priority:** MEDIUM (legal compliance - Ley 8968)

**FR-012: Gym Owner can create manual invoice for member**
- **Journey:** Journey 2 (Monthly E-Invoicing), Journey 4 (Member Check-In for walk-ins)
- **Acceptance Criteria:**
  - Select member from dropdown
  - Add line items (membership, class package, product, service)
  - Calculate IVA 13% automatically
  - Apply discount codes (if applicable)
  - Generate → Sign → Submit to Hacienda in one click
  - Display invoice total before submission
- **Priority:** HIGH (MVP requirement)

**FR-013: System can display simplified 3-state invoice workflow**
- **Journey:** Journey 2 (Monthly E-Invoicing)
- **Acceptance Criteria:**
  - Hide Odoo's 8 internal states (Draft/Generated/Signed/etc.)
  - Show only 3 user-facing states: Preparing → Sent → Approved/Rejected
  - Use Spanish labels: "Preparando" → "Enviado" → "Aprobado/Rechazado"
  - Status transitions happen automatically (no manual state changes)
  - Color coding: Yellow (Preparing), Blue (Sent), Green (Approved), Red (Rejected)
- **Priority:** HIGH (Essential UX - Odoo simplification)

**FR-014: Gym Owner can retry failed invoice submission**
- **Journey:** Journey 2 (Monthly E-Invoicing)
- **Acceptance Criteria:**
  - Display "Retry" button for rejected invoices
  - Show Hacienda rejection reason in plain Spanish
  - Allow editing invoice details before retry
  - Re-sign and re-submit to Hacienda
  - Track retry attempts (max 3 retries, escalate to support after)
- **Priority:** HIGH (MVP requirement)

**FR-015: Gym Owner can access setup wizard for Hacienda configuration**
- **Journey:** Journey 1 (Initial Setup)
- **Acceptance Criteria:**
  - Step-by-step wizard with 5 steps (Company Info → Certificate → Credentials → Test → Complete)
  - Progress indicator (Step 1/5, Step 2/5, etc.)
  - Validation at each step before proceeding
  - Spanish video tutorials embedded in wizard
  - Complete setup in <2 hours for 90% of gym owners
- **Priority:** HIGH (Essential UX - onboarding)
- **Success Metric:** Setup time <2 hours

**FR-016: Gym Owner can access Spanish knowledge base and video tutorials**
- **Journey:** Journey 1 (Initial Setup), Journey 2 (Monthly E-Invoicing)
- **Acceptance Criteria:**
  - Knowledge base covers 100% of MVP workflows (setup, invoicing, troubleshooting, member management)
  - Minimum 5 video tutorials in Spanish (5-10 minutes each)
  - Search functionality returns relevant results in <2 seconds
  - Contextual help links embedded in UI at decision points
  - 24-hour email support response SLA
  - **Success Metric:** 80% of users complete first invoice without support contact
- **Priority:** MEDIUM (MVP requirement)
- **Success Criteria Link:** User Success - <2 support tickets per gym in first month

**FR-017: System can collect NPS feedback 30 days post-signup**
- **Journey:** All journeys (implicit - feedback collection)
- **Acceptance Criteria:**
  - Trigger in-app NPS survey 30 days after signup
  - Ask: "How likely are you to recommend GMS?" (0-10 scale)
  - Ask: "Would you recommend GMS to another gym?" (Yes/No)
  - Ask: "GMS saves me time" (1-5 agreement scale)
  - Store responses and calculate aggregated NPS score
  - **Survey response rate target:** >30% of triggered surveys completed
  - **Minimum sample size:** 20 responses before calculating NPS score
- **Priority:** MEDIUM (feedback collection for Success Criteria)
- **Success Metric:** NPS >40, "Would recommend" >70%, "Saves time" >80%

### Growth Phase 1 Requirements (M4-M6: Payment Automation)

**FR-018: Member can pay via Tilopay gateway (SINPE Móvil or card)**
- **Journey:** Journey 3 (Payment Reconciliation), Journey 5 (Self-Service Payment)
- **Acceptance Criteria:**
  - Redirect member to Tilopay payment page
  - Support SINPE Móvil and credit/debit cards
  - Capture payment amount, member ID, invoice reference
  - Return to GMS after payment completion with success/failure status
  - Handle payment failures gracefully with retry option
- **Priority:** CRITICAL (Growth Phase 1 blocker)

**FR-019: System can auto-generate e-invoice when payment received**
- **Journey:** Journey 3 (Payment Reconciliation)
- **Acceptance Criteria:**
  - Detect payment confirmation from Tilopay redirect
  - Auto-create invoice with payment details
  - Auto-sign and submit to Hacienda
  - Update member account balance immediately
  - Send email with invoice PDF and payment receipt
- **Priority:** CRITICAL (Growth Phase 1 - automation goal)

**FR-020: System can automatically reconcile SINPE Móvil payments**
- **Journey:** Journey 3 (Payment Reconciliation)
- **Acceptance Criteria:**
  - Match Tilopay payment to member account via redirect confirmation
  - Update member balance automatically
  - Mark invoice as "Paid" in system
  - Generate payment receipt
  - Reconciliation completes within 5 minutes of payment
- **Priority:** CRITICAL (Growth Phase 1 - core value prop)

**FR-021: Gym Owner can configure recurring billing for memberships**
- **Journey:** Journey 2 (Monthly E-Invoicing automation)
- **Acceptance Criteria:**
  - Set billing frequency (monthly/quarterly/annual)
  - Set billing day (e.g., 1st of month)
  - Define membership plan pricing
  - Enable/disable auto-billing per member
  - View list of members with auto-billing enabled
- **Priority:** HIGH (Growth Phase 1)

**FR-022: System can auto-bill members with recurring subscriptions**
- **Journey:** Journey 2 (Monthly E-Invoicing automation), Journey 5 (Self-Service Payment)
- **Acceptance Criteria:**
  - Identify members with active subscriptions on billing day
  - Auto-generate invoices for all active members
  - Send payment reminder email with "Pay Now" link
  - Track payment status (Paid/Unpaid/Overdue)
  - Retry failed payments after 3 days (max 2 retries)
- **Priority:** HIGH (Growth Phase 1 - automation)

**FR-023: Member can access self-service payment portal**
- **Journey:** Journey 5 (Self-Service Payment)
- **Acceptance Criteria:**
  - Member logs in with email + password
  - View current balance and payment due date
  - View payment history (last 12 months)
  - Download invoice PDFs
  - Click "Pay Now" to initiate Tilopay payment
- **Priority:** HIGH (Growth Phase 1)

**FR-024: System can send automatic payment reminders**
- **Journey:** Journey 5 (Self-Service Payment)
- **Acceptance Criteria:**
  - Send email reminder 3 days before due date
  - Send email reminder on due date
  - Send overdue notice 3 days after due date
  - Include "Pay Now" link in all reminder emails
  - Allow member to opt-out of reminders (with manual opt-in required)
- **Priority:** MEDIUM (Growth Phase 1)

**FR-025: System can track annual contract adoption**
- **Journey:** Journey 5 (Self-Service Payment - upsell to annual)
- **Acceptance Criteria:**
  - Display annual plan option with 20% discount during monthly payment flow
  - Track conversion rate: (Annual contracts / Total active contracts) × 100
  - Dashboard displays current adoption rate with trend graph
  - Send pre-expiration renewal notice 30 days before annual contract ends
  - Calculate and display annual contract adoption rate on analytics dashboard
  - Export annual contract report (CSV) with member details and renewal dates
  - **Intermediate Milestones:** 10% adoption by Month 6, 20% by Month 9, 30% by Month 12
- **Priority:** MEDIUM (Growth Phase 1 - business metric)
- **Success Metric:** >30% annual contract adoption rate by Month 12

### Growth Phase 2 Requirements (M7-M12: Operations & Engagement)

**FR-026: Gym Owner can view analytics dashboard with KPIs**
- **Journey:** Journey 6 (Analytics & Revenue Reporting)
- **Acceptance Criteria:**
  - Display MRR (Monthly Recurring Revenue)
  - Display active member count
  - Display retention rate (% members retained month-over-month)
  - Display late payment count and total overdue amount
  - Filter by date range (week/month/quarter/year)
- **Priority:** HIGH (Growth Phase 2)

**FR-027: Gym Owner can export accounting reports**
- **Journey:** Journey 6 (Analytics & Revenue Reporting)
- **Acceptance Criteria:**
  - Export revenue report as CSV
  - Include columns: Date, Member, Invoice #, Amount, Tax, Payment Method, Status
  - Filter by date range before export
  - Format compatible with Costa Rica accounting software
  - Include summary row with totals
- **Priority:** MEDIUM (Growth Phase 2)

**FR-028: Gym Owner can identify late payers**
- **Journey:** Journey 6 (Analytics & Revenue Reporting)
- **Acceptance Criteria:**
  - Display list of members with overdue payments
  - Sort by days overdue (ascending/descending)
  - Show total amount overdue per member
  - Provide bulk "Send Reminder" action
  - Track reminder sent date
- **Priority:** HIGH (Growth Phase 2)

**FR-029: Staff can check in members at front desk**
- **Journey:** Journey 4 (Member Check-In)
- **Acceptance Criteria:**
  - Search member by name or scan member card
  - Display member photo and status (active/inactive/overdue)
  - Click "Check In" button to record attendance
  - Check-in completes in <30 seconds
  - Display check-in confirmation on screen
- **Priority:** HIGH (Growth Phase 2 - operations)

**FR-030: Gym Owner can schedule classes and assign instructors**
- **Journey:** Growth Phase 2 - Class Booking (new journey)
- **Acceptance Criteria:**
  - Create recurring class schedule (day, time, instructor, capacity)
  - Assign instructor to class
  - Set maximum capacity (e.g., 20 members)
  - Display class schedule on member portal
  - Allow members to book classes
- **Priority:** MEDIUM (Growth Phase 2)

### Vision Requirements (M13-M24+: Selective)

**FR-031: System can send WhatsApp notifications via WhatsApp Business API**
- **Journey:** Growth Phase 2+ - Multi-channel communication
- **Acceptance Criteria:**
  - Integrate WhatsApp Business API
  - Send payment reminders via WhatsApp (member opt-in required)
  - Send class booking confirmations via WhatsApp
  - Support member-initiated click-to-chat
  - Track WhatsApp message delivery status
- **Priority:** LOW (Vision - dependent on WhatsApp Business API approval)
- **Legal Note:** 80% of Costa Rica uses WhatsApp; no specific regulations beyond general data protection (Ley 8968)

**FR-032: Gym Owner can manage multiple gym locations**
- **Journey:** Vision - Multi-location expansion
- **Acceptance Criteria:**
  - Add multiple gym locations under one account
  - Each location has separate Hacienda credentials
  - Separate member lists per location
  - Consolidated revenue reporting across locations
  - Per-location staff access controls
- **Priority:** LOW (Vision - targets small chains)

### Functional Requirements Summary

**Total FRs:** 32
- **MVP (Critical/High):** 17 FRs (FR-001 to FR-017)
- **Growth Phase 1:** 8 FRs (FR-018 to FR-025)
- **Growth Phase 2:** 6 FRs (FR-026 to FR-030)
- **Vision:** 2 FRs (FR-031 to FR-032)

**Traceability Coverage:**
- ✅ Journey 1 (Initial Setup): FR-001, FR-002, FR-015, FR-016
- ✅ Journey 2 (Monthly E-Invoicing): FR-003, FR-004, FR-005, FR-006, FR-012, FR-013, FR-014, FR-021, FR-022
- ✅ Journey 3 (Payment Reconciliation): FR-018, FR-019, FR-020
- ✅ Journey 4 (Member Check-In): FR-007, FR-008, FR-012, FR-029
- ✅ Journey 5 (Self-Service Payment): FR-018, FR-022, FR-023, FR-024, FR-025
- ✅ Journey 6 (Analytics): FR-026, FR-027, FR-028
- ✅ Legal Compliance (Ley 8968): FR-009, FR-010, FR-011
- ✅ Essential UX: FR-013, FR-015, FR-016

**Success Criteria Coverage:**
- ✅ Setup <2 hours: FR-015
- ✅ Invoice approval <5 minutes: FR-004
- ✅ >95% acceptance rate: FR-004
- ✅ NPS >40: FR-017
- ✅ >30% annual contract adoption: FR-025

---

## Non-Functional Requirements

**Format:** "The system shall [metric] [condition] [measurement method]"
**Categories:** Performance, Security, Availability, Scalability, Compliance, Usability
**Testability:** All NFRs include measurable criteria

### Performance Requirements

**NFR-001: Invoice submission response time**
- The system shall submit e-invoices to Hacienda DGT and receive status response within 5 minutes for 95% of submissions as measured by application monitoring
- **Measurement:** APM tool (Application Performance Monitoring)
- **Target:** 95th percentile <5 minutes
- **Priority:** CRITICAL (Success Criteria requirement)

**NFR-002: Member search responsiveness**
- The system shall return member search results within 1 second for 95% of queries as measured by client-side performance monitoring
- **Measurement:** Browser performance API
- **Target:** 95th percentile <1 second
- **Priority:** HIGH (UX requirement for FR-008)

**NFR-003: Payment reconciliation speed**
- The system shall complete payment reconciliation (payment received → member account updated → invoice generated) within 5 minutes of Tilopay redirect confirmation for 95% of transactions as measured by workflow timing logs
- **Measurement:** Workflow event timestamps
- **Target:** 95th percentile <5 minutes
- **Priority:** HIGH (Growth Phase 1 - FR-020)

**NFR-004: Dashboard load time**
- The system shall load analytics dashboard with all KPIs within 3 seconds for 90% of requests as measured by server response time
- **Measurement:** Server logs and APM
- **Target:** 90th percentile <3 seconds
- **Priority:** MEDIUM (Growth Phase 2 - FR-026)

**NFR-005: Batch invoice generation performance**
- The system shall generate, sign, and submit 100 invoices (monthly billing cycle) within 30 minutes as measured by batch job execution time
- **Measurement:** Batch job logs
- **Target:** 100 invoices in <30 minutes
- **Priority:** HIGH (Growth Phase 1 automation - FR-022)

### Security Requirements

**NFR-006: Data encryption at rest**
- The system shall encrypt all personal data (member information, payment details, tax IDs) at rest using AES-256 encryption as verified by security audit
- **Measurement:** Security configuration audit
- **Standard:** AES-256
- **Priority:** CRITICAL (Ley 8968 compliance)

**NFR-007: Data encryption in transit**
- The system shall encrypt all data in transit using SSL/TLS 1.2 or higher as verified by SSL certificate validation
- **Measurement:** SSL Labs test (A+ rating)
- **Standard:** SSL/TLS 1.2+ (required for BAC Credomatic gateway)
- **Priority:** CRITICAL (Payment gateway and legal compliance)

**NFR-008: Digital certificate security**
- The system shall store gym owner digital certificates in encrypted format with password-protected access as verified by security audit
- **Measurement:** Security configuration review
- **Standard:** Encrypted storage + password protection
- **Priority:** CRITICAL (Hacienda compliance - FR-001)

**NFR-009: Authentication and access control**
- The system shall require authentication for all user actions and enforce role-based access control (gym owner, staff, member) as verified by penetration testing
- **Measurement:** Penetration test report
- **Standard:** Role-based access control (RBAC)
- **Priority:** HIGH (multi-user security)

**NFR-010: Payment data isolation (PCI DSS consideration)**
- The system shall NOT store credit card numbers, CVVs, or full payment credentials (delegated to Tilopay gateway) as verified by data flow audit
- **Measurement:** Data storage audit
- **Standard:** No raw payment data storage (Tilopay handles PCI compliance)
- **Priority:** CRITICAL (payment security - FR-018)

**NFR-011: Audit trail for data deletion**
- The system shall log all member data deletion actions with timestamp, user, and reason as verified by audit log review
- **Measurement:** Audit log verification
- **Standard:** Immutable audit log for data deletion
- **Priority:** HIGH (Ley 8968 compliance - FR-010, FR-011)

### Availability & Reliability Requirements

**NFR-012: System uptime**
- The system shall maintain 99.5% uptime during business hours (6 AM - 10 PM Costa Rica time) as measured by cloud provider SLA and uptime monitoring
- **Measurement:** Cloud provider SLA reports, Uptime Robot
- **Target:** 99.5% uptime (allows ~3.65 hours downtime per month)
- **Priority:** HIGH (Success Criteria - Technical Success)

**NFR-013: Hacienda invoice acceptance rate**
- The system shall achieve >95% first-submission acceptance rate from Hacienda DGT as measured by invoice submission logs
- **Measurement:** Invoice status tracking (Approved/Rejected ratio)
- **Target:** >95% acceptance rate
- **Priority:** CRITICAL (Success Criteria - Technical Success)

**NFR-014: Backup and disaster recovery**
- The system shall perform automated daily backups of all data with 24-hour recovery point objective (RPO) and 4-hour recovery time objective (RTO) as verified by disaster recovery testing
- **Measurement:** Backup logs and DR test results
- **Target:** RPO 24 hours, RTO 4 hours
- **Priority:** HIGH (data protection)

**NFR-015: Graceful degradation for Hacienda API outages**
- The system shall queue invoices locally when Hacienda DGT API is unavailable and auto-retry submission when API recovers as measured by queue monitoring
- **Measurement:** Queue depth monitoring, retry success rate
- **Target:** 100% of queued invoices eventually submitted when API recovers
- **Priority:** HIGH (reliability - handles external dependency failures)

### Scalability Requirements

**NFR-016: Concurrent user support**
- The system shall support up to 50 concurrent gym owners and 500 concurrent members without performance degradation as measured by load testing
- **Measurement:** Load test with JMeter or similar
- **Target:** 50 gym owners + 500 members concurrent (Year 1 target: 30-50 gyms with average 200 members each)
- **Priority:** MEDIUM (Year 1 scaling target)

**NFR-017: Multi-tenant data isolation**
- The system shall ensure complete data isolation between gym tenants (one gym cannot access another gym's data) as verified by penetration testing
- **Measurement:** Penetration test + data access audit
- **Standard:** Row-level security (RLS) or schema-per-tenant isolation
- **Priority:** CRITICAL (multi-tenant SaaS requirement)

**NFR-018: Database transaction volume**
- The system shall handle 10,000 invoice submissions per month (100 gyms × 100 invoices) without database performance degradation as measured by database monitoring
- **Measurement:** Database query performance metrics
- **Target:** <100ms average query response time at peak load
- **Priority:** MEDIUM (Year 1 scaling target)

**NFR-019: Horizontal scaling capability**
- The system shall support horizontal scaling to handle 10x growth (500 gyms, 100,000 members) through infrastructure configuration changes without code refactoring as verified by architecture review
- **Measurement:** Architecture design review
- **Target:** Scale to 10x through infrastructure (not code changes)
- **Priority:** LOW (long-term scaling)

### Compliance Requirements

**NFR-020: Ley 8968 (Data Protection) compliance**
- The system shall achieve 100% compliance with Ley 8968 data protection requirements (consent tracking, data export, deletion, security) as verified by legal compliance audit
- **Measurement:** Legal compliance checklist audit
- **Standard:** Ley 8968 (Costa Rica Data Protection Law)
- **Priority:** CRITICAL (legal requirement - FR-009, FR-010, FR-011)

**NFR-021: Hacienda v4.4 e-invoicing compliance**
- The system shall achieve 100% compliance with Hacienda v4.4 e-invoicing technical specification as verified by Hacienda sandbox testing
- **Measurement:** Hacienda sandbox approval rate + production validation
- **Standard:** Hacienda v4.4 XML schema (Resolution MH-DGT-RES-0027-2024)
- **Priority:** CRITICAL (legal requirement - mandatory September 2025)

**NFR-022: Electronic communications consent compliance**
- The system shall achieve 100% compliance with electronic communications laws (Laws 8968/7975/8642) for email, SMS, and WhatsApp marketing as verified by legal compliance audit
- **Measurement:** Legal compliance checklist audit
- **Standard:** Express written consent before first contact; honor STOP/CANCELAR/NO keywords for SMS; support HELP/AYUDA keywords (EN/ES)
- **Priority:** HIGH (legal requirement - FR-024, FR-031)

**NFR-023: 5-year invoice archival compliance**
- The system shall retain all e-invoices (XML and PDF) for minimum 5 years as required by Costa Rica tax law as verified by data retention policy audit
- **Measurement:** Data retention policy review + oldest invoice age check
- **Standard:** 5-year minimum retention
- **Priority:** HIGH (tax law compliance - FR-006)

**NFR-024: BCCR payment processing compliance**
- The system shall comply with BCCR payment processing regulations (Regulation 9831) through integration with licensed payment gateway (Tilopay) as verified by payment flow audit
- **Measurement:** Payment gateway license verification + transaction flow review
- **Standard:** BCCR Regulation 9831 (delegated to Tilopay gateway)
- **Priority:** HIGH (payment processing legal requirement)

### Usability Requirements

**NFR-025: Spanish-first interface**
- The system shall display all user-facing text in Spanish by default with 100% translation coverage as verified by UI review
- **Measurement:** UI text audit (% translated)
- **Target:** 100% Spanish coverage for gym owner and staff interfaces
- **Priority:** HIGH (market requirement - Costa Rica)

**NFR-026: Mobile responsiveness**
- The system shall display correctly on mobile devices (iOS/Android) with screen widths from 320px to 1920px as verified by responsive design testing
- **Measurement:** Browser responsive design testing (BrowserStack)
- **Target:** Support 320px (iPhone SE) to 1920px (desktop)
- **Priority:** HIGH (Essential UX - mobile-responsive web)

**NFR-027: Setup completion time**
- The system shall enable 90% of gym owners to complete Hacienda setup (company info → certificate → credentials → first invoice) in under 2 hours as measured by user analytics
- **Measurement:** User analytics (time from signup to first invoice submission)
- **Target:** 90% of users complete setup in <2 hours
- **Priority:** CRITICAL (Success Criteria - User Success)

**NFR-028: Simplified workflow states**
- The system shall display maximum 3 user-facing states for invoice workflow (Preparing, Sent, Approved/Rejected) hiding Odoo's internal 8 states as verified by UI review
- **Measurement:** UI state count audit
- **Target:** 3 states maximum
- **Priority:** HIGH (Essential UX - Odoo simplification, FR-013)

**NFR-029: Video tutorial availability**
- The system shall provide minimum 5 Spanish-language video tutorials (setup, invoicing, payment processing, troubleshooting, member management) with average 5-10 minute duration as verified by knowledge base audit
- **Measurement:** Knowledge base content inventory
- **Target:** 5+ videos in Spanish, 5-10 minutes each
- **Priority:** MEDIUM (Essential UX - self-service onboarding, FR-016)

**NFR-030: Support response time**
- The system shall respond to user support requests within 24 hours during business days as measured by support ticket response time analytics
- **Measurement:** Support ticket SLA tracking
- **Target:** <24 hours first response time
- **Priority:** MEDIUM (MVP requirement)

### Deployment & Infrastructure Requirements

**NFR-031: Multi-tenant SaaS architecture**
- The system shall implement multi-tenant SaaS architecture where single Odoo instance serves multiple gym customers with data isolation as verified by architecture review
- **Measurement:** Architecture design document review
- **Standard:** Multi-tenant SaaS pattern (shared infrastructure, isolated data)
- **Priority:** CRITICAL (deployment model)

**NFR-032: Cloud infrastructure deployment**
- The system shall deploy on cloud infrastructure (AWS, GCP, or Azure) with auto-scaling capability as verified by infrastructure configuration review
- **Measurement:** Infrastructure-as-Code (IaC) review
- **Target:** Cloud-native deployment with auto-scaling
- **Priority:** HIGH (scalability and reliability)

**NFR-033: Odoo 19 Enterprise compatibility**
- The system shall maintain compatibility with Odoo 19 Enterprise through module inheritance (extends POS, CRM, Sales, Accounting, Membership modules) without core modifications as verified by code review
- **Measurement:** Code architecture review
- **Standard:** Module inheritance only (no core Odoo modifications)
- **Priority:** CRITICAL (platform foundation)

### Non-Functional Requirements Summary

**Total NFRs:** 33
- **Performance:** 5 NFRs (NFR-001 to NFR-005)
- **Security:** 6 NFRs (NFR-006 to NFR-011)
- **Availability & Reliability:** 4 NFRs (NFR-012 to NFR-015)
- **Scalability:** 4 NFRs (NFR-016 to NFR-019)
- **Compliance:** 5 NFRs (NFR-020 to NFR-024)
- **Usability:** 6 NFRs (NFR-025 to NFR-030)
- **Deployment & Infrastructure:** 3 NFRs (NFR-031 to NFR-033)

**Success Criteria Coverage:**
- ✅ Technical Success (Uptime 99.5%): NFR-012
- ✅ Technical Success (Invoice approval <5 minutes): NFR-001
- ✅ Technical Success (>95% acceptance rate): NFR-013
- ✅ Technical Success (Setup <2 hours): NFR-027
- ✅ User Success (Setup <2 hours): NFR-027

**Legal Compliance Coverage:**
- ✅ Ley 8968 (Data Protection): NFR-020, NFR-006, NFR-007
- ✅ Hacienda v4.4 (E-Invoicing): NFR-021, NFR-023
- ✅ Electronic Communications Laws: NFR-022
- ✅ BCCR Payment Regulations: NFR-024
- ✅ BAC Credomatic SSL/TLS: NFR-007

**Architecture Decision Support:**
- ✅ Multi-tenant SaaS: NFR-031, NFR-017
- ✅ Odoo 19 Enterprise: NFR-033
- ✅ Cloud Infrastructure: NFR-032
- ✅ Horizontal Scaling: NFR-019
- ✅ Payment Gateway Delegation: NFR-010, NFR-024

---

## Legal & Regulatory Compliance Requirements

**Status**: Research Complete - Requirements Documented

### 1. Data Privacy - Ley No. 8968 (Data Protection Law)

**Governing Authority:** PRODHAB (Agency for the Protection of Individual's Data)

**Core Requirements:**
- **Express Consent**: Informed, express consent required from data subjects before processing personal data
- **Data Quality**: Personal data must be accurate, complete, and kept up to date
- **Security Measures**: Appropriate technical and organizational security measures mandatory
- **Transparency**: Data subjects must be informed about data processing purposes before consent
- **International Transfers**: Transferring personal data to third countries requires data subject consent

**Penalties:**
- Fines: 5 to 30 base salaries (approximately USD 4,000 to USD 24,000)
- Marketing violations: 0.025% to 0.5% of annual company income

**Upcoming Changes:**
- GDPR-aligned Bill No. 23097 positioned for Q1 2025 approval, implementation expected 2026
- Will modernize enforcement and align with international standards

**Sources:** [Law 8968](https://globalprivacylaws.com/laws/law-8968/), [DLA Piper Guide](https://www.dlapiperdataprotection.com/index.html?t=law&c=CR)

### 2. E-Invoicing - Resolution MH-DGT-RES-0027-2024 (v4.4)

✅ **Covered in MVP Requirements** - Hacienda v4.4 compliance fully specified in Product Scope

### 3. Payment Processing Regulations

**Governing Authority:** BCCR (Central Bank of Costa Rica) and SUGEF (Superintendent of Financial Entities)

**Key Regulations:**
- **Regulation 9831**: Establishes maximum commissions for card system transactions to promote efficiency, security, and lowest possible costs
- **BCCR Authority**: Regulates SINPE national payment system, including real-time transfers and payment card systems
- **SUGEF Oversight**: Supervises and regulates all financial intermediaries (banks, non-banking financial companies)
- **Interchange Fees**: BCCR sets maximum acquiring and interchange fees, transactional limits, card system requirements
- **Interest Rate Controls**: BCCR establishes maximum loan/microcredit rates biannually for consumer protection

**Payment Gateway Requirements:**
- Banking entity approval required for payment processing
- Businesses must present RUT (single tax registration) and shareholder registry (legal entities)
- SSL/TLS 1.2 certificate mandatory for fraud protection
- Compliance with PCI DSS when handling card data (gateway provider responsibility)

**Sources:** [Banking Regulation 2025](https://practiceguides.chambers.com/practice-guides/banking-regulation-2025/costa-rica), [Digital Payments Framework](https://generisonline.com/understanding-the-regulatory-framework-for-digital-payments-and-fintech-companies-in-costa-rica/)

### 4. Electronic Communications Laws

**Governing Laws:** Law 8968 (Data Protection), Law 7975 (Undisclosed Information), Law 8642 (Telecommunications Act)

**Marketing Communication Requirements:**
- **Express Written Consent**: Required for all marketing via email, phone, and SMS before first contact
- **Existing Customer Exception**: If email provided during purchase and customer informed of future marketing, consent presumed for same product category
- **Opt-Out Mechanism**: All marketing communications must clearly identify sender and include unsubscribe method

**SMS Marketing Specific:**
- Explicit opt-in consent required
- Must honor keywords: STOP, CANCELAR, NO (opt-out)
- Must support keywords: HELP, AYUDA (assistance) with business identification and contact details
- Keyword support required in both English and Spanish

**WhatsApp Business:**
- No specific WhatsApp regulations separate from general telecommunications and data protection laws
- General Law 8968 consent requirements apply
- 80% of Costa Rica population uses WhatsApp (primary business communication channel)

**Enforcement:**
- Marketing consent violations: Fines 0.025% to 0.5% of company income from last fiscal year
- SUTEL (telecommunications authority) oversees SMS communications and marketing activities

**Sources:** [Electronic Marketing Costa Rica](https://www.dlapiperdataprotection.com/index.html?t=electronic-marketing&c=CR), [Costa Rica SMS Guide](https://www.sent.dm/resources/costa-rica-sms-guide)

### 5. Multi-Tenant Data Isolation

**Requirements under Ley 8968:**
- Personal data databases must implement appropriate security measures
- Cross-tenant data exposure constitutes data breach with penalties USD 4,000-24,000
- Technical and organizational measures required to prevent unauthorized access
- Constitutional Article 24 guarantees privacy and communications secrecy

**Implementation Obligations:**
- Database-level tenant isolation
- Access control enforcement per tenant
- Audit logging for data access
- Encryption for data at rest and in transit

### 6. SaaS/Software Consumer Protection

**Requirements:**
- Terms of service must comply with Costa Rican consumer protection laws
- Privacy policy required (Ley 8968 compliance)
- Service level agreements (SLA) for uptime commitments
- Data portability and deletion rights for customers

### 7. Fitness Industry Considerations

**Health Data:**
- Member fitness data may constitute sensitive personal data under Ley 8968
- Enhanced consent requirements for health-related information
- Secure storage and access controls mandatory

**Liability:**
- Standard business liability insurance recommended
- Terms of service should address gym owner responsibility for member safety
- Platform liability limited to software provision (not gym operations)

---

## Technical Dependencies & Assumptions

**Payment Gateway Dependency:**
- **SINPE Móvil Integration**: Requires payment gateway partner (Tilopay or similar)
- **Direct Bank API**: NOT AVAILABLE for SINPE Móvil reconciliation
- **Vendor Dependency**: Tied to Tilopay's uptime, fees, API changes, terms of service
- **Transaction Fees**: Tilopay charges 2-3% per transaction (research exact pricing)

**Pre-MVP Research:**
- [ ] Tilopay API documentation review
- [ ] Tilopay pricing structure (transaction fees, monthly costs)
- [ ] Tilopay partnership terms and SLA
- [✅] **BAC Credomatic Gateway Evaluation (COMPLETE)**:
  - **Business Requirements**: Banking entity approval required; must present RUT (single tax registration) and shareholder registry (for legal entities) for bank approval
  - **Technical Requirements**: SSL/TLS 1.2 certificate mandatory (without it, gateway works but no fraud protection); API credentials (key and secret) from merchant account admin panel
  - **Integration Methods**: e-Socket and 3D Secure with browser redirect capability; supports Verify by Visa and MasterCard SecureCode
  - **Developer Resources**: BAC API Center at developers.baccredomatic.com provides digital tools with banking security
  - **Platform Support**: Official integrations for WooCommerce 5.0+, Magento 2 (Cardinal API), and custom implementations
  - **Regional Coverage**: Operates throughout Central America; supports most major credit and debit cards
  - **Sources**: [Online Payment Processing Costa Rica](https://elcolectivo506.com/online-payment-processing-in-costa-rica-what-small-business-owners-need-to-know/?lang=en), [BAC API Center](https://developers.baccredomatic.com/)
- [ ] Competitor payment gateway analysis (LatinsoftCR, CrossHero integration status)

---

**END OF DOCUMENT**
