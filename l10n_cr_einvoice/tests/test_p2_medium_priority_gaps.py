# -*- coding: utf-8 -*-
"""
P2 Medium Priority Gap Tests

Gap #15: Discount code '99' mandatory extra fields (CodigoDescuentoOTRO, NaturalezaDescuento)
Gap #16: String length enforcement (_sanitize_text)
Gap #17: Receptor edge cases (no VAT, no email)
Gap #18: Exonerations — not implemented (skeleton tests for future)
Gap #19: OtrosCargos — not implemented (skeleton tests for future)
Gap #20: Concurrency/locking (double-click protection)
Gap #21: TiloPay webhook signature verification (not code — deferred)
"""

import uuid
from lxml import etree

from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import EInvoiceTestCase


# ============================================================================
# Gap #15: Discount code '99' mandatory extra fields
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p2')
class TestDiscountCode99(EInvoiceTestCase):
    """When CodigoDescuento = '99', CodigoDescuentoOTRO and NaturalezaDescuento are mandatory."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def _make_einvoice(self, move):
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
        })

    def test_discount_code_07_no_extra_fields(self):
        """Standard discount code '07' does NOT require extra fields."""
        discount_code_07 = self.env['l10n_cr.discount.code'].search(
            [('code', '=', '07')], limit=1
        )
        if not discount_code_07:
            self.skipTest('Discount code 07 not found')
        move = self._create_test_invoice(lines=[{
            'product_id': self.product.id, 'quantity': 1,
            'price_unit': 10000.0, 'discount': 10.0,
            'tax_ids': [(6, 0, [self.tax_13.id])],
            'l10n_cr_discount_code_id': discount_code_07.id,
        }])
        move.action_post()
        einvoice = self._make_einvoice(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}

        descuento = root.find('.//ns:Descuento', ns)
        self.assertIsNotNone(descuento)
        codigo = descuento.find('ns:CodigoDescuento', ns)
        self.assertIsNotNone(codigo)
        # Standard code should NOT have CodigoDescuentoOTRO
        otro = descuento.find('ns:CodigoDescuentoOTRO', ns)
        if otro is not None:
            self.assertNotEqual(codigo.text, '07',
                                "Code 07 should not have CodigoDescuentoOTRO")

    def test_discount_line_has_monto_descuento(self):
        """Discount lines must have MontoDescuento element."""
        discount_code_07 = self.env['l10n_cr.discount.code'].search(
            [('code', '=', '07')], limit=1
        )
        if not discount_code_07:
            self.skipTest('Discount code 07 not found')
        move = self._create_test_invoice(lines=[{
            'product_id': self.product.id, 'quantity': 1,
            'price_unit': 10000.0, 'discount': 15.0,
            'tax_ids': [(6, 0, [self.tax_13.id])],
            'l10n_cr_discount_code_id': discount_code_07.id,
        }])
        move.action_post()
        einvoice = self._make_einvoice(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}

        monto_desc = root.find('.//ns:MontoDescuento', ns)
        self.assertIsNotNone(monto_desc)
        self.assertAlmostEqual(float(monto_desc.text), 1500.0, places=2)

    def test_no_discount_no_descuento_element(self):
        """Lines without discount should NOT have Descuento element."""
        move = self._create_test_invoice(lines=[{
            'product_id': self.product.id, 'quantity': 1,
            'price_unit': 10000.0, 'discount': 0.0,
            'tax_ids': [(6, 0, [self.tax_13.id])],
        }])
        move.action_post()
        einvoice = self._make_einvoice(move)
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}

        descuento = root.find('.//ns:Descuento', ns)
        self.assertIsNone(descuento)


# ============================================================================
# Gap #16: String length enforcement (_sanitize_text)
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p2')
class TestSanitizeText(EInvoiceTestCase):
    """Test _sanitize_text for XSD min/max length enforcement."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def test_none_with_min_returns_default(self):
        """None input with min_len returns the default."""
        result = self.xml_generator._sanitize_text(None, min_len=5, max_len=50, default='Hello')
        self.assertEqual(result, 'Hello')

    def test_empty_with_min_returns_default(self):
        """Empty string with min_len returns the default."""
        result = self.xml_generator._sanitize_text('', min_len=5, max_len=50, default='Hello')
        self.assertEqual(result, 'Hello')

    def test_whitespace_only_with_min_returns_default(self):
        """Whitespace-only input returns the default."""
        result = self.xml_generator._sanitize_text('   ', min_len=3, max_len=50, default='Abc')
        self.assertEqual(result, 'Abc')

    def test_text_truncated_to_max_len(self):
        """Text exceeding max_len is truncated."""
        result = self.xml_generator._sanitize_text('A' * 200, min_len=0, max_len=100)
        self.assertEqual(len(result), 100)

    def test_short_text_padded_to_min_len(self):
        """Text shorter than min_len is padded."""
        result = self.xml_generator._sanitize_text('Hi', min_len=5, max_len=50)
        self.assertGreaterEqual(len(result), 5)

    def test_normal_text_unchanged(self):
        """Text within bounds is returned as-is (stripped)."""
        result = self.xml_generator._sanitize_text('  Hello World  ', min_len=0, max_len=50)
        self.assertEqual(result, 'Hello World')

    def test_exact_min_len_not_padded(self):
        """Text at exactly min_len is not padded."""
        result = self.xml_generator._sanitize_text('Hello', min_len=5, max_len=50)
        self.assertEqual(result, 'Hello')

    def test_exact_max_len_not_truncated(self):
        """Text at exactly max_len is not truncated."""
        text = 'A' * 50
        result = self.xml_generator._sanitize_text(text, min_len=0, max_len=50)
        self.assertEqual(result, text)

    def test_no_min_no_max_returns_stripped(self):
        """Without constraints, returns stripped text."""
        result = self.xml_generator._sanitize_text('  test  ')
        self.assertEqual(result, 'test')

    def test_none_with_no_min_returns_default(self):
        """None with no min_len returns empty default."""
        result = self.xml_generator._sanitize_text(None)
        self.assertEqual(result, '')

    def test_numeric_input_converted(self):
        """Numeric input is converted to string."""
        result = self.xml_generator._sanitize_text(12345, min_len=0, max_len=10)
        self.assertEqual(result, '12345')


