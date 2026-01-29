#!/usr/bin/env python3
"""
Comprehensive POS Test Script v2 for GMS Validation System
Tests Point of Sale functionality for gym retail environment with Costa Rica tax compliance
"""

import logging
from datetime import datetime
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class POSTestResults:
    """Store test results"""
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.warnings = []

    def add_test(self, name, status, details, expected=None, actual=None):
        self.tests.append({
            'name': name,
            'status': status,
            'details': details,
            'expected': expected,
            'actual': actual,
            'timestamp': datetime.now().isoformat()
        })
        if status == 'PASS':
            self.passed += 1
        elif status == 'FAIL':
            self.failed += 1

    def add_warning(self, message):
        self.warnings.append(message)

results = POSTestResults()

def test_setup():
    """Test 1: Verify POS Configuration and Initial Setup"""
    logger.info("=" * 80)
    logger.info("TEST 1: POS Configuration and Setup")
    logger.info("=" * 80)

    try:
        # Get POS config
        pos_config = env['pos.config'].search([('name', '=', 'GMS Retail POS')], limit=1)

        if not pos_config:
            pos_config = env['pos.config'].search([], limit=1)

        if not pos_config:
            results.add_test(
                'POS Configuration Exists',
                'FAIL',
                'No POS configuration found',
                'At least one POS config',
                'None found'
            )
            return None

        results.add_test(
            'POS Configuration Exists',
            'PASS',
            f'Found POS config: {pos_config.name}',
            'POS config exists',
            pos_config.name
        )

        # Check currency
        currency = pos_config.currency_id or env.company.currency_id
        if currency.name != 'CRC':
            results.add_test(
                'Currency Configuration',
                'FAIL',
                f'Currency is {currency.name}, expected CRC',
                'CRC',
                currency.name
            )
        else:
            results.add_test(
                'Currency Configuration',
                'PASS',
                'Currency correctly set to CRC',
                'CRC',
                'CRC'
            )

        # Check payment methods
        payment_methods = pos_config.payment_method_ids
        logger.info(f"Available payment methods: {len(payment_methods)}")
        for pm in payment_methods:
            logger.info(f"  - {pm.name} ({pm.type})")

        if len(payment_methods) == 0:
            results.add_warning('No payment methods configured')

        results.add_test(
            'Payment Methods Available',
            'PASS' if len(payment_methods) > 0 else 'FAIL',
            f'Found {len(payment_methods)} payment methods',
            'At least 1 payment method',
            str(len(payment_methods))
        )

        # Check journal
        if not pos_config.journal_id:
            results.add_test(
                'Accounting Journal',
                'FAIL',
                'No journal configured',
                'Journal configured',
                'None'
            )
        else:
            results.add_test(
                'Accounting Journal',
                'PASS',
                f'Journal: {pos_config.journal_id.name}',
                'Journal configured',
                pos_config.journal_id.name
            )

        logger.info(f"POS Config ID: {pos_config.id}")
        logger.info(f"POS Config Name: {pos_config.name}")
        logger.info(f"Currency: {currency.name}")

        return pos_config

    except Exception as e:
        logger.error(f"Setup test failed: {str(e)}")
        results.add_test('POS Configuration', 'FAIL', str(e))
        return None

