# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoiceSalesReports(models.AbstractModel):
    """Sales Reports for E-Invoice Analytics."""

    _name = 'report.l10n_cr_einvoice.sales_reports'
    _description = 'E-Invoice Sales Reports'

    @api.model
    def get_invoice_summary_report(self, date_from, date_to, partner_id=None, document_type=None):
        """
        Generate invoice summary report.

        Args:
            date_from: Start date
            date_to: End date
            partner_id: Optional customer filter
            document_type: Optional document type filter (FE, TE, NC, ND)

        Returns:
            dict: Report data
        """
        domain = [
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('state', '=', 'accepted'),
        ]

        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        if document_type:
            domain.append(('document_type', '=', document_type))

        documents = self.env['l10n_cr.einvoice.document'].search(domain)

        # Group by document type
        summary_by_type = {}
        for doc in documents:
            doc_type = doc.document_type
            if doc_type not in summary_by_type:
                summary_by_type[doc_type] = {
                    'document_type': doc_type,
                    'document_type_name': dict(doc._fields['document_type'].selection)[doc_type],
                    'count': 0,
                    'total_amount': 0,
                    'tax_amount': 0,
                    'untaxed_amount': 0,
                }

            summary_by_type[doc_type]['count'] += 1
            summary_by_type[doc_type]['total_amount'] += doc.amount_total
            summary_by_type[doc_type]['tax_amount'] += doc.move_id.amount_tax
            summary_by_type[doc_type]['untaxed_amount'] += doc.move_id.amount_untaxed

        return {
            'date_from': date_from,
            'date_to': date_to,
            'partner_name': self.env['res.partner'].browse(partner_id).name if partner_id else 'Todos',
            'total_documents': len(documents),
            'total_revenue': sum(documents.mapped('amount_total')),
            'summary_by_type': list(summary_by_type.values()),
            'documents': documents,
        }

    @api.model
    def get_revenue_analysis_report(self, date_from, date_to, period='daily'):
        """
        Generate revenue analysis report.

        Args:
            date_from: Start date
            date_to: End date
            period: 'daily', 'weekly', or 'monthly'

        Returns:
            dict: Revenue analysis data
        """
        domain = [
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('state', '=', 'accepted'),
        ]

        documents = self.env['l10n_cr.einvoice.document'].search(domain, order='invoice_date')

        # Group by period
        revenue_by_period = {}

        for doc in documents:
            # Determine period key
            if period == 'daily':
                period_key = doc.invoice_date.strftime('%Y-%m-%d')
            elif period == 'weekly':
                period_key = doc.invoice_date.strftime('%Y-W%W')
            else:  # monthly
                period_key = doc.invoice_date.strftime('%Y-%m')

            if period_key not in revenue_by_period:
                revenue_by_period[period_key] = {
                    'period': period_key,
                    'fe_revenue': 0,
                    'te_revenue': 0,
                    'nc_revenue': 0,
                    'nd_revenue': 0,
                    'total_revenue': 0,
                    'document_count': 0,
                }

            amount = doc.amount_total
            revenue_by_period[period_key]['document_count'] += 1

            if doc.document_type == 'FE':
                revenue_by_period[period_key]['fe_revenue'] += amount
                revenue_by_period[period_key]['total_revenue'] += amount
            elif doc.document_type == 'TE':
                revenue_by_period[period_key]['te_revenue'] += amount
                revenue_by_period[period_key]['total_revenue'] += amount
            elif doc.document_type == 'NC':
                revenue_by_period[period_key]['nc_revenue'] += amount
                revenue_by_period[period_key]['total_revenue'] -= amount
            elif doc.document_type == 'ND':
                revenue_by_period[period_key]['nd_revenue'] += amount
                revenue_by_period[period_key]['total_revenue'] += amount

        return {
            'date_from': date_from,
            'date_to': date_to,
            'period': period,
            'total_revenue': sum(p['total_revenue'] for p in revenue_by_period.values()),
            'total_documents': sum(p['document_count'] for p in revenue_by_period.values()),
            'revenue_by_period': sorted(revenue_by_period.values(), key=lambda x: x['period']),
        }

    @api.model
    def get_tax_collection_report(self, date_from, date_to):
        """
        Generate tax collection report (IVA).

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Tax collection data
        """
        domain = [
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('state', '=', 'accepted'),
            ('document_type', 'in', ['FE', 'TE', 'ND']),  # Exclude NC
        ]

        documents = self.env['l10n_cr.einvoice.document'].search(domain)

        # Tax breakdown by rate
        tax_by_rate = {}

        for doc in documents:
            for line in doc.move_id.invoice_line_ids:
                for tax in line.tax_ids:
                    rate = tax.amount
                    if rate not in tax_by_rate:
                        tax_by_rate[rate] = {
                            'tax_rate': rate,
                            'tax_name': tax.name,
                            'taxable_base': 0,
                            'tax_amount': 0,
                        }

                    # Calculate tax for this line
                    line_subtotal = line.price_subtotal
                    line_tax = line.price_total - line.price_subtotal

                    tax_by_rate[rate]['taxable_base'] += line_subtotal
                    tax_by_rate[rate]['tax_amount'] += line_tax

        total_tax = sum(documents.mapped('move_id.amount_tax'))
        total_untaxed = sum(documents.mapped('move_id.amount_untaxed'))

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_tax_collected': total_tax,
            'total_taxable_base': total_untaxed,
            'total_revenue': total_tax + total_untaxed,
            'tax_by_rate': sorted(tax_by_rate.values(), key=lambda x: x['tax_rate'], reverse=True),
            'document_count': len(documents),
        }

    @api.model
    def get_payment_method_report(self, date_from, date_to):
        """
        Generate payment method breakdown report.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Payment method analysis
        """
        domain = [
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('state', '=', 'accepted'),
        ]

        documents = self.env['l10n_cr.einvoice.document'].search(domain)

        # Group by payment method
        payment_breakdown = {}

        for doc in documents:
            payment_methods = doc.move_id.payment_method_ids
            if not payment_methods:
                pm_key = 'no_payment_method'
                pm_name = 'No especificado'
                pm_code = 'N/A'
            else:
                # Handle multiple payment methods (use first one for simplicity)
                pm = payment_methods[0]
                pm_key = f'pm_{pm.id}'
                pm_name = pm.name
                pm_code = pm.code

            if pm_key not in payment_breakdown:
                payment_breakdown[pm_key] = {
                    'payment_method': pm_name,
                    'payment_code': pm_code,
                    'document_count': 0,
                    'total_amount': 0,
                    'fe_count': 0,
                    'te_count': 0,
                    'nc_count': 0,
                    'nd_count': 0,
                }

            payment_breakdown[pm_key]['document_count'] += 1
            payment_breakdown[pm_key]['total_amount'] += doc.amount_total

            if doc.document_type == 'FE':
                payment_breakdown[pm_key]['fe_count'] += 1
            elif doc.document_type == 'TE':
                payment_breakdown[pm_key]['te_count'] += 1
            elif doc.document_type == 'NC':
                payment_breakdown[pm_key]['nc_count'] += 1
            elif doc.document_type == 'ND':
                payment_breakdown[pm_key]['nd_count'] += 1

        total_revenue = sum(documents.mapped('amount_total'))

        # Calculate percentages
        for pm_data in payment_breakdown.values():
            pm_data['percentage'] = (pm_data['total_amount'] / total_revenue * 100) if total_revenue > 0 else 0

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_revenue': total_revenue,
            'total_documents': len(documents),
            'payment_breakdown': sorted(
                payment_breakdown.values(),
                key=lambda x: x['total_amount'],
                reverse=True
            ),
        }

    @api.model
    def get_customer_transaction_report(self, partner_id, date_from=None, date_to=None):
        """
        Generate customer transaction history report.

        Args:
            partner_id: Customer ID
            date_from: Start date (optional)
            date_to: End date (optional)

        Returns:
            dict: Customer transaction history
        """
        domain = [
            ('partner_id', '=', partner_id),
            ('state', '=', 'accepted'),
        ]

        if date_from:
            domain.append(('invoice_date', '>=', date_from))
        if date_to:
            domain.append(('invoice_date', '<=', date_to))

        documents = self.env['l10n_cr.einvoice.document'].search(domain, order='invoice_date desc')
        partner = self.env['res.partner'].browse(partner_id)

        # Calculate statistics
        total_revenue = sum(documents.mapped('amount_total'))
        total_tax = sum(documents.mapped('move_id.amount_tax'))

        # Document type breakdown
        fe_count = len(documents.filtered(lambda x: x.document_type == 'FE'))
        te_count = len(documents.filtered(lambda x: x.document_type == 'TE'))
        nc_count = len(documents.filtered(lambda x: x.document_type == 'NC'))
        nd_count = len(documents.filtered(lambda x: x.document_type == 'ND'))

        # Payment method preferences
        payment_methods = {}
        for doc in documents:
            for pm in doc.move_id.payment_method_ids:
                if pm.name not in payment_methods:
                    payment_methods[pm.name] = 0
                payment_methods[pm.name] += 1

        # Transaction history
        transactions = []
        for doc in documents:
            transactions.append({
                'date': doc.invoice_date,
                'document_number': doc.name,
                'document_type': dict(doc._fields['document_type'].selection)[doc.document_type],
                'amount': doc.amount_total,
                'tax': doc.move_id.amount_tax,
                'payment_methods': ', '.join(doc.move_id.payment_method_ids.mapped('name')) or 'N/A',
            })

        return {
            'partner_name': partner.name,
            'partner_vat': partner.vat or 'N/A',
            'partner_email': partner.email or 'N/A',
            'date_from': date_from,
            'date_to': date_to,
            'total_documents': len(documents),
            'total_revenue': total_revenue,
            'total_tax': total_tax,
            'fe_count': fe_count,
            'te_count': te_count,
            'nc_count': nc_count,
            'nd_count': nd_count,
            'payment_method_preferences': payment_methods,
            'transactions': transactions,
        }

    @api.model
    def export_to_excel(self, report_type, **kwargs):
        """
        Export report data to Excel format.

        Args:
            report_type: Type of report to export
            **kwargs: Report parameters

        Returns:
            bytes: Excel file content
        """
        try:
            import xlsxwriter
            from io import BytesIO
        except ImportError:
            raise UserError(_('The xlsxwriter Python library is required to export to Excel.'))

        # Get report data
        if report_type == 'invoice_summary':
            data = self.get_invoice_summary_report(**kwargs)
        elif report_type == 'revenue_analysis':
            data = self.get_revenue_analysis_report(**kwargs)
        elif report_type == 'tax_collection':
            data = self.get_tax_collection_report(**kwargs)
        elif report_type == 'payment_method':
            data = self.get_payment_method_report(**kwargs)
        elif report_type == 'customer_transaction':
            data = self.get_customer_transaction_report(**kwargs)
        else:
            raise UserError(_('Unknown report type: %s') % report_type)

        # Create Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        currency_format = workbook.add_format({'num_format': '₡#,##0.00'})

        # Write headers and data based on report type
        if report_type == 'invoice_summary':
            headers = ['Tipo Documento', 'Cantidad', 'Subtotal', 'Impuesto', 'Total']
            worksheet.write_row(0, 0, headers, header_format)

            row = 1
            for item in data['summary_by_type']:
                worksheet.write(row, 0, item['document_type_name'])
                worksheet.write(row, 1, item['count'])
                worksheet.write(row, 2, item['untaxed_amount'], currency_format)
                worksheet.write(row, 3, item['tax_amount'], currency_format)
                worksheet.write(row, 4, item['total_amount'], currency_format)
                row += 1

        elif report_type == 'revenue_analysis':
            headers = ['Período', 'FE', 'TE', 'NC', 'ND', 'Total', 'Documentos']
            worksheet.write_row(0, 0, headers, header_format)

            row = 1
            for item in data['revenue_by_period']:
                worksheet.write(row, 0, item['period'])
                worksheet.write(row, 1, item['fe_revenue'], currency_format)
                worksheet.write(row, 2, item['te_revenue'], currency_format)
                worksheet.write(row, 3, item['nc_revenue'], currency_format)
                worksheet.write(row, 4, item['nd_revenue'], currency_format)
                worksheet.write(row, 5, item['total_revenue'], currency_format)
                worksheet.write(row, 6, item['document_count'])
                row += 1

        workbook.close()
        output.seek(0)

        return output.read()
