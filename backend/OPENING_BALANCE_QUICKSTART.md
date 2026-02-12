# Opening Balance - Quick Start Guide

## Test the Implementation

### Prerequisites
- Backend running on `http://localhost:8000`
- Test tenant: `b3776033-40e5-42e2-ab7b-b1df97062d0c`

### Option 1: Run Test Script (Recommended)

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
source venv/bin/activate
python test_opening_balance.py
```

This will test:
1. ✅ Balanced import (success)
2. ✅ Validation with bank verification
3. ✅ Preview
4. ✅ Import to ledger
5. ❌ Unbalanced import (blocked)
6. ❌ Bank mismatch (blocked)
7. ✅ List all

### Option 2: Manual cURL Tests

#### 1. Import Balanced Opening Balance
```bash
curl -X POST http://localhost:8000/api/opening-balance/import \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "b3776033-40e5-42e2-ab7b-b1df97062d0c",
    "import_date": "2024-01-01",
    "fiscal_year": "2024",
    "description": "Test Åpningsbalanse",
    "lines": [
      {"account_number": "1920", "account_name": "Bank", "debit": "100000.00", "credit": "0.00"},
      {"account_number": "2000", "account_name": "Egenkapital", "debit": "0.00", "credit": "100000.00"}
    ]
  }'
```

**Expected:** Status 201, returns opening_balance with `id`

#### 2. Validate Opening Balance
```bash
# Replace {ID} with the ID from step 1
curl -X POST http://localhost:8000/api/opening-balance/validate \
  -H "Content-Type: application/json" \
  -d '{
    "opening_balance_id": "{ID}",
    "bank_balances": [
      {"account_number": "1920", "actual_balance": "100000.00"}
    ]
  }'
```

**Expected:** Status 200, `is_balanced: true`, `bank_balance_verified: true`

#### 3. Preview
```bash
curl http://localhost:8000/api/opening-balance/preview/{ID}
```

**Expected:** `can_import: true`, no errors

#### 4. Import to Ledger
```bash
curl -X POST http://localhost:8000/api/opening-balance/import-to-ledger/{ID}
```

**Expected:** Returns `voucher_number` and `journal_entry_id`

#### 5. Test Unbalanced (Should Fail)
```bash
curl -X POST http://localhost:8000/api/opening-balance/import \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "b3776033-40e5-42e2-ab7b-b1df97062d0c",
    "import_date": "2024-01-01",
    "fiscal_year": "2024",
    "description": "Unbalanced Test",
    "lines": [
      {"account_number": "1920", "account_name": "Bank", "debit": "100000.00", "credit": "0.00"},
      {"account_number": "2000", "account_name": "Egenkapital", "debit": "0.00", "credit": "95000.00"}
    ]
  }' | jq
```

**Expected:** Import succeeds, but validation shows `is_balanced: false`, import blocked

#### 6. List All Opening Balances
```bash
curl http://localhost:8000/api/opening-balance/list/b3776033-40e5-42e2-ab7b-b1df97062d0c | jq
```

### Check Journal Entry

After successful import, verify the journal entry:

```bash
# Replace {JOURNAL_ENTRY_ID} from import response
curl http://localhost:8000/api/journal-entries/{JOURNAL_ENTRY_ID} | jq
```

**Expected:**
- `source_type: "opening_balance"`
- `voucher_series: "IB"`
- `locked: true`
- Lines match opening balance

## Validation Rules Enforced

### Rule 1: Balance Check
- ✅ SUM(debit) = SUM(credit)
- ❌ Blocks if difference ≠ 0.00

### Rule 2: Bank Balance Match
- ✅ Bank accounts (1920, 1921, etc.) match actual balance
- ❌ Blocks if mismatch > 0.01 NOK

### Rule 3: Account Existence
- ✅ All accounts exist in chart of accounts
- ⚠️ Warns if accounts missing

## Status Flow

```
DRAFT → VALIDATING → VALID → IMPORTED
                  ↓
               INVALID
```

## Quick API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/opening-balance/import` | POST | Upload opening balance data |
| `/api/opening-balance/validate` | POST | Validate balance and bank accounts |
| `/api/opening-balance/preview/{id}` | GET | Preview before import |
| `/api/opening-balance/import-to-ledger/{id}` | POST | Import to general ledger (locked) |
| `/api/opening-balance/list/{client_id}` | GET | List all opening balances |
| `/api/opening-balance/{id}` | DELETE | Delete draft (not imported) |

## Troubleshooting

### Import Blocked: "Not balanced"
**Cause:** SUM(debit) ≠ SUM(credit)
**Fix:** Check your data, ensure totals match exactly

### Import Blocked: "Bank balance mismatch"
**Cause:** Opening balance doesn't match actual bank balance
**Fix:** Verify bank statement, provide correct `actual_balance`

### Account Not Found
**Cause:** Account number not in chart of accounts
**Fix:** Add account to chart of accounts first, or fix account number

### Already Imported
**Cause:** Trying to import same opening balance twice
**Fix:** Delete and re-import if needed (only for draft status)

## Need Help?

Check the full documentation:
- **Implementation Details:** `OPENING_BALANCE_IMPLEMENTATION.md`
- **Delivery Report:** `OPENING_BALANCE_DELIVERY.md`
- **Test Script:** `test_opening_balance.py`
