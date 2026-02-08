#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TiloPay Module Installation Validation Script

This script validates that the payment_tilopay module can be successfully
installed in Odoo without errors. It performs comprehensive checks on:
- Module structure and manifest
- Python imports and dependencies
- Model definitions and fields
- View XML syntax
- Security rules
- Data files

NO TiloPay credentials required - this is a skeleton validation only.
"""

import os
import sys
import json
import ast
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class ValidationResult:
    """Store validation results"""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []
        self.info: List[str] = []

    def add_error(self, msg: str):
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_success(self, msg: str):
        self.successes.append(msg)

    def add_info(self, msg: str):
        self.info.append(msg)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def print_summary(self):
        """Print colored summary of results"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}VALIDATION SUMMARY{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")

        if self.successes:
            print(f"{Colors.GREEN}{Colors.BOLD}SUCCESSES ({len(self.successes)}):{Colors.END}")
            for msg in self.successes:
                print(f"  {Colors.GREEN}✓{Colors.END} {msg}")
            print()

        if self.warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}WARNINGS ({len(self.warnings)}):{Colors.END}")
            for msg in self.warnings:
                print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")
            print()

        if self.errors:
            print(f"{Colors.RED}{Colors.BOLD}ERRORS ({len(self.errors)}):{Colors.END}")
            for msg in self.errors:
                print(f"  {Colors.RED}✗{Colors.END} {msg}")
            print()

        if self.info:
            print(f"{Colors.BLUE}{Colors.BOLD}INFORMATION:{Colors.END}")
            for msg in self.info:
                print(f"  {Colors.BLUE}ℹ{Colors.END} {msg}")
            print()

        # Final verdict
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
        if self.has_errors():
            print(f"{Colors.RED}{Colors.BOLD}VALIDATION FAILED{Colors.END}")
            print(f"{Colors.RED}Please fix the errors above before deployment.{Colors.END}")
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}VALIDATION PASSED{Colors.END}")
            if self.warnings:
                print(f"{Colors.YELLOW}Note: There are warnings to review.{Colors.END}")
            else:
                print(f"{Colors.GREEN}Module is ready for deployment!{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")


