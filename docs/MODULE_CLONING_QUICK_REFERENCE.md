# Module Cloning & Integration Quick Reference
## Fast Reference Guide for Odoo Module Customization

**Version:** 1.0.0
**Date:** December 29, 2025

---

## Quick Decision Tree

```
Need to customize Odoo module?
  │
  ├─► Adding features? ────────────► USE INHERITANCE ✅
  │
  ├─► Changing behavior? ──────────► USE INHERITANCE ✅
  │
  ├─► Industry-specific? ──────────► USE INHERITANCE ✅
  │
  └─► Complete replacement? ───────► RARELY NEEDED ❌
                                     (99% use inheritance)
```

---

## Three Approaches Compared

### Option 1: Inheritance (RECOMMENDED 99%)

**When:** Almost always
**Effort:** Low
**Maintenance:** Low
**Update Safety:** Excellent

```python
# Create: gms_pos/__manifest__.py
{
    'name': 'GMS POS Extensions',
    'depends': ['point_of_sale', 'l10n_cr_einvoice'],
}

# Create: gms_pos/models/pos_order.py
class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Add new fields
    gms_custom_field = fields.Char()

    # Override methods
    def _process_order(self, order, existing_order):
        result = super()._process_order(order, existing_order)
        # Custom logic here
        return result
```

**Pros:**
- ✅ No code duplication
- ✅ Automatic Odoo updates
- ✅ Easy to maintain
- ✅ Can be disabled

**Cons:**
- ❌ Can't remove core features

### Option 2: Complete Fork (AVOID)

**When:** Never (99.9% of cases)
**Effort:** Very High
**Maintenance:** Very High
**Update Safety:** Poor

**Why Avoid:**
- ❌ Breaks Odoo updates
- ❌ Duplicate 1000s of lines
- ❌ $50k-100k/year maintenance
- ❌ Security patch hell

### Option 3: Wrapper (RARE)

**When:** Multi-tenant, complex audit
**Effort:** Medium
**Maintenance:** Medium

```python
class GmsPosOrderWrapper(models.Model):
    _name = 'gms.pos.order'
    _inherit = 'pos.order'

    # Intercept all calls
```

---

## Module Structure Template

```
gms_pos/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── pos_order.py
│   ├── pos_session.py
│   └── pos_config.py
├── views/
│   ├── pos_order_views.xml
│   └── pos_session_views.xml
├── security/
│   ├── gms_pos_security.xml
│   └── ir.model.access.csv
├── static/
│   └── src/
│       ├── js/
│       ├── xml/
│       └── css/
└── data/
    └── initial_data.xml
```

---

## Common Extension Patterns

### 1. Add Fields

```python
class PosOrder(models.Model):
    _inherit = 'pos.order'

    gms_membership_discount = fields.Monetary(
        string='Member Discount',
        compute='_compute_membership_discount',
        store=True,
    )
```

### 2. Override Methods

```python
@api.model
def _process_order(self, order, existing_order):
    # Call parent
    result = super()._process_order(order, existing_order)

    # Custom logic
    if result.partner_id.is_member:
        result.apply_membership_discount()

    return result
```

### 3. Add New Methods

```python
def apply_membership_discount(self):
    """New method specific to GMS"""
    self.ensure_one()
    discount = self.partner_id.get_membership_discount()
    for line in self.lines:
        line.discount = max(line.discount, discount)
```

### 4. Extend Views (XPath)

```xml
<record id="view_pos_order_form_gms" model="ir.ui.view">
    <field name="name">pos.order.form.gms</field>
    <field name="model">pos.order</field>
    <field name="inherit_id" ref="point_of_sale.view_pos_pos_form"/>
    <field name="arch" type="xml">

        <!-- Add field after partner -->
        <field name="partner_id" position="after">
            <field name="gms_membership_discount"/>
        </field>

        <!-- Add new tab -->
        <xpath expr="//notebook" position="inside">
            <page string="GMS Services">
                <!-- Your content -->
            </page>
        </xpath>

    </field>
</record>
```

---

## POS ↔ E-Invoice Integration Pattern

### Current Architecture (Excellent Example)

```python
# POS Order extends itself
class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Link to e-invoice
    l10n_cr_einvoice_document_id = fields.Many2one(
        'l10n_cr.einvoice.document'
    )

    # Generate on order validation
    def _process_order(self, order, existing_order):
        result = super()._process_order(order, existing_order)

        if result.l10n_cr_is_einvoice:
            result._l10n_cr_generate_einvoice()

        return result
```

### Integration Methods

**1. Direct Relationship (Tight Coupling)**
```python
einvoice_document_id = fields.Many2one('l10n_cr.einvoice.document')
```

**2. Event-Driven (Loose Coupling)**
```python
def _process_order(self, order, existing_order):
    result = super()._process_order(order, existing_order)
    result._trigger_einvoice_generation()  # Event hook
    return result
```

**3. Offline Queue (Reliability)**
```python
if not self._is_online():
    self.env['l10n_cr.pos.offline.queue'].create({
        'pos_order_id': self.id,
        'xml_data': signed_xml,
    })
```

**4. Bus Messaging (Real-time)**
```python
self.env['bus.bus']._sendone(
    channel='pos_session_123',
    notification_type='einvoice_update',
    message={'status': 'accepted'}
)
```

---

## Naming Conventions

### Modules
```
Format: gms_<functional_area>
Examples:
  - gms_pos
  - gms_membership
  - gms_crm
  - gms_inventory
```

