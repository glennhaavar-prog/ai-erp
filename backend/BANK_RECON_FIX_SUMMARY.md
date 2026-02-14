# Bank Reconciliation Fix - Summary

## Problem
The `/api/bank-recon/unmatched` endpoint was returning 0 bank transactions when it should return 15.

## Root Cause
**Design mismatch between bank transactions and ledger entries:**

1. **Bank transactions** stored the actual bank account number: `"15064142857"`
2. **Ledger entries** use the chart of accounts number: `"1920"`
3. The API filtered both by the same `account` parameter, so they could never match

## Solution

### 1. Database Schema Update
Added `ledger_account_number` column to `bank_transactions` table:
```sql
ALTER TABLE bank_transactions 
ADD COLUMN ledger_account_number VARCHAR(20);

CREATE INDEX ix_bank_transactions_ledger_account 
ON bank_transactions(ledger_account_number);

UPDATE bank_transactions 
SET ledger_account_number = '1920' 
WHERE bank_account = '15064142857';
```

### 2. Model Update
Updated `app/models/bank_transaction.py`:
- Added `ledger_account_number` field to store the chart of accounts number for ledger matching

### 3. API Update
Updated `app/api/routes/bank_recon.py`:
- Changed filter to support both `bank_account` and `ledger_account_number`:
```python
or_(
    BankTransaction.bank_account == account,
    BankTransaction.ledger_account_number == account
)
```

### 4. Populate Script Update
Updated `scripts/populate_bank_transactions.py`:
- Added `LEDGER_ACCOUNT = "1920"` constant
- Set `ledger_account_number=LEDGER_ACCOUNT` on all created transactions

## Results

### Before Fix
```bash
curl "http://localhost:8000/api/bank-recon/unmatched?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&account=1920"
# Result: 0 bank_transactions, 14 ledger_entries
```

### After Fix
```bash
curl "http://localhost:8000/api/bank-recon/unmatched?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&account=1920"
# Result: 15 bank_transactions, 14 ledger_entries ✅
```

## Usage

**For bank reconciliation, use the chart of accounts number (1920):**
```bash
curl "http://localhost:8000/api/bank-recon/unmatched?client_id=CLIENT_ID&account=1920"
```

**Optional date filters (use `from_date` and `to_date`, NOT `period_start`/`period_end`):**
```bash
curl "http://localhost:8000/api/bank-recon/unmatched?client_id=CLIENT_ID&account=1920&from_date=2026-02-01&to_date=2026-02-28"
```

## Notes

- The API parameter names are `from_date` and `to_date`, not `period_start` and `period_end`
- Using `account=15064142857` (actual bank account) will return bank transactions but NO ledger entries
- Using `account=1920` (chart of accounts) will return BOTH bank transactions and ledger entries
- Frontend should use `account=1920` for bank reconciliation

## Files Modified

1. Database: `bank_transactions` table (added column)
2. `app/models/bank_transaction.py` (added field)
3. `app/api/routes/bank_recon.py` (updated filter logic)
4. `scripts/populate_bank_transactions.py` (updated test data generation)
