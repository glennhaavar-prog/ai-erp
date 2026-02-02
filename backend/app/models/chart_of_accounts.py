"""
Chart of Accounts model - Kontoplan (NS 4102 for Norway)
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey,
    UniqueConstraint, ARRAY, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Account(Base):
    """
    Account = Konto i kontoplan
    
    Based on Norwegian standard NS 4102
    Each client has their own chart of accounts
    """
    __tablename__ = "chart_of_accounts"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Account Information
    account_number = Column(String(10), nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # asset/liability/equity/revenue/expense
    
    # Hierarchy
    parent_account_number = Column(String(10), nullable=True)  # For sub-accounts
    account_level = Column(Integer, default=1)
    
    # VAT & Tax
    default_vat_code = Column(String(10), nullable=True)
    vat_deductible = Column(Boolean, default=True)
    
    # Reconciliation
    requires_reconciliation = Column(Boolean, default=False)
    reconciliation_frequency = Column(String(20), nullable=True)  # daily/monthly/quarterly
    
    # AI Learning (helps agent make better decisions)
    ai_suggested_descriptions = Column(ARRAY(String), default=list)  # Common descriptions
    ai_usage_count = Column(Integer, default=0)  # How often agent uses this account
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client", back_populates="chart_of_accounts")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'account_number', name='uq_client_account_number'),
    )
    
    def __repr__(self):
        return f"<Account(id={self.id}, number='{self.account_number}', name='{self.account_name}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "account_number": self.account_number,
            "account_name": self.account_name,
            "account_type": self.account_type,
            "default_vat_code": self.default_vat_code,
            "is_active": self.is_active,
            "ai_usage_count": self.ai_usage_count,
        }
