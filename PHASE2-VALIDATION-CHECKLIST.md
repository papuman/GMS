# Phase 2: Digital Signature - Validation Checklist

## Pre-Deployment Validation

**Date**: _____________
**Validator**: _____________
**Environment**: Development / Staging / Production

---

## 1. Module Installation

- [ ] Module `l10n_cr_einvoice` shows as "Installed" in Apps
- [ ] No installation errors in Odoo log
- [ ] All dependencies installed (cryptography, pyOpenSSL, lxml, requests)
- [ ] Database migrations completed successfully

---

## 2. Certificate Management

### Certificate Upload
- [ ] Can upload PKCS#12 (.p12) certificate
- [ ] Can upload PEM certificate
- [ ] Can upload PEM private key
- [ ] Password field accepts input
- [ ] Certificate filename displays correctly
- [ ] Private key filename displays correctly

### Certificate Validation
- [ ] Certificate loads without errors
- [ ] Certificate info displays correctly:
  - [ ] Subject Common Name
  - [ ] Subject Organization
  - [ ] Issuer
  - [ ] Valid From date
  - [ ] Valid To date
  - [ ] Days until expiry
  - [ ] Is Valid status
- [ ] Expired certificate shows warning
- [ ] Certificate expiring in <30 days shows warning

### Error Handling
- [ ] Wrong password shows clear error message
- [ ] Corrupted certificate shows clear error message
- [ ] Missing private key (PEM) shows clear error message
- [ ] Mismatched certificate/key shows clear error message

---

## 3. XML Signing

### Basic Signing
- [ ] Can sign test XML
- [ ] Signature element added to XML
- [ ] Signature contains all required elements:
  - [ ] SignedInfo
  - [ ] SignatureValue
  - [ ] KeyInfo
  - [ ] X509Certificate
- [ ] Signed XML is well-formed
- [ ] Signature verification returns True

### Signature Structure
- [ ] Canonicalization method correct
- [ ] Signature method is RSA-SHA256
- [ ] Digest method is SHA-256
- [ ] Transform is enveloped-signature
- [ ] DigestValue is Base64 encoded
- [ ] SignatureValue is Base64 encoded
- [ ] X509Certificate is Base64 encoded

### Error Handling
- [ ] Invalid XML shows clear error
- [ ] Missing certificate shows clear error
- [ ] Invalid private key shows clear error

---

## 4. Hacienda API Integration

### Configuration
- [ ] Can select Sandbox environment
- [ ] Can select Production environment
- [ ] Can enter API username
- [ ] Can enter API password (masked)
- [ ] Configuration saves correctly

### Connection Testing
- [ ] Test Connection button works
- [ ] Valid credentials show success message
- [ ] Invalid credentials show error message
- [ ] Network error shows clear error message
- [ ] Timeout shows clear error message

### API Operations
- [ ] Can submit test invoice
- [ ] Can check document status
- [ ] Response parsed correctly
- [ ] Estado field extracted correctly
- [ ] Response message decoded (if base64)

### Retry Logic
- [ ] Network timeout triggers retry
- [ ] 429 (rate limit) triggers retry
- [ ] 5xx error triggers retry
- [ ] 400 error does NOT retry
- [ ] 401 error does NOT retry
- [ ] Exponential backoff working (2s, 4s, 8s)
- [ ] Max 3 attempts enforced

### ID Type Detection
- [ ] 9-digit number detected as type 01 (Cédula Física)
- [ ] 10-digit starting with 3 detected as type 02 (Cédula Jurídica)
- [ ] 10-digit not starting with 3 detected as type 04 (NITE)
- [ ] 11-12 digit number detected as type 03 (DIMEX)
- [ ] Other formats detected as type 05 (Extranjero)

---

## 5. Document Workflow

### State Transitions
- [ ] New document starts in 'draft' state
- [ ] Generate XML moves to 'generated' state
- [ ] Sign XML moves to 'signed' state
- [ ] Submit moves to 'submitted' state
- [ ] Accepted response moves to 'accepted' state
- [ ] Rejected response moves to 'rejected' state
- [ ] Error moves to 'error' state

