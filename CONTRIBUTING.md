# Contributing to GMS

Thank you for your interest in contributing to the **GMS (Gym Management System)** project! This document provides guidelines for contributing code, documentation, and bug reports.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

---

## 🤝 Code of Conduct

### Our Standards

We are committed to providing a welcoming and inclusive environment for all contributors.

**Expected Behavior:**
- ✅ Be respectful and constructive in all communications
- ✅ Welcome newcomers and help them get started
- ✅ Accept constructive criticism gracefully
- ✅ Focus on what is best for the project and community
- ✅ Show empathy towards other community members

**Unacceptable Behavior:**
- ❌ Harassment, discrimination, or offensive comments
- ❌ Personal attacks or inflammatory language
- ❌ Trolling or deliberately derailing discussions
- ❌ Publishing others' private information without permission
- ❌ Any conduct that could be considered unprofessional

**Enforcement:**
Violations of the code of conduct should be reported to [conduct@example.com]. All complaints will be reviewed and investigated promptly and fairly.

---

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.14+** installed
- **PostgreSQL 17+** installed
- **Odoo 19 Enterprise** license (required for development)
- **Git** for version control
- Basic knowledge of Odoo framework
- Familiarity with Python and XML

### Setting Up Development Environment

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/GMS.git
cd GMS

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL-OWNER/GMS.git

# 4. Create development database
createdb gms_dev

# 5. Install dependencies
pip install -r requirements.txt

# 6. Install Odoo modules
./odoo-bin -d gms_dev -i l10n_cr_einvoice,sale_subscription,point_of_sale

# 7. Run development server
./odoo-bin -d gms_dev --dev=all

