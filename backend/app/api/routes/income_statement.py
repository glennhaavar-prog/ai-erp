"""
Income Statement API - Resultatregnskap
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from app.database import get_db
from app.services.income_statement_service import IncomeStatementService

router = APIRouter(prefix="/api/reports/resultatregnskap", tags=["reports"])


@router.get("/{client_id}")
async def get_income_statement(
    client_id: str,
    start_date: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    comparison_start: Optional[date] = Query(None, description="Comparison period start"),
    comparison_end: Optional[date] = Query(None, description="Comparison period end"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Income Statement (Resultatregnskap) for a client
    
    Returns profit & loss breakdown:
    - Revenue (Driftsinntekter)
    - Cost of goods sold (Varekostnad)
    - Gross profit (Bruttofortjeneste)
    - Operating expenses (Driftskostnader)
    - Operating profit (Driftsresultat)
    - Financial items (Finansposter)
    - Profit before tax (Resultat før skatt)
    
    Optional comparison period for period-over-period analysis.
    """
    try:
        result = await IncomeStatementService.generate_income_statement(
            db=db,
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            comparison_start_date=comparison_start,
            comparison_end_date=comparison_end
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate income statement: {str(e)}"
        )


@router.get("/{client_id}/summary")
async def get_income_statement_summary(
    client_id: str,
    start_date: date = Query(..., description="Period start date"),
    end_date: date = Query(..., description="Period end date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get simplified income statement summary (top-line numbers only)
    """
    try:
        result = await IncomeStatementService.generate_income_statement(
            db=db,
            client_id=client_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Return only top-line summary
        summary = {
            "client_id": client_id,
            "period": result["period"],
            "currency": result["currency"],
            "revenue": result["revenue"]["total"],
            "cost_of_goods_sold": result["cost_of_goods_sold"]["total"],
            "gross_profit": result["gross_profit"],
            "operating_expenses": result["operating_expenses"]["total"],
            "operating_profit": result["operating_profit"],
            "profit_before_tax": result["profit_before_tax"]
        }
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )
