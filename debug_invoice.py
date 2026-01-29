#!/usr/bin/env python3
"""Debug invoice country code issue"""

import xmlrpc.client

ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'


def main():
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    uid = common.authenticate(DB, USERNAME, PASSWORD, {})

    # Get last invoice
    invoice_id = models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'search',
        [[('move_type', '=', 'out_invoice')]],
        {'order': 'id desc', 'limit': 1}
    )[0]

    # Read invoice and partner details
    invoice = models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'read',
        [invoice_id],
        {'fields': ['name', 'partner_id', 'country_code', 'company_id', 'move_type', 'l10n_cr_requires_einvoice']}
    )[0]

    partner = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner', 'read',
        [invoice['partner_id'][0]],
        {'fields': ['name', 'country_id', 'country_code']}
    )[0]

    company = models.execute_kw(
        DB, uid, PASSWORD,
        'res.company', 'read',
        [invoice['company_id'][0]],
        {'fields': ['name', 'country_id']}
    )[0]

    print(f"\nInvoice ID: {invoice_id}")
    print(f"Invoice Number: {invoice['name']}")
    print(f"Move Type: {invoice['move_type']}")
    print(f"\nPartner: {partner['name']}")
    print(f"  Country: {partner.get('country_id')}")
    print(f"  Country Code: {partner.get('country_code')}")
    print(f"\nCompany: {company['name']}")
    print(f"  Country: {company.get('country_id')}")
    print(f"\nInvoice country_code: {invoice['country_code']}")
    print(f"Requires E-Invoice: {invoice['l10n_cr_requires_einvoice']}")

    # Try to recompute
    print("\nRecomputing l10n_cr_requires_einvoice...")
    models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'write',
        [[invoice_id], {}]  # Empty write to trigger recompute
    )

    # Read again
    invoice2 = models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'read',
        [invoice_id],
        {'fields': ['country_code', 'l10n_cr_requires_einvoice']}
    )[0]

    print(f"\nAfter recompute:")
    print(f"  country_code: {invoice2['country_code']}")
    print(f"  requires_einvoice: {invoice2['l10n_cr_requires_einvoice']}")


if __name__ == '__main__':
    main()
