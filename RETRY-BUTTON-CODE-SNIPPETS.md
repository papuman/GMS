# Retry Button - Complete Code Snippets

## File Locations
- `/Users/papuman/Documents/My Projects/GMS/l10n_cr_einvoice/views/einvoice_document_views.xml`
- `/Users/papuman/Documents/My Projects/GMS/odoo/addons/l10n_cr_einvoice/views/einvoice_document_views.xml`

---

## 1. Form View Header - Retry Button

**Location**: Inside `<header>` section, after main action buttons, before PDF/Email buttons

```xml
<!-- Retry Button for Error States -->
<button name="action_retry"
        type="object"
        string="Retry"
        class="btn-warning"
        invisible="not retry_button_visible"
        confirm="Retry the failed operation? This will attempt to continue the e-invoice process from the point of failure."/>
```

**Context** (showing surrounding code):
```xml
<header>
    <!-- Action Buttons -->
    <button name="action_generate_xml" string="Generate XML"
            type="object" class="oe_highlight"
            invisible="state not in ['draft', 'error']"/>
    <button name="action_sign_xml" string="Sign XML"
            type="object" class="oe_highlight"
            invisible="state != 'generated'"/>
    <button name="action_submit_to_hacienda" string="Submit to Hacienda"
            type="object" class="oe_highlight"
            invisible="state != 'signed'"/>
    <button name="action_check_status" string="Check Status"
            type="object"
            invisible="state != 'submitted'"/>

    <!-- Retry Button for Error States -->
    <button name="action_retry"
            type="object"
            string="Retry"
            class="btn-warning"
            invisible="not retry_button_visible"
            confirm="Retry the failed operation? This will attempt to continue the e-invoice process from the point of failure."/>

    <!-- PDF and Email Buttons -->
    <button name="action_generate_pdf" string="Generate PDF"
            type="object" class="oe_highlight"
            invisible="not xml_content or pdf_attachment_id"/>
    <button name="action_send_email" string="Send Email"
            type="object"
            invisible="state != 'accepted' or email_sent"/>

    <!-- Status Bar -->
    <field name="state" widget="statusbar"
           statusbar_visible="draft,generated,signed,submitted,accepted"
           statusbar_colors='{"rejected":"danger","error":"danger","generation_error":"danger","signing_error":"danger","submission_error":"danger"}'/>
</header>
```

---

## 2. Status Bar Enhancement

**Location**: Inside `<header>` section, replace existing statusbar field

**Before**:
```xml
<field name="state" widget="statusbar"
       statusbar_visible="draft,generated,signed,submitted,accepted"/>
```

**After**:
```xml
<field name="state" widget="statusbar"
       statusbar_visible="draft,generated,signed,submitted,accepted"
       statusbar_colors='{"rejected":"danger","error":"danger","generation_error":"danger","signing_error":"danger","submission_error":"danger"}'/>
```

---

## 3. Kanban View - Field Declaration

**Location**: Inside `<kanban>` tag, add to field declarations list

**Before**:
```xml
<kanban class="o_kanban_mobile" default_group_by="state">
    <field name="name"/>
    <field name="clave"/>
    <field name="document_type"/>
    <field name="partner_id"/>
    <field name="amount_total"/>
    <field name="currency_id"/>
    <field name="state"/>
    <field name="move_id"/>
    <field name="hacienda_message"/>
    <field name="error_message"/>
```

**After**:
```xml
<kanban class="o_kanban_mobile" default_group_by="state">
    <field name="name"/>
    <field name="clave"/>
    <field name="document_type"/>
    <field name="partner_id"/>
    <field name="amount_total"/>
    <field name="currency_id"/>
    <field name="state"/>
    <field name="move_id"/>
    <field name="hacienda_message"/>
    <field name="error_message"/>
    <field name="retry_button_visible"/>
```

---

## 4. Kanban View - Quick Action Button

**Location**: Inside `<div class="oe_kanban_bottom_right">`, add as first button

```xml
<button t-if="record.retry_button_visible.raw_value"
        name="action_retry"
        type="object"
        class="btn btn-sm btn-warning"
        title="Retry Failed Operation">
    <i class="fa fa-repeat"/>
</button>
```

