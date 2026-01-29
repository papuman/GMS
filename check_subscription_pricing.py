#!/usr/bin/env python3
import xmlrpc.client

URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

# Check subscription pricing fields
print("=== Subscription Pricing Fields ===\n")
fields_info = models.execute_kw(
    DB, uid, PASSWORD,
    'sale.subscription.pricing', 'fields_get',
    [],
    {'attributes': ['string', 'type', 'required']}
)

for field_name in sorted(fields_info.keys()):
    field_type = fields_info[field_name].get('type', 'unknown')
    field_string = fields_info[field_name].get('string', '')
    required = " (REQUIRED)" if fields_info[field_name].get('required') else ""
    print(f"  {field_name:30} | {field_type:15} | {field_string}{required}")

# Check if we can get existing pricing rules
print("\n=== Existing Pricing Rules ===\n")
pricing_rules = models.execute_kw(
    DB, uid, PASSWORD,
    'sale.subscription.pricing', 'search_read',
    [[]],
    {'fields': ['product_template_id', 'plan_id', 'price'], 'limit': 10}
)

for rule in pricing_rules:
    print(f"  Product Template ID: {rule.get('product_template_id')}, Plan ID: {rule.get('plan_id')}, Price: {rule.get('price')}")
