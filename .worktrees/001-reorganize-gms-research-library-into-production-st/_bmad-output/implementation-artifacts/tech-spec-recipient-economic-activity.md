# Tech-Spec: Recipient Economic Activity Field (CIIU 4 Codes)

**Created:** 2025-12-28
**Status:** Ready for Development
**Priority:** HIGH - Compliance Risk (Mandatory Oct 6, 2025)
**Phase:** 1C - Critical Compliance

---

## Overview

### Problem Statement

Costa Rica's v4.4 electronic invoicing specification requires the **recipient's economic activity** (CIIU 4 code) to be included in all invoices. This field becomes **MANDATORY on October 6, 2025** per Resolution MH-DGT-RES-0027-2024.

**Compliance Issue**:
- v4.3 specification: Economic activity was optional
- v4.4 specification: Economic activity REQUIRED (mandatory from Oct 6, 2025)
- Current implementation: Field does NOT exist → **CRITICAL FAILURE after deadline**

**Business Impact**:
- After Oct 6, 2025: ALL invoices without recipient economic activity will be REJECTED
- Cannot invoice B2B customers legally
- System will be completely non-functional for business customers
- Risk of complete business shutdown if not implemented

**Deadline**: October 6, 2025 (9 months from now)

### Solution

Implement recipient economic activity tracking using CIIU 4 (Clasificación Industrial Internacional Uniforme) codes:
1. Add economic activity field to partner (res.partner) model
2. Implement CIIU 4 code catalog (600+ codes)
3. Add validation to ensure field is populated
4. Include economic activity in XML v4.4 generation
5. Update partner form view with economic activity selection
6. Support bulk assignment for existing customers
7. Provide smart defaults based on industry

### Scope

**IN SCOPE**:
- ✅ Partner model extension (economic activity field)
- ✅ CIIU 4 code catalog (core industries - ~100 codes initially)
- ✅ Economic activity selection in partner form
- ✅ XML generation updates for ReceptorActividadEconomica
- ✅ Validation rules (warning before deadline, error after)
- ✅ Bulk assignment wizard for existing partners
- ✅ Smart defaults (suggest code based on industry/tags)
- ✅ Grace period handling (soft warnings until Oct 6, 2025)

**OUT OF SCOPE** (Future Enhancements):
- ❌ Complete CIIU 4 catalog (all 600+ codes) - start with top 100
- ❌ Automatic code suggestion via AI/ML
- ❌ Economic activity change history tracking
- ❌ Industry-specific reporting by CIIU code
- ❌ Integration with government CIIU registry API

---

## Context for Development

### Codebase Patterns

**Partner Model Extension Pattern** (from Odoo standard):
```python
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Field definition pattern
    custom_field = fields.Many2one(
        'related.model',
        string='Display Name',
        help='Help text',
    )

    # Compute method pattern
    @api.depends('some_field')
    def _compute_field(self):
        for record in self:
            record.computed_field = self._calculate_value()
```

**XML Generator Receptor Pattern** (from `xml_generator.py:257-275`):
```python
def _add_receptor(self, root, partner):
    """Add Receptor (receiver) section."""
    receptor = etree.SubElement(root, 'Receptor')

    # Partner name
    etree.SubElement(receptor, 'Nombre').text = partner.name or ''

    # Identification
    if partner.vat:
        identificacion = etree.SubElement(receptor, 'Identificacion')
        tipo_id = self._get_partner_id_type(partner.vat)
        etree.SubElement(identificacion, 'Tipo').text = tipo_id
        numero_id = partner.vat.replace('-', '').replace(' ', '')
        etree.SubElement(identificacion, 'Numero').text = numero_id

    # Email
    if partner.email:
        etree.SubElement(receptor, 'CorreoElectronico').text = partner.email

    # MISSING: ActividadEconomica (economic activity)
```

**Master Data Catalog Pattern** (from `data/document_types.xml`):
```xml
<odoo>
    <data noupdate="1">
        <record id="ciiu_9311" model="l10n_cr.ciiu.code">
            <field name="code">9311</field>
            <field name="name">Gestión de instalaciones deportivas</field>
            <field name="section">S</field>
            <field name="active" eval="True"/>
        </record>
    </data>
</odoo>
```

### Files to Reference

**Models** (Must Read):
- Odoo Core: `base/models/res_partner.py` - Partner model structure
- Extension: `l10n_cr_einvoice/models/xml_generator.py:257-275` - Receptor XML generation

**Models** (Must Create):
- `l10n_cr_einvoice/models/res_partner.py` - NEW FILE (inherit res.partner)
- `l10n_cr_einvoice/models/ciiu_code.py` - NEW FILE (CIIU 4 catalog)

**Views** (Must Modify):
- `l10n_cr_einvoice/views/res_partner_views.xml` - NEW FILE (partner form extension)

**Data Files** (Must Create):
- `l10n_cr_einvoice/data/ciiu_codes.xml` - NEW FILE (catalog)

**Wizards** (Must Create):
- `l10n_cr_einvoice/wizards/ciiu_bulk_assign.py` - NEW FILE (bulk assignment)
- `l10n_cr_einvoice/views/ciiu_bulk_assign_views.xml` - NEW FILE

**Manifest** (Must Update):
- `l10n_cr_einvoice/__manifest__.py:55-74` - Add new files to data list

### Technical Decisions

**Decision 1**: CIIU Catalog Scope = Top 100 Codes Initially
- **Why**: Full catalog (600+ codes) overwhelming, most businesses use ~20 common codes
- **Implementation**: Curated list of top 100 by industry sector
- **Alternative Rejected**: Full 600+ catalog (too complex, poor UX)

**Decision 2**: Economic Activity on Partner, Not Invoice
- **Why**: Customer's economic activity doesn't change per invoice
- **Implementation**: Field on res.partner, referenced in invoice XML
- **Alternative Rejected**: Field per invoice (data duplication, maintenance nightmare)

**Decision 3**: Grace Period with Soft Warnings (Until Oct 6, 2025)
- **Why**: Give users time to populate data without blocking operations
- **Implementation**: Warning if missing, error only after deadline
- **Alternative Rejected**: Hard error immediately (too disruptive)

**Decision 4**: Smart Default Based on Partner Tags/Category
- **Why**: Reduce manual data entry, improve user experience
- **Implementation**: Mapping table: partner category → suggested CIIU code
- **Alternative Rejected**: No defaults (slower adoption, poor UX)

**Decision 5**: Bulk Assignment Wizard for Migration
- **Why**: Existing customers need economic activity codes en masse
- **Implementation**: Wizard to assign code to multiple partners at once
- **Alternative Rejected**: Manual one-by-one (too slow for 100+ customers)

---

## Implementation Plan

### Tasks

#### Phase 1C.1: CIIU Code Catalog (8 hours)
- [ ] **Task 1.1**: Create `l10n_cr.ciiu.code` model
  - File: `models/ciiu_code.py` (NEW)
  - Fields: `code` (Char, 4), `name` (Char), `description` (Text), `section` (Char, 1), `active` (Boolean)
  - Methods: `name_get()` to display "9311 - Gestión de instalaciones deportivas"
  - Add to `models/__init__.py`

- [ ] **Task 1.2**: Research top 100 CIIU 4 codes for Costa Rica
  - Research: Costa Rica industry distribution
  - Prioritize: Retail, services, professional services, manufacturing, food service
  - Create: Spreadsheet with code, name, section, common use cases

- [ ] **Task 1.3**: Create CIIU codes data file
  - File: `data/ciiu_codes.xml` (NEW)
  - Records: Top 100 CIIU 4 codes
  - Sections: A-U (Agriculture through Public Administration)
  - Add to `__manifest__.py` data list

- [ ] **Task 1.4**: Create security rules
  - Add to `security/ir.model.access.csv`
  - Permissions: all_users (read), accountant (write)

#### Phase 1C.2: Partner Model Extension (10 hours)
- [ ] **Task 2.1**: Extend `res.partner` model
  - File: `models/res_partner.py` (NEW - inherit res.partner)
  - Field: `l10n_cr_economic_activity_id` (Many2one to l10n_cr.ciiu.code)
  - Field: `l10n_cr_activity_code` (Char, related, store=True) - for quick XML access
  - Index: `l10n_cr_economic_activity_id` for performance

