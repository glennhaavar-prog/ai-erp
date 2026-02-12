"""
Client Settings Schemas - Pydantic models for API validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID


class AddressInfo(BaseModel):
    """Address information"""
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None


class CompanyInfo(BaseModel):
    """Company information section"""
    company_name: str = Field(..., max_length=255)
    org_number: str = Field(..., max_length=20, description="Organization number")
    address: Optional[AddressInfo] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    ceo_name: Optional[str] = None
    chairman_name: Optional[str] = None
    industry: Optional[str] = None
    nace_code: Optional[str] = None
    accounting_year_start_month: int = Field(default=1, ge=1, le=12)
    incorporation_date: Optional[date] = None
    legal_form: str = Field(default="AS", max_length=20, description="Legal form (AS, ENK, NUF, etc.)")


class AccountingSettings(BaseModel):
    """Accounting configuration section"""
    chart_of_accounts: str = Field(default="NS4102", description="Chart of accounts standard")
    vat_registered: bool = Field(default=True)
    vat_period: str = Field(default="bimonthly", max_length=20)
    currency: str = Field(default="NOK", max_length=3)
    rounding_rules: Optional[Dict[str, Any]] = Field(
        default={"decimals": 2, "method": "standard"},
        description="Rounding configuration"
    )


class BankAccount(BaseModel):
    """Single bank account configuration"""
    bank_name: str = Field(..., max_length=100, description="Bank name (e.g., DNB)")
    account_number: str = Field(..., max_length=20, description="Bank account number")
    ledger_account: str = Field(..., max_length=10, description="Ledger account (e.g., 1920)")
    is_integrated: bool = Field(default=False, description="Is bank integration active?")
    integration_status: Optional[str] = None


class PayrollEmployees(BaseModel):
    """Payroll and employee settings"""
    has_employees: bool = Field(default=False)
    payroll_frequency: Optional[str] = Field(None, max_length=20)
    employer_tax_zone: Optional[str] = Field(None, max_length=20, description="Norwegian tax zones")


class ServicesProvided(BaseModel):
    """Services provided to this client"""
    bookkeeping: bool = Field(default=True)
    payroll: bool = Field(default=False)
    annual_accounts: bool = Field(default=True)
    vat_reporting: bool = Field(default=True)
    other: List[str] = Field(default_factory=list, description="Additional services")


class Services(BaseModel):
    """Services section"""
    services_provided: ServicesProvided = Field(default_factory=ServicesProvided)
    task_templates: List[str] = Field(default_factory=list, description="Task template IDs/names")


class ResponsibleAccountant(BaseModel):
    """Responsible accountant information"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ClientSettingsBase(BaseModel):
    """Base client settings schema"""
    company_info: CompanyInfo
    accounting_settings: AccountingSettings = Field(default_factory=AccountingSettings)
    bank_accounts: List[BankAccount] = Field(default_factory=list)
    payroll_employees: PayrollEmployees = Field(default_factory=PayrollEmployees)
    services: Services = Field(default_factory=Services)
    responsible_accountant: Optional[ResponsibleAccountant] = None


class ClientSettingsCreate(ClientSettingsBase):
    """Schema for creating client settings"""
    client_id: UUID


class ClientSettingsUpdate(BaseModel):
    """Schema for updating client settings (all fields optional)"""
    company_info: Optional[CompanyInfo] = None
    accounting_settings: Optional[AccountingSettings] = None
    bank_accounts: Optional[List[BankAccount]] = None
    payroll_employees: Optional[PayrollEmployees] = None
    services: Optional[Services] = None
    responsible_accountant: Optional[ResponsibleAccountant] = None


class ClientSettingsResponse(ClientSettingsBase):
    """Schema for client settings response"""
    id: UUID
    client_id: UUID
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


def create_default_settings(client_id: UUID, company_name: str, org_number: str) -> Dict[str, Any]:
    """
    Create default settings for a new client
    
    Args:
        client_id: Client UUID
        company_name: Company name
        org_number: Organization number
        
    Returns:
        Dictionary with default settings structure
    """
    return {
        "client_id": client_id,
        "company_name": company_name,
        "org_number": org_number,
        "accounting_year_start_month": 1,
        "legal_form": "AS",
        "chart_of_accounts": "NS4102",
        "vat_registered": True,
        "vat_period": "bimonthly",
        "currency": "NOK",
        "rounding_rules": {"decimals": 2, "method": "standard"},
        "bank_accounts": [],
        "has_employees": False,
        "services_provided": {
            "bookkeeping": True,
            "payroll": False,
            "annual_accounts": True,
            "vat_reporting": True,
            "other": []
        },
        "task_templates": [],
    }
