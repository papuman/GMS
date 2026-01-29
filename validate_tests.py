#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test validation script - checks that test files are syntactically correct
and counts test methods.
"""

import os
import ast
import sys
from pathlib import Path

def analyze_test_file(filepath):
    """Analyze a test file and extract test information."""
    with open(filepath, 'r') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {'error': str(e), 'tests': []}

    tests = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name.startswith('Test'):
                class_tests = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                        # Extract docstring if available
                        docstring = ast.get_docstring(item) or "No description"
                        class_tests.append({
                            'name': item.name,
                            'description': docstring.split('\n')[0][:80]
                        })
                classes.append({
                    'class': node.name,
                    'tests': class_tests
                })

    return {'error': None, 'classes': classes}

def main():
    test_dir = Path('/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/tests')

    print("="*70)
    print("TEST FILE VALIDATION AND ANALYSIS")
    print("="*70)

    test_files = [
        'test_xml_parser.py',
        'test_xml_import_integration.py'
    ]

    total_tests = 0
    results = {}

    for test_file in test_files:
        filepath = test_dir / test_file
        if not filepath.exists():
            print(f"\n❌ {test_file}: FILE NOT FOUND")
            continue

        print(f"\n{'='*70}")
        print(f"Analyzing: {test_file}")
        print(f"{'='*70}")

        result = analyze_test_file(filepath)

        if result['error']:
            print(f"❌ SYNTAX ERROR: {result['error']}")
            results[test_file] = {'status': 'error', 'error': result['error']}
            continue

        print(f"✅ Syntax valid")

        file_tests = 0
        for class_info in result['classes']:
            print(f"\n  Test Class: {class_info['class']}")
            print(f"  Tests found: {len(class_info['tests'])}")

            for test in class_info['tests']:
                print(f"    ✓ {test['name']}: {test['description']}")
                file_tests += 1

        total_tests += file_tests

        results[test_file] = {
            'status': 'ok',
            'classes': len(result['classes']),
            'tests': file_tests
        }

        print(f"\n  Total tests in {test_file}: {file_tests}")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total test files analyzed: {len(test_files)}")
    print(f"Total test methods found: {total_tests}")

    for test_file, result in results.items():
        status_symbol = "✅" if result['status'] == 'ok' else "❌"
        print(f"  {status_symbol} {test_file}: {result.get('tests', 0)} tests")

    print(f"{'='*70}")

if __name__ == '__main__':
    main()
