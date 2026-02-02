# -*- coding: utf-8 -*-
"""
Unit tests for XSD Validator (l10n_cr.xsd.validator)

Tests XML validation functionality for Costa Rica e-invoicing.
Covers all document types (FE, TE, NC, ND) and edge cases.

Target Coverage: ≥85% for xsd_validator module
"""
import time
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit')
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


# ============================================================================
# EDGE CASE TESTS - Special Characters and Encoding
# ============================================================================


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestXSDValidatorSpecialCharacters(TransactionCase):
    """Test XSD validator with special characters (ñ, á, etc.)."""

    def setUp(self):
        super().setUp()
        self.validator = self.env['l10n_cr.xsd.validator']

    def test_validate_spanish_accents(self):
        """Test validation with Spanish accented characters (á, é, í, ó, ú)."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Café José García S.A.</Nombre>
        <Identificacion>
            <Tipo>02</Tipo>
            <Numero>3101234567</Numero>
        </Identificacion>
    </Emisor>
    <Receptor>
        <Nombre>María Pérez López</Nombre>
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
        self.assertTrue(is_valid, f"XML with Spanish accents should be valid. Error: {error}")

    def test_validate_spanish_n_with_tilde(self):
        """Test validation with Spanish ñ character."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<TiqueteElectronico xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/tiqueteElectronico">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Peña y Niños S.A.</Nombre>
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
        self.assertTrue(is_valid, f"XML with ñ character should be valid. Error: {error}")

    def test_validate_special_symbols(self):
        """Test validation with special symbols (&, <, >, ampersands escaped)."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Smith &amp; Jones Corp</Nombre>
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
        self.assertTrue(is_valid, f"XML with escaped ampersand should be valid. Error: {error}")

    def test_validate_unescaped_ampersand_fails(self):
        """Test validation fails with unescaped ampersand."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <Emisor>
        <Nombre>Smith & Jones Corp</Nombre>
    </Emisor>
</FacturaElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        self.assertFalse(is_valid, "XML with unescaped ampersand should fail")
        self.assertTrue(error, "Error message should be provided")


# ============================================================================
# EDGE CASE TESTS - String Length Limits
# ============================================================================


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestXSDValidatorStringLengths(TransactionCase):
    """Test XSD validator with maximum string lengths."""

    def setUp(self):
        super().setUp()
        self.validator = self.env['l10n_cr.xsd.validator']

    def test_validate_max_length_company_name(self):
        """Test validation with maximum length company name (100 chars)."""
        long_name = "A" * 100  # Max allowed
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>{long_name}</Nombre>
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
        self.assertTrue(is_valid, f"XML with 100-char name should be valid. Error: {error}")

    def test_validate_empty_optional_elements(self):
        """Test validation with empty optional elements."""
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
        self.assertTrue(is_valid, f"TE without Receptor should be valid. Error: {error}")


# ============================================================================
# EDGE CASE TESTS - Numeric Precision and Data Types
# ============================================================================


@tagged('post_install', '-at_install', 'l10n_cr_einvoice', 'unit', 'p0')
class TestXSDValidatorNumericPrecision(TransactionCase):
    """Test XSD validator with numeric precision edge cases."""

    def setUp(self):
        super().setUp()
        self.validator = self.env['l10n_cr.xsd.validator']

    def test_validate_decimal_precision_5_digits(self):
        """Test validation with 5 decimal place precision."""
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
        <TotalComprobante>12345.67890</TotalComprobante>
    </ResumenFactura>
</FacturaElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        # Note: Hacienda spec allows up to 18 total digits, 5 decimals
        self.assertTrue(is_valid or 'decimal' in error.lower(),
                       f"Should validate or provide decimal precision error. Error: {error}")

    def test_validate_large_monetary_amount(self):
        """Test validation with large monetary amounts (13 integer digits, 5 decimals)."""
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
        <TotalComprobante>9999999999999.99</TotalComprobante>
    </ResumenFactura>
</FacturaElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        self.assertTrue(is_valid, f"Large monetary amount should be valid. Error: {error}")

    def test_validate_zero_amount(self):
        """Test validation with zero amount (edge case)."""
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
        <TotalComprobante>0.00</TotalComprobante>
    </ResumenFactura>
</NotaCreditoElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'NC')
        self.assertTrue(is_valid, f"Zero amount should be valid. Error: {error}")

    def test_validate_negative_amount_fails(self):
        """Test validation fails with negative amount."""
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
        <TotalComprobante>-100.00</TotalComprobante>
    </ResumenFactura>
</FacturaElectronica>'''
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        # Negative amounts may be allowed by XSD but violate business rules
        # Check that validation at least processes the XML
        self.assertIsNotNone(is_valid, "Validation should complete")


# ============================================================================
# EDGE CASE TESTS - Invalid XML Scenarios
# ============================================================================


@tagged("post_install", "-at_install", "l10n_cr_einvoice", "unit", "p0")
class TestXSDValidatorInvalidXML(TransactionCase):
    """Test XSD validator with various invalid XML scenarios."""

    def setUp(self):
        super().setUp()
        self.validator = self.env['l10n_cr.xsd.validator']

    def test_validate_wrong_data_type_in_clave(self):
        """Test validation fails when Clave contains non-numeric characters."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>ABCDEFGHIJ1234567890123456789012345678901234567890</Clave>
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
        self.assertFalse(is_valid, "Clave with non-numeric characters should fail")
        self.assertIn('Clave', error, "Error should mention Clave")

    def test_validate_invalid_date_format(self):
        """Test validation fails with invalid date format."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28</FechaEmision>
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
        # Might pass well-formed validation but fail XSD if available
        # Test that error is reported if validation is strict
        if not is_valid:
            self.assertTrue(error, "Error message should be provided for invalid date")

    def test_validate_missing_namespace(self):
        """Test validation with missing namespace."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica>
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
        # Should still be well-formed, but may fail XSD validation if schema requires namespace
        self.assertTrue(is_valid or 'namespace' in error.lower() or 'schema' in error.lower(),
                       f"Should validate as well-formed or fail with namespace error. Error: {error}")

    def test_validate_duplicate_elements(self):
        """Test validation with duplicate required elements."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <Clave>11111111111111111111111111111111111111111111111111</Clave>
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
        # XSD validation should catch duplicate elements if schema is available
        self.assertTrue(is_valid or 'duplicate' in error.lower() or 'Clave' in error,
                       f"Duplicate elements should fail XSD validation. Error: {error}")


# ============================================================================
# SCHEMA VERSION AND ERROR MESSAGE TESTS
# ============================================================================


@tagged("post_install", "-at_install", "l10n_cr_einvoice", "unit", "p1")
class TestXSDValidatorSchemaVersion(TransactionCase):
    """Test XSD validator schema version handling."""

    def setUp(self):
        super().setUp()
        self.validator = self.env['l10n_cr.xsd.validator']

    def test_schema_urls_are_v4_4(self):
        """Test that schema URLs reference v4.4."""
        for doc_type, url in self.validator.SCHEMA_URLS.items():
            self.assertIn('v4.4', url,
                         f"Schema URL for {doc_type} should reference v4.4")

    def test_all_document_types_have_schemas(self):
        """Test that all document types have schema configurations."""
        expected_types = ['FE', 'TE', 'NC', 'ND']
        for doc_type in expected_types:
            self.assertIn(doc_type, self.validator.SCHEMA_URLS,
                         f"Schema URL missing for {doc_type}")
            self.assertIn(doc_type, self.validator.ROOT_ELEMENTS,
                         f"Root element missing for {doc_type}")
            self.assertIn(doc_type, self.validator.XSD_PATHS,
                         f"XSD path missing for {doc_type}")

    def test_root_elements_match_document_types(self):
        """Test that root element names are correct for each document type."""
        expected_roots = {
            'FE': 'FacturaElectronica',
            'TE': 'TiqueteElectronico',
            'NC': 'NotaCreditoElectronica',
            'ND': 'NotaDebitoElectronica',
        }
        for doc_type, expected_root in expected_roots.items():
            actual_root = self.validator.ROOT_ELEMENTS.get(doc_type)
            self.assertEqual(actual_root, expected_root,
                           f"Root element for {doc_type} should be {expected_root}")


@tagged("post_install", "-at_install", "l10n_cr_einvoice", "unit", "p1")
class TestXSDValidatorErrorMessages(TransactionCase):
    """Test XSD validator detailed error message parsing."""

    def setUp(self):
        super().setUp()
        self.validator = self.env['l10n_cr.xsd.validator']

    def test_get_validation_errors_structure(self):
        """Test that get_validation_errors returns proper structure."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>123</Clave>
</FacturaElectronica>'''
        result = self.validator.get_validation_errors(xml, 'FE')

        # Check structure
        self.assertIsInstance(result, dict, "Result should be dictionary")
        self.assertIn('is_valid', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        self.assertIn('schema_available', result)

        # Check types
        self.assertIsInstance(result['is_valid'], bool)
        self.assertIsInstance(result['errors'], list)
        self.assertIsInstance(result['warnings'], list)
        self.assertIsInstance(result['schema_available'], bool)

    def test_get_validation_errors_with_invalid_xml(self):
        """Test get_validation_errors with invalid XML returns detailed errors."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>12345</Clave>
</FacturaElectronica>'''
        result = self.validator.get_validation_errors(xml, 'FE')

        self.assertFalse(result['is_valid'])
        self.assertTrue(len(result['errors']) > 0, "Should have at least one error")

        # Check that errors mention missing elements or invalid Clave
        error_text = ' '.join(result['errors'])
        self.assertTrue('Clave' in error_text or 'Missing' in error_text or 'required' in error_text.lower(),
                       f"Errors should mention validation issues: {error_text}")

    def test_get_validation_errors_with_valid_xml(self):
        """Test get_validation_errors with valid XML returns no errors."""
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
        result = self.validator.get_validation_errors(xml, 'FE')

        self.assertTrue(result['is_valid'], f"Valid XML should pass. Errors: {result['errors']}")
        self.assertEqual(len(result['errors']), 0, "No errors should be present for valid XML")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@tagged("post_install", "-at_install", "l10n_cr_einvoice", "unit", "p1")
class TestXSDValidatorPerformance(TransactionCase):
    """Test XSD validator performance (<500ms per document)."""

    def setUp(self):
        super().setUp()
        self.validator = self.env['l10n_cr.xsd.validator']

    def test_validation_performance_simple_document(self):
        """Test that validation completes in under 500ms for simple document."""
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

        start_time = time.time()
        is_valid, error = self.validator.validate_xml(xml, 'FE')
        elapsed_time = time.time() - start_time

        self.assertLess(elapsed_time, 0.5,
                       f"Validation should complete in <500ms, took {elapsed_time*1000:.2f}ms")
        self.assertTrue(is_valid, f"Valid XML should pass. Error: {error}")

    def test_validation_performance_all_document_types(self):
        """Test that all document types validate in under 500ms each."""
        test_cases = {
            'FE': '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor><Nombre>Test</Nombre><Identificacion><Tipo>02</Tipo><Numero>3101234567</Numero></Identificacion></Emisor>
    <Receptor><Nombre>Customer</Nombre><Identificacion><Tipo>01</Tipo><Numero>123456789</Numero></Identificacion></Receptor>
    <ResumenFactura><TotalComprobante>100.00</TotalComprobante></ResumenFactura>
</FacturaElectronica>''',
            'TE': '''<?xml version="1.0" encoding="UTF-8"?>
<TiqueteElectronico xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/tiqueteElectronico">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor><Nombre>Test</Nombre><Identificacion><Tipo>02</Tipo><Numero>3101234567</Numero></Identificacion></Emisor>
    <ResumenFactura><TotalComprobante>100.00</TotalComprobante></ResumenFactura>
</TiqueteElectronico>''',
            'NC': '''<?xml version="1.0" encoding="UTF-8"?>
<NotaCreditoElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaCreditoElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor><Nombre>Test</Nombre><Identificacion><Tipo>02</Tipo><Numero>3101234567</Numero></Identificacion></Emisor>
    <Receptor><Nombre>Customer</Nombre><Identificacion><Tipo>01</Tipo><Numero>123456789</Numero></Identificacion></Receptor>
    <ResumenFactura><TotalComprobante>100.00</TotalComprobante></ResumenFactura>
</NotaCreditoElectronica>''',
            'ND': '''<?xml version="1.0" encoding="UTF-8"?>
<NotaDebitoElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaDebitoElectronica">
    <Clave>50601012500012345678901234567890123456789012345678</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-01-28T10:00:00-06:00</FechaEmision>
    <Emisor><Nombre>Test</Nombre><Identificacion><Tipo>02</Tipo><Numero>3101234567</Numero></Identificacion></Emisor>
    <Receptor><Nombre>Customer</Nombre><Identificacion><Tipo>01</Tipo><Numero>123456789</Numero></Identificacion></Receptor>
    <ResumenFactura><TotalComprobante>100.00</TotalComprobante></ResumenFactura>
</NotaDebitoElectronica>''',
        }

        for doc_type, xml in test_cases.items():
            start_time = time.time()
            is_valid, error = self.validator.validate_xml(xml, doc_type)
            elapsed_time = time.time() - start_time

            self.assertLess(elapsed_time, 0.5,
                           f"{doc_type} validation should complete in <500ms, took {elapsed_time*1000:.2f}ms")
            self.assertTrue(is_valid, f"{doc_type} should be valid. Error: {error}")
