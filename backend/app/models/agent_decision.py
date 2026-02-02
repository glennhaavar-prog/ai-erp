"""
Agent Decision model - Logger alle AI-beslutninger
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean,
    Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class AgentDecision(Base):
    """
    Agent Decision = Log av AI-beslutning
    
    Logs every decision made by AI agents for:
    - Debugging
    - Learning
    - Audit trail
    - Performance monitoring
    """
    __tablename__ = "agent_decisions"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Agent Information
    agent_type = Column(String(50), nullable=False, index=True)  # invoice_agent/bank_agent etc
    agent_session_id = Column(String(255), nullable=True)  # Session/run ID
    
    # Decision Context
    decision_type = Column(String(50), nullable=False)  # auto_book/send_to_review/match_vendor etc
    source_type = Column(String(50), nullable=False)  # vendor_invoice/bank_transaction etc
    source_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Input Data (what agent received)
    input_data = Column(JSON, nullable=False)  # OCR text, vendor history, patterns etc
    
    # Output (what agent decided)
    decision = Column(JSON, nullable=False)  # Booking suggestion, vendor match etc
    confidence_score = Column(Integer, nullable=False)  # 0-100
    reasoning = Column(Text, nullable=True)  # Why agent made this decision
    
    # Patterns Used
    patterns_used = Column(JSON, nullable=True)  # Which learned patterns were applied
    
    # Human Feedback
    correct = Column(Boolean, nullable=True)  # TRUE if human approved, FALSE if corrected, NULL if pending
    human_feedback = Column(Text, nullable=True)  # Accountant's notes
    corrected_decision = Column(JSON, nullable=True)  # What human changed it to
    feedback_received_at = Column(DateTime, nullable=True)
    
    # Performance Metrics
    processing_time_ms = Column(Integer, nullable=True)  # How long did agent take
    model_used = Column(String(100), nullable=True)  # Which AI model
    tokens_used = Column(Integer, nullable=True)  # API tokens consumed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    client = relationship("Client")
    
    def __repr__(self):
        return (
            f"<AgentDecision(id={self.id}, agent={self.agent_type}, "
            f"confidence={self.confidence_score}, correct={self.correct})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "agent_type": self.agent_type,
            "decision_type": self.decision_type,
            "confidence_score": self.confidence_score,
            "correct": self.correct,
            "created_at": self.created_at.isoformat(),
        }
