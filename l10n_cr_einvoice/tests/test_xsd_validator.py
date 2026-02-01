# -*- coding: utf-8 -*-
"""
Unit tests for XSD Validator (l10n_cr.xsd.validator)

Tests XML validation functionality for Costa Rica e-invoicing.
"""
from odoo.tests import TransactionCase


class TestXSDValidator(TransactionCase):
    """Test XSD validator for e-invoice XML validation."""

    def setUp(self):
        super(TestXSDValidator, self).setUp()
        self.validator = self.env['l10n_cr.xsd.validator']

    def test_validator_exists(self):
        """Test that validator model exists."""
        self.assertTrue(self.validator, "XSD validator model should exist")

    def test_validate_empty_xml(self):
        """Test validation of empty XML."""
        is_valid, error = self.validator.validate_xml('', 'FE')
        self.assertFalse(is_valid, "Empty XML should be invalid")
        self.assertTrue(error, "Error message should be provided")

    def test_validate_invalid_document_type(self):
        """Test validation with invalid document type."""
        xml = '<?xml version="1.0" encoding="UTF-8"?><Root/>'
        is_valid, error = self.validator.validate_xml(xml, 'INVALID')
        self.assertFalse(is_valid, "Invalid document type should fail validation")
        self.assertIn('Unknown document type', error)

    def test_validate_malformed_xml(self):
        """Test validation of malformed XML."""
        xml = '<Root>Unclosed tag'
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        self.assertFalse(is_valid, "Malformed XML should fail validation")
        self.assertTrue(error, "Error message should be provided")

    def test_validate_wrong_root_element(self):
        """Test validation with wrong root element."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<WrongRoot xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>12345678901234567890123456789012345678901234567890</Clave>
</WrongRoot>'''
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        self.assertFalse(is_valid, "Wrong root element should fail validation")
        self.assertIn('Invalid root element', error)

    def test_validate_missing_required_elements(self):
        """Test validation with missing required elements."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>12345678901234567890123456789012345678901234567890</Clave>
</FacturaElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        self.assertFalse(is_valid, "XML with missing required elements should fail")
        self.assertTrue(error, "Error message should list missing elements")

    def test_validate_invalid_clave_length(self):
        """Test validation with invalid clave length."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>123</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Test Company</Nombre>
        <Identificacion>
            <Tipo>02</Tipo>
            <Numero>3101234567</Numero>
        </Identificacion>
    </Emisor>
    <Receptor>
        <Nombre>Test Customer</Nombre>
    </Receptor>
    <ResumenFactura>
        <TotalComprobante>100.00</TotalComprobante>
    </ResumenFactura>
</FacturaElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        self.assertFalse(is_valid, "Invalid clave length should fail validation")
        self.assertIn('Clave', error)

    def test_validate_valid_factura_electronica(self):
        """Test validation of valid Factura Electrónica."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Test Company</Nombre>
        <Identificacion>
            <Tipo>02</Tipo>
            <Numero>3101234567</Numero>
        </Identificacion>
    </Emisor>
    <Receptor>
        <Nombre>Test Customer</Nombre>
        <Identificacion>
            <Tipo>01</Tipo>
            <Numero>123456789</Numero>
        </Identificacion>
    </Receptor>
    <ResumenFactura>
        <TotalComprobante>100.00</TotalComprobante>
    </ResumenFactura>
</FacturaElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        self.assertTrue(is_valid, f"Valid FE XML should pass validation. Error: {error}")
        self.assertEqual(error, '', "No error message should be returned for valid XML")

    def test_validate_valid_tiquete_electronico(self):
        """Test validation of valid Tiquete Electrónico."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<TiqueteElectronico xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/tiqueteElectronico">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Test Company</Nombre>
        <Identificacion>
            <Tipo>02</Tipo>
            <Numero>3101234567</Numero>
        </Identificacion>
    </Emisor>
    <ResumenFactura>
        <TotalComprobante>100.00</TotalComprobante>
    </ResumenFactura>
</TiqueteElectronico>'''
        is_valid, error = self.validator.validate_xml(xml, 'TE')
        self.assertTrue(is_valid, f"Valid TE XML should pass validation. Error: {error}")
        self.assertEqual(error, '', "No error message should be returned for valid XML")

    def test_get_validation_errors(self):
        """Test getting detailed validation errors."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>123</Clave>
</FacturaElectronica>'''
        result = self.validator.get_validation_errors(xml, 'FE')

        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn('is_valid', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        self.assertIn('schema_available', result)
        self.assertFalse(result['is_valid'], "Invalid XML should return is_valid=False")
        self.assertTrue(result['errors'], "Errors list should not be empty")

    def test_check_schema_availability(self):
        """Test checking XSD schema availability."""
        availability = self.validator.check_schema_availability()

        self.assertIsInstance(availability, dict, "Result should be a dictionary")
        self.assertIn('FE', availability)
        self.assertIn('TE', availability)
        self.assertIn('NC', availability)
        self.assertIn('ND', availability)

        # Each value should be a boolean
        for doc_type, available in availability.items():
            self.assertIsInstance(available, bool, f"{doc_type} availability should be boolean")

    def test_validate_nota_credito(self):
        """Test validation of Nota de Crédito."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<NotaCreditoElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaCreditoElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Test Company</Nombre>
        <Identificacion>
            <Tipo>02</Tipo>
            <Numero>3101234567</Numero>
        </Identificacion>
    </Emisor>
    <Receptor>
        <Nombre>Test Customer</Nombre>
        <Identificacion>
            <Tipo>01</Tipo>
            <Numero>123456789</Numero>
        </Identificacion>
    </Receptor>
    <ResumenFactura>
        <TotalComprobante>100.00</TotalComprobante>
    </ResumenFactura>
</NotaCreditoElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'NC')
        self.assertTrue(is_valid, f"Valid NC XML should pass validation. Error: {error}")

    def test_validate_nota_debito(self):
        """Test validation of Nota de Débito."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<NotaDebitoElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaDebitoElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Test Company</Nombre>
        <Identificacion>
            <Tipo>02</Tipo>
            <Numero>3101234567</Numero>
        </Identificacion>
    </Emisor>
    <Receptor>
        <Nombre>Test Customer</Nombre>
        <Identificacion>
            <Tipo>01</Tipo>
            <Numero>123456789</Numero>
        </Identificacion>
    </Receptor>
    <ResumenFactura>
        <TotalComprobante>100.00</TotalComprobante>
    </ResumenFactura>
</NotaDebitoElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'ND')
        self.assertTrue(is_valid, f"Valid ND XML should pass validation. Error: {error}")
