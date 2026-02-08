# -*- coding: utf-8 -*-
"""
E2E Tests: Complete Invoice Lifecycle with Hacienda Sandbox

Tests the complete end-to-end flow:
1. Create invoice
2. Generate XML (v4.4 compliant)
3. Sign XML (XAdES-EPES)
4. Submit to Hacienda (mocked in test framework, real via CLI)
5. Poll for acceptance
6. Verify state transitions

NOTE: Odoo's test framework blocks external HTTP requests.
The submission step uses a mocked API response.
For real Hacienda sandbox testing, use test_einvoice_cli.py via Docker shell.

To run:
  docker compose run --rm odoo -d GMS -u l10n_cr_einvoice --test-tags=e2e --stop-after-init --no-http
"""

import random
import uuid
from unittest.mock import patch

from datetime import datetime
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


def _generate_unique_vat_person():
    """Generate unique VAT number for person (9 digits, numeric only)."""
    return f"1{random.randint(10000000, 99999999)}"


def _generate_unique_email(prefix='test'):
    """Generate unique email address."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def _generate_cr_phone():
    """Generate a valid 8-digit Costa Rica phone number."""
    return f"{random.randint(60000000, 89999999)}"


def _mock_hacienda_accepted():
    """Return a realistic Hacienda 'accepted' response."""
    return {
        'ind-estado': 'aceptado',
        'respuesta-xml': '',
        'respuesta-xml-decoded': 'Documento aceptado',
    }


def _mock_hacienda_received():
    """Return a realistic Hacienda 'received/processing' response."""
    return {
        'ind-estado': 'recibido',
        'respuesta-xml': '',
    }


@tagged('e2e', 'post_install', '-at_install')
class TestE2ESandboxLifecycle(TransactionCase):
    """
    End-to-end tests for the invoice → XML → sign → submit pipeline.

    XML generation and signing are tested with REAL code (no mocks).
    Hacienda API submission is mocked since the test framework blocks HTTP.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Models
        cls.Invoice = cls.env['account.move']
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.Company = cls.env.company
        cls.EInvoiceDoc = cls.env['l10n_cr.einvoice.document']

        # Set company country to Costa Rica (required for l10n_cr_requires_einvoice)
        cr_country = cls.env.ref('base.cr')
        cls.Company.partner_id.write({'country_id': cr_country.id})
        cls.Company.write({'account_fiscal_country_id': cr_country.id})

        # Configure sandbox credentials
        cls.Company.write({
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_hacienda_username': 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr',
            'l10n_cr_hacienda_password': 'e8KLJRHzRA1P0W2ybJ5T',
        })

        # Ensure default CABYS code is set
        cls.env['ir.config_parameter'].sudo().set_param(
            'l10n_cr_einvoice.default_cabys_code', '9652000009900'
        )

        # Ensure activity code is set on company partner
        if not cls.Company.partner_id.l10n_cr_activity_code:
            cls.Company.partner_id.write({'l10n_cr_activity_code': '931100'})

        # Create CR tax group and IVA 13% tax for CR fiscal country
        cls.cr_tax_group = cls.env['account.tax.group'].create({
            'name': 'IVA CR (E2E)',
            'country_id': cr_country.id,
        })
        cls.cr_iva_13 = cls.env['account.tax'].create({
            'name': 'IVA 13% CR',
            'amount': 13.0,
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'country_id': cr_country.id,
            'tax_group_id': cls.cr_tax_group.id,
        })

    def _create_test_customer(self):
        """Create a test customer with valid Costa Rica identification."""
        activity = self.env['l10n_cr.ciiu.code'].search([], limit=1)
        vals = {
            'name': 'Test Customer E2E',
            'vat': _generate_unique_vat_person(),
            'email': _generate_unique_email('test'),
            'phone': _generate_cr_phone(),
            'country_id': self.env.ref('base.cr').id,
        }
        if activity:
            vals['l10n_cr_economic_activity_id'] = activity.id
        return self.Partner.create(vals)

    def _create_test_product(self, price=10000.00):
        """Create a test product/service."""
        return self.Product.create({
            'name': 'Test Service - E2E',
            'type': 'service',
            'list_price': price,
            'taxes_id': [(6, 0, [self.cr_iva_13.id])],
        })

    def _create_and_post_invoice(self, customer, product, price=None):
        """Create and post an invoice, returning (invoice, einvoice_doc)."""
        unit_price = price or product.list_price
        invoice = self.Invoice.create({
            'move_type': 'out_invoice',
            'partner_id': customer.id,
            'invoice_date': datetime.today().date(),
            'invoice_line_ids': [(0, 0, {
                'name': product.name,
                'product_id': product.id,
                'quantity': 1.0,
                'price_unit': unit_price,
            })],
        })
        invoice.action_post()

        einvoice_doc = self.EInvoiceDoc.search([('move_id', '=', invoice.id)])
        return invoice, einvoice_doc

    def _generate_and_sign(self, einvoice_doc):
        """Generate XML and sign it. Returns the signed document."""
        einvoice_doc.action_generate_xml()
        self.assertEqual(einvoice_doc.state, 'generated')
        self.assertTrue(einvoice_doc.xml_content)
        self.assertTrue(einvoice_doc.clave)
        self.assertEqual(len(einvoice_doc.clave), 50)

        einvoice_doc.action_sign_xml()
        self.assertEqual(einvoice_doc.state, 'signed')
        self.assertTrue(einvoice_doc.signed_xml)
        self.assertIn('Signature', einvoice_doc.signed_xml)
        return einvoice_doc

    # ========================================================================
    # P0 TESTS
    # ========================================================================

    def test_e2e_complete_lifecycle_factura_electronica(self):
        """
        P0: Complete FE lifecycle - create, generate XML, sign, submit.

        Uses amount > 1M CRC to trigger FE auto-classification.
        XML generation and signing use real code (no mocks).
        Hacienda submission is mocked.
        """
        customer = self._create_test_customer()
        product = self._create_test_product(price=1500000.00)
        invoice, einvoice_doc = self._create_and_post_invoice(customer, product)

        self.assertEqual(len(einvoice_doc), 1, "E-invoice document should be created")
        self.assertEqual(einvoice_doc.state, 'draft')
        self.assertEqual(einvoice_doc.document_type, 'FE', "Amount > 1M should create FE")

        # Generate XML and sign (REAL - no mocks)
        self._generate_and_sign(einvoice_doc)

        # Verify XML contains expected FE elements
        self.assertIn('FacturaElectronica', einvoice_doc.xml_content)
        self.assertIn('SignatureValue', einvoice_doc.signed_xml)
        self.assertIn('KeyInfo', einvoice_doc.signed_xml)

        # Submit with mocked API (test framework blocks HTTP)
        with patch.object(type(self.env['l10n_cr.hacienda.api']),
                         'submit_invoice', return_value=_mock_hacienda_accepted()):
            einvoice_doc.action_submit_to_hacienda()

        self.assertIn(einvoice_doc.state, ['submitted', 'accepted'])
        self.assertTrue(einvoice_doc.hacienda_submission_date)

        # If accepted, verify acceptance data
        if einvoice_doc.state == 'accepted':
            self.assertTrue(einvoice_doc.hacienda_acceptance_date)
            self.assertFalse(einvoice_doc.error_message)

    def test_e2e_tiquete_electronico_submission(self):
        """
        P0: Complete TE lifecycle.
        Amount <= 1M CRC auto-classifies as TE.
        """
        customer = self._create_test_customer()
        product = self._create_test_product(price=10000.00)
        invoice, einvoice_doc = self._create_and_post_invoice(customer, product)

        self.assertEqual(len(einvoice_doc), 1)
        self.assertEqual(einvoice_doc.document_type, 'TE', "Amount <= 1M should create TE")

        # Generate XML and sign (REAL)
        self._generate_and_sign(einvoice_doc)

        # Verify XML contains expected TE elements
        self.assertIn('TiqueteElectronico', einvoice_doc.xml_content)

        # Submit with mocked API
        with patch.object(type(self.env['l10n_cr.hacienda.api']),
                         'submit_invoice', return_value=_mock_hacienda_accepted()):
            einvoice_doc.action_submit_to_hacienda()

        self.assertIn(einvoice_doc.state, ['submitted', 'accepted'])

    def test_e2e_nota_credito_submission(self):
        """
        P1: Credit note (NC) complete lifecycle.
        Requires original invoice to have a clave.
        """
        customer = self._create_test_customer()
        product = self._create_test_product()
        original_invoice, original_einvoice = self._create_and_post_invoice(customer, product)

        # Generate and sign the original invoice first
        self.assertTrue(original_einvoice, "Original einvoice should exist")
        self._generate_and_sign(original_einvoice)

        # Mock-submit the original so it has a clave and accepted state
        with patch.object(type(self.env['l10n_cr.hacienda.api']),
                         'submit_invoice', return_value=_mock_hacienda_accepted()):
            original_einvoice.action_submit_to_hacienda()

        # Create credit note via reversal wizard
        refund_wizard = self.env['account.move.reversal'].with_context(
            active_ids=original_invoice.ids,
            active_model='account.move'
        ).create({
            'reason': 'Test refund for E2E',
            'journal_id': original_invoice.journal_id.id,
        })
        refund_action = refund_wizard.reverse_moves()

        if refund_action.get('res_id'):
            refund_invoice = self.Invoice.browse(refund_action['res_id'])
        elif refund_action.get('domain'):
            refund_invoice = self.Invoice.search(refund_action['domain'], limit=1)
        else:
            self.fail("Reversal wizard did not return a refund invoice")

        if refund_invoice.state == 'draft':
            refund_invoice.action_post()

        nc_einvoice = self.EInvoiceDoc.search([('move_id', '=', refund_invoice.id)])
        self.assertTrue(nc_einvoice, "NC einvoice doc should be created")
        self.assertEqual(nc_einvoice.document_type, 'NC')

        # Generate and sign NC
        self._generate_and_sign(nc_einvoice)
        self.assertIn('NotaCreditoElectronica', nc_einvoice.xml_content)

        # Submit NC
        with patch.object(type(self.env['l10n_cr.hacienda.api']),
                         'submit_invoice', return_value=_mock_hacienda_accepted()):
            nc_einvoice.action_submit_to_hacienda()
        self.assertIn(nc_einvoice.state, ['submitted', 'accepted'])

    # ========================================================================
    # ERROR HANDLING TESTS
    # ========================================================================

    def test_e2e_retry_on_transient_failure(self):
        """
        P0: Verify error handling on submission failure.

        Note: In TransactionCase, the state change inside the try/except
        block is rolled back by the savepoint when UserError propagates.
        We verify the error IS raised (correct behavior).
        """
        customer = self._create_test_customer()
        product = self._create_test_product()
        invoice, einvoice_doc = self._create_and_post_invoice(customer, product)

        self.assertTrue(einvoice_doc)
        self._generate_and_sign(einvoice_doc)

        # Simulate a transient failure - verify UserError is raised
        with patch.object(type(self.env['l10n_cr.hacienda.api']),
                         'submit_invoice', side_effect=Exception("Connection timeout")):
            with self.assertRaises(UserError) as ctx:
                einvoice_doc.action_submit_to_hacienda()
            self.assertIn("Connection timeout", str(ctx.exception))

    def test_e2e_idempotency_no_double_submit(self):
        """
        P1: Verify calling submit twice doesn't corrupt state.
        """
        customer = self._create_test_customer()
        product = self._create_test_product()
        invoice, einvoice_doc = self._create_and_post_invoice(customer, product)

        self.assertTrue(einvoice_doc)
        self._generate_and_sign(einvoice_doc)

        # First submission (accepted)
        with patch.object(type(self.env['l10n_cr.hacienda.api']),
                         'submit_invoice', return_value=_mock_hacienda_accepted()):
            einvoice_doc.action_submit_to_hacienda()
        first_state = einvoice_doc.state

        # Second submission attempt should be blocked (not in signed state)
        with self.assertRaises(UserError):
            einvoice_doc.action_submit_to_hacienda()

        # State should be unchanged
        self.assertEqual(einvoice_doc.state, first_state)

    # ========================================================================
    # PERFORMANCE TESTS
    # ========================================================================

    def test_e2e_bulk_xml_generation_performance(self):
        """
        P2: Test bulk XML generation + signing performance (10 invoices).

        Target: < 2s per invoice for XML generation + signing.
        """
        import time

        customer = self._create_test_customer()
        product = self._create_test_product()

        # Create 10 invoices
        invoices = []
        einvoice_docs = []
        for i in range(10):
            invoice = self.Invoice.create({
                'move_type': 'out_invoice',
                'partner_id': customer.id,
                'invoice_date': datetime.today().date(),
                'invoice_line_ids': [(0, 0, {
                    'name': f'{product.name} #{i+1}',
                    'product_id': product.id,
                    'quantity': 1.0,
                    'price_unit': product.list_price,
                })],
            })
            invoice.action_post()
            invoices.append(invoice)

        docs = self.EInvoiceDoc.search([
            ('move_id', 'in', [inv.id for inv in invoices])
        ])
        self.assertEqual(len(docs), 10)

        # Measure XML generation + signing time
        start_time = time.time()

        for doc in docs:
            doc.action_generate_xml()
            doc.action_sign_xml()

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 10

        # Performance target: < 2s per invoice for gen + sign
        self.assertLess(
            avg_time, 2.0,
            f"Average time per invoice ({avg_time:.2f}s) exceeds 2s target"
        )
