"""
Agent Learned Pattern model - Cross-client læring
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean,
    Text, JSON, Numeric, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid

from app.database import Base


class AgentLearnedPattern(Base):
    """
    Agent Learned Pattern = Lært mønster fra menneskelig feedback
    
    When accountants correct AI suggestions 3+ times in similar ways,
    a pattern is created and applied automatically to future similar cases.
    
    This is the core of the learning system!
    """
    __tablename__ = "agent_learned_patterns"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Pattern Information
    pattern_type = Column(String(50), nullable=False, index=True)  # vendor_category/description_keyword etc
    pattern_name = Column(String(255), nullable=True)  # Human-readable name
    description = Column(Text, nullable=True)  # What this pattern does
    
    # Trigger (when to apply this pattern)
    trigger = Column(JSON, nullable=False)  # Conditions that trigger this pattern
    """
    Example triggers:
    {
        "vendor_id": "uuid",
        "description_contains": "office supplies",
        "amount_range": {"min": 0, "max": 5000}
    }
    """
    
    # Action (what to do when triggered)
    action = Column(JSON, nullable=False)  # What to do when pattern matches
    """
    Example actions:
    {
        "account": "6300",
        "vat_code": "5",
        "default_description": "Office supplies"
    }
    """
    
    # Scope (which clients does this apply to)
    applies_to_clients = Column(ARRAY(UUID), nullable=False, default=list)  # Array of client IDs
    global_pattern = Column(Boolean, default=False)  # Applies to ALL clients if TRUE
    
    # Performance Tracking
    success_rate = Column(Numeric(5, 4), default=Decimal("0.0000"))  # 0.0000 to 1.0000
    times_applied = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    times_incorrect = Column(Integer, default=0)
    
    # Confidence
    confidence_boost = Column(Integer, default=10)  # How much to boost confidence when applied
    
    # Learning Source
    created_from_decision_ids = Column(ARRAY(UUID), default=list)  # Which decisions created this
    learned_from_user_id = Column(UUID(as_uuid=True), nullable=True)  # Which accountant taught this
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_applied_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return (
            f"<AgentLearnedPattern(id={self.id}, type={self.pattern_type}, "
            f"success_rate={self.success_rate})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "pattern_type": self.pattern_type,
            "pattern_name": self.pattern_name,
            "trigger": self.trigger,
            "action": self.action,
            "success_rate": float(self.success_rate),
            "times_applied": self.times_applied,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }
    
    def update_success_rate(self, was_correct: bool):
        """Update success rate based on feedback"""
        self.times_applied += 1
        if was_correct:
            self.times_correct += 1
        else:
            self.times_incorrect += 1
        
        if self.times_applied > 0:
            self.success_rate = Decimal(self.times_correct) / Decimal(self.times_applied)
