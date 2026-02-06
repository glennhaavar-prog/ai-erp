"""
Bank Reconciliation API - Upload and match bank transactions
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID, uuid4
import csv
import io
import pandas as pd

from app.database import get_db
from app.models.bank_transaction import BankTransaction, TransactionStatus, TransactionType
from app.models.client import Client
from app.models.vendor_invoice import VendorInvoice
from app.agents.bank_matching_agent import BankMatchingAgent

router = APIRouter(prefix="/api/bank", tags=["Bank"])


async def parse_norwegian_bank_csv(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Parse Norwegian bank CSV formats (DNB, Sparebank1, Nordea, etc.)
    
    Common Norwegian bank CSV columns:
    - Dato / Bokføringsdato
    - Forklaring / Tekst
    - Beløp inn / Beløp ut / Beløp
    - Saldo
    - KID
    - Motpart / Mottaker
    """
    try:
        # Try pandas first (handles most formats)
        df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8', sep=';')
        
        # Normalize column names (Norwegian banks use different names)
        df.columns = df.columns.str.strip().str.lower()
        
        transactions = []
        
        for _, row in df.iterrows():
            # Extract date (try multiple column names)
            date_str = None
            for date_col in ['dato', 'bokføringsdato', 'transaksjonsdato', 'date']:
                if date_col in df.columns and pd.notna(row[date_col]):
                    date_str = str(row[date_col])
                    break
            
            if not date_str:
                continue
            
            # Parse date (Norwegian format: DD.MM.YYYY or YYYY-MM-DD)
            try:
                if '.' in date_str:
                    transaction_date = datetime.strptime(date_str, '%d.%m.%Y')
                else:
                    transaction_date = datetime.fromisoformat(date_str)
            except:
                continue
            
            # Extract amount
            amount = 0.0
            transaction_type = TransactionType.DEBIT
            
            # Check for separate "inn" and "ut" columns
            if 'beløp inn' in df.columns and pd.notna(row['beløp inn']):
                amount = float(str(row['beløp inn']).replace(',', '.').replace(' ', ''))
                transaction_type = TransactionType.CREDIT
            elif 'beløp ut' in df.columns and pd.notna(row['beløp ut']):
                amount = abs(float(str(row['beløp ut']).replace(',', '.').replace(' ', '')))
                transaction_type = TransactionType.DEBIT
            elif 'beløp' in df.columns and pd.notna(row['beløp']):
                amount_val = float(str(row['beløp']).replace(',', '.').replace(' ', ''))
                transaction_type = TransactionType.CREDIT if amount_val > 0 else TransactionType.DEBIT
                amount = abs(amount_val)
            
            if amount == 0:
                continue
            
            # Extract description
            description = ''
            for desc_col in ['forklaring', 'tekst', 'beskrivelse', 'description', 'text']:
                if desc_col in df.columns and pd.notna(row[desc_col]):
                    description = str(row[desc_col])
                    break
            
            # Extract KID (Norwegian payment reference)
            kid = None
            for kid_col in ['kid', 'kidnummer', 'referanse', 'reference']:
                if kid_col in df.columns and pd.notna(row[kid_col]):
                    kid = str(row[kid_col])
                    break
            
            # Extract counterparty
            counterparty = None
            for party_col in ['motpart', 'mottaker', 'avsender', 'counterparty']:
                if party_col in df.columns and pd.notna(row[party_col]):
                    counterparty = str(row[party_col])
                    break
            
            # Extract balance
            balance = None
            if 'saldo' in df.columns and pd.notna(row['saldo']):
                try:
                    balance = float(str(row['saldo']).replace(',', '.').replace(' ', ''))
                except:
                    pass
            
            transactions.append({
                'transaction_date': transaction_date,
                'amount': amount,
                'transaction_type': transaction_type,
                'description': description,
                'kid_number': kid,
                'counterparty_name': counterparty,
                'balance_after': balance
            })
        
        return transactions
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


