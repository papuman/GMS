# GMS Invoicing & POS - Comprehensive Improvement Plan
## Gym/Fitness Center Optimization

**Date:** December 31, 2025
**Scope:** Two distinct areas requiring improvement
**Reference:** HuliPractice analysis (medical vertical → adapted for gym vertical)
**Goal:** World-class gym management with Costa Rica e-invoicing compliance

---

## Executive Summary: Two Different Worlds

### Area 1: POS (Point of Sale) - FRONTLINE OPERATIONS
**Users:** Front desk staff, trainers, managers
**Use Cases:**
- Member check-ins
- Membership sales/renewals
- Product sales (supplements, merchandise, drinks)
- Class/session bookings
- Quick payments (cash, card, SINPE)
- Issue receipts instantly

**Current State:** Functional but basic
**Goal:** Fast, intuitive, gym-specific POS experience

---

### Area 2: Invoicing Backend - ADMINISTRATIVE CONTROL CENTER
**Users:** Accountants, managers, owners
**Use Cases:**
- Monthly invoicing cycles (recurring memberships)
- Bulk invoice generation
- Tax reports (D-104, D-101, D-151)
- Revenue analytics by service type
- Member payment tracking
- Hacienda compliance management

**Current State:** Standard Odoo accounting
**Goal:** Gym-optimized admin interface with powerful reporting

---

## AREA 1: POS Improvements (Frontline Operations)

### Context: The Gym Front Desk Experience

**Typical Workflow:**
```
6:00 AM - Morning rush
  ├── 20+ members checking in
  ├── 3 new membership signups
  ├── 5 supplement purchases
  └── 2 class bookings

Staff needs:
  ✅ FAST (handle member in < 30 seconds)
  ✅ SIMPLE (minimal clicks)
  ✅ VISUAL (icons, colors, not text)
  ✅ ROBUST (works when internet drops)
```

---

### POS Improvement Plan - 4 Weeks

#### Week 1: Visual Overhaul (Gym-Specific UI)

##### 1.1 Product Categories with Icons (2 hours)
**Current:** Generic product categories
**Problem:** Staff waste time finding items

**Gym-Specific Categories:**
```
┌─────────────────────────────────────────────────┐
│  💪 MEMBRESÍAS    🏋️ CLASES    🥤 SUPLEMENTOS   │
│  👕 MERCHANDISING  🧴 OTROS     ⭐ FAVORITOS    │
└─────────────────────────────────────────────────┘
```

**Implementation:**
```python
# l10n_cr_einvoice/models/pos_category.py

class PosCategory(models.Model):
    _inherit = 'pos.category'

    gym_category_type = fields.Selection([
        ('membership', '💪 Membresías'),
        ('classes', '🏋️ Clases'),
        ('supplements', '🥤 Suplementos'),
        ('merchandise', '👕 Merchandising'),
        ('other', '🧴 Otros'),
    ], string='Tipo Gimnasio')

    icon_image = fields.Binary('Icono', help='Imagen del icono de categoría')
    color_hex = fields.Char('Color', default='#3498db')
```

**POS Screen XML:**
```xml
<!-- Custom POS screen layout -->
<templates>
    <t t-name="CategoryButton">
        <div class="category-button"
             t-att-style="'background-color: ' + category.color_hex">
            <img t-if="category.icon_image"
                 t-att-src="'data:image/png;base64,' + category.icon_image"/>
            <span t-esc="category.name"/>
        </div>
    </t>
</templates>
```

**CSS:**
```scss
.category-button {
    width: 150px;
    height: 120px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    cursor: pointer;
    transition: transform 0.2s;

    &:hover {
        transform: scale(1.05);
    }

    img {
        width: 48px;
        height: 48px;
        margin-bottom: 8px;
    }

    span {
        font-size: 14px;
        font-weight: 600;
        color: white;
        text-align: center;
    }
}
```

**Impact:** ⭐⭐⭐⭐⭐ (30% faster product selection)

---

##### 1.2 Membership Quick Actions (4 hours)
**Current:** Generic "Add Product" flow
**Problem:** Membership sales are multi-step and slow

**Gym-Specific Flow:**
```
┌──────────────────────────────────────────────┐
│  MEMBRESÍAS ACTIVAS                          │
├──────────────────────────────────────────────┤
│  🥇 GOLD      ₡50,000/mes    [Agregar]      │
│  🥈 SILVER    ₡35,000/mes    [Agregar]      │
│  🥉 BASIC     ₡25,000/mes    [Agregar]      │
│  👥 PAREJA    ₡80,000/mes    [Agregar]      │
│  👶 JUVENIL   ₡20,000/mes    [Agregar]      │
└──────────────────────────────────────────────┘
```

**One-Click Membership Sale:**
```javascript
// l10n_cr_einvoice/static/src/js/gym_membership_screen.js

odoo.define('gym_pos.MembershipScreen', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class GymMembershipScreen extends PosComponent {
        async addMembership(membership) {
            // Auto-fill member info if customer selected
            const customer = this.env.pos.get_client();
            if (!customer) {
                this.showPopup('ErrorPopup', {
                    title: 'Cliente requerido',
                    body: 'Seleccione un socio antes de agregar membresía'
                });
                return;
            }

            // Add membership to cart
            const product = this.getMembershipProduct(membership.id);
            const order = this.env.pos.get_order();

            // Add line with special membership properties
            const line = order.add_product(product, {
                price: membership.price,
                extras: {
                    membership_id: membership.id,
                    start_date: new Date(),
                    end_date: this.calculateEndDate(membership.duration),
                    auto_renew: true
                }
            });

            // Auto-apply discount if applicable
            if (membership.has_promotion) {
                line.set_discount(membership.discount_percent);
            }

            // Show confirmation
            this.showNotification(`Membresía ${membership.name} agregada`);
        }

        calculateEndDate(duration_months) {
            const now = new Date();
            return new Date(now.setMonth(now.getMonth() + duration_months));
        }
    }

    Registries.Component.add(GymMembershipScreen);
    return GymMembershipScreen;
});
```

**Impact:** ⭐⭐⭐⭐⭐ (Membership sales 3x faster)

---

##### 1.3 Member Quick Lookup (3 hours)
**Current:** Standard partner search
**Problem:** Slow during rush hours

**Gym-Specific Search:**
```
┌─────────────────────────────────────────────┐
│  🔍  Buscar socio...                        │
│  Nombre, Cédula, Email, o Teléfono          │
├─────────────────────────────────────────────┤
│  Resultados:                                │
│                                             │
│  👤 Laura María Sánchez                     │
│     Cédula: 113170921                       │
│     Membresía: 🥇 GOLD (Activa)            │
│     Vence: 15/01/2026                       │
│     [Seleccionar]                           │
│                                             │
│  👤 Laura Pérez Mora                        │
│     Cédula: 205340876                       │
│     Membresía: ❌ Vencida (30/11/2025)     │
│     [Seleccionar] [Renovar]                 │
└─────────────────────────────────────────────┘
```

