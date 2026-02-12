"""
Bank Matching API - PowerOffice Design Compatible

Endpoints for the 4 matching categories:
1. /api/bank/matching/kid - Match by KID number
2. /api/bank/matching/bilagsnummer - Match by voucher number
3. /api/bank/matching/beløp - Match by amount
4. /api/bank/matching/kombinasjon - Match by combination

Each endpoint returns:
- Matched transaction
- Confidence score (0-100%)
- Suggested alternatives
- Reason for match
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from app.services.bank_matching_service import BankMatchingService
from app.models.bank_transaction import BankTransaction
from app.models.voucher import Voucher


router = APIRouter()
matching_service = BankMatchingService()


# ===== REQUEST/RESPONSE MODELS =====

class VoucherMatch(BaseModel):
    """A matched voucher with confidence"""
    id: str
    voucher_number: str
    date: Optional[str] = None
    amount: float
    description: str
    reference: Optional[str] = None
    confidence: Optional[float] = None


class MatchingResult(BaseModel):
    """Result of a matching attempt"""
    bank_transaction_id: str
    matched_voucher_id: Optional[str]
    category: str  # "kid", "bilagsnummer", "beløp", "kombinasjon"
    confidence: float  # 0-100
    reason: str
    primary_match: Optional[VoucherMatch] = None
    suggested_alternatives: List[VoucherMatch] = []


class BankTransactionForMatching(BaseModel):
    """Bank transaction to be matched"""
    id: str
    date: str  # YYYY-MM-DD
    amount: float
    description: str
    reference: Optional[str] = None


class UnmatchedTransaction(BaseModel):
    """Unmatched bank transaction with suggested matches"""
    transaction: BankTransactionForMatching
    kid_match: Optional[MatchingResult] = None
    bilagsnummer_match: Optional[MatchingResult] = None
    beløp_match: Optional[MatchingResult] = None
    kombinasjon_match: Optional[MatchingResult] = None
    best_match: Optional[MatchingResult] = None
    confidence_category: str  # "high" (>90%), "medium" (70-90%), "low" (<70%), "none"


class AutoMatchResponse(BaseModel):
    """Response from auto-matching run"""
    processed: int
    matched_high_confidence: int  # >90%
    matched_medium_confidence: int  # 70-90%
    matched_low_confidence: int  # <70%
    unmatched: int
    items: List[UnmatchedTransaction]


# ===== MATCHING ENDPOINTS =====

@router.post("/api/bank/matching/kid", response_model=MatchingResult)
async def match_by_kid(
    transaction: BankTransactionForMatching,
    client_id: str = Query(...),
    bank_account: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Match by KID number (Norwegian payment ID).
    
    KID is a 2-15 digit number used for Norwegian payments.
    This is the highest priority matching method.
    
    Returns: 100% confidence if KID matches, 0% otherwise.
    """
    
    try:
        # Get unmatched vouchers for this account
        stmt = select(Voucher).where(
            Voucher.client_id == UUID(client_id),
            Voucher.reconciled == False
        )
        result = await db.execute(stmt)
        vouchers = result.scalars().all()
        
        if not vouchers:
            return MatchingResult(
                bank_transaction_id=transaction.id,
                matched_voucher_id=None,
                category="kid",
                confidence=0,
                reason="No unmatched vouchers found",
                suggested_alternatives=[]
            )
        
        # Create bank transaction object for service
        bank_txn = BankTransaction(
            id=transaction.id,
            transaction_date=datetime.fromisoformat(transaction.date).date(),
            amount=Decimal(str(transaction.amount)),
            description=transaction.description,
            reference=transaction.reference
        )
        
        # Run matching
        match_result = await matching_service.match_by_kid(bank_txn, vouchers, db)
        
        # Format response
        primary = None
        suggested = []
        
        if match_result.suggested_entries:
            primary = VoucherMatch(**match_result.suggested_entries[0])
            for entry in match_result.suggested_entries[1:]:
                suggested.append(VoucherMatch(**entry))
        
        return MatchingResult(
            bank_transaction_id=match_result.bank_transaction_id,
            matched_voucher_id=match_result.matched_voucher_id,
            category=match_result.category,
            confidence=match_result.confidence,
            reason=match_result.reason,
            primary_match=primary,
            suggested_alternatives=suggested
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KID matching error: {str(e)}")


@router.post("/api/bank/matching/bilagsnummer", response_model=MatchingResult)
async def match_by_voucher_number(
    transaction: BankTransactionForMatching,
    client_id: str = Query(...),
    bank_account: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Match by voucher number in description.
    
    Looks for invoice/voucher numbers (4-10 digits) in the transaction description.
    High confidence if voucher number is found and amount matches.
    """
    
    try:
        stmt = select(Voucher).where(
            Voucher.client_id == UUID(client_id),
            Voucher.reconciled == False
        )
        result = await db.execute(stmt)
        vouchers = result.scalars().all()
        
        if not vouchers:
            return MatchingResult(
                bank_transaction_id=transaction.id,
                matched_voucher_id=None,
                category="bilagsnummer",
                confidence=0,
                reason="No unmatched vouchers found",
                suggested_alternatives=[]
            )
        
        bank_txn = BankTransaction(
            id=transaction.id,
            transaction_date=datetime.fromisoformat(transaction.date).date(),
            amount=Decimal(str(transaction.amount)),
            description=transaction.description,
            reference=transaction.reference
        )
        
        match_result = await matching_service.match_by_voucher(bank_txn, vouchers, db)
        
        primary = None
        suggested = []
        
        if match_result.suggested_entries:
            primary = VoucherMatch(**match_result.suggested_entries[0])
            for entry in match_result.suggested_entries[1:]:
                suggested.append(VoucherMatch(**entry))
        
        return MatchingResult(
            bank_transaction_id=match_result.bank_transaction_id,
            matched_voucher_id=match_result.matched_voucher_id,
            category=match_result.category,
            confidence=match_result.confidence,
            reason=match_result.reason,
            primary_match=primary,
            suggested_alternatives=suggested
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voucher matching error: {str(e)}")


@router.post("/api/bank/matching/beløp", response_model=MatchingResult)
async def match_by_amount(
    transaction: BankTransactionForMatching,
    client_id: str = Query(...),
    bank_account: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Match by amount with date tolerance.
    
    Criteria:
    - Amount within ±1 NOK
    - Date within ±3 days
    
    This is the most common matching method.
    Confidence: 80-90% depending on date difference.
    """
    
    try:
        stmt = select(Voucher).where(
            Voucher.client_id == UUID(client_id),
            Voucher.reconciled == False
        )
        result = await db.execute(stmt)
        vouchers = result.scalars().all()
        
        if not vouchers:
            return MatchingResult(
                bank_transaction_id=transaction.id,
                matched_voucher_id=None,
                category="beløp",
                confidence=0,
                reason="No unmatched vouchers found",
                suggested_alternatives=[]
            )
        
        bank_txn = BankTransaction(
            id=transaction.id,
            transaction_date=datetime.fromisoformat(transaction.date).date(),
            amount=Decimal(str(transaction.amount)),
            description=transaction.description,
            reference=transaction.reference
        )
        
        match_result = await matching_service.match_by_amount(bank_txn, vouchers, db)
        
        primary = None
        suggested = []
        
        if match_result.suggested_entries:
            primary = VoucherMatch(**match_result.suggested_entries[0])
            for entry in match_result.suggested_entries[1:]:
                suggested.append(VoucherMatch(**entry))
        
        return MatchingResult(
            bank_transaction_id=match_result.bank_transaction_id,
            matched_voucher_id=match_result.matched_voucher_id,
            category=match_result.category,
            confidence=match_result.confidence,
            reason=match_result.reason,
            primary_match=primary,
            suggested_alternatives=suggested
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Amount matching error: {str(e)}")


@router.post("/api/bank/matching/kombinasjon", response_model=MatchingResult)
async def match_by_combination(
    transaction: BankTransactionForMatching,
    client_id: str = Query(...),
    bank_account: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Match using multiple criteria combination.
    
    Scoring (weighted):
    - Amount: 40% (exact or within ±1 NOK)
    - Description similarity: 30% (fuzzy text matching)
    - Date proximity: 20% (within ±7 days)
    - Counterparty: 10% (vendor/customer match)
    
    Minimum confidence: 60%
    """
    
    try:
        stmt = select(Voucher).where(
            Voucher.client_id == UUID(client_id),
            Voucher.reconciled == False
        )
        result = await db.execute(stmt)
        vouchers = result.scalars().all()
        
        if not vouchers:
            return MatchingResult(
                bank_transaction_id=transaction.id,
                matched_voucher_id=None,
                category="kombinasjon",
                confidence=0,
                reason="No unmatched vouchers found",
                suggested_alternatives=[]
            )
        
        bank_txn = BankTransaction(
            id=transaction.id,
            transaction_date=datetime.fromisoformat(transaction.date).date(),
            amount=Decimal(str(transaction.amount)),
            description=transaction.description,
            reference=transaction.reference
        )
        
        match_result = await matching_service.match_by_combination(bank_txn, vouchers, db)
        
        primary = None
        suggested = []
        
        if match_result.suggested_entries:
            primary = VoucherMatch(**match_result.suggested_entries[0])
            for entry in match_result.suggested_entries[1:]:
                suggested.append(VoucherMatch(**entry))
        
        return MatchingResult(
            bank_transaction_id=match_result.bank_transaction_id,
            matched_voucher_id=match_result.matched_voucher_id,
            category=match_result.category,
            confidence=match_result.confidence,
            reason=match_result.reason,
            primary_match=primary,
            suggested_alternatives=suggested
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Combination matching error: {str(e)}")


@router.post("/api/bank/matching/auto", response_model=AutoMatchResponse)
async def auto_match_transactions(
    transactions: List[BankTransactionForMatching],
    client_id: str = Query(...),
    bank_account: str = Query(...),
    min_confidence: float = Query(70, ge=0, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Run automatic matching on multiple bank transactions.
    
    Runs all 4 algorithms in priority order:
    1. KID (highest priority, 100% if matched)
    2. Voucher number (95% if matched)
    3. Amount (80-90%)
    4. Combination (60-100%)
    
    Parameters:
    - min_confidence: Only include matches >= this confidence level (default: 70%)
    
    Returns:
    - Summary statistics
    - Detailed results for each unmatched transaction
    - Suggested matches for manual review
    """
    
    try:
        stmt = select(Voucher).where(
            Voucher.client_id == UUID(client_id),
            Voucher.reconciled == False
        )
        result = await db.execute(stmt)
        vouchers = result.scalars().all()
        
        if not vouchers:
            return AutoMatchResponse(
                processed=len(transactions),
                matched_high_confidence=0,
                matched_medium_confidence=0,
                matched_low_confidence=0,
                unmatched=len(transactions),
                items=[]
            )
        
        items = []
        matched_high = 0
        matched_medium = 0
        matched_low = 0
        
        for txn in transactions:
            bank_txn = BankTransaction(
                id=txn.id,
                transaction_date=datetime.fromisoformat(txn.date).date(),
                amount=Decimal(str(txn.amount)),
                description=txn.description,
                reference=txn.reference
            )
            
            # Run all matching algorithms
            kid_result = await matching_service.match_by_kid(bank_txn, vouchers, db)
            bilag_result = await matching_service.match_by_voucher(bank_txn, vouchers, db)
            beløp_result = await matching_service.match_by_amount(bank_txn, vouchers, db)
            kombin_result = await matching_service.match_by_combination(bank_txn, vouchers, db)
            
            # Find best match
            results = [
                (kid_result, "KID"),
                (bilag_result, "Bilagsnummer"),
                (beløp_result, "Beløp"),
                (kombin_result, "Kombinasjon"),
            ]
            results.sort(key=lambda x: x[0].confidence, reverse=True)
            best_result = results[0][0]
            
            # Count by confidence level
            if best_result.confidence >= 90:
                matched_high += 1
            elif best_result.confidence >= 70:
                matched_medium += 1
            elif best_result.confidence > 0:
                matched_low += 1
            
            # Format for response
            unmatched = UnmatchedTransaction(
                transaction=txn,
                kid_match=_format_match_result(kid_result),
                bilagsnummer_match=_format_match_result(bilag_result),
                beløp_match=_format_match_result(beløp_result),
                kombinasjon_match=_format_match_result(kombin_result),
                best_match=_format_match_result(best_result) if best_result.confidence > 0 else None,
                confidence_category=_get_confidence_category(best_result.confidence)
            )
            
            items.append(unmatched)
        
        return AutoMatchResponse(
            processed=len(transactions),
            matched_high_confidence=matched_high,
            matched_medium_confidence=matched_medium,
            matched_low_confidence=matched_low,
            unmatched=len(transactions) - (matched_high + matched_medium + matched_low),
            items=items
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-matching error: {str(e)}")


# ===== HELPER FUNCTIONS =====

def _format_match_result(match_result) -> Optional[MatchingResult]:
    """Convert service result to API response"""
    if match_result.confidence == 0:
        return None
    
    primary = None
    suggested = []
    
    if match_result.suggested_entries:
        primary = VoucherMatch(**match_result.suggested_entries[0])
        for entry in match_result.suggested_entries[1:]:
            suggested.append(VoucherMatch(**entry))
    
    return MatchingResult(
        bank_transaction_id=match_result.bank_transaction_id,
        matched_voucher_id=match_result.matched_voucher_id,
        category=match_result.category,
        confidence=match_result.confidence,
        reason=match_result.reason,
        primary_match=primary,
        suggested_alternatives=suggested
    )


def _get_confidence_category(confidence: float) -> str:
    """Map confidence score to category"""
    if confidence >= 90:
        return "high"
    elif confidence >= 70:
        return "medium"
    elif confidence > 0:
        return "low"
    else:
        return "none"
