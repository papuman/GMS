# Costa Rica Electronic Invoicing Module (Tribu-CR v4.4)

Custom Odoo 19 module for GMS (Gym Management System) to generate and submit electronic invoices compliant with Costa Rica's Ministry of Finance (Hacienda) requirements.

## Features

### ✅ Implemented (Phase 1)

- **XML Generation**: Complete v4.4 compliant XML generation for all document types
  - Factura Electrónica (FE)
  - Tiquete Electrónico (TE)
  - Nota de Crédito (NC)
  - Nota de Débito (ND)

- **XSD Validation**: Automatic validation against Hacienda official schemas
  - Schema caching for performance
  - Detailed error reporting
  - Auto-download from Hacienda CDN

- **Clave Generation**: Automatic 50-digit electronic document key generation
  - Proper format validation
  - Check digit calculation
  - Unique sequential numbering

- **API Client**: Hacienda Tribu-CR API integration framework
  - Submit invoices
  - Check document status
  - Sandbox and production environments
  - Authentication handling

- **Odoo Integration**: Seamless integration with Odoo accounting
  - Automatic e-invoice creation on invoice post
  - Document state tracking
  - Partner and company data integration

### 🚧 Pending (Future Phases)

- **Digital Signature** (Phase 2): X.509 certificate signing
- **PDF Generation** (Phase 5): QR code generation and PDF reports
- **Email Delivery** (Phase 5): Automatic customer email delivery
- **UI Views** (Phase 3-4): Web interface for management
- **Advanced Testing** (Phase 7): Comprehensive test suite

## Installation

### Prerequisites

```bash
# Python dependencies
pip install lxml xmlschema cryptography pyOpenSSL requests qrcode
```

### Install Module

1. Copy the `l10n_cr_einvoice` folder to your Odoo addons directory:
   ```bash
   cp -r l10n_cr_einvoice /path/to/odoo/addons/
   ```

2. Update apps list in Odoo:
   - Go to Apps menu
   - Click "Update Apps List"

3. Install the module:
   - Search for "Costa Rica Electronic Invoicing"
   - Click Install

## Configuration

### Company Setup

Navigate to: **Settings → General Settings → Costa Rica E-Invoicing**

1. **Hacienda API Credentials**:
   - Environment: Sandbox (for testing) or Production
   - API Username: Your Hacienda API username
   - API Password: Your Hacienda API password

2. **Digital Certificate** (Phase 2):
   - Upload your X.509 certificate (PEM format)
   - Upload private key (PEM format)
   - Enter private key password if encrypted

3. **Location Code**:
   - Set your emisor location code (8 digits)
   - Format: Provincia-Canton-Distrito-Barrio
   - Example: `01010100` for San José

4. **Automation Settings**:
   - ☑ Auto-generate E-Invoice (recommended)
   - ☐ Auto-submit to Hacienda (optional)
   - ☑ Auto-send Email (recommended)

### Test Connection

Click the "Test Connection" button to verify your Hacienda API credentials.

## Usage

### Automatic Mode

When auto-generation is enabled, e-invoices are created automatically when you post a customer invoice.

1. Create a customer invoice
2. Post the invoice
3. Electronic invoice is automatically created
4. View e-invoice from the invoice form (smart button)

### Manual Mode

1. Create and post a customer invoice
2. Click "Create E-Invoice" button
3. The system generates the electronic invoice document
4. Review and submit to Hacienda

### Document Workflow

```
Draft → Generate XML → Sign XML → Submit to Hacienda → Accepted/Rejected → Email Customer
```

Each step can be executed manually or automatically based on configuration.

## Technical Architecture

### Models

- **l10n_cr.einvoice.document**: Main e-invoice document model
  - Stores XML content, signatures, and Hacienda responses
  - Tracks document lifecycle (draft → accepted)
  - Links to account.move (invoice)

- **l10n_cr.xml.generator**: XML generation engine
  - Generates v4.4 compliant XML for all document types
  - Handles complex tax calculations
  - Supports all Costa Rica specific fields

- **l10n_cr.xsd.validator**: XSD schema validator
  - Downloads and caches official Hacienda schemas
  - Validates XML before submission
  - Provides detailed error messages

- **l10n_cr.hacienda.api**: API client
  - Communicates with Hacienda Tribu-CR API
  - Handles authentication and errors
  - Supports both sandbox and production

### Database Schema

```sql
-- Electronic Invoice Documents
CREATE TABLE l10n_cr_einvoice_document (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),                    -- Document number
    move_id INTEGER REFERENCES account_move(id),
    clave VARCHAR(50) UNIQUE,            -- 50-digit Hacienda key
    document_type VARCHAR(2),            -- FE, TE, NC, ND
    xml_content TEXT,                    -- Generated XML
    signed_xml TEXT,                     -- Signed XML
    state VARCHAR(20),                   -- Document status
    hacienda_response TEXT,              -- API response
    hacienda_submission_date TIMESTAMP,
    hacienda_acceptance_date TIMESTAMP
);
```

