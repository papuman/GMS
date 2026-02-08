# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date

_logger = logging.getLogger(__name__)


class TaxReportPeriod(models.Model):
    """
    Tax Reporting Period Management

    Manages period definitions for different Costa Rica tax reports:
    - D-150: Monthly VAT declaration
    - D-101: Annual income tax
    - D-151: Annual informative declaration

    Handles deadline calculations and period validation.
    """
    _name = 'l10n_cr.tax.report.period'
    _description = 'Tax Report Period'
    _order = 'date_from desc'

    name = fields.Char(
        string='Period',
        compute='_compute_name',
        store=True,
        help='Display name for the period (e.g., "D-150 November 2025")'
    )

    report_type = fields.Selection([
        ('d150', 'D-150 VAT Monthly'),
        ('d101', 'D-101 Income Tax Annual'),
        ('d151', 'D-151 Informative Annual'),
        ('d152', 'D-152 Purchase Withholdings'),
        ('d158', 'D-158 Foreign Payments'),
        ('d195', 'D-195 Inactive Declaration'),
    ], string='Report Type', required=True, default='d150')

    year = fields.Integer(
        string='Year',
        required=True,
        default=lambda self: fields.Date.today().year,
        help='Tax year for this period'
    )

    month = fields.Integer(
        string='Month',
        help='Tax month (only for monthly reports like D-150)'
    )

    date_from = fields.Date(
        string='Start Date',
        help='First day of the reporting period'
    )

    date_to = fields.Date(
        string='End Date',
        help='Last day of the reporting period'
    )

    deadline = fields.Date(
        string='Filing Deadline',
        compute='_compute_deadline',
        store=True,
        help='Legal deadline for filing this report with Hacienda'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', required=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    d150_report_id = fields.Many2one(
        'l10n_cr.d150.report',
        string='D-150 Report',
        ondelete='cascade',
        help='Associated D-150 VAT report'
    )

    d101_report_id = fields.Many2one(
        'l10n_cr.d101.report',
        string='D-101 Report',
        ondelete='cascade',
        help='Associated D-101 Income Tax report'
    )

    d151_report_id = fields.Many2one(
        'l10n_cr.d151.report',
        string='D-151 Report',
        ondelete='cascade',
        help='Associated D-151 Informative report'
    )

    notes = fields.Text(
        string='Internal Notes',
        help='Internal notes about this period'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-compute date_from and date_to if not provided"""
        for vals in vals_list:
            # Auto-compute dates if not provided
            if ('date_from' not in vals or 'date_to' not in vals) and 'year' in vals:
                report_type = vals.get('report_type')
                year = vals.get('year')
                month = vals.get('month')

                if report_type == 'd150' and month:
                    # Monthly report: 1st to last day of month
                    vals['date_from'] = date(year, month, 1)
                    vals['date_to'] = date(year, month, 1) + relativedelta(months=1, days=-1)
                elif report_type in ('d101', 'd151'):
                    # Annual report: January 1 to December 31
                    vals['date_from'] = date(year, 1, 1)
                    vals['date_to'] = date(year, 12, 31)

        return super().create(vals_list)

    @api.depends('report_type', 'year', 'month')
    def _compute_name(self):
        """Compute display name based on report type and period"""
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }

        for record in self:
            if record.report_type == 'd150':
                month_name = month_names.get(record.month, '')
                record.name = f"D-150 {month_name} {record.year}"
            elif record.report_type == 'd101':
                record.name = f"D-101 {record.year}"
            elif record.report_type == 'd151':
                record.name = f"D-151 {record.year}"
            elif record.report_type == 'd152':
                record.name = f"D-152 {record.year}"
            elif record.report_type == 'd158':
                record.name = f"D-158 {record.year}"
            elif record.report_type == 'd195':
                record.name = f"D-195 {record.year}"
            else:
                record.name = f"{record.report_type.upper()} {record.year}"

    @api.depends('report_type', 'year', 'month', 'date_to')
    def _compute_deadline(self):
        """
        Compute filing deadline based on report type and Costa Rica regulations

        D-150 (Monthly VAT): 15th of following month
        D-101 (Annual Income): March 15 of following year
        D-151 (Informative): April 15 of following year
        """
        for record in self:
            if record.report_type == 'd150' and record.month and record.year:
                # D-150: 15th of following month
                next_month = date(record.year, record.month, 1) + relativedelta(months=1)
                record.deadline = date(next_month.year, next_month.month, 15)

            elif record.report_type == 'd101' and record.year:
                # D-101: March 15 of following year
                record.deadline = date(record.year + 1, 3, 15)

            elif record.report_type == 'd151' and record.year:
                # D-151: April 15 of following year
                record.deadline = date(record.year + 1, 4, 15)

            elif record.date_to:
                # Default: 15 days after period end
                record.deadline = record.date_to + relativedelta(days=15)
            else:
                record.deadline = fields.Date.today()

    @api.constrains('year', 'month', 'report_type')
    def _check_period_unique(self):
        """Ensure no duplicate periods for same company and report type"""
        for record in self:
            domain = [
                ('company_id', '=', record.company_id.id),
                ('report_type', '=', record.report_type),
                ('year', '=', record.year),
                ('id', '!=', record.id),
            ]

            if record.report_type == 'd150':
                domain.append(('month', '=', record.month))

            if self.search_count(domain) > 0:
                if record.report_type == 'd150':
                    raise ValidationError(_(
                        'A period for %s %s/%s already exists for this company.'
                    ) % (record.report_type.upper(), record.month, record.year))
                else:
                    raise ValidationError(_(
                        'A period for %s %s already exists for this company.'
                    ) % (record.report_type.upper(), record.year))

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Validate date range"""
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError(_('Start date must be before end date.'))

    @api.onchange('year', 'month', 'report_type')
    def _onchange_period(self):
        """Auto-fill date range based on year/month"""
        if self.report_type == 'd150' and self.year and self.month:
            # Monthly period
            self.date_from = date(self.year, self.month, 1)
            last_day = date(self.year, self.month, 1) + relativedelta(months=1, days=-1)
            self.date_to = last_day

        elif self.report_type in ['d101', 'd151', 'd152', 'd158'] and self.year:
            # Annual period
            self.date_from = date(self.year, 1, 1)
            self.date_to = date(self.year, 12, 31)

    def action_create_report(self):
        """Create associated tax report based on type"""
        self.ensure_one()

        if self.report_type == 'd150':
            if not self.d150_report_id:
                d150 = self.env['l10n_cr.d150.report'].create({
                    'period_id': self.id,
                })
                self.d150_report_id = d150.id

            return {
                'type': 'ir.actions.act_window',
                'name': 'D-150 VAT Report',
                'res_model': 'l10n_cr.d150.report',
                'res_id': self.d150_report_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

        elif self.report_type == 'd101':
            if not self.d101_report_id:
                d101 = self.env['l10n_cr.d101.report'].create({
                    'period_id': self.id,
                })
                self.d101_report_id = d101.id

            return {
                'type': 'ir.actions.act_window',
                'name': 'D-101 Income Tax Report',
                'res_model': 'l10n_cr.d101.report',
                'res_id': self.d101_report_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

        elif self.report_type == 'd151':
            if not self.d151_report_id:
                d151 = self.env['l10n_cr.d151.report'].create({
                    'period_id': self.id,
                })
                self.d151_report_id = d151.id

            return {
                'type': 'ir.actions.act_window',
                'name': 'D-151 Informative Report',
                'res_model': 'l10n_cr.d151.report',
                'res_id': self.d151_report_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

        return True

    @api.model
    def create_monthly_period(self, year=None, month=None):
        """
        Helper method to create D-150 monthly period

        Args:
            year: Year (defaults to current year)
            month: Month (defaults to previous month)

        Returns:
            tax.report.period record
        """
        if not year or not month:
            today = fields.Date.today()
            last_month = today - relativedelta(months=1)
            year = last_month.year
            month = last_month.month

        date_from = date(year, month, 1)
        date_to = date(year, month, 1) + relativedelta(months=1, days=-1)

        return self.create({
            'report_type': 'd150',
            'year': year,
            'month': month,
            'date_from': date_from,
            'date_to': date_to,
        })

    def is_overdue(self):
        """Check if filing deadline has passed"""
        self.ensure_one()
        return fields.Date.today() > self.deadline and self.state not in ['submitted', 'accepted']

    # =====================================================
    # CRON JOBS
    # =====================================================

    @api.model
    def _cron_auto_generate_d150(self):
        """
        Cron job: Auto-generate D-150 monthly reports on 1st of month

        Runs daily but only creates on 1st of month.
        Creates period and D-150 report for previous month.
        Sends notification to accountants.
        """
        today = fields.Date.today()

        # Only run on 1st of month
        if today.day != 1:
            return

        # Get previous month
        last_month = today - relativedelta(months=1)
        year = last_month.year
        month = last_month.month

        # Check each company
        companies = self.env['res.company'].search([])

        for company in companies:
            # Check if period already exists
            existing = self.search([
                ('company_id', '=', company.id),
                ('report_type', '=', 'd150'),
                ('year', '=', year),
                ('month', '=', month),
            ])

            if existing:
                _logger.info(f'D-150 period {year}/{month} already exists for {company.name}')
                continue

            # Create period
            period = self.create({
                'report_type': 'd150',
                'year': year,
                'month': month,
                'company_id': company.id,
            })

            # Create D-150 report
            d150 = self.env['l10n_cr.d150.report'].create({
                'period_id': period.id,
                'company_id': company.id,
            })

            period.d150_report_id = d150.id

            # Auto-calculate if possible
            try:
                d150.action_calculate()
                _logger.info(f'Auto-generated and calculated D-150 for {company.name} - {year}/{month}')

                # Send notification to accountants
                self._notify_accountants_d150_ready(period)

            except Exception as e:
                _logger.warning(f'Could not auto-calculate D-150 for {company.name}: {str(e)}')

    @api.model
    def _cron_check_overdue_d150(self):
        """
        Cron job: Check for overdue D-150 reports and send reminders

        Runs daily.
        Finds D-150 periods past deadline that aren't submitted.
        Sends reminder emails to accountants.
        """
        today = fields.Date.today()

        # Find overdue periods
        overdue_periods = self.search([
            ('report_type', '=', 'd150'),
            ('deadline', '<', today),
            ('state', 'in', ['draft', 'calculated']),
        ])

        for period in overdue_periods:
            days_overdue = (today - period.deadline).days

            # Send reminder
            self._notify_accountants_d150_overdue(period, days_overdue)

            _logger.warning(
                f'D-150 {period.name} is {days_overdue} days overdue for {period.company_id.name}'
            )

    def _notify_accountants_d150_ready(self, period):
        """
        Send notification that D-150 is ready for review

        Args:
            period: tax.report.period record
        """
        # Get accountant group users
        accountant_group = self.env.ref('account.group_account_manager', raise_if_not_found=False)
        if not accountant_group:
            return

        users = accountant_group.users.filtered(
            lambda u: u.company_id == period.company_id
        )

        if not users:
            return

        # Create activity for each accountant
        for user in users:
            period.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary=_('D-150 VAT Report Ready for Review'),
                note=_(
                    'The D-150 monthly VAT report for %s has been automatically generated and calculated. '
                    'Please review and submit before the deadline: %s'
                ) % (period.name, period.deadline.strftime('%Y-%m-%d')),
            )

    def _notify_accountants_d150_overdue(self, period, days_overdue):
        """
        Send notification that D-150 is overdue

        Args:
            period: tax.report.period record
            days_overdue: Number of days past deadline
        """
        # Get accountant group users
        accountant_group = self.env.ref('account.group_account_manager', raise_if_not_found=False)
        if not accountant_group:
            return

        users = accountant_group.users.filtered(
            lambda u: u.company_id == period.company_id
        )

        if not users:
            return

        # Create urgent activity
        for user in users:
            period.activity_schedule(
                'mail.mail_activity_data_warning',
                user_id=user.id,
                summary=_('URGENT: D-150 VAT Report Overdue'),
                note=_(
                    'The D-150 monthly VAT report for %s is %d days overdue! '
                    'Deadline was: %s. Please submit immediately to avoid penalties.'
                ) % (period.name, days_overdue, period.deadline.strftime('%Y-%m-%d')),
            )