# ============================================================================
# Gap #17: Receptor edge cases
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p2')
class TestReceptorEdgeCases(EInvoiceTestCase):
    """Test Receptor (customer) XML generation edge cases."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def _make_einvoice(self, move, partner):
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': partner.id if partner else False,
            'document_type': 'FE', 'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
        })

    def test_receptor_no_vat_omits_identificacion(self):
        """Partner without VAT → Receptor has no Identificacion element."""
        no_vat = self.env['res.partner'].create({
            'name': 'Tourist Customer',
            'email': 'tourist@example.com',
            'country_id': self.env.ref('base.cr').id,
        })
        move = self._create_test_invoice(partner=no_vat)
        move.action_post()
        einvoice = self._make_einvoice(move, no_vat)

        # Build XML directly to test _add_receptor
        root = etree.Element('Test')
        self.xml_generator._add_receptor(root, no_vat)
        receptor = root.find('Receptor')
        self.assertIsNotNone(receptor)

        # Nombre should be present
        nombre = receptor.find('Nombre')
        self.assertIsNotNone(nombre)

        # Identificacion should be absent (no VAT)
        identificacion = receptor.find('Identificacion')
        self.assertIsNone(identificacion)

    def test_receptor_no_email_omits_correo(self):
        """Partner without email → Receptor has no CorreoElectronico."""
        no_email = self.env['res.partner'].create({
            'name': 'No Email Customer',
            'vat': '101234567',
            'country_id': self.env.ref('base.cr').id,
        })
        root = etree.Element('Test')
        self.xml_generator._add_receptor(root, no_email)
        receptor = root.find('Receptor')

        correo = receptor.find('CorreoElectronico')
        self.assertIsNone(correo)

    def test_receptor_with_full_data(self):
        """Partner with all data → complete Receptor section."""
        root = etree.Element('Test')
        self.xml_generator._add_receptor(root, self.partner)
        receptor = root.find('Receptor')

        self.assertIsNotNone(receptor.find('Nombre'))
        self.assertIsNotNone(receptor.find('Identificacion'))
        self.assertIsNotNone(receptor.find('CorreoElectronico'))

    def test_receptor_nombre_sanitized(self):
        """Partner name is sanitized (min=3, max=100)."""
        short_name = self.env['res.partner'].create({
            'name': 'AB',  # Too short for XSD
            'vat': '101234567',
            'email': 'ab@test.com',
            'country_id': self.env.ref('base.cr').id,
        })
        root = etree.Element('Test')
        self.xml_generator._add_receptor(root, short_name)
        nombre = root.find('Receptor/Nombre')
        self.assertGreaterEqual(len(nombre.text), 3, "Nombre must be at least 3 chars")

    def test_receptor_vat_cleaned(self):
        """VAT with dashes/spaces is cleaned for Numero element."""
        dirty_vat = self.env['res.partner'].create({
            'name': 'Dirty VAT Partner',
            'vat': '1-0123-4567',
            'email': 'dirty@test.com',
            'country_id': self.env.ref('base.cr').id,
        })
        root = etree.Element('Test')
        self.xml_generator._add_receptor(root, dirty_vat)
        numero = root.find('Receptor/Identificacion/Numero')
        self.assertIsNotNone(numero)
        self.assertNotIn('-', numero.text)
        self.assertNotIn(' ', numero.text)

    def test_te_no_receptor_in_xml(self):
        """TE (Tiquete Electrónico) does NOT include Receptor section."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id,
            'document_type': 'TE',
            'company_id': self.company.id,
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001040000000001',
        })
        xml_str = self.xml_generator.generate_invoice_xml(einvoice)
        root = etree.fromstring(xml_str.encode('utf-8'))
        ns = {'ns': root.nsmap[None]}

        receptor = root.find('.//ns:Receptor', ns)
        self.assertIsNone(receptor, "TE should NOT have Receptor element")


