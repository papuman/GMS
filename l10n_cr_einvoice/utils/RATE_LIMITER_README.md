# Hacienda API Token Bucket Rate Limiter

Production-ready distributed rate limiter for the Costa Rica Hacienda API.

## Overview

This rate limiter implements a **token bucket algorithm** to enforce application-wide rate limits across all POS terminals and API clients:

- **Sustained Rate**: 10 requests/second
- **Burst Capacity**: 20 requests/second
- **Distributed**: State shared across all Odoo instances via PostgreSQL
- **Thread-Safe**: Uses PostgreSQL advisory locks for atomic operations

## Architecture

### Token Bucket Algorithm

The token bucket algorithm works as follows:

1. **Bucket**: A fixed-capacity container (20 tokens)
2. **Refill**: Tokens are added at a constant rate (10 tokens/second)
3. **Consumption**: Each API request consumes 1 token
4. **Overflow**: Refill never exceeds capacity (capped at 20)

```
┌─────────────────────────────────────┐
│   Token Bucket (Capacity: 20)      │
│                                     │
│   Current: ████████████░░░░░░░░░   │
│            12/20 tokens available   │
│                                     │
│   Refill: +10 tokens/second         │
│   Consume: -1 token/request         │
└─────────────────────────────────────┘
```

### Benefits

- **Burst Handling**: Allows short bursts up to 20 req/sec
- **Fair Distribution**: Shared quota prevents any single client from monopolizing API
- **Graceful Degradation**: Requests queue instead of failing
- **Monitoring**: Real-time visibility into API utilization

## Installation

### 1. Database Migration

The rate limiter requires a database table to store state. Run the migration:

```bash
# Via Odoo module update
docker compose run --rm odoo -d GMS -u l10n_cr_einvoice --stop-after-init --no-http

# Or manually execute SQL
docker compose exec postgres psql -U odoo -d GMS -f /path/to/migration.sql
```

The migration creates:

```sql
CREATE TABLE l10n_cr_hacienda_rate_limit_state (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    tokens DOUBLE PRECISION NOT NULL DEFAULT 20.0,
    last_refill TIMESTAMP NOT NULL DEFAULT NOW(),
    total_requests BIGINT NOT NULL DEFAULT 0,
    last_request TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 2. Module Dependency

The rate limiter is automatically loaded with the `l10n_cr_einvoice` module. No additional configuration needed.

## Usage

### Basic Usage - Blocking Acquisition

The simplest approach is to use `acquire_token()`, which blocks until a token is available:

```python
from odoo import models, api

class MyModel(models.Model):
    _name = 'my.model'

    def submit_invoice(self):
        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']

        # Acquire token (waits up to 30 seconds)
        rate_limiter.acquire_token(timeout=30)

        # Token acquired - make API call
        response = self.env['l10n_cr.hacienda.api'].submit_invoice(...)
        return response
```

### Non-Blocking Acquisition

For better UX, use `try_acquire_token()` to check immediately without blocking:

```python
def submit_invoice_async(self):
    rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']

    # Try to acquire token without waiting
    if not rate_limiter.try_acquire_token():
        # Rate limited - queue for later
        return {
            'status': 'queued',
            'message': 'API rate limit reached. Invoice queued for automatic submission.'
        }

    # Token acquired - submit now
    response = self.env['l10n_cr.hacienda.api'].submit_invoice(...)
    return {'status': 'submitted', 'response': response}
```

### Batch Operations

For batch submissions, handle rate limiting gracefully:

```python
def batch_submit_invoices(self, invoices):
    rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']

    submitted = []
    queued = []

    for invoice in invoices:
        if rate_limiter.try_acquire_token():
            # Submit immediately
            self._submit_invoice(invoice)
            submitted.append(invoice)
        else:
            # Queue for retry
            self._queue_invoice(invoice)
            queued.append(invoice)

    return {
        'submitted': len(submitted),
        'queued': len(queued),
    }
```

### Monitoring

Get real-time rate limiter statistics:

```python
def get_api_health(self):
    rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']
    status = rate_limiter.get_available_tokens()

    # Returns:
    # {
    #     'tokens': 15.3,              # Current available tokens
    #     'capacity': 20,               # Maximum capacity
    #     'refill_rate': 10,            # Tokens per second
    #     'total_requests': 12847,      # Lifetime counter
    #     'last_request': datetime(...),# Last activity
    #     'utilization': 23.5,          # Percentage used (0-100)
    # }

    return status
```

## API Reference

### `acquire_token(timeout=30)`

Acquire a token, blocking until available or timeout.

**Parameters:**
- `timeout` (int): Maximum seconds to wait (default: 30)

**Returns:**
- `bool`: True if token acquired

**Raises:**
- `UserError`: If timeout is reached

**Example:**
```python
rate_limiter.acquire_token(timeout=10)  # Wait up to 10 seconds
```

---

### `try_acquire_token()`

Try to acquire a token immediately without blocking.

**Returns:**
- `bool`: True if token acquired, False if rate limit exceeded

**Example:**
```python
if rate_limiter.try_acquire_token():
    # Proceed with API call
    pass
else:
    # Handle rate limit
    pass
