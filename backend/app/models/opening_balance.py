"""
Opening Balance models - Åpningsbalanse Import

Handles import and validation of opening balances for new clients.
Critical validations:
1. SUM(debits) MUST equal SUM(credits) - no exceptions
2. Bank accounts (1920, 1921, etc.) MUST match actual bank balance
"""
from sqlalchemy import (
    Column, String, Numeric, DateTime, Boolean, ForeignKey, 
    Enum as SQLEnum, Text, Date, Integer
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class OpeningBalanceStatus(str, enum.Enum):
    """Opening balance import status"""
    DRAFT = "draft"              # Uploaded, not validated yet
    VALIDATING = "validating"    # Validation in progress
    INVALID = "invalid"          # Validation failed
    VALID = "valid"              # Passed all validations
    IMPORTED = "imported"        # Successfully imported to ledger
    FAILED = "failed"            # Import failed


class OpeningBalance(Base):
    """
    Opening Balance = Åpningsbalanse Import Session
    
    Tracks an opening balance import from upload to posting.
    Each import session contains multiple line items (accounts).
    
    CRITICAL VALIDATIONS:
    1. Balance Check: SUM(debit) MUST = SUM(credit)
    2. Bank Balance Match: Bank accounts must match actual bank balance
    3. Account Existence: All accounts must exist in chart of accounts
    """
    __tablename__ = "opening_balances"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Client relationship
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Import Details
    import_date = Column(Date, nullable=False)  # Date of opening balance
    fiscal_year = Column(String(4), nullable=False)  # e.g., "2024"
    description = Column(Text, nullable=False, default="Åpningsbalanse")
    
    # Status
    status = Column(
        SQLEnum(OpeningBalanceStatus),
        default=OpeningBalanceStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Validation Results
    is_balanced = Column(Boolean, default=False)  # SUM(debit) = SUM(credit)
    balance_difference = Column(Numeric(15, 2), default=0)  # Should be 0.00
    
    bank_balance_verified = Column(Boolean, default=False)  # Bank accounts checked
    bank_balance_errors = Column(JSONB, nullable=True)  # Array of bank account issues
    
    missing_accounts = Column(JSONB, nullable=True)  # Accounts not in chart
    validation_errors = Column(JSONB, nullable=True)  # All validation errors
    
    # Totals (cached for performance)
    total_debit = Column(Numeric(15, 2), default=0)
    total_credit = Column(Numeric(15, 2), default=0)
    line_count = Column(Integer, default=0)
    
    # Upload metadata
    original_filename = Column(String(255), nullable=True)
    uploaded_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Import Result
    imported_at = Column(DateTime, nullable=True)
    journal_entry_id = Column(
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
    client = relationship("Client", back_populates="opening_balances")
    lines = relationship(
        "OpeningBalanceLine",
        back_populates="opening_balance",
        cascade="all, delete-orphan"
    )
    journal_entry = relationship("GeneralLedger")
    
    def __repr__(self):
        return (
            f"<OpeningBalance(id={self.id}, client_id={self.client_id}, "
            f"status={self.status}, balanced={self.is_balanced})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "import_date": self.import_date.isoformat(),
            "fiscal_year": self.fiscal_year,
            "description": self.description,
            "status": self.status.value,
            "is_balanced": self.is_balanced,
            "balance_difference": float(self.balance_difference) if self.balance_difference else 0.0,
            "bank_balance_verified": self.bank_balance_verified,
            "total_debit": float(self.total_debit),
            "total_credit": float(self.total_credit),
            "line_count": self.line_count,
            "created_at": self.created_at.isoformat(),
            "imported_at": self.imported_at.isoformat() if self.imported_at else None,
        }


class OpeningBalanceLine(Base):
    """
    Opening Balance Line = Single account in opening balance
    
    Each line represents one account's opening balance (debit or credit).
    """
    __tablename__ = "opening_balance_lines"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent Opening Balance
    opening_balance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("opening_balances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number = Column(Integer, nullable=False)  # Sequence in file
    
    # Account Details
    account_number = Column(String(10), nullable=False, index=True)
    account_name = Column(String(255), nullable=False)  # From import file
    
    # Amounts
    debit_amount = Column(Numeric(15, 2), default=0, nullable=False)
    credit_amount = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Validation
    account_exists = Column(Boolean, default=False)  # Account in chart
    is_bank_account = Column(Boolean, default=False)  # Is this 1920, 1921, etc.?
    bank_balance_match = Column(Boolean, nullable=True)  # For bank accounts only
    expected_bank_balance = Column(Numeric(15, 2), nullable=True)  # From bank connection
    
    validation_errors = Column(JSONB, nullable=True)  # Array of error messages
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    opening_balance = relationship("OpeningBalance", back_populates="lines")
    
    def __repr__(self):
        return (
            f"<OpeningBalanceLine(id={self.id}, account={self.account_number}, "
            f"debit={self.debit_amount}, credit={self.credit_amount})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "opening_balance_id": str(self.opening_balance_id),
            "line_number": self.line_number,
            "account_number": self.account_number,
            "account_name": self.account_name,
            "debit_amount": float(self.debit_amount),
            "credit_amount": float(self.credit_amount),
            "account_exists": self.account_exists,
            "is_bank_account": self.is_bank_account,
            "bank_balance_match": self.bank_balance_match,
            "validation_errors": self.validation_errors,
        }
