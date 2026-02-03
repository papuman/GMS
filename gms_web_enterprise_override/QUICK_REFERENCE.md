# Quick Reference Guide - GMS Web Enterprise Override

## Quick Commands

### Install Module
```bash
docker compose run --rm odoo -d GMS -i gms_web_enterprise_override --stop-after-init --no-http
```

### Update Module
```bash
docker compose run --rm odoo -d GMS -u gms_web_enterprise_override --stop-after-init --no-http
```

### Uninstall Module
```bash
docker compose run --rm odoo -d GMS -u gms_web_enterprise_override --stop-after-init --no-http
```
Then use Odoo UI to uninstall.

### Restart Odoo
```bash
docker compose restart odoo
```

## What Gets Overridden

| Original Behavior | New Behavior |
|------------------|--------------|
| Buy button → odoo.com/upgrade | Shows notification to contact admin |
| Renew button → odoo.com/renew | Shows notification to contact admin |
| Upsell button → odoo.com/upsell | Shows notification to contact admin |
| "buy a subscription" link | Plain text: "contact your system administrator" |
| "Odoo Support" link | Plain text: "contact support" |

## File Locations

- **Module Root**: `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/`
- **JavaScript Override**: `static/src/webclient/home_menu/enterprise_subscription_service.js`
- **XML Override**: `static/src/webclient/home_menu/expiration_panel.xml`
- **Manifest**: `__manifest__.py`

## Verification Steps

1. Check module is mounted:
   ```bash
   docker compose exec odoo ls -la /opt/odoo/custom_addons/gms_web_enterprise_override
   ```

2. Test notification (in browser console):
   ```javascript
   const subscription = odoo.__DEBUG__.services['enterprise_subscription'];
   subscription.buy();  // Should show notification, not redirect
   ```

3. Check for JavaScript errors (browser console):
   - Open Developer Tools (F12)
   - Look for errors mentioning 'gms_web_enterprise_override'
   - No errors = working correctly

## Common Issues

### Module Not Loading
- **Problem**: Module not found
- **Solution**: Check docker-compose.yml has the volume mount, restart containers

### Assets Not Loading
- **Problem**: JavaScript/XML not applied
- **Solution**: Update module, clear browser cache, restart Odoo

### Still Redirecting
- **Problem**: Override not working
- **Solution**: Check browser console for errors, verify module is installed

## Dependencies

- Requires: `web_enterprise` (automatically included in Odoo Enterprise)
- Odoo Version: 19.0+e
- No external dependencies

## Key Technical Details

- Uses Odoo 19 patch system (`@web/core/utils/patch`)
- Assets registered in `web.assets_backend` bundle
- XPath-based template inheritance
- Non-destructive override (doesn't modify core files)

## Support Files

- `README.md` - Full module documentation
- `TESTING.md` - Detailed testing procedures
- `__manifest__.py` - Module configuration
- `__init__.py` - Module initialization

## Quick Test

After installation, open Odoo in browser and run in console:
```javascript
// Test buy() override
odoo.__DEBUG__.services['enterprise_subscription'].buy();
// Should see notification, NOT redirect

// Test renew() override
odoo.__DEBUG__.services['enterprise_subscription'].renew();
// Should see notification, NOT redirect

// Test upsell() override
odoo.__DEBUG__.services['enterprise_subscription'].upsell();
// Should see notification, NOT redirect
```

## Module Info

- **Name**: GMS Web Enterprise Override
- **Technical Name**: `gms_web_enterprise_override`
- **Version**: 1.0
- **Author**: SHAAR
- **License**: LGPL-3
- **Category**: Hidden
