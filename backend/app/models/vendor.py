"""
Vendor model - Leverandører
"""
from sqlalchemy import (
    Column, String, Boolean, DateTime, JSON, ForeignKey,
    UniqueConstraint, Numeric
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid

from app.database import Base


class Vendor(Base):
    """
    Vendor = Leverandør
    
    Stores vendor information and AI-learned patterns
    for better invoice processing.
    """
    __tablename__ = "vendors"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Vendor Information
    vendor_number = Column(String(50), nullable=False)  # Sequential per client
    name = Column(String(255), nullable=False, index=True)
    org_number = Column(String(20), nullable=True, index=True)
    
    # Contact Information
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Accounting
    account_number = Column(String(10), nullable=False)  # Default payable account
    payment_terms = Column(String(50), default="30")  # "30 days net"
    default_vat_code = Column(String(10), nullable=True)
    
    # Banking
    bank_account = Column(String(50), nullable=True)
    iban = Column(String(50), nullable=True)
    swift_bic = Column(String(20), nullable=True)
    
    # AI Learning (helps agent make better decisions)
    ai_learned_categories = Column(JSON, default=dict)  # Common expense categories
    ai_average_amount = Column(Numeric(15, 2), nullable=True)  # Detect anomalies
    ai_payment_pattern = Column(String(50), nullable=True)  # "always_on_time" etc
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client", back_populates="vendors")
    invoices = relationship("VendorInvoice", back_populates="vendor")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'vendor_number', name='uq_client_vendor_number'),
    )
    
    def __repr__(self):
        return f"<Vendor(id={self.id}, name='{self.name}', client_id={self.client_id})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "vendor_number": self.vendor_number,
            "name": self.name,
            "org_number": self.org_number,
            "email": self.email,
            "phone": self.phone,
            "payment_terms": self.payment_terms,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }
