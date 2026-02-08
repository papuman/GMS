# -*- coding: utf-8 -*-
"""
Test corporate billing functionality (MVP Task 2).

Tests that invoices bill to parent company when employee has parent_id set,
while maintaining customer relationship for membership tracking.
"""
import unittest
import logging
from lxml import etree

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestCorporateBilling(TransactionCase):
    """Test corporate billing logic for e-invoicing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create company for testing
        cls.company = cls.env['res.company'].search([('name', '=', 'GMS')], limit=1)
        if not cls.company:
            cls.company = cls.env.ref('base.main_company')

        # Create parent company (corporate customer)
        cls.parent_company = cls.env['res.partner'].create({
            'name': 'Acme Corporation',
            'is_company': True,
            'vat': '304567890',  # Corporate ID (9-digit cedula fisica)
            'email': 'billing@acme.com',
            'phone': '22001100',
            'country_id': cls.env.ref('base.cr').id,
        })

        # Create employee (individual customer, child of parent)
        cls.employee = cls.env['res.partner'].create({
            'name': 'John Doe',
            'is_company': False,
            'parent_id': cls.parent_company.id,
            'vat': '109876543',  # Individual ID
            'email': 'john.doe@acme.com',
            'country_id': cls.env.ref('base.cr').id,
        })

        # Create standalone customer (no parent)
        cls.standalone_customer = cls.env['res.partner'].create({
            'name': 'Jane Smith',
            'is_company': False,
            'vat': '108765432',
            'email': 'jane@example.com',
            'country_id': cls.env.ref('base.cr').id,
        })

        # Create product
        cls.product = cls.env['product.product'].create({
            'name': 'Gym Membership',
            'list_price': 50000.0,
            'type': 'service',
        })

        # Use existing payment method from data file
        cls.payment_method = cls.env.ref('l10n_cr_einvoice.payment_method_efectivo')

    def test_get_invoice_partner_with_corporate_parent(self):
        """Test _get_invoice_partner returns parent company when set."""
        invoice_partner = self.employee._get_invoice_partner()

        self.assertEqual(
            invoice_partner.id,
            self.parent_company.id,
            "Should return parent company as invoice partner"
        )
        _logger.info(
            f"Employee {self.employee.name} correctly bills to parent {invoice_partner.name}"
        )

    def test_get_invoice_partner_without_parent(self):
        """Test _get_invoice_partner returns self when no parent."""
        invoice_partner = self.standalone_customer._get_invoice_partner()

        self.assertEqual(
            invoice_partner.id,
            self.standalone_customer.id,
            "Should return self as invoice partner when no parent"
        )

    def test_get_invoice_partner_with_non_company_parent(self):
        """Test _get_invoice_partner returns self when parent is not a company."""
        # Create individual parent (not a company)
        individual_parent = self.env['res.partner'].create({
            'name': 'Parent Individual',
            'is_company': False,
            'vat': '107654321',
            'email': 'parent@example.com',
        })

        customer = self.env['res.partner'].create({
            'name': 'Child Customer',
            'parent_id': individual_parent.id,
            'vat': '106543210',
            'email': 'child@example.com',
        })

        invoice_partner = customer._get_invoice_partner()

        self.assertEqual(
            invoice_partner.id,
            customer.id,
            "Should return self when parent is not a company"
        )

    def test_account_move_uses_billing_partner(self):
        """Test account.move invoice uses parent company for billing."""
        # Create invoice for employee
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.employee.id,
            'invoice_date': '2025-02-04',
            'company_id': self.company.id,
            'l10n_cr_payment_method_id': self.payment_method.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 50000.0,
            })],
        })

        # Post invoice
        invoice.action_post()

        # Create e-invoice document
        invoice._create_einvoice_document()

        # Verify einvoice_document uses parent company
        self.assertTrue(invoice.l10n_cr_einvoice_id, "E-invoice document should be created")
        self.assertEqual(
            invoice.l10n_cr_einvoice_id.partner_id.id,
            self.parent_company.id,
            "E-invoice document should use parent company as partner"
        )

        _logger.info(
            f"Invoice {invoice.name} correctly bills to {invoice.l10n_cr_einvoice_id.partner_id.name}"
        )

    def test_xml_receptor_uses_parent_company(self):
        """Test XML generation uses parent company for Receptor."""
        # Create invoice for employee
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.employee.id,
            'invoice_date': '2025-02-04',
            'company_id': self.company.id,
            'l10n_cr_payment_method_id': self.payment_method.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 50000.0,
            })],
        })

        invoice.action_post()
        invoice._create_einvoice_document()

        einvoice = invoice.l10n_cr_einvoice_id

        # Set required clave and consecutive for XML generation
        import random
        company_cedula = (self.company.vat or '').replace('-', '').ljust(12, '0')[:12]
        date_part = '040225'  # DDMMYY for invoice_date
        consecutive = '00100001040000000001'
        security = '%08d' % random.randint(0, 99999999)
        clave = '506' + date_part + company_cedula + consecutive + '1' + security
        einvoice.write({
            'clave': clave,
            'name': consecutive,
        })

        # Generate XML
        xml_generator = self.env['l10n_cr.xml.generator']
        xml_content = xml_generator.generate_invoice_xml(einvoice)

        # Parse XML
        root = etree.fromstring(xml_content.encode('utf-8'))

        # Find Receptor section
        ns = {'fe': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica'}
        receptor = root.find('.//fe:Receptor', ns)

        self.assertIsNotNone(receptor, "Receptor section should exist in XML")

        # Check Receptor name
        receptor_name = receptor.find('fe:Nombre', ns)
        self.assertEqual(
            receptor_name.text,
            self.parent_company.name,
            "XML Receptor name should be parent company"
        )

        # Check Receptor VAT
        receptor_numero = receptor.find('.//fe:Numero', ns)
        self.assertEqual(
            receptor_numero.text,
            self.parent_company.vat.replace('-', '').replace(' ', ''),
            "XML Receptor ID should be parent company VAT"
        )

        _logger.info(
            f"XML Receptor correctly set to {receptor_name.text} with ID {receptor_numero.text}"
        )

    def test_standalone_customer_invoice_unchanged(self):
        """Test standalone customer (no parent) is billed normally."""
        # Create invoice for standalone customer
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.standalone_customer.id,
            'invoice_date': '2025-02-04',
            'company_id': self.company.id,
            'l10n_cr_payment_method_id': self.payment_method.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 50000.0,
            })],
        })

        invoice.action_post()
        invoice._create_einvoice_document()

        # Verify einvoice_document uses standalone customer
        self.assertEqual(
            invoice.l10n_cr_einvoice_id.partner_id.id,
            self.standalone_customer.id,
            "E-invoice should use standalone customer (no parent)"
        )

    @unittest.skip('Requires full POS infrastructure (journals, payment methods)')
    def test_pos_order_preserves_membership_tracking(self):
        """Test POS order maintains link to actual customer for membership."""
        # Create POS config
        pos_config = self.env['pos.config'].create({
            'name': 'Test POS',
            'l10n_cr_enable_einvoice': True,
        })

        # Create POS order for employee
        pos_order = self.env['pos.order'].create({
            'partner_id': self.employee.id,
            'config_id': pos_config.id,
            'company_id': self.company.id,
            'session_id': False,  # Simplified for test
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 50000.0,
            })],
        })

        # Verify POS order still linked to employee (for membership tracking)
        self.assertEqual(
            pos_order.partner_id.id,
            self.employee.id,
            "POS order should maintain link to actual customer (employee)"
        )

        # When einvoice is created, it should use parent for billing
        # Note: Full POS flow requires session, payment, etc.
        # This test just verifies the relationship is maintained
        _logger.info(
            f"POS order correctly linked to {pos_order.partner_id.name} "
            f"(will bill to {pos_order.partner_id._get_invoice_partner().name})"
        )
