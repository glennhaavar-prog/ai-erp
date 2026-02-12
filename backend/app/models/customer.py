"""
Customer Contact Register - Kundekort (KONTAKTREGISTER)

Master data for customers. The ledger references this.
No deletion allowed - only deactivation.
"""
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey,
    UniqueConstraint, Integer, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Customer(Base):
    """
    Customer Contact Card = Kundekort
    
    Master data for customers. This is the authoritative source.
    Customer ledger entries reference this table.
    
    Rules:
    - No deletion allowed (only deactivation via status='inactive')
    - Unique org_number/birth_number per client (if provided)
    - All changes logged in audit trail
    """
    __tablename__ = "customers"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # === BASIC INFORMATION ===
    customer_number = Column(String(50), nullable=False)  # Sequential per client
    
    # Name (can be company or person)
    is_company = Column(Boolean, default=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)  # Company or full person name
    
    # Identification
    org_number = Column(String(20), nullable=True, index=True)  # For companies
    birth_number = Column(String(20), nullable=True, index=True)  # For individuals (fødselsnummer)
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="Norge", nullable=False)
    
    # Contact
    contact_person = Column(String(255), nullable=True)  # For companies
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    
    # === FINANCIAL INFORMATION ===
    # Payment terms
    payment_terms_days = Column(Integer, default=14, nullable=False)  # Days until due
    
    # Accounting defaults
    currency = Column(String(3), default="NOK", nullable=False)
    vat_code = Column(String(10), nullable=True)  # Default VAT code
    default_revenue_account = Column(String(10), nullable=True)  # Default account number
    
    # KID (Kunde-ID for automatic payment matching)
    kid_prefix = Column(String(20), nullable=True)  # Base for generating KID numbers
    use_kid = Column(Boolean, default=False, nullable=False)  # Whether to use KID
    
    # Credit management
    credit_limit = Column(Integer, nullable=True)  # In NOK
    reminder_fee = Column(Integer, default=0, nullable=False)  # Standard reminder fee
    
    # === SYSTEM FIELDS ===
    status = Column(
        String(20),
        default="active",
        nullable=False,
        index=True
    )  # 'active' or 'inactive' - NO DELETION!
    
    notes = Column(Text, nullable=True)  # Internal notes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    created_by = Column(UUID(as_uuid=True), nullable=True)  # User ID
    updated_by = Column(UUID(as_uuid=True), nullable=True)  # User ID
    
    # Relationships
    client = relationship("Client")
    audit_logs = relationship(
        "CustomerAuditLog",
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'customer_number', name='uq_client_customer_number'),
        UniqueConstraint('client_id', 'org_number', name='uq_client_customer_org_number'),
        UniqueConstraint('client_id', 'birth_number', name='uq_client_customer_birth_number'),
        CheckConstraint("status IN ('active', 'inactive')", name='ck_customer_status'),
    )
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', org={self.org_number})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "customer_number": self.customer_number,
            "is_company": self.is_company,
            "name": self.name,
            "org_number": self.org_number,
            "birth_number": self.birth_number,
            # Address
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "postal_code": self.postal_code,
                "city": self.city,
                "country": self.country,
            },
            # Contact
            "contact": {
                "person": self.contact_person,
                "phone": self.phone,
                "email": self.email,
            },
            # Financial
            "financial": {
                "payment_terms_days": self.payment_terms_days,
                "currency": self.currency,
                "vat_code": self.vat_code,
                "default_revenue_account": self.default_revenue_account,
                "kid_prefix": self.kid_prefix,
                "use_kid": self.use_kid,
                "credit_limit": self.credit_limit,
                "reminder_fee": self.reminder_fee,
            },
            # System
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_by": str(self.updated_by) if self.updated_by else None,
        }


class CustomerAuditLog(Base):
    """
    Audit trail for all customer changes.
    Every create, update, deactivation is logged here.
    """
    __tablename__ = "customer_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    action = Column(String(50), nullable=False)  # 'create', 'update', 'deactivate', 'reactivate'
    changed_fields = Column(Text, nullable=True)  # JSON string of changed fields
    old_values = Column(Text, nullable=True)  # JSON string of old values
    new_values = Column(Text, nullable=True)  # JSON string of new values
    
    performed_by = Column(UUID(as_uuid=True), nullable=True)  # User ID
    performed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<CustomerAuditLog(id={self.id}, action='{self.action}', customer_id={self.customer_id})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "customer_id": str(self.customer_id),
            "action": self.action,
            "changed_fields": self.changed_fields,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "performed_by": str(self.performed_by) if self.performed_by else None,
            "performed_at": self.performed_at.isoformat(),
            "ip_address": self.ip_address,
        }
