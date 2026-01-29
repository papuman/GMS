#!/usr/bin/env python3
"""
Populate GMS Validation Database with Realistic Gym Data
=========================================================
Creates sample data across all Odoo modules for gym management testing.

Usage:
    docker cp populate_gym_data.py gms_odoo:/tmp/
    docker exec gms_odoo python3 /tmp/populate_gym_data.py
"""

import odoorpc
import random
from datetime import datetime, timedelta

# Connection settings
ODOO_HOST = 'localhost'
ODOO_PORT = 8069  # Internal port
ODOO_DB = 'gms_validation'
ODOO_USER = 'admin'
ODOO_PASSWORD = 'admin'

print("=" * 70)
print("GMS VALIDATION - Sample Data Generator")
print("=" * 70)
print()

# Connect via XML-RPC (from inside container)
print("[1/12] Connecting to Odoo...")
odoo = odoorpc.ODOO('db', port=8069)
odoo.login(ODOO_DB, ODOO_USER, ODOO_PASSWORD)
print(f"✓ Connected to database: {ODOO_DB}")
print()

# Get main company
Partner = odoo.env['res.partner']
Product = odoo.env['product.product']
Category = odoo.env['product.category']
SaleOrder = odoo.env['sale.order']
AccountMove = odoo.env['account.move']
CRMLead = odoo.env['crm.lead']
HREmployee = odoo.env['hr.employee']
CalendarEvent = odoo.env['calendar.event']
User = odoo.env['res.users']

company_id = odoo.env.user.company_id.id

# ============================================================================
# STEP 2: CREATE PRODUCT CATEGORIES
# ============================================================================
print("[2/12] Creating product categories...")

categories = {
    'memberships': Category.create({
        'name': 'Gym Memberships',
        'parent_id': False,
    }),
    'classes': Category.create({
        'name': 'Fitness Classes',
        'parent_id': False,
    }),
    'supplements': Category.create({
        'name': 'Supplements',
        'parent_id': False,
    }),
    'merchandise': Category.create({
        'name': 'Gym Merchandise',
        'parent_id': False,
    }),
    'services': Category.create({
        'name': 'Training Services',
        'parent_id': False,
    }),
}

print(f"✓ Created {len(categories)} product categories")
print()

# ============================================================================
# STEP 3: CREATE MEMBERSHIP PRODUCTS
# ============================================================================
print("[3/12] Creating membership products...")

# Get Costa Rica tax (13%)
Tax = odoo.env['account.tax']
tax_ids = Tax.search([('amount', '=', 13), ('type_tax_use', '=', 'sale')])
tax_13 = tax_ids[0] if tax_ids else False

membership_products = []

memberships_data = [
    {
        'name': 'Membresía Mensual - Acceso Completo',
        'list_price': 45000.00,  # ₡45,000 CRC
        'description': 'Acceso ilimitado al gimnasio, clases grupales incluidas',
        'recurring_invoice': True,
    },
    {
        'name': 'Membresía Trimestral - Acceso Completo',
        'list_price': 120000.00,  # ₡120,000 CRC (saves ₡15k)
        'description': 'Acceso ilimitado por 3 meses, ahorra ₡15,000',
        'recurring_invoice': True,
    },
    {
        'name': 'Membresía Anual - Acceso Completo',
        'list_price': 450000.00,  # ₡450,000 CRC (saves ₡90k)
        'description': 'Acceso ilimitado por 12 meses, ahorra ₡90,000',
        'recurring_invoice': True,
    },
    {
        'name': 'Membresía Básica - Solo Gym',
        'list_price': 30000.00,  # ₡30,000 CRC
        'description': 'Acceso al área de pesas y cardio, sin clases grupales',
        'recurring_invoice': True,
    },
    {
        'name': 'Pase del Día',
        'list_price': 5000.00,  # ₡5,000 CRC
        'description': 'Acceso por un día al gimnasio',
        'recurring_invoice': False,
    },
]

for m_data in memberships_data:
    product_id = Product.create({
        'name': m_data['name'],
        'list_price': m_data['list_price'],
        'standard_price': m_data['list_price'] * 0.1,  # Cost basis
        'type': 'service',
        'categ_id': categories['memberships'],
        'description_sale': m_data['description'],
        'taxes_id': [(6, 0, [tax_13])] if tax_13 else [],
        'sale_ok': True,
        'purchase_ok': False,
    })
    membership_products.append(product_id)

