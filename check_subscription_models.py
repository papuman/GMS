#!/usr/bin/env python3
import xmlrpc.client

URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

# Search for all models with 'subscription' in the name
print("=== Subscription-related Models ===\n")
all_models = models.execute_kw(
    DB, uid, PASSWORD,
    'ir.model', 'search_read',
    [[['model', 'ilike', 'subscription']]],
    {'fields': ['model', 'name']}
)

for model_info in sorted(all_models, key=lambda x: x['model']):
    print(f"  {model_info['model']:40} - {model_info['name']}")

# Check product.template fields related to subscription
print("\n=== product.template subscription-related fields ===\n")
fields_info = models.execute_kw(
    DB, uid, PASSWORD,
    'product.template', 'fields_get',
    [],
    {'attributes': ['string', 'type']}
)

for field_name in sorted(fields_info.keys()):
    if 'recur' in field_name.lower() or 'subscription' in field_name.lower():
        field_type = fields_info[field_name].get('type', 'unknown')
        field_string = fields_info[field_name].get('string', '')
        print(f"  {field_name:30} | {field_type:15} | {field_string}")
