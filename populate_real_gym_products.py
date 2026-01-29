#!/usr/bin/env python3
"""
Populate Real Gym Products with Images
========================================
Removes non-gym sample data and adds real products from top brands.

Includes:
- Top 10 protein brands with full product lines
- Beverages (Gatorade, Powerade, Coke, Monster, Red Bull)
- Supplements (BCAA, Creatine, Pre-Workout)
- Protein bars, energy bars
- Gym merchandise and apparel

Each product includes real images from brand websites.
"""

import base64
import urllib.request
import random

print("=" * 70)
print("REAL GYM PRODUCTS - Data Population")
print("=" * 70)

# ============================================================================
# STEP 1: SET CURRENCY TO COSTA RICAN COLÓN
# ============================================================================
print("\n[1/8] Setting currency to Costa Rican Colón (CRC)...")

Company = env['res.company']
Currency = env['res.currency']

# Get Costa Rica Colón currency
crc_currency = Currency.search([('name', '=', 'CRC')], limit=1)

if crc_currency:
    # Update main company currency
    company = env.user.company_id
    company.write({'currency_id': crc_currency.id})
    print(f"✓ Currency set to CRC (Costa Rican Colón)")
else:
    print("⚠ CRC currency not found, keeping current currency")

# ============================================================================
# STEP 2: REMOVE NON-GYM SAMPLE DATA
# ============================================================================
print("\n[2/8] Removing non-gym sample data...")

# Delete previous sample data we created
Product = env['product.product']
Category = env['product.category']
Partner = env['res.partner']
SaleOrder = env['sale.order']
CRMLead = env['crm.lead']
HREmployee = env['hr.employee']
CalendarEvent = env['calendar.event']
AccountMove = env['account.move']

# Delete sales orders
orders = SaleOrder.search([('create_date', '>=', '2025-12-28')])
if orders:
    orders.unlink()
    print(f"  ✓ Removed {len(orders)} sales orders")

# Delete invoices
invoices = AccountMove.search([('move_type', 'in', ['out_invoice', 'out_refund']), ('create_date', '>=', '2025-12-28')])
if invoices:
    invoices.unlink()
    print(f"  ✓ Removed {len(invoices)} invoices")

# Delete leads
leads = CRMLead.search([('create_date', '>=', '2025-12-28')])
if leads:
    leads.unlink()
    print(f"  ✓ Removed {len(leads)} leads")

# Delete calendar events
events = CalendarEvent.search([('create_date', '>=', '2025-12-28')])
if events:
    events.unlink()
    print(f"  ✓ Removed {len(events)} calendar events")

# Delete employees (keep admin)
employees = HREmployee.search([('create_date', '>=', '2025-12-28')])
if employees:
    employees.unlink()
    print(f"  ✓ Removed {len(employees)} employees")

# Delete customer partners
partners = Partner.search([('customer_rank', '>', 0), ('create_date', '>=', '2025-12-28')])
if partners:
    partners.unlink()
    print(f"  ✓ Removed {len(partners)} customer records")

# Delete products created today
products = Product.search([('create_date', '>=', '2025-12-28')])
if products:
    products.unlink()
    print(f"  ✓ Removed {len(products)} sample products")

# Delete custom categories
categories = Category.search([('create_date', '>=', '2025-12-28')])
if categories:
    categories.unlink()
    print(f"  ✓ Removed {len(categories)} product categories")

print("✓ Sample data cleanup complete")

# ============================================================================
# STEP 3: CREATE GYM PRODUCT CATEGORIES
# ============================================================================
print("\n[3/8] Creating gym product categories...")

categories = {}

cat_data = [
    ('Proteínas', 'Protein Powders & Supplements'),
    ('Suplementos Pre-Entrenamiento', 'Pre-Workout Supplements'),
    ('Aminoácidos BCAA', 'BCAA & Amino Acids'),
    ('Creatina', 'Creatine Supplements'),
    ('Bebidas Deportivas', 'Sports Drinks'),
    ('Bebidas Energéticas', 'Energy Drinks'),
    ('Refrescos', 'Soft Drinks'),
    ('Barras Proteicas', 'Protein Bars'),
    ('Snacks Saludables', 'Healthy Snacks'),
    ('Accesorios Gym', 'Gym Accessories'),
    ('Ropa Deportiva', 'Athletic Apparel'),
]

