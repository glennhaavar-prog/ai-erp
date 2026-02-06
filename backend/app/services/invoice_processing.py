"""
Invoice Processing Service
Connects Invoice Agent with Review Queue
"""
import logging
from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.invoice_agent import InvoiceAgent
from app.models.vendor_invoice import VendorInvoice
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)

# Confidence threshold for auto-approval
CONFIDENCE_THRESHOLD = 85


async def process_vendor_invoice(
    db: AsyncSession,
    invoice_id: UUID,
) -> Dict[str, Any]:
    """
    Process a vendor invoice through AI agent and route to Review Queue or auto-book
    
    Flow:
    1. Fetch invoice from DB
    2. Get vendor history (previous invoices from same vendor)
    3. Call Invoice Agent to analyze
    4. If confidence >= 85% → auto-book (future: trigger booking agent)
    5. If confidence < 85% → send to Review Queue
    
    Args:
        db: Database session
        invoice_id: UUID of VendorInvoice to process
    
    Returns:
        {
            'success': True/False,
            'invoice_id': str,
            'confidence': int,
            'action': 'auto_booked' | 'review_queue',
            'review_queue_id': str (if sent to review),
            'error': str (if failed)
        }
    """
    try:
        # 1. Fetch invoice
        query = select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        result = await db.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            logger.error(f"Invoice {invoice_id} not found")
            return {
                'success': False,
                'error': 'Invoice not found'
            }
        
        # 2. Get vendor history
        vendor_history = await _get_vendor_history(db, invoice.vendor_id)
        
        # 3. Prepare OCR text (for now, use description or EHF data)
        # TODO: When PDF upload is implemented, use actual OCR text from AWS Textract
        ocr_text = _prepare_ocr_text(invoice)
        
        # 4. Call Invoice Agent
        agent = InvoiceAgent()
        analysis = await agent.analyze_invoice(
            ocr_text=ocr_text,
            client_id=str(invoice.client_id),
            vendor_history=vendor_history,
            learned_patterns=None  # TODO: Fetch from learning system
        )
        
        confidence = analysis.get('confidence_score', 0)
        
        # 5. Route based on confidence
        if confidence >= CONFIDENCE_THRESHOLD:
            # High confidence → Auto-book
            logger.info(f"Invoice {invoice_id} auto-booking (confidence: {confidence}%)")
            
            # Import booking service
            from app.services.booking_service import book_vendor_invoice
            
            # Create actual General Ledger entries
            booking_result = await book_vendor_invoice(
                db=db,
                invoice_id=invoice_id,
                booking_suggestion=analysis,
                created_by_type="ai_agent"
            )
            
            if not booking_result['success']:
                logger.error(f"Failed to book invoice {invoice_id}: {booking_result.get('error')}")
                # Fall back to review queue if booking fails
                review_item = await _create_review_queue_item(
                    db=db,
                    invoice=invoice,
                    analysis=analysis,
                    confidence=confidence
                )
                invoice.review_status = 'pending'
                invoice.ai_confidence = confidence
                invoice.ai_suggestion = analysis
                await db.commit()
                
                return {
                    'success': False,
                    'invoice_id': str(invoice_id),
                    'confidence': confidence,
                    'action': 'review_queue',
                    'review_queue_id': str(review_item.id),
                    'error': f"Auto-booking failed: {booking_result.get('error')}"
                }
            
            return {
                'success': True,
                'invoice_id': str(invoice_id),
                'confidence': confidence,
                'action': 'auto_booked',
                'general_ledger_id': booking_result['general_ledger_id'],
                'voucher_number': booking_result['voucher_number'],
                'suggested_booking': analysis.get('suggested_booking')
            }
        
        else:
            # Low confidence → Review Queue
            logger.info(f"Invoice {invoice_id} sent to review queue (confidence: {confidence}%)")
            
            review_item = await _create_review_queue_item(
                db=db,
                invoice=invoice,
                analysis=analysis,
                confidence=confidence
            )
            
            # Update invoice status
            invoice.review_status = 'pending'
            invoice.ai_confidence = confidence
            invoice.ai_suggestion = analysis
            await db.commit()
            
            return {
                'success': True,
                'invoice_id': str(invoice_id),
                'confidence': confidence,
                'action': 'review_queue',
                'review_queue_id': str(review_item.id)
            }
    
    except Exception as e:
        logger.error(f"Error processing invoice {invoice_id}: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'invoice_id': str(invoice_id),
            'error': str(e)
        }


