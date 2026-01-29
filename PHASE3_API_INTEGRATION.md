# Phase 3: Hacienda API Integration - Complete Implementation

## Overview

Phase 3 implements complete integration with Costa Rica's Hacienda API for electronic invoice submission and status tracking. This phase includes robust retry logic, comprehensive error handling, and proper response parsing.

## Implementation Status

**Status:** ✅ COMPLETE

**File:** `/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice/models/hacienda_api.py`

## Features Implemented

### 1. API Connection Management

- **Sandbox Environment:** `https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1`
- **Production Environment:** `https://api.comprobanteselectronicos.go.cr/recepcion/v1`
- **Authentication:** HTTP Basic Authentication with credentials from company settings
- **Dynamic URL Selection:** Automatically switches between sandbox/production based on company configuration

### 2. Invoice Submission (`submit_invoice`)

```python
api_client = self.env['l10n_cr.hacienda.api']
response = api_client.submit_invoice(
    clave='50-digit-key',
    xml_content='<signed XML>',
    sender_id='3101234567',
    receiver_id='123456789'
)
```

**Features:**
- Base64 encoding of XML content
- Automatic identification type detection (01-05)
- Costa Rica timezone formatting (UTC-6)
- Clean identification number formatting
- Retry logic with exponential backoff
- Comprehensive error handling

**Payload Structure:**
```json
{
    "clave": "50-digit-electronic-key",
    "fecha": "2024-01-15T10:30:00-06:00",
    "emisor": {
        "tipoIdentificacion": "02",
        "numeroIdentificacion": "3101234567"
    },
    "receptor": {
        "tipoIdentificacion": "01",
        "numeroIdentificacion": "123456789"
    },
    "comprobanteXml": "base64-encoded-xml"
}
```

### 3. Status Checking (`check_status`)

```python
response = api_client.check_status(clave='50-digit-key')
```

**Features:**
- Validates clave format (must be 50 digits)
- Retry logic for network resilience
- Automatic response decoding
- Status normalization

**Response States:**
- `aceptado` - Document accepted by Hacienda
- `rechazado` - Document rejected
- `procesando` - Still processing
- `recibido` - Received but not processed

### 4. Retry Logic (`_make_request_with_retry`)

**Configuration:**
```python
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 2  # seconds
RETRY_BACKOFF_FACTOR = 2  # exponential multiplier
```

**Retry Strategy:**
- Attempt 1: Immediate
- Attempt 2: Wait 2 seconds
- Attempt 3: Wait 4 seconds
- Rate limiting: Double the delay

**Error Handling by Status Code:**

| Code | Action | Retry? | Description |
|------|--------|--------|-------------|
| 200/201 | Success | No | Request successful |
| 400 | Fail | No | Validation error - fix and resubmit |
| 401 | Fail | No | Authentication failed - check credentials |
| 403 | Fail | No | Authorization error - insufficient permissions |
| 404 | Fail | No | Document not found |
| 429 | Retry | Yes | Rate limited - double delay |
| 500+ | Retry | Yes | Server error - temporary issue |

**Network Error Handling:**
- `Timeout` - Retry with backoff
- `ConnectionError` - Retry with backoff
- `RequestException` - Retry with backoff

### 5. Response Parsing (`_parse_response`)

**Enhanced Features:**
- Automatic JSON parsing
- Base64 decoding of `respuesta-xml` field
- Status normalization to lowercase
- Error detail extraction
- Fallback for invalid JSON

**Response Structure:**
```python
{
    'ind-estado': 'aceptado',
    'respuesta-xml': 'base64-encoded-message',
    'respuesta-xml-decoded': 'decoded-message',
    'clave': '50-digit-key',
    'fecha': '2024-01-15T10:30:00',
    'error_details': 'optional-error-info'
}
```

### 6. Error Parsing (`_parse_error`)

**Comprehensive Error Field Detection:**
- `message`
- `error`
- `mensaje`
- `detalle-mensaje`
- `descripcion`
- `errorMessage`
- `errors` (array handling)

**Features:**
- Multi-field error extraction
- Array error concatenation
- JSON decode error handling
- Error message length limiting (500 chars)

### 7. Helper Methods

#### Acceptance Message Retrieval
```python
response = api_client.get_acceptance_message(clave='50-digit-key')
# Returns decoded acceptance/rejection message
```

