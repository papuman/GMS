# Invoice Void Wizard - Quick Start Guide

## 5-Minute Quick Start

### Access the Wizard

**Method 1: From Invoice**
1. Open any posted customer invoice
2. Click **Action** menu (⚙️)
3. Select **"Anular Factura"**

**Method 2: From Menu**
1. Go to **Hacienda → Operations → Anular Factura**
2. Select invoice from context

---

## Common Scenarios

### Scenario 1: Member Canceled Membership

```
Void Reason: Cancelación de membresía
Cancel Membership: ✓ Yes
Refund Method: Transferencia bancaria
Bank Account: [Member's IBAN]
Submit to Hacienda: ✓ Yes
Send Email: ✓ Yes
```

**Result:**
- Credit note created ✓
- Membership canceled ✓
- Hacienda submitted ✓
- Email sent with refund instructions ✓

---

### Scenario 2: Billing Error - Need to Re-Invoice

```
Void Reason: Error en facturación
Cancel Membership: ✗ No (keep active)
Refund Method: Crédito para futuras compras
Submit to Hacienda: ✓ Yes
Send Email: ✓ Yes
```

**Result:**
- Credit note created ✓
- Account credit applied ✓
- Membership stays active ✓
- Re-invoice can be created separately

---

### Scenario 3: Duplicate Invoice

```
Void Reason: Factura duplicada
Cancel Membership: ✗ No
Refund Method: Sin devolución
Notes: "Factura correcta ya existe"
Submit to Hacienda: ✓ Yes
Send Email: ✗ No
```

**Result:**
- Credit note created ✓
- No refund processed ✓
- No email (avoid confusion)

---

### Scenario 4: Cash Refund at Gym

```
Void Reason: Devolución solicitada por cliente
Cancel Membership: Depends on situation
Refund Method: Efectivo
Submit to Hacienda: ✓ Yes
Send Email: ✓ Yes
```

**Email includes:** "Por favor, acérquese a nuestras instalaciones para recibir su devolución en efectivo."

---

## Field Reference

### Void Reasons (Spanish)

| Code | Label | Use Case |
|------|-------|----------|
| `membership_cancel` | Cancelación de membresía | Member wants to cancel |
| `billing_error` | Error en facturación | Wrong amount/service |
| `customer_request` | Devolución solicitada | General refund request |
| `duplicate_invoice` | Factura duplicada | System error |
| `payment_failure` | Fallo en procesamiento | Payment didn't go through |
| `service_not_provided` | Servicio no prestado | Service issue |
| `price_adjustment` | Ajuste de precio | Price correction |
| `other` | Otro motivo | Other reasons |

### Refund Methods (Spanish)

| Code | Label | Processing Time |
|------|-------|----------------|
| `cash` | Efectivo | Immediate at gym |
| `transfer` | Transferencia bancaria | 3-5 business days |
| `credit` | Crédito para futuras compras | Immediate |
| `card` | Tarjeta de crédito/débito | 5-10 business days |
| `no_refund` | Sin devolución | N/A (courtesy) |

---

## What Happens When You Click "Anular Factura"

### 1. Credit Note Creation (1-2 seconds)
- Reversal of original invoice
- Same line items, negative amounts
- Linked to original invoice

### 2. E-Invoice Generation (2-3 seconds)
- XML v4.4 generation
- Digital signature
- 50-digit clave assigned

### 3. Membership Cancellation (if selected) (1 second)
- Status changed to "Closed"
- Cancellation reason logged
- Audit trail created

### 4. Hacienda Submission (if enabled) (5-10 seconds)
- Submit to Tribu-CR API
- Wait for acceptance
- Store response

### 5. Email Notification (if enabled) (1-2 seconds)
- Professional HTML email
- PDF and XML attachments
- Refund instructions

**Total Time:** 10-20 seconds average

---

## Validation Rules

### ❌ Cannot Void If:
- Invoice is not posted (draft/cancel state)
- Invoice already has a credit note
- You don't have accounting permissions
- Invoice is not a customer invoice (out_invoice)