print(f"✓ Created {len(membership_products)} membership products")
print()

# ============================================================================
# STEP 4: CREATE CLASS PACKAGES & SERVICES
# ============================================================================
print("[4/12] Creating class packages and services...")

class_products = []

classes_data = [
    {'name': 'Yoga - Clase Individual', 'price': 8000, 'category': 'classes'},
    {'name': 'CrossFit - Clase Individual', 'price': 10000, 'category': 'classes'},
    {'name': 'Spinning - Clase Individual', 'price': 7000, 'category': 'classes'},
    {'name': 'Zumba - Clase Individual', 'price': 6000, 'category': 'classes'},
    {'name': 'Pilates - Clase Individual', 'price': 9000, 'category': 'classes'},
    {'name': 'Paquete 10 Clases Grupales', 'price': 60000, 'category': 'classes'},
    {'name': 'Paquete 20 Clases Grupales', 'price': 110000, 'category': 'classes'},
    {'name': 'Entrenamiento Personal (1 sesión)', 'price': 25000, 'category': 'services'},
    {'name': 'Paquete 5 Sesiones Personales', 'price': 110000, 'category': 'services'},
    {'name': 'Paquete 10 Sesiones Personales', 'price': 200000, 'category': 'services'},
    {'name': 'Evaluación Física Completa', 'price': 15000, 'category': 'services'},
    {'name': 'Plan Nutricional Personalizado', 'price': 35000, 'category': 'services'},
]

for c_data in classes_data:
    product_id = Product.create({
        'name': c_data['name'],
        'list_price': c_data['price'],
        'standard_price': c_data['price'] * 0.15,
        'type': 'service',
        'categ_id': categories[c_data['category']],
        'taxes_id': [(6, 0, [tax_13])] if tax_13 else [],
        'sale_ok': True,
        'purchase_ok': False,
    })
    class_products.append(product_id)

print(f"✓ Created {len(class_products)} class and service products")
print()

# ============================================================================
# STEP 5: CREATE SUPPLEMENTS & MERCHANDISE
# ============================================================================
print("[5/12] Creating supplements and merchandise...")

retail_products = []

retail_data = [
    # Supplements
    {'name': 'Proteína Whey 2lb', 'price': 28000, 'category': 'supplements', 'type': 'product'},
    {'name': 'Creatina Monohidrato 300g', 'price': 18000, 'category': 'supplements', 'type': 'product'},
    {'name': 'BCAA 200 cápsulas', 'price': 22000, 'category': 'supplements', 'type': 'product'},
    {'name': 'Pre-Workout 300g', 'price': 25000, 'category': 'supplements', 'type': 'product'},
    {'name': 'Glutamina 300g', 'price': 16000, 'category': 'supplements', 'type': 'product'},
    {'name': 'Multivitamínico 60 tabs', 'price': 12000, 'category': 'supplements', 'type': 'product'},
    {'name': 'Omega 3 100 caps', 'price': 15000, 'category': 'supplements', 'type': 'product'},
    # Merchandise
    {'name': 'Shaker Bottle 700ml', 'price': 5000, 'category': 'merchandise', 'type': 'product'},
    {'name': 'Camiseta GYM Oficial', 'price': 12000, 'category': 'merchandise', 'type': 'product'},
    {'name': 'Toalla Deportiva', 'price': 8000, 'category': 'merchandise', 'type': 'product'},
    {'name': 'Guantes de Entrenamiento', 'price': 15000, 'category': 'merchandise', 'type': 'product'},
    {'name': 'Cinturón de Levantamiento', 'price': 35000, 'category': 'merchandise', 'type': 'product'},
    {'name': 'Banda Elástica Set', 'price': 18000, 'category': 'merchandise', 'type': 'product'},
]

for r_data in retail_data:
    product_id = Product.create({
        'name': r_data['name'],
        'list_price': r_data['price'],
        'standard_price': r_data['price'] * 0.5,  # 50% cost for retail
        'type': r_data['type'],
        'categ_id': categories[r_data['category']],
        'taxes_id': [(6, 0, [tax_13])] if tax_13 else [],
        'sale_ok': True,
        'purchase_ok': True,
    })
    retail_products.append(product_id)

print(f"✓ Created {len(retail_products)} retail products")
print()

# ============================================================================
# STEP 6: CREATE GYM MEMBERS
# ============================================================================
print("[6/12] Creating gym members...")

