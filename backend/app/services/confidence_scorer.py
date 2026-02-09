"""
Confidence Scoring Service for Kontali ERP
SkatteFUNN AP2: Tillitsmodell med konfidensbasert eskalering

Evaluerer AI-forslag og bestemmer om fakturaer skal auto-godkjennes
eller eskaleres til manuell review.

Versjon: MVP 1.0
Dato: 2026-02-09
"""

import decimal
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Beregner confidence score for AI-analyserte fakturaer.
    
    Score range: 0.0 - 1.0 (100%)
    Threshold: < 0.80 = eskalerer til Review Queue
    """
    
    # Weights for different confidence factors
    WEIGHTS = {
        'ocr_quality': 0.30,      # OCR tekstgjenkjenning kvalitet
        'ai_confidence': 0.35,    # AI model's egen konfidensverdi
        'field_completeness': 0.20,  # Alle påkrevde felt utfylt?
        'amount_validation': 0.15,   # Beløp validerer (MVA-kalkulator stemmer)
    }
    
    # Threshold for automatic approval
    AUTO_APPROVE_THRESHOLD = 0.80  # 80%
    
    def __init__(self):
        self.logger = logger
    
    def calculate_score(
        self, 
        invoice_data: Dict,
        ocr_confidence: Optional[float] = None,
        ai_confidence: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Beregn total confidence score for en faktura.
        
        Args:
            invoice_data: Dict med fakturadata (vendor_name, amount, etc.)
            ocr_confidence: AWS Textract confidence (0.0-1.0)
            ai_confidence: AI model confidence (0.0-1.0)
        
        Returns:
            {
                'total_score': 0.85,
                'should_auto_approve': True,
                'breakdown': {...},
                'recommendation': 'AUTO_APPROVE' | 'MANUAL_REVIEW'
            }
        """
        
        scores = {}
        
        # 1. OCR Quality Score (30%)
        scores['ocr_quality'] = self._score_ocr_quality(ocr_confidence)
        
        # 2. AI Confidence Score (35%)
        scores['ai_confidence'] = self._score_ai_confidence(ai_confidence)
        
        # 3. Field Completeness Score (20%)
        scores['field_completeness'] = self._score_field_completeness(invoice_data)
        
        # 4. Amount Validation Score (15%)
        scores['amount_validation'] = self._score_amount_validation(invoice_data)
        
        # Calculate weighted total
        total_score = sum(
            scores[factor] * self.WEIGHTS[factor]
            for factor in self.WEIGHTS.keys()
        )
        
        # Determine recommendation
        should_auto_approve = total_score >= self.AUTO_APPROVE_THRESHOLD
        recommendation = 'AUTO_APPROVE' if should_auto_approve else 'MANUAL_REVIEW'
        
        result = {
            'total_score': round(total_score, 4),
            'should_auto_approve': should_auto_approve,
            'recommendation': recommendation,
            'threshold': self.AUTO_APPROVE_THRESHOLD,
            'breakdown': scores,
            'calculated_at': datetime.utcnow().isoformat()
        }
        
        # Log decision
        self.logger.info(
            f"Confidence score calculated: {total_score:.2%} "
            f"({recommendation}) for invoice {invoice_data.get('invoice_number', 'unknown')}"
        )
        
        return result
    
    def _score_ocr_quality(self, ocr_confidence: Optional[float]) -> float:
        """
        Score OCR quality fra AWS Textract.
        
        AWS Textract returnerer confidence per felt.
        Vi bruker gjennomsnittlig confidence for alle felt.
        """
        if ocr_confidence is None:
            # Mangler OCR data = lav score
            return 0.5
        
        # OCR confidence er allerede 0.0-1.0
        # Lineær mapping
        return max(0.0, min(1.0, ocr_confidence))
    
    def _score_ai_confidence(self, ai_confidence: Optional[float]) -> float:
        """
        Score AI model's egen konfidensverdi.
        
        Vår AI returnerer confidence når den foreslår konto.
        Høy confidence = AI er sikker på konteringen.
        """
        if ai_confidence is None:
            # Mangler AI confidence = middels score
            return 0.6
        
        # AI confidence allerede 0.0-1.0
        return max(0.0, min(1.0, ai_confidence))
    
    def _score_field_completeness(self, invoice_data: Dict) -> float:
        """
        Score hvor mange påkrevde felt som er fylt ut.
        
        Påkrevde felt:
        - vendor_name
        - invoice_number  
        - invoice_date
        - due_date
        - amount_excl_vat (or amount_ex_vat)
        - vat_amount
        - total_amount
        - suggested_account
        """
        
        required_fields = [
            'vendor_name',
            'invoice_number',
            'invoice_date',
            'due_date',
            'amount_excl_vat',
            'amount_ex_vat',  # Legacy name support
            'vat_amount',
            'total_amount',
            'suggested_account'
        ]
        
        filled_count = sum(
            1 for field in required_fields
            if invoice_data.get(field) is not None and invoice_data.get(field) != ''
        )
        
        completeness = filled_count / len(required_fields)
        
        return completeness
    
    def _score_amount_validation(self, invoice_data: Dict) -> float:
        """
        Valider at beløp henger sammen.
        
        Sjekk:
        1. total_amount = amount_excl_vat + vat_amount
        2. vat_amount ≈ amount_excl_vat * vat_rate (hvis vat_rate oppgitt)
        
        Hvis validering feiler = lav score (krever manuell review)
        """
        
        try:
            # Support both field names (amount_excl_vat and amount_ex_vat)
            amount_ex_vat = Decimal(str(
                invoice_data.get('amount_excl_vat') or invoice_data.get('amount_ex_vat', 0)
            ))
            vat_amount = Decimal(str(invoice_data.get('vat_amount', 0)))
            total_amount = Decimal(str(invoice_data.get('total_amount', 0)))
            
            # Check 1: Total = Ex VAT + VAT
            calculated_total = amount_ex_vat + vat_amount
            tolerance = Decimal('0.50')  # 50 øre tolerance (rounding)
            
            if abs(total_amount - calculated_total) > tolerance:
                # Amount mismatch = low score
                self.logger.warning(
                    f"Amount validation failed: {total_amount} != {calculated_total}"
                )
                return 0.3
            
            # Check 2: VAT calculation (if vat_rate provided)
            vat_rate = invoice_data.get('vat_rate')
            if vat_rate:
                expected_vat = amount_ex_vat * Decimal(str(vat_rate)) / Decimal('100')
                if abs(vat_amount - expected_vat) > tolerance:
                    self.logger.warning(
                        f"VAT calculation mismatch: {vat_amount} != {expected_vat}"
                    )
                    return 0.5
            
            # All validations passed
            return 1.0
            
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            self.logger.error(f"Amount validation error: {e}")
            return 0.0
    
    def get_escalation_reason(self, score_result: Dict) -> str:
        """
        Generer human-readable forklaring på hvorfor faktura eskaleres.
        
        Brukes i Review Queue UI til regnskapsfører.
        """
        
        if score_result['should_auto_approve']:
            return "High confidence - auto-approved"
        
        # Find lowest scoring factor
        breakdown = score_result['breakdown']
        lowest_factor = min(breakdown.items(), key=lambda x: x[1])
        factor_name, factor_score = lowest_factor
        
        reasons = {
            'ocr_quality': f"Low OCR quality ({factor_score:.1%}) - text recognition uncertain",
            'ai_confidence': f"Low AI confidence ({factor_score:.1%}) - uncertain account suggestion",
            'field_completeness': f"Incomplete data ({factor_score:.1%}) - missing required fields",
            'amount_validation': f"Amount validation failed ({factor_score:.1%}) - numbers don't add up",
        }
        
        return reasons.get(factor_name, "Low confidence - manual review required")


# Convenience function for quick scoring
async def score_invoice(
    invoice_data: Dict,
    ocr_confidence: Optional[float] = None,
    ai_confidence: Optional[float] = None
) -> Dict:
    """
    Quick helper function to score an invoice.
    
    Usage:
        result = await score_invoice(invoice_data, ocr_conf=0.95, ai_conf=0.88)
        if result['should_auto_approve']:
            await auto_approve(invoice)
        else:
            await send_to_review_queue(invoice)
    """
    scorer = ConfidenceScorer()
    return scorer.calculate_score(invoice_data, ocr_confidence, ai_confidence)
