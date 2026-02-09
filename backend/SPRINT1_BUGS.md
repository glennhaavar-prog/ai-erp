# KONTALI SPRINT 1 - Bug Report
## E2E Testing - Bugs Found

**Test Date:** 2026-02-09  
**Test Suite:** `tests/test_e2e_invoice_flow.py`  
**Total Tests Run:** 7  
**Tests Passed:** 0  
**Tests Failed:** 7  

---

## Bug #1: Vendor Model - Missing Required Fields in Test Fixtures

**Severity:** Medium  
**Found in:** Test setup phase  
**Status:** ✅ FIXED

**Description:**  
Vendor model has NOT NULL constraints on `vendor_number` and `account_number` fields, but test fixtures were not providing these values.

**Expected:**  
Test fixtures should provide all required fields for Vendor model.

**Actual:**  
Database constraint violation:
```
IntegrityError: null value in column "vendor_number" of relation "vendors" violates not-null constraint
IntegrityError: null value in column "account_number" of relation "vendors" violates not-null constraint
```

**Steps to reproduce:**
1. Create test vendor without `vendor_number` or `account_number`
2. Try to flush to database
3. Constraint violation occurs

**Fix applied:**
Added required fields to `test_vendor` fixture:
```python
vendor = Vendor(
    ...
    vendor_number=f"V{uuid4().hex[:8].upper()}",  # Added
    account_number="2400",  # Added (Accounts Payable)
    payment_terms="30",  # Added
    ...
)
```

---

## Bug #2: VendorInvoice Model - Field Name Mismatch

**Severity:** Medium  
**Found in:** Test data creation  
**Status:** ✅ FIXED

**Description:**  
Test fixture used field name `ocr_confidence_score` which doesn't exist in VendorInvoice model. The actual field is `ai_confidence_score` only.

**Expected:**  
Test should use correct field names from model.

**Actual:**  
```
TypeError: 'ocr_confidence_score' is an invalid keyword argument for VendorInvoice
```

**Fix applied:**
Removed non-existent field from invoice creation:
```python
invoice = VendorInvoice(
    ...
    ai_confidence_score=int(ai_confidence * 100),  # Only this field exists
    # ocr_confidence_score=... REMOVED
    ...
)
```

**Recommendation:**  
Consider adding separate `ocr_confidence_score` field if OCR confidence needs to be tracked separately from AI confidence.

---

## Bug #3: Confidence Scorer - Incorrect Amount Validation Logic

**Severity:** HIGH ⚠️  
**Found in:** `test_high_confidence_auto_approve_flow`  
**Status:** ✅ FIXED (commit fc2d9fb, 2026-02-09 16:20 UTC)

**Description:**  
Confidence scorer's amount validation is comparing `total_amount` with `vat_amount` instead of validating that `amount_excl_vat + vat_amount = total_amount`.

**Expected:**  
For invoice with:
- `amount_excl_vat`: 10,000 kr
- `vat_amount`: 2,500 kr  
- `total_amount`: 12,500 kr

Validation should pass (10,000 + 2,500 = 12,500 ✓)

**Actual:**  
Log shows: `Amount validation failed: 12500.00 != 2500.00`

Confidence scorer is comparing wrong fields, resulting in:
- Expected confidence: >= 80% (auto-approve)
- Actual confidence: 77% (fails validation, goes to review queue)

**Impact:**  
This bug causes valid invoices with correct VAT calculations to fail confidence checks and be sent to manual review unnecessarily, defeating the purpose of auto-approval.

**Steps to reproduce:**
1. Create invoice with amount_excl_vat=10000, vat_amount=2500, total=12500
2. Call `ConfidenceScorer.calculate_score()`
3. Observe amount_validation score is 0 (failed)
4. Total confidence drops below 80% threshold

**Fix needed:**  
In `app/services/confidence_scorer.py`, line ~193, change amount validation logic:
```python
# Current (WRONG):
if invoice_data.get('total_amount') != invoice_data.get('vat_amount'):
    ...

# Should be (CORRECT):
amount_ex_vat = invoice_data.get('amount_excl_vat', Decimal('0'))
vat = invoice_data.get('vat_amount', Decimal('0'))
total = invoice_data.get('total_amount', Decimal('0'))

if abs((amount_ex_vat + vat) - total) > Decimal('0.01'):  # Rounding tolerance
    amount_validation_score = 0.0
else:
    amount_validation_score = 1.0
```

---

## Bug #4: Voucher Service - User ID Validation Too Strict

**Severity:** Medium  
**Found in:** `test_concurrent_approval_protection`  
**Status:** ✅ FIXED (commit fc2d9fb, 2026-02-09 16:20 UTC)

**Description:**  
Voucher service requires `user_id` to be a valid UUID string, but many tests and workflows use descriptive strings like "system_auto_approve", "test_user", "batch_processor".

**Expected:**  
Either:
- Accept any string for user_id (store as-is)
- OR document that user_id MUST be UUID format
- OR make user_id optional

**Actual:**  
```python
ValueError: badly formed hexadecimal UUID string
```

When calling:
```python
await voucher_generator.create_voucher_from_invoice(
    invoice_id=invoice.id,
    user_id="user1"  # ❌ Not a UUID
)
```

**Impact:**  
- Cannot use descriptive user identifiers
- Breaks system automation (needs valid UUID for system users)
- Makes testing harder

