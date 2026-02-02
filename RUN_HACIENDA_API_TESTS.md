# Quick Reference: Running Hacienda API Integration Tests

## 🚀 Run All Tests

### Using Odoo Test Framework (Recommended)
```bash
# Run all Hacienda API integration tests
docker compose run --rm odoo -d GMS \
  --test-tags=hacienda_api \
  --stop-after-init \
  --no-http

# Run with verbose output
docker compose run --rm odoo -d GMS \
  --test-tags=hacienda_api \
  --log-level=test \
  --stop-after-init \
  --no-http
```

### Using pytest (if configured)
```bash
# Run all tests in the file
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -v

# Run with coverage
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py \
  --cov=l10n_cr_einvoice.models.hacienda_api \
  --cov-report=html \
  --cov-report=term-missing
```

---

## 🎯 Run by Priority

### P0 Tests Only (Critical - Must Pass)
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -m p0 -v
```

**Expected:** 13 tests
**Time:** ~5 seconds

### P1 Tests Only (High Priority)
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -m p1 -v
```

**Expected:** 25 tests
**Time:** ~10 seconds

---

## 🔍 Run by Category

### OAuth2 Authentication Tests
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -k oauth2 -v
```

**Expected:** 7 tests
- Token acquisition
- Invalid credentials
- Timeout handling
- Endpoint selection

### Invoice Submission Tests
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -k submit_invoice -v
```

**Expected:** 7 tests
- Success (200, 202)
- Validation errors (400)
- Auth errors (401)
- Rate limiting (429)
- Server errors (500)
- Timeout handling

### Status Check Tests
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -k check_status -v
```

**Expected:** 5 tests
- Aceptado
- Procesando
- Rechazado
- Invalid clave
- Not found (404)

### Retry Mechanism Tests
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -k retry -v
```

**Expected:** 4 tests
- Exponential backoff
- Max retries
- No retry on 400
- No retry on 401

### Response Parsing Tests
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -k parse_response -v
```

**Expected:** 3 tests
- Base64 decoding
- Malformed JSON
- Empty body

### Helper Method Tests
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -k "get_id_type or is_" -v
```

**Expected:** 8 tests
- ID type detection (5 tests)
- Estado helpers (3 tests)

### Connection Tests
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -k test_connection -v
```

**Expected:** 4 tests
- Success
- Invalid credentials
- Missing config
- Timeout

---

## 📊 Coverage Analysis

### Generate HTML Coverage Report
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py \
  --cov=l10n_cr_einvoice.models.hacienda_api \
  --cov-report=html \
  --cov-report=term

# Open report
open htmlcov/index.html
```

### Terminal Coverage Report
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py \
  --cov=l10n_cr_einvoice.models.hacienda_api \
  --cov-report=term-missing
```

**Expected Coverage:** ≥80%

---

## 🐛 Debugging Failed Tests

### Run Single Test
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py::TestHaciendaAPIIntegration::test_oauth2_obtain_token_success -v
```

### Run with Print Statements (disable capture)
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py -v -s
```

### Run with PDB (debugger)
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py --pdb
```

### Run Last Failed Tests Only
```bash
pytest l10n_cr_einvoice/tests/test_hacienda_api_integration.py --lf -v
```

---

## 🔧 Test Configuration

### Markers Used
- `@pytest.mark.integration` - Integration test (mocked external services)
- `@pytest.mark.p0` - Critical priority (must pass)
- `@pytest.mark.p1` - High priority

### Odoo Tags
- `post_install` - Run after module installation
- `-at_install` - Don't run during installation
- `hacienda_api` - Hacienda API tests
- `integration` - Integration tests

---

## 📈 Expected Results

### All Tests Passing
```
========== 38 passed in 15.23s ==========
```

### By Priority
- **P0:** 13/13 passed ✅
- **P1:** 25/25 passed ✅

### Coverage
- **Target:** ≥80%
- **Expected:** ~85%
- **Critical Paths:** ~90%

---

## 🚨 Common Issues

### Issue: Import Errors
**Solution:** Ensure Odoo modules are in PYTHONPATH
```bash
export PYTHONPATH="/opt/odoo:/opt/odoo/addons:$PYTHONPATH"
```

### Issue: Database Connection Errors
**Solution:** Run tests inside Docker container
```bash
docker compose run --rm odoo -d GMS --test-tags=hacienda_api --stop-after-init --no-http
```

### Issue: Mock Not Working
**Solution:** Check patch path matches import path
```python
# Correct
@patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')

# Incorrect
@patch('requests.post')  # Won't work with Odoo imports
```

---

## 📋 Test Checklist

Before committing:
- [ ] All 38 tests pass
- [ ] Coverage ≥80%
- [ ] No warnings in test output
- [ ] All P0 tests pass (13/13)
- [ ] All mocks properly isolated (no external calls)

Before merging:
- [ ] CI/CD pipeline passes
- [ ] Code review complete
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

---

## 🔗 Related Files

- **Test File:** `l10n_cr_einvoice/tests/test_hacienda_api_integration.py`
- **Module Under Test:** `l10n_cr_einvoice/models/hacienda_api.py`
- **Fixtures:** `l10n_cr_einvoice/tests/conftest.py`
- **Test Design:** `_bmad-output/implementation-artifacts/test-design-system-einvoice.md`
- **Summary:** `TEST_HACIENDA_API_SUMMARY.md`

---

**Quick Start:** `docker compose run --rm odoo -d GMS --test-tags=hacienda_api --stop-after-init --no-http`
