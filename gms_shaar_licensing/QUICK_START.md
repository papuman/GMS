# SHAAR Licensing - Quick Start Guide

## TL;DR

Module **gms_shaar_licensing** replaces Odoo's publisher warranty with SHAAR licensing.

**Status**: ✓ Installed and Ready

## Enable SHAAR (2 Steps)

### 1. Add to `odoo.conf`

```ini
publisher_warranty_url = https://your-shaar-instance.vercel.app/api/license/publisher-warranty
```

### 2. Restart Odoo

```bash
docker compose restart odoo
```

## Verify It's Working

Watch logs for SHAAR activity:

```bash
docker compose logs -f odoo | grep "SHAAR"
```

You should see:
- `SHAAR licensing: Sending telemetry to https://...`
- `SHAAR licensing: Successfully received response from SHAAR server`

## What Gets Sent to SHAAR

```json
{
  "dbuuid": "unique-id",
  "dbname": "GMS",
  "nbr_users": 10,
  "nbr_active_users": 8,
  "version": "19.0",
  "apps": ["base", "account", "sale", ...],
  "web_base_url": "http://localhost:8070",
  "name": "Company Name",
  "email": "company@example.com",
  "phone": "+1234567890"
}
```

## What SHAAR Should Return

```python
{
    "messages": ["Optional message to users"],
    "enterprise_info": {
        "expiration_date": "2026-12-31",
        "expiration_reason": "trial",  # or "subscription"
        "enterprise_code": "your-license-key"
    }
}
```

## SHAAR Endpoint

```
POST /api/license/publisher-warranty
Content-Type: application/x-www-form-urlencoded

arg0={JSON telemetry data}&action=update
```

## Files

```
gms_shaar_licensing/
├── __manifest__.py                      # Module config
├── models/
│   └── publisher_warranty_contract.py   # Override logic
└── security/
    └── ir.model.access.csv              # Access control
```

## Override Details

**What**: Inherits `publisher_warranty.contract` from mail module

**How**: Overrides `_get_sys_logs()` method only

**Preserves**: All original telemetry collection via `_get_message()`

**Changes**: Target URL (reads from config instead of hardcoded)

## Troubleshooting

### No logs appearing?

1. Check `publisher_warranty_url` is in `odoo.conf`
2. Restart Odoo after config change
3. Trigger manually: Settings > Technical > Scheduled Actions > "Update Notification"

### Connection errors?

```bash
# Test SHAAR from container
docker compose exec odoo curl -I https://your-shaar-instance.vercel.app
```

### Module not loaded?

```bash
# Check installation
docker compose exec db psql -U odoo -d GMS -c \
  "SELECT name, state FROM ir_module_module WHERE name = 'gms_shaar_licensing';"
```

Should show: `installed`

## Uninstall

```bash
docker compose run --rm odoo -d GMS -u gms_shaar_licensing --stop-after-init --no-http
```

Remove `publisher_warranty_url` from `odoo.conf`.

## More Info

- `README.md` - Full documentation
- `INSTALLATION_VERIFICATION.md` - Detailed verification steps
- `/Users/papuman/Documents/My Projects/GMS/SHAAR_LICENSING_MODULE_SUMMARY.md` - Implementation summary
