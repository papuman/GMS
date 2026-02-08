# Odoo Framework Architecture

**Generated:** 2025-12-28
**Version:** Odoo 19.0.0 Enterprise
**For:** GMS (Gym Management System) - Architectural Decision Support

---

## Executive Summary

Odoo is a **modular monolith** ERP framework built on a sophisticated ORM and plugin architecture. This document analyzes Odoo's architecture to support your decision on building GMS.

**Key Insight:** Odoo provides mature patterns for billing, memberships, POS, and access control that overlap significantly with your 400+ GMS features.

---

## Core Architecture Pattern

### **Modular Monolith with Plugin System**

```
┌─────────────────────────────────────────────────────────────┐
│                    ODOO FRAMEWORK CORE                      │
│  ┌──────────┐  ┌────────┐  ┌─────────┐  ┌───────────────┐ │
│  │   ORM    │  │  API   │  │ Routing │  │  Authentication│ │
│  │ (Models) │  │(RPC/REST)│ │(HTTP)  │  │   & Security  │ │
│  └──────────┘  └────────┘  └─────────┘  └───────────────┘ │
│  ┌──────────┐  ┌────────┐  ┌─────────┐  ┌───────────────┐ │
│  │  Views   │  │ Reports │  │  Cron  │  │  Translations  │ │
│  │ (QWeb)   │  │  (PDF)  │  │(Jobs)  │  │   (i18n/l10n) │ │
│  └──────────┘  └────────┘  └─────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              MODULE/ADDON ECOSYSTEM (1,369)                 │
│                                                             │
│  ┌─────────┐  ┌──────┐  ┌──────┐  ┌─────┐  ┌────────────┐│
│  │ Account │  │  CRM │  │ Sale │  │ POS │  │ [Custom    ││
│  │(Billing)│  │(Leads)│ │(Orders)│ │(Retail)│ │  Modules]  ││
│  └─────────┘  └──────┘  └──────┘  └─────┘  └────────────┘│
│                                                             │
│  Each module can:                                          │
│  • Define models (database tables)                        │
│  • Extend existing models (inheritance)                   │
│  • Add views (UI)                                         │
│  • Provide controllers (HTTP endpoints)                   │
│  • Declare dependencies on other modules                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. ORM Layer (Odoo Models)

### **Pattern:** Active Record with Multiple Inheritance

**Location:** `/odoo/models`, `/odoo/fields`

**Key Features:**
- **Automatic schema migration** - Odoo introspects models and updates PostgreSQL schema
- **Three types of inheritance:**
  1. **Classical** (`_inherit` - extend existing model)
  2. **Prototype** (`_name` + `_inherit` - copy and extend)
  3. **Delegation** (`_inherits` - composition via foreign key)
- **Computed fields** with dependencies
- **Constraints** (SQL and Python)
- **Record rules** (row-level security)

**Example Model:**
```python
from odoo import models, fields, api

class GymMember(models.Model):
    _name = 'gym.member'
    _description = 'Gym Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add messaging

    name = fields.Char(required=True)
    email = fields.Char()
    membership_id = fields.Many2one('product.product', domain="[('is_membership', '=', True)]")
    membership_state = fields.Selection([
        ('none', 'No Membership'),
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('expired', 'Expired')
    ], compute='_compute_membership_state', store=True)
    check_ins = fields.One2many('gym.checkin', 'member_id')

    @api.depends('membership_id', 'membership_id.expiry_date')
    def _compute_membership_state(self):
        # Auto-compute based on membership status
        for member in self:
            # ... logic ...
