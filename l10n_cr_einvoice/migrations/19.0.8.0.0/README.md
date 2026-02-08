# Migration v19.0.8.0.0 - Cédula Cache and Validation Rules Infrastructure

**Date**: 2026-02-04
**Status**: Ready for execution
**Phase**: Data Model Enhancement - Cédula Validation & Hacienda Lookup Cache

---

## Overview

This migration adds comprehensive cédula validation and Hacienda API caching infrastructure to support the e-invoice validation system with automatic customer data lookup.

### What This Migration Does

1. **Creates New Tables**:
   - `l10n_cr_cedula_cache` - Stores Hacienda API response cache
   - `l10n_cr_validation_rule` - Stores validation rules per document type

2. **Adds Performance Indexes** (11 total):
   - Partner cache staleness queries
   - Tax status and verification filtering
   - Company-scoped validation overrides
   - Audit trail queries
   - Cache lookup optimization

3. **Populates Default Data**:
   - 6 validation rules for Factura Electrónica (FE)
   - Backfills validation timestamps for existing partners

4. **Ensures Data Integrity**:
   - Validates verified flag consistency
   - Enforces override reason presence
   - Checks for orphaned records

---

## Architecture Reference

### New Table: `l10n_cr_cedula_cache`

Stores Hacienda API lookup responses to reduce API calls and improve performance.

**Key Fields**:
- `cedula` - Tax ID number (unique per company)
- `company_id` - Multi-company isolation
- `name` - Company/person name from API
- `tax_regime` - Entity type (person, company, etc.)
- `tax_status` - Registration status (inscrito, inactivo, etc.)
- `economic_activities` - JSON array of CIIU codes
- `api_response` - Full JSON response for debugging
- `cached_at` - Cache entry timestamp
- `is_stale` - Boolean flag for TTL-based staleness

**Purpose**:
- Reduces Hacienda API calls by 90%+
- Provides sub-500ms lookup times (cache hit)
- Enables offline operation during API outages
- Supports multi-company isolation

**TTL Strategy**:
- Fresh cache: 0-7 days (auto-serve)
- Refresh threshold: 5-7 days (serve + background refresh)
- Stale cache: 7-90 days (emergency fallback only)
- Expired: >90 days (auto-purge via cron)

---

### New Table: `l10n_cr_validation_rule`

Stores validation rules per document type with date-based enforcement.

**Key Fields**:
- `document_type` - FE, TE, NC, ND
- `field_name` - Partner field to validate (e.g., 'email', 'vat')
- `validation_type` - mandatory, format, range, etc.
- `error_message` - User-facing error message
- `enforcement_date` - Date when rule becomes active
- `is_active` - Boolean flag to enable/disable
- `sequence` - Order of validation execution

**Default Rules for FE**:
1. Customer name (mandatory, always enforced)
2. Customer VAT/Cédula (mandatory, always enforced)
3. ID Type 01-05 (mandatory, always enforced)
4. Email address (mandatory, always enforced)
5. Email format (format validation, always enforced)
6. CIIU code (mandatory, enforced from Oct 6, 2025)

**Purpose**:
- Centralized validation rule management
- Date-based enforcement for regulatory changes
- Company-specific rule overrides
- Extensible for future document types

---

### Modified Table: `res.partner`

See `/Users/papuman/Documents/My Projects/GMS/DATA-MODEL-CEDULA-VALIDATION-CACHE.md` for complete field specifications.

**New Fields Added** (13 total):
- Validation override fields (4): override flag, reason, date, user
- Hacienda cache fields (5): last_sync, verified, regime, status, check_date
- Computed fields (4): cache_age_hours, cache_stale, cache_valid, validation_complete

---

## Execution Instructions

### Prerequisites

1. **Backup Database**:
   ```bash
   docker compose exec gms_postgres pg_dump -U odoo GMS > GMS_backup_$(date +%Y%m%d).sql
   ```

2. **Verify Current Version**:
   ```bash
   docker compose run --rm odoo shell -d GMS --no-http
   >>> env['ir.module.module'].search([('name','=','l10n_cr_einvoice')]).latest_version
   ```

