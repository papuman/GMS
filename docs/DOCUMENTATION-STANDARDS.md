---
title: "Documentation Standards - Writing & Formatting Guidelines"
category: "documentation"
domain: "meta"
layer: "standards"
audience: ["all", "documentation-team", "developer"]
last_updated: "2026-01-01"
status: "production-ready"
version: "1.0.0"
maintainer: "Documentation Team"
description: "Comprehensive standards for writing, formatting, and maintaining GMS documentation"
keywords: ["documentation", "standards", "guidelines", "formatting", "writing-style", "yaml", "markdown"]
---

# 📍 Navigation Breadcrumb
[Home](index.md) > Documentation Standards

---

# 📝 Documentation Standards
**Writing & Formatting Guidelines**

**Version:** 1.0.0
**Last Updated:** 2026-01-01
**Status:** ✅ Production Ready
**Owner:** Documentation Team

---

## 📊 Executive Summary

This document defines the standards for all GMS documentation, ensuring consistency, clarity, and discoverability across the knowledge repository.

**Why Standards Matter:**
- ✅ **Consistency:** Readers know what to expect
- ✅ **Discoverability:** LLMs can find relevant docs efficiently
- ✅ **Maintainability:** Easy to update and expand
- ✅ **Professionalism:** Reflects quality of the product
- ✅ **Onboarding:** New team members learn patterns quickly

**Scope:**
- YAML frontmatter requirements
- Markdown formatting conventions
- Document structure templates
- Writing style guidelines
- Naming conventions
- Version control practices

---

## 🎯 Table of Contents

