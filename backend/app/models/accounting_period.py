"""
Accounting Period model - Regnskapsperioder (1-13) innen regnskapsår
"""
from sqlalchemy import Column, Integer, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid

from app.database import Base


class AccountingPeriod(Base):
    """
    Accounting Period = Regnskapsperiode

    Represents a period within a fiscal year.
    Norwegian accounting uses 13 periods:
    - Periods 1-12: Monthly periods (Jan-Dec)
    - Period 13: Year-end adjustments (årsoppgjørsposteringer)

    Period closing prevents new entries and enables reporting.
    """
    __tablename__ = "accounting_periods"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Parent fiscal year
    fiscal_year_id = Column(
        UUID(as_uuid=True),
        ForeignKey("fiscal_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Period identification
    period_number = Column(Integer, nullable=False)  # 1-13

    # Period boundaries
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Status
    is_closed = Column(Boolean, default=False)  # Period closed for entries

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="periods")
    journal_entries = relationship("GeneralLedger", back_populates="period_rel")

    # Constraints
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'period_number', name='uq_accounting_periods_fy_number'),
    )

    def __repr__(self):
        return (
            f"<AccountingPeriod(id={self.id}, period={self.period_number}, "
            f"fiscal_year_id={self.fiscal_year_id})>"
        )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "fiscal_year_id": str(self.fiscal_year_id),
            "period_number": self.period_number,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_closed": self.is_closed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def is_year_end_period(self) -> bool:
        """Check if this is period 13 (year-end adjustments)"""
        return self.period_number == 13

    @property
    def period_name(self) -> str:
        """
        Get human-readable period name.
        Returns month name for periods 1-12, "Årsoppgjør" for period 13.
        """
        month_names = [
            "Januar", "Februar", "Mars", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Desember"
        ]
        if self.period_number == 13:
            return "Årsoppgjør"
        return month_names[self.period_number - 1]

    def contains_date(self, target_date: date) -> bool:
        """Check if a date falls within this period"""
        return self.start_date <= target_date <= self.end_date
