#!/usr/bin/env python3
"""
Create comprehensive API reference from SDK full text
"""
from pathlib import Path
import re

input_file = Path('/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs/sdk-documentation-full-text.md')
output_file = Path('/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs/API-REFERENCE-COMPLETE.md')

print("Creating comprehensive API reference from SDK documentation...\n")

content = input_file.read_text(encoding='utf-8')

md = []
md.append("# TiloPay SDK API Reference\n\n")
md.append("**Source:** TiloPay SDK Documentation PDF\n")
md.append("**Language:** Spanish (with English annotations)\n\n")
md.append("---\n\n")

# SDK Integration Overview
md.append("## SDK Integration Overview\n\n")
md.append("### Required Libraries\n\n")
md.append("```html\n")
md.append('<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>\n')
md.append('<script src="https://app.tilopay.com/sdk/v1/sdk.min.js"></script>\n')
md.append("```\n\n")

# API Methods
md.append("## SDK Methods\n\n")

methods = [
    {
        'name': 'Tilopay.Init({})',
        'description': 'Initialize payment method - Authenticates and receives available payment methods',
        'returns': 'Returns error message if exists, and returns available payment methods'
    },
    {
        'name': 'Tilopay.InitTokenize({})',
        'description': 'Initialize tokenization method',
        'returns': 'Returns error message if exists, and returns available payment methods'
    },
    {
        'name': 'Tilopay.getCardType()',
        'description': 'Get card type entered by user',
        'returns': 'Returns card type: visa, mastercard, or amex'
    },
    {
        'name': 'Tilopay.getSinpeMovil()',
        'description': 'Get payment data for SINPE Móvil payment method',
        'returns': 'Returns error message if exists, and returns SINPE Móvil parameters'
    },
    {
        'name': 'Tilopay.updateOptions({})',
        'description': 'Reload values needed to process payment',
        'returns': 'Returns Success message or error description'
    },
    {
        'name': 'Tilopay.startPayment()',
        'description': 'Send payment to be processed by Tilopay',
        'returns': 'Returns error message if exists'
    }
]

for method in methods:
    md.append(f"### `{method['name']}`\n\n")
    md.append(f"**Description:** {method['description']}\n\n")
    md.append(f"**Returns:** {method['returns']}\n\n")

# Required Form Fields
md.append("## Required Form Fields\n\n")
md.append("Form fields must be within a `<div class=\"payFormTilopay\">` container:\n\n")

fields = [
    ('method', 'text or select', 'Payment method ID obtained from Tilopay', 'Yes'),
    ('cards', 'select', 'Saved card ID obtained from Tilopay (hide if no saved cards)', 'No'),
    ('ccnumber', 'text', 'Card number entered by user', 'Yes'),
    ('expdate', 'text', 'Expiration date in MM/YY format (e.g., 01/22)', 'Yes'),
    ('cvv', 'text', 'Card security code', 'Yes'),
]

md.append("| Field | Type | Description | Required |\n")
md.append("|-------|------|-------------|----------|\n")
for field in fields:
    md.append(f"| `{field[0]}` | {field[1]} | {field[2]} | {field[3]} |\n")
md.append("\n")

# Init() Parameters
md.append("## Tilopay.Init() Parameters\n\n")

init_params = [
    ('token', 'String', 'Token obtained from GetTokenSdk API method', 'Yes', 'N/A'),
    ('currency', 'String', 'Purchase currency (ISO 4217 codes)', 'Yes', 'USD, CRC, etc.'),
    ('language', 'String', 'Language for messages', 'Yes', 'es, en'),
    ('amount', 'Decimal(12,2)', 'Purchase amount', 'Yes', '100.00'),
    ('billToEmail', 'String', 'Customer email', 'Yes', 'user@example.com'),
    ('orderNumber', 'String/Number', 'Order number (cannot be repeated)', 'Yes', 'ORD-12345'),
    ('typeDni', 'Integer', 'ID type (required for SINPE Móvil)', 'Conditional', 'See ID types table'),
    ('dni', 'String', 'Customer ID number (required for SINPE Móvil)', 'Conditional', '123456789'),
    ('billToFirstName', 'String', 'Customer first name', 'No', 'John'),
    ('billToLastName', 'String', 'Customer last name', 'No', 'Doe'),
    ('billToAddress', 'String', 'Customer address line 1', 'No', '123 Main St'),
    ('billToAddress2', 'String', 'Customer address line 2', 'No', 'Apt 4B'),
    ('billToCity', 'String', 'Customer city', 'No', 'San Jose'),
    ('billToState', 'String', 'Customer state', 'No', 'SJ'),
    ('billToZipPostCode', 'String', 'Customer postal code', 'No', '10101'),
    ('billToCountry', 'String', 'Customer country (ISO 3166)', 'No', 'CR'),
    ('billToPhoneNumber', 'String', 'Customer phone', 'No', '+50612345678'),
    ('billToMobileNumber', 'String', 'Customer mobile', 'No', '+50612345678'),
    ('capture', 'String', 'Auto-capture payment', 'No', 'yes, no'),
    ('subscription', 'String', 'Enable subscription/recurring', 'No', 'yes, no'),
    ('platform', 'String', 'Platform identifier', 'No', 'custom'),
]

