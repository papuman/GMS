#!/usr/bin/env python3
"""Fix Default Pricelist to Use CRC Currency"""

print("=" * 70)
print("FIXING PRICELIST CURRENCY")
print("=" * 70)

Currency = env['res.currency']
Pricelist = env['product.pricelist']

# Get CRC currency
crc = Currency.search([('name', '=', 'CRC')], limit=1)
print(f"\nCRC Currency ID: {crc.id}")

# Get all pricelists
pricelists = Pricelist.search([])
print(f"Found {len(pricelists)} pricelists")

for pl in pricelists:
    old_currency = pl.currency_id.name
    if old_currency != 'CRC':
        pl.write({'currency_id': crc.id})
        print(f"  ✓ Updated '{pl.name}' from {old_currency} to CRC")
    else:
        print(f"  • '{pl.name}' already using CRC")

# Verify default pricelist
default_pl = Pricelist.search([('name', '=', 'Default')], limit=1) or Pricelist.search([], limit=1)
print(f"\nDefault Pricelist: {default_pl.name}")
print(f"Default Pricelist Currency: {default_pl.currency_id.name}")

env.cr.commit()

print("\n" + "=" * 70)
print("PRICELIST CURRENCY FIX COMPLETE")
print("=" * 70)
