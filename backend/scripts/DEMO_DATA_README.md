# Demo Data Population - TASK 7

## Overview

This script populates realistic Norwegian demo data across all 5 key modules of the ERP system:

1. **Leverandørreskontro** (Supplier Ledger) - 12+ entries
2. **Kundereskontro** (Customer Ledger) - 12+ entries  
3. **Bilagsjournal** (Voucher Journal) - 55+ vouchers
4. **Task Admin** (Task Management) - 50+ tasks
5. **Banktransaksjoner** (Bank Transactions) - 35+ transactions

## Features

✅ **Realistic Norwegian Data**
- Norwegian company names (Equinor, DNB, Telenor, etc.)
- Proper org numbers
- KID numbers for payment matching
- Norwegian transaction types (Vipps, BankAxept, Avtalegiro)

✅ **Balanced Accounting**
- All vouchers balanced (debit = credit)
- Proper account mappings (NS 4102)
- Correct VAT handling

✅ **Varied Statuses**
- Mix of open/partially_paid/paid invoices
- Overdue and current entries
- Different task statuses (not_started, in_progress, completed, deviation)

✅ **Idempotent**
- Can be run multiple times safely
- Checks for existing data before creating
- No duplicates

## Usage

### Run the Script

```bash
# From project root
cd ai-erp/backend
python3 scripts/populate_demo_data.py
```

or

```bash
# From backend directory
python scripts/populate_demo_data.py
```

### Expected Output

```
======================================================================
🚀 DEMO DATA POPULATION - TASK 7
======================================================================

Populating realistic Norwegian demo data for all modules...

📊 Target Client: Test AS (ID: b3776033-40e5-42e2-ab7b-b1df97062d0c)
   Org Number: 99986e7f5

📦 Module 1: Leverandørreskontro (Supplier Ledger)
  Creating 12 vendors...
  ✅ Created 12 vendors
  ✅ Created 12 supplier ledger entries
     - Amount range: 5,000 - 500,000 NOK
     - Due dates: Mix of overdue and current
     - Status: Mix of open/partially_paid/paid

📋 Module 2: Kundereskontro (Customer Ledger)
  ✅ Created 12 customer ledger entries
     - Amount range: 10,000 - 1,000,000 NOK
     - All with KID numbers for payment matching
     - Mix of overdue and current invoices

📓 Module 3: Bilagsjournal (Voucher Journal)
  ✅ Created 55 vouchers (bilag)
     - Spread over Jan-Feb 2026
     - Mix of types: vendor_invoice, customer_invoice, bank, manual
     - All balanced (debit = credit)
     - All with external references

✅ Module 4: Task Admin (Oppgaveadministrasjon)
  ✅ Created 50 tasks
     - Period: Jan-Feb 2026
     - Mix of categories: bokføring, avstemming, rapportering, compliance
     - Mix of status: not_started, in_progress, completed, deviation
     - Some with subtasks (checklist)

🏦 Module 5: Banktransaksjoner (Bank Transactions)
  ✅ Created 35 bank transactions
     - Period: Jan-Feb 2026
     - Norwegian transaction types (Vipps, BankAxept, Avtalegiro, etc.)
     - Mix of matched and unmatched
     - Some with KID numbers for automatic matching

======================================================================
✅ DEMO DATA POPULATION COMPLETE!
======================================================================

📈 Summary:
   • Leverandørreskontro:   12 entries
   • Kundereskontro:        12 entries
   • Bilagsjournal:         55 vouchers
   • Task Admin:            50 tasks
   • Banktransaksjoner:     35 transactions

   📊 Total records created: 164

💾 Data successfully committed to database.
```

## Data Details

### Module 1: Leverandørreskontro (Supplier Ledger)

**Creates:**
- 12 Norwegian suppliers (Equinor ASA, DNB Bank ASA, Telenor Norge AS, etc.)
- 12 supplier invoices with varied characteristics

**Features:**
- Amount range: 5,000 - 500,000 NOK
- Due dates categorized:
  - Not due (future)
  - 0-30 days overdue
  - 31-60 days overdue
  - 61-90 days overdue
  - 90+ days overdue
- Status distribution:
  - 40% open
  - 20% partially_paid
  - 40% paid

### Module 2: Kundereskontro (Customer Ledger)

**Creates:**
- 12 customer invoices to Norwegian companies

**Features:**
- Amount range: 10,000 - 1,000,000 NOK
- All entries have KID numbers for automatic payment matching
- Payment terms: 14 or 30 days
- Mix of overdue and current invoices
- Status: open/partially_paid/paid

### Module 3: Bilagsjournal (Voucher Journal)

**Creates:**
- 55+ balanced journal entries (vouchers)

**Features:**
- Spread across Jan-Feb 2026
- Four voucher types:
  - **L-series**: Leverandørfaktura (Vendor invoices)
  - **K-series**: Kundefaktura (Customer invoices)
  - **B-series**: Banktransaksjoner (Bank transactions)
  - **A-series**: Manuelt bilag (Manual entries)