### ⚠️ Warnings:
- E-invoice not yet accepted by Hacienda (proceeds anyway)
- Member has no email (email not sent)
- Membership already canceled (skips cancellation)

---

## After Voiding

### Actions Available:

**View Credit Note**
- Opens credit note in form view
- Shows all line items
- Check accounting entries

**View E-Invoice**
- Opens e-invoice document
- Check Hacienda status
- Download PDF/XML
- Resend email

**Check Hacienda Status**
- From credit note e-invoice
- Click "Check Status" if still pending
- Wait for acceptance/rejection

**Resend Email**
- If email failed
- If member didn't receive
- From e-invoice form view

---

## Troubleshooting

### Issue: "Cannot void - already has credit note"
**Solution:** Invoice was already voided. Check existing credit notes linked to this invoice.

### Issue: "Hacienda submission failed"
**Solutions:**
1. Check certificate is valid and not expired
2. Verify Hacienda credentials in Company settings
3. Check internet connection
4. Retry from credit note e-invoice

### Issue: "Email not sent"
**Solutions:**
1. Verify member email address
2. Check SMTP configuration
3. Use "Resend Email" from e-invoice
4. Send manually if needed

### Issue: "Bank account required for transfers"
**Solution:** Enter member's IBAN or bank account number in the "Bank Account" field.

### Issue: "Membership cancellation reason required"
**Solution:** If canceling membership, must provide reason in the text field.

---

## Best Practices

### DO:
✓ Always verify invoice details before voiding
✓ Provide detailed notes explaining the void
✓ Send email notification to members
✓ Submit to Hacienda automatically
✓ Keep refund records (reference numbers)
✓ Double-check bank account for transfers

### DON'T:
✗ Void invoices to fix small errors (use credit/debit notes)
✗ Skip email notification without reason
✗ Forget to process the actual refund
✗ Cancel memberships unnecessarily
✗ Ignore Hacienda submission status

---

## Email Preview

**Subject:** Confirmación de Anulación de Factura [Invoice Number]

**Content Includes:**
- Void confirmation
- Original invoice details
- Credit note number and clave
- Refund method and instructions
- Membership cancellation notice (if applicable)
- Hacienda verification info
- PDF and XML attachments
- Contact information

**Languages Supported:** Spanish (Costa Rica)

---

## Keyboard Shortcuts

- **Alt+V**: Open void wizard (from invoice)
- **Enter**: Submit wizard
- **Esc**: Cancel wizard

---

## Access Permissions

**Required Groups:**
- Billing / Invoicing
- Account Manager

**Users Who Can Void:**
- Accountants
- Billing staff
- Account managers
- System administrators

**Users Who CANNOT Void:**
- Portal users
- Sales team (unless also billing)
- Reception staff (unless given permissions)

---

## Integration Points

### Affects These Modules:
- **Accounting**: Credit note in journal
- **E-Invoicing**: New Nota de Crédito document
- **Memberships**: Cancellation status
- **Payments**: Refund processing
- **Email**: Notification to member

### Does NOT Affect:
- Sales orders (if membership ordered separately)
- Access rights (member can still log in)
- Historical data (audit trail preserved)

---

## Support Resources

### Documentation:
- Full guide: `PHASE8_GYM_INVOICE_VOID_WIZARD.md`
- Email templates: `data/void_confirmation_email.xml`
- Wizard code: `wizards/gym_invoice_void_wizard.py`

### Training Videos:
- Coming soon

### Support Contacts:
- Email: support@gms-cr.com
- Internal: #accounting-help channel

---

## Checklist for Training New Staff

- [ ] Show how to access wizard from invoice
- [ ] Explain each void reason
- [ ] Demonstrate refund methods
- [ ] Practice membership cancellation
- [ ] Review email template
- [ ] Test Hacienda submission
- [ ] Show how to check status
- [ ] Explain troubleshooting steps
- [ ] Review audit trail
- [ ] Practice end-to-end scenario

---

**Last Updated:** December 31, 2024
**Quick Start Version:** 1.0
**For Module Version:** 19.0.1.9.0
