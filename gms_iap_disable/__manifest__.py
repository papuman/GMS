# -*- coding: utf-8 -*-
{
    'name': 'GMS IAP Disable',
    'version': '1.0',
    'category': 'Hidden/Tools',
    'summary': 'Disable Odoo In-App Purchases (IAP) external calls',
    'description': """
        This module disables Odoo's In-App Purchase (IAP) system to prevent
        external calls to iap.odoo.com. All IAP calls are intercepted and
        stubbed out with mock responses.

        Features:
        - Overrides iap_jsonrpc() to prevent network calls
        - Returns mock responses that prevent errors
        - Logs attempted IAP calls for debugging
        - Does not break existing code that uses IAP
    """,
    'author': 'GMS',
    'depends': ['iap'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
