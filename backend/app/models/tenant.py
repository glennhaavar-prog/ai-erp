"""
Tenant model - Regnskapsbyrå (Accounting Firms)
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class SubscriptionTier(str, enum.Enum):
    """Subscription tiers for tenants"""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Tenant(Base):
    """
    Tenant = Regnskapsbyrå (Accounting firm)
    
    Multi-tenant architecture: All data is scoped by tenant_id
    """
    __tablename__ = "tenants"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Company Information
    name = Column(String(255), nullable=False, index=True)
    org_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Subscription
    subscription_tier = Column(
        SQLEnum(SubscriptionTier),
        default=SubscriptionTier.BASIC,
        nullable=False
    )
    max_clients = Column(Integer, nullable=True)  # NULL = unlimited
    
    # Billing
    billing_email = Column(String(255), nullable=True)
    
    # Settings (JSONB for flexibility)
    settings = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    clients = relationship("Client", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', org_number='{self.org_number}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "org_number": self.org_number,
            "subscription_tier": self.subscription_tier.value,
            "max_clients": self.max_clients,
            "billing_email": self.billing_email,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
