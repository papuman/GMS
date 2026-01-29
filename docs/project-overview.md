# Odoo ERP Framework - Project Overview

**Generated:** 2025-12-28
**Version:** Odoo 19.0.0 Enterprise Edition
**Repository Type:** Monolithic Backend Framework

---

## Executive Summary

This is the complete **Odoo ERP/CRM framework** - a comprehensive open-source business management platform. The codebase contains:

- **15,382 Python files** across the framework and modules
- **1,369 addon modules** providing business functionality
- **Enterprise-grade ERP features**: Accounting, CRM, HR, Inventory, Manufacturing, E-commerce, POS, and more
- **Modular architecture** allowing customization and extension

**Primary Purpose:** Foundation for building the **GMS (Gym Management System)** - either by:
1. Building custom modules on top of Odoo's framework
2. Extracting and modernizing relevant components
3. Using Odoo modules as reference architecture

---

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Python | 3.10 - 3.13 | Core language |
| **Framework** | Odoo | 19.0.0 | Custom ERP framework with ORM, routing, module system |
| **Database** | PostgreSQL | 13+ (min) | Primary data store |
| **ORM** | Odoo ORM | Custom | Active Record pattern, model inheritance |
| **Web Server** | Werkzeug | 2.0.2 - 3.0.1 | WSGI web server |
| **Async/Concurrency** | Gevent + Greenlet | Latest | Async I/O, concurrent requests |
| **Template Engine** | Jinja2 | 3.0.3 - 3.1.2 | Server-side templates, QWeb |
| **XML Processing** | lxml | 4.8.0 - 5.2.1 | XML/HTML parsing, report generation |
| **PDF Generation** | ReportLab | 3.6.8 - 4.1.0 | Business reports, invoices |
| **Excel Support** | openpyxl, xlrd, xlsxwriter, xlwt | Various | Spreadsheet import/export |
| **Localization** | Babel | 2.9.1 - 2.17.0 | i18n/l10n |
| **Image Processing** | Pillow | 9.0.1 - 11.1.0 | Image manipulation |
| **Security** | cryptography, pyopenssl, passlib | Latest | Encryption, SSL, password hashing |
| **HTTP Client** | requests, urllib3 | 2.25.1 - 2.31.0 | External API calls |
| **Payment/Banking** | zeep (SOAP), ofxparse | Latest | Payment integrations |
| **Barcode/QR** | pyusb, qrcode | Latest | Hardware integration |
| **Testing** | freezegun | 1.1.0 - 1.5.1 | Time-based testing |

---

## Architecture Overview

### **Pattern:** Modular Monolith with Plugin Architecture

Odoo uses a sophisticated **module/addon system** where:
- **Core framework** (`/odoo`) provides ORM, API, authentication, routing
- **Addons** (`/odoo/addons`) are self-contained modules with models, views, controllers
- **Modules can depend on and extend other modules**
- **Models use multiple inheritance** (mixin pattern)

### **Key Architectural Components:**

1. **ORM Layer** (`odoo/models`, `odoo/fields`)
   - Active Record pattern
   - Model inheritance (classical, prototype, delegation)
   - Automated schema migrations
   - Computed fields, constraints, triggers

2. **API Layer** (`odoo/http.py`, `odoo/api.py`)
   - XML-RPC API (legacy)
   - JSON-RPC API (modern)
   - REST-like controllers
   - Authentication via sessions/tokens

3. **Module System** (`odoo/modules`)
   - Declarative manifest (`__manifest__.py`)
   - Dependency resolution
   - Auto-discovery and loading
   - Install/upgrade/uninstall lifecycle

4. **View Layer** (QWeb templates)
   - XML-based view definitions
   - Template inheritance and extension
   - Client-side rendering (Owl framework - JavaScript)

5. **Security** (`odoo/addons/base/security`)
   - Multi-company support
   - Record rules (row-level security)
   - Access control lists (ACLs)
   - Field-level permissions

6. **Database Abstraction** (`odoo/sql_db.py`)
   - PostgreSQL-specific optimizations
   - Connection pooling
   - Cursor management
   - Transaction handling

---

## Repository Structure

