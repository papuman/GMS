# Tech Spec: POS E-Invoice Feedback Notifications

**Status:** approved
**Created:** 2026-02-08
**Source:** UX Design Specification (`_bmad-output/planning-artifacts/ux-design-specification.md`)

## Overview

### Problem
When a cashier enables e-invoice (FE/TE) and completes a POS payment, there is zero feedback about whether Hacienda accepted or rejected the document. The cashier sees "Payment Successful" but has no idea if the e-invoice went through.

### Solution
Add `notification.add()` calls to the ReceiptScreen after order sync completes. The ReceiptScreen already has `this.notification` set up. A new server-side method `get_einvoice_feedback()` returns the notification type and a plain-language Spanish message. Zero custom components — just Odoo's native notification service.

### In Scope
- Green toast on acceptance (auto-dismiss ~4s)
- Red/orange toast on rejection/error with plain-language reason
- Info toast for "still processing" state
- Server-side error message mapping (Hacienda technical → cashier-friendly)

### Out of Scope
- Backend dashboard notifications
- Email/SMS alerts to admins
- Retry UI from POS
- Offline mode handling

## Context for Development

### Reference Files

| File | Role |
|------|------|
| `l10n_cr_einvoice/static/src/js/pos_einvoice.js` | **Primary JS file to modify** — already patches PaymentScreen and PosOrder |
| `l10n_cr_einvoice/models/pos_order.py` | **Primary Python file to modify** — add `get_einvoice_feedback()` method |
| `l10n_cr_einvoice/models/einvoice_document.py` | Reference: `_process_hacienda_response()` sets states and error messages |
| Odoo 19 `receipt_screen.js` | Reference: ReceiptScreen has `this.notification`, uses `this.pos.data.call()` for RPC |

### Key Code Patterns

**ReceiptScreen gets the current order via UUID:**
```javascript
get currentOrder() {
    return this.pos.models["pos.order"].getBy("uuid", this.props.orderUuid);
}
```

**ReceiptScreen already has notification + uses `this.pos.data.call()` for RPC:**
```javascript
this.notification = useService("notification");
// RPC pattern:
await this.pos.data.call("pos.order", "action_send_receipt", [[order.id], ...]);
```

**E-invoice generation is synchronous during `sync_from_ui` → `create()` → `_generate_einvoice_if_requested()`**. By the time ReceiptScreen mounts, Hacienda has already responded.

### Technical Decisions

1. **ReceiptScreen patch (not PaymentScreen):** The PaymentScreen navigates away after sync. ReceiptScreen is where the cashier is looking when they'd want feedback.
2. **ORM call (not field-reading):** Instead of relying on POS data model field loading, we make an explicit `get_einvoice_feedback()` call. This is more reliable and lets the server format the message with full context.
3. **`this.pos.data.call()` (not `useService("orm")`):** Follows Odoo 19 POS pattern exactly (see ReceiptScreen's `_sendReceiptToCustomer`).
4. **Silent fail on error:** If the feedback call fails, don't show anything. Never block the receipt flow.

## Implementation Plan

### Task 1: Server-side `get_einvoice_feedback()` method

**File:** `l10n_cr_einvoice/models/pos_order.py`

Add two methods to `PosOrder`:

```python
def get_einvoice_feedback(self):
    """Return notification data for POS ReceiptScreen."""
    self.ensure_one()
    if not self.l10n_cr_is_einvoice or not self.l10n_cr_einvoice_document_id:
        return {}

    doc = self.l10n_cr_einvoice_document_id
    doc_label = 'Factura Electrónica' if doc.document_type == 'FE' else 'Tiquete Electrónico'

    if doc.state == 'accepted':
        return {'type': 'success', 'message': f'{doc_label} aceptada por Hacienda'}
    elif doc.state == 'rejected':
        reason = self._map_hacienda_error_for_pos(doc.error_message or '')
        return {'type': 'danger', 'message': f'{doc_label} rechazada: {reason}'}
    elif doc.state in ('submitted', 'signed'):
        return {'type': 'info', 'message': f'{doc_label} enviada a Hacienda'}
    elif doc.state == 'error':
        reason = self._map_hacienda_error_for_pos(doc.error_message or '')
        return {'type': 'warning', 'message': f'Error enviando {doc_label}: {reason}'}
    return {}

def _map_hacienda_error_for_pos(self, error_message):
    """Map Hacienda technical errors to plain-language Spanish for cashiers."""
    msg = (error_message or '').lower()

    MAPPING = [
        ('identificacion', 'Falta cédula del cliente'),
        ('receptor', 'Datos del cliente incompletos'),
        ('duplicad', 'Factura duplicada'),
        ('certificado', 'Certificado vencido - contacte administrador'),
        ('firma', 'Error de firma - contacte administrador'),
        ('xml', 'Error interno - contacte administrador'),
        ('esquema', 'Error interno - contacte administrador'),
        ('no disponible', 'Hacienda no disponible - se reintentará'),
        ('timeout', 'Hacienda no disponible - se reintentará'),
        ('connection', 'Sin conexión a Hacienda - se reintentará'),
    ]

    for keyword, friendly_msg in MAPPING:
        if keyword in msg:
            return friendly_msg

    # Default: truncate to 80 chars for POS display
    if error_message and len(error_message) > 80:
        return error_message[:77] + '...'
    return error_message or 'Error desconocido'
```

**Acceptance criteria:**
- Method returns dict with `type` and `message` keys
- Returns empty dict `{}` when no e-invoice
- Maps all known Hacienda error patterns to cashier-friendly Spanish
- Falls back to truncated raw message if no mapping matches

### Task 2: Patch ReceiptScreen in JS

**File:** `l10n_cr_einvoice/static/src/js/pos_einvoice.js`

Add a new patch block for ReceiptScreen:

```javascript
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        onMounted(async () => {
            const order = this.currentOrder;
            if (order && order.l10n_cr_is_einvoice) {
                await this._showEinvoiceFeedback(order);
            }
        });
    },

    async _showEinvoiceFeedback(order) {
        try {
            const result = await this.pos.data.call(
                "pos.order",
                "get_einvoice_feedback",
                [[order.id]]
            );
            if (result && result.message) {
                this.notification.add(result.message, { type: result.type });
            }
        } catch {
            // Silent fail — never block the receipt screen
        }
    },
});
```

**Acceptance criteria:**
- ReceiptScreen shows toast notification after mount when order has e-invoice
- Green toast for accepted, red for rejected, orange for error, blue for processing
- No notification shown for orders without e-invoice
- Errors in feedback call are silently caught — receipt screen works normally

## Notification Types (Odoo native)

| `type` value | Color | Icon | Use case |
|-------------|-------|------|----------|
| `success` | Green | Checkmark | Accepted by Hacienda |
| `danger` | Red | X | Rejected by Hacienda |
| `warning` | Orange | Warning | Submission error |
| `info` | Blue | Info | Still processing |

All auto-dismiss after ~4 seconds (Odoo default). No `sticky: true` needed.

## Testing Strategy

1. **Module load test:** Update module, verify no JS console errors
2. **Manual POS test:** Create order with e-invoice enabled, verify toast appears on receipt
3. **Error case:** Submit with known-bad data, verify rejection toast with plain-language message
