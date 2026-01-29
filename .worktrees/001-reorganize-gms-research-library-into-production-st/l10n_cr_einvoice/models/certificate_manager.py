# -*- coding: utf-8 -*-
import base64
import logging
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CertificateManager(models.AbstractModel):
    """
    Manages X.509 digital certificates for electronic invoice signing.

    Handles certificate loading, validation, and private key extraction
    for both .p12 (PKCS#12) and .pem formats.
    """
    _name = 'l10n_cr.certificate.manager'
    _description = 'Costa Rica E-Invoice Certificate Manager'

    @api.model
    def load_certificate_from_company(self, company):
        """
        Load and validate certificate from company configuration.

        Args:
            company: res.company record

        Returns:
            tuple: (certificate, private_key) as cryptography objects

        Raises:
            UserError: If certificate is missing or invalid
        """
        if not company.l10n_cr_certificate:
            raise UserError(_(
                'Digital certificate not configured for company %s. '
                'Please upload your X.509 certificate in company settings.'
            ) % company.name)

        try:
            # Decode certificate data
            cert_data = base64.b64decode(company.l10n_cr_certificate)

            # Determine format from filename or try both
            filename = company.l10n_cr_certificate_filename or ''

            if filename.endswith('.p12') or filename.endswith('.pfx'):
                return self._load_pkcs12_certificate(
                    cert_data,
                    company.l10n_cr_key_password
                )
            elif filename.endswith('.pem') or filename.endswith('.crt'):
                return self._load_pem_certificate(
                    cert_data,
                    company.l10n_cr_private_key,
                    company.l10n_cr_key_password
                )
            else:
                # Try PKCS#12 first (most common for Hacienda)
                try:
                    return self._load_pkcs12_certificate(
                        cert_data,
                        company.l10n_cr_key_password
                    )
                except Exception:
                    # Fallback to PEM
                    return self._load_pem_certificate(
                        cert_data,
                        company.l10n_cr_private_key,
                        company.l10n_cr_key_password
                    )

        except Exception as e:
            _logger.error(f'Failed to load certificate: {str(e)}')
            raise UserError(_(
                'Failed to load digital certificate: %s\n'
                'Please verify the certificate file and password are correct.'
            ) % str(e))

    def _load_pkcs12_certificate(self, cert_data, password):
        """
        Load certificate and private key from PKCS#12 (.p12) format.

        Args:
            cert_data: Raw certificate bytes
            password: Certificate password (PIN)

        Returns:
            tuple: (certificate, private_key)
        """
        try:
            # Convert password to bytes if provided
            pwd_bytes = None
            if password:
                pwd_bytes = password.encode('utf-8')

            # Load PKCS#12
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                cert_data,
                pwd_bytes,
                backend=default_backend()
            )

            if not certificate:
                raise ValidationError(_('No certificate found in PKCS#12 file'))

            if not private_key:
                raise ValidationError(_('No private key found in PKCS#12 file'))

            # Validate certificate
            self._validate_certificate(certificate)

            _logger.info('Successfully loaded PKCS#12 certificate')
            return certificate, private_key

        except Exception as e:
            _logger.error(f'PKCS#12 loading failed: {str(e)}')
            raise

    def _load_pem_certificate(self, cert_data, private_key_data, password):
        """
        Load certificate and private key from PEM format.

        Args:
            cert_data: Raw certificate bytes (PEM format)
            private_key_data: Raw private key bytes (from company.l10n_cr_private_key)
            password: Private key password if encrypted

        Returns:
            tuple: (certificate, private_key)
        """
        try:
            # Load certificate
            certificate = x509.load_pem_x509_certificate(
                cert_data,
                backend=default_backend()
            )

            # Load private key
            if not private_key_data:
                raise ValidationError(_(
                    'Private key is required when using PEM certificate format'
                ))

            key_data = base64.b64decode(private_key_data)
            pwd_bytes = password.encode('utf-8') if password else None

            private_key = serialization.load_pem_private_key(
                key_data,
                password=pwd_bytes,
                backend=default_backend()
            )

            # Validate certificate
            self._validate_certificate(certificate)

            _logger.info('Successfully loaded PEM certificate')
            return certificate, private_key

        except Exception as e:
            _logger.error(f'PEM loading failed: {str(e)}')
            raise

    def _validate_certificate(self, certificate):
        """
        Validate certificate is suitable for electronic invoicing.

        Args:
            certificate: cryptography certificate object

        Raises:
            ValidationError: If certificate is invalid or expired
        """
        # Check expiration
        now = datetime.utcnow()
        not_before = certificate.not_valid_before
        not_after = certificate.not_valid_after

        if now < not_before:
            raise ValidationError(_(
                'Certificate is not yet valid. Valid from: %s'
            ) % not_before.strftime('%Y-%m-%d'))

        if now > not_after:
            raise ValidationError(_(
                'Certificate has expired. Expired on: %s'
            ) % not_after.strftime('%Y-%m-%d'))

        # Warn if expiring soon (within 30 days)
        days_until_expiry = (not_after - now).days
        if days_until_expiry < 30:
            _logger.warning(
                f'Certificate expires soon! Days remaining: {days_until_expiry}'
            )

        _logger.info(
            f'Certificate valid from {not_before} to {not_after} '
            f'({days_until_expiry} days remaining)'
        )

    @api.model
    def get_certificate_info(self, company):
        """
        Get human-readable certificate information.

        Args:
            company: res.company record

        Returns:
            dict: Certificate details (subject, issuer, validity, etc.)
        """
        try:
            certificate, _ = self.load_certificate_from_company(company)

            # Extract subject information
            subject = certificate.subject
            subject_cn = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
            subject_org = subject.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)

            # Extract issuer information
            issuer = certificate.issuer
            issuer_cn = issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)

            # Calculate days until expiry
            now = datetime.utcnow()
            days_until_expiry = (certificate.not_valid_after - now).days

            return {
                'subject_cn': subject_cn[0].value if subject_cn else '',
                'subject_org': subject_org[0].value if subject_org else '',
                'issuer_cn': issuer_cn[0].value if issuer_cn else '',
                'not_before': certificate.not_valid_before.strftime('%Y-%m-%d'),
                'not_after': certificate.not_valid_after.strftime('%Y-%m-%d'),
                'days_until_expiry': days_until_expiry,
                'serial_number': str(certificate.serial_number),
                'is_valid': days_until_expiry > 0,
            }

        except Exception as e:
            _logger.error(f'Failed to get certificate info: {str(e)}')
            return {
                'error': str(e),
                'is_valid': False,
            }

    @api.model
    def export_certificate_pem(self, certificate):
        """
        Export certificate to PEM format (for debugging/verification).

        Args:
            certificate: cryptography certificate object

        Returns:
            str: PEM-encoded certificate
        """
        pem_bytes = certificate.public_bytes(serialization.Encoding.PEM)
        return pem_bytes.decode('utf-8')
