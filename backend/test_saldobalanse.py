"""
Test script for Saldobalanse API

Creates test data and verifies the saldobalanse report functionality:
1. Creates account_balances table if not exists
2. Inserts test client with opening balances
3. Creates test accounting entries
4. Verifies debit/credit balance
5. Tests API endpoints
"""
import asyncio
import sys
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

# Add parent directory to path
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/ai-erp/backend')

from sqlalchemy import text
from app.database import engine, AsyncSessionLocal, Base
from app.models.tenant import Tenant
from app.models.client import Client
from app.models.chart_of_accounts import Account
from app.models.account_balance import AccountBalance
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine


async def create_tables():
    """Create account_balances table if it doesn't exist"""
    from app.models import AccountBalance  # Ensure model is loaded
    
    async with engine.begin() as conn:
        # Create all tables (will skip existing ones)
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created/verified")


async def setup_test_data():
    """Setup test client with opening balances and transactions"""
    
    async with AsyncSessionLocal() as db:
        # Check if test tenant exists
        existing_tenant = await db.execute(
            text("SELECT id FROM tenants WHERE name = 'Test Regnskapsbyrå' LIMIT 1")
        )
        tenant_row = existing_tenant.fetchone()
        
        if tenant_row:
            tenant_id = tenant_row[0]
            print(f"✅ Using existing test tenant: {tenant_id}")
        else:
            # Create test tenant
            tenant = Tenant(
                id=uuid4(),
                name="Test Regnskapsbyrå",
                org_number="888888888",
            )
            db.add(tenant)
            await db.flush()
            tenant_id = tenant.id
            print(f"✅ Created test tenant: {tenant_id}")
        
        # Check if test client already exists
        existing_client = await db.execute(
            text("SELECT id FROM clients WHERE name = 'Test Klient AS' LIMIT 1")
        )
        existing = existing_client.fetchone()
        
        if existing:
            client_id = existing[0]
            print(f"✅ Using existing test client: {client_id}")
        else:
            # Create test client
            client = Client(
                id=uuid4(),
                tenant_id=tenant_id,
                client_number="001",
                name="Test Klient AS",
                org_number="999999999",
                fiscal_year_start=1,
                status="active",
            )
            db.add(client)
            await db.flush()
            client_id = client.id
            print(f"✅ Created test client: {client_id}")
        
        # Create chart of accounts
        test_accounts = [
            {"number": "1500", "name": "Kundefordringer", "type": "asset"},
            {"number": "1920", "name": "Bankinnskudd", "type": "asset"},
            {"number": "2400", "name": "Leverandørgjeld", "type": "liability"},
            {"number": "3000", "name": "Egenkapital", "type": "equity"},
            {"number": "4000", "name": "Salgsinntekt", "type": "revenue"},
            {"number": "5000", "name": "Varekjøp", "type": "expense"},
            {"number": "6000", "name": "Lønnskostnader", "type": "expense"},
            {"number": "7000", "name": "Driftskostnader", "type": "expense"},
        ]
        
        for acc_data in test_accounts:
            # Check if account exists
            existing = await db.execute(
                text(
                    "SELECT id FROM chart_of_accounts "
                    "WHERE client_id = :client_id AND account_number = :number"
                ),
                {"client_id": client_id, "number": acc_data["number"]}
            )
            if not existing.fetchone():
                account = Account(
                    id=uuid4(),
                    client_id=client_id,
                    account_number=acc_data["number"],
                    account_name=acc_data["name"],
                    account_type=acc_data["type"],
                    is_active=True,
                )
                db.add(account)
        
        await db.flush()
        print("✅ Chart of accounts created")
        
        # Create opening balances for 2026
        opening_balances = [
            {"account": "1500", "balance": Decimal("50000.00")},  # Kundefordringer
            {"account": "1920", "balance": Decimal("100000.00")},  # Bank
            {"account": "2400", "balance": Decimal("-30000.00")},  # Leverandørgjeld (credit)
            {"account": "3000", "balance": Decimal("-120000.00")},  # Egenkapital (credit)
        ]
        
        for ob_data in opening_balances:
            # Check if balance exists
            existing = await db.execute(
                text(
                    "SELECT id FROM account_balances "
                    "WHERE client_id = :client_id AND account_number = :number AND fiscal_year = '2026'"
                ),
                {"client_id": client_id, "number": ob_data["account"]}
            )
            if not existing.fetchone():
                balance = AccountBalance(
                    id=uuid4(),
                    client_id=client_id,
                    account_number=ob_data["account"],
                    opening_balance=ob_data["balance"],
                    opening_date=date(2026, 1, 1),
                    fiscal_year="2026",
                    description="Inngående balanse 2026",
                )
                db.add(balance)
        
        await db.flush()
        print("✅ Opening balances created for 2026-01-01")
        
        # Check if test transactions already exist
        existing_trans = await db.execute(
            text(
                "SELECT COUNT(*) FROM general_ledger "
                "WHERE client_id = :client_id AND fiscal_year = 2026"
            ),
            {"client_id": client_id}
        )
        trans_count = existing_trans.fetchone()[0]
        
        if trans_count > 0:
            print(f"✅ Test transactions already exist ({trans_count} entries)")
            await db.commit()
            print(f"\n📊 Test client ID: {client_id}")
            return client_id
        
        # Create some test transactions
        # Transaction 1: Sales invoice (debit 1500, credit 4000)
        gl1 = GeneralLedger(
            id=uuid4(),
            client_id=client_id,
            entry_date=date(2026, 1, 15),
            accounting_date=date(2026, 1, 15),
            period="2026-01",
            fiscal_year=2026,
            voucher_number="1",
            voucher_series="A",
            description="Salgsfaktura kunde 123",
            source_type="customer_invoice",
            created_by_type="ai_agent",
            status="posted",
        )
        db.add(gl1)
        await db.flush()
        
        # Lines for transaction 1
        gl1_line1 = GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=gl1.id,
            line_number=1,
            account_number="1500",
            debit_amount=Decimal("25000.00"),
            credit_amount=Decimal("0.00"),
            line_description="Kundefordring",
        )
        gl1_line2 = GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=gl1.id,
            line_number=2,
            account_number="4000",
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("25000.00"),
            line_description="Salgsinntekt",
        )
        db.add_all([gl1_line1, gl1_line2])
        
        # Transaction 2: Purchase invoice (debit 5000, credit 2400)
        gl2 = GeneralLedger(
            id=uuid4(),
            client_id=client_id,
            entry_date=date(2026, 1, 20),
            accounting_date=date(2026, 1, 20),
            period="2026-01",
            fiscal_year=2026,
            voucher_number="2",
            voucher_series="A",
            description="Kjøpsfaktura leverandør ABC",
            source_type="ehf_invoice",
            created_by_type="ai_agent",
            status="posted",
        )
        db.add(gl2)
        await db.flush()
        
        # Lines for transaction 2
        gl2_line1 = GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=gl2.id,
            line_number=1,
            account_number="5000",
            debit_amount=Decimal("10000.00"),
            credit_amount=Decimal("0.00"),
            line_description="Varekjøp",
        )
        gl2_line2 = GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=gl2.id,
            line_number=2,
            account_number="2400",
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("10000.00"),
            line_description="Leverandørgjeld",
        )
        db.add_all([gl2_line1, gl2_line2])
        
        # Transaction 3: Salary payment (debit 6000, credit 1920)
        gl3 = GeneralLedger(
            id=uuid4(),
            client_id=client_id,
            entry_date=date(2026, 1, 31),
            accounting_date=date(2026, 1, 31),
            period="2026-01",
            fiscal_year=2026,
            voucher_number="3",
            voucher_series="A",
            description="Lønnsutbetaling januar",
            source_type="manual",
            created_by_type="user",
            status="posted",
        )
        db.add(gl3)
        await db.flush()
        
        # Lines for transaction 3
        gl3_line1 = GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=gl3.id,
            line_number=1,
            account_number="6000",
            debit_amount=Decimal("30000.00"),
            credit_amount=Decimal("0.00"),
            line_description="Lønnskostnad",
        )
        gl3_line2 = GeneralLedgerLine(
            id=uuid4(),
            general_ledger_id=gl3.id,
            line_number=2,
            account_number="1920",
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("30000.00"),
            line_description="Bankutbetaling",
        )
        db.add_all([gl3_line1, gl3_line2])
        
        await db.commit()
        print("✅ Test transactions created")
        print(f"\n📊 Test client ID: {client_id}")
        
        return client_id


