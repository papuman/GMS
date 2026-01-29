# 🏗️ GMS Knowledge Repository Architecture
**Phase 3: Final Documentation Organization Design**

**Architect:** Winston
**Date:** 2026-01-01
**Version:** 1.0.0
**Status:** ✅ **APPROVED ARCHITECTURE - READY FOR IMPLEMENTATION**

---

## Executive Summary

This document defines the comprehensive architecture for the GMS knowledge repository, organizing 148+ documentation files into a coherent, navigable, and maintainable system optimized for both human users and LLM agents.

**Architecture Principles:**
1. **Intelligence Preservation:** Maintain the 4-layer pyramid structure (forensic → domain → strategic → action)
2. **Dual Optimization:** Equal focus on human UX and LLM semantic search
3. **Progressive Disclosure:** Information organized from high-level overviews to deep technical details
4. **Maintenance First:** Built-in versioning, ownership, and update workflows
5. **Future-Proof:** Scalable structure that grows with the project

**Key Design Decisions:**
- ✅ **Keep numbered directory prefixes** (01-, 02-, etc.) for clear ordering
- ✅ **Three-tier navigation** (Global Index → Domain Index → Document)
- ✅ **YAML frontmatter** for metadata (LLM-friendly)
- ✅ **Archive at root** (`_archive/`) to preserve history
- ✅ **Breadcrumb navigation** in all documents
- ✅ **Role-based entry points** for different user types

---

## Directory Structure (Final Design)

### Complete Repository Tree

