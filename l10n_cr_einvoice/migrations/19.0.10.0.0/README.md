# Migration 19.0.10.0.0 - Cédula Cache Table

## Purpose
Creates the `l10n_cr_cedula_cache` table for storing Hacienda API company data with multi-tier caching strategy.

## Table Structure

### Fields (19 total)
1. **cedula** - VARCHAR NOT NULL, indexed
2. **name** - VARCHAR NOT NULL, indexed  
3. **company_type** - VARCHAR DEFAULT 'other'
4. **tax_regime** - VARCHAR
5. **tax_status** - VARCHAR NOT NULL DEFAULT 'inscrito', indexed
6. **economic_activities** - TEXT (JSONB stored as TEXT)
7. **primary_activity** - VARCHAR
8. **ciiu_code_id** - INTEGER, FK to l10n_cr_ciiu_code
9. **cache_tier** - VARCHAR (computed, stored)
10. **fetched_at** - TIMESTAMP NOT NULL, indexed
11. **refreshed_at** - TIMESTAMP NOT NULL, indexed
12. **access_count** - INTEGER DEFAULT 0
13. **last_access_at** - TIMESTAMP
14. **cache_age_hours** - NUMERIC (computed, stored)
15. **cache_age_days** - INTEGER (computed, stored)
16. **source** - VARCHAR DEFAULT 'hacienda'
17. **raw_response** - TEXT (JSONB stored as TEXT)
18. **error_message** - TEXT
19. **company_id** - INTEGER NOT NULL, FK to res_company, indexed

### Foreign Keys (4 total)
1. `company_id` → `res_company(id)` ON DELETE CASCADE
2. `ciiu_code_id` → `l10n_cr_ciiu_code(id)` ON DELETE SET NULL
3. `create_uid` → `res_users(id)` ON DELETE SET NULL
4. `write_uid` → `res_users(id)` ON DELETE SET NULL

### Unique Constraints (1 total)
- `cedula_company_unique`: UNIQUE(cedula, company_id)

### Indexes (6 total)
1. `l10n_cr_cedula_cache_cedula_idx` - For cédula lookups
2. `l10n_cr_cedula_cache_name_idx` - For name searches
3. `l10n_cr_cedula_cache_tax_status_idx` - For filtering active entries
4. `l10n_cr_cedula_cache_fetched_at_idx` - For cache age queries
5. `l10n_cr_cedula_cache_refreshed_at_idx` - For stale entry queries
6. `l10n_cr_cedula_cache_company_id_idx` - For multi-company filtering

## Idempotency
The migration checks if the table already exists before creating it. If it exists, the migration is skipped.

## Cache Tiers
- **Fresh** (0-7 days): Auto-serve, no API call
- **Refresh** (5-7 days): Serve cache + background refresh
- **Stale** (7-90 days): Emergency fallback only
- **Expired** (>90 days): Auto-purge via daily cron

## Related Files
- Model: `l10n_cr_einvoice/models/cedula_cache.py`
- Migration: `l10n_cr_einvoice/migrations/19.0.10.0.0/pre-migrate.py`
- Architecture: `architecture-einvoice-validation-cedula-lookup.md`
