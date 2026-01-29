# Gym Management: POS & E-Invoicing Features Detailed Mapping
## Exact Requirements for Point of Sale and Electronic Invoicing

**Date:** December 29, 2025
**Critical:** This document maps gym requirements to your existing e-invoice module
**Status:** REFERENCE DOCUMENT - KEEP FOR IMPLEMENTATION

---

## Critical POS/Invoicing Features from Gym Requirements

### Category 3: Point of Sale (61 features)

#### ✅ ALREADY COVERED by Odoo POS + l10n_cr_einvoice (45/61 = 74%)

**Your Existing Modules Handle:**

1. ✅ Cash register interface → **Odoo POS**
2. ✅ Quick product search → **Odoo POS**
3. ✅ Barcode scanner → **Odoo POS**
4. ✅ Complete product catalog → **Odoo POS**
5. ✅ Product categories → **Odoo POS**
6. ✅ Customizable pricing → **Odoo POS**
7. ✅ **Multiple tax rates (13%, 4%, 2%, 1%, exempt)** → **Your l10n_cr_einvoice module!**
8. ✅ Percentage discounts → **Odoo POS**
9. ✅ Fixed amount discounts → **Odoo POS**
10. ✅ Promo codes → **Odoo POS**
11. ✅ Product variants → **Odoo POS**
12. ✅ Real-time inventory control → **Odoo Stock**
13. ✅ Low stock alerts → **Odoo Stock**
14. ✅ Supplier management → **Odoo Purchase**
15. ✅ Purchase orders → **Odoo Purchase**
16. ✅ Merchandise receiving → **Odoo Stock**
17. ✅ Inventory adjustments → **Odoo Stock**
18. ✅ Physical inventory count → **Odoo Stock**
19. ✅ Inventory movement history → **Odoo Stock**
20. ✅ Average product cost → **Odoo Stock**
21. ✅ Profit margin per product → **Odoo POS**
22. ✅ Multiple payment methods → **Odoo POS**
23. ✅ Cash payments → **Odoo POS**
24. ✅ Debit/credit card payments → **Odoo POS**
25. ✅ **SINPE Móvil payments** → **Your l10n_cr_einvoice module (payment method 05)!**
26. ✅ Split payments → **Odoo POS**
27. ✅ Payment reconciliation → **Odoo Accounting**
28. ✅ Cash register opening → **Odoo POS**
29. ✅ Cash register closing → **Odoo POS**
30. ✅ Cash counting → **Odoo POS**
31. ✅ Multiple cash registers → **Odoo POS**
32. ✅ Cashier shifts → **Odoo POS**
33. ✅ Refunds and returns → **Odoo POS**
34. ✅ **Credit notes** → **Your l10n_cr_einvoice module (document type NC)!**
35. ✅ **Costa Rica electronic invoicing** → **Your l10n_cr_einvoice module!**
36. ✅ **Invoice generation** → **Your l10n_cr_einvoice module!**
37. ✅ **Draft invoices** → **Your l10n_cr_einvoice module!**
38. ✅ **Invoice cancellation** → **Your l10n_cr_einvoice module!**
39. ✅ **Automatic invoice email delivery** → **Your l10n_cr_einvoice module!**
40. ✅ Receipt/ticket printing → **Odoo POS**
41. ✅ Thermal printer configuration → **Odoo POS**
42. ✅ Transaction history → **Odoo POS**
43. ✅ Daily sales reports → **Odoo POS**
44. ✅ Cashier reports → **Odoo POS**
45. ✅ Payment method reports → **Odoo POS**
46. ✅ **Integration with Tribu-CR (Costa Rica Tax Authority)** → **Your l10n_cr_einvoice module!**
47. ✅ **Digital signature on receipts** → **Your l10n_cr_einvoice module!**

#### ⚠️ NEED TO ADD (16 features)

**Gym-Specific POS Features:**

48. ⚠️ **New membership sales**
   - **What it is:** Sell gym memberships at POS
   - **How to implement:**
     ```python
     # Create membership product
     product_membership = self.env['product.product'].create({
         'name': 'Membership Monthly Premium',
         'type': 'service',
         'gms_is_membership': True,  # Custom field
         'gms_membership_type_id': ref('gms.membership_type_monthly_premium'),
         'list_price': 35000.00,  # ₡35,000
         'taxes_id': [(6, 0, [ref('l10n_cr.tax_13')])],  # 13% VAT
     })

     # When sold at POS, create membership record
     def _process_order(self, order, draft, existing_order):
         result = super()._process_order(order, draft, existing_order)
         if result.is_membership_sale:
             self._create_membership(result)
         return result
     ```
   - **Integrates with:** Your e-invoice module (generates FE or TE)

