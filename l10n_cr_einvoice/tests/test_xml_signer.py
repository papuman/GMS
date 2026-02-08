# -*- coding: utf-8 -*-
"""
Comprehensive Unit Tests for XML Digital Signer (Phase 7)

Tests XAdES-EPES digital signature generation for Costa Rica e-invoicing.
Covers signature structure, certificate validation, canonicalization,
and error handling.

Priority: P0 CRITICAL - Digital signatures legally required for Hacienda compliance
"""
import base64
import hashlib
import re
from datetime import datetime, timedelta
from lxml import etree
from unittest.mock import Mock, patch

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


# Test XML document (minimal valid e-invoice)
SAMPLE_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica"
                     xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Clave>50601012300001010011200001010000000000111111111111</Clave>
  <NumeroConsecutivo>00100001000000001011</NumeroConsecutivo>
  <FechaEmision>2023-01-01T12:00:00-06:00</FechaEmision>
  <Emisor>
    <Nombre>Test Company SA</Nombre>
    <Identificacion>
      <Tipo>02</Tipo>
      <Numero>3101234567</Numero>
    </Identificacion>
  </Emisor>
  <Receptor>
    <Nombre>Test Customer</Nombre>
    <Identificacion>
      <Tipo>01</Tipo>
      <Numero>109876543</Numero>
    </Identificacion>
  </Receptor>
  <ResumenFactura>
    <TotalVenta>100.00</TotalVenta>
    <TotalNeto>100.00</TotalNeto>
  </ResumenFactura>
