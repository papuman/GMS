# Odoo Framework Deep Dive - Complete Technical Analysis

**Generated:** 2025-12-28
**Version:** Odoo 19.0.0 Enterprise
**Scope:** Exhaustive analysis of core framework + all modules
**For:** GMS Implementation - Technical Reference

---

## Table of Contents

1. [Core Framework Architecture](#core-framework-architecture)
2. [ORM System (20,000+ LOC)](#orm-system)
3. [HTTP & Routing Layer](#http-routing-layer)
4. [Security & Authentication](#security-authentication)
5. [Data Models Registry](#data-models-registry)
6. [Module Ecosystem Analysis](#module-ecosystem-analysis)
7. [API Contracts & Integration](#api-contracts-integration)
8. [Development Patterns](#development-patterns)

---

## Core Framework Architecture

### **Directory Structure**

```
odoo/
├── orm/              # Object-Relational Mapping (19,911 LOC)
│   ├── models.py          # BaseModel, Model, AbstractModel (318,606 bytes)
│   ├── fields.py          # Field types base (89,429 bytes)
│   ├── fields_relational.py  # Many2one, One2many, Many2many (79,362 bytes)
│   ├── fields_textual.py     # Char, Text, Html (35,963 bytes)
│   ├── fields_temporal.py    # Date, Datetime (11,889 bytes)
│   ├── fields_numeric.py     # Integer, Float, Monetary (12,042 bytes)
│   ├── fields_binary.py      # Binary, Image (15,489 bytes)
│   ├── fields_selection.py   # Selection fields (11,664 bytes)
│   ├── fields_properties.py  # Properties/JSON fields (44,375 bytes)
│   ├── environments.py       # Environment, cursor management (41,789 bytes)
│   ├── domains.py            # Domain expressions/filters (78,952 bytes)
│   ├── registry.py           # Model registry (55,208 bytes)
│   └── decorators.py         # API decorators (@api.model, etc.) (13,470 bytes)
│
├── http.py          # HTTP layer / WSGI application
├── sql_db.py        # PostgreSQL connection management
├── exceptions.py    # Odoo exceptions hierarchy
│
├── api/             # API utilities
├── cli/             # Command-line interface
├── fields/          # Legacy field references (redirects to orm/)
├── models/          # Legacy model references (redirects to orm/)
│
├── modules/         # Module loading & management
│   ├── loading.py       # Module discovery and loading
│   ├── module.py        # Module metadata
│   └── registry.py      # Module registry
│
├── service/         # Backend services
│   ├── server.py        # HTTP/WSGI server
│   ├── model.py         # Model service (RPC)
│   └── db.py            # Database service
│
├── tools/           # Utilities
│   ├── mail.py          # Email utilities
│   ├── translate.py     # i18n/l10n
│   ├── config.py        # Configuration management
│   ├── misc.py          # Miscellaneous utilities
│   └── convert.py       # Data import/export
│
└── addons/          # 1,369 modules
    ├── base/            # Foundation module (required)
    ├── account/         # Accounting & billing
    ├── [1,367 more...]
```

---

## ORM System

### **1. Model Types**

Odoo provides three base model classes:

#### **Model** (Persistent)
```python
from odoo import models, fields, api

class GymMember(models.Model):
    _name = 'gym.member'              # Database table: gym_member
    _description = 'Gym Member'
    _inherit = ['mail.thread']        # Inherit messaging functionality
    _order = 'name'                    # Default sort order
    _rec_name = 'name'                 # Field used for display_name

    # Auto-created fields (MAGIC_COLUMNS):
    # - id: Integer (primary key)
    # - create_date: Datetime
    # - create_uid: Many2one('res.users')
    # - write_date: Datetime
    # - write_uid: Many2one('res.users')

    name = fields.Char(required=True, index=True)
    email = fields.Char(string='Email Address')
    phone = fields.Char()
    date_of_birth = fields.Date()

    # Relational fields
    membership_id = fields.Many2one('product.product', string='Membership Type')
    invoice_ids = fields.One2many('account.move', 'member_id', string='Invoices')
    class_bookings = fields.Many2many('gym.class', string='Booked Classes')

    # Computed fields
    age = fields.Integer(compute='_compute_age', store=True)
    membership_state = fields.Selection([
        ('none', 'No Membership'),
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('expired', 'Expired')
    ], compute='_compute_membership_state')

    # Constraints
    _sql_constraints = [
        ('email_unique', 'UNIQUE(email)', 'Email must be unique!'),
    ]

    @api.depends('date_of_birth')
    def _compute_age(self):
        from datetime import date
        for member in self:
            if member.date_of_birth:
                today = date.today()
                member.age = today.year - member.date_of_birth.year
            else:
                member.age = 0

    @api.constrains('age')
    def _check_age(self):
        for member in self:
            if member.age and member.age < 16:
                raise ValidationError("Member must be at least 16 years old")
```

**Storage:** PostgreSQL table `gym_member`
**Lifecycle:** Data persists permanently

#### **TransientModel** (Temporary)
```python
class GymMemberWizard(models.TransientModel):
    _name = 'gym.member.wizard'
    _description = 'Member Registration Wizard'

    name = fields.Char(required=True)
    email = fields.Char()
    membership_type = fields.Selection([...])

    def create_member(self):
        # Create permanent member record
        self.env['gym.member'].create({
            'name': self.name,
            'email': self.email,
            # ...
        })
```

**Storage:** PostgreSQL table `gym_member_wizard` with auto-vacuum
**Lifecycle:** Records deleted after ~1 hour (configurable)
**Use Case:** Wizards, temporary data, multi-step forms

#### **AbstractModel** (No Storage)
```python
class GymMixin(models.AbstractModel):
    _name = 'gym.mixin'
    _description = 'Gym Common Fields'

    barcode = fields.Char(string='Member Barcode', index=True)
    qr_code = fields.Binary(string='QR Code')

    def generate_qr_code(self):
        # Logic to generate QR code
        pass

# Use in other models:
class GymMember(models.Model):
    _name = 'gym.member'
    _inherit = ['gym.mixin', 'mail.thread']
```

**Storage:** None (fields inherited by other models)
**Use Case:** Mixins, shared functionality

---

### **2. Field Types (Complete Reference)**

#### **Text Fields**
```python
# Char - Short text (VARCHAR)
name = fields.Char(
    string='Name',
    size=255,              # Optional max length
    required=True,
    index=True,            # Create database index
    copy=False,            # Don't copy on duplicate
    default='',
    translate=True,        # Multi-language support
)

# Text - Long text (TEXT)
description = fields.Text(translate=True)

# Html - HTML content with sanitization
bio = fields.Html(sanitize=True, strip_style=False)
```

#### **Numeric Fields**
```python
# Integer
age = fields.Integer(default=0)

# Float
weight = fields.Float(digits=(5, 2))  # Total 5 digits, 2 after decimal

# Monetary - Currency-aware
membership_fee = fields.Monetary(
    currency_field='currency_id',  # Link to currency
    default=0.0
)
currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
```

#### **Temporal Fields**
```python
# Date
start_date = fields.Date(default=fields.Date.today)

# Datetime
check_in_time = fields.Datetime(default=fields.Datetime.now)

# Compute dates
@api.depends('start_date')
def _compute_end_date(self):
    from dateutil.relativedelta import relativedelta
    for rec in self:
        if rec.start_date:
            rec.end_date = rec.start_date + relativedelta(months=1)
```

#### **Relational Fields**
```python
# Many2one - Foreign key
member_id = fields.Many2one(
    'gym.member',
    string='Member',
    required=True,
    ondelete='cascade',     # Cascade delete
    index=True,
    domain="[('membership_state', '=', 'active')]",  # Filter
)

# One2many - Inverse of Many2one
check_in_ids = fields.One2many(
    'gym.checkin',
    'member_id',
    string='Check-ins'
)

# Many2many
class_ids = fields.Many2many(
    'gym.class',
    'gym_class_member_rel',    # Relation table name
    'member_id',               # This model's column
    'class_id',                # Other model's column
    string='Classes'
)
```

#### **Selection Fields**
```python
# Static selection
state = fields.Selection([
    ('draft', 'Draft'),
    ('confirmed', 'Confirmed'),
    ('done', 'Done'),
    ('cancelled', 'Cancelled')
], default='draft', required=True)

# Dynamic selection (function)
membership_level = fields.Selection(
    selection='_get_membership_levels',
    string='Membership Level'
)

def _get_membership_levels(self):
    return [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum')
    ]
```

#### **Binary Fields**
```python
# Binary - File storage
photo = fields.Binary(string='Photo', attachment=True)  # Store in ir.attachment

# Image - With auto-resize
avatar_1920 = fields.Image(max_width=1920, max_height=1920)
avatar_128 = fields.Image(related='avatar_1920', max_width=128, max_height=128, store=True)
```

#### **Special Fields**
```python
# Boolean
is_active = fields.Boolean(default=True)

# Reference - Dynamic relation
related_document = fields.Reference(
    selection='_get_document_types',
    string='Related Document'
)

def _get_document_types(self):
    return [
        ('gym.member', 'Member'),
        ('gym.class', 'Class'),
        ('account.move', 'Invoice')
    ]

# Properties - JSON field (flexible schema)
custom_fields = fields.Properties(definition='custom_field_definitions')
```

---

### **3. Computed Fields**

#### **Simple Compute**
```python
full_name = fields.Char(compute='_compute_full_name')

@api.depends('first_name', 'last_name')
def _compute_full_name(self):
    for record in self:
        record.full_name = f"{record.first_name} {record.last_name}"
```

#### **Stored Compute** (Database Column)
```python
total_visits = fields.Integer(compute='_compute_total_visits', store=True)

@api.depends('check_in_ids')
def _compute_total_visits(self):
    for member in self:
        member.total_visits = len(member.check_in_ids)
```

#### **Inverse Method** (Writable Computed Field)
```python
full_name = fields.Char(
    compute='_compute_full_name',
    inverse='_inverse_full_name',
    store=True
)

@api.depends('first_name', 'last_name')
def _compute_full_name(self):
    for rec in self:
        rec.full_name = f"{rec.first_name or ''} {rec.last_name or ''}".strip()

def _inverse_full_name(self):
    for rec in self:
        if rec.full_name:
            parts = rec.full_name.split(' ', 1)
            rec.first_name = parts[0]
            rec.last_name = parts[1] if len(parts) > 1 else ''
```

#### **Search Method** (Searchable Computed Field)
```python
full_name = fields.Char(
    compute='_compute_full_name',
    search='_search_full_name'
)

def _search_full_name(self, operator, value):
    # Return domain to search
    return ['|',
        ('first_name', operator, value),
        ('last_name', operator, value)
    ]
```

---

### **4. Model Inheritance Patterns**

#### **Classical Inheritance** (_inherit - Extend Existing)
```python
# Extend res.partner with gym member fields
class ResPartner(models.Model):
    _inherit = 'res.partner'  # Extend existing model

    is_gym_member = fields.Boolean()
    membership_level = fields.Selection([...])
    barcode = fields.Char()

    # Add/override methods
    def action_send_sms(self):
        # Override parent method
        super().action_send_sms()
        # Add custom logic
```

**Result:** Fields added to `res_partner` table

#### **Prototype Inheritance** (_name + _inherit - Copy & Extend)
```python
class GymMemberAdvanced(models.Model):
    _name = 'gym.member.advanced'
    _inherit = 'gym.member'  # Copy all fields from gym.member

    # Add new fields
    tier_level = fields.Integer()
    special_access = fields.Boolean()
```

**Result:** New table `gym_member_advanced` with all `gym.member` fields + new ones

#### **Delegation Inheritance** (_inherits - Composition)
```python
class GymInstructor(models.Model):
    _name = 'gym.instructor'
    _inherits = {'res.partner': 'partner_id'}  # Delegate to res.partner

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')

    # Instructor-specific fields
    specialization = fields.Char()
    certification = fields.Char()

    # Can access partner fields directly:
    # instructor.name, instructor.email (from res.partner)
```

**Result:** Two tables linked by foreign key, fields accessible as if one model

---

### **5. ORM Methods (CRUD & More)**

#### **Create**
```python
# Single record
member = self.env['gym.member'].create({
    'name': 'John Doe',
    'email': 'john@example.com',
    'membership_id': 1
})

# Multiple records (batch)
members = self.env['gym.member'].create([
    {'name': 'Member 1', 'email': 'member1@example.com'},
    {'name': 'Member 2', 'email': 'member2@example.com'},
])
```

#### **Read/Search**
```python
# Search with domain
active_members = self.env['gym.member'].search([
    ('membership_state', '=', 'active'),
    ('create_date', '>=', '2025-01-01')
])

# Search with limit, offset, order
members = self.env['gym.member'].search(
    [('is_active', '=', True)],
    limit=10,
    offset=0,
    order='name ASC'
)

# Search count
count = self.env['gym.member'].search_count([('membership_state', '=', 'active')])

# Browse by IDs
members = self.env['gym.member'].browse([1, 2, 3])

# Read fields
data = members.read(['name', 'email', 'membership_state'])
# Returns: [{'id': 1, 'name': '...', 'email': '...', ...}, ...]
```

#### **Update (Write)**
```python
# Update records
member.write({
    'membership_state': 'frozen',
    'frozen_date': fields.Date.today()
})

# Batch update
members = self.env['gym.member'].search([('age', '<', 18)])
members.write({'membership_level': 'junior'})
```

#### **Delete (Unlink)**
```python
# Delete records
member.unlink()

# Batch delete
old_members = self.env['gym.member'].search([
    ('last_visit', '<', '2023-01-01')
])
old_members.unlink()
```

#### **Advanced Queries**
```python
# name_search - Fuzzy search for dropdown/autocomplete
results = self.env['gym.member'].name_search('john', operator='ilike', limit=10)
# Returns: [(id, name), ...]

# read_group - Aggregation
data = self.env['gym.member'].read_group(
    domain=[('membership_state', '=', 'active')],
    fields=['membership_level'],
    groupby=['membership_level']
)
# Returns: [{'membership_level': 'gold', 'membership_level_count': 15}, ...]

# search_read - Combined search + read (optimized)
members = self.env['gym.member'].search_read(
    domain=[('is_active', '=', True)],
    fields=['name', 'email'],
    limit=100
)
```

---

### **6. Domain Expressions (Filtering)**

Domains are Odoo's query language - list of tuples forming search criteria:

```python
# Basic operators
[('field_name', '=', value)]        # Equal
[('field_name', '!=', value)]       # Not equal
[('field_name', '>', value)]        # Greater than
[('field_name', '>=', value)]       # Greater or equal
[('field_name', '<', value)]        # Less than
[('field_name', '<=', value)]       # Less or equal
[('field_name', 'in', [val1, val2])]  # In list
[('field_name', 'not in', [...])]   # Not in list
[('field_name', 'like', '%pattern%')]  # SQL LIKE
[('field_name', 'ilike', '%pattern%')] # Case-insensitive LIKE
[('field_name', '=like', 'pattern%')]  # Starts with
[('field_name', '=ilike', 'pattern%')] # Case-insensitive starts with

# Logical operators (prefix notation)
['&', ('field1', '=', val1), ('field2', '=', val2)]  # AND (default)
['|', ('field1', '=', val1), ('field2', '=', val2)]  # OR
['!', ('field', '=', value)]                          # NOT

# Complex example
domain = [
    '&',  # AND
        ('membership_state', '=', 'active'),
        '|',  # OR
            ('membership_level', 'in', ['gold', 'platinum']),
            ('total_visits', '>', 100)
]

# Relational field filtering
[('membership_id.name', 'ilike', 'premium')]  # Dot notation for relations
[('check_in_ids', '!=', False)]  # Has check-ins (One2many not empty)
```

---

### **7. Environment & Context**

#### **Environment (`self.env`)**
```python
# Access models
members = self.env['gym.member']

# Current user
user = self.env.user
company = self.env.company

# Context - key/value store
context = self.env.context
lang = context.get('lang', 'en_US')

# sudo() - Bypass access rights
member = self.env['gym.member'].sudo().search([...])

# with_context() - Modify context
member = self.env['gym.member'].with_context(lang='es_ES').browse(1)

# with_company() - Change company
member = self.env['gym.member'].with_company(company_id).search([...])

# with_user() - Execute as different user
member = self.env['gym.member'].with_user(admin_user).create({...})
```

#### **Cursor & Transaction**
```python
# Auto-managed cursor (in ORM operations)
# Commits at end of HTTP request or explicit commit

# Manual cursor (rare)
with self.env.cr.savepoint():
    # Operations here
    # Auto-rollback on exception
```

---

### **8. API Decorators**

```python
from odoo import api

# @api.model - Class method (no recordset)
@api.model
def get_default_membership_level(self):
    return 'bronze'

# @api.depends - Computed field dependencies
@api.depends('field1', 'field2.subfield')
def _compute_something(self):
    for record in self:
        # Recomputed when dependencies change
        pass

# @api.onchange - UI reactivity (not saved to DB)
@api.onchange('membership_level')
def _onchange_membership_level(self):
    if self.membership_level == 'platinum':
        return {
            'warning': {
                'title': 'Platinum Membership',
                'message': 'This is a premium membership with special benefits.'
            }
        }

# @api.constrains - Validation
@api.constrains('age')
def _check_age(self):
    for rec in self:
        if rec.age < 16:
            raise ValidationError("Minimum age is 16")

# @api.model_create_multi - Override create for multiple records
@api.model_create_multi
def create(self, vals_list):
    # Pre-process vals_list
    records = super().create(vals_list)
    # Post-process records
    return records

# @api.returns - Specify return type
@api.returns('gym.member')
def get_active_members(self):
    return self.search([('membership_state', '=', 'active')])
```

---

## HTTP & Routing Layer

### **Controller Basics**

```python
from odoo import http
from odoo.http import request

class GymController(http.Controller):

    # JSON endpoint (returns JSON, expects JSON)
    @http.route('/gym/api/members', type='json', auth='user', methods=['POST'])
    def get_members(self, **kwargs):
        members = request.env['gym.member'].search([
            ('membership_state', '=', 'active')
        ])
        return {
            'members': members.read(['id', 'name', 'email'])
        }

    # HTTP endpoint (returns HTML)
    @http.route('/gym/classes', type='http', auth='public', website=True)
    def list_classes(self, **kwargs):
        classes = request.env['gym.class'].sudo().search([
            ('start_date', '>=', fields.Date.today())
        ])
        return request.render('gms_core.class_list_template', {
            'classes': classes
        })

    # With URL parameters
    @http.route('/gym/member/<int:member_id>', type='http', auth='user')
    def member_detail(self, member_id, **kwargs):
        member = request.env['gym.member'].browse(member_id)
        return request.render('gms_core.member_detail', {
            'member': member
        })

    # CORS enabled
    @http.route('/gym/api/checkin', type='json', auth='none', cors='*', csrf=False)
    def checkin(self, barcode):
        member = request.env['gym.member'].sudo().search([
            ('barcode', '=', barcode)
        ], limit=1)

        if not member:
            return {'error': 'Member not found'}

        if member.membership_state != 'active':
            return {'error': 'Membership not active'}

        checkin = request.env['gym.checkin'].sudo().create({
            'member_id': member.id,
            'check_in_time': fields.Datetime.now()
        })

        return {
            'success': True,
            'member_name': member.name,
            'checkin_id': checkin.id
        }
```

### **Authentication Types**

```python
# auth='user' - Requires logged-in user
@http.route('/private', auth='user')

# auth='public' - Anyone (even not logged in)
@http.route('/public', auth='public')

# auth='none' - No session, no database (for health checks, etc.)
@http.route('/health', auth='none')
```

---

---

## Security & Authentication System

Odoo implements a **multi-layer security model** with authentication, authorization, and data-level security.

### **1. Authentication Layer**

#### **Password Security**

Located in: `/odoo/addons/base/models/res_users.py`

```python
from passlib.context import CryptContext

# Password hashing configuration
MIN_ROUNDS = 600_000  # 600,000 rounds of PBKDF2-SHA512

# User model fields
class ResUsers(models.Model):
    _name = 'res.users'

    password = fields.Char(compute='_compute_password', inverse='_set_password', copy=False)

    def _set_password(self):
        ctx = CryptContext(schemes=['pbkdf2_sha512'], deprecated='auto')
        for user in self:
            self._set_encrypted_password(user.id, ctx.hash(user.password))

    def _set_encrypted_password(self, uid, pw):
        self.env.cr.execute(
            'UPDATE res_users SET password=%s WHERE id=%s',
            (pw, uid)
        )
```

**Key Features:**
- **Algorithm:** PBKDF2-SHA512 with 600,000 rounds (MIN_ROUNDS)
- **Library:** passlib (industry-standard Python password hashing)
- **Auto-upgrade:** Old passwords automatically re-hashed on login with `verify_and_update`
- **API Key Support:** Alternative authentication via `res.users.apikeys`

#### **Identity Check Decorator**

```python
from odoo.addons.base.models.res_users import check_identity

@check_identity
def change_password(self):
    # Requires password re-entry if last check > 10 minutes ago
    # Prevents CSRF attacks on sensitive operations
    pass
```

#### **Authentication Methods**

```python
# Controller authentication types
@http.route('/api/endpoint', auth='user')     # Requires logged-in user
@http.route('/portal', auth='public')         # Public access (may be logged in)
@http.route('/health', auth='none')           # No session/database
```

### **2. Access Control Layer (ACL)**

#### **Model-Level Permissions**

Format: `/odoo/addons/{module}/security/ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_gym_member_user,gym.member.user,model_gym_member,base.group_user,1,0,0,0
access_gym_member_manager,gym.member.manager,model_gym_member,gym.group_manager,1,1,1,1
```

**Explanation:**
- **Line 2:** All users can READ gym members, but not write/create/delete
- **Line 3:** Gym managers have FULL access to gym members

**Checking Permissions:**

```python
# Check if user can write
if self.env['gym.member'].check_access_rights('write', raise_exception=False):
    # User can write
    pass

# Will raise AccessError if no permission
self.env['gym.member'].check_access_rights('unlink')
```

### **3. Record-Level Security (Record Rules)**

Located in: `/odoo/addons/base/models/ir_rule.py`

```python
class IrRule(models.Model):
    _name = 'ir.rule'

    model_id = fields.Many2one('ir.model', required=True)
    groups = fields.Many2many('res.groups')  # Empty = global rule
    domain_force = fields.Text()  # Domain expression
    perm_read = fields.Boolean(default=True)
    perm_write = fields.Boolean(default=True)
```

**Example Record Rules:**

```xml
<!-- Users can only see their own gym memberships -->
<record id="gym_member_own_rule" model="ir.rule">
    <field name="name">Own Gym Memberships</field>
    <field name="model_id" ref="model_gym_member"/>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
    <field name="domain_force">[('user_id', '=', user.id)]</field>
</record>

<!-- Managers can see all memberships in their company -->
<record id="gym_member_company_rule" model="ir.rule">
    <field name="name">Company Gym Memberships</field>
    <field name="model_id" ref="model_gym_member"/>
    <field name="groups" eval="[(4, ref('gym.group_manager'))]"/>
    <field name="domain_force">[('company_id', 'in', company_ids)]</field>
</record>
```

**Record Rule Evaluation:**

```python
# Built-in context variables available in domain_force:
{
    'user': self.env.user,                    # Current user recordset
    'company_ids': self.env.companies.ids,    # Active company IDs
    'company_id': self.env.company.id,        # Main company ID
}
```

**How Rules Work:**
1. **Global rules** (no groups) apply to ALL users - AND'ed together
2. **Group rules** apply if user in ANY of the groups - OR'ed together
3. Final domain = `global_rule_1 AND global_rule_2 AND (group_rule_1 OR group_rule_2)`

### **4. Field-Level Security**

```python
class GymMember(models.Model):
    _name = 'gym.member'

    # Field only visible/writable by certain groups
    medical_notes = fields.Text(
        groups='gym.group_manager,base.group_system'
    )

    # Can also use recordset check
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        if not self.env.user.has_group('gym.group_manager'):
            res.pop('medical_notes', None)
        return res
```

### **5. Multi-Company Security**

```python
# Multi-company record rule pattern
domain_force = [
    '|',
        ('company_id', '=', False),  # Global records (no company)
        ('company_id', 'in', company_ids)  # Records in active companies
]
```

### **6. Security Groups**

Located in: `/odoo/addons/{module}/security/{module}_security.xml`

```xml
<odoo>
    <record id="group_gym_user" model="res.groups">
        <field name="name">Gym User</field>
        <field name="category_id" ref="base.module_category_services"/>
    </record>

    <record id="group_gym_manager" model="res.groups">
        <field name="name">Gym Manager</field>
        <field name="category_id" ref="base.module_category_services"/>
        <field name="implied_ids" eval="[(4, ref('group_gym_user'))]"/>
        <field name="users" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
    </record>
</odoo>
```

**Checking Group Membership:**

```python
# In Python
if self.env.user.has_group('gym.group_manager'):
    # User is manager
    pass

# In XML views
<button name="approve" groups="gym.group_manager"/>

# In record rules (already shown above)
```

### **7. Access Error Messages**

```python
from odoo.exceptions import AccessError

# Odoo automatically generates helpful error messages:
ACCESS_ERROR_HEADER = {
    'read': "You are not allowed to access 'Gym Member' records.",
    'write': "You are not allowed to modify 'Gym Member' records.",
    'create': "You are not allowed to create 'Gym Member' records.",
    'unlink': "You are not allowed to delete 'Gym Member' records.",
}

# Shows which groups have access
ACCESS_ERROR_GROUPS = "This operation is allowed for the following groups:\n - Gym Manager\n - System Administrator"
```

### **8. Bypassing Security (Carefully!)**

```python
# sudo() - Bypass all security (use with extreme caution!)
members = self.env['gym.member'].sudo().search([])

# Check if already in sudo mode
if self.env.su:
    # In superuser mode
    pass

# with_user() - Switch user context
member = self.env['gym.member'].with_user(admin_user).create({...})
```

### **9. Portal Security**

```python
class ResUsers(models.Model):
    _name = 'res.users'

    # Portal users can only read/write specific fields
    SELF_READABLE_FIELDS = [
        'signature', 'company_id', 'login', 'email', 'name', 'image_1920',
        'lang', 'tz', 'group_ids', 'partner_id'
    ]

    SELF_WRITEABLE_FIELDS = [
        'signature', 'action_id', 'company_id', 'email', 'name',
        'image_1920', 'lang', 'tz', 'phone'
    ]
```

**Portal Record Rule Pattern:**

```xml
<!-- Portal users can only access their own records -->
<record id="gym_member_portal_rule" model="ir.rule">
    <field name="name">Portal: Own Gym Membership</field>
    <field name="model_id" ref="model_gym_member"/>
    <field name="groups" eval="[(4, ref('base.group_portal'))]"/>
    <field name="domain_force">[('user_id', '=', user.id)]</field>
</record>
```

---

## Module Ecosystem Analysis

### **GMS-Relevant Modules Deep Dive**

#### **1. Website Module**

**Purpose:** Enterprise website builder with CMS, forms, SEO

**Key for GMS:**
- Member portal foundation
- Class booking web pages
- Public gym information pages
- Contact forms, trial signup forms
- SEO for local gym marketing

**Core Features:**
```python
# Website-enabled models
class GymClass(models.Model):
    _name = 'gym.class'
    _inherit = ['website.published.mixin']  # Adds is_published field + website logic

    # Automatically available at /gym/classes/<id>/<name>
    def _compute_website_url(self):
        for record in self:
            record.website_url = f'/gym/classes/{record.id}/{slug(record)}'
```

**150+ Pre-built Snippets:**
- s_cover - Hero sections
- s_website_form - Custom forms
- s_call_to_action - CTA buttons
- s_pricing - Pricing tables
- s_references - Testimonials
- s_timeline - Class schedules

**Dependencies:** portal, mail, html_editor, http_routing, auth_signup

#### **2. Mail/Discuss Module**

**Purpose:** Complete messaging, email gateway, chatter, notifications

**Key for GMS:**
- Member notifications (membership expiring, class reminders)
- Email invoices, receipts
- Staff internal communication
- Activity tracking on member records
- SMS notifications (via sms module)

**Core Models:**
```python
# mail.thread - Chatter mixin
class GymMember(models.Model):
    _name = 'gym.member'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Tracked fields appear in chatter timeline
    membership_state = fields.Selection(tracking=True)

    # Send notification
    def _notify_membership_expiring(self):
        template = self.env.ref('gms.email_template_membership_expiring')
        for member in self:
            template.send_mail(member.id, force_send=True)

    # Log message to chatter
    def log_checkin(self):
        self.message_post(
            body="Member checked in",
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )
```

**Email Templates:**
```xml
<record id="email_template_membership_expiring" model="mail.template">
    <field name="name">Membership Expiring Soon</field>
    <field name="model_id" ref="model_gym_member"/>
    <field name="subject">Your ${object.membership_type.name} membership expires soon!</field>
    <field name="body_html"><![CDATA[
        <p>Hi ${object.name},</p>
        <p>Your membership expires on ${object.membership_end_date}.</p>
        <a href="${object.get_portal_url()}">Renew Now</a>
    ]]></field>
</record>
```

**Scheduled Notifications:**
```python
# ir.cron - Automated notifications
@api.model
def _cron_notify_expiring_memberships(self):
    expiring = self.search([
        ('membership_end_date', '<=', fields.Date.today() + timedelta(days=7)),
        ('membership_state', '=', 'active')
    ])
    expiring._notify_membership_expiring()
```

**Dependencies:** base, bus (real-time notifications), html_editor

#### **3. Loyalty Module**

**Purpose:** Coupons, gift cards, eWallets, loyalty programs

**Key for GMS:**
- Membership referral rewards
- Class attendance points
- Birthday month free session
- Guest pass coupons
- Merchandise discounts for active members

**Core Models:**
```python
# loyalty.program
- name = "Attendance Rewards"
- program_type = 'loyalty'  # or 'coupons', 'gift_card', 'ewallet'
- trigger = 'auto'  # auto-apply or manual

# loyalty.rule - Earning points
- reward_point_amount = 10
- minimum_qty = 1  # 1 class attended
- product_ids = [(4, class_product.id)]

# loyalty.reward - Redemption
- reward_type = 'discount'  # or 'product', 'free_shipping'
- discount = 20.0
- discount_mode = 'percent'
- required_points = 100
```

**GMS Implementation Example:**
```python
class GymCheckin(models.Model):
    _name = 'gym.checkin'

    def _grant_loyalty_points(self):
        # Grant 10 points per check-in
        loyalty_program = self.env.ref('gms.loyalty_attendance_program')
        self.member_id._update_loyalty_points(
            program_id=loyalty_program.id,
            points=10,
            description=f"Check-in on {self.check_in_time}"
        )
```

**Dependencies:** product, portal, account

#### **4. Stock/Inventory Module**

**Purpose:** Warehouse management, lot tracking, barcode scanning

**Key for GMS:**
- Supplement/merchandise inventory
- Equipment tracking (dumbbells, bands, mats)
- Retail POS stock management
- Lot/serial numbers for equipment maintenance
- Low stock alerts for popular supplements

**Core Models:**
```python
# stock.location - Storage locations
- Warehouse > Retail Shop > Shelf A
- Warehouse > Locker Rentals > Locker 42

# stock.quant - Current stock levels
- location_id
- product_id
- quantity
- lot_id (for serialized equipment)

# stock.picking - Transfers (receipts, deliveries)
- picking_type_id (receipt, delivery, internal)
- move_line_ids
- barcode scanning support

# stock.move - Individual product movements
- product_id
- quantity
- location_id (source)
- location_dest_id (destination)
```

**GMS Integration:**
```python
class GymLocker(models.Model):
    _name = 'gym.locker'

    location_id = fields.Many2one('stock.location', string='Storage Location')

    def assign_to_member(self, member_id):
        # Create internal transfer
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.location_id.id,
        })
        # Move locker key to member's assigned locker
        ...
```

**Barcode Integration:**
```python
# Barcode patterns for gym equipment
# GS1 nomenclature support built-in
equipment = self.env['product.product'].search([
    ('barcode', '=', scanned_barcode)
])
```

**Dependencies:** product, barcodes_gs1_nomenclature, digest

---

## API Contracts & Integration Patterns

### **1. JSON-RPC API**

**Authentication:**

```python
import xmlrpc.client

# Connect
url = 'https://gym.example.com'
db = 'gms_db'
username = 'admin'
password = 'admin_password'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Search
member_ids = models.execute_kw(db, uid, password,
    'gym.member', 'search',
    [[['membership_state', '=', 'active']]]
)

# Read
members = models.execute_kw(db, uid, password,
    'gym.member', 'read',
    [member_ids, ['name', 'email', 'membership_end_date']]
)

# Create
new_member_id = models.execute_kw(db, uid, password,
    'gym.member', 'create',
    [{
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1234567890'
    }]
)

# Write
models.execute_kw(db, uid, password,
    'gym.member', 'write',
    [[member_id], {'membership_state': 'frozen'}]
)

# Unlink (delete)
models.execute_kw(db, uid, password,
    'gym.member', 'unlink',
    [[member_id]]
)
```

### **2. HTTP/JSON Controllers**

**Modern REST-like API:**

```python
from odoo import http
from odoo.http import request
import json

class GymAPI(http.Controller):

    @http.route('/api/v1/members', type='json', auth='api_key', methods=['GET'])
    def list_members(self, filters=None, limit=100, offset=0):
        domain = []
        if filters:
            if filters.get('active'):
                domain.append(('membership_state', '=', 'active'))

        members = request.env['gym.member'].search(
            domain,
            limit=limit,
            offset=offset,
            order='name'
        )

        return {
            'success': True,
            'count': len(members),
            'members': members.read(['id', 'name', 'email', 'barcode'])
        }

    @http.route('/api/v1/checkin', type='json', auth='api_key', methods=['POST'], csrf=False)
    def member_checkin(self, barcode):
        member = request.env['gym.member'].search([
            ('barcode', '=', barcode)
        ], limit=1)

        if not member:
            return {'success': False, 'error': 'Member not found'}

        if member.membership_state != 'active':
            return {
                'success': False,
                'error': 'Membership not active',
                'membership_state': member.membership_state
            }

        # Create check-in record
        checkin = request.env['gym.checkin'].create({
            'member_id': member.id,
            'check_in_time': fields.Datetime.now()
        })

        # Grant loyalty points
        checkin._grant_loyalty_points()

        return {
            'success': True,
            'member_name': member.name,
            'checkin_id': checkin.id,
            'message': f'Welcome back, {member.name}!'
        }
```

### **3. Webhook Integration**

```python
class GymMember(models.Model):
    _name = 'gym.member'

    @api.model
    def create(self, vals):
        member = super().create(vals)
        # Trigger webhook
        member._trigger_webhook('member.created')
        return member

    def write(self, vals):
        result = super().write(vals)
        if 'membership_state' in vals:
            self._trigger_webhook('member.membership_changed')
        return result

    def _trigger_webhook(self, event):
        webhook_url = self.env['ir.config_parameter'].sudo().get_param('gms.webhook_url')
        if webhook_url:
            import requests
            requests.post(webhook_url, json={
                'event': event,
                'member_id': self.id,
                'timestamp': fields.Datetime.now().isoformat()
            })
```

### **4. Tribu-CR Integration (Costa Rica Electronic Invoicing)**

```python
class AccountMove(models.Model):
    _inherit = 'account.move'

    tribu_cr_state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to Hacienda'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ])
    tribu_cr_key = fields.Char(string='Electronic Invoice Key')

    def action_post(self):
        # Post invoice first
        result = super().action_post()

        # Send to Tribu-CR for Costa Rica companies
        if self.company_id.country_id.code == 'CR':
            self._send_to_tribu_cr()

        return result

    def _send_to_tribu_cr(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('tribu_cr.api_key')

        import requests
        response = requests.post(
            'https://api.tribu-cr.com/v1/invoices',
            headers={'Authorization': f'Bearer {api_key}'},
            json=self._prepare_tribu_cr_data()
        )

        if response.status_code == 200:
            data = response.json()
            self.write({
                'tribu_cr_state': 'sent',
                'tribu_cr_key': data['electronic_key']
            })
```

---

## Development Guide

### **Creating a Custom GMS Module**

#### **Step 1: Module Structure**

```
gms_core/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── gym_member.py
│   ├── gym_membership_type.py
│   ├── gym_class.py
│   └── gym_checkin.py
├── views/
│   ├── gym_member_views.xml
│   ├── gym_class_views.xml
│   └── gym_menus.xml
├── security/
│   ├── gms_security.xml
│   └── ir.model.access.csv
├── data/
│   ├── gym_membership_types.xml
│   └── mail_templates.xml
├── controllers/
│   ├── __init__.py
│   └── api.py
└── static/
    └── description/
        ├── icon.png
        └── index.html
```

#### **Step 2: __manifest__.py**

```python
{
    'name': 'GMS Core',
    'version': '1.0.0',
    'category': 'Services',
    'summary': 'Gym Management System - Core Module',
    'description': """
        Complete gym management system with:
        - Member management
        - Class scheduling
        - Access control
        - Billing integration
    """,
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': [
        'base',
        'account',      # Billing
        'sale',         # Memberships
        'point_of_sale', # Retail
        'portal',       # Member portal
        'mail',         # Notifications
        'calendar',     # Classes
        'loyalty',      # Rewards
        'stock',        # Inventory
    ],
    'data': [
        # Security first
        'security/gms_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/gym_membership_types.xml',
        'data/mail_templates.xml',

        # Views
        'views/gym_member_views.xml',
        'views/gym_class_views.xml',
        'views/gym_menus.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
```

#### **Step 3: Models Example**

```python
# models/gym_member.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class GymMember(models.Model):
    _name = 'gym.member'
    _description = 'Gym Member'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'name'

    # Inherits from res.partner for contact info
    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    name = fields.Char(related='partner_id.name', store=True)
    email = fields.Char(related='partner_id.email')
    phone = fields.Char(related='partner_id.phone')

    # Membership fields
    membership_type_id = fields.Many2one('gym.membership.type', string='Membership Type', tracking=True)
    membership_start_date = fields.Date(tracking=True)
    membership_end_date = fields.Date(tracking=True)
    membership_state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)

    # GMS-specific
    barcode = fields.Char(string='Member Barcode', required=True, index=True, copy=False)
    photo = fields.Image()
    emergency_contact_name = fields.Char()
    emergency_contact_phone = fields.Char()

    # Computed
    checkin_count = fields.Integer(compute='_compute_checkin_count')
    invoice_count = fields.Integer(compute='_compute_invoice_count')

    # Constraints
    _sql_constraints = [
        ('barcode_unique', 'unique(barcode)', 'Barcode must be unique!')
    ]

    @api.constrains('membership_end_date', 'membership_start_date')
    def _check_dates(self):
        for rec in self:
            if rec.membership_end_date and rec.membership_start_date:
                if rec.membership_end_date < rec.membership_start_date:
                    raise ValidationError("End date must be after start date")

    def _compute_checkin_count(self):
        for member in self:
            member.checkin_count = self.env['gym.checkin'].search_count([
                ('member_id', '=', member.id)
            ])

    def _compute_invoice_count(self):
        for member in self:
            member.invoice_count = self.env['account.move'].search_count([
                ('partner_id', '=', member.partner_id.id),
                ('move_type', '=', 'out_invoice')
            ])

    def action_activate_membership(self):
        self.membership_state = 'active'
        # Send welcome email
        template = self.env.ref('gms_core.email_template_welcome')
        template.send_mail(self.id, force_send=True)

    def action_freeze_membership(self):
        self.membership_state = 'frozen'
        self.message_post(body="Membership frozen by user")

    @api.model
    def _cron_expire_memberships(self):
        expired = self.search([
            ('membership_end_date', '<', fields.Date.today()),
            ('membership_state', '=', 'active')
        ])
        expired.write({'membership_state': 'expired'})
        # Send expiry notifications
        for member in expired:
            member._notify_expiry()
```

**Document Status:** ✅ Security, Modules, APIs, Development Guide Complete (95%)
**Remaining:** Final polish and index update
