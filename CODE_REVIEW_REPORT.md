# GMS Comprehensive Code Review Report (YOLO)

This report consolidates all findings identified across `l10n_cr_einvoice` and `payment_tilopay`. No code changes were made.

1. Severity: Critical  
File:line: `payment_tilopay/models/__init__.py:3-4` + `payment_tilopay/views/payment_transaction_views.xml:12-24`  
Issue: Views reference TiloPay fields defined in `tilopay_payment_transaction.py`, but that model file is never imported.  
Impact: Module install/view rendering fails due to missing fields.  
Fix: Import `tilopay_payment_transaction` in `payment_tilopay/models/__init__.py`.

2. Severity: Critical  
File:line: `payment_tilopay/models/account_move.py:165-167`  
Issue: Calls `transaction._tilopay_create_payment()` but that method exists only in the unimported `tilopay_payment_transaction.py`.  
Impact: Online payment initiation crashes at runtime.  
Fix: Import the model or move `_tilopay_create_payment()` into the active transaction extension.

3. Severity: High  
File:line: `l10n_cr_einvoice/models/einvoice_document.py:413-419`  
Issue: Validation override branch raises a `UserError`, blocking generation even when override is active.  
Impact: Override cannot be used.  
Fix: Remove the erroneous `raise UserError(...)` in the override branch.

4. Severity: High  
File:line: `l10n_cr_einvoice/models/einvoice_document.py:554-562`  
Issue: `_validate_before_submission()` requires partner/VAT for all document types, including TE.  
Impact: TE submissions blocked or forced to use fake VAT.  
Fix: Make partner/VAT checks conditional on FE (or when receiver is required).

5. Severity: High  
File:line: `l10n_cr_einvoice/models/pos_order.py:84-94` + `l10n_cr_einvoice/static/src/js/pos_einvoice.js:90-95`  
Issue: POS sends `einvoice_type` but server ignores it; FE/TE decided by VAT only.  
Impact: Cashier selection ignored; TE may become FE and fail.  
Fix: Persist `einvoice_type` in `_order_fields()` and use it in `_generate_cr_einvoice()`.

6. Severity: High  
File:line: `l10n_cr_einvoice/models/pos_order.py:160-165`  
Issue: Offline mode sets `l10n_cr_offline_queue = True` but does not create a queue entry.  
Impact: Offline invoices never sync.  
Fix: Create `l10n_cr.pos.offline.queue` entry when offline mode is enabled.

7. Severity: High  
File:line: `l10n_cr_einvoice/models/pos_offline_queue.py:174-178`  
Issue: `_perform_sync()` signs XML when document is still `draft`.  
Impact: Offline sync fails immediately; queue never clears.  
Fix: If `draft`, run `action_generate_xml()` before `action_sign_xml()`.

8. Severity: High  
File:line: `l10n_cr_einvoice/models/hacienda_api.py:231-236`  
Issue: Submission timestamp uses `datetime.now()` with a fixed `-06:00` offset.  
Impact: Wrong timestamps if server timezone differs; potential Hacienda rejections.  
Fix: Use timezone-aware CR timestamp.

9. Severity: High  
File:line: `l10n_cr_einvoice/models/xsd_validator.py:88-100`  
Issue: XSD validation failures are treated as success.  
Impact: Invalid XML can be signed and submitted.  
Fix: Fail hard in production when XSD validation fails.

10. Severity: Medium  
File:line: `l10n_cr_einvoice/models/xsd_validator.py:165-189`  
Issue: Required element checks use unreliable namespace handling.  
Impact: Missing elements can pass validation.  
Fix: Use explicit namespace prefixes in XPath queries.

11. Severity: Medium  
File:line: `l10n_cr_einvoice/models/pos_order.py:96-104`  
Issue: E-invoice generation only triggers on `create()` when `state == 'paid'`.  
Impact: Orders paid later never generate e-invoices.  
Fix: Trigger on state transition to `paid`/`done` in `write()` or a post-processing hook.

12. Severity: Medium  
File:line: `l10n_cr_einvoice/models/xml_generator.py:476-524`  
Issue: POS payment method uses only the first payment line.  
Impact: Split payments are misreported; XML `MedioPago` incorrect.  
Fix: Emit multiple `MedioPago` entries or aggregate correctly.

13. Severity: Medium  
File:line: `l10n_cr_einvoice/models/xml_generator.py:1001-1003`  
Issue: `_add_informacion_referencia()` assumes `original_move.invoice_date` exists.  
Impact: Credit/debit note XML generation can crash if missing.  
Fix: Validate `invoice_date` and raise a clear error if absent.

