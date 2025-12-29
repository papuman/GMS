# -*- coding: utf-8 -*-
"""
Integration tests for XML generator with payment methods (Phase 1A)
Tests that XML contains correct MedioPago and NumeroTransaccion tags
"""
from odoo.tests import TransactionCase
from lxml import etree


class TestXMLGeneratorPayment(TransactionCase):
    """Test XML generation with payment methods."""

    def setUp(self):
        super(TestXMLGeneratorPayment, self).setUp()

        # Create test company in Costa Rica
        self.company = self.env['res.company'].create({
            'name': 'Test Company CR',
            'country_id': self.env.ref('base.cr').id,
            'vat': '3101234567',
            'email': 'test@example.com',
            'phone': '22001100',
        })

        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'country_id': self.env.ref('base.cr').id,
            'vat': '123456789',
            'email': 'customer@example.com',
        })

        # Get payment methods
        self.payment_method_efectivo = self.env.ref('l10n_cr_einvoice.payment_method_efectivo')
        self.payment_method_sinpe = self.env.ref('l10n_cr_einvoice.payment_method_sinpe')
        self.payment_method_tarjeta = self.env.ref('l10n_cr_einvoice.payment_method_tarjeta')

        # Create test product
        self.product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'list_price': 10000.0,
        })

        # Get XML generator
        self.xml_generator = self.env['l10n_cr.xml.generator']

    def _create_test_invoice(self, payment_method=None, transaction_id=None):
        """Helper to create and post test invoice with e-invoice document."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'invoice_date': '2025-12-28',
            'l10n_cr_payment_method_id': payment_method.id if payment_method else False,
            'l10n_cr_payment_transaction_id': transaction_id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 10000.0,
            })],
        })
        invoice.action_post()

        # Create e-invoice document
        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': invoice.id,
            'document_type': 'FE',
            'company_id': self.company.id,
        })

        return invoice, einvoice

    def _parse_xml(self, xml_str):
        """Helper to parse XML string."""
        return etree.fromstring(xml_str.encode('utf-8'))

    def test_xml_contains_medio_pago_efectivo(self):
        """Test that XML contains MedioPago 01 for Efectivo."""
        invoice, einvoice = self._create_test_invoice(payment_method=self.payment_method_efectivo)

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Find MedioPago tag
        namespaces = {'ns': root.nsmap[None]}
        medio_pago = root.find('.//ns:MedioPago', namespaces)

        self.assertIsNotNone(medio_pago, "XML should contain MedioPago tag")
        self.assertEqual(medio_pago.text, '01', "MedioPago should be 01 for Efectivo")

    def test_xml_contains_medio_pago_sinpe(self):
        """Test that XML contains MedioPago 06 for SINPE Móvil."""
        invoice, einvoice = self._create_test_invoice(
            payment_method=self.payment_method_sinpe,
            transaction_id='123456789'
        )

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Find MedioPago tag
        namespaces = {'ns': root.nsmap[None]}
        medio_pago = root.find('.//ns:MedioPago', namespaces)

        self.assertIsNotNone(medio_pago, "XML should contain MedioPago tag")
        self.assertEqual(medio_pago.text, '06', "MedioPago should be 06 for SINPE Móvil")

    def test_xml_contains_numero_transaccion_for_sinpe(self):
        """Test that XML contains NumeroTransaccion for SINPE Móvil."""
        transaction_id = '123456789'
        invoice, einvoice = self._create_test_invoice(
            payment_method=self.payment_method_sinpe,
            transaction_id=transaction_id
        )

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Find NumeroTransaccion tag
        namespaces = {'ns': root.nsmap[None]}
        numero_transaccion = root.find('.//ns:NumeroTransaccion', namespaces)

        self.assertIsNotNone(numero_transaccion, "XML should contain NumeroTransaccion tag for SINPE")
        self.assertEqual(numero_transaccion.text, transaction_id,
                        f"NumeroTransaccion should be {transaction_id}")

    def test_xml_no_numero_transaccion_for_efectivo(self):
        """Test that XML does NOT contain NumeroTransaccion for Efectivo."""
        invoice, einvoice = self._create_test_invoice(payment_method=self.payment_method_efectivo)

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Find NumeroTransaccion tag (should not exist)
        namespaces = {'ns': root.nsmap[None]}
        numero_transaccion = root.find('.//ns:NumeroTransaccion', namespaces)

        self.assertIsNone(numero_transaccion,
                         "XML should NOT contain NumeroTransaccion tag for Efectivo")

    def test_xml_no_numero_transaccion_for_tarjeta(self):
        """Test that XML does NOT contain NumeroTransaccion for Tarjeta."""
        invoice, einvoice = self._create_test_invoice(payment_method=self.payment_method_tarjeta)

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Find NumeroTransaccion tag (should not exist)
        namespaces = {'ns': root.nsmap[None]}
        numero_transaccion = root.find('.//ns:NumeroTransaccion', namespaces)

        self.assertIsNone(numero_transaccion,
                         "XML should NOT contain NumeroTransaccion tag for Tarjeta")

    def test_xml_default_efectivo_when_no_payment_method(self):
        """Test that XML defaults to Efectivo (01) when no payment method set."""
        # Create invoice without payment method (will auto-assign on post)
        invoice, einvoice = self._create_test_invoice()

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Find MedioPago tag
        namespaces = {'ns': root.nsmap[None]}
        medio_pago = root.find('.//ns:MedioPago', namespaces)

        self.assertIsNotNone(medio_pago, "XML should contain MedioPago tag")
        self.assertEqual(medio_pago.text, '01',
                        "MedioPago should default to 01 when no payment method set")

    def test_xml_all_payment_methods(self):
        """Test XML generation for all 5 payment methods."""
        payment_methods = [
            ('l10n_cr_einvoice.payment_method_efectivo', '01', False),
            ('l10n_cr_einvoice.payment_method_tarjeta', '02', False),
            ('l10n_cr_einvoice.payment_method_cheque', '03', False),
            ('l10n_cr_einvoice.payment_method_transferencia', '04', False),
            ('l10n_cr_einvoice.payment_method_sinpe', '06', True),
        ]

        for method_ref, expected_code, requires_transaction in payment_methods:
            with self.subTest(payment_method=method_ref):
                method = self.env.ref(method_ref)
                transaction_id = '987654321' if requires_transaction else None

                invoice, einvoice = self._create_test_invoice(
                    payment_method=method,
                    transaction_id=transaction_id
                )

                # Generate XML
                xml_str = self.xml_generator.generate_invoice_xml(einvoice)
                root = self._parse_xml(xml_str)

                # Check MedioPago
                namespaces = {'ns': root.nsmap[None]}
                medio_pago = root.find('.//ns:MedioPago', namespaces)
                self.assertEqual(medio_pago.text, expected_code,
                               f"MedioPago should be {expected_code} for {method.name}")

                # Check NumeroTransaccion
                numero_transaccion = root.find('.//ns:NumeroTransaccion', namespaces)
                if requires_transaction:
                    self.assertIsNotNone(numero_transaccion,
                                       f"NumeroTransaccion should exist for {method.name}")
                    self.assertEqual(numero_transaccion.text, transaction_id)
                else:
                    self.assertIsNone(numero_transaccion,
                                    f"NumeroTransaccion should NOT exist for {method.name}")

    def test_xml_medio_pago_position(self):
        """Test that MedioPago appears in correct position in XML."""
        invoice, einvoice = self._create_test_invoice(payment_method=self.payment_method_efectivo)

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Get all child elements
        namespaces = {'ns': root.nsmap[None]}
        children = [child.tag.replace('{' + root.nsmap[None] + '}', '') for child in root]

        # MedioPago should appear after CondicionVenta and before DetalleServicio
        self.assertIn('MedioPago', children, "XML should contain MedioPago")
        condicion_venta_index = children.index('CondicionVenta')
        medio_pago_index = children.index('MedioPago')
        detalle_servicio_index = children.index('DetalleServicio')

        self.assertLess(condicion_venta_index, medio_pago_index,
                       "MedioPago should appear after CondicionVenta")
        self.assertLess(medio_pago_index, detalle_servicio_index,
                       "MedioPago should appear before DetalleServicio")

    def test_xml_tiquete_electronico_with_payment_method(self):
        """Test that TE (Tiquete Electrónico) includes payment method."""
        # Create small invoice (below threshold for TE)
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'invoice_date': '2025-12-28',
            'l10n_cr_payment_method_id': self.payment_method_sinpe.id,
            'l10n_cr_payment_transaction_id': '555555555',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 500.0,  # Small amount for TE
            })],
        })
        invoice.action_post()

        # Create e-invoice as TE
        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': invoice.id,
            'document_type': 'TE',
            'company_id': self.company.id,
        })

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Check MedioPago exists in TE
        namespaces = {'ns': root.nsmap[None]}
        medio_pago = root.find('.//ns:MedioPago', namespaces)
        self.assertIsNotNone(medio_pago, "TE should contain MedioPago")
        self.assertEqual(medio_pago.text, '06', "TE should have correct payment method")
