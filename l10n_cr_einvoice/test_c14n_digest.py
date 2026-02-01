#!/usr/bin/env python3
"""Test C14N digest stability before/after signature append."""
from lxml import etree
import hashlib
import base64

xml_content = b'''<?xml version="1.0" encoding="utf-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Clave>50631012600310123456700100001010000000004755507373</Clave>
  <CodigoActividad>9312</CodigoActividad>
</FacturaElectronica>'''

root = etree.fromstring(xml_content)

# C14N digest BEFORE signature
c14n_before = etree.tostring(root, method='c14n', exclusive=True, with_comments=False)
digest_before = base64.b64encode(hashlib.sha256(c14n_before).digest()).decode()
print("=== BEFORE appending signature ===")
print("C14N (len=%d):" % len(c14n_before))
print(c14n_before.decode())
print("Digest: %s" % digest_before)

# Now add a ds:Signature element (simulating our signer)
ds = 'http://www.w3.org/2000/09/xmldsig#'
sig = etree.Element('{%s}Signature' % ds, nsmap={'ds': ds}, Id='test-sig')
etree.SubElement(sig, '{%s}SignedInfo' % ds)
root.append(sig)

# Serialize with tostring (what we send to Hacienda)
final_xml = etree.tostring(root, encoding='utf-8', xml_declaration=True)
print("\n=== FINAL XML (what gets sent) ===")
print(final_xml.decode()[:500])

# Re-parse (simulating what Hacienda does)
root2 = etree.fromstring(final_xml)

# C14N of full tree with signature
c14n_full = etree.tostring(root2, method='c14n', exclusive=True, with_comments=False)
print("\n=== C14N of FULL tree (with sig) ===")
print("len=%d" % len(c14n_full))
print(c14n_full.decode()[:500])

# Remove signature and check if digest matches
for child in list(root2):
    if isinstance(child.tag, str) and 'Signature' in child.tag:
        root2.remove(child)
        break

c14n_after_remove = etree.tostring(root2, method='c14n', exclusive=True, with_comments=False)
digest_after = base64.b64encode(hashlib.sha256(c14n_after_remove).digest()).decode()
print("\n=== AFTER removing signature from re-parsed tree ===")
print("C14N (len=%d):" % len(c14n_after_remove))
print(c14n_after_remove.decode())
print("Digest: %s" % digest_after)

print("\n=== COMPARISON ===")
print("Before: %s" % digest_before)
print("After:  %s" % digest_after)
print("Match:  %s" % (digest_before == digest_after))

if c14n_before != c14n_after_remove:
    print("\nDIFFERENCE FOUND!")
    # Show byte-by-byte diff
    for i, (a, b) in enumerate(zip(c14n_before, c14n_after_remove)):
        if a != b:
            print("  First diff at byte %d: %r vs %r" % (i, chr(a), chr(b)))
            print("  Context before: ...%s..." % c14n_before[max(0,i-20):i+20].decode())
            print("  Context after:  ...%s..." % c14n_after_remove[max(0,i-20):i+20].decode())
            break
    if len(c14n_before) != len(c14n_after_remove):
        print("  Length diff: %d vs %d" % (len(c14n_before), len(c14n_after_remove)))
