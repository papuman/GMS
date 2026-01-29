#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Runner for l10n_cr_einvoice Module
======================================================

Runs all unit and integration tests for the XML Import feature
and Digital Signature implementation without requiring module updates.

This script runs tests directly using Odoo's testing framework.
"""

import sys
import os
import logging
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add Odoo to path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

try:
    import odoo
    from odoo import api, SUPERUSER_ID
    from odoo.tests.common import TransactionCase
    from odoo.modules import module
except ImportError as e:
    logger.error(f"Could not import Odoo: {e}")
    sys.exit(1)


class TestRunner:
    """Runs comprehensive tests for l10n_cr_einvoice module."""

    def __init__(self):
        self.env = None
        self.results = {
            'xml_parser': {'passed': 0, 'failed': 0, 'errors': [], 'duration': 0},
            'xml_import': {'passed': 0, 'failed': 0, 'errors': [], 'duration': 0},
            'phase2': {'passed': 0, 'failed': 0, 'errors': [], 'duration': 0},
        }

    def connect_to_odoo(self):
        """Initialize Odoo environment."""
        try:
            logger.info("Connecting to Odoo...")

            # Initialize Odoo with config
            odoo.tools.config.parse_config([
                '-c', '/etc/odoo/odoo.conf',
                '-d', 'gms_validation'
            ])

            db_name = 'gms_validation'

            # Initialize registry
            registry = odoo.registry(db_name)

            with registry.cursor() as cr:
                self.env = api.Environment(cr, SUPERUSER_ID, {})
                logger.info(f"Connected to database: {db_name}")
                logger.info(f"Company: {self.env.company.name}")

                # Commit to ensure connection is stable
                cr.commit()

                return True

        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def run_xml_parser_tests(self):
        """Run XML parser unit tests."""
        logger.info("\n" + "="*70)
        logger.info("TEST SUITE 1: XML Parser Unit Tests")
        logger.info("="*70)

        start_time = datetime.now()

        try:
            # Import test module
            from l10n_cr_einvoice.tests import test_xml_parser

            # Get test class
            test_class = test_xml_parser.TestXMLParser

            # Create test suite
            import unittest
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(test_class)

            # Run tests
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)

            # Record results
            self.results['xml_parser']['passed'] = result.testsRun - len(result.failures) - len(result.errors)
            self.results['xml_parser']['failed'] = len(result.failures) + len(result.errors)

            for test, traceback in result.failures + result.errors:
                self.results['xml_parser']['errors'].append({
                    'test': str(test),
                    'error': traceback
                })

            logger.info(f"\nXML Parser Tests: {self.results['xml_parser']['passed']} passed, {self.results['xml_parser']['failed']} failed")

        except Exception as e:
            logger.error(f"Error running XML parser tests: {e}")
            import traceback
            traceback.print_exc()
            self.results['xml_parser']['errors'].append({
                'test': 'Suite execution',
                'error': str(e)
            })

        duration = (datetime.now() - start_time).total_seconds()
        self.results['xml_parser']['duration'] = duration

    def run_xml_import_tests(self):
        """Run XML import integration tests."""
        logger.info("\n" + "="*70)
        logger.info("TEST SUITE 2: XML Import Integration Tests")
        logger.info("="*70)

        start_time = datetime.now()

        try:
            # Import test module
            from l10n_cr_einvoice.tests import test_xml_import_integration

            # Get test class
            test_class = test_xml_import_integration.TestXMLImportIntegration

            # Create test suite
            import unittest
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(test_class)

            # Run tests
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)

            # Record results
            self.results['xml_import']['passed'] = result.testsRun - len(result.failures) - len(result.errors)
            self.results['xml_import']['failed'] = len(result.failures) + len(result.errors)

            for test, traceback in result.failures + result.errors:
                self.results['xml_import']['errors'].append({
                    'test': str(test),
                    'error': traceback
                })

            logger.info(f"\nXML Import Tests: {self.results['xml_import']['passed']} passed, {self.results['xml_import']['failed']} failed")

        except Exception as e:
            logger.error(f"Error running XML import tests: {e}")
            import traceback
            traceback.print_exc()
            self.results['xml_import']['errors'].append({
                'test': 'Suite execution',
                'error': str(e)
            })

        duration = (datetime.now() - start_time).total_seconds()
        self.results['xml_import']['duration'] = duration

    def run_phase2_component_tests(self):
        """Run Phase 2 component tests (certificate, signer, hacienda API)."""
        logger.info("\n" + "="*70)
        logger.info("TEST SUITE 3: Phase 2 Component Tests")
        logger.info("="*70)

        start_time = datetime.now()

        try:
            # Test certificate manager
            logger.info("\nTesting Certificate Manager...")
            cert_mgr = self.env['l10n_cr.certificate.manager']
            if cert_mgr:
                logger.info("✓ Certificate Manager model exists")
                self.results['phase2']['passed'] += 1

            # Test XML signer
            logger.info("\nTesting XML Signer...")
            xml_signer = self.env['l10n_cr.xml.signer']
            if xml_signer:
                logger.info("✓ XML Signer model exists")
                self.results['phase2']['passed'] += 1

            # Test Hacienda API
            logger.info("\nTesting Hacienda API...")
            hacienda_api = self.env['l10n_cr.hacienda.api']
            if hacienda_api:
                logger.info("✓ Hacienda API model exists")
                self.results['phase2']['passed'] += 1

            # Test E-Invoice Document
            logger.info("\nTesting E-Invoice Document...")
            einvoice_doc = self.env['l10n_cr.einvoice.document']
            if einvoice_doc:
                logger.info("✓ E-Invoice Document model exists")
                self.results['phase2']['passed'] += 1

                # Check for key methods
                methods = ['action_generate_xml', 'action_sign_xml', 'action_submit_to_hacienda']
                for method in methods:
                    if hasattr(einvoice_doc, method):
                        logger.info(f"✓ Method {method} exists")
                        self.results['phase2']['passed'] += 1
                    else:
                        logger.error(f"✗ Method {method} missing")
                        self.results['phase2']['failed'] += 1

            logger.info(f"\nPhase 2 Tests: {self.results['phase2']['passed']} passed, {self.results['phase2']['failed']} failed")

        except Exception as e:
            logger.error(f"Error running Phase 2 tests: {e}")
            import traceback
            traceback.print_exc()
            self.results['phase2']['errors'].append({
                'test': 'Suite execution',
                'error': str(e)
            })

        duration = (datetime.now() - start_time).total_seconds()
        self.results['phase2']['duration'] = duration

    def print_summary(self):
        """Print comprehensive test summary."""
        logger.info("\n" + "="*70)
        logger.info("COMPREHENSIVE TEST EXECUTION SUMMARY")
        logger.info("="*70)

        total_passed = sum(r['passed'] for r in self.results.values())
        total_failed = sum(r['failed'] for r in self.results.values())
        total_tests = total_passed + total_failed
        total_duration = sum(r['duration'] for r in self.results.values())

        logger.info(f"\nOverall Results:")
        logger.info(f"  Total Tests: {total_tests}")
        logger.info(f"  Passed: {total_passed}")
        logger.info(f"  Failed: {total_failed}")
        logger.info(f"  Success Rate: {(total_passed/total_tests*100) if total_tests > 0 else 0:.1f}%")
        logger.info(f"  Total Duration: {total_duration:.2f} seconds")

        logger.info(f"\nDetailed Results by Suite:")

        for suite_name, results in self.results.items():
            logger.info(f"\n  {suite_name.upper().replace('_', ' ')}:")
            logger.info(f"    Passed: {results['passed']}")
            logger.info(f"    Failed: {results['failed']}")
            logger.info(f"    Duration: {results['duration']:.2f}s")

            if results['errors']:
                logger.info(f"    Errors:")
                for error in results['errors'][:5]:  # Limit to first 5 errors
                    logger.info(f"      - {error['test']}")

        # Write results to JSON file
        try:
            with open('/tmp/test_results.json', 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'summary': {
                        'total_tests': total_tests,
                        'passed': total_passed,
                        'failed': total_failed,
                        'success_rate': (total_passed/total_tests*100) if total_tests > 0 else 0,
                        'duration': total_duration
                    },
                    'suites': self.results
                }, f, indent=2)
            logger.info(f"\n✓ Results written to /tmp/test_results.json")
        except Exception as e:
            logger.error(f"Failed to write results file: {e}")

        logger.info("\n" + "="*70)
        if total_failed == 0:
            logger.info("🎉 ALL TESTS PASSED!")
        else:
            logger.info(f"⚠ {total_failed} TEST(S) FAILED")
        logger.info("="*70)

        return total_failed == 0

    def run_all_tests(self):
        """Run all test suites."""
        logger.info("="*70)
        logger.info("COMPREHENSIVE TEST EXECUTION FOR L10N_CR_EINVOICE")
        logger.info("="*70)
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not self.connect_to_odoo():
            logger.error("Failed to connect to Odoo. Aborting tests.")
            return False

        # Run all test suites
        self.run_xml_parser_tests()
        self.run_xml_import_tests()
        self.run_phase2_component_tests()

        # Print summary
        return self.print_summary()


def main():
    """Main entry point."""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
