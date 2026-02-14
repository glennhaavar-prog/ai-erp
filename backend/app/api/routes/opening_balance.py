"""
Opening Balance API - ÅPNINGSBALANSE (Stub implementation)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/api/opening-balance", tags=["Opening Balance"])


@router.get("/")
async def list_opening_balances(
    client_id: UUID = Query(..., description="Client ID"),
    status: str = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List opening balances (stub - returns empty list)
    """
    return []


@router.get("/{opening_balance_id}")
async def get_opening_balance(
    opening_balance_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get opening balance details (stub)
    """
    raise HTTPException(status_code=404, detail="Opening balance not found")


@router.post("/import")
async def import_opening_balance(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Import opening balance (stub)
    """
    return {
        "success": False,
        "message": "Opening balance import not yet implemented"
    }


@router.post("/upload-csv")
async def upload_csv(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload CSV file (stub)
    """
    return {
        "success": False,
        "message": "CSV upload not yet implemented"
    }


@router.post("/validate")
async def validate_opening_balance(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate opening balance (stub)
    """
    return {
        "valid": False,
        "errors": [],
        "warnings": [{"message": "Validation not yet implemented"}],
        "bank_verifications": []
    }


@router.post("/import-to-ledger")
async def import_to_ledger(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Import to general ledger (stub)
    """
    return {
        "success": False,
        "message": "Import to ledger not yet implemented"
    }


@router.delete("/{opening_balance_id}")
async def delete_opening_balance(
    opening_balance_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete opening balance (stub)
    """
    raise HTTPException(status_code=404, detail="Opening balance not found")
