# Installation & Verification Guide

## Installation

### Step 1: Install the Module

```bash
cd /Users/papuman/Documents/My\ Projects/GMS
docker compose run --rm odoo -d GMS -i gms_disable_telemetry_cron --stop-after-init --no-http
```

### Step 2: Restart Odoo

```bash
docker compose restart odoo
```

## Verification

### Method 1: Database Query (Recommended)

Check the cron status directly in the database:

```bash
docker exec gms_postgres psql -U odoo -d GMS -c "SELECT id, cron_name, active, interval_number, interval_type FROM ir_cron WHERE cron_name='Publisher: Update Notification';"
```

**Expected Output:**
```
 id |          cron_name              | active | interval_number | interval_type
----+---------------------------------+--------+-----------------+---------------
  4 | Publisher: Update Notification  | f      |               1 | weeks
```

The `active` column should show `f` (false), indicating the cron is disabled.

### Method 2: Via Odoo UI

1. Log into Odoo at http://localhost:8070
2. Enable Developer Mode (Settings > Activate Developer Mode)
3. Go to Settings > Technical > Automation > Scheduled Actions
4. Search for "Publisher: Update Notification"
5. The action should have a red "Inactive" badge

### Method 3: Check Installed Modules

```bash
docker exec gms_postgres psql -U odoo -d GMS -c "SELECT name, state FROM ir_module_module WHERE name='gms_disable_telemetry_cron';"
```

**Expected Output:**
```
           name            | state
---------------------------+-------
 gms_disable_telemetry_cron | installed
```

## What This Prevents

This module disables the weekly cron job that:
- Collects system metadata
- Sends usage statistics to Odoo servers
- Reports installed modules and configurations
- Transmits database information

By disabling this cron, you ensure:
- Complete data privacy
- No outbound connections to Odoo servers
- Full control over system information
- Compliance with data sovereignty requirements

## Maintenance

To update the module after code changes:

```bash
docker compose run --rm odoo -d GMS -u gms_disable_telemetry_cron --stop-after-init --no-http
docker compose restart odoo
```

To uninstall (not recommended):

```bash
docker compose run --rm odoo -d GMS --stop-after-init --no-http
# Then in Odoo UI: Go to Apps, find "GMS Disable Telemetry Cron", click Uninstall
```

## Technical Details

- **Module name:** `gms_disable_telemetry_cron`
- **Version:** 19.0.1.0.0
- **Depends on:** `mail`
- **Installation path:** `/opt/odoo/custom_addons/gms_disable_telemetry_cron`
- **Data files:** `data/disable_telemetry_cron.xml`
- **Cron external ID:** `mail.ir_cron_module_update_notification`
- **Cron model:** `publisher.warranty.contract`
- **Cron method:** `update_notification(None)`

## Troubleshooting

### Issue: Module not found during installation

**Solution:** Ensure docker-compose.yml has the correct volume mount:

```yaml
volumes:
  - ./gms_disable_telemetry_cron:/opt/odoo/custom_addons/gms_disable_telemetry_cron
```

### Issue: Cron still active after installation

**Solution:** Force update the module:

```bash
# Stop Odoo
docker compose stop odoo

# Update module
docker compose run --rm odoo -d GMS -u gms_disable_telemetry_cron --stop-after-init --no-http

# Start Odoo
docker compose start odoo
```

### Issue: Need to verify no data is being sent

**Solution:** Monitor outbound network connections:

```bash
# Check Odoo container network activity
docker stats gms_odoo --no-stream

# Inspect iptables rules (if applicable)
docker exec gms_odoo iptables -L -n -v
```

## Additional Security

For enhanced security, you may also want to:

1. Block outbound connections to Odoo domains in your firewall
2. Use a local DNS resolver that filters Odoo tracking domains
3. Implement network policies in your Docker setup
4. Regularly audit outbound connections

## Support

For questions or issues, refer to:
- Main README: `/Users/papuman/Documents/My Projects/GMS/gms_disable_telemetry_cron/README.md`
- Project documentation: `/Users/papuman/Documents/My Projects/GMS/docs/`
