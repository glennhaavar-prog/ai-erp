"""
Auto-Booking API Routes
Endpoints for triggering and monitoring auto-booking agent
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import Optional, List
from datetime import datetime, timedelta, date
from uuid import UUID

from app.database import get_db
from app.services.auto_booking_agent import (
    run_auto_booking_batch,
    process_single_invoice_auto_booking,
    AutoBookingAgent
)
from app.models.auto_booking_stats import AutoBookingStats
from app.models.vendor_invoice import VendorInvoice
from pydantic import BaseModel

router = APIRouter(prefix="/api/auto-booking", tags=["Auto-Booking"])


# === REQUEST/RESPONSE MODELS ===

class ProcessBatchRequest(BaseModel):
    """Request to process batch of invoices"""
    client_id: Optional[str] = None
    limit: int = 50


class ProcessBatchResponse(BaseModel):
    """Response from batch processing"""
    success: bool
    processed_count: int
    auto_booked_count: int
    review_queue_count: int
    failed_count: int
    results: List[dict]


class ProcessSingleRequest(BaseModel):
    """Request to process single invoice"""
    invoice_id: str


class StatsResponse(BaseModel):
    """Auto-booking statistics response"""
    success: bool
    stats: dict
    skattefunn_compliant: bool  # True if success_rate >= 95%
    message: Optional[str] = None


# === ENDPOINTS ===

@router.post("/process", response_model=ProcessBatchResponse)
async def process_batch(
    request: ProcessBatchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger auto-booking batch processing
    
    Processes new unbooked invoices:
    - Calculate confidence scores
    - Auto-book if confidence > 85%
    - Send to review queue if confidence < 85%
    
    **SKATTEFUNN AP1+AP2**: Critical for achieving 95%+ accuracy target
    """
    try:
        client_id = UUID(request.client_id) if request.client_id else None
        
        result = await run_auto_booking_batch(
            db=db,
            client_id=client_id,
            limit=request.limit
        )
        
        return ProcessBatchResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-single", response_model=dict)
async def process_single_invoice(
    request: ProcessSingleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Process a single invoice through auto-booking pipeline
    
    Useful for testing or manual triggering of specific invoices.
    """
    try:
        invoice_id = UUID(request.invoice_id)
        
        result = await process_single_invoice_auto_booking(
            db=db,
            invoice_id=invoice_id
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_auto_booking_stats(
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    days: int = Query(30, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get auto-booking statistics
    
    Returns:
    - Success rate (auto-booked / total processed)
    - False positive rate
    - Escalation rate (sent to review queue)
    - Avg confidence scores
    - Skattefunn compliance status (>= 95% success required)
    
    **SKATTEFUNN REPORTING**: Use this endpoint to track 95%+ accuracy requirement
    """
    try:
        client_uuid = UUID(client_id) if client_id else None
        cutoff_date = date.today() - timedelta(days=days)
        
        # Query stats from database
        query = select(AutoBookingStats).where(
            AutoBookingStats.period_date >= cutoff_date
        )
        
        if client_uuid:
            query = query.where(AutoBookingStats.client_id == client_uuid)
        
        query = query.order_by(desc(AutoBookingStats.period_date))
        
        result = await db.execute(query)
        stats_records = result.scalars().all()
        
        if not stats_records:
            # No stats yet, calculate from actual invoices
            stats = await _calculate_stats_from_invoices(db, client_uuid, cutoff_date)
        else:
            # Aggregate stats from records
            stats = _aggregate_stats(stats_records)
        
        # Check Skattefunn compliance (95%+ success rate required)
        skattefunn_compliant = stats['success_rate'] >= 95.0
        
        message = None
        if not skattefunn_compliant:
            message = (
                f"⚠️ Success rate {stats['success_rate']:.1f}% is below 95% Skattefunn requirement. "
                f"Need {95.0 - stats['success_rate']:.1f}% improvement."
            )
        else:
            message = f"✅ Skattefunn compliant! Success rate: {stats['success_rate']:.1f}%"
        
        return StatsResponse(
            success=True,
            stats=stats,
            skattefunn_compliant=skattefunn_compliant,
            message=message
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_processing_status(
    client_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current processing status
    
    Returns count of:
    - Pending invoices (not yet processed)
    - Auto-booked invoices
    - In review queue
    - Failed
    """
    try:
        client_uuid = UUID(client_id) if client_id else None
        
        # Count pending invoices
        pending_query = select(func.count(VendorInvoice.id)).where(
            and_(
                VendorInvoice.general_ledger_id.is_(None),
                VendorInvoice.review_status.in_(['pending', None])
            )
        )
        if client_uuid:
            pending_query = pending_query.where(VendorInvoice.client_id == client_uuid)
        
        pending_result = await db.execute(pending_query)
        pending_count = pending_result.scalar() or 0
        
        # Count auto-booked today
        today = datetime.utcnow().date()
        auto_booked_query = select(func.count(VendorInvoice.id)).where(
            and_(
                VendorInvoice.review_status == 'auto_approved',
                func.date(VendorInvoice.booked_at) == today
            )
        )
        if client_uuid:
            auto_booked_query = auto_booked_query.where(VendorInvoice.client_id == client_uuid)
        
        auto_booked_result = await db.execute(auto_booked_query)
        auto_booked_today = auto_booked_result.scalar() or 0
        
        # Count in review queue
        review_query = select(func.count(VendorInvoice.id)).where(
            VendorInvoice.review_status == 'needs_review'
        )
        if client_uuid:
            review_query = review_query.where(VendorInvoice.client_id == client_uuid)
        
        review_result = await db.execute(review_query)
        in_review = review_result.scalar() or 0
        
        return {
            'success': True,
            'status': {
                'pending_invoices': pending_count,
                'auto_booked_today': auto_booked_today,
                'in_review_queue': in_review,
                'processing_available': pending_count > 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        'success': True,
        'service': 'auto-booking-agent',
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat()
    }


# === HELPER FUNCTIONS ===

async def _calculate_stats_from_invoices(
    db: AsyncSession,
    client_id: Optional[UUID],
    since_date: date
) -> dict:
    """
    Calculate statistics directly from vendor_invoices table
    """
    # Query all invoices since cutoff date
    query = select(VendorInvoice).where(
        VendorInvoice.invoice_date >= since_date
    )
    
    if client_id:
        query = query.where(VendorInvoice.client_id == client_id)
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    if not invoices:
        return {
            'processed_count': 0,
            'auto_booked_count': 0,
            'review_queue_count': 0,
            'success_rate': 0.0,
            'escalation_rate': 0.0,
            'avg_confidence_auto_booked': None,
            'avg_confidence_escalated': None,
            'false_positives': 0,
            'false_positive_rate': 0.0,
            'period_start': since_date.isoformat(),
            'period_end': date.today().isoformat()
        }
    
    # Count by status
    auto_booked = [inv for inv in invoices if inv.review_status == 'auto_approved']
    in_review = [inv for inv in invoices if inv.review_status == 'needs_review']
    corrected = [inv for inv in invoices if inv.review_status == 'corrected']
    
    processed = len([inv for inv in invoices if inv.review_status is not None])
    
    # Calculate rates
    success_rate = (len(auto_booked) / processed * 100) if processed > 0 else 0
    escalation_rate = (len(in_review) / processed * 100) if processed > 0 else 0
    
    # False positives = invoices that were auto-booked but later corrected
    false_positives = len(corrected)
    false_positive_rate = (false_positives / len(auto_booked) * 100) if len(auto_booked) > 0 else 0
    
    # Average confidence
    auto_booked_with_confidence = [inv for inv in auto_booked if inv.ai_confidence_score]
    avg_confidence_auto = (
        sum(inv.ai_confidence_score for inv in auto_booked_with_confidence) / len(auto_booked_with_confidence)
        if auto_booked_with_confidence else None
    )
    
    in_review_with_confidence = [inv for inv in in_review if inv.ai_confidence_score]
    avg_confidence_escalated = (
        sum(inv.ai_confidence_score for inv in in_review_with_confidence) / len(in_review_with_confidence)
        if in_review_with_confidence else None
    )
    
    return {
        'processed_count': processed,
        'auto_booked_count': len(auto_booked),
        'review_queue_count': len(in_review),
        'success_rate': round(success_rate, 2),
        'escalation_rate': round(escalation_rate, 2),
        'avg_confidence_auto_booked': round(avg_confidence_auto, 2) if avg_confidence_auto else None,
        'avg_confidence_escalated': round(avg_confidence_escalated, 2) if avg_confidence_escalated else None,
        'false_positives': false_positives,
        'false_positive_rate': round(false_positive_rate, 2),
        'period_start': since_date.isoformat(),
        'period_end': date.today().isoformat()
    }


def _aggregate_stats(stats_records: List[AutoBookingStats]) -> dict:
    """
    Aggregate stats from multiple records
    """
    total_processed = sum(s.invoices_processed for s in stats_records)
    total_auto_booked = sum(s.invoices_auto_booked for s in stats_records)
    total_review = sum(s.invoices_to_review for s in stats_records)
    total_false_positives = sum(s.false_positives for s in stats_records)
    
    success_rate = (total_auto_booked / total_processed * 100) if total_processed > 0 else 0
    escalation_rate = (total_review / total_processed * 100) if total_processed > 0 else 0
    false_positive_rate = (total_false_positives / total_auto_booked * 100) if total_auto_booked > 0 else 0
    
    # Average confidence (weighted by count)
    auto_booked_confidences = [
        s.avg_confidence_auto_booked for s in stats_records 
        if s.avg_confidence_auto_booked is not None
    ]
    avg_confidence_auto = (
        sum(auto_booked_confidences) / len(auto_booked_confidences)
        if auto_booked_confidences else None
    )
    
    escalated_confidences = [
        s.avg_confidence_escalated for s in stats_records 
        if s.avg_confidence_escalated is not None
    ]
    avg_confidence_escalated = (
        sum(escalated_confidences) / len(escalated_confidences)
        if escalated_confidences else None
    )
    
    return {
        'processed_count': total_processed,
        'auto_booked_count': total_auto_booked,
        'review_queue_count': total_review,
        'success_rate': round(success_rate, 2),
        'escalation_rate': round(escalation_rate, 2),
        'avg_confidence_auto_booked': round(float(avg_confidence_auto), 2) if avg_confidence_auto else None,
        'avg_confidence_escalated': round(float(avg_confidence_escalated), 2) if avg_confidence_escalated else None,
        'false_positives': total_false_positives,
        'false_positive_rate': round(false_positive_rate, 2),
        'period_start': min(s.period_date for s in stats_records).isoformat(),
        'period_end': max(s.period_date for s in stats_records).isoformat()
    }