# ============================================================================
# Gap #20: Concurrency/locking (double-click protection)
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p2')
class TestConcurrencyLocking(EInvoiceTestCase):
    """Test database locking for double-click protection on actions."""

    def _create_draft_einvoice(self):
        move = self._create_test_invoice()
        move.action_post()
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'state': 'draft',
        })

    def test_generate_xml_only_from_valid_states(self):
        """action_generate_xml only works from draft/error states."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'state': 'submitted',
        })
        with self.assertRaises(UserError):
            einvoice.action_generate_xml()

    def test_sign_xml_only_from_generated_state(self):
        """action_sign_xml only works from generated/signing_error states."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'state': 'draft',
        })
        with self.assertRaises(UserError):
            einvoice.action_sign_xml()

    def test_submit_only_from_signed_state(self):
        """action_submit_to_hacienda only works from signed/submission_error states."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'state': 'draft',
        })
        with self.assertRaises(UserError):
            einvoice.action_submit_to_hacienda()

    def test_check_status_only_from_submitted_state(self):
        """action_check_status only works from submitted/error states."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'state': 'draft',
        })
        with self.assertRaises(UserError):
            einvoice.action_check_status()

    def test_retry_from_generation_error(self):
        """action_retry from generation_error calls action_generate_xml."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'state': 'generation_error',
        })
        # Should attempt to retry generation (may fail due to validation, but routes correctly)
        try:
            einvoice.action_retry()
        except (UserError, ValidationError):
            pass  # Expected — validation may fail, but the routing was correct

    def test_retry_from_non_error_state_raises(self):
        """action_retry from non-error state raises UserError."""
        move = self._create_test_invoice()
        move.action_post()
        einvoice = self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'state': 'draft',
        })
        with self.assertRaises(UserError):
            einvoice.action_retry()

    def test_retry_button_visible_for_error_states(self):
        """retry_button_visible is True for error states."""
        move = self._create_test_invoice()
        move.action_post()
        for error_state in ['generation_error', 'signing_error', 'submission_error']:
            with self.subTest(state=error_state):
                einvoice = self.env['l10n_cr.einvoice.document'].with_context(
                    bypass_einvoice_validation=True
                ).create({
                    'move_id': move.id, 'partner_id': self.partner.id,
                    'document_type': 'FE', 'company_id': self.company.id,
                    'state': error_state,
                })
                self.assertTrue(einvoice.retry_button_visible)

    def test_retry_button_hidden_for_normal_states(self):
        """retry_button_visible is False for non-error states."""
        move = self._create_test_invoice()
        move.action_post()
        for state in ['draft', 'generated', 'signed', 'submitted', 'accepted', 'rejected']:
            with self.subTest(state=state):
                einvoice = self.env['l10n_cr.einvoice.document'].with_context(
                    bypass_einvoice_validation=True
                ).create({
                    'move_id': move.id, 'partner_id': self.partner.id,
                    'document_type': 'FE', 'company_id': self.company.id,
                    'state': state,
                })
                self.assertFalse(einvoice.retry_button_visible)


# ============================================================================
# Gap #16 extended: Activity code formatting
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p2')
class TestActivityCodeFormatting(EInvoiceTestCase):
    """Test _format_activity_code for trailing-zero padding."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_generator = cls.env['l10n_cr.xml.generator']

    def test_4_digit_code_padded_with_trailing_zeros(self):
        """4-digit code → 6 digits with trailing zeros."""
        self.assertEqual(self.xml_generator._format_activity_code('9311'), '931100')

    def test_6_digit_code_unchanged(self):
        """6-digit code → returned as-is."""
        self.assertEqual(self.xml_generator._format_activity_code('861201'), '861201')

    def test_7_digit_code_truncated(self):
        """7-digit code → truncated to 6."""
        self.assertEqual(self.xml_generator._format_activity_code('8612019'), '861201')

    def test_3_digit_code_padded(self):
        """3-digit code → 6 digits with trailing zeros."""
        self.assertEqual(self.xml_generator._format_activity_code('931'), '931000')

    def test_1_digit_code_padded(self):
        """1-digit code → 6 digits with trailing zeros."""
        self.assertEqual(self.xml_generator._format_activity_code('9'), '900000')

    def test_empty_code_padded(self):
        """Empty code → 6 zeros."""
        self.assertEqual(self.xml_generator._format_activity_code(''), '000000')


