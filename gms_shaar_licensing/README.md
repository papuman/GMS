# SHAAR Licensing System

This Odoo 19 module replaces the built-in publisher warranty licensing system with SHAAR, a custom licensing server.

## Overview

SHAAR (Self-Hosted Autonomously Authenticated Registry) is a custom licensing server that provides a drop-in replacement for Odoo's publisher warranty system. This module cleanly overrides the `publisher_warranty.contract` model to communicate with SHAAR instead of Odoo's servers.

## Features

- **Drop-in Replacement**: Uses the same request/response format as Odoo's system
- **Preserves Telemetry**: All original telemetry data is collected and sent to SHAAR
- **Configurable**: Easy configuration via `odoo.conf`
- **Clean Override**: Uses proper Odoo inheritance patterns
- **Error Handling**: Graceful degradation if SHAAR is unavailable
- **Logging**: Detailed logs for debugging and monitoring

## Installation

1. Copy this module to your Odoo addons directory:
   ```bash
   cp -r gms_shaar_licensing /opt/odoo/custom_addons/
   ```

2. Install the module:
   ```bash
   docker compose run --rm odoo -d GMS -i gms_shaar_licensing --stop-after-init --no-http
   ```

## Configuration

Add the following line to your `odoo.conf`:

```ini
[options]
publisher_warranty_url = https://your-shaar-instance.vercel.app/api/license/publisher-warranty
```

Replace `your-shaar-instance.vercel.app` with your actual SHAAR server URL.

## SHAAR Endpoint

The module expects SHAAR to provide an endpoint at:

```
POST /api/license/publisher-warranty
```

### Request Format

The request is sent as `application/x-www-form-urlencoded` with two parameters:

- `arg0`: JSON string containing telemetry data (see below)
- `action`: Always set to "update"

### Telemetry Data Structure

```json
{
  "dbuuid": "unique-database-id",
  "nbr_users": 10,
  "nbr_active_users": 8,
  "nbr_share_users": 2,
  "nbr_active_share_users": 1,
  "dbname": "GMS",
  "db_create_date": "2025-01-01 00:00:00",
  "version": "19.0",
  "language": "en_US",
  "web_base_url": "http://localhost:8070",
  "apps": ["base", "account", "sale", "..."],
  "enterprise_code": "optional-enterprise-code",
  "name": "Company Name",
  "email": "company@example.com",
  "phone": "+1234567890"
}
```

### Response Format

SHAAR should return a Python dict (as a string) with this structure:

```python
{
    "messages": [
        "Optional message to display to users",
        "Another message"
    ],
    "enterprise_info": {
        "expiration_date": "2026-12-31",
        "expiration_reason": "trial",  # or "subscription"
        "enterprise_code": "your-license-key",
        "database_already_linked_subscription_url": "optional-url",
        "database_already_linked_email": "optional-email",
        "database_already_linked_send_mail_url": "optional-url"
    }
}
```

## How It Works

1. **Cron Job**: Odoo's built-in cron job calls `update_notification()` periodically
2. **Data Collection**: The module uses the original `_get_message()` method to collect telemetry
3. **SHAAR Communication**: The overridden `_get_sys_logs()` method sends data to SHAAR
4. **Response Processing**: The `update_notification()` method processes SHAAR's response
5. **Database Updates**: License info and messages are stored in Odoo

## Logging

The module logs all SHAAR interactions:

- **INFO**: Successful connections and responses
- **WARNING**: Missing configuration
- **ERROR**: Connection failures or response errors

Check your Odoo logs for messages prefixed with "SHAAR licensing:"

## Error Handling

If SHAAR is unavailable or returns an error, the module:

1. Logs the error
2. Returns an empty response
3. Allows the cron to complete successfully
4. Prevents Odoo from showing error messages to users

## Verification

After installation, you can verify the module is working:

1. Check the logs for "SHAAR licensing:" messages
2. Manually trigger the cron job:
   ```python
   # In Odoo shell
   env['publisher_warranty.contract'].update_notification(cron_mode=False)
   ```
3. Check your SHAAR server logs for incoming requests

## Uninstallation

To revert to Odoo's default publisher warranty system:

```bash
docker compose run --rm odoo -d GMS -u gms_shaar_licensing --stop-after-init --no-http
```

Then remove or comment out the `publisher_warranty_url` from `odoo.conf`.

## License

LGPL-3

## Support

For issues or questions about this module, contact the GMS Development Team.
