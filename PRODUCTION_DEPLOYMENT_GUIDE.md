# GMS E-Invoice Production Deployment Guide

**System:** l10n_cr_einvoice - Costa Rica Electronic Invoicing
**Version:** 1.0
**Status:** Production Ready
**Last Tested:** December 28, 2025

---

## Prerequisites

- [x] Odoo 19.0 running in Docker
- [x] Module l10n_cr_einvoice installed
- [x] All tests passing (100% Phase 1 & 2)
- [ ] Production X.509 certificate from Banco Central de Costa Rica
- [ ] Hacienda production API credentials

---

## Deployment Steps

### Step 1: Backup Current Database

```bash
# Backup database before deployment
docker exec gms_postgres pg_dump -U odoo gms_validation > backup_pre_prod_$(date +%Y%m%d).sql

# Verify backup
ls -lh backup_pre_prod_*.sql
```

### Step 2: Configure Production Certificate

**Location:** Settings → Companies → Company Settings → E-Invoice Configuration

1. Click on your company (GMS Gym)
2. Navigate to E-Invoice Configuration section
3. Upload production certificate:
   - Field: **Digital Certificate**
   - File: Your production `.p12` or `.pfx` file
   - File size: Typically 5-15 KB

4. Enter certificate password:
   - Field: **Private Key Password**
   - Value: Your certificate PIN/password

5. Save the changes

**Verify Certificate:**

Run test to verify certificate loading:

```bash
python3 -c "
import xmlrpc.client

ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'  # Change to production DB name
USERNAME = 'admin'
PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

uid = common.authenticate(DB, USERNAME, PASSWORD, {})

result = models.execute_kw(
    DB, uid, PASSWORD,
    'l10n_cr.certificate.manager', 'get_certificate_info',
    [1]  # Company ID
)

print('Certificate Info:')
print(f\"  Subject: {result.get('subject_cn')}\")
print(f\"  Valid Until: {result.get('not_after')}\")
print(f\"  Days Remaining: {result.get('days_until_expiry')}\")
print(f\"  Is Valid: {result.get('is_valid')}\")
"
```

Expected output:
```
Certificate Info:
  Subject: YOUR COMPANY NAME
  Valid Until: 2027-XX-XX
  Days Remaining: XXX
  Is Valid: True
```

### Step 3: Configure Hacienda API Credentials

**Location:** Settings → Companies → Company Settings → Hacienda API Configuration

1. **Hacienda Environment:**
   - For testing: Select "Sandbox (Testing)"
   - For production: Select "Production"

2. **Hacienda API Username:**
   - Enter your Hacienda API username
   - Format: Usually your identification number

3. **Hacienda API Password:**
   - Enter your Hacienda API password

4. Save the changes

**Test API Connection:**

```bash
python3 test_phase3_api.py
```

Expected: Connection successful (not 403 Unauthorized)

### Step 4: Configure Email Notifications

**Location:** Settings → Technical → Email → Templates

1. Find or create "E-Invoice Email Template"
2. Configure template:

```xml
Email Subject: Electronic Invoice ${object.name}

Email Body:
Dear ${object.partner_id.name},

Please find attached your electronic invoice ${object.name}.

Invoice Details:
- Number: ${object.name}
- Date: ${object.invoice_date}
- Amount: ${object.amount_total} ${object.currency_id.name}
- Clave: ${object.clave}

This is an official electronic invoice authorized by the Ministry of Finance of Costa Rica.

Best regards,
${object.company_id.name}
```

3. Attachments configuration:
   - Attach: `xml_attachment_id` (Signed XML)
   - Attach: `pdf_attachment_id` (PDF Invoice)

### Step 5: Configure Company Information

**Location:** Settings → Companies → Company Settings

Verify/update these critical fields:

1. **Company Information:**
   - Legal Name: Must match certificate
   - Tax ID (VAT): Your cédula jurídica (10 digits)
   - Phone: International format (+506-XXXX-XXXX)
   - Email: Official company email

2. **E-Invoice Configuration:**
   - Emisor Location Code: 8-digit code (Provincia-Canton-Distrito-Barrio)
     - Example: 01010100 (San José Centro)
   - Auto-generate E-Invoice: ☑ Enabled
   - Auto-submit to Hacienda: ☐ Disabled initially (enable after testing)
   - Auto-send Email: ☑ Enabled

### Step 6: Test Complete Workflow

**Create Test Invoice:**

1. Go to Accounting → Customers → Invoices
2. Create New Invoice
3. Select a customer (ensure customer has valid VAT number)
4. Add products/services
5. Validate the invoice

**Expected Behavior:**

1. Invoice validated → State: "Posted"
2. E-invoice auto-generated → State: "Generated"
3. XML created with valid clave
4. User clicks "Sign XML" → State: "Signed"
5. User clicks "Submit to Hacienda" → State: "Submitted"
6. System checks status → State: "Accepted" or "Rejected"
7. If accepted, email sent automatically (if enabled)

**Verify Each Step:**

```bash
# Monitor Odoo logs
docker logs -f gms_odoo | grep -i "einvoice\|hacienda\|signature"
```

Look for:
- "XML document signed successfully"
- "Submitting to Hacienda"
- "Document accepted by Hacienda"

### Step 7: Production Cutover

**Pre-Cutover Checklist:**

- [ ] Production certificate uploaded and verified
- [ ] Hacienda production credentials configured
- [ ] API connection test successful
- [ ] Email templates configured
- [ ] Test invoice submitted and accepted by Hacienda
- [ ] User training completed
- [ ] Support team briefed
- [ ] Backup completed

**Cutover Steps:**

1. **Switch to Production Environment:**
   ```
   Settings → Companies → Hacienda Environment → Production
   ```