```

**Relevance to GMS:**
- ✅ Member models with complex relationships
- ✅ Membership states and auto-computation
- ✅ Activity tracking (check-ins, class bookings)
- ✅ Automatic database migrations

---

## 2. Module System

### **Pattern:** Dependency-Injected Plugins

**Location:** `/odoo/modules`

**Module Structure:**
```
gms_core/
├── __manifest__.py          # Module metadata
│   {
│     'name': 'GMS Core',
│     'depends': ['base', 'account', 'crm', 'calendar'],
│     'data': [...],         # XML files to load
│     'installable': True,
│     'application': True
│   }
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── gym_member.py
│   ├── gym_class.py
│   └── gym_membership.py
├── views/
│   ├── member_views.xml     # UI definitions
│   └── class_views.xml
├── security/
│   ├── ir.model.access.csv  # Model permissions
│   └── security.xml         # Record rules
├── controllers/
│   └── portal.py            # HTTP endpoints
├── data/
│   └── membership_types.xml # Initial data
└── static/
    └── src/                 # JavaScript/CSS
```

**Module Lifecycle:**
1. **Install** - Creates database tables, loads data, registers views
2. **Upgrade** - Migrates schema, runs upgrade scripts
3. **Uninstall** - Removes data (configurable)

**Relevance to GMS:**
- ✅ Clean separation of gym-specific logic
- ✅ Can depend on Odoo's account, CRM, POS modules
- ✅ Upgrade path as requirements evolve

---

## 3. API Layer

### **Dual API: XML-RPC + JSON-RPC**

**Location:** `/odoo/service/`, `/odoo/http.py`

#### **XML-RPC API** (Legacy, Stable)
```python
# External system calling Odoo
import xmlrpc.client

url = "http://localhost:8069"
db = "gym_db"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Search for active members
member_ids = models.execute_kw(db, uid, password,
    'gym.member', 'search',
    [[['membership_state', '=', 'active']]])

# Read member data
members = models.execute_kw(db, uid, password,
    'gym.member', 'read',
    [member_ids], {'fields': ['name', 'email', 'membership_id']})
```

#### **JSON-RPC API** (Modern)
```python
import requests
import json

url = "http://localhost:8069"
headers = {"Content-Type": "application/json"}

# Authenticate
auth_payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "common",
        "method": "login",
        "args": ["gym_db", "admin", "admin"]
    }
}
response = requests.post(f"{url}/jsonrpc", json=auth_payload, headers=headers)
uid = response.json()['result']

# Call model method
payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "object",
        "method": "execute_kw",
        "args": ["gym_db", uid, "admin", "gym.member", "check_in", [[member_id]]]
    }
}
response = requests.post(f"{url}/jsonrpc", json=payload, headers=headers)
```

#### **REST-like Controllers**
```python
from odoo import http
from odoo.http import request

class GymPortalController(http.Controller):

    @http.route('/gym/member/<int:member_id>/checkin', type='json', auth='user')
    def member_checkin(self, member_id, **kwargs):
        member = request.env['gym.member'].browse(member_id)
        if member.membership_state != 'active':
            return {'error': 'Membership not active'}

        checkin = request.env['gym.checkin'].create({
            'member_id': member_id,
            'check_in_time': fields.Datetime.now()
        })
        return {'success': True, 'checkin_id': checkin.id}

    @http.route('/gym/classes', type='http', auth='public', website=True)
    def list_classes(self, **kwargs):
        classes = request.env['gym.class'].search([
            ('start_date', '>=', fields.Date.today())
        ])
        return request.render('gms_core.class_list_template', {
            'classes': classes
        })
