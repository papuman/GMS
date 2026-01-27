# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoiceAnalyticsDashboard(models.Model):
    """Analytics Dashboard for E-Invoice KPIs and Metrics."""

    _name = 'l10n_cr.einvoice.analytics.dashboard'
    _description = 'E-Invoice Analytics Dashboard'

    name = fields.Char(string='Dashboard Name', default='E-Invoice Analytics')

    @api.model
    def get_kpis(self, date_from=None, date_to=None):
        """
        Get real-time KPIs for the dashboard.

        Args:
            date_from: Start date for filtering (default: 30 days ago)
            date_to: End date for filtering (default: today)

        Returns:
            dict: Dictionary containing all KPI values
        """
        # Default date range: last 30 days
        if not date_from:
            date_from = fields.Datetime.to_string(
                datetime.now() - timedelta(days=30)
            )
        if not date_to:
            date_to = fields.Datetime.to_string(datetime.now())

        # Build domain for date filtering
        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ]

        # Get all documents in range
        Document = self.env['l10n_cr.einvoice.document']
        all_docs = Document.search(domain)

        # Total counts by status
        total_count = len(all_docs)
        draft_count = len(all_docs.filtered(lambda x: x.state == 'draft'))
        generated_count = len(all_docs.filtered(lambda x: x.state == 'generated'))
        signed_count = len(all_docs.filtered(lambda x: x.state == 'signed'))
        submitted_count = len(all_docs.filtered(lambda x: x.state == 'submitted'))
        accepted_count = len(all_docs.filtered(lambda x: x.state == 'accepted'))
        rejected_count = len(all_docs.filtered(lambda x: x.state == 'rejected'))
        error_count = len(all_docs.filtered(lambda x: x.state == 'error'))

        # Acceptance rate calculation
        submitted_total = submitted_count + accepted_count + rejected_count
        acceptance_rate = (accepted_count / submitted_total * 100) if submitted_total > 0 else 0
        rejection_rate = (rejected_count / submitted_total * 100) if submitted_total > 0 else 0

        # Revenue by document type
        fe_docs = all_docs.filtered(lambda x: x.document_type == 'FE')
        te_docs = all_docs.filtered(lambda x: x.document_type == 'TE')
        nc_docs = all_docs.filtered(lambda x: x.document_type == 'NC')
        nd_docs = all_docs.filtered(lambda x: x.document_type == 'ND')

        revenue_fe = sum(fe_docs.mapped('amount_total'))
        revenue_te = sum(te_docs.mapped('amount_total'))
        revenue_nc = sum(nc_docs.mapped('amount_total'))
        revenue_nd = sum(nd_docs.mapped('amount_total'))
        total_revenue = revenue_fe + revenue_te + revenue_nd - revenue_nc

        # Average processing time (submission to acceptance)
        accepted_docs = all_docs.filtered(
            lambda x: x.state == 'accepted' and x.hacienda_submission_date and x.hacienda_acceptance_date
        )
        if accepted_docs:
            processing_times = [
                (doc.hacienda_acceptance_date - doc.hacienda_submission_date).total_seconds() / 60
                for doc in accepted_docs
            ]
            avg_processing_time = sum(processing_times) / len(processing_times)
        else:
            avg_processing_time = 0

        # Email delivery rate
        email_sent_count = len(all_docs.filtered(lambda x: x.email_sent))
        email_eligible_count = len(all_docs.filtered(lambda x: x.state == 'accepted'))
        email_delivery_rate = (email_sent_count / email_eligible_count * 100) if email_eligible_count > 0 else 0

        # Offline queue status (POS)
        OfflineQueue = self.env['l10n_cr.pos.offline.queue']
        offline_pending = OfflineQueue.search_count([
            ('state', '=', 'pending'),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ])
        offline_processing = OfflineQueue.search_count([
            ('state', '=', 'processing'),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ])
        offline_completed = OfflineQueue.search_count([
            ('state', '=', 'completed'),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ])
        offline_failed = OfflineQueue.search_count([
            ('state', '=', 'failed'),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ])

        # Retry queue status
        RetryQueue = self.env['l10n_cr.einvoice.retry.queue']
        retry_pending = RetryQueue.search_count([
            ('state', '=', 'pending'),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ])
        retry_processing = RetryQueue.search_count([
            ('state', '=', 'processing'),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ])
        retry_completed = RetryQueue.search_count([
            ('state', '=', 'completed'),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ])
        retry_failed = RetryQueue.search_count([
            ('state', '=', 'failed'),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ])

        return {
            # Date range
            'date_from': date_from,
            'date_to': date_to,

            # Total counts
            'total_invoices': total_count,
            'draft_count': draft_count,
            'generated_count': generated_count,
            'signed_count': signed_count,
            'submitted_count': submitted_count,
            'accepted_count': accepted_count,
            'rejected_count': rejected_count,
            'error_count': error_count,

            # Rates
            'acceptance_rate': round(acceptance_rate, 2),
            'rejection_rate': round(rejection_rate, 2),
            'email_delivery_rate': round(email_delivery_rate, 2),

            # Document type counts
            'fe_count': len(fe_docs),
            'te_count': len(te_docs),
            'nc_count': len(nc_docs),
            'nd_count': len(nd_docs),

            # Revenue
            'total_revenue': total_revenue,
            'revenue_fe': revenue_fe,
            'revenue_te': revenue_te,
            'revenue_nc': revenue_nc,
            'revenue_nd': revenue_nd,

            # Performance
            'avg_processing_time_minutes': round(avg_processing_time, 2),
            'email_sent_count': email_sent_count,
            'email_eligible_count': email_eligible_count,

            # Queue status
            'offline_pending': offline_pending,
            'offline_processing': offline_processing,
            'offline_completed': offline_completed,
            'offline_failed': offline_failed,
            'retry_pending': retry_pending,
            'retry_processing': retry_processing,
            'retry_completed': retry_completed,
            'retry_failed': retry_failed,
        }

    @api.model
    def get_invoice_trend_data(self, date_from=None, date_to=None, group_by='day'):
        """
        Get invoice trend data for charts.

        Args:
            date_from: Start date
            date_to: End date
            group_by: 'day', 'week', or 'month'

        Returns:
            list: List of data points for trend chart
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=30)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        # SQL query for efficient aggregation
        query = """
            SELECT
                DATE(create_date) as date,
                COUNT(*) as count,
                state,
                document_type
            FROM l10n_cr_einvoice_document
            WHERE create_date >= %s AND create_date <= %s
            GROUP BY DATE(create_date), state, document_type
            ORDER BY date
        """

        self.env.cr.execute(query, (date_from, date_to))
        results = self.env.cr.dictfetchall()

        # Group data by date
        data_by_date = {}
        for row in results:
            date_key = row['date'].strftime('%Y-%m-%d')
            if date_key not in data_by_date:
                data_by_date[date_key] = {
                    'date': date_key,
                    'total': 0,
                    'accepted': 0,
                    'rejected': 0,
                    'pending': 0,
                    'fe': 0,
                    'te': 0,
                    'nc': 0,
                    'nd': 0,
                }

            data_by_date[date_key]['total'] += row['count']

            if row['state'] == 'accepted':
                data_by_date[date_key]['accepted'] += row['count']
            elif row['state'] == 'rejected':
                data_by_date[date_key]['rejected'] += row['count']
            elif row['state'] in ['draft', 'generated', 'signed', 'submitted']:
                data_by_date[date_key]['pending'] += row['count']

            if row['document_type'] == 'FE':
                data_by_date[date_key]['fe'] += row['count']
            elif row['document_type'] == 'TE':
                data_by_date[date_key]['te'] += row['count']
            elif row['document_type'] == 'NC':
                data_by_date[date_key]['nc'] += row['count']
            elif row['document_type'] == 'ND':
                data_by_date[date_key]['nd'] += row['count']

        return list(data_by_date.values())

    @api.model
    def get_revenue_trend_data(self, date_from=None, date_to=None):
        """
        Get revenue trend data for charts.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            list: List of revenue data points
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=30)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        query = """
            SELECT
                DATE(d.create_date) as date,
                d.document_type,
                SUM(m.amount_total) as revenue
            FROM l10n_cr_einvoice_document d
            JOIN account_move m ON d.move_id = m.id
            WHERE d.create_date >= %s AND d.create_date <= %s
                AND d.state = 'accepted'
            GROUP BY DATE(d.create_date), d.document_type
            ORDER BY date
        """

        self.env.cr.execute(query, (date_from, date_to))
        results = self.env.cr.dictfetchall()

        # Group by date
        data_by_date = {}
        for row in results:
            date_key = row['date'].strftime('%Y-%m-%d')
            if date_key not in data_by_date:
                data_by_date[date_key] = {
                    'date': date_key,
                    'total': 0,
                    'fe': 0,
                    'te': 0,
                    'nc': 0,
                    'nd': 0,
                }

            revenue = float(row['revenue'] or 0)

            if row['document_type'] == 'FE':
                data_by_date[date_key]['fe'] += revenue
                data_by_date[date_key]['total'] += revenue
            elif row['document_type'] == 'TE':
                data_by_date[date_key]['te'] += revenue
                data_by_date[date_key]['total'] += revenue
            elif row['document_type'] == 'NC':
                data_by_date[date_key]['nc'] += revenue
                data_by_date[date_key]['total'] -= revenue
            elif row['document_type'] == 'ND':
                data_by_date[date_key]['nd'] += revenue
                data_by_date[date_key]['total'] += revenue

        return list(data_by_date.values())

    @api.model
    def get_top_customers(self, date_from=None, date_to=None, limit=10):
        """
        Get top customers by revenue.

        Args:
            date_from: Start date
            date_to: End date
            limit: Number of top customers to return

        Returns:
            list: List of top customers with revenue
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=30)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        query = """
            SELECT
                p.id as partner_id,
                p.name as customer_name,
                COUNT(d.id) as invoice_count,
                SUM(m.amount_total) as total_revenue
            FROM l10n_cr_einvoice_document d
            JOIN account_move m ON d.move_id = m.id
            JOIN res_partner p ON m.partner_id = p.id
            WHERE d.create_date >= %s AND d.create_date <= %s
                AND d.state = 'accepted'
            GROUP BY p.id, p.name
            ORDER BY total_revenue DESC
            LIMIT %s
        """

        self.env.cr.execute(query, (date_from, date_to, limit))
        results = self.env.cr.dictfetchall()

        return [{
            'partner_id': row['partner_id'],
            'customer_name': row['customer_name'],
            'invoice_count': row['invoice_count'],
            'total_revenue': float(row['total_revenue'] or 0),
        } for row in results]

    @api.model
    def get_payment_method_breakdown(self, date_from=None, date_to=None):
        """
        Get payment method breakdown for charts.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            list: Payment method distribution
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=30)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        query = """
            SELECT
                pm.name as payment_method,
                pm.code as payment_code,
                COUNT(d.id) as count,
                SUM(m.amount_total) as total_amount
            FROM l10n_cr_einvoice_document d
            JOIN account_move m ON d.move_id = m.id
            LEFT JOIN account_move_payment_method_rel pmr ON m.id = pmr.move_id
            LEFT JOIN l10n_cr_payment_method pm ON pmr.payment_method_id = pm.id
            WHERE d.create_date >= %s AND d.create_date <= %s
                AND d.state = 'accepted'
            GROUP BY pm.name, pm.code
            ORDER BY total_amount DESC
        """

        self.env.cr.execute(query, (date_from, date_to))
        results = self.env.cr.dictfetchall()

        return [{
            'payment_method': row['payment_method'] or 'No especificado',
            'payment_code': row['payment_code'] or 'N/A',
            'count': row['count'],
            'total_amount': float(row['total_amount'] or 0),
        } for row in results]

    @api.model
    def get_tax_collection_data(self, date_from=None, date_to=None):
        """
        Get tax collection data (IVA).

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Tax collection summary
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=30)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        query = """
            SELECT
                DATE(d.create_date) as date,
                SUM(m.amount_tax) as tax_amount,
                SUM(m.amount_untaxed) as untaxed_amount,
                SUM(m.amount_total) as total_amount
            FROM l10n_cr_einvoice_document d
            JOIN account_move m ON d.move_id = m.id
            WHERE d.create_date >= %s AND d.create_date <= %s
                AND d.state = 'accepted'
                AND d.document_type IN ('FE', 'TE', 'ND')
            GROUP BY DATE(d.create_date)
            ORDER BY date
        """

        self.env.cr.execute(query, (date_from, date_to))
        results = self.env.cr.dictfetchall()

        trend_data = []
        total_tax = 0
        total_untaxed = 0

        for row in results:
            tax_amount = float(row['tax_amount'] or 0)
            untaxed_amount = float(row['untaxed_amount'] or 0)

            trend_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'tax_amount': tax_amount,
                'untaxed_amount': untaxed_amount,
                'total_amount': float(row['total_amount'] or 0),
            })

            total_tax += tax_amount
            total_untaxed += untaxed_amount

        return {
            'total_tax_collected': total_tax,
            'total_untaxed': total_untaxed,
            'trend_data': trend_data,
        }

    # ========== Automated Report Methods ==========

    @api.model
    def send_daily_summary_email(self):
        """Send daily summary email to administrators."""
        _logger.info("Sending daily e-invoice summary report...")

        # Get KPIs for yesterday
        yesterday = fields.Date.today() - timedelta(days=1)
        date_from = fields.Date.to_string(yesterday)
        date_to = fields.Date.to_string(yesterday)

        kpis = self.get_kpis(date_from, date_to)

        # Get admin users
        admin_users = self.env.ref('base.group_system').users

        # Prepare email
        subject = f"Resumen Diario E-Invoice - {yesterday.strftime('%d/%m/%Y')}"
        body = f"""
        <h2>Resumen Diario de Facturación Electrónica</h2>
        <p><strong>Fecha:</strong> {yesterday.strftime('%d de %B de %Y')}</p>

        <h3>Métricas Clave</h3>
        <ul>
            <li><strong>Total Facturas:</strong> {kpis['total_invoices']}</li>
            <li><strong>Ingresos Totales:</strong> ₡{kpis['total_revenue']:,.2f}</li>
            <li><strong>Tasa de Aceptación:</strong> {kpis['acceptance_rate']}%</li>
            <li><strong>Facturas Aceptadas:</strong> {kpis['accepted_count']}</li>
            <li><strong>Facturas Rechazadas:</strong> {kpis['rejected_count']}</li>
        </ul>

        <h3>Por Tipo de Documento</h3>
        <ul>
            <li><strong>FE:</strong> {kpis['fe_count']} (₡{kpis['revenue_fe']:,.2f})</li>
            <li><strong>TE:</strong> {kpis['te_count']} (₡{kpis['revenue_te']:,.2f})</li>
            <li><strong>NC:</strong> {kpis['nc_count']} (₡{kpis['revenue_nc']:,.2f})</li>
            <li><strong>ND:</strong> {kpis['nd_count']} (₡{kpis['revenue_nd']:,.2f})</li>
        </ul>

        <p><em>Este es un reporte automático generado por el sistema de facturación electrónica.</em></p>
        """

        # Send email to each admin
        for user in admin_users:
            if user.email:
                mail = self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': user.email,
                })
                mail.send()

        _logger.info(f"Daily summary sent to {len(admin_users)} administrators")

    @api.model
    def send_weekly_revenue_report(self):
        """Send weekly revenue report."""
        _logger.info("Sending weekly revenue report...")

        # Get last 7 days
        today = fields.Date.today()
        week_ago = today - timedelta(days=7)

        sales_report = self.env['report.l10n_cr_einvoice.sales_reports']
        data = sales_report.get_revenue_analysis_report(
            fields.Date.to_string(week_ago),
            fields.Date.to_string(today),
            period='daily'
        )

        # Get admin users
        admin_users = self.env.ref('base.group_system').users

        subject = f"Reporte Semanal de Ingresos - {week_ago.strftime('%d/%m')} a {today.strftime('%d/%m/%Y')}"
        body = f"""
        <h2>Reporte Semanal de Ingresos</h2>
        <p><strong>Período:</strong> {week_ago.strftime('%d de %B')} - {today.strftime('%d de %B de %Y')}</p>

        <h3>Resumen</h3>
        <ul>
            <li><strong>Total Documentos:</strong> {data['total_documents']}</li>
            <li><strong>Ingresos Totales:</strong> ₡{data['total_revenue']:,.2f}</li>
        </ul>

        <h3>Desglose Diario</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr style="background-color: #f0f0f0;">
                <th>Fecha</th>
                <th>Documentos</th>
                <th>Total</th>
            </tr>
        """

        for item in data['revenue_by_period']:
            body += f"""
            <tr>
                <td>{item['period']}</td>
                <td>{item['document_count']}</td>
                <td>₡{item['total_revenue']:,.2f}</td>
            </tr>
            """

        body += """
        </table>
        <p><em>Este es un reporte automático generado por el sistema de facturación electrónica.</em></p>
        """

        for user in admin_users:
            if user.email:
                mail = self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': user.email,
                })
                mail.send()

        _logger.info("Weekly revenue report sent")

    @api.model
    def send_monthly_hacienda_report(self):
        """Send monthly Hacienda compliance report."""
        _logger.info("Sending monthly Hacienda report...")

        # Get last month
        today = fields.Date.today()
        first_of_month = today.replace(day=1)
        last_month = first_of_month - timedelta(days=1)
        year = last_month.year
        month = last_month.month

        hacienda_report = self.env['report.l10n_cr_einvoice.hacienda_reports']
        data = hacienda_report.get_monthly_filing_report(year, month)

        # Get admin users
        admin_users = self.env.ref('base.group_system').users

        subject = f"Reporte Mensual Hacienda - {data['month_name']} {year}"
        body = f"""
        <h2>Reporte Mensual para Declaración Hacienda</h2>
        <p><strong>Período:</strong> {data['month_name']} {year}</p>

        <h3>Resumen de Documentos</h3>
        <ul>
            <li><strong>Facturas Electrónicas (FE):</strong> {data['fe_count']}</li>
            <li><strong>Tiquetes Electrónicos (TE):</strong> {data['te_count']}</li>
            <li><strong>Notas de Crédito (NC):</strong> {data['nc_count']}</li>
            <li><strong>Notas de Débito (ND):</strong> {data['nd_count']}</li>
            <li><strong>TOTAL:</strong> {data['total_documents']}</li>
        </ul>

        <h3>Resumen Financiero</h3>
        <ul>
            <li><strong>Ventas Brutas:</strong> ₡{data['total_sales']:,.2f}</li>
            <li><strong>Créditos:</strong> (₡{data['total_credits']:,.2f})</li>
            <li><strong>Débitos:</strong> ₡{data['total_debits']:,.2f}</li>
            <li><strong>VENTAS NETAS:</strong> ₡{data['net_sales']:,.2f}</li>
        </ul>

        <h3>Impuestos</h3>
        <ul>
            <li><strong>Impuesto Total:</strong> ₡{data['total_tax']:,.2f}</li>
            <li><strong>Impuesto en NC:</strong> (₡{data['credit_tax']:,.2f})</li>
            <li><strong>IMPUESTO NETO:</strong> ₡{data['net_tax']:,.2f}</li>
        </ul>

        <p><em>Este es un reporte automático generado por el sistema de facturación electrónica.</em></p>
        """

        for user in admin_users:
            if user.email:
                mail = self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': user.email,
                })
                mail.send()

        _logger.info("Monthly Hacienda report sent")

    @api.model
    def send_quarterly_performance_report(self):
        """Send quarterly performance review."""
        _logger.info("Sending quarterly performance report...")

        # Get last 90 days
        today = fields.Date.today()
        quarter_ago = today - timedelta(days=90)

        kpis = self.get_kpis(
            fields.Date.to_string(quarter_ago),
            fields.Date.to_string(today)
        )

        performance = self.env['report.l10n_cr_einvoice.performance_metrics']
        api_metrics = performance.get_api_response_time_tracking(
            fields.Date.to_string(quarter_ago),
            fields.Date.to_string(today)
        )

        # Get admin users
        admin_users = self.env.ref('base.group_system').users

        subject = f"Reporte Trimestral de Rendimiento - {quarter_ago.strftime('%d/%m')} a {today.strftime('%d/%m/%Y')}"
        body = f"""
        <h2>Reporte Trimestral de Rendimiento</h2>
        <p><strong>Período:</strong> {quarter_ago.strftime('%d de %B')} - {today.strftime('%d de %B de %Y')}</p>

        <h3>Métricas Generales</h3>
        <ul>
            <li><strong>Total Facturas:</strong> {kpis['total_invoices']}</li>
            <li><strong>Ingresos Totales:</strong> ₡{kpis['total_revenue']:,.2f}</li>
            <li><strong>Tasa de Aceptación:</strong> {kpis['acceptance_rate']}%</li>
            <li><strong>Tasa de Entrega Email:</strong> {kpis['email_delivery_rate']}%</li>
        </ul>

        <h3>Rendimiento API</h3>
        <ul>
            <li><strong>Tiempo Promedio de Respuesta:</strong> {api_metrics['avg_response_time_seconds']:.2f}s</li>
            <li><strong>Tiempo Mínimo:</strong> {api_metrics['min_response_time_seconds']:.2f}s</li>
            <li><strong>Tiempo Máximo:</strong> {api_metrics['max_response_time_seconds']:.2f}s</li>
        </ul>

        <p><em>Este es un reporte automático generado por el sistema de facturación electrónica.</em></p>
        """

        for user in admin_users:
            if user.email:
                mail = self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': user.email,
                })
                mail.send()

        _logger.info("Quarterly performance report sent")

    @api.model
    def check_system_health_and_alert(self):
        """Check system health and send alerts if issues detected."""
        performance = self.env['report.l10n_cr_einvoice.performance_metrics']
        health = performance.get_system_health_metrics()

        if health['health_status'] in ['warning', 'critical']:
            _logger.warning(f"System health status: {health['health_status']}")

            # Send alert email
            admin_users = self.env.ref('base.group_system').users

            status_color = 'orange' if health['health_status'] == 'warning' else 'red'
            subject = f"ALERTA: Estado del Sistema E-Invoice - {health['health_status'].upper()}"

            body = f"""
            <h2 style="color: {status_color};">Alerta del Sistema de Facturación Electrónica</h2>
            <p><strong>Estado:</strong> <span style="color: {status_color};">{health['health_status'].upper()}</span></p>
            <p><strong>Fecha:</strong> {health['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}</p>

            <h3>Problemas Detectados</h3>
            <ul>
                <li><strong>Documentos con Error:</strong> {health['error_documents']}</li>
                <li><strong>Documentos Atascados (>24h):</strong> {health['stuck_documents']}</li>
                <li><strong>Cola de Reintentos Pendiente:</strong> {health['retry_queue_backlog']}</li>
                <li><strong>Cola Offline Pendiente:</strong> {health['offline_queue_backlog']}</li>
            </ul>

            <h3>Recomendaciones</h3>
            <ul>
                <li>Revisar documentos con error en el sistema</li>
                <li>Verificar conectividad con API de Hacienda</li>
                <li>Revisar cola de reintentos para identificar patrones de fallo</li>
            </ul>

            <p><em>Por favor, tome acción inmediata para resolver estos problemas.</em></p>
            """

            for user in admin_users:
                if user.email:
                    mail = self.env['mail.mail'].create({
                        'subject': subject,
                        'body_html': body,
                        'email_to': user.email,
                    })
                    mail.send()

            _logger.warning(f"Health alert sent to {len(admin_users)} administrators")
        else:
            _logger.info("System health check passed")
