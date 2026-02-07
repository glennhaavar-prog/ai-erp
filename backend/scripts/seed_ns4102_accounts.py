"""
Seed NS 4102 Norwegian Chart of Accounts
Standard Norwegian accounting accounts for SMB
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.chart_of_accounts import Account
from app.models.client import Client


# NS 4102 Standard Norwegian Chart of Accounts
NS_4102_ACCOUNTS = [
    # Class 1: EIENDELER (ASSETS)
    {"number": "1000", "name": "Immatrielle eiendeler", "type": "asset", "vat_deductible": False},
    {"number": "1100", "name": "Tomter", "type": "asset", "vat_deductible": False},
    {"number": "1200", "name": "Bygninger og annen fast eiendom", "type": "asset", "vat_deductible": False},
    {"number": "1220", "name": "Inventar, verktøy og lignende", "type": "asset", "vat_deductible": True, "vat_code": "5"},
    {"number": "1230", "name": "Transportmidler", "type": "asset", "vat_deductible": True, "vat_code": "5"},
    {"number": "1500", "name": "Aksjer og andeler", "type": "asset", "vat_deductible": False},
    {"number": "1530", "name": "Obligasjoner", "type": "asset", "vat_deductible": False},
    {"number": "1740", "name": "Bankinnskudd, kontanter o.l.", "type": "asset", "vat_deductible": False, "reconciliation": True},
    {"number": "1900", "name": "Kundefordringer", "type": "asset", "vat_deductible": False, "reconciliation": True},
    {"number": "1920", "name": "Fordring på ansatte", "type": "asset", "vat_deductible": False},
    
    # Class 2: GJELD OG EGENKAPITAL (LIABILITIES & EQUITY)
    {"number": "2000", "name": "Annen langsiktig gjeld", "type": "liability", "vat_deductible": False},
    {"number": "2050", "name": "Lån i kredittinstitusjoner", "type": "liability", "vat_deductible": False},
    {"number": "2100", "name": "Sertifikatlån", "type": "liability", "vat_deductible": False},
    {"number": "2400", "name": "Leverandørgjeld", "type": "liability", "vat_deductible": False, "reconciliation": True},
    {"number": "2500", "name": "Skyldige offentlige avgifter", "type": "liability", "vat_deductible": False},
    {"number": "2600", "name": "Skyldig skattetrekk", "type": "liability", "vat_deductible": False},
    {"number": "2700", "name": "Utgående merverdiavgift", "type": "liability", "vat_deductible": False},
    {"number": "2710", "name": "Utgående MVA høy sats (25%)", "type": "liability", "vat_deductible": False},
    {"number": "2720", "name": "Utgående MVA middels sats (15%)", "type": "liability", "vat_deductible": False},
    {"number": "2730", "name": "Utgående MVA lav sats (11.11%)", "type": "liability", "vat_deductible": False},
    {"number": "2740", "name": "Inngående merverdiavgift", "type": "asset", "vat_deductible": False, "reconciliation": True},
    {"number": "2900", "name": "Annen kortsiktig gjeld", "type": "liability", "vat_deductible": False},
    {"number": "2920", "name": "Skyldig lønn", "type": "liability", "vat_deductible": False},
    {"number": "2940", "name": "Påløpte, ikke betalte kostnader", "type": "liability", "vat_deductible": False},
    {"number": "2960", "name": "Forskuddsbetalt inntekt", "type": "liability", "vat_deductible": False},
    
    # Class 3: INNTEKTER (REVENUE)
    {"number": "3000", "name": "Salgsinntekt produkter", "type": "revenue", "vat_deductible": False, "vat_code": "5"},
    {"number": "3100", "name": "Salgsinntekt tjenester", "type": "revenue", "vat_deductible": False, "vat_code": "5"},
    {"number": "3200", "name": "Leieinntekter", "type": "revenue", "vat_deductible": False, "vat_code": "5"},
    {"number": "3900", "name": "Annen driftsinntekt", "type": "revenue", "vat_deductible": False},
    
    # Class 4: VAREKJØP (COST OF GOODS SOLD)
    {"number": "4000", "name": "Varekjøp", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "4010", "name": "Varekjøp import", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "4300", "name": "Toll og transportkostnader ved varekjøp", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    
    # Class 5: LØNNSKOSTNADER (PAYROLL EXPENSES)
    {"number": "5000", "name": "Lønn", "type": "expense", "vat_deductible": False},
    {"number": "5090", "name": "Honorarer", "type": "expense", "vat_deductible": False},
    {"number": "5400", "name": "Arbeidsgiveravgift", "type": "expense", "vat_deductible": False},
    {"number": "5900", "name": "Andre lønn- og personalkostnader", "type": "expense", "vat_deductible": False},
    
    # Class 6: ANDRE DRIFTSKOSTNADER (OTHER OPERATING EXPENSES)
    {"number": "6000", "name": "Leie av lokaler", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6100", "name": "Kontorkostnader", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6300", "name": "Inventar og utstyr", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6340", "name": "Vedlikehold inventar og utstyr", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6500", "name": "Drivstoff", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6540", "name": "Vedlikehold transportmidler", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6700", "name": "Regnskaps- og revisjonskostnader", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6800", "name": "Reisekostnader", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6810", "name": "Kostgodtgjørelse", "type": "expense", "vat_deductible": True, "vat_code": "3"},
    {"number": "6860", "name": "Markedsføring", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6900", "name": "IT-kostnader", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6940", "name": "Forsikringspremier", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6960", "name": "Telefonikostnader", "type": "expense", "vat_deductible": True, "vat_code": "5"},
    {"number": "6980", "name": "Bankkostnader", "type": "expense", "vat_deductible": False},
    {"number": "6990", "name": "Kassedifferanser", "type": "expense", "vat_deductible": False},
    
    # Class 7: FINANSINNTEKTER/-KOSTNADER (FINANCIAL INCOME/EXPENSES)
    {"number": "7140", "name": "Valutagevinst", "type": "revenue", "vat_deductible": False},
    {"number": "7400", "name": "Renteinntekter", "type": "revenue", "vat_deductible": False},
    {"number": "7500", "name": "Utbytte", "type": "revenue", "vat_deductible": False},
    {"number": "7700", "name": "Finanskostnader", "type": "expense", "vat_deductible": False},
    {"number": "7790", "name": "Valutakostnad", "type": "expense", "vat_deductible": False},
    {"number": "7830", "name": "Rentekostnader", "type": "expense", "vat_deductible": False},
    
    # Class 8: AVSKRIVNINGER (DEPRECIATION)
    {"number": "8000", "name": "Avskrivning på bygninger", "type": "expense", "vat_deductible": False},
    {"number": "8050", "name": "Avskrivning på inventar", "type": "expense", "vat_deductible": False},
    {"number": "8070", "name": "Avskrivning på transportmidler", "type": "expense", "vat_deductible": False},
]


async def seed_accounts_for_client(client_id: UUID):
    """Seed NS 4102 accounts for a specific client"""
    async with AsyncSessionLocal() as session:
        try:
            # Check if client exists
            client_query = select(Client).where(Client.id == client_id)
            result = await session.execute(client_query)
            client = result.scalar_one_or_none()
            
            if not client:
                print(f"❌ Client {client_id} not found")
                return False
            
            print(f"📊 Seeding NS 4102 accounts for client: {client.name}")
            
            # Check if accounts already exist
            existing_query = select(Account).where(Account.client_id == client_id)
            result = await session.execute(existing_query)
            existing_accounts = result.scalars().all()
            
            if existing_accounts:
                print(f"⚠️  {len(existing_accounts)} accounts already exist for this client")
                response = input("  Overwrite? (y/n): ")
                if response.lower() != 'y':
                    print("  Cancelled")
                    return False
                
                # Delete existing
                for acc in existing_accounts:
                    await session.delete(acc)
                await session.commit()
                print("  ✓ Cleared existing accounts")
            
            # Create accounts
            created_count = 0
            for acc_data in NS_4102_ACCOUNTS:
                account = Account(
                    client_id=client_id,
                    account_number=acc_data["number"],
                    account_name=acc_data["name"],
                    account_type=acc_data["type"],
                    account_level=1,
                    default_vat_code=acc_data.get("vat_code"),
                    vat_deductible=acc_data.get("vat_deductible", False),
                    requires_reconciliation=acc_data.get("reconciliation", False),
                    is_active=True,
                    ai_usage_count=0
                )
                session.add(account)
                created_count += 1
            
            await session.commit()
            print(f"✅ Created {created_count} NS 4102 accounts")
            return True
            
        except Exception as e:
            print(f"❌ Error seeding accounts: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False


async def seed_all_clients():
    """Seed accounts for all active clients"""
    async with AsyncSessionLocal() as session:
        try:
            # Get all active clients
            query = select(Client).where(Client.status == 'active')
            result = await session.execute(query)
            clients = result.scalars().all()
            
            if not clients:
                print("⚠️  No active clients found")
                print("\n💡 Creating default test client...")
                
                # Create a default test client
                from app.models.tenant import Tenant
                tenant_query = select(Tenant).limit(1)
                tenant_result = await session.execute(tenant_query)
                tenant = tenant_result.scalar_one_or_none()
                
                if not tenant:
                    print("❌ No tenant found - cannot create client")
                    return False
                
                test_client = Client(
                    tenant_id=tenant.id,
                    name="Demo Regnskap AS",
                    org_number="999888777",
                    status="active"
                )
                session.add(test_client)
                await session.commit()
                await session.refresh(test_client)
                clients = [test_client]
                print(f"✅ Created test client: {test_client.name}")
            
            print(f"\n📊 Found {len(clients)} active client(s)")
            
            for client in clients:
                print(f"\n{'='*60}")
                await seed_accounts_for_client(client.id)
            
            print(f"\n{'='*60}")
            print("✅ Seeding complete!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed NS 4102 Norwegian Chart of Accounts")
    parser.add_argument("--client-id", type=str, help="Specific client ID to seed (UUID)")
    parser.add_argument("--all", action="store_true", help="Seed all active clients")
    
    args = parser.parse_args()
    
    if args.client_id:
        try:
            client_uuid = UUID(args.client_id)
            asyncio.run(seed_accounts_for_client(client_uuid))
        except ValueError:
            print("❌ Invalid UUID format")
    elif args.all:
        asyncio.run(seed_all_clients())
    else:
        print("Usage:")
        print("  python seed_ns4102_accounts.py --all")
        print("  python seed_ns4102_accounts.py --client-id <uuid>")