### File Structure

```
l10n_cr_einvoice/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── einvoice_document.py      -- Main e-invoice model
│   ├── account_move.py            -- Invoice integration
│   ├── xml_generator.py           -- XML generation
│   ├── xsd_validator.py           -- Schema validation
│   ├── hacienda_api.py            -- API client
│   ├── res_company.py             -- Company settings
│   └── res_config_settings.py     -- Configuration
├── views/
│   ├── einvoice_document_views.xml     (Pending)
│   ├── account_move_views.xml          (Pending)
│   └── res_config_settings_views.xml   (Pending)
├── security/
│   └── ir.model.access.csv        -- Access rights
├── data/
│   ├── hacienda_sequences.xml     -- Document sequences
│   └── document_types.xml         -- Initial data
├── reports/
│   └── __init__.py                -- PDF reports (Phase 5)
├── tests/
│   └── (To be implemented)
└── static/
    └── description/
        └── icon.png               (Optional)
```

## Development Roadmap

### Phase 1: Core XML Generation ✅ COMPLETE
- ✅ Module structure and dependencies
- ✅ XML generation for v4.4 format
- ✅ XSD validation
- ✅ Clave generation
- ✅ Basic API client
- ✅ Model integration

### Phase 2: Digital Signature (Next)
- ⏳ X.509 certificate handling
- ⏳ XML signing implementation
- ⏳ Private key encryption/decryption
- ⏳ Signature validation

### Phase 3: Hacienda API Integration
- ⏳ Complete API implementation
- ⏳ Error handling and retries
- ⏳ Status checking automation
- ⏳ Response processing

### Phase 4: Odoo Integration
- ⏳ UI views and forms
- ⏳ Smart buttons on invoices
- ⏳ Wizards for manual operations
- ⏳ Settings interface

### Phase 5: PDF Generation & Email
- ⏳ QR code generation
- ⏳ PDF report templates
- ⏳ Email templates
- ⏳ Automatic delivery

### Phase 6: GMS-Specific Features
- ⏳ Membership subscription invoicing
- ⏳ Recurring billing integration
- ⏳ Custom product codes (Cabys)
- ⏳ Gym-specific workflows

### Phase 7: Testing & Certification
- ⏳ Unit tests
- ⏳ Integration tests
- ⏳ Hacienda certification testing
- ⏳ Performance optimization

### Phase 8: Production Deployment
- ⏳ Production credentials setup
- ⏳ Migration plan
- ⏳ Training documentation
- ⏳ Go-live support

## API Reference

### Generate Electronic Invoice

```python
# Automatic (when invoice is posted)
invoice.action_post()  # E-invoice created automatically

# Manual
einvoice = invoice.action_create_einvoice()
```

### Complete Workflow

```python
# Generate → Sign → Submit → Email
invoice.action_generate_and_send_einvoice()
```

### Individual Steps

```python
# 1. Generate XML
einvoice.action_generate_xml()

# 2. Sign XML (Phase 2)
einvoice.action_sign_xml()

# 3. Submit to Hacienda
einvoice.action_submit_to_hacienda()

# 4. Check status
einvoice.action_check_status()
```

## Troubleshooting

### Common Issues

**1. XSD Schema Download Fails**
```
Error: Failed to download XSD schema
Solution: Check internet connection, verify Hacienda CDN is accessible
```

**2. XML Validation Errors**
```
Error: XML validation failed: Line X: Invalid element
Solution: Review product data, ensure all required fields are filled
```

**3. API Authentication Fails**
```
Error: Hacienda API error: 401 Unauthorized
Solution: Verify API credentials in company settings
```

**4. Missing Cédula Jurídica**
```
Error: Company VAT is required
Solution: Set company VAT number in Settings → Companies
```

### Debug Mode

Enable debug logging in Odoo configuration:

```ini
[options]
log_level = debug
log_handler = odoo.addons.l10n_cr_einvoice:DEBUG
```

## Support

### Documentation
- **Hacienda Official Docs**: https://www.hacienda.go.cr/contenido/14185-factura-electronica
- **v4.4 Specifications**: https://www.hacienda.go.cr/docs/Comprobantes_Electronicos_V4_4.pdf
- **API Documentation**: Contact Hacienda for API access

### Development Team
- **Custom Development**: GMS Development Team
- **Module Version**: 19.0.1.0.0
- **Odoo Version**: 19.0

## License

LGPL-3

## Changelog

### Version 19.0.1.0.0 (2025-12-28)
- ✅ Initial release
- ✅ Phase 1 complete: Core XML generation and validation
- ✅ Support for all document types (FE, TE, NC, ND)
- ✅ XSD validation framework
- ✅ Hacienda API client foundation
- ⏳ Digital signature pending (Phase 2)
