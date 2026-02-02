#!/usr/bin/env python3
"""
Coverage Gap Analysis for l10n_cr_einvoice Module
Generates a detailed report of test coverage gaps relative to targets.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Module directory
MODULE_DIR = Path("/Users/papuman/Documents/My Projects/GMS/l10n_cr_einvoice")

# Coverage targets from test design document
COVERAGE_TARGETS = {
    "xml_generator.py": 90,
    "xml_signer.py": 90,
    "certificate_manager.py": 90,
    "xsd_validator.py": 85,
    "hacienda_api.py": 80,
    "tax_report_xml_generator.py": 85,
    "einvoice_document.py": 75,
    "d150_vat_report.py": 80,
    "d101_income_tax_report.py": 80,
    "d151_informative_report.py": 80,
    "einvoice_xml_parser.py": 75,
    "account_move.py": 70,
    "res_company.py": 60,
    "res_partner.py": 60,
}

# Critical modules (P0 priority)
P0_MODULES = [
    "xml_generator.py",
    "xml_signer.py",
    "certificate_manager.py",
    "xsd_validator.py",
    "hacienda_api.py",
]


def count_lines(file_path):
    """Count total lines, code lines, and comment lines in a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total = len(lines)
    blank = sum(1 for line in lines if line.strip() == '')
    comments = sum(1 for line in lines if line.strip().startswith('#'))
    docstrings = 0

    # Rough docstring counting
    in_docstring = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if in_docstring:
                in_docstring = False
                docstrings += 1
            else:
                in_docstring = True
                docstrings += 1
        elif in_docstring:
            docstrings += 1

    code = total - blank - comments - docstrings
    return total, code, blank, comments, docstrings


def find_test_imports(test_file):
    """Find which modules are imported in a test file."""
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for imports from models/
    imports = re.findall(r'from\s+(?:odoo\.addons\.)?l10n_cr_einvoice\.models\.(\w+)', content)
    imports.extend(re.findall(r'import\s+(?:odoo\.addons\.)?l10n_cr_einvoice\.models\.(\w+)', content))

    return set(imports)


def analyze_module_coverage():
    """Analyze test coverage for each module."""
    models_dir = MODULE_DIR / "models"
    tests_dir = MODULE_DIR / "tests"

    # Scan all model files
    modules = {}
    for py_file in models_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        total, code, blank, comments, docstrings = count_lines(py_file)
        modules[py_file.name] = {
            "path": str(py_file),
            "total_lines": total,
            "code_lines": code,
            "blank_lines": blank,
            "comment_lines": comments,
            "docstring_lines": docstrings,
            "test_files": [],
            "tested_by": [],
        }

    # Scan all test files and map to modules
    test_files = {}
    for test_file in tests_dir.glob("test_*.py"):
        total, code, blank, comments, docstrings = count_lines(test_file)
        test_files[test_file.name] = {
            "path": str(test_file),
            "total_lines": total,
            "code_lines": code,
            "tests_modules": find_test_imports(test_file),
        }

        # Map tests to modules
        for module_name in find_test_imports(test_file):
            module_file = f"{module_name}.py"
            if module_file in modules:
                modules[module_file]["test_files"].append(test_file.name)

    return modules, test_files


def estimate_coverage(module_data, module_name):
    """
    Estimate test coverage based on:
    - Presence of dedicated test files
    - Size of test files relative to module size
    - Known test status
    """
    # Known good coverage
    if module_name == "certificate_manager.py":
        return 80  # Known from test design doc

    # Has dedicated test file
    test_files = module_data["test_files"]
    if not test_files:
        return 0

    # Calculate test-to-code ratio
    module_code = module_data["code_lines"]

    # Find test file sizes
    test_code_lines = 0
    for test_file in test_files:
        test_path = MODULE_DIR / "tests" / test_file
        if test_path.exists():
            _, code, _, _, _ = count_lines(test_path)
            test_code_lines += code

    # Estimate coverage based on test-to-code ratio
    # Typical ratio: 1:1 test:code = ~70% coverage
    # Higher ratio = higher coverage
    if module_code == 0:
        return 0

    ratio = test_code_lines / module_code

    # Heuristic mapping
    if ratio >= 2.0:
        return 85
    elif ratio >= 1.5:
        return 75
    elif ratio >= 1.0:
        return 65
    elif ratio >= 0.5:
        return 50
    elif ratio >= 0.25:
        return 35
    else:
        return 20 if test_files else 0


