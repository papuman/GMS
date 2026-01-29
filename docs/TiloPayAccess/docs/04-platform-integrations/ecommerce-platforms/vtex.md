# TiloPay Documentation

Source: https://help.vtex.com/en/docs/tutorials/setting-up-payments-with-tilopay

At VTEX, it is possible to integrate with the Tilopay payment provider. With this provider, your store can make sales through notes payable.

To configure Tilopay, follow the steps below:

- In the VTEX Admin, go to Store Settings > Payment > Providers, or type Providers in the search bar at the top of the page.
- On the providers screen, click the New Provider button.
- Type the name Tilopay in the search bar and click on the name of the provider.
- In Provider Authorization, fill in the App key and App token fields with data provided by your account Tilopay.
- If you wish to modify the identification name to be displayed for the Tilopay provider on the VTEX Admin screen, enter the information in the Name field in Basic Information.
- In Payment Control, select whether you want to activate the provider in a test environment by clicking Enable test mode.
- In the Automatic settlement field, select one of the following option:

`New Provider`- Use behavior recommended by the payment processor: Capture is not automatic; it is scheduled according to the period specified by the acquirer. The acquirer indicates whether the payment has been authorized and can determine or recommend a number of days for the capture upon payment authorization. (This is the platform's default behavior).
- Automatic capture immediately after payment authorization: Capture is automatically performed right after payment authorization, even if the transaction includes an anti-fraud analysis.
- Automatic capture immediately after anti-fraud analysis: Capture is automatically performed right after payment authorization and anti-fraud analysis. If you select this behavior and do not have anti-fraud analysis, the system will perform the payment capture as in "Automatic capture immediately after payment authorization".
- Disabled: Capture takes place only when the order is invoiced. If you select this behavior, it is important to pay attention to the invoicing time, as invoicing can exceed the capture time agreed with the payment provider and lead to the cancellation of the transaction.

- If you want to use [payment split](If you want to use payment split in your store, select the option Enable payout split and send payment recipients and indicate the Accountable for payment processing charges and Accountable for chargebacks (marketplace, sellers or marketplaces and sellers).) in your store, select the option Enable payout split and send payment recipients and indicate the Accountable for payment processing charges and Accountable for chargebacks (marketplace, sellers or marketplaces and sellers).
- Click Save.

`Save`To configure the payment methods to be processed by Tilopay, access Configuring Payment Conditions.

To set special conditions on payment methods, go to Configuring payment special conditions.

After following the indicated steps, Tilopay may take up to 10 minutes to appear at your store's checkout as a payment option.