**Implementation:**
```python
# Override partner search for POS
class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def gym_member_search(self, query):
        """
        Enhanced search for gym members
        Returns: Member + Active membership status
        """
        domain = [
            '|', '|', '|',
            ('name', 'ilike', query),
            ('vat', 'ilike', query),
            ('email', 'ilike', query),
            ('phone', 'ilike', query),
            ('is_gym_member', '=', True)
        ]

        partners = self.search(domain, limit=10)

        results = []
        for partner in partners:
            # Get active membership
            membership = self.env['gym.membership'].search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['active', 'expired'])
            ], limit=1, order='end_date desc')

            results.append({
                'id': partner.id,
                'name': partner.name,
                'vat': partner.vat,
                'email': partner.email,
                'phone': partner.phone,
                'membership': {
                    'name': membership.membership_type_id.name if membership else None,
                    'state': membership.state if membership else None,
                    'end_date': membership.end_date if membership else None,
                    'is_expired': membership.is_expired if membership else True,
                } if membership else None
            })

        return results
```

**Visual Indicators:**
```javascript
// Show membership status with color
getMembershipBadge(member) {
    if (!member.membership) {
        return '<span class="badge badge-secondary">Sin membresía</span>';
    }

    if (member.membership.state === 'active') {
        return '<span class="badge badge-success">✓ Activa</span>';
    }

    if (member.membership.is_expired) {
        return '<span class="badge badge-danger">❌ Vencida</span>';
    }
}
```

**Impact:** ⭐⭐⭐⭐⭐ (50% faster member lookup)

---

#### Week 2: Offline Robustness (Already Good, Enhance Further)

##### 2.1 Enhanced Offline Queue Display (2 hours)
**Current:** Basic queue counter
**Goal:** Visual queue management

**Offline Queue Widget:**
```
┌────────────────────────────────────┐
│  🔴 MODO OFFLINE                   │
│                                    │
│  📱 3 facturas en cola             │
│                                    │
│  Última sincronización:            │
│  Hace 2 minutos                    │
│                                    │
│  [Reintentar ahora]                │
│                                    │
│  Cola:                             │
│  ⏳ Factura #001 - ₡50,000        │
│  ⏳ Factura #002 - ₡35,000        │
│  ⏳ Factura #003 - ₡25,000        │
└────────────────────────────────────┘
```

**Implementation:**
```javascript
// POS offline queue widget
class OfflineQueueWidget extends PosComponent {
    get queueItems() {
        return this.env.pos.db.get_offline_queue();
    }

    get connectionStatus() {
        return this.env.pos.is_online ? 'online' : 'offline';
    }

    get lastSyncTime() {
        const lastSync = this.env.pos.db.get_last_sync_time();
        return moment(lastSync).fromNow();
    }

    async retrySync() {
        this.showPopup('LoadingPopup', {
            title: 'Sincronizando...',
            body: 'Enviando facturas pendientes a Hacienda'
        });

        const result = await this.rpc({
            model: 'pos.order',
            method: 'sync_offline_invoices',
        });

        this.closePopup();

        if (result.success > 0) {
            this.showPopup('SuccessPopup', {
                title: '✓ Sincronización completa',
                body: `${result.success} facturas enviadas correctamente`
            });
        }

        if (result.errors > 0) {
            this.showPopup('ErrorPopup', {
                title: '⚠️ Algunas facturas fallaron',
                body: `${result.errors} facturas no se pudieron enviar. Revise la cola de errores.`
            });
        }
    }
}
```

**Impact:** ⭐⭐⭐⭐ (Better offline visibility)

---

##### 2.2 Print Receipt Without QR (Offline Mode) (3 hours)
**Current:** Receipt waits for Hacienda approval
**Problem:** Can't give customer receipt when offline

**Offline Receipt:**
```
═══════════════════════════════
     GYM TEST CR
═══════════════════════════════

RECIBO PROVISIONAL
(Pendiente aprobación Hacienda)

Consecutivo temporal: TEMP-001
Fecha: 31/12/2025 18:45

Cliente: Laura María Sánchez
Cédula: 113170921

PRODUCTOS
───────────────────────────────
Membresía Gold        ₡50,000.00
Proteína Whey         ₡25,000.00
───────────────────────────────
Subtotal:            ₡75,000.00
IVA 13%:              ₡9,750.00
───────────────────────────────
TOTAL:               ₡84,750.00

PAGO: Efectivo       ₡84,750.00

═══════════════════════════════

⚠️ FACTURA ELECTRÓNICA PENDIENTE

Este recibo será reemplazado por
la factura electrónica oficial
cuando la conexión se restablezca.

Su factura será enviada por email
a: lau_sanleo@hotmail.com

═══════════════════════════════
Gracias por su preferencia!
═══════════════════════════════
```

**Implementation:**
```python
# Generate provisional receipt when offline
def _generate_provisional_receipt(self):
    """
    Generate printable receipt for offline transactions
    To be replaced with official e-invoice when online
    """
    return {
        'type': 'provisional',
        'consecutive': f"TEMP-{self.id:06d}",
        'customer': self.partner_id.name,
        'vat': self.partner_id.vat,
        'date': fields.Datetime.now(),
        'lines': self._get_receipt_lines(),
        'totals': self._get_receipt_totals(),
        'payment_method': self.payment_method_id.name,
        'warning_message': 'FACTURA ELECTRÓNICA PENDIENTE - '
                          'Será enviada por email cuando se restablezca la conexión'
    }
```

**Impact:** ⭐⭐⭐⭐⭐ (Critical for offline operation)

---

#### Week 3: Gym-Specific Features

##### 3.1 Class/Session Quick Add (4 hours)
**Use Case:** Member books a personal training session at front desk

**Quick Add Screen:**
```
┌────────────────────────────────────────┐
│  SESIONES Y CLASES                     │
├────────────────────────────────────────┤
│  🏋️ Entrenamiento Personal             │
│     ₡15,000/sesión    [Agregar]        │
│                                        │
│  🧘 Clase de Yoga                      │
│     ₡8,000/clase      [Agregar]        │
│                                        │
│  🤸 CrossFit Drop-in                   │
│     ₡12,000/clase     [Agregar]        │
│                                        │
│  💆 Masaje Deportivo                   │
│     ₡20,000/sesión    [Agregar]        │
└────────────────────────────────────────┘
```

**Modal for Details:**
```
Cuando hace clic [Agregar]:

┌────────────────────────────────────────┐
│  Entrenamiento Personal                │
├────────────────────────────────────────┤
│  Entrenador:  [Juan Pérez    ▼]       │
│  Fecha:       [01/01/2026    📅]      │
│  Hora:        [08:00 AM      🕐]      │
│  Duración:    [60 minutos    ▼]       │
│                                        │
│  Precio: ₡15,000                       │
│                                        │
│  [Cancelar]        [Agregar al carrito]│
└────────────────────────────────────────┘
```

**Backend:**
```python
class GymSession(models.Model):
    _name = 'gym.session'
    _description = 'Gym Session/Class Booking'

    partner_id = fields.Many2one('res.partner', 'Member', required=True)
    session_type = fields.Selection([
        ('personal_training', 'Entrenamiento Personal'),
        ('yoga', 'Yoga'),
        ('crossfit', 'CrossFit'),
        ('massage', 'Masaje Deportivo'),
    ], required=True)

    trainer_id = fields.Many2one('hr.employee', 'Trainer')
    session_date = fields.Datetime('Fecha/Hora', required=True)
    duration_minutes = fields.Integer('Duración (min)', default=60)

    price = fields.Monetary('Precio', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # Link to POS order line
    pos_order_line_id = fields.Many2one('pos.order.line', 'Línea POS')

    state = fields.Selection([
        ('booked', 'Reservada'),
        ('confirmed', 'Confirmada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ], default='booked')
```

