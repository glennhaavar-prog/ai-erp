"""
Bank Reconciliation API - PowerOffice Compatible

Endpoints for bank account overview and detailed reconciliation view.
- GET /api/bank/accounts - List all accounts with balances
- GET /api/bank/accounts/{id}/reconciliation - Detail view with 4-part categorization
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from app.services.bank_reconciliation_service import BankReconciliationService


router = APIRouter()
bank_recon_service = BankReconciliationService()


# Response Models
class BankAccountSummary(BaseModel):
    """Bank account overview row"""
    account_id: str
    account_number: str
    account_name: str
    saldo_i_bank: float
    saldo_i_go: float
    differanse: float
    poster_a_avstemme: int
    currency: str = "NOK"


class CategorizedTransaction(BaseModel):
    """Transaction in one of the 4 categories"""
    id: str
    date: str
    description: str
    beløp: float
    valutakode: str = "NOK"
    voucher_number: Optional[str] = None
    status: str


class ReconciliationCategory(BaseModel):
    """One of the 4 reconciliation categories"""
    category_key: str
    category_name: str
    transactions: List[CategorizedTransaction]
    total_beløp: float


class ReconciliationDetail(BaseModel):
    """Detailed reconciliation view for one account"""
    account_id: str
    account_number: str
    account_name: str
    period_start: str
    period_end: str
    
    # 4 categories
    categories: List[ReconciliationCategory]
    
    # Summary calculations
    saldo_i_go: float
    korreksjoner_total: float
    saldo_etter_korreksjoner: float
    kontoutskrift_saldo: float
    differanse: float
    is_balanced: bool
    
    currency: str = "NOK"


# Request Models
class ConfirmMatchRequest(BaseModel):
    bank_transaction_id: str
    gl_entry_id: str


@router.get("/api/bank/accounts", response_model=List[BankAccountSummary])
async def get_bank_accounts(
    client_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all bank accounts with balances and differences.
    
    PowerOffice: "Alle bankkonto med differanser"
    
    Returns:
    - Bankkonto
    - Kontonavn
    - Saldo i bank
    - Saldo i Go
    - Avstemming (X poster å avstemme)
    """
    
    try:
        # TODO: Query bank accounts from database
        # For now, return mock data for testing
        
        mock_accounts = [
            BankAccountSummary(
                account_id="1",
                account_number="1920",
                account_name="Hovedkonto - Bank",
                saldo_i_bank=125450.50,
                saldo_i_go=125200.25,
                differanse=250.25,
                poster_a_avstemme=3,
                currency="NOK"
            ),
            BankAccountSummary(
                account_id="2",
                account_number="1921",
                account_name="Sparekonto",
                saldo_i_bank=50000.00,
                saldo_i_go=50000.00,
                differanse=0.0,
                poster_a_avstemme=0,
                currency="NOK"
            ),
        ]
        
        return mock_accounts
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accounts: {str(e)}")


@router.get("/api/bank/accounts/{account_id}/reconciliation", response_model=ReconciliationDetail)
async def get_reconciliation_detail(
    account_id: str,
    client_id: str = Query(...),
    period_start: Optional[str] = Query(None),  # YYYY-MM-DD
    period_end: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed reconciliation view for one account.
    
    PowerOffice: Detail page showing 4-part categorization
    
    Categories (Norwegian):
    1. Uttak postert - ikke inkludert i kontoutskrift (Withdrawals posted, not in statement)
    2. Innskudd postert - ikke inkludert i kontoutskrift (Deposits posted, not in statement)
    3. Uttak ikke postert - inkludert i kontoutskrift (Withdrawals not posted, in statement)
    4. Innskudd ikke postert - inkludert i kontoutskrift (Deposits not posted, in statement)
    
    Calculations:
    - Saldo i Go: Starting balance in system
    - Korreksjoner: Sum of category 1 & 2
    - Saldo etter korreksjoner: Saldo i Go + Korreksjoner
    - Kontoutskrift saldo: Bank statement balance
    - Differanse: Saldo etter korreksjoner - Kontoutskrift saldo
    """
    
    try:
        # Default to current month if not specified
        if not period_start:
            today = date.today()
            period_start = f"{today.year}-{today.month:02d}-01"
        if not period_end:
            period_end = datetime.now().date().isoformat()
        
        # TODO: Query actual data from database
        # For now, return mock data for testing
        
        mock_detail = ReconciliationDetail(
            account_id=account_id,
            account_number="1920",
            account_name="Hovedkonto - Bank",
            period_start=period_start,
            period_end=period_end,
            
            # Mock 4 categories
            categories=[
                ReconciliationCategory(
                    category_key="uttak_postert_ikke_statement",
                    category_name="Uttak postert - ikke inkludert i kontoutskrift",
                    transactions=[
                        CategorizedTransaction(
                            id="t1",
                            date="2026-02-05",
                            description="Lønn utbetaling februar",
                            beløp=-45000.00,
                            valutakode="NOK",
                            voucher_number="V001",
                            status="posted"
                        ),
                        CategorizedTransaction(
                            id="t2",
                            date="2026-02-08",
                            description="Leverandør betaling",
                            beløp=-12500.00,
                            valutakode="NOK",
                            voucher_number="V002",
                            status="posted"
                        ),
                    ],
                    total_beløp=-57500.00
                ),
                ReconciliationCategory(
                    category_key="innskudd_postert_ikke_statement",
                    category_name="Innskudd postert - ikke inkludert i kontoutskrift",
                    transactions=[
                        CategorizedTransaction(
                            id="t3",
                            date="2026-02-10",
                            description="Kundebetalinger",
                            beløp=35250.00,
                            valutakode="NOK",
                            voucher_number="V003",
                            status="posted"
                        ),
                    ],
                    total_beløp=35250.00
                ),
                ReconciliationCategory(
                    category_key="uttak_ikke_postert_i_statement",
                    category_name="Uttak ikke postert - inkludert i kontoutskrift",
                    transactions=[
                        CategorizedTransaction(
                            id="t4",
                            date="2026-02-11",
                            description="Gebyr fra bank",
                            beløp=-500.00,
                            valutakode="NOK",
                            status="in_statement"
                        ),
                    ],
                    total_beløp=-500.00
                ),
                ReconciliationCategory(
                    category_key="innskudd_ikke_postert_i_statement",
                    category_name="Innskudd ikke postert - inkludert i kontoutskrift",
                    transactions=[],
                    total_beløp=0.0
                ),
            ],
            
            # Summary
            saldo_i_go=125200.25,
            korreksjoner_total=-22250.00,  # -57500 + 35250
            saldo_etter_korreksjoner=102950.25,  # 125200 - 22250
            kontoutskrift_saldo=102450.25,  # Actual bank statement
            differanse=500.00,  # Should be 0 if balanced
            is_balanced=False,
            
            currency="NOK"
        )
        
        return mock_detail
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reconciliation: {str(e)}")


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
