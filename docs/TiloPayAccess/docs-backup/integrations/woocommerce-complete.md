# TiloPay WooCommerce Gateway Documentation

Source: https://woocommerce.com/document/tilopay-gateway/


# Tilopay
Accept credit/debit cards, BNPL, financing and other local payment methods on your store. Tilopay is an ecosystem of digital payments that uses the most advanced technology to boost your business’ transactions. Our solution has been developed to solve online payments for businesses in the Retail, Hospitality and Service industries in Central America and the Caribbean.


### Important update notice:
Before updating the production website, we recommend testing it in your staging environment. You can get your integration key, API user and API password, from Tilopay admin


### Why use Tilopay
- Facilitate your clients’ transactions with onsite payments without redirection
- Maximize the approval rate to more than 90% thanks to our processing optimization tools
- Offer a variety of payment methods including the main credit and debit cards (Visa, Mastercard and American
- Express as well as local alternatives such as SINPE Móvil (Costa Rica), Yappy (Panamá), Tasa Cero BAC Credomatic (Central America) and Apple Pay among others
- Provide peace of mind to your consumers by offering state-of-the-art security that includes PCI, 3DS and KOUNT
- Make your business’ recurring charges more flexible with our integration with WooCommerce Subscriptions and with secure card storage (tokenization)


### Top Features:
- LATAM-focused (CAM/CAR) payment facilitation with local bank settlements
- On-site payment with no redirect
- Card-on-file functionality
- Alternative payment methods (wallets, bank transfers, BNPL, etc.)
- Smart Routing for optimal approval rates and antifraud protection (3DS 2.0, Kount Command, Decision Manager and/or ClearSale)


### Plugin Configuration Guide
After activating the plugin, you will be redirected to the screen where you can see all installed plugins. Here, click on “Settings” to configure the plugin.


### Plugin Settings

#### Enable/Disable
This option allows you to enable or disable the plugin.


#### Title
Modify the name of the Tilopay payment method on the purchase confirmation page.


#### API Key
Enter the integration key generated through the Tilopay user portal when associating a payment method with the integration.– Test Key: 6609-5850-8330-8034-3464


#### API User
Enter the integration user generated through the Tilopay user portal.– Test User: lSrT45


#### API Password
Enter the integration password generated through the Tilopay user portal.– Test Password: Zlb8H9


### Capture Mode

#### “Do not capture”
Select “Do not capture” if you want to collect the order in two steps, first authorize and then capture. By selecting this option, the orders will enter with statuses “Pending payment” or “Waiting”, the payment of the order will only be authorized. To capture the payment, the order status must be changed to “Processing” manually in the order itself. The maximum date to capture the payment is 7 calendar days after authorization. After the 7 days mentioned without making the capture, the authorized payment will be automatically cancelled.


#### “Yes, capture”
Select “Yes, capture” if you want to authorize and capture the payment of the order in a single step and automatically. By selecting this option, the orders will enter with statuses “Processing” or “Completed”, this status can be chosen depending on the need of the configuration, and the payment of the order will be authorized and captured automatically.


### Configure Logos
Select which card logos to display:– BAC Minicuotas logo– BAC Tasa Cero logo– Choose all or only the ones you prefer.


### Integrated Payment Options

#### Redirect to the Payment Form
Redirects users to an external payment page to complete their transaction.


#### Native Payment Form
The payment form is integrated directly into the WooCommerce checkout for a seamless experience.


### Save Your Settings
Once all configurations are set, click on “Save Changes” to apply the settings.


## Related Products

### Product Add-Ons
Offer add-ons like gift wrapping, special messages or other special options for your products.


### EU VAT Number
Collect VAT numbers at checkout and remove the VAT charge for eligible EU businesses.

