"""
Reconciliations API - Balansekontoavstemming
"""
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, extract
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid
import os
import shutil
from pathlib import Path
from pydantic import BaseModel, Field
from decimal import Decimal

from app.database import get_db
from app.models.reconciliation import (
    Reconciliation, 
    ReconciliationAttachment,
    ReconciliationStatus,
    ReconciliationType
)
from app.models.general_ledger import GeneralLedger
from app.models.chart_of_accounts import Account
from app.utils.audit import log_audit_event

router = APIRouter(prefix="/api/reconciliations", tags=["Reconciliations"])

# Upload configuration
UPLOAD_DIR = Path("/home/ubuntu/.openclaw/workspace/ai-erp/backend/uploads/reconciliations")
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# Pydantic models for request/response
class ReconciliationCreate(BaseModel):
    client_id: UUID = Field(..., description="Client ID")
    account_id: UUID = Field(..., description="Account ID to reconcile")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")
    reconciliation_type: str = Field(..., description="Type: bank/receivables/payables/inventory/other")
    notes: Optional[str] = Field(None, description="Notes about this reconciliation")


class ReconciliationUpdate(BaseModel):
    expected_balance: Optional[Decimal] = Field(None, description="Expected balance (manual input)")
    notes: Optional[str] = Field(None, description="Notes about this reconciliation")


class ReconciliationResponse(BaseModel):
    id: str
    client_id: str
    account_id: str
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    period_start: str
    period_end: str
    opening_balance: float
    closing_balance: float
    expected_balance: Optional[float]
    difference: Optional[float]
    status: str
    reconciliation_type: str
    notes: Optional[str]
    created_at: str
    reconciled_at: Optional[str]
    reconciled_by: Optional[str]
    approved_at: Optional[str]
    approved_by: Optional[str]
    attachments_count: Optional[int] = None


class AttachmentResponse(BaseModel):
    id: str
    reconciliation_id: str
    file_name: str
    file_path: str
    file_type: Optional[str]
    file_size: Optional[int]
    uploaded_at: str
    uploaded_by: Optional[str]


async def calculate_balance(
    db: AsyncSession,
    client_id: UUID,
    account_id: UUID,
    start_date: datetime,
    end_date: datetime
) -> tuple[Decimal, Decimal]:
    """
    Calculate opening and closing balance for an account in a period
    
    Returns: (opening_balance, closing_balance)
    """
    from app.models.general_ledger import GeneralLedgerLine
    
    # Get opening balance (before start_date)
    # Sum: debit_amount - credit_amount for all lines on this account
    opening_query = select(
        func.sum(GeneralLedgerLine.debit_amount - GeneralLedgerLine.credit_amount)
    ).select_from(GeneralLedgerLine).join(
        GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id
    ).join(
        Account, GeneralLedgerLine.account_number == Account.account_number
    ).where(
        and_(
            GeneralLedger.client_id == client_id,
            Account.id == account_id,
            GeneralLedger.accounting_date < start_date
        )
    )
    opening_result = await db.execute(opening_query)
    opening_balance = opening_result.scalar() or Decimal("0.00")
    
    # Get closing balance (up to end_date)
    closing_query = select(
        func.sum(GeneralLedgerLine.debit_amount - GeneralLedgerLine.credit_amount)
    ).select_from(GeneralLedgerLine).join(
        GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id
    ).join(
        Account, GeneralLedgerLine.account_number == Account.account_number
    ).where(
        and_(
            GeneralLedger.client_id == client_id,
            Account.id == account_id,
            GeneralLedger.accounting_date <= end_date
        )
    )
    closing_result = await db.execute(closing_query)
    closing_balance = closing_result.scalar() or Decimal("0.00")
    
    return opening_balance, closing_balance


