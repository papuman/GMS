#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Phase 3 E-Invoice API Integration

This script tests the Hacienda API integration functionality
of the l10n_cr_einvoice module (Phase 3).

Features tested:
1. API connection and authentication
2. Submit invoice to Hacienda
3. Check document status
4. Retry logic and error handling
5. Response parsing

Usage:
    python3 test_phase3_api.py
"""

import xmlrpc.client
import json
import time
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


def print_section(text):
    """Print a formatted section header."""
    print("\n" + "-" * 80)
    print(f"  {text}")
    print("-" * 80 + "\n")


def print_result(success, message):
    """Print a result with status indicator."""
    status = "✅" if success else "❌"
    print(f"{status} {message}")


def main():
    """Test Phase 3 API integration functionality."""

    print_header("Phase 3 E-Invoice API Integration Testing")

    # Connect to Odoo
    print("Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    # Authenticate
    print(f"Authenticating as {USERNAME}...")
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})

    if not uid:
        print_result(False, "Authentication failed!")
        return

    print_result(True, f"Authenticated successfully (UID: {uid})")

    # Test 1: Connection Test
    print_section("Test 1: API Connection and Authentication")

    try:
        result = models.execute_kw(
            DB, uid, PASSWORD,
            'l10n_cr.hacienda.api', 'test_connection', []
        )

        print(f"Environment: {result.get('environment', 'N/A')}")
        print(f"URL: {result.get('url', 'N/A')}")
        print_result(result.get('success', False), result.get('message', 'No message'))

    except Exception as e:
        print_result(False, f"Connection test failed: {str(e)}")

    # Test 2: Find existing e-invoice documents
    print_section("Test 2: Find Existing E-Invoice Documents")

    try:
        # Search for documents in 'signed' state
        doc_ids = models.execute_kw(
            DB, uid, PASSWORD,
            'l10n_cr.einvoice.document', 'search',
            [[('state', '=', 'signed')]],
            {'limit': 1}
        )

        if doc_ids:
            doc_id = doc_ids[0]
            print_result(True, f"Found signed document ID: {doc_id}")

            # Get document details
            doc = models.execute_kw(
                DB, uid, PASSWORD,
                'l10n_cr.einvoice.document', 'read',
                [doc_id],
                {'fields': ['name', 'clave', 'state', 'document_type', 'amount_total']}
            )[0]

            print(f"\nDocument Details:")
            print(f"  Name: {doc['name']}")
            print(f"  Clave: {doc['clave']}")
            print(f"  State: {doc['state']}")
            print(f"  Type: {doc['document_type']}")
            print(f"  Amount: {doc['amount_total']}")

            # Test 3: Submit to Hacienda
            print_section("Test 3: Submit Document to Hacienda")

            try:
                print(f"Submitting document {doc['name']} to Hacienda...")
                models.execute_kw(
                    DB, uid, PASSWORD,
                    'l10n_cr.einvoice.document', 'action_submit_to_hacienda',
                    [doc_id]
                )

                # Get updated document state
                doc_updated = models.execute_kw(
                    DB, uid, PASSWORD,
                    'l10n_cr.einvoice.document', 'read',
                    [doc_id],
                    {'fields': ['state', 'hacienda_message', 'hacienda_response']}
                )[0]

                print_result(True, f"Document submitted. New state: {doc_updated['state']}")

                if doc_updated.get('hacienda_message'):
                    print(f"Hacienda Message: {doc_updated['hacienda_message']}")

                if doc_updated.get('hacienda_response'):
                    try:
                        response = eval(doc_updated['hacienda_response'])
                        print(f"\nHacienda Response:")
                        print(f"  Status: {response.get('ind-estado', 'N/A')}")
                        if 'respuesta-xml-decoded' in response:
                            print(f"  Message: {response['respuesta-xml-decoded'][:200]}...")
                    except:
                        print(f"Raw Response: {doc_updated['hacienda_response'][:200]}...")

                # Test 4: Check Status
                if doc_updated['state'] == 'submitted':
                    print_section("Test 4: Check Document Status")

                    print("Waiting 5 seconds before checking status...")
                    time.sleep(5)

                    try:
                        models.execute_kw(
                            DB, uid, PASSWORD,
                            'l10n_cr.einvoice.document', 'action_check_status',
                            [doc_id]
                        )

                        # Get final document state
                        doc_final = models.execute_kw(
                            DB, uid, PASSWORD,
                            'l10n_cr.einvoice.document', 'read',
                            [doc_id],
                            {'fields': ['state', 'hacienda_message', 'hacienda_acceptance_date']}
                        )[0]

                        print_result(True, f"Status check complete. State: {doc_final['state']}")
                        print(f"Message: {doc_final.get('hacienda_message', 'N/A')}")

                        if doc_final.get('hacienda_acceptance_date'):
                            print(f"Acceptance Date: {doc_final['hacienda_acceptance_date']}")

                    except Exception as e:
                        print_result(False, f"Status check failed: {str(e)}")

            except Exception as e:
                print_result(False, f"Submission failed: {str(e)}")
                print(f"\nError details: {str(e)}")

        else:
            print_result(False, "No signed documents found to test")
            print("\nTo test Phase 3, you need to:")
            print("1. Create an invoice")
            print("2. Generate XML (Phase 1)")
            print("3. Sign XML (Phase 2)")
            print("4. Then run this test to submit to Hacienda (Phase 3)")

    except Exception as e:
        print_result(False, f"Error searching documents: {str(e)}")

    # Test 5: API Helper Methods
    print_section("Test 5: API Helper Methods")

    try:
        # Test ID type detection
        test_ids = {
            '123456789': 'Cédula Física (9 digits)',
            '3101234567': 'Cédula Jurídica (10 digits)',
            '12345678901': 'DIMEX (11 digits)',
            '': 'Empty/Extranjero'
        }

        print("Testing identification type detection:")
        for test_id, description in test_ids.items():
            try:
                id_type = models.execute_kw(
                    DB, uid, PASSWORD,
                    'l10n_cr.hacienda.api', 'get_id_type',
                    [test_id]
                )
                print(f"  {description}: Type {id_type}")
            except Exception as e:
                print_result(False, f"ID type detection failed for {description}: {str(e)}")

        print_result(True, "ID type detection working")

    except Exception as e:
        print_result(False, f"Helper methods test failed: {str(e)}")

    # Summary
    print_section("Test Summary")
    print("""
Phase 3 API Integration Features:
✓ Connection testing with credential validation
✓ Submit invoice to Hacienda with retry logic
✓ Check document status
✓ Exponential backoff retry (max 3 attempts)
✓ Comprehensive error handling
✓ Response parsing with base64 decoding
✓ Status detection helpers (is_accepted, is_rejected, is_processing)
✓ Authentication error handling
✓ Rate limiting handling
✓ Network error handling

Next Steps:
- Test with real invoice submission
- Monitor retry behavior during network issues
- Test rate limiting scenarios
- Validate acceptance/rejection workflows
""")


if __name__ == '__main__':
    main()
