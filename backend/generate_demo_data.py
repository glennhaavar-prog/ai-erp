#!/usr/bin/env python3
"""
Generate 15 demo clients with realistic accounting data for Kontali ERP demo.

Requirements:
- 15 clients (diverse industries/sizes)
- Opening balances as of 01.01.2026
- Bank transactions (Jan-Feb 2026)
- Vendor invoices (Jan-Feb 2026)
- Customer invoices (Jan-Feb 2026)
- Balanced entries (debit = credit)
"""

import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import (
    Client, Account, AccountBalance, VendorInvoice, 
    CustomerInvoice, BankTransaction, GeneralLedger, 
    GeneralLedgerLine, Document
)

# Database configuration
DATABASE_URL = "postgresql+asyncpg://erp_user:erp_password@localhost:5432/ai_erp"

# Demo data configurations
INDUSTRIES = [
    ("Bygg og anlegg", "7112"),
    ("Restaurant", "5610"),
    ("IT-konsulent", "6201"),
    ("Handelsbedrift", "4711"),
    ("Rørlegger", "4322"),
    ("Frisør", "9602"),
    ("Revisor", "6920"),
    ("Arkitekt", "7111"),
    ("Elektriker", "4321"),
    ("Tannlege", "8623"),
    ("Advokat", "6910"),
    ("Malermeister", "4334"),
    ("Webdesign", "6201"),
    ("Cafè", "5630"),
    ("Treningssenter", "9311"),
]

VENDOR_NAMES = [
    "Telenor Norge AS", "Elkjøp AS", "Statoil ASA", "Rema 1000 AS",
    "Coop Norge SA", "Norgesgruppen ASA", "Schibsted ASA", "DNB Bank ASA",
    "Hydro Energi AS", "Power Norge AS", "Europris ASA", "Bunnpris AS",
    "Maxbo AS", "Plantasjen Norge AS", "Kiwi Norge AS", "Joker AS",
]

CUSTOMER_NAMES = [
    "Oslo Kommune", "Viken Fylkeskommune", "Trondheim Kommune", "Bergen Kommune",
    "Stavanger Kommune", "Nordland Fylkeskommune", "AS Norge", "Norsk AS",
    "Bergen Bygg AS", "Oslo Invest AS", "Trondheim Eiendom AS", "Statoil ASA",
    "DNB Bank ASA", "Telenor Norge AS", "Hydro ASA", "Schibsted ASA",
]

ACCOUNT_MAPPINGS = {
    "bank": "1920",  # Bank
    "accounts_receivable": "1500",  # Kundefordringer
    "accounts_payable": "2400",  # Leverandørgjeld
    "revenue": "3000",  # Salgsinntekt
    "purchases": "4000",  # Varekjøp
    "salaries": "5000",  # Lønnskostnad
    "office_expense": "6300",  # Kontorrekvisita
    "rent": "6100",  # Leie lokaler
    "input_vat": "2740",  # Inngående MVA
    "output_vat": "2700",  # Utgående MVA
}


async def get_or_create_tenant(session: AsyncSession):
    """Get existing tenant or create demo tenant."""
    from app.models import Tenant
    
    # Try to get existing tenant
    result = await session.execute(select(Tenant).limit(1))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        tenant = Tenant(
            id=uuid4(),
            account_name="Demo Regnskapsbyrå AS",
            org_number="999999999",
            created_at=datetime.utcnow(),
        )
        session.add(tenant)
        await session.flush()
    
    return tenant


async def create_demo_client(session: AsyncSession, tenant: any, index: int) -> Client:
    """Create a demo client with opening balances."""
    industry, nace_code = INDUSTRIES[index]
    org_number = f"9{random.randint(10000000, 99999999)}"
    
    client = Client(
        id=uuid4(),
        tenant_id=tenant.id,
        client_number=f"DEMO{index+1:03d}",
        name=f"{industry} Demo {index+1}",
        org_number=org_number,
        status="active",
        ai_automation_level="assisted",
        ai_confidence_threshold=85,
        created_at=datetime(2025, 12, 15),
    )
    
    session.add(client)
    await session.flush()
    
    return client


async def create_accounts_for_client(session: AsyncSession, client: Client):
    """Create standard chart of accounts for a client."""
    standard_accounts = [
        ("1920", "Bank", "asset", 1),
        ("1500", "Kundefordringer", "asset", 1),
        ("2400", "Leverandørgjeld", "liability", 2),
        ("2700", "Utgående MVA", "liability", 2),
        ("2740", "Inngående MVA", "asset", 2),
        ("3000", "Salgsinntekt", "revenue", 3),
        ("4000", "Varekjøp", "expense", 4),
        ("5000", "Lønnskostnad", "expense", 5),
        ("6100", "Leie lokaler", "expense", 6),
        ("6300", "Kontorrekvisita", "expense", 6),
    ]
    
    accounts = []
    for acc_number, acc_name, acc_type, acc_class in standard_accounts:
        account = Account(
            id=uuid4(),
            client_id=client.id,
            account_number=acc_number,
            account_name=acc_name,
            account_type=acc_type,
            is_active=True,
        )
        session.add(account)
        accounts.append(account)
    
    await session.flush()
    return accounts


async def create_opening_balances(session: AsyncSession, client: Client, accounts: list):
    """Create realistic opening balances for 01.01.2026."""
    opening_date = datetime(2026, 1, 1).date()
    
    # Generate realistic balances based on client size (random between 100k - 2M)
    base_amount = Decimal(random.randint(100000, 2000000))
    
    balance_data = {
        "1920": base_amount * Decimal("0.15"),  # Bank 15% of base
        "1500": base_amount * Decimal("0.25"),  # AR 25%
        "2400": base_amount * Decimal("0.20"),  # AP 20%
        "2700": base_amount * Decimal("0.05"),  # Output VAT 5%
        "2740": base_amount * Decimal("0.05"),  # Input VAT 5%
    }
    
    for account in accounts:
        if account.account_number in balance_data:
            balance = AccountBalance(
                id=uuid4(),
                client_id=client.id,
                account_number=account.account_number,
                opening_balance=balance_data[account.account_number],
                opening_date=opening_date,
                fiscal_year="2026",
                created_at=datetime(2025, 12, 31),
            )
            session.add(balance)
    
    await session.flush()


async def create_vendor_invoice(
    session: AsyncSession, 
    client: Client, 
    accounts: list,
    invoice_date: datetime
) -> VendorInvoice:
    """Create a vendor invoice with accounting entries."""
    vendor_name = random.choice(VENDOR_NAMES)
    vendor_org = f"9{random.randint(10000000, 99999999)}"
    
    # Amount between 5k and 50k NOK
    net_amount = Decimal(random.randint(5000, 50000))
    vat_amount = net_amount * Decimal("0.25")
    gross_amount = net_amount + vat_amount
    
    # Create document
    s3_key = f"demo/{uuid4()}.pdf"
    document = Document(
        id=uuid4(),
        client_id=client.id,
        document_type="vendor_invoice",
        filename=f"vendor_invoice_{vendor_org}_{invoice_date.strftime('%Y%m%d')}.pdf",
        s3_bucket="kontali-erp-documents-eu-west-1",
        s3_key=s3_key,
        mime_type="application/pdf",
        file_size=random.randint(50000, 500000),
        uploaded_at=invoice_date,
    )
    session.add(document)
    await session.flush()
    
    # Create invoice
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=client.id,
        document_id=document.id,
        vendor_id=None,  # Demo data without vendor FK
        invoice_number=f"INV-{random.randint(10000, 99999)}",
        invoice_date=invoice_date.date(),
        due_date=(invoice_date + timedelta(days=30)).date(),
        amount_excl_vat=net_amount,
        vat_amount=vat_amount,
        total_amount=gross_amount,
        currency="NOK",
        review_status="reviewed",
        payment_status="unpaid",
        ai_processed=True,
        ai_confidence_score=random.randint(85, 99),
        created_at=invoice_date,
    )
    session.add(invoice)
    await session.flush()
    
    # Create general ledger entry
    entry = GeneralLedger(
        id=uuid4(),
        client_id=client.id,
        voucher_series="INV",
        voucher_number=str(random.randint(1000, 9999)),
        entry_date=invoice_date.date(),
        accounting_date=invoice_date.date(),
        period=invoice_date.strftime("%Y-%m"),
        fiscal_year=invoice_date.year,
        description=f"Vendor invoice {vendor_name}",
        source_type="vendor_invoice",
        source_id=invoice.id,
        created_by_type="demo_system",
        status="posted",
        created_at=invoice_date,
    )
    session.add(entry)
    await session.flush()
    
    # Find accounts
    expense_account = next((a for a in accounts if a.account_number in ["4000", "6100", "6300"]), accounts[0])
    vat_account = next((a for a in accounts if a.account_number == "2740"), None)
    payable_account = next((a for a in accounts if a.account_number == "2400"), None)
    
    # Create entry lines (debit expense + vat, credit payable)
    lines = [
        GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=entry.id,
            account_number=expense_account.account_number,
            line_description=f"Expense - {vendor_name}",
            debit_amount=net_amount,
            credit_amount=Decimal("0"),
            line_number=1,
        ),
        GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=entry.id,
            account_number=vat_account.account_number,
            line_description="Inngående MVA 25%",
            debit_amount=vat_amount,
            credit_amount=Decimal("0"),
            vat_code="5",
            line_number=2,
        ),
        GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=entry.id,
            account_number=payable_account.account_number,
            line_description=f"Accounts Payable - {vendor_name}",
            debit_amount=Decimal("0"),
            credit_amount=gross_amount,
            line_number=3,
        ),
    ]
    
    for line in lines:
        session.add(line)
    
    await session.flush()
    return invoice