2. **Enable Auto-Submit (Optional):**
   ```
   Settings → Companies → Auto-submit to Hacienda → ☑ Enabled
   ```

3. **Process First Real Invoice:**
   - Create invoice for a real customer
   - Verify all data is correct
   - Submit to Hacienda
   - Monitor for acceptance
   - Verify email sent to customer

4. **Monitor for 24 Hours:**
   - Process 5-10 invoices
   - Verify all are accepted
   - Check customer email delivery
   - Monitor error logs

---

## Troubleshooting

### Certificate Issues

**Problem:** "Certificate not configured" error

**Solution:**
1. Verify certificate uploaded: Settings → Companies → Digital Certificate
2. Check certificate password is correct
3. Run certificate verification test (Step 2)

**Problem:** "Certificate expired" error

**Solution:**
1. Check certificate expiry date
2. Obtain new certificate from Banco Central
3. Upload new certificate

### API Issues

**Problem:** "Unauthorized" error (403)

**Solution:**
1. Verify API credentials
2. Check environment (Sandbox vs Production)
3. Contact Hacienda support to verify credentials

**Problem:** "Connection timeout" error

**Solution:**
1. Check internet connection
2. Verify Hacienda API status
3. Check firewall settings (ports 443 must be open)

### Signature Issues

**Problem:** "Invalid signature" rejection

**Solution:**
1. Verify certificate is valid (not expired)
2. Check certificate matches company tax ID
3. Re-sign the document
4. Check XMLDSig structure with test suite

### Email Issues

**Problem:** Emails not sending

**Solution:**
1. Verify email template configured
2. Check SMTP settings: Settings → Technical → Email → Outgoing Mail Servers
3. Test email manually from template
4. Check customer email address is valid

---

## Monitoring and Maintenance

### Daily Monitoring

Check these metrics daily for first week:

```bash
# Count invoices by state
docker exec gms_odoo psql -U odoo -d gms_validation -c "
SELECT state, COUNT(*)
FROM l10n_cr_einvoice_document
WHERE create_date > NOW() - INTERVAL '24 hours'
GROUP BY state;"
```

Expected states:
- `draft` - New, not yet processed
- `generated` - XML created
- `signed` - Digitally signed
- `submitted` - Sent to Hacienda
- `accepted` - Approved by Hacienda
- `rejected` - Rejected by Hacienda (investigate)
- `error` - System error (investigate immediately)

### Certificate Expiry Monitoring

Set up reminder 30 days before expiry:

```bash
# Check certificate expiry
python3 -c "
import xmlrpc.client
ODOO_URL = 'http://localhost:8070'
DB = 'gms_validation'
USERNAME = 'admin'
PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
uid = common.authenticate(DB, USERNAME, PASSWORD, {})

result = models.execute_kw(DB, uid, PASSWORD,
    'l10n_cr.certificate.manager', 'get_certificate_info', [1])

days = result.get('days_until_expiry')
if days < 30:
    print(f'WARNING: Certificate expires in {days} days!')
else:
    print(f'Certificate valid for {days} days')
"
```

### Error Log Monitoring

Monitor Odoo logs for issues:

```bash
# Show last 100 e-invoice related errors
docker logs gms_odoo 2>&1 | grep -i "error.*einvoice" | tail -100
```

### Performance Monitoring

Track processing times:

```bash
# Average processing time per invoice
docker exec gms_odoo psql -U odoo -d gms_validation -c "
SELECT
  AVG(EXTRACT(EPOCH FROM (write_date - create_date))) as avg_seconds
FROM l10n_cr_einvoice_document
WHERE state = 'accepted'
  AND create_date > NOW() - INTERVAL '24 hours';"
```

Expected: < 5 seconds average

---

## Rollback Plan

If issues occur after deployment:

### Immediate Rollback

1. **Disable auto-submit:**
   ```
   Settings → Companies → Auto-submit to Hacienda → ☐ Disabled
   ```

2. **Process invoices manually:**
   - Users create invoices normally
   - Admin reviews and submits manually
   - Gives time to investigate issues

### Full Rollback

If critical issues require full rollback:

```bash
# Stop Odoo
docker stop gms_odoo

# Restore backup
docker exec -i gms_postgres psql -U odoo -d gms_validation < backup_pre_prod_YYYYMMDD.sql

# Start Odoo
docker start gms_odoo

# Verify system operational
docker logs -f gms_odoo
```

---

## Support Contacts

**Technical Support:**
- Odoo Logs: `docker logs gms_odoo`
- Database: `gms_validation` on `localhost:5432`
- Module: `l10n_cr_einvoice` in `/mnt/extra-addons/`

**Hacienda Support:**
- API Documentation: https://www.hacienda.go.cr/
- Technical Support: consult@hacienda.go.cr
- Phone: +506 2539-4760

**Certificate Support:**
- Banco Central de Costa Rica
- Digital Certificates Division

---

## Post-Deployment Checklist

**Week 1:**
- [ ] Process minimum 10 invoices
- [ ] All invoices accepted by Hacienda
- [ ] Customer emails delivered successfully
- [ ] No error state invoices
- [ ] Performance within acceptable range (< 5s)
- [ ] Users comfortable with workflow

**Week 2:**
- [ ] Enable auto-submit if all tests passed
- [ ] Monitor daily metrics
- [ ] Review any rejected invoices
- [ ] Fine-tune email templates if needed

**Month 1:**
- [ ] Review monthly statistics
- [ ] Check certificate expiry date
- [ ] Plan for certificate renewal if needed
- [ ] Document any issues and resolutions

---

**Deployment Guide Version:** 1.0
**Last Updated:** December 28, 2025
**Status:** Ready for Production Deployment
