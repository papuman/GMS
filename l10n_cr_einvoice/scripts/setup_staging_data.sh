#!/bin/bash

################################################################################
# GMS Staging Data Setup Script
# Version: 19.0.1.8.0
# Purpose: Populate staging environment with realistic test data
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker/docker-compose.staging.yml"
ENV_FILE="${PROJECT_ROOT}/docker/.env.staging"

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

echo -e "${BLUE}"
echo "=========================================================================="
echo "  Staging Data Setup - Populating Test Data"
echo "=========================================================================="
echo -e "${NC}"

# Create Python script for data population
cat > /tmp/setup_staging_data.py << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import odoorpc
import sys
from datetime import datetime, timedelta
import random

# Connection settings
HOST = 'localhost'
PORT = 8070
DATABASE = 'staging_gms'
USERNAME = 'admin'
PASSWORD = 'StagingAdmin2024!SecurePass'

def main():
    print("Connecting to Odoo...")
    try:
        odoo = odoorpc.ODOO(HOST, port=PORT)
        odoo.login(DATABASE, USERNAME, PASSWORD)
        print(f"Connected to {DATABASE} as {USERNAME}")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    # Configure company for Costa Rica
    print("\n1. Configuring company...")
    Company = odoo.env['res.company']
    company_id = odoo.env.user.company_id.id
    Company.write([company_id], {
        'country_id': odoo.env.ref('base.cr').id,
        'vat': '3-101-654321',
        'phone': '+506 2222-3333',
        'email': 'staging@gms-cr.com',
    })
    print("   Company configured for Costa Rica")

    # Create test customers
    print("\n2. Creating test customers...")
    Partner = odoo.env['res.partner']

    test_customers = [
        {
            'name': 'Juan Pérez Rodríguez',
            'vat': '1-0234-0567',
            'hacienda_id_type': '01',  # Física
            'email': 'juan.perez@test.cr',
            'phone': '+506 8888-1111',
            'customer_rank': 1,
        },
        {
            'name': 'María González Castro',
            'vat': '1-0345-0678',
            'hacienda_id_type': '01',
            'email': 'maria.gonzalez@test.cr',
            'phone': '+506 8888-2222',
            'customer_rank': 1,
        },
        {
            'name': 'Supermercado El Ahorro S.A.',
            'vat': '3-101-123456',
            'hacienda_id_type': '02',  # Jurídica
            'email': 'compras@superahorro.cr',
            'phone': '+506 2222-4444',
            'customer_rank': 1,
        },
        {
            'name': 'Restaurante La Cocina S.A.',
            'vat': '3-101-234567',
            'hacienda_id_type': '02',
            'email': 'admin@lacocina.cr',
            'phone': '+506 2222-5555',
            'customer_rank': 1,
        },
        {
            'name': 'Ferretería El Constructor Ltda.',
            'vat': '3-102-345678',
            'hacienda_id_type': '02',
            'email': 'ventas@elconstructor.cr',
            'phone': '+506 2222-6666',
            'customer_rank': 1,
        },
        {
            'name': 'Carlos Ramírez (DIMEX)',
            'vat': '123456789012',
            'hacienda_id_type': '03',  # DIMEX
            'email': 'carlos.ramirez@test.cr',
            'phone': '+506 8888-3333',
            'customer_rank': 1,
        },
        {
            'name': 'Tech Solutions NITE',
            'vat': '1234567890',
            'hacienda_id_type': '04',  # NITE
            'email': 'info@techsolutions.cr',
            'phone': '+506 2222-7777',
            'customer_rank': 1,
        },
        {
            'name': 'John Smith (Foreign)',
            'vat': 'PASSPORT-US-123456',
            'hacienda_id_type': '05',  # Extranjero
            'email': 'john.smith@test.com',
            'phone': '+1 555-1234',
            'customer_rank': 1,
        },
    ]

    customer_ids = []
    for customer_data in test_customers:
        customer_id = Partner.create(customer_data)
        customer_ids.append(customer_id)
        print(f"   Created: {customer_data['name']}")

    # Create test products
    print("\n3. Creating test products...")
    Product = odoo.env['product.product']

    test_products = [
        {'name': 'Membresía Mensual', 'list_price': 25000.00, 'type': 'service'},
        {'name': 'Membresía Trimestral', 'list_price': 65000.00, 'type': 'service'},
        {'name': 'Membresía Anual', 'list_price': 240000.00, 'type': 'service'},
        {'name': 'Clase Yoga Individual', 'list_price': 8000.00, 'type': 'service'},
        {'name': 'Clase Spinning', 'list_price': 6000.00, 'type': 'service'},
        {'name': 'Entrenamiento Personal (1 hora)', 'list_price': 15000.00, 'type': 'service'},
        {'name': 'Nutrición - Consulta', 'list_price': 20000.00, 'type': 'service'},
        {'name': 'Proteína Whey 2kg', 'list_price': 35000.00, 'type': 'consu'},
        {'name': 'Creatina Monohidrato 500g', 'list_price': 18000.00, 'type': 'consu'},
        {'name': 'BCAA 300g', 'list_price': 22000.00, 'type': 'consu'},
        {'name': 'Pre-Workout 300g', 'list_price': 25000.00, 'type': 'consu'},
        {'name': 'Toalla Deportiva', 'list_price': 5000.00, 'type': 'consu'},
        {'name': 'Botella de Agua 1L', 'list_price': 4000.00, 'type': 'consu'},
        {'name': 'Guantes de Entrenamiento', 'list_price': 8000.00, 'type': 'consu'},
        {'name': 'Banda Elástica Set', 'list_price': 12000.00, 'type': 'consu'},
        {'name': 'Camiseta Deportiva', 'list_price': 15000.00, 'type': 'consu'},
        {'name': 'Short Deportivo', 'list_price': 18000.00, 'type': 'consu'},
        {'name': 'Tenis Deportivos', 'list_price': 45000.00, 'type': 'consu'},
        {'name': 'Mochila Deportiva', 'list_price': 25000.00, 'type': 'consu'},
        {'name': 'Locker Mensual', 'list_price': 3000.00, 'type': 'service'},
    ]

    product_ids = []
    for product_data in test_products:
        product_id = Product.create(product_data)
        product_ids.append(product_id)
        print(f"   Created: {product_data['name']}")

    # Configure payment methods
    print("\n4. Verifying payment methods...")
    PaymentMethod = odoo.env['hacienda.payment.method']
    payment_methods = PaymentMethod.search([])
    print(f"   Found {len(payment_methods)} payment methods")

    # Create sample invoices
    print("\n5. Creating sample invoices...")
    Invoice = odoo.env['account.move']

    for i in range(10):
        customer_id = random.choice(customer_ids)
        invoice_lines = []

        # Add 1-3 random products
        num_lines = random.randint(1, 3)
        for _ in range(num_lines):
            product_id = random.choice(product_ids)
            product = Product.browse(product_id)
            quantity = random.randint(1, 3)

            invoice_lines.append((0, 0, {
                'product_id': product_id,
                'quantity': quantity,
                'price_unit': product.list_price,
            }))

        invoice_data = {
            'partner_id': customer_id,
            'move_type': 'out_invoice',
            'invoice_date': datetime.now().date(),
            'invoice_line_ids': invoice_lines,
        }

        invoice_id = Invoice.create(invoice_data)
        print(f"   Created invoice #{i+1}")

    print("\n6. Setup complete!")
    print(f"   - Created {len(customer_ids)} test customers")
    print(f"   - Created {len(product_ids)} test products")
    print(f"   - Created 10 sample invoices")
    print("\nStaging data populated successfully!")

if __name__ == '__main__':
    main()
PYTHON_SCRIPT

log "Installing OdooRPC library..."
pip3 install -q odoorpc

log "Populating staging database with test data..."
python3 /tmp/setup_staging_data.py

log "Cleaning up..."
rm /tmp/setup_staging_data.py

echo ""
echo -e "${GREEN}=========================================================================="
echo "  Staging Data Setup Complete!"
echo -e "==========================================================================${NC}"
echo ""
echo "Test data created:"
echo "  - 8 test customers (various ID types)"
echo "  - 20 test products (services and consumables)"
echo "  - 10 sample invoices"
echo ""
echo "You can now:"
echo "  1. Login to http://localhost:8070"
echo "  2. Go to Accounting > Customers > Invoices"
echo "  3. Test e-invoice generation and submission"
echo ""
