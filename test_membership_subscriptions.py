#!/usr/bin/env python3
"""
Comprehensive Membership and Subscription Testing Script for GMS
Tests recurring billing, subscription management, and invoice generation
"""

import xmlrpc.client
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration
URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

class MembershipTester:
    def __init__(self):
        self.common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        self.models = None
        self.uid = None
        self.results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'tests': []
        }

    def connect(self):
        """Authenticate and connect to Odoo"""
        print_header("CONNECTING TO ODOO")
        try:
            self.uid = self.common.authenticate(DB, USERNAME, PASSWORD, {})
            if self.uid:
                self.models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')
                print_success(f"Connected successfully as user ID: {self.uid}")
                return True
            else:
                print_error("Authentication failed")
                return False
        except Exception as e:
            print_error(f"Connection failed: {e}")
            return False

    def record_test(self, name, passed, details):
        """Record test result"""
        self.results['total'] += 1
        if passed:
            self.results['passed'] += 1
            print_success(f"{name}")
        else:
            self.results['failed'] += 1
            print_error(f"{name}")

        self.results['tests'].append({
            'name': name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

        if details:
            print_info(f"  Details: {details}")

    def check_module_installed(self, module_name):
        """Check if a module is installed"""
        print_header(f"CHECKING MODULE: {module_name}")
        try:
            module_ids = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'ir.module.module', 'search_read',
                [[['name', '=', module_name]]],
                {'fields': ['name', 'state']}
            )

            if module_ids and module_ids[0]['state'] == 'installed':
                self.record_test(
                    f"Module {module_name} is installed",
                    True,
                    f"State: {module_ids[0]['state']}"
                )
                return True
            else:
                self.record_test(
                    f"Module {module_name} is NOT installed",
                    False,
                    f"State: {module_ids[0]['state'] if module_ids else 'not found'}"
                )
                return False
        except Exception as e:
            self.record_test(
                f"Error checking module {module_name}",
                False,
                str(e)
            )
            return False

    def get_or_create_tax(self):
        """Get or create 13% IVA tax"""
        print_header("SETTING UP TAX CONFIGURATION")
        try:
            # Search for existing 13% tax
            tax_ids = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'account.tax', 'search_read',
                [[['amount', '=', 13], ['type_tax_use', '=', 'sale']]],
                {'fields': ['name', 'amount'], 'limit': 1}
            )

            if tax_ids:
                print_success(f"Found existing tax: {tax_ids[0]['name']} - {tax_ids[0]['amount']}%")
                return tax_ids[0]['id']

            # Create 13% IVA tax
            tax_id = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'account.tax', 'create',
                [{
                    'name': 'IVA 13%',
                    'amount': 13,
                    'amount_type': 'percent',
                    'type_tax_use': 'sale',
                    'description': 'IVA',
                }]
            )

            print_success(f"Created new 13% IVA tax with ID: {tax_id}")
            return tax_id

        except Exception as e:
            print_error(f"Error setting up tax: {e}")
            return None

    def get_crc_currency(self):
        """Get CRC currency"""
        print_header("SETTING UP CURRENCY CONFIGURATION")
        try:
            currency_ids = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'res.currency', 'search_read',
                [[['name', '=', 'CRC']]],
                {'fields': ['name', 'symbol'], 'limit': 1}
            )

            if currency_ids:
                print_success(f"Found CRC currency: {currency_ids[0]['name']} ({currency_ids[0]['symbol']})")
                return currency_ids[0]['id']
            else:
                print_error("CRC currency not found")
                return None

        except Exception as e:
            print_error(f"Error getting CRC currency: {e}")
            return None

    def create_subscription_template(self, name, interval, interval_type):
        """Create a subscription template (recurrence)"""
        try:
            # Check if template exists
            template_ids = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.temporal.recurrence', 'search',
                [[['duration', '=', interval], ['unit', '=', interval_type]]]
            )

            if template_ids:
                print_info(f"Subscription template '{name}' already exists")
                return template_ids[0]

            # Create new template
            template_id = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.temporal.recurrence', 'create',
                [{
                    'duration': interval,
                    'unit': interval_type,
                }]
            )

            print_success(f"Created subscription template: {name}")
            return template_id

        except Exception as e:
            print_error(f"Error creating subscription template '{name}': {e}")
            return None

    def create_membership_product(self, name, price, recurring=True, interval=1, interval_type='month'):
        """Create a membership product with optional recurring billing"""
        print_header(f"CREATING PRODUCT: {name}")
        try:
            tax_id = self.get_or_create_tax()
            if not tax_id:
                print_error("Cannot create product without tax")
                return None

            product_data = {
                'name': name,
                'type': 'service',
                'list_price': price,
                'taxes_id': [(6, 0, [tax_id])],
                'recurring_invoice': recurring,
                'sale_ok': True,
                'purchase_ok': False,
            }

            if recurring:
                template_id = self.create_subscription_template(
                    f"{name} Template",
                    interval,
                    interval_type
                )
                if template_id:
                    product_data['product_subscription_pricing_ids'] = [(0, 0, {
                        'recurrence_id': template_id,
                        'price': price,
                    })]

            product_id = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'product.product', 'create',
                [product_data]
            )

            # Verify creation
            product = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'product.product', 'read',
                [product_id],
                {'fields': ['name', 'list_price', 'recurring_invoice', 'taxes_id']}
            )[0]

            self.record_test(
                f"Created product: {name}",
                True,
                f"ID: {product_id}, Price: ₡{price:,.2f}, Recurring: {recurring}"
            )

            return product_id

        except Exception as e:
            self.record_test(
                f"Failed to create product: {name}",
                False,
                str(e)
            )
            return None

    def create_test_customer(self, name, email):
        """Create a test customer"""
        try:
            # Check if customer exists
            partner_ids = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'res.partner', 'search',
                [[['email', '=', email]]]
            )

            if partner_ids:
                print_info(f"Customer '{name}' already exists")
                return partner_ids[0]

            partner_id = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'res.partner', 'create',
                [{
                    'name': name,
                    'email': email,
                    'phone': '+506-8888-8888',
                    'customer_rank': 1,
                }]
            )

            print_success(f"Created test customer: {name}")
            return partner_id

        except Exception as e:
            print_error(f"Error creating customer '{name}': {e}")
            return None

    def create_subscription_order(self, customer_id, product_id, product_name):
        """Create a subscription sale order"""
        print_header(f"CREATING SUBSCRIPTION: {product_name}")
        try:
            # Create sale order
            order_id = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.order', 'create',
                [{
                    'partner_id': customer_id,
                    'is_subscription': True,
                }]
            )

            # Add order line
            line_id = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.order.line', 'create',
                [{
                    'order_id': order_id,
                    'product_id': product_id,
                    'product_uom_qty': 1,
                }]
            )

            # Confirm the order
            self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.order', 'action_confirm',
                [[order_id]]
            )

            # Get order details
            order = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.order', 'read',
                [order_id],
                {'fields': ['name', 'amount_total', 'state', 'is_subscription']}
            )[0]

            self.record_test(
                f"Created subscription order: {order['name']}",
                order['state'] in ['sale', 'subscription'],
                f"State: {order['state']}, Total: ₡{order['amount_total']:,.2f}"
            )

            return order_id

        except Exception as e:
            self.record_test(
                f"Failed to create subscription for {product_name}",
                False,
                str(e)
            )
            return None

    def verify_invoice_generation(self, order_id, product_name):
        """Verify that invoices are generated for subscription"""
        print_header(f"VERIFYING INVOICE GENERATION: {product_name}")
        try:
            # Get order
            order = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.order', 'read',
                [order_id],
                {'fields': ['name', 'invoice_ids', 'amount_total']}
            )[0]

            if order['invoice_ids']:
                # Get invoice details
                invoices = self.models.execute_kw(
                    DB, self.uid, PASSWORD,
                    'account.move', 'read',
                    [order['invoice_ids']],
                    {'fields': ['name', 'amount_total', 'state', 'currency_id']}
                )

                for invoice in invoices:
                    print_info(f"Invoice: {invoice['name']}, Amount: ₡{invoice['amount_total']:,.2f}, State: {invoice['state']}")

                self.record_test(
                    f"Invoice(s) generated for {product_name}",
                    True,
                    f"Generated {len(invoices)} invoice(s)"
                )
                return True
            else:
                self.record_test(
                    f"No invoices generated for {product_name}",
                    False,
                    "Invoice generation may require time or manual trigger"
                )
                return False

        except Exception as e:
            self.record_test(
                f"Error verifying invoices for {product_name}",
                False,
                str(e)
            )
            return False

    def verify_tax_calculation(self, order_id, expected_base, product_name):
        """Verify 13% tax calculation on order"""
        print_header(f"VERIFYING TAX CALCULATION: {product_name}")
        try:
            order = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.order', 'read',
                [order_id],
                {'fields': ['amount_untaxed', 'amount_tax', 'amount_total']}
            )[0]

            expected_tax = expected_base * 0.13
            expected_total = expected_base + expected_tax

            tax_correct = abs(order['amount_tax'] - expected_tax) < 0.01
            total_correct = abs(order['amount_total'] - expected_total) < 0.01

            self.record_test(
                f"Tax calculation correct for {product_name}",
                tax_correct and total_correct,
                f"Base: ₡{order['amount_untaxed']:,.2f}, Tax: ₡{order['amount_tax']:,.2f} (expected ₡{expected_tax:,.2f}), Total: ₡{order['amount_total']:,.2f}"
            )

            return tax_correct and total_correct

        except Exception as e:
            self.record_test(
                f"Error verifying tax for {product_name}",
                False,
                str(e)
            )
            return False

    def test_subscription_cancellation(self, order_id, product_name):
        """Test subscription cancellation"""
        print_header(f"TESTING SUBSCRIPTION CANCELLATION: {product_name}")
        try:
            # Cancel the subscription
            self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.order', 'action_cancel',
                [[order_id]]
            )

            # Verify cancellation
            order = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.order', 'read',
                [order_id],
                {'fields': ['name', 'state']}
            )[0]

            self.record_test(
                f"Subscription cancellation for {product_name}",
                order['state'] == 'cancel',
                f"Order state: {order['state']}"
            )

            return order['state'] == 'cancel'

        except Exception as e:
            self.record_test(
                f"Error canceling subscription for {product_name}",
                False,
                str(e)
            )
            return False

    def get_subscription_info(self):
        """Get information about subscription configuration"""
        print_header("SUBSCRIPTION MODULE INFORMATION")
        try:
            # Get subscription plans
            plans = self.models.execute_kw(
                DB, self.uid, PASSWORD,
                'sale.temporal.recurrence', 'search_read',
                [[]],
                {'fields': ['duration', 'unit']}
            )

            print_info(f"Available subscription plans: {len(plans)}")
            for plan in plans:
                print(f"  - {plan['duration']} {plan['unit']}(s)")

            return plans

        except Exception as e:
            print_error(f"Error getting subscription info: {e}")
            return []

    def run_all_tests(self):
        """Run comprehensive membership and subscription tests"""
        print_header("GMS MEMBERSHIP & SUBSCRIPTION TESTING")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Connect
        if not self.connect():
            return

        # Check required modules
        if not self.check_module_installed('sale_subscription'):
            print_warning("sale_subscription module not installed - some tests may fail")

        self.check_module_installed('sale_management')
        self.check_module_installed('account')

        # Get subscription info
        self.get_subscription_info()

        # Setup currency
        currency_id = self.get_crc_currency()

        # Create membership products
        print_header("CREATING MEMBERSHIP PRODUCTS")

        products = {
            'monthly': self.create_membership_product(
                'Membresía Mensual GMS',
                25000.00,
                recurring=True,
                interval=1,
                interval_type='month'
            ),
            'quarterly': self.create_membership_product(
                'Membresía Trimestral GMS',
                65000.00,
                recurring=True,
                interval=3,
                interval_type='month'
            ),
            'annual': self.create_membership_product(
                'Membresía Anual GMS',
                240000.00,
                recurring=True,
                interval=1,
                interval_type='year'
            ),
            'day_pass': self.create_membership_product(
                'Pase Diario GMS',
                5000.00,
                recurring=False
            ),
        }

        # Create test customers
        print_header("CREATING TEST CUSTOMERS")
        customers = {
            'monthly': self.create_test_customer('Juan Pérez', 'juan.perez@test.com'),
            'quarterly': self.create_test_customer('María González', 'maria.gonzalez@test.com'),
            'annual': self.create_test_customer('Carlos Rodríguez', 'carlos.rodriguez@test.com'),
            'day_pass': self.create_test_customer('Ana López', 'ana.lopez@test.com'),
        }

        # Create subscriptions and test
        print_header("CREATING AND TESTING SUBSCRIPTIONS")

        test_cases = [
            ('monthly', 'Membresía Mensual GMS', 25000.00),
            ('quarterly', 'Membresía Trimestral GMS', 65000.00),
            ('annual', 'Membresía Anual GMS', 240000.00),
            ('day_pass', 'Pase Diario GMS', 5000.00),
        ]

        orders = {}
        for key, name, price in test_cases:
            if products[key] and customers[key]:
                order_id = self.create_subscription_order(
                    customers[key],
                    products[key],
                    name
                )

                if order_id:
                    orders[key] = order_id

                    # Verify tax calculation
                    self.verify_tax_calculation(order_id, price, name)

                    # Verify invoice generation
                    self.verify_invoice_generation(order_id, name)

        # Test subscription cancellation (only on one subscription)
        if 'monthly' in orders:
            self.test_subscription_cancellation(orders['monthly'], 'Membresía Mensual GMS')

        # Print final results
        self.print_results()

    def print_results(self):
        """Print test results summary"""
        print_header("TEST RESULTS SUMMARY")

        total = self.results['total']
        passed = self.results['passed']
        failed = self.results['failed']
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n{Colors.BOLD}Total Tests: {total}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {failed}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Pass Rate: {pass_rate:.1f}%{Colors.ENDC}\n")

        if failed > 0:
            print(f"{Colors.FAIL}Failed Tests:{Colors.ENDC}")
            for test in self.results['tests']:
                if not test['passed']:
                    print(f"  ✗ {test['name']}")
                    print(f"    {test['details']}")

    def save_results_to_file(self, filename='membership_test_results.txt'):
        """Save results to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("GMS MEMBERSHIP & SUBSCRIPTION TEST RESULTS\n")
            f.write("="*80 + "\n\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Database: {DB}\n")
            f.write(f"URL: {URL}\n\n")

            f.write(f"Total Tests: {self.results['total']}\n")
            f.write(f"Passed: {self.results['passed']}\n")
            f.write(f"Failed: {self.results['failed']}\n")
            f.write(f"Pass Rate: {(self.results['passed']/self.results['total']*100):.1f}%\n\n")

            f.write("="*80 + "\n")
            f.write("DETAILED TEST RESULTS\n")
            f.write("="*80 + "\n\n")

            for test in self.results['tests']:
                status = "PASS" if test['passed'] else "FAIL"
                f.write(f"[{status}] {test['name']}\n")
                f.write(f"  Details: {test['details']}\n")
                f.write(f"  Time: {test['timestamp']}\n\n")

        print_success(f"Results saved to {filename}")

if __name__ == '__main__':
    tester = MembershipTester()
    tester.run_all_tests()
    tester.save_results_to_file('/tmp/membership_test_results.txt')
    print_info("\nTest results saved to /tmp/membership_test_results.txt")
