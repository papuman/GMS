# -*- coding: utf-8 -*-
"""
Override IAP tools to prevent external calls to iap.odoo.com
"""
import logging
import uuid

from odoo import exceptions, modules
from odoo.addons.iap.tools import iap_tools

_logger = logging.getLogger(__name__)

# Save the original function in case we need to restore it
_original_iap_jsonrpc = iap_tools.iap_jsonrpc


def _iap_jsonrpc_disabled(url, method='call', params=None, timeout=15):
    """
    Replacement for iap_jsonrpc that stubs out all external calls.

    This function intercepts all IAP JSON-RPC calls and returns mock responses
    instead of making actual network requests to iap.odoo.com.

    :param url: The IAP endpoint URL (will be logged but not called)
    :param method: JSON-RPC method (ignored)
    :param params: Parameters for the call (may be inspected for mock response)
    :param timeout: Request timeout (ignored)
    :return: Mock response appropriate for the endpoint
    """
    _logger.info('IAP DISABLED: Intercepted call to %s (method=%s)', url, method)
    _logger.debug('IAP DISABLED: Call params: %s', params)

    # During tests, maintain original behavior of raising AccessError
    if modules.module.current_test:
        raise exceptions.AccessError("Unavailable during tests.")

    # Parse the URL to determine what kind of mock response to return
    if '/iap/1/balance' in url:
        # Balance check - return a high number to prevent credit errors
        _logger.info('IAP DISABLED: Returning mock balance (999999)')
        return 999999

    elif '/iap/1/get-accounts-information' in url:
        # Account information - return minimal info for each account token
        _logger.info('IAP DISABLED: Returning mock account information')
        result = {}
        if params and 'iap_accounts' in params:
            for account in params['iap_accounts']:
                token = account.get('token')
                if token:
                    result[token] = {
                        'balance': 999999,
                        'warning_threshold': 0,
                        'registered': 'registered',
                    }
        return result

    elif '/iap/1/update-warning-email-alerts' in url:
        # Warning email configuration - just acknowledge success
        _logger.info('IAP DISABLED: Acknowledging warning email update (no-op)')
        return {'success': True}

    elif '/iap/1/credit' in url:
        # Credit purchase URL - not a JSON-RPC call, shouldn't reach here
        _logger.warning('IAP DISABLED: Credit URL endpoint called via jsonrpc (unexpected)')
        return {'url': '#'}

    else:
        # Unknown endpoint - return generic success response
        _logger.info('IAP DISABLED: Unknown endpoint, returning generic success')
        return {
            'success': True,
            'message': 'IAP is disabled - this is a mock response',
            'id': uuid.uuid4().hex,
        }


# Monkey-patch the iap_jsonrpc function
_logger.info('IAP DISABLED: Overriding iap_jsonrpc function to disable external calls')
iap_tools.iap_jsonrpc = _iap_jsonrpc_disabled