```

**Relevance to GMS:**
- ✅ Member portal (web routes)
- ✅ Mobile app integration (JSON-RPC)
- ✅ Access control kiosk (API calls)
- ✅ External integrations (payment gateways, etc.)

---

## 4. Key Modules for GMS

### **Account Module** (`/odoo/addons/account`)
**Purpose:** Invoicing, Payments, Tax Compliance

**Features:**
- Invoice generation (membership fees, retail)
- Payment recording (multiple methods)
- Tax management (⭐ Costa Rica compliance available via l10n_cr)
- Account reconciliation
- Financial reports

**Models:**
- `account.move` - Invoices, bills, credit notes
- `account.payment` - Payment transactions
- `account.tax` - Tax rates (13%, 4%, 2%, 1%, exempt for CR)
- `account.journal` - Cash, bank journals

**Relevance:** **HIGH**
- ✅ Handles billing for memberships, classes, retail
- ✅ Tax compliance (Costa Rica localization exists)
- ✅ Payment tracking and reconciliation

---

### **Sale Module** (`/odoo/addons/sale`)
**Purpose:** Sales Orders, Quotations

**Features:**
- Membership sales workflow
- Product catalog (memberships as products)
- Quotations → Orders → Invoices
- Recurring sales (subscriptions)
- Payment integration

**Models:**
- `sale.order` - Sales orders
- `sale.order.line` - Order line items
- `product.product` - Products (memberships, supplements, etc.)

**Relevance:** **HIGH**
- ✅ Membership purchases
- ✅ Retail product sales
- ✅ Subscription management (recurring memberships)

---

### **Point of Sale Module** (`/odoo/addons/point_of_sale`)
**Purpose:** Retail POS System

**Features:**
- Offline-capable POS interface
- Barcode scanning
- Multiple payment methods
- Cash management (open/close sessions)
- Receipt printing
- Product catalog
- Inventory integration

**Technology:** JavaScript (Owl framework) + Python backend

**Relevance:** **VERY HIGH**
- ✅ Gym retail (supplements, merchandise)
- ✅ Walk-in membership sales
- ✅ Quick member check-in at front desk
- ✅ Cash handling

**⚠️ Note:** POS is a full SPA (Single Page App) - can be customized or used as reference

---

### **CRM Module** (`/odoo/addons/crm`)
**Purpose:** Lead & Opportunity Management

**Features:**
- Lead capture (website forms, manual entry)
- Lead scoring
- Opportunity pipeline
- Activities & follow-ups
- Conversion to customers
- Win/loss analysis

**Models:**
- `crm.lead` - Leads/opportunities
- `crm.stage` - Pipeline stages
- `crm.team` - Sales teams

**Relevance:** **HIGH**
- ✅ Prospect tracking (gym tours, trials)
- ✅ Follow-up workflows
- ✅ Conversion tracking (leads → members)

---

### **Calendar Module** (`/odoo/addons/calendar`)
**Purpose:** Event & Appointment Scheduling

**Features:**
- Event creation
- Recurring events
- Attendee management
- Google Calendar integration
- Reminders

**Relevance:** **MODERATE**
- ✅ Class scheduling (base functionality)
- ❌ Lacks booking limits, waitlists (custom needed)
- ❌ No member-specific class restrictions

---

### **Portal Module** (`/odoo/addons/portal`)
**Purpose:** Customer Self-Service

**Features:**
- Customer login
- View invoices, payments
- Access documents
- Submit tickets
- Profile management

**Relevance:** **HIGH**
- ✅ Member portal
- ✅ Self-service account management
- ✅ Payment history viewing
- ✅ Class booking interface (with custom extension)

---

### **HR Module** (`/odoo/addons/hr`)
**Purpose:** Employee Management

**Features:**
- Employee records
- Attendance tracking
- Time off management
- Organizational structure
- Performance reviews

**Relevance:** **MODERATE**
- ✅ Staff/instructor management
- ✅ Attendance tracking (adaptable for members)
- ❌ Commission tracking needs customization

---

## 5. Security Model

### **Multi-Layer Security**

**1. Access Control Lists (ACLs)**
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_gym_member_user,gym.member.user,model_gym_member,base.group_user,1,0,0,0
access_gym_member_manager,gym.member.manager,model_gym_member,group_gym_manager,1,1,1,1
```

**2. Record Rules (Row-Level Security)**
```xml
<record id="gym_member_own_records_rule" model="ir.rule">
    <field name="name">Members: Own Records</field>
    <field name="model_id" ref="model_gym_member"/>
    <field name="domain_force">[('user_id', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('base.group_portal'))]"/>
</record>
```

