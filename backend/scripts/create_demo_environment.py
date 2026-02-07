"""
Create Demo Environment

Sets up a demo tenant with 15 diverse clients across different industries.
All data is marked with is_demo=True for easy identification and cleanup.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.tenant import Tenant, SubscriptionTier
from app.models.client import Client, AutomationLevel
from app.models.chart_of_accounts import Account
from datetime import datetime
import uuid


# Demo tenant information
DEMO_TENANT = {
    "name": "Demo Regnskapsbyrå AS",
    "org_number": "999000001",
    "subscription_tier": SubscriptionTier.ENTERPRISE,
    "billing_email": "demo@kontali.no",
}

# 15 diverse demo clients across different industries
DEMO_CLIENTS = [
    {
        "client_number": "DEMO-001",
        "name": "Fjordvik Fiskeoppdrett AS",
        "org_number": "999100001",
        "industry": "Aquaculture",
        "ai_automation_level": AutomationLevel.FULL,
        "ai_confidence_threshold": 90,
    },
    {
        "client_number": "DEMO-002",
        "name": "Nordic Tech Solutions AS",
        "org_number": "999100002",
        "industry": "IT Services",
        "ai_automation_level": AutomationLevel.ASSISTED,
        "ai_confidence_threshold": 85,
    },
    {
        "client_number": "DEMO-003",
        "name": "Bergen Byggeservice AS",
        "org_number": "999100003",
        "industry": "Construction",
        "ai_automation_level": AutomationLevel.FULL,
        "ai_confidence_threshold": 88,
    },
    {
        "client_number": "DEMO-004",
        "name": "Fjelltoppen Restaurant AS",
        "org_number": "999100004",
        "industry": "Hospitality",
        "ai_automation_level": AutomationLevel.ASSISTED,
        "ai_confidence_threshold": 82,
    },
    {
        "client_number": "DEMO-005",
        "name": "Norsk E-Handel AS",
        "org_number": "999100005",
        "industry": "E-commerce",
        "ai_automation_level": AutomationLevel.FULL,
        "ai_confidence_threshold": 92,
    },
    {
        "client_number": "DEMO-006",
        "name": "Oslo Konsulentgruppe AS",
        "org_number": "999100006",
        "industry": "Consulting",
        "ai_automation_level": AutomationLevel.ASSISTED,
        "ai_confidence_threshold": 85,
    },
    {
        "client_number": "DEMO-007",
        "name": "Vestlandet Transport AS",
        "org_number": "999100007",
        "industry": "Logistics",
        "ai_automation_level": AutomationLevel.FULL,
        "ai_confidence_threshold": 89,
    },
    {
        "client_number": "DEMO-008",
        "name": "Innovative Marketing AS",
        "org_number": "999100008",
        "industry": "Marketing",
        "ai_automation_level": AutomationLevel.ASSISTED,
        "ai_confidence_threshold": 80,
    },
    {
        "client_number": "DEMO-009",
        "name": "Grønn Energi Norge AS",
        "org_number": "999100009",
        "industry": "Renewable Energy",
        "ai_automation_level": AutomationLevel.FULL,
        "ai_confidence_threshold": 91,
    },
    {
        "client_number": "DEMO-010",
        "name": "Norsk Skipsverft AS",
        "org_number": "999100010",
        "industry": "Shipbuilding",
        "ai_automation_level": AutomationLevel.ASSISTED,
        "ai_confidence_threshold": 87,
    },
    {
        "client_number": "DEMO-011",
        "name": "Fjord Eiendom AS",
        "org_number": "999100011",
        "industry": "Real Estate",
        "ai_automation_level": AutomationLevel.FULL,
        "ai_confidence_threshold": 90,
    },
    {
        "client_number": "DEMO-012",
        "name": "Nordic Health Solutions AS",
        "org_number": "999100012",
        "industry": "Healthcare",
        "ai_automation_level": AutomationLevel.ASSISTED,
        "ai_confidence_threshold": 84,
    },
    {
        "client_number": "DEMO-013",
        "name": "Bergen Mote & Design AS",
        "org_number": "999100013",
        "industry": "Fashion",
        "ai_automation_level": AutomationLevel.FULL,
        "ai_confidence_threshold": 86,
    },
    {
        "client_number": "DEMO-014",
        "name": "Stavanger Industri AS",
        "org_number": "999100014",
        "industry": "Manufacturing",
        "ai_automation_level": AutomationLevel.ASSISTED,
        "ai_confidence_threshold": 88,
    },
    {
        "client_number": "DEMO-015",
        "name": "Norsk Utdanningsgruppe AS",
        "org_number": "999100015",
        "industry": "Education",
        "ai_automation_level": AutomationLevel.FULL,
        "ai_confidence_threshold": 85,
    },
]

# Basic Norwegian Chart of Accounts (simplified)
BASIC_ACCOUNTS = [
    {"account_number": "1000", "account_name": "Kasse", "account_type": "asset", "default_vat_code": None},
    {"account_number": "1920", "account_name": "Bank", "account_type": "asset", "default_vat_code": None},
    {"account_number": "1500", "account_name": "Kundefordringer", "account_type": "asset", "default_vat_code": None},
    {"account_number": "2400", "account_name": "Leverandørgjeld", "account_type": "liability", "default_vat_code": None},
    {"account_number": "2700", "account_name": "Utgående MVA", "account_type": "liability", "default_vat_code": None},
    {"account_number": "2710", "account_name": "Inngående MVA", "account_type": "asset", "default_vat_code": None},
    {"account_number": "3000", "account_name": "Salgsinntekt", "account_type": "revenue", "default_vat_code": "3"},
    {"account_number": "4000", "account_name": "Varekjøp", "account_type": "expense", "default_vat_code": "3"},
    {"account_number": "5000", "account_name": "Lønnskostnader", "account_type": "expense", "default_vat_code": None},
    {"account_number": "6000", "account_name": "Kontorkostnader", "account_type": "expense", "default_vat_code": "3"},
    {"account_number": "6300", "account_name": "Markedsføring", "account_type": "expense", "default_vat_code": "3"},
    {"account_number": "6700", "account_name": "Reisekostnader", "account_type": "expense", "default_vat_code": "3"},
    {"account_number": "7000", "account_name": "Driftskostnader", "account_type": "expense", "default_vat_code": "3"},
]


async def create_demo_environment():
    """Create complete demo environment"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🎭 Creating Demo Environment for Kontali ERP")
            print("=" * 60)
            
            # Step 1: Check if demo tenant already exists
            from sqlalchemy import select
            result = await session.execute(
                select(Tenant).where(Tenant.org_number == DEMO_TENANT["org_number"])
            )
            existing_tenant = result.scalar_one_or_none()
            
            if existing_tenant:
                print(f"⚠️  Demo tenant already exists: {existing_tenant.name}")
                tenant = existing_tenant
            else:
                # Create demo tenant
                tenant = Tenant(
                    id=uuid.uuid4(),
                    name=DEMO_TENANT["name"],
                    org_number=DEMO_TENANT["org_number"],
                    subscription_tier=DEMO_TENANT["subscription_tier"],
                    billing_email=DEMO_TENANT["billing_email"],
                    is_demo=True,
                    settings={"demo_environment": True},
                )
                session.add(tenant)
                await session.flush()
                print(f"✅ Created demo tenant: {tenant.name} (ID: {tenant.id})")
            
            # Step 2: Create 15 demo clients
            print(f"\n📋 Creating {len(DEMO_CLIENTS)} demo clients...")
            created_clients = []
            
            for client_data in DEMO_CLIENTS:
                # Check if client already exists
                result = await session.execute(
                    select(Client).where(Client.org_number == client_data["org_number"])
                )
                existing_client = result.scalar_one_or_none()
                
                if existing_client:
                    print(f"   ⚠️  Client already exists: {client_data['name']}")
                    created_clients.append(existing_client)
                    continue
                
                # Create client
                client = Client(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    client_number=client_data["client_number"],
                    name=client_data["name"],
                    org_number=client_data["org_number"],
                    ai_automation_level=client_data["ai_automation_level"],
                    ai_confidence_threshold=client_data["ai_confidence_threshold"],
                    is_demo=True,
                    status="active",
                    fiscal_year_start=1,
                    accounting_method="accrual",
                    vat_term="bimonthly",
                    base_currency="NOK",
                )
                session.add(client)
                await session.flush()
                
                # Create basic chart of accounts for each client
                for account_data in BASIC_ACCOUNTS:
                    account = Account(
                        id=uuid.uuid4(),
                        client_id=client.id,
                        account_number=account_data["account_number"],
                        account_name=account_data["account_name"],
                        account_type=account_data["account_type"],
                        default_vat_code=account_data["default_vat_code"],
                        is_active=True,
                    )
                    session.add(account)
                
                created_clients.append(client)
                print(f"   ✅ {client_data['client_number']}: {client_data['name']} ({client_data['industry']})")
            
            # Commit all changes
            await session.commit()
            
            # Summary
            print("\n" + "=" * 60)
            print("🎉 Demo Environment Created Successfully!")
            print(f"   Tenant: {tenant.name}")
            print(f"   Tenant ID: {tenant.id}")
            print(f"   Clients: {len(created_clients)}")
            print(f"   Total Accounts: {len(created_clients) * len(BASIC_ACCOUNTS)}")
            print("\n💡 Update your .env file with:")
            print(f"   DEMO_MODE_ENABLED=true")
            print(f"   DEMO_TENANT_ID={tenant.id}")
            print(f"   ENVIRONMENT=demo")
            print("=" * 60)
            
            return tenant, created_clients
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error creating demo environment: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(create_demo_environment())
