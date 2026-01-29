# TiloPay Payment Portal - Static Mockups

## Overview

This directory contains static HTML mockups of the TiloPay payment portal that can be viewed directly in a web browser without running Odoo. These mockups demonstrate the enhanced UI/UX design with all animations, responsive behavior, and interactive elements.

## Files

### HTML Mockups
- `mockup_payment_form.html` - Payment form page with method selection
- `mockup_payment_success.html` - Success confirmation page
- `mockup_payment_failed.html` - Payment failure page

### Styles
- `src/css/payment_portal.css` - Complete CSS stylesheet (800+ lines)

### JavaScript
- Inline JavaScript in HTML files for interactive demos
- `src/js/payment_form_enhanced.js` - Full implementation for Odoo

## How to View Mockups

### Option 1: Direct File Opening
1. Navigate to this directory in Finder
2. Double-click any `.html` file
3. It will open in your default browser

### Option 2: Local Web Server (Recommended)
Better for testing since some features work better with a server:

```bash
# Navigate to the static directory
cd /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/payment_tilopay/static

# Start a simple Python web server
python3 -m http.server 8000

# Open browser to:
# http://localhost:8000/mockup_payment_form.html
```

### Option 3: VS Code Live Server
1. Open the `static` folder in VS Code
2. Install "Live Server" extension
3. Right-click on `mockup_payment_form.html`
4. Select "Open with Live Server"

## Testing Scenarios

### Payment Form Page
**File**: `mockup_payment_form.html`

**Test Cases**:
1. Click SINPE Móvil - should highlight and show info alert
2. Click Card - should highlight and show different info alert
3. Click "Pagar Ahora" without selection - should show error
4. Select method and click "Pagar Ahora" - should show loading overlay and redirect to success page

**Mobile Testing**:
- Resize browser to 375px width (iPhone SE)
- Buttons should be full width
- All text should be readable
- Touch targets should be easy to tap

**Keyboard Testing**:
- Tab through all interactive elements
- Arrow keys to navigate payment methods
- Enter/Space to select methods
- Enter to submit form

### Success Page
**File**: `mockup_payment_success.html`

**Features to Observe**:
- Animated checkmark SVG (draws itself)
- Green gradient header
- Transaction details layout
- Responsive button group
- Print functionality (click print badge)

### Failed Page
**File**: `mockup_payment_failed.html`

**Features to Observe**:
- Error icon animation
- Red gradient header
- Error message display
- Common reasons list
- What to do next section
- Retry button
- Support contact info

## Mobile Testing Guide

### iPhone Sizes to Test
```
iPhone SE:      375 x 667
iPhone 12/13:   390 x 844
iPhone 12 Pro:  428 x 926
```

### Android Sizes to Test
```
Galaxy S20:     360 x 800
Pixel 5:        393 x 851
```

### Chrome DevTools Mobile Testing
1. Open mockup in Chrome
2. Press F12 to open DevTools
3. Click device toolbar icon (or Cmd+Shift+M)
4. Select device from dropdown
5. Test interactions and scrolling

### Testing Checklist
- [ ] All text is readable at 320px width
- [ ] Buttons are easy to tap (48px+ height)
- [ ] No horizontal scrolling
- [ ] Images/icons scale appropriately
- [ ] Forms are easy to fill on mobile
- [ ] Animations perform smoothly (60fps)
- [ ] Loading states are visible
- [ ] Error messages are clear

## Responsive Breakpoints

The CSS uses mobile-first design with these breakpoints:

```css
/* Base: 320px - 639px (Mobile) */
/* Default styles */

/* Small tablets: 640px+ */
@media (min-width: 640px) {
  /* Detail rows switch to horizontal layout */
}

/* Tablets/Desktop: 768px+ */
@media (min-width: 768px) {
  /* Button groups horizontal */
  /* Larger font sizes */
  /* Wider max-width (800px) */
}
```

## Accessibility Testing

### Screen Reader Testing
**macOS VoiceOver**:
1. Press Cmd+F5 to enable VoiceOver
2. Use VO+Right Arrow to navigate
3. Listen to ARIA labels
4. Test form submission

**iOS VoiceOver**:
1. Settings > Accessibility > VoiceOver > On
2. Swipe right to navigate
3. Double-tap to activate

### Keyboard Navigation
1. Tab through all interactive elements
2. Verify focus indicators visible
3. Test arrow key navigation for radio buttons
4. Ensure no keyboard traps

### Color Contrast
All text meets WCAG AA standards:
- Regular text: 4.5:1 minimum
- Large text: 3:1 minimum
- Interactive elements clearly distinguishable

## Browser Compatibility

### Tested Browsers
- Chrome 90+ (Desktop + Mobile)
- Safari 14+ (Desktop + iOS)
- Firefox 88+
- Edge 90+

### Known Issues
- IE11: Not supported (uses CSS Grid, Variables)
- Safari < 14: Some animation issues
- Firefox < 88: Minor flexbox differences

## Performance Notes

### Load Time Targets
- First Contentful Paint: < 1.8s
- Time to Interactive: < 3.9s
- Total page weight: < 100KB (excluding fonts)

### Optimization Techniques Used
- No external dependencies (except FontAwesome)
- Inline critical CSS
- Hardware-accelerated animations
- Efficient selectors
- No JavaScript frameworks

## Customization

### Changing Colors
Edit the CSS variables in `src/css/payment_portal.css`:

```css
:root {
    --tilopay-primary: #2563eb;        /* Change primary color */
    --tilopay-success: #10b981;        /* Change success color */
    /* ... more variables ... */
}
```

### Adding Content
The HTML files use semantic structure. To add content:

1. Find the relevant section (marked with comments)
2. Copy the HTML pattern
3. Update text content
4. Test responsiveness

### Modifying Animations
CSS animations are defined at the bottom of `payment_portal.css`:

```css
@keyframes tilopay-spin {
    to { transform: rotate(360deg); }
}

/* Modify timing, easing, or properties */
.tilopay-spinner {
    animation: tilopay-spin 0.8s linear infinite;
}
```

## Screenshots

To capture screenshots for documentation:

### Desktop
1. Open mockup in browser
2. Set browser width to 1280px
3. Cmd+Shift+4 (macOS) to capture region
4. Save to documentation folder

### Mobile
1. Open Chrome DevTools
2. Select iPhone 12 (390px)
3. Capture screenshot from DevTools menu
4. Save with descriptive name

## Integration with Odoo

These mockups demonstrate the final UI/UX that will appear in Odoo. The actual implementation uses:

- **Templates**: `/views/portal_invoice_views.xml`
- **Styles**: `/static/src/css/payment_portal.css`
- **Scripts**: `/static/src/js/payment_form_enhanced.js`

The Odoo templates use the same CSS classes and HTML structure, so the appearance will be identical.

## Feedback & Iteration

### Testing With Users
1. Share mockup URL with test users
2. Ask them to complete payment flow
3. Observe interaction patterns
4. Note confusion points
5. Iterate on design

### A/B Testing Ideas
- Button text variations
- Color scheme preferences
- Layout alternatives
- CTA placement

## Support

For questions about the mockups or implementation:
- **Email**: soporte@gym.cr
- **Phone**: +506 1234-5678
- **Developer**: GMS Development Team

## Version History

### v1.0.0 (2024-12-28)
- Initial mockup release
- Payment form page
- Success/failure pages
- Mobile-first responsive design
- Accessibility features
- Loading states and animations

---

**Last Updated**: December 28, 2024
**Status**: Ready for Testing
