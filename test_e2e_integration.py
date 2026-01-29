#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive End-to-End Integration Testing for Costa Rica E-Invoicing

Tests the complete workflow across all phases:
- Phase 1: Invoice creation and XML generation
- Phase 2: XML structure validation and XSD compliance
- Phase 3: Digital signature and Hacienda submission
- Phase 5: QR code generation, PDF creation, and email delivery

Author: GMS Development Team
Date: 2025-12-28
"""

import sys
import os
import logging
import xmlrpc.client
from datetime import datetime
import base64
import json
from lxml import etree

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Odoo connection parameters
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'tribu_sandbox'
ODOO_USERNAME = 'admin'
ODOO_PASSWORD = 'admin'

class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class IntegrationTestSuite:
    """Comprehensive integration test suite for e-invoicing workflow"""

    def __init__(self):
        self.common = None
        self.uid = None
        self.models = None
        self.test_results = {
            'phase_1': {},
            'phase_2': {},
            'phase_3': {},
            'phase_5': {},
            'integration_points': {},
            'file_sync': {},
            'configuration': {}
        }
        self.test_invoice_id = None
        self.test_document_id = None

    def connect_odoo(self):
        """Establish connection to Odoo"""
        print(f"\n{Color.BOLD}{Color.CYAN}=== Connecting to Odoo ==={Color.END}")
        try:
            self.common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
            version = self.common.version()
            logger.info(f"Connected to Odoo version: {version['server_version']}")
            print(f"{Color.GREEN}✓ Connected to Odoo {version['server_version']}{Color.END}")

            self.uid = self.common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
            if not self.uid:
                raise Exception("Authentication failed")

            logger.info(f"Authenticated as user ID: {self.uid}")
            print(f"{Color.GREEN}✓ Authenticated successfully (UID: {self.uid}){Color.END}")

            self.models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
            return True

        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            print(f"{Color.RED}✗ Connection failed: {str(e)}{Color.END}")
            return False

    def test_phase1_invoice_creation(self):
        """
        PHASE 1: Test invoice creation and basic XML generation
        """
        print(f"\n{Color.BOLD}{Color.MAGENTA}=== PHASE 1: Invoice Creation & XML Generation ==={Color.END}")

        try:
            # Get company
            company_ids = self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'res.company', 'search', [[]]
            )

            if not company_ids:
                print(f"{Color.RED}✗ No company found{Color.END}")
                self.test_results['phase_1']['company_found'] = False
                return False

            company_id = company_ids[0]
            print(f"{Color.GREEN}✓ Company found: ID {company_id}{Color.END}")
            self.test_results['phase_1']['company_found'] = True

            # Get customer
            partner_ids = self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'res.partner', 'search',
                [[('customer_rank', '>', 0)]], {'limit': 1}
            )

            if not partner_ids:
                print(f"{Color.RED}✗ No customer found{Color.END}")
                self.test_results['phase_1']['customer_found'] = False
                return False

            partner_id = partner_ids[0]
            print(f"{Color.GREEN}✓ Customer found: ID {partner_id}{Color.END}")
            self.test_results['phase_1']['customer_found'] = True

            # Get product
            product_ids = self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'product.product', 'search',
                [[('sale_ok', '=', True)]], {'limit': 1}
            )

            if not product_ids:
                print(f"{Color.RED}✗ No product found{Color.END}")
                self.test_results['phase_1']['product_found'] = False
                return False

            product_id = product_ids[0]
            print(f"{Color.GREEN}✓ Product found: ID {product_id}{Color.END}")
            self.test_results['phase_1']['product_found'] = True

            # Create invoice
            print(f"\n{Color.BLUE}Creating test invoice...{Color.END}")
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner_id,
                'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                'invoice_line_ids': [(0, 0, {
                    'product_id': product_id,
                    'quantity': 2,
                    'price_unit': 50000.00,  # CRC 50,000
                })],
            }

            invoice_id = self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'account.move', 'create', [invoice_vals]
            )

            self.test_invoice_id = invoice_id
            print(f"{Color.GREEN}✓ Invoice created: ID {invoice_id}{Color.END}")
            self.test_results['phase_1']['invoice_created'] = True

            # Post the invoice
            print(f"{Color.BLUE}Posting invoice...{Color.END}")
            self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'account.move', 'action_post', [[invoice_id]]
            )
            print(f"{Color.GREEN}✓ Invoice posted{Color.END}")
            self.test_results['phase_1']['invoice_posted'] = True

            # Generate e-invoice
            print(f"{Color.BLUE}Generating electronic invoice...{Color.END}")
            try:
                self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'account.move', 'action_generate_einvoice', [[invoice_id]]
                )
                print(f"{Color.GREEN}✓ E-invoice generation triggered{Color.END}")
                self.test_results['phase_1']['einvoice_generated'] = True
            except Exception as e:
                print(f"{Color.RED}✗ E-invoice generation failed: {str(e)}{Color.END}")
                self.test_results['phase_1']['einvoice_generated'] = False
                self.test_results['phase_1']['error'] = str(e)
                return False

            # Check if document was created
            doc_ids = self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'l10n_cr.einvoice.document', 'search',
                [[('invoice_id', '=', invoice_id)]]
            )

            if doc_ids:
                self.test_document_id = doc_ids[0]
                print(f"{Color.GREEN}✓ E-invoice document created: ID {self.test_document_id}{Color.END}")
                self.test_results['phase_1']['document_created'] = True
                return True
            else:
                print(f"{Color.RED}✗ E-invoice document not created{Color.END}")
                self.test_results['phase_1']['document_created'] = False
                return False

        except Exception as e:
            logger.error(f"Phase 1 test failed: {str(e)}", exc_info=True)
            print(f"{Color.RED}✗ Phase 1 failed: {str(e)}{Color.END}")
            self.test_results['phase_1']['error'] = str(e)
            return False

    def test_phase2_xml_validation(self):
        """
        PHASE 2: Test XML structure and XSD validation
        """
        print(f"\n{Color.BOLD}{Color.MAGENTA}=== PHASE 2: XML Structure & XSD Validation ==={Color.END}")

        if not self.test_document_id:
            print(f"{Color.RED}✗ No document to test (Phase 1 must succeed first){Color.END}")
            return False

        try:
            # Get document data
            doc_data = self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'l10n_cr.einvoice.document', 'read',
                [[self.test_document_id]],
                {'fields': ['xml_content', 'clave', 'state', 'consecutive']}
            )[0]

            # Check if XML was generated
            if not doc_data.get('xml_content'):
                print(f"{Color.RED}✗ XML content not generated{Color.END}")
                self.test_results['phase_2']['xml_generated'] = False
                return False

            print(f"{Color.GREEN}✓ XML content generated{Color.END}")
            self.test_results['phase_2']['xml_generated'] = True

            # Decode and parse XML
            xml_content = base64.b64decode(doc_data['xml_content']).decode('utf-8')
            root = etree.fromstring(xml_content.encode('utf-8'))

            print(f"{Color.GREEN}✓ XML is well-formed{Color.END}")
            self.test_results['phase_2']['xml_wellformed'] = True

            # Check clave
            if doc_data.get('clave') and len(doc_data['clave']) == 50:
                print(f"{Color.GREEN}✓ Clave generated: {doc_data['clave'][:20]}...{Color.END}")
                self.test_results['phase_2']['clave_valid'] = True
            else:
                print(f"{Color.RED}✗ Invalid clave{Color.END}")
                self.test_results['phase_2']['clave_valid'] = False

            # Check consecutive
            if doc_data.get('consecutive'):
                print(f"{Color.GREEN}✓ Consecutive: {doc_data['consecutive']}{Color.END}")
                self.test_results['phase_2']['consecutive_valid'] = True
            else:
                print(f"{Color.RED}✗ No consecutive{Color.END}")
                self.test_results['phase_2']['consecutive_valid'] = False

            # Check DetalleServicio
            ns = {'fe': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.3/facturaElectronica'}
            detalle = root.find('.//fe:DetalleServicio', namespaces=ns)

            if detalle is not None:
                line_count = len(detalle.findall('.//fe:LineaDetalle', namespaces=ns))
                print(f"{Color.GREEN}✓ DetalleServicio populated with {line_count} lines{Color.END}")
                self.test_results['phase_2']['detalle_populated'] = True
                self.test_results['phase_2']['line_count'] = line_count
            else:
                print(f"{Color.RED}✗ DetalleServicio not found{Color.END}")
                self.test_results['phase_2']['detalle_populated'] = False

            # Validate against XSD (if available)
            print(f"{Color.BLUE}Attempting XSD validation...{Color.END}")
            try:
                result = self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'l10n_cr.einvoice.document', 'action_validate_xml',
                    [[self.test_document_id]]
                )
                print(f"{Color.GREEN}✓ XSD validation passed{Color.END}")
                self.test_results['phase_2']['xsd_valid'] = True
            except Exception as e:
                print(f"{Color.YELLOW}⚠ XSD validation: {str(e)}{Color.END}")
                self.test_results['phase_2']['xsd_valid'] = False
                self.test_results['phase_2']['xsd_error'] = str(e)

            return True

        except Exception as e:
            logger.error(f"Phase 2 test failed: {str(e)}", exc_info=True)
            print(f"{Color.RED}✗ Phase 2 failed: {str(e)}{Color.END}")
            self.test_results['phase_2']['error'] = str(e)
            return False

    def test_phase3_signature_submission(self):
        """
        PHASE 3: Test digital signature and Hacienda submission
        """
        print(f"\n{Color.BOLD}{Color.MAGENTA}=== PHASE 3: Digital Signature & Hacienda Submission ==={Color.END}")

        if not self.test_document_id:
            print(f"{Color.RED}✗ No document to test{Color.END}")
            return False

        try:
            # Check if certificate is configured
            company_data = self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'res.company', 'search_read',
                [[]], {'fields': ['cr_einvoice_certificate', 'cr_einvoice_username'], 'limit': 1}
            )

            if not company_data or not company_data[0].get('cr_einvoice_certificate'):
                print(f"{Color.YELLOW}⚠ Certificate not configured - skipping signature test{Color.END}")
                self.test_results['phase_3']['certificate_configured'] = False
                return False

            print(f"{Color.GREEN}✓ Certificate configured{Color.END}")
            self.test_results['phase_3']['certificate_configured'] = True

            # Attempt to sign XML
            print(f"{Color.BLUE}Attempting to sign XML...{Color.END}")
            try:
                self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'l10n_cr.einvoice.document', 'action_sign_xml',
                    [[self.test_document_id]]
                )
                print(f"{Color.GREEN}✓ XML signed successfully{Color.END}")
                self.test_results['phase_3']['xml_signed'] = True
            except Exception as e:
                print(f"{Color.RED}✗ XML signing failed: {str(e)}{Color.END}")
                self.test_results['phase_3']['xml_signed'] = False
                self.test_results['phase_3']['sign_error'] = str(e)
                return False

            # Verify signature structure
            doc_data = self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'l10n_cr.einvoice.document', 'read',
                [[self.test_document_id]],
                {'fields': ['signed_xml_content']}
            )[0]

            if doc_data.get('signed_xml_content'):
                signed_xml = base64.b64decode(doc_data['signed_xml_content']).decode('utf-8')
                root = etree.fromstring(signed_xml.encode('utf-8'))

                # Check for Signature element
                ns_sig = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
                signature = root.find('.//ds:Signature', namespaces=ns_sig)

                if signature is not None:
                    print(f"{Color.GREEN}✓ XMLDSig Signature element found{Color.END}")
                    self.test_results['phase_3']['signature_structure'] = True
                else:
                    print(f"{Color.RED}✗ XMLDSig Signature element not found{Color.END}")
                    self.test_results['phase_3']['signature_structure'] = False

            # Test Hacienda submission (sandbox mode)
            print(f"{Color.BLUE}Testing Hacienda submission...{Color.END}")
            try:
                self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'l10n_cr.einvoice.document', 'action_submit_hacienda',
                    [[self.test_document_id]]
                )
                print(f"{Color.GREEN}✓ Submitted to Hacienda{Color.END}")
                self.test_results['phase_3']['submitted'] = True
            except Exception as e:
                print(f"{Color.YELLOW}⚠ Hacienda submission: {str(e)}{Color.END}")
                self.test_results['phase_3']['submitted'] = False
                self.test_results['phase_3']['submit_error'] = str(e)

            return True

        except Exception as e:
            logger.error(f"Phase 3 test failed: {str(e)}", exc_info=True)
            print(f"{Color.RED}✗ Phase 3 failed: {str(e)}{Color.END}")
            self.test_results['phase_3']['error'] = str(e)
            return False

    def test_phase5_qr_pdf_email(self):
        """
        PHASE 5: Test QR code generation, PDF creation, and email delivery
        """
        print(f"\n{Color.BOLD}{Color.MAGENTA}=== PHASE 5: QR Code, PDF & Email Delivery ==={Color.END}")

        if not self.test_document_id:
            print(f"{Color.RED}✗ No document to test{Color.END}")
            return False

        try:
            doc_data = self.models.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD,
                'l10n_cr.einvoice.document', 'read',
                [[self.test_document_id]],
                {'fields': ['clave', 'qr_code', 'state']}
            )[0]

            clave = doc_data.get('clave')

            # Test QR code generation
            print(f"{Color.BLUE}Testing QR code generation...{Color.END}")
            try:
                qr_generator = self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'l10n_cr.qr.generator', 'generate_qr_code', [clave]
                )

                if qr_generator and len(qr_generator) > 100:  # Should be base64 encoded
                    print(f"{Color.GREEN}✓ QR code generated (base64 length: {len(qr_generator)}){Color.END}")
                    self.test_results['phase_5']['qr_generated'] = True
                else:
                    print(f"{Color.RED}✗ QR code generation failed{Color.END}")
                    self.test_results['phase_5']['qr_generated'] = False
            except Exception as e:
                print(f"{Color.YELLOW}⚠ QR generation: {str(e)}{Color.END}")
                self.test_results['phase_5']['qr_generated'] = False
                self.test_results['phase_5']['qr_error'] = str(e)

            # Test PDF generation
            print(f"{Color.BLUE}Testing PDF generation...{Color.END}")
            try:
                # Generate PDF report
                pdf_data = self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'ir.actions.report', 'sudo', []
                )

                # Try to get PDF
                report_ids = self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'ir.actions.report', 'search',
                    [[('model', '=', 'l10n_cr.einvoice.document')]]
                )

                if report_ids:
                    print(f"{Color.GREEN}✓ PDF report template found{Color.END}")
                    self.test_results['phase_5']['pdf_template_exists'] = True
                else:
                    print(f"{Color.YELLOW}⚠ PDF report template not configured{Color.END}")
                    self.test_results['phase_5']['pdf_template_exists'] = False

            except Exception as e:
                print(f"{Color.YELLOW}⚠ PDF generation: {str(e)}{Color.END}")
                self.test_results['phase_5']['pdf_error'] = str(e)

            # Test email configuration
            print(f"{Color.BLUE}Testing email configuration...{Color.END}")
            try:
                company_data = self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'res.company', 'search_read',
                    [[]], {'fields': ['cr_einvoice_auto_send_email'], 'limit': 1}
                )

                if company_data:
                    auto_send = company_data[0].get('cr_einvoice_auto_send_email', False)
                    print(f"{Color.GREEN}✓ Auto-send email: {auto_send}{Color.END}")
                    self.test_results['phase_5']['auto_send_configured'] = auto_send

            except Exception as e:
                print(f"{Color.YELLOW}⚠ Email config check: {str(e)}{Color.END}")
                self.test_results['phase_5']['email_config_error'] = str(e)

            return True

        except Exception as e:
            logger.error(f"Phase 5 test failed: {str(e)}", exc_info=True)
            print(f"{Color.RED}✗ Phase 5 failed: {str(e)}{Color.END}")
            self.test_results['phase_5']['error'] = str(e)
            return False

    def test_integration_points(self):
        """
        Test critical integration points between phases
        """
        print(f"\n{Color.BOLD}{Color.MAGENTA}=== Testing Integration Points ==={Color.END}")

        try:
            # Test data flow: Invoice → E-Invoice Document
            print(f"{Color.BLUE}Testing Invoice → E-Invoice Document flow...{Color.END}")
            if self.test_invoice_id and self.test_document_id:
                invoice_data = self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'account.move', 'read',
                    [[self.test_invoice_id]],
                    {'fields': ['partner_id', 'amount_total']}
                )[0]

                doc_data = self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'l10n_cr.einvoice.document', 'read',
                    [[self.test_document_id]],
                    {'fields': ['invoice_id', 'partner_id']}
                )[0]

                if doc_data['invoice_id'][0] == self.test_invoice_id:
                    print(f"{Color.GREEN}✓ Invoice linked to document correctly{Color.END}")
                    self.test_results['integration_points']['invoice_document_link'] = True
                else:
                    print(f"{Color.RED}✗ Invoice-document link broken{Color.END}")
                    self.test_results['integration_points']['invoice_document_link'] = False

            # Test state management
            print(f"{Color.BLUE}Testing state management...{Color.END}")
            if self.test_document_id:
                doc_data = self.models.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD,
                    'l10n_cr.einvoice.document', 'read',
                    [[self.test_document_id]],
                    {'fields': ['state']}
                )[0]

                valid_states = ['draft', 'validated', 'signed', 'sent', 'accepted', 'rejected']
                if doc_data['state'] in valid_states:
                    print(f"{Color.GREEN}✓ Document state valid: {doc_data['state']}{Color.END}")
                    self.test_results['integration_points']['state_valid'] = True
                    self.test_results['integration_points']['current_state'] = doc_data['state']
                else:
                    print(f"{Color.RED}✗ Invalid document state: {doc_data['state']}{Color.END}")
                    self.test_results['integration_points']['state_valid'] = False

            return True

        except Exception as e:
            logger.error(f"Integration points test failed: {str(e)}", exc_info=True)
            print(f"{Color.RED}✗ Integration points test failed: {str(e)}{Color.END}")
            self.test_results['integration_points']['error'] = str(e)
            return False

    def test_file_synchronization(self):
        """
        Test that files are synchronized between both locations
        """
        print(f"\n{Color.BOLD}{Color.MAGENTA}=== Testing File Synchronization ==={Color.END}")

        base_path = '/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS'
        main_location = f'{base_path}/l10n_cr_einvoice/models'
        odoo_location = f'{base_path}/odoo/addons/l10n_cr_einvoice/models'

        required_files = [
            '__init__.py',
            'account_move.py',
            'einvoice_document.py',
            'xml_generator.py',
            'xsd_validator.py',
            'certificate_manager.py',
            'xml_signer.py',
            'hacienda_api.py',
            'res_company.py',
            'res_config_settings.py',
        ]

        phase5_files = ['qr_generator.py']

        try:
            all_synced = True

            # Check required files
            for filename in required_files:
                main_exists = os.path.exists(f'{main_location}/{filename}')
                odoo_exists = os.path.exists(f'{odoo_location}/{filename}')

                if main_exists and odoo_exists:
                    print(f"{Color.GREEN}✓ {filename} present in both locations{Color.END}")
                elif main_exists:
                    print(f"{Color.YELLOW}⚠ {filename} only in main location{Color.END}")
                    all_synced = False
                elif odoo_exists:
                    print(f"{Color.YELLOW}⚠ {filename} only in odoo location{Color.END}")
                    all_synced = False
                else:
                    print(f"{Color.RED}✗ {filename} missing from both locations{Color.END}")
                    all_synced = False

            # Check Phase 5 files
            for filename in phase5_files:
                main_exists = os.path.exists(f'{main_location}/{filename}')
                odoo_exists = os.path.exists(f'{odoo_location}/{filename}')

                if main_exists and odoo_exists:
                    print(f"{Color.GREEN}✓ [Phase 5] {filename} present in both locations{Color.END}")
                elif main_exists and not odoo_exists:
                    print(f"{Color.YELLOW}⚠ [Phase 5] {filename} needs copying to odoo location{Color.END}")
                    all_synced = False
                elif not main_exists:
                    print(f"{Color.YELLOW}⚠ [Phase 5] {filename} not yet created{Color.END}")

            self.test_results['file_sync']['all_synced'] = all_synced
            self.test_results['file_sync']['checked_files'] = len(required_files) + len(phase5_files)

            return all_synced

        except Exception as e:
            logger.error(f"File sync test failed: {str(e)}", exc_info=True)
            print(f"{Color.RED}✗ File sync test failed: {str(e)}{Color.END}")
            self.test_results['file_sync']['error'] = str(e)
            return False

    def generate_report(self):
        """
        Generate comprehensive test report
        """
        print(f"\n{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}COMPREHENSIVE E2E INTEGRATION TEST REPORT{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}")
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Summary statistics
        total_tests = 0
        passed_tests = 0

        for phase, results in self.test_results.items():
            for key, value in results.items():
                if isinstance(value, bool):
                    total_tests += 1
                    if value:
                        passed_tests += 1

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n{Color.BOLD}Summary:{Color.END}")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {Color.GREEN}{passed_tests}{Color.END}")
        print(f"  Failed: {Color.RED}{total_tests - passed_tests}{Color.END}")
        print(f"  Success Rate: {Color.BOLD}{success_rate:.1f}%{Color.END}")

        # Detailed results
        print(f"\n{Color.BOLD}Detailed Results:{Color.END}")

        for phase in ['phase_1', 'phase_2', 'phase_3', 'phase_5', 'integration_points', 'file_sync']:
            if phase in self.test_results and self.test_results[phase]:
                phase_name = phase.replace('_', ' ').title()
                print(f"\n  {Color.BOLD}{phase_name}:{Color.END}")

                for key, value in self.test_results[phase].items():
                    if isinstance(value, bool):
                        status = f"{Color.GREEN}✓ PASS{Color.END}" if value else f"{Color.RED}✗ FAIL{Color.END}"
                        print(f"    {key}: {status}")
                    elif key != 'error':
                        print(f"    {key}: {value}")

        # Save to JSON
        report_file = f'{base_path}/e2e_integration_test_results.json'
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': total_tests - passed_tests,
                    'success_rate': success_rate
                },
                'results': self.test_results
            }, f, indent=2)

        print(f"\n{Color.GREEN}Report saved to: {report_file}{Color.END}")

        # Recommendations
        print(f"\n{Color.BOLD}Recommendations:{Color.END}")

        if not self.test_results['file_sync'].get('all_synced', False):
            print(f"  {Color.YELLOW}⚠ Synchronize files between main and odoo locations{Color.END}")

        if not self.test_results['phase_3'].get('certificate_configured', False):
            print(f"  {Color.YELLOW}⚠ Configure digital certificate for signing{Color.END}")

        if not self.test_results['phase_5'].get('qr_generated', False):
            print(f"  {Color.YELLOW}⚠ Install qrcode library: pip install qrcode[pil]{Color.END}")

        if not self.test_results['phase_5'].get('pdf_template_exists', False):
            print(f"  {Color.YELLOW}⚠ Configure PDF report template{Color.END}")

        print(f"\n{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}\n")

    def run_all_tests(self):
        """
        Execute all integration tests in sequence
        """
        if not self.connect_odoo():
            return False

        # Run tests in order
        self.test_phase1_invoice_creation()
        self.test_phase2_xml_validation()
        self.test_phase3_signature_submission()
        self.test_phase5_qr_pdf_email()
        self.test_integration_points()
        self.test_file_synchronization()

        # Generate report
        self.generate_report()

        return True

if __name__ == '__main__':
    print(f"{Color.BOLD}{Color.CYAN}")
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║   Costa Rica E-Invoicing - End-to-End Integration Test Suite         ║")
    print("║   Testing complete workflow: Phase 1 → 2 → 3 → 5                     ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    print(f"{Color.END}")

    suite = IntegrationTestSuite()
    success = suite.run_all_tests()

    sys.exit(0 if success else 1)
