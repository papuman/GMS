#!/usr/bin/env python3
"""Debug: Extract signed XML and verify C14N digests manually."""
import time
import traceback
import base64
import hashlib
from lxml import etree

print("=" * 70)
print("SIGNATURE DIAGNOSTIC")
print("=" * 70)

try:
    company = env['res.company'].browse(1)

    # Find the latest e-invoice doc
    doc = env['l10n_cr.einvoice.document'].search([
        ('company_id', '=', company.id),
    ], limit=1, order='id desc')

    if not doc:
        print("No e-invoice doc found")
        raise SystemExit(1)

    print(f"Doc ID: {doc.id}, State: {doc.state}")

    # Reset and re-generate fresh
    doc.write({
        'state': 'draft',
        'xml_content': False,
        'signed_xml': False,
        'clave': False,
        'error_message': False,
    })
    env.cr.commit()

    # Generate XML
    doc.action_generate_xml()
    env.cr.commit()
    print(f"Generated XML, clave: {doc.clave}")

    # Get the raw XML before signing
    raw_xml = doc.xml_content
    print(f"\n--- RAW XML (first 300 chars) ---")
    print(raw_xml[:300])

    # Parse it the same way the signer does
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(raw_xml.encode('utf-8'), parser)

    # Compute C14N of the parsed root (what signer computes for document digest)
    c14n_before = etree.tostring(root, method='c14n', exclusive=True, with_comments=False)
    digest_before = base64.b64encode(hashlib.sha256(c14n_before).digest()).decode()
    print(f"\n--- C14N of root BEFORE signing ---")
    print(f"Length: {len(c14n_before)}")
    print(f"First 300 chars: {c14n_before[:300].decode()}")
    print(f"Digest: {digest_before}")

    # Now sign it
    doc.action_sign_xml()
    env.cr.commit()
    print(f"\n--- SIGNING DONE, state: {doc.state} ---")

    signed_xml = doc.signed_xml
    print(f"Signed XML length: {len(signed_xml)}")

    # Parse the signed XML
    signed_root = etree.fromstring(signed_xml.encode('utf-8'), parser)

    # Show the Signature element structure
    ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
    sig = signed_root.find('.//ds:Signature', ns)
    if sig is not None:
        print(f"\n--- SIGNATURE STRUCTURE ---")
        print(f"Signature Id: {sig.get('Id')}")

        # Show transforms on the document reference
        refs = sig.findall('.//ds:Reference', ns)
        for ref in refs:
            uri = ref.get('URI', '')
            ref_type = ref.get('Type', '')
            ref_id = ref.get('Id', '')
            transforms = ref.findall('.//ds:Transform', ns)
            algos = [t.get('Algorithm') for t in transforms]
            dv = ref.find('ds:DigestValue', ns)
            digest_val = dv.text if dv is not None else 'N/A'
            print(f"\n  Reference URI='{uri}' Type='{ref_type}' Id='{ref_id}'")
            print(f"    Transforms: {algos}")
            print(f"    DigestValue: {digest_val}")

        # Now simulate what Hacienda does: remove Signature and C14N
        print(f"\n--- SIMULATING HACIENDA VERIFICATION ---")

        # Method 1: Remove signature from parsed signed XML
        sig_elem = signed_root.find('{http://www.w3.org/2000/09/xmldsig#}Signature')
        if sig_elem is not None:
            signed_root.remove(sig_elem)
            c14n_after = etree.tostring(signed_root, method='c14n', exclusive=True, with_comments=False)
            digest_after = base64.b64encode(hashlib.sha256(c14n_after).digest()).decode()
            print(f"C14N after removing signature: length={len(c14n_after)}")
            print(f"First 300 chars: {c14n_after[:300].decode()}")
            print(f"Digest: {digest_after}")
            print(f"\nDIGEST MATCH: {digest_before == digest_after}")

            if c14n_before != c14n_after:
                print("\nDIFFERENCE FOUND!")
                # Compare bytes
                min_len = min(len(c14n_before), len(c14n_after))
                for i in range(min_len):
                    if c14n_before[i] != c14n_after[i]:
                        context_start = max(0, i - 50)
                        context_end = min(min_len, i + 50)
                        print(f"  First diff at byte {i}:")
                        print(f"  Before: ...{c14n_before[context_start:context_end].decode('utf-8', errors='replace')}...")
                        print(f"  After:  ...{c14n_after[context_start:context_end].decode('utf-8', errors='replace')}...")
                        break
                if len(c14n_before) != len(c14n_after):
                    print(f"  Length: before={len(c14n_before)}, after={len(c14n_after)}")
                    # Show the tail difference
                    if len(c14n_before) < len(c14n_after):
                        print(f"  Extra in after: {c14n_after[len(c14n_before):].decode('utf-8', errors='replace')}")
                    else:
                        print(f"  Extra in before: {c14n_before[len(c14n_after):].decode('utf-8', errors='replace')}")
    else:
        print("ERROR: No Signature element found in signed XML!")

    # Also dump the nsmap of root in both cases
    print(f"\n--- NAMESPACE MAPS ---")
    root2 = etree.fromstring(raw_xml.encode('utf-8'), parser)
    print(f"Root nsmap (raw): {root2.nsmap}")

    root3 = etree.fromstring(signed_xml.encode('utf-8'), parser)
    print(f"Root nsmap (signed): {root3.nsmap}")

    sig3 = root3.find('{http://www.w3.org/2000/09/xmldsig#}Signature')
    if sig3 is not None:
        root3.remove(sig3)
    print(f"Root nsmap (after sig removal): {root3.nsmap}")

except SystemExit:
    pass
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
    traceback.print_exc()
