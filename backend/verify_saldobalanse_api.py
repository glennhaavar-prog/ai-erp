"""
Quick API verification script for Saldobalanse endpoints
Run this after starting the server to verify all endpoints work
"""
import requests
import json
from datetime import date

# Test configuration
BASE_URL = "http://localhost:8000"
CLIENT_ID = "2f694acf-938c-43c5-a34d-87eb5b7f5dc8"

def test_json_endpoint():
    """Test JSON endpoint"""
    print("\n1️⃣ Testing JSON endpoint...")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/reports/saldobalanse/"
    params = {
        "client_id": CLIENT_ID,
        "from_date": "2026-01-01",
        "to_date": "2026-01-31",
        "include_summary": True
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Accounts returned: {len(data['accounts'])}")
        print(f"✅ Summary included: {data.get('summary') is not None}")
        
        if data.get('summary'):
            summary = data['summary']
            print(f"\n📊 Summary:")
            print(f"   Total accounts: {summary['total_accounts']}")
            print(f"   Total debit:    {summary['total_debit']:,.2f}")
            print(f"   Total credit:   {summary['total_credit']:,.2f}")
            print(f"   Balanced:       {summary['balance_check']['balanced']}")
        
        # Show first account
        if data['accounts']:
            acc = data['accounts'][0]
            print(f"\n📝 First account:")
            print(f"   {acc['account_number']} - {acc['account_name']}")
            print(f"   Opening: {acc['opening_balance']:,.2f}")
            print(f"   Current: {acc['current_balance']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_excel_endpoint():
    """Test Excel export endpoint"""
    print("\n2️⃣ Testing Excel export endpoint...")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/reports/saldobalanse/export/excel/"
    params = {
        "client_id": CLIENT_ID,
        "from_date": "2026-01-01",
        "to_date": "2026-01-31"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Content-Type: {response.headers.get('content-type')}")
        print(f"✅ File size: {len(response.content)} bytes")
        
        # Check if it's actually an Excel file
        if response.content[:4] == b'PK\x03\x04':  # ZIP signature (xlsx is a zip)
            print(f"✅ Valid Excel file (XLSX format)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_pdf_endpoint():
    """Test PDF export endpoint"""
    print("\n3️⃣ Testing PDF export endpoint...")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/reports/saldobalanse/export/pdf/"
    params = {
        "client_id": CLIENT_ID,
        "from_date": "2026-01-01",
        "to_date": "2026-01-31"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Content-Type: {response.headers.get('content-type')}")
        print(f"✅ File size: {len(response.content)} bytes")
        
        # Check if it's actually a PDF file
        if response.content[:4] == b'%PDF':
            print(f"✅ Valid PDF file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_account_class_filter():
    """Test account class filtering"""
    print("\n4️⃣ Testing account class filter...")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/reports/saldobalanse/"
    params = {
        "client_id": CLIENT_ID,
        "account_class": "1",  # Assets only
        "include_summary": False
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Accounts returned: {len(data['accounts'])}")
        
        # Verify all accounts start with "1"
        all_match = all(acc['account_number'].startswith('1') for acc in data['accounts'])
        
        if all_match:
            print(f"✅ All accounts match filter (start with '1')")
        else:
            print(f"❌ Some accounts don't match filter")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Saldobalanse API Verification")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test Client ID: {CLIENT_ID}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ Server is not responding. Please start the server:")
            print("   cd /home/ubuntu/.openclaw/workspace/ai-erp/backend")
            print("   source venv/bin/activate")
            print("   uvicorn app.main:app --reload")
            return
    except Exception as e:
        print(f"\n❌ Cannot connect to server: {e}")
        print("\nPlease start the server:")
        print("   cd /home/ubuntu/.openclaw/workspace/ai-erp/backend")
        print("   source venv/bin/activate")
        print("   uvicorn app.main:app --reload")
        return
    
    print("✅ Server is running\n")
    
    # Run tests
    results = []
    results.append(("JSON endpoint", test_json_endpoint()))
    results.append(("Excel export", test_excel_endpoint()))
    results.append(("PDF export", test_pdf_endpoint()))
    results.append(("Account class filter", test_account_class_filter()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")


if __name__ == "__main__":
    main()
