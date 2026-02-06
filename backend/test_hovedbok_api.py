"""
Test script for Hovedbok API endpoint
"""
import asyncio
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.client import Client


async def create_test_data():
    """Create test data for Hovedbok API testing"""
    async with AsyncSessionLocal() as db:
        print("Creating test data...")
        
        # Check if client exists
        client_result = await db.execute(select(Client).limit(1))
        client = client_result.scalar_one_or_none()
        
        if not client:
            print("No client found. Creating test client...")
            client = Client(
                id=uuid4(),
                name="Test AS",
                org_number="999999999",
                industry="consulting",
                accounting_start_date=date(2024, 1, 1),
                is_active=True
            )
            db.add(client)
            await db.commit()
            await db.refresh(client)
        
        print(f"Using client: {client.name} ({client.id})")
        
        # Create vendor
        vendor = Vendor(
            id=uuid4(),
            client_id=client.id,
            vendor_number="V001",
            name="Test Leverandør AS",
            org_number="888888888",
            account_number="2400",
            payment_terms="30"
        )
        db.add(vendor)
        await db.commit()
        await db.refresh(vendor)
        print(f"Created vendor: {vendor.name} ({vendor.id})")
        
        # Create vendor invoice
        today = date.today()
        invoice = VendorInvoice(
            id=uuid4(),
            client_id=client.id,
            vendor_id=vendor.id,
            invoice_number="INV-2024-001",
            invoice_date=today,
            due_date=today + timedelta(days=30),
            amount_excl_vat=Decimal("10000.00"),
            vat_amount=Decimal("2500.00"),
            total_amount=Decimal("12500.00"),
            currency="NOK",
            payment_status="unpaid",
            review_status="approved",
            ai_processed=True,
            ai_confidence_score=95
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        print(f"Created invoice: {invoice.invoice_number} ({invoice.id})")
        
        # Create general ledger entry
        gl_entry = GeneralLedger(
            id=uuid4(),
            client_id=client.id,
            entry_date=today,
            accounting_date=today,
            period=today.strftime("%Y-%m"),
            fiscal_year=today.year,
            voucher_number="1001",
            voucher_series="A",
            description=f"Invoice {invoice.invoice_number} - {vendor.name}",
            source_type="ehf_invoice",
            source_id=invoice.id,
            created_by_type="ai_agent",
            status="posted",
            locked=False
        )
        db.add(gl_entry)
        await db.commit()
        await db.refresh(gl_entry)
        print(f"Created GL entry: {gl_entry.voucher_series}-{gl_entry.voucher_number} ({gl_entry.id})")
        
        # Link invoice to GL entry
        invoice.general_ledger_id = gl_entry.id
        await db.commit()
        
        # Create general ledger lines
        lines = [
            GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=gl_entry.id,
                line_number=1,
                account_number="6300",
                debit_amount=Decimal("10000.00"),
                credit_amount=Decimal("0.00"),
                vat_code="3",
                vat_amount=Decimal("2500.00"),
                vat_base_amount=Decimal("10000.00"),
                line_description="Marketing expenses",
                ai_confidence_score=95,
                ai_reasoning="Categorized as marketing based on vendor pattern"
            ),
            GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=gl_entry.id,
                line_number=2,
                account_number="2700",
                debit_amount=Decimal("2500.00"),
                credit_amount=Decimal("0.00"),
                line_description="Input VAT 25%"
            ),
            GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=gl_entry.id,
                line_number=3,
                account_number="2400",
                debit_amount=Decimal("0.00"),
                credit_amount=Decimal("12500.00"),
                line_description=f"Accounts payable - {vendor.name}"
            )
        ]
        
        for line in lines:
            db.add(line)
        
        await db.commit()
        print(f"Created {len(lines)} GL lines")
        
        # Create another entry for variety
        gl_entry2 = GeneralLedger(
            id=uuid4(),
            client_id=client.id,
            entry_date=today - timedelta(days=5),
            accounting_date=today - timedelta(days=5),
            period=(today - timedelta(days=5)).strftime("%Y-%m"),
            fiscal_year=today.year,
            voucher_number="1002",
            voucher_series="A",
            description="Manual journal entry",
            source_type="manual",
            created_by_type="user",
            status="posted",
            locked=False
        )
        db.add(gl_entry2)
        await db.commit()
        await db.refresh(gl_entry2)
        
        lines2 = [
            GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=gl_entry2.id,
                line_number=1,
                account_number="1920",
                debit_amount=Decimal("5000.00"),
                credit_amount=Decimal("0.00"),
                line_description="Bank deposit"
            ),
            GeneralLedgerLine(
                id=uuid4(),
                general_ledger_id=gl_entry2.id,
                line_number=2,
                account_number="3000",
                debit_amount=Decimal("0.00"),
                credit_amount=Decimal("5000.00"),
                line_description="Sales revenue"
            )
        ]
        
        for line in lines2:
            db.add(line)
        
        await db.commit()
        print(f"Created second GL entry with {len(lines2)} lines")
        
        print("\n✅ Test data created successfully!")
        print(f"\nClient ID: {client.id}")
        print(f"Vendor ID: {vendor.id}")
        print(f"GL Entry 1 ID: {gl_entry.id}")
        print(f"GL Entry 2 ID: {gl_entry2.id}")
        
        return {
            "client_id": str(client.id),
            "vendor_id": str(vendor.id),
            "gl_entry_id": str(gl_entry.id),
            "gl_entry2_id": str(gl_entry2.id)
        }