# 8. Access at http://localhost:8069
```

**Full setup guide:** [Development Documentation](docs/11-development/index.md)

---

## 🔄 Development Workflow

### Branching Strategy

We use **Git Flow** with the following branches:

- **`main`** - Production-ready code, always stable
- **`develop`** - Integration branch for features
- **`feature/*`** - New features (e.g., `feature/member-portal`)
- **`bugfix/*`** - Bug fixes (e.g., `bugfix/invoice-calculation`)
- **`hotfix/*`** - Critical production fixes

### Working on a Feature

```bash
# 1. Update your fork
git checkout develop
git pull upstream develop

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make your changes
# ... code, test, commit ...

# 4. Keep your branch updated
git fetch upstream
git rebase upstream/develop

# 5. Push to your fork
git push origin feature/your-feature-name

# 6. Create Pull Request on GitHub
```

### Commit Message Guidelines

Follow **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, no logic change)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**Examples:**

```
feat(einvoice): add PDF generation with QR codes

Implement PDF generation for e-invoices including:
- QR code with invoice verification URL
- Hacienda-compliant layout
- Customer information and line items

Closes #123
```

```
fix(pos): correct tax calculation for 4% IVA

Fixed rounding error in tax calculation that caused
0.01 cent discrepancies in total amounts.

Fixes #456
```

---

## 📝 Coding Standards

### Python Code Style

**Follow PEP 8** with these Odoo-specific additions:

```python
# Good: Odoo model conventions
class EinvoiceDocument(models.Model):
    _name = 'l10n_cr.einvoice.document'
    _description = 'Costa Rica E-Invoice Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Fields grouped logically
    name = fields.Char(string='Number', required=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)

    # Computed fields with dependencies
    @api.depends('line_ids.price_total')
    def _compute_amount_total(self):
        """Compute total amount including taxes."""
        for record in self:
            record.amount_total = sum(line.price_total for line in record.line_ids)
```

**Key Rules:**
- ✅ 4 spaces for indentation (no tabs)
- ✅ Max line length: 120 characters
- ✅ Docstrings for all public methods
- ✅ Type hints where beneficial
- ✅ Follow Odoo naming conventions (`_name`, `_inherit`, etc.)

### XML Code Style

```xml
<!-- Good: Proper Odoo view structure -->
<odoo>
    <record id="view_einvoice_document_form" model="ir.ui.view">
        <field name="name">einvoice.document.form</field>
        <field name="model">l10n_cr.einvoice.document</field>
        <field name="arch" type="xml">
            <form string="E-Invoice">
                <header>
                    <button name="action_submit_to_hacienda"
                            string="Submit to Hacienda"
                            type="object"
                            class="oe_highlight"/>
                </header>
                <sheet>
                    <group>
                        <field name="partner_id"/>
                        <field name="amount_total"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>
</odoo>
```

**Key Rules:**
- ✅ 4 spaces for indentation
- ✅ Proper nesting and closing tags
- ✅ Use `<odoo>` root tag
- ✅ Meaningful record IDs

### JavaScript Code Style

Follow **Odoo JavaScript Guidelines**:

```javascript
// Good: Odoo widget pattern
odoo.define('l10n_cr_einvoice.DocumentWidget', function (require) {
    'use strict';

    const AbstractField = require('web.AbstractField');
    const fieldRegistry = require('web.field_registry');

    const DocumentWidget = AbstractField.extend({
        /**
         * Initialize widget
         */
        init: function () {
            this._super.apply(this, arguments);
            // Initialization code
        },
    });

    fieldRegistry.add('einvoice_document', DocumentWidget);

    return DocumentWidget;
});
```

---

## 🧪 Testing Guidelines

### Writing Tests

All new features and bug fixes **must include tests**.

```python
# tests/test_einvoice_document.py
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestEinvoiceDocument(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Document = self.env['l10n_cr.einvoice.document']
        self.partner = self.env.ref('base.res_partner_1')

    def test_create_invoice(self):
        """Test invoice creation with required fields."""
        invoice = self.Document.create({
            'partner_id': self.partner.id,
            'amount_total': 1000.00,
        })
        self.assertTrue(invoice.id)
        self.assertEqual(invoice.partner_id, self.partner)

    def test_validation_missing_partner(self):
        """Test validation fails without partner."""
        with self.assertRaises(ValidationError):
            self.Document.create({
                'amount_total': 1000.00,
            })
```

### Running Tests

```bash
# Run all tests
./odoo-bin -d gms_test --test-enable --stop-after-init

# Run specific module tests
./odoo-bin -d gms_test --test-enable --stop-after-init -i l10n_cr_einvoice

# Run specific test file
python -m pytest tests/test_einvoice_document.py -v
```

### Test Coverage

- **Minimum requirement:** 80% code coverage for new code
- **Target:** 95%+ coverage
- Run coverage report: `pytest --cov=l10n_cr_einvoice tests/`

---

## 📚 Documentation

### Code Documentation

**All public methods must have docstrings:**

```python
def action_submit_to_hacienda(self):
    """Submit e-invoice to Ministerio de Hacienda.

    This method:
    1. Generates XML per Hacienda v4.4 specifications
    2. Signs XML with BCCR digital certificate
    3. Submits to Hacienda API
    4. Updates invoice status based on response

    Returns:
        bool: True if submission successful, False otherwise

    Raises:
        ValidationError: If invoice is not in draft state
        UserError: If digital certificate is expired
    """
```

### Documentation Files

When adding features, update relevant documentation:

- **Feature docs:** `docs/12-features/your-feature.md`
- **Implementation:** `docs/05-implementation/index.md`
- **API docs:** `docs/10-api-integration/index.md`

**Follow:** [Documentation Standards](docs/DOCUMENTATION-STANDARDS.md)

---

## 🔀 Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features/fixes
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with `develop`
- [ ] No merge conflicts

### Creating Pull Request

1. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub:**
   - Target branch: `develop` (not `main`)
   - Clear title: "feat(einvoice): Add PDF generation"
   - Description template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that breaks existing functionality)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Related Issues
Closes #123
Related to #456

## Screenshots (if applicable)
[Add screenshots for UI changes]
```

### Review Process

1. **Automated checks** run (tests, linting, coverage)
2. **Code review** by 1-2 maintainers
3. **Revisions** if requested
4. **Approval** and merge to `develop`
5. **Release** to `main` during next release cycle

**Response time:** We aim to review PRs within 48 hours.

---

## 🐛 Reporting Bugs

### Before Reporting

1. **Search existing issues** - Your bug may already be reported
2. **Test on latest version** - Bug may be fixed in recent release
3. **Reproduce consistently** - Document exact steps

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- GMS Version: [e.g., 1.0.0]
- Odoo Version: [e.g., 19.0-20251021]
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]

## Screenshots
If applicable, add screenshots

## Additional Context
Any other relevant information
```

**Submit at:** [GitHub Issues](https://github.com/YOUR-REPO/issues)

---

## 💡 Feature Requests

### Suggesting Features

We welcome feature suggestions! Please:

1. **Check roadmap** - Feature may be planned
2. **Search existing requests** - May already be suggested
3. **Provide business case** - Why is this valuable?
4. **Consider scope** - Should fit GMS vision

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature

## Problem it Solves
What problem does this address?

## Proposed Solution
How should it work?

## Alternatives Considered
What other approaches did you consider?

## Target Users
Who would benefit from this?

## Priority
- [ ] Critical (blocks work)
- [ ] High (significant value)
- [ ] Medium (nice to have)
- [ ] Low (future enhancement)
```

---

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in commits

**Thank you for contributing to GMS!**

---

## 📞 Questions?

- **Documentation:** [docs/index.md](docs/index.md)
- **Development Setup:** [docs/11-development/index.md](docs/11-development/index.md)
- **Architecture:** [docs/04-architecture/index.md](docs/04-architecture/index.md)
- **Contact:** [Email or chat link]

---

**Last Updated:** 2026-01-02
**Version:** 1.0.0
**Maintained By:** GMS Development Team