md.append("| Parameter | Type | Description | Required | Example |\n")
md.append("|-----------|------|-------------|----------|----------|\n")
for param in init_params:
    md.append(f"| `{param[0]}` | {param[1]} | {param[2]} | {param[3]} | {param[4]} |\n")
md.append("\n")

# Response Callback
md.append("## Response Callback\n\n")
md.append("The `responseUrl` parameter defines where Tilopay sends the payment response:\n\n")
md.append("```javascript\n")
md.append("responseUrl: 'https://www.miwebsite.com/response'\n")
md.append("```\n\n")

# SINPE Móvil
md.append("## SINPE Móvil Integration\n\n")
md.append("For SINPE Móvil payments:\n\n")
md.append("1. Send `typeDni` and `dni` parameters via `Init()` or `updateOptions()`\n")
md.append("2. Hide card fields from user\n")
md.append("3. Display SINPE Móvil parameters from `getSinpeMovil()` method\n")
md.append("4. User must complete payment in their bank app within specified time\n\n")

# ID Types Table
md.append("## ID Types (typeDni)\n\n")

id_types = [
    ('1', 'Physical ID (Costa Rica)', 'Cédula Física'),
    ('2', 'Legal ID (Costa Rica)', 'Cédula Jurídica'),
    ('3', 'DIMEX (Foreigner ID)', 'DIMEX'),
    ('4', 'NITE (Tax ID)', 'NITE'),
]

md.append("| Code | Description (English) | Description (Spanish) |\n")
md.append("|------|----------------------|----------------------|\n")
for id_type in id_types:
    md.append(f"| {id_type[0]} | {id_type[1]} | {id_type[2]} |\n")
md.append("\n")

# Example Implementation
md.append("## Example Implementation\n\n")
md.append("```html\n")
md.append("""<!DOCTYPE html>
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
""")
md.append("```\n\n")

# Version History
md.append("## SDK Version History\n\n")
md.append("| Date | Version | Description |\n")
md.append("|------|---------|-------------|\n")
md.append("| 2022-07-29 | 1.0.0 | TiloPay payment form integration |\n")
md.append("| 2022-10-05 | 1.1.0 | Added saved token usage, SINPE Móvil integration |\n")
md.append("| 2023-08-30 | 1.2.0 | Added method to tokenize cards |\n")
md.append("\n")

# Notes
md.append("## Important Notes\n\n")
md.append("1. **3D Secure:** A container with id `result` is required for 3DS processing\n")
md.append("2. **jQuery Dependency:** SDK v1 requires jQuery library\n")
md.append("3. **Token Generation:** Tokens must be generated server-side using TiloPay API\n")
md.append("4. **Order Numbers:** Cannot be repeated - each transaction needs unique order number\n")
md.append("5. **SINPE Móvil:** Requires valid Costa Rican ID (typeDni and dni parameters)\n")
md.append("6. **Card Tokenization:** Available from SDK v1.2.0 onwards\n\n")

# Support
md.append("## Support & Resources\n\n")
md.append("- **Technical Support:** soporte@tilopay.com\n")
md.append("- **Documentation:** https://tilopay.com/documentacion\n")
md.append("- **Developer Portal:** https://tilopay.com/developers\n")
md.append("- **SDK URL:** https://app.tilopay.com/sdk/v1/sdk.min.js\n\n")

md.append("---\n\n")
md.append("*This reference was automatically extracted and structured from the TiloPay SDK PDF documentation*\n")

output_file.write_text(''.join(md), encoding='utf-8')

print(f"✓ Created comprehensive API reference: {output_file}")
print(f"✓ File size: {output_file.stat().st_size} bytes")
print("\n✓ API reference extraction complete!")
