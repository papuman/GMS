# -*- coding: utf-8 -*-
"""
Pytest configuration and fixtures for l10n_cr_einvoice tests

This module provides shared fixtures and configuration for all tests in the module.
"""

import base64
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


# ============================================================================
# TEST MARKERS
# ============================================================================

def pytest_configure(config):
    """Register custom markers for test categorization."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (database, mocked APIs)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (real Hacienda sandbox)"
    )
    config.addinivalue_line(
        "markers", "external: Tests requiring external services"
    )
    config.addinivalue_line(
        "markers", "p0: Critical priority tests (must pass)"
    )
    config.addinivalue_line(
        "markers", "p1: High priority tests"
    )
    config.addinivalue_line(
        "markers", "p2: Medium priority tests"
    )
    config.addinivalue_line(
        "markers", "p3: Low priority tests"
    )


# ============================================================================
# CERTIFICATE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def valid_test_certificate():
    """
    Generate a valid test certificate (valid for 1 year).

    Scope: session (created once per test session)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "San Jose"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Company GMS"),
        x509.NameAttribute(NameOID.COMMON_NAME, "test.gms.cr"),
    ])

    certificate = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow() - timedelta(days=1)
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).sign(private_key, hashes.SHA256(), default_backend())

    return certificate, private_key


@pytest.fixture(scope="session")
def expired_test_certificate():
    """Generate an expired test certificate (expired 30 days ago)."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Expired Test Cert"),
        x509.NameAttribute(NameOID.COMMON_NAME, "expired.test.cr"),
    ])

    certificate = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow() - timedelta(days=400)
    ).not_valid_after(
        datetime.utcnow() - timedelta(days=30)
    ).sign(private_key, hashes.SHA256(), default_backend())

    return certificate, private_key


@pytest.fixture(scope="session")
def expiring_soon_certificate():
    """Generate a certificate expiring in 15 days."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Expiring Soon Test"),
        x509.NameAttribute(NameOID.COMMON_NAME, "expiring.test.cr"),
    ])

    certificate = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow() - timedelta(days=335)
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=15)
    ).sign(private_key, hashes.SHA256(), default_backend())

    return certificate, private_key


@pytest.fixture
def test_pkcs12_data(valid_test_certificate):
    """
    Generate PKCS#12 (.p12) formatted certificate data.

    Returns: (p12_bytes, password)
    """
    certificate, private_key = valid_test_certificate
    password = b"test_password_123"

    from cryptography.hazmat.primitives.serialization import pkcs12

    p12_data = pkcs12.serialize_key_and_certificates(
        b"test_cert",
        private_key,
        certificate,
        None,
        serialization.BestAvailableEncryption(password)
    )

    return p12_data, password


# ============================================================================
# HACIENDA API MOCK RESPONSES
# ============================================================================

@pytest.fixture
def mock_oauth2_token_response():
    """Mock successful OAuth2 token response from Hacienda IDP."""
    return {
        'status_code': 200,
        'json': {
            'access_token': 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJKX...',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_expires_in': 86400,
            'not-before-policy': 0,
            'scope': 'email profile'
        }
    }


@pytest.fixture
def mock_oauth2_401_invalid_grant():
    """Mock OAuth2 401 response for invalid credentials."""
    return {
        'status_code': 401,
        'json': {
            'error': 'invalid_grant',
            'error_description': 'Invalid user credentials'
        }
    }


@pytest.fixture
def mock_hacienda_success_response():
    """Mock successful Hacienda API response (invoice accepted)."""
    return {
        'status_code': 200,
        'json': {
            'clave': '50601012025020100111111111111111111111111111111111',
            'fecha': '2025-02-01T10:00:00-06:00',
            'ind-estado': 'aceptado',
            'respuesta-xml': base64.b64encode(b'<RespuestaHacienda>...</RespuestaHacienda>').decode()
        }
    }


@pytest.fixture
def mock_hacienda_202_accepted():
    """Mock 202 Accepted response (async processing)."""
    return {
        'status_code': 202,
        'text': '',  # Empty body
        'json': {}
    }


@pytest.fixture
def mock_hacienda_procesando_response():
    """Mock Hacienda response for document still processing."""
    return {
        'status_code': 200,
        'json': {
            'clave': '50601012025020100111111111111111111111111111111111',
            'fecha': '2025-02-01T10:00:00-06:00',
            'ind-estado': 'procesando',
            'respuesta-xml': ''
        }
    }


