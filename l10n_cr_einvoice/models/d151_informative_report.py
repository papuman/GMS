# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class D151InformativeReport(models.Model):
    """
    D-151 Annual Informative Declaration

    Costa Rica annual informative report.
    Filing deadline: April 15 of following year.

    Reports detailed transactions with customers and suppliers
    for transactions above threshold (currently ₡500,000).
    """
    _name = 'l10n_cr.d151.report'
    _description = 'D-151 Annual Informative Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_id desc'

    name = fields.Char(
        string='Report Number',
        readonly=True,
        copy=False,
        help='Sequential report number'
    )

    period_id = fields.Many2one(
        'l10n_cr.tax.report.period',
        string='Period',
        required=True,
        ondelete='restrict',
        help='Tax period (annual) for this report'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('ready', 'Ready to Submit'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('error', 'Error'),
    ], string='Status', default='draft', required=True, tracking=True)

    # =====================================================
    # CONFIGURATION
    # =====================================================

    threshold_amount = fields.Monetary(
        string='Reporting Threshold',
        currency_field='currency_id',
        default=2500000.0,
        help='Minimum transaction amount to report (₡2,500,000 for general transactions in Costa Rica)'
    )

    specific_expense_threshold = fields.Monetary(
        string='Specific Expense Threshold',
        currency_field='currency_id',
        default=50000.0,
        help='Minimum amount for specific expenses (Professional Services, Rentals, Commissions, Interest)'
    )

    # =====================================================
    # SUMMARY STATISTICS
    # =====================================================

    total_customers_reported = fields.Integer(
        string='Total Customers Reported',
        compute='_compute_statistics',
        store=True,
        help='Number of customers with transactions above threshold'
    )

    total_suppliers_reported = fields.Integer(
        string='Total Suppliers Reported',
        compute='_compute_statistics',
        store=True,
        help='Number of suppliers with transactions above threshold'
    )

    total_sales_amount = fields.Monetary(
        string='Total Sales Reported',
        compute='_compute_statistics',
        store=True,
        currency_field='currency_id',
        help='Total sales to customers above threshold'
    )

    total_purchases_amount = fields.Monetary(
        string='Total Purchases Reported',
        compute='_compute_statistics',
        store=True,
        currency_field='currency_id',
        help='Total purchases from suppliers above threshold'
    )

    # =====================================================
    # DETAILED LINES
    # =====================================================

    customer_line_ids = fields.One2many(
        'l10n_cr.d151.customer.line',
        'report_id',
        string='Customer Lines',
        help='Detailed customer transactions'
    )

    supplier_line_ids = fields.One2many(
        'l10n_cr.d151.supplier.line',
        'report_id',
        string='Supplier Lines',
        help='Detailed supplier transactions'
    )

    expense_line_ids = fields.One2many(
        'l10n_cr.d151.expense.line',
        'report_id',
        string='Specific Expense Lines',
        help='Professional Services, Rentals, Commissions, Interest (above ₡50,000)'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )

    # =====================================================
    # HACIENDA SUBMISSION
    # =====================================================

    xml_content = fields.Text(
        string='D-151 XML',
        readonly=True,
        help='Generated XML for TRIBU-CR submission'
    )

    xml_signed = fields.Text(
        string='Signed XML',
        readonly=True,
        help='Digitally signed XML'
    )

    submission_key = fields.Char(
        string='Submission Key',
        readonly=True,
        copy=False,
        help='Hacienda unique key for this submission'
    )

    submission_date = fields.Datetime(
        string='Submission Date',
        readonly=True,
        help='Date/time submitted to Hacienda'
    )

    acceptance_date = fields.Datetime(
        string='Acceptance Date',
        readonly=True,
        help='Date/time accepted by Hacienda'
    )

    hacienda_message = fields.Text(
        string='Hacienda Response',
        readonly=True,
        help='Latest message from Hacienda'
    )

    notes = fields.Text(
        string='Internal Notes',
        help='Internal notes about this declaration'
    )

    # =====================================================
    # COMPUTED FIELDS
    # =====================================================

    @api.depends('customer_line_ids', 'supplier_line_ids')
    def _compute_statistics(self):
        """Calculate summary statistics"""
        for record in self:
            record.total_customers_reported = len(record.customer_line_ids)
            record.total_suppliers_reported = len(record.supplier_line_ids)

            record.total_sales_amount = sum(
                line.total_amount for line in record.customer_line_ids
            )
            record.total_purchases_amount = sum(
                line.total_amount for line in record.supplier_line_ids
            )

    # =====================================================
    # ACTIONS
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate sequential name"""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_cr.d151.report') or _('New')
        return super().create(vals_list)

    def action_calculate(self):
        """
        Calculate D-151 by finding all customers/suppliers
        with transactions above threshold
        """
        self.ensure_one()

        if not self.period_id:
            raise UserError(_('Period is required to calculate the report.'))

        # Clear existing lines
        self.customer_line_ids.unlink()
        self.supplier_line_ids.unlink()

        # Calculate customer lines (sales above threshold)
        self._calculate_customer_lines()

        # Calculate supplier lines (purchases above threshold)
        self._calculate_supplier_lines()

        self.state = 'calculated'
        self.message_post(body=_(
            'D-151 calculated: %d customers, %d suppliers'
        ) % (self.total_customers_reported, self.total_suppliers_reported))

        return True

    def _calculate_customer_lines(self):
        """
        Find all customers with sales above threshold
        """
        self.ensure_one()

        # Group sales by customer
        query = """
            SELECT
                partner_id,
                SUM(amount_untaxed) as total_sales,
                COUNT(*) as invoice_count
            FROM account_move
            WHERE company_id = %s
                AND move_type IN ('out_invoice', 'out_refund')
                AND state = 'posted'
                AND invoice_date >= %s
                AND invoice_date <= %s
            GROUP BY partner_id
            HAVING SUM(amount_untaxed) >= %s
            ORDER BY SUM(amount_untaxed) DESC
        """

        self.env.cr.execute(query, (
            self.company_id.id,
            self.period_id.date_from,
            self.period_id.date_to,
            self.threshold_amount,
        ))

        CustomerLine = self.env['l10n_cr.d151.customer.line']

        for row in self.env.cr.fetchall():
            partner_id, total_sales, invoice_count = row

            partner = self.env['res.partner'].browse(partner_id)

            CustomerLine.create({
                'report_id': self.id,
                'partner_id': partner_id,
                'partner_vat': partner.vat or '',
                'partner_name': partner.name,
                'total_amount': total_sales,
                'transaction_count': invoice_count,
            })

    def _calculate_supplier_lines(self):
        """
        Find all suppliers with purchases above threshold
        """
        self.ensure_one()

        # Group purchases by supplier
        query = """
            SELECT
                partner_id,
                SUM(amount_untaxed) as total_purchases,
                COUNT(*) as bill_count
            FROM account_move
            WHERE company_id = %s
                AND move_type = 'in_invoice'
                AND state = 'posted'
                AND invoice_date >= %s
                AND invoice_date <= %s
            GROUP BY partner_id
            HAVING SUM(amount_untaxed) >= %s
            ORDER BY SUM(amount_untaxed) DESC
        """

        self.env.cr.execute(query, (
            self.company_id.id,
            self.period_id.date_from,
            self.period_id.date_to,
            self.threshold_amount,
        ))

        SupplierLine = self.env['l10n_cr.d151.supplier.line']

        for row in self.env.cr.fetchall():
            partner_id, total_purchases, bill_count = row

            partner = self.env['res.partner'].browse(partner_id)

            SupplierLine.create({
                'report_id': self.id,
                'partner_id': partner_id,
                'partner_vat': partner.vat or '',
                'partner_name': partner.name,
                'total_amount': total_purchases,
                'transaction_count': bill_count,
            })

    def action_generate_xml(self):
        """Generate D-151 XML for TRIBU-CR submission"""
        self.ensure_one()

        if self.state not in ['calculated', 'ready']:
            raise UserError(_('Report must be calculated before generating XML.'))

        XMLGenerator = self.env['l10n_cr.tax.report.xml.generator']
        xml_content = XMLGenerator.generate_d151_xml(self)

        self.xml_content = xml_content
        self.state = 'ready'
        self.message_post(body=_('D-151 XML generated successfully'))

        return True

    def action_sign_xml(self):
        """Digitally sign the D-151 XML"""
        self.ensure_one()

        if not self.xml_content:
            raise UserError(_('Generate XML before signing.'))

        XMLSigner = self.env['l10n_cr.xml.signer']
        signed_xml = XMLSigner.sign_xml(
            self.xml_content,
            self.company_id.hacienda_certificate_id
        )

        self.xml_signed = signed_xml
        self.message_post(body=_('D-151 XML signed successfully'))

        return True

    def action_submit_to_hacienda(self):
        """Submit signed D-151 to Hacienda"""
        self.ensure_one()

        if not self.xml_signed:
            raise UserError(_('Firme el XML antes de enviar a Hacienda.'))

        try:
            HaciendaAPI = self.env['l10n_cr.hacienda.api']
            result = HaciendaAPI.submit_d151_report(
                report_id=self.id,
                signed_xml=self.xml_signed
            )

            if result.get('success'):
                self.submission_key = result.get('key')
                self.submission_date = fields.Datetime.now()
                self.state = 'submitted'
                self.hacienda_message = result.get('message', _('Enviado exitosamente'))
                self.message_post(body=_('D-151 enviado a Hacienda: %s') % self.submission_key)
            else:
                self.state = 'error'
                self.hacienda_message = result.get('error', _('Error desconocido'))
                self.message_post(body=_('Envío fallido: %s') % self.hacienda_message)

        except Exception as e:
            self.state = 'error'
            self.hacienda_message = str(e)
            self.message_post(body=_('Error durante el envío: %s') % str(e))
            raise

        return True

    def action_check_status(self):
        """Check submission status with Hacienda"""
        self.ensure_one()

        if not self.submission_key:
            raise UserError(_('No se encontró clave de envío. Envíe primero.'))

        try:
            HaciendaAPI = self.env['l10n_cr.hacienda.api']
            result = HaciendaAPI.check_tax_report_status(
                submission_key=self.submission_key,
                report_type='D151'
            )

            estado = result.get('estado', '').lower()

            if estado == 'aceptado':
                self.state = 'accepted'
                self.acceptance_date = fields.Datetime.now()
                self.hacienda_message = result.get('message', _('Aceptado'))
                self.message_post(body=_('D-151 aceptado por Hacienda'))
                if self.period_id:
                    self.period_id.state = 'accepted'

            elif estado == 'rechazado':
                self.state = 'rejected'
                error_details = result.get('detalle', '')
                errores = result.get('errores', [])
                if errores:
                    error_details += '\n' + '\n'.join([str(e) for e in errores])
                self.hacienda_message = result.get('message', _('Rechazado')) + '\n' + error_details
                self.message_post(body=_('D-151 rechazado: %s') % self.hacienda_message)

            elif estado in ['procesando', 'recibido']:
                self.hacienda_message = result.get('message', _('En procesamiento'))
                self.message_post(body=_('D-151 en procesamiento'))

            else:
                self.hacienda_message = result.get('message', _('Estado desconocido: %s') % estado)

        except Exception as e:
            self.message_post(body=_('Error al verificar estado: %s') % str(e))
            raise

        return True

    def action_reset_to_draft(self):
        """Reset to draft for corrections"""
        self.ensure_one()

        if self.state in ['submitted', 'accepted']:
            raise UserError(_('Cannot reset submitted or accepted reports.'))

        self.state = 'draft'
        self.xml_content = False
        self.xml_signed = False
        self.message_post(body=_('Report reset to draft'))

        return True


class D151CustomerLine(models.Model):
    """D-151 Customer Transaction Line"""
    _name = 'l10n_cr.d151.customer.line'
    _description = 'D-151 Customer Line'
    _order = 'total_amount desc'

    report_id = fields.Many2one(
        'l10n_cr.d151.report',
        string='D-151 Report',
        required=True,
        ondelete='cascade'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True
    )

    partner_vat = fields.Char(
        string='Customer VAT',
        required=True,
        help='Customer tax identification number'
    )

    partner_name = fields.Char(
        string='Customer Name',
        required=True
    )

    total_amount = fields.Monetary(
        string='Total Sales',
        required=True,
        currency_field='currency_id',
        help='Total sales to this customer during the year'
    )

    transaction_count = fields.Integer(
        string='Number of Invoices',
        help='Number of invoices issued to this customer'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='report_id.currency_id',
        readonly=True
    )


class D151SupplierLine(models.Model):
    """D-151 Supplier Transaction Line"""
    _name = 'l10n_cr.d151.supplier.line'
    _description = 'D-151 Supplier Line'
    _order = 'total_amount desc'

    report_id = fields.Many2one(
        'l10n_cr.d151.report',
        string='D-151 Report',
        required=True,
        ondelete='cascade'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        required=True
    )

    partner_vat = fields.Char(
        string='Supplier VAT',
        required=True,
        help='Supplier tax identification number'
    )

    partner_name = fields.Char(
        string='Supplier Name',
        required=True
    )

    total_amount = fields.Monetary(
        string='Total Purchases',
        required=True,
        currency_field='currency_id',
        help='Total purchases from this supplier during the year'
    )

    transaction_count = fields.Integer(
        string='Number of Bills',
        help='Number of bills received from this supplier'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='report_id.currency_id',
        readonly=True
    )

class D151ExpenseLine(models.Model):
    """D-151 Specific Expense Line"""
    _name = 'l10n_cr.d151.expense.line'
    _description = 'D-151 Specific Expense Line'
    _order = 'total_amount desc'

    report_id = fields.Many2one(
        'l10n_cr.d151.report',
        string='D-151 Report',
        required=True,
        ondelete='cascade'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Service Provider',
        required=True
    )

    partner_vat = fields.Char(
        string='Provider VAT',
        required=True,
        help='Service provider tax identification number'
    )

    partner_name = fields.Char(
        string='Provider Name',
        required=True
    )

    expense_type = fields.Selection([
        ('SP', 'Professional Services'),
        ('A', 'Rentals'),
        ('M', 'Commissions'),
        ('I', 'Interest'),
    ], string='Expense Type',
        required=True,
        help='Type of specific expense for D-151'
    )

    total_amount = fields.Monetary(
        string='Total Amount',
        required=True,
        currency_field='currency_id',
        help='Total amount paid for this expense type during the year (minimum ₡50,000)'
    )

    transaction_count = fields.Integer(
        string='Number of Transactions',
        help='Number of transactions with this provider'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='report_id.currency_id',
        readonly=True
    )
