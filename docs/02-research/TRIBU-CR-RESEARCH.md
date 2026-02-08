# TRIBU-CR & Tax Declarations Research for GMS
**Created:** December 28, 2025
**Last Updated:** February 6, 2026
**Purpose:** Comprehensive reference on TRIBU-CR platform, tax declarations, and compliance requirements
**For:** Gym Management System (GMS) on Odoo 19

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [What is TRIBU-CR?](#1-what-is-tribu-cr)
3. [All 27 Modules](#2-all-27-modules)
4. [Vector Fiscal](#3-vector-fiscal)
5. [Cuenta Integral Tributaria](#4-cuenta-integral-tributaria)
6. [Oficina Virtual (OVi)](#5-oficina-virtual-ovi)
7. [Pre-filled Declarations](#6-pre-filled-declarations)
8. [TicoFactura (Free Government Invoicing)](#7-ticofactura-free-government-invoicing)
9. [TRIBU-CR vs Commercial Tools](#8-tribu-cr-vs-commercial-tools)
10. [Tax Reports & Declarations](#9-tax-reports--declarations)
11. [D-150 (Monthly IVA)](#10-d-150-formerly-d-104--monthly-iva-declaration)
12. [D-101/102 (Annual Income Tax)](#11-d-101102--annual-income-tax)
13. [D-151/D-270 (Informative Declaration)](#12-d-151d-270--informative-declaration)
14. [D-155 & Other Declarations](#13-d-155--other-declarations)
15. [Penalties & Sanctions](#14-penalties--sanctions-2026-base-salary-462200)
16. [Filing Calendar 2026](#15-filing-calendar-2026)
17. [E-Invoice → Declaration Flow](#16-e-invoice--declaration-flow)
18. [GMS-Specific Relevance](#17-gms-specific-relevance)
19. [Impact on Our Module](#18-impact-on-our-module)
20. [How the Integration Works](#19-how-the-integration-works)
21. [Electronic Invoicing v4.4](#20-electronic-invoicing-v44)
22. [Requirements for GMS](#21-requirements-for-gms)
23. [Sources & References](#22-sources--references)

---

## Executive Summary

**TRIBU-CR** (Sistema Integrado de Gestión Tributaria) is Costa Rica's new unified tax administration platform, launched **October 6, 2025**. It replaces four legacy systems (ATV, TRAVI, EDDI-7, Decla@7) into a single platform serving 800,000+ taxpayers.

**Key takeaway for GMS:** The e-invoicing API (`api.comprobanteselectronicos.go.cr`) is **unchanged** — no migration needed for our module. TRIBU-CR consumes e-invoice data automatically to pre-fill tax declarations. The main impact is on the *declaration side* (new form codes, new frequencies, new portal for filing).

**TRIBU-CR is far more powerful than commercial tools** like GTI, Allegra, or Facturele. It has access to 90%+ of all economic transactions in the country, pre-fills declarations from 1.2 billion monthly e-invoices, and provides a unified tax account with automatic credit compensation — capabilities no commercial tool can replicate.

---

## 1. What is TRIBU-CR?

### Overview

TRIBU-CR (Sistema Integrado de Administración Tributaria) is Costa Rica's new digital tax administration platform. It went live **October 6, 2025**, replacing the old ATV (Administración Tributaria Virtual) system and consolidating four separate legacy systems into one.

| Fact | Detail |
|------|--------|
| **Launch** | October 6, 2025 |
| **ATV shutdown** | July 18, 2025 (e-invoice functions maintained until Aug 31) |
| **Scope** | 800,000+ taxpayers |
| **Total modules** | 27 planned, 10 launched in Phase 1 (~29%) |
| **Full completion** | Gradual rollout through 2028 |
| **Portal URL** | https://ovitribucr.hacienda.go.cr/ |
| **Resolution** | MH-DGT-RES-0011-2025 |

### Systems Replaced

| Legacy System | Function | Replaced By |
|---------------|----------|-------------|
| **ATV** (Administración Tributaria Virtual) | Tax filing portal | TRIBU-CR Declaraciones |
| **TRAVI** | Tax procedure tracking | TRIBU-CR Expediente Electrónico |
| **EDDI-7** | Declaration data entry | TRIBU-CR Declaraciones (online-only) |
| **Decla@7** | Offline declaration tool | Eliminated — online-only now |

### Key Capabilities
- **Pre-filled Tax Returns:** Automatically populates VAT and other tax returns from 1.2 billion monthly e-invoices
- **Vector Fiscal:** AI-driven personalized tax obligation profiles
- **Cuenta Integral:** Real-time unified tax account with automatic credit compensation
- **TicoFactura:** Free government-provided e-invoicing service (v4.4 compliant)
- **AI Integration:** Uses artificial intelligence for tax audits and compliance monitoring
- **Online-Only:** No more offline Excel submissions — all declarations filed through the portal

---

## 2. All 27 Modules

### Phase 1 — Launched October 6, 2025 (10 modules)

| # | Module | Description |
|---|--------|-------------|
| 1 | **Servicio al Ciudadano** | Citizen service / help desk |
| 2 | **Registro Único Hacendario (RUT)** | Unified tax registry management |
| 3 | **Cuenta Integral Tributaria** | Integrated tax account with real-time balances |
| 4 | **Declaraciones** | Tax declaration filing |
| 5 | **Pagos** | Integrated online payment (direct IBAN debit, no bank commission) |
| 6 | **Comunicaciones y Notificaciones** | Official electronic mailbox with legal validity |
| 7 | **Expediente Electrónico** | Digital taxpayer file / history |
| 8 | **Gestor Documental** | Document management system |
| 9 | **Consulta Integral Hacendaria** | Comprehensive tax status inquiry |
| 10 | **TicoFactura** | Free government e-invoicing tool (v4.4 compliant) |

### Phase 2-3 — Planned Through 2028 (17 remaining)

| # | Module | Description |
|---|--------|-------------|
| 11 | **Devoluciones** | Automated tax refunds |
| 12 | **Exenciones** | Tax exemptions management |
| 13 | **Digesto Hacendario** | Tax legal digest / regulatory compendium |
| 14 | **Indicadores y Estadísticas** | Management dashboards and statistics |
| 15 | **Proceso Sancionador** | Sanctions / penalties process |
| 16 | **Proceso Recursivo** | Appeals process |
| 17 | **Control de Cumplimiento** | Tax compliance monitoring |
| 18 | **Fiscalización** | Tax auditing |
| 19 | **Fiscalización de Incentivos** | Incentive auditing (Zona Franca, etc.) |
| 20 | **Intercambio Internacional** | International information exchange (CRS/FATCA) |
| 21 | **Valoración Bienes Muebles** | Personal property valuation |
| 22 | **Valoración Bienes Inmuebles** | Real estate property valuation |
| 23 | **Cobro Judicial** | Judicial collection / enforcement |
| 24 | **Policía de Control Fiscal** | Tax control police |
| 25 | **Tribunal Fiscal Administrativo** | Administrative tax court |
| 26 | **Planificación** | Tax planning tools |
| 27 | **Riesgo** | Risk analysis and management |

---

## 3. Vector Fiscal

The Vector Fiscal is a personalized digital profile that **automatically determines** each taxpayer's specific tax obligations based on their economic activity (CIIU4), business size, and tax history. It:
- Generates the specific declaration forms the taxpayer must complete
- Sends deadline notifications and requirement alerts
- Pre-fills forms relevant to the taxpayer's profile
- Adapts as the taxpayer's situation changes (new activities, regime changes)

This is something no commercial tool can replicate — it uses Hacienda's complete knowledge of each taxpayer.

---

## 4. Cuenta Integral Tributaria

A **real-time unified view** of every taxpayer's financial relationship with Hacienda:
- Favorable balances (tax credits owed to taxpayer)
- Pending debts (taxes owed)
- Payment history with timestamps
- **Automatic credit compensation** — no manual requests needed
- Replaces scattered data across ATV, TRAVI, EDDI-7

Before TRIBU-CR, a taxpayer might have a credit in one system and a debt in another, with no automatic offset. Now it's all in one place.

---

## 5. Oficina Virtual (OVi)

**Portal:** https://ovitribucr.hacienda.go.cr/

| Feature | Description |
|---------|-------------|
| Unified Dashboard | Single view of all obligations, balances, deadlines |
| Declaration Filing | Submit all tax forms online |
| Online Payments | Direct IBAN-based bank debit (no intermediary banks, no commission) |
| Electronic Mailbox | Legally binding notifications from DGT, 24/7 |
| Third-Party Authorization | Delegate access to accountants without sharing passwords |
| RUT Management | Update activities, address, contact info |
| TicoFactura | Free e-invoicing tool integrated directly |

---

## 6. Pre-filled Declarations

This is arguably the most powerful feature of TRIBU-CR. The platform **automatically pre-fills** declaration fields using data from electronic invoices:
- Processes approximately **1.2 billion invoices monthly**
- Initially focused on D-150 (IVA), expanding to income tax by 2026
- Pre-populates: total taxable sales, exempt sales, tax credits, purchases
- Taxpayer must **review, verify, and confirm** (retains final responsibility)
- Daily card withholding reports (D-155) are auto-populated and non-editable

This means if a business issues all its invoices electronically (like GMS does through our Odoo module), most of their D-150 IVA declaration will be pre-filled automatically.

---

## 7. TicoFactura (Free Government Invoicing)

**URL:** https://ticofactura.cr/

### What it does for free
- Emit all document types (FE, NC, ND, TE, FEC, FEE)
- v4.4 compliant, submits to Hacienda directly
- Integrated into TRIBU-CR portal

### Limitations (why businesses still need commercial tools like Odoo)
- **Eligibility restricted:** Only for independent professionals and accredited micro/small businesses (Decreto Ejecutivo No. 44739-H)
- **No inventory management** — no tracking stock levels
- **No client database** — must re-enter customer info each time
- **No multi-user support** — single login only
- **No API integration** — cannot connect to POS, ERP, or e-commerce systems
- **Low volume capacity** — becomes slow at high volumes
- **Minimal data retention** — only 2 months of history
- **No custom branding** — generic invoice format
- **No advanced reporting** — basic only

**Bottom line:** TicoFactura is good for very small, simple businesses. GMS (with POS, subscriptions, multi-staff, inventory needs) requires a proper ERP solution like Odoo.

---

## 8. TRIBU-CR vs Commercial Tools

### What TRIBU-CR does that commercial tools CANNOT

| Capability | TRIBU-CR | GTI/Allegra/Facturele |
|------------|----------|-----------------------|
| Pre-filled declarations from Hacienda data | **YES** | No |
| Official tax account balance | **YES** | No |
| Legal notification mailbox | **YES** | No |
| RUT / Vector Fiscal management | **YES** | No |
| Direct tax payment (no commission) | **YES** | No |
| Third-party authorization | **YES** | No |
| Electronic taxpayer file | **YES** | No |
| Tax compliance monitoring | **YES** (future) | No |
| Audit/fiscalización tools | **YES** (future) | No |
| Access to 90%+ of economic transactions | **YES** | No |

### What commercial tools do that TRIBU-CR cannot

| Capability | TRIBU-CR (TicoFactura) | Commercial Tools |
|------------|------------------------|-----------------|
| Inventory management | No | Yes |
| Multi-user role-based access | No | Yes |
| Accounts receivable/payable | No | Yes |
| High-volume invoicing | No (slow at volume) | Yes |
| POS integration | No | Some |
| ERP/API integration | No | Some |
| Custom invoice branding | No | Yes |
| Client history/CRM | No | Yes |

### How they complement each other

The relationship is **not competitive but complementary:**
1. **Odoo (GMS)** handles business operations: POS sales, subscriptions, invoicing, accounting, CRM
2. **Odoo → Hacienda API** submits e-invoices in v4.4 format
3. **Hacienda → TRIBU-CR** automatically feeds invoice data into the tax system
4. **TRIBU-CR** pre-fills declarations, manages tax accounts, handles compliance
5. **Accountant uses TRIBU-CR** to review pre-filled declarations, file, and pay

---

## 9. Tax Reports & Declarations

### System Change: ATV → TRIBU-CR Declaration Codes

| Aspect | Before (ATV) | After (TRIBU-CR) |
|--------|-------------|-------------------|
| Form codes | Alphanumeric (D-101, D-104) | Numeric only: Series 100 (tax), Series 200 (informative) |
| IVA declaration | D-104 (by economic activity) | D-150 (by tax rate) |
| D-151 frequency | **Annual** | **Monthly** (becomes D-270 starting Jan 2026) |
| D-152 frequency | Annual | Monthly (becomes series 201-217) |
| Data entry | Manual, offline Excel option | Online-only, pre-filled from e-invoices |

### Complete Code Mapping (Old → New)

#### Series 100 — Autoliquidative (Tax Payment)

| Old Code | New Code | Name | Frequency |
|----------|----------|------|-----------|
| D-101 | **101** | Impuesto Utilidades - Persona Física | Annual |
| D-101 | **102** | Impuesto Utilidades - Persona Jurídica | Annual |
| D-101 | **103** | Impuesto Utilidades - Entidad Pública | Annual |
| D-105 | **104-105** | Régimen Simplificado | Quarterly |
| D-125 | **116-118** | Rentas Capital Inmobiliario (by type) | Monthly |
| D-103 | **131-147** | Retenciones (split by type: dividends, interest, salaries, etc.) | Monthly |
| D-104 | **150** | IVA - Impuesto al Valor Agregado | Monthly |

#### Series 200 — Informative Declarations

| Old Code | New Code | Name | Frequency |
|----------|----------|------|-----------|
| D-152 | **201-217** | Withholdings by type (17 forms) | Monthly |
| D-155 | **240-243** | Card Operations Detail & Summary | Daily/Monthly |
| **D-151** | **270** | Monthly Summary - Non-E-Invoice Transactions | **Monthly** |
| D-158 | **271** | Agricultural Auction Sales | Annual |
| D-195 | **272** | Inactive Corporate Entities | Annual |
| New | **273** | Transfer Pricing Information | Annual |

---

## 10. D-150 (formerly D-104) — Monthly IVA Declaration

| Field | Detail |
|-------|--------|
| **New code** | 150 |
| **Frequency** | Monthly |
| **Deadline** | First 15 natural days of following month |
| **Zero declarations** | Required even with no activity |
| **Key change** | No longer by economic activity; organized by **tax rate** (13%, 8%, 4%, 2%, 1%, 0.5%, 0%) |

### 6 Sections

1. **Ventas (Sales)** — Classified by IVA rate, further split: gravadas, exentas, exoneradas, no sujetas
2. **Compras y Crédito Fiscal** — Purchases by rate, differentiated by destination: fully creditable, non-creditable, mixed use (proportionality)
3. **Prorrata** — Annual proportionality adjustment (year-end)
4. **Determinación IVA Neto** — Sales IVA minus purchase credits
5. **Determinación Final** — Prior credits, card retentions (auto-populated), interest
6. **Liquidación del Saldo** — Final amount owed or credit carried forward (3-month carry)

### Pre-fill

TRIBU-CR auto-populates from v4.4 e-invoices + daily bank card reports. Taxpayer reviews and confirms.

### IVA Formula

```
IVA Payable = IVA Débito (Sales) - IVA Crédito (Purchases, adjusted for proportionality)
            - Card retentions (auto) - Prior period credits
```

---

## 11. D-101/102 — Annual Income Tax

| Field | Detail |
|-------|--------|
| **New codes** | 101 (persona física), 102 (persona jurídica), 103 (entidad pública) |
| **Tax period** | Calendar year (Jan 1 - Dec 31) |
| **Deadline** | March 15 of following year |

### 6 Blocks

Assets/Liabilities → Income → Costs/Expenses/Deductions → Taxable Base → Tax Credits → Settlement

### Tax Rates (Legal Entities)
- Gross income > ~₡120,582,000: **30% flat** on net income
- Below threshold: progressive brackets apply

---

## 12. D-151/D-270 — Informative Declaration

| Field | Detail |
|-------|--------|
| **Old code** | D-151 (annual) |
| **New code** | **270** (monthly, starting January 2026) |
| **Deadline** | First 10 natural days of following month |
| **What to report** | ONLY transactions NOT backed by electronic invoices |

**If all transactions have e-invoices, this declaration is essentially empty.**

Reports: Clients >₡2,500,000, Suppliers >₡2,500,000, Specific expenses >₡50,000 (professional services, rentals, commissions, interest).

**Important change:** D-151 was annual. D-270 is **monthly** starting January 2026. This is a significant increase in filing frequency.

---

## 13. D-155 & Other Declarations

### D-155 — Monthly Withholdings

| Field | Detail |
|-------|--------|
| **New codes** | 240-243 (card operations withholdings) |
| **Frequency** | Monthly (some card withholdings now **daily**) |
| **Deadline** | First 10 of following month |

### Other Declarations

| Declaration | New Code | Relevance to GMS |
|-------------|----------|-------------------|
| D-106 (Selective Consumption) | TBD | Not applicable (gyms) |
| D-105 (Simplified Regime) | 104-105 | Not applicable |
| D-125 (Real Estate Capital Income) | 116-118 | Only if owning rental property |
| D-195 (Inactive Entities) | 272 | Only for dormant companies |
| D-179 (Solidarity Housing Tax) | — | Only for luxury residences |

---

## 14. Penalties & Sanctions (2026 Base Salary: ₡462,200)

| Infraction | Penalty |
|-----------|---------|
| Late RUT update | ₡231,100/month (max ₡1,386,600) |
| Late declaration filing (D-150, D-101) | ₡231,100 per form (80% reduction if voluntary) |
| Late tax payment | 1% per month of amount owed (max 20%) |
| Failure to issue e-invoices | ₡924,400; repeat = **5-day business closure** |
| Omitting informative declaration (D-270) | 2% of prior-year gross income (min ₡1,386,600, max ₡46,220,000) |
| Incorrect records in D-270 | ~₡4,622 per error |
| Refusing electronic payment | ₡462,200 |

**75% fine reduction** available if information delivered within 3 days of deadline.

---

## 15. Filing Calendar 2026

### Monthly (every month)

| Deadline | Declaration | Code | Description |
|----------|-------------|------|-------------|
| 10th | D-270 | 270 | Monthly informative (non-e-invoice transactions) |
| 10th | D-155 series | 240-243 | Card withholding details |
| 15th | D-150 | 150 | Monthly IVA declaration |
| 15th | D-152 series | 201-217 | Monthly withholding informative |

### Annual

| Deadline | Declaration | Code | Description |
|----------|-------------|------|-------------|
| Jan 15 | D-179 | — | Solidarity housing tax payment |
| Mar 15 | D-101/102 | 101-103 | Income tax declaration |
| Apr 30 | D-195 | 272 | Inactive legal entities |

---

## 16. E-Invoice → Declaration Flow

```
Odoo (GMS) → Hacienda API (e-invoice v4.4) → Hacienda Internal Systems → TRIBU-CR
                                                                           ↓
                                                             Pre-filled Declaration Drafts
```

| Declaration | Pre-fill from E-Invoices | Status |
|-------------|-------------------------|--------|
| D-150 (IVA) | All issued/received vouchers | **Active** since Aug 2025 |
| D-101/102 (Income) | Aggregated annual data | **Partial** — improving |
| D-270 (Informative) | Only non-e-invoice transactions | N/A — manual |
| D-155 (Withholdings) | Daily bank card reports | **Active** — auto, non-editable |

---

## 17. GMS-Specific Relevance

| Priority | Declaration | Action |
|----------|-------------|--------|
| **HIGH** | D-150 (IVA Monthly) | File by 15th, verify pre-fill against Odoo data |
| **HIGH** | D-101/102 (Income Tax Annual) | File by March 15 |
| **MEDIUM** | D-270 (Monthly Informative) | Likely empty if all transactions have e-invoices |
| **MEDIUM** | D-155 (Withholdings) | If acting as withholding agent (employees, contractors) |
| **LOW** | D-152 series | Only if withholding agent |
| **N/A** | D-106, D-105, D-125, D-179 | Not applicable to standard gym operations |

---

## 18. Impact on Our Module

| Aspect | Changed? | Details |
|--------|----------|---------|
| E-invoice API endpoints | **NO** | `api.comprobanteselectronicos.go.cr` unchanged |
| OAuth2 authentication | **NO** | Same Keycloak IDP, same flow |
| XML schema version | **YES** | Must be v4.4 (already implemented) |
| Receptor activity code | **YES** | Now mandatory (CIIU4) (already implemented) |
| Declaration filing | **YES** | New forms, new codes, new portal |

**The e-invoicing API infrastructure is independent of TRIBU-CR.** No API migration needed for our module. The main change is that TRIBU-CR now consumes our e-invoice data to pre-fill declarations.

---

## 19. How the Integration Works

### Architecture Overview

```
┌─────────────────┐
│   GMS (Odoo 19) │
│                 │
│ - Sales Orders  │
│ - Subscriptions │
│ - POS Sales     │
└────────┬────────┘
         │
         │ 1. Generate Invoice
         ▼
┌─────────────────────┐
│ Electronic Invoice  │
│ Module (v4.4)       │
│                     │
│ - XML Generation    │
│ - Digital Signature │
│ - Validation        │
└────────┬────────────┘
         │
         │ 2. Submit XML via API
         ▼
┌─────────────────────────────┐
│ Ministry of Finance         │
│ (Hacienda)                  │
│                             │
│ - Validate XML              │
│ - Verify Signature          │
│ - Assign Sequential Number  │
│ - Send Confirmation/Error   │
└────────┬────────────────────┘
         │
         │ 3. Invoice Data (automatic)
         ▼
┌─────────────────────────┐
│ TRIBU-CR Platform       │
│                         │
│ - Store Invoice Data    │
│ - Pre-fill Tax Returns  │
│ - Calculate VAT Credits │
│ - Generate Reports      │
└─────────────────────────┘
```

### Important Note

**There is NO direct Odoo-to-TRIBU-CR integration.** The integration is indirect:
- **Odoo → Hacienda** (electronic invoicing v4.4)
- **Hacienda → TRIBU-CR** (automatic government data flow)
- **TRIBU-CR → Tax Returns** (pre-filled from invoice data)

---

## 20. Electronic Invoicing v4.4

### Mandatory Implementation
Version 4.4 is mandatory as of October 6, 2025, completely replacing version 4.3.

### Major Changes in v4.4 (146+ XML changes)

1. **New document type:** ReciboElectronicoPago (Electronic Payment Receipt)
2. **New mandatory field:** "Proveedor de Sistemas" (software provider ID)
3. **New mandatory field:** Receiver economic activity code for FE
4. **New ID types:** `05` (non-resident foreigner), `06` (non-taxpayer)
5. **New payment codes:** `06` (SINPE Móvil), `07` (digital platforms)
6. **New sale conditions:** `14` (operating lease), `15` (financial lease)
7. **New tax code:** `11` (0% without credit rights)
8. **New document types:** `08`, `09`, `10` (guarantees, penalties, late interest)
9. **`numeroIdentificacion` expanded to 20 chars** (for passport numbers)
10. **Discount Code System:** 11 specific discount codes classifying rebates by nature
11. **71+ new fields total**

### GMS Implementation Status
Our `l10n_cr_einvoice` module is **fully compliant** with v4.4 and has been tested with Hacienda sandbox (doc 36052 ACCEPTED).

---

## 21. Requirements for GMS

### Technical Requirements

1. **Digital Certificate:** Company's Costa Rican `.p12` certificate (BCCR CA SINPE)
2. **Taxpayer Registration:** Active RUT with Hacienda
3. **Odoo Module:** Our `l10n_cr_einvoice` module (v4.4 compliant, Odoo 19 Enterprise)
4. **Customer Data:** Valid tax ID (cédula), email, billing address
5. **Product Configuration:** CABYS codes, proper IVA tax codes, unit of measure codes

### Business Requirements

1. **Sequential Numbering:** Configured per location/POS
2. **Backup System:** Offline queue for failed submissions, retry logic
3. **Customer Communication:** Email delivery of e-invoices (PDF + XML)
4. **Reporting:** Monthly IVA reports, annual income tax data, integration with TRIBU-CR declarations

---

## 22. Sources & References

### Official Government Resources — TRIBU-CR

| Resource | URL |
|----------|-----|
| TRIBU-CR Portal | https://www.hacienda.go.cr/TRIBU-CR.html |
| TRIBU-CR FAQ PDF | https://www.hacienda.go.cr/docs/dPreguntasYRespuestasDeTRIBU-CR.pdf |
| OVi Portal | https://ovitribucr.hacienda.go.cr/ |
| TicoFactura | https://ticofactura.cr/ |

### Official Government Resources — Tax Declarations

| Resource | URL |
|----------|-----|
| Nueva codificación consolidada | https://www.hacienda.go.cr/docs/a_1NuevaCodificacionDeDeclaracionesEnTRIBU-CR-Consolidado_PP_PJ_PF.pdf |
| Códigos para declaraciones | https://www.hacienda.go.cr/CodigosParaDeclaraciones.html |
| Presentación ISU 2024 | https://www.hacienda.go.cr/docs/CHARLAISU-2024-27-02-2025.pdf |
| D-101 formulario PDF | https://www.hacienda.go.cr/docs/D-101DeclaracionImpuestossobrelaRenta_casilla46bis-papel.pdf |
| Infracciones y sanciones | https://www.hacienda.go.cr/docs/InfraccionesYSancionesAdministrativasMasRelevantes.pdf |
| Declaraciones informativas anuales | https://www.hacienda.go.cr/docs/PresentacionDeclaracionesInformativasAnualesD-151_D-152_D-158.pdf |

### Community & Analysis — TRIBU-CR

| Resource | URL |
|----------|-----|
| Facturele: Guía Práctica 2025 | https://www.facturele.com/2025/09/29/tribu-cr-guia-practica-2025/ |
| Facturele: Módulos 2025 | https://www.facturele.com/2025/04/23/tribu-cr-modulos-2025/ |
| Facturele: Oficina Virtual | https://www.facturele.com/2025/04/29/oficina-virtual-tribu-cr/ |
| Facturele: Declaraciones prellenadas | https://www.facturele.com/2025/04/28/declaraciones-prellenadas-tribu-cr/ |
| Facturele: D-150 IVA | https://www.facturele.com/2025/09/18/declaracion-del-iva-formulario-d-150/ |
| Facturele: Limitaciones facturador gratuito | https://www.facturele.com/2025/06/13/limitaciones-facturador-gratuito-4-4/ |
| Facturele: Transición ATV→TRIBU-CR IVA | https://www.facturele.com/2025/10/29/transicion-de-atv-a-tribu-cr/ |
| Siempre al Día: Vector Fiscal | https://siemprealdia.co/costa-rica/impuestos/vector-fiscal-en-el-sistema-tribu-cr/ |
| Siempre al Día: Autorización de terceros | https://siemprealdia.co/costa-rica/impuestos/autorizacion-de-terceros-en-tribu-cr/ |
| Siempre al Día: Impacto en PyMEs | https://siemprealdia.co/costa-rica/impuestos/impacto-del-sistema-tribu-cr-en-las-pymes/ |
| Siempre al Día: Formulario 150 IVA | https://siemprealdia.co/costa-rica/impuestos/formulario-150-de-iva/ |
| Siempre al Día: Codificación informativas | https://siemprealdia.co/costa-rica/impuestos/codificacion-de-declaraciones-informativas/ |
| Siempre al Día: Cambios declaraciones TRIBU-CR | https://siemprealdia.co/costa-rica/impuestos/cambios-en-declaraciones-tributarias-con-tribu-cr/ |
| Siempre al Día: Infracciones Parte I | https://siemprealdia.co/costa-rica/impuestos/infracciones-tributarias-en-costa-rica-parte-i/ |
| Siempre al Día: Infracciones Parte II | https://siemprealdia.co/costa-rica/impuestos/infracciones-tributarias-en-costa-rica-parte-ii/ |
| Officium Legal: Primeros módulos | https://blog.officiumlegal.com/es/derecho-tributario/ministerio-de-hacienda-primeros-modulos-que-se-habilitaran-en-tribu-cr |
| Officium Legal: Multas guía práctica | https://blog.officiumlegal.com/es/derecho-tributario/multas-del-ministerio-de-hacienda-guia-practica-para-resolverlas |
| BDO: TRIBU-CR | https://www.bdo.cr/es-cr/publicaciones/2024/lanzamiento-del-sistema-tribu-cr-transformando-la-gestion-tributaria-en-costa-rica |
| KPMG: Lineamientos OVi | https://assets.kpmg.com/content/dam/kpmg/cr/pdf/2025/Lineamientos-para-el-acceso-a-la-oficina-virtual-del-Sistema-de-Gesti%C3%B3n-Tributaria-TRIBU-CR.pdf |
| KPMG: Formularios IVA | https://assets.kpmg.com/content/dam/kpmg/cr/pdf/2025/Formularios-y-medio-para-la-presentaci%C3%B3n-de-declaraciones-del-iva.pdf |
| Auxadi: Cambios declaraciones TRIBU-CR | https://www.auxadi.es/blog/2025/09/29/costa-rica-cambios-declaraciones-tribu-cr/ |
| Baker Tilly: TRIBU-CR claves prácticas | https://bakertilly.cr/wp-content/uploads/2025/10/TRIBU-CR-Claves-practicas-y-retos-inmediatos-Bakertilly-CR.pdf |
| Finube: D-151 todavía? | https://www.finube.com/blog/declaracion-d-151 |

### Odoo Integration References

| Resource | URL |
|----------|-----|
| Localización CR V4.4 (Xalachi) | https://apps.odoo.com/apps/modules/17.0/l10n_cr_invoice |
| OdooCR on GitHub | https://github.com/odoocr/l10n_cr |
| Vauxoo CR E-Invoicing | https://www.vauxoo.com/en_US/blog/our-blog-1/electronic-invoicing-costa-rica-217 |

### Odoo Partners in Costa Rica

| Partner | URL | Notes |
|---------|-----|-------|
| Nimetrix | https://www.nimetrixcostarica.com | DGT-certified, active in CR market |
| Vauxoo | https://www.vauxoo.com/en_US/odoo-costa-rica | Latin America localization expert |
| TI Recursos | https://www.tirecursos.com/en_US | #1 Odoo implementer in CR |

---

*Research originally compiled: December 28, 2025*
*Comprehensively updated with TRIBU-CR modules, tax declarations, and penalty research: February 6, 2026*