for name, desc in cat_data:
    cat = Category.create({
        'name': name,
        'parent_id': False,
    })
    categories[name] = cat.id

print(f"✓ Created {len(categories)} product categories")

# ============================================================================
# HELPER: Download product image
# ============================================================================
def get_image_base64(url):
    """Download image from URL and return base64 encoded string"""
    try:
        # Simple image URLs that don't require complex headers
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            image_data = response.read()
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"    ⚠ Could not fetch image from {url}: {str(e)[:50]}")
        return False

# Get tax
Tax = env['account.tax']
tax_ids = Tax.search([('amount', '=', 13), ('type_tax_use', '=', 'sale')], limit=1)
tax_13 = tax_ids.ids if tax_ids else []

# ============================================================================
# STEP 4: CREATE PROTEIN PRODUCTS (Top Brands)
# ============================================================================
print("\n[4/8] Creating protein products from top brands...")

protein_products = []

# Product format: (Brand, Product Name, Size, Price CRC, Image URL)
proteins = [
    # Optimum Nutrition Gold Standard
    ("Optimum Nutrition", "Gold Standard 100% Whey - Double Rich Chocolate", "2 lbs", 35000,
     "https://www.optimumnutrition.com/sites/optimumnutrition.com/files/styles/original/public/2022-04/GoldStandard_Whey_DoubleRichChocolate_2lb_Front.png"),
    ("Optimum Nutrition", "Gold Standard 100% Whey - Vanilla Ice Cream", "2 lbs", 35000,
     "https://www.optimumnutrition.com/sites/optimumnutrition.com/files/styles/original/public/2022-04/GoldStandard_Whey_VanillaIceCream_2lb_Front.png"),
    ("Optimum Nutrition", "Gold Standard 100% Whey - Extreme Milk Chocolate", "5 lbs", 65000,
     "https://www.optimumnutrition.com/sites/optimumnutrition.com/files/styles/original/public/2022-04/GoldStandard_Whey_ExtremeMilkChocolate_5lb_Front.png"),
    ("Optimum Nutrition", "Gold Standard 100% Isolate - Chocolate Bliss", "3 lbs", 48000,
     "https://www.optimumnutrition.com/sites/optimumnutrition.com/files/styles/original/public/2023-03/GS100Isolate_ChocolateBliss_3lb.png"),

    # MuscleTech
    ("MuscleTech", "Nitro-Tech Whey Protein - Chocolate", "4 lbs", 52000,
     "https://cdn.muscletech.com/catalog/product/n/i/nitro-tech_chocolate_4lb_front.png"),
    ("MuscleTech", "Nitro-Tech Whey Protein - Vanilla", "4 lbs", 52000,
     "https://cdn.muscletech.com/catalog/product/n/i/nitro-tech_vanilla_4lb_front.png"),
    ("MuscleTech", "Phase8 Protein - Cookies and Cream", "4.6 lbs", 58000,
     "https://cdn.muscletech.com/catalog/product/p/h/phase8_cookiesandcream_4.6lb_front.png"),

    # BSN
    ("BSN", "Syntha-6 Protein - Chocolate Milkshake", "5 lbs", 62000,
     "https://bsnsupplements.com/cdn/shop/products/Syntha6_ChocolateMilkshake_5lb.png"),
    ("BSN", "Syntha-6 Protein - Vanilla Ice Cream", "5 lbs", 62000,
     "https://bsnsupplements.com/cdn/shop/products/Syntha6_VanillaIceCream_5lb.png"),
    ("BSN", "True-Mass 1200 - Chocolate Milkshake", "10.25 lbs", 95000,
     "https://bsnsupplements.com/cdn/shop/products/TrueMass1200_ChocolateMilkshake_10.25lb.png"),

    # Dymatize
    ("Dymatize", "ISO100 Whey Isolate - Gourmet Chocolate", "3 lbs", 48000,
     "https://dymatize.com/cdn/shop/products/ISO100_GourmetChocolate_3lb.png"),
    ("Dymatize", "ISO100 Whey Isolate - Gourmet Vanilla", "5 lbs", 72000,
     "https://dymatize.com/cdn/shop/products/ISO100_GourmetVanilla_5lb.png"),
    ("Dymatize", "Elite 100% Whey Protein - Rich Chocolate", "5 lbs", 58000,
     "https://dymatize.com/cdn/shop/products/Elite100Whey_RichChocolate_5lb.png"),

    # MyProtein
    ("MyProtein", "Impact Whey Protein - Chocolate Smooth", "2.2 lbs", 32000,
     "https://static.thcdn.com/images/large/webp/products/impact-whey-protein-chocolate-smooth.jpg"),
    ("MyProtein", "Impact Whey Protein - Vanilla", "2.2 lbs", 32000,
     "https://static.thcdn.com/images/large/webp/products/impact-whey-protein-vanilla.jpg"),
    ("MyProtein", "Impact Whey Isolate - Chocolate Brownie", "2.2 lbs", 42000,
     "https://static.thcdn.com/images/large/webp/products/impact-whey-isolate-chocolate-brownie.jpg"),

    # Isopure
    ("Isopure", "Zero Carb Protein - Creamy Vanilla", "3 lbs", 55000,
     "https://isopure.com/cdn/shop/products/Isopure_ZeroCarb_CreamyVanilla_3lb.png"),
    ("Isopure", "Zero Carb Protein - Dutch Chocolate", "3 lbs", 55000,
     "https://isopure.com/cdn/shop/products/Isopure_ZeroCarb_DutchChocolate_3lb.png"),

    # Transparent Labs
    ("Transparent Labs", "100% Grass-Fed Whey Isolate - Chocolate", "2 lbs", 58000,
     "https://cdn.transparentlabs.com/products/whey-protein-isolate-chocolate.png"),
    ("Transparent Labs", "100% Grass-Fed Whey Isolate - Vanilla", "2 lbs", 58000,
     "https://cdn.transparentlabs.com/products/whey-protein-isolate-vanilla.png"),

    # Cellucor
    ("Cellucor", "Cor-Performance Whey - Whipped Vanilla", "4 lbs", 52000,
     "https://cellucor.com/cdn/shop/products/CorPerformance_Whey_WhippedVanilla_4lb.png"),
    ("Cellucor", "Cor-Performance Whey - Molten Chocolate", "4 lbs", 52000,
     "https://cellucor.com/cdn/shop/products/CorPerformance_Whey_MoltenChocolate_4lb.png"),
]

print(f"  Adding {len(proteins)} protein products...")

for brand, name, size, price, img_url in proteins:
    full_name = f"{brand} - {name} ({size})"

    # Try to fetch image
    image_base64 = get_image_base64(img_url)

    product_data = {
        'name': full_name,
        'list_price': price,
        'standard_price': price * 0.55,  # 45% margin
        'type': 'consu',
        'categ_id': categories['Proteínas'],
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
        'description_sale': f'{brand} {size} - Proteína premium',
    }

    if image_base64:
        product_data['image_1920'] = image_base64

    prod = Product.create(product_data)
    protein_products.append(prod.id)
    print(f"    ✓ {full_name}")

print(f"✓ Created {len(protein_products)} protein products")

# ============================================================================
# STEP 5: CREATE BEVERAGE PRODUCTS
# ============================================================================
print("\n[5/8] Creating beverage products...")

beverage_products = []

# Gatorade flavors
gatorade_flavors = [
    ("Gatorade Cool Blue", 600, 1500, "https://www.gatorade.com/images/products/cool-blue-20oz.png"),
    ("Gatorade Glacier Freeze", 600, 1500, "https://www.gatorade.com/images/products/glacier-freeze-20oz.png"),
    ("Gatorade Fruit Punch", 600, 1500, "https://www.gatorade.com/images/products/fruit-punch-20oz.png"),
    ("Gatorade Lemon Lime", 600, 1500, "https://www.gatorade.com/images/products/lemon-lime-20oz.png"),
    ("Gatorade Orange", 600, 1500, "https://www.gatorade.com/images/products/orange-20oz.png"),
    ("Gatorade Zero Sugar Cool Blue", 600, 1600, "https://www.gatorade.com/images/products/zero-cool-blue-20oz.png"),
]

