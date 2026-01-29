#!/usr/bin/env python3
import xmlrpc.client

URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

# Get subscription_rule_ids field details
fields_info = models.execute_kw(
    DB, uid, PASSWORD,
    'product.template', 'fields_get',
    ['subscription_rule_ids'],
    {'attributes': ['string', 'type', 'relation']}
)

print("=== subscription_rule_ids field ===")
for key, value in fields_info['subscription_rule_ids'].items():
    print(f"  {key}: {value}")

# If it's a relational field, get fields of that model
if 'relation' in fields_info['subscription_rule_ids']:
    relation_model = fields_info['subscription_rule_ids']['relation']
    print(f"\n=== {relation_model} fields ===\n")
    
    rule_fields = models.execute_kw(
        DB, uid, PASSWORD,
        relation_model, 'fields_get',
        [],
        {'attributes': ['string', 'type', 'required']}
    )
    
    for field_name in sorted(rule_fields.keys()):
        field_type = rule_fields[field_name].get('type', 'unknown')
        field_string = rule_fields[field_name].get('string', '')
        required = " (REQUIRED)" if rule_fields[field_name].get('required') else ""
        print(f"  {field_name:30} | {field_type:15} | {field_string}{required}")
