#!/usr/bin/env python3
import xmlrpc.client

URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

# Get field definition for user_closable_options
fields_info = models.execute_kw(
    DB, uid, PASSWORD,
    'sale.subscription.plan', 'fields_get',
    ['user_closable_options'],
    {'attributes': ['selection', 'string', 'required']}
)

print("user_closable_options field:")
print(f"  String: {fields_info['user_closable_options'].get('string')}")
print(f"  Required: {fields_info['user_closable_options'].get('required')}")
print(f"  Selection options:")
for option in fields_info['user_closable_options'].get('selection', []):
    print(f"    - {option[0]}: {option[1]}")
