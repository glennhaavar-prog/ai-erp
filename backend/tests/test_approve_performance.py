"""
Performance Test for Invoice Approval Endpoint
Bug Fix #2: Ensure approval completes in < 5 seconds

This test validates that the optimizations reduce DB round-trips
and complete voucher creation within acceptable time limits.
"""
import pytest
import asyncio
import time
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.voucher_service import VoucherGenerator
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority


@pytest.fixture
async def test_vendor(db_session: AsyncSession):
    """Create a test vendor"""
    vendor = Vendor(
        id=uuid4(),
        client_id=uuid4(),
        name="Test Supplier AS",
        org_number="123456789",
        country="NO"
    )
    db_session.add(vendor)
    await db_session.commit()
    await db_session.refresh(vendor)
    return vendor


@pytest.fixture
async def test_invoice(db_session: AsyncSession, test_vendor: Vendor):
    """Create a test invoice"""
    invoice = VendorInvoice(
        id=uuid4(),
        client_id=test_vendor.client_id,
        vendor_id=test_vendor.id,
        invoice_number="TEST-2026-001",
        invoice_date=date.today(),
        due_date=date.today(),
        amount_excl_vat=Decimal("10000.00"),
        vat_amount=Decimal("2500.00"),
        total_amount=Decimal("12500.00"),
        currency="NOK",
        ai_confidence_score=Decimal("0.95"),
        ai_reasoning="High confidence - standard invoice",
        ai_booking_suggestion={
            "account": "6420",
            "description": "Office supplies"
        },
        review_status="pending"
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    return invoice


@pytest.fixture
async def test_review_item(db_session: AsyncSession, test_invoice: VendorInvoice):
    """Create a review queue item"""
    review = ReviewQueue(
        id=uuid4(),
        client_id=test_invoice.client_id,
        source_type="vendor_invoice",
        source_id=test_invoice.id,
        status=ReviewStatus.PENDING,
        priority=ReviewPriority.MEDIUM,
        issue_category="vouchers",
        issue_description="Standard vendor invoice for approval",
        ai_confidence=95,
        ai_reasoning="High confidence booking",
        ai_suggestion=test_invoice.ai_booking_suggestion
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    return review


@pytest.mark.asyncio
async def test_voucher_creation_performance(
    db_session: AsyncSession,
    test_invoice: VendorInvoice,
    test_vendor: Vendor
):
    """
    Test that voucher creation completes in < 5 seconds
    
    PERFORMANCE TARGET: < 5 seconds (was 30+ seconds before fix)
    """
    generator = VoucherGenerator(db_session)
    
    start_time = time.time()
    
    try:
        voucher_dto = await generator.create_voucher_from_invoice(
            invoice_id=test_invoice.id,
            tenant_id=test_invoice.client_id,
            user_id="test_user",
            accounting_date=None,
            override_account=None
        )
        
        elapsed = time.time() - start_time
        
        # Assert performance target
        assert elapsed < 5.0, f"Voucher creation took {elapsed:.3f}s (target: < 5s)"
        
        # Assert voucher was created correctly
        assert voucher_dto is not None
        assert voucher_dto.is_balanced is True
        assert voucher_dto.total_debit == voucher_dto.total_credit
        assert len(voucher_dto.lines) == 3  # Expense + VAT + Payable
        
        print(f"✅ Voucher creation completed in {elapsed:.3f}s (target: < 5s)")
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        pytest.fail(f"Voucher creation timed out after {elapsed:.3f}s")


@pytest.mark.asyncio
async def test_approve_endpoint_no_timeout(
    db_session: AsyncSession,
    test_review_item: ReviewQueue,
    test_invoice: VendorInvoice
):
    """
    Test that approval endpoint completes without timeout
    
    This simulates the actual API endpoint flow
    """
    from app.services.voucher_service import VoucherGenerator
    
    start_time = time.time()
    
    # Simulate the approve endpoint logic
    generator = VoucherGenerator(db_session)
    
    try:
        # With 10 second timeout (as in the endpoint)
        voucher_dto = await asyncio.wait_for(
            generator.create_voucher_from_invoice(
                invoice_id=test_review_item.source_id,
                tenant_id=test_review_item.client_id,
                user_id="review_queue_user",
                accounting_date=None,
                override_account=test_review_item.ai_suggestion.get('account')
            ),
            timeout=10.0
        )
        
        elapsed = time.time() - start_time
        
        # Update review status
        test_review_item.status = ReviewStatus.APPROVED
        test_review_item.resolved_at = datetime.utcnow()
        
        await db_session.commit()
        
        assert elapsed < 10.0
        assert voucher_dto is not None
        
        print(f"✅ Approval completed in {elapsed:.3f}s (timeout: 10s)")
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        pytest.fail(f"Approval timed out after {elapsed:.3f}s")


@pytest.mark.asyncio
async def test_batch_account_loading(db_session: AsyncSession, test_vendor: Vendor):
    """
    Test that batch account loading is faster than individual queries
    """
    generator = VoucherGenerator(db_session)
    
    account_numbers = ["6420", "2740", "2400", "6300", "5000"]
    
    # Test batch loading
    start_batch = time.time()
    account_map = await generator._get_account_names_batch(
        test_vendor.client_id,
        account_numbers
    )
    elapsed_batch = time.time() - start_batch
    
    # Test individual loading (old way)
    start_individual = time.time()
    for account_num in account_numbers:
        await generator._get_account_name(test_vendor.client_id, account_num)
    elapsed_individual = time.time() - start_individual
    
    # Batch should be faster
    assert elapsed_batch < elapsed_individual, \
        f"Batch loading slower than individual: {elapsed_batch:.3f}s vs {elapsed_individual:.3f}s"
    
    # Verify all accounts loaded
    assert len(account_map) == len(account_numbers)
    
    print(f"✅ Batch loading: {elapsed_batch:.3f}s, Individual: {elapsed_individual:.3f}s")
    print(f"   Speedup: {elapsed_individual / elapsed_batch:.2f}x")


if __name__ == "__main__":
    print("Run with: pytest tests/test_approve_performance.py -v -s")
