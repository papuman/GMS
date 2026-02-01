# -*- coding: utf-8 -*-
"""
Comprehensive tests for D-101 Income Tax Annual Report Workflow (Phase 9C)
Tests end-to-end workflow and progressive tax calculations
"""
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError
from unittest.mock import patch, Mock
from datetime import date


@tagged('post_install', '-at_install', 'tax_reports', 'd101')
class TestD101IncomeTaxWorkflow(TransactionCase):
    """Test complete D-101 income tax report workflow."""

    def setUp(self):
        super(TestD101IncomeTaxWorkflow, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Gym Costa Rica',
            'country_id': self.env.ref('base.cr').id,
            'vat': '3101234567',
            'email': 'admin@testgym.cr',
            'currency_id': self.env.ref('base.CRC').id,
        })

        self.env.user.company_id = self.company

        # Create customers
        self.customer = self.env['res.partner'].create({
            'name': 'Test Customer',
            'country_id': self.env.ref('base.cr').id,
            'vat': '109876543',
        })

        # Create supplier
        self.supplier = self.env['res.partner'].create({
            'name': 'Test Supplier',
            'country_id': self.env.ref('base.cr').id,
            'vat': '3102345678',
        })

        # Create products
        self.product_service = self.env['product.product'].create({
            'name': 'Gym Membership',
            'type': 'service',
            'list_price': 50000.0,
        })

    def _create_sales_invoices(self, year, total_amount):
        """Helper to create sales invoices for the year."""
        invoices = self.env['account.move']

        # Spread across the year
        monthly_amount = total_amount / 12

        for month in range(1, 13):
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.customer.id,
                'company_id': self.company.id,
                'invoice_date': date(year, month, 15),
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.product_service.id,
                    'quantity': 1,
                    'price_unit': monthly_amount,
                })],
            })
            invoice.action_post()
            invoices |= invoice

        return invoices

    def _create_purchase_bills(self, year, total_amount):
        """Helper to create purchase bills for the year."""
        bills = self.env['account.move']

        monthly_amount = total_amount / 12

        for month in range(1, 13):
            bill = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': self.supplier.id,
                'company_id': self.company.id,
                'invoice_date': date(year, month, 10),
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.product_service.id,
                    'quantity': 1,
                    'price_unit': monthly_amount,
                })],
            })
            bill.action_post()
            bills |= bill

        return bills

    # =====================================================
    # PERIOD CREATION TESTS
    # =====================================================

    def test_create_d101_period(self):
        """Test creating a D-101 annual period."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        self.assertEqual(period.name, 'D-101 2025')
        self.assertEqual(period.date_from, date(2025, 1, 1))
        self.assertEqual(period.date_to, date(2025, 12, 31))

    def test_d101_period_deadline_march_15(self):
        """Test D-101 deadline is March 15 of following year."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        expected_deadline = date(2026, 3, 15)
        self.assertEqual(period.deadline, expected_deadline)

    def test_d101_period_duplicate_prevention(self):
        """Test cannot create duplicate D-101 for same year."""
        self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        with self.assertRaises(ValidationError):
            self.env['l10n_cr.tax.report.period'].create({
                'report_type': 'd101',
                'year': 2025,
                'company_id': self.company.id,
            })

    # =====================================================
    # INCOME CALCULATION TESTS
    # =====================================================

    def test_d101_calculate_gross_income(self):
        """Test D-101 calculates gross income from sales."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create sales for ₡50,000,000
        self._create_sales_invoices(2025, 50000000.0)

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d101.action_calculate()

        self.assertEqual(d101.state, 'calculated')
        self.assertAlmostEqual(d101.sales_revenue, 50000000.0, places=2)
        self.assertAlmostEqual(d101.total_gross_income, 50000000.0, places=2)

    def test_d101_calculate_deductible_expenses(self):
        """Test D-101 calculates deductible expenses from bills."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create sales and purchases
        self._create_sales_invoices(2025, 50000000.0)
        self._create_purchase_bills(2025, 20000000.0)

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d101.action_calculate()

        self.assertAlmostEqual(d101.operating_expenses, 20000000.0, places=2)
        self.assertAlmostEqual(d101.total_deductible_expenses, 20000000.0, places=2)

    def test_d101_calculate_taxable_income(self):
        """Test D-101 calculates taxable income correctly."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 50000000.0,
            'other_income': 5000000.0,
            'operating_expenses': 20000000.0,
            'depreciation': 2000000.0,
        })

        # Trigger computations
        d101._compute_gross_income()
        d101._compute_deductible_expenses()
        d101._compute_taxable_income()

        # Total income = 55M
        self.assertEqual(d101.total_gross_income, 55000000.0)

        # Total expenses = 22M
        self.assertEqual(d101.total_deductible_expenses, 22000000.0)

        # Net before adjustments = 33M
        self.assertEqual(d101.net_income_before_adjustments, 33000000.0)

        # Taxable income = 33M (no adjustments)
        self.assertEqual(d101.taxable_income, 33000000.0)

    def test_d101_taxable_income_with_loss_carryforward(self):
        """Test D-101 applies tax loss carryforward."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 20000000.0,
            'operating_expenses': 8000000.0,
            'tax_loss_carryforward': 5000000.0,  # Loss from previous years
        })

        d101._compute_gross_income()
        d101._compute_deductible_expenses()
        d101._compute_taxable_income()

        # Net = 20M - 8M = 12M
        # Taxable = 12M - 5M carryforward = 7M
        self.assertEqual(d101.taxable_income, 7000000.0)

    def test_d101_taxable_income_cannot_be_negative(self):
        """Test D-101 taxable income minimum is zero."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 10000000.0,
            'operating_expenses': 15000000.0,  # Expenses > income
        })

        d101._compute_gross_income()
        d101._compute_deductible_expenses()
        d101._compute_taxable_income()

        # Should be zero, not negative
        self.assertEqual(d101.taxable_income, 0.0)

    # =====================================================
    # TAX BRACKET CALCULATION TESTS
    # =====================================================

    def test_d101_progressive_tax_small_income(self):
        """Test progressive tax for income in 10% bracket."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Taxable income: ₡6,000,000
        # 0% on first 4M, 10% on next 2M
        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 10000000.0,
            'operating_expenses': 4000000.0,
        })

        d101._compute_gross_income()
        d101._compute_deductible_expenses()
        d101._compute_taxable_income()
        d101._compute_income_tax()

        # Taxable = 6M
        self.assertEqual(d101.taxable_income, 6000000.0)

        # Tax bracket 0%: 4M
        self.assertEqual(d101.tax_bracket_0_amount, 4000000.0)

        # Tax bracket 10%: 2M
        self.assertEqual(d101.tax_bracket_10_amount, 2000000.0)

        # Total tax = 0 + (2M * 0.10) = 200,000
        self.assertEqual(d101.total_income_tax, 200000.0)

    def test_d101_progressive_tax_multiple_brackets(self):
        """Test progressive tax across multiple brackets."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Taxable income: ₡20,000,000
        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 30000000.0,
            'operating_expenses': 10000000.0,
        })

        d101._compute_gross_income()
        d101._compute_deductible_expenses()
        d101._compute_taxable_income()
        d101._compute_income_tax()

        # Taxable = 20M
        self.assertEqual(d101.taxable_income, 20000000.0)

        # Bracket 0%: 4M (0%)
        # Bracket 10%: 4M (10%) = 400K
        # Bracket 15%: 8M (15%) = 1.2M
        # Bracket 20%: 4M (20%) = 800K
        # Total = 2.4M

        expected_tax = (
            (4000000 * 0.00) +
            (4000000 * 0.10) +
            (8000000 * 0.15) +
            (4000000 * 0.20)
        )

        self.assertAlmostEqual(d101.total_income_tax, expected_tax, places=2)

    def test_d101_flat_rate_large_entity(self):
        """Test 30% flat rate for large entities."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Gross income > ₡119,626,000 triggers flat 30% rate
        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 150000000.0,  # Over threshold
            'operating_expenses': 50000000.0,
        })

        d101._compute_gross_income()
        d101._compute_deductible_expenses()
        d101._compute_taxable_income()
        d101._compute_income_tax()

        # Taxable = 100M
        self.assertEqual(d101.taxable_income, 100000000.0)

        # Should use flat 30% rate
        expected_tax = 100000000.0 * 0.30
        self.assertEqual(d101.total_income_tax, expected_tax)

    # =====================================================
    # TAX CREDITS AND FINAL SETTLEMENT
    # =====================================================

    def test_d101_final_settlement_amount_to_pay(self):
        """Test final settlement when tax is owed."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 20000000.0,
            'operating_expenses': 8000000.0,
            'advance_payments': 1000000.0,
            'withholdings': 500000.0,
        })

        d101._compute_gross_income()
        d101._compute_deductible_expenses()
        d101._compute_taxable_income()
        d101._compute_income_tax()
        d101._compute_final_amount()

        # Should have amount to pay after credits
        self.assertGreater(d101.amount_to_pay, 0)
        self.assertEqual(d101.refund_amount, 0)

        # Total tax - credits
        expected_amount = d101.total_income_tax - 1500000.0
        self.assertEqual(d101.amount_to_pay, expected_amount)

    def test_d101_final_settlement_refund(self):
        """Test final settlement when refund is due."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 10000000.0,
            'operating_expenses': 5000000.0,
            'advance_payments': 2000000.0,  # Credits > tax
        })

        d101._compute_gross_income()
        d101._compute_deductible_expenses()
        d101._compute_taxable_income()
        d101._compute_income_tax()
        d101._compute_final_amount()

        # Should have refund
        self.assertEqual(d101.amount_to_pay, 0)
        self.assertGreater(d101.refund_amount, 0)

    # =====================================================
    # XML GENERATION TESTS
    # =====================================================

    def test_d101_generate_xml(self):
        """Test D-101 XML generation."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 20000000.0,
            'operating_expenses': 8000000.0,
        })

        d101.state = 'calculated'
        d101.action_generate_xml()

        self.assertEqual(d101.state, 'ready')
        self.assertIsNotNone(d101.xml_content)
        self.assertIn('<D101', d101.xml_content)

    # =====================================================
    # COMPLETE WORKFLOW TEST
    # =====================================================

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_d101_complete_workflow(self, mock_get, mock_post):
        """Test complete D-101 workflow from creation to acceptance."""
        # Step 1: Create period
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Step 2: Create accounting data
        self._create_sales_invoices(2025, 50000000.0)
        self._create_purchase_bills(2025, 20000000.0)

        # Step 3: Create and calculate D-101
        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d101.action_calculate()
        self.assertEqual(d101.state, 'calculated')

        # Step 4: Generate XML
        d101.action_generate_xml()
        self.assertEqual(d101.state, 'ready')

        # Step 5: Sign and submit
        d101.xml_signed = d101.xml_content

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'clave': '50625010100003101234567000000010000001000000001',
            'mensaje': 'D-101 recibido',
        }
        mock_post.return_value = mock_post_response

        d101.action_submit_to_hacienda()
        self.assertEqual(d101.state, 'submitted')

        # Step 6: Check status
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'estado': 'aceptado',
        }
        mock_get.return_value = mock_get_response

        d101.action_check_status()
        self.assertEqual(d101.state, 'accepted')

    # =====================================================
    # ERROR HANDLING TESTS
    # =====================================================

    def test_d101_calculate_without_period(self):
        """Test error when calculating without period."""
        d101 = self.env['l10n_cr.d101.report'].create({
            'company_id': self.company.id,
        })

        with self.assertRaises(UserError):
            d101.action_calculate()

    def test_d101_reset_to_draft(self):
        """Test resetting D-101 to draft."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d101.state = 'calculated'
        d101.xml_content = '<D101>test</D101>'

        d101.action_reset_to_draft()

        self.assertEqual(d101.state, 'draft')
        self.assertFalse(d101.xml_content)

    def test_d101_cannot_reset_after_submission(self):
        """Test cannot reset after submission."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d101.state = 'submitted'

        with self.assertRaises(UserError):
            d101.action_reset_to_draft()
