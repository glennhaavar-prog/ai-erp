#!/usr/bin/env python3
"""
Seed demo accruals data

Creates example accruals for demo/testing:
- Insurance (12 months)
- Office rent (quarterly)
- Software subscription (monthly)
"""

import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.services.accrual_service import AccrualService
from sqlalchemy import select
from app.models.client import Client


async def main():
    """Seed accrual demo data"""
    
    print("🌱 Seeding accrual demo data...")
    
    service = AccrualService()
    
    async for db in get_db():
        try:
            # Get first demo client
            result = await db.execute(
                select(Client)
                .where(Client.is_demo == True)
                .limit(1)
            )
            demo_client = result.scalar_one_or_none()
            
            if not demo_client:
                print("❌ No demo client found. Run demo data generation first.")
                sys.exit(1)
            
            client_id = demo_client.id
            print(f"📋 Using demo client: {demo_client.name} ({client_id})")
            
            # 1. Insurance accrual (12 months)
            print("\n1️⃣  Creating insurance accrual (12 months)...")
            insurance = await service.create_accrual(
                db=db,
                client_id=client_id,
                description="Forsikring 2026 - Bedriftsforsikring",
                from_date=date(2026, 1, 1),
                to_date=date(2026, 12, 31),
                total_amount=Decimal("36000.00"),
                balance_account="1580",  # Forskuddsbetalte kostnader
                result_account="6820",   # Forsikringskostnader
                frequency="monthly",
                created_by="demo_seed",
                ai_detected=False
            )
            print(f"   ✅ Created: {insurance['accrual_id']}")
            print(f"   📅 {len(insurance['posting_schedule'])} monthly postings of 3000 NOK")
            
            # 2. Office rent (quarterly)
            print("\n2️⃣  Creating office rent accrual (quarterly)...")
            rent = await service.create_accrual(
                db=db,
                client_id=client_id,
                description="Kontorleie 2026 - Kvartalsvis forskuddsbetaling",
                from_date=date(2026, 1, 1),
                to_date=date(2026, 12, 31),
                total_amount=Decimal("120000.00"),
                balance_account="1580",  # Forskuddsbetalte kostnader
                result_account="6800",   # Kontorkostnader
                frequency="quarterly",
                created_by="demo_seed",
                ai_detected=False
            )
            print(f"   ✅ Created: {rent['accrual_id']}")
            print(f"   📅 {len(rent['posting_schedule'])} quarterly postings of 30000 NOK")
            
            # 3. Software subscription (monthly)
            print("\n3️⃣  Creating software subscription accrual (monthly)...")
            software = await service.create_accrual(
                db=db,
                client_id=client_id,
                description="Microsoft 365 Business Premium - Årlig abonnement",
                from_date=date(2026, 2, 1),
                to_date=date(2027, 1, 31),
                total_amount=Decimal("15600.00"),
                balance_account="1580",  # Forskuddsbetalte kostnader
                result_account="6940",   # Programvare og lisenser
                frequency="monthly",
                created_by="demo_seed",
                ai_detected=True  # Simulates AI detection from invoice
            )
            print(f"   ✅ Created: {software['accrual_id']}")
            print(f"   📅 {len(software['posting_schedule'])} monthly postings of 1300 NOK")
            
            print("\n✅ Demo accruals seeded successfully!")
            print(f"📊 Total: 3 accruals, {12 + 4 + 12} postings")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        finally:
            break  # Only one iteration


if __name__ == "__main__":
    asyncio.run(main())
