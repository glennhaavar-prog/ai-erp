# TEST DATA SUMMARY - End-to-End Testing

**Created:** 2026-02-14  
**Test Client ID:** `09409ccf-d23e-45e5-93b9-68add0b96277`

---

## ✅ Populated Test Data

### 1. Leverandørfakturaer (Supplier Invoices) - 10 items

**Total Value:** 163,568.75 NOK

**Distribution:**
- ✅ 3 High confidence (85-95%) - Auto-approve candidates
- ✅ 4 Medium confidence (60-75%) - Needs review
- ✅ 3 Low confidence (30-50%) - Manual handling required

**Examples:**
- **Elkjøp Nordic AS** - IT-utstyr (4,953 NOK, 34% confidence) - Low confidence, unclear description
- **Coop Norge SA** - Kontorrekvisita (62,078 NOK, 87% confidence) - High confidence, auto-approve candidate
- **Telenor Norge AS** - Telefoni (2,909 NOK, 69% confidence) - Medium confidence, missing KID
- **BDO Norge AS** - Regnskapstjenester (10,455 NOK, 95% confidence) - Very high confidence

**Features demonstrated:**
- Realistic Norwegian suppliers (Elkjøp, Coop, Circle K, Telenor, etc.)
- Various account types (6540, 6700, 7160, 6900, etc.)
- VAT codes: 3 (25% MVA) and 0 (exempt)
- Some with KID numbers, some without
- Different confidence levels triggering different review priorities

---

### 2. Andre Bilag (Other Vouchers) - 8 new items (12 total with existing)

**Distribution:**
- ✅ 3 Employee expenses (ansatteutlegg)
- ✅ 3 Inventory adjustments (lagerjusteringer)
- ✅ 2 Manual corrections (manuelle korreksjoner)

**Examples:**

**Employee Expenses:**
- **Bensinutlegg Bodø-Tromsø** - 2,000 NOK (72% confidence)
- **Konferanse Oslo** - 3,200 NOK (68% confidence)
- **Kontorrekvisita** - 300 NOK (55% confidence)

**Inventory Adjustments:**
- **Varetelling Q1** - -2,340 NOK adjustment (65% confidence)
- **Svinn** - 8,750 NOK write-off (58% confidence) - Requires manager approval
- **Lagerjustering råvarer** - -1,250 NOK (48% confidence) - Cause unclear

**Manual Corrections:**
- **Feilført bilag #1234** - 4,500 NOK correction (42% confidence)
- **Periodisering forsikring** - 12,000 NOK accrual (52% confidence)

---

### 3. Banktransaksjoner (Bank Transactions) - 15 items

**Bank Account:** 15064142857

**Distribution:**
- ✅ 10 Unmatched (needs matching)
- ✅ 5 Auto-matchable (high confidence matches)

**Transaction Types:**
- 7 Customer payments (inn) - Total: 168,769 NOK
- 4 Supplier payments (ut)
- 2 Bank fees
- 1 Payroll payment - 185,000 NOK
- 1 VAT payment - 42,750 NOK

**Net Movement:** -121,679 NOK (more out than in)

**Examples:**
- **Customer payment** - Nordic Solutions AS, 14,422 NOK (no KID - needs manual match)
- **Supplier payment** - Elkjøp Nordic AS, -17,113 NOK (with KID: 924317753)
- **Bank fee** - Kontokredittavgift, -150 NOK (72% AI confidence)
- **Payroll** - 185,000 NOK (68% AI confidence)
- **MVA** - Skatteetaten, -42,750 NOK (75% AI confidence)

---

## 🎯 Where to Find in UI

### Review Queue - Supplier Invoices
**Endpoint:** `/api/review-queue/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&type=supplier_invoice`

**UI Location:** Review Queue → Filter: "Supplier Invoices"

**What you'll see:**
- 10 invoices sorted by priority (High → Low)
- AI confidence scores (34% to 95%)
- Suggested account postings
- KID numbers where available
- VAT calculations

### Other Vouchers
**Endpoint:** `/api/other-vouchers/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277`

**UI Location:** Review Queue → Filter: "Other Vouchers" or specific types

**What you'll see:**
- 12 items total (8 new + 4 existing from previous tests)
- Employee expenses with receipts
- Inventory adjustments with reasons
- Manual corrections with context

### Bank Reconciliation
**Endpoint:** `/api/bank-recon/unmatched?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&account=1920&period_start=2026-01-01&period_end=2026-02-28`

**Note:** Bank transactions use account `15064142857` (not 1920). Adjust endpoint or use transactions list.

**UI Location:** Bank Reconciliation → Account: 15064142857

**What you'll see:**
- 15 transactions over January-February 2026
- Mix of incoming and outgoing payments
- Some with KID for automatic matching
- AI match suggestions for fees, payroll, VAT

---

## 🧪 Test Scenarios Glenn Can Try

