# GMS Project - Claude Code Context

## ⚠️ CRITICAL: ODOO VERSION - SOURCE OF TRUTH

**THIS PROJECT USES: Odoo 19.0+e-20251007 (Enterprise Edition) ONLY**

- **NEVER** assume APIs from older Odoo versions
- **ALWAYS** verify against Odoo 19 Enterprise documentation
- **This project is NOT compatible with Odoo versions 14, 15, 16, 17, or 18**
- **POS Module**: Uses OWL framework (Odoo Web Library) - completely different from older versions
- **When in doubt**: Search for "Odoo 19" specific documentation or check working examples in the actual Odoo 19 codebase

### 🛑 RULE ZERO: VERIFY FIELDS EXIST BEFORE REFERENCING THEM

**NEVER reference a field name in code, XML data, or validation rules without first confirming it exists in the actual database.**

This rule exists because previous AI sessions wrote code referencing phantom fields (`l10n_latam_identification_type_id`, `l10n_cr_signature_certificate`, `l10n_cr_certificate_expiration`) that do not exist in the database. These caused blocking validation errors in production that were invisible during development.

**Mandatory verification steps:**

1. **Before referencing ANY field on a model**, run:
   ```
   docker compose exec -T db psql -U odoo -d GMS -c \
     "SELECT column_name FROM information_schema.columns WHERE table_name = '<table>' AND column_name = '<field>';"
   ```
2. **If the query returns 0 rows, the field DOES NOT EXIST. Do not use it.**
3. **For related/computed fields**, also verify the underlying stored field exists.
4. **For XML data files** (`data/*.xml`), every `<field name="field_name">some_field</field>` must reference a real database column on the target model.
5. **For validation rules**, the `field_name` value is used in `getattr(record, field_name)` — if the field doesn't exist on the model, the rule will always fail.
6. **Never assume a module is installed.** Check `state` in `ir_module_module`:
   ```
   docker compose exec -T db psql -U odoo -d GMS -c \
     "SELECT name, state FROM ir_module_module WHERE name = '<module_name>';"
   ```

**If you skip this verification and a phantom field causes a runtime error, it is YOUR fault.**

### 🚫 ABSOLUTE CODING RULES - NO EXCEPTIONS

**BEFORE writing ANY code:**

1. ✅ **VERIFY the import path exists in Odoo 19 Enterprise**
   - Use Explore agent to search actual Odoo 19 source code
   - Do NOT trust web tutorials for Odoo 17/18
   - Do NOT assume old patterns still work

2. ✅ **CHECK for Odoo 19-specific patterns**
   - POS popups: Use `Component` + `Dialog` + `makeAwaitable()`, NOT `AbstractAwaitablePopup`
   - POS Order: Import from `@point_of_sale/app/models/pos_order`, NOT `@point_of_sale/app/models/order`
   - POS API: Use `this.pos.selectedOrder`, NOT `this.pos.get_order()`

3. ✅ **SEARCH the Odoo 19 codebase FIRST**
   - Look for working examples in `/opt/odoo/addons/point_of_sale/static/src/`
   - Copy patterns from actual Odoo 19 code
   - Never guess based on older version knowledge

4. ✅ **TEST imports before declaring success**
   - Verify the module loads without "module not found" errors
   - Check browser console for import errors
   - Don't assume it works until tested

**IF YOU SEE web search results mentioning Odoo 17/18:**
- ❌ DO NOT use those patterns
- ✅ Search specifically for "Odoo 19" + your query
- ✅ Or use Explore agent to find correct Odoo 19 implementation

**📋 MANDATORY:** Before writing any code, review: `ODOO-19-CODE-VERIFICATION-CHECKLIST.md`

### Cardinal Rule: Everything Must Feel Native to Odoo

**Our custom features must be indistinguishable from Odoo's own features.** No bolted-on UI, no foreign patterns, no "custom module" feel. A user should never sense they left Odoo.

**Odoo is massive -- almost anything we need already exists somewhere in the codebase.** Before building anything custom, search Odoo's own modules for existing implementations. Reuse patterns, components, and approaches from Odoo's localizations and enterprise modules. Never reinvent what Odoo already solved.

