"""
Accrual model - Periodisering

Handles time-based allocation of expenses/revenues.
Common for insurance, subscriptions, rent.
"""

from sqlalchemy import (
    Column, String, Text, Date, Numeric, Boolean, 
    TIMESTAMP, CheckConstraint, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Accrual(Base):
    """
    Accrual = Periodisering
    
    Represents a time-based expense/revenue allocation.
    Examples: insurance (12 months), rent (3 months), subscriptions.
    """
    
    __tablename__ = "accruals"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    
    # Description
    description = Column(Text, nullable=False)
    
    # Time period
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    
    # Amounts
    total_amount = Column(Numeric(15, 2), nullable=False)
    
    # Accounts (NS 4102)
    balance_account = Column(String(10), nullable=False)  # Kortsiktig fordring/gjeld
    result_account = Column(String(10), nullable=False)   # Kostnad/inntekt
    
    # Posting schedule
    frequency = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    next_posting_date = Column(Date)
    
    # AI features
    auto_post = Column(Boolean, default=True)
    ai_detected = Column(Boolean, default=False)
    source_invoice_id = Column(UUID(as_uuid=True), ForeignKey("vendor_invoices.id"))
    
    # Status
    status = Column(String(20), nullable=False, default="active")  # active/completed/cancelled
    created_by = Column(String(20), nullable=False)  # ai_agent/user
    
    # Timestamps
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    client = relationship("Client", back_populates="accruals")
    source_invoice = relationship("VendorInvoice", back_populates="accruals")
    postings = relationship("AccrualPosting", back_populates="accrual", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("to_date >= from_date", name="check_dates"),
        CheckConstraint("total_amount > 0", name="check_amount"),
    )
    
    def __repr__(self):
        return f"<Accrual(id={self.id}, description='{self.description}', amount={self.total_amount})>"