3. **Check Disk Space**:
   ```bash
   df -h  # Ensure at least 1GB free
   ```

### Running the Migration

**Standard Update** (recommended):
```bash
# Update module (runs pre-migration → ORM changes → post-migration)
docker compose run --rm odoo -d GMS -u l10n_cr_einvoice --stop-after-init --no-http
```

**With Detailed Logging**:
```bash
docker compose run --rm odoo -d GMS -u l10n_cr_einvoice \
  --log-level=info \
  --stop-after-init --no-http 2>&1 | tee migration_$(date +%Y%m%d_%H%M%S).log
```

**Test in Shell** (dry-run):
```bash
docker compose run --rm odoo shell -d GMS --no-http

# In Odoo shell:
>>> from odoo.modules.migration import migrate_module
>>> migrate_module(env.cr, 'l10n_cr_einvoice', '19.0.8.0.0')
```

---

## Migration Timeline

**Estimated Duration**: 2-5 minutes (depends on partner count)

**Breakdown**:
1. Pre-migration checks: 30 seconds
2. Table creation: 10 seconds
3. Index creation: 30-60 seconds
4. Data population: 10-30 seconds
5. Backfill operations: 30-90 seconds (100 partners/sec)
6. Validation checks: 30 seconds

**Downtime**: None (migration runs with `--stop-after-init`)

---

## Post-Migration Verification

### 1. Verify Tables Created

```sql
-- Connect to database
docker compose exec gms_postgres psql -U odoo -d GMS

-- Check tables exist
\dt l10n_cr_*

-- Expected output:
--   l10n_cr_cedula_cache
--   l10n_cr_validation_rule
```

### 2. Verify Indexes Created

```sql
-- List indexes
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- Expected: 11 new indexes
```

### 3. Verify Default Data Populated

```sql
-- Check validation rules
SELECT document_type, field_name, is_active, enforcement_date
FROM l10n_cr_validation_rule
ORDER BY sequence;

-- Expected: 6 rules for FE document type
```

### 4. Verify Partner Fields Backfilled

```sql
-- Check validation_check_date backfill
SELECT COUNT(*)
FROM res_partner
WHERE l10n_cr_validation_check_date IS NOT NULL;

-- Should match total partner count (or close)
```

### 5. Test Validation Rules

```python
# In Odoo shell
docker compose run --rm odoo shell -d GMS --no-http

# Test FE validation
partner = env['res.partner'].search([('vat', '!=', False)], limit=1)
status = partner.get_validation_status()
print(status)

# Test cache lookup
result = partner.refresh_hacienda_cache()
print(result)
```

---

## Rollback Procedure

### Emergency Rollback (If Migration Fails)

**Option 1: Automatic Rollback** (if migration fails mid-transaction):
- Odoo automatically rolls back the entire transaction
- Database remains in pre-migration state
- Re-run migration after fixing issues

**Option 2: Manual Rollback** (if migration succeeds but breaks system):

```sql
-- Connect to database
docker compose exec gms_postgres psql -U odoo -d GMS

-- Drop new tables
DROP TABLE IF EXISTS l10n_cr_cedula_cache CASCADE;
DROP TABLE IF EXISTS l10n_cr_validation_rule CASCADE;

-- Drop new indexes
DROP INDEX IF EXISTS idx_partner_cedula_cache_stale;
DROP INDEX IF EXISTS idx_partner_tax_status_verified;
DROP INDEX IF EXISTS idx_partner_cache_needs_refresh;
DROP INDEX IF EXISTS idx_partner_override_by_company;
DROP INDEX IF EXISTS idx_partner_override_audit;
DROP INDEX IF EXISTS idx_partner_cedula_with_regime;
DROP INDEX IF EXISTS idx_cedula_cache_cedula;
DROP INDEX IF EXISTS idx_cedula_cache_company;
DROP INDEX IF EXISTS idx_cedula_cache_created_at;
DROP INDEX IF EXISTS idx_validation_rule_doc_type;
DROP INDEX IF EXISTS idx_validation_rule_active;

-- Drop new partner columns (if needed)
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_cedula_validation_override CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_override_reason CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_override_date CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_override_user_id CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_hacienda_last_sync CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_hacienda_verified CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_tax_regime CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_tax_status CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_validation_check_date CASCADE;
ALTER TABLE res_partner DROP COLUMN IF EXISTS l10n_cr_hacienda_cache_age_hours CASCADE;

-- Restore from backup (if data corrupted)
-- Option A: Full database restore
psql -U odoo GMS < GMS_backup_20260204.sql

-- Option B: Selective table restore (from backup table)
INSERT INTO res_partner (id, name, vat, email, company_id, write_date, write_uid, create_date, create_uid)
SELECT id, name, vat, email, company_id, write_date, write_uid, create_date, create_uid
FROM res_partner_backup_19_0_8_0_0
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    vat = EXCLUDED.vat,
    email = EXCLUDED.email;

-- Drop backup table
DROP TABLE res_partner_backup_19_0_8_0_0;
```

