"""
Odoo Shell Script for Comprehensive Membership Testing
Execute this inside the Odoo container using:
docker exec -it gms_odoo odoo shell -d gms_validation --no-http
"""

import logging
from datetime import datetime, timedelta
from odoo import fields

_logger = logging.getLogger(__name__)

# Test Results Storage
test_results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'tests': []
}

def log_test(name, passed, details=''):
    """Log test result"""
    test_results['total'] += 1
    if passed:
        test_results['passed'] += 1
        print(f"✓ PASS: {name}")
    else:
        test_results['failed'] += 1
        print(f"✗ FAIL: {name}")

    if details:
        print(f"  → {details}")

    test_results['tests'].append({
        'name': name,
        'passed': passed,
        'details': details,
        'timestamp': datetime.now()
    })

def setup_currency_and_tax():
    """Setup CRC currency and 13% tax"""
    print("\n" + "="*80)
    print("SETUP: Currency and Tax Configuration")
    print("="*80)

    # Get CRC currency
    currency = env['res.currency'].search([('name', '=', 'CRC')], limit=1)
    if not currency:
        print("✗ CRC currency not found - creating it")
        currency = env['res.currency'].create({
            'name': 'CRC',
            'symbol': '₡',
            'rounding': 0.01,
            'position': 'before',
        })
        log_test("Create CRC Currency", True, f"Currency ID: {currency.id}")
    else:
        log_test("Find CRC Currency", True, f"Currency ID: {currency.id}")

    # Get or create 13% tax
    tax = env['account.tax'].search([
        ('amount', '=', 13),
        ('type_tax_use', '=', 'sale')
    ], limit=1)

    if not tax:
        print("Creating 13% IVA tax...")
        tax = env['account.tax'].create({
            'name': 'IVA 13%',
            'amount': 13,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'description': 'IVA',
        })
        log_test("Create 13% IVA Tax", True, f"Tax ID: {tax.id}")
    else:
        log_test("Find 13% IVA Tax", True, f"Tax ID: {tax.id}, Name: {tax.name}")

    return currency, tax

def create_subscription_recurrence(duration, unit, name):
    """Create subscription recurrence/template"""
    recurrence = env['sale.temporal.recurrence'].search([
        ('duration', '=', duration),
        ('unit', '=', unit)
    ], limit=1)

    if not recurrence:
        recurrence = env['sale.temporal.recurrence'].create({
            'duration': duration,
            'unit': unit,
        })
        print(f"  Created recurrence: {name} ({duration} {unit})")
    else:
        print(f"  Found existing recurrence: {name}")

    return recurrence

def create_membership_products():
    """Create all membership products"""
    print("\n" + "="*80)
    print("CREATING MEMBERSHIP PRODUCTS")
    print("="*80)

    currency, tax = setup_currency_and_tax()

    products = {}

    # Monthly Membership
    print("\n→ Creating Monthly Membership...")
    monthly_recurrence = create_subscription_recurrence(1, 'month', 'Monthly')

    monthly = env['product.product'].create({
        'name': 'Membresía Mensual GMS',
        'type': 'service',
        'list_price': 25000.00,
        'standard_price': 0,
        'taxes_id': [(6, 0, [tax.id])],
        'recurring_invoice': True,
        'sale_ok': True,
        'purchase_ok': False,
        'detailed_type': 'service',
    })

    # Add pricing for subscription
    env['sale.subscription.pricing'].create({
        'product_template_id': monthly.product_tmpl_id.id,
        'recurrence_id': monthly_recurrence.id,
        'price': 25000.00,
    })

    products['monthly'] = monthly
    log_test(
        "Create Monthly Membership Product",
        True,
        f"ID: {monthly.id}, Price: ₡25,000.00"
    )

    # Quarterly Membership
    print("\n→ Creating Quarterly Membership...")
    quarterly_recurrence = create_subscription_recurrence(3, 'month', 'Quarterly')

    quarterly = env['product.product'].create({
        'name': 'Membresía Trimestral GMS',
        'type': 'service',
        'list_price': 65000.00,
        'standard_price': 0,
        'taxes_id': [(6, 0, [tax.id])],
        'recurring_invoice': True,
        'sale_ok': True,
        'purchase_ok': False,
        'detailed_type': 'service',
    })

    env['sale.subscription.pricing'].create({
        'product_template_id': quarterly.product_tmpl_id.id,
        'recurrence_id': quarterly_recurrence.id,
        'price': 65000.00,
    })

    products['quarterly'] = quarterly
    log_test(
        "Create Quarterly Membership Product",
        True,
        f"ID: {quarterly.id}, Price: ₡65,000.00"
    )

    # Annual Membership
    print("\n→ Creating Annual Membership...")
    annual_recurrence = create_subscription_recurrence(1, 'year', 'Annual')

    annual = env['product.product'].create({
        'name': 'Membresía Anual GMS',
        'type': 'service',
        'list_price': 240000.00,
        'standard_price': 0,
        'taxes_id': [(6, 0, [tax.id])],
        'recurring_invoice': True,
        'sale_ok': True,
        'purchase_ok': False,
        'detailed_type': 'service',
    })

    env['sale.subscription.pricing'].create({
        'product_template_id': annual.product_tmpl_id.id,
        'recurrence_id': annual_recurrence.id,
        'price': 240000.00,
    })

    products['annual'] = annual
    log_test(
        "Create Annual Membership Product",
        True,
        f"ID: {annual.id}, Price: ₡240,000.00"
    )

    # Day Pass (Non-recurring)
    print("\n→ Creating Day Pass...")
    day_pass = env['product.product'].create({
        'name': 'Pase Diario GMS',
        'type': 'service',
        'list_price': 5000.00,
        'standard_price': 0,
        'taxes_id': [(6, 0, [tax.id])],
        'recurring_invoice': False,
        'sale_ok': True,
        'purchase_ok': False,
        'detailed_type': 'service',
    })

    products['day_pass'] = day_pass
    log_test(
        "Create Day Pass Product",
        True,
        f"ID: {day_pass.id}, Price: ₡5,000.00"
    )

    return products

