# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class D150VATReport(models.Model):
    """
    D-150 Monthly VAT Declaration Report

    Costa Rica monthly VAT (IVA) declaration form.
    Reuses existing invoice data from get_monthly_filing_report().

    Filing deadline: 15th of following month
    """
    _name = 'l10n_cr.d150.report'
    _description = 'D-150 Monthly VAT Report'
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
        help='Tax period for this report'
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
    # SECTION 1: SALES (Ventas - IVA Generado)
    # =====================================================

    sales_13_base = fields.Monetary(
        string='Sales 13% - Base',
        currency_field='currency_id',
        help='Taxable base for sales at 13% VAT rate'
    )
    sales_13_tax = fields.Monetary(
        string='Sales 13% - Tax',
        currency_field='currency_id',
        help='VAT collected on 13% sales'
    )

    sales_4_base = fields.Monetary(
        string='Sales 4% - Base',
        currency_field='currency_id',
        help='Taxable base for sales at 4% VAT rate (reduced rate)'
    )
    sales_4_tax = fields.Monetary(
        string='Sales 4% - Tax',
        currency_field='currency_id',
        help='VAT collected on 4% sales'
    )

    sales_2_base = fields.Monetary(
        string='Sales 2% - Base',
        currency_field='currency_id',
        help='Taxable base for sales at 2% VAT rate (reduced rate)'
    )
    sales_2_tax = fields.Monetary(
        string='Sales 2% - Tax',
        currency_field='currency_id',
        help='VAT collected on 2% sales'
    )

    sales_1_base = fields.Monetary(
        string='Sales 1% - Base',
        currency_field='currency_id',
        help='Taxable base for sales at 1% VAT rate (reduced rate)'
    )
    sales_1_tax = fields.Monetary(
        string='Sales 1% - Tax',
        currency_field='currency_id',
        help='VAT collected on 1% sales'
    )

    sales_exempt = fields.Monetary(
        string='Exempt Sales',
        currency_field='currency_id',
        help='Sales exempt from VAT'
    )

    sales_total_base = fields.Monetary(
        string='Total Sales Base',
        compute='_compute_sales_totals',
        store=True,
        currency_field='currency_id',
        help='Sum of all taxable bases'
    )

    sales_total_tax = fields.Monetary(
        string='Total VAT Collected',
        compute='_compute_sales_totals',
        store=True,
        currency_field='currency_id',
        help='Total VAT collected from sales (IVA Generado)'
    )

    # Credit Notes (reduce VAT collected)
    credit_notes_13_base = fields.Monetary(
        string='Credit Notes 13% - Base',
        currency_field='currency_id',
        help='Credit notes at 13% reducing VAT collected'
    )
    credit_notes_13_tax = fields.Monetary(
        string='Credit Notes 13% - Tax',
        currency_field='currency_id',
        help='VAT reduction from credit notes'
    )

    credit_notes_4_base = fields.Monetary(
        string='Credit Notes 4% - Base',
        currency_field='currency_id',
        help='Credit notes at 4% reducing VAT collected'
    )
    credit_notes_4_tax = fields.Monetary(
        string='Credit Notes 4% - Tax',
        currency_field='currency_id',
        help='VAT reduction from 4% credit notes'
    )

    credit_notes_2_base = fields.Monetary(
        string='Credit Notes 2% - Base',
        currency_field='currency_id',
        help='Credit notes at 2% reducing VAT collected'
    )
    credit_notes_2_tax = fields.Monetary(
        string='Credit Notes 2% - Tax',
        currency_field='currency_id',
        help='VAT reduction from 2% credit notes'
    )

    credit_notes_1_base = fields.Monetary(
        string='Credit Notes 1% - Base',
        currency_field='currency_id',
        help='Credit notes at 1% reducing VAT collected'
    )
    credit_notes_1_tax = fields.Monetary(
        string='Credit Notes 1% - Tax',
        currency_field='currency_id',
        help='VAT reduction from 1% credit notes'
    )

    # =====================================================
    # SECTION 2: PURCHASES (Compras - IVA Soportado)
    # =====================================================

    purchases_goods_13_base = fields.Monetary(
        string='Purchases Goods 13% - Base',
        currency_field='currency_id',
        help='Goods purchases at 13% (deductible VAT)'
    )
    purchases_goods_13_tax = fields.Monetary(
        string='Purchases Goods 13% - Tax',
        currency_field='currency_id',
        help='VAT credit from goods purchases'
    )

    purchases_services_13_base = fields.Monetary(
        string='Purchases Services 13% - Base',
        currency_field='currency_id',
        help='Service purchases at 13% (deductible VAT)'
    )
    purchases_services_13_tax = fields.Monetary(
        string='Purchases Services 13% - Tax',
        currency_field='currency_id',
        help='VAT credit from service purchases'
    )

    purchases_4_base = fields.Monetary(
        string='Purchases 4% - Base',
        currency_field='currency_id',
        help='Purchases at 4% reduced rate'
    )
    purchases_4_tax = fields.Monetary(
        string='Purchases 4% - Tax',
        currency_field='currency_id',
        help='VAT credit from 4% purchases'
    )

    purchases_2_base = fields.Monetary(
        string='Purchases 2% - Base',
        currency_field='currency_id',
        help='Purchases at 2% reduced rate'
    )
    purchases_2_tax = fields.Monetary(
        string='Purchases 2% - Tax',
        currency_field='currency_id',
        help='VAT credit from 2% purchases'
    )

    purchases_1_base = fields.Monetary(
        string='Purchases 1% - Base',
        currency_field='currency_id',
        help='Purchases at 1% reduced rate'
    )
    purchases_1_tax = fields.Monetary(
        string='Purchases 1% - Tax',
        currency_field='currency_id',
        help='VAT credit from 1% purchases'
    )

    purchases_exempt = fields.Monetary(
        string='Exempt Purchases',
        currency_field='currency_id',
        help='Purchases exempt from VAT (no credit)'
    )

    purchases_total_base = fields.Monetary(
        string='Total Purchases Base',
        compute='_compute_purchases_totals',
        store=True,
        currency_field='currency_id',
        help='Sum of all purchase bases'
    )

    purchases_total_tax = fields.Monetary(
        string='Total VAT Credit',
        compute='_compute_purchases_totals',
        store=True,
        currency_field='currency_id',
        help='Total VAT credit available (IVA Soportado)'
    )

    # =====================================================
    # SECTION 3: VAT SETTLEMENT (Liquidación del IVA)
    # =====================================================

    proportionality_factor = fields.Float(
        string='Proportionality Factor',
        compute='_compute_proportionality',
        store=True,
        digits=(5, 2),
        help='Percentage of VAT credit allowed based on taxable vs total sales (auto-calculated)'
    )

    adjusted_credit = fields.Monetary(
        string='Adjusted VAT Credit',
        compute='_compute_settlement',
        store=True,
        currency_field='currency_id',
        help='Purchase VAT credit adjusted by proportionality factor'
    )

    previous_balance = fields.Monetary(
        string='Previous Period Balance',
        currency_field='currency_id',
        default=0.0,
        help='VAT balance from previous month (positive = credit, negative = debt)'
    )

    net_amount_due = fields.Monetary(
        string='Net Amount Due',
        compute='_compute_settlement',
        store=True,
        currency_field='currency_id',
        help='Final VAT to pay (positive) or credit to carry forward (negative)'
    )

    amount_to_pay = fields.Monetary(
        string='Amount to Pay',
        compute='_compute_settlement',
        store=True,
        currency_field='currency_id',
        help='Amount owed to Hacienda (if positive)'
    )

    credit_to_next_period = fields.Monetary(
        string='Credit to Next Period',
        compute='_compute_settlement',
        store=True,
        currency_field='currency_id',
        help='Credit balance to carry forward (if negative)'
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
        string='D-150 XML',
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

    @api.depends(
        'sales_13_base', 'sales_13_tax',
        'sales_4_base', 'sales_4_tax',
        'sales_2_base', 'sales_2_tax',
        'sales_1_base', 'sales_1_tax',
        'sales_exempt',
        'credit_notes_13_base', 'credit_notes_13_tax',
        'credit_notes_4_base', 'credit_notes_4_tax',
        'credit_notes_2_base', 'credit_notes_2_tax',
        'credit_notes_1_base', 'credit_notes_1_tax',
    )
    def _compute_sales_totals(self):
        """Calculate total sales and VAT collected"""
        for record in self:
            total_cn_base = (
                record.credit_notes_13_base + record.credit_notes_4_base +
                record.credit_notes_2_base + record.credit_notes_1_base
            )
            total_cn_tax = (
                record.credit_notes_13_tax + record.credit_notes_4_tax +
                record.credit_notes_2_tax + record.credit_notes_1_tax
            )

            record.sales_total_base = (
                record.sales_13_base + record.sales_4_base +
                record.sales_2_base + record.sales_1_base +
                record.sales_exempt - total_cn_base
            )

            record.sales_total_tax = (
                record.sales_13_tax + record.sales_4_tax +
                record.sales_2_tax + record.sales_1_tax -
                total_cn_tax
            )

    @api.depends(
        'purchases_goods_13_base', 'purchases_goods_13_tax',
        'purchases_services_13_base', 'purchases_services_13_tax',
        'purchases_4_base', 'purchases_4_tax',
        'purchases_2_base', 'purchases_2_tax',
        'purchases_1_base', 'purchases_1_tax',
        'purchases_exempt'
    )
    def _compute_purchases_totals(self):
        """Calculate total purchases and VAT credit"""
        for record in self:
            record.purchases_total_base = (
                record.purchases_goods_13_base + record.purchases_services_13_base +
                record.purchases_4_base + record.purchases_2_base +
                record.purchases_1_base + record.purchases_exempt
            )

            record.purchases_total_tax = (
                record.purchases_goods_13_tax + record.purchases_services_13_tax +
                record.purchases_4_tax + record.purchases_2_tax +
                record.purchases_1_tax
            )

    @api.depends('sales_total_base', 'sales_exempt')
    def _compute_proportionality(self):
        """
        Calculate proportionality factor for VAT credit

        Formula: (Taxable Sales / Total Sales) × 100

        When company has both taxable and exempt sales, only a proportional
        amount of purchase VAT can be credited.

        If all sales are taxable: 100%
        If mixed sales: Proportional to taxable vs total
        """
        for record in self:
            # sales_total_base already includes exempt sales
            # So taxable is total minus exempt
            total_sales = record.sales_total_base
            taxable_sales = total_sales - record.sales_exempt

            if total_sales > 0:
                record.proportionality_factor = (taxable_sales / total_sales) * 100.0
            else:
                # No sales = assume 100% taxable activities
                record.proportionality_factor = 100.0

    @api.depends(
        'sales_total_tax',
        'purchases_total_tax',
        'proportionality_factor',
        'previous_balance'
    )
    def _compute_settlement(self):
        """
        Calculate final VAT settlement

        Formula:
        Net Amount Due = VAT Collected - (VAT Credit × Proportionality) - Previous Balance

        If positive: Amount to pay
        If negative: Credit to next period
        """
        for record in self:
            # Adjust purchase VAT credit by proportionality
            record.adjusted_credit = record.purchases_total_tax * (record.proportionality_factor / 100.0)

            # Calculate net amount
            record.net_amount_due = (
                record.sales_total_tax -
                record.adjusted_credit -
                record.previous_balance
            )

            # Split into payment or credit
            if record.net_amount_due > 0:
                record.amount_to_pay = record.net_amount_due
                record.credit_to_next_period = 0.0
            else:
                record.amount_to_pay = 0.0
                record.credit_to_next_period = abs(record.net_amount_due)

    # =====================================================
    # ACTIONS
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate sequential name"""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_cr.d150.report') or _('New')
        return super().create(vals_list)

    def action_calculate(self):
        """Calculate D-150 VAT report from invoices"""
        self.ensure_one()

        if not self.period_id:
            raise UserError(_('Period is required to calculate the report.'))

        # Calculate sales from customer invoices
        self._calculate_sales()

        # Calculate purchases from vendor bills
        self._calculate_purchases()

        # Get previous period balance if exists
        self._get_previous_balance()

        self.state = 'calculated'
        self.message_post(body=_('Report calculated successfully'))

        return True

    def _calculate_sales(self):
        """Calculate sales VAT from customer invoices"""
        self.ensure_one()

        AccountMove = self.env['account.move']

        # Get all customer invoices in period that are posted
        invoices = AccountMove.search([
            ('company_id', '=', self.company_id.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.period_id.date_from),
            ('invoice_date', '<=', self.period_id.date_to),
        ])

        # Initialize totals by rate
        sales_by_rate = {
            13: {'base': 0.0, 'tax': 0.0},
            4: {'base': 0.0, 'tax': 0.0},
            2: {'base': 0.0, 'tax': 0.0},
            1: {'base': 0.0, 'tax': 0.0},
            0: {'base': 0.0},  # Exempt
        }

        credit_notes = {
            13: {'base': 0.0, 'tax': 0.0},
            4: {'base': 0.0, 'tax': 0.0},
            2: {'base': 0.0, 'tax': 0.0},
            1: {'base': 0.0, 'tax': 0.0},
        }

        # Aggregate invoices by tax rate
        for invoice in invoices:
            is_refund = invoice.move_type == 'out_refund'

            for line in invoice.invoice_line_ids:
                if not line.tax_ids:
                    # No tax = exempt sale
                    if is_refund:
                        sales_by_rate[0]['base'] -= abs(line.price_subtotal)
                    else:
                        sales_by_rate[0]['base'] += line.price_subtotal
                    continue

                # Determine the primary tax rate for base categorization.
                # In Costa Rica IVA, each invoice line typically has exactly
                # one VAT tax. If a line has multiple taxes, we use the
                # highest rate to categorize the base (counted once), and
                # compute each tax's proportional amount individually.
                vat_taxes = []
                for tax in line.tax_ids:
                    rate = int(tax.amount) if tax.amount else 0
                    if rate in sales_by_rate:
                        vat_taxes.append((rate, tax))

                if not vat_taxes:
                    continue

                # Use the highest rate to categorize the base amount (once)
                primary_rate = max(r for r, _ in vat_taxes)
                base_amount = abs(line.price_subtotal)

                if is_refund:
                    if primary_rate in credit_notes:
                        credit_notes[primary_rate]['base'] += base_amount
                elif primary_rate == 0:
                    sales_by_rate[0]['base'] += line.price_subtotal
                else:
                    sales_by_rate[primary_rate]['base'] += line.price_subtotal

                # Compute tax amount per tax (each tax contributes its own rate)
                for rate, tax in vat_taxes:
                    if rate == 0:
                        continue
                    tax_amount = line.price_subtotal * (rate / 100.0)
                    if is_refund:
                        if rate in credit_notes:
                            credit_notes[rate]['tax'] += abs(tax_amount)
                    else:
                        sales_by_rate[rate]['tax'] += tax_amount

        # Assign to fields
        self.sales_13_base = sales_by_rate[13]['base']
        self.sales_13_tax = sales_by_rate[13]['tax']
        self.sales_4_base = sales_by_rate[4]['base']
        self.sales_4_tax = sales_by_rate[4]['tax']
        self.sales_2_base = sales_by_rate[2]['base']
        self.sales_2_tax = sales_by_rate[2]['tax']
        self.sales_1_base = sales_by_rate[1]['base']
        self.sales_1_tax = sales_by_rate[1]['tax']
        self.sales_exempt = sales_by_rate[0]['base']

        self.credit_notes_13_base = credit_notes[13]['base']
        self.credit_notes_13_tax = credit_notes[13]['tax']
        self.credit_notes_4_base = credit_notes[4]['base']
        self.credit_notes_4_tax = credit_notes[4]['tax']
        self.credit_notes_2_base = credit_notes[2]['base']
        self.credit_notes_2_tax = credit_notes[2]['tax']
        self.credit_notes_1_base = credit_notes[1]['base']
        self.credit_notes_1_tax = credit_notes[1]['tax']

    def _calculate_purchases(self):
        """Calculate purchase VAT credit from vendor bills and vendor refunds"""
        self.ensure_one()

        AccountMove = self.env['account.move']

        # Get all vendor bills and vendor refunds in period that are posted
        bills = AccountMove.search([
            ('company_id', '=', self.company_id.id),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.period_id.date_from),
            ('invoice_date', '<=', self.period_id.date_to),
        ])

        # Initialize totals
        purchases_by_rate = {
            13: {'goods': 0.0, 'services': 0.0, 'goods_tax': 0.0, 'services_tax': 0.0},
            4: {'base': 0.0, 'tax': 0.0},
            2: {'base': 0.0, 'tax': 0.0},
            1: {'base': 0.0, 'tax': 0.0},
            0: {'base': 0.0},
        }

        # Aggregate by tax rate
        for bill in bills:
            # Vendor refunds (in_refund) reduce purchase totals
            sign = -1.0 if bill.move_type == 'in_refund' else 1.0

            for line in bill.invoice_line_ids:
                if not line.tax_ids:
                    # No tax = exempt
                    purchases_by_rate[0]['base'] += line.price_subtotal * sign
                    continue

                # Determine tax-specific amounts to avoid double-counting base
                # when a line has multiple taxes
                vat_taxes = []
                for tax in line.tax_ids:
                    rate = int(tax.amount) if tax.amount else 0
                    vat_taxes.append((rate, tax))

                if not vat_taxes:
                    continue

                # Use the highest rate to categorize the base amount (once)
                primary_rate = max(r for r, _ in vat_taxes)
                base_amount = line.price_subtotal * sign

                if primary_rate == 13:
                    # Classify as goods or services using product type
                    if line.product_id and line.product_id.type == 'service':
                        purchases_by_rate[13]['services'] += base_amount
                    else:
                        purchases_by_rate[13]['goods'] += base_amount
                elif primary_rate in (4, 2, 1):
                    purchases_by_rate[primary_rate]['base'] += base_amount
                elif primary_rate == 0:
                    purchases_by_rate[0]['base'] += base_amount

                # Compute tax amount per tax rate
                for rate, tax in vat_taxes:
                    if rate == 0:
                        continue
                    tax_amount = line.price_subtotal * (rate / 100.0) * sign
                    if rate == 13:
                        if line.product_id and line.product_id.type == 'service':
                            purchases_by_rate[13]['services_tax'] += tax_amount
                        else:
                            purchases_by_rate[13]['goods_tax'] += tax_amount
                    elif rate in (4, 2, 1):
                        purchases_by_rate[rate]['tax'] += tax_amount

        # Update fields
        self.purchases_goods_13_base = purchases_by_rate[13]['goods']
        self.purchases_goods_13_tax = purchases_by_rate[13]['goods_tax']
        self.purchases_services_13_base = purchases_by_rate[13]['services']
        self.purchases_services_13_tax = purchases_by_rate[13]['services_tax']

        self.purchases_4_base = purchases_by_rate[4]['base']
        self.purchases_4_tax = purchases_by_rate[4]['tax']

        self.purchases_2_base = purchases_by_rate[2]['base']
        self.purchases_2_tax = purchases_by_rate[2]['tax']

        self.purchases_1_base = purchases_by_rate[1]['base']
        self.purchases_1_tax = purchases_by_rate[1]['tax']

        self.purchases_exempt = purchases_by_rate[0]['base']

    def _get_previous_balance(self):
        """Get VAT balance from previous month to carry forward"""
        self.ensure_one()

        # Find previous month's D-150 report
        prev_month = self.period_id.date_from - relativedelta(months=1)

        # Search for D-150 report from previous month
        prev_report = self.env['l10n_cr.d150.report'].search([
            ('company_id', '=', self.company_id.id),
            ('period_id.report_type', '=', 'd150'),
            ('period_id.year', '=', prev_month.year),
            ('period_id.month', '=', prev_month.month),
            ('state', 'in', ['calculated', 'ready', 'submitted', 'accepted']),
        ], limit=1, order='id desc')

        if prev_report:
            # Carry forward credit to next period
            # If previous had credit (negative net_amount_due), it becomes positive balance
            # If previous had payment due (positive net_amount_due), it's already paid
            if prev_report.net_amount_due < 0:
                self.previous_balance = abs(prev_report.net_amount_due)
            else:
                self.previous_balance = 0.0
        else:
            self.previous_balance = 0.0

    def action_generate_xml(self):
        """Generate D-150 XML for TRIBU-CR submission"""
        self.ensure_one()

        if self.state not in ['calculated', 'ready']:
            raise UserError(_('Report must be calculated before generating XML.'))

        # Use existing XML generator infrastructure
        XMLGenerator = self.env['l10n_cr.tax.report.xml.generator']
        xml_content = XMLGenerator.generate_d150_xml(self)

        self.xml_content = xml_content
        self.state = 'ready'
        self.message_post(body=_('D-150 XML generated successfully'))

        return True

    def action_sign_xml(self):
        """Digitally sign the D-150 XML using company certificate"""
        self.ensure_one()

        if not self.xml_content:
            raise UserError(_('Generate XML before signing.'))

        # Load certificate and private key from company configuration
        cert_manager = self.env['l10n_cr.certificate.manager']
        certificate, private_key = cert_manager.load_certificate_from_company(self.company_id)

        # Sign XML with certificate and private key objects
        XMLSigner = self.env['l10n_cr.xml.signer']
        signed_xml = XMLSigner.sign_xml(
            self.xml_content,
            certificate,
            private_key
        )

        self.xml_signed = signed_xml
        self.message_post(body=_('D-150 XML signed successfully'))

        return True

    def action_submit_to_hacienda(self):
        """Submit signed D-150 to Hacienda TRIBU-CR API"""
        self.ensure_one()

        if not self.xml_signed:
            raise UserError(_('Firme el XML antes de enviar a Hacienda.'))

        try:
            # Use TRIBU-CR API client
            HaciendaAPI = self.env['l10n_cr.hacienda.api']
            result = HaciendaAPI.submit_d150_report(
                report_id=self.id,
                signed_xml=self.xml_signed
            )

            if result.get('success'):
                self.submission_key = result.get('key')
                self.submission_date = fields.Datetime.now()
                self.state = 'submitted'
                self.hacienda_message = result.get('message', _('Enviado exitosamente'))
                self.message_post(body=_('D-150 enviado a Hacienda: %s') % self.submission_key)
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
                report_type='D150'
            )

            estado = result.get('estado', '').lower()

            if estado == 'aceptado':
                self.state = 'accepted'
                self.acceptance_date = fields.Datetime.now()
                self.hacienda_message = result.get('message', _('Aceptado'))
                self.message_post(body=_('D-150 aceptado por Hacienda'))

                # Update period state
                if self.period_id:
                    self.period_id.state = 'accepted'

            elif estado == 'rechazado':
                self.state = 'rejected'
                error_details = result.get('detalle', '')
                errores = result.get('errores', [])
                if errores:
                    error_details += '\n' + '\n'.join([str(e) for e in errores])
                self.hacienda_message = result.get('message', _('Rechazado')) + '\n' + error_details
                self.message_post(body=_('D-150 rechazado: %s') % self.hacienda_message)

            elif estado in ['procesando', 'recibido']:
                # Still processing
                self.hacienda_message = result.get('message', _('En procesamiento'))
                self.message_post(body=_('D-150 en procesamiento'))

            else:
                # Unknown state
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