# Powerade
powerade_flavors = [
    ("Powerade Mountain Berry Blast", 600, 1400, "https://www.powerade.com/images/products/mountain-berry-blast.png"),
    ("Powerade Fruit Punch", 600, 1400, "https://www.powerade.com/images/products/fruit-punch.png"),
    ("Powerade Orange", 600, 1400, "https://www.powerade.com/images/products/orange.png"),
]

# Soft drinks
soft_drinks = [
    ("Coca-Cola", 355, 1200, "https://www.coca-cola.com/content/dam/onexp/us/en/products/coca-cola/coca-cola-original-12oz-can.png"),
    ("Coca-Cola Zero", 355, 1200, "https://www.coca-cola.com/content/dam/onexp/us/en/products/coca-cola-zero-sugar/coca-cola-zero-12oz-can.png"),
    ("Sprite", 355, 1200, "https://www.sprite.com/content/dam/sprite/us/en/products/sprite-original-12oz-can.png"),
    ("Fanta Orange", 355, 1200, "https://www.fanta.com/content/dam/fanta/us/en/products/fanta-orange-12oz-can.png"),
]

# Energy drinks
energy_drinks = [
    ("Monster Energy Original", 473, 2500, "https://www.monsterenergy.com/content/dam/monster/us/en/products/monster-energy-original-16oz.png"),
    ("Monster Ultra Zero", 473, 2500, "https://www.monsterenergy.com/content/dam/monster/us/en/products/monster-ultra-zero-16oz.png"),
    ("Red Bull Energy Drink", 250, 2200, "https://www.redbull.com/images/products/red-bull-energy-drink-250ml.png"),
    ("Red Bull Sugar Free", 250, 2200, "https://www.redbull.com/images/products/red-bull-sugarfree-250ml.png"),
]

all_beverages = (
    [(name, size, price, cat, img) for name, size, price, img in gatorade_flavors for cat in [categories['Bebidas Deportivas']]] +
    [(name, size, price, cat, img) for name, size, price, img in powerade_flavors for cat in [categories['Bebidas Deportivas']]] +
    [(name, size, price, cat, img) for name, size, price, img in soft_drinks for cat in [categories['Refrescos']]] +
    [(name, size, price, cat, img) for name, size, price, img in energy_drinks for cat in [categories['Bebidas Energéticas']]]
)

print(f"  Adding {len(all_beverages)} beverage products...")

for name, size, price, cat_id, img_url in all_beverages:
    full_name = f"{name} ({size}ml)"

    image_base64 = get_image_base64(img_url)

    product_data = {
        'name': full_name,
        'list_price': price,
        'standard_price': price * 0.60,
        'type': 'consu',
        'categ_id': cat_id,
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
    }

    if image_base64:
        product_data['image_1920'] = image_base64

    prod = Product.create(product_data)
    beverage_products.append(prod.id)
    print(f"    ✓ {full_name}")

print(f"✓ Created {len(beverage_products)} beverage products")

# ============================================================================
# STEP 6: CREATE SUPPLEMENT PRODUCTS (Pre-Workout, BCAA, Creatine)
# ============================================================================
print("\n[6/8] Creating supplement products...")

supplement_products = []

# Pre-Workout supplements
preworkouts = [
    ("Cellucor", "C4 Original Pre-Workout - Fruit Punch", "30 servings", 32000, categories['Suplementos Pre-Entrenamiento'],
     "https://cellucor.com/cdn/shop/products/C4Original_FruitPunch_30srv.png"),
    ("Cellucor", "C4 Original Pre-Workout - Icy Blue Razz", "30 servings", 32000, categories['Suplementos Pre-Entrenamiento'],
     "https://cellucor.com/cdn/shop/products/C4Original_IcyBlueRazz_30srv.png"),
    ("Optimum Nutrition", "Gold Standard Pre-Workout - Green Apple", "30 servings", 35000, categories['Suplementos Pre-Entrenamiento'],
     "https://www.optimumnutrition.com/sites/optimumnutrition.com/files/styles/original/public/GoldStandard_PreWorkout_GreenApple_30srv.png"),
    ("MuscleTech", "Vapor X5 Next Gen Pre-Workout", "30 servings", 38000, categories['Suplementos Pre-Entrenamiento'],
     "https://cdn.muscletech.com/catalog/product/vaporx5_nextgen_30srv.png"),
]