- [ ] **Task 2.2**: Add smart default computation
  - Method: `_compute_suggested_ciiu_code()`
  - Logic: Based on partner category_id or industry_id
  - Mapping examples:
    - Gym/Sports → 9311 (Gestión de instalaciones deportivas)
    - Restaurant → 5610 (Actividades de restaurantes)
    - Retail → 4711 (Comercio al por menor)
    - Software → 6201 (Actividades de programación informática)

- [ ] **Task 2.3**: Add validation method
  - Method: `_validate_economic_activity_for_cr_invoices()`
  - Logic: If partner is Costa Rica B2B customer → warn if missing
  - Hook: On partner save (warning only, not blocking)

#### Phase 1C.3: XML Generator Updates (8 hours)
- [ ] **Task 3.1**: Update `_add_receptor()` method
  - File: `models/xml_generator.py:257-275`
  - Add: Economic activity code to Receptor section
  - XML structure per v4.4 spec:
    ```xml
    <Receptor>
      <Nombre>Company Name</Nombre>
      <ActividadEconomica>9311</ActividadEconomica>
      <!-- ... rest of fields ... -->
    </Receptor>
    ```

- [ ] **Task 3.2**: Add conditional validation for economic activity
  - Check: If invoice date >= October 6, 2025 and no economic activity → Error
  - Check: If invoice date < October 6, 2025 and no economic activity → Warning (log only)
  - Error message: "Recipient economic activity is required for invoices after October 6, 2025"

- [ ] **Task 3.3**: Update all document type generators
  - Files: `_generate_factura_electronica()`, `_generate_tiquete_electronico()`, `_generate_nota_credito()`, `_generate_nota_debito()`
  - Ensure all include economic activity in Receptor section

#### Phase 1C.4: UI Updates (12 hours)
- [ ] **Task 4.1**: Create partner form view extension
  - File: `views/res_partner_views.xml` (NEW)
  - Inherit: base partner form view
  - Add: Economic activity field in "Costa Rica" page/group
  - Position: After VAT field
  - Add attrs: visible only for Costa Rica partners

- [ ] **Task 4.2**: Add economic activity to partner list view
  - Add column: Economic activity (optional field)
  - Filter: Partners missing economic activity
  - Group by: Economic activity section

- [ ] **Task 4.3**: Create smart suggestions UI
  - Add: "Suggested CIIU Code" field (compute, not stored)
  - Add: Button "Use Suggested Code" to quickly apply
  - Add: Helper text explaining CIIU code selection

- [ ] **Task 4.4**: Add validation indicators
  - Badge: Show warning icon if missing economic activity for CR partners
  - Tooltip: "Economic activity required for e-invoicing after Oct 6, 2025"

#### Phase 1C.5: Bulk Assignment Wizard (16 hours)
- [ ] **Task 5.1**: Create bulk assignment wizard model
  - File: `wizards/ciiu_bulk_assign.py` (NEW)
  - Model: `l10n_cr.ciiu.bulk.assign` (TransientModel)
  - Fields: `partner_ids` (Many2many), `ciiu_code_id` (Many2one), `filter_by_category` (Many2one)
  - Method: `action_assign()` - assign code to all selected partners

- [ ] **Task 5.2**: Create wizard view
  - File: `wizards/ciiu_bulk_assign_views.xml` (NEW)
  - Form view with:
    - Partner domain filter (by category, tag, country)
    - CIIU code selection
    - Preview count of affected partners
    - Confirm button

- [ ] **Task 5.3**: Add wizard menu action
  - Location: Settings → Configuration → Costa Rica E-Invoicing
  - Action: Open bulk assignment wizard
  - Access: Accountant role only

- [ ] **Task 5.4**: Create pre-populated assignment templates
  - Template 1: Gym/Sports partners → 9311
  - Template 2: Restaurant partners → 5610
  - Template 3: Retail partners → 4711
  - Template 4: Professional services → 6201

#### Phase 1C.6: Migration & Data Population (12 hours)
- [ ] **Task 6.1**: Create migration script
  - File: `migrations/19.0.1.0.0/post-migration.py`
  - Logic:
    1. Find Costa Rica partners without economic activity
    2. Try to auto-assign based on category mapping
    3. Log partners that need manual assignment
  - Report: CSV of partners needing manual assignment