def create_test_customers():
    """Create test customers"""
    print("\n" + "="*80)
    print("CREATING TEST CUSTOMERS")
    print("="*80)

    customers = {}

    customer_data = [
        ('Juan Pérez', 'juan.perez@gmstest.com', 'monthly'),
        ('María González', 'maria.gonzalez@gmstest.com', 'quarterly'),
        ('Carlos Rodríguez', 'carlos.rodriguez@gmstest.com', 'annual'),
        ('Ana López', 'ana.lopez@gmstest.com', 'day_pass'),
    ]

    for name, email, key in customer_data:
        # Check if customer exists
        partner = env['res.partner'].search([('email', '=', email)], limit=1)

        if not partner:
            partner = env['res.partner'].create({
                'name': name,
                'email': email,
                'phone': '+506-8888-8888',
                'customer_rank': 1,
                'company_type': 'person',
            })
            print(f"✓ Created customer: {name}")
        else:
            print(f"  Found existing customer: {name}")

        customers[key] = partner

    log_test("Create Test Customers", True, f"Created/found {len(customers)} customers")

    return customers

def create_subscription_order(customer, product, product_name):
    """Create and confirm a subscription order"""
    print(f"\n→ Creating subscription for {product_name}...")

    # Create sale order
    order = env['sale.order'].create({
        'partner_id': customer.id,
        'is_subscription': product.recurring_invoice,
    })

    # Add order line
    line = env['sale.order.line'].create({
        'order_id': order.id,
        'product_id': product.id,
        'product_uom_qty': 1,
    })

    print(f"  Order created: {order.name}")
    print(f"  Amount before tax: ₡{order.amount_untaxed:,.2f}")
    print(f"  Tax (13%): ₡{order.amount_tax:,.2f}")
    print(f"  Total amount: ₡{order.amount_total:,.2f}")

    # Verify tax calculation
    expected_tax = product.list_price * 0.13
    tax_correct = abs(order.amount_tax - expected_tax) < 0.01

    log_test(
        f"Tax Calculation - {product_name}",
        tax_correct,
        f"Expected: ₡{expected_tax:,.2f}, Actual: ₡{order.amount_tax:,.2f}"
    )

    # Confirm order
    try:
        order.action_confirm()
        print(f"  Order confirmed, state: {order.state}")

        log_test(
            f"Create Subscription Order - {product_name}",
            order.state in ['sale', 'subscription'],
            f"Order: {order.name}, State: {order.state}"
        )
    except Exception as e:
        log_test(
            f"Create Subscription Order - {product_name}",
            False,
            f"Error: {str(e)}"
        )

    return order

