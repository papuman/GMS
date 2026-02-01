#!/usr/bin/env python3
"""Debug: Check invoice line tax data."""
try:
    company = env['res.company'].browse(1)
    invoice = env['account.move'].search([
        ('move_type', '=', 'out_invoice'),
        ('state', '=', 'posted'),
        ('company_id', '=', company.id),
    ], limit=1)
    print(f"Invoice: {invoice.name}")
    print(f"Amount untaxed: {invoice.amount_untaxed}")
    print(f"Amount tax: {invoice.amount_tax}")
    print(f"Amount total: {invoice.amount_total}")

    for line in invoice.invoice_line_ids:
        print(f"\n  Line: display_type={line.display_type}, name={line.name}")
        print(f"    quantity={line.quantity}, price_unit={line.price_unit}")
        print(f"    price_subtotal={line.price_subtotal}, price_total={line.price_total}")
        print(f"    tax_ids={line.tax_ids}")
        print(f"    tax_ids count={len(line.tax_ids)}")
        if line.tax_ids:
            for tax in line.tax_ids:
                print(f"      Tax: {tax.name}, amount={tax.amount}, type={tax.amount_type}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