```
GMS/
├── README.md                                    # Project entry point
├── GMS-README.md                                # GMS features overview
├── PRODUCTION-READINESS-REPORT.md               # Deployment guide
├── 100-PERCENT-COMPLIANCE-ACHIEVED.md           # Compliance status
├── DOCUMENTATION-COMPLETE.md                    # Doc status summary
│
├── docs/                                        # 📚 MAIN DOCUMENTATION HUB
│   ├── index.md                                 # 🌐 GLOBAL MASTER INDEX
│   ├── KNOWLEDGE-REPOSITORY-ARCHITECTURE.md     # This document
│   ├── DOCUMENTATION-STANDARDS.md               # Writing & formatting standards
│   ├── QUICK-START-GUIDE.md                     # Fast onboarding for new users
│   │
│   ├── 01-getting-started/                     # 🚀 Onboarding & Quickstarts
│   │   ├── index.md                             # Getting started navigation
│   │   ├── new-developer-onboarding.md
│   │   ├── new-pm-onboarding.md
│   │   ├── new-designer-onboarding.md
│   │   ├── glossary.md                          # Terms & definitions
│   │   └── faq.md                               # Frequently asked questions
│   │
│   ├── 02-research/                            # 🔬 Market & Competitive Intelligence
│   │   ├── index.md                             # Research hub index
│   │   │
│   │   ├── competitive/                         # Competitive analysis
│   │   │   ├── index.md                         # Competitive intelligence index
│   │   │   │
│   │   │   ├── hulipractice/                    # HuliPractice deep dive
│   │   │   │   ├── 00-INTELLIGENCE-INDEX.md     # ✅ Master navigation (Paige)
│   │   │   │   ├── forensic-analysis.md         # Layer 1: Technical forensics
│   │   │   │   ├── ux-implementation-guide.md   # Layer 2: UX & workflows
│   │   │   │   ├── strategic-analysis.md        # Layer 3: Business intelligence
│   │   │   │   └── action-plan.md               # Layer 4: Implementation roadmap
│   │   │   │
│   │   │   └── market-leaders/                  # Other competitors
│   │   │       ├── mindbody-analysis.md
│   │   │       ├── glofox-analysis.md
│   │   │       └── zenplanner-analysis.md
│   │   │
│   │   ├── costa-rica/                          # Costa Rica market research
│   │   │   ├── 00-COSTA-RICA-RESEARCH-INDEX.md  # ✅ Master navigation (Paige)
│   │   │   ├── einvoice-providers-landscape.md  # Provider comparison
│   │   │   ├── migration-best-practices.md      # Technical migration guide
│   │   │   ├── compliance-requirements.md       # Legal & regulatory
│   │   │   └── gym-market-analysis.md           # CR gym market sizing
│   │   │
│   │   ├── market/                              # Global market intelligence
│   │   │   ├── index.md                         # Market research index
│   │   │   ├── gym-management-software-2025.md  # Comprehensive market analysis
│   │   │   ├── technology-trends-2025.md        # AI, wearables, hybrid fitness
│   │   │   ├── pricing-models-analysis.md       # Pricing strategies
│   │   │   └── user-pain-points.md              # User needs & frustrations
│   │   │
│   │   └── technical/                           # Technical research
│   │       ├── odoo-framework-analysis.md
│   │       ├── payment-gateway-comparison.md
│   │       └── einvoicing-standards.md
│   │
│   ├── 03-planning/                            # 📋 Product Strategy & Roadmaps
│   │   ├── index.md                             # Planning docs index
│   │   ├── prd-gms-main.md                      # Main GMS PRD
│   │   ├── prd-costa-rica-einvoice-module.md    # E-invoice module PRD
│   │   ├── feature-roadmap.md                   # Product roadmap
│   │   ├── feature-master-list.md               # Complete feature catalog
│   │   └── strategic-synthesis.md               # Strategic recommendations
│   │
│   ├── 04-architecture/                        # 🏛️ System Architecture
│   │   ├── index.md                             # Architecture docs index
│   │   ├── system-architecture.md               # High-level system design
│   │   ├── odoo-framework-guide.md              # Odoo architecture deep dive
│   │   ├── module-architecture.md               # Module design patterns
│   │   ├── data-models.md                       # Database schema & ORM
│   │   ├── api-design.md                        # API architecture
│   │   └── integration-architecture.md          # POS, payments, e-invoice integration
│   │
│   ├── 05-implementation/                      # 💻 Implementation Guides
│   │   ├── index.md                             # Implementation index
│   │   │
│   │   ├── phase-1/                             # Phase 1: Payment Methods & Discounts
│   │   │   ├── index.md
│   │   │   ├── phase-1a-sinpe-implementation.md
│   │   │   ├── phase-1b-discount-codes.md
│   │   │   └── phase-1c-ciiu-codes.md
│   │   │
│   │   ├── phase-2/                             # Phase 2: Digital Signatures
│   │   │   ├── index.md
│   │   │   ├── signature-implementation.md
│   │   │   └── tilopay-integration.md
│   │   │
│   │   ├── phase-3/                             # Phase 3: Hacienda API
│   │   │   ├── index.md
│   │   │   ├── api-integration.md
│   │   │   └── retry-queue.md
│   │   │
│   │   ├── phase-4/                             # Phase 4: UI Polish
│   │   ├── phase-5/                             # Phase 5: PDF & Email
│   │   ├── phase-6/                             # Phase 6: Analytics
│   │   ├── phase-7/                             # Phase 7: Deployment
│   │   ├── phase-8/                             # Phase 8: Void Wizard
│   │   └── phase-9/                             # Phase 9: Tax Reports
│   │
│   ├── 06-deployment/                          # 🚀 Deployment & Operations
│   │   ├── index.md                             # Deployment docs index
│   │   ├── deployment-checklist.md              # Step-by-step deployment
│   │   ├── production-deployment-guide.md       # Complete production guide
│   │   ├── docker-setup.md                      # Docker configuration
│   │   ├── staging-deployment.md                # Staging environment
│   │   └── monitoring-setup.md                  # Monitoring & alerts
│   │
│   ├── 07-testing/                             # ✅ Testing & Validation
│   │   ├── index.md                             # Testing docs index
│   │   ├── validation-plan.md                   # Validation strategy
│   │   ├── test-execution-guide.md              # How to run tests
│   │   │
│   │   ├── test-results/                        # Test execution results
│   │   │   ├── compliance-validation.md
│   │   │   ├── phase-integration-tests.md
│   │   │   └── staging-test-results.md
│   │   │
│   │   └── test-suites/                         # Test suite documentation
│   │       ├── einvoice-test-suite.md
│   │       ├── void-wizard-tests.md
│   │       └── integration-tests.md
│   │
│   ├── 08-ui-ux/                               # 🎨 UI/UX Design
│   │   ├── index.md                             # UI/UX docs index
│   │   ├── user-research/                       # User research findings
│   │   │   ├── gym-owner-research.md
│   │   │   ├── user-research-summary.md
│   │   │   └── pain-points-analysis.md
│   │   │
│   │   ├── ux-audits/                           # UX audits
│   │   │   ├── einvoicing-ux-audit.md
│   │   │   └── ux-audit-summary.md
│   │   │
│   │   └── design-specs/                        # Design specifications
│   │       ├── ui-redesign-plan.md
│   │       ├── ui-mockups-reference.md
│   │       └── design-system.md
│   │
│   ├── 09-user-guides/                         # 📖 End User Documentation
│   │   ├── index.md                             # User guides index
│   │   ├── admin-guide.md                       # System administrator guide
│   │   ├── xml-import-user-guide.md             # XML import for users
│   │   ├── void-wizard-guide.md                 # Invoice void wizard
│   │   └── quick-actions-guide.md               # Common tasks quick reference
│   │
│   ├── 10-api-integration/                     # 🔌 Integration Documentation
│   │   ├── index.md                             # API docs index
│   │   ├── tilopay-api.md                       # TiloPay payment gateway
│   │   ├── hacienda-api.md                      # Costa Rica Hacienda API
│   │   ├── pos-integration-spec.md              # POS integration details
│   │   └── webhook-handling.md                  # Webhook implementation
│   │
│   ├── 11-development/                         # 🛠️ Developer Resources
│   │   ├── index.md                             # Dev docs index
│   │   ├── setup-guide.md                       # Dev environment setup
│   │   ├── module-cloning-guide.md              # Odoo module customization
│   │   ├── coding-standards.md                  # Code style & conventions
│   │   ├── git-workflow.md                      # Git branching strategy
│   │   └── troubleshooting.md                   # Common dev issues
│   │
│   └── 12-features/                            # 🎁 Feature Documentation
│       ├── index.md                             # Features index
│       ├── xml-import/                          # XML import feature
│       ├── payment-gateway/                     # Payment integration
│       ├── pos-membership/                      # POS membership
│       ├── void-wizard/                         # Invoice void wizard
│       └── tax-reports/                         # Tax reporting
│
├── _archive/                                    # 📦 HISTORICAL DOCUMENTATION
│   ├── README.md                                # Archive navigation & purpose
│   ├── originals/                               # Pre-consolidation files
│   │   ├── hulipractice/                        # Original HuliPractice files
│   │   ├── costa-rica/                          # Original CR research files
│   │   └── manifest.md                          # What was archived & when
│   │
│   └── session-notes/                           # Historical session metadata
│       ├── HULIPRACTICE-SESSION-STATE.md
│       └── RESUME-AFTER-REBOOT.md
│
├── _bmad-output/                                # 🤖 BMAD Workflow Artifacts
│   ├── planning-artifacts/                      # Product planning docs
│   ├── implementation-artifacts/                # Implementation guides
│   └── analysis/                                # Analysis & brainstorming
│
├── l10n_cr_einvoice/                           # 📄 E-Invoice Module
│   └── docs/                                    # Module-specific docs
│       ├── index.md                             # Module docs index
│       └── ... (module documentation)
│
└── payment_tilopay/                            # 💳 Payment Gateway Module
    └── docs/                                    # Module-specific docs
        ├── index.md                             # Module docs index
        └── ... (payment gateway docs)
```

