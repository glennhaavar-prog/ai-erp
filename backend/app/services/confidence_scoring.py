"""
Confidence Scoring Service
Beregner confidence score (0-100%) for AI-forslag basert på flere faktorer
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.agent_learned_pattern import AgentLearnedPattern
from app.models.correction import Correction

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Beregner confidence score basert på:
    1. Kjente leverandører (vendor familiarity)
    2. Lignende tidligere bilag (historical similarity)
    3. MVA-logikk (VAT validation)
    4. Pattern matching (learned patterns)
    5. Amount reasonableness
    """
    
    # Confidence thresholds
    AUTO_APPROVE_THRESHOLD = 85  # >85% = auto-post
    NEEDS_REVIEW_THRESHOLD = 85  # <85% = send til review queue
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_confidence(
        self,
        invoice: VendorInvoice,
        booking_suggestion: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Beregn total confidence score med delscorer
        
        Returns:
            {
                'total_score': int (0-100),
                'breakdown': {
                    'vendor_familiarity': int (0-30),
                    'historical_similarity': int (0-30),
                    'vat_validation': int (0-20),
                    'pattern_matching': int (0-15),
                    'amount_reasonableness': int (0-5)
                },
                'reasoning': str,
                'should_auto_approve': bool
            }
        """
        try:
            scores = {}
            
            # 1. Vendor Familiarity (0-30 points)
            scores['vendor_familiarity'] = await self._score_vendor_familiarity(invoice)
            
            # 2. Historical Similarity (0-30 points)
            scores['historical_similarity'] = await self._score_historical_similarity(invoice, booking_suggestion)
            
            # 3. VAT Validation (0-20 points)
            scores['vat_validation'] = await self._score_vat_validation(invoice, booking_suggestion)
            
            # 4. Pattern Matching (0-15 points)
            scores['pattern_matching'] = await self._score_pattern_matching(invoice, booking_suggestion)
            
            # 5. Amount Reasonableness (0-5 points)
            scores['amount_reasonableness'] = await self._score_amount_reasonableness(invoice)
            
            # Calculate total
            total_score = sum(scores.values())
            
            # Generate reasoning
            reasoning = self._generate_reasoning(scores, invoice)
            
            return {
                'total_score': min(100, total_score),  # Cap at 100
                'breakdown': scores,
                'reasoning': reasoning,
                'should_auto_approve': total_score >= self.AUTO_APPROVE_THRESHOLD
            }
        
        except Exception as e:
            logger.error(f"Error calculating confidence for invoice {invoice.id}: {str(e)}", exc_info=True)
            return {
                'total_score': 0,
                'breakdown': {},
                'reasoning': f'Error calculating confidence: {str(e)}',
                'should_auto_approve': False
            }
    
    async def _score_vendor_familiarity(self, invoice: VendorInvoice) -> int:
        """
        Score 0-30 basert på hvor godt vi kjenner leverandøren
        - 30: >20 fakturaer siste år
        - 20: 10-20 fakturaer
        - 10: 3-9 fakturaer
        - 5: 1-2 fakturaer
        - 0: Ny leverandør
        """
        if not invoice.vendor_id:
            return 0
        
        # Count invoices from this vendor last 12 months
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        query = select(func.count(VendorInvoice.id)).where(
            and_(
                VendorInvoice.vendor_id == invoice.vendor_id,
                VendorInvoice.client_id == invoice.client_id,
                VendorInvoice.invoice_date >= one_year_ago.date(),
                VendorInvoice.id != invoice.id  # Exclude current invoice
            )
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        
        if count > 20:
            return 30
        elif count >= 10:
            return 20
        elif count >= 3:
            return 10
        elif count >= 1:
            return 5
        else:
            return 0
    
    async def _score_historical_similarity(
        self,
        invoice: VendorInvoice,
        booking_suggestion: Dict[str, Any]
    ) -> int:
        """
        Score 0-30 basert på hvor lik denne fakturaen er til tidligere fakturaer
        fra samme leverandør
        """
        if not invoice.vendor_id:
            return 0
        
        # Find similar invoices from same vendor
        query = select(VendorInvoice).where(
            and_(
                VendorInvoice.vendor_id == invoice.vendor_id,
                VendorInvoice.client_id == invoice.client_id,
                VendorInvoice.general_ledger_id.isnot(None),  # Only booked invoices
                VendorInvoice.id != invoice.id
            )
        ).order_by(VendorInvoice.invoice_date.desc()).limit(10)
        
        result = await self.db.execute(query)
        similar_invoices = result.scalars().all()
        
        if not similar_invoices:
            return 0
        
        # Check if booking suggestion matches any historical booking
        similarity_scores = []
        
        for similar_invoice in similar_invoices:
            if not similar_invoice.general_ledger_id:
                continue
            
            # Fetch GL entry for similar invoice
            gl_query = select(GeneralLedger).where(
                GeneralLedger.id == similar_invoice.general_ledger_id
            )
            gl_result = await self.db.execute(gl_query)
            gl_entry = gl_result.scalar_one_or_none()
            
            if gl_entry and gl_entry.lines:
                # Compare account numbers
                suggested_accounts = set(
                    line.get('account') for line in booking_suggestion.get('lines', [])
                )
                historical_accounts = set(
                    line.account_number for line in gl_entry.lines
                )
                
                if suggested_accounts and historical_accounts:
                    match_ratio = len(suggested_accounts & historical_accounts) / len(suggested_accounts)
                    similarity_scores.append(match_ratio)
        
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            return int(avg_similarity * 30)
        
        return 0
    
    async def _score_vat_validation(
        self,
        invoice: VendorInvoice,
        booking_suggestion: Dict[str, Any]
    ) -> int:
        """
        Score 0-20 basert på MVA-logikk
        - Stemmer MVA-beløp?
        - Er MVA-koder gyldige?
        - Er MVA-konto korrekt?
        """
        score = 0
        
        # Check if VAT amount matches
        suggested_vat_total = sum(
            Decimal(str(line.get('vat_amount', 0)))
            for line in booking_suggestion.get('lines', [])
        )
        
        actual_vat = invoice.vat_amount
        
        if abs(suggested_vat_total - actual_vat) < Decimal('0.01'):
            score += 10  # VAT amount matches
        
        # Check if VAT codes are present where expected
        lines_with_vat = [
            line for line in booking_suggestion.get('lines', [])
            if line.get('vat_code')
        ]
        
        if lines_with_vat and len(lines_with_vat) > 0:
            score += 5  # VAT codes are present
        
        # Check if 2700 (VAT payable) account is used correctly
        vat_payable_lines = [
            line for line in booking_suggestion.get('lines', [])
            if str(line.get('account', '')).startswith('2700')
        ]
        
        if vat_payable_lines:
            vat_payable_amount = sum(
                Decimal(str(line.get('credit', 0))) - Decimal(str(line.get('debit', 0)))
                for line in vat_payable_lines
            )
            
            if abs(vat_payable_amount - actual_vat) < Decimal('0.01'):
                score += 5  # VAT payable account is correct
        
        return score
    
    async def _score_pattern_matching(
        self,
        invoice: VendorInvoice,
        booking_suggestion: Dict[str, Any]
    ) -> int:
        """
        Score 0-15 basert på hvor godt forslaget matcher lærte patterns
        """
        if not invoice.vendor_id:
            return 0
        
        # Find learned patterns that apply to this client
        query = select(AgentLearnedPattern).where(
            and_(
                or_(
                    AgentLearnedPattern.global_pattern == True,
                    AgentLearnedPattern.applies_to_clients.contains([invoice.client_id])
                ),
                AgentLearnedPattern.is_active == True
            )
        ).order_by(AgentLearnedPattern.times_applied.desc()).limit(5)
        
        result = await self.db.execute(query)
        patterns = result.scalars().all()
        
        if not patterns:
            return 0
        
        # Check if booking suggestion matches any pattern
        for pattern in patterns:
            trigger = pattern.trigger or {}
            action = pattern.action or {}
            
            # Simple pattern matching based on vendor and accounts
            if trigger.get('vendor_id') == str(invoice.vendor_id):
                suggested_accounts = set(
                    line.get('account') for line in booking_suggestion.get('lines', [])
                )
                pattern_accounts = set(action.get('accounts', []))
                
                if suggested_accounts == pattern_accounts:
                    # Exact match
                    return 15
                elif suggested_accounts & pattern_accounts:
                    # Partial match
                    return 8
        
        return 0
    
    async def _score_amount_reasonableness(self, invoice: VendorInvoice) -> int:
        """
        Score 0-5 basert på om beløpet er rimelig
        - 5: Normalt beløp (<100k NOK)
        - 3: Middels stort beløp (100k-500k)
        - 0: Veldig stort beløp (>500k)
        """
        amount = invoice.total_amount
        
        if amount < 100000:
            return 5
        elif amount < 500000:
            return 3
        else:
            return 0
    
    def _generate_reasoning(
        self,
        scores: Dict[str, int],
        invoice: VendorInvoice
    ) -> str:
        """
        Generer human-readable reasoning for confidence score
        """
        reasons = []
        
        # Vendor familiarity
        if scores['vendor_familiarity'] >= 20:
            reasons.append("Kjent leverandør med mange tidligere fakturaer")
        elif scores['vendor_familiarity'] >= 10:
            reasons.append("Leverandør med noen tidligere fakturaer")
        elif scores['vendor_familiarity'] > 0:
            reasons.append("Leverandør med få tidligere fakturaer")
        else:
            reasons.append("Ny leverandør uten historikk")
        
        # Historical similarity
        if scores['historical_similarity'] >= 20:
            reasons.append("Lignende kontering som tidligere fakturaer")
        elif scores['historical_similarity'] >= 10:
            reasons.append("Delvis lik tidligere konteringer")
        
        # VAT validation
        if scores['vat_validation'] >= 15:
            reasons.append("MVA-logikk validert OK")
        elif scores['vat_validation'] >= 10:
            reasons.append("MVA-beløp stemmer")
        elif scores['vat_validation'] < 10:
            reasons.append("⚠️ MVA-avvik detektert")
        
        # Pattern matching
        if scores['pattern_matching'] >= 10:
            reasons.append("Matcher lært mønster")
        
        # Amount
        if scores['amount_reasonableness'] < 3:
            reasons.append("⚠️ Uvanlig stort beløp")
        
        return " | ".join(reasons)


async def calculate_invoice_confidence(
    db: AsyncSession,
    invoice: VendorInvoice,
    booking_suggestion: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function for calculating confidence
    """
    scorer = ConfidenceScorer(db)
    return await scorer.calculate_confidence(invoice, booking_suggestion)