**Impact:** ⭐⭐⭐⭐ (Streamlines class/session sales)

---

##### 3.2 Supplement Inventory Quick View (2 hours)
**Use Case:** Check if protein powder is in stock before selling

**Stock Indicator in POS:**
```
┌────────────────────────────────────────┐
│  SUPLEMENTOS                           │
├────────────────────────────────────────┤
│  Proteína Whey 2kg         ₡25,000    │
│  Stock: ✅ 15 unidades                 │
│  [Agregar]                             │
│                                        │
│  Creatina Monohidrato      ₡18,000    │
│  Stock: ⚠️ 3 unidades (bajo)           │
│  [Agregar]                             │
│                                        │
│  Pre-Workout Extreme       ₡22,000    │
│  Stock: ❌ Agotado                     │
│  [No disponible]                       │
└────────────────────────────────────────┘
```

**Real-time Stock in POS:**
```javascript
class ProductCard extends PosComponent {
    get stockLevel() {
        const product = this.props.product;
        const stock = this.env.pos.db.get_stock_by_product_id(product.id);

        if (stock <= 0) {
            return {
                level: 'out',
                text: '❌ Agotado',
                class: 'stock-out'
            };
        } else if (stock <= product.stock_warning_level) {
            return {
                level: 'low',
                text: `⚠️ ${stock} unidades (bajo)`,
                class: 'stock-low'
            };
        } else {
            return {
                level: 'ok',
                text: `✅ ${stock} unidades`,
                class: 'stock-ok'
            };
        }
    }
}
```

**Impact:** ⭐⭐⭐ (Prevents selling out-of-stock items)

---

#### Week 4: Payment Shortcuts

##### 4.1 Common Payment Presets (3 hours)
**Use Case:** Most memberships are exactly ₡50,000 (Gold) or ₡35,000 (Silver)

**Quick Payment Buttons:**
```
┌────────────────────────────────────────┐
│  TOTAL: ₡50,000                        │
├────────────────────────────────────────┤
│  PAGOS RÁPIDOS:                        │
│                                        │
│  [₡50,000]  [₡35,000]  [₡25,000]      │
│  [₡100,000] [₡200,000] [Otro]         │
│                                        │
│  MÉTODO:                               │
│  [💵 Efectivo] [💳 Tarjeta] [📱 SINPE] │
└────────────────────────────────────────┘
```

**One-Click Payment:**
```javascript
// Quick payment buttons
class QuickPaymentScreen extends PosComponent {
    async payWithPreset(amount) {
        const order = this.env.pos.get_order();

        // Set payment amount
        const payment_line = order.add_paymentline(
            this.env.pos.payment_methods_by_id[this.selectedPaymentMethod]
        );
        payment_line.set_amount(amount);

        // If exact amount, finalize immediately
        if (amount === order.get_total_with_tax()) {
            await this.validateOrder();
        }
    }

    get commonAmounts() {
        // Get most common membership prices
        return [
            50000,  // Gold
            35000,  // Silver
            25000,  // Basic
            100000, // Pareja
            200000  // Semestral adelantado
        ];
    }
}
```

**Impact:** ⭐⭐⭐⭐ (2x faster payment processing)

---

##### 4.2 SINPE Móvil Confirmation Flow (4 hours)
**Use Case:** Customer pays via SINPE, staff needs to verify

**SINPE Verification Screen:**
```
┌────────────────────────────────────────┐
│  PAGO SINPE MÓVIL                      │
├────────────────────────────────────────┤
│  Total a pagar: ₡50,000                │
│                                        │
│  Número SINPE gimnasio:                │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓        │
│  ┃  8888-8888                 ┃        │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛        │
│  [Copiar número]                       │
│                                        │
│  ¿Cliente realizó el pago?             │
│  Verificar en app SINPE                │
│                                        │
│  Referencia/Comentario (opcional):     │
│  [_____________________________]       │
│                                        │
│  [Cancelar]  [✓ Pago confirmado]      │
└────────────────────────────────────────┘
```

**After confirmation:**
```
✓ Pago SINPE registrado

Referencia: Laura-Memb-Gold
Monto: ₡50,000
Verificado por: Maria (Recepción)

[Continuar con factura]
```

**Backend:**
```python
class PosPayment(models.Model):
    _inherit = 'pos.payment'

    sinpe_reference = fields.Char('Referencia SINPE')
    sinpe_verified_by = fields.Many2one('res.users', 'Verificado por')
    sinpe_verified_at = fields.Datetime('Fecha verificación')

    def verify_sinpe_payment(self, reference, verified_by):
        """
        Manual verification of SINPE payment
        (Until Tilopay integration in Phase 2)
        """
        self.write({
            'sinpe_reference': reference,
            'sinpe_verified_by': verified_by,
            'sinpe_verified_at': fields.Datetime.now(),
            'payment_status': 'verified'
        })

        # Auto-create payment confirmation email
        if self.partner_id.email:
            self._send_sinpe_confirmation_email()
```

