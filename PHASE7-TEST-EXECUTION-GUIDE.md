# Phase 7: Test Execution Guide

**Date:** 2025-02-01
**Status:** Sprint 0 Complete, P0 Tests Implemented
**Module:** l10n_cr_einvoice

---

## 🎉 What We've Accomplished

### ✅ Sprint 0: Test Infrastructure (COMPLETE)

1. **Test Configuration Created** ✅
   - `conftest.py` with pytest markers and fixtures
   - Certificate fixtures (valid, expired, expiring-soon)
   - Hacienda API mock responses
   - Test data factories

2. **Test Categorization** ✅
   - `@pytest.mark.unit` - Fast, no dependencies
   - `@pytest.mark.integration` - Database, mocked APIs
   - `@pytest.mark.e2e` - Real sandbox API
   - `@pytest.mark.external` - External services
   - `@pytest.mark.p0/p1/p2/p3` - Priority levels

3. **E2E Test Suite Created** ✅
   - Complete invoice lifecycle test (FE)
   - Tiquete electrónico test (TE)
   - Nota de crédito test (NC)
   - Retry mechanism test
   - Idempotency test (no double submit)
   - Bulk submission performance test (10 invoices)

---

## 📋 Test Inventory

### Existing Tests (16 files)
- ✅ `test_certificate_manager.py` (542 lines, 20+ tests) - **EXCELLENT**
- ✅ `test_xsd_validator.py`
- ✅ `test_xml_parser.py`
- ✅ `test_payment_method.py`
- ✅ `test_account_move_payment.py`
- ✅ `test_xml_generator_payment.py`
- ✅ `test_phase3_retry_queue.py`
- ✅ `test_pos_offline.py`
- ✅ `test_gym_void_wizard_unit.py`
- ✅ `test_gym_void_wizard_integration.py`
- ✅ `test_gym_void_wizard_membership.py`
- ✅ `test_tax_report_xml_generation.py`
- ✅ `test_tax_report_api_integration.py`
- ✅ `test_d150_vat_workflow.py`
- ✅ `test_d101_income_tax_workflow.py`
- ✅ `test_d151_informative_workflow.py`

### New Tests Created Today
- ✅ `conftest.py` - Test infrastructure
- ✅ `test_e2e_sandbox_lifecycle.py` - Complete E2E tests

---

## 🚀 Running the Tests

### Quick Start

**Run all unit tests (fast):**
```bash
cd /Users/papuman/Documents/My\ Projects/GMS
docker compose exec odoo python3 -m pytest l10n_cr_einvoice/tests -m "unit" -v
```

**Run all integration tests:**
```bash
docker compose exec odoo python3 -m pytest l10n_cr_einvoice/tests -m "integration" -v
```

**Run E2E tests (requires sandbox access):**
```bash
docker compose exec odoo python3 -m pytest l10n_cr_einvoice/tests -m "e2e" -v
```

**Run P0 critical tests only:**
```bash
docker compose exec odoo python3 -m pytest l10n_cr_einvoice/tests -m "p0" -v
```

**Run all tests except E2E (for CI/CD):**
```bash
docker compose exec odoo python3 -m pytest l10n_cr_einvoice/tests -m "not external" -v
```

---

### Using Odoo Test Framework

**Run with Odoo's built-in test framework:**

```bash
# All tests
docker compose run --rm odoo -d GMS -i l10n_cr_einvoice --test-enable --stop-after-init --no-http

# Specific test file
docker compose run --rm odoo -d GMS --test-file=l10n_cr_einvoice/tests/test_e2e_sandbox_lifecycle.py --stop-after-init --no-http

# With coverage
docker compose run --rm odoo -d GMS -i l10n_cr_einvoice --test-enable --test-tags=l10n_cr_einvoice --stop-after-init --no-http
```

---

## 📊 Test Coverage Analysis

### Measure Current Coverage

```bash
# Install coverage tool (if not already installed)
docker compose exec odoo pip install coverage pytest-cov

# Run tests with coverage
docker compose exec odoo python3 -m pytest l10n_cr_einvoice/tests \
  --cov=l10n_cr_einvoice \
  --cov-report=html \
  --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

### Coverage Targets

| Module | Target | Priority |
|--------|--------|----------|
| `xml_generator.py` | 90% | P0 |
| `xml_signer.py` | 90% | P0 |
| `certificate_manager.py` | 90% | P0 (likely met ✅) |
| `xsd_validator.py` | 85% | P0 |
| `hacienda_api.py` | 80% | P1 |
| `einvoice_document.py` | 75% | P1 |
| **Overall** | **≥80%** | **Gate Criteria** |

---

## 🧪 E2E Sandbox Testing

### Prerequisites

1. **Sandbox Credentials** (configured in company settings)
   - Username: `cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr`
   - Password: `e8KLJRHzRA1P0W2ybJ5T`
   - Environment: `sandbox`

2. **Test Certificate** (docs/Tribu-CR/certificado.p12)
   - PIN: `5147`
   - Valid until: 2029-12-27

3. **Network Access**
   - Hacienda sandbox API: `https://idp.comprobanteselectronicos.go.cr`
   - OAuth2 IDP: `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag`

### E2E Test Scenarios

**Test 1: Complete FE Lifecycle** ✅
```python
# test_e2e_complete_lifecycle_factura_electronica
# Creates invoice → Generates XML → Signs → Submits → Polls → Verifies acceptance
```

**Test 2: Tiquete Electrónico** ✅
```python
# test_e2e_tiquete_electronico_submission
# POS-style simplified invoice
```

**Test 3: Nota de Crédito** ✅
```python
# test_e2e_nota_credito_submission
# Credit note/refund
```

