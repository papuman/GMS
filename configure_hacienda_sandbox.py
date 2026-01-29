#!/usr/bin/env python3
"""
Configure Hacienda Sandbox Environment
Configures the GMS Odoo instance with Hacienda sandbox credentials and certificate
"""
import xmlrpc.client
import base64
import os

# Odoo connection details
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'gms_validation'
ODOO_USERNAME = 'admin'
ODOO_PASSWORD = 'admin'

# Hacienda sandbox credentials
HACIENDA_USERNAME = 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr'
HACIENDA_PASSWORD = 'e8KLJRHzRA1P0W2ybJ5T'
CERTIFICATE_PIN = '5147'
CERTIFICATE_PATH = 'docs/Tribu-CR/certificado.p12'

def configure_sandbox():
    """Configure Hacienda sandbox environment in Odoo"""
    print("🚀 Configuring Hacienda Sandbox Environment...")

    try:
        # Connect to Odoo
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

        if not uid:
            print("❌ Authentication failed. Check Odoo credentials.")
            return False

        print(f"✅ Connected to Odoo as user ID: {uid}")

        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

        # Get company
        company_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.company', 'search',
            [[('name', '=', 'Tribu Fitness & Wellness')]]
        )

        if not company_ids:
            print("❌ Company 'Tribu Fitness & Wellness' not found")
            return False

        company_id = company_ids[0]
        print(f"✅ Found company ID: {company_id}")

        # Read certificate file
        if os.path.exists(CERTIFICATE_PATH):
            with open(CERTIFICATE_PATH, 'rb') as f:
                cert_data = base64.b64encode(f.read()).decode('utf-8')
            print(f"✅ Read certificate from {CERTIFICATE_PATH}")
        else:
            print(f"⚠️  Certificate not found at {CERTIFICATE_PATH}")
            cert_data = False

        # Update company configuration
        update_values = {
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_hacienda_username': HACIENDA_USERNAME,
            'l10n_cr_hacienda_password': HACIENDA_PASSWORD,
            'l10n_cr_key_password': CERTIFICATE_PIN,
            'l10n_cr_auto_generate_einvoice': True,
            'l10n_cr_auto_submit_einvoice': False,  # Manual submission for testing
            'l10n_cr_auto_send_email': False,  # Disable email for testing
            'l10n_cr_emisor_location': '01010100',  # San José default
        }

        if cert_data:
            update_values.update({
                'l10n_cr_certificate': cert_data,
                'l10n_cr_certificate_filename': 'certificado.p12',
            })

        models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.company', 'write',
            [[company_id], update_values]
        )

        print("✅ Company configuration updated:")
        print(f"   - Environment: Sandbox")
        print(f"   - API Username: {HACIENDA_USERNAME}")
        print(f"   - Auto-generate E-Invoice: Yes")
        print(f"   - Auto-submit: No (manual testing)")
        print(f"   - Certificate: {'Loaded' if cert_data else 'Not loaded'}")

        # Verify configuration
        company_data = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.company', 'read',
            [[company_id]],
            {'fields': ['name', 'l10n_cr_hacienda_env', 'l10n_cr_hacienda_username']}
        )

        print(f"\n✅ Verification:")
        print(f"   Company: {company_data[0]['name']}")
        print(f"   Environment: {company_data[0]['l10n_cr_hacienda_env']}")
        print(f"   Username: {company_data[0]['l10n_cr_hacienda_username']}")

        print("\n🎉 Hacienda sandbox configuration complete!")
        print("\n📋 Next steps:")
        print("   1. Install l10n_cr_einvoice module")
        print("   2. Create a test invoice")
        print("   3. Post the invoice to generate e-invoice")
        print("   4. Implement digital signature (Phase 2)")
        print("   5. Submit to Hacienda sandbox")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    configure_sandbox()
