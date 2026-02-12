"""
Client Settings model - FIRMAINNSTILLINGER
Company-specific configuration visible only in client view
"""
from sqlalchemy import (
    Column, String, Boolean, DateTime, JSON,
    ForeignKey, Integer, Date
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid

from app.database import Base


class ClientSettings(Base):
    """
    Client-specific settings (FIRMAINNSTILLINGER)
    
    This contains all company-specific configuration that should ONLY
    be visible in the client view, NOT in the multi-client list view.
    """
    __tablename__ = "client_settings"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key to Client (one-to-one relationship)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # ===== SECTION 1: COMPANY INFO =====
    company_name = Column(String(255), nullable=False)
    org_number = Column(String(20), nullable=False)
    address_street = Column(String(255), nullable=True)
    address_postal_code = Column(String(10), nullable=True)
    address_city = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    ceo_name = Column(String(255), nullable=True)
    chairman_name = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)  # Free text or NACE code
    nace_code = Column(String(10), nullable=True)  # Standard NACE classification
    accounting_year_start_month = Column(Integer, nullable=False, default=1)  # 1-12
    incorporation_date = Column(Date, nullable=True)
    legal_form = Column(String(20), nullable=False, default="AS")  # AS, ENK, NUF, etc.
    
    # ===== SECTION 2: ACCOUNTING SETTINGS =====
    chart_of_accounts = Column(String(50), nullable=False, default="NS4102")
    vat_registered = Column(Boolean, nullable=False, default=True)
    vat_period = Column(String(20), nullable=False, default="bimonthly")  # bimonthly/annual
    currency = Column(String(3), nullable=False, default="NOK")
    rounding_rules = Column(JSON, nullable=True)  # {"decimals": 2, "method": "standard"}
    
    # Multi-currency support
    supported_currencies = Column(JSON, nullable=False, default=list)  # ["NOK", "USD", "EUR"]
    auto_update_rates = Column(Boolean, nullable=False, default=True)
    last_rate_update = Column(DateTime, nullable=True)
    
    # ===== SECTION 3: BANK ACCOUNTS =====
    # JSON array of bank accounts with structure:
    # [
    #   {
    #     "bank_name": "DNB",
    #     "account_number": "12345678901",
    #     "ledger_account": "1920",
    #     "is_integrated": true,
    #     "integration_status": "active"
    #   }
    # ]
    bank_accounts = Column(JSON, nullable=False, default=list)
    
    # ===== SECTION 4: PAYROLL/EMPLOYEES =====
    has_employees = Column(Boolean, nullable=False, default=False)
    payroll_frequency = Column(String(20), nullable=True)  # monthly, bi-weekly, etc.
    employer_tax_zone = Column(String(20), nullable=True)  # Zone 1-5 in Norway
    
    # ===== SECTION 5: SERVICES =====
    # JSON structure for services provided:
    # {
    #   "bookkeeping": true,
    #   "payroll": false,
    #   "annual_accounts": true,
    #   "vat_reporting": true,
    #   "other": ["advisory", "budgeting"]
    # }
    services_provided = Column(JSON, nullable=False, default=dict)
    
    # Task templates (references to task template IDs or names)
    task_templates = Column(JSON, nullable=False, default=list)
    
    # ===== SECTION 6: RESPONSIBLE ACCOUNTANT =====
    responsible_accountant_name = Column(String(255), nullable=True)
    responsible_accountant_email = Column(String(255), nullable=True)
    responsible_accountant_phone = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("Client", back_populates="settings")
    
    def __repr__(self):
        return f"<ClientSettings(id={self.id}, client_id={self.client_id}, company_name='{self.company_name}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            # Company Info
            "company_info": {
                "company_name": self.company_name,
                "org_number": self.org_number,
                "address": {
                    "street": self.address_street,
                    "postal_code": self.address_postal_code,
                    "city": self.address_city,
                },
                "phone": self.phone,
                "email": self.email,
                "ceo_name": self.ceo_name,
                "chairman_name": self.chairman_name,
                "industry": self.industry,
                "nace_code": self.nace_code,
                "accounting_year_start_month": self.accounting_year_start_month,
                "incorporation_date": self.incorporation_date.isoformat() if self.incorporation_date else None,
                "legal_form": self.legal_form,
            },
            # Accounting Settings
            "accounting_settings": {
                "chart_of_accounts": self.chart_of_accounts,
                "vat_registered": self.vat_registered,
                "vat_period": self.vat_period,
                "currency": self.currency,
                "rounding_rules": self.rounding_rules or {"decimals": 2, "method": "standard"},
                "supported_currencies": self.supported_currencies or ["NOK"],
                "auto_update_rates": self.auto_update_rates,
                "last_rate_update": self.last_rate_update.isoformat() if self.last_rate_update else None,
            },
            # Bank Accounts
            "bank_accounts": self.bank_accounts or [],
            # Payroll/Employees
            "payroll_employees": {
                "has_employees": self.has_employees,
                "payroll_frequency": self.payroll_frequency,
                "employer_tax_zone": self.employer_tax_zone,
            },
            # Services
            "services": {
                "services_provided": self.services_provided or {},
                "task_templates": self.task_templates or [],
            },
            # Responsible Accountant
            "responsible_accountant": {
                "name": self.responsible_accountant_name,
                "email": self.responsible_accountant_email,
                "phone": self.responsible_accountant_phone,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
