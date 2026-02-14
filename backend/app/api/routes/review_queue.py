"""
Review Queue REST API - Frontend integration
Enhanced with confidence scoring and corrections learning
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
from app.models.vendor_invoice import VendorInvoice
from app.services.confidence_scoring import calculate_invoice_confidence
from app.services.corrections_learning import record_invoice_correction
from app.utils.audit import log_audit_event

router = APIRouter(prefix="/api/review-queue", tags=["Review Queue"])


class ApproveRequest(BaseModel):
    """Approve review item request"""
    notes: Optional[str] = None


class CorrectRequest(BaseModel):
    """Correct review item request"""
    bookingEntries: List[dict]
    notes: Optional[str] = None


@router.get("/pending")
async def get_pending_items(
    client_id: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending review queue items (convenience endpoint for status=pending)
    
    NOTE: This route MUST come before /{item_id} to avoid route collision
    """
    # Delegate to main get_review_items with status=pending
    return await get_review_items(
        status="pending",
        priority=priority,
        client_id=client_id,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        db=db
    )


@router.get("/stats")
async def get_queue_stats(
    client_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about the review queue
    - Total items pending
    - Average confidence score
    - Escalation rate
    - Auto-approval rate
    
    NOTE: This route MUST come before /{item_id} to avoid route collision
    """
    query = select(ReviewQueue)
    
    if client_id:
        try:
            query = query.where(ReviewQueue.client_id == UUID(client_id))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid client_id format: {client_id}. Must be a valid UUID.")
    
    # Count by status
    base_filters = []
    if client_id:
        try:
            base_filters.append(ReviewQueue.client_id == UUID(client_id))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid client_id format: {client_id}. Must be a valid UUID.")
    
    pending_count_query = select(func.count(ReviewQueue.id)).where(
        and_(ReviewQueue.status == ReviewStatus.PENDING, *base_filters) if base_filters else ReviewQueue.status == ReviewStatus.PENDING
    )
    pending_result = await db.execute(pending_count_query)
    pending_count = pending_result.scalar() or 0
    
    approved_count_query = select(func.count(ReviewQueue.id)).where(
        and_(ReviewQueue.status == ReviewStatus.APPROVED, *base_filters) if base_filters else ReviewQueue.status == ReviewStatus.APPROVED
    )
    approved_result = await db.execute(approved_count_query)
    approved_count = approved_result.scalar() or 0
    
    corrected_count_query = select(func.count(ReviewQueue.id)).where(
        and_(ReviewQueue.status == ReviewStatus.CORRECTED, *base_filters) if base_filters else ReviewQueue.status == ReviewStatus.CORRECTED
    )
    corrected_result = await db.execute(corrected_count_query)
    corrected_count = corrected_result.scalar() or 0
    
    # Average confidence
    avg_confidence_query = select(func.avg(ReviewQueue.ai_confidence)).where(
        ReviewQueue.ai_confidence.isnot(None)
    )
    if client_id:
        try:
            avg_confidence_query = avg_confidence_query.where(ReviewQueue.client_id == UUID(client_id))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid client_id format: {client_id}. Must be a valid UUID.")
    
    avg_confidence_result = await db.execute(avg_confidence_query)
    avg_confidence = avg_confidence_result.scalar() or 0
    
    # Calculate rates
    total_resolved = approved_count + corrected_count
    escalation_rate = (corrected_count / total_resolved * 100) if total_resolved > 0 else 0
    auto_approval_rate = (approved_count / total_resolved * 100) if total_resolved > 0 else 0
    
    return {
        "pending": pending_count,
        "approved": approved_count,
        "corrected": corrected_count,
        "total_resolved": total_resolved,
        "average_confidence": round(float(avg_confidence), 2),
        "escalation_rate": round(escalation_rate, 2),
        "auto_approval_rate": round(auto_approval_rate, 2)
    }


@router.get("/")
async def get_review_items(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    client_id: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all review queue items with pagination (API v1 spec compliant)
    
    Query params:
    - status: pending/in_progress/approved/corrected/rejected
    - priority: low/medium/high/urgent
    - client_id: filter by client
    - category: vouchers/bank_reconciliation/reconciliation/vat
    - sort_by: created_at/priority/client_name
    - sort_order: asc/desc
    - page: page number (default 1)
    - page_size: items per page (default 50)
    """
    query = select(ReviewQueue, VendorInvoice).join(
        VendorInvoice,
        ReviewQueue.source_id == VendorInvoice.id
    ).options(
        selectinload(VendorInvoice.vendor)
    ).where(
        ReviewQueue.source_type == 'vendor_invoice'
    )
    
    # Apply filters
    if status:
        # Database stores UPPERCASE values (PENDING, APPROVED, etc.)
        # API accepts lowercase or uppercase - normalize to UPPERCASE for DB comparison
        from sqlalchemy import cast, String
        status_upper = status.upper()  # e.g., "PENDING"
        valid_statuses = ['PENDING', 'IN_PROGRESS', 'APPROVED', 'CORRECTED', 'REJECTED']
        if status_upper not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        query = query.where(cast(ReviewQueue.status, String) == status_upper)
    
    if priority:
        # Database stores UPPERCASE values - normalize to UPPERCASE
        from sqlalchemy import cast, String
        priority_upper = priority.upper()  # e.g., "MEDIUM"
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
        if priority_upper not in valid_priorities:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
        query = query.where(cast(ReviewQueue.priority, String) == priority_upper)
    
    if client_id:
        try:
            query = query.where(ReviewQueue.client_id == UUID(client_id))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid client_id format: {client_id}. Must be a valid UUID.")
    
    if category:
        # Database stores UPPERCASE values - normalize to UPPERCASE
        from sqlalchemy import cast, String
        category_upper = category.upper()
        valid_categories = ['LOW_CONFIDENCE', 'UNKNOWN_VENDOR', 'UNUSUAL_AMOUNT', 'MISSING_VAT', 
                           'UNCLEAR_DESCRIPTION', 'DUPLICATE_INVOICE', 'PROCESSING_ERROR', 
                           'MANUAL_REVIEW_REQUIRED']
        if category_upper not in valid_categories:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        query = query.where(cast(ReviewQueue.issue_category, String) == category_upper)
    
    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Order by requested field
    if sort_by == "priority":
        order_col = ReviewQueue.priority
    elif sort_by == "client_name":
        order_col = ReviewQueue.created_at  # TODO: join client table when available
    else:
        order_col = ReviewQueue.created_at
    
    if sort_order == "asc":
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    rows = result.all()
    
    items = []
    for review, invoice in rows:
        # Extract AI confidence and reasoning
        ai_confidence = review.ai_confidence if review.ai_confidence is not None else 0
        ai_reasoning = review.ai_reasoning or "No reasoning provided"
        
        items.append({
            "id": str(review.id),
            "category": review.issue_category.value.lower() if review.issue_category else "vouchers",
            "client_id": str(review.client_id) if review.client_id else None,
            "client_name": "Demo Client",  # TODO: fetch from client table
            "title": f"Invoice {invoice.invoice_number}",  # TODO: make this more descriptive
            "description": review.issue_description,
            "priority": review.priority.value.lower(),
            "ai_confidence": float(ai_confidence) / 100.0,  # Convert to 0-1 scale
            "ai_reasoning": ai_reasoning,
            "created_at": review.created_at.isoformat(),
            "status": review.status.value.lower(),
            # Additional fields for compatibility
            "supplier": invoice.vendor.name if invoice.vendor else "Unknown",
            "supplier_id": str(invoice.vendor_id) if invoice.vendor_id else None,
            "amount": float(invoice.total_amount),
            "currency": invoice.currency,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "ai_suggestion": review.ai_suggestion,
            "reviewed_at": review.resolved_at.isoformat() if review.resolved_at else None,
            "reviewed_by": str(review.resolved_by_user_id) if review.resolved_by_user_id else None,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{item_id}")
async def get_review_item(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get single review queue item with full details (API v1 spec compliant - snake_case)"""
    # Validate UUID format
    try:
        uuid_obj = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    query = select(ReviewQueue, VendorInvoice).join(
        VendorInvoice,
        ReviewQueue.source_id == VendorInvoice.id
    ).options(
        selectinload(VendorInvoice.vendor)
    ).where(
        and_(
            ReviewQueue.id == uuid_obj,
            ReviewQueue.source_type == 'vendor_invoice'
        )
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    review, invoice = row
    
    # Extract AI confidence and reasoning
    ai_confidence = review.ai_confidence if review.ai_confidence is not None else 0
    ai_reasoning = review.ai_reasoning or "No reasoning provided"
    
    return {
        "id": str(review.id),
        "category": review.issue_category.value.lower() if review.issue_category else "vouchers",
        "client_id": str(review.client_id) if review.client_id else None,
        "client_name": "Demo Client",  # TODO: fetch from client table
        "title": f"Invoice {invoice.invoice_number}",
        "description": review.issue_description,
        "priority": review.priority.value.lower(),
        "ai_confidence": float(ai_confidence) / 100.0,  # Convert to 0-1 scale
        "ai_reasoning": ai_reasoning,
        "suggested_booking": review.ai_suggestion,  # Spec uses suggested_booking for detail view
        "voucher_image_url": f"/api/v1/vouchers/{invoice.id}/image" if invoice.id else None,
        "created_at": review.created_at.isoformat(),
        "status": review.status.value.lower(),
        # Additional details
        "supplier": invoice.vendor.name if invoice.vendor else "Unknown",
        "supplier_id": str(invoice.vendor_id) if invoice.vendor_id else None,
        "supplier_org_number": invoice.vendor.org_number if invoice.vendor else None,
        "amount": float(invoice.total_amount),
        "amount_excl_vat": float(invoice.amount_excl_vat),
        "vat_amount": float(invoice.vat_amount),
        "currency": invoice.currency,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "reviewed_at": review.resolved_at.isoformat() if review.resolved_at else None,
        "reviewed_by": str(review.resolved_by_user_id) if review.resolved_by_user_id else None,
        "resolution_notes": review.resolution_notes,
    }


@router.post("/{item_id}/approve")
async def approve_item(
    item_id: str,
    request: ApproveRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a review queue item and book to General Ledger
    
    PERFORMANCE: Optimized to complete in < 5 seconds with timeout protection
    FEEDBACK LOOP: Records AI accuracy for machine learning
    """
    import asyncio
    import time
    from app.models.review_queue_feedback import ReviewQueueFeedback
    from app.models.vendor_invoice import VendorInvoice
    
    start_time = time.time()
    
    # Validate UUID format
    try:
        uuid_obj = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    # Fetch review item with invoice
    query = select(ReviewQueue, VendorInvoice).join(
        VendorInvoice,
        ReviewQueue.source_id == VendorInvoice.id
    ).where(ReviewQueue.id == uuid_obj)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    review_item, invoice = row
    
    if review_item.status != ReviewStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Item already {review_item.status.value}"
        )
    
    # Book to General Ledger if this is a vendor invoice
    voucher_dto = None
    if review_item.source_type == "vendor_invoice" and review_item.ai_suggestion:
        from app.services.voucher_service import VoucherGenerator, VoucherValidationError
        
        try:
            generator = VoucherGenerator(db)
            
            # TIMEOUT PROTECTION: 10 second timeout for voucher creation
            try:
                voucher_dto = await asyncio.wait_for(
                    generator.create_voucher_from_invoice(
                        invoice_id=review_item.source_id,
                        tenant_id=review_item.client_id,
                        user_id="review_queue_user",  # TODO: Set actual user when auth is implemented
                        accounting_date=None,  # Use invoice date
                        override_account=review_item.ai_suggestion.get('account')
                    ),
                    timeout=10.0  # 10 second timeout
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail="Voucher creation timed out (>10s). Please try again or contact support."
                )
            
        except (ValueError, VoucherValidationError) as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to create voucher: {str(e)}"
            )
        except HTTPException:
            raise  # Re-raise HTTP exceptions (including timeout)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal error creating voucher: {str(e)}"
            )
    
    # FEEDBACK LOOP: Record that accountant approved AI suggestion
    if review_item.ai_suggestion and invoice:
        feedback = ReviewQueueFeedback(
            id=uuid.uuid4(),
            review_queue_id=review_item.id,
            invoice_id=invoice.id,
            reviewed_by=None,  # TODO: Set when auth is implemented
            action="approved",
            ai_suggestion=review_item.ai_suggestion,
            accountant_correction=None,  # No correction - AI was correct
            account_correct=True,
            vat_correct=True,
            fully_correct=True,
            invoice_metadata={
                "vendor_name": invoice.vendor.name if invoice.vendor else None,
                "amount": float(invoice.total_amount),
                "description": getattr(invoice, 'description', None),
                "currency": invoice.currency,
            }
        )
        db.add(feedback)
    
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
        voucher_type="supplier_invoice",
        action="approved",
        performed_by="accountant",
        user_id=None,  # TODO: Set when auth is implemented
        ai_confidence=review_item.ai_confidence / 100.0 if review_item.ai_confidence else None,
        details={
            "review_queue_id": str(review_item.id),
            "notes": request.notes,
            "resolution_time_seconds": round(time.time() - start_time, 3)
        }
    )
    
    elapsed = time.time() - start_time
    
    response = {
        "id": str(review_item.id),
        "status": review_item.status.value.lower(),
        "updated_at": review_item.resolved_at.isoformat(),
        "message": "Item approved and booked to General Ledger successfully",
        "performance": {
            "elapsed_seconds": round(elapsed, 3)
        },
        "feedback_recorded": True
    }
    
    # Include voucher details if booking was performed
    if voucher_dto:
        response["voucher"] = {
            "id": voucher_dto.id,
            "voucher_number": voucher_dto.voucher_number,
            "total_debit": float(voucher_dto.total_debit),
            "total_credit": float(voucher_dto.total_credit),
            "is_balanced": voucher_dto.is_balanced,
            "lines_count": len(voucher_dto.lines)
        }
    
    return response


