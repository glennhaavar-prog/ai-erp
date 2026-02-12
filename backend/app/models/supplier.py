"""
Supplier Contact Register - Leverandørkort (KONTAKTREGISTER)

Master data for suppliers. The ledger references this.
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


class Supplier(Base):
    """
    Supplier Contact Card = Leverandørkort
    
    Master data for suppliers. This is the authoritative source.
    Supplier ledger entries reference this table.
    
    Rules:
    - No deletion allowed (only deactivation via status='inactive')
    - Unique org_number per client (if provided)
    - All changes logged in audit trail
    """
    __tablename__ = "suppliers"
    
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
    supplier_number = Column(String(50), nullable=False)  # Sequential per client
    company_name = Column(String(255), nullable=False, index=True)
    org_number = Column(String(20), nullable=True, index=True)  # Organizational number
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="Norge", nullable=False)
    
    # Contact
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    # === FINANCIAL INFORMATION ===
    # Banking
    bank_account = Column(String(50), nullable=True)
    iban = Column(String(50), nullable=True)
    swift_bic = Column(String(20), nullable=True)
    
    # Payment terms
    payment_terms_days = Column(Integer, default=30, nullable=False)  # Days until due
    
    # Accounting defaults
    currency = Column(String(3), default="NOK", nullable=False)
    vat_code = Column(String(10), nullable=True)  # Default VAT code
    default_expense_account = Column(String(10), nullable=True)  # Default account number
    
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
        "SupplierAuditLog",
        back_populates="supplier",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'supplier_number', name='uq_client_supplier_number'),
        UniqueConstraint('client_id', 'org_number', name='uq_client_supplier_org_number'),
        CheckConstraint("status IN ('active', 'inactive')", name='ck_supplier_status'),
    )
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.company_name}', org={self.org_number})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "supplier_number": self.supplier_number,
            "company_name": self.company_name,
            "org_number": self.org_number,
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
                "website": self.website,
            },
            # Financial
            "financial": {
                "bank_account": self.bank_account,
                "iban": self.iban,
                "swift_bic": self.swift_bic,
                "payment_terms_days": self.payment_terms_days,
                "currency": self.currency,
                "vat_code": self.vat_code,
                "default_expense_account": self.default_expense_account,
            },
            # System
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_by": str(self.updated_by) if self.updated_by else None,
        }


class SupplierAuditLog(Base):
    """
    Audit trail for all supplier changes.
    Every create, update, deactivation is logged here.
    """
    __tablename__ = "supplier_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
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
    supplier = relationship("Supplier", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<SupplierAuditLog(id={self.id}, action='{self.action}', supplier_id={self.supplier_id})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "supplier_id": str(self.supplier_id),
            "action": self.action,
            "changed_fields": self.changed_fields,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "performed_by": str(self.performed_by) if self.performed_by else None,
            "performed_at": self.performed_at.isoformat(),
            "ip_address": self.ip_address,
        }
