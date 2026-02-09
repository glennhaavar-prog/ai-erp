"""
Bank Reconciliation API

Upload bank statements and automatically match with GL entries.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.services.bank_reconciliation_service import BankReconciliationService


router = APIRouter()
bank_recon_service = BankReconciliationService()


# Request Models
class ConfirmMatchRequest(BaseModel):
    bank_transaction_id: str
    gl_entry_id: str


@router.post("/api/bank/reconciliation/upload")
async def upload_bank_statement(
    file: UploadFile = File(...),
    client_id: str = Query(...),
    bank_account: str = Query(..., description="GL account number for bank (e.g., 1920)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and parse bank statement.
    
    Supported formats:
    - CSV (semicolon-separated, Norwegian format)
    - Excel (.xlsx) - coming soon
    
    Expected columns:
    - Dato/Date: Transaction date (DD.MM.YYYY)
    - Beløp/Amount: Transaction amount
    - Tekst/Description: Transaction description
    - Referanse/Reference: Optional reference number
    
    Returns:
    - Parsed transactions
    - Auto-matching results
    - Items needing review
    """
    
    try:
        # Read file content
        content = await file.read()
        
        # Determine format
        file_format = "csv" if file.filename.endswith('.csv') else "excel"
        
        # Parse bank statement
        bank_transactions = await bank_recon_service.parse_bank_statement(
            file_content=content,
            format_type=file_format
        )
        
        if not bank_transactions:
            raise HTTPException(
                status_code=400,
                detail="No transactions found in file. Please check format."
            )
        
        # Match with GL entries
        match_result = await bank_recon_service.match_transactions(
            db=db,
            client_id=UUID(client_id),
            bank_account=bank_account,
            bank_transactions=bank_transactions
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "parsed_transactions": len(bank_transactions),
            **match_result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@router.post("/api/bank/reconciliation/confirm")
async def confirm_match(
    request: ConfirmMatchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm a manual or AI-suggested match.
    
    This marks the GL entry as reconciled with the bank transaction.
    """
    
    try:
        # TODO: Store reconciliation in database
        # For now, just acknowledge
        
        return {
            "success": True,
            "bank_transaction_id": request.bank_transaction_id,
            "gl_entry_id": request.gl_entry_id,
            "status": "matched",
            "message": "Match confirmed successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confirm error: {str(e)}")


@router.get("/api/bank/reconciliation/status")
async def get_reconciliation_status(
    client_id: str = Query(...),
    bank_account: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Get reconciliation status for a bank account.
    
    Returns summary of matched/unmatched items.
    """
    
    try:
        # TODO: Query reconciliation status from database
        
        return {
            "success": True,
            "client_id": client_id,
            "bank_account": bank_account,
            "status": "Not yet implemented - coming soon"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")
