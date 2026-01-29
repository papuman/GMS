# Retry Button Visual Reference

## Form View - Header Section

### Before:
```
[Generate XML] [Sign XML] [Submit to Hacienda] [Check Status] [Generate PDF] [Send Email]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: Draft → Generated → Signed → Submitted → Accepted
```

### After (when error occurs):
```
[Generate XML] [Sign XML] [Submit to Hacienda] [Check Status] [⚠️ Retry] [Generate PDF] [Send Email]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: Draft → Generated → Signed → Submitted → 🔴 Generation Error
```

The Retry button:
- Appears in **warning color** (yellow/orange)
- Only visible when `retry_button_visible` is True
- Shows confirmation: "Retry the failed operation?"

## Status Bar Color Coding

### Success States (Normal Flow):
- **Draft** - Muted gray
- **Generated** - Blue
- **Signed** - Primary
- **Submitted** - Warning yellow
- **Accepted** - Green ✓

### Error States (Now in Red):
- **🔴 Error** - Generic error
- **🔴 Rejected** - Hacienda rejected
- **🔴 Generation Error** - XML creation failed
- **🔴 Signing Error** - Digital signature failed
- **🔴 Submission Error** - Hacienda submission failed

## Kanban View - Quick Actions

### Card Layout with Retry Button:
```
┌─────────────────────────────────────┐
│ EINV-0001                  [FE]    │
│ Customer Name                       │
│                                     │
│ Invoice: INV/2026/0001             │
│ Amount: ₡50,000.00                 │
│                                     │
│ ⚠️  Error Details                   │
│                                     │
│  [⟳ Retry] [📄] [✏️] [📤] [↻]      │
└─────────────────────────────────────┘
```

Quick action buttons from left to right:
1. **⟳ Retry** - Yellow/Warning (only when error)
2. **📄 Generate** - Primary blue (draft/error states)
3. **✏️ Sign** - Primary blue (generated state)
4. **📤 Submit** - Green (signed state)
5. **↻ Check Status** - Secondary (submitted state)

## Button Behavior Matrix

| State              | Retry Button | Primary Action   |
|-------------------|--------------|------------------|
| Draft             | Hidden       | Generate XML     |
| Generated         | Hidden       | Sign XML         |
| Signed            | Hidden       | Submit           |
| Submitted         | Hidden       | Check Status     |
| Accepted          | Hidden       | -                |
| **Generation Error** | **Visible** | **Generate XML** |
| **Signing Error**    | **Visible** | **Sign XML**     |
| **Submission Error** | **Visible** | **Submit**       |
| **Rejected**         | **Visible** | **Generate XML** |
| **Error (generic)**  | **Visible** | **Generate XML** |

## User Flow Example

### Scenario: XML Generation Fails

1. User creates invoice → E-invoice auto-generated in "draft" state
2. System attempts XML generation → Fails
3. **Status bar turns RED** with "Generation Error"
4. **Retry button appears** in header and kanban card
5. User clicks "Retry" → Confirmation dialog appears
6. User confirms → `action_retry()` method called
7. System re-attempts generation from point of failure
8. On success: Button disappears, status returns to normal flow
9. On failure: Button remains, error message updated

## Technical Implementation

### Computed Field Logic
```python
@api.depends('state')
def _compute_retry_button_visible(self):
    for doc in self:
        doc.retry_button_visible = doc.state in [
            'generation_error',
            'signing_error',
            'submission_error',
            'rejected',
            'error'
        ]
```

### Button Attributes
- **name**: `action_retry` - Calls existing retry method
- **type**: `object` - Python method call
- **class**: `btn-warning` - Yellow/orange warning color
- **invisible**: `not retry_button_visible` - Smart visibility
- **confirm**: User-friendly confirmation dialog

## Accessibility Features

1. **Visual Indicators**: Red status bar + warning button color
2. **Icon Clarity**: Repeat icon (fa-repeat) universally understood
3. **Confirmation Safety**: Prevents accidental retries
4. **Multi-location Access**: Available in both form and kanban
5. **Context-aware**: Only appears when retry is meaningful
6. **Error Information**: Error message banner shows details

## CSS Classes Used

- `btn-warning` - Bootstrap warning button (yellow/orange)
- `text-bg-success` - Green ribbon for accepted
- `text-bg-danger` - Red ribbon for rejected/error
- `text-bg-warning` - Yellow ribbon for generic error
- `fa fa-repeat` - FontAwesome repeat/retry icon
- `fa fa-exclamation-triangle` - FontAwesome error indicator
