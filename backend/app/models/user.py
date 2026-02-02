"""
User model - Regnskapsførere (Accountants)
"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class User(Base):
    """
    User = Regnskapsfører/bokfører
    
    Users belong to a tenant (accounting firm) and can access
    specific clients based on assigned_clients array.
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # User Information
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Role-based access control
    role = Column(String(50), nullable=False)  # admin/senior_accountant/accountant/viewer
    
    # Access Control
    assigned_clients = Column(ARRAY(UUID), default=list)  # Array of client IDs
    permissions = Column(JSON, default=dict)  # Granular permissions
    
    # BankID Integration
    national_id_hash = Column(String(255), nullable=True)  # Hashed fødselsnummer
    bankid_verified = Column(Boolean, default=False)
    last_bankid_verification = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    def to_dict(self):
        """Convert to dictionary (exclude password)"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "is_active": self.is_active,
            "bankid_verified": self.bankid_verified,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