first_names = [
    'Carlos', 'María', 'José', 'Ana', 'Luis', 'Carmen', 'Diego', 'Laura',
    'Miguel', 'Sofia', 'Javier', 'Isabel', 'Roberto', 'Valentina', 'Fernando',
    'Camila', 'Andrés', 'Daniela', 'Ricardo', 'Gabriela', 'Pablo', 'Natalia',
    'Esteban', 'Adriana', 'Mauricio', 'Paola', 'Sergio', 'Melissa', 'Rodrigo', 'Carolina'
]

last_names = [
    'González', 'Rodríguez', 'Fernández', 'López', 'Martínez', 'Sánchez',
    'Pérez', 'Gómez', 'Ramírez', 'Castro', 'Morales', 'Vargas', 'Jiménez',
    'Rojas', 'Alvarado', 'Herrera', 'Solís', 'Mora', 'Quesada', 'Arias'
]

members = []

for i in range(30):
    first = random.choice(first_names)
    last = random.choice(last_names)

    member_id = Partner.create({
        'name': f'{first} {last}',
        'email': f'{first.lower()}.{last.lower()}{i}@email.com',
        'phone': f'8{random.randint(100, 999)}-{random.randint(1000, 9999)}',
        'street': f'Calle {random.randint(1, 100)}',
        'city': random.choice(['San José', 'Alajuela', 'Cartago', 'Heredia', 'Escazú']),
        'country_id': odoo.env.ref('base.cr').id,  # Costa Rica
        'customer_rank': 1,
        'is_company': False,
        'company_id': company_id,
    })
    members.append(member_id)

print(f"✓ Created {len(members)} gym members")
print()

# ============================================================================
# STEP 7: CREATE CRM LEADS (PROSPECTS)
# ============================================================================
print("[7/12] Creating CRM leads (prospects)...")

leads = []
lead_stages = CRMLead.search([], limit=4)  # Get first 4 pipeline stages

for i in range(15):
    first = random.choice(first_names)
    last = random.choice(last_names)

    lead_id = CRMLead.create({
        'name': f'Interesado en membresía - {first} {last}',
        'contact_name': f'{first} {last}',
        'email_from': f'{first.lower()}.{last.lower()}.lead{i}@email.com',
        'phone': f'8{random.randint(100, 999)}-{random.randint(1000, 9999)}',
        'description': random.choice([
            'Quiere probar clases de CrossFit',
            'Busca membresía anual con descuento',
            'Interesado en entrenamiento personal',
            'Pregunta por clases de Yoga',
            'Quiere tour del gimnasio',
        ]),
        'type': 'opportunity',
        'stage_id': random.choice(lead_stages) if lead_stages else False,
    })
    leads.append(lead_id)

print(f"✓ Created {len(leads)} CRM leads")
print()

# ============================================================================
# STEP 8: CREATE EMPLOYEES (STAFF & INSTRUCTORS)
# ============================================================================
print("[8/12] Creating employees (staff & instructors)...")

employees = []

staff_data = [
    {'name': 'Ana Martínez', 'job': 'Gerente General', 'email': 'ana.martinez@gym.cr'},
    {'name': 'Carlos Rodríguez', 'job': 'Recepcionista', 'email': 'carlos.rodriguez@gym.cr'},
    {'name': 'María González', 'job': 'Instructora de Yoga', 'email': 'maria.gonzalez@gym.cr'},
    {'name': 'José Pérez', 'job': 'Instructor de CrossFit', 'email': 'jose.perez@gym.cr'},
    {'name': 'Laura Sánchez', 'job': 'Instructora de Spinning', 'email': 'laura.sanchez@gym.cr'},
    {'name': 'Diego Morales', 'job': 'Entrenador Personal', 'email': 'diego.morales@gym.cr'},
    {'name': 'Sofia Vargas', 'job': 'Instructora de Zumba', 'email': 'sofia.vargas@gym.cr'},
    {'name': 'Miguel Castro', 'job': 'Entrenador Personal', 'email': 'miguel.castro@gym.cr'},
]

for staff in staff_data:
    emp_id = HREmployee.create({
        'name': staff['name'],
        'job_title': staff['job'],
        'work_email': staff['email'],
        'company_id': company_id,
    })
    employees.append(emp_id)

print(f"✓ Created {len(employees)} employees")
print()

# ============================================================================
# STEP 9: CREATE SALES ORDERS (MEMBERSHIPS)
# ============================================================================
print("[9/12] Creating sales orders for memberships...")

