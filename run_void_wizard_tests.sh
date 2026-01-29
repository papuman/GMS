#!/bin/bash
# -*- coding: utf-8 -*-
"""
Simple Test Runner for Gym Invoice Void Wizard

Runs all test suites using odoo-bin test command.

Usage:
    ./run_void_wizard_tests.sh              # Run all tests
    ./run_void_wizard_tests.sh unit         # Run unit tests only
    ./run_void_wizard_tests.sh integration  # Run integration tests only
    ./run_void_wizard_tests.sh membership   # Run membership tests only
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Gym Invoice Void Wizard Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Determine which tests to run
TEST_SUITE=${1:-all}

case $TEST_SUITE in
    unit)
        echo -e "${YELLOW}Running Unit Tests...${NC}"
        python3 odoo-bin -c odoo.conf \
            --test-enable \
            --test-tags l10n_cr_einvoice.test_gym_void_wizard_unit \
            --stop-after-init \
            --log-level=test
        ;;

    integration)
        echo -e "${YELLOW}Running Integration Tests...${NC}"
        python3 odoo-bin -c odoo.conf \
            --test-enable \
            --test-tags l10n_cr_einvoice.test_gym_void_wizard_integration \
            --stop-after-init \
            --log-level=test
        ;;

    membership)
        echo -e "${YELLOW}Running Membership Tests...${NC}"
        python3 odoo-bin -c odoo.conf \
            --test-enable \
            --test-tags l10n_cr_einvoice.test_gym_void_wizard_membership \
            --stop-after-init \
            --log-level=test
        ;;

    all)
        echo -e "${YELLOW}Running All Tests...${NC}"
        echo ""

        echo -e "${BLUE}1/3: Unit Tests${NC}"
        python3 odoo-bin -c odoo.conf \
            --test-enable \
            --test-tags l10n_cr_einvoice.test_gym_void_wizard_unit \
            --stop-after-init \
            --log-level=test
        UNIT_RESULT=$?

        echo ""
        echo -e "${BLUE}2/3: Integration Tests${NC}"
        python3 odoo-bin -c odoo.conf \
            --test-enable \
            --test-tags l10n_cr_einvoice.test_gym_void_wizard_integration \
            --stop-after-init \
            --log-level=test
        INTEGRATION_RESULT=$?

        echo ""
        echo -e "${BLUE}3/3: Membership Tests${NC}"
        python3 odoo-bin -c odoo.conf \
            --test-enable \
            --test-tags l10n_cr_einvoice.test_gym_void_wizard_membership \
            --stop-after-init \
            --log-level=test
        MEMBERSHIP_RESULT=$?

        echo ""
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}  Test Results Summary${NC}"
        echo -e "${BLUE}========================================${NC}"

        if [ $UNIT_RESULT -eq 0 ]; then
            echo -e "${GREEN}✅ Unit Tests: PASSED${NC}"
        else
            echo -e "${RED}❌ Unit Tests: FAILED${NC}"
        fi

        if [ $INTEGRATION_RESULT -eq 0 ]; then
            echo -e "${GREEN}✅ Integration Tests: PASSED${NC}"
        else
            echo -e "${RED}❌ Integration Tests: FAILED${NC}"
        fi

        if [ $MEMBERSHIP_RESULT -eq 0 ]; then
            echo -e "${GREEN}✅ Membership Tests: PASSED${NC}"
        else
            echo -e "${RED}❌ Membership Tests: FAILED${NC}"
        fi

        echo ""

        if [ $UNIT_RESULT -eq 0 ] && [ $INTEGRATION_RESULT -eq 0 ] && [ $MEMBERSHIP_RESULT -eq 0 ]; then
            echo -e "${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
            exit 0
        else
            echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
            exit 1
        fi
        ;;

    *)
        echo -e "${RED}Unknown test suite: $TEST_SUITE${NC}"
        echo "Usage: $0 [unit|integration|membership|all]"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}========================================${NC}"
