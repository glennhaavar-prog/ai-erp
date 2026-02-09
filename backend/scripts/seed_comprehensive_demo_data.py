#!/usr/bin/env python3
"""
Seed comprehensive demo data for all 15 clients
- Vendor invoices (50+ per client)
- Customer invoices (30+ per client)
- Bank transactions (100+ per client)
- General ledger entries
- Realistic Norwegian data
"""
import asyncio
import random
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models import (
    Client, VendorInvoice, CustomerInvoice, GeneralLedger, 
    GeneralLedgerLine
)

# Norwegian vendor names
VENDORS = [
    "Telenor Norge AS", "Elkjøp Nordic AS", "Coop Norge SA",
    "Rema 1000 AS", "Kiwi Norge AS", "Circle K Norge AS",
    "Uno-X Energi AS", "Norsk Tipping AS", "Posten Norge AS",
    "Bring AS", "DHL Express Norway AS", "Schenker AS",
    "Staples Norge AS", "Office Partner AS", "Lyreco Norge AS",
    "ISS Facility Services AS", "Vakt Service AS", "Renhold Bodø AS",
    "Sparebanken Nord-Norge", "DNB Bank ASA", "Nordea Bank Norge ASA",
    "Advokatfirma Nord", "Revisorgruppen AS", "BDO Norge AS",
    "Husleie Bodø AS", "Næringsmegling AS", "Eiendomsdrift Nord AS",
    "Strømberg Elektro AS", "VVS Nord AS", "Malermester Hansen AS",
    "Kontorrekvisita AS", "Papir og Kontor AS", "Trykkservice Bodø AS",
    "Datasikkerhet Norge AS", "IT-Support Nord AS", "CloudNorge AS"
]

# Norwegian customer names
CUSTOMERS = [
    "Bodø Kommune", "Nordland Fylkeskommune", "NAV Bodø",
    "Salten Regionråd", "Bodø Havn KF", "Bodø Lufthavn AS",
    "Avinor AS", "Nordlandssykehuset", "Helse Nord RHF",
    "Universitetet i Nordland", "Nord Universitet", "Bodø Videregående Skole",
    "Norsk Hydro ASA", "Equinor ASA", "Statkraft AS",
    "Elkem ASA", "Alcoa Norway AS", "Rana Gruber AS",
    "Sparebank 1 Nord-Norge", "Arctic Securities AS", "Nordea Markets",
    "Hurtigruten Group AS", "Widerøe Flyveselskap AS", "SAS Norge AS",
    "Thon Hotels AS", "Scandic Hotels AS", "Clarion Hotel Bodø",
    "Coop Marked Bodø", "Amfi Storsenter AS", "City Nord AS"
]

# Account mappings (NS 4102)
EXPENSE_ACCOUNTS = [
    (4000, "Varekjøp"),
    (4300, "Elektrisitet"),
    (5000, "Lønninger"),
    (5400, "Arbeidsgiveravgift"),
    (6000, "Avskrivninger"),
    (6100, "Vedlikehold"),
    (6300, "Leie lokaler"),
    (6340, "Leasing"),
    (6540, "Kontorrekvisita"),
    (6700, "Regnskapsføring"),
    (6800, "Kontingenter"),
    (6900, "Telefon/data"),
    (7140, "Reisekostnader"),
    (7320, "Reklamekostnader"),
    (7500, "Forsikringer"),
    (7700, "Bank- og kortgebyr")
]

REVENUE_ACCOUNTS = [
    (3000, "Salgsinntekter"),
    (3100, "Konsulentinntekter"),
    (3400, "Prosjektinntekter")
]

BANK_DESCRIPTIONS = [
    "Varekjøp butikk", "Strøm fjordkraft", "Lønn medarbeider",
    "Husleie kontor", "Telefon telenor", "Internett fiber",
    "Forsikring bedrift", "Regnskapsfører", "Revisjon årsoppgjør",
    "Kontorrekvisita", "Reise Oslo", "Hotell overnatting",
    "Drivstoff bil", "Parkering", "Bomavgift autopass",
    "Kundefaktura betalt", "Leverandørfaktura", "MVA til staten"
]


