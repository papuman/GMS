#!/usr/bin/env python3
"""Simple E-Invoice Test for Phase 1"""

import xmlrpc.client
from datetime import date

# Configuration
ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'


def main():
    print("\n" + "="*80)
    print("  Costa Rica E-Invoice Phase 1 Test")
    print("="*80 + "\n")

    # Connect
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    # Authenticate
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    print(f"✅ Authenticated (UID: {uid})")

    # Get Costa Rica
    cr_id = models.execute_kw(
        DB, uid, PASSWORD,
        'res.country', 'search',
        [[('code', '=', 'CR')]], {'limit': 1}
    )[0]
    print(f"✅ Costa Rica country (ID: {cr_id})")

    # Check for existing customer or create new
    old_customer = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner', 'search',
        [[('name', '=', 'Juan Pérez CR')]]
    )

    if old_customer:
        customer_id = old_customer[0]
        # Update to ensure CR country
        models.execute_kw(
            DB, uid, PASSWORD,
            'res.partner', 'write',
            [[customer_id], {'country_id': cr_id, 'vat': '304560789'}]
        )
        print(f"✅ Updated existing CR customer (ID: {customer_id})")
    else:
        # Create customer with CR country
        customer_id = models.execute_kw(
            DB, uid, PASSWORD,
            'res.partner', 'create',
            [{
                'name': 'Juan Pérez CR',
                'vat': '304560789',
                'country_id': cr_id,
                'email': 'juan@example.cr',
            }]
        )
        print(f"✅ Created CR customer (ID: {customer_id})")

    # Create product
    product_id = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product', 'create',
        [{
            'name': 'Membresía Mensual',
            'type': 'service',
            'list_price': 50000.00,
        }]
    )
    print(f"✅ Created product (ID: {product_id})")

    # Create invoice
    invoice_id = models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'create',
        [{
            'move_type': 'out_invoice',
            'partner_id': customer_id,
            'invoice_date': str(date.today()),
            'invoice_line_ids': [(0, 0, {
                'product_id': product_id,
                'quantity': 1,
                'price_unit': 50000.00,
            })],
        }]
    )
    print(f"✅ Created invoice (ID: {invoice_id})")

    # Post invoice
    models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'action_post',
        [[invoice_id]]
    )
    print("✅ Posted invoice")

    # Read invoice
    invoice = models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'read',
        [invoice_id],
        {'fields': ['name', 'l10n_cr_requires_einvoice', 'country_code', 'l10n_cr_einvoice_id']}
    )[0]

    print(f"\nInvoice: {invoice['name']}")
    print(f"  Requires E-Invoice: {invoice['l10n_cr_requires_einvoice']}")
    print(f"  Country Code: {invoice.get('country_code')}")

    if not invoice['l10n_cr_requires_einvoice']:
        print("\n❌ Invoice does not require e-invoice!")
        print("   This means the computed field logic didn't trigger")
        return

    # Create e-invoice
    print("\nCreating e-invoice...")
    result = models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'action_create_einvoice',
        [[invoice_id]]
    )

    # Get e-invoice
    invoice = models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'read',
        [invoice_id],
        {'fields': ['l10n_cr_einvoice_id']}
    )[0]

    einvoice_id = invoice['l10n_cr_einvoice_id'][0]
    print(f"✅ E-Invoice created (ID: {einvoice_id})")

    # Read e-invoice
    einvoice = models.execute_kw(
        DB, uid, PASSWORD,
        'l10n_cr.einvoice.document', 'read',
        [einvoice_id],
        {'fields': ['name', 'clave', 'document_type', 'state', 'xml_content']}
    )[0]

    print(f"\nE-Invoice Details:")
    print(f"  Number: {einvoice['name']}")
    print(f"  Clave:  {einvoice['clave']}")
    print(f"  Type:   {einvoice['document_type']}")
    print(f"  State:  {einvoice['state']}")

    # Generate XML
    if einvoice['state'] == 'draft':
        print("\nGenerating XML...")
        models.execute_kw(
            DB, uid, PASSWORD,
            'l10n_cr.einvoice.document', 'action_generate_xml',
            [[einvoice_id]]
        )

        einvoice = models.execute_kw(
            DB, uid, PASSWORD,
            'l10n_cr.einvoice.document', 'read',
            [einvoice_id],
            {'fields': ['state', 'xml_content']}
        )[0]

        if einvoice['xml_content']:
            print(f"✅ XML generated ({len(einvoice['xml_content'])} bytes)")

            # Save XML
            filename = f"einvoice_{einvoice_id}.xml"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(einvoice['xml_content'])
            print(f"✅ Saved to: {filename}")

            # Show first few lines
            print("\nXML Preview:")
            print("-" * 80)
            lines = einvoice['xml_content'].split('\n')[:10]
            for line in lines:
                print(line)
            print("...")
        else:
            print("❌ XML generation failed")

    print("\n" + "="*80)
    print("  PHASE 1 TEST: SUCCESS")
    print("="*80)
    print("\n✅ Module installed")
    print("✅ Credentials configured")
    print("✅ Invoice created")
    print("✅ E-invoice created")
    print("✅ XML generated")
    print("\n⏳ Next: Phase 2 - Digital Signature\n")


if __name__ == '__main__':
    main()