async def create_customer_invoice(
    session: AsyncSession,
    client: Client,
    accounts: list,
    invoice_date: datetime
) -> CustomerInvoice:
    """Create a customer invoice with accounting entries."""
    customer_name = random.choice(CUSTOMER_NAMES)
    customer_org = f"9{random.randint(10000000, 99999999)}"
    
    # Amount between 10k and 100k NOK
    net_amount = Decimal(random.randint(10000, 100000))
    vat_amount = net_amount * Decimal("0.25")
    gross_amount = net_amount + vat_amount
    
    # Create invoice
    invoice = CustomerInvoice(
        id=uuid4(),
        client_id=client.id,
        customer_name=customer_name,
        customer_org_number=customer_org,
        invoice_number=f"CUST-{random.randint(1000, 9999)}",
        invoice_date=invoice_date.date(),
        due_date=(invoice_date + timedelta(days=14)).date(),
        amount_excl_vat=net_amount,
        vat_amount=vat_amount,
        total_amount=gross_amount,
        currency="NOK",
        payment_status="unpaid",
        ai_processed=True,
        ai_confidence_score=Decimal(random.randint(85, 99)),
        created_at=invoice_date,
    )
    session.add(invoice)
    await session.flush()
    
    # Create general ledger entry
    entry = GeneralLedger(
        id=uuid4(),
        client_id=client.id,
        voucher_series="CUST",
        voucher_number=str(random.randint(1000, 9999)),
        entry_date=invoice_date.date(),
        accounting_date=invoice_date.date(),
        period=invoice_date.strftime("%Y-%m"),
        fiscal_year=invoice_date.year,
        description=f"Customer invoice {customer_name}",
        source_type="customer_invoice",
        source_id=invoice.id,
        created_by_type="demo_system",
        status="posted",
        created_at=invoice_date,
    )
    session.add(entry)
    await session.flush()
    
    # Find accounts
    receivable_account = next((a for a in accounts if a.account_number == "1500"), None)
    revenue_account = next((a for a in accounts if a.account_number == "3000"), None)
    vat_account = next((a for a in accounts if a.account_number == "2700"), None)
    
    # Create entry lines (debit AR, credit revenue + vat)
    lines = [
        GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=entry.id,
            account_number=receivable_account.account_number,
            line_description=f"Accounts Receivable - {customer_name}",
            debit_amount=gross_amount,
            credit_amount=Decimal("0"),
            line_number=1,
        ),
        GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=entry.id,
            account_number=revenue_account.account_number,
            line_description=f"Sales Revenue - {customer_name}",
            debit_amount=Decimal("0"),
            credit_amount=net_amount,
            line_number=2,
        ),
        GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=entry.id,
            account_number=vat_account.account_number,
            line_description="Utgående MVA 25%",
            debit_amount=Decimal("0"),
            credit_amount=vat_amount,
            vat_code="3",
            line_number=3,
        ),
    ]
    
    for line in lines:
        session.add(line)
    
    await session.flush()
    return invoice


