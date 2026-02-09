"""
Auto-Booking Agent Service
Automatically processes and books vendor invoices based on confidence scoring

FASE 2.3: Automatisk bokføring - AI-agent bokfører uten review
Target: 95%+ accuracy (critical for Skattefunn AP1+AP2)
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.vendor_invoice import VendorInvoice
from app.models.review_queue import ReviewQueue, ReviewStatus
from app.models.agent_learned_pattern import AgentLearnedPattern
from app.services.confidence_scoring import calculate_invoice_confidence
from app.services.booking_service import book_vendor_invoice
from app.services.corrections_learning import record_invoice_correction
from app.services.review_queue_manager import ReviewQueueManager

logger = logging.getLogger(__name__)


class AutoBookingAgent:
    """
    Automatic Booking Agent - Core logic for auto-booking invoices
    
    Workflow:
    1. Read new vendor_invoices from database (not yet booked)
    2. Generate booking suggestion (using AI agent)
    3. Calculate confidence score
    4. If confidence > 85%: Auto-post to GL
    5. If confidence < 85%: Send to review_queue
    6. Learn from successful bookings → create patterns
    7. Patterns → higher confidence next time
    """
    
    # Confidence threshold (configurable)
    AUTO_APPROVE_THRESHOLD = 85
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.review_queue_manager = ReviewQueueManager(db)
    
    async def process_new_invoices(
        self,
        client_id: Optional[UUID] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Process new unbooked invoices in batch
        
        Args:
            client_id: Optional filter by client
            limit: Max number of invoices to process in one batch
        
        Returns:
            {
                'success': True,
                'processed_count': int,
                'auto_booked_count': int,
                'review_queue_count': int,
                'failed_count': int,
                'results': List[Dict]
            }
        """
        try:
            # 1. Find new invoices that need processing
            new_invoices = await self._fetch_unbooked_invoices(client_id, limit)
            
            if not new_invoices:
                logger.info("No new invoices to process")
                return {
                    'success': True,
                    'processed_count': 0,
                    'auto_booked_count': 0,
                    'review_queue_count': 0,
                    'failed_count': 0,
                    'results': []
                }
            
            logger.info(f"Found {len(new_invoices)} new invoices to process")
            
            # 2. Process each invoice
            results = []
            auto_booked = 0
            review_queue = 0
            failed = 0
            
            for invoice in new_invoices:
                try:
                    result = await self.process_single_invoice(invoice.id)
                    results.append(result)
                    
                    if result.get('action') == 'auto_booked':
                        auto_booked += 1
                    elif result.get('action') == 'review_queue':
                        review_queue += 1
                    elif not result.get('success'):
                        failed += 1
                
                except Exception as e:
                    logger.error(f"Error processing invoice {invoice.id}: {str(e)}", exc_info=True)
                    failed += 1
                    results.append({
                        'success': False,
                        'invoice_id': str(invoice.id),
                        'error': str(e)
                    })
            
            # 3. Record batch statistics
            await self._record_batch_stats(
                processed=len(new_invoices),
                auto_booked=auto_booked,
                review_queue=review_queue,
                failed=failed,
                client_id=client_id
            )
            
            logger.info(
                f"Batch complete: {len(new_invoices)} processed, "
                f"{auto_booked} auto-booked, {review_queue} to review, {failed} failed"
            )
            
            return {
                'success': True,
                'processed_count': len(new_invoices),
                'auto_booked_count': auto_booked,
                'review_queue_count': review_queue,
                'failed_count': failed,
                'results': results
            }
        
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def process_single_invoice(
        self,
        invoice_id: UUID
    ) -> Dict[str, Any]:
        """
        Process a single invoice through auto-booking pipeline
        
        Returns:
            {
                'success': bool,
                'invoice_id': str,
                'action': 'auto_booked' | 'review_queue',
                'confidence': int,
                'general_ledger_id': str (if auto_booked),
                'review_queue_id': str (if review_queue),
                'reasoning': str
            }
        """
        try:
            # 1. Fetch invoice
            query = select(VendorInvoice).where(VendorInvoice.id == invoice_id)
            result = await self.db.execute(query)
            invoice = result.scalar_one_or_none()
            
            if not invoice:
                return {'success': False, 'error': 'Invoice not found'}
            
            # 2. Generate booking suggestion (AI)
            booking_suggestion = await self._generate_booking_suggestion(invoice)
            
            if not booking_suggestion or not booking_suggestion.get('lines'):
                logger.warning(f"No booking suggestion generated for invoice {invoice_id}")
                # Send to review queue as fallback
                return await self._send_to_review_queue(
                    invoice=invoice,
                    booking_suggestion={},
                    confidence=0,
                    reason="Failed to generate booking suggestion"
                )
            
            # 3. Calculate confidence score
            confidence_result = await calculate_invoice_confidence(
                db=self.db,
                invoice=invoice,
                booking_suggestion=booking_suggestion
            )
            
            confidence = confidence_result['total_score']
            should_auto_approve = confidence_result['should_auto_approve']
            
            # Update invoice with AI data
            invoice.ai_confidence_score = confidence
            invoice.ai_booking_suggestion = booking_suggestion
            invoice.ai_reasoning = confidence_result['reasoning']
            invoice.ai_processed = True
            
            # 4. Decision: Auto-book or Review Queue
            if should_auto_approve and confidence >= self.AUTO_APPROVE_THRESHOLD:
                # AUTO-BOOK
                return await self._auto_book_invoice(
                    invoice=invoice,
                    booking_suggestion=booking_suggestion,
                    confidence_result=confidence_result
                )
            else:
                # REVIEW QUEUE
                return await self._send_to_review_queue(
                    invoice=invoice,
                    booking_suggestion=booking_suggestion,
                    confidence=confidence,
                    confidence_result=confidence_result
                )
        
        except Exception as e:
            logger.error(f"Error processing invoice {invoice_id}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'invoice_id': str(invoice_id),
                'error': str(e)
            }
    
    async def _fetch_unbooked_invoices(
        self,
        client_id: Optional[UUID],
        limit: int
    ) -> List[VendorInvoice]:
        """
        Fetch invoices that need processing
        - Not yet booked (general_ledger_id is NULL)
        - Not in review queue or failed
        """
        query = select(VendorInvoice).where(
            and_(
                VendorInvoice.general_ledger_id.is_(None),  # Not booked
                or_(
                    VendorInvoice.review_status == 'pending',
                    VendorInvoice.review_status.is_(None)
                )
            )
        )
        
        if client_id:
            query = query.where(VendorInvoice.client_id == client_id)
        
        query = query.order_by(VendorInvoice.invoice_date.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _generate_booking_suggestion(
        self,
        invoice: VendorInvoice
    ) -> Dict[str, Any]:
        """
        Generate booking suggestion using AI
        
        For now, uses learned patterns + simple heuristics.
        In production, this would call the full AI Invoice Agent.
        """
        try:
            # Check for learned patterns first
            pattern = await self._find_matching_pattern(invoice)
            
            if pattern:
                # Use learned pattern
                return await self._generate_from_pattern(invoice, pattern)
            
            # Fallback: Generate standard vendor invoice booking
            return await self._generate_standard_booking(invoice)
        
        except Exception as e:
            logger.error(f"Error generating booking suggestion: {str(e)}", exc_info=True)
            return {}
    
    async def _find_matching_pattern(
        self,
        invoice: VendorInvoice
    ) -> Optional[AgentLearnedPattern]:
        """
        Find a learned pattern that matches this invoice
        """
        if not invoice.vendor_id:
            return None
        
        query = select(AgentLearnedPattern).where(
            and_(
                AgentLearnedPattern.is_active == True,
                or_(
                    AgentLearnedPattern.global_pattern == True,
                    AgentLearnedPattern.applies_to_clients.contains([invoice.client_id])
                )
            )
        ).order_by(
            AgentLearnedPattern.success_rate.desc(),
            AgentLearnedPattern.times_applied.desc()
        )
        
        result = await self.db.execute(query)
        patterns = result.scalars().all()
        
        # Find pattern matching this vendor
        for pattern in patterns:
            trigger = pattern.trigger or {}
            if trigger.get('vendor_id') == str(invoice.vendor_id):
                return pattern
        
        return None
    
    async def _generate_from_pattern(
        self,
        invoice: VendorInvoice,
        pattern: AgentLearnedPattern
    ) -> Dict[str, Any]:
        """
        Generate booking from learned pattern
        """
        pattern_data = pattern.pattern_data or {}
        sample_booking = pattern_data.get('sample_booking', [])
        
        if not sample_booking:
            return await self._generate_standard_booking(invoice)
        
        # Scale amounts from pattern to current invoice
        lines = []
        for line in sample_booking:
            scaled_line = {
                'account': line.get('account'),
                'debit': float(line.get('debit', 0)),
                'credit': float(line.get('credit', 0)),
                'vat_code': line.get('vat_code'),
                'vat_amount': float(line.get('vat_amount', 0)),
                'description': line.get('description', '')
            }
            lines.append(scaled_line)
        
        # Update pattern stats
        pattern.times_applied = (pattern.times_applied or 0) + 1
        
        return {
            'lines': lines,
            'source': 'learned_pattern',
            'pattern_id': str(pattern.id),
            'confidence_boost': pattern.confidence_boost or 0
        }
    
    async def _generate_standard_booking(
        self,
        invoice: VendorInvoice
    ) -> Dict[str, Any]:
        """
        Generate standard vendor invoice booking
        
        Standard booking:
        - Debit: 6000 (Varekjøp) or 6800 (Kontorrekvisita) based on heuristics
        - Debit: 2700 (Inngående MVA) for VAT
        - Credit: 2400 (Leverandørgjeld)
        """
        lines = []
        
        # Line 1: Expense account (debit)
        # Simple heuristic: if description contains certain keywords, use specific account
        expense_account = '6000'  # Default: Varekjøp
        description = (invoice.vendor.name if invoice.vendor else '').lower()
        
        if any(kw in description for kw in ['kontor', 'office', 'papir', 'rekvisita']):
            expense_account = '6800'  # Kontorrekvisita
        elif any(kw in description for kw in ['it', 'data', 'software', 'lisens']):
            expense_account = '6900'  # Fremmede tjenester
        
        lines.append({
            'account': expense_account,
            'debit': float(invoice.amount_excl_vat),
            'credit': 0,
            'vat_code': '3',  # Kjøp med fradragsrett
            'vat_amount': 0,
            'description': f"{invoice.vendor.name if invoice.vendor else 'Leverandør'} - {invoice.invoice_number}"
        })
        
        # Line 2: VAT (debit)
        if invoice.vat_amount > 0:
            lines.append({
                'account': '2700',  # Inngående MVA
                'debit': float(invoice.vat_amount),
                'credit': 0,
                'vat_code': '3',
                'vat_amount': float(invoice.vat_amount),
                'description': 'Inngående mva'
            })
        
        # Line 3: Accounts Payable (credit)
        lines.append({
            'account': '2400',  # Leverandørgjeld
            'debit': 0,
            'credit': float(invoice.total_amount),
            'vat_code': None,
            'vat_amount': 0,
            'description': f"{invoice.vendor.name if invoice.vendor else 'Leverandør'} - {invoice.invoice_number}"
        })
        
        return {
            'lines': lines,
            'source': 'standard_heuristic',
            'confidence_boost': 0
        }
    
    async def _auto_book_invoice(
        self,
        invoice: VendorInvoice,
        booking_suggestion: Dict[str, Any],
        confidence_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Auto-book invoice to General Ledger
        """
        try:
            # Book to GL
            booking_result = await book_vendor_invoice(
                db=self.db,
                invoice_id=invoice.id,
                booking_suggestion=booking_suggestion,
                created_by_type="ai_agent"
            )
            
            if not booking_result['success']:
                logger.error(
                    f"Auto-booking failed for invoice {invoice.id}: "
                    f"{booking_result.get('error')}"
                )
                # Fallback to review queue
                return await self._send_to_review_queue(
                    invoice=invoice,
                    booking_suggestion=booking_suggestion,
                    confidence=confidence_result['total_score'],
                    confidence_result=confidence_result,
                    reason=f"Auto-booking failed: {booking_result.get('error')}"
                )
            
            # Update invoice status
            invoice.review_status = 'auto_approved'
            await self.db.commit()
            
            # Learn from successful booking
            await self._learn_from_success(invoice, booking_suggestion)
            
            logger.info(
                f"Invoice {invoice.id} auto-booked successfully with confidence "
                f"{confidence_result['total_score']}%"
            )
            
            return {
                'success': True,
                'invoice_id': str(invoice.id),
                'action': 'auto_booked',
                'confidence': confidence_result['total_score'],
                'confidence_breakdown': confidence_result['breakdown'],
                'reasoning': confidence_result['reasoning'],
                'general_ledger_id': booking_result['general_ledger_id'],
                'voucher_number': booking_result['voucher_number']
            }
        
        except Exception as e:
            logger.error(f"Error in auto-booking: {str(e)}", exc_info=True)
            await self.db.rollback()
            return {
                'success': False,
                'invoice_id': str(invoice.id),
                'error': str(e)
            }
    
    async def _send_to_review_queue(
        self,
        invoice: VendorInvoice,
        booking_suggestion: Dict[str, Any],
        confidence: int,
        confidence_result: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send invoice to review queue for human review
        """
        try:
            # Use ReviewQueueManager to create review item
            result = await self.review_queue_manager.process_invoice_with_confidence(
                invoice_id=invoice.id,
                booking_suggestion=booking_suggestion
            )
            
            if result.get('action') == 'needs_review':
                logger.info(
                    f"Invoice {invoice.id} sent to review queue (confidence: {confidence}%)"
                )
                return {
                    'success': True,
                    'invoice_id': str(invoice.id),
                    'action': 'review_queue',
                    'confidence': confidence,
                    'confidence_breakdown': result.get('confidence_breakdown'),
                    'reasoning': result.get('reasoning') or reason,
                    'review_queue_id': result.get('review_queue_id'),
                    'priority': result.get('priority')
                }
            else:
                # Unexpected: manager decided to auto-approve
                return result
        
        except Exception as e:
            logger.error(f"Error sending to review queue: {str(e)}", exc_info=True)
            return {
                'success': False,
                'invoice_id': str(invoice.id),
                'error': str(e)
            }
    
    async def _learn_from_success(
        self,
        invoice: VendorInvoice,
        booking_suggestion: Dict[str, Any]
    ) -> None:
        """
        Learn from successful auto-booking
        
        If this is from a new vendor or improved accuracy, create/update pattern
        """
        try:
            if not invoice.vendor_id:
                return
            
            # Check if we should create a new pattern
            # Only create pattern if this vendor has few previous bookings
            query = select(func.count(VendorInvoice.id)).where(
                and_(
                    VendorInvoice.vendor_id == invoice.vendor_id,
                    VendorInvoice.general_ledger_id.isnot(None)
                )
            )
            result = await self.db.execute(query)
            booking_count = result.scalar() or 0
            
            # Create pattern after 3rd successful booking
            if booking_count == 3:
                await self._create_success_pattern(invoice, booking_suggestion)
        
        except Exception as e:
            logger.error(f"Error learning from success: {str(e)}", exc_info=True)
    
    async def _create_success_pattern(
        self,
        invoice: VendorInvoice,
        booking_suggestion: Dict[str, Any]
    ) -> None:
        """
        Create a learned pattern from successful booking
        """
        try:
            # Check if pattern already exists
            query = select(AgentLearnedPattern).where(
                and_(
                    AgentLearnedPattern.pattern_type == 'auto_booking_success',
                    AgentLearnedPattern.is_active == True
                )
            )
            result = await self.db.execute(query)
            existing_patterns = result.scalars().all()
            
            # Check for duplicate
            for existing in existing_patterns:
                trigger = existing.trigger or {}
                if trigger.get('vendor_id') == str(invoice.vendor_id):
                    logger.info(f"Pattern already exists for vendor {invoice.vendor_id}")
                    return
            
            # Create new pattern
            accounts = list(set(
                line.get('account') for line in booking_suggestion.get('lines', [])
            ))
            
            pattern = AgentLearnedPattern(
                id=uuid4(),
                pattern_type='auto_booking_success',
                pattern_name=f"Auto-booking pattern for {invoice.vendor.name if invoice.vendor else 'vendor'}",
                description=f"Learned from successful auto-bookings",
                trigger={
                    'vendor_id': str(invoice.vendor_id),
                    'vendor_name': invoice.vendor.name if invoice.vendor else None
                },
                action={'accounts': accounts},
                pattern_data={
                    'vendor_id': str(invoice.vendor_id),
                    'sample_booking': booking_suggestion.get('lines', [])
                },
                applies_to_clients=[invoice.client_id],
                global_pattern=False,
                confidence_boost=15,
                is_active=True,
                times_applied=0,
                success_rate=Decimal('1.0')
            )
            
            self.db.add(pattern)
            await self.db.commit()
            
            logger.info(f"Created auto-booking pattern {pattern.id} from successful booking")
        
        except Exception as e:
            logger.error(f"Error creating success pattern: {str(e)}", exc_info=True)
    
    async def _record_batch_stats(
        self,
        processed: int,
        auto_booked: int,
        review_queue: int,
        failed: int,
        client_id: Optional[UUID]
    ) -> None:
        """
        Record batch processing statistics
        
        Note: For now, we'll just log. In production, this would write to auto_booking_stats table.
        """
        success_rate = (auto_booked / processed * 100) if processed > 0 else 0
        escalation_rate = (review_queue / processed * 100) if processed > 0 else 0
        
        logger.info(
            f"Batch stats: {processed} processed, {auto_booked} auto-booked ({success_rate:.1f}%), "
            f"{review_queue} escalated ({escalation_rate:.1f}%), {failed} failed"
        )
        
        # TODO: Write to auto_booking_stats table when implemented


async def run_auto_booking_batch(
    db: AsyncSession,
    client_id: Optional[UUID] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Convenience function to run auto-booking batch
    """
    agent = AutoBookingAgent(db)
    return await agent.process_new_invoices(client_id=client_id, limit=limit)


async def process_single_invoice_auto_booking(
    db: AsyncSession,
    invoice_id: UUID
) -> Dict[str, Any]:
    """
    Convenience function to process single invoice
    """
    agent = AutoBookingAgent(db)
    return await agent.process_single_invoice(invoice_id=invoice_id)