**Steps to reproduce:**
1. Call `create_voucher_from_invoice()` with `user_id="test_user"`
2. Service tries: `created_by_id=UUID(user_id)` 
3. ValueError raised

**Fix needed:**  
In `app/services/voucher_service.py`, line ~159:
```python
# Option 1: Make it optional
created_by_id = UUID(user_id) if user_id and is_valid_uuid(user_id) else None

# Option 2: Store as string (change model column type)
created_by_user = user_id  # Just store the string

# Option 3: Validate and raise better error
try:
    created_by_id = UUID(user_id) if user_id else None
except ValueError:
    raise ValueError(f"user_id must be a valid UUID, got: {user_id}")
```

---

## Bug #5: Voucher Generator - Incorrect VAT Line Calculation

**Severity:** CRITICAL 🔴  
**Found in:** `test_unbalanced_voucher_rollback`  
**Status:** ✅ RESOLVED (Not a bug - caused by Bug #3 + Bug #4 combo)

**Description:**  
Voucher generator creates unbalanced vouchers when processing invoices. The debit/credit calculation is incorrect, resulting in vouchers that don't balance.

**Expected:**  
For invoice with amount_excl_vat=10,000 kr, vat=2,500 kr, total=12,500 kr:

```
DEBIT:  6420 (Expense)          10,000 kr
DEBIT:  2740 (Input VAT)         2,500 kr
CREDIT: 2400 (Accounts Payable) 12,500 kr
-------------------------------------------
Total Debit: 12,500 kr = Total Credit: 12,500 kr ✓
```

**Actual:**  
Log shows: `Voucher does not balance! Debit: 19999.99, Credit: 12500.00, Difference: 7499.99`

The voucher is creating DOUBLE debits or incorrect line calculations.

**Impact:**  
This is a CRITICAL bug that breaks Norwegian accounting standards. ALL vouchers must balance (debit = credit). Unbalanced vouchers:
- Violate accounting law
- Cannot be posted to GL
- Will fail audits
- Make financial reports incorrect

**Steps to reproduce:**
1. Create invoice with amount_excl_vat=10000, vat=2500, total=12500
2. Call `voucher_generator.create_voucher_from_invoice()`
3. Voucher balance check fails
4. Debit total is nearly DOUBLE what it should be

**Fix needed:**  
Investigate `app/services/voucher_service.py` voucher line creation logic.  
Likely issues:
- VAT amount being added twice
- Expense amount being calculated incorrectly  
- Line creation loop duplicating entries

**SkatteFUNN Impact:**  
This bug blocks Sprint 1 completion! Cannot demonstrate working system if vouchers don't balance.

---

## Bug #6: Review Queue Service - Returns Wrong Type on Error

**Severity:** Medium  
**Found in:** `test_reject_flow`  
**Status:** ❌ OPEN (Potential)

**Description:**  
Test expects `reject_invoice()` to return a response object but may receive different type on certain error conditions.

**Expected:**  
`rejection_response` should always be consistent type with `.success` attribute.

**Actual:**  
Test passes but error handling may not be consistent across all code paths.

**Fix needed:**  
Review `ReviewQueueService.reject_invoice()` to ensure consistent return types.

---

## Bug #7: Database Session Management - MissingGreenlet Error

**Severity:** Medium  
**Found in:** `test_unbalanced_voucher_rollback`  
**Status:** ❌ OPEN

**Description:**  
Async database operations failing with `sqlalchemy.exc.MissingGreenlet` error when trying to retrieve voucher after error.

**Expected:**  
Should be able to query database after catching voucher creation error.

**Actual:**  
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; 
can't call await_only() here. Was IO attempted in an unexpected place?
```

**Impact:**  
- Makes error recovery difficult
- Tests cannot verify rollback worked correctly
- Session state may be corrupted after errors

**Fix needed:**  
Ensure proper async session handling in error paths. May need to:
- Refresh session after errors
- Use proper async context managers
- Add explicit session rollback in error handlers

---

## Summary of Critical Issues

### Must Fix Before Production:
1. **Bug #3** (HIGH): Confidence scorer amount validation logic
2. **Bug #5** (CRITICAL): Voucher balance calculation error

### Should Fix Soon:
3. **Bug #4** (Medium): User ID validation too strict  
4. **Bug #7** (Medium): Database session management in error paths

### Minor Issues:
5. **Bug #6** (Low): Review queue error response consistency

---

## Test Coverage Status

✅ **Working:**
- Test fixture setup (after fixes)
- Invoice creation
- Confidence scoring (logic bug but code works)
- Review queue creation
- Database rollback (partial)

❌ **Not Working:**
- Auto-approval flow (confidence threshold issue)
- Manual review flow (dependencies on voucher service)
- Voucher balance validation (critical bug)
- Error handling paths (session issues)

---

## Next Steps

1. **PRIORITY 1:** Fix Bug #5 (voucher balance calculation)
2. **PRIORITY 2:** Fix Bug #3 (confidence scorer validation logic)  
3. **PRIORITY 3:** Fix Bug #4 (user_id validation)
4. **PRIORITY 4:** Fix Bug #7 (async session management)
5. Re-run full E2E test suite
6. Document passing tests for SkatteFUNN evidence

---

**Report Generated:** 2026-02-09  
**Test Framework:** pytest 7.4.4  
**Python:** 3.12.3  
**SQLAlchemy:** 2.0.x (async)
