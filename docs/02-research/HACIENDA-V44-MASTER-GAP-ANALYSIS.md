# Hacienda v4.4 Factura Electronica - Master Gap Analysis

**Date:** 2026-02-06
**Module:** l10n_cr_einvoice
**Version:** v4.4 (mandatory since 2025-09-01)

This document compares every Hacienda v4.4 requirement against our current implementation, identifies all gaps, and prioritizes the work needed.

---

## TABLE OF CONTENTS

1. [Document Types](#1-document-types)
2. [Clave Numerica (50-digit key)](#2-clave-numerica)
3. [Emisor (Sender)](#3-emisor-sender)
4. [Receptor (Customer)](#4-receptor-customer)
5. [Condicion Venta (Sale Terms)](#5-condicion-venta)
6. [Medio Pago (Payment Method)](#6-medio-pago)
7. [Detalle Servicio (Line Items)](#7-detalle-servicio)
8. [Impuesto (Tax)](#8-impuesto-tax)
9. [Descuento (Discount)](#9-descuento-discount)
10. [Otros Cargos (Other Charges)](#10-otros-cargos)
11. [Resumen Factura (Summary)](#11-resumen-factura)
12. [Informacion Referencia (NC/ND)](#12-informacion-referencia)
13. [Multi-Currency & Exchange Rate](#13-multi-currency)
14. [Hacienda API Submission](#14-hacienda-api)
15. [BCCR Exchange Rate Provider](#15-bccr-provider)
16. [Priority Matrix](#16-priority-matrix)

---

## 1. DOCUMENT TYPES

### v4.4 Supported Types (Nota 1 - Clave position 22-23)
| Code | Type | Our Status |
|------|------|------------|
| 01 | Factura Electronica (FE) | IMPLEMENTED |
| 02 | Nota de Debito Electronica (ND) | IMPLEMENTED |
| 03 | Nota de Credito Electronica (NC) | IMPLEMENTED |
| 04 | Tiquete Electronico (TE) | IMPLEMENTED |
| 05 | Confirmacion Aceptacion | NOT IMPLEMENTED |
| 06 | Confirmacion Aceptacion Parcial | NOT IMPLEMENTED |
| 07 | Confirmacion Rechazo | NOT IMPLEMENTED |
| 08 | Factura Electronica de Compra (FEC) | NOT IMPLEMENTED |
| 09 | Factura Electronica de Exportacion (FEE) | NOT IMPLEMENTED |
| 10 | Recibo Electronico de Pago (REP) - NEW v4.4 | NOT IMPLEMENTED |

### v4.4 Changes
- **REP (code 10)** is new in v4.4. Required when invoicing government entities with deferred IVA payment. The IVA is due when payment is received, not when invoice is issued.
- **FEC (code 08)** expanded to cover more purchase categories.

### Impact Assessment
- Codes 01-04: Core business - DONE
- Codes 05-07: Receiver confirmation messages - needed for accepting supplier invoices
- Code 08: Purchase invoices - needed for expense management
- Code 09: Export invoices - needed if exporting services
- Code 10: REP - needed only for government clients with credit terms
- **Priority: Codes 05-07 are MEDIUM (needed for full workflow), rest LOW for MVP**

---

## 2. CLAVE NUMERICA (50-digit key)

### v4.4 Structure (unchanged from v4.3)
```
PPDDMMAACC SSSTTDDNNNNNNNNNNNNN SS
│ │          │ │ │ │             │
│ │          │ │ │ │             └─ SecurityCode (8 digits, random)
│ │          │ │ │ └───────────── Consecutive (13 digits)
│ │          │ │ └──────────────── DocType (2 digits, from Nota 1)
│ │          │ └────────────────── Terminal (5 digits)
│ │          └──────────────────── Sucursal (3 digits)
│ └─────────────────────────────── Date (DDMMYY, 2-digit year)
└───────────────────────────────── Country code (506)
```

### NumeroConsecutivo (20 digits) - Per v4.4 XSD
```
SSSTTDDNNNNNNNNNNNN
│  │ │ │
│  │ │ └──── Numero Comprobante (12 digits, sequential from 1)
│  │ └────── Tipo Documento (2 digits, from Nota 1)
│  └──────── Terminal/Punto de Venta (3 digits, sequential per branch)
└─────────── Sucursal (3 digits, "001" = headquarters)
```

### Current Status
**File:** `einvoice_document.py` lines 1001-1052

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| Country (3) | `506` | `506` | OK |
| Date (6) | DDMMYY | DDMMYY | OK (now with CR timezone fix) |
| Cedula (12) | Zero-padded | Zero-padded | OK |
| Sucursal (3) | 001-999 | Hardcoded `001` | HARDCODED |
| Terminal (3) | 001-999 | Hardcoded `00001` (wrong length!) | BUG |
| DocType (2) | From Nota 1 | Mapped correctly | OK |
| Consecutive (12) | From sequence | From `ir.sequence` | CHECK LENGTH |
| Situacion (1) | 1=Normal, 2=Contingencia, 3=Sin Internet | 1 | OK |
| SecurityCode (8) | Algorithmically generated | `random.randint` | OK (but see note) |

### Gaps
1. **Terminal is 3 digits, not 5** - Current code uses `00001` (5 digits). Must be `001` (3 digits)
2. **Consecutive should be 12 digits, not 13** - Verify ir.sequence produces correct length
3. **Sucursal/Terminal hardcoded** - Should come from POS config or company settings
4. **Security code uses `random`** - Should use `secrets` module for cryptographic randomness
5. **No collision detection** - Race condition possible with concurrent generation

---

## 3. EMISOR (Sender)

### v4.4 Requirements
| Element | Required | Max Length | Current | Status |
|---------|----------|-----------|---------|--------|
| Nombre | YES | 100 | company.name | OK |
| Identificacion.Tipo | YES | 2 | `_get_company_id_type()` | OK (fixed) |
| Identificacion.Numero | YES | 12 | company.vat | OK |
| NombreComercial | NO | 80 | company.l10n_cr_trade_name | OK |
| Ubicacion.Provincia | YES | 1 | From location code | FRAGILE |
| Ubicacion.Canton | YES | 2 | From location code | FRAGILE |
| Ubicacion.Distrito | YES | 2 | From location code | FRAGILE |
| Ubicacion.Barrio | NO (v4.4) | 2 | From location code | OK |
| Ubicacion.OtrasSenas | YES | 250 | company.street | OK |
| Telefono.CodigoPais | NO | 3 | `506` | OK |
| Telefono.NumTelefono | NO | 20 | company.phone | OK |
| CorreoElectronico | YES | 160 | company.email | BUG |
| **ActividadComercial** | **YES (v4.4)** | 6 | From CIIU | OK |
| **CodigoProveedorSistema** | **NEW v4.4** | 12 | NOT IMPLEMENTED | MISSING |

### Gaps
1. **CorreoElectronico** falls back to `info@example.com` - Should raise error
2. **Location parsing** uses `lstrip('0')` which can destroy valid codes
3. **CodigoProveedorSistema** (NEW in v4.4) - Software developer's cedula. MANDATORY.
4. **Phone validation** too strict / fragile string parsing

### ProveedorSistemas (NEW v4.4) - TOP-LEVEL REQUIRED ELEMENT
This is the identification number of the software developer/provider. In v4.4, this is MANDATORY as a **top-level element** (element #2 in the XML, right after Clave). Max 20 chars. Documents without it will be rejected.

**v4.4 XML Element Order (FE):**
1. `Clave`
2. `ProveedorSistemas` (NEW - REQUIRED)
3. `CodigoActividadEmisor`
4. `NumeroConsecutivo`
5. `FechaEmision`
6. `Emisor`
7. `Receptor`
8. `CondicionVenta`
9. ... (rest of elements)

We need to add a field to company settings or module config to store this value.

---

## 4. RECEPTOR (Customer)

### v4.4 Requirements
| Element | Required | Current | Status |
|---------|----------|---------|--------|
| Nombre | YES | partner.name | OK |
| Identificacion.Tipo | Conditional | `_get_partner_id_type()` | PARTIAL |
| Identificacion.Numero | Conditional | partner.vat | OK |
| **IdentificacionExtranjero** | Type 05 | NOT IMPLEMENTED | CRITICAL |
| CorreoElectronico | NO | partner.email | OK |
| Telefono | NO | NOT IMPLEMENTED | MISSING |
| Ubicacion | NO | NOT IMPLEMENTED | MISSING |
| **ActividadEconomicaReceptor** | **NEW v4.4** | Field exists, NOT in XML | CRITICAL |

### v4.4 Identification Types (Nota 2)
| Code | Type | Current |
|------|------|---------|
| 01 | Cedula Fisica | OK |
| 02 | Cedula Juridica | OK |
| 03 | DIMEX | OK |
| 04 | NITE | OK (fixed) |
| 05 | Extranjero No Domiciliado - NEW v4.4 | WRONG STRUCTURE |
| **06** | **No Contribuyente** - NEW v4.4 | NOT IMPLEMENTED |

### Critical Gaps
1. **Type 05 (Foreign ID)** generates `<Identificacion>` but should generate `<IdentificacionExtranjero>` - different XML element
2. **Types 06, 07** are NEW in v4.4 - not handled at all
3. **ActividadEconomicaReceptor** - NEW v4.4 MANDATORY field when document is used to justify deductible expenses. Field exists on partner model but NOT written to XML.
4. No customer phone or location in XML

---

## 5. CONDICION VENTA (Sale Terms)

### v4.4 Codes (Nota 4)
| Code | Description | Current |
|------|-------------|---------|
| 01 | Contado (Cash) | OK |
| 02 | Credito (Credit) | OK |
| 03 | Consignacion | NOT IMPLEMENTED |
| 04 | Apartado (Layaway) | NOT IMPLEMENTED |
| 05 | Arrendamiento con opcion de compra | NOT IMPLEMENTED |
| 06 | Arrendamiento financiero | NOT IMPLEMENTED |
| 07 | Cobro a favor de un tercero | NOT IMPLEMENTED |
| 08 | Servicios al Estado a credito | NOT IMPLEMENTED |
| 10 | Venta a credito en IVA hasta 90 dias | NOT IMPLEMENTED |
| 12 | Mercancia no nacionalizada (FE only) | NOT IMPLEMENTED |
| 13 | Bienes usados no contribuyente | NOT IMPLEMENTED |
| **14** | **Arrendamiento operativo** - NEW v4.4 | NOT IMPLEMENTED |
| **15** | **Arrendamiento financiero** - NEW v4.4 | NOT IMPLEMENTED |
| 99 | Otros (requires CondicionVentaOtros) | NOT IMPLEMENTED |

### Gaps
1. Only codes 01, 02 are implemented
2. PlazoCredito calculation sums all payment term lines (should use max)
3. New v4.4 codes 07-09 relate to government invoicing and deferred IVA

---

## 6. MEDIO PAGO (Payment Method)

### v4.4 Codes (Nota 5)
| Code | Description | Current |
|------|-------------|---------|
| 01 | Efectivo | OK |
| 02 | Tarjeta | OK |
| 03 | Cheque | OK |
| 04 | Transferencia deposito bancario | OK |
| 05 | Recaudado por terceros | NOT IMPLEMENTED |
| 06 | SINPE Movil | BUG (mapped to 04) |
| **07** | **Plataforma de pago digital** - NEW v4.4 | NOT IMPLEMENTED |
| 99 | Otros | OK |

### v4.4 Structure Change
In v4.4, MedioPago moved from document header to inside ResumenFactura. Our code already places it there.

**MedioPago is now a complex type (max 4 per document):**
```xml
<MedioPago>
  <TipoMedioPago>02</TipoMedioPago>
  <MedioPagoOtros>if code 99</MedioPagoOtros>  <!-- 3-100 chars, required if 99 -->
  <TotalMedioPago>50000.00</TotalMedioPago>     <!-- required if multiple methods -->
</MedioPago>
```

### Gaps
1. **SINPE Movil (06) mapped to 04 (Transferencia)** - BUG. Should be separate code `06`
2. **No TotalMedioPago** per payment method - v4.4 REQUIRES this for split payments
3. **Code 07** new for digital payment platforms (PayPal, etc.)
4. **MedioPagoOtros** field missing (required when code = 99)
5. POS payment detection uses fragile string matching on method name
6. Only generates 1 MedioPago element - should support up to 4

---

## 7. DETALLE SERVICIO (Line Items)

### v4.4 Line Structure
| Element | Required | Current | Status |
|---------|----------|---------|--------|
| NumeroLinea | YES | Sequential | OK |
| **PartidaArancelaria** | NO (new v4.4) | NOT IMPLEMENTED | LOW |
| CodigoCBYS (CABYS) | YES | product field | PARTIAL |
| CodigoComercial | NO | NOT IMPLEMENTED | LOW |
| Cantidad | YES | line.qty | OK |
| UnidadMedida | YES | Hardcoded `Unid` | BUG |
| Detalle | YES | product name | OK |
| PrecioUnitario | YES | line.price_unit | OK |
| MontoTotal | YES | qty * price | OK |
| Descuento | Conditional | Partial | PARTIAL |
| SubTotal | YES | Calculated | OK |
| BaseImponible | Conditional | Calculated | OK |
| Impuesto | Conditional | See section 8 | PARTIAL |
| ImpuestoNeto | YES | Calculated | OK |
| MontoTotalLinea | YES | Calculated | OK |

### v4.4 CABYS Codes
- 13-digit code from Hacienda's official catalog
- Default `8611001000000` (Services/Unclassified) is used as fallback
- Each product SHOULD have its own CABYS code assigned
- **No validation** of CABYS format or validity

### UnidadMedida Valid Codes (Nota 15)
Must use one of: `Al`, `Alc`, `Cm`, `I`, `Os`, `Sp`, `Spe`, `St`, `Unid`, `m`, `kg`, `s`, `A`, `K`, `mol`, `cd`, `m2`, `m3`, `mL`, `L`, `kWh`, `d`, `h`, `min`, `Otros`

Current: Always `Unid` - Cannot invoice by kg, hour, liter, etc.

### Gaps
1. **UnidadMedida hardcoded to `Unid`** - Must be configurable per product/line
2. **CABYS validation** missing - should validate 13-digit format
3. **PartidaArancelaria** (tariff heading) - new in v4.4, optional but useful for imports
4. **No product classification** (service vs merchandise) for summary totals

---

## 8. IMPUESTO (Tax)

### v4.4 Tax Code Table (Nota 6)
| Code | Tax Type | Current |
|------|----------|---------|
| 01 | Impuesto al Valor Agregado (IVA) | OK |
| 02 | Impuesto Selectivo de Consumo | NOT MAPPED |
| 03 | Unico a los combustibles | NOT MAPPED |
| 04 | Bebidas alcoholicas | NOT MAPPED |
| 05 | Bebidas envasadas sin alcohol/jabones tocador | NOT MAPPED |
| 06 | Tabaco | NOT MAPPED |
| 07 | IVA (calculo especial) | NOT MAPPED |
| 08 | IVA Regimen Bienes Usados | NOT MAPPED |
| 12 | Impuesto especifico al cemite asfaltico | NOT MAPPED |
| 99 | Otros | NOT MAPPED |

### CodigoTarifaIVA (Nota 7) - CRITICAL BUG
| Code | Rate | Description | Current |
|------|------|-------------|---------|
| 01 | 0% | Tarifa 0% (Exento) | NOT MAPPED |
| 02 | 1% | Tarifa reducida 1% | NOT MAPPED |
| 03 | 2% | Tarifa reducida 2% | NOT MAPPED |
| 04 | 4% | Tarifa reducida 4% | NOT MAPPED |
| 05 | 0% | Transitorio 0% | NOT MAPPED |
| 06 | 0% | Transitorio 4% | NOT MAPPED |
| 07 | 0% | Transitorio 8% | NOT MAPPED |
| 08 | 13% | Tarifa general 13% | USED AS DEFAULT |
| **09** | **0%** | **No sujeto** - NEW v4.4 | NOT IMPLEMENTED |
| **10** | **0%** | **IVA Regimen Simplificado** - NEW v4.4 | NOT IMPLEMENTED |
| **11** | **0%** | **0% sin derecho a credito** - NEW v4.4 | NOT IMPLEMENTED |

### CRITICAL BUG: `CodigoTarifaIVA = codigo_tax`
**File:** `xml_generator.py` line ~588

Current code sets `CodigoTarifaIVA` to the same value as `Codigo` (the tax type code). This is WRONG.

- `Codigo` = tax TYPE (01=IVA, 02=ISC, etc.)
- `CodigoTarifaIVA` = tax RATE code (01=0%, 08=13%, etc.)

These are completely different tables. A 13% IVA line should have:
```xml
<Codigo>01</Codigo>           <!-- IVA -->
<CodigoTarifaIVA>08</CodigoTarifaIVA>  <!-- 13% rate -->
<Tarifa>13.00</Tarifa>
```

But our code generates:
```xml
<Codigo>01</Codigo>
<CodigoTarifaIVA>01</CodigoTarifaIVA>  <!-- WRONG! 01 = 0% Exento -->
<Tarifa>13.00</Tarifa>
```

**This WILL cause Hacienda rejection.**

### Exoneracion (Tax Exemption) - NOT IMPLEMENTED
v4.4 structure when tax is partially/fully exempt:
```xml
<Exoneracion>
  <TipoDocumento>01-07</TipoDocumento>
  <NumeroDocumento>string</NumeroDocumento>
  <NombreInstitucion>string</NombreInstitucion>
  <FechaEmision>date</FechaEmision>
  <PorcentajeExoneracion>0-100</PorcentajeExoneracion>
  <MontoExoneracion>decimal</MontoExoneracion>
</Exoneracion>
```
Use cases: Medical supplies, medicines, exports, government purchases.

---

## 9. DESCUENTO (Discount)

### CodigoDescuento / NaturalezaDescuento Codes (Nota 8 - ENTIRELY NEW in v4.4)

v4.4 replaced the old freeform NaturalezaDescuento with mandatory CodigoDescuento codes:

| Code | Description | Current |
|------|-------------|---------|
| 01 | Descuento por Regalia (Royalty) | NOT MAPPED |
| 02 | Descuento por Regalia (IVA cobrado al cliente) | NOT MAPPED |
| 03 | Descuento por Bonificacion | NOT MAPPED |
| 04 | Descuento por Volumen | NOT MAPPED |
| 05 | Descuento por Temporada (Seasonal) | NOT MAPPED |
| 06 | Descuento Promocional | NOT MAPPED |
| 07 | Descuento Comercial | NOT MAPPED |
| 08 | Descuento por Frecuencia | NOT MAPPED |
| 09 | Descuento Sostenido | NOT MAPPED |
| 99 | Otros (requires CodigoDescuentoOTRO, 5-100 chars) | USED AS DEFAULT |

**Max 5 discounts per line item.** Structure:
```xml
<Descuento>
  <MontoDescuento>1000.00</MontoDescuento>
  <CodigoDescuento>04</CodigoDescuento>
  <CodigoDescuentoOTRO>text if 99</CodigoDescuentoOTRO>
  <NaturalezaDescuento>optional description 3-80 chars</NaturalezaDescuento>
</Descuento>
```

### Gaps
1. All POS discounts use `99` (Otros) - should map to specific codes
2. account.move calls `_get_discount_nature_for_xml()` which DOES NOT EXIST - will crash
3. `TotalDescuentos` in ResumenFactura is always `0.00000` - BUG
4. Field renamed from `NaturalezaDescuento` to `CodigoDescuento` in v4.4
5. Only 1 discount per line - v4.4 allows up to 5

---

## 10. OTROS CARGOS (Other Charges) - NOT IMPLEMENTED

### TipoDocumentoOC Codes (Nota 11)
| Code | Description | Status |
|------|-------------|--------|
| 01 | Contribucion Parafiscal | NOT IMPLEMENTED |
| 02 | Timbre de la Cruz Roja | NOT IMPLEMENTED |
| 03 | Timbre Colegio de Abogados | NOT IMPLEMENTED |
| 04 | Timbre Archivo Nacional | NOT IMPLEMENTED |
| 05 | Comision por servicio de recaudacion | NOT IMPLEMENTED |
| 06 | Contribucion especial SBD | NOT IMPLEMENTED |
| 07 | Cobros de terceros | NOT IMPLEMENTED |
| **08** | **Deposito de garantia** - NEW v4.4 | NOT IMPLEMENTED |
| **09** | **Multas o Penalizaciones** - NEW v4.4 | NOT IMPLEMENTED |
| **10** | **Intereses moratorios** - NEW v4.4 | NOT IMPLEMENTED |
| 99 | Otros | NOT IMPLEMENTED |

### Structure
```xml
<OtrosCargos>
  <TipoDocumento>code</TipoDocumento>
  <NumeroIdentidadTercero>optional</NumeroIdentidadTercero>
  <NombreTercero>optional</NombreTercero>
  <Detalle>description</Detalle>
  <Porcentaje>optional</Porcentaje>
  <MontoCargo>amount</MontoCargo>
</OtrosCargos>
```

**Priority: LOW** - Not needed for gym membership billing MVP.

---

## 11. RESUMEN FACTURA (Summary)

### Required Elements
| Element | Current | Status |
|---------|---------|--------|
| CodigoTipoMoneda | From currency | OK |
| TipoCambio | Hardcoded `1.00000` | CRITICAL BUG |
| TotalServGravados | Always = amount_untaxed | BUG |
| TotalServExentos | Always `0.00000` | BUG |
| **TotalServExonerado** | NOT IMPLEMENTED | MISSING (NEW v4.4) |
| **TotalServNoSujeto** | NOT IMPLEMENTED | MISSING (NEW v4.4) |
| TotalMercanciasGravadas | Always `0.00000` | BUG |
| TotalMercanciasExentas | Always `0.00000` | BUG |
| **TotalMercExonerada** | NOT IMPLEMENTED | MISSING (NEW v4.4) |
| **TotalMercNoSujeta** | NOT IMPLEMENTED | MISSING (NEW v4.4) |
| TotalGravado | OK | OK |
| TotalExento | Always `0.00000` | BUG |
| **TotalExonerado** | NOT IMPLEMENTED | MISSING (NEW v4.4) |
| **TotalNoSujeto** | NOT IMPLEMENTED | MISSING (NEW v4.4) |
| TotalVenta | OK | OK |
| TotalDescuentos | Always `0.00000` | BUG |
| TotalVentaNeta | OK | OK |
| TotalDesgloseImpuesto | NOT IMPLEMENTED | MISSING |
| TotalImpuesto | OK | OK |
| **TotalImpAsumEmisorFabrica** | NOT IMPLEMENTED | MISSING (NEW v4.4) |
| TotalIVADevuelto | NOT IMPLEMENTED | LOW |
| TotalOtrosCargos | NOT IMPLEMENTED | MISSING |
| MedioPago (complex, max 4) | Simple code only | PARTIAL |
| TotalComprobante | OK | OK |

### Critical Gaps
1. **TipoCambio hardcoded to 1.00000** - USD invoices will be rejected
2. **All items classified as services** - No merchandise classification
3. **No exempt/exonerated totals** - Cannot invoice exempt items
4. **TotalDescuentos always 0** - Even when lines have discounts

---

## 12. INFORMACION REFERENCIA (for NC/ND)

### TipoDocIR Codes (Nota 10) - v4.4 Updated
| Code | Description | Current |
|------|-------------|---------|
| 01 | Factura electronica | HARDCODED |
| 02 | Nota debito electronica | NOT MAPPED |
| 03 | Nota credito electronica | NOT MAPPED |
| 04 | Tiquete electronico | NOT MAPPED |
| 05 | Nota debito al tiquete | NOT MAPPED |
| 06 | Nota credito al tiquete | NOT MAPPED |
| 07 | -- (disabled in v4.4) | N/A |
| 08 | Factura electronica de compra | NOT MAPPED |
| 09 | Factura electronica de exportacion | NOT MAPPED |
| **10** | **Comprobante rechazado por Hacienda** - CHANGED v4.4 | NOT MAPPED |
| 11 | (reserved) | N/A |
| 12 | Documento emitido en contingencia | NOT MAPPED |
| 13 | Factura proforma | NOT MAPPED |
| 14 | Comprobante fisico | NOT MAPPED |
| 15 | Comprobante electronico extranjero | NOT MAPPED |
| 16 | Otros | NOT MAPPED |
| **17** | **NC a FEC** - NEW v4.4 | NOT MAPPED |
| **18** | **ND a FEC** - NEW v4.4 | NOT MAPPED |
| 99 | Otros (require OtroTipoDocRefIR) | NOT MAPPED |

### CodigoReferencia Codes (Nota 9)
| Code | Description | Current |
|------|-------------|---------|
| 01 | Anula Documento de Referencia | HARDCODED |
| 02 | Corrige texto documento de referencia | NOT MAPPED |
| 04 | Referencia a otro documento | NOT MAPPED |
| 05 | Sustituye comprobante provisional de contingencia | NOT MAPPED |
| **06** | **Devolucion de mercancia** - NEW v4.4 | NOT MAPPED |
| **07** | **Sustituye Comprobante Electronico** - NEW v4.4 | NOT MAPPED |
| **08** | **Factura Endosada** - NEW v4.4 | NOT MAPPED |
| **09** | **Nota de credito financiera** - NEW v4.4 | NOT MAPPED |
| **10** | **Nota de debito financiera** - NEW v4.4 | NOT MAPPED |
| 99 | Otros (requires CodigoReferenciaOTRO) | NOT MAPPED |

Note: Code 03 (Corrige monto) was REMOVED in v4.4.

### Gaps
1. **TipoDocIR always `01`** - Should be set based on original document type
2. **CodigoReferencia always `01`** - Should be configurable (text correction vs amount correction)
3. **Razon always `Anulacion de factura`** - Should be user-provided
4. **Original Clave NOT included** in reference XML
5. **Only one reference per document** - v4.4 allows multiple

---

## 13. MULTI-CURRENCY & EXCHANGE RATE

### v4.4 Requirement
CodigoTipoMoneda is **MANDATORY** in v4.4 (was optional in v4.3).

```xml
<CodigoTipoMoneda>
  <CodigoMoneda>USD</CodigoMoneda>
  <TipoCambio>507.25000</TipoCambio>
</CodigoTipoMoneda>
```

### Rules
- If invoice currency = CRC: TipoCambio = `1.00000`
- If invoice currency = USD: TipoCambio = BCCR sell rate (CRC per 1 USD)
- If invoice currency = EUR: TipoCambio = BCCR sell rate (CRC per 1 EUR)
- All amounts in XML stay in invoice currency
- Hacienda uses TipoCambio internally for CRC conversion
- Must use BCCR reference rate per Article 15 of IVA law

### Current Status
- Exchange rate hardcoded to `1.00000` in xml_generator.py line ~635
- Company currency is currently USD, needs to be CRC
- No automatic rate fetching

### What Needs to Happen
1. Change company currency to CRC
2. Enable USD as secondary currency
3. Implement BCCR rate provider (see section 15)
4. In xml_generator, use `invoice_currency_rate` from Odoo's built-in field
5. Formula: `tipo_cambio = 1.0 / self.invoice_currency_rate` (for foreign currency)

---

## 14. HACIENDA API SUBMISSION

### API Specification (v1)
**Base URL:** `https://api.comprobanteselectronicos.go.cr/recepcion/v1/`
**Sandbox:** `https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1/`

### Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/recepcion` | Submit document |
| GET | `/recepcion/{clave}` | Check status |
| GET | `/comprobantes` | List documents |
| GET | `/comprobantes/{clave}` | Get document details |

### POST /recepcion Request
```json
{
  "clave": "50-char string",
  "fecha": "yyyy-MM-dd'T'HH:mm:ssZ",
  "emisor": {
    "tipoIdentificacion": "01-07",
    "numeroIdentificacion": "max 12"
  },
  "receptor": {
    "tipoIdentificacion": "01-07",
    "numeroIdentificacion": "max 12"
  },
  "comprobanteXml": "Base64-encoded XAdES-EPES signed XML",
  "callbackUrl": "optional"
}
```

### Response Statuses
| Status | Meaning |
|--------|---------|
| `recibido` | Received, queued |
| `procesando` | Being processed |
| `aceptado` | Accepted |
| `rechazado` | Rejected |
| `error` | Processing error |

### Authentication
- OAuth2 Resource Owner Password flow
- Token from Keycloak IDP
- Sandbox: `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token`
- Production: `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token`

### Rate Limiting Headers
- `X-Ratelimit-Limit`, `X-Ratelimit-Remaining`, `X-Ratelimit-Reset`

### Current Status
Our `hacienda_api.py` has working submission (confirmed HTTP 202). The submission pipeline works. Main issue is the XML content being rejected due to validation errors (CodigoTarifaIVA, TipoCambio, etc.)

---

## 15. BCCR EXCHANGE RATE PROVIDER

### BCCR API Details
**Endpoint:** `https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx`
**Protocol:** SOAP (but HTTP GET works too)
**Cost:** FREE
**Auth:** Email + Token (free registration at bccr.fi.cr)

### Indicator Codes
| Code | Description |
|------|-------------|
| 317 | USD/CRC Buy rate (Compra) |
| 318 | USD/CRC Sell rate (Venta) - USE THIS |
| 3323 | MONEX average rate |

### HTTP GET Example
```
GET .../ObtenerIndicadoresEconomicosXML?Indicador=318&FechaInicio=05/02/2026&FechaFinal=05/02/2026&Nombre=GMS&SubNiveles=N&CorreoElectronico=email&Token=token
```

### Response XML
```xml
<INGC011_CAT_INDICADORECONOMIC>
  <COD_INDICADORINTERNO>318</COD_INDICADORINTERNO>
  <DES_FECHA>2026-02-05T00:00:00-06:00</DES_FECHA>
  <NUM_VALOR>507.25000000</NUM_VALOR>
</INGC011_CAT_INDICADORECONOMIC>
```

### Odoo Integration Pattern
Use Odoo's `currency_rate_live` module provider framework:
1. Register `('CR', 'bccr', '[CR] Banco Central de Costa Rica')` in `CURRENCY_PROVIDER_SELECTION`
2. Implement `_parse_bccr_data(self, available_currencies)` method on `res.company`
3. Return `{'CRC': (1.0, date), 'USD': (1/rate, date)}`
4. Cron runs daily via existing `currency_rate_live` infrastructure

### Configuration Fields Needed
- `bccr_email` - Registered email for API
- `bccr_token` - Subscription token (free)

### Date Format
**IMPORTANT:** BCCR uses `dd/mm/yyyy` (NOT ISO 8601)

---

## 16. PRIORITY MATRIX

### TIER 1: Fix NOW (Hacienda will reject)

| # | Issue | File | Impact |
|---|-------|------|--------|
| 1 | **CodigoTarifaIVA = Codigo** (wrong mapping) | xml_generator.py:~588 | ALL invoices rejected |
| 2 | **TipoCambio hardcoded to 1** | xml_generator.py:~635 | USD invoices rejected |
| 3 | **TotalDescuentos always 0** | xml_generator.py:~650 | Invoices with discounts rejected |
| 4 | **ProveedorSistemas missing** (NEW v4.4 mandatory) | xml_generator.py | ALL v4.4 invoices rejected |
| 5 | **Terminal is 5 digits, should be 3** | einvoice_document.py | Clave format wrong |
| 6 | **Email fallback info@example.com** | xml_generator.py:~370 | Silent data corruption |
| 7 | **SINPE mapped to code 04** | xml_generator.py:~465 | Wrong payment type |

### TIER 2: Fix before Go-Live (functional gaps)

| # | Issue | File | Impact |
|---|-------|------|--------|
| 8 | UnidadMedida hardcoded `Unid` | xml_generator.py | Cannot invoice by kg/hr/liter |
| 9 | IdentificacionExtranjero (type 05) wrong XML | xml_generator.py | Cannot invoice foreigners |
| 10 | New v4.4 ID type 06 (No Contribuyente) | xml_generator.py | Cannot invoice non-taxpayers |
| 11 | ActividadEconomicaReceptor not in XML | xml_generator.py | v4.4 mandatory field |
| 12 | Service vs Merchandise classification | xml_generator.py | Summary totals wrong |
| 13 | CodigoDescuento (renamed from NaturalezaDescuento) | xml_generator.py | Wrong discount field name |
| 14 | InformacionReferencia hardcoded | xml_generator.py | NC/ND reasons wrong |
| 15 | `_get_discount_nature_for_xml()` missing | account_move.py | Crashes on discounted invoices |
| 16 | PlazoCredito sums instead of max, must be days | xml_generator.py | Wrong credit terms |
| 17 | BCCR exchange rate provider | New file | No automatic rate fetching |
| 18 | Company currency change to CRC | DB/Settings | Wrong base currency |
| 19 | Consecutive number 12 digits (not 13) | einvoice_document.py | Verify sequence format |

### TIER 3: Nice to Have (not blocking)

| # | Issue | Impact |
|---|-------|--------|
| 20 | OtrosCargos section | Cannot add surcharges |
| 21 | Exoneracion support | Cannot do tax exemptions |
| 22 | Confirmation messages (codes 05-07) | Cannot accept supplier invoices |
| 23 | Sucursal/Terminal from config | Hardcoded values |
| 24 | Multiple InformacionReferencia (up to 10) | Only one reference per doc |
| 25 | CondicionVenta codes 03-15, 99 | Advanced sale conditions |
| 26 | PartidaArancelaria | Import products |
| 27 | REP (code 10) | Government clients |
| 28 | DetalleSurtido (combo breakdown) | Bundle products |
| 29 | Multiple emails (up to 4) | Currently 1 |
| 30 | TotalDesgloseImpuesto | Tax breakdown in summary |

---

## OFFICIAL REFERENCES

- [Anexos y Estructuras v4.4 (Hacienda)](https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/ANEXOS%20Y%20ESTRUCTURAS_V4.4.pdf)
- [Hacienda v4.4 Overview (March 2025)](https://www.hacienda.go.cr/docs/ComprobantesElectronicos-GeneralidadesyVersion4.4.marzo2025.pdf)
- [Resolution MH-DGT-RES-0027-2024](https://www.hacienda.go.cr/docs/DGT-R-000-2024DisposicionesTecnicasDeComprobantesElectronicosCP.pdf)
- [Hacienda API Documentation](https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/comprobantes-electronicos-api.html)
- [BCCR Web Service](https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx)
- [BCCR Exchange Rate API Documentation](https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/DocumentosMetodologiasNotasTecnicas/Webservices_de_indicadores_economicos.pdf)
- [v4.4 146 XML Adjustments Detail](https://www.facturele.com/2025/10/20/ajustes-xml-facturacion-electronica/)
- [v4.4 New Document Types](https://www.facturele.com/2025/09/19/nuevos-tipos-de-documento-version-4-4/)
- [v4.4 New Discount Codes](https://www.facturele.com/2025/06/24/nuevos-codigos-de-descuento-4-4/)
- [v4.4 IVA Classifications](https://www.facturele.com/2025/06/26/clasificacion-iva-factura-electronica/)
- [Odoo currency_rate_live Module Source](odoo/addons/currency_rate_live/)
- [odoocr/res_currency_cr_adapter (Reference)](https://github.com/odoocr/res_currency_cr_adapter)
