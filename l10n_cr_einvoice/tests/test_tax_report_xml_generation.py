# -*- coding: utf-8 -*-
"""
Comprehensive tests for Tax Report XML Generation (Phase 9C)
Tests XML structure, formatting, and validation for D-150, D-101, D-151
"""
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
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


from lxml import etree
from datetime import date


@tagged('post_install', '-at_install', 'tax_reports')
class TestTaxReportXMLGeneration(TransactionCase):
    """Test XML generation for all tax report types."""

    def setUp(self):
        super(TestTaxReportXMLGeneration, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Gym Costa Rica',
            'country_id': self.env.ref('base.cr').id,
            'vat': _generate_unique_vat_company(),
            'email': _generate_unique_email('company'),
            'phone': '22001100',
        })

        self.env.user.company_id = self.company

        # Get XML generator
        self.XMLGenerator = self.env['l10n_cr.tax.report.xml.generator']

    def _parse_xml(self, xml_str):
        """Helper to parse and validate XML structure."""
        try:
            root = etree.fromstring(xml_str.encode('utf-8'))
            return root
        except etree.XMLSyntaxError as e:
            self.fail(f"Invalid XML syntax: {str(e)}")

    def _get_xml_namespaces(self, root):
        """Get XML namespaces from root element."""
        nsmap = root.nsmap
        if None in nsmap:
            return {'ns': nsmap[None]}
        return {}

    # =====================================================
    # D-150 VAT REPORT XML GENERATION TESTS
    # =====================================================

    def test_d150_xml_basic_structure(self):
        """Test D-150 XML contains all required root elements."""
        # Create period
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        # Create D-150 report
        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        # Generate XML
        xml_str = self.XMLGenerator.generate_d150_xml(d150)
        root = self._parse_xml(xml_str)

        # Check root element
        self.assertEqual(root.tag, 'D150')

        # Check required child elements exist
        required_elements = ['Periodo', 'Contribuyente', 'Ventas', 'Compras', 'Liquidacion']
        for elem_name in required_elements:
            elem = root.find(elem_name)
            self.assertIsNotNone(elem, f"Missing required element: {elem_name}")

    def test_d150_xml_period_information(self):
        """Test D-150 period information is correctly formatted."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        xml_str = self.XMLGenerator.generate_d150_xml(d150)
        root = self._parse_xml(xml_str)

        # Check period
        periodo = root.find('Periodo')
        self.assertIsNotNone(periodo)

        anio = periodo.find('Anio')
        self.assertEqual(anio.text, '2025')

        mes = periodo.find('Mes')
        self.assertEqual(mes.text, '11')

    def test_d150_xml_company_identification(self):
        """Test company identification in D-150 XML."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        xml_str = self.XMLGenerator.generate_d150_xml(d150)
        root = self._parse_xml(xml_str)

        # Check company info
        contribuyente = root.find('Contribuyente')
        self.assertIsNotNone(contribuyente)

        identificacion = contribuyente.find('Identificacion')
        tipo = identificacion.find('Tipo')
        self.assertEqual(tipo.text, '02', "Should be type 02 for legal entity")

        numero = identificacion.find('Numero')
        self.assertEqual(numero.text, self.company.vat, "Should match company VAT")

        nombre = contribuyente.find('Nombre')
        self.assertEqual(nombre.text, 'Test Gym Costa Rica')

    def test_d150_xml_sales_section(self):
        """Test D-150 sales section with various tax rates."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 1000000.00,
            'sales_13_tax': 130000.00,
            'sales_4_base': 500000.00,
            'sales_4_tax': 20000.00,
            'sales_exempt': 100000.00,
        })

        xml_str = self.XMLGenerator.generate_d150_xml(d150)
        root = self._parse_xml(xml_str)

        ventas = root.find('Ventas')
        self.assertIsNotNone(ventas)

        # Check 13% rate
        tarifa_13 = ventas.find('Tarifa13')
        self.assertIsNotNone(tarifa_13)
        base_13 = tarifa_13.find('BaseImponible')
        self.assertEqual(base_13.text, '1000000.00')
        impuesto_13 = tarifa_13.find('Impuesto')
        self.assertEqual(impuesto_13.text, '130000.00')

        # Check 4% rate
        tarifa_4 = ventas.find('Tarifa4')
        self.assertIsNotNone(tarifa_4)
        base_4 = tarifa_4.find('BaseImponible')
        self.assertEqual(base_4.text, '500000.00')

        # Check exempt sales
        exentas = ventas.find('VentasExentas')
        self.assertIsNotNone(exentas)
        self.assertEqual(exentas.text, '100000.00')

    def test_d150_xml_purchases_section(self):
        """Test D-150 purchases section."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'purchases_goods_13_base': 300000.00,
            'purchases_goods_13_tax': 39000.00,
            'purchases_services_13_base': 200000.00,
            'purchases_services_13_tax': 26000.00,
        })

        xml_str = self.XMLGenerator.generate_d150_xml(d150)
        root = self._parse_xml(xml_str)

        compras = root.find('Compras')
        self.assertIsNotNone(compras)

        # Check goods purchases
        bienes_13 = compras.find('Bienes13')
        self.assertIsNotNone(bienes_13)
        bienes_base = bienes_13.find('BaseImponible')
        self.assertEqual(bienes_base.text, '300000.00')

        # Check services purchases
        servicios_13 = compras.find('Servicios13')
        self.assertIsNotNone(servicios_13)
        servicios_base = servicios_13.find('BaseImponible')
        self.assertEqual(servicios_base.text, '200000.00')

    def test_d150_xml_settlement_section(self):
        """Test D-150 liquidation/settlement section."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 1000000.00,
            'sales_13_tax': 130000.00,
            'purchases_goods_13_base': 300000.00,
            'purchases_goods_13_tax': 39000.00,
        })

        # Trigger computation
        d150._compute_sales_totals()
        d150._compute_purchases_totals()
        d150._compute_settlement()

        xml_str = self.XMLGenerator.generate_d150_xml(d150)
        root = self._parse_xml(xml_str)

        liquidacion = root.find('Liquidacion')
        self.assertIsNotNone(liquidacion)

        iva_generado = liquidacion.find('IVAGenerado')
        self.assertIsNotNone(iva_generado)

        iva_soportado = liquidacion.find('IVASoportado')
        self.assertIsNotNone(iva_soportado)

    def test_d150_xml_amount_formatting(self):
        """Test that amounts are properly formatted (2 decimals)."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 1234567.89,
            'sales_13_tax': 160493.43,
        })

        xml_str = self.XMLGenerator.generate_d150_xml(d150)
        root = self._parse_xml(xml_str)

        ventas = root.find('Ventas')
        tarifa_13 = ventas.find('Tarifa13')
        base_13 = tarifa_13.find('BaseImponible')

        # Should have exactly 2 decimal places
        self.assertEqual(base_13.text, '1234567.89')
        self.assertIn('.', base_13.text)
        decimals = base_13.text.split('.')[1]
        self.assertEqual(len(decimals), 2)

    def test_d150_xml_zero_amounts(self):
        """Test D-150 XML handles zero amounts correctly."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_13_base': 0.0,
            'sales_13_tax': 0.0,
        })

        xml_str = self.XMLGenerator.generate_d150_xml(d150)
        root = self._parse_xml(xml_str)

        # Zero amounts should not create elements
        ventas = root.find('Ventas')
        tarifa_13 = ventas.find('Tarifa13')
        self.assertIsNone(tarifa_13, "Zero amounts should not generate XML elements")

    def test_d150_xml_metadata(self):
        """Test D-150 XML includes metadata section."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        xml_str = self.XMLGenerator.generate_d150_xml(d150)
        root = self._parse_xml(xml_str)

        metadata = root.find('Metadata')
        self.assertIsNotNone(metadata)

        fecha = metadata.find('FechaGeneracion')
        self.assertIsNotNone(fecha)
        # Should be ISO format with timezone
        self.assertIn('T', fecha.text)
        self.assertIn('-06:00', fecha.text)

    # =====================================================
    # D-101 INCOME TAX REPORT XML GENERATION TESTS
    # =====================================================

    def test_d101_xml_basic_structure(self):
        """Test D-101 XML contains all required elements."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        xml_str = self.XMLGenerator.generate_d101_xml(d101)
        root = self._parse_xml(xml_str)

        # Handle namespace
        ns = self._get_xml_namespaces(root)
        if ns:
            self.assertTrue(root.tag.endswith('D101'))
        else:
            self.assertEqual(root.tag, 'D101')

        required_elements = ['Periodo', 'Contribuyente', 'IngresosBrutos',
                            'GastosDeducibles', 'RentaNeta', 'Impuesto', 'Liquidacion']
        for elem_name in required_elements:
            elem = root.find(elem_name, ns) if ns else root.find(elem_name)
            self.assertIsNotNone(elem, f"Missing required element: {elem_name}")

    def test_d101_xml_income_section(self):
        """Test D-101 gross income section."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 50000000.00,
            'other_income': 5000000.00,
        })

        xml_str = self.XMLGenerator.generate_d101_xml(d101)
        root = self._parse_xml(xml_str)

        # Handle namespace
        ns = self._get_xml_namespaces(root)

        ingresos = root.find('ns:IngresosBrutos', ns) if ns else root.find('IngresosBrutos')
        self.assertIsNotNone(ingresos)

        ventas = ingresos.find('ns:VentasServicios', ns) if ns else ingresos.find('VentasServicios')
        self.assertEqual(ventas.text, '50000000.00')

        otros = ingresos.find('ns:OtrosIngresos', ns) if ns else ingresos.find('OtrosIngresos')
        self.assertEqual(otros.text, '5000000.00')

    def test_d101_xml_expenses_section(self):
        """Test D-101 deductible expenses section."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'cost_of_goods_sold': 10000000.00,
            'operating_expenses': 15000000.00,
            'depreciation': 2000000.00,
        })

        xml_str = self.XMLGenerator.generate_d101_xml(d101)
        root = self._parse_xml(xml_str)

        # Handle namespace
        ns = self._get_xml_namespaces(root)

        gastos = root.find('ns:GastosDeducibles', ns) if ns else root.find('GastosDeducibles')
        self.assertIsNotNone(gastos)

        costo = gastos.find('ns:CostoVentas', ns) if ns else gastos.find('CostoVentas')
        self.assertEqual(costo.text, '10000000.00')

        operacion = gastos.find('ns:GastosOperacion', ns) if ns else gastos.find('GastosOperacion')
        self.assertEqual(operacion.text, '15000000.00')

        depreciacion = gastos.find('ns:Depreciacion', ns) if ns else gastos.find('Depreciacion')
        self.assertEqual(depreciacion.text, '2000000.00')

    def test_d101_xml_tax_brackets(self):
        """Test D-101 progressive tax bracket calculation."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd101',
            'year': 2025,
            'company_id': self.company.id,
        })

        d101 = self.env['l10n_cr.d101.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
            'sales_revenue': 20000000.00,
            'operating_expenses': 8000000.00,
        })

        # Trigger computations
        d101._compute_gross_income()
        d101._compute_deductible_expenses()
        d101._compute_taxable_income()
        d101._compute_income_tax()

        xml_str = self.XMLGenerator.generate_d101_xml(d101)
        root = self._parse_xml(xml_str)

        # Handle namespace
        ns = self._get_xml_namespaces(root)

        impuesto = root.find('ns:Impuesto', ns) if ns else root.find('Impuesto')
        self.assertIsNotNone(impuesto)

        # Should have tax brackets based on taxable income
        total_impuesto = impuesto.find('ns:TotalImpuesto', ns) if ns else impuesto.find('TotalImpuesto')
        self.assertIsNotNone(total_impuesto)

    # =====================================================
    # D-151 INFORMATIVE REPORT XML GENERATION TESTS
    # =====================================================

    def test_d151_xml_basic_structure(self):
        """Test D-151 XML contains all required elements."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        xml_str = self.XMLGenerator.generate_d151_xml(d151)
        root = self._parse_xml(xml_str)

        # Handle namespaced tag
        self.assertTrue(root.tag.endswith('D151'), f"Expected tag ending with 'D151', got: {root.tag}")

        # Handle namespace in element finding
        ns = self._get_xml_namespaces(root)

        required_elements = ['Periodo', 'Contribuyente', 'Configuracion', 'Resumen']
        for elem_name in required_elements:
            elem = root.find(f'ns:{elem_name}', ns) if ns else root.find(elem_name)
            self.assertIsNotNone(elem, f"Missing required element: {elem_name}")

    def test_d151_xml_customer_lines(self):
        """Test D-151 customer transaction lines."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        # Create test customer partner
        customer = self.env['res.partner'].create({
            'name': 'Juan Pérez',
            'vat': '109876543',
            'country_id': self.env.ref('base.cr').id,
        })

        # Add customer line
        self.env['l10n_cr.d151.customer.line'].create({
            'report_id': d151.id,
            'partner_id': customer.id,
            'partner_vat': '109876543',
            'partner_name': 'Juan Pérez',
            'total_amount': 5000000.00,
            'transaction_count': 12,
        })

        xml_str = self.XMLGenerator.generate_d151_xml(d151)
        root = self._parse_xml(xml_str)

        # Handle namespace
        ns = self._get_xml_namespaces(root)

        clientes = root.find('ns:Clientes', ns) if ns else root.find('Clientes')
        self.assertIsNotNone(clientes)

        cliente = clientes.find('ns:Cliente', ns) if ns else clientes.find('Cliente')
        self.assertIsNotNone(cliente)

        nombre = cliente.find('ns:Nombre', ns) if ns else cliente.find('Nombre')
        self.assertEqual(nombre.text, 'Juan Pérez')

        monto = cliente.find('ns:MontoTotal', ns) if ns else cliente.find('MontoTotal')
        self.assertEqual(monto.text, '5000000.00')

    def test_d151_xml_supplier_lines(self):
        """Test D-151 supplier transaction lines."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd151',
            'year': 2025,
            'company_id': self.company.id,
        })

        d151 = self.env['l10n_cr.d151.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        # Create test supplier partner
        supplier = self.env['res.partner'].create({
            'name': 'Proveedor ABC SA',
            'vat': '3102345678',
            'country_id': self.env.ref('base.cr').id,
        })

        # Add supplier line
        self.env['l10n_cr.d151.supplier.line'].create({
            'report_id': d151.id,
            'partner_id': supplier.id,
            'partner_vat': '3102345678',
            'partner_name': 'Proveedor ABC SA',
            'total_amount': 8000000.00,
            'transaction_count': 8,
        })

        xml_str = self.XMLGenerator.generate_d151_xml(d151)
        root = self._parse_xml(xml_str)

        # Handle namespace
        ns = self._get_xml_namespaces(root)

        proveedores = root.find('ns:Proveedores', ns) if ns else root.find('Proveedores')
        self.assertIsNotNone(proveedores)

        proveedor = proveedores.find('ns:Proveedor', ns) if ns else proveedores.find('Proveedor')
        self.assertIsNotNone(proveedor)

        nombre = proveedor.find('ns:Nombre', ns) if ns else proveedor.find('Nombre')
        self.assertEqual(nombre.text, 'Proveedor ABC SA')

    def test_d151_xml_id_type_detection(self):
        """Test D-151 ID type detection from VAT format."""
        # Física (9 digits)
        id_type = self.XMLGenerator._detect_id_type('123456789')
        self.assertEqual(id_type, '01')

        # Jurídica (10 digits)
        id_type = self.XMLGenerator._detect_id_type('3101234567')
        self.assertEqual(id_type, '02')

        # DIMEX (11-12 digits)
        id_type = self.XMLGenerator._detect_id_type('12345678901')
        self.assertEqual(id_type, '03')

        # Extranjero (other)
        id_type = self.XMLGenerator._detect_id_type('ABC123')
        self.assertEqual(id_type, '05')

        # Empty/None
        id_type = self.XMLGenerator._detect_id_type('')
        self.assertEqual(id_type, '05')

    # =====================================================
    # ERROR HANDLING TESTS
    # =====================================================

    def test_xml_generation_without_period(self):
        """Test error when creating report without period (database constraint)."""
        # period_id is required=True at the model level, creating NOT NULL constraint
        # Attempting to create without period_id should raise a database exception
        with self.assertRaises(Exception):  # Will be psycopg2.errors.NotNullViolation
            self.env['l10n_cr.d150.report'].create({
                'company_id': self.company.id,
            })

    def test_xml_validation(self):
        """Test XML validation helper."""
        period = self.env['l10n_cr.tax.report.period'].create({
            'report_type': 'd150',
            'year': 2025,
            'month': 11,
            'company_id': self.company.id,
        })

        d150 = self.env['l10n_cr.d150.report'].create({
            'period_id': period.id,
            'company_id': self.company.id,
        })

        xml_str = self.XMLGenerator.generate_d150_xml(d150)

        result = self.XMLGenerator.validate_xml_structure(xml_str, 'D150')

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_xml_validation_invalid_structure(self):
        """Test XML validation detects missing required elements."""
        invalid_xml = '<?xml version="1.0"?><D150><Periodo></Periodo></D150>'

        result = self.XMLGenerator.validate_xml_structure(invalid_xml, 'D150')

        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
