# Testing Guide for GMS Web Enterprise Override

## Overview

This document describes how to test that the `gms_web_enterprise_override` module successfully removes Odoo.com redirects from the web_enterprise module.

## Installation Verification

1. Check that the module is installed:
   ```bash
   docker compose run --rm odoo -d GMS -u gms_web_enterprise_override --stop-after-init --no-http
   ```

2. Verify the module is mounted:
   ```bash
   docker compose exec odoo ls -la /opt/odoo/custom_addons/gms_web_enterprise_override
   ```

## Manual Testing Steps

### Test 1: Verify JavaScript Override

The module overrides three methods in the `SubscriptionManager` class:

1. **buy()** - Previously redirected to `https://www.odoo.com/odoo-enterprise/upgrade`
2. **renew()** - Previously redirected to `https://www.odoo.com/odoo-enterprise/renew`
3. **upsell()** - Previously redirected to `https://www.odoo.com/odoo-enterprise/upsell`

To test:
1. Access your Odoo instance at http://localhost:8070
2. Navigate to the home menu
3. If your database is near expiration, you should see the expiration panel
4. Click on any "buy", "renew", or "upsell" links
5. Verify that instead of redirecting to odoo.com, you see a notification message saying "To purchase/renew/upgrade your subscription, please contact your system administrator or SHAAR support."

### Test 2: Verify XML Template Override

The module removes external links from the expiration panel:

1. Look for the expiration panel at the top of the home menu
2. Verify that:
   - "buy a subscription" link is replaced with "contact your system administrator" (plain text)
   - Odoo Support links are replaced with "contact support" (plain text)
   - No clickable links to odoo.com are present

### Test 3: Check Browser Console

1. Open browser developer tools (F12)
2. Go to Console tab
3. Check for any JavaScript errors related to the module
4. Look for successful patch application (no errors should appear)

### Test 4: Verify Assets Loading

Check that the module's assets are properly included:

1. In browser developer tools, go to Network tab
2. Refresh the page
3. Filter for JavaScript files
4. Look for `enterprise_subscription_service.js` - should load without errors
5. Filter for XML/template files
6. Look for `expiration_panel.xml` - should load without errors

## Expected Behavior After Override

### Before Override (Original Behavior)
- Clicking "buy a subscription" redirected to: `https://www.odoo.com/odoo-enterprise/upgrade?num_users=X`
- Clicking "renew" redirected to: `https://www.odoo.com/odoo-enterprise/renew?contract=XXX`
- Clicking "upsell" redirected to: `https://www.odoo.com/odoo-enterprise/upsell?num_users=X&contract=XXX`
- Links to "Odoo Support" opened: `https://www.odoo.com/help`

### After Override (New Behavior)
- Clicking "buy"/"renew"/"upsell" shows an info notification with contact instructions
- Links to odoo.com are replaced with plain text "contact your system administrator"
- Links to Odoo Support are replaced with "contact support"
- No external redirects occur
- UI remains functional

## Troubleshooting

### Module Not Loading
If the module doesn't appear to be working:

1. Verify the module is installed:
   ```bash
   docker compose run --rm odoo -d GMS -u gms_web_enterprise_override --stop-after-init --no-http
   ```

2. Check the module is mounted in docker-compose.yml:
   ```yaml
   - ./gms_web_enterprise_override:/opt/odoo/custom_addons/gms_web_enterprise_override
   ```

3. Restart containers:
   ```bash
   docker compose restart
   ```

### Assets Not Loading
If JavaScript/XML files aren't loading:

1. Clear browser cache
2. Clear Odoo assets cache by restarting with `--dev=all`:
   ```bash
   docker compose down
   docker compose up
   ```
3. Check browser console for asset loading errors

### Override Not Working
If redirects still occur:

1. Verify the patch syntax is correct
2. Check that web_enterprise is installed and active
3. Verify the module depends on 'web_enterprise' in __manifest__.py
4. Check browser console for JavaScript errors

## Success Criteria

The override is successful if:

1. Module installs without errors
2. No JavaScript errors in browser console
3. Clicking buy/renew/upsell shows notifications instead of redirecting
4. No links to odoo.com are present in the UI
5. Expiration panel displays correctly with modified text
6. UI remains fully functional

## Additional Notes

- The module uses Odoo 19's patching system (`@web/core/utils/patch`)
- Templates use XPath inheritance with `t-inherit-mode="extension"`
- All assets are registered in the `web.assets_backend` bundle
- The module follows Odoo best practices for overriding core functionality
