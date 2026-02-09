#!/usr/bin/env python3
"""
Generate Bank Reconciliation Demo Data

Creates 100 bank transactions:
- 90 auto-matched to vendor invoices
- 10 unmatched (for manual review demo)
"""
import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models import Client, VendorInvoice, BankTransaction


async def generate_bank_transactions(session: AsyncSession):
    """Generate 100 bank transactions (90 matched, 10 unmatched)"""
    
    print("=" * 60)
    print("🏦 Generating Bank Reconciliation Demo Data")
    print("=" * 60)
    
    # Get demo clients
    result = await session.execute(
        select(Client).where(Client.is_demo == True).limit(10)
    )
    clients = result.scalars().all()
    
    if not clients:
        print("❌ No demo clients found!")
        return
    
    print(f"✅ Found {len(clients)} demo clients")
    
    # Get unpaid vendor invoices (for matching)
    result = await session.execute(
        select(VendorInvoice)
        .where(VendorInvoice.payment_status == "UNPAID")
        .where(VendorInvoice.client_id.in_([c.id for c in clients]))
        .limit(90)
    )
    unpaid_invoices = result.scalars().all()
    
    print(f"✅ Found {len(unpaid_invoices)} unpaid invoices for matching")
    
    transactions_created = 0
    matched_count = 0
    unmatched_count = 0
    
    # Create 90 matched transactions (one per invoice)
    for invoice in unpaid_invoices[:90]:
        # Payment date after invoice date
        payment_date = invoice.invoice_date + timedelta(days=random.randint(5, 30))
        
        transaction = BankTransaction(
            id=uuid4(),
            client_id=invoice.client_id,
            transaction_date=payment_date,
            amount=-invoice.total_amount,  # Negative = outgoing
            transaction_type="DEBIT",
            description=f"Betaling faktura {invoice.invoice_number}",
            reference_number=invoice.invoice_number,
            bank_account="12345678901",  # Demo account
            status="MATCHED",
            ai_matched_invoice_id=invoice.id,
            ai_match_confidence=Decimal("95.0"),
            matched_at=datetime.now(),
            posted_to_ledger=True
        )
        session.add(transaction)
        matched_count += 1
        transactions_created += 1
        
        if transactions_created % 20 == 0:
            print(f"  Created {transactions_created}/100 transactions...")
    
    # Create 10 unmatched transactions
    unmatched_descriptions = [
        "Overføring til sparing",
        "Uttak minibank",
        "Lønnsutbetaling",
        "Depositum kontorlokale",
        "Refusjon fra kunde",
        "Moms til skatteetaten",
        "Renter fra banken",
        "Utbytte fra investering",
        "Diverse kontantuttak",
        "Bankgebyr konto"
    ]
    
    for i in range(10):
        client = random.choice(clients)
        amount = Decimal(random.randint(-50000, -1000))
        trans_date = datetime.now().date() - timedelta(days=random.randint(1, 60))
        
        transaction = BankTransaction(
            id=uuid4(),
            client_id=client.id,
            transaction_date=trans_date,
            amount=amount,
            transaction_type="DEBIT",
            description=unmatched_descriptions[i],
            reference_number=f"REF-{random.randint(100000, 999999)}",
            bank_account="12345678901",
            status="UNMATCHED",
            posted_to_ledger=False
        )
        session.add(transaction)
        unmatched_count += 1
        transactions_created += 1
    
    print(f"  Created {transactions_created}/100 transactions...")
    
    # Commit
    await session.commit()
    
    print(f"\n✅ Successfully created {transactions_created} bank transactions")
    print(f"   - Matched: {matched_count} (90%)")
    print(f"   - Unmatched: {unmatched_count} (10%)")
    
    # Verify
    result = await session.execute(select(func.count(BankTransaction.id)))
    total = result.scalar()
    
    result = await session.execute(
        select(func.count(BankTransaction.id))
        .where(BankTransaction.status == "MATCHED")
    )
    reconciled = result.scalar()
    
    result = await session.execute(
        select(func.count(BankTransaction.id))
        .where(BankTransaction.status == "UNMATCHED")
    )
    unreconciled = result.scalar()
    
    print(f"\n📊 Total bank transactions: {total}")
    print(f"📊 Reconciled: {reconciled}")
    print(f"📊 Unreconciled: {unreconciled}")


async def main():
    async with AsyncSessionLocal() as session:
        try:
            await generate_bank_transactions(session)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await session.rollback()
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
