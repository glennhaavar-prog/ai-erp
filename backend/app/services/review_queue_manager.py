"""
Review Queue Manager Service
Manages automatic escalation of low-confidence invoices to review queue
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.review_queue import ReviewQueue, ReviewPriority, ReviewStatus, IssueCategory
from app.models.vendor_invoice import VendorInvoice
from app.services.confidence_scoring import calculate_invoice_confidence
from app.services.booking_service import book_vendor_invoice

logger = logging.getLogger(__name__)


class ReviewQueueManager:
    """
    Håndterer automatisk eskalering til review queue basert på confidence score
    """
    
    AUTO_APPROVE_THRESHOLD = 85  # >85% = auto-post
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_invoice_with_confidence(
        self,
        invoice_id: UUID,
        booking_suggestion: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prosesser faktura med confidence scoring
        
        Flow:
        1. Beregn confidence score
        2. Hvis >85%: Auto-approve og book til GL
        3. Hvis <85%: Send til review queue
        
        Returns:
            {
                'success': bool,
                'action': 'auto_approved' | 'needs_review',
                'confidence': int,
                'review_queue_id': str (if needs review),
                'general_ledger_id': str (if auto approved)
            }
        """
        try:
            # 1. Fetch invoice
            query = select(VendorInvoice).where(VendorInvoice.id == invoice_id)
            result = await self.db.execute(query)
            invoice = result.scalar_one_or_none()
            
            if not invoice:
                return {'success': False, 'error': 'Invoice not found'}
            
            # 2. Calculate confidence
            confidence_result = await calculate_invoice_confidence(
                db=self.db,
                invoice=invoice,
                booking_suggestion=booking_suggestion
            )
            
            total_score = confidence_result['total_score']
            should_auto_approve = confidence_result['should_auto_approve']
            
            # Update invoice with confidence
            invoice.ai_confidence_score = total_score
            invoice.ai_booking_suggestion = booking_suggestion
            invoice.ai_reasoning = confidence_result['reasoning']
            
            # 3. Decision: Auto-approve or escalate
            if should_auto_approve:
                # Auto-approve and book to GL
                booking_result = await book_vendor_invoice(
                    db=self.db,
                    invoice_id=invoice_id,
                    booking_suggestion=booking_suggestion,
                    created_by_type="ai_agent"
                )
                
                if booking_result['success']:
                    invoice.review_status = 'auto_approved'
                    await self.db.commit()
                    
                    logger.info(
                        f"Invoice {invoice_id} auto-approved with confidence {total_score}%"
                    )
                    
                    return {
                        'success': True,
                        'action': 'auto_approved',
                        'confidence': total_score,
                        'confidence_breakdown': confidence_result['breakdown'],
                        'reasoning': confidence_result['reasoning'],
                        'general_ledger_id': booking_result['general_ledger_id'],
                        'voucher_number': booking_result['voucher_number']
                    }
                else:
                    # Booking failed, escalate to review
                    logger.warning(
                        f"Invoice {invoice_id} booking failed despite high confidence: "
                        f"{booking_result.get('error')}"
                    )
                    should_auto_approve = False
            
            # 4. Escalate to review queue
            if not should_auto_approve:
                review_item = await self._create_review_item(
                    invoice=invoice,
                    booking_suggestion=booking_suggestion,
                    confidence_result=confidence_result
                )
                
                invoice.review_status = 'needs_review'
                await self.db.commit()
                
                logger.info(
                    f"Invoice {invoice_id} escalated to review queue with confidence {total_score}%"
                )
                
                return {
                    'success': True,
                    'action': 'needs_review',
                    'confidence': total_score,
                    'confidence_breakdown': confidence_result['breakdown'],
                    'reasoning': confidence_result['reasoning'],
                    'review_queue_id': str(review_item.id),
                    'priority': review_item.priority.value
                }
        
        except Exception as e:
            logger.error(f"Error processing invoice {invoice_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    async def _create_review_item(
        self,
        invoice: VendorInvoice,
        booking_suggestion: Dict[str, Any],
        confidence_result: Dict[str, Any]
    ) -> ReviewQueue:
        """
        Opprett review queue item for faktura
        """
        confidence = confidence_result['total_score']
        
        # Determine priority based on confidence and amount
        if confidence < 40:
            priority = ReviewPriority.HIGH
        elif confidence < 60:
            priority = ReviewPriority.MEDIUM
        else:
            priority = ReviewPriority.LOW
        
        # Determine issue category
        issue_category = self._determine_issue_category(invoice, confidence_result)
        
        # Generate issue description
        issue_description = self._generate_issue_description(invoice, confidence_result)
        
        review_item = ReviewQueue(
            id=uuid4(),
            client_id=invoice.client_id,
            source_type='vendor_invoice',
            source_id=invoice.id,
            priority=priority,
            status=ReviewStatus.PENDING,
            issue_category=issue_category,
            issue_description=issue_description,
            ai_suggestion=booking_suggestion,
            ai_confidence=confidence,
            ai_reasoning=confidence_result['reasoning']
        )
        
        self.db.add(review_item)
        return review_item
    
    def _determine_issue_category(
        self,
        invoice: VendorInvoice,
        confidence_result: Dict[str, Any]
    ) -> IssueCategory:
        """
        Bestem issue category basert på hva som trekker confidence ned
        """
        breakdown = confidence_result.get('breakdown', {})
        
        # Check vendor familiarity
        if breakdown.get('vendor_familiarity', 0) == 0:
            return IssueCategory.UNKNOWN_VENDOR
        
        # Check VAT validation
        if breakdown.get('vat_validation', 0) < 10:
            return IssueCategory.MISSING_VAT
        
        # Check amount
        if breakdown.get('amount_reasonableness', 0) == 0:
            return IssueCategory.UNUSUAL_AMOUNT
        
        # Check historical similarity
        if breakdown.get('historical_similarity', 0) < 10:
            return IssueCategory.UNCLEAR_DESCRIPTION
        
        # Default
        return IssueCategory.LOW_CONFIDENCE
    
    def _generate_issue_description(
        self,
        invoice: VendorInvoice,
        confidence_result: Dict[str, Any]
    ) -> str:
        """
        Generer human-readable beskrivelse av hvorfor fakturaen trenger review
        """
        confidence = confidence_result['total_score']
        breakdown = confidence_result.get('breakdown', {})
        
        description_parts = [
            f"AI confidence: {confidence}%"
        ]
        
        # Add specific issues
        if breakdown.get('vendor_familiarity', 0) == 0:
            description_parts.append("⚠️ Ny leverandør uten historikk")
        elif breakdown.get('vendor_familiarity', 0) < 10:
            description_parts.append("⚠️ Få tidligere fakturaer fra leverandør")
        
        if breakdown.get('vat_validation', 0) < 10:
            description_parts.append("⚠️ MVA-avvik detektert")
        
        if breakdown.get('amount_reasonableness', 0) == 0:
            description_parts.append(f"⚠️ Uvanlig stort beløp ({invoice.total_amount:,.2f} {invoice.currency})")
        
        if breakdown.get('historical_similarity', 0) < 10:
            description_parts.append("⚠️ Kontering avviker fra tidligere fakturaer")
        
        return " | ".join(description_parts)


async def process_invoice_for_review(
    db: AsyncSession,
    invoice_id: UUID,
    booking_suggestion: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function for processing invoice with confidence scoring
    """
    manager = ReviewQueueManager(db)
    return await manager.process_invoice_with_confidence(
        invoice_id=invoice_id,
        booking_suggestion=booking_suggestion
    )
