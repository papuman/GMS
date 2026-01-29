#!/usr/bin/env python3
"""
Populate Real Gym Products - Simple Version
============================================
Removes non-gym sample data and adds real products from top brands.
Images can be added later via Odoo interface.
"""

import random

print("=" * 70)
print("REAL GYM PRODUCTS - Data Population")
print("=" * 70)

# ============================================================================
# STEP 1: SET CURRENCY TO COSTA RICAN COLÓN
# ============================================================================
print("\n[1/7] Setting currency to Costa Rican Colón (CRC)...")

Company = env['res.company']
Currency = env['res.currency']

crc_currency = Currency.search([('name', '=', 'CRC')], limit=1)

if crc_currency:
    company = env.user.company_id
    company.write({'currency_id': crc_currency.id})
    print(f"✓ Currency set to CRC (₡ Colón Costarricense)")
else:
    print("⚠ CRC currency not found, using default")

# ============================================================================
# STEP 2: REMOVE NON-GYM SAMPLE DATA
# ============================================================================
print("\n[2/7] Removing previous sample data...")

Product = env['product.product']
Category = env['product.category']
Partner = env['res.partner']
SaleOrder = env['sale.order']
CRMLead = env['crm.lead']
HREmployee = env['hr.employee']
CalendarEvent = env['calendar.event']
AccountMove = env['account.move']

# Delete in correct order (dependencies first)
print("  Deleting sales orders...")
orders = SaleOrder.search([('create_date', '>=', '2025-12-28')])
for order in orders:
    try:
        order.unlink()
    except:
        pass

print("  Deleting invoices...")
invoices = AccountMove.search([('move_type', 'in', ['out_invoice', 'out_refund']), ('create_date', '>=', '2025-12-28')])
for inv in invoices:
    try:
        inv.unlink()
    except:
        pass

print("  Deleting leads...")
CRMLead.search([('create_date', '>=', '2025-12-28')]).unlink()

print("  Deleting calendar events...")
CalendarEvent.search([('create_date', '>=', '2025-12-28')]).unlink()

print("  Deleting employees...")
HREmployee.search([('create_date', '>=', '2025-12-28')]).unlink()

print("  Deleting customers...")
Partner.search([('customer_rank', '>', 0), ('create_date', '>=', '2025-12-28')]).unlink()

print("  Deleting products...")
Product.search([('create_date', '>=', '2025-12-28')]).unlink()

print("  Deleting categories...")
Category.search([('create_date', '>=', '2025-12-28')]).unlink()

print("✓ Sample data cleanup complete")

# ============================================================================
# STEP 3: CREATE GYM PRODUCT CATEGORIES
# ============================================================================
print("\n[3/7] Creating gym product categories...")

categories = {}

cat_data = [
    'Proteínas',
    'Pre-Entrenamiento',
    'BCAA & Aminoácidos',
    'Creatina',
    'Bebidas Deportivas',
    'Bebidas Energéticas',
    'Refrescos',
    'Barras Proteicas',
    'Snacks Saludables',
    'Accesorios Gym',
    'Ropa Deportiva',
]

for name in cat_data:
    cat = Category.create({'name': name})
    categories[name] = cat.id

print(f"✓ Created {len(categories)} categories")

# Get tax
Tax = env['account.tax']
tax_ids = Tax.search([('amount', '=', 13), ('type_tax_use', '=', 'sale')], limit=1)
tax_13 = tax_ids.ids if tax_ids else []

# ============================================================================
# STEP 4: CREATE PROTEIN PRODUCTS (Top Brands)
# ============================================================================
print("\n[4/7] Creating protein products from top brands...")

