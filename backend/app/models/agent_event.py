"""
Agent Event model - Hendelser som trigger orkestratoren
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class AgentEvent(Base):
    """
    Agent Event = Hendelse i systemet
    
    Orkestratoren lytter på events og oppretter tasks.
    Events er hvordan agenter kommuniserer indirekte.
    """
    __tablename__ = "agent_events"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Event Information
    event_type = Column(String(100), nullable=False, index=True)
    # 'invoice_received', 'invoice_parsed', 'booking_completed',
    # 'correction_received', 'period_closing', 'reconciliation_needed'
    
    payload = Column(JSON, nullable=False)
    # Event-specific data
    
    # Processing
    processed = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Client", foreign_keys=[tenant_id])
    
    def __repr__(self):
        return (
            f"<AgentEvent(id={self.id}, type={self.event_type}, "
            f"processed={self.processed})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "event_type": self.event_type,
            "payload": self.payload,
            "processed": self.processed,
            "created_at": self.created_at.isoformat(),
        }
