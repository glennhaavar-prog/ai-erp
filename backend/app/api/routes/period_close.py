"""
Period Close API - Automated monthly/quarterly closing
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID

from app.database import get_db
from app.services.period_close_service import PeriodCloseService


router = APIRouter()


# Request/Response Models
class PeriodCloseRequest(BaseModel):
    client_id: str
    period: str  # YYYY-MM


@router.post("/api/period-close/run")
async def run_period_close(
    request: PeriodCloseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run automated period close.
    
    Body:
    {
      "client_id": "uuid",
      "period": "2026-01"
    }
    
    Returns:
    {
      "period": "2026-01",
      "status": "success",
      "checks": [
        {
          "name": "Balansekontroll",
          "status": "passed",
          "message": "15 bilag kontrollert, alt balanserer"
        },
        {
          "name": "Periodiseringer",
          "status": "passed",
          "message": "3 periodiseringer bokført",
          "posted_count": 3,
          "amount": 10000.00
        }
      ],
      "warnings": ["3 periodiseringer ble automatisk bokført"],
      "errors": [],
      "summary": "✅ Periode 2026-01 lukket. 2 kontroller utført, 1 advarsler."
    }
    """
    
    try:
        service = PeriodCloseService()
        result = await service.run_period_close(
            client_id=UUID(request.client_id),
            period=request.period,
            db=db
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Period close error: {str(e)}")


@router.get("/api/period-close/status/{client_id}/{period}")
async def get_period_status(
    client_id: str,
    period: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of a specific period.
    
    Returns whether period is open or closed.
    """
    
    try:
        from app.models.accounting_period import AccountingPeriod
        from sqlalchemy import select
        
        result = await db.execute(
            select(AccountingPeriod).where(
                AccountingPeriod.client_id == UUID(client_id),
                AccountingPeriod.period == period
            )
        )
        period_obj = result.scalar_one_or_none()
        
        if period_obj:
            return {
                "period": period,
                "status": period_obj.status,
                "closed_at": period_obj.closed_at.isoformat() if period_obj.closed_at else None
            }
        else:
            return {
                "period": period,
                "status": "open",
                "closed_at": null
            }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID or period format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
