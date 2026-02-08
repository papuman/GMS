# Costa Rica Hacienda E-Invoice Complete Reference

> Compiled from official Hacienda documentation, public APIs, community resources, and our own testing experience.
> Last updated: 2026-02-06

---

## Table of Contents

1. [Official Documentation Portal](#1-official-documentation-portal)
2. [XSD Schemas & Technical Specs (v4.4)](#2-xsd-schemas--technical-specs-v44)
3. [REST API Endpoints](#3-rest-api-endpoints)
4. [OAuth2 Authentication (IDP)](#4-oauth2-authentication-idp)
5. [Public APIs (No Auth Required)](#5-public-apis-no-auth-required)
6. [Clave Structure (50 digits)](#6-clave-structure-50-digits)
7. [Consecutive Number (20 digits)](#7-consecutive-number-20-digits)
8. [CABYS Codes (Product/Service Catalog)](#8-cabys-codes-productservice-catalog)
9. [Activity Codes (CIIU Classification)](#9-activity-codes-ciiu-classification)
10. [Tax Rate Codes (CodigoTarifaIVA)](#10-tax-rate-codes-codigotarifaiva)
11. [Identification Types](#11-identification-types)
12. [Payment Method Codes](#12-payment-method-codes)
13. [Sale Condition Codes](#13-sale-condition-codes)
14. [Document Types](#14-document-types)
15. [Location Codes (Province/Canton/District)](#15-location-codes-provincecantonddistrict)
16. [Digital Certificate & XML Signing](#16-digital-certificate--xml-signing)
17. [Validation Levels & Common Errors](#17-validation-levels--common-errors)
18. [Our Errors & Lessons Learned](#18-our-errors--lessons-learned)
19. [Developer Portal & Sandbox](#19-developer-portal--sandbox)
20. [v4.4 Timeline & Key Changes](#20-v44-timeline--key-changes)
21. [Community Resources & GitHub](#21-community-resources--github)

---

## 1. Official Documentation Portal

| Resource | URL |
|----------|-----|
| **ATV Anexos y Estructuras (ALL versions)** | https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/frmAnexosyEstructuras.aspx |
| **v4.4 Anexos y Estructuras PDF** | https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/ANEXOS%20Y%20ESTRUCTURAS_V4.4.pdf |
| **v4.4 Resolution (MH-DGT-RES-0027-2024)** | https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/Resolución_General_sobre_disposiciones_técnicas_comprobantes_electrónicos_para_efectos_tributarios.pdf |
| **v4.4 Reglamento** | https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/REGLAMENTO_DE_COMPROBANTES_ELECTRONICOS.pdf |
| **v4.4 API Documentation** | https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/comprobantes-electronicos-api.html |
| **v4.4 Overview (March 2025)** | https://www.hacienda.go.cr/docs/ComprobantesElectronicos-GeneralidadesyVersion4.4.marzo2025.pdf |
| **Resolution DGT-R-48-2016 (original)** | https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2016/v4/Resolucion%20Comprobantes%20Electronicos%20%20DGT-R-48-2016.pdf |
| **DGT-R-000-2024 (v4.4 draft resolution)** | https://www.hacienda.go.cr/docs/DGT-R-000-2024DisposicionesTecnicasDeComprobantesElectronicosCP.pdf |
| **Factura vs Tiquete guide** | https://www.hacienda.go.cr/docs/Diferenciaentreunafacturayuntiqueteelectronico.pdf |
| **What you need to issue CE** | https://www.hacienda.go.cr/docs/QuedebotenerpresenteparaemitiryentregarunCEJun2024.pdf |
| **Important considerations for CE** | https://www.hacienda.go.cr/docs/CONSIDERACIONESIMPORTANTESENLAEMISIONDECOMPROBANTESELECTRONICOS004.pdf |
| **Guide for querying emitted CE** | https://www.hacienda.go.cr/docs/GuiaparaConsultasdecomprobantesemitidos-v01.pdf |
| **SCIJ Legal Text (Reglamento)** | https://pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=103276&nValor3=143300&strTipM=TC |

---

## 2. XSD Schemas & Technical Specs (v4.4)

All files at base URL: `https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/`

| Document | XSD | DOC |
|----------|-----|-----|
| Factura Electrónica | `FacturaElectronica_V4.4.xsd` | `FacturaElectronica_V4.4.doc` |
| Tiquete Electrónico | `TiqueteElectronico_V4.4.xsd` | `TiqueteElectronico_V4.4.doc` |
| Nota Crédito Electrónica | `NotaCreditoElectronica_V4.4.xsd` | `NotaCreditoElectronica_V4.4.doc` |
| Nota Débito Electrónica | `NotaDebitoElectronica_V4.4.xsd` | `NotaDebitoElectronica_V4.4.doc` |
| Factura Electrónica Compra | `FacturaElectronicaCompra_V4.4.xsd` | `FacturaElectronicaCompra_V4.4.doc` |
| Factura Electrónica Exportación | `FacturaElectronicaExportacion_V4.4.xsd` | `FacturaElectronicaExportacion_V4.4.doc` |
| Recibo Electrónico Pago (NEW) | `ReciboElectronicoPago_V4.4.xsd` | `ReciboElectronicoPago_V4.4.doc` |
| Mensaje Hacienda | `MensajeHacienda_V4.4.xsd` | `MensajeHacienda_V4.4.doc` |
| Mensaje Receptor | `MensajeReceptor_V4.4.xsd` | `MensajeReceptor_V4.4.doc` |

Other v4.4 files:
- IdP Guide: `Guia_IdP.pdf`
- Location codes: `Codificacionubicacion_V4.4.rar`
- Currency codes: `Codigodemoneda_V4.4.pdf`
- Pharmaceutical codes: `Nota_9_Codigo_Forma_Farmaceutica.xlsx`
- Dropbox Paper API reference: https://paper.dropbox.com/doc/API-Ministerio-de-Hacienda-znrOU6bGjTHcXjo8oUmBj

### XML Namespaces (v4.4)

```
https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica
https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/tiqueteElectronico
https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaCreditoElectronica
https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaDebitoElectronica
```

---

## 3. REST API Endpoints

### Base URLs

| Environment | Base URL |
|-------------|----------|
| **Production** | `https://api.comprobanteselectronicos.go.cr/recepcion/v1/` |
| **Sandbox** | `https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/` |

> **NOTE:** Our code had `https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1` (subdomain-based). The official docs show path-based sandbox: `recepcion-sandbox`. Both may work, but the canonical URL is path-based.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/recepcion` | Submit signed XML (Base64). Returns `201` with `Location` header. |
| `GET` | `/recepcion/{clave}` | Check status. Returns `ind-estado`: `recibido`, `procesando`, `aceptado`, `rechazado`, `error`. |
| `GET` | `/comprobantes` | List all vouchers (paginated). Query params: `offset`, `limit` (max 50), `emisor`, `receptor`. |
| `GET` | `/comprobantes/{clave}` | Get specific voucher. |

### POST /recepcion Request Body

```json
{
  "clave": "50-digit key (string, max 50)",
  "fecha": "RFC 3339: yyyy-MM-dd'T'HH:mm:ssZ",
  "emisor": {
    "tipoIdentificacion": "01-06 (string, max 2)",
    "numeroIdentificacion": "string, max 12"
  },
  "receptor": {
    "tipoIdentificacion": "string, max 2",
    "numeroIdentificacion": "string, max 12"
  },
  "callbackUrl": "optional, HTTP/HTTPS POST callback",
  "consecutivoReceptor": "optional, for receiver confirmation",
  "comprobanteXml": "required, Base64-encoded UTF-8 XAdES-EPES signed XML"
}
```

### Rate Limiting

All responses include:
- `X-Ratelimit-Limit` — Requests allowed
- `X-Ratelimit-Remaining` — Requests remaining
- `X-Ratelimit-Reset` — UTC Epoch seconds until reset

---

## 4. OAuth2 Authentication (IDP)

### Token Endpoints

| Environment | URL | Client ID |
|-------------|-----|-----------|
| **Sandbox** | `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token` | `api-stag` |
| **Production** | `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token` | `api-prod` |

### Logout/Revocation

| Environment | URL |
|-------------|-----|
| Sandbox | `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/logout` |
| Production | `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token/logout` |

### Token Request

```
POST {token_url}
Content-Type: application/x-www-form-urlencoded

grant_type=password
client_id=api-stag  (or api-prod)
client_secret=       (always blank)
username={ATV_USERNAME}
password={ATV_PASSWORD}
scope=               (always blank)
```

Response: JSON with `access_token`, `refresh_token`, `expires_in`, etc.

### IdP Guide
https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/Guia_IdP.pdf

---

## 5. Public APIs (No Auth Required)

All at `https://api.hacienda.go.cr/`

| Endpoint | Description |
|----------|-------------|
| `GET /fe/ae?identificacion={cedula}` | Taxpayer lookup: name, activities, tax status, regime |
| `GET /fe/cabys?q={search}&top={limit}` | CABYS code search (min 3 chars) |
| `GET /fe/cabys?codigo={13-digit}` | CABYS lookup by exact code |
| `GET /fe/cabys/test` | Interactive CABYS test interface |
| `GET /fe/ex?autorizacion={code}` | Tax exemption lookup (format: `AL-XXXXXXXX-XX`) |
| `GET /fe/agropecuario?identificacion={cedula}` | Agricultural producer data (MAG) |
| `GET /fe/pesca?identificacion={cedula}` | Fishing industry data (INCOPESCA) |
| `GET /indicadores/tc/dolar` | Current USD/CRC exchange rate |
| `GET /indicadores/tc/dolar/historico?d={from}&h={to}` | Historical USD rates |
| `GET /indicadores/tc/euro` | Current EUR rates |
| `GET /indicadores/tc` | All exchange rates |

**API Docs portal:** https://api.hacienda.go.cr/docs/
**Support email:** facturati@hacienda.go.cr

### Rate Limits (Public APIs)

- **Burst:** 20 requests/second over 5 seconds (max 100 in 5 seconds)
- **Sustained:** 10 requests/second over 120 seconds
- **Penalty:** Both thresholds trigger a **10-minute IP block**
- **Error:** `HTTP 429 Too Many Requests`

---

## 6. Clave Structure (50 digits)

Per Resolution DGT-R-48-2016, Article 5:

```
CCC DD MM YY CCCCCCCCCCCC CCCCCCCCCCCCCCCCCCCC S CCCCCCCC
506 day mo yr cedula(12)   consecutive(20)      sit security(8)
 3   2  2  2    12              20               1    8    = 50
```

| Position | Length | Field | Description |
|----------|--------|-------|-------------|
| 1-3 | 3 | Country | Always `506` (Costa Rica) |
| 4-5 | 2 | Day | DD |
| 6-7 | 2 | Month | MM |
| 8-9 | 2 | Year | YY |
| 10-21 | 12 | Cedula | Issuer ID, zero-padded left |
| 22-41 | 20 | Consecutive | See section 7 |
| 42 | 1 | Situación | `1`=Normal, `2`=Contingencia, `3`=Sin internet |
| 43-50 | 8 | Security code | 8 random digits |

**CRITICAL:** Position 42 is the "situación" code, NOT a check digit! Our original code was computing a check digit here, which caused error -15.

---

## 7. Consecutive Number (20 digits)

Per Resolution DGT-R-48-2016, Article 4:

```
SSS TTTTT DD NNNNNNNNNN
suc  term  dt  sequence
 3    5     2     10     = 20
```

| Position | Length | Field | Description |
|----------|--------|-------|-------------|
| 1-3 | 3 | Sucursal | Branch number (001 = main) |
| 4-8 | 5 | Terminal | Terminal/POS number (00001 = main) |
| 9-10 | 2 | Doc Type | `01`=FE, `02`=ND, `03`=NC, `04`=TE |
| 11-20 | 10 | Sequence | Sequential number, zero-padded |

**CRITICAL:** Terminal is 5 digits, not 3! Our original code used 3 digits, causing error -78.

---

## 8. CABYS Codes (Product/Service Catalog)

CABYS = Catálogo de Bienes y Servicios. 13-digit hierarchical codes covering 20,000+ items.

| Resource | URL |
|----------|-----|
| **BCCR CABYS Landing Page** | https://www.bccr.fi.cr/indicadores-economicos/cat%C3%A1logo-de-bienes-y-servicios |
| **Full Excel Catalog** | https://www.bccr.fi.cr/indicadores-economicos/cabys/Catalogo-de-bienes-servicios.xlsx |
| **FAQ PDF** | https://www.bccr.fi.cr/indicadores-economicos/cabys/Preguntas-frecuentes-CABYS.pdf |
| **API Search** | `https://api.hacienda.go.cr/fe/cabys?q={term}&top={limit}` |
| **API Lookup** | `https://api.hacienda.go.cr/fe/cabys?codigo={13-digit}` |
| **Test Interface** | https://api.hacienda.go.cr/fe/cabys/test |
| **UCR Interactive Search** | https://bite.ucr.ac.cr/cabys/list |
| **CABYS 2025 Update Notice** | https://www.hacienda.go.cr/docs/CP-BCCR-015-2025.pdf |
| **Community guide** | https://siemprealdia.co/costa-rica/impuestos/codigos-cabys-costa-rica/ |

### Key CABYS Codes for GMS (Gym)

| Code | Description | IVA |
|------|-------------|-----|
| `9652000009900` | Sports/recreation facility services | 13% |

**CRITICAL:** Old fallback `8611001000000` is INVALID. POS lines don't have `l10n_cr_product_code`, must read from `product_template`.

---

## 9. Activity Codes (CIIU Classification)

| Resource | URL |
|----------|-----|
| **Hacienda Activity Codes** | https://www.hacienda.go.cr/ClasificacionActividadesEconomicas.html |
| **CIIU3→CIIU4 transition guide** | https://gosocket.net/centro-de-recursos/el-ministerio-de-hacienda-informa-nuevos-codigos-de-actividad-economica-ciiu-4/ |
| **v4.4 receiver activity requirement** | https://www.facturele.com/2025/07/22/codigo-de-actividad-economica-cr-4-4/ |
| **Lookup via public API** | `https://api.hacienda.go.cr/fe/ae?identificacion={cedula}` |

### Key Rules

- **Format:** 6 digits, padded with **trailing zeros** (not leading). `9311` → `931100`
- **Must match exactly** what's registered in Hacienda's RUT for the taxpayer
- **CIIU3 vs CIIU4:** Sandbox may still use CIIU3 codes. CIIU4 mandatory from Oct 6, 2025 (TRIBU-CR)
- **Receiver activity code:** NEW mandatory field in v4.4 for FE (Factura Electrónica)
- **Check registered codes:** Use API `https://api.hacienda.go.cr/fe/ae?identificacion={cedula}` — look at `actividades[].codigo`

**CRITICAL:** Our code originally used `zfill(6)` which pad with LEADING zeros (`9311` → `009311`). Fixed to `ljust(6, '0')` for trailing zeros. But the real lesson is: always use the EXACT code from Hacienda's API response.

---

## 10. Tax Rate Codes (CodigoTarifaIVA)

| Code | Rate | Description |
|------|------|-------------|
| `01` | 0% | Tarifa 0% (Exento) |
| `02` | 1% | Tarifa reducida 1% |
| `03` | 2% | Tarifa reducida 2% |
| `04` | 4% | Tarifa reducida 4% |
| `05` | 0% | Transitorio 0% |
| `06` | 4% | Transitorio 4% |
| `07` | 8% | Transitorio 8% |
| `08` | 13% | Tarifa general |
| `11` | 0% | 0% sin derecho a crédito (NEW in v4.4) |

**CRITICAL:** The code MUST match the actual rate. If rate is 13%, code must be `08`. If rate is 15% (doesn't exist!), Hacienda rejects with error -505.

---

## 11. Identification Types

| Code | Type | Length | Description |
|------|------|--------|-------------|
| `01` | Cédula Física | 9 digits | Costa Rican national ID |
| `02` | Cédula Jurídica | 10 digits (starts with 3) | Corporate/legal entity ID |
| `03` | DIMEX | 11-12 digits | Foreign resident ID |
| `04` | NITE | 10 digits | Special tax ID |
| `05` | Extranjero No Domiciliado | Up to 20 chars | Non-resident foreigner (NEW v4.4) |
| `06` | No Contribuyente | Up to 20 chars | Non-taxpayer (NEW v4.4) |

---

## 12. Payment Method Codes

| Code | Description |
|------|-------------|
| `01` | Efectivo (Cash) |
| `02` | Tarjeta (Credit/Debit Card) |
| `03` | Cheque |
| `04` | Transferencia / Depósito bancario |
| `05` | Recaudado por terceros |
| `06` | SINPE Móvil (NEW v4.4) |
| `07` | Plataformas digitales (NEW v4.4) |

**Source:** https://www.facturele.com/2025/05/23/nuevos-medios-de-pago-version-4-4/

---

## 13. Sale Condition Codes

| Code | Description |
|------|-------------|
| `01` | Contado (Cash) — MUST include payment method |
| `02` | Crédito — MUST specify plazo (term) in days > 0 |
| `03` | Consignación |
| `04` | Apartado |
| `05` | Arrendamiento con opción de compra |
| `06` | Arrendamiento en función financiera |
| `07`-`13` | Other conditions |
| `14` | Arrendamiento Operativo (NEW v4.4) |
| `15` | Arrendamiento Financiero (NEW v4.4) |
| `99` | Otros |

**CRITICAL:** Contado without payment method = REJECTED. Crédito with plazo=0 = REJECTED.

**Source:** https://www.facturele.com/2025/05/23/condiciones-de-venta-facturacion-e-cr/

---

## 14. Document Types

| Code | Type | Description |
|------|------|-------------|
| `01` | FE | Factura Electrónica (requires receiver cédula) |
| `02` | ND | Nota de Débito Electrónica |
| `03` | NC | Nota de Crédito Electrónica |
| `04` | TE | Tiquete Electrónico (no receiver cédula needed) |
| `05` | -- | Confirmación de Aceptación |
| `06` | -- | Confirmación de Aceptación Parcial |
| `07` | -- | Confirmación de Rechazo |
| `08` | -- | Depósito de garantía (NEW v4.4) |
| `09` | -- | Multas/Penalizaciones (NEW v4.4) |
| `10` | -- | Intereses moratorios (NEW v4.4) |

FE vs TE: Use FE when receiver has a cédula (for tax deduction). Use TE for anonymous sales (walk-in gym customers without FE request).

**Source:** https://www.facturele.com/2025/09/19/nuevos-tipos-de-documento-version-4-4/

---

## 15. Location Codes (Province/Canton/District)

| Resource | URL |
|----------|-----|
| **Official v4.4 codes (RAR)** | https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/Codificacionubicacion_V4.4.rar |
| **v4.1 codes (readable PDF)** | https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2016/v4.1/Codificacion,canton,provincia,distritoybarrio.pdf |
| **Community JSON API** | https://ubicaciones.paginasweb.cr/ |
| **API endpoints:** | `/provincias.json`, `/provincia/:id/cantones.json`, `/provincia/:id/canton/:id/distritos.json` |
| **INEC Official Codes** | https://inec.cr/wwwisis/documentos/Clasificacion_Industrial/Codigos_Territorial_CR_07.pdf |
| **GitHub CR Division Data** | https://github.com/bernethe/cr-division-politica |

### Province Codes

| Code | Province |
|------|----------|
| 1 | San José |
| 2 | Alajuela |
| 3 | Cartago |
| 4 | Heredia |
| 5 | Guanacaste |
| 6 | Puntarenas |
| 7 | Limón |

---

## 16. Digital Certificate & XML Signing

| Resource | URL |
|----------|-----|
| **IdP Guide** | https://atv.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/Guia_IdP.pdf |
| **BCCR Firma Digital** | https://www.bccr.fi.cr/firma-digital |
| **Mi Firma Digital** | https://www.mifirmadigital.go.cr/ |
| **Signing guide** | https://siemprealdia.co/costa-rica/impuestos/firma-digital-en-la-factura-electronica/ |
| **Creating .p12 guide** | https://fran.cr/como-crear-un-p12-de-persona-juridica-emitido-por-el-bccr-sinpe-para-firmar-comprobantes-electronicos-de-costa-rica/ |

### Technical Requirements

- **Certificate Authority:** BCCR CA SINPE
- **Certificate format:** `.p12` (PKCS#12) with private key + cert chain
- **Signing standard:** **XAdES-EPES** (XML Advanced Electronic Signatures)
- **Hash algorithm:** SHA-256
- **Key size:** RSA 2048-bit
- **Hacienda responses are signed with:** **XAdES-XL**

---

## 17. Validation Levels & Common Errors

### Three-Level Validation

1. **Nivel 1 (Structure):** Checks XML has all required fields. Reject → rejection message sent.
2. **Nivel 2 (Format):** Checks fields have correct formats, lengths, data types. Reject → rejection message sent.
3. **Nivel 3 (Coherence):** Cross-references against Hacienda DB (RUT, activity codes, CABYS catalog, etc.). Reject → rejection message sent.

### Common Rejection Reasons

| Category | Description |
|----------|-------------|
| Invalid activity code | Code doesn't match what's registered in RUT |
| Invalid CABYS code | 13-digit code not found in CABYS catalog |
| Invalid clave structure | Not 50 digits, wrong format |
| Invalid consecutive | Wrong length or format for the 20-digit consecutive |
| Tax rate mismatch | CodigoTarifaIVA doesn't match the actual rate |
| Location mismatch | Province/canton/district codes inconsistent |
| Missing payment method | Contado without MedioPago |
| Missing receiver activity | v4.4: FE requires receiver's economic activity |
| Missing software provider | v4.4: requires "Proveedor de Sistemas" identification |

### January 2026 Mass Rejection Event

On January 6, 2026, Hacienda activated a new validation filter for activity codes. **30%+ of invoices were rejected** in a single day. **50% of companies** had not updated their activity codes to CIIU4.

**Source:** https://www.monumental.co.cr/2026/01/08/advierten-por-rechazo-masivo-de-facturas-ante-nuevo-filtro-de-hacienda/

---

## 18. Our Errors & Lessons Learned

These are the 7 Hacienda rejection errors we encountered and fixed during development:

### Error -15: Invalid Clave Structure
- **Cause:** Position 42 had a computed check digit instead of the "situación" code
- **Fix:** Removed `_calculate_check_digit()`, added `situacion = '1'` (Normal)
- **Lesson:** There is NO check digit in the clave. Position 42 is always 1, 2, or 3.

### Error -37: Province/Canton/District Mismatch
- **Cause:** Initially thought to be location data, but was actually masked by other errors
- **Fix:** Once activity code was correct, this error disappeared
- **Lesson:** Fix other errors first; some errors cascade

### Error -78: Invalid Consecutive Number
- **Cause:** Terminal field was 3 digits instead of 5
- **Fix:** Changed from `str(terminal).zfill(3)` to `str(terminal).zfill(5)`
- **Lesson:** Consecutive = 3 (sucursal) + **5** (terminal) + 2 (doc type) + 10 (sequence) = 20

### Error -400: Invalid CABYS Code
- **Cause:** Default CABYS `8611001000000` doesn't exist in catalog
- **Fix:** Changed to `9652000009900` (Sports/recreation facility services). Also read from `product_template` first.
- **Lesson:** Always verify CABYS codes against the official catalog API

### Error -408: Invalid Activity Code
- **Cause 1:** `zfill(6)` padded with leading zeros: `9311` → `009311` (wrong)
- **Cause 2:** Even `ljust(6, '0')` → `931100` was wrong — code wasn't registered
- **Cause 3:** CIIU4 code `469000` also not registered in sandbox
- **Fix:** Used CIIU3 code `513910` from Hacienda API response (`ciiu3` field)
- **Lesson:** ALWAYS use the exact code from `https://api.hacienda.go.cr/fe/ae?identificacion={cedula}`. Don't guess or transform.

### Error -487: Missing TotalDesgloseImpuesto
- **Cause:** Tax breakdown element was missing from XML
- **Fix:** Added `TotalDesgloseImpuesto` section in XML generator
- **Lesson:** Read the XSD schema carefully for required elements

### Error -505: Tax Rate Mismatch
- **Cause:** Product had 15% tax rate, but code `08` requires exactly 13%
- **Fix:** Changed product tax to IVA 13%. Added fallback logic to map to closest valid rate.
- **Lesson:** Valid IVA rates are: 0%, 1%, 2%, 4%, 8%, 13%. Nothing else.

---

## 19. Developer Portal & Sandbox

| Resource | URL |
|----------|-----|
| **ATV Login Portal** | https://atv.hacienda.go.cr/ATV/login.aspx |
| **ATV Invoice Lookup** | https://atv.hacienda.go.cr/ATV/frmConsultaFactura.aspx |
| **ATV Tax Status Check** | https://atv.hacienda.go.cr/ATV/frmConsultaSituTributaria.aspx |
| **TRIBU-CR Portal** | https://www.hacienda.go.cr/TRIBU-CR.html |
| **TRIBU-CR FAQ** | https://www.hacienda.go.cr/docs/dPreguntasYRespuestasDeTRIBU-CR.pdf |
| **Postman Collection** | https://documenter.getpostman.com/view/9097384/SW7gVR3D |
| **API Status Monitor** | https://apis.gometa.org/status/ |
| **XML Validator** | https://apis.gometa.org/validar/ |

---

## 20. v4.4 Timeline & Key Changes

### Timeline

| Date | Event |
|------|-------|
| Nov 19, 2024 | Resolution MH-DGT-RES-0027-2024 published |
| Apr 1, 2025 | Voluntary v4.4 usage begins; CABYS 2025 transition begins |
| Jun 1, 2025 | Original mandatory date (extended) |
| Sep 1, 2025 | v4.4 mandatory for ALL taxpayers (MH-DGT-RES-0001-2025) |
| Oct 6, 2025 | CIIU4 activity codes mandatory (TRIBU-CR activated) |
| Jan 6, 2026 | Activity code validation filter activated (30%+ rejections) |

### Key v4.4 Changes (146+ XML changes)

- **New document type:** ReciboElectronicoPago (Electronic Payment Receipt)
- **New field:** "Proveedor de Sistemas" (software provider ID) — MANDATORY
- **New field:** Receiver economic activity code — MANDATORY for FE
- **New ID types:** `05` (non-resident foreigner), `06` (non-taxpayer)
- **New payment codes:** `06` (SINPE Móvil), `07` (digital platforms)
- **New sale conditions:** `14` (operating lease), `15` (financial lease)
- **New tax code:** `11` (0% without credit rights)
- **New document types:** `08`, `09`, `10` (guarantees, penalties, late interest)
- **`numeroIdentificacion` expanded to 20 chars** (for passport numbers)
- **QR code:** Requirement suspended by Hacienda
- **71+ new fields total**
- **After Sep 1, 2025:** v4.3 only for NC/ND on pre-deadline documents

### Sources for v4.4 Changes

| Resource | URL |
|----------|-----|
| **Facturele 146 XML changes** | https://www.facturele.com/2025/10/20/ajustes-xml-facturacion-electronica/ |
| **Facturele v4.4 portal** | https://facturacion-electronica-4-4.facturelo.com/ |
| **Facturele system ID required** | https://www.facturele.com/2025/09/02/identificacion-de-sistema-requerida/ |
| **Facturele QR suspension** | https://www.facturele.com/2025/10/24/suspension-del-codigo-qr-factura-4-4/ |
| **Gosocket v4.4 guide** | https://gosocket.net/centro-de-recursos/prepare-su-empresa-para-la-version-4-4-del-anexo-de-comprobantes-electronicos-en-costa-rica/ |
| **Deloitte analysis** | https://www.deloitte.com/latam/es/services/tax/perspectives/cr-comprobante-electronico-4-4-cinco-cambios-relevantes.html |
| **Siemprealdia novelties** | https://siemprealdia.co/costa-rica/impuestos/novedades-en-facturacion-electronica/ |
| **Facturele discount codes** | https://www.facturele.com/2025/06/24/nuevos-codigos-de-descuento-4-4/ |
| **Facturele exonerations** | https://www.facturele.com/2025/07/08/exoneraciones-factura-electronica-4-4/ |

---

## 21. Community Resources & GitHub

### GitHub Repositories

| Repository | Language | Description |
|-----------|----------|-------------|
| [CRLibre/API_Hacienda](https://github.com/CRLibre/API_Hacienda) | PHP | Most comprehensive open-source Hacienda API wrapper |
| [CRLibre/API_Hacienda Wiki](https://github.com/CRLibre/API_Hacienda/wiki) | — | 17+ pages: signing, tokens, keys, submission workflow |
| [apokalipto/facturacr](https://github.com/apokalipto/facturacr) | Ruby | Full e-invoice library with native XAdES-EPES signing |
| [odoocr/l10n_cr](https://github.com/odoocr/l10n_cr) | Python | Odoo CR localization (migrating, not fully functional) |
| [odoocr organization](https://github.com/odoocr) | — | Multiple CR localization modules |
| [royrojas/FacturaElectronicaCR](https://github.com/royrojas/FacturaElectronicaCR) | VB.NET/C# | .NET implementation |
| [dbadillasanchez/factura-electronica-API](https://github.com/dbadillasanchez/factura-electronica-API-Ministerio-de-Hacienda-CR) | PHP | Raw API consumption examples |

### GitHub Topics

| Topic | URL |
|-------|-----|
| facturacion-electronica-costa-rica | https://github.com/topics/facturacion-electronica-costa-rica |
| ministerio-de-hacienda-costa-rica | https://github.com/topics/ministerio-de-hacienda-costa-rica |
| factura-electronica | https://github.com/topics/factura-electronica |

### Community Websites

| Site | URL | Focus |
|------|-----|-------|
| **Facturele.com** | https://www.facturele.com/ | Ongoing v4.4 coverage, detailed articles |
| **Siemprealdia.co** | https://siemprealdia.co/costa-rica/impuestos/ | Tax and e-invoicing changes |
| **Gosocket** | https://gosocket.net/centro-de-recursos/ | Enterprise guides, deadline tracking |
| **royrojas.com** | https://www.royrojas.com/ | XML examples, technical guides |
| **ComprobanteselectronicosCR** | https://www.comprobanteselectronicoscr.com/ | General info portal |
| **IntegrAFactura** | https://www.integrafactura.com/ | Web API integration system |
| **APIs GoMeta** | https://apis.gometa.org/ | Status monitoring, validation, utilities |
| **Sovos** | https://sovos.com/es/iva/reglas-fiscales/factura-electronica-costa-rica/ | Regulatory tracking |
| **EDICOM** | https://edicom.co/blog/como-es-la-factura-electronica-en-costa-rica | Comprehensive overview |

### Professional Analyses

| Source | URL |
|--------|-----|
| **Deloitte v4.4 Analysis** | https://www.deloitte.com/latam/es/services/tax/perspectives/cr-comprobante-electronico-4-4-cinco-cambios-relevantes.html |
| **BDO TRIBU-CR Analysis** | https://www.bdo.cr/es-cr/publicaciones/2024/lanzamiento-del-sistema-tribu-cr-transformando-la-gestion-tributaria-en-costa-rica |

