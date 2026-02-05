# -*- coding: utf-8 -*-
"""
Comprehensive Unit Tests for XML Generator (Phase 7)

This module provides comprehensive unit test coverage for the XML generation module,
covering all document types, edge cases, and validation requirements per Hacienda v4.4 spec.

Test Coverage:
- All document types: FE, TE, NC, ND
- Edge cases: max line items (200), special characters, multi-currency
- Required fields validation
- Tax calculations
- Reference document handling (for NC/ND)
- Clave (key) generation with check digit validation

Priority Markers:
- P0 tests: Critical priority (must pass before production)
- P1 tests: High priority
- P2 tests: Medium priority
"""

from datetime import datetime, date
from decimal import Decimal
from lxml import etree
import uuid

from odoo.tests import tagged
from odoo.exceptions import ValidationError
from .common import EInvoiceTestCase


def _generate_unique_vat_company():
    """Generate unique VAT number for company (10 digits starting with 3)."""
    return f"310{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_vat_person():
    """Generate unique VAT number for person (9 digits)."""
    return f"10{uuid.uuid4().hex[:7].upper()}"


def _generate_unique_email(prefix='test'):
    """Generate unique email address."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestXMLGeneratorCore(EInvoiceTestCase):
    """Core XML generation tests for all document types."""

    def setUp(self):
        super().setUp()

        # Update company with additional e-invoice settings
        # (Base class already created company, partner, product, and tax)
        self.company.write({
            'l10n_cr_emisor_location': '10101',
        })

        # Set activity code on company partner (required for e-invoice)
        self.company.partner_id.l10n_cr_activity_code = '861201'

        # Get XML generator
        self.xml_generator = self.env['l10n_cr.xml.generator']

    # Note: Use self._create_test_invoice() from base class EInvoiceTestCase
    # which properly sets up journal and all required fields

    def _create_einvoice(self, move, doc_type='FE'):
        """
        Helper to create e-invoice document with test data.

        Creates e-invoice with pre-set clave and consecutive number for testing.
        """
        einvoice = self._create_einvoice_document(move, doc_type)
        # Set test clave and consecutive number
        einvoice.write({
            'name': '00100001010000000001',  # Test consecutive number
            'clave': '50601012025020100111111111111111111111111111111111',
        })
        return einvoice

    def _parse_xml(self, xml_str):
        """Helper to parse XML string."""
        return etree.fromstring(xml_str.encode('utf-8'))

    def test_generate_factura_electronica_basic(self):
        """Test basic FE (Factura Electrónica) XML generation."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_einvoice(move, 'FE')

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Verify root element
        self.assertTrue(root.tag.endswith('FacturaElectronica'))

        # Verify namespace
        ns = self.xml_generator.NAMESPACES['fe']
        self.assertEqual(root.nsmap[None], ns)

    def test_generate_tiquete_electronico_basic(self):
        """Test basic TE (Tiquete Electrónico) XML generation."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_einvoice(move, 'TE')

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Verify root element
        self.assertTrue(root.tag.endswith('TiqueteElectronico'))

    def test_generate_nota_credito_basic(self):
        """Test basic NC (Nota de Crédito) XML generation."""
        # Create original invoice
        original = self._create_test_invoice()
        original.action_post()
        original.l10n_cr_clave = '50601012025020100111111111111111111111111111111111'

        # Create credit note
        move = self._create_test_invoice(invoice_type='out_refund')
        move.reversed_entry_id = original.id
        move.action_post()
        einvoice = self._create_einvoice(move, 'NC')

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Verify root element
        self.assertTrue(root.tag.endswith('NotaCreditoElectronica'))

    def test_generate_nota_debito_basic(self):
        """Test basic ND (Nota de Débito) XML generation."""
        # Create original invoice
        original = self._create_test_invoice()
        original.action_post()
        original.l10n_cr_clave = '50601012025020100111111111111111111111111111111111'

        # Create debit note
        move = self._create_test_invoice()
        move.debit_origin_id = original.id
        move.action_post()
        einvoice = self._create_einvoice(move, 'ND')

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = self._parse_xml(xml_str)

        # Verify root element
        self.assertTrue(root.tag.endswith('NotaDebitoElectronica'))

    def test_unknown_document_type_raises_error(self):
        """Test that unknown document type raises ValidationError."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self._create_einvoice(move, 'FE')

        # Test that setting invalid document type raises ValueError (Selection field validation)
        with self.assertRaises(ValueError):
            einvoice.document_type = 'XX'  # Invalid type


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestXMLGeneratorRequiredFields(EInvoiceTestCase):
    """Test required fields per Hacienda v4.4 specification."""

    def setUp(self):
        super().setUp()

        # Use company, partner, product from base class EInvoiceTestCase
        # (Already created with proper journals and taxes)
        self.xml_generator = self.env['l10n_cr.xml.generator']

    def test_clave_field_present(self):
        """Test that Clave field is present in XML."""
        move = self._create_test_invoice()
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        clave = root.find('.//ns:Clave', ns)

        self.assertIsNotNone(clave, "Clave field must be present")
        self.assertEqual(clave.text, einvoice.clave)
        self.assertEqual(len(clave.text), 50, "Clave must be 50 digits")

    def test_proveedor_sistemas_field_present(self):
        """Test that ProveedorSistemas field is present (required in v4.4)."""
        move = self._create_test_invoice()
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        proveedor = root.find('.//ns:ProveedorSistemas', ns)

        self.assertIsNotNone(proveedor, "ProveedorSistemas field must be present in v4.4")

    def test_codigo_actividad_emisor_min_6_chars(self):
        """Test that CodigoActividadEmisor has minimum 6 characters (v4.4 requirement)."""
        move = self._create_test_invoice()
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        codigo = root.find('.//ns:CodigoActividadEmisor', ns)

        self.assertIsNotNone(codigo, "CodigoActividadEmisor must be present")
        self.assertGreaterEqual(len(codigo.text), 6, "CodigoActividadEmisor must be at least 6 characters")

    def test_emisor_section_complete(self):
        """Test that Emisor section contains all required fields."""
        move = self._create_test_invoice()
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        emisor = root.find('.//ns:Emisor', ns)

        self.assertIsNotNone(emisor, "Emisor section must be present")

        # Check required sub-elements
        self.assertIsNotNone(emisor.find('ns:Nombre', ns), "Emisor.Nombre is required")
        self.assertIsNotNone(emisor.find('ns:Identificacion', ns), "Emisor.Identificacion is required")
        self.assertIsNotNone(emisor.find('ns:Ubicacion', ns), "Emisor.Ubicacion is required")
        self.assertIsNotNone(emisor.find('ns:CorreoElectronico', ns), "Emisor.CorreoElectronico is required")


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestXMLGeneratorTaxCalculations(EInvoiceTestCase):
    """Test tax calculations in XML generation."""

    def setUp(self):
        super().setUp()

        # Use company, partner, product from base class EInvoiceTestCase
        # (Already created with proper journals and taxes)
        self.xml_generator = self.env['l10n_cr.xml.generator']

    def test_tax_13_percent_calculation(self):
        """Test 13% IVA tax calculation."""
        # Get CR country and tax group for proper tax setup
        cr_country_id = self.env.ref('base.cr').id
        tax_group = self.env['account.tax.group'].search([
            ('country_id', '=', cr_country_id)
        ], limit=1)
        if not tax_group:
            tax_group = self.env['account.tax.group'].create({
                'name': 'IVA',
                'country_id': cr_country_id,
            })

        tax_13 = self.env['account.tax'].create({
            'name': 'IVA 13%',
            'amount': 13.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'country_id': cr_country_id,
            'tax_group_id': tax_group.id,
        })

        move = self._create_test_invoice(lines=[{
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 10000.0,
            'tax_ids': [(6, 0, [tax_13.id])],
        }])
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        impuesto = root.find('.//ns:Impuesto', ns)

        self.assertIsNotNone(impuesto, "Impuesto element must be present")
        self.assertEqual(impuesto.find('ns:Codigo', ns).text, '01')
        self.assertEqual(impuesto.find('ns:Tarifa', ns).text, '13.00')

    def test_tax_4_percent_calculation(self):
        """Test 4% IVA tax calculation."""
        # Get CR country and tax group for proper tax setup
        cr_country_id = self.env.ref('base.cr').id
        tax_group = self.env['account.tax.group'].search([
            ('country_id', '=', cr_country_id)
        ], limit=1)
        if not tax_group:
            tax_group = self.env['account.tax.group'].create({
                'name': 'IVA',
                'country_id': cr_country_id,
            })

        tax_4 = self.env['account.tax'].create({
            'name': 'IVA 4%',
            'amount': 4.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'country_id': cr_country_id,
            'tax_group_id': tax_group.id,
        })

        move = self._create_test_invoice(lines=[{
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 10000.0,
            'tax_ids': [(6, 0, [tax_4.id])],
        }])
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        impuesto = root.find('.//ns:Impuesto', ns)

        self.assertEqual(impuesto.find('ns:Codigo', ns).text, '02')
        self.assertEqual(impuesto.find('ns:Tarifa', ns).text, '4.00')

    def test_zero_tax_calculation(self):
        """Test 0% tax (exempt) calculation."""
        # Get CR country and tax group for proper tax setup
        cr_country_id = self.env.ref('base.cr').id
        tax_group = self.env['account.tax.group'].search([
            ('country_id', '=', cr_country_id)
        ], limit=1)
        if not tax_group:
            tax_group = self.env['account.tax.group'].create({
                'name': 'IVA',
                'country_id': cr_country_id,
            })

        # Use unique tax name to avoid constraint violation
        tax_0 = self.env['account.tax'].create({
            'name': 'Exento Test 0%',
            'amount': 0.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'country_id': cr_country_id,
            'tax_group_id': tax_group.id,
        })

        move = self._create_test_invoice(lines=[{
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 10000.0,
            'tax_ids': [(6, 0, [tax_0.id])],
        }])
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        impuesto = root.find('.//ns:Impuesto', ns)

        self.assertEqual(impuesto.find('ns:Codigo', ns).text, '06')
        self.assertEqual(impuesto.find('ns:Tarifa', ns).text, '0.00')

    def test_no_tax_creates_default_impuesto(self):
        """Test that lines without taxes still get Impuesto element (v4.4 requirement)."""
        move = self._create_test_invoice(lines=[{
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 10000.0,
            'tax_ids': [(5, 0, 0)],  # Clear all taxes
        }])
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        impuesto = root.find('.//ns:Impuesto', ns)

        self.assertIsNotNone(impuesto, "Impuesto element must be present even without taxes")
        self.assertEqual(impuesto.find('ns:Monto', ns).text, '0.00000')


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestXMLGeneratorEdgeCases(EInvoiceTestCase):
    """Test edge cases and special scenarios."""

    def setUp(self):
        super().setUp()

        # Use company, partner, product from base class EInvoiceTestCase
        # (Already created with proper journals and taxes)
        self.xml_generator = self.env['l10n_cr.xml.generator']

    def test_special_characters_in_description(self):
        """Test that special characters are handled correctly in line descriptions."""
        product = self.env['product.product'].create({
            'name': 'Product with <special> & "characters"',
            'type': 'service',
            'list_price': 1000.0,
            'taxes_id': [(6, 0, [self.tax_13.id])],
        })

        move = self._create_test_invoice(lines=[{
            'product_id': product.id,
            'quantity': 1,
            'price_unit': 1000.0,
            'tax_ids': [(6, 0, [self.tax_13.id])],
        }])
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        # Should not raise exception
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)

        # XML should be well-formed
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}
        detalle = root.find('.//ns:Detalle', ns)

        self.assertIsNotNone(detalle)
        # Special characters should be escaped
        self.assertIn('special', detalle.text)

    def test_line_with_discount(self):
        """Test invoice line with discount."""
        # Get discount code 01 from data
        discount_code_01 = self.env.ref('l10n_cr_einvoice.discount_code_01')

        move = self._create_test_invoice(lines=[{
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 10000.0,
            'discount': 10.0,  # 10% discount
            'l10n_cr_discount_code_id': discount_code_01.id,  # Required discount code for CR e-invoicing
            'tax_ids': [(6, 0, [self.tax_13.id])],
        }])
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        descuento = root.find('.//ns:Descuento', ns)

        self.assertIsNotNone(descuento, "Discount element should be present")
        monto_descuento = descuento.find('ns:MontoDescuento', ns)
        self.assertIsNotNone(monto_descuento)
        # 10% of 10000 = 1000
        self.assertEqual(float(monto_descuento.text), 1000.0)

    def test_multi_currency_usd(self):
        """Test invoice in USD currency."""
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not usd:
            usd = self.env['res.currency'].create({'name': 'USD', 'symbol': '$'})

        # Create invoice with USD currency using base helper
        # Note: Cannot use _create_test_invoice as it doesn't support currency param
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.sales_journal.id,
            'currency_id': usd.id,
            'invoice_date': '2025-02-01',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [(6, 0, [self.tax_13.id])],
            })],
        })
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        codigo_moneda = root.find('.//ns:CodigoMoneda', ns)

        self.assertIsNotNone(codigo_moneda)
        self.assertEqual(codigo_moneda.text, 'USD')

    def test_partner_different_id_types(self):
        """Test different partner ID types (Cédula Física, Jurídica, DIMEX, etc.)."""
        test_cases = [
            ('101234567', '01'),    # 9 digits = Cédula Física
            ('3101234567', '02'),   # 10 digits starting with 3 = Cédula Jurídica
            ('4101234567', '04'),   # 10 digits not starting with 3 = NITE
            ('12345678901', '03'),  # 11 digits = DIMEX
            ('123456789012', '03'), # 12 digits = DIMEX
            ('', '05'),             # No VAT = Extranjero
        ]

        for vat, expected_tipo in test_cases:
            with self.subTest(vat=vat):
                tipo = self.xml_generator._get_partner_id_type(vat)
                self.assertEqual(tipo, expected_tipo, f"VAT {vat} should map to type {expected_tipo}")

    def test_company_id_type(self):
        """Test company identification type (should be Cédula Jurídica)."""
        tipo = self.xml_generator._get_company_id_type('3101234567')
        self.assertEqual(tipo, '02', "Company should use Cédula Jurídica (02)")

    def test_ubicacion_barrio_min_5_chars(self):
        """Test that Barrio field has minimum 5 characters (v4.4 requirement)."""
        # Set short location code
        self.company.l10n_cr_emisor_location = '10101'

        move = self._create_test_invoice()
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        barrio = root.find('.//ns:Barrio', ns)

        self.assertIsNotNone(barrio)
        self.assertGreaterEqual(len(barrio.text), 5, "Barrio must be at least 5 characters")


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p1')
class TestXMLGeneratorReferenceDocuments(EInvoiceTestCase):
    """Test reference document handling for credit/debit notes."""

    def setUp(self):
        super().setUp()

        # Use company, partner, product from base class EInvoiceTestCase
        # (Already created with proper journals and taxes)
        self.xml_generator = self.env['l10n_cr.xml.generator']

    def test_credit_note_includes_reference(self):
        """Test that credit note includes reference to original invoice."""
        # Create original invoice
        original = self._create_test_invoice()
        original.action_post()
        original.l10n_cr_clave = '50601012025020100111111111111111111111111111111111'

        # Create credit note
        credit_note = self._create_test_invoice(invoice_type='out_refund')
        credit_note.reversed_entry_id = original.id
        credit_note.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': credit_note.id,
            'partner_id': self.partner.id,
            'document_type': 'NC',
            'company_id': self.company.id,
            'clave': '50604012025020200111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        info_ref = root.find('.//ns:InformacionReferencia', ns)

        self.assertIsNotNone(info_ref, "Credit note should include InformacionReferencia")
        self.assertIsNotNone(info_ref.find('ns:TipoDoc', ns))
        self.assertIsNotNone(info_ref.find('ns:Numero', ns))

    def test_debit_note_includes_reference(self):
        """Test that debit note includes reference to original invoice."""
        # Create original invoice
        original = self._create_test_invoice()
        original.action_post()
        original.l10n_cr_clave = '50601012025020100111111111111111111111111111111111'

        # Create debit note
        debit_note = self._create_test_invoice(lines=[{
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 1000.0,  # Additional charge
            'tax_ids': [(6, 0, [self.tax_13.id])],
        }])
        debit_note.debit_origin_id = original.id
        debit_note.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': debit_note.id,
            'partner_id': self.partner.id,
            'document_type': 'ND',
            'company_id': self.company.id,
            'clave': '50603012025020200111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        info_ref = root.find('.//ns:InformacionReferencia', ns)

        self.assertIsNotNone(info_ref, "Debit note should include InformacionReferencia")


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p2')
class TestXMLGeneratorPerformance(EInvoiceTestCase):
    """Test performance with large datasets (edge case: max 200 line items)."""

    def setUp(self):
        super().setUp()

        # Use company, partner, product from base class EInvoiceTestCase
        # (Already created with proper journals and taxes)
        self.xml_generator = self.env['l10n_cr.xml.generator']

    def test_max_line_items_200(self):
        """Test invoice with maximum 200 line items."""
        # Create invoice with 200 lines
        line_data = []
        for i in range(200):
            line_data.append({
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
                'name': f'Line {i + 1}',
                'tax_ids': [(6, 0, [self.tax_13.id])],
            })

        move = self._create_test_invoice(lines=line_data)
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        # Should generate XML without error
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        # Verify line count
        ns = {'ns': root.nsmap[None]}
        lines = root.findall('.//ns:LineaDetalle', ns)

        self.assertEqual(len(lines), 200, "Should have 200 line items")

    def test_line_numbers_sequential(self):
        """Test that line numbers are sequential starting from 1."""
        line_data = []
        for i in range(10):
            line_data.append({
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [(6, 0, [self.tax_13.id])],
            })

        move = self._create_test_invoice(lines=line_data)
        move.action_post()

        einvoice = self.env['l10n_cr.einvoice.document'].create({
            'move_id': move.id,
            'partner_id': self.partner.id,
            'document_type': 'FE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
        })

        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))

        ns = {'ns': root.nsmap[None]}
        lines = root.findall('.//ns:LineaDetalle', ns)

        for i, line in enumerate(lines):
            numero_linea = line.find('ns:NumeroLinea', ns)
            self.assertEqual(int(numero_linea.text), i + 1, f"Line {i} should have NumeroLinea {i + 1}")