```
GMS/
├── odoo/                       # Core Odoo framework
│   ├── __main__.py            # Entry point (CLI)
│   ├── http.py                # HTTP routing, controllers
│   ├── models/                # ORM base classes
│   ├── fields/                # Field types (Char, Integer, Many2one, etc.)
│   ├── api/                   # API decorators and utilities
│   ├── modules/               # Module loading and management
│   ├── service/               # Server services (RPC, cron, etc.)
│   ├── tools/                 # Utilities (mail, config, translate, etc.)
│   ├── cli/                   # Command-line interface
│   ├── tests/                 # Core framework tests
│   └── addons/                # 1,369 business modules
│       ├── base/              # Foundation module (required)
│       ├── account/           # Accounting (invoicing, payments, taxes)
│       ├── crm/               # Customer Relationship Management
│       ├── hr/                # Human Resources
│       ├── sale/              # Sales Management
│       ├── purchase/          # Purchase Management
│       ├── stock/             # Inventory/Warehouse Management
│       ├── point_of_sale/     # POS system
│       ├── website/           # Website builder
│       ├── project/           # Project management
│       ├── membership/        # Membership management (⭐ relevant for gym)
│       └── [1,365 more modules...]
├── setup.py                   # Python package setup
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

---

## Modules Potentially Relevant to GMS

Based on your 400+ gym management features, these Odoo modules may be relevant:

| Module | Purpose | Relevance to GMS |
|--------|---------|------------------|
| `membership` | Membership management, tiers, renewals | Core for gym memberships |
| `account` | Invoicing, payments, taxes | Billing, Costa Rica compliance |
| `account_payment` | Payment processing | Member payments |
| `sale` | Sales orders, quotas | Membership sales, retail |
| `point_of_sale` | POS system | Gym retail, supplements |
| `crm` | Lead management, opportunities | Lead/prospect tracking |
| `hr` | Employee management | Staff management |
| `hr_attendance` | Attendance tracking | Staff check-in (adaptable for members) |
| `calendar` | Event/appointment scheduling | Class scheduling |
| `mail` | Email, messaging, notifications | Member communications |
| `sms` | SMS gateway integration | SMS reminders |
| `website` | Website builder | Member portal |
| `portal` | Customer self-service | Member dashboard |
| `loyalty` | Loyalty programs, rewards | Gamification, points |
| `stock` | Inventory management | Retail inventory |
| `payment_*` | Payment provider integrations | Costa Rica payment gateways |

---

## Development Approach

### **Environment:**
- **OS Support:** Linux (Ubuntu 24.04, Debian 12), Windows, macOS
- **Python:** 3.10 minimum, 3.13 maximum
- **PostgreSQL:** 13+ required

### **Installation:**
```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
createdb gym_management

# Run Odoo server
python odoo-bin -d gym_management -i base
```

### **Custom Module Development:**
```bash
# Create custom GMS module
python odoo-bin scaffold gms_core /path/to/custom/addons

# Structure:
# gms_core/
# ├── __manifest__.py        # Module metadata
# ├── models/                # Data models (members, classes, etc.)
# ├── views/                 # UI definitions
# ├── controllers/           # HTTP endpoints
# ├── security/              # ACLs, record rules
# └── data/                  # Demo/initial data
```

---

## Integration Points

Odoo provides extensive integration capabilities:

1. **XML-RPC API** - Legacy but stable
2. **JSON-RPC API** - Modern, recommended
3. **REST API** (via custom controllers)
4. **Webhook support** (via custom modules)
5. **External database connections** (via connectors)

---

## Testing

Odoo includes comprehensive test infrastructure:
- Unit tests in `/tests` directories
- Integration tests via HTTP test client
- Test database isolation
- Selenium/browser tests for UI

---

## Key Decision Points for GMS

Based on this Odoo codebase analysis, you face critical architectural decisions:

### **Option 1: Build on Odoo (Full Framework)**
- ✅ Mature billing, invoicing, tax compliance
- ✅ Authentication, permissions, multi-user
- ✅ 1,369 modules to learn from or extend
- ❌ Heavy framework (15K+ files)
- ❌ Locked to Odoo's architecture patterns
- ❌ Learning curve for Odoo ORM/module system

### **Option 2: Extract & Modernize Specific Components**
- ✅ Take proven business logic (billing, memberships)
- ✅ Modernize to current Python practices
- ✅ Lighter, more maintainable
- ❌ Significant refactoring effort
- ❌ May lose Odoo's integration benefits

### **Option 3: Reference Architecture Only**
- ✅ Learn patterns and approaches
- ✅ Build modern GMS from scratch
- ✅ Full control, modern stack
- ❌ Rebuild all functionality
- ❌ Longer development time

**Recommendation:** Proceed to Architecture documentation and PRD phases to make informed decision based on:
1. Detailed analysis of which Odoo modules overlap with GMS features
2. Assessment of Costa Rica tax compliance (account module capabilities)
3. Evaluation of Odoo's POS vs GMS retail requirements
4. Decision on membership management (extend Odoo's vs custom)

---

**Next Steps:**
1. Review this overview
2. Identify specific Odoo modules to deep-dive
3. Create Architecture document with technical decision framework
4. Proceed to PRD phase with informed architectural direction
