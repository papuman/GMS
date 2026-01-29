#!/usr/bin/env python3
"""
Portal Setup and Configuration Script for GMS Validation
Creates test members with portal access and configures portal permissions
"""

import xmlrpc.client
import sys
from datetime import datetime, timedelta

# Connection settings
url = 'http://localhost:8070'
db = 'gms_validation'
username = 'admin'
password = 'admin'

def connect_odoo():
    """Establish connection to Odoo"""
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    return uid, models

def create_test_members_with_portal(uid, models):
    """Create test gym members with portal access"""
    print("\n=== Creating Test Members with Portal Access ===\n")

    test_members = [
        {
            'name': 'John Portal Member',
            'email': 'john.portal@gymtest.com',
            'phone': '555-0101',
            'street': '123 Fitness Street',
            'city': 'Gym City',
            'zip': '12345',
            'country_id': None,  # Will be set to US if available
        },
        {
            'name': 'Jane Premium Member',
            'email': 'jane.premium@gymtest.com',
            'phone': '555-0102',
            'street': '456 Wellness Ave',
            'city': 'Health Town',
            'zip': '67890',
            'country_id': None,
        },
        {
            'name': 'Mike Basic Member',
            'email': 'mike.basic@gymtest.com',
            'phone': '555-0103',
            'street': '789 Training Blvd',
            'city': 'Fitness City',
            'zip': '11111',
            'country_id': None,
        }
    ]

    # Get US country if available
    try:
        country_ids = models.execute_kw(db, uid, password,
            'res.country', 'search',
            [[['code', '=', 'US']]], {'limit': 1})
        if country_ids:
            for member in test_members:
                member['country_id'] = country_ids[0]
    except Exception as e:
        print(f"Warning: Could not set country: {e}")

    created_members = []
    for member_data in test_members:
        try:
            # Check if member already exists
            existing = models.execute_kw(db, uid, password,
                'res.partner', 'search',
                [[['email', '=', member_data['email']]]], {'limit': 1})

            if existing:
                partner_id = existing[0]
                print(f"✓ Member already exists: {member_data['name']} (ID: {partner_id})")
            else:
                # Create partner
                partner_id = models.execute_kw(db, uid, password,
                    'res.partner', 'create', [member_data])
                print(f"✓ Created member: {member_data['name']} (ID: {partner_id})")

            created_members.append({
                'id': partner_id,
                'name': member_data['name'],
                'email': member_data['email']
            })

        except Exception as e:
            print(f"✗ Error creating member {member_data['name']}: {e}")

    return created_members

def grant_portal_access(uid, models, members):
    """Grant portal access to members"""
    print("\n=== Granting Portal Access ===\n")

    portal_users = []
    for member in members:
        try:
            partner_id = member['id']
            email = member['email']

            # Check if user already exists
            existing_user = models.execute_kw(db, uid, password,
                'res.users', 'search',
                [[['partner_id', '=', partner_id]]], {'limit': 1})

            if existing_user:
                user_id = existing_user[0]
                print(f"✓ Portal user already exists for {member['name']} (User ID: {user_id})")
            else:
                # Get portal group using XML ID (most reliable)
                portal_group = None
                try:
                    portal_group_ref = models.execute_kw(db, uid, password,
                        'ir.model.data', 'search_read',
                        [[['module', '=', 'base'], ['name', '=', 'group_portal']]],
                        {'fields': ['res_id'], 'limit': 1})
                    if portal_group_ref:
                        portal_group = [portal_group_ref[0]['res_id']]
                        print(f"  Found portal group via XML ID: {portal_group[0]}")
                except Exception as e:
                    print(f"  Could not find via XML ID: {e}")

                if not portal_group:
                    # Try by name
                    try:
                        portal_group = models.execute_kw(db, uid, password,
                            'res.groups', 'search',
                            [[['name', 'ilike', 'portal']]], {'limit': 1})
                        if portal_group:
                            print(f"  Found portal group by name: {portal_group[0]}")
                    except Exception as e:
                        print(f"  Could not find by name: {e}")

                if not portal_group:
                    print(f"✗ Portal group not found!")
                    print(f"  Available groups:")
                    all_groups = models.execute_kw(db, uid, password,
                        'res.groups', 'search_read',
                        [[]], {'fields': ['name'], 'limit': 10})
                    for g in all_groups:
                        print(f"    - {g['name']}")
                    continue

                # Create portal user
                user_vals = {
                    'name': member['name'],
                    'login': email,
                    'partner_id': partner_id,
                    'groups_id': [(6, 0, portal_group)],
                    'password': 'portal123',  # Default password for testing
                }

                user_id = models.execute_kw(db, uid, password,
                    'res.users', 'create', [user_vals])

                print(f"✓ Created portal user for {member['name']} (User ID: {user_id})")
                print(f"  Login: {email}, Password: portal123")

            portal_users.append({
                'partner_id': partner_id,
                'user_id': user_id,
                'name': member['name'],
                'email': email
            })

        except Exception as e:
            print(f"✗ Error granting portal access to {member['name']}: {e}")

    return portal_users

