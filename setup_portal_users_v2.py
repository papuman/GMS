#!/usr/bin/env python3
"""
Create portal users using Odoo shell - simplified approach
"""

import sys
import subprocess

script = """
# Create test members and grant portal access
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

portal_wizard = env['portal.wizard']
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
        # Use portal wizard to grant access
        wizard = portal_wizard.create({
            'partner_ids': [(4, partner.id)]
        })

        # Get the wizard user line
        user_line = wizard.user_ids.filtered(lambda u: u.partner_id.id == partner.id)

        if user_line:
            # Grant portal access
            user_line.action_grant_access()
            env.cr.commit()

            # Fetch created user
            user = env['res.users'].search([('partner_id', '=', partner.id)], limit=1)

            if user:
                # Set password
                user.write({'password': 'portal123'})
                print(f"Created portal user: {user.name} (User ID: {user.id}, Login: {user.login})")
                created_users.append(user)
        else:
            print(f"Could not create wizard line for {partner.name}")
    else:
        print(f"User exists: {user.name} (User ID: {user.id})")
        # Reset password
        user.write({'password': 'portal123'})
        created_users.append(user)

env.cr.commit()

print(f"\\n{'='*70}")
print("PORTAL USERS READY")
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