async def create_bank_transaction(
    session: AsyncSession,
    client: Client,
    accounts: list,
    transaction_date: datetime,
    is_payment: bool = True
):
    """Create a bank transaction (payment or receipt)."""
    amount = Decimal(random.randint(5000, 50000))
    
    if is_payment:
        description = f"Payment - {random.choice(VENDOR_NAMES)}"
        reference = f"PAYMENT-{random.randint(10000, 99999)}"
    else:
        description = f"Receipt - {random.choice(CUSTOMER_NAMES)}"
        reference = f"RECEIPT-{random.randint(10000, 99999)}"
    
    # Create bank transaction
    transaction = BankTransaction(
        id=uuid4(),
        client_id=client.id,
        transaction_date=transaction_date,
        booking_date=transaction_date,
        amount=amount if not is_payment else amount,
        transaction_type="credit" if not is_payment else "debit",
        description=description,
        reference_number=reference,
        bank_account="15031234567",
        status="matched",
    )
    session.add(transaction)
    await session.flush()
    
    # Create general ledger entry
    entry = GeneralLedger(
        id=uuid4(),
        client_id=client.id,
        voucher_series="BANK",
        voucher_number=str(random.randint(1000, 9999)),
        entry_date=transaction_date.date(),
        accounting_date=transaction_date.date(),
        period=transaction_date.strftime("%Y-%m"),
        fiscal_year=transaction_date.year,
        description=description,
        source_type="bank_transaction",
        source_id=transaction.id,
        created_by_type="demo_system",
        status="posted",
        created_at=transaction_date,
    )
    session.add(entry)
    await session.flush()
    
    # Find accounts
    bank_account = next((a for a in accounts if a.account_number == "1920"), None)
    if is_payment:
        contra_account = next((a for a in accounts if a.account_number == "2400"), None)  # AP
    else:
        contra_account = next((a for a in accounts if a.account_number == "1500"), None)  # AR
    
    # Create entry lines
    if is_payment:
        lines = [
            GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=entry.id,
                account_number=contra_account.account_number,
                line_description="Payment to vendor",
                debit_amount=amount,
                credit_amount=Decimal("0"),
                line_number=1,
            ),
            GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=entry.id,
                account_number=bank_account.account_number,
                line_description="Bank payment",
                debit_amount=Decimal("0"),
                credit_amount=amount,
                line_number=2,
            ),
        ]
    else:
        lines = [
            GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=entry.id,
                account_number=bank_account.account_number,
                line_description="Bank receipt",
                debit_amount=amount,
                credit_amount=Decimal("0"),
                line_number=1,
            ),
            GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=entry.id,
                account_number=contra_account.account_number,
                line_description="Payment from customer",
                debit_amount=Decimal("0"),
                credit_amount=amount,
                line_number=2,
            ),
        ]
    
    for line in lines:
        session.add(line)
    
    await session.flush()


async def generate_demo_data():
    """Main function to generate all demo data."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    print("🚀 Starting demo data generation...")
    print("=" * 60)
    
    async with async_session() as session:
        async with session.begin():
            # Get or create tenant
            tenant = await get_or_create_tenant(session)
            print(f"✅ Using tenant: {tenant.name}\n")
            
            # Generate dates for Jan-Feb 2026
            start_date = datetime(2026, 1, 2)
            end_date = datetime(2026, 2, 7)
            
            all_clients = []
            
            for i in range(15):
                print(f"\n📊 Creating client {i+1}/15...")
                
                # Create client
                client = await create_demo_client(session, tenant, i)
                all_clients.append(client)
                print(f"  ✅ Client: {client.name}")
                
                # Create accounts
                accounts = await create_accounts_for_client(session, client)
                print(f"  ✅ Accounts: {len(accounts)} standard accounts")
                
                # Create opening balances
                await create_opening_balances(session, client, accounts)
                print(f"  ✅ Opening balances: 01.01.2026")
                
                # Generate transactions (Jan-Feb 2026)
                # 3-5 vendor invoices
                vendor_count = random.randint(3, 5)
                for _ in range(vendor_count):
                    invoice_date = start_date + timedelta(days=random.randint(0, 37))
                    await create_vendor_invoice(session, client, accounts, invoice_date)
                print(f"  ✅ Vendor invoices: {vendor_count}")
                
                # 4-7 customer invoices
                customer_count = random.randint(4, 7)
                for _ in range(customer_count):
                    invoice_date = start_date + timedelta(days=random.randint(0, 37))
                    await create_customer_invoice(session, client, accounts, invoice_date)
                print(f"  ✅ Customer invoices: {customer_count}")
                
                # 5-10 bank transactions (mix of payments and receipts)
                bank_count = random.randint(5, 10)
                for _ in range(bank_count):
                    transaction_date = start_date + timedelta(days=random.randint(0, 37))
                    is_payment = random.choice([True, False])
                    await create_bank_transaction(
                        session, client, accounts, transaction_date, is_payment
                    )
                print(f"  ✅ Bank transactions: {bank_count}")
                
                print(f"  🎉 Client {i+1} complete!")
            
            print("\n" + "=" * 60)
            print("✅ Demo data generation COMPLETE!")
            print(f"📊 Created {len(all_clients)} clients with full accounting data")
            print("\nYou can now:")
            print("  1. Navigate between clients in the UI")
            print("  2. View saldobalanse reports")
            print("  3. View hovedbok reports")
            print("  4. Test all accounting features")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(generate_demo_data())
