"""
Natural Language Query (NLQ) API

Allows querying accounting data using natural language.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID

from app.database import get_db
from app.services.nlq_service import NLQService


router = APIRouter()
nlq_service = NLQService()


# Request/Response Models
class NLQRequest(BaseModel):
    question: str
    client_id: str


@router.post("/api/nlq/query")
async def nlq_query(
    request: NLQRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Natural language query endpoint.
    
    Body:
    {
      "question": "Vis meg alle fakturaer fra Telenor",
      "client_id": "uuid"
    }
    
    Returns:
    {
      "success": true,
      "question": "Vis meg alle fakturaer fra Telenor",
      "sql": "SELECT ...",
      "results": [...],
      "count": 42
    }
    """
    
    try:
        result = await nlq_service.parse_and_execute(
            question=request.question,
            client_id=UUID(request.client_id),
            db=db
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLQ error: {str(e)}")


@router.get("/api/nlq/examples")
async def get_examples():
    """
    Get example natural language queries.
    
    Returns list of example questions users can ask.
    """
    
    return {
        "success": True,
        "examples": [
            "Vis meg alle fakturaer fra Telenor",
            "Hvor mye har vi brukt på forsikring i år?",
            "Siste 10 bilag",
            "Hvilke kunder har ikke betalt ennå?",
            "Vis transaksjoner siste måneden",
            "Hvor mye MVA har vi betalt i 2026?",
            "Alle periodiseringer for software",
        ]
    }


@router.get("/api/nlq/health")
async def health():
    """Health check for NLQ service"""
    return {
        "status": "healthy",
        "service": "Natural Language Query",
        "model": nlq_service.model
    }
