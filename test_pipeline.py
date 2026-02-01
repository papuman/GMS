#!/usr/bin/env python3
"""
End-to-end test: Generate XML -> Sign -> Submit to Hacienda Sandbox.

Run inside container via odoo shell:
  cat /opt/test_pipeline.py | python3 /opt/odoo/odoo-bin shell -d GMS --config=/etc/odoo/odoo.conf --no-http
"""
import time
import traceback

print("=" * 70)
print("E-INVOICE PIPELINE TEST (Hacienda Sandbox)")
print("=" * 70)

try:
    company = env['res.company'].browse(1)
    print(f"\nCompany: {company.name}")
    print(f"VAT: {company.vat}")
    print(f"Environment: {company.l10n_cr_hacienda_env}")
    print(f"Certificate: {company.l10n_cr_certificate_filename}")
    print(f"Has username: {bool(company.l10n_cr_hacienda_username)}")
    print(f"Has password: {bool(company.l10n_cr_hacienda_password)}")

    # Step 0: Verify certificate loading
    print("\n--- STEP 0: Test Certificate Loading ---")
    cert_mgr = env['l10n_cr.certificate.manager']
    cert_obj, key_obj = cert_mgr.load_certificate_from_company(company)
    print(f"Certificate loaded: {type(cert_obj).__name__}")
    print(f"Private key loaded: {type(key_obj).__name__}")
    print(f"Cert subject: {cert_obj.subject}")
    print(f"Cert valid until: {cert_obj.not_valid_after}")

    # Find existing invoice
    invoice = env['account.move'].search([
        ('move_type', '=', 'out_invoice'),
        ('state', '=', 'posted'),
        ('company_id', '=', company.id),
    ], limit=1)

    if not invoice:
        print("\nERROR: No posted invoice found.")
        raise SystemExit(1)

    print(f"\nUsing invoice: {invoice.name} (ID={invoice.id})")
    print(f"Partner: {invoice.partner_id.name} (VAT: {invoice.partner_id.vat})")
    print(f"Amount: {invoice.amount_total} {invoice.currency_id.name}")

    # Create or reset e-invoice document
    print("\n--- Creating fresh e-invoice document ---")
    existing = env['l10n_cr.einvoice.document'].search([
        ('move_id', '=', invoice.id),
    ])
    if existing:
        print(f"Found {len(existing)} existing e-invoice doc(s), resetting first one...")
        doc = existing[0]
        doc.write({
            'state': 'draft',
            'xml_content': False,
            'signed_xml': False,
            'clave': False,
            'error_message': False,
        })
    else:
        doc = env['l10n_cr.einvoice.document'].create({
            'move_id': invoice.id,
            'company_id': company.id,
            'document_type': 'FE',
        })
    env.cr.commit()
    print(f"E-invoice doc ID: {doc.id}, state: {doc.state}")

    # Step 1: Generate XML
    print("\n--- STEP 1: Generate XML ---")
    try:
        doc.action_generate_xml()
        env.cr.commit()
        print(f"State: {doc.state}")
        print(f"Clave: {doc.clave}")
        if doc.xml_content:
            print(f"XML length: {len(doc.xml_content)} chars")
            print(f"XML preview:\n{doc.xml_content[:500]}...")
    except Exception as e:
        print(f"FAILED: {e}")
        traceback.print_exc()
        raise SystemExit(1)

    # Step 2: Sign XML
    print("\n--- STEP 2: Sign XML ---")
    try:
        doc.action_sign_xml()
        env.cr.commit()
        print(f"State: {doc.state}")
        if doc.signed_xml:
            print(f"Signed XML length: {len(doc.signed_xml)} chars")
            if '<ds:Signature' in doc.signed_xml or 'Signature' in doc.signed_xml:
                print("Signature element: PRESENT")
            else:
                print("WARNING: No Signature element found!")
            sig_start = doc.signed_xml.find('Signature')
            if sig_start >= 0:
                print(f"Signature snippet: ...{doc.signed_xml[sig_start:sig_start+200]}...")
    except Exception as e:
        print(f"FAILED: {e}")
        traceback.print_exc()
        raise SystemExit(1)

    # Step 3: Submit to Hacienda
    print("\n--- STEP 3: Submit to Hacienda Sandbox ---")
    submission_ok = False
    try:
        doc.action_submit_to_hacienda()
        env.cr.commit()
        print(f"State: {doc.state}")
        print(f"Hacienda response: {doc.hacienda_response}")
        print(f"Hacienda message: {doc.hacienda_message}")
        submission_ok = True
    except Exception as e:
        print(f"SUBMISSION ERROR: {e}")
        traceback.print_exc()
        env.cr.rollback()
        doc = env['l10n_cr.einvoice.document'].browse(doc.id)

    # Step 4: Wait and check status
    if doc.state == 'submitted':
        print("\n--- STEP 4: Check Status (waiting 10s for processing) ---")
        time.sleep(10)

        try:
            doc.action_check_status()
            env.cr.commit()
            print(f"Final state: {doc.state}")
            print(f"Hacienda response: {doc.hacienda_response}")
            print(f"Hacienda message: {doc.hacienda_message}")
            if doc.error_message:
                print(f"Error message: {doc.error_message}")
        except Exception as e:
            print(f"STATUS CHECK ERROR: {e}")
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"FINAL STATE: {doc.state}")
    if doc.state == 'accepted':
        print("SUCCESS! Invoice accepted by Hacienda sandbox!")
    elif doc.state == 'rejected':
        print(f"REJECTED: {doc.hacienda_message or doc.error_message}")
    elif doc.state == 'submitted':
        print("Still processing - check again later")
    else:
        print(f"Current state: {doc.state}, Error: {doc.error_message}")
    print("=" * 70)

except SystemExit:
    pass
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
    traceback.print_exc()
