#!/usr/bin/env python3
"""Reset admin password properly using Odoo's password hashing"""

import sys

# Get admin user and set password
admin = env['res.users'].search([('login', '=', 'admin')], limit=1)
if admin:
    # This will properly hash the password
    admin.write({'password': 'admin'})
    print(f"✅ Password reset for user: {admin.login} (ID: {admin.id})")
    print(f"   New password: admin")
    env.cr.commit()
else:
    print("❌ Admin user not found")
    sys.exit(1)
