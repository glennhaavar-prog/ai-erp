"""
Reconciliation models - Balansekontoavstemming
"""
from sqlalchemy import Column, String, DateTime, Numeric, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ReconciliationStatus(str, enum.Enum):
    """Status for reconciliation"""
    PENDING = "pending"
    RECONCILED = "reconciled"
    APPROVED = "approved"


class ReconciliationType(str, enum.Enum):
    """Type of reconciliation"""
    BANK = "bank"
    RECEIVABLES = "receivables"
    PAYABLES = "payables"
    INVENTORY = "inventory"
    OTHER = "other"


class Reconciliation(Base):
    """
    Reconciliation = Balansekontoavstemming
    
    Tracks reconciliation of balance accounts for a specific period.
    Auto-calculates opening and closing balances from ledger.
    """
    __tablename__ = "reconciliations"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    
    # Balances
    opening_balance = Column(Numeric(15, 2), nullable=False)
    closing_balance = Column(Numeric(15, 2), nullable=False)
    expected_balance = Column(Numeric(15, 2), nullable=True)  # Manual input
    difference = Column(Numeric(15, 2), nullable=True)  # Auto-calculated
    
    # Classification
    status = Column(
        SQLEnum(ReconciliationStatus, values_callable=lambda x: [e.value for e in x], name='reconciliationstatus'),
        default=ReconciliationStatus.PENDING,
        nullable=False,
        index=True
    )
    reconciliation_type = Column(
        SQLEnum(ReconciliationType, values_callable=lambda x: [e.value for e in x], name='reconciliationtype'),
        nullable=False,
        index=True
    )
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps and User Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reconciled_at = Column(DateTime, nullable=True)
    reconciled_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    client = relationship("Client", back_populates="reconciliations")
    account = relationship("Account")
    attachments = relationship(
        "ReconciliationAttachment",
        back_populates="reconciliation",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Reconciliation(id={self.id}, account_id={self.account_id}, status={self.status})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "account_id": str(self.account_id),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "opening_balance": float(self.opening_balance) if self.opening_balance else 0.0,
            "closing_balance": float(self.closing_balance) if self.closing_balance else 0.0,
            "expected_balance": float(self.expected_balance) if self.expected_balance else None,
            "difference": float(self.difference) if self.difference else None,
            "status": self.status.value,
            "reconciliation_type": self.reconciliation_type.value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "reconciled_at": self.reconciled_at.isoformat() if self.reconciled_at else None,
            "reconciled_by": str(self.reconciled_by) if self.reconciled_by else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": str(self.approved_by) if self.approved_by else None,
        }


class ReconciliationAttachment(Base):
    """
    Attachment for reconciliation documentation
    """
    __tablename__ = "reconciliation_attachments"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    reconciliation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reconciliations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # File Information
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative path from uploads dir
    file_type = Column(String(50), nullable=True)
    file_size = Column(Numeric(15, 0), nullable=True)  # Bytes
    
    # Upload Tracking
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    reconciliation = relationship("Reconciliation", back_populates="attachments")
    
    def __repr__(self):
        return f"<ReconciliationAttachment(id={self.id}, file_name='{self.file_name}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "reconciliation_id": str(self.reconciliation_id),
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": int(self.file_size) if self.file_size else None,
            "uploaded_at": self.uploaded_at.isoformat(),
            "uploaded_by": str(self.uploaded_by) if self.uploaded_by else None,
        }