14. Severity: Medium  
File:line: `l10n_cr_einvoice/models/hacienda_api.py:39-63` + `l10n_cr_einvoice/models/einvoice_document.py:628-638`  
Issue: API client uses `env.company` without forcing document company context.  
Impact: Multi-company submissions can use wrong credentials/environment.  
Fix: Call API with `with_company(self.company_id)`.

15. Severity: Medium  
File:line: `l10n_cr_einvoice/models/einvoice_document.py:369-373`  
Issue: NOWAIT row lock errors are not handled gracefully.  
Impact: Random lock exceptions surfaced to users.  
Fix: Catch lock errors and show a user-friendly “try again” message.

16. Severity: Medium  
File:line: `l10n_cr_einvoice/models/xml_generator.py:1203-1239` + `l10n_cr_einvoice/models/certificate_manager.py:40-80`  
Issue: Validation uses env-specific certificate fields, while signing uses `l10n_cr_active_*` fields.  
Impact: Validation and signing can use different certificates.  
Fix: Align validation and signing to the same fields.

17. Severity: Medium  
File:line: `l10n_cr_einvoice/models/pos_order.py:126-131`  
Issue: TE still requires a partner (default partner mandatory).  
Impact: True anonymous TE cannot be issued.  
Fix: Allow TE without partner or enforce a “Final Consumer” partner.

18. Severity: Medium  
File:line: `l10n_cr_einvoice/static/src/js/pos_einvoice.js:108-127`  
Issue: `useState()` is initialized only once; does not resync when order/partner changes.  
Impact: FE/TE UI and validation become stale when switching orders.  
Fix: Re-sync state on order change and partner change.

19. Severity: Medium  
File:line: `l10n_cr_einvoice/static/src/js/pos_einvoice.js:138-170`  
Issue: CIIU mandatory date is hard-coded in POS JS while backend uses configurable parameter.  
Impact: Frontend/backed can disagree on enforcement.  
Fix: Load config param into POS session data.

20. Severity: Medium  
File:line: `l10n_cr_einvoice/models/pos_order.py:200-210`  
Issue: Receipt feedback treats `signed` as “sent to Hacienda” and ignores offline queue state.  
Impact: POS UI can falsely report success.  
Fix: Add explicit “queued/offline” states in feedback.

21. Severity: Medium  
File:line: `l10n_cr_einvoice/models/cedula_cache.py:372-415`  
Issue: Cache refresh job is unimplemented (`_enqueue_refresh_job` is TODO).  
Impact: Cache never refreshes; stale data persists.  
Fix: Implement background refresh or remove refresh-zone logic.

22. Severity: Medium  
File:line: `l10n_cr_einvoice/models/cedula_lookup_service.py:160-178`  
Issue: GoMeta fallback is always used without configuration.  
Impact: External dependency and privacy/compliance risk.  
Fix: Add config switch and user disclosure.

23. Severity: Medium  
File:line: `l10n_cr_einvoice/models/validation_rule.py:438-622`  
Issue: `safe_eval()` allows expressions with `env` in context.  
Impact: If rule editing is not strictly admin-only, this is a privilege escalation vector.  
Fix: Restrict rule edits to admins and reduce eval context surface.

24. Severity: Medium  
File:line: `l10n_cr_einvoice/models/einvoice_document.py:1234-1238`  
Issue: `hacienda_submission_date` is updated on every status check.  
Impact: Original submission timestamp is lost.  
Fix: Only set submission date at submission time.

25. Severity: Medium  
File:line: `payment_tilopay/controllers/__init__.py:3` + `payment_tilopay/controllers/tilopay_webhook.py:1-220`  
Issue: Two competing webhook controllers exist; only `main.py` is imported.  
Impact: Dead code and architectural drift.  
Fix: Choose one webhook path and remove or wire the other.

26. Severity: Medium  
File:line: `payment_tilopay/models/payment_provider.py:38-47`  
Issue: Credential constraint checks only API key.  
Impact: Provider can be enabled with incomplete credentials.  
Fix: Validate API user and password too.

27. Severity: Medium  
File:line: `payment_tilopay/models/payment_transaction.py:238-256`  
Issue: Hash verification uses partner email; if missing, empty string is used, possibly violating Tilopay hash rules.  
Impact: Valid callbacks rejected when email is missing.  
Fix: Enforce email or follow official hash behavior for missing fields.

