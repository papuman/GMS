# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class D101IncomeTaxReport(models.Model):
    """
    D-101 Annual Income Tax Declaration

    Costa Rica annual income tax report (Renta Anual).
    Filing deadline: March 15 of following year.

    Calculates:
    - Gross income (from sales/invoices)
    - Deductible expenses (from purchases/bills)
    - Taxable income
    - Income tax owed
    """
    _name = 'l10n_cr.d101.report'
    _description = 'D-101 Annual Income Tax Report'
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
    # SECTION 1: GROSS INCOME (Ingresos Brutos)
    # =====================================================

    sales_revenue = fields.Monetary(
        string='Sales Revenue',
        currency_field='currency_id',
        help='Total revenue from sales of goods/services'
    )

    other_income = fields.Monetary(
        string='Other Income',
        currency_field='currency_id',
        help='Interest, dividends, rental income, etc.'
    )

    total_gross_income = fields.Monetary(
        string='Total Gross Income',
        compute='_compute_gross_income',
        store=True,
        currency_field='currency_id',
        help='Sum of all income'
    )

    # =====================================================
    # SECTION 2: DEDUCTIBLE EXPENSES (Gastos Deducibles)
    # =====================================================

    cost_of_goods_sold = fields.Monetary(
        string='Cost of Goods Sold',
        currency_field='currency_id',
        help='Direct costs of goods sold'
    )

    operating_expenses = fields.Monetary(
        string='Operating Expenses',
        currency_field='currency_id',
        help='Salaries, rent, utilities, marketing, etc.'
    )

    depreciation = fields.Monetary(
        string='Depreciation',
        currency_field='currency_id',
        help='Depreciation of fixed assets'
    )

    financial_expenses = fields.Monetary(
        string='Financial Expenses',
        currency_field='currency_id',
        help='Interest on loans, bank fees'
    )

    other_deductible_expenses = fields.Monetary(
        string='Other Deductible Expenses',
        currency_field='currency_id',
        help='Other tax-deductible expenses'
    )

    total_deductible_expenses = fields.Monetary(
        string='Total Deductible Expenses',
        compute='_compute_deductible_expenses',
        store=True,
        currency_field='currency_id',
        help='Sum of all deductible expenses'
    )

    # =====================================================
    # SECTION 3: TAXABLE INCOME (Renta Neta Gravable)
    # =====================================================

    net_income_before_adjustments = fields.Monetary(
        string='Net Income Before Adjustments',
        compute='_compute_taxable_income',
        store=True,
        currency_field='currency_id',
        help='Gross Income - Deductible Expenses'
    )

    tax_loss_carryforward = fields.Monetary(
        string='Tax Loss Carryforward',
        currency_field='currency_id',
        default=0.0,
        help='Losses from previous years (max 3 years)'
    )

    non_deductible_expenses = fields.Monetary(
        string='Non-Deductible Expenses',
        currency_field='currency_id',
        default=0.0,
        help='Expenses rejected by Hacienda'
    )

    taxable_income = fields.Monetary(
        string='Taxable Income',
        compute='_compute_taxable_income',
        store=True,
        currency_field='currency_id',
        help='Final taxable income after adjustments'
    )

    # =====================================================
    # SECTION 4: INCOME TAX CALCULATION
    # =====================================================

    # Costa Rica income tax rates (progressive):
    # ₡0 - ₡4,000,000: 0%
    # ₡4,000,001 - ₡8,000,000: 10%
    # ₡8,000,001 - ₡16,000,000: 15%
    # ₡16,000,001 - ₡48,000,000: 20%
    # Over ₡48,000,000: 25%

    tax_bracket_0_amount = fields.Monetary(
        string='Tax 0% Bracket',
        compute='_compute_income_tax',
        store=True,
        currency_field='currency_id',
        help='Income in 0% bracket (₡0 - ₡4M)'
    )

    tax_bracket_10_amount = fields.Monetary(
        string='Tax 10% Bracket',
        compute='_compute_income_tax',
        store=True,
        currency_field='currency_id',
        help='Income in 10% bracket (₡4M - ₡8M)'
    )

    tax_bracket_15_amount = fields.Monetary(
        string='Tax 15% Bracket',
        compute='_compute_income_tax',
        store=True,
        currency_field='currency_id',
        help='Income in 15% bracket (₡8M - ₡16M)'
    )

    tax_bracket_20_amount = fields.Monetary(
        string='Tax 20% Bracket',
        compute='_compute_income_tax',
        store=True,
        currency_field='currency_id',
        help='Income in 20% bracket (₡16M - ₡48M)'
    )

    tax_bracket_25_amount = fields.Monetary(
        string='Tax 25% Bracket',
        compute='_compute_income_tax',
        store=True,
        currency_field='currency_id',
        help='Income in 25% bracket (over ₡48M)'
    )

    total_income_tax = fields.Monetary(
        string='Total Income Tax',
        compute='_compute_income_tax',
        store=True,
        currency_field='currency_id',
        help='Total tax calculated from progressive brackets'
    )

    # =====================================================
    # SECTION 5: TAX CREDITS & PAYMENTS
    # =====================================================

    advance_payments = fields.Monetary(
        string='Advance Payments',
        currency_field='currency_id',
        default=0.0,
        help='Quarterly advance payments made during the year'
    )

    withholdings = fields.Monetary(
        string='Tax Withholdings',
        currency_field='currency_id',
        default=0.0,
        help='Tax withheld at source by customers'
    )

    tax_credits = fields.Monetary(
        string='Other Tax Credits',
        currency_field='currency_id',
        default=0.0,
        help='Investment incentives, donations, etc.'
    )

    total_credits = fields.Monetary(
        string='Total Credits',
        compute='_compute_final_amount',
        store=True,
        currency_field='currency_id',
        help='Sum of advance payments, withholdings, and credits'
    )

    # =====================================================
    # SECTION 6: FINAL SETTLEMENT
    # =====================================================

    net_tax_due = fields.Monetary(
        string='Net Tax Due',
        compute='_compute_final_amount',
        store=True,
        currency_field='currency_id',
        help='Tax owed after credits (positive) or refund (negative)'
    )

    amount_to_pay = fields.Monetary(
        string='Amount to Pay',
        compute='_compute_final_amount',
        store=True,
        currency_field='currency_id',
        help='Final amount owed to Hacienda'
    )

    refund_amount = fields.Monetary(
        string='Refund Amount',
        compute='_compute_final_amount',
        store=True,
        currency_field='currency_id',
        help='Amount to be refunded by Hacienda'
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
        string='D-101 XML',
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

    @api.depends('sales_revenue', 'other_income')
    def _compute_gross_income(self):
        """Calculate total gross income"""
        for record in self:
            record.total_gross_income = record.sales_revenue + record.other_income

    @api.depends(
        'cost_of_goods_sold', 'operating_expenses', 'depreciation',
        'financial_expenses', 'other_deductible_expenses'
    )
    def _compute_deductible_expenses(self):
        """Calculate total deductible expenses"""
        for record in self:
            record.total_deductible_expenses = (
                record.cost_of_goods_sold +
                record.operating_expenses +
                record.depreciation +
                record.financial_expenses +
                record.other_deductible_expenses
            )

    @api.depends(
        'total_gross_income', 'total_deductible_expenses',
        'tax_loss_carryforward', 'non_deductible_expenses'
    )
    def _compute_taxable_income(self):
        """Calculate taxable income after adjustments"""
        for record in self:
            record.net_income_before_adjustments = (
                record.total_gross_income - record.total_deductible_expenses
            )

            # Apply adjustments
            record.taxable_income = (
                record.net_income_before_adjustments -
                record.tax_loss_carryforward +
                record.non_deductible_expenses
            )

            # Cannot be negative
            if record.taxable_income < 0:
                record.taxable_income = 0

    @api.depends('taxable_income', 'total_gross_income')
    def _compute_income_tax(self):
        """
        Calculate income tax using Costa Rica tax rules (2025)

        Legal Entities with Gross Income > ₡119,626,000:
        - Flat 30% rate on taxable income

        Legal Entities with Gross Income ≤ ₡119,626,000 (Progressive brackets):
        - ₡0 - ₡4,000,000: 0%
        - ₡4,000,001 - ₡8,000,000: 10%
        - ₡8,000,001 - ₡16,000,000: 15%
        - ₡16,000,001 - ₡48,000,000: 20%
        - Over ₡48,000,000: 25%
        """
        for record in self:
            taxable = record.taxable_income
            gross_income = record.total_gross_income
            tax = 0.0

            # Threshold for flat 30% rate
            FLAT_RATE_THRESHOLD = 119626000.0

            if gross_income > FLAT_RATE_THRESHOLD:
                # Flat 30% rate for large entities
                tax = taxable * 0.30

                # Clear bracket amounts (not used in flat rate)
                record.tax_bracket_0_amount = 0.0
                record.tax_bracket_10_amount = 0.0
                record.tax_bracket_15_amount = 0.0
                record.tax_bracket_20_amount = 0.0
                record.tax_bracket_25_amount = 0.0
            else:
                # Progressive brackets for smaller entities
                brackets = [
                    (4000000, 0.0),   # 0% up to 4M
                    (8000000, 0.10),  # 10% from 4M to 8M
                    (16000000, 0.15), # 15% from 8M to 16M
                    (48000000, 0.20), # 20% from 16M to 48M
                    (float('inf'), 0.25), # 25% over 48M
                ]

                # Calculate tax per bracket
                previous_limit = 0
                bracket_amounts = []

                for limit, rate in brackets:
                    if taxable > previous_limit:
                        # Amount in this bracket
                        bracket_income = min(taxable, limit) - previous_limit
                        bracket_tax = bracket_income * rate
                        tax += bracket_tax
                        bracket_amounts.append((bracket_income, bracket_tax))
                    else:
                        bracket_amounts.append((0, 0))

                    previous_limit = limit

                # Assign bracket amounts
                record.tax_bracket_0_amount = bracket_amounts[0][0]
                record.tax_bracket_10_amount = bracket_amounts[1][0]
                record.tax_bracket_15_amount = bracket_amounts[2][0]
                record.tax_bracket_20_amount = bracket_amounts[3][0]
                record.tax_bracket_25_amount = bracket_amounts[4][0]

            record.total_income_tax = tax

    @api.depends('total_income_tax', 'advance_payments', 'withholdings', 'tax_credits')
    def _compute_final_amount(self):
        """Calculate final amount to pay or refund"""
        for record in self:
            record.total_credits = (
                record.advance_payments +
                record.withholdings +
                record.tax_credits
            )

            record.net_tax_due = record.total_income_tax - record.total_credits

            if record.net_tax_due > 0:
                record.amount_to_pay = record.net_tax_due
                record.refund_amount = 0.0
            else:
                record.amount_to_pay = 0.0
                record.refund_amount = abs(record.net_tax_due)

    # =====================================================
    # ACTIONS
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate sequential name"""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_cr.d101.report') or _('New')
        return super().create(vals_list)

    def action_calculate(self):
        """
        Calculate D-101 amounts from accounting data

        Aggregates all income and expenses for the fiscal year.
        """
        self.ensure_one()

        if not self.period_id:
            raise UserError(_('Period is required to calculate the report.'))

        # Get all customer invoices (sales revenue)
        sales_invoices = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.period_id.date_from),
            ('invoice_date', '<=', self.period_id.date_to),
        ])

        # Calculate sales revenue (subtract refunds)
        sales_revenue = sum(
            inv.amount_untaxed if inv.move_type == 'out_invoice' else -inv.amount_untaxed
            for inv in sales_invoices
        )
        self.sales_revenue = sales_revenue

        # Get vendor bills (expenses)
        vendor_bills = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id),
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.period_id.date_from),
            ('invoice_date', '<=', self.period_id.date_to),
        ])

        # WARNING: Simplified calculation — all vendor bills treated as operating expenses.
        # For accurate D-101 filing, manual categorization by account type is required:
        # - Cost of Goods Sold (COGS) → costo_ventas
        # - Operating Expenses → gastos_operativos
        # - Depreciation → depreciacion
        # - Financial Expenses → gastos_financieros
        _logger.warning(
            'D-101 for %s: Using simplified expense calculation. '
            'All vendor bills treated as operating expenses. '
            'Manual adjustment may be required for accurate filing.',
            self.name
        )
        total_expenses = sum(bill.amount_untaxed for bill in vendor_bills)
        self.operating_expenses = total_expenses

        self.state = 'calculated'
        self.message_post(body=_('D-101 calculated successfully'))

        return True

    def action_generate_xml(self):
        """Generate D-101 XML for TRIBU-CR submission"""
        self.ensure_one()

        if self.state not in ['calculated', 'ready']:
            raise UserError(_('Report must be calculated before generating XML.'))

        # Use XML generator
        XMLGenerator = self.env['l10n_cr.tax.report.xml.generator']
        xml_content = XMLGenerator.generate_d101_xml(self)

        self.xml_content = xml_content
        self.state = 'ready'
        self.message_post(body=_('D-101 XML generated successfully'))

        return True

    def action_sign_xml(self):
        """Digitally sign the D-101 XML"""
        self.ensure_one()

        if not self.xml_content:
            raise UserError(_('Generate XML before signing.'))

        cert_manager = self.env['l10n_cr.certificate.manager']
        certificate, private_key = cert_manager.load_certificate_from_company(self.company_id)
        if not certificate:
            raise UserError(_('Certificate not configured. Please upload certificate in Company settings.'))
        XMLSigner = self.env['l10n_cr.xml.signer']
        signed_xml = XMLSigner.sign_xml(self.xml_content, certificate, private_key)

        self.xml_signed = signed_xml
        self.message_post(body=_('D-101 XML signed successfully'))

        return True

    def action_submit_to_hacienda(self):
        """Submit signed D-101 to Hacienda"""
        self.ensure_one()

        if not self.xml_signed:
            raise UserError(_('Firme el XML antes de enviar a Hacienda.'))

        try:
            HaciendaAPI = self.env['l10n_cr.hacienda.api']
            result = HaciendaAPI.submit_d101_report(
                report_id=self.id,
                signed_xml=self.xml_signed
            )

            if result.get('success'):
                self.submission_key = result.get('key')
                self.submission_date = fields.Datetime.now()
                self.state = 'submitted'
                self.hacienda_message = result.get('message', _('Enviado exitosamente'))
                self.message_post(body=_('D-101 enviado a Hacienda: %s') % self.submission_key)
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
                report_type='D101'
            )

            estado = result.get('estado', '').lower()

            if estado == 'aceptado':
                self.state = 'accepted'
                self.acceptance_date = fields.Datetime.now()
                self.hacienda_message = result.get('message', _('Aceptado'))
                self.message_post(body=_('D-101 aceptado por Hacienda'))
                if self.period_id:
                    self.period_id.state = 'accepted'

            elif estado == 'rechazado':
                self.state = 'rejected'
                error_details = result.get('detalle', '')
                errores = result.get('errores', [])
                if errores:
                    error_details += '\n' + '\n'.join([str(e) for e in errores])
                self.hacienda_message = result.get('message', _('Rechazado')) + '\n' + error_details
                self.message_post(body=_('D-101 rechazado: %s') % self.hacienda_message)

            elif estado in ['procesando', 'recibido']:
                self.hacienda_message = result.get('message', _('En procesamiento'))
                self.message_post(body=_('D-101 en procesamiento'))

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