def test_products(pos_config):
    """Test 2: Verify Product Configuration"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Product Configuration")
    logger.info("=" * 80)

    try:
        # Get GYM products available in POS
        products = env['product.product'].search([
            ('available_in_pos', '=', True),
            ('sale_ok', '=', True),
            ('categ_id.name', 'ilike', 'gym')
        ], limit=20)

        # If no gym products, get any products
        if not products:
            products = env['product.product'].search([
                ('available_in_pos', '=', True),
                ('sale_ok', '=', True)
            ], limit=20)

        logger.info(f"Found {len(products)} products available in POS")

        if len(products) == 0:
            results.add_test(
                'Products Available',
                'FAIL',
                'No products available in POS',
                'At least 1 product',
                '0'
            )
            return []

        results.add_test(
            'Products Available',
            'PASS',
            f'Found {len(products)} products in POS',
            'Products available',
            str(len(products))
        )

        # Check product details
        sample_products = []
        tax_issues = []
        gym_products_count = 0

        for product in products[:10]:
            logger.info(f"\nProduct: {product.name}")
            logger.info(f"  - Category: {product.categ_id.name}")
            logger.info(f"  - List Price: {product.list_price} {product.currency_id.name}")
            logger.info(f"  - Taxes: {', '.join([t.name for t in product.taxes_id]) if product.taxes_id else 'None'}")

            # Count gym products
            if 'gym' in product.categ_id.name.lower() or any(keyword in product.name.lower() for keyword in ['protein', 'amino', 'creatine', 'bcaa', 'pre-workout', 'shaker', 'belt', 'gloves', 'towel']):
                gym_products_count += 1

            # Check for 13% IVA tax
            has_13_tax = False
            for tax in product.taxes_id:
                if '13' in tax.name or tax.amount == 13:
                    has_13_tax = True
                    logger.info(f"  - Tax found: {tax.name} ({tax.amount}%)")

            if not has_13_tax and product.taxes_id:
                tax_issues.append(f"{product.name}: {', '.join([f'{t.name} ({t.amount}%)' for t in product.taxes_id])}")
            elif not product.taxes_id:
                tax_issues.append(f"{product.name}: No taxes configured")

            if len(sample_products) < 5:
                sample_products.append(product)

        logger.info(f"\nGym products found: {gym_products_count}/{len(products[:10])}")

        if tax_issues:
            results.add_test(
                '13% IVA Tax Configuration',
                'FAIL',
                f'{len(tax_issues)} products without 13% IVA tax',
                'All products with 13% IVA',
                f'{len(tax_issues)} issues found'
            )
            for issue in tax_issues[:5]:
                logger.warning(f"Tax issue: {issue}")
        else:
            results.add_test(
                '13% IVA Tax Configuration',
                'PASS',
                'All sampled products have 13% IVA tax',
                '13% IVA on products',
                'Verified'
            )

        return sample_products

    except Exception as e:
        logger.error(f"Product test failed: {str(e)}")
        results.add_test('Product Configuration', 'FAIL', str(e))
        return []

def test_open_session(pos_config):
    """Test 3: Open POS Session"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Opening POS Session")
    logger.info("=" * 80)

    try:
        # Close any existing open sessions for this config
        open_sessions = env['pos.session'].search([
            ('config_id', '=', pos_config.id),
            ('state', '!=', 'closed')
        ])

        if open_sessions:
            logger.info(f"Found {len(open_sessions)} open sessions, closing them...")
            for session in open_sessions:
                try:
                    if session.state == 'opened':
                        session.action_pos_session_closing_control()
                        logger.info(f"Closed session: {session.name}")
                except Exception as e:
                    logger.warning(f"Could not close session {session.name}: {str(e)}")

        # Commit to clear any pending transactions
        env.cr.commit()

        # Create new session
        session = env['pos.session'].create({
            'config_id': pos_config.id,
            'user_id': env.user.id,
        })

        logger.info(f"Created session: {session.name} (ID: {session.id})")

        # Open the session
        session.action_pos_session_open()
        env.cr.commit()

        logger.info(f"Session state: {session.state}")
        logger.info(f"Session start: {session.start_at}")

        if session.state == 'opened':
            results.add_test(
                'Open POS Session',
                'PASS',
                f'Session {session.name} opened successfully',
                'Session opened',
                session.state
            )
        else:
            results.add_test(
                'Open POS Session',
                'FAIL',
                f'Session state is {session.state}',
                'opened',
                session.state
            )

        return session

    except Exception as e:
        logger.error(f"Session opening failed: {str(e)}")
        results.add_test('Open POS Session', 'FAIL', str(e))
        env.cr.rollback()
        return None