This means:
- **Search before building** -- Find how other Odoo localizations solved the same problem (Mexico, Chile, Ecuador, Brazil, Peru, Saudi Arabia all have POS e-invoicing)
- Use Odoo's existing UI patterns (dialogs, notifications, button states) -- never invent custom ones
- Integrate into existing Odoo flows (PartnerList, PaymentScreen) -- don't create parallel workflows
- Match Odoo's visual language (Bootstrap classes, `fa` icons, spacing) -- don't introduce new CSS unless Odoo has no equivalent
- Follow Odoo's interaction patterns (click disabled button = explain why via dialog) -- don't add inline error text if Odoo doesn't

### Blueprint Modules -- Study These BEFORE Writing POS Code

These Odoo 19 modules solve problems nearly identical to ours. **Read them first, copy their patterns:**

| Module | Path | What to learn from it |
|--------|------|-----------------------|
| **l10n_mx_edi_pos** (Mexico CFDI) | `odoo/addons/l10n_mx_edi_pos/` | POS e-invoice popup, payment validation, partner field loading, `AddInfoPopup` dialog component |
| **l10n_ec_edi_pos** (Ecuador SRI) | `odoo/addons/l10n_ec_edi_pos/` | "Final Consumer" default partner pattern (for gym walk-ins without Factura) |
| **l10n_br_edi_pos** (Brazil NFCe) | `odoo/addons/l10n_br_edi_pos/` | External API integration pattern, cron-based EDI processing |
| **l10n_pe_edi_pos** (Peru) | `odoo/addons/l10n_pe_edi_pos/` | Clean `makeAwaitable()` popup for collecting extra data |
| **partner_autocomplete** | `odoo/addons/partner_autocomplete/` | External API lookup for partner enrichment (adapt for Hacienda cedula API) |

**Key patterns from these blueprints:**

1. **Load partner fields to POS** via `_load_pos_data_fields()`:
   ```python
   def _load_pos_data_fields(self, config):
       result = super()._load_pos_data_fields(config)
       result += ['l10n_cr_economic_activity_id', 'l10n_cr_cedula_verified']
       return result
   ```

