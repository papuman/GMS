---
title: "Architecture Documentation - System Design Index"
category: "architecture"
domain: "architecture"
layer: "index"
audience: ["developer", "architect", "product-manager"]
last_updated: "2026-01-02"
status: "production-ready"
version: "1.0.0"
maintainer: "Development Team"
description: "Master index for GMS system architecture, module design, and technical documentation"
keywords: ["architecture", "system-design", "odoo", "module-architecture", "data-models"]
---

# 📍 Navigation Breadcrumb
[Home](../index.md) > Architecture Documentation

---

# 🏛️ Architecture Documentation
**System Design & Technical Architecture - Master Index**

**Version:** 1.0.0
**Last Updated:** 2026-01-01
**Status:** ✅ Production Ready - Complete Architecture Documentation
**Architecture Team:** GMS Engineering

---

## 📊 Executive Summary

The Architecture Documentation contains comprehensive system design, module architecture patterns, and technical specifications for the GMS platform built on Odoo ERP framework.

**Architecture Coverage:**
- **System Architecture:** High-level design and modular monolith pattern
- **Odoo Framework:** Deep technical analysis and best practices
- **Module Architecture:** Cloning, customization, and integration patterns
- **Data Models:** Database schema and ORM patterns
- **API Design:** Integration architecture and API specifications

**Key Principles:**
- **Modular Monolith:** Single deployment, modular design
- **Odoo-Native:** Follow Odoo framework conventions
- **Costa Rica First:** Built for Costa Rica compliance
- **Integration-Ready:** POS, payments, e-invoicing APIs

---

## 🎯 Quick Navigation

| I Need To... | Go Here |
|--------------|---------|
| **Understand overall system design** | [System Architecture](../architecture.md) |
| **Learn Odoo framework patterns** | [Odoo Framework Deep Dive](../odoo-framework-deep-dive.md) |
| **Clone/customize Odoo modules** | [Module Architecture Guide](../GMS_MODULE_ARCHITECTURE_GUIDE.md) |
| **Quick module cloning reference** | [Module Cloning Quick Reference](../MODULE_CLONING_QUICK_REFERENCE.md) |
| **Understand data models** | [Odoo Data Models Reference](../odoo-data-models-reference.md) |
| **Design new APIs** | API Design *(to be created)* |
| **Integrate POS/payments/e-invoice** | [POS E-Invoice Integration Spec](../POS_EINVOICE_INTEGRATION_SPEC.md) |

---

## 📚 Architecture Documents

> **📍 Note on File Locations:**
>
> Most architecture documents are located in the repository root (`docs/`) rather than this subdirectory (`docs/04-architecture/`). This design decision:
> - Makes critical architecture files highly visible and easy to find
> - Follows the pattern of keeping frequently-accessed documents at the top level
> - Maintains backward compatibility with existing documentation references
> - Allows this index to serve as a curated navigation hub without file duplication
>
> All documents below are accessible via the links provided.

---

### 1. System Architecture
**Document:** [architecture.md](../architecture.md)
**Size:** 21KB
**Audience:** All developers, architects, product managers

**What's Inside:**
- ✅ Modular monolith pattern explained
- ✅ Odoo framework overview
- ✅ Multi-module architecture
- ✅ Costa Rica e-invoicing architecture
- ✅ Integration points (POS, payments, Hacienda)
- ✅ Deployment architecture

**Key Concepts:**
```
Modular Monolith Pattern:
- Single deployment (one Odoo instance)
- Multiple modules (l10n_cr_einvoice, payment_tilopay, etc.)
- Clear module boundaries
- Shared database with proper isolation
- Event-driven communication between modules
```

**Architecture Layers:**
1. **Presentation Layer:** Odoo web UI + custom views
2. **Business Logic Layer:** Python models and workflows
3. **Data Access Layer:** Odoo ORM
4. **Integration Layer:** External APIs (Hacienda, TiloPay, POS)
5. **Persistence Layer:** PostgreSQL database

**Use This Document When:**
- Starting new development
- Planning module structure
- Understanding system boundaries
- Onboarding new developers

---

### 2. Odoo Framework Deep Dive
**Document:** [odoo-framework-deep-dive.md](../odoo-framework-deep-dive.md)
**Size:** 45KB
**Audience:** Odoo developers (beginner to advanced)

**What's Inside:**
- ✅ Odoo MVC architecture
- ✅ ORM in depth (CRUD, relations, computed fields)
- ✅ View architecture (form, tree, kanban, pivot)
- ✅ Security model (access rights, record rules)
- ✅ Workflows and business logic
- ✅ API and RPC mechanisms
- ✅ QWeb templating engine
- ✅ JavaScript framework integration

**Key Topics:**

#### ORM Patterns
```python
# Model definition
class EinvoiceDocument(models.Model):
    _name = 'l10n_cr.einvoice.document'
    _description = 'E-Invoice Document'

    # Fields with ORM magic
    partner_id = fields.Many2one('res.partner', required=True)
    line_ids = fields.One2many('l10n_cr.einvoice.line', 'document_id')
    amount_total = fields.Monetary(compute='_compute_amount_total', store=True)

    # Computed field with dependencies
    @api.depends('line_ids.price_total')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(line.price_total for line in record.line_ids)
```

#### View Architecture
```xml
<!-- Form view with inheritance -->
<record id="view_einvoice_document_form" model="ir.ui.view">
    <field name="name">einvoice.document.form</field>
    <field name="model">l10n_cr.einvoice.document</field>
    <field name="arch" type="xml">
        <form string="E-Invoice">
            <header>
                <button name="action_submit_to_hacienda" type="object"/>
            </header>
            <sheet>
                <group>
                    <field name="partner_id"/>
                    <field name="amount_total"/>
                </group>
                <notebook>
                    <page string="Invoice Lines">
                        <field name="line_ids"/>
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>
```

**Use This Document When:**
- Learning Odoo development
- Understanding ORM behavior
- Designing views
- Implementing security
- Debugging Odoo issues

---

### 3. Module Architecture Guide
**Document:** [GMS_MODULE_ARCHITECTURE_GUIDE.md](../GMS_MODULE_ARCHITECTURE_GUIDE.md)
**Size:** 96KB (comprehensive guide)
**Audience:** Odoo developers customizing modules

**What's Inside:**
- ✅ Module cloning strategies
- ✅ Inheritance patterns (model, view, controller)
- ✅ When to clone vs extend vs create new
- ✅ Module dependencies management
- ✅ Data migration between modules
- ✅ Testing cloned modules
- ✅ Best practices and anti-patterns

**Cloning Strategies:**

#### Strategy 1: Extension (Inheritance)
```python
# Extend existing model without cloning
class AccountMove(models.Model):
    _inherit = 'account.move'

    # Add Costa Rica fields
    einvoice_clave = fields.Char('Clave')
    hacienda_status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
    ])
```

**When to use:** Adding fields/methods to existing models

#### Strategy 2: Full Clone
```python
# Clone entire module for heavy customization
# Copy all files, rename module, modify extensively
l10n_cr/ → l10n_cr_einvoice/
```

**When to use:** Costa Rica-specific functionality that diverges significantly

#### Strategy 3: Hybrid (Clone + Extend)
```python
# Clone core, extend Odoo standard
# Best of both worlds
```

**When to use:** Country-specific compliance while maintaining upgrade path

**Module Structure Best Practices:**
```
l10n_cr_einvoice/
├── __init__.py
├── __manifest__.py          # Module metadata
├── models/                  # Business logic
│   ├── __init__.py
│   ├── einvoice_document.py
│   ├── xml_generator.py
│   └── hacienda_api.py
├── views/                   # XML views
│   └── einvoice_document_views.xml
├── data/                    # Master data
│   ├── document_types.xml
│   └── payment_methods.xml
├── security/                # Access control
│   └── ir.model.access.csv
├── wizards/                 # Transient models
│   └── void_wizard.py
└── tests/                   # Unit tests
    └── test_einvoice.py
```

**Use This Document When:**
- Customizing Odoo modules
- Planning module structure
- Deciding clone vs extend
- Managing module dependencies

---

### 4. Module Cloning Quick Reference
**Document:** [MODULE_CLONING_QUICK_REFERENCE.md](../MODULE_CLONING_QUICK_REFERENCE.md)
**Size:** 11KB
**Audience:** Developers needing quick answers

**What's Inside:**
- ✅ Quick decision tree (clone vs extend)
- ✅ Common patterns with code examples
- ✅ Inheritance cheat sheet
- ✅ View inheritance examples
- ✅ Common pitfalls and solutions

**Quick Decision Tree:**
```
Need Costa Rica compliance?
├─ YES → Clone standard module (l10n_cr_einvoice)
│   ├─ Heavy customization → Full clone
│   └─ Minor changes → Extend with inheritance
└─ NO → Extend existing Odoo modules
```

**Common Patterns:**

| Pattern | Use Case | Example |
|---------|----------|---------|
| **Model Inheritance (_inherit)** | Add fields to existing model | Add `einvoice_clave` to `account.move` |
| **Model Delegation (_inherits)** | Reuse model as component | Partner extends `res.partner` |
| **View Inheritance** | Modify existing views | Add fields to invoice form |
| **Controller Extension** | Modify HTTP routes | Custom portal routes |

**Use This Document When:**
- Need quick answer on cloning
- Looking for code examples
- Choosing inheritance pattern

---

### 5. Odoo Data Models Reference
**Document:** [odoo-data-models-reference.md](../odoo-data-models-reference.md)
**Size:** 17KB
**Audience:** Developers, DBAs, architects

**What's Inside:**
- ✅ Odoo ORM overview
- ✅ Field types reference
- ✅ Relational fields (Many2one, One2many, Many2many)
- ✅ Computed fields and dependencies
- ✅ Constraints and validation
- ✅ Database schema mapping
- ✅ Performance optimization tips

**Field Types Quick Reference:**

| Field Type | Use Case | Example |
|------------|----------|---------|
| **Char** | Short text | `name`, `clave` |
| **Text** | Long text | `notes`, `description` |
| **Integer** | Whole numbers | `sequence`, `count` |
| **Float** | Decimals | `amount`, `quantity` |
| **Monetary** | Currency amounts | `amount_total`, `subtotal` |
| **Date** | Date only | `invoice_date` |
| **Datetime** | Date + time | `create_date`, `submitted_at` |
| **Boolean** | True/False | `is_accepted`, `is_voided` |
| **Selection** | Dropdown | `status`, `document_type` |
| **Many2one** | Foreign key | `partner_id`, `company_id` |
| **One2many** | Reverse FK | `line_ids`, `tax_ids` |
| **Many2many** | Join table | `tag_ids` |
| **Binary** | Files | `pdf_file`, `xml_file` |

**Relational Patterns:**
```python
# Many2one (N:1) - Invoice → Customer
partner_id = fields.Many2one('res.partner', 'Customer')

# One2many (1:N) - Invoice → Lines (reverse of Many2one)
line_ids = fields.One2many('l10n_cr.einvoice.line', 'document_id', 'Lines')

# Many2many (N:M) - Invoice → Tags
tag_ids = fields.Many2many('l10n_cr.invoice.tag', string='Tags')
```

**Computed Fields Pattern:**
```python
# Stored computed field (performance)
amount_total = fields.Monetary(
    compute='_compute_amount_total',
    store=True,  # Stored in DB for performance
    currency_field='currency_id'
)

@api.depends('line_ids.price_total')  # Dependencies trigger recomputation
def _compute_amount_total(self):
    for record in self:
        record.amount_total = sum(line.price_total for line in record.line_ids)
```

**Use This Document When:**
- Designing database schema
- Choosing field types
- Implementing computed fields
- Optimizing queries

---

### 6. POS E-Invoice Integration Spec
**Document:** [POS_EINVOICE_INTEGRATION_SPEC.md](../POS_EINVOICE_INTEGRATION_SPEC.md)
**Size:** 97KB (detailed specification)
**Audience:** Developers implementing POS integration

**What's Inside:**
- ✅ POS to e-invoice data flow
- ✅ Offline mode handling
- ✅ Automatic document type selection (invoice vs ticket)
- ✅ Membership integration with POS
- ✅ Payment capture and Hacienda submission
- ✅ Error handling and retry logic
- ✅ Performance optimization
- ✅ Testing scenarios

**Integration Architecture:**
```
POS Sale
   ↓
Auto-detect document type
   ├─ ₡0-500,000 → Ticket (type 04)
   └─ >₡500,000 → Invoice (type 01)
   ↓
Generate XML
   ↓
Sign XML
   ↓
Submit to Hacienda (async)
   ↓
Poll for response
   ↓
Update POS order status
```