def generate_report():
    """Generate comprehensive coverage gap report."""
    modules, test_files = analyze_module_coverage()

    # Sort by priority (P0 first, then by size)
    sorted_modules = sorted(
        modules.items(),
        key=lambda x: (
            0 if x[0] in P0_MODULES else 1,
            -x[1]["code_lines"]
        )
    )

    print("=" * 80)
    print("COVERAGE GAP ANALYSIS - l10n_cr_einvoice Module")
    print("=" * 80)
    print()

    # Summary statistics
    total_modules = len(modules)
    total_code_lines = sum(m["code_lines"] for m in modules.values())
    modules_with_tests = sum(1 for m in modules.values() if m["test_files"])

    print("SUMMARY")
    print("-" * 80)
    print(f"Total Modules: {total_modules}")
    print(f"Total Code Lines: {total_code_lines:,}")
    print(f"Modules with Tests: {modules_with_tests} ({modules_with_tests/total_modules*100:.1f}%)")
    print(f"Modules without Tests: {total_modules - modules_with_tests}")
    print()

    # Critical modules analysis
    print("P0 CRITICAL MODULES (Must have ≥80% coverage)")
    print("-" * 80)
    print(f"{'Module':<35} {'Lines':<8} {'Target':<8} {'Est.':<8} {'Gap':<8} {'Status'}")
    print("-" * 80)

    p0_gaps = []
    for module_name in P0_MODULES:
        if module_name not in modules:
            continue

        data = modules[module_name]
        target = COVERAGE_TARGETS.get(module_name, 80)
        estimated = estimate_coverage(data, module_name)
        gap = target - estimated
        status = "✓ OK" if gap <= 0 else f"⚠ -{gap}%"

        print(f"{module_name:<35} {data['code_lines']:<8} {target}%{'':<5} {estimated}%{'':<5} {gap:>3}%{'':<5} {status}")

        if gap > 0:
            p0_gaps.append((module_name, gap, estimated, target))

    print()

    # All modules analysis
    print("ALL MODULES COVERAGE ANALYSIS")
    print("-" * 80)
    print(f"{'Module':<35} {'Lines':<8} {'Target':<8} {'Est.':<8} {'Tests'}")
    print("-" * 80)

    for module_name, data in sorted_modules:
        target = COVERAGE_TARGETS.get(module_name, 60)
        estimated = estimate_coverage(data, module_name)
        test_count = len(data["test_files"])
        test_info = f"{test_count} file(s)" if test_count > 0 else "None"

        print(f"{module_name:<35} {data['code_lines']:<8} {target}%{'':<5} {estimated}%{'':<5} {test_info}")

    print()

    # Gap prioritization
    print("TOP 10 PRIORITY GAPS")
    print("-" * 80)
    print(f"{'#':<4} {'Module':<35} {'Gap':<8} {'Priority'}")
    print("-" * 80)

    all_gaps = []
    for module_name, data in modules.items():
        target = COVERAGE_TARGETS.get(module_name, 60)
        estimated = estimate_coverage(data, module_name)
        gap = target - estimated

        if gap > 0:
            priority = "P0" if module_name in P0_MODULES else "P1"
            weighted_gap = gap * 2 if module_name in P0_MODULES else gap
            all_gaps.append((weighted_gap, module_name, gap, priority))

    all_gaps.sort(reverse=True)

    for idx, (_, module_name, gap, priority) in enumerate(all_gaps[:10], 1):
        print(f"{idx:<4} {module_name:<35} {gap}%{'':<5} {priority}")

    print()

    # Test file inventory
    print("TEST FILE INVENTORY")
    print("-" * 80)
    print(f"Total Test Files: {len(test_files)}")
    print()

    for test_name, data in sorted(test_files.items(), key=lambda x: -x[1]["code_lines"]):
        print(f"  {test_name:<50} {data['code_lines']:>5} lines")
        if data["tests_modules"]:
            print(f"    Tests: {', '.join(sorted(data['tests_modules']))}")

    print()

    # Recommendations
    print("RECOMMENDATIONS")
    print("-" * 80)

    if p0_gaps:
        print("1. CRITICAL (P0) - Address these first:")
        for module_name, gap, estimated, target in p0_gaps:
            print(f"   - {module_name}: Need {gap}% more coverage ({estimated}% → {target}%)")
    else:
        print("1. ✓ All P0 critical modules meet coverage targets")

    print()
    print("2. Missing Tests:")
    for module_name, data in modules.items():
        if not data["test_files"] and data["code_lines"] > 50:
            print(f"   - {module_name} ({data['code_lines']} lines) has NO tests")

    print()
    print("3. Estimated Effort to 80% Overall Coverage:")

    total_gap_lines = 0
    for module_name, data in modules.items():
        target = COVERAGE_TARGETS.get(module_name, 60)
        estimated = estimate_coverage(data, module_name)
        gap = max(0, target - estimated)
        gap_lines = int(data["code_lines"] * gap / 100)
        total_gap_lines += gap_lines

    test_lines_needed = int(total_gap_lines * 1.2)  # 1.2:1 test-to-code ratio
    hours = test_lines_needed / 50  # ~50 lines per hour

    print(f"   - Estimated gap: ~{total_gap_lines:,} uncovered code lines")
    print(f"   - Test lines needed: ~{test_lines_needed:,} lines")
    print(f"   - Estimated effort: ~{hours:.0f} hours ({hours/8:.1f} days)")

    print()
    print("=" * 80)


if __name__ == "__main__":
    generate_report()
