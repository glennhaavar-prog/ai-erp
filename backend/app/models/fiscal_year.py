"""
Fiscal Year model - Regnskapsår med perioder og status
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid

from app.database import Base


class FiscalYear(Base):
    """
    Fiscal Year = Regnskapsår

    Represents a company's accounting year (usually calendar year in Norway).
    Contains 13 accounting periods (12 months + year-end adjustments).

    Norwegian fiscal year typically runs Jan 1 - Dec 31.
    """
    __tablename__ = "fiscal_years"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant (FK to clients)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Year identification
    year = Column(Integer, nullable=False)  # e.g., 2026

    # Period boundaries
    start_date = Column(Date, nullable=False)  # e.g., 2026-01-01
    end_date = Column(Date, nullable=False)    # e.g., 2026-12-31

    # Status flags
    is_closed = Column(Boolean, default=False)  # Year closed for new entries
    is_locked = Column(Boolean, default=False)  # Year locked (cannot reopen)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="fiscal_years")
    periods = relationship(
        "AccountingPeriod",
        back_populates="fiscal_year",
        cascade="all, delete-orphan",
        order_by="AccountingPeriod.period_number"
    )
    journal_entries = relationship("GeneralLedger", back_populates="fiscal_year_rel")

    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'year', name='uq_fiscal_years_client_year'),
    )

    def __repr__(self):
        return f"<FiscalYear(id={self.id}, year={self.year}, client_id={self.client_id})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "year": self.year,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_closed": self.is_closed,
            "is_locked": self.is_locked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def is_current(self) -> bool:
        """Check if this fiscal year contains today's date"""
        today = date.today()
        return self.start_date <= today <= self.end_date

    def get_period_for_date(self, target_date: date) -> int:
        """
        Get the period number (1-12) for a given date.
        Returns 13 for year-end adjustments (only valid for Dec 31).
        """
        if target_date < self.start_date or target_date > self.end_date:
            raise ValueError(f"Date {target_date} is not within fiscal year {self.year}")
        return target_date.month