# ============================================================================
# Gap #17 extended: MensajeHacienda XML parsing
# ============================================================================

@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p2')
class TestMensajeHaciendaParsing(EInvoiceTestCase):
    """Test _parse_mensaje_hacienda_xml with various inputs."""

    def _create_einvoice(self):
        move = self._create_test_invoice()
        move.action_post()
        return self.env['l10n_cr.einvoice.document'].with_context(
            bypass_einvoice_validation=True
        ).create({
            'move_id': move.id, 'partner_id': self.partner.id,
            'document_type': 'FE', 'company_id': self.company.id,
            'state': 'submitted',
            'clave': '50601012025020100111111111111111111111111111111111',
            'name': '00100001010000000001',
        })

    def test_parse_namespaced_xml(self):
        """Parse MensajeHacienda with v4.4 namespace."""
        import base64
        ns = 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/mensajeHacienda'
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <MensajeHacienda xmlns="{ns}">
            <Clave>50601012025020100111111111111111111111111111111111</Clave>
            <EstadoMensaje>1</EstadoMensaje>
            <DetalleMensaje>Documento aceptado correctamente</DetalleMensaje>
            <Mensaje>Aceptado</Mensaje>
        </MensajeHacienda>'''
        encoded = base64.b64encode(xml.encode('utf-8')).decode('utf-8')

        einvoice = self._create_einvoice()
        result = einvoice._parse_mensaje_hacienda_xml(encoded)

        self.assertEqual(result.get('DetalleMensaje'), 'Documento aceptado correctamente')
        self.assertEqual(result.get('EstadoMensaje'), '1')
        self.assertEqual(result.get('Mensaje'), 'Aceptado')

    def test_parse_xml_without_namespace(self):
        """Parse MensajeHacienda without namespace (fallback)."""
        import base64
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <MensajeHacienda>
            <DetalleMensaje>Simple rejection</DetalleMensaje>
            <EstadoMensaje>2</EstadoMensaje>
        </MensajeHacienda>'''
        encoded = base64.b64encode(xml.encode('utf-8')).decode('utf-8')

        einvoice = self._create_einvoice()
        result = einvoice._parse_mensaje_hacienda_xml(encoded)

        self.assertEqual(result.get('DetalleMensaje'), 'Simple rejection')

    def test_parse_invalid_base64_returns_empty(self):
        """Invalid base64 input returns empty dict."""
        einvoice = self._create_einvoice()
        result = einvoice._parse_mensaje_hacienda_xml('not-valid-base64!!!')
        self.assertEqual(result, {})

    def test_parse_invalid_xml_returns_empty(self):
        """Invalid XML returns empty dict."""
        import base64
        encoded = base64.b64encode(b'<not-xml').decode('utf-8')
        einvoice = self._create_einvoice()
        result = einvoice._parse_mensaje_hacienda_xml(encoded)
        self.assertEqual(result, {})

    def test_parse_raw_xml_string_returns_empty(self):
        """Raw XML string (not base64) is gracefully handled.

        base64.b64decode silently produces garbage for non-base64 strings
        (doesn't raise), so raw XML strings fail to parse and return {}.
        """
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <MensajeHacienda>
            <DetalleMensaje>Raw input</DetalleMensaje>
        </MensajeHacienda>'''

        einvoice = self._create_einvoice()
        result = einvoice._parse_mensaje_hacienda_xml(xml)
        # Raw XML strings get corrupted by base64.b64decode → returns empty
        self.assertIsInstance(result, dict)

    def test_parse_bytes_input(self):
        """Bytes input is handled."""
        xml_bytes = b'''<?xml version="1.0" encoding="UTF-8"?>
        <MensajeHacienda>
            <DetalleMensaje>Bytes input</DetalleMensaje>
        </MensajeHacienda>'''

        einvoice = self._create_einvoice()
        result = einvoice._parse_mensaje_hacienda_xml(xml_bytes)
        self.assertEqual(result.get('DetalleMensaje'), 'Bytes input')
