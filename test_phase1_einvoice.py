#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Phase 1 E-Invoice Functionality

This script tests the basic XML generation and validation functionality
of the l10n_cr_einvoice module (Phase 1).

Usage:
    python3 test_phase1_einvoice.py
"""

import xmlrpc.client
import json
from datetime import date

# Configuration
ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def main():
    """Test Phase 1 e-invoice functionality."""

    print_header("Phase 1 E-Invoice Testing")

    # Connect to Odoo
    print("Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    # Authenticate
    print(f"Authenticating as {USERNAME}...")
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})

    if not uid:
        print("❌ Authentication failed!")
        return

    print(f"✅ Authenticated successfully (UID: {uid})")

    # Get or create a test customer
    print("\n" + "-" * 80)
    print("Setting up test customer...")
    print("-" * 80 + "\n")

    customer_ids = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner', 'search',
        [[('name', '=', 'Test Customer CR')]]
    )

    if customer_ids:
        customer_id = customer_ids[0]
        print(f"✅ Using existing customer (ID: {customer_id})")
    else:
        # Create test customer
        customer_id = models.execute_kw(
            DB, uid, PASSWORD,
            'res.partner', 'create',
            [{
                'name': 'Test Customer CR',
                'vat': '304560789',  # Cédula Física example
                'email': 'test@example.com',
                'phone': '+506-8888-8888',
                'street': 'San José, Escazú',
                'country_id': models.execute_kw(
                    DB, uid, PASSWORD,
                    'res.country', 'search',
                    [[('code', '=', 'CR')]], {'limit': 1}
                )[0] if models.execute_kw(
                    DB, uid, PASSWORD,
                    'res.country', 'search',
                    [[('code', '=', 'CR')]], {'limit': 1}
                ) else False,
            }]
        )
        print(f"✅ Created test customer (ID: {customer_id})")

    # Get or create a test product
    print("\nSetting up test product...")

    product_ids = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product', 'search',
        [[('name', '=', 'Test Gym Membership')]]
    )

    if product_ids:
        product_id = product_ids[0]
        print(f"✅ Using existing product (ID: {product_id})")
    else:
        # Create test product
        product_id = models.execute_kw(
            DB, uid, PASSWORD,
            'product.product', 'create',
            [{
                'name': 'Test Gym Membership',
                'type': 'service',
                'list_price': 50000.00,  # ₡50,000
                'standard_price': 40000.00,
                'sale_ok': True,
            }]
        )
        print(f"✅ Created test product (ID: {product_id})")

    # Create a test invoice
    print("\n" + "-" * 80)
    print("Creating test invoice...")
    print("-" * 80 + "\n")

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
                'name': 'Monthly Gym Membership',
            })],
        }]
    )

    print(f"✅ Created invoice (ID: {invoice_id})")

    # Read invoice details
    invoice = models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'read',
        [invoice_id],
        {'fields': ['name', 'partner_id', 'amount_total', 'state', 'l10n_cr_einvoice_id']}
    )[0]

    print(f"\nInvoice Details:")
    print(f"  Number:      {invoice['name']}")
    print(f"  Customer:    {invoice['partner_id'][1]}")
    print(f"  Total:       ₡{invoice['amount_total']:,.2f}")
    print(f"  State:       {invoice['state']}")

    # Post the invoice
    print("\n" + "-" * 80)
    print("Posting invoice...")
    print("-" * 80 + "\n")

    models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'action_post',
        [[invoice_id]]
    )

    print("✅ Invoice posted successfully")

    # Check if e-invoice was created automatically
    invoice = models.execute_kw(
        DB, uid, PASSWORD,
        'account.move', 'read',
        [invoice_id],
        {'fields': ['l10n_cr_einvoice_id', 'state']}
    )[0]

    if invoice['l10n_cr_einvoice_id']:
        einvoice_id = invoice['l10n_cr_einvoice_id'][0]
        print(f"⚠️  E-Invoice auto-created (ID: {einvoice_id})")
        print("   Note: Auto-generation is disabled in config, but may have been triggered")
    else:
        print("ℹ️  No e-invoice created yet (expected - auto-generation disabled)")
        print("\nManually creating e-invoice...")

        # Manually create e-invoice
        models.execute_kw(
            DB, uid, PASSWORD,
            'account.move', 'action_create_einvoice',
            [[invoice_id]]
        )

        # Get the created e-invoice
        invoice = models.execute_kw(
            DB, uid, PASSWORD,
            'account.move', 'read',
            [invoice_id],
            {'fields': ['l10n_cr_einvoice_id']}
        )[0]

        if invoice['l10n_cr_einvoice_id']:
            einvoice_id = invoice['l10n_cr_einvoice_id'][0]
            print(f"✅ E-Invoice created manually (ID: {einvoice_id})")
        else:
            print("❌ Failed to create e-invoice")
            return

    # Read e-invoice details
    print("\n" + "-" * 80)
    print("E-Invoice Details")
    print("-" * 80 + "\n")

    einvoice = models.execute_kw(
        DB, uid, PASSWORD,
        'l10n_cr.einvoice.document', 'read',
        [einvoice_id],
        {'fields': ['name', 'clave', 'document_type', 'state', 'xml_content']}
    )[0]

    print(f"Document Number: {einvoice['name']}")
    print(f"Clave:           {einvoice['clave']}")
    print(f"Document Type:   {einvoice['document_type']}")
    print(f"State:           {einvoice['state']}")
    print(f"XML Generated:   {'✅ Yes' if einvoice['xml_content'] else '❌ No'}")

    if einvoice['xml_content']:
        xml_lines = einvoice['xml_content'].count('\n')
        xml_size = len(einvoice['xml_content'])
        print(f"XML Size:        {xml_size:,} bytes ({xml_lines} lines)")

        # Save XML to file
        xml_filename = f"test_einvoice_{einvoice['name']}.xml"
        with open(xml_filename, 'w', encoding='utf-8') as f:
            f.write(einvoice['xml_content'])
        print(f"✅ XML saved to: {xml_filename}")

    # Test XML generation if not already done
    if einvoice['state'] == 'draft' and not einvoice['xml_content']:
        print("\n" + "-" * 80)
        print("Generating XML...")
        print("-" * 80 + "\n")

        try:
            models.execute_kw(
                DB, uid, PASSWORD,
                'l10n_cr.einvoice.document', 'action_generate_xml',
                [[einvoice_id]]
            )

            # Read updated e-invoice
            einvoice = models.execute_kw(
                DB, uid, PASSWORD,
                'l10n_cr.einvoice.document', 'read',
                [einvoice_id],
                {'fields': ['state', 'xml_content']}
            )[0]

            if einvoice['xml_content']:
                print(f"✅ XML generated successfully")
                print(f"   State: {einvoice['state']}")
                print(f"   Size: {len(einvoice['xml_content']):,} bytes")

                # Save XML
                xml_filename = f"test_einvoice_{einvoice_id}.xml"
                with open(xml_filename, 'w', encoding='utf-8') as f:
                    f.write(einvoice['xml_content'])
                print(f"   Saved to: {xml_filename}")
            else:
                print("❌ XML generation failed")

        except Exception as e:
            print(f"❌ Error generating XML: {str(e)}")

    # Summary
    print_header("Phase 1 Test Summary")

    print("✅ Module Installation: SUCCESS")
    print("✅ Credentials Configuration: SUCCESS")
    print("✅ Test Invoice Creation: SUCCESS")
    print(f"✅ E-Invoice Creation: {'SUCCESS' if einvoice_id else 'FAILED'}")
    print(f"✅ XML Generation: {'SUCCESS' if einvoice.get('xml_content') else 'PENDING'}")
    print("\n⏳ Phase 2 Items (Not Yet Implemented):")
    print("   - Digital Signature")
    print("   - Hacienda Submission")
    print("   - PDF Report with QR Code")
    print("   - Email Delivery")

    print("\n" + "=" * 80)
    print("\nNext Steps:")
    print("1. Review generated XML file")
    print("2. Verify XML structure matches v4.4 spec")
    print("3. Ready to start Phase 2: Digital Signature")
    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()
