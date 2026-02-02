#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 Verification Test
Tests certificate loading and XML signing with actual sandbox credentials
"""

import sys
import os
import base64
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_phase2_components():
    """Test Phase 2: Certificate Management and XML Signing"""

    print("=" * 70)
    print("PHASE 2 VERIFICATION TEST")
    print("=" * 70)

    results = {
        'passed': [],
        'failed': [],
    }

    # Test 1: Load certificate with PIN
    print("\n[TEST 1] Loading certificate with sandbox PIN...")
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography.hazmat.backends import default_backend

        cert_path = Path("docs/Tribu-CR/certificado.p12")
        if not cert_path.exists():
            raise FileNotFoundError(f"Certificate not found at {cert_path}")

        with open(cert_path, 'rb') as f:
            p12_data = f.read()

        # PIN from Credentials.md
        pin = "5147"

        # Load certificate
        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            p12_data,
            pin.encode('utf-8'),
            backend=default_backend()
        )

        if not certificate:
            raise ValueError("No certificate found in P12 file")
        if not private_key:
            raise ValueError("No private key found in P12 file")

        # Get certificate details
        subject = certificate.subject
        issuer = certificate.issuer
        not_before = certificate.not_valid_before_utc
        not_after = certificate.not_valid_after_utc

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        days_until_expiry = (not_after - now).days

        print(f"  ✓ Certificate loaded successfully")
        print(f"  ✓ Subject: {subject.rfc4514_string()}")
        print(f"  ✓ Issuer: {issuer.rfc4514_string()}")
        print(f"  ✓ Valid from: {not_before}")
        print(f"  ✓ Valid until: {not_after}")
        print(f"  ✓ Days until expiry: {days_until_expiry}")

        if days_until_expiry < 0:
            raise ValueError("Certificate has expired!")

        results['passed'].append("Certificate Loading")

    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
        results['failed'].append(f"Certificate Loading: {str(e)}")
        return results

    # Test 2: Generate sample XML
    print("\n[TEST 2] Generating sample e-invoice XML...")
    try:
        from lxml import etree

        # Create sample invoice XML (simplified v4.4 structure)
        NS = 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica'

        root = etree.Element(
            '{%s}FacturaElectronica' % NS,
            nsmap={'fe': NS},
        )

        # Add Clave (50-digit key)
        clave = etree.SubElement(root, '{%s}Clave' % NS)
        clave.text = '50601012025020100111111111111111111111111111111111'

        # Add NumeroConsecutivo
        num_cons = etree.SubElement(root, '{%s}NumeroConsecutivo' % NS)
        num_cons.text = '00100001010000000001'

        # Add FechaEmision
        fecha = etree.SubElement(root, '{%s}FechaEmision' % NS)
        fecha.text = '2025-02-01T10:00:00-06:00'

        # Add Emisor
        emisor = etree.SubElement(root, '{%s}Emisor' % NS)
        nombre_e = etree.SubElement(emisor, '{%s}Nombre' % NS)
        nombre_e.text = 'Test Company'
        id_e = etree.SubElement(emisor, '{%s}Identificacion' % NS)
        tipo_e = etree.SubElement(id_e, '{%s}Tipo' % NS)
        tipo_e.text = '02'
        num_e = etree.SubElement(id_e, '{%s}Numero' % NS)
        num_e.text = '3101234567'

        # Add Receptor
        receptor = etree.SubElement(root, '{%s}Receptor' % NS)
        nombre_r = etree.SubElement(receptor, '{%s}Nombre' % NS)
        nombre_r.text = 'Test Customer'
        id_r = etree.SubElement(receptor, '{%s}Identificacion' % NS)
        tipo_r = etree.SubElement(id_r, '{%s}Tipo' % NS)
        tipo_r.text = '01'
        num_r = etree.SubElement(id_r, '{%s}Numero' % NS)
        num_r.text = '101234567'

        # Add ResumenFactura
        resumen = etree.SubElement(root, '{%s}ResumenFactura' % NS)
        total_venta = etree.SubElement(resumen, '{%s}TotalVenta' % NS)
        total_venta.text = '10000.00'
        total_neto = etree.SubElement(resumen, '{%s}TotalVentaNeta' % NS)
        total_neto.text = '10000.00'
        total_impuesto = etree.SubElement(resumen, '{%s}TotalImpuesto' % NS)
        total_impuesto.text = '1300.00'
        total_comprobante = etree.SubElement(resumen, '{%s}TotalComprobante' % NS)
        total_comprobante.text = '11300.00'

        xml_content = etree.tostring(
            root,
            encoding='UTF-8',
            xml_declaration=True,
            pretty_print=True
        ).decode('utf-8')

        print(f"  ✓ Sample XML generated ({len(xml_content)} bytes)")
        results['passed'].append("XML Generation")

    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
        results['failed'].append(f"XML Generation: {str(e)}")
        return results

    # Test 3: Sign XML with XAdES-EPES
    print("\n[TEST 3] Signing XML with XAdES-EPES...")
    try:
        from lxml import etree
        import hashlib
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        import uuid
        from datetime import datetime

        # Parse XML
        parser = etree.XMLParser(remove_blank_text=True)
        doc_root = etree.fromstring(xml_content.encode('utf-8'), parser)

        # Generate unique IDs
        uid = uuid.uuid4().hex[:32]
        sig_id = 'Signature-' + uid
        sig_value_id = 'SignatureValue-' + uid
        ref_id = 'Reference-' + uid
        key_info_id = 'KeyInfo-' + uid
        xades_sp_id = 'SignedProperties-' + uid

        DS_NS = 'http://www.w3.org/2000/09/xmldsig#'
        XADES_NS = 'http://uri.etsi.org/01903/v1.3.2#'
        C14N_EXCL = 'http://www.w3.org/2001/10/xml-exc-c14n#'
        SIG_RSA_SHA256 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
        DIGEST_SHA256 = 'http://www.w3.org/2001/04/xmlenc#sha256'
        ENVELOPED_SIG = 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
        SIGNED_PROPS_TYPE = 'http://uri.etsi.org/01903#SignedProperties'

        # Helper function for C14N digest
        def c14n_digest(element):
            canonical = etree.tostring(
                element, method='c14n', exclusive=True, with_comments=False
            )
            return base64.b64encode(hashlib.sha256(canonical).digest()).decode('utf-8')

        # Compute document digest
        doc_digest = c14n_digest(doc_root)

        # Build KeyInfo
        key_info = etree.Element('{%s}KeyInfo' % DS_NS, nsmap={'ds': DS_NS}, Id=key_info_id)
        x509_data = etree.SubElement(key_info, '{%s}X509Data' % DS_NS)
        cert_der = certificate.public_bytes(serialization.Encoding.DER)
        x509_cert = etree.SubElement(x509_data, '{%s}X509Certificate' % DS_NS)
        x509_cert.text = base64.b64encode(cert_der).decode('utf-8')
        key_info_digest = c14n_digest(key_info)

        # Build SignedProperties (simplified)
        qp = etree.Element(
            '{%s}QualifyingProperties' % XADES_NS,
            nsmap={'xades': XADES_NS, 'ds': DS_NS},
            Target='#' + sig_id
        )
        sp = etree.SubElement(qp, '{%s}SignedProperties' % XADES_NS, Id=xades_sp_id)
        ssp = etree.SubElement(sp, '{%s}SignedSignatureProperties' % XADES_NS)
        st = etree.SubElement(ssp, '{%s}SigningTime' % XADES_NS)
        st.text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        signed_props_digest = c14n_digest(sp)

        # Build SignedInfo with three references
        signed_info = etree.Element('{%s}SignedInfo' % DS_NS, nsmap={'ds': DS_NS})
        etree.SubElement(signed_info, '{%s}CanonicalizationMethod' % DS_NS, Algorithm=C14N_EXCL)
        etree.SubElement(signed_info, '{%s}SignatureMethod' % DS_NS, Algorithm=SIG_RSA_SHA256)

        # Reference 1: Document
        ref1 = etree.SubElement(signed_info, '{%s}Reference' % DS_NS, Id=ref_id, URI='')
        transforms1 = etree.SubElement(ref1, '{%s}Transforms' % DS_NS)
        etree.SubElement(transforms1, '{%s}Transform' % DS_NS, Algorithm=ENVELOPED_SIG)
        etree.SubElement(transforms1, '{%s}Transform' % DS_NS, Algorithm=C14N_EXCL)
        etree.SubElement(ref1, '{%s}DigestMethod' % DS_NS, Algorithm=DIGEST_SHA256)
        dv1 = etree.SubElement(ref1, '{%s}DigestValue' % DS_NS)
        dv1.text = doc_digest

        # Reference 2: KeyInfo
        ref2 = etree.SubElement(signed_info, '{%s}Reference' % DS_NS, URI='#' + key_info_id)
        transforms2 = etree.SubElement(ref2, '{%s}Transforms' % DS_NS)
        etree.SubElement(transforms2, '{%s}Transform' % DS_NS, Algorithm=C14N_EXCL)
        etree.SubElement(ref2, '{%s}DigestMethod' % DS_NS, Algorithm=DIGEST_SHA256)
        dv2 = etree.SubElement(ref2, '{%s}DigestValue' % DS_NS)
        dv2.text = key_info_digest

        # Reference 3: SignedProperties
        ref3 = etree.SubElement(
            signed_info, '{%s}Reference' % DS_NS,
            Type=SIGNED_PROPS_TYPE, URI='#' + xades_sp_id
        )
        transforms3 = etree.SubElement(ref3, '{%s}Transforms' % DS_NS)
        etree.SubElement(transforms3, '{%s}Transform' % DS_NS, Algorithm=C14N_EXCL)
        etree.SubElement(ref3, '{%s}DigestMethod' % DS_NS, Algorithm=DIGEST_SHA256)
        dv3 = etree.SubElement(ref3, '{%s}DigestValue' % DS_NS)
        dv3.text = signed_props_digest

        # Sign SignedInfo
        canonical_si = etree.tostring(
            signed_info, method='c14n', exclusive=True, with_comments=False
        )
        sig_bytes = private_key.sign(canonical_si, padding.PKCS1v15(), hashes.SHA256())
        sig_value = base64.b64encode(sig_bytes).decode('utf-8')

        # Build complete Signature element
        signature = etree.Element('{%s}Signature' % DS_NS, nsmap={'ds': DS_NS}, Id=sig_id)
        signature.append(signed_info)

        sig_value_elem = etree.SubElement(signature, '{%s}SignatureValue' % DS_NS, Id=sig_value_id)
        sig_value_elem.text = sig_value

        signature.append(key_info)

        obj = etree.SubElement(signature, '{%s}Object' % DS_NS)
        obj.append(qp)

        # Append signature to document
        doc_root.append(signature)

        signed_xml = etree.tostring(
            doc_root,
            encoding='UTF-8',
            xml_declaration=True,
        ).decode('utf-8')

        print(f"  ✓ XML signed successfully")
        print(f"  ✓ Signature ID: {sig_id}")
        print(f"  ✓ Document digest: {doc_digest[:32]}...")
        print(f"  ✓ KeyInfo digest: {key_info_digest[:32]}...")
        print(f"  ✓ SignedProperties digest: {signed_props_digest[:32]}...")
        print(f"  ✓ Signed XML size: {len(signed_xml)} bytes")

        # Verify signature element exists
        parser = etree.XMLParser(remove_blank_text=True)
        verify_root = etree.fromstring(signed_xml.encode('utf-8'), parser)
        sig_elem = verify_root.find('.//{%s}Signature' % DS_NS)

        if sig_elem is None:
            raise ValueError("Signature element not found in signed XML")

        print(f"  ✓ Signature element verified in output")

        # Save signed XML for inspection
        output_file = "test_signed_invoice.xml"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(signed_xml)
        print(f"  ✓ Signed XML saved to: {output_file}")

        results['passed'].append("XML Signing")

    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        results['failed'].append(f"XML Signing: {str(e)}")
        return results

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✓ Passed: {len(results['passed'])}")
    for test in results['passed']:
        print(f"  - {test}")

    if results['failed']:
        print(f"\n✗ Failed: {len(results['failed'])}")
        for test in results['failed']:
            print(f"  - {test}")

    print("\n" + "=" * 70)

    if not results['failed']:
        print("🎉 PHASE 2: ALL TESTS PASSED")
        print("=" * 70)
        return True
    else:
        print("❌ PHASE 2: SOME TESTS FAILED")
        print("=" * 70)
        return False


if __name__ == '__main__':
    success = test_phase2_components()
    sys.exit(0 if success else 1)