**3. Field-Level Security**
```python
class GymMember(models.Model):
    _name = 'gym.member'

    ssn = fields.Char(groups="base.group_system")  # Only admins see
```

**Relevance to GMS:**
- ✅ Multi-user access control (reception, trainers, admin)
- ✅ Member privacy (GDPR/CCPA compliant)
- ✅ Portal users (members) see only their data

---

## 6. Database & ORM Patterns

### **PostgreSQL Integration**

**Features:**
- **Automatic migrations** - Add/remove fields without SQL
- **JSONB support** - Flexible data storage
- **Full-text search** - Built-in
- **Triggers & constraints** - Declarative in Python

**Example:**
```python
class GymClass(models.Model):
    _name = 'gym.class'
    _sql_constraints = [
        ('max_capacity_check', 'CHECK(current_attendees <= max_capacity)',
         'Class is overbooked!')
    ]

    current_attendees = fields.Integer(compute='_compute_attendees', store=True)
    max_capacity = fields.Integer(required=True)

    _constraints = [
        (lambda self: self.start_time < self.end_time,
         'Start time must be before end time', ['start_time', 'end_time'])
    ]
```

---

## 7. Integration & Extension Points

### **Ways to Extend Odoo for GMS:**

**1. Custom Modules** (Recommended)
- Build `gms_core`, `gms_access_control`, `gms_classes` modules
- Inherit from account, sale, CRM modules
- Add gym-specific models and logic

**2. Model Inheritance**
```python
# Extend res.partner (contacts) with gym member fields
class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_gym_member = fields.Boolean()
    membership_level = fields.Selection([...])
    barcode = fields.Char()  # For access control
```

**3. View Inheritance**
```xml
<!-- Add gym fields to partner form -->
<record id="view_partner_form_gym" model="ir.ui.view">
    <field name="name">res.partner.form.gym</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="base.view_partner_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='category_id']" position="after">
            <field name="is_gym_member"/>
            <field name="membership_level" attrs="{'invisible': [('is_gym_member', '=', False)]}"/>
        </xpath>
    </field>
</record>
```

**4. API Hooks**
```python
# Override create to add custom logic
@api.model_create_multi
def create(self, vals_list):
    # Send welcome email on member creation
    members = super().create(vals_list)
    for member in members:
        member.send_welcome_email()
    return members
```

---

## 8. Costa Rica Compliance

### **Localization Module:** `l10n_cr` (Community)

**Features:**
- Chart of accounts (Costa Rica GAAP)
- Tax rates (13% IVA, reduced rates)
- Electronic invoicing (Hacienda integration)
- TSE/DIMEX validation

**⚠️ Consideration:**
- Electronic invoicing via Tribu-CR requires separate integration
- Odoo has base support, but GMS may need custom connector

---

## Architectural Decision Framework

### **Option A: Build on Odoo (Full Stack)**

**What You Get:**
```
✅ account → Billing, invoicing, Costa Rica taxes
✅ sale → Membership sales, recurring billing
✅ point_of_sale → Retail POS for supplements
✅ crm → Lead management, gym tours
✅ portal → Member self-service
✅ calendar → Basic class scheduling (needs extension)
✅ hr → Staff management
✅ ORM → Database handling, migrations
✅ Security → Multi-user, ACLs, record rules
✅ API → Mobile app integration (JSON-RPC)
```

**Custom Modules Needed:**
```
❌ gms_classes → Class booking, capacity limits, waitlists
❌ gms_access_control → Check-in system, RFID integration
❌ gms_gamification → Points, badges, challenges (extend loyalty module)
❌ gms_analytics → Custom reports, KPIs
❌ gms_mobile_api → Enhanced API for mobile apps
```