async def create_vendor_invoices(session: AsyncSession, client_id: str, count: int = 60):
    """Create realistic vendor invoices"""
    invoices = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(count):
        invoice_date = start_date + timedelta(days=random.randint(0, 365))
        due_date = invoice_date + timedelta(days=random.choice([14, 30, 45]))
        
        # Random account
        account_no, description = random.choice(EXPENSE_ACCOUNTS)
        net_amount = Decimal(str(random.randint(500, 50000)))
        
        # 25% VAT for most, 0% for salaries/fees
        if account_no in [5000, 5400, 6000, 6300, 6800, 7500, 7700]:
            vat_amount = Decimal("0")
        else:
            vat_amount = (net_amount * Decimal("0.25")).quantize(Decimal("0.01"))
        
        total_amount = net_amount + vat_amount
        
        invoice = VendorInvoice(
            id=str(uuid4()),
            client_id=client_id,
            vendor_id=None,  # Will be set when vendor system is implemented
            invoice_number=f"INV-{invoice_date.year}-{random.randint(1000, 9999)}",
            invoice_date=invoice_date.date(),
            due_date=due_date.date(),
            amount_excl_vat=net_amount,
            vat_amount=vat_amount,
            total_amount=total_amount,
            payment_status="paid" if random.random() > 0.2 else "unpaid",
            ai_confidence_score=random.randint(85, 99),
            ai_booking_suggestion={
                "account": account_no,
                "description": description,
                "vendor": random.choice(VENDORS)
            },
            created_at=datetime.now()
        )
        invoices.append(invoice)
    
    session.add_all(invoices)
    return invoices


async def create_customer_invoices(session: AsyncSession, client_id: str, count: int = 40):
    """Create realistic customer invoices"""
    invoices = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(count):
        invoice_date = start_date + timedelta(days=random.randint(0, 365))
        due_date = invoice_date + timedelta(days=random.choice([14, 30]))
        
        # Revenue account with output VAT
        account_no, description = random.choice(REVENUE_ACCOUNTS)
        net_amount = Decimal(str(random.randint(5000, 100000)))
        vat_amount = (net_amount * Decimal("0.25")).quantize(Decimal("0.01"))
        total_amount = net_amount + vat_amount
        
        invoice = CustomerInvoice(
            id=str(uuid4()),
            client_id=client_id,
            customer_name=random.choice(CUSTOMERS),
            invoice_number=f"SALE-{invoice_date.year}-{1000+i}",
            invoice_date=invoice_date.date(),
            due_date=due_date.date(),
            amount_excl_vat=net_amount,
            vat_amount=vat_amount,
            total_amount=total_amount,
            description=description,
            payment_status="paid" if random.random() > 0.15 else "unpaid",
            created_at=datetime.now()
        )
        invoices.append(invoice)
    
    session.add_all(invoices)
    return invoices


async def create_bank_transactions(session: AsyncSession, client_id: str, count: int = 120):
    """Create realistic bank transactions"""
    transactions = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(count):
        trans_date = start_date + timedelta(days=random.randint(0, 365))
        
        # Mix of income and expenses
        is_income = random.random() < 0.3  # 30% income, 70% expenses
        
        if is_income:
            amount = Decimal(str(random.randint(10000, 150000)))
            description = f"Betaling {random.choice(CUSTOMERS)}"
        else:
            amount = -Decimal(str(random.randint(500, 50000)))
            description = random.choice(BANK_DESCRIPTIONS)
        
        # Create GL entry for bank transaction
        trans_date_obj = trans_date.date()
        period = trans_date_obj.strftime("%Y-%m")
        fiscal_year = trans_date_obj.year
        
        gl_entry = GeneralLedger(
            id=str(uuid4()),
            client_id=client_id,
            entry_date=trans_date_obj,
            accounting_date=trans_date_obj,
            period=period,
            fiscal_year=fiscal_year,
            voucher_number=f"BANK-{trans_date.year}-{1000+i}",
            voucher_series="B",  # B for bank transactions
            description=description,
            source_type="bank_transaction",
            created_by_type="ai_agent"
        )
        session.add(gl_entry)
        
        # Debit/Credit lines
        if amount > 0:
            # Income: Debit bank, Credit revenue
            debit_line = GeneralLedgerLine(
                id=str(uuid4()),
                general_ledger_id=gl_entry.id,
                line_number=1,
                account_number="1920",
                debit_amount=amount,
                credit_amount=Decimal("0")
            )
            credit_account = random.choice([3000, 3100, 3400])
            credit_line = GeneralLedgerLine(
                id=str(uuid4()),
                general_ledger_id=gl_entry.id,
                line_number=2,
                account_number=str(credit_account),
                debit_amount=Decimal("0"),
                credit_amount=amount
            )
        else:
            # Expense: Debit expense, Credit bank
            expense_account = random.choice([a[0] for a in EXPENSE_ACCOUNTS])
            debit_line = GeneralLedgerLine(
                id=str(uuid4()),
                general_ledger_id=gl_entry.id,
                line_number=1,
                account_number=str(expense_account),
                debit_amount=abs(amount),
                credit_amount=Decimal("0")
            )
            credit_line = GeneralLedgerLine(
                id=str(uuid4()),
                general_ledger_id=gl_entry.id,
                line_number=2,
                account_number="1920",
                debit_amount=Decimal("0"),
                credit_amount=abs(amount)
            )
        
        session.add_all([debit_line, credit_line])
        transactions.append(gl_entry)
    
    return transactions