def test_create_order(session, products):
    """Test 4: Create POS Orders with Different Scenarios"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Creating POS Orders")
    logger.info("=" * 80)

    orders = []

    if len(products) < 3:
        logger.warning("Not enough products for comprehensive testing")
        results.add_warning("Limited product selection for testing")

    # Get payment methods
    cash_method = session.config_id.payment_method_ids.filtered(lambda pm: pm.type == 'cash')
    bank_method = session.config_id.payment_method_ids.filtered(lambda pm: pm.type == 'bank')

    if not cash_method:
        cash_method = session.config_id.payment_method_ids[:1]

    if not cash_method:
        results.add_test(
            'Payment Method Available',
            'FAIL',
            'No payment methods available',
            'At least 1 payment method',
            'None'
        )
        return []

    # Test Case 1: Simple single-product order
    try:
        logger.info("\n--- Test Case 1: Single Product Order (Cash) ---")
        product1 = products[0]

        # Calculate amounts
        qty = 1
        price_unit = product1.list_price
        price_subtotal = qty * price_unit
        price_subtotal_incl = price_subtotal

        # Calculate tax
        tax_amount = 0
        if product1.taxes_id:
            for tax in product1.taxes_id:
                tax_amount = price_subtotal * (tax.amount / 100.0)
                price_subtotal_incl += tax_amount

        order1_data = {
            'session_id': session.id,
            'partner_id': False,
            'pricelist_id': session.config_id.pricelist_id.id,
            'fiscal_position_id': False,
            'lines': [(0, 0, {
                'product_id': product1.id,
                'price_unit': price_unit,
                'qty': qty,
                'price_subtotal': price_subtotal,
                'price_subtotal_incl': price_subtotal_incl,
                'tax_ids': [(6, 0, product1.taxes_id.ids)],
                'full_product_name': product1.name,
            })],
            'amount_paid': price_subtotal_incl,
            'amount_total': price_subtotal_incl,
            'amount_tax': tax_amount,
            'amount_return': 0,
        }

        order1 = env['pos.order'].create(order1_data)
        env.cr.commit()

        # Add payment
        env['pos.payment'].create({
            'pos_order_id': order1.id,
            'payment_method_id': cash_method.id,
            'amount': order1.amount_total,
        })
        env.cr.commit()

        # Validate order
        order1.action_pos_order_paid()
        env.cr.commit()

        logger.info(f"Order: {order1.name}")
        logger.info(f"  Product: {product1.name}")
        logger.info(f"  Price: {price_unit}")
        logger.info(f"  Amount before tax: {order1.amount_total - order1.amount_tax}")
        logger.info(f"  Tax amount: {order1.amount_tax}")
        logger.info(f"  Total: {order1.amount_total}")
        logger.info(f"  State: {order1.state}")

        # Verify tax calculation (13%)
        if product1.taxes_id:
            expected_tax = float(price_unit) * 0.13
            actual_tax = float(order1.amount_tax)
            tax_difference = abs(expected_tax - actual_tax)

            if tax_difference < 0.5:  # Allow small rounding difference
                results.add_test(
                    'Tax Calculation - Simple Order',
                    'PASS',
                    f'Tax calculated correctly: {actual_tax:.2f} CRC',
                    f'{expected_tax:.2f} CRC',
                    f'{actual_tax:.2f} CRC'
                )
            else:
                results.add_test(
                    'Tax Calculation - Simple Order',
                    'FAIL',
                    f'Tax mismatch',
                    f'{expected_tax:.2f} CRC',
                    f'{actual_tax:.2f} CRC'
                )

        results.add_test(
            'Single Product Order Creation',
            'PASS',
            f'Order {order1.name} created successfully',
            'Order created and paid',
            order1.state
        )

        orders.append(order1)

    except Exception as e:
        logger.error(f"Test Case 1 failed: {str(e)}")
        results.add_test('Single Product Order', 'FAIL', str(e))
        env.cr.rollback()

    # Test Case 2: Multi-product order
    if len(products) >= 3:
        try:
            logger.info("\n--- Test Case 2: Multi-Product Order (Mixed Payment) ---")

            lines_data = []
            total_amount = 0
            total_tax = 0

            # Create lines for multiple products
            for i, product in enumerate(products[:3]):
                qty = i + 1
                price_unit = product.list_price
                price_subtotal = qty * price_unit
                price_subtotal_incl = price_subtotal

                # Calculate tax
                line_tax = 0
                if product.taxes_id:
                    for tax in product.taxes_id:
                        line_tax = price_subtotal * (tax.amount / 100.0)
                        price_subtotal_incl += line_tax

                lines_data.append((0, 0, {
                    'product_id': product.id,
                    'price_unit': price_unit,
                    'qty': qty,
                    'price_subtotal': price_subtotal,
                    'price_subtotal_incl': price_subtotal_incl,
                    'tax_ids': [(6, 0, product.taxes_id.ids)],
                    'full_product_name': product.name,
                }))

                total_amount += price_subtotal_incl
                total_tax += line_tax

            order2_data = {
                'session_id': session.id,
                'partner_id': False,
                'pricelist_id': session.config_id.pricelist_id.id,
                'fiscal_position_id': False,
                'lines': lines_data,
                'amount_paid': total_amount,
                'amount_total': total_amount,
                'amount_tax': total_tax,
                'amount_return': 0,
            }

            order2 = env['pos.order'].create(order2_data)
            env.cr.commit()

            # Split payment - half cash, half bank
            if bank_method:
                half_amount = order2.amount_total / 2
                env['pos.payment'].create({
                    'pos_order_id': order2.id,
                    'payment_method_id': cash_method.id,
                    'amount': half_amount,
                })
                env['pos.payment'].create({
                    'pos_order_id': order2.id,
                    'payment_method_id': bank_method.id,
                    'amount': half_amount,
                })
            else:
                env['pos.payment'].create({
                    'pos_order_id': order2.id,
                    'payment_method_id': cash_method.id,
                    'amount': order2.amount_total,
                })
            env.cr.commit()

            order2.action_pos_order_paid()
            env.cr.commit()

            logger.info(f"Order: {order2.name}")
            logger.info(f"  Products: {len(order2.lines)}")
            for line in order2.lines:
                logger.info(f"    - {line.product_id.name} x {line.qty} @ {line.price_unit}")
            logger.info(f"  Subtotal: {order2.amount_total - order2.amount_tax}")
            logger.info(f"  Tax: {order2.amount_tax}")
            logger.info(f"  Total: {order2.amount_total}")
            logger.info(f"  Payments: {len(order2.payment_ids)}")

            results.add_test(
                'Multi-Product Order',
                'PASS',
                f'Created order with {len(order2.lines)} products',
                'Order created',
                order2.state
            )

            orders.append(order2)

        except Exception as e:
            logger.error(f"Test Case 2 failed: {str(e)}")
            results.add_test('Multi-Product Order', 'FAIL', str(e))
            env.cr.rollback()

    return orders

def test_refund(session, orders):
    """Test 5: Process Refunds"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Processing Refunds")
    logger.info("=" * 80)

    if not orders:
        logger.warning("No orders available for refund testing")
        results.add_warning("Skipped refund test - no orders")
        return

    try:
        original_order = orders[0]

        logger.info(f"Creating refund for order: {original_order.name}")
        logger.info(f"Original amount: {original_order.amount_total}")

        # Create refund
        refund = original_order.refund()
        env.cr.commit()

        logger.info(f"Refund order: {refund.name}")
        logger.info(f"Refund amount: {refund.amount_total}")
        logger.info(f"Refund state: {refund.state}")

        # Add payment for refund
        cash_method = session.config_id.payment_method_ids.filtered(lambda pm: pm.type == 'cash')[:1]

        env['pos.payment'].create({
            'pos_order_id': refund.id,
            'payment_method_id': cash_method.id,
            'amount': refund.amount_total,
        })
        env.cr.commit()

        refund.action_pos_order_paid()
        env.cr.commit()

        # Verify refund amount matches original
        if abs(refund.amount_total - original_order.amount_total) < 0.01:
            results.add_test(
                'Refund Processing',
                'PASS',
                f'Refund created successfully: {refund.name}',
                f'Amount: {original_order.amount_total}',
                f'Amount: {refund.amount_total}'
            )
        else:
            results.add_test(
                'Refund Processing',
                'FAIL',
                'Refund amount mismatch',
                f'{original_order.amount_total}',
                f'{refund.amount_total}'
            )

    except Exception as e:
        logger.error(f"Refund test failed: {str(e)}")
        results.add_test('Refund Processing', 'FAIL', str(e))
        env.cr.rollback()

