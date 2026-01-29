#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Structure Verification Script
Verifies that all modules have proper structure and all imports are valid.
"""

import os
import sys
import importlib.util
from pathlib import Path


def verify_module_structure(module_path):
    """Verify a single Odoo module structure"""
    module_name = os.path.basename(module_path)
    errors = []
    warnings = []

    print(f"\n{'='*70}")
    print(f"Verifying module: {module_name}")
    print(f"{'='*70}")

    # Check __manifest__.py exists
    manifest_path = os.path.join(module_path, '__manifest__.py')
    if not os.path.exists(manifest_path):
        errors.append("Missing __manifest__.py file")
        return errors, warnings

    # Check __init__.py exists
    init_path = os.path.join(module_path, '__init__.py')
    if not os.path.exists(init_path):
        errors.append("Missing __init__.py file at module root")
        return errors, warnings

    # Verify subdirectories
    subdirs = ['models', 'views', 'data', 'security']
    for subdir in subdirs:
        subdir_path = os.path.join(module_path, subdir)
        if os.path.exists(subdir_path):
            print(f"✓ Found {subdir}/ directory")

            # Check for __init__.py in Python directories
            if subdir in ['models', 'wizards', 'controllers', 'reports']:
                init_file = os.path.join(subdir_path, '__init__.py')
                if not os.path.exists(init_file):
                    errors.append(f"Missing __init__.py in {subdir}/ directory")
                else:
                    # Verify imports match files
                    verify_imports(module_name, subdir_path, errors, warnings)

    # Check optional directories
    optional_dirs = ['wizards', 'controllers', 'reports', 'tests']
    for subdir in optional_dirs:
        subdir_path = os.path.join(module_path, subdir)
        if os.path.exists(subdir_path):
            print(f"✓ Found {subdir}/ directory")
            init_file = os.path.join(subdir_path, '__init__.py')
            if not os.path.exists(init_file):
                errors.append(f"Missing __init__.py in {subdir}/ directory")
            else:
                verify_imports(module_name, subdir_path, errors, warnings)

    return errors, warnings


def verify_imports(module_name, directory_path, errors, warnings):
    """Verify that __init__.py imports match actual files in directory"""
    init_file = os.path.join(directory_path, '__init__.py')
    subdir_name = os.path.basename(directory_path)

    # Read imports from __init__.py
    imports = []
    try:
        with open(init_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('from . import '):
                    imported = line.replace('from . import ', '').strip()
                    imports.append(imported)
    except Exception as e:
        errors.append(f"Error reading {subdir_name}/__init__.py: {str(e)}")
        return

    # Get actual Python files (excluding __init__.py and __pycache__)
    actual_files = []
    for file in os.listdir(directory_path):
        if file.endswith('.py') and file != '__init__.py' and not file.startswith('.'):
            actual_files.append(file[:-3])  # Remove .py extension

    # Check for missing imports
    missing_imports = set(actual_files) - set(imports)
    if missing_imports:
        for missing in sorted(missing_imports):
            errors.append(f"{subdir_name}/__init__.py missing import: {missing}")

    # Check for invalid imports (importing non-existent files)
    invalid_imports = set(imports) - set(actual_files)
    if invalid_imports:
        for invalid in sorted(invalid_imports):
            errors.append(f"{subdir_name}/__init__.py imports non-existent file: {invalid}")

    if not missing_imports and not invalid_imports:
        print(f"  ✓ {subdir_name}/__init__.py: All imports valid ({len(imports)} files)")

    return


def main():
    """Main verification function"""
    project_root = Path(__file__).parent

    # Modules to verify
    modules = [
        project_root / 'l10n_cr_einvoice',
        project_root / 'payment_tilopay',
    ]

    total_errors = 0
    total_warnings = 0

    for module_path in modules:
        if not module_path.exists():
            print(f"\n❌ Module not found: {module_path}")
            total_errors += 1
            continue

        errors, warnings = verify_module_structure(str(module_path))

        if errors:
            print(f"\n❌ ERRORS found in {module_path.name}:")
            for error in errors:
                print(f"   • {error}")
            total_errors += len(errors)

        if warnings:
            print(f"\n⚠️  WARNINGS in {module_path.name}:")
            for warning in warnings:
                print(f"   • {warning}")
            total_warnings += len(warnings)

        if not errors and not warnings:
            print(f"\n✅ {module_path.name}: All checks passed!")

    # Summary
    print(f"\n{'='*70}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*70}")
    if total_errors == 0 and total_warnings == 0:
        print("✅ All modules passed verification!")
        return 0
    else:
        print(f"❌ Found {total_errors} errors and {total_warnings} warnings")
        return 1


if __name__ == '__main__':
    sys.exit(main())
