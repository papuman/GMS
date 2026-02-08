# -*- coding: utf-8 -*-
"""
Base test case classes for l10n_cr_einvoice tests.

This module provides base test classes that set up complete Odoo accounting
infrastructure required for e-invoice testing. All test classes should inherit
from these base classes instead of directly from TransactionCase.

Classes:
    L10nCrEInvoiceCommon: Lightweight base class with validation-compliant partner/company fixtures
    EInvoiceTestCase: Full accounting setup base class for CR e-invoicing
"""

import base64
import uuid
from odoo import fields
from odoo.tests import TransactionCase


class L10nCrEInvoiceCommon(TransactionCase):
    """
    Base test class with common fixtures for l10n_cr_einvoice tests.

    Provides validation-compliant partner and company data that all tests can inherit.
    This is a lightweight alternative to EInvoiceTestCase that focuses on partner
    and company fixtures without full accounting infrastructure setup.

    Use this class when you need standard test partners but don't need journals,
    taxes, or full accounting setup.

    Fixtures provided:
    - costa_rica: Costa Rica country record
    - payment_method: Standard payment method (Efectivo)
    - partner_fisica: Valid física partner (individual)
    - partner_juridica: Valid jurídica partner (company)
    - partner_dimex: Valid DIMEX partner (foreign resident)
    - product: Generic test product
    - company: Company with Hacienda configuration

    Usage:
        class TestMyFeature(L10nCrEInvoiceCommon):
            def test_something(self):
                # Use inherited fixtures
                einvoice = self.env['l10n_cr.einvoice.document'].create({
                    'partner_id': self.partner_fisica.id,
                    'document_type': 'FE',
                    ...
                })
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Costa Rica country
        cls.costa_rica = cls.env.ref('base.cr')

        # Standard payment method (Efectivo)
        # This assumes the payment methods data file has been loaded
        cls.payment_method = cls.env['l10n_cr.payment.method'].search([
            ('code', '=', '01')  # Efectivo
        ], limit=1)
        if not cls.payment_method:
            # Fallback: create payment method if not found
            cls.payment_method = cls.env['l10n_cr.payment.method'].create({
                'code': '01',
                'name': 'Efectivo',
                'description': 'Pago en efectivo',
                'active': True,
            })

        # Valid física partner (individual)
        cls.partner_fisica = cls.env['res.partner'].create({
            'name': 'Juan Pérez García',
            'vat': '123456789',
            'email': 'juan.perez@example.com',
            'phone': '88887777',
            'mobile': '88889999',
            'street': 'Calle Principal 123',
            'street2': 'Apartado 456',
            'city': 'San José',
            'state_id': False,
            'zip': '10101',
            'country_id': cls.costa_rica.id,
        })

        # Valid jurídica partner (company)
        cls.partner_juridica = cls.env['res.partner'].create({
            'name': 'Empresa Test S.A.',
            'vat': '3101234567',
            'is_company': True,
            'email': 'info@empresatest.cr',
            'phone': '22223333',
            'mobile': '88886666',
            'street': 'Avenida Central 789',
            'city': 'San José',
            'country_id': cls.costa_rica.id,
        })

        # Valid DIMEX partner (foreign resident)
        cls.partner_dimex = cls.env['res.partner'].create({
            'name': 'María González',
            'vat': '123456789012',
            'email': 'maria.gonzalez@example.com',
            'phone': '88885555',
            'street': 'Residencial Internacional',
            'city': 'San José',
            'country_id': cls.costa_rica.id,
        })

        # Generic product for testing
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.00,
            'standard_price': 50.00,
        })

        # Company with Hacienda configuration
        cls.company = cls.env.company
        cls.company.write({
            'vat': '3999999999',
            'country_id': cls.costa_rica.id,
            'l10n_cr_emisor_location': '10101',
            'l10n_cr_proveedor_sistemas': '3999999999',  # Required by v4.4
        })

        # Set activity code on company partner (required for e-invoice)
        if cls.company.partner_id:
            cls.company.partner_id.l10n_cr_activity_code = '861201'


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
            'l10n_cr_proveedor_sistemas': '3101234567',  # Required by v4.4
        })

        # Set activity code on company partner (required for e-invoice)
        cls.company.partner_id.l10n_cr_activity_code = '861201'

        # Set dummy certificate for XML generation validation
        # (bypasses _validate_company_certificate check in xml_generator)
        dummy_cert = base64.b64encode(b'dummy-test-certificate-data')
        cls.company.write({
            'l10n_cr_certificate': dummy_cert,
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': 'test1234',
        })

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

        # Get a CIIU code for FE mandatory field validation (required after Oct 6, 2025)
        ciiu_code = cls.env['l10n_cr.ciiu.code'].search([], limit=1)

        partner_vals = {
            'name': name,
            'country_id': cls.env.ref('base.cr').id,
            'vat': vat,
            'email': f'{vat}@test.example.com',
            'phone': '22001100',
            'company_id': cls.company.id,
        }
        if ciiu_code:
            partner_vals['l10n_cr_economic_activity_id'] = ciiu_code.id
        return cls.env['res.partner'].create(partner_vals)

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
        # Get partner from move
        partner = move.partner_id if move.partner_id else False

        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id,
            'document_type': document_type,
            'company_id': self.company.id,
            'partner_id': partner.id if partner else False,
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

    # Cédula Cache Test Fixtures

    @classmethod
    def _create_verified_partner(cls, name='Verified Partner', vat=None):
        """
        Create a partner with verified Hacienda cache.

        Args:
            name (str): Partner name
            vat (str, optional): Partner VAT. If None, generates unique VAT.

        Returns:
            res.partner: Partner with verified cache (inscrito status)

        Example:
            partner = self._create_verified_partner(name='Acme Corp', vat='3101234567')
        """
        from datetime import datetime, timezone
        if vat is None:
            vat = str(uuid.uuid4().int)[:10]

        return cls.env['res.partner'].create({
            'name': name,
            'vat': vat,
            'country_id': cls.env.ref('base.cr').id,
            'company_id': cls.company.id,
            'l10n_cr_hacienda_verified': True,
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(datetime.now(timezone.utc)),
        })

    @classmethod
    def _create_unverified_partner(cls, name='Unverified Partner', vat=None):
        """
        Create a partner without Hacienda verification.

        Args:
            name (str): Partner name
            vat (str, optional): Partner VAT. If None, generates unique VAT.

        Returns:
            res.partner: Partner without cache verification

        Example:
            partner = self._create_unverified_partner(name='New Customer', vat='1234567890')
        """
        if vat is None:
            vat = str(uuid.uuid4().int)[:10]

        return cls.env['res.partner'].create({
            'name': name,
            'vat': vat,
            'country_id': cls.env.ref('base.cr').id,
            'company_id': cls.company.id,
            'l10n_cr_hacienda_verified': False,
        })

    @classmethod
    def _create_stale_cache_partner(cls, name='Stale Cache Partner', vat=None, days_old=30):
        """
        Create a partner with stale cache.

        Args:
            name (str): Partner name
            vat (str, optional): Partner VAT. If None, generates unique VAT.
            days_old (int): How many days old the cache should be

        Returns:
            res.partner: Partner with stale cache

        Example:
            partner = self._create_stale_cache_partner(name='Old Customer', days_old=45)
        """
        from datetime import datetime, timedelta, timezone
        if vat is None:
            vat = str(uuid.uuid4().int)[:10]

        old_sync = datetime.now(timezone.utc) - timedelta(days=days_old)

        return cls.env['res.partner'].create({
            'name': name,
            'vat': vat,
            'country_id': cls.env.ref('base.cr').id,
            'company_id': cls.company.id,
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(old_sync),
            'l10n_cr_tax_status': 'inscrito',
            'l10n_cr_hacienda_verified': False,
        })

    @classmethod
    def _create_override_partner(cls, name='Override Partner', vat=None, reason='Test override'):
        """
        Create a partner with validation override.

        Args:
            name (str): Partner name
            vat (str, optional): Partner VAT. If None, generates unique VAT.
            reason (str): Override justification reason

        Returns:
            res.partner: Partner with validation override

        Example:
            partner = self._create_override_partner(
                name='Government Entity',
                reason='Exempt government entity'
            )
        """
        if vat is None:
            vat = str(uuid.uuid4().int)[:10]

        return cls.env['res.partner'].create({
            'name': name,
            'vat': vat,
            'country_id': cls.env.ref('base.cr').id,
            'company_id': cls.company.id,
            'l10n_cr_cedula_validation_override': True,
            'l10n_cr_override_reason': reason,
            'l10n_cr_override_user_id': cls.env.user.id,
            'l10n_cr_override_date': fields.Datetime.now(),
        })

    @classmethod
    def _create_not_found_partner(cls, name='Not Found Partner', vat=None):
        """
        Create a partner not found in Hacienda registry.

        Args:
            name (str): Partner name
            vat (str, optional): Partner VAT. If None, generates unique VAT.

        Returns:
            res.partner: Partner with no_encontrado status

        Example:
            partner = self._create_not_found_partner(name='Invalid ID', vat='9999999999')
        """
        from datetime import datetime, timezone
        if vat is None:
            vat = str(uuid.uuid4().int)[:10]

        return cls.env['res.partner'].create({
            'name': name,
            'vat': vat,
            'country_id': cls.env.ref('base.cr').id,
            'company_id': cls.company.id,
            'l10n_cr_hacienda_verified': False,
            'l10n_cr_tax_status': 'no_encontrado',
            'l10n_cr_hacienda_last_sync': fields.Datetime.to_string(datetime.now(timezone.utc)),
        })