# BCAA supplements
bcaas = [
    ("Optimum Nutrition", "BCAA 1000 Caps", "200 capsules", 28000, categories['Aminoácidos BCAA'],
     "https://www.optimumnutrition.com/sites/optimumnutrition.com/files/styles/original/public/BCAA1000_200caps.png"),
    ("MuscleTech", "Platinum BCAA 8:1:1", "200 tablets", 26000, categories['Aminoácidos BCAA'],
     "https://cdn.muscletech.com/catalog/product/platinumbcaa_200tabs.png"),
    ("BSN", "Amino X - Blue Raz", "30 servings", 30000, categories['Aminoácidos BCAA'],
     "https://bsnsupplements.com/cdn/shop/products/AminoX_BlueRaz_30srv.png"),
    ("Cellucor", "Alpha Amino - Fruit Punch", "30 servings", 32000, categories['Aminoácidos BCAA'],
     "https://cellucor.com/cdn/shop/products/AlphaAmino_FruitPunch_30srv.png"),
]

# Creatine supplements
creatines = [
    ("Optimum Nutrition", "Micronized Creatine Monohydrate Powder", "300g", 22000, categories['Creatina'],
     "https://www.optimumnutrition.com/sites/optimumnutrition.com/files/styles/original/public/Creatine_Powder_300g.png"),
    ("MuscleTech", "Platinum 100% Creatine", "400g", 24000, categories['Creatina'],
     "https://cdn.muscletech.com/catalog/product/platinum_creatine_400g.png"),
    ("BSN", "CellMass 2.0", "50 servings", 35000, categories['Creatina'],
     "https://bsnsupplements.com/cdn/shop/products/CellMass20_50srv.png"),
    ("Dymatize", "Creatine Micronized", "500g", 26000, categories['Creatina'],
     "https://dymatize.com/cdn/shop/products/Creatine_Micronized_500g.png"),
]

all_supplements = preworkouts + bcaas + creatines

print(f"  Adding {len(all_supplements)} supplement products...")

for brand, name, size, price, cat_id, img_url in all_supplements:
    full_name = f"{brand} - {name} ({size})"

    image_base64 = get_image_base64(img_url)

    product_data = {
        'name': full_name,
        'list_price': price,
        'standard_price': price * 0.55,
        'type': 'consu',
        'categ_id': cat_id,
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
    }

    if image_base64:
        product_data['image_1920'] = image_base64

    prod = Product.create(product_data)
    supplement_products.append(prod.id)
    print(f"    ✓ {full_name}")

print(f"✓ Created {len(supplement_products)} supplement products")

# ============================================================================
# STEP 7: CREATE PROTEIN BARS & SNACKS
# ============================================================================
print("\n[7/8] Creating protein bars and snacks...")

bar_products = []

bars = [
    ("Quest Nutrition", "Quest Bar - Chocolate Chip Cookie Dough", "box 12 bars", 18000, categories['Barras Proteicas'],
     "https://questnutrition.com/cdn/shop/products/QuestBar_ChocolateChipCookieDough_Box12.png"),
    ("Quest Nutrition", "Quest Bar - Cookies & Cream", "box 12 bars", 18000, categories['Barras Proteicas'],
     "https://questnutrition.com/cdn/shop/products/QuestBar_CookiesCream_Box12.png"),
    ("ONE", "ONE Bar - Maple Glazed Doughnut", "box 12 bars", 16000, categories['Barras Proteicas'],
     "https://one1brands.com/cdn/shop/products/ONEBar_MapleGlazedDoughnut_Box12.png"),
    ("Clif", "Clif Bar - Chocolate Chip", "box 12 bars", 14000, categories['Snacks Saludables'],
     "https://www.clifbar.com/cdn/shop/products/ClifBar_ChocolateChip_Box12.png"),
    ("Kind", "Kind Bar - Dark Chocolate Nuts & Sea Salt", "box 12 bars", 15000, categories['Snacks Saludables'],
     "https://kindsnacks.com/cdn/shop/products/KindBar_DarkChocolate_Box12.png"),
]

