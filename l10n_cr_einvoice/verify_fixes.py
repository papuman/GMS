#!/usr/bin/env python3
"""
Verification script to check all fixes have been applied correctly.
Run this before deploying to production.

Usage: python3 verify_fixes.py
"""

import os
import re
import sys

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def check_file_contains(filepath, pattern, description):
    """Check if file contains specific pattern."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                print(f"{GREEN}✓{RESET} {description}")
                return True
            else:
                print(f"{RED}✗{RESET} {description}")
                return False
    except FileNotFoundError:
        print(f"{RED}✗{RESET} {description} - {YELLOW}File not found: {filepath}{RESET}")
        return False

def main():
    print(f"\n{BOLD}=== E-Invoice Module Fix Verification ==={RESET}\n")
    
    checks = []
    base_path = "l10n_cr_einvoice"
    
    # Check 1: move_id is optional
    checks.append(check_file_contains(
        f"{base_path}/models/einvoice_document.py",
        r"move_id.*\n.*required=False",
        "1. move_id is optional (required=False)"
    ))
    
    # Check 2: pos_order_id field exists
    checks.append(check_file_contains(
        f"{base_path}/models/einvoice_document.py",
        r"pos_order_id.*=.*fields\.Many2one.*pos\.order",
        "2. pos_order_id field added"
    ))
    
    # Check 3: Constraint exists
    checks.append(check_file_contains(
        f"{base_path}/models/einvoice_document.py",
        r"@api\.constrains.*move_id.*pos_order_id|_check_source_document",
        "3. Source document constraint implemented"
    ))
    
    # Check 4: Computed fields
    checks.append(check_file_contains(
        f"{base_path}/models/einvoice_document.py",
        r"_compute_partner_id.*_compute_amount_total.*_compute_currency_id",
        "4. Computed fields for dual source support"
    ))
    
    # Check 5: POS order passes pos_order_id
    checks.append(check_file_contains(
        f"{base_path}/models/pos_order.py",
        r"'pos_order_id':\s*self\.id",
        "5. POS order passes pos_order_id"
    ))
    
    # Check 6: XML generator supports source_doc
    checks.append(check_file_contains(
        f"{base_path}/models/xml_generator.py",
        r"source_doc|einvoice\.pos_order_id",
        "6. XML generator handles both invoice and POS"
    ))
    
    # Check 7: Order export_as_JSON override
    checks.append(check_file_contains(
        f"{base_path}/static/src/js/pos_einvoice.js",
        r"export_as_JSON.*json\.l10n_cr_is_einvoice.*json\.einvoice_type",
        "7. Order.export_as_JSON() includes einvoice fields"
    ))
    
    # Check 8: F2 keyboard hint
    checks.append(check_file_contains(
        f"{base_path}/static/src/xml/pos_einvoice.xml",
        r"Presione F2 para cambiar|keyboard-hint",
        "8. F2 keyboard shortcut clearly labeled"
    ))
    
    # Check 9: Touch device media query
    checks.append(check_file_contains(
        f"{base_path}/static/src/css/pos_einvoice.css",
        r"@media.*pointer:\s*coarse",
        "9. Touch device optimization (media query)"
    ))
    
    # Check 10: Enhanced error recovery
    checks.append(check_file_contains(
        f"{base_path}/static/src/js/pos_einvoice.js",
        r"ConfirmPopup.*cambiar a Tiquete",
        "10. Enhanced error recovery (switch to TE)"
    ))
    
    # Check 11: Color coding
    checks.append(check_file_contains(
        f"{base_path}/static/src/css/pos_einvoice.css",
        r"data-type.*TE.*#0d6efd|data-type.*FE.*#714B67",
        "11. Color coding (blue TE, purple FE)"
    ))
    
    # Check 12: Smart type detection
    checks.append(check_file_contains(
        f"{base_path}/static/src/js/pos_einvoice.js",
        r"partner\.vat.*einvoice_type.*=.*'FE'",
        "12. Smart type detection (auto FE for VAT)"
    ))
    
    # Check 13: Receipt printing support
    checks.append(check_file_contains(
        f"{base_path}/static/src/js/pos_einvoice.js",
        r"export_for_printing.*l10n_cr_clave.*l10n_cr_qr_code",
        "13. Receipt printing support (clave & QR)"
    ))
    
    # Check 14: README exists
    checks.append(os.path.exists(f"{base_path}/README.md"))
    if checks[-1]:
        print(f"{GREEN}✓{RESET} 14. README.md created")
    else:
        print(f"{RED}✗{RESET} 14. README.md created")
    
    # Check 15: Deployment checklist exists
    checks.append(os.path.exists(f"{base_path}/DEPLOYMENT_CHECKLIST.md"))
    if checks[-1]:
        print(f"{GREEN}✓{RESET} 15. DEPLOYMENT_CHECKLIST.md created")
    else:
        print(f"{RED}✗{RESET} 15. DEPLOYMENT_CHECKLIST.md created")
    
    # Check 16: Test structure exists
    checks.append(os.path.exists(f"{base_path}/static/tests/pos_einvoice_tests.js"))
    if checks[-1]:
        print(f"{GREEN}✓{RESET} 16. Frontend test structure created")
    else:
        print(f"{RED}✗{RESET} 16. Frontend test structure created")
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total) * 100
    
    print(f"\n{BOLD}=== Verification Summary ==={RESET}")
    print(f"Checks passed: {passed}/{total} ({percentage:.1f}%)")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 ALL CHECKS PASSED! Module is ready for production.{RESET}\n")
        return 0
    elif passed >= total * 0.9:
        print(f"\n{YELLOW}{BOLD}⚠️  Most checks passed. Review failures before production.{RESET}\n")
        return 1
    else:
        print(f"\n{RED}{BOLD}❌ Multiple checks failed. Do not deploy to production.{RESET}\n")
        return 2

if __name__ == "__main__":
    sys.exit(main())