**Full Context** (showing complete quick actions section):
```xml
<div class="oe_kanban_bottom_right">
    <!-- Quick Actions -->
    <button t-if="record.retry_button_visible.raw_value"
            name="action_retry"
            type="object"
            class="btn btn-sm btn-warning"
            title="Retry Failed Operation">
        <i class="fa fa-repeat"/>
    </button>
    <button t-if="record.state.raw_value == 'draft' || record.state.raw_value == 'error'"
            name="action_generate_xml"
            type="object"
            class="btn btn-sm btn-primary"
            title="Generate XML">
        <i class="fa fa-file-code-o"/>
    </button>
    <button t-if="record.state.raw_value == 'generated'"
            name="action_sign_xml"
            type="object"
            class="btn btn-sm btn-primary"
            title="Sign XML">
        <i class="fa fa-pencil"/>
    </button>
    <button t-if="record.state.raw_value == 'signed'"
            name="action_submit_to_hacienda"
            type="object"
            class="btn btn-sm btn-success"
            title="Submit to Hacienda">
        <i class="fa fa-send"/>
    </button>
    <button t-if="record.state.raw_value == 'submitted'"
            name="action_check_status"
            type="object"
            class="btn btn-sm btn-secondary"
            title="Check Status">
        <i class="fa fa-refresh"/>
    </button>
</div>
```

---

## Summary of Changes

### Form View (einvoice_document_form)
1. ✅ Added retry button in header (lines 59-65)
2. ✅ Enhanced statusbar with error colors (line 78)

### Kanban View (einvoice_document_kanban)
1. ✅ Added retry_button_visible field declaration (line 269)
2. ✅ Added retry button in quick actions (lines 336-342)

### Total Lines Modified
- Form view header: +7 lines
- Status bar: +1 attribute
- Kanban fields: +1 line
- Kanban button: +7 lines

### No Changes Required In
- Python model (retry_button_visible already exists)
- Security rules
- Database schema
- Translations (optional enhancement)

---

## Verification Commands

```bash
# Check XML syntax is valid
xmllint --noout /Users/papuman/Documents/My\ Projects/GMS/l10n_cr_einvoice/views/einvoice_document_views.xml
xmllint --noout /Users/papuman/Documents/My\ Projects/GMS/odoo/addons/l10n_cr_einvoice/views/einvoice_document_views.xml

# Compare both files for consistency
diff -u \
  /Users/papuman/Documents/My\ Projects/GMS/l10n_cr_einvoice/views/einvoice_document_views.xml \
  /Users/papuman/Documents/My\ Projects/GMS/odoo/addons/l10n_cr_einvoice/views/einvoice_document_views.xml

# Restart Odoo to apply changes
sudo systemctl restart odoo

# Or upgrade module
odoo-bin -u l10n_cr_einvoice -d your_database
```

---

## Button Attributes Reference

### `name="action_retry"`
- Calls the `action_retry()` method on the einvoice.document model
- Method already exists, implements smart retry logic

### `type="object"`
- Indicates this is a Python method call (not an action window)

### `string="Retry"`
- Button label text displayed to user

### `class="btn-warning"`
- Bootstrap warning button style (yellow/orange color)
- Makes button stand out without being alarming

### `invisible="not retry_button_visible"`
- Dynamic visibility based on computed field
- Only shows when state indicates retry is possible

### `confirm="..."`
- Shows confirmation dialog before executing
- Prevents accidental clicks
- Provides context about what will happen

### `title="Retry Failed Operation"`
- Tooltip shown on hover (kanban button)
- Provides additional context

---

## Related Model Code

The computed field that controls button visibility:

```python
# From l10n_cr_einvoice/models/einvoice_document.py

retry_button_visible = fields.Boolean(
    compute='_compute_retry_button_visible',
    string='Show Retry Button',
    help='Indicates if the retry button should be visible based on error state',
)

@api.depends('state')
def _compute_retry_button_visible(self):
    """Determine if the retry button should be visible based on error state."""
    for doc in self:
        doc.retry_button_visible = doc.state in [
            'generation_error',
            'signing_error',
            'submission_error',
            'rejected',
            'error',
        ]
```

The method called when button is clicked:

```python
def action_retry(self):
    """Retry failed e-invoice operations."""
    # Implementation already exists in model
    # Smart retry based on current error state
```
