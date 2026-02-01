# Epic 001: Costa Rica Electronic Invoicing (Tribu-CR v4.4)

**Status**: In Progress
**Priority**: Critical
**Started**: 2025-12-28
**Target Phase**: Foundation
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

2. **Digital Signature** (Phase 2) 🚧 IN PROGRESS
   - X.509 certificate handling
   - XMLDSig signing
   - Certificate validation

3. **Hacienda API Integration** (Phase 3)
   - Submit signed invoices
   - Check acceptance status
   - Handle responses and errors

4. **User Interface** (Phase 4)
   - E-invoice management views
   - Invoice form integration
   - Configuration screens

5. **PDF & Email** (Phase 5)
   - QR code generation
   - PDF invoice reports
   - Automated customer emails

6. **GMS Integration** (Phase 6)
   - Membership billing
   - Recurring subscriptions
   - POS integration

7. **Testing & Certification** (Phase 7)
   - Unit and integration tests
   - Hacienda sandbox validation
   - Production certification

8. **Production Deployment** (Phase 8)
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

### Phase 2 🚧 IN PROGRESS
- [ ] Load and validate X.509 certificates
- [ ] Sign XML with XMLDSig
- [ ] Verify signed XML structure
- [ ] Pass signature validation tests

### Phase 3 ⏳ PENDING
- [ ] Submit signed invoices to Hacienda sandbox
- [ ] Receive acceptance confirmations
- [ ] Handle rejection errors gracefully
- [ ] Store Hacienda responses

### Phase 4 ⏳ PENDING
- [ ] User can manage e-invoices from UI
- [ ] Configuration screen for Hacienda setup
- [ ] Smart buttons on invoices
- [ ] Status indicators and alerts

### Phase 5 ⏳ PENDING
- [ ] Generate QR codes per Hacienda spec
- [ ] PDF invoice with e-invoice data
- [ ] Email template with XML attachment
- [ ] Automated customer delivery

### Phase 6-8 ⏳ PENDING
- [ ] Membership billing automation
- [ ] POS tiquete generation
- [ ] Comprehensive test coverage
- [ ] Production certification
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

### In Progress (Phase 2)

🚧 **Digital Signature** - CURRENT FOCUS
- Certificate manager implementation
- XML signing with XMLDSig
- Hacienda sandbox testing

**Blockers**: None
**Resources Available**:
- ✅ Sandbox credentials
- ✅ Test certificate (certificado.p12)
- ✅ Certificate PIN ([REDACTED - use environment variable EINVOICE_CERT_PIN])

### Pending (Phases 3-8)

⏳ API Integration → UI → PDF/Email → GMS Features → Testing → Deployment

## Timeline & Effort

**Total Estimate**: 8 phases
**Completed**: Phase 1 (34 hours, $1,700)
**Current**: Phase 2 (estimated 40 hours)
**Budget**: $13,000 - $15,000 total
**Burn Rate**: 13% spent

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
