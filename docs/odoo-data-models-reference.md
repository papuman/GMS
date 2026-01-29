# Odoo Data Models Reference - GMS Relevant Models

**Generated:** 2025-12-28
**Version:** Odoo 19.0.0 Enterprise
**Scope:** Key data models across core + GMS-relevant modules
**Total Models:** 1,214 modules with models

---

## Core Base Models

### **res.partner** (Contacts/Customers)
**Module:** `base`
**Table:** `res_partner`
**Use in GMS:** Foundation for member profiles

**Key Fields:**
```python
name = fields.Char(required=True, index=True)          # Full name
email = fields.Char()                                   # Email address
phone = fields.Char()                                   # Phone number
mobile = fields.Char()                                  # Mobile number
street = fields.Char()                                  # Street address
city = fields.Char()
state_id = fields.Many2one('res.country.state')        # State/Province
country_id = fields.Many2one('res.country')            # Country
zip = fields.Char()                                     # Postal code
website = fields.Char()
comment = fields.Text()                                 # Internal notes
category_id = fields.Many2many('res.partner.category') # Tags
user_id = fields.Many2one('res.users')                 # Salesperson
company_id = fields.Many2one('res.company')            # Company
parent_id = fields.Many2one('res.partner')             # Parent contact
child_ids = fields.One2many('res.partner', 'parent_id') # Contacts
is_company = fields.Boolean()                           # Is a company?
type = fields.Selection([...])                          # Contact type
image_1920 = fields.Image()                            # Profile photo
```

**For GMS:** Extend this model to add:
- `is_gym_member`, `membership_level`, `barcode`, `member_since`, etc.

---

### **res.users** (Users/Authentication)
**Module:** `base`
**Table:** `res_users`
**Inherits:** `res.partner`
**Use in GMS:** Staff logins, member portal access

**Key Fields:**
```python
login = fields.Char(required=True, unique=True)        # Username
password = fields.Char()                                # Hashed (600k rounds)
partner_id = fields.Many2one('res.partner')            # Linked contact
company_id = fields.Many2one('res.company')
company_ids = fields.Many2many('res.company')          # Multi-company
groups_id = fields.Many2many('res.groups')             # Permissions
active = fields.Boolean(default=True)
lang = fields.Selection()                               # Language
tz = fields.Selection()                                 # Timezone
signature = fields.Html()                               # Email signature
```

**Password Security:**
- Uses `passlib` with PBKDF2-SHA512
- Min 600,000 rounds
- Passwords never stored in plain text

---

### **res.company** (Multi-Company)
**Module:** `base`
**Table:** `res_company`
**Use in GMS:** Multiple gym locations

**Key Fields:**
```python
name = fields.Char(required=True)                      # Company name
partner_id = fields.Many2one('res.partner')
currency_id = fields.Many2one('res.currency')          # Default currency
logo = fields.Binary()
email = fields.Char()
phone = fields.Char()
website = fields.Char()
```

---

## Accounting Models (account module)

### **account.move** (Invoices/Bills)
**Module:** `account`
**Table:** `account_move`
**Use in GMS:** Member invoicing, billing

**Key Fields:**
```python
name = fields.Char()                                    # Invoice number
move_type = fields.Selection([                          # Invoice/Bill/etc.
    ('entry', 'Journal Entry'),
    ('out_invoice', 'Customer Invoice'),
    ('out_refund', 'Customer Credit Note'),
    ('in_invoice', 'Vendor Bill'),
    ('in_refund', 'Vendor Credit Note'),
])
partner_id = fields.Many2one('res.partner')            # Customer
invoice_date = fields.Date()
invoice_date_due = fields.Date()
amount_untaxed = fields.Monetary()                     # Subtotal
amount_tax = fields.Monetary()                         # Tax amount
amount_total = fields.Monetary()                       # Total
state = fields.Selection([                              # Status
    ('draft', 'Draft'),
    ('posted', 'Posted'),
    ('cancel', 'Cancelled')
])
invoice_line_ids = fields.One2many('account.move.line', 'move_id')
payment_state = fields.Selection([                      # Payment status
    ('not_paid', 'Not Paid'),
    ('in_payment', 'In Payment'),
    ('paid', 'Paid'),
    ('partial', 'Partially Paid'),
    ('reversed', 'Reversed'),
    ('invoicing_legacy', 'Invoicing App Legacy')
])
```