49. ⚠️ **Membership renewals**
   - **What it is:** Renew existing memberships at POS
   - **How to implement:**
     ```python
     # POS button: "Renew Membership"
     def action_renew_membership(self):
         member = self.get_current_customer()
         membership = member.active_membership_id

         # Add renewal product to cart
         self.add_product(membership.membership_type_id.product_id)

         # Link to existing membership for renewal
         self.current_order.gms_renewal_membership_id = membership.id
     ```

50. ⚠️ **Additional service sales**
   - **What it is:** Sell PT sessions, locker rentals, etc.
   - **How to implement:** Standard products, just categorize them
     ```python
     # Product categories
     - Services > Personal Training
     - Services > Locker Rental
     - Services > Guest Pass
     ```

51. ⚠️ **Volume discounts**
   - **What it is:** Buy 10 PT sessions, get discount
   - **Odoo has this:** Pricelist rules
     ```xml
     <record id="pricelist_rule_pt_10" model="product.pricelist.item">
         <field name="pricelist_id" ref="pricelist_gym"/>
         <field name="product_id" ref="product_personal_training"/>
         <field name="min_quantity">10</field>
         <field name="percent_price">10</field>  <!-- 10% off -->
     </record>
     ```

52. ⚠️ **Membership-based special pricing**
   - **What it is:** Premium members get discounts on products
   - **How to implement:**
     ```python
     # Create pricelist per membership type
     pricelist_premium = self.env['product.pricelist'].create({
         'name': 'Premium Member Pricing',
         'gms_membership_type_id': ref('gms.membership_type_premium'),
     })

     # At POS, set customer's pricelist based on membership
     def set_customer(self, partner):
         super().set_customer(partner)
         if partner.active_membership_id:
             membership_pricelist = partner.active_membership_id.membership_type_id.pricelist_id
             self.pricelist_id = membership_pricelist
     ```

53. ⚠️ **Combos and bundles**
   - **What it is:** "Membership + PT session + locker" bundle
   - **Odoo has this:** Product bundles (may need BoM module)
     ```python
     bundle = self.env['product.product'].create({
         'name': 'Premium Bundle',
         'type': 'consu',
         'is_bundle': True,  # Odoo field
         'bundle_line_ids': [
             (0, 0, {'product_id': membership_product.id, 'qty': 1}),
             (0, 0, {'product_id': pt_session_product.id, 'qty': 4}),
             (0, 0, {'product_id': locker_product.id, 'qty': 1}),
         ]
     })
     ```

54. ⚠️ **Credit/account payments**
   - **What it is:** Member pays later, charge to account
   - **Odoo has this:** Partner credit limit
     ```python
     # Enable credit for member
     partner.credit_limit = 100000  # ₡100,000 credit
     partner.property_payment_term_id = ref('account.account_payment_term_30days')

     # At POS
     payment_method_credit = {
         'name': 'Crédito a Cuenta',
         'journal_id': ref('account.sales_journal'),
         'is_credit': True,  # Custom field
     }
     ```

55. ⚠️ **Installment plans**
   - **What it is:** Pay membership in 3 monthly installments
   - **How to implement:**
     ```python
     # Sale order with payment terms
     sale = self.env['sale.order'].create({
         'partner_id': member.id,
         'payment_term_id': ref('gms.payment_term_3_installments'),
         'order_line': [(0, 0, {
             'product_id': membership_product.id,
             'product_uom_qty': 1,
         })]
     })

     # Create 3 invoices
     sale.action_confirm()
     # Payment term auto-creates 3 installments
     ```

56. ⚠️ **Integrated payment processing**
   - **What it is:** Process card payments through gateway
   - **Need:** Payment gateway module (BAC, BCR, Stripe, etc.)
     ```python
     # Install payment_stripe or payment_authorize
     # Configure in Odoo
     payment_acquirer = self.env['payment.acquirer'].create({
         'name': 'BAC Credomatic',
         'provider': 'stripe',  # Or custom CR bank
         'state': 'enabled',
     })
     ```

