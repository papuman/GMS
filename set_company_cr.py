#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Set Company Country to Costa Rica

This script updates the company to be located in Costa Rica,
which is required for electronic invoicing.
"""

import xmlrpc.client

# Configuration
ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'


def main():
    """Set company country to Costa Rica."""

    print("Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    # Authenticate
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        print("❌ Authentication failed!")
        return

    print(f"✅ Authenticated (UID: {uid})")

    # Get Costa Rica country
    cr_ids = models.execute_kw(
        DB, uid, PASSWORD,
        'res.country', 'search',
        [[('code', '=', 'CR')]]
    )

    if not cr_ids:
        print("❌ Costa Rica country not found!")
        return

    cr_id = cr_ids[0]
    print(f"✅ Found Costa Rica (ID: {cr_id})")

    # Get main company
    company_ids = models.execute_kw(
        DB, uid, PASSWORD,
        'res.company', 'search',
        [[]], {'limit': 1}
    )

    company_id = company_ids[0]

    # Update company
    models.execute_kw(
        DB, uid, PASSWORD,
        'res.company', 'write',
        [[company_id], {
            'country_id': cr_id,
            'vat': '3101234567',  # Example Cédula Jurídica
            'name': 'GMS Gym',
        }]
    )

    print(f"✅ Company updated to Costa Rica")

    # Verify
    company = models.execute_kw(
        DB, uid, PASSWORD,
        'res.company', 'read',
        [company_id],
        {'fields': ['name', 'country_id', 'vat']}
    )[0]

    print(f"\nCompany Details:")
    print(f"  Name:     {company['name']}")
    print(f"  Country:  {company['country_id'][1]}")
    print(f"  VAT:      {company['vat']}")
    print("\n✅ Ready for electronic invoicing!")


if __name__ == '__main__':
    main()
