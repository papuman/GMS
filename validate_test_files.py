#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test File Validator - Validates test files without running Odoo

Checks:
1. Python syntax is valid
2. Test classes are properly defined
3. Test methods follow naming conventions
4. Required imports are present
"""
import ast
import sys
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def validate_file(filepath):
    """Validate a single test file."""
    print(f"\n{Colors.BLUE}Validating: {filepath.name}{Colors.ENDC}")

    errors = []
    warnings = []

    # Read file
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read file: {e}")
        return errors, warnings

    # Parse Python syntax
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        return errors, warnings

    # Find test classes
    test_classes = []
    test_methods = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name.startswith('Test'):
                test_classes.append(node.name)
                # Count test methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name.startswith('test_'):
                            test_methods.append(f"{node.name}.{item.name}")

    # Validation checks
    if not test_classes:
        warnings.append("No test classes found (class names should start with 'Test')")
    else:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Found {len(test_classes)} test class(es): {', '.join(test_classes)}")

    if not test_methods:
        warnings.append("No test methods found (method names should start with 'test_')")
    else:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Found {len(test_methods)} test method(s)")

    # Check required imports
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)

    required_imports = ['odoo.tests.common', 'odoo.exceptions']
    for req in required_imports:
        found = any(req in imp or imp in req for imp in imports)
        if found:
            print(f"  {Colors.GREEN}✓{Colors.ENDC} Has import: {req}")
        else:
            warnings.append(f"Missing recommended import: {req}")

    # Check file encoding
    if '# -*- coding: utf-8 -*-' in content.split('\n')[0:2]:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Has UTF-8 encoding declaration")
    else:
        warnings.append("Missing UTF-8 encoding declaration")

    # Check docstrings
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Has module docstring")
    else:
        warnings.append("Missing module docstring")

    return errors, warnings


def main():
    """Main validation."""
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'Gym Void Wizard Test File Validator'.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.ENDC}")

    # Find test files
    test_dir = Path('l10n_cr_einvoice/tests')
    test_files = list(test_dir.glob('test_gym_void_wizard*.py'))

    if not test_files:
        print(f"\n{Colors.RED}✗ No test files found in {test_dir}{Colors.ENDC}")
        sys.exit(1)

    print(f"\n{Colors.BLUE}Found {len(test_files)} test file(s):{Colors.ENDC}")
    for f in test_files:
        print(f"  • {f.name}")

    # Validate each file
    total_errors = 0
    total_warnings = 0

    for filepath in test_files:
        errors, warnings = validate_file(filepath)

        if errors:
            print(f"\n{Colors.RED}✗ Errors in {filepath.name}:{Colors.ENDC}")
            for error in errors:
                print(f"    {Colors.RED}• {error}{Colors.ENDC}")
            total_errors += len(errors)

        if warnings:
            print(f"\n{Colors.YELLOW}⚠ Warnings in {filepath.name}:{Colors.ENDC}")
            for warning in warnings:
                print(f"    {Colors.YELLOW}• {warning}{Colors.ENDC}")
            total_warnings += len(warnings)

    # Summary
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'VALIDATION SUMMARY'.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

    print(f"Files Validated: {len(test_files)}")
    print(f"Errors: {Colors.RED if total_errors > 0 else Colors.GREEN}{total_errors}{Colors.ENDC}")
    print(f"Warnings: {Colors.YELLOW if total_warnings > 0 else Colors.GREEN}{total_warnings}{Colors.ENDC}")

    if total_errors == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All test files are valid!{Colors.ENDC}")
        print(f"\n{Colors.BLUE}Next steps:{Colors.ENDC}")
        print(f"  1. Install Odoo environment")
        print(f"  2. Run: ./run_void_wizard_tests.sh")
        print(f"  3. Or run: python3 odoo-bin -c odoo.conf --test-enable --test-tags l10n_cr_einvoice.tests.test_gym_void_wizard_unit")
        print()
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Validation failed with {total_errors} error(s){Colors.ENDC}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
