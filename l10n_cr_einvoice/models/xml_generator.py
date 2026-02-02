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

        # Get source document (either account.move or pos.order)
        if einvoice.move_id:
            source_doc = einvoice.move_id
        elif einvoice.pos_order_id:
            source_doc = einvoice.pos_order_id
        else:
            raise ValidationError(_('E-invoice must have either an Invoice or POS Order linked.'))

        # Select the appropriate generator method
        if doc_type == 'FE':
            return self._generate_factura_electronica(einvoice, source_doc)
        elif doc_type == 'TE':
            return self._generate_tiquete_electronico(einvoice, source_doc)
        elif doc_type == 'NC':
            return self._generate_nota_credito(einvoice, source_doc)
        elif doc_type == 'ND':
            return self._generate_nota_debito(einvoice, source_doc)
        else:
            raise ValidationError(_('Unknown document type: %s') % doc_type)

    def _generate_factura_electronica(self, einvoice, source_doc):
        """Generate Factura Electrónica (FE) XML.

        Args:
            einvoice: l10n_cr.einvoice.document record
            source_doc: account.move or pos.order record
        """
        # Create root element with namespace
        ns = self.NAMESPACES['fe']
        root = etree.Element(
            '{%s}FacturaElectronica' % ns,
            nsmap={None: ns, 'ds': self.NAMESPACES['ds'], 'xsd': self.NAMESPACES['xsd']},
        )

        # 1. Clave (50-digit key)
        etree.SubElement(root, 'Clave').text = einvoice.clave

        # 1b. ProveedorSistemas (system provider identification - required in v4.4)
        proveedor = getattr(source_doc.company_id, 'l10n_cr_proveedor_sistemas', '') or ''
        if not proveedor:
            # Default: use company VAT as provider ID (self-developed system)
            proveedor = (source_doc.company_id.vat or '').replace('-', '').replace(' ', '')
        if proveedor:
            etree.SubElement(root, 'ProveedorSistemas').text = proveedor

        # 2. CodigoActividadEmisor (economic activity code, min 6 chars in v4.4)
        codigo_actividad = getattr(source_doc.company_id.partner_id, 'l10n_cr_activity_code', '') or '861201'
        codigo_actividad = codigo_actividad.zfill(6)
        etree.SubElement(root, 'CodigoActividadEmisor').text = codigo_actividad

        # 3. NumeroConsecutivo (consecutive number)
        numero = einvoice.name or ''
        etree.SubElement(root, 'NumeroConsecutivo').text = numero

        # 4. FechaEmision (emission date/time)
        # Handle both account.move (invoice_date) and pos.order (date_order)
        if hasattr(source_doc, 'invoice_date'):
            fecha_emision = source_doc.invoice_date or fields.Date.today()
        else:
            fecha_emision = source_doc.date_order.date() if source_doc.date_order else fields.Date.today()
        fecha_hora = datetime.combine(fecha_emision, datetime.now().time())
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.isoformat()

        # 5. Emisor (sender/company information)
        self._add_emisor(root, source_doc.company_id)

        # 6. Receptor (receiver/customer information) - Updated for Phase 1C
        if source_doc.partner_id:
            self._add_receptor(root, source_doc.partner_id, fecha_emision)

        # 7. CondicionVenta (payment terms)
        self._add_condicion_venta(root, source_doc)

        # 8. MedioPago (payment method) - Updated for Phase 1A
        self._add_medio_pago(root, source_doc)

        # 9. DetalleServicio (line items)
        self._add_detalle_servicio(root, source_doc)

        # 10. ResumenFactura (invoice summary)
        self._add_resumen_factura(root, source_doc)

        # Convert to string
        xml_str = etree.tostring(
            root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True,
        ).decode('utf-8')

        return xml_str

    def _generate_tiquete_electronico(self, einvoice, source_doc):
        """Generate Tiquete Electrónico (TE) XML.

        Args:
            einvoice: l10n_cr.einvoice.document record
            source_doc: account.move or pos.order record
        """
        # Similar to FE but with simplified structure
        ns = self.NAMESPACES['te']
        root = etree.Element(
            '{%s}TiqueteElectronico' % ns,
            nsmap={None: ns, 'ds': self.NAMESPACES['ds']},
        )

        # Add basic elements (similar to FE but without Receptor for anonymous sales)
        etree.SubElement(root, 'Clave').text = einvoice.clave

        # ProveedorSistemas (required in v4.4)
        proveedor = getattr(source_doc.company_id, 'l10n_cr_proveedor_sistemas', '') or ''
        if not proveedor:
            proveedor = (source_doc.company_id.vat or '').replace('-', '').replace(' ', '')
        if proveedor:
            etree.SubElement(root, 'ProveedorSistemas').text = proveedor

        # CodigoActividadEmisor (required in v4.4, min 6 chars)
        codigo_actividad = getattr(source_doc.company_id.partner_id, 'l10n_cr_activity_code', '') or '861201'
        codigo_actividad = codigo_actividad.zfill(6)
        etree.SubElement(root, 'CodigoActividadEmisor').text = codigo_actividad

        etree.SubElement(root, 'NumeroConsecutivo').text = einvoice.name or ''

        # Handle both account.move and pos.order
        if hasattr(source_doc, 'invoice_date'):
            fecha_emision = source_doc.invoice_date or fields.Date.today()
        else:
            fecha_emision = source_doc.date_order.date() if source_doc.date_order else fields.Date.today()
        fecha_hora = datetime.combine(fecha_emision, datetime.now().time())
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.isoformat()

        self._add_emisor(root, source_doc.company_id)
        self._add_condicion_venta(root, source_doc)
        self._add_medio_pago(root, source_doc)

        self._add_detalle_servicio(root, source_doc)
        self._add_resumen_factura(root, source_doc)

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
            nsmap={None: ns, 'ds': self.NAMESPACES['ds']},
        )

        # Similar to FE with reference to original invoice
        etree.SubElement(root, 'Clave').text = einvoice.clave

        # ProveedorSistemas (required in v4.4)
        proveedor = getattr(move.company_id, 'l10n_cr_proveedor_sistemas', '') or ''
        if not proveedor:
            proveedor = (move.company_id.vat or '').replace('-', '').replace(' ', '')
        if proveedor:
            etree.SubElement(root, 'ProveedorSistemas').text = proveedor

        # CodigoActividadEmisor (required in v4.4, min 6 chars)
        codigo_actividad = getattr(move.company_id.partner_id, 'l10n_cr_activity_code', '') or '861201'
        codigo_actividad = codigo_actividad.zfill(6)
        etree.SubElement(root, 'CodigoActividadEmisor').text = codigo_actividad

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
            nsmap={None: ns, 'ds': self.NAMESPACES['ds']},
        )

        etree.SubElement(root, 'Clave').text = einvoice.clave

        # ProveedorSistemas (required in v4.4)
        proveedor = getattr(move.company_id, 'l10n_cr_proveedor_sistemas', '') or ''
        if not proveedor:
            proveedor = (move.company_id.vat or '').replace('-', '').replace(' ', '')
        if proveedor:
            etree.SubElement(root, 'ProveedorSistemas').text = proveedor

        # CodigoActividadEmisor (required in v4.4, min 6 chars)
        codigo_actividad = getattr(move.company_id.partner_id, 'l10n_cr_activity_code', '') or '861201'
        codigo_actividad = codigo_actividad.zfill(6)
        etree.SubElement(root, 'CodigoActividadEmisor').text = codigo_actividad

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
        commercial_name = getattr(company, 'commercial_name', '') or ''
        if commercial_name:
            etree.SubElement(emisor, 'NombreComercial').text = commercial_name

        # Location
        ubicacion = etree.SubElement(emisor, 'Ubicacion')

        # v4.4 Ubicacion: Provincia (1 digit 1-7), Canton (2 digits), Distrito (2 digits),
        # Barrio (min 5 chars). Parse from stored location code.
        location_code = (company.l10n_cr_emisor_location or '').strip()
        # Normalize: strip leading zeros from province part
        location_code = location_code.lstrip('0') or '1010101'
        # Extract parts with safe defaults
        provincia = location_code[0:1] if len(location_code) >= 1 else '1'
        canton = location_code[1:3] if len(location_code) >= 3 else '01'
        distrito = location_code[3:5] if len(location_code) >= 5 else '01'
        barrio_raw = location_code[5:] if len(location_code) > 5 else '01'
        # Barrio must be at least 5 chars in v4.4
        barrio = barrio_raw.zfill(5)
        etree.SubElement(ubicacion, 'Provincia').text = provincia
        etree.SubElement(ubicacion, 'Canton').text = canton
        etree.SubElement(ubicacion, 'Distrito').text = distrito
        etree.SubElement(ubicacion, 'Barrio').text = barrio

        # Address details (OtrasSenas is required in v4.4)
        otras_senas = company.street or 'Sin otras señas'
        etree.SubElement(ubicacion, 'OtrasSenas').text = otras_senas

        # Contact info (Telefono is optional, only include if phone is set)
        phone = (company.phone or '').replace(' ', '').replace('-', '')
        if phone and int(phone[:8] or '0') >= 100:
            telefono = etree.SubElement(emisor, 'Telefono')
            etree.SubElement(telefono, 'CodigoPais').text = '506'
            etree.SubElement(telefono, 'NumTelefono').text = phone[:8]

        # CorreoElectronico (required in v4.4 if Telefono is absent)
        email = company.email or 'info@example.com'
        etree.SubElement(emisor, 'CorreoElectronico').text = email

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

        # Note: ActividadEconomica is NOT a valid element in Receptor per v4.4 XSD.
        # The economic activity code goes in CodigoActividadEmisor at the document root level.

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

            # CABYS product code (required in v4.4, replaces old Codigo element)
            cabys_code = getattr(line, 'l10n_cr_product_code', '') or '8611001000000'
            etree.SubElement(linea_detalle, 'CodigoCABYS').text = cabys_code

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

            # v4.4 LineaDetalle requires: BaseImponible, Impuesto+,
            # ImpuestoAsumidoEmisorFabrica, ImpuestoNeto, MontoTotalLinea
            etree.SubElement(linea_detalle, 'BaseImponible').text = '%.5f' % subtotal_after_discount

            total_tax = 0.0
            if line.tax_ids:
                total_tax = self._add_line_tax(linea_detalle, line, subtotal_after_discount)
            else:
                # Even without taxes, v4.4 requires at least one Impuesto element
                impuesto = etree.SubElement(linea_detalle, 'Impuesto')
                etree.SubElement(impuesto, 'Codigo').text = '01'
                etree.SubElement(impuesto, 'CodigoTarifaIVA').text = '08'
                etree.SubElement(impuesto, 'Tarifa').text = '0.00'
                etree.SubElement(impuesto, 'Monto').text = '0.00000'

            etree.SubElement(linea_detalle, 'ImpuestoAsumidoEmisorFabrica').text = '0.00000'
            etree.SubElement(linea_detalle, 'ImpuestoNeto').text = '%.5f' % total_tax

            # MontoTotalLinea
            etree.SubElement(linea_detalle, 'MontoTotalLinea').text = '%.5f' % (subtotal_after_discount + total_tax)

            line_number += 1

    def _add_line_tax(self, linea_detalle, line, base_amount):
        """Add tax information to line item (v4.4: each tax is a separate Impuesto element).

        Returns:
            float: Total tax amount for the line.
        """
        total_tax = 0.0

        for tax in line.tax_ids:
            # Each tax gets its own Impuesto element in v4.4
            impuesto = etree.SubElement(linea_detalle, 'Impuesto')

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
            etree.SubElement(impuesto, 'CodigoTarifaIVA').text = codigo_tax
            etree.SubElement(impuesto, 'Tarifa').text = tarifa

            # Calculate tax amount
            tax_amount = base_amount * (float(tarifa) / 100)
            etree.SubElement(impuesto, 'Monto').text = '%.5f' % tax_amount
            total_tax += tax_amount

        return total_tax

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
