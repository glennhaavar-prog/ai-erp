#!/usr/bin/env python3
"""
Populate 15 bank transactions for end-to-end testing
Client: 09409ccf-d23e-45e5-93b9-68add0b96277

Distribution:
- 10 unmatched (needs matching to ledger)
- 5 auto-matchable (KID/amount match)

Transaction types:
- Customer payments (credit)
- Supplier payments (debit)
- Bank fees (debit)
- Payroll (debit)
- VAT payments (debit)
"""
import asyncio
import random
import sys
import os
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models.bank_transaction import (
    BankTransaction,
    TransactionType,
    TransactionStatus
)

# Test client ID
TEST_CLIENT_ID = UUID("09409ccf-d23e-45e5-93b9-68add0b96277")

# Norwegian bank account (main business account)
BANK_ACCOUNT = "15064142857"
LEDGER_ACCOUNT = "1920"  # Chart of accounts number for bank account


async def create_customer_payments(db, matchable: bool = False):
    """Create customer payment transactions (money in)"""
    transactions = []
    
    # Customer names
    customers = [
        "ABC Handel AS",
        "Nordic Solutions AS",
        "Norsk Industri AS",
        "Bergen Bygg AS",
        "Trondheim Tech AS"
    ]
    
    count = 3 if matchable else 4
    
    for i in range(count):
        # Generate realistic amount
        amount = Decimal(random.randint(5000, 50000))
        
        # KID number for matchable transactions
        kid = None
        if matchable:
            kid = f"{random.randint(1000000, 9999999):07d}{random.randint(10, 99)}"
        
        transaction = BankTransaction(
            id=uuid4(),
            client_id=TEST_CLIENT_ID,
            transaction_date=datetime.now() - timedelta(days=random.randint(1, 20)),
            booking_date=datetime.now() - timedelta(days=random.randint(1, 20)),
            amount=amount,
            transaction_type=TransactionType.CREDIT,
            description=f"Betaling fra {random.choice(customers)}",
            reference_number=f"REF{random.randint(100000, 999999)}",
            kid_number=kid,
            counterparty_name=random.choice(customers),
            counterparty_account=f"{random.randint(1000, 9999)}{random.randint(10, 99)}{random.randint(10000, 99999)}",
            bank_account=BANK_ACCOUNT,
            ledger_account_number=LEDGER_ACCOUNT,
            status=TransactionStatus.UNMATCHED,
            ai_match_confidence=Decimal("85.0") if matchable else None,
            ai_match_reason="KID match found" if matchable else None,
            created_at=datetime.utcnow() - timedelta(hours=i)
        )
        db.add(transaction)
        transactions.append(transaction)
    
    return transactions


async def create_supplier_payments(db):
    """Create supplier payment transactions (money out)"""
    transactions = []
    
    suppliers = [
        "Elkjøp Nordic AS",
        "Telenor Norge AS",
        "Circle K Norge AS",
        "ISS Facility Services AS",
        "CloudNorge AS"
    ]
    
    for i in range(4):
        amount = Decimal(random.randint(2000, 30000))
        
        # Some have KID (payment reference)
        kid = None
        if random.random() > 0.5:
            kid = f"{random.randint(1000000, 9999999):07d}{random.randint(10, 99)}"
        
        transaction = BankTransaction(
            id=uuid4(),
            client_id=TEST_CLIENT_ID,
            transaction_date=datetime.now() - timedelta(days=random.randint(1, 25)),
            booking_date=datetime.now() - timedelta(days=random.randint(1, 25)),
            amount=-amount,  # Negative for money out
            transaction_type=TransactionType.DEBIT,
            description=f"Betaling til {random.choice(suppliers)}",
            reference_number=f"REF{random.randint(100000, 999999)}",
            kid_number=kid,
            counterparty_name=random.choice(suppliers),
            counterparty_account=f"{random.randint(1000, 9999)}{random.randint(10, 99)}{random.randint(10000, 99999)}",
            bank_account=BANK_ACCOUNT,
            ledger_account_number=LEDGER_ACCOUNT,
            status=TransactionStatus.UNMATCHED,
            created_at=datetime.utcnow() - timedelta(hours=i + 5)
        )
        db.add(transaction)
        transactions.append(transaction)
    
    return transactions