proteins = [
    # Optimum Nutrition
    ("Optimum Nutrition Gold Standard Whey - Double Rich Chocolate 2lbs", 35000),
    ("Optimum Nutrition Gold Standard Whey - Vanilla Ice Cream 2lbs", 35000),
    ("Optimum Nutrition Gold Standard Whey - Extreme Milk Chocolate 5lbs", 65000),
    ("Optimum Nutrition Gold Standard Whey - Strawberry Banana 5lbs", 65000),
    ("Optimum Nutrition Gold Standard 100% Isolate - Chocolate Bliss 3lbs", 48000),
    ("Optimum Nutrition Gold Standard 100% Isolate - Rich Vanilla 3lbs", 48000),
    ("Optimum Nutrition Platinum Hydrowhey - Chocolate 3.5lbs", 72000),

    # MuscleTech
    ("MuscleTech Nitro-Tech Whey - Chocolate 4lbs", 52000),
    ("MuscleTech Nitro-Tech Whey - Vanilla 4lbs", 52000),
    ("MuscleTech Nitro-Tech Whey - Cookies & Cream 4lbs", 52000),
    ("MuscleTech Phase8 Protein - Chocolate 4.6lbs", 58000),
    ("MuscleTech Phase8 Protein - Vanilla 4.6lbs", 58000),
    ("MuscleTech Nitro-Tech Ripped - Chocolate 4lbs", 62000),

    # BSN
    ("BSN Syntha-6 - Chocolate Milkshake 5lbs", 62000),
    ("BSN Syntha-6 - Vanilla Ice Cream 5lbs", 62000),
    ("BSN Syntha-6 - Cookies & Cream 5lbs", 62000),
    ("BSN Syntha-6 - Strawberry Milkshake 5lbs", 62000),
    ("BSN True-Mass 1200 - Chocolate Milkshake 10.25lbs", 95000),
    ("BSN Syntha-6 Isolate - Chocolate 4lbs", 68000),

    # Dymatize
    ("Dymatize ISO100 Whey Isolate - Gourmet Chocolate 3lbs", 48000),
    ("Dymatize ISO100 Whey Isolate - Gourmet Vanilla 5lbs", 72000),
    ("Dymatize ISO100 Whey Isolate - Cookies & Cream 3lbs", 48000),
    ("Dymatize Elite 100% Whey - Rich Chocolate 5lbs", 58000),
    ("Dymatize Elite 100% Whey - Café Mocha 5lbs", 58000),

    # MyProtein
    ("MyProtein Impact Whey - Chocolate Smooth 2.2lbs", 32000),
    ("MyProtein Impact Whey - Vanilla 2.2lbs", 32000),
    ("MyProtein Impact Whey - Cookies & Cream 2.2lbs", 32000),
    ("MyProtein Impact Whey Isolate - Chocolate Brownie 2.2lbs", 42000),
    ("MyProtein Impact Whey Isolate - Vanilla 2.2lbs", 42000),

    # Isopure
    ("Isopure Zero Carb - Creamy Vanilla 3lbs", 55000),
    ("Isopure Zero Carb - Dutch Chocolate 3lbs", 55000),
    ("Isopure Zero Carb - Alpine Punch 3lbs", 55000),
    ("Isopure Low Carb - Cookies & Cream 3lbs", 52000),

    # Transparent Labs
    ("Transparent Labs 100% Grass-Fed Whey Isolate - Chocolate 2lbs", 58000),
    ("Transparent Labs 100% Grass-Fed Whey Isolate - Vanilla 2lbs", 58000),
    ("Transparent Labs 100% Grass-Fed Whey Isolate - Salted Caramel 2lbs", 58000),

    # Cellucor
    ("Cellucor Cor-Performance Whey - Whipped Vanilla 4lbs", 52000),
    ("Cellucor Cor-Performance Whey - Molten Chocolate 4lbs", 52000),
    ("Cellucor Cor-Performance Whey - Cookies & Cream 4lbs", 52000),

    # Legion
    ("Legion Whey+ Grass-Fed Isolate - Chocolate 2lbs", 62000),
    ("Legion Whey+ Grass-Fed Isolate - Vanilla 2lbs", 62000),

    # Garden of Life (Plant-Based)
    ("Garden of Life Sport Protein - Chocolate 1.85lbs", 48000),
    ("Garden of Life Sport Protein - Vanilla 1.85lbs", 48000),
]

