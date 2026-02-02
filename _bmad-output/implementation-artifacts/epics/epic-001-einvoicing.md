# Epic 001: Costa Rica Electronic Invoicing (Tribu-CR v4.4)

**Status**: 75% Complete (6/8 phases)
**Priority**: Critical
**Started**: 2025-12-28
**Last Updated**: 2025-02-01
**Current Phase**: Testing & Certification (Phase 7)
**Dependencies**: Odoo 19 Core, l10n_cr module

## Overview

Implement complete Costa Rica electronic invoicing compliance system for GMS using Tribu-CR v4.4 specification. This enables the gym to legally issue electronic invoices, comply with Ministry of Finance (Hacienda) regulations, and automate billing workflows.

## Business Value

- **Legal Compliance**: Meet Costa Rica tax authority requirements
- **Operational Efficiency**: Automate invoice generation and submission
- **Customer Experience**: Digital invoices with QR codes, automatic delivery
- **Revenue Protection**: Prevent tax audit issues and penalties
- **Scalability**: Handle growing membership base automatically

## Scope

### In Scope

1. **v4.4 XML Generation** (Phase 1) ✅ COMPLETE
   - Factura Electrónica (FE)
   - Tiquete Electrónico (TE)
   - Nota de Crédito (NC)
   - Nota de Débito (ND)

2. **Digital Signature** (Phase 2) ✅ COMPLETE
   - X.509 certificate handling
   - XMLDSig signing
   - Certificate validation

3. **Hacienda API Integration** (Phase 3) ✅ COMPLETE
   - Submit signed invoices
   - Check acceptance status
   - Handle responses and errors
   - OAuth2 authentication
   - Intelligent retry queue

4. **User Interface** (Phase 4) ✅ COMPLETE
   - E-invoice management views
   - Invoice form integration
   - Configuration screens
   - Dashboards and statistics
   - Bulk operation wizards

5. **PDF & Email** (Phase 5) ✅ COMPLETE
   - QR code generation
   - PDF invoice reports
   - Automated customer emails

6. **GMS Integration** (Phase 6) 🔄 NEEDS COMPLETION
   - Membership billing
   - Recurring subscriptions
   - POS integration (basic)
   - Gym POS store type card (NEW)
   - Payment methods
   - Discount codes

7. **Testing & Certification** (Phase 7) 🔄 MOSTLY COMPLETE
   - Unit and integration tests (100% pass rate - 301/301)
   - POS integration testing (PENDING)
   - Full UI workflow testing (PENDING)
   - Hacienda sandbox validation (PENDING)
   - Production certification

8. **Production Deployment** (Phase 8) ⏳ PENDING
   - Migration strategy
   - User training
   - Go-live support

### Out of Scope

- International invoicing (non-Costa Rica)
- Legacy invoice migration
- Custom invoice designs (beyond Hacienda requirements)

## Technical Architecture

### Components

```
l10n_cr_einvoice/
├── models/
│   ├── einvoice_document.py      ✅ Main e-invoice lifecycle
│   ├── xml_generator.py           ✅ v4.4 XML generation
│   ├── xsd_validator.py           ✅ Schema validation
│   ├── hacienda_api.py            ✅ API client
│   ├── certificate_manager.py     🚧 Phase 2
│   ├── xml_signer.py              🚧 Phase 2
│   ├── account_move.py            ✅ Invoice integration
│   ├── res_company.py             ✅ Company configuration
│   └── res_config_settings.py     ✅ Settings
├── views/                         ⏳ Phase 4
├── reports/                       ⏳ Phase 5
├── security/                      ✅ Access control
├── data/                          ✅ Sequences, defaults
└── tests/                         ⏳ Phase 7
```

### Integration Points

- **account.move**: Customer invoices → automatic e-invoice creation
- **res.company**: Hacienda credentials, certificates, configuration
- **res.partner**: Customer identification (cédula, passport, etc.)
- **product.product**: Cabys codes for tax classification
- **sale.subscription**: Recurring membership billing
- **pos.order**: Point of sale → tiquetes electrónicos

## Success Criteria

### Phase 1 ✅ COMPLETE
- [x] Generate valid v4.4 XML for all document types
- [x] Pass XSD schema validation
- [x] Generate unique 50-digit clave
- [x] Integrate with Odoo invoice workflow

### Phase 2 ✅ COMPLETE
- [x] Load and validate X.509 certificates
- [x] Sign XML with XMLDSig
- [x] Verify signed XML structure
- [x] Pass signature validation tests
**Completed**: 2025-02-01
**Verified**: Sandbox certificate loading, RSA-SHA256 signing, XAdES-EPES structure

### Phase 3 ✅ COMPLETE
- [x] Submit signed invoices to Hacienda sandbox
- [x] Receive acceptance confirmations
- [x] Handle rejection errors gracefully
- [x] Store Hacienda responses
- [x] OAuth2 authentication implemented
- [x] Intelligent retry queue with 7 error categories
**Completed**: 2025-12-29

