"""
Vouchers API - Automatic Voucher Creation + Viewing
KONTALI SPRINT 1 - Task 2

Supports:
- POST /create-from-invoice/{invoice_id} - Create voucher from vendor invoice
- GET /{voucher_id} - Get voucher details
- GET /by-number/{voucher_number} - Get voucher by number
- GET /list - List vouchers with filters
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.database import get_db
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.document import Document
from app.models.chart_of_accounts import Account
from app.models.audit_trail import AuditTrail
from app.services.voucher_service import (
    VoucherGenerator,
    VoucherValidationError,
    get_voucher_by_id,
    list_vouchers
)
from app.schemas.voucher import (
    VoucherCreateRequest,
    VoucherCreateResponse,
    VoucherDTO,
    VoucherListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vouchers", tags=["vouchers"])


@router.post("/create-from-invoice/{invoice_id}", response_model=VoucherCreateResponse)
async def create_voucher_from_invoice(
    invoice_id: UUID,
    request: VoucherCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create voucher (General Ledger entry) from vendor invoice
    
    **SkatteFUNN-kritisk**: Dette er kjernen i automatisk bokføring!
    
    Workflow:
    1. Fetch invoice from database
    2. Generate voucher lines (Norwegian accounting logic)
    3. Validate balance (debit = credit)
    4. Create voucher + lines in database (ACID transaction)
    5. Update invoice status to 'approved'
    
    Example:
    ```
    POST /api/vouchers/create-from-invoice/550e8400-e29b-41d4-a716-446655440000
    {
      "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "admin",
      "accounting_date": "2026-02-09",
      "override_account": null
    }
    ```
    
    Response:
    ```
    {
      "success": true,
      "voucher_id": "...",
      "voucher_number": "2026-0042",
      "total_debit": 12500.00,
      "total_credit": 12500.00,
      "is_balanced": true,
      "lines_count": 3,
      "message": "Voucher created successfully"
    }
    ```
    """
    try:
        # Create voucher using VoucherGenerator service
        generator = VoucherGenerator(db)
        
        voucher_dto = await generator.create_voucher_from_invoice(
            invoice_id=invoice_id,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            accounting_date=request.accounting_date,
            override_account=request.override_account
        )
        
        logger.info(
            f"✅ Created voucher {voucher_dto.voucher_number} from invoice {invoice_id}"
        )
        
        return VoucherCreateResponse(
            success=True,
            voucher_id=voucher_dto.id,
            voucher_number=voucher_dto.voucher_number,
            total_debit=voucher_dto.total_debit,
            total_credit=voucher_dto.total_credit,
            is_balanced=voucher_dto.is_balanced,
            lines_count=len(voucher_dto.lines),
            message=f"Voucher {voucher_dto.voucher_number} created successfully"
        )
    
    except ValueError as e:
        # Invoice not found or already posted
        logger.warning(f"⚠️ Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except VoucherValidationError as e:
        # Voucher doesn't balance
        logger.error(f"❌ Voucher validation failed: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    
    except Exception as e:
        # Unexpected error
        logger.error(f"❌ Error creating voucher: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/list", response_model=VoucherListResponse)
async def list_vouchers_endpoint(
    client_id: UUID = Query(..., description="Client ID"),
    period: Optional[str] = Query(None, description="Filter by period (YYYY-MM)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List vouchers for a client with optional period filter
    
    Example:
    ```
    GET /api/vouchers/list?client_id=123e4567-e89b-12d3-a456-426614174000&period=2026-02&page=1&page_size=50
    ```
    
    Returns paginated list of vouchers (without line details for performance)
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        count_query = select(func.count(GeneralLedger.id)).where(
            GeneralLedger.client_id == client_id
        )
        if period:
            count_query = count_query.where(GeneralLedger.period == period)
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Get vouchers
        vouchers = await list_vouchers(
            db=db,
            client_id=client_id,
            period=period,
            limit=page_size,
            offset=offset
        )
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        return VoucherListResponse(
            items=vouchers,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    except Exception as e:
        logger.error(f"Error listing vouchers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{voucher_id}", response_model=VoucherDTO)
async def get_voucher(
    voucher_id: UUID,
    client_id: UUID = Query(..., description="Client ID for security"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get voucher by ID with complete details
    
    Returns:
    - Voucher information (number, date, description)
    - All voucher lines (account, debit, credit, description)
    - Balance validation
    
    Example:
    ```
    GET /api/vouchers/550e8400-e29b-41d4-a716-446655440000?client_id=123e4567-e89b-12d3-a456-426614174000
    ```
    """
    voucher = await get_voucher_by_id(db, voucher_id, client_id)
    
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    return voucher


@router.get("/by-number/{voucher_number}", response_model=VoucherDTO)
async def get_voucher_by_number(
    voucher_number: str,
    client_id: UUID = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get voucher by voucher number (e.g., "2026-0001")
    
    Useful for cross-navigation when you only have the voucher number.
    
    Example:
    ```
    GET /api/vouchers/by-number/2026-0042?client_id=123e4567-e89b-12d3-a456-426614174000
    ```
    """
    query = (
        select(GeneralLedger)
        .where(GeneralLedger.client_id == client_id)
        .where(GeneralLedger.voucher_number == voucher_number)
    )
    
    result = await db.execute(query)
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"Voucher {voucher_number} not found for client {client_id}"
        )
    
    # Reuse get_voucher_by_id logic
    return await get_voucher_by_id(db, entry.id, client_id)


@router.get("/{voucher_id}/audit-trail")
async def get_voucher_audit_trail(
    voucher_id: UUID,
    client_id: UUID = Query(..., description="Client ID for security"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit trail for a voucher
    
    Returns all changes made to this voucher:
    - Who created it (AI or user)
    - When it was created
    - Any modifications (if editable vouchers are implemented)
    
    Example:
    ```
    GET /api/vouchers/550e8400-e29b-41d4-a716-446655440000/audit-trail?client_id=123e4567...
    ```
    
    Returns:
    ```
    {
      "voucher_id": "...",
      "entries": [
        {
          "id": "...",
          "action": "create",
          "changed_by_type": "ai_agent",
          "changed_by_name": "AI Bokfører",
          "timestamp": "2026-02-09T20:15:00Z",
          "reason": "Automatic booking from vendor invoice"
        }
      ]
    }
    ```
    """
    try:
        # Verify voucher exists and belongs to client
        voucher_query = select(GeneralLedger).where(
            GeneralLedger.id == voucher_id,
            GeneralLedger.client_id == client_id
        )
        result = await db.execute(voucher_query)
        voucher = result.scalar_one_or_none()
        
        if not voucher:
            raise HTTPException(status_code=404, detail="Voucher not found")
        
        # Get audit trail entries for this voucher
        audit_query = (
            select(AuditTrail)
            .where(AuditTrail.table_name == "general_ledger")
            .where(AuditTrail.record_id == voucher_id)
            .order_by(AuditTrail.timestamp.desc())
        )
        
        audit_result = await db.execute(audit_query)
        entries = audit_result.scalars().all()
        
        return {
            "voucher_id": str(voucher_id),
            "voucher_number": voucher.voucher_number,
            "entries": [
                {
                    "id": str(entry.id),
                    "action": entry.action,
                    "changed_by_type": entry.changed_by_type,
                    "changed_by_name": entry.changed_by_name or entry.changed_by_type,
                    "timestamp": entry.timestamp.isoformat(),
                    "reason": entry.reason,
                    "old_value": entry.old_value,
                    "new_value": entry.new_value
                }
                for entry in entries
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audit trail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