async def create_bank_fees(db):
    """Create bank fee transactions"""
    transactions = []
    
    fees = [
        ("Kontokredittavgift", 150.00),
        ("Bankkortavgift", 45.00),
    ]
    
    for i, (desc, fee) in enumerate(fees):
        transaction = BankTransaction(
            id=uuid4(),
            client_id=TEST_CLIENT_ID,
            transaction_date=datetime.now() - timedelta(days=random.randint(5, 15)),
            booking_date=datetime.now() - timedelta(days=random.randint(5, 15)),
            amount=-Decimal(fee),
            transaction_type=TransactionType.DEBIT,
            description=desc,
            reference_number=f"BANKFEE{random.randint(1000, 9999)}",
            kid_number=None,
            counterparty_name="DNB Bank ASA",
            counterparty_account=None,
            bank_account=BANK_ACCOUNT,
            ledger_account_number=LEDGER_ACCOUNT,
            status=TransactionStatus.UNMATCHED,
            ai_match_confidence=Decimal("72.0"),
            ai_match_reason="Bank fee pattern recognized",
            created_at=datetime.utcnow() - timedelta(hours=i + 10)
        )
        db.add(transaction)
        transactions.append(transaction)
    
    return transactions


async def create_payroll_payment(db):
    """Create payroll payment transaction"""
    transaction = BankTransaction(
        id=uuid4(),
        client_id=TEST_CLIENT_ID,
        transaction_date=datetime.now() - timedelta(days=10),
        booking_date=datetime.now() - timedelta(days=10),
        amount=-Decimal("185000.00"),
        transaction_type=TransactionType.DEBIT,
        description="Lønnsutbetaling januar 2026",
        reference_number=f"SALARY{datetime.now().strftime('%Y%m')}",
        kid_number=None,
        counterparty_name="Diverse ansatte",
        counterparty_account=None,
        bank_account=BANK_ACCOUNT,
        ledger_account_number=LEDGER_ACCOUNT,
        status=TransactionStatus.UNMATCHED,
        ai_match_confidence=Decimal("68.0"),
        ai_match_reason="Payroll pattern - verify against payroll records",
        created_at=datetime.utcnow() - timedelta(hours=12)
    )
    db.add(transaction)
    return [transaction]


async def create_vat_payment(db):
    """Create VAT payment transaction"""
    transaction = BankTransaction(
        id=uuid4(),
        client_id=TEST_CLIENT_ID,
        transaction_date=datetime.now() - timedelta(days=12),
        booking_date=datetime.now() - timedelta(days=12),
        amount=-Decimal("42750.00"),
        transaction_type=TransactionType.DEBIT,
        description="MVA Q4 2025 - Skatteetaten",
        reference_number=f"MVA{datetime.now().strftime('%Y%m')}",
        kid_number=None,
        counterparty_name="Skatteetaten",
        counterparty_account="97710000000",  # Skatteetaten account
        bank_account=BANK_ACCOUNT,
        ledger_account_number=LEDGER_ACCOUNT,
        status=TransactionStatus.UNMATCHED,
        ai_match_confidence=Decimal("75.0"),
        ai_match_reason="VAT payment pattern recognized",
        created_at=datetime.utcnow() - timedelta(hours=13)
    )
    db.add(transaction)
    return [transaction]


