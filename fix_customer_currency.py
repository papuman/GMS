#!/usr/bin/env python3
"""Fix Customer Currency Settings"""

print("=" * 70)
print("FIXING CUSTOMER CURRENCY DEFAULTS")
print("=" * 70)

Currency = env['res.currency']
Partner = env['res.partner']
Company = env['res.company']

# Get CRC currency
crc = Currency.search([('name', '=', 'CRC')], limit=1)
print(f"\nCRC Currency ID: {crc.id}")
print(f"Company Currency: {env.user.company_id.currency_id.name}")

# Update all existing customers to use company currency (CRC)
all_partners = Partner.search([('is_company', '=', False)])
print(f"\nFound {len(all_partners)} customer records")

# Remove explicit currency from partners so they use company default
all_partners.write({'currency_id': False})
print(f"✓ Reset {len(all_partners)} customers to use company default currency")

# Verify
test_customer = Partner.search([('name', '=', 'Validation Test Customer')], limit=1)
if test_customer:
    # The property_product_pricelist should use company currency
    pricelist = test_customer.property_product_pricelist
    print(f"\nTest Customer Pricelist: {pricelist.name}")
    print(f"Pricelist Currency: {pricelist.currency_id.name}")

env.cr.commit()

print("\n" + "=" * 70)
print("CUSTOMER CURRENCY FIX COMPLETE")
print("=" * 70)
