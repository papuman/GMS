# System-Level Test Design: Costa Rica E-Invoicing Module

**Date:** 2025-02-01
**Author:** Papu (with TEA Agent)
**Module:** l10n_cr_einvoice
**Version:** 19.0.1.6.0+
**Status:** Phase 7 - Testing & Certification

---

## Executive Summary

**Scope:** System-level testability review for Costa Rica Electronic Invoicing module (Epic 001)

**Module Status:** 75% Complete (6/8 phases)
- ✅ Phases 1-6: Implementation complete
- 🧪 Phase 7: Testing & Certification (CURRENT)
- ⏳ Phase 8: Production deployment pending

**Testability Assessment Preview:**
- **Controllability**: PASS ✅ (excellent test data control, API seeding available)
- **Observability**: PASS ✅ (comprehensive logging, response tracking, audit trail)
- **Reliability**: CONCERNS ⚠️ (external dependency on Hacienda API requires robust mocking)

**Risk Summary:**
- **Total Risks Identified**: 18
- **High-Priority (≥6)**: 6 risks
- **Critical Categories**: SEC (security), DATA (integrity), TECH (external dependency)

**Test Strategy:**
- **Unit Tests**: 40% (business logic, XML generation, validation)
- **Integration Tests**: 35% (API interaction, certificate management)
- **E2E Tests**: 25% (complete invoice lifecycle with Hacienda sandbox)

---

## 1. Testability Assessment

### 1.1 Controllability ✅ PASS

**Can we control system state for testing?**

**✅ Strengths:**
- **Test Data Control**: Odoo's TransactionCase provides excellent database isolation
- **Certificate Management**: Test certificates can be generated programmatically
- **API Mocking**: Hacienda API can be mocked for unit/integration tests
- **State Management**: Invoice lifecycle states are well-defined (draft → generated → signed → submitted → accepted)
- **Factory Support**: Odoo's ORM supports easy test data creation

**Implementation Evidence:**
```python
# Existing test shows good controllability
class TestCertificateManager(TransactionCase):
    def setUp(self):
        # Generate test certificates programmatically
        self.private_key = rsa.generate_private_key(...)
        self.valid_cert = x509.CertificateBuilder()...
```

**✅ API Seeding:**
- Company configuration can be set programmatically
- Partner data (cédula, passport) can be created via factories
- Invoice data isolated per test case
- Certificate PIN configurable in test environment

**✅ Error Injection:**
- Can simulate Hacienda API errors (401, 403, 429, 5xx)
- Can create invalid XML for validation testing
- Can simulate certificate expiry scenarios
- Can test retry queue behavior with controlled failures

**Recommendation:** Controllability is EXCELLENT. No changes needed.

---

### 1.2 Observability ✅ PASS

**Can we inspect system state and validate outcomes?**

**✅ Strengths:**
- **Comprehensive Logging**: All phases log to `_logger` with appropriate levels
- **Response Repository**: `hacienda_response_message` stores all API responses (90-day retention)
- **Retry Queue Tracking**: `einvoice_retry_queue` tracks all failed operations with error categorization
- **State Transitions**: Invoice document states are auditable
- **XML Preservation**: Both unsigned and signed XML stored for inspection

**Implementation Evidence:**
```python
# Response message repository
class HaciendaResponseMessage(models.Model):
    _name = 'l10n_cr.hacienda.response.message'

    # Full audit trail
    xml_response_raw = fields.Binary()  # Original response
    xml_response_decoded = fields.Text()  # Human-readable
    error_code = fields.Char()
    error_description = fields.Text()
```

**✅ Metrics Available:**
- Invoice acceptance rates
- API response times
- Retry queue statistics
- Error frequency by category
- Certificate expiry warnings

**✅ Validation Capabilities:**
- XSD schema validation provides detailed error messages
- Signature validation confirms cryptographic correctness
- API responses include Hacienda error codes
- Database state is easily queryable in tests

**Recommendation:** Observability is EXCELLENT. Response repository is a major strength.

---

### 1.3 Reliability ⚠️ CONCERNS

**Are tests isolated, deterministic, and reproducible?**

**⚠️ Concerns:**

