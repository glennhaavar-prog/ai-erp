"""
AccrualPosting model

Individual posting from an accrual schedule.
Links to GeneralLedger when posted.
"""

from sqlalchemy import (
    Column, String, Date, Numeric, 
    TIMESTAMP, CheckConstraint, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class AccrualPosting(Base):
    """
    Individual posting from an accrual schedule.
    
    Each accrual generates multiple postings (e.g., 12 monthly postings).
    When posted, creates a balanced GeneralLedger entry.
    """
    
    __tablename__ = "accrual_postings"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    accrual_id = Column(UUID(as_uuid=True), ForeignKey("accruals.id", ondelete="CASCADE"), nullable=False)
    
    # Posting details
    posting_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    period = Column(String(7), nullable=False)  # YYYY-MM
    
    # Link to general ledger
    general_ledger_id = Column(UUID(as_uuid=True), ForeignKey("general_ledger.id", ondelete="SET NULL"))
    
    # Status
    status = Column(String(20), nullable=False, default="pending")  # pending/posted/cancelled
    posted_by = Column(String(20))  # ai_agent/user
    posted_at = Column(TIMESTAMP)
    
    # Timestamps
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    
    # Relationships
    accrual = relationship("Accrual", back_populates="postings")
    general_ledger_entry = relationship("GeneralLedger", back_populates="accrual_postings")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_posting_amount"),
    )
    
    def __repr__(self):
        return f"<AccrualPosting(id={self.id}, date={self.posting_date}, amount={self.amount}, status='{self.status}')>"