def create_subscriptions_for_members(uid, models, portal_users):
    """Create subscription records for portal members"""
    print("\n=== Creating Subscriptions ===\n")

    # Get or create product categories
    try:
        membership_category = models.execute_kw(db, uid, password,
            'product.category', 'search',
            [[['name', '=', 'Gym Memberships']]], {'limit': 1})

        if not membership_category:
            membership_category_id = models.execute_kw(db, uid, password,
                'product.category', 'create', [{
                    'name': 'Gym Memberships'
                }])
        else:
            membership_category_id = membership_category[0]

        print(f"✓ Membership category ID: {membership_category_id}")
    except Exception as e:
        print(f"Warning: Could not create product category: {e}")
        membership_category_id = None

    # Create membership products
    membership_products = [
        {'name': 'Monthly Premium Membership', 'price': 99.00, 'type': 'service'},
        {'name': 'Monthly Basic Membership', 'price': 49.00, 'type': 'service'},
        {'name': 'Annual VIP Membership', 'price': 999.00, 'type': 'service'},
    ]

    created_products = []
    for product in membership_products:
        try:
            existing = models.execute_kw(db, uid, password,
                'product.product', 'search',
                [[['name', '=', product['name']]]], {'limit': 1})

            if existing:
                product_id = existing[0]
                print(f"✓ Product exists: {product['name']} (ID: {product_id})")
            else:
                product_vals = {
                    'name': product['name'],
                    'list_price': product['price'],
                    'type': product['type'],
                    'categ_id': membership_category_id if membership_category_id else False,
                }
                product_id = models.execute_kw(db, uid, password,
                    'product.product', 'create', [product_vals])
                print(f"✓ Created product: {product['name']} (ID: {product_id})")

            created_products.append({
                'id': product_id,
                'name': product['name'],
                'price': product['price']
            })
        except Exception as e:
            print(f"✗ Error creating product {product['name']}: {e}")

    return created_products

def create_invoices_for_members(uid, models, portal_users, products):
    """Create invoices for portal members"""
    print("\n=== Creating Invoices ===\n")

    created_invoices = []

    for i, user in enumerate(portal_users):
        try:
            partner_id = user['partner_id']

            # Check if invoice already exists
            existing = models.execute_kw(db, uid, password,
                'account.move', 'search',
                [[['partner_id', '=', partner_id], ['move_type', '=', 'out_invoice']]],
                {'limit': 1})

            if existing:
                invoice_id = existing[0]
                print(f"✓ Invoice exists for {user['name']} (ID: {invoice_id})")
            else:
                # Select product for this user
                product = products[i % len(products)]

                # Create invoice
                invoice_vals = {
                    'partner_id': partner_id,
                    'move_type': 'out_invoice',
                    'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product['id'],
                        'name': product['name'],
                        'quantity': 1,
                        'price_unit': product['price'],
                    })]
                }

                invoice_id = models.execute_kw(db, uid, password,
                    'account.move', 'create', [invoice_vals])

                print(f"✓ Created invoice for {user['name']} (ID: {invoice_id}) - {product['name']}")

                # Try to post the invoice
                try:
                    models.execute_kw(db, uid, password,
                        'account.move', 'action_post', [[invoice_id]])
                    print(f"  Posted invoice {invoice_id}")
                except Exception as e:
                    print(f"  Warning: Could not post invoice {invoice_id}: {e}")

            created_invoices.append({
                'id': invoice_id,
                'partner_id': partner_id,
                'partner_name': user['name']
            })

        except Exception as e:
            print(f"✗ Error creating invoice for {user['name']}: {e}")

    return created_invoices

