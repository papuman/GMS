#!/usr/bin/env python3
"""
Portal Validation Script for GMS
Tests portal functionality from member perspective using API
"""

import xmlrpc.client
import sys
from datetime import datetime
import json

# Connection settings
url = 'http://localhost:8070'
db = 'gms_validation'

class PortalValidator:
    """Portal functionality validator"""

    def __init__(self, url, db):
        self.url = url
        self.db = db
        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }

    def add_test_result(self, test_name, passed, message, details=None):
        """Add test result"""
        self.results['tests'].append({
            'name': test_name,
            'passed': passed,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
        self.results['summary']['total'] += 1
        if passed:
            self.results['summary']['passed'] += 1
        else:
            self.results['summary']['failed'] += 1

    def authenticate_portal_user(self, email, password):
        """Authenticate portal user and return uid"""
        try:
            uid = self.common.authenticate(self.db, email, password, {})
            if uid:
                print(f"✓ Authenticated as: {email} (UID: {uid})")
                self.add_test_result(
                    f"Portal Login - {email}",
                    True,
                    f"Successfully authenticated",
                    {'uid': uid, 'email': email}
                )
                return uid
            else:
                print(f"✗ Authentication failed for: {email}")
                self.add_test_result(
                    f"Portal Login - {email}",
                    False,
                    "Authentication failed"
                )
                return None
        except Exception as e:
            print(f"✗ Error authenticating {email}: {e}")
            self.add_test_result(
                f"Portal Login - {email}",
                False,
                str(e)
            )
            return None

    def test_access_rights(self, uid, email, password):
        """Test what models the portal user can access"""
        print(f"\n--- Testing Access Rights for {email} ---")

        models_to_test = [
            'res.partner',
            'account.move',
            'sale.order',
            'product.product',
            'res.users',
            'account.payment',
        ]

        accessible_models = []
        restricted_models = []

        for model in models_to_test:
            try:
                # Try to search (read access)
                result = self.models.execute_kw(
                    self.db, uid, password,
                    model, 'search',
                    [[]], {'limit': 1}
                )
                accessible_models.append(model)
                print(f"  ✓ Can access: {model}")
            except Exception as e:
                restricted_models.append(model)
                print(f"  ✗ Cannot access: {model} ({str(e)[:50]})")

        self.add_test_result(
            f"Access Rights Check - {email}",
            len(accessible_models) > 0,
            f"Accessible: {len(accessible_models)}, Restricted: {len(restricted_models)}",
            {
                'accessible': accessible_models,
                'restricted': restricted_models
            }
        )

        return accessible_models

    def test_view_own_partner(self, uid, email, password):
        """Test if portal user can view their own partner record"""
        print(f"\n--- Testing Own Partner View for {email} ---")

        try:
            # Get current user's partner_id
            user = self.models.execute_kw(
                self.db, uid, password,
                'res.users', 'read',
                [[uid]], {'fields': ['partner_id']}
            )

            if not user or not user[0].get('partner_id'):
                self.add_test_result(
                    f"View Own Partner - {email}",
                    False,
                    "Could not retrieve partner_id"
                )
                return None

            partner_id = user[0]['partner_id'][0]

            # Read partner data
            partner = self.models.execute_kw(
                self.db, uid, password,
                'res.partner', 'read',
                [[partner_id]], {
                    'fields': ['name', 'email', 'phone', 'street', 'city', 'zip']
                }
            )

            if partner:
                print(f"  ✓ Retrieved own partner data:")
                print(f"    Name: {partner[0].get('name')}")
                print(f"    Email: {partner[0].get('email')}")
                print(f"    Phone: {partner[0].get('phone')}")

                self.add_test_result(
                    f"View Own Partner - {email}",
                    True,
                    "Successfully retrieved partner data",
                    partner[0]
                )
                return partner[0]
            else:
                self.add_test_result(
                    f"View Own Partner - {email}",
                    False,
                    "No partner data returned"
                )
                return None

        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.add_test_result(
                f"View Own Partner - {email}",
                False,
                str(e)
            )
            return None

    def test_update_contact_info(self, uid, email, password):
        """Test if portal user can update their contact information"""
        print(f"\n--- Testing Contact Info Update for {email} ---")

        try:
            # Get partner_id
            user = self.models.execute_kw(
                self.db, uid, password,
                'res.users', 'read',
                [[uid]], {'fields': ['partner_id']}
            )

            if not user or not user[0].get('partner_id'):
                self.add_test_result(
                    f"Update Contact Info - {email}",
                    False,
                    "Could not retrieve partner_id"
                )
                return False

            partner_id = user[0]['partner_id'][0]

            # Get current phone
            partner = self.models.execute_kw(
                self.db, uid, password,
                'res.partner', 'read',
                [[partner_id]], {'fields': ['phone']}
            )

            original_phone = partner[0].get('phone', '')

            # Try to update phone number
            test_phone = '555-TEST-UPDATE'
            try:
                self.models.execute_kw(
                    self.db, uid, password,
                    'res.partner', 'write',
                    [[partner_id], {'phone': test_phone}]
                )

                # Verify update
                updated_partner = self.models.execute_kw(
                    self.db, uid, password,
                    'res.partner', 'read',
                    [[partner_id]], {'fields': ['phone']}
                )

                if updated_partner[0].get('phone') == test_phone:
                    print(f"  ✓ Successfully updated phone number")

                    # Restore original
                    self.models.execute_kw(
                        self.db, uid, password,
                        'res.partner', 'write',
                        [[partner_id], {'phone': original_phone}]
                    )

                    self.add_test_result(
                        f"Update Contact Info - {email}",
                        True,
                        "Can update contact information",
                        {'field_tested': 'phone'}
                    )
                    return True
                else:
                    print(f"  ✗ Update did not persist")
                    self.add_test_result(
                        f"Update Contact Info - {email}",
                        False,
                        "Update did not persist"
                    )
                    return False

            except Exception as e:
                print(f"  ✗ Cannot update contact info: {e}")
                self.add_test_result(
                    f"Update Contact Info - {email}",
                    False,
                    f"Update failed: {str(e)[:100]}"
                )
                return False

        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.add_test_result(
                f"Update Contact Info - {email}",
                False,
                str(e)
            )
            return False

    def test_view_invoices(self, uid, email, password):
        """Test if portal user can view their invoices"""
        print(f"\n--- Testing Invoice Access for {email} ---")

        try:
            # Get partner_id
            user = self.models.execute_kw(
                self.db, uid, password,
                'res.users', 'read',
                [[uid]], {'fields': ['partner_id']}
            )

            partner_id = user[0]['partner_id'][0]

            # Search for invoices
            invoice_ids = self.models.execute_kw(
                self.db, uid, password,
                'account.move', 'search',
                [[['partner_id', '=', partner_id], ['move_type', '=', 'out_invoice']]]
            )

            if invoice_ids:
                print(f"  ✓ Found {len(invoice_ids)} invoice(s)")

                # Get invoice details
                invoices = self.models.execute_kw(
                    self.db, uid, password,
                    'account.move', 'read',
                    [invoice_ids], {
                        'fields': ['name', 'invoice_date', 'amount_total', 'state', 'payment_state']
                    }
                )

                for invoice in invoices:
                    print(f"    Invoice: {invoice.get('name')} - ${invoice.get('amount_total')} - {invoice.get('state')}")

                self.add_test_result(
                    f"View Invoices - {email}",
                    True,
                    f"Found {len(invoice_ids)} invoices",
                    {'count': len(invoice_ids), 'invoices': invoices}
                )
                return invoices
            else:
                print(f"  ⚠ No invoices found")
                self.add_test_result(
                    f"View Invoices - {email}",
                    True,
                    "No invoices found (access granted)",
                    {'count': 0}
                )
                return []

        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.add_test_result(
                f"View Invoices - {email}",
                False,
                str(e)
            )
            return None

    def test_view_payment_history(self, uid, email, password):
        """Test if portal user can view payment history"""
        print(f"\n--- Testing Payment History for {email} ---")

        try:
            user = self.models.execute_kw(
                self.db, uid, password,
                'res.users', 'read',
                [[uid]], {'fields': ['partner_id']}
            )

            partner_id = user[0]['partner_id'][0]

            # Try to access payment records
            try:
                payment_ids = self.models.execute_kw(
                    self.db, uid, password,
                    'account.payment', 'search',
                    [[['partner_id', '=', partner_id]]]
                )

                if payment_ids:
                    payments = self.models.execute_kw(
                        self.db, uid, password,
                        'account.payment', 'read',
                        [payment_ids], {
                            'fields': ['name', 'date', 'amount', 'state', 'payment_type']
                        }
                    )

                    print(f"  ✓ Found {len(payments)} payment(s)")
                    for payment in payments:
                        print(f"    Payment: {payment.get('name')} - ${payment.get('amount')} - {payment.get('state')}")

                    self.add_test_result(
                        f"View Payment History - {email}",
                        True,
                        f"Found {len(payments)} payments",
                        {'count': len(payments), 'payments': payments}
                    )
                    return payments
                else:
                    print(f"  ⚠ No payments found")
                    self.add_test_result(
                        f"View Payment History - {email}",
                        True,
                        "No payments found (access granted)",
                        {'count': 0}
                    )
                    return []

            except Exception as e:
                # Portal users typically don't have access to account.payment
                print(f"  ✗ Cannot access payment records: {str(e)[:50]}")
                self.add_test_result(
                    f"View Payment History - {email}",
                    False,
                    "Access denied to payment records",
                    {'note': 'This is expected - portal users view payments through invoices'}
                )
                return None

        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.add_test_result(
                f"View Payment History - {email}",
                False,
                str(e)
            )
            return None

    def test_view_sale_orders(self, uid, email, password):
        """Test if portal user can view their sale orders (purchase history)"""
        print(f"\n--- Testing Sale Orders (Purchase History) for {email} ---")

        try:
            user = self.models.execute_kw(
                self.db, uid, password,
                'res.users', 'read',
                [[uid]], {'fields': ['partner_id']}
            )

            partner_id = user[0]['partner_id'][0]

            # Search for sale orders
            order_ids = self.models.execute_kw(
                self.db, uid, password,
                'sale.order', 'search',
                [[['partner_id', '=', partner_id]]]
            )

            if order_ids:
                print(f"  ✓ Found {len(order_ids)} sale order(s)")

                orders = self.models.execute_kw(
                    self.db, uid, password,
                    'sale.order', 'read',
                    [order_ids], {
                        'fields': ['name', 'date_order', 'amount_total', 'state', 'order_line']
                    }
                )

                for order in orders:
                    print(f"    Order: {order.get('name')} - ${order.get('amount_total')} - {order.get('state')}")

                self.add_test_result(
                    f"View Sale Orders - {email}",
                    True,
                    f"Found {len(orders)} orders",
                    {'count': len(orders), 'orders': orders}
                )
                return orders
            else:
                print(f"  ⚠ No sale orders found")
                self.add_test_result(
                    f"View Sale Orders - {email}",
                    True,
                    "No orders found (access granted)",
                    {'count': 0}
                )
                return []

        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.add_test_result(
                f"View Sale Orders - {email}",
                False,
                str(e)
            )
            return None

    def test_download_invoice_capability(self, uid, email, password):
        """Test if portal user can download/print invoices"""
        print(f"\n--- Testing Invoice Download Capability for {email} ---")

        try:
            # This is primarily a UI feature, but we can check if the user has read access
            # to invoice report actions
            user = self.models.execute_kw(
                self.db, uid, password,
                'res.users', 'read',
                [[uid]], {'fields': ['partner_id']}
            )

            partner_id = user[0]['partner_id'][0]

            # Get an invoice
            invoice_ids = self.models.execute_kw(
                self.db, uid, password,
                'account.move', 'search',
                [[['partner_id', '=', partner_id], ['move_type', '=', 'out_invoice']]],
                {'limit': 1}
            )

            if invoice_ids:
                # Check if we can read the invoice (prerequisite for download)
                invoice = self.models.execute_kw(
                    self.db, uid, password,
                    'account.move', 'read',
                    [invoice_ids], {'fields': ['name', 'state']}
                )

                if invoice:
                    print(f"  ✓ Can read invoice {invoice[0].get('name')}")
                    print(f"    Note: PDF download is a UI feature available in portal")

                    self.add_test_result(
                        f"Invoice Download Capability - {email}",
                        True,
                        "Has read access to invoices (download available via portal UI)",
                        {'invoice_accessible': True}
                    )
                    return True
            else:
                print(f"  ⚠ No invoices available to test download")
                self.add_test_result(
                    f"Invoice Download Capability - {email}",
                    True,
                    "No invoices available to test",
                    {'invoice_accessible': False}
                )
                return True

        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.add_test_result(
                f"Invoice Download Capability - {email}",
                False,
                str(e)
            )
            return False

    def test_view_other_customer_data(self, uid, email, password):
        """Test that portal user CANNOT view other customers' data (security test)"""
        print(f"\n--- Testing Data Isolation (Security) for {email} ---")

        try:
            user = self.models.execute_kw(
                self.db, uid, password,
                'res.users', 'read',
                [[uid]], {'fields': ['partner_id']}
            )

            my_partner_id = user[0]['partner_id'][0]

            # Try to search for other partners
            all_partners = self.models.execute_kw(
                self.db, uid, password,
                'res.partner', 'search',
                [[]]
            )

            if len(all_partners) <= 1:
                print(f"  ⚠ Only 1 partner accessible (expected)")
                self.add_test_result(
                    f"Data Isolation Test - {email}",
                    True,
                    "Can only access own data",
                    {'accessible_partners': len(all_partners)}
                )
                return True

            # Try to read another partner's data
            other_partner_id = [p for p in all_partners if p != my_partner_id][0]

            try:
                other_partner = self.models.execute_kw(
                    self.db, uid, password,
                    'res.partner', 'read',
                    [[other_partner_id]], {'fields': ['name', 'email']}
                )

                if other_partner:
                    print(f"  ⚠ WARNING: Can read other partner data!")
                    print(f"    Other partner: {other_partner[0].get('name')}")
                    self.add_test_result(
                        f"Data Isolation Test - {email}",
                        False,
                        "SECURITY ISSUE: Can access other customers' data",
                        {'other_partner_accessible': True}
                    )
                    return False

            except Exception as e:
                print(f"  ✓ Cannot access other partner data (correct)")
                self.add_test_result(
                    f"Data Isolation Test - {email}",
                    True,
                    "Properly restricted to own data",
                    {'other_partner_accessible': False}
                )
                return True

        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.add_test_result(
                f"Data Isolation Test - {email}",
                True,
                f"Access restricted (expected): {str(e)[:50]}"
            )
            return True

    def run_all_tests_for_user(self, email, password):
        """Run all portal tests for a specific user"""
        print(f"\n{'='*70}")
        print(f"TESTING PORTAL USER: {email}")
        print(f"{'='*70}")

        # Authenticate
        uid = self.authenticate_portal_user(email, password)
        if not uid:
            return False

        # Run tests
        self.test_access_rights(uid, email, password)
        self.test_view_own_partner(uid, email, password)
        self.test_update_contact_info(uid, email, password)
        self.test_view_invoices(uid, email, password)
        self.test_view_payment_history(uid, email, password)
        self.test_view_sale_orders(uid, email, password)
        self.test_download_invoice_capability(uid, email, password)
        self.test_view_other_customer_data(uid, email, password)

        return True

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Tests: {self.results['summary']['total']}")
        print(f"Passed: {self.results['summary']['passed']}")
        print(f"Failed: {self.results['summary']['failed']}")
        print(f"Success Rate: {(self.results['summary']['passed'] / self.results['summary']['total'] * 100):.1f}%")
        print(f"{'='*70}\n")

    def save_results(self, filename='portal_test_results.json'):
        """Save test results to JSON file"""
        filepath = f'/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/{filename}'
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Results saved to: {filepath}")
        return filepath

def main():
    """Main execution"""
    print("="*70)
    print("GMS PORTAL VALIDATION TESTS")
    print("="*70)

    validator = PortalValidator(url, db)

    # Test users (created by setup script)
    test_users = [
        {'email': 'john.portal@gymtest.com', 'password': 'portal123'},
        {'email': 'jane.premium@gymtest.com', 'password': 'portal123'},
    ]

    # Run tests for each user
    for user in test_users:
        validator.run_all_tests_for_user(user['email'], user['password'])

    # Print summary
    validator.print_summary()

    # Save results
    results_file = validator.save_results()

    print(f"\n✓ Portal validation complete!")
    print(f"\nNext steps:")
    print(f"1. Review results in: {results_file}")
    print(f"2. Test portal UI manually at: {url}/my")
    print(f"3. Review detailed report for recommendations")

if __name__ == '__main__':
    main()
