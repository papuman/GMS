# -*- coding: utf-8 -*-
import logging
from datetime import datetime, date
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class XMLGenerator(models.AbstractModel):
    _name = 'l10n_cr.xml.generator'
    _description = 'Costa Rica E-Invoice XML Generator v4.4'

    # XML Namespaces for v4.4
    NAMESPACES = {
        'fe': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica',
        'te': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/tiqueteElectronico',
        'nc': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaCreditoElectronica',
        'nd': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaDebitoElectronica',
        'ds': 'http://www.w3.org/2000/09/xmldsig#',
        'xsd': 'http://www.w3.org/2001/XMLSchema',
    }

    # CIIU mandatory deadline (October 6, 2025)
    CIIU_MANDATORY_DATE = date(2025, 10, 6)

    @api.model
    def generate_invoice_xml(self, einvoice):
        """
        Generate the complete XML for an electronic invoice.

        Args:
            einvoice: l10n_cr.einvoice.document record

        Returns:
            str: XML content
        """
        doc_type = einvoice.document_type
        move = einvoice.move_id

        # Select the appropriate generator method
        if doc_type == 'FE':
            return self._generate_factura_electronica(einvoice, move)
        elif doc_type == 'TE':
            return self._generate_tiquete_electronico(einvoice, move)
        elif doc_type == 'NC':
            return self._generate_nota_credito(einvoice, move)
        elif doc_type == 'ND':
            return self._generate_nota_debito(einvoice, move)
        else:
            raise ValidationError(_('Unknown document type: %s') % doc_type)

    def _generate_factura_electronica(self, einvoice, move):
        """Generate Factura Electrónica (FE) XML."""
        # Create root element with namespace
        ns = self.NAMESPACES['fe']
        root = etree.Element(
            '{%s}FacturaElectronica' % ns,
            nsmap={'': ns, 'ds': self.NAMESPACES['ds'], 'xsd': self.NAMESPACES['xsd']},
        )

        # 1. Clave (50-digit key)
        etree.SubElement(root, 'Clave').text = einvoice.clave

        # 2. CodigoActividad (economic activity code)
        codigo_actividad = move.company_id.l10n_cr_activity_code or '861201'
        etree.SubElement(root, 'CodigoActividad').text = codigo_actividad

        # 3. NumeroConsecutivo (consecutive number)
        numero = einvoice.name or ''
        etree.SubElement(root, 'NumeroConsecutivo').text = numero

        # 4. FechaEmision (emission date/time)
        fecha_emision = move.invoice_date or fields.Date.today()
        fecha_hora = datetime.combine(fecha_emision, datetime.now().time())
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.isoformat()

        # 5. Emisor (sender/company information)
        self._add_emisor(root, move.company_id)

        # 6. Receptor (receiver/customer information) - Updated for Phase 1C
        if move.partner_id:
            self._add_receptor(root, move.partner_id, move.invoice_date)

        # 7. CondicionVenta (payment terms)
        self._add_condicion_venta(root, move)

        # 8. MedioPago (payment method) - Updated for Phase 1A
        self._add_medio_pago(root, move)

        # 9. DetalleServicio (line items)
        self._add_detalle_servicio(root, move)

        # 10. ResumenFactura (invoice summary)
        self._add_resumen_factura(root, move)

        # Convert to string
        xml_str = etree.tostring(
            root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True,
        ).decode('utf-8')

        return xml_str

    def _generate_tiquete_electronico(self, einvoice, move):
        """Generate Tiquete Electrónico (TE) XML."""
        # Similar to FE but with simplified structure
        ns = self.NAMESPACES['te']
        root = etree.Element(
            '{%s}TiqueteElectronico' % ns,
            nsmap={'': ns, 'ds': self.NAMESPACES['ds']},
        )

        # Add basic elements (similar to FE but without Receptor for anonymous sales)
        etree.SubElement(root, 'Clave').text = einvoice.clave
        etree.SubElement(root, 'NumeroConsecutivo').text = einvoice.name or ''

        fecha_emision = move.invoice_date or fields.Date.today()
        fecha_hora = datetime.combine(fecha_emision, datetime.now().time())
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.isoformat()

        self._add_emisor(root, move.company_id)
        self._add_condicion_venta(root, move)
        self._add_medio_pago(root, move)
        self._add_detalle_servicio(root, move)
        self._add_resumen_factura(root, move)

        xml_str = etree.tostring(
            root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True,
        ).decode('utf-8')

        return xml_str

    def _generate_nota_credito(self, einvoice, move):
        """Generate Nota de Crédito (NC) XML."""
        ns = self.NAMESPACES['nc']
        root = etree.Element(
            '{%s}NotaCreditoElectronica' % ns,
            nsmap={'': ns, 'ds': self.NAMESPACES['ds']},
        )

        # Similar to FE with reference to original invoice
        etree.SubElement(root, 'Clave').text = einvoice.clave
        etree.SubElement(root, 'NumeroConsecutivo').text = einvoice.name or ''

        fecha_emision = move.invoice_date or fields.Date.today()
        fecha_hora = datetime.combine(fecha_emision, datetime.now().time())
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.isoformat()

        self._add_emisor(root, move.company_id)

        if move.partner_id:
            self._add_receptor(root, move.partner_id, move.invoice_date)

        # Reference to original invoice
        if move.reversed_entry_id:
            self._add_informacion_referencia(root, move.reversed_entry_id)

        self._add_condicion_venta(root, move)
        self._add_medio_pago(root, move)
        self._add_detalle_servicio(root, move)
        self._add_resumen_factura(root, move)

        xml_str = etree.tostring(
            root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True,
        ).decode('utf-8')

        return xml_str

    def _generate_nota_debito(self, einvoice, move):
        """Generate Nota de Débito (ND) XML."""
        # Very similar to NC
        ns = self.NAMESPACES['nd']
        root = etree.Element(
            '{%s}NotaDebitoElectronica' % ns,
            nsmap={'': ns, 'ds': self.NAMESPACES['ds']},
        )

        etree.SubElement(root, 'Clave').text = einvoice.clave
        etree.SubElement(root, 'NumeroConsecutivo').text = einvoice.name or ''

        fecha_emision = move.invoice_date or fields.Date.today()
        fecha_hora = datetime.combine(fecha_emision, datetime.now().time())
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.isoformat()

        self._add_emisor(root, move.company_id)

        if move.partner_id:
            self._add_receptor(root, move.partner_id, move.invoice_date)

        if move.debit_origin_id:
            self._add_informacion_referencia(root, move.debit_origin_id)

        self._add_condicion_venta(root, move)
        self._add_medio_pago(root, move)
        self._add_detalle_servicio(root, move)
        self._add_resumen_factura(root, move)

        xml_str = etree.tostring(
            root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True,
        ).decode('utf-8')

        return xml_str

    def _add_emisor(self, root, company):
        """Add Emisor (sender) section."""
        emisor = etree.SubElement(root, 'Emisor')

        # Company name
        nombre = company.name or ''
        etree.SubElement(emisor, 'Nombre').text = nombre

        # Identification
        identificacion = etree.SubElement(emisor, 'Identificacion')
        tipo_id = self._get_company_id_type(company.vat or '')
        etree.SubElement(identificacion, 'Tipo').text = tipo_id
        numero_id = (company.vat or '').replace('-', '').replace(' ', '')
        etree.SubElement(identificacion, 'Numero').text = numero_id

        # Commercial name (if different)
        if company.commercial_name:
            etree.SubElement(emisor, 'NombreComercial').text = company.commercial_name

        # Location
        ubicacion = etree.SubElement(emisor, 'Ubicacion')

        # Province, Canton, District, Neighborhood
        location_code = company.l10n_cr_emisor_location or '01010100'
        etree.SubElement(ubicacion, 'Provincia').text = location_code[0:1]
        etree.SubElement(ubicacion, 'Canton').text = location_code[1:3]
        etree.SubElement(ubicacion, 'Distrito').text = location_code[3:5]
        etree.SubElement(ubicacion, 'Barrio').text = location_code[5:7]

        # Address details
        if company.street:
            etree.SubElement(ubicacion, 'OtrasSenas').text = company.street

        # Contact info
        telefono = etree.SubElement(emisor, 'Telefono')
        etree.SubElement(telefono, 'CodigoPais').text = '506'
        phone = (company.phone or '').replace(' ', '').replace('-', '')
        etree.SubElement(telefono, 'NumTelefono').text = phone[:8] if phone else '00000000'

        if company.email:
            etree.SubElement(emisor, 'CorreoElectronico').text = company.email

    def _add_receptor(self, root, partner, invoice_date=None):
        """
        Add Receptor (receiver) section.

        Updated for Phase 1C: Recipient Economic Activity Field
        Includes ActividadEconomica tag (CIIU 4 code) per v4.4 spec.
        """
        receptor = etree.SubElement(root, 'Receptor')

        # Partner name
        etree.SubElement(receptor, 'Nombre').text = partner.name or ''

        # Identification
        if partner.vat:
            identificacion = etree.SubElement(receptor, 'Identificacion')
            tipo_id = self._get_partner_id_type(partner.vat)
            etree.SubElement(identificacion, 'Tipo').text = tipo_id
            numero_id = partner.vat.replace('-', '').replace(' ', '')
            etree.SubElement(identificacion, 'Numero').text = numero_id

        # Economic Activity (CIIU 4 code) - NEW for Phase 1C
        # Mandatory from October 6, 2025 per Resolution MH-DGT-RES-0027-2024
        if partner.l10n_cr_activity_code:
            etree.SubElement(receptor, 'ActividadEconomica').text = partner.l10n_cr_activity_code
            _logger.debug(
                'Added economic activity %s to receptor for partner %s',
                partner.l10n_cr_activity_code,
                partner.name
            )
        else:
            # Check if we're past the mandatory deadline
            current_date = invoice_date or fields.Date.today()
            deadline = self._get_ciiu_mandatory_date()

            if current_date >= deadline:
                # Hard error after deadline
                raise ValidationError(
                    _('Recipient economic activity (CIIU code) is required for invoices '
                      'from October 6, 2025 onwards. Please add economic activity to '
                      'partner "%s" before generating the invoice.') % partner.name
                )
            else:
                # Warning only before deadline (grace period)
                days_remaining = (deadline - current_date).days
                _logger.warning(
                    'Partner %s (ID: %s) is missing CIIU economic activity code. '
                    'This will be REQUIRED from October 6, 2025. '
                    'Days remaining: %s',
                    partner.name,
                    partner.id,
                    days_remaining
                )

        # Email
        if partner.email:
            etree.SubElement(receptor, 'CorreoElectronico').text = partner.email

    def _add_condicion_venta(self, root, move):
        """Add CondicionVenta (payment terms)."""
        # Payment terms:
        # 01 = Contado (Cash)
        # 02 = Crédito (Credit)
        # 03 = Consignación
        # 04 = Apartado
        # 05 = Arrendamiento con opción de compra
        # 06 = Arrendamiento en función financiera
        # 99 = Otros

        if move.invoice_payment_term_id and move.invoice_payment_term_id.line_ids:
            # Has payment terms - credit
            etree.SubElement(root, 'CondicionVenta').text = '02'

            # Add PlazoCredito (credit days)
            days = sum(line.days for line in move.invoice_payment_term_id.line_ids)
            etree.SubElement(root, 'PlazoCredito').text = str(int(days))
        else:
            # No payment terms - cash
            etree.SubElement(root, 'CondicionVenta').text = '01'

    def _add_medio_pago(self, root, move):
        """
        Add MedioPago (payment method) section.

        Updated for Phase 1A: SINPE Móvil Payment Method Integration
        Now uses payment method from invoice and includes transaction ID for SINPE Móvil.

        Payment methods (Hacienda v4.4):
        01 = Efectivo (Cash)
        02 = Tarjeta (Card)
        03 = Cheque (Check)
        04 = Transferencia (Bank Transfer)
        05 = Recaudado por terceros (Collected by third parties)
        06 = SINPE Móvil (Mobile payment)
        99 = Otros (Others)
        """
        # Get payment method code from invoice
        payment_method_code = '01'  # Default to Efectivo

        if move.l10n_cr_payment_method_id:
            payment_method_code = move.l10n_cr_payment_method_id.code
            _logger.debug(
                'Using payment method %s (%s) for invoice %s',
                payment_method_code,
                move.l10n_cr_payment_method_id.name,
                move.name
            )
        else:
            _logger.warning(
                'No payment method set for invoice %s, defaulting to "01" (Efectivo)',
                move.name
            )

        # Add MedioPago tag
        etree.SubElement(root, 'MedioPago').text = payment_method_code

        # Add NumeroTransaccion if payment method requires it (e.g., SINPE Móvil = "06")
        if move.l10n_cr_payment_method_id and move.l10n_cr_payment_method_id.requires_transaction_id:
            if move.l10n_cr_payment_transaction_id:
                etree.SubElement(root, 'NumeroTransaccion').text = move.l10n_cr_payment_transaction_id
                _logger.debug(
                    'Added transaction ID %s for payment method %s',
                    move.l10n_cr_payment_transaction_id,
                    payment_method_code
                )
            else:
                # This should never happen due to validation in account_move.py
                # But we log it for safety
                _logger.error(
                    'Payment method %s requires transaction ID but none provided for invoice %s',
                    payment_method_code,
                    move.name
                )

    def _add_detalle_servicio(self, root, move):
        """Add DetalleServicio (line items)."""
        detalle_servicio = etree.SubElement(root, 'DetalleServicio')

        line_number = 1
        for line in move.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
            linea_detalle = etree.SubElement(detalle_servicio, 'LineaDetalle')

            # Line number
            etree.SubElement(linea_detalle, 'NumeroLinea').text = str(line_number)

            # Product code (Cabys code required)
            codigo = etree.SubElement(linea_detalle, 'Codigo')
            cabys_code = line.product_id.l10n_cr_cabys_code if line.product_id else '8611'
            etree.SubElement(codigo, 'Tipo').text = '04'  # Código de producto
            etree.SubElement(codigo, 'Codigo').text = cabys_code

            # Quantity
            etree.SubElement(linea_detalle, 'Cantidad').text = str(line.quantity)

            # Unit of measure
            etree.SubElement(linea_detalle, 'UnidadMedida').text = 'Unid'  # TODO: Get from product UOM

            # Description
            etree.SubElement(linea_detalle, 'Detalle').text = line.name or ''

            # Unit price
            price_unit = line.price_unit
            etree.SubElement(linea_detalle, 'PrecioUnitario').text = '%.5f' % price_unit

            # Subtotal (before discounts)
            subtotal = line.quantity * price_unit
            etree.SubElement(linea_detalle, 'MontoTotal').text = '%.5f' % subtotal

            # Discount (if any)
            if line.discount > 0:
                descuento = etree.SubElement(linea_detalle, 'Descuento')
                discount_amount = subtotal * (line.discount / 100)
                etree.SubElement(descuento, 'MontoDescuento').text = '%.5f' % discount_amount
                # Get discount nature (code or code + description for "99")
                discount_nature = line._get_discount_nature_for_xml()

                etree.SubElement(descuento, 'NaturalezaDescuento').text = discount_nature
            # Subtotal after discount
            subtotal_after_discount = subtotal - (subtotal * line.discount / 100)
            etree.SubElement(linea_detalle, 'SubTotal').text = '%.5f' % subtotal_after_discount

            # Taxes
            if line.tax_ids:
                self._add_line_tax(linea_detalle, line, subtotal_after_discount)

            # Total
            total_line = line.price_subtotal + line.price_total - line.price_subtotal
            etree.SubElement(linea_detalle, 'MontoTotalLinea').text = '%.5f' % line.price_total

            line_number += 1

    def _add_line_tax(self, linea_detalle, line, base_amount):
        """Add tax information to line item."""
        impuesto = etree.SubElement(linea_detalle, 'Impuesto')

        for tax in line.tax_ids:
            # Determine tax code
            tax_amount_percent = tax.amount

            if tax_amount_percent == 13.0:
                codigo_tax = '01'  # IVA 13%
                tarifa = '13.00'
            elif tax_amount_percent == 4.0:
                codigo_tax = '02'  # IVA 4%
                tarifa = '4.00'
            elif tax_amount_percent == 2.0:
                codigo_tax = '03'  # IVA 2%
                tarifa = '2.00'
            elif tax_amount_percent == 1.0:
                codigo_tax = '04'  # IVA 1%
                tarifa = '1.00'
            elif tax_amount_percent == 0.0:
                codigo_tax = '06'  # Gravado 0%
                tarifa = '0.00'
            else:
                codigo_tax = '01'  # Default to IVA 13%
                tarifa = str(tax_amount_percent)

            etree.SubElement(impuesto, 'Codigo').text = codigo_tax
            etree.SubElement(impuesto, 'CodigoTarifa').text = codigo_tax
            etree.SubElement(impuesto, 'Tarifa').text = tarifa

            # Calculate tax amount
            tax_amount = base_amount * (float(tarifa) / 100)
            etree.SubElement(impuesto, 'Monto').text = '%.5f' % tax_amount

    def _add_resumen_factura(self, root, move):
        """Add ResumenFactura (invoice summary)."""
        resumen = etree.SubElement(root, 'ResumenFactura')

        # Currency
        currency_codes = {
            'CRC': 'CRC',
            'USD': 'USD',
            'EUR': 'EUR',
        }
        currency_code = currency_codes.get(move.currency_id.name, 'CRC')
        codigo_moneda = etree.SubElement(resumen, 'CodigoTipoMoneda')
        etree.SubElement(codigo_moneda, 'CodigoMoneda').text = currency_code
        etree.SubElement(codigo_moneda, 'TipoCambio').text = '1.00000'  # TODO: Get actual exchange rate

        # Totals
        etree.SubElement(resumen, 'TotalServGravados').text = '%.5f' % move.amount_untaxed
        etree.SubElement(resumen, 'TotalServExentos').text = '0.00000'
        etree.SubElement(resumen, 'TotalMercanciasGravadas').text = '0.00000'
        etree.SubElement(resumen, 'TotalMercanciasExentas').text = '0.00000'
        etree.SubElement(resumen, 'TotalGravado').text = '%.5f' % move.amount_untaxed
        etree.SubElement(resumen, 'TotalExento').text = '0.00000'
        etree.SubElement(resumen, 'TotalVenta').text = '%.5f' % move.amount_untaxed
        etree.SubElement(resumen, 'TotalDescuentos').text = '0.00000'  # TODO: Calculate discounts
        etree.SubElement(resumen, 'TotalVentaNeta').text = '%.5f' % move.amount_untaxed
        etree.SubElement(resumen, 'TotalImpuesto').text = '%.5f' % move.amount_tax
        etree.SubElement(resumen, 'TotalComprobante').text = '%.5f' % move.amount_total

    def _add_informacion_referencia(self, root, original_move):
        """Add InformacionReferencia for credit/debit notes."""
        if not original_move.l10n_cr_clave:
            return

        info_ref = etree.SubElement(root, 'InformacionReferencia')

        # Reference type: 01 = Anula documento de referencia
        etree.SubElement(info_ref, 'TipoDoc').text = '01'
        etree.SubElement(info_ref, 'Numero').text = original_move.name or ''
        etree.SubElement(info_ref, 'FechaEmision').text = original_move.invoice_date.isoformat()
        etree.SubElement(info_ref, 'Codigo').text = '01'  # Reference code
        etree.SubElement(info_ref, 'Razon').text = 'Anulación de factura'

    def _get_company_id_type(self, vat):
        """Get company identification type code."""
        # Usually companies use Cédula Jurídica (02)
        return '02'

    def _get_partner_id_type(self, vat):
        """Get partner identification type code."""
        if not vat:
            return '05'  # Extranjero

        clean_vat = vat.replace('-', '').replace(' ', '')
        length = len(clean_vat)

        if length == 9:
            return '01'  # Cédula Física
        elif length == 10:
            if clean_vat.startswith('3'):
                return '02'  # Cédula Jurídica
            return '04'  # NITE
        elif length in [11, 12]:
            return '03'  # DIMEX
        else:
            return '05'  # Extranjero

    def _get_ciiu_mandatory_date(self):
        """
        Get the CIIU mandatory date from system parameter or constant.

        This allows overriding for testing purposes.
        """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        date_str = IrConfigParameter.get_param('l10n_cr_einvoice.ciiu_mandatory_date')

        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                _logger.warning(
                    'Invalid CIIU mandatory date in system parameter: %s. '
                    'Using default: October 6, 2025',
                    date_str
                )

        return self.CIIU_MANDATORY_DATE
