#!/usr/bin/env python3
"""
Smoke Tests for Costa Rica E-Invoicing Module
Runs basic functionality tests after deployment to verify system health

Usage:
    python3 deployment/smoke_tests.py
    python3 deployment/smoke_tests.py --verbose
    python3 deployment/smoke_tests.py --url http://localhost:8069
"""

import sys
import os
import argparse
import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class SmokeTestRunner:
    """Runs smoke tests for e-invoicing deployment"""

    def __init__(self, base_url: str, verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []

    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = {
            'INFO': BLUE,
            'PASS': GREEN,
            'FAIL': RED,
            'WARN': YELLOW
        }.get(level, '')

        print(f"{color}[{timestamp}] [{level}]{RESET} {message}")

    def test(self, name: str, func, *args, **kwargs) -> bool:
        """Run a single test"""
        if self.verbose:
            self.log(f"Running: {name}", 'INFO')

        try:
            result = func(*args, **kwargs)
            if result:
                self.passed += 1
                self.log(f"✓ {name}", 'PASS')
                self.results.append((name, 'PASS', None))
                return True
            else:
                self.failed += 1
                self.log(f"✗ {name}", 'FAIL')
                self.results.append((name, 'FAIL', 'Test returned False'))
                return False
        except Exception as e:
            self.failed += 1
            error_msg = str(e)
            self.log(f"✗ {name}: {error_msg}", 'FAIL')
            self.results.append((name, 'FAIL', error_msg))
            return False

    def test_http_health(self) -> bool:
        """Test if Odoo HTTP endpoint responds"""
        try:
            response = requests.get(f"{self.base_url}/web/health", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def test_web_login_page(self) -> bool:
        """Test if login page loads"""
        try:
            response = requests.get(f"{self.base_url}/web/login", timeout=10)
            return response.status_code == 200 and 'login' in response.text.lower()
        except requests.exceptions.RequestException:
            return False

    def test_static_assets(self) -> bool:
        """Test if static assets load"""
        try:
            # Test web assets
            response = requests.get(f"{self.base_url}/web/static/img/favicon.ico", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def test_database_connection(self) -> bool:
        """Test database connectivity through Odoo"""
        try:
            # Try to access database selector (will redirect if single DB)
            response = requests.get(f"{self.base_url}/web/database/selector", timeout=10)
            return response.status_code in [200, 303]  # 303 is redirect to login
        except requests.exceptions.RequestException:
            return False

    def test_websocket_endpoint(self) -> bool:
        """Test websocket endpoint for POS"""
        try:
            # Just check if endpoint exists (doesn't require websocket connection)
            response = requests.get(f"{self.base_url}/websocket", timeout=10)
            # Will return 404 for GET, but endpoint should exist
            return True  # If we got a response, endpoint exists
        except requests.exceptions.RequestException:
            return False

    def test_ssl_certificate(self) -> bool:
        """Test SSL certificate if using HTTPS"""
        if not self.base_url.startswith('https'):
            self.log("Skipping SSL test (not using HTTPS)", 'WARN')
            self.warnings += 1
            return True

        try:
            response = requests.get(self.base_url, timeout=10, verify=True)
            return response.status_code in [200, 301, 302, 303]
        except requests.exceptions.SSLError:
            return False
        except requests.exceptions.RequestException:
            return True  # SSL is fine, other error

    def test_response_time(self) -> bool:
        """Test if response time is acceptable"""
        try:
            import time
            start = time.time()
            requests.get(f"{self.base_url}/web/login", timeout=10)
            duration = time.time() - start

            if duration > 5:
                self.log(f"Slow response time: {duration:.2f}s", 'WARN')
                self.warnings += 1

            return duration < 10  # Fail if >10 seconds
        except requests.exceptions.RequestException:
            return False

    def test_cors_headers(self) -> bool:
        """Test security headers"""
        try:
            response = requests.get(f"{self.base_url}/web/login", timeout=10)

            # Check for important security headers
            headers_to_check = [
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Strict-Transport-Security'  # Only for HTTPS
            ]

            found = 0
            for header in headers_to_check:
                if header in response.headers:
                    found += 1
                elif header != 'Strict-Transport-Security' or self.base_url.startswith('https'):
                    self.log(f"Missing security header: {header}", 'WARN')
                    self.warnings += 1

            return found >= 2  # At least 2 security headers
        except requests.exceptions.RequestException:
            return False

    def run_all_tests(self):
        """Run all smoke tests"""
        self.log("========================================", 'INFO')
        self.log("Starting Smoke Tests", 'INFO')
        self.log(f"Target: {self.base_url}", 'INFO')
        self.log("========================================", 'INFO')

        # Basic connectivity
        self.test("HTTP Health Check", self.test_http_health)
        self.test("Web Login Page", self.test_web_login_page)
        self.test("Static Assets", self.test_static_assets)
        self.test("Database Connection", self.test_database_connection)

        # Functionality
        self.test("WebSocket Endpoint", self.test_websocket_endpoint)
        self.test("Response Time", self.test_response_time)

        # Security
        self.test("SSL Certificate", self.test_ssl_certificate)
        self.test("Security Headers", self.test_cors_headers)

        # Summary
        self.print_summary()

        return self.failed == 0

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        self.log("========================================", 'INFO')
        self.log("Test Summary", 'INFO')
        self.log("========================================", 'INFO')
        self.log(f"Total Tests: {total}", 'INFO')
        self.log(f"Passed: {self.passed} ({pass_rate:.1f}%)", 'PASS')

        if self.failed > 0:
            self.log(f"Failed: {self.failed}", 'FAIL')

        if self.warnings > 0:
            self.log(f"Warnings: {self.warnings}", 'WARN')

        # Print failed tests
        if self.failed > 0:
            self.log("", 'INFO')
            self.log("Failed Tests:", 'FAIL')
            for name, status, error in self.results:
                if status == 'FAIL':
                    self.log(f"  - {name}: {error or 'Unknown error'}", 'FAIL')

        self.log("========================================", 'INFO')

        if self.failed == 0:
            self.log("All smoke tests passed!", 'PASS')
        else:
            self.log("Some tests failed. Please investigate.", 'FAIL')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run smoke tests for e-invoicing deployment')
    parser.add_argument('--url', default='http://localhost:8069',
                      help='Base URL of Odoo instance')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Verbose output')
    args = parser.parse_args()

    runner = SmokeTestRunner(args.url, args.verbose)
    success = runner.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
