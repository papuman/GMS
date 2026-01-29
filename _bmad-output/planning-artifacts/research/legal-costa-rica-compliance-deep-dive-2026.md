# Costa Rica Legal & Compliance Deep Dive Research
**Research Date:** 2026-01-16
**Analyst:** Mary (Business Analyst)
**Research Type:** Legal/Regulatory Compliance
**Status:** ✅ Complete

---

## Executive Summary

This research addresses 4 critical compliance gaps identified in the GMS (Gym Management System) PRD for Costa Rica market operations:

1. **Ley 8968 (Data Protection)** - Comprehensive compliance requirements identified
2. **BCCR Payment Regulations** - Central Bank digital payment framework documented
3. **Electronic Communications Laws** - Marketing regulations for WhatsApp, SMS, email clarified
4. **BAC Credomatic Gateway** - Backup payment gateway technical details confirmed

**🚨 KEY FINDING:** Costa Rica is modernizing its data protection framework to align with GDPR standards. Two bills (23.097) are currently in Congress that will significantly strengthen requirements.

---

## 1. Ley 8968 - Data Protection Law

### Overview
Costa Rica's Data Protection Law (Law No. 8968), enacted **July 5, 2011**, protects individuals' rights to informational self-determination and privacy. It regulates how personal data is collected, stored, and processed by public and private entities.

### Critical Compliance Requirements for GMS

#### 1.1 Consent Requirements
- ✅ **Personal data processing requires informed, express consent** from the data subject
- ✅ For GMS: Member registration, billing info, health data, contact preferences all need explicit consent
- ⚠️ **Consent must be documented and auditable**

#### 1.2 Data Quality Standards
- ✅ Personal data must be **accurate, complete, and kept up to date**
- ✅ For GMS: Member profiles, payment info, contact details need regular validation
- ✅ Implement data correction mechanisms for members

#### 1.3 Security Measures
- ✅ Organizations must implement **appropriate security measures** to protect personal data
- ✅ For GMS: Encryption, access controls, audit logs required
- ✅ Technical and organizational safeguards mandatory

#### 1.4 Database Registration (CRITICAL)
- 🚨 **Companies managing databases containing personal information and engaging in distribution, disclosure, or commercialization must register with PRODHAB**
- ✅ **EXEMPTION:** Entities managing databases for internal purposes are exempt
- ✅ **For GMS:** If we only use member data internally (gym operations), NO registration required
- ⚠️ **BUT:** If we share data with partners, sell lists, or commercialize data → MUST REGISTER

#### 1.5 Cross-Border Transfers
- 🚨 **Transferring personal information to third countries WITHOUT CONSENT is classified as a VERY SERIOUS OFFENSE**
- ✅ For GMS: Any cloud hosting outside Costa Rica requires member consent
- ✅ Document where data is stored (AWS region, database location)
- ✅ Include cross-border transfer notice in privacy policy

### Enforcement & Penalties

