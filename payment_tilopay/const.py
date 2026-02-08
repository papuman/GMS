# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Base URL for all Tilopay API calls (same for sandbox and production;
# environment is determined by credentials, not URL).
API_URL = 'https://app.tilopay.com'

# Controller routes
PAYMENT_RETURN_ROUTE = '/payment/tilopay/return'
WEBHOOK_ROUTE = '/payment/tilopay/webhook'

# Default payment method codes activated for new TiloPay providers.
# TiloPay supports credit/debit cards and SINPE Movil (mapped to bank_transfer).
DEFAULT_PAYMENT_METHOD_CODES = {'card', 'bank_transfer'}

# processPayment response type codes (Tilopay returns these as STRINGS, not ints)
PAYMENT_RESPONSE_REDIRECT = '100'   # Success — url contains hosted payment page
PAYMENT_RESPONSE_DIRECT = '200'     # Direct approval — url contains redirect with results
PAYMENT_RESPONSE_LICENSE = '300'    # License error
# '400'-'404' are various errors

# processModification type codes
MODIFICATION_CAPTURE = '1'
MODIFICATION_REFUND = '2'
MODIFICATION_REVERSAL = '3'
