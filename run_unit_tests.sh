#!/bin/bash
# Run Odoo unit tests for l10n_cr_einvoice module
# Usage: ./run_unit_tests.sh

set -e

DB_NAME="gms_validation"
MODULE="l10n_cr_einvoice"

echo "======================================================================"
echo "Running Unit Tests for $MODULE"
echo "======================================================================"
echo ""

# Run tests using Odoo test framework
docker exec gms_odoo odoo \
    -d $DB_NAME \
    --test-enable \
    --test-tags /l10n_cr_einvoice \
    --stop-after-init \
    --log-level=test \
    2>&1 | tee /tmp/test_output.log

echo ""
echo "======================================================================"
echo "Test execution completed"
echo "======================================================================"
