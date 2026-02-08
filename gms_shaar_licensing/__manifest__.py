# -*- coding: utf-8 -*-
{
    'name': 'SHAAR Licensing System',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Replace Odoo publisher warranty with SHAAR custom licensing',
    'description': """
SHAAR Custom Licensing System
==============================

This module replaces Odoo's built-in publisher warranty licensing system
with SHAAR, a custom licensing server running on Vercel.

Features:
---------
* Drop-in replacement for publisher_warranty.contract model
* Configurable via publisher_warranty_url in odoo.conf
* Preserves all telemetry collection (SHAAR needs same data)
* Maintains request/response format compatibility
* Clean inheritance pattern following Odoo 19 conventions

Configuration:
--------------
Add to your odoo.conf:
    publisher_warranty_url = https://your-shaar-instance.vercel.app/api/license/publisher-warranty

SHAAR Endpoint:
---------------
POST /api/license/publisher-warranty
    """,
    'author': 'GMS Development Team',
    'website': 'https://gms-cr.com',
    'license': 'LGPL-3',
    'depends': [
        'mail',  # Depends on mail module which contains publisher_warranty.contract
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
