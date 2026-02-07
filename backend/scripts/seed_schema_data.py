#!/usr/bin/env python3
"""
Seed Script: Create voucher series, fiscal years, and accounting periods for demo clients

This script seeds the accounting schema tables for all demo clients:
- 3 voucher series per client (EF, BK, MAN)
- 1 fiscal year (2026) per client
- 13 accounting periods per fiscal year (12 months + year-end)

Usage:
    cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
    python scripts/seed_schema_data.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import date
from dateutil.relativedelta import relativedelta

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.client import Client
from app.models.voucher_series import VoucherSeries
from app.models.fiscal_year import FiscalYear
from app.models.accounting_period import AccountingPeriod


# Voucher series definitions
VOUCHER_SERIES_DATA = [
    {"code": "EF", "name": "EHF Elektroniske fakturaer"},
    {"code": "BK", "name": "Banktransaksjoner"},
    {"code": "MAN", "name": "Manuelle posteringer"},
]


async def seed_voucher_series(session, client_id: str) -> int:
    """Create voucher series for a client. Returns count created."""
    created = 0
    for series in VOUCHER_SERIES_DATA:
        # Check if already exists
        result = await session.execute(
            select(VoucherSeries).where(
                VoucherSeries.client_id == client_id,
                VoucherSeries.code == series["code"]
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            continue

        vs = VoucherSeries(
            client_id=client_id,
            code=series["code"],
            name=series["name"],
            next_number=1,
            is_active=True
        )
        session.add(vs)
        created += 1
    return created


async def seed_fiscal_year(session, client_id: str, year: int = 2026) -> FiscalYear | None:
    """Create fiscal year for a client. Returns the FiscalYear or None if exists."""
    # Check if already exists
    result = await session.execute(
        select(FiscalYear).where(
            FiscalYear.client_id == client_id,
            FiscalYear.year == year
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    fy = FiscalYear(
        client_id=client_id,
        year=year,
        start_date=date(year, 1, 1),
        end_date=date(year, 12, 31),
        is_closed=False,
        is_locked=False
    )
    session.add(fy)
    return fy


async def seed_accounting_periods(session, fiscal_year: FiscalYear) -> int:
    """Create 13 accounting periods for a fiscal year. Returns count created."""
    year = fiscal_year.year
    created = 0

    # Check if periods already exist
    result = await session.execute(
        select(AccountingPeriod).where(
            AccountingPeriod.fiscal_year_id == fiscal_year.id
        )
    )
    existing_periods = result.scalars().all()
    existing_numbers = {p.period_number for p in existing_periods}

    # Create periods 1-12 (monthly)
    for month in range(1, 13):
        if month in existing_numbers:
            continue

        start = date(year, month, 1)
        # Calculate end of month
        if month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month + 1, 1) - relativedelta(days=1)

        period = AccountingPeriod(
            fiscal_year_id=fiscal_year.id,
            period_number=month,
            start_date=start,
            end_date=end,
            is_closed=False
        )
        session.add(period)
        created += 1

    # Create period 13 (year-end adjustments)
    if 13 not in existing_numbers:
        period_13 = AccountingPeriod(
            fiscal_year_id=fiscal_year.id,
            period_number=13,
            start_date=date(year, 12, 31),
            end_date=date(year, 12, 31),
            is_closed=False
        )
        session.add(period_13)
        created += 1

    return created


async def seed_schema_data():
    """Main function to seed all schema data for demo clients."""
    print("=" * 60)
    print("Seeding Accounting Schema Data")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # Get all demo clients
        result = await session.execute(
            select(Client).where(Client.is_demo == True)
        )
        clients = result.scalars().all()

        if not clients:
            print("No demo clients found! Please run the demo environment setup first.")
            return

        print(f"Found {len(clients)} demo client(s)")
        print("-" * 60)

        total_vs = 0
        total_fy = 0
        total_periods = 0

        for client in clients:
            print(f"\nProcessing: {client.name} ({client.org_number})")

            # 1. Seed voucher series
            vs_count = await seed_voucher_series(session, client.id)
            total_vs += vs_count
            print(f"  - Voucher series: {vs_count} created")

            # 2. Seed fiscal year
            fy = await seed_fiscal_year(session, client.id, 2026)
            await session.flush()  # Ensure fy.id is available
            if fy and fy.id:
                is_new = fy not in session.dirty and vs_count == 0  # Rough check
                total_fy += 1
                print(f"  - Fiscal year 2026: {'created' if is_new else 'exists'}")

                # 3. Seed accounting periods
                period_count = await seed_accounting_periods(session, fy)
                total_periods += period_count
                print(f"  - Accounting periods: {period_count} created")

        # Commit all changes
        await session.commit()

        print("\n" + "=" * 60)
        print("SEEDING COMPLETE")
        print("=" * 60)
        print(f"Voucher series created: {total_vs}")
        print(f"Fiscal years processed: {total_fy}")
        print(f"Accounting periods created: {total_periods}")


async def verify_data():
    """Verify seeded data counts."""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # Count voucher series
        result = await session.execute(select(VoucherSeries))
        vs_count = len(result.scalars().all())
        print(f"Total voucher_series: {vs_count}")

        # Count fiscal years
        result = await session.execute(select(FiscalYear))
        fy_count = len(result.scalars().all())
        print(f"Total fiscal_years: {fy_count}")

        # Count accounting periods
        result = await session.execute(select(AccountingPeriod))
        period_count = len(result.scalars().all())
        print(f"Total accounting_periods: {period_count}")

        # Expected counts (assuming 15 demo clients)
        print("\nExpected (for 15 demo clients):")
        print(f"  - Voucher series: 45 (3 per client)")
        print(f"  - Fiscal years: 15 (1 per client)")
        print(f"  - Accounting periods: 195 (13 per fiscal year)")


async def main():
    """Run seeding and verification."""
    await seed_schema_data()
    await verify_data()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SCHEMA DATA SEEDER")
    print("=" * 60 + "\n")

    asyncio.run(main())

    print("\nDone!")
