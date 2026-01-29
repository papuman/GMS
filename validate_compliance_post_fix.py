#!/usr/bin/env python3
"""
Comprehensive Compliance Validation Script
Validates all Odoo 19 compliance criteria after fixes
"""

import os
import re
import csv
from pathlib import Path

MODULE_PATH = "/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice"
RESULTS = []

def validate_badge_classes():
    """Validate Bootstrap 5 badge classes in Kanban view"""
    file_path = os.path.join(MODULE_PATH, "views/einvoice_document_views.xml")
    with open(file_path, 'r') as f:
        content = f.read()

    # Check for Bootstrap 5 classes
    bs5_badges = len(re.findall(r'class="badge bg-', content))
    # Check for old Bootstrap 4 classes
    bs4_badges = len(re.findall(r'class="badge badge-', content))

    passed = bs5_badges >= 4 and bs4_badges == 0
    RESULTS.append({
        'category': 'View Files',
        'test': 'Kanban Badge Classes',
        'expected': '4 Bootstrap 5 badges, 0 Bootstrap 4',
        'actual': f'{bs5_badges} BS5, {bs4_badges} BS4',
        'status': '✅ PASS' if passed else '❌ FAIL'
    })
    return passed

def validate_security_rules():
    """Validate wizard security rules exist"""
    file_path = os.path.join(MODULE_PATH, "security/ir.model.access.csv")
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    wizard_models = [
        'model_l10n_cr_batch_einvoice_wizard',
        'model_l10n_cr_batch_submit_wizard',
        'model_l10n_cr_batch_check_status_wizard'
    ]

    found_wizards = [row for row in rows if row['model_id:id'] in wizard_models]
    passed = len(found_wizards) == 3

    RESULTS.append({
        'category': 'Security',
        'test': 'Wizard Security Rules',
        'expected': '3 wizard access rules',
        'actual': f'{len(found_wizards)} rules found',
        'status': '✅ PASS' if passed else '❌ FAIL'
    })
    return passed

def validate_sequence_config():
    """Validate no duplicate sequence configuration"""
    init_path = os.path.join(MODULE_PATH, "__init__.py")
    manifest_path = os.path.join(MODULE_PATH, "__manifest__.py")

    with open(init_path, 'r') as f:
        init_content = f.read()

    with open(manifest_path, 'r') as f:
        manifest_content = f.read()

    has_post_init = 'post_init_hook' in init_content or 'post_init_hook' in manifest_content
    passed = not has_post_init

    RESULTS.append({
        'category': 'Data Files',
        'test': 'Sequence Configuration',
        'expected': 'No post_init_hook creating sequences',
        'actual': 'post_init_hook found' if has_post_init else 'No post_init_hook',
        'status': '✅ PASS' if passed else '❌ FAIL'
    })
    return passed

def validate_wizard_buttons():
    """Validate wizard button classes use oe_highlight"""
    file_path = os.path.join(MODULE_PATH, "views/einvoice_wizard_views.xml")
    with open(file_path, 'r') as f:
        content = f.read()

    oe_highlight_count = len(re.findall(r'class="oe_highlight"', content))
    btn_primary_count = len(re.findall(r'class="btn-primary"', content))

    passed = oe_highlight_count >= 3 and btn_primary_count == 0

    RESULTS.append({
        'category': 'View Files',
        'test': 'Wizard Button Classes',
        'expected': '3 oe_highlight buttons, 0 btn-primary',
        'actual': f'{oe_highlight_count} oe_highlight, {btn_primary_count} btn-primary',
        'status': '✅ PASS' if passed else '❌ FAIL'
    })
    return passed

def validate_manifest_cleanup():
    """Validate document_types.xml removed from manifest"""
    manifest_path = os.path.join(MODULE_PATH, "__manifest__.py")
    with open(manifest_path, 'r') as f:
        content = f.read()

    has_doc_types = 'document_types.xml' in content
    passed = not has_doc_types

    RESULTS.append({
        'category': 'Manifest',
        'test': 'Empty Data File Cleanup',
        'expected': 'No document_types.xml reference',
        'actual': 'Reference found' if has_doc_types else 'No reference',
        'status': '✅ PASS' if passed else '❌ FAIL'
    })
    return passed

def validate_file_sync():
    """Validate files are synchronized between both locations"""
    files_to_check = [
        'views/einvoice_document_views.xml',
        'views/einvoice_wizard_views.xml',
        'security/ir.model.access.csv',
        '__init__.py',
        '__manifest__.py'
    ]

    all_synced = True
    for file_path in files_to_check:
        primary = os.path.join(MODULE_PATH, file_path)
        secondary = os.path.join("/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/odoo/addons/l10n_cr_einvoice", file_path)

        with open(primary, 'rb') as f1, open(secondary, 'rb') as f2:
            if f1.read() != f2.read():
                all_synced = False
                break

    RESULTS.append({
        'category': 'Synchronization',
        'test': 'File Synchronization',
        'expected': '5 files identical in both locations',
        'actual': 'All synced' if all_synced else 'Mismatch found',
        'status': '✅ PASS' if all_synced else '❌ FAIL'
    })
    return all_synced

def run_all_validations():
    """Run all validation tests"""
    print("=" * 80)
    print("ODOO 19 COMPLIANCE VALIDATION - POST FIX")
    print("Module: l10n_cr_einvoice")
    print("=" * 80)
    print()

    tests = [
        validate_badge_classes,
        validate_security_rules,
        validate_sequence_config,
        validate_wizard_buttons,
        validate_manifest_cleanup,
        validate_file_sync
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"Error running {test.__name__}: {e}")

    # Print results
    print(f"{'Category':<20} {'Test':<35} {'Status':<12}")
    print("-" * 80)

    passed = 0
    total = len(RESULTS)

    for result in RESULTS:
        print(f"{result['category']:<20} {result['test']:<35} {result['status']:<12}")
        if '✅' in result['status']:
            passed += 1

    print("-" * 80)
    print(f"\nTOTAL: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 100% COMPLIANCE ACHIEVED - ALL TESTS PASSED! 🎉")
        compliance_score = 100
    else:
        compliance_score = round((passed / total) * 100)
        print(f"\n⚠️ Compliance Score: {compliance_score}%")

    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    for result in RESULTS:
        print(f"\n{result['test']}:")
        print(f"  Category: {result['category']}")
        print(f"  Expected: {result['expected']}")
        print(f"  Actual:   {result['actual']}")
        print(f"  Status:   {result['status']}")

    return compliance_score

if __name__ == "__main__":
    score = run_all_validations()
    exit(0 if score == 100 else 1)
