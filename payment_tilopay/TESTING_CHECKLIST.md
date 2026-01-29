# TiloPay Payment Portal - UI/UX Testing Checklist

## Overview
Complete testing checklist for the enhanced TiloPay payment portal UI/UX. Use this checklist to ensure all features work correctly before deployment.

---

## 1. Visual Design Testing

### Desktop (1920x1080)
- [ ] Payment form displays correctly
- [ ] Cards have proper shadows and borders
- [ ] Gradients render smoothly in headers
- [ ] Icons display correctly (FontAwesome loaded)
- [ ] Typography is readable and well-spaced
- [ ] Colors match brand guidelines
- [ ] Payment method cards are visually distinct
- [ ] Security badges visible and aligned
- [ ] Payment logos display in a row
- [ ] Footer spacing appropriate

### Tablet (768px - 1024px)
- [ ] Layout adjusts appropriately
- [ ] Text remains readable
- [ ] Buttons maintain appropriate size
- [ ] Card width adapts to viewport
- [ ] Images/icons scale correctly
- [ ] Navigation remains accessible
- [ ] Two-column layouts work correctly
- [ ] Spacing feels balanced

### Mobile (375px - 414px)
- [ ] Single-column layout active
- [ ] Buttons are full-width
- [ ] Touch targets minimum 48px height
- [ ] Text size at least 16px (prevents zoom)
- [ ] Horizontal scrolling absent
- [ ] Cards fit viewport width
- [ ] Payment methods stack vertically
- [ ] All content accessible without zooming

### Very Small Mobile (320px)
- [ ] Content still readable
- [ ] No layout breaking
- [ ] Buttons remain tappable
- [ ] Text doesn't overflow
- [ ] Critical info visible

---

## 2. Payment Form Page Testing

### Initial Load
- [ ] Page loads within 2 seconds
- [ ] All CSS styles applied
- [ ] JavaScript loads without errors
- [ ] No console errors
- [ ] FontAwesome icons display
- [ ] Page is responsive immediately

### Payment Summary Section
- [ ] Invoice number displays correctly
- [ ] Issue date formatted properly (Spanish)
- [ ] Due date visible and accurate
- [ ] Total amount prominently displayed
- [ ] Currency symbol correct (₡ for CRC)
- [ ] Border/styling on summary box

### Payment Method Selection
- [ ] Both methods visible (SINPE & Card)
- [ ] Radio buttons hidden (custom UI)
- [ ] Icons display correctly
- [ ] Method names in Spanish
- [ ] Descriptions clear and helpful
- [ ] Click anywhere on card selects method
- [ ] Selection highlights correctly
- [ ] Border changes on selection
- [ ] Icon background color changes
- [ ] Only one method selectable at a time

### Payment Method Info Alerts
- [ ] Selecting SINPE shows SINPE info
- [ ] Selecting Card shows Card info
- [ ] Previous alert removed when switching
- [ ] Alert has proper icon and styling
- [ ] Text is informative

### Form Validation
- [ ] Submit without selection shows error
- [ ] Error message in Spanish
- [ ] Error displays prominently
- [ ] Error auto-scrolls into view
- [ ] Error is dismissible or auto-hides
- [ ] Valid submission proceeds

### Payment Button
- [ ] "Pagar Ahora" button prominent
- [ ] Button has lock icon
- [ ] Hover effect works
- [ ] Click triggers submission
- [ ] Button disables during processing
- [ ] Loading spinner shows on submit

### Cancel Button
- [ ] "Cancelar" button visible
- [ ] Secondary styling (less prominent)
- [ ] Click navigates back
- [ ] Hover effect works

### Security Badges
- [ ] Three badges visible
- [ ] SSL badge
- [ ] Encryption badge
- [ ] Secure processing badge
- [ ] Icons display correctly
- [ ] Aligned horizontally (desktop)
- [ ] Stack or wrap on mobile

### Payment Logos
- [ ] VISA logo
- [ ] Mastercard logo
- [ ] AMEX logo
- [ ] SINPE logo
- [ ] Logos aligned
- [ ] Slightly transparent (60% opacity)

---

## 3. Loading States Testing

### Button Loading
- [ ] Button text changes to "Procesando..."
- [ ] Spinner icon appears
- [ ] Button becomes disabled
- [ ] Button cannot be clicked twice

### Overlay Loading
- [ ] Full-screen overlay appears
- [ ] Background dims (50% opacity)
- [ ] Loading card centered
- [ ] Spinner animates smoothly
- [ ] "Procesando su pago" text visible
- [ ] Subtext visible
- [ ] Progress bar animates
- [ ] User cannot interact with form