async def create_matchable_customer_payment(db):
    """Create easily matchable customer payment (high confidence KID match)"""
    transaction = BankTransaction(
        id=uuid4(),
        client_id=TEST_CLIENT_ID,
        transaction_date=datetime.now() - timedelta(days=3),
        booking_date=datetime.now() - timedelta(days=3),
        amount=Decimal("15450.00"),
        transaction_type=TransactionType.CREDIT,
        description="Betaling faktura #12845 - Nordic Solutions AS",
        reference_number=f"REF{random.randint(100000, 999999)}",
        kid_number="1234567890",  # Known KID for matching
        counterparty_name="Nordic Solutions AS",
        counterparty_account=f"{random.randint(1000, 9999)}{random.randint(10, 99)}{random.randint(10000, 99999)}",
        bank_account=BANK_ACCOUNT,
        ledger_account_number=LEDGER_ACCOUNT,
        status=TransactionStatus.UNMATCHED,
        ai_match_confidence=Decimal("95.0"),
        ai_match_reason="Exact KID match to invoice #12845",
        created_at=datetime.utcnow() - timedelta(hours=14)
    )
    db.add(transaction)
    return [transaction]


async def main():
    """Main function to populate bank transactions"""
    print("=" * 70)
    print("POPULATING BANK TRANSACTIONS FOR E2E TESTING")
    print("=" * 70)
    print(f"Client ID: {TEST_CLIENT_ID}")
    print(f"Bank Account: {BANK_ACCOUNT}")
    print()
    
    async with AsyncSessionLocal() as db:
        all_transactions = []
        
        # Create unmatched transactions (10 total)
        print("Creating unmatched transactions...")
        unmatched = []
        unmatched.extend(await create_customer_payments(db, matchable=False))  # 4
        unmatched.extend(await create_supplier_payments(db))  # 4
        unmatched.extend(await create_payroll_payment(db))  # 1
        unmatched.extend(await create_vat_payment(db))  # 1
        
        print(f"  ✅ Created {len(unmatched)} unmatched transactions")
        
        # Create matchable transactions (5 total)
        print("\nCreating auto-matchable transactions...")
        matchable = []
        matchable.extend(await create_customer_payments(db, matchable=True))  # 3
        matchable.extend(await create_bank_fees(db))  # 2
        # matchable.extend(await create_matchable_customer_payment(db))  # 1 (extra high-confidence)
        
        print(f"  ✅ Created {len(matchable)} auto-matchable transactions")
        
        all_transactions = unmatched + matchable
        
        await db.commit()
        
        print()
        print("=" * 70)
        print("✅ BANK TRANSACTIONS CREATED SUCCESSFULLY")
        print("=" * 70)
        print(f"Total transactions: {len(all_transactions)}")
        print(f"  - Unmatched: {len(unmatched)}")
        print(f"  - Auto-matchable: {len(matchable)}")
        print()
        
        # Calculate totals
        total_in = sum(float(t.amount) for t in all_transactions if t.transaction_type == TransactionType.CREDIT)
        total_out = sum(float(t.amount) for t in all_transactions if t.transaction_type == TransactionType.DEBIT)
        net = total_in + total_out
        
        print(f"Transaction summary:")
        print(f"  - Money in (credit): {total_in:>12,.2f} NOK ({sum(1 for t in all_transactions if t.transaction_type == TransactionType.CREDIT)} txns)")
        print(f"  - Money out (debit): {total_out:>12,.2f} NOK ({sum(1 for t in all_transactions if t.transaction_type == TransactionType.DEBIT)} txns)")
        print(f"  - Net movement:      {net:>12,.2f} NOK")
        print()
        
        # Transaction types
        print("Transaction types:")
        print(f"  - Customer payments: {sum(1 for t in all_transactions if 'Betaling fra' in t.description)}")
        print(f"  - Supplier payments: {sum(1 for t in all_transactions if 'Betaling til' in t.description)}")
        print(f"  - Bank fees:         {sum(1 for t in all_transactions if 'avgift' in t.description.lower())}")
        print(f"  - Payroll:           {sum(1 for t in all_transactions if 'Lønn' in t.description)}")
        print(f"  - VAT:               {sum(1 for t in all_transactions if 'MVA' in t.description)}")
        print()
        
        print("Test with:")
        print(f'  curl "http://localhost:8000/api/bank-recon/unmatched?client_id={TEST_CLIENT_ID}&account=1920&period_start=2026-01-01&period_end=2026-02-28"')


if __name__ == "__main__":
    asyncio.run(main())