**Test 4: Retry on Failure** ✅
```python
# test_e2e_retry_on_transient_failure
# Verifies retry queue mechanism
```

**Test 5: Idempotency** ✅
```python
# test_e2e_idempotency_no_double_submit
# No duplicate submissions
```

**Test 6: Bulk Performance** ✅
```python
# test_e2e_bulk_submission_performance
# 10 invoices, <15s per invoice target
```

---

## 🎯 Phase 7 Roadmap

### Week 1: Unit Tests (Current Week)
- [x] Sprint 0 setup (conftest.py) ✅
- [x] E2E test suite creation ✅
- [ ] Run coverage analysis
- [ ] Fill unit test gaps (xml_generator, xsd_validator)
- [ ] Achieve 80%+ coverage on critical modules

### Week 2: Integration Tests
- [ ] API mocking tests (Hacienda client with mocked responses)
- [ ] Retry queue behavior tests (401, 429, 500 responses)
- [ ] State transition tests (draft → accepted)
- [ ] Multi-company isolation tests
- [ ] Access control tests (RBAC)

### Week 3: E2E Tests & Performance
- [ ] Run all E2E tests against sandbox
- [ ] Verify all document types (FE, TE, NC, ND)
- [ ] Bulk operations (100+ invoices)
- [ ] Performance baseline (<2s signing, <10s submit)
- [ ] QR code + PDF generation validation

### Week 4: Certification & Production Prep
- [ ] Hacienda sandbox certification (all document types)
- [ ] Security audit (access control, credential handling)
- [ ] Documentation review (README, API docs)
- [ ] Acquire production certificate
- [ ] Deployment runbook
- [ ] Go-live checklist

---

## 🚨 Quality Gates

### Gate 1: Unit Tests (End of Week 1)
- [ ] ≥80% code coverage on critical modules
- [ ] All P0 unit tests pass (100%)
- [ ] No unhandled exceptions in logs
- [ ] XSD validation tests cover all document types

**Status:** IN PROGRESS

---

### Gate 2: Integration Tests (End of Week 2)
- [ ] All P0 integration tests pass (100%)
- [ ] Retry queue validated (3+ failure modes)
- [ ] State transitions complete (draft → accepted)
- [ ] Idempotency confirmed
- [ ] Multi-company isolation verified

**Status:** PENDING

---

### Gate 3: E2E Tests (End of Week 3)
- [ ] All P0 E2E tests pass (100%)
- [ ] Sandbox accepts all document types (FE, TE, NC, ND)
- [ ] Complete lifecycle works end-to-end
- [ ] QR code generation validated
- [ ] PDF generation works
- [ ] No high-priority risks unmitigated

**Status:** PENDING

---

### Gate 4: Certification (End of Week 4)
- [ ] Hacienda sandbox certification complete
- [ ] Security audit complete (no high/critical)
- [ ] Performance acceptable (<2s signing)
- [ ] Documentation complete
- [ ] Production certificate acquired
- [ ] Deployment tested

**Status:** PENDING

---

## 🐛 Known Issues & Gaps

### Gaps to Fill

1. **Unit Test Coverage** ⚠️
   - Need comprehensive `test_xml_generator.py` for all document types
   - Need edge cases for `test_xsd_validator.py`
   - Need `test_hacienda_api_oauth2.py` for OAuth2 flow

2. **Integration Tests** ⚠️
   - Mock Hacienda API responses (401, 429, 500)
   - Database persistence tests
   - Concurrent modification tests

3. **Security Tests** ⚠️
   - Access control validation
   - Certificate PIN protection
   - OAuth2 token expiry handling

4. **Performance Tests** ⚠️
   - Bulk operations (100+ invoices)
   - Memory profiling
   - Database query optimization

### Next Actions

**Immediate (This Week):**
1. Run coverage analysis: `pytest --cov=l10n_cr_einvoice --cov-report=html`
2. Review coverage report and identify gaps
3. Implement missing unit tests for uncovered modules
4. Run E2E tests against sandbox (verify connectivity)

**Week 2:**
5. Create API mocking infrastructure
6. Implement integration test suite
7. Validate retry queue behavior

**Week 3:**
8. Run full E2E test suite
9. Performance baseline measurement
10. QR code/PDF validation

**Week 4:**
11. Sandbox certification
12. Security audit
13. Production readiness review

---

## 📞 Support & Resources

**Documentation:**
- Test Design: `_bmad-output/implementation-artifacts/test-design-system-einvoice.md`
- Module Status: `EINVOICE-STATUS-2025-02-01.md`
- Epic: `_bmad-output/implementation-artifacts/epics/epic-001-einvoicing.md`

**Hacienda Resources:**
- Sandbox API: `https://api-sandbox.comprobanteselectronicos.go.cr`
- Documentation: `https://www.hacienda.go.cr/contenido/14185-factura-electronica`
- XSD Schemas: `https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/`

**Credentials (Sandbox):**
- Location: `docs/Tribu-CR/Credentials.md`
- Certificate: `docs/Tribu-CR/certificado.p12`
- PIN: `5147`

---

## ✅ Success Criteria

**Phase 7 Complete When:**
- [x] Sprint 0 complete (test infrastructure) ✅
- [x] E2E test suite created ✅
- [ ] 90+ tests implemented
- [ ] ≥80% code coverage
- [ ] All P0 tests pass (100%)
- [ ] All document types certified in sandbox (FE, TE, NC, ND)
- [ ] Security audit complete
- [ ] Performance baseline met
- [ ] Production certificate acquired
- [ ] Ready for Phase 8 (deployment)

**Current Progress:** ~15% complete (Sprint 0 + E2E tests created)

---

**Generated:** 2025-02-01
**Next Review:** End of Week 1 (after coverage analysis)
**Owner:** QA Team + Development