async def test_api_endpoint(test_data):
    """Test the API endpoint"""
    import httpx
    
    print("\n" + "="*60)
    print("Testing Hovedbok API Endpoint")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Basic query with client_id
    print("\n📋 Test 1: GET all entries for client")
    url = f"{base_url}/api/reports/hovedbok/"
    params = {"client_id": test_data["client_id"]}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data['entries'])} entries")
                print(f"   Total entries in DB: {data['summary']['total_entries']}")
                print(f"   Total debit: {data['summary']['total_debit']}")
                print(f"   Total credit: {data['summary']['total_credit']}")
                print(f"   Pagination: Page {data['pagination']['page']} of {data['pagination']['total_pages']}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test 2: Filter by account number
    print("\n📋 Test 2: Filter by account number (6300)")
    params = {
        "client_id": test_data["client_id"],
        "account_number": "6300"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data['entries'])} entries with account 6300")
                if data['entries']:
                    entry = data['entries'][0]
                    print(f"   Entry: {entry['full_voucher']} - {entry['description']}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test 3: Filter by vendor
    print("\n📋 Test 3: Filter by vendor_id")
    params = {
        "client_id": test_data["client_id"],
        "vendor_id": test_data["vendor_id"]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data['entries'])} entries for vendor")
                if data['entries']:
                    entry = data['entries'][0]
                    if 'invoice' in entry:
                        print(f"   Invoice: {entry['invoice']['invoice_number']}")
                        print(f"   Vendor: {entry['invoice']['vendor']['name']}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test 4: Get single entry by ID
    print("\n📋 Test 4: GET single entry by ID")
    entry_url = f"{base_url}/api/reports/hovedbok/{test_data['gl_entry_id']}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(entry_url, timeout=10.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Entry details:")
                print(f"   Voucher: {data['full_voucher']}")
                print(f"   Description: {data['description']}")
                print(f"   Lines: {len(data['lines'])}")
                print(f"   Debit: {data['totals']['debit']}")
                print(f"   Credit: {data['totals']['credit']}")
                print(f"   Balanced: {data['totals']['balanced']}")
                if 'invoice' in data:
                    print(f"   Invoice: {data['invoice']['invoice_number']}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test 5: Date range filter
    print("\n📋 Test 5: Date range filter")
    today = date.today()
    params = {
        "client_id": test_data["client_id"],
        "start_date": (today - timedelta(days=7)).isoformat(),
        "end_date": today.isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data['entries'])} entries in date range")
                print(f"   Date range: {data['summary']['date_range']['start']} to {data['summary']['date_range']['end']}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test 6: Sorting and pagination
    print("\n📋 Test 6: Sorting (desc) and pagination")
    params = {
        "client_id": test_data["client_id"],
        "sort_by": "accounting_date",
        "sort_order": "desc",
        "page": 1,
        "page_size": 1
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data['entries'])} entry (page 1, size 1)")
                print(f"   Has next page: {data['pagination']['has_next']}")
                if data['entries']:
                    entry = data['entries'][0]
                    print(f"   Most recent entry: {entry['full_voucher']} ({entry['accounting_date']})")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)


async def main():
    """Main test function"""
    # Initialize database
    await init_db()
    
    # Create test data
    test_data = await create_test_data()
    
    # Test the API
    await test_api_endpoint(test_data)


if __name__ == "__main__":
    asyncio.run(main())
