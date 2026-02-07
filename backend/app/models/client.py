"""
Client model - Klienter under hvert regnskapsbyrå
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, JSON,
    ForeignKey, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class AutomationLevel(str, enum.Enum):
    """AI automation level for client"""
    FULL = "full"          # AI auto-books everything above threshold
    ASSISTED = "assisted"   # AI suggests, human approves
    MANUAL = "manual"       # AI disabled, manual only


class Client(Base):
    """
    Client = Kunde under regnskapsbyrå
    
    Each client is a separate company with their own:
    - Chart of accounts
    - Vendors
    - General ledger
    - AI settings
    """
    __tablename__ = "clients"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Client Information
    client_number = Column(String(50), nullable=False)  # Sequential per tenant
    name = Column(String(255), nullable=False, index=True)
    org_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Integrations
    ehf_endpoint = Column(String(255), nullable=True)  # Pepol access point
    active_banks = Column(JSON, default=list)  # Array of connected banks
    altinn_api_access = Column(Boolean, default=False)
    
    # Fiscal Setup
    fiscal_year_start = Column(Integer, default=1)  # Month (1=January)
    accounting_method = Column(String(20), default="accrual")  # accrual/cash
    vat_term = Column(String(20), default="bimonthly")  # monthly/bimonthly/annual
    base_currency = Column(String(3), default="NOK")
    
    # AI Agent Settings
    ai_automation_level = Column(
        SQLEnum(AutomationLevel),
        default=AutomationLevel.ASSISTED,
        nullable=False
    )
    ai_confidence_threshold = Column(Integer, default=85)  # 0-100
    
    # Status
    status = Column(String(20), default="active")  # active/inactive/suspended
    
    # Demo Environment Flag
    is_demo = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    tenant = relationship("Tenant", back_populates="clients")
    vendors = relationship("Vendor", back_populates="client", cascade="all, delete-orphan")
    chart_of_accounts = relationship("Account", back_populates="client", cascade="all, delete-orphan")
    vendor_invoices = relationship("VendorInvoice", back_populates="client")
    customer_invoices = relationship("CustomerInvoice", back_populates="client", cascade="all, delete-orphan")
    bank_transactions = relationship("BankTransaction", back_populates="client", cascade="all, delete-orphan")
    general_ledger_entries = relationship("GeneralLedger", back_populates="client")
    voucher_series = relationship("VoucherSeries", back_populates="client", cascade="all, delete-orphan")
    fiscal_years = relationship("FiscalYear", back_populates="client", cascade="all, delete-orphan")
    accruals = relationship("Accrual", back_populates="client", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'client_number', name='uq_tenant_client_number'),
    )
    
    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "client_number": self.client_number,
            "name": self.name,
            "org_number": self.org_number,
            "base_currency": self.base_currency,
            "ai_automation_level": self.ai_automation_level.value,
            "ai_confidence_threshold": self.ai_confidence_threshold,
            "status": self.status,
            "is_demo": self.is_demo,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
