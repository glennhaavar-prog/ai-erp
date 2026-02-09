"""
Journal Entries API - Bokføringsgrensesnitt

Production-grade API for creating and managing journal entries (bilag).
Enforces double-entry bookkeeping: SUM(debits) = SUM(credits)
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime
import uuid

from app.database import get_db
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.client import Client

router = APIRouter(prefix="/api/journal-entries", tags=["Journal Entries"])


# ============================================================================
# Request/Response Models
# ============================================================================

class JournalLineCreate(BaseModel):
    """Single line in a journal entry (one account movement)"""
    account_number: str = Field(..., min_length=4, max_length=10, description="Account number from chart of accounts")
    debit_amount: Decimal = Field(Decimal("0.00"), ge=0, description="Debit amount (if debit)")
    credit_amount: Decimal = Field(Decimal("0.00"), ge=0, description="Credit amount (if credit)")
    vat_code: Optional[str] = Field(None, description="VAT code (5=25%, 3=15%, etc)")
    vat_amount: Decimal = Field(Decimal("0.00"), description="VAT amount")
    line_description: Optional[str] = Field(None, description="Line description")
    
    @validator('debit_amount', 'credit_amount')
    def validate_debit_or_credit(cls, v, values):
        """Ensure either debit OR credit, not both"""
        if 'debit_amount' in values:
            debit = values.get('debit_amount', Decimal("0"))
            credit = v if 'credit_amount' not in values else values.get('credit_amount', Decimal("0"))
            
            if debit > 0 and credit > 0:
                raise ValueError("Line cannot have both debit and credit")
            if debit == 0 and credit == 0:
                raise ValueError("Line must have either debit or credit")
        
        return v


class JournalEntryCreate(BaseModel):
    """Create a new journal entry (bilag)"""
    client_id: uuid.UUID = Field(..., description="Client ID")
    accounting_date: date = Field(..., description="Accounting date (bokføringsdato)")
    voucher_series: str = Field("A", max_length=10, description="Voucher series (A/B/C)")
    description: str = Field(..., min_length=1, max_length=500, description="Entry description")
    source_type: str = Field("manual", description="Source type (manual/ai_agent/ehf_invoice etc)")
    lines: List[JournalLineCreate] = Field(..., min_items=2, description="Journal lines (min 2)")
    
    @validator('lines')
    def validate_balance(cls, lines):
        """Enforce double-entry bookkeeping: SUM(debits) = SUM(credits)"""
        total_debit = sum(line.debit_amount for line in lines)
        total_credit = sum(line.credit_amount for line in lines)
        
        if total_debit != total_credit:
            raise ValueError(
                f"Entry does not balance: debits={total_debit}, credits={total_credit}. "
                f"Difference: {abs(total_debit - total_credit)}"
            )
        
        if total_debit == 0:
            raise ValueError("Entry total cannot be zero")
        
        return lines


class JournalLineResponse(BaseModel):
    """Journal line in response"""
    id: uuid.UUID
    line_number: int
    account_number: str
    debit_amount: Decimal
    credit_amount: Decimal
    vat_code: Optional[str]
    vat_amount: Decimal
    line_description: Optional[str]
    
    class Config:
        from_attributes = True


class JournalEntryResponse(BaseModel):
    """Journal entry response"""
    id: uuid.UUID
    client_id: uuid.UUID
    voucher_number: str
    voucher_series: str
    accounting_date: date
    period: str
    fiscal_year: int
    description: str
    source_type: str
    status: str
    created_at: datetime
    lines: List[JournalLineResponse]
    
    # Calculated fields
    total_debit: Decimal
    total_credit: Decimal
    
    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    entry: JournalEntryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new journal entry (bokfør bilag)
    
    - Validates double-entry bookkeeping (debit = credit)
    - Auto-generates voucher number
    - Creates immutable ledger entry
    - Returns complete entry with all lines
    """
    # Verify client exists
    result = await db.execute(
        select(Client).where(Client.id == entry.client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {entry.client_id} not found"
        )
    
    # Generate voucher number (simple incrementing for now)
    # TODO: Use proper voucher series management
    result = await db.execute(
        select(GeneralLedger)
        .where(
            and_(
                GeneralLedger.client_id == entry.client_id,
                GeneralLedger.voucher_series == entry.voucher_series
            )
        )
        .order_by(GeneralLedger.voucher_number.desc())
    )
    last_entry = result.scalar_one_or_none()
    
    if last_entry:
        try:
            last_number = int(last_entry.voucher_number.split('-')[-1])
            voucher_number = f"{entry.accounting_date.year}-{last_number + 1:04d}"
        except (ValueError, IndexError):
            voucher_number = f"{entry.accounting_date.year}-0001"
    else:
        voucher_number = f"{entry.accounting_date.year}-0001"
    
    # Create general ledger entry
    gl_entry = GeneralLedger(
        id=uuid.uuid4(),
        client_id=entry.client_id,
        entry_date=date.today(),
        accounting_date=entry.accounting_date,
        period=entry.accounting_date.strftime("%Y-%m"),
        fiscal_year=entry.accounting_date.year,
        voucher_number=voucher_number,
        voucher_series=entry.voucher_series,
        description=entry.description,
        source_type=entry.source_type,
        created_by_type="user",  # TODO: Get from auth context
        status="posted",
        locked=False,
    )
    
    db.add(gl_entry)
    
    # Create lines
    gl_lines = []
    for idx, line_data in enumerate(entry.lines, start=1):
        gl_line = GeneralLedgerLine(
            id=uuid.uuid4(),
            general_ledger_id=gl_entry.id,
            line_number=idx,
            account_number=line_data.account_number,
            debit_amount=line_data.debit_amount,
            credit_amount=line_data.credit_amount,
            vat_code=line_data.vat_code,
            vat_amount=line_data.vat_amount,
            line_description=line_data.line_description,
        )
        db.add(gl_line)
        gl_lines.append(gl_line)
    
    # Commit transaction
    await db.commit()
    await db.refresh(gl_entry)
    
    # Reload with lines
    result = await db.execute(
        select(GeneralLedger)
        .where(GeneralLedger.id == gl_entry.id)
    )
    gl_entry = result.scalar_one()
    
    result = await db.execute(
        select(GeneralLedgerLine)
        .where(GeneralLedgerLine.general_ledger_id == gl_entry.id)
        .order_by(GeneralLedgerLine.line_number)
    )
    gl_lines = result.scalars().all()
    
    # Calculate totals
    total_debit = sum(line.debit_amount for line in gl_lines)
    total_credit = sum(line.credit_amount for line in gl_lines)
    
    # Build response
    response_lines = [
        JournalLineResponse(
            id=line.id,
            line_number=line.line_number,
            account_number=line.account_number,
            debit_amount=line.debit_amount,
            credit_amount=line.credit_amount,
            vat_code=line.vat_code,
            vat_amount=line.vat_amount,
            line_description=line.line_description,
        )
        for line in gl_lines
    ]
    
    return JournalEntryResponse(
        id=gl_entry.id,
        client_id=gl_entry.client_id,
        voucher_number=gl_entry.voucher_number,
        voucher_series=gl_entry.voucher_series,
        accounting_date=gl_entry.accounting_date,
        period=gl_entry.period,
        fiscal_year=gl_entry.fiscal_year,
        description=gl_entry.description,
        source_type=gl_entry.source_type,
        status=gl_entry.status,
        created_at=gl_entry.created_at,
        lines=response_lines,
        total_debit=total_debit,
        total_credit=total_credit,
    )


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a journal entry by ID
    
    Returns complete entry with all lines
    """
    # Get entry
    result = await db.execute(
        select(GeneralLedger).where(GeneralLedger.id == entry_id)
    )
    gl_entry = result.scalar_one_or_none()
    
    if not gl_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )
    
    # Get lines
    result = await db.execute(
        select(GeneralLedgerLine)
        .where(GeneralLedgerLine.general_ledger_id == entry_id)
        .order_by(GeneralLedgerLine.line_number)
    )
    gl_lines = result.scalars().all()
    
    # Calculate totals
    total_debit = sum(line.debit_amount for line in gl_lines)
    total_credit = sum(line.credit_amount for line in gl_lines)
    
    # Build response
    response_lines = [
        JournalLineResponse(
            id=line.id,
            line_number=line.line_number,
            account_number=line.account_number,
            debit_amount=line.debit_amount,
            credit_amount=line.credit_amount,
            vat_code=line.vat_code,
            vat_amount=line.vat_amount,
            line_description=line.line_description,
        )
        for line in gl_lines
    ]
    
    return JournalEntryResponse(
        id=gl_entry.id,
        client_id=gl_entry.client_id,
        voucher_number=gl_entry.voucher_number,
        voucher_series=gl_entry.voucher_series,
        accounting_date=gl_entry.accounting_date,
        period=gl_entry.period,
        fiscal_year=gl_entry.fiscal_year,
        description=gl_entry.description,
        source_type=gl_entry.source_type,
        status=gl_entry.status,
        created_at=gl_entry.created_at,
        lines=response_lines,
        total_debit=total_debit,
        total_credit=total_credit,
    )
