#!/usr/bin/env python3
"""
Quick test for the verification API endpoint
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import get_db, init_db
from app.api.routes.dashboard import get_verification_status


async def test_verification_endpoint():
    """Test the verification endpoint"""
    print("🧪 Testing Receipt Verification API Endpoint\n")
    
    # Initialize database
    await init_db()
    
    # Get database session
    async for db in get_db():
        try:
            # Call the endpoint function
            result = await get_verification_status(db)
            
            print("✅ API Response:")
            print(f"   Overall Status: {result['overall_status']}")
            print(f"   Message: {result['status_message']}")
            print(f"\n📊 EHF Invoices:")
            print(f"   Received: {result['ehf_invoices']['received']}")
            print(f"   Processed: {result['ehf_invoices']['processed']}")
            print(f"   Booked: {result['ehf_invoices']['booked']}")
            print(f"   Pending: {result['ehf_invoices']['pending']}")
            print(f"   Status: {result['ehf_invoices']['status']}")
            print(f"\n🏦 Bank Transactions:")
            print(f"   Total: {result['bank_transactions']['total']}")
            print(f"   Booked: {result['bank_transactions']['booked']}")
            print(f"   Status: {result['bank_transactions']['status']}")
            print(f"\n📋 Review Queue:")
            print(f"   Pending: {result['review_queue']['pending']}")
            print(f"   Status: {result['review_queue']['status']}")
            print(f"\n📈 Summary:")
            print(f"   Total Items: {result['summary']['total_items']}")
            print(f"   Fully Tracked: {result['summary']['fully_tracked']}")
            print(f"   Needs Attention: {result['summary']['needs_attention']}")
            print(f"   Completion Rate: {result['summary']['completion_rate']}%")
            
            print("\n✅ Test PASSED - API endpoint working correctly!")
            return True
            
        except Exception as e:
            print(f"\n❌ Test FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    result = asyncio.run(test_verification_endpoint())
    sys.exit(0 if result else 1)
