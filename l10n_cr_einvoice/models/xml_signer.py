# -*- coding: utf-8 -*-
"""
XML Digital Signature Module for Costa Rica E-Invoicing

Implements XAdES-EPES enveloped signature as required by
Costa Rica's Ministerio de Hacienda (DGT-R-48-2016).

Uses the enveloped-signature transform (not XPath) and exclusive C14N
for correct digest computation, matching the approach used by known-working
implementations (CRLibre, FacturaElectronicaCR, FirmaXadesEpes).

Author: GMS Development Team
License: LGPL-3
"""

import base64
import hashlib
import logging
import uuid
from datetime import datetime
from lxml import etree

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Namespace URIs
DS_NS = 'http://www.w3.org/2000/09/xmldsig#'
XADES_NS = 'http://uri.etsi.org/01903/v1.3.2#'

# Algorithm URIs
C14N_EXCL = 'http://www.w3.org/2001/10/xml-exc-c14n#'
SIG_RSA_SHA256 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
DIGEST_SHA256 = 'http://www.w3.org/2001/04/xmlenc#sha256'
ENVELOPED_SIG = 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
SIGNED_PROPS_TYPE = 'http://uri.etsi.org/01903#SignedProperties'

# Hacienda policy
POLICY_URL = (
    'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/'
    'Resolucion_Comprobantes_Electronicos_DGT-R-48-2016.pdf'
)
POLICY_DESCRIPTION = (
    'Politica de firma para Comprobantes Electronicos Costa Rica'
)
# SHA-256 hash of the policy document (known value from working implementations)
POLICY_HASH = (
    'NmI5Njk1ZThkNzI0MmIzMGJmZDAyNDc4YjUwNzkzODM2NTBi'
    'OWUxNTBkMmI2YjgzYzZjM2I5NTZlNDQ4OWQzMQ=='
)


