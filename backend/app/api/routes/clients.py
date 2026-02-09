"""
Clients API - List demo clients
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.models.client import Client
from app.models.review_queue import ReviewQueue

router = APIRouter(prefix="/api/v1/clients", tags=["Clients"])


class StatusSummary(BaseModel):
    vouchers_pending: int
    bank_items_open: int
    reconciliation_status: str
    vat_status: str


class ClientListItem(BaseModel):
    id: str
    name: str
    org_number: str
    status_summary: StatusSummary


class ClientListResponse(BaseModel):
    items: list[ClientListItem]
    total: int


class ClientDetail(BaseModel):
    id: str
    name: str
    org_number: str
    address: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    fiscal_year_start: str | None = None
    vat_registered: bool = True
    status_summary: StatusSummary


async def get_status_summary(client_id: UUID, db: AsyncSession) -> StatusSummary:
    """Calculate status summary for a client"""
    # TODO: Implement actual calculation per client
    # For now, return defaults to get API working
    return StatusSummary(
        vouchers_pending=0,
        bank_items_open=0,
        reconciliation_status="not_started",
        vat_status="not_started"
    )


@router.get("/")
async def get_clients(
    db: AsyncSession = Depends(get_db)
) -> ClientListResponse:
    """
    Get list of all demo clients with status summary
    """
    query = select(Client).where(Client.is_demo == True).order_by(Client.name)
    result = await db.execute(query)
    clients = result.scalars().all()
    
    items = []
    for client in clients:
        status_summary = await get_status_summary(client.id, db)
        items.append(
            ClientListItem(
                id=str(client.id),
                name=client.name,
                org_number=client.org_number,
                status_summary=status_summary
            )
        )
    
    return ClientListResponse(
        items=items,
        total=len(items)
    )


@router.get("/{client_id}")
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
) -> ClientDetail:
    """
    Get a single client by ID with full details
    """
    try:
        query = select(Client).where(Client.id == UUID(client_id))
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        status_summary = await get_status_summary(client.id, db)
        
        return ClientDetail(
            id=str(client.id),
            name=client.name,
            org_number=client.org_number,
            address=getattr(client, 'address', None),
            contact_person=getattr(client, 'contact_person', None),
            contact_email=getattr(client, 'contact_email', None),
            fiscal_year_start=getattr(client, 'fiscal_year_start', None),
            vat_registered=getattr(client, 'vat_registered', True),
            status_summary=status_summary
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
