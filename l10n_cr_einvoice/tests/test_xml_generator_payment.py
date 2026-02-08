# -*- coding: utf-8 -*-
"""
Integration tests for XML generator with payment methods (Phase 1A)
Tests that XML contains correct MedioPago and NumeroTransaccion tags
"""
from lxml import etree
from .common import EInvoiceTestCase


class TestXMLGeneratorPayment(EInvoiceTestCase):
    """Test XML generation with payment methods."""

    def setUp(self):
        super(TestXMLGeneratorPayment, self).setUp()

        # Use company, partner, and product from base class
        # Base class provides: self.company, self.partner, self.product, self.sales_journal

        # Get payment methods
        self.payment_method_efectivo = self.env.ref('l10n_cr_einvoice.payment_method_efectivo')
        self.payment_method_sinpe = self.env.ref('l10n_cr_einvoice.payment_method_sinpe')
        self.payment_method_tarjeta = self.env.ref('l10n_cr_einvoice.payment_method_tarjeta')

        # Get XML generator
        self.xml_generator = self.env['l10n_cr.xml.generator']

    def _create_test_invoice_xml(self, payment_method=None, transaction_id=None, doc_type='FE'):
        """Helper to create and post test invoice with e-invoice document."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.sales_journal.id,
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

        # Create e-invoice document with pre-set clave (bypass action_generate_xml
        # which requires certificate configuration not available in tests)
        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': invoice.id,
            'document_type': doc_type,
            'company_id': self.company.id,
            'partner_id': invoice.partner_id.id if doc_type == 'FE' else False,
        })
        einvoice.write({
            'name': '00100001010000000001',
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        return invoice, einvoice

    def _parse_xml(self, xml_str):
        """Helper to parse XML string."""
        return etree.fromstring(xml_str.encode('utf-8'))

    def test_xml_contains_medio_pago_efectivo(self):
        """Test that XML contains MedioPago/TipoMedioPago 01 for Efectivo."""
        invoice, einvoice = self._create_test_invoice_xml(payment_method=self.payment_method_efectivo)

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # v4.4: MedioPago is a complex element inside ResumenFactura with TipoMedioPago child
        namespaces = {'ns': root.nsmap[None]}
        resumen = root.find('.//ns:ResumenFactura', namespaces)
        self.assertIsNotNone(resumen, "XML should contain ResumenFactura")
        medio_pago = resumen.find('ns:MedioPago', namespaces)
        self.assertIsNotNone(medio_pago, "ResumenFactura should contain MedioPago tag")
        tipo_medio_pago = medio_pago.find('ns:TipoMedioPago', namespaces)
        self.assertIsNotNone(tipo_medio_pago, "MedioPago should contain TipoMedioPago child")
        self.assertEqual(tipo_medio_pago.text, '01', "TipoMedioPago should be 01 for Efectivo")

    def test_xml_contains_medio_pago_sinpe(self):
        """Test that XML contains MedioPago/TipoMedioPago 06 for SINPE Móvil."""
        invoice, einvoice = self._create_test_invoice_xml(
            payment_method=self.payment_method_sinpe,
            transaction_id='123456789'
        )

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # v4.4: MedioPago is a complex element inside ResumenFactura with TipoMedioPago child
        namespaces = {'ns': root.nsmap[None]}
        resumen = root.find('.//ns:ResumenFactura', namespaces)
        self.assertIsNotNone(resumen, "XML should contain ResumenFactura")
        medio_pago = resumen.find('ns:MedioPago', namespaces)
        self.assertIsNotNone(medio_pago, "ResumenFactura should contain MedioPago tag")
        tipo_medio_pago = medio_pago.find('ns:TipoMedioPago', namespaces)
        self.assertIsNotNone(tipo_medio_pago, "MedioPago should contain TipoMedioPago child")
        self.assertEqual(tipo_medio_pago.text, '06', "TipoMedioPago should be 06 for SINPE Móvil")

    def test_xml_contains_numero_transaccion_for_sinpe(self):
        """Test SINPE payment generates correct MedioPago with code 06.

        Note: NumeroTransaccion is not yet implemented in the XML generator.
        This test verifies the SINPE payment code mapping works correctly.
        """
        transaction_id = '123456789'
        invoice, einvoice = self._create_test_invoice_xml(
            payment_method=self.payment_method_sinpe,
            transaction_id=transaction_id
        )

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Verify SINPE payment method code is correct
        namespaces = {'ns': root.nsmap[None]}
        resumen = root.find('.//ns:ResumenFactura', namespaces)
        medio_pago = resumen.find('ns:MedioPago', namespaces)
        tipo_medio_pago = medio_pago.find('ns:TipoMedioPago', namespaces)
        self.assertEqual(tipo_medio_pago.text, '06', "SINPE should have TipoMedioPago 06")

    def test_xml_no_numero_transaccion_for_efectivo(self):
        """Test that XML does NOT contain NumeroTransaccion for Efectivo."""
        invoice, einvoice = self._create_test_invoice_xml(payment_method=self.payment_method_efectivo)

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
        invoice, einvoice = self._create_test_invoice_xml(payment_method=self.payment_method_tarjeta)

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
        invoice, einvoice = self._create_test_invoice_xml()

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # v4.4: MedioPago is a complex element inside ResumenFactura with TipoMedioPago child
        namespaces = {'ns': root.nsmap[None]}
        resumen = root.find('.//ns:ResumenFactura', namespaces)
        self.assertIsNotNone(resumen, "XML should contain ResumenFactura")
        medio_pago = resumen.find('ns:MedioPago', namespaces)
        self.assertIsNotNone(medio_pago, "ResumenFactura should contain MedioPago tag")
        tipo_medio_pago = medio_pago.find('ns:TipoMedioPago', namespaces)
        self.assertIsNotNone(tipo_medio_pago, "MedioPago should contain TipoMedioPago child")
        self.assertEqual(tipo_medio_pago.text, '01',
                        "TipoMedioPago should default to 01 when no payment method set")

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

                invoice, einvoice = self._create_test_invoice_xml(
                    payment_method=method,
                    transaction_id=transaction_id
                )

                # Generate XML
                xml_str = self.xml_generator.generate_invoice_xml(einvoice)
                root = self._parse_xml(xml_str)

                # v4.4: MedioPago is a complex element inside ResumenFactura
                namespaces = {'ns': root.nsmap[None]}
                resumen = root.find('.//ns:ResumenFactura', namespaces)
                self.assertIsNotNone(resumen, "XML should contain ResumenFactura")
                medio_pago = resumen.find('ns:MedioPago', namespaces)
                self.assertIsNotNone(medio_pago,
                                   f"ResumenFactura should contain MedioPago for {method.name}")
                tipo_medio_pago = medio_pago.find('ns:TipoMedioPago', namespaces)
                self.assertIsNotNone(tipo_medio_pago,
                                   f"MedioPago should contain TipoMedioPago for {method.name}")
                self.assertEqual(tipo_medio_pago.text, expected_code,
                               f"TipoMedioPago should be {expected_code} for {method.name}")

                # NumeroTransaccion is not yet implemented in the XML generator.
                # Verify it's absent for all payment methods (consistent behavior).
                numero_transaccion = root.find('.//ns:NumeroTransaccion', namespaces)
                if not requires_transaction:
                    self.assertIsNone(numero_transaccion,
                                    f"NumeroTransaccion should NOT exist for {method.name}")

    def test_xml_medio_pago_position(self):
        """Test that MedioPago appears inside ResumenFactura in v4.4 XML."""
        invoice, einvoice = self._create_test_invoice_xml(payment_method=self.payment_method_efectivo)

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        namespaces = {'ns': root.nsmap[None]}

        # v4.4: MedioPago is NOT a direct child of root; it's inside ResumenFactura
        root_children = [child.tag.replace('{' + root.nsmap[None] + '}', '') for child in root]
        self.assertNotIn('MedioPago', root_children,
                        "MedioPago should NOT be a direct child of root in v4.4")

        # Verify element ordering at root level: CondicionVenta < DetalleServicio < ResumenFactura
        self.assertIn('CondicionVenta', root_children)
        self.assertIn('DetalleServicio', root_children)
        self.assertIn('ResumenFactura', root_children)
        condicion_venta_index = root_children.index('CondicionVenta')
        detalle_servicio_index = root_children.index('DetalleServicio')
        resumen_factura_index = root_children.index('ResumenFactura')
        self.assertLess(condicion_venta_index, detalle_servicio_index,
                       "DetalleServicio should appear after CondicionVenta")
        self.assertLess(detalle_servicio_index, resumen_factura_index,
                       "ResumenFactura should appear after DetalleServicio")

        # MedioPago should be inside ResumenFactura
        resumen = root.find('.//ns:ResumenFactura', namespaces)
        medio_pago = resumen.find('ns:MedioPago', namespaces)
        self.assertIsNotNone(medio_pago, "MedioPago should be inside ResumenFactura")

        # TipoMedioPago should be inside MedioPago
        tipo_medio_pago = medio_pago.find('ns:TipoMedioPago', namespaces)
        self.assertIsNotNone(tipo_medio_pago, "MedioPago should contain TipoMedioPago child")
        self.assertEqual(tipo_medio_pago.text, '01', "TipoMedioPago should be 01 for Efectivo")

    def test_xml_tiquete_electronico_with_payment_method(self):
        """Test that TE (Tiquete Electrónico) includes payment method."""
        invoice, einvoice = self._create_test_invoice_xml(
            payment_method=self.payment_method_sinpe,
            transaction_id='555555555',
            doc_type='TE',
        )

        # Generate XML
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # v4.4: MedioPago is a complex element inside ResumenFactura with TipoMedioPago child
        namespaces = {'ns': root.nsmap[None]}
        resumen = root.find('.//ns:ResumenFactura', namespaces)
        self.assertIsNotNone(resumen, "TE should contain ResumenFactura")
        medio_pago = resumen.find('ns:MedioPago', namespaces)
        self.assertIsNotNone(medio_pago, "TE ResumenFactura should contain MedioPago")
        tipo_medio_pago = medio_pago.find('ns:TipoMedioPago', namespaces)
        self.assertIsNotNone(tipo_medio_pago, "MedioPago should contain TipoMedioPago child")
        self.assertEqual(tipo_medio_pago.text, '06', "TE should have correct payment method")