def create_sale_orders_for_members(uid, models, portal_users, products):
    """Create sale orders (for retail products) for portal members"""
    print("\n=== Creating Sale Orders ===\n")

    # Create retail products
    retail_products = [
        {'name': 'Protein Shake', 'price': 5.99, 'type': 'consu'},
        {'name': 'Gym Towel', 'price': 15.00, 'type': 'consu'},
        {'name': 'Water Bottle', 'price': 12.00, 'type': 'consu'},
    ]

    created_retail = []
    for product in retail_products:
        try:
            existing = models.execute_kw(db, uid, password,
                'product.product', 'search',
                [[['name', '=', product['name']]]], {'limit': 1})

            if existing:
                product_id = existing[0]
            else:
                product_id = models.execute_kw(db, uid, password,
                    'product.product', 'create', [{
                        'name': product['name'],
                        'list_price': product['price'],
                        'type': product['type'],
                    }])

            created_retail.append({
                'id': product_id,
                'name': product['name'],
                'price': product['price']
            })
        except Exception as e:
            print(f"Error creating retail product: {e}")

    # Create sale orders
    created_orders = []
    for user in portal_users[:2]:  # Create orders for first 2 users
        try:
            partner_id = user['partner_id']

            # Check existing
            existing = models.execute_kw(db, uid, password,
                'sale.order', 'search',
                [[['partner_id', '=', partner_id]]], {'limit': 1})

            if existing:
                order_id = existing[0]
                print(f"✓ Sale order exists for {user['name']} (ID: {order_id})")
            else:
                # Create sale order
                order_vals = {
                    'partner_id': partner_id,
                    'order_line': [(0, 0, {
                        'product_id': created_retail[0]['id'],
                        'name': created_retail[0]['name'],
                        'product_uom_qty': 2,
                        'price_unit': created_retail[0]['price'],
                    }), (0, 0, {
                        'product_id': created_retail[1]['id'],
                        'name': created_retail[1]['name'],
                        'product_uom_qty': 1,
                        'price_unit': created_retail[1]['price'],
                    })]
                }

                order_id = models.execute_kw(db, uid, password,
                    'sale.order', 'create', [order_vals])

                print(f"✓ Created sale order for {user['name']} (ID: {order_id})")

                # Confirm the order
                try:
                    models.execute_kw(db, uid, password,
                        'sale.order', 'action_confirm', [[order_id]])
                    print(f"  Confirmed order {order_id}")
                except Exception as e:
                    print(f"  Warning: Could not confirm order: {e}")

            created_orders.append({
                'id': order_id,
                'partner_id': partner_id,
                'partner_name': user['name']
            })

        except Exception as e:
            print(f"✗ Error creating sale order for {user['name']}: {e}")

    return created_orders

