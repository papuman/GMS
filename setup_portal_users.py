#!/usr/bin/env python3
"""
Create portal users using Odoo shell
"""

import sys
import subprocess

script = """
# Find portal group
portal_group = env['res.groups'].search([('name', 'ilike', 'portal')], limit=1)
print(f"Portal group: {portal_group.name} (ID: {portal_group.id})")

# Create test members and portal users
test_data = [
    {
        'name': 'John Portal Member',
        'email': 'john.portal@gymtest.com',
        'phone': '555-0101',
        'street': '123 Fitness Street',
        'city': 'Gym City',
        'zip': '12345',
    },
    {
        'name': 'Jane Premium Member',
        'email': 'jane.premium@gymtest.com',
        'phone': '555-0102',
        'street': '456 Wellness Ave',
        'city': 'Health Town',
        'zip': '67890',
    },
    {
        'name': 'Mike Basic Member',
        'email': 'mike.basic@gymtest.com',
        'phone': '555-0103',
        'street': '789 Training Blvd',
        'city': 'Fitness City',
        'zip': '11111',
    }
]

created_users = []

for data in test_data:
    # Check if partner exists
    partner = env['res.partner'].search([('email', '=', data['email'])], limit=1)

    if not partner:
        partner = env['res.partner'].create(data)
        print(f"Created partner: {partner.name} (ID: {partner.id})")
    else:
        print(f"Partner exists: {partner.name} (ID: {partner.id})")

    # Check if user exists
    user = env['res.users'].search([('partner_id', '=', partner.id)], limit=1)

    if not user:
        # Create portal user
        user = env['res.users'].with_context(no_reset_password=True).create({
            'name': partner.name,
            'login': data['email'],
            'partner_id': partner.id,
            'groups_id': [(6, 0, [portal_group.id])],  # Portal group
            'password': 'portal123',
        })
        print(f"Created portal user: {user.name} (User ID: {user.id}, Login: {user.login})")
        created_users.append(user)
    else:
        print(f"User exists: {user.name} (User ID: {user.id})")
        # Update to portal group if not already
        if portal_group.id not in user.groups_id.ids:
            user.write({'groups_id': [(6, 0, [portal_group.id])]})
            print(f"  Updated to portal user")
        created_users.append(user)

env.cr.commit()

print(f"\\n{'='*70}")
print("PORTAL USERS CREATED")
print(f"{'='*70}")
for user in created_users:
    print(f"Name: {user.name}")
    print(f"Login: {user.login}")
    print(f"Password: portal123")
    print(f"Portal URL: http://localhost:8070/my")
    print("-" * 70)
"""

# Execute via docker
cmd = [
    'docker', 'exec', '-i', 'gms_odoo',
    'odoo', 'shell', '-d', 'gms_validation', '--no-http'
]

try:
    result = subprocess.run(cmd, input=script, text=True, capture_output=True, timeout=60)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr, file=sys.stderr)
    sys.exit(result.returncode)
except subprocess.TimeoutExpired:
    print("ERROR: Command timed out")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
