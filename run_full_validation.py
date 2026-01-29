#!/usr/bin/env python3
"""
COMPREHENSIVE ODOO VALIDATION TEST SUITE
=========================================
Tests all critical functionality for Gym Management System validation
"""

print("=" * 80)
print("ODOO 19.0 GMS VALIDATION TEST SUITE")
print("=" * 80)

# Models
Currency = env['res.currency']
Company = env['res.company']
Product = env['product.product']
Category = env['product.category']
Tax = env['account.tax']
Partner = env['res.partner']
SaleOrder = env['sale.order']
PosConfig = env['pos.config']
Invoice = env['account.move']

# Test results tracking
tests_passed = 0
tests_failed = 0
total_tests = 0

def test(description, condition, error_msg=""):
    global tests_passed, tests_failed, total_tests
    total_tests += 1
    if condition:
        print(f"  ✓ PASS: {description}")
        tests_passed += 1
        return True
    else:
        print(f"  ✗ FAIL: {description} → {error_msg}")
        tests_failed += 1
        return False

# ============================================================================
# TEST SECTION 1: CURRENCY CONFIGURATION
# ============================================================================
print("\n" + "=" * 80)
print("TEST SECTION 1: CURRENCY CONFIGURATION")
print("=" * 80)

company = env.user.company_id
currency_name = company.currency_id.name
currency_symbol = company.currency_id.symbol

test("Currency is Costa Rican Colón (CRC)",
     currency_name == 'CRC',
     f"Currency: {currency_name}")
test("Currency symbol is ₡",
     currency_symbol == '₡',
     f"Symbol: {currency_symbol}")

# ============================================================================
# TEST SECTION 2: PRODUCT CATALOG
# ============================================================================
print("\n" + "=" * 80)
print("TEST SECTION 2: PRODUCT CATALOG")
print("=" * 80)

gym_categories = [
    'Proteínas', 'Pre-Entrenamiento', 'BCAA & Aminoácidos', 'Creatina',
    'Bebidas Deportivas', 'Bebidas Energéticas', 'Refrescos',
    'Barras Proteicas', 'Snacks Saludables', 'Accesorios Gym', 'Ropa Deportiva',
]

categories = Category.search([('name', 'in', gym_categories)])
gym_products = Product.search([('categ_id', 'in', categories.ids)])

test("112 gym products available",
     len(gym_products) == 112,
     f"Found: {len(gym_products)}")

products_with_images = sum(1 for p in gym_products if p.image_1920)
test("All products have images",
     products_with_images == 112,
     f"{products_with_images}/112 have images")

products_with_prices = sum(1 for p in gym_products if p.list_price > 0)
test("All products have pricing",
     products_with_prices == 112,
     f"{products_with_prices}/112 have prices")

# ============================================================================
# TEST SECTION 3: TAX CONFIGURATION (CRITICAL)
# ============================================================================
print("\n" + "=" * 80)
print("TEST SECTION 3: TAX CONFIGURATION")
print("=" * 80)

tax = Tax.search([('amount', '=', 13), ('type_tax_use', '=', 'sale')], limit=1)
test("13% IVA tax configured",
     bool(tax),
     f"Tax found: {tax.name if tax else 'None'}")

if tax:
    products_with_tax = Product.search_count([
        ('categ_id', 'in', categories.ids),
        ('taxes_id', 'in', [tax.id])
    ])
    test("All gym products have 13% tax assigned",
         products_with_tax == 112,
         f"{products_with_tax}/112 products have tax")

# ============================================================================
# TEST SECTION 4: SALES ORDER WORKFLOW
# ============================================================================
print("\n" + "=" * 80)
print("TEST SECTION 4: SALES ORDER WORKFLOW")
print("=" * 80)

# Get or create test customer
partner = Partner.search([('name', '=', 'Validation Test Customer')], limit=1)
if not partner:
    partner = Partner.create({
        'name': 'Validation Test Customer',
        'email': 'validation@test.com',
        'phone': '+506 8888-8888',
    })

test("Test customer created",
     bool(partner),
     f"Customer ID: {partner.id if partner else 'None'}")

# Get sample products for order
protein = Product.search([('name', 'ilike', 'Optimum Nutrition'), ('list_price', '>', 0)], limit=1)
gatorade = Product.search([('name', 'ilike', 'Gatorade')], limit=1)

