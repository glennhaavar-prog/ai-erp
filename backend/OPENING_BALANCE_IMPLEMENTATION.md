# Opening Balance (Åpningsbalanse) Implementation

## Overview

Complete backend implementation for Opening Balance Import with **strict validation** per Glenn's requirements.

## Critical Requirements (IMPLEMENTED ✓)

### Rule 1: MUST Balance to Zero
- **SUM(debit) MUST = SUM(credit)** - No exceptions
- Blocks save/import if not balanced
- Shows clear error with exact difference amount
- Validation happens in `validate_opening_balance()` function

### Rule 2: Bank Balance MUST Match
- Balance on account 1920 (or other bank accounts) must match actual bank balance
- Validates down to 2 decimals
- Accepts manual bank balance verification
- Shows clear error if mismatch detected
- Bank accounts identified by prefixes: 1920, 1921, 1930, 1940, 1950, 1960

## Features Implemented

### 1. Import Wizard
**Endpoint:** `POST /api/opening-balance/import`

- Uploads opening balance data (JSON format)
- Supports account_number, account_name, debit, credit
- Creates draft opening balance
- Returns import ID for further processing

**Example Request:**
```json
{
  "client_id": "b3776033-40e5-42e2-ab7b-b1df97062d0c",
  "import_date": "2024-01-01",
  "fiscal_year": "2024",
  "description": "Åpningsbalanse 2024",
  "lines": [
    {"account_number": "1920", "account_name": "Bank", "debit": "100000.00", "credit": "0.00"},
    {"account_number": "2000", "account_name": "Egenkapital", "debit": "0.00", "credit": "100000.00"}
  ]
}
```

### 2. Validation
**Endpoint:** `POST /api/opening-balance/validate`

Validates:
- ✓ **Balance Check**: SUM(debit) = SUM(credit)
- ✓ **Bank Balance Match**: Compare with actual bank balance (manual or connection)
- ✓ **Account Existence**: All accounts must exist in chart of accounts
- ✓ **Missing Accounts**: Flags accounts not found

**Example Request:**
```json
{
  "opening_balance_id": "...",
  "bank_balances": [
    {
      "account_number": "1920",
      "actual_balance": "100000.00"
    }
  ]
}
```

**Validation Errors:**
- `NOT_BALANCED`: Shows difference amount
- `BANK_BALANCE_MISMATCH`: Shows expected vs actual
- `ACCOUNT_NOT_FOUND`: Lists missing accounts

### 3. Preview Display
**Endpoint:** `GET /api/opening-balance/preview/{id}`

Shows:
- All accounts with opening balances
- Highlighted bank accounts
- Validation status (passed/failed)
- Balance difference if not balanced
- List of errors and warnings
- `can_import` flag (only true if all validations passed)

### 4. Import to Ledger
**Endpoint:** `POST /api/opening-balance/import-to-ledger/{id}`

- Creates journal entry with source_type="opening_balance"
- Uses voucher series "IB" (Opening Balance)
- **LOCKS entry** (cannot be edited after import)
- Links opening balance to journal entry
- Marks status as "IMPORTED"

**Blocking Rules:**
- Blocks if `status != VALID`
- Blocks if `is_balanced == false`
- Blocks if already imported

### 5. List Opening Balances
**Endpoint:** `GET /api/opening-balance/list/{client_id}`

Returns all opening balances for a client with status info.

### 6. Delete Draft
**Endpoint:** `DELETE /api/opening-balance/{id}`

- Allows deletion of draft opening balances
- Blocks deletion of imported opening balances

## Database Schema

