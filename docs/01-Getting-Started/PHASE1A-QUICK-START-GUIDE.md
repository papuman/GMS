# Phase 1A: Quick Start Guide - Payment Methods for Costa Rica E-Invoicing

**For:** GMS Users and Administrators
**Date:** 2025-12-28
**Module:** Costa Rica Electronic Invoicing (l10n_cr_einvoice)

---

## What's New in Phase 1A?

Phase 1A adds **payment method tracking** to all Costa Rica electronic invoices, with special support for **SINPE Móvil** - the most popular payment method in Costa Rica (used by 84% of the population).

### Key Features:
- 5 payment methods available: Efectivo, Tarjeta, Cheque, Transferencia, SINPE Móvil
- Automatic validation for SINPE Móvil transaction IDs
- Default to "Efectivo" if no payment method selected
- Payment method included in XML sent to Hacienda

---

## Available Payment Methods

| Code | Name | Description | Requires Transaction ID? |
|------|------|-------------|-------------------------|
| **01** | Efectivo | Cash payment | No |
| **02** | Tarjeta | Credit/debit card | No |
| **03** | Cheque | Bank check | No |
| **04** | Transferencia | Bank transfer/deposit | No |
| **06** | SINPE Móvil | Mobile payment system | **YES** |

---

## How to Use Payment Methods

### Creating a New Invoice

1. **Open Customer Invoice** (Accounting → Customers → Invoices → Create)

2. **Fill Invoice Details** as usual:
   - Customer
   - Invoice date
   - Product lines
   - Payment terms

3. **Select Payment Method** (NEW FIELD):
   - Located below "Payment Terms" field
   - Dropdown with 5 options
   - **Default:** "01 - Efectivo" if not selected

4. **For SINPE Móvil ONLY:**
   - After selecting "06 - SINPE Móvil"
   - A new field appears: **"Transaction ID"**
   - **REQUIRED:** Enter the transaction reference number
   - Example: "123456789"

5. **Confirm Invoice** as usual

### Important Rules

- **SINPE Móvil MUST have Transaction ID** → You'll get an error if missing
- **Other methods:** Transaction ID is optional
- **Default:** If you forget to select a method, system uses "01-Efectivo"

---

## Examples

### Example 1: Cash Payment (Efectivo)

```
Customer: Juan Pérez
Amount: ₡50,000
Payment Method: 01 - Efectivo
Transaction ID: [leave empty]
✅ Invoice posts successfully
```

### Example 2: SINPE Móvil Payment (Correct)

```
Customer: María González
Amount: ₡75,000
Payment Method: 06 - SINPE Móvil
Transaction ID: 987654321
✅ Invoice posts successfully
✅ XML includes transaction ID
```

### Example 3: SINPE Móvil Payment (Error)

```
Customer: María González
Amount: ₡75,000
Payment Method: 06 - SINPE Móvil
Transaction ID: [empty]
❌ ERROR: "Transaction ID is required for payment method SINPE Móvil"
👉 Solution: Enter the transaction ID from the SINPE app
```

---

## Where to Find Transaction IDs

### SINPE Móvil Transaction ID

After customer pays via SINPE Móvil:
1. Open SINPE Móvil app
2. Go to transaction history
3. Find the payment
4. Copy the transaction reference number (usually 8-12 digits)
5. Enter this number in the "Transaction ID" field

### Card Payments (Optional)

While not required, you can optionally enter:
- Authorization code
- Last 4 digits of card
- Payment gateway reference

---

## Reporting and Filtering

### New Filters Available

In the invoice list, you can now filter by payment method:

- **SINPE Móvil Payments** → Shows all invoices paid via SINPE
- **Card Payments** → Shows all invoices paid by card
- **Cash Payments** → Shows all invoices paid in cash

### Group By Payment Method

Click **Group By** → **Payment Method** to organize invoices by how customers paid.

---

## What Happens to Existing Invoices?

**Don't worry!** All your existing invoices are automatically updated:

- ✅ All posted invoices get payment method "01 - Efectivo"
- ✅ No data is lost
- ✅ You can change the payment method later if needed
- ✅ Migration happens automatically when you upgrade the module

---

## Common Questions (FAQ)

### Q: What if I don't know the payment method?
**A:** The system will default to "01 - Efectivo" (cash). You can update it later.

### Q: Can I change the payment method after posting?
**A:** No, payment methods are tracked and locked after invoice confirmation. Choose carefully before posting.

### Q: What if the customer paid with multiple methods?
**A:** Currently, select the primary payment method. Multiple payment methods will be supported in a future update.