@router.post("/upload")
async def upload_bank_transactions(
    client_id: UUID = Query(..., description="Client ID"),
    bank_account: str = Query(..., description="Bank account number"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload bank transactions from CSV/Excel
    
    Supports Norwegian bank formats (DNB, Sparebank1, Nordea, etc.)
    """
    
    # Validate client exists
    client_query = select(Client).where(Client.id == client_id)
    client_result = await db.execute(client_query)
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Read file
    file_content = await file.read()
    
    # Parse transactions
    transactions = await parse_norwegian_bank_csv(file_content)
    
    if not transactions:
        raise HTTPException(status_code=400, detail="No valid transactions found in file")
    
    # Create batch ID
    batch_id = uuid4()
    
    # Insert transactions
    inserted_count = 0
    for txn_data in transactions:
        transaction = BankTransaction(
            client_id=client_id,
            bank_account=bank_account,
            upload_batch_id=batch_id,
            original_filename=file.filename,
            **txn_data
        )
        db.add(transaction)
        inserted_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "batch_id": str(batch_id),
        "transactions_imported": inserted_count,
        "filename": file.filename,
        "client_id": str(client_id),
        "bank_account": bank_account
    }


@router.get("/transactions")
async def get_bank_transactions(
    client_id: UUID = Query(..., description="Client ID"),
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get bank transactions for a client
    """
    
    query = select(BankTransaction).where(
        BankTransaction.client_id == client_id
    )
    
    if status:
        query = query.where(BankTransaction.status == status)
    
    query = query.order_by(BankTransaction.transaction_date.desc()).limit(limit)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return {
        "transactions": [t.to_dict() for t in transactions],
        "total": len(transactions)
    }


@router.get("/stats")
async def get_bank_stats(
    client_id: UUID = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get bank reconciliation statistics for a client
    """
    
    # Total transactions
    total_query = select(func.count(BankTransaction.id)).where(
        BankTransaction.client_id == client_id
    )
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0
    
    # Unmatched
    unmatched_query = select(func.count(BankTransaction.id)).where(
        BankTransaction.client_id == client_id,
        BankTransaction.status == TransactionStatus.UNMATCHED
    )
    unmatched_result = await db.execute(unmatched_query)
    unmatched = unmatched_result.scalar() or 0
    
    # Matched
    matched_query = select(func.count(BankTransaction.id)).where(
        BankTransaction.client_id == client_id,
        BankTransaction.status == TransactionStatus.MATCHED
    )
    matched_result = await db.execute(matched_query)
    matched = matched_result.scalar() or 0
    
    return {
        "total": total,
        "unmatched": unmatched,
        "matched": matched,
        "reviewed": 0,  # TODO: Add when review workflow is implemented
        "match_rate": round((matched / total * 100) if total > 0 else 0, 1)
    }


@router.post("/match")
async def run_ai_matching(
    client_id: UUID = Query(..., description="Client ID"),
    batch_id: UUID = Query(None, description="Process specific upload batch"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run AI matching on unmatched bank transactions
    
    Matches transactions to unpaid invoices using:
    1. KID number (99% confidence)
    2. Amount + date + vendor (80-95% confidence)
    3. AI description analysis (50-80% confidence)
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
    
    # Get unpaid invoices for this client
    invoices_query = select(VendorInvoice).where(
        VendorInvoice.client_id == client_id,
        VendorInvoice.payment_status.in_(['unpaid', 'partial'])
    )
    invoices_result = await db.execute(invoices_query)
    invoices = invoices_result.scalars().all()
    
    # Run AI matching
    agent = BankMatchingAgent()
    match_results = await agent.batch_match_transactions(transactions, invoices)
    
    # Update database with matches
    for match in match_results["matched"]:
        txn_id = UUID(match["transaction_id"])
        inv_id = UUID(match["invoice_id"])
        
        # Update transaction
        update_query = select(BankTransaction).where(BankTransaction.id == txn_id)
        update_result = await db.execute(update_query)
        txn = update_result.scalar_one()
        
        txn.ai_matched_invoice_id = inv_id
        txn.ai_match_confidence = Decimal(str(match["confidence"]))
        txn.ai_match_reason = match["reason"]
        txn.status = TransactionStatus.MATCHED
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Matched {match_results['summary']['matched']} transactions",
        "summary": match_results["summary"],
        "matched": match_results["matched"]
    }