2. **Collect invoice metadata** via custom Dialog + `makeAwaitable()` (Mexico's `AddInfoPopup` pattern)

3. **Block payment** when required fields missing by patching `PosStore.pay()` or `PosOrder.setToInvoice()`

4. **Default to "Final Consumer"** for anonymous gym walk-ins (Ecuador's pattern)

### POS Feature Design Checklist

**BEFORE designing or implementing ANY POS feature, ask these questions:**

1. **"How does Odoo 19 POS already solve this?"** -- Search `/opt/odoo/addons/point_of_sale/static/src/` for existing patterns. Read the actual component source. Copy Odoo's exact approach rather than inventing your own.

2. **"What services are available in this component's context?"** -- POS OWL components support `useService("rpc")`, `useService("orm")`, `useService("notification")`, `useService("dialog")`. Verify the specific component you're patching.

3. **"How does the component I'm patching handle its data flow?"** -- Before patching `PartnerList`, `PaymentScreen`, or any POS component, read the actual Odoo 19 source to understand its props, callbacks (`getPayload`, `close`), and data model APIs. Do NOT guess prop names.

4. **"Am I using Odoo 19 data APIs or legacy patterns?"** -- For model operations in POS:
   - Use `useService("orm")` for `orm.call('model', 'method', args)` -- preferred
   - Use `this.rpc('/custom/route', params)` for custom JSON controllers only
   - Do NOT use `/web/dataset/call_kw` -- this is a legacy pattern
   - Use `this.pos.data` / `this.pos.models` for POS-specific data access
   - Never use `window.prompt()` or `window.confirm()` -- use OWL dialogs

5. **"Does my UX match Odoo's native feedback patterns?"** -- Odoo 19 POS uses these specific patterns for user feedback:
   - **Disabled buttons**: CSS class `disabled` (NOT HTML attribute) -- button stays clickable
   - **Explain why blocked**: Override `validateOrder()` / `isOrderValid()` to show `AlertDialog` when user clicks a disabled-looking button
   - **Quick warnings**: `notification.add()` for toast messages
   - **Confirmation flows**: `ConfirmationDialog` with confirm/cancel callbacks
   - **Async dialogs returning data**: `makeAwaitable(this.dialog, ComponentClass, props)`
   - **NEVER**: Inline error text next to buttons, custom modal implementations, or browser alerts

### Odoo 19 POS Verified Patterns (from actual source code)

**Validate button behavior:**
```javascript
// Button uses CSS class, NOT disabled attribute -- it stays clickable
// t-attf-class="{{ order.canBeValidated() ? 'highlight' : 'disabled' }}"
// When clicked while "disabled", validateOrder() runs and shows dialogs explaining why
```

**PartnerList props (verified):**
```javascript
static props = {
    partner: { optional: true, type: [{ value: null }, Object] },
    getPayload: { type: Function },  // Callback: receives selected partner
    close: { type: Function },       // Callback: closes the dialog
};
// Partner creation: this.editPartner() opens partner form
// Partner search: this.pos.data.callRelated("res.partner", "get_new_partner", [...])
// Partner selection: this.props.getPayload(partner); this.props.close();
```

**Dialog patterns:**
```javascript
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
// Alert: this.dialog.add(AlertDialog, { title, body });
// Confirm: this.dialog.add(ConfirmationDialog, { title, body, confirm, cancel });
// Awaitable: const result = await makeAwaitable(this.dialog, MyComponent, props);
```

### Known POS Pitfall: Cedula Lookup

The `pos_cedula_lookup.js` is currently **disabled** in `__manifest__.py` because it violates the native-feel principle. Before re-enabling, it must be rewritten to:
- Integrate into PartnerList's existing Dialog flow (not a bolted-on section above the list)
- Use `useService("orm")` instead of `/web/dataset/call_kw`
- Use `makeAwaitable()` + OWL dialog for email input instead of `window.prompt()`
- Use verified `getPayload`/`close` prop pattern for partner selection
- Use `this.pos.data.callRelated("res.partner", "get_new_partner", [...])` for partner reload

## Tech Stack

- **Odoo Enterprise 19** (19.0+e-20251007) - NOT community, NOT older versions
  - Odoo 19 uses subcommand CLI: `python3 -m odoo server [options]`, `python3 -m odoo shell`, etc.
  - `display_notification` does NOT render HTML in messages -- keep them plain text
  - Hacienda API uses **OAuth2 bearer tokens** (Keycloak IDP), NOT Basic Auth
- **PostgreSQL 13** via Docker
- **Docker Compose** setup: `gms_odoo` + `gms_postgres` containers
- **Database name:** `GMS` (only database -- do not create others)
- **Port:** localhost:8070 -> container 8069

## Custom Module

- `l10n_cr_einvoice` - Costa Rica electronic invoicing for Hacienda
- Mounted at: `/opt/odoo/custom_addons/l10n_cr_einvoice`

## Hacienda API Authentication

The Costa Rica Hacienda API uses OAuth2 Resource Owner Password flow:
- **Sandbox IDP:** `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token` (client_id: `api-stag`)
- **Production IDP:** `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token` (client_id: `api-prod`)
- Credentials and certificate PIN are stored in `docs/Tribu-CR/Credentials.md`

## Docker Commands

- Module update: `docker compose run --rm odoo -d GMS -u l10n_cr_einvoice --stop-after-init --no-http`
- Module install: `docker compose run --rm odoo -d GMS -i l10n_cr_einvoice --stop-after-init --no-http`
- Odoo shell: `docker compose run --rm odoo shell -d GMS --no-http`
- The entrypoint already runs `python3 -m odoo -c /etc/odoo/odoo.conf "$@"` -- do NOT pass `odoo` or `server` as args

## Important: Use Project Documentation First

Before guessing, trial-and-error, or fetching external resources, **always check the project's existing documentation** under `docs/`, `_bmad-output/`, and research directories. This project has extensive reference material including:

- Hacienda v4.4 XSD schemas, annexes, and element structures
- Competitive analysis and implementation guides
- PRD, architecture docs, and epic specifications

When facing schema validation errors or unknown API structures, read the local docs first -- do not iterate through external API error responses one at a time.
