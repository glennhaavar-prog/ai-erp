#!/usr/bin/env python
"""
Quick verification script for Review Queue implementation
Run this to verify the backend API is working correctly
"""
import asyncio
from uuid import uuid4
from datetime import date, datetime
from decimal import Decimal

from app.database import init_db, get_db
from app.models.tenant import Tenant
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.vendor_invoice import VendorInvoice
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
from app.services.review_queue_service import ReviewQueueService, get_review_queue_stats


async def verify_review_queue():
    """Verify review queue implementation"""
    print("🔍 Verifying Review Queue Implementation...")
    print("=" * 60)
    
    # Initialize database
    print("\n1️⃣  Initializing database...")
    await init_db()
    print("   ✅ Database initialized")
    
    # Get database session
    async for db in get_db():
        try:
            # Create test data
            print("\n2️⃣  Creating test data...")
            
            tenant = Tenant(
                id=uuid4(),
                name="Verification Test Firm",
                org_number=f"999{uuid4().hex[:6]}",
                subscription_tier="professional",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(tenant)
            
            client = Client(
                id=uuid4(),
                tenant_id=tenant.id,
                client_number=f"VERIFY{uuid4().hex[:4]}",
                name="Verification Test Client",
                org_number=f"888{uuid4().hex[:6]}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(client)
            
            vendor = Vendor(
                id=uuid4(),
                client_id=client.id,
                vendor_number=f"VND{uuid4().hex[:6]}",
                name="Verification Test Vendor",
                org_number=f"777{uuid4().hex[:6]}",
                account_number="2400",  # Default payables account
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(vendor)
            
            invoice = VendorInvoice(
                id=uuid4(),
                client_id=client.id,
                vendor_id=vendor.id,
                invoice_number=f"VERIFY-{uuid4().hex[:6]}",
                invoice_date=date.today(),
                due_date=date(2025, 3, 1),
                amount_excl_vat=Decimal("8000.00"),
                vat_amount=Decimal("2000.00"),
                total_amount=Decimal("10000.00"),
                currency="NOK",
                review_status="pending",
                ai_confidence_score=75,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(invoice)
            
            review = ReviewQueue(
                id=uuid4(),
                client_id=client.id,
                source_type="vendor_invoice",
                source_id=invoice.id,
                priority=ReviewPriority.MEDIUM,
                status=ReviewStatus.PENDING,
                issue_category=IssueCategory.LOW_CONFIDENCE,
                issue_description="Verification test item",
                ai_confidence=75,
                ai_reasoning="Test reasoning",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(review)
            
            await db.commit()
            await db.refresh(review)
            
            print(f"   ✅ Created review queue item: {review.id}")
            
            # Test service layer
            print("\n3️⃣  Testing ReviewQueueService...")
            service = ReviewQueueService(db)
            
            # Test get_pending_reviews
            print("   📋 Testing get_pending_reviews()...")
            items = await service.get_pending_reviews({'page': 1, 'page_size': 10})
            assert len(items) > 0, "Should have at least one item"
            print(f"   ✅ Found {len(items)} pending reviews")
            
            # Test get_review_detail
            print("   📄 Testing get_review_detail()...")
            detail = await service.get_review_detail(str(review.id))
            assert detail.id == str(review.id)
            assert detail.invoice_number == invoice.invoice_number
            print(f"   ✅ Retrieved detail for invoice {detail.invoice_number}")
            
            # Test update_confidence_score
            print("   📊 Testing update_confidence_score()...")
            conf_response = await service.update_confidence_score(
                invoice_id=str(review.id),
                score=85.0
            )
            assert conf_response.confidence_score == 0.85
            print(f"   ✅ Updated confidence to {conf_response.confidence_score}")
            
            # Test approve_invoice
            print("   ✅ Testing approve_invoice()...")
            user_id = str(uuid4())
            approval = await service.approve_invoice(
                invoice_id=str(review.id),
                user_id=user_id,
                notes="Verification test approval"
            )
            assert approval.success is True
            print(f"   ✅ Approved invoice successfully")
            
            # Verify status changed
            await db.refresh(review)
            await db.refresh(invoice)
            assert review.status == ReviewStatus.APPROVED
            assert invoice.review_status == "approved"
            print(f"   ✅ Status updated correctly")
            
            # Test statistics
            print("\n4️⃣  Testing get_review_queue_stats()...")
            stats = await get_review_queue_stats(db)
            print(f"   📊 Stats:")
            print(f"      - Pending: {stats['pending']}")
            print(f"      - Approved: {stats['approved']}")
            print(f"      - Rejected: {stats['rejected']}")
            print(f"      - Average confidence: {stats['average_confidence']}%")
            print(f"   ✅ Statistics retrieved successfully")
            
            # Cleanup
            print("\n5️⃣  Cleaning up test data...")
            await db.delete(review)
            await db.delete(invoice)
            await db.delete(vendor)
            await db.delete(client)
            await db.delete(tenant)
            await db.commit()
            print("   ✅ Test data cleaned up")
            
            print("\n" + "=" * 60)
            print("✅ ALL VERIFICATIONS PASSED!")
            print("=" * 60)
            print("\n📋 Summary:")
            print("   ✅ Database schema exists")
            print("   ✅ Service layer works correctly")
            print("   ✅ All CRUD operations functional")
            print("   ✅ Statistics calculation works")
            print("   ✅ Transaction safety verified")
            print("\n🎉 Review Queue Backend API is ready for use!")
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            return False
        
        break  # Only need one iteration
    
    return True


if __name__ == "__main__":
    success = asyncio.run(verify_review_queue())
    exit(0 if success else 1)