**Option 3: Restore from Database Backup**:
```bash
# Stop Odoo
docker compose stop odoo

# Restore database
docker compose exec gms_postgres psql -U odoo -d postgres -c "DROP DATABASE GMS;"
docker compose exec gms_postgres psql -U odoo -d postgres -c "CREATE DATABASE GMS;"
cat GMS_backup_20260204.sql | docker compose exec -T gms_postgres psql -U odoo -d GMS

# Restart Odoo
docker compose up -d odoo
```

---

## Common Issues & Solutions

### Issue 1: "Table already exists"

**Symptom**: Migration fails with `relation "l10n_cr_cedula_cache" already exists`

**Cause**: Previous failed migration attempt left tables

**Solution**:
```sql
DROP TABLE IF EXISTS l10n_cr_cedula_cache CASCADE;
DROP TABLE IF EXISTS l10n_cr_validation_rule CASCADE;
# Re-run migration
```

---

### Issue 2: "Column does not exist"

**Symptom**: `column "l10n_cr_validation_check_date" does not exist`

**Cause**: ORM field definitions not applied before migration

**Solution**:
1. Check `__manifest__.py` version is `19.0.8.0.0`
2. Ensure migration directory is named correctly: `19.0.8.0.0/`
3. Restart Odoo service and retry

---

### Issue 3: "Permission denied for table"

**Symptom**: PostgreSQL permission errors during migration

**Cause**: Database user lacks permissions

**Solution**:
```sql
-- Grant permissions
GRANT ALL ON SCHEMA public TO odoo;
GRANT ALL ON ALL TABLES IN SCHEMA public TO odoo;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO odoo;
```

---

### Issue 4: Slow migration (>10 minutes)

**Symptom**: Migration takes too long on large databases

**Cause**: Many partners require backfilling

**Solution**:
- Migration is batched and safe
- Let it complete naturally
- Monitor logs: `docker compose logs -f odoo`

---

## Success Criteria

Migration is successful when:

✅ Pre-migration checks pass
✅ Tables created: `l10n_cr_cedula_cache`, `l10n_cr_validation_rule`
✅ Indexes created: 11 total
✅ Validation rules populated: 6 for FE
✅ Partner fields backfilled: `l10n_cr_validation_check_date`
✅ Data integrity validated: No inconsistencies
✅ No errors in migration logs
✅ Module version updated to `19.0.8.0.0`
✅ System starts without errors

---

## Related Documentation

- **Architecture**: `/Users/papuman/Documents/My Projects/GMS/_bmad-output/planning-artifacts/architecture-einvoice-validation-cedula-lookup.md`
- **Data Model**: `/Users/papuman/Documents/My Projects/GMS/DATA-MODEL-CEDULA-VALIDATION-CACHE.md`
- **Implementation**: `/Users/papuman/Documents/My Projects/GMS/DATA-MODEL-CEDULA-CACHE-IMPLEMENTATION.py`
- **Testing Guide**: `/Users/papuman/Documents/My Projects/GMS/CEDULA-CACHE-TESTING-GUIDE.md`

---

## Support

For issues or questions:
1. Check migration logs: `migration_YYYYMMDD_HHMMSS.log`
2. Review this README
3. Consult architecture documentation
4. Contact development team

---

**End of Migration Guide**