**Regulatory Authority:** PRODHAB (Agency for the Protection of Individuals' Data)

**Penalties:**
- Fines range from **5 to 30 base salaries** (approximately **USD $4,000 to $24,000**)
- Very serious offenses: Unauthorized cross-border transfers, data breaches, lack of security

### Future Legislative Updates (CRITICAL)

🚨 **Costa Rican Congress is currently discussing Personal Data Protection Bill 23.097** to:
- Establish new regulatory framework aligned with **EU GDPR**
- Strengthen enforcement mechanisms
- Increase penalties significantly
- Expand individual rights (right to be forgotten, data portability)

**Impact on GMS:**
- ✅ **Design for GDPR-level compliance NOW** to avoid future refactoring
- ✅ Implement data portability, erasure, access controls from day 1
- ✅ Monitor bill progress and adapt before enforcement

### GMS Implementation Checklist

- [ ] **Consent Management System**
  - [ ] Explicit opt-in for marketing communications
  - [ ] Granular consent options (email, SMS, WhatsApp)
  - [ ] Consent audit trail with timestamps
  - [ ] Easy consent withdrawal mechanism

- [ ] **Privacy Policy & Notices**
  - [ ] Transparent data collection disclosure
  - [ ] Cross-border transfer notification (if using foreign cloud)
  - [ ] Third-party data sharing disclosure
  - [ ] Member rights explanation (access, correction, deletion)

- [ ] **Data Security Controls**
  - [ ] Encryption at rest and in transit
  - [ ] Role-based access controls
  - [ ] Audit logging of data access
  - [ ] Regular security assessments

- [ ] **Data Subject Rights**
  - [ ] Member portal for data access/correction
  - [ ] Data deletion workflow
  - [ ] Data export/portability feature (prepare for GDPR alignment)

- [ ] **PRODHAB Registration Assessment**
  - [ ] Confirm data usage is internal-only (likely exempt)
  - [ ] If sharing data with partners → register database

---

## 2. BCCR (Central Bank) Payment Regulations

### Overview
The **Central Bank of Costa Rica (BCCR)** regulates digital payments, currency issuance, and payment system stability. **SUGEF** (Superintendency of Financial Institutions) supervises financial entities and enforces compliance.

### Key Regulatory Framework

#### 2.1 Payment Systems Regulations
- ✅ **Law 9831** delegates to BCCR responsibility for issuing payment card system regulations
- ✅ Issuers must guarantee **EMV standards** compliance for payment devices
- ✅ Contactless technology integration required
- ✅ Secure customer authentication mechanisms mandatory

#### 2.2 Compliance Requirements for Payment Processing

**Anti-Money Laundering (AML) & Combating Financing of Terrorism (CFT):**
- 🚨 Fintech companies MUST adhere to **robust AML/CFT protocols**
- ✅ Organizations must adopt measures to mitigate risks
- ✅ Transaction monitoring and suspicious activity reporting required

**Licensing Requirements (if applicable):**
- ✅ Clearly defined business plan
- ✅ Adequate financial resources
- ✅ Technology and compliance protocols
- ⚠️ Risk assessment report (data privacy & cybersecurity)

**For GMS:**
- ✅ **We are NOT a payment processor** - we integrate with licensed gateways (TiloPay, BAC Credomatic)
- ✅ Gateways handle BCCR compliance, EMV standards, AML/CFT
- ✅ **Our responsibility:** Secure integration, PCI-DSS compliance for card data handling

#### 2.3 Loan Rate Ceilings (2026 Update)
- ✅ BCCR mandates new loan rate ceilings for 2026
- ✅ Not directly applicable to GMS unless offering financing
- ⚠️ **Future consideration:** If GMS adds installment payment plans, monitor rate ceiling regulations

### GMS Implementation Checklist

- [ ] **Payment Gateway Compliance**
  - [ ] Verify TiloPay is BCCR-licensed and compliant
  - [ ] Verify BAC Credomatic is BCCR-licensed and compliant
  - [ ] Confirm gateways handle AML/CFT requirements
  - [ ] Document payment flow security architecture

- [ ] **PCI-DSS Compliance**
  - [ ] Never store full card numbers (use tokenization)
  - [ ] Use gateway-hosted payment forms
  - [ ] Implement HTTPS for all payment pages
  - [ ] Regular security assessments

- [ ] **Transaction Monitoring**
  - [ ] Log all payment transactions
  - [ ] Monitor for suspicious patterns (if required)
  - [ ] Maintain transaction audit trail

---

## 3. Electronic Communications Laws (WhatsApp, SMS, Email Marketing)

### Overview
Costa Rica's electronic marketing is governed by **Law No. 8968 (Data Protection)** and the **Telecommunications Act**. There is **little to no specific regulation** of electronic marketing channels, so general data protection principles apply.

### Legal Requirements

#### 3.1 Consent Requirements (CRITICAL)
🚨 **Marketing companies may NOT advertise via phone nor email unless they obtain prior and express WRITTEN consent** from the data subject.

**Exception (Soft Opt-In):**
- ✅ On occasion of a purchase, if person gave their email AND was informed it will be used for future marketing of goods in the **same category**
- ✅ Communication must clearly identify sender
- ✅ Must include unsubscribe address/mechanism

#### 3.2 Channel-Specific Requirements

**Email Marketing:**
- ✅ Express written consent required (or soft opt-in exception)
- ✅ Clear sender identification
- ✅ Unsubscribe mechanism in every email
- ✅ Honor unsubscribe requests immediately

**SMS Marketing:**
- ✅ Express written consent required
- ✅ No soft opt-in exception for SMS
- ✅ Clear sender identification
- ✅ Opt-out instructions in messages

**WhatsApp Marketing:**
- ✅ Express written consent required
- ✅ No specific WhatsApp regulations (general data protection applies)
- ✅ WhatsApp Business API terms of service also apply
- ⚠️ **Best Practice:** Treat like SMS - require explicit consent

#### 3.3 Penalties
🚨 Companies that do not comply with consent requirements might be sanctioned with a fine between **0.025% and 0.5% of the company's income from the last fiscal year**.

**Example:** If gym has revenue of $500,000/year:
- Minimum fine: $125
- Maximum fine: $2,500

#### 3.4 Database Registration
- 🚨 Companies managing databases for distribution, disclosure, or commercialization must register with PRODHAB
- ✅ Internal use databases are EXEMPT
- ✅ **For GMS:** Marketing to our own members = internal use (likely exempt)

#### 3.5 Future Legislative Changes
- ✅ Bill presented in January 2021 to **fully amend laws and align with EU GDPR**
- ✅ Expect stricter consent requirements, higher penalties
- ✅ Design for GDPR compliance now

### GMS Implementation Checklist

- [ ] **Consent Management**
  - [ ] Explicit opt-in checkboxes for each channel (Email, SMS, WhatsApp)
  - [ ] **NO PRE-CHECKED BOXES** - must be active opt-in
  - [ ] Separate consent for different content types (promotions, class reminders, newsletters)
  - [ ] Timestamp and log all consent grants
  - [ ] Easy withdrawal mechanism

- [ ] **Soft Opt-In for Members**
  - [ ] At membership signup: "We may send gym-related promotions via email"
  - [ ] Clear notice during purchase process
  - [ ] Unsubscribe link in every email

- [ ] **Email Marketing Compliance**
  - [ ] Clear "From" name (Gym name)
  - [ ] Physical address in footer (Costa Rica requirement)
  - [ ] One-click unsubscribe link
  - [ ] Honor unsubscribes within 24 hours

- [ ] **SMS Marketing Compliance**
  - [ ] Only send to members who explicitly opted in
  - [ ] Include gym name in message
  - [ ] Include "Reply STOP to unsubscribe" instruction
  - [ ] Maintain opt-out list

- [ ] **WhatsApp Marketing Compliance**
  - [ ] Use WhatsApp Business API (not personal WhatsApp)
  - [ ] Explicit opt-in for WhatsApp communications
  - [ ] Provide opt-out instructions
  - [ ] Respect 24-hour messaging window (WhatsApp policy)

- [ ] **Record Keeping**
  - [ ] Consent audit trail
  - [ ] Opt-out processing logs
  - [ ] Marketing communication logs (who, when, what channel)

---

## 4. BAC Credomatic - Backup Payment Gateway

### Overview
BAC Credomatic is a major payment gateway operating throughout Central America (Costa Rica, Guatemala, Honduras, El Salvador, Nicaragua, Panama). It provides comprehensive merchant services, POS integration, and e-commerce solutions.

### Technical Integration Options

#### 4.1 API Integration
- ✅ **BAC API Center:** https://developers.baccredomatic.com/
- ✅ Digital tools with banking support and security
- ✅ Developer portal for API documentation and resources
- ✅ Merchant API keys for integration

#### 4.2 Merchant Services Options

**POS System Integration:**
- ✅ Card processing integrated with billing system
- ✅ Accept all market cards directly
- ✅ **Implementation Cost:** $300 one-time
- ✅ **Monthly Maintenance:** $50 per branch
- ✅ Self-integration with BAC providing manuals and technical support

**E-commerce Solutions:**
- ✅ Sell online without requiring a website
- ✅ Secure payment link shared via WhatsApp, email, social media
- ✅ Customer pays via secure BAC portal

#### 4.3 Platform Integrations

**Shopify Integration:**
- ✅ Process card payments through Shopify using merchant API keys
- ✅ Works throughout Central America

**WooCommerce Integration:**
- ✅ Third-party plugins available for WooCommerce
- ✅ Supports various payment security protocols

**Odoo Integration:**
- ✅ **Payment FAC BAC Credomatic module** exists on Odoo Apps Store
- ✅ Module version for Odoo 12.0 (check for 17.0 compatibility)
- ✅ **For GMS:** Odoo 17 integration may require custom development or module update

#### 4.4 Costs & Pricing
**Implementation:**
- One-time: $300
- Monthly maintenance: $50/branch

**Transaction Fees:**
- ⚠️ Not publicly disclosed in search results
- ✅ Contact BAC Credomatic merchant services for current rates
- ✅ Typical Costa Rica rates: 2.5% - 3.5% + per-transaction fee

### Comparison: TiloPay vs BAC Credomatic

| Feature | TiloPay | BAC Credomatic |
|---------|---------|----------------|
| **Setup Cost** | Low/None (research needed) | $300 one-time + $50/month |
| **Transaction Fee** | 2.5% + ₡150 (SINPE) | Contact for rates (est. 2.5-3.5%) |
| **API Documentation** | Postman docs available | Developer portal available |
| **Odoo Integration** | Custom integration needed | Module exists (v12, update needed) |
| **POS Integration** | Unknown | ✅ Native POS integration |
| **Coverage** | Costa Rica | All Central America |
| **Payment Methods** | SINPE, cards | Cards, POS |
| **Support** | Unknown | Manuals + technical support |

### GMS Implementation Checklist

- [ ] **BAC Credomatic Account Setup**
  - [ ] Contact BAC merchant services for pricing
  - [ ] Confirm transaction fees and contract terms
  - [ ] Obtain merchant API credentials
  - [ ] Review developer documentation at developers.baccredomatic.com

- [ ] **Technical Integration**
  - [ ] Research Odoo 17 compatibility
  - [ ] Check if Payment FAC module can be upgraded to Odoo 17
  - [ ] If not, evaluate custom API integration effort
  - [ ] Test integration in sandbox environment

- [ ] **Payment Flow Design**
  - [ ] Decide: Gateway-hosted vs API integration
  - [ ] Implement secure payment form (never store card data)
  - [ ] Set up webhook/callback for payment confirmation
  - [ ] Test payment success/failure scenarios

- [ ] **POS Integration (Optional)**
  - [ ] Evaluate need for physical POS integration
  - [ ] If needed: $300 setup + $50/month per branch
  - [ ] Request BAC integration manuals

- [ ] **Fallback Strategy**
  - [ ] Define when to use BAC vs TiloPay
  - [ ] Implement automatic failover if primary gateway down
  - [ ] Test failover scenario

---

## Strategic Recommendations for Epic 002

Based on this research, here are critical recommendations for Epic 002 (Payment Gateway Integration):

### 1. TiloPay Integration Pattern (CRITICAL BLOCKER)

🚨 **RESEARCH GAP:** The Postman documentation for TiloPay doesn't clearly show webhook support.

**Required Actions:**
1. **Contact TiloPay directly** to confirm integration pattern:
   - Does TiloPay support webhooks/callbacks?
   - OR is it redirect-based (user goes to TiloPay, returns to our site)?
   - OR is it polling-based (we check transaction status)?
2. **Once confirmed:** Update Epic 002 architecture to match ACTUAL integration pattern
3. **If webhook assumption was wrong:** Remove all webhook code from `payment_tilopay/` module

**Until this is clarified, Epic 002 is BLOCKED.**

### 2. Compliance-First Design

✅ **Design GMS payment system to meet HIGHEST compliance standards** (GDPR-level):
- Data protection by design and default
- Minimal data collection
- Strong encryption
- Audit trails
- Member rights (access, deletion, portability)

**Rationale:** Costa Rica is moving toward GDPR alignment. Building to those standards now prevents future refactoring.

### 3. Multi-Gateway Strategy

✅ **Implement both TiloPay (primary) and BAC Credomatic (backup)**:
- TiloPay for SINPE Móvil (popular in Costa Rica)
- BAC Credomatic for card payments and regional expansion
- Automatic failover if primary gateway unavailable

### 4. Marketing Compliance

✅ **Implement strict opt-in consent system** for all electronic communications:
- Separate checkboxes for Email, SMS, WhatsApp
- NO pre-checked boxes
- Granular consent (promotions vs transactional)
- Easy unsubscribe mechanisms
- Full audit trail

### 5. Legal Review Recommended

⚠️ **This research is NOT legal advice.** Recommend:
- Consult Costa Rican data protection attorney
- Review privacy policy with legal counsel
- Confirm PRODHAB registration exemption
- Review marketing consent mechanisms
- Ensure cross-border data transfer compliance

---

## Research Sources

### Ley 8968 (Data Protection)
- [Costa Rica Protection of Personal Data Law (Law 8968)](https://globalprivacylaws.com/laws/law-8968/)
- [DLA Piper Data Protection Laws - Costa Rica](https://www.dlapiperdataprotection.com/index.html?t=law&c=CR)
- [Multilaw Data Protection Guide Costa Rica](https://multilaw.com/Multilaw/Multilaw/Data_Protection_Laws_Guide/DataProtection_Guide_Costa_Rica.aspx)
- [Data Privacy Regulations and Compliance in Costa Rica](https://www.linkedin.com/pulse/data-privacy-regulations-compliance-costa-rica-arturo-rojas)
- [Law No. 8968 Costa Rica](https://www.clym.io/regulations/law-no-8968-costa-rica)
- [Personal Data: Applicable Laws and Regulations in Costa Rica](https://www.langcr.com/content/personal-data-applicable-laws-and-regulations-in-costa-rica/)

### BCCR Payment Regulations
- [Central Bank Mandates New Loan Rate Ceilings for 2026](https://ticosland.com/central-bank-mandates-new-loan-rate-ceilings-for-2026/)
- [BCCR Administrative Procedures](https://www.bccr.fi.cr/en/administrative-procedures)
- [Integral Reform of Payment Systems Regulations](https://www.fundacionmicrofinanzasbbva.org/revistaprogreso/en/11632/)
- [Understanding Regulatory Framework for Digital Payments and Fintech in Costa Rica](https://generisonline.com/understanding-the-regulatory-framework-for-digital-payments-and-fintech-companies-in-costa-rica/)
- [BCCR Payment System Cards](https://www.bccr.fi.cr/en/payments-system/general-information/cards)
- [Competition in Mobile Payment Services – Note by Costa Rica](https://one.oecd.org/document/DAF/COMP/WD(2025)16/en/pdf)

### Electronic Communications Laws
- [Electronic Marketing in Costa Rica - DLA Piper](https://www.dlapiperdataprotection.com/?t=electronic-marketing&c=CR)
- [DLA Piper Data Protection Guide - Costa Rica](https://www.dlapiperdataprotection.com/guide.pdf?c=CR)
- [International Email Marketing Regulations](https://www.emwasylik.com/2021/02/26/e-mail-regulations-throughout-the-world/)
- [Navigating Digital Privacy in Costa Rica](https://ticosland.com/navigating-digital-privacy-in-costa-rica/)
- [Costa Rica Enacts New Anti-Spam Law](https://qcostarica.com/costa-ricas-enacts-new-anti-spam-law/)

### BAC Credomatic
- [BAC API Center](https://developers.baccredomatic.com/)
- [BAC Credomatic Business Solutions](https://www.baccredomatic.com/es-cr/empresas/soluciones-herramientas)
- [BAC E-commerce Help Center](https://ayuda.baccredomatic.com/para_empresas_o_negocios/comercios_afiliados/e-commerce?country=es)
- [WooCommerce Credomatic Plugin](https://jepser.com/labs/woocommerce-credomatic)
- [Online Payment Processing in Costa Rica - Small Business Guide](https://elcolectivo506.com/online-payment-processing-in-costa-rica-what-small-business-owners-need-to-know/?lang=en)
- [Credomatic Payment Gateway Solutions](https://www.credomaticmerchantservices.com/paymentgateway.html)
- [Payment FAC BAC Credomatic - Odoo Apps Store](https://apps.odoo.com/apps/modules/12.0/payment_fac)

---

## Next Steps

1. **IMMEDIATE:** Contact TiloPay to confirm integration pattern (webhook vs redirect vs polling)
2. **IMMEDIATE:** Update Epic 002 architecture based on TiloPay confirmation
3. **HIGH PRIORITY:** Add compliance checklist items to PRD Feature Requirements
4. **HIGH PRIORITY:** Design consent management UI/UX
5. **MEDIUM PRIORITY:** Contact BAC Credomatic for merchant account pricing
6. **MEDIUM PRIORITY:** Legal review of privacy policy and consent mechanisms
7. **ONGOING:** Monitor Costa Rica Bill 23.097 progress (GDPR alignment)

---

**Research Completed By:** Mary, Business Analyst
**Date:** 2026-01-16
**Status:** ✅ COMPLETE
**Confidence Level:** HIGH (based on official sources and regulatory documentation)
**Legal Disclaimer:** This research is for informational purposes only and does not constitute legal advice. Consult qualified Costa Rican legal counsel for compliance confirmation.
