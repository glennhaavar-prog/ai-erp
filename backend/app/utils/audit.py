"""
Audit Trail Utilities
"""
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voucher_audit_log import VoucherAuditLog


async def log_audit_event(
    db: AsyncSession,
    voucher_id: uuid.UUID,
    voucher_type: str,
    action: str,
    performed_by: str,
    user_id: Optional[uuid.UUID] = None,
    ai_confidence: Optional[float] = None,
    details: Optional[dict] = None
) -> VoucherAuditLog:
    """
    Log an audit event for a voucher action.
    
    Args:
        db: Database session
        voucher_id: ID of the voucher being audited
        voucher_type: Type of voucher (supplier_invoice, other_voucher, bank_recon, balance_recon)
        action: Action performed (created, ai_suggested, approved, rejected, corrected, rule_applied)
        performed_by: Who performed the action (ai, accountant, supervisor, manager)
        user_id: User ID if performed by a human (optional)
        ai_confidence: AI confidence score 0-1 if performed by AI (optional)
        details: Additional details as JSON (optional)
        
    Returns:
        VoucherAuditLog: The created audit log entry
        
    Example:
        await log_audit_event(
            db=db,
            voucher_id=invoice_id,
            voucher_type="supplier_invoice",
            action="approved",
            performed_by="accountant",
            user_id=user.id,
            details={"notes": "Approved with corrections", "changes": {...}}
        )
    """
    audit = VoucherAuditLog(
        voucher_id=voucher_id,
        voucher_type=voucher_type,
        action=action,
        performed_by=performed_by,
        user_id=user_id,
        ai_confidence=ai_confidence,
        details=details
    )
    db.add(audit)
    await db.flush()  # Flush instead of commit to allow caller to manage transaction
    return audit


async def get_voucher_audit_trail(
    db: AsyncSession,
    voucher_id: uuid.UUID
) -> list[VoucherAuditLog]:
    """
    Retrieve the complete audit trail for a voucher.
    
    Args:
        db: Database session
        voucher_id: ID of the voucher
        
    Returns:
        List of audit log entries ordered by timestamp (newest first)
    """
    from sqlalchemy import select
    
    query = (
        select(VoucherAuditLog)
        .where(VoucherAuditLog.voucher_id == voucher_id)
        .order_by(VoucherAuditLog.timestamp.desc())
    )
    
    result = await db.execute(query)
    return list(result.scalars().all())
