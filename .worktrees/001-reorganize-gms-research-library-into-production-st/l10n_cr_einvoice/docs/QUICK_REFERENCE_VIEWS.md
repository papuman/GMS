# Quick Reference: Views & Actions

Fast lookup guide for developers working with Costa Rica E-Invoice views.

---

## View IDs

### E-Invoice Document Views

```python
# Tree View
ref("l10n_cr_einvoice.view_einvoice_document_tree")

# Form View
ref("l10n_cr_einvoice.view_einvoice_document_form")

# Kanban View
ref("l10n_cr_einvoice.view_einvoice_document_kanban")

# Search View
ref("l10n_cr_einvoice.view_einvoice_document_search")

# Activity View
ref("l10n_cr_einvoice.view_einvoice_document_activity")

# Graph View
ref("l10n_cr_einvoice.view_einvoice_graph")

# Pivot View
ref("l10n_cr_einvoice.view_einvoice_pivot")
```

### Invoice Integration Views

```python
# Form Inheritance
ref("l10n_cr_einvoice.view_move_form_einvoice")

# Tree Inheritance
ref("l10n_cr_einvoice.view_move_tree_einvoice")

# Search Inheritance
ref("l10n_cr_einvoice.view_account_invoice_filter_einvoice")
```

### Configuration Views

```python
# Settings Form
ref("l10n_cr_einvoice.res_config_settings_view_form_einvoice")

# Company Form
ref("l10n_cr_einvoice.view_company_form_einvoice")
```

---

## Action IDs

### Main Actions

```python
# E-Invoice List
ref("l10n_cr_einvoice.action_einvoice_document")

# Pending E-Invoices
ref("l10n_cr_einvoice.action_invoices_requiring_einvoice")

# E-Invoice Errors
ref("l10n_cr_einvoice.action_invoices_einvoice_errors")

# Dashboard
ref("l10n_cr_einvoice.action_einvoice_dashboard")

# View Invoice from E-Invoice
ref("l10n_cr_einvoice.action_view_invoice_from_einvoice")
```

### Batch Actions

```python
# Batch Generate
ref("l10n_cr_einvoice.action_batch_generate_einvoice")

# Batch Submit
ref("l10n_cr_einvoice.action_batch_submit_einvoice")

# Batch Check Status
ref("l10n_cr_einvoice.action_batch_check_status")
```

---

## Menu IDs

```python
# Main Menu
ref("l10n_cr_einvoice.menu_hacienda_root")

# Sub-Menus
ref("l10n_cr_einvoice.menu_hacienda_einvoices")
ref("l10n_cr_einvoice.menu_hacienda_pending_invoices")
ref("l10n_cr_einvoice.menu_hacienda_errors")
ref("l10n_cr_einvoice.menu_hacienda_dashboard")
ref("l10n_cr_einvoice.menu_hacienda_reports")
ref("l10n_cr_einvoice.menu_hacienda_configuration")
```

---

## Common XPaths

### Invoice Form

```xml
<!-- Smart Buttons -->
<xpath expr="//div[@name='button_box']" position="inside">

<!-- Header Actions -->
<xpath expr="//header" position="inside">

<!-- After Header Group -->
<xpath expr="//group[@name='header_group']" position="after">
```

### Invoice List

```xml
<!-- After Payment State Column -->
<xpath expr="//field[@name='payment_state']" position="after">
```

### Invoice Search

```xml
<!-- After Draft Filter -->
<xpath expr="//filter[@name='draft']" position="after">

<!-- After Invoice Date Group -->
<xpath expr="//filter[@name='invoice_date']" position="after">
```

### Settings

```xml
<!-- After Localization Settings -->
<xpath expr="//div[@id='localization_settings']" position="after">
```

---

## Model Methods

### E-Invoice Document

```python
# Action Methods
einvoice.action_generate_xml()
einvoice.action_sign_xml()
einvoice.action_submit_to_hacienda()
einvoice.action_check_status()
einvoice.action_download_xml()
einvoice.action_view_hacienda_response()
einvoice.action_resend_email()

# Internal Methods
einvoice._generate_clave()
einvoice._build_xml_content(clave)
einvoice._validate_xml(xml_content)
einvoice._sign_xml_content(xml_content, cert, key)
einvoice._create_xml_attachment(xml_content)
einvoice._process_hacienda_response(response)
```

### Account Move

```python
# E-Invoice Methods
invoice.action_create_einvoice()
invoice.action_generate_and_send_einvoice()
invoice._create_einvoice_document()
invoice._get_einvoice_document_type()
invoice._send_einvoice_email()
```

### Settings

```python
# Configuration Methods
settings.action_test_hacienda_connection()
```

---

## Field Names

### E-Invoice Document