@router.get("/")
async def list_reconciliations(
    client_id: UUID = Query(..., description="Client ID to filter reconciliations"),
    period: Optional[str] = Query(None, description="Period filter (YYYY-MM format)"),
    status: Optional[str] = Query(None, description="Status filter: pending/reconciled/approved"),
    type: Optional[str] = Query(None, description="Type filter: bank/receivables/payables/inventory/other"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all reconciliations for a client with optional filters
    
    Returns list of reconciliations with account details
    """
    # Build query
    query = select(Reconciliation).where(Reconciliation.client_id == client_id)
    
    # Apply filters
    if status:
        try:
            status_enum = ReconciliationStatus(status)
            query = query.where(Reconciliation.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    if type:
        try:
            type_enum = ReconciliationType(type)
            query = query.where(Reconciliation.reconciliation_type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid type: {type}")
    
    if period:
        try:
            # Parse YYYY-MM format
            year, month = period.split("-")
            query = query.where(
                and_(
                    extract('year', Reconciliation.period_start) == int(year),
                    extract('month', Reconciliation.period_start) == int(month)
                )
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid period format. Use YYYY-MM")
    
    # Sort by period_start descending
    query = query.order_by(Reconciliation.period_start.desc())
    
    # Execute
    result = await db.execute(query)
    reconciliations = result.scalars().all()
    
    # Get account details for each reconciliation
    reconciliations_list = []
    for recon in reconciliations:
        # Get account details
        account_query = select(Account).where(Account.id == recon.account_id)
        account_result = await db.execute(account_query)
        account = account_result.scalar_one_or_none()
        
        # Count attachments
        attachments_query = select(func.count(ReconciliationAttachment.id)).where(
            ReconciliationAttachment.reconciliation_id == recon.id
        )
        attachments_result = await db.execute(attachments_query)
        attachments_count = attachments_result.scalar() or 0
        
        recon_dict = recon.to_dict()
        recon_dict["account_number"] = account.account_number if account else None
        recon_dict["account_name"] = account.account_name if account else None
        recon_dict["attachments_count"] = attachments_count
        reconciliations_list.append(recon_dict)
    
    return {
        "reconciliations": reconciliations_list,
        "count": len(reconciliations_list)
    }


@router.get("/{reconciliation_id}")
async def get_reconciliation(
    reconciliation_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ReconciliationResponse:
    """
    Get a single reconciliation with full details and attachments
    """
    # Get reconciliation
    query = select(Reconciliation).where(Reconciliation.id == reconciliation_id)
    result = await db.execute(query)
    reconciliation = result.scalar_one_or_none()
    
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    # Get account details
    account_query = select(Account).where(Account.id == reconciliation.account_id)
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()
    
    # Count attachments
    attachments_query = select(func.count(ReconciliationAttachment.id)).where(
        ReconciliationAttachment.reconciliation_id == reconciliation.id
    )
    attachments_result = await db.execute(attachments_query)
    attachments_count = attachments_result.scalar() or 0
    
    recon_dict = reconciliation.to_dict()
    recon_dict["account_number"] = account.account_number if account else None
    recon_dict["account_name"] = account.account_name if account else None
    recon_dict["attachments_count"] = attachments_count
    
    return ReconciliationResponse(**recon_dict)


@router.post("/")
async def create_reconciliation(
    data: ReconciliationCreate,
    db: AsyncSession = Depends(get_db)
) -> ReconciliationResponse:
    """
    Create a new reconciliation
    
    Auto-calculates opening_balance and closing_balance from ledger
    """
    # Validate reconciliation_type
    try:
        type_enum = ReconciliationType(data.reconciliation_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid reconciliation_type: {data.reconciliation_type}")
    
    # Verify account exists
    account_query = select(Account).where(Account.id == data.account_id)
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Strip timezone from datetime inputs (database expects naive datetime)
    period_start_naive = data.period_start.replace(tzinfo=None) if data.period_start.tzinfo else data.period_start
    period_end_naive = data.period_end.replace(tzinfo=None) if data.period_end.tzinfo else data.period_end
    
    # Calculate balances from ledger
    opening_balance, closing_balance = await calculate_balance(
        db,
        data.client_id,
        data.account_id,
        period_start_naive,
        period_end_naive
    )
    
    # Create reconciliation
    reconciliation = Reconciliation(
        id=uuid.uuid4(),
        client_id=data.client_id,
        account_id=data.account_id,
        period_start=period_start_naive,
        period_end=period_end_naive,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        reconciliation_type=type_enum,
        notes=data.notes,
        status=ReconciliationStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    db.add(reconciliation)
    await db.commit()
    await db.refresh(reconciliation)
    
    # Return with account details
    recon_dict = reconciliation.to_dict()
    recon_dict["account_number"] = account.account_number
    recon_dict["account_name"] = account.account_name
    recon_dict["attachments_count"] = 0
    
    return ReconciliationResponse(**recon_dict)


@router.put("/{reconciliation_id}")
async def update_reconciliation(
    reconciliation_id: UUID,
    data: ReconciliationUpdate,
    db: AsyncSession = Depends(get_db)
) -> ReconciliationResponse:
    """
    Update a reconciliation (expected_balance and notes)
    
    Auto-recalculates difference
    """
    # Get reconciliation
    query = select(Reconciliation).where(Reconciliation.id == reconciliation_id)
    result = await db.execute(query)
    reconciliation = result.scalar_one_or_none()
    
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    # Update fields
    if data.expected_balance is not None:
        reconciliation.expected_balance = data.expected_balance
        # Auto-calculate difference
        reconciliation.difference = reconciliation.closing_balance - data.expected_balance
        
        # Update status based on difference
        if reconciliation.difference == 0:
            reconciliation.status = ReconciliationStatus.RECONCILED
            reconciliation.reconciled_at = datetime.utcnow()
    
    if data.notes is not None:
        reconciliation.notes = data.notes
    
    await db.commit()
    await db.refresh(reconciliation)
    
    # Get account details
    account_query = select(Account).where(Account.id == reconciliation.account_id)
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()
    
    # Count attachments
    attachments_query = select(func.count(ReconciliationAttachment.id)).where(
        ReconciliationAttachment.reconciliation_id == reconciliation.id
    )
    attachments_result = await db.execute(attachments_query)
    attachments_count = attachments_result.scalar() or 0
    
    recon_dict = reconciliation.to_dict()
    recon_dict["account_number"] = account.account_number if account else None
    recon_dict["account_name"] = account.account_name if account else None
    recon_dict["attachments_count"] = attachments_count
    
    return ReconciliationResponse(**recon_dict)


@router.post("/{reconciliation_id}/approve")
async def approve_reconciliation(
    reconciliation_id: UUID,
    user_id: UUID = Query(..., description="User ID performing the approval"),
    db: AsyncSession = Depends(get_db)
) -> ReconciliationResponse:
    """
    Mark reconciliation as approved
    
    Sets approved_at and approved_by
    """
    # Get reconciliation
    query = select(Reconciliation).where(Reconciliation.id == reconciliation_id)
    result = await db.execute(query)
    reconciliation = result.scalar_one_or_none()
    
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    # Check if already approved
    if reconciliation.status == ReconciliationStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Reconciliation already approved")
    
    # Update status
    reconciliation.status = ReconciliationStatus.APPROVED
    reconciliation.approved_at = datetime.utcnow()
    reconciliation.approved_by = user_id
    
    await db.commit()
    await db.refresh(reconciliation)
    
    # Log audit event
    await log_audit_event(
        db=db,
        voucher_id=reconciliation.id,
        voucher_type="balance_recon",
        action="approved",
        performed_by="accountant",
        user_id=user_id,
        ai_confidence=None,
        details={
            "account_id": str(reconciliation.account_id),
            "reconciliation_type": reconciliation.reconciliation_type.value,
            "period_start": reconciliation.period_start.isoformat() if reconciliation.period_start else None,
            "period_end": reconciliation.period_end.isoformat() if reconciliation.period_end else None,
            "reconciled_balance": float(reconciliation.reconciled_balance) if reconciliation.reconciled_balance else None
        }
    )
    
    # Get account details
    account_query = select(Account).where(Account.id == reconciliation.account_id)
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()
    
    # Count attachments
    attachments_query = select(func.count(ReconciliationAttachment.id)).where(
        ReconciliationAttachment.reconciliation_id == reconciliation.id
    )
    attachments_result = await db.execute(attachments_query)
    attachments_count = attachments_result.scalar() or 0
    
    recon_dict = reconciliation.to_dict()
    recon_dict["account_number"] = account.account_number if account else None
    recon_dict["account_name"] = account.account_name if account else None
    recon_dict["attachments_count"] = attachments_count
    
    return ReconciliationResponse(**recon_dict)


@router.post("/{reconciliation_id}/attachments")
async def upload_attachment(
    reconciliation_id: UUID,
    file: UploadFile = File(...),
    user_id: Optional[UUID] = Form(None),
    db: AsyncSession = Depends(get_db)
) -> AttachmentResponse:
    """
    Upload an attachment for a reconciliation
    
    Saves file to uploads/reconciliations/{reconciliation_id}/
    Max size: 10MB
    Allowed types: PDF, PNG, JPG, XLSX, CSV
    """
    # Verify reconciliation exists
    query = select(Reconciliation).where(Reconciliation.id == reconciliation_id)
    result = await db.execute(query)
    reconciliation = result.scalar_one_or_none()
    
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file and validate size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Create directory if not exists
    recon_dir = UPLOAD_DIR / str(reconciliation_id)
    recon_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{file_ext}"
    file_path = recon_dir / safe_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create database record
    relative_path = f"reconciliations/{reconciliation_id}/{safe_filename}"
    attachment = ReconciliationAttachment(
        id=uuid.uuid4(),
        reconciliation_id=reconciliation_id,
        file_name=file.filename,
        file_path=relative_path,
        file_type=file.content_type,
        file_size=file_size,
        uploaded_at=datetime.utcnow(),
        uploaded_by=user_id
    )
    
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    
    return AttachmentResponse(**attachment.to_dict())


@router.get("/{reconciliation_id}/attachments")
async def list_attachments(
    reconciliation_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all attachments for a reconciliation
    """
    # Verify reconciliation exists
    query = select(Reconciliation).where(Reconciliation.id == reconciliation_id)
    result = await db.execute(query)
    reconciliation = result.scalar_one_or_none()
    
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    # Get attachments
    attachments_query = select(ReconciliationAttachment).where(
        ReconciliationAttachment.reconciliation_id == reconciliation_id
    ).order_by(ReconciliationAttachment.uploaded_at.desc())
    
    attachments_result = await db.execute(attachments_query)
    attachments = attachments_result.scalars().all()
    
    attachments_list = [attachment.to_dict() for attachment in attachments]
    
    return {
        "attachments": attachments_list,
        "count": len(attachments_list)
    }


@router.delete("/{reconciliation_id}/attachments/{attachment_id}")
async def delete_attachment(
    reconciliation_id: UUID,
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete an attachment
    
    Removes file from disk and database record
    """
    # Get attachment
    query = select(ReconciliationAttachment).where(
        and_(
            ReconciliationAttachment.id == attachment_id,
            ReconciliationAttachment.reconciliation_id == reconciliation_id
        )
    )
    result = await db.execute(query)
    attachment = result.scalar_one_or_none()
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Delete file from disk
    file_path = UPLOAD_DIR.parent / attachment.file_path
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        # Log error but continue with database deletion
        print(f"Error deleting file: {e}")
    
    # Delete from database
    await db.delete(attachment)
    await db.commit()
    
    return {"message": "Attachment deleted successfully"}
