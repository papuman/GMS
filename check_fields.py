#!/usr/bin/env python3
"""Check actual field names in Odoo 19"""
import xmlrpc.client

URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

print("\n=== product.product fields ===")
fields = models.execute_kw(
    DB, uid, PASSWORD,
    'ir.model.fields', 'search_read',
    [[['model', '=', 'product.product'], ['name', 'in', ['type', 'detailed_type']]]],
    {'fields': ['name', 'field_description', 'ttype']}
)
for field in fields:
    print(f"Field: {field['name']} - {field['field_description']} ({field['ttype']})")

print("\n=== sale.subscription.plan fields ===")
fields = models.execute_kw(
    DB, uid, PASSWORD,
    'ir.model.fields', 'search_read',
    [[['model', '=', 'sale.subscription.plan']]],
    {'fields': ['name', 'field_description', 'ttype'], 'limit': 20}
)
for field in fields:
    print(f"Field: {field['name']} - {field['field_description']} ({field['ttype']})")
