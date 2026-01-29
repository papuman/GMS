# TiloPay SDK API Reference

**Source:** TiloPay SDK Documentation PDF
**Language:** Spanish (with English annotations)

---

## SDK Integration Overview

### Required Libraries

```html
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<script src="https://app.tilopay.com/sdk/v1/sdk.min.js"></script>
```

## SDK Methods

### `Tilopay.Init({})`

**Description:** Initialize payment method - Authenticates and receives available payment methods

**Returns:** Returns error message if exists, and returns available payment methods

### `Tilopay.InitTokenize({})`

**Description:** Initialize tokenization method

**Returns:** Returns error message if exists, and returns available payment methods

### `Tilopay.getCardType()`

**Description:** Get card type entered by user

**Returns:** Returns card type: visa, mastercard, or amex

### `Tilopay.getSinpeMovil()`

**Description:** Get payment data for SINPE Móvil payment method

**Returns:** Returns error message if exists, and returns SINPE Móvil parameters

### `Tilopay.updateOptions({})`

**Description:** Reload values needed to process payment

**Returns:** Returns Success message or error description

### `Tilopay.startPayment()`

**Description:** Send payment to be processed by Tilopay

**Returns:** Returns error message if exists

## Required Form Fields

Form fields must be within a `<div class="payFormTilopay">` container:

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `method` | text or select | Payment method ID obtained from Tilopay | Yes |
| `cards` | select | Saved card ID obtained from Tilopay (hide if no saved cards) | No |
| `ccnumber` | text | Card number entered by user | Yes |
| `expdate` | text | Expiration date in MM/YY format (e.g., 01/22) | Yes |
| `cvv` | text | Card security code | Yes |

## Tilopay.Init() Parameters

| Parameter | Type | Description | Required | Example |
|-----------|------|-------------|----------|----------|
| `token` | String | Token obtained from GetTokenSdk API method | Yes | N/A |
| `currency` | String | Purchase currency (ISO 4217 codes) | Yes | USD, CRC, etc. |
| `language` | String | Language for messages | Yes | es, en |
| `amount` | Decimal(12,2) | Purchase amount | Yes | 100.00 |
| `billToEmail` | String | Customer email | Yes | user@example.com |
| `orderNumber` | String/Number | Order number (cannot be repeated) | Yes | ORD-12345 |
| `typeDni` | Integer | ID type (required for SINPE Móvil) | Conditional | See ID types table |
| `dni` | String | Customer ID number (required for SINPE Móvil) | Conditional | 123456789 |
| `billToFirstName` | String | Customer first name | No | John |
| `billToLastName` | String | Customer last name | No | Doe |
| `billToAddress` | String | Customer address line 1 | No | 123 Main St |
| `billToAddress2` | String | Customer address line 2 | No | Apt 4B |
| `billToCity` | String | Customer city | No | San Jose |
| `billToState` | String | Customer state | No | SJ |
| `billToZipPostCode` | String | Customer postal code | No | 10101 |
| `billToCountry` | String | Customer country (ISO 3166) | No | CR |
| `billToPhoneNumber` | String | Customer phone | No | +50612345678 |
| `billToMobileNumber` | String | Customer mobile | No | +50612345678 |
| `capture` | String | Auto-capture payment | No | yes, no |
| `subscription` | String | Enable subscription/recurring | No | yes, no |
| `platform` | String | Platform identifier | No | custom |

## Response Callback

The `responseUrl` parameter defines where Tilopay sends the payment response:

```javascript
responseUrl: 'https://www.miwebsite.com/response'
```

## SINPE Móvil Integration

For SINPE Móvil payments:

1. Send `typeDni` and `dni` parameters via `Init()` or `updateOptions()`
2. Hide card fields from user
3. Display SINPE Móvil parameters from `getSinpeMovil()` method
4. User must complete payment in their bank app within specified time

## ID Types (typeDni)

| Code | Description (English) | Description (Spanish) |
|------|----------------------|----------------------|
| 1 | Physical ID (Costa Rica) | Cédula Física |
| 2 | Legal ID (Costa Rica) | Cédula Jurídica |
| 3 | DIMEX (Foreigner ID) | DIMEX |
| 4 | NITE (Tax ID) | NITE |

## Example Implementation

```html
<!DOCTYPE html>
<html>
<head>
    <title>TiloPay Integration</title>
</head>
<body>
    <div class="payFormTilopay">
        <label>Payment Method</label>
        <select name="method" id="method">
            <option value="">Select payment method</option>
        </select>

        <label>Saved Cards</label>
        <select name="cards" id="cards">
            <option value="">Select card</option>
        </select>

        <label>Card Number</label>
        <input type="text" id="ccnumber" name="ccnumber">

        <label>Expiration Date (MM/YY)</label>
        <input type="text" id="expdate" name="expdate">

        <label>CVV</label>
        <input type="text" id="cvv" name="cvv">

        <button onclick="processPayment()">Pay Now</button>
    </div>

    <div id="result"></div>

    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://app.tilopay.com/sdk/v1/sdk.min.js"></script>
    <script>
        function processPayment() {
            Tilopay.Init({
                token: 'YOUR_TOKEN_HERE',
                currency: 'USD',
                language: 'en',
                amount: 100.00,
                billToEmail: 'customer@example.com',
                orderNumber: 'ORD-' + Date.now(),
                responseUrl: 'https://yoursite.com/payment/response',
                capture: 'yes'
            });
        }
    </script>
</body>
</html>
```

## SDK Version History

| Date | Version | Description |
|------|---------|-------------|
| 2022-07-29 | 1.0.0 | TiloPay payment form integration |
| 2022-10-05 | 1.1.0 | Added saved token usage, SINPE Móvil integration |
| 2023-08-30 | 1.2.0 | Added method to tokenize cards |

## Important Notes

1. **3D Secure:** A container with id `result` is required for 3DS processing
2. **jQuery Dependency:** SDK v1 requires jQuery library
3. **Token Generation:** Tokens must be generated server-side using TiloPay API
4. **Order Numbers:** Cannot be repeated - each transaction needs unique order number
5. **SINPE Móvil:** Requires valid Costa Rican ID (typeDni and dni parameters)
6. **Card Tokenization:** Available from SDK v1.2.0 onwards

## Support & Resources

- **Technical Support:** soporte@tilopay.com
- **Documentation:** https://tilopay.com/documentacion
- **Developer Portal:** https://tilopay.com/developers
- **SDK URL:** https://app.tilopay.com/sdk/v1/sdk.min.js

---

*This reference was automatically extracted and structured from the TiloPay SDK PDF documentation*
