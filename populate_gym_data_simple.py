#!/usr/bin/env python3
"""
Populate GMS Validation Database - Simple Version
==================================================
Run this inside Odoo shell to populate sample gym data.

Usage:
    docker exec -it gms_odoo odoo shell -d gms_validation --no-http < /tmp/populate_gym_data_simple.py
"""

import random
from datetime import datetime, timedelta

print("=" * 70)
print("GMS VALIDATION - Sample Data Generator")
print("=" * 70)

# Get models
Partner = env['res.partner']
Product = env['product.product']
Template = env['product.template']
Category = env['product.category']
SaleOrder = env['sale.order']
AccountMove = env['account.move']
CRMLead = env['crm.lead']
HREmployee = env['hr.employee']
CalendarEvent = env['calendar.event']

company_id = env.company.id

# ============================================================================
# STEP 1: CREATE PRODUCT CATEGORIES
# ============================================================================
print("\n[1/11] Creating product categories...")

categories = {}

cat_names = [
    'Gym Memberships',
    'Fitness Classes',
    'Supplements',
    'Gym Merchandise',
    'Training Services',
]

for cat_name in cat_names:
    cat = Category.create({
        'name': cat_name,
    })
    categories[cat_name] = cat.id

print(f"✓ Created {len(categories)} product categories")

# ============================================================================
# STEP 2: CREATE MEMBERSHIP PRODUCTS
# ============================================================================
print("\n[2/11] Creating membership products...")

# Get Costa Rica tax (13%)
Tax = env['account.tax']
tax_ids = Tax.search([('amount', '=', 13), ('type_tax_use', '=', 'sale')], limit=1)
tax_13 = tax_ids.ids if tax_ids else []

memberships_data = [
    ('Membresía Mensual - Acceso Completo', 45000, 'Acceso ilimitado al gimnasio'),
    ('Membresía Trimestral - Acceso Completo', 120000, 'Acceso ilimitado por 3 meses'),
    ('Membresía Anual - Acceso Completo', 450000, 'Acceso ilimitado por 12 meses'),
    ('Membresía Básica - Solo Gym', 30000, 'Solo área de pesas y cardio'),
    ('Pase del Día', 5000, 'Acceso por un día'),
]

membership_products = []

for name, price, desc in memberships_data:
    prod = Product.create({
        'name': name,
        'list_price': price,
        'standard_price': price * 0.1,
        'type': 'service',
        'categ_id': categories['Gym Memberships'],
        'description_sale': desc,
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': False,
    })
    membership_products.append(prod.id)

print(f"✓ Created {len(membership_products)} membership products")

# ============================================================================
# STEP 3: CREATE CLASS PACKAGES & SERVICES
# ============================================================================
print("\n[3/11] Creating classes and services...")

classes_data = [
    ('Yoga - Clase Individual', 8000, 'Fitness Classes'),
    ('CrossFit - Clase Individual', 10000, 'Fitness Classes'),
    ('Spinning - Clase Individual', 7000, 'Fitness Classes'),
    ('Zumba - Clase Individual', 6000, 'Fitness Classes'),
    ('Pilates - Clase Individual', 9000, 'Fitness Classes'),
    ('Paquete 10 Clases Grupales', 60000, 'Fitness Classes'),
    ('Paquete 20 Clases Grupales', 110000, 'Fitness Classes'),
    ('Entrenamiento Personal (1 sesión)', 25000, 'Training Services'),
    ('Paquete 5 Sesiones Personales', 110000, 'Training Services'),
    ('Paquete 10 Sesiones Personales', 200000, 'Training Services'),
    ('Evaluación Física Completa', 15000, 'Training Services'),
    ('Plan Nutricional Personalizado', 35000, 'Training Services'),
]

class_products = []

for name, price, cat in classes_data:
    prod = Product.create({
        'name': name,
        'list_price': price,
        'standard_price': price * 0.15,
        'type': 'service',
        'categ_id': categories[cat],
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': False,
    })
    class_products.append(prod.id)

print(f"✓ Created {len(class_products)} class/service products")

