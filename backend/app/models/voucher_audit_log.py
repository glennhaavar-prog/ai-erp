"""
VoucherAuditLog model - Comprehensive audit trail for all voucher actions
"""
from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, JSON,
    Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class AuditVoucherType(str, enum.Enum):
    """Type of voucher being audited"""
    SUPPLIER_INVOICE = "supplier_invoice"
    OTHER_VOUCHER = "other_voucher"
    BANK_RECON = "bank_recon"
    BALANCE_RECON = "balance_recon"


class AuditAction(str, enum.Enum):
    """Type of action performed on voucher"""
    CREATED = "created"
    AI_SUGGESTED = "ai_suggested"
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTED = "corrected"
    RULE_APPLIED = "rule_applied"


class PerformedBy(str, enum.Enum):
    """Who performed the action"""
    AI = "ai"
    ACCOUNTANT = "accountant"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"


class VoucherAuditLog(Base):
    """
    VoucherAuditLog = Comprehensive audit trail for all voucher-related actions
    
    Tracks every action across all modules (supplier invoices, other vouchers,
    bank reconciliations, balance reconciliations) to provide full transparency
    and control overview.
    """
    __tablename__ = "voucher_audit_log"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Voucher Reference
    voucher_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    voucher_type = Column(
        SQLEnum(AuditVoucherType),
        nullable=False,
        index=True
    )
    
    # Action Details
    action = Column(
        SQLEnum(AuditAction),
        nullable=False,
        index=True
    )
    performed_by = Column(
        SQLEnum(PerformedBy),
        nullable=False,
        index=True
    )
    
    # User Reference (null for AI actions)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # AI Confidence (for AI actions)
    ai_confidence = Column(Float, nullable=True)
    
    # Timestamp
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Additional Details (JSON for flexibility)
    details = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_voucher_audit_log_voucher_lookup', 'voucher_id', 'voucher_type'),
        Index('ix_voucher_audit_log_timeline', 'voucher_id', 'timestamp'),
        Index('ix_voucher_audit_log_action_time', 'action', 'timestamp'),
    )
    
    def __repr__(self):
        return (
            f"<VoucherAuditLog(id={self.id}, voucher_id={self.voucher_id}, "
            f"action={self.action.value}, performed_by={self.performed_by.value})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "voucher_id": str(self.voucher_id),
            "voucher_type": self.voucher_type.value,
            "action": self.action.value,
            "performed_by": self.performed_by.value,
            "user_id": str(self.user_id) if self.user_id else None,
            "ai_confidence": self.ai_confidence,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }
