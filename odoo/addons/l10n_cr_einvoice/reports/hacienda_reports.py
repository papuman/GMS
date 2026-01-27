# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EInvoiceHaciendaReports(models.AbstractModel):
    """Hacienda Compliance Reports for E-Invoice."""

    _name = 'report.l10n_cr_einvoice.hacienda_reports'
    _description = 'E-Invoice Hacienda Compliance Reports'

    @api.model
    def get_monthly_filing_report(self, year, month):
        """
        Generate monthly Hacienda filing report.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            dict: Monthly filing summary for tax filing
        """
        # Calculate date range
        date_from = fields.Date.to_string(datetime(year, month, 1))
        if month == 12:
            date_to = fields.Date.to_string(datetime(year, 12, 31))
        else:
            date_to = fields.Date.to_string(datetime(year, month + 1, 1) - timedelta(days=1))

        domain = [
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('state', '=', 'accepted'),
        ]

        documents = self.env['l10n_cr.einvoice.document'].search(domain, order='invoice_date')

        # Separate by document type
        invoices_fe = documents.filtered(lambda x: x.document_type == 'FE')
        receipts_te = documents.filtered(lambda x: x.document_type == 'TE')
        credit_notes = documents.filtered(lambda x: x.document_type == 'NC')
        debit_notes = documents.filtered(lambda x: x.document_type == 'ND')

        # Calculate totals
        total_sales = sum(invoices_fe.mapped('amount_total')) + sum(receipts_te.mapped('amount_total'))
        total_credits = sum(credit_notes.mapped('amount_total'))
        total_debits = sum(debit_notes.mapped('amount_total'))
        net_sales = total_sales - total_credits + total_debits

        # Tax calculations
        total_tax = sum(documents.filtered(
            lambda x: x.document_type in ['FE', 'TE', 'ND']
        ).mapped('move_id.amount_tax'))

        credit_tax = sum(credit_notes.mapped('move_id.amount_tax'))
        net_tax = total_tax - credit_tax

        # Tax breakdown by rate
        tax_by_rate = {}
        for doc in documents.filtered(lambda x: x.document_type in ['FE', 'TE', 'ND']):
            for line in doc.move_id.invoice_line_ids:
                for tax in line.tax_ids:
                    rate = tax.amount
                    if rate not in tax_by_rate:
                        tax_by_rate[rate] = {
                            'rate': rate,
                            'name': tax.name,
                            'base': 0,
                            'tax': 0,
                        }

                    line_subtotal = line.price_subtotal
                    line_tax = line.price_total - line.price_subtotal
                    tax_by_rate[rate]['base'] += line_subtotal
                    tax_by_rate[rate]['tax'] += line_tax

        # Customer breakdown (top 20)
        customer_summary = {}
        for doc in documents:
            partner_id = doc.partner_id.id
            if partner_id not in customer_summary:
                customer_summary[partner_id] = {
                    'partner_name': doc.partner_id.name,
                    'partner_vat': doc.partner_id.vat or 'N/A',
                    'invoice_count': 0,
                    'total_amount': 0,
                }

            customer_summary[partner_id]['invoice_count'] += 1
            if doc.document_type in ['FE', 'TE', 'ND']:
                customer_summary[partner_id]['total_amount'] += doc.amount_total
            elif doc.document_type == 'NC':
                customer_summary[partner_id]['total_amount'] -= doc.amount_total

        top_customers = sorted(
            customer_summary.values(),
            key=lambda x: x['total_amount'],
            reverse=True
        )[:20]

        return {
            'year': year,
            'month': month,
            'month_name': datetime(year, month, 1).strftime('%B'),
            'date_from': date_from,
            'date_to': date_to,

            # Document counts
            'total_documents': len(documents),
            'fe_count': len(invoices_fe),
            'te_count': len(receipts_te),
            'nc_count': len(credit_notes),
            'nd_count': len(debit_notes),

            # Financial summary
            'total_sales': total_sales,
            'total_credits': total_credits,
            'total_debits': total_debits,
            'net_sales': net_sales,

            # Tax summary
            'total_tax': total_tax,
            'credit_tax': credit_tax,
            'net_tax': net_tax,
            'tax_by_rate': sorted(tax_by_rate.values(), key=lambda x: x['rate'], reverse=True),

            # Customer summary
            'top_customers': top_customers,

            # Documents detail
            'documents': documents,
        }

    @api.model
    def get_rejected_invoices_report(self, date_from=None, date_to=None):
        """
        Generate rejected invoices report with error analysis.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Rejected invoices analysis
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
            ('state', '=', 'rejected'),
        ]

        rejected_docs = self.env['l10n_cr.einvoice.document'].search(domain, order='create_date desc')

        # Error categorization
        error_categories = {}
        for doc in rejected_docs:
            # Try to categorize error
            error_msg = doc.hacienda_message or doc.error_message or 'Error desconocido'

            # Simple categorization based on common error patterns
            if 'certificado' in error_msg.lower() or 'firma' in error_msg.lower():
                category = 'Problemas de certificado/firma'
            elif 'xml' in error_msg.lower() or 'formato' in error_msg.lower():
                category = 'Errores de formato XML'
            elif 'receptor' in error_msg.lower() or 'emisor' in error_msg.lower():
                category = 'Datos de emisor/receptor'
            elif 'impuesto' in error_msg.lower() or 'iva' in error_msg.lower():
                category = 'Errores de impuestos'
            elif 'clave' in error_msg.lower():
                category = 'Problemas con clave numérica'
            else:
                category = 'Otros errores'

            if category not in error_categories:
                error_categories[category] = {
                    'category': category,
                    'count': 0,
                    'examples': [],
                }

            error_categories[category]['count'] += 1
            if len(error_categories[category]['examples']) < 5:
                error_categories[category]['examples'].append({
                    'document_number': doc.name,
                    'error_message': error_msg,
                    'date': doc.create_date,
                })

        # Document type breakdown
        fe_rejected = len(rejected_docs.filtered(lambda x: x.document_type == 'FE'))
        te_rejected = len(rejected_docs.filtered(lambda x: x.document_type == 'TE'))
        nc_rejected = len(rejected_docs.filtered(lambda x: x.document_type == 'NC'))
        nd_rejected = len(rejected_docs.filtered(lambda x: x.document_type == 'ND'))

        # Retry statistics
        avg_retries = sum(rejected_docs.mapped('retry_count')) / len(rejected_docs) if rejected_docs else 0

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_rejected': len(rejected_docs),
            'fe_rejected': fe_rejected,
            'te_rejected': te_rejected,
            'nc_rejected': nc_rejected,
            'nd_rejected': nd_rejected,
            'avg_retries': round(avg_retries, 2),
            'error_categories': sorted(
                error_categories.values(),
                key=lambda x: x['count'],
                reverse=True
            ),
            'rejected_documents': rejected_docs,
        }

    @api.model
    def get_pending_invoices_report(self):
        """
        Generate pending invoices report (requiring attention).

        Returns:
            dict: Pending invoices summary
        """
        # Find documents in non-final states
        pending_domain = [
            ('state', 'in', ['draft', 'generated', 'signed', 'submitted']),
        ]

        pending_docs = self.env['l10n_cr.einvoice.document'].search(
            pending_domain,
            order='create_date'
        )

        # Group by state
        by_state = {}
        for doc in pending_docs:
            state = doc.state
            if state not in by_state:
                by_state[state] = {
                    'state': state,
                    'state_name': dict(doc._fields['state'].selection)[state],
                    'count': 0,
                    'oldest_date': None,
                    'documents': [],
                }

            by_state[state]['count'] += 1
            if not by_state[state]['oldest_date'] or doc.create_date < by_state[state]['oldest_date']:
                by_state[state]['oldest_date'] = doc.create_date

            by_state[state]['documents'].append(doc)

        # Identify stuck documents (older than 24 hours)
        stuck_threshold = datetime.now() - timedelta(hours=24)
        stuck_docs = pending_docs.filtered(
            lambda x: x.create_date < stuck_threshold
        )

        # Documents in retry queue
        retry_pending = self.env['l10n_cr.einvoice.retry.queue'].search_count([
            ('state', '=', 'pending')
        ])

        return {
            'total_pending': len(pending_docs),
            'stuck_count': len(stuck_docs),
            'retry_queue_pending': retry_pending,
            'by_state': sorted(
                by_state.values(),
                key=lambda x: x['count'],
                reverse=True
            ),
            'stuck_documents': stuck_docs,
        }

    @api.model
    def get_status_timeline_report(self, date_from=None, date_to=None):
        """
        Generate status timeline report (submission to acceptance).

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            dict: Timeline analysis
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
            ('hacienda_submission_date', '!=', False),
            ('hacienda_acceptance_date', '!=', False),
        ]

        documents = self.env['l10n_cr.einvoice.document'].search(domain)

        # Calculate processing times
        timeline_data = []
        total_processing_time = 0

        for doc in documents:
            processing_time = (doc.hacienda_acceptance_date - doc.hacienda_submission_date).total_seconds() / 60

            timeline_data.append({
                'document_number': doc.name,
                'document_type': dict(doc._fields['document_type'].selection)[doc.document_type],
                'submission_date': doc.hacienda_submission_date,
                'acceptance_date': doc.hacienda_acceptance_date,
                'processing_time_minutes': round(processing_time, 2),
                'amount': doc.amount_total,
            })

            total_processing_time += processing_time

        avg_processing_time = total_processing_time / len(documents) if documents else 0

        # Find fastest and slowest
        if timeline_data:
            fastest = min(timeline_data, key=lambda x: x['processing_time_minutes'])
            slowest = max(timeline_data, key=lambda x: x['processing_time_minutes'])
        else:
            fastest = slowest = None

        # Distribution by time ranges
        time_distribution = {
            '0-5 min': 0,
            '5-15 min': 0,
            '15-30 min': 0,
            '30-60 min': 0,
            '60+ min': 0,
        }

        for item in timeline_data:
            time = item['processing_time_minutes']
            if time <= 5:
                time_distribution['0-5 min'] += 1
            elif time <= 15:
                time_distribution['5-15 min'] += 1
            elif time <= 30:
                time_distribution['15-30 min'] += 1
            elif time <= 60:
                time_distribution['30-60 min'] += 1
            else:
                time_distribution['60+ min'] += 1

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_documents': len(documents),
            'avg_processing_time': round(avg_processing_time, 2),
            'fastest_processing': fastest,
            'slowest_processing': slowest,
            'time_distribution': time_distribution,
            'timeline_data': sorted(timeline_data, key=lambda x: x['processing_time_minutes']),
        }

    @api.model
    def get_audit_trail_report(self, document_id=None, date_from=None, date_to=None):
        """
        Generate complete audit trail report.

        Args:
            document_id: Specific document ID (optional)
            date_from: Start date
            date_to: End date

        Returns:
            dict: Audit trail data
        """
        if document_id:
            domain = [('document_id', '=', document_id)]
        else:
            domain = []
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))

        # Get response messages (audit trail)
        ResponseMessage = self.env['l10n_cr.hacienda.response.message']
        messages = ResponseMessage.search(domain, order='create_date desc')

        # Group by document
        by_document = {}
        for msg in messages:
            doc_id = msg.document_id.id
            if doc_id not in by_document:
                by_document[doc_id] = {
                    'document_number': msg.document_id.name,
                    'document_type': dict(msg.document_id._fields['document_type'].selection)[msg.document_id.document_type],
                    'final_status': msg.document_id.state,
                    'messages': [],
                }

            by_document[doc_id]['messages'].append({
                'date': msg.create_date,
                'message_type': msg.message_type,
                'status_code': msg.status_code,
                'message': msg.message,
                'response_data': msg.response_data,
            })

        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_messages': len(messages),
            'total_documents': len(by_document),
            'audit_by_document': list(by_document.values()),
            'all_messages': messages,
        }

    @api.model
    def export_monthly_filing_to_excel(self, year, month):
        """
        Export monthly filing report to Excel.

        Args:
            year: Year
            month: Month

        Returns:
            bytes: Excel file content
        """
        try:
            import xlsxwriter
            from io import BytesIO
        except ImportError:
            raise UserError(_('The xlsxwriter Python library is required to export to Excel.'))

        data = self.get_monthly_filing_report(year, month)

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        currency_format = workbook.add_format({'num_format': '₡#,##0.00'})
        title_format = workbook.add_format({'bold': True, 'font_size': 14})

        # Summary sheet
        summary = workbook.add_worksheet('Resumen Mensual')

        summary.write('A1', f'Reporte Mensual Hacienda - {data["month_name"]} {data["year"]}', title_format)

        row = 3
        summary.write(row, 0, 'Total Facturas Electrónicas:', header_format)
        summary.write(row, 1, data['fe_count'])
        row += 1
        summary.write(row, 0, 'Total Tiquetes Electrónicos:', header_format)
        summary.write(row, 1, data['te_count'])
        row += 1
        summary.write(row, 0, 'Total Notas de Crédito:', header_format)
        summary.write(row, 1, data['nc_count'])
        row += 1
        summary.write(row, 0, 'Total Notas de Débito:', header_format)
        summary.write(row, 1, data['nd_count'])
        row += 2

        summary.write(row, 0, 'Ventas Brutas:', header_format)
        summary.write(row, 1, data['total_sales'], currency_format)
        row += 1
        summary.write(row, 0, 'Créditos:', header_format)
        summary.write(row, 1, data['total_credits'], currency_format)
        row += 1
        summary.write(row, 0, 'Débitos:', header_format)
        summary.write(row, 1, data['total_debits'], currency_format)
        row += 1
        summary.write(row, 0, 'Ventas Netas:', header_format)
        summary.write(row, 1, data['net_sales'], currency_format)
        row += 2

        summary.write(row, 0, 'Impuesto Total:', header_format)
        summary.write(row, 1, data['total_tax'], currency_format)
        row += 1
        summary.write(row, 0, 'Impuesto en Créditos:', header_format)
        summary.write(row, 1, data['credit_tax'], currency_format)
        row += 1
        summary.write(row, 0, 'Impuesto Neto:', header_format)
        summary.write(row, 1, data['net_tax'], currency_format)

        # Tax details sheet
        tax_sheet = workbook.add_worksheet('Detalle Impuestos')
        tax_sheet.write_row(0, 0, ['Tasa', 'Nombre', 'Base Imponible', 'Impuesto'], header_format)

        row = 1
        for item in data['tax_by_rate']:
            tax_sheet.write(row, 0, f"{item['rate']}%")
            tax_sheet.write(row, 1, item['name'])
            tax_sheet.write(row, 2, item['base'], currency_format)
            tax_sheet.write(row, 3, item['tax'], currency_format)
            row += 1

        workbook.close()
        output.seek(0)

        return output.read()