```python
# Basic
'name'                      # Document Number
'move_id'                   # Invoice
'company_id'                # Company
'partner_id'                # Customer
'document_type'             # FE/TE/NC/ND
'clave'                     # 50-digit key

# XML
'xml_content'               # Generated XML
'signed_xml'                # Signed XML
'xml_attachment_id'         # XML File

# Status
'state'                     # Workflow state
'hacienda_response'         # API response
'hacienda_message'          # Short message
'hacienda_submission_date'  # When submitted
'hacienda_acceptance_date'  # When accepted

# Error
'error_message'             # Error details
'retry_count'               # Number of retries

# Email
'email_sent'                # Boolean
'email_sent_date'           # Timestamp

# Related
'amount_total'              # Total amount
'currency_id'               # Currency
'invoice_date'              # Invoice date
```

### Account Move

```python
# E-Invoice Fields
'l10n_cr_einvoice_id'       # Link to e-invoice
'l10n_cr_einvoice_state'    # E-invoice state
'l10n_cr_clave'             # Hacienda key
'l10n_cr_requires_einvoice' # Boolean
```

### Company

```python
# API
'l10n_cr_hacienda_env'      # sandbox/production
'l10n_cr_hacienda_username' # API username
'l10n_cr_hacienda_password' # API password

# Certificate
'l10n_cr_certificate'       # Certificate binary
'l10n_cr_certificate_filename'
'l10n_cr_private_key'       # Key binary
'l10n_cr_private_key_filename'
'l10n_cr_key_password'      # Key password

# Config
'l10n_cr_emisor_location'   # 8-digit code

# Automation
'l10n_cr_auto_generate_einvoice'
'l10n_cr_auto_submit_einvoice'
'l10n_cr_auto_send_email'
'l10n_cr_einvoice_email_template_id'
```

---

## Domain Filters

### Common Domains

```python
# By State
[('state', '=', 'draft')]
[('state', '=', 'accepted')]
[('state', 'in', ['rejected', 'error'])]

# By Document Type
[('document_type', '=', 'FE')]
[('document_type', 'in', ['FE', 'TE'])]

# By Date
[('create_date', '>=', start_date)]
[('invoice_date', '=', today)]

# Requires E-Invoice
[('l10n_cr_requires_einvoice', '=', True)]

# Has E-Invoice
[('l10n_cr_einvoice_id', '!=', False)]

# Email Status
[('email_sent', '=', True)]
[('email_sent', '=', False), ('state', '=', 'accepted')]
```

---

## Context Keys

```python
# Default Values
{'default_move_id': invoice_id}
{'default_document_type': 'FE'}

# Filters
{'search_default_filter_draft': 1}
{'search_default_filter_accepted': 1}
{'search_default_filter_this_month': 1}
{'search_default_einvoice_pending': 1}

# Group By
{'group_by': 'state'}
{'group_by': 'document_type'}
{'group_by': 'partner_id'}
```

---

## Widget Reference

```xml
<!-- Status Badge -->
<field name="state" widget="badge"/>

<!-- Monetary -->
<field name="amount_total" widget="monetary"
       options="{'currency_field': 'currency_id'}"/>

<!-- Boolean Toggle -->
<field name="email_sent" widget="boolean_toggle"/>

<!-- Copy to Clipboard -->
<field name="clave" widget="CopyClipboardChar"/>

<!-- Code Editor -->
<field name="xml_content" widget="ace"
       options="{'mode': 'xml'}"/>

<!-- Statistics -->
<field name="count" widget="statinfo"/>

<!-- Radio Horizontal -->
<field name="env" widget="radio"
       options="{'horizontal': true}"/>
```

---

## Decoration Attributes

```xml
<!-- Tree View Row Colors -->
decoration-muted="state == 'draft'"
decoration-info="state == 'generated'"
decoration-primary="state == 'signed'"
decoration-warning="state == 'submitted'"
decoration-success="state == 'accepted'"
decoration-danger="state in ('rejected', 'error')"

<!-- Badge Colors -->
decoration-info="document_type == 'FE'"
decoration-success="document_type == 'TE'"
decoration-warning="document_type == 'NC'"
decoration-danger="document_type == 'ND'"
```

---

## Security Groups

```xml
<!-- Technical Users -->
groups="base.group_no_one"

<!-- Account Invoice Users -->
groups="account.group_account_invoice"

<!-- Account Managers -->
groups="account.group_account_manager"

<!-- Multi-Company -->
groups="base.group_multi_company"
```

---

## Return Action Examples

### Open Form View

```python
return {
    'type': 'ir.actions.act_window',
    'name': _('Electronic Invoice'),
    'res_model': 'l10n_cr.einvoice.document',
    'res_id': einvoice.id,
    'view_mode': 'form',
    'target': 'current',
}
```

### Open List View

