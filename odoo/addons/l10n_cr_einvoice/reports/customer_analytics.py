# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoiceCustomerAnalytics(models.AbstractModel):
    """Customer Analytics for E-Invoice."""

    _name = 'report.l10n_cr_einvoice.customer_analytics'
    _description = 'E-Invoice Customer Analytics'

    @api.model
    def get_top_customers_by_revenue(self, date_from=None, date_to=None, limit=20):
        """
        Get top customers by revenue.

        Args:
            date_from: Start date
            date_to: End date
            limit: Number of top customers to return

        Returns:
            list: Top customers with detailed metrics
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=90)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        query = """
            SELECT
                p.id as partner_id,
                p.name as customer_name,
                p.vat as customer_vat,
                p.email as customer_email,
                COUNT(DISTINCT d.id) as invoice_count,
                SUM(CASE WHEN d.document_type IN ('FE', 'TE', 'ND') THEN m.amount_total ELSE 0 END) as total_revenue,
                SUM(CASE WHEN d.document_type = 'NC' THEN m.amount_total ELSE 0 END) as total_credits,
                SUM(CASE WHEN d.document_type IN ('FE', 'TE', 'ND') THEN m.amount_tax ELSE 0 END) as total_tax,
                MIN(d.invoice_date) as first_invoice_date,
                MAX(d.invoice_date) as last_invoice_date,
                COUNT(DISTINCT DATE(d.invoice_date)) as active_days
            FROM l10n_cr_einvoice_document d
            JOIN account_move m ON d.move_id = m.id
            JOIN res_partner p ON m.partner_id = p.id
            WHERE d.invoice_date >= %s AND d.invoice_date <= %s
                AND d.state = 'accepted'
            GROUP BY p.id, p.name, p.vat, p.email
            ORDER BY total_revenue DESC
            LIMIT %s
        """

        self.env.cr.execute(query, (date_from, date_to, limit))
        results = self.env.cr.dictfetchall()

        customers = []
        for row in results:
            net_revenue = float(row['total_revenue'] or 0) - float(row['total_credits'] or 0)
            avg_order_value = net_revenue / row['invoice_count'] if row['invoice_count'] > 0 else 0

            # Calculate purchase frequency
            if row['first_invoice_date'] and row['last_invoice_date']:
                days_span = (row['last_invoice_date'] - row['first_invoice_date']).days + 1
                purchase_frequency = days_span / row['invoice_count'] if row['invoice_count'] > 0 else 0
            else:
                purchase_frequency = 0

            customers.append({
                'partner_id': row['partner_id'],
                'customer_name': row['customer_name'],
                'customer_vat': row['customer_vat'] or 'N/A',
                'customer_email': row['customer_email'] or 'N/A',
                'invoice_count': row['invoice_count'],
                'total_revenue': float(row['total_revenue'] or 0),
                'total_credits': float(row['total_credits'] or 0),
                'net_revenue': net_revenue,
                'total_tax': float(row['total_tax'] or 0),
                'avg_order_value': avg_order_value,
                'first_invoice_date': row['first_invoice_date'],
                'last_invoice_date': row['last_invoice_date'],
                'active_days': row['active_days'],
                'purchase_frequency_days': round(purchase_frequency, 1),
            })

        return {
            'date_from': date_from,
            'date_to': date_to,
            'top_customers': customers,
            'total_customers_analyzed': len(customers),
        }

    @api.model
    def get_customer_purchase_frequency(self, date_from=None, date_to=None):
        """
        Analyze customer purchase frequency patterns.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Purchase frequency analysis
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=90)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        domain = [
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('state', '=', 'accepted'),
        ]

        documents = self.env['l10n_cr.einvoice.document'].search(domain)

        # Group by customer
        customer_frequency = {}
        for doc in documents:
            partner_id = doc.partner_id.id
            if partner_id not in customer_frequency:
                customer_frequency[partner_id] = {
                    'partner_name': doc.partner_id.name,
                    'invoice_count': 0,
                    'invoice_dates': [],
                }

            customer_frequency[partner_id]['invoice_count'] += 1
            customer_frequency[partner_id]['invoice_dates'].append(doc.invoice_date)

        # Categorize customers by frequency
        frequency_categories = {
            'high_frequency': [],  # >10 invoices
            'medium_frequency': [],  # 5-10 invoices
            'low_frequency': [],  # 2-4 invoices
            'one_time': [],  # 1 invoice
        }

        for partner_id, data in customer_frequency.items():
            count = data['invoice_count']
            customer_info = {
                'partner_id': partner_id,
                'partner_name': data['partner_name'],
                'invoice_count': count,
            }

            if count > 10:
                frequency_categories['high_frequency'].append(customer_info)
            elif count >= 5:
                frequency_categories['medium_frequency'].append(customer_info)
            elif count >= 2:
                frequency_categories['low_frequency'].append(customer_info)
            else:
                frequency_categories['one_time'].append(customer_info)

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_customers': len(customer_frequency),
            'high_frequency_count': len(frequency_categories['high_frequency']),
            'medium_frequency_count': len(frequency_categories['medium_frequency']),
            'low_frequency_count': len(frequency_categories['low_frequency']),
            'one_time_count': len(frequency_categories['one_time']),
            'frequency_categories': frequency_categories,
        }

    @api.model
    def get_customer_payment_preferences(self, date_from=None, date_to=None):
        """
        Analyze customer payment method preferences.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Payment preference analysis
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=90)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        query = """
            SELECT
                p.id as partner_id,
                p.name as customer_name,
                pm.name as payment_method,
                pm.code as payment_code,
                COUNT(d.id) as usage_count,
                SUM(m.amount_total) as total_amount
            FROM l10n_cr_einvoice_document d
            JOIN account_move m ON d.move_id = m.id
            JOIN res_partner p ON m.partner_id = p.id
            LEFT JOIN account_move_payment_method_rel pmr ON m.id = pmr.move_id
            LEFT JOIN l10n_cr_payment_method pm ON pmr.payment_method_id = pm.id
            WHERE d.invoice_date >= %s AND d.invoice_date <= %s
                AND d.state = 'accepted'
            GROUP BY p.id, p.name, pm.name, pm.code
            ORDER BY total_amount DESC
        """

        self.env.cr.execute(query, (date_from, date_to))
        results = self.env.cr.dictfetchall()

        # Group by customer
        customer_preferences = {}
        for row in results:
            partner_id = row['partner_id']
            if partner_id not in customer_preferences:
                customer_preferences[partner_id] = {
                    'customer_name': row['customer_name'],
                    'payment_methods': [],
                    'total_invoices': 0,
                }

            customer_preferences[partner_id]['payment_methods'].append({
                'payment_method': row['payment_method'] or 'No especificado',
                'payment_code': row['payment_code'] or 'N/A',
                'usage_count': row['usage_count'],
                'total_amount': float(row['total_amount'] or 0),
            })
            customer_preferences[partner_id]['total_invoices'] += row['usage_count']

        # Find dominant payment method per customer
        for partner_id, data in customer_preferences.items():
            if data['payment_methods']:
                dominant = max(data['payment_methods'], key=lambda x: x['usage_count'])
                data['dominant_payment_method'] = dominant['payment_method']
                data['dominant_usage_percentage'] = (
                    dominant['usage_count'] / data['total_invoices'] * 100
                ) if data['total_invoices'] > 0 else 0

        return {
            'date_from': date_from,
            'date_to': date_to,
            'customer_preferences': customer_preferences,
        }

    @api.model
    def get_customer_ciiu_distribution(self, date_from=None, date_to=None):
        """
        Analyze customer distribution by CIIU economic activity.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: CIIU activity distribution
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=90)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        query = """
            SELECT
                c.code as ciiu_code,
                c.name as ciiu_name,
                COUNT(DISTINCT p.id) as customer_count,
                COUNT(d.id) as invoice_count,
                SUM(m.amount_total) as total_revenue
            FROM l10n_cr_einvoice_document d
            JOIN account_move m ON d.move_id = m.id
            JOIN res_partner p ON m.partner_id = p.id
            LEFT JOIN l10n_cr_ciiu_code c ON p.ciiu_activity_id = c.id
            WHERE d.invoice_date >= %s AND d.invoice_date <= %s
                AND d.state = 'accepted'
            GROUP BY c.code, c.name
            ORDER BY total_revenue DESC
        """

        self.env.cr.execute(query, (date_from, date_to))
        results = self.env.cr.dictfetchall()

        ciiu_distribution = []
        for row in results:
            ciiu_distribution.append({
                'ciiu_code': row['ciiu_code'] or 'Sin CIIU',
                'ciiu_name': row['ciiu_name'] or 'No especificado',
                'customer_count': row['customer_count'],
                'invoice_count': row['invoice_count'],
                'total_revenue': float(row['total_revenue'] or 0),
                'avg_revenue_per_customer': (
                    float(row['total_revenue'] or 0) / row['customer_count']
                ) if row['customer_count'] > 0 else 0,
            })

        return {
            'date_from': date_from,
            'date_to': date_to,
            'ciiu_distribution': ciiu_distribution,
        }

    @api.model
    def get_email_engagement_metrics(self, date_from=None, date_to=None):
        """
        Analyze email engagement metrics.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Email engagement analysis
        """
        if not date_from:
            date_from = fields.Date.to_string(
                fields.Date.today() - timedelta(days=30)
            )
        if not date_to:
            date_to = fields.Date.to_string(fields.Date.today())

        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
            ('state', '=', 'accepted'),
        ]

        documents = self.env['l10n_cr.einvoice.document'].search(domain)

        # Email metrics
        total_eligible = len(documents)
        emails_sent = len(documents.filtered(lambda x: x.email_sent))
        emails_not_sent = total_eligible - emails_sent

        email_delivery_rate = (emails_sent / total_eligible * 100) if total_eligible > 0 else 0

        # Group by customer
        customer_engagement = {}
        for doc in documents:
            partner_id = doc.partner_id.id
            if partner_id not in customer_engagement:
                customer_engagement[partner_id] = {
                    'partner_name': doc.partner_id.name,
                    'partner_email': doc.partner_id.email or 'N/A',
                    'total_invoices': 0,
                    'emails_sent': 0,
                    'emails_not_sent': 0,
                }

            customer_engagement[partner_id]['total_invoices'] += 1
            if doc.email_sent:
                customer_engagement[partner_id]['emails_sent'] += 1
            else:
                customer_engagement[partner_id]['emails_not_sent'] += 1

        # Calculate engagement rate per customer
        for data in customer_engagement.values():
            data['engagement_rate'] = (
                data['emails_sent'] / data['total_invoices'] * 100
            ) if data['total_invoices'] > 0 else 0

        # Find customers with no email
        customers_no_email = []
        for partner_id, data in customer_engagement.items():
            if data['partner_email'] == 'N/A':
                customers_no_email.append({
                    'partner_id': partner_id,
                    'partner_name': data['partner_name'],
                    'invoice_count': data['total_invoices'],
                })

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_eligible_invoices': total_eligible,
            'emails_sent': emails_sent,
            'emails_not_sent': emails_not_sent,
            'email_delivery_rate': round(email_delivery_rate, 2),
            'total_customers': len(customer_engagement),
            'customers_no_email': customers_no_email,
            'customer_engagement': customer_engagement,
        }

    @api.model
    def get_customer_lifetime_value(self, partner_id=None, limit=50):
        """
        Calculate customer lifetime value (CLV).

        Args:
            partner_id: Specific customer ID (optional)
            limit: Number of top customers to return

        Returns:
            dict or list: CLV analysis
        """
        if partner_id:
            domain = [('partner_id', '=', partner_id)]
        else:
            domain = []

        domain.append(('state', '=', 'accepted'))

        query = """
            SELECT
                p.id as partner_id,
                p.name as customer_name,
                p.create_date as customer_since,
                MIN(d.invoice_date) as first_purchase_date,
                MAX(d.invoice_date) as last_purchase_date,
                COUNT(DISTINCT d.id) as total_invoices,
                SUM(CASE WHEN d.document_type IN ('FE', 'TE', 'ND') THEN m.amount_total ELSE 0 END) as total_revenue,
                SUM(CASE WHEN d.document_type = 'NC' THEN m.amount_total ELSE 0 END) as total_credits,
                COUNT(DISTINCT DATE(d.invoice_date)) as active_days,
                COUNT(DISTINCT EXTRACT(MONTH FROM d.invoice_date)) as active_months
            FROM res_partner p
            JOIN account_move m ON m.partner_id = p.id
            JOIN l10n_cr_einvoice_document d ON d.move_id = m.id
            WHERE d.state = 'accepted'
        """

        if partner_id:
            query += " AND p.id = %s"
            params = (partner_id,)
        else:
            query += " GROUP BY p.id, p.name, p.create_date ORDER BY total_revenue DESC LIMIT %s"
            params = (limit,)

        if not partner_id:
            query = query.replace("FROM res_partner p", "FROM res_partner p")
            query += """
            GROUP BY p.id, p.name, p.create_date
            ORDER BY total_revenue DESC
            LIMIT %s
            """

        self.env.cr.execute(query, params)
        results = self.env.cr.dictfetchall()

        clv_data = []
        for row in results:
            net_revenue = float(row['total_revenue'] or 0) - float(row['total_credits'] or 0)
            avg_order_value = net_revenue / row['total_invoices'] if row['total_invoices'] > 0 else 0

            # Calculate customer age in days
            customer_age = (datetime.now().date() - row['customer_since'].date()).days if row['customer_since'] else 0

            # Purchase recency (days since last purchase)
            if row['last_purchase_date']:
                recency_days = (datetime.now().date() - row['last_purchase_date']).days
            else:
                recency_days = 0

            clv_data.append({
                'partner_id': row['partner_id'],
                'customer_name': row['customer_name'],
                'customer_since': row['customer_since'],
                'customer_age_days': customer_age,
                'first_purchase_date': row['first_purchase_date'],
                'last_purchase_date': row['last_purchase_date'],
                'recency_days': recency_days,
                'total_invoices': row['total_invoices'],
                'total_revenue': float(row['total_revenue'] or 0),
                'total_credits': float(row['total_credits'] or 0),
                'net_revenue': net_revenue,
                'avg_order_value': avg_order_value,
                'active_days': row['active_days'],
                'active_months': row['active_months'],
                'lifetime_value': net_revenue,  # Simplified CLV
            })

        if partner_id:
            return clv_data[0] if clv_data else {}
        else:
            return {
                'top_customers_by_clv': clv_data,
                'total_analyzed': len(clv_data),
            }
