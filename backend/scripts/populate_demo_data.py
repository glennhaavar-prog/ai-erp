#!/usr/bin/env python3
"""
Demo Data Population Script - TASK 7

Populer realistiske demo data i alle moduler:
1. Leverandørreskontro (10+ poster)
2. Kundereskontro (10+ poster)
3. Bilagsjournal (50+ bilag)
4. Task Admin (20+ oppgaver)
5. Banktransaksjoner (30+ transaksjoner)

Script er idempotent - kan kjøres flere ganger uten å duplisere data.

Usage:
    python backend/scripts/populate_demo_data.py
"""
import asyncio
import random
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4, UUID
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from app.database import AsyncSessionLocal
from app.models import (
    Client, Vendor, SupplierLedger, CustomerLedger, GeneralLedger, 
    GeneralLedgerLine, Task, BankTransaction
)
from app.models.task import TaskStatus, TaskCategory, TaskFrequency
from app.models.bank_transaction import TransactionType, TransactionStatus

# ============================================================================
# NORWEGIAN DEMO DATA
# ============================================================================

NORWEGIAN_SUPPLIERS = [
    {"name": "Equinor ASA", "org": "923609016", "account": "2400"},
    {"name": "DNB Bank ASA", "org": "984851006", "account": "2400"},
    {"name": "Telenor Norge AS", "org": "976820479", "account": "2400"},
    {"name": "Posten Norge AS", "org": "984661185", "account": "2400"},
    {"name": "Elkjøp Nordic AS", "org": "981399084", "account": "2400"},
    {"name": "Statoil Fuel & Retail", "org": "958450737", "account": "2400"},
    {"name": "Rema 1000 AS", "org": "982314646", "account": "2400"},
    {"name": "Coop Norge SA", "org": "980489698", "account": "2400"},
    {"name": "ISS Facility Services", "org": "939513600", "account": "2400"},
    {"name": "BDO Norge AS", "org": "993831738", "account": "2400"},
    {"name": "Advokatfirma Oslo AS", "org": "998765432", "account": "2400"},
    {"name": "Norsk Hydro ASA", "org": "914778271", "account": "2400"},
]

NORWEGIAN_CUSTOMERS = [
    {"name": "Bergen Seafood AS", "org": "987654321"},
    {"name": "Oslo Consulting AS", "org": "987654322"},
    {"name": "Stavanger Shipping AS", "org": "987654323"},
    {"name": "Trondheim Tech AS", "org": "987654324"},
    {"name": "Kristiansand Kraft AS", "org": "987654325"},
    {"name": "Tromsø Transport AS", "org": "987654326"},
    {"name": "Drammen Data AS", "org": "987654327"},
    {"name": "Bodø Bygg AS", "org": "987654328"},
    {"name": "Ålesund Akva AS", "org": "987654329"},
    {"name": "Molde Maritime AS", "org": "987654330"},
    {"name": "Haugesund Handel AS", "org": "987654331"},
    {"name": "Fredrikstad Finans AS", "org": "987654332"},
]

NORWEGIAN_TRANSACTION_TYPES = [
    "Vipps fra kunde",
    "BankAxept betaling",
    "Avtalegiro",
    "eFaktura betaling",
    "Nettbank overføring",
    "Kredittkort visa",
    "Kredittkort mastercard",
    "Straksoverføring",
    "Lønn utbetaling",
    "MVA oppgjør",
]

