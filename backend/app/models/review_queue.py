"""
Review Queue model - Køsystem for menneskelig review
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean,
    Text, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ReviewPriority(str, enum.Enum):
    """Priority levels for review items"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ReviewStatus(str, enum.Enum):
    """Status of review item"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    CORRECTED = "corrected"
    REJECTED = "rejected"


class IssueCategory(str, enum.Enum):
    """Category of issue that needs review"""
    LOW_CONFIDENCE = "low_confidence"
    UNKNOWN_VENDOR = "unknown_vendor"
    UNUSUAL_AMOUNT = "unusual_amount"
    MISSING_VAT = "missing_vat"
    UNCLEAR_DESCRIPTION = "unclear_description"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PROCESSING_ERROR = "processing_error"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class ReviewQueue(Base):
    """
    Review Queue = Kø for menneskelig review
    
    When AI is uncertain or detects issues, items are sent here
    for human accountants to review and approve/correct.
    """
    __tablename__ = "review_queue"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Source (what needs review)
    source_type = Column(String(50), nullable=False)  # vendor_invoice/bank_transaction etc
    source_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Priority & Status
    priority = Column(SQLEnum(ReviewPriority), default=ReviewPriority.MEDIUM, nullable=False)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False, index=True)
    
    # Issue Details
    issue_category = Column(SQLEnum(IssueCategory), nullable=False)
    issue_description = Column(Text, nullable=False)
    
    # AI Suggestion
    ai_suggestion = Column(JSON, nullable=True)  # What AI suggests
    ai_confidence = Column(Integer, nullable=True)  # 0-100
    ai_reasoning = Column(Text, nullable=True)  # Why AI is uncertain
    
    # Assignment
    assigned_to_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    
    # Resolution
    resolved_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Apply to Similar
    apply_to_similar = Column(Boolean, default=False)  # Create pattern from this correction
    similar_items_affected = Column(Integer, default=0)  # Count of similar items auto-fixed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client")
    
    def __repr__(self):
        return (
            f"<ReviewQueue(id={self.id}, priority={self.priority.value}, "
            f"status={self.status.value})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "source_type": self.source_type,
            "source_id": str(self.source_id),
            "priority": self.priority.value,
            "status": self.status.value,
            "issue_category": self.issue_category.value,
            "issue_description": self.issue_description,
            "ai_confidence": self.ai_confidence,
            "ai_reasoning": self.ai_reasoning,
            "assigned_to_user_id": str(self.assigned_to_user_id) if self.assigned_to_user_id else None,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
