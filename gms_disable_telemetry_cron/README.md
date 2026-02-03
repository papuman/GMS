# GMS Disable Telemetry Cron

## Purpose

This module disables the Odoo weekly telemetry cron job that phones home to Odoo servers.

## What it Disables

- **Cron Job**: `mail.ir_cron_module_update_notification`
- **Name**: "Publisher: Update Notification"
- **Function**: `model.update_notification(None)` on `publisher.warranty.contract`
- **Frequency**: Weekly (every 7 days)

## Installation

```bash
# Install the module
docker compose run --rm odoo -d GMS -i gms_disable_telemetry_cron --stop-after-init --no-http

# Or update if already installed
docker compose run --rm odoo -d GMS -u gms_disable_telemetry_cron --stop-after-init --no-http
```

## Verification

To verify the cron job is disabled:

```python
# In Odoo shell
docker compose run --rm odoo shell -d GMS --no-http

# Then run:
cron = env.ref('mail.ir_cron_module_update_notification')
print(f"Cron active: {cron.active}")
print(f"Cron name: {cron.name}")
# Should print: Cron active: False
```

## Technical Details

- Uses `noupdate="0"` to ensure the data file always overwrites on module update
- Sets `active=False` on the existing cron record
- Depends on `mail` module since that's where the cron is defined
- The cron job is not deleted, just deactivated (safer approach)

## Privacy & Security

This module enhances privacy by preventing automatic data transmission to external Odoo servers. All data stays within the GMS system.