---

## Navigation Architecture

### Three-Tier Navigation System

```
TIER 1: GLOBAL NAVIGATION
├─ docs/index.md (Global Master Index)
│  - Overview of entire documentation system
│  - Quick navigation by role (PM, Dev, Designer, QA)
│  - Quick navigation by task ("I need to...")
│  - Links to all 12 domain indices
│
TIER 2: DOMAIN NAVIGATION
├─ docs/02-research/index.md (Research Hub Index)
│  - Overview of research domain
│  - Links to competitive/, costa-rica/, market/, technical/
│  - Quick navigation within research
│
TIER 3: SUB-DOMAIN NAVIGATION
└─ docs/02-research/competitive/hulipractice/00-INTELLIGENCE-INDEX.md
   - Deep navigation within specific intelligence area
   - Layer-by-layer navigation (forensic → strategic → action)
   - Role-based entry points
   - Cross-references to related docs
```

### Navigation Elements in Every Document

**1. Frontmatter (YAML metadata)**
```yaml
---
title: "Document Title"
category: "research" # research, planning, architecture, implementation, etc.
domain: "competitive" # For research: competitive, costa-rica, market, technical
audience: ["product-manager", "developer", "designer"] # Target audiences
last_updated: "2026-01-01"
status: "production-ready" # draft, in-progress, production-ready, archived
version: "1.0.0"
maintainer: "Product Team" # Who owns this doc
related_docs: # Cross-references
  - "docs/02-research/costa-rica/00-COSTA-RICA-RESEARCH-INDEX.md"
  - "docs/03-planning/prd-gms-main.md"
keywords: ["hulipractice", "competitive analysis", "ux patterns"] # Search optimization
---
```