1. [YAML Frontmatter Standards](#yaml-frontmatter-standards)
2. [Markdown Formatting](#markdown-formatting)
3. [Document Structure](#document-structure)
4. [Writing Style Guide](#writing-style-guide)
5. [Naming Conventions](#naming-conventions)
6. [Version Control](#version-control)
7. [LLM Optimization](#llm-optimization)
8. [Review Process](#review-process)

---

## 1. YAML Frontmatter Standards

### Required Fields (All Documents)

Every documentation file MUST include YAML frontmatter at the top:

```yaml
---
title: "Clear, Descriptive Title - Subtitle if Needed"
category: "category-name"
domain: "domain-name"
layer: "index|domain|document|reference"
audience: ["role1", "role2"]
last_updated: "YYYY-MM-DD"
status: "draft|in-review|production-ready|deprecated"
version: "X.Y.Z"
maintainer: "Team Name"
description: "One-sentence description of document purpose"
keywords: ["keyword1", "keyword2", "keyword3"]
---
```

### Field Definitions

**title:**
- Format: "Primary Title - Optional Subtitle"
- Style: Title Case
- Length: 50-100 characters
- Example: "User Guides Documentation - End-User Help & Quick Reference Index"

**category:**
- Purpose: High-level categorization
- Values: `research`, `planning`, `architecture`, `implementation`, `deployment`, `testing`, `ui-ux`, `user-guides`, `api-integration`, `development`, `features`, `getting-started`, `documentation`
- Format: lowercase, hyphenated

**domain:**
- Purpose: Semantic domain for LLM search
- Examples: `research-hub`, `planning`, `architecture`, `ui-ux`
- Format: lowercase, hyphenated

**layer:**
- Purpose: Document hierarchy level
- Values:
  - `index` - Top-level domain index (e.g., docs/05-implementation/index.md)
  - `domain` - Sub-domain index (e.g., docs/02-research/competitive/index.md)
  - `document` - Standard documentation file
  - `reference` - Quick reference card
  - `standards` - Meta-documentation (this file)

**audience:**
- Purpose: Target readers (for filtering)
- Values: `["all"]`, `["developer"]`, `["product-manager"]`, `["gym-owner"]`, `["front-desk"]`, `["admin"]`, `["stakeholder"]`
- Format: Array of lowercase, hyphenated strings

**last_updated:**
- Format: ISO 8601 date (YYYY-MM-DD)
- Example: "2026-01-01"
- Update whenever content changes

**status:**
- Values:
  - `draft` - Work in progress
  - `in-review` - Pending team review
  - `production-ready` - Approved and published
  - `deprecated` - Outdated, kept for reference
- Emoji indicators in document:
  - 🔄 Draft
  - 👀 In Review
  - ✅ Production Ready
  - ⚠️ Deprecated

**version:**
- Format: Semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes or complete rewrites
- MINOR: New sections or significant additions
- PATCH: Minor corrections, typos, clarifications
- Example: "1.0.0", "1.2.3", "2.0.0"

**maintainer:**
- Team or person responsible for updates
- Examples: "Documentation Team", "Backend Team", "Product Team"

**description:**
- One concise sentence describing document purpose
- Length: 50-150 characters
- No period at end
- Example: "Comprehensive standards for writing, formatting, and maintaining GMS documentation"

**keywords:**
- Array of 5-15 search terms
- Include synonyms, abbreviations, common misspellings
- Format: lowercase, hyphenated
- Example: `["documentation", "standards", "guidelines", "formatting", "writing-style"]`

### Optional Fields

**related_docs:**
```yaml
related_docs:
  - path: "../05-implementation/index.md"
    title: "Implementation Domain"
    why: "See implementation guides for context"
  - path: "../02-research/index.md"
    title: "Research Hub"
    why: "Research backing design decisions"
```

**changelog:**
```yaml
changelog:
  - version: "1.0.0"
    date: "2026-01-01"
    changes: "Initial release"
  - version: "1.1.0"
    date: "2026-02-15"
    changes: "Added LLM optimization section"
```

---

## 2. Markdown Formatting

### Headers

**Hierarchy:**
```markdown
# Level 1 - Document Title (Only ONE per document)
## Level 2 - Major Section
### Level 3 - Subsection
#### Level 4 - Sub-subsection (use sparingly)
```

**Rules:**
- ✅ Always use ATX-style headers (`#`) not Setext (`===`, `---`)
- ✅ Include space after `#` symbols
- ✅ Use Title Case for H1, H2
- ✅ Use Sentence case for H3, H4
- ✅ No punctuation at end of headers
- ❌ Don't skip levels (e.g., H2 → H4)

### Lists

**Unordered Lists:**
```markdown
- Use hyphens (not asterisks or plus)
- Maintain consistent indentation (2 spaces)
  - Nested item
  - Another nested item
- Back to parent level
```

**Ordered Lists:**
```markdown
1. Use sequential numbers
2. Start at 1, increment by 1
3. Use periods after numbers
   - Can mix with unordered
   - For sub-items
```

**Task Lists:**
```markdown
- ✅ Completed item (use checkmark emoji)
- 🔄 In progress (use cycle emoji)
- ❌ Blocked/failed (use X emoji)
- ⏳ Pending (use hourglass emoji)
```

### Code Blocks

**Fenced Code Blocks (Preferred):**
````markdown
```python
def example_function():
    """Always include language identifier."""
    return "formatted code"
```
````

**Supported Languages:**
- `python` - Python code
- `javascript` or `js` - JavaScript
- `xml` - XML/HTML
- `bash` or `shell` - Shell commands
- `sql` - SQL queries
- `yaml` - YAML configuration
- `json` - JSON data
- `css` - CSS styles

**Inline Code:**
```markdown
Use `backticks` for inline code, variable names, file names.
Examples: `l10n_cr_einvoice`, `account.move`, `POST /api/v1/invoices`
```

### Tables

**Standard Table Format:**
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

**Alignment:**
```markdown
| Left | Center | Right |
|:-----|:------:|------:|
| Text | Text   | Text  |
```

**Complex Tables:**
- Keep cell content concise
- Use abbreviations if needed
- Add table caption above table
- Link to detailed docs if table too complex

### Links

**Internal Links (Relative):**
````markdown
```markdown
[Link Text](../path/to/file.md)
[Implementation Guide](../05-implementation/index.md)
[Section in Same File](#section-anchor)
```
````

**External Links:**
```markdown
[Odoo Documentation](https://www.odoo.com/documentation/19.0)
[Hacienda API](https://www.hacienda.go.cr/factura-electronica)
```

**Reference-Style Links:**
```markdown
See the [Odoo docs][odoo] for details.

[odoo]: https://www.odoo.com/documentation/19.0
```

### Emphasis

**Bold:**
```markdown
Use **bold** for:
- Important terms on first use
- UI element names (e.g., **Submit** button)
- Strong emphasis
```

**Italic:**
```markdown
Use *italic* for:
- Book/document titles
- Foreign words (e.g., *cédula jurídica*)
- Mild emphasis
```

**Code:**
```markdown
Use `code` for:
- Variable names
- File names
- Code snippets
- API endpoints
- Database table/field names
```

### Blockquotes

```markdown
> Use blockquotes for:
> - Important callouts
> - Quotes from specifications
> - Warning messages

> **Note:** This is a note blockquote.
> Use bold for the type (Note, Warning, Tip).
```

### Horizontal Rules

```markdown
Use three hyphens for section breaks:

---

Not asterisks (***) or underscores (___).
```

### Emojis

**Approved Emojis:**
- ✅ Completed/Success
- 🔄 In Progress
- ❌ Failed/Error
- ⚠️ Warning
- 📊 Data/Analytics
- 🎯 Goal/Target
- 🚀 Deployment/Launch
- 📝 Documentation
- 🔍 Search/Find
- 💡 Tip/Idea
- 🎨 Design/UI
- 🔐 Security
- 🔌 Integration/API
- 📱 Mobile
- 🖥️ Desktop

**Usage:**
- Use sparingly (1-2 per section max)
- Consistent meaning across all docs
- Don't replace words with emojis in prose

---

## 3. Document Structure

### Standard Document Template

```markdown
---
title: "Document Title - Subtitle"
category: "category-name"
# ... (complete YAML frontmatter)
---

# 📍 Navigation Breadcrumb
Home > Parent Domain > Current Document

---

# Document Title
**Subtitle or Tagline**

**Version:** 1.0.0
**Last Updated:** 2026-01-01
**Status:** ✅ Production Ready
**Owner:** Team Name

---

## 📊 Executive Summary

[2-3 paragraph overview of document contents, purpose, and key takeaways]

**Key Points:**
- Bullet list of 3-5 most important items
- What reader will learn
- Why this matters

---

## 🎯 Quick Navigation / Table of Contents

| I Need To... | Go Here |
|--------------|---------|
| Common task 1 | Link to section |
| Common task 2 | Link to section |

---

## Main Content Sections

[Organized by topic, with clear headers and subsections]

---

## 🔍 Search Keywords (For LLM Agents)

**Category 1:**
- `keyword1`, `keyword2`, `keyword3`

**Category 2:**
- `keyword4`, `keyword5`, `keyword6`

---

## 🔗 Related Documentation

**For [Purpose]:**
- Document Title - Brief description
- Another Document - Brief description

---

## 🔄 Maintenance & Updates

### Update Schedule

- **Trigger 1** - When to update (e.g., "After feature release")
- **Trigger 2** - Regular schedule (e.g., "Monthly review")

### Document Ownership

| Section | Owner |
|---------|-------|
| Section 1 | Team A |
| Section 2 | Team B |

---

## ✅ Document Status

**Status:** ✅ **PRODUCTION READY - v1.0.0**
**Coverage:**
- ✅ Topic 1 documented
- ✅ Topic 2 documented
- 🔄 Topic 3 in progress

**Last Update:** 2026-01-01
**Next Review:** 2026-02-01

---

**📝 Document Maintained By:** Team Name
**Version:** 1.0.0
**Last Updated:** 2026-01-01
```

### Index Document Template

Index documents (domain-level) should follow this structure:

```markdown
---
title: "Domain Name Documentation - Index"
category: "domain-name"
domain: "domain-name"
layer: "index"
# ... (complete YAML frontmatter)
---

# 📍 Navigation Breadcrumb
Home > Domain Name Documentation

---

# 🔍 Domain Name Documentation
**Subtitle - Master Index**

**Version:** 1.0.0
**Last Updated:** 2026-01-01
**Status:** ✅ Production Ready
**Lead:** Team Name

---

## 📊 Executive Summary

[Overview of domain, what it contains, current status]

---

## 🎯 Quick Navigation

| I Need To... | Go Here |
|--------------|---------|
| [Task 1] | [Link] |
| [Task 2] | [Link] |

---

## 📚 Domain Categories

### 1. Category Name

**Purpose:** Brief description
**Status:** ✅ Complete / 🔄 In Progress

[Details about this category, links to documents]

### 2. Another Category

[Repeat pattern...]

---

## 🔍 Search Keywords (For LLM Agents)

**Domain:**
- `keywords`, `related`, `to-domain`

---

## 🔗 Related Documentation

[Links to related domains]

---

## 🔄 Maintenance & Updates

[Update schedule and ownership]

---

## ✅ Domain Status

[Status summary]
```

---

## 4. Writing Style Guide

### Voice & Tone

**Active Voice (Preferred):**
- ✅ "The system generates XML"
- ❌ "XML is generated by the system"

**Direct Address:**
- ✅ "You can create invoices by..."
- ❌ "One can create invoices by..."
- ✅ "Click the **Submit** button"
- ❌ "The Submit button should be clicked"

**Present Tense:**
- ✅ "The function returns a value"
- ❌ "The function will return a value"

**Concise:**
- ✅ "Use Docker for deployment"
- ❌ "It is recommended that you should consider using Docker as a viable option for deployment"

### Technical Writing Guidelines

**Be Specific:**
```markdown
❌ "Configure the settings appropriately"
✅ "Set the polling interval to 5 minutes"

❌ "Install the necessary dependencies"
✅ "Run `pip install -r requirements.txt`"
```

**Define Acronyms:**
```markdown
First use: "Costa Rica Dirección General de Tributación (DGT)"
Subsequent: "DGT" or "Hacienda"

First use: "Point of Sale (POS)"
Subsequent: "POS"
```

**Avoid Jargon:**
```markdown
❌ "Leverage the synergy between modules"
✅ "Use modules together"

❌ "Utilize the paradigm"
✅ "Use the pattern"
```

**Use Examples:**
```markdown
Good: "Valid CIIU codes include 9311 (gym operation), 9312 (fitness center)"
Better: "For a gym, use CIIU code 9311. For example:
- CrossFit box: 9311
- Yoga studio: 9312
- Personal training: 9311"
```

### Formatting Guidelines

**Numbers:**
- 0-10: Spell out ("five invoices")
- 11+: Use digits ("15 invoices", "200 customers")
- Technical: Always digits ("8GB RAM", "3.5 seconds")
- Percentages: Always digits ("95% coverage")

**Dates:**
- ISO 8601: 2026-01-01 (YYYY-MM-DD)
- Avoid: "January 1st, 2026" or "01/01/2026"

**Currency:**
- Costa Rica: ₡50,000 (colón symbol, comma separators)
- USD: $50.00 (dollar sign, decimal point)

**Time:**
- 24-hour format: 14:30
- Avoid: 2:30 PM

**File Paths:**
- Unix-style: `/path/to/file.md`
- Always absolute or clearly relative: `../parent/file.md`
- Use `code formatting` for paths: `odoo/addons/l10n_cr_einvoice/`

### Capitalization

**Title Case (Headers H1, H2):**
```markdown
## Costa Rica E-Invoice Compliance Guide
## Payment Gateway Integration Tutorial
```

**Sentence case (Headers H3, H4):**
```markdown
### Configure the certificate
### Set up Hacienda credentials
```

**Product Names:**
- GMS (always uppercase)
- Odoo (capital O)
- TiloPay (camel case)
- PostgreSQL (capital SQL)
- Costa Rica (always capital C and R)
- Hacienda (capital H when referring to DGT)

**UI Elements:**
- Use **bold** for button/menu names
- Match exact capitalization from UI
- Example: "Click **Submit to Hacienda**"

---

## 5. Naming Conventions

### File Naming

**General Rules:**
- Use UPPERCASE for important/summary docs: `README.md`, `PHASE3-IMPLEMENTATION-COMPLETE.md`
- Use lowercase for supporting docs: `architecture-decisions.md`, `setup-guide.md`
- Use hyphens (not underscores or spaces): `user-research-summary.md`
- Be descriptive: `costa-rica-einvoice-compliance.md` not `cr-comp.md`

**Prefixes:**
```
PHASE[N]-          Implementation phase docs
QUICK-            Quick reference cards
GYM_MANAGEMENT_   Product-level docs (legacy, maintain consistency)
```

**Extensions:**
- Documentation: `.md`
- Images: `.png`, `.jpg`, `.svg`
- Data: `.json`, `.yaml`
- Code: `.py`, `.js`, `.xml`

### Directory Naming

**Numbered Directories:**
```
01-getting-started/
02-research/
03-planning/
...
12-features/
```

**Sub-directories:**
```
competitive/
costa-rica/
market/
technical/
```

**Rules:**
- Lowercase, hyphenated
- Descriptive, not abbreviated
- Singular or plural (be consistent within domain)

---

## 6. Version Control

### Git Commit Messages

**Format:**
```
type(scope): brief description

Detailed explanation (if needed)

- Bullet points for multiple changes
- Reference issues: Closes #123
```

**Types:**
- `docs`: Documentation changes
- `feat`: New feature documentation
- `fix`: Fix errors in documentation
- `refactor`: Reorganize without content change
- `style`: Formatting fixes only

**Examples:**
```bash
docs(research): add HuliPractice competitive analysis

docs(deployment): update production deployment guide

Expanded security section with certificate management.
Added monitoring setup procedures.

fix(standards): correct YAML frontmatter examples

refactor(index): reorganize domain navigation structure
```

### Branching Strategy

**Documentation Updates:**
```
main                    # Production-ready docs
  ├─ docs/feature-name  # Documentation for new feature
  ├─ docs/update-guide  # Update existing guide
  └─ docs/fix-typos     # Quick fixes
```

**Review Process:**
1. Create branch: `docs/descriptive-name`
2. Make changes
3. Self-review (use checklist below)
4. Create pull request
5. Peer review (1+ approver)
6. Merge to main

---

## 7. LLM Optimization

### Search Keywords

**Purpose:** Help LLMs find relevant documents quickly

**Guidelines:**
- Include 5-15 keywords per document
- Mix of:
  - Primary terms (e.g., "deployment", "testing")
  - Synonyms (e.g., "deployment", "production", "go-live")
  - Technical terms (e.g., "docker", "kubernetes")
  - Common misspellings (e.g., "hacienda", "acienda")
  - Abbreviations (e.g., "api", "rest-api", "restful")

**Organization:**
```markdown
## 🔍 Search Keywords (For LLM Agents)

**Primary Domain:**
- `keyword1`, `keyword2`, `keyword3`

**Related Concepts:**
- `keyword4`, `keyword5`, `keyword6`

**Technical:**
- `keyword7`, `keyword8`, `keyword9`
```

### Metadata Richness

**Why It Matters:**
- LLMs use YAML frontmatter to filter and rank documents
- Rich metadata = better search results
- `audience` field enables role-based filtering

**Best Practices:**
- Always complete all required YAML fields
- Use consistent values (from controlled vocabularies)
- Add `related_docs` for semantic connections
- Keep `description` clear and keyword-rich

### Semantic Structure

**Breadcrumb Navigation:**
````markdown
```markdown
# 📍 Navigation Breadcrumb
[Home](../index.md) > [Domain](../domain/index.md) > Current Doc
```
````

**Benefits:**
- LLMs understand document hierarchy
- Humans can navigate up the tree
- Shows document context

**Related Documentation Section:**
````markdown
```markdown
## 🔗 Related Documentation

**For [Purpose]:**
- [Doc Title](path.md) - Why it's related

**For [Another Purpose]:**
- [Doc Title](path.md) - Why it's related
```
````

**Benefits:**
- Creates semantic graph
- LLMs can traverse relationships
- Humans discover related content

---

## 8. Review Process

### Self-Review Checklist

Before submitting for peer review, verify:

**YAML Frontmatter:**
- [ ] All required fields present
- [ ] `last_updated` is today's date
- [ ] `version` incremented appropriately
- [ ] `keywords` array has 5-15 relevant terms
- [ ] `description` is clear and concise

**Markdown Formatting:**
- [ ] Headers follow hierarchy (no skipped levels)
- [ ] Code blocks have language identifiers
- [ ] Tables are properly formatted
- [ ] Lists use consistent style (hyphens for unordered)
- [ ] Links work (internal and external)

**Content Quality:**
- [ ] No spelling or grammar errors
- [ ] Active voice used
- [ ] Present tense used
- [ ] Examples included where helpful
- [ ] Acronyms defined on first use
- [ ] Screenshots/diagrams added if needed

**Structure:**
- [ ] Breadcrumb navigation present
- [ ] Executive summary included
- [ ] Quick navigation table (for indices)
- [ ] Search keywords section
- [ ] Related documentation section
- [ ] Maintenance schedule defined
- [ ] Status section complete

**Accessibility:**
- [ ] Alt text for images
- [ ] Tables have headers
- [ ] Links have descriptive text (not "click here")
- [ ] Color not the only indicator

### Peer Review Checklist

Reviewers should check:

**Accuracy:**
- [ ] Technical information is correct
- [ ] Code examples work as shown
- [ ] Links point to correct destinations
- [ ] Version numbers match actual releases

**Clarity:**
- [ ] Content is understandable by target audience
- [ ] Examples are clear and relevant
- [ ] Jargon is explained or avoided
- [ ] Structure aids comprehension

**Completeness:**
- [ ] All promised sections delivered
- [ ] No TODO or placeholder text
- [ ] References are complete
- [ ] Related docs are linked

**Consistency:**
- [ ] Follows documentation standards (this doc)
- [ ] Matches style of related documents
- [ ] Terminology is consistent across docs
- [ ] Formatting is consistent

### Approval Process

**Required Approvers by Document Type:**

| Document Type | Approvers Needed | Who |
|---------------|-----------------|-----|
| Standards/Meta | 2 | Documentation Lead + Tech Lead |
| Architecture | 2 | Tech Lead + Senior Dev |
| Implementation | 1 | Tech Lead or Senior Dev |
| User Guides | 1 | Documentation Team or Product |
| Quick Reference | 1 | Domain Expert |
| Typo/Minor Fix | 0 | Self-merge OK |

---

## 📊 Documentation Quality Metrics

### Quality Indicators

**Excellent Documentation:**
- ✅ Complete YAML frontmatter
- ✅ Clear executive summary
- ✅ Code examples that work
- ✅ Screenshots where helpful
- ✅ Links all valid
- ✅ Updated in last 90 days
- ✅ 2+ peer reviews

**Needs Improvement:**
- ⚠️ Missing YAML fields
- ⚠️ No examples
- ⚠️ Broken links
- ⚠️ Last updated > 6 months ago
- ⚠️ No peer review

### Metrics to Track

**Document Health:**
- Last update date
- Number of broken links
- Number of TODOs/placeholders
- Review coverage (% with peer review)

**Usage Metrics:**
- Search hits (if tracking available)
- User feedback/ratings
- Support tickets referencing doc

---

## 🔧 Tools & Automation

### Recommended Tools

**Markdown Linting:**
```bash
# Install markdownlint
npm install -g markdownlint-cli

# Lint all docs
markdownlint docs/**/*.md
```

**Link Checking:**
```bash
# Install markdown-link-check
npm install -g markdown-link-check

# Check links
markdown-link-check docs/**/*.md
```

**Spell Checking:**
```bash
# Install codespell
pip install codespell

# Check spelling
codespell docs/
```

**YAML Validation:**
```bash
# Install yamllint
pip install yamllint

# Validate YAML frontmatter (requires extraction)
```

### Pre-commit Hooks

Recommended pre-commit hook to enforce standards:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run markdown linter
markdownlint docs/**/*.md || exit 1

# Check for broken links (optional, slow)
# markdown-link-check docs/**/*.md || exit 1

# Spell check
codespell docs/ || exit 1

echo "Documentation checks passed ✅"
```

---

## 📋 Quick Reference Card

**Creating New Documentation:**

1. **Copy template** from this document
2. **Fill YAML frontmatter** (all required fields)
3. **Write content** following style guide
4. **Add breadcrumb** navigation
5. **Include search keywords**
6. **Link related docs**
7. **Self-review** using checklist
8. **Submit for peer review**
9. **Update version** on approval
10. **Merge to main**

**Updating Existing Documentation:**

1. **Read current version** fully
2. **Increment version** (patch for minor, minor for additions)
3. **Update `last_updated`** field
4. **Make changes** following standards
5. **Update changelog** (if present)
6. **Self-review** using checklist
7. **Submit for peer review** (if major change)
8. **Merge to main**

---

## ✅ Documentation Standards Status

**Status:** ✅ **PRODUCTION READY - v1.0.0**

**This document:**
- ✅ Defines all required standards
- ✅ Provides clear examples
- ✅ Includes review checklists
- ✅ Covers LLM optimization
- ✅ Addresses quality metrics

**Enforcement:**
- ✅ Pre-commit hooks recommended
- ✅ Peer review process defined
- ✅ Quality metrics tracked

**Last Update:** 2026-01-01
**Next Review:** 2026-04-01 (Quarterly)

---

**📝 Documentation Standards Maintained By:** GMS Documentation Team
**Version:** 1.0.0
**Last Updated:** 2026-01-01

---

## Appendix A: YAML Field Values

### Controlled Vocabularies

**category:**
- `research`
- `planning`
- `architecture`
- `implementation`
- `deployment`
- `testing`
- `ui-ux`
- `user-guides`
- `api-integration`
- `development`
- `features`
- `getting-started`
- `documentation`

**layer:**
- `index` - Domain index
- `domain` - Sub-domain index
- `document` - Standard doc
- `reference` - Quick reference
- `standards` - Meta-documentation

**status:**
- `draft` - 🔄 Work in progress
- `in-review` - 👀 Pending review
- `production-ready` - ✅ Published
- `deprecated` - ⚠️ Outdated

**audience:**
- `all`
- `developer`
- `product-manager`
- `gym-owner`
- `front-desk`
- `admin`
- `stakeholder`
- `designer`
- `architect`
- `integration-specialist`
- `devops`
- `system-admin`
- `end-user`
- `documentation-team`

---

## Appendix B: Common Patterns

### Pattern: Technical Tutorial

```markdown
## Tutorial: [Task Name]

**⏱️ Time:** 15 minutes
**Prerequisites:**
- Prerequisite 1
- Prerequisite 2

**Step 1: [Action]**
[Instructions]

```code
Example code
```

**Step 2: [Action]**
[Instructions]

**Troubleshooting:**
- **Issue:** Description
  - **Solution:** Fix

**Next Steps:**
- Link to related tutorial
```

### Pattern: API Documentation

```markdown
## API Endpoint: `POST /api/endpoint`

**Purpose:** Brief description

**Request:**
```json
{
  "field": "value"
}
```

**Response:**
```json
{
  "result": "success"
}
```

**Error Codes:**
- `400` - Bad Request: Description
- `401` - Unauthorized: Description
```

### Pattern: Configuration Guide

```markdown
## Configuration: [Feature Name]

**Location:** Path to config file

**Settings:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `setting_name` | string | "default" | What it does |

**Example:**
```yaml
setting_name: "custom_value"
another_setting: true
```

**Validation:**
```bash
# Test configuration
command --validate
```
```
