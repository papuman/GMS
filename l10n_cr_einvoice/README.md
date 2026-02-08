# Costa Rica Electronic Invoicing Module (l10n_cr_einvoice)

## 📋 Overview

Production-ready Odoo 19 module for Costa Rica electronic invoicing (Facturación Electrónica) with full Hacienda v4.4 compliance, POS integration, and advanced features.

**Version**: 19.0.1.0.0
**Author**: GMS Development Team
**License**: LGPL-3
**Compliance**: Hacienda Costa Rica v4.4, Tribu-CR API

---

## ✨ Key Features

### Core E-Invoicing
- ✅ Document Types: FE, TE, NC, ND
- ✅ XML v4.4 compliant generation
- ✅ X.509 digital signature
- ✅ Hacienda API integration with retry logic
- ✅ PDF generation with QR codes
- ✅ Automatic email delivery

### POS Integration  
- ✅ Payment screen extension with FE/TE toggle
- ✅ Smart type detection (auto-select FE for customers with VAT)
- ✅ Touch-optimized UI (48px targets)
- ✅ Keyboard shortcuts (F2/F4)
- ✅ Error recovery flow
- ✅ Offline mode support

### Compliance
- ✅ Phase 1A: Payment methods + SINPE Móvil
- ✅ Phase 1B: Discount codes (11 official)
- ✅ Phase 1C: CIIU economic activity codes (100+)

---

## 🚀 Quick Start

### Installation
\`\`\`bash
pip install lxml xmlschema cryptography pyOpenSSL requests qrcode
\`\`\`

### Configuration
1. **Settings → Accounting → Costa Rica E-Invoicing**
2. Enter Hacienda credentials
3. Upload X.509 certificate
4. Set company activity code
5. **POS → Configuration** → Enable E-Invoicing

### Usage (POS)
1. Add products to cart
2. Payment screen shows **Tiquete (blue)** / **Factura (purple)**
3. Press **F2** to toggle
4. For Factura: Press **F4** to select customer
5. Complete payment → E-invoice auto-generated

---

## 📖 Documentation

See full documentation in `/docs/` folder or [README.md](README.md) for complete guide.

**Quick Links**:
- Installation & Setup
- POS Configuration
- Troubleshooting
- API Reference

---

## 🧪 Testing

\`\`\`bash
# Backend tests
odoo-bin -d DB -i l10n_cr_einvoice --test-enable --stop-after-init

# Specific test
odoo-bin -d DB --test-file=addons/l10n_cr_einvoice/tests/test_pos_offline.py
\`\`\`

---

## 📞 Support

- **Email**: support@gms-cr.com
- **Issues**: GitHub Issues
- **Docs**: See `/docs/` folder

---

Made with ❤️ for Costa Rica
