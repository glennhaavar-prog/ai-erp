#!/usr/bin/env python3
"""
Simple Demo Data Generator - Focus on working demo

Generates minimal realistic data for demo:
- 1 client
- 5 vendors
- 10 vendor invoices (mixed statuses)
- 5 customer invoices
- 10 bank transactions
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
from uuid import uuid4, UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.models import (
    Tenant, Client, Vendor, VendorInvoice, CustomerInvoice, BankTransaction
)
from app.models.bank_transaction import TransactionType, TransactionStatus

# Database URL
DATABASE_URL = "postgresql+asyncpg://erp_user:erp_password@localhost:5432/ai_erp"

# Sample data
VENDORS = [
    ("Telenor Norge AS", "976820037"),
    ("DNB Bank ASA", "984851006"),
    ("Posten Norge AS", "984661185"),
    ("Fjordkraft ASA", "918942873"),
    ("Rema 1000 AS", "987654321"),
]

CUSTOMERS = [
    ("Acme Solutions AS", "912345678"),
    ("Nordic Tech AS", "923456789"),
    ("Fjord Consulting AS", "934567890"),
]


async def generate_demo_data():
    """Generate simple demo dataset"""
    
    print("🚀 Generating demo data...")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Get or create tenant
        print("\n1️⃣ Setting up tenant...")
        tenant_query = select(Tenant).limit(1)
        result = await session.execute(tenant_query)
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            tenant = Tenant(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                name="Demo Regnskapsbyrå AS",
                org_number="987654321",
                email="demo@kontali.no"
            )
            session.add(tenant)
            await session.flush()
        
        print(f"   ✅ Tenant: {tenant.name}")
        
        # 2. Get or create demo client
        print("\n2️⃣ Setting up client...")
        client_query = select(Client).where(Client.tenant_id == tenant.id).limit(1)
        result = await session.execute(client_query)
        client = result.scalar_one_or_none()
        
        if not client:
            client = Client(
                tenant_id=tenant.id,
                client_number="KL0001",
                name="Demo Handel AS",
                org_number="991234567",
                fiscal_year_start=1,
                base_currency="NOK"
            )
            session.add(client)
            await session.flush()
        
        print(f"   ✅ Client: {client.name}")
        
        # 3. Create vendors
        print("\n3️⃣ Creating vendors...")
        vendors = []
        
        for i, (name, org_no) in enumerate(VENDORS, start=1):
            vendor = Vendor(
                client_id=client.id,
                vendor_number=f"V{i:04d}",
                name=name,
                org_number=org_no,
                email=f"faktura@vendor{i}.no",
                account_number=f"{2400 + i}"  # 2401, 2402, etc. (short account numbers)
            )
            session.add(vendor)
            vendors.append(vendor)
        
        await session.flush()
        print(f"   ✅ Created {len(vendors)} vendors")
        
        # 4. Create vendor invoices
        print("\n4️⃣ Creating vendor invoices...")
        vendor_invoices = []
        
        for i in range(10):
            vendor = random.choice(vendors)
            invoice_date = datetime.now() - timedelta(days=random.randint(1, 60))
            due_date = invoice_date + timedelta(days=14)
            
            amount_excl = Decimal(str(random.randint(1000, 25000)))
            vat = amount_excl * Decimal("0.25")
            total = amount_excl + vat
            
            statuses = ['pending', 'pending', 'auto_approved', 'reviewed']
            payment_statuses = ['unpaid', 'unpaid', 'paid']
            
            invoice = VendorInvoice(
                client_id=client.id,
                vendor_id=vendor.id,
                invoice_number=f"F{100000 + i}",
                invoice_date=invoice_date.date(),
                due_date=due_date.date(),
                amount_excl_vat=amount_excl,
                vat_amount=vat,
                total_amount=total,
                currency="NOK",
                payment_status=random.choice(payment_statuses),
                review_status=random.choice(statuses),
                ai_confidence_score=random.randint(70, 98)
            )
            session.add(invoice)
            vendor_invoices.append(invoice)
        
        await session.flush()
        print(f"   ✅ Created {len(vendor_invoices)} vendor invoices")
        
        # 5. Create customer invoices
        print("\n5️⃣ Creating customer invoices...")
        customer_invoices = []
        
        for i in range(5):
            customer_name, customer_org = random.choice(CUSTOMERS)
            invoice_date = datetime.now() - timedelta(days=random.randint(1, 45))
            due_date = invoice_date + timedelta(days=30)
            
            amount_excl = Decimal(str(random.randint(5000, 50000)))
            vat = amount_excl * Decimal("0.25")
            total = amount_excl + vat
            
            payment_statuses = ['unpaid', 'unpaid', 'paid']
            
            invoice = CustomerInvoice(
                client_id=client.id,
                customer_name=customer_name,
                customer_org_number=customer_org,
                invoice_number=f"KF{1000 + i}",
                invoice_date=invoice_date.date(),
                due_date=due_date.date(),
                kid_number=f"{random.randint(1000000000, 9999999999)}",
                amount_excl_vat=amount_excl,
                vat_amount=vat,
                total_amount=total,
                currency="NOK",
                payment_status=random.choice(payment_statuses),
                description=f"Faktura til {customer_name}"
            )
            session.add(invoice)
            customer_invoices.append(invoice)
        
        await session.flush()
        print(f"   ✅ Created {len(customer_invoices)} customer invoices")
        
        # 6. Create bank transactions
        print("\n6️⃣ Creating bank transactions...")
        bank_transactions = []
        
        # CREDIT transactions (payments IN from customers)
        for invoice in customer_invoices[:3]:
            transaction_date = invoice.invoice_date + timedelta(days=random.randint(5, 25))
            
            txn = BankTransaction(
                client_id=client.id,
                bank_account="12345678901",
                transaction_date=datetime.combine(transaction_date, datetime.min.time()),
                amount=invoice.total_amount,
                transaction_type=TransactionType.CREDIT,
                description=f"Betaling faktura {invoice.invoice_number}",
                kid_number=invoice.kid_number if hasattr(invoice, 'kid_number') else None,
                counterparty_name=invoice.customer_name,
                status=TransactionStatus.UNMATCHED
            )
            session.add(txn)
            bank_transactions.append(txn)
        
        # DEBIT transactions (payments OUT to vendors)
        for i, invoice in enumerate(vendor_invoices[:4]):
            vendor = vendors[i % len(vendors)]
            transaction_date = invoice.due_date + timedelta(days=random.randint(-2, 5))
            
            txn = BankTransaction(
                client_id=client.id,
                bank_account="12345678901",
                transaction_date=datetime.combine(transaction_date, datetime.min.time()),
                amount=invoice.total_amount,
                transaction_type=TransactionType.DEBIT,
                description=f"Betalt faktura {invoice.invoice_number}",
                kid_number=None,  # VendorInvoice doesn't have kid_number
                counterparty_name=vendor.name,
                status=TransactionStatus.UNMATCHED
            )
            session.add(txn)
            bank_transactions.append(txn)
        
        # Some unmatched transactions
        for i in range(3):
            txn_type = random.choice([TransactionType.CREDIT, TransactionType.DEBIT])
            amount = Decimal(str(random.randint(500, 5000)))
            
            txn = BankTransaction(
                client_id=client.id,
                bank_account="12345678901",
                transaction_date=datetime.now() - timedelta(days=random.randint(1, 20)),
                amount=amount,
                transaction_type=txn_type,
                description=random.choice([
                    "Kortavgift",
                    "Bankkostnader",
                    "Renter",
                    "Diverse kostnader"
                ]),
                status=TransactionStatus.UNMATCHED
            )
            session.add(txn)
            bank_transactions.append(txn)
        
        await session.flush()
        print(f"   ✅ Created {len(bank_transactions)} bank transactions")
        
        # Commit all
        await session.commit()
        print("\n✅ Demo data generation complete!")
        print(f"\n📊 Summary:")
        print(f"   • 1 client: {client.name}")
        print(f"   • {len(vendors)} vendors")
        print(f"   • {len(vendor_invoices)} vendor invoices")
        print(f"   • {len(customer_invoices)} customer invoices")
        print(f"   • {len(bank_transactions)} bank transactions")
        print("\n🎉 Ready for demo on localhost:3000!")


if __name__ == "__main__":
    asyncio.run(generate_demo_data())