### Action Buttons
- [ ] "Generate XML" visible in draft/error states
- [ ] "Sign XML" visible in generated state
- [ ] "Submit to Hacienda" visible in signed state
- [ ] "Check Status" visible in submitted state
- [ ] Buttons disabled in wrong states

### Document Fields
- [ ] xml_content populated after generation
- [ ] signed_xml populated after signing
- [ ] clave populated (50 digits)
- [ ] hacienda_response populated after submission
- [ ] hacienda_message populated
- [ ] hacienda_submission_date set correctly
- [ ] hacienda_acceptance_date set when accepted
- [ ] error_message populated on error

### Smart Buttons
- [ ] "View Invoice" button works
- [ ] "Download XML" button works (when XML available)
- [ ] "Download PDF" button works (when PDF available)
- [ ] "View Hacienda Response" button works (when response available)

---

## 6. User Interface

### Settings Page
- [ ] "Costa Rica Electronic Invoicing" section visible
- [ ] Environment radio buttons work
- [ ] API credentials fields work
- [ ] Test Connection button works
- [ ] Certificate upload works
- [ ] Private key upload works
- [ ] Key password field works
- [ ] Emisor location field works
- [ ] Automation checkboxes work
- [ ] Getting Started guide displays
- [ ] Save changes works

### Company Configuration
- [ ] "Hacienda (CR E-Invoicing)" tab visible
- [ ] All fields from Settings available
- [ ] Certificate requirements info displays
- [ ] Changes save correctly
- [ ] Only visible to Account Manager group

### E-Invoice Document Views
- [ ] Tree view displays documents
- [ ] State-based coloring works:
  - [ ] Draft: Muted
  - [ ] Generated: Info
  - [ ] Signed: Primary
  - [ ] Submitted: Warning
  - [ ] Accepted: Success
  - [ ] Rejected/Error: Danger
- [ ] Form view displays all fields
- [ ] Status bar shows workflow states
- [ ] Action buttons display correctly
- [ ] Smart buttons display correctly

---

## 7. Security & Access Control

### Invoice Users
- [ ] Can read e-invoice documents
- [ ] Can write e-invoice documents
- [ ] Can create e-invoice documents
- [ ] Cannot delete e-invoice documents

### Account Managers
- [ ] Can read e-invoice documents
- [ ] Can write e-invoice documents
- [ ] Can create e-invoice documents
- [ ] Can delete e-invoice documents
- [ ] Can access all wizards

### Readonly Users
- [ ] Can read e-invoice documents
- [ ] Cannot write e-invoice documents
- [ ] Cannot create e-invoice documents
- [ ] Cannot delete e-invoice documents

---

## 8. Complete Workflow Test

### Setup
- [ ] Certificate uploaded
- [ ] API credentials configured
- [ ] Test connection successful
- [ ] Emisor location set

### Test Invoice Creation
- [ ] Create test customer with valid identification
- [ ] Create test invoice with:
  - [ ] At least 1 line item
  - [ ] Valid tax configuration
  - [ ] Valid payment method
- [ ] Post invoice
- [ ] E-invoice document created automatically (if auto-generate enabled)

### XML Generation
- [ ] Click "Generate XML" button
- [ ] No errors displayed
- [ ] State changes to 'generated'
- [ ] Clave field populated (50 digits)
- [ ] xml_content field populated
- [ ] XML passes XSD validation

### XML Signing
- [ ] Click "Sign XML" button
- [ ] No errors displayed
- [ ] State changes to 'signed'
- [ ] signed_xml field populated
- [ ] Signature element present in XML
- [ ] XML attachment created

### Submission to Hacienda
- [ ] Click "Submit to Hacienda" button
- [ ] No errors displayed
- [ ] State changes to 'submitted'
- [ ] hacienda_submission_date set
- [ ] hacienda_response populated

