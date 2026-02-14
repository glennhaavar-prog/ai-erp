"""
Customer Invoice model - Outgoing invoices (sales invoices)
"""
from sqlalchemy import (
    Column, String, Numeric, Date, DateTime, Boolean, ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid
import enum

from app.database import Base


class CustomerInvoice(Base):
    """
    Customer Invoice = Utgående faktura (sales invoice)
    
    Complements VendorInvoice (incoming) to complete the A-Z accounting workflow
    """
    __tablename__ = "customer_invoices"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Client relationship
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Customer Information
    customer_name = Column(String(255), nullable=False, index=True)
    customer_org_number = Column(String(20), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_address = Column(Text, nullable=True)
    
    # Invoice Details
    invoice_number = Column(String(50), nullable=False, index=True)
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False)
    kid_number = Column(String(50), nullable=True, index=True)  # Payment reference
    
    # Amounts
    amount_excl_vat = Column(Numeric(15, 2), nullable=False)
    vat_amount = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="NOK", nullable=False)
    
    # Line Items
    line_items = Column(JSON, default=list)  # Array of invoice lines
    
    # Description
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Payment Status
    payment_status = Column(
        SQLEnum('unpaid', 'partially_paid', 'paid', 'overdue', name='payment_status_enum', create_type=False),
        default="unpaid",
        nullable=False,
        index=True
    )  # unpaid/partially_paid/paid/overdue (enum in DB)
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    paid_date = Column(Date, nullable=True)  # When fully paid
    
    # AI Processing
    ai_processed = Column(Boolean, default=False)
    ai_confidence_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    ai_booking_suggestion = Column(JSON, nullable=True)
    ai_detected_issues = Column(JSON, default=list)
    
    # Booking Status
    booked_at = Column(DateTime, nullable=True)
    ledger_entry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("general_ledger.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client", back_populates="customer_invoices")
    ledger_entry = relationship("GeneralLedger")
    
    def __repr__(self):
        return f"<CustomerInvoice(id={self.id}, number='{self.invoice_number}', total={self.total_amount})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "customer_name": self.customer_name,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "amount_excl_vat": float(self.amount_excl_vat),
            "vat_amount": float(self.vat_amount),
            "total_amount": float(self.total_amount),
            "currency": self.currency,
            "payment_status": self.payment_status,
            "paid_amount": float(self.paid_amount),
            "booked_at": self.booked_at.isoformat() if self.booked_at else None,
            "created_at": self.created_at.isoformat(),
        }