**For GMS:**
- Membership fee invoices
- Retail product invoices
- Class package invoices
- Recurring billing

---

### **account.payment** (Payments)
**Module:** `account`
**Table:** `account_payment`
**Use in GMS:** Payment processing

**Key Fields:**
```python
partner_id = fields.Many2one('res.partner')
amount = fields.Monetary()
payment_type = fields.Selection([                       # Inbound/Outbound
    ('outbound', 'Send Money'),
    ('inbound', 'Receive Money'),
])
partner_type = fields.Selection([
    ('customer', 'Customer'),
    ('supplier', 'Vendor'),
])
date = fields.Date(default=fields.Date.context_today)
journal_id = fields.Many2one('account.journal')        # Payment method
payment_method_id = fields.Many2one('account.payment.method')
state = fields.Selection([
    ('draft', 'Draft'),
    ('posted', 'Validated'),
    ('sent', 'Sent'),
    ('reconciled', 'Reconciled'),
    ('cancelled', 'Cancelled')
])
```

---

### **account.tax** (Tax Rates)
**Module:** `account`
**Table:** `account_tax`
**Use in GMS:** Costa Rica tax compliance (13%, 4%, 2%, 1%, exempt)

**Key Fields:**
```python
name = fields.Char(required=True)                      # Tax name
type_tax_use = fields.Selection([
    ('sale', 'Sales'),
    ('purchase', 'Purchases'),
    ('none', 'None'),
])
amount_type = fields.Selection([
    ('percent', 'Percentage of Price'),
    ('fixed', 'Fixed'),
    ('division', 'Percentage of Price Tax Included'),
])
amount = fields.Float(required=True)                    # 13.0 for 13%
price_include = fields.Boolean()                        # Tax included?
country_id = fields.Many2one('res.country')
```

**Costa Rica Setup:**
```python
# IVA 13% (standard)
{'name': 'IVA 13%', 'amount': 13.0, 'type_tax_use': 'sale', 'country_id': CR}

# Reduced rates
{'name': 'IVA 4%', 'amount': 4.0, ...}
{'name': 'IVA 2%', 'amount': 2.0, ...}
{'name': 'IVA 1%', 'amount': 1.0, ...}

# Exempt
{'name': 'Exento', 'amount': 0.0, ...}
```

---

## Sale Models (sale module)

### **sale.order** (Sales Orders)
**Module:** `sale`
**Table:** `sale_order`
**Use in GMS:** Membership sales, quotations

**Key Fields:**
```python
name = fields.Char()                                    # SO number
partner_id = fields.Many2one('res.partner')
date_order = fields.Datetime()
validity_date = fields.Date()                           # Quote expiry
user_id = fields.Many2one('res.users')                 # Salesperson
order_line = fields.One2many('sale.order.line', 'order_id')
amount_untaxed = fields.Monetary()
amount_tax = fields.Monetary()
amount_total = fields.Monetary()
state = fields.Selection([
    ('draft', 'Quotation'),
    ('sent', 'Quotation Sent'),
    ('sale', 'Sales Order'),
    ('done', 'Locked'),
    ('cancel', 'Cancelled'),
])
invoice_ids = fields.Many2many('account.move')
payment_term_id = fields.Many2one('account.payment.term')
```

---

### **product.product** (Products/Services)
**Module:** `product`
**Table:** `product_product`
**Use in GMS:** Memberships, supplements, merchandise, classes

**Key Fields:**
```python
name = fields.Char(required=True)
default_code = fields.Char()                            # SKU/barcode
list_price = fields.Float()                             # Sale price
standard_price = fields.Float()                         # Cost
type = fields.Selection([
    ('consu', 'Consumable'),
    ('service', 'Service'),
    ('product', 'Storable Product')
])
categ_id = fields.Many2one('product.category')
taxes_id = fields.Many2many('account.tax')             # Taxes
image_1920 = fields.Image()
description_sale = fields.Text()
qty_available = fields.Float()                          # Stock quantity
```

**GMS Product Types:**
- Service: Memberships, personal training, classes
- Consumable/Storable: Supplements, merchandise, equipment

---

## CRM Models (crm module)

### **crm.lead** (Leads/Opportunities)
**Module:** `crm`
**Table:** `crm_lead`
**Use in GMS:** Prospect tracking, gym tours

