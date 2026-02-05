# -*- coding: utf-8 -*-
"""
Mock Fixtures for Cédula Lookup Service Tests

Provides comprehensive mock responses for Hacienda and GoMeta APIs,
including success cases, error scenarios, timeouts, and malformed responses.

These mocks are used across all lookup service tests to ensure consistent
and predictable testing of external API integrations.

Priority: P0 (Critical - shared test infrastructure)
"""

from unittest.mock import Mock


class HaciendaAPIMocks:
    """Mock responses for Hacienda API."""

    @staticmethod
    def success_response_inscrito():
        """Successful response for inscrito (active) company."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            'nombre': 'Gimnasio Fitness Center SA',
            'tipoIdentificacion': '02',  # Jurídica
            'regimen': {
                'codigo': '01',
                'descripcion': 'General'
            },
            'situacion': 'INSCRITO',
            'correo': 'info@gimnasio.cr',
            'telefono': '2200-1100',
            'actividades': [
                {
                    'codigo': '9311',
                    'descripcion': 'Gestión de instalaciones deportivas',
                    'estado': 'ACTIVO',
                    'tipo': 'PRINCIPAL'
                },
                {
                    'codigo': '9313',
                    'descripcion': 'Actividades de gimnasios',
                    'estado': 'ACTIVO',
                    'tipo': 'SECUNDARIA'
                }
            ]
        }
        return mock

    @staticmethod
    def success_response_inactivo():
        """Successful response for inactive company."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            'nombre': 'Empresa Inactiva SA',
            'tipoIdentificacion': '02',
            'regimen': {
                'codigo': '01',
                'descripcion': 'General'
            },
            'situacion': 'INACTIVO',
            'correo': '',
            'telefono': '',
            'actividades': []
        }
        return mock

    @staticmethod
    def success_response_fisica():
        """Successful response for physical person (cédula física)."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            'nombre': 'Juan Pérez Mora',
            'tipoIdentificacion': '01',  # Física
            'regimen': {
                'codigo': '02',
                'descripcion': 'Simplificado'
            },
            'situacion': 'INSCRITO',
            'correo': 'juan.perez@email.cr',
            'actividades': [
                {
                    'codigo': '9602',
                    'descripcion': 'Peluquería y otros tratamientos de belleza',
                    'estado': 'ACTIVO',
                    'tipo': 'PRINCIPAL'
                }
            ]
        }
        return mock

    @staticmethod
    def error_404_not_found():
        """404 response for cédula not found in registry."""
        mock = Mock()
        mock.status_code = 404
        mock.json.return_value = {
            'error': 'not_found',
            'message': 'Cédula no encontrada en el registro de Hacienda'
        }
        return mock

    @staticmethod
    def error_400_invalid_format():
        """400 response for invalid cédula format."""
        mock = Mock()
        mock.status_code = 400
        mock.json.return_value = {
            'error': 'invalid_request',
            'message': 'Formato de cédula inválido'
        }
        return mock

    @staticmethod
    def error_401_unauthorized():
        """401 response for authentication failure."""
        mock = Mock()
        mock.status_code = 401
        mock.json.return_value = {
            'error': 'invalid_token',
            'error_description': 'Token has expired or is invalid'
        }
        return mock

    @staticmethod
    def error_429_rate_limit():
        """429 response for rate limit exceeded."""
        mock = Mock()
        mock.status_code = 429
        mock.headers = {'Retry-After': '60'}
        mock.json.return_value = {
            'error': 'rate_limit_exceeded',
            'message': 'Too many requests. Please retry after 60 seconds.'
        }
        return mock

    @staticmethod
    def error_500_internal_error():
        """500 response for server error."""
        mock = Mock()
        mock.status_code = 500
        mock.json.return_value = {
            'error': 'internal_server_error',
            'message': 'Database connection error'
        }
        return mock

    @staticmethod
    def error_503_unavailable():
        """503 response for service unavailable."""
        mock = Mock()
        mock.status_code = 503
        mock.json.return_value = {
            'error': 'service_unavailable',
            'message': 'Service temporarily unavailable. Please retry later.'
        }
        return mock

    @staticmethod
    def error_504_timeout():
        """504 response for gateway timeout."""
        mock = Mock()
        mock.status_code = 504
        mock.json.return_value = {
            'error': 'gateway_timeout',
            'message': 'Request timeout'
        }
        return mock

    @staticmethod
    def malformed_json():
        """Response with malformed JSON."""
        mock = Mock()
        mock.status_code = 200
        mock.json.side_effect = ValueError("Invalid JSON")
        return mock

    @staticmethod
    def timeout_exception():
        """Simulate connection timeout."""
        import requests
        raise requests.Timeout("Connection timeout after 5 seconds")

    @staticmethod
    def connection_error():
        """Simulate connection error."""
        import requests
        raise requests.ConnectionError("Failed to establish connection")


class GoMetaAPIMocks:
    """Mock responses for GoMeta fallback API."""

    @staticmethod
    def success_response_inscrito():
        """Successful response from GoMeta."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            'nombre': 'GoMeta Lookup Company SA',
            'tipo': 'JURIDICA',
            'estado': 'ACTIVO',
            'email': 'gometa@company.cr',
            'telefono': '2300-4500'
        }
        return mock

    @staticmethod
    def success_response_fisica():
        """Successful response for physical person."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            'nombre': 'María González López',
            'tipo': 'FISICA',
            'estado': 'ACTIVO',
            'email': 'maria@email.cr'
        }
        return mock

    @staticmethod
    def error_404_not_found():
        """404 response from GoMeta."""
        mock = Mock()
        mock.status_code = 404
        mock.json.return_value = {
            'error': 'not_found',
            'message': 'Registro no encontrado'
        }
        return mock

    @staticmethod
    def error_500_internal():
        """500 response from GoMeta."""
        mock = Mock()
        mock.status_code = 500
        mock.json.return_value = {
            'error': 'server_error',
            'message': 'Internal server error'
        }
        return mock

    @staticmethod
    def error_503_unavailable():
        """503 response from GoMeta."""
        mock = Mock()
        mock.status_code = 503
        mock.json.return_value = {
            'error': 'unavailable',
            'message': 'Service temporarily unavailable'
        }
        return mock

    @staticmethod
    def timeout_exception():
        """Simulate timeout."""
        import requests
        raise requests.Timeout("GoMeta API timeout")

    @staticmethod
    def connection_error():
        """Simulate connection error."""
        import requests
        raise requests.ConnectionError("Cannot connect to GoMeta API")


class CacheDataFixtures:
    """Test data fixtures for cache entries."""

    @staticmethod
    def fresh_cache_data():
        """Data for fresh cache entry (<7 days)."""
        from datetime import datetime, timezone
        from odoo import fields

        now = datetime.now(timezone.utc)
        return {
            'cedula': '3101234567',
            'name': 'Fresh Cache Company SA',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'tax_regime': 'General',
            'economic_activities': '[{"code": "9311", "description": "Gimnasios"}]',
            'primary_activity': '9311',
            'fetched_at': fields.Datetime.to_string(now),
            'refreshed_at': fields.Datetime.to_string(now),
            'source': 'hacienda',
            'access_count': 10,
            'last_access_at': fields.Datetime.to_string(now),
        }

    @staticmethod
    def refresh_zone_cache_data():
        """Data for cache in refresh zone (5-7 days)."""
        from datetime import datetime, timedelta, timezone
        from odoo import fields

        now = datetime.now(timezone.utc)
        refresh_time = now - timedelta(days=6)
        return {
            'cedula': '3101234568',
            'name': 'Refresh Zone Company SA',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'tax_regime': 'General',
            'fetched_at': fields.Datetime.to_string(refresh_time),
            'refreshed_at': fields.Datetime.to_string(refresh_time),
            'source': 'hacienda',
            'access_count': 50,
        }

    @staticmethod
    def stale_cache_data():
        """Data for stale cache (7-90 days)."""
        from datetime import datetime, timedelta, timezone
        from odoo import fields

        now = datetime.now(timezone.utc)
        stale_time = now - timedelta(days=30)
        return {
            'cedula': '3101234569',
            'name': 'Stale Cache Company SA',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'tax_regime': 'General',
            'fetched_at': fields.Datetime.to_string(stale_time),
            'refreshed_at': fields.Datetime.to_string(stale_time),
            'source': 'hacienda',
            'access_count': 5,
        }

    @staticmethod
    def expired_cache_data():
        """Data for expired cache (>90 days)."""
        from datetime import datetime, timedelta, timezone
        from odoo import fields

        now = datetime.now(timezone.utc)
        expired_time = now - timedelta(days=100)
        return {
            'cedula': '3101234570',
            'name': 'Expired Cache Company SA',
            'company_type': 'company',
            'tax_status': 'inscrito',
            'tax_regime': 'General',
            'fetched_at': fields.Datetime.to_string(expired_time),
            'refreshed_at': fields.Datetime.to_string(expired_time),
            'source': 'hacienda',
            'access_count': 2,
        }

    @staticmethod
    def not_found_cache_data():
        """Data for cédula not found in registry."""
        from datetime import datetime, timezone
        from odoo import fields

        now = datetime.now(timezone.utc)
        return {
            'cedula': '9999999999',
            'name': 'Not Found',
            'company_type': 'other',
            'tax_status': 'no_encontrado',
            'fetched_at': fields.Datetime.to_string(now),
            'refreshed_at': fields.Datetime.to_string(now),
            'source': 'hacienda',
            'error_message': 'Cédula not found in Hacienda registry',
        }


class WaterfallScenarios:
    """Complete waterfall scenario mocks."""

    @staticmethod
    def scenario_hacienda_success():
        """Scenario: Hacienda API succeeds."""
        return {
            'hacienda': HaciendaAPIMocks.success_response_inscrito(),
            'expected_source': 'hacienda',
            'expected_status': 'inscrito'
        }

    @staticmethod
    def scenario_hacienda_fails_gometa_succeeds():
        """Scenario: Hacienda fails, GoMeta succeeds."""
        return {
            'hacienda': HaciendaAPIMocks.error_503_unavailable(),
            'gometa': GoMetaAPIMocks.success_response_inscrito(),
            'expected_source': 'gometa',
            'expected_status': 'inscrito'
        }

    @staticmethod
    def scenario_both_apis_fail_stale_cache():
        """Scenario: Both APIs fail, use stale cache."""
        return {
            'hacienda': HaciendaAPIMocks.error_503_unavailable(),
            'gometa': GoMetaAPIMocks.error_503_unavailable(),
            'cache': CacheDataFixtures.stale_cache_data(),
            'expected_source': 'cache',
            'expected_warning': True
        }

    @staticmethod
    def scenario_all_fail_manual_entry():
        """Scenario: All fail, require manual entry."""
        return {
            'hacienda': HaciendaAPIMocks.error_404_not_found(),
            'gometa': GoMetaAPIMocks.error_404_not_found(),
            'expected_error': True,
            'expected_message_contains': 'manual'
        }

    @staticmethod
    def scenario_rate_limit_exceeded():
        """Scenario: Rate limit exceeded."""
        return {
            'hacienda': HaciendaAPIMocks.error_429_rate_limit(),
            'expected_error': True,
            'expected_message_contains': 'rate limit'
        }

    @staticmethod
    def scenario_timeout_fallback():
        """Scenario: Timeout triggers fallback."""
        return {
            'hacienda_timeout': True,
            'gometa': GoMetaAPIMocks.success_response_inscrito(),
            'expected_source': 'gometa'
        }


class BatchLookupMocks:
    """Mocks for batch lookup scenarios."""

    @staticmethod
    def batch_all_success(count=10):
        """All lookups succeed."""
        results = []
        for i in range(count):
            mock = Mock()
            mock.status_code = 200
            mock.json.return_value = {
                'nombre': f'Batch Company {i} SA',
                'tipoIdentificacion': '02',
                'regimen': {'descripcion': 'General'},
                'situacion': 'INSCRITO',
            }
            results.append(mock)
        return results

    @staticmethod
    def batch_partial_failures(success_count=7, fail_count=3):
        """Mixed success and failures."""
        results = []

        # Success responses
        for i in range(success_count):
            mock = Mock()
            mock.status_code = 200
            mock.json.return_value = {
                'nombre': f'Success Company {i}',
                'tipoIdentificacion': '02',
                'regimen': {'descripcion': 'General'},
                'situacion': 'INSCRITO',
            }
            results.append(mock)

        # Failure responses
        for i in range(fail_count):
            mock = Mock()
            mock.status_code = 500
            results.append(mock)

        return results


class ConcurrentLookupMocks:
    """Mocks for concurrent lookup scenarios."""

    @staticmethod
    def thread_safe_responses(thread_count=5):
        """Generate unique responses for each thread."""
        responses = []
        for i in range(thread_count):
            mock = Mock()
            mock.status_code = 200
            mock.json.return_value = {
                'nombre': f'Thread {i} Company',
                'tipoIdentificacion': '02',
                'regimen': {'descripcion': 'General'},
                'situacion': 'INSCRITO',
            }
            responses.append(mock)
        return responses


class EdgeCaseMocks:
    """Mocks for edge cases and error scenarios."""

    @staticmethod
    def empty_response():
        """Empty API response."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {}
        return mock

    @staticmethod
    def missing_required_fields():
        """Response missing required fields."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            'nombre': 'Incomplete Data',
            # Missing tipoIdentificacion, situacion, etc.
        }
        return mock

    @staticmethod
    def special_characters_in_name():
        """Company name with special characters."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            'nombre': 'Café & Restaurant "El Típico" S.A.',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }
        return mock

    @staticmethod
    def very_long_name():
        """Company name exceeding typical limits."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            'nombre': 'A' * 300,  # 300 character name
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }
        return mock

    @staticmethod
    def unicode_characters():
        """Response with Unicode characters."""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            'nombre': 'Empresa 中文 العربية 日本語 SA',
            'tipoIdentificacion': '02',
            'regimen': {'descripcion': 'General'},
            'situacion': 'INSCRITO',
        }
        return mock
