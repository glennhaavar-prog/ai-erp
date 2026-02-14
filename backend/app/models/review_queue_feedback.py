"""
Review Queue Feedback Model - AI learning from accountant decisions
"""
from sqlalchemy import Column, String, Boolean, JSON, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class ReviewQueueFeedback(Base):
    """
    Lagrer feedback fra regnskapsfører på AI-forslag
    
    Når regnskapsfører godkjenner eller korrigerer et AI-forslag,
    lagres denne feedbacken strukturert for ML-modell fine-tuning.
    """
    __tablename__ = "review_queue_feedback"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relasjon til review queue item
    review_queue_id = Column(
        UUID(as_uuid=True),
        ForeignKey("review_queue.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relasjon til faktura (nullable for andre bilagstyper)
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vendor_invoices.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for employee expenses, inventory adjustments, etc.
        index=True
    )
    
    # Relasjon til bruker (nullable for anonymisering)
    reviewed_by = Column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="SET NULL"),  # Users table doesn't exist yet
        nullable=True
    )
    
    # Feedback type
    action = Column(
        String(20), 
        nullable=False,
        index=True
    )  # 'approved', 'rejected', 'corrected'
    
    # AI's original prediction
    ai_suggestion = Column(JSON, nullable=False)
    # Structure:
    # {
    #   "account_number": "4000",
    #   "vat_code": "5",
    #   "confidence_account": 0.75,
    #   "confidence_vat": 0.85,
    #   "reasoning": "Typical office expense pattern"
    # }
    
    # Regnskapsførers korreksjon (hvis avvist/korrigert)
    accountant_correction = Column(JSON, nullable=True)
    # Structure:
    # {
    #   "account_number": "6000",
    #   "vat_code": "5",
    #   "reason": "Should be consultant fee, not office expense"
    # }
    
    # Accuracy metrics
    account_correct = Column(Boolean, nullable=True)
    vat_correct = Column(Boolean, nullable=True)
    fully_correct = Column(Boolean, nullable=True)
    
    # Context (for å forstå hva som påvirket beslutningen)
    invoice_metadata = Column(JSON, nullable=True)
    # Structure:
    # {
    #   "vendor_name": "Acme Consulting AS",
    #   "amount": 12500.00,
    #   "description": "Konsulenthonorar Q1",
    #   "previous_invoices_count": 5,
    #   "amount_category": "medium"
    # }
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    review_queue_item = relationship(
        "ReviewQueue",
        back_populates="feedback"
    )
    invoice = relationship("VendorInvoice")  # Optional - only for supplier invoices
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_feedback_fully_correct', 'fully_correct'),
        Index('idx_feedback_action_created', 'action', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ReviewQueueFeedback(id={self.id}, action='{self.action}', fully_correct={self.fully_correct})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "review_queue_id": str(self.review_queue_id),
            "invoice_id": str(self.invoice_id),
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "action": self.action,
            "ai_suggestion": self.ai_suggestion,
            "accountant_correction": self.accountant_correction,
            "account_correct": self.account_correct,
            "vat_correct": self.vat_correct,
            "fully_correct": self.fully_correct,
            "invoice_metadata": self.invoice_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