#### Status Checkers
```python
if api_client.is_accepted(response):
    # Document accepted

if api_client.is_rejected(response):
    # Document rejected

if api_client.is_processing(response):
    # Still processing
```

#### Identification Type Detection
```python
id_type = api_client._get_id_type('123456789')
# Returns: '01' (Cédula Física)
```

**Type Mapping:**
- 9 digits → `01` (Cédula Física)
- 10 digits starting with 3 → `02` (Cédula Jurídica)
- 10 digits not starting with 3 → `04` (NITE)
- 11-12 digits → `03` (DIMEX)
- Other → `05` (Extranjero)

#### Connection Testing
```python
result = api_client.test_connection()
# Returns: {'success': True/False, 'message': '...', 'environment': '...'}
```

**Features:**
- Validates credentials are configured
- Tests authentication
- Reports environment (sandbox/production)
- Returns API base URL
- Handles timeouts and connection errors

## Integration with E-Invoice Document

The API client integrates with `einvoice_document.py`:

```python
def action_submit_to_hacienda(self):
    """Submit the signed XML to Hacienda API."""
    api_client = self.env['l10n_cr.hacienda.api']

    response = api_client.submit_invoice(
        clave=self.clave,
        xml_content=self.signed_xml,
        sender_id=self.company_id.vat,
        receiver_id=self.partner_id.vat or '',
    )

    self._process_hacienda_response(response)
```

## Configuration

### Company Settings Required

```python
# In res.company
l10n_cr_hacienda_env = 'sandbox'  # or 'production'
l10n_cr_hacienda_username = 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr'
l10n_cr_hacienda_password = 'your-password'
```

### Sandbox Credentials

```
URL: https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1
Username: cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr
Password: e8KLJRHzRA1P0W2ybJ5T
```

## Error Scenarios and Handling

### 1. Authentication Errors
```
Error: Authentication failed. Please check API credentials.
Action: Verify username/password in company settings
Retry: No
```

### 2. Validation Errors
```
Error: Validation error: [specific validation message]
Action: Fix XML or payload data
Retry: No
```

### 3. Network Errors
```
Error: Connection error / Request timeout
Action: Automatic retry with exponential backoff
Retry: Yes (up to 3 attempts)
```

### 4. Rate Limiting
```
Error: Rate limit exceeded
Action: Retry with doubled delay
Retry: Yes (up to 3 attempts)
```

### 5. Server Errors (5xx)
```
Error: Server error: [error message]
Action: Automatic retry with backoff
Retry: Yes (up to 3 attempts)
```

## Logging

The module implements comprehensive logging:

```python
_logger.info(f'Attempt {attempt}/{MAX_RETRY_ATTEMPTS}: {operation}')
_logger.debug(f'Request URL: {url}')
_logger.debug(f'Response status: {response.status_code}')
_logger.debug(f'Response body: {response.text[:500]}...')
_logger.warning(f'Rate limited on attempt {attempt}')
_logger.error(f'Authentication failed for {operation}')
```

**Log Levels:**
- `INFO` - Normal operations, retry attempts
- `DEBUG` - Request/response details
- `WARNING` - Retryable errors, rate limits
- `ERROR` - Permanent failures, authentication issues

## Testing

**Test Script:** `/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/test_phase3_api.py`

**Test Coverage:**
1. ✅ Connection testing with credential validation
2. ✅ Document submission to Hacienda
3. ✅ Status checking
4. ✅ Retry logic validation
5. ✅ Error handling scenarios
6. ✅ Response parsing and decoding
7. ✅ Helper method functionality
8. ✅ ID type detection

**Run Tests:**
```bash
python3 test_phase3_api.py
```

## Usage Examples

### Example 1: Submit Invoice
```python
# In Odoo shell or code
api_client = env['l10n_cr.hacienda.api']

response = api_client.submit_invoice(
    clave='50618010600001010001431130000100001000000001',
    xml_content=signed_xml,
    sender_id='3101234567',
    receiver_id='123456789'
)

if api_client.is_accepted(response):
    print("Invoice accepted!")
elif api_client.is_rejected(response):
    print(f"Invoice rejected: {response.get('error_details')}")
else:
    print("Invoice still processing...")
```

