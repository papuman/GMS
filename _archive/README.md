# 📦 Documentation Archive

**Purpose:** This directory preserves historical documentation for reference and audit trail purposes.

---

## Archive Structure

```
_archive/
├── README.md (this file)          # Archive navigation & purpose
├── originals/                     # Pre-consolidation files
│   ├── hulipractice/              # Original HuliPractice research files
│   ├── costa-rica/                # Original Costa Rica research files
│   └── manifest.md                # Archive catalog (what was moved & when)
│
├── session-notes/                 # Historical session metadata
│   └── (session state files)
│
└── deprecated/                    # Outdated documents replaced by newer versions
    └── (future deprecated docs)
```

---

## What's Archived Here

### 1. Originals (Pre-Consolidation Files)

**Purpose:** Preserve the original scattered documentation files before they were consolidated into the organized knowledge repository structure.

**Retention:** Permanent (historical reference)

**Use Cases:**
- Audit trail for documentation evolution
- Reference for what intelligence was captured when
- Historical context for decision-making
- Verify no information was lost during consolidation

**See:** [`originals/manifest.md`](./originals/manifest.md) for complete catalog

---

### 2. Session Notes (Historical Metadata)

**Purpose:** Preserve session state and project continuation notes from development work.

**Retention:** Permanent (project history)

**Use Cases:**
- Understanding project context and decision history
- Reconstructing work sessions for audit purposes
- Historical reference for "why we did X"

---

### 3. Deprecated (Outdated Documentation)

**Purpose:** Temporarily preserve documents that have been replaced by newer, improved versions.

**Retention:** 2 years after deprecation, then delete if no references remain

**Use Cases:**
- Transition period support (teams updating their bookmarks)
- Reference during migration to new documentation
- Comparison between old and new approaches

---

## Accessing Archived Content

**Warning:** Archived documents are **historical snapshots only** and may contain:
- Outdated information
- Superseded recommendations
- Deprecated technical details
- References to changed file locations

**Always use the current documentation** in `docs/` for accurate, up-to-date information.

**To Find Current Version:**
1. Check the archive manifest for replacement document path
2. Check frontmatter in archived document for `replacement_doc` field
3. Consult global index: [`docs/index.md`](../docs/index.md)

---

## Archive Policies

### What Gets Archived

**✅ Archived:**
- Original files before consolidation (originals/)
- Session state and continuation notes (session-notes/)
- Documentation replaced by newer versions (deprecated/)
- Historical research and analysis (preserved context)

**❌ NOT Archived:**
- Current production documentation (stays in `docs/`)
- Test results and execution logs (separate test directories)
- Code files (managed by git history)
- Binary files (screenshots, PDFs - referenced in docs)

### Retention Periods

| Category | Retention | Rationale |
|----------|-----------|-----------|
| Originals | Forever | Historical reference, audit trail |
| Session Notes | Forever | Project history, decision context |
| Deprecated | 2 years | Transition support, then cleanup |

---

## Archive Manifest

**Complete catalog of archived files:**
- [`originals/manifest.md`](./originals/manifest.md) - Pre-consolidation files
- (Future: deprecated/manifest.md when needed)

---

## Questions?

**For Current Documentation:** See [`docs/index.md`](../docs/index.md)

**For Archive Questions:**
- What was archived? → Check manifest files
- Where is current version? → Check replacement paths in manifests
- Why was this archived? → Check archive_reason in document frontmatter

---

**Last Updated:** 2026-01-01
**Maintained By:** Product Team
**Archive Started:** 2026-01-01 (Documentation consolidation project)