57. ⚠️ **Configurable tips**
   - **What it is:** Add tip to trainer/instructor
   - **How to implement:**
     ```python
     # POS extension
     class PosOrder(models.Model):
         _inherit = 'pos.order'

         tip_amount = fields.Float()
         tip_recipient_id = fields.Many2one('hr.employee')

     # Add to receipt
     TOTAL:           ₡39,550
     Propina (15%):    ₡5,933
     ━━━━━━━━━━━━━━━━━━━━━━
     GRAN TOTAL:      ₡45,483
     ```

58-61. **Quick sales (favorite products)**
   - **Odoo has this:** POS favorites
   - Just configure in POS settings

62. ⚠️ **Cash refund management**
   - **What it is:** Refund membership cancellation
   - **Odoo has this:** Refund process exists, just add business rules
     ```python
     def action_refund_membership(self):
         # Calculate prorated refund
         days_used = (fields.Date.today() - self.start_date).days
         total_days = (self.end_date - self.start_date).days
         refund_amount = self.price * (1 - days_used / total_days)

         # Create refund invoice
         refund = self.invoice_id.refund({
             'reason': 'Membership cancellation',
             'refund_amount': refund_amount,
         })
     ```

---

### Category 5: Costa Rica Compliance (21 features)

#### ✅ 100% COVERED by l10n_cr_einvoice!

Your module handles ALL of these:

1. ✅ **Full electronic invoicing**
2. ✅ **Direct integration with Tribu-CR / Hacienda**
3. ✅ **XML generation per DGT format** (Version 4.4)
4. ✅ **Digital signing of electronic documents** (XAdES-EPES)
5. ✅ **National ID validation (TSE)** - Cédula física
6. ✅ **DIMEX validation for foreigners**
7. ✅ **Document types: Electronic Invoice (FE)**
8. ✅ **Document types: Electronic Receipt (TE)**
9. ✅ **Document types: Credit Note (NC)**
10. ✅ **Document types: Debit Note (ND)**
11. ✅ **Correct application of Costa Rican taxes** (13%, 4%, 2%, 1%, exempt)
12. ✅ **Reduced VAT rates** (your tax configuration)
13. ✅ **VAT-exempt products** (your tax configuration)
14. ✅ **CRC currency handling**
15. ✅ **USD currency handling**
16. ✅ **Automatic exchange rate updates** (Odoo multi-currency)
17. ✅ **Reports for tax filings**
18. ✅ **Tax withholdings**
19. ✅ **D-151 declaration** (Transaction Summary)
20. ✅ **Legal storage compliance (5 years)**
21. ✅ **Storage of Hacienda responses**

**NO WORK NEEDED HERE - YOUR MODULE IS PERFECT!**

---

### Category 4: Finance and Billing (31 features)

#### ✅ COVERED by Odoo Accounting (20/31 = 65%)

**Standard Odoo handles:**

1. ✅ Accounts receivable
2. ✅ Accounts payable
3. ✅ Outstanding payment tracking
4. ✅ Member account statements
5. ✅ Complete payment history
6. ✅ Partial payment application
7. ✅ Bank reconciliation
8. ✅ Income reports
9. ✅ Expense reports
10. ✅ Cash flow
11. ✅ Financial projections
12. ✅ Profitability analysis
13. ✅ Cost centers
14. ✅ Budgeting and control
15. ✅ Accounting books
16. ✅ Balance sheet
17. ✅ Income statement
18. ✅ Accounting period close
19. ✅ Export to accounting systems
20. ✅ Tax management
21. ✅ **Tax filings** (your module helps here!)
22. ✅ Financial transaction auditing

#### ⚠️ NEED TO ADD (11 features)

23. ⚠️ **Automatic payment reminders**
   - **How to implement:**
     ```python
     # Automated action
     @api.model
     def cron_send_payment_reminders(self):
         overdue_invoices = self.env['account.move'].search([
             ('state', '=', 'posted'),
             ('payment_state', 'in', ['not_paid', 'partial']),
             ('invoice_date_due', '<', fields.Date.today()),
         ])
         for invoice in overdue_invoices:
             invoice._send_payment_reminder_email()
     ```