**2. Breadcrumb Navigation**
````markdown
```markdown
# 📍 Navigation Breadcrumb
[Home](../../../index.md) > [Research](../../index.md) > [Competitive](../index.md) > [HuliPractice](./00-INTELLIGENCE-INDEX.md) > Current Document
```
````

**3. Related Documents Section**
````markdown
```markdown
## 🔗 Related Documentation

**See Also:**
- [Costa Rica Research Hub](../../costa-rica/00-COSTA-RICA-RESEARCH-INDEX.md) - Compliance requirements
- [GMS PRD](../../../03-planning/prd-gms-main.md) - Product strategy
- [Implementation Roadmap](../../../05-implementation/index.md) - How to build
```
````

**4. Quick Navigation Section (Top of Document)**
````markdown
```markdown
## 🎯 Quick Navigation

| I Need To... | Go To |
|--------------|-------|
| Understand competitive landscape | [Strategic Analysis](#strategic-analysis) |
| Copy UX patterns | [UX Implementation Guide](./ux-implementation-guide.md) |
| See API endpoints | [Forensic Analysis](./forensic-analysis.md) |
```
````

---

## LLM Optimization Strategy

### YAML Frontmatter for Semantic Search

**All documents include:**
- **title:** Human-readable title
- **category:** Top-level classification
- **domain:** Sub-category
- **audience:** Who should read this
- **keywords:** Search terms for LLM
- **related_docs:** Semantic relationships

**LLM Benefits:**
- Agents can filter by category/domain/audience
- Keywords improve semantic search accuracy
- Related docs provide context graph
- Status indicates document freshness

### Keyword Strategy

**Primary Keywords (Always Include):**
- Document subject (e.g., "hulipractice", "costa-rica")
- Document type (e.g., "competitive-analysis", "migration-guide")
- Target domain (e.g., "gym-management", "einvoicing")

**Secondary Keywords (Context-Specific):**
- Technologies mentioned (e.g., "vue.js", "odoo", "xml")
- Features discussed (e.g., "consecutive-numbering", "api-integration")
- Use cases (e.g., "migration", "compliance", "ux-design")

### Document Summary Snippets

**Top of every document (after frontmatter):**
```markdown
## 📊 Executive Summary

**Purpose:** [One sentence describing what this document does]
**Audience:** [Who should read this]
**Key Takeaways:** [3-5 bullet points of main insights]
**Use This Document When:** [Common scenarios for referencing]
```

**LLM Benefits:**
- Quick context without reading full document
- Helps agents decide if document is relevant
- Provides high-level overview for summarization

### Semantic Relationships Graph

**Create:** `docs/DOCUMENTATION-GRAPH.md`

```markdown
# Documentation Relationship Graph

## HuliPractice Intelligence Network
- hulipractice/00-INTELLIGENCE-INDEX.md
  ├─ forensic-analysis.md (Layer 1: Technical)
  ├─ ux-implementation-guide.md (Layer 2: UX)
  │  └─ References: odoo-framework-guide.md (how to implement)
  ├─ strategic-analysis.md (Layer 3: Business)
  │  └─ References: prd-gms-main.md (competitive positioning)
  └─ action-plan.md (Layer 4: Implementation)
     └─ References: phase-*/index.md (execution phases)

## Costa Rica Compliance Network
- costa-rica/00-COSTA-RICA-RESEARCH-INDEX.md
  ├─ einvoice-providers-landscape.md
  ├─ migration-best-practices.md
  │  └─ References: implementation/phase-3/api-integration.md
  └─ compliance-requirements.md
     └─ References: testing/compliance-validation.md
```

---

## Human UX Enhancements

### Visual Aids