### Scenario 1: Auto-Approve High Confidence Invoice
1. Go to Review Queue → Supplier Invoices
2. Find **BDO Norge AS** (95% confidence, 10,455 NOK)
3. Review AI suggestion:
   - Account 7500 (Regnskapstjenester)
   - VAT code 0 (exempt)
   - KID: 948943840
4. **Action:** Approve automatically
5. **Expected:** Invoice posted to ledger, removed from queue

### Scenario 2: Correct Medium Confidence Invoice
1. Find **Telenor Norge AS** (69% confidence, 2,909 NOK)
2. Issue: Missing KID number
3. **Action:** Add KID manually or verify account
4. **Expected:** Confidence increases, can approve

### Scenario 3: Manual Handling Low Confidence
1. Find **Elkjøp Nordic AS** (34% confidence, 4,953 NOK)
2. Issues: Low confidence + unclear description
3. **Action:** Verify invoice details, correct if needed
4. **Expected:** Learn AI pattern from correction

### Scenario 4: Employee Expense Review
1. Go to Other Vouchers → Employee Expenses
2. Find **Bensinutlegg Bodø-Tromsø** (2,000 NOK)
3. **Action:** Verify distance (850 km) matches amount
4. Approve or request clarification

### Scenario 5: Inventory Write-off
1. Go to Other Vouchers → Inventory Adjustments
2. Find **Svinn - defekte varer** (8,750 NOK)
3. Requires manager approval (high priority)
4. **Action:** Approve or reject with reason
5. **Expected:** Adjustment posted to account 6390

### Scenario 6: Bank Transaction Matching
1. Go to Bank Reconciliation
2. Find **Customer payment** - Nordic Solutions AS (14,422 NOK)
3. No KID - needs manual match
4. **Action:** Search invoices, match by amount/date
5. **Expected:** Transaction marked as matched

### Scenario 7: Auto-Match Bank Fee
1. Find **Kontokredittavgift** (-150 NOK)
2. AI suggests account 7700 (Bankgebyrer) with 72% confidence
3. **Action:** Review and approve match
4. **Expected:** Transaction posted to ledger

---

## 📊 Statistics

| Category | Count | Value (NOK) |
|----------|-------|-------------|
| Supplier Invoices | 10 | 163,568.75 |
| Employee Expenses | 3 | 5,500.00 |
| Inventory Adjustments | 3 | -12,340.00 |
| Manual Corrections | 2 | 16,500.00 |
| Bank Transactions (In) | 7 | 168,769.00 |
| Bank Transactions (Out) | 8 | -290,448.00 |
| **Total Items** | **33** | **51,549.75** |

---

## 🔍 Verification Commands

### Count items in each category
```bash
# Supplier invoices
curl "http://localhost:8000/api/review-queue/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&type=supplier_invoice" | jq '.items | length'

# Other vouchers
curl "http://localhost:8000/api/other-vouchers/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277" | jq '.items | length'

# Bank transactions (check database directly)
psql $DATABASE_URL -c "SELECT COUNT(*) FROM bank_transactions WHERE client_id = '09409ccf-d23e-45e5-93b9-68add0b96277';"
```

### View specific confidence distributions
```bash
# High confidence invoices (85%+)
curl "http://localhost:8000/api/review-queue/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&type=supplier_invoice" | jq '.items[] | select(.ai_confidence >= 0.85) | {supplier: .supplier, confidence: .ai_confidence, amount: .amount}'

# Low confidence items (< 60%)
curl "http://localhost:8000/api/review-queue/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277" | jq '.items[] | select(.ai_confidence < 0.60) | {description: .description, confidence: .ai_confidence}'
```

---

## ✅ Deliverables Complete

- [x] 10 supplier invoices with varying confidence levels
- [x] 8 other vouchers (employee expenses, inventory, corrections)
- [x] 15 bank transactions (10 unmatched, 5 matchable)
- [x] All data verified via API
- [x] Summary document created

**Ready for Glenn's end-to-end testing!** 🎉

---

## 📝 Notes

- All test data uses **Norwegian** suppliers, account numbers (NS 4102), and terminology
- Realistic amounts (500 - 62,000 NOK)
- Proper VAT handling (25% and exempt)
- KID numbers where appropriate
- AI confidence levels distributed to test all review flows
- Data created: 2026-02-14 at 17:45 UTC

**Note:** Test client may have additional existing test data from previous tests. The numbers above represent NEW data created for this E2E test session:
- Current total in Review Queue: ~50 supplier invoices (10 new)
- Current total Other Vouchers: 12 items (8 new)
- Current total Bank Transactions: 15 items (all new)

The new data is easily identifiable by creation timestamp (2026-02-14 17:45-17:46)

---

## 🔧 Scripts Used

1. `scripts/populate_supplier_invoices.py` - 10 supplier invoices
2. `scripts/populate_other_vouchers.py` - 8 other vouchers
3. `scripts/populate_bank_transactions.py` - 15 bank transactions

All scripts are idempotent and can be run multiple times to add more test data if needed.