def test_invoice_generation(order, product_name):
    """Test invoice generation for subscription"""
    print(f"\n→ Testing invoice generation for {product_name}...")

    try:
        # Try to create invoice
        if hasattr(order, '_create_invoices'):
            invoices = order._create_invoices()
        elif hasattr(order, 'action_invoice_create'):
            order.action_invoice_create()
            invoices = order.invoice_ids
        else:
            # Manual invoice creation
            invoice_ids = order._create_invoices()
            invoices = env['account.move'].browse(invoice_ids)

        if invoices:
            for invoice in invoices:
                print(f"  Invoice: {invoice.name}")
                print(f"  Amount: ₡{invoice.amount_total:,.2f}")
                print(f"  State: {invoice.state}")

            log_test(
                f"Invoice Generation - {product_name}",
                True,
                f"Generated {len(invoices)} invoice(s)"
            )
        else:
            log_test(
                f"Invoice Generation - {product_name}",
                False,
                "No invoices generated - may require subscription cron"
            )

    except Exception as e:
        log_test(
            f"Invoice Generation - {product_name}",
            False,
            f"Error: {str(e)}"
        )

def test_subscription_cancellation(order, product_name):
    """Test subscription cancellation"""
    print(f"\n→ Testing cancellation for {product_name}...")

    try:
        order.action_cancel()
        cancelled = order.state == 'cancel'

        log_test(
            f"Subscription Cancellation - {product_name}",
            cancelled,
            f"Order state: {order.state}"
        )

        return cancelled
    except Exception as e:
        log_test(
            f"Subscription Cancellation - {product_name}",
            False,
            f"Error: {str(e)}"
        )
        return False

def check_subscription_module():
    """Check if subscription module is installed"""
    print("\n" + "="*80)
    print("CHECKING SUBSCRIPTION MODULE")
    print("="*80)

    module = env['ir.module.module'].search([
        ('name', '=', 'sale_subscription'),
        ('state', '=', 'installed')
    ], limit=1)

    if module:
        log_test(
            "Subscription Module Installed",
            True,
            f"sale_subscription is installed"
        )
        return True
    else:
        log_test(
            "Subscription Module Installed",
            False,
            "sale_subscription is NOT installed"
        )
        return False

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)

    total = test_results['total']
    passed = test_results['passed']
    failed = test_results['failed']
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {pass_rate:.1f}%\n")

    if failed > 0:
        print("Failed Tests:")
        for test in test_results['tests']:
            if not test['passed']:
                print(f"  ✗ {test['name']}")
                if test['details']:
                    print(f"    → {test['details']}")

def run_all_tests():
    """Main test execution"""
    print("\n" + "="*80)
    print("GMS MEMBERSHIP & SUBSCRIPTION TESTING")
    print("Odoo Shell Script")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check subscription module
    if not check_subscription_module():
        print("\n⚠ WARNING: Subscription module not installed - tests may fail")

    # Create products
    products = create_membership_products()

    # Create customers
    customers = create_test_customers()

    # Create subscriptions
    print("\n" + "="*80)
    print("CREATING AND TESTING SUBSCRIPTIONS")
    print("="*80)

    orders = {}

    # Monthly subscription
    if 'monthly' in products and 'monthly' in customers:
        orders['monthly'] = create_subscription_order(
            customers['monthly'],
            products['monthly'],
            'Monthly Membership'
        )

    # Quarterly subscription
    if 'quarterly' in products and 'quarterly' in customers:
        orders['quarterly'] = create_subscription_order(
            customers['quarterly'],
            products['quarterly'],
            'Quarterly Membership'
        )

    # Annual subscription
    if 'annual' in products and 'annual' in customers:
        orders['annual'] = create_subscription_order(
            customers['annual'],
            products['annual'],
            'Annual Membership'
        )

    # Day pass
    if 'day_pass' in products and 'day_pass' in customers:
        orders['day_pass'] = create_subscription_order(
            customers['day_pass'],
            products['day_pass'],
            'Day Pass'
        )

    # Test invoice generation
    print("\n" + "="*80)
    print("TESTING INVOICE GENERATION")
    print("="*80)

    for key in ['monthly', 'quarterly', 'annual', 'day_pass']:
        if key in orders:
            test_invoice_generation(orders[key], key.replace('_', ' ').title())

    # Test cancellation on one subscription
    print("\n" + "="*80)
    print("TESTING SUBSCRIPTION CANCELLATION")
    print("="*80)

    if 'monthly' in orders:
        test_subscription_cancellation(orders['monthly'], 'Monthly Membership')

    # Commit changes
    env.cr.commit()
    print("\n✓ All changes committed to database")

    # Print summary
    print_summary()

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)

# Run tests
if __name__ == '__main__':
    run_all_tests()
