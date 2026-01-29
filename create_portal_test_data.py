#!/usr/bin/env python3
"""
Create test data for portal users
"""

import sys
import subprocess

script = """
# Get portal users
portal_users = env['res.users'].search([
    ('login', 'in', ['john.portal@gymtest.com', 'jane.premium@gymtest.com', 'mike.basic@gymtest.com'])
])

print(f"Found {len(portal_users)} portal users")

# Create membership products
product_obj = env['product.product']
membership_products = []

for product_data in [
    {'name': 'Monthly Premium Membership', 'price': 99.00},
    {'name': 'Monthly Basic Membership', 'price': 49.00},
    {'name': 'Annual VIP Membership', 'price': 999.00},
]:
    product = product_obj.search([('name', '=', product_data['name'])], limit=1)
    if not product:
        product = product_obj.create({
            'name': product_data['name'],
            'list_price': product_data['price'],
            'type': 'service',
        })
        print(f"Created product: {product.name}")
    else:
        print(f"Product exists: {product.name}")
    membership_products.append(product)

# Create retail products
retail_products = []
for product_data in [
    {'name': 'Protein Shake', 'price': 5.99},
    {'name': 'Gym Towel', 'price': 15.00},
    {'name': 'Water Bottle', 'price': 12.00},
]:
    product = product_obj.search([('name', '=', product_data['name'])], limit=1)
    if not product:
        product = product_obj.create({
            'name': product_data['name'],
            'list_price': product_data['price'],
            'type': 'consu',
        })
        print(f"Created retail product: {product.name}")
    else:
        print(f"Retail product exists: {product.name}")
    retail_products.append(product)

# Create invoices for each portal user
invoice_obj = env['account.move']
for i, user in enumerate(portal_users):
    partner = user.partner_id
    print(f"\\nProcessing {partner.name}...")

    # Check if invoice exists
    existing_invoice = invoice_obj.search([
        ('partner_id', '=', partner.id),
        ('move_type', '=', 'out_invoice')
    ], limit=1)

    if not existing_invoice:
        # Select product
        product = membership_products[i % len(membership_products)]

        # Create invoice
        invoice = invoice_obj.create({
            'partner_id': partner.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'quantity': 1,
                'price_unit': product.list_price,
            })]
        })
        print(f"  Created invoice {invoice.name} for ${invoice.amount_total}")

        # Try to post
        try:
            invoice.action_post()
            print(f"  Posted invoice {invoice.name}")
        except Exception as e:
            print(f"  Note: Could not post invoice: {str(e)[:100]}")
    else:
        print(f"  Invoice exists: {existing_invoice.name}")

# Create sale orders for first 2 users
sale_obj = env['sale.order']
for user in portal_users[:2]:
    partner = user.partner_id
    print(f"\\nCreating sale order for {partner.name}...")

    existing_order = sale_obj.search([('partner_id', '=', partner.id)], limit=1)

    if not existing_order:
        order = sale_obj.create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': retail_products[0].id,
                    'name': retail_products[0].name,
                    'product_uom_qty': 2,
                    'price_unit': retail_products[0].list_price,
                }),
                (0, 0, {
                    'product_id': retail_products[1].id,
                    'name': retail_products[1].name,
                    'product_uom_qty': 1,
                    'price_unit': retail_products[1].list_price,
                })
            ]
        })
        print(f"  Created order {order.name} for ${order.amount_total}")

        try:
            order.action_confirm()
            print(f"  Confirmed order {order.name}")
        except Exception as e:
            print(f"  Note: Could not confirm order: {str(e)[:100]}")
    else:
        print(f"  Order exists: {existing_order.name}")

env.cr.commit()

print(f"\\n{'='*70}")
print("TEST DATA CREATED SUCCESSFULLY")
print(f"{'='*70}")
print("Portal users can now:")
print("  - View their invoices")
print("  - View their sale orders")
print("  - Access their account information")
print("  - Update contact details")
"""

# Execute via docker
cmd = [
    'docker', 'exec', '-i', 'gms_odoo',
    'odoo', 'shell', '-d', 'gms_validation', '--no-http'
]

try:
    result = subprocess.run(cmd, input=script, text=True, capture_output=True, timeout=90)
    print(result.stdout)
    if result.stderr:
        # Only print warning/error lines from stderr
        for line in result.stderr.split('\n'):
            if 'ERROR' in line or 'CRITICAL' in line or 'Traceback' in line:
                print("STDERR:", line, file=sys.stderr)
    sys.exit(result.returncode)
except subprocess.TimeoutExpired:
    print("ERROR: Command timed out")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
