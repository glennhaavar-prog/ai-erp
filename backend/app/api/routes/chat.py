"""
Chat API endpoint for conversational interface with Review Queue
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.review_queue import ReviewQueue, ReviewStatus
from app.models.vendor_invoice import VendorInvoice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat message request"""
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat message response"""
    role: str  # 'assistant' or 'system'
    content: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None


async def fetch_reviews_from_db(db: AsyncSession) -> List[Dict]:
    """Fetch review queue items from database"""
    query = select(ReviewQueue, VendorInvoice).join(
        VendorInvoice,
        ReviewQueue.source_id == VendorInvoice.id
    ).where(
        ReviewQueue.source_type == 'vendor_invoice'
    ).order_by(
        ReviewQueue.priority.desc(),
        ReviewQueue.created_at.desc()
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    reviews = []
    for review, invoice in rows:
        reviews.append({
            "id": str(review.id),
            "supplier": invoice.vendor.name if invoice.vendor else "Unknown",
            "amount": float(invoice.total_amount),
            "status": review.status.value,
            "priority": review.priority.value,
            "confidence": review.ai_confidence or 0,
            "invoiceNumber": invoice.invoice_number,
            "description": review.issue_description,
            "createdAt": review.created_at.isoformat(),
            "invoice_id": str(invoice.id)
        })
    
    return reviews


async def process_command(message: str, db: AsyncSession) -> ChatResponse:
    """Process chat command and return appropriate response"""
    cmd = message.lower().strip()
    
    # Get reviews from database
    reviews = await fetch_reviews_from_db(db)
    pending_reviews = [r for r in reviews if r['status'] == 'pending']
    
    # Command: show reviews
    if cmd in ['show reviews', 'reviews', 'list', 'show']:
        if not pending_reviews:
            return ChatResponse(
                role='assistant',
                content='✅ Ingen fakturaer venter på godkjenning!',
                timestamp=datetime.utcnow().isoformat(),
            )
        
        reviews_text = '\n'.join([
            f"{idx + 1}. [{r['id'][:8]}] {r['supplier']} - {r['amount']:,} kr ({r['priority']})"
            for idx, r in enumerate(pending_reviews)
        ])
        
        return ChatResponse(
            role='assistant',
            content=f"📋 **{len(pending_reviews)} fakturaer venter på godkjenning:**\n\n{reviews_text}",
            timestamp=datetime.utcnow().isoformat(),
            data={'reviews': pending_reviews},
        )
    
    # Command: status
    if cmd == 'status':
        stats = {
            'total': len(reviews),
            'pending': len([r for r in reviews if r['status'] == 'pending']),
            'approved': len([r for r in reviews if r['status'] == 'approved']),
            'rejected': len([r for r in reviews if r['status'] == 'rejected']),
        }
        
        return ChatResponse(
            role='assistant',
            content=(
                f"📊 **Status oversikt:**\n\n"
                f"• Total: {stats['total']} fakturaer\n"
                f"• ⏳ Venter: {stats['pending']}\n"
                f"• ✅ Godkjent: {stats['approved']}\n"
                f"• ❌ Avvist: {stats['rejected']}"
            ),
            timestamp=datetime.utcnow().isoformat(),
            data=stats,
        )
    
    # Command: approve [id]
    approve_match = re.match(r'^approve\s+(.+)$', cmd)
    if approve_match:
        id_prefix = approve_match.group(1).strip()
        matching_review = next(
            (r for r in pending_reviews if r['id'].lower().startswith(id_prefix.lower())),
            None
        )
        
        if not matching_review:
            return ChatResponse(
                role='assistant',
                content=f'❌ Fant ingen faktura med ID som starter med "{id_prefix}" eller den er allerede behandlet.',
                timestamp=datetime.utcnow().isoformat(),
            )
        
        # Update DB to mark as approved
        review_id = UUID(matching_review['id'])
        query = select(ReviewQueue).where(ReviewQueue.id == review_id)
        result = await db.execute(query)
        review_item = result.scalar_one_or_none()
        
        if review_item:
            review_item.status = ReviewStatus.APPROVED
            review_item.resolved_at = datetime.utcnow()
            # TODO: Set resolved_by_user_id when auth is implemented
            await db.commit()
        
        return ChatResponse(
            role='assistant',
            content=(
                f"✅ **Faktura godkjent!**\n\n"
                f"• Leverandør: {matching_review['supplier']}\n"
                f"• Beløp: {matching_review['amount']:,} kr\n"
                f"• Fakturanr: {matching_review.get('invoiceNumber', 'N/A')}"
            ),
            timestamp=datetime.utcnow().isoformat(),
            data={'approved': matching_review},
        )
    
    # Command: reject [id] [reason]
    reject_match = re.match(r'^reject\s+(\S+)(?:\s+(.+))?$', cmd)
    if reject_match:
        id_prefix = reject_match.group(1).strip()
        reason = reject_match.group(2).strip() if reject_match.group(2) else 'Ingen grunn oppgitt'
        matching_review = next(
            (r for r in pending_reviews if r['id'].lower().startswith(id_prefix.lower())),
            None
        )
        
        if not matching_review:
            return ChatResponse(
                role='assistant',
                content=f'❌ Fant ingen faktura med ID som starter med "{id_prefix}" eller den er allerede behandlet.',
                timestamp=datetime.utcnow().isoformat(),
            )
        
        # Update DB to mark as rejected
        review_id = UUID(matching_review['id'])
        query = select(ReviewQueue).where(ReviewQueue.id == review_id)
        result = await db.execute(query)
        review_item = result.scalar_one_or_none()
        
        if review_item:
            review_item.status = ReviewStatus.REJECTED
            review_item.resolved_at = datetime.utcnow()
            review_item.resolution_notes = reason
            # TODO: Set resolved_by_user_id when auth is implemented
            await db.commit()
        
        return ChatResponse(
            role='assistant',
            content=(
                f"❌ **Faktura avvist!**\n\n"
                f"• Leverandør: {matching_review['supplier']}\n"
                f"• Beløp: {matching_review['amount']:,} kr\n"
                f"• Grunn: {reason}"
            ),
            timestamp=datetime.utcnow().isoformat(),
            data={'rejected': matching_review, 'reason': reason},
        )
    
    # Command: help
    if cmd in ['help', 'hjelp']:
        return ChatResponse(
            role='assistant',
            content=(
                "🤖 **Tilgjengelige kommandoer:**\n\n"
                "• **show reviews** - Vis alle fakturaer som venter\n"
                "• **status** - Vis oversikt over alle fakturaer\n"
                "• **approve [id]** - Godkjenn en faktura\n"
                "• **reject [id] [grunn]** - Avvis en faktura\n"
                "• **help** - Vis denne hjelpen\n\n"
                "Tips: Du kan bruke de første tegnene av ID-en, f.eks. 'approve abc123'"
            ),
            timestamp=datetime.utcnow().isoformat(),
        )
    
    # Unknown command
    return ChatResponse(
        role='assistant',
        content=f'🤔 Beklager, jeg forstod ikke kommandoen "{message}". Skriv "help" for å se tilgjengelige kommandoer.',
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Process a chat message and return a response
    
    Supports commands:
    - show reviews / list - Show pending reviews
    - status - Show statistics
    - approve [id] - Approve a review item
    - reject [id] [reason] - Reject a review item
    - help - Show available commands
    """
    try:
        response = await process_command(request.message, db)
        return response
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chat_health():
    """Health check for chat endpoint"""
    return {
        "status": "healthy",
        "service": "chat",
        "commands": ["show reviews", "status", "approve [id]", "reject [id]", "help"],
    }