def test_close_session(session):
    """Test 6: Close POS Session and Reconciliation"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 6: Closing POS Session")
    logger.info("=" * 80)

    try:
        logger.info(f"Session: {session.name}")
        logger.info(f"Orders count: {len(session.order_ids)}")
        logger.info(f"Total sales: {session.total_payments_amount}")

        # Show payment summary
        logger.info("\nPayment Summary:")
        for statement in session.statement_ids:
            logger.info(f"  {statement.journal_id.name}:")
            logger.info(f"    - Total: {statement.total_entry_encoding}")

        # Close session
        session.action_pos_session_closing_control()
        env.cr.commit()

        logger.info(f"\nSession state after closing: {session.state}")
        logger.info(f"Stop time: {session.stop_at}")

        if session.state == 'closed':
            results.add_test(
                'Close POS Session',
                'PASS',
                f'Session closed successfully',
                'closed',
                session.state
            )
        else:
            results.add_test(
                'Close POS Session',
                'FAIL',
                f'Session state is {session.state}',
                'closed',
                session.state
            )

        # Verify accounting entries
        if session.move_id:
            logger.info(f"\nAccounting Entry: {session.move_id.name}")
            logger.info(f"  State: {session.move_id.state}")
            logger.info(f"  Lines: {len(session.move_id.line_ids)}")

            for line in session.move_id.line_ids:
                logger.info(f"    - {line.account_id.name}: Debit {line.debit}, Credit {line.credit}")

            results.add_test(
                'Accounting Integration',
                'PASS',
                f'Journal entry created: {session.move_id.name}',
                'Journal entry exists',
                'Created'
            )
        else:
            results.add_warning('No accounting entry created')

    except Exception as e:
        logger.error(f"Session closing failed: {str(e)}")
        results.add_test('Close POS Session', 'FAIL', str(e))
        env.cr.rollback()

def generate_report():
    """Generate final test report"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    logger.info(f"\nTotal Tests: {results.passed + results.failed}")
    logger.info(f"Passed: {results.passed}")
    logger.info(f"Failed: {results.failed}")
    logger.info(f"Warnings: {len(results.warnings)}")
    success_rate = (results.passed / (results.passed + results.failed) * 100) if (results.passed + results.failed) > 0 else 0
    logger.info(f"Success Rate: {success_rate:.1f}%")

    logger.info("\n" + "-" * 80)
    logger.info("DETAILED RESULTS:")
    logger.info("-" * 80)

    for test in results.tests:
        status_symbol = "PASS" if test['status'] == 'PASS' else "FAIL"
        logger.info(f"\n[{status_symbol}] {test['name']}")
        logger.info(f"   {test['details']}")
        if test['expected']:
            logger.info(f"   Expected: {test['expected']}")
        if test['actual']:
            logger.info(f"   Actual: {test['actual']}")

    if results.warnings:
        logger.info("\n" + "-" * 80)
        logger.info("WARNINGS:")
        logger.info("-" * 80)
        for warning in results.warnings:
            logger.info(f"  - {warning}")

    return results

# Main execution
def main():
    logger.info("Starting GMS POS Test Suite v2")
    logger.info(f"Database: {env.cr.dbname}")
    logger.info(f"User: {env.user.name}")
    logger.info(f"Company: {env.company.name}")
    logger.info(f"Start time: {datetime.now()}\n")

    # Run tests
    pos_config = test_setup()

    if pos_config:
        products = test_products(pos_config)

        if products:
            session = test_open_session(pos_config)

            if session:
                orders = test_create_order(session, products)
                test_refund(session, orders)
                test_close_session(session)

    # Generate final report
    test_results = generate_report()

    logger.info("\n" + "=" * 80)
    logger.info("POS Test Suite Completed")
    logger.info(f"End time: {datetime.now()}")
    logger.info("=" * 80)

    return test_results

# Execute tests
if __name__ == '__main__':
    test_results = main()
