# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # E-Invoice Fields
    l10n_cr_einvoice_document_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='Electronic Invoice Document',
        readonly=True,
        copy=False,
        help='Related Tiquete Electrónico (TE) document',
    )

    l10n_cr_is_einvoice = fields.Boolean(
        string='Generate E-Invoice',
        compute='_compute_l10n_cr_is_einvoice',
        store=True,
        help='Automatically generate electronic invoice for Costa Rica',
    )

    l10n_cr_consecutive = fields.Char(
        string='Consecutive Number',
        readonly=True,
        copy=False,
        help='20-digit consecutive number for electronic receipt',
    )

    l10n_cr_clave = fields.Char(
        string='Hacienda Key',
        size=50,
        readonly=True,
        copy=False,
        help='50-digit unique electronic document key',
    )

    l10n_cr_customer_id_type = fields.Selection([
        ('01', 'Cédula Física'),
        ('02', 'Cédula Jurídica'),
        ('03', 'DIMEX'),
        ('04', 'NITE'),
        ('05', 'Extranjero'),
    ], string='Customer ID Type', help='Type of customer identification')

    l10n_cr_customer_id_number = fields.Char(
        string='Customer ID Number',
        help='Customer identification number',
    )

    l10n_cr_customer_name = fields.Char(
        string='Customer Name',
        help='Customer name for electronic receipt',
    )

    l10n_cr_customer_email = fields.Char(
        string='Customer Email',
        help='Email address for sending electronic receipt',
    )

    l10n_cr_hacienda_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('accepted', 'Accepted by Hacienda'),
        ('rejected', 'Rejected by Hacienda'),
        ('queued', 'Queued for Sync'),
    ], string='Hacienda Status', default='draft', readonly=True, copy=False)

    l10n_cr_offline_queue = fields.Boolean(
        string='In Offline Queue',
        default=False,
        readonly=True,
        copy=False,
        help='Invoice queued for submission when online',
    )

    l10n_cr_hacienda_error = fields.Text(
        string='Hacienda Error Message',
        readonly=True,
        help='Error message from Hacienda if rejected',
    )

    l10n_cr_qr_code = fields.Binary(
        string='QR Code',
        readonly=True,
        attachment=True,
        help='QR code for Hacienda verification',
    )

    @api.depends('company_id', 'company_id.country_id')
    def _compute_l10n_cr_is_einvoice(self):
        """Determine if e-invoice should be generated."""
        for order in self:
            order.l10n_cr_is_einvoice = (
                order.company_id.country_id.code == 'CR' and
                order.company_id.l10n_cr_enable_einvoice
            )

    @api.constrains('l10n_cr_customer_id_type', 'l10n_cr_customer_id_number')
    def _check_l10n_cr_customer_id(self):
        """Validate customer ID format based on type."""
        for order in self:
            if not order.l10n_cr_is_einvoice or not order.l10n_cr_customer_id_type:
                continue

            id_type = order.l10n_cr_customer_id_type
            id_number = order.l10n_cr_customer_id_number or ''

            # Validation patterns
            patterns = {
                '01': (9, 9, 'numeric'),    # Cédula Física: 9 digits
                '02': (10, 10, 'numeric'),  # Cédula Jurídica: 10 digits
                '03': (11, 12, 'numeric'),  # DIMEX: 11-12 digits
                '04': (10, 10, 'numeric'),  # NITE: 10 digits
                '05': (1, 20, 'alphanumeric'),  # Extranjero: 1-20 alphanumeric
            }

            if id_type in patterns:
                min_len, max_len, char_type = patterns[id_type]

                if len(id_number) < min_len or len(id_number) > max_len:
                    raise ValidationError(_(
                        'Invalid ID number length for %s. Expected %s-%s characters, got %s.'
                    ) % (dict(self._fields['l10n_cr_customer_id_type'].selection)[id_type],
                         min_len, max_len, len(id_number)))

                if char_type == 'numeric' and not id_number.isdigit():
                    raise ValidationError(_(
                        'ID number must contain only digits for %s.'
                    ) % dict(self._fields['l10n_cr_customer_id_type'].selection)[id_type])

                if char_type == 'alphanumeric' and not id_number.replace('-', '').replace('_', '').isalnum():
                    raise ValidationError(_(
                        'ID number must be alphanumeric for %s.'
                    ) % dict(self._fields['l10n_cr_customer_id_type'].selection)[id_type])

    def _l10n_cr_is_online(self):
        """Check if Hacienda API is accessible."""
        self.ensure_one()
        try:
            api = self.env['l10n_cr.hacienda.api']
            return api._test_connection(self.company_id)
        except Exception as e:
            _logger.warning('Hacienda API connectivity check failed: %s', str(e))
            return False

    def _l10n_cr_generate_consecutive(self):
        """Generate 20-digit consecutive number for TE."""
        self.ensure_one()

        # Get sequence for this POS terminal
        sequence = self.session_id.config_id.l10n_cr_te_sequence_id
        if not sequence:
            raise UserError(_('No TE sequence configured for POS %s') % self.session_id.config_id.name)

        consecutive = sequence.next_by_id()
        self.l10n_cr_consecutive = consecutive
        return consecutive

    def _l10n_cr_generate_clave(self):
        """Generate 50-digit Hacienda key."""
        self.ensure_one()

        company = self.company_id
        consecutive = self.l10n_cr_consecutive

        if not consecutive:
            raise UserError(_('Consecutive number must be generated first'))

        # Country code (3 digits) - Costa Rica = 506
        country_code = '506'

        # Document date (8 digits: DDMMYYYY)
        doc_date = fields.Datetime.context_timestamp(self, self.date_order)
        date_str = doc_date.strftime('%d%m%Y')

        # Company ID (12 digits - padded)
        company_vat = (company.vat or '').replace('-', '').zfill(12)

        # Consecutive (20 digits)
        consecutive_padded = consecutive.zfill(20)

        # Security code (8 digits - random)
        import random
        security_code = ''.join([str(random.randint(0, 9)) for _ in range(8)])

        # Document type (1 digit) - TE = 04
        doc_type = '4'  # Tiquete Electrónico

        # Build clave (50 digits total)
        clave = country_code + date_str + company_vat + consecutive_padded + doc_type + security_code

        if len(clave) != 50:
            raise UserError(_('Generated clave must be exactly 50 digits, got %s') % len(clave))

        self.l10n_cr_clave = clave
        return clave

    def _l10n_cr_prepare_invoice_data(self):
        """Prepare data for electronic invoice document."""
        self.ensure_one()

        # Ensure we have consecutive and clave
        if not self.l10n_cr_consecutive:
            self._l10n_cr_generate_consecutive()

        if not self.l10n_cr_clave:
            self._l10n_cr_generate_clave()

        # Get customer data (use session partner if no specific customer)
        customer_id_type = self.l10n_cr_customer_id_type
        customer_id_number = self.l10n_cr_customer_id_number
        customer_name = self.l10n_cr_customer_name
        customer_email = self.l10n_cr_customer_email

        if not customer_id_type or not customer_id_number:
            # Use default "walk-in customer" ID
            customer_id_type = '05'  # Extranjero
            customer_id_number = '999999999999'
            customer_name = 'Cliente General'

        # Prepare line items
        lines = []
        for line in self.lines:
            if line.qty <= 0:
                continue

            # Get Cabys code from product
            cabys_code = line.product_id.l10n_cr_cabys_code or '0000000000000'

            line_data = {
                'sequence': len(lines) + 1,
                'product_id': line.product_id.id,
                'product_code': line.product_id.default_code or '',
                'product_code_type': '04',  # Internal code
                'cabys_code': cabys_code,
                'product_name': line.product_id.name,
                'quantity': line.qty,
                'uom': line.product_id.uom_id.name or 'Unidad',
                'unit_price': line.price_unit,
                'subtotal': line.price_subtotal,
                'discount': line.discount,
                'tax_amount': line.price_subtotal_incl - line.price_subtotal,
            }
            lines.append(line_data)

        # Prepare payment methods
        payment_methods = []
        for payment in self.payment_ids:
            payment_method = payment.payment_method_id
            method_code = '01'  # Default to Efectivo

            # Map Odoo payment methods to Hacienda codes
            if payment_method.is_cash_count:
                method_code = '01'  # Efectivo
            elif payment_method.use_payment_terminal:
                method_code = '02'  # Tarjeta

            payment_data = {
                'payment_method': method_code,
                'amount': payment.amount,
            }
            payment_methods.append(payment_data)

        return {
            'document_type': 'TE',
            'clave': self.l10n_cr_clave,
            'consecutive': self.l10n_cr_consecutive,
            'date_issue': self.date_order,
            'customer_id_type': customer_id_type,
            'customer_id_number': customer_id_number,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'currency_code': self.currency_id.name,
            'exchange_rate': 1.0,
            'lines': lines,
            'payment_methods': payment_methods,
            'total_amount': self.amount_total,
            'total_tax': self.amount_tax,
        }

    def _l10n_cr_generate_einvoice(self):
        """Generate Tiquete Electrónico after POS order validation."""
        self.ensure_one()

        if not self.l10n_cr_is_einvoice:
            _logger.info('E-invoice generation disabled for order %s', self.name)
            return

        if self.l10n_cr_einvoice_document_id:
            _logger.warning('E-invoice already generated for order %s', self.name)
            return

        try:
            # Prepare invoice data
            invoice_data = self._l10n_cr_prepare_invoice_data()

            # Create account move for the einvoice document
            move_vals = {
                'move_type': 'out_invoice',
                'partner_id': self.partner_id.id or self.env.ref('base.public_partner').id,
                'invoice_date': fields.Date.context_today(self),
                'invoice_line_ids': [],
                'pos_order_ids': [(4, self.id)],
            }

            # Add invoice lines
            for line_data in invoice_data['lines']:
                line = self.lines.filtered(lambda l: l.product_id.id == line_data.get('product_id'))[:1]
                if line:
                    move_vals['invoice_line_ids'].append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line_data['quantity'],
                        'price_unit': line_data['unit_price'],
                        'name': line_data['product_name'],
                    }))

            # Create invoice
            move = self.env['account.move'].create(move_vals)
            move.action_post()

            # Create einvoice document
            einvoice_vals = {
                'name': self.l10n_cr_consecutive,
                'move_id': move.id,
                'company_id': self.company_id.id,
                'document_type': 'TE',
                'clave': self.l10n_cr_clave,
            }

            einvoice = self.env['l10n_cr.einvoice.document'].create(einvoice_vals)
            self.l10n_cr_einvoice_document_id = einvoice

            # Generate and sign XML
            einvoice.action_generate_xml()
            einvoice.action_sign_xml()

            # Submit to Hacienda or queue for later
            if self._l10n_cr_is_online():
                einvoice.action_submit_to_hacienda()
                self.l10n_cr_hacienda_status = 'pending'
            else:
                self._l10n_cr_queue_for_sync(einvoice)

            # Generate QR code
            self._l10n_cr_generate_qr_code(einvoice)

            _logger.info('E-invoice generated successfully for POS order %s', self.name)

        except Exception as e:
            _logger.error('Error generating e-invoice for POS order %s: %s', self.name, str(e))
            self.l10n_cr_hacienda_status = 'draft'
            self.l10n_cr_hacienda_error = str(e)
            raise UserError(_('Failed to generate electronic invoice: %s') % str(e))

    def _l10n_cr_queue_for_sync(self, einvoice):
        """Queue invoice for later submission when offline."""
        self.ensure_one()

        # Create queue entry
        queue_vals = {
            'pos_order_id': self.id,
            'einvoice_document_id': einvoice.id,
            'xml_data': einvoice.signed_xml,
            'state': 'pending',
        }

        self.env['l10n_cr.pos.offline.queue'].create(queue_vals)

        self.l10n_cr_offline_queue = True
        self.l10n_cr_hacienda_status = 'queued'

        _logger.info('E-invoice queued for sync: POS order %s', self.name)

    def _l10n_cr_generate_qr_code(self, einvoice):
        """Generate QR code for receipt."""
        self.ensure_one()

        try:
            qr_generator = self.env['l10n_cr.qr.generator']
            qr_data = qr_generator.generate_qr_code(
                clave=self.l10n_cr_clave,
                emisor=self.company_id.vat or '',
                receptor=self.l10n_cr_customer_id_number or '999999999999',
                total=str(self.amount_total),
                tax=str(self.amount_tax),
            )

            self.l10n_cr_qr_code = qr_data

        except Exception as e:
            _logger.warning('Failed to generate QR code for POS order %s: %s', self.name, str(e))

    @api.model
    def _l10n_cr_sync_offline_invoices(self):
        """Sync queued offline invoices (called by cron or manually)."""
        queue_entries = self.env['l10n_cr.pos.offline.queue'].search([
            ('state', '=', 'pending'),
        ], limit=50)  # Process in batches

        if not queue_entries:
            return

        _logger.info('Starting sync of %d queued invoices', len(queue_entries))

        success_count = 0
        error_count = 0

        for entry in queue_entries:
            try:
                # Check if we're online
                if not entry.pos_order_id._l10n_cr_is_online():
                    _logger.warning('Still offline, skipping sync')
                    break

                # Submit to Hacienda
                entry.state = 'syncing'
                entry.einvoice_document_id.action_submit_to_hacienda()

                # Mark as synced
                entry.state = 'synced'
                entry.pos_order_id.l10n_cr_offline_queue = False
                entry.pos_order_id.l10n_cr_hacienda_status = 'pending'

                success_count += 1
                _logger.info('Successfully synced invoice for POS order %s', entry.pos_order_id.name)

            except Exception as e:
                error_count += 1
                entry.retry_count += 1
                entry.last_error = str(e)

                # Mark as failed after 5 retries
                if entry.retry_count >= 5:
                    entry.state = 'failed'
                else:
                    entry.state = 'pending'

                _logger.error('Error syncing invoice for POS order %s: %s',
                             entry.pos_order_id.name, str(e))

        _logger.info('Sync completed: %d success, %d errors', success_count, error_count)

        return {
            'success': success_count,
            'errors': error_count,
        }

    def action_l10n_cr_resend_email(self):
        """Resend electronic receipt via email."""
        self.ensure_one()

        if not self.l10n_cr_einvoice_document_id:
            raise UserError(_('No electronic invoice found for this order'))

        if not self.l10n_cr_customer_email:
            raise UserError(_('No customer email address configured'))

        try:
            self.l10n_cr_einvoice_document_id.action_send_email()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Email Sent'),
                    'message': _('Electronic receipt sent to %s') % self.l10n_cr_customer_email,
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError(_('Failed to send email: %s') % str(e))

    def action_l10n_cr_resubmit_hacienda(self):
        """Resubmit invoice to Hacienda."""
        self.ensure_one()

        if not self.l10n_cr_einvoice_document_id:
            raise UserError(_('No electronic invoice found for this order'))

        if self.l10n_cr_hacienda_status == 'accepted':
            raise UserError(_('Invoice already accepted by Hacienda'))

        try:
            if not self._l10n_cr_is_online():
                raise UserError(_('Cannot connect to Hacienda. Check your internet connection.'))

            self.l10n_cr_einvoice_document_id.action_submit_to_hacienda()
            self.l10n_cr_hacienda_status = 'pending'

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Resubmitted'),
                    'message': _('Invoice resubmitted to Hacienda'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError(_('Failed to resubmit: %s') % str(e))

    def action_l10n_cr_check_status(self):
        """Check Hacienda status for this invoice."""
        self.ensure_one()

        if not self.l10n_cr_einvoice_document_id:
            raise UserError(_('No electronic invoice found for this order'))

        try:
            einvoice = self.l10n_cr_einvoice_document_id
            api = self.env['l10n_cr.hacienda.api']
            status = api.check_invoice_status(einvoice.clave, self.company_id)

            # Update status based on response
            if status.get('estado') == 'aceptado':
                self.l10n_cr_hacienda_status = 'accepted'
                einvoice.state = 'accepted'
            elif status.get('estado') == 'rechazado':
                self.l10n_cr_hacienda_status = 'rejected'
                einvoice.state = 'rejected'
                self.l10n_cr_hacienda_error = status.get('detalle', 'Unknown error')

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Status Updated'),
                    'message': _('Current status: %s') % self.l10n_cr_hacienda_status,
                    'type': 'info',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError(_('Failed to check status: %s') % str(e))
