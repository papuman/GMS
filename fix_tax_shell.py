#!/usr/bin/env python3
"""Fix 13% IVA Tax Configuration - Odoo Shell Script"""

print("=" * 70)
print("FIXING TAX CONFIGURATION FOR COSTA RICA")
print("=" * 70)

# In Odoo shell, 'env' is already available
# Models
Tax = env['account.tax']
Product = env['product.product']
Category = env['product.category']
SaleOrder = env['sale.order']
Partner = env['res.partner']

# Step 1: Find or create 13% IVA sales tax
print("\n1. Configuring 13% IVA Sales Tax...")
print("-" * 70)

tax = Tax.search([('amount', '=', 13), ('type_tax_use', '=', 'sale')], limit=1)

if tax:
    print(f"✓ Found existing 13% sales tax: {tax.name}")
else:
    print("Creating new 13% IVA sales tax...")
    tax = Tax.create({
        'name': 'IVA 13% (Ventas)',
        'amount': 13.0,
        'amount_type': 'percent',
        'type_tax_use': 'sale',
        'description': 'IVA13',
        'active': True,
    })
    print(f"✓ Created tax: {tax.name} (ID: {tax.id})")

# Step 2: Get all gym product categories
print("\n2. Identifying Gym Products...")
print("-" * 70)

gym_categories = [
    'Proteínas', 'Pre-Entrenamiento', 'BCAA & Aminoácidos', 'Creatina',
    'Bebidas Deportivas', 'Bebidas Energéticas', 'Refrescos',
    'Barras Proteicas', 'Snacks Saludables', 'Accesorios Gym', 'Ropa Deportiva',
]

categories = Category.search([('name', 'in', gym_categories)])
print(f"Found {len(categories)} gym categories")

# Step 3: Get all gym products
gym_products = Product.search([('categ_id', 'in', categories.ids)])
print(f"Found {len(gym_products)} gym products")

# Step 4: Assign tax to all gym products
print("\n3. Assigning 13% IVA Tax to All Gym Products...")
print("-" * 70)

if gym_products:
    gym_products.write({'taxes_id': [(6, 0, [tax.id])]})
    env.cr.commit()
    print(f"✓ Assigned 13% IVA tax to {len(gym_products)} products")

# Step 5: Verify configuration
print("\n4. Verifying Tax Configuration...")
print("-" * 70)

sample = gym_products[:5]
for product in sample:
    tax_count = len(product.taxes_id)
    print(f"  • {product.name[:50]:<50} | ₡{product.list_price:>8,.0f} | Taxes: {tax_count}")

products_with_tax = Product.search_count([
    ('categ_id', 'in', categories.ids),
    ('taxes_id', '!=', False)
])

print(f"\n✓ Products with tax: {products_with_tax}/{len(gym_products)}")

# Step 6: Test with sample sales order
print("\n5. Testing Tax Calculation on Sales Order...")
print("-" * 70)

# Get or create test customer
partner = Partner.search([('name', '=', 'Test Customer')], limit=1)
if not partner:
    partner = Partner.create({'name': 'Test Customer', 'email': 'test@example.com'})

# Get a protein product
protein = Product.search([('name', 'ilike', 'Optimum Nutrition')], limit=1)

if protein:
    print(f"Test Product: {protein.name}")
    print(f"Price: ₡{protein.list_price:,.2f}")
    print(f"Taxes: {len(protein.taxes_id)} tax(es) assigned")

    # Create test order
    order = SaleOrder.create({
        'partner_id': partner.id,
        'order_line': [(0, 0, {
            'product_id': protein.id,
            'product_uom_qty': 2,
        })],
    })

    print(f"\nSales Order Created:")
    print(f"  Subtotal:  ₡{order.amount_untaxed:>10,.2f}")
    print(f"  Tax (13%): ₡{order.amount_tax:>10,.2f}")
    print(f"  Total:     ₡{order.amount_total:>10,.2f}")

    expected_tax = order.amount_untaxed * 0.13
    tax_pct = (order.amount_tax / order.amount_untaxed * 100) if order.amount_untaxed > 0 else 0

    if abs(order.amount_tax - expected_tax) < 0.01:
        print(f"\n✓ Tax calculation CORRECT ({tax_pct:.1f}%)")
    else:
        print(f"\n✗ Tax calculation INCORRECT")
        print(f"  Expected: ₡{expected_tax:,.2f}")
        print(f"  Got:      ₡{order.amount_tax:,.2f}")

    # Clean up
    order.unlink()

env.cr.commit()

print("\n" + "=" * 70)
print("TAX CONFIGURATION COMPLETE")
print("=" * 70)
