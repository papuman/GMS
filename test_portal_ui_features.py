#!/usr/bin/env python3
"""
Test Portal UI Features via HTTP requests
Tests what's actually available in the portal web interface
"""

import requests
from bs4 import BeautifulSoup
import json
import re

BASE_URL = 'http://localhost:8070'
TEST_USER = {
    'login': 'john.portal@gymtest.com',
    'password': 'portal123'
}

class PortalUITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.csrf_token = None

    def login(self, login, password):
        """Login to portal"""
        print(f"\n=== Testing Portal Login ===")

        # Get login page first to get CSRF token
        login_page = self.session.get(f'{self.base_url}/web/login')

        if login_page.status_code == 200:
            soup = BeautifulSoup(login_page.text, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrf_token'})
            if csrf_input:
                self.csrf_token = csrf_input.get('value')

        # Perform login
        login_data = {
            'login': login,
            'password': password,
            'csrf_token': self.csrf_token
        }

        response = self.session.post(
            f'{self.base_url}/web/login',
            data=login_data,
            allow_redirects=True
        )

        if response.status_code == 200:
            # Check if login successful by looking for logout link or user menu
            if 'o_user_menu' in response.text or '/web/session/logout' in response.text:
                print(f"✓ Successfully logged in as {login}")
                print(f"  Redirected to: {response.url}")
                return True
            else:
                print(f"✗ Login failed - no user menu found")
                return False
        else:
            print(f"✗ Login failed with status code: {response.status_code}")
            return False

    def test_portal_home(self):
        """Test portal home page"""
        print(f"\n=== Testing Portal Home (/my) ===")

        response = self.session.get(f'{self.base_url}/my')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            print(f"✓ Portal home accessible")

            # Find available menu items/links
            links = soup.find_all('a')
            portal_links = []

            for link in links:
                href = link.get('href', '')
                if href.startswith('/my') and href != '/my':
                    text = link.get_text(strip=True)
                    if text and href not in [l['url'] for l in portal_links]:
                        portal_links.append({
                            'text': text,
                            'url': href
                        })

            print(f"\n  Available Portal Sections:")
            for link in portal_links[:15]:  # Show first 15
                print(f"    - {link['text']}: {link['url']}")

            return portal_links
        else:
            print(f"✗ Cannot access portal home: {response.status_code}")
            return []

    def test_invoices(self):
        """Test invoice viewing"""
        print(f"\n=== Testing Invoices (/my/invoices) ===")

        response = self.session.get(f'{self.base_url}/my/invoices')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"✓ Invoices page accessible")

            # Look for invoice listings
            tables = soup.find_all('table')
            if tables:
                print(f"  Found {len(tables)} table(s) with data")

            # Look for download buttons
            download_links = soup.find_all('a', href=re.compile(r'/my/invoices/.*pdf'))
            if download_links:
                print(f"  ✓ PDF download available ({len(download_links)} links)")
            else:
                print(f"  ⚠ No PDF download links found")

            # Look for payment buttons
            pay_buttons = soup.find_all(['a', 'button'], text=re.compile(r'pay|payment', re.I))
            if pay_buttons:
                print(f"  ✓ Payment buttons found ({len(pay_buttons)})")
            else:
                print(f"  ⚠ No payment buttons found")

            return True
        else:
            print(f"✗ Cannot access invoices: {response.status_code}")
            return False

    def test_orders(self):
        """Test sale order viewing"""
        print(f"\n=== Testing Orders (/my/orders) ===")

        response = self.session.get(f'{self.base_url}/my/orders')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"✓ Orders page accessible")

            # Look for order listings
            tables = soup.find_all('table')
            if tables:
                print(f"  Found {len(tables)} table(s) with data")

            return True
        else:
            print(f"✗ Cannot access orders: {response.status_code}")
            return False

    def test_account_settings(self):
        """Test account settings page"""
        print(f"\n=== Testing Account Settings (/my/account) ===")

        response = self.session.get(f'{self.base_url}/my/account')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"✓ Account page accessible")

            # Look for editable fields
            form = soup.find('form')
            if form:
                inputs = form.find_all(['input', 'textarea', 'select'])
                editable_fields = []

                for inp in inputs:
                    field_name = inp.get('name', '')
                    field_type = inp.get('type', inp.name)
                    if field_name and field_name not in ['csrf_token', 'redirect']:
                        editable_fields.append({
                            'name': field_name,
                            'type': field_type
                        })

                print(f"\n  Editable Fields:")
                for field in editable_fields[:10]:  # Show first 10
                    print(f"    - {field['name']} ({field['type']})")

                # Check for save button
                save_button = form.find(['button', 'input'], type='submit')
                if save_button:
                    print(f"\n  ✓ Save button available - users can update info")
                else:
                    print(f"\n  ✗ No save button found")

                return editable_fields
            else:
                print(f"  ⚠ No form found on account page")
                return []
        else:
            print(f"✗ Cannot access account settings: {response.status_code}")
            return []

    def test_portal_features(self):
        """Test various portal endpoints"""
        print(f"\n=== Testing Additional Portal Features ===")

        endpoints = [
            ('/my/quotes', 'Quotations'),
            ('/my/home', 'Portal Dashboard'),
            ('/my/invoices', 'Invoices'),
            ('/my/orders', 'Sale Orders'),
            ('/my/tickets', 'Tickets/Support'),
            ('/shop', 'eCommerce Shop'),
            ('/my/security', 'Security Settings'),
        ]

        results = {}

        for url, name in endpoints:
            try:
                response = self.session.get(f'{self.base_url}{url}', timeout=5)
                if response.status_code == 200:
                    print(f"  ✓ {name} - Available")
                    results[name] = 'Available'
                elif response.status_code == 404:
                    print(f"  ✗ {name} - Not Found")
                    results[name] = 'Not Available'
                elif response.status_code == 403:
                    print(f"  ✗ {name} - Access Denied")
                    results[name] = 'Access Denied'
                else:
                    print(f"  ? {name} - Status {response.status_code}")
                    results[name] = f'Status {response.status_code}'
            except Exception as e:
                print(f"  ✗ {name} - Error: {str(e)[:50]}")
                results[name] = 'Error'

        return results

    def analyze_portal_structure(self):
        """Analyze overall portal structure"""
        print(f"\n=== Analyzing Portal Structure ===")

        response = self.session.get(f'{self.base_url}/my')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for navigation menu
            nav = soup.find(['nav', 'ul', 'div'], class_=re.compile(r'nav|menu|sidebar', re.I))

            if nav:
                print(f"✓ Navigation menu found")
                menu_items = nav.find_all('a')
                print(f"  Menu has {len(menu_items)} items")

            # Look for widgets/cards
            cards = soup.find_all(['div'], class_=re.compile(r'card|widget|panel', re.I))
            if cards:
                print(f"✓ Found {len(cards)} card/widget elements")

            # Check for responsive design
            if 'viewport' in response.text:
                print(f"✓ Mobile-responsive design detected")

            return True
        else:
            return False

def main():
    """Main test execution"""
    print("="*70)
    print("GMS PORTAL UI FEATURE TESTS")
    print("="*70)

    tester = PortalUITester(BASE_URL)

    # Login
    if not tester.login(TEST_USER['login'], TEST_USER['password']):
        print("\n✗ Login failed. Cannot continue tests.")
        return

    # Run tests
    portal_links = tester.test_portal_home()
    tester.test_invoices()
    tester.test_orders()
    editable_fields = tester.test_account_settings()
    feature_results = tester.test_portal_features()
    tester.analyze_portal_structure()

    # Summary
    print(f"\n{'='*70}")
    print("UI TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Portal Sections Found: {len(portal_links)}")
    print(f"Editable Fields: {len(editable_fields)}")
    print(f"Feature Availability:")
    for feature, status in feature_results.items():
        print(f"  {feature}: {status}")

    # Save results
    results = {
        'portal_sections': portal_links,
        'editable_fields': editable_fields,
        'features': feature_results,
        'test_user': TEST_USER['login']
    }

    with open('/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/portal_ui_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ UI test results saved")

if __name__ == '__main__':
    main()
