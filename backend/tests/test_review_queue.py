"""
Comprehensive tests for Review Queue API and Service
"""
import pytest
from uuid import uuid4
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.tenant import Tenant
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.vendor_invoice import VendorInvoice
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
from app.services.review_queue_service import ReviewQueueService, get_review_queue_stats


class TestReviewQueueService:
    """Test ReviewQueueService business logic"""
    
    @pytest.fixture
    async def setup_test_data(self, db_session: AsyncSession):
        """Setup test data"""
        # Create tenant
        tenant = Tenant(
            id=uuid4(),
            name="Test Accounting Firm",
            org_number="999999999",
            subscription_tier="professional",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(tenant)
        
        # Create client
        client = Client(
            id=uuid4(),
            tenant_id=tenant.id,
            client_number="TEST001",
            name="Test Client AS",
            org_number="888888888",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(client)
        
        # Create vendor
        vendor = Vendor(
            id=uuid4(),
            client_id=client.id,
            name="Test Supplier AS",
            org_number="777777777",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(vendor)
        
        # Create vendor invoice
        invoice = VendorInvoice(
            id=uuid4(),
            client_id=client.id,
            vendor_id=vendor.id,
            invoice_number="INV-001",
            invoice_date=date.today(),
            due_date=date(2025, 3, 1),
            amount_excl_vat=Decimal("8000.00"),
            vat_amount=Decimal("2000.00"),
            total_amount=Decimal("10000.00"),
            currency="NOK",
            review_status="pending",
            ai_processed=True,
            ai_confidence_score=75,
            ai_booking_suggestion={
                "lines": [
                    {"account_number": "6000", "debit": 8000, "credit": 0},
                    {"account_number": "2700", "debit": 2000, "credit": 0},
                    {"account_number": "2400", "debit": 0, "credit": 10000}
                ]
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(invoice)
        
        # Create review queue item
        review = ReviewQueue(
            id=uuid4(),
            client_id=client.id,
            source_type="vendor_invoice",
            source_id=invoice.id,
            priority=ReviewPriority.MEDIUM,
            status=ReviewStatus.PENDING,
            issue_category=IssueCategory.LOW_CONFIDENCE,
            issue_description="AI confidence: 75% | Low historical similarity",
            ai_suggestion={
                "lines": [
                    {"account_number": "6000", "debit": 8000, "credit": 0},
                    {"account_number": "2700", "debit": 2000, "credit": 0},
                    {"account_number": "2400", "debit": 0, "credit": 10000}
                ]
            },
            ai_confidence=75,
            ai_reasoning="Vendor has limited history",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(review)
        
        await db_session.commit()
        await db_session.refresh(review)
        await db_session.refresh(invoice)
        await db_session.refresh(vendor)
        await db_session.refresh(client)
        
        return {
            'tenant': tenant,
            'client': client,
            'vendor': vendor,
            'invoice': invoice,
            'review': review
        }
    
    @pytest.mark.asyncio
    async def test_get_pending_reviews(self, db_session: AsyncSession, setup_test_data):
        """Test getting pending reviews"""
        service = ReviewQueueService(db_session)
        
        items = await service.get_pending_reviews()
        
        assert len(items) >= 1
        assert items[0].review_status == "pending"
        assert items[0].vendor_name == "Test Supplier AS"
        assert items[0].amount == Decimal("10000.00")
    
    @pytest.mark.asyncio
    async def test_get_pending_reviews_with_filters(self, db_session: AsyncSession, setup_test_data):
        """Test getting pending reviews with filters"""
        test_data = setup_test_data
        service = ReviewQueueService(db_session)
        
        filters = {
            'status': 'pending',
            'client_id': str(test_data['client'].id)
        }
        items = await service.get_pending_reviews(filters)
        
        assert len(items) >= 1
        assert items[0].client_id == str(test_data['client'].id)
    
    @pytest.mark.asyncio
    async def test_get_review_detail(self, db_session: AsyncSession, setup_test_data):
        """Test getting review detail"""
        test_data = setup_test_data
        service = ReviewQueueService(db_session)
        
        detail = await service.get_review_detail(str(test_data['review'].id))
        
        assert detail.id == str(test_data['review'].id)
        assert detail.vendor_name == "Test Supplier AS"
        assert detail.invoice_number == "INV-001"
        assert detail.amount == Decimal("10000.00")
        assert detail.confidence_score == 0.75
        assert detail.ai_reasoning == "Vendor has limited history"
    
    @pytest.mark.asyncio
    async def test_approve_invoice(self, db_session: AsyncSession, setup_test_data):
        """Test approving an invoice"""
        test_data = setup_test_data
        service = ReviewQueueService(db_session)
        user_id = str(uuid4())
        
        # Approve the invoice
        response = await service.approve_invoice(
            invoice_id=str(test_data['review'].id),
            user_id=user_id,
            notes="Looks good!"
        )
        
        assert response.success is True
        assert "approved" in response.message.lower()
        
        # Verify status changed
        await db_session.refresh(test_data['review'])
        await db_session.refresh(test_data['invoice'])
        
        assert test_data['review'].status == ReviewStatus.APPROVED
        assert test_data['invoice'].review_status == "approved"
        assert test_data['review'].resolved_at is not None
    
    @pytest.mark.asyncio
    async def test_approve_already_approved(self, db_session: AsyncSession, setup_test_data):
        """Test approving an already approved invoice (should fail)"""
        test_data = setup_test_data
        service = ReviewQueueService(db_session)
        user_id = str(uuid4())
        
        # Approve once
        await service.approve_invoice(
            invoice_id=str(test_data['review'].id),
            user_id=user_id,
            notes="First approval"
        )
        
        # Try to approve again
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.approve_invoice(
                invoice_id=str(test_data['review'].id),
                user_id=user_id,
                notes="Second approval"
            )
        
        assert exc_info.value.status_code == 400
        assert "already" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_reject_invoice(self, db_session: AsyncSession, setup_test_data):
        """Test rejecting an invoice"""
        test_data = setup_test_data
        service = ReviewQueueService(db_session)
        user_id = str(uuid4())
        
        # Reject the invoice
        response = await service.reject_invoice(
            invoice_id=str(test_data['review'].id),
            user_id=user_id,
            reason="Invalid VAT calculation"
        )
        
        assert response.success is True
        assert "rejected" in response.message.lower()
        
        # Verify status changed
        await db_session.refresh(test_data['review'])
        await db_session.refresh(test_data['invoice'])
        
        assert test_data['review'].status == ReviewStatus.REJECTED
        assert test_data['invoice'].review_status == "rejected"
        assert test_data['review'].resolution_notes == "Invalid VAT calculation"
    
    @pytest.mark.asyncio
    async def test_update_confidence_score(self, db_session: AsyncSession, setup_test_data):
        """Test updating confidence score"""
        test_data = setup_test_data
        service = ReviewQueueService(db_session)
        
        # Update confidence score
        response = await service.update_confidence_score(
            invoice_id=str(test_data['review'].id),
            score=90.0
        )
        
        assert response.confidence_score == 0.90
        assert response.should_auto_approve is True
        
        # Verify priority changed
        await db_session.refresh(test_data['review'])
        assert test_data['review'].ai_confidence == 90
        assert test_data['review'].priority == ReviewPriority.LOW
    
    @pytest.mark.asyncio
    async def test_update_status(self, db_session: AsyncSession, setup_test_data):
        """Test updating review status"""
        test_data = setup_test_data
        service = ReviewQueueService(db_session)
        user_id = str(uuid4())
        
        # Update status to in_progress
        response = await service.update_status(
            invoice_id=str(test_data['review'].id),
            new_status='in_progress',
            user_id=user_id,
            notes="Working on it"
        )
        
        assert response['success'] is True
        assert response['new_status'] == 'in_progress'
        
        # Verify status changed
        await db_session.refresh(test_data['review'])
        assert test_data['review'].status == ReviewStatus.IN_PROGRESS


class TestReviewQueueAPI:
    """Test Review Queue REST API endpoints"""
    
    @pytest.fixture
    async def setup_api_test_data(self, db_session: AsyncSession):
        """Setup test data for API tests"""
        # Create tenant
        tenant = Tenant(
            id=uuid4(),
            name="API Test Firm",
            org_number="111111111",
            subscription_tier="professional",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(tenant)
        
        # Create client
        client = Client(
            id=uuid4(),
            tenant_id=tenant.id,
            client_number="API001",
            name="API Test Client",
            org_number="222222222",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(client)
        
        # Create vendor
        vendor = Vendor(
            id=uuid4(),
            client_id=client.id,
            name="API Test Vendor",
            org_number="333333333",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(vendor)
        
        # Create invoice
        invoice = VendorInvoice(
            id=uuid4(),
            client_id=client.id,
            vendor_id=vendor.id,
            invoice_number="API-INV-001",
            invoice_date=date.today(),
            due_date=date(2025, 3, 15),
            amount_excl_vat=Decimal("5000.00"),
            vat_amount=Decimal("1250.00"),
            total_amount=Decimal("6250.00"),
            currency="NOK",
            review_status="pending",
            ai_confidence_score=65,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(invoice)
        
        # Create review queue item
        review = ReviewQueue(
            id=uuid4(),
            client_id=client.id,
            source_type="vendor_invoice",
            source_id=invoice.id,
            priority=ReviewPriority.HIGH,
            status=ReviewStatus.PENDING,
            issue_category=IssueCategory.UNKNOWN_VENDOR,
            issue_description="New vendor without history",
            ai_confidence=65,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(review)
        
        await db_session.commit()
        
        return {
            'tenant': tenant,
            'client': client,
            'vendor': vendor,
            'invoice': invoice,
            'review': review
        }
    
    @pytest.mark.asyncio
    async def test_get_review_queue_list(self, async_client: AsyncClient, setup_api_test_data):
        """Test GET /api/review-queue/ endpoint"""
        response = await async_client.get("/api/review-queue/")
        
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert len(data['items']) >= 1
    
    @pytest.mark.asyncio
    async def test_get_review_queue_with_filters(self, async_client: AsyncClient, setup_api_test_data):
        """Test GET /api/review-queue/ with filters"""
        test_data = setup_api_test_data
        
        response = await async_client.get(
            "/api/review-queue/",
            params={'status': 'pending', 'client_id': str(test_data['client'].id)}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) >= 1
    
    @pytest.mark.asyncio
    async def test_get_review_queue_stats(self, async_client: AsyncClient, setup_api_test_data):
        """Test GET /api/review-queue/stats endpoint"""
        response = await async_client.get("/api/review-queue/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert 'pending' in data
        assert 'approved' in data
        assert 'rejected' in data
        assert 'average_confidence' in data
    
    @pytest.mark.asyncio
    async def test_get_review_item_detail(self, async_client: AsyncClient, setup_api_test_data):
        """Test GET /api/review-queue/{item_id} endpoint"""
        test_data = setup_api_test_data
        
        response = await async_client.get(f"/api/review-queue/{test_data['review'].id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == str(test_data['review'].id)
        assert data['invoice_number'] == "API-INV-001"
    
    @pytest.mark.asyncio
    async def test_get_review_item_not_found(self, async_client: AsyncClient):
        """Test GET /api/review-queue/{item_id} with invalid ID"""
        fake_id = str(uuid4())
        
        response = await async_client.get(f"/api/review-queue/{fake_id}")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_approve_review_item(self, async_client: AsyncClient, setup_api_test_data):
        """Test POST /api/review-queue/{item_id}/approve endpoint"""
        test_data = setup_api_test_data
        
        response = await async_client.post(
            f"/api/review-queue/{test_data['review'].id}/approve",
            json={'notes': 'API test approval'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'approved'
    
    @pytest.mark.asyncio
    async def test_reject_review_item(self, async_client: AsyncClient, setup_api_test_data):
        """Test POST /api/review-queue/{item_id}/reject endpoint (if exists)"""
        # This tests the reject endpoint if implemented
        # Note: Current API may not have this endpoint yet
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_approvals(self, async_client: AsyncClient, setup_api_test_data, db_session: AsyncSession):
        """Test concurrent approval attempts (locking test)"""
        test_data = setup_api_test_data
        review_id = str(test_data['review'].id)
        
        # First approval should succeed
        response1 = await async_client.post(
            f"/api/review-queue/{review_id}/approve",
            json={'notes': 'First approval'}
        )
        
        # Second approval should fail (already approved)
        response2 = await async_client.post(
            f"/api/review-queue/{review_id}/approve",
            json={'notes': 'Second approval'}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 400


class TestReviewQueueStats:
    """Test review queue statistics"""
    
    @pytest.mark.asyncio
    async def test_get_queue_stats(self, db_session: AsyncSession):
        """Test getting queue statistics"""
        stats = await get_review_queue_stats(db_session)
        
        assert 'pending' in stats
        assert 'approved' in stats
        assert 'rejected' in stats
        assert 'average_confidence' in stats
        assert 'approval_rate' in stats
        assert isinstance(stats['pending'], int)
        assert isinstance(stats['average_confidence'], float)


class TestReviewQueueErrorHandling:
    """Test error handling in review queue"""
    
    @pytest.mark.asyncio
    async def test_approve_invalid_uuid(self, db_session: AsyncSession):
        """Test approving with invalid UUID"""
        service = ReviewQueueService(db_session)
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.approve_invoice(
                invoice_id="not-a-uuid",
                user_id=str(uuid4()),
                notes="Test"
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid UUID" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_approve_nonexistent_invoice(self, db_session: AsyncSession):
        """Test approving nonexistent invoice"""
        service = ReviewQueueService(db_session)
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.approve_invoice(
                invoice_id=str(uuid4()),
                user_id=str(uuid4()),
                notes="Test"
            )
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_confidence_invalid_score(self, db_session: AsyncSession, setup_test_data):
        """Test updating confidence with invalid score"""
        test_data = setup_test_data
        service = ReviewQueueService(db_session)
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.update_confidence_score(
                invoice_id=str(test_data['review'].id),
                score=150.0  # Invalid: > 100
            )
        
        assert exc_info.value.status_code == 400


# Fixtures for pytest
@pytest.fixture
async def db_session():
    """Database session fixture"""
    from app.database import get_db, init_db
    
    # Initialize test database
    await init_db()
    
    # Get session
    async for session in get_db():
        yield session


@pytest.fixture
async def async_client(db_session):
    """Async HTTP client fixture"""
    from httpx import AsyncClient
    from app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