- [ ] **Task 6.2**: Create CIIU code mapping table
  - Map: Odoo partner categories → CIIU codes
  - Map: Industry IDs → CIIU codes
  - Map: Common company name patterns → CIIU codes (e.g., "Gym" → 9311)

- [ ] **Task 6.3**: Test migration on staging
  - Backup test database
  - Run migration script
  - Review auto-assignments for accuracy
  - Test bulk wizard for manual assignments

#### Phase 1C.7: Validation & Deadline Enforcement (10 hours)
- [ ] **Task 7.1**: Create deadline configuration
  - Add system parameter: `l10n_cr_einvoice.ciiu_mandatory_date`
  - Default: October 6, 2025
  - Allow override for testing

- [ ] **Task 7.2**: Implement grace period logic
  - Before deadline: Warning only (log message)
  - After deadline: Hard error (block invoice generation)
  - Method: `_check_ciiu_deadline()`

- [ ] **Task 7.3**: Add invoice validation
  - File: `models/account_move.py`
  - Hook: Before XML generation
  - Check: Partner has economic activity OR date < deadline
  - Error: "Recipient economic activity is required after October 6, 2025"

- [ ] **Task 7.4**: Create dashboard widget
  - Widget: Show count of partners missing economic activity
  - Location: Hacienda dashboard
  - Action: Click to see list of partners
  - Alert: Turn red when deadline is within 30 days

#### Phase 1C.8: Testing (18 hours)
- [ ] **Task 8.1**: Unit tests for CIIU code model
  - File: `tests/test_ciiu_code.py` (NEW)
  - Test catalog creation
  - Test code uniqueness
  - Test name_get() format
  - Test section filtering

- [ ] **Task 8.2**: Unit tests for partner extension
  - File: `tests/test_res_partner_ciiu.py` (NEW)
  - Test smart default computation
  - Test economic activity assignment
  - Test validation warnings

- [ ] **Task 8.3**: Unit tests for bulk assignment wizard
  - File: `tests/test_ciiu_bulk_assign.py` (NEW)
  - Test partner filtering
  - Test bulk assignment to 100 partners
  - Test template application

- [ ] **Task 8.4**: Integration tests for XML generation
  - File: `tests/test_xml_generator_ciiu.py` (NEW)
  - Test XML contains `ActividadEconomica` tag
  - Test all CIIU codes generate valid XML
  - Test missing code behavior (warning vs error by date)

- [ ] **Task 8.5**: E2E test: Invoice with economic activity
  - Create Costa Rica partner with CIIU code 9311
  - Create invoice
  - Generate XML
  - Validate `<ActividadEconomica>9311</ActividadEconomica>` exists
  - Submit to Hacienda sandbox
  - Verify acceptance

- [ ] **Task 8.6**: Deadline enforcement tests
  - Test 1: Invoice before Oct 6, 2025, no code → Warning only
  - Test 2: Invoice after Oct 6, 2025, no code → Error (blocked)
  - Test 3: Invoice after Oct 6, 2025, with code → Success

### Acceptance Criteria

#### AC1: CIIU Code Catalog Exists
**Given** I am a system administrator
**When** I navigate to Settings → Technical → Database Structure → Models
**Then** I should see `l10n_cr.ciiu.code` model
**And** the model should contain at least 100 CIIU 4 code records

#### AC2: Partner Form Has Economic Activity Field
**Given** I am viewing a Costa Rica partner's form
**When** I scroll to the "Costa Rica" section
**Then** I should see an "Economic Activity" dropdown field
**And** the dropdown should contain CIIU codes in format "9311 - Gestión de instalaciones deportivas"

#### AC3: Smart Default Suggestions Work
**Given** I create a new partner with category = "Gym/Sports"
**When** I open the partner form
**Then** I should see a suggested CIIU code = "9311 - Gestión de instalaciones deportivas"
**And** I can click "Use Suggested Code" to apply it

