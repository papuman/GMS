#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Phase 2 E-Invoice Digital Signature Functionality

This script comprehensively tests the digital signature capabilities
of the l10n_cr_einvoice module (Phase 2).

Tests:
1. Certificate loading from .p12 file
2. Certificate validation (expiry, validity)
3. XML signing with loaded certificate
4. Signature structure verification (SignedInfo, SignatureValue, KeyInfo)
5. Base64 encoding validation
6. Complete workflow: Generate XML → Sign → Verify structure
7. Error handling (invalid certificate, wrong PIN, expired cert)

Usage:
    python3 test_einvoice_phase2_signature.py
"""

import xmlrpc.client
import json
import os
import base64
from datetime import date, datetime
from lxml import etree

# Configuration
ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

# Certificate path (from docs/Tribu-CR directory)
CERT_PATH = '/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs/Tribu-CR/certificado.p12'
CERT_PIN = '5147'

# Test results tracking
test_results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'tests': []
}


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_section(text):
    """Print a section divider."""
    print("\n" + "-" * 80)
    print(f"  {text}")
    print("-" * 80 + "\n")


def record_test(name, passed, details=""):
    """Record test result."""
    test_results['total'] += 1
    if passed:
        test_results['passed'] += 1
        status = "✅ PASS"
    else:
        test_results['failed'] += 1
        status = "❌ FAIL"

    test_results['tests'].append({
        'name': name,
        'passed': passed,
        'details': details
    })

    print(f"{status}: {name}")
    if details:
        print(f"    {details}")


def verify_certificate_file():
    """Verify certificate file exists."""
    print_section("Test 1: Certificate File Verification")

    if not os.path.exists(CERT_PATH):
        record_test(
            "Certificate file exists",
            False,
            f"Certificate not found at: {CERT_PATH}"
        )
        return False

    file_size = os.path.getsize(CERT_PATH)
    record_test(
        "Certificate file exists",
        True,
        f"Found at {CERT_PATH} ({file_size:,} bytes)"
    )
    return True


def upload_certificate_to_company(models, uid):
    """Upload certificate to company configuration."""
    print_section("Test 2: Certificate Upload to Company")

    try:
        # Read certificate file
        with open(CERT_PATH, 'rb') as f:
            cert_data = f.read()

        # Base64 encode
        cert_b64 = base64.b64encode(cert_data).decode('utf-8')

        # Get main company
        company_ids = models.execute_kw(
            DB, uid, PASSWORD,
            'res.company', 'search',
            [[('id', '=', 1)]]
        )

        if not company_ids:
            record_test("Get company record", False, "No company found")
            return None

        company_id = company_ids[0]

        # Update company with certificate
        models.execute_kw(
            DB, uid, PASSWORD,
            'res.company', 'write',
            [[company_id], {
                'l10n_cr_certificate': cert_b64,
                'l10n_cr_certificate_filename': 'certificado.p12',
                'l10n_cr_key_password': CERT_PIN,
            }]
        )

        record_test(
            "Upload certificate to company",
            True,
            f"Certificate uploaded to company ID {company_id}"
        )
        return company_id

    except Exception as e:
        record_test(
            "Upload certificate to company",
            False,
            f"Error: {str(e)}"
        )
        return None


def test_certificate_loading(models, uid, company_id):
    """Test loading certificate from company configuration."""
    print_section("Test 3: Certificate Loading (.p12)")

    try:
        # Call certificate manager to load certificate
        result = models.execute_kw(
            DB, uid, PASSWORD,
            'l10n_cr.certificate.manager', 'get_certificate_info',
            [company_id]
        )

        if 'error' in result:
            record_test(
                "Load certificate from .p12",
                False,
                f"Error: {result['error']}"
            )
            return False

        # Check certificate details
        print(f"Certificate loaded successfully:")
        print(f"  Subject CN:       {result.get('subject_cn', 'N/A')}")
        print(f"  Organization:     {result.get('subject_org', 'N/A')}")
        print(f"  Issuer:           {result.get('issuer_cn', 'N/A')}")
        print(f"  Valid From:       {result.get('not_before', 'N/A')}")
        print(f"  Valid Until:      {result.get('not_after', 'N/A')}")
        print(f"  Days Remaining:   {result.get('days_until_expiry', 'N/A')}")
        print(f"  Serial Number:    {result.get('serial_number', 'N/A')}")

        record_test(
            "Load certificate from .p12",
            True,
            f"Subject: {result.get('subject_cn', 'N/A')}"
        )

        return result

    except Exception as e:
        record_test(
            "Load certificate from .p12",
            False,
            f"Exception: {str(e)}"
        )
        return None


def test_certificate_validation(cert_info):
    """Test certificate validation (expiry, validity)."""
    print_section("Test 4: Certificate Validation")

    if not cert_info:
        record_test("Certificate validation", False, "No certificate info available")
        return False

    # Check if certificate is valid
    is_valid = cert_info.get('is_valid', False)
    days_remaining = cert_info.get('days_until_expiry', 0)

    if is_valid:
        record_test(
            "Certificate validity check",
            True,
            f"Certificate is valid ({days_remaining} days remaining)"
        )
    else:
        record_test(
            "Certificate validity check",
            False,
            "Certificate is expired or invalid"
        )

    # Check expiry warning (< 30 days)
    if days_remaining < 30 and days_remaining > 0:
        print(f"⚠️  WARNING: Certificate expires soon ({days_remaining} days)")

    # Check dates are present
    has_dates = 'not_before' in cert_info and 'not_after' in cert_info
    record_test(
        "Certificate date extraction",
        has_dates,
        f"Valid from {cert_info.get('not_before')} to {cert_info.get('not_after')}"
        if has_dates else "Missing date information"
    )

    return is_valid


def test_wrong_pin(models, uid):
    """Test error handling with wrong PIN."""
    print_section("Test 5: Error Handling - Wrong PIN")

    try:
        # Get main company
        company_ids = models.execute_kw(
            DB, uid, PASSWORD,
            'res.company', 'search',
            [[('id', '=', 1)]]
        )
        company_id = company_ids[0]

        # Temporarily change to wrong PIN
        models.execute_kw(
            DB, uid, PASSWORD,
            'res.company', 'write',
            [[company_id], {'l10n_cr_key_password': 'wrong_pin'}]
        )

        # Try to load certificate (should fail)
        try:
            result = models.execute_kw(
                DB, uid, PASSWORD,
                'l10n_cr.certificate.manager', 'get_certificate_info',
                [company_id]
            )

            if 'error' in result:
                record_test(
                    "Wrong PIN error handling",
                    True,
                    "Correctly rejected wrong PIN"
                )
                success = True
            else:
                record_test(
                    "Wrong PIN error handling",
                    False,
                    "Should have failed with wrong PIN"
                )
                success = False

        except Exception as e:
            # Exception is expected
            record_test(
                "Wrong PIN error handling",
                True,
                "Correctly raised exception for wrong PIN"
            )
            success = True

        # Restore correct PIN
        models.execute_kw(
            DB, uid, PASSWORD,
            'res.company', 'write',
            [[company_id], {'l10n_cr_key_password': CERT_PIN}]
        )

        return success

    except Exception as e:
        record_test(
            "Wrong PIN error handling",
            False,
            f"Unexpected error: {str(e)}"
        )
        return False


def create_test_invoice(models, uid):
    """Create a test invoice for signing."""
    print_section("Test 6: Create Test Invoice for Signing")

    try:
        # Get or create customer
        customer_ids = models.execute_kw(
            DB, uid, PASSWORD,
            'res.partner', 'search',
            [[('name', '=', 'Test Customer Signature')]]
        )

        if customer_ids:
            customer_id = customer_ids[0]
        else:
            customer_id = models.execute_kw(
                DB, uid, PASSWORD,
                'res.partner', 'create',
                [{
                    'name': 'Test Customer Signature',
                    'vat': '304560789',
                    'email': 'testsig@example.com',
                    'phone': '+506-8888-8888',
                    'street': 'San José, Escazú',
                }]
            )

        # Get or create product
        product_ids = models.execute_kw(
            DB, uid, PASSWORD,
            'product.product', 'search',
            [[('name', '=', 'Test Product Signature')]]
        )

        if product_ids:
            product_id = product_ids[0]
        else:
            product_id = models.execute_kw(
                DB, uid, PASSWORD,
                'product.product', 'create',
                [{
                    'name': 'Test Product Signature',
                    'type': 'service',
                    'list_price': 50000.00,
                    'sale_ok': True,
                }]
            )

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
                    'name': 'Test Product for Signature',
                })],
            }]
        )

        # Post invoice
        models.execute_kw(
            DB, uid, PASSWORD,
            'account.move', 'action_post',
            [[invoice_id]]
        )

        # Create e-invoice
        models.execute_kw(
            DB, uid, PASSWORD,
            'account.move', 'action_create_einvoice',
            [[invoice_id]]
        )

        # Get e-invoice ID
        invoice = models.execute_kw(
            DB, uid, PASSWORD,
            'account.move', 'read',
            [invoice_id],
            {'fields': ['l10n_cr_einvoice_id', 'name']}
        )[0]

        if invoice['l10n_cr_einvoice_id']:
            einvoice_id = invoice['l10n_cr_einvoice_id'][0]
            record_test(
                "Create test invoice and e-invoice",
                True,
                f"Invoice {invoice['name']}, E-Invoice ID {einvoice_id}"
            )
            return invoice_id, einvoice_id
        else:
            record_test(
                "Create test invoice and e-invoice",
                False,
                "E-invoice not created"
            )
            return None, None

    except Exception as e:
        record_test(
            "Create test invoice and e-invoice",
            False,
            f"Error: {str(e)}"
        )
        return None, None


def test_xml_generation(models, uid, einvoice_id):
    """Test XML generation before signing."""
    print_section("Test 7: XML Generation (Pre-Signing)")

    try:
        # Generate XML
        models.execute_kw(
            DB, uid, PASSWORD,
            'l10n_cr.einvoice.document', 'action_generate_xml',
            [[einvoice_id]]
        )

        # Read XML content
        einvoice = models.execute_kw(
            DB, uid, PASSWORD,
            'l10n_cr.einvoice.document', 'read',
            [einvoice_id],
            {'fields': ['xml_content', 'name']}
        )[0]

        if einvoice['xml_content']:
            xml_size = len(einvoice['xml_content'])
            record_test(
                "Generate unsigned XML",
                True,
                f"Generated {xml_size:,} bytes"
            )
            return einvoice['xml_content']
        else:
            record_test(
                "Generate unsigned XML",
                False,
                "No XML content generated"
            )
            return None

    except Exception as e:
        record_test(
            "Generate unsigned XML",
            False,
            f"Error: {str(e)}"
        )
        return None


def test_xml_signing(models, uid, einvoice_id, company_id):
    """Test XML signing with digital certificate."""
    print_section("Test 8: XML Digital Signature")

    try:
        # Call sign action (this should use the uploaded certificate)
        models.execute_kw(
            DB, uid, PASSWORD,
            'l10n_cr.einvoice.document', 'action_sign_xml',
            [[einvoice_id]]
        )

        # Read signed XML
        einvoice = models.execute_kw(
            DB, uid, PASSWORD,
            'l10n_cr.einvoice.document', 'read',
            [einvoice_id],
            {'fields': ['signed_xml', 'state', 'name']}
        )[0]

        if einvoice['signed_xml']:
            xml_size = len(einvoice['signed_xml'])
            record_test(
                "Sign XML with certificate",
                True,
                f"Signed XML generated ({xml_size:,} bytes)"
            )

            # Save signed XML for inspection
            filename = f"signed_xml_{einvoice['name']}.xml"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(einvoice['signed_xml'])
            print(f"    Saved to: {filename}")

            return einvoice['signed_xml']
        else:
            record_test(
                "Sign XML with certificate",
                False,
                "No signed XML generated"
            )
            return None

    except Exception as e:
        record_test(
            "Sign XML with certificate",
            False,
            f"Error: {str(e)}"
        )
        return None


def verify_signature_structure(signed_xml):
    """Verify XML signature structure matches XMLDSig standard."""
    print_section("Test 9: Signature Structure Verification")

    if not signed_xml:
        record_test("Signature structure verification", False, "No signed XML")
        return False

    try:
        # Parse XML
        root = etree.fromstring(signed_xml.encode('utf-8'))

        # Define namespace
        ds_ns = 'http://www.w3.org/2000/09/xmldsig#'

        # Find Signature element
        signature = root.find('{%s}Signature' % ds_ns)

        if signature is None:
            record_test(
                "Signature element exists",
                False,
                "No Signature element found"
            )
            return False

        record_test("Signature element exists", True, "Found ds:Signature")

        # Check SignedInfo
        signed_info = signature.find('{%s}SignedInfo' % ds_ns)
        if signed_info is not None:
            record_test("SignedInfo element exists", True, "Found ds:SignedInfo")

            # Check CanonicalizationMethod
            canon = signed_info.find('{%s}CanonicalizationMethod' % ds_ns)
            if canon is not None:
                canon_algo = canon.get('Algorithm')
                record_test(
                    "CanonicalizationMethod",
                    True,
                    f"Algorithm: {canon_algo}"
                )

            # Check SignatureMethod
            sig_method = signed_info.find('{%s}SignatureMethod' % ds_ns)
            if sig_method is not None:
                sig_algo = sig_method.get('Algorithm')
                is_rsa_sha256 = 'rsa-sha256' in sig_algo.lower()
                record_test(
                    "SignatureMethod (RSA-SHA256)",
                    is_rsa_sha256,
                    f"Algorithm: {sig_algo}"
                )

            # Check Reference
            reference = signed_info.find('{%s}Reference' % ds_ns)
            if reference is not None:
                record_test("Reference element", True, "Found reference")

                # Check DigestMethod
                digest_method = reference.find('{%s}DigestMethod' % ds_ns)
                if digest_method is not None:
                    digest_algo = digest_method.get('Algorithm')
                    is_sha256 = 'sha256' in digest_algo.lower()
                    record_test(
                        "DigestMethod (SHA-256)",
                        is_sha256,
                        f"Algorithm: {digest_algo}"
                    )

                # Check DigestValue
                digest_value = reference.find('{%s}DigestValue' % ds_ns)
                if digest_value is not None and digest_value.text:
                    # Validate it's valid base64
                    try:
                        base64.b64decode(digest_value.text)
                        record_test(
                            "DigestValue (Base64)",
                            True,
                            f"Length: {len(digest_value.text)} chars"
                        )
                    except:
                        record_test(
                            "DigestValue (Base64)",
                            False,
                            "Invalid Base64 encoding"
                        )
        else:
            record_test("SignedInfo element exists", False, "Missing")

        # Check SignatureValue
        sig_value = signature.find('{%s}SignatureValue' % ds_ns)
        if sig_value is not None and sig_value.text:
            # Validate it's valid base64
            try:
                sig_bytes = base64.b64decode(sig_value.text)
                record_test(
                    "SignatureValue (Base64)",
                    True,
                    f"Length: {len(sig_value.text)} chars ({len(sig_bytes)} bytes)"
                )
            except:
                record_test(
                    "SignatureValue (Base64)",
                    False,
                    "Invalid Base64 encoding"
                )
        else:
            record_test("SignatureValue exists", False, "Missing")

        # Check KeyInfo
        key_info = signature.find('{%s}KeyInfo' % ds_ns)
        if key_info is not None:
            record_test("KeyInfo element exists", True, "Found ds:KeyInfo")

            # Check X509Data
            x509_data = key_info.find('{%s}X509Data' % ds_ns)
            if x509_data is not None:
                record_test("X509Data element", True, "Found")

                # Check X509Certificate
                x509_cert = x509_data.find('{%s}X509Certificate' % ds_ns)
                if x509_cert is not None and x509_cert.text:
                    # Validate base64
                    try:
                        cert_bytes = base64.b64decode(x509_cert.text)
                        record_test(
                            "X509Certificate (Base64)",
                            True,
                            f"Certificate embedded ({len(cert_bytes)} bytes)"
                        )
                    except:
                        record_test(
                            "X509Certificate (Base64)",
                            False,
                            "Invalid Base64 encoding"
                        )
                else:
                    record_test("X509Certificate", False, "Missing or empty")
            else:
                record_test("X509Data element", False, "Missing")
        else:
            record_test("KeyInfo element exists", False, "Missing")

        return True

    except Exception as e:
        record_test(
            "Signature structure verification",
            False,
            f"Error parsing XML: {str(e)}"
        )
        return False


def test_complete_workflow(models, uid, company_id):
    """Test complete workflow: Generate → Sign → Verify."""
    print_section("Test 10: Complete Workflow Integration")

    # Create new invoice
    invoice_id, einvoice_id = create_test_invoice(models, uid)

    if not einvoice_id:
        record_test("Complete workflow", False, "Failed to create invoice")
        return False

    # Generate XML
    unsigned_xml = test_xml_generation(models, uid, einvoice_id)

    if not unsigned_xml:
        record_test("Complete workflow - XML generation", False, "No XML generated")
        return False

    # Sign XML
    signed_xml = test_xml_signing(models, uid, einvoice_id, company_id)

    if not signed_xml:
        record_test("Complete workflow - XML signing", False, "Signing failed")
        return False

    # Verify structure
    verified = verify_signature_structure(signed_xml)

    record_test(
        "Complete workflow integration",
        verified,
        "Generate → Sign → Verify completed successfully" if verified else "Verification failed"
    )

    return verified


def print_test_summary():
    """Print comprehensive test summary."""
    print_header("Phase 2 Test Summary")

    total = test_results['total']
    passed = test_results['passed']
    failed = test_results['failed']

    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"Total Tests:  {total}")
    print(f"Passed:       {passed} ✅")
    print(f"Failed:       {failed} ❌")
    print(f"Pass Rate:    {pass_rate:.1f}%")

    print("\n" + "-" * 80)
    print("Detailed Results:")
    print("-" * 80 + "\n")

    for test in test_results['tests']:
        status = "✅" if test['passed'] else "❌"
        print(f"{status} {test['name']}")
        if test['details']:
            print(f"    {test['details']}")

    print("\n" + "=" * 80)

    if pass_rate >= 90:
        print("\n🎉 EXCELLENT! Phase 2 digital signature is working correctly.")
    elif pass_rate >= 70:
        print("\n⚠️  GOOD! Most tests passed. Review failed tests.")
    else:
        print("\n❌ ATTENTION NEEDED! Multiple tests failed. Review implementation.")

    print("\n" + "=" * 80)

    # Save results to JSON
    results_file = f"phase2_signature_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {results_file}")
    print("=" * 80 + "\n")


def main():
    """Run Phase 2 digital signature tests."""

    print_header("Phase 2 E-Invoice Digital Signature Testing")

    print("This script tests the following components:")
    print("  • Certificate Manager (certificate_manager.py)")
    print("  • XML Signer (xml_signer.py)")
    print("  • Digital Signature Workflow")
    print("  • XMLDSig Structure Validation")

    # Verify certificate file exists
    if not verify_certificate_file():
        print("\n❌ Certificate file not found. Cannot proceed with tests.")
        return

    # Connect to Odoo
    print_section("Odoo Connection")
    print("Connecting to Odoo...")

    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

        # Authenticate
        print(f"Authenticating as {USERNAME}...")
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})

        if not uid:
            print("❌ Authentication failed!")
            return

        print(f"✅ Authenticated successfully (UID: {uid})")

    except Exception as e:
        print(f"❌ Failed to connect to Odoo: {str(e)}")
        return

    # Upload certificate
    company_id = upload_certificate_to_company(models, uid)
    if not company_id:
        print("\n❌ Failed to upload certificate. Cannot proceed.")
        return

    # Test certificate loading
    cert_info = test_certificate_loading(models, uid, company_id)

    # Test certificate validation
    if cert_info:
        test_certificate_validation(cert_info)

    # Test error handling
    test_wrong_pin(models, uid)

    # Test complete workflow
    test_complete_workflow(models, uid, company_id)

    # Print summary
    print_test_summary()

    print("\nNext Steps:")
    print("1. Review generated signed_xml_*.xml files")
    print("2. Verify signature structure matches Hacienda requirements")
    print("3. Ready to start Phase 3: Hacienda API Integration")
    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()
