"""
Pydantic schemas for Voucher (General Ledger) API
KONTALI SPRINT 1 - Task 2
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class VoucherLineCreate(BaseModel):
    """Voucher line (journal entry line)"""
    line_number: int = Field(ge=1, description="Line number within voucher")
    account_number: str = Field(min_length=4, max_length=10, description="Account number")
    account_name: str = Field(description="Account name from chart of accounts")
    line_description: str = Field(default="", description="Line description")
    debit_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Debit amount")
    credit_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Credit amount")
    vat_code: Optional[str] = Field(default=None, description="VAT code (3, 5, 0, etc.)")
    vat_amount: Optional[Decimal] = Field(default=None, ge=0, description="VAT amount")
    
    @validator('debit_amount', 'credit_amount', 'vat_amount', pre=True)
    def validate_decimal(cls, v):
        """Ensure decimals are properly formatted"""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v
    
    @validator('credit_amount')
    def validate_debit_or_credit(cls, v, values):
        """Ensure either debit OR credit is set, not both"""
        debit = values.get('debit_amount', Decimal("0.00"))
        if debit > 0 and v > 0:
            raise ValueError("Line cannot have both debit and credit amounts")
        if debit == 0 and v == 0:
            raise ValueError("Line must have either debit or credit amount")
        return v
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class VoucherCreate(BaseModel):
    """Request to create a new voucher"""
    client_id: UUID = Field(description="Client/tenant ID")
    voucher_series: str = Field(default="GENERAL", description="Voucher series (AP, AR, GENERAL, etc.)")
    entry_date: date = Field(description="Entry date (when created)")
    accounting_date: date = Field(description="Accounting date (when it should be posted)")
    period: str = Field(description="Accounting period (YYYY-MM)")
    fiscal_year: int = Field(ge=2000, le=2100, description="Fiscal year")
    description: str = Field(min_length=1, max_length=500, description="Voucher description")
    source_type: str = Field(default="vendor_invoice", description="Source type (vendor_invoice, manual, etc.)")
    lines: List[VoucherLineCreate] = Field(min_items=2, description="Voucher lines (min 2 for balance)")
    
    @validator('period')
    def validate_period_format(cls, v):
        """Validate period format YYYY-MM"""
        import re
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError("Period must be in format YYYY-MM")
        return v
    
    @validator('lines')
    def validate_lines_balance(cls, v):
        """Validate that lines balance (debit = credit)"""
        total_debit = sum(line.debit_amount for line in v)
        total_credit = sum(line.credit_amount for line in v)
        
        if abs(total_debit - total_credit) > Decimal("0.01"):
            raise ValueError(
                f"Voucher lines do not balance! "
                f"Debit: {total_debit}, Credit: {total_credit}"
            )
        
        return v
    
    class Config:
        from_attributes = True


class VoucherDTO(BaseModel):
    """Voucher response DTO"""
    id: str
    client_id: str
    voucher_number: str
    voucher_series: str
    entry_date: date
    accounting_date: date
    period: str
    fiscal_year: int
    description: str
    source_type: str
    source_id: Optional[str] = None
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    lines: List[VoucherLineCreate]
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class VoucherCreateRequest(BaseModel):
    """Request to create voucher from invoice"""
    tenant_id: UUID = Field(description="Tenant/client ID")
    user_id: str = Field(description="User or agent ID creating the voucher")
    accounting_date: Optional[date] = Field(default=None, description="Override accounting date")
    override_account: Optional[str] = Field(default=None, description="Manual account override")
    
    class Config:
        from_attributes = True


class VoucherCreateResponse(BaseModel):
    """Response after creating voucher"""
    success: bool
    voucher_id: Optional[str] = None
    voucher_number: Optional[str] = None
    total_debit: Optional[Decimal] = None
    total_credit: Optional[Decimal] = None
    is_balanced: Optional[bool] = None
    lines_count: Optional[int] = None
    message: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class VoucherListRequest(BaseModel):
    """Request parameters for listing vouchers"""
    client_id: UUID
    period: Optional[str] = Field(default=None, description="Filter by period (YYYY-MM)")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    
    class Config:
        from_attributes = True


class VoucherListResponse(BaseModel):
    """Response for voucher list"""
    items: List[VoucherDTO]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True