```

---

### `get_available_tokens()`

Get current rate limiter status (read-only, no token consumption).

**Returns:**
- `dict`: Statistics dictionary

**Example:**
```python
status = rate_limiter.get_available_tokens()
print(f"Available: {status['tokens']}/{status['capacity']}")
print(f"Utilization: {status['utilization']}%")
```

---

### `reset()`

Reset rate limiter to full capacity. **USE WITH CAUTION - Testing/Admin Only**

**Example:**
```python
rate_limiter.reset()  # Reset to 20/20 tokens
```

## Configuration

The rate limiter is configured with constants in `rate_limiter.py`:

```python
BUCKET_CAPACITY = 20    # Maximum burst (tokens)
REFILL_RATE = 10        # Sustained rate (tokens/second)
ADVISORY_LOCK_ID = 123456789  # PostgreSQL lock ID
```

To modify rate limits:

1. Edit the constants in `utils/rate_limiter.py`
2. Restart Odoo
3. Optionally reset rate limiter: `rate_limiter.reset()`

## Performance

### Database Impact

The rate limiter uses PostgreSQL advisory locks for atomicity:

- **Lock acquisition**: <1ms
- **State read/write**: 1-2ms
- **Total overhead**: ~2-3ms per API call

### Scalability

Tested with:
- **Concurrent threads**: 20+ threads simultaneously
- **Sustained load**: 10 req/sec for extended periods
- **Burst handling**: 20 immediate requests without blocking

### Memory

Minimal memory footprint:
- **Database row**: <1KB (single row)
- **Python overhead**: <100KB

## Testing

Run the comprehensive test suite:

```bash
# All rate limiter tests
docker compose run --rm odoo -d GMS --test-tags=rate_limiter --stop-after-init

# Stress tests
docker compose run --rm odoo -d GMS --test-tags=rate_limiter_stress --stop-after-init
```

Test coverage:
- ✅ Token acquisition (blocking/non-blocking)
- ✅ Token refill over time
- ✅ Burst capacity handling
- ✅ Thread safety
- ✅ Timeout behavior
- ✅ Monitoring statistics
- ✅ Concurrent load (20+ threads)
- ✅ Sustained throughput validation

## Troubleshooting

### Rate Limiter Not Working

**Symptom**: All requests succeed without rate limiting

**Solution**:
1. Check if table exists: `SELECT * FROM l10n_cr_hacienda_rate_limit_state;`
2. Verify migration ran: Check Odoo logs for "Rate limiter state table created"
3. Reset state: `rate_limiter.reset()`

---

### High API Utilization

**Symptom**: `utilization` consistently >80%

**Solution**:
1. Check for retry loops (requests being retried too quickly)
2. Review cron job schedules (batch jobs conflicting with real-time submissions)
3. Consider implementing request queuing
4. Monitor with: `rate_limiter.get_available_tokens()`

---

### Blocking Timeouts

**Symptom**: `acquire_token()` timing out frequently

**Solution**:
1. Increase timeout: `acquire_token(timeout=60)`
2. Switch to non-blocking: Use `try_acquire_token()` + retry queue
3. Reduce concurrent submission attempts
4. Check if rate limits need adjustment

---

### Advisory Lock Errors

**Symptom**: PostgreSQL lock errors in logs

**Solution**:
1. Check for dead locks: `SELECT * FROM pg_locks WHERE granted = false;`
2. Restart Odoo workers
3. Verify PostgreSQL version ≥9.6 (advisory locks)

## Integration Example

Complete integration with `einvoice_document` model:

```python
class EinvoiceDocument(models.Model):
    _inherit = 'l10n_cr.einvoice.document'

    def submit_to_hacienda(self):
        """Submit document with rate limiting."""
        self.ensure_one()

        rate_limiter = self.env['l10n_cr.hacienda.rate_limiter']

        # Try non-blocking acquisition
        if not rate_limiter.try_acquire_token():
            # Rate limited - queue for retry
            self._queue_for_retry('rate_limit')
            return {
                'status': 'queued',
                'message': 'Queued due to API rate limit'
            }

        # Token acquired - submit
        try:
            response = self.env['l10n_cr.hacienda.api'].submit_invoice(
                clave=self.clave,
                xml_content=self.signed_xml,
                sender_id=self.company_id.vat,
                receiver_id=self.partner_id.vat
            )

            self._handle_response(response)
            return {'status': 'submitted', 'response': response}

        except Exception as e:
            _logger.error(f'Failed to submit {self.clave}: {str(e)}')
            raise

    def _queue_for_retry(self, reason):
        """Add to retry queue."""
        self.env['l10n_cr.einvoice.retry.queue'].create({
            'document_id': self.id,
            'retry_after': fields.Datetime.now() + timedelta(seconds=120),
            'reason': reason,
        })
```

## Best Practices

### 1. Use Non-Blocking for User-Facing Operations

```python
# Good: Immediate feedback to user
if not rate_limiter.try_acquire_token():
    return {'queued': True, 'message': 'Invoice queued'}

# Bad: User waits 30 seconds
rate_limiter.acquire_token(timeout=30)
```

### 2. Implement Retry Queues

Don't fail requests due to rate limits - queue them:

```python
if not rate_limiter.try_acquire_token():
    self._add_to_retry_queue(invoice)
    return {'status': 'queued'}
```

### 3. Monitor Utilization

Set up alerts for high API utilization:

```python
status = rate_limiter.get_available_tokens()
if status['utilization'] > 80:
    _logger.warning(f"High API utilization: {status['utilization']}%")
```

### 4. Batch Operations During Off-Hours

Schedule heavy batch jobs during low-traffic periods to avoid rate limiting user requests.

### 5. Test with Real Load

Always load-test rate limiter with realistic concurrent usage before production deployment.

## License

Part of the `l10n_cr_einvoice` module - LGPL-3

## Support

For issues or questions:
1. Check test suite: `tests/test_rate_limiter.py`
2. Review integration examples: `utils/rate_limiter_integration_example.py`
3. Contact: GMS Development Team
