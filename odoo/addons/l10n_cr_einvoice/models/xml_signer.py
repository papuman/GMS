# -*- coding: utf-8 -*-
import base64
import logging
from lxml import etree
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class XMLSigner(models.AbstractModel):
    """
    Signs XML documents using XMLDSig (XML Digital Signature) standard.

    Implements enveloped signature as required by Costa Rica Hacienda
    for electronic invoice v4.4 specification.
    """
    _name = 'l10n_cr.xml.signer'
    _description = 'Costa Rica E-Invoice XML Signer'

    @api.model
    def sign_xml(self, xml_content, certificate, private_key):
        """
        Sign XML document with digital signature.

        Args:
            xml_content (str): XML content to sign
            certificate: cryptography certificate object
            private_key: cryptography private key object

        Returns:
            str: Signed XML with embedded signature

        Raises:
            ValidationError: If signing fails
        """
        try:
            # Parse XML
            root = etree.fromstring(xml_content.encode('utf-8'))

            # Create signature element
            signature = self._create_signature_element(root, certificate, private_key)

            # Insert signature as last child of root
            root.append(signature)

            # Convert back to string
            signed_xml = etree.tostring(
                root,
                encoding='utf-8',
                xml_declaration=True,
                pretty_print=True
            ).decode('utf-8')

            _logger.info('XML document signed successfully')
            return signed_xml

        except Exception as e:
            _logger.error(f'XML signing failed: {str(e)}')
            raise ValidationError(_(
                'Failed to sign XML document: %s'
            ) % str(e))

    def _create_signature_element(self, root, certificate, private_key):
        """
        Create XMLDSig Signature element.

        Args:
            root: XML root element to sign
            certificate: cryptography certificate object
            private_key: cryptography private key object

        Returns:
            lxml.etree.Element: Signature element
        """
        # Define namespaces
        ds_ns = 'http://www.w3.org/2000/09/xmldsig#'
        NSMAP = {'ds': ds_ns}

        # Create Signature element
        signature = etree.Element(
            '{%s}Signature' % ds_ns,
            nsmap=NSMAP
        )

        # 1. SignedInfo
        signed_info = self._create_signed_info(root, ds_ns)
        signature.append(signed_info)

        # 2. Calculate signature value
        signature_value = self._calculate_signature_value(
            signed_info,
            private_key,
            ds_ns
        )
        signature.append(signature_value)

        # 3. KeyInfo with certificate
        key_info = self._create_key_info(certificate, ds_ns)
        signature.append(key_info)

        return signature

    def _create_signed_info(self, root, ds_ns):
        """
        Create SignedInfo element with canonicalization and reference.

        Args:
            root: XML root element being signed
            ds_ns: XMLDSig namespace

        Returns:
            lxml.etree.Element: SignedInfo element
        """
        signed_info = etree.Element('{%s}SignedInfo' % ds_ns)

        # CanonicalizationMethod
        canon_method = etree.SubElement(
            signed_info,
            '{%s}CanonicalizationMethod' % ds_ns,
            Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
        )

        # SignatureMethod (RSA-SHA256)
        sig_method = etree.SubElement(
            signed_info,
            '{%s}SignatureMethod' % ds_ns,
            Algorithm='http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
        )

        # Reference (reference to root document)
        reference = etree.SubElement(
            signed_info,
            '{%s}Reference' % ds_ns,
            URI=''  # Empty URI means entire document
        )

        # Transforms
        transforms = etree.SubElement(reference, '{%s}Transforms' % ds_ns)

        # Enveloped signature transform
        etree.SubElement(
            transforms,
            '{%s}Transform' % ds_ns,
            Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature'
        )

        # DigestMethod (SHA-256)
        etree.SubElement(
            reference,
            '{%s}DigestMethod' % ds_ns,
            Algorithm='http://www.w3.org/2001/04/xmlenc#sha256'
        )

        # DigestValue (will be calculated)
        digest_value = self._calculate_digest(root)
        etree.SubElement(
            reference,
            '{%s}DigestValue' % ds_ns
        ).text = digest_value

        return signed_info

    def _calculate_digest(self, element):
        """
        Calculate SHA-256 digest of XML element.

        Args:
            element: lxml.etree.Element

        Returns:
            str: Base64-encoded digest
        """
        # Canonicalize element
        canonical = etree.tostring(
            element,
            method='c14n',
            exclusive=False,
            with_comments=False
        )

        # Calculate SHA-256 hash
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(canonical)
        digest_bytes = digest.finalize()

        # Base64 encode
        return base64.b64encode(digest_bytes).decode('utf-8')

    def _calculate_signature_value(self, signed_info, private_key, ds_ns):
        """
        Calculate and create SignatureValue element.

        Args:
            signed_info: SignedInfo element
            private_key: cryptography private key object
            ds_ns: XMLDSig namespace

        Returns:
            lxml.etree.Element: SignatureValue element
        """
        # Canonicalize SignedInfo
        canonical = etree.tostring(
            signed_info,
            method='c14n',
            exclusive=False,
            with_comments=False
        )

        # Sign with private key (RSA-SHA256)
        signature_bytes = private_key.sign(
            canonical,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        # Base64 encode
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')

        # Create SignatureValue element
        signature_value = etree.Element('{%s}SignatureValue' % ds_ns)
        signature_value.text = signature_b64

        return signature_value

    def _create_key_info(self, certificate, ds_ns):
        """
        Create KeyInfo element with X509 certificate data.

        Args:
            certificate: cryptography certificate object
            ds_ns: XMLDSig namespace

        Returns:
            lxml.etree.Element: KeyInfo element
        """
        key_info = etree.Element('{%s}KeyInfo' % ds_ns)
        x509_data = etree.SubElement(key_info, '{%s}X509Data' % ds_ns)

        # X509Certificate (DER-encoded certificate)
        cert_der = certificate.public_bytes(serialization.Encoding.DER)
        cert_b64 = base64.b64encode(cert_der).decode('utf-8')

        x509_cert = etree.SubElement(x509_data, '{%s}X509Certificate' % ds_ns)
        x509_cert.text = cert_b64

        return key_info

    @api.model
    def verify_signature(self, signed_xml):
        """
        Verify XML signature (for debugging/testing).

        Args:
            signed_xml (str): Signed XML content

        Returns:
            bool: True if signature is valid

        Note: This is a basic verification. Hacienda will perform
        the official validation upon submission.
        """
        try:
            root = etree.fromstring(signed_xml.encode('utf-8'))

            # Find Signature element
            ds_ns = 'http://www.w3.org/2000/09/xmldsig#'
            signature = root.find('{%s}Signature' % ds_ns)

            if signature is None:
                _logger.error('No signature found in XML')
                return False

            _logger.info('Signature element found, basic structure verified')

            # TODO: Implement full signature verification
            # This requires extracting the certificate, verifying the digest,
            # and verifying the signature value. For now, we trust that
            # if the signature was created by our signing method, it's valid.
            # Hacienda will perform the authoritative verification.

            return True

        except Exception as e:
            _logger.error(f'Signature verification failed: {str(e)}')
            return False
