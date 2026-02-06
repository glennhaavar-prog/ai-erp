"""
Simple test script for Hovedbok API endpoint using existing data
"""
import asyncio
import httpx
from datetime import date, timedelta
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.general_ledger import GeneralLedger
from app.models.client import Client


async def get_test_data():
    """Get existing test data from database"""
    async with AsyncSessionLocal() as db:
        # Get first client
        client_result = await db.execute(select(Client).limit(1))
        client = client_result.scalar_one_or_none()
        
        if not client:
            print("❌ No client found in database")
            return None
        
        # Get a GL entry
        gl_result = await db.execute(
            select(GeneralLedger).where(
                GeneralLedger.client_id == client.id
            ).limit(1)
        )
        gl_entry = gl_result.scalar_one_or_none()
        
        return {
            "client_id": str(client.id),
            "client_name": client.name,
            "gl_entry_id": str(gl_entry.id) if gl_entry else None
        }


async def test_api():
    """Test the Hovedbok API endpoint"""
    print("\n" + "="*70)
    print("🧪 Testing Hovedbok REST API Endpoint")
    print("="*70)
    
    # Get test data
    test_data = await get_test_data()
    if not test_data:
        print("❌ No test data available")
        return
    
    print(f"\n📊 Using client: {test_data['client_name']} ({test_data['client_id']})")
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Basic query - get all entries for client
        print("\n" + "-"*70)
        print("📋 Test 1: GET /api/reports/hovedbok/ (all entries)")
        print("-"*70)
        try:
            response = await client.get(
                f"{base_url}/api/reports/hovedbok/",
                params={"client_id": test_data["client_id"]}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS")
                print(f"   Entries returned: {len(data['entries'])}")
                print(f"   Total entries: {data['summary']['total_entries']}")
                print(f"   Total debit: {data['summary']['total_debit']:.2f}")
                print(f"   Total credit: {data['summary']['total_credit']:.2f}")
                print(f"   Page: {data['pagination']['page']} of {data['pagination']['total_pages']}")
                
                # Show first entry if available
                if data['entries']:
                    entry = data['entries'][0]
                    print(f"\n   First Entry:")
                    print(f"   - Voucher: {entry['full_voucher']}")
                    print(f"   - Date: {entry['accounting_date']}")
                    print(f"   - Description: {entry['description']}")
                    print(f"   - Lines: {len(entry.get('lines', []))}")
                    if entry.get('totals'):
                        print(f"   - Debit: {entry['totals']['debit']:.2f}")
                        print(f"   - Credit: {entry['totals']['credit']:.2f}")
                        print(f"   - Balanced: {entry['totals']['balanced']}")
            else:
                print(f"❌ FAILED: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        # Test 2: Pagination
        print("\n" + "-"*70)
        print("📋 Test 2: Pagination (page_size=1)")
        print("-"*70)
        try:
            response = await client.get(
                f"{base_url}/api/reports/hovedbok/",
                params={
                    "client_id": test_data["client_id"],
                    "page_size": 1,
                    "page": 1
                }
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS")
                print(f"   Entries per page: {data['pagination']['page_size']}")
                print(f"   Current page: {data['pagination']['page']}")
                print(f"   Has next: {data['pagination']['has_next']}")
                print(f"   Has previous: {data['pagination']['has_prev']}")
            else:
                print(f"❌ FAILED: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        # Test 3: Date range filter
        print("\n" + "-"*70)
        print("📋 Test 3: Date Range Filter (last 30 days)")
        print("-"*70)
        try:
            today = date.today()
            start_date = (today - timedelta(days=30)).isoformat()
            end_date = today.isoformat()
            
            response = await client.get(
                f"{base_url}/api/reports/hovedbok/",
                params={
                    "client_id": test_data["client_id"],
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS")
                print(f"   Date range: {start_date} to {end_date}")
                print(f"   Entries found: {len(data['entries'])}")
                print(f"   Total in range: {data['summary']['total_entries']}")
            else:
                print(f"❌ FAILED: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        # Test 4: Sorting
        print("\n" + "-"*70)
        print("📋 Test 4: Sorting (by accounting_date desc)")
        print("-"*70)
        try:
            response = await client.get(
                f"{base_url}/api/reports/hovedbok/",
                params={
                    "client_id": test_data["client_id"],
                    "sort_by": "accounting_date",
                    "sort_order": "desc",
                    "page_size": 3
                }
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS")
                print(f"   Entries (newest first):")
                for entry in data['entries']:
                    print(f"   - {entry['full_voucher']}: {entry['accounting_date']} - {entry['description'][:50]}")
            else:
                print(f"❌ FAILED: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        # Test 5: Status filter
        print("\n" + "-"*70)
        print("📋 Test 5: Filter by status (posted)")
        print("-"*70)
        try:
            response = await client.get(
                f"{base_url}/api/reports/hovedbok/",
                params={
                    "client_id": test_data["client_id"],
                    "status": "posted"
                }
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS")
                print(f"   Posted entries: {len(data['entries'])}")
                print(f"   Filter applied: status={data['summary']['filters_applied']['status']}")
            else:
                print(f"❌ FAILED: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        # Test 6: Exclude details
        print("\n" + "-"*70)
        print("📋 Test 6: Exclude lines and invoice details")
        print("-"*70)
        try:
            response = await client.get(
                f"{base_url}/api/reports/hovedbok/",
                params={
                    "client_id": test_data["client_id"],
                    "include_lines": False,
                    "include_invoice": False,
                    "page_size": 1
                }
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS")
                if data['entries']:
                    entry = data['entries'][0]
                    has_lines = 'lines' in entry
                    has_invoice = 'invoice' in entry
                    print(f"   Lines included: {has_lines}")
                    print(f"   Invoice included: {has_invoice}")
                    if not has_lines and not has_invoice:
                        print(f"   ✅ Details correctly excluded")
            else:
                print(f"❌ FAILED: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        # Test 7: Get single entry by ID (if available)
        if test_data.get('gl_entry_id'):
            print("\n" + "-"*70)
            print(f"📋 Test 7: GET single entry by ID")
            print("-"*70)
            try:
                response = await client.get(
                    f"{base_url}/api/reports/hovedbok/{test_data['gl_entry_id']}"
                )
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS")
                    print(f"   Voucher: {data['full_voucher']}")
                    print(f"   Description: {data['description']}")
                    print(f"   Date: {data['accounting_date']}")
                    print(f"   Status: {data['status']}")
                    print(f"   Lines: {len(data.get('lines', []))}")
                    if data.get('totals'):
                        print(f"   Debit: {data['totals']['debit']:.2f}")
                        print(f"   Credit: {data['totals']['credit']:.2f}")
                        print(f"   Balanced: {'✅' if data['totals']['balanced'] else '❌'}")
                    if data.get('invoice'):
                        print(f"   Invoice: {data['invoice']['invoice_number']}")
                        if data['invoice'].get('vendor'):
                            print(f"   Vendor: {data['invoice']['vendor']['name']}")
                else:
                    print(f"❌ FAILED: {response.text}")
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
        
        # Test 8: Error handling - invalid UUID
        print("\n" + "-"*70)
        print("📋 Test 8: Error Handling (invalid client_id)")
        print("-"*70)
        try:
            response = await client.get(
                f"{base_url}/api/reports/hovedbok/",
                params={"client_id": "not-a-uuid"}
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 422:
                print(f"✅ Correctly rejected invalid UUID (422 Unprocessable Entity)")
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\n" + "="*70)
    print("✅ All API tests completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_api())
