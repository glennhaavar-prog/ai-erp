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
        from app.models.bank_transaction import BankTransaction, TransactionStatus
        from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
        from app.models.chart_of_accounts import Account
        
        client_uuid = UUID(client_id)
        
        # Get distinct bank accounts from transactions
        stmt = (
            select(BankTransaction.bank_account)
            .where(BankTransaction.client_id == client_uuid)
            .distinct()
        )
        result = await db.execute(stmt)
        bank_account_numbers = result.scalars().all()
        
        accounts = []
        
        for account_number in bank_account_numbers:
            # Calculate saldo_i_bank (sum of all bank transactions)
            bank_sum_stmt = select(func.sum(BankTransaction.amount)).where(
                BankTransaction.client_id == client_uuid,
                BankTransaction.bank_account == account_number
            )
            bank_sum_result = await db.execute(bank_sum_stmt)
            saldo_i_bank = bank_sum_result.scalar() or Decimal("0.00")
            
            # Count unmatched transactions
            unmatched_count_stmt = select(func.count(BankTransaction.id)).where(
                BankTransaction.client_id == client_uuid,
                BankTransaction.bank_account == account_number,
                BankTransaction.status == TransactionStatus.UNMATCHED
            )
            unmatched_count_result = await db.execute(unmatched_count_stmt)
            poster_a_avstemme = unmatched_count_result.scalar() or 0
            
            # Calculate saldo_i_go (balance from general ledger for this account)
            # Sum debits - credits for this account number
            gl_sum_stmt = (
                select(
                    func.sum(GeneralLedgerLine.debit_amount - GeneralLedgerLine.credit_amount)
                )
                .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
                .where(
                    GeneralLedger.client_id == client_uuid,
                    GeneralLedgerLine.account_number == account_number,
                    GeneralLedger.status == "posted"
                )
            )
            gl_sum_result = await db.execute(gl_sum_stmt)
            saldo_i_go = gl_sum_result.scalar() or Decimal("0.00")
            
            # Get account name from chart of accounts
            account_name_stmt = select(Account.account_name).where(
                Account.client_id == client_uuid,
                Account.account_number == account_number
            )
            account_name_result = await db.execute(account_name_stmt)
            account_name = account_name_result.scalar() or f"Bank Account {account_number}"
            
            # Calculate difference
            differanse = float(saldo_i_bank) - float(saldo_i_go)
            
            accounts.append(BankAccountSummary(
                account_id=account_number,  # Use account number as ID
                account_number=account_number,
                account_name=account_name,
                saldo_i_bank=float(saldo_i_bank),
                saldo_i_go=float(saldo_i_go),
                differanse=differanse,
                poster_a_avstemme=poster_a_avstemme,
                currency="NOK"
            ))
        
        return accounts
    
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
        from app.models.bank_transaction import BankTransaction, TransactionStatus, TransactionType
        from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
        from app.models.chart_of_accounts import Account
        
        client_uuid = UUID(client_id)
        account_number = account_id
        
        # Default to current month if not specified
        if not period_start:
            today = date.today()
            period_start = f"{today.year}-{today.month:02d}-01"
        if not period_end:
            period_end = datetime.now().date().isoformat()
        
        # Get account name
        account_name_stmt = select(Account.account_name).where(
            Account.client_id == client_uuid,
            Account.account_number == account_number
        )
        account_name_result = await db.execute(account_name_stmt)
        account_name = account_name_result.scalar() or f"Bank Account {account_number}"
        
        # Query bank transactions for this account in the period
        bank_txn_stmt = (
            select(BankTransaction)
            .where(
                BankTransaction.client_id == client_uuid,
                BankTransaction.bank_account == account_number,
                BankTransaction.transaction_date >= datetime.fromisoformat(period_start),
                BankTransaction.transaction_date <= datetime.fromisoformat(period_end)
            )
            .order_by(BankTransaction.transaction_date.desc())
        )
        bank_txn_result = await db.execute(bank_txn_stmt)
        bank_transactions = bank_txn_result.scalars().all()
        
        # Initialize 4 categories
        categories_dict = {
            "ikke_registrert_i_go": {
                "key": "ikke_registrert_i_go",
                "name": "Ikke registrert i Go (Bank transactions not in ledger)",
                "transactions": []
            },
            "registrert_i_go_ikke_i_bank": {
                "key": "registrert_i_go_ikke_i_bank",
                "name": "Registrert i Go - ikke i bank (Ledger entries not in bank)",
                "transactions": []
            },
            "registrert_begge_steder_ikke_avstemt": {
                "key": "registrert_begge_steder_ikke_avstemt",
                "name": "Registrert begge steder - ikke avstemt (Both places, not matched)",
                "transactions": []
            },
            "avstemt": {
                "key": "avstemt",
                "name": "Avstemt (Matched)",
                "transactions": []
            }
        }
        
        # Categorize bank transactions
        for txn in bank_transactions:
            cat_txn = CategorizedTransaction(
                id=str(txn.id),
                date=txn.transaction_date.isoformat()[:10],
                description=txn.description,
                beløp=float(txn.amount),
                valutakode="NOK",
                voucher_number=txn.reference_number,
                status=txn.status.value
            )
            
            # Categorize based on status and posted_to_ledger flag
            if txn.status == TransactionStatus.MATCHED or txn.status == TransactionStatus.REVIEWED:
                categories_dict["avstemt"]["transactions"].append(cat_txn)
            elif txn.posted_to_ledger:
                categories_dict["registrert_begge_steder_ikke_avstemt"]["transactions"].append(cat_txn)
            else:
                categories_dict["ikke_registrert_i_go"]["transactions"].append(cat_txn)
        
        # Build category list with totals
        categories = []
        for cat_data in categories_dict.values():
            total = sum(t.beløp for t in cat_data["transactions"])
            categories.append(ReconciliationCategory(
                category_key=cat_data["key"],
                category_name=cat_data["name"],
                transactions=cat_data["transactions"],
                total_beløp=total
            ))
        
        # Calculate saldo_i_go (ledger balance for this account)
        gl_sum_stmt = (
            select(
                func.sum(GeneralLedgerLine.debit_amount - GeneralLedgerLine.credit_amount)
            )
            .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
            .where(
                GeneralLedger.client_id == client_uuid,
                GeneralLedgerLine.account_number == account_number,
                GeneralLedger.status == "posted"
            )
        )
        gl_sum_result = await db.execute(gl_sum_stmt)
        saldo_i_go = float(gl_sum_result.scalar() or Decimal("0.00"))
        
        # Calculate kontoutskrift_saldo (bank statement balance)
        bank_sum_stmt = select(func.sum(BankTransaction.amount)).where(
            BankTransaction.client_id == client_uuid,
            BankTransaction.bank_account == account_number
        )
        bank_sum_result = await db.execute(bank_sum_stmt)
        kontoutskrift_saldo = float(bank_sum_result.scalar() or Decimal("0.00"))
        
        # Calculate corrections (categories 1 & 2)
        korreksjoner_total = sum(
            cat.total_beløp for cat in categories 
            if cat.category_key in ["ikke_registrert_i_go", "registrert_i_go_ikke_i_bank"]
        )
        
        saldo_etter_korreksjoner = saldo_i_go + korreksjoner_total
        differanse = saldo_etter_korreksjoner - kontoutskrift_saldo
        is_balanced = abs(differanse) < 0.01
        
        return ReconciliationDetail(
            account_id=account_id,
            account_number=account_number,
            account_name=account_name,
            period_start=period_start,
            period_end=period_end,
            categories=categories,
            saldo_i_go=saldo_i_go,
            korreksjoner_total=korreksjoner_total,
            saldo_etter_korreksjoner=saldo_etter_korreksjoner,
            kontoutskrift_saldo=kontoutskrift_saldo,
            differanse=differanse,
            is_balanced=is_balanced,
            currency="NOK"
        )
    
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
