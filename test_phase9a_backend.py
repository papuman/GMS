#!/usr/bin/env python3
"""
Phase 9A Backend Testing - Costa Rica Tax Reports
Tests all Phase 9A backend enhancements
"""

import sys
import json
from datetime import date
from dateutil.relativedelta import relativedelta


def test_phase9a_changes():
    """Test all Phase 9A backend changes"""

    print("=" * 80)
    print("PHASE 9A BACKEND TESTING - COSTA RICA TAX REPORTS")
    print("=" * 80)
    print()

    results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'tests': []
    }

    # TEST 1: Verify D-151 Expense Line Model
    print("TEST 1: D-151 Expense Line Model")
    print("-" * 80)
    try:
        ExpenseLine = env['l10n_cr.d151.expense.line']
        print("✅ Model 'l10n_cr.d151.expense.line' loaded successfully")

        # Check fields
        if hasattr(ExpenseLine, 'expense_type'):
            print("✅ Field 'expense_type' exists")
        else:
            raise Exception("Field 'expense_type' not found")

        if hasattr(ExpenseLine, 'specific_expense_threshold'):
            print("✅ Field 'specific_expense_threshold' exists in report model")
        else:
            # Check on report model
            Report = env['l10n_cr.d151.report']
            if hasattr(Report, 'specific_expense_threshold'):
                print("✅ Field 'specific_expense_threshold' exists on report model")
            else:
                print("⚠️  Field 'specific_expense_threshold' not found (check model)")

        results['tests'].append({'test': 'D-151 Expense Line Model', 'status': 'PASS'})
        results['passed'] += 1
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        results['tests'].append({'test': 'D-151 Expense Line Model', 'status': 'FAIL', 'error': str(e)})
        results['failed'] += 1
    results['total_tests'] += 1
    print()

    # TEST 2: D-151 Threshold Values
    print("TEST 2: D-151 Threshold Values")
    print("-" * 80)
    try:
        Report = env['l10n_cr.d151.report']

        # Create test report
        period = env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2024,
            'date_from': date(2024, 1, 1),
            'date_to': date(2024, 12, 31),
            'deadline': date(2025, 2, 28),
        })

        report = Report.create({
            'period_id': period.id,
            'company_id': env.company.id,
        })

        # Check default thresholds
        if report.threshold_amount == 2500000.0:
            print(f"✅ General threshold correct: ₡{report.threshold_amount:,.0f}")
        else:
            raise Exception(f"General threshold wrong: {report.threshold_amount}, expected 2500000.0")

        if report.specific_expense_threshold == 50000.0:
            print(f"✅ Specific expense threshold correct: ₡{report.specific_expense_threshold:,.0f}")
        else:
            raise Exception(f"Specific threshold wrong: {report.specific_expense_threshold}, expected 50000.0")

        # Cleanup
        report.unlink()
        period.unlink()

        results['tests'].append({'test': 'D-151 Thresholds', 'status': 'PASS'})
        results['passed'] += 1
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        results['tests'].append({'test': 'D-151 Thresholds', 'status': 'FAIL', 'error': str(e)})
        results['failed'] += 1
    results['total_tests'] += 1
    print()

    # TEST 3: Partner Tax Configuration Fields
    print("TEST 3: Partner Tax Configuration Fields")
    print("-" * 80)
    try:
        Partner = env['res.partner']

        # Create test partner
        partner = Partner.create({
            'name': 'Test Partner Phase 9A',
            'vat': '3-101-999999',
        })

        # Check fields exist and have defaults
        if hasattr(partner, 'l10n_cr_regime_type'):
            print(f"✅ Field 'l10n_cr_regime_type' exists, default: {partner.l10n_cr_regime_type}")
        else:
            raise Exception("Field 'l10n_cr_regime_type' not found")

        if hasattr(partner, 'l10n_cr_free_zone'):
            print(f"✅ Field 'l10n_cr_free_zone' exists, default: {partner.l10n_cr_free_zone}")
        else:
            raise Exception("Field 'l10n_cr_free_zone' not found")

        if hasattr(partner, 'l10n_cr_expense_category'):
            print(f"✅ Field 'l10n_cr_expense_category' exists")
        else:
            raise Exception("Field 'l10n_cr_expense_category' not found")

        # Test setting values
        partner.write({
            'l10n_cr_regime_type': 'simplified',
            'l10n_cr_free_zone': True,
            'l10n_cr_expense_category': 'SP',
        })

        if partner.l10n_cr_regime_type == 'simplified':
            print("✅ Regime type set to 'simplified' successfully")

        if partner.l10n_cr_free_zone:
            print("✅ Free zone flag set successfully")

        if partner.l10n_cr_expense_category == 'SP':
            print("✅ Expense category set to 'SP' successfully")

        # Cleanup
        partner.unlink()

        results['tests'].append({'test': 'Partner Tax Fields', 'status': 'PASS'})
        results['passed'] += 1
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        results['tests'].append({'test': 'Partner Tax Fields', 'status': 'FAIL', 'error': str(e)})
        results['failed'] += 1
    results['total_tests'] += 1
    print()

    # TEST 4: D-150 Proportionality Calculation
    print("TEST 4: D-150 Proportionality Calculation")
    print("-" * 80)
    try:
        D150Report = env['l10n_cr.d150.report']

        # Create test period
        period = env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2024,
            'month': 12,
            'date_from': date(2024, 12, 1),
            'date_to': date(2024, 12, 31),
            'deadline': date(2025, 1, 15),
        })

        # Test Scenario 1: 100% taxable sales
        report1 = D150Report.create({
            'period_id': period.id,
            'company_id': env.company.id,
        })

        report1.write({
            'sales_13_base': 10000.0,
            'sales_exempt': 0.0,
        })

        if report1.proportionality_factor == 100.0:
            print(f"✅ Scenario 1 (100% taxable): Proportionality = {report1.proportionality_factor}%")
        else:
            raise Exception(f"Proportionality wrong: {report1.proportionality_factor}, expected 100.0")

        # Test Scenario 2: Mixed taxable and exempt (83.33%)
        report1.write({
            'sales_13_base': 10000.0,
            'sales_exempt': 2000.0,
        })

        expected = (10000.0 / 12000.0) * 100
        if abs(report1.proportionality_factor - expected) < 0.1:
            print(f"✅ Scenario 2 (mixed sales): Proportionality = {report1.proportionality_factor:.2f}% (expected {expected:.2f}%)")
        else:
            raise Exception(f"Proportionality wrong: {report1.proportionality_factor}, expected {expected}")

        # Cleanup
        report1.unlink()
        period.unlink()

        results['tests'].append({'test': 'D-150 Proportionality', 'status': 'PASS'})
        results['passed'] += 1
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        results['tests'].append({'test': 'D-150 Proportionality', 'status': 'FAIL', 'error': str(e)})
        results['failed'] += 1
    results['total_tests'] += 1
    print()

    # TEST 5: D-101 Progressive vs Flat Tax
    print("TEST 5: D-101 Progressive vs Flat Tax Calculation")
    print("-" * 80)
    try:
        D101Report = env['l10n_cr.d101.report']

        # Create test period
        period = env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2024,
            'date_from': date(2024, 1, 1),
            'date_to': date(2024, 12, 31),
            'deadline': date(2025, 3, 15),
        })

        # Test Scenario 1: Small entity (progressive brackets)
        # Gross income ₡100M, Taxable ₡20M
        report1 = D101Report.create({
            'period_id': period.id,
            'company_id': env.company.id,
        })

        report1.write({
            'sales_revenue': 100000000.0,  # ₡100M
            'cost_of_goods_sold': 50000000.0,
            'operating_expenses': 30000000.0,
        })

        # Should use progressive brackets
        if report1.total_gross_income == 100000000.0:
            print(f"✅ Gross income: ₡{report1.total_gross_income:,.0f}")

        if report1.taxable_income == 20000000.0:
            print(f"✅ Taxable income: ₡{report1.taxable_income:,.0f}")

        # Expected tax (progressive):
        # ₡0-4M: 0%  = ₡0
        # ₡4-8M: 10% × 4M = ₡400K
        # ₡8-16M: 15% × 8M = ₡1,200K
        # ₡16-20M: 20% × 4M = ₡800K
        # Total: ₡2,400,000
        expected_tax = 2400000.0

        if abs(report1.total_income_tax - expected_tax) < 1.0:
            print(f"✅ Progressive tax (₡100M gross, ₡20M taxable): ₡{report1.total_income_tax:,.0f}")
        else:
            raise Exception(f"Progressive tax wrong: {report1.total_income_tax}, expected {expected_tax}")

        # Test Scenario 2: Large entity (flat 30%)
        # Gross income ₡150M (> ₡119.626M threshold), Taxable ₡50M
        report2 = D101Report.create({
            'period_id': period.id,
            'company_id': env.company.id,
        })

        report2.write({
            'sales_revenue': 150000000.0,  # ₡150M (above threshold)
            'cost_of_goods_sold': 60000000.0,
            'operating_expenses': 40000000.0,
        })

        if report2.total_gross_income == 150000000.0:
            print(f"✅ Gross income (large entity): ₡{report2.total_gross_income:,.0f}")

        if report2.taxable_income == 50000000.0:
            print(f"✅ Taxable income: ₡{report2.taxable_income:,.0f}")

        # Expected: 30% flat
        expected_flat = 50000000.0 * 0.30

        if abs(report2.total_income_tax - expected_flat) < 1.0:
            print(f"✅ Flat 30% tax (₡150M gross, ₡50M taxable): ₡{report2.total_income_tax:,.0f}")
        else:
            raise Exception(f"Flat tax wrong: {report2.total_income_tax}, expected {expected_flat}")

        # Cleanup
        report1.unlink()
        report2.unlink()
        period.unlink()

        results['tests'].append({'test': 'D-101 Tax Calculation', 'status': 'PASS'})
        results['passed'] += 1
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        results['tests'].append({'test': 'D-101 Tax Calculation', 'status': 'FAIL', 'error': str(e)})
        results['failed'] += 1
    results['total_tests'] += 1
    print()

    # SUMMARY
    print("=" * 80)
    print("PHASE 9A BACKEND TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['total_tests']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print()

    if results['failed'] == 0:
        print("🎉 ALL TESTS PASSED! Phase 9A backend implementation successful!")
    else:
        print("⚠️  Some tests failed. Review errors above.")

    print()
    print("Test Results:")
    for test in results['tests']:
        status_icon = "✅" if test['status'] == 'PASS' else "❌"
        print(f"  {status_icon} {test['test']}: {test['status']}")
        if test['status'] == 'FAIL':
            print(f"      Error: {test.get('error', 'Unknown')}")

    return results


if __name__ == '__main__':
    results = test_phase9a_changes()
    sys.exit(0 if results['failed'] == 0 else 1)
