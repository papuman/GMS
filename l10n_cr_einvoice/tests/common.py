# -*- coding: utf-8 -*-
"""
Base test case classes for l10n_cr_einvoice tests.

This module provides base test classes that set up complete Odoo accounting
infrastructure required for e-invoice testing. All test classes should inherit
from these base classes instead of directly from TransactionCase.

Classes:
    EInvoiceTestCase: Base class with full accounting setup for CR e-invoicing
"""

import uuid
from odoo.tests import TransactionCase


class EInvoiceTestCase(TransactionCase):
    """
    Base test case for Costa Rica e-invoicing tests.

    This class sets up a complete Odoo accounting infrastructure including:
    - Costa Rica chart of accounts
    - Required accounting journals (sales, purchase, cash, bank)
    - Default fiscal positions
    - Test company with proper CR configuration
    - Test customer partner
    - Test invoiceable product

    All e-invoice tests should inherit from this class to ensure proper
    accounting setup and avoid "No journal could be found" errors.

    Usage:
        class TestMyFeature(EInvoiceTestCase):
            def test_something(self):
                invoice = self._create_test_invoice()
                # ... your test code
    """

    @classmethod
    def setUpClass(cls):
        """Set up test company and accounting infrastructure."""
        super().setUpClass()

        # Get Costa Rica country reference
        cr_country = cls.env.ref('base.cr')

        # Create test company with Costa Rica configuration
        cls.company = cls.env['res.company'].create({
            'name': 'Test Company SA',
            'country_id': cr_country.id,
            'vat': '3101234567',  # Cédula Jurídica format
            'email': 'test@example.com',
            'phone': '22001100',
            'street': 'Avenida Central, San José',
            'currency_id': cls.env.ref('base.CRC').id,
            'l10n_cr_emisor_location': '10101',  # San José, Carmen
        })

        # Set activity code on company partner (required for e-invoice)
        cls.company.partner_id.l10n_cr_activity_code = '861201'

        # Load Costa Rica chart of accounts if available
        # This creates all required accounts, taxes, and fiscal positions
        try:
            cls.env['account.chart.template'].try_loading('l10n_cr', company=cls.company)
        except KeyError:
            # l10n_cr chart template not installed, use generic template
            try:
                cls.env['account.chart.template'].try_loading('generic_coa', company=cls.company)
            except (KeyError, Exception):
                # No chart template available, will create journals manually
                pass

        # Set fiscal country to Costa Rica (must be done AFTER chart template loading
        # because chart templates override this field)
        cls.company.write({'account_fiscal_country_id': cr_country.id})

        # Remove any auto-apply fiscal positions that might interfere with tests
        # (Chart templates often create fiscal positions with auto_apply=True
        # that can cause tax validation errors in tests)
        problematic_fps = cls.env['account.fiscal.position'].search([
            ('company_id', '=', cls.company.id),
            ('auto_apply', '=', True),
        ])
        if problematic_fps:
            problematic_fps.unlink()

        # Find or create sales journal (code 'SALE' is standard for sales)
        cls.sales_journal = cls.env['account.journal'].search([
            ('code', '=', 'SALE'),
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.sales_journal:
            cls.sales_journal = cls.env['account.journal'].create({
                'name': 'Sales Journal',
                'code': 'SALE',
                'type': 'sale',
                'company_id': cls.company.id,
            })

        # Find or create purchase journal (code 'BILL' is standard for vendor bills)
        cls.purchase_journal = cls.env['account.journal'].search([
            ('code', '=', 'BILL'),
            ('type', '=', 'purchase'),
            ('company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.purchase_journal:
            cls.purchase_journal = cls.env['account.journal'].create({
                'name': 'Purchase Journal',
                'code': 'BILL',
                'type': 'purchase',
                'company_id': cls.company.id,
            })

        # Find or create cash journal
        cls.cash_journal = cls.env['account.journal'].search([
            ('code', '=', 'CASH'),
            ('type', '=', 'cash'),
            ('company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.cash_journal:
            cls.cash_journal = cls.env['account.journal'].create({
                'name': 'Cash Journal',
                'code': 'CASH',
                'type': 'cash',
                'company_id': cls.company.id,
            })

        # Find or create bank journal
        cls.bank_journal = cls.env['account.journal'].search([
            ('code', '=', 'BANK'),
            ('type', '=', 'bank'),
            ('company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.bank_journal:
            cls.bank_journal = cls.env['account.journal'].create({
                'name': 'Bank Journal',
                'code': 'BANK',
                'type': 'bank',
                'company_id': cls.company.id,
            })

        # Get or create tax group (required in Odoo 19)
        # Tax group must have same country_id as company
        cr_country_id = cls.env.ref('base.cr').id
        tax_group = cls.env['account.tax.group'].search([
            ('country_id', '=', cr_country_id)
        ], limit=1)
        if not tax_group:
            tax_group = cls.env['account.tax.group'].create({
                'name': 'IVA',
                'country_id': cr_country_id,
            })

        # Create default tax (13% IVA - standard Costa Rica sales tax)
        cls.tax_13 = cls.env['account.tax'].create({
            'name': 'IVA 13% (Ventas)',
            'amount': 13.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': cls.company.id,
            'country_id': cr_country_id,  # Must match tax_group country
            'tax_group_id': tax_group.id,
        })

        # Create purchase tax (13% IVA for vendor bills)
        cls.tax_13_purchase = cls.env['account.tax'].create({
            'name': 'IVA 13% (Compras)',
            'amount': 13.0,
            'amount_type': 'percent',
            'type_tax_use': 'purchase',
            'company_id': cls.company.id,
            'country_id': cr_country_id,  # Must match tax_group country
            'tax_group_id': tax_group.id,
        })

        # Create 0% tax (for exempt products)
        cls.tax_0 = cls.env['account.tax'].create({
            'name': 'Exento',
            'amount': 0.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': cls.company.id,
            'country_id': cr_country_id,  # Must match tax_group country
            'tax_group_id': tax_group.id,
        })

        # Create test customer partner
        cls.partner = cls._create_test_partner(
            vat='101234567',  # Cédula Física format (9 digits)
            name='Test Customer'
        )

        # Create test invoiceable product with CABYS code
        cls.product = cls._create_test_product(
            name='Test Service',
            price=10000.0
        )

    @classmethod
    def _create_test_partner(cls, vat=None, name=None):
        """
        Create a test partner with unique VAT number.

        Args:
            vat (str, optional): Partner VAT/ID number. If None, generates unique VAT.
            name (str, optional): Partner name. If None, generates unique name.

        Returns:
            res.partner: Created partner record

        Example:
            partner = self._create_test_partner(vat='101234567', name='Customer A')
        """
        if vat is None:
            # Generate unique VAT using UUID (take first 9 digits)
            vat = str(uuid.uuid4().int)[:9]

        if name is None:
            name = f'Test Partner {vat}'

        return cls.env['res.partner'].create({
            'name': name,
            'country_id': cls.env.ref('base.cr').id,
            'vat': vat,
            'email': f'{vat}@test.example.com',
            'company_id': cls.company.id,
        })

    @classmethod
    def _create_test_product(cls, name=None, price=100.0):
        """
        Create a test invoiceable product.

        Args:
            name (str, optional): Product name. If None, generates unique name.
            price (float, optional): Product list price. Defaults to 100.0.

        Returns:
            product.product: Created product record

        Example:
            product = self._create_test_product(name='Premium Service', price=5000.0)
        """
        if name is None:
            unique_id = str(uuid.uuid4())[:8]
            name = f'Test Product {unique_id}'

        return cls.env['product.product'].create({
            'name': name,
            'type': 'service',
            'list_price': price,
            'invoice_policy': 'order',
            # Note: l10n_cr_product_code is set on invoice lines, not products
            'taxes_id': [(6, 0, [cls.tax_13.id])],  # Default to 13% IVA
        })

    def _create_test_invoice(self, invoice_type='out_invoice', partner=None, lines=None):
        """
        Create a test invoice with proper journal and lines.

        Args:
            invoice_type (str): Type of invoice: 'out_invoice', 'out_refund',
                               'in_invoice', 'in_refund'. Defaults to 'out_invoice'.
            partner (res.partner, optional): Invoice partner. If None, uses cls.partner.
            lines (list, optional): Invoice line data as list of dicts.
                                   If None, creates single line with default product.

        Returns:
            account.move: Created invoice record (in draft state)

        Example:
            # Simple invoice with default line
            invoice = self._create_test_invoice()

            # Invoice with custom lines
            invoice = self._create_test_invoice(
                invoice_type='out_invoice',
                lines=[
                    {'product_id': product1.id, 'quantity': 2, 'price_unit': 5000.0},
                    {'product_id': product2.id, 'quantity': 1, 'price_unit': 10000.0},
                ]
            )
        """
        if partner is None:
            partner = self.partner

        # Select proper journal based on invoice type
        if invoice_type in ('out_invoice', 'out_refund'):
            journal = self.sales_journal
        elif invoice_type in ('in_invoice', 'in_refund'):
            journal = self.purchase_journal
        else:
            raise ValueError(f"Invalid invoice_type: {invoice_type}")

        # Create default invoice lines if none provided
        if lines is None:
            lines = [{
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': self.product.list_price,
                'tax_ids': [(6, 0, [self.tax_13.id])],
            }]

        # Convert lines to Odoo command format
        invoice_lines = [(0, 0, line) for line in lines]

        # Create invoice
        invoice = self.env['account.move'].create({
            'move_type': invoice_type,
            'partner_id': partner.id,
            'company_id': self.company.id,
            'journal_id': journal.id,
            'invoice_date': '2025-02-01',
            'invoice_line_ids': invoice_lines,
        })

        return invoice

    def _create_einvoice_document(self, move, document_type='FE'):
        """
        Create an e-invoice document record for a move.

        Args:
            move (account.move): The invoice/move to create e-invoice for
            document_type (str): Document type code: 'FE', 'TE', 'NC', 'ND', 'FEE', 'MR'

        Returns:
            l10n_cr.einvoice.document: Created e-invoice document record

        Example:
            invoice = self._create_test_invoice()
            einvoice = self._create_einvoice_document(invoice, document_type='FE')
        """
        return self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'document_type': document_type,
            'company_id': self.company.id,
        })

    def _post_invoice(self, invoice):
        """
        Post an invoice and return it.

        Args:
            invoice (account.move): Invoice to post

        Returns:
            account.move: Posted invoice

        Example:
            invoice = self._create_test_invoice()
            posted_invoice = self._post_invoice(invoice)
            self.assertEqual(posted_invoice.state, 'posted')
        """
        invoice.action_post()
        return invoice

    def _create_and_post_invoice(self, **kwargs):
        """
        Create and post an invoice in one step.

        Args:
            **kwargs: Arguments passed to _create_test_invoice()

        Returns:
            account.move: Posted invoice

        Example:
            invoice = self._create_and_post_invoice(
                lines=[{'product_id': self.product.id, 'quantity': 2, 'price_unit': 5000}]
            )
        """
        invoice = self._create_test_invoice(**kwargs)
        return self._post_invoice(invoice)