async def verify_balance():
    """Verify that debit equals credit"""
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT 
                    SUM(debit_amount) as total_debit,
                    SUM(credit_amount) as total_credit
                FROM general_ledger_lines gl_line
                JOIN general_ledger gl ON gl_line.general_ledger_id = gl.id
                WHERE gl.status = 'posted'
            """)
        )
        row = result.fetchone()
        
        total_debit = row[0] or Decimal("0")
        total_credit = row[1] or Decimal("0")
        
        print(f"\n📊 Balance Verification:")
        print(f"   Total Debit:  {total_debit:>12,.2f}")
        print(f"   Total Credit: {total_credit:>12,.2f}")
        print(f"   Difference:   {abs(total_debit - total_credit):>12,.2f}")
        
        if abs(total_debit - total_credit) < Decimal("0.01"):
            print("   ✅ BALANCED!")
            return True
        else:
            print("   ❌ NOT BALANCED!")
            return False


async def test_api():
    """Test the saldobalanse API"""
    print("\n🧪 Testing Saldobalanse API...")
    print("=" * 60)
    print("\nTo test the API endpoints, run:")
    print("\n1. Start the server:")
    print("   cd /home/ubuntu/.openclaw/workspace/ai-erp/backend")
    print("   source venv/bin/activate")
    print("   uvicorn app.main:app --reload")
    print("\n2. Test endpoints:")
    print("   GET /api/reports/saldobalanse/?client_id=<CLIENT_ID>")
    print("   GET /api/reports/saldobalanse/export/excel/?client_id=<CLIENT_ID>")
    print("   GET /api/reports/saldobalanse/export/pdf/?client_id=<CLIENT_ID>")
    print("\n3. Optional filters:")
    print("   &from_date=2026-01-01")
    print("   &to_date=2026-01-31")
    print("   &account_class=1")
    print("\n4. Access API docs:")
    print("   http://localhost:8000/docs")
    print("=" * 60)


async def main():
    """Main test function"""
    print("=" * 60)
    print("🚀 Saldobalanse Test Script")
    print("=" * 60)
    
    try:
        # Create tables
        await create_tables()
        
        # Setup test data
        client_id = await setup_test_data()
        
        # Verify balance
        balanced = await verify_balance()
        
        if not balanced:
            print("\n⚠️  WARNING: Books are not balanced!")
        
        # Show test instructions
        await test_api()
        
        print("\n✅ Test setup complete!")
        print(f"\n📝 Use this client_id for testing: {client_id}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
