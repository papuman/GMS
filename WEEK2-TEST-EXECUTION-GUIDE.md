# Week 2 Integration Tests - Quick Execution Guide

**Module:** l10n_cr_einvoice
**Test Phase:** Week 2 - Integration Tests
**Total Tests:** 35 (13 P0, 20 P1, 2 P2)
**Expected Runtime:** ~37 seconds

---

## Quick Start (Run All Week 2 Tests)

```bash
cd /Users/papuman/Documents/My\ Projects/GMS

# Run all integration tests
docker compose run --rm odoo -d GMS \
  --test-tags=integration \
  --stop-after-init --no-http
```

---

## Run by Priority

### P0 - Critical Tests Only (13 tests)
```bash
docker compose run --rm odoo -d GMS \
  --test-tags=integration,p0 \
  --stop-after-init --no-http
```

### P1 - High Priority Tests Only (20 tests)
```bash
docker compose run --rm odoo -d GMS \
  --test-tags=integration,p1 \
  --stop-after-init --no-http
```

### P2 - Medium Priority Tests Only (2 tests)
```bash
docker compose run --rm odoo -d GMS \
  --test-tags=integration,p2 \
  --stop-after-init --no-http
```

---

## Run by Test Category

### 1. State Transitions (13 tests)
```bash
docker compose run --rm odoo -d GMS \
  --test-enable \
  --test-file=l10n_cr_einvoice/tests/test_einvoice_state_transitions.py \
  --stop-after-init --no-http
```

**Tests:**
- Happy path: draft → generated → signed → submitted → accepted
- Rejection path: submitted → rejected
- Invalid transitions: skip state prevention
- State persistence: commit/rollback handling
- Error recovery: retry mechanism

### 2. Multi-Company Isolation (10 tests)
```bash
docker compose run --rm odoo -d GMS \
  --test-enable \
  --test-file=l10n_cr_einvoice/tests/test_multi_company_isolation.py \
  --stop-after-init --no-http
```

**Tests:**
- Data isolation: Company A cannot see Company B invoices
- Certificate isolation: Each company uses own cert
- Credential isolation: Separate Hacienda credentials
- Response isolation: Hacienda messages filtered by company

### 3. Access Control / RBAC (12 tests)
```bash
docker compose run --rm odoo -d GMS \
  --test-enable \
  --test-file=l10n_cr_einvoice/tests/test_access_control_rbac.py \
  --stop-after-init --no-http
```

**Tests:**
- Read-only users: Can view but not modify
- Manager users: Full permissions (generate, sign, submit)
- Company boundaries: Users only access own company
- Database security: ORM-level filtering

---

## Run Specific Test Class

### Example: Happy Path Only
```bash
docker compose run --rm odoo -d GMS \
  --test-enable \
  --test-file=l10n_cr_einvoice/tests/test_einvoice_state_transitions.py::TestEInvoiceStateTransitionsHappyPath \
  --stop-after-init --no-http
```

### Example: Multi-Company Data Isolation
```bash
docker compose run --rm odoo -d GMS \
  --test-enable \
  --test-file=l10n_cr_einvoice/tests/test_multi_company_isolation.py::TestMultiCompanyDataIsolation \
  --stop-after-init --no-http
```

---

## Run Single Test Method

### Example: Test Complete Happy Path Lifecycle
```bash
docker compose run --rm odoo -d GMS \
  --test-enable \
  --test-file=l10n_cr_einvoice/tests/test_einvoice_state_transitions.py::TestEInvoiceStateTransitionsHappyPath::test_06_complete_happy_path_lifecycle \
  --stop-after-init --no-http
```

---

## Troubleshooting

### Test Failures

#### 1. Database Connection Issues
```bash
# Ensure PostgreSQL is running
docker compose ps gms_postgres

# Restart if needed
docker compose restart gms_postgres
```

#### 2. Module Not Installed
```bash
# Install/update module first
docker compose run --rm odoo -d GMS \
  -u l10n_cr_einvoice \
  --stop-after-init --no-http
```

#### 3. Import Errors
```bash
# Check Python dependencies
docker compose run --rm odoo python3 -c "import pytest; print(pytest.__version__)"
```

#### 4. TransactionCase Errors
```bash
# Ensure test database is clean
docker compose down
docker compose up -d gms_postgres
docker compose run --rm odoo -d GMS -i l10n_cr_einvoice --stop-after-init --no-http
```

---

## Expected Output

### Successful Run
```
odoo.modules.loading: Modules loaded.
odoo.tests.common: running tests for module l10n_cr_einvoice
odoo.addons.l10n_cr_einvoice.tests.test_einvoice_state_transitions
  test_01_initial_state_is_draft ... ok
  test_02_draft_to_generated_transition ... ok
  test_03_generated_to_signed_transition ... ok
  test_04_signed_to_submitted_transition ... ok
  test_05_submitted_to_accepted_transition ... ok
  test_06_complete_happy_path_lifecycle ... ok
  test_07_submitted_to_rejected_transition ... ok
  test_08_cannot_sign_without_generate ... ok
  test_09_cannot_submit_without_sign ... ok
  test_10_cannot_regenerate_accepted_document ... ok
  test_11_generation_error_sets_error_state ... ok
  test_12_state_persists_after_commit ... ok
  test_13_error_state_allows_retry ... ok

----------------------------------------------------------------------
Ran 35 tests in 37.234s

OK
```

### Failed Test Example
```
FAIL: test_02_draft_to_generated_transition
AssertionError: 'draft' != 'generated'
```

**Fix:** Check XML generation mocking and state transition logic.

---

## Debug Mode

### Enable Verbose Output
```bash
docker compose run --rm odoo -d GMS \
  --test-tags=integration,p0 \
  --log-level=debug \
  --stop-after-init --no-http
```

### Enable SQL Logging
```bash
docker compose run --rm odoo -d GMS \
  --test-tags=integration \
  --log-level=debug_sql \
  --stop-after-init --no-http
```

---

## Test Coverage Report

### Generate Coverage (Future)
```bash
# Install coverage.py in container
docker compose run --rm odoo pip3 install coverage

# Run tests with coverage
docker compose run --rm odoo coverage run \
  --source=l10n_cr_einvoice \
  -m odoo -d GMS \
  --test-tags=integration \
  --stop-after-init --no-http

# Generate report
docker compose run --rm odoo coverage report
docker compose run --rm odoo coverage html
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Week 2 Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: |
          docker compose up -d gms_postgres
          docker compose run --rm odoo -d GMS \
            --test-tags=integration,p0 \
            --stop-after-init --no-http
```

---

## Test Files Reference

| File | Tests | Priority | Runtime |
|------|-------|----------|---------|
| `test_einvoice_state_transitions.py` | 13 | P0/P1 | ~15s |
| `test_multi_company_isolation.py` | 10 | P1/P2 | ~10s |
| `test_access_control_rbac.py` | 12 | P1/P2 | ~12s |

---

## Next Steps After Tests Pass

1. ✅ **Mark Week 2 Complete** in Epic 001
2. ✅ **Update Test Design Document** with results
3. ✅ **Prepare Week 3 E2E Tests** (Hacienda sandbox)
4. ✅ **Add Security Rules** (ir.rule for multi-company)

---

## Support

**Questions?** Check:
- Test design: `_bmad-output/implementation-artifacts/test-design-system-einvoice.md`
- Epic 001: `_bmad-output/implementation-artifacts/epics/epic-001-einvoicing.md`
- Summary: `WEEK2-INTEGRATION-TESTS-SUMMARY.md`

---

**Last Updated:** 2025-02-01
**Maintained by:** Papu (with Claude Code)