async def recalculate_account_balances(session: AsyncSession, client_id: str):
    """Count unique accounts used (balances are calculated on-demand from GL)"""
    
    # Get all GL lines for this client
    result = await session.execute(
        select(func.count(func.distinct(GeneralLedgerLine.account_number)))
        .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
        .where(GeneralLedger.client_id == client_id)
    )
    
    account_count = result.scalar()
    return account_count


async def seed_client_data(client_id: str, client_name: str):
    """Seed comprehensive data for one client"""
    async with AsyncSessionLocal() as session:
        try:
            print(f"\n📊 Seeding data for: {client_name}")
            
            # Create vendor invoices
            vendor_invoices = await create_vendor_invoices(session, client_id, 60)
            print(f"  ✅ Created {len(vendor_invoices)} vendor invoices")
            
            # Create customer invoices
            customer_invoices = await create_customer_invoices(session, client_id, 40)
            print(f"  ✅ Created {len(customer_invoices)} customer invoices")
            
            # Create bank transactions with GL entries
            bank_transactions = await create_bank_transactions(session, client_id, 120)
            print(f"  ✅ Created {len(bank_transactions)} bank transactions")
            
            # Count unique accounts
            account_count = await recalculate_account_balances(session, client_id)
            print(f"  ✅ Using {account_count} unique accounts")
            
            await session.commit()
            print(f"  ✅ {client_name} complete!")
            
        except Exception as e:
            await session.rollback()
            print(f"  ❌ Error seeding {client_name}: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """Seed all demo clients with comprehensive data"""
    async with AsyncSessionLocal() as session:
        # Get demo clients only
        result = await session.execute(
            select(Client).where(Client.is_demo == True)
        )
        clients = result.scalars().all()
        
        print(f"\n{'='*60}")
        print(f"🚀 Comprehensive Demo Data Seeding")
        print(f"{'='*60}")
        print(f"Found {len(clients)} demo clients to populate")
        
        for client in clients[:15]:  # Limit to 15 clients
            await seed_client_data(str(client.id), client.name)
        
        print(f"\n{'='*60}")
        print(f"✅ All {min(len(clients), 15)} clients populated!")
        print(f"{'='*60}")
        print(f"\n📈 Total data created (per client):")
        print(f"  • 60 vendor invoices")
        print(f"  • 40 customer invoices")
        print(f"  • 120 bank transactions (240 GL lines)")
        print(f"  • Account balances recalculated")
        print(f"\n💾 Grand total across all clients:")
        print(f"  • {min(len(clients), 15) * 60} vendor invoices")
        print(f"  • {min(len(clients), 15) * 40} customer invoices")
        print(f"  • {min(len(clients), 15) * 120} bank transactions")
        print(f"  • {min(len(clients), 15) * 240} GL lines")


if __name__ == "__main__":
    asyncio.run(main())
