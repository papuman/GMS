# -*- coding: utf-8 -*-
"""
P0 Critical Gap Tests — Must Pass Before Production

Gap #1: ResumenFactura 6-way classification (service/merch x taxed/exempt/no-sujeto)
Gap #2: POS order → XML code path
Gap #3: Token cache/refresh lifecycle
Gap #4: NC/ND error paths (missing reference, missing clave)
Gap #5: Clave generation format (50-digit structure)
Gap #6: Pre-flight validation per document type (FE, TE, NC, ND)
"""

import time
import uuid
from datetime import datetime, date
from unittest.mock import patch, MagicMock
from lxml import etree

from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import EInvoiceTestCase


# ============================================================================
# Gap #1: ResumenFactura 6-way classification
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestResumenFacturaClassification(EInvoiceTestCase):
    """Verify the 6-way split: service/merch x taxed/exempt/no-sujeto.

    Hacienda v4.4 requires separate totals for each combination:
    - TotalServGravados: services with IVA > 0%
    - TotalServExentos: services with 0% IVA tax assigned
    - TotalServNoSujeto: services with NO tax at all
    - TotalMercanciasGravadas: merchandise with IVA > 0%
    - TotalMercanciasExentas: merchandise with 0% IVA tax assigned
    - TotalMercNoSujeta: merchandise with NO tax at all
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

        cr_country_id = cls.env.ref('base.cr').id
        tax_group = cls.env['account.tax.group'].search([
            ('country_id', '=', cr_country_id)
        ], limit=1)
        if not tax_group:
            tax_group = cls.env['account.tax.group'].create({
                'name': 'IVA',
                'country_id': cr_country_id,
            })

        # Create 0% explicit tax (exento — HAS a tax with 0%)
        cls.tax_exempt = cls.env['account.tax'].create({
            'name': f'Exento Gap1 {uuid.uuid4().hex[:6]}',
            'amount': 0.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': cls.company.id,
            'country_id': cr_country_id,
            'tax_group_id': tax_group.id,
        })

        # Service product (CABYS prefix 96-99 → service)
        cls.service_product = cls.env['product.product'].create({
            'name': 'Gym Service',
            'type': 'service',
            'list_price': 5000.0,
        })
        # CABYS code set on invoice lines via l10n_cr_product_code (not on product template)
        cls.service_cabys = '9652000009900'

        # Merchandise product (CABYS prefix NOT 96-99 → merchandise)
        cls.merch_product = cls.env['product.product'].create({
            'name': 'Protein Powder',
            'type': 'consu',
            'list_price': 8000.0,
        })
        cls.merch_cabys = '2110011000000'

    def _create_einvoice_for_move(self, move):
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
        })
        return einvoice

    def _get_resumen_values(self, xml_str):
        """Parse ResumenFactura totals from XML."""
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        resumen = root.find('.//ns:ResumenFactura', ns)
        vals = {}
        for tag in [
            'TotalServGravados', 'TotalServExentos', 'TotalServNoSujeto',
            'TotalMercanciasGravadas', 'TotalMercanciasExentas', 'TotalMercNoSujeta',
            'TotalGravado', 'TotalExento', 'TotalNoSujeto',
            'TotalVenta', 'TotalDescuentos', 'TotalVentaNeta',
            'TotalImpuesto', 'TotalComprobante',
        ]:
            el = resumen.find(f'ns:{tag}', ns)
            vals[tag] = float(el.text) if el is not None else 0.0
        return vals

    def test_service_gravado_classification(self):
        """Service line with 13% IVA → TotalServGravados."""
        move = self._create_test_invoice(lines=[{
            'product_id': self.service_product.id,
            'quantity': 1,
            'price_unit': 5000.0,
            'tax_ids': [(6, 0, [self.tax_13.id])],
            'l10n_cr_product_code': self.service_cabys,
        }])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        vals = self._get_resumen_values(xml_str)

        self.assertAlmostEqual(vals['TotalServGravados'], 5000.0, places=2)
        self.assertEqual(vals['TotalMercanciasGravadas'], 0.0)
        self.assertEqual(vals['TotalServExentos'], 0.0)
        self.assertEqual(vals['TotalServNoSujeto'], 0.0)

    def test_service_exento_classification(self):
        """Service line with explicit 0% tax → TotalServExentos."""
        move = self._create_test_invoice(lines=[{
            'product_id': self.service_product.id,
            'quantity': 1,
            'price_unit': 5000.0,
            'tax_ids': [(6, 0, [self.tax_exempt.id])],
            'l10n_cr_product_code': self.service_cabys,
        }])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        vals = self._get_resumen_values(xml_str)

        self.assertAlmostEqual(vals['TotalServExentos'], 5000.0, places=2)
        self.assertEqual(vals['TotalServGravados'], 0.0)
        self.assertEqual(vals['TotalServNoSujeto'], 0.0)

    def test_service_no_sujeto_classification(self):
        """Service line with NO tax at all → TotalServNoSujeto."""
        move = self._create_test_invoice(lines=[{
            'product_id': self.service_product.id,
            'quantity': 1,
            'price_unit': 5000.0,
            'tax_ids': [(5, 0, 0)],  # Clear all taxes
            'l10n_cr_product_code': self.service_cabys,
        }])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        vals = self._get_resumen_values(xml_str)

        self.assertAlmostEqual(vals['TotalServNoSujeto'], 5000.0, places=2)
        self.assertEqual(vals['TotalServGravados'], 0.0)
        self.assertEqual(vals['TotalServExentos'], 0.0)

    def test_merch_gravado_classification(self):
        """Merchandise line with 13% IVA → TotalMercanciasGravadas."""
        move = self._create_test_invoice(lines=[{
            'product_id': self.merch_product.id,
            'quantity': 1,
            'price_unit': 8000.0,
            'tax_ids': [(6, 0, [self.tax_13.id])],
            'l10n_cr_product_code': self.merch_cabys,
        }])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        vals = self._get_resumen_values(xml_str)

        self.assertAlmostEqual(vals['TotalMercanciasGravadas'], 8000.0, places=2)
        self.assertEqual(vals['TotalServGravados'], 0.0)

    def test_merch_exenta_classification(self):
        """Merchandise line with explicit 0% tax → TotalMercanciasExentas."""
        move = self._create_test_invoice(lines=[{
            'product_id': self.merch_product.id,
            'quantity': 1,
            'price_unit': 8000.0,
            'tax_ids': [(6, 0, [self.tax_exempt.id])],
            'l10n_cr_product_code': self.merch_cabys,
        }])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        vals = self._get_resumen_values(xml_str)

        self.assertAlmostEqual(vals['TotalMercanciasExentas'], 8000.0, places=2)
        self.assertEqual(vals['TotalMercanciasGravadas'], 0.0)

    def test_merch_no_sujeta_classification(self):
        """Merchandise line with NO tax → TotalMercNoSujeta."""
        move = self._create_test_invoice(lines=[{
            'product_id': self.merch_product.id,
            'quantity': 1,
            'price_unit': 8000.0,
            'tax_ids': [(5, 0, 0)],
            'l10n_cr_product_code': self.merch_cabys,
        }])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        vals = self._get_resumen_values(xml_str)

        self.assertAlmostEqual(vals['TotalMercNoSujeta'], 8000.0, places=2)
        self.assertEqual(vals['TotalMercanciasGravadas'], 0.0)
        self.assertEqual(vals['TotalMercanciasExentas'], 0.0)

    def test_mixed_all_six_categories(self):
        """Invoice with all 6 categories simultaneously."""
        move = self._create_test_invoice(lines=[
            # Service + taxed
            {'product_id': self.service_product.id, 'quantity': 1,
             'price_unit': 1000.0, 'tax_ids': [(6, 0, [self.tax_13.id])],
             'l10n_cr_product_code': self.service_cabys},
            # Service + exempt
            {'product_id': self.service_product.id, 'quantity': 1,
             'price_unit': 2000.0, 'tax_ids': [(6, 0, [self.tax_exempt.id])],
             'l10n_cr_product_code': self.service_cabys},
            # Service + no sujeto
            {'product_id': self.service_product.id, 'quantity': 1,
             'price_unit': 3000.0, 'tax_ids': [(5, 0, 0)],
             'l10n_cr_product_code': self.service_cabys},
            # Merch + taxed
            {'product_id': self.merch_product.id, 'quantity': 1,
             'price_unit': 4000.0, 'tax_ids': [(6, 0, [self.tax_13.id])],
             'l10n_cr_product_code': self.merch_cabys},
            # Merch + exempt
            {'product_id': self.merch_product.id, 'quantity': 1,
             'price_unit': 5000.0, 'tax_ids': [(6, 0, [self.tax_exempt.id])],
             'l10n_cr_product_code': self.merch_cabys},
            # Merch + no sujeta
            {'product_id': self.merch_product.id, 'quantity': 1,
             'price_unit': 6000.0, 'tax_ids': [(5, 0, 0)],
             'l10n_cr_product_code': self.merch_cabys},
        ])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        vals = self._get_resumen_values(xml_str)

        self.assertAlmostEqual(vals['TotalServGravados'], 1000.0, places=2)
        self.assertAlmostEqual(vals['TotalServExentos'], 2000.0, places=2)
        self.assertAlmostEqual(vals['TotalServNoSujeto'], 3000.0, places=2)
        self.assertAlmostEqual(vals['TotalMercanciasGravadas'], 4000.0, places=2)
        self.assertAlmostEqual(vals['TotalMercanciasExentas'], 5000.0, places=2)
        self.assertAlmostEqual(vals['TotalMercNoSujeta'], 6000.0, places=2)

        # Verify aggregated totals
        self.assertAlmostEqual(vals['TotalGravado'], 5000.0, places=2)   # 1000+4000
        self.assertAlmostEqual(vals['TotalExento'], 7000.0, places=2)    # 2000+5000
        self.assertAlmostEqual(vals['TotalNoSujeto'], 9000.0, places=2)  # 3000+6000
        self.assertAlmostEqual(vals['TotalVenta'], 21000.0, places=2)

    def test_total_venta_equals_sum_of_categories(self):
        """TotalVenta must equal sum of Gravado + Exento + NoSujeto."""
        move = self._create_test_invoice(lines=[
            {'product_id': self.service_product.id, 'quantity': 2,
             'price_unit': 1500.0, 'tax_ids': [(6, 0, [self.tax_13.id])],
             'l10n_cr_product_code': self.service_cabys},
            {'product_id': self.merch_product.id, 'quantity': 3,
             'price_unit': 2000.0, 'tax_ids': [(5, 0, 0)],
             'l10n_cr_product_code': self.merch_cabys},
        ])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        vals = self._get_resumen_values(xml_str)

        expected_total_venta = (
            vals['TotalGravado'] + vals['TotalExento'] + vals['TotalNoSujeto']
        )
        self.assertAlmostEqual(vals['TotalVenta'], expected_total_venta, places=2)

    def test_total_comprobante_formula(self):
        """TotalComprobante = TotalVentaNeta + TotalImpuesto."""
        move = self._create_test_invoice(lines=[
            {'product_id': self.service_product.id, 'quantity': 1,
             'price_unit': 10000.0, 'tax_ids': [(6, 0, [self.tax_13.id])],
             'l10n_cr_product_code': self.service_cabys},
        ])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        vals = self._get_resumen_values(xml_str)

        expected = vals['TotalVentaNeta'] + vals['TotalImpuesto']
        self.assertAlmostEqual(vals['TotalComprobante'], expected, places=2)

    def test_desglose_impuesto_present_for_taxed_lines(self):
        """TotalDesgloseImpuesto elements must be present when lines have tax."""
        move = self._create_test_invoice(lines=[{
            'product_id': self.service_product.id,
            'quantity': 1,
            'price_unit': 10000.0,
            'tax_ids': [(6, 0, [self.tax_13.id])],
            'l10n_cr_product_code': self.service_cabys,
        }])
        move.action_post()
        einvoice = self._create_einvoice_for_move(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}

        desglose = root.findall('.//ns:TotalDesgloseImpuesto', ns)
        self.assertTrue(len(desglose) >= 1, "Should have at least one TotalDesgloseImpuesto")

        # Verify structure
        first = desglose[0]
        self.assertIsNotNone(first.find('ns:Codigo', ns))
        self.assertIsNotNone(first.find('ns:CodigoTarifaIVA', ns))
        self.assertIsNotNone(first.find('ns:TotalMontoImpuesto', ns))


# ============================================================================
# Gap #2: POS order → XML code path
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestPosOrderXmlGeneration(EInvoiceTestCase):
    """Test the entire pos.order → XML code path.

    The XML generator supports both account.move and pos.order as source
    documents. POS orders use different field names (lines vs invoice_line_ids,
    qty vs quantity, full_product_name vs name, etc.).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

        # Use POS config from the main company (creating POS configs for test
        # companies requires many inter-dependent records)
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            raise cls.skipTest(cls, 'No POS config available for testing')
        # Override company to match the POS config's company for consistency
        cls.company = cls.pos_config.company_id

    def _create_pos_order(self, partner=None, lines=None):
        """Create a POS order with lines for testing."""
        if partner is None:
            partner = self.partner

        # Open a session if not already open
        session = self.env['pos.session'].search([
            ('config_id', '=', self.pos_config.id),
            ('state', '=', 'opened'),
        ], limit=1)
        if not session:
            session = self.env['pos.session'].create({
                'config_id': self.pos_config.id,
                'user_id': self.env.uid,
            })

        if lines is None:
            lines = [(0, 0, {
                'full_product_name': 'Gym Service',
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 10000.0,
                'price_subtotal': 10000.0,
                'price_subtotal_incl': 11300.0,
                'tax_ids': [(6, 0, [self.tax_13.id])],
            })]

        order = self.env['pos.order'].create({
            'session_id': session.id,
            'partner_id': partner.id,
            'company_id': self.company.id,
            'lines': lines,
            'amount_total': 11300.0,
            'amount_tax': 1300.0,
            'amount_paid': 11300.0,
            'amount_return': 0,
        })
        return order

    def _create_pos_einvoice(self, pos_order, doc_type='TE'):
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'pos_order_id': pos_order.id,
            'partner_id': pos_order.partner_id.id or False,
            'document_type': doc_type,
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001040000000001',
        })

    def test_pos_order_generates_valid_xml(self):
        """POS order produces well-formed XML."""
        order = self._create_pos_order()
        einvoice = self._create_pos_einvoice(order, 'TE')
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)

        root = etree.fromstring(xml_str.encode('utf-8'))
        self.assertTrue(root.tag.endswith('TiqueteElectronico'))

    def test_pos_order_as_factura_electronica(self):
        """POS order can also generate FE (when customer data is present)."""
        order = self._create_pos_order(partner=self.partner)
        einvoice = self._create_pos_einvoice(order, 'FE')
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)

        root = etree.fromstring(xml_str.encode('utf-8'))
        self.assertTrue(root.tag.endswith('FacturaElectronica'))
        ns = {'ns': root.nsmap[None]}
        receptor = root.find('.//ns:Receptor', ns)
        self.assertIsNotNone(receptor, "FE from POS must include Receptor")

    def test_pos_line_uses_qty_not_quantity(self):
        """POS lines use 'qty' field, not 'quantity'. Verify computation works."""
        order = self._create_pos_order()
        einvoice = self._create_pos_einvoice(order, 'TE')
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)

        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        cantidad = root.find('.//ns:Cantidad', ns)
        self.assertIsNotNone(cantidad)
        self.assertEqual(float(cantidad.text), 1.0)

    def test_pos_condicion_venta_always_01(self):
        """POS orders always use CondicionVenta = '01' (Contado/Cash)."""
        order = self._create_pos_order()
        einvoice = self._create_pos_einvoice(order, 'TE')
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)

        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        condicion = root.find('.//ns:CondicionVenta', ns)
        self.assertEqual(condicion.text, '01')

    def test_pos_resumen_factura_from_lines(self):
        """POS ResumenFactura computes from lines (not from amount_tax which can be 0)."""
        order = self._create_pos_order()
        einvoice = self._create_pos_einvoice(order, 'TE')
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)

        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        total_impuesto = root.find('.//ns:TotalImpuesto', ns)
        self.assertIsNotNone(total_impuesto)
        # Tax should be > 0 (13% of 10000 = 1300)
        self.assertGreater(float(total_impuesto.text), 0)

    def test_pos_cabys_defaults_to_service(self):
        """POS lines without l10n_cr_product_code default to service CABYS."""
        order = self._create_pos_order()
        einvoice = self._create_pos_einvoice(order, 'TE')
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)

        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        cabys = root.find('.//ns:CodigoCABYS', ns)
        # POS lines don't have l10n_cr_product_code, so falls through to default
        self.assertEqual(cabys.text, '9652000009900')


# ============================================================================
# Gap #3: Token cache/refresh lifecycle
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestTokenCacheLifecycle(EInvoiceTestCase):
    """Test OAuth2 token caching, reuse, expiry, and refresh grant fallback."""

    def setUp(self):
        super().setUp()
        from odoo.addons.l10n_cr_einvoice.models import hacienda_api
        # CRITICAL: clear module-level cache to avoid cross-test pollution
        hacienda_api._TOKEN_CACHE.clear()

        # Use with_company so self.env.company = self.company for API calls
        self.api = self.env['l10n_cr.hacienda.api'].with_company(self.company)
        # Set sandbox credentials (active_username/password are computed from these)
        self.company.write({
            'l10n_cr_hacienda_env': 'sandbox',
            'l10n_cr_hacienda_username': 'test@stag.comprobanteselectronicos.go.cr',
            'l10n_cr_hacienda_password': 'test_password',
        })
        # Invalidate computed fields cache so active_username/password are recomputed
        self.company.invalidate_recordset()

    def tearDown(self):
        from odoo.addons.l10n_cr_einvoice.models import hacienda_api
        hacienda_api._TOKEN_CACHE.clear()
        super().tearDown()

    def _mock_token_response(self, access_token='tok123', expires_in=3600,
                              refresh_token='ref456', refresh_expires_in=86400):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': expires_in,
            'refresh_expires_in': refresh_expires_in,
        }
        return resp

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_first_call_does_password_grant(self, mock_post):
        """First call must perform a password grant."""
        mock_post.return_value = self._mock_token_response()
        token = self.api._obtain_token()

        self.assertEqual(token, 'tok123')
        mock_post.assert_called_once()
        call_data = mock_post.call_args[1].get('data') or mock_post.call_args[0][1] if len(mock_post.call_args[0]) > 1 else mock_post.call_args[1]['data']
        self.assertEqual(call_data['grant_type'], 'password')

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_cached_token_reused(self, mock_post):
        """Second call within expiry window returns cached token without HTTP call."""
        mock_post.return_value = self._mock_token_response()

        token1 = self.api._obtain_token()
        token2 = self.api._obtain_token()

        self.assertEqual(token1, token2)
        # Only one HTTP call (the first password grant)
        self.assertEqual(mock_post.call_count, 1)

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_expired_token_triggers_refresh(self, mock_post):
        """Expired access token uses refresh_token grant."""
        from odoo.addons.l10n_cr_einvoice.models import hacienda_api

        # Seed cache with expired access_token but valid refresh_token
        hacienda_api._TOKEN_CACHE[self.company.id] = {
            'access_token': 'old_token',
            'refresh_token': 'valid_refresh',
            'expires_at': time.time() - 100,       # Expired
            'refresh_expires_at': time.time() + 3600,  # Still valid
        }

        # Mock refresh grant
        mock_post.return_value = self._mock_token_response(access_token='new_token')
        token = self.api._obtain_token()

        self.assertEqual(token, 'new_token')
        call_data = mock_post.call_args[1].get('data', {})
        self.assertEqual(call_data.get('grant_type'), 'refresh_token')

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_expired_refresh_falls_back_to_password(self, mock_post):
        """Both tokens expired → full password grant."""
        from odoo.addons.l10n_cr_einvoice.models import hacienda_api

        hacienda_api._TOKEN_CACHE[self.company.id] = {
            'access_token': 'old',
            'refresh_token': 'old_refresh',
            'expires_at': time.time() - 100,
            'refresh_expires_at': time.time() - 50,  # Also expired
        }

        mock_post.return_value = self._mock_token_response(access_token='fresh')
        token = self.api._obtain_token()

        self.assertEqual(token, 'fresh')
        call_data = mock_post.call_args[1].get('data', {})
        self.assertEqual(call_data.get('grant_type'), 'password')

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_refresh_failure_falls_back_to_password(self, mock_post):
        """If refresh_token grant fails, fall back to password grant."""
        from odoo.addons.l10n_cr_einvoice.models import hacienda_api

        hacienda_api._TOKEN_CACHE[self.company.id] = {
            'access_token': 'old',
            'refresh_token': 'stale_refresh',
            'expires_at': time.time() - 100,
            'refresh_expires_at': time.time() + 3600,
        }

        # First call = refresh (fails), second call = password (succeeds)
        fail_resp = MagicMock()
        fail_resp.status_code = 400
        fail_resp.text = '{"error": "invalid_grant"}'
        fail_resp.json.return_value = {'error': 'invalid_grant'}

        ok_resp = self._mock_token_response(access_token='fallback_token')
        mock_post.side_effect = [fail_resp, ok_resp]

        token = self.api._obtain_token()
        self.assertEqual(token, 'fallback_token')
        self.assertEqual(mock_post.call_count, 2)

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_force_refresh_ignores_cache(self, mock_post):
        """force_refresh=True always does a full password grant."""
        from odoo.addons.l10n_cr_einvoice.models import hacienda_api

        hacienda_api._TOKEN_CACHE[self.company.id] = {
            'access_token': 'cached',
            'refresh_token': 'refresh',
            'expires_at': time.time() + 9999,  # Still valid
            'refresh_expires_at': time.time() + 9999,
        }

        mock_post.return_value = self._mock_token_response(access_token='forced_new')
        token = self.api._obtain_token(force_refresh=True)

        self.assertEqual(token, 'forced_new')

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_safety_margin_30_seconds(self, mock_post):
        """Cache expires 30 seconds before actual token expiry."""
        from odoo.addons.l10n_cr_einvoice.models import hacienda_api

        # Token with expires_in=60 should be cached with expires_at = now + 60 - 30 = now + 30
        mock_post.return_value = self._mock_token_response(expires_in=60)
        self.api._obtain_token()

        cached = hacienda_api._TOKEN_CACHE[self.company.id]
        expected_max = time.time() + 60
        # Expiry should be ~30s before actual
        self.assertLess(cached['expires_at'], expected_max)

    def test_clear_cache_specific_company(self):
        """_clear_token_cache(company_id) clears only that company."""
        from odoo.addons.l10n_cr_einvoice.models import hacienda_api

        hacienda_api._TOKEN_CACHE[1] = {'access_token': 'a'}
        hacienda_api._TOKEN_CACHE[2] = {'access_token': 'b'}

        self.api._clear_token_cache(1)
        self.assertNotIn(1, hacienda_api._TOKEN_CACHE)
        self.assertIn(2, hacienda_api._TOKEN_CACHE)

    def test_clear_cache_all(self):
        """_clear_token_cache() with no arg clears everything."""
        from odoo.addons.l10n_cr_einvoice.models import hacienda_api

        hacienda_api._TOKEN_CACHE[1] = {'access_token': 'a'}
        hacienda_api._TOKEN_CACHE[2] = {'access_token': 'b'}

        self.api._clear_token_cache()
        self.assertEqual(len(hacienda_api._TOKEN_CACHE), 0)

    @patch('odoo.addons.l10n_cr_einvoice.models.hacienda_api.requests.post')
    def test_missing_credentials_raises_user_error(self, mock_post):
        """Missing API credentials raises UserError before any HTTP call."""
        self.company.write({
            'l10n_cr_hacienda_username': False,
            'l10n_cr_hacienda_password': False,
        })
        self.company.invalidate_recordset()
        with self.assertRaises(UserError):
            self.api._obtain_token()
        mock_post.assert_not_called()


