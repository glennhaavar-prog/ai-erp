"""
Accruals API Endpoints - Periodisering
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.models.accrual import Accrual
from app.models.accrual_posting import AccrualPosting
from app.services.accrual_service import AccrualService


router = APIRouter()
accrual_service = AccrualService()


# Request/Response Models
class CreateAccrualRequest(BaseModel):
    client_id: str
    description: str
    from_date: str  # YYYY-MM-DD
    to_date: str    # YYYY-MM-DD
    total_amount: float
    balance_account: str
    result_account: str
    frequency: str  # monthly, quarterly, yearly
    source_invoice_id: Optional[str] = None


class AccrualResponse(BaseModel):
    id: str
    client_id: str
    description: str
    from_date: str
    to_date: str
    total_amount: float
    balance_account: str
    result_account: str
    frequency: str
    next_posting_date: Optional[str]
    status: str
    created_by: str
    postings_count: int
    postings_pending: int
    postings_posted: int


@router.get("/api/accruals/")
async def list_accruals(
    client_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List all accruals.
    
    Query params:
    - client_id: Filter by client
    - status: Filter by status (active/completed/cancelled)
    """
    
    query = select(Accrual)
    
    if client_id:
        query = query.where(Accrual.client_id == UUID(client_id))
    
    if status:
        query = query.where(Accrual.status == status)
    
    query = query.order_by(Accrual.next_posting_date.asc().nullslast())
    
    result = await db.execute(query)
    accruals = result.scalars().all()
    
    # Build response with posting counts
    response = []
    for accrual in accruals:
        postings_result = await db.execute(
            select(AccrualPosting)
            .where(AccrualPosting.accrual_id == accrual.id)
        )
        postings = postings_result.scalars().all()
        
        postings_pending = len([p for p in postings if p.status == "pending"])
        postings_posted = len([p for p in postings if p.status == "posted"])
        
        response.append({
            "id": str(accrual.id),
            "client_id": str(accrual.client_id),
            "description": accrual.description,
            "from_date": accrual.from_date.isoformat(),
            "to_date": accrual.to_date.isoformat(),
            "total_amount": float(accrual.total_amount),
            "balance_account": accrual.balance_account,
            "result_account": accrual.result_account,
            "frequency": accrual.frequency,
            "next_posting_date": accrual.next_posting_date.isoformat() if accrual.next_posting_date else None,
            "status": accrual.status,
            "created_by": accrual.created_by,
            "postings_count": len(postings),
            "postings_pending": postings_pending,
            "postings_posted": postings_posted
        })
    
    return {
        "success": True,
        "count": len(response),
        "accruals": response
    }


@router.post("/api/accruals/")
async def create_accrual(
    request: CreateAccrualRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new accrual.
    
    Body:
    {
      "client_id": "uuid",
      "description": "Forsikring 2026",
      "from_date": "2026-01-01",
      "to_date": "2026-12-31",
      "total_amount": 12000.00,
      "balance_account": "1580",
      "result_account": "6820",
      "frequency": "monthly",
      "source_invoice_id": "uuid" (optional)
    }
    """
    
    try:
        result = await accrual_service.create_accrual(
            db=db,
            client_id=UUID(request.client_id),
            description=request.description,
            from_date=date.fromisoformat(request.from_date),
            to_date=date.fromisoformat(request.to_date),
            total_amount=Decimal(str(request.total_amount)),
            balance_account=request.balance_account,
            result_account=request.result_account,
            frequency=request.frequency,
            source_invoice_id=UUID(request.source_invoice_id) if request.source_invoice_id else None,
            created_by="user"
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/api/accruals/{accrual_id}")
async def get_accrual(
    accrual_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get accrual details with posting schedule.
    """
    
    try:
        # Fetch accrual
        result = await db.execute(
            select(Accrual)
            .where(Accrual.id == UUID(accrual_id))
        )
        accrual = result.scalar_one_or_none()
        
        if not accrual:
            raise HTTPException(status_code=404, detail="Accrual not found")
        
        # Fetch postings
        postings_result = await db.execute(
            select(AccrualPosting)
            .where(AccrualPosting.accrual_id == accrual.id)
            .order_by(AccrualPosting.posting_date)
        )
        postings = postings_result.scalars().all()
        
        return {
            "success": True,
            "accrual": {
                "id": str(accrual.id),
                "client_id": str(accrual.client_id),
                "description": accrual.description,
                "from_date": accrual.from_date.isoformat(),
                "to_date": accrual.to_date.isoformat(),
                "total_amount": float(accrual.total_amount),
                "balance_account": accrual.balance_account,
                "result_account": accrual.result_account,
                "frequency": accrual.frequency,
                "next_posting_date": accrual.next_posting_date.isoformat() if accrual.next_posting_date else None,
                "status": accrual.status,
                "created_by": accrual.created_by,
                "ai_detected": accrual.ai_detected,
                "source_invoice_id": str(accrual.source_invoice_id) if accrual.source_invoice_id else None,
                "created_at": accrual.created_at.isoformat(),
            },
            "postings": [
                {
                    "id": str(p.id),
                    "posting_date": p.posting_date.isoformat(),
                    "amount": float(p.amount),
                    "period": p.period,
                    "status": p.status,
                    "posted_by": p.posted_by,
                    "posted_at": p.posted_at.isoformat() if p.posted_at else None,
                    "general_ledger_id": str(p.general_ledger_id) if p.general_ledger_id else None
                }
                for p in postings
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/api/accruals/{accrual_id}/postings/{posting_id}/post")
async def post_accrual_manually(
    accrual_id: str,
    posting_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually post an accrual (if auto_post = false).
    
    Creates balanced GL entry.
    """
    
    try:
        result = await accrual_service.post_accrual(
            db=db,
            posting_id=UUID(posting_id),
            posted_by="user"
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/api/accruals/{accrual_id}")
async def cancel_accrual(
    accrual_id: str,
    reason: str = Query(..., description="Reason for cancellation"),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an active accrual.
    
    Sets status to 'cancelled' and cancels all pending postings.
    """
    
    try:
        # Fetch accrual
        result = await db.execute(
            select(Accrual)
            .where(Accrual.id == UUID(accrual_id))
        )
        accrual = result.scalar_one_or_none()
        
        if not accrual:
            raise HTTPException(status_code=404, detail="Accrual not found")
        
        if accrual.status != "active":
            raise HTTPException(status_code=400, detail=f"Cannot cancel accrual with status '{accrual.status}'")
        
        # Cancel accrual
        accrual.status = "cancelled"
        
        # Cancel all pending postings
        result = await db.execute(
            select(AccrualPosting)
            .where(
                and_(
                    AccrualPosting.accrual_id == accrual.id,
                    AccrualPosting.status == "pending"
                )
            )
        )
        pending_postings = result.scalars().all()
        
        for posting in pending_postings:
            posting.status = "cancelled"
        
        await db.commit()
        
        return {
            "success": True,
            "accrual_id": accrual_id,
            "status": "cancelled",
            "cancelled_postings": len(pending_postings),
            "reason": reason
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/api/accruals/auto-post")
async def auto_post_due_accruals(
    as_of_date: Optional[str] = Query(None, description="Date to check (YYYY-MM-DD), defaults to today"),
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-post all pending accruals due today or earlier.
    
    This endpoint is called by the daily cron job.
    """
    
    try:
        target_date = date.fromisoformat(as_of_date) if as_of_date else None
        
        result = await accrual_service.auto_post_due_accruals(
            db=db,
            as_of_date=target_date
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
