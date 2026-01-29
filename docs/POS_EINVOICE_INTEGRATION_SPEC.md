# POS ↔ E-Invoice Integration Specification
## Detailed Technical Architecture for Costa Rica E-Invoicing in Point of Sale

**Document Version:** 1.0.0
**Last Updated:** December 29, 2025
**Author:** GMS Development Team
**Status:** Production Implementation Guide

---

## Table of Contents

1. [Integration Overview](#integration-overview)
2. [Architecture Diagrams](#architecture-diagrams)
3. [Data Models & Relationships](#data-models--relationships)
4. [API Specifications](#api-specifications)
5. [Event Flow Diagrams](#event-flow-diagrams)
6. [Database Schema](#database-schema)
7. [UI Integration Points](#ui-integration-points)
8. [Background Jobs](#background-jobs)
9. [Error Handling Strategy](#error-handling-strategy)
10. [Performance Requirements](#performance-requirements)

---

## Integration Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GMS ECOSYSTEM                                │
│                                                                     │
│  ┌────────────────┐      ┌─────────────────┐      ┌─────────────┐ │
│  │   POS Module   │◄────►│  E-Invoice Mod  │◄────►│  Hacienda   │ │
│  │  (Odoo Core)   │      │ (l10n_cr_einv)  │      │  API (Gov)  │ │
│  └────────┬───────┘      └────────┬────────┘      └─────────────┘ │
│           │                       │                                │
│           │                       │                                │
│           ▼                       ▼                                │
│  ┌────────────────────────────────────────┐                        │
│  │         PostgreSQL Database            │                        │
│  │  - pos.order                           │                        │
│  │  - l10n_cr.einvoice.document           │                        │
│  │  - l10n_cr.pos.offline.queue           │                        │
│  └────────────────────────────────────────┘                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Integration Points

| Integration Point | Type | Direction | Trigger |
|------------------|------|-----------|---------|
| Order Validation | Synchronous | POS → E-Invoice | Order paid |
| E-Invoice Creation | Asynchronous | POS → E-Invoice | After order save |
| Status Update | Bus Message | E-Invoice → POS | Status change |
| Offline Queue | Batch | E-Invoice → Hacienda | Cron (5 min) |
| Status Polling | Batch | E-Invoice ↔ Hacienda | Cron (15 min) |
| Email Delivery | Asynchronous | E-Invoice → Customer | Status accepted |

### 1.3 Module Dependencies

```
point_of_sale (Odoo Core)
    ↓
l10n_cr (Costa Rica Localization)
    ↓
l10n_cr_einvoice (E-Invoice Module)
    ↓ extends
pos.order, pos.session, pos.config
```

---

## Architecture Diagrams

### 2.1 High-Level Component Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                          │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │   POS UI       │  │  Backend Forms │  │  Portal Access   │  │
│  │  (JavaScript)  │  │  (Odoo Views)  │  │  (Customer View) │  │
│  └───────┬────────┘  └───────┬────────┘  └────────┬─────────┘  │
│          │                   │                     │            │
└──────────┼───────────────────┼─────────────────────┼────────────┘
           │                   │                     │
┌──────────▼───────────────────▼─────────────────────▼────────────┐
│                       BUSINESS LOGIC LAYER                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              POS Module (Extended)                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │  pos.order   │  │ pos.session  │  │ pos.config   │  │    │
│  │  │  + CR fields │  │  + CR fields │  │ + CR fields  │  │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │    │
│  └─────────┼──────────────────┼──────────────────┼─────────┘    │
│            │                  │                  │              │
│            └──────────────────┼──────────────────┘              │
│                               │                                 │
│  ┌────────────────────────────▼────────────────────────────┐    │
│  │           E-Invoice Module (l10n_cr_einvoice)          │    │
│  │  ┌──────────────────┐  ┌──────────────────────────┐    │    │
│  │  │ einvoice.document│  │  XML Generator           │    │    │
│  │  │  - clave         │  │  - v4.4 compliance       │    │    │
│  │  │  - status        │  │  - validation            │    │    │
│  │  └────────┬─────────┘  └──────────┬───────────────┘    │    │
│  │           │                       │                     │    │
│  │  ┌────────▼─────────┐  ┌─────────▼──────────────┐     │    │
│  │  │  XML Signer      │  │  Hacienda API Client   │     │    │
│  │  │  - Certificate   │  │  - HTTPS client        │     │    │
│  │  │  - RSA signature │  │  - Retry logic         │     │    │
│  │  └──────────────────┘  └────────┬───────────────┘     │    │
│  │                                 │                      │    │
│  │  ┌──────────────────┐  ┌────────▼────────────────┐    │    │
│  │  │  Offline Queue   │  │  Response Processor     │    │    │
│  │  │  - Retry logic   │  │  - Status mapping       │    │    │
│  │  │  - Batch sync    │  │  - Error categorization │    │    │
│  │  └──────────────────┘  └─────────────────────────┘    │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                │
└────────────────────────────────┬───────────────────────────────┘
                                 │
┌────────────────────────────────▼───────────────────────────────┐
│                       DATA PERSISTENCE LAYER                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL Database                        │   │
│  │                                                         │   │
│  │  Core Tables:           Extension Tables:              │   │
│  │  - pos_order            - l10n_cr_einvoice_document    │   │
│  │  - pos_session          - l10n_cr_pos_offline_queue    │   │
│  │  - pos_payment          - l10n_cr_response_message     │   │
│  │  - res_partner          - l10n_cr_retry_queue          │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL INTEGRATION LAYER                   │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Hacienda API    │  │  SMTP Server     │  │  SMS Gateway │ │
│  │  (Government)    │  │  (Email)         │  │  (Optional)  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Sequence Diagram: Complete Order Flow

```
POS UI          POS Order       E-Invoice        XML Gen       Signer      Hacienda API    Queue
  │                │              Document          │             │              │           │
  │                │                │               │             │              │           │
  │ 1. Validate    │                │               │             │              │           │
  │   Order        │                │               │             │              │           │
  ├───────────────►│                │               │             │              │           │
  │                │                │               │             │              │           │
  │                │ 2. Check CR    │               │             │              │           │
  │                │    Company     │               │             │              │           │
  │                │    Enabled     │               │             │              │           │
  │                │                │               │             │              │           │
  │                │ 3. Generate    │               │             │              │           │
  │                │    Consecutive │               │             │              │           │
  │                │    & Clave     │               │             │              │           │
  │                │                │               │             │              │           │
  │                │ 4. Create      │               │             │              │           │
  │                │    Document    │               │             │              │           │
  │                ├───────────────►│               │             │              │           │
  │                │                │               │             │              │           │
  │                │                │ 5. Generate   │             │              │           │
  │                │                │    XML v4.4   │             │              │           │
  │                │                ├──────────────►│             │              │           │
  │                │                │               │             │              │           │
  │                │                │ 6. Validate   │             │              │           │
  │                │                │    XSD        │             │              │           │
  │                │                │◄──────────────┤             │              │           │
  │                │                │               │             │              │           │
  │                │                │ 7. Sign XML   │             │              │           │
  │                │                ├──────────────────────────► │              │           │
  │                │                │               │             │              │           │
  │                │                │ 8. Signed XML │             │              │           │
  │                │                │◄───────────────────────────┤              │           │
  │                │                │               │             │              │           │
  │                │ 9. Check       │               │             │              │           │
  │                │    Online      │               │             │              │           │
  │                │                │               │             │              │           │
  │                ├─ Online? ──────┤               │             │              │           │
  │                │                │               │             │              │           │
  │         ┌──────┴───────┐        │               │             │              │           │
  │         │ YES          │ NO     │               │             │              │           │
  │         │              │        │               │             │              │           │
  │         │ 10. Submit   │  11. Queue            │             │              │           │
  │         │     to       │      for              │             │              │           │
  │         │     Hacienda │      Retry            │             │              │           │
  │         │              ├────────────────────────────────────────────────────────────────►│
  │         ├─────────────►│        │               │             │              │           │
  │         │              │        │               │             │              │           │
  │         │              │ 12. POST /submit      │             │              │           │
  │         │              ├─────────────────────────────────────────────────► │           │
  │         │              │        │               │             │              │           │
  │         │              │ 13. Response         │             │              │           │
  │         │              │◄──────────────────────────────────────────────────┤           │
  │         │              │        │               │             │              │           │
  │         │ 14. Update   │        │               │             │              │           │
  │         │     Status   │        │               │             │              │           │
  │         │              │        │               │             │              │           │
  │         └──────┬───────┘        │               │             │              │           │
  │                │                │               │             │              │           │
  │                │ 15. Generate   │               │             │              │           │
  │                │     QR Code    │               │             │              │           │
  │                │                │               │             │              │           │
  │                │ 16. Bus        │               │             │              │           │
  │                │     Notification               │             │              │           │
  │◄───────────────┤                │               │             │              │           │
  │                │                │               │             │              │           │
  │ 17. Update UI  │                │               │             │              │           │
  │    Show Status │                │               │             │              │           │
  │                │                │               │             │              │           │

                         BACKGROUND PROCESS (Cron)

                                                                                  Queue
                                                                                    │
                                                                                    │ 18. Cron
                                                                                    │     (Every 5min)
                                                                    E-Invoice       │
                                                                    Document        │
                                                                       │◄───────────┤
                                                                       │            │
                                                                       │ 19. Process│
                                                                       │     Batch  │
                                                                       │            │
                                                    Hacienda API       │            │
                                                          │◄───────────┤            │
                                                          │            │            │
                                                          │ 20. Submit │            │
                                                          │◄───────────┤            │
                                                          │            │            │
                                                          │ 21. Response            │
                                                          ├───────────►│            │
                                                                       │            │
                                                                       │ 22. Update │
                                                                       │     Status │
                                                                       ├───────────►│
```

### 2.3 State Transition Diagram

```
E-Invoice Document State Machine
=================================

                     ┌─────────┐
                     │  DRAFT  │
                     └────┬────┘
                          │
                          │ action_generate_xml()
                          ▼
                     ┌──────────┐
                     │GENERATED │
                     └────┬─────┘
                          │
                          │ action_sign_xml()
                          ▼
                     ┌─────────┐
                     │ SIGNED  │
                     └────┬────┘
                          │
                    ┌─────┴─────┐
                    │           │
        Online?     │           │  Offline?
                    ▼           ▼
            ┌────────────┐  ┌─────────┐
            │ SUBMITTED  │  │ QUEUED  │──────► Retry Queue
            └─────┬──────┘  └─────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
  ┌──────────┐        ┌──────────┐
  │ ACCEPTED │        │ REJECTED │
  └────┬─────┘        └─────┬────┘
       │                    │
       │                    │
       ▼                    ▼
  ┌──────────┐        ┌──────────┐
  │Send Email│        │  ERROR   │
  └──────────┘        └──────────┘
       │                    │
       │                    └────► Manual Review
       ▼
  ┌──────────┐
  │ COMPLETE │
  └──────────┘


POS Order Hacienda Status
==========================

  ┌───────┐
  │ DRAFT │
  └───┬───┘
      │
      │ Order validated
      ▼
  ┌─────────┐
  │ PENDING │ ◄────── Submitted to Hacienda
  └────┬────┘
       │
   ┌───┴────┐
   │        │
   ▼        ▼
┌─────────┐ ┌─────────┐
│ACCEPTED │ │REJECTED │
└─────────┘ └────┬────┘
                 │
                 └────► Retry or Manual Fix
```

---

## Data Models & Relationships

### 3.1 Entity Relationship Diagram

```
┌─────────────────────────────┐
│       res.partner           │
│  ┌──────────────────────┐   │
│  │ - name               │   │
│  │ - vat                │   │
│  │ - l10n_cr_id_type    │   │
│  │ - l10n_cr_id_number  │   │
│  │ - l10n_cr_economic_  │   │
│  │   activity_id        │   │
│  └──────────────────────┘   │
└─────────────┬───────────────┘
              │
              │ partner_id
              │
┌─────────────▼───────────────┐
│       pos.order             │
│  ┌──────────────────────┐   │         ┌────────────────────────┐
│  │ - name               │   │         │  pos.session           │
│  │ - partner_id         │───┼─────────┤  - name                │
│  │ - session_id         │   │         │  - config_id           │
│  │ - amount_total       │   │         │  - state               │
│  │                      │   │         └────────────────────────┘
│  │ CR E-Invoice Fields: │   │
│  │ - l10n_cr_einvoice_  │   │
│  │   document_id        ├───┼──┐
│  │ - l10n_cr_consecutive│   │  │
│  │ - l10n_cr_clave      │   │  │
│  │ - l10n_cr_customer_  │   │  │
│  │   id_type            │   │  │
│  │ - l10n_cr_customer_  │   │  │
│  │   id_number          │   │  │
│  │ - l10n_cr_hacienda_  │   │  │
│  │   status             │   │  │
│  │ - l10n_cr_offline_   │   │  │
│  │   queue              │   │  │
│  │ - l10n_cr_qr_code    │   │  │
│  └──────────────────────┘   │  │
└──────────┬──────────────────┘  │
           │                     │
           │ pos_order_id        │ l10n_cr_einvoice_document_id
           │                     │
┌──────────▼─────────────┐       │
│   pos.order.line       │       │
│  ┌─────────────────┐   │       │
│  │ - product_id    │   │       │
│  │ - qty           │   │       │
│  │ - price_unit    │   │       │
│  │ - discount      │   │       │
│  │ - tax_ids       │   │       │
│  └─────────────────┘   │       │
└────────────────────────┘       │
                                 │
           ┌─────────────────────┘
           │
┌──────────▼───────────────────────┐
│  l10n_cr.einvoice.document       │
│  ┌────────────────────────────┐  │
│  │ - name                     │  │
│  │ - move_id                  │  │
│  │ - company_id               │  │
│  │ - partner_id               │  │
│  │ - document_type (TE/FE/NC) │  │
│  │ - clave (50 digits)        │  │
│  │ - consecutive (20 digits)  │  │
│  │ - xml_content              │  │
│  │ - signed_xml               │  │
│  │ - state                    │  │
│  │ - hacienda_response        │  │
│  │ - hacienda_message         │  │
│  │ - hacienda_submission_date │  │
│  │ - hacienda_acceptance_date │  │
│  │ - error_message            │  │
│  │ - retry_count              │  │
│  └────────────────────────────┘  │
└──────────┬──────────┬────────────┘
           │          │
           │          │ einvoice_document_id
           │          │
           │  ┌───────▼──────────────────────┐
           │  │ l10n_cr.pos.offline.queue    │
           │  │  ┌───────────────────────┐   │
           │  │  │ - pos_order_id        │   │
           │  │  │ - einvoice_document_id│   │
           │  │  │ - xml_data            │   │
           │  │  │ - state               │   │
           │  │  │ - retry_count         │   │
           │  │  │ - last_error          │   │
           │  │  │ - priority            │   │
           │  │  └───────────────────────┘   │
           │  └──────────────────────────────┘
           │
           │ einvoice_document_id
           │
           │  ┌───────────────────────────────┐
           │  │ l10n_cr.response.message      │
           └─►│  ┌────────────────────────┐   │
              │  │ - einvoice_document_id │   │
              │  │ - message_type         │   │
              │  │ - message_content      │   │
              │  │ - hacienda_response    │   │
              │  │ - create_date          │   │
              │  └────────────────────────┘   │
              └────────────────────────────────┘
```

### 3.2 Database Tables Specification

**Table: pos_order (Extended)**

```sql
-- New fields added by l10n_cr_einvoice module
ALTER TABLE pos_order ADD COLUMN IF NOT EXISTS
  l10n_cr_einvoice_document_id INTEGER REFERENCES l10n_cr_einvoice_document(id),
  l10n_cr_consecutive VARCHAR(20),
  l10n_cr_clave VARCHAR(50),
  l10n_cr_customer_id_type VARCHAR(2),
  l10n_cr_customer_id_number VARCHAR(20),
  l10n_cr_customer_name VARCHAR(255),
  l10n_cr_customer_email VARCHAR(255),
  l10n_cr_hacienda_status VARCHAR(20) DEFAULT 'draft',
  l10n_cr_offline_queue BOOLEAN DEFAULT FALSE,
  l10n_cr_hacienda_error TEXT,
  l10n_cr_qr_code BYTEA;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_pos_order_einvoice_doc
  ON pos_order(l10n_cr_einvoice_document_id);
CREATE INDEX IF NOT EXISTS idx_pos_order_hacienda_status
  ON pos_order(l10n_cr_hacienda_status);
CREATE INDEX IF NOT EXISTS idx_pos_order_clave
  ON pos_order(l10n_cr_clave);
```

**Table: l10n_cr_einvoice_document**

```sql
CREATE TABLE IF NOT EXISTS l10n_cr_einvoice_document (
  id SERIAL PRIMARY KEY,
  create_date TIMESTAMP NOT NULL DEFAULT NOW(),
  write_date TIMESTAMP NOT NULL DEFAULT NOW(),
  create_uid INTEGER REFERENCES res_users(id),
  write_uid INTEGER REFERENCES res_users(id),

  -- Basic info
  name VARCHAR(255) NOT NULL,
  move_id INTEGER NOT NULL REFERENCES account_move(id) ON DELETE CASCADE,
  company_id INTEGER NOT NULL REFERENCES res_company(id),
  partner_id INTEGER REFERENCES res_partner(id),

  -- Document type
  document_type VARCHAR(2) NOT NULL,  -- FE, TE, NC, ND
  clave VARCHAR(50) UNIQUE,
  consecutive VARCHAR(20),

  -- XML content
  xml_content TEXT,
  signed_xml TEXT,
  xml_attachment_id INTEGER REFERENCES ir_attachment(id),

  -- Status
  state VARCHAR(20) NOT NULL DEFAULT 'draft',
  hacienda_response TEXT,
  hacienda_message VARCHAR(500),
  hacienda_submission_date TIMESTAMP,
  hacienda_acceptance_date TIMESTAMP,

  -- Error handling
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,

  -- PDF & Email
  pdf_attachment_id INTEGER REFERENCES ir_attachment(id),
  email_sent BOOLEAN DEFAULT FALSE,
  email_sent_date TIMESTAMP,
  email_retry_count INTEGER DEFAULT 0,

  -- Audit
  processing_time_ms INTEGER,
  submission_time_ms INTEGER
);

-- Indexes
CREATE INDEX idx_einvoice_clave ON l10n_cr_einvoice_document(clave);
CREATE INDEX idx_einvoice_state ON l10n_cr_einvoice_document(state);
CREATE INDEX idx_einvoice_company ON l10n_cr_einvoice_document(company_id);
CREATE INDEX idx_einvoice_submission_date
  ON l10n_cr_einvoice_document(hacienda_submission_date);
```

**Table: l10n_cr_pos_offline_queue**

```sql
CREATE TABLE IF NOT EXISTS l10n_cr_pos_offline_queue (
  id SERIAL PRIMARY KEY,
  create_date TIMESTAMP NOT NULL DEFAULT NOW(),
  write_date TIMESTAMP NOT NULL DEFAULT NOW(),

  -- Relations
  pos_order_id INTEGER NOT NULL REFERENCES pos_order(id) ON DELETE CASCADE,
  einvoice_document_id INTEGER REFERENCES l10n_cr_einvoice_document(id) ON DELETE CASCADE,

  -- Queue data
  xml_data TEXT NOT NULL,
  state VARCHAR(20) NOT NULL DEFAULT 'pending',

  -- Retry logic
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 5,
  last_sync_attempt TIMESTAMP,
  last_error TEXT,

  -- Priority
  priority INTEGER DEFAULT 10,

  -- Performance tracking
  sync_duration_ms INTEGER
);

-- Indexes
CREATE INDEX idx_offline_queue_state ON l10n_cr_pos_offline_queue(state);
CREATE INDEX idx_offline_queue_priority ON l10n_cr_pos_offline_queue(priority, create_date);
CREATE INDEX idx_offline_queue_pos_order ON l10n_cr_pos_offline_queue(pos_order_id);
```

---

## API Specifications

### 4.1 Public API Methods

**Module:** `l10n_cr.einvoice.document`

#### Method: `create_from_pos_order`

**Signature:**
```python
@api.model
def create_from_pos_order(self, pos_order: recordset) -> recordset:
    """
    Create electronic invoice from POS order

    This is the main entry point for POS-to-E-Invoice integration.

    Args:
        pos_order: pos.order recordset (single record)

    Returns:
        l10n_cr.einvoice.document recordset (single record)

    Raises:
        UserError: If validation fails
        ValidationError: If data is invalid

    Example:
        einvoice = self.env['l10n_cr.einvoice.document'].create_from_pos_order(order)
    """
```

**Implementation:**
```python
@api.model
def create_from_pos_order(self, pos_order):
    self._validate_pos_order(pos_order)

    # Prepare data
    invoice_data = self._prepare_invoice_from_pos(pos_order)

    # Create document
    einvoice = self.create(invoice_data)

    # Link to POS order
    pos_order.l10n_cr_einvoice_document_id = einvoice

    return einvoice
```

#### Method: `submit_to_hacienda`

**Signature:**
```python
def submit_to_hacienda(self) -> dict:
    """
    Submit signed XML to Hacienda API

    Returns:
        dict: {
            'success': bool,
            'message': str,
            'clave': str,
            'response_code': str,
        }

    Raises:
        UserError: If not in valid state for submission
        ConnectionError: If API is unreachable

    Example:
        result = einvoice.submit_to_hacienda()
        if result['success']:
            print(f"Submitted successfully: {result['clave']}")
    """
```

**Return Schema:**
```python
{
    "success": True,
    "message": "Documento enviado correctamente",
    "clave": "50612202500011234567890123456789012345678901234567",
    "response_code": "200",
    "submission_date": "2025-12-29T10:30:45",
    "hacienda_response": {
        "estado": "procesando",
        "mensaje": "Documento recibido y en proceso de validación"
    }
}
```

#### Method: `check_hacienda_status`

**Signature:**
```python
def check_hacienda_status(self) -> dict:
    """
    Poll Hacienda for document status

    Returns:
        dict: {
            'estado': str,  # aceptado, rechazado, procesando
            'mensaje': str,
            'fecha': str,
            'detalle': str (if rejected)
        }

    Example:
        status = einvoice.check_hacienda_status()
        if status['estado'] == 'aceptado':
            einvoice.action_send_email()
    """
```

### 4.2 Internal API Methods

**Module:** `pos.order` (Extended)

#### Method: `_l10n_cr_generate_einvoice`

```python
def _l10n_cr_generate_einvoice(self) -> recordset:
    """
    Generate e-invoice for POS order

    INTERNAL METHOD - Called automatically after order validation

    Returns:
        l10n_cr.einvoice.document recordset

    Side Effects:
        - Creates einvoice document
        - Generates XML
        - Signs XML
        - Submits to Hacienda or queues
        - Generates QR code
    """
```

#### Method: `_l10n_cr_queue_for_sync`

```python
def _l10n_cr_queue_for_sync(self, einvoice: recordset) -> recordset:
    """
    Queue invoice for offline sync

    Args:
        einvoice: l10n_cr.einvoice.document record

    Returns:
        l10n_cr.pos.offline.queue recordset
    """
```

### 4.3 RPC API (JavaScript ↔ Python)

**Client-Side Call:**

```javascript
// JavaScript: POS UI
const result = await this.env.services.rpc({
    model: 'l10n_cr.einvoice.document',
    method: 'get_einvoice_status',
    args: [einvoice_id],
});

if (result.state === 'accepted') {
    this.showPopup('SuccessPopup', {
        title: 'E-Invoice Accepted',
        body: `Clave: ${result.clave}`,
    });
}
```

**Server-Side Handler:**

```python
@api.model
def get_einvoice_status(self, einvoice_id):
    """RPC endpoint for POS UI to check e-invoice status"""
    einvoice = self.browse(einvoice_id)

    return {
        'state': einvoice.state,
        'clave': einvoice.clave,
        'hacienda_message': einvoice.hacienda_message,
        'qr_code': einvoice.partner_id.l10n_cr_qr_code,
        'pdf_url': einvoice.pdf_attachment_id.url if einvoice.pdf_attachment_id else False,
    }
```

### 4.4 Bus Messages API

**Server → Client Notifications:**

```python
def _send_status_update(self):
    """Send bus notification when status changes"""
    self.ensure_one()

    if self.pos_order_ids:
        pos_session = self.pos_order_ids[0].session_id
        channel = f'pos_session_{pos_session.id}'

        self.env['bus.bus']._sendone(channel, 'einvoice_status_update', {
            'order_id': self.pos_order_ids[0].id,
            'einvoice_id': self.id,
            'state': self.state,
            'hacienda_status': self.hacienda_message,
            'clave': self.clave,
            'timestamp': fields.Datetime.now().isoformat(),
        })
```

**Client-Side Listener:**

```javascript
// JavaScript: Subscribe to bus messages
setup() {
    super.setup();

    this.env.services.bus_service.addChannel(`pos_session_${this.pos.pos_session.id}`);
    this.env.services.bus_service.addEventListener(
        'notification',
        this._onBusNotification.bind(this)
    );
}

_onBusNotification({ detail: notifications }) {
    for (const { type, payload } of notifications) {
        if (type === 'einvoice_status_update') {
            this._handleEInvoiceUpdate(payload);
        }
    }
}

_handleEInvoiceUpdate(data) {
    const order = this.pos.orders.find(o => o.id === data.order_id);
    if (order) {
        order.l10n_cr_hacienda_status = data.state;
        order.l10n_cr_clave = data.clave;

        this.showNotification(`E-Invoice ${data.state}: ${data.hacienda_status}`, {
            type: data.state === 'accepted' ? 'success' : 'warning',
        });
    }
}
```

---

## Event Flow Diagrams

### 5.1 Happy Path: Successful E-Invoice Generation

```
Time     POS Terminal    POS Order Model    E-Invoice Module    Hacienda API    Customer
 │           │                │                    │                  │            │
 │  Customer checkout         │                    │                  │            │
 ├──────────►│                │                    │                  │            │
 │           │                │                    │                  │            │
 │           │ Select payment │                    │                  │            │
 │           │ method         │                    │                  │            │
 │           │                │                    │                  │            │
 │           │ Validate order │                    │                  │            │
 │           ├───────────────►│                    │                  │            │
 │           │                │                    │                  │            │
 │           │                │ Create consecutive │                  │            │
 │           │                │ & clave            │                  │            │
 │           │                │                    │                  │            │
 │           │                │ Generate e-invoice │                  │            │
 │           │                ├───────────────────►│                  │            │
 │           │                │                    │                  │            │
 │           │                │                    │ Generate XML     │            │
 │           │                │                    │ (v4.4)           │            │
 │           │                │                    │                  │            │
 │           │                │                    │ Sign XML         │            │
 │           │                │                    │ (Certificate)    │            │
 │           │                │                    │                  │            │
 │           │                │                    │ Submit           │            │
 │           │                │                    ├─────────────────►│            │
 │           │                │                    │                  │            │
 │           │                │                    │ Response:        │            │
 │           │                │                    │ Accepted         │            │
 │           │                │                    │◄─────────────────┤            │
 │           │                │                    │                  │            │
 │           │                │                    │ Generate QR      │            │
 │           │                │                    │                  │            │
 │           │                │ Update status      │                  │            │
 │           │                │◄───────────────────┤                  │            │
 │           │                │                    │                  │            │
 │           │ Print receipt  │                    │                  │            │
 │           │ with QR code   │                    │                  │            │
 │◄──────────┤                │                    │                  │            │
 │           │                │                    │                  │            │
 │           │                │                    │ Send email       │            │
 │           │                │                    ├─────────────────────────────►│
 │           │                │                    │                  │            │
 │  Receipt  │                │                    │                  │  Email     │
 │  printed  │                │                    │                  │  received  │
 │           │                │                    │                  │            │
 ▼           ▼                ▼                    ▼                  ▼            ▼

Total Time: ~5-8 seconds
```

### 5.2 Offline Path: Queue and Retry

```
Time     POS Terminal    POS Order Model    E-Invoice Module    Offline Queue    Hacienda API
 │           │                │                    │                  │                │
 │  Customer checkout         │                    │                  │                │
 ├──────────►│                │                    │                  │                │
 │           │                │                    │                  │                │
 │           │ Validate order │                    │                  │                │
 │           ├───────────────►│                    │                  │                │
 │           │                │                    │                  │                │
 │           │                │ Generate e-invoice │                  │                │
 │           │                ├───────────────────►│                  │                │
 │           │                │                    │                  │                │
 │           │                │                    │ Generate & Sign  │                │
 │           │                │                    │ XML              │                │
 │           │                │                    │                  │                │
 │           │                │                    │ Check online     │                │
 │           │                │                    │ status           │                │
 │           │                │                    │                  │                │
 │           │                │                    │ OFFLINE          │                │
 │           │                │                    │ detected         │                │
 │           │                │                    │                  │                │
 │           │                │                    │ Queue for sync   │                │
 │           │                │                    ├─────────────────►│                │
 │           │                │                    │                  │                │
 │           │                │ Set status:        │                  │                │
 │           │                │ 'queued'           │                  │                │
 │           │                │◄───────────────────┤                  │                │
 │           │                │                    │                  │                │
 │           │ Print receipt  │                    │                  │                │
 │           │ "Pending sync" │                    │                  │                │
 │◄──────────┤                │                    │                  │                │
 │           │                │                    │                  │                │
 │  Customer │                │                    │                  │                │
 │  completes│                │                    │                  │                │
 │           │                │                    │                  │                │
 │           │                │                    │                  │                │
 │           │         LATER: Cron Job            │                  │                │
 │           │                │                    │                  │                │
 │           │                │                    │ Process queue    │                │
 │           │                │                    │◄─────────────────┤                │
 │           │                │                    │                  │                │
 │           │                │                    │ Check online     │                │
 │           │                │                    │                  │                │
 │           │                │                    │ ONLINE           │                │
 │           │                │                    │                  │                │
 │           │                │                    │ Submit batch     │                │
 │           │                │                    ├────────────────────────────────►│
 │           │                │                    │                  │                │
 │           │                │                    │ Response         │                │
 │           │                │                    │◄────────────────────────────────┤
 │           │                │                    │                  │                │
 │           │                │ Update status      │                  │                │
 │           │                │◄───────────────────┤                  │                │
 │           │                │                    │                  │                │
 │           │ Bus notification                    │                  │                │
 │           │ to POS                              │                  │                │
 │◄──────────┴────────────────┴────────────────────┤                  │                │
 │           │                │                    │                  │                │
 │  UI shows │                │                    │                  │                │
 │  "Accepted"                │                    │                  │                │
 │           │                │                    │                  │                │
 ▼           ▼                ▼                    ▼                  ▼                ▼
```

### 5.3 Error Path: Hacienda Rejection

```
Time     POS Terminal    POS Order Model    E-Invoice Module    Hacienda API    Admin
 │           │                │                    │                  │           │
 │  Normal flow...            │                    │                  │           │
 │           │                │                    │                  │           │
 │           │                │                    │ Submit           │           │
 │           │                │                    ├─────────────────►│           │
 │           │                │                    │                  │           │
 │           │                │                    │ Response:        │           │
 │           │                │                    │ REJECTED         │           │
 │           │                │                    │ Error: Invalid   │           │
 │           │                │                    │ Cabys code       │           │
 │           │                │                    │◄─────────────────┤           │
 │           │                │                    │                  │           │
 │           │                │                    │ Parse error      │           │
 │           │                │                    │ Categorize       │           │
 │           │                │                    │                  │           │
 │           │                │ Update status:     │                  │           │
 │           │                │ 'rejected'         │                  │           │
 │           │                │◄───────────────────┤                  │           │
 │           │                │                    │                  │           │
 │           │                │                    │ Create response  │           │
 │           │                │                    │ message record   │           │
 │           │                │                    │                  │           │
 │           │ Show warning   │                    │                  │           │
 │◄──────────┤                │                    │                  │           │
 │           │                │                    │                  │           │
 │  "E-invoice│                │                    │                  │           │
 │   rejected,│                │                    │                  │           │
 │   but order│                │                    │                  │           │
 │   is valid"│                │                    │                  │           │
 │           │                │                    │                  │           │
 │           │                │                    │ Send email       │           │
 │           │                │                    │ notification     │           │
 │           │                │                    ├────────────────────────────►│
 │           │                │                    │                  │           │
 │           │                │                    │                  │  Admin    │
 │           │                │                    │                  │  reviews  │
 │           │                │                    │                  │           │
 │           │                │                    │                  │  Fixes    │
 │           │                │                    │                  │  product  │
 │           │                │                    │                  │  Cabys    │
 │           │                │                    │                  │           │
 │           │                │                    │ Manual resubmit  │           │
 │           │                │                    │◄────────────────────────────┤
 │           │                │                    │                  │           │
 ▼           ▼                ▼                    ▼                  ▼           ▼
```

---

## Database Schema

### 6.1 Complete Schema Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SCHEMA                               │
│                         l10n_cr_einvoice + POS                             │
└────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐
│     res_company         │
│─────────────────────────│
│  id                PK   │
│  name                   │
│  vat                    │
│  country_id         FK  │
│  ─ CR Fields ─          │
│  l10n_cr_enable_        │
│    einvoice             │
│  l10n_cr_certificate_   │
│    id               FK  │
│  l10n_cr_hacienda_      │
│    username             │
│  l10n_cr_hacienda_      │
│    password             │
│  l10n_cr_hacienda_      │
│    environment          │
└────────┬────────────────┘
         │
         │ company_id
         │
┌────────▼────────────────┐      ┌──────────────────────────┐
│     pos_config          │      │    pos_session           │
│─────────────────────────│      │──────────────────────────│
│  id                PK   │◄─────┤  id                 PK   │
│  name                   │ FK   │  name                    │
│  company_id         FK  ├──┐   │  config_id          FK   │
│  ─ CR Fields ─          │  │   │  state                   │
│  l10n_cr_enable_        │  │   │  start_at                │
│    einvoice             │  │   │  stop_at                 │
│  l10n_cr_te_sequence_   │  │   └────────┬─────────────────┘
│    id               FK  │  │            │
└─────────────────────────┘  │            │ session_id
                             │            │
                             │   ┌────────▼─────────────────┐
                             │   │     pos_order            │
                             │   │──────────────────────────│
                             │   │  id                 PK   │
                             │   │  name                    │
                             │   │  session_id         FK   ├──┐
                             │   │  partner_id         FK   │  │
                             │   │  date_order              │  │
                             │   │  amount_total            │  │
                             │   │  state                   │  │
                             │   │  ─ CR E-Invoice Fields ──│  │
                             │   │  l10n_cr_einvoice_       │  │
                             │   │    document_id      FK   ├──┼──┐
                             │   │  l10n_cr_consecutive     │  │  │
                             │   │  l10n_cr_clave           │  │  │
                             │   │  l10n_cr_customer_       │  │  │
                             │   │    id_type               │  │  │
                             │   │  l10n_cr_customer_       │  │  │
                             │   │    id_number             │  │  │
                             │   │  l10n_cr_customer_name   │  │  │
                             │   │  l10n_cr_customer_email  │  │  │
                             │   │  l10n_cr_hacienda_status │  │  │
                             │   │  l10n_cr_offline_queue   │  │  │
                             │   │  l10n_cr_hacienda_error  │  │  │
                             │   │  l10n_cr_qr_code         │  │  │
                             │   └────────┬─────────────────┘  │  │
                             │            │                     │  │
                             │            │ pos_order_id        │  │
                             │            │                     │  │
                             │   ┌────────▼─────────────────┐   │  │
                             │   │   pos_order_line         │   │  │
                             │   │──────────────────────────│   │  │
                             │   │  id                 PK   │   │  │
                             │   │  order_id           FK   ├───┘  │
                             │   │  product_id         FK   │      │
                             │   │  qty                     │      │
                             │   │  price_unit              │      │
                             │   │  discount                │      │
                             │   │  tax_ids_after_fiscal_   │      │
                             │   │    position              │      │
                             │   └──────────────────────────┘      │
                             │                                     │
                             └─────────────────────────────────────┼──┐
                                                                   │  │
┌──────────────────────────┐         ┌──────────────────────────┐ │  │
│   res_partner            │         │  account_move            │ │  │
│──────────────────────────│         │──────────────────────────│ │  │
│  id                 PK   │◄────────┤  id                 PK   │ │  │
│  name                    │ FK      │  partner_id         FK   │ │  │
│  vat                     │         │  company_id         FK   ├─┘  │
│  email                   │         │  move_type               │    │
│  ─ CR Fields ─           │         │  invoice_date            │    │
│  l10n_cr_identification_ │         │  state                   │    │
│    type                  │         └────────┬─────────────────┘    │
│  l10n_cr_identification_ │                  │                      │
│    number                │                  │ move_id              │
│  l10n_cr_economic_       │                  │                      │
│    activity_id      FK   │                  │                      │
└──────────────────────────┘         ┌────────▼────────────────────┐ │
                                     │  l10n_cr_einvoice_document  │ │
                                     │─────────────────────────────│ │
                                     │  id                    PK   │◄┘
                                     │  create_date                │
                                     │  write_date                 │
                                     │  ─ Basic Info ─             │
                                     │  name                       │
                                     │  move_id              FK   ─┘
                                     │  company_id           FK
                                     │  partner_id           FK
                                     │  ─ Document Info ─
                                     │  document_type
                                     │  clave (UNIQUE)
                                     │  consecutive
                                     │  ─ XML ─
                                     │  xml_content          TEXT
                                     │  signed_xml           TEXT
                                     │  xml_attachment_id    FK
                                     │  ─ Status ─
                                     │  state
                                     │  hacienda_response    TEXT
                                     │  hacienda_message
                                     │  hacienda_submission_date
                                     │  hacienda_acceptance_date
                                     │  ─ Error ─
                                     │  error_message        TEXT
                                     │  retry_count
                                     │  ─ PDF & Email ─
                                     │  pdf_attachment_id    FK
                                     │  email_sent
                                     │  email_sent_date
                                     │  email_retry_count
                                     │  ─ Performance ─
                                     │  processing_time_ms
                                     │  submission_time_ms
                                     └──────┬──────────────────────┘
                                            │
                            ┌───────────────┴────────────────────┐
                            │                                    │
               ┌────────────▼────────────────┐    ┌──────────────▼──────────────────┐
               │ l10n_cr_pos_offline_queue   │    │ l10n_cr_response_message        │
               │──────────────────────────────│    │─────────────────────────────────│
               │  id                     PK   │    │  id                        PK   │
               │  create_date                 │    │  create_date                    │
               │  write_date                  │    │  einvoice_document_id      FK   │
               │  ─ Relations ─               │    │  message_type                   │
               │  pos_order_id          FK    │    │  message_content           TEXT │
               │  einvoice_document_id  FK    │    │  hacienda_response         TEXT │
               │  ─ Queue Data ─              │    │  response_code                  │
               │  xml_data              TEXT  │    │  severity                       │
               │  state                       │    └─────────────────────────────────┘
               │  ─ Retry Logic ─             │
               │  retry_count                 │
               │  max_retries                 │
               │  last_sync_attempt           │
               │  last_error            TEXT  │
               │  ─ Priority ─                │
               │  priority                    │
               │  ─ Performance ─             │
               │  sync_duration_ms            │
               └──────────────────────────────┘


INDEXES
=======
pos_order:
  - idx_pos_order_einvoice_doc (l10n_cr_einvoice_document_id)
  - idx_pos_order_hacienda_status (l10n_cr_hacienda_status)
  - idx_pos_order_clave (l10n_cr_clave)

l10n_cr_einvoice_document:
  - idx_einvoice_clave (clave) UNIQUE
  - idx_einvoice_state (state)
  - idx_einvoice_company (company_id)
  - idx_einvoice_submission_date (hacienda_submission_date)

l10n_cr_pos_offline_queue:
  - idx_offline_queue_state (state)
  - idx_offline_queue_priority (priority, create_date)
  - idx_offline_queue_pos_order (pos_order_id)
```

---

## UI Integration Points

### 7.1 POS Terminal UI Extensions

**File:** `l10n_cr_einvoice/static/src/xml/pos_einvoice.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates id="template" xml:space="preserve">

    <!-- Customer Selection with E-Invoice Fields -->
    <t t-name="CustomerEInvoiceFields" t-inherit="point_of_sale.ClientListScreen" t-inherit-mode="extension">
        <xpath expr="//div[hasclass('client-details')]" position="inside">
            <div class="einvoice-section">
                <h4>Información para Factura Electrónica</h4>

                <div class="form-group">
                    <label>Tipo de Identificación</label>
                    <select t-model="state.customer.l10n_cr_identification_type">
                        <option value="01">Cédula Física</option>
                        <option value="02">Cédula Jurídica</option>
                        <option value="03">DIMEX</option>
                        <option value="04">NITE</option>
                        <option value="05">Extranjero</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Número de Identificación</label>
                    <input type="text"
                           t-model="state.customer.l10n_cr_identification_number"
                           placeholder="Ingrese número"/>
                </div>

                <div class="form-group">
                    <label>Actividad Económica (CIIU)</label>
                    <select t-model="state.customer.l10n_cr_economic_activity_id">
                        <t t-foreach="getEconomicActivities()" t-as="activity">
                            <option t-att-value="activity.id" t-esc="activity.name"/>
                        </t>
                    </select>
                </div>
            </div>
        </xpath>
    </t>

    <!-- E-Invoice Status Badge on Order -->
    <t t-name="OrderEInvoiceStatus" t-inherit="point_of_sale.OrderWidget" t-inherit-mode="extension">
        <xpath expr="//div[hasclass('order-info')]" position="inside">
            <div class="einvoice-status"
                 t-if="order.l10n_cr_hacienda_status">
                <span class="badge"
                      t-att-class="{
                          'badge-success': order.l10n_cr_hacienda_status === 'accepted',
                          'badge-warning': order.l10n_cr_hacienda_status === 'pending',
                          'badge-danger': order.l10n_cr_hacienda_status === 'rejected',
                          'badge-info': order.l10n_cr_hacienda_status === 'queued'
                      }">
                    <i class="fa fa-file-text-o"/>
                    <t t-if="order.l10n_cr_hacienda_status === 'accepted'">E-Factura Aceptada</t>
                    <t t-if="order.l10n_cr_hacienda_status === 'pending'">E-Factura Pendiente</t>
                    <t t-if="order.l10n_cr_hacienda_status === 'rejected'">E-Factura Rechazada</t>
                    <t t-if="order.l10n_cr_hacienda_status === 'queued'">E-Factura en Cola</t>
                </span>
            </div>
        </xpath>
    </t>

    <!-- E-Invoice Actions on Receipt Screen -->
    <t t-name="ReceiptEInvoiceActions" t-inherit="point_of_sale.ReceiptScreen" t-inherit-mode="extension">
        <xpath expr="//div[hasclass('receipt-actions')]" position="inside">
            <button class="button einvoice-resend"
                    t-if="order.l10n_cr_einvoice_document_id and order.partner_id.email"
                    t-on-click="resendEInvoiceEmail">
                <i class="fa fa-envelope"/>
                Reenviar Factura Electrónica
            </button>

            <button class="button einvoice-check-status"
                    t-if="order.l10n_cr_hacienda_status === 'pending'"
                    t-on-click="checkEInvoiceStatus">
                <i class="fa fa-refresh"/>
                Verificar Estado
            </button>

            <button class="button einvoice-print-qr"
                    t-if="order.l10n_cr_qr_code"
                    t-on-click="printQRCode">
                <i class="fa fa-qrcode"/>
                Imprimir Código QR
            </button>
        </xpath>
    </t>

    <!-- QR Code Display -->
    <t t-name="EInvoiceQRCode">
        <div class="einvoice-qr-code">
            <h3>Factura Electrónica - Código QR</h3>
            <div class="qr-container">
                <img t-att-src="'data:image/png;base64,' + order.l10n_cr_qr_code"
                     alt="QR Code"/>
            </div>
            <p class="clave">
                <strong>Clave:</strong> <t t-esc="order.l10n_cr_clave"/>
            </p>
            <p class="instructions">
                Escanee este código para verificar la factura en el sitio de Hacienda
            </p>
        </div>
    </t>

</templates>
```

### 7.2 Backend Form Extensions

**File:** `l10n_cr_einvoice/views/pos_order_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Add E-Invoice Tab to POS Order Form -->
    <record id="view_pos_order_form_einvoice" model="ir.ui.view">
        <field name="name">pos.order.form.einvoice</field>
        <field name="model">pos.order</field>
        <field name="inherit_id" ref="point_of_sale.view_pos_pos_form"/>
        <field name="arch" type="xml">

            <!-- Smart Buttons -->
            <div name="button_box" position="inside">
                <!-- E-Invoice Document Button -->
                <button name="action_view_einvoice_document"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-file-text-o"
                        attrs="{'invisible': [('l10n_cr_einvoice_document_id', '=', False)]}">
                    <div class="o_stat_info">
                        <field name="l10n_cr_hacienda_status"
                               widget="badge"
                               decoration-success="l10n_cr_hacienda_status == 'accepted'"
                               decoration-warning="l10n_cr_hacienda_status == 'pending'"
                               decoration-danger="l10n_cr_hacienda_status == 'rejected'"
                               decoration-info="l10n_cr_hacienda_status == 'queued'"/>
                        <span class="o_stat_text">E-Invoice</span>
                    </div>
                </button>

                <!-- Offline Queue Button -->
                <button name="action_view_offline_queue"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-clock-o"
                        attrs="{'invisible': [('l10n_cr_offline_queue', '=', False)]}">
                    <div class="o_stat_info">
                        <span class="o_stat_value">Queued</span>
                        <span class="o_stat_text">Offline Sync</span>
                    </div>
                </button>
            </div>

            <!-- Add E-Invoice Tab -->
            <xpath expr="//notebook" position="inside">
                <page string="E-Invoice (Costa Rica)"
                      name="einvoice_cr"
                      attrs="{'invisible': [('l10n_cr_is_einvoice', '=', False)]}">

                    <group>
                        <group string="Document Information">
                            <field name="l10n_cr_consecutive" readonly="1"/>
                            <field name="l10n_cr_clave" readonly="1"/>
                            <field name="l10n_cr_einvoice_document_id" readonly="1"/>
                            <field name="l10n_cr_hacienda_status" widget="badge"/>
                        </group>

                        <group string="Customer Information">
                            <field name="l10n_cr_customer_id_type"/>
                            <field name="l10n_cr_customer_id_number"/>
                            <field name="l10n_cr_customer_name"/>
                            <field name="l10n_cr_customer_email"/>
                        </group>
                    </group>

                    <!-- QR Code Display -->
                    <group string="QR Code for Verification"
                           attrs="{'invisible': [('l10n_cr_qr_code', '=', False)]}">
                        <field name="l10n_cr_qr_code"
                               widget="image"
                               options="{'size': [200, 200]}"/>
                    </group>

                    <!-- Error Messages -->
                    <group string="Error Details"
                           attrs="{'invisible': [('l10n_cr_hacienda_error', '=', False)]}">
                        <field name="l10n_cr_hacienda_error"
                               widget="text"
                               class="text-danger"/>
                    </group>

                    <!-- Action Buttons -->
                    <group>
                        <button name="action_l10n_cr_resend_email"
                                string="Resend E-Invoice Email"
                                type="object"
                                class="btn-primary"
                                icon="fa-envelope"
                                attrs="{'invisible': ['|',
                                                     ('l10n_cr_einvoice_document_id', '=', False),
                                                     ('l10n_cr_customer_email', '=', False)]}"/>

                        <button name="action_l10n_cr_resubmit_hacienda"
                                string="Resubmit to Hacienda"
                                type="object"
                                class="btn-warning"
                                icon="fa-refresh"
                                attrs="{'invisible': ['|',
                                                     ('l10n_cr_hacienda_status', '=', 'accepted'),
                                                     ('l10n_cr_einvoice_document_id', '=', False)]}"/>

                        <button name="action_l10n_cr_check_status"
                                string="Check Hacienda Status"
                                type="object"
                                icon="fa-search"
                                attrs="{'invisible': [('l10n_cr_einvoice_document_id', '=', False)]}"/>
                    </group>

                </page>
            </xpath>

        </field>
    </record>

</odoo>
```

---

## Background Jobs

### 8.1 Cron Job Specifications

**File:** `l10n_cr_einvoice/data/pos_cron_jobs.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">

        <!-- Sync Offline E-Invoices -->
        <record id="ir_cron_sync_offline_einvoices" model="ir.cron">
            <field name="name">POS: Sync Offline E-Invoices</field>
            <field name="model_id" ref="model_l10n_cr_pos_offline_queue"/>
            <field name="state">code</field>
            <field name="code">
model.cron_sync_offline_invoices()
            </field>
            <field name="interval_number">5</field>
            <field name="interval_type">minutes</field>
            <field name="numbercall">-1</field>
            <field name="priority">5</field>
            <field name="active">True</field>
            <field name="doall">False</field>
        </record>

        <!-- Poll Hacienda Status -->
        <record id="ir_cron_poll_hacienda_status" model="ir.cron">
            <field name="name">E-Invoice: Poll Hacienda Status</field>
            <field name="model_id" ref="model_l10n_cr_einvoice_document"/>
            <field name="state">code</field>
            <field name="code">
model.cron_poll_hacienda_status()
            </field>
            <field name="interval_number">15</field>
            <field name="interval_type">minutes</field>
            <field name="numbercall">-1</field>
            <field name="priority">10</field>
            <field name="active">True</field>
            <field name="doall">False</field>
        </record>

        <!-- Cleanup Old Queue Entries -->
        <record id="ir_cron_cleanup_queue" model="ir.cron">
            <field name="name">POS: Cleanup Old Queue Entries</field>
            <field name="model_id" ref="model_l10n_cr_pos_offline_queue"/>
            <field name="state">code</field>
            <field name="code">
model.cron_cleanup_old_entries()
            </field>
            <field name="interval_number">1</field>
            <field name="interval_type">days</field>
            <field name="nextcall" eval="(DateTime.now() + timedelta(days=1)).strftime('%Y-%m-%d 02:00:00')"/>
            <field name="numbercall">-1</field>
            <field name="priority">50</field>
            <field name="active">True</field>
            <field name="doall">False</field>
        </record>

        <!-- Send Pending Emails -->
        <record id="ir_cron_send_pending_emails" model="ir.cron">
            <field name="name">E-Invoice: Send Pending Emails</field>
            <field name="model_id" ref="model_l10n_cr_einvoice_document"/>
            <field name="state">code</field>
            <field name="code">
model.cron_send_pending_emails()
            </field>
            <field name="interval_number">10</field>
            <field name="interval_type">minutes</field>
            <field name="numbercall">-1</field>
            <field name="priority">20</field>
            <field name="active">True</field>
            <field name="doall">False</field>
        </record>

    </data>
</odoo>
```

### 8.2 Job Implementation

**Sync Offline Invoices:**
```python
@api.model
def cron_sync_offline_invoices(self):
    """
    Sync queued offline invoices to Hacienda

    Runs every 5 minutes
    Processes up to 50 invoices per run
    """
    _logger.info('Starting offline e-invoice sync job')

    # Get pending entries
    queue_entries = self.search([
        ('state', '=', 'pending'),
        ('retry_count', '<', 5),
    ], limit=50, order='priority, create_date')

    if not queue_entries:
        _logger.info('No pending invoices to sync')
        return

    _logger.info(f'Processing {len(queue_entries)} queued invoices')

    # Check if we're online
    api = self.env['l10n_cr.hacienda.api']
    if not api._test_connection():
        _logger.warning('Hacienda API not reachable, skipping sync')
        return

    # Process batch
    success_count = 0
    error_count = 0

    for entry in queue_entries:
        try:
            entry.process_sync()
            if entry.state == 'synced':
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            _logger.error(f'Error syncing entry {entry.id}: {e}', exc_info=True)
            error_count += 1

    _logger.info(f'Sync complete: {success_count} success, {error_count} errors')

    # Send summary notification if errors
    if error_count > 0:
        self._notify_sync_errors(error_count)

    return {
        'success': success_count,
        'errors': error_count,
        'total': len(queue_entries),
    }
```

**Poll Hacienda Status:**
```python
@api.model
def cron_poll_hacienda_status(self):
    """
    Check status of submitted e-invoices

    Runs every 15 minutes
    Checks invoices submitted in last 24 hours
    """
    _logger.info('Starting Hacienda status polling job')

    # Get pending documents
    pending_docs = self.search([
        ('state', '=', 'submitted'),
        ('hacienda_submission_date', '>', fields.Datetime.now() - timedelta(hours=24)),
    ], limit=100, order='hacienda_submission_date')

    if not pending_docs:
        _logger.info('No pending documents to check')
        return

    _logger.info(f'Checking status for {len(pending_docs)} documents')

    api = self.env['l10n_cr.hacienda.api']
    accepted_count = 0
    rejected_count = 0
    still_pending = 0

    for doc in pending_docs:
        try:
            status = api.check_invoice_status(doc.clave, doc.company_id)

            if status['estado'] == 'aceptado':
                doc.write({
                    'state': 'accepted',
                    'hacienda_acceptance_date': fields.Datetime.now(),
                    'hacienda_message': status.get('mensaje'),
                })
                doc.action_send_email()
                accepted_count += 1

            elif status['estado'] == 'rechazado':
                doc.write({
                    'state': 'rejected',
                    'hacienda_message': status.get('mensaje'),
                    'error_message': status.get('detalle'),
                })
                doc._notify_rejection()
                rejected_count += 1

            else:
                still_pending += 1

        except Exception as e:
            _logger.error(f'Error checking status for {doc.clave}: {e}')

    _logger.info(f'Status check complete: {accepted_count} accepted, '
                f'{rejected_count} rejected, {still_pending} still pending')

    return {
        'accepted': accepted_count,
        'rejected': rejected_count,
        'pending': still_pending,
    }
```

---

## Error Handling Strategy

### 9.1 Error Categories

| Category | Severity | Recovery Strategy | User Impact |
|----------|----------|-------------------|-------------|
| **Validation Errors** | Medium | Auto-fix or queue | Order completes, e-invoice queued |
| **Network Errors** | Low | Auto-retry | Transparent to user |
| **Hacienda Rejection** | High | Manual review | Admin notification |
| **Certificate Issues** | Critical | Immediate alert | All e-invoicing blocked |
| **System Errors** | High | Log and notify | Graceful degradation |

### 9.2 Error Handling Implementation

```python
class EInvoiceErrorHandler:
    """Centralized error handling for e-invoice module"""

    ERROR_CATEGORIES = {
        'validation': {
            'severity': 'medium',
            'retry': False,
            'notify_admin': False,
        },
        'network': {
            'severity': 'low',
            'retry': True,
            'max_retries': 5,
            'notify_admin': False,
        },
        'hacienda_rejection': {
            'severity': 'high',
            'retry': False,
            'notify_admin': True,
        },
        'certificate': {
            'severity': 'critical',
            'retry': False,
            'notify_admin': True,
            'block_operations': True,
        },
        'system': {
            'severity': 'high',
            'retry': False,
            'notify_admin': True,
        },
    }

    @classmethod
    def handle_error(cls, exception, context):
        """
        Handle error based on category

        Args:
            exception: Exception object
            context: dict with context info

        Returns:
            dict: Action to take
        """
        category = cls._categorize_error(exception)
        config = cls.ERROR_CATEGORIES[category]

        # Log error
        _logger.error(
            f'E-Invoice error [{category}]: {str(exception)}',
            exc_info=True,
            extra={'context': context}
        )

        # Create error record
        cls._create_error_record(exception, category, context)

        # Notify if needed
        if config['notify_admin']:
            cls._notify_admin(exception, category, context)

        # Block operations if critical
        if config.get('block_operations'):
            cls._block_einvoice_operations(context.get('company_id'))

        return {
            'category': category,
            'severity': config['severity'],
            'should_retry': config.get('retry', False),
            'max_retries': config.get('max_retries', 0),
        }

    @classmethod
    def _categorize_error(cls, exception):
        """Determine error category from exception"""

        if isinstance(exception, ValidationError):
            return 'validation'

        if isinstance(exception, (requests.exceptions.Timeout,
                                 requests.exceptions.ConnectionError)):
            return 'network'

        if hasattr(exception, 'hacienda_code'):
            return 'hacienda_rejection'

        if 'certificate' in str(exception).lower():
            return 'certificate'

        return 'system'

    @classmethod
    def _create_error_record(cls, exception, category, context):
        """Create error log record"""
        env = context.get('env')
        if not env:
            return

        env['l10n_cr.einvoice.error.log'].sudo().create({
            'category': category,
            'exception_type': type(exception).__name__,
            'error_message': str(exception),
            'context': json.dumps(context),
            'einvoice_document_id': context.get('einvoice_id'),
            'pos_order_id': context.get('pos_order_id'),
        })

    @classmethod
    def _notify_admin(cls, exception, category, context):
        """Send notification to administrators"""
        env = context.get('env')
        if not env:
            return

        admin_group = env.ref('l10n_cr_einvoice.group_einvoice_manager')

        env['mail.message'].sudo().create({
            'subject': f'E-Invoice Error: {category.upper()}',
            'body': cls._format_error_message(exception, category, context),
            'model': 'l10n_cr.einvoice.document',
            'res_id': context.get('einvoice_id'),
            'partner_ids': [(6, 0, admin_group.users.mapped('partner_id').ids)],
            'subtype_id': env.ref('mail.mt_comment').id,
        })

    @classmethod
    def _format_error_message(cls, exception, category, context):
        """Format error message for notification"""
        return f"""
<h3>E-Invoice Error Detected</h3>
<p><strong>Category:</strong> {category}</p>
<p><strong>Severity:</strong> {cls.ERROR_CATEGORIES[category]['severity']}</p>
<p><strong>Error:</strong> {str(exception)}</p>
<p><strong>Context:</strong></p>
<ul>
    <li>POS Order: {context.get('pos_order_id')}</li>
    <li>E-Invoice Document: {context.get('einvoice_id')}</li>
    <li>Company: {context.get('company_id')}</li>
    <li>Timestamp: {fields.Datetime.now()}</li>
</ul>
<p><strong>Action Required:</strong></p>
<p>{cls._get_action_guidance(category)}</p>
        """

    @classmethod
    def _get_action_guidance(cls, category):
        """Get guidance message for error category"""
        guidance = {
            'validation': 'Review data and fix validation issues',
            'network': 'Check internet connectivity',
            'hacienda_rejection': 'Review Hacienda response and correct data',
            'certificate': 'URGENT: Check certificate validity and renewal',
            'system': 'Check system logs and contact support if needed',
        }
        return guidance.get(category, 'Review error details')
```

---

## Performance Requirements

### 10.1 Target Metrics

| Operation | Target | Acceptable | Critical |
|-----------|--------|------------|----------|
| POS Order Creation | < 2s | < 5s | > 10s |
| E-Invoice Generation | < 3s | < 5s | > 8s |
| XML Generation | < 1s | < 2s | > 3s |
| XML Signing | < 0.5s | < 1s | > 2s |
| Hacienda Submission | < 5s | < 10s | > 15s |
| Queue Processing (50 items) | < 60s | < 120s | > 180s |
| Status Polling (100 items) | < 30s | < 60s | > 90s |

### 10.2 Performance Monitoring

```python
class PerformanceMonitor:
    """Monitor and track e-invoice performance metrics"""

    @contextmanager
    def track_operation(self, operation_name):
        """
        Context manager to track operation timing

        Usage:
            with self.track_operation('xml_generation'):
                # ... operation code ...
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # milliseconds
            self._record_metric(operation_name, duration)
            self._check_threshold(operation_name, duration)

    def _record_metric(self, operation, duration_ms):
        """Record metric in database"""
        self.env['l10n_cr.einvoice.metrics'].create({
            'operation': operation,
            'duration_ms': duration_ms,
            'timestamp': fields.Datetime.now(),
            'company_id': self.env.company.id,
        })

    def _check_threshold(self, operation, duration_ms):
        """Check if performance threshold exceeded"""
        thresholds = {
            'xml_generation': 3000,
            'xml_signing': 1000,
            'hacienda_submission': 10000,
        }

        threshold = thresholds.get(operation)
        if threshold and duration_ms > threshold:
            _logger.warning(
                f'Performance threshold exceeded: {operation} '
                f'took {duration_ms}ms (threshold: {threshold}ms)'
            )

    @api.model
    def get_performance_report(self, period_hours=24):
        """Generate performance report"""
        cutoff = fields.Datetime.now() - timedelta(hours=period_hours)

        metrics = self.env['l10n_cr.einvoice.metrics'].search([
            ('timestamp', '>', cutoff)
        ])

        # Group by operation
        by_operation = defaultdict(list)
        for metric in metrics:
            by_operation[metric.operation].append(metric.duration_ms)

        # Calculate statistics
        report = {}
        for operation, durations in by_operation.items():
            report[operation] = {
                'count': len(durations),
                'avg': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations),
                'p95': sorted(durations)[int(len(durations) * 0.95)],
            }

        return report
```

---

## Conclusion

This document provides a complete technical specification for the POS ↔ E-Invoice integration. Key implementation points:

1. **Use Model Inheritance** - Extend pos.order without forking
2. **Offline Queue** - Ensure reliability with automatic retry
3. **Real-time Updates** - Use bus messaging for UI feedback
4. **Error Handling** - Graceful degradation with admin notifications
5. **Performance Monitoring** - Track and optimize critical paths

**Next Steps:**
1. Review architecture with development team
2. Create detailed task breakdown
3. Set up development environment
4. Implement Phase 1: Core integration
5. Test in staging environment
6. Deploy to production

**Document References:**
- Main Architecture Guide: `/docs/GMS_MODULE_ARCHITECTURE_GUIDE.md`
- API Documentation: Auto-generated from code
- Test Suite: `/l10n_cr_einvoice/tests/`

---

**Document Status:** Production Ready
**Last Updated:** December 29, 2025
**Maintained By:** GMS Development Team