**Key Fields:**
```python
name = fields.Char(required=True)                      # Opportunity name
partner_id = fields.Many2one('res.partner')
contact_name = fields.Char()                            # Lead name
email_from = fields.Char()
phone = fields.Char()
mobile = fields.Char()
type = fields.Selection([
    ('lead', 'Lead'),
    ('opportunity', 'Opportunity')
])
stage_id = fields.Many2one('crm.stage')                # Pipeline stage
user_id = fields.Many2one('res.users')                 # Salesperson
team_id = fields.Many2one('crm.team')                  # Sales team
expected_revenue = fields.Monetary()
probability = fields.Float()                            # Win probability
date_deadline = fields.Date()                           # Expected close
won_status = fields.Selection([
    ('won', 'Won'),
    ('lost', 'Lost'),
    ('pending', 'Pending')
])
lost_reason_id = fields.Many2one('crm.lost.reason')
```

---

## Point of Sale Models (point_of_sale module)

### **pos.session** (POS Sessions)
**Module:** `point_of_sale`
**Table:** `pos_session`
**Use in GMS:** Cash register management

**Key Fields:**
```python
name = fields.Char(required=True)
config_id = fields.Many2one('pos.config')              # POS terminal
user_id = fields.Many2one('res.users')                 # Cashier
start_at = fields.Datetime()
stop_at = fields.Datetime()
state = fields.Selection([
    ('opening_control', 'Opening Control'),
    ('opened', 'In Progress'),
    ('closing_control', 'Closing Control'),
    ('closed', 'Closed & Posted'),
])
cash_register_balance_start = fields.Monetary()
cash_register_balance_end_real = fields.Monetary()
cash_register_difference = fields.Monetary()
```

---

### **pos.order** (POS Orders)
**Module:** `point_of_sale`
**Table:** `pos_order`
**Use in GMS:** Retail sales tracking

**Key Fields:**
```python
name = fields.Char(required=True)                      # Receipt number
session_id = fields.Many2one('pos.session')
partner_id = fields.Many2one('res.partner')
lines = fields.One2many('pos.order.line', 'order_id')
amount_total = fields.Float()
amount_tax = fields.Float()
amount_paid = fields.Float()
amount_return = fields.Float()
date_order = fields.Datetime()
state = fields.Selection([
    ('draft', 'New'),
    ('paid', 'Paid'),
    ('done', 'Posted'),
    ('invoiced', 'Invoiced'),
    ('cancel', 'Cancelled')
])
payment_ids = fields.One2many('pos.payment', 'pos_order_id')
```

---

## Calendar Models (calendar module)

### **calendar.event** (Events/Appointments)
**Module:** `calendar`
**Table:** `calendar_event`
**Use in GMS:** Class scheduling (base - extend for gym classes)

**Key Fields:**
```python
name = fields.Char(required=True)                      # Event title
start = fields.Datetime(required=True)
stop = fields.Datetime(required=True)
allday = fields.Boolean()
partner_ids = fields.Many2many('res.partner')          # Attendees
location = fields.Char()
description = fields.Html()
recurrency = fields.Boolean()                           # Recurring?
rrule = fields.Char()                                   # Recurrence rule
rrule_type = fields.Selection([
    ('daily', 'Days'),
    ('weekly', 'Weeks'),
    ('monthly', 'Months'),
    ('yearly', 'Years')
])
end_type = fields.Selection([
    ('count', 'Number of repetitions'),
    ('end_date', 'End date')
])
```

**For GMS:** Extend for:
- `max_capacity`, `current_bookings`, `instructor_id`, `class_type_id`
- Waitlist management
- Booking restrictions by membership level

---

## Additional GMS-Relevant Models

### **mail.thread** (Messaging Mixin)
**Module:** `mail`
**Abstract Model:** Inherit to add messaging

**Features:**
- Activity tracking
- Message posting
- Email integration
- Followers system
- Notifications

**Usage:**
```python
class GymMember(models.Model):
    _name = 'gym.member'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(tracking=True)  # Track changes
    membership_state = fields.Selection(tracking=True)
```

---

### **stock.quant** (Inventory)
**Module:** `stock`
**Table:** `stock_quant`
**Use in GMS:** Supplement/merchandise inventory

**Key Fields:**
```python
product_id = fields.Many2one('product.product')
location_id = fields.Many2one('stock.location')
quantity = fields.Float()                               # Available qty
reserved_quantity = fields.Float()                      # Reserved
lot_id = fields.Many2one('stock.lot')                  # Lot/Serial number
```

