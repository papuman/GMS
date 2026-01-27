# -*- coding: utf-8 -*-
import logging
import base64
import zipfile
import io
import traceback
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class EInvoiceImportWizard(models.TransientModel):
    _name = 'l10n_cr.einvoice.import.wizard'
    _description = 'E-Invoice Import Wizard'

    # State management
    state = fields.Selection([
        ('upload', 'Upload File'),
        ('processing', 'Processing'),
        ('done', 'Completed'),
    ], string='Status', default='upload', required=True)

    # Step 1: Upload
    upload_file = fields.Binary(
        string='ZIP File with XMLs',
        required=True,
        help='Upload a ZIP file containing Costa Rica e-invoice XML files (v4.4)',
    )

    file_name = fields.Char(
        string='File Name',
    )

    original_provider = fields.Selection([
        ('gti', 'GTI Costa Rica'),
        ('facturatica', 'FACTURATica'),
        ('ticopay', 'TicoPay'),
        ('alegra', 'Alegra'),
        ('procom', 'PROCOM'),
        ('alanube', 'Alanube'),
        ('other', 'Other Provider'),
    ], string='Previous Provider', help='Select your previous e-invoicing provider')

    other_provider_name = fields.Char(
        string='Provider Name',
        help='Enter provider name if you selected "Other"',
    )

    # Options
    skip_duplicates = fields.Boolean(
        string='Skip Duplicates',
        default=True,
        help='Skip invoices that already exist (based on clave)',
    )

    auto_create_partners = fields.Boolean(
        string='Auto-Create Customers',
        default=True,
        help='Automatically create customer records if they do not exist',
    )

    auto_create_products = fields.Boolean(
        string='Auto-Create Products',
        default=True,
        help='Automatically create product records for unknown Cabys codes',
    )

    validate_signatures = fields.Boolean(
        string='Validate Digital Signatures',
        default=False,
        help='Validate XML digital signatures (slower but more secure)',
    )

    # Processing state
    batch_id = fields.Many2one(
        'l10n_cr.einvoice.import.batch',
        string='Import Batch',
        readonly=True,
    )

    total_files = fields.Integer(
        string='Total Files',
        readonly=True,
    )

    processed_files = fields.Integer(
        string='Processed Files',
        readonly=True,
    )

    successful_imports = fields.Integer(
        string='Successful',
        readonly=True,
    )

    failed_imports = fields.Integer(
        string='Failed',
        readonly=True,
    )

    skipped_duplicates = fields.Integer(
        string='Skipped',
        readonly=True,
    )

    progress_percentage = fields.Float(
        string='Progress',
        compute='_compute_progress',
    )

    # Results
    result_message = fields.Html(
        string='Results',
        readonly=True,
    )

    error_details = fields.Text(
        string='Error Details',
        readonly=True,
    )

    @api.depends('total_files', 'processed_files')
    def _compute_progress(self):
        for wizard in self:
            if wizard.total_files > 0:
                wizard.progress_percentage = (wizard.processed_files / wizard.total_files) * 100
            else:
                wizard.progress_percentage = 0.0

    def action_start_import(self):
        """Start the import process."""
        self.ensure_one()

        if not self.upload_file:
            raise UserError(_('Please upload a ZIP file'))

        # Get provider name
        provider_name = self._get_provider_name()

        # Create batch record
        batch = self.env['l10n_cr.einvoice.import.batch'].create({
            'name': _('Import %s - %s') % (provider_name, fields.Datetime.now().strftime('%Y-%m-%d %H:%M')),
            'company_id': self.env.company.id,
            'original_provider': provider_name,
            'file_name': self.file_name or 'upload.zip',
        })

        self.batch_id = batch

        try:
            # Extract ZIP file
            xml_files = self._extract_zip_files()

            # Update batch with file count
            batch.write({
                'total_files': len(xml_files),
                'state': 'processing',
                'start_time': fields.Datetime.now(),
            })

            self.write({
                'state': 'processing',
                'total_files': len(xml_files),
            })

            # Process each XML file
            self._process_xml_files(xml_files, batch)

            # Mark batch as done
            batch.action_mark_done()

            # Update wizard state
            self.write({
                'state': 'done',
                'result_message': self._generate_result_html(),
            })

            return self._get_wizard_action()

        except Exception as e:
            _logger.error(f'Import failed: {str(e)}', exc_info=True)
            batch.action_mark_error(str(e))

            self.write({
                'state': 'done',
                'error_details': str(e),
                'result_message': self._generate_error_html(str(e)),
            })

            return self._get_wizard_action()

    def _get_provider_name(self):
        """Get the provider name based on selection."""
        if self.original_provider == 'other' and self.other_provider_name:
            return self.other_provider_name
        elif self.original_provider:
            return dict(self._fields['original_provider'].selection).get(self.original_provider, 'Unknown')
        else:
            return 'Unknown'

    def _extract_zip_files(self):
        """Extract XML files from ZIP."""
        try:
            zip_data = base64.b64decode(self.upload_file)
            zip_buffer = io.BytesIO(zip_data)

            xml_files = []

            with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                # Get all XML files
                all_files = zip_ref.namelist()
                xml_filenames = [f for f in all_files if f.lower().endswith('.xml') and not f.startswith('__MACOSX')]

                if not xml_filenames:
                    raise UserError(_('No XML files found in the ZIP archive'))

                # Read XML content
                for xml_filename in xml_filenames:
                    try:
                        xml_content = zip_ref.read(xml_filename)
                        xml_files.append({
                            'filename': xml_filename,
                            'content': xml_content,
                        })
                    except Exception as e:
                        _logger.warning(f'Could not read file {xml_filename}: {str(e)}')
                        continue

            return xml_files

        except zipfile.BadZipFile:
            raise UserError(_('Invalid ZIP file. Please upload a valid ZIP archive.'))
        except Exception as e:
            raise UserError(_('Error extracting ZIP file: %s') % str(e))

    def _process_xml_files(self, xml_files, batch):
        """Process all XML files with enhanced error handling."""
        parser = self.env['l10n_cr.einvoice.xml.parser']
        error_model = self.env['l10n_cr.einvoice.import.error']

        successful = 0
        failed = 0
        skipped = 0

        for idx, xml_file in enumerate(xml_files, 1):
            invoice_data = None
            clave = None
            consecutive = None

            try:
                # Parse XML
                invoice_data = parser.parse_xml_file(xml_file['content'])
                clave = invoice_data.get('clave')
                consecutive = invoice_data.get('consecutive')

                # Check for duplicates
                if self.skip_duplicates and self._check_duplicate(clave):
                    skipped += 1
                    _logger.info(f"Skipped duplicate: {clave}")
                else:
                    # Create invoice
                    self._create_invoice_from_data(invoice_data, batch, xml_file)
                    successful += 1

            except Exception as e:
                _logger.error(f"Error processing {xml_file['filename']}: {str(e)}", exc_info=True)

                # Categorize the exception
                error_type, error_message, error_context = error_model.categorize_exception(
                    e, xml_file['filename']
                )

                # Extract clave and consecutive if available from invoice_data
                if invoice_data:
                    clave = invoice_data.get('clave', clave)
                    consecutive = invoice_data.get('consecutive', consecutive)

                # Get stack trace for debugging
                stack_trace = traceback.format_exc()

                # Create enhanced error record
                error_model.create_error(
                    batch_id=batch,
                    file_name=xml_file['filename'],
                    error_type=error_type,
                    error_message=error_message,
                    clave=clave,
                    consecutive=consecutive,
                    xml_content=base64.b64encode(xml_file['content']),
                    error_context=error_context,
                    stack_trace=stack_trace,
                )
                failed += 1

            # Update progress every 10 files or on last file
            if idx % 10 == 0 or idx == len(xml_files):
                self.write({
                    'processed_files': idx,
                    'successful_imports': successful,
                    'failed_imports': failed,
                    'skipped_duplicates': skipped,
                })

                batch.write({
                    'processed_files': idx,
                    'successful_imports': successful,
                    'failed_imports': failed,
                    'skipped_duplicates': skipped,
                })

                # Commit every 50 files for better performance
                if idx % 50 == 0:
                    self.env.cr.commit()

    def _check_duplicate(self, clave):
        """Check if invoice with this clave already exists."""
        existing = self.env['account.move'].search([
            ('l10n_cr_original_clave', '=', clave),
        ], limit=1)

        return bool(existing)

    def _create_invoice_from_data(self, invoice_data, batch, xml_file):
        """Create invoice from parsed XML data."""
        # Get or create partner
        partner = self._get_or_create_partner(invoice_data)

        # Determine invoice type
        move_type = self._get_move_type(invoice_data['document_type'])

        # Create invoice
        invoice_vals = {
            'move_type': move_type,
            'partner_id': partner.id if partner else False,
            'invoice_date': invoice_data['date'],
            'currency_id': self._get_currency_id(invoice_data['summary'].get('currency', 'CRC')),
            'company_id': self.env.company.id,

            # Historical import fields
            'l10n_cr_is_historical': True,
            'l10n_cr_import_batch_id': batch.id,
            'l10n_cr_original_xml': invoice_data['original_xml'],
            'l10n_cr_original_provider': batch.original_provider,
            'l10n_cr_original_clave': invoice_data['clave'],

            # Payment fields
            'l10n_cr_payment_method_id': self._get_payment_method(invoice_data['payment_method']),
        }

        # Create invoice
        invoice = self.env['account.move'].create(invoice_vals)

        # Create invoice lines
        self._create_invoice_lines(invoice, invoice_data['line_items'])

        # Validate amounts
        self._validate_invoice_amounts(invoice, invoice_data['summary'])

        _logger.info(f"Created historical invoice: {invoice.name} (clave: {invoice_data['clave']})")

        return invoice

    def _get_or_create_partner(self, invoice_data):
        """Get or create partner from invoice data."""
        receptor = invoice_data.get('receptor')

        # No receptor for anonymous sales (Tiquete Electrónico)
        if not receptor:
            return None

        # Try to find existing partner by VAT
        vat = receptor.get('id_number')
        if vat:
            partner = self.env['res.partner'].search([
                ('vat', '=', vat),
                ('company_id', 'in', [self.env.company.id, False]),
            ], limit=1)

            if partner:
                return partner

        # Auto-create partner if enabled
        if self.auto_create_partners and vat:
            partner_vals = {
                'name': receptor.get('name', 'Unknown'),
                'vat': vat,
                'l10n_latam_identification_type_id': self._get_identification_type(receptor.get('id_type')),
                'email': receptor.get('email'),
                'phone': receptor.get('phone'),
                'company_id': self.env.company.id,
                'customer_rank': 1,
            }

            # Add address if available
            location = receptor.get('location', {})
            if location.get('otras_senas'):
                partner_vals['street'] = location['otras_senas']

            partner = self.env['res.partner'].create(partner_vals)
            _logger.info(f"Created new partner: {partner.name} (VAT: {vat})")

            return partner

        return None

    def _get_identification_type(self, tipo_code):
        """Map Hacienda ID type to Odoo identification type."""
        # Map CR ID types to l10n_latam identification types
        # This is simplified - in production, you'd need proper mapping
        if tipo_code == '01':  # Cédula Física
            return self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False)
        elif tipo_code == '02':  # Cédula Jurídica
            return self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False)
        else:
            return self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False)

    def _get_move_type(self, document_type):
        """Map document type to Odoo move type."""
        if document_type in ['FE', 'TE']:
            return 'out_invoice'
        elif document_type == 'NC':
            return 'out_refund'
        elif document_type == 'ND':
            return 'out_invoice'  # Debit note as invoice
        else:
            return 'out_invoice'

    def _get_currency_id(self, currency_code):
        """Get currency record ID."""
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        return currency.id if currency else self.env.company.currency_id.id

    def _get_payment_method(self, method_code):
        """Get payment method record."""
        if not method_code:
            method_code = '01'  # Default: Efectivo

        payment_method = self.env['l10n_cr.payment.method'].search([
            ('code', '=', method_code)
        ], limit=1)

        return payment_method.id if payment_method else False

    def _create_invoice_lines(self, invoice, line_items):
        """Create invoice lines from parsed line items."""
        if not line_items:
            return

        for line_data in line_items:
            # Get or create product
            product = self._get_or_create_product(line_data)

            # Get tax
            tax_ids = self._get_tax_ids(line_data.get('taxes', []))

            # Calculate discount percentage
            discount_percent = 0.0
            if line_data.get('discount_amount') and line_data.get('amount_total'):
                discount_percent = (line_data['discount_amount'] / line_data['amount_total']) * 100

            # Create line
            line_vals = {
                'move_id': invoice.id,
                'product_id': product.id if product else False,
                'name': line_data.get('description', 'Imported Product'),
                'quantity': line_data.get('quantity', 1.0),
                'price_unit': line_data.get('price_unit', 0.0),
                'discount': discount_percent,
                'tax_ids': [(6, 0, tax_ids)],
            }

            self.env['account.move.line'].create(line_vals)

    def _get_or_create_product(self, line_data):
        """Get or create product from line data."""
        cabys_code = line_data.get('cabys_code')

        # Try to find existing product by Cabys code
        if cabys_code:
            product = self.env['product.product'].search([
                ('l10n_cr_cabys_code', '=', cabys_code),
                ('company_id', 'in', [self.env.company.id, False]),
            ], limit=1)

            if product:
                return product

        # Auto-create product if enabled
        if self.auto_create_products and cabys_code:
            product_vals = {
                'name': line_data.get('description', f'Product {cabys_code}'),
                'l10n_cr_cabys_code': cabys_code,
                'type': 'service',  # Default to service
                'list_price': line_data.get('price_unit', 0.0),
                'company_id': self.env.company.id,
            }

            product = self.env['product.product'].create(product_vals)
            _logger.info(f"Created new product: {product.name} (Cabys: {cabys_code})")

            return product

        return None

    def _get_tax_ids(self, tax_data_list):
        """Map tax data to Odoo tax IDs."""
        tax_ids = []

        for tax_data in tax_data_list:
            tax_rate = tax_data.get('rate', 0.0)

            # Find matching tax by rate
            # In CR, common rates are 13% (IVA), 1%, 2%, 4%, 8%
            tax = self.env['account.tax'].search([
                ('amount', '=', tax_rate),
                ('type_tax_use', '=', 'sale'),
                ('company_id', '=', self.env.company.id),
            ], limit=1)

            if tax:
                tax_ids.append(tax.id)
            else:
                _logger.warning(f"Could not find tax with rate {tax_rate}%")

        return tax_ids

    def _validate_invoice_amounts(self, invoice, summary):
        """Validate that invoice amounts match XML summary."""
        # Compute invoice totals
        invoice._recompute_dynamic_lines()

        # Get expected totals from XML
        expected_total = summary.get('total_invoice', 0.0)
        expected_tax = summary.get('total_tax', 0.0)

        # Compare (allow small rounding differences)
        if abs(invoice.amount_total - expected_total) > 0.50:
            _logger.warning(
                f"Invoice total mismatch: Odoo={invoice.amount_total}, XML={expected_total}"
            )

        if abs(invoice.amount_tax - expected_tax) > 0.50:
            _logger.warning(
                f"Tax total mismatch: Odoo={invoice.amount_tax}, XML={expected_tax}"
            )

    def _generate_result_html(self):
        """Generate HTML summary of import results."""
        html = f"""
        <div class="alert alert-success">
            <h4><i class="fa fa-check-circle"></i> Import Completed Successfully</h4>
            <hr/>
            <table class="table table-sm">
                <tr>
                    <td><strong>Total Files:</strong></td>
                    <td>{self.total_files}</td>
                </tr>
                <tr>
                    <td><strong>Successfully Imported:</strong></td>
                    <td class="text-success"><strong>{self.successful_imports}</strong></td>
                </tr>
                <tr>
                    <td><strong>Skipped (Duplicates):</strong></td>
                    <td class="text-warning">{self.skipped_duplicates}</td>
                </tr>
                <tr>
                    <td><strong>Failed:</strong></td>
                    <td class="text-danger">{self.failed_imports}</td>
                </tr>
            </table>
        </div>
        """

        if self.failed_imports > 0:
            html += f"""
            <div class="alert alert-warning">
                <p><i class="fa fa-exclamation-triangle"></i>
                {self.failed_imports} file(s) failed to import.
                Click "View Errors" to see details and retry options.</p>
            </div>
            """

        return html

    def _generate_error_html(self, error_message):
        """Generate HTML for error display."""
        return f"""
        <div class="alert alert-danger">
            <h4><i class="fa fa-times-circle"></i> Import Failed</h4>
            <hr/>
            <p><strong>Error:</strong> {error_message}</p>
            <p>Please check the file format and try again.</p>
        </div>
        """

    def _get_wizard_action(self):
        """Return action to keep wizard open."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_cr.einvoice.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_batch(self):
        """Open the import batch record."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Batch'),
            'res_model': 'l10n_cr.einvoice.import.batch',
            'res_id': self.batch_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoices(self):
        """View imported invoices."""
        self.ensure_one()

        if not self.batch_id:
            return

        return self.batch_id.action_view_invoices()

    def action_view_errors(self):
        """View import errors."""
        self.ensure_one()

        if not self.batch_id:
            return

        return self.batch_id.action_view_errors()

    def action_close(self):
        """Close the wizard."""
        return {'type': 'ir.actions.act_window_close'}
