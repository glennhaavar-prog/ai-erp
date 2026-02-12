"""
Bank Reconciliation API - Upload and match bank transactions
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID, uuid4
from decimal import Decimal

from app.database import get_db
from app.models.bank_transaction import BankTransaction, TransactionStatus, TransactionType
from app.models.bank_reconciliation import BankReconciliation
from app.models.client import Client
from app.models.vendor_invoice import VendorInvoice
from app.services.bank_import import BankImportService
from app.services.bank_reconciliation import BankReconciliationService

router = APIRouter(prefix="/api/bank", tags=["Bank"])


@router.post("/import")
async def import_bank_transactions(
    client_id: UUID = Query(..., description="Client ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Import bank transactions from CSV
    
    Supports Norwegian bank formats (DNB, Sparebank1, Nordea, etc.)
    Automatically runs matching after import.
    """
    
    # Validate client exists
    client_query = select(Client).where(Client.id == client_id)
    client_result = await db.execute(client_query)
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Read file
    file_content = await file.read()
    file_text = file_content.decode('utf-8')
    
    # Create batch ID
    batch_id = uuid4()
    
    # Parse transactions using BankImportService
    transactions = BankImportService.parse_norwegian_csv(
        file_text,
        client_id,
        batch_id,
        file.filename
    )
    
    if not transactions:
        raise HTTPException(status_code=400, detail="No valid transactions found in file")
    
    # Import transactions
    inserted_count = await BankImportService.import_transactions(db, transactions)
    
    # Run auto-matching on imported transactions
    matched_count = 0
    for trans_data in transactions:
        # Get the transaction we just created (match by batch_id and amount/date)
        stmt = select(BankTransaction).where(
            BankTransaction.upload_batch_id == batch_id,
            BankTransaction.amount == trans_data['amount'],
            BankTransaction.transaction_date == trans_data['transaction_date']
        )
        result = await db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if transaction:
            match_result = await BankReconciliationService.auto_match_transaction(
                db, transaction.id, client_id
            )
            if match_result:
                matched_count += 1
    
    return {
        "success": True,
        "batch_id": str(batch_id),
        "transactions_imported": inserted_count,
        "auto_matched": matched_count,
        "match_rate": round((matched_count / inserted_count * 100) if inserted_count > 0 else 0, 1),
        "filename": file.filename,
        "client_id": str(client_id),
    }


@router.get("/transactions")
async def get_bank_transactions(
    client_id: UUID = Query(..., description="Client ID"),
    status: str = Query(None, description="Filter by status (unmatched, matched, reviewed, ignored)"),
    limit: int = Query(50, ge=1, le=500, description="Items per page (default: 50)"),
    offset: int = Query(0, ge=0, description="Starting index (default: 0)"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get bank transactions for a client with pagination
    
    Query params:
    - client_id: Client ID (required)
    - status: Filter by status (unmatched, matched, reviewed, ignored)
    - limit: Items per page (default: 50, max: 500)
    - offset: Starting index (default: 0)
    
    Returns:
    {
        "items": [...],
        "total": int,
        "limit": int,
        "offset": int,
        "page_number": int
    }
    """
    
    query = select(BankTransaction).where(
        BankTransaction.client_id == client_id
    )
    
    if status:
        query = query.where(BankTransaction.status == status)
    
    # Get total count
    count_query = select(func.count()).select_from(BankTransaction).where(
        BankTransaction.client_id == client_id
    )
    if status:
        count_query = count_query.where(BankTransaction.status == status)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(BankTransaction.transaction_date.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    page_number = (offset // limit) + 1 if limit > 0 else 1
    
    return {
        "items": [t.to_dict() for t in transactions],
        "total": total,
        "limit": limit,
        "offset": offset,
        "page_number": page_number
    }


@router.get("/transactions/{transaction_id}")
async def get_transaction_details(
    transaction_id: UUID,
    client_id: UUID = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get details for a single bank transaction
    """
    stmt = select(BankTransaction).where(
        BankTransaction.id == transaction_id,
        BankTransaction.client_id == client_id
    )
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction.to_dict()


@router.get("/transactions/{transaction_id}/suggestions")
async def get_match_suggestions(
    transaction_id: UUID,
    client_id: UUID = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get matching suggestions for a bank transaction
    
    Returns potential invoice matches with confidence scores.
    """
    # Find matches
    matches = await BankReconciliationService.find_matches(
        db, transaction_id, client_id
    )
    
    # Get the transaction
    stmt = select(BankTransaction).where(BankTransaction.id == transaction_id)
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "transaction": transaction.to_dict(),
        "suggestions": matches,
        "count": len(matches)
    }


@router.post("/transactions/{transaction_id}/match")
async def manual_match_transaction(
    transaction_id: UUID,
    client_id: UUID = Query(..., description="Client ID"),
    invoice_id: UUID = Query(..., description="Invoice ID to match"),
    invoice_type: str = Query(..., description="Invoice type: vendor or customer"),
    user_id: UUID = Query(..., description="User ID performing the match"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually match a bank transaction to an invoice
    """
    # Validate invoice type
    if invoice_type not in ['vendor', 'customer']:
        raise HTTPException(status_code=400, detail="invoice_type must be 'vendor' or 'customer'")
    
    # Create manual match
    reconciliation = await BankReconciliationService.create_manual_match(
        db, transaction_id, invoice_id, invoice_type, client_id, user_id
    )
    
    return {
        "success": True,
        "reconciliation": reconciliation,
        "message": "Transaction successfully matched"
    }


@router.get("/reconciliation/stats")
async def get_reconciliation_statistics(
    client_id: UUID = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get bank reconciliation statistics for a client
    
    Returns:
    - Total transactions
    - Matched count
    - Unmatched count
    - Auto-match rate
    - Manual match count
    """
    stats = await BankReconciliationService.get_reconciliation_stats(db, client_id)
    return stats


@router.post("/auto-match")
async def run_auto_matching(
    client_id: UUID = Query(..., description="Client ID"),
    batch_id: UUID = Query(None, description="Process specific upload batch"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run automatic matching on unmatched bank transactions
    
    Uses AI matching algorithm with:
    1. Exact amount match (40 points)
    2. Date proximity (30 points)
    3. KID number match (20 points)
    4. Vendor/customer name match (20 points)
    5. Invoice number in description (10 points)
    
    Auto-approves matches with confidence >= 85%
    """
    
    # Get unmatched transactions
    query = select(BankTransaction).where(
        BankTransaction.client_id == client_id,
        BankTransaction.status == TransactionStatus.UNMATCHED
    )
    
    if batch_id:
        query = query.where(BankTransaction.upload_batch_id == batch_id)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    if not transactions:
        return {
            "success": True,
            "message": "No unmatched transactions to process",
            "summary": {
                "total": 0,
                "matched": 0,
                "unmatched": 0
            }
        }
    
    # Run auto-matching
    matched_count = 0
    low_confidence_count = 0
    
    for transaction in transactions:
        match_result = await BankReconciliationService.auto_match_transaction(
            db, transaction.id, client_id
        )
        
        if match_result:
            matched_count += 1
        else:
            low_confidence_count += 1
    
    return {
        "success": True,
        "message": f"Auto-matched {matched_count} of {len(transactions)} transactions",
        "summary": {
            "total": len(transactions),
            "matched": matched_count,
            "low_confidence": low_confidence_count,
            "match_rate": round((matched_count / len(transactions) * 100) if len(transactions) > 0 else 0, 1)
        }
    }