**Pros:**
- ⏱️ **Faster time to market** - 60%+ features already exist
- 💰 **Lower development cost** - Reuse proven code
- 🔒 **Enterprise security** - Battle-tested
- 📈 **Scalability** - Handles large datasets
- 🌍 **i18n/l10n** - Already supports Costa Rica

**Cons:**
- 📚 **Learning curve** - Odoo ORM, module system
- 🏗️ **Framework lock-in** - Tied to Odoo architecture
- 🐘 **Heavy** - Full framework (may be overkill)
- 🔧 **Customization complexity** - Must work within Odoo patterns

---

### **Option B: Extract & Modernize**

**Extract These Components:**
```
✅ Billing logic from account module
✅ Subscription patterns from sale module
✅ Payment processing from account_payment
✅ Security model patterns
✅ Tax calculation logic
```

**Rebuild with Modern Stack:**
```
→ FastAPI / Django (Python) or Node.js/NestJS
→ PostgreSQL (keep)
→ React/Next.js frontend
→ Prisma/TypeORM for modern ORM
→ Stripe/payment gateway SDKs
```

**Pros:**
- 🎯 **Lightweight** - Only what you need
- 🆕 **Modern patterns** - Clean architecture
- 🚀 **Performance** - Optimized for GMS use case
- 📖 **Easier onboarding** - Standard frameworks

**Cons:**
- ⏳ **Longer development** - Rebuild functionality
- 💸 **Higher initial cost** - More coding required
- 🐛 **More bugs initially** - Less battle-tested
- 🔧 **Manual migrations** - No auto-schema updates

---

### **Option C: Hybrid Approach** (Recommended)

**Use Odoo For:**
```
✅ Billing & invoicing (account module)
✅ Costa Rica tax compliance (l10n_cr + account)
✅ Payment processing (account_payment)
✅ Admin backend (Odoo UI)
```

**Build Custom For:**
```
❌ Member portal (modern React/Next.js)
❌ Mobile apps (React Native + JSON-RPC to Odoo)
❌ Class booking system (custom, calls Odoo for billing)
❌ Access control kiosks (custom, syncs with Odoo)
```

**Integration:**
- Odoo handles money, compliance, admin operations
- Custom apps handle member experience, real-time features
- JSON-RPC API bridges the two

**Pros:**
- 🎯 **Best of both worlds**
- 💰 **Proven billing** + modern UX
- ⚡ **Fast member-facing features**
- 🔒 **Secure financial operations**

**Cons:**
- 🔌 **Integration complexity** - Two systems to maintain
- 🔄 **Data sync** - Keep systems in sync

---

## Recommendations

### **For Your GMS Project:**

**Phase 1: Validation (2-4 weeks)**
1. Install Odoo locally
2. Enable: account, sale, point_of_sale, crm, portal
3. Configure Costa Rica localization
4. Create prototype member module
5. Test billing workflow for memberships

**Phase 2: Decision (1 week)**
Based on Phase 1 findings:
- If Odoo billing works well → **Hybrid Approach**
- If too complex/rigid → **Option B (Extract & Modernize)**
- If you want fastest path → **Option A (Full Odoo)**

**Phase 3: Architecture**
- Create Architecture document with chosen approach
- Define integration points
- Plan custom modules or external apps

---

## Next Steps

1. **Review this architecture document**
2. **Run Phase 1 validation** (install Odoo, test key modules)
3. **Make architectural decision** based on findings
4. **Proceed to PRD** with chosen architecture in mind
5. **Begin implementation** with clear technical direction

**Critical Questions to Answer:**
- Can Odoo's account module handle all Costa Rica tax requirements?
- Is point_of_sale suitable for your gym retail needs?
- Can you live within Odoo's UI constraints or need custom frontend?
- How important is modern mobile app experience?

---

**Ready for PRD Phase:** Once you've made the architectural decision, the PRD workflow will detail specific features, user flows, and integration requirements for your chosen approach.
