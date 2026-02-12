"""
Opening Balance API - Åpningsbalanse Import

Handles opening balance import with strict validations:
1. MUST balance to zero (sum debit = sum credit)
2. Bank accounts MUST match actual bank balance
3. All accounts must exist in chart of accounts

Workflow:
1. POST /import - Upload and parse CSV/Excel
2. POST /validate - Validate balance and bank accounts
3. GET /preview/{id} - Preview before import
4. POST /import-to-ledger - Import to journal entries (locked)
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime
import uuid
import csv
import io

from app.database import get_db
from app.models.opening_balance import (
    OpeningBalance, OpeningBalanceLine, OpeningBalanceStatus
)
from app.models.client import Client
from app.models.chart_of_accounts import Account
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.bank_connection import BankConnection
from app.schemas.opening_balance import (
    OpeningBalanceImportRequest,
    OpeningBalanceValidateRequest,
    OpeningBalanceResponse,
    OpeningBalancePreviewResponse,
    OpeningBalanceImportResponse,
    OpeningBalanceLineResponse,
    ValidationError,
    BankBalanceVerification
)

router = APIRouter(prefix="/api/opening-balance", tags=["Opening Balance"])


# ============================================================================
# Helper Functions
# ============================================================================

# Norwegian bank account prefixes (typically 1920, 1921, 1930, etc.)
BANK_ACCOUNT_PREFIXES = ["1920", "1921", "1930", "1940", "1950", "1960"]


def is_bank_account(account_number: str) -> bool:
    """Check if account is a bank account"""
    return any(account_number.startswith(prefix) for prefix in BANK_ACCOUNT_PREFIXES)


async def calculate_totals(
    opening_balance_id: uuid.UUID,
    db: AsyncSession
) -> dict:
    """Calculate total debit and credit for opening balance"""
    result = await db.execute(
        select(
            func.sum(OpeningBalanceLine.debit_amount).label('total_debit'),
            func.sum(OpeningBalanceLine.credit_amount).label('total_credit'),
            func.count(OpeningBalanceLine.id).label('line_count')
        ).where(OpeningBalanceLine.opening_balance_id == opening_balance_id)
    )
    row = result.first()
    
    total_debit = row.total_debit or Decimal("0.00")
    total_credit = row.total_credit or Decimal("0.00")
    line_count = row.line_count or 0
    
    return {
        "total_debit": total_debit,
        "total_credit": total_credit,
        "line_count": line_count,
        "difference": total_debit - total_credit
    }


async def validate_opening_balance(
    opening_balance: OpeningBalance,
    db: AsyncSession,
    manual_bank_balances: Optional[List[BankBalanceVerification]] = None
) -> dict:
    """
    Validate opening balance against all rules
    
    Returns:
        dict with validation results
    """
    errors = []
    warnings = []
    
    # Get all lines
    result = await db.execute(
        select(OpeningBalanceLine)
        .where(OpeningBalanceLine.opening_balance_id == opening_balance.id)
        .order_by(OpeningBalanceLine.line_number)
    )
    lines = result.scalars().all()
    
    if not lines:
        errors.append({
            "severity": "error",
            "code": "NO_LINES",
            "message": "Opening balance has no lines"
        })
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings
        }
    
    # Rule 1: Check balance (SUM(debit) = SUM(credit))
    totals = await calculate_totals(opening_balance.id, db)
    is_balanced = totals["difference"] == Decimal("0.00")
    
    if not is_balanced:
        errors.append({
            "severity": "error",
            "code": "NOT_BALANCED",
            "message": f"Opening balance does not balance. Difference: {totals['difference']} NOK",
            "amount": float(totals["difference"])
        })
    
    # Check if accounts exist in chart of accounts
    result = await db.execute(
        select(Account)
        .where(
            and_(
                Account.client_id == opening_balance.client_id,
                Account.is_active == True
            )
        )
    )
    existing_accounts = {acc.account_number: acc for acc in result.scalars().all()}
    
    missing_accounts = []
    bank_balance_errors = []
    
    # Create manual bank balance lookup
    manual_bank_lookup = {}
    if manual_bank_balances:
        for mb in manual_bank_balances:
            manual_bank_lookup[mb.account_number] = mb.actual_balance
    
    # Validate each line
    for line in lines:
        line_errors = []
        
        # Check if account exists
        if line.account_number not in existing_accounts:
            missing_accounts.append(line.account_number)
            line_errors.append({
                "code": "ACCOUNT_NOT_FOUND",
                "message": f"Account {line.account_number} not found in chart of accounts"
            })
            line.account_exists = False
        else:
            line.account_exists = True
        
        # Check if it's a bank account
        line.is_bank_account = is_bank_account(line.account_number)
        
        # Rule 2: Validate bank accounts
        if line.is_bank_account:
            # Calculate net balance (debit - credit for bank accounts)
            net_balance = line.debit_amount - line.credit_amount
            
            # Check manual verification first
            if line.account_number in manual_bank_lookup:
                expected_balance = manual_bank_lookup[line.account_number]
                line.expected_bank_balance = expected_balance
                
                # Compare with tolerance for rounding (2 decimals)
                difference = abs(net_balance - expected_balance)
                if difference > Decimal("0.01"):
                    line.bank_balance_match = False
                    bank_balance_errors.append({
                        "severity": "error",
                        "code": "BANK_BALANCE_MISMATCH",
                        "message": (
                            f"Bank account {line.account_number} ({line.account_name}): "
                            f"Opening balance {net_balance} does not match actual bank balance {expected_balance}. "
                            f"Difference: {difference} NOK"
                        ),
                        "account_number": line.account_number,
                        "amount": float(difference)
                    })
                else:
                    line.bank_balance_match = True
            else:
                # No manual verification provided
                warnings.append({
                    "severity": "warning",
                    "code": "BANK_NOT_VERIFIED",
                    "message": f"Bank account {line.account_number} ({line.account_name}) not verified against actual bank balance",
                    "account_number": line.account_number
                })
                line.bank_balance_match = None
        
        line.validation_errors = line_errors if line_errors else None
    
    # Update opening balance status
    opening_balance.is_balanced = is_balanced
    opening_balance.balance_difference = totals["difference"]
    opening_balance.total_debit = totals["total_debit"]
    opening_balance.total_credit = totals["total_credit"]
    opening_balance.line_count = totals["line_count"]
    opening_balance.missing_accounts = missing_accounts if missing_accounts else None
    opening_balance.validation_errors = errors if errors else None
    opening_balance.bank_balance_errors = bank_balance_errors if bank_balance_errors else None
    
    # Bank balance is verified if no errors and all bank accounts checked
    bank_accounts = [line for line in lines if line.is_bank_account]
    if bank_accounts:
        opening_balance.bank_balance_verified = (
            len(bank_balance_errors) == 0 and
            all(line.bank_balance_match is not None for line in bank_accounts)
        )
    else:
        opening_balance.bank_balance_verified = True  # No bank accounts to verify
    
    # Determine status
    if errors or bank_balance_errors:
        opening_balance.status = OpeningBalanceStatus.INVALID
    else:
        opening_balance.status = OpeningBalanceStatus.VALID
    
    await db.commit()
    await db.refresh(opening_balance)
    
    # Combine all errors
    all_errors = errors + bank_balance_errors
    
    return {
        "valid": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": warnings,
        "is_balanced": is_balanced,
        "bank_balance_verified": opening_balance.bank_balance_verified,
        "missing_accounts": missing_accounts
    }


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/import", response_model=OpeningBalanceResponse, status_code=status.HTTP_201_CREATED)
async def import_opening_balance(
    request: OpeningBalanceImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1: Import opening balance from data
    
    - Parses lines
    - Creates draft opening balance
    - Does NOT validate yet (use /validate endpoint)
    """
    # Verify client exists
    result = await db.execute(
        select(Client).where(Client.id == request.client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {request.client_id} not found"
        )
    
    # Check if opening balance already exists for this fiscal year
    result = await db.execute(
        select(OpeningBalance)
        .where(
            and_(
                OpeningBalance.client_id == request.client_id,
                OpeningBalance.fiscal_year == request.fiscal_year,
                OpeningBalance.status == OpeningBalanceStatus.IMPORTED
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Opening balance for fiscal year {request.fiscal_year} already imported"
        )
    
    # Create opening balance
    opening_balance = OpeningBalance(
        id=uuid.uuid4(),
        client_id=request.client_id,
        import_date=request.import_date,
        fiscal_year=request.fiscal_year,
        description=request.description,
        status=OpeningBalanceStatus.DRAFT,
    )
    
    db.add(opening_balance)
    await db.flush()
    
    # Create lines
    for idx, line_data in enumerate(request.lines, start=1):
        line = OpeningBalanceLine(
            id=uuid.uuid4(),
            opening_balance_id=opening_balance.id,
            line_number=idx,
            account_number=line_data.account_number,
            account_name=line_data.account_name,
            debit_amount=line_data.debit,
            credit_amount=line_data.credit,
        )
        db.add(line)
    
    # Flush lines to database BEFORE calculating totals
    await db.flush()
    
    await db.commit()
    await db.refresh(opening_balance)
    
    # Calculate totals
    totals = await calculate_totals(opening_balance.id, db)
    opening_balance.total_debit = totals["total_debit"]
    opening_balance.total_credit = totals["total_credit"]
    opening_balance.line_count = totals["line_count"]
    opening_balance.balance_difference = totals["difference"]
    
    await db.commit()
    
    return OpeningBalanceResponse(
        id=opening_balance.id,
        client_id=opening_balance.client_id,
        import_date=opening_balance.import_date,
        fiscal_year=opening_balance.fiscal_year,
        description=opening_balance.description,
        status=opening_balance.status.value,
        is_balanced=False,  # Not validated yet
        balance_difference=opening_balance.balance_difference,
        bank_balance_verified=False,
        total_debit=opening_balance.total_debit,
        total_credit=opening_balance.total_credit,
        line_count=opening_balance.line_count,
        original_filename=opening_balance.original_filename,
        created_at=opening_balance.created_at,
        imported_at=opening_balance.imported_at,
        journal_entry_id=opening_balance.journal_entry_id,
    )


@router.post("/validate", response_model=OpeningBalanceResponse)
async def validate_opening_balance_endpoint(
    request: OpeningBalanceValidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Validate opening balance
    
    - Checks SUM(debit) = SUM(credit) (MUST be zero)
    - Verifies bank accounts match actual balance
    - Checks all accounts exist in chart of accounts
    
    Blocks import if validation fails.
    """
    # Get opening balance
    result = await db.execute(
        select(OpeningBalance).where(OpeningBalance.id == request.opening_balance_id)
    )
    opening_balance = result.scalar_one_or_none()
    if not opening_balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opening balance {request.opening_balance_id} not found"
        )
    
    # Cannot validate already imported
    if opening_balance.status == OpeningBalanceStatus.IMPORTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opening balance already imported"
        )
    
    opening_balance.status = OpeningBalanceStatus.VALIDATING
    await db.commit()
    
    # Run validation
    validation_result = await validate_opening_balance(
        opening_balance,
        db,
        manual_bank_balances=request.bank_balances
    )
    
    await db.refresh(opening_balance)
    
    # Get lines for response
    result = await db.execute(
        select(OpeningBalanceLine)
        .where(OpeningBalanceLine.opening_balance_id == opening_balance.id)
        .order_by(OpeningBalanceLine.line_number)
    )
    lines = result.scalars().all()
    
    return OpeningBalanceResponse(
        id=opening_balance.id,
        client_id=opening_balance.client_id,
        import_date=opening_balance.import_date,
        fiscal_year=opening_balance.fiscal_year,
        description=opening_balance.description,
        status=opening_balance.status.value,
        is_balanced=opening_balance.is_balanced,
        balance_difference=opening_balance.balance_difference,
        bank_balance_verified=opening_balance.bank_balance_verified,
        total_debit=opening_balance.total_debit,
        total_credit=opening_balance.total_credit,
        line_count=opening_balance.line_count,
        lines=[
            OpeningBalanceLineResponse(
                id=line.id,
                line_number=line.line_number,
                account_number=line.account_number,
                account_name=line.account_name,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                account_exists=line.account_exists,
                is_bank_account=line.is_bank_account,
                bank_balance_match=line.bank_balance_match,
                expected_bank_balance=line.expected_bank_balance,
                validation_errors=line.validation_errors,
            )
            for line in lines
        ],
        validation_errors=opening_balance.validation_errors,
        bank_balance_errors=opening_balance.bank_balance_errors,
        missing_accounts=opening_balance.missing_accounts,
        original_filename=opening_balance.original_filename,
        created_at=opening_balance.created_at,
        imported_at=opening_balance.imported_at,
        journal_entry_id=opening_balance.journal_entry_id,
    )


@router.get("/preview/{opening_balance_id}", response_model=OpeningBalancePreviewResponse)
async def preview_opening_balance(
    opening_balance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 3: Preview opening balance before import
    
    Shows:
    - All accounts with balances
    - Validation status
    - Errors/warnings
    - Whether import is allowed
    """
    # Get opening balance
    result = await db.execute(
        select(OpeningBalance).where(OpeningBalance.id == opening_balance_id)
    )
    opening_balance = result.scalar_one_or_none()
    if not opening_balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opening balance {opening_balance_id} not found"
        )
    
    # Get lines
    result = await db.execute(
        select(OpeningBalanceLine)
        .where(OpeningBalanceLine.opening_balance_id == opening_balance_id)
        .order_by(OpeningBalanceLine.line_number)
    )
    lines = result.scalars().all()
    
    # Build validation summary
    validation_summary = {
        "balance_check": "passed" if opening_balance.is_balanced else "failed",
        "bank_accounts_check": "passed" if opening_balance.bank_balance_verified else "not_verified",
        "missing_accounts_count": len(opening_balance.missing_accounts) if opening_balance.missing_accounts else 0,
        "total_debit": float(opening_balance.total_debit),
        "total_credit": float(opening_balance.total_credit),
        "difference": float(opening_balance.balance_difference),
    }
    
    # Parse errors and warnings
    errors = []
    warnings = []
    
    if opening_balance.validation_errors:
        for err in opening_balance.validation_errors:
            errors.append(ValidationError(**err))
    
    if opening_balance.bank_balance_errors:
        for err in opening_balance.bank_balance_errors:
            errors.append(ValidationError(**err))
    
    # Check for warnings (e.g., bank accounts not verified)
    for line in lines:
        if line.is_bank_account and line.bank_balance_match is None:
            warnings.append(ValidationError(
                severity="warning",
                code="BANK_NOT_VERIFIED",
                message=f"Bank account {line.account_number} not verified",
                account_number=line.account_number
            ))
    
    # Can import only if valid status and no errors
    can_import = (
        opening_balance.status == OpeningBalanceStatus.VALID and
        len(errors) == 0
    )
    
    return OpeningBalancePreviewResponse(
        opening_balance=OpeningBalanceResponse(
            id=opening_balance.id,
            client_id=opening_balance.client_id,
            import_date=opening_balance.import_date,
            fiscal_year=opening_balance.fiscal_year,
            description=opening_balance.description,
            status=opening_balance.status.value,
            is_balanced=opening_balance.is_balanced,
            balance_difference=opening_balance.balance_difference,
            bank_balance_verified=opening_balance.bank_balance_verified,
            total_debit=opening_balance.total_debit,
            total_credit=opening_balance.total_credit,
            line_count=opening_balance.line_count,
            lines=[
                OpeningBalanceLineResponse(
                    id=line.id,
                    line_number=line.line_number,
                    account_number=line.account_number,
                    account_name=line.account_name,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    account_exists=line.account_exists,
                    is_bank_account=line.is_bank_account,
                    bank_balance_match=line.bank_balance_match,
                    expected_bank_balance=line.expected_bank_balance,
                    validation_errors=line.validation_errors,
                )
                for line in lines
            ],
            validation_errors=opening_balance.validation_errors,
            bank_balance_errors=opening_balance.bank_balance_errors,
            missing_accounts=opening_balance.missing_accounts,
            original_filename=opening_balance.original_filename,
            created_at=opening_balance.created_at,
            imported_at=opening_balance.imported_at,
            journal_entry_id=opening_balance.journal_entry_id,
        ),
        validation_summary=validation_summary,
        can_import=can_import,
        errors=errors,
        warnings=warnings,
    )


@router.post("/import-to-ledger/{opening_balance_id}", response_model=OpeningBalanceImportResponse)
async def import_to_ledger(
    opening_balance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 4: Import opening balance to general ledger
    
    - Creates journal entry with source_type="opening_balance"
    - Locks entry (cannot be edited)
    - Marks opening balance as imported
    
    Only allowed if validation passed.
    """
    # Get opening balance
    result = await db.execute(
        select(OpeningBalance).where(OpeningBalance.id == opening_balance_id)
    )
    opening_balance = result.scalar_one_or_none()
    if not opening_balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opening balance {opening_balance_id} not found"
        )
    
    # Check status
    if opening_balance.status != OpeningBalanceStatus.VALID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Opening balance not validated. Status: {opening_balance.status.value}"
        )
    
    if opening_balance.status == OpeningBalanceStatus.IMPORTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Opening balance already imported"
        )
    
    # CRITICAL: Block if not balanced
    if not opening_balance.is_balanced:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot import: Opening balance not balanced. Difference: {opening_balance.balance_difference} NOK"
        )
    
    # Get lines
    result = await db.execute(
        select(OpeningBalanceLine)
        .where(OpeningBalanceLine.opening_balance_id == opening_balance_id)
        .order_by(OpeningBalanceLine.line_number)
    )
    lines = result.scalars().all()
    
    # Generate voucher number
    result = await db.execute(
        select(GeneralLedger)
        .where(
            and_(
                GeneralLedger.client_id == opening_balance.client_id,
                GeneralLedger.voucher_series == "IB"  # IB = Ingående Balans (Opening Balance)
            )
        )
        .order_by(GeneralLedger.voucher_number.desc())
    )
    last_entry = result.scalar_one_or_none()
    
    if last_entry:
        try:
            last_number = int(last_entry.voucher_number.split('-')[-1])
            voucher_number = f"{opening_balance.fiscal_year}-{last_number + 1:04d}"
        except (ValueError, IndexError):
            voucher_number = f"{opening_balance.fiscal_year}-0001"
    else:
        voucher_number = f"{opening_balance.fiscal_year}-0001"
    
    # Create general ledger entry
    gl_entry = GeneralLedger(
        id=uuid.uuid4(),
        client_id=opening_balance.client_id,
        entry_date=opening_balance.import_date,
        accounting_date=opening_balance.import_date,
        period=opening_balance.import_date.strftime("%Y-%m"),
        fiscal_year=int(opening_balance.fiscal_year),
        voucher_number=voucher_number,
        voucher_series="IB",  # Opening Balance series
        description=opening_balance.description,
        source_type="opening_balance",
        source_id=opening_balance.id,
        created_by_type="user",  # TODO: Get from auth context
        status="posted",
        locked=True,  # LOCKED - cannot be edited
    )
    
    db.add(gl_entry)
    await db.flush()
    
    # Create lines
    for line in lines:
        gl_line = GeneralLedgerLine(
            id=uuid.uuid4(),
            general_ledger_id=gl_entry.id,
            line_number=line.line_number,
            account_number=line.account_number,
            debit_amount=line.debit_amount,
            credit_amount=line.credit_amount,
            line_description=line.account_name,
        )
        db.add(gl_line)
    
    # Update opening balance
    opening_balance.status = OpeningBalanceStatus.IMPORTED
    opening_balance.imported_at = datetime.utcnow()
    opening_balance.journal_entry_id = gl_entry.id
    
    await db.commit()
    
    return OpeningBalanceImportResponse(
        opening_balance_id=opening_balance.id,
        journal_entry_id=gl_entry.id,
        voucher_number=voucher_number,
        message=f"Opening balance successfully imported as voucher {voucher_number}"
    )


@router.get("/list/{client_id}", response_model=List[OpeningBalanceResponse])
async def list_opening_balances(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    List all opening balances for a client
    """
    result = await db.execute(
        select(OpeningBalance)
        .where(OpeningBalance.client_id == client_id)
        .order_by(OpeningBalance.created_at.desc())
    )
    opening_balances = result.scalars().all()
    
    return [
        OpeningBalanceResponse(
            id=ob.id,
            client_id=ob.client_id,
            import_date=ob.import_date,
            fiscal_year=ob.fiscal_year,
            description=ob.description,
            status=ob.status.value,
            is_balanced=ob.is_balanced,
            balance_difference=ob.balance_difference,
            bank_balance_verified=ob.bank_balance_verified,
            total_debit=ob.total_debit,
            total_credit=ob.total_credit,
            line_count=ob.line_count,
            original_filename=ob.original_filename,
            created_at=ob.created_at,
            imported_at=ob.imported_at,
            journal_entry_id=ob.journal_entry_id,
        )
        for ob in opening_balances
    ]


@router.delete("/{opening_balance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opening_balance(
    opening_balance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an opening balance (only if not imported)
    """
    result = await db.execute(
        select(OpeningBalance).where(OpeningBalance.id == opening_balance_id)
    )
    opening_balance = result.scalar_one_or_none()
    if not opening_balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opening balance {opening_balance_id} not found"
        )
    
    if opening_balance.status == OpeningBalanceStatus.IMPORTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete imported opening balance"
        )
    
    await db.delete(opening_balance)
    await db.commit()
    
    return None
