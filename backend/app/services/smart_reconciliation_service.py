"""
Smart Reconciliation Service - Fuzzy Matching for Bank Transactions

Features:
1. Fuzzy match bank transactions to journal entries/invoices
2. Match criteria:
   - Amount (±1% tolerance)
   - Date (±3 days)
   - Description similarity (Levenshtein distance, 80%+)
3. Auto-suggest matches in bank reconciliation page
4. Support KID number matching (Norwegian payment reference)

Uses Levenshtein distance for text matching.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from datetime import datetime, timedelta
import uuid
from decimal import Decimal
import difflib

from app.models import (
    BankTransaction,
    VendorInvoice,
    CustomerInvoice,
    GeneralLedger,
    GeneralLedgerLine,
    Vendor
)


class ReconciliationMatch:
    """Represents a potential match between bank transaction and invoice/ledger"""
    def __init__(
        self,
        bank_transaction_id: uuid.UUID,
        matched_entity_type: str,  # "vendor_invoice" | "customer_invoice" | "ledger_entry"
        matched_entity_id: uuid.UUID,
        confidence: int,  # 0-100
        match_reason: str,
        details: Dict[str, Any] = None
    ):
        self.bank_transaction_id = bank_transaction_id
        self.matched_entity_type = matched_entity_type
        self.matched_entity_id = matched_entity_id
        self.confidence = confidence
        self.match_reason = match_reason
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bank_transaction_id": str(self.bank_transaction_id),
            "matched_entity_type": self.matched_entity_type,
            "matched_entity_id": str(self.matched_entity_id),
            "confidence": self.confidence,
            "match_reason": self.match_reason,
            "details": self.details
        }


class SmartReconciliationService:
    """
    Smart Reconciliation Service
    
    Uses fuzzy matching to suggest reconciliation matches
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Match configuration
        self.amount_tolerance_pct = 1.0  # ±1%
        self.date_tolerance_days = 3  # ±3 days
        self.description_similarity_threshold = 0.80  # 80%
        self.kid_match_confidence = 95  # High confidence for KID matches
    
    def calculate_levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein (edit) distance between two strings
        
        Returns number of edits needed to transform s1 into s2
        """
        if len(s1) < len(s2):
            return self.calculate_levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two texts (0.0 - 1.0)
        
        Uses Levenshtein distance normalized by length
        """
        if not text1 or not text2:
            return 0.0
        
        text1_clean = text1.lower().strip()
        text2_clean = text2.lower().strip()
        
        if text1_clean == text2_clean:
            return 1.0
        
        # Calculate Levenshtein distance
        distance = self.calculate_levenshtein_distance(text1_clean, text2_clean)
        max_len = max(len(text1_clean), len(text2_clean))
        
        if max_len == 0:
            return 0.0
        
        # Normalize to 0-1 similarity
        similarity = 1.0 - (distance / max_len)
        return max(0.0, similarity)
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison
        
        Removes extra spaces, converts to lowercase, removes special chars
        """
        import re
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.lower()
    
    async def find_matches_for_transaction(
        self,
        transaction: BankTransaction,
        limit: int = 5
    ) -> List[ReconciliationMatch]:
        """
        Find potential matches for a bank transaction
        
        Returns sorted list of matches (best first)
        """
        matches = []
        
        # 1. Try KID number match (highest priority)
        if transaction.kid_number:
            kid_matches = await self._match_by_kid(transaction)
            matches.extend(kid_matches)
        
        # 2. Match vendor invoices (for outgoing payments)
        if transaction.transaction_type.value == "debit":
            vendor_matches = await self._match_vendor_invoices(transaction)
            matches.extend(vendor_matches)
        
        # 3. Match customer invoices (for incoming payments)
        elif transaction.transaction_type.value == "credit":
            customer_matches = await self._match_customer_invoices(transaction)
            matches.extend(customer_matches)
        
        # 4. Match general ledger entries
        ledger_matches = await self._match_ledger_entries(transaction)
        matches.extend(ledger_matches)
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda m: m.confidence, reverse=True)
        
        return matches[:limit]
    
    async def _match_by_kid(
        self,
        transaction: BankTransaction
    ) -> List[ReconciliationMatch]:
        """
        Match by KID number (Norwegian payment reference)
        
        This is the most reliable matching method
        """
        matches = []
        
        if not transaction.kid_number:
            return matches
        
        # Search vendor invoices with matching KID/reference
        query = select(VendorInvoice).where(
            and_(
                VendorInvoice.client_id == transaction.client_id,
                VendorInvoice.invoice_number == transaction.kid_number
            )
        )
        
        result = await self.db.execute(query)
        invoices = result.scalars().all()
        
        for invoice in invoices:
            # Amount check (±1%)
            amount_match = self._check_amount_match(
                float(transaction.amount),
                float(invoice.total_amount)
            )
            
            if amount_match['matches']:
                matches.append(ReconciliationMatch(
                    bank_transaction_id=transaction.id,
                    matched_entity_type="vendor_invoice",
                    matched_entity_id=invoice.id,
                    confidence=self.kid_match_confidence,
                    match_reason=f"KID number match: {transaction.kid_number}",
                    details={
                        "invoice_number": invoice.invoice_number,
                        "amount_transaction": float(transaction.amount),
                        "amount_invoice": float(invoice.total_amount),
                        "amount_diff_pct": amount_match['diff_pct']
                    }
                ))
        
        return matches
    
    async def _match_vendor_invoices(
        self,
        transaction: BankTransaction
    ) -> List[ReconciliationMatch]:
        """
        Match transaction to vendor invoices
        
        For outgoing payments (debits)
        """
        matches = []
        
        # Get candidate invoices (±3 days, similar amount)
        date_from = transaction.transaction_date - timedelta(days=self.date_tolerance_days)
        date_to = transaction.transaction_date + timedelta(days=self.date_tolerance_days)
        
        amount = abs(float(transaction.amount))
        amount_min = amount * (1 - self.amount_tolerance_pct / 100)
        amount_max = amount * (1 + self.amount_tolerance_pct / 100)
        
        query = select(VendorInvoice).where(
            and_(
                VendorInvoice.client_id == transaction.client_id,
                VendorInvoice.due_date.between(date_from, date_to),
                VendorInvoice.total_amount.between(Decimal(str(amount_min)), Decimal(str(amount_max))),
                VendorInvoice.payment_status != "paid"  # Not already paid
            )
        ).limit(10)
        
        result = await self.db.execute(query)
        invoices = result.scalars().all()
        
        for invoice in invoices:
            # Get vendor for name matching
            if invoice.vendor_id:
                vendor_result = await self.db.execute(
                    select(Vendor).where(Vendor.id == invoice.vendor_id)
                )
                vendor = vendor_result.scalar_one_or_none()
            else:
                vendor = None
            
            # Calculate match score
            confidence, reason = self._calculate_match_confidence(
                transaction=transaction,
                invoice_amount=float(invoice.total_amount),
                invoice_date=invoice.due_date,
                counterparty_name=vendor.name if vendor else None
            )
            
            if confidence >= 60:  # Minimum threshold
                matches.append(ReconciliationMatch(
                    bank_transaction_id=transaction.id,
                    matched_entity_type="vendor_invoice",
                    matched_entity_id=invoice.id,
                    confidence=confidence,
                    match_reason=reason,
                    details={
                        "invoice_number": invoice.invoice_number,
                        "vendor_name": vendor.name if vendor else "Unknown",
                        "amount": float(invoice.total_amount),
                        "due_date": invoice.due_date.isoformat()
                    }
                ))
        
        return matches
    
    async def _match_customer_invoices(
        self,
        transaction: BankTransaction
    ) -> List[ReconciliationMatch]:
        """
        Match transaction to customer invoices
        
        For incoming payments (credits)
        """
        matches = []
        
        # Similar logic to vendor invoices
        date_from = transaction.transaction_date - timedelta(days=self.date_tolerance_days)
        date_to = transaction.transaction_date + timedelta(days=self.date_tolerance_days)
        
        amount = abs(float(transaction.amount))
        amount_min = amount * (1 - self.amount_tolerance_pct / 100)
        amount_max = amount * (1 + self.amount_tolerance_pct / 100)
        
        query = select(CustomerInvoice).where(
            and_(
                CustomerInvoice.client_id == transaction.client_id,
                CustomerInvoice.due_date.between(date_from, date_to),
                CustomerInvoice.total_amount.between(Decimal(str(amount_min)), Decimal(str(amount_max))),
                CustomerInvoice.payment_status != "paid"
            )
        ).limit(10)
        
        result = await self.db.execute(query)
        invoices = result.scalars().all()
        
        for invoice in invoices:
            confidence, reason = self._calculate_match_confidence(
                transaction=transaction,
                invoice_amount=float(invoice.total_amount),
                invoice_date=invoice.due_date,
                counterparty_name=transaction.counterparty_name
            )
            
            if confidence >= 60:
                matches.append(ReconciliationMatch(
                    bank_transaction_id=transaction.id,
                    matched_entity_type="customer_invoice",
                    matched_entity_id=invoice.id,
                    confidence=confidence,
                    match_reason=reason,
                    details={
                        "invoice_number": invoice.invoice_number,
                        "amount": float(invoice.total_amount),
                        "due_date": invoice.due_date.isoformat()
                    }
                ))
        
        return matches
    
    async def _match_ledger_entries(
        self,
        transaction: BankTransaction
    ) -> List[ReconciliationMatch]:
        """
        Match transaction to general ledger entries
        
        Fallback for transactions without invoices
        """
        matches = []
        
        # Get recent ledger entries with similar amounts
        date_from = transaction.transaction_date - timedelta(days=self.date_tolerance_days)
        date_to = transaction.transaction_date + timedelta(days=self.date_tolerance_days)
        
        amount = abs(float(transaction.amount))
        amount_min = amount * (1 - self.amount_tolerance_pct / 100)
        amount_max = amount * (1 + self.amount_tolerance_pct / 100)
        
        # Search general ledger
        query = select(GeneralLedger).where(
            and_(
                GeneralLedger.client_id == transaction.client_id,
                GeneralLedger.entry_date.between(date_from, date_to)
            )
        ).limit(20)
        
        result = await self.db.execute(query)
        entries = result.scalars().all()
        
        for entry in entries:
            # Check if any line matches amount
            for line in entry.lines:
                line_amount = abs(float(line.debit or 0) - float(line.credit or 0))
                amount_match = self._check_amount_match(amount, line_amount)
                
                if amount_match['matches']:
                    # Calculate text similarity
                    similarity = 0.0
                    if transaction.description and entry.description:
                        similarity = self.calculate_text_similarity(
                            transaction.description,
                            entry.description
                        )
                    
                    confidence = int(70 * amount_match['score'] + 30 * similarity)
                    
                    if confidence >= 60:
                        matches.append(ReconciliationMatch(
                            bank_transaction_id=transaction.id,
                            matched_entity_type="ledger_entry",
                            matched_entity_id=entry.id,
                            confidence=confidence,
                            match_reason=f"Amount and date match (similarity: {similarity:.0%})",
                            details={
                                "voucher_number": entry.voucher_number,
                                "description": entry.description,
                                "amount": line_amount
                            }
                        ))
        
        return matches
    
    def _check_amount_match(
        self,
        amount1: float,
        amount2: float
    ) -> Dict[str, Any]:
        """
        Check if two amounts match within tolerance
        
        Returns dict with 'matches' bool and 'diff_pct' float
        """
        amount1_abs = abs(amount1)
        amount2_abs = abs(amount2)
        
        if amount1_abs == 0 or amount2_abs == 0:
            return {'matches': False, 'diff_pct': 100.0, 'score': 0.0}
        
        diff_pct = abs(amount1_abs - amount2_abs) / max(amount1_abs, amount2_abs) * 100
        matches = diff_pct <= self.amount_tolerance_pct
        
        # Score: 1.0 for exact match, decreasing with difference
        score = max(0.0, 1.0 - (diff_pct / self.amount_tolerance_pct))
        
        return {
            'matches': matches,
            'diff_pct': diff_pct,
            'score': score
        }
    
    def _calculate_match_confidence(
        self,
        transaction: BankTransaction,
        invoice_amount: float,
        invoice_date: datetime,
        counterparty_name: Optional[str] = None
    ) -> Tuple[int, str]:
        """
        Calculate overall match confidence
        
        Returns (confidence_score, reason_text)
        """
        scores = []
        reasons = []
        
        # Amount similarity (40% weight)
        amount_match = self._check_amount_match(
            float(transaction.amount),
            invoice_amount
        )
        if amount_match['matches']:
            amount_score = amount_match['score'] * 40
            scores.append(amount_score)
            reasons.append(f"amount match ({amount_match['diff_pct']:.1f}% diff)")
        else:
            return (0, "Amount mismatch")
        
        # Date proximity (30% weight)
        date_diff = abs((transaction.transaction_date.date() - invoice_date).days)
        if date_diff <= self.date_tolerance_days:
            date_score = (1.0 - date_diff / self.date_tolerance_days) * 30
            scores.append(date_score)
            reasons.append(f"{date_diff} days apart")
        else:
            return (0, "Date outside range")
        
        # Description/name similarity (30% weight)
        if counterparty_name and transaction.counterparty_name:
            text_similarity = self.calculate_text_similarity(
                transaction.counterparty_name,
                counterparty_name
            )
            if text_similarity >= self.description_similarity_threshold:
                text_score = text_similarity * 30
                scores.append(text_score)
                reasons.append(f"name match ({text_similarity:.0%})")
        
        total_confidence = int(sum(scores))
        reason_text = ", ".join(reasons)
        
        return (total_confidence, reason_text)
    
    async def apply_match(
        self,
        match: ReconciliationMatch
    ) -> bool:
        """
        Apply a reconciliation match
        
        Updates transaction and invoice status
        """
        # Get transaction
        result = await self.db.execute(
            select(BankTransaction).where(BankTransaction.id == match.bank_transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            return False
        
        # Update transaction
        transaction.ai_matched_invoice_id = match.matched_entity_id
        transaction.ai_match_confidence = Decimal(str(match.confidence))
        transaction.ai_match_reason = match.match_reason
        transaction.status = "matched"
        transaction.updated_at = datetime.utcnow()
        
        # Update invoice payment status using PaymentStatusService
        from app.services.payment_status_service import PaymentStatusService
        
        if match.matched_entity_type == "vendor_invoice":
            try:
                await PaymentStatusService.update_vendor_invoice_payment(
                    db=self.db,
                    invoice_id=match.matched_entity_id,
                    payment_amount=abs(transaction.amount),
                    payment_date=transaction.transaction_date.date(),
                    transaction_id=transaction.id
                )
            except Exception as e:
                print(f"Error updating vendor invoice payment status: {e}")
        
        elif match.matched_entity_type == "customer_invoice":
            try:
                await PaymentStatusService.update_customer_invoice_payment(
                    db=self.db,
                    invoice_id=match.matched_entity_id,
                    payment_amount=abs(transaction.amount),
                    payment_date=transaction.transaction_date.date(),
                    transaction_id=transaction.id
                )
            except Exception as e:
                print(f"Error updating customer invoice payment status: {e}")
        
        await self.db.commit()
        return True


# Helper functions
async def find_transaction_matches(
    db: AsyncSession,
    transaction_id: uuid.UUID,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Find matches for a transaction
    """
    result = await db.execute(
        select(BankTransaction).where(BankTransaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        return []
    
    service = SmartReconciliationService(db)
    matches = await service.find_matches_for_transaction(transaction, limit)
    
    return [m.to_dict() for m in matches]


async def auto_reconcile_transactions(
    db: AsyncSession,
    client_id: uuid.UUID,
    confidence_threshold: int = 90
) -> Dict[str, Any]:
    """
    Auto-reconcile all unmatched transactions above confidence threshold
    
    Returns summary of matches made
    """
    service = SmartReconciliationService(db)
    
    # Get unmatched transactions
    result = await db.execute(
        select(BankTransaction).where(
            and_(
                BankTransaction.client_id == client_id,
                BankTransaction.status == "unmatched"
            )
        )
    )
    transactions = result.scalars().all()
    
    matched_count = 0
    suggestions_count = 0
    
    for transaction in transactions:
        matches = await service.find_matches_for_transaction(transaction, limit=1)
        
        if matches and matches[0].confidence >= confidence_threshold:
            # Auto-apply high-confidence matches
            success = await service.apply_match(matches[0])
            if success:
                matched_count += 1
        elif matches:
            # Store as suggestion for manual review
            suggestions_count += 1
    
    return {
        "total_transactions": len(transactions),
        "auto_matched": matched_count,
        "suggestions_pending": suggestions_count
    }
