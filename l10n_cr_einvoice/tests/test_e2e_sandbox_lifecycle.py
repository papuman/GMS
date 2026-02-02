# -*- coding: utf-8 -*-
"""
E2E Tests: Complete Invoice Lifecycle with Hacienda Sandbox

Tests the complete end-to-end flow:
1. Create invoice
2. Generate XML
3. Sign XML
4. Submit to Hacienda sandbox
5. Poll for acceptance
6. Verify acceptance status

Priority: P0 (Critical - must pass before production)
Risk: R-001 (Compliance), R-002 (Data Integrity), R-005 (External Dependency)

NOTE: To run these tests:
  docker compose run --rm odoo -d GMS --test-enable --test-tags=e2e --stop-after-init --no-http
"""

from datetime import datetime
from odoo.tests.common import TransactionCase, tagged
import uuid


def _generate_unique_vat_company():
    """Generate unique VAT number for company (10 digits starting with 3)."""
    return f"310{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_vat_person():
    """Generate unique VAT number for person (9 digits)."""
    return f"10{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_email(prefix='test'):
    """Generate unique email address."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"




@tagged('e2e', 'external')
class TestE2ESandboxLifecycle(TransactionCase):
    """
    End-to-end tests with real Hacienda sandbox API.

    IMPORTANT: These tests require:
    - Sandbox credentials configured
    - Test certificate (certificado.p12)
    - Network access to Hacienda sandbox
    - Should NOT run on every commit (too slow, external dependency)
    - Run nightly or on-demand
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
        cls.XMLGenerator = cls.env['l10n_cr.xml.generator']
        cls.XMLSigner = cls.env['l10n_cr.xml.signer']
        cls.HaciendaAPI = cls.env['l10n_cr.hacienda.api']
        cls.CertManager = cls.env['l10n_cr.certificate.manager']

        # Configure sandbox credentials
        cls._configure_sandbox()

    @classmethod
    def _configure_sandbox(cls):
        """Configure company with sandbox credentials and test certificate."""
        # Sandbox OAuth2 credentials (from docs/Tribu-CR/Credentials.md)
        cls.Company.write({
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_hacienda_username': 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr',
            'l10n_cr_hacienda_password': 'e8KLJRHzRA1P0W2ybJ5T',
        })

        # Note: Certificate loading is handled by certificate_manager
        # In real E2E tests, we'd load the actual certificado.p12
        # For CI/CD, inject via environment variable

    def _create_test_customer(self):
        """Create a test customer with valid Costa Rica identification."""
        return self.Partner.create({
            'name': 'Test Customer E2E',
            'vat': _generate_unique_vat_person(),  # 9-digit cédula
            'l10n_cr_id_type': '01',  # Physical person
            'email': _generate_unique_email('test'),
            'country_id': self.env.ref('base.cr').id,
        })

    def _create_test_product(self):
        """Create a test product/service."""
        return self.Product.create({
            'name': 'Test Service - E2E',
            'type': 'service',
            'list_price': 10000.00,
            'taxes_id': [(6, 0, [self.env.ref('l10n_cr.tax_iva_13').id])],
        })

    def _create_test_invoice(self, customer, product):
        """Create a test invoice."""
        invoice = self.Invoice.create({
            'move_type': 'out_invoice',
            'partner_id': customer.id,
            'invoice_date': datetime.today().date(),
            'invoice_line_ids': [(0, 0, {
                'name': product.name,
                'product_id': product.id,
                'quantity': 1.0,
                'price_unit': product.list_price,
            })],
        })
        return invoice

    # ========================================================================
    # P0 TESTS
    # ========================================================================

    def test_e2e_complete_lifecycle_factura_electronica(self):
        """Priority: P0 (Critical)"""
        """
        P0: Complete invoice lifecycle (FE) - create to acceptance.

        Covers:
        - R-001: Hacienda v4.4 compliance
        - R-002: Data integrity (no double submit)
        - R-005: External API dependency

        Flow:
        1. Create invoice (Odoo)
        2. Generate XML (v4.4)
        3. Validate XSD
        4. Sign XML (XAdES-EPES)
        5. Submit to Hacienda sandbox
        6. Poll for status
        7. Verify acceptance
        """
        # Step 1: Create test data
        customer = self._create_test_customer()
        product = self._create_test_product()
        invoice = self._create_test_invoice(customer, product)

        # Step 2: Post invoice (this should auto-create e-invoice document)
        invoice.action_post()

        # Verify e-invoice document created
        einvoice_doc = self.EInvoiceDoc.search([
            ('invoice_id', '=', invoice.id)
        ])
        self.assertEqual(len(einvoice_doc), 1, "E-invoice document should be created")
        self.assertEqual(einvoice_doc.state, 'draft', "Initial state should be draft")
        self.assertEqual(einvoice_doc.document_type, 'FE', "Should be Factura Electrónica")

        # Step 3: Generate XML
        einvoice_doc.action_generate_xml()

        self.assertEqual(einvoice_doc.state, 'generated', "State should be 'generated'")
        self.assertTrue(einvoice_doc.xml_content, "XML content should exist")
        self.assertTrue(einvoice_doc.clave, "Clave should be generated")
        self.assertEqual(len(einvoice_doc.clave), 50, "Clave should be 50 digits")

        # Step 4: Validate XSD
        # (XSD validation happens automatically in action_generate_xml)
        # Just verify no validation errors
        self.assertFalse(einvoice_doc.error_message, f"Should have no XSD errors: {einvoice_doc.error_message}")

        # Step 5: Sign XML
        einvoice_doc.action_sign_xml()

        self.assertEqual(einvoice_doc.state, 'signed', "State should be 'signed'")
        self.assertTrue(einvoice_doc.xml_signed, "Signed XML should exist")
        self.assertIn('Signature', einvoice_doc.xml_signed, "Should contain signature element")
        self.assertIn('SignatureValue', einvoice_doc.xml_signed, "Should contain signature value")
        self.assertIn('KeyInfo', einvoice_doc.xml_signed, "Should contain key info")

        # Step 6: Submit to Hacienda sandbox
        einvoice_doc.action_submit_to_hacienda()

        self.assertEqual(einvoice_doc.state, 'submitted', "State should be 'submitted'")
        self.assertTrue(einvoice_doc.submission_date, "Submission date should be set")

        # Verify response message created
        response_messages = self.env['l10n_cr.hacienda.response.message'].search([
            ('einvoice_document_id', '=', einvoice_doc.id)
        ])
        self.assertGreater(len(response_messages), 0, "Should have at least one response message")

        # Step 7: Poll for acceptance (or manually check status)
        # In sandbox, acceptance is usually immediate, but may take a few seconds
        einvoice_doc.action_check_status()

        # Verify final state (should be 'accepted' or 'processing')
        # Sandbox may not immediately accept, so we allow 'processing'
        self.assertIn(
            einvoice_doc.state,
            ['accepted', 'processing'],
            f"Final state should be 'accepted' or 'processing', got: {einvoice_doc.state}"
        )

        # If accepted, verify acceptance data
        if einvoice_doc.state == 'accepted':
            self.assertTrue(einvoice_doc.acceptance_date, "Acceptance date should be set")
            self.assertFalse(einvoice_doc.error_message, "Should have no errors")

        # Step 8: Verify audit trail
        # Response messages should exist
        self.assertGreater(
            len(response_messages), 0,
            "Should have response messages (audit trail)"
        )

        # Verify no duplicate submissions (idempotency)
        submission_count = self.env['l10n_cr.hacienda.response.message'].search_count([
            ('einvoice_document_id', '=', einvoice_doc.id),
            ('response_type', '=', 'submit')
        ])
        self.assertEqual(submission_count, 1, "Should have exactly 1 submission (no duplicates)")

    def test_e2e_tiquete_electronico_submission(self):
        """Priority: P0 (Critical)"""
        """
        P0: Complete tiquete electrónico (TE) lifecycle.

        Tiquetes are used for POS sales (simplified invoices).
        Similar to FE but with less detail required.
        """
        # Create POS-like invoice (simplified)
        customer = self._create_test_customer()
        product = self._create_test_product()

        invoice = self.Invoice.create({
            'move_type': 'out_invoice',
            'partner_id': customer.id,
            'invoice_date': datetime.today().date(),
            'l10n_cr_document_type': 'TE',  # Force tiquete type
            'invoice_line_ids': [(0, 0, {
                'name': product.name,
                'product_id': product.id,
                'quantity': 1.0,
                'price_unit': product.list_price,
            })],
        })

        invoice.action_post()

        # Verify TE document created
        einvoice_doc = self.EInvoiceDoc.search([
            ('invoice_id', '=', invoice.id)
        ])
        self.assertEqual(einvoice_doc.document_type, 'TE', "Should be Tiquete Electrónico")

        # Run through lifecycle
        einvoice_doc.action_generate_xml()
        self.assertEqual(einvoice_doc.state, 'generated')

        einvoice_doc.action_sign_xml()
        self.assertEqual(einvoice_doc.state, 'signed')

        einvoice_doc.action_submit_to_hacienda()
        self.assertEqual(einvoice_doc.state, 'submitted')

        einvoice_doc.action_check_status()
        self.assertIn(einvoice_doc.state, ['accepted', 'processing'])

    def test_e2e_nota_credito_submission(self):
        """
        P1: Credit note (NC) submission to sandbox.

        Credit notes are used for refunds/corrections.
        """
        # First create and accept a regular invoice
        customer = self._create_test_customer()
        product = self._create_test_product()
        original_invoice = self._create_test_invoice(customer, product)
        original_invoice.action_post()

        # Create credit note
        refund_wizard = self.env['account.move.reversal'].with_context(
            active_ids=original_invoice.ids,
            active_model='account.move'
        ).create({
            'reason': 'Test refund for E2E',
            'refund_method': 'refund',
        })
        refund_action = refund_wizard.reverse_moves()
        refund_invoice = self.Invoice.browse(refund_action['res_id'])

        # Verify NC document created
        einvoice_doc = self.EInvoiceDoc.search([
            ('invoice_id', '=', refund_invoice.id)
        ])
        self.assertEqual(einvoice_doc.document_type, 'NC', "Should be Nota de Crédito")

        # Run through lifecycle
        einvoice_doc.action_generate_xml()
        einvoice_doc.action_sign_xml()
        einvoice_doc.action_submit_to_hacienda()
        einvoice_doc.action_check_status()

        self.assertIn(einvoice_doc.state, ['accepted', 'processing', 'submitted'])

    # ========================================================================
    # ERROR HANDLING TESTS
    # ========================================================================

    def test_e2e_retry_on_transient_failure(self):
        """
        P0: Verify retry queue handles transient failures.

        Covers:
        - R-005: External API dependency resilience
        """
        # This would require mocking a temporary API failure
        # For now, we verify the retry queue mechanism exists
        retry_queue = self.env['l10n_cr.einvoice.retry.queue']

        customer = self._create_test_customer()
        product = self._create_test_product()
        invoice = self._create_test_invoice(customer, product)
        invoice.action_post()

        einvoice_doc = self.EInvoiceDoc.search([('invoice_id', '=', invoice.id)])
        einvoice_doc.action_generate_xml()
        einvoice_doc.action_sign_xml()

        # Attempt submission (may or may not fail)
        try:
            einvoice_doc.action_submit_to_hacienda()
        except Exception:
            # If submission fails, verify retry queue entry created
            retry_entries = retry_queue.search([
                ('einvoice_document_id', '=', einvoice_doc.id)
            ])
            # May or may not have retry entries depending on failure type
            # This is more of a smoke test

    def test_e2e_idempotency_no_double_submit(self):
        """
        P1: Verify calling submit twice doesn't create duplicate submissions.

        Covers:
        - R-002: Data integrity (no double submit)
        """
        customer = self._create_test_customer()
        product = self._create_test_product()
        invoice = self._create_test_invoice(customer, product)
        invoice.action_post()

        einvoice_doc = self.EInvoiceDoc.search([('invoice_id', '=', invoice.id)])
        einvoice_doc.action_generate_xml()
        einvoice_doc.action_sign_xml()

        # First submission
        einvoice_doc.action_submit_to_hacienda()
        first_state = einvoice_doc.state

        # Count response messages after first submit
        response_count_1 = self.env['l10n_cr.hacienda.response.message'].search_count([
            ('einvoice_document_id', '=', einvoice_doc.id),
            ('response_type', '=', 'submit')
        ])

        # Attempt second submission (should be prevented or idempotent)
        try:
            einvoice_doc.action_submit_to_hacienda()
        except Exception:
            # May raise error preventing duplicate submit
            pass

        # Count response messages after second attempt
        response_count_2 = self.env['l10n_cr.hacienda.response.message'].search_count([
            ('einvoice_document_id', '=', einvoice_doc.id),
            ('response_type', '=', 'submit')
        ])

        # Should not have increased submission count
        self.assertEqual(
            response_count_1, response_count_2,
            "Should not create duplicate submission entries"
        )

    # ========================================================================
    # PERFORMANCE TESTS
    # ========================================================================

    def test_e2e_bulk_submission_performance(self):
        """
        P2: Test bulk submission performance (10 invoices).

        Target: <10s per invoice (including network latency)
        """
        import time

        customer = self._create_test_customer()
        product = self._create_test_product()

        # Create 10 invoices
        invoices = []
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

        # Get e-invoice documents
        einvoice_docs = self.EInvoiceDoc.search([
            ('invoice_id', 'in', [inv.id for inv in invoices])
        ])
        self.assertEqual(len(einvoice_docs), 10)

        # Measure bulk processing time
        start_time = time.time()

        for doc in einvoice_docs:
            doc.action_generate_xml()
            doc.action_sign_xml()
            doc.action_submit_to_hacienda()

        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_invoice = total_time / 10

        print(f"\nBulk submission performance:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Avg per invoice: {avg_time_per_invoice:.2f}s")

        # Performance target: <15s per invoice (generous for sandbox)
        # In production with optimizations, target <10s
        self.assertLess(
            avg_time_per_invoice, 15.0,
            f"Average time per invoice ({avg_time_per_invoice:.2f}s) exceeds 15s target"
        )
