# TiloPay Payment Gateway - Administrator Setup Guide

**Version:** 1.0
**Date:** 2025-12-28
**Audience:** System Administrators, Gym Managers

---

## Overview

This guide walks you through the complete setup process for enabling TiloPay payment gateway in your GMS Odoo system. Follow these steps in order to configure online payments for your gym members.

**Estimated Time:** 30-45 minutes (after obtaining TiloPay credentials)

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Odoo 19** installed and running
- [ ] **l10n_cr_einvoice** module installed and configured
- [ ] **TiloPay merchant account** approved
- [ ] **TiloPay credentials** obtained from dashboard
- [ ] **System administrator** access to Odoo
- [ ] **Internet connection** for webhook configuration
- [ ] **HTTPS enabled** on your domain (required for webhooks)

---

## Part 1: TiloPay Account Credentials

### Step 1.1: Log into TiloPay Dashboard

1. Go to https://admin.tilopay.com/
2. Log in with your TiloPay merchant credentials
3. You should see your merchant dashboard

### Step 1.2: Locate API Credentials

1. Click **Account** in top menu
2. Select **Checkout** from dropdown
3. Scroll to **API Credentials** section
4. You'll see:
   - **API Key** (format: xxxx-xxxx-xxxx-xxxx-xxxx)
   - **API User** (username for API access)
   - **API Password** (password for API access)

5. Click **Show** to reveal each credential
6. **Copy each value** - you'll need them in Odoo

### Step 1.3: Locate Security Keys

1. In same **Checkout** page, scroll to **Developer Settings**
2. Find **Merchant Code** (your merchant identifier)
3. Find **Secret Key** (for webhook signature verification)
4. Copy both values

**⚠️ SECURITY WARNING:**
- Never share these credentials publicly
- Store them securely (password manager recommended)
- Don't commit them to version control
- Treat Secret Key like a password

---

## Part 2: Odoo Module Installation

### Step 2.1: Install payment_tilopay Module

1. Log into Odoo as administrator
2. Go to: **Apps** (top menu)
3. Click **Update Apps List** (may take 30 seconds)
4. Search for: **"tilopay"**
5. Find **"TiloPay Payment Gateway for Costa Rica"**
6. Click **Install**
7. Wait for installation to complete (1-2 minutes)

**Expected Result:**
- Module status: **Installed** ✅
- No error messages
- New menu items appear

### Step 2.2: Verify Installation

1. Go to: **Accounting > Configuration > Payment Providers**
2. You should see **TiloPay** in the list
3. Status should be: **Disabled**
4. If you don't see TiloPay, refresh the page

---

## Part 3: Configure TiloPay Provider

### Step 3.1: Open Provider Configuration

1. Go to: **Accounting > Configuration > Payment Providers**
2. Click on **TiloPay** row to open it
3. You'll see the configuration form

### Step 3.2: Enter API Credentials

In the **TiloPay Credentials** section:

1. **TiloPay API Key:**
   - Paste your API Key from TiloPay dashboard
   - Should look like: `6609-5850-8330-8034-3464`

2. **TiloPay API User:**
   - Paste your API User
   - Example: `lSrT45` or your actual username

3. **TiloPay API Password:**
   - Paste your API Password
   - Field will be masked with asterisks

4. **Merchant Code:** (optional but recommended)
   - Paste your Merchant Code if you have it

5. **Secret Key:** (REQUIRED for production)
   - Paste your Secret Key
   - This is critical for webhook security
   - Field will be masked

**✅ Checkpoint:** All credential fields should be filled (no red borders)

### Step 3.3: Configure Environment

In the **TiloPay Credentials** section:

**Use Sandbox Environment:**
- ☑️ **CHECKED** - For testing (use test credentials)
- ☐ **UNCHECKED** - For production (use real credentials)

**For initial setup, keep this CHECKED** ✅

### Step 3.4: Configure Payment Methods

In the **Payment Methods** section:

**Enable SINPE Móvil:**
- ☑️ **CHECKED** - Allow SINPE Móvil payments (recommended)
- Most popular payment method in Costa Rica
- Lowest fees (1.0-1.5%)

**Enable Credit/Debit Cards:**
- ☑️ **CHECKED** - Allow card payments (recommended)
- Visa, Mastercard, American Express
- Higher fees (3.5-3.9%)

**Enable Yappy:**
- ☐ **UNCHECKED** - Only if you have Panama members
- Yappy is a Panama payment method

**Recommendation:** Enable both SINPE and Cards for maximum flexibility.

### Step 3.5: Copy Webhook URL

In the **Webhook Configuration** section:

