"""
Tests for Accruals (Periodisering)
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accrual import Accrual
from app.models.accrual_posting import AccrualPosting
from app.models.general_ledger import GeneralLedger
from app.services.accrual_service import AccrualService


@pytest.mark.asyncio
async def test_create_monthly_accrual(db_session: AsyncSession, test_client_id):
    """Test creating a 12-month accrual with monthly postings"""
    
    service = AccrualService()
    
    result = await service.create_accrual(
        db=db_session,
        client_id=test_client_id,
        description="Forsikring 2026",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 12, 31),
        total_amount=Decimal("12000.00"),
        balance_account="1580",  # Forskuddsbetalte kostnader
        result_account="6820",   # Forsikringskostnader
        frequency="monthly",
        created_by="test_user"
    )
    
    assert result["success"] is True
    assert "accrual_id" in result
    assert len(result["posting_schedule"]) == 12
    
    # Verify each posting is 1000 NOK
    for posting in result["posting_schedule"]:
        assert posting["amount"] == Decimal("1000.00")


@pytest.mark.asyncio
async def test_accrual_posting_creates_gl_entry(db_session: AsyncSession, test_client_id):
    """Test that posting an accrual creates a balanced GL entry"""
    
    service = AccrualService()
    
    # Create accrual
    accrual_result = await service.create_accrual(
        db=db_session,
        client_id=test_client_id,
        description="Test accrual",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 3, 31),
        total_amount=Decimal("3000.00"),
        balance_account="1580",
        result_account="6820",
        frequency="monthly",
        created_by="test_user"
    )
    
    # Get first posting
    from sqlalchemy import select
    result = await db_session.execute(
        select(AccrualPosting)
        .where(AccrualPosting.accrual_id == accrual_result["accrual_id"])
        .order_by(AccrualPosting.posting_date)
    )
    first_posting = result.scalars().first()
    
    # Post it
    posting_result = await service.post_accrual(
        db=db_session,
        posting_id=first_posting.id,
        posted_by="test_user"
    )
    
    assert posting_result["success"] is True
    assert posting_result["amount"] == 1000.00
    
    # Verify GL entry created
    gl_result = await db_session.execute(
        select(GeneralLedger)
        .where(GeneralLedger.id == posting_result["gl_entry_id"])
    )
    gl_entry = gl_result.scalar_one()
    
    assert gl_entry is not None
    assert gl_entry.voucher_series == "P"  # Periodisering
    assert len(gl_entry.lines) == 2  # Debit + Credit
    
    # Verify balance
    total_debit = sum(line.debit_amount for line in gl_entry.lines)
    total_credit = sum(line.credit_amount for line in gl_entry.lines)
    assert total_debit == total_credit == Decimal("1000.00")


@pytest.mark.asyncio
async def test_auto_post_due_accruals(db_session: AsyncSession, test_client_id):
    """Test that auto-posting picks up due accruals"""
    
    service = AccrualService()
    
    # Create accrual with posting date in the past
    await service.create_accrual(
        db=db_session,
        client_id=test_client_id,
        description="Overdue accrual",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 2, 28),
        total_amount=Decimal("2000.00"),
        balance_account="1580",
        result_account="6820",
        frequency="monthly",
        created_by="test_user"
    )
    
    # Auto-post everything up to today
    result = await service.auto_post_due_accruals(
        db=db_session,
        as_of_date=date(2026, 2, 7)
    )
    
    assert result["success"] is True
    assert result["posted_count"] >= 1
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_quarterly_accrual(db_session: AsyncSession, test_client_id):
    """Test creating a quarterly accrual"""
    
    service = AccrualService()
    
    result = await service.create_accrual(
        db=db_session,
        client_id=test_client_id,
        description="Quarterly rent",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 12, 31),
        total_amount=Decimal("12000.00"),
        balance_account="1580",
        result_account="6800",
        frequency="quarterly",
        created_by="test_user"
    )
    
    assert result["success"] is True
    assert len(result["posting_schedule"]) == 4  # 4 quarters
    
    # Each posting should be 3000 NOK
    for posting in result["posting_schedule"]:
        assert posting["amount"] == Decimal("3000.00")


@pytest.mark.asyncio
async def test_cancel_accrual_stops_future_postings(db_session: AsyncSession, test_client_id):
    """Test that cancelling an accrual stops future postings"""
    
    service = AccrualService()
    
    # Create accrual
    accrual_result = await service.create_accrual(
        db=db_session,
        client_id=test_client_id,
        description="To be cancelled",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 6, 30),
        total_amount=Decimal("6000.00"),
        balance_account="1580",
        result_account="6820",
        frequency="monthly",
        created_by="test_user"
    )
    
    accrual_id = accrual_result["accrual_id"]
    
    # Verify accrual is active
    from sqlalchemy import select
    result = await db_session.execute(
        select(Accrual).where(Accrual.id == accrual_id)
    )
    accrual = result.scalar_one()
    assert accrual.status == "active"
    
    # Count pending postings
    result = await db_session.execute(
        select(AccrualPosting)
        .where(
            AccrualPosting.accrual_id == accrual_id,
            AccrualPosting.status == "pending"
        )
    )
    pending_before = len(result.scalars().all())
    assert pending_before == 6
    
    # Cancel accrual (this would normally be done via API endpoint)
    accrual.status = "cancelled"
    
    # Cancel all pending postings
    result = await db_session.execute(
        select(AccrualPosting)
        .where(
            AccrualPosting.accrual_id == accrual_id,
            AccrualPosting.status == "pending"
        )
    )
    for posting in result.scalars().all():
        posting.status = "cancelled"
    
    await db_session.commit()
    
    # Verify no pending postings remain
    result = await db_session.execute(
        select(AccrualPosting)
        .where(
            AccrualPosting.accrual_id == accrual_id,
            AccrualPosting.status == "pending"
        )
    )
    pending_after = len(result.scalars().all())
    assert pending_after == 0
