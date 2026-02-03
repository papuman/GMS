# GMS IAP Disable Module

## Overview

This module disables Odoo's In-App Purchase (IAP) system to prevent external calls to `iap.odoo.com`. All IAP calls are intercepted and stubbed out with mock responses.

## Why This Module?

Odoo's IAP system makes external calls to `https://iap.odoo.com` for various features:
- Account balance checks
- Credit purchases
- Warning email configuration
- Account information retrieval

For development, testing, or air-gapped environments, these external calls may be:
- Unwanted or unnecessary
- Blocked by firewall rules
- Causing performance issues
- Triggering errors in logs

This module provides a clean way to disable IAP without modifying Odoo core files.

## What It Does

### 1. Monkey-patches `iap_jsonrpc()` function
- Located in: `odoo.addons.iap.tools.iap_tools`
- Intercepts all JSON-RPC calls to IAP endpoints
- Returns mock responses instead of making network requests
- Logs all attempted IAP calls for debugging

### 2. Overrides `iap.account` model methods
- `web_read()`: Skips IAP server fetch for account information
- `write()`: Skips warning email configuration updates to IAP server
- `_get_account_information_from_iap()`: Returns immediately without external calls
- `get_credits()`: Returns mock credit balance (999999)

### 3. Mock Response Strategy

The module returns appropriate mock responses for different IAP endpoints:

- **Balance check** (`/iap/1/balance`): Returns 999999 credits
- **Account information** (`/iap/1/get-accounts-information`): Returns mock registered account data
- **Warning email updates** (`/iap/1/update-warning-email-alerts`): Returns success acknowledgment
- **Unknown endpoints**: Returns generic success response

## Installation

1. The module is already mounted in `docker-compose.yml`:
   ```yaml
   - ./gms_iap_disable:/opt/odoo/custom_addons/gms_iap_disable
   ```

2. Install the module:
   ```bash
   docker compose run --rm odoo -d GMS -i gms_iap_disable --stop-after-init --no-http
   ```

3. Restart Odoo:
   ```bash
   docker compose restart odoo
   ```

## Usage

Once installed, the module works automatically. All IAP calls will be intercepted and logged.

Check the logs to see when IAP would have been called:
```bash
docker compose logs -f odoo | grep "IAP DISABLED"
```

Example log output:
```
INFO IAP DISABLED: Intercepted call to https://iap.odoo.com/iap/1/balance (method=call)
INFO IAP DISABLED: Returning mock balance (999999)
```

## Dependencies

- `iap` (Odoo core module)

## Technical Details

### Files Structure
```
gms_iap_disable/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── iap_account.py          # Overrides iap.account model
└── tools/
    ├── __init__.py
    └── iap_tools_override.py    # Monkey-patches iap_jsonrpc()
```

### Key Implementation Details

1. **Module Loading Order**: Depends on `iap` module, ensuring it loads after IAP is initialized

2. **Monkey Patching**: The `iap_jsonrpc` function is replaced at module load time, before any IAP calls are made

3. **Model Inheritance**: Uses standard Odoo inheritance (`_inherit`) to override IAP account methods

4. **Test Compatibility**: During tests (`modules.module.current_test`), maintains original behavior of raising `AccessError`

5. **Graceful Degradation**: Returns responses that prevent errors in code expecting IAP functionality

## Future Considerations

This is a temporary solution. For production environments, consider:

1. Properly configuring IAP settings in Odoo
2. Using network-level blocking if needed
3. Evaluating which IAP features you actually need
4. Checking if enterprise features require IAP

## Uninstallation

To re-enable IAP:

```bash
docker compose run --rm odoo -d GMS -u iap --stop-after-init --no-http
```

Then uninstall this module via Odoo UI or CLI.

## License

LGPL-3 (same as Odoo)