### Example 2: Check Status
```python
response = api_client.check_status(
    clave='50618010600001010001431130000100001000000001'
)

print(f"Status: {response.get('ind-estado')}")
if response.get('respuesta-xml-decoded'):
    print(f"Message: {response['respuesta-xml-decoded']}")
```

### Example 3: Test Connection
```python
result = api_client.test_connection()

if result['success']:
    print(f"✅ Connected to {result['environment']}")
    print(f"URL: {result['url']}")
else:
    print(f"❌ Connection failed: {result['message']}")
```

## Performance Considerations

### Timeout Configuration
- Default request timeout: 30 seconds
- Connection test timeout: 10 seconds

### Retry Impact
- Maximum retry time: ~14 seconds (2s + 4s + 8s)
- Rate limit scenario: ~28 seconds (4s + 8s + 16s)

### Recommendations
- Use async processing for bulk submissions
- Implement status polling with delays for large batches
- Monitor retry rates in production
- Consider queue-based submission for high volume

## Security

### Credential Storage
- Username and password stored in company settings
- Transmitted via HTTPS only
- Basic Auth encoding in Authorization header

### XML Transmission
- XML is base64 encoded before transmission
- Signed XML ensures integrity
- HTTPS ensures confidentiality

### Error Messages
- Sensitive data not logged in error messages
- Credential values never appear in logs
- Error messages truncated to 500 characters

## Future Enhancements

### Potential Improvements
1. OAuth 2.0 support (if Hacienda implements it)
2. Webhook support for status callbacks
3. Batch submission API (if available)
4. Response caching for status checks
5. Async/background job processing
6. Metrics and monitoring dashboard
7. Advanced rate limiting with token bucket
8. Circuit breaker pattern for failing endpoints

## API Reference

### Main Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `submit_invoice()` | clave, xml_content, sender_id, receiver_id | dict | Submit invoice to Hacienda |
| `check_status()` | clave | dict | Check document status |
| `get_acceptance_message()` | clave | dict | Get decoded acceptance message |
| `is_accepted()` | response | bool | Check if accepted |
| `is_rejected()` | response | bool | Check if rejected |
| `is_processing()` | response | bool | Check if processing |
| `test_connection()` | none | dict | Test API connectivity |

### Internal Methods

| Method | Description |
|--------|-------------|
| `_make_request_with_retry()` | HTTP request with retry logic |
| `_get_base_url()` | Get API base URL |
| `_get_auth_headers()` | Build authentication headers |
| `_get_id_type()` | Detect identification type |
| `_parse_response()` | Parse successful response |
| `_parse_error()` | Parse error response |

## Troubleshooting

### Issue: Authentication Failed
**Solution:**
1. Check credentials in Settings > Companies
2. Verify environment setting (sandbox vs production)
3. Test with `test_connection()` method

### Issue: Validation Error
**Solution:**
1. Check XML is properly signed (Phase 2)
2. Verify clave format (50 digits)
3. Validate identification numbers
4. Review error details in response

### Issue: Timeout Errors
**Solution:**
1. Check network connectivity
2. Verify Hacienda API status
3. Monitor retry attempts in logs
4. Consider increasing timeout if consistent

### Issue: Rate Limiting
**Solution:**
1. Reduce submission frequency
2. Implement batch processing with delays
3. Monitor retry backoff in logs
4. Contact Hacienda for rate limit increase

## Dependencies

```python
import base64
import json
import logging
import requests
import time
from datetime import datetime
from odoo import models, api, _
from odoo.exceptions import UserError
```

**External:** `requests` library (standard in Odoo)

## Version History

- **v1.0** (Phase 3 Complete) - Full API integration with retry logic
- **v0.2** (Phase 2) - Digital signature support
- **v0.1** (Phase 1) - XML generation

## Support

For issues or questions:
1. Check logs: `_logger` messages in Odoo
2. Run test script: `test_phase3_api.py`
3. Review Hacienda API documentation
4. Test with `test_connection()` method

## Conclusion

Phase 3 API integration is complete with:
- ✅ Robust submission logic
- ✅ Comprehensive retry mechanism
- ✅ Proper error handling
- ✅ Response parsing with base64 decode
- ✅ Status checking
- ✅ Helper utilities
- ✅ Connection testing
- ✅ Production-ready code

**Next Phase:** Email notifications and PDF generation with QR codes.