sales_orders = []

for i, member in enumerate(members[:20]):  # First 20 members get active memberships
    # Randomly assign membership type
    membership_product = random.choice(membership_products[:4])  # Exclude day pass

    so_id = SaleOrder.create({
        'partner_id': member,
        'date_order': (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d %H:%M:%S'),
        'order_line': [(0, 0, {
            'product_id': membership_product,
            'product_uom_qty': 1,
            'price_unit': Product.browse(membership_product).list_price,
        })],
    })

    # Confirm the order
    SaleOrder.browse(so_id).action_confirm()

    sales_orders.append(so_id)

print(f"✓ Created {len(sales_orders)} membership sales orders")
print()

# ============================================================================
# STEP 10: CREATE INVOICES
# ============================================================================
print("[10/12] Creating invoices...")

invoices_created = 0

for so_id in sales_orders[:15]:  # Invoice first 15 orders
    so = SaleOrder.browse(so_id)

    # Create invoice
    invoice_ids = so._create_invoices()

    if invoice_ids:
        invoice = AccountMove.browse(invoice_ids[0])

        # Post some invoices (mark as confirmed)
        if random.random() > 0.3:  # 70% posted
            invoice.action_post()

            # Register payment for some
            if random.random() > 0.4:  # 60% of posted invoices are paid
                invoices_created += 1

print(f"✓ Created and processed {invoices_created} invoices")
print()

# ============================================================================
# STEP 11: CREATE CALENDAR EVENTS (CLASSES)
# ============================================================================
print("[11/12] Creating calendar events (fitness classes)...")

events = []

class_schedule = [
    {'name': 'Yoga Matutino', 'hour': 6, 'duration': 1.5, 'day_offset': 0},
    {'name': 'CrossFit Mañana', 'hour': 7, 'duration': 1, 'day_offset': 0},
    {'name': 'Spinning', 'hour': 9, 'duration': 1, 'day_offset': 0},
    {'name': 'Yoga Medio Día', 'hour': 12, 'duration': 1.5, 'day_offset': 0},
    {'name': 'Zumba', 'hour': 17, 'duration': 1, 'day_offset': 0},
    {'name': 'CrossFit Tarde', 'hour': 18, 'duration': 1, 'day_offset': 0},
    {'name': 'Pilates', 'hour': 19, 'duration': 1.5, 'day_offset': 0},
]

# Create classes for next 7 days
for day in range(7):
    for class_info in class_schedule:
        start = datetime.now() + timedelta(days=day, hours=class_info['hour'] - datetime.now().hour)
        stop = start + timedelta(hours=class_info['duration'])

        # Assign random instructor
        instructor = random.choice(employees[2:])  # Skip manager and receptionist

        event_id = CalendarEvent.create({
            'name': class_info['name'],
            'start': start.strftime('%Y-%m-%d %H:%M:%S'),
            'stop': stop.strftime('%Y-%m-%d %H:%M:%S'),
            'allday': False,
            'description': f'Clase grupal de {class_info["name"]}',
            'user_id': odoo.env.user.id,
        })
        events.append(event_id)

print(f"✓ Created {len(events)} calendar events (classes)")
print()

# ============================================================================
# STEP 12: SUMMARY
# ============================================================================
print("=" * 70)
print("DATA POPULATION COMPLETE!")
print("=" * 70)
print()
print("Summary of created records:")
print(f"  • Product Categories: {len(categories)}")
print(f"  • Membership Products: {len(membership_products)}")
print(f"  • Class/Service Products: {len(class_products)}")
print(f"  • Retail Products: {len(retail_products)}")
print(f"  • Gym Members: {len(members)}")
print(f"  • CRM Leads: {len(leads)}")
print(f"  • Employees: {len(employees)}")
print(f"  • Sales Orders: {len(sales_orders)}")
print(f"  • Invoices: {invoices_created}")
print(f"  • Calendar Events: {len(events)}")
print()
print("You can now explore:")
print("  • Sales → Customers (gym members)")
print("  • Sales → Products (memberships, classes, retail)")
print("  • Sales → Orders (membership purchases)")
print("  • Accounting → Invoices")
print("  • CRM → Leads (prospects)")
print("  • Employees → Employees (staff)")
print("  • Calendar → Events (fitness class schedule)")
print()
print("Access Odoo at: http://localhost:8070")
print("=" * 70)
