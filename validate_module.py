#!/usr/bin/env python3
"""
Comprehensive Module Validation Script
Validates the l10n_cr_einvoice module for production readiness

This script checks:
1. File structure and completeness
2. Python syntax validation
3. XML file validation
4. Import statements
5. Test coverage
6. Security configuration
7. Documentation completeness
8. Manifest correctness

Usage:
    python3 validate_module.py
    python3 validate_module.py --verbose
"""

import os
import sys
import ast
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict
import re

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


class ModuleValidator:
    """Validates Odoo module for production readiness"""

    def __init__(self, module_path: str, verbose: bool = False):
        self.module_path = Path(module_path)
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []

    def log(self, message: str, level: str = 'INFO'):
        """Log message with color"""
        color = {
            'INFO': BLUE,
            'PASS': GREEN,
            'FAIL': RED,
            'WARN': YELLOW
        }.get(level, '')

        symbol = {
            'PASS': '✓',
            'FAIL': '✗',
            'WARN': '⚠',
            'INFO': '•'
        }.get(level, '')

        print(f"{color}{symbol} {message}{RESET}")

    def check_file_exists(self, filepath: str) -> bool:
        """Check if a file exists"""
        path = self.module_path / filepath
        exists = path.exists()

        if not exists:
            self.errors.append(f"Missing file: {filepath}")

        return exists

    def validate_python_syntax(self, filepath: str) -> bool:
        """Validate Python file syntax"""
        path = self.module_path / filepath

        if not path.exists():
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                ast.parse(content)
            return True
        except SyntaxError as e:
            self.errors.append(f"Syntax error in {filepath}: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading {filepath}: {e}")
            return False

    def validate_xml_syntax(self, filepath: str) -> bool:
        """Validate XML file syntax"""
        path = self.module_path / filepath

        if not path.exists():
            return False

        try:
            ET.parse(path)
            return True
        except ET.ParseError as e:
            self.errors.append(f"XML error in {filepath}: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading {filepath}: {e}")
            return False

    def check_manifest(self) -> bool:
        """Validate __manifest__.py"""
        manifest_path = self.module_path / '__manifest__.py'

        if not manifest_path.exists():
            self.errors.append("Missing __manifest__.py")
            return False

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()
                manifest = ast.literal_eval(content)

            # Check required keys
            required_keys = ['name', 'version', 'depends', 'data']
            for key in required_keys:
                if key not in manifest:
                    self.errors.append(f"Missing key in manifest: {key}")
                    return False

            # Check version format
            version = manifest.get('version', '')
            if not re.match(r'^\d+\.\d+\.\d+\.\d+\.\d+$', version):
                self.warnings += 1
                self.log(f"Version format warning: {version}", 'WARN')

            # Check dependencies
            expected_deps = ['base', 'account', 'l10n_cr', 'sale', 'sale_subscription',
                           'mail', 'point_of_sale']
            missing_deps = set(expected_deps) - set(manifest.get('depends', []))
            if missing_deps:
                self.warnings += 1
                self.log(f"Missing dependencies: {missing_deps}", 'WARN')

            return True

        except Exception as e:
            self.errors.append(f"Error reading manifest: {e}")
            return False

    def count_test_files(self) -> Tuple[int, int]:
        """Count test files and estimate test count"""
        test_dir = self.module_path / 'tests'

        if not test_dir.exists():
            return 0, 0

        test_files = list(test_dir.glob('test_*.py'))
        total_tests = 0

        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Count test methods (def test_)
                    total_tests += len(re.findall(r'def test_\w+\(', content))
            except:
                pass

        return len(test_files), total_tests

    def check_security_rules(self) -> bool:
        """Check security access rules"""
        csv_path = self.module_path / 'security' / 'ir.model.access.csv'

        if not csv_path.exists():
            self.errors.append("Missing security/ir.model.access.csv")
            return False

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Should have header + rules
            if len(lines) < 2:
                self.errors.append("Security file is empty")
                return False

            # Count rules
            rule_count = len(lines) - 1  # Exclude header

            if self.verbose:
                self.log(f"Found {rule_count} security rules", 'INFO')

            return True

        except Exception as e:
            self.errors.append(f"Error reading security rules: {e}")
            return False

    def validate_file_structure(self) -> bool:
        """Validate expected file structure"""
        self.log(f"{BOLD}Validating File Structure...{RESET}", 'INFO')

        # Core files
        core_files = [
            '__init__.py',
            '__manifest__.py',
        ]

        # Model files
        model_files = [
            'models/__init__.py',
            'models/einvoice_document.py',
            'models/res_partner.py',
            'models/account_move.py',
            'models/hacienda_response_message.py',
            'models/einvoice_retry_queue.py',
            'models/pos_integration.py',
            'models/pos_offline_queue.py',
            'models/einvoice_analytics_dashboard.py',
        ]

        # View files
        view_files = [
            'views/einvoice_document_views.xml',
            'views/res_partner_views.xml',
            'views/account_move_views.xml',
            'views/hacienda_menu.xml',
            'views/hacienda_response_message_views.xml',
            'views/einvoice_retry_queue_views.xml',
            'views/pos_config_views.xml',
            'views/pos_order_views.xml',
            'views/einvoice_analytics_dashboard_views.xml',
        ]

        # Data files
        data_files = [
            'data/payment_methods.xml',
            'data/discount_codes.xml',
            'data/ciiu_codes.xml',
            'data/hacienda_sequences.xml',
            'data/email_templates.xml',
            'data/hacienda_cron_jobs.xml',
            'data/pos_sequences.xml',
            'data/report_cron_jobs.xml',
        ]

        # Security files
        security_files = [
            'security/ir.model.access.csv',
        ]

        # Test files
        test_files = [
            'tests/__init__.py',
            'tests/test_certificate_manager.py',
            'tests/test_xml_signer.py',
            'tests/test_hacienda_api.py',
            'tests/test_phase3_polling.py',
            'tests/test_pdf_generation.py',
            'tests/test_email_sending.py',
            'tests/test_pos_integration.py',
            'tests/test_dashboard_kpis.py',
        ]

        all_files = core_files + model_files + view_files + data_files + security_files + test_files

        missing = []
        for filepath in all_files:
            if not self.check_file_exists(filepath):
                missing.append(filepath)

        if missing:
            self.log(f"Missing {len(missing)} files", 'FAIL')
            self.failed += len(missing)
            if self.verbose:
                for f in missing:
                    self.log(f"  Missing: {f}", 'FAIL')
        else:
            self.log(f"All {len(all_files)} critical files present", 'PASS')
            self.passed += 1

        return len(missing) == 0

    def validate_python_files(self) -> bool:
        """Validate all Python files for syntax errors"""
        self.log(f"{BOLD}Validating Python Syntax...{RESET}", 'INFO')

        python_files = list(self.module_path.rglob('*.py'))
        valid = 0
        invalid = 0

        for py_file in python_files:
            relative_path = py_file.relative_to(self.module_path)
            if self.validate_python_syntax(str(relative_path)):
                valid += 1
            else:
                invalid += 1

        if invalid > 0:
            self.log(f"{invalid}/{len(python_files)} Python files have syntax errors", 'FAIL')
            self.failed += 1
        else:
            self.log(f"All {valid} Python files have valid syntax", 'PASS')
            self.passed += 1

        return invalid == 0

    def validate_xml_files(self) -> bool:
        """Validate all XML files for syntax errors"""
        self.log(f"{BOLD}Validating XML Syntax...{RESET}", 'INFO')

        xml_files = list(self.module_path.rglob('*.xml'))
        valid = 0
        invalid = 0

        for xml_file in xml_files:
            relative_path = xml_file.relative_to(self.module_path)
            if self.validate_xml_syntax(str(relative_path)):
                valid += 1
            else:
                invalid += 1

        if invalid > 0:
            self.log(f"{invalid}/{len(xml_files)} XML files have syntax errors", 'FAIL')
            self.failed += 1
        else:
            self.log(f"All {valid} XML files have valid syntax", 'PASS')
            self.passed += 1

        return invalid == 0

    def validate_tests(self) -> bool:
        """Validate test coverage"""
        self.log(f"{BOLD}Validating Test Coverage...{RESET}", 'INFO')

        test_file_count, test_count = self.count_test_files()

        if test_file_count == 0:
            self.log("No test files found", 'FAIL')
            self.failed += 1
            return False

        if test_count < 100:
            self.log(f"Only {test_count} tests found (expected 100+)", 'WARN')
            self.warnings += 1
        else:
            self.log(f"Found {test_file_count} test files with {test_count} tests", 'PASS')
            self.passed += 1

        return test_count >= 100

    def validate_documentation(self) -> bool:
        """Check for documentation files"""
        self.log(f"{BOLD}Validating Documentation...{RESET}", 'INFO')

        # Look in parent directory for phase documentation
        parent_dir = self.module_path.parent

        doc_patterns = [
            'PHASE*-IMPLEMENTATION-COMPLETE.md',
            'PHASE*-QUICK-REFERENCE.md',
            'PHASE*_COMPLETION_SUMMARY.md',
            'deployment/README.md',
            'deployment/QUICK_START.md',
        ]

        found_docs = 0

        # Check for phase documentation in parent
        for pattern in doc_patterns[:3]:
            matching = list(parent_dir.glob(pattern))
            found_docs += len(matching)

        # Check deployment docs
        for pattern in doc_patterns[3:]:
            if (self.module_path / pattern).exists():
                found_docs += 1

        if found_docs >= 10:
            self.log(f"Found {found_docs} documentation files", 'PASS')
            self.passed += 1
            return True
        else:
            self.log(f"Only {found_docs} documentation files found (expected 10+)", 'WARN')
            self.warnings += 1
            return False

    def validate_deployment_files(self) -> bool:
        """Check deployment infrastructure"""
        self.log(f"{BOLD}Validating Deployment Infrastructure...{RESET}", 'INFO')

        deployment_files = [
            'docker/Dockerfile',
            'docker/docker-compose.yml',
            'docker/nginx.conf',
            'deployment/smoke_tests.py',
            'scripts/deploy_production.sh',
            'scripts/backup_database.sh',
            'monitoring/prometheus.yml',
        ]

        found = 0
        for filepath in deployment_files:
            if self.check_file_exists(filepath):
                found += 1

        if found >= len(deployment_files) - 1:  # Allow 1 missing
            self.log(f"Found {found}/{len(deployment_files)} deployment files", 'PASS')
            self.passed += 1
            return True
        else:
            self.log(f"Only {found}/{len(deployment_files)} deployment files found", 'WARN')
            self.warnings += 1
            return False

    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}  Costa Rica E-Invoicing Module Validation{RESET}")
        print(f"{BOLD}  Module: l10n_cr_einvoice{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")

        # Run validations
        self.check_manifest()
        self.validate_file_structure()
        self.validate_python_files()
        self.validate_xml_files()
        self.check_security_rules()
        self.validate_tests()
        self.validate_documentation()
        self.validate_deployment_files()

        # Print summary
        self.print_summary()

        return self.failed == 0

    def print_summary(self):
        """Print validation summary"""
        total_checks = self.passed + self.failed
        pass_rate = (self.passed / total_checks * 100) if total_checks > 0 else 0

        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}  Validation Summary{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")

        self.log(f"Total Checks: {total_checks}", 'INFO')
        self.log(f"Passed: {self.passed} ({pass_rate:.1f}%)", 'PASS')

        if self.failed > 0:
            self.log(f"Failed: {self.failed}", 'FAIL')

        if self.warnings > 0:
            self.log(f"Warnings: {self.warnings}", 'WARN')

        # Print errors
        if self.errors and self.verbose:
            print(f"\n{RED}{BOLD}Errors:{RESET}")
            for error in self.errors[:10]:  # Show first 10
                print(f"  {RED}• {error}{RESET}")
            if len(self.errors) > 10:
                print(f"  {RED}... and {len(self.errors) - 10} more{RESET}")

        print(f"\n{BOLD}{'='*60}{RESET}")

        if self.failed == 0:
            print(f"{GREEN}{BOLD}✓ Module validation PASSED!{RESET}")
            print(f"{GREEN}Module is ready for production deployment.{RESET}")
        else:
            print(f"{RED}{BOLD}✗ Module validation FAILED!{RESET}")
            print(f"{RED}Please fix the errors before deploying.{RESET}")

        print(f"{BOLD}{'='*60}{RESET}\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Validate e-invoicing module')
    parser.add_argument('--module-path', default='l10n_cr_einvoice',
                       help='Path to module directory')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    args = parser.parse_args()

    validator = ModuleValidator(args.module_path, args.verbose)
    success = validator.run_all_validations()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
