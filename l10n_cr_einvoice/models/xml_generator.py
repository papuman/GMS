# -*- coding: utf-8 -*-
import re
import logging
from datetime import datetime, date, timezone, timedelta
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

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

    # Costa Rica timezone (UTC-6, no DST)
    CR_TZ = timezone(timedelta(hours=-6))

    def _get_fecha_emision(self, source_doc):
        """Get emission date and datetime in Costa Rica timezone (UTC-6).

        Returns:
            tuple: (fecha_date, fecha_datetime) - date for receptor, datetime for XML
        """
        now_cr = datetime.now(self.CR_TZ)

        if hasattr(source_doc, 'invoice_date'):
            # account.move - invoice_date is a Date field (no TZ conversion needed)
            fecha = source_doc.invoice_date or now_cr.date()
        else:
            # pos.order - date_order is UTC Datetime, convert to CR timezone
            if source_doc.date_order:
                dt_utc = source_doc.date_order.replace(tzinfo=timezone.utc)
                dt_cr = dt_utc.astimezone(self.CR_TZ)
                fecha = dt_cr.date()
            else:
                fecha = now_cr.date()

        # Combine date with current Costa Rica time (naive for XML output)
        cr_time = now_cr.time().replace(tzinfo=None)
        fecha_hora = datetime.combine(fecha, cr_time)
        return fecha, fecha_hora

    def _get_proveedor_sistemas(self, company):
        """Get ProveedorSistemas value (REQUIRED in v4.4).

        Returns the software developer/provider cedula. Falls back to company VAT.
        Raises ValidationError if no value can be determined.
        """
        proveedor = (company.l10n_cr_proveedor_sistemas or '').strip()
        if not proveedor:
            proveedor = (company.vat or '').replace('-', '').replace(' ', '').strip()
        if not proveedor:
            raise ValidationError(_(
                'ProveedorSistemas es obligatorio en v4.4 de Hacienda.\n'
                'Configure el campo "Software Provider ID" en la compañía, '
                'o asegúrese de que la cédula jurídica esté configurada.'
            ))
        return proveedor[:20]

    @api.model
    def generate_invoice_xml(self, einvoice, dry_run=False):
        """
        Generate the complete XML for an electronic invoice.

        Args:
            einvoice: l10n_cr.einvoice.document record
            dry_run: If True, only validate without generating XML

        Returns:
            str: XML content (or True if dry_run and validation passes)
        """
        # PRE-FLIGHT VALIDATION
        self._validate_before_generation(einvoice)

        if dry_run:
            _logger.info('Dry-run validation passed for document %s', einvoice.name)
            return True

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

        Note: Pre-flight validation is performed in generate_invoice_xml().
        This method assumes all validation has passed.

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

        # v4.4 element order: Clave, ProveedorSistemas, CodigoActividadEmisor,
        # NumeroConsecutivo, FechaEmision, Emisor, Receptor, ...
        etree.SubElement(root, 'Clave').text = einvoice.clave
        etree.SubElement(root, 'ProveedorSistemas').text = self._get_proveedor_sistemas(source_doc.company_id)

        codigo_actividad = self._get_activity_code(source_doc.company_id)
        etree.SubElement(root, 'CodigoActividadEmisor').text = self._format_activity_code(codigo_actividad)
        etree.SubElement(root, 'NumeroConsecutivo').text = einvoice.name or ''

        fecha_emision, fecha_hora = self._get_fecha_emision(source_doc)
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.replace(microsecond=0).isoformat()

        self._add_emisor(root, source_doc.company_id)

        # 6. Receptor (receiver/customer information) - Updated for Phase 1C and MVP Task 2
        # Use einvoice.partner_id (which may be the corporate parent for billing)
        receptor_added = False
        if einvoice.partner_id:
            self._add_receptor(root, einvoice.partner_id, fecha_emision)
            receptor_added = True

        # XSD: Receptor is REQUIRED for FE (Factura Electronica)
        if not receptor_added:
            raise UserError(_("Receptor is required for Factura Electrónica (FE). Please set a customer."))

        # 7. CondicionVenta (payment terms)
        self._add_condicion_venta(root, source_doc)

        # Compute line amounts once for consistency between detail and summary
        lines_data = self._compute_line_amounts(source_doc)

        # 8. DetalleServicio (line items)
        self._add_detalle_servicio(root, source_doc, lines_data)

        # 9. ResumenFactura (invoice summary) - MedioPago is inside ResumenFactura in v4.4
        self._add_resumen_factura(root, source_doc, lines_data)

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

        Note: Pre-flight validation is performed in generate_invoice_xml().
        This method assumes all validation has passed.

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

        # v4.4 element order (TE has no Receptor for anonymous sales)
        etree.SubElement(root, 'Clave').text = einvoice.clave
        etree.SubElement(root, 'ProveedorSistemas').text = self._get_proveedor_sistemas(source_doc.company_id)

        codigo_actividad = self._get_activity_code(source_doc.company_id)
        etree.SubElement(root, 'CodigoActividadEmisor').text = self._format_activity_code(codigo_actividad)
        etree.SubElement(root, 'NumeroConsecutivo').text = einvoice.name or ''

        fecha_emision, fecha_hora = self._get_fecha_emision(source_doc)
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.replace(microsecond=0).isoformat()

        self._add_emisor(root, source_doc.company_id)
        self._add_condicion_venta(root, source_doc)

        lines_data = self._compute_line_amounts(source_doc)
        self._add_detalle_servicio(root, source_doc, lines_data)
        self._add_resumen_factura(root, source_doc, lines_data)

        xml_str = etree.tostring(
            root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True,
        ).decode('utf-8')

        return xml_str

    def _generate_nota_credito(self, einvoice, move):
        """Generate Nota de Crédito (NC) XML.

        Note: Pre-flight validation is performed in generate_invoice_xml().
        """
        ns = self.NAMESPACES['nc']
        root = etree.Element(
            '{%s}NotaCreditoElectronica' % ns,
            nsmap={None: ns, 'ds': self.NAMESPACES['ds']},
        )

        etree.SubElement(root, 'Clave').text = einvoice.clave
        etree.SubElement(root, 'ProveedorSistemas').text = self._get_proveedor_sistemas(move.company_id)

        codigo_actividad = self._get_activity_code(move.company_id)
        etree.SubElement(root, 'CodigoActividadEmisor').text = self._format_activity_code(codigo_actividad)
        etree.SubElement(root, 'NumeroConsecutivo').text = einvoice.name or ''

        fecha_emision, fecha_hora = self._get_fecha_emision(move)
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.replace(microsecond=0).isoformat()

        self._add_emisor(root, move.company_id)

        if einvoice.partner_id:
            self._add_receptor(root, einvoice.partner_id, fecha_emision)

        self._add_condicion_venta(root, move)
        lines_data = self._compute_line_amounts(move)
        self._add_detalle_servicio(root, move, lines_data)
        self._add_resumen_factura(root, move, lines_data)

        # InformacionReferencia is REQUIRED for NC per v4.4 XSD
        if not move.reversed_entry_id:
            raise UserError(_("Credit Note requires a reference document (reversed_entry_id)"))
        self._add_informacion_referencia(root, move.reversed_entry_id)

        xml_str = etree.tostring(
            root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True,
        ).decode('utf-8')

        return xml_str

    def _generate_nota_debito(self, einvoice, move):
        """Generate Nota de Débito (ND) XML.

        Note: Pre-flight validation is performed in generate_invoice_xml().
        """
        # Very similar to NC
        ns = self.NAMESPACES['nd']
        root = etree.Element(
            '{%s}NotaDebitoElectronica' % ns,
            nsmap={None: ns, 'ds': self.NAMESPACES['ds']},
        )

        etree.SubElement(root, 'Clave').text = einvoice.clave
        etree.SubElement(root, 'ProveedorSistemas').text = self._get_proveedor_sistemas(move.company_id)

        codigo_actividad = self._get_activity_code(move.company_id)
        etree.SubElement(root, 'CodigoActividadEmisor').text = self._format_activity_code(codigo_actividad)
        etree.SubElement(root, 'NumeroConsecutivo').text = einvoice.name or ''

        fecha_emision, fecha_hora = self._get_fecha_emision(move)
        etree.SubElement(root, 'FechaEmision').text = fecha_hora.replace(microsecond=0).isoformat()

        self._add_emisor(root, move.company_id)

        if einvoice.partner_id:
            self._add_receptor(root, einvoice.partner_id, fecha_emision)

        self._add_condicion_venta(root, move)
        lines_data = self._compute_line_amounts(move)
        self._add_detalle_servicio(root, move, lines_data)
        self._add_resumen_factura(root, move, lines_data)

        # InformacionReferencia is REQUIRED for ND per v4.4 XSD
        if not move.debit_origin_id:
            raise UserError(_("Debit Note requires a reference document (debit_origin_id)"))
        self._add_informacion_referencia(root, move.debit_origin_id)

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

        # Company name (XSD: min=5, max=100)
        nombre = self._sanitize_text(company.name, min_len=5, max_len=100, default='Emisor')
        etree.SubElement(emisor, 'Nombre').text = nombre

        # Identification
        identificacion = etree.SubElement(emisor, 'Identificacion')
        tipo_id = self._get_company_id_type(company.vat or '')
        etree.SubElement(identificacion, 'Tipo').text = tipo_id
        numero_id = (company.vat or '').replace('-', '').replace(' ', '')
        etree.SubElement(identificacion, 'Numero').text = numero_id

        # Commercial name (if different) (XSD: min=3, max=80)
        commercial_name = getattr(company, 'commercial_name', '') or ''
        if commercial_name:
            commercial_name = self._sanitize_text(commercial_name, min_len=3, max_len=80)
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
        etree.SubElement(ubicacion, 'Provincia').text = provincia
        etree.SubElement(ubicacion, 'Canton').text = canton
        etree.SubElement(ubicacion, 'Distrito').text = distrito

        # v4.4: Barrio changed from numeric code to text description (min=5, max=50).
        # Barrio is OPTIONAL -- only emit if there's a meaningful value.
        barrio_raw = location_code[5:] if len(location_code) > 5 else ''
        # If it looks like a zero-padded numeric code, use street2 or skip
        if barrio_raw and barrio_raw.isdigit():
            barrio_text = (company.street2 or '').strip()
            if not barrio_text or barrio_text == barrio_raw:
                barrio_text = ''  # Don't emit dummy numeric values
        else:
            barrio_text = barrio_raw.strip()
        if barrio_text:
            barrio_text = self._sanitize_text(barrio_text, min_len=5, max_len=50, default='No indicado')
            etree.SubElement(ubicacion, 'Barrio').text = barrio_text

        # Address details (OtrasSenas is required in v4.4)
        otras_senas = self._sanitize_text(company.street, min_len=5, max_len=250, default='Sin otras señas')
        etree.SubElement(ubicacion, 'OtrasSenas').text = otras_senas

        # Contact info (Telefono is optional, only include if phone is set)
        phone = (company.phone or '').replace(' ', '').replace('-', '')
        if phone and int(phone[:8] or '0') >= 100:
            telefono = etree.SubElement(emisor, 'Telefono')
            etree.SubElement(telefono, 'CodigoPais').text = '506'
            etree.SubElement(telefono, 'NumTelefono').text = phone[:8]

        # CorreoElectronico (required in v4.4)
        email = company.email
        if not email:
            raise ValidationError(_(
                'El correo electrónico de la empresa es obligatorio para facturación electrónica.\n'
                'Configure el email en Configuración > Compañía.'
            ))
        etree.SubElement(emisor, 'CorreoElectronico').text = email

    def _add_receptor(self, root, partner, invoice_date=None):
        """
        Add Receptor (receiver) section.

        Updated for Phase 1C: Recipient Economic Activity Field
        Includes ActividadEconomica tag (CIIU 4 code) per v4.4 spec.
        """
        receptor = etree.SubElement(root, 'Receptor')

        # Partner name (XSD: min=3, max=100)
        etree.SubElement(receptor, 'Nombre').text = self._sanitize_text(
            partner.name, min_len=3, max_len=100, default='Cliente'
        )

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

    def _add_condicion_venta(self, root, source_doc):
        """Add CondicionVenta (payment terms).

        Handles both account.move and pos.order source documents.
        POS orders are always cash (01). Account moves check payment terms.

        Valid codes per Hacienda v4.4:
        01 = Contado (Cash)
        02 = Crédito (Credit)
        03 = Consignación (Consignment)
        04 = Apartado (Layaway)
        05 = Arrendamiento con opción de compra (Lease-to-own)
        06 = Arrendamiento en función financiera (Financial lease)
        99 = Otros (Other)
        """
        VALID_CONDICION_CODES = {'01', '02', '03', '04', '05', '06', '99'}

        # POS orders are always cash
        if source_doc._name == 'pos.order':
            etree.SubElement(root, 'CondicionVenta').text = '01'
            return

        # account.move: check for explicit override field first
        custom_code = getattr(source_doc, 'l10n_cr_condicion_venta', '') or ''
        custom_code = custom_code.strip()
        if custom_code and custom_code in VALID_CONDICION_CODES:
            etree.SubElement(root, 'CondicionVenta').text = custom_code
            if custom_code == '02' and source_doc.invoice_payment_term_id:
                days = sum(line.nb_days for line in source_doc.invoice_payment_term_id.line_ids)
                if days > 0:
                    etree.SubElement(root, 'PlazoCredito').text = str(int(days))
            return

        # Default behavior: detect from payment terms
        if source_doc.invoice_payment_term_id and source_doc.invoice_payment_term_id.line_ids:
            etree.SubElement(root, 'CondicionVenta').text = '02'
            days = sum(line.nb_days for line in source_doc.invoice_payment_term_id.line_ids)
            etree.SubElement(root, 'PlazoCredito').text = str(int(days))
        else:
            etree.SubElement(root, 'CondicionVenta').text = '01'

    def _add_medio_pago(self, root, source_doc):
        """
        Add MedioPago (payment method) section.

        Handles both account.move and pos.order source documents.
        POS orders derive payment method from pos.payment records.
        account.move uses l10n_cr_payment_method_id, with fallback to
        auto-detection from linked payment transactions (e.g. TiloPay).

        Payment methods (Hacienda v4.4):
        01 = Efectivo (Cash)
        02 = Tarjeta (Card)
        03 = Cheque (Check)
        04 = Transferencia (Bank Transfer)
        05 = Recaudado por terceros (Collected by third parties)
        06 = SINPE Movil (Mobile payment)
        99 = Otros (Others)
        """
        payment_method_codes = []

        if source_doc._name == 'pos.order':
            # POS: derive from pos.payment records — emit one MedioPago per
            # distinct payment method so split payments are correctly reported.
            payments = source_doc.payment_ids
            if payments:
                seen_codes = []
                for payment in payments:
                    code = self._pos_payment_to_hacienda_code(payment)
                    if code not in seen_codes:
                        seen_codes.append(code)
                payment_method_codes = seen_codes
            if not payment_method_codes:
                payment_method_codes = ['01']  # Default to Efectivo
            _logger.debug(
                'POS order %s: payment method codes %s',
                source_doc.name, payment_method_codes
            )
        else:
            # account.move: use configured payment method
            if source_doc.l10n_cr_payment_method_id:
                payment_method_codes = [source_doc.l10n_cr_payment_method_id.code]
            else:
                # Fallback: try to detect from linked payment transactions
                # This covers cases where the payment method was not set during
                # invoice posting (e.g., existing invoices, manual e-invoice creation)
                detected = source_doc._detect_payment_method_from_transactions()
                if detected:
                    payment_method_codes = [detected.code]
                    # Also update the invoice field for future reference
                    source_doc.l10n_cr_payment_method_id = detected
                    _logger.info(
                        'Auto-detected payment method "%s" (code %s) from transactions '
                        'for invoice %s at XML generation time',
                        detected.name, detected.code, source_doc.name
                    )
                else:
                    payment_method_codes = ['01']
                    _logger.warning(
                        'No payment method set for invoice %s, defaulting to "01" (Efectivo). '
                        'Set payment method on invoice to avoid this default.',
                        source_doc.name
                    )

        # v4.4: MedioPago is a complex type inside ResumenFactura.
        # Hacienda allows multiple MedioPago elements for split payments.
        for code in payment_method_codes:
            medio_pago = etree.SubElement(root, 'MedioPago')
            etree.SubElement(medio_pago, 'TipoMedioPago').text = code

    @staticmethod
    def _pos_payment_to_hacienda_code(payment):
        """Map a single pos.payment record to a Hacienda MedioPago code.

        Uses name matching on the payment method. For reliability, consider
        adding a l10n_cr_payment_code field to pos.payment.method.
        """
        method_name = (payment.payment_method_id.name or '').lower()
        if any(k in method_name for k in ('sinpe', 'sinpé', 'movil', 'móvil')):
            return '06'  # SINPE Móvil
        elif any(k in method_name for k in ('card', 'tarjeta', 'crédito', 'credito', 'débito', 'debito', 'visa', 'mastercard')):
            return '02'  # Card
        elif any(k in method_name for k in ('transfer', 'transferencia', 'wire', 'banco')):
            return '04'  # Bank transfer
        elif any(k in method_name for k in ('check', 'cheque')):
            return '03'  # Check
        elif any(k in method_name for k in ('customer_account', 'cuenta', 'crédito cliente')):
            return '99'  # Others
        return '01'  # Cash/Efectivo

    def _compute_line_amounts(self, source_doc):
        """Compute line-level amounts for both DetalleServicio and ResumenFactura.

        This ensures the line items and summary totals are always consistent,
        regardless of the source document's computed fields (which may differ
        for POS orders where amount_tax can be 0 even when taxes exist on lines).

        Also collects tax breakdown by (Codigo, CodigoTarifaIVA) for the
        TotalDesgloseImpuesto elements required in v4.4.

        Returns:
            list of dicts with per-line amounts, plus aggregated totals.
        """
        if source_doc._name == 'pos.order':
            order_lines = source_doc.lines
        else:
            order_lines = source_doc.invoice_line_ids.filtered(lambda l: l.display_type == 'product')

        lines_data = []
        for line in order_lines:
            quantity = line.qty if source_doc._name == 'pos.order' else line.quantity
            price_unit = line.price_unit
            subtotal = quantity * price_unit
            discount_amount = subtotal * (line.discount / 100) if line.discount > 0 else 0.0
            subtotal_after_discount = subtotal - discount_amount

            # Compute tax from line.tax_ids (same logic as _add_line_tax)
            # Also track breakdown by (codigo, codigo_tarifa) for TotalDesgloseImpuesto
            line_tax = 0.0
            line_tax_breakdown = []
            if line.tax_ids:
                for tax in line.tax_ids:
                    codigo_tipo = '01'  # IVA
                    tarifa_info = self.TARIFA_IVA_MAP.get(tax.amount)
                    if tarifa_info:
                        codigo_tarifa, tarifa_str = tarifa_info
                        tarifa = float(tarifa_str)
                    else:
                        # Map to closest valid rate (same logic as _add_line_tax)
                        closest_rate = min(self.TARIFA_IVA_MAP.keys(), key=lambda r: abs(r - tax.amount))
                        codigo_tarifa, tarifa_str = self.TARIFA_IVA_MAP[closest_rate]
                        tarifa = float(tarifa_str)
                    tax_amt = subtotal_after_discount * (tarifa / 100)
                    line_tax += tax_amt
                    line_tax_breakdown.append({
                        'codigo': codigo_tipo,
                        'codigo_tarifa': codigo_tarifa,
                        'amount': tax_amt,
                    })

            lines_data.append({
                'line': line,
                'quantity': quantity,
                'price_unit': price_unit,
                'subtotal': subtotal,
                'discount_amount': discount_amount,
                'subtotal_after_discount': subtotal_after_discount,
                'tax_amount': line_tax,
                'tax_breakdown': line_tax_breakdown,
                'total': subtotal_after_discount + line_tax,
            })

        return lines_data

    def _add_detalle_servicio(self, root, source_doc, lines_data=None):
        """Add DetalleServicio (line items).

        Handles both account.move and pos.order source documents.
        POS order lines use 'lines' with 'qty'; account.move uses 'invoice_line_ids' with 'quantity'.

        Args:
            root: XML root element
            source_doc: account.move or pos.order record
            lines_data: Pre-computed line amounts from _compute_line_amounts()
        """
        if lines_data is None:
            lines_data = self._compute_line_amounts(source_doc)

        detalle_servicio = etree.SubElement(root, 'DetalleServicio')

        for line_number, ld in enumerate(lines_data, start=1):
            line = ld['line']
            linea_detalle = etree.SubElement(detalle_servicio, 'LineaDetalle')

            # Line number
            etree.SubElement(linea_detalle, 'NumeroLinea').text = str(line_number)

            # CABYS product code (required in v4.4)
            # Try: 1) line field (account.move.line), 2) product template, 3) default
            cabys_code = getattr(line, 'l10n_cr_product_code', '') or ''
            if not cabys_code and line.product_id:
                cabys_code = getattr(line.product_id.product_tmpl_id, 'l10n_cr_cabys_code', '') or ''
            if not cabys_code:
                cabys_code = self._get_default_cabys_code()
            etree.SubElement(linea_detalle, 'CodigoCABYS').text = cabys_code

            etree.SubElement(linea_detalle, 'Cantidad').text = str(ld['quantity'])

            # Unit of measure
            etree.SubElement(linea_detalle, 'UnidadMedida').text = 'Unid'

            # Description (XSD: min=3, max=200) — pos.order.line uses 'full_product_name', account.move.line uses 'name'
            if source_doc._name == 'pos.order':
                description = line.full_product_name or (line.product_id.display_name if line.product_id else '')
            else:
                description = line.name or ''
            etree.SubElement(linea_detalle, 'Detalle').text = self._sanitize_text(
                description, min_len=3, max_len=200, default='Producto'
            )

            # Unit price
            etree.SubElement(linea_detalle, 'PrecioUnitario').text = '%.5f' % ld['price_unit']

            # Subtotal (before discounts)
            etree.SubElement(linea_detalle, 'MontoTotal').text = '%.5f' % ld['subtotal']

            # Discount (if any)
            if line.discount > 0:
                descuento = etree.SubElement(linea_detalle, 'Descuento')
                etree.SubElement(descuento, 'MontoDescuento').text = '%.5f' % ld['discount_amount']
                # v4.4: CodigoDescuento codes
                # 01=Trueque, 02=Cortesia, 03=Detalles, 04=Condicion especial,
                # 05=Descuento por campaña, 06=Descuento otros departamentos,
                # 07=Descuento comercial, 08=Descuento por frecuencia,
                # 09=Descuento sostenido, 99=Otros
                if source_doc._name == 'account.move' and hasattr(line, '_get_discount_code_for_xml'):
                    discount_code = line._get_discount_code_for_xml()
                else:
                    discount_code = '07'  # Descuento Comercial (safe default)
                etree.SubElement(descuento, 'CodigoDescuento').text = discount_code
                # When code is '99' (Otros), NaturalezaDescuento and
                # CodigoDescuentoOTRO are mandatory per Hacienda v4.4
                if discount_code == '99':
                    desc_nature = 'Descuento aplicado'
                    if hasattr(line, 'l10n_cr_discount_nature') and line.l10n_cr_discount_nature:
                        desc_nature = line.l10n_cr_discount_nature
                    etree.SubElement(descuento, 'CodigoDescuentoOTRO').text = desc_nature
                    etree.SubElement(descuento, 'NaturalezaDescuento').text = desc_nature

            # Subtotal after discount
            etree.SubElement(linea_detalle, 'SubTotal').text = '%.5f' % ld['subtotal_after_discount']

            # BaseImponible
            etree.SubElement(linea_detalle, 'BaseImponible').text = '%.5f' % ld['subtotal_after_discount']

            total_tax = 0.0
            if line.tax_ids:
                total_tax = self._add_line_tax(linea_detalle, line, ld['subtotal_after_discount'])
            else:
                # v4.4 requires at least one Impuesto element even with no taxes
                impuesto = etree.SubElement(linea_detalle, 'Impuesto')
                etree.SubElement(impuesto, 'Codigo').text = '01'       # Tax type: IVA
                etree.SubElement(impuesto, 'CodigoTarifaIVA').text = '01'  # Rate code: 0%
                etree.SubElement(impuesto, 'Tarifa').text = '0.00'
                etree.SubElement(impuesto, 'Monto').text = '0.00000'

            etree.SubElement(linea_detalle, 'ImpuestoAsumidoEmisorFabrica').text = '0.00000'
            etree.SubElement(linea_detalle, 'ImpuestoNeto').text = '%.5f' % total_tax

            # MontoTotalLinea
            etree.SubElement(linea_detalle, 'MontoTotalLinea').text = '%.5f' % ld['total']

    # CodigoTarifaIVA mapping: tax rate percentage -> Hacienda rate code
    # Per Hacienda v4.4 Anexo: 01=0%, 02=1%, 03=2%, 04=4%, 05=transitorio,
    # 06=8%, 07=4% canasta basica, 08=13%, 09=0.5% reducida
    TARIFA_IVA_MAP = {
        0.0: ('01', '0.00'),    # Exento / 0%
        0.5: ('09', '0.50'),    # Tarifa reducida 0.5%
        1.0: ('02', '1.00'),    # Tarifa reducida 1%
        2.0: ('03', '2.00'),    # Tarifa reducida 2%
        4.0: ('04', '4.00'),    # Tarifa reducida 4%
        8.0: ('06', '8.00'),    # Tarifa reducida 8%
        13.0: ('08', '13.00'),  # Tarifa general 13%
    }

    def _add_line_tax(self, linea_detalle, line, base_amount):
        """Add tax information to line item (v4.4: each tax is a separate Impuesto element).

        Returns:
            float: Total tax amount for the line.
        """
        total_tax = 0.0

        for tax in line.tax_ids:
            # Each tax gets its own Impuesto element in v4.4
            impuesto = etree.SubElement(linea_detalle, 'Impuesto')

            tax_amount_percent = tax.amount

            # Codigo = Tax TYPE code (01=IVA for all value-added taxes)
            # CodigoTarifaIVA = Tax RATE code (01=0%, 02=1%, 03=2%, 04=4%, 08=13%)
            codigo_tipo = '01'  # IVA (all CR taxes are IVA variants)
            tarifa_info = self.TARIFA_IVA_MAP.get(tax_amount_percent)
            if tarifa_info:
                codigo_tarifa, tarifa = tarifa_info
            else:
                # Unknown rate: find closest valid rate to avoid code/tarifa mismatch
                # Hacienda rejects if code doesn't match tarifa (e.g. code 08 with 15%)
                _logger.warning('Tax rate %.1f%% not in TARIFA_IVA_MAP, mapping to closest valid rate', tax_amount_percent)
                closest_rate = min(self.TARIFA_IVA_MAP.keys(), key=lambda r: abs(r - tax_amount_percent))
                codigo_tarifa, tarifa = self.TARIFA_IVA_MAP[closest_rate]

            etree.SubElement(impuesto, 'Codigo').text = codigo_tipo
            etree.SubElement(impuesto, 'CodigoTarifaIVA').text = codigo_tarifa
            etree.SubElement(impuesto, 'Tarifa').text = tarifa

            # Calculate tax amount
            tax_amount = base_amount * (float(tarifa) / 100)
            etree.SubElement(impuesto, 'Monto').text = '%.5f' % tax_amount
            total_tax += tax_amount

        return total_tax

    def _get_default_cabys_code(self):
        """Get the default CABYS code from system parameter.

        Configurable via Settings > Technical > System Parameters:
            key: l10n_cr_einvoice.default_cabys_code
        If not set, raises UserError so the user is aware they need to
        configure CABYS codes on their products.
        """
        default_code = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_cr_einvoice.default_cabys_code', ''
        )
        if not default_code:
            raise UserError(_(
                'No CABYS code found for one or more invoice lines, and no '
                'default CABYS code is configured.\n\n'
                'Please either:\n'
                '1. Set the CABYS code on each product/invoice line, or\n'
                '2. Set a default via Settings > Technical > System Parameters:\n'
                '   Key: l10n_cr_einvoice.default_cabys_code\n'
                '   Value: your 13-digit CABYS code'
            ))
        return default_code

    def _get_activity_code(self, company):
        """Get the CIIU activity code for a company, raising if not configured.

        The activity code must match what's registered in Hacienda's RUT
        for the taxpayer. Using a wrong code causes invoice rejection.
        """
        code = getattr(company.partner_id, 'l10n_cr_activity_code', '') or ''
        if not code:
            raise UserError(_(
                'Activity code (Código de Actividad Económica) is not configured '
                'for company "%s".\n\n'
                'Please set it in the partner record or verify your registered '
                'code at: https://www.hacienda.go.cr/ATV/Login.aspx'
            ) % company.name)
        return code

    def _format_activity_code(self, code):
        """Format activity code for CodigoActividadEmisor (6 digits).

        Hacienda uses CIIU Rev.4 codes with trailing zeros to fill 6 digits.
        Example: CIIU class 9311 → '931100' (NOT '009311').
        """
        code = str(code).strip()
        if len(code) >= 6:
            return code[:6]
        # Pad with TRAILING zeros (CIIU sub-levels)
        return code.ljust(6, '0')

    def _get_exchange_rate(self, source_doc):
        """Get exchange rate for the invoice currency to CRC.

        Per Hacienda v4.4: TipoCambio is always relative to CRC (colones).
        If currency IS CRC, rate = 1. Otherwise, look up from company rates.

        Returns:
            float: Exchange rate (e.g. 530.50 for USD)
        """
        currency = source_doc.currency_id
        if not currency or currency.name == 'CRC':
            return 1.0

        # Get CRC currency
        crc = self.env['res.currency'].search([('name', '=', 'CRC')], limit=1)
        if not crc:
            _logger.warning('CRC currency not found, defaulting TipoCambio to 1.0')
            return 1.0

        # Get the invoice date for rate lookup
        if hasattr(source_doc, 'invoice_date') and source_doc.invoice_date:
            rate_date = source_doc.invoice_date
        elif hasattr(source_doc, 'date_order') and source_doc.date_order:
            rate_date = source_doc.date_order.date()
        else:
            rate_date = fields.Date.today()

        # Use Odoo's built-in rate conversion: how many CRC per 1 unit of invoice currency
        company = source_doc.company_id
        rate = currency._get_conversion_rate(currency, crc, company, rate_date)
        if rate and rate > 0:
            return round(rate, 5)

        _logger.warning(
            'No exchange rate found for %s→CRC on %s, defaulting to 1.0',
            currency.name, rate_date,
        )
        return 1.0

    def _is_service_line(self, line_data):
        """Determine if a line represents a service (vs merchandise).

        Classification is based on the CABYS code that will actually be emitted
        in the XML, ensuring consistency between DetalleServicio and ResumenFactura.

        CABYS codes starting with '96'-'99' are service categories per Hacienda.
        When no CABYS code is configured, falls back to the system parameter
        l10n_cr_einvoice.default_cabys_code
        (Sports/recreation facility services), which is a service category.

        Args:
            line_data: dict from _compute_line_amounts()

        Returns:
            bool: True if service, False if merchandise
        """
        line = line_data['line']
        product = line.product_id if hasattr(line, 'product_id') else None

        # Resolve the CABYS code exactly as _add_detalle_servicio does
        cabys_code = getattr(line, 'l10n_cr_product_code', '') or ''
        if not cabys_code and product:
            cabys_code = getattr(product.product_tmpl_id, 'l10n_cr_cabys_code', '') or ''
        if not cabys_code:
            cabys_code = self._get_default_cabys_code()

        # CABYS prefixes 96-99 are service categories per Hacienda classification
        if cabys_code[:2] in ('96', '97', '98', '99'):
            return True

        # All other CABYS prefixes are merchandise/goods
        return False

    def _add_resumen_factura(self, root, source_doc, lines_data=None):
        """Add ResumenFactura (invoice summary).

        Computes totals from line-level data to ensure consistency between
        DetalleServicio and ResumenFactura. This avoids the issue where
        POS order's amount_tax=0 even when lines have taxes configured.

        Args:
            root: XML root element
            source_doc: account.move or pos.order record
            lines_data: Pre-computed line amounts from _compute_line_amounts()
        """
        if lines_data is None:
            lines_data = self._compute_line_amounts(source_doc)

        resumen = etree.SubElement(root, 'ResumenFactura')

        # Currency and exchange rate
        currency_name = source_doc.currency_id.name if source_doc.currency_id else 'CRC'
        currency_codes = {'CRC': 'CRC', 'USD': 'USD', 'EUR': 'EUR'}
        currency_code = currency_codes.get(currency_name, 'CRC')
        tipo_cambio = self._get_exchange_rate(source_doc)
        codigo_moneda = etree.SubElement(resumen, 'CodigoTipoMoneda')
        etree.SubElement(codigo_moneda, 'CodigoMoneda').text = currency_code
        etree.SubElement(codigo_moneda, 'TipoCambio').text = '%.5f' % tipo_cambio

        # Compute totals from line data, classifying service vs merchandise
        # Per Hacienda v4.4 XSD:
        #   TotalServGravados etc. = amounts BEFORE discount (subtotal per line)
        #   TotalVenta = sum of all category totals (before discount)
        #   TotalDescuentos = sum of all discount amounts
        #   TotalVentaNeta = TotalVenta - TotalDescuentos
        #   TotalComprobante = TotalVentaNeta + TotalImpuesto
        total_descuentos = sum(ld['discount_amount'] for ld in lines_data)
        amount_tax = sum(ld['tax_amount'] for ld in lines_data)

        # Classify lines into service vs merchandise with 4-way tax classification:
        #   Gravado:   has IVA tax with rate > 0%
        #   Exento:    has IVA tax with rate = 0% (explicitly exempt)
        #   NoSujeto:  has NO tax at all (outside IVA scope)
        #   Exonerado: exonerated by decree (not implemented for gym)
        # Use 'subtotal' (qty * price_unit, before discount) for category totals
        total_serv_gravados = 0.0
        total_serv_exentos = 0.0
        total_serv_no_sujeto = 0.0
        total_merc_gravadas = 0.0
        total_merc_exentas = 0.0
        total_merc_no_sujeta = 0.0

        for ld in lines_data:
            is_service = self._is_service_line(ld)
            has_tax = bool(ld['line'].tax_ids)
            is_taxed = ld['tax_amount'] > 0
            amount = ld['subtotal']  # Before discount

            if is_service:
                if is_taxed:
                    total_serv_gravados += amount
                elif has_tax:
                    total_serv_exentos += amount  # Has 0% IVA tax
                else:
                    total_serv_no_sujeto += amount  # No tax at all
            else:
                if is_taxed:
                    total_merc_gravadas += amount
                elif has_tax:
                    total_merc_exentas += amount
                else:
                    total_merc_no_sujeta += amount

        total_gravado = total_serv_gravados + total_merc_gravadas
        total_exento = total_serv_exentos + total_merc_exentas
        total_no_sujeto = total_serv_no_sujeto + total_merc_no_sujeta
        total_venta = total_gravado + total_exento + total_no_sujeto
        total_venta_neta = total_venta - total_descuentos
        amount_total = total_venta_neta + amount_tax

        # Totals - per XSD v4.4 sequence order; only emit non-zero (all are minOccurs=0)
        fmt = '%.5f'
        if total_serv_gravados:
            etree.SubElement(resumen, 'TotalServGravados').text = fmt % total_serv_gravados
        if total_serv_exentos:
            etree.SubElement(resumen, 'TotalServExentos').text = fmt % total_serv_exentos
        if total_serv_no_sujeto:
            etree.SubElement(resumen, 'TotalServNoSujeto').text = fmt % total_serv_no_sujeto
        if total_merc_gravadas:
            etree.SubElement(resumen, 'TotalMercanciasGravadas').text = fmt % total_merc_gravadas
        if total_merc_exentas:
            etree.SubElement(resumen, 'TotalMercanciasExentas').text = fmt % total_merc_exentas
        if total_merc_no_sujeta:
            etree.SubElement(resumen, 'TotalMercNoSujeta').text = fmt % total_merc_no_sujeta
        if total_gravado:
            etree.SubElement(resumen, 'TotalGravado').text = fmt % total_gravado
        if total_exento:
            etree.SubElement(resumen, 'TotalExento').text = fmt % total_exento
        if total_no_sujeto:
            etree.SubElement(resumen, 'TotalNoSujeto').text = fmt % total_no_sujeto
        etree.SubElement(resumen, 'TotalVenta').text = fmt % total_venta
        etree.SubElement(resumen, 'TotalDescuentos').text = fmt % total_descuentos
        etree.SubElement(resumen, 'TotalVentaNeta').text = fmt % total_venta_neta

        # v4.4: TotalDesgloseImpuesto - tax breakdown by code (BEFORE TotalImpuesto)
        # Aggregate tax amounts by (Codigo, CodigoTarifaIVA) across all lines
        tax_desglose = {}
        for ld in lines_data:
            for tb in ld.get('tax_breakdown', []):
                key = (tb['codigo'], tb['codigo_tarifa'])
                tax_desglose[key] = tax_desglose.get(key, 0.0) + tb['amount']

        for (codigo, codigo_tarifa), total_monto in sorted(tax_desglose.items()):
            if total_monto > 0:
                desglose = etree.SubElement(resumen, 'TotalDesgloseImpuesto')
                etree.SubElement(desglose, 'Codigo').text = codigo
                etree.SubElement(desglose, 'CodigoTarifaIVA').text = codigo_tarifa
                etree.SubElement(desglose, 'TotalMontoImpuesto').text = fmt % total_monto

        if amount_tax > 0:
            etree.SubElement(resumen, 'TotalImpuesto').text = fmt % amount_tax

        # v4.4: MedioPago is now inside ResumenFactura (complex type)
        self._add_medio_pago(resumen, source_doc)

        etree.SubElement(resumen, 'TotalComprobante').text = '%.5f' % amount_total

    def _add_informacion_referencia(self, root, original_move):
        """Add InformacionReferencia for credit/debit notes."""
        numero_ref = original_move.l10n_cr_clave or original_move.name or ''
        if not numero_ref:
            raise UserError(_(
                'El documento de referencia no tiene clave de Hacienda ni número de documento.\n'
                'No se puede generar la InformacionReferencia sin un número de referencia.'
            ))

        info_ref = etree.SubElement(root, 'InformacionReferencia')

        # Reference type: 01 = Anula documento de referencia
        etree.SubElement(info_ref, 'TipoDocIR').text = '01'
        etree.SubElement(info_ref, 'Numero').text = numero_ref
        # XSD requires xs:dateTime format YYYY-MM-DDTHH:MM:SS (not just YYYY-MM-DD)
        ref_date = original_move.invoice_date
        if not ref_date:
            raise ValidationError(_('Referenced document %s has no invoice date.') % numero_ref)
        etree.SubElement(info_ref, 'FechaEmisionIR').text = datetime.combine(
            ref_date, datetime.min.time()
        ).isoformat()
        etree.SubElement(info_ref, 'Codigo').text = '01'  # Reference code
        etree.SubElement(info_ref, 'Razon').text = 'Anulación de factura'

    def _get_company_id_type(self, vat):
        """Get company identification type code based on VAT length."""
        if not vat:
            return '02'
        clean_vat = vat.replace('-', '').replace(' ', '')
        length = len(clean_vat)
        if length == 9:
            return '01'  # Cédula Física
        elif length == 10 and clean_vat.startswith('10'):
            return '04'  # NITE (check before generic jurídica)
        elif length == 10:
            return '02'  # Cédula Jurídica
        elif length in (11, 12):
            return '03'  # DIMEX
        return '02'  # Default to Jurídica

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

    def _sanitize_text(self, text, min_len=0, max_len=999, default=''):
        """Sanitize text to comply with XSD string length constraints.

        Args:
            text: Input text (may be None/empty)
            min_len: Minimum length required by XSD
            max_len: Maximum length allowed by XSD
            default: Default value if text is empty and min_len > 0

        Returns:
            str: Sanitized text within length bounds
        """
        if not text or not str(text).strip():
            if min_len > 0:
                return (default or ' ' * min_len)[:max_len]
            return default
        result = str(text).strip()
        # Truncate to max length
        result = result[:max_len]
        # Pad to min length if needed
        if len(result) < min_len:
            result = result.ljust(min_len)
        return result

    # ===== PRE-FLIGHT VALIDATION METHODS =====

    def _validate_before_generation(self, einvoice):
        """
        Comprehensive pre-flight validation before XML generation.

        Validates:
        - Mandatory fields based on document type
        - Company certificate validity
        - Partner data format (cédula, email)
        - CIIU code (date-based enforcement)
        - Validation rules from l10n_cr.validation.rule

        Args:
            einvoice: l10n_cr.einvoice.document record

        Raises:
            UserError: If validation fails with actionable Spanish error message
        """
        # Note: No ensure_one() - this is an AbstractModel (no DB records).
        # Called via self.env['l10n_cr.xml.generator'] which returns empty recordset.
        errors = []

        _logger.info(
            'Starting pre-flight validation for document %s (type: %s)',
            einvoice.name,
            einvoice.document_type
        )

        # Get source document
        if einvoice.move_id:
            source_doc = einvoice.move_id
        elif einvoice.pos_order_id:
            source_doc = einvoice.pos_order_id
        else:
            raise UserError(_(
                'Error de Configuración\n'
                '══════════════════════\n\n'
                'El comprobante electrónico debe estar vinculado a una Factura o Orden de POS.\n\n'
                'Documento: %s'
            ) % einvoice.name)

        # 1. Validate Company Certificate
        certificate_errors = self._validate_company_certificate(einvoice.company_id)
        if certificate_errors:
            errors.extend(certificate_errors)

        # 2. Document Type Specific Validation
        if einvoice.document_type == 'FE':
            fe_errors = self._validate_factura_requirements(einvoice, source_doc)
            if fe_errors:
                errors.extend(fe_errors)
        elif einvoice.document_type == 'TE':
            # Tiquete has minimal requirements
            te_errors = self._validate_tiquete_requirements(einvoice, source_doc)
            if te_errors:
                errors.extend(te_errors)
        elif einvoice.document_type in ('NC', 'ND'):
            # Credit/Debit notes need reference validation
            ref_errors = self._validate_reference_document(einvoice, source_doc)
            if ref_errors:
                errors.extend(ref_errors)

        # 3. Run configurable validation rules
        if self.env['l10n_cr.validation.rule'].search_count([('active', '=', True)]) > 0:
            try:
                is_valid, rule_errors = self.env['l10n_cr.validation.rule'].validate_all_rules(einvoice)
                if not is_valid and rule_errors:
                    errors.extend(rule_errors)
            except ValidationError as e:
                # Re-raise blocking validation errors
                raise
            except Exception as e:
                _logger.error('Error running validation rules: %s', str(e))
                errors.append(f'Error en reglas de validación: {str(e)}')

        # If errors found, raise with formatted message
        if errors:
            error_count = len(errors)
            error_list = '\n'.join(f'  • {err}' for err in errors)

            raise UserError(_(
                'No se puede generar el comprobante electrónico\n'
                '════════════════════════════════════════════\n\n'
                'Se encontraron {count} errores de validación:\n\n'
                '{errors}\n\n'
                '──────────────────────────────────────────\n'
                'Documento: {doc_name}\n'
                'Tipo: {doc_type}\n'
                'Cliente: {partner}\n\n'
                'Por favor corrija estos errores antes de continuar.'
            ).format(
                count=error_count,
                errors=error_list,
                doc_name=einvoice.name,
                doc_type=dict(einvoice._fields['document_type'].selection).get(einvoice.document_type),
                partner=einvoice.partner_id.name if einvoice.partner_id else 'N/A'
            ))

        _logger.info(
            'Pre-flight validation passed for document %s',
            einvoice.name
        )

    def _validate_company_certificate(self, company):
        """
        Validate company signing certificate.

        Args:
            company: res.company record

        Returns:
            list: Error messages (empty if valid)
        """
        errors = []

        # Get active credentials based on environment.
        # Note: l10n_cr_active_* fields are computed from the current environment
        # (sandbox/production) setting. Both validation and signing use the same
        # active certificate through these computed fields. Here we resolve the
        # env-specific fields directly for explicit error messages, but the
        # result is equivalent to using l10n_cr_active_certificate etc.
        if company.l10n_cr_hacienda_env == 'production':
            certificate = company.l10n_cr_prod_certificate
            certificate_filename = company.l10n_cr_prod_certificate_filename
            private_key = company.l10n_cr_prod_private_key
            key_password = company.l10n_cr_prod_key_password
        else:
            certificate = company.l10n_cr_certificate
            certificate_filename = company.l10n_cr_certificate_filename
            private_key = company.l10n_cr_private_key
            key_password = company.l10n_cr_key_password

        env_label = 'Producción' if company.l10n_cr_hacienda_env == 'production' else 'Sandbox'

        # Check certificate presence
        if not certificate:
            errors.append(
                f'Certificado digital no configurado para el ambiente {env_label}. '
                'Configure el certificado en Configuración > Compañía > Hacienda'
            )
            return errors

        # For .p12/.pfx files, private key is embedded in the certificate file.
        # Only require separate private_key for PEM format.
        is_pkcs12 = (certificate_filename or '').lower().endswith(('.p12', '.pfx'))
        if not is_pkcs12 and not private_key:
            errors.append(
                f'Llave privada no configurada para el ambiente {env_label}. '
                'Para certificados PEM (.pem/.crt) se requiere un archivo de llave privada separado. '
                'Para certificados PKCS#12 (.p12/.pfx), la llave está incluida en el archivo.'
            )

        if not key_password:
            errors.append(
                f'Contraseña/PIN del certificado no configurada para el ambiente {env_label}'
            )

        return errors

    def _validate_factura_requirements(self, einvoice, source_doc):
        """
        Validate Factura Electrónica (FE) specific requirements.

        FE Requirements (Hacienda v4.4):
        - Customer (partner) required
        - Customer name required
        - Customer VAT/ID required (valid format)
        - Customer ID type required (01-05)
        - Customer email required (valid format)
        - Customer CIIU required (after Oct 6, 2025)

        Args:
            einvoice: l10n_cr.einvoice.document record
            source_doc: account.move or pos.order record

        Returns:
            list: Error messages (empty if valid)
        """
        errors = []
        partner = einvoice.partner_id

        # 1. Partner required
        if not partner:
            errors.append(
                'La Factura Electrónica requiere un cliente. '
                'Seleccione un cliente o cambie a Tiquete Electrónico (TE)'
            )
            return errors  # Can't continue without partner

        # 2. Partner name required
        if not partner.name or not partner.name.strip():
            errors.append(
                'El nombre del cliente es obligatorio. '
                'Cliente ID: {partner_id}'.format(partner_id=partner.id)
            )

        # 3. Partner VAT/ID required and format validation
        if not partner.vat or not partner.vat.strip():
            errors.append(
                'El número de cédula/identificación del cliente es obligatorio. '
                'Cliente: {partner}'.format(partner=partner.name)
            )
        else:
            # Validate VAT format
            vat_errors = self._validate_cedula_format(partner)
            if vat_errors:
                errors.extend(vat_errors)

        # 4. ID Type - auto-detected from VAT format via _get_partner_id_type()
        # No explicit field check needed; type is derived from VAT at XML generation time

        # 5. Email required and format validation
        if not partner.email or not partner.email.strip():
            errors.append(
                'El correo electrónico del cliente es obligatorio según normativa de Hacienda. '
                'Cliente: {partner}'.format(partner=partner.name)
            )
        else:
            # Validate email format
            email_errors = self._validate_email_format(partner.email, partner.name)
            if email_errors:
                errors.extend(email_errors)

        # 6. CIIU code (date-based enforcement)
        invoice_date = einvoice.invoice_date or fields.Date.today()
        ciiu_mandatory_date = self._get_ciiu_mandatory_date()

        if invoice_date >= ciiu_mandatory_date:
            if not partner.l10n_cr_economic_activity_id:
                errors.append(
                    'El código de actividad económica (CIIU) del cliente es obligatorio '
                    'para facturas desde el {date}. '
                    'Fecha factura: {invoice_date}. '
                    'Cliente: {partner}'.format(
                        date=ciiu_mandatory_date.strftime('%d/%m/%Y'),
                        invoice_date=invoice_date.strftime('%d/%m/%Y'),
                        partner=partner.name
                    )
                )

        return errors

    def _validate_tiquete_requirements(self, einvoice, source_doc):
        """
        Validate Tiquete Electrónico (TE) requirements.

        TE has minimal requirements - mainly company data.

        Args:
            einvoice: l10n_cr.einvoice.document record
            source_doc: account.move or pos.order record

        Returns:
            list: Error messages (empty if valid)
        """
        errors = []

        # Tiquete doesn't require customer data
        # But we still validate company fields
        company = einvoice.company_id

        if not company.vat:
            errors.append('La compañía debe tener un número de cédula jurídica configurado')

        if not company.l10n_cr_emisor_location:
            errors.append('La ubicación del emisor no está configurada en la compañía')

        return errors

    def _validate_reference_document(self, einvoice, source_doc):
        """
        Validate credit/debit note reference to original document.

        Args:
            einvoice: l10n_cr.einvoice.document record
            source_doc: account.move record

        Returns:
            list: Error messages (empty if valid)
        """
        errors = []

        if einvoice.document_type == 'NC':
            # Credit note requires reversed_entry_id
            if not source_doc.reversed_entry_id:
                errors.append(
                    'La Nota de Crédito debe referenciar una factura original. '
                    'No se encontró reversed_entry_id en la factura'
                )
            elif not source_doc.reversed_entry_id.l10n_cr_clave:
                errors.append(
                    'La factura original no tiene clave de Hacienda. '
                    'Factura original: {invoice}'.format(
                        invoice=source_doc.reversed_entry_id.name
                    )
                )

        elif einvoice.document_type == 'ND':
            # Debit note requires debit_origin_id
            if not source_doc.debit_origin_id:
                errors.append(
                    'La Nota de Débito debe referenciar una factura original. '
                    'No se encontró debit_origin_id en la factura'
                )
            elif not source_doc.debit_origin_id.l10n_cr_clave:
                errors.append(
                    'La factura original no tiene clave de Hacienda. '
                    'Factura original: {invoice}'.format(
                        invoice=source_doc.debit_origin_id.name
                    )
                )

        return errors

    def _validate_cedula_format(self, partner):
        """
        Validate Costa Rica cédula/ID format based on ID type.

        Formats (Hacienda v4.4):
        - 01 (Física): 9 digits
        - 02 (Jurídica): 10 digits
        - 03 (DIMEX): 11-12 digits
        - 04 (NITE): 10 digits
        - 05 (Extranjero): max 20 characters

        Args:
            partner: res.partner record

        Returns:
            list: Error messages (empty if valid)
        """
        errors = []

        if not partner.vat:
            return errors  # Already checked elsewhere

        clean_vat = partner.vat.replace('-', '').replace(' ', '').strip()
        id_code = self._get_partner_id_type(partner.vat)

        # Validate based on type
        if id_code == '01':  # Cédula Física
            if not clean_vat.isdigit() or len(clean_vat) != 9:
                errors.append(
                    'Formato inválido de Cédula Física. '
                    'Debe tener exactamente 9 dígitos. '
                    'Valor actual: {vat} ({length} caracteres). '
                    'Cliente: {partner}'.format(
                        vat=clean_vat,
                        length=len(clean_vat),
                        partner=partner.name
                    )
                )

        elif id_code == '02':  # Cédula Jurídica
            if not clean_vat.isdigit() or len(clean_vat) != 10:
                errors.append(
                    'Formato inválido de Cédula Jurídica. '
                    'Debe tener exactamente 10 dígitos. '
                    'Valor actual: {vat} ({length} caracteres). '
                    'Cliente: {partner}'.format(
                        vat=clean_vat,
                        length=len(clean_vat),
                        partner=partner.name
                    )
                )

        elif id_code == '03':  # DIMEX
            if not clean_vat.isdigit() or len(clean_vat) not in [11, 12]:
                errors.append(
                    'Formato inválido de DIMEX. '
                    'Debe tener 11 o 12 dígitos. '
                    'Valor actual: {vat} ({length} caracteres). '
                    'Cliente: {partner}'.format(
                        vat=clean_vat,
                        length=len(clean_vat),
                        partner=partner.name
                    )
                )

        elif id_code == '04':  # NITE
            if not clean_vat.isdigit() or len(clean_vat) != 10:
                errors.append(
                    'Formato inválido de NITE. '
                    'Debe tener exactamente 10 dígitos. '
                    'Valor actual: {vat} ({length} caracteres). '
                    'Cliente: {partner}'.format(
                        vat=clean_vat,
                        length=len(clean_vat),
                        partner=partner.name
                    )
                )

        elif id_code == '05':  # Foreign ID
            if len(clean_vat) > 20:
                errors.append(
                    'Formato inválido de Identificación Extranjera. '
                    'No puede exceder 20 caracteres. '
                    'Valor actual: {vat} ({length} caracteres). '
                    'Cliente: {partner}'.format(
                        vat=clean_vat,
                        length=len(clean_vat),
                        partner=partner.name
                    )
                )

        return errors

    def _validate_email_format(self, email, partner_name=''):
        """
        Validate email address format.

        Args:
            email: Email address string
            partner_name: Partner name for error message

        Returns:
            list: Error messages (empty if valid)
        """
        errors = []

        if not email:
            return errors  # Already checked elsewhere

        # RFC 5322 simplified email regex
        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        clean_email = email.strip()

        if not EMAIL_REGEX.match(clean_email):
            context = f'Cliente: {partner_name}' if partner_name else ''
            errors.append(
                'Formato inválido de correo electrónico. '
                'Valor actual: {email}. '
                '{context}'.format(
                    email=clean_email,
                    context=context
                )
            )

        return errors
