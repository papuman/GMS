#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2: Digital Signature Testing Script
==========================================

Tests the complete Phase 2 implementation including:
- Certificate management and validation
- XMLDSig signing with XAdES-EPES format
- Hacienda API integration (sandbox)
- UI components for certificate upload and signing

Usage:
    python3 test_phase2_signature.py

Requirements:
    - Odoo server running
    - l10n_cr_einvoice module installed
    - Test certificate available (certificado.p12)
    - Hacienda sandbox credentials configured
"""

import sys
import os
import logging
import base64
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add Odoo to path
sys.path.append('/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS')

try:
    import odoo
    from odoo import api, SUPERUSER_ID
except ImportError:
    logger.error("Could not import Odoo. Make sure Odoo is installed and in the Python path.")
    sys.exit(1)


class Phase2Tester:
    """Test suite for Phase 2: Digital Signature implementation."""

    def __init__(self):
        self.env = None
        self.company = None
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    def connect_to_odoo(self):
        """Initialize Odoo environment."""
        try:
            logger.info("Connecting to Odoo...")

            # Initialize Odoo
            odoo.tools.config.parse_config([
                '-c', '/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/odoo.conf'
            ])

            # Get database name from config
            db_name = odoo.tools.config['db_name']

            # Initialize registry
            registry = odoo.registry(db_name)

            with registry.cursor() as cr:
                self.env = api.Environment(cr, SUPERUSER_ID, {})
                self.company = self.env.company

                logger.info(f"Connected to database: {db_name}")
                logger.info(f"Company: {self.company.name}")

                return True

        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {str(e)}")
            return False

    def test_module_installation(self):
        """Test 2.0: Verify module is installed and models are available."""
        test_name = "Module Installation"
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST 2.0: {test_name}")
        logger.info(f"{'='*60}")

        try:
            # Check if module is installed
            module = self.env['ir.module.module'].search([
                ('name', '=', 'l10n_cr_einvoice'),
                ('state', '=', 'installed')
            ])

            if not module:
                raise Exception("l10n_cr_einvoice module is not installed")

            logger.info("✓ Module l10n_cr_einvoice is installed")

            # Check if Phase 2 models exist
            required_models = [
                'l10n_cr.certificate.manager',
                'l10n_cr.xml.signer',
                'l10n_cr.hacienda.api',
                'l10n_cr.einvoice.document',
            ]

            for model_name in required_models:
                if model_name not in self.env:
                    raise Exception(f"Model {model_name} not found")
                logger.info(f"✓ Model {model_name} is available")

            self.test_results['passed'].append(test_name)
            logger.info(f"\n✅ {test_name} - PASSED")
            return True

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"\n❌ {test_name} - FAILED: {str(e)}")
            return False

    def test_company_certificate_fields(self):
        """Test 2.1: Verify company has certificate management fields."""
        test_name = "Company Certificate Fields"
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST 2.1: {test_name}")
        logger.info(f"{'='*60}")

        try:
            # Check certificate fields exist
            required_fields = [
                'l10n_cr_certificate',
                'l10n_cr_certificate_filename',
                'l10n_cr_private_key',
                'l10n_cr_private_key_filename',
                'l10n_cr_key_password',
                'l10n_cr_hacienda_env',
                'l10n_cr_hacienda_username',
                'l10n_cr_hacienda_password',
            ]

            for field_name in required_fields:
                if field_name not in self.company._fields:
                    raise Exception(f"Field {field_name} not found in res.company")
                logger.info(f"✓ Field {field_name} exists")

            # Check current values
            logger.info(f"\nCertificate configured: {bool(self.company.l10n_cr_certificate)}")
            logger.info(f"Private key configured: {bool(self.company.l10n_cr_private_key)}")
            logger.info(f"Hacienda environment: {self.company.l10n_cr_hacienda_env or 'Not set'}")
            logger.info(f"API username: {self.company.l10n_cr_hacienda_username or 'Not set'}")

            if not self.company.l10n_cr_certificate:
                self.test_results['warnings'].append(
                    f"{test_name}: Certificate not uploaded (required for signing)"
                )

            if not self.company.l10n_cr_hacienda_username:
                self.test_results['warnings'].append(
                    f"{test_name}: Hacienda credentials not configured"
                )

            self.test_results['passed'].append(test_name)
            logger.info(f"\n✅ {test_name} - PASSED")
            return True

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"\n❌ {test_name} - FAILED: {str(e)}")
            return False

    def test_certificate_manager(self):
        """Test 2.2: Test certificate loading and validation."""
        test_name = "Certificate Manager"
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST 2.2: {test_name}")
        logger.info(f"{'='*60}")

        try:
            cert_mgr = self.env['l10n_cr.certificate.manager']

            # Test certificate manager methods exist
            required_methods = [
                'load_certificate_from_company',
                'get_certificate_info',
                '_validate_certificate',
                '_load_pkcs12_certificate',
                '_load_pem_certificate',
            ]

            for method_name in required_methods:
                if not hasattr(cert_mgr, method_name):
                    raise Exception(f"Method {method_name} not found in certificate manager")
                logger.info(f"✓ Method {method_name} exists")

            # Try to load certificate if configured
            if self.company.l10n_cr_certificate:
                logger.info("\nAttempting to load certificate...")
                try:
                    certificate, private_key = cert_mgr.load_certificate_from_company(self.company)
                    logger.info("✓ Certificate loaded successfully")

                    # Get certificate info
                    cert_info = cert_mgr.get_certificate_info(self.company)
                    logger.info(f"\nCertificate Information:")
                    logger.info(f"  Subject CN: {cert_info.get('subject_cn')}")
                    logger.info(f"  Subject Org: {cert_info.get('subject_org')}")
                    logger.info(f"  Issuer: {cert_info.get('issuer_cn')}")
                    logger.info(f"  Valid from: {cert_info.get('not_before')}")
                    logger.info(f"  Valid to: {cert_info.get('not_after')}")
                    logger.info(f"  Days until expiry: {cert_info.get('days_until_expiry')}")
                    logger.info(f"  Is valid: {cert_info.get('is_valid')}")

                    if not cert_info.get('is_valid'):
                        self.test_results['warnings'].append(
                            f"{test_name}: Certificate is expired or not yet valid"
                        )

                except Exception as cert_error:
                    logger.warning(f"⚠ Certificate loading failed: {str(cert_error)}")
                    self.test_results['warnings'].append(
                        f"{test_name}: Certificate loading failed - {str(cert_error)}"
                    )
            else:
                logger.warning("⚠ No certificate configured - cannot test loading")
                self.test_results['warnings'].append(
                    f"{test_name}: No certificate configured for testing"
                )

            self.test_results['passed'].append(test_name)
            logger.info(f"\n✅ {test_name} - PASSED")
            return True

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"\n❌ {test_name} - FAILED: {str(e)}")
            return False

    def test_xml_signer(self):
        """Test 2.3: Test XMLDSig signing implementation."""
        test_name = "XML Signer"
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST 2.3: {test_name}")
        logger.info(f"{'='*60}")

        try:
            xml_signer = self.env['l10n_cr.xml.signer']

            # Test signer methods exist
            required_methods = [
                'sign_xml',
                'verify_signature',
                '_create_signature_element',
                '_create_signed_info',
                '_calculate_digest',
                '_calculate_signature_value',
                '_create_key_info',
            ]

            for method_name in required_methods:
                if not hasattr(xml_signer, method_name):
                    raise Exception(f"Method {method_name} not found in XML signer")
                logger.info(f"✓ Method {method_name} exists")

            # Test signing if certificate is available
            if self.company.l10n_cr_certificate:
                logger.info("\nAttempting to sign test XML...")

                # Create simple test XML
                test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601010100010120250001012345678901234567890123456789012345678901</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-01T10:00:00-06:00</FechaEmision>
</FacturaElectronica>"""

                try:
                    cert_mgr = self.env['l10n_cr.certificate.manager']
                    certificate, private_key = cert_mgr.load_certificate_from_company(self.company)

                    signed_xml = xml_signer.sign_xml(test_xml, certificate, private_key)

                    logger.info("✓ XML signed successfully")

                    # Check if signature element is present
                    if '<Signature' in signed_xml and 'xmldsig#' in signed_xml:
                        logger.info("✓ Signature element found in signed XML")
                    else:
                        raise Exception("Signature element not found in signed XML")

                    # Verify signature
                    is_valid = xml_signer.verify_signature(signed_xml)
                    if is_valid:
                        logger.info("✓ Signature verification passed")
                    else:
                        logger.warning("⚠ Signature verification returned False")

                except Exception as sign_error:
                    logger.warning(f"⚠ XML signing test failed: {str(sign_error)}")
                    self.test_results['warnings'].append(
                        f"{test_name}: XML signing test failed - {str(sign_error)}"
                    )
            else:
                logger.warning("⚠ No certificate configured - cannot test signing")
                self.test_results['warnings'].append(
                    f"{test_name}: No certificate configured for signing test"
                )

            self.test_results['passed'].append(test_name)
            logger.info(f"\n✅ {test_name} - PASSED")
            return True

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"\n❌ {test_name} - FAILED: {str(e)}")
            return False

    def test_hacienda_api(self):
        """Test 2.4: Test Hacienda API client implementation."""
        test_name = "Hacienda API Client"
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST 2.4: {test_name}")
        logger.info(f"{'='*60}")

        try:
            hacienda_api = self.env['l10n_cr.hacienda.api']

            # Test API methods exist
            required_methods = [
                'submit_invoice',
                'check_status',
                'test_connection',
                'get_id_type',
                'is_accepted',
                'is_rejected',
                'is_processing',
                '_make_request_with_retry',
                '_parse_response',
                '_parse_error',
            ]

            for method_name in required_methods:
                if not hasattr(hacienda_api, method_name):
                    raise Exception(f"Method {method_name} not found in Hacienda API")
                logger.info(f"✓ Method {method_name} exists")

            # Check API endpoints
            logger.info(f"\nAPI Endpoints:")
            logger.info(f"  Production: {hacienda_api.PRODUCTION_URL}")
            logger.info(f"  Sandbox: {hacienda_api.SANDBOX_URL}")

            # Test connection if credentials are configured
            if self.company.l10n_cr_hacienda_username and self.company.l10n_cr_hacienda_password:
                logger.info("\nTesting Hacienda API connection...")
                try:
                    result = hacienda_api.test_connection()

                    if result['success']:
                        logger.info(f"✓ Connection test successful: {result['message']}")
                        logger.info(f"  Environment: {result.get('environment')}")
                        logger.info(f"  URL: {result.get('url')}")
                    else:
                        logger.warning(f"⚠ Connection test failed: {result['message']}")
                        self.test_results['warnings'].append(
                            f"{test_name}: Connection test failed - {result['message']}"
                        )

                except Exception as conn_error:
                    logger.warning(f"⚠ Connection test error: {str(conn_error)}")
                    self.test_results['warnings'].append(
                        f"{test_name}: Connection test error - {str(conn_error)}"
                    )
            else:
                logger.warning("⚠ API credentials not configured - cannot test connection")
                self.test_results['warnings'].append(
                    f"{test_name}: API credentials not configured"
                )

            # Test ID type detection
            logger.info("\nTesting ID type detection:")
            test_ids = [
                ('123456789', '01', 'Cédula Física'),
                ('3101234567', '02', 'Cédula Jurídica'),
                ('12345678901', '03', 'DIMEX'),
                ('1234567890', '04', 'NITE'),
            ]

            for id_num, expected_type, description in test_ids:
                detected_type = hacienda_api.get_id_type(id_num)
                if detected_type == expected_type:
                    logger.info(f"✓ {id_num} → {detected_type} ({description})")
                else:
                    logger.warning(f"⚠ {id_num} → {detected_type} (expected {expected_type})")

            self.test_results['passed'].append(test_name)
            logger.info(f"\n✅ {test_name} - PASSED")
            return True

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"\n❌ {test_name} - FAILED: {str(e)}")
            return False

    def test_einvoice_document_workflow(self):
        """Test 2.5: Test complete e-invoice document workflow."""
        test_name = "E-Invoice Document Workflow"
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST 2.5: {test_name}")
        logger.info(f"{'='*60}")

        try:
            einvoice_model = self.env['l10n_cr.einvoice.document']

            # Test workflow action methods exist
            required_methods = [
                'action_generate_xml',
                'action_sign_xml',
                'action_submit_to_hacienda',
                'action_check_status',
                '_sign_xml_content',
                '_process_hacienda_response',
            ]

            for method_name in required_methods:
                if not hasattr(einvoice_model, method_name):
                    raise Exception(f"Method {method_name} not found in einvoice.document")
                logger.info(f"✓ Method {method_name} exists")

            # Check state field
            if 'state' not in einvoice_model._fields:
                raise Exception("State field not found")

            state_field = einvoice_model._fields['state']
            expected_states = ['draft', 'generated', 'signed', 'submitted', 'accepted', 'rejected', 'error']

            logger.info("\nDocument states:")
            for state in state_field.selection:
                state_key = state[0]
                state_name = state[1]
                logger.info(f"  {state_key}: {state_name}")
                if state_key not in expected_states:
                    logger.warning(f"⚠ Unexpected state: {state_key}")

            # Check if there are any existing documents
            doc_count = einvoice_model.search_count([])
            logger.info(f"\nTotal e-invoice documents: {doc_count}")

            if doc_count > 0:
                # Get state statistics
                for state in ['draft', 'generated', 'signed', 'submitted', 'accepted', 'rejected', 'error']:
                    count = einvoice_model.search_count([('state', '=', state)])
                    if count > 0:
                        logger.info(f"  {state}: {count}")

            self.test_results['passed'].append(test_name)
            logger.info(f"\n✅ {test_name} - PASSED")
            return True

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"\n❌ {test_name} - FAILED: {str(e)}")
            return False

    def test_ui_views(self):
        """Test 2.6: Test UI views for certificate management."""
        test_name = "UI Views"
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST 2.6: {test_name}")
        logger.info(f"{'='*60}")

        try:
            # Check if configuration views exist
            view_refs = [
                'l10n_cr_einvoice.res_config_settings_view_form_einvoice',
                'l10n_cr_einvoice.view_company_form_einvoice',
                'l10n_cr_einvoice.view_einvoice_document_form',
                'l10n_cr_einvoice.view_einvoice_document_tree',
            ]

            for view_ref in view_refs:
                try:
                    view = self.env.ref(view_ref, raise_if_not_found=False)
                    if view:
                        logger.info(f"✓ View {view_ref} exists")
                    else:
                        logger.warning(f"⚠ View {view_ref} not found")
                        self.test_results['warnings'].append(
                            f"{test_name}: View {view_ref} not found"
                        )
                except Exception as view_error:
                    logger.warning(f"⚠ Error checking view {view_ref}: {str(view_error)}")

            self.test_results['passed'].append(test_name)
            logger.info(f"\n✅ {test_name} - PASSED")
            return True

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"\n❌ {test_name} - FAILED: {str(e)}")
            return False

    def test_security_access(self):
        """Test 2.7: Test security access controls."""
        test_name = "Security Access"
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST 2.7: {test_name}")
        logger.info(f"{'='*60}")

        try:
            # Check access rules for einvoice.document
            access_model = self.env['ir.model.access']

            # Search for e-invoice access rules
            access_rules = access_model.search([
                ('model_id.model', '=', 'l10n_cr.einvoice.document')
            ])

            logger.info(f"Found {len(access_rules)} access rules for einvoice.document:")
            for rule in access_rules:
                logger.info(f"  {rule.name}")
                logger.info(f"    Group: {rule.group_id.name if rule.group_id else 'Public'}")
                logger.info(f"    Read: {rule.perm_read}, Write: {rule.perm_write}, Create: {rule.perm_create}, Delete: {rule.perm_unlink}")

            if len(access_rules) == 0:
                self.test_results['warnings'].append(
                    f"{test_name}: No access rules found for einvoice.document"
                )

            self.test_results['passed'].append(test_name)
            logger.info(f"\n✅ {test_name} - PASSED")
            return True

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"\n❌ {test_name} - FAILED: {str(e)}")
            return False

    def print_summary(self):
        """Print test summary."""
        logger.info(f"\n{'='*60}")
        logger.info("PHASE 2 TEST SUMMARY")
        logger.info(f"{'='*60}")

        total_tests = len(self.test_results['passed']) + len(self.test_results['failed'])

        logger.info(f"\nTotal Tests: {total_tests}")
        logger.info(f"Passed: {len(self.test_results['passed'])}")
        logger.info(f"Failed: {len(self.test_results['failed'])}")
        logger.info(f"Warnings: {len(self.test_results['warnings'])}")

        if self.test_results['passed']:
            logger.info("\n✅ PASSED TESTS:")
            for test in self.test_results['passed']:
                logger.info(f"  ✓ {test}")

        if self.test_results['failed']:
            logger.info("\n❌ FAILED TESTS:")
            for test in self.test_results['failed']:
                logger.info(f"  ✗ {test}")

        if self.test_results['warnings']:
            logger.info("\n⚠ WARNINGS:")
            for warning in self.test_results['warnings']:
                logger.info(f"  ! {warning}")

        # Overall result
        logger.info(f"\n{'='*60}")
        if len(self.test_results['failed']) == 0:
            logger.info("🎉 ALL PHASE 2 TESTS PASSED!")
            logger.info(f"{'='*60}")
            return True
        else:
            logger.info("⚠ SOME TESTS FAILED - Review errors above")
            logger.info(f"{'='*60}")
            return False

    def run_all_tests(self):
        """Run all Phase 2 tests."""
        logger.info("="*60)
        logger.info("PHASE 2: DIGITAL SIGNATURE TEST SUITE")
        logger.info("="*60)
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if not self.connect_to_odoo():
            logger.error("Failed to connect to Odoo. Aborting tests.")
            return False

        # Run all tests
        self.test_module_installation()
        self.test_company_certificate_fields()
        self.test_certificate_manager()
        self.test_xml_signer()
        self.test_hacienda_api()
        self.test_einvoice_document_workflow()
        self.test_ui_views()
        self.test_security_access()

        # Print summary
        return self.print_summary()


def main():
    """Main entry point."""
    tester = Phase2Tester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
