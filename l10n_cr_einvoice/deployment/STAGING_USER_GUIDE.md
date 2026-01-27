# Staging Environment User Guide

**Version:** 19.0.1.8.0
**Environment:** Local Staging (Docker)
**Purpose:** User acceptance testing and validation

---

## Table of Contents

1. [Access Information](#access-information)
2. [Initial Setup](#initial-setup)
3. [Test Scenarios](#test-scenarios)
4. [Common Tasks](#common-tasks)
5. [Troubleshooting](#troubleshooting)
6. [Feedback Process](#feedback-process)

---

## Access Information

### Web Interfaces

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Odoo Web | http://localhost:8070 | admin | StagingAdmin2024!SecurePass |
| Nginx Proxy | http://localhost:8080 | - | - |
| Grafana | http://localhost:3001 | admin | StagingGrafana2024! |
| Prometheus | http://localhost:9091 | - | - |

### Database Access (Advanced)

| Parameter | Value |
|-----------|-------|
| Host | localhost |
| Port | 5433 |
| Database | staging_gms |
| Username | odoo_staging |
| Password | StagingDB2024!SecurePass |

---

## Initial Setup

### Step 1: Access Odoo

1. Open your web browser
2. Navigate to http://localhost:8070
3. You should see the Odoo login page
4. Login with credentials:
   - **Email:** admin
   - **Password:** StagingAdmin2024!SecurePass

### Step 2: Activate Developer Mode

1. Go to **Settings** (gear icon in top menu)
2. Scroll to bottom of page
3. Click **Activate the developer mode**
4. Wait for page to reload

### Step 3: Configure Hacienda Credentials

1. Go to **Settings** > **Technical** > **System Parameters**
2. Add Hacienda sandbox credentials:
   - `hacienda.api.url`: https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1
   - `hacienda.username`: [Your sandbox username]
   - `hacienda.password`: [Your sandbox password]
3. Click **Save**

### Step 4: Upload Test Certificate

1. Go to **Settings** > **General Settings**
2. Scroll to **Costa Rica E-Invoicing** section
3. Upload your test certificate (.p12 file)
4. Enter certificate password
5. Click **Save**

### Step 5: Verify Company Information

1. Go to **Settings** > **Companies**
2. Open your company record
3. Verify and complete:
   - **Name:** Your company name
   - **VAT:** Company identification (e.g., 3-101-654321)
   - **Country:** Costa Rica
   - **Phone:** Company phone
   - **Email:** Company email
4. Click **Save**

---

## Test Scenarios

### Scenario 1: Create and Submit Basic Invoice

**Purpose:** Test basic invoice creation and e-invoice generation
**Duration:** 10-15 minutes
**Prerequisites:** Company configured, test certificate uploaded

#### Steps

1. **Navigate to Invoices**
   - Go to **Accounting** > **Customers** > **Invoices**
   - Click **Create**

2. **Fill Invoice Details**
   - **Customer:** Select a test customer (e.g., "Juan Pérez Rodríguez")
   - **Invoice Date:** Today's date
   - **Payment Method:** Select "Efectivo" (Cash)

3. **Add Invoice Lines**
   - Click **Add a line**
   - **Product:** Select "Membresía Mensual"
   - **Quantity:** 1
   - **Price:** Should auto-fill from product
   - Verify tax is applied correctly

4. **Validate Invoice**
   - Review all information
   - Click **Confirm** button
   - Invoice should change to "Posted" status

5. **Generate E-Invoice**
   - Click **Generate E-Invoice** button
   - XML should be generated automatically
   - Check **E-Invoice Status** field

6. **Sign E-Invoice**
   - Click **Sign E-Invoice** button
   - Document should be signed with certificate
   - Verify signature in **XML Signed** field

7. **Submit to Hacienda**
   - Click **Submit to Hacienda** button
   - System will send to sandbox API
   - Monitor **Hacienda Status** field

8. **Check Response**
   - Wait 30-60 seconds for response
   - Click **Check Status** button
   - Review response messages
   - Status should update to "Accepted" or show rejection reason

9. **Generate PDF**
   - Click **Generate PDF** button
   - PDF should include QR code
   - Download and verify formatting

10. **Send Email**
    - Click **Send by Email** button
    - Verify email template
    - Click **Send**

**Expected Results:**
- ✓ Invoice created and validated
- ✓ XML generated in v4.4 format
- ✓ Document signed successfully
- ✓ Submitted to Hacienda sandbox
- ✓ Status updated (Accepted/Rejected)
- ✓ PDF generated with QR code
- ✓ Email sent to customer

**Validation Checklist:**
- [ ] Invoice number assigned correctly
- [ ] Customer ID type and number correct
- [ ] Payment method code in XML (01 for Efectivo)
- [ ] Tax calculations accurate
- [ ] XML well-formed and valid
- [ ] Digital signature present
- [ ] Hacienda key (clave) generated
- [ ] QR code readable
- [ ] Email received

---

### Scenario 2: Create Invoice with Discounts

**Purpose:** Test discount codes functionality
**Duration:** 5-10 minutes
**Prerequisites:** Scenario 1 completed

#### Steps

1. **Create New Invoice**
   - Go to **Accounting** > **Customers** > **Invoices**
   - Click **Create**
   - Select customer

2. **Add Product with Discount**
   - Add product: "Proteína Whey 2kg"
   - Quantity: 2
   - Apply 10% discount
   - **Discount Code:** Select "01 - Descuento comercial"

3. **Add Product with Different Discount**
   - Add product: "Creatina Monohidrato 500g"
   - Quantity: 1
   - Apply 15% discount
   - **Discount Code:** Select "02 - Descuento por pronto pago"

4. **Validate and Submit**
   - Confirm invoice
   - Generate and sign e-invoice
   - Submit to Hacienda

**Expected Results:**
- ✓ Discount codes appear in XML
- ✓ Discount amounts calculated correctly
- ✓ Total reflects all discounts
- ✓ Hacienda accepts invoice with discounts

**Validation Checklist:**
- [ ] Discount percentages correct
- [ ] Discount codes in XML (01, 02)
- [ ] Line totals accurate
- [ ] Invoice total correct

---

### Scenario 3: Credit Note Creation

**Purpose:** Test credit note (refund) workflow
**Duration:** 5-10 minutes
**Prerequisites:** Scenario 1 completed with accepted invoice

#### Steps

1. **Open Original Invoice**
   - Find an accepted invoice from Scenario 1
   - Open the invoice

2. **Create Credit Note**
   - Click **Add Credit Note** button
   - Select reason: "03 - Devolución de mercadería"
   - Enter reason description
   - Click **Create Credit Note**

3. **Review Credit Note**
   - Verify it references original invoice
   - Check that amounts are negative
   - Verify customer information

4. **Submit Credit Note**
   - Confirm credit note
   - Generate e-invoice (type: NC)
   - Sign and submit to Hacienda

**Expected Results:**
- ✓ Credit note references original invoice
- ✓ Document type is "NC" (Nota de Crédito)
- ✓ Amounts are negative
- ✓ Hacienda accepts credit note
- ✓ Link to original invoice in XML

**Validation Checklist:**
- [ ] Reference to original invoice present
- [ ] Document type correct (NC)
- [ ] Reason code in XML
- [ ] Amounts negative
- [ ] Hacienda acceptance

---

### Scenario 4: POS Transaction (Tiquete Electrónico)

**Purpose:** Test point-of-sale e-invoice generation
**Duration:** 10 minutes
**Prerequisites:** POS configured

#### Steps

1. **Open Point of Sale**
   - Go to **Point of Sale**
   - Select POS session
   - Click **New Session**

2. **Create Sale**
   - Add products to cart:
     - Toalla Deportiva (2 units)
     - Botella de Agua 1L (1 unit)
   - Total should calculate automatically

3. **Add Customer Information**
   - Click **Customer** button
   - Select or create customer
   - Ensure customer has ID type and number

4. **Process Payment**
   - Click **Payment** button
   - Select payment method: SINPE Móvil
   - Enter SINPE transaction ID
   - Click **Validate**

5. **Generate Tiquete Electrónico**
   - System should automatically generate TE
   - TE should be submitted to Hacienda
   - Verify status in order details

6. **Print Receipt**
   - Receipt should include QR code
   - Verify all information correct

**Expected Results:**
- ✓ TE generated automatically
- ✓ Customer ID captured correctly
- ✓ Payment method correct (SINPE code: 04)
- ✓ SINPE transaction ID in XML
- ✓ Submitted to Hacienda
- ✓ QR code on receipt

**Validation Checklist:**
- [ ] Document type TE
- [ ] Customer ID present
- [ ] Payment method code correct
- [ ] SINPE transaction ID captured
- [ ] QR code present
- [ ] Hacienda acceptance

---

### Scenario 5: Bulk Operations

**Purpose:** Test batch processing capabilities
**Duration:** 10 minutes
**Prerequisites:** Multiple draft invoices

#### Steps

1. **Create Multiple Invoices**
   - Create 5 draft invoices with different customers
   - Leave them unconfirmed

2. **Bulk Validation**
   - Go to **Hacienda** > **E-Invoice Documents**
   - Select all draft invoices
   - Click **Action** > **Bulk Validate**
   - All should be confirmed

3. **Bulk Sign**
   - Select all validated invoices
   - Click **Action** > **Bulk Sign**
   - All should be signed

4. **Bulk Submit**
   - Select all signed invoices
   - Click **Action** > **Bulk Submit**
   - All should be submitted to Hacienda

5. **Monitor Status**
   - Wait 1-2 minutes
   - Click **Action** > **Bulk Check Status**
   - All statuses should update

**Expected Results:**
- ✓ Bulk operations process all selected documents
- ✓ No errors during processing
- ✓ All documents reach "Accepted" status
- ✓ Performance acceptable (< 5s per document)

**Validation Checklist:**
- [ ] All documents processed
- [ ] No validation errors
- [ ] All signatures valid
- [ ] All submissions successful
- [ ] Statuses updated correctly

---

### Scenario 6: Error Handling

**Purpose:** Test error scenarios and retry logic
**Duration:** 10 minutes
**Prerequisites:** Basic understanding of system

#### Steps

1. **Create Invalid Invoice**
   - Create invoice without customer ID
   - Try to generate e-invoice
   - System should show validation error

2. **Simulate Network Error**
   - Temporarily disconnect from network
   - Try to submit invoice
   - Should queue for retry

3. **Reconnect and Retry**
   - Reconnect network
   - Go to **Hacienda** > **Retry Queue**
   - Click **Process Queue**
   - Invoice should submit successfully

4. **Handle Rejection**
   - Create invoice with intentionally wrong data
   - Submit to Hacienda
   - Review rejection message
   - Fix issue and resubmit

**Expected Results:**
- ✓ Validation prevents invalid submissions
- ✓ Network errors handled gracefully
- ✓ Retry queue works correctly
- ✓ Rejection messages clear and actionable

**Validation Checklist:**
- [ ] Validation errors clear
- [ ] Offline queue works
- [ ] Retry successful
- [ ] Rejection messages helpful

---

### Scenario 7: Analytics and Reporting

**Purpose:** Test reporting and dashboard functionality
**Duration:** 10 minutes
**Prerequisites:** Multiple invoices created

#### Steps

1. **View Executive Dashboard**
   - Go to **Hacienda** > **Reports** > **Analytics Dashboard**
   - Review KPIs:
     - Total invoices
     - Acceptance rate
     - Revenue
     - Average processing time

2. **Generate Sales Report**
   - Go to **Hacienda** > **Reports** > **Sales Reports**
   - Select date range: This month
   - Click **Generate Report**
   - Export to Excel

3. **View Compliance Report**
   - Go to **Hacienda** > **Reports** > **Compliance Reports**
   - Select **Monthly Filing Report**
   - Review all submitted documents
   - Export to PDF

4. **Check Performance Metrics**
   - Go to **Hacienda** > **Reports** > **Performance Metrics**
   - Review API response times
   - Check retry efficiency
   - Monitor system health

**Expected Results:**
- ✓ Dashboard loads quickly (< 3s)
- ✓ All metrics display correctly
- ✓ Reports generate successfully
- ✓ Export functions work
- ✓ Data is accurate

**Validation Checklist:**
- [ ] Dashboard responsive
- [ ] Metrics accurate
- [ ] Excel export works
- [ ] PDF export works
- [ ] Data matches invoices

---

## Common Tasks

### How to Check Invoice Status

1. Go to **Accounting** > **Customers** > **Invoices**
2. Find your invoice
3. Check **Hacienda Status** field:
   - **Draft:** Not submitted
   - **Pending:** Waiting for Hacienda response
   - **Accepted:** Approved by Hacienda
   - **Rejected:** Rejected with error message

### How to Resend Email

1. Open invoice
2. Click **Send by Email** button
3. Verify recipient email
4. Click **Send**

### How to Download PDF

1. Open invoice
2. Click **Print** menu
3. Select **Invoice PDF**
4. PDF downloads automatically

### How to View XML

1. Open invoice
2. Scroll to **Technical Information** section
3. Click **Download XML** button
4. Save XML file

### How to Check Hacienda Response

1. Open invoice
2. Click **Response Messages** smart button
3. View all messages from Hacienda
4. Check timestamps and status

### How to Retry Failed Submission

1. Go to **Hacienda** > **Retry Queue**
2. Find failed document
3. Review error message
4. Fix issue in document
5. Click **Retry** button

---

## Troubleshooting

### Issue: Cannot Login

**Symptoms:** Login page shows error or credentials rejected

**Solutions:**
1. Verify credentials:
   - Username: admin
   - Password: StagingAdmin2024!SecurePass
2. Check if Odoo service is running:
   ```bash
   docker-compose -f docker/docker-compose.staging.yml ps
   ```
3. Restart Odoo if needed:
   ```bash
   docker-compose -f docker/docker-compose.staging.yml restart odoo-staging
   ```

### Issue: E-Invoice Generation Fails

**Symptoms:** "Generate E-Invoice" button shows error

**Solutions:**
1. Verify customer has ID type and number
2. Check payment method is selected
3. Ensure all invoice lines have products
4. Verify company VAT is configured
5. Check error log for specific message

### Issue: Cannot Submit to Hacienda

**Symptoms:** Submission fails with error

**Solutions:**
1. Verify Hacienda credentials configured
2. Check internet connectivity
3. Verify certificate is uploaded and valid
4. Review error message for specific issue
5. Check if document is signed

### Issue: PDF Not Generating

**Symptoms:** PDF button doesn't work

**Solutions:**
1. Ensure invoice is confirmed
2. Verify e-invoice is generated
3. Check QR code library installed
4. Review logs for errors

### Issue: Email Not Sending

**Symptoms:** Email send fails

**Solutions:**
1. Verify SMTP configured in settings
2. Check email address is valid
3. Verify internet connectivity
4. Check spam folder
5. Review email server logs

### Issue: Slow Performance

**Symptoms:** System is slow or unresponsive

**Solutions:**
1. Check Docker resources:
   ```bash
   docker stats
   ```
2. Restart services if needed
3. Clear browser cache
4. Check database connections
5. Review logs for errors

### Issue: Container Won't Start

**Symptoms:** Docker container fails to start

**Solutions:**
1. Check logs:
   ```bash
   docker-compose -f docker/docker-compose.staging.yml logs odoo-staging
   ```
2. Verify ports are available
3. Check disk space
4. Restart Docker
5. Rebuild containers if needed

---

## Feedback Process

### How to Report Issues

1. **Document the Issue**
   - Screenshot the error
   - Note the steps to reproduce
   - Record timestamp
   - Check logs if possible

2. **Classify Severity**
   - **Critical:** System unusable
   - **High:** Major feature broken
   - **Medium:** Minor issue, workaround exists
   - **Low:** Cosmetic or enhancement

3. **Submit Feedback**
   - Use issue tracking system
   - Include all documentation
   - Provide context (what you were trying to do)
   - Suggest expected behavior

### What to Test

Focus your testing on:

1. **Your Typical Workflows**
   - How you normally create invoices
   - Your most common document types
   - Your usual customer types

2. **Edge Cases**
   - Large invoices (many lines)
   - Special characters in names
   - Different ID types
   - Various payment methods

3. **Performance**
   - How fast operations complete
   - Any delays or timeouts
   - Bulk operation speed

4. **User Experience**
   - Is UI intuitive?
   - Are error messages helpful?
   - Is navigation logical?

### Feedback Checklist

After testing, please provide feedback on:

- [ ] Overall system performance
- [ ] Ease of use
- [ ] Error message clarity
- [ ] Missing features
- [ ] Documentation quality
- [ ] Training needs
- [ ] Production readiness concerns

---

## Additional Resources

### Documentation
- Administrator Guide: `deployment/README.md`
- Deployment Checklist: `deployment/DEPLOYMENT_CHECKLIST.md`
- Troubleshooting Guide: `deployment/README.md#troubleshooting`

### Support Contacts
- Technical Support: [Contact information]
- Training: [Contact information]
- Emergency: [Contact information]

### Useful Commands

**View logs:**
```bash
docker-compose -f docker/docker-compose.staging.yml logs -f odoo-staging
```

**Restart services:**
```bash
docker-compose -f docker/docker-compose.staging.yml restart
```

**Stop staging:**
```bash
docker-compose -f docker/docker-compose.staging.yml stop
```

**Start staging:**
```bash
docker-compose -f docker/docker-compose.staging.yml start
```

---

**Document Version:** 1.0
**Last Updated:** 2024-12-29
**For Questions:** Contact your system administrator
