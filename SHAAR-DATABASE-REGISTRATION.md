# SHAAR Database Registration - GMS Odoo 19

**Date:** 2026-02-03
**Status:** Ready for Registration

---

## 📋 Database Information

**Database UUID:** `d1e4a5be-feb7-11f0-aad2-5e9cdeb859d1`
**Database Name:** `GMS`
**Odoo Version:** `19.0+e-20251007` (Enterprise)
**SHAAR Endpoint:** `https://shaar-prod.vercel.app/api/license/publisher-warranty`

---

## 🔑 Registration Required

Your GMS database is configured to use SHAAR for licensing, but it needs to be registered in SHAAR's tenant management system.

### Required Actions in SHAAR:

1. **Create Tenant Record** in `odoo_tenants` table:
   ```json
   {
     "databaseUuid": "d1e4a5be-feb7-11f0-aad2-5e9cdeb859d1",
     "databaseName": "GMS",
     "customerName": "Your Organization",
     "status": "active",
     "subscriptionStart": "2026-02-03",
     "subscriptionEnd": "2027-02-03",
     "planId": "<your_plan_id>",
     "enterpriseCode": "<optional_enterprise_code>",
     "maxUsers": 50,
     "contactEmail": "admin@example.com",
     "notes": "GMS Gym Management System - Odoo 19 Enterprise"
   }
   ```

2. **Assign License Plan** - Choose appropriate plan from `odoo_plans` table

3. **Generate Enterprise Code** (optional) - If you want to use enterprise codes

---

## 🧪 Test License Validation

After registering in SHAAR, test the connection:

### Option 1: Trigger Manual Check (via Odoo Shell)
```bash
docker compose run --rm odoo shell -d GMS --no-http
```

Then in Python shell:
```python
# Get the publisher warranty contract model
env['publisher_warranty.contract'].update_notification(None)
```

### Option 2: Wait for Automatic Check
The system will automatically check weekly (but the cron is disabled, so you need to trigger manually).

### Option 3: Monitor Logs
```bash
docker compose logs -f odoo | grep -i "shaar\|publisher\|warranty"
```

You should see log entries like:
```
INFO GMS odoo.addons.gms_shaar_licensing: SHAAR licensing: Sending telemetry to https://shaar-prod.vercel.app/api/license/publisher-warranty
INFO GMS odoo.addons.gms_shaar_licensing: SHAAR licensing: Response received successfully
```

---

## 📊 What SHAAR Will Receive

When GMS validates its license, SHAAR will receive:

```json
{
  "arg0": {
    "dbuuid": "d1e4a5be-feb7-11f0-aad2-5e9cdeb859d1",
    "nbr_users": 5,
    "nbr_active_users": 3,
    "dbname": "GMS",
    "version": "19.0+e-20251007",
    "language": "en_US",
    "web_base_url": "http://localhost:8070",
    "apps": ["base", "web", "web_enterprise", "l10n_cr_einvoice", ...],
    "enterprise_code": "<if_set>"
  },
  "action": "update"
}
```

SHAAR should validate and return:
```json
{
  "messages": [],
  "enterprise_info": {
    "type": "success",
    "message": "valid",
    "expiration_date": "2027-02-03",
    "expiration_reason": ""
  }
}
```

---

## ⚠️ Important Notes

### Before Registration:
- GMS will show "database will expire" warnings
- License validation will fail gracefully
- System remains functional

### After Registration:
- License validation succeeds
- No expiration warnings
- Full Enterprise features enabled
- Audit trail logged in SHAAR's `odoo_license_logs`

---

## 🔍 Troubleshooting

### If License Check Fails:

1. **Check SHAAR is running:**
   ```bash
   curl https://shaar-prod.vercel.app/api/health
   ```

2. **Verify configuration:**
   ```bash
   cat /Users/papuman/Documents/My\ Projects/GMS/odoo.conf | grep publisher
   ```

3. **Check Odoo logs:**
   ```bash
   docker compose logs odoo | grep -i "shaar\|publisher\|warranty" | tail -20
   ```

4. **Verify module is active:**
   ```bash
   docker exec gms_postgres psql -U odoo -d GMS -c \
     "SELECT name, state FROM ir_module_module WHERE name='gms_shaar_licensing';"
   ```

---

## 🎯 Next Steps Checklist

- [ ] Access SHAAR admin dashboard at https://shaar-prod.vercel.app
- [ ] Create tenant record with UUID: `d1e4a5be-feb7-11f0-aad2-5e9cdeb859d1`
- [ ] Assign license plan (Free/Starter/Pro/Enterprise)
- [ ] Set subscription end date
- [ ] Test license validation (see "Test License Validation" above)
- [ ] Verify in SHAAR logs that validation succeeded
- [ ] Confirm no expiration warnings in Odoo

---

## 📚 References

- **SHAAR Project:** https://github.com/papuman/shaar
- **SHAAR Production:** https://shaar-prod.vercel.app
- **GMS Integration Docs:** `SHAAR-INTEGRATION-COMPLETE.md`
- **Module Docs:** See `gms_shaar_licensing/README.md`

---

**Status:** ✅ Configuration Complete - Waiting for SHAAR Registration