#### AC4: XML Contains Economic Activity Code
**Given** I have a partner with economic activity = "9311"
**When** I create and confirm an invoice for this partner
**And** the e-invoice XML is generated
**Then** the XML should contain:
```xml
<Receptor>
  <ActividadEconomica>9311</ActividadEconomica>
</Receptor>
```

#### AC5: Grace Period Warning (Before Deadline)
**Given** today's date is before October 6, 2025
**When** I generate an invoice for a partner without economic activity
**Then** I should see a warning message in the logs
**But** the invoice should still be generated successfully

#### AC6: Hard Error After Deadline
**Given** today's date is October 6, 2025 or later
**When** I try to generate an invoice for a partner without economic activity
**Then** I should receive a hard error: "Recipient economic activity is required"
**And** the XML generation should fail

#### AC7: Bulk Assignment Wizard Works
**Given** I have 50 partners without economic activity
**When** I open the bulk assignment wizard
**And** I filter for category = "Gyms"
**And** I select CIIU code = "9311"
**And** I click "Assign"
**Then** all 50 partners should have economic activity = "9311"
**And** I should see a success message with count

#### AC8: Partner List Filter for Missing Activity
**Given** I am on the partners list view
**When** I apply filter "Missing Economic Activity"
**Then** I should see only Costa Rica partners without an economic activity code
**And** the count should be displayed

#### AC9: Dashboard Shows Missing Activity Count
**Given** I am viewing the Hacienda dashboard
**When** I look at the "Data Quality" widget
**Then** I should see "Partners Missing Economic Activity: XX"
**And** clicking it should open the filtered partner list

#### AC10: Hacienda Accepts Invoice with Economic Activity
**Given** I have generated and signed an e-invoice with economic activity code
**When** I submit the invoice to Hacienda sandbox
**Then** Hacienda should accept the invoice
**And** the invoice state should change to "Accepted"
**And** no validation errors related to economic activity should occur

---

## Additional Context

### Dependencies

**Python Libraries** (already in external_dependencies):
- ✅ `lxml` - XML generation

**Odoo Modules**:
- ✅ `base` - Partner model
- ✅ `account` - Invoice model
- ✅ `l10n_cr` - Costa Rica localization

**External Resources**:
- 📚 CIIU 4 Official Classification: https://unstats.un.org/unsd/classifications/Econ/ISIC
- 📚 Costa Rica adaptation of CIIU 4

### Testing Strategy

**Unit Tests** (pytest + Odoo test framework):
```python
# tests/test_res_partner_ciiu.py
from odoo.tests import TransactionCase
from datetime import date

class TestPartnerCIIU(TransactionCase):
    def test_smart_default_gym_category(self):
        # Create partner with gym category
        gym_category = self.env.ref('base.res_partner_category_gym')
        partner = self.env['res.partner'].create({
            'name': 'Test Gym',
            'category_id': [(4, gym_category.id)],
            'country_id': self.env.ref('base.cr').id,
        })

        # Should suggest CIIU 9311
        suggested = partner._compute_suggested_ciiu_code()
        self.assertEqual(suggested.code, '9311')

    def test_deadline_enforcement(self):
        # Create partner without economic activity
        partner = self.env['res.partner'].create({
            'name': 'Test Company',
            'country_id': self.env.ref('base.cr').id,
        })

        # Before deadline: should warn but allow
        with self.mock_date('2025-10-05'):
            invoice = self.create_test_invoice(partner)
            # Should generate with warning
            self.assertTrue(invoice.l10n_cr_einvoice_id.xml_content)

        # After deadline: should block
        with self.mock_date('2025-10-06'):
            invoice2 = self.create_test_invoice(partner)
            with self.assertRaises(ValidationError):
                invoice2.l10n_cr_einvoice_id.action_generate_xml()
```

**XSD Schema Validation**:
- Validate `<ActividadEconomica>` tag format (4-digit numeric code)
- Test against official Hacienda v4.4 XSD schemas

**Sandbox Testing**:
- Test sample invoices with various CIIU codes
- Verify Hacienda accepts all valid codes
- Test edge cases (missing code, invalid code format)

### Notes

