# GMS Web Enterprise Override

## Purpose

This module overrides the `web_enterprise` module to remove all redirects to Odoo.com servers for license purchases, renewals, and upgrades. This is necessary for SHAAR's self-hosted Odoo installation to prevent users from being redirected to external Odoo.com services.

## What it does

### JavaScript Overrides

The module patches the `SubscriptionManager` class from `web_enterprise/static/src/webclient/home_menu/enterprise_subscription_service.js` to override three methods:

1. **buy()** - Originally redirected to `https://www.odoo.com/odoo-enterprise/upgrade`
   - Now displays a notification asking users to contact their system administrator

2. **renew()** - Originally redirected to `https://www.odoo.com/odoo-enterprise/renew`
   - Now displays a notification asking users to contact their system administrator

3. **upsell()** - Originally redirected to `https://www.odoo.com/odoo-enterprise/upsell`
   - Now displays a notification asking users to contact their system administrator

### XML Template Overrides

The module also overrides the `DatabaseExpirationPanel` template to:

- Replace "buy a subscription" links with plain text "contact your system administrator"
- Replace Odoo Support links with generic "contact support" text
- Keep the UI functional but remove all external links

## Installation

1. The module is located at: `/Users/papuman/Documents/My Projects/GMS/gms_web_enterprise_override/`

2. Install the module using Docker:
   ```bash
   docker compose run --rm odoo -d GMS -i gms_web_enterprise_override --stop-after-init --no-http
   ```

3. The module will automatically be available and can be activated from the Apps menu.

## Technical Details

- **Depends on**: `web_enterprise`
- **Odoo Version**: 19.0
- **Uses**: Odoo 19 JavaScript patching system (`@web/core/utils/patch`)
- **Assets**: Registered in `web.assets_backend` bundle

## Files Structure

```
gms_web_enterprise_override/
├── __init__.py
├── __manifest__.py
├── README.md
└── static/
    └── src/
        └── webclient/
            └── home_menu/
                ├── enterprise_subscription_service.js
                └── expiration_panel.xml
```

## Testing

After installation, you can verify the override works by:

1. Triggering the expiration panel (if your database is near expiration)
2. Checking that clicking "buy", "renew", or "upsell" buttons shows notifications instead of redirecting
3. Verifying that no links to odoo.com appear in the expiration panel

## Maintenance

This module uses the patching system which is the recommended way to override Odoo functionality. If `web_enterprise` is updated in future Odoo versions, this module may need to be reviewed to ensure compatibility.