# ============================================================================
# STEP 4: CREATE SUPPLEMENTS & MERCHANDISE
# ============================================================================
print("\n[4/11] Creating supplements and merchandise...")

retail_data = [
    ('Proteína Whey 2lb', 28000, 'Supplements', 'consu'),
    ('Creatina Monohidrato 300g', 18000, 'Supplements', 'consu'),
    ('BCAA 200 cápsulas', 22000, 'Supplements', 'consu'),
    ('Pre-Workout 300g', 25000, 'Supplements', 'consu'),
    ('Glutamina 300g', 16000, 'Supplements', 'consu'),
    ('Multivitamínico 60 tabs', 12000, 'Supplements', 'consu'),
    ('Omega 3 100 caps', 15000, 'Supplements', 'consu'),
    ('Shaker Bottle 700ml', 5000, 'Gym Merchandise', 'consu'),
    ('Camiseta GYM Oficial', 12000, 'Gym Merchandise', 'consu'),
    ('Toalla Deportiva', 8000, 'Gym Merchandise', 'consu'),
    ('Guantes de Entrenamiento', 15000, 'Gym Merchandise', 'consu'),
    ('Cinturón de Levantamiento', 35000, 'Gym Merchandise', 'consu'),
    ('Banda Elástica Set', 18000, 'Gym Merchandise', 'consu'),
]

retail_products = []

for name, price, cat, ptype in retail_data:
    prod = Product.create({
        'name': name,
        'list_price': price,
        'standard_price': price * 0.5,
        'type': ptype,
        'categ_id': categories[cat],
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
    })
    retail_products.append(prod.id)

print(f"✓ Created {len(retail_products)} retail products")

# ============================================================================
# STEP 5: CREATE GYM MEMBERS
# ============================================================================
print("\n[5/11] Creating gym members...")

first_names = ['Carlos', 'María', 'José', 'Ana', 'Luis', 'Carmen', 'Diego', 'Laura',
    'Miguel', 'Sofia', 'Javier', 'Isabel', 'Roberto', 'Valentina', 'Fernando',
    'Camila', 'Andrés', 'Daniela', 'Ricardo', 'Gabriela', 'Pablo', 'Natalia',
    'Esteban', 'Adriana', 'Mauricio', 'Paola', 'Sergio', 'Melissa', 'Rodrigo', 'Carolina']

last_names = ['González', 'Rodríguez', 'Fernández', 'López', 'Martínez', 'Sánchez',
    'Pérez', 'Gómez', 'Ramírez', 'Castro', 'Morales', 'Vargas', 'Jiménez',
    'Rojas', 'Alvarado', 'Herrera', 'Solís', 'Mora', 'Quesada', 'Arias']

members = []

for i in range(30):
    first = random.choice(first_names)
    last = random.choice(last_names)

    member = Partner.create({
        'name': f'{first} {last}',
        'email': f'{first.lower()}.{last.lower()}{i}@email.com',
        'phone': f'8{random.randint(100, 999)}-{random.randint(1000, 9999)}',
        'street': f'Calle {random.randint(1, 100)}',
        'city': random.choice(['San José', 'Alajuela', 'Cartago', 'Heredia', 'Escazú']),
        'country_id': env.ref('base.cr').id,
        'customer_rank': 1,
        'is_company': False,
    })
    members.append(member.id)

print(f"✓ Created {len(members)} gym members")

# ============================================================================
# STEP 6: CREATE CRM LEADS
# ============================================================================
print("\n[6/11] Creating CRM leads...")

Stage = env['crm.stage']
stages = Stage.search([], limit=4)

leads = []

for i in range(15):
    first = random.choice(first_names)
    last = random.choice(last_names)

    lead = CRMLead.create({
        'name': f'Interesado - {first} {last}',
        'contact_name': f'{first} {last}',
        'email_from': f'{first.lower()}.{last.lower()}.lead{i}@email.com',
        'phone': f'8{random.randint(100, 999)}-{random.randint(1000, 9999)}',
        'description': random.choice([
            'Quiere probar clases de CrossFit',
            'Busca membresía anual',
            'Interesado en entrenamiento personal',
            'Pregunta por clases de Yoga',
            'Quiere tour del gimnasio',
        ]),
        'type': 'opportunity',
        'stage_id': random.choice(stages).id if stages else False,
    })
    leads.append(lead.id)