async def _get_vendor_history(
    db: AsyncSession,
    vendor_id: UUID
) -> Optional[Dict]:
    """Get previous invoices from same vendor for learning"""
    query = select(VendorInvoice).where(
        VendorInvoice.vendor_id == vendor_id,
        VendorInvoice.review_status == 'approved'
    ).limit(5).order_by(VendorInvoice.invoice_date.desc())
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    if not invoices:
        return None
    
    return {
        'vendor_id': str(vendor_id),
        'previous_invoices': [
            {
                'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else None,
                'amount': float(inv.total_amount),
                'ai_suggestion': inv.ai_suggestion
            }
            for inv in invoices
            if inv.ai_suggestion  # Only include if we have AI data
        ]
    }


def _prepare_ocr_text(invoice: VendorInvoice) -> str:
    """
    Prepare OCR text for Invoice Agent
    
    For EHF invoices, we extract structured data.
    For PDF uploads (future), this will be actual OCR text from AWS Textract.
    """
    if invoice.ehf_raw_xml:
        # EHF invoice - extract key fields
        return f"""
EHF Invoice Data:

Vendor: {invoice.vendor.name if invoice.vendor else 'Unknown'}
Organization Number: {invoice.vendor.org_number if invoice.vendor else 'Unknown'}
Invoice Number: {invoice.invoice_number}
Invoice Date: {invoice.invoice_date}
Due Date: {invoice.due_date}
Currency: {invoice.currency}

Amount (excl VAT): {invoice.amount_excl_vat}
VAT Amount: {invoice.vat_amount}
Total Amount: {invoice.total_amount}
"""
    else:
        # Future: PDF upload case
        # This will be replaced with actual OCR text from AWS Textract
        return f"""
Invoice from vendor (PDF)

Vendor: {invoice.vendor.name if invoice.vendor else 'Unknown'}
Organization Number: {invoice.vendor.org_number if invoice.vendor else 'Unknown'}
Invoice Number: {invoice.invoice_number}
Amount: {invoice.total_amount} {invoice.currency}
Date: {invoice.invoice_date}
"""


async def _create_review_queue_item(
    db: AsyncSession,
    invoice: VendorInvoice,
    analysis: Dict[str, Any],
    confidence: int
) -> ReviewQueue:
    """Create a Review Queue item for human review"""
    
    # Determine priority based on confidence and amount
    if confidence < 50:
        priority = ReviewPriority.HIGH
    elif invoice.total_amount > 50000:  # Large amounts need attention
        priority = ReviewPriority.HIGH
    elif confidence < 70:
        priority = ReviewPriority.MEDIUM
    else:
        priority = ReviewPriority.LOW
    
    # Determine issue category
    if confidence < 50:
        issue_category = IssueCategory.LOW_CONFIDENCE
    elif not invoice.vendor_id:
        issue_category = IssueCategory.UNKNOWN_VENDOR
    elif analysis.get('error'):
        issue_category = IssueCategory.PROCESSING_ERROR
    else:
        issue_category = IssueCategory.LOW_CONFIDENCE
    
    # Create issue description
    issue_description = f"""
AI er {confidence}% sikker på denne bokføringen.

Årsak: {analysis.get('reasoning', 'AI er usikker på riktig kontoføring')}

Vennligst gjennomgå og godkjenn eller korriger forslaget.
"""
    
    review_item = ReviewQueue(
        client_id=invoice.client_id,
        source_type='vendor_invoice',
        source_id=invoice.id,
        priority=priority,
        status=ReviewStatus.PENDING,
        issue_category=issue_category,
        issue_description=issue_description.strip(),
        ai_suggestion=analysis,
        ai_confidence=confidence,
        ai_reasoning=analysis.get('reasoning')
    )
    
    db.add(review_item)
    await db.commit()
    await db.refresh(review_item)
    
    logger.info(f"Created review queue item {review_item.id} for invoice {invoice.id}")
    
    return review_item
