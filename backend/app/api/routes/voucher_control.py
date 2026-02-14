"""
Voucher Control API - Overview and Audit Trail
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, List
from datetime import date, datetime
import uuid

from app.database import get_db
from app.models.voucher_audit_log import VoucherAuditLog, AuditVoucherType, AuditAction, PerformedBy
from app.models.review_queue import ReviewQueue, ReviewStatus
from app.models.vendor_invoice import VendorInvoice
from app.models.reconciliation import Reconciliation
from app.models.bank_reconciliation import BankReconciliation

router = APIRouter()


@router.get("/overview")
async def get_voucher_control_overview(
    client_id: uuid.UUID = Query(..., description="Client ID"),
    filter: Optional[str] = Query(None, description="Filter: auto_approved, pending, corrected, rule_based, all"),
    voucher_type: Optional[str] = Query(None, description="Filter by voucher type: supplier_invoice, other_voucher, bank_recon, balance_recon"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get voucher control overview with filtering.
    
    Aggregates data from all modules (supplier invoices, other vouchers, bank recon, balance recon)
    and provides filtering based on status and audit trail.
    
    **Filters:**
    - auto_approved: Vouchers automatically approved by AI
    - pending: Vouchers pending review
    - corrected: Vouchers that were corrected after AI suggestion
    - rule_based: Vouchers processed by learned rules
    - all: All vouchers (default)
    
    **Returns:**
    List of vouchers with:
    - Basic voucher info (id, type, amount, date)
    - Audit summary (who handled it, when, confidence)
    - Current status
    """
    
    # Base query for audit logs
    audit_query = select(VoucherAuditLog).where(True)
    
    # Apply voucher type filter
    if voucher_type:
        try:
            voucher_type_enum = AuditVoucherType(voucher_type)
            audit_query = audit_query.where(VoucherAuditLog.voucher_type == voucher_type_enum)
        except ValueError:
            pass
    
    # Apply date range filter
    if start_date:
        audit_query = audit_query.where(VoucherAuditLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        audit_query = audit_query.where(VoucherAuditLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
    
    # Apply status-based filters
    if filter == "auto_approved":
        audit_query = audit_query.where(
            and_(
                VoucherAuditLog.action == AuditAction.APPROVED,
                VoucherAuditLog.performed_by == PerformedBy.AI
            )
        )
    elif filter == "pending":
        # Get vouchers that are in review queue
        pending_query = select(ReviewQueue.source_id).where(
            and_(
                ReviewQueue.client_id == client_id,
                ReviewQueue.status == ReviewStatus.PENDING
            )
        )
        pending_result = await db.execute(pending_query)
        pending_voucher_ids = [row[0] for row in pending_result.fetchall()]
        
        if pending_voucher_ids:
            audit_query = audit_query.where(VoucherAuditLog.voucher_id.in_(pending_voucher_ids))
        else:
            # No pending items
            return {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
    elif filter == "corrected":
        audit_query = audit_query.where(VoucherAuditLog.action == AuditAction.CORRECTED)
    elif filter == "rule_based":
        audit_query = audit_query.where(VoucherAuditLog.action == AuditAction.RULE_APPLIED)
    
    # Order by timestamp DESC
    audit_query = audit_query.order_by(VoucherAuditLog.timestamp.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(audit_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    audit_query = audit_query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(audit_query)
    audit_logs = list(result.scalars().all())
    
    # Group by voucher_id and get latest action for each
    voucher_map = {}
    for log in audit_logs:
        if log.voucher_id not in voucher_map:
            voucher_map[log.voucher_id] = {
                "voucher_id": str(log.voucher_id),
                "voucher_type": log.voucher_type.value,
                "latest_action": log.action.value,
                "performed_by": log.performed_by.value,
                "ai_confidence": log.ai_confidence,
                "timestamp": log.timestamp.isoformat(),
                "details": log.details,
                "user_id": str(log.user_id) if log.user_id else None
            }
    
    return {
        "items": list(voucher_map.values()),
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {
            "filter": filter,
            "voucher_type": voucher_type,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    }


@router.get("/{voucher_id}/audit-trail")
async def get_voucher_audit_trail(
    voucher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete audit trail for a specific voucher.
    
    Returns chronological timeline of all actions performed on the voucher:
    - AI suggestions
    - Approvals/rejections
    - Corrections
    - Rule applications
    
    **Returns:**
    - List of audit events ordered by timestamp (oldest first for timeline view)
    - Includes who performed each action, when, and details
    """
    
    query = (
        select(VoucherAuditLog)
        .where(VoucherAuditLog.voucher_id == voucher_id)
        .order_by(VoucherAuditLog.timestamp.asc())  # Chronological order
    )
    
    result = await db.execute(query)
    audit_logs = list(result.scalars().all())
    
    if not audit_logs:
        return {
            "voucher_id": str(voucher_id),
            "audit_trail": [],
            "total_events": 0
        }
    
    # Format audit trail
    trail = []
    for log in audit_logs:
        trail.append({
            "id": str(log.id),
            "action": log.action.value,
            "performed_by": log.performed_by.value,
            "user_id": str(log.user_id) if log.user_id else None,
            "ai_confidence": log.ai_confidence,
            "timestamp": log.timestamp.isoformat(),
            "details": log.details
        })
    
    return {
        "voucher_id": str(voucher_id),
        "voucher_type": audit_logs[0].voucher_type.value,
        "audit_trail": trail,
        "total_events": len(trail),
        "created_at": audit_logs[0].timestamp.isoformat() if audit_logs else None,
        "last_updated": audit_logs[-1].timestamp.isoformat() if audit_logs else None
    }


@router.get("/stats")
async def get_voucher_control_stats(
    client_id: uuid.UUID = Query(..., description="Client ID"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get voucher control statistics.
    
    Returns aggregated statistics about voucher processing:
    - Total vouchers by type
    - Auto-approval rate
    - Correction rate
    - AI confidence distribution
    """
    
    # Base query
    query = select(VoucherAuditLog)
    
    # Apply date filters
    if start_date:
        query = query.where(VoucherAuditLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(VoucherAuditLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
    
    result = await db.execute(query)
    logs = list(result.scalars().all())
    
    # Calculate statistics
    total_vouchers = len(set(log.voucher_id for log in logs))
    auto_approved = len([log for log in logs if log.action == AuditAction.APPROVED and log.performed_by == PerformedBy.AI])
    manual_approved = len([log for log in logs if log.action == AuditAction.APPROVED and log.performed_by != PerformedBy.AI])
    corrected = len([log for log in logs if log.action == AuditAction.CORRECTED])
    rule_based = len([log for log in logs if log.action == AuditAction.RULE_APPLIED])
    
    # By voucher type
    by_type = {}
    for log in logs:
        vtype = log.voucher_type.value
        if vtype not in by_type:
            by_type[vtype] = 0
        by_type[vtype] += 1
    
    # AI confidence distribution
    ai_confidences = [log.ai_confidence for log in logs if log.ai_confidence is not None]
    avg_confidence = sum(ai_confidences) / len(ai_confidences) if ai_confidences else None
    
    return {
        "total_vouchers": total_vouchers,
        "auto_approved": auto_approved,
        "manual_approved": manual_approved,
        "corrected": corrected,
        "rule_based": rule_based,
        "auto_approval_rate": (auto_approved / total_vouchers * 100) if total_vouchers > 0 else 0,
        "correction_rate": (corrected / total_vouchers * 100) if total_vouchers > 0 else 0,
        "by_voucher_type": by_type,
        "avg_ai_confidence": round(avg_confidence, 2) if avg_confidence else None,
        "date_range": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        }
    }
