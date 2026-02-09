# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import common
from . import test_payment_provider
from . import test_payment_transaction
from . import test_controller

# TiloPay-specific tests (depend on TiloPayMockFactory in common.py)
# These are Phase 3+ tests that require the mock infrastructure
import logging
_logger = logging.getLogger(__name__)

try:
    from . import test_tilopay_api_client
except ImportError as e:
    _logger.warning("Skipping test_tilopay_api_client: %s", e)

try:
    from . import test_tilopay_integration
except ImportError as e:
    _logger.warning("Skipping test_tilopay_integration: %s", e)

try:
    from . import test_tilopay_payment_provider
except ImportError as e:
    _logger.warning("Skipping test_tilopay_payment_provider: %s", e)

try:
    from . import test_tilopay_payment_transaction
except ImportError as e:
    _logger.warning("Skipping test_tilopay_payment_transaction: %s", e)

from . import test_tilopay_webhook
