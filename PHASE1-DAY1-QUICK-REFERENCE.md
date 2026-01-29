# Phase 1 Day 1: Quick Reference Guide

## Message Tracking Pattern

### Success Message Pattern
```python
self.message_post(
    body=_('✓ Operation completed successfully<br/>Details: %s') % details,
    message_type='notification',
)
```

### Error Message Pattern
```python
self.message_post(
    body=_('✗ Operation failed: %s') % error_msg,
    message_type='notification',
)
```

---

## Logging Levels

### Info Level
Use for major operations and their outcomes:
```python
_logger.info(f'Starting XML generation for document {self.name}')
_logger.info(f'Generated XML for document {self.name}, clave: {clave}')
```

### Debug Level
Use for detailed data and intermediate steps:
```python
_logger.debug(f'Generated clave: {clave}')
_logger.debug(f'XML content generated, length: {len(xml_content)} bytes')
_logger.debug(f'Using CIIU code: {ciiu_code}')
```

### Error Level
Use for failures with stack traces:
```python
_logger.error(f'Error generating XML for {self.name}: {error_msg}', exc_info=True)
```

### Warning Level
Use for non-critical issues:
```python
_logger.warning(f'Certificate expires soon! Days remaining: {days_until_expiry}')
```

### Critical Level
Use for urgent issues:
```python
_logger.critical(f'Certificate expires very soon! Days remaining: {days_until_expiry}')
```

---

## Action Method Template

```python
def action_operation(self):
    """Perform operation."""
    self.ensure_one()

    # Validation
    if self.state != 'expected_state':
        raise UserError(_('Invalid state for this operation'))

    try:
        _logger.info(f'Starting operation for document {self.name}')
        _logger.debug(f'Key parameter: {value}')

        # Perform operation
        result = self._do_operation()
        _logger.debug(f'Operation result: {result}')

        # Update state
        self.write({
            'state': 'new_state',
            'error_message': False,
        })

        # Post success message
        self.message_post(
            body=_('✓ Operation completed<br/>Result: %s') % result,
            message_type='notification',
        )

        _logger.info(f'Operation completed for {self.name}')
        return True

    except Exception as e:
        error_msg = str(e)
        _logger.error(f'Error in operation for {self.name}: {error_msg}', exc_info=True)

        # Update state and post error
        self.write({
            'state': 'error',
            'error_message': error_msg,
        })

        self.message_post(
            body=_('✗ Operation failed: %s') % error_msg,
            message_type='notification',
        )

        raise UserError(_('Error in operation: %s') % error_msg)
```

---

## Viewing Logs and Messages

### View Chatter Messages (UI)
1. Open any invoice with e-invoice document
2. Scroll to "Chatter" section at bottom
3. See operation history with checkmarks/crosses

### View Logs (Terminal)
```bash
# Follow logs in real-time
tail -f /path/to/odoo/logs/odoo.log

# Filter for e-invoice module
tail -f /path/to/odoo/logs/odoo.log | grep "l10n_cr"

# Filter by log level
tail -f /path/to/odoo/logs/odoo.log | grep "ERROR"
```

### View Logs (Odoo Shell)
```python
# Not typically used for logs, but can query message_post history
invoice = env['account.move'].browse(ID)
einvoice = invoice.l10n_cr_einvoice_document_id
messages = einvoice.message_ids
for msg in messages:
    print(f"{msg.date}: {msg.body}")
```

---

## Common Debugging Scenarios

### Scenario 1: XML Generation Fails
**Check:**
1. Chatter message for error details
2. Log for `ERROR: Error generating XML`
3. Debug logs for clave generation
4. Company CIIU code configuration

**Example Log Pattern:**
```
INFO: Starting XML generation for document INV/2024/001
DEBUG: Generated clave: 506...
ERROR: Error generating XML for INV/2024/001: Invalid CIIU code
```

### Scenario 2: Certificate Loading Fails
**Check:**
1. Log for `ERROR: Failed to load certificate`
2. Debug logs for certificate format detection
3. Company certificate configuration
4. Certificate password

**Example Log Pattern:**
```
INFO: Loading certificate for company My Company
DEBUG: Certificate data decoded, size: 3456 bytes
DEBUG: Certificate filename: cert.p12
INFO: Loading certificate as PKCS#12 format
ERROR: PKCS#12 loading failed: Incorrect password
```

### Scenario 3: Hacienda Submission Fails
**Check:**
1. Chatter message for error and retry count
2. Log for `ERROR: Error submitting to Hacienda`
3. Debug logs for payload and response
4. Network connectivity
5. Hacienda API credentials

**Example Log Pattern:**
```
INFO: Starting submission to Hacienda for document INV/2024/001
DEBUG: API URL: https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1/recepcion
DEBUG: Payload prepared - Sender: 02/1234567890, Receiver: 01/987654321
ERROR: Timeout submitting invoice to Hacienda: Request took too long
```

---

## Modified Files Summary

| File | Methods Modified | Changes |
|------|-----------------|---------|
| `einvoice_document.py` | 4 action methods | Added logging + message_post |
| `xml_generator.py` | 4 methods | Added debug/info logging |
| `hacienda_api.py` | 3 methods | Added comprehensive API logging |
| `certificate_manager.py` | 3 methods | Added certificate loading logging |

---

## Logging Best Practices

1. **Always log at operation start:**
   ```python
   _logger.info(f'Starting {operation} for {record}')
   ```

2. **Log key parameters:**
   ```python
   _logger.debug(f'Parameter: {value}')
   ```

3. **Log operation outcome:**
   ```python
   _logger.info(f'{operation} completed for {record}')
   ```

4. **Always use exc_info=True for errors:**
   ```python
   _logger.error(f'Error: {msg}', exc_info=True)
   ```

5. **Truncate large data:**
   ```python
   _logger.debug(f'Response: {data[:500]}...' if len(data) > 500 else f'Response: {data}')
   ```

---

## Testing Checklist

- [ ] Test XML generation success and failure
- [ ] Test XML signing success and failure
- [ ] Test Hacienda submission success and failure
- [ ] Test status check success and failure
- [ ] Verify chatter messages appear for all operations
- [ ] Verify logs contain appropriate level messages
- [ ] Verify error states are set correctly
- [ ] Verify retry count increments on submission failure
- [ ] Test certificate loading with valid certificate
- [ ] Test certificate loading with invalid certificate
- [ ] Test certificate expiration warnings

---

## Next Implementation: Retry Logic

For Phase 1 Day 2, implement automatic retry with exponential backoff:

```python
def action_submit_with_retry(self, max_retries=3):
    """Submit with automatic retry."""
    for attempt in range(max_retries):
        try:
            _logger.info(f'Submission attempt {attempt + 1} of {max_retries}')
            return self.action_submit_to_hacienda()
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                _logger.warning(f'Attempt {attempt + 1} failed, retrying in {wait_time}s')
                time.sleep(wait_time)
            else:
                _logger.error(f'All {max_retries} attempts failed')
                raise
```

---

## Conclusion

This quick reference provides the essential patterns and commands for working with the new message tracking and logging system. Keep this handy for implementing similar patterns in other modules.
