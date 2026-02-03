# Architecture Documentation - GMS Web Enterprise Override

## System Overview

This document describes how the `gms_web_enterprise_override` module integrates with Odoo's web_enterprise module to prevent external redirects.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Odoo 19 Enterprise                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           web_enterprise (Core Module)                  │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  enterprise_subscription_service.js              │  │    │
│  │  │  ┌──────────────────────────────────────────┐   │  │    │
│  │  │  │  SubscriptionManager Class               │   │  │    │
│  │  │  │  ├─ buy()    → odoo.com/upgrade         │   │  │    │
│  │  │  │  ├─ renew()  → odoo.com/renew           │   │  │    │
│  │  │  │  └─ upsell() → odoo.com/upsell          │   │  │    │
│  │  │  └──────────────────────────────────────────┘   │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  │                                                         │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  expiration_panel.xml                            │  │    │
│  │  │  ├─ "buy a subscription" → odoo.com link        │  │    │
│  │  │  ├─ "Odoo Support" → odoo.com/help              │  │    │
│  │  │  └─ Various redirect links                       │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                          ▲                                       │
│                          │                                       │
│                          │ PATCHES & OVERRIDES                  │
│                          │                                       │
│  ┌───────────────────────┴──────────────────────────────────┐  │
│  │     gms_web_enterprise_override (Custom Module)          │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │  enterprise_subscription_service.js (Patch)      │   │  │
│  │  │  ┌──────────────────────────────────────────┐   │   │  │
│  │  │  │  patch(SubscriptionManager.prototype)    │   │   │  │
│  │  │  │  ├─ buy()    → Show notification         │   │   │  │
│  │  │  │  ├─ renew()  → Show notification         │   │   │  │
│  │  │  │  └─ upsell() → Show notification         │   │   │  │
│  │  │  └──────────────────────────────────────────┘   │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │  expiration_panel.xml (XPath Override)           │   │  │
│  │  │  ├─ Replace "buy" link → Plain text             │   │  │
│  │  │  ├─ Replace "support" link → Plain text         │   │  │
│  │  │  └─ Remove all odoo.com URLs                    │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### Original Flow (Before Override)

```
User clicks "Buy" button
         ↓
SubscriptionManager.buy() called
         ↓
Calculate number of users
         ↓
browser.location = "https://www.odoo.com/odoo-enterprise/upgrade?num_users=X"
         ↓
User redirected to Odoo.com
```

### Overridden Flow (After Module Installation)

```
User clicks "Buy" button
         ↓
SubscriptionManager.buy() called
         ↓
PATCHED METHOD EXECUTES
         ↓
notification.add("To purchase or upgrade...")
         ↓
Notification displayed to user
         ↓
No redirect occurs
```

## Technical Implementation

### JavaScript Patching Mechanism

```javascript
import { patch } from "@web/core/utils/patch";
import { SubscriptionManager } from "@web_enterprise/webclient/home_menu/enterprise_subscription_service";

// Patch applied at runtime
patch(SubscriptionManager.prototype, {
    async buy() {
        // Custom implementation replaces original
        this.notification.add(...);
    }
});
```

**How it works:**
1. Odoo loads web_enterprise module first
2. SubscriptionManager class is registered
3. gms_web_enterprise_override loads after (dependency order)
4. patch() modifies the prototype at runtime
5. All instances now use patched methods

### XML Inheritance Mechanism

```xml
<t t-name="DatabaseExpirationPanel"
   t-inherit="web_enterprise.DatabaseExpirationPanel"
   t-inherit-mode="extension">

    <xpath expr="//a[@class='oe_instance_buy']" position="replace">
        <span>contact your system administrator</span>
    </xpath>
</t>
```

**How it works:**
1. Template inherits from web_enterprise.DatabaseExpirationPanel
2. XPath expressions locate specific elements
3. position="replace" swaps elements
4. Original template structure maintained
5. Only targeted elements modified

## Asset Loading Sequence

