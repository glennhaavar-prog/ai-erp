"""
Chat Booking API - Natural language interface for invoice booking
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.chat.chat_service import ChatService

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat-booking", tags=["chat-booking"])

# Initialize chat service
chat_service = ChatService()


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatAttachment(BaseModel):
    """File attachment model"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type (e.g., 'application/pdf')")
    data: str = Field(..., description="Base64-encoded file data")


class ChatRequest(BaseModel):
    """Chat request"""
    message: str = Field(..., description="User's message")
    client_id: str = Field(..., description="Client UUID")
    user_id: Optional[str] = Field(None, description="User UUID (optional)")
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")
    conversation_history: Optional[List[ChatMessage]] = Field(None, description="Conversation history")
    attachments: Optional[List[ChatAttachment]] = Field(None, description="File attachments (PDF, images)")


class ChatResponse(BaseModel):
    """Chat response"""
    message: str
    action: str
    data: Dict[str, Any]
    timestamp: str
    session_id: str


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a chat message for invoice booking
    
    Supports commands:
    - "Bokfør denne faktura"
    - "Vis meg faktura INV-12345"
    - "Hva er status på alle fakturaer?"
    - "Godkjenn bokføring for faktura X"
    - "Korriger bokføring: bruk konto 6300 i stedet"
    
    The chat maintains context across messages in a session.
    """
    
    try:
        # Validate UUIDs
        try:
            UUID(request.client_id)
            if request.user_id:
                UUID(request.user_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(UUID(int=0))  # Default session
        
        # Process message
        attachment_info = f", attachments={len(request.attachments)}" if request.attachments else ""
        logger.info(f"Chat booking: session={session_id}, client={request.client_id}, message={request.message[:50]}{attachment_info}")
        
        # Log attachment details
        if request.attachments:
            for att in request.attachments:
                logger.info(f"  - Attachment: {att.filename} ({att.content_type}, {len(att.data)} bytes base64)")
        
        result = await chat_service.process_message(
            db=db,
            session_id=session_id,
            client_id=request.client_id,
            user_id=request.user_id,
            message=request.message,
            attachments=request.attachments  # Pass attachments to service
        )
        
        return ChatResponse(
            message=result['message'],
            action=result['action'],
            data=result.get('data', {}),
            timestamp=result['timestamp'],
            session_id=session_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat booking: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    Get conversation history for a session
    """
    try:
        context = chat_service.context_manager.get_context(session_id)
        history = context.get('conversation_history', [])
        
        return {
            "session_id": session_id,
            "message_count": len(history),
            "history": history,
            "current_invoice": context.get('current_invoice_number'),
            "last_intent": context.get('last_intent')
        }
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear session context
    """
    try:
        chat_service.context_manager.clear_context(session_id)
        return {
            "success": True,
            "message": f"Session {session_id} cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_suggestions():
    """
    Get command suggestions
    """
    return {
        "suggestions": [
            {
                "command": "Bokfør denne faktura",
                "description": "Start bokføring av en faktura",
                "category": "booking"
            },
            {
                "command": "Vis meg faktura INV-12345",
                "description": "Se detaljer for en faktura",
                "category": "query"
            },
            {
                "command": "Hva er status på alle fakturaer?",
                "description": "Oversikt over alle fakturaer",
                "category": "status"
            },
            {
                "command": "Vis meg fakturaer med lav confidence",
                "description": "Filtrer fakturaer som trenger manuell gjennomgang",
                "category": "query"
            },
            {
                "command": "Godkjenn bokføring",
                "description": "Godkjenn en bokføring i review queue",
                "category": "approval"
            },
            {
                "command": "Korriger bokføring: bruk konto 6340",
                "description": "Endre kontonummer i en bokføring",
                "category": "correction"
            },
            {
                "command": "help",
                "description": "Vis alle tilgjengelige kommandoer",
                "category": "help"
            }
        ]
    }


@router.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "chat_booking",
        "features": [
            "book_invoice",
            "show_invoice",
            "invoice_status",
            "approve_booking",
            "correct_booking",
            "list_invoices"
        ]
    }
