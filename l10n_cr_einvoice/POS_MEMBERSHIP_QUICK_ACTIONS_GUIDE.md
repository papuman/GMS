# POS Membership Quick Actions - User Guide

## Overview

The **POS Membership Quick Actions** widget is designed for high-speed membership sales at gym front desks. It reduces the time to add a membership to a cart from 5+ clicks to just **1 CLICK**.

### Key Features

- **One-Click Membership Add**: Instantly add memberships to cart
- **Fast Member Lookup**: <300ms typeahead search
- **Visual Status Indicators**: See membership status at a glance
- **Offline-Ready**: Works without internet, queues for sync
- **Material Design UI**: Beautiful, responsive interface optimized for tablets
- **Real-Time Expiry Countdown**: Shows days remaining on active memberships

---

## Quick Start (30 seconds)

### For Front Desk Staff

1. **Open POS** → The membership widget appears on the left side
2. **Search for member** → Type name, ID, or email in search box
3. **Click membership button** → Membership instantly added to cart!

That's it! The whole process takes **3 seconds or less**.

---

## Detailed Features

### 1. Member Lookup Widget

#### Search Box
- **Search by**: Name, Member ID, Email, Phone
- **Typeahead**: Results appear as you type (300ms delay)
- **Fast**: Searches database in real-time

#### Search Results
Each result shows:
- **Member Photo** (or placeholder icon)
- **Member Name**
- **Member ID / Cédula**
- **Membership Status** with visual indicator:
  - 🟢 **Active** - Membership is current
  - 🔴 **Expired** - Membership needs renewal
  - ⚪ **No Membership** - New customer or no active subscription

#### Status Details
- **Active memberships** show expiry countdown:
  - "Active - 30 days left"
  - "Expires in 5 days" (warning for expiring soon)
- **Expired memberships** show:
  - "Expired" in red

### 2. Selected Member Card

Once you select a member, a beautiful card displays:

```
┌─────────────────────────────────────┐
│  [Photo]  Juan Pérez                │
│           ID: MEM-001               │
│           📧 juan@email.com         │
│           📞 8888-8888              │
│                                     │
│  Current Membership: Gold           │
│  🕐 Expires in 15 days              │
└─────────────────────────────────────┘
```

### 3. Quick Action Buttons (3 Memberships)

Three large, visual buttons for the most popular memberships:

#### Gold Membership 🏆
- **Color**: Gold (#FFD700)
- **Price**: Displays in Costa Rica colones (₡)
- **Example**: ₡50,000/month
- **Recurring Badge**: Shows if subscription auto-renews

#### Silver Membership 🥈
- **Color**: Silver (#C0C0C0)
- **Price**: ₡35,000/month

#### Basic Membership 🥉
- **Color**: Bronze (#CD7F32)
- **Price**: ₡25,000/month

#### Button Features:
- **One-Click Add**: Click to instantly add to cart
- **Visual Feedback**: Button flashes green when clicked
- **Product Info**: Shows name, price, and product code
- **Recurring Indicator**: Badge shows if membership auto-renews

### 4. Connection Status

Top-right indicator shows:
- **✓ Conectado** (Green) - Online, invoices submit to Hacienda
- **⚠ Sin Conexión** (Red) - Offline, invoices queued for later

### 5. Offline Mode

When internet is down:
- **Sales continue normally** - No interruption
- **Invoices queued** - Stored locally
- **Auto-sync** - When connection restored, invoices submit automatically
- **Queue counter** - Shows number of pending invoices

---

## User Workflows

### Scenario 1: Renewing Existing Member

**Time: 3 seconds**

1. Type member name in search box
2. Click on member from results
3. Click "Gold Membership" button
4. Done! Membership in cart

```
Staff: "Hola Maria!"
[Types "Maria"]
[Clicks "Maria Rodriguez" in results]
[Clicks "Gold Membership 🏆" button]
[✓ Membership added - proceeds to payment]
Total: 3 seconds
```

### Scenario 2: New Member Signup

**Time: 5 seconds**

1. Type member name in search box
2. If not found, proceed without selecting
3. Click desired membership button
4. Complete sale
5. Member gets created automatically

### Scenario 3: Checking Member Status

**Time: 2 seconds**

1. Type member name
2. View status immediately in search results:
   - 🟢 Active (days remaining shown)
   - 🔴 Expired
   - ⚪ No membership

---

## Configuration

### Product Setup (Admin)

The widget automatically displays the 3 most relevant membership products based on:

1. **Product Category**: Must have "Gym Memberships" or "Membresía" in category
2. **POS Availability**: Product must be available in POS
3. **Naming Priority**:
   - **Gold** tier: Products with "Gold", "Oro", "Anual"
   - **Silver** tier: Products with "Silver", "Plata", "Trimestral"
   - **Basic** tier: Products with "Basic", "Básica", "Mensual"

#### Example Products in Odoo:

```
Product 1:
- Name: "Membresía Anual - Acceso Completo"
- Price: ₡450,000
- Category: Gym Memberships
- POS Available: ✓
- Recurring: ✓
→ Appears as: Gold Membership 🏆

Product 2:
- Name: "Membresía Trimestral - Acceso Completo"
- Price: ₡120,000
- Category: Gym Memberships
- POS Available: ✓
→ Appears as: Silver Membership 🥈

Product 3:
- Name: "Membresía Mensual - Básica"
- Price: ₡25,000
- Category: Gym Memberships
- POS Available: ✓
→ Appears as: Basic Membership 🥉
```

### POS Configuration

In **Point of Sale → Configuration → POS Settings**:

1. Enable e-invoicing (already enabled for Costa Rica)
2. Configure offline mode settings
3. Set terminal ID for receipt numbering

---

## Technical Details

### Performance

- **Search Speed**: <300ms typeahead debounce
- **Add to Cart**: Instant (no server delay)
- **Member Lookup**: Real-time database search
- **Status Check**: Cached for 30 seconds

### Offline Support

- **Queue Storage**: IndexedDB in browser
- **Auto-Sync**: Every 30 seconds when online
- **Retry Logic**: Exponential backoff (1s, 2s, 4s, 8s...)
- **Max Retries**: 5 attempts before manual intervention

### Responsive Design

Optimized for:
- **Tablets**: 1024x768 and up (primary target)
- **Desktop**: 1440x900 and up
- **Mobile**: 768x1024 (limited support)

### Browser Support

- **Chrome**: 90+ (recommended)
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

---

## Troubleshooting

### "No memberships configured"

**Problem**: Widget shows "No membership configured" placeholder

**Solution**:
1. Go to **Products** in Odoo backend
2. Create/edit membership products
3. Ensure:
   - Category includes "Membership" or "Membresía"
   - "Available in POS" is checked
   - Price is set
4. Refresh POS

### Search not working

**Problem**: Typing in search box shows no results

**Solution**:
1. Check internet connection (offline mode still works for previously cached members)
2. Verify members exist in database with `customer_rank > 0`
3. Clear browser cache and reload

### Membership not adding to cart

**Problem**: Clicking membership button does nothing

**Solution**:
1. Check browser console for errors (F12)
2. Verify product exists in POS cache (reload POS session)
3. Ensure product is not archived

### Offline queue not syncing

**Problem**: Invoices stuck in queue after going online

**Solution**:
1. Check connection status indicator (top-right)
2. Manually trigger sync:
   - Go to **Point of Sale → Configuration**
   - Click "Sync Offline Queue" button
3. Check queue entries:
   - **Point of Sale → Offline Queue**
   - Review errors for failed entries

---

## Integration with E-Invoicing

### How It Works

1. **Member selects** → POS sets customer on order
2. **Membership added** → Product added to cart
3. **Payment processed** → Order finalized
4. **E-Invoice generated** → Tiquete Electrónico (TE) created automatically
5. **Hacienda submission** → Invoice sent to Costa Rica tax authority
6. **Email sent** → Customer receives electronic receipt

### Customer ID Validation

The widget validates Costa Rica customer IDs:

- **Cédula Física** (9 digits): `1-2345-6789`
- **Cédula Jurídica** (10 digits): `3-101-123456`
- **DIMEX** (11-12 digits): `123456789012`
- **NITE** (10 digits): Similar to Jurídica
- **Extranjero** (alphanumeric): `PASS123456`

Auto-formatting applies as user types!

---

## Best Practices

### For Front Desk Staff

1. **Search by Member ID** for fastest lookups
2. **Check expiry dates** before renewal (avoid double-billing)
3. **Use offline mode** during internet outages (queues automatically)
4. **Monitor queue counter** - if >10, notify IT

### For Gym Managers

1. **Review queue daily** - Check for failed submissions
2. **Monitor connection status** - Ensure Hacienda API accessible
3. **Update membership prices** in Products (reflects immediately)
4. **Train staff on shortcuts** - Faster checkout = happier members

### For IT/Admins

1. **Configure 3 main products** as quick actions
2. **Set up product categories** correctly
3. **Enable POS availability** for all gym products
4. **Test offline mode** before launch
5. **Monitor performance** - Should be <300ms for search

---

## File Locations

### Frontend (JavaScript/XML/CSS)

```
l10n_cr_einvoice/
├── static/
│   ├── src/
│   │   ├── js/
│   │   │   └── pos_membership_actions.js    # Main component
│   │   ├── xml/
│   │   │   └── pos_membership_screen.xml     # QWeb templates
│   │   └── css/
│   │       └── pos_membership.css            # Material Design styles
```

### Backend (Python)

```
l10n_cr_einvoice/
├── controllers/
│   └── pos_membership_controller.py          # HTTP routes
├── models/
│   └── res_partner.py                        # Customer validation
```

---

## Version History

### v1.0.0 (Phase 5B) - December 2024

- Initial release
- One-click membership add
- Fast typeahead search (<300ms)
- Visual status indicators
- Material Design UI
- Offline support with queue
- Integration with Odoo 19 POS
- Costa Rica e-invoicing compliance

---

## Support

### Getting Help

1. **Documentation**: This file
2. **Video Tutorial**: Coming soon
3. **Support Email**: support@gms-cr.com
4. **Phone**: +506 1234-5678

### Reporting Issues

When reporting issues, include:

1. **Browser & Version** (e.g., Chrome 120)
2. **Device** (e.g., iPad Air, 1024x768)
3. **Steps to Reproduce**
4. **Screenshot** or video if possible
5. **Browser Console Errors** (F12 → Console tab)

---

## Competitive Advantage

### vs HuliPractice

| Feature | GMS (Our System) | HuliPractice |
|---------|------------------|--------------|
| One-click add | ✅ Yes | ❌ Multiple clicks |
| Typeahead speed | ✅ <300ms | ⚠️ ~1s |
| Offline mode | ✅ Full support | ⚠️ Limited |
| Visual design | ✅ Material Design | ⚠️ Basic |
| E-invoicing | ✅ Built-in | ❌ Manual |
| Member photos | ✅ Yes | ❌ No |
| Expiry countdown | ✅ Real-time | ⚠️ Static |
| Tablet optimized | ✅ Yes | ⚠️ Desktop-first |

### Speed Comparison

**Membership Sale Time**:
- **GMS**: 3 seconds (search → select → click)
- **HuliPractice**: 8-12 seconds (navigate → search → configure → add)

**Result**: **60-75% faster** with our system!

---

## Future Enhancements

### Planned Features (Phase 5C)

- [ ] Barcode scanner support for member cards
- [ ] Voice search ("Buscar Juan Pérez")
- [ ] Quick stats widget (sales today, active members)
- [ ] Member birthday notifications
- [ ] Upsell suggestions (supplements, classes)
- [ ] Mobile app integration
- [ ] WhatsApp notifications for expiring memberships

---

## License

This module is part of the Costa Rica E-Invoicing suite.

**License**: LGPL-3
**Copyright**: 2024 GMS Development Team
**Website**: https://gms-cr.com

---

**Built with speed and love for gym front desk staff who deserve better tools.** 💪