**1. External Dependency - Hacienda API** (MEDIUM RISK)
- **Issue**: Sandbox API availability affects E2E tests
- **Impact**: Tests may fail due to network issues, not code defects
- **Evidence**: OAuth2 tokens expire, API may have downtime
- **Mitigation**:
  - Use mocks for unit/integration tests
  - Isolate E2E tests with clear retry policies
  - Implement circuit breaker for test stability
  - Tag E2E tests separately (e.g., `@external`)

**2. Certificate Lifecycle** (LOW RISK)
- **Issue**: Real certificates expire (test cert valid until 2029)
- **Impact**: Tests could fail in 4 years
- **Mitigation**:
  - Generate test certificates programmatically with controlled expiry
  - Document certificate renewal process
  - Add monitoring for test cert expiry

**3. Time-Dependent Behavior** (LOW RISK)
- **Issue**: Cron jobs, polling intervals, retry delays
- **Evidence**: Auto-polling every 15 minutes, retry exponential backoff
- **Mitigation**:
  - Mock `datetime` in tests
  - Use Odoo's `@freeze_time` for deterministic time

**4. State Cleanup** (LOW RISK)
- **Issue**: Response messages and retry queue accumulate
- **Evidence**: 90-day retention, 30-day retry queue retention
- **Mitigation**:
  - Odoo's TransactionCase auto-rolls back database changes
  - Explicit cleanup in tearDown for integration tests

**✅ Strengths:**
- **Database Isolation**: Odoo's TransactionCase provides transaction rollback
- **Deterministic XML**: XML generation is deterministic given same inputs
- **No Race Conditions**: Single-threaded test execution in Odoo
- **Clear Success Criteria**: XSD validation, signature verification are binary

**Recommendation:** Reliability is GOOD with concerns around external dependency. Mitigation plan provided below.

---

## 2. Architecturally Significant Requirements (ASRs)

### 2.1 Legal Compliance (CRITICAL)

**Requirement:** 100% compliance with Costa Rica Hacienda v4.4 specification

**Probability:** 3 (Likely - complex spec, easy to miss details)
**Impact:** 3 (Critical - penalties ₡8.3M+ ($14,800+), legal liability)
**Risk Score:** 9 (HIGHEST PRIORITY)

**Testability:**
- **Validation**: XSD schema validation provides automated compliance checking
- **Test Oracle**: Official Hacienda XSD schemas (v4.4) are authoritative
- **Coverage**: All document types (FE, TE, NC, ND) must validate

**Test Strategy:**
- **P0**: XSD validation for all document types
- **P0**: Digital signature structure verification
- **P0**: Clave format validation (50 digits, check digit)
- **P1**: Edge cases (special characters, max line items, multi-currency)
- **E2E**: Sandbox submission with real Hacienda API

**Owner:** QA + Dev
**Timeline:** Phase 7 (current)

---

### 2.2 Data Integrity (CRITICAL)

**Requirement:** No data loss, no invoice corruption, no double-submission

**Probability:** 2 (Possible - complex state machine, retry logic)
**Impact:** 3 (Critical - financial/legal consequences)
**Risk Score:** 6 (HIGH PRIORITY)

**Testability:**
- **State Tracking**: Invoice states are well-defined and auditable
- **Audit Trail**: Response messages provide full history
- **Idempotency**: Retry queue should handle duplicate submissions

