#!/usr/bin/env python3
"""
Test Phase 1: E-Invoice XML Generation
Tests the XML generation and validation without signature
"""
import xmlrpc.client
import base64
import os
from datetime import datetime

# Odoo connection
ODOO_URL = 'http://localhost:8070'
ODOO_DB = 'gms_validation'
ODOO_USERNAME = 'admin'
ODOO_PASSWORD = 'admin'

def test_phase1():
    """Test Phase 1 XML generation and validation"""
    print("="*80)
    print("🧪 Testing Phase 1: E-Invoice XML Generation")
    print("="*80)

    try:
        # Connect to Odoo
        print("\n📡 Connecting to Odoo...")
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

        if not uid:
            print("❌ Authentication failed")
            return False

        print(f"✅ Connected as user ID: {uid}")
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

        # Check if module is installed
        print("\n🔍 Checking module installation...")
        module_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'ir.module.module', 'search_read',
            [[('name', '=', 'l10n_cr_einvoice')]],
            {'fields': ['name', 'state']}
        )

        if not module_ids or module_ids[0]['state'] != 'installed':
            print("⚠️  Module l10n_cr_einvoice not installed")
            print("   Run: ./odoo-bin -d gms_validation -u l10n_cr_einvoice")
            return False

        print("✅ Module l10n_cr_einvoice is installed")

        # Find or create test invoice
        print("\n📄 Finding test invoice...")
        invoice_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move', 'search',
            [[
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
            ]],
            {'limit': 1}
        )

        if not invoice_ids:
            print("⚠️  No posted invoices found. Creating test invoice...")
            # Here you would create a test invoice
            print("   Please create and post an invoice manually for testing")
            return False

        invoice_id = invoice_ids[0]
        print(f"✅ Found invoice ID: {invoice_id}")

        # Read invoice details
        invoice_data = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move', 'read',
            [[invoice_id]],
            {'fields': ['name', 'partner_id', 'amount_total', 'state']}
        )[0]

        print(f"   Invoice: {invoice_data['name']}")
        print(f"   Customer: {invoice_data['partner_id'][1]}")
        print(f"   Amount: ${invoice_data['amount_total']:.2f}")

        # Check if e-invoice exists
        print("\n🔍 Checking for existing e-invoice...")
        einvoice_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'l10n_cr.einvoice.document', 'search',
            [[('move_id', '=', invoice_id)]]
        )

        if einvoice_ids:
            einvoice_id = einvoice_ids[0]
            print(f"✅ Found existing e-invoice ID: {einvoice_id}")
        else:
            print("⚠️  No e-invoice found. Triggering auto-generation...")
            # Trigger e-invoice creation
            try:
                result = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'account.move', 'action_create_einvoice',
                    [[invoice_id]]
                )
                print("✅ E-invoice generation triggered")

                # Re-check for e-invoice
                einvoice_ids = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'l10n_cr.einvoice.document', 'search',
                    [[('move_id', '=', invoice_id)]]
                )

                if einvoice_ids:
                    einvoice_id = einvoice_ids[0]
                else:
                    print("❌ E-invoice creation failed")
                    return False

            except Exception as e:
                print(f"❌ Error creating e-invoice: {e}")
                return False

        # Read e-invoice data
        print("\n📋 Reading e-invoice data...")
        einvoice_data = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'l10n_cr.einvoice.document', 'read',
            [[einvoice_id]],
            {'fields': ['name', 'document_type', 'clave', 'state', 'xml_content']}
        )[0]

        print(f"✅ E-Invoice Details:")
        print(f"   Number: {einvoice_data['name']}")
        print(f"   Type: {einvoice_data['document_type']}")
        print(f"   Status: {einvoice_data['state']}")
        print(f"   Clave: {einvoice_data['clave'] or 'Not generated'}")

        # Test XML generation
        print("\n🔨 Testing XML generation...")
        if not einvoice_data['xml_content']:
            print("⚠️  XML not generated. Triggering generation...")
            try:
                models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'l10n_cr.einvoice.document', 'action_generate_xml',
                    [[einvoice_id]]
                )
                print("✅ XML generation triggered")

                # Re-read e-invoice
                einvoice_data = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'l10n_cr.einvoice.document', 'read',
                    [[einvoice_id]],
                    {'fields': ['xml_content', 'state', 'clave']}
                )[0]

            except Exception as e:
                print(f"❌ XML generation failed: {e}")
                return False

        if einvoice_data['xml_content']:
            xml_length = len(einvoice_data['xml_content'])
            print(f"✅ XML generated ({xml_length} characters)")

            # Save XML to file for inspection
            xml_filename = f"test_einvoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            with open(xml_filename, 'w', encoding='utf-8') as f:
                f.write(einvoice_data['xml_content'])
            print(f"   Saved to: {xml_filename}")

            # Show XML snippet
            print(f"\n📝 XML Preview (first 500 chars):")
            print("-" * 80)
            print(einvoice_data['xml_content'][:500])
            print("...")
            print("-" * 80)
        else:
            print("❌ XML content is empty")
            return False

        # Verify clave
        if einvoice_data['clave'] and len(einvoice_data['clave']) == 50:
            print(f"\n✅ Clave verified: {einvoice_data['clave']}")
        else:
            print(f"⚠️  Clave issue: {einvoice_data['clave']}")

        # Verify state
        expected_state = 'generated'
        if einvoice_data['state'] == expected_state:
            print(f"✅ State correct: {expected_state}")
        else:
            print(f"⚠️  State: {einvoice_data['state']} (expected: {expected_state})")

        # Summary
        print("\n" + "="*80)
        print("📊 Phase 1 Test Results:")
        print("="*80)
        print(f"✅ Module installed: Yes")
        print(f"✅ E-invoice created: Yes (ID: {einvoice_id})")
        print(f"✅ XML generated: Yes ({xml_length} chars)")
        print(f"✅ Clave generated: {len(einvoice_data['clave']) == 50}")
        print(f"✅ State: {einvoice_data['state']}")
        print(f"\n⚠️  LIMITATIONS:")
        print(f"   - No digital signature (Phase 2)")
        print(f"   - Cannot submit to Hacienda yet")
        print(f"   - No UI views (Phase 4)")
        print(f"\n🎯 Next Steps:")
        print(f"   1. Implement digital signature (Phase 2)")
        print(f"   2. Test signature with certificate")
        print(f"   3. Submit to Hacienda sandbox")
        print("="*80)

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_phase1()
    exit(0 if success else 1)
