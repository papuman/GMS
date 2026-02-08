# -*- coding: utf-8 -*-
"""
Unit tests for E-Invoice XML Parser
Tests XML parsing for Costa Rica e-invoice format v4.4
"""
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date


class TestXMLParser(TransactionCase):
    """Test l10n_cr.einvoice.xml.parser model."""

    def setUp(self):
        super(TestXMLParser, self).setUp()
        self.parser = self.env['l10n_cr.einvoice.xml.parser']

    def _get_sample_fe_xml(self):
        """Get a sample Factura Electrónica XML for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012400010001234567890123456789012345678901</Clave>
    <CodigoActividad>861201</CodigoActividad>
    <NumeroConsecutivo>001-00001-01-0000000001</NumeroConsecutivo>
    <FechaEmision>2024-01-15T10:30:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Empresa de Prueba SA</Nombre>
        <Identificacion>
            <Tipo>02</Tipo>
            <Numero>3101234567</Numero>
        </Identificacion>
        <NombreComercial>Empresa Prueba</NombreComercial>
        <Ubicacion>
            <Provincia>1</Provincia>
            <Canton>01</Canton>
            <Distrito>01</Distrito>
            <Barrio>01</Barrio>
            <OtrasSenas>Frente al parque central</OtrasSenas>
        </Ubicacion>
        <Telefono>
            <CodigoPais>506</CodigoPais>
            <NumTelefono>22223333</NumTelefono>
        </Telefono>
        <CorreoElectronico>emisor@example.com</CorreoElectronico>
    </Emisor>
    <Receptor>
        <Nombre>Cliente de Prueba</Nombre>
        <Identificacion>
            <Tipo>01</Tipo>
            <Numero>104560789</Numero>
        </Identificacion>
        <Ubicacion>
            <Provincia>2</Provincia>
            <Canton>02</Canton>
            <Distrito>03</Distrito>
            <OtrasSenas>200 metros norte del mall</OtrasSenas>
        </Ubicacion>
        <CorreoElectronico>receptor@example.com</CorreoElectronico>
    </Receptor>
    <CondicionVenta>01</CondicionVenta>
    <MedioPago>01</MedioPago>
    <ResumenFactura>
        <TotalMercanciasGravadas>100.00</TotalMercanciasGravadas>
        <TotalDescuentos>0.00</TotalDescuentos>
        <TotalMercanciasExentas>0.00</TotalMercanciasExentas>
        <TotalExento>0.00</TotalExento>
        <TotalVenta>100.00</TotalVenta>
        <TotalVentaNeta>100.00</TotalVentaNeta>
        <TotalImpuesto>13.00</TotalImpuesto>
        <TotalComprobante>113.00</TotalComprobante>
    </ResumenFactura>
</FacturaElectronica>"""

    def _get_sample_te_xml(self):
        """Get a sample Tiquete Electrónico XML for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<TiqueteElectronico xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/tiqueteElectronico">
    <Clave>50604012400010001234567890123456789012345678901</Clave>
    <CodigoActividad>861201</CodigoActividad>
    <NumeroConsecutivo>001-00001-04-0000000001</NumeroConsecutivo>
    <FechaEmision>2024-01-15T14:30:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Tienda Local SA</Nombre>
        <Identificacion>
            <Tipo>02</Tipo>
            <Numero>3109876543</Numero>
        </Identificacion>
        <Ubicacion>
            <Provincia>1</Provincia>
            <Canton>02</Canton>
            <Distrito>05</Distrito>
            <OtrasSenas>Centro comercial local 5</OtrasSenas>
        </Ubicacion>
        <CorreoElectronico>tienda@example.com</CorreoElectronico>
    </Emisor>
    <CondicionVenta>01</CondicionVenta>
    <MedioPago>01</MedioPago>
    <ResumenFactura>
        <TotalMercanciasGravadas>50.00</TotalMercanciasGravadas>
        <TotalDescuentos>0.00</TotalDescuentos>
        <TotalMercanciasExentas>0.00</TotalMercanciasExentas>
        <TotalExento>0.00</TotalExento>
        <TotalVenta>50.00</TotalVenta>
        <TotalVentaNeta>50.00</TotalVentaNeta>
        <TotalImpuesto>6.50</TotalImpuesto>
        <TotalComprobante>56.50</TotalComprobante>
    </ResumenFactura>
</TiqueteElectronico>"""

    def test_parse_factura_electronica(self):
        """Test parsing a Factura Electrónica (FE) XML."""
        xml = self._get_sample_fe_xml()
        data = self.parser.parse_xml_file(xml)

        # Validate document type
        self.assertEqual(data['document_type'], 'FE', "Should detect FE document type")

        # Validate clave
        self.assertEqual(
            data['clave'],
            '50601012400010001234567890123456789012345678901',
            "Should extract correct clave"
        )

        # Validate consecutive
        self.assertEqual(
            data['consecutive'],
            '001-00001-01-0000000001',
            "Should extract correct consecutive"
        )

        # Validate date
        self.assertEqual(data['date'], date(2024, 1, 15), "Should parse date correctly")

        # Validate activity code
        self.assertEqual(data['activity_code'], '861201', "Should extract activity code")

    def test_parse_tiquete_electronico(self):
        """Test parsing a Tiquete Electrónico (TE) XML."""
        xml = self._get_sample_te_xml()
        data = self.parser.parse_xml_file(xml)

        # Validate document type
        self.assertEqual(data['document_type'], 'TE', "Should detect TE document type")

        # Validate clave
        self.assertEqual(
            data['clave'],
            '50604012400010001234567890123456789012345678901',
            "Should extract correct clave"
        )

        # Validate consecutive
        self.assertEqual(
            data['consecutive'],
            '001-00001-04-0000000001',
            "Should extract correct consecutive"
        )

    def test_detect_document_type(self):
        """Test document type detection from XML root element."""
        from lxml import etree

        # Test FE detection
        fe_xml = self._get_sample_fe_xml()
        fe_root = etree.fromstring(fe_xml.encode('utf-8'))
        fe_type = self.parser._detect_document_type(fe_root)
        self.assertEqual(fe_type, 'FE', "Should detect FE from FacturaElectronica")

        # Test TE detection
        te_xml = self._get_sample_te_xml()
        te_root = etree.fromstring(te_xml.encode('utf-8'))
        te_type = self.parser._detect_document_type(te_root)
        self.assertEqual(te_type, 'TE', "Should detect TE from TiqueteElectronico")

    def test_extract_clave(self):
        """Test clave extraction and validation."""
        xml = self._get_sample_fe_xml()
        data = self.parser.parse_xml_file(xml)

        # Validate clave format (50 digits)
        self.assertEqual(len(data['clave']), 50, "Clave should be 50 digits")
        self.assertTrue(data['clave'].isdigit(), "Clave should contain only digits")

    def test_extract_clave_invalid(self):
        """Test that invalid clave raises error."""
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>12345</Clave>
    <NumeroConsecutivo>001-00001-01-0000000001</NumeroConsecutivo>
    <FechaEmision>2024-01-15T10:30:00-06:00</FechaEmision>
    <Emisor>
        <Nombre>Test</Nombre>
        <Identificacion><Tipo>02</Tipo><Numero>3101234567</Numero></Identificacion>
    </Emisor>
</FacturaElectronica>"""

        with self.assertRaises(ValidationError):
            self.parser.parse_xml_file(invalid_xml)

    def test_extract_consecutive(self):
        """Test consecutive extraction and validation."""
        xml = self._get_sample_fe_xml()
        data = self.parser.parse_xml_file(xml)

        # Validate consecutive format
        consecutive = data['consecutive']
        parts = consecutive.split('-')
        self.assertEqual(len(parts), 4, "Consecutive should have 4 parts")
        self.assertEqual(len(parts[0]), 3, "Establishment should be 3 digits")
        self.assertEqual(len(parts[1]), 5, "Terminal should be 5 digits")
        self.assertEqual(len(parts[2]), 2, "Doc type should be 2 digits")
        self.assertEqual(len(parts[3]), 10, "Sequence should be 10 digits")

    def test_extract_emisor(self):
        """Test emisor (company) data extraction."""
        xml = self._get_sample_fe_xml()
        data = self.parser.parse_xml_file(xml)

        emisor = data['emisor']
        self.assertIsNotNone(emisor, "Should extract emisor data")

        # Validate identification
        self.assertEqual(emisor['id_type'], '02', "Should extract emisor ID type")
        self.assertEqual(emisor['id_number'], '3101234567', "Should extract emisor ID number")

        # Validate name
        self.assertEqual(emisor['name'], 'Empresa de Prueba SA', "Should extract emisor name")
        self.assertEqual(
            emisor['commercial_name'],
            'Empresa Prueba',
            "Should extract commercial name"
        )

        # Validate contact info
        self.assertEqual(emisor['email'], 'emisor@example.com', "Should extract emisor email")
        self.assertIn('506', emisor['phone'], "Should extract phone with country code")

        # Validate location
        self.assertIsNotNone(emisor['location'], "Should extract emisor location")
        self.assertEqual(emisor['location']['provincia'], '1', "Should extract provincia")

    def test_extract_receptor(self):
        """Test receptor (customer) data extraction."""
        xml = self._get_sample_fe_xml()
        data = self.parser.parse_xml_file(xml)

        receptor = data['receptor']
        self.assertIsNotNone(receptor, "Should extract receptor data")

        # Validate identification
        self.assertEqual(receptor['id_type'], '01', "Should extract receptor ID type")
        self.assertEqual(receptor['id_number'], '104560789', "Should extract receptor ID number")

        # Validate name
        self.assertEqual(receptor['name'], 'Cliente de Prueba', "Should extract receptor name")

        # Validate contact info
        self.assertEqual(receptor['email'], 'receptor@example.com', "Should extract receptor email")

    def test_extract_receptor_optional_in_tiquete(self):
        """Test that receptor is optional in Tiquete Electrónico."""
        xml = self._get_sample_te_xml()
        data = self.parser.parse_xml_file(xml)

        # TE doesn't have Receptor in this sample
        self.assertIsNone(data['receptor'], "Receptor should be None for TE without customer")

    def test_extract_payment_condition(self):
        """Test payment condition extraction."""
        xml = self._get_sample_fe_xml()
        data = self.parser.parse_xml_file(xml)

        self.assertEqual(
            data['payment_condition'],
            '01',
            "Should extract payment condition (01 = Contado)"
        )

    def test_extract_payment_method(self):
        """Test payment method extraction."""
        xml = self._get_sample_fe_xml()
        data = self.parser.parse_xml_file(xml)

        self.assertEqual(
            data['payment_method'],
            '01',
            "Should extract payment method (01 = Efectivo)"
        )

    def test_extract_date_various_formats(self):
        """Test date extraction with different ISO formats."""
        # Test with timezone
        xml1 = self._get_sample_fe_xml()
        data1 = self.parser.parse_xml_file(xml1)
        self.assertEqual(data1['date'], date(2024, 1, 15), "Should parse date with timezone")

        # Test with Z (UTC)
        xml2 = xml1.replace('2024-01-15T10:30:00-06:00', '2024-01-15T16:30:00Z')
        data2 = self.parser.parse_xml_file(xml2)
        self.assertEqual(data2['date'], date(2024, 1, 15), "Should parse date with Z timezone")

    def test_missing_clave_raises_error(self):
        """Test that missing Clave raises ValidationError."""
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <NumeroConsecutivo>001-00001-01-0000000001</NumeroConsecutivo>
    <FechaEmision>2024-01-15T10:30:00-06:00</FechaEmision>
</FacturaElectronica>"""

        with self.assertRaises(ValidationError):
            self.parser.parse_xml_file(invalid_xml)

    def test_missing_consecutive_raises_error(self):
        """Test that missing NumeroConsecutivo raises ValidationError."""
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012400010001234567890123456789012345678901</Clave>
    <FechaEmision>2024-01-15T10:30:00-06:00</FechaEmision>
</FacturaElectronica>"""

        with self.assertRaises(ValidationError):
            self.parser.parse_xml_file(invalid_xml)

    def test_missing_emisor_raises_error(self):
        """Test that missing Emisor raises ValidationError."""
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012400010001234567890123456789012345678901</Clave>
    <NumeroConsecutivo>001-00001-01-0000000001</NumeroConsecutivo>
    <FechaEmision>2024-01-15T10:30:00-06:00</FechaEmision>
</FacturaElectronica>"""

        with self.assertRaises(ValidationError):
            self.parser.parse_xml_file(invalid_xml)

    def test_invalid_xml_syntax_raises_error(self):
        """Test that malformed XML raises ValidationError."""
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica">
    <Clave>50601012400010001234567890123456789012345678901
    <NumeroConsecutivo>001-00001-01-0000000001</NumeroConsecutivo>
</FacturaElectronica>"""

        with self.assertRaises(ValidationError):
            self.parser.parse_xml_file(invalid_xml)

    def test_original_xml_stored(self):
        """Test that original XML is stored in base64."""
        xml = self._get_sample_fe_xml()
        data = self.parser.parse_xml_file(xml)

        # Should have original_xml field
        self.assertIn('original_xml', data, "Should store original XML")
        self.assertIsNotNone(data['original_xml'], "Original XML should not be None")

        # Verify it's base64 encoded
        import base64
        try:
            decoded = base64.b64decode(data['original_xml'])
            self.assertIn(b'FacturaElectronica', decoded, "Should contain original XML content")
        except Exception:
            self.fail("Original XML should be valid base64")

    def test_get_namespace(self):
        """Test namespace retrieval for different document types."""
        fe_ns = self.parser._get_namespace('FE')
        self.assertIn('facturaElectronica', fe_ns, "Should return FE namespace")

        te_ns = self.parser._get_namespace('TE')
        self.assertIn('tiqueteElectronico', te_ns, "Should return TE namespace")

        nc_ns = self.parser._get_namespace('NC')
        self.assertIn('notaCreditoElectronica', nc_ns, "Should return NC namespace")

        nd_ns = self.parser._get_namespace('ND')
        self.assertIn('notaDebitoElectronica', nd_ns, "Should return ND namespace")

    def test_validate_invoice_data(self):
        """Test invoice data validation."""
        xml = self._get_sample_fe_xml()
        data = self.parser.parse_xml_file(xml)

        # Should not raise error for valid data
        result = self.parser._validate_invoice_data(data)
        self.assertTrue(result, "Should validate correct invoice data")