def create_payments_for_invoices(uid, models, invoices):
    """Create payment records for invoices"""
    print("\n=== Creating Payments ===\n")

    for invoice in invoices[:2]:  # Create payments for first 2 invoices
        try:
            invoice_id = invoice['id']

            # Get invoice details
            invoice_data = models.execute_kw(db, uid, password,
                'account.move', 'read',
                [[invoice_id]], {'fields': ['amount_total', 'partner_id', 'state']})

            if not invoice_data:
                continue

            invoice_info = invoice_data[0]

            # Skip if not posted
            if invoice_info['state'] != 'posted':
                print(f"  Skipping invoice {invoice_id} - not posted")
                continue

            # Check if payment already registered
            payment_state = models.execute_kw(db, uid, password,
                'account.move', 'read',
                [[invoice_id]], {'fields': ['payment_state']})

            if payment_state and payment_state[0].get('payment_state') in ['paid', 'in_payment']:
                print(f"✓ Payment already exists for invoice {invoice_id}")
                continue

            # Get journal for payment
            journal_ids = models.execute_kw(db, uid, password,
                'account.journal', 'search',
                [[['type', '=', 'bank']]], {'limit': 1})

            if not journal_ids:
                print(f"  No bank journal found for payment")
                continue

            # Register payment
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice_info['partner_id'][0],
                'amount': invoice_info['amount_total'],
                'journal_id': journal_ids[0],
                'date': datetime.now().strftime('%Y-%m-%d'),
            }

            payment_id = models.execute_kw(db, uid, password,
                'account.payment', 'create', [payment_vals])

            # Post the payment
            models.execute_kw(db, uid, password,
                'account.payment', 'action_post', [[payment_id]])

            print(f"✓ Created and posted payment for invoice {invoice_id} (Payment ID: {payment_id})")

        except Exception as e:
            print(f"✗ Error creating payment for invoice {invoice_id}: {e}")

def check_portal_configuration(uid, models):
    """Check portal module and configuration"""
    print("\n=== Checking Portal Configuration ===\n")

    try:
        # Check if portal module is installed
        portal_module = models.execute_kw(db, uid, password,
            'ir.module.module', 'search_read',
            [[['name', '=', 'portal']]],
            {'fields': ['name', 'state']})

        if portal_module:
            print(f"✓ Portal module: {portal_module[0]['state']}")
        else:
            print("✗ Portal module not found!")

        # Check portal groups
        portal_groups = models.execute_kw(db, uid, password,
            'res.groups', 'search_read',
            [[['name', 'ilike', 'portal']]],
            {'fields': ['name']})

        print(f"\nPortal Groups Found: {len(portal_groups)}")
        for group in portal_groups:
            print(f"  - {group['name']}")

        # Check portal menu items
        portal_menus = models.execute_kw(db, uid, password,
            'ir.ui.menu', 'search_read',
            [[['name', 'ilike', 'portal']]],
            {'fields': ['name', 'parent_id']})

        print(f"\nPortal Menus Found: {len(portal_menus)}")
        for menu in portal_menus[:5]:  # Show first 5
            print(f"  - {menu['name']}")

    except Exception as e:
        print(f"✗ Error checking portal configuration: {e}")

def print_summary(portal_users):
    """Print summary of created test data"""
    print("\n" + "="*70)
    print("PORTAL SETUP COMPLETE - Test Credentials")
    print("="*70)
    print(f"\nPortal URL: {url}/my")
    print("\nTest Portal Users:")
    print("-" * 70)
    for user in portal_users:
        print(f"Name:     {user['name']}")
        print(f"Email:    {user['email']}")
        print(f"Password: portal123")
        print(f"URL:      {url}/web/login")
        print("-" * 70)
    print("\n")

def main():
    """Main execution"""
    try:
        print("="*70)
        print("GMS PORTAL SETUP SCRIPT")
        print("="*70)
        print(f"URL: {url}")
        print(f"Database: {db}")
        print(f"User: {username}")

        # Connect
        uid, models = connect_odoo()
        print(f"\n✓ Connected successfully (UID: {uid})")

        # Check portal configuration
        check_portal_configuration(uid, models)

        # Create members
        members = create_test_members_with_portal(uid, models)

        if not members:
            print("\n✗ No members created. Exiting.")
            sys.exit(1)

        # Grant portal access
        portal_users = grant_portal_access(uid, models, members)

        if not portal_users:
            print("\n✗ No portal users created. Exiting.")
            sys.exit(1)

        # Create products
        products = create_subscriptions_for_members(uid, models, portal_users)

        # Create invoices
        invoices = create_invoices_for_members(uid, models, portal_users, products)

        # Create sale orders
        orders = create_sale_orders_for_members(uid, models, portal_users, products)

        # Create payments
        create_payments_for_invoices(uid, models, invoices)

        # Print summary
        print_summary(portal_users)

        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Login to portal at: http://localhost:8070/my")
        print("2. Use any test user credentials listed above")
        print("3. Run portal validation tests")

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