print(f"✓ Created {len(leads)} CRM leads")

# ============================================================================
# STEP 7: CREATE EMPLOYEES
# ============================================================================
print("\n[7/11] Creating employees...")

staff_data = [
    ('Ana Martínez', 'Gerente General'),
    ('Carlos Rodríguez', 'Recepcionista'),
    ('María González', 'Instructora de Yoga'),
    ('José Pérez', 'Instructor de CrossFit'),
    ('Laura Sánchez', 'Instructora de Spinning'),
    ('Diego Morales', 'Entrenador Personal'),
    ('Sofia Vargas', 'Instructora de Zumba'),
    ('Miguel Castro', 'Entrenador Personal'),
]

employees = []

for name, job in staff_data:
    emp = HREmployee.create({
        'name': name,
        'job_title': job,
        'work_email': f'{name.lower().replace(" ", ".")}@gym.cr',
    })
    employees.append(emp.id)

print(f"✓ Created {len(employees)} employees")

# ============================================================================
# STEP 8: CREATE SALES ORDERS
# ============================================================================
print("\n[8/11] Creating sales orders...")

sales_orders = []

for member_id in members[:20]:
    membership = random.choice(membership_products[:4])

    so = SaleOrder.create({
        'partner_id': member_id,
        'date_order': (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d'),
        'order_line': [(0, 0, {
            'product_id': membership,
            'product_uom_qty': 1,
        })],
    })

    so.action_confirm()
    sales_orders.append(so.id)

print(f"✓ Created {len(sales_orders)} sales orders")

# ============================================================================
# STEP 9: CREATE INVOICES
# ============================================================================
print("\n[9/11] Creating invoices...")

invoices_count = 0

for so_id in sales_orders[:15]:
    so = SaleOrder.browse(so_id)
    inv_ids = so._create_invoices()

    if inv_ids:
        inv = AccountMove.browse(inv_ids[0])
        if random.random() > 0.3:
            inv.action_post()
            invoices_count += 1

print(f"✓ Created {invoices_count} invoices")

# ============================================================================
# STEP 10: CREATE CALENDAR EVENTS
# ============================================================================
print("\n[10/11] Creating calendar events...")

class_schedule = [
    ('Yoga Matutino', 6, 1.5),
    ('CrossFit Mañana', 7, 1),
    ('Spinning', 9, 1),
    ('Yoga Medio Día', 12, 1.5),
    ('Zumba', 17, 1),
    ('CrossFit Tarde', 18, 1),
    ('Pilates', 19, 1.5),
]

events = []

for day in range(7):
    for class_name, hour, duration in class_schedule:
        start = datetime.now() + timedelta(days=day, hours=hour - datetime.now().hour)
        stop = start + timedelta(hours=duration)

        event = CalendarEvent.create({
            'name': class_name,
            'start': start.strftime('%Y-%m-%d %H:%M:%S'),
            'stop': stop.strftime('%Y-%m-%d %H:%M:%S'),
            'allday': False,
        })
        events.append(event.id)

print(f"✓ Created {len(events)} calendar events")

# ============================================================================
# COMMIT
# ============================================================================
print("\n[11/11] Committing to database...")
env.cr.commit()

print("\n" + "=" * 70)
print("DATA POPULATION COMPLETE!")
print("=" * 70)
print(f"\nSummary:")
print(f"  • Categories: {len(categories)}")
print(f"  • Memberships: {len(membership_products)}")
print(f"  • Classes/Services: {len(class_products)}")
print(f"  • Retail: {len(retail_products)}")
print(f"  • Members: {len(members)}")
print(f"  • Leads: {len(leads)}")
print(f"  • Employees: {len(employees)}")
print(f"  • Sales Orders: {len(sales_orders)}")
print(f"  • Invoices: {invoices_count}")
print(f"  • Events: {len(events)}")
print("\nAccess: http://localhost:8070")
print("=" * 70)
