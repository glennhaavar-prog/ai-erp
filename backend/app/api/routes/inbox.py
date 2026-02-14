"""
Inbox API - Items needing accountant review
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Dict, Any
from uuid import UUID

from app.database import get_db
from app.models.review_queue import ReviewQueue, ReviewStatus
from app.models.vendor_invoice import VendorInvoice

router = APIRouter(prefix="/api/inbox", tags=["Inbox"])


@router.get("/")
async def get_inbox_items(
    client_id: UUID = Query(..., description="Client ID"),
    status: str = Query(None, description="Filter by status (pending/processing/reviewed)"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    offset: int = Query(0, ge=0, description="Starting index"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get inbox items (vendor invoices and other items needing review)
    
    Returns items from review_queue with linked invoice details.
    Replaces mock data in frontend inbox component.
    """
    
    # Build base query
    query = select(ReviewQueue).where(
        ReviewQueue.client_id == client_id
    )
    
    # Filter by status
    if status:
        status_map = {
            "pending": ReviewStatus.PENDING,
            "processing": ReviewStatus.IN_PROGRESS,
            "reviewed": [ReviewStatus.APPROVED, ReviewStatus.CORRECTED],
            "posted": ReviewStatus.APPROVED
        }
        
        if status in status_map:
            mapped_status = status_map[status]
            if isinstance(mapped_status, list):
                query = query.where(ReviewQueue.status.in_(mapped_status))
            else:
                query = query.where(ReviewQueue.status == mapped_status)
    
    # Get total count
    count_query = select(func.count()).select_from(ReviewQueue).where(
        ReviewQueue.client_id == client_id
    )
    if status:
        if isinstance(status_map.get(status), list):
            count_query = count_query.where(ReviewQueue.status.in_(status_map[status]))
        else:
            count_query = count_query.where(ReviewQueue.status == status_map.get(status))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and sorting
    query = query.order_by(
        ReviewQueue.priority.desc(),
        ReviewQueue.created_at.desc()
    ).limit(limit).offset(offset)
    
    result = await db.execute(query)
    review_items = result.scalars().all()
    
    # Enrich with invoice details
    items = []
    for review_item in review_items:
        # Fetch linked invoice if source is vendor_invoice
        invoice_details = None
        if review_item.source_type == "vendor_invoice":
            invoice_query = select(VendorInvoice).where(
                VendorInvoice.id == review_item.source_id
            )
            invoice_result = await db.execute(invoice_query)
            invoice = invoice_result.scalar_one_or_none()
            
            if invoice:
                invoice_details = {
                    "vendor_name": invoice.vendor_name,
                    "amount": float(invoice.total_amount),
                    "invoice_number": invoice.invoice_number,
                    "description": invoice.description
                }
        
        # Build inbox item
        item = {
            "id": str(review_item.id),
            "type": review_item.source_type,
            "filename": f"{review_item.source_type}_{review_item.source_id}",  # Fallback
            "uploaded_at": review_item.created_at.isoformat(),
            "status": review_item.status.value,
            "vendor_name": invoice_details["vendor_name"] if invoice_details else None,
            "amount": invoice_details["amount"] if invoice_details else None,
            "confidence": review_item.ai_confidence,
            "description": invoice_details.get("description") if invoice_details else review_item.issue_description
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "page_number": (offset // limit) + 1 if limit > 0 else 1
    }


@router.get("/summary")
async def get_inbox_summary(
    client_id: UUID = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, int]:
    """
    Get summary counts for inbox dashboard cards
    """
    
    # Pending count
    pending_query = select(func.count()).select_from(ReviewQueue).where(
        ReviewQueue.client_id == client_id,
        ReviewQueue.status == ReviewStatus.PENDING
    )
    pending_result = await db.execute(pending_query)
    pending = pending_result.scalar() or 0
    
    # Processing count
    processing_query = select(func.count()).select_from(ReviewQueue).where(
        ReviewQueue.client_id == client_id,
        ReviewQueue.status == ReviewStatus.IN_PROGRESS
    )
    processing_result = await db.execute(processing_query)
    processing = processing_result.scalar() or 0
    
    # Total today
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_today_query = select(func.count()).select_from(ReviewQueue).where(
        ReviewQueue.client_id == client_id,
        ReviewQueue.created_at >= today_start
    )
    total_today_result = await db.execute(total_today_query)
    total_today = total_today_result.scalar() or 0
    
    return {
        "pending": pending,
        "processing": processing,
        "total_today": total_today
    }