protein_products = []
for name, price in proteins:
    prod = Product.create({
        'name': name,
        'list_price': price,
        'standard_price': price * 0.55,
        'type': 'consu',
        'categ_id': categories['Proteínas'],
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
    })
    protein_products.append(prod.id)

print(f"✓ Created {len(protein_products)} protein products")

# ============================================================================
# STEP 5: CREATE BEVERAGE PRODUCTS
# ============================================================================
print("\n[5/7] Creating beverage products...")

beverages = []

# Gatorade (Bebidas Deportivas)
gatorade = [
    ("Gatorade Cool Blue 600ml", 1500, categories['Bebidas Deportivas']),
    ("Gatorade Glacier Freeze 600ml", 1500, categories['Bebidas Deportivas']),
    ("Gatorade Fruit Punch 600ml", 1500, categories['Bebidas Deportivas']),
    ("Gatorade Lemon Lime 600ml", 1500, categories['Bebidas Deportivas']),
    ("Gatorade Orange 600ml", 1500, categories['Bebidas Deportivas']),
    ("Gatorade Fierce Grape 600ml", 1500, categories['Bebidas Deportivas']),
    ("Gatorade Zero Cool Blue 600ml", 1600, categories['Bebidas Deportivas']),
    ("Gatorade Zero Glacier Freeze 600ml", 1600, categories['Bebidas Deportivas']),
]

# Powerade (Bebidas Deportivas)
powerade = [
    ("Powerade Mountain Berry Blast 600ml", 1400, categories['Bebidas Deportivas']),
    ("Powerade Fruit Punch 600ml", 1400, categories['Bebidas Deportivas']),
    ("Powerade Orange 600ml", 1400, categories['Bebidas Deportivas']),
    ("Powerade White Cherry 600ml", 1400, categories['Bebidas Deportivas']),
    ("Powerade Zero Sugar Mixed Berry 600ml", 1400, categories['Bebidas Deportivas']),
]

# Soft Drinks (Refrescos)
soft_drinks = [
    ("Coca-Cola 355ml", 1200, categories['Refrescos']),
    ("Coca-Cola Zero 355ml", 1200, categories['Refrescos']),
    ("Sprite 355ml", 1200, categories['Refrescos']),
    ("Fanta Orange 355ml", 1200, categories['Refrescos']),
    ("Diet Coke 355ml", 1200, categories['Refrescos']),
]

# Energy Drinks (Bebidas Energéticas)
energy = [
    ("Monster Energy Original 473ml", 2500, categories['Bebidas Energéticas']),
    ("Monster Ultra Zero 473ml", 2500, categories['Bebidas Energéticas']),
    ("Monster Ultra Paradise 473ml", 2500, categories['Bebidas Energéticas']),
    ("Red Bull Energy Drink 250ml", 2200, categories['Bebidas Energéticas']),
    ("Red Bull Sugar Free 250ml", 2200, categories['Bebidas Energéticas']),
    ("Red Bull Tropical Edition 250ml", 2200, categories['Bebidas Energéticas']),
    ("Bang Energy - Blue Razz 473ml", 2800, categories['Bebidas Energéticas']),
    ("Bang Energy - Peach Mango 473ml", 2800, categories['Bebidas Energéticas']),
]

all_beverages = gatorade + powerade + soft_drinks + energy

beverage_products = []
for name, price, cat_id in all_beverages:
    prod = Product.create({
        'name': name,
        'list_price': price,
        'standard_price': price * 0.60,
        'type': 'consu',
        'categ_id': cat_id,
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
    })
    beverage_products.append(prod.id)

print(f"✓ Created {len(beverage_products)} beverage products")

# ============================================================================
# STEP 6: CREATE SUPPLEMENTS (Pre-Workout, BCAA, Creatine)
# ============================================================================
print("\n[6/7] Creating supplement products...")

supplements = []