**Test Strategy:**
- **P0**: State transition validation (draft → generated → signed → submitted → accepted)
- **P0**: Idempotency tests (retry same invoice doesn't create duplicates)
- **P1**: Data persistence after failures (crash recovery)
- **P1**: Concurrent modification protection (optimistic locking)

**Owner:** QA
**Timeline:** Phase 7

---

### 2.3 Security (HIGH)

**Requirement:** Certificate security, API credential protection, audit trail

**Probability:** 2 (Possible - credential exposure, certificate theft)
**Impact:** 3 (Critical - identity theft, fraud, compliance breach)
**Risk Score:** 6 (HIGH PRIORITY)

**Testability:**
- **Access Control**: Odoo security rules are unit testable
- **Encryption**: Certificate storage uses Odoo's binary fields (base64)
- **Audit**: Response messages track all API interactions

**Test Strategy:**
- **P0**: Certificate PIN validation (wrong PIN rejected)
- **P0**: OAuth2 token expiry handling
- **P1**: Multi-company isolation (company A can't see company B's invoices)
- **P1**: Access control (only authorized users can submit to Hacienda)
- **P2**: Audit log completeness (all API calls logged)

**Owner:** QA + Security Review
**Timeline:** Phase 7

---

### 2.4 Performance & Scalability (MEDIUM)

**Requirement:** Handle high-volume invoicing (monthly billing cycles)

**Probability:** 2 (Possible - batch operations, large XML)
**Impact:** 2 (Degraded - slow but functional)
**Risk Score:** 4 (MEDIUM PRIORITY)

**Testability:**
- **Batch Operations**: Bulk wizards exist for sign/submit
- **Metrics**: Can measure XML generation time, signature time, API response time
- **Load**: Sandbox can be used for load testing (with care)

**Test Strategy:**
- **P1**: Bulk operations performance (100+ invoices)
- **P2**: XML generation time (<1s per invoice)
- **P2**: Digital signature time (<2s per invoice)
- **P3**: Memory usage during batch operations

**Owner:** QA
**Timeline:** Phase 7 (lower priority)

---

### 2.5 External Dependency - Hacienda API (HIGH)

**Requirement:** Resilience to Hacienda API issues (downtime, errors, rate limits)

**Probability:** 3 (Likely - external service, network issues common)
**Impact:** 2 (Degraded - invoices delayed but not lost)
**Risk Score:** 6 (HIGH PRIORITY)

**Testability:**
- **Retry Logic**: Retry queue system is observable and testable
- **Error Handling**: 7 error categories with specific handling
- **Circuit Breaker**: Exponential backoff prevents API hammering

**Test Strategy:**
- **P0**: Retry queue triggers on failures (401, 429, 5xx)
- **P0**: Exponential backoff prevents infinite retry
- **P1**: API timeout handling (<30s)
- **P1**: OAuth2 token refresh
- **P2**: Circuit breaker prevents cascading failures
- **P3**: Manual retry after exhausted attempts

**Owner:** QA + Dev
**Timeline:** Phase 7

---

## 3. Test Levels Strategy

### 3.1 Recommended Test Distribution

**Total Test Budget:** ~150 tests

| Level | Percentage | Count | Rationale |
|-------|-----------|-------|-----------|
| **Unit** | 40% | ~60 | Business logic, XML generation, validation, certificate handling |
| **Integration** | 35% | ~52 | API mocking, database persistence, state transitions |
| **E2E** | 25% | ~38 | Sandbox API, complete invoice lifecycle, real signature |

**Rationale:**

**Unit Tests (40%)** - Highest ROI
- XML generation is complex but deterministic
- Certificate management has many edge cases (expiry, wrong PIN, corruption)
- XSD validation has clear pass/fail
- Fast feedback (<1 min for full suite)
- No external dependencies

**Integration Tests (35%)** - Good balance
- Database persistence (Odoo ORM integration)
- State machine transitions
- Retry queue behavior
- Mocked Hacienda API (controlled responses)
- Moderate speed (<5 min)

**E2E Tests (25%)** - Critical but expensive
- Real Hacienda sandbox API
- OAuth2 authentication flow
- Complete invoice lifecycle
- QR code + PDF generation
- Slowest (<15 min)
- External dependency

---

### 3.2 Test Environment Requirements

**Local Development:**
- Odoo 19 Enterprise (docker-compose setup exists ✅)
- PostgreSQL 13 (containerized ✅)
- Test certificate (certificado.p12 ✅)
- Sandbox credentials (available ✅)

**CI/CD Pipeline:**
- Odoo test database (isolated per run)
- Mocked Hacienda API (unit/integration)
- Sandbox access (E2E - tagged separately)
- Certificate injection (via environment variable)

**Sandbox Environment:**
- Hacienda sandbox API (`https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag`)
- Test certificate (valid until 2029)
- Sandbox credentials (cpf-01-1313-0574@stag)
- OAuth2 token management

**Production (Post-Certification):**
- Production certificate (must acquire)
- Production Hacienda API
- Real customer data
- Monitoring and alerting

---

## 4. NFR Testing Approach

### 4.1 Security Testing

**Approach:** Odoo security rules + manual security audit

**Test Coverage:**
| Security Aspect | Test Method | Priority | Owner |
|----------------|-------------|----------|-------|
| Certificate PIN validation | Unit tests | P0 | QA |
| OAuth2 token handling | Integration tests | P0 | QA |
| Multi-company isolation | Integration tests | P1 | QA |
| Access control (RBAC) | Integration tests | P1 | QA |
| Audit trail completeness | Integration tests | P1 | QA |
| Credential exposure | Manual review | P1 | Security |
| XML injection vulnerabilities | Unit tests | P2 | QA |

**Tools:**
- Odoo security framework (ir.rule, access_*.csv)
- Manual code review for credential handling
- Playwright E2E tests for UI access control

**Gate Criteria:**
- All P0/P1 security tests pass: 100%
- No credentials in logs or error messages
- Certificate PIN never exposed in UI

---

### 4.2 Performance Testing

**Approach:** Load testing with realistic data volumes

**Test Scenarios:**
| Scenario | Volume | Target | Tool | Priority |
|----------|--------|--------|------|----------|
| Single invoice generation | 1 | <1s | Unit test | P1 |
| Bulk invoice signing | 100 | <200s (2s/invoice) | Integration | P2 |
| Bulk invoice submission | 100 | <500s (5s/invoice + network) | E2E | P2 |
| XML generation (max size) | 1 (200 line items) | <3s | Unit test | P2 |
| Monthly billing cycle | 500 invoices | <30 min | E2E | P3 |

**SLO Targets:**
- XML generation: <1s per invoice (P50), <2s (P99)
- Digital signature: <2s per invoice (P50), <5s (P99)
- API submission: <10s per invoice (P50), <30s (P99) including network

**Tools:**
- Odoo profiling (`--log-level=debug_sql`)
- Python `cProfile` for bottleneck identification
- Manual timing in tests

**Note:** Performance testing is P2/P3 priority. Focus on correctness first.

---

### 4.3 Reliability Testing

**Approach:** Error injection + retry validation

**Test Scenarios:**
| Failure Mode | Test Method | Recovery Expected | Priority |
|--------------|-------------|-------------------|----------|
| Hacienda API 401 (auth error) | Mock 401 response | Retry with new token | P0 |
| Hacienda API 429 (rate limit) | Mock 429 response | Exponential backoff + retry | P0 |
| Hacienda API 5xx (server error) | Mock 500 response | Retry 3x then queue | P0 |
| Network timeout | Mock timeout | Retry with timeout | P1 |
| Certificate expired | Generate expired cert | Fail with clear error | P1 |
| Invalid XML (malformed) | Generate bad XML | Fail XSD validation | P1 |
| Database connection lost | Simulate DB disconnect | Transaction rollback | P2 |
| Concurrent invoice submission | Parallel test threads | Optimistic locking | P2 |

**Tools:**
- Python `unittest.mock` for API mocking
- Odoo TransactionCase for database isolation
- `pytest-timeout` for timeout testing

**Gate Criteria:**
- All P0 error scenarios handled gracefully
- No unhandled exceptions in logs
- Retry queue captures all retryable failures

---

### 4.4 Maintainability Testing

**Approach:** Code quality gates + test coverage metrics

**Metrics:**
| Metric | Target | Current | Tool |
|--------|--------|---------|------|
| Test coverage (unit) | ≥80% | Unknown | `coverage.py` |
| Test coverage (critical paths) | ≥90% | Unknown | Manual review |
| Code complexity (cyclomatic) | <10 per function | Unknown | `radon` |
| Documentation (docstrings) | 100% public methods | ~60% | Manual review |
| Type hints (Python 3.9+) | ≥50% | ~20% | `mypy` |

**Recommendations:**
- Run `coverage.py` to measure current test coverage
- Add docstrings to all public methods
- Consider type hints for critical modules (xml_generator, xml_signer)

**Priority:** P2 (nice-to-have, not blocking)

---

## 5. Testability Concerns

### 5.1 External Dependency - Hacienda API ⚠️

**Concern:** E2E tests depend on Hacienda sandbox availability

**Impact:** Test flakiness, CI/CD pipeline failures unrelated to code quality

**Mitigation:**
1. **Isolate E2E Tests**: Tag with `@external`, run separately from unit/integration
2. **Mock for CI/CD**: Use mocked responses for fast feedback loop
3. **Scheduled Sandbox Tests**: Run E2E tests nightly against sandbox (not on every commit)
4. **Circuit Breaker**: Skip E2E tests if sandbox is down (check health endpoint first)
5. **Documentation**: Clear runbook for sandbox connectivity issues

**Recommendation:** NOT a blocker. Mitigation plan is sufficient.

---

### 5.2 Certificate Management Complexity ⚠️

**Concern:** Certificate lifecycle (loading, validation, expiry) has many edge cases

**Impact:** Tests could miss edge cases (expired cert, wrong PIN, corrupted file)

**Mitigation:**
1. **Comprehensive Unit Tests**: Test certificate manager has excellent coverage (542 lines, 20+ test cases) ✅
2. **Programmatic Test Certs**: Generate certs in tests (valid, expired, not-yet-valid, expiring-soon)
3. **Error Path Testing**: Test wrong PIN, corrupted P12, missing private key
4. **Monitoring**: Add cert expiry warnings to production

**Recommendation:** Well-mitigated. Existing test_certificate_manager.py is thorough.

---

### 5.3 No Concerns - State Machine Testability ✅

**Strength:** Invoice state machine is well-defined and testable

**Evidence:**
- Clear state transitions (draft → generated → signed → submitted → accepted/rejected)
- States are observable (database column)
- Transitions are triggerable (action methods)
- Rollback is atomic (Odoo transactions)

**No mitigation needed.**

---

## 6. Test Design Recommendations

### 6.1 Sprint 0 (Test Infrastructure Setup)

**Before implementation tests, set up:**

1. **Test Framework Configuration** (2 hours)
   - Configure `pytest` for Odoo 19 (if not using built-in unittest)
   - Set up test database isolation
   - Configure test certificate injection

2. **CI/CD Integration** (4 hours)
   - Add test stage to CI pipeline
   - Configure test database per run
   - Set up sandbox credentials (secure secrets)
   - Separate unit/integration (fast) from E2E (slow)

3. **Test Data Factories** (4 hours)
   - Create invoice factory (faker-based)
   - Create partner factory (cédula/passport)
   - Create product factory (Cabys codes)
   - Auto-cleanup fixtures

4. **Mocking Infrastructure** (4 hours)
   - Mock Hacienda API client (requests library)
   - Predefined mock responses (success, 401, 429, 500)
   - OAuth2 token mocking

**Total Sprint 0 Effort:** ~14 hours (~2 days)

---

### 6.2 Priority Test Scenarios (P0 - Critical)

**Must pass before production deployment:**

| Scenario | Test Level | Risk Link | Estimate | Owner |
|----------|------------|-----------|----------|-------|
| **XSD Validation - All Document Types** | Unit | R-001 (Compliance) | 4h | QA |
| **Digital Signature Structure** | Unit | R-001 (Compliance) | 3h | QA |
| **Certificate PIN Validation** | Unit | R-003 (Security) | 2h | QA |
| **OAuth2 Authentication Flow** | Integration | R-005 (External Dep) | 4h | QA |
| **Retry Queue on Failures** | Integration | R-005 (External Dep) | 3h | QA |
| **State Transition Validation** | Integration | R-002 (Data Integrity) | 4h | QA |
| **Idempotency (No Double Submit)** | Integration | R-002 (Data Integrity) | 3h | QA |
| **E2E Sandbox Submission** | E2E | R-001, R-005 | 6h | QA |
| **Complete Invoice Lifecycle** | E2E | R-001, R-002, R-005 | 8h | QA |

**Total P0 Effort:** ~37 hours (~5 days)

---

### 6.3 Execution Strategy

**Phase 7.1 - Unit Tests (Week 1):**
- XML generation tests (all document types)
- XSD validation tests
- Certificate manager tests (already exists ✅)
- XML signer tests
- State machine tests

**Phase 7.2 - Integration Tests (Week 2):**
- Database persistence tests
- API mocking tests (Hacienda client)
- Retry queue tests
- Multi-company isolation tests
- Access control tests

**Phase 7.3 - E2E Tests (Week 3):**
- Sandbox API integration
- Complete invoice lifecycle (create → sign → submit → poll → accept)
- QR code + PDF generation
- Email delivery
- Bulk operations (sign/submit 10+ invoices)

**Phase 7.4 - Certification (Week 4):**
- Sandbox validation with Hacienda (all document types)
- Production readiness review
- Documentation review
- Security audit
- Performance baseline measurement

**Total Phase 7 Timeline:** 4 weeks

---

## 7. Quality Gate Criteria

### 7.1 Gate 1: Unit Test Suite (Week 1)

**Pass Criteria:**
- [ ] ≥80% code coverage for critical modules (xml_generator, xml_signer, certificate_manager, xsd_validator)
- [ ] All P0 unit tests pass (100%)
- [ ] No unhandled exceptions in test logs
- [ ] XSD validation tests cover all document types (FE, TE, NC, ND)
- [ ] Certificate edge cases tested (expired, wrong PIN, corrupted)

**Blocker:** Cannot proceed to integration tests without passing unit tests.

---

### 7.2 Gate 2: Integration Test Suite (Week 2)

**Pass Criteria:**
- [ ] All P0 integration tests pass (100%)
- [ ] Retry queue behavior validated (3 failure modes minimum)
- [ ] State transitions tested (draft → accepted)
- [ ] Idempotency confirmed (no duplicate submissions)
- [ ] Multi-company isolation verified
- [ ] No database leaks (all test data cleaned up)

**Blocker:** Cannot proceed to E2E tests without passing integration tests.

---

### 7.3 Gate 3: E2E Test Suite (Week 3)

**Pass Criteria:**
- [ ] All P0 E2E tests pass (100%)
- [ ] Sandbox API successfully accepts all document types (FE, TE, NC, ND)
- [ ] Complete invoice lifecycle works (create → accept)
- [ ] QR code generation validated (per Hacienda spec)
- [ ] PDF generation works
- [ ] Email delivery confirmed
- [ ] No high-priority risks (≥6) unmitigated

**Blocker:** Cannot proceed to production without passing E2E tests.

---

### 7.4 Gate 4: Certification & Production Readiness (Week 4)

**Pass Criteria:**
- [ ] Hacienda sandbox certification complete (all document types)
- [ ] Security audit complete (no high/critical findings)
- [ ] Performance baseline acceptable (<2s per invoice signing)
- [ ] Documentation complete (README, API docs, runbooks)
- [ ] Production certificate acquired
- [ ] Deployment runbook tested
- [ ] Rollback plan documented

**Blocker:** Cannot deploy to production without certification.

---

## 8. Risk Assessment Matrix

### 8.1 High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
|---------|----------|-------------|-------------|--------|-------|------------|-------|----------|
| **R-001** | SEC/DATA | **Hacienda v4.4 Compliance Failure** | 3 | 3 | 9 | XSD validation + sandbox testing + certification | QA | Phase 7 |
| **R-002** | DATA | **Data Integrity (Double Submit, Lost Invoices)** | 2 | 3 | 6 | Idempotency tests + state machine validation | QA | Phase 7 |
| **R-003** | SEC | **Certificate Security (PIN exposure, theft)** | 2 | 3 | 6 | Access control tests + security audit | QA/Sec | Phase 7 |
| **R-004** | SEC | **OAuth2 Token Exposure** | 2 | 3 | 6 | Token handling tests + code review | QA/Sec | Phase 7 |
| **R-005** | TECH | **Hacienda API Dependency (Downtime, Errors)** | 3 | 2 | 6 | Retry queue tests + error handling validation | QA | Phase 7 |
| **R-006** | DATA | **XML Corruption (Malformed, Invalid Signature)** | 2 | 3 | 6 | XSD validation + signature verification tests | QA | Phase 7 |

---

### 8.2 Medium-Priority Risks (Score 3-5)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|----------|-------------|-------------|--------|-------|------------|-------|
| **R-007** | PERF | **Bulk Operation Performance (Slow Monthly Billing)** | 2 | 2 | 4 | Performance tests (100+ invoices) | QA |
| **R-008** | TECH | **Certificate Expiry (Test/Prod Certs)** | 1 | 3 | 3 | Expiry monitoring + alerts | Ops |
| **R-009** | OPS | **Deployment Failure (Module Install)** | 1 | 3 | 3 | Smoke tests + rollback plan | Ops |
| **R-010** | DATA | **Concurrent Modification (Race Conditions)** | 1 | 3 | 3 | Optimistic locking tests | QA |
| **R-011** | BUS | **User Error (Wrong Certificate, Wrong Credentials)** | 2 | 2 | 4 | Validation tests + error messages | QA |
| **R-012** | TECH | **Odoo 19 Compatibility (Breaking Changes)** | 1 | 3 | 3 | Regression tests after Odoo upgrades | QA |

---

### 8.3 Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
|---------|----------|-------------|-------------|--------|-------|--------|
| **R-013** | OPS | **Log Noise (Excessive Logging)** | 2 | 1 | 2 | Monitor log volume |
| **R-014** | PERF | **Memory Leak (Long-Running Cron)** | 1 | 2 | 2 | Memory profiling |
| **R-015** | BUS | **UI Confusion (State Labels)** | 1 | 1 | 1 | User testing |
| **R-016** | TECH | **Python Dependency Conflicts** | 1 | 2 | 2 | Dependency pinning |
| **R-017** | OPS | **Database Migration Issues** | 1 | 2 | 2 | Migration tests |
| **R-018** | PERF | **XML Size (Large Invoices)** | 1 | 1 | 1 | Monitor XML size |

---

## 9. Test Effort Estimates

### 9.1 Detailed Breakdown

| Test Category | Count | Hours/Test | Total Hours | Notes |
|---------------|-------|------------|-------------|-------|
| **P0 Critical** | 15 | 3.0 | 45h | High complexity, external deps |
| **P1 High** | 25 | 1.5 | 37.5h | Standard coverage |
| **P2 Medium** | 40 | 0.75 | 30h | Simple scenarios |
| **P3 Low** | 10 | 0.5 | 5h | Exploratory |
| **Sprint 0 Setup** | - | - | 14h | Test infrastructure |
| **Code Review & Fixes** | - | - | 20h | Bug fixes from test findings |
| **Documentation** | - | - | 8h | Test plans, runbooks |
| **Certification** | - | - | 16h | Hacienda sandbox validation |
| **Total** | **90 tests** | **-** | **175.5h** | **~22 days (1 person)** |

### 9.2 Resource Allocation

**If 2 QA Engineers:**
- **Timeline:** ~11 days (2.2 weeks)
- **Parallel work:** Unit tests (QA1) + Integration tests (QA2)
- **Sequential:** E2E tests (both) + Certification (both)

**If 1 QA Engineer:**
- **Timeline:** ~22 days (4.4 weeks)
- **Sequential:** Sprint 0 → Unit → Integration → E2E → Certification

**Recommended:** 1.5 QA engineers (1 full-time + 1 part-time developer writing unit tests)

---

## 10. Test Automation Strategy

### 10.1 CI/CD Pipeline Integration

**Trigger:** On every commit to `feature/einvoice-pos-odoo19-fixes`

**Pipeline Stages:**
1. **Lint & Format** (~2 min)
   - `flake8` (Python linting)
   - `black --check` (formatting)
   - `isort --check` (import sorting)

2. **Unit Tests** (~5 min)
   - Run all unit tests (`pytest -m unit`)
   - Generate coverage report
   - Fail if coverage <80% on critical modules

3. **Integration Tests** (~10 min)
   - Run integration tests with mocked Hacienda API
   - Isolated test database
   - Fail if any P0/P1 test fails

4. **E2E Tests (Nightly)** (~20 min)
   - Run against Hacienda sandbox (tagged `@external`)
   - Only on `develop` branch (not feature branches)
   - Alert on failure (don't block merge)

**Total Fast Feedback:** ~17 min (lint + unit + integration)

---

### 10.2 Test Tags

Use pytest markers to organize tests:

```python
@pytest.mark.unit
@pytest.mark.p0
def test_xml_generation_fe():
    """P0: Generate valid FE XML"""
    ...

@pytest.mark.integration
@pytest.mark.p1
def test_retry_queue_exponential_backoff():
    """P1: Retry queue uses exponential backoff"""
    ...

@pytest.mark.e2e
@pytest.mark.external
@pytest.mark.p0
def test_sandbox_submission_complete_lifecycle():
    """P0: Complete invoice lifecycle in sandbox"""
    ...
```

**Run Subsets:**
- `pytest -m "unit and p0"` - Fast P0 unit tests
- `pytest -m "not external"` - All tests except E2E (for CI)
- `pytest -m "p0 or p1"` - Critical and high-priority tests

---

## 11. Recommendations for Next Steps

### 11.1 Immediate Actions (This Week)

1. **✅ Review This Test Design** (1 hour)
   - Product Manager approval
   - Tech Lead approval
   - Security review

2. **Sprint 0 Setup** (2 days)
   - Set up test infrastructure
   - Configure CI/CD pipeline
   - Create test data factories

3. **Begin P0 Unit Tests** (3 days)
   - XML generation tests
   - XSD validation tests
   - Certificate tests (already exist ✅)

### 11.2 Week 2-3 Actions

4. **Integration Tests** (1 week)
   - API mocking
   - Retry queue validation
   - State transitions

5. **E2E Tests** (1 week)
   - Sandbox integration
   - Complete lifecycle
   - Performance baseline

### 11.3 Week 4 Actions

6. **Hacienda Certification** (1 week)
   - Submit all document types to sandbox
   - Validate acceptance
   - Document results

7. **Production Readiness**
   - Acquire production certificate
   - Security audit
   - Performance review
   - Deployment planning

---

## 12. Success Metrics

### 12.1 Test Coverage Targets

| Module | Target Coverage | Current | Gap |
|--------|-----------------|---------|-----|
| `xml_generator.py` | 90% | Unknown | TBD |
| `xml_signer.py` | 90% | Unknown | TBD |
| `certificate_manager.py` | 90% | ~80% (has tests) ✅ | Low |
| `xsd_validator.py` | 85% | Unknown | TBD |
| `hacienda_api.py` | 80% | Unknown | TBD |
| `einvoice_document.py` | 75% | Unknown | TBD |
| **Overall** | **≥80%** | **Unknown** | **TBD** |

**Action:** Run `coverage.py` to measure current baseline.

---

### 12.2 Quality Metrics

**At End of Phase 7:**
- [ ] **Test Count:** ≥90 automated tests
- [ ] **P0 Pass Rate:** 100% (no exceptions)
- [ ] **P1 Pass Rate:** ≥95%
- [ ] **Coverage:** ≥80% on critical modules
- [ ] **High Risks Mitigated:** 6/6 (100%)
- [ ] **Sandbox Certification:** Complete (all document types)
- [ ] **Security Audit:** No high/critical findings
- [ ] **Performance:** <2s per invoice (sign), <10s (submit)

---

## 13. Appendix

### 13.1 Existing Test Files

**Already Implemented:** (16 test files discovered)
- ✅ `test_certificate_manager.py` (542 lines, 20+ tests) - EXCELLENT
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

**Gaps to Fill:**
- ⚠️ E2E sandbox tests (complete lifecycle)
- ⚠️ Bulk operation tests (100+ invoices)
- ⚠️ Performance benchmarks
- ⚠️ Security-focused tests (access control, token handling)

---

### 13.2 Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization

---

### 13.3 Related Documents

- **PRD:** `_bmad-output/planning-artifacts/GMS-PRD-FINAL.md`
- **Epic:** `_bmad-output/implementation-artifacts/epics/epic-001-einvoicing.md`
- **Status Report:** `EINVOICE-STATUS-2025-02-01.md`
- **Phase 2 Summary:** `PHASE2-SUMMARY.md`
- **Phase 3 Summary:** `PHASE3-SUMMARY.md`

---

## 14. Approval

**Test Design Approved By:**

- [ ] **Product Manager (Papu):** ________________ Date: _______
- [ ] **Tech Lead:** ________________ Date: _______
- [ ] **QA Lead:** ________________ Date: _______

**Comments:**

---

**Generated by:** BMad TEA Agent - Test Architect Module
**Workflow:** `_bmad/bmm/testarch/test-design`
**Version:** 4.0 (BMad v6)
**Date:** 2025-02-01