### Loading Animation
- [ ] Spinner rotates smoothly (60fps)
- [ ] Progress bar animates continuously
- [ ] No jankiness or stuttering
- [ ] Animation respects prefers-reduced-motion

---

## 4. Success Page Testing

### Visual Elements
- [ ] Green gradient header
- [ ] Success icon displays
- [ ] Checkmark SVG visible
- [ ] Checkmark animates (draws itself)
- [ ] Animation smooth and satisfying

### Content
- [ ] "Pago Exitoso" heading
- [ ] Success message in Spanish
- [ ] Thank you message
- [ ] Transaction details visible
- [ ] All details populated:
  - [ ] Reference number
  - [ ] Amount paid
  - [ ] Payment method
  - [ ] Transaction ID
  - [ ] Date and time

### E-invoice Alert
- [ ] Green success alert visible
- [ ] Envelope icon present
- [ ] Message about e-invoice clear
- [ ] Alert properly styled

### Action Buttons
- [ ] "Ver Mis Facturas" button primary
- [ ] "Ver Detalles de Factura" button secondary
- [ ] Buttons side-by-side on desktop
- [ ] Buttons stack on mobile
- [ ] Hover effects work
- [ ] Navigation works correctly

### Print Receipt
- [ ] Print badge/link visible
- [ ] Click triggers print dialog
- [ ] Printed page looks good
- [ ] Unnecessary elements hidden in print

---

## 5. Failed Page Testing

### Visual Elements
- [ ] Red gradient header
- [ ] Error icon displays
- [ ] Warning triangle icon
- [ ] Icon scales in smoothly

### Content
- [ ] "Pago No Procesado" heading
- [ ] Error message clear
- [ ] Apologetic tone
- [ ] Error details shown (if available)

### Error Details Alert
- [ ] Red danger alert
- [ ] Error message from backend
- [ ] Technical details visible
- [ ] Alert properly formatted

### Common Reasons Section
- [ ] Blue info alert
- [ ] List of common reasons:
  - [ ] Insufficient funds
  - [ ] Incorrect card data
  - [ ] Bank rejection
  - [ ] Transaction limit
  - [ ] Connection issues
- [ ] List properly formatted

### What to Do Section
- [ ] Clear heading
- [ ] Actionable steps:
  - [ ] Check funds
  - [ ] Try another method
  - [ ] Contact bank
  - [ ] Contact support
- [ ] Steps easy to read

### Retry Button
- [ ] "Intentar Nuevamente" button
- [ ] Primary button styling
- [ ] Refresh icon present
- [ ] Click navigates to payment form
- [ ] Tracking event fires

### Support Contact
- [ ] Support section visible
- [ ] Phone number clickable (tel: link)
- [ ] Email clickable (mailto: link)
- [ ] Info properly formatted

---

## 6. Pending Page Testing

### Visual Elements
- [ ] Orange/yellow gradient header
- [ ] Pending icon (hourglass)
- [ ] Icon has pulse animation
- [ ] Animation smooth and continuous

### Content
- [ ] "Pago en Proceso" heading
- [ ] Waiting message clear
- [ ] Timeline expectation set (2 minutes)
- [ ] Warning not to close window

### Info Alert
- [ ] Blue info alert
- [ ] "Por favor espere" heading
- [ ] Clear waiting instructions
- [ ] Alert properly styled

### Progress Indicator
- [ ] "Verificando transacción..." text
- [ ] Progress bar visible
- [ ] Progress bar animates
- [ ] Animation continuous

### Transaction Reference
- [ ] Reference number shown (if available)
- [ ] Properly formatted
- [ ] Copy-able

### Refresh Button
- [ ] "Actualizar Estado" button
- [ ] Refresh icon
- [ ] Click reloads page
- [ ] Button prominent

### Auto-Refresh
- [ ] Timer starts on page load
- [ ] Notification shows after 10 seconds
- [ ] Page refreshes after 13 seconds
- [ ] User can manually refresh sooner

---

## 7. Error Page Testing

### Visual Elements
- [ ] Red gradient header
- [ ] Error icon (bug)
- [ ] Icon displays correctly
- [ ] Appropriate tone for technical error

### Content
- [ ] "Error en el Proceso" heading
- [ ] Apologetic message
- [ ] Technical error message
- [ ] Error code (if available)

### What Happened Section
- [ ] Info alert explaining no charge made
- [ ] Reassurance safe to retry
- [ ] Clear explanation

### Support Information
- [ ] Timestamp visible
- [ ] Error code displayed
- [ ] Info for support team
- [ ] Contact details prominent

