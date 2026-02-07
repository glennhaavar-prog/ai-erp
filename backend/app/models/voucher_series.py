"""
Voucher Series model - Bilagsserier for nummerering av bilag
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class VoucherSeries(Base):
    """
    Voucher Series = Bilagsserie

    Each series (EF, BK, MAN etc) has its own sequential numbering.
    Used for organizing journal entries by source type.

    Common series:
    - EF: EHF elektroniske fakturaer (electronic invoices)
    - BK: Banktransaksjoner (bank transactions)
    - MAN: Manuelle posteringer (manual entries)
    """
    __tablename__ = "voucher_series"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant (FK to clients)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Series identification
    code = Column(String(10), nullable=False)  # "EF", "BK", "MAN"
    name = Column(String(100), nullable=False)  # Human-readable name

    # Sequential numbering
    next_number = Column(Integer, default=1)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="voucher_series")
    journal_entries = relationship("GeneralLedger", back_populates="voucher_series_rel")

    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'code', name='uq_voucher_series_client_code'),
    )

    def __repr__(self):
        return f"<VoucherSeries(id={self.id}, code='{self.code}', name='{self.name}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "code": self.code,
            "name": self.name,
            "next_number": self.next_number,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_next_voucher_number(self) -> str:
        """
        Get the next voucher number and increment counter.
        Returns formatted string like "EF-00001"
        """
        number = self.next_number
        self.next_number += 1
        return f"{self.code}-{number:05d}"