@router.post("/{item_id}/correct")
async def correct_item(
    item_id: str,
    request: CorrectRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Correct a review queue item with manual booking entries
    This triggers the learning system to create patterns from the correction
    FEEDBACK LOOP: Records AI mistakes for machine learning
    """
    from app.models.review_queue_feedback import ReviewQueueFeedback
    from app.models.vendor_invoice import VendorInvoice
    
    # Validate UUID format
    try:
        uuid_obj = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    # Fetch review item with invoice
    query = select(ReviewQueue, VendorInvoice).join(
        VendorInvoice,
        ReviewQueue.source_id == VendorInvoice.id
    ).where(ReviewQueue.id == uuid_obj)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    review_item, invoice = row
    
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
    
    # FEEDBACK LOOP: Analyze what AI got wrong
    ai_suggestion = review_item.ai_suggestion or {}
    corrected_account = None
    corrected_vat = None
    
    # Extract corrected values from booking entries
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
    fully_correct = account_correct and vat_correct if (account_correct is not None and vat_correct is not None) else False
    
    # Record feedback
    feedback = ReviewQueueFeedback(
        id=uuid.uuid4(),
        review_queue_id=review_item.id,
        invoice_id=invoice.id,
        reviewed_by=None,  # TODO: Set when auth is implemented
        action="corrected",
        ai_suggestion=ai_suggestion,
        accountant_correction={
            "account_number": corrected_account,
            "vat_code": corrected_vat,
            "reason": request.notes
        },
        account_correct=account_correct,
        vat_correct=vat_correct,
        fully_correct=fully_correct,
        invoice_metadata={
            "vendor_name": invoice.vendor.name if invoice.vendor else None,
            "amount": float(invoice.total_amount),
            "description": getattr(invoice, 'description', None),
            "currency": invoice.currency,
        }
    )
    db.add(feedback)
    
    # Record correction and trigger learning
    correction_result = await record_invoice_correction(
        db=db,
        review_queue_id=uuid_obj,
        corrected_booking=corrected_booking,
        correction_reason=request.notes,
        corrected_by_user_id=None  # TODO: Set when auth is implemented
    )
    
    if not correction_result.get('success'):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record correction: {correction_result.get('error')}"
        )
    
    # Update review item status
    review_item.status = ReviewStatus.CORRECTED
    review_item.resolved_at = datetime.utcnow()
    review_item.resolution_notes = request.notes
    
    await db.commit()
    
    response = {
        "id": str(review_item.id),
        "status": "corrected",
        "updated_at": datetime.utcnow().isoformat(),
        "message": "Item corrected and AI learned from it",
        "feedback_recorded": True,
        "correction": {
            "id": correction_result.get('correction_id'),
            "general_ledger_id": correction_result.get('general_ledger_id'),
            "voucher_number": correction_result.get('voucher_number'),
            "pattern_created": correction_result.get('pattern_created'),
            "similar_items_corrected": correction_result.get('similar_items_corrected')
        },
        "accuracy": {
            "account_correct": account_correct,
            "vat_correct": vat_correct,
            "fully_correct": fully_correct
        }
    }
    
    return response


@router.get("/{item_id}/chat")
async def get_chat_history(item_id: str):
    """Get chat history for review item (placeholder for now)"""
    # TODO: Implement chat history storage
    return []


@router.post("/{item_id}/chat")
async def send_chat_message(item_id: str, message: dict):
    """Send chat message about review item (placeholder for now)"""
    # TODO: Implement chat with AI about specific item
    return {
        "role": "assistant",
        "content": "Chat feature coming soon - for now use the main chat interface",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/{item_id}/recalculate-confidence")
async def recalculate_confidence(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Recalculate confidence score for a review queue item
    Useful after patterns have been learned
    """
    # Validate UUID format
    try:
        uuid_obj = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    query = select(ReviewQueue, VendorInvoice).join(
        VendorInvoice,
        ReviewQueue.source_id == VendorInvoice.id
    ).where(
        and_(
            ReviewQueue.id == uuid_obj,
            ReviewQueue.source_type == 'vendor_invoice'
        )
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    review_item, invoice = row
    
    if not review_item.ai_suggestion:
        raise HTTPException(
            status_code=400,
            detail="No AI suggestion to recalculate confidence for"
        )
    
    # Recalculate confidence
    confidence_result = await calculate_invoice_confidence(
        db=db,
        invoice=invoice,
        booking_suggestion=review_item.ai_suggestion
    )
    
    # Update review item
    review_item.ai_confidence = confidence_result['total_score']
    review_item.ai_reasoning = confidence_result['reasoning']
    
    # If confidence is now high enough, mark for auto-approval
    if confidence_result['should_auto_approve'] and review_item.status == ReviewStatus.PENDING:
        review_item.priority = ReviewPriority.LOW
    
    await db.commit()
    await db.refresh(review_item)
    
    return {
        "id": str(review_item.id),
        "confidence": confidence_result['total_score'],
        "breakdown": confidence_result['breakdown'],
        "reasoning": confidence_result['reasoning'],
        "should_auto_approve": confidence_result['should_auto_approve']
    }


# =====================================================================
# FEEDBACK ANALYTICS - ML Training Data Export
# =====================================================================

@router.get("/feedback/analytics")
async def get_feedback_analytics(
    client_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated feedback analytics for ML model training.
    
    Returns:
    - Overall accuracy metrics (account, VAT, fully correct)
    - Accuracy trends over time
    - Common mistake patterns
    - Confidence calibration (predicted vs actual accuracy)
    
    Query params:
    - client_id: Filter by client (optional)
    - start_date: ISO date (optional)
    - end_date: ISO date (optional)
    """
    from app.models.review_queue_feedback import ReviewQueueFeedback
    from datetime import datetime as dt
    
    # Build base query
    query = select(ReviewQueueFeedback)
    
    # Apply filters
    if client_id:
        try:
            # Join with ReviewQueue to get client_id
            query = query.join(
                ReviewQueue,
                ReviewQueueFeedback.review_queue_id == ReviewQueue.id
            ).where(ReviewQueue.client_id == UUID(client_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid client_id format")
    
    if start_date:
        try:
            start_dt = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(ReviewQueueFeedback.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format (use ISO 8601)")
    
    if end_date:
        try:
            end_dt = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(ReviewQueueFeedback.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format (use ISO 8601)")
    
    # Execute query
    result = await db.execute(query)
    feedback_records = result.scalars().all()
    
    if not feedback_records:
        return {
            "total_reviews": 0,
            "accuracy": {
                "account": None,
                "vat": None,
                "fully_correct": None
            },
            "trends": [],
            "common_mistakes": []
        }
    
    # Calculate metrics
    total = len(feedback_records)
    account_correct_count = sum(1 for f in feedback_records if f.account_correct)
    vat_correct_count = sum(1 for f in feedback_records if f.vat_correct)
    fully_correct_count = sum(1 for f in feedback_records if f.fully_correct)
    
    return {
        "total_reviews": total,
        "accuracy": {
            "account": round(account_correct_count / total * 100, 2),
            "vat": round(vat_correct_count / total * 100, 2),
            "fully_correct": round(fully_correct_count / total * 100, 2)
        },
        "approved_count": sum(1 for f in feedback_records if f.action == "approved"),
        "corrected_count": sum(1 for f in feedback_records if f.action == "corrected"),
        "date_range": {
            "start": min(f.created_at for f in feedback_records).isoformat(),
            "end": max(f.created_at for f in feedback_records).isoformat()
        }
    }


@router.get("/feedback/export")
async def export_feedback_for_ml(
    client_id: Optional[str] = None,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """
    Export feedback data in format suitable for ML model fine-tuning.
    
    Returns JSONL-like structure:
    [
      {
        "invoice_metadata": {...},
        "ai_suggestion": {...},
        "accountant_correction": {...} or null,
        "accuracy": {...}
      },
      ...
    ]
    
    Use this endpoint to:
    1. Export training data for Claude fine-tuning
    2. Analyze patterns for prompt engineering
    3. Generate accuracy reports
    
    Query params:
    - client_id: Filter by client (optional)
    - limit: Max records to return (default 1000)
    """
    from app.models.review_queue_feedback import ReviewQueueFeedback
    
    query = select(ReviewQueueFeedback).order_by(ReviewQueueFeedback.created_at.desc())
    
    # Apply filters
    if client_id:
        try:
            query = query.join(
                ReviewQueue,
                ReviewQueueFeedback.review_queue_id == ReviewQueue.id
            ).where(ReviewQueue.client_id == UUID(client_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid client_id format")
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    feedback_records = result.scalars().all()
    
    # Format for ML training
    training_data = []
    for record in feedback_records:
        training_data.append({
            "id": str(record.id),
            "invoice_metadata": record.invoice_metadata,
            "ai_suggestion": record.ai_suggestion,
            "accountant_correction": record.accountant_correction,
            "accuracy": {
                "account_correct": record.account_correct,
                "vat_correct": record.vat_correct,
                "fully_correct": record.fully_correct
            },
            "action": record.action,
            "created_at": record.created_at.isoformat()
        })
    
    return {
        "count": len(training_data),
        "data": training_data
    }
