"""
General Ledger models - Hovedbok (immutable journal entries)
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean,
    Text, Date, Numeric, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date
from decimal import Decimal
import uuid

from app.database import Base


class GeneralLedger(Base):
    """
    General Ledger = Hovedbok entry (Bilag)
    
    IMMUTABLE: Once posted, entries cannot be modified or deleted.
    Only reversals are allowed to correct mistakes.
    
    Each entry must balance: SUM(debits) = SUM(credits)
    """
    __tablename__ = "general_ledger"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Dates
    entry_date = Column(Date, nullable=False)  # When entry was created
    accounting_date = Column(Date, nullable=False, index=True)  # Accounting period date
    period = Column(String(7), nullable=False, index=True)  # YYYY-MM format
    fiscal_year = Column(Integer, nullable=False, index=True)
    
    # Voucher (Bilag)
    voucher_number = Column(String(50), nullable=False, index=True)  # Bilagsnummer
    voucher_series = Column(String(10), default="A")  # A/B/C series
    description = Column(Text, nullable=False)
    
    # Source Tracking
    source_type = Column(String(50), nullable=False)  # ehf_invoice/bank_transaction/manual etc
    source_id = Column(UUID(as_uuid=True), nullable=True)  # FK to source table
    
    # Creator Tracking (AI or Human)
    created_by_type = Column(String(20), nullable=False)  # ai_agent/user
    created_by_id = Column(UUID(as_uuid=True), nullable=True)  # user_id or agent_session_id
    
    # Reversal Handling (for corrections)
    is_reversed = Column(Boolean, default=False)
    reversed_by_entry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("general_ledger.id"),
        nullable=True
    )
    reversal_reason = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="posted", nullable=False)  # draft/posted/reversed
    locked = Column(Boolean, default=False)  # Locked after period close

    # FK relationships to accounting schema (nullable for backward compatibility)
    voucher_series_id = Column(
        UUID(as_uuid=True),
        ForeignKey("voucher_series.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    fiscal_year_id = Column(
        UUID(as_uuid=True),
        ForeignKey("fiscal_years.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounting_periods.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="general_ledger_entries")
    voucher_series_rel = relationship("VoucherSeries", back_populates="journal_entries")
    fiscal_year_rel = relationship("FiscalYear", back_populates="journal_entries")
    period_rel = relationship("AccountingPeriod", back_populates="journal_entries")
    lines = relationship(
        "GeneralLedgerLine",
        back_populates="general_ledger_entry",
        cascade="all, delete-orphan"
    )
    reversed_by = relationship("GeneralLedger", remote_side=[id])
    accrual_postings = relationship("AccrualPosting", back_populates="general_ledger_entry")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'voucher_series', 'voucher_number', name='uq_client_voucher'),
    )
    
    def __repr__(self):
        return (
            f"<GeneralLedger(id={self.id}, voucher={self.voucher_series}-{self.voucher_number}, "
            f"date={self.accounting_date})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "voucher_number": self.voucher_number,
            "voucher_series": self.voucher_series,
            "accounting_date": self.accounting_date.isoformat(),
            "period": self.period,
            "description": self.description,
            "source_type": self.source_type,
            "created_by_type": self.created_by_type,
            "status": self.status,
            "is_reversed": self.is_reversed,
            "locked": self.locked,
            "created_at": self.created_at.isoformat(),
        }


class GeneralLedgerLine(Base):
    """
    General Ledger Line = Bilagslinje (debit/credit entry)
    
    Each line represents one account movement.
    Multiple lines make up a complete journal entry.
    """
    __tablename__ = "general_ledger_lines"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent Entry
    general_ledger_id = Column(
        UUID(as_uuid=True),
        ForeignKey("general_ledger.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number = Column(Integer, nullable=False)  # Sequence within voucher
    
    # Accounting
    account_number = Column(String(10), nullable=False, index=True)
    debit_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    credit_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # VAT
    vat_code = Column(String(10), nullable=True)  # Legacy string code (kept for backward compatibility)
    tax_code_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tax_codes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    vat_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    vat_base_amount = Column(Numeric(15, 2), nullable=True)  # Amount VAT calculated from
    
    # Dimensions (optional - for cost centers, projects, etc)
    department_id = Column(UUID(as_uuid=True), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    cost_center_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Description
    line_description = Column(Text, nullable=True)
    
    # AI Metadata
    ai_confidence_score = Column(Integer, nullable=True)  # 0-100 for this line
    ai_reasoning = Column(Text, nullable=True)  # Why agent chose this account
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    general_ledger_entry = relationship("GeneralLedger", back_populates="lines")
    tax_code = relationship("TaxCode", foreign_keys=[tax_code_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('general_ledger_id', 'line_number', name='uq_gl_line_number'),
        CheckConstraint(
            'debit_amount >= 0 AND credit_amount >= 0',
            name='check_amounts_positive'
        ),
        CheckConstraint(
            '(debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0)',
            name='check_debit_or_credit'
        ),
    )
    
    def __repr__(self):
        return (
            f"<GeneralLedgerLine(id={self.id}, account={self.account_number}, "
            f"debit={self.debit_amount}, credit={self.credit_amount})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "general_ledger_id": str(self.general_ledger_id),
            "line_number": self.line_number,
            "account_number": self.account_number,
            "debit_amount": float(self.debit_amount),
            "credit_amount": float(self.credit_amount),
            "vat_code": self.vat_code,
            "vat_amount": float(self.vat_amount) if self.vat_amount else 0.0,
            "line_description": self.line_description,
            "ai_confidence_score": self.ai_confidence_score,
        }
