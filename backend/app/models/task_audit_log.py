"""
Task Audit Log model - Sporbarhet for oppgaveadministrasjon
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class TaskAuditAction(str, enum.Enum):
    """Action performed on task"""
    CREATED = "created"
    COMPLETED = "completed"
    MARKED_DEVIATION = "marked_deviation"
    MANUALLY_CHECKED = "manually_checked"
    AUTO_COMPLETED = "auto_completed"


class TaskAuditResult(str, enum.Enum):
    """Result of action"""
    OK = "ok"
    DEVIATION = "deviation"


class TaskAuditLog(Base):
    """
    Task Audit Log = Revisjonsspor for oppgaver
    
    Full sporbarhet - hver endring på oppgaver logges.
    Kan IKKE endres eller slettes.
    """
    __tablename__ = "task_audit_log"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Task Reference
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Action Details
    action = Column(SQLEnum(TaskAuditAction), nullable=False)
    performed_by = Column(String(100), nullable=False)  # 'AI-agent' or user name
    performed_at = Column(DateTime, nullable=False, index=True)
    
    # Result
    result = Column(SQLEnum(TaskAuditResult), nullable=True)
    result_description = Column(Text, nullable=True)
    documentation_reference = Column(Text, nullable=True)  # URL to PDF, report, etc.
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    task = relationship("Task", back_populates="audit_logs")
    
    def __repr__(self):
        return (
            f"<TaskAuditLog(id={self.id}, action={self.action.value}, "
            f"performed_by='{self.performed_by}')>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "action": self.action.value,
            "performed_by": self.performed_by,
            "performed_at": self.performed_at.isoformat(),
            "result": self.result.value if self.result else None,
            "result_description": self.result_description,
            "documentation_reference": self.documentation_reference,
            "created_at": self.created_at.isoformat(),
        }
