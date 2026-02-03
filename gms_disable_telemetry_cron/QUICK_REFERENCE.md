# Quick Reference - GMS Disable Telemetry Cron

## One-Command Verification

```bash
docker exec gms_postgres psql -U odoo -d GMS -c \
  "SELECT cron_name, active FROM ir_cron WHERE cron_name='Publisher: Update Notification';"
```

**Expected:** `active | f` (false = disabled)

## Installation

```bash
cd /Users/papuman/Documents/My\ Projects/GMS
docker compose run --rm odoo -d GMS -i gms_disable_telemetry_cron --stop-after-init --no-http
docker compose restart odoo
```

## Update Module

```bash
docker compose run --rm odoo -d GMS -u gms_disable_telemetry_cron --stop-after-init --no-http
docker compose restart odoo
```

## Module Status Check

```bash
docker exec gms_postgres psql -U odoo -d GMS -c \
  "SELECT name, state FROM ir_module_module WHERE name='gms_disable_telemetry_cron';"
```

**Expected:** `state | installed`

## What It Does

- **Disables:** Weekly phone-home to Odoo servers
- **Method:** Sets `active=False` on cron job
- **Target:** `mail.ir_cron_module_update_notification`
- **Impact:** Zero - no other functionality affected

## Files

```
gms_disable_telemetry_cron/
├── __init__.py                    # Empty init
├── __manifest__.py                # Module definition
├── README.md                      # Full documentation
├── INSTALLATION_GUIDE.md          # Detailed install steps
├── QUICK_REFERENCE.md             # This file
└── data/
    └── disable_telemetry_cron.xml # Overrides cron to inactive
```

## Key Facts

- **Version:** 19.0.1.0.0
- **Depends:** mail
- **Auto-install:** No
- **Data files:** 1 (disable_telemetry_cron.xml)
- **noupdate:** 0 (always applies)

## Troubleshooting

### Cron still active?
```bash
# Force reinstall
docker compose run --rm odoo -d GMS -i gms_disable_telemetry_cron --stop-after-init --no-http
```

### Module not found?
Check docker-compose.yml has:
```yaml
- ./gms_disable_telemetry_cron:/opt/odoo/custom_addons/gms_disable_telemetry_cron
```

### Verify in UI
1. Settings > Developer Mode
2. Technical > Scheduled Actions
3. Search "Publisher: Update Notification"
4. Should show "Inactive"

## Security Notes

This module prevents:
- Usage statistics transmission
- Module inventory reporting
- Database metadata collection
- System configuration reporting

## Maintenance

- Check after Odoo upgrades
- Verify cron stays disabled
- Update module if needed
- Monitor for any new telemetry crons

---

**Status:** Installed & Verified
**Last Check:** 2026-02-03
**Result:** Cron disabled (active=false)