</FacturaElectronica>
'''


@tagged('post_install', '-at_install', 'unit', 'p0', 'l10n_cr_einvoice')
class TestXMLSignerBasic(TransactionCase):
    """Test basic XML signing functionality (P0 Critical)."""

    def setUp(self):
        super(TestXMLSignerBasic, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']

        # Generate test certificate and private key
        self._create_test_certificate()

    def _create_test_certificate(self):
        """Create a valid test certificate for signing."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "San Jose"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Company SA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "test.company.cr"),
        ])

        self.valid_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    def test_sign_valid_xml_success(self):
        """P0: Sign valid XML document successfully."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        # Verify signed XML is not empty
        self.assertTrue(signed_xml)
        self.assertIsInstance(signed_xml, str)

        # Verify it's valid XML
        root = etree.fromstring(signed_xml.encode('utf-8'))
        self.assertIsNotNone(root)

    def test_signature_element_present(self):
        """P0: Signature element is appended to XML."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))

        # Find Signature element
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signature = root.find('.//ds:Signature', namespaces=ns)

        self.assertIsNotNone(signature, "Signature element not found")
        self.assertTrue('Id' in signature.attrib, "Signature missing Id attribute")

    def test_signature_has_required_children(self):
        """P0: Signature contains SignedInfo, SignatureValue, KeyInfo, Object."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signature = root.find('.//ds:Signature', namespaces=ns)

        # Check required children
        signed_info = signature.find('ds:SignedInfo', namespaces=ns)
        self.assertIsNotNone(signed_info, "SignedInfo missing")

        signature_value = signature.find('ds:SignatureValue', namespaces=ns)
        self.assertIsNotNone(signature_value, "SignatureValue missing")
        self.assertTrue(signature_value.text, "SignatureValue empty")

        key_info = signature.find('ds:KeyInfo', namespaces=ns)
        self.assertIsNotNone(key_info, "KeyInfo missing")

        obj = signature.find('ds:Object', namespaces=ns)
        self.assertIsNotNone(obj, "Object missing")

    def test_signature_value_is_base64(self):
        """P0: SignatureValue contains valid base64 data."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signature = root.find('.//ds:Signature', namespaces=ns)
        signature_value = signature.find('ds:SignatureValue', namespaces=ns)

        # Verify it's valid base64
        try:
            decoded = base64.b64decode(signature_value.text)
            self.assertTrue(len(decoded) > 0, "Decoded signature is empty")
            # RSA-2048 signature should be 256 bytes
            self.assertEqual(len(decoded), 256, "Unexpected signature length")
        except Exception as e:
            self.fail(f"SignatureValue is not valid base64: {e}")


@tagged('post_install', '-at_install', 'unit', 'p0', 'l10n_cr_einvoice')
class TestXMLSignerSignedInfo(TransactionCase):
    """Test SignedInfo structure with 3 references (P0 Critical)."""

    def setUp(self):
        super(TestXMLSignerSignedInfo, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']
        self._create_test_certificate()

    def _create_test_certificate(self):
        """Create a valid test certificate."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Company SA"),
        ])
        self.valid_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(issuer).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    def test_signed_info_has_three_references(self):
        """P0: SignedInfo contains exactly 3 references (document, KeyInfo, SignedProperties)."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signed_info = root.find('.//ds:SignedInfo', namespaces=ns)

        references = signed_info.findall('ds:Reference', namespaces=ns)
        self.assertEqual(len(references), 3, "SignedInfo must have exactly 3 references")

    def test_reference_1_document_enveloped_signature(self):
        """P0: Reference 1 targets document with enveloped-signature transform."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signed_info = root.find('.//ds:SignedInfo', namespaces=ns)
        references = signed_info.findall('ds:Reference', namespaces=ns)

        # Reference 1 should have URI="" (document)
        ref1 = references[0]
        self.assertEqual(ref1.get('URI'), '', "Reference 1 should target document (URI='')")

        # Check transforms
        transforms = ref1.find('ds:Transforms', namespaces=ns)
        transform_list = transforms.findall('ds:Transform', namespaces=ns)

        # Should have 2 transforms: enveloped-signature + C14N
        self.assertEqual(len(transform_list), 2, "Reference 1 should have 2 transforms")

        # First transform: enveloped-signature
        self.assertEqual(
            transform_list[0].get('Algorithm'),
            'http://www.w3.org/2000/09/xmldsig#enveloped-signature',
            "First transform must be enveloped-signature"
        )

        # Second transform: C14N exclusive
        self.assertEqual(
            transform_list[1].get('Algorithm'),
            'http://www.w3.org/2001/10/xml-exc-c14n#',
            "Second transform must be exclusive C14N"
        )

    def test_reference_2_keyinfo(self):
        """P0: Reference 2 targets KeyInfo with fragment URI."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signed_info = root.find('.//ds:SignedInfo', namespaces=ns)
        references = signed_info.findall('ds:Reference', namespaces=ns)

        # Reference 2 targets KeyInfo
        ref2 = references[1]
        uri = ref2.get('URI')
        self.assertTrue(uri.startswith('#KeyInfo-'), "Reference 2 should target KeyInfo with #KeyInfo- prefix")

        # Should have 1 transform: C14N
        transforms = ref2.find('ds:Transforms', namespaces=ns)
        transform_list = transforms.findall('ds:Transform', namespaces=ns)
        self.assertEqual(len(transform_list), 1, "Reference 2 should have 1 transform")
        self.assertEqual(
            transform_list[0].get('Algorithm'),
            'http://www.w3.org/2001/10/xml-exc-c14n#',
            "KeyInfo reference must use exclusive C14N"
        )

    def test_reference_3_signed_properties(self):
        """P0: Reference 3 targets SignedProperties with Type attribute (XAdES)."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signed_info = root.find('.//ds:SignedInfo', namespaces=ns)
        references = signed_info.findall('ds:Reference', namespaces=ns)

        # Reference 3 targets SignedProperties
        ref3 = references[2]
        uri = ref3.get('URI')
        self.assertTrue(uri.startswith('#SignedProperties-'),
                       "Reference 3 should target SignedProperties")

        # Must have Type attribute for XAdES
        ref_type = ref3.get('Type')
        self.assertEqual(
            ref_type,
            'http://uri.etsi.org/01903#SignedProperties',
            "Reference 3 must have SignedProperties Type attribute"
        )

    def test_canonicalization_method_exclusive_c14n(self):
        """P0: SignedInfo uses exclusive C14N canonicalization."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signed_info = root.find('.//ds:SignedInfo', namespaces=ns)

        c14n_method = signed_info.find('ds:CanonicalizationMethod', namespaces=ns)
        self.assertIsNotNone(c14n_method, "CanonicalizationMethod missing")
        self.assertEqual(
            c14n_method.get('Algorithm'),
            'http://www.w3.org/2001/10/xml-exc-c14n#',
            "Must use exclusive C14N"
        )

    def test_signature_method_rsa_sha256(self):
        """P0: SignedInfo uses RSA-SHA256 signature algorithm."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signed_info = root.find('.//ds:SignedInfo', namespaces=ns)

        sig_method = signed_info.find('ds:SignatureMethod', namespaces=ns)
        self.assertIsNotNone(sig_method, "SignatureMethod missing")
        self.assertEqual(
            sig_method.get('Algorithm'),
            'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256',
            "Must use RSA-SHA256 signature algorithm"
        )

    def test_all_digest_methods_sha256(self):
        """P0: All references use SHA-256 digest algorithm."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signed_info = root.find('.//ds:SignedInfo', namespaces=ns)
        references = signed_info.findall('ds:Reference', namespaces=ns)

        for idx, ref in enumerate(references):
            digest_method = ref.find('ds:DigestMethod', namespaces=ns)
            self.assertIsNotNone(digest_method, f"Reference {idx+1} missing DigestMethod")
            self.assertEqual(
                digest_method.get('Algorithm'),
                'http://www.w3.org/2001/04/xmlenc#sha256',
                f"Reference {idx+1} must use SHA-256"
            )

            # Check DigestValue is not empty
            digest_value = ref.find('ds:DigestValue', namespaces=ns)
            self.assertIsNotNone(digest_value, f"Reference {idx+1} missing DigestValue")
            self.assertTrue(digest_value.text, f"Reference {idx+1} DigestValue is empty")


@tagged('post_install', '-at_install', 'unit', 'p0', 'l10n_cr_einvoice')
class TestXMLSignerKeyInfo(TransactionCase):
    """Test KeyInfo structure and certificate embedding (P0 Critical)."""

    def setUp(self):
        super(TestXMLSignerKeyInfo, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']
        self._create_test_certificate()

    def _create_test_certificate(self):
        """Create test certificate."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
        ])
        self.valid_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(issuer).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    def test_keyinfo_has_id_attribute(self):
        """P0: KeyInfo has Id attribute for referencing."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        key_info = root.find('.//ds:KeyInfo', namespaces=ns)

        self.assertTrue('Id' in key_info.attrib, "KeyInfo must have Id attribute")
        self.assertTrue(key_info.get('Id').startswith('KeyInfo-'),
                       "KeyInfo Id should start with 'KeyInfo-'")

    def test_keyinfo_contains_x509_data(self):
        """P0: KeyInfo contains X509Data with certificate."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        key_info = root.find('.//ds:KeyInfo', namespaces=ns)

        x509_data = key_info.find('ds:X509Data', namespaces=ns)
        self.assertIsNotNone(x509_data, "X509Data missing in KeyInfo")

        x509_cert = x509_data.find('ds:X509Certificate', namespaces=ns)
        self.assertIsNotNone(x509_cert, "X509Certificate missing in X509Data")
        self.assertTrue(x509_cert.text, "X509Certificate is empty")

    def test_x509_certificate_is_valid_base64_der(self):
        """P0: X509Certificate contains valid base64-encoded DER certificate."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        x509_cert_elem = root.find('.//ds:X509Certificate', namespaces=ns)

        # Decode and verify it's a valid certificate
        try:
            cert_der = base64.b64decode(x509_cert_elem.text)
            loaded_cert = x509.load_der_x509_certificate(cert_der, default_backend())
            self.assertIsNotNone(loaded_cert, "Failed to load certificate from DER")
        except Exception as e:
            self.fail(f"X509Certificate is not valid base64 DER: {e}")

    def test_embedded_certificate_matches_signing_certificate(self):
        """P0: Embedded certificate matches the signing certificate."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        x509_cert_elem = root.find('.//ds:X509Certificate', namespaces=ns)

        cert_der = base64.b64decode(x509_cert_elem.text)
        loaded_cert = x509.load_der_x509_certificate(cert_der, default_backend())

        # Verify serial number matches
        self.assertEqual(
            loaded_cert.serial_number,
            self.valid_cert.serial_number,
            "Embedded certificate serial number doesn't match"
        )


@tagged('post_install', '-at_install', 'unit', 'p0', 'l10n_cr_einvoice')
class TestXMLSignerXAdES(TransactionCase):
    """Test XAdES-EPES QualifyingProperties structure (P0 Critical)."""

    def setUp(self):
        super(TestXMLSignerXAdES, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']
        self._create_test_certificate()

    def _create_test_certificate(self):
        """Create test certificate."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
        ])
        self.valid_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(issuer).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    def test_qualifying_properties_present(self):
        """P0: QualifyingProperties element present in Object."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }

        qp = root.find('.//xades:QualifyingProperties', namespaces=ns)
        self.assertIsNotNone(qp, "QualifyingProperties missing")

        # Should have Target attribute pointing to Signature
        target = qp.get('Target')
        self.assertTrue(target.startswith('#Signature-'),
                       "QualifyingProperties Target should reference Signature")

    def test_signed_properties_present_with_id(self):
        """P0: SignedProperties element present with Id attribute."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'xades': 'http://uri.etsi.org/01903/v1.3.2#'}

        sp = root.find('.//xades:SignedProperties', namespaces=ns)
        self.assertIsNotNone(sp, "SignedProperties missing")

        sp_id = sp.get('Id')
        self.assertTrue(sp_id, "SignedProperties must have Id attribute")
        self.assertTrue(sp_id.startswith('SignedProperties-'),
                       "SignedProperties Id should start with 'SignedProperties-'")

    def test_signing_time_present_and_valid(self):
        """P0: SigningTime element present with valid ISO 8601 timestamp."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'xades': 'http://uri.etsi.org/01903/v1.3.2#'}

        signing_time = root.find('.//xades:SigningTime', namespaces=ns)
        self.assertIsNotNone(signing_time, "SigningTime missing")
        self.assertTrue(signing_time.text, "SigningTime is empty")

        # Verify it's a valid ISO 8601 timestamp
        try:
            datetime.strptime(signing_time.text, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            self.fail(f"SigningTime is not valid ISO 8601: {signing_time.text}")

    def test_signature_policy_identifier_present(self):
        """P0: SignaturePolicyIdentifier present (XAdES-EPES requirement)."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'xades': 'http://uri.etsi.org/01903/v1.3.2#'}

        spi = root.find('.//xades:SignaturePolicyIdentifier', namespaces=ns)
        self.assertIsNotNone(spi, "SignaturePolicyIdentifier missing (required for XAdES-EPES)")

    def test_policy_url_and_description(self):
        """P0: Signature policy contains Hacienda policy URL and description."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'xades': 'http://uri.etsi.org/01903/v1.3.2#'}

        identifier = root.find('.//xades:Identifier', namespaces=ns)
        self.assertIsNotNone(identifier, "Policy Identifier missing")
        self.assertIn('comprobanteselectronicos.go.cr', identifier.text,
                     "Policy URL should point to Hacienda")

        description = root.find('.//xades:Description', namespaces=ns)
        self.assertIsNotNone(description, "Policy Description missing")
        self.assertIn('Comprobantes Electronicos', description.text,
                     "Policy description should mention e-invoices")

    def test_policy_hash_present(self):
        """P0: Signature policy hash present and non-empty."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }

        # Navigate: SigPolicyHash -> DigestValue
        sig_policy_hash = root.find('.//xades:SigPolicyHash', namespaces=ns)
        self.assertIsNotNone(sig_policy_hash, "SigPolicyHash missing")

        digest_value = sig_policy_hash.find('ds:DigestValue', namespaces=ns)
        self.assertIsNotNone(digest_value, "Policy DigestValue missing")
        self.assertTrue(digest_value.text, "Policy DigestValue is empty")

    def test_signing_certificate_present(self):
        """P0: SigningCertificate element present with certificate digest."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }

        signing_cert = root.find('.//xades:SigningCertificate', namespaces=ns)
        self.assertIsNotNone(signing_cert, "SigningCertificate missing")

        cert_digest = signing_cert.find('.//xades:CertDigest', namespaces=ns)
        self.assertIsNotNone(cert_digest, "CertDigest missing")

        digest_value = cert_digest.find('ds:DigestValue', namespaces=ns)
        self.assertIsNotNone(digest_value, "Certificate DigestValue missing")
        self.assertTrue(digest_value.text, "Certificate DigestValue is empty")

    def test_certificate_digest_matches(self):
        """P0: Certificate digest in SigningCertificate matches actual certificate."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }

        # Get digest from SigningCertificate
        cert_digest_elem = root.find('.//xades:CertDigest/ds:DigestValue', namespaces=ns)
        embedded_digest = cert_digest_elem.text

        # Compute actual certificate digest
        cert_der = self.valid_cert.public_bytes(serialization.Encoding.DER)
        actual_digest = base64.b64encode(hashlib.sha256(cert_der).digest()).decode('utf-8')

        self.assertEqual(embedded_digest, actual_digest,
                        "Certificate digest doesn't match actual certificate")

    def test_issuer_serial_present(self):
        """P0: IssuerSerial element present with X509IssuerName and X509SerialNumber."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }

        issuer_serial = root.find('.//xades:IssuerSerial', namespaces=ns)
        self.assertIsNotNone(issuer_serial, "IssuerSerial missing")

        issuer_name = issuer_serial.find('ds:X509IssuerName', namespaces=ns)
        self.assertIsNotNone(issuer_name, "X509IssuerName missing")
        self.assertTrue(issuer_name.text, "X509IssuerName is empty")

        serial_number = issuer_serial.find('ds:X509SerialNumber', namespaces=ns)
        self.assertIsNotNone(serial_number, "X509SerialNumber missing")
        self.assertEqual(serial_number.text, str(self.valid_cert.serial_number),
                        "Serial number doesn't match certificate")

    def test_data_object_format_present(self):
        """P0: DataObjectFormat element present with MimeType."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))
        ns = {'xades': 'http://uri.etsi.org/01903/v1.3.2#'}

        data_obj_format = root.find('.//xades:DataObjectFormat', namespaces=ns)
        self.assertIsNotNone(data_obj_format, "DataObjectFormat missing")

        mime_type = data_obj_format.find('xades:MimeType', namespaces=ns)
        self.assertIsNotNone(mime_type, "MimeType missing")
        self.assertEqual(mime_type.text, 'text/xml', "MimeType should be 'text/xml'")


@tagged('post_install', '-at_install', 'unit', 'p0', 'l10n_cr_einvoice')
class TestXMLSignerCertificateValidation(TransactionCase):
    """Test certificate validation and error handling (P0 Critical)."""

    def setUp(self):
        super(TestXMLSignerCertificateValidation, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']
        self._create_test_certificates()

    def _create_test_certificates(self):
        """Create test certificates."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
        ])
        self.valid_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(issuer).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    def test_missing_certificate_raises_error(self):
        """P0: Missing certificate raises UserError."""
        with self.assertRaises(UserError) as cm:
            self.signer.sign_xml(
                SAMPLE_XML,
                certificate=None,
                private_key=self.private_key
            )
        self.assertIn('Certificate and private key must be provided', str(cm.exception))

    def test_missing_private_key_raises_error(self):
        """P0: Missing private key raises UserError."""
        with self.assertRaises(UserError) as cm:
            self.signer.sign_xml(
                SAMPLE_XML,
                certificate=self.valid_cert,
                private_key=None
            )
        self.assertIn('Certificate and private key must be provided', str(cm.exception))

    def test_certificate_id_not_implemented(self):
        """P0: Passing certificate ID raises 'not implemented' error."""
        with self.assertRaises(UserError) as cm:
            self.signer.sign_xml(
                SAMPLE_XML,
                certificate=123,  # Pass an ID instead of object
                private_key=self.private_key
            )
        self.assertIn('not yet implemented', str(cm.exception))

    def test_invalid_certificate_type_raises_error(self):
        """P0: Invalid certificate type raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.signer.sign_xml(
                SAMPLE_XML,
                certificate="not_a_certificate",  # Invalid type
                private_key=self.private_key
            )
        self.assertIn('Invalid certificate object', str(cm.exception))

    def test_invalid_private_key_type_raises_error(self):
        """P0: Invalid private key type raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.signer.sign_xml(
                SAMPLE_XML,
                certificate=self.valid_cert,
                private_key="not_a_key"  # Invalid type
            )
        self.assertIn('Invalid private key object', str(cm.exception))


@tagged('post_install', '-at_install', 'unit', 'p0', 'l10n_cr_einvoice')
class TestXMLSignerXMLValidation(TransactionCase):
    """Test XML content validation and error handling (P0 Critical)."""

    def setUp(self):
        super(TestXMLSignerXMLValidation, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']
        self._create_test_certificate()

    def _create_test_certificate(self):
        """Create test certificate."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
        ])
        self.valid_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(issuer).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    def test_empty_xml_raises_error(self):
        """P0: Empty XML content raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.signer.sign_xml(
                '',
                certificate=self.valid_cert,
                private_key=self.private_key
            )
        self.assertIn('XML content cannot be empty', str(cm.exception))

    def test_none_xml_raises_error(self):
        """P0: None XML content raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.signer.sign_xml(
                None,
                certificate=self.valid_cert,
                private_key=self.private_key
            )
        self.assertIn('XML content cannot be empty', str(cm.exception))

    def test_malformed_xml_raises_error(self):
        """P0: Malformed XML raises ValidationError."""
        malformed_xml = '<FacturaElectronica><Unclosed>'

        with self.assertRaises(ValidationError) as cm:
            self.signer.sign_xml(
                malformed_xml,
                certificate=self.valid_cert,
                private_key=self.private_key
            )
        self.assertIn('Invalid XML content', str(cm.exception))

    def test_invalid_xml_syntax_raises_error(self):
        """P0: Invalid XML syntax raises ValidationError with details."""
        invalid_xml = '<Root><>Invalid<></Root>'

        with self.assertRaises(ValidationError) as cm:
            self.signer.sign_xml(
                invalid_xml,
                certificate=self.valid_cert,
                private_key=self.private_key
            )
        self.assertIn('Invalid XML content', str(cm.exception))


@tagged('post_install', '-at_install', 'unit', 'p1', 'l10n_cr_einvoice')
class TestXMLSignerUniqueIDs(TransactionCase):
    """Test unique ID generation for signature components (P1 High)."""

    def setUp(self):
        super(TestXMLSignerUniqueIDs, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']
        self._create_test_certificate()

    def _create_test_certificate(self):
        """Create test certificate."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
        ])
        self.valid_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(issuer).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    def test_all_ids_are_unique(self):
        """P1: All generated IDs (Signature, SignatureValue, KeyInfo, etc.) are unique."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root = etree.fromstring(signed_xml.encode('utf-8'))

        # Collect all Id attributes
        all_ids = []
        for elem in root.iter():
            if 'Id' in elem.attrib:
                all_ids.append(elem.get('Id'))

        # Check uniqueness
        self.assertEqual(len(all_ids), len(set(all_ids)),
                        f"Duplicate IDs found: {all_ids}")

        # Should have at least 5 IDs: Signature, SignatureValue, Reference, KeyInfo, SignedProperties
        self.assertGreaterEqual(len(all_ids), 5,
                               "Expected at least 5 unique IDs")

    def test_two_signatures_have_different_ids(self):
        """P1: Signing twice generates different IDs each time."""
        signed_xml1 = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        signed_xml2 = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        root1 = etree.fromstring(signed_xml1.encode('utf-8'))
        root2 = etree.fromstring(signed_xml2.encode('utf-8'))

        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        sig1 = root1.find('.//ds:Signature', namespaces=ns)
        sig2 = root2.find('.//ds:Signature', namespaces=ns)

        self.assertNotEqual(sig1.get('Id'), sig2.get('Id'),
                           "Signature IDs should be unique across invocations")


@tagged('post_install', '-at_install', 'unit', 'p1', 'l10n_cr_einvoice')
class TestXMLSignerRFC2253Names(TransactionCase):
    """Test RFC 2253 name conversion for X.509 Distinguished Names (P1 High)."""

    def setUp(self):
        super(TestXMLSignerRFC2253Names, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']

    def test_rfc2253_simple_name(self):
        """P1: Convert simple X.509 name to RFC 2253 format."""
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Company"),
            x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(subject).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(private_key, hashes.SHA256(), default_backend())

        rfc2253_name = self.signer._get_rfc2253_name(cert.issuer)

        # Verify format: CN=...,O=...,C=...
        self.assertIn('CN=test.example.com', rfc2253_name)
        self.assertIn('O=Test Company', rfc2253_name)
        self.assertIn('C=CR', rfc2253_name)

    def test_rfc2253_with_organizational_unit(self):
        """P1: Convert X.509 name with OU to RFC 2253 format."""
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Acme Corp"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "IT Department"),
            x509.NameAttribute(NameOID.COMMON_NAME, "server.acme.cr"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(subject).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(private_key, hashes.SHA256(), default_backend())

        rfc2253_name = self.signer._get_rfc2253_name(cert.issuer)

        self.assertIn('OU=IT Department', rfc2253_name)


@tagged('post_install', '-at_install', 'unit', 'p1', 'l10n_cr_einvoice')
class TestXMLSignerCanonicalization(TransactionCase):
    """Test C14N canonicalization and digest computation (P1 High)."""

    def setUp(self):
        super(TestXMLSignerCanonicalization, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']
        self._create_test_certificate()

    def _create_test_certificate(self):
        """Create test certificate."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
        ])
        self.valid_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(issuer).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    def test_c14n_digest_deterministic(self):
        """P1: C14N digest is deterministic for same element."""
        # Create a test element
        test_elem = etree.fromstring('<Test><Child>Value</Child></Test>')

        digest1 = self.signer._c14n_digest(test_elem)
        digest2 = self.signer._c14n_digest(test_elem)

        self.assertEqual(digest1, digest2, "C14N digest should be deterministic")

    def test_c14n_digest_ignores_whitespace(self):
        """P1: C14N digest produces same result regardless of whitespace."""
        elem1 = etree.fromstring('<Test><Child>Value</Child></Test>')
        elem2 = etree.fromstring('<Test>  \n  <Child>Value</Child>  \n</Test>',
                                etree.XMLParser(remove_blank_text=True))

        digest1 = self.signer._c14n_digest(elem1)
        digest2 = self.signer._c14n_digest(elem2)

        self.assertEqual(digest1, digest2,
                        "C14N should normalize whitespace")

    def test_c14n_digest_returns_base64(self):
        """P1: C14N digest returns valid base64 string."""
        test_elem = etree.fromstring('<Test>Content</Test>')

        digest = self.signer._c14n_digest(test_elem)

        # Should be valid base64
        try:
            decoded = base64.b64decode(digest)
            # SHA-256 produces 32 bytes
            self.assertEqual(len(decoded), 32, "SHA-256 digest should be 32 bytes")
        except Exception as e:
            self.fail(f"Digest is not valid base64: {e}")


@tagged('post_install', '-at_install', 'unit', 'p2', 'l10n_cr_einvoice')
class TestXMLSignerPerformance(TransactionCase):
    """Test signing performance and efficiency (P2 Medium)."""

    def setUp(self):
        super(TestXMLSignerPerformance, self).setUp()
        self.signer = self.env['l10n_cr.xml.signer']
        self._create_test_certificate()

    def _create_test_certificate(self):
        """Create test certificate."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
        ])
        self.valid_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(issuer).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=1)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    def test_signing_performance_under_2_seconds(self):
        """P2: XML signing completes in under 2 seconds (target from test design)."""
        import time

        start_time = time.time()
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )
        elapsed_time = time.time() - start_time

        self.assertLess(elapsed_time, 2.0,
                       f"Signing took {elapsed_time:.2f}s, target is <2s")

    def test_signed_xml_size_reasonable(self):
        """P2: Signed XML size is not excessively large."""
        signed_xml = self.signer.sign_xml(
            SAMPLE_XML,
            certificate=self.valid_cert,
            private_key=self.private_key
        )

        original_size = len(SAMPLE_XML)
        signed_size = len(signed_xml)
        size_increase = signed_size - original_size

        # Signature typically adds ~4-6KB
        self.assertLess(size_increase, 10000,
                       f"Signature added {size_increase} bytes, seems excessive")
