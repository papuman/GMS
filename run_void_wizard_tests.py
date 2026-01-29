#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Runner for Gym Invoice Void Wizard

Runs all test suites and provides comprehensive reporting.

Usage:
    python3 run_void_wizard_tests.py

Or run specific test suite:
    python3 run_void_wizard_tests.py unit
    python3 run_void_wizard_tests.py integration
    python3 run_void_wizard_tests.py membership
    python3 run_void_wizard_tests.py all
"""
import sys
import subprocess
import time
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print colored header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def run_odoo_test(module, test_class):
    """
    Run specific Odoo test class.

    Args:
        module: Module name (e.g., 'l10n_cr_einvoice')
        test_class: Test class name (e.g., 'TestGymVoidWizardUnit')

    Returns:
        tuple: (success: bool, output: str, duration: float)
    """
    print_info(f"Running test: {test_class}...")

    start_time = time.time()

    # Build Odoo test command
    cmd = [
        'python3',
        'odoo-bin',
        '-c', 'odoo.conf',
        '--test-enable',
        '--test-tags', f'{module}.{test_class}',
        '--stop-after-init',
        '--log-level=test',
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        duration = time.time() - start_time

        # Check if tests passed
        success = result.returncode == 0 and 'FAILED' not in result.stderr

        return success, result.stderr + result.stdout, duration

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return False, "Test timed out after 5 minutes", duration

    except Exception as e:
        duration = time.time() - start_time
        return False, f"Error running test: {str(e)}", duration


def run_test_suite(suite_name):
    """
    Run a complete test suite.

    Args:
        suite_name: 'unit', 'integration', 'membership', or 'all'

    Returns:
        dict: Test results with statistics
    """
    test_suites = {
        'unit': [
            ('l10n_cr_einvoice.tests.test_gym_void_wizard_unit', 'TestGymVoidWizardUnit'),
        ],
        'integration': [
            ('l10n_cr_einvoice.tests.test_gym_void_wizard_integration', 'TestGymVoidWizardIntegration'),
        ],
        'membership': [
            ('l10n_cr_einvoice.tests.test_gym_void_wizard_membership', 'TestGymVoidWizardMembership'),
        ],
    }

    if suite_name == 'all':
        tests_to_run = []
        for suite_tests in test_suites.values():
            tests_to_run.extend(suite_tests)
    else:
        tests_to_run = test_suites.get(suite_name, [])

    if not tests_to_run:
        print_error(f"Unknown test suite: {suite_name}")
        return None

    results = {
        'total': len(tests_to_run),
        'passed': 0,
        'failed': 0,
        'duration': 0,
        'details': [],
    }

    for module_path, test_class in tests_to_run:
        success, output, duration = run_odoo_test(module_path, test_class)

        results['duration'] += duration

        if success:
            results['passed'] += 1
            print_success(f"{test_class} - PASSED ({duration:.2f}s)")
        else:
            results['failed'] += 1
            print_error(f"{test_class} - FAILED ({duration:.2f}s)")

        results['details'].append({
            'class': test_class,
            'success': success,
            'duration': duration,
            'output': output,
        })

    return results


def print_summary(results):
    """Print test results summary."""
    print_header("TEST RESULTS SUMMARY")

    total = results['total']
    passed = results['passed']
    failed = results['failed']
    duration = results['duration']

    print(f"\n{Colors.BOLD}Total Tests:{Colors.ENDC} {total}")
    print(f"{Colors.OKGREEN}Passed:{Colors.ENDC} {passed}")
    print(f"{Colors.FAIL}Failed:{Colors.ENDC} {failed}")
    print(f"{Colors.OKCYAN}Duration:{Colors.ENDC} {duration:.2f}s")

    if passed == total:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}⚠️  {failed} TEST(S) FAILED{Colors.ENDC}")

    # Print failed test details
    if failed > 0:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Failed Tests:{Colors.ENDC}")
        for detail in results['details']:
            if not detail['success']:
                print(f"\n{Colors.FAIL}  • {detail['class']}{Colors.ENDC}")
                # Print last 20 lines of output
                output_lines = detail['output'].split('\n')
                relevant_lines = output_lines[-20:]
                for line in relevant_lines:
                    if 'FAIL' in line or 'ERROR' in line:
                        print(f"    {line}")

    print("\n" + "=" * 80 + "\n")


def main():
    """Main test runner."""
    print_header("GYM INVOICE VOID WIZARD - TEST SUITE")

    print(f"{Colors.BOLD}Start Time:{Colors.ENDC} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Determine which tests to run
    suite = 'all'
    if len(sys.argv) > 1:
        suite = sys.argv[1].lower()

    print_info(f"Running test suite: {suite}")
    print()

    # Run tests
    results = run_test_suite(suite)

    if results:
        print_summary(results)

        # Exit with appropriate code
        sys.exit(0 if results['failed'] == 0 else 1)
    else:
        print_error("No tests were run")
        sys.exit(1)


if __name__ == '__main__':
    main()
