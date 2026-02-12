"""
Bank Matching Service - PowerOffice Design Compatible

Implements 4 matching categories with confidence scoring:
1. KID - Exact KID number matching (Norwegian payment ID)
2. Bilagsnummer - Match by voucher number in description
3. Beløp - Match by exact amount with date tolerance
4. Kombinasjon - Multiple criteria combination matching

Confidence scoring: 0-100% per match
Algorithm priority:
1. KID exact match (highest priority, 100% if matched)
2. Voucher number in description (95% if matched)
3. Amount ±1 NOK + date ±3 days (80-90% range)
4. Fuzzy text matching (60-80% range)
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
import re
from difflib import SequenceMatcher
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.bank_transaction import BankTransaction
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.voucher import Voucher


@dataclass
class BankMatchResult:
    """Result of a matching attempt"""
    bank_transaction_id: str
    matched_voucher_id: Optional[str]
    matched_gl_line_id: Optional[str]
    category: str  # "kid", "bilagsnummer", "beløp", "kombinasjon"
    confidence: float  # 0-100
    reason: str
    suggested_entries: List[Dict[str, Any]]  # Backup suggestions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bank_transaction_id": self.bank_transaction_id,
            "matched_voucher_id": self.matched_voucher_id,
            "matched_gl_line_id": self.matched_gl_line_id,
            "category": self.category,
            "confidence": round(self.confidence, 2),
            "reason": self.reason,
            "suggested_entries": self.suggested_entries,
        }


class BankMatchingService:
    """Service for intelligent bank transaction matching"""
    
    # KID validation: Norwegian standard 2-15 digit number
    KID_PATTERN = re.compile(r'\b\d{2,15}\b')
    
    # Voucher number patterns (typically 5-10 digits)
    VOUCHER_PATTERN = re.compile(r'#?(\d{4,10})')
    
    def __init__(self):
        pass
    
    # ===== CATEGORY 1: KID MATCHING =====
    async def match_by_kid(
        self,
        bank_transaction: BankTransaction,
        potential_vouchers: List[Voucher],
        db: Optional[AsyncSession] = None
    ) -> BankMatchResult:
        """
        Match by KID number (Norwegian payment ID).
        KID is typically in the description field.
        
        Norwegian KID format:
        - 2-15 digits
        - Often prefixed with "KID:" or similar
        - Can be in description or reference fields
        """
        
        # Extract KID from transaction description/reference
        transaction_kids = self._extract_kids(bank_transaction.description)
        
        if not transaction_kids:
            return BankMatchResult(
                bank_transaction_id=bank_transaction.id,
                matched_voucher_id=None,
                matched_gl_line_id=None,
                category="kid",
                confidence=0,
                reason="No KID found in transaction",
                suggested_entries=[]
            )
        
        # Look for exact KID match in vouchers
        for voucher in potential_vouchers:
            voucher_kid = self._extract_kid_from_voucher(voucher)
            
            if voucher_kid and voucher_kid in transaction_kids:
                # Verify amount match (within 1 NOK tolerance)
                if abs(float(bank_transaction.amount) - float(voucher.amount)) <= 1.0:
                    return BankMatchResult(
                        bank_transaction_id=bank_transaction.id,
                        matched_voucher_id=voucher.id,
                        matched_gl_line_id=None,
                        category="kid",
                        confidence=100.0,
                        reason=f"Exact KID match: {voucher_kid}",
                        suggested_entries=[self._voucher_to_entry(voucher)]
                    )
        
        # No match found
        return BankMatchResult(
            bank_transaction_id=bank_transaction.id,
            matched_voucher_id=None,
            matched_gl_line_id=None,
            category="kid",
            confidence=0,
            reason=f"No KID match found (found KID: {transaction_kids[0]})",
            suggested_entries=[]
        )
    
    # ===== CATEGORY 2: BILAGSNUMMER (VOUCHER NUMBER) MATCHING =====
    async def match_by_voucher(
        self,
        bank_transaction: BankTransaction,
        potential_vouchers: List[Voucher],
        db: Optional[AsyncSession] = None
    ) -> BankMatchResult:
        """
        Match by voucher number in description.
        Looks for invoice/voucher numbers in the description field.
        """
        
        # Extract voucher number from transaction
        transaction_vouchers = self._extract_voucher_numbers(bank_transaction.description)
        
        if not transaction_vouchers:
            return BankMatchResult(
                bank_transaction_id=bank_transaction.id,
                matched_voucher_id=None,
                matched_gl_line_id=None,
                category="bilagsnummer",
                confidence=0,
                reason="No voucher number found in transaction",
                suggested_entries=[]
            )
        
        # Look for exact voucher match
        for voucher in potential_vouchers:
            for trans_voucher in transaction_vouchers:
                if str(voucher.voucher_number) == str(trans_voucher):
                    # Verify amount match
                    if abs(float(bank_transaction.amount) - float(voucher.amount)) <= 1.0:
                        return BankMatchResult(
                            bank_transaction_id=bank_transaction.id,
                            matched_voucher_id=voucher.id,
                            matched_gl_line_id=None,
                            category="bilagsnummer",
                            confidence=95.0,
                            reason=f"Voucher number match: {trans_voucher}",
                            suggested_entries=[self._voucher_to_entry(voucher)]
                        )
        
        return BankMatchResult(
            bank_transaction_id=bank_transaction.id,
            matched_voucher_id=None,
            matched_gl_line_id=None,
            category="bilagsnummer",
            confidence=0,
            reason=f"No voucher number match found",
            suggested_entries=[]
        )
    
    # ===== CATEGORY 3: BELØP (AMOUNT) MATCHING =====
    async def match_by_amount(
        self,
        bank_transaction: BankTransaction,
        potential_vouchers: List[Voucher],
        db: Optional[AsyncSession] = None
    ) -> BankMatchResult:
        """
        Match by exact amount with date tolerance (±3 days).
        This is the most common matching method.
        
        Matching criteria:
        - Amount within ±1 NOK
        - Date within ±3 days
        """
        
        transaction_amount = Decimal(str(bank_transaction.amount))
        transaction_date = bank_transaction.transaction_date
        
        candidates = []
        
        for voucher in potential_vouchers:
            voucher_amount = Decimal(str(voucher.amount))
            voucher_date = voucher.date
            
            # Check amount tolerance (±1 NOK)
            if abs(transaction_amount - voucher_amount) > Decimal("1.0"):
                continue
            
            # Check date tolerance (±3 days)
            days_diff = abs((transaction_date - voucher_date).days)
            if days_diff > 3:
                continue
            
            # Passed filters, calculate confidence
            amount_match_score = self._calculate_amount_similarity(
                transaction_amount, voucher_amount
            )
            date_penalty = min(days_diff * 3, 10)  # Max 10% penalty for 3+ days
            
            confidence = 90 - date_penalty
            
            candidates.append((voucher, confidence, days_diff))
        
        if not candidates:
            return BankMatchResult(
                bank_transaction_id=bank_transaction.id,
                matched_voucher_id=None,
                matched_gl_line_id=None,
                category="beløp",
                confidence=0,
                reason=f"No amount match found (amount: {transaction_amount} NOK)",
                suggested_entries=[]
            )
        
        # Sort by confidence (highest first)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        best_voucher, best_confidence, days_diff = candidates[0]
        
        # Also suggest other high-confidence candidates
        suggested = []
        for voucher, conf, days in candidates[:3]:
            suggested.append(self._voucher_to_entry(voucher, conf))
        
        return BankMatchResult(
            bank_transaction_id=bank_transaction.id,
            matched_voucher_id=best_voucher.id,
            matched_gl_line_id=None,
            category="beløp",
            confidence=best_confidence,
            reason=f"Amount match: {transaction_amount} NOK, {days_diff} days difference",
            suggested_entries=suggested
        )
    
    # ===== CATEGORY 4: KOMBINASJON (COMBINATION) MATCHING =====
    async def match_by_combination(
        self,
        bank_transaction: BankTransaction,
        potential_vouchers: List[Voucher],
        db: Optional[AsyncSession] = None
    ) -> BankMatchResult:
        """
        Match using multiple criteria combination:
        - Amount (most important, 40%)
        - Description similarity (30%)
        - Date proximity (20%)
        - Other fields (10%)
        """
        
        transaction_amount = Decimal(str(bank_transaction.amount))
        transaction_date = bank_transaction.transaction_date
        transaction_desc = bank_transaction.description.lower()
        
        candidates = []
        
        for voucher in potential_vouchers:
            voucher_amount = Decimal(str(voucher.amount))
            voucher_date = voucher.date
            voucher_desc = (voucher.description or "").lower()
            
            # Amount match (40% weight)
            amount_diff = abs(transaction_amount - voucher_amount)
            if amount_diff > Decimal("100"):  # Skip if amount differs by >100 NOK
                continue
            
            amount_score = max(0, 100 - (float(amount_diff) * 10))  # 0-100
            
            # Description similarity (30% weight)
            desc_similarity = self._calculate_text_similarity(
                transaction_desc, voucher_desc
            )
            
            # Date proximity (20% weight)
            days_diff = abs((transaction_date - voucher_date).days)
            date_score = max(0, 100 - (days_diff * 5))
            
            # Vendor/counterparty match (10% weight)
            vendor_score = 50  # Default
            
            # Calculate weighted score
            confidence = (
                (amount_score * 0.40) +
                (desc_similarity * 0.30) +
                (date_score * 0.20) +
                (vendor_score * 0.10)
            )
            
            # Only include if confidence >= 60%
            if confidence >= 60:
                candidates.append((voucher, confidence))
        
        if not candidates:
            return BankMatchResult(
                bank_transaction_id=bank_transaction.id,
                matched_voucher_id=None,
                matched_gl_line_id=None,
                category="kombinasjon",
                confidence=0,
                reason="No combination match found",
                suggested_entries=[]
            )
        
        # Sort by confidence
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        best_voucher, best_confidence = candidates[0]
        
        # Suggest top matches
        suggested = []
        for voucher, conf in candidates[:3]:
            suggested.append(self._voucher_to_entry(voucher, conf))
        
        return BankMatchResult(
            bank_transaction_id=bank_transaction.id,
            matched_voucher_id=best_voucher.id if best_confidence >= 70 else None,
            matched_gl_line_id=None,
            category="kombinasjon",
            confidence=best_confidence,
            reason="Multiple criteria match",
            suggested_entries=suggested
        )
    
    # ===== AUTO-MATCHING (RUNS ALL 4 ALGORITHMS) =====
    async def auto_match(
        self,
        bank_transaction: BankTransaction,
        potential_vouchers: List[Voucher],
        db: Optional[AsyncSession] = None
    ) -> BankMatchResult:
        """
        Run all matching algorithms in priority order:
        1. KID (highest priority)
        2. Voucher number
        3. Amount
        4. Combination
        
        Returns the best match with confidence score.
        """
        
        # Try KID first (highest priority)
        kid_result = await self.match_by_kid(bank_transaction, potential_vouchers, db)
        if kid_result.confidence >= 100:
            return kid_result
        
        # Try voucher number
        voucher_result = await self.match_by_voucher(bank_transaction, potential_vouchers, db)
        if voucher_result.confidence >= 95:
            return voucher_result
        
        # Try amount matching
        amount_result = await self.match_by_amount(bank_transaction, potential_vouchers, db)
        if amount_result.confidence >= 80:
            return amount_result
        
        # Fall back to combination matching
        combo_result = await self.match_by_combination(bank_transaction, potential_vouchers, db)
        
        return combo_result
    
    # ===== HELPER METHODS =====
    
    def _extract_kids(self, text: str) -> List[str]:
        """Extract KID numbers from text"""
        matches = self.KID_PATTERN.findall(text or "")
        # Filter for Norwegian KID length (2-15 digits)
        return [m for m in matches if 2 <= len(m) <= 15]
    
    def _extract_kid_from_voucher(self, voucher: Voucher) -> Optional[str]:
        """Extract KID from voucher reference fields"""
        combined = f"{voucher.description or ''} {voucher.reference or ''}"
        kids = self._extract_kids(combined)
        return kids[0] if kids else None
    
    def _extract_voucher_numbers(self, text: str) -> List[str]:
        """Extract voucher/invoice numbers from text"""
        matches = self.VOUCHER_PATTERN.findall(text or "")
        # Return unique matches
        return list(set(matches))
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using SequenceMatcher.
        Returns 0-100 score.
        """
        if not text1 or not text2:
            return 0
        
        # Normalize texts
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        similarity = SequenceMatcher(None, text1, text2).ratio()
        return similarity * 100
    
    def _calculate_amount_similarity(self, amount1: Decimal, amount2: Decimal) -> float:
        """Calculate amount similarity as percentage (0-100)"""
        if amount1 == amount2:
            return 100
        
        diff = abs(amount1 - amount2)
        max_amount = max(amount1, amount2)
        
        if max_amount == 0:
            return 100
        
        similarity = 1 - (float(diff) / float(max_amount))
        return max(0, similarity * 100)
    
    def _voucher_to_entry(
        self,
        voucher: Voucher,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """Convert voucher to dictionary entry"""
        return {
            "id": voucher.id,
            "voucher_number": voucher.voucher_number,
            "date": voucher.date.isoformat() if voucher.date else None,
            "amount": float(voucher.amount),
            "description": voucher.description,
            "reference": voucher.reference,
            "confidence": round(confidence, 2) if confidence else None,
        }
