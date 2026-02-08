# -*- coding: utf-8 -*-
import logging
import base64
import re
from datetime import datetime
from lxml import etree

from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class EInvoiceXMLParser(models.AbstractModel):
    _name = 'l10n_cr.einvoice.xml.parser'
    _description = 'Costa Rica E-Invoice XML Parser v4.4'

    # XML Namespaces for v4.4
    NAMESPACES = {
        'fe': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica',
        'te': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/tiqueteElectronico',
        'nc': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaCreditoElectronica',
        'nd': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaDebitoElectronica',
        'ds': 'http://www.w3.org/2000/09/xmldsig#',
    }

    # Document type to namespace mapping
    DOCTYPE_NAMESPACES = {
        'FE': 'fe',
        'TE': 'te',
        'NC': 'nc',
        'ND': 'nd',
    }

    @api.model
    def parse_xml_file(self, xml_content):
        """
        Parse Costa Rica e-invoice XML v4.4 and extract all data.

        Args:
            xml_content: XML content as bytes or string

        Returns:
            dict: Extracted invoice data
        """
        try:
            # Parse XML
            if isinstance(xml_content, str):
                xml_content = xml_content.encode('utf-8')

            root = etree.fromstring(xml_content)

            # Detect document type from root element
            doc_type = self._detect_document_type(root)

            # Extract all data
            data = {
                'document_type': doc_type,
                'clave': self._extract_clave(root, doc_type),
                'consecutive': self._extract_consecutive(root, doc_type),
                'date': self._extract_date(root, doc_type),
                'activity_code': self._extract_activity_code(root, doc_type),
                'emisor': self._extract_emisor(root, doc_type),
                'receptor': self._extract_receptor(root, doc_type),
                'payment_condition': self._extract_payment_condition(root, doc_type),
                'payment_method': self._extract_payment_method(root, doc_type),
                'line_items': self._extract_line_items(root, doc_type),
                'summary': self._extract_summary(root, doc_type),
                'reference': self._extract_reference(root, doc_type) if doc_type in ['NC', 'ND'] else None,
                'original_xml': base64.b64encode(xml_content).decode('utf-8'),
            }

            # Validate extracted data
            self._validate_invoice_data(data)

            return data

        except etree.XMLSyntaxError as e:
            _logger.error(f'XML parsing error: {str(e)}')
            raise ValidationError(_('Invalid XML file: %s') % str(e))
        except Exception as e:
            _logger.error(f'Error parsing XML: {str(e)}')
            raise ValidationError(_('Error parsing XML file: %s') % str(e))

    @api.model
    def _detect_document_type(self, root):
        """Detect document type from XML root element."""
        tag = etree.QName(root.tag).localname

        if 'FacturaElectronica' in tag:
            return 'FE'
        elif 'TiqueteElectronico' in tag:
            return 'TE'
        elif 'NotaCreditoElectronica' in tag:
            return 'NC'
        elif 'NotaDebitoElectronica' in tag:
            return 'ND'
        else:
            raise ValidationError(_('Unknown document type in XML: %s') % tag)

    @api.model
    def _get_namespace(self, doc_type):
        """Get the namespace URI for a document type."""
        ns_key = self.DOCTYPE_NAMESPACES.get(doc_type)
        if not ns_key:
            raise ValidationError(_('Unknown document type: %s') % doc_type)
        return self.NAMESPACES[ns_key]

    @api.model
    def _extract_clave(self, root, doc_type):
        """Extract the 50-digit clave (unique key)."""
        ns = self._get_namespace(doc_type)
        clave_elem = root.find(f'{{{ns}}}Clave')

        if clave_elem is None or not clave_elem.text:
            raise ValidationError(_('Missing Clave in XML'))

        clave = clave_elem.text.strip()

        # Validate clave format (50 digits)
        if not re.match(r'^\d{50}$', clave):
            raise ValidationError(_('Invalid Clave format: must be 50 digits'))

        return clave

    @api.model
    def _extract_consecutive(self, root, doc_type):
        """Extract the consecutive number."""
        ns = self._get_namespace(doc_type)
        consecutivo_elem = root.find(f'{{{ns}}}NumeroConsecutivo')

        if consecutivo_elem is None or not consecutivo_elem.text:
            raise ValidationError(_('Missing NumeroConsecutivo in XML'))

        consecutive = consecutivo_elem.text.strip()

        # Validate format: XXX-XXXXX-XX-XXXXXXXXXX (establishment-terminal-doctype-sequence)
        if not re.match(r'^\d{3}-\d{5}-\d{2}-\d{10}$', consecutive):
            _logger.warning(f'Consecutive number has non-standard format: {consecutive}')

        return consecutive

    @api.model
    def _extract_date(self, root, doc_type):
        """Extract the emission date."""
        ns = self._get_namespace(doc_type)
        fecha_elem = root.find(f'{{{ns}}}FechaEmision')

        if fecha_elem is None or not fecha_elem.text:
            raise ValidationError(_('Missing FechaEmision in XML'))

        fecha_str = fecha_elem.text.strip()

        # Parse ISO format datetime
        try:
            # Handle both with and without timezone
            if '+' in fecha_str or fecha_str.endswith('Z'):
                # Remove timezone for parsing
                fecha_str = fecha_str.split('+')[0].split('Z')[0]

            fecha_dt = datetime.fromisoformat(fecha_str)
            return fecha_dt.date()

        except ValueError as e:
            raise ValidationError(_('Invalid date format in FechaEmision: %s') % str(e))

    @api.model
    def _extract_activity_code(self, root, doc_type):
        """Extract the economic activity code (CIIU)."""
        ns = self._get_namespace(doc_type)
        codigo_elem = root.find(f'{{{ns}}}CodigoActividad')

        # CodigoActividad is optional in some document types
        if codigo_elem is not None and codigo_elem.text:
            return codigo_elem.text.strip()

        return None

    @api.model
    def _extract_emisor(self, root, doc_type):
        """Extract emisor (sender/company) information."""
        ns = self._get_namespace(doc_type)
        emisor_elem = root.find(f'{{{ns}}}Emisor')

        if emisor_elem is None:
            raise ValidationError(_('Missing Emisor in XML'))

        emisor_data = {}

        # Identification
        identificacion = emisor_elem.find(f'{{{ns}}}Identificacion')
        if identificacion is not None:
            tipo_elem = identificacion.find(f'{{{ns}}}Tipo')
            numero_elem = identificacion.find(f'{{{ns}}}Numero')

            if tipo_elem is not None and numero_elem is not None:
                emisor_data['id_type'] = tipo_elem.text.strip() if tipo_elem.text else None
                emisor_data['id_number'] = numero_elem.text.strip() if numero_elem.text else None

        # Name
        nombre_elem = emisor_elem.find(f'{{{ns}}}Nombre')
        if nombre_elem is not None and nombre_elem.text:
            emisor_data['name'] = nombre_elem.text.strip()

        # Commercial name (optional)
        nombre_comercial_elem = emisor_elem.find(f'{{{ns}}}NombreComercial')
        if nombre_comercial_elem is not None and nombre_comercial_elem.text:
            emisor_data['commercial_name'] = nombre_comercial_elem.text.strip()

        # Location
        ubicacion = emisor_elem.find(f'{{{ns}}}Ubicacion')
        if ubicacion is not None:
            emisor_data['location'] = self._extract_location(ubicacion, ns)

        # Phone (optional)
        telefono = emisor_elem.find(f'{{{ns}}}Telefono')
        if telefono is not None:
            codigo_pais = telefono.find(f'{{{ns}}}CodigoPais')
            num_telefono = telefono.find(f'{{{ns}}}NumTelefono')

            phone_parts = []
            if codigo_pais is not None and codigo_pais.text:
                phone_parts.append(codigo_pais.text.strip())
            if num_telefono is not None and num_telefono.text:
                phone_parts.append(num_telefono.text.strip())

            if phone_parts:
                emisor_data['phone'] = ' '.join(phone_parts)

        # Email
        correo_elem = emisor_elem.find(f'{{{ns}}}CorreoElectronico')
        if correo_elem is not None and correo_elem.text:
            emisor_data['email'] = correo_elem.text.strip()

        return emisor_data

    @api.model
    def _extract_receptor(self, root, doc_type):
        """Extract receptor (customer) information."""
        ns = self._get_namespace(doc_type)
        receptor_elem = root.find(f'{{{ns}}}Receptor')

        # Receptor is optional in Tiquete Electrónico
        if receptor_elem is None:
            return None

        receptor_data = {}

        # Identification
        identificacion = receptor_elem.find(f'{{{ns}}}Identificacion')
        if identificacion is not None:
            tipo_elem = identificacion.find(f'{{{ns}}}Tipo')
            numero_elem = identificacion.find(f'{{{ns}}}Numero')

            if tipo_elem is not None and numero_elem is not None:
                receptor_data['id_type'] = tipo_elem.text.strip() if tipo_elem.text else None
                receptor_data['id_number'] = numero_elem.text.strip() if numero_elem.text else None

        # Name (optional for foreign customers)
        nombre_elem = receptor_elem.find(f'{{{ns}}}Nombre')
        if nombre_elem is not None and nombre_elem.text:
            receptor_data['name'] = nombre_elem.text.strip()

        # Commercial name (optional)
        nombre_comercial_elem = receptor_elem.find(f'{{{ns}}}NombreComercial')
        if nombre_comercial_elem is not None and nombre_comercial_elem.text:
            receptor_data['commercial_name'] = nombre_comercial_elem.text.strip()

        # Location (optional)
        ubicacion = receptor_elem.find(f'{{{ns}}}Ubicacion')
        if ubicacion is not None:
            receptor_data['location'] = self._extract_location(ubicacion, ns)

        # Phone (optional)
        telefono = receptor_elem.find(f'{{{ns}}}Telefono')
        if telefono is not None:
            codigo_pais = telefono.find(f'{{{ns}}}CodigoPais')
            num_telefono = telefono.find(f'{{{ns}}}NumTelefono')

            phone_parts = []
            if codigo_pais is not None and codigo_pais.text:
                phone_parts.append(codigo_pais.text.strip())
            if num_telefono is not None and num_telefono.text:
                phone_parts.append(num_telefono.text.strip())

            if phone_parts:
                receptor_data['phone'] = ' '.join(phone_parts)

        # Email
        correo_elem = receptor_elem.find(f'{{{ns}}}CorreoElectronico')
        if correo_elem is not None and correo_elem.text:
            receptor_data['email'] = correo_elem.text.strip()

        return receptor_data

    @api.model
    def _extract_location(self, ubicacion_elem, ns):
        """Extract location information."""
        location = {}

        provincia_elem = ubicacion_elem.find(f'{{{ns}}}Provincia')
        if provincia_elem is not None and provincia_elem.text:
            location['provincia'] = provincia_elem.text.strip()

        canton_elem = ubicacion_elem.find(f'{{{ns}}}Canton')
        if canton_elem is not None and canton_elem.text:
            location['canton'] = canton_elem.text.strip()

        distrito_elem = ubicacion_elem.find(f'{{{ns}}}Distrito')
        if distrito_elem is not None and distrito_elem.text:
            location['distrito'] = distrito_elem.text.strip()

        barrio_elem = ubicacion_elem.find(f'{{{ns}}}Barrio')
        if barrio_elem is not None and barrio_elem.text:
            location['barrio'] = barrio_elem.text.strip()

        otras_senas_elem = ubicacion_elem.find(f'{{{ns}}}OtrasSenas')
        if otras_senas_elem is not None and otras_senas_elem.text:
            location['otras_senas'] = otras_senas_elem.text.strip()

        return location

    @api.model
    def _extract_payment_condition(self, root, doc_type):
        """Extract payment condition (payment terms)."""
        ns = self._get_namespace(doc_type)
        condicion_elem = root.find(f'{{{ns}}}CondicionVenta')

        if condicion_elem is not None and condicion_elem.text:
            return condicion_elem.text.strip()

        return '01'  # Default: Contado (Cash)

    @api.model
    def _extract_payment_method(self, root, doc_type):
        """Extract payment method."""
        ns = self._get_namespace(doc_type)
        medio_elem = root.find(f'{{{ns}}}MedioPago')

        if medio_elem is not None and medio_elem.text:
            return medio_elem.text.strip()

        return '01'  # Default: Efectivo (Cash)

    @api.model
    def _extract_line_items(self, root, doc_type):
        """Extract line items (products/services)."""
        ns = self._get_namespace(doc_type)
        detalle_elem = root.find(f'{{{ns}}}DetalleServicio')

        if detalle_elem is None:
            return []

        line_items = []

        # Iterate through LineaDetalle elements
        for linea in detalle_elem.findall(f'{{{ns}}}LineaDetalle'):
            line_data = {}

            # Line number
            numero_linea = linea.find(f'{{{ns}}}NumeroLinea')
            if numero_linea is not None and numero_linea.text:
                line_data['line_number'] = int(numero_linea.text.strip())

            # Product code (Cabys)
            codigo_elem = linea.find(f'{{{ns}}}Codigo')
            if codigo_elem is not None:
                tipo_elem = codigo_elem.find(f'{{{ns}}}Tipo')
                codigo_producto = codigo_elem.find(f'{{{ns}}}Codigo')

                if tipo_elem is not None and tipo_elem.text:
                    line_data['code_type'] = tipo_elem.text.strip()
                if codigo_producto is not None and codigo_producto.text:
                    line_data['cabys_code'] = codigo_producto.text.strip()

            # Quantity
            cantidad_elem = linea.find(f'{{{ns}}}Cantidad')
            if cantidad_elem is not None and cantidad_elem.text:
                line_data['quantity'] = float(cantidad_elem.text.strip())

            # Unit of measure
            unidad_elem = linea.find(f'{{{ns}}}UnidadMedida')
            if unidad_elem is not None and unidad_elem.text:
                line_data['uom'] = unidad_elem.text.strip()

            # Description
            detalle_text_elem = linea.find(f'{{{ns}}}Detalle')
            if detalle_text_elem is not None and detalle_text_elem.text:
                line_data['description'] = detalle_text_elem.text.strip()

            # Unit price
            precio_elem = linea.find(f'{{{ns}}}PrecioUnitario')
            if precio_elem is not None and precio_elem.text:
                line_data['price_unit'] = float(precio_elem.text.strip())

            # Total (before discount)
            monto_total_elem = linea.find(f'{{{ns}}}MontoTotal')
            if monto_total_elem is not None and monto_total_elem.text:
                line_data['amount_total'] = float(monto_total_elem.text.strip())

            # Discount (optional)
            descuento_elem = linea.find(f'{{{ns}}}Descuento')
            if descuento_elem is not None:
                monto_desc = descuento_elem.find(f'{{{ns}}}MontoDescuento')
                naturaleza_desc = descuento_elem.find(f'{{{ns}}}NaturalezaDescuento')

                if monto_desc is not None and monto_desc.text:
                    line_data['discount_amount'] = float(monto_desc.text.strip())
                if naturaleza_desc is not None and naturaleza_desc.text:
                    line_data['discount_nature'] = naturaleza_desc.text.strip()

            # Subtotal (after discount)
            subtotal_elem = linea.find(f'{{{ns}}}SubTotal')
            if subtotal_elem is not None and subtotal_elem.text:
                line_data['subtotal'] = float(subtotal_elem.text.strip())

            # Taxes (optional)
            line_data['taxes'] = []
            impuesto_elem = linea.find(f'{{{ns}}}Impuesto')
            if impuesto_elem is not None:
                codigo_impuesto = impuesto_elem.find(f'{{{ns}}}Codigo')
                codigo_tarifa = impuesto_elem.find(f'{{{ns}}}CodigoTarifa')
                tarifa_elem = impuesto_elem.find(f'{{{ns}}}Tarifa')
                monto_impuesto = impuesto_elem.find(f'{{{ns}}}Monto')

                tax_data = {}
                if codigo_impuesto is not None and codigo_impuesto.text:
                    tax_data['code'] = codigo_impuesto.text.strip()
                if codigo_tarifa is not None and codigo_tarifa.text:
                    tax_data['rate_code'] = codigo_tarifa.text.strip()
                if tarifa_elem is not None and tarifa_elem.text:
                    tax_data['rate'] = float(tarifa_elem.text.strip())
                if monto_impuesto is not None and monto_impuesto.text:
                    tax_data['amount'] = float(monto_impuesto.text.strip())

                if tax_data:
                    line_data['taxes'].append(tax_data)

            # Total line (with taxes)
            monto_total_linea = linea.find(f'{{{ns}}}MontoTotalLinea')
            if monto_total_linea is not None and monto_total_linea.text:
                line_data['line_total'] = float(monto_total_linea.text.strip())

            line_items.append(line_data)

        return line_items

    @api.model
    def _extract_summary(self, root, doc_type):
        """Extract invoice summary (totals)."""
        ns = self._get_namespace(doc_type)
        resumen_elem = root.find(f'{{{ns}}}ResumenFactura')

        if resumen_elem is None:
            _logger.warning('No ResumenFactura found in XML')
            return {
                'total_merchandise': 0.0,
                'total_discount': 0.0,
                'subtotal': 0.0,
                'total_tax': 0.0,
                'total': 0.0,
            }

        summary = {}

        # Currency
        codigo_moneda_elem = resumen_elem.find(f'{{{ns}}}CodigoTipoMoneda')
        if codigo_moneda_elem is not None:
            moneda = codigo_moneda_elem.find(f'{{{ns}}}CodigoMoneda')
            tipo_cambio = codigo_moneda_elem.find(f'{{{ns}}}TipoCambio')

            if moneda is not None and moneda.text:
                summary['currency'] = moneda.text.strip()
            if tipo_cambio is not None and tipo_cambio.text:
                summary['exchange_rate'] = float(tipo_cambio.text.strip())

        # Services taxable
        total_serv_gravados = resumen_elem.find(f'{{{ns}}}TotalServGravados')
        if total_serv_gravados is not None and total_serv_gravados.text:
            summary['total_services_taxable'] = float(total_serv_gravados.text.strip())

        # Services exempt
        total_serv_exentos = resumen_elem.find(f'{{{ns}}}TotalServExentos')
        if total_serv_exentos is not None and total_serv_exentos.text:
            summary['total_services_exempt'] = float(total_serv_exentos.text.strip())

        # Merchandise taxable
        total_merc_gravadas = resumen_elem.find(f'{{{ns}}}TotalMercanciasGravadas')
        if total_merc_gravadas is not None and total_merc_gravadas.text:
            summary['total_merchandise_taxable'] = float(total_merc_gravadas.text.strip())

        # Merchandise exempt
        total_merc_exentas = resumen_elem.find(f'{{{ns}}}TotalMercanciasExentas')
        if total_merc_exentas is not None and total_merc_exentas.text:
            summary['total_merchandise_exempt'] = float(total_merc_exentas.text.strip())

        # Total taxable
        total_gravado = resumen_elem.find(f'{{{ns}}}TotalGravado')
        if total_gravado is not None and total_gravado.text:
            summary['total_taxable'] = float(total_gravado.text.strip())

        # Total exempt
        total_exento = resumen_elem.find(f'{{{ns}}}TotalExento')
        if total_exento is not None and total_exento.text:
            summary['total_exempt'] = float(total_exento.text.strip())

        # Total sale (before discounts)
        total_venta = resumen_elem.find(f'{{{ns}}}TotalVenta')
        if total_venta is not None and total_venta.text:
            summary['total_sale'] = float(total_venta.text.strip())

        # Total discounts
        total_descuentos = resumen_elem.find(f'{{{ns}}}TotalDescuentos')
        if total_descuentos is not None and total_descuentos.text:
            summary['total_discount'] = float(total_descuentos.text.strip())

        # Total sale net (after discounts, before tax)
        total_venta_neta = resumen_elem.find(f'{{{ns}}}TotalVentaNeta')
        if total_venta_neta is not None and total_venta_neta.text:
            summary['total_sale_net'] = float(total_venta_neta.text.strip())

        # Total tax
        total_impuesto = resumen_elem.find(f'{{{ns}}}TotalImpuesto')
        if total_impuesto is not None and total_impuesto.text:
            summary['total_tax'] = float(total_impuesto.text.strip())

        # Total invoice (net + tax)
        total_comprobante = resumen_elem.find(f'{{{ns}}}TotalComprobante')
        if total_comprobante is not None and total_comprobante.text:
            summary['total_invoice'] = float(total_comprobante.text.strip())

        return summary

    @api.model
    def _extract_reference(self, root, doc_type):
        """Extract reference information (for credit/debit notes)."""
        # Only for NC (Credit Notes) and ND (Debit Notes)
        if doc_type not in ['NC', 'ND']:
            return None

        ns = self._get_namespace(doc_type)
        info_ref_elem = root.find(f'{{{ns}}}InformacionReferencia')

        if info_ref_elem is None:
            _logger.warning(f'No InformacionReferencia found in {doc_type} XML')
            return None

        reference = {}

        # Document type
        tipo_doc = info_ref_elem.find(f'{{{ns}}}TipoDoc')
        if tipo_doc is not None and tipo_doc.text:
            reference['doc_type'] = tipo_doc.text.strip()

        # Reference number (consecutive of original invoice)
        numero = info_ref_elem.find(f'{{{ns}}}Numero')
        if numero is not None and numero.text:
            reference['number'] = numero.text.strip()

        # Emission date of referenced document
        fecha_emision = info_ref_elem.find(f'{{{ns}}}FechaEmision')
        if fecha_emision is not None and fecha_emision.text:
            try:
                fecha_str = fecha_emision.text.strip()
                # Handle both date and datetime formats
                if 'T' in fecha_str:
                    fecha_str = fecha_str.split('T')[0]
                reference['date'] = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError as e:
                _logger.warning(f'Could not parse reference date: {e}')

        # Reference code
        codigo = info_ref_elem.find(f'{{{ns}}}Codigo')
        if codigo is not None and codigo.text:
            reference['code'] = codigo.text.strip()

        # Reason
        razon = info_ref_elem.find(f'{{{ns}}}Razon')
        if razon is not None and razon.text:
            reference['reason'] = razon.text.strip()

        return reference

    @api.model
    def _validate_invoice_data(self, data):
        """Validate extracted invoice data for consistency."""
        # Validate clave
        if not data.get('clave'):
            raise ValidationError(_('Missing clave in invoice data'))

        # Validate consecutive
        if not data.get('consecutive'):
            raise ValidationError(_('Missing consecutive in invoice data'))

        # Validate consecutive matches clave
        # Positions 31-50 of clave should match consecutive (20 digits)
        clave = data['clave']
        consecutive_from_clave = clave[30:50]
        consecutive_digits = re.sub(r'\D', '', data['consecutive'])  # Remove non-digits
        consecutive_padded = consecutive_digits.zfill(20)

        if consecutive_from_clave != consecutive_padded:
            _logger.warning(
                f'Consecutive in Clave ({consecutive_from_clave}) does not match '
                f'NumeroConsecutivo ({consecutive_padded})'
            )

        # Validate date
        if not data.get('date'):
            raise ValidationError(_('Missing date in invoice data'))

        # Validate emisor
        if not data.get('emisor'):
            raise ValidationError(_('Missing emisor in invoice data'))

        _logger.info(f'Successfully validated invoice data for clave: {data["clave"]}')

        return True
