"""
Other Vouchers Review Queue API - For non-supplier-invoice voucher types
Handles employee expenses, inventory adjustments, manual corrections, etc.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.review_queue import (
    ReviewQueue,
    ReviewStatus,
    ReviewPriority,
    IssueCategory,
    VoucherType
)
from app.models.review_queue_feedback import ReviewQueueFeedback
from app.utils.audit import log_audit_event

router = APIRouter(prefix="/api/other-vouchers", tags=["Other Vouchers"])


class ApproveRequest(BaseModel):
    """Approve review item request"""
    notes: Optional[str] = None


class CorrectRequest(BaseModel):
    """Correct review item request"""
    bookingEntries: List[dict]
    notes: Optional[str] = None


# IMPORTANT: Specific routes MUST come before parameterized routes in FastAPI!
# Order: /stats, /pending, then /{voucher_id}


@router.get("/stats")
async def get_other_voucher_stats(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for other vouchers review queue
    
    Returns:
    - Total pending by type (employee_expense, inventory_adjustment, manual_correction, other)
    - Average confidence per type
    - Total approved/rejected today/this week/this month
    """
    # Validate client_id
    try:
        client_uuid = UUID(client_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid client_id format: {client_id}. Must be a valid UUID."
        )
    
    from sqlalchemy import cast, String
    
    # Base query - exclude supplier invoices
    base_query = select(ReviewQueue).where(
        and_(
            ReviewQueue.client_id == client_uuid,
            cast(ReviewQueue.type, String) != 'SUPPLIER_INVOICE'
        )
    )
    
    # Total pending by type
    pending_by_type = {}
    for voucher_type in VoucherType:
        if voucher_type == VoucherType.SUPPLIER_INVOICE:
            continue
        
        query = select(func.count()).where(
            and_(
                ReviewQueue.client_id == client_uuid,
                ReviewQueue.type == voucher_type,
                cast(ReviewQueue.status, String) == 'PENDING'
            )
        )
        result = await db.execute(query)
        count = result.scalar() or 0
        pending_by_type[voucher_type.value.lower()] = count
    
    # Average confidence per type
    avg_confidence_by_type = {}
    for voucher_type in VoucherType:
        if voucher_type == VoucherType.SUPPLIER_INVOICE:
            continue
        
        query = select(func.avg(ReviewQueue.ai_confidence)).where(
            and_(
                ReviewQueue.client_id == client_uuid,
                ReviewQueue.type == voucher_type,
                ReviewQueue.ai_confidence.isnot(None)
            )
        )
        result = await db.execute(query)
        avg_conf = result.scalar()
        avg_confidence_by_type[voucher_type.value.lower()] = (
            float(avg_conf) / 100.0 if avg_conf is not None else 0.0
        )
    
    # Time-based statistics
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = datetime(now.year, now.month, 1)
    
    async def count_status_in_period(status: ReviewStatus, start_date: datetime):
        query = select(func.count()).where(
            and_(
                ReviewQueue.client_id == client_uuid,
                cast(ReviewQueue.type, String) != 'SUPPLIER_INVOICE',
                cast(ReviewQueue.status, String) == status.value.upper(),
                ReviewQueue.resolved_at >= start_date
            )
        )
        result = await db.execute(query)
        return result.scalar() or 0
    
    # Count approved/corrected
    approved_today = await count_status_in_period(ReviewStatus.APPROVED, today_start)
    approved_week = await count_status_in_period(ReviewStatus.APPROVED, week_start)
    approved_month = await count_status_in_period(ReviewStatus.APPROVED, month_start)
    
    corrected_today = await count_status_in_period(ReviewStatus.CORRECTED, today_start)
    corrected_week = await count_status_in_period(ReviewStatus.CORRECTED, week_start)
    corrected_month = await count_status_in_period(ReviewStatus.CORRECTED, month_start)
    
    rejected_today = await count_status_in_period(ReviewStatus.REJECTED, today_start)
    rejected_week = await count_status_in_period(ReviewStatus.REJECTED, week_start)
    rejected_month = await count_status_in_period(ReviewStatus.REJECTED, month_start)
    
    return {
        "pending_by_type": pending_by_type,
        "avg_confidence_by_type": avg_confidence_by_type,
        "approved": {
            "today": approved_today,
            "this_week": approved_week,
            "this_month": approved_month
        },
        "corrected": {
            "today": corrected_today,
            "this_week": corrected_week,
            "this_month": corrected_month
        },
        "rejected": {
            "today": rejected_today,
            "this_week": rejected_week,
            "this_month": rejected_month
        }
    }


