#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Stuck Module Installation
Diagnoses and fixes modules stuck in intermediate states
"""

import sys
import argparse

# This script needs to run with Odoo shell
print("""
╔════════════════════════════════════════════════════════════════════╗
║           FIX STUCK MODULE INSTALLATION                            ║
╚════════════════════════════════════════════════════════════════════╝

This script will check for and fix modules stuck in intermediate states.
""")

# SQL queries to run in Odoo shell
sql_checks = """
# Check for stuck modules
SELECT name, state FROM ir_module_module
WHERE state IN ('to install', 'to upgrade', 'to remove')
ORDER BY name;
"""

fix_instructions = """
INSTRUCTIONS TO FIX:

Option 1: Use Odoo Shell (RECOMMENDED)
---------------------------------------
1. Open a terminal in your Odoo directory

2. Run Odoo shell:
   odoo-bin shell -c odoo.conf -d YOUR_DATABASE_NAME

3. Execute these commands:

   # Find stuck modules
   stuck_modules = env['ir.module.module'].search([
       ('state', 'in', ['to install', 'to upgrade', 'to remove'])
   ])

   # Show stuck modules
   for module in stuck_modules:
       print(f"Module: {module.name} - State: {module.state}")

   # Reset stuck modules to 'uninstalled' or 'installed'
   for module in stuck_modules:
       if module.state in ['to install', 'to remove']:
           module.state = 'uninstalled'
       elif module.state == 'to upgrade':
           module.state = 'installed'

   env.cr.commit()
   print("✅ Fixed! Try installing modules again.")


Option 2: Direct SQL (USE WITH CAUTION)
----------------------------------------
1. Connect to PostgreSQL:
   docker exec -it <container_name> psql -U odoo -d YOUR_DATABASE_NAME

2. Check stuck modules:
   SELECT name, state FROM ir_module_module
   WHERE state IN ('to install', 'to upgrade', 'to remove');

3. Reset them (ONLY if you know what you're doing):
   UPDATE ir_module_module
   SET state = 'uninstalled'
   WHERE state IN ('to install', 'to remove');

   UPDATE ir_module_module
   SET state = 'installed'
   WHERE state = 'to upgrade';


Option 3: Restart Odoo with --stop-after-init (SAFEST)
-------------------------------------------------------
1. Stop Odoo completely

2. Run with --stop-after-init to process pending operations:
   odoo-bin -c odoo.conf -d YOUR_DATABASE_NAME --stop-after-init

3. Start Odoo normally again


Option 4: If Running in Docker
--------------------------------
1. Restart the Odoo container:
   docker-compose restart odoo

2. Check logs:
   docker-compose logs -f odoo

3. If still stuck, use Option 1 inside the container:
   docker-compose exec odoo odoo shell -c /etc/odoo/odoo.conf


PREVENTION:
-----------
- Always wait for module operations to complete
- Don't close browser during installation
- Don't stop Odoo server during module updates
- Use --stop-after-init for bulk module operations
"""

print(sql_checks)
print(fix_instructions)
