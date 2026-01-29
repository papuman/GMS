#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configure Hacienda Sandbox Credentials for Phase 3 Testing

This script configures the sandbox API credentials needed for Phase 3 testing.
"""

import xmlrpc.client
import base64
import os

# Configuration (matching test_phase3_api.py)
ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

# Hacienda sandbox credentials (from docs/Tribu-CR/Credentials.md)
HACIENDA_USERNAME = 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr'
HACIENDA_PASSWORD = 'e8KLJRHzRA1P0W2ybJ5T'
CERTIFICATE_PIN = '5147'
CERTIFICATE_PATH = 'docs/Tribu-CR/certificado.p12'


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_result(success, message):
    """Print a result with status indicator."""
    status = "✅" if success else "❌"
    print(f"{status} {message}")


def main():
    """Configure Hacienda sandbox credentials."""

    print_header("Configure Hacienda Sandbox Credentials for Phase 3")

    # Connect to Odoo
    print("Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    # Authenticate
    print(f"Authenticating as {USERNAME}...")
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})

    if not uid:
        print_result(False, "Authentication failed!")
        return False

    print_result(True, f"Authenticated successfully (UID: {uid})")

    # Get company
    print("\nSearching for company...")
    company_ids = models.execute_kw(
        DB, uid, PASSWORD,
        'res.company', 'search',
        [[]]
    )

    if not company_ids:
        print_result(False, "No company found")
        return False

    company_id = company_ids[0]

    # Get company details
    company = models.execute_kw(
        DB, uid, PASSWORD,
        'res.company', 'read',
        [company_id],
        {'fields': ['name', 'l10n_cr_hacienda_env', 'l10n_cr_hacienda_username']}
    )[0]

    print_result(True, f"Found company: {company['name']} (ID: {company_id})")

    # Read certificate file
    cert_data = False
    cert_path = f"/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/{CERTIFICATE_PATH}"
    if os.path.exists(cert_path):
        with open(cert_path, 'rb') as f:
            cert_data = base64.b64encode(f.read()).decode('utf-8')
        print_result(True, f"Read certificate from {CERTIFICATE_PATH}")
    else:
        print_result(False, f"Certificate not found at {cert_path}")

    # Update company configuration
    print("\nConfiguring Hacienda API settings...")

    update_values = {
        'l10n_cr_hacienda_env': 'sandbox',
        'l10n_cr_hacienda_username': HACIENDA_USERNAME,
        'l10n_cr_hacienda_password': HACIENDA_PASSWORD,
        'l10n_cr_key_password': CERTIFICATE_PIN,
    }

    if cert_data:
        update_values['l10n_cr_certificate'] = cert_data
        update_values['l10n_cr_certificate_filename'] = 'certificado.p12'

    try:
        models.execute_kw(
            DB, uid, PASSWORD,
            'res.company', 'write',
            [[company_id], update_values]
        )

        print_result(True, "Company configuration updated")

        # Verify configuration
        company_updated = models.execute_kw(
            DB, uid, PASSWORD,
            'res.company', 'read',
            [company_id],
            {'fields': ['name', 'l10n_cr_hacienda_env', 'l10n_cr_hacienda_username']}
        )[0]

        print("\nConfiguration Summary:")
        print(f"  Company: {company_updated['name']}")
        print(f"  Environment: {company_updated['l10n_cr_hacienda_env']}")
        print(f"  API Username: {company_updated['l10n_cr_hacienda_username']}")
        print(f"  Certificate: {'Configured' if cert_data else 'Not configured'}")

        print("\n" + "=" * 80)
        print_result(True, "Phase 3 credentials configured successfully!")
        print("=" * 80)

        print("\nNext step: Run test_phase3_api.py to test API integration")

        return True

    except Exception as e:
        print_result(False, f"Error updating company: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    main()
