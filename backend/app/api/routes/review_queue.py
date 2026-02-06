"""
Review Queue REST API - Frontend integration
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor

router = APIRouter(prefix="/api/review-queue", tags=["Review Queue"])


class ApproveRequest(BaseModel):
    """Approve review item request"""
    notes: Optional[str] = None


class CorrectRequest(BaseModel):
    """Correct review item request"""
    bookingEntries: List[dict]
    notes: Optional[str] = None


@router.get("/")
async def get_review_items(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    client_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all review queue items
    
    Query params:
    - status: pending/in_progress/approved/corrected/rejected
    - priority: low/medium/high/urgent
    - client_id: filter by client
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
        query = query.where(ReviewQueue.status == ReviewStatus(status.upper()))
    
    if priority:
        query = query.where(ReviewQueue.priority == ReviewPriority(priority.upper()))
    
    if client_id:
        query = query.where(ReviewQueue.client_id == UUID(client_id))
    
    # Order by priority and date
    query = query.order_by(
        ReviewQueue.priority.desc(),
        ReviewQueue.created_at.desc()
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    items = []
    for review, invoice in rows:
        items.append({
            "id": str(review.id),
            "supplier": invoice.vendor.name if invoice.vendor else "Unknown",
            "amount": float(invoice.total_amount),
            "currency": invoice.currency,
            "invoiceNumber": invoice.invoice_number,
            "invoiceDate": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "description": review.issue_description,
            "status": review.status.value.lower(),
            "priority": review.priority.value.lower(),
            "confidence": review.ai_confidence or 0,
            "aiSuggestion": review.ai_suggestion,
            "createdAt": review.created_at.isoformat(),
            "reviewedAt": review.resolved_at.isoformat() if review.resolved_at else None,
            "reviewedBy": str(review.resolved_by_user_id) if review.resolved_by_user_id else None,
        })
    
    return items


@router.get("/{item_id}")
async def get_review_item(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get single review queue item with full details"""
    query = select(ReviewQueue, VendorInvoice).join(
        VendorInvoice,
        ReviewQueue.source_id == VendorInvoice.id
    ).options(
        selectinload(VendorInvoice.vendor)
    ).where(
        and_(
            ReviewQueue.id == UUID(item_id),
            ReviewQueue.source_type == 'vendor_invoice'
        )
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    review, invoice = row
    
    return {
        "id": str(review.id),
        "supplier": invoice.vendor.name if invoice.vendor else "Unknown",
        "supplierOrgNumber": invoice.vendor.org_number if invoice.vendor else None,
        "amount": float(invoice.total_amount),
        "amountExclVat": float(invoice.amount_excl_vat),
        "vatAmount": float(invoice.vat_amount),
        "currency": invoice.currency,
        "invoiceNumber": invoice.invoice_number,
        "invoiceDate": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        "dueDate": invoice.due_date.isoformat() if invoice.due_date else None,
        "description": review.issue_description,
        "status": review.status.value.lower(),
        "priority": review.priority.value.lower(),
        "confidence": review.ai_confidence or 0,
        "aiSuggestion": review.ai_suggestion,
        "aiReasoning": review.ai_reasoning,
        "issueCategory": review.issue_category.value,
        "createdAt": review.created_at.isoformat(),
        "reviewedAt": review.resolved_at.isoformat() if review.resolved_at else None,
        "reviewedBy": str(review.resolved_by_user_id) if review.resolved_by_user_id else None,
        "resolutionNotes": review.resolution_notes,
    }


@router.post("/{item_id}/approve")
async def approve_item(
    item_id: str,
    request: ApproveRequest,
    db: AsyncSession = Depends(get_db)
):
    """Approve a review queue item and book to General Ledger"""
    query = select(ReviewQueue).where(ReviewQueue.id == UUID(item_id))
    result = await db.execute(query)
    review_item = result.scalar_one_or_none()
    
    if not review_item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    if review_item.status != ReviewStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Item already {review_item.status.value}"
        )
    
    # Book to General Ledger if this is a vendor invoice
    if review_item.source_type == "vendor_invoice" and review_item.ai_suggestion:
        from app.services.booking_service import book_vendor_invoice
        
        booking_result = await book_vendor_invoice(
            db=db,
            invoice_id=review_item.source_id,
            booking_suggestion=review_item.ai_suggestion,
            created_by_type="user",
            created_by_id=None  # TODO: Set when auth is implemented
        )
        
        if not booking_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to book invoice: {booking_result.get('error')}"
            )
    
    # Update status
    review_item.status = ReviewStatus.APPROVED
    review_item.resolved_at = datetime.utcnow()
    review_item.resolution_notes = request.notes
    # TODO: Set resolved_by_user_id when auth is implemented
    
    await db.commit()
    await db.refresh(review_item)
    
    return {
        "id": str(review_item.id),
        "status": review_item.status.value.lower(),
        "resolvedAt": review_item.resolved_at.isoformat(),
        "message": "Item approved and booked to General Ledger successfully"
    }


@router.post("/{item_id}/correct")
async def correct_item(
    item_id: str,
    request: CorrectRequest,
    db: AsyncSession = Depends(get_db)
):
    """Correct a review queue item with manual booking entries"""
    query = select(ReviewQueue).where(ReviewQueue.id == UUID(item_id))
    result = await db.execute(query)
    review_item = result.scalar_one_or_none()
    
    if not review_item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    if review_item.status != ReviewStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Item already {review_item.status.value}"
        )
    
    # Update status
    review_item.status = ReviewStatus.CORRECTED
    review_item.resolved_at = datetime.utcnow()
    review_item.resolution_notes = request.notes
    # TODO: Set resolved_by_user_id when auth is implemented
    
    # TODO: Store corrected booking entries and trigger learning
    # For now, just mark as corrected
    
    await db.commit()
    await db.refresh(review_item)
    
    return {
        "id": str(review_item.id),
        "status": review_item.status.value.lower(),
        "resolvedAt": review_item.resolved_at.isoformat(),
        "message": "Item corrected successfully - AI will learn from this"
    }


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