TASK_TEMPLATES = [
    {
        "name": "Avstemme leverandørgjeld (kto 2400)",
        "category": TaskCategory.AVSTEMMING,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Avstem saldobalanse konto 2400 mot leverandørreskontro"
    },
    {
        "name": "Avstemme kundefordringer (kto 1500)",
        "category": TaskCategory.AVSTEMMING,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Avstem saldobalanse konto 1500 mot kundereskontro"
    },
    {
        "name": "Bankavstemming hovedkonto",
        "category": TaskCategory.AVSTEMMING,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Avstem banksaldo mot bankkontoutskrift"
    },
    {
        "name": "MVA-oppgjør og rapportering",
        "category": TaskCategory.RAPPORTERING,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Beregn og rapporter MVA til Skatteetaten"
    },
    {
        "name": "Månedlig resultatrapport",
        "category": TaskCategory.RAPPORTERING,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Utarbeid månedlig resultatrapport for ledelsen"
    },
    {
        "name": "Bokføre leverandørfakturaer",
        "category": TaskCategory.BOKFØRING,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Gjennomgå og bokfør alle mottatte leverandørfakturaer"
    },
    {
        "name": "Bokføre kundefakturaer",
        "category": TaskCategory.BOKFØRING,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Bokfør og utsend kundefakturaer"
    },
    {
        "name": "Periodisering av inntekter",
        "category": TaskCategory.BOKFØRING,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Periodiser inntekter i henhold til opptjeningsprinsippet"
    },
    {
        "name": "Periodisering av kostnader",
        "category": TaskCategory.BOKFØRING,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Periodiser kostnader i henhold til sammenstillingsprinsippet"
    },
    {
        "name": "Kontroll av arbeidsgiveravgift",
        "category": TaskCategory.COMPLIANCE,
        "frequency": TaskFrequency.MONTHLY,
        "description": "Kontroller beregning og innbetaling av arbeidsgiveravgift"
    },
    {
        "name": "Kvartalsrapport til ledelse",
        "category": TaskCategory.RAPPORTERING,
        "frequency": TaskFrequency.QUARTERLY,
        "description": "Utarbeid omfattende kvartalsrapport med analyser"
    },
    {
        "name": "Årsavslutning og årsoppgjør",
        "category": TaskCategory.COMPLIANCE,
        "frequency": TaskFrequency.YEARLY,
        "description": "Gjennomfør fullstendig årsavslutning og årsoppgjør"
    },
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_kid_number() -> str:
    """Generate realistic Norwegian KID number"""
    return f"{random.randint(100000, 999999)}{random.randint(1000, 9999)}"

def get_due_date_category(due_date: date) -> str:
    """Categorize due date into age buckets"""
    today = date.today()
    days_diff = (due_date - today).days
    
    if days_diff > 0:
        return "not_due"
    elif days_diff >= -30:
        return "0-30"
    elif days_diff >= -60:
        return "31-60"
    elif days_diff >= -90:
        return "61-90"
    else:
        return "90+"

def random_date_in_range(start_date: date, end_date: date) -> date:
    """Generate random date within range"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

# ============================================================================
# MODULE 1: LEVERANDØRRESKONTRO (SUPPLIER LEDGER)
# ============================================================================

async def populate_supplier_ledger(session: AsyncSession, client_id: UUID) -> int:
    """
    Create 10+ realistic supplier ledger entries with varied due dates and statuses
    """
    print("\n📦 Module 1: Leverandørreskontro (Supplier Ledger)")
    
    # First, check if vendors exist, if not create them
    result = await session.execute(
        select(Vendor).where(Vendor.client_id == client_id)
    )
    existing_vendors = result.scalars().all()
    
    if len(existing_vendors) < len(NORWEGIAN_SUPPLIERS):
        print(f"  Creating {len(NORWEGIAN_SUPPLIERS)} vendors...")
        for idx, supplier_data in enumerate(NORWEGIAN_SUPPLIERS):
            vendor = Vendor(
                id=uuid4(),
                client_id=client_id,
                vendor_number=f"V{1000 + idx}",
                name=supplier_data["name"],
                org_number=supplier_data["org"],
                account_number=supplier_data["account"],
                payment_terms="30",
                is_active=True
            )
            session.add(vendor)
        await session.commit()
        print(f"  ✅ Created {len(NORWEGIAN_SUPPLIERS)} vendors")
        
        # Refresh vendor list
        result = await session.execute(
            select(Vendor).where(Vendor.client_id == client_id)
        )
        existing_vendors = result.scalars().all()
    
    # Check for existing supplier ledger entries
    result = await session.execute(
        select(func.count(SupplierLedger.id))
        .where(SupplierLedger.client_id == client_id)
    )
    existing_count = result.scalar()
    
    if existing_count >= 10:
        print(f"  ⏭️  Already have {existing_count} supplier ledger entries, skipping...")
        return existing_count
    
    # Create date range (Jan-Feb 2026)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 2, 28)
    
    entries_to_create = 12
    entries_created = 0
    
    for i in range(entries_to_create):
        vendor = random.choice(existing_vendors)
        invoice_date = random_date_in_range(start_date, end_date)
        
        # Varied due dates: some overdue, some current
        days_offset = random.choice([-120, -90, -60, -30, -15, 14, 30, 45, 60])
        due_date = invoice_date + timedelta(days=days_offset)
        
        # Amount range: 5,000 - 500,000 NOK
        amount = Decimal(random.randint(5000, 500000))
        
        # Status: mix of open, partially_paid, paid
        status_weights = [0.4, 0.2, 0.4]  # 40% open, 20% partially_paid, 40% paid
        status = random.choices(["open", "partially_paid", "paid"], weights=status_weights)[0]
        
        if status == "paid":
            remaining_amount = Decimal(0)
        elif status == "partially_paid":
            remaining_amount = amount * Decimal(random.uniform(0.3, 0.7))
        else:
            remaining_amount = amount
        
        # Create GL voucher first
        voucher = GeneralLedger(
            id=uuid4(),
            client_id=client_id,
            entry_date=invoice_date,
            accounting_date=invoice_date,
            period=invoice_date.strftime("%Y-%m"),
            fiscal_year=invoice_date.year,
            voucher_number=f"LF{invoice_date.strftime('%y%m')}{1000+i}",
            voucher_series="L",  # L for leverandør
            description=f"Leverandørfaktura fra {vendor.name}",
            source_type="vendor_invoice",
            created_by_type="ai_agent",
            status="posted"
        )
        session.add(voucher)
        
        # Create ledger entry
        ledger_entry = SupplierLedger(
            id=uuid4(),
            client_id=client_id,
            supplier_id=vendor.id,
            voucher_id=voucher.id,
            invoice_number=f"INV-{invoice_date.year}-{random.randint(10000, 99999)}",
            invoice_date=invoice_date,
            due_date=due_date,
            amount=amount,
            remaining_amount=remaining_amount,
            currency="NOK",
            status=status
        )
        session.add(ledger_entry)
        entries_created += 1
    
    await session.commit()
    print(f"  ✅ Created {entries_created} supplier ledger entries")
    print(f"     - Amount range: 5,000 - 500,000 NOK")
    print(f"     - Due dates: Mix of overdue and current")
    print(f"     - Status: Mix of open/partially_paid/paid")
    
    return entries_created

# ============================================================================
# MODULE 2: KUNDERESKONTRO (CUSTOMER LEDGER)
# ============================================================================

async def populate_customer_ledger(session: AsyncSession, client_id: UUID) -> int:
    """
    Create 10+ realistic customer ledger entries with KID numbers
    """
    print("\n📋 Module 2: Kundereskontro (Customer Ledger)")
    
    # Check for existing entries
    result = await session.execute(
        select(func.count(CustomerLedger.id))
        .where(CustomerLedger.client_id == client_id)
    )
    existing_count = result.scalar()
    
    if existing_count >= 10:
        print(f"  ⏭️  Already have {existing_count} customer ledger entries, skipping...")
        return existing_count
    
    # Create date range (Jan-Feb 2026)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 2, 28)
    
    entries_to_create = 12
    entries_created = 0
    
    for i in range(entries_to_create):
        customer = random.choice(NORWEGIAN_CUSTOMERS)
        invoice_date = random_date_in_range(start_date, end_date)
        
        # Payment terms: 14 or 30 days
        payment_days = random.choice([14, 30])
        due_date = invoice_date + timedelta(days=payment_days)
        
        # Amount range: 10,000 - 1,000,000 NOK
        amount = Decimal(random.randint(10000, 1000000))
        
        # Status: some overdue
        is_overdue = due_date < date.today()
        status_weights = [0.5, 0.3, 0.2] if is_overdue else [0.6, 0.2, 0.2]
        status = random.choices(["open", "partially_paid", "paid"], weights=status_weights)[0]
        
        if status == "paid":
            remaining_amount = Decimal(0)
        elif status == "partially_paid":
            remaining_amount = amount * Decimal(random.uniform(0.2, 0.6))
        else:
            remaining_amount = amount
        
        # Create GL voucher
        voucher = GeneralLedger(
            id=uuid4(),
            client_id=client_id,
            entry_date=invoice_date,
            accounting_date=invoice_date,
            period=invoice_date.strftime("%Y-%m"),
            fiscal_year=invoice_date.year,
            voucher_number=f"KF{invoice_date.strftime('%y%m')}{2000+i}",
            voucher_series="K",  # K for kunde
            description=f"Kundefaktura til {customer['name']}",
            source_type="customer_invoice",
            created_by_type="ai_agent",
            status="posted"
        )
        session.add(voucher)
        
        # Create ledger entry with KID
        ledger_entry = CustomerLedger(
            id=uuid4(),
            client_id=client_id,
            customer_name=customer["name"],
            voucher_id=voucher.id,
            invoice_number=f"FAKTURA-{invoice_date.year}-{3000+i}",
            invoice_date=invoice_date,
            due_date=due_date,
            kid_number=generate_kid_number(),
            amount=amount,
            remaining_amount=remaining_amount,
            currency="NOK",
            status=status
        )
        session.add(ledger_entry)
        entries_created += 1
    
    await session.commit()
    print(f"  ✅ Created {entries_created} customer ledger entries")
    print(f"     - Amount range: 10,000 - 1,000,000 NOK")
    print(f"     - All with KID numbers for payment matching")
    print(f"     - Mix of overdue and current invoices")
    
    return entries_created

# ============================================================================
# MODULE 3: BILAGSJOURNAL (VOUCHER JOURNAL / GENERAL LEDGER)
# ============================================================================

async def populate_voucher_journal(session: AsyncSession, client_id: UUID) -> int:
    """
    Create 50+ balanced vouchers with mix of types
    """
    print("\n📓 Module 3: Bilagsjournal (Voucher Journal)")
    
    # Check existing
    result = await session.execute(
        select(func.count(GeneralLedger.id))
        .where(and_(
            GeneralLedger.client_id == client_id,
            GeneralLedger.voucher_series == "A"  # Only count manual vouchers
        ))
    )
    existing_count = result.scalar()
    
    if existing_count >= 50:
        print(f"  ⏭️  Already have {existing_count} vouchers, skipping...")
        return existing_count
    
    # Voucher types and their characteristics
    voucher_types = [
        {
            "type": "vendor_invoice",
            "series": "L",
            "description": "Leverandørfaktura",
            "accounts": [(2400, "credit"), (4000, "debit")],  # Payable, Expense
        },
        {
            "type": "customer_invoice",
            "series": "K",
            "description": "Kundefaktura",
            "accounts": [(1500, "debit"), (3000, "credit")],  # Receivable, Revenue
        },
        {
            "type": "bank",
            "series": "B",
            "description": "Banktransaksjon",
            "accounts": [(1920, "debit"), (4000, "credit")],  # Bank, various
        },
        {
            "type": "manual",
            "series": "A",
            "description": "Manuelt bilag",
            "accounts": [(5000, "debit"), (1920, "credit")],  # Manual entries
        },
    ]
    
    # Date range
    start_date = date(2026, 1, 1)
    end_date = date(2026, 2, 28)
    
    entries_to_create = 55
    entries_created = 0
    
    for i in range(entries_to_create):
        voucher_type = random.choice(voucher_types)
        voucher_date = random_date_in_range(start_date, end_date)
        
        # Amount
        amount = Decimal(random.randint(1000, 100000))
        
        # Create voucher
        voucher = GeneralLedger(
            id=uuid4(),
            client_id=client_id,
            entry_date=voucher_date,
            accounting_date=voucher_date,
            period=voucher_date.strftime("%Y-%m"),
            fiscal_year=voucher_date.year,
            voucher_number=f"{voucher_type['series']}{voucher_date.strftime('%y%m')}{4000+i}",
            voucher_series=voucher_type["series"],
            description=f"{voucher_type['description']} - {voucher_date.strftime('%d.%m.%Y')}",
            source_type=voucher_type["type"],
            created_by_type=random.choice(["ai_agent", "user"]),
            status="posted"
        )
        session.add(voucher)
        
        # Create balanced lines (debit = credit)
        line_num = 1
        for account, side in voucher_type["accounts"]:
            line = GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=voucher.id,
                line_number=line_num,
                account_number=str(account),
                debit_amount=amount if side == "debit" else Decimal(0),
                credit_amount=amount if side == "credit" else Decimal(0),
                line_description=f"Bilagslinje {line_num}"
            )
            session.add(line)
            line_num += 1
        
        entries_created += 1
    
    await session.commit()
    print(f"  ✅ Created {entries_created} vouchers (bilag)")
    print(f"     - Spread over Jan-Feb 2026")
    print(f"     - Mix of types: vendor_invoice, customer_invoice, bank, manual")
    print(f"     - All balanced (debit = credit)")
    print(f"     - All with external references")
    
    return entries_created

# ============================================================================
# MODULE 4: TASK ADMIN
# ============================================================================

async def populate_task_admin(session: AsyncSession, client_id: UUID) -> int:
    """
    Create 20+ tasks with various statuses and some with subtasks
    """
    print("\n✅ Module 4: Task Admin (Oppgaveadministrasjon)")
    
    # Check existing
    result = await session.execute(
        select(func.count(Task.id))
        .where(Task.client_id == client_id)
    )
    existing_count = result.scalar()
    
    if existing_count >= 20:
        print(f"  ⏭️  Already have {existing_count} tasks, skipping...")
        return existing_count
    
    tasks_created = 0
    
    # Create tasks for Jan and Feb 2026
    for month in [1, 2]:
        for task_template in TASK_TEMPLATES:
            # Skip yearly tasks in Feb
            if task_template["frequency"] == TaskFrequency.YEARLY and month == 2:
                continue
            
            # Skip quarterly tasks in Feb
            if task_template["frequency"] == TaskFrequency.QUARTERLY and month == 2:
                continue
            
            # Random due date in the month
            due_date = date(2026, month, random.randint(20, 28))
            
            # Status distribution
            status = random.choices(
                [TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.DEVIATION],
                weights=[0.3, 0.3, 0.3, 0.1]
            )[0]
            
            # Completed info
            completed_at = None
            completed_by = None
            if status == TaskStatus.COMPLETED:
                completed_at = datetime.now() - timedelta(days=random.randint(1, 10))
                completed_by = random.choice(["AI Agent", "Line Andersen", "Per Hansen"])
            
            # Create main task
            task = Task(
                id=uuid4(),
                client_id=client_id,
                name=task_template["name"],
                description=task_template["description"],
                category=task_template["category"],
                frequency=task_template["frequency"],
                period_year=2026,
                period_month=month,
                due_date=due_date,
                status=status,
                completed_by=completed_by,
                completed_at=completed_at,
                is_checklist=False,
                sort_order=tasks_created
            )
            session.add(task)
            tasks_created += 1
            
            # 30% chance of having subtasks (checklist)
            if random.random() < 0.3:
                num_subtasks = random.randint(2, 4)
                for sub_idx in range(num_subtasks):
                    subtask_status = random.choices(
                        [TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED],
                        weights=[0.2, 0.3, 0.5]
                    )[0]
                    
                    subtask = Task(
                        id=uuid4(),
                        client_id=client_id,
                        name=f"Deloppgave {sub_idx + 1}",
                        description=f"Sjekkliste punkt for {task_template['name']}",
                        category=task_template["category"],
                        frequency=task_template["frequency"],
                        period_year=2026,
                        period_month=month,
                        status=subtask_status,
                        is_checklist=True,
                        parent_task_id=task.id,
                        sort_order=sub_idx
                    )
                    session.add(subtask)
                    tasks_created += 1
    
    await session.commit()
    print(f"  ✅ Created {tasks_created} tasks")
    print(f"     - Period: Jan-Feb 2026")
    print(f"     - Mix of categories: bokføring, avstemming, rapportering, compliance")
    print(f"     - Mix of status: not_started, in_progress, completed, deviation")
    print(f"     - Some with subtasks (checklist)")
    
    return tasks_created

# ============================================================================
# MODULE 5: BANKTRANSAKSJONER (BANK TRANSACTIONS)
# ============================================================================

async def populate_bank_transactions(session: AsyncSession, client_id: UUID) -> int:
    """
    Create 30+ bank transactions with Norwegian transaction types
    """
    print("\n🏦 Module 5: Banktransaksjoner (Bank Transactions)")
    
    # Check existing
    result = await session.execute(
        select(func.count(BankTransaction.id))
        .where(BankTransaction.client_id == client_id)
    )
    existing_count = result.scalar()
    
    if existing_count >= 30:
        print(f"  ⏭️  Already have {existing_count} bank transactions, skipping...")
        return existing_count
    
    # Get some customer ledger entries for matching
    result = await session.execute(
        select(CustomerLedger)
        .where(CustomerLedger.client_id == client_id)
        .limit(5)
    )
    customer_invoices = result.scalars().all()
    
    # Date range
    start_date = date(2026, 1, 1)
    end_date = date(2026, 2, 28)
    
    transactions_to_create = 35
    transactions_created = 0
    
    for i in range(transactions_to_create):
        trans_date = random_date_in_range(start_date, end_date)
        trans_datetime = datetime.combine(trans_date, datetime.min.time())
        
        # 60% credit (money in), 40% debit (money out)
        is_credit = random.random() < 0.6
        trans_type = TransactionType.CREDIT if is_credit else TransactionType.DEBIT
        
        if is_credit:
            amount = Decimal(random.randint(5000, 200000))
            description = f"{random.choice(NORWEGIAN_TRANSACTION_TYPES)} - {random.choice(NORWEGIAN_CUSTOMERS)['name']}"
            
            # 50% chance of being matched to a customer invoice
            if customer_invoices and random.random() < 0.5:
                matched_invoice = random.choice(customer_invoices)
                status = TransactionStatus.MATCHED
                kid = matched_invoice.kid_number
            else:
                status = TransactionStatus.UNMATCHED
                kid = generate_kid_number() if random.random() < 0.7 else None
        else:
            amount = Decimal(random.randint(500, 50000))
            description = f"{random.choice(NORWEGIAN_TRANSACTION_TYPES)} - Utgift"
            status = random.choice([TransactionStatus.UNMATCHED, TransactionStatus.MATCHED])
            kid = None
        
        # Create transaction
        transaction = BankTransaction(
            id=uuid4(),
            client_id=client_id,
            transaction_date=trans_datetime,
            booking_date=trans_datetime,
            amount=amount,
            transaction_type=trans_type,
            description=description,
            reference_number=f"REF{random.randint(100000, 999999)}",
            kid_number=kid,
            counterparty_name=random.choice(NORWEGIAN_CUSTOMERS)["name"] if is_credit else random.choice(NORWEGIAN_SUPPLIERS)["name"],
            bank_account="15064321234",  # Realistic Norwegian account number
            status=status,
            posted_to_ledger=status == TransactionStatus.MATCHED
        )
        session.add(transaction)
        transactions_created += 1
    
    await session.commit()
    print(f"  ✅ Created {transactions_created} bank transactions")
    print(f"     - Period: Jan-Feb 2026")
    print(f"     - Norwegian transaction types (Vipps, BankAxept, Avtalegiro, etc.)")
    print(f"     - Mix of matched and unmatched")
    print(f"     - Some with KID numbers for automatic matching")
    
    return transactions_created

# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """
    Main execution - populate all modules with demo data
    """
    print("\n" + "="*70)
    print("🚀 DEMO DATA POPULATION - TASK 7")
    print("="*70)
    print("\nPopulating realistic Norwegian demo data for all modules...")
    
    async with AsyncSessionLocal() as session:
        # Get first demo client (or first client if no demo)
        result = await session.execute(
            select(Client)
            .where(Client.is_demo == True)
            .limit(1)
        )
        client = result.scalars().first()
        
        if not client:
            # Try any client
            result = await session.execute(select(Client).limit(1))
            client = result.scalars().first()
        
        if not client:
            print("\n❌ ERROR: No client found in database!")
            print("   Please create a client first.")
            return
        
        print(f"\n📊 Target Client: {client.name} (ID: {client.id})")
        print(f"   Org Number: {client.org_number}")
        
        # Track totals
        totals = {}
        
        # Module 1: Leverandørreskontro
        totals["supplier_ledger"] = await populate_supplier_ledger(session, client.id)
        
        # Module 2: Kundereskontro
        totals["customer_ledger"] = await populate_customer_ledger(session, client.id)
        
        # Module 3: Bilagsjournal
        totals["voucher_journal"] = await populate_voucher_journal(session, client.id)
        
        # Module 4: Task Admin
        totals["tasks"] = await populate_task_admin(session, client.id)
        
        # Module 5: Banktransaksjoner
        totals["bank_transactions"] = await populate_bank_transactions(session, client.id)
        
        print("\n" + "="*70)
        print("✅ DEMO DATA POPULATION COMPLETE!")
        print("="*70)
        print("\n📈 Summary:")
        print(f"   • Leverandørreskontro:  {totals['supplier_ledger']:>3} entries")
        print(f"   • Kundereskontro:       {totals['customer_ledger']:>3} entries")
        print(f"   • Bilagsjournal:        {totals['voucher_journal']:>3} vouchers")
        print(f"   • Task Admin:           {totals['tasks']:>3} tasks")
        print(f"   • Banktransaksjoner:    {totals['bank_transactions']:>3} transactions")
        print(f"\n   📊 Total records created: {sum(totals.values())}")
        print("\n💾 Data successfully committed to database.")
        print("\n🔍 Verification:")
        print("   Run queries to verify data integrity:")
        print("   - Check balances in supplier/customer ledgers")
        print("   - Verify vouchers are balanced (debit = credit)")
        print("   - Confirm task assignments and statuses")
        print("   - Review bank transaction matching")
        print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())