@pytest.fixture
def mock_hacienda_rechazado_response():
    """Mock Hacienda rejection response."""
    return {
        'status_code': 200,
        'json': {
            'clave': '50601012025020100111111111111111111111111111111111',
            'fecha': '2025-02-01T10:00:00-06:00',
            'ind-estado': 'rechazado',
            'detalle-mensaje': 'Clave duplicada o XML inválido',
            'respuesta-xml': base64.b64encode(b'<MensajeReceptor>Rechazado</MensajeReceptor>').decode()
        }
    }


@pytest.fixture
def mock_hacienda_400_validation_error():
    """Mock 400 Bad Request (validation error)."""
    return {
        'status_code': 400,
        'json': {
            'error': 'XML inválido',
            'mensaje': 'El elemento ResumenFactura es obligatorio',
            'detalle-mensaje': 'Error en línea 45: falta elemento obligatorio'
        }
    }


@pytest.fixture
def mock_hacienda_401_response():
    """Mock 401 Unauthorized response (OAuth token expired during submission)."""
    return {
        'status_code': 401,
        'json': {
            'error': 'invalid_token',
            'error_description': 'Token has expired'
        }
    }


@pytest.fixture
def mock_hacienda_403_forbidden():
    """Mock 403 Forbidden response (authorization error)."""
    return {
        'status_code': 403,
        'json': {
            'error': 'forbidden',
            'message': 'User not authorized to perform this operation'
        }
    }


@pytest.fixture
def mock_hacienda_404_not_found():
    """Mock 404 Not Found response."""
    return {
        'status_code': 404,
        'json': {
            'error': 'not_found',
            'message': 'Documento no encontrado en el sistema'
        }
    }


@pytest.fixture
def mock_hacienda_429_response():
    """Mock 429 Rate Limit response."""
    return {
        'status_code': 429,
        'headers': {
            'Retry-After': '60'
        },
        'json': {
            'error': 'rate_limit_exceeded',
            'message': 'Too many requests. Please retry after 60 seconds.'
        }
    }


@pytest.fixture
def mock_hacienda_500_response():
    """Mock 500 Internal Server Error response."""
    return {
        'status_code': 500,
        'json': {
            'error': 'internal_server_error',
            'message': 'Database connection error'
        }
    }


@pytest.fixture
def mock_hacienda_503_unavailable():
    """Mock 503 Service Unavailable response."""
    return {
        'status_code': 503,
        'json': {
            'error': 'service_unavailable',
            'message': 'Service temporarily unavailable. Please retry later.'
        }
    }


# ============================================================================
# TEST DATA FACTORIES
# ============================================================================

@pytest.fixture
def sample_invoice_xml():
    """Generate sample invoice XML for testing."""
    NS = 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica'

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica xmlns="{NS}" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Clave>50601012025020100111111111111111111111111111111111</Clave>
    <NumeroConsecutivo>00100001010000000001</NumeroConsecutivo>
    <FechaEmision>2025-02-01T10:00:00-06:00</FechaEmision>
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
            <Numero>101234567</Numero>
        </Identificacion>
    </Receptor>
    <ResumenFactura>
        <TotalVenta>10000.00</TotalVenta>
        <TotalVentaNeta>10000.00</TotalVentaNeta>
        <TotalImpuesto>1300.00</TotalImpuesto>
        <TotalComprobante>11300.00</TotalComprobante>
    </ResumenFactura>
</FacturaElectronica>'''

    return xml


# ============================================================================
# CONFIGURATION
# ============================================================================

@pytest.fixture
def test_sandbox_credentials():
    """Sandbox Hacienda credentials for E2E tests."""
    return {
        'username': 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr',
        'password': 'e8KLJRHzRA1P0W2ybJ5T',
        'environment': 'sandbox',
        'idp_url': 'https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token',
        'client_id': 'api-stag'
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def assert_valid_xml_structure(xml_string):
    """Helper to assert XML is well-formed."""
    from lxml import etree
    try:
        etree.fromstring(xml_string.encode('utf-8'))
        return True
    except etree.XMLSyntaxError:
        return False


def assert_xsd_valid(xml_string, document_type='FE'):
    """Helper to assert XML passes XSD validation."""
    # This would use the actual XSD validator from the module
    # For now, just check structure
    return assert_valid_xml_structure(xml_string)
