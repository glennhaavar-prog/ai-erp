"""
Customer Ledger models - Kundereskontro
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Numeric, Date
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid

from app.database import Base


class CustomerLedger(Base):
    """
    Customer Ledger = Kundereskontro entry
    
    Tracks individual customer invoices and their payment status.
    Must reconcile with account 1500 (Kundefordringer).
    """
    __tablename__ = "customer_ledger"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Customer (can be NULL for one-time customers)
    customer_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    customer_name = Column(String(255), nullable=False)  # Denormalized for performance
    
    # Voucher link
    voucher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("general_ledger.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Invoice Details
    invoice_number = Column(String(100), nullable=True)
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    kid_number = Column(String(50), nullable=True, index=True)  # KID for automatic matching
    
    # Amounts
    amount = Column(Numeric(15, 2), nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="NOK", nullable=False)
    
    # Status
    status = Column(
        String(50),
        default="open",
        nullable=False,
        index=True
    )  # 'open', 'partially_paid', 'paid', 'overdue'
    
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
    voucher = relationship("GeneralLedger")
    transactions = relationship(
        "CustomerLedgerTransaction",
        back_populates="ledger_entry",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return (
            f"<CustomerLedger(id={self.id}, customer_name='{self.customer_name}', "
            f"amount={self.amount}, remaining={self.remaining_amount})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "customer_name": self.customer_name,
            "voucher_id": str(self.voucher_id),
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "kid_number": self.kid_number,
            "amount": float(self.amount),
            "remaining_amount": float(self.remaining_amount),
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class CustomerLedgerTransaction(Base):
    """
    Customer Ledger Transaction
    
    Tracks payments and adjustments to customer invoices.
    """
    __tablename__ = "customer_ledger_transactions"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent Ledger Entry
    ledger_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_ledger.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Voucher link (payment voucher)
    voucher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("general_ledger.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Transaction Details
    transaction_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    type = Column(
        String(50),
        nullable=False
    )  # 'invoice', 'payment', 'credit_note'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    ledger_entry = relationship("CustomerLedger", back_populates="transactions")
    voucher = relationship("GeneralLedger")
    
    def __repr__(self):
        return (
            f"<CustomerLedgerTransaction(id={self.id}, type={self.type}, "
            f"amount={self.amount})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "ledger_id": str(self.ledger_id),
            "voucher_id": str(self.voucher_id),
            "transaction_date": self.transaction_date.isoformat(),
            "amount": float(self.amount),
            "type": self.type,
            "created_at": self.created_at.isoformat(),
        }