**1. Directory Tree Diagrams**
```markdown
# 📂 Documentation Structure

```
docs/
├── 01-getting-started/  ← Start here if you're new
├── 02-research/         ← Market & competitive intelligence
├── 03-planning/         ← Product strategy & roadmaps
├── 04-architecture/     ← System design
└── ... (12 categories)
```
```

**2. Intelligence Pyramid Visualization**
```markdown
# 🗂️ HuliPractice Intelligence Layers

```
       ┌─────────────────────┐
       │   ACTION PLANS      │ ← Week-by-week tasks
       │   (action-plan.md)  │
       └─────────────────────┘
              ▲
       ┌─────────────────────┐
       │ STRATEGIC ANALYSIS  │ ← Business intelligence
       │ (strategic-*.md)    │
       └─────────────────────┘
              ▲
       ┌─────────────────────┐
       │  DOMAIN EXPERTISE   │ ← UX & workflows
       │  (ux-guide.md)      │
       └─────────────────────┘
              ▲
       ┌─────────────────────┐
       │ FORENSIC CAPTURE    │ ← Technical data
       │ (forensic-*.md)     │
       └─────────────────────┘
```
```

**3. User Journey Flowcharts**
```markdown
# 🗺️ Documentation Navigation Paths

**Product Manager Journey:**
Research Hub → Competitive Analysis → Strategic Analysis → PRD

**Developer Journey:**
Architecture Docs → Implementation Guides → Code Examples → Testing

**Designer Journey:**
User Research → UX Audits → Design Specs → Mockups
```

### Quick-Start Workflows

**Create:** `docs/QUICK-START-GUIDE.md`

**Scenarios:**
1. **"I'm new to GMS"** → Onboarding path
2. **"I need to deploy to production"** → Deployment checklist
3. **"I'm researching competitors"** → Competitive intelligence hub
4. **"I need to understand compliance"** → Costa Rica research hub
5. **"I want to implement a feature"** → Implementation guides

### Mobile-Friendly Navigation

**Optimizations:**
- Short document names (display well on mobile GitHub)
- Emoji navigation aids (visual landmarks)
- Collapsible sections (GitHub markdown supports details/summary)
- Quick navigation tables at top (jump links)

**Example Mobile-Optimized Navigation:**
```markdown
<details>
<summary>🎯 Quick Navigation (Click to expand)</summary>

| I Need To... | Go Here |
|--------------|---------|
| Deploy | [Deployment Guide](#deployment) |
| Test | [Testing Guide](#testing) |
| Research | [Research Hub](#research) |

</details>
```

---

## Maintenance Framework

### Version Control Strategy

**Semantic Versioning for Documentation:**
- **Major (1.0.0 → 2.0.0):** Complete restructure or major content changes
- **Minor (1.0.0 → 1.1.0):** New documents added, significant updates
- **Patch (1.0.0 → 1.0.1):** Typo fixes, minor corrections

**Version Tracking:**
- Version number in YAML frontmatter
- CHANGELOG.md tracks major documentation updates
- Git tags for major versions (docs-v1.0.0, docs-v2.0.0)

### Document Ownership

**Ownership Model:**
```yaml
maintainer: "Product Team" # Who owns this doc
review_schedule: "quarterly" # How often to review
last_reviewed: "2026-01-01" # When last reviewed
next_review: "2026-04-01" # When next review is due
```

**Ownership Matrix:**

| Domain | Primary Owner | Review Schedule |
|--------|---------------|-----------------|
| Research (Competitive) | Product Team | Quarterly |
| Research (Costa Rica) | Compliance Team | Quarterly (or when regulations change) |
| Planning | Product Team | Monthly |
| Architecture | Engineering Team | Bi-annually |
| Implementation | Engineering Team | Per sprint |
| Deployment | DevOps Team | Monthly |
| Testing | QA Team | Per release |
| UI/UX | Design Team | Quarterly |
| User Guides | Product Team | Per major release |
| API Integration | Engineering Team | Per API version change |
| Development | Engineering Team | Quarterly |
| Features | Product Team | Per feature release |

### Update Workflow

**Process:**
1. **Trigger:** Code change, market update, regulation change, or scheduled review
2. **Update Document:** Edit content, update `last_updated` and `version`
3. **Update Related Docs:** Check cross-references, update if needed
4. **Update Indices:** Ensure domain and global indices reflect changes
5. **Commit:** Git commit with clear message (e.g., "docs: update CR compliance requirements v4.5")
6. **Review:** Peer review for major updates
7. **Publish:** Merge to main branch

### Deprecation Process

**When Document Becomes Outdated:**

**Option 1: Archive**
````markdown
```markdown
---
status: "archived"
archived_date: "2026-01-01"
archived_reason: "Replaced by docs/new-document.md"
replacement_doc: "docs/new-document.md"
---

# ⚠️ ARCHIVED DOCUMENT

**This document is archived and no longer maintained.**

**Reason:** Replaced by improved comprehensive guide
**Replacement:** [New Document](./new-document.md)
**Archived:** 2026-01-01

For historical reference only. Do not use for current implementation.

---

[Original content preserved below for history]
```
````

**Option 2: Move to Archive**
- Move file to `_archive/deprecated/`
- Create redirect in original location pointing to replacement
- Update all indices to remove reference

---

## Archive Strategy

### Archive Directory Structure

```
_archive/
├── README.md                      # Archive purpose & navigation
│
├── originals/                     # Pre-consolidation files
│   ├── manifest.md                # What was moved & when
│   ├── hulipractice/              # Original HuliPractice files (pre-consolidation)
│   │   ├── HULIPRACTICE-EXECUTIVE-SUMMARY.md
│   │   ├── HULIPRACTICE-COMPETITIVE-ANALYSIS.md
│   │   └── ... (other originals)
│   │
│   └── costa-rica/                # Original CR research (pre-consolidation)
│       ├── COSTA-RICA-EINVOICE-PROVIDERS-RESEARCH.md
│       └── ... (other originals)
│
├── session-notes/                 # Historical session metadata
│   ├── HULIPRACTICE-SESSION-STATE.md
│   └── RESUME-AFTER-REBOOT.md
│
└── deprecated/                    # Outdated documents replaced by newer versions
    └── (future deprecated docs)
```

### Archive Manifest

**File:** `_archive/originals/manifest.md`

```markdown
# Archive Manifest

## Files Archived During Documentation Consolidation (2026-01-01)

### HuliPractice Originals

**Consolidated Into:** `docs/02-research/competitive/hulipractice/strategic-analysis.md`

| Original File | Lines | Archived Date | Unique Content |
|--------------|-------|---------------|----------------|
| HULIPRACTICE-EXECUTIVE-SUMMARY.md | 468 | 2026-01-01 | Executive summary, feature gap matrix |
| HULIPRACTICE-COMPETITIVE-ANALYSIS.md | 865 | 2026-01-01 | Feature comparison, architectural analysis |

**Consolidated Into:** `docs/02-research/competitive/hulipractice/ux-implementation-guide.md`

| Original File | Lines | Archived Date | Unique Content |
|--------------|-------|---------------|----------------|
| HULIPRACTICE-UIUX-ANALYSIS.md | 1,297 | 2026-01-01 | UX patterns, Odoo implementation code |
| HULIPRACTICE-WORKFLOW-ANALYSIS.md | 818 | 2026-01-01 | User journey, workflow reconstruction |

### Costa Rica Originals

(Similar structure for CR research files)
```

### Archive Retention Policy

**Retention Rules:**
- **Originals (pre-consolidation):** Keep forever (historical reference)
- **Session Notes:** Keep forever (project history)
- **Deprecated Docs:** Keep for 2 years after deprecation, then delete if no references

**Rationale:** Originals preserve research history and investment. Session notes document decision-making process. Deprecated docs retained briefly for reference during transition.

---

## Documentation Standards

**Create:** `docs/DOCUMENTATION-STANDARDS.md`

**Standards Include:**
- **Markdown Formatting:** Consistent heading levels, code blocks, tables
- **Naming Conventions:** kebab-case for files, numbered prefixes for ordering
- **Frontmatter Template:** Standard YAML fields
- **Writing Style:** Clear, concise, professional tone
- **Code Examples:** Syntax highlighting, commented, runnable
- **Cross-References:** Always use relative paths (`./`, `../`)
- **Images & Diagrams:** Store in `docs/images/`, reference with relative paths
- **Emojis:** Use consistently for visual navigation (🎯, 📊, ✅, etc.)

---

## Implementation Checklist

**For Paige to Complete Phase 2:**

### Priority 1: Create Directory Structure ✅
- [ ] Create all 12 numbered subdirectories (01-12)
- [ ] Create `_archive/` with subdirectories (originals/, session-notes/, deprecated/)
- [ ] Verify all directories have proper permissions

### Priority 2: Update Global Index ✅
- [ ] Update `docs/index.md` to reference all 12 domains
- [ ] Add quick navigation by role (PM, Dev, Designer, QA)
- [ ] Add quick navigation by task ("I need to...")
- [ ] Link to domain indices

### Priority 3: Create Domain Indices ✅
- [ ] Create `index.md` for each of 12 domains
- [ ] Ensure consistent format across all indices
- [ ] Link domain indices to global index
- [ ] Add cross-references between related domains

### Priority 4: Consolidate Documents ✅
- [ ] HuliPractice: strategic-analysis.md (merge 3 files)
- [ ] HuliPractice: ux-implementation-guide.md (merge 2 files)
- [ ] HuliPractice: Copy forensic-analysis.md and action-plan.md as-is
- [ ] Costa Rica: einvoice-providers-landscape.md (merge 2 files)
- [ ] Costa Rica: migration-best-practices.md (extract from 1 file)
- [ ] Costa Rica: compliance-requirements.md (synthesize)
- [ ] Market: gym-management-software-2025.md (consolidate)

### Priority 5: Move Files to Final Locations ✅
- [ ] Move consolidated docs to proper directories
- [ ] Move phase docs to `05-implementation/phase-*/`
- [ ] Move testing docs to `07-testing/`
- [ ] Move UX docs to `08-ui-ux/`
- [ ] Move deployment docs to `06-deployment/`

### Priority 6: Archive Originals ✅
- [ ] Move original scattered files to `_archive/originals/`
- [ ] Create archive manifest with file metadata
- [ ] Move session notes to `_archive/session-notes/`
- [ ] Create `_archive/README.md` explaining purpose

### Priority 7: Update Cross-References ✅
- [ ] Update all internal links to point to new locations
- [ ] Add breadcrumb navigation to all documents
- [ ] Add "Related Documentation" sections
- [ ] Verify no broken links

### Priority 8: Add Metadata ✅
- [ ] Add YAML frontmatter to all consolidated documents
- [ ] Ensure all documents have `last_updated`, `version`, `status`
- [ ] Add keywords for LLM optimization
- [ ] Add maintainer and review schedule

### Priority 9: Create Supporting Documents ✅
- [ ] Create `DOCUMENTATION-STANDARDS.md`
- [ ] Create `QUICK-START-GUIDE.md`
- [ ] Create `DOCUMENTATION-GRAPH.md` (semantic relationships)
- [ ] Create `CHANGELOG.md` for documentation updates

### Priority 10: Quality Validation ✅
- [ ] Verify all links work
- [ ] Test navigation from global index to documents
- [ ] Validate YAML frontmatter syntax
- [ ] Spell check all new content
- [ ] Review with Mary (LLM optimization) and Winston (architecture)

---

## Success Criteria

**Phase 3 Complete When:**
- ✅ All architectural decisions documented
- ✅ Complete directory structure designed
- ✅ Navigation system defined with examples
- ✅ LLM optimization strategy specified
- ✅ Human UX enhancements planned
- ✅ Maintenance framework established
- ✅ Implementation checklist provided for Paige
- ✅ Standards and templates created
- ✅ Team has reviewed and approved

**Phase 2 Complete When (Paige's Work):**
- ✅ All directories created per architecture
- ✅ All documents consolidated and moved
- ✅ All cross-references updated
- ✅ All metadata added
- ✅ Archive complete with manifest
- ✅ No broken links
- ✅ Global and domain indices complete
- ✅ Quality validation passed

---

## Timeline

**Winston's Phase 3 Work:** 3-4 hours (Architecture design)
**Paige's Phase 2 Completion:** 4-5 hours (Implementation)

**Total Estimated Time to Complete Knowledge Repository:** ~8-9 hours

---

**Status:** ✅ **ARCHITECTURE APPROVED - READY FOR IMPLEMENTATION**

**Next Step:** Handoff to Paige for Phase 2 completion following this architecture blueprint.

---

**Architect:** Winston
**Approved By:** Product Team
**Date:** 2026-01-01
**Version:** 1.0.0