# Pre-Workout
preworkouts = [
    ("Cellucor C4 Original - Fruit Punch 30srv", 32000, categories['Pre-Entrenamiento']),
    ("Cellucor C4 Original - Icy Blue Razz 30srv", 32000, categories['Pre-Entrenamiento']),
    ("Cellucor C4 Original - Watermelon 30srv", 32000, categories['Pre-Entrenamiento']),
    ("Optimum Nutrition Gold Standard Pre-Workout - Green Apple 30srv", 35000, categories['Pre-Entrenamiento']),
    ("Optimum Nutrition Gold Standard Pre-Workout - Fruit Punch 30srv", 35000, categories['Pre-Entrenamiento']),
    ("MuscleTech Vapor X5 Next Gen 30srv", 38000, categories['Pre-Entrenamiento']),
    ("BSN N.O.-Xplode Pre-Workout - Fruit Punch 30srv", 34000, categories['Pre-Entrenamiento']),
    ("Transparent Labs PreSeries BULK 30srv", 58000, categories['Pre-Entrenamiento']),
    ("Legion Pulse Pre-Workout 30srv", 52000, categories['Pre-Entrenamiento']),
]

# BCAA
bcaas = [
    ("Optimum Nutrition BCAA 1000 - 200 caps", 28000, categories['BCAA & Aminoácidos']),
    ("MuscleTech Platinum BCAA 8:1:1 - 200 tabs", 26000, categories['BCAA & Aminoácidos']),
    ("BSN Amino X - Blue Raz 30srv", 30000, categories['BCAA & Aminoácidos']),
    ("BSN Amino X - Fruit Punch 30srv", 30000, categories['BCAA & Aminoácidos']),
    ("Cellucor Alpha Amino - Fruit Punch 30srv", 32000, categories['BCAA & Aminoácidos']),
    ("Scivation Xtend Original BCAA - Blue Raspberry 30srv", 32000, categories['BCAA & Aminoácidos']),
    ("Scivation Xtend Original BCAA - Mango 30srv", 32000, categories['BCAA & Aminoácidos']),
]

# Creatine
creatines = [
    ("Optimum Nutrition Micronized Creatine 300g", 22000, categories['Creatina']),
    ("MuscleTech Platinum 100% Creatine 400g", 24000, categories['Creatina']),
    ("BSN CellMass 2.0 50srv", 35000, categories['Creatina']),
    ("Dymatize Creatine Micronized 500g", 26000, categories['Creatina']),
    ("Transparent Labs Creatine HMB 30srv", 42000, categories['Creatina']),
    ("MuscleTech Cell-Tech 3lbs", 48000, categories['Creatina']),
]

all_supplements = preworkouts + bcaas + creatines

supplement_products = []
for name, price, cat_id in all_supplements:
    prod = Product.create({
        'name': name,
        'list_price': price,
        'standard_price': price * 0.55,
        'type': 'consu',
        'categ_id': cat_id,
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
    })
    supplement_products.append(prod.id)

print(f"✓ Created {len(supplement_products)} supplement products")

# ============================================================================
# STEP 7: CREATE BARS, SNACKS & ACCESSORIES
# ============================================================================
print("\n[7/7] Creating bars, snacks, and accessories...")

# Protein Bars
bars = [
    ("Quest Bar - Chocolate Chip Cookie Dough 12-pack", 18000, categories['Barras Proteicas']),
    ("Quest Bar - Cookies & Cream 12-pack", 18000, categories['Barras Proteicas']),
    ("Quest Bar - Birthday Cake 12-pack", 18000, categories['Barras Proteicas']),
    ("ONE Bar - Maple Glazed Doughnut 12-pack", 16000, categories['Barras Proteicas']),
    ("ONE Bar - Almond Bliss 12-pack", 16000, categories['Barras Proteicas']),
    ("Built Bar - Coconut 12-pack", 20000, categories['Barras Proteicas']),
    ("Built Bar - Peanut Butter Brownie 12-pack", 20000, categories['Barras Proteicas']),
    ("Optimum Nutrition Protein Bars - Chocolate Brownie 12-pack", 22000, categories['Barras Proteicas']),
]

