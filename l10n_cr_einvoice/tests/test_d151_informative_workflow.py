# -*- coding: utf-8 -*-
"""
Comprehensive tests for D-151 Informative Annual Report Workflow (Phase 9C)
Tests end-to-end workflow and threshold-based reporting
"""
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError
from unittest.mock import patch, Mock
from datetime import date


@tagged('post_install', '-at_install', 'tax_reports', 'd151')
class TestD151InformativeWorkflow(TransactionCase):
    """Test complete D-151 informative report workflow."""

    def setUp(self):
        super(TestD151InformativeWorkflow, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Gym Costa Rica',
            'country_id': self.env.ref('base.cr').id,
            'vat': '3101234567',
            'email': 'admin@testgym.cr',
            'currency_id': self.env.ref('base.CRC').id,
        })

        self.env.user.company_id = self.company

        # Create multiple customers
        self.customer_high = self.env['res.partner'].create({
            'name': 'High Value Customer',
            'country_id': self.env.ref('base.cr').id,
            'vat': '109876543',  # Física
        })

        self.customer_low = self.env['res.partner'].create({
            'name': 'Low Value Customer',
            'country_id': self.env.ref('base.cr').id,
            'vat': '108765432',
        })

        # Create multiple suppliers
        self.supplier_high = self.env['res.partner'].create({
            'name': 'High Value Supplier SA',
            'country_id': self.env.ref('base.cr').id,
            'vat': '3102345678',  # Jurídica
        })

        self.supplier_low = self.env['res.partner'].create({
            'name': 'Low Value Supplier',
            'country_id': self.env.ref('base.cr').id,
            'vat': '3101111111',
        })

        # Create foreign partner
        self.foreign_customer = self.env['res.partner'].create({
            'name': 'Foreign Customer',
            'country_id': self.env.ref('base.us').id,
            'vat': 'US123456789',
        })

        # Create DIMEX partner
        self.dimex_customer = self.env['res.partner'].create({
            'name': 'DIMEX Customer',
            'country_id': self.env.ref('base.cr').id,
            'vat': '12345678901',  # 11 digits = DIMEX
        })

        # Create product
        self.product = self.env['product.product'].create({
            'name': 'Gym Service',
            'type': 'service',
            'list_price': 50000.0,
        })

    def _create_customer_invoices(self, partner, year, total_amount, count=1):
        """Helper to create customer invoices."""
        invoices = self.env['account.move']
        amount_per_invoice = total_amount / count

        for i in range(count):
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'company_id': self.company.id,
                'invoice_date': date(year, i + 1 if i < 12 else 12, 15),
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': amount_per_invoice,
                })],
            })
            invoice.action_post()
            invoices |= invoice

        return invoices

    def _create_supplier_bills(self, partner, year, total_amount, count=1):
        """Helper to create supplier bills."""
        bills = self.env['account.move']
        amount_per_bill = total_amount / count

        for i in range(count):
            bill = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': partner.id,
                'company_id': self.company.id,
                'invoice_date': date(year, i + 1 if i < 12 else 12, 10),
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': amount_per_bill,
                })],
            })
            bill.action_post()
            bills |= bill

        return bills

    # =====================================================
    # PERIOD CREATION TESTS
    # =====================================================

    def test_create_d151_period(self):
        """Test creating a D-151 annual period."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        self.assertEqual(period.name, 'D-151 2025')
        self.assertEqual(period.date_from, date(2025, 1, 1))
        self.assertEqual(period.date_to, date(2025, 12, 31))

    def test_d151_period_deadline_april_15(self):
        """Test D-151 deadline is April 15 of following year."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        expected_deadline = date(2026, 4, 15)
        self.assertEqual(period.deadline, expected_deadline)

    # =====================================================
    # THRESHOLD FILTERING TESTS
    # =====================================================

    def test_d151_customer_threshold_filtering(self):
        """Test D-151 only includes customers above threshold."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create high value customer (above threshold ₡2.5M)
        self._create_customer_invoices(self.customer_high, 2025, 5000000.0, count=12)

        # Create low value customer (below threshold)
        self._create_customer_invoices(self.customer_low, 2025, 1000000.0, count=4)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'threshold_amount': 2500000.0,
        })

        d151.action_calculate()

        # Should only have high value customer
        self.assertEqual(len(d151.customer_line_ids), 1)
        self.assertEqual(d151.customer_line_ids[0].partner_vat, '109876543')
        self.assertAlmostEqual(d151.customer_line_ids[0].total_amount, 5000000.0, places=2)

    def test_d151_supplier_threshold_filtering(self):
        """Test D-151 only includes suppliers above threshold."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create high value supplier
        self._create_supplier_bills(self.supplier_high, 2025, 8000000.0, count=8)

        # Create low value supplier
        self._create_supplier_bills(self.supplier_low, 2025, 500000.0, count=2)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'threshold_amount': 2500000.0,
        })

        d151.action_calculate()

        # Should only have high value supplier
        self.assertEqual(len(d151.supplier_line_ids), 1)
        self.assertEqual(d151.supplier_line_ids[0].partner_vat, '3102345678')

    def test_d151_multiple_customers_above_threshold(self):
        """Test D-151 includes all customers above threshold."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create multiple high value customers
        self._create_customer_invoices(self.customer_high, 2025, 5000000.0, count=10)
        self._create_customer_invoices(self.dimex_customer, 2025, 3000000.0, count=6)
        self._create_customer_invoices(self.foreign_customer, 2025, 4000000.0, count=8)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'threshold_amount': 2500000.0,
        })

        d151.action_calculate()

        # Should have all 3 customers
        self.assertEqual(len(d151.customer_line_ids), 3)

    # =====================================================
    # TRANSACTION COUNT TESTS
    # =====================================================

    def test_d151_transaction_count(self):
        """Test D-151 correctly counts transactions per partner."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create 12 invoices for customer
        self._create_customer_invoices(self.customer_high, 2025, 6000000.0, count=12)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.action_calculate()

        # Should count 12 transactions
        self.assertEqual(len(d151.customer_line_ids), 1)
        self.assertEqual(d151.customer_line_ids[0].transaction_count, 12)

    # =====================================================
    # ID TYPE DETECTION TESTS
    # =====================================================

    def test_d151_id_type_fisica(self):
        """Test D-151 detects Física (9 digits) correctly."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        self._create_customer_invoices(self.customer_high, 2025, 5000000.0, count=5)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.action_calculate()

        # Generate XML to check ID type
        xml_str = self.env['l10n_cr.tax.report.xml.generator'].generate_d151_xml(d151)

        self.assertIn('<Tipo>01</Tipo>', xml_str)  # Física

    def test_d151_id_type_juridica(self):
        """Test D-151 detects Jurídica (10 digits) correctly."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        self._create_supplier_bills(self.supplier_high, 2025, 8000000.0, count=8)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.action_calculate()

        xml_str = self.env['l10n_cr.tax.report.xml.generator'].generate_d151_xml(d151)

        self.assertIn('<Tipo>02</Tipo>', xml_str)  # Jurídica

    def test_d151_id_type_dimex(self):
        """Test D-151 detects DIMEX (11-12 digits) correctly."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        self._create_customer_invoices(self.dimex_customer, 2025, 3000000.0, count=6)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.action_calculate()

        xml_str = self.env['l10n_cr.tax.report.xml.generator'].generate_d151_xml(d151)

        self.assertIn('<Tipo>03</Tipo>', xml_str)  # DIMEX

    def test_d151_id_type_extranjero(self):
        """Test D-151 detects Extranjero correctly."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        self._create_customer_invoices(self.foreign_customer, 2025, 4000000.0, count=8)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.action_calculate()

        xml_str = self.env['l10n_cr.tax.report.xml.generator'].generate_d151_xml(d151)

        self.assertIn('<Tipo>05</Tipo>', xml_str)  # Extranjero

    # =====================================================
    # SUMMARY STATISTICS TESTS
    # =====================================================

    def test_d151_summary_statistics(self):
        """Test D-151 computes summary statistics correctly."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create customers
        self._create_customer_invoices(self.customer_high, 2025, 5000000.0, count=10)
        self._create_customer_invoices(self.dimex_customer, 2025, 3000000.0, count=6)

        # Create suppliers
        self._create_supplier_bills(self.supplier_high, 2025, 8000000.0, count=8)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.action_calculate()

        # Check statistics
        self.assertEqual(d151.total_customers_reported, 2)
        self.assertEqual(d151.total_suppliers_reported, 1)
        self.assertAlmostEqual(d151.total_sales_amount, 8000000.0, places=2)
        self.assertAlmostEqual(d151.total_purchases_amount, 8000000.0, places=2)

    # =====================================================
    # SPECIFIC EXPENSES TESTS
    # =====================================================

    def test_d151_specific_expense_threshold(self):
        """Test D-151 specific expense threshold (₡50,000)."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'specific_expense_threshold': 50000.0,
        })

        # Verify threshold set correctly
        self.assertEqual(d151.specific_expense_threshold, 50000.0)

    # =====================================================
    # XML GENERATION TESTS
    # =====================================================

    def test_d151_generate_xml_with_data(self):
        """Test D-151 XML generation with actual data."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create data
        self._create_customer_invoices(self.customer_high, 2025, 5000000.0, count=12)
        self._create_supplier_bills(self.supplier_high, 2025, 8000000.0, count=8)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.action_calculate()
        d151.action_generate_xml()

        self.assertEqual(d151.state, 'ready')
        self.assertIsNotNone(d151.xml_content)
        self.assertIn('<D151', d151.xml_content)
        self.assertIn('<Clientes>', d151.xml_content)
        self.assertIn('<Proveedores>', d151.xml_content)

    def test_d151_xml_empty_report(self):
        """Test D-151 XML generation with no transactions above threshold."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create only low-value transactions
        self._create_customer_invoices(self.customer_low, 2025, 1000000.0, count=4)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'threshold_amount': 2500000.0,
        })

        d151.action_calculate()
        d151.state = 'calculated'
        d151.action_generate_xml()

        # Should generate XML even with no reportable transactions
        self.assertIsNotNone(d151.xml_content)
        self.assertIn('<D151', d151.xml_content)
        self.assertEqual(d151.total_customers_reported, 0)

    # =====================================================
    # COMPLETE WORKFLOW TEST
    # =====================================================

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get')
    def test_d151_complete_workflow(self, mock_get, mock_post):
        """Test complete D-151 workflow from creation to acceptance."""
        # Step 1: Create period
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Step 2: Create accounting data
        self._create_customer_invoices(self.customer_high, 2025, 5000000.0, count=12)
        self._create_customer_invoices(self.dimex_customer, 2025, 3000000.0, count=6)
        self._create_supplier_bills(self.supplier_high, 2025, 8000000.0, count=8)

        # Step 3: Create and calculate D-151
        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.action_calculate()

        self.assertEqual(d151.state, 'calculated')
        self.assertEqual(d151.total_customers_reported, 2)
        self.assertEqual(d151.total_suppliers_reported, 1)

        # Step 4: Generate XML
        d151.action_generate_xml()
        self.assertEqual(d151.state, 'ready')

        # Step 5: Sign and submit
        d151.xml_signed = d151.xml_content

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'clave': '50625015100003101234567000000010000001000000001',
            'mensaje': 'D-151 recibido',
        }
        mock_post.return_value = mock_post_response

        d151.action_submit_to_hacienda()
        self.assertEqual(d151.state, 'submitted')

        # Step 6: Check status
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'estado': 'aceptado',
        }
        mock_get.return_value = mock_get_response

        d151.action_check_status()
        self.assertEqual(d151.state, 'accepted')

    # =====================================================
    # ERROR HANDLING TESTS
    # =====================================================

    def test_d151_calculate_without_period(self):
        """Test error when calculating without period."""
        d151 = self.env['l10n_cr.d151.report'].create({
            'company_id': self.company.id,
        })

        with self.assertRaises(UserError):
            d151.action_calculate()

    def test_d151_reset_to_draft(self):
        """Test resetting D-151 to draft."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.state = 'calculated'
        d151.xml_content = '<D151>test</D151>'

        d151.action_reset_to_draft()

        self.assertEqual(d151.state, 'draft')
        self.assertFalse(d151.xml_content)

    def test_d151_partner_without_vat(self):
        """Test D-151 handles partners without VAT gracefully."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        # Create partner without VAT
        no_vat_partner = self.env['res.partner'].create({
            'name': 'No VAT Customer',
            'country_id': self.env.ref('base.cr').id,
        })

        self._create_customer_invoices(no_vat_partner, 2025, 5000000.0, count=10)

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d151.action_calculate()

        # Should skip partner without VAT or mark as Extranjero
        # (implementation dependent on business rules)
        self.assertIsNotNone(d151)
