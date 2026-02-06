"""
Chat API endpoint for conversational review queue management
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from uuid import UUID

from app.database import get_db
from app.agents.orchestrator_chat import OrchestratorChatAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request payload"""
    client_id: str = Field(..., description="Client UUID")
    message: str = Field(..., description="User's message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Previous conversation messages for context"
    )


class ChatResponse(BaseModel):
    """Chat response payload"""
    message: str = Field(..., description="Assistant's response message")
    action: Optional[str] = Field(None, description="Action performed (e.g., 'approve', 'reject', 'list_queue')")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional structured data")
    timestamp: str = Field(..., description="Response timestamp")


# Initialize chat agent (singleton)
chat_agent = OrchestratorChatAgent()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Chat endpoint for conversational review queue management
    
    This endpoint provides a natural language interface for accountants to:
    - View pending review queue items
    - Approve or reject items via chat commands
    - Get detailed information about transactions
    - Ask questions about workload and status
    
    Example requests:
    - "Show me the review queue"
    - "Approve <item-id>"
    - "Reject <item-id> because incorrect vendor"
    - "What's my workload?"
    - "Show details for <item-id>"
    
    Args:
        request: Chat request containing client_id, message, and optional conversation history
        db: Database session (injected)
    
    Returns:
        ChatResponse with assistant's message, action performed, and structured data
    """
    try:
        # Validate client_id format
        try:
            UUID(request.client_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid client_id format: {request.client_id}"
            )
        
        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
        
        # Process chat message
        logger.info(f"Chat: Processing message for client {request.client_id}")
        
        result = await chat_agent.chat(
            db=db,
            client_id=request.client_id,
            user_message=request.message,
            conversation_history=history
        )
        
        # Build response
        from datetime import datetime
        response = ChatResponse(
            message=result["message"],
            action=result.get("action"),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(
            f"Chat: Response generated for client {request.client_id} "
            f"(action={result.get('action')})"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat: Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """Health check for chat endpoint"""
    return {
        "status": "healthy",
        "service": "chat_api",
        "agent_type": chat_agent.agent_type,
        "claude_configured": chat_agent.client is not None
    }


# Additional convenience endpoints

@router.get("/queue/{client_id}")
async def get_review_queue(
    client_id: str,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Get review queue items directly (convenience endpoint)
    
    This is equivalent to sending "show review queue" via chat,
    but returns the same structured format.
    
    Args:
        client_id: Client UUID
        db: Database session (injected)
    
    Returns:
        ChatResponse with formatted queue listing
    """
    try:
        UUID(client_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid client_id format: {client_id}"
        )
    
    try:
        result = await chat_agent.chat(
            db=db,
            client_id=client_id,
            user_message="show review queue",
            conversation_history=None
        )
        
        from datetime import datetime
        return ChatResponse(
            message=result["message"],
            action=result.get("action"),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat: Error fetching queue for {client_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching queue: {str(e)}"
        )


@router.post("/approve/{item_id}")
async def approve_item(
    item_id: str,
    client_id: str,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Approve a review queue item directly (convenience endpoint)
    
    Args:
        item_id: Review queue item UUID
        client_id: Client UUID (query parameter)
        db: Database session (injected)
    
    Returns:
        ChatResponse with approval confirmation
    """
    try:
        UUID(item_id)
        UUID(client_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid UUID format"
        )
    
    try:
        result = await chat_agent.chat(
            db=db,
            client_id=client_id,
            user_message=f"approve {item_id}",
            conversation_history=None
        )
        
        from datetime import datetime
        return ChatResponse(
            message=result["message"],
            action=result.get("action"),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat: Error approving item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error approving item: {str(e)}"
        )


@router.post("/reject/{item_id}")
async def reject_item(
    item_id: str,
    client_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Reject a review queue item directly (convenience endpoint)
    
    Args:
        item_id: Review queue item UUID
        client_id: Client UUID (query parameter)
        reason: Optional rejection reason
        db: Database session (injected)
    
    Returns:
        ChatResponse with rejection confirmation
    """
    try:
        UUID(item_id)
        UUID(client_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid UUID format"
        )
    
    try:
        message = f"reject {item_id}"
        if reason:
            message += f" {reason}"
        
        result = await chat_agent.chat(
            db=db,
            client_id=client_id,
            user_message=message,
            conversation_history=None
        )
        
        from datetime import datetime
        return ChatResponse(
            message=result["message"],
            action=result.get("action"),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat: Error rejecting item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error rejecting item: {str(e)}"
        )
