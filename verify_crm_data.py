#!/usr/bin/env python3
"""Verify CRM test data"""

print("\n=== CRM Leads/Opportunities ===")
leads = env['crm.lead'].search([('id', '>=', 4)], order='id')
for lead in leads:
    print(f"ID: {lead.id} | {lead.name}")
    print(f"  Type: {lead.type}")
    print(f"  Contact: {lead.contact_name}")
    print(f"  Email: {lead.email_from}")
    print(f"  Source: {lead.source_id.name if lead.source_id else 'N/A'}")
    print(f"  Stage: {lead.stage_id.name}")
    print(f"  Partner: {lead.partner_id.name if lead.partner_id else 'N/A'}")
    print(f"  Revenue: ${lead.expected_revenue}")
    print()

print("\n=== Sale Orders ===")
orders = env['sale.order'].search([('id', '>=', 10)], order='id')
for order in orders:
    print(f"ID: {order.id} | {order.name}")
    print(f"  Customer: {order.partner_id.name}")
    print(f"  Opportunity: {order.opportunity_id.name if order.opportunity_id else 'N/A'}")
    print(f"  State: {order.state}")
    print(f"  Total: ${order.amount_total}")
    print(f"  Lines: {len(order.order_line)}")
    for line in order.order_line:
        print(f"    - {line.name} | Qty: {line.product_uom_qty} | Price: ${line.price_unit}")
    print()

print("\n=== Products Created ===")
products = env['product.product'].search([('name', 'ilike', '% - Test')])
for product in products:
    print(f"ID: {product.id} | {product.name} | ${product.list_price}")

print("\n=== Lead Sources (Gym-specific) ===")
sources = env['utm.source'].search([('name', 'in', ['Website', 'Walk-in', 'Phone', 'Referral', 'Social Media', 'Email Campaign'])])
for source in sources:
    count = env['crm.lead'].search_count([('source_id', '=', source.id)])
    print(f"{source.name}: {count} leads")
