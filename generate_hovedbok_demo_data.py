#!/usr/bin/env python3
"""
Generate realistic Hovedbok (General Ledger) demo data

This script:
1. Books existing vendor invoices using the booking service
2. Creates 20-30 manual journal entries for realistic scenarios:
   - Bank transfers
   - Salary payments
   - VAT settlements
   - Period adjustments
   - Customer invoices (revenue side)

Ensures variety in accounts (1xxx-6xxx), VAT codes, dates, amounts, and vendors
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4, UUID
from collections import defaultdict
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.client import Client
from app.models.vendor_invoice import VendorInvoice
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.services.booking_service import book_vendor_invoice


# Norwegian descriptions for various transaction types
TRANSACTION_TEMPLATES = {
    "bank_transfers": [
        ("Overføring fra driftskonto til sparekonto", "1920", "1500", Decimal("50000.00"), 0),
        ("Overføring mellom bankkonti", "1920", "1500", Decimal("25000.00"), 0),
        ("Innbetaling til bankkonto", "1920", "2400", Decimal("30000.00"), 0),
    ],
    "salaries": [
        ("Utbetaling lønn ansatte januar 2026", "5000", "2400", Decimal("125000.00"), 0),
        ("Utbetaling lønn ansatte februar 2026", "5000", "2400", Decimal("128000.00"), 0),
        ("Arbeidsgiveravgift januar 2026", "5400", "2740", Decimal("17500.00"), 0),
        ("Arbeidsgiveravgift februar 2026", "5400", "2740", Decimal("17920.00"), 0),
        ("Feriepenger avsetning", "5090", "2770", Decimal("15600.00"), 0),
    ],
    "vat_settlements": [
        ("MVA oppgjør 1. termin 2026", "2720", "1920", Decimal("48500.00"), 0),
        ("MVA oppgjør inngående januar", "2740", "2720", Decimal("12300.00"), 0),
        ("MVA utgående mva januar", "2700", "2720", Decimal("36800.00"), 0),
    ],
    "customer_invoices": [
        ("Kundefaktura #2026-001 - Konsulentoppdrag Nordlaks AS", "1500", "3000", Decimal("85000.00"), 5),
        ("Kundefaktura #2026-002 - Rådgivning SalMar ASA", "1500", "3000", Decimal("125000.00"), 5),
        ("Kundefaktura #2026-003 - Analyse og rapport Lerøy", "1500", "3000", Decimal("65000.00"), 5),
        ("Kundefaktura #2026-004 - Prosjektledelse Grieg Seafood", "1500", "3000", Decimal("95000.00"), 5),
        ("Kundefaktura #2026-005 - Strategiutvikling Mowi", "1500", "3000", Decimal("110000.00"), 5),
    ],
    "period_adjustments": [
        ("Avskrivning inventar og utstyr januar", "6000", "1230", Decimal("2500.00"), 0),
        ("Avskrivning inventar og utstyr februar", "6000", "1230", Decimal("2500.00"), 0),
        ("Periodisering forsikring", "6820", "2900", Decimal("3200.00"), 0),
        ("Periodisering leie", "6200", "2900", Decimal("6000.00"), 0),
        ("Renteinntekt bankinnskudd", "1920", "8050", Decimal("850.00"), 0),
    ],
    "other_expenses": [
        ("Forsikring næringseiendom", "6820", "2400", Decimal("15000.00"), 5),
        ("Markedsføring og annonsering", "6100", "2400", Decimal("12500.00"), 5),
        ("Reiseutgifter ansatte", "6800", "2400", Decimal("8500.00"), 5),
        ("Kontingent Sjømatbedriftene", "6900", "2400", Decimal("4500.00"), 5),
        ("Bankgebyr og kortavgift", "6900", "1920", Decimal("850.00"), 5),
    ],
}


def get_random_date_in_range(year=2026, month_range=(1, 2)):
    """Generate random date within specified month range"""
    month = random.choice(range(month_range[0], month_range[1] + 1))
    day = random.randint(1, 28)  # Safe for all months
    return date(year, month, day)


def create_vat_line(amount: Decimal, vat_code: int) -> Decimal:
    """Calculate VAT amount based on vat_code"""
    if vat_code == 0:
        return Decimal("0.00")
    elif vat_code == 3:
        return amount * Decimal("0.15")  # 15% VAT
    elif vat_code == 5:
        return amount * Decimal("0.25")  # 25% VAT
    return Decimal("0.00")


async def get_next_voucher_number(db: AsyncSession, client_id: UUID, series: str = "M") -> str:
    """Generate next voucher number for manual entries"""
    query = select(GeneralLedger).where(
        GeneralLedger.client_id == client_id,
        GeneralLedger.voucher_series == series
    ).order_by(GeneralLedger.voucher_number.desc()).limit(1)
    
    result = await db.execute(query)
    last_entry = result.scalar_one_or_none()
    
    if last_entry:
        try:
            last_number = int(last_entry.voucher_number)
            next_number = last_number + 1
        except ValueError:
            next_number = 1
    else:
        next_number = 1
    
    return str(next_number).zfill(6)


async def create_manual_journal_entry(
    db: AsyncSession,
    client_id: UUID,
    description: str,
    accounting_date: date,
    lines: list,
    series: str = "M",
    voucher_number: str = None
) -> GeneralLedger:
    """
    Create a manual journal entry
    
    Args:
        lines: List of tuples (account, debit, credit, description, vat_code)
    """
    if voucher_number is None:
        voucher_number = await get_next_voucher_number(db, client_id, series)
    
    gl_entry = GeneralLedger(
        id=uuid4(),
        client_id=client_id,
        entry_date=datetime.now().date(),
        accounting_date=accounting_date,
        period=accounting_date.strftime("%Y-%m"),
        fiscal_year=accounting_date.year,
        voucher_number=voucher_number,
        voucher_series=series,
        description=description,
        source_type="manual",
        source_id=None,
        created_by_type="demo_generator",
        created_by_id=None,
        status="posted",
        locked=False
    )
    
    db.add(gl_entry)
    
    # Create lines
    for idx, (account, debit, credit, line_desc, vat_code) in enumerate(lines, start=1):
        vat_amount = Decimal("0.00")
        
        # Calculate VAT if needed
        if vat_code and vat_code > 0:
            if debit > 0:
                vat_amount = create_vat_line(debit, vat_code)
            elif credit > 0:
                vat_amount = create_vat_line(credit, vat_code)
        
        gl_line = GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=gl_entry.id,
            line_number=idx,
            account_number=str(account),
            debit_amount=debit,
            credit_amount=credit,
            vat_code=str(vat_code) if vat_code else None,
            vat_amount=vat_amount,
            line_description=line_desc
        )
        db.add(gl_line)
    
    return gl_entry


async def book_existing_invoices(db: AsyncSession, client_id: UUID) -> dict:
    """Book all unbooked vendor invoices"""
    from sqlalchemy.orm import selectinload
    
    stats = {
        "attempted": 0,
        "success": 0,
        "failed": 0,
        "already_booked": 0,
        "no_suggestion": 0
    }
    
    # Find all unbooked invoices with AI suggestions (eagerly load vendor)
    query = select(VendorInvoice).options(
        selectinload(VendorInvoice.vendor)
    ).where(
        VendorInvoice.client_id == client_id,
        VendorInvoice.general_ledger_id.is_(None),
        VendorInvoice.ai_booking_suggestion.is_not(None)
    )
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    print(f"\n📋 Found {len(invoices)} unbooked invoices with AI suggestions")
    
    for invoice in invoices:
        stats["attempted"] += 1
        
        # Check if invoice already booked
        if invoice.general_ledger_id:
            stats["already_booked"] += 1
            continue
        
        # Check if has AI suggestion
        if not invoice.ai_booking_suggestion:
            stats["no_suggestion"] += 1
            continue
        
        # Validate AI suggestion has proper lines
        lines = invoice.ai_booking_suggestion.get('lines', [])
        if not lines:
            stats["no_suggestion"] += 1
            continue
        
        # Validate each line has either debit or credit (not both zero)
        valid_lines = True
        for line in lines:
            debit = Decimal(str(line.get('debit', 0)))
            credit = Decimal(str(line.get('credit', 0)))
            if debit == 0 and credit == 0:
                valid_lines = False
                break
        
        if not valid_lines:
            stats["failed"] += 1
            vendor_name = invoice.vendor.name if invoice.vendor else 'Unknown'
            print(f"   Booking invoice {invoice.invoice_number} ({vendor_name})")
            print(f"      ❌ Failed: Invalid booking lines (both debit and credit are zero)")
            continue
        
        vendor_name = invoice.vendor.name if invoice.vendor else 'Unknown'
        print(f"   Booking invoice {invoice.invoice_number} ({vendor_name})")
        
        # Book the invoice
        try:
            result = await book_vendor_invoice(
                db=db,
                invoice_id=invoice.id,
                booking_suggestion=invoice.ai_booking_suggestion,
                created_by_type="demo_generator",
                created_by_id=None
            )
            
            if result.get("success"):
                stats["success"] += 1
                print(f"      ✅ Booked as {result.get('voucher_number')}")
            else:
                stats["failed"] += 1
                print(f"      ❌ Failed: {result.get('error')}")
        except Exception as e:
            stats["failed"] += 1
            print(f"      ❌ Failed: {str(e)[:100]}")
    
    await db.commit()
    return stats


async def create_diverse_manual_entries(db: AsyncSession, client_id: UUID, count: int = 25) -> list:
    """Create diverse manual journal entries"""
    created_entries = []
    
    print(f"\n📝 Creating {count} manual journal entries...")
    
    # Create entries from each category
    categories = list(TRANSACTION_TEMPLATES.keys())
    entries_per_category = count // len(categories)
    
    for category in categories:
        templates = TRANSACTION_TEMPLATES[category]
        num_entries = entries_per_category if category != categories[-1] else count - len(created_entries)
        
        print(f"\n   Category: {category} ({num_entries} entries)")
        
        for i in range(num_entries):
            template = random.choice(templates)
            description, debit_account, credit_account, base_amount, vat_code = template
            
            # Add some randomness to amounts (±20%)
            amount_variation = Decimal(str(random.uniform(0.8, 1.2)))
            amount = (base_amount * amount_variation).quantize(Decimal("0.01"))
            
            # Generate random date
            accounting_date = get_random_date_in_range()
            
            # Build lines
            lines = []
            
            if vat_code > 0:
                # With VAT - need to split
                vat_amount = create_vat_line(amount, vat_code)
                net_amount = amount
                
                if category == "customer_invoices":
                    # Revenue: Debit customer (1500), Credit revenue (3000) + VAT out (2700)
                    gross_amount = net_amount + vat_amount
                    lines = [
                        (debit_account, gross_amount, Decimal("0.00"), f"{description} - brutto", 0),
                        (credit_account, Decimal("0.00"), net_amount, f"{description} - netto", vat_code),
                        ("2700", Decimal("0.00"), vat_amount, "Utgående mva", 0),
                    ]
                else:
                    # Expense: Debit expense + VAT in, Credit bank
                    lines = [
                        (debit_account, net_amount, Decimal("0.00"), description, vat_code),
                        ("2740", vat_amount, Decimal("0.00"), "Inngående mva", 0),
                        (credit_account, Decimal("0.00"), net_amount + vat_amount, "Betaling", 0),
                    ]
            else:
                # No VAT - simple debit/credit
                lines = [
                    (debit_account, amount, Decimal("0.00"), description, 0),
                    (credit_account, Decimal("0.00"), amount, description, 0),
                ]
            
            # Create entry
            entry = await create_manual_journal_entry(
                db=db,
                client_id=client_id,
                description=description,
                accounting_date=accounting_date,
                lines=lines,
                series="M"  # Manual series
            )
            
            # Commit after each entry to ensure voucher numbers are correct
            await db.commit()
            
            created_entries.append(entry)
            print(f"      ✅ M-{entry.voucher_number}: {description[:60]}...")
    
    return created_entries


async def print_summary(db: AsyncSession, client_id: UUID):
    """Print comprehensive summary of generated data"""
    print("\n" + "="*80)
    print("📊 HOVEDBOK DEMO DATA SUMMARY")
    print("="*80)
    
    # Count total entries
    query = select(func.count(GeneralLedger.id)).where(GeneralLedger.client_id == client_id)
    result = await db.execute(query)
    total_entries = result.scalar()
    
    print(f"\n✅ Total General Ledger entries created: {total_entries}")
    
    # Count by series
    query = select(
        GeneralLedger.voucher_series,
        func.count(GeneralLedger.id)
    ).where(
        GeneralLedger.client_id == client_id
    ).group_by(GeneralLedger.voucher_series)
    
    result = await db.execute(query)
    series_counts = result.all()
    
    print("\n📋 Entries by voucher series:")
    for series, count in series_counts:
        series_name = {
            "AP": "Accounts Payable (Leverandørfakturaer)",
            "M": "Manual Entries (Manuelle posteringer)"
        }.get(series, series)
        print(f"   {series}: {count} entries - {series_name}")
    
    # Total debit/credit (must balance!)
    query = select(
        func.sum(GeneralLedgerLine.debit_amount),
        func.sum(GeneralLedgerLine.credit_amount)
    ).join(GeneralLedger).where(GeneralLedger.client_id == client_id)
    
    result = await db.execute(query)
    total_debit, total_credit = result.first()
    
    print(f"\n💰 Balance check:")
    print(f"   Total Debit:  {total_debit:>15,.2f} NOK")
    print(f"   Total Credit: {total_credit:>15,.2f} NOK")
    print(f"   Difference:   {abs(total_debit - total_credit):>15,.2f} NOK")
    
    if abs(total_debit - total_credit) < Decimal("0.01"):
        print("   ✅ BALANCED!")
    else:
        print("   ⚠️  NOT BALANCED!")
    
    # Entries per month
    query = select(
        GeneralLedger.period,
        func.count(GeneralLedger.id)
    ).where(
        GeneralLedger.client_id == client_id
    ).group_by(GeneralLedger.period).order_by(GeneralLedger.period)
    
    result = await db.execute(query)
    period_counts = result.all()
    
    print(f"\n📅 Entries per period:")
    for period, count in period_counts:
        print(f"   {period}: {count} entries")
    
    # Entries per account range
    query = select(
        GeneralLedgerLine.account_number,
        func.count(GeneralLedgerLine.id),
        func.sum(GeneralLedgerLine.debit_amount),
        func.sum(GeneralLedgerLine.credit_amount)
    ).join(GeneralLedger).where(
        GeneralLedger.client_id == client_id
    ).group_by(GeneralLedgerLine.account_number).order_by(GeneralLedgerLine.account_number)
    
    result = await db.execute(query)
    account_data = result.all()
    
    # Group by account range (1xxx, 2xxx, etc.)
    account_ranges = defaultdict(lambda: {"count": 0, "debit": Decimal("0"), "credit": Decimal("0")})
    
    for account_num, count, debit, credit in account_data:
        range_key = f"{account_num[0]}xxx"
        account_ranges[range_key]["count"] += count
        account_ranges[range_key]["debit"] += debit or Decimal("0")
        account_ranges[range_key]["credit"] += credit or Decimal("0")
    
    print(f"\n📊 Entries per account range:")
    range_names = {
        "1xxx": "Assets (Eiendeler)",
        "2xxx": "Liabilities (Gjeld)",
        "3xxx": "Revenue (Inntekter)",
        "4xxx": "Cost of Goods (Varekostnad)",
        "5xxx": "Salaries (Lønnskostnader)",
        "6xxx": "Other Expenses (Andre kostnader)",
        "8xxx": "Financial Items (Finansposter)"
    }
    
    for range_key in sorted(account_ranges.keys()):
        data = account_ranges[range_key]
        range_name = range_names.get(range_key, range_key)
        net = data["debit"] - data["credit"]
        print(f"   {range_key}: {data['count']:3d} lines | "
              f"Debit: {data['debit']:12,.2f} | "
              f"Credit: {data['credit']:12,.2f} | "
              f"Net: {net:12,.2f} - {range_name}")
    
    print("\n" + "="*80)
    print("✅ Demo data generation complete!")
    print("="*80 + "\n")


async def main():
    """Main function"""
    print("\n🚀 Starting Hovedbok demo data generation...")
    
    async with AsyncSessionLocal() as db:
        # Get first client (Kontali AS)
        query = select(Client).limit(1)
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            print("❌ No client found! Please run generate_demo_data.py first.")
            return
        
        print(f"📊 Client: {client.name} (ID: {client.id})")
        
        # Step 1: Book existing vendor invoices
        print("\n" + "="*80)
        print("STEP 1: Booking existing vendor invoices")
        print("="*80)
        
        invoice_stats = await book_existing_invoices(db, client.id)
        
        print(f"\n📊 Invoice booking summary:")
        print(f"   Attempted:      {invoice_stats['attempted']}")
        print(f"   ✅ Success:     {invoice_stats['success']}")
        print(f"   ❌ Failed:      {invoice_stats['failed']}")
        print(f"   Already booked: {invoice_stats['already_booked']}")
        print(f"   No suggestion:  {invoice_stats['no_suggestion']}")
        
        # Step 2: Create manual journal entries
        print("\n" + "="*80)
        print("STEP 2: Creating manual journal entries")
        print("="*80)
        
        manual_entries = await create_diverse_manual_entries(db, client.id, count=25)
        print(f"\n✅ Created {len(manual_entries)} manual journal entries")
        
        # Step 3: Print summary
        await print_summary(db, client.id)


if __name__ == "__main__":
    asyncio.run(main())
