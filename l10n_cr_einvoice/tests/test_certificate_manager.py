# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for Certificate Manager (Phase 2)
Tests certificate loading, validation, and error handling
"""
import base64
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install')
class TestCertificateManager(TransactionCase):
    """Test l10n_cr.certificate.manager model."""

    def setUp(self):
        super(TestCertificateManager, self).setUp()
        self.CertManager = self.env['l10n_cr.certificate.manager']
        self.company = self.env.company

        # Generate test certificates for various scenarios
        self._create_test_certificates()

    def _create_test_certificates(self):
        """Create test certificates for various test scenarios."""
        # Create a valid certificate for testing
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Build certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"CR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"San Jose"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Test Company"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"test.company.cr"),
        ])

        # Valid certificate (current date +/- 1 year)
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

        # Expired certificate
        self.expired_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=400)
        ).not_valid_after(
            datetime.utcnow() - timedelta(days=30)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

        # Not yet valid certificate
        self.future_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() + timedelta(days=30)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=395)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

        # Expiring soon certificate (within 30 days)
        self.expiring_soon_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow() - timedelta(days=335)
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=15)
        ).sign(self.private_key, hashes.SHA256(), default_backend())

    # ========== Certificate Loading Tests ==========

    def test_load_certificate_missing_certificate(self):
        """Test error when certificate is not configured."""
        self.company.l10n_cr_certificate = False

        with self.assertRaises(UserError) as cm:
            self.CertManager.load_certificate_from_company(self.company)

        self.assertIn('not configured', str(cm.exception))

    def test_load_certificate_from_company_id(self):
        """Test loading certificate using company ID instead of record."""
        # Setup valid PKCS#12 data
        from cryptography.hazmat.primitives.serialization import pkcs12

        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test_cert",
            self.private_key,
            self.valid_cert,
            None,
            serialization.BestAvailableEncryption(b"test_password")
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': 'test_password',
        })

        # Load using company ID
        cert, key = self.CertManager.load_certificate_from_company(self.company.id)

        self.assertIsNotNone(cert)
        self.assertIsNotNone(key)

    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.pkcs12.load_key_and_certificates')
    def test_load_pkcs12_certificate_success(self, mock_load):
        """Test successful PKCS#12 certificate loading."""
        # Mock successful load
        mock_load.return_value = (self.private_key, self.valid_cert, None)

        from cryptography.hazmat.primitives.serialization import pkcs12
        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test",
            self.private_key,
            self.valid_cert,
            None,
            serialization.BestAvailableEncryption(b"password")
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': 'password',
        })

        cert, key = self.CertManager.load_certificate_from_company(self.company)

        self.assertEqual(cert, self.valid_cert)
        self.assertEqual(key, self.private_key)

    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.pkcs12.load_key_and_certificates')
    def test_load_pkcs12_with_password(self, mock_load):
        """Test PKCS#12 loading with password encoding."""
        mock_load.return_value = (self.private_key, self.valid_cert, None)

        from cryptography.hazmat.primitives.serialization import pkcs12
        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test",
            self.private_key,
            self.valid_cert,
            None,
            serialization.BestAvailableEncryption(b"SecurePass123")
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': 'certificate.pfx',
            'l10n_cr_key_password': 'SecurePass123',
        })

        cert, key = self.CertManager.load_certificate_from_company(self.company)

        # Verify password was encoded to bytes
        mock_load.assert_called_once()
        call_args = mock_load.call_args[0]
        self.assertIsNotNone(call_args[1])  # Password bytes

    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.pkcs12.load_key_and_certificates')
    def test_load_pkcs12_without_password(self, mock_load):
        """Test PKCS#12 loading without password."""
        mock_load.return_value = (self.private_key, self.valid_cert, None)

        from cryptography.hazmat.primitives.serialization import pkcs12
        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test",
            self.private_key,
            self.valid_cert,
            None,
            serialization.NoEncryption()
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': False,
        })

        cert, key = self.CertManager.load_certificate_from_company(self.company)

        self.assertIsNotNone(cert)

    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.pkcs12.load_key_and_certificates')
    def test_load_pkcs12_no_certificate(self, mock_load):
        """Test error when PKCS#12 file has no certificate."""
        mock_load.return_value = (self.private_key, None, None)

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(b'fake_data'),
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': 'password',
        })

        with self.assertRaises(UserError):
            self.CertManager.load_certificate_from_company(self.company)

    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager.pkcs12.load_key_and_certificates')
    def test_load_pkcs12_no_private_key(self, mock_load):
        """Test error when PKCS#12 file has no private key."""
        mock_load.return_value = (None, self.valid_cert, None)

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(b'fake_data'),
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': 'password',
        })

        with self.assertRaises(UserError):
            self.CertManager.load_certificate_from_company(self.company)

    def test_load_pem_certificate_success(self):
        """Test successful PEM certificate loading."""
        # Serialize certificate and key to PEM
        cert_pem = self.valid_cert.public_bytes(serialization.Encoding.PEM)
        key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(cert_pem),
            'l10n_cr_certificate_filename': 'cert.pem',
            'l10n_cr_private_key': base64.b64encode(key_pem),
            'l10n_cr_key_password': False,
        })

        cert, key = self.CertManager.load_certificate_from_company(self.company)

        self.assertIsNotNone(cert)
        self.assertIsNotNone(key)

    def test_load_pem_certificate_with_encrypted_key(self):
        """Test PEM certificate with encrypted private key."""
        cert_pem = self.valid_cert.public_bytes(serialization.Encoding.PEM)
        key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(b'SecureKey456')
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(cert_pem),
            'l10n_cr_certificate_filename': 'cert.crt',
            'l10n_cr_private_key': base64.b64encode(key_pem),
            'l10n_cr_key_password': 'SecureKey456',
        })

        cert, key = self.CertManager.load_certificate_from_company(self.company)

        self.assertIsNotNone(cert)
        self.assertIsNotNone(key)

    def test_load_pem_certificate_missing_private_key(self):
        """Test error when PEM format but private key is missing."""
        cert_pem = self.valid_cert.public_bytes(serialization.Encoding.PEM)

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(cert_pem),
            'l10n_cr_certificate_filename': 'cert.pem',
            'l10n_cr_private_key': False,
            'l10n_cr_key_password': False,
        })

        with self.assertRaises(UserError):
            self.CertManager.load_certificate_from_company(self.company)

    def test_load_certificate_format_detection_p12(self):
        """Test automatic format detection for .p12 files."""
        from cryptography.hazmat.primitives.serialization import pkcs12

        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test",
            self.private_key,
            self.valid_cert,
            None,
            serialization.NoEncryption()
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': 'certificate.p12',
            'l10n_cr_key_password': False,
        })

        cert, key = self.CertManager.load_certificate_from_company(self.company)
        self.assertIsNotNone(cert)

    def test_load_certificate_format_detection_pfx(self):
        """Test automatic format detection for .pfx files."""
        from cryptography.hazmat.primitives.serialization import pkcs12

        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test",
            self.private_key,
            self.valid_cert,
            None,
            serialization.NoEncryption()
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': 'certificate.pfx',
            'l10n_cr_key_password': False,
        })

        cert, key = self.CertManager.load_certificate_from_company(self.company)
        self.assertIsNotNone(cert)

    def test_load_certificate_invalid_base64(self):
        """Test error with invalid base64 encoded certificate."""
        self.company.write({
            'l10n_cr_certificate': 'not_valid_base64!!!',
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': 'password',
        })

        with self.assertRaises(UserError):
            self.CertManager.load_certificate_from_company(self.company)

    # ========== Certificate Validation Tests ==========

    def test_validate_certificate_valid(self):
        """Test validation passes for valid certificate."""
        # Should not raise any exception
        self.CertManager._validate_certificate(self.valid_cert)

    def test_validate_certificate_expired(self):
        """Test error for expired certificate."""
        with self.assertRaises(ValidationError) as cm:
            self.CertManager._validate_certificate(self.expired_cert)

        self.assertIn('expired', str(cm.exception).lower())

    def test_validate_certificate_not_yet_valid(self):
        """Test error for certificate not yet valid."""
        with self.assertRaises(ValidationError) as cm:
            self.CertManager._validate_certificate(self.future_cert)

        self.assertIn('not yet valid', str(cm.exception).lower())

    @patch('odoo.addons.l10n_cr_einvoice.models.certificate_manager._logger')
    def test_validate_certificate_expiring_soon(self, mock_logger):
        """Test warning logged for certificate expiring soon."""
        self.CertManager._validate_certificate(self.expiring_soon_cert)

        # Should log a warning
        mock_logger.warning.assert_called()
        warning_msg = str(mock_logger.warning.call_args)
        self.assertIn('expires soon', warning_msg.lower())

    # ========== Certificate Info Tests ==========

    def test_get_certificate_info_success(self):
        """Test getting certificate information."""
        from cryptography.hazmat.primitives.serialization import pkcs12

        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test",
            self.private_key,
            self.valid_cert,
            None,
            serialization.NoEncryption()
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': False,
        })

        info = self.CertManager.get_certificate_info(self.company)

        self.assertIn('subject_cn', info)
        self.assertIn('subject_org', info)
        self.assertIn('issuer_cn', info)
        self.assertIn('not_before', info)
        self.assertIn('not_after', info)
        self.assertIn('days_until_expiry', info)
        self.assertIn('serial_number', info)
        self.assertIn('is_valid', info)

        self.assertTrue(info['is_valid'])
        self.assertEqual(info['subject_org'], 'Test Company')
        self.assertEqual(info['subject_cn'], 'test.company.cr')

    def test_get_certificate_info_from_id(self):
        """Test getting certificate info using company ID."""
        from cryptography.hazmat.primitives.serialization import pkcs12

        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test",
            self.private_key,
            self.valid_cert,
            None,
            serialization.NoEncryption()
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': False,
        })

        info = self.CertManager.get_certificate_info(self.company.id)

        self.assertIn('is_valid', info)
        self.assertTrue(info['is_valid'])

    def test_get_certificate_info_error_handling(self):
        """Test certificate info returns error dict on failure."""
        self.company.l10n_cr_certificate = False

        info = self.CertManager.get_certificate_info(self.company)

        self.assertIn('error', info)
        self.assertIn('is_valid', info)
        self.assertFalse(info['is_valid'])

    # ========== Certificate Export Tests ==========

    def test_export_certificate_pem(self):
        """Test exporting certificate to PEM format."""
        pem_output = self.CertManager.export_certificate_pem(self.valid_cert)

        self.assertIsInstance(pem_output, str)
        self.assertIn('BEGIN CERTIFICATE', pem_output)
        self.assertIn('END CERTIFICATE', pem_output)

    # ========== Edge Cases and Error Handling ==========

    def test_load_certificate_wrong_password(self):
        """Test error with incorrect PKCS#12 password."""
        from cryptography.hazmat.primitives.serialization import pkcs12

        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test",
            self.private_key,
            self.valid_cert,
            None,
            serialization.BestAvailableEncryption(b"correct_password")
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': 'wrong_password',
        })

        with self.assertRaises(UserError):
            self.CertManager.load_certificate_from_company(self.company)

    def test_load_certificate_corrupted_data(self):
        """Test error with corrupted certificate data."""
        self.company.write({
            'l10n_cr_certificate': base64.b64encode(b'corrupted binary data'),
            'l10n_cr_certificate_filename': 'test.p12',
            'l10n_cr_key_password': 'password',
        })

        with self.assertRaises(UserError):
            self.CertManager.load_certificate_from_company(self.company)

    def test_load_pem_wrong_key_password(self):
        """Test error with wrong PEM key password."""
        cert_pem = self.valid_cert.public_bytes(serialization.Encoding.PEM)
        key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(b'CorrectPass')
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(cert_pem),
            'l10n_cr_certificate_filename': 'cert.pem',
            'l10n_cr_private_key': base64.b64encode(key_pem),
            'l10n_cr_key_password': 'WrongPass',
        })

        with self.assertRaises(UserError):
            self.CertManager.load_certificate_from_company(self.company)

    def test_load_certificate_no_filename(self):
        """Test loading certificate with no filename (fallback to auto-detect)."""
        from cryptography.hazmat.primitives.serialization import pkcs12

        pkcs12_data = pkcs12.serialize_key_and_certificates(
            b"test",
            self.private_key,
            self.valid_cert,
            None,
            serialization.NoEncryption()
        )

        self.company.write({
            'l10n_cr_certificate': base64.b64encode(pkcs12_data),
            'l10n_cr_certificate_filename': False,  # No filename
            'l10n_cr_key_password': False,
        })

        # Should try PKCS#12 first and succeed
        cert, key = self.CertManager.load_certificate_from_company(self.company)
        self.assertIsNotNone(cert)
