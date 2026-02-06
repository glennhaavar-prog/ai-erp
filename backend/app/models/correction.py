"""
Correction model - Menneskelige korreksjoner for læring
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, JSON, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Correction(Base):
    """
    Correction = Korreksjon fra regnskapsfører
    
    Når regnskapsfører korrigerer AI's forslag, lagres det her.
    Dette er kjernen i læringssystemet - patterns opprettes fra corrections.
    """
    __tablename__ = "corrections"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Source
    review_queue_id = Column(
        UUID(as_uuid=True),
        ForeignKey("review_queue.id"),
        nullable=False,
        index=True
    )
    
    journal_entry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("general_ledger.id"),
        nullable=False,
        index=True
    )
    
    # What AI suggested (original)
    original_entry = Column(JSON, nullable=False)
    
    # What accountant corrected to
    corrected_entry = Column(JSON, nullable=False)
    
    # Accountant's explanation (natural language)
    correction_reason = Column(Text, nullable=True)
    # "PowerRent delivers furniture, not office space"
    
    # Batch correction info
    batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    similar_corrected = Column(Integer, default=0)
    
    # Who corrected
    corrected_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Client", foreign_keys=[tenant_id])
    review_queue = relationship("ReviewQueue")
    journal_entry = relationship("GeneralLedger")
    user = relationship("User")
    
    def __repr__(self):
        return (
            f"<Correction(id={self.id}, journal_entry={self.journal_entry_id})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "review_queue_id": str(self.review_queue_id),
            "journal_entry_id": str(self.journal_entry_id),
            "original_entry": self.original_entry,
            "corrected_entry": self.corrected_entry,
            "correction_reason": self.correction_reason,
            "batch_id": str(self.batch_id) if self.batch_id else None,
            "similar_corrected": self.similar_corrected,
            "corrected_by": str(self.corrected_by),
            "created_at": self.created_at.isoformat(),
        }