**Top 20 CIIU 4 Codes for Costa Rica** (Priority for initial catalog):
```
9311 = Gestión de instalaciones deportivas (Sports facilities)
5610 = Actividades de restaurantes y de servicio móvil de comidas (Restaurants)
4711 = Comercio al por menor en establecimientos no especializados (General retail)
6201 = Actividades de programación informática (Software development)
8511 = Educación preescolar y primaria (Primary education)
8512 = Educación secundaria (Secondary education)
8621 = Actividades de la práctica médica (Medical practice)
8690 = Otras actividades de atención de la salud humana (Other health services)
4520 = Mantenimiento y reparación de vehículos automotores (Auto repair)
9602 = Peluquería y otros tratamientos de belleza (Beauty salons)
9609 = Otras actividades de servicios personales n.c.p. (Other personal services)
7010 = Actividades de oficinas principales (Head office activities)
7020 = Actividades de consultoría de gestión (Management consulting)
4646 = Comercio al por mayor de productos farmacéuticos (Pharma wholesale)
5630 = Expendio de bebidas (Beverage service)
8010 = Actividades de seguridad privada (Private security)
4920 = Transporte de pasajeros (Passenger transport)
8220 = Actividades de centros de llamadas (Call centers)
6209 = Otras actividades de tecnología de la información (Other IT services)
6810 = Actividades inmobiliarias (Real estate)
```

**CIIU 4 Section Codes**:
```
A = Agriculture, forestry and fishing
B = Mining and quarrying
C = Manufacturing
D = Electricity, gas, steam and air conditioning supply
E = Water supply; sewerage, waste management
F = Construction
G = Wholesale and retail trade
H = Transportation and storage
I = Accommodation and food service
J = Information and communication
K = Financial and insurance activities
L = Real estate activities
M = Professional, scientific and technical
N = Administrative and support service
O = Public administration and defence
P = Education
Q = Human health and social work
R = Arts, entertainment and recreation
S = Other service activities
T = Households as employers
U = Extraterritorial organizations
```

**XML v4.4 Specification Reference**:
- Section 4.1.6.8: ActividadEconomica (Economic Activity)
- Format: 4-digit numeric code (CIIU 4)
- Official XSD: Line 280-285 in v4.4 schema

**Partner Category Mapping Examples**:
```python
CIIU_MAPPING = {
    'Gym': '9311',
    'Sports': '9311',
    'Restaurant': '5610',
    'Cafe': '5630',
    'Retail': '4711',
    'Software': '6201',
    'IT Services': '6209',
    'Consulting': '7020',
    'Education': '8511',
    'Medical': '8621',
    'Beauty Salon': '9602',
    'Auto Repair': '4520',
    'Real Estate': '6810',
}
```

**Dashboard Widget Spec**:
```xml
<!-- Hacienda Dashboard Widget -->
<div class="alert alert-warning" t-if="partners_missing_ciiu > 0">
  <strong>Data Quality Alert</strong>
  <p>
    <span t-esc="partners_missing_ciiu"/> partners missing economic activity code.
    <t t-if="days_until_deadline < 30">
      <strong class="text-danger">Deadline in <t t-esc="days_until_deadline"/> days!</strong>
    </t>
  </p>
  <button class="btn btn-sm btn-warning" name="action_view_partners_missing_ciiu">
    View Partners
  </button>
</div>
```

**Migration Strategy**:
1. **Auto-assign** where confident (based on category/tags)
2. **Flag for review** where uncertain
3. **Provide bulk wizard** for manual batch assignment
4. **Generate report** for remaining partners
5. **Monitor progress** via dashboard widget

**Future Enhancements** (Out of Scope):
- AI-powered CIIU code suggestion based on company description
- Integration with government CIIU registry API for validation
- Historical tracking of economic activity changes
- Industry benchmarking by CIIU code
- Automatic code updates from government registry

---

**Estimated Effort**: 94 hours (12 days)
**Developer Skill Level**: Intermediate Odoo developer
**Testing Time**: 18 hours included in estimate
**Documentation Time**: 8 hours (user guide on CIIU codes)

**Total Phase 1C Effort**: 94 hours

---

**Document Version**: 1.0
**Last Updated**: 2025-12-28
**Author**: BMAD Workflow System
**Reviewed By**: Pending
**Approved By**: Pending