28. Severity: Low  
File:line: `l10n_cr_einvoice/models/xml_generator.py:516-520`  
Issue: Defaulting to cash (01) without a hard error can silently misreport payment method.  
Impact: Wrong `MedioPago` in XML.  
Fix: Warn loudly or block FE when payment method is unknown.

29. Severity: Low  
File:line: `l10n_cr_einvoice/models/einvoice_document.py:1001-1062`  
Issue: `_generate_clave()` does not validate company VAT before embedding it.  
Impact: Clave may contain zeros; Hacienda rejection later.  
Fix: Validate VAT before clave generation.

30. Severity: Low  
File:line: `l10n_cr_einvoice/models/pos_order.py:166-169`  
Issue: `raise e` loses traceback.  
Impact: Debugging becomes harder.  
Fix: Use `raise`.

31. Severity: High  
File:line: `l10n_cr_einvoice/models/d150_vat_report.py:570-582`  
Issue: VAT tax is computed as `price_subtotal * rate` instead of using actual tax amounts.  
Impact: Incorrect VAT credit/amount due with discounts, tax-included prices, or multiple taxes.  
Fix: Use Odoo’s tax computation (`tax_ids.compute_all`) or line tax totals.

32. Severity: High  
File:line: `l10n_cr_einvoice/models/d150_vat_report.py:495-523`  
Issue: Line tax is computed once per line but added per tax in loop; multi-tax lines double-count.  
Impact: Sales VAT overstated.  
Fix: Use per-tax breakdown from Odoo tax engine.

33. Severity: Medium  
File:line: `l10n_cr_einvoice/models/d150_vat_report.py:487-536`  
Issue: Credit notes only tracked for 13% and not for reduced rates; refunds for reduced rates are ignored.  
Impact: VAT report overstated for 4/2/1% refunds.  
Fix: Track credit notes for all applicable rates.

34. Severity: Medium  
File:line: `l10n_cr_einvoice/models/d150_vat_report.py:573-590`  
Issue: Goods vs services split is TODO; all 13% purchases treated as goods.  
Impact: D-150 goods/services breakdown is wrong.  
Fix: Classify based on product/service or account.

35. Severity: High  
File:line: `l10n_cr_einvoice/models/d150_vat_report.py:647-661`  
Issue: `XMLSigner.sign_xml()` is called with a single `hacienda_certificate_id`. The signer expects certificate and private key objects.  
Impact: Tax report signing fails at runtime.  
Fix: Use `certificate_manager.load_certificate_from_company()` and pass objects to signer.

36. Severity: High  
File:line: `l10n_cr_einvoice/models/d101_income_tax_report.py:551-555`  
Issue: `XMLSigner.sign_xml()` called with `hacienda_certificate_id` only.  
Impact: D-101 XML signing fails.  
Fix: Load certificate/private key objects and pass both.

37. Severity: Medium  
File:line: `l10n_cr_einvoice/models/d101_income_tax_report.py:486-520`  
Issue: D-101 calculation is overly simplified; all expenses are lumped into operating expenses, and depreciation/financials/other income are TODO.  
Impact: D-101 values are materially incorrect.  
Fix: Categorize by account types and implement remaining sections.

38. Severity: High  
File:line: `l10n_cr_einvoice/models/d151_informative_report.py:240-260`  
Issue: Customer totals include `out_refund` but do not negate refunds.  
Impact: D-151 overstates customer totals.  
Fix: Subtract refunds or use signed amounts in SQL.

39. Severity: Medium  
File:line: `l10n_cr_einvoice/models/d151_informative_report.py:286-307`  
Issue: Supplier totals ignore vendor refunds (`in_refund`).  
Impact: D-151 overstates supplier totals.  
Fix: Include `in_refund` and negate amounts.

40. Severity: Medium  
File:line: `l10n_cr_einvoice/models/d151_informative_report.py:246-285`  
Issue: SQL groups by `partner_id` without excluding null; then `browse(None)` creates lines with missing partner.  
Impact: Potential crashes or invalid lines.  
Fix: Add `partner_id IS NOT NULL` in SQL.

41. Severity: High  
File:line: `l10n_cr_einvoice/models/d151_informative_report.py:348-359`  
Issue: `XMLSigner.sign_xml()` called with `hacienda_certificate_id` only.  
Impact: D-151 XML signing fails.  
Fix: Load certificate/private key objects and pass both.

