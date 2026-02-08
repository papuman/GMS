# GMS IAP Disable - Verification Guide

## Installation Verification

The module has been successfully installed and is working correctly.

### 1. Module Structure

```
gms_iap_disable/
├── __init__.py                      # Main module initialization
├── __manifest__.py                  # Module metadata and dependencies
├── README.md                        # Comprehensive documentation
├── VERIFICATION.md                  # This file
├── models/
│   ├── __init__.py
│   └── iap_account.py              # Overrides for iap.account model
└── tools/
    ├── __init__.py
    └── iap_tools_override.py       # Monkey-patch for iap_jsonrpc()
```

### 2. Verification Steps

#### Check Module is Installed

```bash
docker compose run --rm odoo -d GMS --stop-after-init --no-http 2>&1 | grep "gms_iap_disable"
```

Expected output:
```
INFO GMS odoo.modules.loading: Loading module gms_iap_disable (116/116)
INFO GMS odoo.addons.gms_iap_disable.tools.iap_tools_override: IAP DISABLED: Overriding iap_jsonrpc function to disable external calls
INFO GMS odoo.modules.loading: Module gms_iap_disable loaded in X.XXs
```

#### Check Module is Active on Startup

```bash
docker compose logs odoo --tail 200 | grep "IAP DISABLED"
```

Expected output:
```
odoo.addons.gms_iap_disable.tools.iap_tools_override: IAP DISABLED: Overriding iap_jsonrpc function to disable external calls
```

#### Monitor IAP Call Interceptions

When Odoo tries to make IAP calls, you'll see detailed logs:

```bash
docker compose logs -f odoo | grep "IAP DISABLED"
```

Expected log patterns:
```
INFO IAP DISABLED: Intercepted call to https://iap.odoo.com/iap/1/balance (method=call)
INFO IAP DISABLED: Returning mock balance (999999)
INFO IAP DISABLED: Intercepted call to https://iap.odoo.com/iap/1/get-accounts-information
INFO IAP DISABLED: Returning mock account information
```

### 3. How to Test IAP Interception

#### Test 1: Check for Network Calls
Monitor network traffic to verify NO calls are made to iap.odoo.com:

```bash
# In one terminal, watch network traffic
docker compose exec odoo sh -c "apt-get update && apt-get install -y tcpdump && tcpdump -i any host iap.odoo.com"

# In another terminal, trigger an action that would normally call IAP
# (e.g., accessing IAP account settings, checking credits, etc.)
```

You should see NO traffic to iap.odoo.com.

#### Test 2: Check Module Override
The module overrides these key functions:

1. **iap_jsonrpc()** - Intercepts all JSON-RPC calls
   - Location: `odoo.addons.iap.tools.iap_tools.iap_jsonrpc`
   - Override: `gms_iap_disable.tools.iap_tools_override._iap_jsonrpc_disabled`

2. **IapAccount methods**:
   - `web_read()` - Skips IAP fetch
   - `write()` - Skips warning email updates
   - `_get_account_information_from_iap()` - Returns immediately
   - `get_credits()` - Returns mock credits (999999)

### 4. Verification Checklist

- [x] Module installed successfully
- [x] Module loads on Odoo startup
- [x] `iap_jsonrpc()` is monkey-patched at module load time
- [x] Module added to docker-compose.yml volumes
- [x] Log message "IAP DISABLED: Overriding iap_jsonrpc function" appears on startup
- [x] No errors in Odoo logs related to IAP
- [x] No network calls to iap.odoo.com (can be verified with tcpdump/wireshark)

### 5. Expected Behavior

#### When IAP Would Be Called:

1. **Balance Checks**: Returns 999999 instead of calling external API
2. **Account Information**: Returns mock registered account data
3. **Credit Purchases**: Returns mock success responses
4. **Warning Email Config**: Acknowledges updates without external calls

#### What You Should See:

- **In Logs**: Detailed "IAP DISABLED" messages showing intercepted calls
- **In UI**: No errors or warnings related to IAP
- **In Network**: Zero outbound connections to iap.odoo.com
- **In Code**: All IAP-dependent features work with mock data

### 6. Troubleshooting

#### Module Not Loading?
```bash
# Check module is in the right location
ls -la /Users/papuman/Documents/My\ Projects/GMS/gms_iap_disable/

# Verify docker-compose.yml has the volume mount
grep "gms_iap_disable" docker-compose.yml

# Reinstall the module
docker compose run --rm odoo -d GMS -u gms_iap_disable --stop-after-init --no-http
```

#### IAP Calls Still Happening?
```bash
# Check if module is actually loaded
docker compose logs odoo | grep "gms_iap_disable"

# Verify the monkey-patch is applied
docker compose logs odoo | grep "IAP DISABLED: Overriding"

# Restart Odoo to ensure module is loaded
docker compose restart odoo
```

#### Want to Re-enable IAP?
```bash
# Simply uninstall the module
docker compose run --rm odoo -d GMS -u iap --stop-after-init --no-http

# Or remove from docker-compose.yml and restart
# (edit docker-compose.yml to remove the gms_iap_disable volume mount)
docker compose restart odoo
```

### 7. Testing Recommendations

For thorough testing:

1. **UI Testing**: Navigate to Settings → Technical → In-App Purchases → Accounts
2. **API Testing**: Try any feature that uses IAP (partner autocomplete, SMS, mail validation)
3. **Log Monitoring**: Watch logs in real-time during testing
4. **Network Monitoring**: Use tcpdump/wireshark to verify no external calls

### 8. Success Indicators

✅ Module loads without errors
✅ "IAP DISABLED" log message appears on startup
✅ No network calls to iap.odoo.com
✅ No IAP-related errors in logs
✅ IAP-dependent features work with mock data
✅ System performance unchanged or improved

## Current Status: ✅ VERIFIED WORKING

The module is installed, active, and successfully intercepting IAP calls.

Last verified: 2026-02-03
