# -*- coding: utf-8 -*-
import base64
import logging
from datetime import datetime
from lxml import etree

import psycopg2

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class EInvoiceDocument(models.Model):
    _name = 'l10n_cr.einvoice.document'
    _description = 'Costa Rica Electronic Invoice Document'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ===== SQL CONSTRAINTS (Odoo 19 format) =====
    _clave_unique = models.UniqueIndex(
        '(clave)',
        'La clave de Hacienda debe ser única para cada documento.',
    )
    _source_document_check = models.Constraint(
        "CHECK ((move_id IS NOT NULL OR pos_order_id IS NOT NULL) AND NOT (move_id IS NOT NULL AND pos_order_id IS NOT NULL))",
        'El documento electrónico debe estar vinculado a una Factura O a una Orden de POS (no ambos).',
    )

    # Basic Information
    name = fields.Char(
        string='Document Number',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New'),
    )

    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=False,  # Optional to support POS orders without immediate invoice
        ondelete='cascade',
        index=True,
        tracking=True,
    )

    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        ondelete='cascade',
        index=True,
        copy=False,
        help='Link to POS order for e-invoices generated from Point of Sale',
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=False,
        help='The partner to bill (Receptor in XML). May be different from POS order partner if using corporate billing.',
    )

    # Document Type
    document_type = fields.Selection([
        ('FE', 'Factura Electrónica'),
        ('TE', 'Tiquete Electrónico'),
        ('NC', 'Nota de Crédito Electrónica'),
        ('ND', 'Nota de Débito Electrónica'),
    ], string='Document Type', required=True, default='FE', tracking=True)

    # Hacienda Key (50-digit unique identifier)
    clave = fields.Char(
        string='Hacienda Key (Clave)',
        size=50,
        copy=False,
        readonly=True,
        index=True,
        tracking=True,
        help='50-digit unique electronic document key assigned by Hacienda',
    )

    # XML Content
    xml_content = fields.Text(
        string='Generated XML',
        readonly=True,
        help='Generated XML content before signing',
    )

    signed_xml = fields.Text(
        string='Signed XML',
        readonly=True,
        help='Digitally signed XML content ready for submission',
    )

    xml_attachment_id = fields.Many2one(
        'ir.attachment',
        string='XML Attachment',
        readonly=True,
    )

    # Status and Responses
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'XML Generated'),
        ('generation_error', 'Generation Failed'),
        ('signed', 'Digitally Signed'),
        ('signing_error', 'Signing Failed'),
        ('submitted', 'Submitted to Hacienda'),
        ('submission_error', 'Submission Failed'),
        ('accepted', 'Accepted by Hacienda'),
        ('rejected', 'Rejected by Hacienda'),
        ('error', 'Error'),  # Keep for backward compatibility
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    hacienda_response = fields.Text(
        string='Hacienda Response',
        readonly=True,
        help='Complete response from Hacienda API',
    )

    hacienda_message = fields.Text(
        string='Response Message',
        readonly=True,
        tracking=True,
    )

    hacienda_submission_date = fields.Datetime(
        string='Submission Date',
        readonly=True,
        tracking=True,
    )

    hacienda_acceptance_date = fields.Datetime(
        string='Acceptance Date',
        readonly=True,
        tracking=True,
    )

    # Error Handling
    error_message = fields.Text(
        string='Error Details',
        readonly=True,
    )

    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        readonly=True,
    )

    retry_button_visible = fields.Boolean(
        compute='_compute_retry_button_visible',
        string='Show Retry Button',
        help='Indicates if the retry button should be visible based on error state',
    )

    # Validation Override (for exceptional cases)
    validation_override = fields.Boolean(
        string='Validation Override',
        default=False,
        tracking=True,
        help='If True, validation errors are logged but do not block document processing',
    )

    validation_override_reason = fields.Text(
        string='Override Reason',
        tracking=True,
        help='Required justification for overriding validation rules (minimum 20 characters)',
    )

    validation_override_user_id = fields.Many2one(
        'res.users',
        string='Override Approved By',
        readonly=True,
        tracking=True,
        help='User who approved the validation override',
    )

    validation_override_date = fields.Datetime(
        string='Override Date',
        readonly=True,
        tracking=True,
        help='Timestamp when validation was overridden',
    )

    validation_errors = fields.Text(
        string='Validation Errors',
        readonly=True,
        help='List of validation errors that were overridden',
    )

    # PDF and Email
    pdf_attachment_id = fields.Many2one(
        'ir.attachment',
        string='PDF with QR',
        readonly=True,
    )

    email_sent = fields.Boolean(
        string='Email Sent',
        default=False,
        tracking=True,
    )

    email_sent_date = fields.Datetime(
        string='Email Sent Date',
        readonly=True,
    )

    # Computed Fields
    amount_total = fields.Monetary(
        string='Total Amount',
        compute='_compute_amount_total',
        store=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_currency_id',
        store=True,
    )

    invoice_date = fields.Date(
        string='Invoice Date',
        compute='_compute_invoice_date',
        store=True,
    )

    @api.depends('move_id.amount_total', 'pos_order_id.amount_total')
    def _compute_amount_total(self):
        """Compute amount from either invoice or POS order."""
        for doc in self:
            if doc.move_id:
                doc.amount_total = doc.move_id.amount_total
            elif doc.pos_order_id:
                doc.amount_total = doc.pos_order_id.amount_total
            else:
                doc.amount_total = 0.0

    @api.depends('move_id.currency_id', 'pos_order_id.currency_id')
    def _compute_currency_id(self):
        """Compute currency from either invoice or POS order."""
        for doc in self:
            if doc.move_id:
                doc.currency_id = doc.move_id.currency_id
            elif doc.pos_order_id:
                doc.currency_id = doc.pos_order_id.currency_id
            else:
                doc.currency_id = doc.company_id.currency_id

    @api.depends('move_id.invoice_date', 'pos_order_id.date_order')
    def _compute_invoice_date(self):
        """Compute invoice date from either invoice or POS order."""
        for doc in self:
            if doc.move_id:
                doc.invoice_date = doc.move_id.invoice_date
            elif doc.pos_order_id:
                doc.invoice_date = doc.pos_order_id.date_order.date() if doc.pos_order_id.date_order else fields.Date.today()
            else:
                doc.invoice_date = fields.Date.today()

    @api.depends('state')
    def _compute_retry_button_visible(self):
        """Determine if the retry button should be visible based on error state."""
        for doc in self:
            doc.retry_button_visible = doc.state in [
                'generation_error',
                'signing_error',
                'submission_error',
            ]

    @api.constrains('move_id', 'pos_order_id')
    def _check_source_document(self):
        """Ensure at least one source document exists."""
        for doc in self:
            if not doc.move_id and not doc.pos_order_id:
                raise ValidationError(_('E-invoice document must be linked to either an Invoice or a POS Order.'))

    @api.constrains('document_type', 'partner_id', 'invoice_date')
    def _check_mandatory_fields(self):
        """
        Backend validation constraint for Factura Electrónica mandatory fields.

        This is Layer 2 of the validation architecture - enforces hard constraints
        at the database/ORM level to prevent invalid data regardless of UI bypass.

        Integrates with l10n_cr.validation.rule model to fetch active validation rules
        and enforce them during record creation/modification.

        Validation bypass is supported via context flag for special cases.

        Raises:
            ValidationError: If any mandatory field validation fails for FE documents
        """
        # Check if validation should be bypassed (for imports, migrations, etc.)
        if self.env.context.get('bypass_einvoice_validation', False):
            _logger.info('E-invoice validation bypassed via context flag')
            return

        for doc in self:
            # Check if validation override is active
            if doc.validation_override:
                _logger.warning(
                    f'Validation override active for document {doc.name} '
                    f'by user {doc.validation_override_user_id.name} '
                    f'on {doc.validation_override_date}. '
                    f'Reason: {doc.validation_override_reason}'
                )
                continue

            # Skip validation for non-FE document types
            # TE (Tiquete) has no mandatory customer fields
            if doc.document_type != 'FE':
                _logger.debug(f'Skipping validation for document {doc.name} - type {doc.document_type}')
                continue

            # Call validation rule engine
            try:
                is_valid, error_messages = self.env['l10n_cr.validation.rule'].validate_all_rules(doc)

                # If validation rule engine found errors, they would have been raised
                # This check is for non-blocking rules or custom logging
                if not is_valid and error_messages:
                    _logger.warning(
                        f'Validation warnings for document {doc.name}: '
                        f'{"; ".join(error_messages)}'
                    )

            except ValidationError:
                # Re-raise validation errors from rule engine
                raise
            except (AttributeError, KeyError, TypeError) as e:
                # Log common data issues but don't block document creation
                _logger.error(
                    f'Unexpected error during validation for document {doc.name}: {str(e)}'
                )

            # Fallback validation if rule engine is not available or misconfigured
            # This ensures critical validations are always enforced
            self._check_fe_mandatory_fields_fallback(doc)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence number."""
        # Odoo 19: create() now receives a list of dictionaries
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_cr.einvoice') or _('New')
        return super(EInvoiceDocument, self).create(vals_list)

    def action_generate_xml(self):
        """
        Generate the XML content for the electronic invoice.

        This method performs Layer 3 validation (pre-generation) before
        attempting XML generation. For Factura Electrónica documents,
        it validates all mandatory fields are present unless override is active.
        """
        self.ensure_one()

        # Acquire database lock to prevent concurrent modifications
        try:
            self.env.cr.execute(
                'SELECT id FROM l10n_cr_einvoice_document WHERE id = %s FOR UPDATE NOWAIT',
                (self.id,)
            )
        except psycopg2.OperationalError:
            raise UserError(_('This document is currently being processed by another user. Please try again in a moment.'))

        if self.state not in ['draft', 'error', 'generation_error']:
            raise UserError(_('Can only generate XML for draft or error documents.'))

        # Pre-generation validation for Factura Electrónica
        if self.document_type == 'FE' and not self.validation_override:
            is_valid, errors, can_downgrade = self.validate_factura_requirements()

            if not is_valid:
                error_msg = _(
                    'No se puede generar Factura Electrónica:\n'
                    '═══════════════════════════════════════\n\n'
                ) + '\n'.join(f'• {e}' for e in errors)

                if can_downgrade:
                    error_msg += '\n\n' + _(
                        'SUGERENCIA: Puede generar un Tiquete Electrónico (TE) en su lugar,\n'
                        'que no requiere datos del cliente.\n\n'
                        'Para cambiar el tipo de documento, edite el registro y seleccione "TE".'
                    )

                # Log validation failure
                _logger.warning(
                    f'Pre-generation validation failed for FE document {self.name or "NEW"}: '
                    f'{len(errors)} error(s)'
                )

                # Store validation errors
                self.sudo().write({
                    'state': 'generation_error',
                    'error_message': error_msg,
                    'validation_errors': '\n'.join(errors),
                })

                raise ValidationError(error_msg)

            _logger.info(
                f'Pre-generation validation passed for FE document {self.name or "NEW"}'
            )
        elif self.document_type == 'FE' and self.validation_override:
            _logger.warning(
                f'Pre-generation validation SKIPPED for FE document {self.name or "NEW"} '
                f'due to validation override by {self.validation_override_user_id.name}'
            )

        try:
            # Generate the clave (50-digit key) and consecutive number
            clave, consecutive = self._generate_clave()
            self.clave = clave
            self.name = consecutive

            # Generate XML content
            xml_content = self._build_xml_content(clave)

            # Add warning comment if validation override is active
            if self.validation_override:
                override_comment = (
                    f'<!-- VALIDATION OVERRIDE ACTIVE -->\n'
                    f'<!-- Approved by: {self.validation_override_user_id.name} -->\n'
                    f'<!-- Date: {self.validation_override_date} -->\n'
                    f'<!-- Reason: {self.validation_override_reason} -->\n'
                )
                # Insert comment after XML declaration
                if '?>' in xml_content:
                    parts = xml_content.split('?>', 1)
                    xml_content = parts[0] + '?>\n' + override_comment + parts[1]

            # Validate XML against XSD
            self._validate_xml(xml_content)

            # Update document
            self.write({
                'clave': clave,
                'xml_content': xml_content,
                'state': 'generated',
                'error_message': False,
            })

            _logger.info(f'Generated XML for document {self.name}, clave: {clave}')

        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error generating XML for {self.name}: {error_msg}')
            # Persist error state in a separate cursor so it survives the
            # transaction rollback triggered by UserError.
            self._write_error_state_safe('generation_error', error_msg)
            raise UserError(_('Error generating XML: %s') % error_msg)

    def action_sign_xml(self):
        """Digitally sign the XML content."""
        self.ensure_one()

        # Acquire database lock to prevent concurrent modifications
        try:
            self.env.cr.execute(
                'SELECT id FROM l10n_cr_einvoice_document WHERE id = %s FOR UPDATE NOWAIT',
                (self.id,)
            )
        except psycopg2.OperationalError:
            raise UserError(_('This document is currently being processed by another user. Please try again in a moment.'))

        if self.state not in ['generated', 'signing_error']:
            raise UserError(_('Can only sign generated XML documents.'))

        if not self.xml_content:
            raise UserError(_('No XML content to sign.'))

        try:
            # Verify certificate is configured
            certificate = self.company_id.l10n_cr_active_certificate
            if not certificate:
                raise UserError(_('Company digital certificate must be configured.'))

            # For .p12 files, private key is embedded; for PEM, it must be separate
            private_key = self.company_id.l10n_cr_active_private_key
            filename = (self.company_id.l10n_cr_active_certificate_filename or '').lower()
            if not filename.endswith(('.p12', '.pfx')) and not private_key:
                raise UserError(_('Private key file is required for PEM certificates.'))

            # Sign the XML (certificate manager handles .p12 extraction)
            signed_xml = self._sign_xml_content(self.xml_content, certificate, private_key)

            # Create XML attachment
            attachment = self._create_xml_attachment(signed_xml)

            # Update document
            self.write({
                'signed_xml': signed_xml,
                'xml_attachment_id': attachment.id,
                'state': 'signed',
                'error_message': False,
            })

            _logger.info(f'Signed XML for document {self.name}')

        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error signing XML for {self.name}: {error_msg}')
            self._write_error_state_safe('signing_error', error_msg)
            raise UserError(_('Error signing XML: %s') % error_msg)

    def _validate_before_submission(self):
        """
        Validate all required data before submission to Hacienda.

        This comprehensive validation ensures all critical fields are properly
        configured before attempting to submit to the Hacienda API, preventing
        submission failures and improving user experience.

        Raises:
            ValidationError: If any validation check fails, with a detailed
                           message listing all issues found.
        """
        self.ensure_one()
        errors = []

        # Company validation
        if not self.company_id.l10n_cr_active_username:
            errors.append(_('Hacienda API username is missing - configure in Company settings'))

        if not self.company_id.l10n_cr_active_password:
            errors.append(_('Hacienda API password is missing - configure in Company settings'))

        if not self.company_id.vat:
            errors.append(_('Company Tax ID (VAT/Cédula Jurídica) is required'))

        # Digital certificate validation
        if not self.company_id.l10n_cr_active_certificate:
            errors.append(_('Digital certificate not configured - upload in Company settings'))

        # For PEM certs, private key file is required; for .p12/.pfx it's embedded
        cert_filename = (self.company_id.l10n_cr_active_certificate_filename or '').lower()
        if not cert_filename.endswith(('.p12', '.pfx')) and not self.company_id.l10n_cr_active_private_key:
            errors.append(_('Private key not configured - upload in Company settings'))

        # Partner/Customer validation
        if not self.partner_id:
            errors.append(_('Customer is required for e-invoice'))
        elif self.document_type == 'FE':
            if not self.partner_id.vat:
                errors.append(
                    _('Customer Tax ID (VAT/Cédula) is required for customer "%s"') %
                    self.partner_id.name
                )

        # Document validation
        if not self.clave:
            errors.append(_('Hacienda key (clave) is missing - generate XML first'))

        if not self.signed_xml:
            errors.append(_('Signed XML is missing - sign the document first'))

        # Currency validation
        if not self.currency_id:
            errors.append(_('Currency is required'))

        # Amount validation
        if self.amount_total <= 0:
            errors.append(_('Invoice total must be greater than zero'))

        # Source document validation
        if not self.move_id and not self.pos_order_id:
            errors.append(_('E-invoice must be linked to either an Invoice or POS Order'))

        # Line items validation
        if self.move_id:
            if not self.move_id.invoice_line_ids:
                errors.append(_('Invoice has no line items'))
        elif self.pos_order_id:
            if not self.pos_order_id.lines:
                errors.append(_('POS order has no line items'))

        # Emisor location validation (required for clave generation)
        if not self.company_id.l10n_cr_emisor_location:
            errors.append(_('Emisor location code is missing - configure in Company settings'))

        # Environment configuration check
        if not self.company_id.l10n_cr_hacienda_env:
            errors.append(_('Hacienda environment (sandbox/production) not configured'))

        # If there are errors, raise ValidationError with all issues
        if errors:
            error_message = _('Cannot submit to Hacienda due to the following issues:\n\n') + '\n'.join(
                '• %s' % error for error in errors
            )
            raise ValidationError(error_message)

        _logger.info(f'Pre-flight validation passed for document {self.name}')
        return True

    def action_submit_to_hacienda(self):
        """Submit the signed XML to Hacienda API."""
        self.ensure_one()

        # Run comprehensive pre-flight validation
        self._validate_before_submission()

        # Acquire database lock to prevent concurrent submissions (double-click protection)
        try:
            self.env.cr.execute(
                'SELECT id FROM l10n_cr_einvoice_document WHERE id = %s FOR UPDATE NOWAIT',
                (self.id,)
            )
        except psycopg2.OperationalError:
            raise UserError(_('This document is currently being processed by another user. Please try again in a moment.'))

        if self.state not in ['signed', 'submission_error']:
            raise UserError(_('Can only submit signed documents.'))

        if not self.signed_xml:
            raise UserError(_('No signed XML to submit.'))

        try:
            # Get API client (use document's company for multi-company safety)
            api_client = self.env['l10n_cr.hacienda.api'].with_company(self.company_id)

            # Submit to Hacienda
            response = api_client.submit_invoice(
                clave=self.clave,
                xml_content=self.signed_xml,
                sender_id=self.company_id.vat,
                receiver_id=self.partner_id.vat or '',
            )

            # Update document based on response
            self._process_hacienda_response(response)

            _logger.info(f'Submitted document {self.name} to Hacienda')

        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error submitting {self.name} to Hacienda: {error_msg}')
            self._write_error_state_safe(
                'submission_error', error_msg,
                extra_vals={'retry_count': self.retry_count + 1},
            )
            raise UserError(_('Error submitting to Hacienda: %s') % error_msg)

    def action_check_status(self):
        """Check the status of a submitted document with Hacienda."""
        self.ensure_one()

        # Acquire database lock to prevent concurrent status checks
        try:
            self.env.cr.execute(
                'SELECT id FROM l10n_cr_einvoice_document WHERE id = %s FOR UPDATE NOWAIT',
                (self.id,)
            )
        except psycopg2.OperationalError:
            raise UserError(_('This document is currently being processed by another user. Please try again in a moment.'))

        if self.state not in ['submitted', 'submission_error', 'error']:
            raise UserError(_('Can only check status for submitted documents.'))

        try:
            api_client = self.env['l10n_cr.hacienda.api'].with_company(self.company_id)

            response = api_client.check_status(self.clave)

            self._process_hacienda_response(response)

        except Exception as e:
            _logger.error(f'Error checking status for {self.name}: {str(e)}')
            raise UserError(_('Error checking status: %s') % str(e))

    def action_retry(self):
        """
        Retry failed operation based on current error state.

        This method intelligently retries the failed step in the e-invoice workflow.
        It determines which action to retry based on the current error state.

        Returns:
            dict or None: Action dictionary if redirect needed, None otherwise
        """
        self.ensure_one()

        _logger.info(f'Retrying failed operation for document {self.name}, current state: {self.state}')

        if self.state == 'generation_error':
            return self.action_generate_xml()
        elif self.state == 'signing_error':
            return self.action_sign_xml()
        elif self.state == 'submission_error':
            return self.action_submit_to_hacienda()
        else:
            raise UserError(_('No failed operation to retry. Current state: %s') % self.state)

    def action_override_validation(self):
        """
        Open validation override wizard for exceptional cases.

        This action opens a wizard that allows authorized users (account managers
        or POS managers) to override validation errors with proper justification
        and audit trail.

        Returns:
            dict: Action to open the validation override wizard
        """
        self.ensure_one()

        # Check if there are validation errors to override
        try:
            is_valid, error_messages = self.env['l10n_cr.validation.rule'].validate_all_rules(self)
            if is_valid:
                raise UserError(_('No validation errors found. Override is not needed.'))
        except ValidationError as e:
            error_messages = [str(e)]

        # Store validation errors for the wizard
        self.write({'validation_errors': '\n'.join(error_messages)})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Override Validation'),
            'res_model': 'l10n_cr.validation.override.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_id': self.id,
                'default_validation_errors': '\n'.join(error_messages),
            },
        }

    def action_download_xml(self):
        """Download the XML attachment."""
        self.ensure_one()

        if not self.xml_attachment_id:
            raise UserError(_('No XML attachment available.'))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.xml_attachment_id.id}?download=true',
            'target': 'new',
        }

    def action_view_hacienda_response(self):
        """View Hacienda response in a dialog."""
        self.ensure_one()

        if not self.hacienda_response:
            raise UserError(_('No Hacienda response available.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Hacienda Response'),
            'res_model': 'l10n_cr.einvoice.document',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'views': [(False, 'form')],
        }

    def action_resend_email(self):
        """Resend email to customer."""
        self.ensure_one()

        if self.state != 'accepted':
            raise UserError(_('Can only send email for accepted documents.'))

        # Reset sent flag so action_send_email() works
        self.email_sent = False
        return self.action_send_email()

    def action_generate_pdf(self):
        """Generate PDF report with QR code."""
        self.ensure_one()

        if not self.clave:
            raise UserError(_('Cannot generate PDF: Document has no clave.'))

        if not self.xml_content:
            raise UserError(_('Cannot generate PDF: No XML content available.'))

        try:
            # Get the PDF report
            report = self.env.ref('l10n_cr_einvoice.action_report_einvoice')

            # Generate the PDF
            pdf_content, _ = report._render_qweb_pdf([self.id])

            # Create PDF attachment
            filename = f'{self.clave}.pdf'
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })

            # Update document
            self.write({
                'pdf_attachment_id': attachment.id,
            })

            _logger.info(f'Generated PDF for document {self.name}')

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('PDF generated successfully'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error generating PDF for {self.name}: {error_msg}')
            raise UserError(_('Error generating PDF: %s') % error_msg)

    def action_download_pdf(self):
        """Download PDF report."""
        self.ensure_one()

        if not self.pdf_attachment_id:
            raise UserError(_('No PDF attachment available. Generate PDF first.'))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.pdf_attachment_id.id}?download=true',
            'target': 'new',
        }

    def action_send_email(self):
        """Send email to customer with PDF attachment."""
        self.ensure_one()

        if self.state != 'accepted':
            raise UserError(_('Can only send email for accepted documents.'))

        if not self.partner_id.email:
            raise UserError(_(
                'Cannot send email: Customer %s has no email address.'
            ) % self.partner_id.name)

        try:
            # Generate PDF if not exists
            if not self.pdf_attachment_id:
                self.action_generate_pdf()

            # Get email template based on document type
            if self.document_type == 'TE':
                template = self.env.ref('l10n_cr_einvoice.email_template_eticket', raise_if_not_found=False)
            else:
                template = self.env.ref('l10n_cr_einvoice.email_template_einvoice', raise_if_not_found=False)

            if not template:
                raise UserError(_('Email template not found.'))

            # Attach PDF + signed XML (Chile pattern)
            attachment_ids = [(4, self.pdf_attachment_id.id)]
            if self.xml_attachment_id:
                attachment_ids.append((4, self.xml_attachment_id.id))

            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'attachment_ids': attachment_ids,
                }
            )

            # Update document
            self.write({
                'email_sent': True,
                'email_sent_date': fields.Datetime.now(),
            })

            _logger.info(f'Sent email for document {self.name} to {self.partner_id.email}')

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Email sent to %s') % self.partner_id.email,
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error sending email for {self.name}: {error_msg}')
            raise UserError(_('Error sending email: %s') % error_msg)

    def _auto_send_email_on_acceptance(self):
        """
        Automatically send email when document is accepted by Hacienda.

        Called internally after state changes to 'accepted'.
        Respects company configuration for auto-send.
        """
        self.ensure_one()

        # Check if auto-send is enabled
        if not self.company_id.l10n_cr_auto_send_email:
            _logger.debug(f'Auto-send email disabled for company {self.company_id.name}')
            return

        # Check if already sent
        if self.email_sent:
            _logger.debug(f'Email already sent for document {self.name}')
            return

        # Check if customer has email
        if not self.partner_id.email:
            _logger.warning(
                f'Cannot auto-send email for {self.name}: '
                f'Customer {self.partner_id.name} has no email'
            )
            return

        try:
            # Send email
            self.action_send_email()
            _logger.info(f'Auto-sent email for document {self.name}')

        except Exception as e:
            # Don't fail the acceptance if email fails
            _logger.error(f'Failed to auto-send email for {self.name}: {str(e)}')

    def _get_qr_code_image(self):
        """
        Get QR code image for PDF report.

        Returns:
            str: Base64 encoded PNG image
        """
        self.ensure_one()

        if not self.clave:
            return False

        try:
            qr_generator = self.env['l10n_cr.qr.generator']
            qr_code = qr_generator.generate_qr_code(self.clave)
            return qr_code

        except Exception as e:
            _logger.error(f'Error generating QR code for {self.name}: {str(e)}')
            return False

    def _generate_clave(self):
        """
        Generate the 50-digit Hacienda key (clave).

        Format per resolution 48-2016, Article 5 (50 digits total):
        CCC DD MM YY CCCCCCCCCCCC CCCCCCCCCCCCCCCCCCCC S CCCCCCCC
        506 day mo yr cedula(12)   consecutive(20)      sit security
         3   2  2  2    12              20               1    8    = 50
        """
        import random

        company = self.company_id

        # Country code (3 digits)
        country = '506'

        # Date DDMMYY (6 digits, 2-digit year)
        if self.move_id and self.move_id.invoice_date:
            invoice_date = self.move_id.invoice_date
        elif self.pos_order_id and self.pos_order_id.date_order:
            invoice_date = self.pos_order_id.date_order.date()
        else:
            invoice_date = fields.Date.today()
        date_str = invoice_date.strftime('%d%m%y')

        # Cedula juridica (12 digits, zero-padded)
        raw_vat = (company.vat or '').replace('-', '').replace(' ', '')
        if not raw_vat or not raw_vat.isdigit():
            raise ValidationError(
                _('Company VAT (cédula) is missing or invalid: "%s". '
                  'Configure a valid numeric cédula in Company settings before generating e-invoices.')
                % (company.vat or '')
            )
        cedula = raw_vat.zfill(12)[:12]

        # Consecutive number (20 digits)
        # Format per Hacienda v4.4 Article 4: SSS + TTTTT + DD + NNNNNNNNNN
        # SSS = Sucursal (3 digits), TTTTT = Terminal (5 digits),
        # DD = DocType (2 digits), NNNNNNNNNN = Sequence (10 digits)
        doc_type_codes = {
            'FE': '01',
            'ND': '02',
            'NC': '03',
            'TE': '04',
        }
        doc_type = doc_type_codes.get(self.document_type, '01')

        # Sucursal from company (3 digits), Terminal from POS config or company (5 digits)
        sucursal = (company.l10n_cr_sucursal or '001').zfill(3)[:3]
        terminal = '00001'
        if self.pos_order_id and self.pos_order_id.config_id:
            terminal = (self.pos_order_id.config_id.l10n_cr_terminal_id or '00001').zfill(5)[:5]
        elif company.l10n_cr_terminal:
            terminal = company.l10n_cr_terminal.zfill(5)[:5]
        consecutive = sucursal + terminal + doc_type + str(self.id).zfill(10)  # 3+5+2+10 = 20

        # Situación del comprobante (1 digit): 1=Normal, 2=Contingencia, 3=Sin internet
        situacion = '1'

        # Security code (8 random digits)
        security_code = str(random.randint(10000000, 99999999))

        # Build clave (50 digits)
        clave = country + date_str + cedula + consecutive + situacion + security_code

        if len(clave) != 50:
            raise ValidationError(_('Invalid clave length: %s (expected 50)') % len(clave))

        return clave, consecutive

    def _calculate_check_digit(self, clave):
        """Calculate the verification digit using module 10."""
        total = 0
        for i, digit in enumerate(reversed(clave)):
            n = int(digit)
            if i % 2 == 0:
                n = n * 2
                if n > 9:
                    n = n - 9
            total += n

        check = (10 - (total % 10)) % 10
        return str(check)

    def _build_xml_content(self, clave):
        """Build the v4.4 XML content structure."""
        self.ensure_one()

        # Use the XML generator
        xml_generator = self.env['l10n_cr.xml.generator']
        xml_content = xml_generator.generate_invoice_xml(self)

        return xml_content

    def _validate_xml(self, xml_content):
        """Validate XML against XSD schema."""
        self.ensure_one()

        # Use XSD validator
        validator = self.env['l10n_cr.xsd.validator']
        is_valid, error_message = validator.validate_xml(xml_content, self.document_type)

        if not is_valid:
            raise ValidationError(_('XML validation failed:\n%s') % error_message)

        _logger.info(f'XML validation passed for document {self.name}')

    def _sign_xml_content(self, xml_content, certificate, private_key):
        """
        Digitally sign the XML content using X.509 certificate.

        Args:
            xml_content (str): XML content to sign
            certificate: Not used (kept for API compatibility)
            private_key: Not used (kept for API compatibility)

        Returns:
            str: Signed XML with embedded signature
        """
        # Load certificate from company using certificate manager
        cert_mgr = self.env['l10n_cr.certificate.manager']
        certificate_obj, private_key_obj = cert_mgr.load_certificate_from_company(
            self.company_id
        )

        # Sign XML using XML signer
        xml_signer = self.env['l10n_cr.xml.signer']
        signed_xml = xml_signer.sign_xml(xml_content, certificate_obj, private_key_obj)

        _logger.info(f'Successfully signed XML for document {self.name}')
        return signed_xml

    def _create_xml_attachment(self, xml_content):
        """Create an attachment with the XML content."""
        self.ensure_one()

        filename = f'{self.clave}.xml'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(xml_content.encode('utf-8')),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/xml',
        })

        return attachment

    def _parse_mensaje_hacienda_xml(self, xml_content):
        """Parse MensajeHacienda XML and extract key fields.

        The Hacienda API returns a base64-encoded MensajeHacienda XML in the
        ``respuesta-xml`` field. This method decodes and extracts the human-readable
        fields such as DetalleMensaje (rejection reason), Mensaje, etc.

        Args:
            xml_content: Base64 string or raw bytes/string of the MensajeHacienda XML.

        Returns:
            dict: Extracted fields (DetalleMensaje, Mensaje, EstadoMensaje, etc.)
                  Empty dict if parsing fails.
        """
        try:
            # Decode base64 if needed
            if isinstance(xml_content, str):
                try:
                    xml_bytes = base64.b64decode(xml_content)
                except Exception:
                    xml_bytes = xml_content.encode('utf-8')
            else:
                xml_bytes = xml_content

            root = etree.fromstring(xml_bytes)

            # MensajeHacienda namespace for v4.4
            ns = {'mh': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/mensajeHacienda'}

            result = {}
            fields_to_extract = [
                'DetalleMensaje', 'Mensaje', 'EstadoMensaje',
                'TotalFactura', 'MontoTotalImpuesto', 'Clave',
            ]

            # Try with namespace first, then without
            for use_ns in [True, False]:
                for field_name in fields_to_extract:
                    if use_ns:
                        elem = root.find(f'mh:{field_name}', ns)
                    else:
                        elem = root.find(field_name)
                    if elem is not None and elem.text:
                        result[field_name] = elem.text

                if result:
                    break

            return result
        except Exception as e:
            _logger.warning("Failed to parse MensajeHacienda XML: %s", str(e))
            return {}

    def _write_error_state_safe(self, state, error_msg, extra_vals=None):
        """Write error state using a separate DB cursor so it survives rollback.

        When a UserError is raised after writing error state, Odoo rolls back
        the entire transaction — erasing the error state we just wrote. This
        method uses a fresh cursor to persist the error state independently,
        so the document shows the correct error even after rollback.
        """
        vals = {'state': state, 'error_message': error_msg}
        if extra_vals:
            vals.update(extra_vals)
        try:
            registry = self.env.registry
            with registry.cursor() as new_cr:
                new_cr.execute(
                    """UPDATE l10n_cr_einvoice_document
                       SET state = %s, error_message = %s, write_date = NOW()
                       WHERE id = %s""",
                    (state, error_msg, self.id),
                )
                if extra_vals and 'retry_count' in extra_vals:
                    new_cr.execute(
                        """UPDATE l10n_cr_einvoice_document
                           SET retry_count = %s WHERE id = %s""",
                        (extra_vals['retry_count'], self.id),
                    )
        except Exception:
            _logger.warning(
                'Failed to persist error state for %s via separate cursor',
                self.name, exc_info=True,
            )

    def _process_hacienda_response(self, response):
        """
        Process the response from Hacienda API.

        Args:
            response (dict): Response from Hacienda API with structure:
                - ind-estado: Document status
                - respuesta-xml: Response message (base64)
                - respuesta-xml-decoded: Decoded message (if available)
                - error_details: Error information (if rejected)
        """
        self.ensure_one()

        status = response.get('ind-estado', '').lower()

        # Use decoded message if available, otherwise use base64
        message = response.get('respuesta-xml-decoded') or response.get('respuesta-xml', '')

        # Parse the MensajeHacienda XML to extract human-readable fields
        parsed_xml = {}
        respuesta_xml = response.get('respuesta-xml')
        if respuesta_xml:
            parsed_xml = self._parse_mensaje_hacienda_xml(respuesta_xml)
            if parsed_xml:
                _logger.info(
                    'Parsed MensajeHacienda for %s: EstadoMensaje=%s, DetalleMensaje=%s',
                    self.name,
                    parsed_xml.get('EstadoMensaje', 'N/A'),
                    (parsed_xml.get('DetalleMensaje', 'N/A'))[:200],
                )

        # Use DetalleMensaje as the human-readable message when available
        detalle_mensaje = parsed_xml.get('DetalleMensaje', '')
        if detalle_mensaje:
            message = detalle_mensaje

        # Extract error details if present
        error_info = response.get('error_details', '')

        vals = {
            'hacienda_response': str(response),
            'hacienda_message': message or '',
            'hacienda_submission_date': self.hacienda_submission_date or fields.Datetime.now(),
        }

        if status == 'aceptado':
            vals.update({
                'state': 'accepted',
                'hacienda_acceptance_date': fields.Datetime.now(),
                'error_message': False,  # Clear any previous errors
            })
            _logger.info(f'Document {self.name} accepted by Hacienda')

            # Update document first
            self.write(vals)

            # Auto-send email if configured
            self._auto_send_email_on_acceptance()

            # Return early to avoid duplicate write
            return

        elif status == 'rechazado':
            # Build descriptive rejection message
            rejection_detail = detalle_mensaje or error_info or message
            rejection_msg = _('Rejected by Hacienda')
            if rejection_detail:
                rejection_msg = _('Rejected by Hacienda: %s') % rejection_detail

            vals.update({
                'state': 'rejected',
                'error_message': rejection_msg,
            })
            _logger.warning(
                'Document %s rejected by Hacienda: %s',
                self.name, rejection_detail or 'No detail provided'
            )

        elif status in ['procesando', 'recibido']:
            vals.update({
                'state': 'submitted',
            })
            _logger.info(f'Document {self.name} submitted, status: {status}')

        elif status == 'error':
            # Explicit error status from Hacienda
            error_detail = detalle_mensaje or error_info or message
            vals.update({
                'state': 'error',
                'error_message': _('Hacienda returned error: %s') % (error_detail or _('No details provided')),
            })
            _logger.error(
                'Document %s received error status from Hacienda: %s',
                self.name, error_detail or 'No details'
            )

        else:
            # Unknown status
            error_detail = detalle_mensaje or error_info or message
            vals.update({
                'state': 'error',
                'error_message': _(
                    'Unknown Hacienda status: "%(status)s". %(detail)s'
                ) % {'status': status, 'detail': error_detail or ''},
            })
            _logger.error(
                'Document %s unknown status from Hacienda: "%s". Detail: %s',
                self.name, status, error_detail or 'None'
            )

        self.write(vals)

    # ===== VALIDATION METHODS =====

    def _check_fe_mandatory_fields_fallback(self, doc):
        """
        Fallback validation for FE mandatory fields.

        This method provides a safety net if the validation rule engine is not
        configured or fails. It enforces the absolute minimum requirements for
        Factura Electrónica documents per Hacienda v4.4 specifications.

        Args:
            doc: Single einvoice.document record

        Raises:
            ValidationError: If critical mandatory fields are missing
        """
        from datetime import date

        CIIU_MANDATORY_DATE = date(2025, 10, 6)

        errors = []
        partner = doc.partner_id

        # HARD: Partner required for FE
        if not partner:
            errors.append(_(
                'La Factura Electrónica requiere un cliente.\n\n'
                'Opciones:\n'
                '- Seleccione un cliente, o\n'
                '- Cambie el tipo de documento a Tiquete Electrónico (TE)'
            ))
            # Cannot continue validation without partner
            if errors:
                raise ValidationError('\n\n'.join(errors))

        # HARD: Customer name required
        if not partner.name or not partner.name.strip():
            errors.append(_(
                'El nombre del cliente es obligatorio para Factura Electrónica.\n\n'
                'Cliente: %s\n'
                'Por favor actualice el registro del cliente o cambie a Tiquete (TE).'
            ) % (partner.display_name or 'Desconocido'))

        # HARD: Customer VAT/ID required
        if not partner.vat or not partner.vat.strip():
            errors.append(_(
                'El número de cédula/identificación es obligatorio para Factura Electrónica.\n\n'
                'Cliente: %s\n'
                'Por favor actualice el registro del cliente o cambie a Tiquete (TE).'
            ) % partner.name)

        # HARD: ID Type - auto-detected from VAT format via xml_generator._get_partner_id_type()
        # Note: l10n_latam_base is not installed, so l10n_latam_identification_type_id
        # does not exist. The XML generator auto-detects the type from the VAT format.

        # HARD: Email required and valid format
        if not partner.email or not partner.email.strip():
            errors.append(_(
                'El correo electrónico del cliente es obligatorio para Factura Electrónica.\n\n'
                'Cliente: %s\n'
                'El email es obligatorio según normativa de Hacienda.\n'
                'Por favor actualice el registro del cliente o cambie a Tiquete (TE).'
            ) % partner.name)
        else:
            # Validate email format
            import re
            EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not EMAIL_REGEX.match(partner.email.strip()):
                errors.append(_(
                    'Formato de correo electrónico inválido: %s\n\n'
                    'Cliente: %s\n'
                    'Por favor ingrese un email válido para Factura Electrónica.'
                ) % (partner.email, partner.name))

        # DATE-BASED HARD: CIIU required after Oct 6, 2025
        invoice_date = doc.invoice_date or fields.Date.today()
        if invoice_date >= CIIU_MANDATORY_DATE:
            if not partner.l10n_cr_economic_activity_id:
                errors.append(_(
                    'La actividad económica (CIIU) es obligatoria para Factura Electrónica.\n\n'
                    'Cliente: %s\n'
                    'Fecha de factura: %s\n'
                    'El CIIU es obligatorio desde el 6 de octubre de 2025 según normativa de Hacienda.\n\n'
                    'Opciones:\n'
                    '1. Agregue el código CIIU al registro del cliente\n'
                    '2. Cambie a Tiquete Electrónico (TE, no requiere CIIU)'
                ) % (partner.name, invoice_date.strftime('%Y-%m-%d')))

        # If any errors found, raise ValidationError
        if errors:
            error_message = _(
                'No se puede crear Factura Electrónica - Datos del cliente incompletos:\n'
                '═══════════════════════════════════════════════════════════\n\n'
            ) + '\n\n'.join(errors)

            # Log validation failure for audit trail
            _logger.warning(
                f'FE validation failed for document {doc.name or "NEW"}, '
                f'partner {partner.name} (ID: {partner.id}): '
                f'{len(errors)} error(s) found'
            )

            raise ValidationError(error_message)

        # Log successful validation
        _logger.info(
            f'FE mandatory field validation passed for document {doc.name or "NEW"}, '
            f'partner {partner.name} (ID: {partner.id})'
        )

    def validate_factura_requirements(self):
        """
        Public method to validate all Factura Electrónica requirements.

        This method can be called from UI/wizards to check if a document
        can be generated as FE before attempting generation.

        Returns:
            tuple: (is_valid: bool, errors: list, can_downgrade_to_te: bool)
                - is_valid: True if all FE requirements met
                - errors: List of error messages (empty if valid)
                - can_downgrade_to_te: True if TE is a viable alternative
        """
        self.ensure_one()

        errors = []
        partner = self.partner_id

        # All FE validation checks
        if not partner:
            errors.append('No se ha seleccionado un cliente')
            return (False, errors, True)  # Can always downgrade to TE

        if not partner.name or not partner.name.strip():
            errors.append(f'El nombre del cliente está vacío (Partner ID: {partner.id})')

        if not partner.vat or not partner.vat.strip():
            errors.append(f'La cédula/VAT del cliente está vacía: {partner.name}')

        # ID type is auto-detected from VAT format by xml_generator._get_partner_id_type()

        if not partner.email or not partner.email.strip():
            errors.append(f'El correo electrónico del cliente está vacío: {partner.name}')
        else:
            # Validate email format
            import re
            EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not EMAIL_REGEX.match(partner.email.strip()):
                errors.append(f'Formato de email inválido: {partner.email}')

        # Date-based CIIU check
        from datetime import date
        CIIU_MANDATORY_DATE = date(2025, 10, 6)
        invoice_date = self.invoice_date or fields.Date.today()

        if invoice_date >= CIIU_MANDATORY_DATE:
            if not partner.l10n_cr_economic_activity_id:
                errors.append(
                    f'Actividad económica (CIIU) requerida para facturas después del 6 de octubre de 2025 '
                    f'(Fecha de factura: {invoice_date.strftime("%Y-%m-%d")})'
                )

        is_valid = len(errors) == 0
        can_downgrade = True  # FE can always downgrade to TE

        return (is_valid, errors, can_downgrade)

    # ===== CRON JOBS =====

    @api.model
    def _cron_poll_pending_documents(self):
        """
        Cron job: Poll Hacienda for status of submitted documents.
        Called every 15 minutes by ir.cron.
        """
        pending_docs = self.search([
            ('state', 'in', ['submitted']),
        ], limit=50)

        if not pending_docs:
            _logger.info('No pending documents to poll')
            return

        _logger.info('Polling Hacienda for %d pending documents', len(pending_docs))

        success = 0
        failed = 0
        for doc in pending_docs:
            try:
                doc.action_check_status()
                success += 1
            except Exception as e:
                failed += 1
                _logger.warning(
                    'Failed to poll status for document %s: %s',
                    doc.name, str(e)
                )

        _logger.info(
            'Poll complete: %d success, %d failed out of %d total',
            success, failed, len(pending_docs)
        )
