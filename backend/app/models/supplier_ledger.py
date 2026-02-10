"""
Supplier Ledger models - Leverandørreskontro
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


class SupplierLedger(Base):
    """
    Supplier Ledger = Leverandørreskontro entry
    
    Tracks individual supplier invoices and their payment status.
    Must reconcile with account 2400 (Leverandørgjeld).
    """
    __tablename__ = "supplier_ledger"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Supplier
    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
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
    )  # 'open', 'partially_paid', 'paid'
    
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
    supplier = relationship("Vendor")
    voucher = relationship("GeneralLedger")
    transactions = relationship(
        "SupplierLedgerTransaction",
        back_populates="ledger_entry",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return (
            f"<SupplierLedger(id={self.id}, supplier_id={self.supplier_id}, "
            f"amount={self.amount}, remaining={self.remaining_amount})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "supplier_id": str(self.supplier_id),
            "voucher_id": str(self.voucher_id),
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "amount": float(self.amount),
            "remaining_amount": float(self.remaining_amount),
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SupplierLedgerTransaction(Base):
    """
    Supplier Ledger Transaction
    
    Tracks payments and adjustments to supplier invoices.
    """
    __tablename__ = "supplier_ledger_transactions"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent Ledger Entry
    ledger_id = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier_ledger.id", ondelete="CASCADE"),
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
    ledger_entry = relationship("SupplierLedger", back_populates="transactions")
    voucher = relationship("GeneralLedger")
    
    def __repr__(self):
        return (
            f"<SupplierLedgerTransaction(id={self.id}, type={self.type}, "
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