### Table: `opening_balances`
```sql
CREATE TABLE opening_balances (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id),
    import_date DATE NOT NULL,
    fiscal_year VARCHAR(4) NOT NULL,
    description TEXT DEFAULT 'Åpningsbalanse',
    status VARCHAR(50) DEFAULT 'draft',
    
    -- Validation Results
    is_balanced BOOLEAN DEFAULT false,
    balance_difference NUMERIC(15, 2) DEFAULT 0,
    bank_balance_verified BOOLEAN DEFAULT false,
    bank_balance_errors JSONB,
    missing_accounts JSONB,
    validation_errors JSONB,
    
    -- Cached Totals
    total_debit NUMERIC(15, 2) DEFAULT 0,
    total_credit NUMERIC(15, 2) DEFAULT 0,
    line_count INTEGER DEFAULT 0,
    
    -- Import Result
    imported_at TIMESTAMP,
    journal_entry_id UUID REFERENCES general_ledger(id),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Table: `opening_balance_lines`
```sql
CREATE TABLE opening_balance_lines (
    id UUID PRIMARY KEY,
    opening_balance_id UUID NOT NULL REFERENCES opening_balances(id),
    line_number INTEGER NOT NULL,
    account_number VARCHAR(10) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    
    -- Amounts
    debit_amount NUMERIC(15, 2) DEFAULT 0,
    credit_amount NUMERIC(15, 2) DEFAULT 0,
    
    -- Validation
    account_exists BOOLEAN DEFAULT false,
    is_bank_account BOOLEAN DEFAULT false,
    bank_balance_match BOOLEAN,
    expected_bank_balance NUMERIC(15, 2),
    validation_errors JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Workflow

1. **Import** → `POST /api/opening-balance/import`
2. **Validate** → `POST /api/opening-balance/validate`
3. **Preview** → `GET /api/opening-balance/preview/{id}`
4. **Import to Ledger** → `POST /api/opening-balance/import-to-ledger/{id}`

## Files Created/Modified

### New Files
- `/app/models/opening_balance.py` - SQLAlchemy models
- `/app/schemas/opening_balance.py` - Pydantic schemas
- `/app/api/routes/opening_balance.py` - API routes (27k lines)
- `/alembic/versions/20260211_1016_add_opening_balance.py` - Migration
- `/test_opening_balance.py` - Comprehensive test script

### Modified Files
- `/app/models/__init__.py` - Added OpeningBalance imports
- `/app/models/client.py` - Added opening_balances relationship
- `/app/main.py` - Registered opening_balance router

## Testing

Run comprehensive test suite:
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
source venv/bin/activate
python test_opening_balance.py
```

Tests cover:
1. ✓ Balanced opening balance (successful import)
2. ✓ Bank balance verification (matching)
3. ✓ Preview before import
4. ✓ Import to general ledger
5. ✓ Unbalanced opening balance (blocked)
6. ✓ Bank balance mismatch (blocked)
7. ✓ List all opening balances

## Test Client

Use test tenant: `b3776033-40e5-42e2-ab7b-b1df97062d0c`

## Key Validation Logic

### Balance Check
```python
total_debit = sum(line.debit_amount for line in lines)
total_credit = sum(line.credit_amount for line in lines)
difference = total_debit - total_credit

if difference != Decimal("0.00"):
    errors.append({
        "code": "NOT_BALANCED",
        "message": f"Difference: {difference} NOK"
    })
```

### Bank Balance Check
```python
if is_bank_account(account_number):
    net_balance = debit_amount - credit_amount
    difference = abs(net_balance - expected_balance)
    
    if difference > Decimal("0.01"):  # 2 decimal tolerance
        errors.append({
            "code": "BANK_BALANCE_MISMATCH",
            "message": f"Opening: {net_balance}, Actual: {expected_balance}"
        })
```

### Import Blocking
```python
if not opening_balance.is_balanced:
    raise HTTPException(
        status_code=400,
        detail=f"Cannot import: Not balanced. Difference: {difference} NOK"
    )
```

## Integration with Journal Entries

Opening balances are imported as **locked journal entries**:
- Source type: `"opening_balance"`
- Voucher series: `"IB"` (Opening Balance)
- Status: `"posted"`
- **Locked: `true`** (cannot be edited)

## Next Steps

1. **Frontend Integration**:
   - File upload component (CSV/Excel)
   - Preview table with validation indicators
   - Bank balance verification form
   - Visual balance summary (inspired by PowerOffice)

2. **Bank Connection Integration**:
   - Auto-fetch bank balances from DNB/Sbanken
   - Compare automatically during validation

3. **Bulk Upload**:
   - Parse CSV/Excel files
   - Map columns to fields
   - Preview before import

## Summary

✅ **Complete backend implementation**
✅ **All critical validations enforced**
✅ **MUST balance to zero** (Rule 1)
✅ **Bank accounts MUST match** (Rule 2)
✅ **Locked entries** (cannot edit after import)
✅ **Comprehensive error messages**
✅ **Ready for frontend integration**

**Test tenant:** b3776033-40e5-42e2-ab7b-b1df97062d0c