@router.get("/pending")
async def get_pending_other_vouchers(
    client_id: str,
    type: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending review queue items for OTHER voucher types (not supplier_invoice)
    
    Query params:
    - client_id: Client UUID (required)
    - type: Filter by specific voucher type (employee_expense, inventory_adjustment, etc.)
    - priority: Filter by priority (low/medium/high/urgent)
    - page: Page number (default 1)
    - page_size: Items per page (default 50)
    
    Returns items WHERE type != 'supplier_invoice' AND status = 'pending'
    """
    # Validate client_id
    try:
        client_uuid = UUID(client_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid client_id format: {client_id}. Must be a valid UUID."
        )
    
    # Build query - exclude supplier invoices
    from sqlalchemy import cast, String
    query = select(ReviewQueue).where(
        and_(
            ReviewQueue.client_id == client_uuid,
            cast(ReviewQueue.status, String) == 'PENDING',
            cast(ReviewQueue.type, String) != 'SUPPLIER_INVOICE'
        )
    )
    
    # Apply type filter if specified
    if type:
        type_upper = type.upper()
        valid_types = ['EMPLOYEE_EXPENSE', 'INVENTORY_ADJUSTMENT', 'MANUAL_CORRECTION', 'OTHER']
        if type_upper not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid type: {type}. Must be one of: {', '.join(valid_types)}"
            )
        # Convert string to enum
        voucher_type = VoucherType[type_upper]
        query = query.where(ReviewQueue.type == voucher_type)
    
    # Apply priority filter if specified
    if priority:
        from sqlalchemy import cast, String
        priority_upper = priority.upper()
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
        if priority_upper not in valid_priorities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority: {priority}"
            )
        query = query.where(cast(ReviewQueue.priority, String) == priority_upper)
    
    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Order by priority and created_at
    query = query.order_by(
        ReviewQueue.priority.desc(),
        ReviewQueue.created_at.desc()
    )
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Format response
    formatted_items = []
    for item in items:
        # Extract AI confidence and reasoning
        ai_confidence = item.ai_confidence if item.ai_confidence is not None else 0
        ai_reasoning = item.ai_reasoning or "No reasoning provided"
        
        formatted_items.append({
            "id": str(item.id),
            "type": item.type.value.lower(),
            "client_id": str(item.client_id),
            "source_type": item.source_type,
            "source_id": str(item.source_id),
            "title": f"{item.type.value.replace('_', ' ').title()} - {item.issue_category.value.replace('_', ' ')}",
            "description": item.issue_description,
            "priority": item.priority.value.lower(),
            "status": item.status.value.lower(),
            "issue_category": item.issue_category.value.lower(),
            "ai_confidence": float(ai_confidence) / 100.0,  # Convert to 0-1 scale
            "ai_reasoning": ai_reasoning,
            "ai_suggestion": item.ai_suggestion,
            "created_at": item.created_at.isoformat(),
            "assigned_to_user_id": str(item.assigned_to_user_id) if item.assigned_to_user_id else None,
        })
    
    return {
        "items": formatted_items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{voucher_id}")
async def get_other_voucher(
    voucher_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single other voucher review queue item by ID
    
    Returns full details including AI suggestion, confidence, reasoning, etc.
    """
    # Fetch review item
    query = select(ReviewQueue).where(ReviewQueue.id == voucher_id)
    result = await db.execute(query)
    review_item = result.scalar_one_or_none()
    
    if not review_item:
        raise HTTPException(
            status_code=404,
            detail=f"Review item with ID {voucher_id} not found"
        )
    
    # Validate it's not a supplier invoice
    if review_item.type == VoucherType.SUPPLIER_INVOICE:
        raise HTTPException(
            status_code=400,
            detail="Use /api/review-queue/{id} for supplier invoices"
        )
    
    # Format AI confidence
    ai_confidence = review_item.ai_confidence if review_item.ai_confidence is not None else 0
    
    return {
        "id": str(review_item.id),
        "type": review_item.type.value.lower(),
        "client_id": str(review_item.client_id),
        "source_type": review_item.source_type,
        "source_id": str(review_item.source_id),
        "title": f"{review_item.type.value.replace('_', ' ').title()} - {review_item.issue_category.value.replace('_', ' ')}",
        "description": review_item.issue_description,
        "priority": review_item.priority.value.lower(),
        "status": review_item.status.value.lower(),
        "issue_category": review_item.issue_category.value.lower(),
        "ai_confidence": float(ai_confidence) / 100.0,
        "ai_reasoning": review_item.ai_reasoning or "No reasoning provided",
        "ai_suggestion": review_item.ai_suggestion,
        "assigned_to_user_id": str(review_item.assigned_to_user_id) if review_item.assigned_to_user_id else None,
        "assigned_at": review_item.assigned_at.isoformat() if review_item.assigned_at else None,
        "resolved_by_user_id": str(review_item.resolved_by_user_id) if review_item.resolved_by_user_id else None,
        "resolved_at": review_item.resolved_at.isoformat() if review_item.resolved_at else None,
        "resolution_notes": review_item.resolution_notes,
        "created_at": review_item.created_at.isoformat(),
        "updated_at": review_item.updated_at.isoformat(),
    }


@router.post("/{id}/approve")
async def approve_other_voucher(
    id: str,
    request: ApproveRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve an other voucher review queue item
    
    This endpoint:
    1. Validates that the item is pending
    2. Validates that it's NOT a supplier invoice
    3. Records feedback for AI learning
    4. Marks item as approved
    5. (Future: Book to general ledger based on voucher type)
    """
    # Validate UUID format
    try:
        uuid_obj = UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    # Fetch review item
    query = select(ReviewQueue).where(ReviewQueue.id == uuid_obj)
    result = await db.execute(query)
    review_item = result.scalar_one_or_none()
    
    if not review_item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    # Validate it's not a supplier invoice
    if review_item.type == VoucherType.SUPPLIER_INVOICE:
        raise HTTPException(
            status_code=400,
            detail="Use /api/review-queue/{id}/approve for supplier invoices"
        )
    
    # Validate status
    if review_item.status != ReviewStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Item already {review_item.status.value}"
        )
    
    # Record feedback for AI learning
    feedback_recorded = False
    if review_item.ai_suggestion:
        feedback = ReviewQueueFeedback(
            id=uuid4(),
            review_queue_id=review_item.id,
            invoice_id=None,  # NULL for non-invoice vouchers
            reviewed_by=None,  # TODO: Set when auth is implemented
            action="approved",
            ai_suggestion=review_item.ai_suggestion,
            accountant_correction=None,  # No correction - AI was correct
            account_correct=True,
            vat_correct=True,
            fully_correct=True,
            invoice_metadata={
                "voucher_type": review_item.type.value,
                "source_type": review_item.source_type,
                "issue_category": review_item.issue_category.value,
            }
        )
        db.add(feedback)
        feedback_recorded = True
    
    # Update status
    review_item.status = ReviewStatus.APPROVED
    review_item.resolved_at = datetime.utcnow()
    review_item.resolution_notes = request.notes
    # TODO: Set resolved_by_user_id when auth is implemented
    
    await db.commit()
    await db.refresh(review_item)
    
    # Log audit event
    await log_audit_event(
        db=db,
        voucher_id=review_item.source_id,
        voucher_type="other_voucher",
        action="approved",
        performed_by="accountant",
        user_id=None,  # TODO: Set when auth is implemented
        ai_confidence=review_item.ai_confidence / 100.0 if review_item.ai_confidence else None,
        details={
            "review_queue_id": str(review_item.id),
            "voucher_type": review_item.type.value,
            "notes": request.notes
        }
    )
    
    return {
        "id": str(review_item.id),
        "type": review_item.type.value.lower(),
        "status": review_item.status.value.lower(),
        "updated_at": review_item.resolved_at.isoformat(),
        "message": f"{review_item.type.value.replace('_', ' ').title()} approved successfully",
        "feedback_recorded": feedback_recorded
    }


@router.post("/{id}/reject")
async def reject_other_voucher(
    id: str,
    request: CorrectRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reject and correct an other voucher review queue item
    
    This endpoint:
    1. Validates that the item is pending
    2. Validates that it's NOT a supplier invoice
    3. Records the accountant's correction
    4. Records feedback for AI learning (what AI got wrong)
    5. Marks item as corrected
    """
    # Validate UUID format
    try:
        uuid_obj = UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    # Fetch review item
    query = select(ReviewQueue).where(ReviewQueue.id == uuid_obj)
    result = await db.execute(query)
    review_item = result.scalar_one_or_none()
    
    if not review_item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    # Validate it's not a supplier invoice
    if review_item.type == VoucherType.SUPPLIER_INVOICE:
        raise HTTPException(
            status_code=400,
            detail="Use /api/review-queue/{id}/correct for supplier invoices"
        )
    
    # Validate status
    if review_item.status != ReviewStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Item already {review_item.status.value}"
        )
    
    # Validate corrected booking
    if not request.bookingEntries:
        raise HTTPException(
            status_code=400,
            detail="Corrected booking entries required"
        )
    
    # Convert to expected format
    corrected_booking = {
        'lines': request.bookingEntries
    }
    
    # Extract corrected values from booking entries
    ai_suggestion = review_item.ai_suggestion or {}
    corrected_account = None
    corrected_vat = None
    
    if request.bookingEntries:
        first_entry = request.bookingEntries[0]
        corrected_account = first_entry.get('account_number')
        corrected_vat = first_entry.get('vat_code')
    
    # Compare AI suggestion vs correction
    account_correct = (
        ai_suggestion.get('account_number') == corrected_account
        if corrected_account else None
    )
    vat_correct = (
        ai_suggestion.get('vat_code') == corrected_vat
        if corrected_vat else None
    )
    fully_correct = (
        account_correct and vat_correct
        if (account_correct is not None and vat_correct is not None)
        else False
    )
    
    # Record feedback
    feedback = ReviewQueueFeedback(
        id=uuid4(),
        review_queue_id=review_item.id,
        invoice_id=None,  # NULL for non-invoice vouchers
        reviewed_by=None,  # TODO: Set when auth is implemented
        action="corrected",
        ai_suggestion=ai_suggestion,
        accountant_correction={
            "account_number": corrected_account,
            "vat_code": corrected_vat,
            "booking_entries": request.bookingEntries,
            "reason": request.notes
        },
        account_correct=account_correct,
        vat_correct=vat_correct,
        fully_correct=fully_correct,
        invoice_metadata={
            "voucher_type": review_item.type.value,
            "source_type": review_item.source_type,
            "issue_category": review_item.issue_category.value,
        }
    )
    db.add(feedback)
    feedback_recorded = True
    
    # Update review item status
    review_item.status = ReviewStatus.CORRECTED
    review_item.resolved_at = datetime.utcnow()
    review_item.resolution_notes = request.notes
    
    await db.commit()
    await db.refresh(review_item)
    
    return {
        "id": str(review_item.id),
        "type": review_item.type.value.lower(),
        "status": "corrected",
        "updated_at": review_item.resolved_at.isoformat(),
        "message": f"{review_item.type.value.replace('_', ' ').title()} corrected successfully",
        "feedback_recorded": feedback_recorded,
        "correction": {
            "account_number": corrected_account,
            "vat_code": corrected_vat,
            "notes": request.notes
        },
        "accuracy": {
            "account_correct": account_correct,
            "vat_correct": vat_correct,
            "fully_correct": fully_correct
        }
    }
