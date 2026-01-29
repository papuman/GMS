#!/usr/bin/env python3
"""
Check actual fields in Odoo 19 subscription models
"""
import xmlrpc.client

URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

# Connect
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

print("=== Checking sale.subscription.plan fields ===\n")

try:
    # Get model fields
    fields_info = models.execute_kw(
        DB, uid, PASSWORD,
        'sale.subscription.plan', 'fields_get',
        [],
        {'attributes': ['string', 'type', 'required']}
    )

    print("Available fields in sale.subscription.plan:\n")
    for field_name, field_info in sorted(fields_info.items()):
        field_type = field_info.get('type', 'unknown')
        field_string = field_info.get('string', '')
        required = field_info.get('required', False)
        req_mark = " (REQUIRED)" if required else ""
        print(f"  {field_name:30} | {field_type:15} | {field_string}{req_mark}")

    # Look for period/interval related fields
    print("\n=== Period/Interval related fields ===\n")
    for field_name in fields_info.keys():
        if any(keyword in field_name.lower() for keyword in ['period', 'interval', 'recur', 'billing']):
            print(f"  {field_name}: {fields_info[field_name].get('string', '')}")

except Exception as e:
    print(f"Error: {e}")

print("\n\n=== Checking sale.order available methods ===\n")

try:
    # Try to get available methods (this might not work via XML-RPC)
    # Instead, let's try common invoice-related method names
    method_names = [
        '_create_invoices',
        'create_invoices',
        'action_invoice_create',
        'invoice_create',
        '_create_invoice',
    ]

    print("Testing invoice-related methods:\n")
    for method_name in method_names:
        try:
            # Try to check if method exists by calling fields_view_get which should always exist
            # If we can access the model, we know the connection works
            result = models.execute_kw(
                DB, uid, PASSWORD,
                'sale.order', 'search',
                [[]], {'limit': 1}
            )
            print(f"  {method_name}: (needs actual test order to verify)")
        except Exception as e:
            if 'does not exist' in str(e):
                print(f"  {method_name}: DOES NOT EXIST")
            else:
                print(f"  {method_name}: (error checking: {str(e)[:50]})")

except Exception as e:
    print(f"Error: {e}")
