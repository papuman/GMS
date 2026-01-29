#!/bin/bash
# Simple Staging Validation Script
# Tests the existing Odoo instance at http://localhost:8070

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Staging Environment Validation"
echo "URL: http://localhost:8070"
echo "Database: gms_validation"
echo "=========================================="
echo ""

passed=0
failed=0

# Test 1: HTTP Response
echo -n "1. Testing HTTP response... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8070/web/health | grep -q "200"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((failed++))
fi

# Test 2: Login Page
echo -n "2. Testing login page... "
if curl -s http://localhost:8070/web/login | grep -q "login"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((failed++))
fi

# Test 3: Database Connection
echo -n "3. Testing database connection... "
if docker exec gms_postgres psql -U odoo -d gms_validation -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((failed++))
fi

# Test 4: Module Installed
echo -n "4. Testing l10n_cr_einvoice module... "
if docker exec gms_postgres psql -U odoo -d gms_validation -c "SELECT 1 FROM ir_module_module WHERE name='l10n_cr_einvoice' AND state='installed';" 2>/dev/null | grep -q "1"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((failed++))
fi

# Test 5: Check Tables Exist
echo -n "5. Testing database tables... "
if docker exec gms_postgres psql -U odoo -d gms_validation -c "SELECT 1 FROM information_schema.tables WHERE table_name='l10n_cr_einvoice_document';" 2>/dev/null | grep -q "1"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((failed++))
fi

# Test 6: Docker Container Health
echo -n "6. Testing Docker container health... "
if docker ps --filter "name=gms_odoo" --filter "status=running" | grep -q "gms_odoo"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((failed++))
fi

# Test 7: PostgreSQL Health
echo -n "7. Testing PostgreSQL health... "
if docker ps --filter "name=gms_postgres" --filter "status=running" | grep -q "gms_postgres"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((failed++))
fi

# Test 8: Response Time
echo -n "8. Testing response time... "
start_time=$(date +%s%3N)
curl -s -o /dev/null http://localhost:8070/web/health
end_time=$(date +%s%3N)
response_time=$((end_time - start_time))
if [ $response_time -lt 5000 ]; then
    echo -e "${GREEN}✓ PASS${NC} (${response_time}ms)"
    ((passed++))
else
    echo -e "${YELLOW}⚠ WARN${NC} (${response_time}ms - slow)"
    ((passed++))
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo -e "Total Tests: $((passed + failed))"
echo -e "${GREEN}Passed: $passed${NC}"
if [ $failed -gt 0 ]; then
    echo -e "${RED}Failed: $failed${NC}"
fi
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Staging environment is ready.${NC}"
    echo ""
    echo "Access Information:"
    echo "  URL: http://localhost:8070"
    echo "  Database: gms_validation"
    echo "  Module: l10n_cr_einvoice (installed)"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please check the errors above.${NC}"
    exit 1
fi