24. ⚠️ **Automatic recurring charges**
   - **Odoo has this:** sale_subscription module
     ```python
     # Recurring subscription
     subscription = self.env['sale.subscription'].create({
         'partner_id': member.id,
         'template_id': ref('gms.membership_monthly_template'),
         'recurring_rule_type': 'monthly',
         'recurring_invoice_line_ids': [(0, 0, {
             'product_id': membership_product.id,
             'quantity': 1,
             'price_unit': 35000,
         })]
     })
     # Auto-creates invoice every month!
     ```

25. ⚠️ **Automatic payment processing**
   - **Need:** Payment gateway with auto-charge
     ```python
     # Store payment method token
     member.payment_token_id = stripe_token

     # Auto-charge on invoice creation
     @api.model
     def cron_process_subscriptions(self):
         invoices = self.env['account.move'].search([
             ('invoice_date', '=', fields.Date.today()),
             ('state', '=', 'draft'),
             ('partner_id.auto_pay', '=', True),
         ])
         for invoice in invoices:
             invoice.action_post()  # Confirm
             invoice._auto_charge_payment_token()  # Charge saved card
     ```

26. ⚠️ **Multiple payment plans**
   - **Odoo has this:** Payment terms
     ```python
     # 3 monthly installments
     payment_term_3months = self.env['account.payment.term'].create({
         'name': '3 Cuotas Mensuales',
         'line_ids': [
             (0, 0, {'value': 'percent', 'value_amount': 33.33, 'days': 0}),
             (0, 0, {'value': 'percent', 'value_amount': 33.33, 'days': 30}),
             (0, 0, {'value': 'percent', 'value_amount': 33.34, 'days': 60}),
         ]
     })
     ```

27. ⚠️ **Installment configuration**
   - Same as above (payment terms)

28. ⚠️ **Configurable late fees**
   - **How to implement:**
     ```python
     # Automated action
     @api.model
     def cron_apply_late_fees(self):
         overdue = self.env['account.move'].search([
             ('invoice_date_due', '<', fields.Date.today() - timedelta(days=7)),
             ('payment_state', '!=', 'paid'),
         ])
         for invoice in overdue:
             late_fee = invoice.amount_total * 0.05  # 5%
             invoice.write({
                 'invoice_line_ids': [(0, 0, {
                     'name': 'Mora por pago tardío (5%)',
                     'quantity': 1,
                     'price_unit': late_fee,
                     'account_id': ref('account.income_late_fees'),
                 })]
             })
     ```

29. ⚠️ **Late fee exemptions**
   - **How to implement:**
     ```python
     class AccountMove(models.Model):
         _inherit = 'account.move'

         gms_exempt_late_fees = fields.Boolean('Exento de Mora')

     # Check before applying
     if not invoice.gms_exempt_late_fees:
         apply_late_fee(invoice)
     ```

30. ⚠️ **Integration with Costa Rican banks**
   - **Need:** Bank API integration
   - **Options:**
     - BAC Credomatic API
     - BCR (Banco de Costa Rica) API
     - SINPE Móvil API (you may already have this!)
     - Custom integration per bank

31. ⚠️ **External accountant integration**
   - **Odoo has this:** Multi-user access
   - Just give accountant user access
   - Export to Excel/CSV for external software

---

## Summary: What You Need to Build for POS/Invoicing

### From 61 POS features:

**✅ Already done:** 45 features (74%)
- Your l10n_cr_einvoice handles: 10 features
- Standard Odoo POS handles: 35 features

**⚠️ Need to build:** 16 features (26%)