---

### **loyalty.program** (Loyalty Programs)
**Module:** `loyalty`
**Table:** `loyalty_program`
**Use in GMS:** Member rewards, gamification

**Key Fields:**
```python
name = fields.Char(required=True)
program_type = fields.Selection([
    ('coupons', 'Coupons'),
    ('promotion', 'Promotions'),
    ('loyalty', 'Loyalty Cards'),
    ('buy_x_get_y', 'Buy X Get Y'),
])
rule_ids = fields.One2many('loyalty.rule', 'program_id')
reward_ids = fields.One2many('loyalty.reward', 'program_id')
```

---

### **sms.sms** (SMS Messages)
**Module:** `sms`
**Table:** `sms_sms`
**Use in GMS:** Member notifications

**Key Fields:**
```python
number = fields.Char(required=True)                    # Phone number
body = fields.Text(required=True)                      # Message content
partner_id = fields.Many2one('res.partner')
state = fields.Selection([
    ('outgoing', 'In Queue'),
    ('sent', 'Sent'),
    ('error', 'Error'),
    ('canceled', 'Canceled')
])
```

---

## Custom GMS Models (To Be Created)

### **Recommended Custom Models:**

#### **gym.member** (Extend res.partner or standalone)
```python
_name = 'gym.member'
_inherit = ['res.partner', 'mail.thread']

membership_level = fields.Selection([...])
membership_state = fields.Selection([...])
membership_start = fields.Date()
membership_end = fields.Date()
barcode = fields.Char(unique=True)
qr_code = fields.Binary()
emergency_contact_name = fields.Char()
emergency_contact_phone = fields.Char()
medical_notes = fields.Text()
check_in_ids = fields.One2many('gym.checkin', 'member_id')
class_booking_ids = fields.Many2many('gym.class')
```

#### **gym.class**
```python
_name = 'gym.class'
_inherit = ['mail.thread']

name = fields.Char(required=True)
instructor_id = fields.Many2one('res.users')
class_type_id = fields.Many2one('gym.class.type')
start_time = fields.Datetime(required=True)
end_time = fields.Datetime(required=True)
max_capacity = fields.Integer(default=20)
booked_member_ids = fields.Many2many('gym.member')
current_bookings = fields.Integer(compute='...')
waitlist_ids = fields.Many2many('gym.member')
location = fields.Char()
```

#### **gym.checkin**
```python
_name = 'gym.checkin'

member_id = fields.Many2one('gym.member', required=True)
check_in_time = fields.Datetime(default=fields.Datetime.now)
check_out_time = fields.Datetime()
entry_point = fields.Selection([...])  # Gate, POS, etc.
```

#### **gym.class.type**
```python
_name = 'gym.class.type'

name = fields.Char(required=True)  # Yoga, Spin, HIIT, etc.
description = fields.Text()
duration = fields.Integer()  # Minutes
difficulty_level = fields.Selection([...])
required_membership_level = fields.Selection([...])
```

---

## Model Relationships for GMS

```
res.partner (Base Contact)
    ├─> gym.member (Member Extension)
    │   ├─> gym.checkin (Check-ins)
    │   ├─> gym.class (Bookings - M2M)
    │   ├─> account.move (Invoices)
    │   └─> loyalty.card (Rewards)
    │
    ├─> sale.order (Membership Sales)
    │   └─> sale.order.line
    │       └─> product.product (Memberships)
    │
    ├─> pos.order (Retail Sales)
    │   └─> pos.order.line
    │       └─> product.product (Supplements)
    │
    └─> crm.lead (Prospects)
        └─> Convert to gym.member

gym.class
    ├─> gym.class.type (Class Category)
    ├─> res.users (Instructor)
    └─> gym.member (Bookings - M2M)

account.move (Invoices)
    ├─> account.move.line (Invoice Lines)
    ├─> account.payment (Payments)
    └─> account.tax (Taxes)
```

---

**Document Status:** ✅ Core data models documented
**Models Covered:** 25+ key models across 8 modules
**Next:** API contracts, development guide, integration patterns

**See Also:**
- [odoo-framework-deep-dive.md](./odoo-framework-deep-dive.md) - ORM & HTTP details
- [architecture.md](./architecture.md) - High-level architecture
