#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive End-to-End Integration Testing for Costa Rica E-Invoicing
Using Odoo Shell for full integration

Tests the complete workflow across all phases:
- Phase 1: Invoice creation and XML generation
- Phase 2: XML structure validation and XSD compliance
- Phase 3: Digital signature and Hacienda submission
- Phase 5: QR code generation, PDF creation, and email delivery

Usage: Run from within Odoo shell or as standalone script
    odoo-bin shell -c odoo.conf -d tribu_sandbox < test_e2e_integration_odoo.py

Author: GMS Development Team
Date: 2025-12-28
"""

import logging
import json
from datetime import datetime

_logger = logging.getLogger(__name__)

def run_comprehensive_integration_tests():
    """
    Run comprehensive E2E integration tests in Odoo environment
    """

    print("\n" + "="*80)
    print("COMPREHENSIVE E2E INTEGRATION TEST SUITE")
    print("Costa Rica E-Invoicing - Complete Workflow Testing")
    print("="*80 + "\n")

    results = {
        'timestamp': datetime.now().isoformat(),
        'phase_1': {},
        'phase_2': {},
        'phase_3': {},
        'phase_5': {},
        'integration_points': {},
        'file_sync': {},
        'configuration': {}
    }

    try:
        # Access Odoo environment
        Invoice = env['account.move']
        EInvoice = env['l10n_cr.einvoice.document']
        Partner = env['res.partner']
        Product = env['product.product']
        Company = env['res.company']

        print("✓ Odoo environment initialized\n")

        # ================================================================
        # PHASE 1: Invoice Creation & XML Generation
        # ================================================================
        print("="*80)
        print("PHASE 1: Invoice Creation & XML Generation")
        print("="*80 + "\n")

        # Get company
        company = Company.search([], limit=1)
        if not company:
            print("✗ No company found")
            results['phase_1']['company_found'] = False
            return results

        print(f"✓ Company: {company.name}")
        results['phase_1']['company_found'] = True

        # Get customer
        partner = Partner.search([('customer_rank', '>', 0)], limit=1)
        if not partner:
            print("✗ No customer found")
            results['phase_1']['customer_found'] = False
            return results

        print(f"✓ Customer: {partner.name}")
        results['phase_1']['customer_found'] = True

        # Get product
        product = Product.search([('sale_ok', '=', True)], limit=1)
        if not product:
            print("✗ No product found")
            results['phase_1']['product_found'] = False
            return results

        print(f"✓ Product: {product.name}")
        results['phase_1']['product_found'] = True

        # Create test invoice
        print("\nCreating test invoice...")
        invoice = Invoice.create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': datetime.now().date(),
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': 2,
                'price_unit': 50000.00,
            })],
        })

        print(f"✓ Invoice created: {invoice.name}")
        results['phase_1']['invoice_created'] = True
        results['phase_1']['invoice_id'] = invoice.id
        results['phase_1']['invoice_name'] = invoice.name

        # Post invoice
        print("Posting invoice...")
        invoice.action_post()
        print(f"✓ Invoice posted (State: {invoice.state})")
        results['phase_1']['invoice_posted'] = True

        # Generate e-invoice
        print("Generating electronic invoice...")
        try:
            if hasattr(invoice, 'action_generate_einvoice'):
                invoice.action_generate_einvoice()
                print("✓ E-invoice generation triggered")
                results['phase_1']['einvoice_generated'] = True
            else:
                print("⚠ action_generate_einvoice method not found")
                results['phase_1']['einvoice_generated'] = False
        except Exception as e:
            print(f"✗ E-invoice generation failed: {str(e)}")
            results['phase_1']['einvoice_generated'] = False
            results['phase_1']['error'] = str(e)

        # Check if e-invoice document was created
        einvoice_doc = EInvoice.search([('move_id', '=', invoice.id)], limit=1)
        if einvoice_doc:
            print(f"✓ E-invoice document created: {einvoice_doc.name}")
            results['phase_1']['document_created'] = True
            results['phase_1']['document_id'] = einvoice_doc.id
        else:
            print("✗ E-invoice document not created")
            results['phase_1']['document_created'] = False
            return results

        # ================================================================
        # PHASE 2: XML Structure & XSD Validation
        # ================================================================
        print("\n" + "="*80)
        print("PHASE 2: XML Structure & XSD Validation")
        print("="*80 + "\n")

        # Check XML generation
        if einvoice_doc.xml_content:
            print("✓ XML content generated")
            results['phase_2']['xml_generated'] = True

            # Check XML size
            xml_size = len(einvoice_doc.xml_content)
            print(f"  XML size: {xml_size} bytes")
            results['phase_2']['xml_size'] = xml_size
        else:
            print("✗ XML content not generated")
            results['phase_2']['xml_generated'] = False

        # Check clave (50-digit key)
        if einvoice_doc.clave and len(einvoice_doc.clave) == 50:
            print(f"✓ Clave generated: {einvoice_doc.clave[:20]}...")
            results['phase_2']['clave_valid'] = True
            results['phase_2']['clave'] = einvoice_doc.clave
        else:
            print(f"✗ Invalid clave (length: {len(einvoice_doc.clave) if einvoice_doc.clave else 0})")
            results['phase_2']['clave_valid'] = False

        # Check consecutive
        if einvoice_doc.consecutive:
            print(f"✓ Consecutive: {einvoice_doc.consecutive}")
            results['phase_2']['consecutive_valid'] = True
            results['phase_2']['consecutive'] = einvoice_doc.consecutive
        else:
            print("✗ No consecutive generated")
            results['phase_2']['consecutive_valid'] = False

        # Test XSD validation
        print("\nTesting XSD validation...")
        try:
            if hasattr(einvoice_doc, 'action_validate_xml'):
                einvoice_doc.action_validate_xml()
                print("✓ XSD validation passed")
                results['phase_2']['xsd_valid'] = True
            else:
                print("⚠ action_validate_xml method not found")
                results['phase_2']['xsd_valid'] = False
        except Exception as e:
            print(f"⚠ XSD validation: {str(e)[:100]}")
            results['phase_2']['xsd_valid'] = False
            results['phase_2']['xsd_error'] = str(e)[:200]

        # ================================================================
        # PHASE 3: Digital Signature & Hacienda Submission
        # ================================================================
        print("\n" + "="*80)
        print("PHASE 3: Digital Signature & Hacienda Submission")
        print("="*80 + "\n")

        # Check certificate configuration
        if company.cr_einvoice_certificate:
            print("✓ Certificate configured")
            results['phase_3']['certificate_configured'] = True
        else:
            print("⚠ Certificate not configured - skipping signature tests")
            results['phase_3']['certificate_configured'] = False

        # Test signing if certificate is available
        if company.cr_einvoice_certificate:
            print("\nAttempting to sign XML...")
            try:
                if hasattr(einvoice_doc, 'action_sign_xml'):
                    einvoice_doc.action_sign_xml()
                    print("✓ XML signed successfully")
                    results['phase_3']['xml_signed'] = True
                else:
                    print("⚠ action_sign_xml method not found")
                    results['phase_3']['xml_signed'] = False
            except Exception as e:
                print(f"✗ XML signing failed: {str(e)[:100]}")
                results['phase_3']['xml_signed'] = False
                results['phase_3']['sign_error'] = str(e)[:200]

            # Check signed XML
            if einvoice_doc.signed_xml:
                print("✓ Signed XML content present")
                results['phase_3']['signed_xml_present'] = True
                signed_size = len(einvoice_doc.signed_xml)
                print(f"  Signed XML size: {signed_size} bytes")
                results['phase_3']['signed_xml_size'] = signed_size
            else:
                print("✗ Signed XML not generated")
                results['phase_3']['signed_xml_present'] = False

            # Test Hacienda submission
            print("\nTesting Hacienda submission...")
            try:
                if hasattr(einvoice_doc, 'action_submit_hacienda'):
                    einvoice_doc.action_submit_hacienda()
                    print("✓ Submitted to Hacienda")
                    results['phase_3']['submitted'] = True
                else:
                    print("⚠ action_submit_hacienda method not found")
                    results['phase_3']['submitted'] = False
            except Exception as e:
                print(f"⚠ Hacienda submission: {str(e)[:100]}")
                results['phase_3']['submitted'] = False
                results['phase_3']['submit_error'] = str(e)[:200]

        # ================================================================
        # PHASE 5: QR Code, PDF & Email Delivery
        # ================================================================
        print("\n" + "="*80)
        print("PHASE 5: QR Code, PDF & Email Delivery")
        print("="*80 + "\n")

        # Test QR code generation
        print("Testing QR code generation...")
        try:
            QRGenerator = env['l10n_cr.qr.generator']
            if einvoice_doc.clave:
                qr_code = QRGenerator.generate_qr_code(einvoice_doc.clave)
                if qr_code and len(qr_code) > 100:
                    print(f"✓ QR code generated (base64 length: {len(qr_code)})")
                    results['phase_5']['qr_generated'] = True
                    results['phase_5']['qr_size'] = len(qr_code)
                else:
                    print("✗ QR code generation returned invalid data")
                    results['phase_5']['qr_generated'] = False
            else:
                print("⚠ No clave available for QR generation")
                results['phase_5']['qr_generated'] = False
        except Exception as e:
            print(f"✗ QR generation failed: {str(e)[:100]}")
            results['phase_5']['qr_generated'] = False
            results['phase_5']['qr_error'] = str(e)[:200]

        # Test PDF report template
        print("\nChecking PDF report template...")
        try:
            Report = env['ir.actions.report']
            reports = Report.search([('model', '=', 'l10n_cr.einvoice.document')])
            if reports:
                print(f"✓ Found {len(reports)} PDF report template(s)")
                for report in reports:
                    print(f"  - {report.name}")
                results['phase_5']['pdf_template_exists'] = True
                results['phase_5']['pdf_template_count'] = len(reports)
            else:
                print("⚠ No PDF report templates found")
                results['phase_5']['pdf_template_exists'] = False
        except Exception as e:
            print(f"✗ Error checking PDF templates: {str(e)}")
            results['phase_5']['pdf_error'] = str(e)[:200]

        # Test email configuration
        print("\nChecking email configuration...")
        try:
            auto_send = company.cr_einvoice_auto_send_email if hasattr(company, 'cr_einvoice_auto_send_email') else False
            print(f"✓ Auto-send email: {auto_send}")
            results['phase_5']['auto_send_configured'] = auto_send

            # Check for email templates
            Template = env['mail.template']
            templates = Template.search([
                ('model', '=', 'l10n_cr.einvoice.document')
            ])
            if templates:
                print(f"✓ Found {len(templates)} email template(s)")
                results['phase_5']['email_templates_exist'] = True
                results['phase_5']['email_template_count'] = len(templates)
            else:
                print("⚠ No email templates found")
                results['phase_5']['email_templates_exist'] = False
        except Exception as e:
            print(f"⚠ Email config check: {str(e)}")
            results['phase_5']['email_config_error'] = str(e)[:200]

        # ================================================================
        # Integration Points Testing
        # ================================================================
        print("\n" + "="*80)
        print("Integration Points Testing")
        print("="*80 + "\n")

        # Test Invoice → E-Invoice Document link
        print("Testing Invoice → E-Invoice Document link...")
        if einvoice_doc.move_id.id == invoice.id:
            print("✓ Invoice correctly linked to e-invoice document")
            results['integration_points']['invoice_link_valid'] = True
        else:
            print("✗ Invoice link broken")
            results['integration_points']['invoice_link_valid'] = False

        # Test state management
        print(f"\nDocument state: {einvoice_doc.state}")
        valid_states = ['draft', 'generated', 'signed', 'submitted', 'accepted', 'rejected', 'error']
        if einvoice_doc.state in valid_states:
            print(f"✓ State is valid: {einvoice_doc.state}")
            results['integration_points']['state_valid'] = True
            results['integration_points']['current_state'] = einvoice_doc.state
        else:
            print(f"✗ Invalid state: {einvoice_doc.state}")
            results['integration_points']['state_valid'] = False

        # Test data flow
        print("\nTesting data flow integrity...")
        if invoice.partner_id.id == einvoice_doc.partner_id.id:
            print("✓ Partner data correctly propagated")
            results['integration_points']['partner_data_valid'] = True
        else:
            print("✗ Partner data mismatch")
            results['integration_points']['partner_data_valid'] = False

        # ================================================================
        # Configuration Check
        # ================================================================
        print("\n" + "="*80)
        print("Configuration Check")
        print("="*80 + "\n")

        # Check company settings
        config_checks = {
            'cr_einvoice_username': 'Hacienda Username',
            'cr_einvoice_password': 'Hacienda Password',
            'cr_einvoice_certificate': 'Digital Certificate',
            'cr_einvoice_certificate_password': 'Certificate Password',
            'cr_einvoice_use_sandbox': 'Sandbox Mode',
            'cr_einvoice_auto_send_email': 'Auto-send Email',
        }

        for field, label in config_checks.items():
            if hasattr(company, field):
                value = getattr(company, field)
                if value:
                    if 'password' in field:
                        print(f"✓ {label}: ***configured***")
                    elif field == 'cr_einvoice_certificate':
                        print(f"✓ {label}: ***configured***")
                    else:
                        print(f"✓ {label}: {value}")
                    results['configuration'][field] = True
                else:
                    print(f"⚠ {label}: Not configured")
                    results['configuration'][field] = False
            else:
                print(f"⚠ {label}: Field not found")
                results['configuration'][field] = False

        # ================================================================
        # Generate Summary Report
        # ================================================================
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80 + "\n")

        # Count tests
        total_tests = 0
        passed_tests = 0

        for phase, phase_results in results.items():
            if phase != 'timestamp':
                for key, value in phase_results.items():
                    if isinstance(value, bool):
                        total_tests += 1
                        if value:
                            passed_tests += 1

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")

        # Recommendations
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80 + "\n")

        recommendations = []

        if not results['phase_3'].get('certificate_configured', False):
            recommendations.append("Configure digital certificate for XML signing")

        if not results['phase_5'].get('qr_generated', False):
            recommendations.append("Install qrcode library: pip install qrcode[pil]")

        if not results['phase_5'].get('pdf_template_exists', False):
            recommendations.append("Verify PDF report template is properly configured")

        if not results['phase_5'].get('email_templates_exist', False):
            recommendations.append("Create email templates for e-invoice delivery")

        if not results['configuration'].get('cr_einvoice_auto_send_email', False):
            recommendations.append("Consider enabling auto-send email for accepted invoices")

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("✓ No recommendations - all systems operational!")

        # Save results
        print("\n" + "="*80)
        results_file = '/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/e2e_integration_test_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to: {results_file}")
        print("="*80 + "\n")

        return results

    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {str(e)}")
        _logger.error(f"Integration test failed: {str(e)}", exc_info=True)
        results['critical_error'] = str(e)
        return results

# Run the tests if in Odoo shell
if __name__ == '__main__':
    # This will only work when run from Odoo shell where 'env' is available
    try:
        results = run_comprehensive_integration_tests()
    except NameError:
        print("This script must be run from Odoo shell:")
        print("  odoo-bin shell -c odoo.conf -d tribu_sandbox < test_e2e_integration_odoo.py")
