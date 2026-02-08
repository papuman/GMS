# -*- coding: utf-8 -*-
{
    'name': 'GMS Web Enterprise Override',
    'version': '1.0',
    'category': 'Hidden',
    'author': 'SHAAR',
    'summary': 'Remove Odoo.com redirects from web_enterprise',
    'description': """
GMS Web Enterprise Override
===========================

This module overrides the web_enterprise module to remove redirects to Odoo.com
for license purchases and renewals. It replaces these with SHAAR-specific messaging
or disables them entirely.

Key changes:
- Removes buy() redirect to odoo.com/odoo-enterprise/upgrade
- Removes renew() redirect to odoo.com/odoo-enterprise/renew
- Removes upsell() redirect to odoo.com/odoo-enterprise/upsell
- Modifies expiration panel to remove external links
    """,
    'depends': ['web_enterprise'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'gms_web_enterprise_override/static/src/webclient/home_menu/enterprise_subscription_service.js',
            'gms_web_enterprise_override/static/src/webclient/home_menu/expiration_panel.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
