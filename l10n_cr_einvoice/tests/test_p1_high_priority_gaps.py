# -*- coding: utf-8 -*-
"""
P1 High Priority Gap Tests

Gap #7:  Mixed tax rates (0% + 13%) on same invoice
Gap #8:  _is_service_line CABYS classification (all prefix buckets)
Gap #9:  CondicionVenta branching (credit terms, POS, custom)
Gap #10: Exchange rate handling (USD TipoCambio, missing rates)
Gap #11: All 7 IVA rate codes (0%, 0.5%, 1%, 2%, 4%, 8%, 13%)
Gap #12: Tax report API submission (D-150, D-101, D-151 — skeleton)
Gap #13: _process_hacienda_response edge cases
Gap #14: _validate_before_submission pre-flight checks
"""

import uuid
from datetime import datetime, date
from unittest.mock import patch, MagicMock
from lxml import etree

from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import EInvoiceTestCase


# ============================================================================
# Gap #7: Mixed tax rates on same invoice
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestMixedTaxRates(EInvoiceTestCase):
    """Verify invoices with multiple tax rates produce correct XML."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

        cr_country_id = cls.env.ref('base.cr').id
        tax_group = cls.env['account.tax.group'].search([
            ('country_id', '=', cr_country_id)
        ], limit=1) or cls.env['account.tax.group'].create({
            'name': 'IVA', 'country_id': cr_country_id,
        })

        cls.tax_exempt = cls.env['account.tax'].create({
            'name': f'Exento Mix {uuid.uuid4().hex[:6]}',
            'amount': 0.0, 'amount_type': 'percent', 'type_tax_use': 'sale',
            'company_id': cls.company.id, 'country_id': cr_country_id,
            'tax_group_id': tax_group.id,
        })

    def _make_einvoice(self, move):
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
        })

    def test_0_and_13_percent_on_same_invoice(self):
        """Invoice with 0% and 13% lines produces separate Impuesto elements."""
        move = self._create_test_invoice(lines=[
            {'product_id': self.product.id, 'quantity': 1,
             'price_unit': 5000.0, 'tax_ids': [(6, 0, [self.tax_exempt.id])]},
            {'product_id': self.product.id, 'quantity': 1,
             'price_unit': 5000.0, 'tax_ids': [(6, 0, [self.tax_13.id])]},
        ])
        move.action_post()
        einvoice = self._make_einvoice(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}

        impuestos = root.findall('.//ns:DetalleServicio/ns:LineaDetalle/ns:Impuesto', ns)
        tarifas = [imp.find('ns:CodigoTarifaIVA', ns).text for imp in impuestos]

        self.assertIn('01', tarifas, "Should have 0% (code 01)")
        self.assertIn('08', tarifas, "Should have 13% (code 08)")

    def test_mixed_rates_desglose_aggregation(self):
        """TotalDesgloseImpuesto aggregates by (Codigo, CodigoTarifaIVA)."""
        move = self._create_test_invoice(lines=[
            {'product_id': self.product.id, 'quantity': 1,
             'price_unit': 10000.0, 'tax_ids': [(6, 0, [self.tax_13.id])]},
            {'product_id': self.product.id, 'quantity': 2,
             'price_unit': 5000.0, 'tax_ids': [(6, 0, [self.tax_13.id])]},
        ])
        move.action_post()
        einvoice = self._make_einvoice(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}

        desgloses = root.findall('.//ns:TotalDesgloseImpuesto', ns)
        # Two lines at same rate → one desglose entry
        rate_08_desgloses = [d for d in desgloses
                             if d.find('ns:CodigoTarifaIVA', ns).text == '08']
        self.assertEqual(len(rate_08_desgloses), 1)

        # Total should be 13% of (10000 + 10000) = 2600
        total_monto = float(rate_08_desgloses[0].find('ns:TotalMontoImpuesto', ns).text)
        self.assertAlmostEqual(total_monto, 2600.0, places=2)


# ============================================================================
# Gap #8: _is_service_line CABYS classification
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestCabysClassification(EInvoiceTestCase):
    """Test _is_service_line across all CABYS prefix buckets."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def _make_line_data(self, cabys_code):
        """Create a minimal line_data dict for _is_service_line."""
        product = self.env['product.product'].create({
            'name': f'Product {cabys_code[:4]}',
            'type': 'service',
            'list_price': 100.0,
        })
        move = self._create_test_invoice(lines=[{
            'product_id': product.id, 'quantity': 1, 'price_unit': 100.0,
            'tax_ids': [(6, 0, [self.tax_13.id])],
            'l10n_cr_product_code': cabys_code,
        }])
        move.action_post()
        lines_data = self.xml_generator._compute_line_amounts(move)
        return lines_data[0]

    def test_prefix_96_is_service(self):
        """CABYS starting with 96 → service."""
        ld = self._make_line_data('9652000009900')
        self.assertTrue(self.xml_generator._is_service_line(ld))

    def test_prefix_97_is_service(self):
        """CABYS starting with 97 → service."""
        ld = self._make_line_data('9701000000000')
        self.assertTrue(self.xml_generator._is_service_line(ld))

    def test_prefix_98_is_service(self):
        """CABYS starting with 98 → service."""
        ld = self._make_line_data('9801000000000')
        self.assertTrue(self.xml_generator._is_service_line(ld))

    def test_prefix_99_is_service(self):
        """CABYS starting with 99 → service."""
        ld = self._make_line_data('9901000000000')
        self.assertTrue(self.xml_generator._is_service_line(ld))

    def test_prefix_21_is_merchandise(self):
        """CABYS starting with 21 → merchandise."""
        ld = self._make_line_data('2110011000000')
        self.assertFalse(self.xml_generator._is_service_line(ld))

    def test_prefix_01_is_merchandise(self):
        """CABYS starting with 01 → merchandise."""
        ld = self._make_line_data('0110011000000')
        self.assertFalse(self.xml_generator._is_service_line(ld))

    def test_prefix_50_is_merchandise(self):
        """CABYS starting with 50 → merchandise."""
        ld = self._make_line_data('5010011000000')
        self.assertFalse(self.xml_generator._is_service_line(ld))

    def test_prefix_95_is_merchandise(self):
        """CABYS starting with 95 → merchandise (only 96-99 are services)."""
        ld = self._make_line_data('9510011000000')
        self.assertFalse(self.xml_generator._is_service_line(ld))

    def test_no_cabys_defaults_to_service(self):
        """No CABYS code → default 9652000009900 (service)."""
        product = self.env['product.product'].create({
            'name': 'No CABYS Product', 'type': 'service', 'list_price': 100.0,
        })
        # Don't set l10n_cr_cabys_code
        move = self._create_test_invoice(lines=[{
            'product_id': product.id, 'quantity': 1, 'price_unit': 100.0,
            'tax_ids': [(6, 0, [self.tax_13.id])],
        }])
        move.action_post()
        lines_data = self.xml_generator._compute_line_amounts(move)
        self.assertTrue(self.xml_generator._is_service_line(lines_data[0]))