### Models
```python
# Extended models (keep original name)
class PosOrder(models.Model):
    _inherit = 'pos.order'

# New models
class GmsMember(models.Model):
    _name = 'gms.member'
```

### Fields
```python
# On standard models (use x_ prefix)
x_gms_membership_level = fields.Selection()

# On GMS models (no prefix)
membership_level = fields.Selection()
```

### XML IDs
```
Format: <module>.<entity>_<name>

Examples:
  - gms_pos.view_pos_order_form
  - gms_pos.menu_gms_pos
  - gms_membership.group_member_manager
```

---

## Security Checklist

```xml
<!-- 1. Create groups -->
<record id="group_gms_pos_user" model="res.groups">
    <field name="name">GMS POS User</field>
    <field name="implied_ids" eval="[(4, ref('point_of_sale.group_pos_user'))]"/>
</record>

<!-- 2. Set access rights (ir.model.access.csv) -->
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_gms_pos_user,access pos.order,point_of_sale.model_pos_order,group_gms_pos_user,1,1,1,0

<!-- 3. Record rules -->
<record id="pos_order_rule" model="ir.rule">
    <field name="name">POS Orders: multi-company</field>
    <field name="model_id" ref="point_of_sale.model_pos_order"/>
    <field name="domain_force">[('company_id', 'in', company_ids)]</field>
</record>
```

---

## Testing Checklist

```python
# tests/test_gms_pos.py

from odoo.tests import TransactionCase, tagged

@tagged('post_install', 'gms_pos')
class TestGmsPosIntegration(TransactionCase):

    def setUp(self):
        super().setUp()
        # Setup test data

    def test_membership_discount(self):
        """Test member gets discount"""
        order = self._create_order()
        self.assertEqual(order.gms_membership_discount, 10.0)

    def test_einvoice_generation(self):
        """Test e-invoice created"""
        order = self._create_order()
        self.assertTrue(order.l10n_cr_einvoice_document_id)
```

---

## Common Mistakes to Avoid

### ❌ Don't Copy Core Files
```bash
# WRONG
cp odoo/addons/point_of_sale gms_pos
```

### ❌ Don't Use Same Model Name
```python
# WRONG
class PosOrder(models.Model):
    _name = 'pos.order'  # Conflict!
```

### ❌ Don't Hardcode IDs
```python
# WRONG
partner = self.env['res.partner'].browse(42)

# RIGHT
partner = self.env.ref('base.res_partner_1')
```

### ❌ Don't Forget Dependencies
```python
# WRONG
{
    'depends': ['base'],  # Missing point_of_sale!
}

# RIGHT
{
    'depends': ['point_of_sale', 'l10n_cr_einvoice'],
}
```

---

## Quick Commands

### Install/Update Module
```bash
# Install
odoo-bin -d mydb -i gms_pos

# Update
odoo-bin -d mydb -u gms_pos

# Update with tests
odoo-bin -d mydb -u gms_pos --test-tags gms_pos --stop-after-init
```

### Debug Mode
```python
import pdb; pdb.set_trace()  # Debugger

import logging
_logger = logging.getLogger(__name__)
_logger.info('Debug: %s', self.name)
```

### Find Inheritance Chain
```python
# In Odoo shell
model = env['pos.order']
print(model.__mro__)  # Method Resolution Order
```

---

## Performance Tips

### 1. Use @api.depends Correctly
```python
@api.depends('lines.price_subtotal')  # Specific path
def _compute_total(self):
    for order in self:
        order.total = sum(order.lines.mapped('price_subtotal'))
```

### 2. Batch Operations
```python
# Bad: N+1 queries
for order in orders:
    partner = order.partner_id
    print(partner.name)

# Good: Prefetch
orders.mapped('partner_id.name')
```

### 3. Use store=True
```python
custom_field = fields.Monetary(
    compute='_compute_field',
    store=True,  # Cache in database
)
```

### 4. Async for Heavy Operations
```python
self.with_delay()._generate_einvoice()
```

---

## Integration Checklist

When integrating POS with E-Invoice:

- [ ] Add Many2one link field
- [ ] Override order processing
- [ ] Add customer ID capture
- [ ] Implement offline queue
- [ ] Add status display in UI
- [ ] Create background sync job
- [ ] Add error handling
- [ ] Test offline mode
- [ ] Test status updates
- [ ] Document integration points

---

## Key Takeaways

1. **Always use inheritance** - Don't fork modules
2. **Follow naming conventions** - Consistency matters
3. **Test thoroughly** - Write tests first
4. **Document public APIs** - Help future developers
5. **Handle errors gracefully** - Never block POS operations
6. **Monitor performance** - Track critical paths
7. **Use existing patterns** - l10n_cr_einvoice is excellent example

---

## Resources

**Full Documentation:**
- `/docs/GMS_MODULE_ARCHITECTURE_GUIDE.md` - Complete guide (150+ pages)
- `/docs/POS_EINVOICE_INTEGRATION_SPEC.md` - Integration details (100+ pages)
- This document - Quick reference (5 min read)

**Example Code:**
- `/l10n_cr_einvoice/` - Production-ready e-invoice module
- `/odoo/addons/pos_enterprise/` - Odoo enterprise patterns
- `/odoo/addons/point_of_sale/` - Core POS module

**Official Odoo:**
- [Odoo Documentation](https://www.odoo.com/documentation/19.0/)
- [ORM API Reference](https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html)
- [View Architecture](https://www.odoo.com/documentation/19.0/developer/reference/backend/views.html)

---

**Remember:** When in doubt, use inheritance. The existing `l10n_cr_einvoice` module is an excellent example to follow.