### Status Checking
- [ ] Click "Check Status" button
- [ ] No errors displayed
- [ ] Response processed correctly
- [ ] State updates based on response:
  - [ ] 'accepted' if aceptado
  - [ ] 'rejected' if rechazado
  - [ ] 'submitted' if procesando/recibido
- [ ] hacienda_message displays correctly

### Acceptance Flow
- [ ] When accepted:
  - [ ] hacienda_acceptance_date set
  - [ ] State is 'accepted'
  - [ ] Error message cleared
  - [ ] Auto-send email triggered (if enabled)

### Rejection Flow
- [ ] When rejected:
  - [ ] State is 'rejected'
  - [ ] error_message populated with rejection reason
  - [ ] Can view rejection details

---

## 9. Error Handling

### Certificate Errors
- [ ] Missing certificate shows user-friendly error
- [ ] Expired certificate shows warning
- [ ] Invalid password shows clear error
- [ ] Corrupted file shows clear error

### XML Errors
- [ ] Invalid XML structure shows validation error
- [ ] XSD validation failure shows specific error
- [ ] Signing failure shows clear error

### API Errors
- [ ] Network timeout shows retry message
- [ ] Invalid credentials show auth error
- [ ] Server error shows retry message
- [ ] Validation error shows Hacienda message
- [ ] Max retries shows final error

### Recovery
- [ ] Can retry from 'error' state
- [ ] Error message cleared on successful retry
- [ ] Retry count increments correctly

---

## 10. Performance

### Certificate Loading
- [ ] PKCS#12 loads in <1 second
- [ ] PEM loads in <1 second
- [ ] Certificate info retrieves in <1 second

### XML Signing
- [ ] Small invoice (<10 lines) signs in <1 second
- [ ] Medium invoice (10-50 lines) signs in <2 seconds
- [ ] Large invoice (>50 lines) signs in <5 seconds

### API Calls
- [ ] Submit completes in <30 seconds (or shows retry)
- [ ] Status check completes in <30 seconds (or shows retry)
- [ ] Test connection completes in <10 seconds

---

## 11. Documentation

- [ ] PHASE2-IMPLEMENTATION-COMPLETE.md available
- [ ] PHASE2-QUICK-REFERENCE.md available
- [ ] PHASE2-SUMMARY.md available
- [ ] Epic 001 updated with Phase 2 completion
- [ ] Code includes comprehensive docstrings
- [ ] All methods documented
- [ ] Error messages are clear and helpful

---

## 12. Code Quality

- [ ] No syntax errors
- [ ] No runtime errors in log
- [ ] All imports resolve
- [ ] No deprecated Odoo API usage
- [ ] Follows Odoo coding standards
- [ ] No security vulnerabilities
- [ ] No SQL injection risks
- [ ] No XSS risks

---

## Sign-Off

### Development Environment
- [ ] All checks passed
- **Tested By**: ________________
- **Date**: ________________
- **Notes**: ________________

### Staging Environment
- [ ] All checks passed
- **Tested By**: ________________
- **Date**: ________________
- **Notes**: ________________

### Production Readiness
- [ ] Development tests passed
- [ ] Staging tests passed
- [ ] Sandbox validation completed
- [ ] Certificate uploaded (production)
- [ ] API credentials configured (production)
- [ ] Backup completed
- [ ] Rollback plan documented

**Approved By**: ________________
**Date**: ________________

---

## Issues Found

| # | Issue Description | Severity | Status | Resolution |
|---|------------------|----------|---------|------------|
| 1 |                  |          |         |            |
| 2 |                  |          |         |            |
| 3 |                  |          |         |            |

---

**Validation Status**: ☐ Passed  ☐ Failed  ☐ Passed with Issues

**Ready for Production**: ☐ Yes  ☐ No  ☐ Pending Fixes

---

**Document Version**: 1.0
**Last Updated**: 2025-12-29
