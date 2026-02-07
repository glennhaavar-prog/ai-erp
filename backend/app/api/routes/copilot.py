"""
AI Copilot API - Context-aware assistant for accountants
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from pydantic import BaseModel
from uuid import UUID

from app.database import get_db
from app.services.copilot_service import CopilotService


router = APIRouter()
copilot_service = CopilotService()


# Request/Response Models
class CopilotChatRequest(BaseModel):
    message: str
    context: Dict[str, Any]  # {"page": "review_queue", "item_id": "uuid", "client_id": "uuid"}


class CopilotChatResponse(BaseModel):
    response: str
    suggestions: list


@router.post("/api/copilot/chat")
async def chat(
    request: CopilotChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with AI Copilot.
    
    Body:
    {
      "message": "Hva er konto 6820?",
      "context": {
        "page": "review_queue",
        "item_id": "uuid" (optional),
        "client_id": "uuid" (optional)
      }
    }
    
    Returns:
    {
      "response": "Konto 6820 er Forsikringskostnader...",
      "suggestions": [
        {
          "type": "tip",
          "text": "Du bør vurdere periodisering for årlige forsikringer",
          "action": "create_accrual"
        }
      ]
    }
    """
    
    try:
        result = await copilot_service.chat(
            message=request.message,
            context=request.context,
            db=db
        )
        
        return {
            "success": True,
            "response": result["response"],
            "suggestions": result["suggestions"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot error: {str(e)}")


@router.get("/api/copilot/suggest")
async def suggest(
    context: str,
    item_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get proactive suggestions based on context.
    
    Query params:
    - context: "review_queue" | "hovedbok" | "accruals"
    - item_id: Optional item UUID to analyze
    
    Returns:
    {
      "suggestions": [
        {
          "type": "warning" | "tip" | "automation",
          "text": "Dette kan være en periodiseringskostnad",
          "action": "create_accrual" | null,
          "action_data": {...} | null
        }
      ]
    }
    """
    
    try:
        item_uuid = UUID(item_id) if item_id else None
        
        result = await copilot_service.suggest(
            context=context,
            item_id=item_uuid,
            db=db
        )
        
        return {
            "success": True,
            "suggestions": result["suggestions"]
        }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item_id format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion error: {str(e)}")


@router.get("/api/copilot/health")
async def health():
    """Health check for Copilot service"""
    return {
        "status": "healthy",
        "service": "AI Copilot",
        "model": copilot_service.model
    }