**Key Features:**
- Automatic document type selection based on amount
- Offline queue for unstable internet
- Background submission (don't block POS)
- Real-time status updates via WebSocket
- Member discount application
- Payment method mapping (cash, card, SINPE)

**Use This Document When:**
- Integrating POS with e-invoicing
- Implementing offline mode
- Optimizing POS performance
- Troubleshooting POS issues

---

### 7. API Design Patterns
**Document:** `api-design.md` *(to be created)*
**Status:** 🔄 Pending

**Planned Content:**
- REST API design principles
- Hacienda API integration patterns
- TiloPay payment gateway API
- POS API endpoints
- Webhook handling
- Authentication and security
- Rate limiting and throttling

---

### 8. Integration Architecture
**Document:** `integration-architecture.md` *(to be created)*
**Status:** 🔄 Pending

**Planned Content:**
- External system integrations
- API gateway patterns
- Event-driven architecture
- Message queues
- Webhook management
- Error handling and retry logic

---

## 📐 Architecture Principles

### 1. Modular Monolith
**Why:** Single deployment, modular design
- ✅ Easier to develop and debug
- ✅ Simpler deployment (single Odoo instance)
- ✅ Shared database with proper isolation
- ✅ Clear module boundaries via Odoo dependencies

**vs Microservices:** Monolith chosen for:
- Faster development (no network overhead)
- Easier transactions (single DB)
- Simpler operations (one deploy)
- Lower infrastructure costs

### 2. Odoo-Native Development
**Why:** Leverage framework strengths
- ✅ Use Odoo ORM (don't fight it)
- ✅ Follow Odoo view patterns
- ✅ Extend, don't replace Odoo modules
- ✅ Use Odoo security model

**Benefits:**
- Easier upgrades
- Community module compatibility
- Reduced maintenance
- Better performance

### 3. Costa Rica First
**Why:** Compliance is non-negotiable
- ✅ Build for Costa Rica requirements from day 1
- ✅ Don't abstract too early (YAGNI)
- ✅ Test against real Hacienda sandbox
- ✅ Follow official DGT specifications

### 4. Integration-Ready
**Why:** Modern gyms need integrations
- ✅ Clean API boundaries
- ✅ Webhook support
- ✅ Event-driven architecture
- ✅ Async where needed (Hacienda submission)

---

## 🔍 Search Keywords (For LLM Agents)

**Architecture:**
- `architecture`, `system-design`, `modular-monolith`
- `odoo-architecture`, `module-design`, `integration-patterns`

**Odoo:**
- `odoo-orm`, `odoo-views`, `odoo-models`, `odoo-framework`
- `inheritance`, `model-extension`, `view-inheritance`
- `computed-fields`, `relational-fields`, `security-model`

**Integration:**
- `api-integration`, `hacienda-api`, `tilopay-api`, `pos-integration`
- `webhook`, `async`, `event-driven`, `message-queue`

---

## 🔗 Related Documentation

**For Implementation:**
- [Implementation Guides](../05-implementation/index.md) - How to build based on this architecture
- [Module Cloning Guide](../GMS_MODULE_ARCHITECTURE_GUIDE.md) - Detailed customization patterns

**For Development:**
- [Development Domain](../11-development/index.md) - Dev setup and coding standards
- [Odoo Framework Deep Dive](../odoo-framework-deep-dive.md) - Framework mastery

**For Research:**
- [HuliPractice Forensic Analysis](../02-research/competitive/hulipractice/forensic-analysis.md) - Competitor architecture

**For Planning:**
- [Planning Documents](../03-planning/index.md) - Why these architecture decisions were made

---

## 🔄 Maintenance & Updates

### Update Schedule

- **After major architecture changes** - Update relevant docs
- **Monthly** - Review and refresh code examples
- **Quarterly** - Architecture decision record review
- **Annually** - Full architecture audit

### Document Ownership

| Document | Owner |
|----------|-------|
| System Architecture | Lead Architect |
| Odoo Framework Docs | Backend Team |
| Module Architecture | Backend Team |
| Integration Specs | Integration Team |

---

## ✅ Architecture Documentation Status

**Status:** ✅ **PRODUCTION READY - v1.0.0**
**Coverage:**
- ✅ System architecture documented
- ✅ Odoo framework deep dive complete
- ✅ Module cloning patterns documented
- ✅ POS integration spec complete
- 🔄 API design patterns (pending)
- 🔄 Integration architecture (pending)

**Quality Indicators:**
- ✅ Comprehensive coverage of Odoo patterns
- ✅ Real code examples from production
- ✅ Architecture decisions documented
- ✅ Integration patterns proven in production

**Last Update:** 2026-01-01
**Next Review:** 2026-04-01 (Quarterly)

---

**🏛️ Architecture Documentation Maintained By:** GMS Architecture Team
**Version:** 1.0.0
**Last Updated:** 2026-01-01