- All vouchers properly balanced (debit = credit)
- External references (invoice numbers, etc.)
- Created by mix of AI agent and user

### Module 4: Task Admin

**Creates:**
- 50+ tasks spread across Jan-Feb 2026

**Features:**
- Task categories:
  - **Avstemming**: Reconciliation tasks
  - **Rapportering**: Reporting tasks
  - **Bokføring**: Bookkeeping tasks
  - **Compliance**: Compliance tasks
- Task frequencies:
  - Monthly (most common)
  - Quarterly
  - Yearly
- Status distribution:
  - 30% not_started
  - 30% in_progress
  - 30% completed
  - 10% deviation
- Some tasks include subtasks (checklist items)
- Completed tasks show who completed them (AI Agent, Line Andersen, Per Hansen)

### Module 5: Banktransaksjoner (Bank Transactions)

**Creates:**
- 35+ bank transactions

**Features:**
- Norwegian transaction types:
  - Vipps fra kunde
  - BankAxept betaling
  - Avtalegiro
  - eFaktura betaling
  - Nettbank overføring
  - Kredittkort visa/mastercard
  - Straksoverføring
  - Lønn utbetaling
  - MVA oppgjør
- 60% credit (money in), 40% debit (money out)
- Some transactions matched to customer invoices via KID
- Mix of matched/unmatched status
- Realistic Norwegian bank account numbers

## Verification

After running the script, verify data integrity:

### 1. Check Record Counts

```python
cd ai-erp/backend
python3 -c "
import asyncio
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models import SupplierLedger, CustomerLedger, GeneralLedger, Task, BankTransaction, Client

async def verify():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Client).where(Client.is_demo == True).limit(1))
        client = result.scalars().first()
        
        print(f'Client: {client.name}')
        
        for model, name in [
            (SupplierLedger, 'Supplier Ledger'),
            (CustomerLedger, 'Customer Ledger'),
            (GeneralLedger, 'Vouchers'),
            (Task, 'Tasks'),
            (BankTransaction, 'Bank Transactions')
        ]:
            result = await session.execute(
                select(func.count(model.id)).where(model.client_id == client.id)
            )
            print(f'{name}: {result.scalar()}')

asyncio.run(verify())
"
```

### 2. Check Voucher Balances

All vouchers should be balanced (sum of debits = sum of credits).

### 3. Check Status Distribution

Run queries to verify proper distribution of statuses across ledgers.

### 4. Check Date Ranges

All data should be within Jan-Feb 2026 date range.

## Idempotency Testing

Run the script multiple times to verify idempotency:

```bash
# First run - creates data
python3 scripts/populate_demo_data.py

# Second run - should skip existing data
python3 scripts/populate_demo_data.py
```

Second run should show:
```
⏭️  Already have 12 supplier ledger entries, skipping...
⏭️  Already have 12 customer ledger entries, skipping...
etc.
```

## Troubleshooting

### "No client found in database"

**Problem:** Script cannot find a demo client to populate.

**Solution:**
1. Ensure at least one client exists in the database
2. Mark a client as demo: `UPDATE clients SET is_demo = true WHERE id = '<client-id>';`

### Import Errors

**Problem:** Module import errors when running script.

**Solution:**
```bash
# Ensure you're in the backend directory
cd ai-erp/backend

# Activate venv if using one
source venv/bin/activate

# Run script
python3 scripts/populate_demo_data.py
```

### Database Connection Issues

**Problem:** Cannot connect to database.

**Solution:**
1. Check `.env` file has correct `DATABASE_URL`
2. Ensure PostgreSQL is running
3. Verify database exists: `psql -U erp_user -d ai_erp`

## Technical Details

### Dependencies

- SQLAlchemy (async)
- PostgreSQL database
- Python 3.8+

### Models Used

- `Client` - Multi-tenant client records
- `Vendor` - Supplier master data
- `SupplierLedger` - Accounts payable entries
- `CustomerLedger` - Accounts receivable entries
- `GeneralLedger` & `GeneralLedgerLine` - Journal entries
- `Task` - Task management records
- `BankTransaction` - Bank transaction records

### Database Tables

The script populates these tables:
- `vendors`
- `supplier_ledger`
- `customer_ledger`
- `general_ledger`
- `general_ledger_lines`
- `tasks`
- `bank_transactions`

## Future Enhancements

Potential improvements:
- [ ] Add command-line arguments for customization (--count, --client-id)
- [ ] Support multiple clients at once
- [ ] Add more diverse transaction patterns
- [ ] Include VAT calculations
- [ ] Add customer master data (like vendors)
- [ ] Generate PDF attachments for invoices
- [ ] Create matching entries for bank reconciliation

## Related Files

- **Script**: `backend/scripts/populate_demo_data.py`
- **Models**: `backend/app/models/`
- **Database Config**: `backend/app/database.py`
- **Environment**: `backend/.env`

## Contact

For issues or questions about this script, check the project documentation or raise an issue.
