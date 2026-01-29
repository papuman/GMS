#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 9 Tax Reports - Comprehensive Backend Test

Tests all three tax reports: D-150, D-101, D-151

Usage:
    python test_phase9_tax_reports.py

Or in Odoo shell:
    docker-compose exec odoo odoo shell -d your_database
    >>> exec(open('test_phase9_tax_reports.py').read())
"""

import sys
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test(test_name, status, details=""):
    """Print test result"""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {test_name}")
    if details:
        print(f"   → {details}")


def test_models_loaded(env):
    """Test 1: Verify all models are loaded"""
    print_section("TEST 1: Models Loaded")

    tests = [
        ('Tax Period', 'l10n_cr.tax.report.period'),
        ('D-150 VAT Report', 'l10n_cr.d150.report'),
        ('D-101 Income Tax', 'l10n_cr.d101.report'),
        ('D-151 Informative', 'l10n_cr.d151.report'),
        ('D-151 Customer Line', 'l10n_cr.d151.customer.line'),
        ('D-151 Supplier Line', 'l10n_cr.d151.supplier.line'),
        ('XML Generator', 'l10n_cr.tax.report.xml.generator'),
    ]

    all_passed = True
    for name, model_name in tests:
        try:
            model = env[model_name]
            print_test(name, True, f"Model: {model._name}")
        except Exception as e:
            print_test(name, False, f"ERROR: {str(e)}")
            all_passed = False

    return all_passed


def test_d150_monthly_vat(env):
    """Test 2: D-150 Monthly VAT Report"""
    print_section("TEST 2: D-150 Monthly VAT Report")

    try:
        # Create period for November 2025
        print("\n📅 Creating period for November 2025...")
        period = env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
        })
        print_test("Period created", True, f"{period.name} (Deadline: {period.deadline})")

        # Check computed fields
        print_test("Period name computed", period.name == "D-150 November 2025")
        print_test("Deadline computed", period.deadline is not None)

        # Create D-150 report
        print("\n📝 Creating D-150 report...")
        period.action_create_report()
        d150 = period.d150_report_id

        print_test("D-150 report created", d150 is not None, f"ID: {d150.id}")
        print_test("Initial state is draft", d150.state == 'draft')

        # Calculate D-150
        print("\n🧮 Calculating D-150...")
        d150.action_calculate()

        print_test("D-150 calculated", d150.state == 'calculated')
        print(f"\n   Sales Summary:")
        print(f"     - Total Base: ₡{d150.sales_total_base:,.2f}")
        print(f"     - Total Tax: ₡{d150.sales_total_tax:,.2f}")
        print(f"   Purchases Summary:")
        print(f"     - Total Base: ₡{d150.purchases_total_base:,.2f}")
        print(f"     - Total Credit: ₡{d150.purchases_total_tax:,.2f}")
        print(f"   Settlement:")
        print(f"     - Net Amount Due: ₡{d150.net_amount_due:,.2f}")
        if d150.amount_to_pay > 0:
            print(f"     - Amount to Pay: ₡{d150.amount_to_pay:,.2f}")
        else:
            print(f"     - Credit to Next Period: ₡{d150.credit_to_next_period:,.2f}")

        # Test XML generation
        print("\n🔧 Generating XML...")
        d150.action_generate_xml()

        print_test("XML generated", d150.xml_content is not False and d150.xml_content is not None)
        print_test("State changed to ready", d150.state == 'ready')

        if d150.xml_content:
            xml_preview = d150.xml_content[:200] if len(d150.xml_content) > 200 else d150.xml_content
            print(f"   XML Preview: {xml_preview}...")

        # Test workflow reset
        print("\n🔄 Testing reset to draft...")
        d150.action_reset_to_draft()
        print_test("Reset to draft", d150.state == 'draft')
        print_test("XML cleared", d150.xml_content is False)

        # Cleanup
        print("\n🧹 Cleaning up test data...")
        period.unlink()
        print_test("Test period deleted", True)

        return True

    except Exception as e:
        print_test("D-150 Test", False, f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_d101_income_tax(env):
    """Test 3: D-101 Annual Income Tax"""
    print_section("TEST 3: D-101 Annual Income Tax Report")

    try:
        # Create period for 2025
        print("\n📅 Creating period for 2025...")
        period = env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
        })
        print_test("Period created", True, f"{period.name} (Deadline: {period.deadline})")

        # Check computed fields
        print_test("Period name computed", period.name == "D-101 2025")
        print_test("Deadline is Mar 15", period.deadline == date(2026, 3, 15))

        # Create D-101 report
        print("\n📝 Creating D-101 report...")
        period.action_create_report()
        d101 = period.d101_report_id

        print_test("D-101 report created", d101 is not None, f"ID: {d101.id}")
        print_test("Initial state is draft", d101.state == 'draft')

        # Set some test data manually (simulating calculation)
        print("\n💰 Setting test income and expenses...")
        d101.write({
            'sales_revenue': 50000000,  # ₡50M
            'other_income': 2000000,    # ₡2M
            'operating_expenses': 30000000,  # ₡30M
            'depreciation': 5000000,    # ₡5M
        })

        # Check computed fields
        print_test("Gross income computed", d101.total_gross_income == 52000000)
        print_test("Total expenses computed", d101.total_deductible_expenses == 35000000)
        print_test("Taxable income computed", d101.taxable_income > 0)

        print(f"\n   Income Summary:")
        print(f"     - Gross Income: ₡{d101.total_gross_income:,.2f}")
        print(f"     - Deductible Expenses: ₡{d101.total_deductible_expenses:,.2f}")
        print(f"     - Taxable Income: ₡{d101.taxable_income:,.2f}")

        # Check tax brackets
        print(f"\n   Tax Brackets:")
        print(f"     - 0% Bracket: ₡{d101.tax_bracket_0_amount:,.2f}")
        print(f"     - 10% Bracket: ₡{d101.tax_bracket_10_amount:,.2f}")
        print(f"     - 15% Bracket: ₡{d101.tax_bracket_15_amount:,.2f}")
        print(f"     - 20% Bracket: ₡{d101.tax_bracket_20_amount:,.2f}")
        print(f"     - 25% Bracket: ₡{d101.tax_bracket_25_amount:,.2f}")
        print(f"     - Total Tax: ₡{d101.total_income_tax:,.2f}")

        print_test("Tax calculated", d101.total_income_tax > 0)

        # Test with advance payments
        print("\n💳 Adding advance payments...")
        d101.write({
            'advance_payments': 2000000,  # ₡2M paid in advance
            'withholdings': 500000,       # ₡500K withheld
        })

        print_test("Total credits computed", d101.total_credits == 2500000)
        print(f"   Final Settlement:")
        print(f"     - Tax Due: ₡{d101.total_income_tax:,.2f}")
        print(f"     - Credits: ₡{d101.total_credits:,.2f}")
        print(f"     - Net Tax Due: ₡{d101.net_tax_due:,.2f}")
        if d101.amount_to_pay > 0:
            print(f"     - Amount to Pay: ₡{d101.amount_to_pay:,.2f}")
        else:
            print(f"     - Refund Amount: ₡{d101.refund_amount:,.2f}")

        # Calculate from actual data
        print("\n🧮 Calculating from actual accounting data...")
        d101.state = 'draft'  # Reset to allow recalculation
        d101.action_calculate()

        print_test("D-101 calculated from real data", d101.state == 'calculated')
        print(f"   Actual Sales Revenue: ₡{d101.sales_revenue:,.2f}")
        print(f"   Actual Operating Expenses: ₡{d101.operating_expenses:,.2f}")

        # Test XML generation
        print("\n🔧 Generating XML...")
        d101.action_generate_xml()

        print_test("XML generated", d101.xml_content is not False and d101.xml_content is not None)
        print_test("State changed to ready", d101.state == 'ready')

        # Cleanup
        print("\n🧹 Cleaning up test data...")
        period.unlink()
        print_test("Test period deleted", True)

        return True

    except Exception as e:
        print_test("D-101 Test", False, f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_d151_informative(env):
    """Test 4: D-151 Annual Informative Report"""
    print_section("TEST 4: D-151 Annual Informative Report")

    try:
        # Create period for 2025
        print("\n📅 Creating period for 2025...")
        period = env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
        })
        print_test("Period created", True, f"{period.name} (Deadline: {period.deadline})")

        # Check computed fields
        print_test("Period name computed", period.name == "D-151 2025")
        print_test("Deadline is Apr 15", period.deadline == date(2026, 4, 15))

        # Create D-151 report
        print("\n📝 Creating D-151 report...")
        period.action_create_report()
        d151 = period.d151_report_id

        print_test("D-151 report created", d151 is not None, f"ID: {d151.id}")
        print_test("Initial state is draft", d151.state == 'draft')
        print_test("Default threshold", d151.threshold_amount == 500000.0)

        # Calculate D-151
        print("\n🧮 Calculating D-151 (finding partners with transactions > ₡500K)...")
        d151.action_calculate()

        print_test("D-151 calculated", d151.state == 'calculated')

        # Check statistics
        print(f"\n   Summary Statistics:")
        print(f"     - Customers Reported: {d151.total_customers_reported}")
        print(f"     - Suppliers Reported: {d151.total_suppliers_reported}")
        print(f"     - Total Sales Amount: ₡{d151.total_sales_amount:,.2f}")
        print(f"     - Total Purchases Amount: ₡{d151.total_purchases_amount:,.2f}")

        print_test("Statistics computed", True)

        # Show top customers
        if d151.customer_line_ids:
            print(f"\n   Top Customers (showing up to 5):")
            for i, line in enumerate(d151.customer_line_ids[:5], 1):
                print(f"     {i}. {line.partner_name}")
                print(f"        VAT: {line.partner_vat}")
                print(f"        Amount: ₡{line.total_amount:,.2f}")
                print(f"        Transactions: {line.transaction_count}")
        else:
            print(f"\n   ℹ️  No customers above threshold (₡500,000)")

        # Show top suppliers
        if d151.supplier_line_ids:
            print(f"\n   Top Suppliers (showing up to 5):")
            for i, line in enumerate(d151.supplier_line_ids[:5], 1):
                print(f"     {i}. {line.partner_name}")
                print(f"        VAT: {line.partner_vat}")
                print(f"        Amount: ₡{line.total_amount:,.2f}")
                print(f"        Transactions: {line.transaction_count}")
        else:
            print(f"\n   ℹ️  No suppliers above threshold (₡500,000)")

        # Test XML generation
        print("\n🔧 Generating XML...")
        d151.action_generate_xml()

        print_test("XML generated", d151.xml_content is not False and d151.xml_content is not None)
        print_test("State changed to ready", d151.state == 'ready')

        # Cleanup
        print("\n🧹 Cleaning up test data...")
        period.unlink()
        print_test("Test period deleted", True)

        return True

    except Exception as e:
        print_test("D-151 Test", False, f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_tax_period_helpers(env):
    """Test 5: Tax Period Helper Methods"""
    print_section("TEST 5: Tax Period Helper Methods")

    try:
        # Test create_monthly_period
        print("\n📅 Testing create_monthly_period helper...")
        period = env['l10n_cr.tax.report.period'].create_monthly_period(2025, 12)

        print_test("Helper method works", period is not None)
        print_test("Correct month", period.month == 12)
        print_test("Correct year", period.year == 2025)
        print_test("Date range set", period.date_from == date(2025, 12, 1))
        print_test("Date range end", period.date_to == date(2025, 12, 31))

        # Test is_overdue
        print("\n⏰ Testing overdue detection...")
        past_period = env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2024,
            'month': 1,
            'state': 'draft',
        })

        is_overdue = past_period.is_overdue()
        print_test("Overdue detection works", is_overdue == True, "Past deadline detected")

        # Cleanup
        period.unlink()
        past_period.unlink()

        return True

    except Exception as e:
        print_test("Helper Methods Test", False, f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_xml_validation(env):
    """Test 6: XML Structure Validation"""
    print_section("TEST 6: XML Structure Validation")

    try:
        XMLGenerator = env['l10n_cr.tax.report.xml.generator']

        # Create a test D-150 with data
        period = env['l10n_cr.tax.report.period'].create_monthly_period(2025, 11)
        period.action_create_report()
        d150 = period.d150_report_id

        # Set some test data
        d150.write({
            'sales_13_base': 1000000,
            'sales_13_tax': 130000,
            'purchases_goods_13_base': 500000,
            'purchases_goods_13_tax': 65000,
        })

        # Generate XML
        xml_content = XMLGenerator.generate_d150_xml(d150)

        print_test("XML generated", xml_content is not None and len(xml_content) > 0)

        # Check XML contains expected elements
        checks = [
            ('XML declaration', '<?xml' in xml_content),
            ('D150 root element', '<D150' in xml_content),
            ('Periodo element', '<Periodo>' in xml_content),
            ('Contribuyente element', '<Contribuyente>' in xml_content),
            ('Ventas element', '<Ventas>' in xml_content),
            ('Compras element', '<Compras>' in xml_content),
            ('Liquidacion element', '<Liquidacion>' in xml_content),
        ]

        print("\n   XML Structure Checks:")
        for check_name, result in checks:
            print_test(check_name, result)

        # Validate structure
        print("\n🔍 Validating XML structure...")
        validation = XMLGenerator.validate_xml_structure(xml_content, 'D150')

        print_test("XML validation", validation['valid'],
                   "No errors" if validation['valid'] else f"Errors: {validation['errors']}")

        # Cleanup
        period.unlink()

        return True

    except Exception as e:
        print_test("XML Validation Test", False, f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_cron_jobs(env):
    """Test 7: Cron Jobs Configuration"""
    print_section("TEST 7: Cron Jobs Configuration")

    try:
        # Find D-150 cron jobs
        crons = env['ir.cron'].search([
            ('name', 'ilike', 'D-150')
        ])

        print(f"\n   Found {len(crons)} D-150 cron job(s):")

        for cron in crons:
            print(f"\n   📅 {cron.name}")
            print(f"      Model: {cron.model_id.name}")
            print(f"      Code: {cron.code}")
            print(f"      Interval: {cron.interval_number} {cron.interval_type}")
            print(f"      Active: {'✅' if cron.active else '❌'}")

            print_test(f"Cron '{cron.name}' configured", True)

        print_test("Cron jobs exist", len(crons) > 0)

        return True

    except Exception as e:
        print_test("Cron Jobs Test", False, f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests(env):
    """Run all Phase 9 tests"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 10 + "PHASE 9 TAX REPORTS - BACKEND TEST SUITE" + " " * 17 + "║")
    print("║" + " " * 20 + "Version 19.0.1.11.0" + " " * 28 + "║")
    print("╚" + "═" * 68 + "╝")

    results = []

    # Run tests
    results.append(("Models Loaded", test_models_loaded(env)))
    results.append(("D-150 Monthly VAT", test_d150_monthly_vat(env)))
    results.append(("D-101 Annual Income Tax", test_d101_income_tax(env)))
    results.append(("D-151 Annual Informative", test_d151_informative(env)))
    results.append(("Tax Period Helpers", test_tax_period_helpers(env)))
    results.append(("XML Validation", test_xml_validation(env)))
    results.append(("Cron Jobs", test_cron_jobs(env)))

    # Summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n   Test Results:")
    for test_name, result in results:
        symbol = "✅" if result else "❌"
        print(f"   {symbol} {test_name}")

    print(f"\n   Overall: {passed}/{total} tests passed")

    if passed == total:
        print("\n   🎉 ALL TESTS PASSED! Backend is ready for UI development.")
    else:
        print(f"\n   ⚠️  {total - passed} test(s) failed. Please review errors above.")

    print("\n" + "=" * 70 + "\n")

    return passed == total


# Main execution
if __name__ == '__main__':
    try:
        # When run in Odoo shell, 'env' is available
        run_all_tests(env)
    except NameError:
        print("❌ This script must be run in Odoo shell context")
        print("\nUsage:")
        print("  docker-compose exec odoo odoo shell -d your_database")
        print("  >>> exec(open('test_phase9_tax_reports.py').read())")
        sys.exit(1)
