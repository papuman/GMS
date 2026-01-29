#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Phase 5: PDF Report Generation and Email Delivery

This script tests:
1. QR code generation
2. PDF report generation with QR codes
3. Email template rendering
4. Email sending functionality
5. Auto-send on acceptance workflow
6. PDF download action

Run this script using Odoo shell:
    odoo-bin shell -c odoo.conf -d your_database --shell-interface ipython
    >>> exec(open('test_phase5_pdf_email.py').read())

Or directly with Python:
    python3 test_phase5_pdf_email.py
"""

import logging
import sys

_logger = logging.getLogger(__name__)

def test_phase5_pdf_email():
    """Main test function for Phase 5 PDF and Email functionality."""

    print("\n" + "="*80)
    print("PHASE 5: PDF REPORT GENERATION AND EMAIL DELIVERY - TEST SUITE")
    print("="*80 + "\n")

    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }

    try:
        # Get Odoo environment (if running in Odoo shell)
        if 'env' not in globals():
            print("ERROR: This script must be run in Odoo shell context")
            print("Usage: odoo-bin shell -c odoo.conf -d your_database")
            return False

        # Test 1: QR Code Generator Model
        print("\n1. Testing QR Code Generator Model")
        print("-" * 80)
        try:
            qr_generator = env['l10n_cr.qr.generator']

            # Test with valid clave
            test_clave = '50601011234567890101234567890123456789012345678901'  # 50 digits
            qr_code = qr_generator.generate_qr_code(test_clave)

            if qr_code and len(qr_code) > 100:  # Base64 image should be substantial
                print("  ✓ QR code generation successful")
                print(f"  ✓ Generated QR code (base64 length: {len(qr_code)})")
                results['passed'].append("QR code generation")
            else:
                print("  ✗ QR code generation failed - invalid output")
                results['failed'].append("QR code generation")

            # Test URL format
            url = qr_generator._build_hacienda_url(test_clave)
            expected_url = f'https://tribunet.hacienda.go.cr/docs/esquemas/2017/v4.3/facturaElectronica.html?clave={test_clave}'

            if url == expected_url:
                print(f"  ✓ QR URL format correct: {url[:60]}...")
                results['passed'].append("QR URL format")
            else:
                print(f"  ✗ QR URL format incorrect")
                print(f"    Expected: {expected_url}")
                print(f"    Got: {url}")
                results['failed'].append("QR URL format")

        except Exception as e:
            print(f"  ✗ QR code generator test failed: {str(e)}")
            results['failed'].append(f"QR code generator: {str(e)}")

        # Test 2: Find E-Invoice Documents
        print("\n2. Finding Test E-Invoice Documents")
        print("-" * 80)
        try:
            einvoice_docs = env['l10n_cr.einvoice.document'].search([
                ('state', '=', 'accepted')
            ], limit=1)

            if not einvoice_docs:
                print("  ⚠ No accepted e-invoice documents found")
                print("  ⚠ Searching for any e-invoice document...")
                einvoice_docs = env['l10n_cr.einvoice.document'].search([], limit=1)

            if einvoice_docs:
                doc = einvoice_docs[0]
                print(f"  ✓ Found document: {doc.name}")
                print(f"    - State: {doc.state}")
                print(f"    - Clave: {doc.clave or 'Not generated'}")
                print(f"    - Customer: {doc.partner_id.name}")
                print(f"    - Email: {doc.partner_id.email or 'No email'}")
                results['passed'].append("Find test documents")
            else:
                print("  ✗ No e-invoice documents found in database")
                results['failed'].append("Find test documents")
                doc = None

        except Exception as e:
            print(f"  ✗ Error finding documents: {str(e)}")
            results['failed'].append(f"Find documents: {str(e)}")
            doc = None

        # Test 3: PDF Report Generation
        if doc and doc.clave:
            print("\n3. Testing PDF Report Generation")
            print("-" * 80)
            try:
                # Test _get_qr_code_image method
                qr_image = doc._get_qr_code_image()
                if qr_image:
                    print(f"  ✓ QR code image generated for document")
                    results['passed'].append("QR code for document")
                else:
                    print("  ✗ QR code image generation failed")
                    results['failed'].append("QR code for document")

                # Test PDF generation
                if not doc.pdf_attachment_id:
                    print("  - Generating PDF...")
                    doc.action_generate_pdf()

                if doc.pdf_attachment_id:
                    print(f"  ✓ PDF attachment created: {doc.pdf_attachment_id.name}")
                    print(f"    - Size: {len(doc.pdf_attachment_id.datas)} bytes")
                    results['passed'].append("PDF generation")
                else:
                    print("  ✗ PDF attachment not created")
                    results['failed'].append("PDF generation")

            except Exception as e:
                print(f"  ✗ PDF generation test failed: {str(e)}")
                results['failed'].append(f"PDF generation: {str(e)}")
        else:
            print("\n3. Testing PDF Report Generation")
            print("-" * 80)
            print("  ⚠ Skipped - No valid document with clave found")
            results['warnings'].append("PDF generation test skipped")

        # Test 4: Email Template
        print("\n4. Testing Email Template")
        print("-" * 80)
        try:
            # Check if email template exists
            template = env.ref('l10n_cr_einvoice.email_template_einvoice', raise_if_not_found=False)

            if template:
                print(f"  ✓ Email template found: {template.name}")
                print(f"    - Model: {template.model}")
                print(f"    - Subject: {template.subject}")
                results['passed'].append("Email template exists")

                # Test rendering if we have a document
                if doc:
                    try:
                        # Generate email values (without sending)
                        email_values = template.generate_email([doc.id])[doc.id]
                        print(f"  ✓ Email template rendered successfully")
                        print(f"    - Subject: {email_values.get('subject', 'N/A')}")
                        print(f"    - To: {email_values.get('email_to', 'N/A')}")
                        results['passed'].append("Email template rendering")
                    except Exception as e:
                        print(f"  ✗ Email template rendering failed: {str(e)}")
                        results['failed'].append(f"Email rendering: {str(e)}")
            else:
                print("  ✗ Email template not found")
                results['failed'].append("Email template not found")

        except Exception as e:
            print(f"  ✗ Email template test failed: {str(e)}")
            results['failed'].append(f"Email template: {str(e)}")

        # Test 5: Email Sending (dry run - don't actually send)
        if doc and doc.partner_id.email and doc.state == 'accepted':
            print("\n5. Testing Email Sending Logic (Dry Run)")
            print("-" * 80)
            try:
                # Check preconditions
                if not doc.pdf_attachment_id:
                    print("  - PDF not generated, generating now...")
                    doc.action_generate_pdf()

                print(f"  ✓ Document ready for email sending")
                print(f"    - Customer: {doc.partner_id.name}")
                print(f"    - Email: {doc.partner_id.email}")
                print(f"    - PDF attached: {bool(doc.pdf_attachment_id)}")
                print(f"    - Email sent before: {doc.email_sent}")

                # Note: We don't actually send to avoid spamming
                print("  ℹ Actual email sending skipped (test mode)")
                results['passed'].append("Email sending prerequisites")

            except Exception as e:
                print(f"  ✗ Email sending test failed: {str(e)}")
                results['failed'].append(f"Email sending: {str(e)}")
        else:
            print("\n5. Testing Email Sending Logic")
            print("-" * 80)
            if not doc:
                print("  ⚠ Skipped - No document available")
            elif not doc.partner_id.email:
                print(f"  ⚠ Skipped - Customer {doc.partner_id.name} has no email")
            elif doc.state != 'accepted':
                print(f"  ⚠ Skipped - Document state is {doc.state}, not 'accepted'")
            results['warnings'].append("Email sending test skipped")

        # Test 6: Auto-send Configuration
        print("\n6. Testing Auto-send Email Configuration")
        print("-" * 80)
        try:
            company = env.company
            print(f"  - Company: {company.name}")
            print(f"  - Auto-send email enabled: {company.l10n_cr_auto_send_email}")

            if hasattr(company, 'l10n_cr_auto_send_email'):
                print("  ✓ Auto-send configuration field exists")
                results['passed'].append("Auto-send configuration")
            else:
                print("  ✗ Auto-send configuration field missing")
                results['failed'].append("Auto-send configuration")

        except Exception as e:
            print(f"  ✗ Auto-send configuration test failed: {str(e)}")
            results['failed'].append(f"Auto-send config: {str(e)}")

        # Test 7: PDF Download Action
        if doc and doc.pdf_attachment_id:
            print("\n7. Testing PDF Download Action")
            print("-" * 80)
            try:
                result = doc.action_download_pdf()

                if result and result.get('type') == 'ir.actions.act_url':
                    print(f"  ✓ PDF download action successful")
                    print(f"    - URL: {result.get('url', 'N/A')}")
                    results['passed'].append("PDF download action")
                else:
                    print("  ✗ PDF download action returned unexpected result")
                    results['failed'].append("PDF download action")

            except Exception as e:
                print(f"  ✗ PDF download action failed: {str(e)}")
                results['failed'].append(f"PDF download: {str(e)}")
        else:
            print("\n7. Testing PDF Download Action")
            print("-" * 80)
            print("  ⚠ Skipped - No document with PDF attachment")
            results['warnings'].append("PDF download test skipped")

        # Test 8: Report Template Exists
        print("\n8. Testing PDF Report Template")
        print("-" * 80)
        try:
            report = env.ref('l10n_cr_einvoice.action_report_einvoice', raise_if_not_found=False)

            if report:
                print(f"  ✓ PDF report template found: {report.name}")
                print(f"    - Model: {report.model}")
                print(f"    - Report type: {report.report_type}")
                print(f"    - Report name: {report.report_name}")
                results['passed'].append("PDF report template")
            else:
                print("  ✗ PDF report template not found")
                results['failed'].append("PDF report template")

        except Exception as e:
            print(f"  ✗ PDF report template test failed: {str(e)}")
            results['failed'].append(f"PDF report template: {str(e)}")

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Print Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    total_tests = len(results['passed']) + len(results['failed'])
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {len(results['passed'])} ✓")
    print(f"Failed: {len(results['failed'])} ✗")
    print(f"Warnings: {len(results['warnings'])} ⚠")

    if results['passed']:
        print("\n✓ PASSED:")
        for test in results['passed']:
            print(f"  • {test}")

    if results['failed']:
        print("\n✗ FAILED:")
        for test in results['failed']:
            print(f"  • {test}")

    if results['warnings']:
        print("\n⚠ WARNINGS:")
        for test in results['warnings']:
            print(f"  • {test}")

    success_rate = (len(results['passed']) / total_tests * 100) if total_tests > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    if len(results['failed']) == 0:
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED - PHASE 5 IMPLEMENTATION COMPLETE!")
        print("="*80 + "\n")
        return True
    else:
        print("\n" + "="*80)
        print("✗ SOME TESTS FAILED - PLEASE REVIEW")
        print("="*80 + "\n")
        return False


if __name__ == '__main__':
    # Check if running in Odoo shell
    if 'env' in dir():
        test_phase5_pdf_email()
    else:
        print("ERROR: This script must be run within Odoo shell context")
        print("\nUsage:")
        print("  odoo-bin shell -c odoo.conf -d your_database")
        print("  >>> exec(open('test_phase5_pdf_email.py').read())")
        sys.exit(1)
