# Tilopay WordPress/WooCommerce Plugin - Technical Documentation

Source: https://wordpress.org/plugins/tilopay/

## Plugin Overview
- **Name:** Tilopay
- **Version:** 3.1.2
- **Type:** WooCommerce Payment Gateway Plugin
- **Operating System:** WordPress
- **Minimum PHP:** 7.4
- **Minimum WordPress:** 3.9
- **Tested up to:** 6.8.3

## Installation

### Modern Method (Recommended)
1. Go to WordPress Dashboard → "Add New Plugin"
2. Search for "Tilopay"
3. Install and Activate
4. Click "Settings" or go to WooCommerce → Settings → Payments → Tilopay
5. Reference: [Tilopay Admin Guide](https://app.tilopay.com/admin/guide/)

### Manual Method
1. Upload `tilopay` folder to `/wp-content/plugins/`
2. Activate via WordPress Plugins menu
3. Configure settings in WooCommerce → Payments

## Configuration Settings

### Required Credentials
Obtain from [Tilopay Admin Panel](https://app.tilopay.com/admin/checkout):
- **API Key (Integration Key)** - Test: `6609-5850-8330-8034-3464`
- **API User** - Test: `lSrT45`
- **API Password** - Test: `Zlb8H9`

### Core Settings

| Setting | Purpose |
|---------|---------|
| Enable/Disable | Toggle payment method availability |
| Title | Custom payment method name on checkout |
| API Key | Integration key from Tilopay portal |
| API User | Integration user credentials |
| API Password | Integration password |

### Capture Mode Options

#### "Do not capture"
- Two-step authorization and capture process
- Orders enter with "Pending Payment" or "Waiting" status
- Manual status change to "Processing" triggers capture
- Maximum 7 calendar days to capture after authorization
- Auto-cancels after 7 days if not captured

#### "Yes, capture"
- Single-step authorization and automatic capture
- Orders enter with "Processing" or "Completed" status
- Configurable final status based on business needs

### Additional Configuration

**Card Logos Display:**
- BAC Minicuotas logo
- BAC Tasa Cero logo
- Select all or preferred options

**Payment Form Options:**
1. **Redirect to Payment Form** - External payment page (off-site)
2. **Native Payment Form** - Integrated directly into WooCommerce checkout

## Key Features

### Payment Methods Supported
- Credit/Debit Cards (Visa, Mastercard, American Express)
- SINPE Móvil (Costa Rica)
- Yappy (Panama)
- Tasa Cero BAC Credomatic (Central America)
- Apple Pay
- BNPL (Buy Now, Pay Later)
- Financing options
- Bank transfers
- Local payment methods

### Security Features
- PCI Compliance
- 3DS 2.0 (3D Secure)
- KOUNT fraud detection
- ClearSale integration
- Decision Manager
- Card tokenization (card-on-file)

### Advanced Features
- Smart routing for optimal approval rates
- WooCommerce Subscriptions integration
- Recurring payment support
- Multi-currency support
- LATAM/CAM/CAR focus with local bank settlements
- On-site payment processing (no redirect option)

## Important Notes

### Before Updates
**Test in staging environment first**, especially when updating production sites.

### WooCommerce Compatibility
- Requires WooCommerce to be installed
- Supports WooCommerce Subscriptions for recurring charges
- Compatible with WooCommerce High-Performance Order Storage (HPOS)
- WooCommerce Blocks compatible (v3.0.0+)

### Subscription Payments
- Subscriptions not allowed in test environment
- Auto-selects "Save card" checkbox if subscription products present
- Supports variable subscription products

## Support

**Contact:** sac@tilopay.com

**Documentation:** [Tilopay Admin Documentation for WooCommerce](https://app.tilopay.com/admin/guide/)

**Support Forum:** [WordPress.org Plugin Support](https://wordpress.org/support/plugin/tilopay/)

## Language Support
- English (US)
- Spanish (8 variants: Spain, Mexico, Costa Rica, Colombia, Chile, Ecuador, and others)
- Dutch
- [Additional translations via Translate.WordPress.org](https://translate.wordpress.org/projects/wp-plugins/tilopay)

## Recent Changes (v3.1.2)
- Multi-site and single-site support improvements
- Previous version (3.1.1) reverted changes from 3.1.0

## Technical Requirements
- **WordPress:** 3.9 or higher
- **PHP:** 7.4 or higher
- **WooCommerce:** Required
- **Active Installations:** 1,000+
