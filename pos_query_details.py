#!/usr/bin/env python3
"""
Query POS transaction details for report generation
"""

print("\n" + "=" * 80)
print("POS TRANSACTION DETAILS")
print("=" * 80)

# Get the latest POS session
sessions = env['pos.session'].search([('config_id.name', '=', 'My Company')], order='id desc', limit=3)

for session in sessions:
    print(f"\n{'='*80}")
    print(f"Session: {session.name}")
    print(f"State: {session.state}")
    print(f"Start: {session.start_at}")
    print(f"Stop: {session.stop_at}")
    print(f"{'='*80}")

    # Get orders for this session
    orders = env['pos.order'].search([('session_id', '=', session.id)], order='id asc')

    print(f"\nOrders in session: {len(orders)}")

    for order in orders:
        print(f"\n  Order: {order.name}")
        print(f"  Date: {order.date_order}")
        print(f"  State: {order.state}")
        print(f"  Partner: {order.partner_id.name if order.partner_id else 'Walk-in Customer'}")
        print(f"  Currency: {order.currency_id.name}")
        print(f"\n  Line Items:")

        for line in order.lines:
            print(f"    - {line.full_product_name}")
            print(f"      Qty: {line.qty}")
            print(f"      Unit Price: {line.price_unit:.2f} {order.currency_id.name}")
            print(f"      Subtotal: {line.price_subtotal:.2f} {order.currency_id.name}")
            print(f"      Subtotal Incl: {line.price_subtotal_incl:.2f} {order.currency_id.name}")
            if line.tax_ids:
                print(f"      Taxes: {', '.join([t.name for t in line.tax_ids])}")

        print(f"\n  Financial Summary:")
        print(f"    Subtotal (excl tax): {order.amount_total - order.amount_tax:.2f} {order.currency_id.name}")
        print(f"    Tax Amount: {order.amount_tax:.2f} {order.currency_id.name}")
        print(f"    Total: {order.amount_total:.2f} {order.currency_id.name}")

        print(f"\n  Payments:")
        for payment in order.payment_ids:
            print(f"    - {payment.payment_method_id.name}: {payment.amount:.2f} {order.currency_id.name}")

        print(f"    Total Paid: {sum([p.amount for p in order.payment_ids]):.2f} {order.currency_id.name}")

# Get product statistics
print("\n" + "=" * 80)
print("GYM PRODUCT STATISTICS")
print("=" * 80)

gym_categories = env['product.category'].search([('name', 'ilike', 'gym')])
print(f"\nGym Categories found: {len(gym_categories)}")

for cat in gym_categories:
    products = env['product.product'].search([
        ('categ_id', '=', cat.id),
        ('available_in_pos', '=', True)
    ])
    print(f"\n  {cat.name}: {len(products)} products")

    # Sample products
    for prod in products[:5]:
        print(f"    - {prod.name} @ {prod.list_price:.0f} CRC")
        if prod.taxes_id:
            print(f"      Taxes: {', '.join([f'{t.name} ({t.amount}%)' for t in prod.taxes_id])}")

# Tax verification
print("\n" + "=" * 80)
print("TAX CONFIGURATION VERIFICATION")
print("=" * 80)

iva_taxes = env['account.tax'].search([('name', 'ilike', 'iva')])
print(f"\nIVA Taxes configured: {len(iva_taxes)}")

for tax in iva_taxes:
    print(f"\n  {tax.name}")
    print(f"    Amount: {tax.amount}%")
    print(f"    Type: {tax.type_tax_use}")
    print(f"    Active: {tax.active}")

    # Count products using this tax
    products_with_tax = env['product.template'].search([('taxes_id', 'in', [tax.id])])
    print(f"    Products using this tax: {len(products_with_tax)}")

print("\n" + "=" * 80)
print("END OF REPORT DATA")
print("=" * 80)