```
1. Odoo starts
   ↓
2. Load core modules (web, base)
   ↓
3. Load web_enterprise
   ├─ Register SubscriptionManager
   ├─ Register DatabaseExpirationPanel template
   └─ Add to assets_backend bundle
   ↓
4. Load gms_web_enterprise_override (depends on web_enterprise)
   ├─ Apply SubscriptionManager patches
   ├─ Merge template overrides
   └─ Add to assets_backend bundle (loaded after web_enterprise)
   ↓
5. Frontend receives merged assets
   ├─ Original code + patches
   └─ Original templates + overrides
   ↓
6. User interface renders with overrides active
```

## Module Dependencies

```
gms_web_enterprise_override
         ↓ depends on
   web_enterprise
         ↓ depends on
    web + base_setup
         ↓ depends on
        base
```

## File Organization

```
gms_web_enterprise_override/
├── __init__.py                    # Python module init
├── __manifest__.py                # Module definition
├── README.md                      # Module documentation
├── TESTING.md                     # Testing procedures
├── QUICK_REFERENCE.md             # Quick commands
├── ARCHITECTURE.md                # This file
└── static/
    └── src/
        └── webclient/
            └── home_menu/
                ├── enterprise_subscription_service.js  # JS patch
                └── expiration_panel.xml               # XML override
```

## Data Flow

### User Action → Override Response

```
User Interface
     ↓ (click event)
Event Handler
     ↓ (calls method)
Patched Method (gms_web_enterprise_override)
     ↓ (executes)
Notification Service
     ↓ (displays)
User sees notification
     ↓
No external redirect
```

### Original vs Override Comparison

| Layer | Original Behavior | Override Behavior |
|-------|------------------|-------------------|
| UI | Clickable link to odoo.com | Plain text or notification trigger |
| JavaScript | `browser.location = "odoo.com/..."` | `notification.add("Contact admin...")` |
| Network | HTTP redirect to external site | No network request |
| User Experience | Leaves Odoo instance | Stays in Odoo instance |

## Security Implications

### Benefits
- ✓ Prevents accidental navigation to external sites
- ✓ Keeps users within controlled environment
- ✓ No data sent to external servers
- ✓ Maintains session security

### Considerations
- Module must be kept updated with Odoo versions
- Patches must match original method signatures
- XPath expressions must match template structure

## Performance Impact

- **Minimal**: Patches applied once at startup
- **No runtime overhead**: Patched methods execute directly
- **Template merging**: Done during asset compilation
- **Asset size**: +3KB for override code

## Maintenance Workflow

```
Odoo Update Released
         ↓
Check if web_enterprise changed
         ↓
   ┌────┴────┐
   │         │
   NO       YES
   │         │
   │         ↓
   │    Test override compatibility
   │         ↓
   │    Update patches if needed
   │         ↓
   │    Update XPath expressions if needed
   │         ↓
   └────┬────┘
        ↓
   Deploy updated module
        ↓
   Test in staging
        ↓
   Deploy to production
```

## Integration Points

### With web_enterprise
- Patches SubscriptionManager class methods
- Inherits from DatabaseExpirationPanel template
- Loads after web_enterprise in asset bundle

### With notification service
- Uses `@web/core/notification` service
- Displays info-type notifications
- Translatable messages with `_t()`

### With translation system
- All user-facing strings wrapped in `_t()`
- Supports multi-language deployments
- Follows Odoo i18n patterns

## Extensibility

To add custom branding to notifications:

```javascript
patch(SubscriptionManager.prototype, {
    async buy() {
        this.notification.add(
            _t("Please contact SHAAR Support at support@shaar.com"),
            {
                type: "info",
                title: _t("SHAAR License Management")
            }
        );
    }
});
```

To add custom links in template:

```xml
<xpath expr="//span[@class='custom-target']" position="after">
    <a href="mailto:support@shaar.com">Contact SHAAR Support</a>
</xpath>
```

## Version Compatibility

| Odoo Version | Compatible | Notes |
|--------------|-----------|-------|
| 19.0+e | ✓ Yes | Tested and working |
| 18.0 | ✗ No | Different JS module system |
| 17.0 | ✗ No | Different patching mechanism |
| Future 19.x | ? Unknown | May need updates |

## Summary

The module uses Odoo's official extension mechanisms (patching and template inheritance) to non-destructively override web_enterprise behavior. It maintains compatibility with Odoo's architecture while preventing external redirects through runtime method replacement and template modification.
