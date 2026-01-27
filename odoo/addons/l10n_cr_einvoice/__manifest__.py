# -*- coding: utf-8 -*-
{
    'name': 'Costa Rica Electronic Invoicing (Tribu-CR v4.4)',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Costa Rica Electronic Invoicing with Tribu-CR v4.4 compliance for GMS',
    'description': """
Costa Rica Electronic Invoicing - Tribu-CR v4.4
================================================

Custom module for GMS (Gym Management System) to generate and submit
electronic invoices compliant with Costa Rica's Ministry of Finance
(Hacienda) requirements.

Features:
---------
* Generate v4.4 compliant XML invoices
* Digital signature with X.509 certificates
* Submit invoices to Hacienda Tribu-CR API
* Automatic validation and status tracking
* PDF generation with QR codes
* Email delivery to customers
* Support for all document types:
  - Facturas Electrónicas (FE)
  - Notas de Crédito (NC)
  - Notas de Débito (ND)
  - Tiquetes Electrónicos (TE)
* Payment Method Tracking (Phase 1A):
  - 5 payment methods (Efectivo, Tarjeta, Cheque, Transferencia, SINPE Móvil)
  - Transaction ID support for SINPE Móvil
  - XML v4.4 generation with payment method codes
* Discount Codes Catalog (Phase 1B):
  - 11 official Hacienda discount codes (01-10, 99)
  - Discount code validation on invoice lines
  - Code "99" requires description
  - XML v4.4 generation with discount codes
* Recipient Economic Activity (Phase 1C):
  - 100+ CIIU 4 economic activity codes catalog
  - Smart code suggestions based on partner category
  - Bulk assignment wizard for mass updates
  - Grace period enforcement (mandatory Oct 6, 2025)

Requirements:
-------------
* Valid Hacienda credentials
* X.509 digital certificate
* Internet connection for API submission
    """,
    'author': 'GMS Development Team',
    'website': 'https://gms-cr.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'l10n_cr',  # Costa Rica localization
        'sale',
        'sale_subscription',
    ],
    'external_dependencies': {
        'python': [
            'lxml',
            'xmlschema',
            'cryptography',
            'pyOpenSSL',
            'requests',
            'qrcode',
        ],
    },
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data (load BEFORE views to ensure catalog exists)
        'data/document_types.xml',
        'data/ciiu_codes.xml',
        'data/payment_methods.xml',
        'data/discount_codes.xml',
        'data/hacienda_sequences.xml',
        'data/pos_sequences.xml',
        'data/tax_report_sequences.xml',
        'data/email_templates.xml',
        'data/void_confirmation_email.xml',
        'data/hacienda_cron_jobs.xml',
        'data/report_cron_jobs.xml',
        'data/tax_report_cron_jobs.xml',

        # Views - Order matters for dependencies
        'views/res_partner_views.xml',
        'views/einvoice_document_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_company_views.xml',
        'views/hacienda_menu.xml',
        'views/einvoice_wizard_views.xml',
        'views/einvoice_dashboard_views.xml',
        'views/ciiu_bulk_assign_views.xml',

        # Reports
        'reports/einvoice_report_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