if protein and gatorade:
    # Create sales order
    order = SaleOrder.create({
        'partner_id': partner.id,
        'order_line': [
            (0, 0, {
                'product_id': protein.id,
                'product_uom_qty': 2,
            }),
            (0, 0, {
                'product_id': gatorade.id,
                'product_uom_qty': 5,
            }),
        ],
    })

    test("Sales order created",
         bool(order),
         f"Order ID: {order.id if order else 'None'}")

    test("Order uses CRC currency",
         order.currency_id.name == 'CRC',
         f"Currency: {order.currency_id.name}")

    # Calculate expected tax
    expected_tax = order.amount_untaxed * 0.13
    tax_tolerance = 1.0  # ₡1 tolerance for rounding

    test("Tax calculated on sales order (13%)",
         abs(order.amount_tax - expected_tax) < tax_tolerance,
         f"Subtotal: ₡{order.amount_untaxed:,.2f}, Tax: ₡{order.amount_tax:,.2f} (expected ₡{expected_tax:,.2f})")

    test("Order total = Subtotal + Tax",
         abs(order.amount_total - (order.amount_untaxed + order.amount_tax)) < 0.01,
         f"Total: ₡{order.amount_total:,.2f}")

    # Confirm the order
    order.action_confirm()
    test("Sales order confirmation successful",
         order.state == 'sale',
         f"State: {order.state}")

    # Try to create invoice
    try:
        invoice = order._create_invoices()
        test("Invoice creation successful",
             bool(invoice),
             f"Invoice ID: {invoice.id if invoice else 'None'}")

        if invoice:
            test("Invoice uses CRC currency",
                 invoice.currency_id.name == 'CRC',
                 f"Currency: {invoice.currency_id.name}")

            test("Invoice tax matches order tax",
                 abs(invoice.amount_tax - order.amount_tax) < 0.01,
                 f"Invoice tax: ₡{invoice.amount_tax:,.2f}, Order tax: ₡{order.amount_tax:,.2f}")

            # Clean up invoice
            invoice.button_draft()
            invoice.button_cancel()
            invoice.unlink()
    except Exception as e:
        test("Invoice creation successful", False, str(e))

    # Clean up order
    order.action_cancel()
    order.unlink()

else:
    test("Sample products found for testing", False, "No products found")

# ============================================================================
# TEST SECTION 5: POINT OF SALE
# ============================================================================
print("\n" + "=" * 80)
print("TEST SECTION 5: POINT OF SALE")
print("=" * 80)

pos_configs = PosConfig.search([], limit=1)
test("POS configuration exists",
     bool(pos_configs),
     f"Config: {pos_configs.name if pos_configs else 'None'}")

pos_products = Product.search_count([('available_in_pos', '=', True)])
test("Products available in POS",
     pos_products >= 112,
     f"Found: {pos_products} products")

if pos_configs:
    test("POS uses CRC currency",
         pos_configs.currency_id.name == 'CRC',
         f"Currency: {pos_configs.currency_id.name}")

# ============================================================================
# TEST SECTION 6: PRODUCT CATEGORIES
# ============================================================================
print("\n" + "=" * 80)
print("TEST SECTION 6: PRODUCT CATEGORIES")
print("=" * 80)

category_tests = {
    'Proteínas': 29,
    'Pre-Entrenamiento': 7,
    'BCAA & Aminoácidos': 5,
    'Creatina': 5,
    'Bebidas Deportivas': 13,
    'Bebidas Energéticas': 9,
    'Refrescos': 5,
    'Barras Proteicas': 8,
    'Snacks Saludables': 6,
    'Accesorios Gym': 9,
    'Ropa Deportiva': 16,
}

for cat_name, expected_count in category_tests.items():
    cat = Category.search([('name', '=', cat_name)], limit=1)
    if cat:
        actual_count = Product.search_count([('categ_id', '=', cat.id)])
        test(f"{cat_name}: {expected_count} products",
             actual_count == expected_count,
             f"Found: {actual_count}")
    else:
        test(f"Category '{cat_name}' exists", False, "Category not found")

# ============================================================================
# FINAL RESULTS
# ============================================================================
print("\n" + "=" * 80)
print("VALIDATION TEST RESULTS")
print("=" * 80)

success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

print(f"\nTotal Tests: {total_tests}")
print(f"Passed: {tests_passed} ({success_rate:.1f}%)")
print(f"Failed: {tests_failed}")

if tests_failed == 0:
    status = "✓ VALIDATION COMPLETE - All tests passed!"
    emoji = "🎉"
elif tests_failed <= 3:
    status = "⚠ VALIDATION PARTIAL - Some issues need attention"
    emoji = "⚠️"
else:
    status = "✗ VALIDATION FAILED - Critical issues detected"
    emoji = "❌"

print(f"\nStatus: {status}")
print(f"\n{emoji} " + "=" * 78 + f" {emoji}")

# Commit any changes (like test customer creation)
env.cr.commit()
