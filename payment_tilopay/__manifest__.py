{
    'name': 'Payment Provider: TiloPay',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "Payment provider for Costa Rica supporting cards and SINPE Movil.",
    'description': " ",  # Non-empty string to avoid loading the README file.
    'depends': ['payment', 'point_of_sale'],
    'data': [
        'views/payment_provider_views.xml',
        'views/redirect_form.xml',
        'data/payment_provider_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'assets': {
        'point_of_sale._assets_pos': [
            'payment_tilopay/static/src/js/payment_screen_patch.js',
        ],
    },
    'author': 'GMS Development Team',
    'website': 'https://gms-cr.com',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
