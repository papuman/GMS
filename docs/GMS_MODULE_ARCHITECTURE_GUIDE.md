# GMS Module Architecture & Integration Guide
## Comprehensive Technical Documentation for Module Cloning, Customization & Integration

**Document Version:** 1.0.0
**Last Updated:** December 29, 2025
**Author:** GMS Development Team
**Status:** Production Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Odoo Module Inheritance Patterns](#odoo-module-inheritance-patterns)
3. [Module Cloning Strategies](#module-cloning-strategies)
4. [GMS Module Organization](#gms-module-organization)
5. [Integration Architecture Patterns](#integration-architecture-patterns)
6. [POS ↔ E-Invoice Integration Design](#pos--e-invoice-integration-design)
7. [Implementation Guidelines](#implementation-guidelines)
8. [Code Examples](#code-examples)
9. [Testing & Validation](#testing--validation)
10. [Migration & Updates](#migration--updates)

---

## Executive Summary

### Purpose

This document provides comprehensive guidance for:
- Cloning and customizing Odoo standard modules for GMS-specific needs
- Designing integration architecture between modules
- Implementing the POS ↔ E-Invoice integration for Costa Rica compliance

### Key Recommendations

**1. Use Inheritance Over Forking**
- ✅ **RECOMMENDED:** Inherit and extend standard modules using Odoo's module inheritance
- ❌ **NOT RECOMMENDED:** Complete fork and rename (breaks upgrades)
- ⚠️ **USE SPARINGLY:** Wrapper modules (adds complexity)

**2. Current Architecture Success**
- The existing `l10n_cr_einvoice` module demonstrates **excellent architecture**
- Uses model inheritance (`_inherit`) to extend standard models
- Maintains compatibility with Odoo core updates
- Clean separation of concerns

**3. Integration Pattern**
- **Event-Driven Architecture** for POS ↔ E-Invoice communication
- Model relationships using Many2one fields
- Offline queue for reliability
- Real-time updates via Odoo's bus messaging

---

## Odoo Module Inheritance Patterns

### 1.1 Understanding Odoo's Inheritance System

Odoo provides three primary inheritance mechanisms:

#### A. Classical Inheritance (`_inherit` on same model)
**When to use:** Extend an existing model with new fields and methods

```python
class PosOrder(models.Model):
    _inherit = 'pos.order'  # Extend pos.order model

    # Add new fields
    l10n_cr_einvoice_document_id = fields.Many2one('l10n_cr.einvoice.document')
    l10n_cr_hacienda_status = fields.Selection([...])

    # Add new methods
    def _l10n_cr_generate_einvoice(self):
        pass

    # Override existing methods
    def _process_order(self, order, existing_order):
        result = super()._process_order(order, existing_order)
        # Add custom logic
        return result
```

**Advantages:**
- ✅ No code duplication
- ✅ Automatic updates when core changes
- ✅ Maintains compatibility
- ✅ Can add fields, methods, and constraints

**Disadvantages:**
- ❌ Cannot remove existing fields
- ❌ Must be careful with method overrides
- ❌ All instances of model affected

#### B. Delegation Inheritance (`_inherit` + `_name`)
**When to use:** Create a new model that extends another

```python
class GmsCustomer(models.Model):
    _name = 'gms.customer'  # New model
    _inherit = 'res.partner'  # Inherit from partner

    # All res.partner fields available
    # Plus new GMS-specific fields
    membership_level = fields.Selection([...])
    fitness_goals = fields.Text()
```

**Advantages:**
- ✅ Separate table in database
- ✅ Can have different security rules
- ✅ Doesn't affect original model
- ✅ Good for specialized data

**Disadvantages:**
- ❌ Data duplication
- ❌ Synchronization complexity
- ❌ More complex queries

#### C. Prototype Inheritance (`_inherits`)
**When to use:** Embed one model inside another (composition)

```python
class GmsMember(models.Model):
    _name = 'gms.member'
    _inherits = {'res.partner': 'partner_id'}  # Delegate to partner

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    membership_number = fields.Char()
    # Access partner fields as if they were on gms.member
```

**Advantages:**
- ✅ Clean composition
- ✅ Reuses partner functionality
- ✅ Separate concerns

**Disadvantages:**
- ❌ Complex to understand
- ❌ Database joins
- ❌ Can't override inherited methods easily

### 1.2 View Inheritance Patterns

#### XPath-Based View Extension

```xml
<odoo>
    <record id="view_pos_order_form_einvoice" model="ir.ui.view">
        <field name="name">pos.order.form.einvoice</field>
        <field name="model">pos.order</field>
        <field name="inherit_id" ref="point_of_sale.view_pos_pos_form"/>
        <field name="arch" type="xml">

            <!-- Add field after existing field -->
            <field name="partner_id" position="after">
                <field name="l10n_cr_einvoice_document_id"/>
                <field name="l10n_cr_hacienda_status"/>
            </field>

            <!-- Add new notebook page -->
            <xpath expr="//notebook" position="inside">
                <page string="E-Invoice" name="einvoice">
                    <group>
                        <field name="l10n_cr_clave"/>
                        <field name="l10n_cr_consecutive"/>
                    </group>
                </page>
            </xpath>

            <!-- Replace existing element -->
            <button name="action_invoice" position="replace">
                <button name="action_l10n_cr_generate_einvoice"
                        string="Generate E-Invoice"
                        type="object"/>
            </button>

        </field>
    </record>
</odoo>
```

**XPath Positions:**
- `before`: Insert before the element
- `after`: Insert after the element
- `inside`: Insert inside the element (for containers)
- `replace`: Replace the entire element
- `attributes`: Modify attributes

---

## Module Cloning Strategies

### 2.1 Three Approaches Compared

| Aspect | Inheritance (Recommended) | Complete Fork | Wrapper Module |
|--------|--------------------------|---------------|----------------|
| **Code Duplication** | Minimal | 100% | Medium |
| **Update Safety** | Excellent | Poor | Good |
| **Complexity** | Low | Medium | High |
| **Customization Scope** | Wide | Total | Limited |
| **Maintenance Burden** | Low | Very High | Medium |
| **Use Case** | Most scenarios | Never | Rare edge cases |

### 2.2 Option A: Inheritance and Extension (RECOMMENDED)

**Philosophy:** Don't clone modules; extend them through inheritance

**Process:**
1. Create a new module that depends on the standard module
2. Use `_inherit` to extend models
3. Use XPath to extend views
4. Override methods as needed

**Example Directory Structure:**
```
gms_pos/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── pos_order.py          # Extends pos.order
│   ├── pos_session.py        # Extends pos.session
│   └── pos_config.py         # Extends pos.config
├── views/
│   ├── pos_order_views.xml   # Extends POS views
│   └── pos_session_views.xml
├── security/
│   └── ir.model.access.csv
└── static/
    └── src/
        └── js/
            └── pos_gms.js    # JavaScript extensions
```

**__manifest__.py:**
```python
{
    'name': 'GMS Point of Sale Extensions',
    'version': '19.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'GMS-specific POS customizations',
    'depends': [
        'point_of_sale',        # Extend standard POS
        'l10n_cr_einvoice',     # Integrate with e-invoice
        'sale_subscription',    # Membership integration
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
        'views/pos_session_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
```

**Advantages:**
- ✅ No code duplication
- ✅ Automatic Odoo updates applied
- ✅ Clear what's customized (only override files)
- ✅ Easy to disable/enable
- ✅ Follows Odoo best practices

**Disadvantages:**
- ❌ Cannot remove core functionality (only extend)
- ❌ Must understand inheritance chain
- ❌ Potential conflicts with other modules

**When to Use:**
- 99% of customization scenarios
- Adding features to standard modules
- Integration between modules
- Industry-specific extensions

### 2.3 Option B: Complete Fork and Rename (NOT RECOMMENDED)

**Process:**
1. Copy entire module directory
2. Rename module (e.g., `point_of_sale` → `gms_point_of_sale`)
3. Update all references in code
4. Maintain separately

**Why This Fails:**
- ❌ **Update Hell:** Cannot apply Odoo security patches or feature updates
- ❌ **Dependency Conflicts:** Other modules expect standard module name
- ❌ **Code Duplication:** Thousands of lines to maintain
- ❌ **Asset Management:** JavaScript/CSS paths all need updating
- ❌ **Testing Burden:** Must test everything, not just changes

**ONLY use if:**
- You need to completely replace core functionality (extremely rare)
- You're creating a fundamentally different product
- You have a large team dedicated to maintenance

**Cost Analysis:**
- Initial setup: 2-3 days
- Monthly maintenance: 40-60 hours
- Update compatibility: 80-120 hours per major version
- **Total annual cost:** $50,000-$100,000+ in developer time

### 2.4 Option C: Wrapper Module Pattern

**When to use:** Need to intercept and modify all calls to a model

**Pattern:**
```python
class GmsPosOrderWrapper(models.Model):
    _name = 'gms.pos.order'
    _inherit = 'pos.order'
    _description = 'GMS POS Order Wrapper'

    # Delegate all calls through custom logic
    @api.model
    def create(self, vals):
        # Custom pre-processing
        vals = self._gms_preprocess_order(vals)

        # Call original
        result = super().create(vals)

        # Custom post-processing
        self._gms_postprocess_order(result)

        return result
```

**Use Cases:**
- Multi-tenant scenarios
- Audit trail requirements
- Complex business rules

**Complexity Trade-off:**
- Adds extra layer
- Performance overhead
- Harder to debug

---

## GMS Module Organization

### 3.1 Recommended Module Structure

**Core Principle:** One module per functional area, following Odoo conventions

```
GMS Custom Modules Structure:
============================

l10n_cr_einvoice/          # Costa Rica e-invoicing (existing - excellent)
├── Models extend: account.move, res.partner, res.company
├── New models: einvoice.document, hacienda.api, etc.
└── Purpose: Costa Rica compliance

gms_pos/                   # POS extensions (NEW)
├── Models extend: pos.order, pos.session, pos.config
├── Purpose: GMS-specific POS features
└── Integration: Links to l10n_cr_einvoice

gms_membership/            # Membership management (FUTURE)
├── Models extend: sale.subscription, res.partner
├── Purpose: Gym membership, access control
└── Integration: Links to POS, CRM

gms_crm/                   # CRM extensions (FUTURE)
├── Models extend: crm.lead, res.partner
├── Purpose: Lead to member conversion
└── Integration: Links to membership

gms_inventory/             # Inventory extensions (FUTURE)
├── Models extend: stock.picking, product.product
├── Purpose: Gym equipment, consumables
└── Integration: Links to POS, purchasing
```

### 3.2 Naming Conventions

**Module Names:**
- Format: `gms_<functional_area>`
- Examples: `gms_pos`, `gms_membership`, `gms_crm`
- Prefix ensures alphabetical grouping
- Lowercase with underscores

**Model Names:**
- Extended models: Keep original name with `_inherit`
- New models: `gms.<domain>.<entity>`
- Examples: `gms.member`, `gms.access.log`, `gms.equipment`

**Field Names:**
- GMS fields on standard models: `x_gms_<field_name>`
- Fields on GMS models: `<field_name>` (no prefix)
- Example: `x_gms_membership_level` on `res.partner`

**XML IDs:**
- Format: `<module>.<entity>_<name>`
- Examples: `gms_pos.view_pos_order_form`, `gms_membership.menu_members`

### 3.3 Dependency Management

**Module Loading Order:**

```python
# l10n_cr_einvoice/__manifest__.py
{
    'depends': [
        'base',
        'account',
        'l10n_cr',
        'sale',
        'point_of_sale',  # Extends POS
    ],
}

# gms_pos/__manifest__.py
{
    'depends': [
        'point_of_sale',      # Base POS functionality
        'l10n_cr_einvoice',   # E-invoice integration
        'sale_subscription',  # Optional: member discounts
    ],
}

# gms_membership/__manifest__.py
{
    'depends': [
        'sale_subscription',
        'gms_pos',           # POS integration
        'gms_crm',           # CRM integration
    ],
}
```

**Dependency Rules:**
1. Always depend on base Odoo modules first
2. Then localization modules (`l10n_*`)
3. Then GMS modules in order of dependency
4. Use `external_dependencies` for Python packages

### 3.4 Security and Access Rights

**File Structure:**
```
gms_pos/
└── security/
    ├── gms_pos_security.xml      # Groups and rules
    └── ir.model.access.csv       # Model access rights
```

**Security Groups:**
```xml
<record id="group_gms_pos_user" model="res.groups">
    <field name="name">GMS POS User</field>
    <field name="category_id" ref="base.module_category_sales_point_of_sale"/>
    <field name="implied_ids" eval="[(4, ref('point_of_sale.group_pos_user'))]"/>
</record>

<record id="group_gms_pos_manager" model="res.groups">
    <field name="name">GMS POS Manager</field>
    <field name="implied_ids" eval="[(4, ref('group_gms_pos_user'))]"/>
</record>
```

**Access Rights (ir.model.access.csv):**
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_pos_order_user,pos.order user,point_of_sale.model_pos_order,group_gms_pos_user,1,1,1,0
access_pos_order_manager,pos.order manager,point_of_sale.model_pos_order,group_gms_pos_manager,1,1,1,1
```

### 3.5 Multi-Company Considerations

**Company-Specific Data:**
```python
class PosConfig(models.Model):
    _inherit = 'pos.config'

    l10n_cr_enable_einvoice = fields.Boolean(
        string='Enable E-Invoice',
        compute='_compute_l10n_cr_enable_einvoice',
        store=True,
    )

    @api.depends('company_id', 'company_id.country_id')
    def _compute_l10n_cr_enable_einvoice(self):
        for config in self:
            # Only enable for Costa Rica companies
            config.l10n_cr_enable_einvoice = (
                config.company_id.country_id.code == 'CR'
            )
```

**Record Rules:**
```xml
<record id="pos_order_company_rule" model="ir.rule">
    <field name="name">POS Orders: multi-company</field>
    <field name="model_id" ref="point_of_sale.model_pos_order"/>
    <field name="domain_force">[('company_id', 'in', company_ids)]</field>
</record>
```

---

## Integration Architecture Patterns

### 4.1 Integration Patterns in Odoo

#### Pattern 1: Direct Model Relationships (Most Common)

**Use Case:** Tight coupling where one model owns another

```python
class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Many2one: POS Order → E-Invoice Document
    l10n_cr_einvoice_document_id = fields.Many2one(
        'l10n_cr.einvoice.document',
        string='Electronic Invoice',
        readonly=True,
        copy=False,
    )

class EInvoiceDocument(models.Model):
    _name = 'l10n_cr.einvoice.document'

    # One2many: E-Invoice Document ← POS Orders
    pos_order_ids = fields.One2many(
        'pos.order',
        'l10n_cr_einvoice_document_id',
        string='POS Orders',
    )
```

**Advantages:**
- ✅ Simple and clear
- ✅ Enforced referential integrity
- ✅ Automatic cascade options
- ✅ ORM handles relationships

**When to Use:**
- Parent-child relationships
- One model owns the other
- Need database constraints

#### Pattern 2: Event-Driven via Hooks

**Use Case:** Loose coupling, one module reacts to another's events

```python
class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self, vals):
        # Create order
        order = super().create(vals)

        # Trigger event for e-invoice generation
        if order._should_generate_einvoice():
            order._trigger_einvoice_generation()

        return order

    def _trigger_einvoice_generation(self):
        """Event hook for e-invoice module to catch"""
        self.ensure_one()

        # Check if e-invoice module is installed
        if not self.env['ir.module.module'].search([
            ('name', '=', 'l10n_cr_einvoice'),
            ('state', '=', 'installed')
        ]):
            return

        # Delegate to e-invoice module
        self._l10n_cr_generate_einvoice()
```

**Advantages:**
- ✅ Loose coupling
- ✅ Modules can be enabled/disabled
- ✅ Clear extension points

**When to Use:**
- Optional features
- Plugin architecture
- Cross-module notifications

#### Pattern 3: Computed Fields

**Use Case:** Derived data from related models

```python
class PosOrder(models.Model):
    _inherit = 'pos.order'

    l10n_cr_hacienda_status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
        ],
        compute='_compute_l10n_cr_hacienda_status',
        store=True,
    )

    @api.depends('l10n_cr_einvoice_document_id.state')
    def _compute_l10n_cr_hacienda_status(self):
        for order in self:
            if order.l10n_cr_einvoice_document_id:
                # Map e-invoice state to POS status
                state_map = {
                    'accepted': 'accepted',
                    'rejected': 'rejected',
                    'submitted': 'pending',
                }
                order.l10n_cr_hacienda_status = state_map.get(
                    order.l10n_cr_einvoice_document_id.state,
                    'draft'
                )
            else:
                order.l10n_cr_hacienda_status = 'draft'
```

**Advantages:**
- ✅ Always up-to-date
- ✅ No manual synchronization
- ✅ Store=True for performance

#### Pattern 4: Message Bus (Real-time Updates)

**Use Case:** UI updates, multi-user notifications

```python
class EInvoiceDocument(models.Model):
    _name = 'l10n_cr.einvoice.document'
    _inherit = ['l10n_cr.einvoice.document', 'bus.bus']

    def _notify_hacienda_status_change(self):
        """Send bus notification when status changes"""
        self.ensure_one()

        # Send to specific POS session
        if self.pos_order_ids:
            pos_session = self.pos_order_ids[0].session_id
            channel = f'pos_session_{pos_session.id}'

            self.env['bus.bus']._sendone(channel, 'einvoice_status_update', {
                'order_id': self.pos_order_ids[0].id,
                'status': self.state,
                'message': self.hacienda_message,
            })
```

**JavaScript Listener:**
```javascript
odoo.define('gms_pos.einvoice_listener', function (require) {
    const { PosGlobalState } = require('point_of_sale.models');
    const { patch } = require('web.utils');

    patch(PosGlobalState.prototype, 'gms_pos.einvoice_listener', {
        _onEInvoiceStatusUpdate(data) {
            const order = this.orders.find(o => o.id === data.order_id);
            if (order) {
                order.l10n_cr_hacienda_status = data.status;
                this.showNotification(data.message);
            }
        }
    });
});
```

#### Pattern 5: Scheduled Actions (Async Processing)

**Use Case:** Background jobs, queue processing

```python
class PosOfflineQueue(models.Model):
    _name = 'l10n_cr.pos.offline.queue'

    @api.model
    def cron_sync_offline_invoices(self):
        """Called by scheduled action every 5 minutes"""
        queue_entries = self.search([
            ('state', '=', 'pending'),
        ], limit=50)

        for entry in queue_entries:
            try:
                entry.process_sync()
            except Exception as e:
                _logger.error(f'Sync failed: {e}')
                entry.retry_count += 1
```

**Cron Job Definition:**
```xml
<record id="ir_cron_sync_offline_invoices" model="ir.cron">
    <field name="name">Sync Offline E-Invoices</field>
    <field name="model_id" ref="model_l10n_cr_pos_offline_queue"/>
    <field name="state">code</field>
    <field name="code">model.cron_sync_offline_invoices()</field>
    <field name="interval_number">5</field>
    <field name="interval_type">minutes</field>
    <field name="numbercall">-1</field>
    <field name="active">True</field>
</record>
```

### 4.2 API Design Between Modules

#### Public API Pattern

**E-Invoice Module Exposes Public Methods:**
```python
class EInvoiceDocument(models.Model):
    _name = 'l10n_cr.einvoice.document'

    # PUBLIC API - Stable interface for other modules

    @api.model
    def create_from_pos_order(self, pos_order):
        """
        Create e-invoice from POS order

        PUBLIC API - Do not change signature

        Args:
            pos_order: pos.order recordset

        Returns:
            l10n_cr.einvoice.document record

        Raises:
            UserError: If validation fails
        """
        self._validate_pos_order(pos_order)

        invoice_data = self._prepare_invoice_from_pos(pos_order)
        einvoice = self.create(invoice_data)

        # Async generation
        einvoice.with_delay().action_generate_xml()

        return einvoice

    def submit_to_hacienda(self):
        """
        Submit signed XML to Hacienda

        PUBLIC API - Do not change signature

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'clave': str,
            }
        """
        self.ensure_one()

        api = self.env['l10n_cr.hacienda.api']
        response = api.submit_invoice(
            xml=self.signed_xml,
            clave=self.clave,
            company=self.company_id,
        )

        return response

    # PRIVATE METHODS - Can change

    def _validate_pos_order(self, pos_order):
        """Internal validation logic"""
        pass

    def _prepare_invoice_from_pos(self, pos_order):
        """Internal data preparation"""
        pass
```

**POS Module Uses Public API:**
```python
class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _l10n_cr_generate_einvoice(self):
        """Generate e-invoice using public API"""
        self.ensure_one()

        # Use public API - stable and documented
        EInvoice = self.env['l10n_cr.einvoice.document']

        try:
            einvoice = EInvoice.create_from_pos_order(self)
            self.l10n_cr_einvoice_document_id = einvoice

            # Check if online
            if self._l10n_cr_is_online():
                result = einvoice.submit_to_hacienda()
                if result['success']:
                    self.l10n_cr_hacienda_status = 'pending'
            else:
                self._l10n_cr_queue_for_sync(einvoice)

        except Exception as e:
            _logger.error(f'E-invoice generation failed: {e}')
            raise
```

#### Error Handling Across Modules

**Pattern: Graceful Degradation**
```python
class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _process_order(self, order, existing_order):
        """Override to add e-invoice generation"""

        # Always process the order first
        result = super()._process_order(order, existing_order)

        # Try e-invoice generation (non-critical)
        if self._should_generate_einvoice():
            try:
                self._l10n_cr_generate_einvoice()
            except Exception as e:
                # Log but don't block order
                _logger.error(f'E-invoice generation failed: {e}')

                # Queue for retry
                self.env['l10n_cr.einvoice.retry.queue'].create({
                    'pos_order_id': result.id,
                    'error_message': str(e),
                })

        return result
```

### 4.3 Data Synchronization

#### Pattern: Eventual Consistency

**Scenario:** Offline POS generates orders, syncs when online

```python
class PosOfflineQueue(models.Model):
    _name = 'l10n_cr.pos.offline.queue'
    _description = 'Offline E-Invoice Queue'

    pos_order_id = fields.Many2one('pos.order', required=True)
    einvoice_document_id = fields.Many2one('l10n_cr.einvoice.document')
    xml_data = fields.Text('Signed XML')
    state = fields.Selection([
        ('pending', 'Pending Sync'),
        ('syncing', 'Syncing Now'),
        ('synced', 'Successfully Synced'),
        ('failed', 'Sync Failed'),
    ], default='pending')
    retry_count = fields.Integer(default=0)
    last_error = fields.Text()

    @api.model
    def process_sync_batch(self, batch_size=50):
        """Process batch of queued invoices"""

        # Get pending entries
        entries = self.search([
            ('state', '=', 'pending'),
            ('retry_count', '<', 5),  # Max 5 retries
        ], limit=batch_size, order='create_date')

        success_count = 0
        for entry in entries:
            entry.state = 'syncing'

            try:
                # Submit to Hacienda
                response = entry.einvoice_document_id.submit_to_hacienda()

                if response['success']:
                    entry.state = 'synced'
                    entry.pos_order_id.l10n_cr_hacienda_status = 'pending'
                    success_count += 1
                else:
                    raise UserError(response['message'])

            except Exception as e:
                entry.state = 'pending'
                entry.retry_count += 1
                entry.last_error = str(e)

                if entry.retry_count >= 5:
                    entry.state = 'failed'
                    # Notify manager
                    entry._notify_failed_sync()

        return {
            'processed': len(entries),
            'success': success_count,
            'failed': len(entries) - success_count,
        }
```

#### Conflict Resolution

**Pattern: Last Write Wins**
```python
@api.model
def _reconcile_offline_data(self, local_order, server_order):
    """Reconcile conflicts between offline and server data"""

    # Compare timestamps
    if local_order['write_date'] > server_order.write_date:
        # Local is newer - update server
        server_order.write(local_order)
    else:
        # Server is newer - discard local changes
        # Or merge based on business rules
        merged_data = self._merge_order_data(local_order, server_order)
        server_order.write(merged_data)
```

---

## POS ↔ E-Invoice Integration Design

### 5.1 Integration Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         POS TERMINAL                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Customer   │  │   Products   │  │   Payment    │          │
│  │     Data     │  │   & Taxes    │  │   Methods    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │                                     │
│                    ┌───────▼────────┐                            │
│                    │   POS Order    │                            │
│                    │   Validation   │                            │
│                    └───────┬────────┘                            │
│                            │                                     │
│                            ▼                                     │
│                    ┌───────────────┐                             │
│                    │  Order Saved  │                             │
│                    └───────┬───────┘                             │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             │ Trigger E-Invoice Generation
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                    E-INVOICE MODULE                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. CREATE INVOICE DOCUMENT                              │   │
│  │     - Generate consecutive number                        │   │
│  │     - Generate 50-digit clave                            │   │
│  │     - Create einvoice.document record                    │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │  2. GENERATE XML                                         │   │
│  │     - Map POS data to v4.4 schema                        │   │
│  │     - Validate against XSD                               │   │
│  │     - Add payment methods, taxes, discounts              │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │  3. SIGN XML                                             │   │
│  │     - Load company certificate                           │   │
│  │     - Apply digital signature                            │   │
│  │     - Embed signature in XML                             │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                        │
│                    ┌────▼─────┐                                 │
│                    │ Online?  │                                 │
│                    └────┬─────┘                                 │
│                         │                                        │
│         ┌───────────────┴───────────────┐                       │
│         │ YES                            │ NO                   │
│         ▼                                ▼                       │
│  ┌──────────────┐              ┌─────────────────┐              │
│  │ 4a. SUBMIT   │              │ 4b. QUEUE       │              │
│  │  TO HACIENDA │              │  FOR LATER      │              │
│  │              │              │                 │              │
│  │ - POST XML   │              │ - Save to queue │              │
│  │ - Get status │              │ - Retry later   │              │
│  └──────┬───────┘              └────────┬────────┘              │
│         │                               │                       │
│         │                               │                       │
│  ┌──────▼──────────────────────────────▼────────┐              │
│  │  5. GENERATE QR CODE                         │              │
│  │     - Create verification QR                 │              │
│  │     - Attach to order                        │              │
│  └──────────────────────┬───────────────────────┘              │
│                         │                                       │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                          │ Return to POS
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    POS TERMINAL                                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  RECEIPT PRINTING                                        │  │
│  │  - Print receipt with QR code                            │  │
│  │  - Show Hacienda status                                  │  │
│  │  - Email option                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

                    BACKGROUND SYNC PROCESS

┌─────────────────────────────────────────────────────────────────┐
│  CRON JOB (Every 5 minutes)                                     │
│                                                                 │
│  1. Check offline queue                                         │
│  2. Test Hacienda connectivity                                  │
│  3. Process up to 50 queued invoices                            │
│  4. Update POS order statuses                                   │
│  5. Send bus notifications to terminals                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Data Flow Specification

#### Step 1: POS Order Creation

**Trigger Point:** When POS order is validated and payment completed

**POS Terminal → Server:**
```javascript
// JavaScript: POS UI
async _finalizeValidation() {
    const order = this.get_order();

    // Add e-invoice customer data if available
    if (order.get_partner()) {
        order.l10n_cr_customer_id_type = this.gui.get_customer_id_type();
        order.l10n_cr_customer_id_number = this.gui.get_customer_id();
        order.l10n_cr_customer_email = order.get_partner().email;
    }

    // Send to server
    const result = await this.env.services.rpc({
        model: 'pos.order',
        method: 'create_from_ui',
        args: [[order.export_as_JSON()]],
    });

    // Listen for e-invoice status
    this.env.services.bus_service.addEventListener(
        'einvoice_status_update',
        this._onEInvoiceUpdate.bind(this)
    );
}
```

**Server Receives Order:**
```python
# Python: Server-side
class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_from_ui(self, orders, draft=False):
        """Override to add e-invoice generation"""

        # Create orders using standard method
        order_ids = super().create_from_ui(orders, draft)

        # Generate e-invoices for new orders
        for order_id in order_ids:
            order = self.browse(order_id)

            if order.l10n_cr_is_einvoice and not draft:
                # Async e-invoice generation
                order.with_delay(priority=5)._l10n_cr_generate_einvoice()

        return order_ids
```

#### Step 2: E-Invoice Document Creation

**Input:** POS Order record
**Output:** einvoice.document record with generated clave

```python
def _l10n_cr_generate_einvoice(self):
    """Generate Tiquete Electrónico"""
    self.ensure_one()

    # 1. Generate consecutive and clave
    consecutive = self._l10n_cr_generate_consecutive()
    clave = self._l10n_cr_generate_clave()

    # 2. Create account.move
    move = self._create_einvoice_move()

    # 3. Create einvoice document
    einvoice_vals = {
        'name': consecutive,
        'move_id': move.id,
        'company_id': self.company_id.id,
        'document_type': 'TE',
        'clave': clave,
    }

    einvoice = self.env['l10n_cr.einvoice.document'].create(einvoice_vals)
    self.l10n_cr_einvoice_document_id = einvoice

    # 4. Generate XML (async)
    einvoice.action_generate_xml()

    # 5. Sign XML
    einvoice.action_sign_xml()

    # 6. Submit or queue
    if self._l10n_cr_is_online():
        einvoice.action_submit_to_hacienda()
        self.l10n_cr_hacienda_status = 'pending'
    else:
        self._l10n_cr_queue_for_sync(einvoice)

    # 7. Generate QR
    self._l10n_cr_generate_qr_code(einvoice)

    return einvoice
```

#### Step 3: XML Generation

**Mapping POS Data to XML v4.4:**

```python
class XMLGenerator(models.AbstractModel):
    _name = 'l10n_cr.xml.generator'

    def generate_te_from_pos_order(self, pos_order):
        """Generate TE XML from POS order"""

        # Build XML structure
        root = etree.Element('TiqueteElectronico',
                            xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/tiqueteElectronico")

        # 1. Clave
        clave = etree.SubElement(root, 'Clave')
        clave.text = pos_order.l10n_cr_clave

        # 2. Emisor (Company)
        emisor = self._build_emisor(pos_order.company_id)
        root.append(emisor)

        # 3. Receptor (Customer) - Optional for TE
        if pos_order.l10n_cr_customer_id_number:
            receptor = self._build_receptor_pos(pos_order)
            root.append(receptor)

        # 4. Payment Methods
        medio_pago = etree.SubElement(root, 'MedioPago')
        for payment in pos_order.payment_ids:
            detalle = self._build_payment_method(payment)
            medio_pago.append(detalle)

        # 5. Line Items
        detalle_servicio = etree.SubElement(root, 'DetalleServicio')
        for line in pos_order.lines:
            linea = self._build_line_item_pos(line)
            detalle_servicio.append(linea)

        # 6. Resumen (Totals)
        resumen = self._build_resumen_pos(pos_order)
        root.append(resumen)

        # 7. Normativa (Version info)
        normativa = self._build_normativa()
        root.append(normativa)

        return etree.tostring(root,
                             encoding='utf-8',
                             xml_declaration=True,
                             pretty_print=True)

    def _build_payment_method(self, pos_payment):
        """Map POS payment to Hacienda code"""

        # Payment method mapping
        method_map = {
            'cash': '01',      # Efectivo
            'card': '02',      # Tarjeta
            'bank': '04',      # Transferencia
            'sinpe': '05',     # SINPE Móvil
        }

        payment_method = pos_payment.payment_method_id
        hacienda_code = '01'  # Default to cash

        if payment_method.is_cash_count:
            hacienda_code = '01'
        elif payment_method.use_payment_terminal:
            hacienda_code = '02'
        elif payment_method.l10n_cr_payment_code:
            hacienda_code = payment_method.l10n_cr_payment_code

        # Build XML
        detalle_pago = etree.Element('DetallePago')

        medio_pago = etree.SubElement(detalle_pago, 'MedioPago')
        medio_pago.text = hacienda_code

        monto = etree.SubElement(detalle_pago, 'Monto')
        monto.text = f'{pos_payment.amount:.2f}'

        return detalle_pago

    def _build_line_item_pos(self, pos_line):
        """Build line item from POS order line"""

        linea = etree.Element('LineaDetalle')

        # Line number
        numero = etree.SubElement(linea, 'NumeroLinea')
        numero.text = str(pos_line.sequence or 1)

        # Product code
        codigo = etree.SubElement(linea, 'Codigo')
        tipo = etree.SubElement(codigo, 'Tipo')
        tipo.text = '04'  # Internal code
        codigo_elem = etree.SubElement(codigo, 'Codigo')
        codigo_elem.text = pos_line.product_id.default_code or ''

        # Cabys code
        codigo_comercial = etree.SubElement(linea, 'CodigoComercial')
        tipo_com = etree.SubElement(codigo_comercial, 'Tipo')
        tipo_com.text = '04'
        codigo_com = etree.SubElement(codigo_comercial, 'Codigo')
        codigo_com.text = pos_line.product_id.l10n_cr_cabys_code or '0000000000000'

        # Quantity
        cantidad = etree.SubElement(linea, 'Cantidad')
        cantidad.text = f'{pos_line.qty:.2f}'

        # Unit of measure
        unidad = etree.SubElement(linea, 'UnidadMedida')
        unidad.text = pos_line.product_id.uom_id.name or 'Unidad'

        # Description
        detalle = etree.SubElement(linea, 'Detalle')
        detalle.text = pos_line.product_id.name

        # Price
        precio = etree.SubElement(linea, 'PrecioUnitario')
        precio.text = f'{pos_line.price_unit:.5f}'

        # Subtotal
        monto_total = etree.SubElement(linea, 'MontoTotal')
        monto_total.text = f'{pos_line.price_subtotal_incl:.2f}'

        # Discount
        if pos_line.discount > 0:
            descuento = etree.SubElement(linea, 'Descuento')
            monto_desc = etree.SubElement(descuento, 'MontoDescuento')
            discount_amount = pos_line.price_unit * pos_line.qty * (pos_line.discount / 100)
            monto_desc.text = f'{discount_amount:.2f}'

            # Discount reason
            naturaleza = etree.SubElement(descuento, 'NaturalezaDescuento')
            naturaleza.text = 'Descuento comercial'

        # Taxes
        if pos_line.tax_ids_after_fiscal_position:
            impuesto = self._build_tax_detail(pos_line)
            linea.append(impuesto)

        return linea
```

#### Step 4: Online vs Offline Handling

**Decision Tree:**

```python
def _should_submit_immediately(self):
    """Determine if should submit now or queue"""

    # Check 1: Is e-invoice enabled?
    if not self.l10n_cr_is_einvoice:
        return False

    # Check 2: Is internet available?
    if not self._l10n_cr_is_online():
        return False

    # Check 3: Is outside business hours? (queue for later)
    now = fields.Datetime.now()
    if now.hour < 6 or now.hour > 22:
        # Hacienda API slower at night
        return False

    # Check 4: Queue size (avoid overload)
    queue_size = self.env['l10n_cr.pos.offline.queue'].search_count([
        ('state', '=', 'pending')
    ])
    if queue_size > 100:
        # Too many queued, process those first
        return False

    return True
```

**Offline Queue Implementation:**

```python
class PosOfflineQueue(models.Model):
    _name = 'l10n_cr.pos.offline.queue'
    _description = 'Offline E-Invoice Queue'
    _order = 'create_date'

    # Relations
    pos_order_id = fields.Many2one('pos.order', required=True, ondelete='cascade')
    einvoice_document_id = fields.Many2one('l10n_cr.einvoice.document', ondelete='cascade')

    # Queue data
    xml_data = fields.Text('Signed XML', required=True)
    state = fields.Selection([
        ('pending', 'Pending Sync'),
        ('syncing', 'Syncing Now'),
        ('synced', 'Successfully Synced'),
        ('failed', 'Sync Failed'),
    ], default='pending', index=True)

    # Retry logic
    retry_count = fields.Integer(default=0)
    max_retries = fields.Integer(default=5)
    last_sync_attempt = fields.Datetime()
    last_error = fields.Text()

    # Priority
    priority = fields.Integer(default=10, help='Lower = higher priority')

    def process_sync(self):
        """Process single queue entry"""
        self.ensure_one()

        if self.state != 'pending':
            return

        self.state = 'syncing'
        self.last_sync_attempt = fields.Datetime.now()

        try:
            # Submit to Hacienda
            api = self.env['l10n_cr.hacienda.api']
            response = api.submit_invoice_xml(
                xml_content=self.xml_data,
                clave=self.einvoice_document_id.clave,
                company=self.pos_order_id.company_id,
            )

            if response['success']:
                # Mark as synced
                self.state = 'synced'
                self.einvoice_document_id.write({
                    'state': 'submitted',
                    'hacienda_submission_date': fields.Datetime.now(),
                })
                self.pos_order_id.l10n_cr_hacienda_status = 'pending'

                # Notify POS terminal
                self._send_bus_notification('synced')

            else:
                raise UserError(response.get('message', 'Unknown error'))

        except Exception as e:
            self.retry_count += 1
            self.last_error = str(e)

            if self.retry_count >= self.max_retries:
                self.state = 'failed'
                self._notify_manager()
            else:
                self.state = 'pending'
                # Exponential backoff
                self.priority = self.retry_count * 10

            _logger.error(f'Queue sync failed for {self.pos_order_id.name}: {e}')

    def _send_bus_notification(self, status):
        """Send real-time update to POS terminal"""
        channel = f'pos_session_{self.pos_order_id.session_id.id}'

        self.env['bus.bus']._sendone(channel, 'einvoice_sync_update', {
            'order_id': self.pos_order_id.id,
            'status': status,
            'clave': self.einvoice_document_id.clave,
        })
```

#### Step 5: Status Polling

**Scheduled Action:**
```python
@api.model
def cron_poll_hacienda_status(self):
    """Check status of pending invoices"""

    # Get submitted but not accepted/rejected
    pending_docs = self.env['l10n_cr.einvoice.document'].search([
        ('state', '=', 'submitted'),
        ('hacienda_submission_date', '>', fields.Datetime.now() - timedelta(hours=24)),
    ], limit=100)

    api = self.env['l10n_cr.hacienda.api']

    for doc in pending_docs:
        try:
            status = api.check_invoice_status(doc.clave, doc.company_id)

            if status['estado'] == 'aceptado':
                doc.write({
                    'state': 'accepted',
                    'hacienda_acceptance_date': fields.Datetime.now(),
                    'hacienda_message': status.get('mensaje'),
                })

                # Update POS order
                if doc.pos_order_ids:
                    doc.pos_order_ids.l10n_cr_hacienda_status = 'accepted'

                # Send email
                doc.action_send_email()

            elif status['estado'] == 'rechazado':
                doc.write({
                    'state': 'rejected',
                    'hacienda_message': status.get('mensaje'),
                    'error_message': status.get('detalle'),
                })

                if doc.pos_order_ids:
                    doc.pos_order_ids.write({
                        'l10n_cr_hacienda_status': 'rejected',
                        'l10n_cr_hacienda_error': status.get('detalle'),
                    })

        except Exception as e:
            _logger.error(f'Status check failed for {doc.clave}: {e}')
```

### 5.3 Customer Data Capture

**UI Extension for POS:**

```javascript
// l10n_cr_einvoice/static/src/js/pos_customer_dialog.js

odoo.define('l10n_cr_einvoice.CustomerDialog', function(require) {
    'use strict';

    const { Component } = owl;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');

    class CRCustomerDialog extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = {
                id_type: '01',  // Default: Cédula Física
                id_number: '',
                name: '',
                email: '',
            };
        }

        get idTypeOptions() {
            return [
                { value: '01', label: 'Cédula Física (9 dígitos)' },
                { value: '02', label: 'Cédula Jurídica (10 dígitos)' },
                { value: '03', label: 'DIMEX (11-12 dígitos)' },
                { value: '04', label: 'NITE (10 dígitos)' },
                { value: '05', label: 'Extranjero (Pasaporte)' },
            ];
        }

        async confirm() {
            // Validate ID format
            if (!this._validateIdNumber()) {
                this.showPopup('ErrorPopup', {
                    title: 'ID Inválido',
                    body: 'El número de identificación no es válido para el tipo seleccionado',
                });
                return;
            }

            // Check if customer exists
            const partner = await this._findOrCreatePartner();

            // Return customer data
            this.trigger('confirm', {
                partner_id: partner.id,
                id_type: this.state.id_type,
                id_number: this.state.id_number,
                name: this.state.name || partner.name,
                email: this.state.email || partner.email,
            });
        }

        _validateIdNumber() {
            const { id_type, id_number } = this.state;

            const validations = {
                '01': /^\d{9}$/,           // Cédula Física
                '02': /^\d{10}$/,          // Cédula Jurídica
                '03': /^\d{11,12}$/,       // DIMEX
                '04': /^\d{10}$/,          // NITE
                '05': /^[A-Za-z0-9]{1,20}$/, // Extranjero
            };

            return validations[id_type].test(id_number);
        }

        async _findOrCreatePartner() {
            const partners = await this.rpc({
                model: 'res.partner',
                method: 'search_read',
                domain: [
                    ['l10n_cr_identification_type', '=', this.state.id_type],
                    ['l10n_cr_identification_number', '=', this.state.id_number],
                ],
                fields: ['id', 'name', 'email'],
                limit: 1,
            });

            if (partners.length > 0) {
                return partners[0];
            }

            // Create new partner
            const partner_id = await this.rpc({
                model: 'res.partner',
                method: 'create',
                args: [{
                    name: this.state.name,
                    email: this.state.email,
                    l10n_cr_identification_type: this.state.id_type,
                    l10n_cr_identification_number: this.state.id_number,
                }],
            });

            return { id: partner_id, name: this.state.name, email: this.state.email };
        }
    }

    CRCustomerDialog.template = 'CRCustomerDialog';

    return CRCustomerDialog;
});
```

**XML Template:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates id="template" xml:space="preserve">
    <t t-name="CRCustomerDialog">
        <div class="popup-customer-dialog">
            <header>
                <h3>Datos del Cliente</h3>
                <p>Para generar factura electrónica</p>
            </header>

            <main>
                <div class="form-group">
                    <label>Tipo de Identificación</label>
                    <select t-model="state.id_type">
                        <t t-foreach="idTypeOptions" t-as="option">
                            <option t-att-value="option.value"
                                    t-esc="option.label"/>
                        </t>
                    </select>
                </div>

                <div class="form-group">
                    <label>Número de Identificación</label>
                    <input type="text"
                           t-model="state.id_number"
                           placeholder="Ingrese número"
                           autofocus="true"/>
                </div>

                <div class="form-group">
                    <label>Nombre</label>
                    <input type="text" t-model="state.name"/>
                </div>

                <div class="form-group">
                    <label>Correo Electrónico (opcional)</label>
                    <input type="email" t-model="state.email"/>
                </div>
            </main>

            <footer>
                <button class="button cancel" t-on-click="cancel">
                    Cancelar
                </button>
                <button class="button confirm" t-on-click="confirm">
                    Confirmar
                </button>
            </footer>
        </div>
    </t>
</templates>
```

### 5.4 Payment Method Mapping

**Extend Payment Methods:**

```python
class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    l10n_cr_payment_code = fields.Selection([
        ('01', 'Efectivo'),
        ('02', 'Tarjeta'),
        ('03', 'Cheque'),
        ('04', 'Transferencia Bancaria'),
        ('05', 'SINPE Móvil'),
        ('99', 'Otros'),
    ], string='Hacienda Payment Code')

    l10n_cr_requires_reference = fields.Boolean(
        string='Requires Reference',
        help='Check if payment requires reference number (e.g., SINPE transaction ID)',
        compute='_compute_l10n_cr_requires_reference',
        store=True,
    )

    @api.depends('l10n_cr_payment_code')
    def _compute_l10n_cr_requires_reference(self):
        for method in self:
            # SINPE Móvil requires transaction ID
            method.l10n_cr_requires_reference = (
                method.l10n_cr_payment_code == '05'
            )

class PosPayment(models.Model):
    _inherit = 'pos.payment'

    l10n_cr_transaction_reference = fields.Char(
        string='Transaction Reference',
        help='SINPE transaction ID or check number',
    )
```

**POS UI Extension:**
```javascript
// Prompt for SINPE transaction ID
async _processSinpePayment(payment_method, amount) {
    const { confirmed, payload } = await this.showPopup('TextInputPopup', {
        title: 'SINPE Móvil',
        startingValue: '',
        placeholder: 'ID de Transacción',
    });

    if (confirmed) {
        const payment = this.currentOrder.add_paymentline(payment_method);
        payment.set_amount(amount);
        payment.l10n_cr_transaction_reference = payload;
    }
}
```

### 5.5 Multi-Step Workflows

#### Refunds

**Process:**
1. POS creates refund order
2. Link to original order
3. Generate NC (Nota de Crédito) instead of TE
4. Reference original invoice clave

```python
class PosOrder(models.Model):
    _inherit = 'pos.order'

    def refund(self):
        """Override to handle e-invoice credit notes"""

        # Create refund using standard method
        refund_order = super().refund()

        # Generate Nota de Crédito if original had e-invoice
        if self.l10n_cr_einvoice_document_id:
            refund_order._l10n_cr_generate_credit_note(
                original_invoice=self.l10n_cr_einvoice_document_id
            )

        return refund_order

    def _l10n_cr_generate_credit_note(self, original_invoice):
        """Generate NC (Nota de Crédito)"""

        # Similar to TE generation but document_type = 'NC'
        einvoice_vals = {
            'document_type': 'NC',
            'reference_document_type': original_invoice.document_type,
            'reference_clave': original_invoice.clave,
            'reference_reason': 'Devolución de mercancía',
            # ... other fields
        }

        einvoice = self.env['l10n_cr.einvoice.document'].create(einvoice_vals)
        # ... continue with XML generation, signing, submission
```

#### Exchanges

**Pattern:** Create NC for returned items + new TE for new items

```python
def process_exchange(self, return_lines, new_lines):
    """Handle product exchange"""

    # 1. Create credit note for returns
    refund_order = self._create_refund_for_lines(return_lines)
    refund_order._l10n_cr_generate_credit_note(self.l10n_cr_einvoice_document_id)

    # 2. Create new order for new items
    new_order = self._create_order_for_lines(new_lines)
    new_order._l10n_cr_generate_einvoice()

    # 3. Link together
    self.env['l10n_cr.exchange.transaction'].create({
        'original_order_id': self.id,
        'refund_order_id': refund_order.id,
        'new_order_id': new_order.id,
    })
```

### 5.6 Error Scenarios and Handling

**Error Categories:**

1. **Validation Errors** (Pre-submission)
2. **Network Errors** (Connectivity)
3. **Hacienda Rejection** (Business rules)
4. **System Errors** (Internal)

**Error Handling Matrix:**

| Error Type | Severity | Action | User Impact |
|------------|----------|--------|-------------|
| Missing customer ID | Warning | Allow TE with generic ID | None - auto-recover |
| Invalid Cabys code | Error | Block submission | Must fix product |
| Network timeout | Warning | Queue for retry | Receipt shows "pending" |
| Hacienda rejection | Error | Log + notify | Manual review needed |
| Certificate expired | Critical | Block all e-invoices | Admin alert |

**Implementation:**

```python
class EInvoiceDocument(models.Model):
    _name = 'l10n_cr.einvoice.document'

    def action_submit_to_hacienda(self):
        """Submit with comprehensive error handling"""

        try:
            # Validation
            self._validate_before_submission()

            # Submit
            api = self.env['l10n_cr.hacienda.api']
            response = api.submit_invoice(
                xml=self.signed_xml,
                clave=self.clave,
                company=self.company_id,
            )

            if response['success']:
                self.write({
                    'state': 'submitted',
                    'hacienda_submission_date': fields.Datetime.now(),
                })
            else:
                self._handle_hacienda_error(response)

        except ValidationError as e:
            # Pre-submission validation failed
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
            raise

        except requests.exceptions.Timeout:
            # Network timeout - queue for retry
            self._queue_for_retry('Network timeout')

        except requests.exceptions.ConnectionError:
            # No internet - queue for retry
            self._queue_for_retry('Connection error')

        except Exception as e:
            # Unknown error - log and notify
            _logger.error(f'E-invoice submission failed: {e}', exc_info=True)
            self.write({
                'state': 'error',
                'error_message': f'System error: {str(e)}',
            })
            self._notify_admin_error(e)
            raise

    def _handle_hacienda_error(self, response):
        """Process Hacienda rejection"""

        error_code = response.get('codigo_error')
        error_message = response.get('mensaje')

        # Categorize error
        if error_code in ['X001', 'X002']:  # Business rule violations
            self.write({
                'state': 'rejected',
                'hacienda_message': error_message,
                'error_message': self._get_user_friendly_message(error_code),
            })

        elif error_code == 'X999':  # Temporary Hacienda issue
            self._queue_for_retry(f'Hacienda error: {error_message}')

        else:
            self.write({
                'state': 'error',
                'error_message': error_message,
            })

    def _queue_for_retry(self, reason):
        """Add to retry queue"""

        self.env['l10n_cr.einvoice.retry.queue'].create({
            'einvoice_document_id': self.id,
            'error_message': reason,
            'retry_count': 0,
        })

        self.write({
            'state': 'draft',  # Reset to allow retry
        })
```

### 5.7 Performance Requirements

**Target Metrics:**

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| E-invoice generation | < 3 seconds | 5 seconds |
| XML signing | < 1 second | 2 seconds |
| Hacienda submission | < 5 seconds | 10 seconds |
| Queue processing rate | 50/minute | 20/minute |
| POS order completion | < 10 seconds total | 15 seconds |

**Optimization Strategies:**

```python
# 1. Async Processing
def _l10n_cr_generate_einvoice(self):
    """Use job queue for heavy operations"""

    # Quick operations in sync
    consecutive = self._l10n_cr_generate_consecutive()
    clave = self._l10n_cr_generate_clave()

    # Heavy operations async
    self.with_delay(priority=5, eta=5).with_context(
        allowed_company_ids=self.company_id.ids
    )._async_generate_and_submit(consecutive, clave)

# 2. Batch Processing
@api.model
def cron_batch_submit_invoices(self):
    """Submit in batches for efficiency"""

    pending_docs = self.search([
        ('state', '=', 'signed'),
        ('hacienda_submission_date', '=', False),
    ], limit=100)

    # Group by company for certificate reuse
    by_company = defaultdict(list)
    for doc in pending_docs:
        by_company[doc.company_id.id].append(doc)

    for company_id, docs in by_company.items():
        # Reuse HTTP session
        api = self.env['l10n_cr.hacienda.api']
        with api._get_session() as session:
            for doc in docs:
                doc.with_context(
                    hacienda_session=session
                ).action_submit_to_hacienda()

# 3. Caching
@tools.ormcache('company_id')
def _get_company_certificate(self, company_id):
    """Cache certificates in memory"""
    company = self.env['res.company'].browse(company_id)
    return company.l10n_cr_certificate_data
```

---

## Implementation Guidelines

### 6.1 Step-by-Step Module Creation

**Creating a New GMS Extension Module:**

```bash
# 1. Create module directory
mkdir -p gms_pos
cd gms_pos

# 2. Create __init__.py
cat > __init__.py << 'EOF'
# -*- coding: utf-8 -*-
from . import models
EOF

# 3. Create __manifest__.py
cat > __manifest__.py << 'EOF'
{
    'name': 'GMS Point of Sale Extensions',
    'version': '19.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'GMS-specific POS customizations for gym management',
    'description': """
GMS Point of Sale Extensions
=============================

Extensions to Odoo POS for GMS (Gym Management System):
- Integration with l10n_cr_einvoice for Costa Rica compliance
- Membership discount application
- Equipment rental tracking
- Locker assignment
- Personal trainer session sales
    """,
    'author': 'GMS Development Team',
    'website': 'https://gms-cr.com',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale',
        'l10n_cr_einvoice',
        'sale_subscription',  # For memberships
    ],
    'data': [
        'security/gms_pos_security.xml',
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
        'views/pos_session_views.xml',
        'views/pos_config_views.xml',
        'data/product_categories.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'gms_pos/static/src/js/**/*.js',
            'gms_pos/static/src/xml/**/*.xml',
            'gms_pos/static/src/css/**/*.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
EOF

# 4. Create models directory
mkdir -p models
cat > models/__init__.py << 'EOF'
# -*- coding: utf-8 -*-
from . import pos_order
from . import pos_session
from . import pos_config
EOF

# 5. Create views directory
mkdir -p views

# 6. Create security directory
mkdir -p security

# 7. Create static assets
mkdir -p static/src/{js,xml,css}

# 8. Create data directory
mkdir -p data
```

### 6.2 Development Workflow

**1. Enable Developer Mode:**
```
Settings → Activate Developer Mode
```

**2. Install Module:**
```
Apps → Update Apps List → Search "GMS POS" → Install
```

**3. Development Cycle:**
```bash
# Edit code
vim models/pos_order.py

# Update module
# Apps → GMS POS → Upgrade

# Or use CLI
odoo-bin -u gms_pos -d your_database --stop-after-init
```

**4. Debug:**
```python
import logging
_logger = logging.getLogger(__name__)

def my_method(self):
    import pdb; pdb.set_trace()  # Debugger
    _logger.info('Debug info: %s', self.name)
```

### 6.3 Testing Strategy

**Unit Tests:**
```python
# gms_pos/tests/__init__.py
from . import test_pos_einvoice_integration

# gms_pos/tests/test_pos_einvoice_integration.py
from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install', 'gms_pos')
class TestPosEInvoiceIntegration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'l10n_cr_cabys_code': '1234567890123',
        })

    def test_einvoice_generation_from_pos_order(self):
        """Test e-invoice is generated when POS order is validated"""

        # Create POS order
        order = self.env['pos.order'].create({
            'session_id': self.pos_config.current_session_id.id,
            'partner_id': self.env.ref('base.res_partner_1').id,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 100.0,
            })],
        })

        # Trigger e-invoice generation
        order._l10n_cr_generate_einvoice()

        # Assert e-invoice created
        self.assertTrue(order.l10n_cr_einvoice_document_id)
        self.assertEqual(order.l10n_cr_einvoice_document_id.document_type, 'TE')
        self.assertTrue(order.l10n_cr_clave)

    def test_offline_queue_when_no_internet(self):
        """Test invoice queued when offline"""

        # Mock offline
        self.env['l10n_cr.hacienda.api']._test_connection = lambda *args: False

        order = self._create_test_order()
        order._l10n_cr_generate_einvoice()

        # Should be queued
        self.assertTrue(order.l10n_cr_offline_queue)
        self.assertEqual(order.l10n_cr_hacienda_status, 'queued')

        # Check queue entry
        queue_entry = self.env['l10n_cr.pos.offline.queue'].search([
            ('pos_order_id', '=', order.id)
        ])
        self.assertTrue(queue_entry)
        self.assertEqual(queue_entry.state, 'pending')
```

**Run Tests:**
```bash
odoo-bin -c odoo.conf -d test_db --test-tags gms_pos --stop-after-init
```

### 6.4 Version Control Best Practices

**.gitignore for module:**
```
# Python
__pycache__/
*.pyc
*.pyo

# IDE
.vscode/
.idea/

# Odoo specific
*.pot
*.mo
```

**Git workflow:**
```bash
# Feature branch
git checkout -b feature/gms-pos-membership-integration

# Commit standards
git commit -m "[GMS_POS] Add membership discount calculation

- Extend pos.order with membership_discount field
- Compute discount based on partner membership level
- Apply discount at checkout
- Tests for all membership tiers

Refs: #123"

# Pull request template
```

### 6.5 Documentation Standards

**Module Documentation:**
```python
# models/pos_order.py

class PosOrder(models.Model):
    """
    Extend POS Order for GMS-specific features

    This model adds:
    - E-invoice integration for Costa Rica compliance
    - Membership discount calculation
    - Equipment rental tracking
    - Locker assignment

    Integration Points:
    - l10n_cr.einvoice.document: E-invoice generation
    - sale.subscription: Membership status
    - gms.equipment: Equipment rental

    Public API:
    - calculate_membership_discount(): Calculate member discount
    - assign_locker(): Assign locker to member

    Hooks:
    - _process_order(): Triggers e-invoice generation
    """
    _inherit = 'pos.order'
```

**Method Documentation:**
```python
def calculate_membership_discount(self):
    """
    Calculate discount based on member's subscription tier

    Discount tiers:
    - Basic: 5%
    - Premium: 10%
    - VIP: 15%
    - Corporate: 20%

    Returns:
        float: Discount percentage (0-100)

    Raises:
        UserError: If partner has no active membership

    Example:
        >>> order.partner_id.subscription_tier = 'premium'
        >>> order.calculate_membership_discount()
        10.0
    """
    self.ensure_one()

    if not self.partner_id.subscription_id:
        return 0.0

    tier_map = {
        'basic': 5.0,
        'premium': 10.0,
        'vip': 15.0,
        'corporate': 20.0,
    }

    return tier_map.get(self.partner_id.subscription_tier, 0.0)
```

---

## Code Examples

### 7.1 Complete Module Extension Example

**File: gms_pos/models/pos_order.py**

```python
# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    """GMS POS Order Extensions"""
    _inherit = 'pos.order'

    # === MEMBERSHIP INTEGRATION ===

    membership_discount_amount = fields.Monetary(
        string='Membership Discount',
        compute='_compute_membership_discount',
        store=True,
        currency_field='currency_id',
    )

    membership_tier = fields.Selection(
        related='partner_id.subscription_tier',
        string='Member Tier',
        store=True,
    )

    # === EQUIPMENT RENTAL ===

    equipment_rental_ids = fields.One2many(
        'gms.equipment.rental',
        'pos_order_id',
        string='Equipment Rentals',
    )

    has_equipment_rental = fields.Boolean(
        compute='_compute_has_equipment_rental',
        store=True,
    )

    # === LOCKER ASSIGNMENT ===

    locker_id = fields.Many2one(
        'gms.locker',
        string='Assigned Locker',
        ondelete='set null',
    )

    # === COMPUTEDS ===

    @api.depends('partner_id', 'partner_id.subscription_id', 'lines.price_subtotal')
    def _compute_membership_discount(self):
        """Calculate membership discount"""
        for order in self:
            if order.partner_id and order.partner_id.subscription_id:
                discount_pct = order._get_membership_discount_percentage()
                subtotal = sum(order.lines.mapped('price_subtotal'))
                order.membership_discount_amount = subtotal * (discount_pct / 100)
            else:
                order.membership_discount_amount = 0.0

    @api.depends('equipment_rental_ids')
    def _compute_has_equipment_rental(self):
        for order in self:
            order.has_equipment_rental = bool(order.equipment_rental_ids)

    # === BUSINESS LOGIC ===

    def _get_membership_discount_percentage(self):
        """Get discount % based on membership tier"""
        self.ensure_one()

        if not self.partner_id.subscription_id:
            return 0.0

        # Check if membership is active
        subscription = self.partner_id.subscription_id
        if subscription.stage_id.category != 'progress':
            return 0.0

        # Tier-based discounts
        tier_discounts = {
            'basic': 5.0,
            'premium': 10.0,
            'vip': 15.0,
            'corporate': 20.0,
        }

        return tier_discounts.get(self.partner_id.subscription_tier, 0.0)

    def action_assign_locker(self):
        """Wizard to assign locker to member"""
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_('Please select a customer first'))

        return {
            'name': _('Assign Locker'),
            'type': 'ir.actions.act_window',
            'res_model': 'gms.locker.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_pos_order_id': self.id,
            },
        }

    def action_add_equipment_rental(self):
        """Add equipment rental to order"""
        self.ensure_one()

        return {
            'name': _('Rent Equipment'),
            'type': 'ir.actions.act_window',
            'res_model': 'gms.equipment.rental.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_pos_order_id': self.id,
            },
        }

    # === OVERRIDE CORE METHODS ===

    @api.model
    def _process_order(self, order, existing_order):
        """Override to add GMS-specific processing"""

        # Process order normally
        pos_order = super()._process_order(order, existing_order)

        # Apply membership discount
        if pos_order.partner_id and pos_order.partner_id.subscription_id:
            pos_order._apply_membership_discount()

        # Process equipment rentals
        if order.get('equipment_rentals'):
            pos_order._process_equipment_rentals(order['equipment_rentals'])

        # Assign locker if requested
        if order.get('locker_id'):
            pos_order.locker_id = order['locker_id']

        return pos_order

    def _apply_membership_discount(self):
        """Apply membership discount to order lines"""
        self.ensure_one()

        discount_pct = self._get_membership_discount_percentage()

        if discount_pct > 0:
            for line in self.lines:
                # Only apply to products, not services
                if line.product_id.type == 'product':
                    line.discount = max(line.discount, discount_pct)

    def _process_equipment_rentals(self, rental_data):
        """Process equipment rental data from POS"""
        self.ensure_one()

        for rental in rental_data:
            self.env['gms.equipment.rental'].create({
                'pos_order_id': self.id,
                'partner_id': self.partner_id.id,
                'equipment_id': rental['equipment_id'],
                'rental_start': fields.Datetime.now(),
                'rental_duration': rental['duration'],
                'rental_amount': rental['amount'],
            })
```

### 7.2 View Extension Example

**File: gms_pos/views/pos_order_views.xml**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Extend POS Order Form View -->
    <record id="view_pos_order_form_gms" model="ir.ui.view">
        <field name="name">pos.order.form.gms</field>
        <field name="model">pos.order</field>
        <field name="inherit_id" ref="point_of_sale.view_pos_pos_form"/>
        <field name="arch" type="xml">

            <!-- Add membership info after partner -->
            <field name="partner_id" position="after">
                <field name="membership_tier" readonly="1"/>
                <field name="membership_discount_amount" readonly="1"/>
            </field>

            <!-- Add GMS tab -->
            <xpath expr="//notebook" position="inside">
                <page string="GMS Services" name="gms_services">
                    <group>
                        <group string="Locker">
                            <field name="locker_id"/>
                            <button name="action_assign_locker"
                                    string="Assign Locker"
                                    type="object"
                                    class="oe_highlight"
                                    attrs="{'invisible': [('locker_id', '!=', False)]}"/>
                        </group>

                        <group string="Equipment Rental">
                            <field name="has_equipment_rental" invisible="1"/>
                            <button name="action_add_equipment_rental"
                                    string="Add Equipment Rental"
                                    type="object"
                                    class="btn-primary"/>
                        </group>
                    </group>

                    <group string="Equipment Rentals">
                        <field name="equipment_rental_ids" nolabel="1">
                            <tree>
                                <field name="equipment_id"/>
                                <field name="rental_start"/>
                                <field name="rental_duration"/>
                                <field name="rental_amount"/>
                                <field name="state"/>
                            </tree>
                        </field>
                    </group>
                </page>
            </xpath>

            <!-- Add smart button for e-invoice -->
            <div name="button_box" position="inside">
                <button name="action_view_einvoice"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-file-text-o"
                        attrs="{'invisible': [('l10n_cr_einvoice_document_id', '=', False)]}">
                    <div class="o_stat_info">
                        <field name="l10n_cr_hacienda_status" widget="badge"/>
                        <span class="o_stat_text">E-Invoice</span>
                    </div>
                </button>
            </div>

        </field>
    </record>

    <!-- Extend POS Order Tree View -->
    <record id="view_pos_order_tree_gms" model="ir.ui.view">
        <field name="name">pos.order.tree.gms</field>
        <field name="model">pos.order</field>
        <field name="inherit_id" ref="point_of_sale.view_pos_order_tree"/>
        <field name="arch" type="xml">

            <field name="partner_id" position="after">
                <field name="membership_tier" optional="show"/>
                <field name="membership_discount_amount" optional="hide" sum="Total Discount"/>
            </field>

            <field name="state" position="after">
                <field name="l10n_cr_hacienda_status" optional="show" widget="badge"/>
            </field>

        </field>
    </record>

</odoo>
```

### 7.3 JavaScript Extension Example

**File: gms_pos/static/src/js/membership_discount.js**

```javascript
odoo.define('gms_pos.MembershipDiscount', function(require) {
    'use strict';

    const { Order } = require('point_of_sale.models');
    const { patch } = require('web.utils');
    const { Gui } = require('point_of_sale.Gui');

    // Extend Order model
    patch(Order.prototype, 'gms_pos.MembershipDiscount', {

        /**
         * Override set_partner to apply membership discount
         */
        set_partner(partner) {
            this._super(...arguments);

            if (partner && partner.subscription_tier) {
                this._applyMembershipDiscount(partner);
            }
        },

        /**
         * Apply membership discount to all order lines
         */
        _applyMembershipDiscount(partner) {
            const discountPct = this._getMembershipDiscountPercentage(partner);

            if (discountPct > 0) {
                // Show notification
                this.env.services.pos.showNotification(
                    `Member discount applied: ${discountPct}%`,
                    { type: 'success' }
                );

                // Apply to lines
                this.get_orderlines().forEach(line => {
                    // Only apply to products, not services
                    if (line.product.type === 'product') {
                        line.set_discount(Math.max(line.discount, discountPct));
                    }
                });
            }
        },

        /**
         * Get discount percentage based on membership tier
         */
        _getMembershipDiscountPercentage(partner) {
            const tierDiscounts = {
                'basic': 5,
                'premium': 10,
                'vip': 15,
                'corporate': 20,
            };

            return tierDiscounts[partner.subscription_tier] || 0;
        },

        /**
         * Export membership data with order
         */
        export_as_JSON() {
            const json = this._super(...arguments);

            // Add GMS-specific data
            json.membership_tier = this.partner ? this.partner.subscription_tier : false;
            json.membership_discount_amount = this.get_total_discount();
            json.equipment_rentals = this._exportEquipmentRentals();
            json.locker_id = this.locker_id || false;

            return json;
        },

        /**
         * Export equipment rental data
         */
        _exportEquipmentRentals() {
            // Implementation depends on equipment rental module
            return [];
        },
    });

    return Order;
});
```

### 7.4 Security Configuration Example

**File: gms_pos/security/gms_pos_security.xml**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="0">

        <!-- Security Groups -->
        <record id="group_gms_pos_user" model="res.groups">
            <field name="name">GMS POS User</field>
            <field name="category_id" ref="base.module_category_sales_point_of_sale"/>
            <field name="implied_ids" eval="[(4, ref('point_of_sale.group_pos_user'))]"/>
            <field name="comment">Basic POS access with GMS features</field>
        </record>

        <record id="group_gms_pos_manager" model="res.groups">
            <field name="name">GMS POS Manager</field>
            <field name="category_id" ref="base.module_category_sales_point_of_sale"/>
            <field name="implied_ids" eval="[(4, ref('group_gms_pos_user')), (4, ref('point_of_sale.group_pos_manager'))]"/>
            <field name="comment">Full POS management including GMS configuration</field>
        </record>

        <!-- Record Rules -->
        <record id="gms_equipment_rental_user_rule" model="ir.rule">
            <field name="name">Equipment Rental: User Access</field>
            <field name="model_id" ref="model_gms_equipment_rental"/>
            <field name="domain_force">[('partner_id.user_id', '=', user.id)]</field>
            <field name="groups" eval="[(4, ref('group_gms_pos_user'))]"/>
        </record>

        <record id="gms_equipment_rental_manager_rule" model="ir.rule">
            <field name="name">Equipment Rental: Manager Access</field>
            <field name="model_id" ref="model_gms_equipment_rental"/>
            <field name="domain_force">[(1, '=', 1)]</field>
            <field name="groups" eval="[(4, ref('group_gms_pos_manager'))]"/>
        </record>

    </data>
</odoo>
```

**File: gms_pos/security/ir.model.access.csv**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_gms_equipment_rental_user,gms.equipment.rental user,model_gms_equipment_rental,group_gms_pos_user,1,1,1,0
access_gms_equipment_rental_manager,gms.equipment.rental manager,model_gms_equipment_rental,group_gms_pos_manager,1,1,1,1
access_gms_locker_user,gms.locker user,model_gms_locker,group_gms_pos_user,1,0,0,0
access_gms_locker_manager,gms.locker manager,model_gms_locker,group_gms_pos_manager,1,1,1,1
access_pos_order_user,pos.order user,point_of_sale.model_pos_order,group_gms_pos_user,1,1,1,0
access_pos_order_manager,pos.order manager,point_of_sale.model_pos_order,group_gms_pos_manager,1,1,1,1
```

---

## Testing & Validation

### 8.1 Test Checklist

**Module Installation:**
- [ ] Module installs without errors
- [ ] All dependencies are met
- [ ] Demo data loads correctly
- [ ] Security groups created
- [ ] Menu items visible

**Model Extensions:**
- [ ] New fields appear in forms
- [ ] Computed fields calculate correctly
- [ ] Constraints validate properly
- [ ] Related fields sync correctly

**View Extensions:**
- [ ] XPath modifications apply
- [ ] No layout breaks
- [ ] All buttons functional
- [ ] Smart buttons show correct data

**Integration:**
- [ ] POS → E-Invoice generation works
- [ ] Offline queue captures orders
- [ ] Status updates in real-time
- [ ] Email delivery succeeds

**Performance:**
- [ ] Order creation < 10 seconds
- [ ] E-invoice generation < 5 seconds
- [ ] No N+1 queries
- [ ] Batch operations efficient

### 8.2 Test Scenarios

**Scenario 1: Standard POS Sale with E-Invoice**

```python
def test_scenario_standard_sale(self):
    """Complete flow: POS sale → E-invoice → Email"""

    # 1. Create POS session
    session = self.pos_config.open_session_cb()

    # 2. Create order with customer
    order = self.env['pos.order'].create({
        'session_id': session.id,
        'partner_id': self.partner_cr.id,  # Costa Rica partner
        'lines': [(0, 0, {
            'product_id': self.product.id,
            'qty': 2,
            'price_unit': 100.0,
        })],
    })

    # 3. Add payment
    payment = self.env['pos.payment'].create({
        'order_id': order.id,
        'payment_method_id': self.payment_method_cash.id,
        'amount': 200.0,
    })

    # 4. Validate order (triggers e-invoice)
    order.action_pos_order_paid()

    # 5. Assertions
    self.assertTrue(order.l10n_cr_einvoice_document_id)
    self.assertEqual(order.l10n_cr_einvoice_document_id.document_type, 'TE')
    self.assertTrue(order.l10n_cr_clave)
    self.assertTrue(order.l10n_cr_consecutive)

    # 6. Check XML generated
    einvoice = order.l10n_cr_einvoice_document_id
    self.assertTrue(einvoice.xml_content)
    self.assertTrue(einvoice.signed_xml)

    # 7. Check submitted (or queued if offline)
    self.assertIn(einvoice.state, ['submitted', 'draft'])

    # 8. Check QR code
    self.assertTrue(order.l10n_cr_qr_code)
```

**Scenario 2: Offline Mode**

```python
def test_scenario_offline_mode(self):
    """Order created offline, synced when online"""

    # 1. Mock offline
    with patch.object(type(self.env['l10n_cr.hacienda.api']),
                     '_test_connection',
                     return_value=False):

        # 2. Create order
        order = self._create_test_order()

        # 3. Should be queued
        self.assertTrue(order.l10n_cr_offline_queue)
        self.assertEqual(order.l10n_cr_hacienda_status, 'queued')

        # 4. Check queue entry
        queue_entry = self.env['l10n_cr.pos.offline.queue'].search([
            ('pos_order_id', '=', order.id)
        ])
        self.assertEqual(len(queue_entry), 1)
        self.assertEqual(queue_entry.state, 'pending')

    # 5. Mock online
    with patch.object(type(self.env['l10n_cr.hacienda.api']),
                     '_test_connection',
                     return_value=True):

        # 6. Process queue
        queue_entry.process_sync()

        # 7. Should be synced
        self.assertEqual(queue_entry.state, 'synced')
        self.assertFalse(order.l10n_cr_offline_queue)
        self.assertEqual(order.l10n_cr_hacienda_status, 'pending')
```

**Scenario 3: Membership Discount**

```python
def test_scenario_membership_discount(self):
    """Member gets automatic discount"""

    # 1. Create member with premium subscription
    member = self.env['res.partner'].create({
        'name': 'Premium Member',
        'subscription_tier': 'premium',
        'subscription_id': self.subscription_premium.id,
    })

    # 2. Create order
    order = self._create_test_order(partner=member)

    # 3. Check discount applied
    self.assertEqual(order.membership_discount_amount, 20.0)  # 10% of 200

    # 4. Check line discount
    for line in order.lines:
        self.assertEqual(line.discount, 10.0)
```

### 8.3 Performance Testing

**Load Test:**
```python
import time
from odoo.tests import TransactionCase

class TestPosPerformance(TransactionCase):

    def test_order_creation_performance(self):
        """Order creation should be fast"""

        start = time.time()

        for i in range(100):
            order = self._create_test_order()

        elapsed = time.time() - start
        avg_time = elapsed / 100

        self.assertLess(avg_time, 1.0,
                       f'Order creation too slow: {avg_time:.2f}s')

    def test_einvoice_generation_performance(self):
        """E-invoice generation should be fast"""

        order = self._create_test_order()

        start = time.time()
        order._l10n_cr_generate_einvoice()
        elapsed = time.time() - start

        self.assertLess(elapsed, 3.0,
                       f'E-invoice generation too slow: {elapsed:.2f}s')

    def test_batch_processing_performance(self):
        """Batch queue processing should be efficient"""

        # Create 50 queued entries
        for i in range(50):
            self.env['l10n_cr.pos.offline.queue'].create({
                'pos_order_id': self._create_test_order().id,
                'einvoice_document_id': self._create_test_einvoice().id,
                'xml_data': '<xml>test</xml>',
                'state': 'pending',
            })

        # Process batch
        start = time.time()
        self.env['l10n_cr.pos.offline.queue'].process_sync_batch(batch_size=50)
        elapsed = time.time() - start

        self.assertLess(elapsed, 60.0,
                       f'Batch processing too slow: {elapsed:.2f}s')
```

---

## Migration & Updates

### 9.1 Version Upgrade Strategy

**When Odoo Updates:**

1. **Test in Staging:**
```bash
# Create test database
createdb gms_test_upgrade

# Restore production backup
pg_restore -d gms_test_upgrade production_backup.dump

# Upgrade Odoo
git pull odoo/odoo
git checkout 19.0  # New version

# Test upgrade
odoo-bin -d gms_test_upgrade --update all --stop-after-init

# Run tests
odoo-bin -d gms_test_upgrade --test-tags gms_pos --stop-after-init
```

2. **Check for Breaking Changes:**
```python
# Search for deprecated methods
grep -r "_get_" odoo/addons/point_of_sale/models/*.py

# Check manifest dependencies
diff old_manifest.py new_manifest.py
```

3. **Update Custom Code:**
```python
# Example: Method renamed
# OLD (Odoo 18):
def _process_order(self, order):
    pass

# NEW (Odoo 19):
def _process_order(self, order, existing_order):
    pass

# Update custom module:
@api.model
def _process_order(self, order, existing_order=None):
    # Handle both old and new signatures
    return super()._process_order(order, existing_order)
```

### 9.2 Data Migration

**Migration Script Example:**

```python
# migrations/19.0.1.1.0/post-migrate.py

def migrate(cr, version):
    """Migrate data for version 19.0.1.1.0"""

    # 1. Add new field data
    cr.execute("""
        UPDATE pos_order
        SET membership_tier = partner.subscription_tier
        FROM res_partner partner
        WHERE pos_order.partner_id = partner.id
        AND partner.subscription_tier IS NOT NULL
    """)

    # 2. Update computed fields
    cr.execute("""
        UPDATE pos_order
        SET membership_discount_amount =
            CASE membership_tier
                WHEN 'basic' THEN amount_total * 0.05
                WHEN 'premium' THEN amount_total * 0.10
                WHEN 'vip' THEN amount_total * 0.15
                WHEN 'corporate' THEN amount_total * 0.20
                ELSE 0
            END
        WHERE membership_tier IS NOT NULL
    """)

    # 3. Clean up old data
    cr.execute("""
        DELETE FROM l10n_cr_pos_offline_queue
        WHERE state = 'synced'
        AND create_date < NOW() - INTERVAL '90 days'
    """)
```

### 9.3 Module Version Control

**__manifest__.py versioning:**

```python
{
    'name': 'GMS Point of Sale Extensions',
    # Version format: ODOO.MAJOR.MINOR.PATCH
    # 19.0.1.0.0 = Odoo 19, Major 1, Minor 0, Patch 0
    'version': '19.0.1.0.0',

    # Update with each change:
    # - Patch: Bug fixes (19.0.1.0.1)
    # - Minor: New features (19.0.1.1.0)
    # - Major: Breaking changes (19.0.2.0.0)
    # - Odoo: Odoo version upgrade (20.0.1.0.0)
}
```

**CHANGELOG.md:**

```markdown
# Changelog

## [19.0.1.1.0] - 2025-12-29

### Added
- Membership discount calculation
- Equipment rental tracking
- Locker assignment feature

### Changed
- Improved e-invoice generation performance
- Updated offline queue retry logic

### Fixed
- Fixed discount not applying to membership tiers
- Corrected QR code generation for foreign customers

### Migration Notes
- Run `odoo-bin -d your_db -u gms_pos`
- Review membership tier mappings in partner records
```

---

## Conclusion

### Summary of Best Practices

**Module Strategy:**
1. ✅ Use inheritance, not forking
2. ✅ Follow Odoo naming conventions
3. ✅ Maintain clean dependencies
4. ✅ Document public APIs
5. ✅ Test thoroughly

**Integration Patterns:**
1. ✅ Direct model relationships for tight coupling
2. ✅ Event hooks for loose coupling
3. ✅ Offline queue for reliability
4. ✅ Bus messaging for real-time updates
5. ✅ Scheduled actions for background jobs

**Code Quality:**
1. ✅ Write comprehensive tests
2. ✅ Document all methods
3. ✅ Use meaningful variable names
4. ✅ Handle errors gracefully
5. ✅ Optimize for performance

### Current GMS Architecture Assessment

The existing `l10n_cr_einvoice` module demonstrates **excellent architecture**:

**Strengths:**
- ✅ Proper model inheritance
- ✅ Clean separation of concerns
- ✅ Comprehensive error handling
- ✅ Offline queue implementation
- ✅ Well-documented code

**Recommended Next Steps:**

1. **Create gms_pos module** using inheritance pattern
2. **Extend POS UI** with JavaScript components
3. **Add membership integration** for discounts
4. **Implement equipment rental** tracking
5. **Create comprehensive tests**

### Resources

**Odoo Documentation:**
- [Official Odoo Documentation](https://www.odoo.com/documentation/19.0/)
- [Odoo ORM API](https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html)
- [Odoo Views](https://www.odoo.com/documentation/19.0/developer/reference/backend/views.html)

**Community Resources:**
- [Odoo Community Association](https://odoo-community.org/)
- [OCA Guidelines](https://github.com/OCA/maintainer-tools)
- [Odoo Forums](https://www.odoo.com/forum)

**GMS-Specific:**
- Internal documentation: `/docs/`
- Test suite: `/l10n_cr_einvoice/tests/`
- Example modules: `/odoo/addons/pos_enterprise/`

---

**Document Status:** Production Ready
**Next Review:** After Odoo 20.0 release
**Contact:** GMS Development Team

---
