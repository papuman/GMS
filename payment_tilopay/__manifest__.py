# -*- coding: utf-8 -*-
{
    'name': 'TiloPay Payment Gateway for Costa Rica',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'TiloPay payment gateway integration with e-invoicing support',
    'description': """
TiloPay Payment Gateway Integration
====================================

Integrate TiloPay payment gateway for automated online payment processing
in Costa Rica. Supports SINPE Móvil and credit/debit cards.

Features:
---------
* SINPE Móvil payment processing
* Credit/Debit card processing (Visa, Mastercard, Amex)
* Real-time payment confirmations via webhooks
* Automatic invoice payment reconciliation
* Integration with l10n_cr_einvoice for automatic e-invoicing
* Member portal "Pay Now" functionality with enhanced UI/UX
* Mobile-first responsive design
* Accessibility features (WCAG compliant)
* Sandbox and production modes
* Transaction tracking and history
* Secure webhook signature verification

Requirements:
-------------
* TiloPay merchant account
* API credentials (API Key, User, Password)
* HTTPS enabled for webhook endpoint
* l10n_cr_einvoice module (for e-invoicing integration)

Setup:
------
1. Register at https://tilopay.com/developers
2. Obtain API credentials from TiloPay dashboard
3. Go to Odoo: Accounting > Configuration > Payment Providers
4. Enable and configure TiloPay provider
5. Configure webhook URL in TiloPay dashboard:
   https://your-domain.com/payment/tilopay/webhook
6. Test with sandbox credentials first
7. Switch to production when ready

Support:
--------
* TiloPay Support: sac@tilopay.com
* TiloPay Developer Portal: https://cst.support.tilopay.com/servicedesk/customer/portal/21
    """,
    'author': 'GMS Development Team',
    'website': 'https://gms-cr.com',
    'license': 'LGPL-3',
    'depends': [
        'payment',              # Odoo payment provider framework
        'account',              # Invoicing
        'portal',               # Member portal
        'l10n_cr_einvoice',     # Costa Rica e-invoicing (our custom module)
    ],
    'external_dependencies': {
        'python': [
            'requests',         # HTTP client for API calls
            'cryptography',     # Webhook signature verification
        ],
    },
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/payment_provider_data.xml',

        # Views
        'views/payment_provider_views.xml',
        'views/payment_transaction_views.xml',
        'views/portal_invoice_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # CSS - Mobile-first responsive styles
            'payment_tilopay/static/src/css/payment_portal.css',

            # JavaScript - Enhanced UX with loading states and animations
            'payment_tilopay/static/src/js/payment_form.js',
            'payment_tilopay/static/src/js/payment_form_enhanced.js',
        ],
    },
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_post_init_hook',
}
