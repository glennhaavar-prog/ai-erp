"""
Bank Reconciliation model - Track matching history between bank transactions and vouchers
"""
from sqlalchemy import (
    Column, String, Numeric, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class MatchType(str, enum.Enum):
    """Type of match"""
    AUTO = "auto"          # Automatic match (AI)
    MANUAL = "manual"      # Manual match by user
    SUGGESTED = "suggested"  # AI suggestion awaiting approval


class MatchStatus(str, enum.Enum):
    """Status of reconciliation match"""
    PENDING = "pending"      # Awaiting approval
    APPROVED = "approved"    # Match approved
    REJECTED = "rejected"    # Match rejected


class BankReconciliation(Base):
    """
    Bank Reconciliation = Track matching between bank transactions and vouchers/invoices
    
    This table maintains the relationship history and confidence scores for
    automated and manual reconciliation.
    """
    __tablename__ = "bank_reconciliations"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Client relationship
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Transaction and Voucher
    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bank_transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Can match to either vendor invoice, customer invoice, or general ledger entry
    vendor_invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vendor_invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    customer_invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    voucher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("general_ledger.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Match Details
    match_type = Column(
        SQLEnum(MatchType),
        nullable=False,
        index=True
    )
    match_status = Column(
        SQLEnum(MatchStatus),
        default=MatchStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Confidence and Reasoning
    confidence_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    match_reason = Column(Text, nullable=True)  # Explanation of why matched
    match_criteria = Column(Text, nullable=True)  # JSON with matching criteria used
    
    # Amount reconciliation
    transaction_amount = Column(Numeric(15, 2), nullable=False)
    voucher_amount = Column(Numeric(15, 2), nullable=False)
    amount_difference = Column(Numeric(15, 2), nullable=True)
    
    # User actions
    matched_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    matched_at = Column(DateTime, nullable=True)
    
    approved_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at = Column(DateTime, nullable=True)
    
    rejected_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client")
    transaction = relationship("BankTransaction", backref="reconciliations")
    vendor_invoice = relationship("VendorInvoice")
    customer_invoice = relationship("CustomerInvoice")
    voucher = relationship("GeneralLedger")
    matched_by_user = relationship("User", foreign_keys=[matched_by_user_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by_user_id])
    rejected_by_user = relationship("User", foreign_keys=[rejected_by_user_id])
    
    def __repr__(self):
        return f"<BankReconciliation(id={self.id}, type={self.match_type}, status={self.match_status}, confidence={self.confidence_score})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "transaction_id": str(self.transaction_id),
            "vendor_invoice_id": str(self.vendor_invoice_id) if self.vendor_invoice_id else None,
            "customer_invoice_id": str(self.customer_invoice_id) if self.customer_invoice_id else None,
            "voucher_id": str(self.voucher_id) if self.voucher_id else None,
            "match_type": self.match_type.value,
            "match_status": self.match_status.value,
            "confidence_score": float(self.confidence_score),
            "match_reason": self.match_reason,
            "transaction_amount": float(self.transaction_amount),
            "voucher_amount": float(self.voucher_amount),
            "amount_difference": float(self.amount_difference) if self.amount_difference else 0.0,
            "created_at": self.created_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }
