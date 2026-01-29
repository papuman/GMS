#!/bin/bash
# Complete E-Invoice Test Suite Execution Script
# Tests Phase 1 (XML Generation), Phase 2 (Digital Signature), and Phase 3 (Hacienda API)
# Generated: 2025-12-28

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS"
ODOO_URL="http://localhost:8070"
STARTUP_WAIT=60

# Function to print colored header
print_header() {
    echo ""
    echo -e "${BLUE}======================================================================"
    echo -e "  $1"
    echo -e "======================================================================${NC}"
    echo ""
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Change to project directory
cd "$PROJECT_DIR"

print_header "E-Invoice Complete Test Suite - Starting at: $(date)"

# Step 1: Check if Docker is running
echo ""
echo -e "${BLUE}[1/6] Checking Docker environment...${NC}"
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi
print_success "Docker is running"

# Step 2: Start Odoo containers
echo ""
echo -e "${BLUE}[2/6] Starting Odoo containers...${NC}"
docker-compose up -d

if [ $? -eq 0 ]; then
    print_success "Containers started successfully"
else
    print_error "Failed to start containers"
    exit 1
fi

# Show running containers
echo ""
echo "Running containers:"
docker ps --filter "name=gms" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Wait for Odoo to start
echo ""
print_warning "Waiting $STARTUP_WAIT seconds for Odoo to fully start..."
for i in $(seq $STARTUP_WAIT -10 1); do
    echo -ne "Time remaining: ${i}s\r"
    sleep 10
done
echo ""

# Step 3: Verify Odoo is accessible
echo ""
echo -e "${BLUE}[3/6] Verifying Odoo accessibility...${NC}"
for attempt in {1..5}; do
    if curl -s -o /dev/null -w "%{http_code}" "$ODOO_URL" | grep -q "200\|303"; then
        print_success "Odoo is accessible at $ODOO_URL"
        break
    else
        if [ $attempt -eq 5 ]; then
            print_error "Odoo is not accessible after 5 attempts"
            print_warning "Check logs with: docker logs gms_odoo"
            exit 1
        fi
        print_warning "Attempt $attempt: Odoo not ready, waiting 10 more seconds..."
        sleep 10
    fi
done

# Step 4: Run Phase 1 tests
echo ""
print_header "[4/6] Phase 1: XML Generation Tests"
if [ -f "test_einvoice_phase1.py" ]; then
    chmod +x test_einvoice_phase1.py
    if python3 test_einvoice_phase1.py 2>&1 | tee phase1_test_output.txt; then
        print_success "Phase 1 tests completed"

        # Check for generated XML
        if ls test_einvoice_*.xml 1> /dev/null 2>&1; then
            XML_COUNT=$(ls -1 test_einvoice_*.xml 2>/dev/null | wc -l)
            print_success "Generated $XML_COUNT XML file(s)"
        fi
    else
        print_error "Phase 1 tests encountered errors (check phase1_test_output.txt)"
    fi
else
    print_error "Phase 1 test script not found: test_einvoice_phase1.py"
fi

# Step 5: Run Phase 2 tests
echo ""
print_header "[5/6] Phase 2: Digital Signature Tests"
if [ -f "test_einvoice_phase2_signature.py" ]; then
    # Verify certificate exists
    CERT_PATH="/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs/Tribu-CR/certificado.p12"
    if [ -f "$CERT_PATH" ]; then
        print_success "Certificate found at $CERT_PATH"
    else
        print_warning "Certificate not found at $CERT_PATH"
        print_warning "Phase 2 tests may fail"
    fi

    chmod +x test_einvoice_phase2_signature.py
    if python3 test_einvoice_phase2_signature.py 2>&1 | tee phase2_test_output.txt; then
        print_success "Phase 2 tests completed"

        # Check for signed XML and JSON results
        if ls signed_xml_*.xml 1> /dev/null 2>&1; then
            SIGNED_COUNT=$(ls -1 signed_xml_*.xml 2>/dev/null | wc -l)
            print_success "Generated $SIGNED_COUNT signed XML file(s)"
        fi

        if ls phase2_signature_test_results_*.json 1> /dev/null 2>&1; then
            print_success "JSON results file generated"
        fi
    else
        print_error "Phase 2 tests encountered errors (check phase2_test_output.txt)"
    fi
else
    print_error "Phase 2 test script not found: test_einvoice_phase2_signature.py"
fi

# Step 6: Run Phase 3 tests
echo ""
print_header "[6/6] Phase 3: Hacienda API Integration Tests"
if [ -f "test_phase3_api.py" ]; then
    chmod +x test_phase3_api.py
    if python3 test_phase3_api.py 2>&1 | tee phase3_test_output.txt; then
        print_success "Phase 3 tests completed"
    else
        print_error "Phase 3 tests encountered errors (check phase3_test_output.txt)"
    fi
else
    print_error "Phase 3 test script not found: test_phase3_api.py"
fi

# Generate summary report
echo ""
print_header "Test Suite Completion Summary - $(date)"

echo ""
echo "Generated Files:"
echo "----------------"
ls -lh test_einvoice_*.xml signed_xml_*.xml phase*_test_output.txt phase2_signature_test_results_*.json 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "Test Output Files:"
echo "------------------"
echo "  Phase 1 Results: phase1_test_output.txt"
echo "  Phase 2 Results: phase2_test_output.txt"
echo "  Phase 3 Results: phase3_test_output.txt"

echo ""
echo "Quick Results Summary:"
echo "----------------------"

# Parse Phase 1 results
if [ -f "phase1_test_output.txt" ]; then
    if grep -q "✅ Module installed: Yes" phase1_test_output.txt; then
        echo -e "  Phase 1: ${GREEN}PASS${NC} - XML Generation working"
    else
        echo -e "  Phase 1: ${RED}FAIL${NC} - Check phase1_test_output.txt"
    fi
fi

# Parse Phase 2 results
if [ -f "phase2_test_output.txt" ]; then
    if grep -q "Pass Rate:" phase2_test_output.txt; then
        PASS_RATE=$(grep "Pass Rate:" phase2_test_output.txt | awk '{print $3}')
        if [ ! -z "$PASS_RATE" ]; then
            PASS_NUM=$(echo $PASS_RATE | cut -d'%' -f1 | cut -d'.' -f1)
            if [ "$PASS_NUM" -ge 90 ]; then
                echo -e "  Phase 2: ${GREEN}PASS${NC} - Pass Rate: $PASS_RATE"
            elif [ "$PASS_NUM" -ge 70 ]; then
                echo -e "  Phase 2: ${YELLOW}PARTIAL${NC} - Pass Rate: $PASS_RATE"
            else
                echo -e "  Phase 2: ${RED}FAIL${NC} - Pass Rate: $PASS_RATE"
            fi
        fi
    else
        echo -e "  Phase 2: ${YELLOW}UNKNOWN${NC} - Check phase2_test_output.txt"
    fi
fi

# Parse Phase 3 results
if [ -f "phase3_test_output.txt" ]; then
    if grep -q "✅.*Authenticated successfully" phase3_test_output.txt; then
        echo -e "  Phase 3: ${GREEN}CONNECTED${NC} - API Integration functional"
    else
        echo -e "  Phase 3: ${RED}FAIL${NC} - Check phase3_test_output.txt"
    fi
fi

echo ""
echo "Recommended Actions:"
echo "--------------------"
echo "  1. Review all three test output files"
echo "  2. Inspect generated XML files for correctness"
echo "  3. Verify signed XML contains valid XMLDSig signature"
echo "  4. Check Phase 2 JSON results for detailed test breakdown"
echo "  5. Address any failed tests before production deployment"

echo ""
print_header "Test Suite Execution Completed"

# Create consolidated report
REPORT_FILE="E_INVOICE_TEST_CONSOLIDATED_REPORT_$(date +%Y%m%d_%H%M%S).txt"
cat > "$REPORT_FILE" << EOF
====================================================================
E-INVOICE TEST SUITE - CONSOLIDATED REPORT
====================================================================

Execution Date: $(date)
Project: GMS E-Invoice System
Database: gms_validation
Odoo Version: 19.0
Module: l10n_cr_einvoice

====================================================================
ENVIRONMENT CONFIGURATION
====================================================================

Docker Containers:
$(docker ps --filter "name=gms" --format "  - {{.Names}}: {{.Status}}" 2>/dev/null || echo "  Unable to retrieve container status")

Odoo URL: $ODOO_URL
Database: gms_validation
Test Scripts:
  - Phase 1: test_einvoice_phase1.py
  - Phase 2: test_einvoice_phase2_signature.py
  - Phase 3: test_phase3_api.py

====================================================================
PHASE 1: XML GENERATION TESTS
====================================================================

Status: $(grep -q "✅ Module installed: Yes" phase1_test_output.txt 2>/dev/null && echo "PASSED" || echo "FAILED/INCOMPLETE")

Key Results:
$(grep "✅\|❌\|⚠️" phase1_test_output.txt 2>/dev/null | head -20 || echo "  No results available")

Generated Files:
$(ls -lh test_einvoice_*.xml 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}' || echo "  No XML files generated")

====================================================================
PHASE 2: DIGITAL SIGNATURE TESTS
====================================================================

Status: $(grep "Pass Rate:" phase2_test_output.txt 2>/dev/null || echo "UNKNOWN")

Detailed Results:
$(grep "✅\|❌" phase2_test_output.txt 2>/dev/null | head -30 || echo "  No results available")

Generated Files:
$(ls -lh signed_xml_*.xml phase2_signature_test_results_*.json 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}' || echo "  No signed files generated")

====================================================================
PHASE 3: HACIENDA API INTEGRATION TESTS
====================================================================

Status: $(grep -q "✅.*Authenticated successfully" phase3_test_output.txt 2>/dev/null && echo "CONNECTED" || echo "FAILED/INCOMPLETE")

Key Results:
$(grep "✅\|❌\|⚠️" phase3_test_output.txt 2>/dev/null | head -20 || echo "  No results available")

====================================================================
OVERALL ASSESSMENT
====================================================================

Production Readiness:
  - Phase 1 (XML Generation): $(grep -q "✅ Module installed: Yes" phase1_test_output.txt 2>/dev/null && echo "READY" || echo "NOT READY")
  - Phase 2 (Digital Signature): $(grep "Pass Rate:" phase2_test_output.txt 2>/dev/null | awk '{rate=$3; gsub(/%/,"",rate); if(rate+0>=90) print "READY"; else if(rate+0>=70) print "PARTIAL"; else print "NOT READY"}' || echo "UNKNOWN")
  - Phase 3 (Hacienda API): $(grep -q "✅.*Authenticated successfully" phase3_test_output.txt 2>/dev/null && echo "CONNECTED" || echo "NOT READY")

Critical Issues Found:
$(grep "❌" phase*_test_output.txt 2>/dev/null | wc -l || echo "0") total failures detected across all phases

Warnings:
$(grep "⚠️" phase*_test_output.txt 2>/dev/null | wc -l || echo "0") total warnings detected across all phases

====================================================================
RECOMMENDATIONS
====================================================================

1. Review Individual Test Outputs:
   - phase1_test_output.txt for XML generation details
   - phase2_test_output.txt for signature validation details
   - phase3_test_output.txt for API integration details

2. Validate Generated Files:
   - Inspect XML structure against Hacienda v4.4 specification
   - Verify signature structure with external XMLDSig validators
   - Test signed XML submission to Hacienda sandbox

3. Address Failures:
   - Fix any critical failures before production deployment
   - Review warnings for potential issues
   - Re-run tests after fixes

4. Next Steps:
   - If all tests pass: Proceed to production configuration
   - If partial pass: Review and fix failed components
   - If tests fail: Review implementation and configuration

====================================================================
REPORT END - Generated at $(date)
====================================================================
EOF

print_success "Consolidated report saved: $REPORT_FILE"
cat "$REPORT_FILE"

echo ""
exit 0
