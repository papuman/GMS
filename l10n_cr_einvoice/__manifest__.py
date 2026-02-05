# -*- coding: utf-8 -*-
{
    'name': 'Costa Rica Electronic Invoicing (Tribu-CR v4.4)',
    'version': '19.0.10.0.0',
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
* 4-Layer Validation System (Phase 2):
  - Backend database constraints with rule engine
  - XML generator pre-flight checks
  - POS real-time validation UI
  - Validation override wizard with audit trail
* Cédula Lookup Service (Phase 3):
  - 5-step waterfall lookup strategy (cache → API → manual)
  - Multi-tier cache (Fresh/Refresh/Stale/Expired)
  - Rate limiter (20 burst, 10/sec sustained)
  - Real-time lookup dashboard with health metrics
  - POS integration with auto-formatting
  - Background cache refresh jobs

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
        'l10n_cr',
        'sale',
        'sale_subscription',
        'point_of_sale',
    ],
    'assets': {
        'point_of_sale.assets_prod': [
            'l10n_cr_einvoice/static/src/css/pos_einvoice.css',
            'l10n_cr_einvoice/static/src/js/pos_einvoice.js',
            'l10n_cr_einvoice/static/src/xml/pos_einvoice.xml',
            'l10n_cr_einvoice/static/src/xml/pos_receipt.xml',
            # TODO: Re-enable when cedula lookup is rewritten for Odoo 19 POS data API
            # 'l10n_cr_einvoice/static/src/css/pos_cedula_lookup.css',
            # 'l10n_cr_einvoice/static/src/js/pos_cedula_lookup.js',
            # 'l10n_cr_einvoice/static/src/xml/pos_cedula_lookup.xml',
        ],
        'web.assets_backend': [
            'l10n_cr_einvoice/static/src/js/pos_kanban_gym.js',
            'l10n_cr_einvoice/static/src/js/cedula_dashboard.js',
        ],
    },
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
        'data/validation_rules.xml',
        'data/partner_tags.xml',
        'data/hacienda_sequences.xml',
        'data/pos_sequences.xml',
        'data/tax_report_sequences.xml',
        'data/gym_pos_products.xml',
        'data/pos_config_gym.xml',
        # TODO: Fix Odoo 19 XML schema validation for email templates
        # 'data/email_templates.xml',
        # 'data/void_confirmation_email.xml',
        'data/hacienda_cron_jobs.xml',
        'data/report_cron_jobs.xml',
        'data/tax_report_cron_jobs.xml',
        'data/cedula_cache_cron_jobs.xml',
        'data/cedula_dashboard_cron_jobs.xml',

        # Views - Core views enabled (functional views only)
        'views/res_partner_views.xml',          # Partner CIIU fields
        'views/einvoice_document_views.xml',    # E-invoice document views
        'views/res_company_views.xml',          # Company Hacienda settings
        'views/pos_order_views.xml',            # POS Order e-invoice integration
        'views/pos_config_views.xml',           # POS Config e-invoice settings (fixed for Odoo 19)
        'views/pos_offline_queue_views.xml',    # POS offline queue management

        # Phase 9B: Tax Reports Views (MUST load BEFORE hacienda_menu.xml to define actions)
        'views/tax_report_period_views.xml',    # Tax report periods
        'views/d150_vat_report_views.xml',      # D-150 Monthly VAT
        'views/d101_income_tax_report_views.xml', # D-101 Annual Income Tax
        'views/d151_informative_report_views.xml', # D-151 Informative Declaration

        # Catalog Views (MUST load BEFORE hacienda_menu.xml to define actions)
        'views/payment_method_views.xml',       # Payment methods catalog
        'views/discount_code_views.xml',        # Discount codes catalog
        'views/validation_rule_views.xml',      # Validation rules catalog

        # Cédula Lookup Dashboard (MUST load BEFORE hacienda_menu.xml to define actions)
        'views/cedula_dashboard_views.xml',     # Cédula lookup monitoring dashboard

        # Menu structure (MUST load AFTER view files to reference their actions)
        'views/hacienda_menu.xml',              # Hacienda menu structure

        # Wizards
        'views/validation_override_wizard_views.xml',  # Validation override wizard
        'views/partner_cedula_lookup_wizard_views.xml',  # Partner cédula lookup wizard

        # TODO: Enable when models are implemented:
        # 'views/einvoice_wizard_views.xml',      # Other wizards (models not implemented)
        # 'views/einvoice_dashboard_views.xml',   # Dashboard (analytics model)
        # 'views/ciiu_bulk_assign_views.xml',     # Bulk wizard (model exists, needs testing)

        # TODO: Fix Odoo 19 XPath issues for these views:
        # 'views/account_move_views.xml',       # Discount code fields (Phase 1B optional)
        # 'views/res_config_settings_views.xml', # Settings page integration (optional)

        # Reports
        'reports/einvoice_report_templates.xml',  # PDF report templates
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