42. Severity: Medium  
File:line: `l10n_cr_einvoice/models/tax_report_xml_generator.py:60-62`  
Issue: XML generator explicitly omits XML namespaces (“removed for simpler testing”).  
Impact: Production submissions may be rejected if namespaces are required.  
Fix: Use official TRIBU-CR namespaces in generated XML.

43. Severity: Medium  
File:line: `l10n_cr_einvoice/models/tax_report_xml_generator.py:72-77`  
Issue: Company ID type is hard-coded to `02` (jurídica).  
Impact: Incorrect for físicas or other ID types.  
Fix: Derive ID type from VAT format (same logic as HACIENDA ID detection).

44. Severity: Medium  
File:line: `l10n_cr_einvoice/models/tax_report_xml_generator.py:590`  
Issue: Tax report XML has no XSD validation (TODO).  
Impact: Invalid tax report XML can be sent.  
Fix: Add XSD validation when schemas are available.

# Additional Findings (Appended)

45. Severity: High  
File:line: `l10n_cr_einvoice/models/pos_order.py:108-153`  
Issue: `_generate_cr_einvoice()` does not check for an existing `l10n_cr_einvoice_document_id` before creating a new document.  
Impact: Duplicate e-invoices can be created on retries or multiple calls.  
Fix: Guard against duplicates or add a unique constraint on `pos_order_id` in `l10n_cr.einvoice.document`.

46. Severity: Medium  
File:line: `l10n_cr_einvoice/models/einvoice_document.py:369-373`  
Issue: NOWAIT row lock errors are not handled; users get raw DB errors.  
Impact: Poor UX, confusion in POS/invoicing flows.  
Fix: Catch lock errors and show a user-friendly “record is being processed” message.

47. Severity: Medium  
File:line: `l10n_cr_einvoice/models/xsd_validator.py:92-100`  
Issue: XSD validation errors are logged as warnings and treated as success.  
Impact: Invalid XML can pass local validation and later be rejected by Hacienda.  
Fix: Fail XSD validation in production; allow a bypass only in dev/test mode.

48. Severity: Medium  
File:line: `l10n_cr_einvoice/models/cedula_lookup_service.py:260-319`  
Issue: Hacienda API rate limiting is enforced via a custom limiter, but failure returns a user-facing error without automatic retry or queue.  
Impact: Lookup failures during spikes; manual retry required.  
Fix: Add retry with jitter or enqueue refresh job when rate-limited.

49. Severity: Medium  
File:line: `l10n_cr_einvoice/models/cedula_cache.py:340-370`  
Issue: `get_cached()` increments access count and returns stale entries but doesn’t automatically trigger refresh unless `refresh_if_needed()` is called elsewhere.  
Impact: Stale entries can linger without refresh.  
Fix: Call `refresh_if_needed()` within `get_cached()` when in refresh tier.

50. Severity: Medium  
File:line: `l10n_cr_einvoice/models/xml_generator.py:981-985`  
Issue: `TotalImpuesto` is always emitted even if zero. Some schemas expect `TotalImpuesto` to be omitted when zero.  
Impact: Possible schema or Hacienda rejection depending on strictness.  
Fix: Emit `TotalImpuesto` only if non-zero (align with XSD requirements).

51. Severity: Medium  
File:line: `l10n_cr_einvoice/models/hacienda_api.py:65-106`  
Issue: OAuth token cache is module-level and keyed by company id; in long-lived workers, token refresh failures can persist across requests.  
Impact: Random auth failures under load; hard to diagnose.  
Fix: On refresh failure, force password grant immediately and log full failure context.

52. Severity: Medium  
File:line: `l10n_cr_einvoice/models/xml_generator.py:456-524`  
Issue: Payment method detection for POS uses payment method *name* string matching.  
Impact: Misclassification when names are customized or localized.  
Fix: Use POS payment method configuration mapping (codes) instead of name matching.

53. Severity: Medium  
File:line: `l10n_cr_einvoice/models/einvoice_document.py:340-408`  
Issue: Validation rules engine exceptions are swallowed (logged) and then fallback validation runs.  
Impact: A broken rule engine may silently degrade validations without alerting admins.  
Fix: Raise a visible warning or flag system health if rule engine errors occur.

54. Severity: Low  
File:line: `l10n_cr_einvoice/models/einvoice_document.py:421-430`  
Issue: `self.name = clave[21:41]` assumes clave format; any change or mismatch produces wrong consecutive.  
Impact: Incorrect `NumeroConsecutivo`.  
Fix: Derive consecutive from actual sequence rather than slicing clave.
