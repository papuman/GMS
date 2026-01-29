# Phase 3 Quick Reference Guide

## File Locations

### Models
```
/l10n_cr_einvoice/models/
├── einvoice_document.py          (MODIFIED - Phase 3 integration)
├── hacienda_response_message.py  (NEW - 430 lines)
└── einvoice_retry_queue.py       (NEW - 579 lines)
```

### Views
```
/l10n_cr_einvoice/views/
├── hacienda_response_message_views.xml  (NEW - 180 lines)
├── einvoice_retry_queue_views.xml       (NEW - 200 lines)
├── bulk_operation_wizard_views.xml      (NEW - 160 lines)
└── einvoice_document_views.xml          (MODIFIED - smart buttons)
```

### Wizards
```
/l10n_cr_einvoice/wizards/
└── bulk_operations.py  (NEW - 400 lines)
```

### Tests
```
/l10n_cr_einvoice/tests/
├── test_phase3_polling.py      (NEW - 320 lines, 7 tests)
├── test_phase3_retry_queue.py  (NEW - 350 lines, 12 tests)
└── test_phase3_integration.py  (NEW - 380 lines, 12 tests)
```

---

## Quick Commands

### Access Features

```python
# View Response Messages
Menu: E-Invoicing → Response Messages

# View Retry Queue
Menu: E-Invoicing → Retry Queue

# Access Dashboard
Menu: E-Invoicing → Dashboard

# Bulk Operations (from document list)
Select docs → Action → Bulk Sign/Submit/Check
```

---

**Version:** 19.0.1.4.0
**Phase:** 3 Complete
**Date:** December 29, 2024