### Q: Do I need a transaction ID for card payments?
**A:** No, only SINPE Móvil requires it. For cards, it's optional.

### Q: What happens if I enter the wrong transaction ID?
**A:** Contact your administrator to correct it. The field is tracked in the invoice history.

### Q: Will Hacienda reject my invoice if I use the wrong payment method?
**A:** No, but accurate payment method tracking is required by law. Use the correct method to stay compliant.

---

## Compliance Information

### Why This Matters (Legal Context)

Costa Rica's Ministry of Finance (Hacienda) requires payment method tracking per:
- **Resolution:** MH-DGT-RES-0027-2024
- **Effective:** January 1, 2025
- **Penalties:** Up to 150% of tax amount for non-compliance

### Your Responsibilities

1. **Select correct payment method** for each invoice
2. **Enter transaction ID** for SINPE Móvil payments
3. **Keep records** of payment confirmations
4. **Train your team** on the 5 payment methods

---

## Troubleshooting

### Error: "Transaction ID is required for payment method SINPE Móvil"

**Cause:** You selected SINPE Móvil but didn't enter the transaction ID.

**Solution:**
1. Click the invoice to edit (if still in draft)
2. Enter the transaction ID in the "Transaction ID" field
3. Click "Confirm" again

### Error: "Payment method is required for Costa Rica electronic invoicing"

**Cause:** Payment method field is empty and default couldn't be assigned.

**Solution:**
1. Manually select a payment method from the dropdown
2. If SINPE Móvil, enter transaction ID
3. Try confirming again

### Can't See Payment Method Field

**Cause:** You might be viewing a non-Costa Rica invoice or supplier bill.

**Solution:**
- Payment methods only show for **customer invoices** (outgoing)
- Only for **Costa Rica** invoices
- Not visible on vendor bills (incoming)

---

## Tips for Different Business Types

### Gyms & Fitness Centers (like GMS)

**Common payment mix:**
- 60% SINPE Móvil (monthly memberships)
- 30% Tarjeta (recurring subscriptions)
- 10% Efectivo (drop-ins)

**Best Practice:**
- Set up recurring invoices with default payment method
- Update to SINPE when customer pays via mobile
- Keep transaction IDs in payment notes

### Retail Stores

**Common payment mix:**
- 40% Efectivo (walk-ins)
- 40% Tarjeta (POS terminal)
- 20% SINPE Móvil (mobile payments)

**Best Practice:**
- Train cashiers on payment method selection
- Integrate with POS system for automatic selection
- Keep daily payment method reports

### Service Businesses

**Common payment mix:**
- 50% Transferencia (bank transfers)
- 30% SINPE Móvil (mobile payments)
- 20% Cheque (large invoices)

**Best Practice:**
- Match payment method to invoice terms
- Request transaction IDs when receiving SINPE payments
- Verify transaction IDs before posting invoices

---

## Training Checklist for Staff

- [ ] Understand the 5 payment methods
- [ ] Know when transaction ID is required (SINPE Móvil only)
- [ ] Can locate transaction IDs in SINPE app
- [ ] Know how to select payment method on invoice
- [ ] Understand error messages and how to fix them
- [ ] Know where to find payment method reports
- [ ] Aware of legal compliance requirements

---

## Support Contacts

**Technical Issues:**
- Module: l10n_cr_einvoice v19.0.1.0.0
- Support: GMS Development Team
- Email: support@gms-cr.com

**Compliance Questions:**
- Hacienda Website: https://www.hacienda.go.cr
- Resolution: MH-DGT-RES-0027-2024
- Help: Ministry of Finance Support

---

## Quick Reference Card (Print & Post)

```
┌─────────────────────────────────────────────────────┐
│   COSTA RICA E-INVOICE PAYMENT METHODS             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  01 Efectivo        → Cash (default)               │
│  02 Tarjeta         → Credit/Debit Card            │
│  03 Cheque          → Check                        │
│  04 Transferencia   → Bank Transfer                │
│  06 SINPE Móvil     → Mobile Payment ⚠ Needs ID!  │
│                                                     │
│  ⚠️  IMPORTANT:                                     │
│  SINPE Móvil REQUIRES Transaction ID              │
│  Get it from the SINPE app after payment          │
│                                                     │
│  💡 TIP:                                            │
│  If unsure, select "01 - Efectivo"                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

**Version:** 1.0
**Last Updated:** 2025-12-28
**Next Review:** After Phase 1B deployment

---
