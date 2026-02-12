"""
Client schemas for API validation
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class ClientCreateSchema(BaseModel):
    """Schema for creating a new client"""
    name: str = Field(..., min_length=1, max_length=255, description="Client company name")
    org_number: str = Field(..., pattern=r"^\d{9}$", description="Norwegian org number (9 digits)")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    start_date: str = Field(..., description="Accounting start date (YYYY-MM-DD)")
    address: Optional[str] = Field(None, max_length=500, description="Company address")
    contact_person: Optional[str] = Field(None, max_length=200, description="Contact person name")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    fiscal_year_start: str = Field("01-01", pattern=r"^\d{2}-\d{2}$", description="Fiscal year start (MM-DD)")
    vat_registered: bool = Field(True, description="VAT registered")
    
    @field_validator('org_number')
    @classmethod
    def validate_org_number(cls, v: str) -> str:
        """Validate Norwegian org number"""
        if not v.isdigit() or len(v) != 9:
            raise ValueError("Org number must be exactly 9 digits")
        return v
    
    @field_validator('fiscal_year_start')
    @classmethod
    def validate_fiscal_year(cls, v: str) -> str:
        """Validate fiscal year format (MM-DD)"""
        try:
            month, day = v.split('-')
            if not (1 <= int(month) <= 12 and 1 <= int(day) <= 31):
                raise ValueError("Invalid month or day")
        except (ValueError, AttributeError):
            raise ValueError("Fiscal year start must be in format MM-DD (e.g., 01-01)")
        return v


class ClientUpdateSchema(BaseModel):
    """Schema for updating client details"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[EmailStr] = None
    fiscal_year_start: Optional[str] = Field(None, pattern=r"^\d{2}-\d{2}$")
    vat_registered: Optional[bool] = None
    status: Optional[str] = Field(None, pattern=r"^(active|inactive|suspended)$")


class ClientResponse(BaseModel):
    """Schema for client response"""
    id: str
    name: str
    org_number: str
    industry: Optional[str] = None
    start_date: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    fiscal_year_start: str
    vat_registered: bool
    status: str
    is_demo: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
