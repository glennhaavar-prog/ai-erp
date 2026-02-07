"""
Action Handlers - Execute booking, status, approval, correction actions
"""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, cast, String
from datetime import datetime, timedelta

from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.review_queue import ReviewQueue, ReviewStatus
from app.models.general_ledger import GeneralLedger
from app.agents.invoice_agent import InvoiceAgent
from app.services.booking_service import book_vendor_invoice

logger = logging.getLogger(__name__)


class BookingActionHandler:
    """
    Handle booking-related actions
    - Analyze invoice and suggest booking
    - Execute booking
    """
    
    def __init__(self):
        self.invoice_agent = InvoiceAgent()
    
    async def analyze_invoice(
        self,
        db: AsyncSession,
        invoice_number: Optional[str] = None,
        invoice_id: Optional[str] = None,
        client_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze invoice and suggest booking
        
        Returns:
            {
                'success': True,
                'invoice': {...},
                'suggested_booking': {...},
                'confidence': 95,
                'reasoning': '...'
            }
        """
        try:
            # Find invoice
            invoice = await self._find_invoice(db, invoice_number, invoice_id, client_id)
            
            if not invoice:
                return {
                    'success': False,
                    'error': 'Faktura ikke funnet',
                    'message': f"❌ Fant ingen faktura {invoice_number or invoice_id}"
                }
            
            # Check if already booked
            if invoice.general_ledger_id:
                return {
                    'success': False,
                    'error': 'already_booked',
                    'message': f"⚠️ Faktura {invoice.invoice_number} er allerede bokført",
                    'invoice': self._format_invoice(invoice)
                }
            
            # Get OCR text (if available)
            ocr_text = invoice.ocr_text or "No OCR text available"
            
            # Analyze with AI
            analysis = await self.invoice_agent.analyze_invoice(
                ocr_text=ocr_text,
                client_id=str(invoice.client_id),
                vendor_history=None,  # TODO: Fetch from learning agent
                learned_patterns=None
            )
            
            # Format response
            return {
                'success': True,
                'invoice': self._format_invoice(invoice),
                'suggested_booking': analysis.get('suggested_booking', []),
                'confidence': analysis.get('confidence_score', 0),
                'reasoning': analysis.get('reasoning', ''),
                'amount_excl_vat': float(analysis.get('amount_excl_vat', 0)),
                'vat_amount': float(analysis.get('vat_amount', 0)),
                'total_amount': float(analysis.get('total_amount', invoice.total_amount))
            }
        
        except Exception as e:
            logger.error(f"Error analyzing invoice: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Feil ved analyse: {str(e)}"
            }
    
    async def book_invoice(
        self,
        db: AsyncSession,
        invoice_id: str,
        booking_suggestion: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute booking for invoice
        
        Returns:
            {
                'success': True,
                'voucher_number': 'AP-000123',
                'general_ledger_id': '...',
                'message': '✅ Faktura bokført'
            }
        """
        try:
            # Book invoice
            result = await book_vendor_invoice(
                db=db,
                invoice_id=UUID(invoice_id),
                booking_suggestion=booking_suggestion,
                created_by_type='user' if user_id else 'ai_agent',
                created_by_id=UUID(user_id) if user_id else None
            )
            
            if result['success']:
                return {
                    'success': True,
                    'voucher_number': result['voucher_number'],
                    'general_ledger_id': result['general_ledger_id'],
                    'message': f"✅ Faktura bokført på bilag {result['voucher_number']}"
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'message': f"❌ Bokføring feilet: {result['error']}"
                }
        
        except Exception as e:
            logger.error(f"Error booking invoice: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Feil ved bokføring: {str(e)}"
            }
    
    async def _find_invoice(
        self,
        db: AsyncSession,
        invoice_number: Optional[str],
        invoice_id: Optional[str],
        client_id: Optional[str]
    ) -> Optional[VendorInvoice]:
        """Find invoice by number or ID"""
        
        if invoice_id:
            # Find by ID
            result = await db.execute(
                select(VendorInvoice).where(VendorInvoice.id == UUID(invoice_id))
            )
            return result.scalar_one_or_none()
        
        elif invoice_number and client_id:
            # Find by invoice number
            result = await db.execute(
                select(VendorInvoice).where(
                    and_(
                        VendorInvoice.invoice_number == invoice_number,
                        VendorInvoice.client_id == UUID(client_id)
                    )
                )
            )
            return result.scalar_one_or_none()
        
        return None
    
    def _format_invoice(self, invoice: VendorInvoice) -> Dict[str, Any]:
        """Format invoice for response"""
        return {
            'id': str(invoice.id),
            'invoice_number': invoice.invoice_number,
            'vendor': invoice.vendor.name if invoice.vendor else 'Ukjent',
            'total_amount': float(invoice.total_amount),
            'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'status': invoice.review_status
        }


class StatusQueryHandler:
    """
    Handle status queries
    - Invoice status
    - Overall statistics
    - Pending/review queue
    """
    
    async def get_invoice_status(
        self,
        db: AsyncSession,
        invoice_number: Optional[str] = None,
        invoice_id: Optional[str] = None,
        client_id: str = None
    ) -> Dict[str, Any]:
        """Get status of specific invoice"""
        
        try:
            # Find invoice
            if invoice_id:
                result = await db.execute(
                    select(VendorInvoice).where(VendorInvoice.id == UUID(invoice_id))
                )
            elif invoice_number and client_id:
                result = await db.execute(
                    select(VendorInvoice).where(
                        and_(
                            VendorInvoice.invoice_number == invoice_number,
                            VendorInvoice.client_id == UUID(client_id)
                        )
                    )
                )
            else:
                return {'success': False, 'error': 'Missing invoice identifier'}
            
            invoice = result.scalar_one_or_none()
            
            if not invoice:
                return {
                    'success': False,
                    'error': 'not_found',
                    'message': f"❌ Fant ingen faktura {invoice_number or invoice_id}"
                }
            
            # Build status response
            status_emoji = {
                'pending': '⏳',
                'processing': '🔄',
                'auto_approved': '✅',
                'requires_review': '⚠️',
                'rejected': '❌'
            }.get(invoice.review_status, '❓')
            
            booked = invoice.general_ledger_id is not None
            
            message = f"{status_emoji} **Faktura {invoice.invoice_number}**\n\n"
            message += f"• Leverandør: {invoice.vendor.name if invoice.vendor else 'Ukjent'}\n"
            message += f"• Beløp: {invoice.total_amount:,.2f} kr\n"
            message += f"• Dato: {invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else 'N/A'}\n"
            message += f"• Status: {invoice.review_status}\n"
            message += f"• Bokført: {'Ja ✓' if booked else 'Nei'}\n"
            
            if booked:
                # Get GL entry
                gl_result = await db.execute(
                    select(GeneralLedger).where(GeneralLedger.id == invoice.general_ledger_id)
                )
                gl_entry = gl_result.scalar_one_or_none()
                if gl_entry:
                    message += f"• Bilag: {gl_entry.voucher_series}-{gl_entry.voucher_number}\n"
            
            return {
                'success': True,
                'message': message,
                'invoice': {
                    'id': str(invoice.id),
                    'invoice_number': invoice.invoice_number,
                    'status': invoice.review_status,
                    'booked': booked,
                    'total_amount': float(invoice.total_amount)
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting invoice status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Feil: {str(e)}"
            }
    
    async def get_overall_status(
        self,
        db: AsyncSession,
        client_id: str
    ) -> Dict[str, Any]:
        """Get overall statistics"""
        
        try:
            # Count invoices by status
            total_count = await db.scalar(
                select(func.count(VendorInvoice.id)).where(
                    VendorInvoice.client_id == UUID(client_id)
                )
            )
            
            pending_count = await db.scalar(
                select(func.count(VendorInvoice.id)).where(
                    and_(
                        VendorInvoice.client_id == UUID(client_id),
                        VendorInvoice.general_ledger_id == None
                    )
                )
            )
            
            booked_today_count = await db.scalar(
                select(func.count(VendorInvoice.id)).where(
                    and_(
                        VendorInvoice.client_id == UUID(client_id),
                        VendorInvoice.booked_at >= datetime.utcnow().date()
                    )
                )
            )
            
            # Count review queue items
            review_count = await db.scalar(
                select(func.count(ReviewQueue.id)).where(
                    and_(
                        ReviewQueue.client_id == UUID(client_id),
                        cast(ReviewQueue.status, String) == 'PENDING'
                    )
                )
            )
            
            message = "📊 **Status oversikt**\n\n"
            message += f"• Total fakturaer: {total_count}\n"
            message += f"• ⏳ Venter på bokføring: {pending_count}\n"
            message += f"• ✅ Bokført i dag: {booked_today_count}\n"
            message += f"• ⚠️ I Review Queue: {review_count}\n"
            
            return {
                'success': True,
                'message': message,
                'stats': {
                    'total': total_count,
                    'pending': pending_count,
                    'booked_today': booked_today_count,
                    'in_review': review_count
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting overall status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Feil: {str(e)}"
            }
    
    async def list_pending_invoices(
        self,
        db: AsyncSession,
        client_id: str,
        filter_type: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """List pending invoices"""
        
        try:
            # Build query
            query = select(VendorInvoice).where(
                and_(
                    VendorInvoice.client_id == UUID(client_id),
                    VendorInvoice.general_ledger_id == None
                )
            )
            
            # Apply filter
            if filter_type == 'low_confidence':
                # Find invoices with review items of low confidence
                query = query.join(ReviewQueue, VendorInvoice.id == ReviewQueue.source_id).where(
                    and_(
                        ReviewQueue.source_type == 'vendor_invoice',
                        ReviewQueue.ai_confidence < 70
                    )
                )
            
            query = query.order_by(desc(VendorInvoice.created_at)).limit(limit)
            
            result = await db.execute(query)
            invoices = result.scalars().all()
            
            if not invoices:
                return {
                    'success': True,
                    'message': '✅ Ingen fakturaer venter!',
                    'invoices': []
                }
            
            message = f"📋 **{len(invoices)} fakturaer venter på bokføring:**\n\n"
            
            invoice_list = []
            for idx, inv in enumerate(invoices, 1):
                message += f"{idx}. **{inv.invoice_number}** - {inv.vendor.name if inv.vendor else 'Ukjent'} - {inv.total_amount:,.2f} kr\n"
                
                invoice_list.append({
                    'id': str(inv.id),
                    'invoice_number': inv.invoice_number,
                    'vendor': inv.vendor.name if inv.vendor else 'Ukjent',
                    'total_amount': float(inv.total_amount),
                    'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else None
                })
            
            return {
                'success': True,
                'message': message,
                'invoices': invoice_list
            }
        
        except Exception as e:
            logger.error(f"Error listing invoices: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Feil: {str(e)}"
            }


class ApprovalHandler:
    """Handle approval of bookings in review queue"""
    
    async def approve_booking(
        self,
        db: AsyncSession,
        item_id: str,
        client_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve a booking in review queue"""
        
        try:
            # Find review item
            result = await db.execute(
                select(ReviewQueue).where(
                    and_(
                        ReviewQueue.id == UUID(item_id),
                        ReviewQueue.client_id == UUID(client_id)
                    )
                )
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return {
                    'success': False,
                    'error': 'not_found',
                    'message': f"❌ Fant ikke item {item_id}"
                }
            
            # Update status
            item.status = ReviewStatus.APPROVED
            item.resolved_at = datetime.utcnow()
            item.resolution_notes = "Approved via chat"
            
            # If it's a GL entry, post it
            if item.source_type == 'general_ledger':
                gl_result = await db.execute(
                    select(GeneralLedger).where(GeneralLedger.id == item.source_id)
                )
                gl_entry = gl_result.scalar_one_or_none()
                if gl_entry:
                    gl_entry.status = 'posted'
            
            await db.commit()
            
            return {
                'success': True,
                'message': f"✅ Bokføring godkjent!",
                'item_id': item_id
            }
        
        except Exception as e:
            logger.error(f"Error approving booking: {str(e)}")
            await db.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Feil: {str(e)}"
            }


class CorrectionHandler:
    """Handle corrections to bookings"""
    
    async def correct_account(
        self,
        db: AsyncSession,
        invoice_id: str,
        old_account: str,
        new_account: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Correct account number in a booking"""
        
        try:
            # Find invoice and GL entry
            result = await db.execute(
                select(VendorInvoice).where(VendorInvoice.id == UUID(invoice_id))
            )
            invoice = result.scalar_one_or_none()
            
            if not invoice or not invoice.general_ledger_id:
                return {
                    'success': False,
                    'error': 'Invoice not found or not booked',
                    'message': "❌ Faktura ikke funnet eller ikke bokført"
                }
            
            # Get GL entry
            gl_result = await db.execute(
                select(GeneralLedger).where(GeneralLedger.id == invoice.general_ledger_id)
            )
            gl_entry = gl_result.scalar_one_or_none()
            
            if not gl_entry:
                return {
                    'success': False,
                    'error': 'GL entry not found',
                    'message': "❌ Bilag ikke funnet"
                }
            
            # Find and update line with old_account
            updated = False
            for line in gl_entry.lines:
                if line.account_number == old_account:
                    line.account_number = new_account
                    updated = True
                    logger.info(f"Corrected account {old_account} -> {new_account} in GL {gl_entry.id}")
            
            if not updated:
                return {
                    'success': False,
                    'error': 'Account not found in booking',
                    'message': f"❌ Fant ikke konto {old_account} i bokføring"
                }
            
            await db.commit()
            
            return {
                'success': True,
                'message': f"✅ Konto korrigert: {old_account} → {new_account}",
                'voucher_number': f"{gl_entry.voucher_series}-{gl_entry.voucher_number}"
            }
        
        except Exception as e:
            logger.error(f"Error correcting account: {str(e)}")
            await db.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Feil: {str(e)}"
            }
