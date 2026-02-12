"""
Opening Balance Schemas - Pydantic models for API validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, datetime
import uuid


# ============================================================================
# Request Models
# ============================================================================

class OpeningBalanceLineImport(BaseModel):
    """Single line from import file"""
    account_number: str = Field(..., min_length=4, max_length=10, description="Account number")
    account_name: str = Field(..., min_length=1, max_length=255, description="Account name")
    debit: Decimal = Field(Decimal("0.00"), ge=0, description="Debit amount")
    credit: Decimal = Field(Decimal("0.00"), ge=0, description="Credit amount")
    
    @validator('debit', 'credit')
    def validate_amounts(cls, v, values):
        """Ensure at least one amount is provided"""
        if 'debit' in values:
            debit = values.get('debit', Decimal("0"))
            credit = v if 'credit' not in values else values.get('credit', Decimal("0"))
            
            if debit == 0 and credit == 0:
                raise ValueError("Line must have either debit or credit amount")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_number": "1920",
                "account_name": "Bank Account",
                "debit": "50000.00",
                "credit": "0.00"
            }
        }


class OpeningBalanceImportRequest(BaseModel):
    """Request to import opening balance"""
    client_id: uuid.UUID = Field(..., description="Client ID")
    import_date: date = Field(..., description="Opening balance date (typically 01.01.YYYY)")
    fiscal_year: str = Field(..., min_length=4, max_length=4, description="Fiscal year (YYYY)")
    description: str = Field("Åpningsbalanse", max_length=500, description="Description")
    lines: List[OpeningBalanceLineImport] = Field(..., min_items=1, description="Account lines")
    
    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "b3776033-40e5-42e2-ab7b-b1df97062d0c",
                "import_date": "2024-01-01",
                "fiscal_year": "2024",
                "description": "Åpningsbalanse 2024",
                "lines": [
                    {"account_number": "1920", "account_name": "Bank", "debit": "50000.00", "credit": "0.00"},
                    {"account_number": "2000", "account_name": "Egenkapital", "debit": "0.00", "credit": "50000.00"}
                ]
            }
        }


class BankBalanceVerification(BaseModel):
    """Manual bank balance verification"""
    account_number: str = Field(..., description="Bank account number (1920, 1921, etc.)")
    actual_balance: Decimal = Field(..., description="Actual balance from bank statement")


class OpeningBalanceValidateRequest(BaseModel):
    """Request to validate opening balance"""
    opening_balance_id: uuid.UUID = Field(..., description="Opening balance ID to validate")
    bank_balances: Optional[List[BankBalanceVerification]] = Field(
        None,
        description="Manual bank balance verification (if no bank connection)"
    )


# ============================================================================
# Response Models
# ============================================================================

class ValidationError(BaseModel):
    """Single validation error"""
    severity: str = Field(..., description="error/warning")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable message")
    account_number: Optional[str] = Field(None, description="Related account")
    amount: Optional[Decimal] = Field(None, description="Related amount")


class OpeningBalanceLineResponse(BaseModel):
    """Opening balance line in response"""
    id: uuid.UUID
    line_number: int
    account_number: str
    account_name: str
    debit_amount: Decimal
    credit_amount: Decimal
    account_exists: bool
    is_bank_account: bool
    bank_balance_match: Optional[bool]
    expected_bank_balance: Optional[Decimal]
    validation_errors: Optional[List[Dict[str, Any]]]
    
    class Config:
        from_attributes = True


class OpeningBalanceResponse(BaseModel):
    """Opening balance response"""
    id: uuid.UUID
    client_id: uuid.UUID
    import_date: date
    fiscal_year: str
    description: str
    status: str
    
    # Validation status
    is_balanced: bool
    balance_difference: Decimal
    bank_balance_verified: bool
    
    # Totals
    total_debit: Decimal
    total_credit: Decimal
    line_count: int
    
    # Lines (optional - included in preview/detail)
    lines: Optional[List[OpeningBalanceLineResponse]] = None
    
    # Validation results
    validation_errors: Optional[List[Dict[str, Any]]] = None
    bank_balance_errors: Optional[List[Dict[str, Any]]] = None
    missing_accounts: Optional[List[str]] = None
    
    # Metadata
    original_filename: Optional[str]
    created_at: datetime
    imported_at: Optional[datetime]
    journal_entry_id: Optional[uuid.UUID]
    
    class Config:
        from_attributes = True


class OpeningBalancePreviewResponse(BaseModel):
    """Preview of opening balance before import"""
    opening_balance: OpeningBalanceResponse
    validation_summary: Dict[str, Any] = Field(
        ...,
        description="Summary of validation results"
    )
    can_import: bool = Field(..., description="Whether import is allowed")
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "opening_balance": {
                    "id": "...",
                    "client_id": "...",
                    "status": "valid",
                    "is_balanced": True,
                    "balance_difference": "0.00",
                    "total_debit": "150000.00",
                    "total_credit": "150000.00"
                },
                "validation_summary": {
                    "balance_check": "passed",
                    "bank_accounts_check": "passed",
                    "missing_accounts_count": 0
                },
                "can_import": True,
                "errors": [],
                "warnings": []
            }
        }


class OpeningBalanceImportResponse(BaseModel):
    """Response after successful import"""
    opening_balance_id: uuid.UUID
    journal_entry_id: uuid.UUID
    voucher_number: str
    message: str = Field(..., description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "opening_balance_id": "...",
                "journal_entry_id": "...",
                "voucher_number": "2024-0001",
                "message": "Opening balance successfully imported"
            }
        }