**Focus areas:**
1. **Membership sales integration** (features #48-49)
   - Sell memberships at POS
   - Create membership records
   - Link to e-invoice

2. **Payment enhancements** (features #54-56)
   - Credit/account payments
   - Installment plans
   - Payment gateway

3. **Gym-specific pricing** (features #51-53)
   - Member discounts
   - Volume pricing
   - Bundles

### From 21 Costa Rica Compliance features:

**✅ Already done:** 21 features (100%)
- Your l10n_cr_einvoice is COMPLETE!

**⚠️ Need to build:** 0 features

### From 31 Finance features:

**✅ Already done:** 20 features (65%)
- Standard Odoo Accounting

**⚠️ Need to build:** 11 features (35%)

**Focus areas:**
1. **Automation** (features #23-25)
   - Payment reminders
   - Recurring billing
   - Auto-payments

2. **Payment flexibility** (features #26-29)
   - Installment plans
   - Late fees
   - Exemptions

---

## Integration Code Example

### Complete Flow: Member Buys Membership at POS

```python
# File: gms_pos_extensions/models/pos_order.py

class PosOrder(models.Model):
    _inherit = 'pos.order'

    gms_membership_id = fields.Many2one('gms.membership', 'Membership Created/Renewed')
    gms_is_membership_sale = fields.Boolean(compute='_compute_is_membership_sale')

    def _compute_is_membership_sale(self):
        for order in self:
            order.gms_is_membership_sale = any(
                line.product_id.gms_is_membership
                for line in order.lines
            )

    def _process_order(self, order, draft, existing_order):
        """
        Process POS order - integrates with:
        1. Standard POS (Odoo)
        2. GMS membership (custom)
        3. E-invoice (your l10n_cr_einvoice module)
        """
        # STEP 1: Standard POS processing
        result = super()._process_order(order, draft, existing_order)

        # STEP 2: Create/renew membership if membership product sold
        if result.gms_is_membership_sale:
            membership = self._create_or_renew_membership(result)
            result.gms_membership_id = membership.id

            # Log membership creation
            result.message_post(
                body=f"Membresía {membership.membership_type_id.name} creada/renovada"
            )

        # STEP 3: Generate e-invoice (YOUR MODULE!)
        if result.company_id.country_id.code == 'CR':
            # This is YOUR existing code - no changes needed!
            result._l10n_cr_generate_einvoice()

        return result

    def _create_or_renew_membership(self, order):
        """Create new or renew existing membership"""
        Membership = self.env['gms.membership']

        for line in order.lines:
            if not line.product_id.gms_is_membership:
                continue

            membership_type = line.product_id.gms_membership_type_id

            # Check if renewal or new
            active_membership = order.partner_id.active_membership_id
            if active_membership and active_membership.membership_type_id == membership_type:
                # Renewal: extend end date
                active_membership.write({
                    'end_date': active_membership.end_date + timedelta(
                        days=membership_type.duration_value * 30
                    ),
                })
                return active_membership
            else:
                # New membership
                return Membership.create({
                    'partner_id': order.partner_id.id,
                    'membership_type_id': membership_type.id,
                    'start_date': fields.Date.today(),
                    'end_date': fields.Date.today() + timedelta(
                        days=membership_type.duration_value * 30
                    ),
                    'state': 'active',
                    'invoice_id': order.account_move.id,  # Link to invoice
                })

# File: gms_pos_extensions/models/product_product.py

class ProductProduct(models.Model):
    _inherit = 'product.product'

    gms_is_membership = fields.Boolean('Is Gym Membership')
    gms_membership_type_id = fields.Many2one('gms.membership.type')
```

**When this runs:**

1. Member arrives → Cashier searches member (F4)
2. Cashier selects "Membership Monthly Premium" product
3. Member provides cédula → System validates format
4. Member pays with SINPE Móvil
5. **POS creates order** (standard Odoo)
6. **gms_pos_extensions creates membership** (custom code above)
7. **l10n_cr_einvoice generates FE** (YOUR existing module!)
8. Receipt prints with:
   - Membership details
   - Hacienda clave
   - QR code
9. Email sent with invoice PDF

**No changes needed to your e-invoice module!**

---

## Conclusion

**Your e-invoice module gives you a HUGE head start:**

| Component | Status | Work Needed |
|-----------|--------|-------------|
| **E-invoicing** | ✅ 100% complete | None - your module is perfect! |
| **POS basics** | ✅ 74% complete | 16 features (membership sales, pricing) |
| **Finance basics** | ✅ 65% complete | 11 features (automation, installments) |

**Total POS/invoicing work:** ~27 features out of 113 (24%)

**This is MUCH less work than building from scratch!**

The key is your existing l10n_cr_einvoice module handles all the hard stuff:
- XML generation
- Digital signatures
- Hacienda API
- All tax rates
- All document types
- Offline queue
- PDF generation
- Email delivery

You just need to:
1. Create membership products
2. Add logic to create membership records
3. Configure pricing/discounts
4. Add recurring billing

**Your e-invoice module does the rest automatically!**
