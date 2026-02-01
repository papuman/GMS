# -*- coding: utf-8 -*-
"""
Comprehensive tests for D-150 VAT Monthly Report Workflow (Phase 9C)
Tests end-to-end workflow: create period → calculate → generate XML → sign → submit
"""
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError
from unittest.mock import patch, Mock
from datetime import date
from dateutil.relativedelta import relativedelta


@tagged('post_install', '-at_install', 'tax_reports', 'd150')
class TestD150VATWorkflow(TransactionCase):
    """Test complete D-150 VAT report workflow."""

    def setUp(self):
        super(TestD150VATWorkflow, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Gym Costa Rica',
            'country_id': self.env.ref('base.cr').id,
            'vat': '3101234567',
            'email': 'admin@testgym.cr',
            'phone': '22001100',
            'currency_id': self.env.ref('base.CRC').id,
        })

        self.env.user.company_id = self.company

        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'country_id': self.env.ref('base.cr').id,
            'vat': '109876543',
            'email': 'customer@test.cr',
        })

        # Create test product
        self.product = self.env['product.product'].create({
            'name': 'Gym Membership',
            'type': 'service',
            'list_price': 25000.0,
        })

        # Get 13% tax
        self.tax_13 = self.env['account.tax'].search([
            ('company_id', '=', self.company.id),
            ('amount', '=', 13),
            ('type_tax_use', '=', 'sale'),
        ], limit=1)

        if not self.tax_13:
            self.tax_13 = self.env['account.tax'].create({
                'name': 'IVA 13%',
                'amount': 13.0,
                'amount_type': 'percent',
                'type_tax_use': 'sale',
                'company_id': self.company.id,
            })

    def _create_test_invoices(self, period_start, period_end, count=5):
        """Helper to create test invoices for a period."""
        invoices = self.env['account.move']

        for i in range(count):
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.partner.id,
                'company_id': self.company.id,
                'invoice_date': period_start,
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': 25000.0,
                    'tax_ids': [(6, 0, [self.tax_13.id])],
                })],
            })
            invoice.action_post()
            invoices |= invoice

        return invoices

    # =====================================================
    # PERIOD CREATION TESTS
    # =====================================================

    def test_create_d150_period(self):
        """Test creating a D-150 period."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        self.assertEqual(period.name, 'D-150 November 2025')
        self.assertEqual(period.date_from, date(2025, 11, 1))
        self.assertEqual(period.date_to, date(2025, 11, 30))

    def test_d150_period_deadline_calculation(self):
        """Test D-150 deadline is 15th of following month."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        expected_deadline = date(2025, 12, 15)
        self.assertEqual(period.deadline, expected_deadline)

    def test_d150_period_duplicate_prevention(self):
        """Test cannot create duplicate D-150 period."""
        self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        # Try to create duplicate
        with self.assertRaises(ValidationError) as cm:
            self.env['l10n_cr.tax.report.period'].create({
                'report_type': 'd150',
                'year': 2025,
                'month': 11,
                'company_id': self.company.id,
            })

        self.assertIn('already exists', str(cm.exception))

    # =====================================================
    # REPORT CALCULATION TESTS
    # =====================================================

    def test_d150_create_report_from_period(self):
        """Test creating D-150 report from period."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        result = period.action_create_report()

        self.assertEqual(result['res_model'], 'l10n_cr.d150.report')
        self.assertIsNotNone(period.d150_report_id)

    def test_d150_calculate_from_invoices(self):
        """Test D-150 calculates correctly from posted invoices."""
        # Create period for November 2025
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        # Create test invoices
        invoices = self._create_test_invoices(
            date(2025, 11, 1),
            date(2025, 11, 30),
            count=5
        )

        # Create and calculate D-150
        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d150.action_calculate()

        # Verify calculations
        self.assertEqual(d150.state, 'calculated')
        self.assertGreater(d150.sales_13_base, 0)
        self.assertGreater(d150.sales_13_tax, 0)

        # 5 invoices * 25000 = 125000
        expected_base = 125000.0
        self.assertAlmostEqual(d150.sales_13_base, expected_base, places=2)

        # 125000 * 0.13 = 16250
        expected_tax = 16250.0
        self.assertAlmostEqual(d150.sales_13_tax, expected_tax, places=2)

    def test_d150_calculate_with_credit_notes(self):
        """Test D-150 handles credit notes correctly."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        # Create invoice
        invoice = self._create_test_invoices(
            date(2025, 11, 1),
            date(2025, 11, 30),
            count=1
        )[0]

        # Create credit note
        credit_note = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'invoice_date': date(2025, 11, 15),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 25000.0,
                'tax_ids': [(6, 0, [self.tax_13.id])],
            })],
        })
        credit_note.action_post()

        # Calculate D-150
        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d150.action_calculate()

        # Credit note should reduce tax
        self.assertGreater(d150.credit_notes_13_base, 0)
        self.assertGreater(d150.credit_notes_13_tax, 0)

    def test_d150_calculate_with_exempt_sales(self):
        """Test D-150 handles exempt sales."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        # Create tax-exempt invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'invoice_date': date(2025, 11, 1),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 25000.0,
                'tax_ids': [],  # No tax
            })],
        })
        invoice.action_post()

        # Calculate D-150
        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d150.action_calculate()

        # Should have exempt sales
        self.assertGreater(d150.sales_exempt, 0)

    def test_d150_calculate_empty_period(self):
        """Test D-150 calculation with no transactions."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d150.action_calculate()

        # Should complete but with zero amounts
        self.assertEqual(d150.state, 'calculated')
        self.assertEqual(d150.sales_13_base, 0)
        self.assertEqual(d150.sales_total_tax, 0)

    # =====================================================
    # VAT SETTLEMENT TESTS
    # =====================================================

    def test_d150_vat_settlement_to_pay(self):
        """Test D-150 settlement when VAT is owed."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 1000000.00,
            'sales_13_tax': 130000.00,
            'purchases_goods_13_base': 300000.00,
            'purchases_goods_13_tax': 39000.00,
        })

        # Trigger computations
        d150._compute_sales_totals()
        d150._compute_purchases_totals()
        d150._compute_settlement()

        # Should have amount to pay
        self.assertGreater(d150.amount_to_pay, 0)
        self.assertEqual(d150.credit_to_next_period, 0)

        # Expected: 130000 - 39000 = 91000
        self.assertAlmostEqual(d150.amount_to_pay, 91000.0, places=2)

    def test_d150_vat_settlement_credit(self):
        """Test D-150 settlement when VAT credit exists."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 500000.00,
            'sales_13_tax': 65000.00,
            'purchases_goods_13_base': 1000000.00,
            'purchases_goods_13_tax': 130000.00,
        })

        # Trigger computations
        d150._compute_sales_totals()
        d150._compute_purchases_totals()
        d150._compute_settlement()

        # Should have credit to next period
        self.assertEqual(d150.amount_to_pay, 0)
        self.assertGreater(d150.credit_to_next_period, 0)

        # Expected: 130000 - 65000 = 65000
        self.assertAlmostEqual(d150.credit_to_next_period, 65000.0, places=2)

    def test_d150_proportionality_factor(self):
        """Test D-150 proportionality factor calculation."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 800000.00,
            'sales_exempt': 200000.00,
        })

        # Trigger computation
        d150._compute_proportionality_factor()

        # Factor = 800000 / (800000 + 200000) = 0.80
        self.assertAlmostEqual(d150.proportionality_factor, 0.80, places=2)

    # =====================================================
    # XML GENERATION TESTS
    # =====================================================

    def test_d150_generate_xml_success(self):
        """Test successful D-150 XML generation."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 1000000.00,
            'sales_13_tax': 130000.00,
        })

        d150.state = 'calculated'
        d150.action_generate_xml()

        self.assertEqual(d150.state, 'ready')
        self.assertIsNotNone(d150.xml_content)
        self.assertIn('<?xml', d150.xml_content)
        self.assertIn('<D150', d150.xml_content)

    def test_d150_generate_xml_before_calculation(self):
        """Test error when generating XML before calculation."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        with self.assertRaises(UserError) as cm:
            d150.action_generate_xml()

        self.assertIn('calculated', str(cm.exception).lower())

    # =====================================================
    # COMPLETE WORKFLOW TEST
    # =====================================================

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_d150_complete_workflow_success(self, mock_post):
        """Test complete D-150 workflow from creation to acceptance."""
        # Step 1: Create period
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        self.assertEqual(period.state, 'draft')

        # Step 2: Create test data
        invoices = self._create_test_invoices(
            date(2025, 11, 1),
            date(2025, 11, 30),
            count=5
        )

        # Step 3: Create D-150 report
        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        self.assertEqual(d150.state, 'draft')

        # Step 4: Calculate
        d150.action_calculate()

        self.assertEqual(d150.state, 'calculated')
        self.assertGreater(d150.sales_13_base, 0)

        # Step 5: Generate XML
        d150.action_generate_xml()

        self.assertEqual(d150.state, 'ready')
        self.assertIsNotNone(d150.xml_content)

        # Step 6: Sign XML (mock)
        d150.xml_signed = d150.xml_content

        # Step 7: Submit to Hacienda
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'clave': '50625112300003101234567000000010000001000000001',
            'mensaje': 'Recibido exitosamente',
        }
        mock_post.return_value = mock_response

        d150.action_submit_to_hacienda()

        self.assertEqual(d150.state, 'submitted')
        self.assertIsNotNone(d150.submission_key)

        # Step 8: Check status and accept
        with patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.get') as mock_get:
            mock_get_response = Mock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                'estado': 'aceptado',
                'mensaje': 'Declaración aceptada',
            }
            mock_get.return_value = mock_get_response

            d150.action_check_status()

        self.assertEqual(d150.state, 'accepted')
        self.assertEqual(period.state, 'accepted')

    # =====================================================
    # ERROR RECOVERY TESTS
    # =====================================================

    def test_d150_reset_to_draft(self):
        """Test resetting D-150 to draft for corrections."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 1000000.00,
            'sales_13_tax': 130000.00,
        })

        d150.state = 'calculated'
        d150.xml_content = '<D150>test</D150>'

        # Reset to draft
        d150.action_reset_to_draft()

        self.assertEqual(d150.state, 'draft')
        self.assertFalse(d150.xml_content)

    def test_d150_cannot_reset_submitted(self):
        """Test cannot reset submitted D-150."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        d150.state = 'submitted'
        d150.submission_key = 'test_key'

        with self.assertRaises(UserError):
            d150.action_reset_to_draft()

    # =====================================================
    # OVERDUE PERIOD TESTS
    # =====================================================

    def test_d150_period_is_overdue(self):
        """Test overdue period detection."""
        # Create old period
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2024,
            'month': 1,
            'company_id': self.company.id,
        })

        # Should be overdue
        self.assertTrue(period.is_overdue())

    def test_d150_period_not_overdue_when_submitted(self):
        """Test submitted period not marked overdue."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2024,
            'month': 1,
            'company_id': self.company.id,
            'state': 'submitted',
        })

        # Should not be overdue
        self.assertFalse(period.is_overdue())
