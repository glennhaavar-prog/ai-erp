"""
Audit Trail model - Fullstendig revisjonslogg (immutable)
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class AuditTrail(Base):
    """
    Audit Trail = Revisjonslogg
    
    IMMUTABLE: Logs every change to the system for compliance.
    Required by Norwegian Accounting Act (5-year retention).
    
    Tracks:
    - Who made the change (user or AI)
    - What was changed
    - When it was changed
    - Why it was changed
    - Old and new values
    """
    __tablename__ = "audit_trail"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=True,  # NULL for tenant-level changes
        index=True
    )
    
    # What was changed
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action = Column(String(20), nullable=False)  # create/update/delete
    
    # Old and new values
    old_value = Column(JSON, nullable=True)  # Before change
    new_value = Column(JSON, nullable=True)  # After change
    
    # Who made the change
    changed_by_type = Column(String(20), nullable=False)  # user/ai_agent/system
    changed_by_id = Column(UUID(as_uuid=True), nullable=True)  # user_id or agent_session_id
    changed_by_name = Column(String(255), nullable=True)  # Human-readable name
    
    # Why was it changed
    reason = Column(Text, nullable=True)  # Optional explanation
    
    # Context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)  # Browser/client info
    
    # Timestamp (immutable!)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    client = relationship("Client")
    
    def __repr__(self):
        return (
            f"<AuditTrail(id={self.id}, table={self.table_name}, "
            f"action={self.action}, by={self.changed_by_type})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id) if self.client_id else None,
            "table_name": self.table_name,
            "record_id": str(self.record_id),
            "action": self.action,
            "changed_by_type": self.changed_by_type,
            "changed_by_name": self.changed_by_name,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }
