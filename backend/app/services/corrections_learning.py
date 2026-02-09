"""
Corrections Learning Service
Lærer fra regnskapsfører's korreksjoner og oppretter patterns
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime
from decimal import Decimal

from app.models.correction import Correction
from app.models.review_queue import ReviewQueue, ReviewStatus
from app.models.vendor_invoice import VendorInvoice
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.agent_learned_pattern import AgentLearnedPattern

logger = logging.getLogger(__name__)


class CorrectionsLearner:
    """
    Lærer fra korreksjoner og oppretter patterns for fremtidig bruk
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_correction(
        self,
        review_queue_id: UUID,
        corrected_booking: Dict[str, Any],
        correction_reason: Optional[str],
        corrected_by_user_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """
        Lagre en korreksjon og lær fra den
        
        Args:
            review_queue_id: ID til review queue item
            corrected_booking: Korrekt kontering (med lines)
            correction_reason: Forklaring fra regnskapsfører
            corrected_by_user_id: Hvem som korrigerte
        
        Returns:
            {
                'success': bool,
                'correction_id': str,
                'pattern_created': bool,
                'similar_items_corrected': int
            }
        """
        try:
            # 1. Fetch review queue item
            rq_query = select(ReviewQueue).where(ReviewQueue.id == review_queue_id)
            rq_result = await self.db.execute(rq_query)
            review_item = rq_result.scalar_one_or_none()
            
            if not review_item:
                return {'success': False, 'error': 'Review item not found'}
            
            # 2. Fetch the invoice
            invoice_query = select(VendorInvoice).where(VendorInvoice.id == review_item.source_id)
            invoice_result = await self.db.execute(invoice_query)
            invoice = invoice_result.scalar_one_or_none()
            
            if not invoice:
                return {'success': False, 'error': 'Invoice not found'}
            
            # 3. Create General Ledger entry with corrected booking
            from app.services.booking_service import _generate_voucher_number
            
            voucher_number = await _generate_voucher_number(self.db, invoice.client_id)
            
            gl_entry = GeneralLedger(
                id=uuid4(),
                client_id=invoice.client_id,
                entry_date=datetime.now().date(),
                accounting_date=invoice.invoice_date,
                period=invoice.invoice_date.strftime("%Y-%m"),
                fiscal_year=invoice.invoice_date.year,
                voucher_number=voucher_number,
                voucher_series="AP",
                description=f"Leverandørfaktura {invoice.invoice_number} - {invoice.vendor.name if invoice.vendor else 'Ukjent'} (KORRIGERT)",
                source_type="vendor_invoice",
                source_id=invoice.id,
                created_by_type="user",
                created_by_id=corrected_by_user_id,
                status="posted",
                locked=False
            )
            
            self.db.add(gl_entry)
            
            # 4. Create GL lines from corrected booking
            for idx, line in enumerate(corrected_booking.get('lines', []), start=1):
                gl_line = GeneralLedgerLine(
                    id=uuid4(),
                    general_ledger_id=gl_entry.id,
                    line_number=idx,
                    account_number=str(line.get('account', '')),
                    debit_amount=Decimal(str(line.get('debit', 0))),
                    credit_amount=Decimal(str(line.get('credit', 0))),
                    vat_code=str(line.get('vat_code', '')) if line.get('vat_code') else None,
                    vat_amount=Decimal(str(line.get('vat_amount', 0))) if line.get('vat_amount') else Decimal(0),
                    line_description=line.get('description', '')
                )
                self.db.add(gl_line)
            
            # 5. Create Correction record
            correction = Correction(
                id=uuid4(),
                tenant_id=invoice.client_id,
                review_queue_id=review_queue_id,
                journal_entry_id=gl_entry.id,
                original_entry=review_item.ai_suggestion or {},
                corrected_entry=corrected_booking,
                correction_reason=correction_reason,
                corrected_by=corrected_by_user_id
            )
            
            self.db.add(correction)
            
            # 6. Update review queue status
            review_item.status = ReviewStatus.CORRECTED
            review_item.resolved_at = datetime.utcnow()
            review_item.resolved_by_user_id = corrected_by_user_id
            review_item.resolution_notes = correction_reason
            
            # 7. Link invoice to GL entry
            invoice.general_ledger_id = gl_entry.id
            invoice.booked_at = datetime.utcnow()
            invoice.review_status = 'corrected'
            
            await self.db.commit()
            await self.db.refresh(correction)
            
            # 8. Try to learn a pattern
            pattern_created = await self._try_create_pattern(correction, invoice)
            
            # 9. Apply pattern to similar pending items
            similar_corrected = 0
            if pattern_created:
                similar_corrected = await self._apply_pattern_to_similar(correction, invoice)
            
            logger.info(
                f"Correction recorded: {correction.id}, pattern_created={pattern_created}, "
                f"similar_corrected={similar_corrected}"
            )
            
            return {
                'success': True,
                'correction_id': str(correction.id),
                'pattern_created': pattern_created,
                'similar_items_corrected': similar_corrected,
                'general_ledger_id': str(gl_entry.id),
                'voucher_number': f"{gl_entry.voucher_series}-{voucher_number}"
            }
        
        except Exception as e:
            logger.error(f"Error recording correction: {str(e)}", exc_info=True)
            await self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    async def _try_create_pattern(
        self,
        correction: Correction,
        invoice: VendorInvoice
    ) -> bool:
        """
        Forsøk å opprette et pattern basert på korreksjonen
        
        Pattern opprettes hvis:
        - Leverandør er kjent
        - Det finnes en tydelig forskjell mellom original og korrigert
        """
        try:
            if not invoice.vendor_id:
                return False
            
            original = correction.original_entry or {}
            corrected = correction.corrected_entry or {}
            
            original_lines = original.get('lines', [])
            corrected_lines = corrected.get('lines', [])
            
            if not original_lines or not corrected_lines:
                return False
            
            # Extract key differences
            original_accounts = set(line.get('account') for line in original_lines)
            corrected_accounts = set(line.get('account') for line in corrected_lines)
            
            # Check if there's a significant change
            if original_accounts == corrected_accounts:
                # Same accounts, probably just amount adjustments
                return False
            
            # Create pattern
            pattern_data = {
                'vendor_id': str(invoice.vendor_id),
                'vendor_name': invoice.vendor.name if invoice.vendor else None,
                'original_accounts': list(original_accounts),
                'corrected_accounts': list(corrected_accounts),
                'accounts': list(corrected_accounts),  # Use corrected accounts for matching
                'correction_reason': correction.correction_reason,
                'sample_booking': corrected_lines
            }
            
            # Check if similar pattern already exists
            existing_query = select(AgentLearnedPattern).where(
                and_(
                    AgentLearnedPattern.pattern_type == 'vendor_correction',
                    AgentLearnedPattern.is_active == True
                )
            )
            
            existing_result = await self.db.execute(existing_query)
            existing_patterns = existing_result.scalars().all()
            
            # Check for duplicate
            for existing in existing_patterns:
                existing_data = existing.pattern_data or {}
                if (existing_data.get('vendor_id') == pattern_data['vendor_id'] and
                    set(existing_data.get('corrected_accounts', [])) == corrected_accounts):
                    logger.info(f"Pattern already exists for vendor {invoice.vendor_id}")
                    return False
            
            # Create new pattern
            pattern = AgentLearnedPattern(
                id=uuid4(),
                pattern_type='vendor_correction',
                pattern_name=f"Correction for {invoice.vendor.name if invoice.vendor else 'vendor'}",
                description=f"Learned from correction: {correction.correction_reason}",
                trigger=pattern_data,
                action={'accounts': list(corrected_accounts)},
                applies_to_clients=[invoice.client_id],
                global_pattern=False,
                confidence_boost=10,  # Boost confidence by 10% when this pattern matches
                is_active=True,
                times_applied=0,
                success_rate=Decimal('1.0'),
                learned_from_user_id=correction.corrected_by
            )
            
            self.db.add(pattern)
            await self.db.commit()
            
            logger.info(f"Created new pattern {pattern.id} from correction {correction.id}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating pattern: {str(e)}", exc_info=True)
            return False
    
    async def _apply_pattern_to_similar(
        self,
        correction: Correction,
        invoice: VendorInvoice
    ) -> int:
        """
        Anvend det lærte patternet på lignende pending items
        
        Returns:
            Antall items som ble automatisk korrigert
        """
        try:
            if not invoice.vendor_id:
                return 0
            
            # Find similar pending items from same vendor
            similar_query = select(ReviewQueue).where(
                and_(
                    ReviewQueue.client_id == invoice.client_id,
                    ReviewQueue.status == ReviewStatus.PENDING,
                    ReviewQueue.source_type == 'vendor_invoice',
                    ReviewQueue.id != correction.review_queue_id
                )
            )
            
            similar_result = await self.db.execute(similar_query)
            similar_items = similar_result.scalars().all()
            
            corrected_count = 0
            
            for item in similar_items:
                # Fetch the invoice for this item
                inv_query = select(VendorInvoice).where(VendorInvoice.id == item.source_id)
                inv_result = await self.db.execute(inv_query)
                similar_invoice = inv_result.scalar_one_or_none()
                
                if not similar_invoice or similar_invoice.vendor_id != invoice.vendor_id:
                    continue
                
                # Apply the same correction
                corrected_booking = correction.corrected_entry.copy()
                
                # Adjust amounts to match the similar invoice
                amount_ratio = similar_invoice.total_amount / invoice.total_amount
                
                for line in corrected_booking.get('lines', []):
                    if line.get('debit'):
                        line['debit'] = float(Decimal(str(line['debit'])) * Decimal(str(amount_ratio)))
                    if line.get('credit'):
                        line['credit'] = float(Decimal(str(line['credit'])) * Decimal(str(amount_ratio)))
                    if line.get('vat_amount'):
                        line['vat_amount'] = float(Decimal(str(line['vat_amount'])) * Decimal(str(amount_ratio)))
                
                # Record correction for similar item
                result = await self.record_correction(
                    review_queue_id=item.id,
                    corrected_booking=corrected_booking,
                    correction_reason=f"Auto-korrigert basert på læring fra {invoice.invoice_number}",
                    corrected_by_user_id=correction.corrected_by
                )
                
                if result.get('success'):
                    corrected_count += 1
                    
                    # Update correction with batch info
                    if corrected_count == 1:
                        batch_id = uuid4()
                        correction.batch_id = batch_id
                    
                    # Link to batch
                    correction_id = result.get('correction_id')
                    if correction_id:
                        batch_correction_query = select(Correction).where(
                            Correction.id == UUID(correction_id)
                        )
                        batch_correction_result = await self.db.execute(batch_correction_query)
                        batch_correction = batch_correction_result.scalar_one_or_none()
                        if batch_correction:
                            batch_correction.batch_id = correction.batch_id
            
            # Update original correction with count
            if corrected_count > 0:
                correction.similar_corrected = corrected_count
                await self.db.commit()
            
            logger.info(f"Applied pattern to {corrected_count} similar items")
            return corrected_count
        
        except Exception as e:
            logger.error(f"Error applying pattern to similar items: {str(e)}", exc_info=True)
            return 0


async def record_invoice_correction(
    db: AsyncSession,
    review_queue_id: UUID,
    corrected_booking: Dict[str, Any],
    correction_reason: Optional[str] = None,
    corrected_by_user_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Convenience function for recording a correction
    """
    learner = CorrectionsLearner(db)
    return await learner.record_correction(
        review_queue_id=review_queue_id,
        corrected_booking=corrected_booking,
        correction_reason=correction_reason,
        corrected_by_user_id=corrected_by_user_id
    )
