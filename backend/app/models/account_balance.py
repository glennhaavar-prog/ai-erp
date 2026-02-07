"""
Account Balance model - Opening balances for accounts
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Date, Numeric, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid

from app.database import Base


class AccountBalance(Base):
    """
    AccountBalance = Inngående saldo per konto
    
    Stores opening balance for each account at the beginning of a fiscal period.
    Used as starting point for saldobalanse calculations.
    """
    __tablename__ = "account_balances"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Account reference
    account_number = Column(String(10), nullable=False, index=True)
    
    # Balance Information
    opening_balance = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    opening_date = Column(Date, nullable=False, index=True)  # Date of opening balance
    fiscal_year = Column(String(4), nullable=False)  # Which fiscal year this applies to
    
    # Description
    description = Column(String(255), nullable=True)
    
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
    
    # Constraints - one opening balance per account per fiscal year per client
    __table_args__ = (
        UniqueConstraint(
            'client_id', 
            'account_number', 
            'fiscal_year', 
            name='uq_client_account_fiscal_year'
        ),
    )
    
    def __repr__(self):
        return (
            f"<AccountBalance(id={self.id}, account={self.account_number}, "
            f"balance={self.opening_balance}, date={self.opening_date})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "account_number": self.account_number,
            "opening_balance": float(self.opening_balance),
            "opening_date": self.opening_date.isoformat(),
            "fiscal_year": self.fiscal_year,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