### Back Button
- [ ] "Volver a Mis Facturas" button
- [ ] Primary styling
- [ ] Navigation works

---

## 8. Accessibility Testing

### Keyboard Navigation
- [ ] Tab through all elements
- [ ] Focus indicators visible
- [ ] Focus order logical
- [ ] Arrow keys navigate payment methods
- [ ] Enter/Space select methods
- [ ] Enter submits form
- [ ] No keyboard traps
- [ ] Skip links available

### Screen Reader (VoiceOver/NVDA)
- [ ] Page title announced
- [ ] Headings announced correctly
- [ ] All buttons have labels
- [ ] Form fields labeled
- [ ] ARIA labels on custom controls
- [ ] Payment methods announced as radio group
- [ ] Selection state announced
- [ ] Error messages announced
- [ ] Loading state announced
- [ ] Live regions update properly

### ARIA Attributes
- [ ] `role="radio"` on payment methods
- [ ] `aria-checked` updates on selection
- [ ] `aria-label` on buttons
- [ ] `aria-hidden="true"` on decorative icons
- [ ] `role="alert"` on error messages
- [ ] `aria-live="polite"` on dynamic content

### Color Contrast
- [ ] Text meets 4.5:1 ratio (WCAG AA)
- [ ] Large text meets 3:1 ratio
- [ ] Interactive elements meet 3:1 ratio
- [ ] Error messages clearly visible
- [ ] Links distinguishable from text

### Focus Management
- [ ] Focus visible on all elements
- [ ] Focus outline at least 2px
- [ ] Focus not hidden by design
- [ ] Focus moves logically
- [ ] Focus returns after modal close

---

## 9. Responsive Behavior Testing

### Breakpoint Transitions
- [ ] Smooth transition at 640px
- [ ] Smooth transition at 768px
- [ ] No layout breaks between breakpoints
- [ ] Content remains accessible at all sizes

### Orientation Changes
- [ ] Portrait to landscape smooth
- [ ] Landscape to portrait smooth
- [ ] No content cut off
- [ ] Layout adjusts appropriately

### Font Scaling
- [ ] Page usable at 200% zoom
- [ ] Text doesn't overflow
- [ ] Layout doesn't break
- [ ] Horizontal scroll minimal

### Touch Interactions (Mobile)
- [ ] Tap targets large enough (48px)
- [ ] No accidental double-taps
- [ ] Swipe gestures don't interfere
- [ ] Pull-to-refresh works (browser native)
- [ ] Pinch-to-zoom works

---

## 10. Animation & Performance Testing

### Animation Smoothness
- [ ] All animations 60fps
- [ ] No janky scrolling
- [ ] Transitions smooth
- [ ] Spinner rotates evenly
- [ ] Checkmark draws smoothly
- [ ] Pulse animation consistent

### Page Load Performance
- [ ] First Contentful Paint < 1.8s
- [ ] Time to Interactive < 3.9s
- [ ] Total page weight < 200KB
- [ ] No render-blocking resources
- [ ] Critical CSS inlined

### Animation Preferences
- [ ] `prefers-reduced-motion` respected
- [ ] Animations disabled for reduced motion
- [ ] Transitions still instant
- [ ] No functionality lost

### Memory & CPU
- [ ] No memory leaks
- [ ] CPU usage reasonable
- [ ] Animations stop when page inactive
- [ ] No infinite loops

---

## 11. Cross-Browser Testing

### Chrome (Latest)
- [ ] All features work
- [ ] Animations smooth
- [ ] Layout correct
- [ ] No console errors

### Safari (Latest)
- [ ] All features work
- [ ] iOS Safari tested
- [ ] Animations smooth
- [ ] Layout correct
- [ ] No console errors

### Firefox (Latest)
- [ ] All features work
- [ ] Animations smooth
- [ ] Layout correct
- [ ] No console errors

### Edge (Latest)
- [ ] All features work
- [ ] Animations smooth
- [ ] Layout correct
- [ ] No console errors

### Mobile Browsers
- [ ] Chrome Mobile
- [ ] Safari iOS
- [ ] Samsung Internet
- [ ] Firefox Mobile

---

## 12. JavaScript Functionality Testing

### Event Handlers
- [ ] Click handlers work
- [ ] Keyboard handlers work
- [ ] Form submission handler
- [ ] Validation runs correctly

### DOM Manipulation
- [ ] Elements added/removed correctly
- [ ] Classes toggle properly
- [ ] Attributes update
- [ ] No DOM errors in console

### Analytics Tracking
- [ ] Page view tracked
- [ ] Payment method selection tracked
- [ ] Payment submission tracked
- [ ] Error events tracked
- [ ] Retry attempts tracked

