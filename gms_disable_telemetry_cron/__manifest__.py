{
    'name': 'GMS Disable Telemetry Cron',
    'version': '19.0.1.0.0',
    'category': 'Hidden',
    'summary': 'Disables Odoo publisher phone-home telemetry cron job',
    'description': """
        Disables Odoo Phone-Home Telemetry
        ===================================

        This module disables the weekly cron job that sends usage data to Odoo servers.

        Specifically disables:
        * Publisher: Update Notification (ir_cron_module_update_notification)
        * Weekly phone-home to Odoo services

        This ensures complete control over data transmission from the GMS system.
    """,
    'author': 'GMS Team',
    'website': 'https://gms.local',
    'depends': ['mail'],
    'data': [
        'data/disable_telemetry_cron.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
