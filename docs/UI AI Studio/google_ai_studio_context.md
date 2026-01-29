# Odoo 19 Native Design & POS Framework Context

Use the following context to ensure the UI/UX design for the Invoicing Module and Integration matches the native **Odoo 19 Enterprise** aesthetic.

## 1. Core Design Tokens (SCSS Variables & Odoo 19 Defaults)

Derived from `odoo/addons/web/static/src/scss/primary_variables.scss` and `bootstrap_overridden.scss`.

### Colors (Enterprise)
**Brand Identity:**
- **Primary (Enterprise Purple):** `#714B67`
- **Action Color (Teal):** `#017e84`
- **Community Primary:** `#71639e` (Do not use for Enterprise)

**Semantic Colors:**
- Success: `#28a745` (Green)
- Warning: `#ffac00` (Orange)
- Danger: `#dc3545` (Red)
- Info: `#17a2b8` (Cyan)

**Grays (Bootstrap 5 Compatible):**
- Gray-100: `#f8f9fa` (Backgrounds)
- Gray-200: `#e9ecef` (Borders/Dividers)
- Gray-300: `#dee2e6`
- Gray-700: `#495057` (Secondary Text)
- Gray-900: `#212529` (Primary Text)

### Typography
- **Font Stack**: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Ubuntu, "Noto Sans", Arial, sans-serif`
- **Headings**: `"SF Pro Display"`, plus system fonts.
- **Base Size**: `14px` (Desktop), `16px` (Touch/Mobile).

## 2. Point of Sale (POS) Styles (Odoo 19 Specific)

Derived from `point_of_sale/static/src/scss/pos.scss` and `app/components`.

### Layout Widths
- **Left Pane (Order/Numpad)**: `$pos-left-pane-width` (typically 40-50% on tablets).
- **Responsive Grid**:
  - `xl` screens: columns `minmax(115px, 1fr)`
  - `lg`/`md` screens: columns `minmax(100px, 1fr)`

### Navbar (`navbar.scss`)
- **Height**: Based on `$pos-navbar-height`.
- **Logo**: Centered, `contain` background size.
- **Drop-down Menus**: No padding on container, `2` spacer padding on items.

### Component Styling
- **Buttons**:
  - Standard Height: `calc(var(--btn-height-size) * 2)` (~100px).
  - Tablet Height: `70px`.
  - `.btn-switchpane`: Min-height `70px`.
  - `.button-no-demo`: Teal color `#017e84`.
- **Cards**:
  - Background: `white` (Light Mode).
  - Hover effects: Lighten background by 4%.

### Dark Mode Support (`pos_dashboard.dark.scss`)
Odoo 19 includes native dark mode classes.
- **Card Backgrounds**: `darken($card-bg, 2%)`.
- **Hover**: Lighten by 4%.
- Ensure all new components use CSS variables for colors (e.g., `var(--card-bg)`) to support automatic switching.

## 3. UI Layout Patterns (XML Structure)

### Root Structure (`pos_app.xml`)
```xml
<div class="pos dvh-100 d-flex flex-column">
    <Navbar />
    <div class="pos-content flex-grow-1 overflow-auto bg-100">
        <!-- Dynamic Screen Content -->
    </div>
</div>
```

### Product Screen (`product_screen.xml`)
- **Left Pane**: Order summary, Numpad, Action Buttons.
- **Right Pane**: Category Selector, Product Grid (Flex/Grid layout).
- **Mobile Handling**: Uses `ui.isSmall` to toggle distinct "panes" (Product vs. Cart).

### Payment Screen (`payment_screen.xml`)
- **Left Pane**: Payment Methods (Grid), Numpad, Invoice/Tip buttons.
- **Center/Right**: Large "Total Due" display, Payment Lines list, Validate button.

## 4. Odoo 19 UX Guidelines
1.  **Mobile-First & Responsive**: Use `ui.isSmall` in templates to render different layouts for mobile (single column) vs. desktop (split view).
2.  **Touch Targets**: Minimum `44px` (optimally `70px` for main POS actions).
3.  **Toasts & Popups**: Use native `Transition` and `Popup` components; avoid browser alerts.
4.  **Icons**: Use FontAwesome (`fa-`) or Odoo icons (`oi-`).
5.  **State Management**: Use reactive `useState` inside components.