### Error Handling
- [ ] Try/catch blocks work
- [ ] Errors logged to console
- [ ] User sees friendly messages
- [ ] Page doesn't crash

---

## 13. Content & Copy Testing

### Spanish Translation
- [ ] All text in Spanish
- [ ] Grammar correct
- [ ] Spelling correct
- [ ] Tone appropriate (formal but friendly)
- [ ] Technical terms accurate

### User Messaging
- [ ] Success messages positive
- [ ] Error messages helpful
- [ ] Loading messages reassuring
- [ ] Instructions clear
- [ ] No jargon

### Call-to-Action
- [ ] Primary CTAs clear
- [ ] Button text actionable
- [ ] "Pagar Ahora" prominent
- [ ] "Intentar Nuevamente" encouraging

---

## 14. Security & Trust Elements

### Visual Trust Signals
- [ ] Security badges visible
- [ ] Lock icon on payment button
- [ ] HTTPS mentioned
- [ ] Encryption noted
- [ ] Professional design

### Information Display
- [ ] Transaction details complete
- [ ] Reference numbers shown
- [ ] Timestamps accurate
- [ ] No sensitive data exposed

---

## 15. Integration Testing (with Odoo)

### Template Rendering
- [ ] Templates compile without errors
- [ ] Variables populate correctly
- [ ] Conditional logic works
- [ ] Loops render properly

### Asset Loading
- [ ] CSS loads from manifest
- [ ] JS loads from manifest
- [ ] Load order correct
- [ ] No 404 errors

### Backend Integration
- [ ] Invoice data passes to template
- [ ] Transaction data available
- [ ] Payment methods from config
- [ ] Error messages from backend

### Form Submission
- [ ] Form posts to correct URL
- [ ] CSRF token included
- [ ] Data reaches controller
- [ ] Redirect works

---

## 16. Edge Cases & Error Scenarios

### Network Issues
- [ ] Offline: appropriate error
- [ ] Slow connection: loading state persists
- [ ] Timeout: error message shown
- [ ] Retry works after network restored

### Invalid Data
- [ ] Missing invoice: error page
- [ ] Invalid amount: validation error
- [ ] Expired invoice: appropriate message
- [ ] Already paid: status shown

### Browser Edge Cases
- [ ] JavaScript disabled: fallback
- [ ] Cookies disabled: still works
- [ ] Ad blockers: doesn't break
- [ ] Old browsers: degrades gracefully

---

## 17. User Experience Testing

### First-Time User
- [ ] Interface intuitive
- [ ] No confusion
- [ ] Clear next steps
- [ ] Help available

### Return User
- [ ] Process feels familiar
- [ ] Faster second time
- [ ] Confidence in system

### Task Completion
- [ ] Can pay invoice in < 2 minutes
- [ ] Success rate high
- [ ] Minimal errors
- [ ] Clear feedback throughout

---

## 18. Print Testing

### Print Success Page
- [ ] Page breaks appropriately
- [ ] Colors or grayscale acceptable
- [ ] Unnecessary elements hidden
- [ ] Transaction details complete
- [ ] Readable on paper

### Print Styles
- [ ] Buttons hidden
- [ ] Navigation hidden
- [ ] White background
- [ ] Black text
- [ ] Logo visible (if applicable)

---

## Testing Tools Recommended

### Automated Testing
```bash
# Lighthouse (Performance, Accessibility, SEO)
lighthouse https://your-domain.com/my/invoices/123/pay --view

# Pa11y (Accessibility)
pa11y https://your-domain.com/my/invoices/123/pay

# axe DevTools (Accessibility)
# Install browser extension and run audit

# CSS Validation
npx stylelint "**/*.css"

# JavaScript Linting
npx eslint "**/*.js"
```

### Manual Testing Tools
- Chrome DevTools (Responsive, Performance)
- Firefox DevTools (Accessibility, CSS Grid)
- Safari Web Inspector (iOS testing)
- BrowserStack (Cross-browser)
- LambdaTest (Cross-browser, mobile)

### Accessibility Tools
- WAVE (Browser extension)
- axe DevTools (Browser extension)
- VoiceOver (macOS/iOS)
- NVDA (Windows)
- ChromeVox (Chrome extension)

---

## Sign-off

### Tested By: ___________________________
### Date: ___________________________
### Environment: ___________________________
### Status: [ ] PASS  [ ] FAIL  [ ] NEEDS WORK

### Notes:
```
_______________________________________________________
_______________________________________________________
_______________________________________________________
```

---

**Last Updated**: December 28, 2024
**Version**: 1.0.0
**Module**: payment_tilopay
