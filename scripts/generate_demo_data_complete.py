#!/usr/bin/env python3
"""
Complete Demo Data Generator - All Workflows

Generates realistic mock data for complete A-Z demo:
1. Multiple clients
2. Vendor invoices (various statuses)
3. Customer invoices
4. Bank transactions (matched & unmatched)
5. Chart of accounts
6. General ledger entries
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
    Tenant, Client, User, Vendor, VendorInvoice, CustomerInvoice,
    BankTransaction, Account, GeneralLedger
)
from app.models.bank_transaction import TransactionType, TransactionStatus

# Database URL
DATABASE_URL = "postgresql+asyncpg://erp_user:erp_password@localhost:5432/ai_erp"


# Sample data
NORWEGIAN_COMPANIES = [
    ("Telenor Norge AS", "976820037"),
    ("DNB Bank ASA", "984851006"),
    ("Elkjøp Nordic AS", "981593522"),
    ("Power Norge AS", "991123456"),
    ("Fjordkraft ASA", "918942873"),
    ("Posten Norge AS", "984661185"),
    ("Rema 1000 AS", "987654321"),
    ("Kiwi Norge AS", "998765432"),
    ("Norgesgruppen ASA", "886203702"),
    ("Schibsted ASA", "992476022"),
]

CUSTOMER_COMPANIES = [
    ("Acme Solutions AS", "912345678"),
    ("Nordic Tech AS", "923456789"),
    ("Fjord Consulting AS", "934567890"),
    ("Arctic Services AS", "945678901"),
    ("Coastal Trading AS", "956789012"),
]


async def generate_demo_data():
    """Generate complete demo dataset"""
    
    print("🚀 Generating complete demo data...")
    
    # Create engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Create/Get Tenant
        print("\n1️⃣ Creating tenant...")
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
        
        # 2. Create Clients
        print("\n2️⃣ Creating clients...")
        clients = []
        
        for i, (name, org_no) in enumerate([
            ("Fjellby Handel AS", "991234567"),
            ("Nordlys Consulting AS", "992345678"),
            ("Kystfisk AS", "993456789"),
        ], start=1):
            client = Client(
                tenant_id=tenant.id,
                client_number=f"KL{i:04d}",
                name=name,
                org_number=org_no,
                fiscal_year_start=1,
                base_currency="NOK"
            )
            session.add(client)
            clients.append(client)
        
        await session.flush()
        print(f"   ✅ Created {len(clients)} clients")
        
        # 3. Create Vendors
        print("\n3️⃣ Creating vendors...")
        vendors = []
        
        vendor_counter = 1
        for client in clients:
            for vendor_name, vendor_org in random.sample(NORWEGIAN_COMPANIES, 5):
                vendor = Vendor(
                    client_id=client.id,
                    vendor_number=f"V{vendor_counter:04d}",
                    name=vendor_name,
                    org_number=vendor_org,
                    email=f"faktura@{vendor_name.lower().replace(' ', '')}.no",
                    account_number=f"{random.randint(1000000000, 9999999999)}"
                )
                session.add(vendor)
                vendors.append(vendor)
                vendor_counter += 1
        
        await session.flush()
        print(f"   ✅ Created {len(vendors)} vendors")
        
        # 4. Create Vendor Invoices
        print("\n4️⃣ Creating vendor invoices...")
        vendor_invoices = []
        
        for client in clients:
            client_vendors = [v for v in vendors if v.client_id == client.id]
            
            for i in range(15):  # 15 invoices per client
                vendor = random.choice(client_vendors)
                invoice_date = datetime.now() - timedelta(days=random.randint(1, 90))
                due_date = invoice_date + timedelta(days=14)
                
                amount_excl = Decimal(str(random.randint(1000, 50000)))
                vat = amount_excl * Decimal("0.25")
                total = amount_excl + vat
                
                # Mix of statuses
                statuses = ['pending', 'pending', 'pending', 'auto_approved', 'reviewed']
                payment_statuses = ['unpaid', 'unpaid', 'unpaid', 'paid']
                
                invoice = VendorInvoice(
                    client_id=client.id,
                    vendor_id=vendor.id,
                    vendor_name=vendor.name,
                    invoice_number=f"F{random.randint(100000, 999999)}",
                    invoice_date=invoice_date.date(),
                    due_date=due_date.date(),
                    kid_number=f"{random.randint(1000000000, 9999999999)}",
                    amount_excl_vat=amount_excl,
                    vat_amount=vat,
                    total_amount=total,
                    currency="NOK",
                    payment_status=random.choice(payment_statuses),
                    review_status=random.choice(statuses),
                    ai_confidence_score=random.randint(65, 99),
                    description=f"Faktura fra {vendor.name}"
                )
                session.add(invoice)
                vendor_invoices.append(invoice)
        
        await session.flush()
        print(f"   ✅ Created {len(vendor_invoices)} vendor invoices")
        
        # 5. Create Customer Invoices
        print("\n5️⃣ Creating customer invoices...")
        customer_invoices = []
        
        for client in clients:
            for i in range(10):  # 10 customer invoices per client
                customer_name, customer_org = random.choice(CUSTOMER_COMPANIES)
                invoice_date = datetime.now() - timedelta(days=random.randint(1, 60))
                due_date = invoice_date + timedelta(days=30)
                
                amount_excl = Decimal(str(random.randint(5000, 100000)))
                vat = amount_excl * Decimal("0.25")
                total = amount_excl + vat
                
                payment_statuses = ['unpaid', 'unpaid', 'paid', 'paid']
                
                invoice = CustomerInvoice(
                    client_id=client.id,
                    customer_name=customer_name,
                    customer_org_number=customer_org,
                    invoice_number=f"KF{random.randint(1000, 9999)}",
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
        
        # 6. Create Bank Transactions
        print("\n6️⃣ Creating bank transactions...")
        bank_transactions = []
        
        for client in clients:
            # Get client's invoices for matching
            client_vendor_invoices = [inv for inv in vendor_invoices if inv.client_id == client.id]
            client_customer_invoices = [inv for inv in customer_invoices if inv.client_id == client.id]
            
            # Generate CREDIT transactions (payments IN from customers)
            for invoice in random.sample(client_customer_invoices, min(5, len(client_customer_invoices))):
                transaction_date = invoice.invoice_date + timedelta(days=random.randint(5, 45))
                
                txn = BankTransaction(
                    client_id=client.id,
                    bank_account="12345678901",
                    transaction_date=datetime.combine(transaction_date, datetime.min.time()),
                    amount=invoice.total_amount,
                    transaction_type=TransactionType.CREDIT,
                    description=f"Betaling faktura {invoice.invoice_number}",
                    kid_number=invoice.kid_number,
                    counterparty_name=invoice.customer_name,
                    status=TransactionStatus.UNMATCHED  # Will be matched by AI
                )
                session.add(txn)
                bank_transactions.append(txn)
            
            # Generate DEBIT transactions (payments OUT to vendors)
            for invoice in random.sample(client_vendor_invoices, min(5, len(client_vendor_invoices))):
                transaction_date = invoice.due_date + timedelta(days=random.randint(-3, 7))
                
                txn = BankTransaction(
                    client_id=client.id,
                    bank_account="12345678901",
                    transaction_date=datetime.combine(transaction_date, datetime.min.time()),
                    amount=invoice.total_amount,
                    transaction_type=TransactionType.DEBIT,
                    description=f"Betalt faktura {invoice.invoice_number}",
                    kid_number=invoice.kid_number,
                    counterparty_name=invoice.vendor_name,
                    status=TransactionStatus.UNMATCHED
                )
                session.add(txn)
                bank_transactions.append(txn)
            
            # Add some unmatched transactions
            for i in range(3):
                txn_type = random.choice([TransactionType.CREDIT, TransactionType.DEBIT])
                amount = Decimal(str(random.randint(500, 10000)))
                
                descriptions = [
                    "Overføring kontanter",
                    "Kortavgift",
                    "Bankkostnader",
                    "Renter",
                    "Andre kostnader"
                ]
                
                txn = BankTransaction(
                    client_id=client.id,
                    bank_account="12345678901",
                    transaction_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                    amount=amount,
                    transaction_type=txn_type,
                    description=random.choice(descriptions),
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
        print(f"   • {len(clients)} clients")
        print(f"   • {len(vendors)} vendors")
        print(f"   • {len(vendor_invoices)} vendor invoices")
        print(f"   • {len(customer_invoices)} customer invoices")
        print(f"   • {len(bank_transactions)} bank transactions")
        print("\n🎉 Ready for full A-Z demo!")


if __name__ == "__main__":
    asyncio.run(generate_demo_data())
