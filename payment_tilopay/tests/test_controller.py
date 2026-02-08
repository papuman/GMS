# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon
from odoo.addons.payment_tilopay import const
from odoo.addons.payment_tilopay.tests.common import TilopayCommon


# Patch path for _extract_amount_data to opt out of amount validation
# (TiloPay does not implement _extract_amount_data; the base returns {},
# which triggers a KeyError. Returning None opts out of the check.)
_EXTRACT_AMOUNT_DATA_PATH = (
    'odoo.addons.payment.models.payment_transaction'
    '.PaymentTransaction._extract_amount_data'
)


@tagged('post_install', '-at_install')
class TestTilopayController(TilopayCommon, PaymentHttpCommon):

    # ===================================================================
    # Return route (GET /payment/tilopay/return)
    # ===================================================================

    @mute_logger(
        'odoo.addons.payment_tilopay.controllers.main',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_return_route_confirms_transaction(self):
        """A valid return with code=1 should set the tx state to 'done'."""
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(const.PAYMENT_RETURN_ROUTE)
        with patch(
            'odoo.addons.payment_tilopay.models.payment_transaction'
            '.PaymentTransaction._tilopay_verify_hash',
            return_value=True,
        ), patch(_EXTRACT_AMOUNT_DATA_PATH, return_value=None):
            response = self._make_http_get_request(url, params=self.return_data)
        self.assertEqual(
            response.status_code, 200,
            msg="Return route should respond with 200 (after redirect to /payment/status).",
        )
        self.assertEqual(tx.state, 'done')

    @mute_logger(
        'odoo.addons.payment_tilopay.controllers.main',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_return_route_pending_transaction(self):
        """A return with code='Pending' should set the tx to pending state."""
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(const.PAYMENT_RETURN_ROUTE)
        pending_data = dict(self.return_data, code='Pending', description='Awaiting confirmation')
        with patch(
            'odoo.addons.payment_tilopay.models.payment_transaction'
            '.PaymentTransaction._tilopay_verify_hash',
            return_value=True,
        ), patch(_EXTRACT_AMOUNT_DATA_PATH, return_value=None):
            self._make_http_get_request(url, params=pending_data)
        self.assertEqual(tx.state, 'pending')

    @mute_logger(
        'odoo.addons.payment_tilopay.controllers.main',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_return_route_cancelled_transaction(self):
        """A return with wp_cancel=yes should set the tx to cancelled."""
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(const.PAYMENT_RETURN_ROUTE)
        cancel_data = dict(self.return_data, code='', wp_cancel='yes')
        with patch(
            'odoo.addons.payment_tilopay.models.payment_transaction'
            '.PaymentTransaction._tilopay_verify_hash',
            return_value=True,
        ), patch(_EXTRACT_AMOUNT_DATA_PATH, return_value=None):
            self._make_http_get_request(url, params=cancel_data)
        self.assertEqual(tx.state, 'cancel')

    @mute_logger(
        'odoo.addons.payment_tilopay.controllers.main',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_return_route_invalid_hash_does_not_process(self):
        """If hash verification fails, the transaction should not be processed."""
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(const.PAYMENT_RETURN_ROUTE)
        with patch(
            'odoo.addons.payment_tilopay.models.payment_transaction'
            '.PaymentTransaction._tilopay_verify_hash',
            side_effect=Exception("Invalid hash"),
        ):
            self._make_http_get_request(url, params=self.return_data)
        self.assertEqual(
            tx.state, 'draft',
            msg="Transaction should remain in draft if hash verification fails.",
        )

    # ===================================================================
    # Webhook route (POST /payment/tilopay/webhook)
    # ===================================================================

    @mute_logger(
        'odoo.addons.payment_tilopay.controllers.main',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_webhook_confirms_transaction(self):
        """A valid webhook notification with code=1 should set the tx to done."""
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(const.WEBHOOK_ROUTE)
        with patch(
            'odoo.addons.payment_tilopay.models.payment_transaction'
            '.PaymentTransaction._tilopay_verify_hash',
            return_value=True,
        ), patch(_EXTRACT_AMOUNT_DATA_PATH, return_value=None):
            response = self._make_json_request(url, data=self.webhook_data)
        self.assertEqual(
            response.status_code, 200,
            msg="Webhook should respond with 200.",
        )
        self.assertEqual(tx.state, 'done')

    @mute_logger(
        'odoo.addons.payment_tilopay.controllers.main',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_webhook_triggers_hash_verification(self):
        """Receiving a webhook should trigger hash verification."""
        self._create_transaction(flow='redirect')
        url = self._build_url(const.WEBHOOK_ROUTE)
        with patch(
            'odoo.addons.payment_tilopay.models.payment_transaction'
            '.PaymentTransaction._tilopay_verify_hash',
            return_value=True,
        ) as hash_mock, patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction._process',
        ):
            self._make_json_request(url, data=self.webhook_data)
            self.assertEqual(
                hash_mock.call_count, 1,
                msg="Hash verification should be called exactly once per webhook.",
            )

    @mute_logger(
        'odoo.addons.payment_tilopay.controllers.main',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_webhook_no_matching_tx_does_not_crash(self):
        """A webhook for a non-existent transaction should not raise errors."""
        url = self._build_url(const.WEBHOOK_ROUTE)
        data = dict(self.webhook_data, orderNumber='NONEXISTENT-REF-999')
        # Should not raise -- controller gracefully handles missing tx
        response = self._make_json_request(url, data=data)
        self.assertEqual(response.status_code, 200)

    @mute_logger(
        'odoo.addons.payment_tilopay.controllers.main',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_webhook_invalid_hash_does_not_process(self):
        """If webhook hash verification fails, tx should not be updated."""
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(const.WEBHOOK_ROUTE)
        with patch(
            'odoo.addons.payment_tilopay.models.payment_transaction'
            '.PaymentTransaction._tilopay_verify_hash',
            side_effect=Exception("Invalid hash"),
        ):
            self._make_json_request(url, data=self.webhook_data)
        self.assertEqual(
            tx.state, 'draft',
            msg="Transaction should stay in draft if webhook hash is invalid.",
        )

    @mute_logger(
        'odoo.addons.payment_tilopay.controllers.main',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_webhook_error_status_sets_error(self):
        """A webhook with an error status code should set the tx to error."""
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(const.WEBHOOK_ROUTE)
        error_data = dict(
            self.webhook_data, code='99', description='Card declined',
        )
        with patch(
            'odoo.addons.payment_tilopay.models.payment_transaction'
            '.PaymentTransaction._tilopay_verify_hash',
            return_value=True,
        ), patch(_EXTRACT_AMOUNT_DATA_PATH, return_value=None):
            self._make_json_request(url, data=error_data)
        self.assertEqual(tx.state, 'error')
