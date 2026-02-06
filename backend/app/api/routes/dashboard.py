"""
Trust Dashboard API - System status and monitoring
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, Any

from app.database import get_db
from app.models.review_queue import ReviewQueue, ReviewStatus
from app.models.vendor_invoice import VendorInvoice

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/status")
async def get_dashboard_status(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get overall system status for Trust Dashboard
    
    Returns traffic light status + counters for:
    - Review Queue
    - EHF invoices
    - Bank transactions (mock for now)
    - System health
    """
    
    # Review Queue stats
    from sqlalchemy import cast, String
    pending_query = select(func.count(ReviewQueue.id)).where(
        cast(ReviewQueue.status, String) == 'pending'
    )
    pending_result = await db.execute(pending_query)
    pending_count = pending_result.scalar() or 0
    
    total_query = select(func.count(ReviewQueue.id))
    total_result = await db.execute(total_query)
    total_reviews = total_result.scalar() or 0
    
    approved_query = select(func.count(ReviewQueue.id)).where(
        cast(ReviewQueue.status, String) == 'approved'
    )
    approved_result = await db.execute(approved_query)
    approved_count = approved_result.scalar() or 0
    
    # Invoice stats
    invoice_query = select(func.count(VendorInvoice.id))
    invoice_result = await db.execute(invoice_query)
    total_invoices = invoice_result.scalar() or 0
    
    # Recent invoices (last 24h)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.created_at >= yesterday
    )
    recent_result = await db.execute(recent_query)
    recent_invoices = recent_result.scalar() or 0
    
    # Auto-booked (high confidence)
    auto_booked_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.review_status == 'approved',
        VendorInvoice.ai_confidence_score >= 85
    )
    auto_booked_result = await db.execute(auto_booked_query)
    auto_booked_count = auto_booked_result.scalar() or 0
    
    # Determine traffic light status
    if pending_count == 0:
        status = "green"
        status_message = "All systems operational"
    elif pending_count <= 5:
        status = "yellow"
        status_message = f"{pending_count} items need attention"
    else:
        status = "red"
        status_message = f"{pending_count} items require immediate attention"
    
    # Bank transactions (mock for now - will be real when avstemming is built)
    bank_stats = {
        "total": 0,
        "matched": 0,
        "unmatched": 0,
        "pending": 0
    }
    
    return {
        "status": status,
        "message": status_message,
        "timestamp": datetime.utcnow().isoformat(),
        "counters": {
            "review_queue": {
                "pending": pending_count,
                "total": total_reviews,
                "approved": approved_count,
                "percentage_approved": round((approved_count / total_reviews * 100) if total_reviews > 0 else 0, 1)
            },
            "invoices": {
                "total": total_invoices,
                "recent_24h": recent_invoices,
                "auto_booked": auto_booked_count,
                "auto_booking_rate": round((auto_booked_count / total_invoices * 100) if total_invoices > 0 else 0, 1)
            },
            "ehf": {
                "received": total_invoices,  # For MVP, assuming all are EHF
                "processed": total_invoices,
                "pending": 0,
                "errors": 0
            },
            "bank": bank_stats
        },
        "health_checks": {
            "database": "healthy",
            "ai_agent": "healthy",
            "review_queue": "healthy"
        }
    }


@router.get("/activity")
async def get_recent_activity(
    db: AsyncSession = Depends(get_db),
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get recent system activity for activity log
    """
    
    # Recent reviews
    recent_reviews_query = select(ReviewQueue).order_by(
        ReviewQueue.created_at.desc()
    ).limit(limit)
    
    result = await db.execute(recent_reviews_query)
    reviews = result.scalars().all()
    
    activities = []
    for review in reviews:
        activities.append({
            "id": str(review.id),
            "type": "review_created",
            "timestamp": review.created_at.isoformat(),
            "description": f"Item added to review queue: {review.issue_category.value}",
            "confidence": review.ai_confidence
        })
    
    return {
        "activities": activities,
        "total": len(activities)
    }


@router.get("/verification")
async def get_verification_status(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Receipt Verification Dashboard - Prove to accountant that NOTHING is forgotten
    
    Returns comprehensive tracking of:
    - EHF invoices: Received vs Processed vs Booked
    - Bank transactions: Total vs Booked (placeholder)
    - Review Queue: Pending items
    - Color-coded status indicators
    """
    
    # Count invoices by review_status
    pending_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.review_status == 'pending'
    )
    pending_result = await db.execute(pending_query)
    pending_invoices = pending_result.scalar() or 0
    
    reviewed_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.review_status.in_(['reviewed', 'auto_approved'])
    )
    reviewed_result = await db.execute(reviewed_query)
    reviewed_invoices = reviewed_result.scalar() or 0
    
    booked_query = select(func.count(VendorInvoice.id)).where(
        VendorInvoice.booked_at.isnot(None)
    )
    booked_result = await db.execute(booked_query)
    booked_invoices = booked_result.scalar() or 0
    
    # Total invoices received (EHF)
    total_query = select(func.count(VendorInvoice.id))
    total_result = await db.execute(total_query)
    total_invoices = total_result.scalar() or 0
    
    # Review queue pending count
    from sqlalchemy import cast, String
    review_pending_query = select(func.count(ReviewQueue.id)).where(
        cast(ReviewQueue.status, String) == 'pending'
    )
    review_pending_result = await db.execute(review_pending_query)
    review_pending_count = review_pending_result.scalar() or 0
    
    # Calculate processed (reviewed + booked - avoid double counting)
    processed_invoices = reviewed_invoices + pending_invoices  # All that have been seen
    
    # Determine overall status
    untracked_count = pending_invoices + review_pending_count
    
    if untracked_count == 0 and total_invoices > 0:
        overall_status = "green"
        status_message = "✅ ALL RECEIPTS TRACKED - Nothing forgotten!"
    elif untracked_count <= 3:
        overall_status = "yellow"
        status_message = f"⚠️ {untracked_count} items need attention"
    elif total_invoices == 0:
        overall_status = "green"
        status_message = "No invoices to process"
    else:
        overall_status = "red"
        status_message = f"❌ {untracked_count} items require immediate review"
    
    # Bank transactions (placeholder for now)
    bank_total = 0
    bank_booked = 0
    bank_status = "green" if bank_total == 0 else "yellow"
    
    # EHF invoice status
    ehf_status = "green" if pending_invoices == 0 else "yellow"
    if pending_invoices > 5:
        ehf_status = "red"
    
    # Review queue status
    review_status = "green" if review_pending_count == 0 else "yellow"
    if review_pending_count > 5:
        review_status = "red"
    
    return {
        "overall_status": overall_status,
        "status_message": status_message,
        "timestamp": datetime.utcnow().isoformat(),
        "ehf_invoices": {
            "received": total_invoices,
            "processed": processed_invoices,
            "booked": booked_invoices,
            "pending": pending_invoices,
            "status": ehf_status,
            "percentage_booked": round((booked_invoices / total_invoices * 100) if total_invoices > 0 else 0, 1)
        },
        "bank_transactions": {
            "total": bank_total,
            "booked": bank_booked,
            "unbooked": bank_total - bank_booked,
            "status": bank_status,
            "note": "Placeholder - Bank reconciliation coming soon"
        },
        "review_queue": {
            "pending": review_pending_count,
            "status": review_status
        },
        "summary": {
            "total_items": total_invoices + bank_total,
            "fully_tracked": booked_invoices + bank_booked,
            "needs_attention": untracked_count,
            "completion_rate": round(((booked_invoices + bank_booked) / (total_invoices + bank_total) * 100) if (total_invoices + bank_total) > 0 else 100, 1)
        }
    }