```python
return {
    'type': 'ir.actions.act_window',
    'name': _('Electronic Invoices'),
    'res_model': 'l10n_cr.einvoice.document',
    'view_mode': 'tree,form',
    'domain': [('state', '=', 'accepted')],
    'context': {'search_default_filter_this_month': 1},
}
```

### Download File

```python
return {
    'type': 'ir.actions.act_url',
    'url': f'/web/content/{attachment.id}?download=true',
    'target': 'new',
}
```

### Show Notification

```python
return {
    'type': 'ir.actions.client',
    'tag': 'display_notification',
    'params': {
        'title': _('Success'),
        'message': _('Operation completed'),
        'type': 'success',  # success, warning, danger, info
        'sticky': False,
    }
}
```

### Open Wizard

```python
return {
    'type': 'ir.actions.act_window',
    'name': _('Batch Generate'),
    'res_model': 'l10n_cr.batch.einvoice.wizard',
    'view_mode': 'form',
    'target': 'new',
    'context': {'default_invoice_ids': invoice_ids},
}
```

---

## Common Code Snippets

### Create E-Invoice

```python
einvoice = self.env['l10n_cr.einvoice.document'].create({
    'move_id': invoice.id,
    'document_type': 'FE',
    'company_id': invoice.company_id.id,
})
```

### Search E-Invoices

```python
# Draft e-invoices
drafts = self.env['l10n_cr.einvoice.document'].search([
    ('state', '=', 'draft')
])

# This month's accepted
accepted = self.env['l10n_cr.einvoice.document'].search([
    ('state', '=', 'accepted'),
    ('create_date', '>=', month_start),
])
```

### Update State

```python
einvoice.write({
    'state': 'accepted',
    'hacienda_acceptance_date': fields.Datetime.now(),
    'error_message': False,
})
```

### Get Related Invoice

```python
invoice = einvoice.move_id
customer = einvoice.partner_id
company = einvoice.company_id
```

---

## URL Patterns

```python
# E-Invoice Form
/web#id={id}&model=l10n_cr.einvoice.document&view_type=form

# E-Invoice List
/web#model=l10n_cr.einvoice.document&view_type=list

# Settings
/web#model=res.config.settings&action={action_id}

# Download XML
/web/content/{attachment_id}?download=true

# Dashboard
/web#model=l10n_cr.einvoice.document&view_type=graph
```

---

## Testing Commands

```bash
# Upgrade module
odoo-bin -u l10n_cr_einvoice -d database_name

# Run tests
odoo-bin -u l10n_cr_einvoice -d database_name --test-enable

# Check views
odoo-bin -u l10n_cr_einvoice -d database_name --log-level=debug

# Shell access
odoo-bin shell -d database_name
```

### Shell Commands

```python
# Get e-invoice
einvoice = env['l10n_cr.einvoice.document'].browse(1)

# Check state
einvoice.state

# Generate XML
einvoice.action_generate_xml()

# Search
env['l10n_cr.einvoice.document'].search([('state', '=', 'draft')])

# Count
env['l10n_cr.einvoice.document'].search_count([('state', '=', 'accepted')])
```

---

## Debugging Tips

### View Errors

```bash
# Check logs for XML syntax errors
grep -i "error" odoo.log | grep -i "einvoice"

# Check view loading
grep -i "loading view" odoo.log | grep -i "einvoice"
```

### Database Inspection

```sql
-- Check e-invoices
SELECT id, name, state, clave FROM l10n_cr_einvoice_document;

-- Check invoices with e-invoices
SELECT am.name, ed.name, ed.state
FROM account_move am
JOIN l10n_cr_einvoice_document ed ON ed.move_id = am.id;

-- Count by state
SELECT state, COUNT(*)
FROM l10n_cr_einvoice_document
GROUP BY state;
```

### Python Debugging

```python
# Add to method
import pdb; pdb.set_trace()

# Or use logging
import logging
_logger = logging.getLogger(__name__)
_logger.info(f"State: {self.state}, Clave: {self.clave}")
```

---

## File Paths

```
l10n_cr_einvoice/
├── views/
│   ├── einvoice_document_views.xml
│   ├── account_move_views.xml
│   ├── res_config_settings_views.xml
│   ├── res_company_views.xml
│   ├── hacienda_menu.xml
│   ├── einvoice_wizard_views.xml
│   └── einvoice_dashboard_views.xml
├── models/
│   ├── einvoice_document.py
│   └── account_move.py
└── docs/
    ├── USER_GUIDE_PHASE4_UI.md
    ├── PHASE4_TECHNICAL_SUMMARY.md
    ├── UI_MOCKUPS_REFERENCE.md
    └── QUICK_REFERENCE_VIEWS.md
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-28
**Quick Access**: Keep this handy for fast lookups!