# ============================================================================
# Gap #4: NC/ND error paths
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestNcNdErrorPaths(EInvoiceTestCase):
    """Test credit/debit note error paths: missing reference, missing clave."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def _create_einvoice_for_move(self, move, doc_type):
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': doc_type,
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001030000000001',
        })

    def test_nc_missing_reversed_entry_raises_error(self):
        """NC without reversed_entry_id raises UserError."""
        move = self._create_test_invoice(invoice_type='out_refund')
        move.action_post()
        # Don't set reversed_entry_id
        einvoice = self._create_einvoice_for_move(move, 'NC')

        with self.assertRaises(UserError):
            self.xml_generator.generate_invoice_xml(einvoice)

    def test_nc_missing_clave_on_original_raises_error(self):
        """NC with original invoice that has no l10n_cr_clave raises UserError."""
        original = self._create_test_invoice()
        original.action_post()
        # Don't set l10n_cr_clave on original

        credit_note = self._create_test_invoice(invoice_type='out_refund')
        credit_note.reversed_entry_id = original.id
        credit_note.action_post()

        einvoice = self._create_einvoice_for_move(credit_note, 'NC')

        # Should raise because original has no clave and no name is useful as reference
        # The _add_informacion_referencia checks for l10n_cr_clave || name
        # If original.name is set (auto-generated) it won't error, but the pre-flight
        # _validate_reference_document should catch missing clave
        errors = self.xml_generator._validate_reference_document(einvoice, credit_note)
        self.assertTrue(len(errors) > 0, "Should detect missing clave on original invoice")

    def test_nd_missing_debit_origin_raises_error(self):
        """ND without debit_origin_id raises UserError."""
        move = self._create_test_invoice()
        move.action_post()
        # Don't set debit_origin_id
        einvoice = self._create_einvoice_for_move(move, 'ND')

        with self.assertRaises(UserError):
            self.xml_generator.generate_invoice_xml(einvoice)

    def test_nd_missing_clave_on_original_raises_error(self):
        """ND with original invoice that has no clave raises validation error."""
        original = self._create_test_invoice()
        original.action_post()
        # Don't set l10n_cr_clave

        debit_note = self._create_test_invoice()
        debit_note.debit_origin_id = original.id
        debit_note.action_post()

        einvoice = self._create_einvoice_for_move(debit_note, 'ND')
        errors = self.xml_generator._validate_reference_document(einvoice, debit_note)
        self.assertTrue(len(errors) > 0, "Should detect missing clave on original for ND")

    def test_nc_with_valid_reference_succeeds(self):
        """NC with properly configured original invoice succeeds."""
        original = self._create_test_invoice()
        original.action_post()
        original.l10n_cr_clave = '50601012025020100111111111111111111111111111111111'

        credit_note = self._create_test_invoice(invoice_type='out_refund')
        credit_note.reversed_entry_id = original.id
        credit_note.action_post()

        einvoice = self._create_einvoice_for_move(credit_note, 'NC')
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)

        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        info_ref = root.find('.//ns:InformacionReferencia', ns)
        self.assertIsNotNone(info_ref)

        # Verify v4.4 field names (TipoDocIR, FechaEmisionIR — NOT TipoDoc/FechaEmision)
        self.assertIsNotNone(info_ref.find('ns:TipoDocIR', ns))
        self.assertIsNotNone(info_ref.find('ns:FechaEmisionIR', ns))
        self.assertIsNotNone(info_ref.find('ns:Numero', ns))
        self.assertIsNotNone(info_ref.find('ns:Razon', ns))

    def test_nd_validate_reference_no_errors_when_valid(self):
        """ND validation returns no errors when original has clave."""
        original = self._create_test_invoice()
        original.action_post()
        original.l10n_cr_clave = '50601012025020100111111111111111111111111111111111'

        debit_note = self._create_test_invoice()
        debit_note.debit_origin_id = original.id
        debit_note.action_post()

        einvoice = self._create_einvoice_for_move(debit_note, 'ND')
        errors = self.xml_generator._validate_reference_document(einvoice, debit_note)
        self.assertEqual(len(errors), 0)


# ============================================================================
# Gap #5: Clave generation format (50-digit structure)
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestClaveGeneration(EInvoiceTestCase):
    """Validate the 50-digit clave structure per Resolution 48-2016, Article 5.

    Format: 506 + DDMMYY + cedula(12) + consecutive(20) + situación(1) + security(8) = 50
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write({
            'vat': '3101234567',
            'l10n_cr_emisor_location': '10101',
        })

    def _create_test_einvoice(self, move, doc_type='FE'):
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': doc_type,
            'company_id': self.company.id,
        })

    def test_clave_exactly_50_digits(self):
        """Generated clave must be exactly 50 characters."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_test_einvoice(move)
        clave, _ = einvoice._generate_clave()
        self.assertEqual(len(clave), 50)

    def test_clave_starts_with_506(self):
        """Clave must start with country code 506 (Costa Rica)."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_test_einvoice(move)
        clave, _ = einvoice._generate_clave()
        self.assertEqual(clave[:3], '506')

    def test_clave_date_segment_ddmmyy(self):
        """Clave positions 3-8 must be DDMMYY of the invoice date."""
        move = self._create_test_invoice()
        move.invoice_date = date(2025, 2, 1)
        move.action_post()
        einvoice = self._create_test_einvoice(move)
        clave, _ = einvoice._generate_clave()

        date_segment = clave[3:9]
        self.assertEqual(date_segment, '010225')  # 01 Feb 2025

    def test_clave_cedula_12_digits_zero_padded(self):
        """Cedula segment (positions 9-20) must be 12 digits, zero-padded."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_test_einvoice(move)
        clave, _ = einvoice._generate_clave()

        cedula_segment = clave[9:21]
        self.assertEqual(len(cedula_segment), 12)
        self.assertTrue(cedula_segment.isdigit())
        self.assertEqual(cedula_segment, '003101234567')

    def test_clave_consecutive_20_digits(self):
        """Consecutive number (positions 21-40) must be exactly 20 digits."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_test_einvoice(move)
        clave, _ = einvoice._generate_clave()

        consecutive = clave[21:41]
        self.assertEqual(len(consecutive), 20)

    def test_clave_consecutive_contains_doc_type(self):
        """Consecutive includes doc type code (01=FE, 02=ND, 03=NC, 04=TE)."""
        for doc_type, expected_code in [('FE', '01'), ('ND', '02'), ('NC', '03'), ('TE', '04')]:
            with self.subTest(doc_type=doc_type):
                move = self._create_test_invoice()
                move.action_post()
                einvoice = self._create_test_einvoice(move, doc_type)
                clave, _ = einvoice._generate_clave()

                consecutive = clave[21:41]
                # SSS(3) + TTTTT(5) + DD(2) = doc type at positions 8-9 of consecutive
                doc_type_code = consecutive[8:10]
                self.assertEqual(doc_type_code, expected_code,
                                 f"{doc_type} should have code {expected_code} in consecutive")

    def test_clave_situacion_is_1_normal(self):
        """Situación (position 41) should be '1' for normal operation."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_test_einvoice(move)
        clave, _ = einvoice._generate_clave()

        situacion = clave[41]
        self.assertEqual(situacion, '1')

    def test_clave_security_code_8_digits(self):
        """Security code (positions 42-49) must be 8 random digits."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_test_einvoice(move)
        clave, _ = einvoice._generate_clave()

        security = clave[42:50]
        self.assertEqual(len(security), 8)
        self.assertTrue(security.isdigit())

    def test_clave_all_digits(self):
        """All 50 characters must be digits."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_test_einvoice(move)
        clave, _ = einvoice._generate_clave()
        self.assertTrue(clave.isdigit(), f"Clave must be all digits, got: {clave}")

    def test_clave_unique_security_codes(self):
        """Two consecutive claves should have different security codes."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_test_einvoice(move)

        clave1, _ = einvoice._generate_clave()
        clave2, _ = einvoice._generate_clave()
        # Security codes (last 8 digits) should almost always differ
        self.assertNotEqual(clave1[42:50], clave2[42:50])

    def test_clave_consecutive_has_sucursal_terminal(self):
        """Consecutive begins with SSS (sucursal 3 digits) + TTTTT (terminal 5 digits)."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_test_einvoice(move)
        clave, _ = einvoice._generate_clave()

        consecutive = clave[21:41]
        sucursal = consecutive[:3]
        terminal = consecutive[3:8]

        self.assertEqual(len(sucursal), 3)
        self.assertEqual(len(terminal), 5)
        self.assertTrue(sucursal.isdigit())
        self.assertTrue(terminal.isdigit())


# ============================================================================
# Gap #6: Pre-flight validation per document type
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestPreflightValidation(EInvoiceTestCase):
    """Test _validate_before_generation for all 4 doc types (FE, TE, NC, ND)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def _make_einvoice(self, move, doc_type, partner=None):
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id,
            'partner_id': partner.id if partner else False,
            'document_type': doc_type,
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
        })

    # --- FE validations ---

    def test_fe_no_partner_raises_error(self):
        """FE requires a partner (Receptor)."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._make_einvoice(move, 'FE', partner=None)

        # Call validation directly — assertRaises triggers savepoint flush
        # which runs @api.constrains before our code runs
        errors = self.xml_generator._validate_factura_requirements(einvoice, move)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any('cliente' in e.lower() for e in errors))

    def test_fe_partner_no_vat_raises_error(self):
        """FE requires partner VAT."""
        no_vat_partner = self.env['res.partner'].create({
            'name': 'No VAT Partner',
            'email': 'novat@test.com',
            'country_id': self.env.ref('base.cr').id,
        })
        move = self._create_test_invoice(partner=no_vat_partner)
        move.action_post()
        einvoice = self._make_einvoice(move, 'FE', partner=no_vat_partner)

        errors = self.xml_generator._validate_factura_requirements(einvoice, move)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any('cédula' in e.lower() or 'identificación' in e.lower() for e in errors))

    def test_fe_partner_no_email_raises_error(self):
        """FE requires partner email."""
        no_email_partner = self.env['res.partner'].create({
            'name': 'No Email Partner',
            'vat': '101111111',
            'country_id': self.env.ref('base.cr').id,
        })
        move = self._create_test_invoice(partner=no_email_partner)
        move.action_post()
        einvoice = self._make_einvoice(move, 'FE', partner=no_email_partner)

        errors = self.xml_generator._validate_factura_requirements(einvoice, move)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any('correo' in e.lower() or 'email' in e.lower() for e in errors))

    def test_fe_valid_partner_passes(self):
        """FE with complete partner data passes validation."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._make_einvoice(move, 'FE', partner=self.partner)

        # Should not raise
        self.xml_generator._validate_before_generation(einvoice)

    # --- TE validations ---

    def test_te_no_partner_passes(self):
        """TE does NOT require a partner (anonymous sales)."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._make_einvoice(move, 'TE', partner=None)

        # TE has minimal requirements — company data only
        errors = self.xml_generator._validate_tiquete_requirements(einvoice, move)
        # May have errors if company is missing location, but NOT for partner
        partner_errors = [e for e in errors if 'cliente' in e.lower() or 'customer' in e.lower()]
        self.assertEqual(len(partner_errors), 0)

    def test_te_company_no_vat_raises_error(self):
        """TE still requires company VAT."""
        self.company.vat = False
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._make_einvoice(move, 'TE')

        errors = self.xml_generator._validate_tiquete_requirements(einvoice, move)
        self.assertTrue(len(errors) > 0)

    def test_te_company_no_location_raises_error(self):
        """TE requires company emisor location."""
        self.company.l10n_cr_emisor_location = False
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._make_einvoice(move, 'TE')

        errors = self.xml_generator._validate_tiquete_requirements(einvoice, move)
        self.assertTrue(len(errors) > 0)

    # --- NC validations ---

    def test_nc_no_source_document_raises_error(self):
        """NC without reversed_entry_id fails validation."""
        move = self._create_test_invoice(invoice_type='out_refund')
        move.action_post()
        einvoice = self._make_einvoice(move, 'NC', partner=self.partner)

        errors = self.xml_generator._validate_reference_document(einvoice, move)
        self.assertTrue(len(errors) > 0)

    # --- ND validations ---

    def test_nd_no_source_document_raises_error(self):
        """ND without debit_origin_id fails validation."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._make_einvoice(move, 'ND', partner=self.partner)

        errors = self.xml_generator._validate_reference_document(einvoice, move)
        self.assertTrue(len(errors) > 0)

    # --- Certificate validation ---

    def test_no_certificate_raises_error(self):
        """Missing digital certificate raises validation error."""
        self.company.l10n_cr_certificate = False
        errors = self.xml_generator._validate_company_certificate(self.company)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any('certificado' in e.lower() for e in errors))

    def test_no_key_password_raises_error(self):
        """Missing certificate password raises validation error."""
        self.company.l10n_cr_key_password = False
        errors = self.xml_generator._validate_company_certificate(self.company)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any('contraseña' in e.lower() or 'pin' in e.lower() for e in errors))

    def test_valid_p12_certificate_no_errors(self):
        """Valid .p12 certificate with password passes."""
        errors = self.xml_generator._validate_company_certificate(self.company)
        self.assertEqual(len(errors), 0)

    # --- Email format validation ---

    def test_invalid_email_format_detected(self):
        """Invalid email format caught by _validate_email_format."""
        errors = self.xml_generator._validate_email_format('not-an-email', 'Test')
        self.assertTrue(len(errors) > 0)

    def test_valid_email_format_passes(self):
        """Valid email passes format check."""
        errors = self.xml_generator._validate_email_format('user@example.com', 'Test')
        self.assertEqual(len(errors), 0)

    # --- Cedula format validation ---

    def test_cedula_fisica_9_digits_valid(self):
        """9-digit cedula fisica is valid."""
        partner = self.env['res.partner'].create({
            'name': 'Fisica', 'vat': '101234567',
            'country_id': self.env.ref('base.cr').id,
        })
        errors = self.xml_generator._validate_cedula_format(partner)
        self.assertEqual(len(errors), 0)

    def test_cedula_fisica_non_numeric_invalid(self):
        """9-char non-numeric cedula is invalid (detected as Fisica but fails isdigit)."""
        partner = self.env['res.partner'].create({
            'name': 'BadFisica', 'vat': '12345678A',
            'country_id': self.env.ref('base.cr').id,
        })
        errors = self.xml_generator._validate_cedula_format(partner)
        self.assertTrue(len(errors) > 0)

    def test_dimex_11_digits_valid(self):
        """11-digit DIMEX is valid."""
        partner = self.env['res.partner'].create({
            'name': 'Dimex11', 'vat': '12345678901',
            'country_id': self.env.ref('base.cr').id,
        })
        errors = self.xml_generator._validate_cedula_format(partner)
        self.assertEqual(len(errors), 0)

    def test_dimex_12_digits_valid(self):
        """12-digit DIMEX is valid."""
        partner = self.env['res.partner'].create({
            'name': 'Dimex12', 'vat': '123456789012',
            'country_id': self.env.ref('base.cr').id,
        })
        errors = self.xml_generator._validate_cedula_format(partner)
        self.assertEqual(len(errors), 0)
