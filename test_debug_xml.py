#!/usr/bin/env python3
"""Debug: Generate XML and dump it."""
try:
    company = env['res.company'].browse(1)
    doc = env['l10n_cr.einvoice.document'].search([
        ('company_id', '=', company.id),
    ], limit=1, order='id desc')
    doc.write({
        'state': 'draft',
        'xml_content': False,
        'signed_xml': False,
        'clave': False,
        'error_message': False,
    })
    env.cr.commit()
    doc.action_generate_xml()
    env.cr.commit()
    print("=== GENERATED XML ===")
    print(doc.xml_content)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