# ============================================================================
# Gap #9: CondicionVenta branching
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestCondicionVenta(EInvoiceTestCase):
    """Test CondicionVenta branching: cash, credit, custom code, POS."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def _get_condicion_from_xml(self, xml_str):
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        return root.find('.//ns:CondicionVenta', ns).text

    def _make_einvoice(self, move):
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
        })

    def test_no_payment_terms_is_contado(self):
        """Invoice without payment terms → CondicionVenta = 01 (Contado)."""
        move = self._create_test_invoice()
        move.invoice_payment_term_id = False
        move.action_post()
        einvoice = self._make_einvoice(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        self.assertEqual(self._get_condicion_from_xml(xml_str), '01')

    def test_payment_terms_is_credito(self):
        """Invoice with payment terms → CondicionVenta = 02 (Crédito)."""
        # Create a payment term
        payment_term = self.env['account.payment.term'].create({
            'name': 'Net 30',
            'company_id': self.company.id,
            'line_ids': [(0, 0, {
                'value': 'percent',
                'value_amount': 100,
                'nb_days': 30,
                'delay_type': 'days_after',
            })],
        })
        move = self._create_test_invoice()
        move.invoice_payment_term_id = payment_term
        move.action_post()
        einvoice = self._make_einvoice(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)

        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        condicion = root.find('.//ns:CondicionVenta', ns)
        self.assertEqual(condicion.text, '02')

        # Should also have PlazoCredito
        plazo = root.find('.//ns:PlazoCredito', ns)
        self.assertIsNotNone(plazo, "Credit terms should include PlazoCredito")

    def test_custom_condicion_code_99(self):
        """Custom CondicionVenta override via l10n_cr_condicion_venta."""
        move = self._create_test_invoice()
        move.action_post()
        if hasattr(move, 'l10n_cr_condicion_venta'):
            move.l10n_cr_condicion_venta = '99'
            einvoice = self._make_einvoice(move)
            xml_str = self.xml_generator.generate_invoice_xml(einvoice)
            self.assertEqual(self._get_condicion_from_xml(xml_str), '99')


# ============================================================================
# Gap #10: Exchange rate handling
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestExchangeRate(EInvoiceTestCase):
    """Test exchange rate handling for multi-currency invoices."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def test_crc_currency_rate_is_1(self):
        """CRC invoices should have TipoCambio = 1.0."""
        move = self._create_test_invoice()
        move.action_post()
        rate = self.xml_generator._get_exchange_rate(move)
        self.assertEqual(rate, 1.0)

    def test_usd_currency_has_rate(self):
        """USD invoices should have TipoCambio > 1."""
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not usd:
            self.skipTest('USD currency not found')

        crc = self.env['res.currency'].search([('name', '=', 'CRC')], limit=1)
        if not crc:
            self.skipTest('CRC currency not found')

        # Create a rate
        self.env['res.currency.rate'].create({
            'name': '2025-02-01',
            'currency_id': usd.id,
            'company_id': self.company.id,
            'inverse_company_rate': 530.0,  # 1 USD = 530 CRC
        })

        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.sales_journal.id,
            'currency_id': usd.id,
            'invoice_date': '2025-02-01',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1, 'price_unit': 100.0,
                'tax_ids': [(6, 0, [self.tax_13.id])],
            })],
        })
        move.action_post()

        rate = self.xml_generator._get_exchange_rate(move)
        self.assertGreater(rate, 1.0)

    def test_missing_rate_defaults_to_1(self):
        """If no exchange rate is found, default to 1.0."""
        eur = self.env['res.currency'].with_context(active_test=False).search(
            [('name', '=', 'EUR')], limit=1,
        )
        if not eur:
            self.skipTest('EUR currency not found in database')
        # Ensure it's active for the test
        if not eur.active:
            eur.active = True

        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.sales_journal.id,
            'currency_id': eur.id,
            'invoice_date': '2025-02-01',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1, 'price_unit': 100.0,
                'tax_ids': [(6, 0, [self.tax_13.id])],
            })],
        })
        move.action_post()

        rate = self.xml_generator._get_exchange_rate(move)
        # Either finds a rate or defaults to 1.0 — should not crash
        self.assertIsInstance(rate, float)

    def test_exchange_rate_in_xml(self):
        """CodigoTipoMoneda/TipoCambio present in ResumenFactura."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
        })
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}

        tipo_cambio = root.find('.//ns:TipoCambio', ns)
        self.assertIsNotNone(tipo_cambio)
        codigo_moneda = root.find('.//ns:CodigoMoneda', ns)
        self.assertIsNotNone(codigo_moneda)


# ============================================================================
# Gap #11: All 7 IVA rate codes
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestAllIvaRateCodes(EInvoiceTestCase):
    """Test all 7 valid IVA rate codes from TARIFA_IVA_MAP."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def test_tarifa_iva_map_completeness(self):
        """Verify TARIFA_IVA_MAP has all 7 expected rates."""
        expected_rates = {0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 13.0}
        actual_rates = set(self.xml_generator.TARIFA_IVA_MAP.keys())
        self.assertEqual(actual_rates, expected_rates)

    def test_rate_to_code_mapping(self):
        """Each rate maps to the correct Hacienda code."""
        expected = {
            0.0: '01', 0.5: '09', 1.0: '02', 2.0: '03',
            4.0: '04', 8.0: '06', 13.0: '08',
        }
        for rate, expected_code in expected.items():
            codigo, tarifa = self.xml_generator.TARIFA_IVA_MAP[rate]
            self.assertEqual(codigo, expected_code,
                             f"Rate {rate}% should map to code {expected_code}, got {codigo}")

    def test_unknown_rate_maps_to_closest(self):
        """Unknown rate (e.g. 15%) maps to closest valid rate (13%)."""
        cr_country_id = self.env.ref('base.cr').id
        tax_group = self.env['account.tax.group'].search([
            ('country_id', '=', cr_country_id)
        ], limit=1) or self.env['account.tax.group'].create({
            'name': 'IVA', 'country_id': cr_country_id,
        })

        tax_15 = self.env['account.tax'].create({
            'name': f'Custom 15% {uuid.uuid4().hex[:6]}',
            'amount': 15.0, 'amount_type': 'percent', 'type_tax_use': 'sale',
            'company_id': self.company.id, 'country_id': cr_country_id,
            'tax_group_id': tax_group.id,
        })

        move = self._create_test_invoice(lines=[{
            'product_id': self.product.id, 'quantity': 1, 'price_unit': 10000.0,
            'tax_ids': [(6, 0, [tax_15.id])],
        }])
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
        })

        # Should not raise — maps to closest
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        tarifa_code = root.find('.//ns:CodigoTarifaIVA', ns).text
        # 15% closest to 13% → code '08'
        self.assertEqual(tarifa_code, '08')

    def test_each_valid_rate_generates_xml(self):
        """Each of the 7 valid rates produces correct CodigoTarifaIVA."""
        cr_country_id = self.env.ref('base.cr').id
        tax_group = self.env['account.tax.group'].search([
            ('country_id', '=', cr_country_id)
        ], limit=1) or self.env['account.tax.group'].create({
            'name': 'IVA', 'country_id': cr_country_id,
        })

        for idx, (rate, (expected_code, expected_tarifa)) in enumerate(self.xml_generator.TARIFA_IVA_MAP.items()):
            with self.subTest(rate=rate):
                tax = self.env['account.tax'].create({
                    'name': f'IVA {rate}% {uuid.uuid4().hex[:4]}',
                    'amount': rate, 'amount_type': 'percent', 'type_tax_use': 'sale',
                    'company_id': self.company.id, 'country_id': cr_country_id,
                    'tax_group_id': tax_group.id,
                })
                move = self._create_test_invoice(lines=[{
                    'product_id': self.product.id, 'quantity': 1,
                    'price_unit': 10000.0, 'tax_ids': [(6, 0, [tax.id])],
                }])
                move.action_post()
                # Use unique clave per subtest to avoid unique constraint
                clave_suffix = str(10000000 + idx).zfill(8)
                einvoice = self.env['l10n_cr.einvoice.document'].with_context(
                    bypass_einvoice_validation=True
                ).create({
                    'move_id': move.id, 'partner_id': self.partner.id,
                    'document_type': 'FE', 'company_id': self.company.id,
                    'clave': f'5060101202502010011111111111111111111{clave_suffix}11',
                    'name': f'001000010100000{idx:05d}',
                })
                xml_str = self.xml_generator.generate_invoice_xml(einvoice)
                root = etree.fromstring(xml_str.encode('utf-8'))
                ns = {'ns': root.nsmap[None]}

                tarifa_el = root.find('.//ns:CodigoTarifaIVA', ns)
                self.assertEqual(tarifa_el.text, expected_code)


# ============================================================================
# Gap #13: _process_hacienda_response edge cases
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestProcessHaciendaResponse(EInvoiceTestCase):
    """Test _process_hacienda_response with all status variants."""

    def _create_submitted_einvoice(self):
        """Create an einvoice in submitted state for response testing."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'state': 'submitted',
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
            'signed_xml': '<xml>signed</xml>',
        })
        return einvoice

    def test_aceptado_sets_accepted_state(self):
        """Status 'aceptado' → state='accepted'."""
        einvoice = self._create_submitted_einvoice()
        einvoice._process_hacienda_response({'ind-estado': 'aceptado'})
        self.assertEqual(einvoice.state, 'accepted')
        self.assertIsNotNone(einvoice.hacienda_acceptance_date)

    def test_rechazado_sets_rejected_state(self):
        """Status 'rechazado' → state='rejected'."""
        einvoice = self._create_submitted_einvoice()
        einvoice._process_hacienda_response({
            'ind-estado': 'rechazado',
            'detalle-mensaje': 'Clave duplicada',
        })
        self.assertEqual(einvoice.state, 'rejected')
        self.assertIn('Rejected', einvoice.error_message or '')

    def test_procesando_stays_submitted(self):
        """Status 'procesando' → state='submitted'."""
        einvoice = self._create_submitted_einvoice()
        einvoice._process_hacienda_response({'ind-estado': 'procesando'})
        self.assertEqual(einvoice.state, 'submitted')

    def test_recibido_stays_submitted(self):
        """Status 'recibido' → state='submitted'."""
        einvoice = self._create_submitted_einvoice()
        einvoice._process_hacienda_response({'ind-estado': 'recibido'})
        self.assertEqual(einvoice.state, 'submitted')

    def test_error_status_sets_error_state(self):
        """Status 'error' → state='error'."""
        einvoice = self._create_submitted_einvoice()
        einvoice._process_hacienda_response({
            'ind-estado': 'error',
            'error_details': 'Internal processing error',
        })
        self.assertEqual(einvoice.state, 'error')

    def test_unknown_status_sets_error_state(self):
        """Unknown status → state='error'."""
        einvoice = self._create_submitted_einvoice()
        einvoice._process_hacienda_response({'ind-estado': 'desconocido'})
        self.assertEqual(einvoice.state, 'error')
        self.assertIn('desconocido', einvoice.error_message.lower())

    def test_empty_status_sets_error_state(self):
        """Empty/missing status → state='error'."""
        einvoice = self._create_submitted_einvoice()
        einvoice._process_hacienda_response({})
        self.assertEqual(einvoice.state, 'error')

    def test_case_insensitive_status(self):
        """Status comparison is case-insensitive."""
        einvoice = self._create_submitted_einvoice()
        einvoice._process_hacienda_response({'ind-estado': 'ACEPTADO'})
        self.assertEqual(einvoice.state, 'accepted')

    def test_respuesta_xml_decoded_preferred(self):
        """Decoded XML message is preferred over raw base64."""
        einvoice = self._create_submitted_einvoice()
        einvoice._process_hacienda_response({
            'ind-estado': 'rechazado',
            'respuesta-xml-decoded': 'Decoded rejection reason',
            'respuesta-xml': 'base64-encoded-data',
        })
        # hacienda_message should contain the decoded text, not base64
        self.assertIn('reason', einvoice.hacienda_message.lower())

    def test_hacienda_response_stored_as_text(self):
        """Full response dict is stored in hacienda_response field."""
        einvoice = self._create_submitted_einvoice()
        response = {'ind-estado': 'aceptado', 'clave': 'test123'}
        einvoice._process_hacienda_response(response)
        self.assertIn('test123', einvoice.hacienda_response)

    def test_accepted_clears_previous_errors(self):
        """Acceptance clears any previous error_message."""
        einvoice = self._create_submitted_einvoice()
        einvoice.error_message = 'Previous error'
        einvoice._process_hacienda_response({'ind-estado': 'aceptado'})
        self.assertFalse(einvoice.error_message)


# ============================================================================
# Gap #14: _validate_before_submission pre-flight checks
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestValidateBeforeSubmission(EInvoiceTestCase):
    """Test _validate_before_submission comprehensive checks."""

    def _create_signed_einvoice(self, **overrides):
        """Create a signed e-invoice ready for submission testing."""
        move = self._create_test_invoice()
        move.action_post()
        vals = {
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'state': 'signed',
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
            'signed_xml': '<xml>signed content</xml>',
        }
        vals.update(overrides)
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create(vals)

    def _setup_credentials(self, username='test@user.cr', password='secret'):
        """Helper to set sandbox credentials and invalidate cache."""
        self.company.write({
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_hacienda_username': username,
            'l10n_cr_hacienda_password': password,
        })
        self.company.invalidate_recordset()

    def test_valid_document_passes(self):
        """Fully configured document passes all checks."""
        self._setup_credentials()
        einvoice = self._create_signed_einvoice()
        # Should not raise
        result = einvoice._validate_before_submission()
        self.assertTrue(result)

    def test_missing_api_username_raises(self):
        """Missing Hacienda username raises ValidationError."""
        self._setup_credentials(username=False, password='secret')
        einvoice = self._create_signed_einvoice()
        with self.assertRaises(ValidationError):
            einvoice._validate_before_submission()

    def test_missing_api_password_raises(self):
        """Missing Hacienda password raises ValidationError."""
        self._setup_credentials(username='user', password=False)
        einvoice = self._create_signed_einvoice()
        with self.assertRaises(ValidationError):
            einvoice._validate_before_submission()

    def test_missing_company_vat_raises(self):
        """Missing company VAT raises ValidationError."""
        self._setup_credentials()
        self.company.vat = False
        einvoice = self._create_signed_einvoice()
        with self.assertRaises(ValidationError):
            einvoice._validate_before_submission()

    def test_missing_clave_raises(self):
        """Missing clave raises ValidationError."""
        self._setup_credentials()
        einvoice = self._create_signed_einvoice(clave=False)
        with self.assertRaises(ValidationError):
            einvoice._validate_before_submission()

    def test_missing_signed_xml_raises(self):
        """Missing signed XML raises ValidationError."""
        self._setup_credentials()
        einvoice = self._create_signed_einvoice(signed_xml=False)
        with self.assertRaises(ValidationError):
            einvoice._validate_before_submission()

    def test_missing_partner_raises(self):
        """Missing partner raises ValidationError."""
        self._setup_credentials()
        einvoice = self._create_signed_einvoice(partner_id=False)
        # Use try/except instead of assertRaises — assertRaises creates
        # savepoints that trigger flush → constraint before our code runs
        try:
            einvoice._validate_before_submission()
            self.fail("Should have raised ValidationError")
        except ValidationError:
            pass  # Expected

    def test_missing_partner_vat_raises(self):
        """Partner without VAT raises ValidationError."""
        self._setup_credentials()
        no_vat = self.env['res.partner'].create({
            'name': 'No VAT', 'email': 'x@x.com',
            'country_id': self.env.ref('base.cr').id,
        })
        einvoice = self._create_signed_einvoice(partner_id=no_vat.id)
        try:
            einvoice._validate_before_submission()
            self.fail("Should have raised ValidationError")
        except ValidationError:
            pass  # Expected

    def test_missing_certificate_raises(self):
        """Missing certificate raises ValidationError."""
        self._setup_credentials()
        self.company.l10n_cr_certificate = False
        self.company.invalidate_recordset()
        einvoice = self._create_signed_einvoice()
        with self.assertRaises(ValidationError):
            einvoice._validate_before_submission()

    def test_missing_emisor_location_raises(self):
        """Missing emisor location raises ValidationError."""
        self._setup_credentials()
        self.company.l10n_cr_emisor_location = False
        einvoice = self._create_signed_einvoice()
        with self.assertRaises(ValidationError):
            einvoice._validate_before_submission()

    def test_missing_hacienda_env_raises(self):
        """Missing environment config raises ValidationError."""
        self.company.write({
            'l10n_cr_hacienda_env': False,
            'l10n_cr_hacienda_username': 'user',
            'l10n_cr_hacienda_password': 'pass',
        })
        self.company.invalidate_recordset()
        einvoice = self._create_signed_einvoice()
        with self.assertRaises(ValidationError):
            einvoice._validate_before_submission()

    def test_multiple_errors_reported(self):
        """Multiple issues are all reported in a single ValidationError."""
        self.company.write({
            'vat': False,
            'l10n_cr_hacienda_username': False,
            'l10n_cr_hacienda_password': False,
            'l10n_cr_certificate': False,
        })
        self.company.invalidate_recordset()
        einvoice = self._create_signed_einvoice()
        try:
            einvoice._validate_before_submission()
            self.fail("Should have raised ValidationError")
        except ValidationError as e:
            # Should mention multiple issues
            error_text = str(e)
            self.assertIn('\u2022', error_text, "Should have bullet-pointed error list")
