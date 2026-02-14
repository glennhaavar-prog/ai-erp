"""
Bank Transaction model - Bank transactions for reconciliation
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


class TransactionType(str, enum.Enum):
    """Transaction type"""
    DEBIT = "debit"    # Money out
    CREDIT = "credit"  # Money in


class TransactionStatus(str, enum.Enum):
    """Transaction reconciliation status"""
    UNMATCHED = "unmatched"       # Not matched yet
    MATCHED = "matched"           # Matched to invoice/ledger
    REVIEWED = "reviewed"         # Manually reviewed
    IGNORED = "ignored"           # Marked as ignorable


class BankTransaction(Base):
    """
    Bank Transaction = Single transaction from bank statement
    
    Used for bank reconciliation workflow:
    1. Upload CSV/Excel from bank
    2. AI matches transactions to invoices
    3. Accountant approves/corrects matches
    4. Unmatched transactions go to review queue
    """
    __tablename__ = "bank_transactions"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Client relationship
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Transaction Details
    transaction_date = Column(DateTime, nullable=False, index=True)
    booking_date = Column(DateTime, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(
        SQLEnum(TransactionType),
        nullable=False,
        index=True
    )
    
    # Description and References
    description = Column(Text, nullable=False)
    reference_number = Column(String(100), nullable=True)
    kid_number = Column(String(50), nullable=True, index=True)  # Norwegian KID number
    
    # Counterparty
    counterparty_name = Column(String(255), nullable=True)
    counterparty_account = Column(String(50), nullable=True)
    
    # Bank Details
    bank_account = Column(String(20), nullable=False, index=True)  # Own account (actual bank account number)
    ledger_account_number = Column(String(20), nullable=True, index=True)  # Chart of accounts number for ledger matching
    balance_after = Column(Numeric(15, 2), nullable=True)
    
    # Reconciliation
    status = Column(
        SQLEnum(TransactionStatus),
        default=TransactionStatus.UNMATCHED,
        nullable=False,
        index=True
    )
    
    # AI Matching
    ai_matched_invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vendor_invoices.id", ondelete="SET NULL"),
        nullable=True
    )
    ai_match_confidence = Column(Numeric(5, 2), nullable=True)  # 0-100
    ai_match_reason = Column(Text, nullable=True)
    
    # Manual Matching
    manually_matched_invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vendor_invoices.id", ondelete="SET NULL"),
        nullable=True
    )
    matched_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    matched_at = Column(DateTime, nullable=True)
    
    # Posting
    posted_to_ledger = Column(Boolean, default=False, nullable=False)
    ledger_entry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("general_ledger.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Upload metadata
    upload_batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    original_filename = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client", back_populates="bank_transactions")
    ai_matched_invoice = relationship(
        "VendorInvoice",
        foreign_keys=[ai_matched_invoice_id],
        back_populates="ai_matched_transactions"
    )
    manually_matched_invoice = relationship(
        "VendorInvoice",
        foreign_keys=[manually_matched_invoice_id]
    )
    
    def __repr__(self):
        return f"<BankTransaction(id={self.id}, date={self.transaction_date}, amount={self.amount}, status={self.status})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "transaction_date": self.transaction_date.isoformat(),
            "booking_date": self.booking_date.isoformat() if self.booking_date else None,
            "amount": float(self.amount),
            "transaction_type": self.transaction_type.value,
            "description": self.description,
            "reference_number": self.reference_number,
            "kid_number": self.kid_number,
            "counterparty_name": self.counterparty_name,
            "counterparty_account": self.counterparty_account,
            "bank_account": self.bank_account,
            "status": self.status.value,
            "ai_match_confidence": float(self.ai_match_confidence) if self.ai_match_confidence else None,
            "posted_to_ledger": self.posted_to_ledger,
            "created_at": self.created_at.isoformat(),
        }
