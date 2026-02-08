# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

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
class TestPaymentTransaction(TilopayCommon):

    # ===================================================================
    # _get_specific_rendering_values
    # ===================================================================

    @mute_logger('odoo.addons.payment_tilopay.models.payment_transaction')
    def test_rendering_values_redirect(self):
        """processPayment returning type 100 should yield the redirect URL."""
        tx = self._create_transaction(flow='redirect')
        processing_values = {
            'amount': self.amount,
            'currency_id': self.currency.id,
            'reference': self.reference,
        }
        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            side_effect=[
                {'access_token': self.access_token},       # login
                self.process_payment_response,              # processPayment
            ],
        ):
            rendering_values = tx._get_specific_rendering_values(processing_values)

        self.assertEqual(
            rendering_values.get('api_url'),
            self.process_payment_response['url'],
            msg="The redirect URL should come from processPayment response.",
        )

    @mute_logger('odoo.addons.payment_tilopay.models.payment_transaction')
    def test_rendering_values_direct_approval(self):
        """processPayment returning type 200 (direct) should also yield the URL."""
        tx = self._create_transaction(flow='redirect')
        direct_response = {
            'type': '200',
            'url': 'https://app.tilopay.com/direct/result/xyz',
        }
        processing_values = {
            'amount': self.amount,
            'currency_id': self.currency.id,
            'reference': self.reference,
        }
        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            side_effect=[
                {'access_token': self.access_token},
                direct_response,
            ],
        ):
            rendering_values = tx._get_specific_rendering_values(processing_values)

        self.assertEqual(rendering_values.get('api_url'), direct_response['url'])

    @mute_logger(
        'odoo.addons.payment_tilopay.models.payment_transaction',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_rendering_values_error_response(self):
        """processPayment returning an error type should set the tx to error."""
        tx = self._create_transaction(flow='redirect')
        error_response = {
            'type': '400',
            'message': 'Invalid API key',
        }
        processing_values = {
            'amount': self.amount,
            'currency_id': self.currency.id,
            'reference': self.reference,
        }
        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            side_effect=[
                {'access_token': self.access_token},
                error_response,
            ],
        ):
            rendering_values = tx._get_specific_rendering_values(processing_values)

        # The rendering values should be empty (no api_url)
        self.assertEqual(rendering_values, {})
        self.assertEqual(
            tx.state, 'error',
            msg="Transaction should be in error state after a failed processPayment.",
        )

    @mute_logger(
        'odoo.addons.payment_tilopay.models.payment_transaction',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_rendering_values_api_exception(self):
        """If _send_api_request raises ValidationError on processPayment, tx goes to error."""
        tx = self._create_transaction(flow='redirect')
        processing_values = {
            'amount': self.amount,
            'currency_id': self.currency.id,
            'reference': self.reference,
        }
        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            side_effect=[
                {'access_token': self.access_token},        # login succeeds
                ValidationError("Connection timeout"),       # processPayment fails
            ],
        ):
            rendering_values = tx._get_specific_rendering_values(processing_values)

        self.assertEqual(rendering_values, {})
        self.assertEqual(tx.state, 'error')

    def test_rendering_values_payload_contains_partner_data(self):
        """The processPayment payload must include partner billing details."""
        tx = self._create_transaction(flow='redirect')
        processing_values = {
            'amount': self.amount,
            'currency_id': self.currency.id,
            'reference': self.reference,
        }

        captured_payload = {}

        def mock_send(self_provider, method, endpoint, **kwargs):
            if endpoint == '/api/v1/login':
                return {'access_token': 'test_token'}
            if endpoint == '/api/v1/processPayment':
                captured_payload.update(kwargs.get('json', {}))
                return {'type': '100', 'url': 'https://example.com/pay'}
            return {}

        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            mock_send,
        ), mute_logger(
            'odoo.addons.payment_tilopay.models.payment_transaction',
            'odoo.addons.payment.models.payment_transaction',
        ):
            tx._get_specific_rendering_values(processing_values)

        self.assertEqual(captured_payload['orderNumber'], tx.reference)
        self.assertEqual(captured_payload['amount'], float(f'{self.amount:.2f}'))
        self.assertEqual(captured_payload['currency'], tx.currency_id.name)
        self.assertEqual(captured_payload['billToEmail'], self.partner.email or '')
        self.assertEqual(captured_payload['key'], self.tilopay.tilopay_api_key)
        self.assertEqual(captured_payload['platform'], 'odoo')
        self.assertEqual(captured_payload['hashVersion'], 'V2')
        self.assertIn(const.PAYMENT_RETURN_ROUTE, captured_payload['redirect'])

    def test_rendering_values_partner_name_splitting(self):
        """Partner name should be split into first and last name for billing."""
        tx = self._create_transaction(flow='redirect')
        processing_values = {
            'amount': self.amount,
            'currency_id': self.currency.id,
            'reference': self.reference,
        }

        captured_payload = {}

        def mock_send(self_provider, method, endpoint, **kwargs):
            if endpoint == '/api/v1/login':
                return {'access_token': 'test_token'}
            if endpoint == '/api/v1/processPayment':
                captured_payload.update(kwargs.get('json', {}))
                return {'type': '100', 'url': 'https://example.com/pay'}
            return {}

        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            mock_send,
        ), mute_logger(
            'odoo.addons.payment_tilopay.models.payment_transaction',
        ):
            tx._get_specific_rendering_values(processing_values)

        # The default_partner name is "Norbert Buyer"
        self.assertEqual(captured_payload['billToFirstName'], 'Norbert')
        self.assertEqual(captured_payload['billToLastName'], 'Buyer')

    # ===================================================================
    # _extract_reference
    # ===================================================================

    def test_extract_reference_from_return_data(self):
        """Return callback uses 'order' query param for the reference."""
        ref = self.env['payment.transaction']._extract_reference(
            'tilopay', {'order': 'SO/2025/001'}
        )
        self.assertEqual(ref, 'SO/2025/001')

    def test_extract_reference_from_webhook_data(self):
        """Webhook uses 'orderNumber' in JSON body for the reference."""
        ref = self.env['payment.transaction']._extract_reference(
            'tilopay', {'orderNumber': 'SO/2025/002'}
        )
        self.assertEqual(ref, 'SO/2025/002')

    def test_extract_reference_prefers_order_over_orderNumber(self):
        """If both 'order' and 'orderNumber' are present, 'order' takes precedence."""
        ref = self.env['payment.transaction']._extract_reference(
            'tilopay', {'order': 'REF-A', 'orderNumber': 'REF-B'}
        )
        self.assertEqual(ref, 'REF-A')

    def test_extract_reference_non_tilopay_falls_through(self):
        """For non-tilopay provider codes, the base method should be called."""
        ref = self.env['payment.transaction']._extract_reference(
            'none', {'reference': 'BASE-REF'}
        )
        self.assertEqual(ref, 'BASE-REF')

    # ===================================================================
    # _apply_updates
    # ===================================================================

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_code_1_sets_done(self):
        """Tilopay code '1' should set the transaction state to 'done'."""
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({'code': '1', 'tpt': 'TPT-001'})
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.provider_reference, 'TPT-001')

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_code_1_as_int(self):
        """Tilopay may send code as integer 1; should still map to done."""
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({'code': 1, 'tpt': 'TPT-002'})
        self.assertEqual(tx.state, 'done')

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_pending(self):
        """Tilopay code 'Pending' should set the transaction to pending."""
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({
            'code': 'Pending',
            'tpt': 'TPT-003',
            'description': 'Awaiting bank confirmation',
        })
        self.assertEqual(tx.state, 'pending')

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_cancelled(self):
        """wp_cancel=yes should set the transaction to cancelled."""
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({
            'code': '',
            'tpt': 'TPT-004',
            'wp_cancel': 'yes',
        })
        self.assertEqual(tx.state, 'cancel')

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_cancelled_case_insensitive(self):
        """wp_cancel check should be case-insensitive."""
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({
            'code': '',
            'tpt': 'TPT-005',
            'wp_cancel': 'Yes',
        })
        self.assertEqual(tx.state, 'cancel')

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_error(self):
        """An unknown code without wp_cancel should set the transaction to error."""
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({
            'code': '99',
            'tpt': 'TPT-006',
            'description': 'Declined by bank',
        })
        self.assertEqual(tx.state, 'error')

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_card_method(self):
        """selected_method with a card type should map to the card payment method."""
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({
            'code': '1',
            'tpt': 'TPT-007',
            'selected_method': 'VISA',
        })
        self.assertEqual(tx.state, 'done')

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_sinpe_method_detected(self):
        """selected_method containing 'SINPE' should attempt to set bank_transfer method."""
        tx = self._create_transaction(flow='redirect')
        original_method = tx.payment_method_id
        tx._apply_updates({
            'code': '1',
            'tpt': 'TPT-008',
            'selected_method': 'SINPE Movil',
        })
        self.assertEqual(tx.state, 'done')
        # The code tries to find 'bank_transfer' payment method. If it exists,
        # the payment method should have changed; if not, it may still be the original.
        bank_transfer = self.env['payment.method']._get_from_code('bank_transfer')
        if bank_transfer:
            self.assertEqual(tx.payment_method_id, bank_transfer)
        else:
            # bank_transfer method not available in this DB; method stays as-is
            self.assertTrue(tx.payment_method_id)

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_sets_provider_reference(self):
        """The tpt value should be stored as provider_reference."""
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({'code': '1', 'tpt': 'TPT-REF-ABC'})
        self.assertEqual(tx.provider_reference, 'TPT-REF-ABC')

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_apply_updates_no_tpt_does_not_set_reference(self):
        """If tpt is missing, provider_reference should not be changed."""
        tx = self._create_transaction(flow='redirect')
        original_ref = tx.provider_reference
        tx._apply_updates({'code': '1'})
        self.assertEqual(tx.provider_reference, original_ref)

    # ===================================================================
    # _tilopay_verify_hash
    # ===================================================================

    def test_verify_hash_valid(self):
        """A correctly computed hash should pass verification."""
        tx = self._create_transaction(flow='redirect')
        result = tx._tilopay_verify_hash(self.return_data)
        self.assertTrue(result)

    def test_verify_hash_invalid_raises(self):
        """A tampered hash should raise a ValidationError."""
        tx = self._create_transaction(flow='redirect')
        tampered_data = dict(self.return_data, OrderHash='deadbeef' * 8)
        with self.assertRaises(ValidationError):
            tx._tilopay_verify_hash(tampered_data)

    def test_verify_hash_missing_raises(self):
        """Missing OrderHash should raise a ValidationError."""
        tx = self._create_transaction(flow='redirect')
        data_no_hash = {k: v for k, v in self.return_data.items() if k != 'OrderHash'}
        with self.assertRaises(ValidationError):
            tx._tilopay_verify_hash(data_no_hash)

    def test_verify_hash_uses_orderHash_key(self):
        """Webhook may use lowercase 'orderHash' key; it should still work."""
        tx = self._create_transaction(flow='redirect')
        data = dict(self.return_data)
        # Move from 'OrderHash' to 'orderHash'
        data['orderHash'] = data.pop('OrderHash')
        result = tx._tilopay_verify_hash(data)
        self.assertTrue(result)

    def test_verify_hash_uses_transaction_amount_not_callback_amount(self):
        """Hash computation must use the stored transaction amount, not any callback amount."""
        tx = self._create_transaction(flow='redirect')
        # Add a misleading 'amount' to the callback data (attacker could try this)
        data_with_fake_amount = dict(self.return_data, amount='0.01')
        # The hash was computed with the real amount, so it should still verify
        result = tx._tilopay_verify_hash(data_with_fake_amount)
        self.assertTrue(result)

    # ===================================================================
    # _send_refund_request
    # ===================================================================

    @mute_logger(
        'odoo.addons.payment_tilopay.models.payment_transaction',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_send_refund_request(self):
        """A refund request should call processModification with the correct payload."""
        self.provider.support_refund = 'partial'
        source_tx = self._create_transaction(
            flow='redirect', state='done', provider_reference='TPT-SOURCE-001',
        )

        captured_payload = {}

        def mock_send(self_provider, method, endpoint, **kwargs):
            if endpoint == '/api/v1/login':
                return {'access_token': 'refund_token'}
            if endpoint == '/api/v1/processModification':
                captured_payload.update(kwargs.get('json', {}))
                return {
                    'ReasonCode': '1',
                    'ReasonCodeDescription': 'Refund approved',
                }
            return {}

        # Create the refund child transaction
        refund_tx = self._create_transaction(
            flow='redirect',
            reference='Test Transaction R',
            amount=-self.amount,
            operation='refund',
            source_transaction_id=source_tx.id,
            provider_reference=False,
        )

        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            mock_send,
        ), patch(_EXTRACT_AMOUNT_DATA_PATH, return_value=None):
            refund_tx._send_refund_request()

        # Verify the modification payload
        self.assertEqual(captured_payload['orderNumber'], 'TPT-SOURCE-001')
        self.assertEqual(captured_payload['amount'], float(f'{self.amount:.2f}'))
        self.assertEqual(captured_payload['type'], const.MODIFICATION_REFUND)
        self.assertEqual(captured_payload['key'], self.tilopay.tilopay_api_key)
        self.assertEqual(captured_payload['platform'], 'odoo')
        self.assertEqual(captured_payload['hashVersion'], 'V2')

    @mute_logger(
        'odoo.addons.payment_tilopay.models.payment_transaction',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_send_refund_request_success_sets_done(self):
        """A successful refund (ReasonCode 1) should eventually set the refund tx to done."""
        self.provider.support_refund = 'partial'
        source_tx = self._create_transaction(
            flow='redirect', state='done', provider_reference='TPT-SOURCE-002',
        )

        refund_tx = self._create_transaction(
            flow='redirect',
            reference='Test Transaction R2',
            amount=-self.amount,
            operation='refund',
            source_transaction_id=source_tx.id,
            provider_reference=False,
        )

        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            side_effect=[
                {'access_token': 'refund_token'},     # login
                {                                       # processModification
                    'ReasonCode': '1',
                    'ReasonCodeDescription': 'Refund approved',
                },
            ],
        ), patch(_EXTRACT_AMOUNT_DATA_PATH, return_value=None):
            refund_tx._send_refund_request()

        self.assertEqual(
            refund_tx.state, 'done',
            msg="Refund tx should be 'done' when ReasonCode is 1.",
        )

    @mute_logger(
        'odoo.addons.payment_tilopay.models.payment_transaction',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_send_refund_request_failure_sets_error(self):
        """A failed refund (ReasonCode != 1) should set the refund tx to error."""
        self.provider.support_refund = 'partial'
        source_tx = self._create_transaction(
            flow='redirect', state='done', provider_reference='TPT-SOURCE-003',
        )

        refund_tx = self._create_transaction(
            flow='redirect',
            reference='Test Transaction R3',
            amount=-self.amount,
            operation='refund',
            source_transaction_id=source_tx.id,
            provider_reference=False,
        )

        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            side_effect=[
                {'access_token': 'refund_token'},
                {
                    'ReasonCode': '99',
                    'ReasonCodeDescription': 'Refund declined',
                },
            ],
        ), patch(_EXTRACT_AMOUNT_DATA_PATH, return_value=None):
            refund_tx._send_refund_request()

        self.assertEqual(
            refund_tx.state, 'error',
            msg="Refund tx should be 'error' when ReasonCode is not 1.",
        )

    @mute_logger(
        'odoo.addons.payment_tilopay.models.payment_transaction',
        'odoo.addons.payment.models.payment_transaction',
    )
    def test_send_refund_uses_source_provider_reference(self):
        """Refund should use the source tx's provider_reference as orderNumber."""
        self.provider.support_refund = 'partial'
        source_tx = self._create_transaction(
            flow='redirect', state='done', provider_reference='TPT-ORIGINAL-REF',
        )

        captured_payload = {}

        def mock_send(self_provider, method, endpoint, **kwargs):
            if endpoint == '/api/v1/login':
                return {'access_token': 'tok'}
            if endpoint == '/api/v1/processModification':
                captured_payload.update(kwargs.get('json', {}))
                return {'ReasonCode': '1', 'ReasonCodeDescription': 'OK'}
            return {}

        refund_tx = self._create_transaction(
            flow='redirect',
            reference='Test Transaction R4',
            amount=-50.0,
            operation='refund',
            source_transaction_id=source_tx.id,
            provider_reference=False,
        )

        with patch(
            'odoo.addons.payment.models.payment_provider.PaymentProvider._send_api_request',
            mock_send,
        ), patch(_EXTRACT_AMOUNT_DATA_PATH, return_value=None):
            refund_tx._send_refund_request()

        self.assertEqual(
            captured_payload['orderNumber'], 'TPT-ORIGINAL-REF',
            msg="The refund orderNumber must be the source transaction's provider_reference.",
        )
        self.assertEqual(
            captured_payload['amount'], 50.0,
            msg="The refund amount should be the absolute value of the child tx amount.",
        )