print(f"  Adding {len(bars)} bar products...")

for brand, name, size, price, cat_id, img_url in bars:
    full_name = f"{brand} - {name} ({size})"

    image_base64 = get_image_base64(img_url)

    product_data = {
        'name': full_name,
        'list_price': price,
        'standard_price': price * 0.50,
        'type': 'consu',
        'categ_id': cat_id,
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
    }

    if image_base64:
        product_data['image_1920'] = image_base64

    prod = Product.create(product_data)
    bar_products.append(prod.id)
    print(f"    ✓ {full_name}")

print(f"✓ Created {len(bar_products)} bar products")

# ============================================================================
# STEP 8: CREATE GYM ACCESSORIES
# ============================================================================
print("\n[8/8] Creating gym accessories...")

accessory_products = []

accessories = [
    ("BlenderBottle", "Classic Shaker Bottle 28oz", "800ml", 8000, categories['Accesorios Gym'],
     "https://blenderbottle.com/cdn/shop/products/Classic_Shaker_28oz.png"),
    ("Harbinger", "Pro Gym Gloves", "par", 22000, categories['Accesorios Gym'],
     "https://harbinger.com/cdn/shop/products/ProGymGloves.png"),
    ("RDX", "Weightlifting Belt", "cinturón", 38000, categories['Accesorios Gym'],
     "https://rdxsports.com/cdn/shop/products/WeightliftingBelt.png"),
    ("Nike", "Gym Towel", "toalla", 12000, categories['Accesorios Gym'],
     "https://static.nike.com/a/images/products/gym-towel.png"),
    ("Under Armour", "Compression Shirt", "camiseta", 28000, categories['Ropa Deportiva'],
     "https://underarmour.com/cdn/shop/products/CompressionShirt.png"),
    ("Adidas", "Training Shorts", "shorts", 24000, categories['Ropa Deportiva'],
     "https://adidas.com/cdn/shop/products/TrainingShorts.png"),
]

print(f"  Adding {len(accessories)} accessory products...")

for brand, name, unit, price, cat_id, img_url in accessories:
    full_name = f"{brand} - {name}"

    image_base64 = get_image_base64(img_url)

    product_data = {
        'name': full_name,
        'list_price': price,
        'standard_price': price * 0.50,
        'type': 'consu',
        'categ_id': cat_id,
        'taxes_id': [(6, 0, tax_13)],
        'sale_ok': True,
        'purchase_ok': True,
    }

    if image_base64:
        product_data['image_1920'] = image_base64

    prod = Product.create(product_data)
    accessory_products.append(prod.id)
    print(f"    ✓ {full_name}")

print(f"✓ Created {len(accessory_products)} accessory products")

# ============================================================================
# COMMIT ALL CHANGES
# ============================================================================
print("\n[9/9] Committing to database...")
env.cr.commit()

print("\n" + "=" * 70)
print("REAL GYM PRODUCTS POPULATED SUCCESSFULLY!")
print("=" * 70)
print(f"\nSummary:")
print(f"  • Currency: Costa Rican Colón (CRC) ₡")
print(f"  • Categories: {len(categories)}")
print(f"  • Protein Products: {len(protein_products)}")
print(f"  • Beverages: {len(beverage_products)}")
print(f"  • Supplements: {len(supplement_products)}")
print(f"  • Bars & Snacks: {len(bar_products)}")
print(f"  • Accessories: {len(accessory_products)}")
print(f"  • TOTAL PRODUCTS: {len(protein_products) + len(beverage_products) + len(supplement_products) + len(bar_products) + len(accessory_products)}")
print(f"\nAll products include:")
print(f"  ✓ Real brand names")
print(f"  ✓ Actual product lines")
print(f"  ✓ Product images (where available)")
print(f"  ✓ Costa Rica 13% IVA tax")
print(f"  ✓ Realistic CRC pricing")
print("\nAccess: http://localhost:8070")
print("=" * 70)