### Phase 4 ✅ COMPLETE
- [x] User can manage e-invoices from UI
- [x] Configuration screen for Hacienda setup
- [x] Smart buttons on invoices
- [x] Status indicators and alerts
- [x] Dashboard with real-time statistics
- [x] Bulk operation wizards
**Completed**: 2025-12-29

### Phase 5 ✅ COMPLETE
- [x] Generate QR codes per Hacienda spec
- [x] PDF invoice with e-invoice data
- [x] Email template with XML attachment
- [x] Automated customer delivery
**Completed**: 2025-12-29

### Phase 6 🔄 NEEDS COMPLETION
- [x] Membership billing automation
- [x] POS tiquete generation (basic)
- [x] Discount codes integration
- [x] Payment method tracking
- [x] CIIU economic activity codes
- [ ] **Gym POS store type card** - Add "Gym" option to POS store selection
- [ ] Gym-specific POS configuration template
- [ ] Gym product catalog (memberships, day passes, training)
- [ ] POS offline queue testing and fixes
- [ ] Complete POS→TE e-invoice integration testing
**Status**: Core features done, Gym POS and testing pending

### Phase 7 🔄 MOSTLY COMPLETE
- [x] Comprehensive test coverage (301/301 tests passing - 100%)
- [x] Unit tests for all core features
- [x] Integration tests for Hacienda API (mocked)
- [x] Tax reports testing (D101, D150, D151)
- [x] XAdES-EPES signature testing (48 tests)
- [ ] POS integration testing
- [ ] Full UI workflow integration testing
- [ ] Hacienda sandbox end-to-end validation (manual)
- [ ] Production certification
**Status**: Core testing complete, integration testing pending

### Phase 8 ⏳ PENDING
- [ ] Acquire production certificate
- [ ] Production environment configuration
- [ ] User training materials
- [ ] Go-live checklist
- [ ] Successful go-live

## Current Progress

### Completed (Phase 1)

✅ **Module Structure**
- Complete addon scaffolding
- Dependencies configured
- Security rules defined

✅ **XML Generation Engine**
- v4.4 namespace support
- All document types (FE, TE, NC, ND)
- Tax calculations (IVA 13%, 4%, 2%, 1%, Exento)
- Line items with discounts
- Payment terms and methods

✅ **Validation Framework**
- XSD schema caching
- Auto-download from Hacienda CDN
- Detailed error reporting
- Version 4.4 compliance

✅ **Clave Generation**
- 50-digit unique keys
- Check digit calculation
- Sequential numbering

✅ **API Client Foundation**
- Sandbox/production URLs
- Basic authentication
- Submit/status methods

### Completed (Phase 2) ✅

✅ **Digital Signature** - VERIFIED 2025-02-01
- Certificate manager implementation
- XML signing with XMLDSig
- Sandbox testing completed

**Test Results**:
- ✅ Certificate valid until 2029-12-27
- ✅ RSA-SHA256 signing operational
- ✅ XAdES-EPES structure verified
- ✅ All cryptographic components working

### Pending (Phases 3-8)

⏳ API Integration → UI → PDF/Email → GMS Features → Testing → Deployment

## Timeline & Effort

**Total Estimate**: 8 phases
**Completed**: Phase 1 + Phase 2 (verified working)
**Current**: Phase 3 (Hacienda API Integration)
**Budget**: $13,000 - $15,000 total
**Status**: Foundation phases complete, moving to API integration

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Certificate validation issues | Medium | High | Test with sandbox cert first |
| API changes by Hacienda | Low | High | Monitor official documentation |
| Missing Cabys codes | High | Medium | Create product configuration wizard |
| Performance with high volume | Medium | Medium | Implement async processing |

## Dependencies

**External**:
- Hacienda API availability
- Valid X.509 certificate
- Internet connectivity

**Internal**:
- Odoo 19 installation
- l10n_cr module
- Python dependencies (lxml, xmlschema, cryptography, pyOpenSSL)

## Stories

1. **Story 001.1**: Digital Certificate Management ⏳
2. **Story 001.2**: XML Digital Signature ⏳
3. **Story 001.3**: Hacienda Sandbox Integration ⏳
4. **Story 001.4**: E-Invoice UI Views ⏳
5. **Story 001.5**: PDF & QR Code Generation ⏳
6. **Story 001.6**: Email Automation ⏳
7. **Story 001.7**: Membership Billing Integration ⏳
8. **Story 001.8**: Production Deployment ⏳

## Notes

- **Architecture Decision**: Build custom module vs. extend existing addon
  - Decision: Custom module for full control and GMS-specific requirements

- **Testing Strategy**: Sandbox → staging → production
  - All features must pass sandbox validation before production

- **Data Migration**: Not applicable (new implementation)

## References

- [Hacienda Official Docs](https://www.hacienda.go.cr/contenido/14185-factura-electronica)
- [v4.4 Specification](https://www.hacienda.go.cr/docs/Comprobantes_Electronicos_V4_4.pdf)
- [Tribu-CR Progress Report](./TRIBU-CR-MODULE-PROGRESS.md)
