"""
Bank Reconciliation Service
Match bank transactions to invoices/vouchers using AI and fuzzy matching
"""
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from difflib import SequenceMatcher

from app.models.bank_transaction import BankTransaction, TransactionType, TransactionStatus
from app.models.bank_reconciliation import BankReconciliation, MatchType, MatchStatus
from app.models.vendor_invoice import VendorInvoice
from app.models.customer_invoice import CustomerInvoice
from app.models.vendor import Vendor
import logging
import json

logger = logging.getLogger(__name__)


class BankReconciliationService:
    """Service for automatic and manual bank reconciliation"""
    
    # Confidence thresholds
    CONFIDENCE_AUTO_MATCH = 85.0
    CONFIDENCE_SUGGEST = 50.0
    
    @staticmethod
    async def find_matches(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        client_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Find potential matches for a bank transaction
        
        Args:
            db: Database session
            transaction_id: Bank transaction UUID
            client_id: Client UUID
            
        Returns:
            List of potential matches with confidence scores
        """
        # Get transaction
        stmt = select(BankTransaction).where(BankTransaction.id == transaction_id)
        result = await db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            return []
        
        # Find candidates based on transaction type
        candidates = []
        
        if transaction.transaction_type == TransactionType.DEBIT:
            # Money out = likely vendor invoice payment
            candidates = await BankReconciliationService._find_vendor_invoice_matches(
                db, transaction, client_id
            )
        else:
            # Money in = likely customer invoice payment
            candidates = await BankReconciliationService._find_customer_invoice_matches(
                db, transaction, client_id
            )
        
        # Sort by confidence
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        
        return candidates
    
    @staticmethod
    async def _find_vendor_invoice_matches(
        db: AsyncSession,
        transaction: BankTransaction,
        client_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Find vendor invoice matches for a debit transaction"""
        # Query unpaid vendor invoices around the same date and amount
        date_min = transaction.transaction_date - timedelta(days=3)
        date_max = transaction.transaction_date + timedelta(days=3)
        amount_min = transaction.amount * Decimal('0.99')  # ±1%
        amount_max = transaction.amount * Decimal('1.01')
        
        stmt = (
            select(VendorInvoice)
            .where(
                and_(
                    VendorInvoice.client_id == client_id,
                    VendorInvoice.payment_status != 'paid',
                    VendorInvoice.total_amount >= amount_min,
                    VendorInvoice.total_amount <= amount_max,
                )
            )
            .limit(20)
        )
        
        result = await db.execute(stmt)
        invoices = result.scalars().all()
        
        candidates = []
        for invoice in invoices:
            # Calculate match confidence
            confidence, reason, criteria = await BankReconciliationService._calculate_match_confidence(
                db, transaction, invoice, 'vendor'
            )
            
            if confidence >= BankReconciliationService.CONFIDENCE_SUGGEST:
                candidates.append({
                    'type': 'vendor_invoice',
                    'invoice_id': str(invoice.id),
                    'invoice': invoice.to_dict(),
                    'confidence': float(confidence),
                    'reason': reason,
                    'criteria': criteria,
                    'amount_difference': float(transaction.amount - invoice.total_amount),
                })
        
        return candidates
    
    @staticmethod
    async def _find_customer_invoice_matches(
        db: AsyncSession,
        transaction: BankTransaction,
        client_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Find customer invoice matches for a credit transaction"""
        # Query unpaid customer invoices
        date_min = transaction.transaction_date - timedelta(days=3)
        date_max = transaction.transaction_date + timedelta(days=3)
        amount_min = transaction.amount * Decimal('0.99')
        amount_max = transaction.amount * Decimal('1.01')
        
        stmt = (
            select(CustomerInvoice)
            .where(
                and_(
                    CustomerInvoice.client_id == client_id,
                    CustomerInvoice.payment_status != 'paid',
                    CustomerInvoice.total_amount >= amount_min,
                    CustomerInvoice.total_amount <= amount_max,
                )
            )
            .limit(20)
        )
        
        result = await db.execute(stmt)
        invoices = result.scalars().all()
        
        candidates = []
        for invoice in invoices:
            confidence, reason, criteria = await BankReconciliationService._calculate_match_confidence(
                db, transaction, invoice, 'customer'
            )
            
            if confidence >= BankReconciliationService.CONFIDENCE_SUGGEST:
                candidates.append({
                    'type': 'customer_invoice',
                    'invoice_id': str(invoice.id),
                    'invoice': invoice.to_dict(),
                    'confidence': float(confidence),
                    'reason': reason,
                    'criteria': criteria,
                    'amount_difference': float(transaction.amount - invoice.total_amount),
                })
        
        return candidates
    
    @staticmethod
    async def _calculate_match_confidence(
        db: AsyncSession,
        transaction: BankTransaction,
        invoice: Any,
        invoice_type: str
    ) -> Tuple[Decimal, str, Dict[str, Any]]:
        """
        Calculate confidence score for a potential match
        
        Returns:
            (confidence_score, reason, criteria_dict)
        """
        confidence = Decimal('0.00')
        reasons = []
        criteria = {}
        
        # 1. Amount match (40 points max)
        amount_diff = abs(transaction.amount - invoice.total_amount)
        if amount_diff == 0:
            confidence += Decimal('40.00')
            reasons.append("Exact amount match")
            criteria['amount_match'] = 'exact'
        elif amount_diff <= Decimal('0.01'):
            confidence += Decimal('38.00')
            reasons.append("Amount match within 1 øre")
            criteria['amount_match'] = 'near_exact'
        elif amount_diff <= (invoice.total_amount * Decimal('0.01')):
            confidence += Decimal('30.00')
            reasons.append("Amount match within 1%")
            criteria['amount_match'] = 'close'
        else:
            confidence += Decimal('10.00')
            criteria['amount_match'] = 'poor'
        
        # 2. Date proximity (30 points max)
        date_diff = abs((transaction.transaction_date.date() - invoice.due_date).days)
        if date_diff == 0:
            confidence += Decimal('30.00')
            reasons.append("Same date as due date")
            criteria['date_match'] = 'exact'
        elif date_diff <= 1:
            confidence += Decimal('25.00')
            reasons.append("Within 1 day of due date")
            criteria['date_match'] = 'very_close'
        elif date_diff <= 3:
            confidence += Decimal('20.00')
            reasons.append("Within 3 days of due date")
            criteria['date_match'] = 'close'
        elif date_diff <= 7:
            confidence += Decimal('10.00')
            criteria['date_match'] = 'acceptable'
        else:
            confidence += Decimal('5.00')
            criteria['date_match'] = 'far'
        
        # 3. KID number match (20 points max)
        if transaction.kid_number and hasattr(invoice, 'kid_number') and invoice.kid_number:
            if transaction.kid_number == invoice.kid_number:
                confidence += Decimal('20.00')
                reasons.append("KID number match")
                criteria['kid_match'] = True
        
        # 4. Invoice number in description (10 points max)
        if invoice.invoice_number and invoice.invoice_number in transaction.description:
            confidence += Decimal('10.00')
            reasons.append("Invoice number found in description")
            criteria['invoice_number_match'] = True
        
        # 5. Vendor/Customer name fuzzy match (20 points max)
        if invoice_type == 'vendor' and invoice.vendor:
            # Load vendor
            stmt = select(Vendor).where(Vendor.id == invoice.vendor_id)
            result = await db.execute(stmt)
            vendor = result.scalar_one_or_none()
            
            if vendor and transaction.counterparty_name:
                similarity = BankReconciliationService._string_similarity(
                    transaction.counterparty_name.lower(),
                    vendor.name.lower()
                )
                if similarity > 0.8:
                    confidence += Decimal('20.00')
                    reasons.append(f"Vendor name match ({int(similarity*100)}%)")
                    criteria['vendor_name_similarity'] = float(similarity)
                elif similarity > 0.6:
                    confidence += Decimal('15.00')
                    criteria['vendor_name_similarity'] = float(similarity)
                elif similarity > 0.4:
                    confidence += Decimal('10.00')
                    criteria['vendor_name_similarity'] = float(similarity)
        
        # Build reason string
        reason_str = "; ".join(reasons) if reasons else "Low confidence match"
        
        return confidence, reason_str, criteria
    
    @staticmethod
    def _string_similarity(str1: str, str2: str) -> float:
        """Calculate string similarity using SequenceMatcher"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    @staticmethod
    async def auto_match_transaction(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        client_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt automatic matching for a transaction
        
        Returns:
            Match info if auto-match succeeded, None otherwise
        """
        matches = await BankReconciliationService.find_matches(db, transaction_id, client_id)
        
        if not matches:
            return None
        
        best_match = matches[0]
        
        # Only auto-match if confidence is high enough
        if best_match['confidence'] < BankReconciliationService.CONFIDENCE_AUTO_MATCH:
            logger.info(f"Best match confidence {best_match['confidence']} below threshold {BankReconciliationService.CONFIDENCE_AUTO_MATCH}")
            return None
        
        # Create reconciliation record
        reconciliation = BankReconciliation(
            client_id=client_id,
            transaction_id=transaction_id,
            vendor_invoice_id=uuid.UUID(best_match['invoice_id']) if best_match['type'] == 'vendor_invoice' else None,
            customer_invoice_id=uuid.UUID(best_match['invoice_id']) if best_match['type'] == 'customer_invoice' else None,
            match_type=MatchType.AUTO,
            match_status=MatchStatus.APPROVED,  # Auto-approve high confidence matches
            confidence_score=Decimal(str(best_match['confidence'])),
            match_reason=best_match['reason'],
            match_criteria=json.dumps(best_match['criteria']),
            transaction_amount=best_match['invoice']['total_amount'],
            voucher_amount=best_match['invoice']['total_amount'],
            amount_difference=Decimal(str(best_match['amount_difference'])),
            matched_at=BankReconciliationService._now(),
            approved_at=BankReconciliationService._now(),
        )
        
        db.add(reconciliation)
        
        # Update transaction status
        stmt = select(BankTransaction).where(BankTransaction.id == transaction_id)
        result = await db.execute(stmt)
        transaction = result.scalar_one()
        transaction.status = TransactionStatus.MATCHED
        
        await db.commit()
        
        logger.info(f"Auto-matched transaction {transaction_id} with confidence {best_match['confidence']}")
        
        return {
            'reconciliation_id': str(reconciliation.id),
            'match': best_match,
        }
    
    @staticmethod
    async def create_manual_match(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        invoice_id: uuid.UUID,
        invoice_type: str,
        client_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Create a manual match between transaction and invoice
        
        Args:
            db: Database session
            transaction_id: Bank transaction UUID
            invoice_id: Invoice UUID
            invoice_type: 'vendor' or 'customer'
            client_id: Client UUID
            user_id: User who created the match
            
        Returns:
            Created reconciliation record
        """
        # Get transaction
        stmt = select(BankTransaction).where(BankTransaction.id == transaction_id)
        result = await db.execute(stmt)
        transaction = result.scalar_one()
        
        # Get invoice
        if invoice_type == 'vendor':
            stmt = select(VendorInvoice).where(VendorInvoice.id == invoice_id)
            result = await db.execute(stmt)
            invoice = result.scalar_one()
        else:
            stmt = select(CustomerInvoice).where(CustomerInvoice.id == invoice_id)
            result = await db.execute(stmt)
            invoice = result.scalar_one()
        
        # Create reconciliation
        reconciliation = BankReconciliation(
            client_id=client_id,
            transaction_id=transaction_id,
            vendor_invoice_id=invoice_id if invoice_type == 'vendor' else None,
            customer_invoice_id=invoice_id if invoice_type == 'customer' else None,
            match_type=MatchType.MANUAL,
            match_status=MatchStatus.APPROVED,
            confidence_score=Decimal('100.00'),  # Manual matches are 100% confident
            match_reason="Manually matched by user",
            transaction_amount=transaction.amount,
            voucher_amount=invoice.total_amount,
            amount_difference=transaction.amount - invoice.total_amount,
            matched_by_user_id=user_id,
            matched_at=BankReconciliationService._now(),
            approved_by_user_id=user_id,
            approved_at=BankReconciliationService._now(),
        )
        
        db.add(reconciliation)
        
        # Update transaction status
        transaction.status = TransactionStatus.MATCHED
        
        # Update invoice payment status
        invoice.payment_status = 'paid'
        invoice.paid_amount = invoice.total_amount
        invoice.payment_date = transaction.transaction_date.date()
        
        await db.commit()
        
        return reconciliation.to_dict()
    
    @staticmethod
    async def get_reconciliation_stats(
        db: AsyncSession,
        client_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get reconciliation statistics for a client"""
        # Count transactions by status
        stmt = select(BankTransaction).where(BankTransaction.client_id == client_id)
        result = await db.execute(stmt)
        transactions = result.scalars().all()
        
        total = len(transactions)
        matched = sum(1 for t in transactions if t.status == TransactionStatus.MATCHED)
        unmatched = sum(1 for t in transactions if t.status == TransactionStatus.UNMATCHED)
        reviewed = sum(1 for t in transactions if t.status == TransactionStatus.REVIEWED)
        
        # Count reconciliations by type
        stmt = select(BankReconciliation).where(BankReconciliation.client_id == client_id)
        result = await db.execute(stmt)
        reconciliations = result.scalars().all()
        
        auto_matches = sum(1 for r in reconciliations if r.match_type == MatchType.AUTO)
        manual_matches = sum(1 for r in reconciliations if r.match_type == MatchType.MANUAL)
        
        return {
            'total_transactions': total,
            'matched': matched,
            'unmatched': unmatched,
            'reviewed': reviewed,
            'auto_match_rate': round((auto_matches / total * 100) if total > 0 else 0, 2),
            'manual_match_count': manual_matches,
            'auto_match_count': auto_matches,
        }
    
    @staticmethod
    def _now():
        """Get current UTC datetime"""
        from datetime import datetime
        return datetime.utcnow()
