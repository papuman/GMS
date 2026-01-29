#!/usr/bin/env python3
"""
Fix 13% IVA Tax Configuration for Costa Rica
============================================
This script configures the 13% Costa Rica sales tax and assigns it to all gym products.
"""

import xmlrpc.client

# Connection details
url = 'http://localhost:8070'
db = 'gms_validation'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("=" * 70)
print("FIXING TAX CONFIGURATION FOR COSTA RICA")
print("=" * 70)

# Step 1: Find or create 13% IVA sales tax
print("\n1. Configuring 13% IVA Sales Tax...")
print("-" * 70)

# Search for existing 13% sales tax
tax_ids = models.execute_kw(db, uid, password, 'account.tax', 'search', [
    [('amount', '=', 13), ('type_tax_use', '=', 'sale')]
])

if tax_ids:
    tax_id = tax_ids[0]
    tax = models.execute_kw(db, uid, password, 'account.tax', 'read', [tax_id], {'fields': ['name', 'amount', 'type_tax_use']})[0]
    print(f"✓ Found existing 13% sales tax: {tax['name']}")
else:
    # Create the 13% IVA tax
    print("Creating new 13% IVA sales tax...")
    tax_id = models.execute_kw(db, uid, password, 'account.tax', 'create', [{
        'name': 'IVA 13% (Ventas)',
        'amount': 13.0,
        'amount_type': 'percent',
        'type_tax_use': 'sale',
        'description': 'IVA13',
        'active': True,
    }])
    print(f"✓ Created tax ID: {tax_id}")

# Step 2: Get all gym product categories
print("\n2. Identifying Gym Products...")
print("-" * 70)

gym_categories = [
    'Proteínas',
    'Pre-Entrenamiento',
    'BCAA & Aminoácidos',
    'Creatina',
    'Bebidas Deportivas',
    'Bebidas Energéticas',
    'Refrescos',
    'Barras Proteicas',
    'Snacks Saludables',
    'Accesorios Gym',
    'Ropa Deportiva',
]

# Get category IDs
category_ids = models.execute_kw(db, uid, password, 'product.category', 'search', [
    [('name', 'in', gym_categories)]
])

print(f"Found {len(category_ids)} gym categories")

# Step 3: Get all gym products
gym_product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [
    [('categ_id', 'in', category_ids)]
])

print(f"Found {len(gym_product_ids)} gym products")

# Step 4: Assign tax to all gym products
print("\n3. Assigning 13% IVA Tax to All Gym Products...")
print("-" * 70)

if gym_product_ids:
    # Update all products with the tax
    models.execute_kw(db, uid, password, 'product.product', 'write', [
        gym_product_ids,
        {'taxes_id': [(6, 0, [tax_id])]}  # Replace all taxes with this one
    ])
    print(f"✓ Assigned 13% IVA tax to {len(gym_product_ids)} products")
else:
    print("⚠ No gym products found!")

# Step 5: Verify configuration
print("\n4. Verifying Tax Configuration...")
print("-" * 70)

# Sample a few products to verify
sample_products = models.execute_kw(db, uid, password, 'product.product', 'search_read', [
    [('categ_id', 'in', category_ids)],
    ['name', 'list_price', 'taxes_id']
], {'limit': 5})

for product in sample_products:
    tax_count = len(product['taxes_id'])
    print(f"  • {product['name'][:50]:<50} | ₡{product['list_price']:>8,.0f} | Taxes: {tax_count}")

# Count products with tax
products_with_tax = models.execute_kw(db, uid, password, 'product.product', 'search_count', [
    [('categ_id', 'in', category_ids), ('taxes_id', '!=', False)]
])

print(f"\n✓ Products with tax configured: {products_with_tax}/{len(gym_product_ids)}")

# Step 6: Test with a sample sale order
print("\n5. Testing Tax Calculation on Sales Order...")
print("-" * 70)

# Get a test customer
partner_ids = models.execute_kw(db, uid, password, 'res.partner', 'search', [
    [('name', '=', 'Test Customer')]
], {'limit': 1})

if not partner_ids:
    # Create test customer
    partner_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{
        'name': 'Test Customer',
        'email': 'test@example.com',
    }])
else:
    partner_id = partner_ids[0]

# Get a protein product
protein_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [
    [('name', 'ilike', 'Optimum Nutrition')]
], {'limit': 1})

if protein_ids:
    protein = models.execute_kw(db, uid, password, 'product.product', 'read', [protein_ids[0]],
                                {'fields': ['name', 'list_price', 'taxes_id']})[0]

    print(f"Test Product: {protein['name']}")
    print(f"Price: ₡{protein['list_price']:,.2f}")
    print(f"Taxes: {len(protein['taxes_id'])} tax(es) assigned")

    # Create a test sales order
    order_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [{
        'partner_id': partner_id,
        'order_line': [(0, 0, {
            'product_id': protein['id'],
            'product_uom_qty': 2,
        })],
    }])

    # Read the order to see calculated taxes
    order = models.execute_kw(db, uid, password, 'sale.order', 'read', [order_id],
                              {'fields': ['amount_untaxed', 'amount_tax', 'amount_total']})[0]

    print(f"\nSales Order Created:")
    print(f"  Subtotal:  ₡{order['amount_untaxed']:>10,.2f}")
    print(f"  Tax (13%): ₡{order['amount_tax']:>10,.2f}")
    print(f"  Total:     ₡{order['amount_total']:>10,.2f}")

    expected_tax = order['amount_untaxed'] * 0.13
    tax_percentage = (order['amount_tax'] / order['amount_untaxed'] * 100) if order['amount_untaxed'] > 0 else 0

    if abs(order['amount_tax'] - expected_tax) < 0.01:
        print(f"\n✓ Tax calculation CORRECT ({tax_percentage:.1f}%)")
    else:
        print(f"\n✗ Tax calculation INCORRECT")
        print(f"  Expected: ₡{expected_tax:,.2f}")
        print(f"  Got:      ₡{order['amount_tax']:,.2f}")

    # Clean up test order
    models.execute_kw(db, uid, password, 'sale.order', 'unlink', [[order_id]])

print("\n" + "=" * 70)
print("TAX CONFIGURATION COMPLETE")
print("=" * 70)
