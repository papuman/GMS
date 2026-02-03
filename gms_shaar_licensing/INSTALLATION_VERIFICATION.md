# SHAAR Licensing Module - Installation & Verification Guide

## Module Structure

```
gms_shaar_licensing/
├── __init__.py                          # Module initialization
├── __manifest__.py                      # Module metadata and dependencies
├── README.md                            # User documentation
├── INSTALLATION_VERIFICATION.md         # This file
├── models/
│   ├── __init__.py                      # Models initialization
│   └── publisher_warranty_contract.py   # Override of publisher_warranty.contract
└── security/
    └── ir.model.access.csv              # Access control (empty - inherits from mail)
```

## Installation Steps

### 1. Mount the Module in Docker

The module is already mounted in `docker-compose.yml`:

```yaml
volumes:
  - ./gms_shaar_licensing:/opt/odoo/custom_addons/gms_shaar_licensing
```

### 2. Restart Docker Containers

If you added the volume mount, restart containers to apply changes:

```bash
cd /Users/papuman/Documents/My\ Projects/GMS
docker compose down
docker compose up -d
```

### 3. Install the Module

```bash
docker compose run --rm odoo -d GMS -i gms_shaar_licensing --stop-after-init --no-http
```

Expected output should show:
```
loading gms_shaar_licensing/security/ir.model.access.csv
Module gms_shaar_licensing loaded in X.XXs
```

## Verification

### Method 1: Database Check

Verify the module is installed in the database:

```bash
docker compose exec db psql -U odoo -d GMS -c "SELECT name, state FROM ir_module_module WHERE name = 'gms_shaar_licensing';"
```

Expected output:
```
        name         |   state
---------------------+-----------
 gms_shaar_licensing | installed
(1 row)
```

### Method 2: Check Module Files in Container

Verify the module files are mounted correctly:

```bash
docker compose exec odoo ls -la /opt/odoo/custom_addons/gms_shaar_licensing/
```

You should see all module files.

### Method 3: Check Module Code

Verify the override code is present:

```bash
docker compose exec odoo cat /opt/odoo/custom_addons/gms_shaar_licensing/models/publisher_warranty_contract.py | grep -A 5 "class PublisherWarrantyContractSHAAR"
```

### Method 4: Test with Configuration

1. Add SHAAR URL to `odoo.conf`:

```ini
[options]
addons_path = /opt/odoo/custom_addons,/opt/odoo/addons
data_dir = /var/lib/odoo
list_db = True
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
publisher_warranty_url = https://your-shaar-instance.vercel.app/api/license/publisher-warranty
```

2. Restart Odoo:

```bash
docker compose restart odoo
```

3. Check logs for SHAAR activity:

```bash
docker compose logs -f odoo | grep -i "SHAAR"
```

You should see messages like:
- `SHAAR licensing: Sending telemetry to https://your-shaar...`
- `SHAAR licensing: Successfully received response from SHAAR server`

Or if not configured:
- `SHAAR licensing: publisher_warranty_url not configured in odoo.conf`

### Method 5: Manual Trigger

You can manually trigger the warranty check by accessing Odoo and looking for the publisher warranty cron job in Settings > Technical > Automation > Scheduled Actions.

Look for "Update Notification" and run it manually to see SHAAR in action.

## What the Module Does

### Override Behavior

The module inherits from `publisher_warranty.contract` (defined in `/opt/odoo/addons/mail/models/update.py`) and overrides only the `_get_sys_logs()` method to:

1. **Preserve Data Collection**: Uses the original `_get_message()` method to collect all telemetry
2. **Change Target URL**: Reads `publisher_warranty_url` from `odoo.conf` instead of hardcoded Odoo servers
3. **Error Handling**: Returns empty response if SHAAR is unavailable (prevents cron failures)
4. **Logging**: Adds detailed logging for monitoring and debugging

### What Gets Sent to SHAAR

The module sends the same telemetry data that Odoo would normally send:

```json
{
  "dbuuid": "database-unique-id",
  "nbr_users": 10,
  "nbr_active_users": 8,
  "nbr_share_users": 2,
  "nbr_active_share_users": 1,
  "dbname": "GMS",
  "db_create_date": "2025-01-01 00:00:00",
  "version": "19.0",
  "language": "en_US",
  "web_base_url": "http://localhost:8070",
  "apps": ["base", "account", "sale", ...],
  "enterprise_code": "optional",
  "name": "Company Name",
  "email": "company@example.com",
  "phone": "+1234567890"
}
```

### Expected SHAAR Response

SHAAR should return:

```python
{
    "messages": [
        "Optional message to display in Odoo"
    ],
    "enterprise_info": {
        "expiration_date": "2026-12-31",
        "expiration_reason": "trial",
        "enterprise_code": "your-license-key",
        "database_already_linked_subscription_url": "optional",
        "database_already_linked_email": "optional",
        "database_already_linked_send_mail_url": "optional"
    }
}
```

## Troubleshooting

### Module Not Loading

1. Check if the module is in the addons path:
   ```bash
   docker compose exec odoo python3 -c "import odoo; odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf']); print(odoo.tools.config['addons_path'])"
   ```

2. Verify the manifest is valid:
   ```bash
   docker compose exec odoo cat /opt/odoo/custom_addons/gms_shaar_licensing/__manifest__.py
   ```

### No SHAAR Logs Appearing

1. Check if `publisher_warranty_url` is configured in `odoo.conf`
2. Restart Odoo after changing configuration
3. Check log level allows INFO messages
4. Manually trigger the "Update Notification" cron job

### SHAAR Connection Errors

1. Verify the SHAAR URL is accessible from the container:
   ```bash
   docker compose exec odoo curl -I https://your-shaar-instance.vercel.app
   ```

2. Check SHAAR server logs for incoming requests
3. Verify SHAAR endpoint returns valid Python dict format

## Uninstallation

To remove the module:

```bash
docker compose run --rm odoo -d GMS -u gms_shaar_licensing --stop-after-init --no-http
```

Then remove or comment out the `publisher_warranty_url` from `odoo.conf`.

## Success Criteria

The module is successfully installed and working when:

1. ✓ Module shows as "installed" in database
2. ✓ Module files are present in container
3. ✓ No errors during installation
4. ✓ SHAAR logs appear when configured
5. ✓ Publisher warranty updates complete without errors
6. ✓ License information is updated in Odoo (when SHAAR returns data)

## Support

For issues or questions, contact the GMS Development Team.
