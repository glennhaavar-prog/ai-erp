"""
Clients API - List demo clients
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from uuid import UUID

from app.database import get_db
from app.models.client import Client

router = APIRouter(prefix="/api/clients", tags=["Clients"])


@router.get("/")
async def get_clients(
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get list of all demo clients
    """
    query = select(Client).where(Client.is_demo == True).order_by(Client.name)
    result = await db.execute(query)
    clients = result.scalars().all()
    
    return [
        {
            "id": str(client.id),
            "name": client.name,
            "org_number": client.org_number,
            "is_demo": client.is_demo,
        }
        for client in clients
    ]


@router.get("/{client_id}")
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a single client by ID
    """
    try:
        query = select(Client).where(Client.id == UUID(client_id))
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return {
            "id": str(client.id),
            "name": client.name,
            "org_number": client.org_number,
            "base_currency": client.base_currency,
            "is_demo": client.is_demo,
            "status": client.status,
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
