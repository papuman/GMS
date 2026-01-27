#!/bin/bash
# ============================================================================
# Run All Comprehensive Tests for Costa Rica E-Invoicing Module
# ============================================================================
# This script runs all test suites and generates comprehensive reports
# for production readiness validation.
#
# Usage: ./RUN_ALL_COMPREHENSIVE_TESTS.sh [test_suite]
#   test_suite: Optional. Run specific suite (performance, load, edge_cases,
#               security, integration, compatibility) or 'all' (default)
#
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ODOO_BIN="${ODOO_BIN:-odoo-bin}"
ODOO_CONF="${ODOO_CONF:-odoo.conf}"
TEST_DB="test_l10n_cr_einvoice_$(date +%Y%m%d_%H%M%S)"
MODULE_PATH="$(pwd)"
RESULTS_DIR="${MODULE_PATH}/test_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Test suite to run
TEST_SUITE="${1:-all}"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Costa Rica E-Invoicing Module - Comprehensive Test Suite${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo -e "Test Suite: ${GREEN}${TEST_SUITE}${NC}"
echo -e "Test Database: ${GREEN}${TEST_DB}${NC}"
echo -e "Timestamp: ${GREEN}${TIMESTAMP}${NC}"
echo -e "${BLUE}============================================================================${NC}\n"

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Function to run test suite
run_test_suite() {
    local suite_name=$1
    local test_tags=$2
    local output_file="${RESULTS_DIR}/${suite_name}_${TIMESTAMP}.txt"

    echo -e "${YELLOW}Running ${suite_name} tests...${NC}"

    # Run tests with specified tags
    if python3 -m pytest \
        --odoo-database="${TEST_DB}" \
        --odoo-config="${ODOO_CONF}" \
        -v \
        --tb=short \
        --junit-xml="${RESULTS_DIR}/${suite_name}_${TIMESTAMP}.xml" \
        -k "${test_tags}" \
        2>&1 | tee "${output_file}"; then
        echo -e "${GREEN}✓ ${suite_name} tests PASSED${NC}\n"
        return 0
    else
        echo -e "${RED}✗ ${suite_name} tests FAILED${NC}\n"
        return 1
    fi
}

# Function to run Odoo tests
run_odoo_tests() {
    local suite_name=$1
    local test_tags=$2
    local output_file="${RESULTS_DIR}/${suite_name}_${TIMESTAMP}.txt"

    echo -e "${YELLOW}Running ${suite_name} tests (Odoo framework)...${NC}"

    # Run Odoo tests
    if ${ODOO_BIN} \
        -c "${ODOO_CONF}" \
        -d "${TEST_DB}" \
        -i l10n_cr_einvoice \
        --test-enable \
        --test-tags="${test_tags}" \
        --stop-after-init \
        --log-level=test \
        2>&1 | tee "${output_file}"; then
        echo -e "${GREEN}✓ ${suite_name} tests PASSED${NC}\n"
        return 0
    else
        echo -e "${RED}✗ ${suite_name} tests FAILED${NC}\n"
        return 1
    fi
}

# Initialize counters
PASSED=0
FAILED=0
TOTAL=0

# Function to increment counters
record_result() {
    TOTAL=$((TOTAL + 1))
    if [ $1 -eq 0 ]; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
}

# Create test database
echo -e "${YELLOW}Creating test database...${NC}"
createdb "${TEST_DB}" 2>/dev/null || true
echo -e "${GREEN}✓ Test database created${NC}\n"

# Run test suites based on selection
if [ "$TEST_SUITE" = "all" ] || [ "$TEST_SUITE" = "performance" ]; then
    run_odoo_tests "performance" "performance"
    record_result $?
fi

if [ "$TEST_SUITE" = "all" ] || [ "$TEST_SUITE" = "load" ]; then
    run_odoo_tests "load" "load"
    record_result $?
fi

if [ "$TEST_SUITE" = "all" ] || [ "$TEST_SUITE" = "edge_cases" ]; then
    run_odoo_tests "edge_cases" "edge_cases"
    record_result $?
fi

if [ "$TEST_SUITE" = "all" ] || [ "$TEST_SUITE" = "security" ]; then
    run_odoo_tests "security" "security"
    record_result $?
fi

if [ "$TEST_SUITE" = "all" ] || [ "$TEST_SUITE" = "integration" ]; then
    run_odoo_tests "integration" "integration"
    record_result $?
fi

if [ "$TEST_SUITE" = "all" ] || [ "$TEST_SUITE" = "compatibility" ]; then
    run_odoo_tests "compatibility" "compatibility"
    record_result $?
fi

# Run all existing tests if running comprehensive suite
if [ "$TEST_SUITE" = "all" ]; then
    echo -e "${YELLOW}Running existing test suite...${NC}"
    run_odoo_tests "existing_tests" "post_install,-at_install"
    record_result $?
fi

# Clean up test database
echo -e "${YELLOW}Cleaning up test database...${NC}"
dropdb "${TEST_DB}" 2>/dev/null || true
echo -e "${GREEN}✓ Test database cleaned up${NC}\n"

# Generate summary report
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Test Execution Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo -e "Total Test Suites: ${TOTAL}"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo -e "Results Directory: ${RESULTS_DIR}"
echo -e "${BLUE}============================================================================${NC}\n"

# Generate detailed report
SUMMARY_FILE="${RESULTS_DIR}/SUMMARY_${TIMESTAMP}.txt"
cat > "${SUMMARY_FILE}" << EOF
================================================================================
Costa Rica E-Invoicing Module - Comprehensive Test Results
================================================================================
Date: $(date)
Test Suite: ${TEST_SUITE}
Database: ${TEST_DB}

Summary
--------
Total Test Suites: ${TOTAL}
Passed: ${PASSED}
Failed: ${FAILED}
Success Rate: $(echo "scale=2; ${PASSED}*100/${TOTAL}" | bc 2>/dev/null || echo "N/A")%

Test Suites Executed
---------------------
EOF

# List all result files
for file in "${RESULTS_DIR}"/*_${TIMESTAMP}.txt; do
    if [ -f "$file" ]; then
        echo "- $(basename "$file")" >> "${SUMMARY_FILE}"
    fi
done

cat >> "${SUMMARY_FILE}" << EOF

Results Location
-----------------
All test results are saved in: ${RESULTS_DIR}

Individual test outputs:
EOF

ls -lh "${RESULTS_DIR}"/*_${TIMESTAMP}.* >> "${SUMMARY_FILE}" 2>/dev/null || true

echo -e "${GREEN}Summary report saved to: ${SUMMARY_FILE}${NC}\n"

# Display summary
cat "${SUMMARY_FILE}"

# Generate HTML report if possible
if command -v pytest-html &> /dev/null; then
    echo -e "${YELLOW}Generating HTML report...${NC}"
    HTML_REPORT="${RESULTS_DIR}/report_${TIMESTAMP}.html"
    # HTML generation would go here
    echo -e "${GREEN}HTML report would be at: ${HTML_REPORT}${NC}\n"
fi

# Exit with appropriate code
if [ ${FAILED} -gt 0 ]; then
    echo -e "${RED}Some tests failed. Please review the results.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed successfully!${NC}"
    exit 0
fi
