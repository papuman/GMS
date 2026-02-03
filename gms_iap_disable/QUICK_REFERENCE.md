# GMS IAP Disable - Quick Reference

## What Does This Module Do?

Disables all external calls to `https://iap.odoo.com` by intercepting and mocking IAP (In-App Purchase) requests.

## Status Check

```bash
# Verify module is active
docker compose logs odoo | grep "IAP DISABLED"

# Expected output:
# INFO odoo.addons.gms_iap_disable.tools.iap_tools_override: IAP DISABLED: Overriding iap_jsonrpc function to disable external calls
```

## Common Commands

### Monitor IAP Activity
```bash
# Watch for intercepted IAP calls
docker compose logs -f odoo | grep "IAP DISABLED"
```

### Reinstall Module
```bash
docker compose run --rm odoo -d GMS -u gms_iap_disable --stop-after-init --no-http
```

### Uninstall Module (Re-enable IAP)
```bash
# Via Odoo UI: Settings → Apps → Installed → Find "GMS IAP Disable" → Uninstall
```

### Check Module Status
```bash
docker compose run --rm odoo -d GMS --stop-after-init --no-http 2>&1 | grep gms_iap_disable
```

## What Gets Mocked?

| IAP Endpoint | Mock Response |
|-------------|---------------|
| `/iap/1/balance` | 999999 credits |
| `/iap/1/get-accounts-information` | Registered account data |
| `/iap/1/update-warning-email-alerts` | Success acknowledgment |
| Others | Generic success response |

## Overridden Methods

| Model | Method | Behavior |
|-------|--------|----------|
| `iap.account` | `web_read()` | Skips IAP server fetch |
| `iap.account` | `write()` | Skips warning email updates |
| `iap.account` | `_get_account_information_from_iap()` | No-op |
| `iap.account` | `get_credits()` | Returns 999999 |
| `iap_tools` | `iap_jsonrpc()` | Returns mock data |

## Troubleshooting

### Module Not Working?
1. Check logs: `docker compose logs odoo | grep "gms_iap_disable"`
2. Verify docker-compose.yml has volume mount
3. Restart: `docker compose restart odoo`

### Still Seeing IAP Calls?
1. Verify module is installed (should see "IAP DISABLED" in logs)
2. Check module isn't in error state: `docker compose logs odoo | grep -i error`
3. Try reinstalling: `-u gms_iap_disable`

### Want to Verify No External Calls?
```bash
# Monitor network traffic (requires tcpdump)
docker compose exec odoo tcpdump -i any host iap.odoo.com
# Should see NO traffic
```

## Key Log Messages

| Message | Meaning |
|---------|---------|
| `IAP DISABLED: Overriding iap_jsonrpc function` | Module loaded successfully |
| `IAP DISABLED: Intercepted call to ...` | IAP call was blocked |
| `IAP DISABLED: Returning mock balance` | Balance check mocked |
| `IAP DISABLED: Returning mock account information` | Account fetch mocked |
| `IAP: Skipping web_read IAP server fetch` | Model override working |

## Files Location

```
/Users/papuman/Documents/My Projects/GMS/gms_iap_disable/
├── __manifest__.py          # Module metadata
├── models/iap_account.py    # Model overrides
└── tools/iap_tools_override.py  # Main monkey-patch
```

## Quick Test

```bash
# 1. Check module loads
docker compose logs odoo | grep "IAP DISABLED"

# 2. Should see this:
# INFO odoo.addons.gms_iap_disable.tools.iap_tools_override: IAP DISABLED: Overriding iap_jsonrpc function

# ✅ If you see this message, the module is working!
```

## Support

- Full documentation: See `README.md`
- Verification guide: See `VERIFICATION.md`
- Implementation details: See `/GMS_IAP_DISABLE_IMPLEMENTATION.md`

## Last Updated

2026-02-03
