-- disable tilopay payment provider
UPDATE payment_provider
   SET tilopay_api_key = NULL,
       tilopay_api_user = NULL,
       tilopay_api_password = NULL;