1. You'll see a **Webhook URL** field (read-only)
2. Example: `https://yourgym.com/payment/tilopay/webhook`
3. **Click to select** the entire URL
4. **Copy it** (Ctrl+C or Cmd+C)
5. **Keep this copied** - you'll need it in TiloPay dashboard

**⚠️ IMPORTANT:**
- This URL MUST use HTTPS (not HTTP)
- If you see HTTP, you need to enable SSL/TLS first
- Webhooks won't work without HTTPS

### Step 3.6: Save Configuration

1. Click **Save** button (top-left or bottom)
2. Configuration is saved but provider is still **Disabled**
3. **Don't enable yet** - we need to test first

---

## Part 4: Configure TiloPay Webhook

### Step 4.1: Open TiloPay Developer Settings

1. Log into TiloPay dashboard: https://admin.tilopay.com/
2. Click **Developer** in top menu (or Account > Developer)
3. Select **Webhooks** from sidebar
4. You'll see list of configured webhooks (may be empty)

### Step 4.2: Add New Webhook

1. Click **Add Webhook** or **+ New Webhook** button
2. Fill in the form:

**Webhook URL:**
- Paste the URL you copied from Odoo
- Example: `https://yourgym.com/payment/tilopay/webhook`
- Verify it starts with `https://` (not http://)

**Event Selection:**
Select these events (check all three):
- ☑️ **payment.completed** - Payment successful
- ☑️ **payment.failed** - Payment failed
- ☑️ **payment.cancelled** - Payment cancelled

**Status:**
- Set to: **Active** ✅

3. Click **Save** or **Create Webhook**

### Step 4.3: Verify Webhook Configuration

1. You should see your webhook in the list
2. Status: **Active** (green)
3. URL: Shows your Odoo webhook URL
4. Events: Shows 3 events selected

**⚠️ Common Issues:**
- If webhook creation fails, verify HTTPS is enabled on your domain
- TiloPay requires valid SSL certificate
- Self-signed certificates won't work

---

## Part 5: Test Connection

### Step 5.1: Test API Credentials

1. Go back to Odoo: **Accounting > Configuration > Payment Providers > TiloPay**
2. Ensure you're still in **Sandbox mode** (checkbox checked)
3. Click **Test Connection** button (below webhook URL)
4. Wait for response (5-10 seconds)

**Expected Results:**

**✅ Success:**
- Green notification: "Connection test successful"
- This means credentials are valid

**❌ Failure:**
- Red notification with error message
- Common errors:
  - "Invalid credentials" → Check API Key, User, Password
  - "Connection timeout" → Check internet connection
  - "Authentication failed" → Verify sandbox mode matches credentials

### Step 5.2: Troubleshoot Connection Issues

If test fails:

1. **Verify Environment:**
   - Sandbox mode = Use test credentials
   - Production mode = Use production credentials
   - Don't mix them!

2. **Re-copy Credentials:**
   - Go back to TiloPay dashboard
   - Copy credentials again (avoid typos)
   - Paste fresh into Odoo

3. **Check Credential Format:**
   - API Key: Should have dashes (xxxx-xxxx-xxxx-xxxx-xxxx)
   - No extra spaces at start/end
   - No line breaks

4. **Contact Support:**
   - If still failing, email: sac@tilopay.com
   - Include: "API connection test failing in sandbox mode"
   - Don't include your actual credentials in email

---

## Part 6: Enable Provider (Production)

**⚠️ CRITICAL:** Only do this after successful testing in sandbox!

### Step 6.1: Switch to Production

1. Open TiloPay provider in Odoo
2. **Uncheck** "Use Sandbox Environment" ☐
3. **Replace credentials** with production credentials:
   - Production API Key
   - Production API User
   - Production API Password
   - Production Secret Key
4. Click **Save**

### Step 6.2: Test Production Connection

1. Click **Test Connection** again
2. Wait for response
3. Should see: "Connection test successful" ✅

**If it fails:**
- Verify you're using PRODUCTION credentials (not test)
- Double-check you copied them correctly
- Test credentials won't work in production mode

### Step 6.3: Enable Provider

1. At top of form, find **State** field
2. Change from **Disabled** to **Enabled**
3. Click **Save**

**⚠️ WARNING:**
- Once enabled, provider is LIVE
- Members can start making real payments
- Real money will be processed
- Double-check everything first!

### Step 6.4: Publish Provider

1. Find **Is Published** checkbox
2. Check it: ☑️
3. Click **Save**

**What this does:**
- Makes TiloPay visible as payment option
- Shows in member portal
- Members can select it during checkout

**✅ Provider is now LIVE and accepting payments!**

---

## Part 7: Test with Real Payment (Optional but Recommended)

### Step 7.1: Create Test Invoice

1. Go to: **Accounting > Customers > Invoices**
2. Click **Create**
3. Fill in:
   - **Customer:** Select yourself or test member
   - **Invoice Lines:** Add a ₡100 test item
4. Click **Confirm** (top-left)
5. Invoice state: **Posted** ✅

### Step 7.2: Make Test Payment

1. **Option A - Member Portal:**
   - Log out of Odoo
   - Go to member portal: `https://yourgym.com/my/invoices`
   - Log in as test member
   - Find the ₡100 invoice
   - Click **Pay Online Now**

2. **Option B - Direct:**
   - Open the invoice in Odoo
   - Click **Pay Now** button (if visible)

3. **Complete Payment:**
   - You'll be redirected to TiloPay payment page
   - Select payment method (SINPE or Card)
   - Use real payment method (only ₡100)
   - Complete the payment

4. **Verify Results:**
   - You should be redirected back to portal
   - Should see: "Payment Successful" ✅
   - Invoice should be marked "Paid"
   - You should receive e-invoice via email

**Expected Timeline:**
- Payment redirect: Instant
- Payment processing: 5-30 seconds
- Webhook notification: 5-60 seconds
- E-invoice generation: 1-2 minutes
- Email delivery: 2-5 minutes

### Step 7.3: Verify in Odoo

1. Go to: **Accounting > Configuration > Payment Transactions**
2. Find your test transaction (top of list)
3. Verify:
   - State: **Done** ✅
   - Provider: **TiloPay**
   - Amount: ₡100
   - Payment Method: SINPE or Card
   - Webhook Received: ✅ (checked)

4. Open the invoice:
   - Payment State: **Paid** ✅
   - Payment Method: 06-SINPE Móvil or 02-Tarjeta
   - E-Invoice Generated: ✅
   - PDF attached
   - Email sent

**✅ If all checks pass, your TiloPay integration is working perfectly!**

---

## Part 8: Monitor & Maintain

### Daily Monitoring (First Week)

**Check daily for first 7 days:**

1. **Transaction Success Rate:**
   - Go to: **Accounting > Configuration > Payment Transactions**
   - Filter: Provider = TiloPay, Last 24 hours
   - Goal: >95% success rate

2. **Webhook Delivery:**
   - Check: Webhook Received = ✅
   - Goal: 100% of transactions have webhook

3. **E-Invoice Generation:**
   - Check paid invoices have e-invoice attached
   - Goal: 100% automatic generation

4. **Member Feedback:**
   - Ask members about payment experience
   - Watch for support tickets
   - Goal: <5 support tickets per week

### Weekly Monitoring (Ongoing)

**Check weekly:**

1. **Payment Volume:**
   - How many payments processed
   - Total amount
   - Average transaction size

2. **Payment Method Mix:**
   - SINPE vs Cards ratio
   - Optimize based on fees

3. **Failed Payments:**
   - Review reasons for failures
   - Common error patterns
   - Member communication needs

4. **Reconciliation:**
   - Verify all payments matched invoices
   - Check for any manual reconciliation needed
   - Goal: 100% automatic

### Monthly Maintenance

**Check monthly:**

1. **Transaction Fees Review:**
   - Calculate actual fees paid
   - Compare to negotiated rates
   - Ensure no surprise charges

2. **Credential Rotation:** (Security best practice)
   - Consider rotating API credentials every 3-6 months
   - Contact TiloPay to generate new credentials
   - Update in Odoo
   - Test before deploying

3. **Webhook Health:**
   - Verify webhook still configured in TiloPay
   - Check for any webhook errors in logs
   - Test webhook delivery

4. **Performance Metrics:**
   - Average payment time
   - Member adoption rate
   - Time saved vs manual processing

---

## Troubleshooting Guide

### Issue: "Pay Now" Button Doesn't Appear

**Possible Causes:**
- Provider not enabled
- Provider not published
- Invoice already paid
- Invoice not posted
- Customer missing email

**Solutions:**
1. Check provider State = Enabled
2. Check provider Is Published = ✅
3. Verify invoice Payment State = Not Paid
4. Verify invoice State = Posted
5. Add email to customer record

### Issue: Payment Redirect Fails

**Symptoms:** Error when clicking "Pay Now"

**Possible Causes:**
- Invalid API credentials
- Provider disabled
- Sandbox/production mismatch

**Solutions:**
1. Check Odoo logs for error details
2. Test connection again
3. Verify environment mode matches credentials
4. Check internet connectivity

### Issue: Payment Completes but Invoice Not Marked Paid

**Symptoms:** Member pays but invoice still shows "Not Paid"

**Possible Causes:**
- Webhook not received
- Webhook signature invalid
- Transaction processing error

**Solutions:**
1. Go to transaction record
2. Check: Webhook Received field
3. If No webhook:
   - Click **Refresh Status** button
   - Manually query TiloPay for status
4. Check webhook configuration in TiloPay dashboard
5. Verify Secret Key in Odoo matches TiloPay

### Issue: E-Invoice Not Generated

**Symptoms:** Invoice marked paid but no e-invoice

**Possible Causes:**
- l10n_cr_einvoice module issue
- Hacienda credentials missing
- Integration not triggered

**Solutions:**
1. Verify l10n_cr_einvoice is installed
2. Check Hacienda credentials configured
3. Manually generate e-invoice:
   - Open invoice
   - Click **Generate E-Invoice** button
4. Check Odoo logs for errors

### Issue: Members Report Payment Confusion

**Symptoms:** Members don't know how to pay online

**Solutions:**
1. Add clear instructions in portal
2. Send announcement email (see templates)
3. Add tutorial video
4. Provide support contact
5. Consider in-person training session

---

## Security Checklist

Before going live, verify:

- [ ] HTTPS enabled on domain (not HTTP)
- [ ] SSL certificate valid (not expired, not self-signed)
- [ ] Secret Key configured for webhook verification
- [ ] Production credentials (not test) in production
- [ ] Credentials stored securely (not in version control)
- [ ] Only system admins can view credentials
- [ ] Webhook URL uses HTTPS
- [ ] Transaction logging enabled
- [ ] Regular credential rotation scheduled
- [ ] Two-factor authentication on TiloPay account

---

## Performance Optimization

### Optimize for SINPE Móvil (Lower Fees)

**Goal:** Maximize SINPE usage (1.0-1.5% vs 3.5-3.9% cards)

**Strategies:**
1. **Make SINPE default option** in payment page
2. **Show fee comparison** to members
3. **Highlight savings:** "Pay with SINPE and save!"
4. **Mobile-optimize** payment flow (SINPE is mobile-first)
5. **Education campaign** about SINPE benefits

**Expected Impact:**
- Increase SINPE ratio from 50% to 70%
- Save ₡30-40K monthly in fees

### Optimize Payment Success Rate

**Goal:** >98% payment success rate

**Strategies:**
1. **Test all payment flows** before launch
2. **Monitor failed payments** daily
3. **Improve error messages** (user-friendly)
4. **Add payment retry option** for failed payments
5. **Provide alternative payment methods**

### Optimize Member Experience

**Goal:** <3 minutes from invoice to paid

**Strategies:**
1. **One-click payment** from invoice email
2. **Mobile-responsive** payment pages
3. **Clear instructions** at each step
4. **Instant confirmation** messages
5. **Automatic e-invoice** delivery

---

## Support Contacts

### TiloPay Support
- **Email:** sac@tilopay.com
- **Developer Portal:** https://cst.support.tilopay.com/servicedesk/customer/portal/21
- **Documentation:** https://tilopay.com/documentacion
- **Phone:** [Check TiloPay website for current number]

### Odoo/Module Support
- **Internal:** Your IT team / System administrator
- **External:** GMS Development Team (if applicable)

### Emergency Contacts
- **Payment System Down:** Disable provider, use manual payments
- **Security Issue:** Rotate credentials immediately
- **TiloPay Outage:** Check https://status.tilopay.com/ (if available)

---

## Appendix: Configuration Quick Reference

### Sandbox Configuration
```
Environment: Sandbox ☑️
API Key: 6609-5850-8330-8034-3464
API User: lSrT45
API Password: Zlb8H9
State: Enabled
Published: Yes
```

### Production Configuration
```
Environment: Sandbox ☐ (unchecked)
API Key: [Your production API key]
API User: [Your production user]
API Password: [Your production password]
Secret Key: [Your production secret]
State: Enabled
Published: Yes
```

### Payment Methods (Recommended)
```
SINPE Móvil: ☑️ Enabled
Cards: ☑️ Enabled
Yappy: ☐ Disabled (unless serving Panama)
```

---

**Setup Complete!** 🎉

Your TiloPay payment gateway is now configured and ready to process online payments for your gym members.

**Next Steps:**
1. Monitor transactions daily for first week
2. Train staff on new payment system
3. Announce to members (use email templates)
4. Collect feedback and optimize

**Questions?** Review troubleshooting section or contact support.

---

**Document Version:** 1.0
**Last Updated:** 2025-12-28
**Author:** GMS Development Team
