# -*- coding: utf-8 -*-
import base64
import logging
from lxml import etree
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoicePDFGenerator(models.AbstractModel):
    """
    Advanced PDF generator for Costa Rica electronic invoices.

    Generates Costa Rica compliant PDF invoices with:
    - QR code for invoice verification
    - Company branding (logo, colors)
    - All required Hacienda fields
    - Digital signature status
    - Hacienda acceptance status
    - Multi-language support (Spanish primary, English optional)
    - PDF/A-3 compliance for archival

    QR Code Content:
    - Hacienda verification URL
    - Clave (50-digit unique identifier)
    - Emisor ID and type
    - Receptor ID and type
    - Total amount
    - Tax amount
    """
    _name = 'l10n_cr.einvoice.pdf.generator'
    _description = 'Costa Rica E-Invoice PDF Generator'

    @api.model
    def generate_pdf_for_document(self, document):
        """
        Generate PDF for an electronic invoice document.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            tuple: (pdf_content bytes, filename str)

        Raises:
            UserError: If generation fails
        """
        document.ensure_one()

        # Validate document has required data
        if not document.clave:
            raise UserError(_('Cannot generate PDF: Document has no clave'))

        if not document.xml_content and not document.signed_xml:
            raise UserError(_('Cannot generate PDF: No XML content available'))

        try:
            # Get the PDF report action
            report = self.env.ref('l10n_cr_einvoice.action_report_einvoice')

            # Generate PDF using QWeb
            pdf_content, _ = report._render_qweb_pdf([document.id])

            # Generate filename
            filename = self._generate_filename(document)

            _logger.info(f'Generated PDF for document {document.name}: {filename}')

            return (pdf_content, filename)

        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error generating PDF for {document.name}: {error_msg}')
            raise UserError(_('Error generating PDF: %s') % error_msg)

    @api.model
    def _generate_filename(self, document):
        """
        Generate PDF filename according to Costa Rica standards.

        Format: {DocumentType}_{Clave}.pdf
        Example: FE_50612345678901234567890123456789012345678901234.pdf

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            str: Filename
        """
        doc_type_prefix = {
            'FE': 'FacturaElectronica',
            'TE': 'TiqueteElectronico',
            'NC': 'NotaCreditoElectronica',
            'ND': 'NotaDebitoElectronica',
        }

        prefix = doc_type_prefix.get(document.document_type, 'Documento')

        if document.clave:
            return f'{prefix}_{document.clave}.pdf'
        else:
            return f'{prefix}_{document.name}.pdf'

    @api.model
    def create_pdf_attachment(self, document):
        """
        Generate PDF and create attachment record.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            ir.attachment record
        """
        # Generate PDF
        pdf_content, filename = self.generate_pdf_for_document(document)

        # Check if attachment already exists
        if document.pdf_attachment_id:
            # Update existing attachment
            document.pdf_attachment_id.write({
                'datas': base64.b64encode(pdf_content),
                'name': filename,
            })
            _logger.info(f'Updated PDF attachment for {document.name}')
            return document.pdf_attachment_id
        else:
            # Create new attachment
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': document._name,
                'res_id': document.id,
                'mimetype': 'application/pdf',
                'description': _(
                    'Electronic invoice PDF with QR code - %s'
                ) % document.name,
            })

            _logger.info(f'Created PDF attachment for {document.name}')
            return attachment

    @api.model
    def get_qr_code_data(self, document):
        """
        Generate QR code data for PDF embedding.

        QR Code Format (Hacienda specification):
        https://tribunet.hacienda.go.cr/docs/esquemas/2017/v4.3/comprobantes/verificacion
        clave={50-digit-clave}
        emisor={id-type}-{id-number}
        receptor={id-type}-{id-number}
        total={total-amount}
        tax={tax-amount}

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            dict: QR code data for template
        """
        # Get QR code generator
        qr_generator = self.env['l10n_cr.qr.generator']

        # Generate QR code image (base64 PNG)
        qr_image = qr_generator.generate_qr_code_for_document(document)

        # Build verification URL
        verification_url = self._build_verification_url(document)

        return {
            'qr_image': qr_image,
            'verification_url': verification_url,
        }

    @api.model
    def _build_verification_url(self, document):
        """
        Build Hacienda verification URL with all required parameters.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            str: Complete verification URL
        """
        base_url = 'https://tribunet.hacienda.go.cr/docs/esquemas/2017/v4.3/comprobantes/verificacion'

        # Get emisor ID
        emisor_id_type = document.company_id.l10n_cr_identification_type or '02'
        emisor_id_number = (document.company_id.vat or '').replace('-', '')
        emisor = f'{emisor_id_type}-{emisor_id_number}'

        # Get receptor ID
        receptor_id_type = document.partner_id.l10n_cr_identification_type or '01'
        receptor_id_number = (document.partner_id.vat or '').replace('-', '')
        receptor = f'{receptor_id_type}-{receptor_id_number}'

        # Get amounts
        total_amount = document.amount_total
        tax_amount = document.move_id.amount_tax if document.move_id else 0

        # Build URL with parameters
        url = (
            f'{base_url}?'
            f'clave={document.clave}&'
            f'emisor={emisor}&'
            f'receptor={receptor}&'
            f'total={total_amount:.2f}&'
            f'tax={tax_amount:.2f}'
        )

        return url

    @api.model
    def get_document_data_for_pdf(self, document):
        """
        Prepare all document data needed for PDF template.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            dict: Complete document data
        """
        move = document.move_id

        # Parse XML for additional data
        xml_data = self._parse_xml_for_display(document)

        # Company (Emisor) data
        emisor_data = {
            'name': document.company_id.name,
            'vat': document.company_id.vat,
            'id_type': self._get_id_type_name(
                document.company_id.l10n_cr_identification_type
            ),
            'street': document.company_id.street or '',
            'street2': document.company_id.street2 or '',
            'city': document.company_id.city or '',
            'state': document.company_id.state_id.name if document.company_id.state_id else '',
            'zip': document.company_id.zip or '',
            'country': document.company_id.country_id.name if document.company_id.country_id else '',
            'phone': document.company_id.phone or '',
            'email': document.company_id.email or '',
            'logo': document.company_id.logo if hasattr(document.company_id, 'logo') else False,
        }

        # Customer (Receptor) data
        receptor_data = {
            'name': document.partner_id.name,
            'vat': document.partner_id.vat or '',
            'id_type': self._get_id_type_name(
                document.partner_id.l10n_cr_identification_type
            ),
            'street': document.partner_id.street or '',
            'street2': document.partner_id.street2 or '',
            'city': document.partner_id.city or '',
            'state': document.partner_id.state_id.name if document.partner_id.state_id else '',
            'zip': document.partner_id.zip or '',
            'country': document.partner_id.country_id.name if document.partner_id.country_id else '',
            'phone': document.partner_id.phone or '',
            'email': document.partner_id.email or '',
        }

        # Document details
        document_data = {
            'type': document.document_type,
            'type_name': dict(document._fields['document_type'].selection).get(
                document.document_type
            ),
            'number': document.name,
            'clave': document.clave,
            'date': document.invoice_date,
            'state': document.state,
            'state_name': dict(document._fields['state'].selection).get(document.state),
            'acceptance_date': document.hacienda_acceptance_date,
            'submission_date': document.hacienda_submission_date,
        }

        # Line items
        lines_data = []
        line_number = 1
        for line in move.invoice_line_ids:
            if line.display_type:
                continue

            lines_data.append({
                'number': line_number,
                'name': line.name,
                'product_code': line.product_id.default_code or '',
                'cabys_code': line.l10n_cr_cabys_code or '',
                'quantity': line.quantity,
                'uom': line.product_uom_id.name if line.product_uom_id else '',
                'price_unit': line.price_unit,
                'discount': line.discount,
                'subtotal': line.price_subtotal,
                'tax_amount': sum(line.tax_ids.mapped('amount')),
                'total': line.price_total,
            })
            line_number += 1

        # Tax breakdown
        tax_data = []
        for tax_group in move.amount_by_group:
            tax_data.append({
                'name': tax_group[0],
                'amount': tax_group[1],
                'base': tax_group[2] if len(tax_group) > 2 else 0,
            })

        # Totals
        totals_data = {
            'subtotal': move.amount_untaxed,
            'discount': sum(
                line.discount * line.price_unit * line.quantity / 100
                for line in move.invoice_line_ids
                if not line.display_type
            ),
            'tax': move.amount_tax,
            'total': move.amount_total,
        }

        # Payment method
        payment_data = {
            'method': '',
            'term': move.invoice_payment_term_id.name if move.invoice_payment_term_id else '',
        }

        if hasattr(move, 'l10n_cr_payment_method_id') and move.l10n_cr_payment_method_id:
            payment_data['method'] = move.l10n_cr_payment_method_id.name

        # Notes
        notes = move.narration or ''

        return {
            'emisor': emisor_data,
            'receptor': receptor_data,
            'document': document_data,
            'lines': lines_data,
            'taxes': tax_data,
            'totals': totals_data,
            'payment': payment_data,
            'notes': notes,
            'xml_data': xml_data,
        }

    @api.model
    def _parse_xml_for_display(self, document):
        """
        Parse XML content for additional display data.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            dict: Parsed XML data
        """
        xml_content = document.signed_xml or document.xml_content

        if not xml_content:
            return {}

        try:
            root = etree.fromstring(xml_content.encode('utf-8'))

            # Extract namespace
            ns = {'fe': 'https://tribunet.hacienda.go.cr/docs/esquemas/2017/v4.3/facturaElectronica'}

            # Extract additional data from XML
            xml_data = {
                'consecutive': self._get_xml_text(root, './/fe:NumeroConsecutivo', ns),
                'condition_sale': self._get_xml_text(root, './/fe:CondicionVenta', ns),
                'credit_days': self._get_xml_text(root, './/fe:PlazoCredito', ns),
            }

            return xml_data

        except Exception as e:
            _logger.warning(f'Could not parse XML for display: {e}')
            return {}

    @api.model
    def _get_xml_text(self, root, xpath, namespaces):
        """
        Safely extract text from XML element.

        Args:
            root: lxml element
            xpath: XPath expression
            namespaces: Namespace dict

        Returns:
            str: Element text or empty string
        """
        try:
            element = root.find(xpath, namespaces)
            return element.text if element is not None else ''
        except:
            return ''

    @api.model
    def _get_id_type_name(self, id_type_code):
        """
        Get identification type name from code.

        Args:
            id_type_code: Identification type code (01, 02, 03, 04)

        Returns:
            str: Type name
        """
        id_types = {
            '01': 'Cédula Física',
            '02': 'Cédula Jurídica',
            '03': 'DIMEX',
            '04': 'NITE',
        }
        return id_types.get(id_type_code, 'Otro')

    @api.model
    def generate_batch_pdfs(self, documents):
        """
        Generate PDFs for multiple documents in batch.

        Args:
            documents: l10n_cr.einvoice.document recordset

        Returns:
            dict: Statistics {generated: int, failed: int}
        """
        stats = {'generated': 0, 'failed': 0}

        _logger.info(f'Batch generating PDFs for {len(documents)} documents')

        for doc in documents:
            try:
                self.create_pdf_attachment(doc)
                stats['generated'] += 1
            except Exception as e:
                _logger.error(f'Batch PDF generation failed for {doc.name}: {e}')
                stats['failed'] += 1
                continue

        _logger.info(
            f'Batch PDF generation complete: {stats["generated"]} generated, '
            f'{stats["failed"]} failed'
        )

        return stats
