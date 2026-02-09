"""
Balance Sheet API - Balanserapport
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.database import get_db
from app.services.balance_sheet_service import BalanceSheetService

router = APIRouter(prefix="/api/reports/balanse", tags=["reports"])


@router.get("/{client_id}")
async def get_balance_sheet(
    client_id: str,
    as_of_date: date = Query(..., description="Balance sheet date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Balance Sheet (Balanserapport) for a client as of a specific date
    
    Returns statement of financial position:
    - Assets (Eiendeler)
      - Fixed assets (Anleggsmidler)
      - Current assets (Omløpsmidler)
    - Liabilities & Equity (Gjeld og egenkapital)
      - Equity (Egenkapital)
      - Long-term liabilities (Langsiktig gjeld)
      - Current liabilities (Kortsiktig gjeld)
    
    Includes balance validation check (Assets = Liabilities + Equity).
    """
    try:
        result = await BalanceSheetService.generate_balance_sheet(
            db=db,
            client_id=client_id,
            as_of_date=as_of_date
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate balance sheet: {str(e)}"
        )


@router.get("/{client_id}/summary")
async def get_balance_sheet_summary(
    client_id: str,
    as_of_date: date = Query(..., description="Balance sheet date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get simplified balance sheet summary (top-line numbers only)
    """
    try:
        result = await BalanceSheetService.generate_balance_sheet(
            db=db,
            client_id=client_id,
            as_of_date=as_of_date
        )
        
        # Return only top-line summary
        summary = {
            "client_id": client_id,
            "as_of_date": result["as_of_date"],
            "currency": result["currency"],
            "total_assets": result["assets"]["total"],
            "fixed_assets": result["assets"]["fixed_assets"]["total"],
            "current_assets": result["assets"]["current_assets"]["total"],
            "total_equity": result["liabilities_and_equity"]["equity"]["total"],
            "total_liabilities": result["liabilities_and_equity"]["total_liabilities"],
            "long_term_liabilities": result["liabilities_and_equity"]["long_term_liabilities"]["total"],
            "current_liabilities": result["liabilities_and_equity"]["current_liabilities"]["total"],
            "is_balanced": result["balance_check"]["is_balanced"]
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