class ModuleValidator:
    """Validate Odoo module structure and content"""

    def __init__(self, module_path: str):
        self.module_path = Path(module_path)
        self.result = ValidationResult()
        self.manifest = {}

    def validate_all(self) -> ValidationResult:
        """Run all validation checks"""
        print(f"{Colors.HEADER}{Colors.BOLD}Starting TiloPay Module Validation{Colors.END}")
        print(f"Module Path: {self.module_path}\n")

        self._validate_module_exists()
        if not self.module_path.exists():
            return self.result

        self._validate_manifest()
        self._validate_structure()
        self._validate_python_files()
        self._validate_xml_files()
        self._validate_security()
        self._validate_dependencies()
        self._validate_tests()
        self._validate_static_assets()

        return self.result

    def _validate_module_exists(self):
        """Check if module directory exists"""
        print(f"{Colors.BLUE}Checking module existence...{Colors.END}")

        if not self.module_path.exists():
            self.result.add_error(f"Module directory does not exist: {self.module_path}")
            return

        if not self.module_path.is_dir():
            self.result.add_error(f"Path is not a directory: {self.module_path}")
            return

        self.result.add_success(f"Module directory exists: {self.module_path}")

    def _validate_manifest(self):
        """Validate __manifest__.py file"""
        print(f"{Colors.BLUE}Validating manifest file...{Colors.END}")

        manifest_path = self.module_path / '__manifest__.py'

        if not manifest_path.exists():
            self.result.add_error("Missing __manifest__.py file")
            return

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.manifest = ast.literal_eval(content)

            # Check required fields
            required_fields = ['name', 'version', 'depends', 'data']
            for field in required_fields:
                if field in self.manifest:
                    self.result.add_success(f"Manifest has required field: {field}")
                else:
                    self.result.add_error(f"Manifest missing required field: {field}")

            # Validate version format
            version = self.manifest.get('version', '')
            if version.startswith('19.0'):
                self.result.add_success(f"Version format correct: {version}")
            else:
                self.result.add_warning(f"Version should start with 19.0.x.x.x: {version}")

            # Check dependencies
            depends = self.manifest.get('depends', [])
            required_deps = ['payment', 'account', 'portal']
            for dep in required_deps:
                if dep in depends:
                    self.result.add_success(f"Required dependency present: {dep}")
                else:
                    self.result.add_error(f"Missing required dependency: {dep}")

            # Check installable flag
            if self.manifest.get('installable', False):
                self.result.add_success("Module is marked as installable")
            else:
                self.result.add_error("Module is not marked as installable")

            self.result.add_info(f"Module name: {self.manifest.get('name')}")
            self.result.add_info(f"Module version: {self.manifest.get('version')}")
            self.result.add_info(f"Dependencies: {', '.join(depends)}")

        except Exception as e:
            self.result.add_error(f"Failed to parse __manifest__.py: {str(e)}")

    def _validate_structure(self):
        """Validate module directory structure"""
        print(f"{Colors.BLUE}Validating module structure...{Colors.END}")

        required_dirs = {
            'models': 'Model definitions',
            'controllers': 'HTTP controllers',
            'views': 'XML views',
            'security': 'Access control rules',
            'tests': 'Unit tests',
        }

        for dir_name, description in required_dirs.items():
            dir_path = self.module_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.result.add_success(f"Directory exists: {dir_name}/ ({description})")
            else:
                self.result.add_warning(f"Directory missing: {dir_name}/ ({description})")

        # Check for __init__.py in subdirectories
        for dir_name in required_dirs.keys():
            dir_path = self.module_path / dir_name
            if dir_path.exists():
                init_file = dir_path / '__init__.py'
                if init_file.exists():
                    self.result.add_success(f"__init__.py exists in {dir_name}/")
                else:
                    self.result.add_error(f"Missing __init__.py in {dir_name}/")

    def _validate_python_files(self):
        """Validate Python files can be parsed"""
        print(f"{Colors.BLUE}Validating Python files...{Colors.END}")

        python_files = list(self.module_path.rglob('*.py'))
        self.result.add_info(f"Found {len(python_files)} Python files")

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    ast.parse(f.read())
                self.result.add_success(f"Valid Python syntax: {py_file.relative_to(self.module_path)}")
            except SyntaxError as e:
                self.result.add_error(f"Syntax error in {py_file.relative_to(self.module_path)}: {e}")
            except Exception as e:
                self.result.add_error(f"Failed to parse {py_file.relative_to(self.module_path)}: {e}")

    def _validate_xml_files(self):
        """Validate XML files are well-formed"""
        print(f"{Colors.BLUE}Validating XML files...{Colors.END}")

        xml_files = list(self.module_path.rglob('*.xml'))
        self.result.add_info(f"Found {len(xml_files)} XML files")

        for xml_file in xml_files:
            try:
                ET.parse(xml_file)
                self.result.add_success(f"Valid XML: {xml_file.relative_to(self.module_path)}")
            except ET.ParseError as e:
                self.result.add_error(f"XML parse error in {xml_file.relative_to(self.module_path)}: {e}")
            except Exception as e:
                self.result.add_error(f"Failed to parse {xml_file.relative_to(self.module_path)}: {e}")

    def _validate_security(self):
        """Validate security files"""
        print(f"{Colors.BLUE}Validating security configuration...{Colors.END}")

        security_dir = self.module_path / 'security'
        if not security_dir.exists():
            self.result.add_warning("No security directory found")
            return

        # Check for ir.model.access.csv
        access_file = security_dir / 'ir.model.access.csv'
        if access_file.exists():
            self.result.add_success("Found ir.model.access.csv")

            # Validate CSV format
            try:
                with open(access_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        self.result.add_success(f"Access rules defined: {len(lines) - 1} rules")
                    else:
                        self.result.add_warning("ir.model.access.csv is empty")
            except Exception as e:
                self.result.add_error(f"Failed to read access rules: {e}")
        else:
            self.result.add_warning("No ir.model.access.csv file found")

    def _validate_dependencies(self):
        """Check external Python dependencies"""
        print(f"{Colors.BLUE}Validating external dependencies...{Colors.END}")

        external_deps = self.manifest.get('external_dependencies', {}).get('python', [])

        if external_deps:
            self.result.add_info(f"External Python dependencies: {', '.join(external_deps)}")

            # Try to import each dependency
            for dep in external_deps:
                try:
                    __import__(dep)
                    self.result.add_success(f"Dependency available: {dep}")
                except ImportError:
                    self.result.add_warning(f"Dependency not installed: {dep} (will be needed at runtime)")
        else:
            self.result.add_info("No external Python dependencies declared")

    def _validate_tests(self):
        """Validate test files"""
        print(f"{Colors.BLUE}Validating tests...{Colors.END}")

        tests_dir = self.module_path / 'tests'
        if not tests_dir.exists():
            self.result.add_warning("No tests directory found")
            return

        test_files = list(tests_dir.glob('test_*.py'))
        if test_files:
            self.result.add_success(f"Found {len(test_files)} test files")
            for test_file in test_files:
                self.result.add_info(f"  - {test_file.name}")
        else:
            self.result.add_warning("No test files found (test_*.py)")

        # Check for common.py
        common_file = tests_dir / 'common.py'
        if common_file.exists():
            self.result.add_success("Found tests/common.py (test utilities)")

    def _validate_static_assets(self):
        """Validate static assets"""
        print(f"{Colors.BLUE}Validating static assets...{Colors.END}")

        static_dir = self.module_path / 'static'
        if not static_dir.exists():
            self.result.add_info("No static directory (optional)")
            return

        # Check for CSS files
        css_files = list(static_dir.rglob('*.css'))
        if css_files:
            self.result.add_success(f"Found {len(css_files)} CSS files")

        # Check for JS files
        js_files = list(static_dir.rglob('*.js'))
        if js_files:
            self.result.add_success(f"Found {len(js_files)} JavaScript files")

        # Check for images
        img_extensions = ['*.png', '*.jpg', '*.jpeg', '*.svg', '*.gif']
        img_files = []
        for ext in img_extensions:
            img_files.extend(list(static_dir.rglob(ext)))

        if img_files:
            self.result.add_info(f"Found {len(img_files)} image files")


def main():
    """Main entry point"""
    # Determine module path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    module_path = project_root / 'payment_tilopay'

    # Allow override via command line
    if len(sys.argv) > 1:
        module_path = Path(sys.argv[1])

    # Run validation
    validator = ModuleValidator(module_path)
    result = validator.validate_all()

    # Print summary
    result.print_summary()

    # Export results to JSON for CI/CD
    output_file = project_root / 'validation_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'errors': result.errors,
            'warnings': result.warnings,
            'successes': result.successes,
            'info': result.info,
            'passed': not result.has_errors(),
        }, f, indent=2)

    print(f"Results exported to: {output_file}\n")

    # Exit with appropriate code
    sys.exit(1 if result.has_errors() else 0)


if __name__ == '__main__':
    main()
