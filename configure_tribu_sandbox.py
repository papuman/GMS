#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configure Tribu-CR Sandbox Credentials in Odoo GMS

This script configures your Odoo company with Tribu-CR sandbox credentials
for electronic invoicing development and testing.

Usage:
    python3 configure_tribu_sandbox.py

Requirements:
    - Odoo instance running on localhost:8070
    - Database: gms_validation
    - User: admin / admin
    - Certificate file: docs/Tribu-CR/certificado.p12
"""

import xmlrpc.client
import base64
import os

# Configuration
ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

# Tribu-CR Sandbox Credentials
HACIENDA_USERNAME = 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr'
HACIENDA_PASSWORD = 'e8KLJRHzRA1P0W2ybJ5T'
HACIENDA_ENV = 'sandbox'  # or 'production'

# Certificate
CERT_PATH = '/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs/Tribu-CR/certificado.p12'
CERT_PIN = '5147'  # Certificate PIN from Tribu-CR

# Company Location Code (San José - Escazú)
# Format: Provincia-Canton-Distrito-Barrio
EMISOR_LOCATION = '01051001'  # San José, Escazú, Escazú, Escazú


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def main():
    """Configure Tribu-CR credentials in Odoo."""

    print_header("Tribu-CR Sandbox Configuration for GMS")

    # Connect to Odoo
    print("Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')

    # Authenticate
    print(f"Authenticating as {USERNAME}...")
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})

    if not uid:
        print("❌ Authentication failed!")
        return

    print(f"✅ Authenticated successfully (UID: {uid})")

    # Get models proxy
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    # Get main company
    print("\nFetching main company...")
    company_ids = models.execute_kw(
        DB, uid, PASSWORD,
        'res.company', 'search',
        [[('name', '=', 'GMS')]]
    )

    if not company_ids:
        print("⚠️  Company 'GMS' not found, using first company...")
        company_ids = models.execute_kw(
            DB, uid, PASSWORD,
            'res.company', 'search',
            [[]], {'limit': 1}
        )

    company_id = company_ids[0]

    company = models.execute_kw(
        DB, uid, PASSWORD,
        'res.company', 'read',
        [company_id], {'fields': ['name']}
    )[0]

    print(f"✅ Company found: {company['name']} (ID: {company_id})")

    # Read certificate file
    print("\nReading certificate file...")

    if not os.path.exists(CERT_PATH):
        print(f"❌ Certificate file not found: {CERT_PATH}")
        print("Please ensure certificado.p12 exists in docs/Tribu-CR/")
        return

    with open(CERT_PATH, 'rb') as f:
        cert_data = base64.b64encode(f.read()).decode('utf-8')

    cert_size = os.path.getsize(CERT_PATH)
    print(f"✅ Certificate loaded ({cert_size} bytes)")

    # Check if certificate PIN is set
    if not CERT_PIN:
        print("\n⚠️  WARNING: Certificate PIN not set!")
        print("Please edit this script and add your certificate PIN to CERT_PIN variable")
        print("Continuing without PIN (you can add it later)...")

    # Update company configuration
    print("\nConfiguring Tribu-CR credentials...")

    update_vals = {
        # API Credentials
        'l10n_cr_hacienda_env': HACIENDA_ENV,
        'l10n_cr_hacienda_username': HACIENDA_USERNAME,
        'l10n_cr_hacienda_password': HACIENDA_PASSWORD,

        # Certificate
        'l10n_cr_certificate': cert_data,
        'l10n_cr_certificate_filename': 'certificado.p12',

        # Location
        'l10n_cr_emisor_location': EMISOR_LOCATION,

        # Automation (disabled for testing)
        'l10n_cr_auto_generate_einvoice': False,  # Manual for testing
        'l10n_cr_auto_submit_einvoice': False,
        'l10n_cr_auto_send_email': False,
    }

    # Add certificate PIN if provided
    if CERT_PIN:
        update_vals['l10n_cr_key_password'] = CERT_PIN

    try:
        models.execute_kw(
            DB, uid, PASSWORD,
            'res.company', 'write',
            [[company_id], update_vals]
        )

        print("✅ Configuration updated successfully!")

    except Exception as e:
        print(f"❌ Error updating configuration: {str(e)}")
        return

    # Summary
    print_header("Configuration Summary")

    print(f"Company ID:            {company_id}")
    print(f"Company Name:          {company['name']}")
    print(f"\nHacienda Configuration:")
    print(f"  Environment:         {HACIENDA_ENV}")
    print(f"  Username:            {HACIENDA_USERNAME}")
    print(f"  Password:            {'*' * len(HACIENDA_PASSWORD)}")
    print(f"  Certificate:         ✅ Uploaded")
    print(f"  Certificate PIN:     {'✅ Set' if CERT_PIN else '⚠️  Not set (add later)'}")
    print(f"  Location Code:       {EMISOR_LOCATION}")
    print(f"\nAutomation:")
    print(f"  Auto-generate:       Disabled (manual for testing)")
    print(f"  Auto-submit:         Disabled")
    print(f"  Auto-email:          Disabled")

    print_header("Next Steps")

    print("1. ✅ Credentials configured")
    print("2. 📝 Add certificate PIN if not set:")
    print("   - Edit this script, set CERT_PIN = 'your-pin'")
    print("   - Run script again")
    print("3. 🧪 Test the configuration:")
    print("   - Create a test invoice in Odoo")
    print("   - Generate e-invoice")
    print("   - Check XML generation")
    print("4. 🚀 Ready to develop Phase 2 (Digital Signature)")

    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()
