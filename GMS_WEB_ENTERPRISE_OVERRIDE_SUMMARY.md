# GMS Web Enterprise Override - Implementation Summary

## Overview

Successfully created a custom Odoo module `gms_web_enterprise_override` that removes all redirects to Odoo.com servers for license purchases, renewals, and upgrades from the `web_enterprise` module.

## Module Location

```
/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/
```

## What Was Done

### 1. Created Module Structure

```
gms_web_enterprise_override/
├── __init__.py
├── __manifest__.py
├── README.md
├── TESTING.md
└── static/
    └── src/
        └── webclient/
            └── home_menu/
                ├── enterprise_subscription_service.js
                └── expiration_panel.xml
```

### 2. JavaScript Override (`enterprise_subscription_service.js`)

Created patches for three methods in the `SubscriptionManager` class:

#### buy() Method
- **Original behavior**: Redirected to `https://www.odoo.com/odoo-enterprise/upgrade?num_users=X`
- **New behavior**: Shows notification: "To purchase or upgrade your subscription, please contact your system administrator or SHAAR support."

#### renew() Method
- **Original behavior**: Redirected to `https://www.odoo.com/odoo-enterprise/renew?contract=XXX`
- **New behavior**: Shows notification: "To renew your subscription, please contact your system administrator or SHAAR support."

#### upsell() Method
- **Original behavior**: Redirected to `https://www.odoo.com/odoo-enterprise/upsell?num_users=X&contract=XXX`
- **New behavior**: Shows notification: "To upgrade your subscription for additional users or apps, please contact your system administrator or SHAAR support."

**Technical Implementation:**
- Uses Odoo 19's `@web/core/utils/patch` system
- Imports from `@web_enterprise/webclient/home_menu/enterprise_subscription_service`
- Follows Odoo module declaration pattern with `/** @odoo-module **/`

### 3. XML Template Override (`expiration_panel.xml`)

Modified the `DatabaseExpirationPanel` template using XPath inheritance:

- **Replaced**: `<a class="oe_instance_buy alert-link text-decoration-underline">buy a subscription</a>`
- **With**: `<span class="alert-link">contact your system administrator</span>`

- **Replaced**: `<a href="https://www.odoo.com/help">Odoo Support</a>`
- **With**: `<span class="alert-link">contact support</span>`

- **Replaced**: Additional "buy" links in the "already linked" section
- **With**: `<span class="alert-link">contact your system administrator</span>`

**Technical Implementation:**
- Uses `t-inherit` with `t-inherit-mode="extension"`
- XPath expressions to target specific elements
- Maintains UI structure while removing external links

### 4. Module Manifest (`__manifest__.py`)

Configuration:
- **Name**: GMS Web Enterprise Override
- **Version**: 1.0
- **Category**: Hidden
- **Author**: SHAAR
- **Depends on**: web_enterprise
- **Assets**: Registered in `web.assets_backend` bundle

### 5. Docker Integration

Updated `docker-compose.yml` to mount the new module:

```yaml
- ./gms_web_enterprise_override:/opt/odoo/custom_addons/gms_web_enterprise_override
```

### 6. Installation

Successfully installed the module:

```bash
docker compose run --rm odoo -d GMS -i gms_web_enterprise_override --stop-after-init --no-http
```

Installation log showed:
```
INFO GMS odoo.modules.loading: Loading module gms_web_enterprise_override (117/117)
INFO GMS odoo.modules.loading: Module gms_web_enterprise_override loaded in 0.16s
```

## Files Modified

### Modified Files:
1. `/Users/papuman/Documents/My Projects/GMS/docker-compose.yml` - Added volume mount for new module

### Created Files:
1. `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/__init__.py`
2. `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/__manifest__.py`
3. `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/README.md`
4. `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/TESTING.md`
5. `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/static/src/webclient/home_menu/enterprise_subscription_service.js`
6. `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/static/src/webclient/home_menu/expiration_panel.xml`

## Technical Approach

### Odoo 19 Compatibility

The module uses Odoo 19-specific patterns:

1. **JavaScript Module System**: `/** @odoo-module **/` declaration
2. **Patching System**: `@web/core/utils/patch` instead of class extension
3. **Import Syntax**: Uses Odoo's module path system with `@web_enterprise/...`
4. **Template Inheritance**: XPath-based inheritance with `t-inherit-mode="extension"`

### Non-Breaking Implementation

The override:
- Does not modify core Odoo files
- Uses official patching mechanisms
- Maintains UI functionality
- Shows user-friendly notifications instead of errors
- Can be easily disabled by uninstalling the module

## Testing Verification

To verify the override is working:

1. Access Odoo at http://localhost:8070
2. Look for the database expiration panel (appears near expiration)
3. Click any "buy", "renew", or "upsell" buttons
4. Verify notifications appear instead of redirects
5. Check that no odoo.com links are present

See `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/TESTING.md` for detailed testing procedures.

## Benefits

1. **Prevents External Redirects**: Users cannot accidentally navigate to Odoo.com
2. **Maintains UI**: Expiration panel still displays and functions
3. **Clear Messaging**: Users know to contact system administrator
4. **Easy Maintenance**: Uses official override patterns
5. **Reversible**: Can be uninstalled without affecting core system
6. **No Code Modification**: Original Odoo files remain untouched

## Maintenance Notes

- Module uses stable Odoo APIs (patching system)
- Should be compatible with future Odoo 19 updates
- If web_enterprise changes significantly, may need review
- All overrides are documented in code comments

## Next Steps

1. Test the module in the running Odoo instance
2. Verify notifications appear correctly
3. Ensure no JavaScript errors in browser console
4. Document any additional customizations needed for SHAAR branding
5. Consider adding company contact information to notifications

## Support

For issues or questions:
- Check `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/README.md`
- Review `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/TESTING.md`
- Examine browser console for JavaScript errors
- Verify module is installed and updated