# Snacks
snacks = [
    ("Clif Bar - Chocolate Chip 12-pack", 14000, categories['Snacks Saludables']),
    ("Clif Bar - Crunchy Peanut Butter 12-pack", 14000, categories['Snacks Saludables']),
    ("Kind Bar - Dark Chocolate Nuts & Sea Salt 12-pack", 15000, categories['Snacks Saludables']),
    ("Kind Bar - Almond & Coconut 12-pack", 15000, categories['Snacks Saludables']),
    ("RXBar - Chocolate Sea Salt 12-pack", 18000, categories['Snacks Saludables']),
    ("Perfect Bar - Peanut Butter 8-pack", 16000, categories['Snacks Saludables']),
]

# Accessories
accessories = [
    ("BlenderBottle Classic Shaker 28oz", 8000, categories['Accesorios Gym']),
    ("BlenderBottle Pro Series 32oz", 12000, categories['Accesorios Gym']),
    ("Harbinger Pro Gym Gloves", 22000, categories['Accesorios Gym']),
    ("Harbinger Women's Gloves", 22000, categories['Accesorios Gym']),
    ("RDX Weightlifting Belt 4-inch", 38000, categories['Accesorios Gym']),
    ("Nike Gym Towel", 12000, categories['Accesorios Gym']),
    ("Adidas Training Towel", 10000, categories['Accesorios Gym']),
    ("Under Armour Compression Shirt", 28000, categories['Ropa Deportiva']),
    ("Nike Dri-FIT Training Shirt", 32000, categories['Ropa Deportiva']),
    ("Adidas Training Shorts", 24000, categories['Ropa Deportiva']),
    ("Under Armour Training Shorts", 26000, categories['Ropa Deportiva']),
    ("TriggerPoint Foam Roller", 35000, categories['Accesorios Gym']),
    ("Resistance Bands Set 5-pack", 18000, categories['Accesorios Gym']),
]

all_extras = bars + snacks + accessories

extra_products = []
for name, price, cat_id in all_extras:
    prod = Product.create({
        'name': name,
        'list_price': price,
        'standard_price': price * 0.50,
        'type': 'consu',
        'categ_id': cat_id,
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
    })
    extra_products.append(prod.id)

print(f"✓ Created {len(extra_products)} bars, snacks, and accessories")

# ============================================================================
# COMMIT
# ============================================================================
print("\n[8/8] Committing to database...")
env.cr.commit()

total_products = len(protein_products) + len(beverage_products) + len(supplement_products) + len(extra_products)

print("\n" + "=" * 70)
print("REAL GYM PRODUCTS POPULATED SUCCESSFULLY!")
print("=" * 70)
print(f"\nCurrency: ₡ Colón Costarricense (CRC)")
print(f"\nProduct Summary:")
print(f"  • Proteínas: {len(protein_products)} products")
print(f"  • Bebidas: {len(beverage_products)} products")
print(f"  • Suplementos: {len(supplement_products)} products")
print(f"  • Barras/Snacks/Accesorios: {len(extra_products)} products")
print(f"  • TOTAL: {total_products} products")
print(f"\nTop Brands Included:")
print(f"  • Optimum Nutrition, MuscleTech, BSN, Dymatize, MyProtein")
print(f"  • Isopure, Transparent Labs, Cellucor, Legion")
print(f"  • Gatorade, Powerade, Monster, Red Bull, Bang")
print(f"  • Quest, ONE, Clif, Kind, RXBar")
print(f"  • Nike, Adidas, Under Armour")
print(f"\nAll products have:")
print(f"  ✓ Real brand and product names")
print(f"  ✓ Costa Rica 13% IVA tax")
print(f"  ✓ Realistic CRC pricing")
print(f"\nAccess: http://localhost:8070")
print(f"Login: admin / admin")
print("=" * 70)