**Impact:** ⭐⭐⭐⭐⭐ (Critical for CR market - SINPE is #1 payment method)

---

## AREA 2: Invoicing Backend (Administrative Control Center)

### Context: Monthly Invoicing Operations

**Typical Workflow:**
```
End of month (28-31):
  ├── Generate 200+ recurring membership invoices
  ├── Send bulk emails to all members
  ├── Track which invoices are paid
  ├── Follow up on late payments
  ├── Generate tax reports for accountant
  └── Analyze revenue by membership type

Accountant needs:
  ✅ BULK OPERATIONS (not one-by-one)
  ✅ CLEAR REPORTS (D-104, D-101, D-151)
  ✅ FILTERS (find unpaid invoices fast)
  ✅ AUTOMATION (recurring invoices)
```

---

### Backend Improvement Plan - 4 Weeks

#### Week 1: Critical Workflow Fixes (From HuliPractice Analysis)

##### 1.1 Invoice Void/Cancel with Gym Context (8 hours)
**Use Case:** Member cancels membership, need to refund

**Void Workflow:**
```
Member: "Necesito cancelar mi membresía por mudanza"

Manager opens invoice:
  ├── Invoice #FE-00234
  ├── Member: Juan Pérez
  ├── Membresía Gold - ₡50,000
  ├── Status: ✓ Aprobado por Hacienda
  └── Paid: Yes

Manager clicks [Anular y Reembolsar]
  ↓
Wizard opens:

┌────────────────────────────────────────┐
│  Anular Factura y Reembolsar           │
├────────────────────────────────────────┤
│  Factura: FE-00234                     │
│  Cliente: Juan Pérez                   │
│  Monto: ₡50,000                        │
│                                        │
│  Razón de anulación:                   │
│  ○ Cancelación de membresía            │
│  ○ Error en facturación                │
│  ○ Devolución solicitada               │
│  ○ Otro: [_______________]            │
│                                        │
│  Método de reembolso:                  │
│  ○ Efectivo                            │
│  ○ Transferencia bancaria              │
│  ○ Crédito para futuras compras        │
│                                        │
│  ☑ Cancelar membresía activa           │
│  ☑ Enviar email de confirmación        │
│                                        │
│  [Cancelar]     [Procesar anulación]  │
└────────────────────────────────────────┘

Process:
  1. Create Nota de Crédito (100% amount)
  2. Submit to Hacienda
  3. Cancel membership (if selected)
  4. Record refund payment
  5. Send confirmation email
  6. Mark original invoice as "Anulada"
```

**Implementation:**
```python
class EinvoiceDocument(models.Model):
    _inherit = 'l10n_cr.einvoice.document'

    def action_void_with_refund(self):
        """
        Gym-specific void workflow:
        - Create credit note
        - Cancel membership if applicable
        - Process refund
        - Email confirmations
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gym.invoice.void.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount_total,
            }
        }

class GymInvoiceVoidWizard(models.TransientModel):
    _name = 'gym.invoice.void.wizard'

    invoice_id = fields.Many2one('l10n_cr.einvoice.document', required=True)
    partner_id = fields.Many2one('res.partner', required=True)
    amount = fields.Monetary('Monto', required=True)
    currency_id = fields.Many2one('res.currency')

    void_reason = fields.Selection([
        ('membership_cancel', 'Cancelación de membresía'),
        ('billing_error', 'Error en facturación'),
        ('customer_request', 'Devolución solicitada'),
        ('other', 'Otro'),
    ], required=True)

    void_reason_other = fields.Char('Especifique')

    refund_method = fields.Selection([
        ('cash', 'Efectivo'),
        ('transfer', 'Transferencia bancaria'),
        ('credit', 'Crédito para futuras compras'),
    ], required=True)

    cancel_membership = fields.Boolean('Cancelar membresía activa', default=True)
    send_confirmation_email = fields.Boolean('Enviar email', default=True)

    def action_process_void(self):
        """Execute void workflow"""
        # 1. Create credit note
        credit_note = self.invoice_id._create_credit_note(
            reason=self.void_reason,
            reason_detail=self.void_reason_other
        )

        # 2. Submit to Hacienda
        credit_note.submit_to_hacienda()

        # 3. Cancel membership if selected
        if self.cancel_membership:
            membership = self.env['gym.membership'].search([
                ('partner_id', '=', self.partner_id.id),
                ('invoice_id', '=', self.invoice_id.id),
                ('state', '=', 'active')
            ], limit=1)

            if membership:
                membership.action_cancel(
                    reason=f"Factura anulada: {self.void_reason}"
                )

        # 4. Record refund
        self._create_refund_payment()

        # 5. Send confirmation email
        if self.send_confirmation_email:
            self._send_void_confirmation_email()

        # 6. Mark original as void
        self.invoice_id.write({
            'state': 'void',
            'void_reason': self.void_reason,
            'void_date': fields.Date.today(),
            'credit_note_id': credit_note.id,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✓ Factura anulada',
                'message': f'Nota de crédito #{credit_note.consecutive} creada. '
                          f'Reembolso de ₡{self.amount:,.0f} procesado.',
                'type': 'success',
                'sticky': False,
            }
        }
```

**Impact:** ⭐⭐⭐⭐⭐ (BLOCKING - must have before launch)

---

##### 1.2 Preview Before Submit (Gym Context) (4 hours)
**Use Case:** Verify membership invoice is correct before sending 200+ emails

**Preview Wizard:**
```
┌────────────────────────────────────────┐
│  Vista Previa - Factura Membresía     │
├────────────────────────────────────────┤
│                                        │
│  [PDF Preview displays here]           │
│                                        │
│  Cliente: Laura María Sánchez          │
│  Membresía: 🥇 GOLD                    │
│  Período: 01/01/2026 - 31/01/2026     │
│  Monto: ₡50,000 + IVA (₡6,500)        │
│  Total: ₡56,500                        │
│                                        │
│  ☑ Todo se ve correcto                 │
│                                        │
│  Acciones después de envío:            │
│  ☑ Enviar por email automáticamente    │
│  ☑ Generar PDF para archivo            │
│  ☐ Programar recordatorio de pago      │
│                                        │
│  [← Cancelar]      [Enviar a Hacienda →]│
└────────────────────────────────────────┘
```

**Implementation:**
```python
class GymInvoicePreviewWizard(models.TransientModel):
    _name = 'gym.invoice.preview.wizard'

    invoice_id = fields.Many2one('l10n_cr.einvoice.document', required=True)
    pdf_preview = fields.Binary('Preview PDF', compute='_compute_preview_pdf')

    auto_send_email = fields.Boolean('Enviar por email', default=True)
    generate_pdf = fields.Boolean('Generar PDF', default=True)
    schedule_payment_reminder = fields.Boolean('Recordatorio de pago', default=False)
    reminder_days = fields.Integer('Días para recordatorio', default=7)

    @api.depends('invoice_id')
    def _compute_preview_pdf(self):
        for wizard in self:
            wizard.pdf_preview = wizard.invoice_id._generate_pdf_preview()

    def action_confirm_and_submit(self):
        """Submit after preview confirmation"""
        # Submit to Hacienda
        self.invoice_id.submit_to_hacienda()

        # Post-submission actions
        if self.auto_send_email and self.invoice_id.hacienda_state == 'accepted':
            self.invoice_id.send_einvoice_email()

        if self.schedule_payment_reminder:
            self.invoice_id._schedule_payment_reminder(days=self.reminder_days)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✓ Factura enviada',
                'message': f'Factura #{self.invoice_id.consecutive} enviada a Hacienda',
                'type': 'success',
            }
        }
```

**Impact:** ⭐⭐⭐⭐⭐ (Prevents errors in bulk operations)

---

##### 1.3 CR Tax Reports (D-104, D-101, D-151) (8 hours)
**Use Case:** Accountant needs to file quarterly VAT report

**Tax Report Menu:**
```
┌────────────────────────────────────────┐
│  REPORTES HACIENDA                     │
├────────────────────────────────────────┤
│                                        │
│  📊 IVA D-104 (Trimestral)             │
│     Reporte de IVA para Hacienda       │
│     Último generado: Q3 2025           │
│     [Generar reporte]                  │
│                                        │
│  📊 Renta D-101 (Anual)                │
│     Declaración de renta               │
│     Último: 2024                       │
│     [Generar reporte]                  │
│                                        │
│  📊 Hacienda D-151 (Mensual)           │
│     Reporte de ventas mensuales        │
│     Último: Diciembre 2025             │
│     [Generar reporte]                  │
│                                        │
│  📈 Resumen Anual                      │
│     Todas las facturas 2025            │
│     [Ver resumen]                      │
└────────────────────────────────────────┘
```

**Report Generation Wizard:**
```
Click [Generar reporte] for D-104:

┌────────────────────────────────────────┐
│  Generar Reporte IVA D-104             │
├────────────────────────────────────────┤
│  Período:                              │
│  ○ Q1 2026 (Ene-Mar)                   │
│  ○ Q2 2026 (Abr-Jun)                   │
│  ● Q4 2025 (Oct-Dic)  ← Selected       │
│  ○ Personalizado: [____] a [____]     │
│                                        │
│  Filtros:                              │
│  ☑ Solo facturas aprobadas             │
│  ☐ Incluir notas de crédito            │
│  ☑ Agrupar por tasa de IVA             │
│                                        │
│  Formato de salida:                    │
│  ☑ PDF                                 │
│  ☑ Excel                               │
│  ☑ XML (para envío electrónico)        │
│                                        │
│  [Cancelar]        [Generar reporte]  │
└────────────────────────────────────────┘
```

**Implementation:**
```python
class HaciendaD104Report(models.AbstractModel):
    _name = 'report.l10n_cr_einvoice.hacienda_d104'
    _description = 'Reporte IVA D-104 para Hacienda'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Generate D-104 VAT report for Hacienda filing
        """
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        include_credit_notes = data.get('include_credit_notes', False)

        # Get all accepted invoices in period
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('hacienda_state', '=', 'accepted'),
            ('document_type', 'in', ['FE', 'TE']),
        ]

        invoices = self.env['l10n_cr.einvoice.document'].search(domain)

        # Calculate totals by tax rate
        tax_summary = {}
        for invoice in invoices:
            for line in invoice.line_ids:
                tax_rate = line.tax_ids.amount if line.tax_ids else 0

                if tax_rate not in tax_summary:
                    tax_summary[tax_rate] = {
                        'base': 0,
                        'tax': 0,
                        'total': 0,
                        'invoice_count': 0,
                    }

                tax_summary[tax_rate]['base'] += line.price_subtotal
                tax_summary[tax_rate]['tax'] += line.price_tax
                tax_summary[tax_rate]['total'] += line.price_total
                tax_summary[tax_rate]['invoice_count'] += 1

        # Get credit notes if included
        credit_notes = []
        if include_credit_notes:
            credit_domain = domain + [('document_type', '=', 'NC')]
            credit_notes = self.env['l10n_cr.einvoice.document'].search(credit_domain)

        # Calculate net IVA due
        total_tax_collected = sum(s['tax'] for s in tax_summary.values())
        total_tax_credit = sum(cn.amount_tax for cn in credit_notes)
        net_iva_due = total_tax_collected - total_tax_credit

        return {
            'doc_ids': docids,
            'doc_model': 'l10n_cr.einvoice.document',
            'date_from': date_from,
            'date_to': date_to,
            'company': self.env.company,
            'invoices': invoices,
            'credit_notes': credit_notes,
            'tax_summary': tax_summary,
            'total_tax_collected': total_tax_collected,
            'total_tax_credit': total_tax_credit,
            'net_iva_due': net_iva_due,
            'currency': self.env.company.currency_id,
        }
```

**QWeb Report Template:**
```xml
<template id="report_hacienda_d104_document">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="o">
            <div class="page">
                <h2>Declaración IVA D-104</h2>
                <h3>Ministerio de Hacienda - Costa Rica</h3>

                <!-- Company Info -->
                <div class="row mt-4">
                    <div class="col-6">
                        <strong><span t-field="company.name"/></strong><br/>
                        Cédula Jurídica: <span t-field="company.vat"/><br/>
                        Período: <span t-esc="date_from"/> - <span t-esc="date_to"/>
                    </div>
                </div>

                <!-- Tax Summary Table -->
                <table class="table table-sm mt-4">
                    <thead>
                        <tr>
                            <th>Tasa IVA</th>
                            <th>Base Imponible</th>
                            <th>IVA Cobrado</th>
                            <th># Facturas</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="tax_summary.items()" t-as="tax_item">
                            <tr>
                                <td><span t-esc="tax_item[0]"/>%</td>
                                <td class="text-right">
                                    <span t-esc="tax_item[1]['base']"
                                          t-options="{'widget': 'monetary', 'display_currency': currency}"/>
                                </td>
                                <td class="text-right">
                                    <span t-esc="tax_item[1]['tax']"
                                          t-options="{'widget': 'monetary', 'display_currency': currency}"/>
                                </td>
                                <td class="text-right"><span t-esc="tax_item[1]['invoice_count']"/></td>
                            </tr>
                        </t>
                        <tr class="font-weight-bold">
                            <td>TOTAL IVA COBRADO</td>
                            <td></td>
                            <td class="text-right">
                                <span t-esc="total_tax_collected"
                                      t-options="{'widget': 'monetary', 'display_currency': currency}"/>
                            </td>
                            <td></td>
                        </tr>
                    </tbody>
                </table>

                <!-- Credit Notes -->
                <t t-if="credit_notes">
                    <h4 class="mt-4">Notas de Crédito</h4>
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Consecutivo</th>
                                <th>Fecha</th>
                                <th>Cliente</th>
                                <th>IVA Creditado</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="credit_notes" t-as="cn">
                                <tr>
                                    <td><span t-esc="cn.consecutive"/></td>
                                    <td><span t-esc="cn.date"/></td>
                                    <td><span t-esc="cn.partner_id.name"/></td>
                                    <td class="text-right">
                                        <span t-esc="cn.amount_tax"
                                              t-options="{'widget': 'monetary', 'display_currency': currency}"/>
                                    </td>
                                </tr>
                            </t>
                            <tr class="font-weight-bold">
                                <td colspan="3">TOTAL CRÉDITO IVA</td>
                                <td class="text-right">
                                    <span t-esc="total_tax_credit"
                                          t-options="{'widget': 'monetary', 'display_currency': currency}"/>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </t>

                <!-- Net IVA Due -->
                <div class="row mt-4">
                    <div class="col-12 text-right">
                        <h3>
                            IVA NETO A PAGAR:
                            <span t-esc="net_iva_due"
                                  t-options="{'widget': 'monetary', 'display_currency': currency}"
                                  class="text-success"/>
                        </h3>
                    </div>
                </div>
            </div>
        </t>
    </t>
</template>
```

**Impact:** ⭐⭐⭐⭐⭐ (CRITICAL for compliance)

---

#### Week 2: Bulk Operations (Gym-Specific)

##### 2.1 Recurring Membership Invoice Generation (6 hours)
**Use Case:** Generate 200 membership invoices on the 1st of each month

**Bulk Generation Wizard:**
```
Invoicing > Recurring Invoices > [Generate Monthly Invoices]

┌────────────────────────────────────────┐
│  Generar Facturas Recurrentes          │
├────────────────────────────────────────┤
│  Período: Enero 2026                   │
│                                        │
│  Membresías activas: 187               │
│  ├─ Gold: 65 socios                    │
│  ├─ Silver: 89 socios                  │
│  └─ Basic: 33 socios                   │
│                                        │
│  Fecha de facturación: 01/01/2026      │
│  Fecha de vencimiento: 10/01/2026      │
│                                        │
│  Opciones:                             │
│  ☑ Enviar emails automáticamente        │
│  ☑ Aplicar descuentos configurados      │
│  ☑ Incluir solo membresías activas      │
│  ☐ Generar borrador (no enviar)        │
│                                        │
│  Total a facturar: ₡8,450,000          │
│                                        │
│  [Cancelar]    [Generar 187 facturas] │
└────────────────────────────────────────┘

Processing:
  ⏳ Generando facturas... (15/187)
  [████████░░░░░░░░░░░░░░] 8%

  Tiempo estimado: 2 minutos

After completion:
  ✓ 187 facturas generadas
  ✓ 187 emails enviados
  ✓ 0 errores

  [Ver facturas generadas]
```

**Implementation:**
```python
class RecurringInvoiceGenerator(models.TransientModel):
    _name = 'gym.recurring.invoice.generator'

    period_month = fields.Selection([
        ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'),
        # ... all months
    ], required=True)
    period_year = fields.Integer('Año', required=True, default=lambda self: fields.Date.today().year)

    invoice_date = fields.Date('Fecha factura', required=True)
    due_date = fields.Date('Fecha vencimiento', required=True)

    auto_send_email = fields.Boolean('Enviar emails', default=True)
    apply_discounts = fields.Boolean('Aplicar descuentos', default=True)
    only_active = fields.Boolean('Solo activas', default=True)
    create_draft = fields.Boolean('Generar borrador', default=False)

    membership_count = fields.Integer('Membresías', compute='_compute_membership_count')
    estimated_total = fields.Monetary('Total estimado', compute='_compute_estimated_total')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.depends('period_month', 'period_year', 'only_active')
    def _compute_membership_count(self):
        for wizard in self:
            domain = [('state', '=', 'active')] if wizard.only_active else []
            wizard.membership_count = self.env['gym.membership'].search_count(domain)

    @api.depends('membership_count')
    def _compute_estimated_total(self):
        for wizard in self:
            memberships = self.env['gym.membership'].search([
                ('state', '=', 'active')
            ] if wizard.only_active else [])
            wizard.estimated_total = sum(m.monthly_price for m in memberships)

    def action_generate_invoices(self):
        """
        Generate recurring invoices for all active memberships
        """
        memberships = self.env['gym.membership'].search([
            ('state', '=', 'active')
        ] if self.only_active else [])

        invoices_created = []
        errors = []

        for i, membership in enumerate(memberships):
            try:
                # Create invoice
                invoice = self.env['l10n_cr.einvoice.document'].create({
                    'partner_id': membership.partner_id.id,
                    'date': self.invoice_date,
                    'invoice_date_due': self.due_date,
                    'document_type': 'FE',
                    'line_ids': [(0, 0, {
                        'product_id': membership.membership_type_id.product_id.id,
                        'name': f"Membresía {membership.membership_type_id.name} - "
                               f"{self.period_month}/{self.period_year}",
                        'quantity': 1,
                        'price_unit': membership.monthly_price,
                        'tax_ids': [(6, 0, membership.membership_type_id.product_id.taxes_id.ids)],
                    })],
                    'membership_id': membership.id,
                })

                # Apply discount if configured
                if self.apply_discounts and membership.discount_percent:
                    invoice.line_ids[0].discount = membership.discount_percent

                # Submit to Hacienda (unless draft mode)
                if not self.create_draft:
                    invoice.submit_to_hacienda()

                    # Send email if auto-send enabled
                    if self.auto_send_email and invoice.hacienda_state == 'accepted':
                        invoice.send_einvoice_email()

                invoices_created.append(invoice)

                # Update progress (every 10 invoices)
                if i % 10 == 0:
                    self.env.cr.commit()  # Commit progress

            except Exception as e:
                errors.append({
                    'membership': membership,
                    'error': str(e)
                })

        # Show results
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gym.recurring.invoice.result',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoices_created': len(invoices_created),
                'default_errors_count': len(errors),
                'default_invoice_ids': [(6, 0, [inv.id for inv in invoices_created])],
            }
        }
```

**Impact:** ⭐⭐⭐⭐⭐ (Saves 4-6 hours per month!)

---

##### 2.2 Bulk Actions on Invoice List (4 hours)
**Use Case:** Select 20 unpaid invoices and send reminder emails

**Enhanced List View:**
```
┌────────────────────────────────────────────────────────────┐
│  FACTURAS ELECTRÓNICAS                                     │
├────────────────────────────────────────────────────────────┤
│  [🔍 Filtros ▼]  [☑ 15 seleccionadas]  [Acciones ▼]      │
│                                                            │
│  Acciones disponibles:                                     │
│  ├─ Enviar recordatorio de pago (email)                   │
│  ├─ Marcar como pagadas                                   │
│  ├─ Exportar a Excel                                      │
│  ├─ Generar reporte PDF consolidado                       │
│  └─ Aplicar etiqueta                                      │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  ☑ #FE-001  Laura Sánchez    ₡56,500  ⚠️ Vencida 5 días  │
│  ☑ #FE-002  Juan Pérez       ₡40,400  ⚠️ Vencida 3 días  │
│  ☑ #FE-003  María González   ₡30,100  ⚠️ Vence hoy       │
│  ☐ #FE-004  Carlos Mora      ₡56,500  ✓ Pagada           │
└────────────────────────────────────────────────────────────┘

Click [Enviar recordatorio]:

┌────────────────────────────────────────┐
│  Enviar Recordatorio de Pago           │
├────────────────────────────────────────┤
│  Facturas seleccionadas: 15            │
│                                        │
│  Plantilla de email:                   │
│  [Recordatorio amigable ▼]             │
│                                        │
│  Vista previa:                         │
│  ┌──────────────────────────────────┐ │
│  │ Estimado Juan,                   │ │
│  │                                  │ │
│  │ Tu membresía vence en 3 días.   │ │
│  │ Monto: ₡40,400                   │ │
│  │                                  │ │
│  │ [Pagar ahora]                    │ │
│  └──────────────────────────────────┘ │
│                                        │
│  [Cancelar]      [Enviar 15 emails]   │
└────────────────────────────────────────┘
```

**Implementation:**
```python
class EinvoiceDocument(models.Model):
    _inherit = 'l10n_cr.einvoice.document'

    def action_send_payment_reminder_bulk(self):
        """
        Send payment reminder emails to selected invoices
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gym.payment.reminder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_ids': [(6, 0, self.ids)],
                'default_invoice_count': len(self.ids),
            }
        }

    def action_mark_paid_bulk(self):
        """
        Bulk mark invoices as paid
        (With confirmation wizard)
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gym.mark.paid.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_ids': [(6, 0, self.ids)],
            }
        }

    def action_export_excel_bulk(self):
        """Export selected invoices to Excel"""
        return self.env.ref('l10n_cr_einvoice.invoice_export_xlsx').report_action(self)

    def action_apply_tag_bulk(self):
        """Apply tag to multiple invoices"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gym.apply.tag.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_ids': [(6, 0, self.ids)],
            }
        }
```

**Add to tree view:**
```xml
<record id="view_einvoice_document_tree_gym" model="ir.ui.view">
    <field name="name">einvoice.document.tree.gym</field>
    <field name="model">l10n_cr.einvoice.document</field>
    <field name="arch" type="xml">
        <tree multi_edit="1">
            <!-- Standard fields -->
            <field name="consecutive"/>
            <field name="partner_id"/>
            <field name="amount_total"/>
            <field name="hacienda_state" widget="badge"/>

            <!-- Gym-specific: Days overdue -->
            <field name="days_overdue" invisible="1"/>
            <field name="payment_status" decoration-danger="payment_status == 'overdue'"
                                        decoration-warning="payment_status == 'due_soon'"/>
        </tree>
    </field>
</record>
```

**Impact:** ⭐⭐⭐⭐⭐ (Massively reduces admin time)

---

#### Week 3: Analytics & Dashboards

##### 3.1 Gym Revenue Dashboard (6 hours)
**Use Case:** Owner wants to see revenue by membership type, retention, churn

**Dashboard Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  PANEL DE INGRESOS - Diciembre 2025                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Ingresos MES │  │ Facturas     │  │ Tasa Pago    │         │
│  │ ₡8,450,000   │  │ 187          │  │ 94%          │         │
│  │ +12% vs Nov  │  │ ✓ 176 pagadas│  │ ✓ Excelente  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  INGRESOS POR TIPO DE MEMBRESÍA                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🥇 GOLD      ████████████░░░░  ₡3,250,000  (38%)        │   │
│  │ 🥈 SILVER    ████████░░░░░░░░  ₡3,115,000  (37%)        │   │
│  │ 🥉 BASIC     ████░░░░░░░░░░░░  ₡1,155,000  (14%)        │   │
│  │ 👥 PAREJA    ██░░░░░░░░░░░░░░    ₡640,000   (8%)        │   │
│  │ 🏋️ CLASES    █░░░░░░░░░░░░░░░    ₡290,000   (3%)        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  FACTURAS PENDIENTES DE PAGO                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Vencidas (> 5 días):     8 facturas    ₡448,000 ⚠️      │   │
│  │ Vence hoy:               3 facturas    ₡168,000         │   │
│  │ Próximos 7 días:        15 facturas    ₡840,000         │   │
│  │                                                           │   │
│  │ [Ver detalles]  [Enviar recordatorios]                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  TENDENCIA DE INGRESOS (6 MESES)                               │
│  ₡10M ┤                                              ●         │
│       ┤                                         ●               │
│   ₡8M ┤                                    ●                    │
│       ┤                               ●                         │
│   ₡6M ┤                          ●                              │
│       ┤                     ●                                   │
│   ₡4M └─────┬─────┬─────┬─────┬─────┬─────┬                   │
│           Jul   Ago   Sep   Oct   Nov   Dic                    │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation:**
```python
class GymRevenueDashboard(models.Model):
    _name = 'gym.revenue.dashboard'
    _description = 'Gym Revenue Analytics Dashboard'

    @api.model
    def get_dashboard_data(self, date_from=None, date_to=None):
        """
        Get comprehensive revenue analytics for gym
        """
        if not date_from:
            date_from = fields.Date.today().replace(day=1)
        if not date_to:
            date_to = fields.Date.today()

        # Total revenue
        invoices = self.env['l10n_cr.einvoice.document'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('hacienda_state', '=', 'accepted'),
            ('document_type', '=', 'FE'),
        ])

        total_revenue = sum(invoices.mapped('amount_total'))
        invoice_count = len(invoices)
        paid_count = len(invoices.filtered(lambda i: i.payment_state == 'paid'))
        payment_rate = (paid_count / invoice_count * 100) if invoice_count > 0 else 0

        # Revenue by membership type
        revenue_by_type = {}
        for invoice in invoices:
            if invoice.membership_id:
                mem_type = invoice.membership_id.membership_type_id.name
                if mem_type not in revenue_by_type:
                    revenue_by_type[mem_type] = 0
                revenue_by_type[mem_type] += invoice.amount_total

        # Sort by revenue descending
        revenue_by_type = dict(sorted(
            revenue_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        # Overdue invoices
        overdue_invoices = self.env['l10n_cr.einvoice.document'].search([
            ('invoice_date_due', '<', fields.Date.today()),
            ('payment_state', '!=', 'paid'),
            ('hacienda_state', '=', 'accepted'),
        ])

        # Due soon
        due_soon = self.env['l10n_cr.einvoice.document'].search([
            ('invoice_date_due', '>=', fields.Date.today()),
            ('invoice_date_due', '<=', fields.Date.today() + timedelta(days=7)),
            ('payment_state', '!=', 'paid'),
        ])

        # 6-month trend
        trend_data = []
        for i in range(6):
            month_start = (date_to - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            month_invoices = self.env['l10n_cr.einvoice.document'].search([
                ('date', '>=', month_start),
                ('date', '<=', month_end),
                ('hacienda_state', '=', 'accepted'),
            ])

            trend_data.append({
                'month': month_start.strftime('%b'),
                'revenue': sum(month_invoices.mapped('amount_total')),
            })

        return {
            'total_revenue': total_revenue,
            'invoice_count': invoice_count,
            'paid_count': paid_count,
            'payment_rate': payment_rate,
            'revenue_by_type': revenue_by_type,
            'overdue': {
                'count': len(overdue_invoices),
                'amount': sum(overdue_invoices.mapped('amount_residual')),
            },
            'due_soon': {
                'count': len(due_soon),
                'amount': sum(due_soon.mapped('amount_residual')),
            },
            'trend': trend_data,
        }
```

**Dashboard View:**
```xml
<record id="view_gym_revenue_dashboard" model="ir.ui.view">
    <field name="name">gym.revenue.dashboard</field>
    <field name="model">gym.revenue.dashboard</field>
    <field name="arch" type="xml">
        <dashboard>
            <group>
                <!-- KPI Cards -->
                <group>
                    <field name="total_revenue" widget="monetary"/>
                    <field name="invoice_count"/>
                    <field name="payment_rate" widget="percentage"/>
                </group>

                <!-- Revenue by Type Chart -->
                <field name="revenue_by_type" widget="pie_chart"/>

                <!-- Overdue Invoices -->
                <field name="overdue_invoices" widget="list">
                    <tree>
                        <field name="consecutive"/>
                        <field name="partner_id"/>
                        <field name="amount_residual"/>
                        <field name="days_overdue"/>
                    </tree>
                </field>

                <!-- Trend Chart -->
                <field name="trend_data" widget="line_chart"/>
            </group>
        </dashboard>
    </field>
</record>
```

**Impact:** ⭐⭐⭐⭐⭐ (Critical for business intelligence)

---

##### 3.2 Member Lifecycle Analytics (4 hours)
**Use Case:** Understand retention, churn, lifetime value

**Member Analytics View:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ANÁLISIS DE SOCIOS - 2025                                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Socios       │  │ Retención    │  │ Churn Rate   │         │
│  │ 187 activos  │  │ 89%          │  │ 11%          │         │
│  │ +15 este mes │  │ ✓ Bueno      │  │ ⚠️ Mejorable │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  NUEVOS SOCIOS (Últimos 30 días)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Total: 15 nuevos socios                                 │   │
│  │                                                           │   │
│  │ Por membresía:                                           │   │
│  │  • GOLD: 6 socios                                        │   │
│  │  • SILVER: 7 socios                                      │   │
│  │  • BASIC: 2 socios                                       │   │
│  │                                                           │   │
│  │ Fuente de referencia:                                    │   │
│  │  • Instagram: 8                                          │   │
│  │  • Referido: 4                                           │   │
│  │  • Google: 2                                             │   │
│  │  • Walk-in: 1                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  SOCIOS EN RIESGO DE CANCELACIÓN (Pago atrasado > 10 días)    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Laura Sánchez    GOLD      15 días atraso  ⚠️ Alto      │   │
│  │ Juan Pérez       SILVER    12 días atraso  ⚠️ Alto      │   │
│  │ Carlos Mora      BASIC     10 días atraso  ⚠️ Medio     │   │
│  │                                                           │   │
│  │ [Contactar socios]  [Ofrecer plan de pagos]             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  LIFETIME VALUE PROMEDIO                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Estadía promedio: 18 meses                              │   │
│  │ Gasto mensual promedio: ₡45,000                         │   │
│  │ LTV promedio: ₡810,000                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation:** Similar to revenue dashboard but focused on member metrics

**Impact:** ⭐⭐⭐⭐ (Helps reduce churn, improve retention)

---

#### Week 4: UI/UX Polish (Administrative Interface)

##### 4.1 Enhanced Search Panel (From HuliPractice) (3 hours)
Already covered in UI/UX analysis - implement persistent filter sidebar

##### 4.2 Status Badges & Visual Indicators (2 hours)
Already covered - implement status badge widget

##### 4.3 Document Tags for Organization (3 hours)
Already covered - implement tags system

##### 4.4 Keyboard Shortcuts for Power Users (2 hours)
**Use Case:** Accountant processes 50 invoices/day, needs speed

**Shortcuts:**
```
Ctrl + N     = Nueva factura
Ctrl + S     = Guardar
Ctrl + Enter = Enviar a Hacienda
Ctrl + P     = Vista previa
Ctrl + E     = Exportar a Excel
Ctrl + F     = Buscar
Ctrl + /     = Mostrar ayuda de atajos
```

**Implementation:**
```javascript
// Add keyboard shortcuts
odoo.define('l10n_cr_einvoice.KeyboardShortcuts', function(require) {
    'use strict';

    const core = require('web.core');
    const Widget = require('web.Widget');

    const KeyboardShortcuts = Widget.extend({
        events: {
            'keydown': '_onKeyDown',
        },

        _onKeyDown: function(e) {
            // Ctrl + N: New invoice
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                this.do_action('l10n_cr_einvoice.action_einvoice_document_create');
            }

            // Ctrl + Enter: Submit to Hacienda
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.trigger_up('submit_to_hacienda');
            }

            // Ctrl + P: Preview
            if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                this.trigger_up('preview_invoice');
            }

            // Ctrl + /: Show help
            if (e.ctrlKey && e.key === '/') {
                e.preventDefault();
                this._showShortcutsHelp();
            }
        },

        _showShortcutsHelp: function() {
            this.do_warn('Atajos de teclado', `
                Ctrl + N: Nueva factura
                Ctrl + S: Guardar
                Ctrl + Enter: Enviar a Hacienda
                Ctrl + P: Vista previa
                Ctrl + E: Exportar Excel
                Ctrl + F: Buscar
                Ctrl + /: Mostrar esta ayuda
            `);
        },
    });

    core.action_registry.add('keyboard_shortcuts', KeyboardShortcuts);
    return KeyboardShortcuts;
});
```

**Impact:** ⭐⭐⭐ (Power users love this)

---

## Implementation Summary

### Total Effort Estimate

**POS Improvements (Area 1):**
- Week 1: 9 hours (Visual overhaul)
- Week 2: 5 hours (Offline enhancements)
- Week 3: 6 hours (Gym-specific features)
- Week 4: 7 hours (Payment shortcuts)
- **Total POS: 27 hours**

**Backend Improvements (Area 2):**
- Week 1: 20 hours (Critical fixes)
- Week 2: 10 hours (Bulk operations)
- Week 3: 10 hours (Analytics dashboards)
- Week 4: 10 hours (UI/UX polish)
- **Total Backend: 50 hours**

**GRAND TOTAL: 77 hours (2 developers × 4 weeks)**

---

### Priority Matrix

| Feature | POS | Backend | Priority | Effort | Impact |
|---------|-----|---------|----------|--------|--------|
| Invoice void/cancel | - | ✓ | 🔴 CRITICAL | 8h | ⭐⭐⭐⭐⭐ |
| Preview before submit | - | ✓ | 🔴 CRITICAL | 4h | ⭐⭐⭐⭐⭐ |
| CR Tax Reports | - | ✓ | 🔴 CRITICAL | 8h | ⭐⭐⭐⭐⭐ |
| Membership quick actions | ✓ | - | 🟡 HIGH | 4h | ⭐⭐⭐⭐⭐ |
| Recurring invoice gen | - | ✓ | 🟡 HIGH | 6h | ⭐⭐⭐⭐⭐ |
| SINPE verification | ✓ | - | 🟡 HIGH | 4h | ⭐⭐⭐⭐⭐ |
| Bulk actions | - | ✓ | 🟡 HIGH | 4h | ⭐⭐⭐⭐⭐ |
| Revenue dashboard | - | ✓ | 🟡 HIGH | 6h | ⭐⭐⭐⭐⭐ |
| Product categories w/ icons | ✓ | - | 🟢 MEDIUM | 2h | ⭐⭐⭐⭐ |
| Enhanced offline queue | ✓ | - | 🟢 MEDIUM | 2h | ⭐⭐⭐⭐ |
| Member quick lookup | ✓ | - | 🟢 MEDIUM | 3h | ⭐⭐⭐⭐⭐ |
| Class/session quick add | ✓ | - | 🟢 MEDIUM | 4h | ⭐⭐⭐⭐ |
| Stock quick view | ✓ | - | 🟢 MEDIUM | 2h | ⭐⭐⭐ |
| Payment presets | ✓ | - | 🟢 MEDIUM | 3h | ⭐⭐⭐⭐ |
| Member lifecycle analytics | - | ✓ | 🟢 MEDIUM | 4h | ⭐⭐⭐⭐ |
| Keyboard shortcuts | - | ✓ | 🟢 LOW | 2h | ⭐⭐⭐ |

---

## Conclusion

### What We're Building

**TWO distinct but integrated systems:**

1. **POS (Frontline)** - Fast, visual, offline-ready
   - For daily operations (check-ins, sales, renewals)
   - Must be fast (< 30 seconds per transaction)
   - Gym-specific categories and workflows
   - Robust offline mode (your advantage!)

2. **Backend (Admin)** - Powerful, analytical, compliant
   - For monthly/quarterly operations
   - Bulk invoice generation
   - Tax reports (D-104, D-101, D-151)
   - Revenue analytics by membership type
   - Hacienda compliance management

### Success Metrics

**POS:**
- Transaction time: < 30 seconds (from 60 seconds)
- Member lookup: < 5 seconds (from 15 seconds)
- Offline reliability: 99%+ (already good)
- Staff satisfaction: 8+/10

**Backend:**
- Monthly invoicing time: < 30 minutes (from 4-6 hours)
- Tax report generation: < 5 minutes
- Accountant satisfaction: 9+/10
- Zero Hacienda compliance issues

---

**LET'S BUILD THE BEST GYM MANAGEMENT SYSTEM IN COSTA RICA** 💪🏋️

**Next Step:** Which area do you want to tackle first - POS or Backend?
