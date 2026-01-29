#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5: POS Integration - Installation Verification Script
Verifies that all Phase 5 components are properly installed

Usage:
    python3 verify_phase5_installation.py

Or in Odoo shell:
    odoo-bin shell -c odoo.conf -d your_database
    >>> exec(open('verify_phase5_installation.py').read())
"""

import os
import sys


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_success(message):
    """Print success message."""
    print(f"✓ {message}")


def print_error(message):
    """Print error message."""
    print(f"✗ {message}")


def print_warning(message):
    """Print warning message."""
    print(f"⚠ {message}")


def check_files():
    """Check if all required files exist."""
    print_header("File Existence Check")

    base_path = "/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice"

    required_files = [
        # Models
        "models/pos_integration.py",
        "models/pos_offline_queue.py",
        "models/pos_config.py",

        # Views
        "views/pos_config_views.xml",
        "views/pos_order_views.xml",
        "views/pos_offline_queue_views.xml",

        # Static
        "static/src/js/pos_einvoice.js",
        "static/src/xml/pos_einvoice.xml",
        "static/src/css/pos_einvoice.css",

        # Data
        "data/pos_sequences.xml",

        # Tests
        "tests/test_pos_integration.py",
        "tests/test_pos_offline.py",

        # Documentation
        "PHASE5_IMPLEMENTATION_COMPLETE.md",
        "PHASE5_QUICK_REFERENCE.md",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print_success(f"{file_path} ({size:,} bytes)")
        else:
            print_error(f"{file_path} - NOT FOUND")
            all_exist = False

    return all_exist


def check_odoo_models():
    """Check if Odoo models are loaded (only works in Odoo shell)."""
    print_header("Odoo Model Check")

    try:
        from odoo import api, SUPERUSER_ID

        # This will only work if run inside Odoo shell
        print_warning("Run this inside Odoo shell for model verification")
        print("Command: odoo-bin shell -c odoo.conf -d your_database")
        print("Then: exec(open('verify_phase5_installation.py').read())")

        return False
    except ImportError:
        print_warning("Not running in Odoo environment")
        print("Skipping Odoo-specific checks")
        return False


def check_manifest():
    """Check manifest file for correct version and dependencies."""
    print_header("Manifest Check")

    manifest_path = "/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/__manifest__.py"

    try:
        with open(manifest_path, 'r') as f:
            content = f.read()

        # Check version
        if "'version': '19.0.1.6.0'" in content:
            print_success("Version is correct: 19.0.1.6.0")
        else:
            print_error("Version mismatch - should be 19.0.1.6.0")
            return False

        # Check POS dependency
        if "'point_of_sale'" in content:
            print_success("point_of_sale dependency present")
        else:
            print_error("point_of_sale dependency missing")
            return False

        # Check data files
        required_data = [
            "data/pos_sequences.xml",
            "views/pos_config_views.xml",
            "views/pos_order_views.xml",
            "views/pos_offline_queue_views.xml",
        ]

        for data_file in required_data:
            if data_file in content:
                print_success(f"{data_file} in manifest")
            else:
                print_error(f"{data_file} missing from manifest")
                return False

        # Check assets
        if "'point_of_sale.assets'" in content:
            print_success("POS assets configuration present")
        else:
            print_error("POS assets configuration missing")
            return False

        return True

    except FileNotFoundError:
        print_error(f"Manifest file not found: {manifest_path}")
        return False


def check_init_files():
    """Check __init__.py files for proper imports."""
    print_header("Import Check")

    # Check models/__init__.py
    models_init = "/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/models/__init__.py"
    try:
        with open(models_init, 'r') as f:
            content = f.read()

        required_imports = [
            "from . import pos_config",
            "from . import pos_integration",
            "from . import pos_offline_queue",
        ]

        for imp in required_imports:
            if imp in content:
                print_success(f"Import present: {imp}")
            else:
                print_error(f"Import missing: {imp}")
                return False

    except FileNotFoundError:
        print_error(f"File not found: {models_init}")
        return False

    # Check tests/__init__.py
    tests_init = "/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/tests/__init__.py"
    try:
        with open(tests_init, 'r') as f:
            content = f.read()

        required_imports = [
            "from . import test_pos_integration",
            "from . import test_pos_offline",
        ]

        for imp in required_imports:
            if imp in content:
                print_success(f"Import present: {imp}")
            else:
                print_error(f"Import missing: {imp}")
                return False

    except FileNotFoundError:
        print_error(f"File not found: {tests_init}")
        return False

    return True


def check_security():
    """Check security file for POS access rules."""
    print_header("Security Check")

    security_file = "/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/security/ir.model.access.csv"

    try:
        with open(security_file, 'r') as f:
            content = f.read()

        required_rules = [
            "access_pos_offline_queue_pos_user",
            "access_pos_offline_queue_pos_manager",
            "access_pos_offline_queue_accountant",
        ]

        for rule in required_rules:
            if rule in content:
                print_success(f"Security rule present: {rule}")
            else:
                print_error(f"Security rule missing: {rule}")
                return False

        return True

    except FileNotFoundError:
        print_error(f"Security file not found: {security_file}")
        return False


def count_test_methods():
    """Count test methods in test files."""
    print_header("Test Coverage Check")

    test_files = [
        "/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/tests/test_pos_integration.py",
        "/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/tests/test_pos_offline.py",
    ]

    total_tests = 0
    for test_file in test_files:
        try:
            with open(test_file, 'r') as f:
                content = f.read()

            # Count test methods (def test_)
            test_count = content.count("def test_")
            total_tests += test_count

            file_name = os.path.basename(test_file)
            print_success(f"{file_name}: {test_count} test methods")

        except FileNotFoundError:
            print_error(f"Test file not found: {test_file}")
            return False

    print(f"\n  Total test methods: {total_tests}")

    if total_tests >= 25:
        print_success("Test coverage meets requirement (25+ tests)")
        return True
    else:
        print_warning(f"Test coverage below requirement: {total_tests}/25")
        return False


def generate_summary():
    """Generate installation summary."""
    print_header("Installation Summary")

    results = {
        "Files": check_files(),
        "Manifest": check_manifest(),
        "Imports": check_init_files(),
        "Security": check_security(),
        "Tests": count_test_methods(),
    }

    print("\nResults:")
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {check:20s} {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("  ✓ Phase 5 installation VERIFIED - All checks passed!")
    else:
        print("  ✗ Phase 5 installation INCOMPLETE - Some checks failed")
    print("=" * 70)

    return all_passed


def main():
    """Main verification function."""
    print("\n" + "=" * 70)
    print("  Phase 5: POS Integration - Installation Verification")
    print("  Module: l10n_cr_einvoice")
    print("  Version: 19.0.1.6.0")
    print("=" * 70)

    success = generate_summary()

    if success:
        print("\nNext Steps:")
        print("1. Update Odoo module:")
        print("   odoo-bin -c odoo.conf -d your_database -u l10n_cr_einvoice")
        print("\n2. Run tests:")
        print("   odoo-bin -c odoo.conf -d test_db --test-tags=pos --stop-after-init")
        print("\n3. Configure POS terminals:")
        print("   Point of Sale > Configuration > Point of Sale")
        print("\n4. Test connection:")
        print("   Click 'Test Connection' in POS config")
    else:
        print("\nPlease fix the issues above before proceeding.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
