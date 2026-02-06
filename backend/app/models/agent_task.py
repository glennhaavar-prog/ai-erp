"""
Agent Task model - Oppgaver for agenter
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class AgentTask(Base):
    """
    Agent Task = Oppgave for en spesialist-agent
    
    Orkestratoren oppretter tasks basert på events.
    Agenter claimer og utfører tasks.
    """
    __tablename__ = "agent_tasks"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Agent Information
    agent_type = Column(String(50), nullable=False, index=True)
    # 'orchestrator', 'invoice_parser', 'bookkeeper', 'reconciler'
    
    task_type = Column(String(100), nullable=False)
    # 'parse_invoice', 'book_invoice', 'evaluate_confidence',
    # 'process_correction', 'check_period', 'reconcile'
    
    # Status
    status = Column(String(20), nullable=False, default='pending', index=True)
    # 'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    
    priority = Column(Integer, nullable=False, default=5)
    # 1 = lowest, 10 = highest
    
    # Data
    payload = Column(JSON, nullable=False)
    # Task-specific data (invoice_id, correction_id, etc.)
    
    result = Column(JSON, nullable=True)
    # Agent's output (parsed data, journal entry, etc.)
    
    error_message = Column(Text, nullable=True)
    
    # Retry handling
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Parent task (for chained operations)
    parent_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_tasks.id"),
        nullable=True
    )
    
    # Relationships
    tenant = relationship("Client", foreign_keys=[tenant_id])
    parent_task = relationship("AgentTask", remote_side=[id])
    
    def __repr__(self):
        return (
            f"<AgentTask(id={self.id}, agent={self.agent_type}, "
            f"task={self.task_type}, status={self.status})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "agent_type": self.agent_type,
            "task_type": self.task_type,
            "status": self.status,
            "priority": self.priority,
            "payload": self.payload,
            "result": self.result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
