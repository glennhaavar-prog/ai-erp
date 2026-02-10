"""
Task model - Oppgaveadministrasjon (Task Administration)
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean,
    Text, Date, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class TaskStatus(str, enum.Enum):
    """Status of task"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEVIATION = "deviation"


class TaskFrequency(str, enum.Enum):
    """Frequency of task"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    AD_HOC = "ad_hoc"


class TaskCategory(str, enum.Enum):
    """Category of task"""
    AVSTEMMING = "avstemming"
    RAPPORTERING = "rapportering"
    BOKFØRING = "bokføring"
    COMPLIANCE = "compliance"


class Task(Base):
    """
    Task = Oppgave i kvalitetssystemet
    
    Hver klient har en liste over oppgaver som skal utføres per periode.
    Oppgaver kan være auto-utført av AI eller manuelt utført av regnskapsfører.
    """
    __tablename__ = "tasks"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Task Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(TaskCategory), nullable=True, index=True)
    frequency = Column(SQLEnum(TaskFrequency), nullable=True)
    
    # Period
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=True)  # NULL for yearly tasks
    due_date = Column(Date, nullable=True)
    
    # Status
    status = Column(
        SQLEnum(TaskStatus), 
        default=TaskStatus.NOT_STARTED, 
        nullable=False,
        index=True
    )
    
    # Completion
    completed_by = Column(String(100), nullable=True)  # 'AI' or accountant name
    completed_at = Column(DateTime, nullable=True)
    documentation_url = Column(Text, nullable=True)
    ai_comment = Column(Text, nullable=True)  # AI's summary when auto-completed
    
    # Checklist Support
    is_checklist = Column(Boolean, default=False, nullable=False)
    parent_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Ordering
    sort_order = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client")
    subtasks = relationship(
        "Task",
        backref="parent_task",
        remote_side=[id],
        cascade="all, delete"
    )
    audit_logs = relationship(
        "TaskAuditLog",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return (
            f"<Task(id={self.id}, name='{self.name}', "
            f"status={self.status.value})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "name": self.name,
            "description": self.description,
            "category": self.category.value if self.category else None,
            "frequency": self.frequency.value if self.frequency else None,
            "period_year": self.period_year,
            "period_month": self.period_month,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "completed_by": self.completed_by,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "documentation_url": self.documentation_url,
            "ai_comment": self.ai_comment,
            "is_checklist": self.is_checklist,
            "parent_task_id": str(self.parent_task_id) if self.parent_task_id else None,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