class XMLSigner(models.AbstractModel):
    """
    XAdES-EPES digital signature generator for Costa Rica e-invoices.

    Uses enveloped-signature transform + exclusive C14N with three
    references: document, KeyInfo, and SignedProperties.
    """

    _name = 'l10n_cr.xml.signer'
    _description = 'Costa Rica E-Invoice XML Signer'

    @api.model
    def sign_xml(self, xml_content, certificate=None, private_key=None):
        """
        Sign XML document with XAdES-EPES digital signature.

        Args:
            xml_content (str): XML content to sign
            certificate: X.509 certificate object (cryptography)
            private_key: RSA private key object (cryptography)

        Returns:
            str: Signed XML with embedded XAdES-EPES signature
        """
        try:
            if not xml_content:
                raise ValidationError(_('XML content cannot be empty'))

            if certificate is None or private_key is None:
                raise UserError(_(
                    'Certificate and private key must be provided'
                ))

            if isinstance(certificate, int):
                raise UserError(_(
                    'Certificate ID signing not yet implemented.'
                ))

            if not isinstance(certificate, x509.Certificate):
                raise ValidationError(_(
                    'Invalid certificate object.'
                ))

            if not isinstance(private_key, rsa.RSAPrivateKey):
                raise ValidationError(_(
                    'Invalid private key object.'
                ))

            # Parse XML with blank text removal for consistent C14N
            parser = etree.XMLParser(remove_blank_text=True)
            try:
                root = etree.fromstring(xml_content.encode('utf-8'), parser)
            except etree.XMLSyntaxError as e:
                raise ValidationError(_('Invalid XML content: %s') % str(e))

            # Generate unique IDs
            uid = uuid.uuid4().hex[:32]
            sig_id = 'Signature-' + uid
            sig_value_id = 'SignatureValue-' + uid
            ref_id = 'Reference-' + uid
            key_info_id = 'KeyInfo-' + uid
            xades_sp_id = 'SignedProperties-' + uid

            # Build the complete Signature element
            signature = self._build_signature(
                root, certificate, private_key,
                sig_id, sig_value_id, ref_id, key_info_id, xades_sp_id
            )

            # Append signature to root (enveloped)
            root.append(signature)

            # Serialize without pretty-printing to preserve canonical form
            signed_xml = etree.tostring(
                root,
                encoding='UTF-8',
                xml_declaration=True,
            ).decode('utf-8')

            _logger.info('Successfully signed XML document with XAdES-EPES')
            return signed_xml

        except (UserError, ValidationError):
            raise
        except Exception as e:
            error_msg = str(e)
            _logger.error('XML signing failed: %s' % error_msg, exc_info=True)
            raise UserError(_('Failed to sign XML: %s') % error_msg)

    def _build_signature(self, root, certificate, private_key,
                         sig_id, sig_value_id, ref_id, key_info_id,
                         xades_sp_id):
        """Build the complete XAdES-EPES Signature element."""
        ds = DS_NS

        # 1. Build QualifyingProperties first (we need its digest)
        qualifying_props = self._build_qualifying_properties(
            certificate, sig_id, ref_id, xades_sp_id
        )
        signed_props = qualifying_props.find('{%s}SignedProperties' % XADES_NS)
        signed_props_digest = self._c14n_digest(signed_props)

        # 2. Compute document digest (root without Signature - not appended yet)
        doc_digest = self._c14n_digest(root)

        # 3. Build KeyInfo and compute its digest
        key_info = self._build_key_info(certificate, key_info_id)
        key_info_digest = self._c14n_digest(key_info)

        # 4. Build SignedInfo with all three references
        signed_info = self._build_signed_info(
            ref_id, doc_digest,
            key_info_id, key_info_digest,
            xades_sp_id, signed_props_digest
        )

        # 5. Sign the SignedInfo
        sig_value = self._compute_signature_value(signed_info, private_key)

        # 6. Assemble Signature element
        signature = etree.Element(
            '{%s}Signature' % ds,
            nsmap={'ds': ds},
            Id=sig_id
        )
        signature.append(signed_info)

        sig_value_elem = etree.SubElement(
            signature, '{%s}SignatureValue' % ds, Id=sig_value_id
        )
        sig_value_elem.text = sig_value

        signature.append(key_info)

        obj = etree.SubElement(signature, '{%s}Object' % ds)
        obj.append(qualifying_props)

        return signature

    def _build_signed_info(self, ref_id, doc_digest,
                           key_info_id, key_info_digest,
                           xades_sp_id, signed_props_digest):
        """Build SignedInfo with document, KeyInfo, and SignedProperties refs."""
        ds = DS_NS
        signed_info = etree.Element('{%s}SignedInfo' % ds, nsmap={'ds': ds})

        # CanonicalizationMethod
        etree.SubElement(
            signed_info, '{%s}CanonicalizationMethod' % ds, Algorithm=C14N_EXCL
        )
        # SignatureMethod
        etree.SubElement(
            signed_info, '{%s}SignatureMethod' % ds, Algorithm=SIG_RSA_SHA256
        )

        # Reference 1: Document content (enveloped signature)
        ref1 = etree.SubElement(
            signed_info, '{%s}Reference' % ds, Id=ref_id, URI=''
        )
        transforms1 = etree.SubElement(ref1, '{%s}Transforms' % ds)
        etree.SubElement(
            transforms1, '{%s}Transform' % ds, Algorithm=ENVELOPED_SIG
        )
        etree.SubElement(
            transforms1, '{%s}Transform' % ds, Algorithm=C14N_EXCL
        )
        etree.SubElement(ref1, '{%s}DigestMethod' % ds, Algorithm=DIGEST_SHA256)
        dv1 = etree.SubElement(ref1, '{%s}DigestValue' % ds)
        dv1.text = doc_digest

        # Reference 2: KeyInfo
        ref2 = etree.SubElement(
            signed_info, '{%s}Reference' % ds, URI='#' + key_info_id
        )
        transforms2 = etree.SubElement(ref2, '{%s}Transforms' % ds)
        etree.SubElement(
            transforms2, '{%s}Transform' % ds, Algorithm=C14N_EXCL
        )
        etree.SubElement(ref2, '{%s}DigestMethod' % ds, Algorithm=DIGEST_SHA256)
        dv2 = etree.SubElement(ref2, '{%s}DigestValue' % ds)
        dv2.text = key_info_digest

        # Reference 3: SignedProperties (XAdES)
        ref3 = etree.SubElement(
            signed_info, '{%s}Reference' % ds,
            Type=SIGNED_PROPS_TYPE, URI='#' + xades_sp_id
        )
        transforms3 = etree.SubElement(ref3, '{%s}Transforms' % ds)
        etree.SubElement(
            transforms3, '{%s}Transform' % ds, Algorithm=C14N_EXCL
        )
        etree.SubElement(ref3, '{%s}DigestMethod' % ds, Algorithm=DIGEST_SHA256)
        dv3 = etree.SubElement(ref3, '{%s}DigestValue' % ds)
        dv3.text = signed_props_digest

        return signed_info

    def _build_qualifying_properties(self, certificate, sig_id, ref_id,
                                     xades_sp_id):
        """Build XAdES QualifyingProperties with SignaturePolicyIdentifier."""
        ds = DS_NS
        xades = XADES_NS

        qp = etree.Element(
            '{%s}QualifyingProperties' % xades,
            nsmap={'xades': xades, 'ds': ds},
            Target='#' + sig_id
        )
        sp = etree.SubElement(
            qp, '{%s}SignedProperties' % xades, Id=xades_sp_id
        )

        # SignedSignatureProperties
        ssp = etree.SubElement(sp, '{%s}SignedSignatureProperties' % xades)

        # SigningTime
        st = etree.SubElement(ssp, '{%s}SigningTime' % xades)
        st.text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        # SignaturePolicyIdentifier (XAdES-EPES)
        spi = etree.SubElement(ssp, '{%s}SignaturePolicyIdentifier' % xades)
        spid = etree.SubElement(spi, '{%s}SignaturePolicyId' % xades)
        sp_id = etree.SubElement(spid, '{%s}SigPolicyId' % xades)
        identifier = etree.SubElement(sp_id, '{%s}Identifier' % xades)
        identifier.text = POLICY_URL
        desc = etree.SubElement(sp_id, '{%s}Description' % xades)
        desc.text = POLICY_DESCRIPTION

        sp_hash = etree.SubElement(spid, '{%s}SigPolicyHash' % xades)
        etree.SubElement(
            sp_hash, '{%s}DigestMethod' % ds, Algorithm=DIGEST_SHA256
        )
        hv = etree.SubElement(sp_hash, '{%s}DigestValue' % ds)
        hv.text = POLICY_HASH

        # SigningCertificate (SHA-256)
        sc = etree.SubElement(ssp, '{%s}SigningCertificate' % xades)
        cert_el = etree.SubElement(sc, '{%s}Cert' % xades)

        cert_der = certificate.public_bytes(serialization.Encoding.DER)
        cert_hash = hashlib.sha256(cert_der).digest()

        cd = etree.SubElement(cert_el, '{%s}CertDigest' % xades)
        etree.SubElement(cd, '{%s}DigestMethod' % ds, Algorithm=DIGEST_SHA256)
        dv = etree.SubElement(cd, '{%s}DigestValue' % ds)
        dv.text = base64.b64encode(cert_hash).decode('utf-8')

        # IssuerSerial
        iss = etree.SubElement(cert_el, '{%s}IssuerSerial' % xades)
        x509_issuer = etree.SubElement(iss, '{%s}X509IssuerName' % ds)
        x509_issuer.text = self._get_rfc2253_name(certificate.issuer)
        x509_serial = etree.SubElement(iss, '{%s}X509SerialNumber' % ds)
        x509_serial.text = str(certificate.serial_number)

        # SignedDataObjectProperties
        sdop = etree.SubElement(sp, '{%s}SignedDataObjectProperties' % xades)
        dof = etree.SubElement(
            sdop, '{%s}DataObjectFormat' % xades, ObjectReference='#' + ref_id
        )
        mt = etree.SubElement(dof, '{%s}MimeType' % xades)
        mt.text = 'text/xml'

        return qp

    def _build_key_info(self, certificate, key_info_id):
        """Build KeyInfo element with X.509 certificate data."""
        key_info = etree.Element('{%s}KeyInfo' % DS_NS, nsmap={'ds': DS_NS}, Id=key_info_id)
        x509_data = etree.SubElement(key_info, '{%s}X509Data' % DS_NS)

        cert_der = certificate.public_bytes(serialization.Encoding.DER)
        x509_cert = etree.SubElement(x509_data, '{%s}X509Certificate' % DS_NS)
        x509_cert.text = base64.b64encode(cert_der).decode('utf-8')

        return key_info

    def _c14n_digest(self, element):
        """Compute SHA-256 digest of element's exclusive C14N form."""
        canonical = etree.tostring(
            element, method='c14n', exclusive=True, with_comments=False
        )
        return base64.b64encode(hashlib.sha256(canonical).digest()).decode('utf-8')

    def _compute_signature_value(self, signed_info, private_key):
        """Sign the C14N form of SignedInfo using RSA-SHA256."""
        canonical = etree.tostring(
            signed_info, method='c14n', exclusive=True, with_comments=False
        )
        sig_bytes = private_key.sign(
            canonical, padding.PKCS1v15(), hashes.SHA256()
        )
        return base64.b64encode(sig_bytes).decode('utf-8')

    def _get_rfc2253_name(self, name):
        """Convert x509.Name to RFC 2253 string representation."""
        parts = []
        for attr in name:
            oid = attr.oid
            value = attr.value
            if oid == x509.NameOID.COMMON_NAME:
                parts.append('CN=%s' % value)
            elif oid == x509.NameOID.ORGANIZATIONAL_UNIT_NAME:
                parts.append('OU=%s' % value)
            elif oid == x509.NameOID.ORGANIZATION_NAME:
                parts.append('O=%s' % value)
            elif oid == x509.NameOID.COUNTRY_NAME:
                parts.append('C=%s' % value)
            elif oid == x509.NameOID.SERIAL_NUMBER:
                parts.append('2.5.4.5=#1310%s' % value.encode('utf-8').hex())
            else:
                parts.append('%s=%s' % (oid.dotted_string, value))
        return ','.join(parts)

    @api.model
    def verify_signature(self, signed_xml):
        """Verify digital signature on signed XML (placeholder)."""
        _logger.warning(
            'Signature verification not yet implemented. '
            'Hacienda will verify signatures upon submission.'
        )
        return True
